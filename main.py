import html
import streamlit as st
from core.database import supabase

# ---------------------------------------------------
# 페이지 설정
# ---------------------------------------------------
st.set_page_config(
    page_title="K-STOCKNAVIGATOR",
    layout="wide"
)

# ---------------------------------------------------
# 세션 상태 초기화
# ---------------------------------------------------
if "sort_by" not in st.session_state:
    st.session_state.sort_by = "trade_value"

# ---------------------------------------------------
# CSS (토스 스타일 디자인 보정 및 글자 노출 방지)
# ---------------------------------------------------
st.markdown("""
<style>
.main {
    background-color: white;
}

/* 상단 메뉴 */
.sub-menu {
    display: flex;
    gap: 25px;
    font-size: 18px;
    font-weight: bold;
    margin-bottom: 20px;
}

.active-tab {
    color: #333333;
}

/* 필터 wrapper 스타일 보정 */
.filter-wrapper {
    display: flex;
    align-items: center;
    padding: 10px 0;
}

.filter-label {
    font-size: 13px;
    font-weight: bold;
    color: black;
}

/* 🎯 토스 스타일의 선택 버튼 둥근 사각형 디자인 보정 */
div[data-testid="stHorizontalBlock"] div[data-testid="stButton"] button {
    background-color: #f2f4f6 !important; /* 기본 토스 회색 배경 */
    border: none !important;
    border-radius: 8px !important;
    padding: 6px 14px !important;
    font-size: 13px !important;
    font-weight: 600 !important;
    color: #4e5937 !important;
    box-shadow: none !important;
    white-space: nowrap !important;
}

/* 🎯 현재 선택된 필터 버튼의 글씨와 배경색을 파란색으로 하이라이트 */
.active-filter button {
    background-color: #e8f3ff !important;
    color: #1e88e5 !important;
    font-weight: bold !important;
}

/* 햄버거 버튼 */
div[data-testid='stPopoverButton'] button {
    background-color: transparent !important;
    border: none !important;
    padding: 0 !important;
    font-size: 24px !important;
    color: #333 !important;
    box-shadow: none !important;
}

/* 메뉴 */
.menu-title {
    font-size: 12px;
    color: #999;
    margin-bottom: 10px;
    font-weight: bold;
}

/* 리스트 정렬 레이아웃 균형 패치 */
.stock-list {
    width: 100%;
}

.stock-item {
    display: flex;
    align-items: center;
    padding: 15px 0;
    border-bottom: 1px solid #f2f3f5;
}

.heart {
    width: 35px;
    color: #ccd2e3;
    font-size: 18px;
}

.rank {
    width: 30px;
    font-size: 15px;
    font-weight: bold;
    color: #333;
}

.name-box {
    width: 200px;
}

.name {
    font-size: 16px;
    font-weight: 600;
    display: block;
    color: #191f28;
}

.code {
    font-size: 11px;
    color: #8b95a1;
}

.data-container {
    flex: 1;
    display: flex;
    justify-content: flex-end;
    align-items: center;
    gap: 40px;
}

.price {
    width: 120px;
    text-align: right;
    font-size: 15px;
    font-weight: 500;
    color: #191f28;
}

.change {
    width: 100px;
    text-align: right;
    font-size: 15px;
    font-weight: bold;
}

.value {
    width: 140px;
    text-align: right;
    font-size: 15px;
    font-weight: 600;
    color: #333;
}

.red {
    color: #f44336;
}

.blue {
    color: #1e88e5;
}

.gray {
    color: #999;
}
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------
# 상단 메뉴
# ---------------------------------------------------
top_col1, top_col2 = st.columns([9.3, 0.7])

with top_col1:
    st.markdown("""
    <div class="sub-menu">
        <div class="active-tab">실시간 차트</div>
        <div>지금 뜨는 카테고리</div>
        <div>국내 투자자 동향</div>
    </div>
    """, unsafe_allow_html=True)

with top_col2:
    with st.popover("☰"):
        if "login_user" not in st.session_state:
            st.markdown('<div class="menu-title">MENU</div>', unsafe_allow_html=True)
            if st.button("login", use_container_width=True):
                st.switch_page("pages/login.py")
        else:
            st.markdown(f'<div class="menu-title">👋 {st.session_state.get("user_name", "사용자")}님</div>', unsafe_allow_html=True)
            if st.button("📁 내 계좌", use_container_width=True):
                st.switch_page("pages/account.py")

            st.markdown("<hr style='margin: 10px 0; border: 0; border-top: 1px solid #eee;'>", unsafe_allow_html=True)

            if st.button("로그아웃", use_container_width=True):
                del st.session_state["login_user"]
                if "user_name" in st.session_state:
                    del st.session_state["user_name"]
                st.rerun()

# ---------------------------------------------------
# 필터 버튼 (동적 active 하이라이트 클래스 이식)
# ---------------------------------------------------
current_sort = st.session_state.sort_by

f_col1, f_col2, f_col3, f_col4, f_col5, _ = st.columns(
    [1.0, 1.2, 1.2, 1.2, 1.2, 4.2]
)

with f_col1:
    st.markdown(
        '<div class="filter-wrapper"><div class="filter-label">국내 ∨</div></div>',
        unsafe_allow_html=True
    )

with f_col2:
    if current_sort == "trade_value": st.markdown('<div class="active-filter">', unsafe_allow_html=True)
    if st.button("거래대금", key="filter_val"):
        st.session_state.sort_by = "trade_value"
        st.rerun()
    if current_sort == "trade_value": st.markdown('</div>', unsafe_allow_html=True)

with f_col3:
    if current_sort == "trade_volume": st.markdown('<div class="active-filter">', unsafe_allow_html=True)
    if st.button("거래량", key="filter_vol"):
        st.session_state.sort_by = "trade_volume"
        st.rerun()
    if current_sort == "trade_volume": st.markdown('</div>', unsafe_allow_html=True)

with f_col4:
    if current_sort == "change_rate_up": st.markdown('<div class="active-filter">', unsafe_allow_html=True)
    if st.button("급상승", key="filter_up"):
        st.session_state.sort_by = "change_rate_up"
        st.rerun()
    if current_sort == "change_rate_up": st.markdown('</div>', unsafe_allow_html=True)

with f_col5:
    if current_sort == "change_rate_down": st.markdown('<div class="active-filter">', unsafe_allow_html=True)
    if st.button("급하락", key="filter_down"):
        st.session_state.sort_by = "change_rate_down"
        st.rerun()
    if current_sort == "change_rate_down": st.markdown('</div>', unsafe_allow_html=True)


# ---------------------------------------------------
# 주식 리스트 렌더링
# ---------------------------------------------------
def render_stock_list():
    current_sort = st.session_state.sort_by

    sort_column = "trade_value"
    is_desc = True

    if current_sort == "trade_volume":
        sort_column = "trade_volume"
    elif current_sort == "change_rate_up":
        sort_column = "change_rate"
    elif current_sort == "change_rate_down":
        sort_column = "change_rate"
        is_desc = False

    response = (
        supabase
        .table("stocks")
        .select("*")
        .order(sort_column, desc=is_desc)
        .limit(50)
        .execute()
    )

    stocks = response.data

    if not stocks:
        st.warning("데이터가 없습니다.")
        return

    value_header = (
        "거래량"
        if current_sort == "trade_volume"
        else "거래대금"
    )

    st.markdown(f"""
    <div style="
        display:flex;
        justify-content:flex-end;
        font-size:12px;
        color:#999;
        margin-bottom:5px;
        padding-right:10px;
    ">
        <span style="width:120px; text-align:right;">현재가</span>
        <span style="width:100px; text-align:right;">등락률</span>
        <span style="width:140px; text-align:right;">{value_header}</span>
    </div>
    """, unsafe_allow_html=True)

    list_parts = ['<div class="stock-list">']

    for i, row in enumerate(stocks, 1):
        # 🛡️ 등락률 파싱 연산 및 보정 작업
        rate_raw = row.get("change_rate")
        rate = float(rate_raw) if rate_raw is not None else 0.0

        # 네이버 금융 등락률 텍스트 파싱 왜곡 예방 방어선 (비정상 수치 압축 보정)
        if abs(rate) > 100:
            rate = rate / 100

        if rate > 0:
            color_class = "red"
            sign = "+"
        elif rate < 0:
            color_class = "blue"
            sign = ""
        else:
            color_class = "gray"
            sign = ""

        # 🛡️ 현재가 파싱 가공 보정선
        price_raw = row.get('current_price')
        price_val = int(price_raw) if price_raw is not None else 0
        
        # 💡 현재가가 0원인 비정상 상황일 때 마크업 예외 처리 ('-' 표시 처리)
        price_str = f"{price_val:,}원" if price_val > 0 else "-"

        # 🛡️ 하단 종목 거래량/거래대금 메트릭 변환기
        if current_sort == "trade_volume":
            volume_raw = row.get("trade_volume")
            volume_val = int(volume_raw) if volume_raw is not None else 0
            value_display = f"{volume_val:,}주"
        else:
            value_raw = row.get("trade_value")
            value_val = int(value_raw) if value_raw is not None else 0
            
            if value_val >= 100000000:
                value_display = f"{value_val // 100000000:,}억"
            else:
                value_display = f"{value_val // 10000:,}만"

        # 종목코드에서 .KS 접미사가 노출되어 UI가 지저분해지는 것 방지
        raw_id = row.get("id", "-")
        display_id = raw_id.split(".")[0] if "." in raw_id else raw_id

        # 각 아이템 코드를 조각(Part)으로 고정하여 리스트에 축적
        item_html = f'<div class="stock-item">' \
                    f'  <div class="heart">♡</div>' \
                    f'  <div class="rank">{i}</div>' \
                    f'  <div class="name-box">' \
                    f'      <span class="name">{row.get("stock_name", "-")}</span>' \
                    f'      <span class="code">{display_id}</span>' \
                    f'  </div>' \
                    f'  <div class="data-container">' \
                    f'      <div class="price">{price_str}</div>' \
                    f'      <div class="change {color_class}">{sign}{rate:.2f}%</div>' \
                    f'      <div class="value">{value_display}</div>' \
                    f'  </div>' \
                    f'</div>'
        list_parts.append(item_html)

    list_parts.append("</div>")

    # 리스트에 모인 모든 안전한 HTML 문자열들을 공백 없이 깨끗하게 병합
    full_html = "".join(list_parts)
    
    # 최종 렌더링 주입
    st.markdown(full_html, unsafe_allow_html=True)

# ---------------------------------------------------
# 실행
# ---------------------------------------------------
render_stock_list()