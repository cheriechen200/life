# 数据 Schema 规范

本仓库所有领域的数据都遵循统一结构。目的：加新领域时，报表 Skill 与可视化面板无需改代码。

## 通用记录结构

每条记录是一个 JSON 对象：

```json
{
  "date": "2025-10-09",
  "time": "08:30",
  "domain": "health",
  "type": "meal",
  "metrics": {},
  "note": "",
  "source": "data/raw/2025-10-09/meal_breakfast.jpg",
  "created_at": "2025-10-09T08:35:00+08:00"
}
```

字段说明：

| 字段 | 必填 | 说明 |
| --- | --- | --- |
| `date` | 是 | 记录归属日期，`YYYY-MM-DD` |
| `time` | 否 | 发生时间，`HH:mm` |
| `domain` | 是 | 领域标识：`health` / `invest` / `career` / `growth` |
| `type` | 是 | 记录类型，见下方各领域定义 |
| `metrics` | 是 | 结构化指标对象，字段随 type 变化 |
| `note` | 否 | 自然语言备注 |
| `source` | 否 | 原始附件的**本地相对路径**（`data/raw/` 仅本地归档、不入库；无附件时留空字符串） |
| `created_at` | 是 | 入库时间戳，ISO 8601 带时区 |

## 存储位置

数据按月分文件，降低单文件体积、便于 diff：

```
domains/<domain>/data/<type>/<YYYY-MM>.json
```

例如：`domains/health/data/meals/2025-10.json`

每个文件的根结构是一个数组：

```json
[
  { "date": "...", "domain": "health", "type": "meal", "metrics": {}, ... },
  { "date": "...", "domain": "health", "type": "meal", "metrics": {}, ... }
]
```

## 数据来源与覆盖规则

同一份数据可能有两个来源，需明确权威方：

| 类型 | 日常记录 | 月度导出包 | 权威方 |
| --- | --- | --- | --- |
| `meal` | 随时记录，单独维护 | 不含 | 日常记录 |
| `workout` | 截图临时记录 | 完整训练数据 | 导出包 |
| `sleep` | 截图临时记录 | 完整睡眠数据 | 导出包 |
| `daily_metrics` | 不记录 | 每日基础指标 | 导出包 |
| `body_comp` | InBody 报告解析 | 不含 | 日常记录 |
| `medical_report` | 体检 / 检验报告解析 | 不含 | 日常记录（报告原件） |

- 日常截图属临时记录，先落库保证当天可见。
- 每月 Apple 健康导出包到达后，覆盖更新对应月份；`workout` 按 `(date, time)` 覆盖、`sleep` / `daily_metrics` 按 `date` 覆盖。
- 覆盖时保留导出包无法提供的手动字段：`body_parts` / `exercises` / `circuit`。
- 导入水位记录在 `domains/health/.import_state.json`，用于增量解析（详见 `skills/health-import`）。

## health 领域

### type = meal（餐食）

```json
{
  "metrics": {
    "meal_slot": "breakfast",
    "calories": 520,
    "protein_g": 32,
    "carbs_g": 60,
    "fat_g": 14,
    "fiber_g": 6,
    "sodium_mg": 780,
    "balance_score": 8,
    "comment": "蛋白质达标，碳水以全麦为主，脂肪略高"
  }
}
```

`meal_slot` 取值：`breakfast` / `lunch` / `dinner` / `snack`。

### type = workout（运动）

```json
{
  "metrics": {
    "activity": "strength_training",
    "duration_min": 60,
    "calories_burned": 420,
    "avg_heart_rate": 128,
    "max_heart_rate": 162,
    "distance_km": null,
    "intensity": "moderate",
    "body_parts": ["back", "biceps", "triceps"],
    "exercises": [
      { "name": "seated_cable_row", "name_cn": "坐姿划船", "weight_kg": 40, "sets": 4, "reps": 12, "equipment": "cable" },
      { "name": "dumbbell_bicep_curl", "name_cn": "哑铃弯举", "weight_kg": 10, "sets": 2, "reps": 5, "unilateral": true, "equipment": "dumbbell" }
    ]
  }
}
```

