---
name: capture-router
description: life-os 的统一入口 Skill。当用户发来与个人记录相关的内容（餐食照片、运动记录截图、睡眠报告截图、券商或支付宝基金持仓截图、成交/申赎截图、研报、投资想法），或咨询明确的股票/基金资产时，由本 Skill 判断类型并分发到对应子 Skill。当前启用健康域、股票投资域与支付宝场外基金/黄金基金流程。
---

# capture-router

life-os 的统一捕捉入口。用户不需要关心"这条该存到哪"，凡是与个人记录相关的内容都先走这里。

## 触发场景

用户发来以下任意内容时应启用本 Skill：

- 一张餐食照片
- 一张运动记录截图（苹果健康 App / 手表）
- 一张睡眠报告截图
- 一张 InBody / 体成分分析报告照片
- 一张体检 / 检验检查报告（血常规、尿常规、肝肾功能、血脂、心电图、DR/CT/超声报告单）
- 一句饮水口述（「我喝了 x 杯水」/「刚喝了一瓶水」）或水瓶照片
- 一张券商持仓截图 / 成交交割单截图
- 一张支付宝场外基金/黄金基金持仓截图、申购或赎回截图
- 一段投资想法、研报、公司公告、行情截图或明确基金研究咨询

## 路由决策流程

0. **先判只查不记或明确资产意图**：
   - **健康意图优先**：若主体是餐食、运动、睡眠、体重、InBody 等健康问题，走健康域，不因“该不该/怎么选”等泛决策词误入 `life-guide`。
   - **养生咨询意图**：命中「体质 / 养生 / 调理 / 上火 / 湿气 / 气虚 / 怕冷 / 秋燥 / 失眠 / 多汗 / 食疗 / 药膳 / 节气 / 这算不算 xx 体质」等无附件的中医养生咨询 → 转交 `skills/yangsheng-health`（只辨证给建议，**不落库**）。
   - **明确股票或基金资产咨询优先于 life-guide**：问「这只股票买不买」→ `invest-router`；明确询问支付宝场外基金、基金名称/身份、余额宝/货币基金、QDII、FOF、黄金基金或黄金 ETF 联接 → `fund-router`；明确场内股票/ETF/LOF → `invest-router`。只说“黄金”或身份不清的 ETF 时交由对应路由澄清，不按代码前缀猜。
   - **一般人生决策咨询**：命中「该不该 / 值不值 / 要不要 / 划不划算 / 怎么选 / 帮我决定 / 这样犯法吗 / 能领什么 / 先做什么 / 性价比 / 是不是智商税 / 靠谱吗」，且无附件，也未指明基金或证券资产 → 转交 `skills/life-guide`，由它检索 `domains/lifeguide/` 并在回答末尾注明出处（第几节第几条）。例如「借钱给朋友该不该打借条」「虚拟货币能不能碰」走 `life-guide`。
1. **再判领域（domain）**，判定优先级如下 —— **健康主体优先于投资关键词**，防止持仓页截图里的步数等信息造成误判：
   - 命中**健康关键词**（餐食 / 卡路里 / 运动 / 训练 / 睡眠 / 体重 / InBody / 体成分 / 步数 / **饮水 / 喝水 / 杯水 / 水喝** / **体检 / 化验 / 检验 / 血常规 / 尿常规 / 肝功 / 肾功 / 尿酸 / 血脂 / 心电图 / X 光 / DR / CT / 超声 / 报告单**）→ `health`
   - 命中支付宝场外基金 / 余额宝 / 基金份额或净值 / QDII / FOF / 黄金基金 / 黄金 ETF 联接 → `invest`，转交 `skills/fund-router`。
   - 命中股票 / 场内 ETF 或 LOF 等证券类投资 → `invest`，转交 `skills/invest-router`。
   - “ETF / 黄金 / 基金”产品类型无法确认时，先向用户确认是场内证券、支付宝场外基金、账户金/积存金等哪类。
   - 两者都不命中 → 向用户确认，不猜测
2. 判断类型（type）：参考 `schema/data-schema.md` 中对应领域定义的 type。
3. 分发到对应子 Skill。

路由对照表（health 与 invest）：

| 用户发来的内容 | domain | type | 子 Skill |
| --- | --- | --- | --- |
| 餐食照片 | health | meal | meal-nutrition |
| 运动记录截图 | health | workout | workout-parse |
| 睡眠报告截图 | health | sleep | sleep-parse |
| InBody / 体成分报告 | health | body_comp | body-comp |
| 体检 / 检验检查报告（血常规、尿常规、肝肾功能、血脂、心电图、X 光等） | health | medical_report | **medical-report** |
| 饮水量口述 / 水瓶照片 | health | water | water-log |
| 支付宝场外基金 / 余额宝 / QDII / FOF / 黄金基金咨询或账户截图 | invest | fund_* | **fund-router** |
| 基金持仓快照 / 申购或赎回记录 | invest | fund_position / fund_trade | **fund-position**（由 fund-router 分发） |
| 基金研究咨询 / 明确要求保存的研究逻辑 | invest | — / fund_note | **fund-note**（由 fund-router 分发） |
| 股票 / 场内 ETF / LOF 持仓、成交、研究或复盘 | invest | position / trade / note / review | **invest-router** |

