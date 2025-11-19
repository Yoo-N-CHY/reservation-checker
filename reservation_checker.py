import streamlit as st
from datetime import datetime, timedelta, time as dtime
import re

st.title("예약 가능 시간 확인기")

uploaded_text = st.text_area("예약 텍스트를 붙여넣으세요:", height=400)
weekday_only = st.toggle("주간 사용시간만 포함 (09:00~18:00)", value=True)

FULL_TIME_RANGE = (dtime(8, 0), dtime(23, 0))
WEEKDAY_TIME_RANGE = (dtime(9, 0), dtime(18, 0))
LUNCH_TIME = (dtime(12, 0), dtime(13, 0))

# 타임슬롯 30분 단위로 생성
def generate_slots(start, end):
    slots = []
    current = datetime.combine(datetime.today(), start)
    end_time = datetime.combine(datetime.today(), end)
    while current < end_time:
        slot_end = current + timedelta(minutes=30)
        slots.append((current.time(), slot_end.time()))
        current = slot_end
    return slots

# 예약 문자열을 time 객체로 변환
def parse_time_range(text):
    match = re.match(r"(\d{2}):(\d{2})~(\d{2}):(\d{2})", text)
    if not match:
        return None
    h1, m1, h2, m2 = map(int, match.groups())
    return dtime(h1, m1), dtime(h2, m2)

# 날짜 문자열을 datetime 객체로 변환

def parse_date(text):
    text = text.strip()
    # "12.10" 같은 형식 처리
    try:
        month, day = map(int, text.split("."))
        year = datetime.today().year
        return datetime(year, month, day)
    except:
        return None

if uploaded_text:
    lines = uploaded_text.splitlines()
    schedule = {}
    current_date = None

    for line in lines:
        if line.strip() == "" or "예약하기" in line:
            continue
        parsed = parse_date(line)
        if parsed:
            current_date = parsed
            schedule[current_date] = []
        elif current_date and re.match(r"\d{2}:\d{2}~\d{2}:\d{2}", line):
            time_range = parse_time_range(line.strip())
            if time_range:
                schedule[current_date].append(time_range)

    st.markdown("---")
    st.subheader("예약 가능 시간표")

    for day, reservations in sorted(schedule.items()):
        # 1. 오늘 날짜 기준 주말이면 건너뜀
        if day.weekday() >= 5:
            continue

        # 2. 시간대 기준 정리
        if weekday_only:
            base_slots = generate_slots(*WEEKDAY_TIME_RANGE)
        else:
            base_slots = generate_slots(*FULL_TIME_RANGE)

        # 점심시간 강제로 추가
        reservations.append(LUNCH_TIME)

        # 3. 예약 겹치는 시간 제거
        available_slots = []
        for slot_start, slot_end in base_slots:
            conflict = False
            for r_start, r_end in reservations:
                if not (slot_end <= r_start or slot_start >= r_end):
                    conflict = True
                    break
            if not conflict:
                available_slots.append((slot_start, slot_end))

        # 4. 출력
        if available_slots:
            st.markdown(f"### {day.strftime('%m월 %d일 (%a)')}")
            for s, e in available_slots:
                st.write(f"{s.strftime('%H:%M')} ~ {e.strftime('%H:%M')}")
        else:
            st.markdown(f"### {day.strftime('%m월 %d일 (%a)')}: 예약 가능 시간 없음")