`exercises`（训练明细，可选）：每个元素描述一个动作。

| 字段 | 必填 | 说明 |
| --- | --- | --- |
| `name` | 是 | 稳定英文标识（动作命名表见 `skills/workout-parse/SKILL.md`） |
| `name_cn` | 是 | 中文动作名 |
| `weight_kg` | 否 | 负重 kg；单侧负重填单侧值并置 `unilateral: true` |
| `sets` | 是 | 组数 |
| `reps` | 是 | 每组次数 |
| `unilateral` | 否 | 是否单侧交替，默认 false |
| `equipment` | 否 | `cable` / `dumbbell` / `barbell` / `machine` / `bodyweight` |
| `depth` | 否 | 深蹲 / 腿举类幅度：`above_parallel`（半蹲）/ `at_parallel` / `at_or_below_parallel`（标准深度）。影响重量可比性，采集深蹲时应问清 |
| `belt` | 否 | 腰带：`none` / `all` / `partial`；`partial` 时在 `note` 写清哪几组使用。带与不带是两条不同的力量曲线，不可混比 |
| `note` | 否 | 动作名存疑等说明 |

循环 / 间歇训练的动作由 `circuit` 统一给出组次与节奏，`exercises` 内的动作可不填 `sets` / `reps` / `weight_kg`。

循环 / 间歇训练用 `circuit` 描述节奏：

```json
{
  "circuit": { "rounds": 6, "work_sec": 50, "rest_sec": 10, "exercises": ["crunch", "leg_raise"] },
  "exercises": [
    { "name": "crunch", "name_cn": "卷腹", "equipment": "bodyweight" }
  ]
}
```

`body_parts` 取值：`back` / `chest` / `shoulder` / `biceps` / `triceps` / `legs` / `abs` / `core` / `glutes`。

`activity` 示例：`strength_training` / `running` / `cycling` / `swimming` / `yoga` / `walking` / `hiit`。
`intensity` 由平均心率推导：< 100 为 `low`，100-139 为 `moderate`，≥ 140 为 `high`。
`body_parts` 由 Apple Health 无法提供，需用户手动补充。

`activity` / `intensity` 在数据文件中一律存英文原值，看板展示时映射为中文（映射表见 `skills/workout-parse/SKILL.md`），保证数据口径统一、展示可读。空 `intensity` 展示为「未记录」，未知 `activity` 展示为「其他」。

### type = sleep（睡眠）

```json
{
  "metrics": {
    "sleep_start": "23:15",
    "sleep_end": "07:00",
    "total_min": 465,
    "deep_min": 95,
    "light_min": 280,
    "rem_min": 90,
    "awake_min": 12,
    "sleep_score": 85,
    "comment": "深睡占比良好，入睡稍晚"
  }
}
```

### type = nap（午休 / 短时睡眠，2025-MM-DD 新增）

与 `sleep` 分开存放：**`sleep` 只记夜间主睡眠**（date 取起床日），午休单独走 `nap`，避免两者争抢同一 `date` 槽位、也避免被导出包按日覆盖。

```json
{
  "date": "2025-MM-DD",
  "time": "13:30",
  "domain": "health",
  "type": "nap",
  "metrics": {
    "nap_start": "13:30",
    "nap_end": "14:00",
    "duration_min": 30,
    "source_kind": "self_report",
    "comment": "控制在 30 分钟内，避免进入深睡"
  }
}
```

| 字段 | 必填 | 说明 |
| --- | --- | --- |
| `nap_start` / `nap_end` | 是 | 起止时间 `HH:mm`；计划值时在 `note` 注明「计划，待修正」 |
| `duration_min` | 是 | 时长（分钟） |
| `source_kind` | 否 | `self_report`（自报）/ `device`（设备记录） |
| `comment` | 否 | 说明 |

### type = daily_metrics（每日基础指标）

由 Apple Health 导出批量导入。每日一条，聚合当天各来源数据。

