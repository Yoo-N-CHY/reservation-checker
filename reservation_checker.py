import streamlit as st
from datetime import datetime, timedelta

# 기본 설정
WORK_START = datetime.strptime("08:00", "%H:%M")
WORK_END = datetime.strptime("23:00", "%H:%M")
LUNCH_START = datetime.strptime("12:00", "%H:%M")
LUNCH_END = datetime.strptime("13:00", "%H:%M")

# 텍스트 입력 받기
st.title("🔍 분석실 빈자리 찾기 프로그램")
st.write("날짜 + '해당날짜 예약하기' + 시간 형식의 텍스트를 입력해주세요.")
text_input = st.text_area("텍스트 입력", height=100)

def parse_reservations(text):
    lines = text.strip().splitlines()
    data = {}
    current_date = None
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if line.isdigit():  # 날짜로 판단
            current_date = line
            data[current_date] = []
        elif "~" in line and current_date:
            time_range = line.split()[0]
            start, end = time_range.split("~")
            data[current_date].append((start, end))
    return data

def find_free_slots(bookings):
    free_slots = []
    current = WORK_START
    sorted_bookings = sorted([(datetime.strptime(s, "%H:%M"), datetime.strptime(e, "%H:%M")) for s, e in bookings])

    for start, end in sorted_bookings:
        # 예약 전 빈 시간 계산
        if current < start:
            slot_start = current
            slot_end = start

            # 점심시간과 겹치는 부분 제외
            if slot_end <= LUNCH_START or slot_start >= LUNCH_END:
                free_slots.append((slot_start, slot_end))
            elif slot_start < LUNCH_START and slot_end > LUNCH_END:
                free_slots.append((slot_start, LUNCH_START))
                free_slots.append((LUNCH_END, slot_end))
            elif slot_start < LUNCH_START < slot_end <= LUNCH_END:
                free_slots.append((slot_start, LUNCH_START))
            elif LUNCH_START <= slot_start < LUNCH_END < slot_end:
                free_slots.append((LUNCH_END, slot_end))
            # (완전히 점심시간과 겹치면 아무것도 추가하지 않음)

        # 다음 예약 시점으로 이동
        current = max(current, end)

    # 마지막 예약 이후의 시간도 고려
    if current < WORK_END:
        if current < LUNCH_START:
            free_slots.append((current, min(LUNCH_START, WORK_END)))
        elif current >= LUNCH_END:
            free_slots.append((current, WORK_END))

    # 문자열 포맷으로 반환
    return [(s.strftime("%H:%M"), e.strftime("%H:%M")) for s, e in free_slots if e > s]


# 버튼 클릭 시 분석
if st.button("분석 시작"):
    if not text_input.strip():
        st.warning("텍스트를 입력해주세요.")
    else:
        parsed = parse_reservations(text_input)
        result = []
        for date, bookings in parsed.items():
            if bookings:
                free_times = find_free_slots(bookings)
                for start, end in free_times:
                    result.append({"날짜": date, "시작시간": start, "종료시간": end})
        if result:
            st.success("분석 완료! 아래 표를 확인하세요.")
            st.dataframe(result)
        else:
            st.info("예약이 없는 날짜이거나, 빈 시간이 존재하지 않습니다.")
