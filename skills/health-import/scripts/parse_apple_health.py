#!/usr/bin/env python3
"""解析 Apple Health 导出 XML，转换为 life-os 统一 schema（支持增量导入）。

用法：
  python3 parse_apple_health.py <导出.xml路径> <life-os仓库根目录> [选项]

选项：
  --since <YYYY-MM-DD>  只处理该日期（含回溯窗口）之后的数据；缺省时读取状态文件
  --lookback <N>        回溯天数，默认 1，避免边界日遗漏
  --full                忽略状态与过滤，全量解析
  --no-state            不读取也不写入状态文件

设计要点：
  1. 每次导出都是全量，脚本按「上次导入水位」过滤，只处理新数据，避免冗余改写。
  2. 导出包为睡眠 / 运动 / 每日指标的权威来源；解析结果与现有月文件合并时，
     同键记录以导出包为准，但保留仅手动的字段（body_parts / exercises / circuit）。
  3. 状态写入 domains/health/.import_state.json，供下次增量过滤。
"""
import re
import sys
import os
import json
from collections import defaultdict
from datetime import datetime, timedelta

WORKOUT_MAP = {
    "HKWorkoutActivityTypeFunctionalStrengthTraining": "strength_training",
    "HKWorkoutActivityTypeTraditionalStrengthTraining": "strength_training",
    "HKWorkoutActivityTypeHighIntensityIntervalTraining": "hiit",
    "HKWorkoutActivityTypeRunning": "running",
    "HKWorkoutActivityTypeCycling": "cycling",
    "HKWorkoutActivityTypeWalking": "walking",
    "HKWorkoutActivityTypeSwimming": "swimming",
    "HKWorkoutActivityTypeYoga": "yoga",
    "HKWorkoutActivityTypeElliptical": "elliptical",
    "HKWorkoutActivityTypeRowing": "rowing",
}

SLEEP_STAGE_MAP = {
    "HKCategoryValueSleepAnalysisInBed": "in_bed",
    "HKCategoryValueSleepAnalysisAsleep": "asleep",
    "HKCategoryValueSleepAnalysisAsleepCore": "light",
    "HKCategoryValueSleepAnalysisAsleepDeep": "deep",
    "HKCategoryValueSleepAnalysisAsleepREM": "rem",
    "HKCategoryValueSleepAnalysisAwake": "awake",
}

DAILY_TYPES = {
    "HKQuantityTypeIdentifierStepCount": ("steps", "count"),
    "HKQuantityTypeIdentifierActiveEnergyBurned": ("active_energy_kcal", "kcal"),
    "HKQuantityTypeIdentifierBasalEnergyBurned": ("basal_energy_kcal", "kcal"),
    "HKQuantityTypeIdentifierRestingHeartRate": ("resting_heart_rate", "bpm"),
    "HKQuantityTypeIdentifierHeartRateVariabilitySDNN": ("hrv_sdnn_ms", "ms"),
    "HKQuantityTypeIdentifierVO2Max": ("vo2max", "ml/kg/min"),
    "HKQuantityTypeIdentifierBodyMass": ("weight_kg", "kg"),
    "HKQuantityTypeIdentifierAppleExerciseTime": ("exercise_min", "min"),
    "HKQuantityTypeIdentifierDistanceWalkingRunning": ("distance_km", "km"),
    "HKQuantityTypeIdentifierOxygenSaturation": ("spo2_pct", "pct"),
    "HKQuantityTypeIdentifierRespiratoryRate": ("respiratory_rate", "count/min"),
    "HKQuantityTypeIdentifierAppleSleepingWristTemperature": ("wrist_temp_c", "degC"),
}

record_re = re.compile(r'<Record\s+([^>]*?)/?>')
workout_block_re = re.compile(r'<Workout\s+(.*?)</Workout>', re.S)
stat_re = re.compile(r'<WorkoutStatistics\s+([^>]*?)/?>')
attr_re = re.compile(r'(\w+)="([^"]*)"')

STATE_REL = "domains/health/.import_state.json"
MANUAL_WORKOUT_FIELDS = ("body_parts", "exercises", "circuit")

workouts = []
sleep_by_day = defaultdict(list)
daily = defaultdict(dict)
steps_seen = set()
max_seen_date = None
CUTOFF = None  # 日期字符串，早于该日期的记录跳过；None 表示不过滤


