#!/usr/bin/env python3
"""规范化 life-os 投资域数据。

用法：
  python3 scripts/normalize_invest_data.py --check   # 只报告问题，不改文件
  python3 scripts/normalize_invest_data.py           # 修复并写回

规范化内容：
  1. created_at 统一为 ISO 8601 带时区（+0800 -> +08:00）
  2. 计数字段（shares / process_score）去小数，统一为 int
  3. 金额类字段（market_value / pnl / stop_loss 等）统一为 float
  4. 记录字段顺序统一为 date / time? / domain / type / metrics / note / source / created_at
  5. 按 date (+time) 排序，保证 diff 稳定
  6. 校验 domain 必须为 invest、type 必须与目录匹配
  7. 校验 symbol 是否通过 domains/invest/universe.json 的标的池合规检查
  8. 校验 position 类型：同一 date + symbol 不得重复

与 normalize_health_data.py 的区别：本脚本不生成 dashboard 数据包
（投资域面板尚未接入，见 reports/invest/topics/股票研究板块规划方案_2025-MM-DD.md 阶段二）。
"""
import json
import os
import re
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(SCRIPT_DIR)
DATA_DIR = os.path.join(REPO_ROOT, "domains/invest/data")
UNIVERSE_PATH = os.path.join(REPO_ROOT, "domains/invest/universe.json")

TYPES = {
    "positions": "position",
    "trades": "trade",
    "notes": "note",
    "reviews": "review",
    "watchlist": "watchlist",
}

# 计数字段：强制 int
INT_FIELDS = {"shares", "process_score"}
# 金额 / 价格字段：强制 float
FLOAT_FIELDS = {
    "cost_price", "close_price", "market_value", "pnl", "pnl_pct",
    "weight_pct", "stop_loss", "price", "amount", "fee", "fee_pct",
    "pe_ttm", "pe_forward", "pb", "div_ttm_pct",
    "div_forward_pct", "rsi6", "kdj_j", "pct_52w",
}

KEY_ORDER = ["date", "time", "domain", "type", "metrics", "note", "source", "created_at"]

TZ_RE = re.compile(r"([+-]\d{2})(\d{2})$")
CHECK_ONLY = "--check" in sys.argv


def load_universe():
    """读标的池合规配置。文件缺失时返回 None（跳过校验）。"""
    if not os.path.isfile(UNIVERSE_PATH):
        return None
    with open(UNIVERSE_PATH, encoding="utf-8") as f:
        return json.load(f)


def check_symbol(symbol, universe, issues, where):
    """按 universe.json 做前缀校验：先 deny 后 allow。"""
    if not universe or not isinstance(symbol, str):
        return
    code = symbol[2:] if symbol[:2] in ("sh", "sz") else symbol
    raw_deny = universe.get("deny", {}).get("stock", [])
    etf_deny = universe.get("deny", {}).get("etf", [])
    for prefix in list(raw_deny) + list(etf_deny):
        if code.startswith(prefix):
            issues.append(f"{where}: symbol '{symbol}' 命中 deny 前缀 '{prefix}'，违反标的池合规")
            return
    allow_stock = universe.get("allow", {}).get("stock", [])
    allow_etf = universe.get("allow", {}).get("etf", [])
    if not any(code.startswith(p) for p in list(allow_stock) + list(allow_etf)):
        issues.append(f"{where}: symbol '{symbol}' 未命中任何 allow 前缀，需人工确认")


def fix_created_at(v):
    if not isinstance(v, str):
        return v
    return TZ_RE.sub(r"\1:\2", v)