```json
{
  "metrics": {
    "steps": 8420,
    "active_energy_kcal": 620,
    "basal_energy_kcal": 1580,
    "resting_heart_rate": 58,
    "hrv_sdnn_ms": 42,
    "vo2max": 46.2,
    "weight_kg": 68.5,
    "exercise_min": 45,
    "distance_km": 6.2,
    "spo2_pct": 0.97,
    "respiratory_rate": 15.2,
    "wrist_temp_c": 35.6,
    "water_ml": 2400
  }
}
```

字段按当日是否有数据动态存在，缺失字段不出现。

`water_ml`：**可选**，表示当天来自 Apple 健康导出包的饮水总量（Apple Health 的 Dietary Water）。**仅在导出包提供时写入，不作为日常饮水记录的载体**——日常饮水走下面的 `type = water`。原因是 `daily_metrics` 每月会被导出包按 `date` 覆盖，若把手工记录写在这里会被冲掉。

### type = water（饮水，2025-MM-DD 新增）

一天内多次记录，每次一条。用于跟踪饮水量达标情况（用户服用肌酸 5 g/天，需保证充足饮水）。

```json
{
  "date": "2025-MM-DD",
  "time": "09:30",
  "domain": "health",
  "type": "water",
  "metrics": {
    "amount_ml": 700,
    "container_ml": 700,
    "containers": 1.0,
    "source_type": "manual",
    "comment": "办公室杯 1 杯，上午第一杯"
  },
  "note": "",
  "source": "",
  "created_at": "2025-MM-DDT09:30:00+08:00"
}
```

| 字段 | 含义 |
| --- | --- |
| `amount_ml` | 本次饮水量（ml），**必填** |
| `container_ml` | 容器容量（ml），用于换算杯数；已知容器时填写 |
| `containers` | 折合杯数 = `amount_ml / container_ml`，可含小数 |
| `source_type` | `manual`（口述/手动）/ `photo`（照片）/ `apple_health`（导出包） |

存储路径：`domains/health/data/water/<YYYY-MM>.json`。

**已知容器容量**：办公室杯 **700 ml**（2025-MM-DD 用户更正，原记 550 ml 有误）、标准矿泉水瓶 550 ml、一次性纸杯约 250 ml（待确认）、美式咖啡一杯约 350 ml（待确认）。

**口径**：记录的是**饮品**（白水、茶、咖啡、汤不算饮品而算食物含水）。食物含水约 600 ml/天，不逐条记录，仅在统计全天总量时按常量补上。目标值见 `reports/health/topics/饮水方案_2025-MM-DD.md`：**训练日饮品 2500 ml / 休息日 2100 ml**。

### type = body_comp（身体成分）

由 InBody 等人体成分分析仪报告解析而来，用于跟踪体成分长期变化。

```json
{
  "metrics": {
    "device": "InBody270",
    "serial_no": "3316899160",
    "height_cm": 179,
    "age": 21,
    "gender": "male",
    "weight_kg": 70.0,
    "skeletal_muscle_kg": 32.0,
    "body_fat_kg": 12.0,
    "body_fat_pct": 18.3,
    "bmi": 24.2,
    "whr": 0.91,
    "bmr_kcal": 1736,
    "visceral_fat_level": 5,
    "body_water_kg": 42.0,
    "lean_body_mass_kg": 58.0,
    "inbody_score": 80,
    "muscle_control_kg": 0.0,
    "fat_control_kg": -3.0,
    "target_weight_kg": 68.0,
    "recommended_intake_kcal": 2901,
    "segmental_muscle": { "left_arm_kg": 3.74, "right_arm_kg": 3.77, "trunk_kg": 29.0, "left_leg_kg": 10.85, "right_leg_kg": 10.99 },
    "segmental_fat": { "left_arm_kg": 0.6, "right_arm_kg": 0.6, "trunk_kg": 7.6, "left_leg_kg": 2.0, "right_leg_kg": 2.1 }
  }
}
```

`gender`：`male` / `female`。体脂百分比与腰臀比填报告原始数值（18.3 表示 17.0%）。`muscle_control_kg` / `fat_control_kg` 保留正负号语义（正值为建议增加，负值为建议减少）。`segmental_muscle` / `segmental_fat` 仅在报告提供时出现。字段按报告实际提供动态存在，缺失字段不出现。