def parse_args(argv):
    positional = []
    opts = {"since": None, "lookback": 1, "full": False, "no_state": False}
    i = 0
    while i < len(argv):
        a = argv[i]
        if a == "--since":
            i += 1
            opts["since"] = argv[i]
        elif a == "--lookback":
            i += 1
            opts["lookback"] = int(argv[i])
        elif a == "--full":
            opts["full"] = True
        elif a == "--no-state":
            opts["no_state"] = True
        else:
            positional.append(a)
        i += 1
    return positional, opts


def load_state(path):
    if os.path.exists(path):
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            return data if isinstance(data, dict) else {}
        except Exception:
            return {}
    return {}


def save_state(path, state):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)
        f.write("\n")


def now_iso():
    now = datetime.now().astimezone()
    return now.strftime("%Y-%m-%dT%H:%M:%S") + now.strftime("%z")[:3] + ":" + now.strftime("%z")[3:]


def parse_attrs(s):
    return dict(attr_re.findall(s))


def to_local(s):
    return datetime.strptime(s, "%Y-%m-%d %H:%M:%S %z")


def iso(dt):
    return dt.strftime("%Y-%m-%dT%H:%M:%S%z")


def date_str(dt):
    return dt.strftime("%Y-%m-%d")


def jk_to_kcal(v, unit):
    if unit == "kJ":
        return round(v * 0.239006, 1)
    return round(v, 1)


def note_date(d):
    global max_seen_date
    if d and (max_seen_date is None or d > max_seen_date):
        max_seen_date = d


def flush_workout(block):
    head_end = block.find(">")
    head = block[:head_end + 1]
    attrs = parse_attrs(head)
    wt_raw = attrs.get("workoutActivityType", "")
    activity = WORKOUT_MAP.get(wt_raw)
    if activity is None:
        activity = wt_raw.replace("HKWorkoutActivityType", "").lower() or "other"

    dur_min = None
    if attrs.get("duration"):
        d = float(attrs["duration"])
        unit = attrs.get("durationUnit", "min")
        dur_min = round(d / 60.0, 1) if unit == "sec" else round(d, 1)

    sd = attrs.get("startDate")
    if not sd:
        return
    start = to_local(sd)
    end = to_local(attrs["endDate"]) if attrs.get("endDate") else None

    d = date_str(start)
    note_date(d)
    if CUTOFF and d < CUTOFF:
        return

    metrics = {
        "activity": activity,
        "duration_min": dur_min,
        "calories_burned": None,
        "avg_heart_rate": None,
        "max_heart_rate": None,
        "distance_km": None,
        "intensity": None,
    }

    for m in stat_re.finditer(block):
        a = parse_attrs(m.group(1))
        t = a.get("type", "")
        if t == "HKQuantityTypeIdentifierActiveEnergyBurned" and a.get("sum"):
            metrics["calories_burned"] = jk_to_kcal(float(a["sum"]), a.get("unit", "kcal"))
        elif t == "HKQuantityTypeIdentifierHeartRate":
            if a.get("average"):
                metrics["avg_heart_rate"] = round(float(a["average"]))
            if a.get("maximum"):
                metrics["max_heart_rate"] = round(float(a["maximum"]))
        elif t in ("HKQuantityTypeIdentifierDistanceCycling",
                   "HKQuantityTypeIdentifierDistanceWalkingRunning") and a.get("sum"):
            metrics["distance_km"] = round(float(a["sum"]), 2)

    avg_hr = metrics["avg_heart_rate"]
    if avg_hr:
        if avg_hr < 100:
            metrics["intensity"] = "low"
        elif avg_hr < 140:
            metrics["intensity"] = "moderate"
        else:
            metrics["intensity"] = "high"

    workouts.append({
        "date": d,
        "time": start.strftime("%H:%M"),
        "domain": "health",
        "type": "workout",
        "metrics": metrics,
        "note": attrs.get("sourceName", "").strip(),
        "source": "apple_health_export",
        "created_at": iso(end or start),
    })


