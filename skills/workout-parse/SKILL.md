---
name: workout-parse
description: 健康域运动解析子 Skill。输入苹果健康 App 或智能手表的运动记录截图，输出运动类型、时长、心率区间、消耗卡路里、训练部位、强度等结构化字段。支持单次 / 每周 / 每月三种粒度，结果写入 domains/health/data/workouts。
---

# workout-parse

运动记录截图解析。覆盖力量训练、跑步、骑行、游泳、瑜伽、快走等类型。

## 数据定位（重要）

截图解析是**临时记录**：用户当天发来就先落库，保证当天可见、日报可用。截图给不出的字段（训练部位、动作明细）反而只能靠这里补齐。

每月一次的 Apple 健康导出包是运动的**权威来源**，会用它的完整数据覆盖同月的截图记录（见 `skills/health-import`）。覆盖时**保留**截图补录的 `body_parts` / `exercises` / `circuit`，因此这些手动字段不会被导出包冲掉，放心记录。

## 触发场景

- 用户发来运动记录截图（公司健身、居家运动、晨跑等）
- 用户发来每周 / 每月的运动汇总截图

## 分析流程

1. 识别截图来源（苹果健康 App / 手表原生 / 其他）。
2. 提取运动类型、起止时间、时长。
3. 提取心率数据：平均、最大、心率区间。
4. 提取消耗卡路里。
5. 力量训练时识别训练部位（可辅助用户补充）。
6. 组装 `metrics` 并写入 `domains/health/data/workouts/<YYYY-MM>.json`。

## 输出字段

```json
{
  "metrics": {
    "activity": "strength_training",
    "duration_min": 60,
    "calories_burned": 420,
    "avg_heart_rate": 128,
    "max_heart_rate": 162,
    "hr_zone": "aerobic",
    "body_parts": ["chest", "triceps"],
    "intensity": "moderate",
    "exercises": [
      { "name": "seated_cable_row", "name_cn": "坐姿划船", "weight_kg": 40, "sets": 4, "reps": 12 }
    ]
  }
}
```

## 训练明细（力量 / 循环训练）

截图只给得出时长与心率，动作明细必须问用户或由用户提供，不要凭截图臆测。拿到后按下面两种形态写入。

### 力量训练 → `metrics.exercises`

| 字段 | 必填 | 说明 |
| --- | --- | --- |
| `name` | 是 | 稳定英文标识，见下方动作命名表，便于长期趋势比对 |
| `name_cn` | 是 | 中文动作名，展示用 |
| `weight_kg` | 否 | 负重（kg）。单侧负重填单侧数值并把 `unilateral` 置 true |
| `sets` | 是 | 组数 |
| `reps` | 是 | 每组次数 |
| `unilateral` | 否 | 是否单侧交替（如单臂哑铃弯举），默认 false |
| `equipment` | 否 | 器械：`cable` / `dumbbell` / `barbell` / `machine` / `bodyweight` |
| `depth` | 否 | 深蹲类幅度：`above_parallel` / `at_parallel` / `at_or_below_parallel`。**采集深蹲时必须问清**，半蹲与标准深度的重量不可比 |
| `belt` | 否 | 腰带：`none` / `all` / `partial`（`partial` 时在 `note` 写清哪几组）。**采集大重量深蹲/硬拉时必须问清**，带与不带是两条曲线 |
| `note` | 否 | 动作名不确定、重量口径存疑等说明 |

### 间歇 / 循环训练 → `metrics.circuit`

一组动作循环做若干轮时，用 `circuit` 描述节奏，`exercises` 内只列动作本身：

```json
{
  "circuit": { "rounds": 6, "work_sec": 50, "rest_sec": 10, "exercises": ["crunch", "flutter_kick"] },
  "exercises": [
    { "name": "crunch", "name_cn": "卷腹", "equipment": "bodyweight" },
    { "name": "flutter_kick", "name_cn": "仰卧交替摆腿", "equipment": "bodyweight" }
  ]
}
```

| 字段 | 说明 |
| --- | --- |
| `rounds` | 总轮数（用户说"6 组训练"即 6 轮） |
| `work_sec` / `rest_sec` | 单轮工作 / 间歇秒数 |
| `circuit.exercises` | 本轮动作顺序（用 `name` 标识） |

动作名不确定时：先按用户描述给出**最接近的专业叫法**并在 `note` 标注「动作名待确认」，不要留空、不要编造重量。

### 动作命名表

数据文件存英文 `name`，看板/日报展示 `name_cn`。新增动作需同步补进本表。

