---
name: dashboard
description: life-os 的可视化面板 Skill。读取仓库内的健康数据（内嵌数据包 dashboard/data.js 或按月 JSON），渲染可交互的 ECharts 图表（热量收支、睡眠阶段、训练分布、趋势折线等）。支持 file:// 直接打开，无需本地静态服务。
---

# dashboard

把 life-os 的结构化数据渲染成可交互的可视化面板。

## 触发场景

- 用户说"更新面板""看趋势图""生成可视化"
- 数据更新后自动刷新

## 产出物

`dashboard/index.html`，单文件、无后端、无构建步骤，直接浏览器打开或由 GitHub Pages 托管。

## 技术选型

- ECharts（CDN 引入）绘制图表
- 原生 fetch 读取仓库内 JSON
- 纯静态，无框架

## 图表清单

**周期区（随上方「按月 / 按年」切换，仅展示所选周期数据）**

1. 摘要卡：训练次数 / 总时长 / 运动消耗 / 平均睡眠 / 日均步数 / 平均静息心率
2. 步数趋势：每日步数折线
3. 静息心率 & HRV：双轴折线（bpm / ms）
4. 能量消耗：活动能量 + 基础能量堆叠柱
5. 睡眠结构与评分：深睡 / 浅睡 / REM 堆叠柱 + 评分折线
6. 训练类型分布：饼图（activity 中文映射）
7. 训练强度分布：饼图（按平均心率推导，intensity 中文映射）
8. 热量收支：摄入 vs 运动消耗折线
9. 身体指标：体重 / VO2Max 双轴折线（数据稀疏）

**身体成分区（独立于周期切换，按真实测量日期铺满全周期时间轴）**

10. 体测摘要卡：最新体测日 + 体重 / 骨骼肌 / 体脂率 / InBody 评分，含与上次测量的增减对比
11. 体成分变化趋势：体重 / 骨骼肌 / 体脂率 双轴折线
12. 身体成分评估：BMI / 内脏脂肪等级 / InBody 评分
13. 节段肌肉量：左臂 / 右臂 / 躯干 / 左腿 / 右腿
14. 节段脂肪量：左臂 / 右臂 / 躯干 / 左腿 / 右腿

> 说明：身体成分为低频测量（每次间隔可达数月），若并入周期切换会因默认只显示单月 / 单年而几乎看不到，故拆分为独立区块，横轴用实际测量日期直接连线。

> 说明：面板当前仅展示健康域；职业与成长域已搁置，待后续需求启用后再补充页签。

## 数据读取约定

面板按以下优先级取数，保证「本地双击打开」与「HTTP 托管」两种方式都能工作：

1. 内嵌数据包 `dashboard/data.js`（`window.LIFE_OS_DATA`）：由 `scripts/normalize_health_data.py` 生成，`<script src="data.js">` 同步加载。此方式不触发 fetch，`file://` 直接双击 `index.html` 即可读取。
2. 回退 fetch：数据包缺失时，按月请求 `../domains/health/data/<type>/<YYYY-MM>.json`。此方式需通过 HTTP 访问（如 `python3 -m http.server`），`file://` 下会被浏览器同源策略拦截。

数据更新后运行 `python3 scripts/normalize_health_data.py` 重新生成数据包，保证面板读到的是最新数据。

## 数据规范化

`scripts/normalize_health_data.py` 负责把解析产物规范为可稳定读取的格式：

- `created_at` 统一为 ISO 8601 带冒号时区（`+0800` → `+08:00`）
- 计数字段（`steps` / `resting_heart_rate` 等）去小数，统一为整数
- 记录字段顺序统一为 `date / time? / domain / type / metrics / note / source / created_at`
- 按 `date` + `time` 排序，保证 diff 稳定
- `--check` 参数只报告问题、不修改文件

## 更新流程

1. 数据入库后运行 `python3 scripts/normalize_health_data.py`，写入规范化数据并生成 `dashboard/data.js`。
2. 双击 `dashboard/index.html` 即可查看；或通过 HTTP 托管访问。

## 注意事项

- 面板是只读视图，不修改数据。
- `dashboard/data.js` 为自动生成产物，不要手工编辑。
- 图表配色统一，深色 / 浅色主题可切换。
- 移动端自适应：针对 iPhone 14 Pro（393 × 852）等窄屏做了专门适配——摘要卡与图表改单列排布，图表高度收窄，坐标轴边距自动收紧，并启用刘海屏安全区（`viewport-fit=cover` + `env(safe-area-inset-*)`）。断点：≤ 360px 摘要卡进一步降为单列；641–900px 维持双列并收紧内边距；跨断点旋转屏幕时自动重绘。