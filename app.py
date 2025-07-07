import streamlit as st
import requests

# -------------------- #
#      환율 데이터      #
# -------------------- #
@st.cache_data(ttl=3600)  # 1시간 캐싱
def get_rates(base='USD'):
    url = f"https://open.er-api.com/v6/latest/{base}"
    response = requests.get(url)
    data = response.json()
    if data['result'] == 'success':
        return data['rates'], data['time_last_update_utc']
    else:
        st.error("환율 데이터를 불러오지 못했습니다.")
        return {}, None

# -------------------- #
#   통화 코드 및 이름   #
# -------------------- #
CURRENCIES = {
    "KRW": "대한민국 원",
    "USD": "미국 달러",
    "JPY": "일본 엔",
    "EUR": "유로",
    "CNY": "중국 위안",
    "GBP": "영국 파운드",
    "AUD": "호주 달러"
}

curr_list = list(CURRENCIES.keys())

# -------------------- #
#      SessionState    #
# -------------------- #
if "swap" not in st.session_state:
    st.session_state.swap = False


if "left_value" not in st.session_state:
    st.session_state.left_value = 10000

if "right_value" not in st.session_state:
    st.session_state.right_value = 0

# 입력 위젯용 세션 상태 초기화
if "left_input" not in st.session_state:
    st.session_state.left_input = st.session_state.left_value
if "right_input" not in st.session_state:
    st.session_state.right_input = st.session_state.right_value

if "left_currency" not in st.session_state:
    st.session_state.left_currency = "KRW"

if "right_currency" not in st.session_state:
    st.session_state.right_currency = "USD"

# -------------------- #
#      메인 UI 구성     #
# -------------------- #
st.title("💱 양방향 환율 변환기")
st.markdown("실시간 환율을 기반으로 두 통화 간 금액을 서로 변환해보세요.")

# ---- 컬럼 배치 ---- #
cols = st.columns([2,1,1,1,2])

with cols[0]:
    left_value = st.number_input(
        "금액 입력",
        min_value=0.0, value=float(st.session_state.left_value),
        key="left_input"
    )
with cols[1]:
    left_currency = st.selectbox("통화", curr_list, index=curr_list.index(st.session_state.left_currency), key="left_cur")

with cols[2]:
    if st.button("⇄ 화폐 바꾸기", use_container_width=True):
        # swap currency and value
        st.session_state.left_currency, st.session_state.right_currency = st.session_state.right_currency, st.session_state.left_currency
        st.session_state.left_value, st.session_state.right_value = st.session_state.right_value, st.session_state.left_value
        st.experimental_rerun()

with cols[3]:
    right_currency = st.selectbox("통화 ", curr_list, index=curr_list.index(st.session_state.right_currency), key="right_cur")

with cols[4]:
    right_value = st.number_input(
        "금액 입력 ",
        min_value=0.0, value=float(st.session_state.right_value),
        key="right_input"
    )

# 환율 데이터 불러오기 (왼쪽 통화를 기준)
rates, update_time = get_rates(st.session_state.left_currency)

# 변환 로직
def convert(val, from_cur, to_cur, rates):
    try:
        if from_cur == to_cur:
            return val
        rate = rates[to_cur]
        return round(val * rate, 4)
    except Exception:
        return 0

# 어느 쪽이 수정됐는지 감지 (Streamlit 특성상 약간의 한계가 있으나 기본 동작 구현)
if st.session_state.left_input != st.session_state.left_value:
    # 왼쪽 입력 바뀜 -> 오른쪽 자동 계산
    st.session_state.left_value = st.session_state.left_input
    st.session_state.right_value = convert(st.session_state.left_input, st.session_state.left_currency, st.session_state.right_currency, rates)
    st.session_state.right_input = st.session_state.right_value
elif st.session_state.right_input != st.session_state.right_value:
    # 오른쪽 입력 바뀜 -> 왼쪽 자동 계산
    # 역변환: 오른쪽 기준으로 왼쪽 금액 구함
    rates_rev, _ = get_rates(st.session_state.right_currency)
    st.session_state.right_value = st.session_state.right_input
    st.session_state.left_value = convert(st.session_state.right_input, st.session_state.right_currency, st.session_state.left_currency, rates_rev)
    st.session_state.left_input = st.session_state.left_value

# 결과 출력
st.markdown(f"""
#### {st.session_state.left_value:,} {CURRENCIES[st.session_state.left_currency]}(으)로 변환:
**{st.session_state.right_value:,} {CURRENCIES[st.session_state.right_currency]}**
""")

if update_time:
    st.caption(f"최신 환율 기준: {update_time}")

st.info("환율 정보는 [exchangerate-api.com](https://www.exchangerate-api.com)에서 제공합니다.")

# 간단한 에러 안내
if st.session_state.left_currency == st.session_state.right_currency:
    st.warning("같은 통화 간 변환은 결과가 동일합니다.")

