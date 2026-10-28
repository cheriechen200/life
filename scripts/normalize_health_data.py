#!/usr/bin/env python3
"""规范化 life-os 健康数据，并生成面板可直接本地读取的数据包。

用法：
  python3 scripts/normalize_health_data.py --check   # 只报告问题，不改文件
  python3 scripts/normalize_health_data.py           # 修复并写回，同时生成 dashboard/data.js

规范化内容：
  1. created_at 统一为 ISO 8601 带时区（+0800 -> +08:00）
  2. 计数字段（如 steps）去小数，统一为 int
  3. 记录字段顺序统一为 date / time? / domain / type / metrics / note / source / created_at
  4. 按 date (+time) 排序，保证 diff 稳定
  5. 汇总输出 dashboard/data.js（window.LIFE_OS_DATA），供 file:// 直接打开面板读取
"""
import json
import os
import re
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(SCRIPT_DIR)
DATA_DIR = os.path.join(REPO_ROOT, "domains/health/data")
BUNDLE_PATH = os.path.join(REPO_ROOT, "dashboard/data.js")

TYPES = {
    "meals": "meal",
    "workouts": "workout",
    "sleep": "sleep",
    "naps": "nap",
    "daily": "daily_metrics",
    "body_comp": "body_comp",
    "water": "water",
    "medical": "medical_report",
}

# 需要强制为整数的计数字段
INT_FIELDS = {"steps", "resting_heart_rate", "exercise_min", "awake_min",
              "deep_min", "light_min", "rem_min", "total_min", "sleep_score",
              "height_cm", "age", "visceral_fat_level", "inbody_score",
              "bmr_kcal", "recommended_intake_kcal",
              # 饮水计数字段（amount_ml / water_ml / container_ml 取整到 ml）
              "amount_ml", "water_ml", "container_ml",
              # 训练明细计数字段
              "sets", "reps", "rounds", "work_sec", "rest_sec"}

# 训练明细：exercises 为数组时逐条规范化计数字段与字段顺序
EXERCISE_KEY_ORDER = ["name", "name_cn", "weight_kg", "sets", "reps",
                      "unilateral", "equipment", "note"]
KEY_ORDER = ["date", "time", "domain", "type", "metrics", "note", "source", "created_at"]

TZ_RE = re.compile(r"([+-]\d{2})(\d{2})$")
CHECK_ONLY = "--check" in sys.argv


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
    # 训练明细：exercises 内每条动作也做取整与字段定序
    exercises = metrics.get("exercises")
    if isinstance(exercises, list):
        fixed_items = []
        for idx, ex in enumerate(exercises):
            if not isinstance(ex, dict):
                continue
            for k in list(ex.keys()):
                val = ex[k]
                if k in INT_FIELDS and isinstance(val, float) and val.is_integer():
                    ex[k] = int(val)
                    notes.append(f"exercises[{idx}].{k}")
            ordered = {k: ex[k] for k in EXERCISE_KEY_ORDER if k in ex}
            ordered.update({k: v for k, v in ex.items() if k not in ordered})
            fixed_items.append(ordered)
        metrics["exercises"] = fixed_items
    # 循环训练节奏：circuit 内的计数字段同样取整
    circuit = metrics.get("circuit")
    if isinstance(circuit, dict):
        for k in list(circuit.keys()):
            val = circuit[k]
            if k in INT_FIELDS and isinstance(val, float) and val.is_integer():
                circuit[k] = int(val)
                notes.append(f"circuit.{k}")
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
    return (r.get("date", ""), r.get("time", ""))


def process():
    issues = []
    bundle = {}
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
                    old_ca = r.get("created_at")
                    new_ca = fix_created_at(old_ca)
                    if new_ca != old_ca:
                        issues.append(f"{folder}/{fn}#{i}: created_at '{old_ca}' -> '{new_ca}'")
                        r["created_at"] = new_ca
                    if r.get("type") != rtype:
                        issues.append(f"{folder}/{fn}#{i}: type '{r.get('type')}' != '{rtype}'")
                        r["type"] = rtype
                    r["metrics"], fixed = coerce_metrics(r.get("metrics", {}))
                    if fixed:
                        issues.append(f"{folder}/{fn}#{i}: 取整 {fixed}")
                    recs.append(reorder(r))
        recs.sort(key=sort_key)
        out_path = None
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
        bundle[folder] = recs

    if not CHECK_ONLY:
        with open(BUNDLE_PATH, "w", encoding="utf-8") as f:
            f.write("// 自动生成，请勿手动编辑。由 scripts/normalize_health_data.py 生成。\n")
            f.write("// 供 dashboard 在 file:// 下直接读取，无需本地静态服务。\n")
            f.write("window.LIFE_OS_DATA = ")
            json.dump(bundle, f, ensure_ascii=False, separators=(",", ":"))
            f.write(";\n")

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
        print(f"已生成 {BUNDLE_PATH}")


if __name__ == "__main__":
    process()