### type = medical_report（体检 / 检验检查报告，2025-MM-DD 新增）

由体检中心或医院的检验单、检查报告解析而来（血常规、尿常规、生化肝肾功能、血脂、心电图、影像报告等），用于建立个人检验基线并做长期趋势对比。

```json
{
  "date": "2025-MM-DD",
  "time": "09:30",
  "domain": "health",
  "type": "medical_report",
  "metrics": {
    "exam_date": "2025-MM-DD",
    "institution": "",
    "checkup_type": "annual_checkup",
    "fasting": true,
    "panels": [
      {
        "panel": "lipid",
        "name_cn": "血脂",
        "items": [
          { "name": "hdl_c", "name_cn": "高密度脂蛋白胆固醇", "value": 1.0, "unit": "mmol/L",
            "ref_low": 1.04, "ref_high": 1.55, "ref_text": "1.04-1.55", "flag": "low", "comment": "" }
        ]
      }
    ],
    "findings": [
      { "modality": "ecg", "name_cn": "常规心电图",
        "fields": { "rhythm": "窦性心律", "hr_bpm": 62, "qtc_ms": 410 },
        "impression": "（报告结论原文摘录，不改写）" }
    ],
    "abnormal": [
      { "panel": "lipid", "name_cn": "高密度脂蛋白胆固醇", "value": 1.0, "unit": "mmol/L",
        "ref_text": "1.04-1.55", "flag": "low" }
    ],
    "summary": { "item_count": 1, "abnormal_count": 1, "high": 0, "low": 1, "unknown": 0 },
    "comment": ""
  },
  "note": "",
  "source": "",
  "created_at": "2025-MM-DDT11:40:00+08:00"
}
```

| 字段 | 含义 |
| --- | --- |
| `exam_date` | 检查（采样）日期，报告印刷值为准 |
| `checkup_type` | `annual_checkup`（年度体检）/ `outpatient`（门诊复查）/ `screening`（单项筛查） |
| `fasting` | 是否空腹采血，影响 TG、血糖解读 |
| `panels[].panel` | 分组：`blood_routine` / `urine` / `renal` / `liver` / `lipid` / `ophthalmology` / `imaging` / `other` |
| `items[].name` | 稳定英文标识（清单见 `skills/medical-report/SKILL.md`），用于长期趋势比对 |
| `items[].flag` | `low` / `normal` / `high` / `critical_low` / `critical_high` / `unknown`；参考范围缺失或未拿到数值时一律 `unknown` |
| `findings` | 文本型结论（心电图、影像「所见 / 印象」），**原文摘录不改写** |
| `abnormal` | `flag` 非 `normal` 的项汇总，供日报与看板直接读 |
| `summary` | 项数与各 `flag` 计数 |

存储路径：`domains/health/data/medical/<YYYY-MM>.json`。

口径与边界：**只做数值整理与异常标注，不下医学诊断**；影像结论一律以放射科 / 超声报告原文为准；异常项提示由医生复核；**姓名、身份证号、病案号等身份信息一律不入库**。数值不可辨认时留空并在 `note` 标「待确认」，严禁凭经验填数。解读时必须套用本人画像口径（在服肌酸会使血清肌酐假性升高、高蛋白饮食升高尿素氮、力量训练后 24–72h 可升高 AST/CK），详见 `skills/medical-report/SKILL.md`。长文解读放 `reports/health/topics/体检解读_<YYYY-MM-DD>.md`。

## career 领域（规划中，暂未启用）

> 本节为设计草案，当前项目仅启用健康域，career 与 growth 的采集与面板暂未接入。

### type = milestone（里程碑）

职业轨迹上的关键坐标：晋升、获奖、重要交付、Offer、外部认可。

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

`category`：`promotion` / `award` / `delivery` / `offer` / `recognition` / `other`。
`impact`：`high` / `medium` / `low`。

### type = project（项目推进）

同一项目可在不同时间点反复记录，形成进度快照。

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

