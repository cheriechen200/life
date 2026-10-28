#!/usr/bin/env python3
"""扫描 Apple Health 导出 XML，统计 Record 类型分布与时间范围。"""
import re
import sys
from collections import Counter

XML_PATH = sys.argv[1] if len(sys.argv) > 1 else "导出.xml"

type_counter = Counter()
min_date = None
max_date = None
workout_types = Counter()
workout_min = None
workout_max = None

record_re = re.compile(r'<Record\s+([^>]*?)/?>')
attr_re = re.compile(r'(\w+)="([^"]*)"')
workout_re = re.compile(r'<Workout\s+([^>]*?)/?>')

with open(XML_PATH, "r", encoding="utf-8", errors="ignore") as f:
    for line in f:
        if "<Record " in line:
            m = record_re.search(line)
            if m:
                attrs = dict(attr_re.findall(m.group(1)))
                t = attrs.get("type", "")
                type_counter[t] += 1
                sd = attrs.get("startDate", "")
                ed = attrs.get("endDate", "")
                if sd:
                    if min_date is None or sd < min_date:
                        min_date = sd
                    if max_date is None or sd > max_date:
                        max_date = sd
        elif "<Workout " in line:
            m = workout_re.search(line)
            if m:
                attrs = dict(attr_re.findall(m.group(1)))
                wt = attrs.get("workoutActivityType", "")
                workout_types[wt] += 1
                sd = attrs.get("startDate", "")
                if sd:
                    if workout_min is None or sd < workout_min:
                        workout_min = sd
                    if workout_max is None or sd > workout_max:
                        workout_max = sd

print("=== Record 总类型数:", len(type_counter))
print("=== 记录时间范围:", min_date, "~", max_date)
print("=== Workout 时间范围:", workout_min, "~", workout_max)
print()
print("=== 记录数 Top 40 类型 ===")
for t, c in type_counter.most_common(40):
    print(f"{c:>10}  {t}")
print()
print("=== 全部 Workout 类型 ===")
for t, c in workout_types.most_common():
    print(f"{c:>6}  {t}")