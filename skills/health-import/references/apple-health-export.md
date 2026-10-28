# Apple Health 数据导入

把 Apple 健康 App 的完整导出包解析为 life-os 统一 schema。详细流程见 [health-import SKILL](../../SKILL.md)。

## 导出步骤（iPhone）

1. 打开「健康」App → 右上角头像
2. 滑到最下方 → 「导出所有健康数据」
3. 得到 `导出.zip`（含 `导出.xml` 主数据文件）

## 解析

```bash
# 1. 解压到临时目录
unzip 导出.zip -d data/raw/

# 2. （可选）先扫描 Record 类型分布与时间范围
python3 skills/health-import/scripts/scan_health.py \
  "data/raw/apple_health_export/apple_health_export/导出.xml"

# 3. 增量解析（读取上次水位，只处理新数据）
python3 skills/health-import/scripts/parse_apple_health.py \
  "data/raw/apple_health_export/apple_health_export/导出.xml" .

# 4. 规范化并生成面板数据包
python3 scripts/normalize_health_data.py

# 5. 清理原始大文件，只留 JSON
rm -rf data/raw/apple_health_export 导出.zip

# 6. 同步到 GitHub
./scripts/sync.sh "data: import apple health export"
```

## 输出

| 输出位置 | 内容 |
| --- | --- |
| `domains/health/data/workouts/<YYYY-MM>.json` | 每次运动 |
| `domains/health/data/sleep/<YYYY-MM>.json` | 每晚睡眠（按起床日聚合） |
| `domains/health/data/daily/<YYYY-MM>.json` | 每日基础指标 |
| `domains/health/.import_state.json` | 导入水位 |

## 增量机制

Apple 健康每次导出都是全量，脚本按 `domains/health/.import_state.json` 中的水位 `last_import_date` 过滤，只解析水位之后（+1 天回溯）的数据。首次导入或需重建时加 `--full`。

## 说明

- 原始导出包（约 600MB）不入库，已在 `.gitignore` 排除，解析完成后删除，仅保留结构化后的 JSON。
- 此导出包是睡眠 / 运动 / 每日指标的**权威来源**；日常截图为临时记录，导入后由导出包覆盖。
- 覆盖时保留导出包无法提供的手动字段：`body_parts` / `exercises` / `circuit`。
- 睡眠归属以「起床当天」为准。
- 运动强度由平均心率推导，训练部位 Apple Health 不提供，需手动补充。
- 心率、能量等单位为 kcal / bpm，与 Apple Health 的 kJ 已自动换算。
- 重复导入会覆盖同键记录，属幂等操作。