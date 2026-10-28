# life-os

> 个人生涯操作系统 · **去敏模板仓库**

一套把饮食、运动、睡眠、饮水、身体指标、投资等数据统一沉淀到 Git 仓库的 Agent 工作流框架。你只负责「发内容」（照片、截图、一句话），Agent 负责识别、解析、结构化、汇总、入库、可视化。

**本仓库只含方法论与骨架，无任何真实个人数据。** 所有数值均为占位符或随机示例。详见 [PRIVACY.md](PRIVACY.md)。

## 这是什么

life-os 不是软件，而是一套**约定 + Skill 集合**：

- 约定数据怎么存（`schema/`）、放哪（`domains/`）、怎么规范化（`scripts/`）。
- Skill 是 Agent 的能力单元（`skills/`），每个 `SKILL.md` 描述「收到什么 → 怎么做 → 产出什么」。
- 使用者克隆后，填入自己的数据，由一个长期运行的 Agent 驱动。

## 快速开始

```bash
git clone https://github.com/cheriechen40/life.git
cd life

# 1. 建自己的数据目录（已 gitignore，不会误提交）
mkdir -p domains/health/data/{meals,workouts,sleep,water,body_comp}

# 2.（可选）建个人健康档案
cp skills/yangsheng-health/references/personal-profile.template.md \
   skills/yangsheng-health/references/personal-profile.md

# 3. 把 skills/ 目录挂到你的 Agent（如 Knot / Claude / Cursor）

# 4. 发一张餐食照片给 Agent，看它入库
```

查看面板：把 `dashboard/data.sample.js` 复制为 `dashboard/data.js`，双击 `dashboard/index.html` 即可（单文件、无后端、无需构建）。

## 我要做什么 → 找谁

| 我想…… | 直接说 / 发 | 触发 Skill |
| --- | --- | --- |
| 记一顿饭 | ［餐食照片］ | `meal-nutrition` |
| 记一次训练 | ［运动记录截图］ | `workout-parse` |
| 记睡眠 | ［睡眠报告截图］ | `sleep-parse` |
| 记体成分 | ［InBody 报告］ | `body-comp` |
| 记喝水 | 「我喝了 2 杯水」 | `water-log` |
| 记体检 / 检验报告 | ［体检报告］ | `medical-report` |
| 回填历史数据 | ［Apple 健康导出包］ | `health-import` |
| 问体质 / 养生调理 | 「我是不是湿气重」 | `yangsheng-health` |
| 记持仓 / 成交 | ［券商持仓截图］ | `invest-router` |
| 记基金 | ［基金持仓截图］ | `fund-router` |
| 要投资简报 | 「生成今日简报」 | `invest-morning` |
| 复盘交易 | 「复盘本周」 | `invest-review` |
| 复盘训练 | 「复盘训练」 | `training-review` |
| 问人生决策 | 「该不该 / 值不值」 | `life-guide` |
| 看今天汇总 | 「生成今天的日报」 | `report-daily` |
| 看趋势 | 「生成周报 / 月报」 | `report-periodic` |
| 看图表 | 打开 `dashboard/index.html` | `dashboard` |

> 不必手动指定 Skill，直接发内容，`capture-router` 会判断领域并分发。全部索引见 [`skills/README.md`](skills/README.md)。

## 目录结构

```
life/
├── skills/                  # Skill 集合，一目录一 Skill（扁平）
│   ├── README.md            # 总索引
│   ├── capture-router/      # 统一入口：识别类型 → 分发
│   ├── meal-nutrition/ workout-parse/ sleep-parse/ body-comp/
│   ├── water-log/ medical-report/ health-import/ training-review/
│   ├── invest-router/ invest-position/ invest-note/
│   ├── invest-morning/ invest-review/ stock-research/
│   ├── fund-router/ fund-position/ fund-note/ fund-research/
│   ├── life-guide/ report-daily/ report-periodic/ dashboard/
│   └── career-*/ reading-log/ habit-tracker/ reflection-log/   # 规划中
├── domains/                 # 数据存放地（空骨架，真实数据 gitignore）
│   ├── health/data/         # meals workouts sleep naps water body_comp …
│   ├── invest/data/         # positions trades notes reviews watchlist
│   └── lifeguide/ career/ growth/
├── schema/                  # 数据结构定义
│   └── data-schema.md       # 统一结构（含各域 type）
├── scripts/                 # 运维脚本
│   ├── repo-root.sh         # 环境无关定位仓库根
│   ├── normalize_health_data.py
│   ├── normalize_invest_data.py
│   └── normalize_fund_data.py
├── dashboard/
│   ├── index.html           # 单文件面板，双击可开
│   └── data.sample.js       # 示例数据（假数据，仅演示）
├── examples/                # 使用示例
├── automations/             # 定时任务提示词（预留）
├── PRIVACY.md               # 隐私声明
└── README.md
```