def handle_record(line):
    m = record_re.search(line)
    if not m:
        return
    a = parse_attrs(m.group(1))
    t = a.get("type", "")
    sd = a.get("startDate")
    if not sd:
        return
    start = to_local(sd)

    if t == "HKCategoryTypeIdentifierSleepAnalysis":
        stage = SLEEP_STAGE_MAP.get(a.get("value", ""), "unknown")
        end = to_local(a["endDate"]) if a.get("endDate") else None
        if end:
            d = date_str(end)
            note_date(d)
            if CUTOFF and d < CUTOFF:
                return
            sleep_by_day[d].append({
                "stage": stage,
                "start": start,
                "end": end,
                "minutes": round((end - start).total_seconds() / 60.0, 1),
            })
        return

    if t in DAILY_TYPES:
        key, unit = DAILY_TYPES[t]
        val = a.get("value")
        if val is None:
            return
        try:
            v = float(val)
        except ValueError:
            return
        if unit == "pct" and v > 1.5:
            v = v / 100.0
        d = date_str(start)
        note_date(d)
        if CUTOFF and d < CUTOFF:
            return
        if key == "steps":
            k = (d, key, a.get("sourceName", ""), a.get("startDate"), a.get("endDate"))
            if k in steps_seen:
                return
            steps_seen.add(k)
            daily[d][key] = daily[d].get(key, 0) + v
        elif key in ("active_energy_kcal", "basal_energy_kcal", "exercise_min", "distance_km"):
            if a.get("unit") == "kJ" and "energy" in key:
                v = jk_to_kcal(v, "kJ")
            daily[d][key] = round(daily[d].get(key, 0) + v, 1)
        else:
            daily[d][key] = round(v, 2)


def aggregate_sleep(day, stages):
    deep = sum(s["minutes"] for s in stages if s["stage"] == "deep")
    light = sum(s["minutes"] for s in stages if s["stage"] == "light")
    rem = sum(s["minutes"] for s in stages if s["stage"] == "rem")
    awake = sum(s["minutes"] for s in stages if s["stage"] == "awake")
    in_bed = sum(s["minutes"] for s in stages if s["stage"] == "in_bed")
    asleep_generic = sum(s["minutes"] for s in stages if s["stage"] == "asleep")

    if deep == 0 and light == 0 and rem == 0 and asleep_generic == 0 and in_bed == 0:
        return None

    total = deep + light + rem
    if total == 0:
        total = asleep_generic
    if total == 0:
        return None

    starts = [s["start"] for s in stages if s["stage"] != "in_bed"]
    ends = [s["end"] for s in stages if s["stage"] != "in_bed"]
    if not starts:
        starts = [s["start"] for s in stages]
        ends = [s["end"] for s in stages]
    sleep_start = min(starts)
    sleep_end = max(ends)

    score = min(100, round(total / 480.0 * 100))
    if total > 0 and 0.13 <= (deep / total) <= 0.23:
        score = min(100, score + 5)

    if total and deep / total < 0.13:
        comment = "深睡占比偏低"
    elif total < 420:
        comment = "总睡眠时长偏短"
    else:
        comment = "睡眠结构正常"

    return {
        "date": day,
        "time": sleep_end.strftime("%H:%M"),
        "domain": "health",
        "type": "sleep",
        "metrics": {
            "sleep_start": sleep_start.strftime("%H:%M"),
            "sleep_end": sleep_end.strftime("%H:%M"),
            "total_min": round(total),
            "deep_min": round(deep),
            "light_min": round(light),
            "rem_min": round(rem),
            "awake_min": round(awake),
            "sleep_score": score,
            "comment": comment,
        },
        "note": "",
        "source": "apple_health_export",
        "created_at": iso(sleep_end),
    }


def load_month(path):
    if os.path.exists(path):
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, list):
                return data
        except Exception:
            pass
    return []


def save_month(path, recs):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    recs.sort(key=lambda r: (r.get("date", ""), r.get("time", "")))
    with open(path, "w", encoding="utf-8") as f:
        json.dump(recs, f, ensure_ascii=False, indent=2)
        f.write("\n")


