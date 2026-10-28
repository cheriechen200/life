#!/usr/bin/env python3
"""审计或规范化 invest 域的场外基金数据。

用法：
  python3 scripts/normalize_fund_data.py --check   # 只审计，不写入
  python3 scripts/normalize_fund_data.py           # 修复确定性格式问题并写回

本脚本只扫描 fund_positions / fund_trades / fund_notes；绝不读取、改写或校验
股票侧 positions / trades / notes / reviews / watchlist。基金代码身份须由用户确认，
本脚本只验证代码保存为六位数字字符串，不会把数值代码自动转成字符串或推断产品身份。
"""
from __future__ import annotations

import datetime as dt
import json
import os
import re
import sys
from typing import Any

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(SCRIPT_DIR)
DATA_DIR = os.path.join(REPO_ROOT, "domains/invest/data")
FUND_UNIVERSE_PATH = os.path.join(REPO_ROOT, "domains/invest/fund_universe.json")

TYPES = {
    "fund_positions": "fund_position",
    "fund_trades": "fund_trade",
    "fund_notes": "fund_note",
}
PRODUCT_CATEGORIES = {"equity", "bond", "money_market", "qdii", "fof", "gold_fund"}
POSITION_STATUSES = {"held", "redeeming", "closed"}
TRADE_TYPES = {"subscribe", "redeem"}
TRADE_STATUSES = {"applied", "confirmed", "in_transit", "completed", "cancelled", "failed"}
KEY_ORDER = ["date", "time", "domain", "type", "metrics", "note", "source", "created_at"]
MONTH_FILE_RE = re.compile(r"^\d{4}-(0[1-9]|1[0-2])\.json$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
FUND_CODE_RE = re.compile(r"^\d{6}$")
TZ_RE = re.compile(r"([+-]\d{2})(\d{2})$")
CHECK_ONLY = "--check" in sys.argv

# 基金份额允许小数；只对金额、净值和比例字段做 int -> float 的无损归一。
FLOAT_FIELDS = {
    "shares", "requested_shares", "confirmed_shares", "redeemed_shares",
    "requested_amount", "confirmed_amount", "cash_amount", "fee_amount",
    "cost_amount", "cost_nav", "latest_nav", "confirmed_nav", "nav", "market_value", "pnl",
    "pnl_pct", "income_amount", "daily_income", "income_per_10k",
    "annualized_7d_pct", "management_fee_pct", "custody_fee_pct",
    "sales_service_fee_pct", "purchase_discount_pct",
}


def add_issue(issues: list[str], where: str, message: str) -> None:
    issues.append(f"{where}: {message}")


def normalize_timestamp(value: Any) -> Any:
    if not isinstance(value, str):
        return value
    return TZ_RE.sub(r"\1:\2", value)


def has_timezone(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    try:
        parsed = dt.datetime.fromisoformat(value)
    except ValueError:
        return False
    return parsed.tzinfo is not None and parsed.utcoffset() is not None


def valid_date(value: Any) -> bool:
    if not isinstance(value, str) or not DATE_RE.fullmatch(value):
        return False
    try:
        dt.date.fromisoformat(value)
    except ValueError:
        return False
    return True


def load_fund_catalog(issues: list[str]) -> dict[str, dict[str, Any]]:
    try:
        with open(FUND_UNIVERSE_PATH, encoding="utf-8") as handle:
            catalog = json.load(handle)
    except (OSError, json.JSONDecodeError) as exc:
        add_issue(issues, "fund_universe.json", f"基金身份目录无法读取：{exc}")
        return {}

    products = catalog.get("products") if isinstance(catalog, dict) else None
    if not isinstance(products, list):
        add_issue(issues, "fund_universe.json", "products 必须是数组")
        return {}

    indexed: dict[str, dict[str, Any]] = {}
    for index, product in enumerate(products):
        where = f"fund_universe.json#products[{index}]"
        if not isinstance(product, dict):
            add_issue(issues, where, "产品条目必须是对象")
            continue
        code = product.get("fund_code")
        if not isinstance(code, str) or not FUND_CODE_RE.fullmatch(code):
            add_issue(issues, where, "fund_code 必须是六位数字字符串")
            continue
        if product.get("identity_verified") is not True:
            add_issue(issues, where, "产品身份未经确认；identity_verified 必须为 true")
            continue
        if not isinstance(product.get("fund_name"), str) or not product["fund_name"].strip():
            add_issue(issues, where, "fund_name 缺失或为空")
            continue
        if product.get("platform") != "alipay":
            add_issue(issues, where, "platform 必须为 alipay")
            continue
        if product.get("product_category") not in PRODUCT_CATEGORIES:
            add_issue(issues, where, "product_category 缺失或不在基金类别枚举中")
            continue
        if not isinstance(product.get("identity_source"), dict):
            add_issue(issues, where, "identity_source 必须记录身份核验来源对象")
            continue
        if code in indexed:
            add_issue(issues, where, f"fund_code {code!r} 在产品目录中重复")
            continue
        indexed[code] = product
    return indexed


def reorder(record: dict[str, Any]) -> dict[str, Any]:
    ordered = {key: record[key] for key in KEY_ORDER if key in record}
    ordered.update((key, value) for key, value in record.items() if key not in ordered)
    return ordered


def normalize_metrics(metrics: Any) -> tuple[Any, list[str]]:
    if not isinstance(metrics, dict):
        return metrics, []
    converted = []
    for key, value in list(metrics.items()):
        if key in FLOAT_FIELDS and isinstance(value, int) and not isinstance(value, bool):
            metrics[key] = float(value)
            converted.append(key)
    return metrics, converted


def validate_record(record: Any, folder: str, expected_type: str, filename: str,
                    index: int, issues: list[str],
                    catalog: dict[str, dict[str, Any]]) -> dict[str, Any] | None:
    where = f"{folder}/{filename}#{index}"
    if not isinstance(record, dict):
        add_issue(issues, where, "记录不是 JSON 对象")
        return None

    expected_key_order = list(reorder(record).keys())
    if list(record.keys()) != expected_key_order:
        add_issue(issues, where, "envelope 字段顺序不符合统一 Schema")

    if not valid_date(record.get("date")):
        add_issue(issues, where, "date 缺失或不是有效的 YYYY-MM-DD")
    elif filename.endswith(".json") and filename[:7] != record["date"][:7]:
        add_issue(issues, where, f"date {record['date']} 与文件月份 {filename[:7]} 不一致")

    if record.get("domain") != "invest":
        add_issue(issues, where, f"domain 必须为 'invest'，当前为 {record.get('domain')!r}")
        if not CHECK_ONLY:
            record["domain"] = "invest"

    if record.get("type") != expected_type:
        add_issue(issues, where, f"type 必须为 {expected_type!r}，当前为 {record.get('type')!r}")
        if not CHECK_ONLY:
            record["type"] = expected_type

    if not isinstance(record.get("metrics"), dict):
        add_issue(issues, where, "metrics 必须是对象")
        return record

    metrics, converted = normalize_metrics(record["metrics"])
    if converted:
        add_issue(issues, where, f"金额/份额字段 int -> float：{converted}")
    record["metrics"] = metrics

    fund_code = metrics.get("fund_code")
    if not isinstance(fund_code, str):
        add_issue(issues, where, "fund_code 必须是字符串；禁止自动转换以免丢失前导零")
    elif not FUND_CODE_RE.fullmatch(fund_code):
        add_issue(issues, where, f"fund_code {fund_code!r} 必须是六位数字字符串")

    if not isinstance(metrics.get("fund_name"), str) or not metrics["fund_name"].strip():
        add_issue(issues, where, "fund_name 缺失或为空")

    category = metrics.get("product_category")
    if category not in PRODUCT_CATEGORIES:
        add_issue(issues, where, f"product_category 缺失或不在允许值 {sorted(PRODUCT_CATEGORIES)}")

    if metrics.get("platform") != "alipay":
        add_issue(issues, where, "platform 必须为 'alipay'；本期范围不自动扩展到其他平台")

    catalog_product = catalog.get(fund_code) if isinstance(fund_code, str) else None
    if catalog_product is None:
        add_issue(issues, where, f"fund_code {fund_code!r} 未登记为已核实产品；先核验并登记 fund_universe.json")
    else:
        aliases = catalog_product.get("aliases", [])
        if not isinstance(aliases, list):
            aliases = []
        if metrics.get("fund_name") != catalog_product.get("fund_name") and metrics.get("fund_name") not in aliases:
            add_issue(issues, where, "fund_name 与已核实产品目录不匹配")
        if metrics.get("platform") != catalog_product.get("platform"):
            add_issue(issues, where, "platform 与已核实产品目录不匹配")
        if category != catalog_product.get("product_category"):
            add_issue(issues, where, "product_category 与已核实产品目录不匹配")

    if expected_type == "fund_position":
        if metrics.get("status") not in POSITION_STATUSES:
            add_issue(issues, where, f"持仓 status 必须为 {sorted(POSITION_STATUSES)} 之一")
        if metrics.get("latest_nav") is not None and not valid_date(metrics.get("nav_date")):
            add_issue(issues, where, "latest_nav 有值时必须提供有效 nav_date")

    elif expected_type == "fund_trade":
        if metrics.get("transaction_type") not in TRADE_TYPES:
            add_issue(issues, where, f"transaction_type 必须为 {sorted(TRADE_TYPES)} 之一")
        if metrics.get("status") not in TRADE_STATUSES:
            add_issue(issues, where, f"交易 status 必须为 {sorted(TRADE_STATUSES)} 之一")
        if metrics.get("confirmed_nav") is not None and not valid_date(metrics.get("nav_date")):
            add_issue(issues, where, "confirmed_nav 有值时必须提供有效 nav_date")

    elif expected_type == "fund_note":
        if not isinstance(metrics.get("thesis"), str) or not metrics["thesis"].strip():
            add_issue(issues, where, "fund_note 必须有 thesis 核心论点")
        sources = metrics.get("evidence")
        if not isinstance(sources, list) or not sources:
            add_issue(issues, where, "fund_note evidence 必须至少包含一个可追溯来源对象")
        else:
            allowed_levels = {"official", "third_party", "user_screenshot", "user_statement"}
            for source_index, source in enumerate(sources):
                if not isinstance(source, dict) or not isinstance(source.get("name"), str) or not source["name"].strip():
                    add_issue(issues, where, f"evidence[{source_index}] 必须包含来源名称")
                    continue
                if source.get("source_level") not in allowed_levels:
                    add_issue(issues, where, f"evidence[{source_index}].source_level 必须是 {sorted(allowed_levels)} 之一")
                for date_field in ("published_at", "as_of"):
                    if source.get(date_field) is not None and not valid_date(source[date_field]):
                        add_issue(issues, where, f"evidence[{source_index}].{date_field} 必须为 YYYY-MM-DD")

    created_at = record.get("created_at")
    fixed_created_at = normalize_timestamp(created_at)
    if fixed_created_at != created_at:
        add_issue(issues, where, f"created_at 时区格式规范化：{created_at!r} -> {fixed_created_at!r}")
        if not CHECK_ONLY:
            record["created_at"] = fixed_created_at
    if not has_timezone(record.get("created_at")):
        add_issue(issues, where, "created_at 必须是带时区的 ISO 8601 时间戳")

    for optional_date in ("confirmed_date", "settlement_date", "application_date"):
        value = metrics.get(optional_date)
        if value is not None and not valid_date(value):
            add_issue(issues, where, f"{optional_date} 不是有效的 YYYY-MM-DD")

    return record


def record_sort_key(record: dict[str, Any]) -> tuple[str, str, str, str, str]:
    metrics = record.get("metrics") or {}
    return (
        str(record.get("date", "")),
        str(record.get("time", "")),
        str(metrics.get("fund_code", "")),
        str(metrics.get("share_class", "")),
        str(metrics.get("transaction_id", "")),
    )


def audit_duplicates(folder: str, record_type: str, records: list[dict[str, Any]],
                     issues: list[str]) -> None:
    if record_type == "fund_position":
        seen: set[tuple[str, str, str, str]] = set()
        for record in records:
            metrics = record.get("metrics") or {}
            key = (str(record.get("date")), str(metrics.get("fund_code")),
                   str(metrics.get("share_class", "")), str(metrics.get("account_alias", "")))
            if key in seen:
                add_issue(issues, folder, f"同日重复基金持仓快照 {key}")
            seen.add(key)
    else:
        id_field = "transaction_id" if record_type == "fund_trade" else "note_id"
        seen_ids: set[str] = set()
        for record in records:
            metrics = record.get("metrics") or {}
            identifier = metrics.get(id_field)
            if isinstance(identifier, str) and identifier:
                if identifier in seen_ids:
                    add_issue(issues, folder, f"重复 {id_field} {identifier!r}")
                seen_ids.add(identifier)


def process() -> int:
    global CHECK_ONLY
    issues: list[str] = []
    catalog = load_fund_catalog(issues)
    total = 0
    for folder, record_type in TYPES.items():
        directory = os.path.join(DATA_DIR, folder)
        if not os.path.isdir(directory):
            add_issue(issues, folder, "基金类型目录缺失")
            continue

        for filename in sorted(os.listdir(directory)):
            if not filename.endswith(".json"):
                continue
            path = os.path.join(directory, filename)
            if not MONTH_FILE_RE.fullmatch(filename):
                add_issue(issues, f"{folder}/{filename}", "文件名必须为 YYYY-MM.json")
            try:
                with open(path, encoding="utf-8") as handle:
                    data = json.load(handle)
            except (OSError, json.JSONDecodeError) as exc:
                add_issue(issues, f"{folder}/{filename}", f"JSON 无法读取：{exc}")
                continue
            if not isinstance(data, list):
                add_issue(issues, f"{folder}/{filename}", "根结构必须是数组")
                continue

            total += len(data)
            normalized: list[dict[str, Any]] = []
            safe_to_write = True
            for index, record in enumerate(data):
                validated = validate_record(record, folder, record_type, filename, index, issues, catalog)
                if validated is not None:
                    normalized.append(reorder(validated))
                else:
                    # Preserve malformed list members verbatim; never drop data while normalizing.
                    safe_to_write = False

            sorted_records = sorted(normalized, key=record_sort_key)
            if normalized != sorted_records:
                add_issue(issues, f"{folder}/{filename}", "记录未按 date/time/fund_code/share_class/transaction_id 排序")
            audit_duplicates(folder, record_type, sorted_records, issues)

            if not CHECK_ONLY and safe_to_write:
                with open(path, "w", encoding="utf-8") as handle:
                    json.dump(sorted_records, handle, ensure_ascii=False, indent=2)
                    handle.write("\n")

    print(f"扫描基金记录 {total} 条（仅 fund_positions / fund_trades / fund_notes）")
    if issues:
        print(f"发现 {len(issues)} 项待检查/规范：")
        for issue in issues[:60]:
            print(f"  - {issue}")
        if len(issues) > 60:
            print(f"  ... 其余 {len(issues) - 60} 项")
        if CHECK_ONLY:
            print("只读检查已完成，未修改任何文件。")
            return 1
        print("已写回可确定规范化的字段；正在复查未能自动修复的身份/数据问题。")
        CHECK_ONLY = True
        try:
            return process()
        finally:
            CHECK_ONLY = False

    print("基金数据符合规范，无待修复项。")
    if not CHECK_ONLY:
        print(f"已规范化基金目录：{DATA_DIR}/fund_*")
    return 0


if __name__ == "__main__":
    sys.exit(process())