分发：

- `health/meal` → `skills/meal-nutrition`
- `health/workout` → `skills/workout-parse`
- `health/sleep` → `skills/sleep-parse`
- `health/body_comp` → `skills/body-comp`
- `health/medical_report` → `skills/medical-report`
- `health/water` → `skills/water-log`

> **饮水意图的两种分支**：用户在**陈述已喝**（「我喝了 3 杯水」）→ 落库；用户只是在**提问**（「我今天喝了多少水」「一天喝多少水合适」）→ `water-log` 只做汇总或给建议，**不落库**。

- 支付宝场外基金 / 黄金基金 → `skills/fund-router`，再到 `fund-position` / `fund-note`；研究方法由 `fund-research` 提供。
- 股票 / 场内 ETF / LOF → `skills/invest-router`，由其做股票侧二级分发。本 Skill 不重复实现投资域的业务逻辑。

> 股票方法论仅由 [`stock-research`](../stock-research/SKILL.md) 提供；基金方法论由 [`fund-research`](../fund-research/SKILL.md) 提供，两者不得互相套用。

## 体检 / 检验报告的特殊规则

- 一次体检常是**多张报告**（检验单 + 心电图 + 影像）：同一 `date` 下可写**多条** `medical_report`，按 `panel` / `modality` 区分，不合并。
- **读不到图时必须说**：若会话无法读取图片内容，明确告知用户，只记能确认的项，其余写 `null` 并在 `note` 列「待确认」，**严禁凭经验填数**（2025-MM-DD 事故教训）。
- 原始报告图片存 `data/raw/<日期>/`，不 commit；**身份信息（姓名 / 身份证号 / 病案号）一律不入库**。
- 解析后**不下医学诊断**，异常项一律提示由医生复核。

## 落库规则

1. 原始附件**只存本地**：保存到 `data/raw/<YYYY-MM-DD>/`，文件名格式 `<type>_<slot>_<时间戳>.<ext>`。该目录已被 `.gitignore` 排除，**解析完成后不 commit、不 push**（图片只用于解析取证，入库对象是结构化数据）。
2. 调用子 Skill 得到 `metrics`。
3. 按 `schema/data-schema.md` 组装完整记录对象。`source` 填原始附件的**本地相对路径**（仅本机可追溯），无附件时留空字符串，不要写成本地绝对路径或外链。
4. 追加写入 `domains/<domain>/data/<type>/<YYYY-MM>.json`（不存在则创建数组）。
5. 同一文件内按 `date` + `time` 排序，保证 diff 稳定：health 域由 `scripts/normalize_health_data.py` 保证；股票投资由 `scripts/normalize_invest_data.py` 保证；基金由 `scripts/normalize_fund_data.py` 保证。基金脚本只扫描 `fund_*` 类型目录。
6. 提交前确认只纳入本次相关的 Schema / Skill / `domains/` / 脚本文件，不含 `data/raw/`；不要因基金记录变更而改动股票数据。

## 日记录与月度导出包

- 餐饮（meal）单独维护、随时记录，导出包不含，以日常记录为准。
- 睡眠 / 训练（sleep、workout）日常截图属**临时记录**，先落库保证当天可见。
- 每月用户发来 Apple 健康导出包后，由 `health-import` 用完整数据**覆盖更新对应月份**（睡眠 / 运动 / 每日指标），并把截图记录替换为完整值。覆盖时保留截图补录的 `body_parts` / `exercises` / `circuit`。
- 因此日常记录不必追求字段齐全，缺的字段交给月度导出包补齐。

## 输出确认

解析完成后，向用户简短回报：识别到的领域、类型、关键指标、写入的文件路径。不要输出冗长的原始 JSON，除非用户要求。

## 提交约定

- 原始附件不入库。若 `git status` 中出现 `data/raw/`，说明规则被绕过，先修 `.gitignore` 再提交。
- 提交信息沿用常规提交格式（如 `data(health): 记录 2025-10-10 训练与早餐`），不携带附件。

## 注意事项

- 无法确定类型时，先向用户确认，不要猜测落库。
- 同一餐可能多次拍摄，以 `meal_slot` + `time` 区分，不要覆盖已有记录。
- 所有时间戳使用本机时区（+08:00）。
- **股票侧投资分发前必须做证券标的池校验**（读 `domains/invest/universe.json`）：命中 deny 前缀直接拒绝，不得进入股票子 Skill。支付宝场外基金与黄金基金改读 `domains/invest/fund_universe.json` 核对产品身份；不得套用股票前缀白名单、不得调用股票行情接口。
- 职业域（career）与成长域（growth）当前已搁置，暂不分发；相关设计保留在 `domains/career`、`domains/growth`，待后续需求启用。