`status`：`planning` / `in_progress` / `blocked` / `done` / `paused`。
`role`：`owner` / `contributor` / `reviewer` / `support`。

### type = review（目标与复盘）

`mode=goal` 记录目标设定，`mode=review` 记录阶段复盘。

```json
{
  "metrics": {
    "mode": "goal",
    "title": "2026 年内晋升到技术专家",
    "category": "promotion",
    "horizon": "2026-Q4",
    "status": "on_track",
    "key_results": ["主导 1 个核心项目", "拿到 1 次高绩效"]
  }
}
```

```json
{
  "metrics": {
    "mode": "review",
    "period": "2026-Q3",
    "went_well": ["完成 life-os 立项"],
    "gap": ["对外影响力不足"],
    "next_action": ["每月输出 1 篇技术文章"]
  }
}
```

`category`：`promotion` / `skill` / `influence` / `leadership` / `direction` / `other`。
`status`：`on_track` / `at_risk` / `off_track` / `done`。

## growth 领域

### type = reading（阅读）

```json
{
  "metrics": {
    "title": "《深度工作》",
    "author": "Cal Newport",
    "pages": 60,
    "minutes": 45,
    "progress_pct": 40,
    "highlights": ["深度工作的稀缺性正在成为核心竞争力"],
    "rating": null
  }
}
```

### type = habit（习惯打点）

同一天同一习惯只保留一条记录，重复打卡执行更新。

```json
{
  "metrics": {
    "habit": "meditation",
    "done": true,
    "streak_days": 12,
    "month_rate": 0.8,
    "note": ""
  }
}
```

`habit` 使用稳定英文标识：`meditation` / `reading` / `exercise` / `early_rise` / `no_sugar` / `journaling` 等。

### type = reflection（反思）

```json
{
  "metrics": {
    "theme": "关于工作节奏的反思",
    "mood": "calm",
    "action_intent": "试着每天留出 1 小时不被打扰的时间",
    "tags": ["work", "focus"]
  }
}
```

`mood`：`positive` / `calm` / `mixed` / `low` / `anxious`。

## invest 领域（投资 · 股票与场外基金）

`invest` 是统一投资域，但股票 / 场内 ETF 与支付宝场外基金使用不同的 type、字段、路由和规范化脚本。不得因同域而混用代码规则、交易成本或行情接口。板块显示名「投资」，域标识 `invest` 与 `health` / `career` / `growth` 同层。

领域配置见 [`domains/invest/universe.json`](../domains/invest/universe.json)（标的池前缀白 / 黑名单），产出规范见 [`skills/stock-research/`](../skills/stock-research/SKILL.md)。

### type = position（持仓快照）

每日一条，记录当日收盘时的持仓状态。**同一天同一 `symbol` 只保留一条**，重复执行更新而非追加。

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

| 字段 | 必填 | 说明 |
| --- | --- | --- |
| `symbol` | 是 | 带市场前缀代码：`sh600000` / `sz000001` |
| `name` | 是 | 标的名称 |
| `asset_type` | 是 | `stock` / `etf` |
| `shares` | 是 | 持仓数量；ETF 为份额，股票为股数 |
| `cost_price` | 否 | 成本价。**未经用户确认时不得填，且不得据此驱动加减仓建议** |
| `close_price` | 是 | 当日收盘价 |
| `market_value` | 是 | 市值 = shares × close_price |
| `pnl` / `pnl_pct` | 否 | 浮动盈亏额 / 百分比，缺成本价时省略 |
| `weight_pct` | 否 | 占组合总资产百分比 |
| `action` | 是 | 当日建议动作，见下方行动分类 |
| `stop_loss` | 否 | 止损 / 移动止盈参考位 |

`action` 取值：`buy`（买入）/ `add`（加仓）/ `hold`（持有）/ `reduce`（减仓）/ `clear`（清仓）/ `watch`（观察）/ `avoid`（回避）。

### type = trade（成交记录）

```json
{
  "date": "2025-MM-DD",
  "time": "15:00",
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
  "note": "",
  "source": "",
  "created_at": "2025-MM-DDT16:40:00+08:00"
}
```