def merge_workouts(existing, incoming):
    """导出包为准覆盖同键记录，并保留仅手动的字段。"""
    ex_by_key = {}
    ex_by_act = defaultdict(list)
    for r in existing:
        ex_by_key[(r.get("date"), r.get("time"))] = r
        ex_by_act[(r.get("date"), r.get("metrics", {}).get("activity"))].append(r)
    incoming_keys = set()
    used = set()
    out = []
    for n in incoming:
        k = (n.get("date"), n.get("time"))
        incoming_keys.add(k)
        ex = ex_by_key.get(k)
        if ex is None:
            cands = ex_by_act.get((n.get("date"), n.get("metrics", {}).get("activity")), [])
            ex = cands[0] if len(cands) == 1 else None
        if ex is not None:
            used.add(id(ex))
            exm = ex.get("metrics", {})
            nm = n.setdefault("metrics", {})
            for f in MANUAL_WORKOUT_FIELDS:
                if not nm.get(f) and exm.get(f):
                    nm[f] = exm[f]
        out.append(n)
    for r in existing:
        if id(r) in used:
            continue
        if (r.get("date"), r.get("time")) in incoming_keys:
            continue
        out.append(r)
    return out


def merge_by_date(existing, incoming):
    """按 date 覆盖：导出包为准，保留导出未覆盖的旧日期。"""
    incoming_keys = {r.get("date") for r in incoming}
    out = list(incoming)
    for r in existing:
        if r.get("date") not in incoming_keys:
            out.append(r)
    return out


def write_outputs():
    base = os.path.join(REPO_ROOT, "domains/health/data")
    stats = {}

    wdir = os.path.join(base, "workouts")
    by_month = defaultdict(list)
    for w in workouts:
        by_month[w["date"][:7]].append(w)
    for month, recs in by_month.items():
        path = os.path.join(wdir, month + ".json")
        save_month(path, merge_workouts(load_month(path), recs))
    stats["workouts"] = len(workouts)

    sdir = os.path.join(base, "sleep")
    sleep_by_month = defaultdict(list)
    for d, stages in sleep_by_day.items():
        rec = aggregate_sleep(d, stages)
        if rec:
            sleep_by_month[d[:7]].append(rec)
    for month, recs in sleep_by_month.items():
        path = os.path.join(sdir, month + ".json")
        save_month(path, merge_by_date(load_month(path), recs))
    stats["sleep"] = sum(len(v) for v in sleep_by_month.values())

    ddir = os.path.join(base, "daily")
    daily_by_month = defaultdict(list)
    for d, metrics in daily.items():
        daily_by_month[d[:7]].append({
            "date": d,
            "domain": "health",
            "type": "daily_metrics",
            "metrics": metrics,
            "note": "",
            "source": "apple_health_export",
            "created_at": d + "T23:59:59+08:00",
        })
    for month, recs in daily_by_month.items():
        path = os.path.join(ddir, month + ".json")
        save_month(path, merge_by_date(load_month(path), recs))
    stats["daily"] = len(daily)

    return stats


def main():
    global XML_PATH, REPO_ROOT, CUTOFF
    positional, opts = parse_args(sys.argv[1:])
    if len(positional) < 2:
        print(__doc__)
        sys.exit(1)
    XML_PATH, REPO_ROOT = positional[0], positional[1]

    state_path = os.path.join(REPO_ROOT, STATE_REL)
    state = {} if opts["no_state"] else load_state(state_path)

    since = opts["since"] or state.get("last_import_date")
    if not opts["full"] and since:
        base_day = datetime.strptime(since, "%Y-%m-%d").date()
        CUTOFF = (base_day - timedelta(days=opts["lookback"])).strftime("%Y-%m-%d")

    print(f"解析范围：{'全量' if CUTOFF is None else '自 %s 起（含回溯 %d 天）' % (CUTOFF, opts['lookback'])}")

    with open(XML_PATH, "r", encoding="utf-8", errors="ignore") as f:
        buf = []
        in_workout = False
        for line in f:
            if in_workout:
                buf.append(line)
                if "</Workout>" in line:
                    flush_workout("".join(buf))
                    buf = []
                    in_workout = False
                continue
            if "<Workout " in line:
                if "</Workout>" in line:
                    flush_workout(line)
                else:
                    in_workout = True
                    buf = [line]
                continue
            if "<Record " in line:
                handle_record(line)

    stats = write_outputs()

    if not opts["no_state"]:
        state.update({
            "last_import_date": max_seen_date,
            "last_import_at": now_iso(),
            "last_source": os.path.basename(XML_PATH),
            "stats": stats,
        })
        save_state(state_path, state)

    print("运动记录: %d 条" % stats["workouts"])
    print("睡眠记录: %d 天" % stats["sleep"])
    print("每日指标: %d 天" % stats["daily"])
    print("数据水位: %s" % (max_seen_date or "-"))


if __name__ == "__main__":
    main()