| name | name_cn | 常见别名 / 识别线索 |
| --- | --- | --- |
| `seated_cable_row` | 坐姿划船 | 坐姿、绳索拉向腹部 |
| `lat_pulldown` | 高位下拉 | 横杆从上往下拉至锁骨 |
| `dumbbell_bicep_curl` | 哑铃弯举 | 单臂/双臂弯举，常标单侧重量 |
| `triceps_pushdown` | 绳索下压（三头） | 龙门架/绳索，手臂向下压到底 |
| `crunch` | 卷腹 | 仰卧、上背离地 |
| `flutter_kick` | 仰卧交替摆腿 | 肩离地、双腿交替上下（自由泳式打腿） |
| `bicycle_crunch` | 自行车卷腹 | 平躺、手肘交替碰对侧膝、蹬车 |
| `mountain_climber` | 登山者 | 手撑地、屈膝交替收向胸口 |
| `v_sit_hold` | V 字支撑 | 臀坐地、双腿高举呈 V，手轻撑地 |
| `leg_raise` | 仰卧举腿 | 平躺、双腿垂直上下举落 |
| `barbell_back_squat` | 杠铃深蹲 | 杠铃颈后深蹲；逐组加重时 weight_kg 存最大组重量，note 记全程 |
| `hip_adduction` | 髋内收（夹腿） | 坐姿夹腿机，双腿向内合拢 |
| `hip_abduction` | 髋外展 | 坐姿外展机，双腿向外打开 |
| `leg_extension` | 坐姿腿屈伸 | 坐姿伸膝机，小腿向上抬 |
| `leg_curl` | 腿弯举 | 俯卧 / 坐姿屈膝机，小腿向后勾 |
| `dumbbell_shoulder_press` | 哑铃肩上推举 | 坐姿 / 站姿双手哑铃过头推；单侧负重记单侧值并置 `unilateral` |
| `reverse_pec_deck` | 反向蝴蝶机（后束飞鸟） | 蝴蝶机反向坐、双臂向后打开；用户只说"蝴蝶"时需问清是夹胸还是反向 |
| `dumbbell_lateral_raise` | 站姿哑铃侧平举 | 双臂侧向抬平至肩高；递减组时 `weight_kg` 存最大档、`note` 记全部档位 |
| `barbell_bench_press` | 杠铃卧推 | 平躺杠铃推起；逐组加重时 `weight_kg` 存最大组、`note` 记全程（2025-MM-DD 新增） |
| `barbell_incline_bench_press` | 杠铃上斜推胸 | 上斜凳杠铃推胸（2025-MM-DD 新增） |
| `machine_chest_fly` | 蝴蝶机夹胸 | 蝴蝶机正向坐、双臂向内夹拢（2025-MM-DD 新增；与 `reverse_pec_deck` 方向相反） |
| `barbell_bicep_curl` | 杠铃弯举 | 站姿杠铃弯举练二头（2025-MM-DD 新增） |
| `smith_bench_press` | 史密斯卧推（平板） | 史密斯机平板推胸，杆垂直轨迹，`equipment: smith_machine`；与自由杠铃是两条趋势线，不可混比（2025-10-19 新增） |
| `barbell_decline_bench_press` | 杠铃下斜卧推（下胸） | 下斜凳杠铃推胸，落点下胸；头低位，组间坐起休息（2025-10-19 新增） |

### 动作参考库（`domains/health/reference/exercise_ref.json`）

解析力量训练明细时，先查本仓库的动作参考库（精选自 openGym 动作目录，见其 `_meta` 的来源与许可说明）：

- **动作识别**：用户口述模糊（"练背那个拉的"）时，按库内 `equipment` + `target_muscle` 缩小候选，再与用户确认，不要直接猜。
- **肌群归属**：`body_parts` 优先由库内 `target_muscle` / `secondary_muscles` 推导（映射到本 Skill 的 `body_parts` 枚举），比凭印象标注稳定。
- **动作要点**：库内 `instructions` 是标准动作步骤，点评时可作为"动作质量提示"引用一句，不整段搬运。
- **新增动作**：命名表新增动作时，同步在参考库补一条（带 openGym `og_id` 便于回查；库中确无可对应条目则 `og_id: null`、`source: "custom"`）。

### 容量与强度估算（可选字段，注明估算）

拿到完整组数明细时，可在 `metrics` 补两个派生字段（**入库时在 `note` 标注"派生值"**，非设备原始数据）：

- `volume_kg`：Σ(sets × reps × weight_kg)，单侧动作按单侧重量 ×2 计入总量；自重动作不计入容量。
- `e1rm_kg`：单动作取最大组按 Epley 公式估算 1RM = w × (1 + reps/30)，仅对 reps ≤ 12 的组有效（更高次数误差过大，不估）。用于同动作长期趋势比对，不用于训练当日的重量决策。

### `body_parts` 取值

`back` / `chest` / `shoulder` / `biceps` / `triceps` / `legs` / `abs` / `core` / `glutes`。由动作推导并在 `note` 中保留用户原话（如"今天练背"）。

## 粒度处理

- 单次记录：一条 workout 记录。
- 周 / 月汇总截图：拆分为多条单次记录（若截图含每日明细），或作为一条 `type = workout_summary` 的记录存入同一目录并在 `note` 标注周期。

## 枚举与展示映射

数据文件中 `activity` / `intensity` 一律存英文原值（与 Apple Health 口径一致），看板展示时再映射为中文，映射关系如下：

`activity`：

| 数据值 | 看板中文 |
| --- | --- |
| `strength_training` | 力量训练 |
| `hiit` | 高强度间歇 |
| `running` | 跑步 |
| `cycling` | 骑行 |
| `walking` | 步行 |
| `swimming` | 游泳 |
| 其他值 | 其他 |

`intensity`（由平均心率推导）：

| 数据值 | 看板中文 |
| --- | --- |
| `low` | 低强度 |
| `moderate` | 中等强度 |
| `high` | 高强度 |
| 空值 | 未记录 |

新增取值时，需同步在 `dashboard/index.html` 的 `ACTIVITY_CN` / `INTENSITY_CN` 映射表中补充，否则前端回退为「其他」或「未记录」。

## 用户向回报格式

```
运动已记录 · 力量训练
时长 60 min · 消耗 420 kcal · 平均心率 128
训练部位：胸、三头 · 强度：中等
```

## 注意事项

- 心率单位统一为 bpm，时长统一为分钟。
- 无法从截图读取的字段（训练部位、动作名、重量组数）主动询问用户，不要靠猜测补齐。
- 截图含多天数据时逐条拆分，不要合并成一条。
- 原始截图只作解析取证，保存到 `data/raw/` 后**不 commit、不 push**；`source` 填本地相对路径即可。
- Apple/Watch 截图给的是千焦，取「动态千焦」（活动能量）÷ 4.184 换算为 `calories_burned`，与 `apple_health_export` 口径一致；「总千焦」含静息能耗，不要混用。