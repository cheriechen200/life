---
name: habit-tracker
description: 个人成长域的习惯打点子 Skill。输入某个习惯当天的完成情况，输出结构化习惯记录并自动计算连续天数与本月完成率，按统一 schema 写入 domains/growth/data/habits。
---

# habit-tracker

习惯打点。这是成长域里最高频的记录：每天一句话甚至一个词即可完成打卡。

## 触发场景

- 用户说"今天冥想打勾了""断了三天没跑步""早起打卡"
- 用户发来习惯追踪 App 的截图

## 记录流程

1. 识别习惯名称，保持命名稳定（同一习惯用同一个 `habit` 值）。
2. 记录当天是否完成（`done`）与备注。
3. 读取该习惯在本月的历史记录，计算 `streak_days`（连续完成天数，遇到 `done=false` 归零）与 `month_rate`（本月完成率）。
4. 按 schema 写入 `domains/growth/data/habits/<YYYY-MM>.json`。

同一天同一习惯只保留一条记录，重复打卡执行更新而非追加。

## 输出字段

```json
{
  "metrics": {
    "habit": "meditation",
    "done": true,
    "streak_days": 12,
    "month_rate": 0.8,
    "note": ""
  }
}
```

`habit` 建议使用稳定的英文标识：`meditation` / `reading` / `exercise` / `early_rise` / `no_sugar` / `journaling` 等，中文名写入 `note` 便于展示。

## 用户向回报格式

```
习惯已打卡 · 2025-10-09
冥想 ✓ · 连续 12 天 · 本月完成率 80%
```

## 注意事项

- 连续天数从本月已记录数据推算；跨越月份时，若上月存在记录，需一并读取上月文件。
- 未打卡不要臆断为失败，只记录用户明确表达的状态。
- 习惯标识一旦确定不要更改，否则历史统计会断裂。