| 字段 | 必填 | 说明 |
| --- | --- | --- |
| `side` | 是 | `buy` / `sell` |
| `shares` | 是 | 成交数量 |
| `price` | 是 | 成交均价 |
| `amount` | 是 | 成交金额 = shares × price |
| `fee` | 是 | 手续费（元） |
| `fee_pct` | 是 | **手续费占成交金额百分比**。小额账户的关键约束字段，缺此字段无法回溯该笔交易是否划算 |
| `reason` | 是 | 成交理由，必须引用具体数据，禁止"好公司便宜"式泛论 |
| `plan_ref` | 否 | 关联的决策文档相对路径 |

> 费率约束（当前账户口径）：单笔佣金 5 元固定。**单笔金额 ≥1,000 元**（`fee_pct ≤ 0.5%`）为红线，≥2,000 元为理想，**<500 元禁止下单**。股票卖出另加印花税 0.05%，ETF 免征。

### type = note（研究笔记）

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

| 字段 | 必填 | 说明 |
| --- | --- | --- |
| `thesis` | 是 | 核心论点一句话 |
| `catalyst` | 否 | 催化剂列表，每条带日期 |
| `kill_criteria` | 是 | **证伪条件**。写不出证伪条件 = 研究深度不足 |
| `valuation` | 否 | `pe_ttm` / `pb` / `div_ttm_pct`，缺失字段不出现 |
| `technical` | 否 | `ma_bull`（均线是否多头）/ `rsi6` / `pct_52w`（52 周价格分位） |
| `rating` | 是 | `buy` / `hold` / `sell` |
| `position_cap_pct` | 否 | 建议仓位上限（占组合百分比） |
| `stop_loss` | 否 | 止损参考位 |
| `brief_ref` | 否 | 关联深度报告相对路径 |

### type = review（复盘）

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
`process_score`：1–10，**评价决策过程质量而非盈亏结果**，避免用结果倒推过程。

### type = watchlist（观察池变动）

```json
{
  "date": "2025-MM-DD",
  "domain": "invest",
  "type": "watchlist",
  "metrics": {
    "symbol": "sz002594",
    "name": "比亚迪",
    "action": "avoid",
    "reason": "主力 20 日净流出 20.28 亿 + 碳酸锂期货跌超 11% + 出口退税率 13%→9%",
    "trigger": "跌破 80 且主力 20 日转正",
    "removed": false
  },
  "note": "",
  "source": "",
  "created_at": "2025-MM-DDT16:20:00+08:00"
}
```

`action` 同 `position.action`。`trigger` 为状态变更触发条件。`removed`：`true` 表示已移出观察池（如违反标的池合规）。

### 数据来源与覆盖规则

| 类型 | 权威方 | 说明 |
| --- | --- | --- |
| `position` | 券商账户 | 以用户券商 App 持仓页为准；每日收盘后一条 |
| `trade` | 券商交割单 | 手续费以实际交割单为准，`fee_pct` 由脚本计算 |
| `note` | 研究者判断 | 判断需标注依据来源与日期 |
| `review` | 研究者判断 | — |
| `watchlist` | `domains/invest/holdings.md` 观察池表 | **JSON 是 md 的投影**。改动先落 md，再反向同步 JSON；两者条目数必须一致 |

- **禁止编造数据**：取不到的数据写 `[MISSING]`，超过 90 天的写 `[STALE]`。
- **禁止用未经确认的成本 / 仓位驱动加减仓建议**：`cost_price` 缺失时，`pnl` / `pnl_pct` / `weight_pct` 一律省略。
- 财报口径数据以公司正式披露（定期报告、公告）为准，新闻稿与研报仅作线索，未经核对的推断标 `[假设]`。
- **观察池双写防漂移**：`holdings.md` 观察池为唯一权威方，`data/watchlist/*.json` 为其投影。任何一方改动后，必须核对「md 观察池行数 + 已移出行数 == JSON 中 `removed:false` 条数 + `removed:true` 条数」，不一致即为漂移，需反向补齐。曾因定稿后只补 md 未同步 JSON 而缺 7 只标的（2025-MM-DD）。
- 水位文件 `domains/invest/.brief_state.json` 记录已生成简报的日期，防止同日重复生成。

