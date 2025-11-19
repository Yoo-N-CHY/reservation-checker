import streamlit as st
import re
from datetime import datetime, timedelta
import pandas as pd

st.title("예약 가능한 시간 찾기")

# 텍스트 입력
input_text = st.text_area("예약 텍스트 입력", height=400)

# 주간 시간만 포함할지 여부
only_working_hours = st.toggle("주간 사용시간만 포함 (09:00~18:00)", value=True)

# 실행 버튼
run_check = st.button("빈자리 찾기!")

if run_check:
    def parse_schedule(text):
        days = {}
        current_day = None
        for line in text.splitlines():
            line = line.strip()
            if not line:
                continue
            if re.match(r"^\d{1,2}(\.\d{1,2})?$", line):
                current_day = line
                days[current_day] = []
            elif re.match(r"\d{2}:\d{2}~\d{2}:\d{2}", line):
                time_range = re.findall(r"\d{2}:\d{2}~\d{2}:\d{2}", line)[0]
                days[current_day].append(time_range)
        return days

    def get_time_slots(start="08:00", end="23:00"):
        slots = []
        current = datetime.strptime(start, "%H:%M")
        end_time = datetime.strptime(end, "%H:%M")
        while current < end_time:
            next_time = current + timedelta(minutes=30)
            slots.append((current.time(), next_time.time()))
            current = next_time
        return slots

    def merge_slots(slots):
        if not slots:
            return []
        merged = [slots[0]]
        for start, end in slots[1:]:
            last_start, last_end = merged[-1]
            if start == last_end:
                merged[-1] = (last_start, end)
            else:
                merged.append((start, end))
        return merged

    def format_slot(slot):
        return f"{slot[0].strftime('%H:%M')}~{slot[1].strftime('%H:%M')}"

    def is_weekend(day_label):
        today = datetime.today()
        try:
            if "." in day_label:
                month, day = map(int, day_label.split("."))
            else:
                month = today.month
                day = int(day_label)
            date_obj = datetime(today.year, month, day)
            return date_obj.weekday() >= 5
        except:
            return False

    def find_available_times(days):
        output = {}
        full_slots = get_time_slots("09:00" if only_working_hours else "08:00", "18:00" if only_working_hours else "23:00")
        lunch = [(datetime.strptime("12:00", "%H:%M").time(), datetime.strptime("13:00", "%H:%M").time())]

        for day, reserved in days.items():
            if is_weekend(day):
                continue
            reserved_times = []
            for r in reserved:
                start, end = r.split("~")
                s_time = datetime.strptime(start, "%H:%M").time()
                e_time = datetime.strptime(end, "%H:%M").time()
                reserved_times.append((s_time, e_time))

            reserved_times += lunch

            available = []
            for slot in full_slots:
                if any(not (slot[1] <= r[0] or slot[0] >= r[1]) for r in reserved_times):
                    continue
                available.append(slot)

            merged = merge_slots(available)
            if merged:
                output[day] = [format_slot(slot) for slot in merged]
        return output

    schedule = parse_schedule(input_text)
    available_times = find_available_times(schedule)

    if not available_times:
        st.write("예약 가능한 시간이 없습니다.")
    else:
        df_rows = []
        for day, times in available_times.items():
            for t in times:
                df_rows.append({"날짜": day, "예약 가능 시간": t})
        df = pd.DataFrame(df_rows)
        st.dataframe(df, use_container_width=True)

