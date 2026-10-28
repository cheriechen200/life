/**
 * 示例数据包（SAMPLE DATA — 全部为虚构数值）
 *
 * 本文件所有数字均为随机生成的假数据，仅用于演示面板渲染效果，
 * 不代表任何真实个人记录。使用前请用真实数据覆盖，或改名为 data.js。
 *
 * 生成真实数据包：python3 scripts/normalize_health_data.py
 */

window.LIFE_OS_DATA = {
  meta: {
    generated_at: "2025-01-01T00:00:00+08:00",
    note: "示例数据，非真实记录",
    months: ["2025-01"]
  },
  months: {
    "2025-01": {
      days: {
        "2025-01-01": {
          meals: [
            { time: "08:00", type: "breakfast", calories: 480, protein_g: 30, carbs_g: 55, fat_g: 14, note: "示例早餐" },
            { time: "12:00", type: "lunch", calories: 620, protein_g: 38, carbs_g: 65, fat_g: 20, note: "示例午餐" },
            { time: "18:30", type: "dinner", calories: 560, protein_g: 35, carbs_g: 50, fat_g: 18, note: "示例晚餐" }
          ],
          workouts: [
            { time: "19:30", type: "strength", duration_min: 45, active_energy_kcal: 300, note: "示例训练" }
          ],
          sleep: { start: "23:00", end: "07:00", duration_min: 480, score: 82 },
          water: { total_ml: 2000, target_ml: 2100 },
          daily_metrics: {
            active_energy_kcal: 520,
            step_count: 8000,
            resting_energy_kcal: 1650
          }
        },
        "2025-01-02": {
          meals: [
            { time: "08:15", type: "breakfast", calories: 450, protein_g: 28, carbs_g: 50, fat_g: 13, note: "示例早餐" },
            { time: "12:10", type: "lunch", calories: 650, protein_g: 40, carbs_g: 68, fat_g: 21, note: "示例午餐" },
            { time: "18:45", type: "dinner", calories: 580, protein_g: 36, carbs_g: 52, fat_g: 19, note: "示例晚餐" }
          ],
          workouts: [
            { time: "07:30", type: "cycling", duration_min: 60, active_energy_kcal: 420, note: "示例骑行" }
          ],
          sleep: { start: "22:45", end: "06:50", duration_min: 485, score: 85 },
          water: { total_ml: 2200, target_ml: 2100 },
          daily_metrics: {
            active_energy_kcal: 610,
            step_count: 9500,
            resting_energy_kcal: 1650
          }
        }
      },
      body_comp: [
        { date: "2025-01-01", weight_kg: 70.0, skeletal_muscle_kg: 32.0, body_fat_kg: 12.0, body_fat_pct: 17.0 }
      ]
    }
  }
};
