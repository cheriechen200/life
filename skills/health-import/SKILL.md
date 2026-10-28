---
name: health-import
description: 健康域的批量导入 Skill。把 Apple 健康 App 导出的完整数据包解析为 life-os 统一 schema，并按增量方式回填运动 / 睡眠 / 每日指标。当用户说"导入 Apple 健康数据""解析导出包""批量导入历史数据"，或提供 导出.xml / 导出.zip / apple_health_export 目录时使用。
---

# health-import

Apple 健康导出包的批量解析与回填。用于每月一次的增量导入，是**睡眠 / 运动 / 每日指标的权威数据源**。

## 数据来源优先级（重要）

| 数据类型 | 日常（用户随时发） | 月度导出包 | 权威方 |
| --- | --- | --- | --- |
| meal（餐饮） | 单独维护、随时记录 | 不含 | 日常记录 |
| workout（训练） | 截图临时记录 | 完整训练数据 | **导出包** |
| sleep（睡眠） | 截图临时记录 | 完整睡眠数据 | **导出包** |
| daily_metrics | 不记录 | 每日基础指标 | **导出包** |

- 用户每天发来的睡眠 / 训练截图只作**临时保存**，先落库保证当天可见。
- 每月导出包到达后，用它**覆盖更新对应月份**，把截图记录的粗略值替换为完整值。
- 覆盖时保留导出包无法提供的**手动字段**：`body_parts` / `exercises` / `circuit`（训练部位与动作明细 Apple Health 不提供）。

## 触发场景

- 用户提供 Apple 健康导出包（`导出.zip` / `导出.xml` / 解压后的 `apple_health_export/` 目录）
- 用户说"导入健康数据""把 Apple 健康的记录解析进来""这个月的导出包来了"

## 全量导出 + 增量解析

Apple 健康每次导出都是**全量**（包含全部历史），但脚本内置**增量过滤**：

1. 导入水位记录在 `domains/health/.import_state.json`（`last_import_date` 字段）。
2. 解析时只处理**水位之后**的数据（额外回溯 1 天，避免边界日遗漏），早于水位的记录直接跳过，不重复改写。
3. 解析完成后自动更新水位为本次处理到的最大日期。

因此第二次及以后的导入天然是增量的，无需人工干预。

## 使用流程

1. 解压导出包到临时目录。
2. 可选：运行 `scripts/scan_health.py` 查看类型分布与时间范围。
3. 运行解析脚本（默认增量；首次或需重建时加 `--full`）。
4. 运行 `python3 scripts/normalize_health_data.py` 规范化并生成面板数据包。
5. **清理原始大文件**：删除导出包与 zip，只保留 `domains/` 下的 JSON。
6. 提示用户通过 `scripts/sync.sh` 提交推送。

```bash
unzip 导出.zip -d data/raw/

python3 skills/health-import/scripts/scan_health.py \
  "data/raw/apple_health_export/apple_health_export/导出.xml"

# 增量导入（读取上次水位，只解析新数据）
python3 skills/health-import/scripts/parse_apple_health.py \
  "data/raw/apple_health_export/apple_health_export/导出.xml" .

# 需要重建全部历史时（忽略水位）
# python3 skills/health-import/scripts/parse_apple_health.py \
#   "data/raw/apple_health_export/apple_health_export/导出.xml" . --full

python3 scripts/normalize_health_data.py

rm -rf data/raw/apple_health_export 导出.zip

./scripts/sync.sh "data: import apple health export"
```

## 脚本选项

| 选项 | 说明 |
| --- | --- |
| `--since <YYYY-MM-DD>` | 手动指定起始日期，覆盖状态文件中的水位 |
| `--lookback <N>` | 回溯天数，默认 1 |
| `--full` | 忽略水位，全量解析 |
| `--no-state` | 不读取也不写入状态文件（仅调试用） |

## 产出

| 输出位置 | 内容 |
| --- | --- |
| `domains/health/data/workouts/<YYYY-MM>.json` | 每次运动 |
| `domains/health/data/sleep/<YYYY-MM>.json` | 每晚睡眠（按起床日聚合） |
| `domains/health/data/daily/<YYYY-MM>.json` | 每日基础指标 |
| `domains/health/.import_state.json` | 导入水位（供下次增量过滤） |
| `dashboard/data.js` | 面板可直接读取的汇总数据包 |

字段定义见 [`schema/data-schema.md`](../../schema/data-schema.md)。

## 合并规则

- **workout**：以 `(date, time)` 为键精确匹配；若无精确匹配但同一天同类型唯一，也视为同一场。匹配到则用导出包数据覆盖，仅保留手动字段；未匹配到的新记录直接追加；导出包没有的旧记录原样保留。
- **sleep / daily_metrics**：以 `date` 为键覆盖，导出包为准；导出包未覆盖的日期保留。
- 运动强度由平均心率推导。

## 规范化

`parse_apple_health.py` 的输出保留了 Apple Health 的原始格式（如 `+0800` 时区、浮点计数值）。`scripts/normalize_health_data.py` 负责统一为稳定可读格式，详见 [dashboard Skill](../dashboard/SKILL.md) 的「数据规范化」一节。先解析再规范化，两步都不可省。

## 注意事项

- 重复导入是幂等的：同键记录被覆盖而非重复追加。
- 睡眠归属以「起床当天」为准。
- 运动强度由平均心率推导；训练部位 Apple Health 不提供，需手动补充，合并时会保留。
- 能量统一为 kcal、心率统一为 bpm，脚本已自动换算 kJ。
- 解析完成后向用户回报各类型记录条数与数据水位，不要粘贴原始 JSON。
- **原始导出包（`导出.zip` / 解压后的 XML）只作临时中转，解析完成后立即删除，不保留、不入库。** 项目一律只留 `domains/` 下的结构化 JSON。

## 参考

- 导入步骤与字段说明：[references/apple-health-export.md](references/apple-health-export.md)