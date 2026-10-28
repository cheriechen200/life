---
name: invest-position
description: 投资域持仓与成交维护 Skill。输入券商持仓截图或成交 / 交割单截图、或"我买了 X"这类描述，更新 domains/invest/holdings.md 台账，并按统一 schema 写入 positions / trades 两类 JSON。分析框架与合规铁律引用 stock-research。
---

# invest-position

维护持仓台账与成交记录。`holdings.md` 是人工可读的"当前状态"，`positions/*.json` 是机器可消费的时序快照，两者同步更新。

## 触发场景

- 用户发来券商 App 持仓页截图
- 用户发来成交 / 交割单截图
- 用户说"我买了 X""今天卖了 X""更新一下持仓"

## 输入

- 券商持仓页 / 交割单截图，或结构化的描述（代码、数量、价格）
- 目标日期，默认今天

## 处理流程

1. 先读 `skills/stock-research/SKILL.md`（框架与铁律）与 `domains/invest/universe.json`（标的池校验）。
2. 抽取字段：代码、名称、类型（股票 / ETF）、成本价、持仓数量、买入日期、现价。
3. **核对**（关键，防止解析错）：
   - `数量 × (现价 − 前收)` 应等于截图上的"当日参考盈亏"
   - `数量 × (现价 − 成本价)` 应等于截图上的"浮动盈亏"
   - 对不上时**不要强行入库**，标注差异并向用户确认
4. 计算：市值 = 数量 × 现价；盈亏 = 数量 × (现价 − 成本)；仓位% = 市值 / 总资产。
5. 更新 `domains/invest/holdings.md`：持仓表、观察池表、变动日志。
6. 写入 `domains/invest/data/positions/<YYYY-MM>.json`，**同一天同一 `symbol` 只保留一条**（重复执行更新而非追加）。
7. 若有成交，同时写入 `domains/invest/data/trades/<YYYY-MM>.json`。
8. 运行 `python3 scripts/normalize_invest_data.py` 规范化。

## 输出字段

### position

```json
{
  "date": "2025-MM-DD",
  "time": "15:00",
  "domain": "invest",
  "type": "position",
  "metrics": {
    "symbol": "sh600000",
    "name": "示例股票A",
    "asset_type": "stock",
    "shares": 200,
    "cost_price": <成本价>,
    "close_price": 29.15,
    "market_value": 5830.00,
    "pnl": 1162.94,
    "pnl_pct": 24.94,
    "weight_pct": 56.07,
    "action": "reduce",
    "stop_loss": 28.375
  },
  "note": "Q3 发电量同比 -14.89%（公告 2025-033），建议减半",
  "source": "",
  "created_at": "2025-MM-DDT16:30:00+08:00"
}
```

### trade

```json
{
  "date": "2025-MM-DD",
  "domain": "invest",
  "type": "trade",
  "metrics": {
    "symbol": "sh512800",
    "name": "示例ETF",
    "side": "buy",
    "shares": 1200,
    "price": 0.864,
    "amount": 1036.80,
    "fee": 5.00,
    "fee_pct": 0.48,
    "reason": "底仓首笔：均线全多头 + RSI6 66 未超买 + 主力 20 日净流入 3.83 亿",
    "plan_ref": "domains/invest/reports/daily/2025-MM-DD.md"
  },
  "created_at": "2025-MM-DDT16:40:00+08:00"
}
```

## 小额账户费率约束

当前账户单笔佣金 5 元固定。写入 `trade` 时必须计算并落库 `fee_pct`：

| 单笔金额 | `fee_pct` | 结论 |
| --- | --- | --- |
| < 500 元 | > 1.00% | ❌ 禁止下单，回报时警示 |
| 1,000 元 | 0.50% | ⚠️ 红线 |
| 2,000 元 | 0.25% | ✅ 理想 |

- **低价 ETF 必须买够股数**：示例ETF 100 股仅 <金额>，`fee_pct` = 5.79%，必须提示"最少买 1,200 股"。
- 股票卖出另加印花税 0.05%，ETF 免征 —— 计算 `fee` 时区分。

## 用户向回报格式

```
持仓已更新 · 2025-MM-DD 收盘
示例股票A sh600000 · 200 股 · 成本 <示例> · 现价 <现价>
市值 5,830.00 ｜ 浮盈 +1,162.94（+24.940%）｜ 仓位 56.1%
核对：200 × (29.15 − 29.379) = −45.8 ≈ 当日 −46.00 ✓
建议：减仓 100 股（止损 28.375）
```

## 注意事项

- **未经用户确认的成本价 / 持仓数量不得驱动加减仓建议**。缺失时 `cost_price` / `pnl` / `pnl_pct` 一律省略，并把缺口写入 `holdings.md` 的「待用户确认」。
- **"可用数量 < 持仓数量"** 是常见状态（限售、T+1、锁定）。减仓建议的**执行上限取可用数量**，并在备注中标注差额原因 [待确认]。
- 只追加或更新当日记录，**不改写历史快照**。历史就是历史。
- 现金若已用于国债逆回购，**到期前不可用于买入**，需在回报中提示。