## 设计理念

- **Skill 集中管理**：`skills/` 下一目录一 Skill，结构 `SKILL.md` + 可选 `references/` `scripts/` `assets/`；目录保持扁平，保证自动发现稳定。
- **数据按领域分域**：`domains/` 只管「数据落在哪」，新增领域不影响既有 Skill。
- **记录型与知识型分开**：记录型按天累积、走统一 schema、跑规范化脚本（如 `meal-nutrition`）；知识型只检索引用、不按天记录（如 `life-guide`）。
- **记录型与咨询型分开**：记录型写数据，咨询型只读不写，不污染数据文件。
- **统一 schema**：时间戳 + 领域标识 + 指标结构，加新领域时报表与面板无需改代码。
- **只入库结构化数据**：照片 / 截图仅作解析输入，本地归档不进仓库。
- **路径环境无关**：路径相对「仓库根」书写；需绝对路径时用 `scripts/repo-root.sh` 推导。

## 数据 schema

```json
{
  "date": "2025-01-01",
  "time": "08:30",
  "domain": "health",
  "type": "meal",
  "metrics": { "calories": 480, "protein_g": 30, "carbs_g": 55, "fat_g": 14 },
  "note": "早餐：示例",
  "source": "data/raw/2025-01-01/meal_breakfast.jpg",
  "created_at": "2025-01-01T08:35:00+08:00"
}
```

按月分文件：`domains/<domain>/data/<type>/<YYYY-MM>.json`。完整定义见 [`schema/data-schema.md`](schema/data-schema.md)。

## 规范化与自动化

```bash
python3 scripts/normalize_health_data.py      # 健康数据 + 生成看板数据包
python3 scripts/normalize_invest_data.py      # 股票 / 场内证券
python3 scripts/normalize_fund_data.py        # 场外基金
python3 scripts/normalize_health_data.py --check   # 只审计不改
./scripts/sync.sh "chore: daily sync"         # 提交并推送
```

定时任务提示词放 `automations/`：建议每日 22:30 日报、每周日 22:00 周报、每月末 22:00 月报、每日 09:00 投资晨间简报。

> 分工：提示词只写调度与落盘，分析方法论一律由对应 Skill 提供。

## 扩展新领域

- **记录型**（按天累积）：`domains/<新域>/data/` 建目录 → 新增记录型 Skill → `schema/data-schema.md` 补 `type` → 按需接入报表 / 面板。
- **知识型**（外部资料提炼）：参照 `lifeguide`，自建 `schema.md` + `INDEX.md` + `data/index.json`，由专属 Skill 检索并标注出处，不进统一 schema、不接面板。

新增后同步三处：`skills/README.md` 索引、`domains/<域>/README.md`、根 README 的「我要做什么 → 找谁」表。

## 与原始实例的关系

本仓库由一份真实使用的 life-os 实例去敏而来：剥离全部真实数据、个人档案、内部食堂与菜品库、第三方版权资料，保留方法论与结构。

- `canteen-advisor`（食堂点餐）依赖企业内部食堂与菜品数据，**不包含在本模板中**；如需使用，请按 `schema/` 自建数据并参照其他 Skill 编写。
- `social-situations-guide`（人情世故）依赖第三方版权资料，**不包含在本模板中**。

## 隐私

本仓库不含任何真实个人数据，详见 [PRIVACY.md](PRIVACY.md)。克隆后你自己的真实数据请勿提交回公开仓库。

## 免责声明

健康与投资相关内容仅供个人记录与方法论参考，**不构成医学诊断、治疗建议或投资建议**。症状持续请就医；投资决策请自负风险。