### 基金记录（支付宝场外基金与黄金基金）

基金记录仍使用通用 envelope（`date/time/domain/type/metrics/note/source/created_at`），存于 `domains/invest/data/<基金类型>/<YYYY-MM>.json`。原始截图只保存在被 `.gitignore` 排除的 `data/raw/`，`source` 仅填仓库内相对路径；外部网页和披露来源放入 `metrics.evidence`，不把外链塞入附件路径字段。

基金代码必须以**字符串**保存（如 `"000961"`），保留前导零；产品身份应由用户截图、基金公司/销售平台信息等确认证据建立，不能仅凭六位数字推断，也不得补 `sh` / `sz` 前缀后送入股票接口。`product_category` 仅取 `equity` / `bond` / `money_market` / `qdii` / `fof` / `gold_fund`。指数、混合等产品子类可另用 `product_subcategory` 记录，不取代类别。

写入任何基金持仓、交易或研究记录前，先把经核实产品登记到 `domains/invest/fund_universe.json` 的 `products` 数组，至少提供 `fund_code`（字符串）、`fund_name`、`platform=alipay`、`product_category`、`identity_verified=true` 和 `identity_source` 对象；可选 `aliases` 只收录有证据的页面名称。发生代码/名称冲突时不得覆盖目录，先澄清并保留冲突证据。独立 normalizer 会核对每条数据是否匹配此身份目录，不会因为代码符合六位格式就放行。

来源对象建议结构：`{"name":"来源名称","url":"https://...","published_at":"YYYY-MM-DD","as_of":"YYYY-MM-DD","metric":"指标/信息","source_level":"official|third_party|user_screenshot|user_statement"}`。缺少的值不填、不推算；无法核验时在 `note` 中标 `[待确认]`。

#### type = fund_position（基金持仓快照）

每日每只基金 / 份额类别 / 账户别名最多一条。持仓台账 `domains/invest/fund_holdings.md` 是人读当前状态，JSON 是按日期保留的快照历史。重复录入同日快照时更新对应键，不覆盖历史日期。

```json
{
  "date": "2025-MM-DD",
  "time": "15:30",
  "domain": "invest",
  "type": "fund_position",
  "metrics": {
    "fund_code": "000961",
    "fund_name": "天弘沪深300ETF联接A",
    "share_class": "A",
    "platform": "alipay",
    "product_category": "equity",
    "product_subcategory": "index",
    "status": "held",
    "shares": 1200.5,
    "cost_amount": 1500.0,
    "cost_nav": 1.2495,
    "latest_nav": 1.281,
    "nav_date": "2025-MM-DD",
    "market_value": 1537.84,
    "pnl": 37.84,
    "pnl_pct": 2.52,
    "account_alias": "支付宝主账户"
  },
  "note": "示例结构，非真实用户持仓；缺失字段不得照抄",
  "source": "data/raw/2025-MM-DD/fund_position_153000.png",
  "created_at": "2025-MM-DDT15:30:00+08:00"
}
```

| 字段 | 要求 | 说明 |
| --- | --- | --- |
| `fund_code` / `fund_name` | 必填 | `fund_code` 必须是字符串；禁止按股票代码前缀校验。 |
| `platform` / `product_category` | 必填 | 平台与类别须有证据；类别取上方枚举。 |
| `share_class` / `product_subcategory` | 可选 | 如 A/C 类、指数/混合；无法确认时省略。 |
| `status` | 必填 | `held` / `redeeming` / `closed`。 |
| `shares` | 可选 | 份额可为小数；只录账户显示值。 |
| `cost_amount` / `cost_nav` | 可选 | 以用户确认或账户展示为准；不从当前净值反推。 |
| `latest_nav` / `nav_date` | 可选 | 只有可验证正式净值时填写；有 `latest_nav` 必须同时有 `nav_date`。 |
| `market_value` / `pnl` / `pnl_pct` | 可选 | 可录用户页面值或按已确认数据计算；注明口径，不补估值。 |
| `account_alias` | 可选 | 非敏感自定义账户标识，不保存账号、手机号等个人信息。 |

