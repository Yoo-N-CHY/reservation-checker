import streamlit as st
from datetime import datetime, timedelta

# 기본 설정
WORK_START = datetime.strptime("08:00", "%H:%M")
WORK_END = datetime.strptime("23:00", "%H:%M")
LUNCH_START = datetime.strptime("12:00", "%H:%M")
LUNCH_END = datetime.strptime("13:00", "%H:%M")

# 제목 및 입력창
st.title("🔍 분석실 남는자리 찾기 피로그램")
st.write("날짜 + '해당날짜 예약하기' + 시간 형식의 텍스트를 입력해주세요.")
text_input = st.text_area("텍스트 입력", height=400)

# 스위치: 업무시간 모드
mode_daytime_only = st.toggle("09:00~18:00만 보기 (업무시간 모드)", value=False)

# 파서: 날짜별 예약 시간 추출
def parse_reservations(text):
    lines = text.strip().splitlines()
    data = {}
    current_date = None
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if line.isdigit():
            current_date = line
            data[current_date] = []
        elif "~" in line and current_date:
            time_range = line.split()[0]
            start, end = time_range.split("~")
            data[current_date].append((start, end))
    return data

# 빈 시간 계산 함수 (점심시간 제외 반영)
def find_free_slots(bookings, start_time, end_time):
    free_slots = []
    current = start_time
    sorted_bookings = sorted([(datetime.strptime(s, "%H:%M"), datetime.strptime(e, "%H:%M")) for s, e in bookings])

    for start, end in sorted_bookings:
        if current < start:
            slot_start = current
            slot_end = start

            # 점심시간 제외 처리
            if slot_end <= LUNCH_START or slot_start >= LUNCH_END:
                free_slots.append((slot_start, slot_end))
            elif slot_start < LUNCH_START and slot_end > LUNCH_END:
                free_slots.append((slot_start, LUNCH_START))
                free_slots.append((LUNCH_END, slot_end))
            elif slot_start < LUNCH_START < slot_end <= LUNCH_END:
                free_slots.append((slot_start, LUNCH_START))
            elif LUNCH_START <= slot_start < LUNCH_END < slot_end:
                free_slots.append((LUNCH_END, slot_end))

        current = max(current, end)

    if current < end_time:
        if current < LUNCH_START:
            free_slots.append((current, min(end_time, LUNCH_START)))
        elif current >= LUNCH_END:
            free_slots.append((current, end_time))

    return [(s.strftime("%H:%M"), e.strftime("%H:%M")) for s, e in free_slots if e > s]

# 분석 버튼 클릭
if st.button("분석 시작"):
    if not text_input.strip():
        st.warning("텍스트를 입력해주세요.")
    else:
        parsed = parse_reservations(text_input)
        result = []

        # 시간 범위 설정: 업무시간 or 전체시간
        start_scope = datetime.strptime("09:00", "%H:%M") if mode_daytime_only else WORK_START
        end_scope = datetime.strptime("18:00", "%H:%M") if mode_daytime_only else WORK_END

        for date, bookings in parsed.items():
            if bookings:
                free_times = find_free_slots(bookings, start_scope, end_scope)
                for start, end in free_times:
                    result.append({"날짜": date, "시작시간": start, "종료시간": end})

        if result:
            st.success("분석 완료! 아래 표를 확인하세요.")
            st.dataframe(result)
        else:
            st.info("예약이 없는 날짜이거나, 빈 시간이 존재하지 않습니다.")
