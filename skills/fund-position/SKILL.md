---
name: fund-position
description: 支付宝场外基金与黄金基金持仓、申购和赎回台账维护。用户发送支付宝基金持仓/交易截图、描述申购赎回或要求更新基金持仓时使用；核实产品身份和日期后更新 fund_holdings.md 及 fund_positions/fund_trades JSON，并运行独立基金规范化脚本。
agent_created: true
---

# fund-position

## 目的与数据权威性

维护 `domains/invest/fund_holdings.md` 的基金当前状态，以及 `fund_positions` 持仓快照和 `fund_trades` 交易事件。账户份额、成本、申请状态、确认数据以用户提供的支付宝页面或明确确认文字为准；外部查询只用于基金资料和已发布净值，不能覆盖账户事实。

## 处理流程

1. 读取 `domains/invest/fund_universe.json`、`schema/data-schema.md` 中基金 Schema 和本 Skill 关联模板。
2. **确认产品身份**：对照截图中的基金代码、名称、份额类别和支付宝页面，并确认 `fund_universe.json` 有匹配的已验证映射。目录缺项时，先通过用户页面与基金公司/正式产品资料核实，再登记 `fund_code`、名称、平台、类别和身份来源；冲突时先提问，不覆盖目录。代码保留字符串/前导零；不把代码改为 `sh`/`sz`，不调用股票行情接口。
3. **解析时点与页面状态**：区分申请日、确认日、净值日、到账日；识别申购/赎回、申请金额/份额、已确认份额、费用及状态。截图看不清、字段冲突或算术对不上时暂停写入并询问。
4. **保护隐私**：只摘录与记录相关的必要字段；不得抄录账号、手机号、身份证号、银行卡号。截图原件只存 `data/raw/<YYYY-MM-DD>/`，确认该路径被忽略且不进入提交。
5. **避免臆造**：未在截图或用户文字中提供的份额、成本、费用、确认净值、状态等字段保持缺省；不得从市值、收益率或当前净值反推历史成本和交易。外部净值必须带 `nav_date`、来源和获取时点，估算值不能存作正式 NAV。
6. **更新当前台账**：新建或更新 `domains/invest/fund_holdings.md` 对应持仓行，并保留在途交易区和待确认项。历史快照不删除；同一日期、基金代码、份额类别、账户别名键重复时更新该日快照，不重复追加。
7. **写 JSON**：按统一 envelope 将持仓快照写入 `domains/invest/data/fund_positions/<YYYY-MM>.json`；申购/赎回事件写入 `fund_trades/<YYYY-MM>.json`。日期使用申请日或快照日，确认、净值和到账日期用各自字段，不混成同一天。
8. **处理在途交易**：订单申请后为 `applied`；已确认但尚未完成资金/份额结算时按页面记 `confirmed` 或 `in_transit`；只有页面显示完成后才记 `completed`。撤销/失败要保留事件记录，不把申请额冒充实收/实付。
9. **规范与复核**：运行 `python3 scripts/normalize_fund_data.py --check`；如报告需规范的问题，先运行写回模式，再重跑 `--check`。复核检查范围只涉及基金三类目录；不要运行股票 normalizer 来处理基金。
10. **回报用户**：简要说明识别的产品、记录类型、已确认字段、缺失/待确认字段及实际写入路径；不得输出冗长原始 JSON。

## 类型与路径

| 记录 | 目录 | 幂等键 / 规则 |
|---|---|---|
| 持仓快照 | `fund_positions` | 同日 + `fund_code` + `share_class` + `account_alias` 最多一条；缺少份额类别/账户别名时按空值处理，不自行创造。 |
| 申购/赎回 | `fund_trades` | 每笔交易一条；平台订单号有证据时用 `transaction_id`，没有就不编。 |
| 研究笔记 | `fund_notes` | 不由本 Skill 写；显式研究保存请求转 `fund-note`。 |

基金代码应是六位字符串，但这只是格式校验，不是身份验证。黄金基金按 `product_category=gold_fund` 记录；场内黄金 ETF 仍由股票侧处理。

## 输出边界

- 本 Skill 只记录事实，不评价基金是否值得买，不据用户成本或持仓盈亏提出加减仓建议。
- 不将余额宝账户总余额和基金份额重复计为两份资产。
- 不把待确认赎回金额作为已到账现金，不把浮动估值当正式净值。
- 不更新 `domains/invest/holdings.md`（股票台账），不更改 `universe.json`（股票标的池）。
