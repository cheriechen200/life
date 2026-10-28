---
name: invest-review
description: 投资域复盘 Skill。按周 / 月 / 单次事件三个维度复盘投资决策，评价决策过程质量而非盈亏结果，结构化写入 reviews JSON 并生成 markdown 周期报到 domains/invest/reports/weekly 或 monthly。模板与铁律引用 stock-research。
---

# invest-review

复盘的核心原则：**评价决策过程质量，而不是盈亏结果。** 用结果倒推过程是最常见的认知陷阱 —— 一笔赚钱的错误决策仍是错误决策。

## 触发场景

- 用户说"复盘一下本周 / 本月""这笔交易做得对不对"
- 定时任务：每周日 22:00（weekly）、每月最后一天 22:00（monthly）
- 重大事件后用户主动要求复盘（event）

## 输入

- 复盘范围：`weekly` / `monthly` / `event`
- 数据来源：`domains/invest/data/reviews/<YYYY-MM>.json`、`trades/<YYYY-MM>.json`、`positions/<YYYY-MM>.json`
- 对比基准：同期指数（沪深300 / 上证指数）

## 复盘流程

1. 先读 `skills/stock-research/SKILL.md` 与 `references/output-templates.md`。
2. 汇总区间内的全部 `trade` 与 `position` 变动，形成决策清单。
3. 逐笔判定 `outcome`：`win` / `loss` / `pending`。
4. **分开设两组评价**：
   - **结果**：盈亏金额、相对指数超额
   - **过程**：是否按 SOP 执行？是否有止损位？是否有证伪条件？是否被情绪驱动？
5. 总结 `went_well` / `gap` / `next_action`。
6. 打 `process_score`（1–10），**评过程不评结果**。
7. 写入 `reviews/<YYYY-MM>.json`，周期复盘另外生成 `reports/weekly/<YYYY-WW>.md` 或 `reports/monthly/<YYYY-MM>.md`。

## 输出字段

```json
{
  "date": "2025-MM-DD",
  "domain": "invest",
  "type": "review",
  "metrics": {
    "scope": "weekly",
    "period": "2026-W42",
    "decisions": [
      { "symbol": "sh600000", "action": "reduce", "shares": 100, "price": <价格>, "outcome": "pending" }
    ],
    "went_well": ["按公告（Q3 发电量 -14.89%）及时下调评级"],
    "gap": ["早盘未挂单，错过 29.40 减仓价"],
    "next_action": ["10-31 三季报验证净利降幅", "回踩 0.850 补示例ETF 1200 股"],
    "process_score": 7
  },
  "note": "",
  "source": "",
  "created_at": "2025-MM-DDT22:00:00+08:00"
}
```

`scope`：`weekly` / `monthly` / `event`。
`outcome`：`win` / `loss` / `pending`（未平仓或尚未验证）。
`process_score`：1–10，评过程质量。

## 周期报模板

```markdown
# 投资周报 · 2026-W42

> 统计区间：2025-MM-DD ~ 2025-10-19 ｜ 生成时间：…

## 一、区间表现
| 项目 | 期初 | 期末 | 变化 |
| 总资产 / 股票市值 / 现金 / 仓位 |
| 同期沪深300 | … | … | … |（用于算超额）

## 二、区间决策
| 日期 | 标的 | 动作 | 价格 | 数量 | 手续费占比 | 结果 |

## 三、做对了什么 / 差在哪
- went_well：…
- gap：…

## 四、过程分：<n>/10
评分依据（评过程不评结果）：…

## 五、下一步
- [ ] …

## 六、待验证
| 事件 | 日期 | 影响 |

---
本报告仅供研究参考，不构成个人投资建议，投资有风险，决策需独立。
```

## 过程评分参考

| 分 | 含义 |
| --- | --- |
| 9–10 | 按 SOP 完整执行：有理由（带数据）、有止损、有证伪条件、按计划价位成交 |
| 7–8 | 基本按 SOP，个别环节缺失（如未设止损、追高成交） |
| 5–6 | 有分析但执行走形（临时起意、情绪驱动） |
| ≤ 4 | 无分析依据，或未设任何风控 |

## 注意事项

- **不要用盈亏倒推决策质量**。赚钱的错误决策要指出错在哪，亏钱的正确决策要肯定过程。
- `outcome` 为 `pending` 时不要提前判定胜负，标注"待验证"+ 验证时间点。
- 复盘要能落到**具体可执行的下一步**，`next_action` 必须是动作而不是感想。
- 复盘只追加，**不改写历史决策记录**。
- 结尾固定免责句。
