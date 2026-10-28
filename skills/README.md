# skills 索引

life-os 的全部 Skill 集中在本目录，**一目录一个 Skill**，结构统一为 `SKILL.md` + 可选 `references/` / `scripts/` / `assets/`。

> 目录保持**扁平**（不按领域再分层），以确保 `skills/*/SKILL.md` 这一自动发现约定对所有工具稳定生效。领域归属通过下方分组与命名前缀体现。

## 总入口

| Skill | 作用 |
| --- | --- |
| [capture-router](capture-router/SKILL.md) | 统一入口：识别内容类型 → 分发到对应子 Skill（含健康 / 投资 / 人生决策 / 养生分支） |

## 健康域

**记录型**（写入 `domains/health/data/`，走规范化脚本）

| Skill | 输入 | 产出 |
| --- | --- | --- |
| [meal-nutrition](meal-nutrition/SKILL.md) | 餐食照片 | 热量与三大营养素 |
| [workout-parse](workout-parse/SKILL.md) | 运动记录截图 | 运动结构化数据（含训练明细） |
| [sleep-parse](sleep-parse/SKILL.md) | 睡眠报告截图 | 睡眠结构数据 |
| [body-comp](body-comp/SKILL.md) | InBody 体成分报告 | 身体成分数据（含节段） |
| [medical-report](medical-report/SKILL.md) | 体检 / 检验检查报告（血常规、尿常规、肝肾功能、血脂、心电图、X 光等） | 逐项数值 + 参考范围 + 异常标注（**不下医学诊断**） |
| [water-log](water-log/SKILL.md) | 饮水口述 / 水瓶照片 | 饮水量记录 |
| [health-import](health-import/SKILL.md) | Apple 健康导出包 | 批量回填运动 / 睡眠 / 每日指标 |

**咨询型**（只读不写，不落库）

| Skill | 输入 | 产出 |
| --- | --- | --- |
| [yangsheng-health](yangsheng-health/SKILL.md) | 身体自评 / 体质辨识 / 四季养生 | 体质判定 + 饮食起居方案（内置个人档案） |
| [training-review](training-review/SKILL.md) | 「复盘训练」/ 每周日定时 | 周训练容量 / 频次 / 肌群三问复盘，排期调整建议须用户批准后落盘 |

## 投资域

**股票 / 场内证券**

| Skill | 作用 |
| --- | --- |
| [invest-router](invest-router/SKILL.md) | 股票侧二级路由 |
| [invest-position](invest-position/SKILL.md) | 持仓台账 + positions / trades |
| [invest-note](invest-note/SKILL.md) | 研究笔记 + 单标的深度报告 |
| [invest-morning](invest-morning/SKILL.md) | 晨间投资决策简报 |
| [invest-review](invest-review/SKILL.md) | 复盘记录 + 周期报 |
| [stock-research](stock-research/SKILL.md) | 方法论核心：框架 / SOP / 模板 / 合规铁律 |

**支付宝场外基金 / 黄金基金**

| Skill | 作用 |
| --- | --- |
| [fund-router](fund-router/SKILL.md) | 基金二级路由（判断产品身份） |
| [fund-position](fund-position/SKILL.md) | 基金台账 + fund_positions / fund_trades |
| [fund-note](fund-note/SKILL.md) | 基金研究咨询与按需落笔记 |
| [fund-research](fund-research/SKILL.md) | 方法论核心：分类 / 框架 / 费率口径 |

## 知识域

| Skill | 作用 |
| --- | --- |
| [life-guide](life-guide/SKILL.md) | 人生决策咨询：检索 `domains/lifeguide/` 并带出处作答 |

## 汇总类（跨域）

| Skill | 作用 |
| --- | --- |
| [report-daily](report-daily/SKILL.md) | 聚合当天数据 → `data/daily/<日期>.md` |
| [report-periodic](report-periodic/SKILL.md) | 周报 / 月报 → `reports/health/{weekly,monthly}/` |
| [dashboard](dashboard/SKILL.md) | 读取仓库 JSON，渲染可交互面板 |

## 规划中（未启用）

| 域 | Skill |
| --- | --- |
| 职业 career | [career-milestone](career-milestone/SKILL.md) · [career-project](career-project/SKILL.md) · [career-review](career-review/SKILL.md) |
| 成长 growth | [reading-log](reading-log/SKILL.md) · [habit-tracker](habit-tracker/SKILL.md) · [reflection-log](reflection-log/SKILL.md) |