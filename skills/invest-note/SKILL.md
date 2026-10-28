---
name: invest-note
description: 投资域研究笔记 Skill。输入一段投资想法、研报、公司公告或"记一下 X 的逻辑"，按 stock-research 的三维框架分析，结构化写入 notes JSON，必要时生成单标的深度报告 markdown 到 briefs/。同时负责观察池（watchlist）的纳入与移出。
---

# invest-note

把一次研究判断沉淀为可回溯的结构化记录。核心是 `kill_criteria`（证伪条件）—— 写不出证伪条件，说明研究还没做透。

## 触发场景

- 用户说"记一下 X 的逻辑""为什么看好 X""帮我分析一下 X"
- 用户发来研报、公司公告、新闻链接
- 用户说"把 X 加入观察池""X 不用看了"

## 输入

- 标的代码（带 `sh` / `sz` 前缀）或名称
- 可选：用户已有的判断、研报内容、公告原文

## 分析流程

1. 先读 `skills/stock-research/SKILL.md` 及 `references/analysis-framework.md`。
2. **标的池校验**：读 `domains/invest/universe.json`，命中 `deny` 直接拒绝。
3. 三维分析（基本面 / 技术面 / 信息面），每个定性结论必须有数字支撑。
4. 过 **PM 七问**，重点回答第 1 问（什么被错误定价）与第 4 问（什么能推翻论点）。
5. 输出评级（`buy` / `hold` / `sell`）+ 行动分类 + 仓位上限 + 止损位。
6. **若需深度分析**，另外生成 `domains/invest/briefs/<代码>_<简称>_<YYYY-MM-DD>.md`（八节结构见 `stock-research/references/output-templates.md`）。
7. **同步更新观察池**：**先改 `holdings.md` 观察池表（唯一权威方），再反向同步 `watchlist` JSON**。两条必须同一次完成，禁止只改一边 —— 曾因只补 md 未同步 JSON，导致 7 只标的在 JSON 中缺失（2025-MM-DD）。

## 输出字段

```json
{
  "date": "2025-MM-DD",
  "domain": "invest",
  "type": "note",
  "metrics": {
    "symbol": "sh601000",
    "name": "示例股票B",
    "thesis": "Q2 单季净利 +29.11% 确立拐点，主力资金三期全正，红海绕行支撑运价",
    "catalyst": ["小摩重申增持 2025-MM-DD", "也门冲突升级、海峡通行量为零", "三季报 2025-10-31"],
    "kill_criteria": ["红海复航", "Q4 运量继续下滑", "主力 20 日转净流出"],
    "valuation": { "pe_ttm": 9.75, "pb": 1.12, "div_ttm_pct": 5.90 },
    "technical": { "ma_bull": true, "rsi6": 78.25, "pct_52w": 91.4 },
    "rating": "buy",
    "position_cap_pct": 6,
    "stop_loss": 16.02,
    "brief_ref": "domains/invest/briefs/sh601000_示例股票B_2025-MM-DD.md"
  },
  "note": "52 周分位 91.4%，需回踩 16.40–16.75 再介入",
  "source": "",
  "created_at": "2025-MM-DDT16:45:00+08:00"
}
```

### watchlist（观察池变动）

```json
{
  "metrics": {
    "symbol": "sz002594",
    "name": "比亚迪",
    "action": "avoid",
    "reason": "主力 20 日净流出 20.28 亿 + 碳酸锂期货跌超 11% + 出口退税率 13%→9%",
    "trigger": "跌破 80 且主力 20 日转正",
    "removed": false
  }
}
```

`action`：`buy` / `add` / `hold` / `reduce` / `clear` / `watch` / `avoid`。
`trigger`：状态变更的触发条件（什么情况下从"回避"改为"观察"，从"观察"改为"买入"）。
`removed`：`true` 表示已移出观察池（如违反标的池合规）。

## 深度报告八节结构

```
〇、结论（评级 + 行动分类 + 核心理由三条）
一、持仓快照
二、基本面（公告拆解 + 分季度数据 + 敏感性测算 + 表观 vs 前瞻估值）
三、技术面
四、资金面
五、PM 七问
六、多空论点对照
七、行动方案（执行清单 / 防守线 / 候选替代 / 催化剂日历）
八、数据来源与缺口
```

命名：`domains/invest/briefs/<代码>_<简称>_<YYYY-MM-DD>.md`，例 `sh600000_示例股票A_2025-MM-DD.md`。

## 用户向回报格式

```
研究笔记已记录 · sh601000 示例股票B
评级 buy ｜ 行动 买入（回踩确认）｜ 仓位上限 6% ｜ 止损 16.02
论点：Q2 单季净利 +29.11% 确立拐点，主力资金三期全正
证伪：红海复航 / Q4 运量继续下滑 / 主力 20 日转净流出
风险：52 周分位 91.4%，距高点仅 2.2%
深度报告：domains/invest/briefs/sh601000_示例股票B_2025-MM-DD.md
```

## 注意事项

- **`kill_criteria` 是必填项**。写不出来就说明研究深度不足，此时评级降级为 `hold` 或标「等待证据」。
- **区分事实与判断**：行情 / 公告是事实，研报观点是第三方判断，自己的推演标 `[假设]`。
- **估值要说清表观还是前瞻**。TTM 口径可能包含已过去的异常年份，用业绩推算做前瞻估值并标注 `[假设]`。
- 52 周分位是**价格位置**，不是估值分位，报告中必须注明。
- 结尾固定免责句。
