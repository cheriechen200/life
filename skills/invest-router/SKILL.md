---
name: invest-router
description: 投资域股票与场内证券的入口 Skill。当用户发来股票、场内 ETF/LOF 的券商持仓/成交截图、研报、投资想法、行情截图或复盘请求时使用并分发到 invest 子 Skill；支付宝场外基金、余额宝、QDII、FOF 与黄金基金转交 fund-router，不使用股票规则。
---

# invest-router

投资域的统一捕捉入口。用户不需要关心"这条该存到哪"，凡是与投资相关的内容都先走这里。

## 触发场景

用户发来以下任意内容时应启用本 Skill：

- 券商 App 的**持仓页截图**（含总资产、市值、成本价、盈亏、仓位）
- **成交 / 交割单截图**（含成交价、数量、手续费）
- 研报、公司公告、新闻链接
- 一段投资想法（"我觉得 XX 值得看一下""记一下 XX 的逻辑"）
- 行情截图 / K 线图
- 复盘请求（"复盘一下本周""这笔交易做得对不对"）

明确属于支付宝场外基金、余额宝/货币基金、QDII、FOF、场外黄金基金或黄金 ETF 联接的请求，应直接转交 [`fund-router`](../fund-router/SKILL.md)；本 Skill 只处理股票及场内 ETF / LOF。若“ETF”或“黄金”产品形态不清，先澄清交易场所/产品类型，不要仅凭代码分类。

## 路由决策流程

1. **先判领域**：命中「健康关键词」（餐食 / 运动 / 睡眠 / InBody / 体成分 / 卡路里）→ **交回 `capture-router`**，不进入投资域。健康主体判定**优先于**投资关键词。
2. **再核对产品形态**：明确的支付宝场外基金、余额宝/货币基金、QDII、FOF、场外黄金基金或黄金 ETF 联接 → 转交 `skills/fund-router/SKILL.md`；不读股票标的池、不调用股票行情源。类型不明时先确认。
3. 本 Skill 只继续处理已识别的股票、场内 ETF / LOF 等证券，参考 `schema/data-schema.md` 的 invest 股票记录定义。
4. 分发到对应股票子 Skill。

路由对照表：

| 用户发来的内容 | type | 子 Skill | 主要产出 |
| --- | --- | --- | --- |
| 支付宝场外基金 / 余额宝 / QDII / FOF / 黄金基金咨询或账户截图 | `fund_*` | [fund-router](../fund-router/SKILL.md) | 转交基金研究、持仓或笔记流程；本 Skill 不处理 |
| 券商持仓截图 / "更新持仓" / "我买了 X"（股票/场内证券） | `position` | [invest-position](../invest-position/SKILL.md) | `holdings.md` + `data/positions/*.json` |
| 成交 / 交割单截图 | `trade` | [invest-position](../invest-position/SKILL.md) | `data/trades/*.json` |
| 一段投资想法 / 研报 / "记一下 X 的逻辑" | `note` | [invest-note](../invest-note/SKILL.md) | `data/notes/*.json` + `briefs/*.md` |
| "复盘本周 / 本月 / 这笔交易" | `review` | [invest-review](../invest-review/SKILL.md) | `data/reviews/*.json` + `reports/{weekly,monthly}/*.md` |
| "生成今日简报" / 定时任务 | — | [invest-morning](../invest-morning/SKILL.md) | `reports/daily/<YYYY-MM-DD>.md` |
| 观察池变动（纳入 / 移出） | `watchlist` | [invest-note](../invest-note/SKILL.md) | `data/watchlist/*.json` |

分发：

- `invest/position` / `invest/trade` → `skills/invest-position`
- `invest/note` / `invest/watchlist` → `skills/invest-note`
- `invest/review` → `skills/invest-review`
- 简报生成 → `skills/invest-morning`

## 落库规则

1. 原始附件**只存本地**：保存到 `data/raw/<YYYY-MM-DD>/`，文件名格式 `<type>_<时间戳>.<ext>`。该目录已被 `.gitignore` 排除，**解析完成后不 commit、不 push**（截图只用于解析取证，入库对象是结构化数据）。
2. **证券标的池校验**：只对股票/场内证券分发前读取 `domains/invest/universe.json`，命中 `deny` 的直接拒绝并说明原因。场外基金已在前一步转交 `fund-router`，不得经过本规则。
3. 按 `schema/data-schema.md` 中的股票记录定义组装 JSON，字段顺序固定。
4. 追加写入股票类型目录 `domains/invest/data/<type>/<YYYY-MM>.json`（不存在则创建数组）。
5. 由 `scripts/normalize_invest_data.py` 规范股票数据；基金数据仅由 `scripts/normalize_fund_data.py` 处理。
6. 提交推送前确认改动只落在 `domains/invest/`，不含 `data/raw/`。

## 输出确认

解析完成后，向用户简短回报：识别到的类型、写入的文件路径、关键数值。不要输出冗长的原始 JSON，除非用户要求。

## 注意事项

- **健康 vs 投资的误判是本 Skill 最大风险**。持仓截图可能同时含"总资产"与"步数"等信息，判定以**主体内容**为准；拿不准时向用户确认，不猜。
- 用户没说要记录时（例如只是问"XX 怎么样"），走 `invest-note` 的**分析模式**，不落库。
- 股票侧子 Skill 执行前，先读 `skills/stock-research/SKILL.md` 取股票框架、模板与铁律；不得把其价格、佣金、止损规则套用到场外基金。基金请求必须由 `fund-router` 转交独立基金 Skills。