示例数值仅用于说明字段结构，**不可当作真实数据入库**。`market_value` 与盈亏字段如由持仓份额、净值计算，需保证对应 `nav_date` 一致；估算净值不作为正式快照字段。

#### type = fund_trade（申购 / 赎回记录）

`date` 是用户下单 / 申请日期；确认和到账日期分别记录，不将申请金额误记为最终成交金额。交易金额、份额、费率均可缺省，必须以截图或用户明确文字为准。每条已确认交易若有平台订单号可存 `transaction_id`，不得编造。

```json
{
  "date": "2025-MM-DD",
  "time": "14:20",
  "domain": "invest",
  "type": "fund_trade",
  "metrics": {
    "transaction_id": "用户页面可见的订单标识",
    "fund_code": "000961",
    "fund_name": "天弘沪深300ETF联接A",
    "share_class": "A",
    "platform": "alipay",
    "product_category": "equity",
    "transaction_type": "subscribe",
    "status": "applied",
    "requested_amount": 500.0,
    "application_date": "2025-MM-DD",
    "confirmed_date": null,
    "confirmed_shares": null,
    "confirmed_nav": null,
    "nav_date": null,
    "fee_amount": null,
    "settlement_date": null
  },
  "note": "示例结构，非真实用户交易；没有页面证据的字段应省略",
  "source": "data/raw/2025-MM-DD/fund_trade_142000.png",
  "created_at": "2025-MM-DDT15:30:00+08:00"
}
```

`transaction_type`：`subscribe` / `redeem`；`status`：`applied` / `confirmed` / `in_transit` / `completed` / `cancelled` / `failed`。`requested_amount`、`requested_shares` 表示申请值；`confirmed_amount`、`confirmed_shares` 表示确认值；`cash_amount`、`fee_amount` 以最终页面为准。赎回未到账时保留 `in_transit`，不可算作已到账现金。分红、转换、定投计划和红利再投资本期不作为交易枚举，收到相关记录时先确认处理范围。

#### type = fund_note（研究笔记）

只在用户明确要求沉淀时写入；普通研究咨询不自动落库。研究依据及指标时点写入 `metrics.evidence`，主张、证伪条件和风险区分事实与判断。

```json
{
  "date": "2025-MM-DD",
  "domain": "invest",
  "type": "fund_note",
  "metrics": {
    "fund_code": "000961",
    "fund_name": "天弘沪深300ETF联接A",
    "share_class": "A",
    "platform": "alipay",
    "product_category": "equity",
    "thesis": "核心研究论点；必须由可追溯证据支撑",
    "risks": ["跟踪误差", "净值披露存在时滞"],
    "kill_criteria": ["明确可观测的证伪条件"],
    "evidence": [
      {
        "name": "基金管理人定期报告",
        "url": "https://example.invalid/",
        "published_at": "2025-MM-DD",
        "as_of": "2025-MM-DD",
        "metric": "需按实际披露填写",
        "source_level": "official"
      }
    ],
    "review_date": "2025-MM-DD"
  },
  "note": "示例结构，非真实研究结论",
  "source": "",
  "created_at": "2025-MM-DDT16:00:00+08:00"
}
```

> 所有示例代码、名称、数值、URL 均是 Schema 说明，不是产品身份验证或用户真实数据；不得复制进账户数据。

基金数据由独立脚本 `scripts/normalize_fund_data.py` 审计与规范化。`--check` 只读且非零退出码表示发现问题；写回模式只处理三个 `fund_*` 目录，不调用 `universe.json` 股票前缀规则，不触碰股票数据。周期报告和 dashboard 不因这些记录存在而自动获得基金适配能力。

## 扩展新领域

1. 在 `domains/` 下新建目录，含 `data/`。
2. 在 `skills/` 下新增对应 Skill。
3. 在本文件补充该领域的 `type` 与 `metrics` 定义。
4. 报表与面板会自动包含新领域，无需改代码（只要遵循通用结构）。