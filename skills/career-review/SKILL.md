---
name: career-review
description: 职业发展域的目标设定与阶段复盘子 Skill。输入用户对职业目标、发展方向、阶段复盘的描述，输出结构化目标或复盘记录，按统一 schema 写入 domains/career/data/reviews。
---

# career-review

职业目标设定与阶段复盘。这是职业域里最"向内看"的一环：不只是记录做了什么，而是记录想去哪、走到了哪、偏差在哪。

## 触发场景

- 用户说"我给自己定个目标：今年内做到 XX""复盘一下这个季度""我在纠结要不要转方向"
- 用户发来一段职业规划、方向思考、阶段性总结的文字

## 两种记录模式

`mode = goal`：目标设定。记录想达成的状态与期限。

`mode = review`：阶段复盘。回看一段时间内的进展、偏差、调整方向。

由内容自动判断，也可由用户显式指定。

## 记录流程

1. 判断模式（goal / review）。
2. 抽取目标或复盘要点、时间跨度、状态。
3. 对 review 模式，尝试关联同期的 `milestone` 与 `project` 记录，形成证据支撑。
4. 按 schema 写入 `domains/career/data/reviews/<YYYY-MM>.json`。

## 输出字段

goal 模式：

```json
{
  "metrics": {
    "mode": "goal",
    "title": "2026 年内晋升到技术专家",
    "category": "promotion",
    "horizon": "2026-Q4",
    "status": "on_track",
    "key_results": ["主导 1 个核心项目", "拿到 1 次高绩效"]
  }
}
```

review 模式：

```json
{
  "metrics": {
    "mode": "review",
    "period": "2026-Q3",
    "went_well": ["完成 life-os 立项", "带教 1 名新人"],
    "gap": ["对外影响力不足", "技术深度输出偏少"],
    "next_action": ["每月输出 1 篇技术文章"]
  }
}
```

`category` 取值：`promotion`（晋升）/ `skill`（能力）/ `influence`（影响力）/ `leadership`（管理）/ `direction`（方向选择）/ `other`。
`horizon` 取值示例：`2026-Q4` / `2026-H2` / `2027`。
`status` 取值：`on_track`（正常推进）/ `at_risk`（有风险）/ `off_track`（偏离）/ `done`（达成）。

## 用户向回报格式

```
职业目标已记录 · 2025-10-09
2026 年内晋升到技术专家（promotion / 2026-Q4）
状态：正常推进 · 关键结果 2 项
```

## 注意事项

- goal 与 review 是主观内容，忠实记录用户原意，不加评判、不做心理分析。
- review 模式关联证据时，只引用仓库中真实存在的记录，不编造。
- 目标状态由用户判断，不擅自判定达成或失败。