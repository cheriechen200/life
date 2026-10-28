---
name: career-project
description: 职业发展域的项目推进子 Skill。输入一段关于项目进展的描述，输出结构化项目记录，跟踪状态、进度、投入与阻塞点，按统一 schema 写入 domains/career/data/projects。
---

# career-project

项目推进跟踪。同一项目可以在不同时间点反复记录，形成进度快照，用于回看推进节奏。

## 触发场景

- 用户说"XX 项目这周推进到 XX 了""今天在这个项目上花了 3 小时""XX 卡住了"
- 用户发来需求评审、排期、上线相关的描述或截图

## 记录流程

1. 识别项目名称，保持命名稳定（同一项目用同一个 `title`，便于聚合）。
2. 抽取当前状态与进度百分比。
3. 记录本次投入时长、角色、阻塞点。
4. 按 schema 写入 `domains/career/data/projects/<YYYY-MM>.json`。

同一项目多次记录是允许的，每条是独立快照，不做覆盖。

## 输出字段

```json
{
  "metrics": {
    "title": "life-os",
    "status": "in_progress",
    "progress_pct": 35,
    "hours_spent": 2.5,
    "role": "owner",
    "blocker": ""
  }
}
```

`status` 取值：`planning`（规划）/ `in_progress`（推进中）/ `blocked`（阻塞）/ `done`（完成）/ `paused`（暂停）。
`role` 取值：`owner`（负责人）/ `contributor`（参与）/ `reviewer`（评审）/ `support`（支持）。
`blocker` 无阻塞时留空字符串。

## 用户向回报格式

```
项目已记录 · 2025-10-09
life-os（推进中 35%）· 本次投入 2.5h · 角色：负责人
```

## 注意事项

- 项目命名一旦确定尽量沿用，避免同项目出现多个别名导致统计分散。
- 进度百分比是估算，允许用户修正。
- 阻塞状态应主动提示，帮助用户识别卡点。