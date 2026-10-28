---
name: career-milestone
description: 职业发展域的里程碑记录子 Skill。输入一段关于晋升、获奖、重要交付、职级评定、Offer、转岗等职业节点的描述，输出结构化里程碑记录，按统一 schema 写入 domains/career/data/milestones。
---

# career-milestone

职业里程碑记录。里程碑是职业轨迹上的关键坐标，只记"值得回看"的大事，不做日常流水账。

## 触发场景

- 用户说"记一下，我晋升了""今天拿了年度优秀员工""完成了 XX 重要交付""拿到 XX 公司的 offer"
- 用户发来一段描述职业节点的文字，或相关的通知截图、邮件截图

## 判定标准

一条记录能否称为 milestone，看它是否满足任一：

- 职级、职位、团队发生变化（晋升、转岗、换公司）
- 获得正式认可（奖项、表彰、专利、论文录用）
- 完成有分量的交付（上线核心项目、拿下关键客户、发布重要版本）
- 职业能力的标志性突破（首次带团队、首次对外演讲）

日常任务推进不算里程碑，归 `career-project`。

## 记录流程

1. 抽取事件标题、时间、类别、影响等级。
2. 补充一段自然语言备注（背景、成果、感受），写入 `note`。
3. 若用户提供截图或邮件，保存到 `data/raw/<YYYY-MM-DD>/`，路径写入 `source`。
4. 按 schema 写入 `domains/career/data/milestones/<YYYY-MM>.json`。

## 输出字段

```json
{
  "metrics": {
    "title": "晋升为高级工程师",
    "category": "promotion",
    "impact": "high",
    "evidence": "2026 年中晋升评审通过"
  }
}
```

`category` 取值：`promotion`（晋升）/ `award`（获奖）/ `delivery`（重要交付）/ `offer`（Offer 或转岗）/ `recognition`（外部认可）/ `other`。
`impact` 取值：`high` / `medium` / `low`，指对职业轨迹的影响程度，不是工作量。

## 用户向回报格式

```
里程碑已记录 · 2025-10-09
晋升为高级工程师（promotion / 高影响）
备注：2026 年中晋升评审通过
```

## 注意事项

- 类别拿不准时向用户确认，不要硬塞进 `other`。
- 影响等级如用户未表态，按客观事实判断并说明依据。
- 不为凑数而记录，里程碑贵精不贵多。