def coerce_metrics(metrics):
    if not isinstance(metrics, dict):
        return metrics, []
    notes = []
    for k in list(metrics.keys()):
        val = metrics[k]
        if k in INT_FIELDS and isinstance(val, float) and val.is_integer():
            metrics[k] = int(val)
            notes.append(k)
        elif k in FLOAT_FIELDS and isinstance(val, int) and not isinstance(val, bool):
            metrics[k] = float(val)
            notes.append(k)
    # 嵌套对象（valuation / technical）内的字段同样做类型归一
    for nested_key in ("valuation", "technical"):
        nested = metrics.get(nested_key)
        if isinstance(nested, dict):
            for k in list(nested.keys()):
                val = nested[k]
                if k in FLOAT_FIELDS and isinstance(val, int) and not isinstance(val, bool):
                    nested[k] = float(val)
                    notes.append(f"{nested_key}.{k}")
    return metrics, notes


def reorder(rec):
    out = {}
    for k in KEY_ORDER:
        if k in rec:
            out[k] = rec[k]
    for k in rec:
        if k not in out:
            out[k] = rec[k]
    return out


def sort_key(r):
    return (r.get("date", ""), r.get("time", ""), r.get("metrics", {}).get("symbol", ""))


def process():
    issues = []
    universe = load_universe()
    total = 0

    for folder, rtype in TYPES.items():
        d = os.path.join(DATA_DIR, folder)
        recs = []
        if os.path.isdir(d):
            for fn in sorted(os.listdir(d)):
                if not fn.endswith(".json"):
                    continue
                path = os.path.join(d, fn)
                with open(path, encoding="utf-8") as f:
                    data = json.load(f)
                if not isinstance(data, list):
                    issues.append(f"{folder}/{fn}: 根结构不是数组")
                    continue
                for i, r in enumerate(data):
                    total += 1
                    where = f"{folder}/{fn}#{i}"

                    old_ca = r.get("created_at")
                    new_ca = fix_created_at(old_ca)
                    if new_ca != old_ca:
                        issues.append(f"{where}: created_at '{old_ca}' -> '{new_ca}'")
                        r["created_at"] = new_ca

                    if r.get("domain") != "invest":
                        issues.append(f"{where}: domain '{r.get('domain')}' != 'invest'")
                        r["domain"] = "invest"

                    if r.get("type") != rtype:
                        issues.append(f"{where}: type '{r.get('type')}' != '{rtype}'")
                        r["type"] = rtype

                    metrics = r.get("metrics", {})
                    metrics, fixed = coerce_metrics(metrics)
                    if fixed:
                        issues.append(f"{where}: 类型归一 {fixed}")
                    r["metrics"] = metrics

                    # removed=True 是"已移出的违规标的"审计记录（如 2025-MM-DD 误纳入的
                    # 三只创业板标的），属预期内容，跳过合规校验以免污染审计输出
                    if metrics.get("removed") is not True:
                        check_symbol(metrics.get("symbol"), universe, issues, where)

                    recs.append(reorder(r))

        # position：同一 date + symbol 不得重复
        if rtype == "position":
            seen = {}
            for r in recs:
                key = (r.get("date"), r.get("metrics", {}).get("symbol"))
                if key in seen:
                    issues.append(f"{folder}: 重复快照 {key[0]} {key[1]}")
                seen[key] = True

        recs.sort(key=sort_key)

        if not CHECK_ONLY:
            month_map = {}
            for r in recs:
                m = r.get("date", "")[:7]
                month_map.setdefault(m, []).append(r)
            for m, items in month_map.items():
                out_path = os.path.join(d, m + ".json")
                with open(out_path, "w", encoding="utf-8") as f:
                    json.dump(items, f, ensure_ascii=False, indent=2)
                    f.write("\n")

    print(f"扫描记录 {total} 条")
    if issues:
        print(f"发现 {len(issues)} 处待规范：")
        for s in issues[:40]:
            print("  -", s)
        if len(issues) > 40:
            print(f"  ... 其余 {len(issues) - 40} 处")
    else:
        print("数据已符合规范，无待修复项。")
    if not CHECK_ONLY:
        print(f"已写回 {DATA_DIR}")
    if CHECK_ONLY and issues:
        print("\n提示：去掉 --check 可自动修复上述问题。")


if __name__ == "__main__":
    process()
