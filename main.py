# 홈 화면
import html #데이터 보안: 데이터베이스(Supabase) 입력/출력값에 대한 XSS(크로스 사이트 스크립팅) 공격 방어 및 문자열 이스케이프용 가용 모듈
import streamlit as st #프레임워크: 파이썬 기반 웹 애플리케이션 및 반응형 UI 레이아웃 빌더
from core.database import supabase # 백엔드 엔진: 데이터베이스 연동 및 실시간 데이터 트랜잭션 처리를 위한 Supabase 클라이언트 인스턴스

# ---------------------------------------------------
# 1. 전역 웹 페이지 메타 데이터 설정 (SPA 구조의 브라우저 환경 초기화)
# ---------------------------------------------------
st.set_page_config(
    page_title="K-STOCKNAVIGATOR",  #브라우저 탭에 표시될 플랫폼 공식 명칭
    layout="wide"   #그리드 시스템: 디바이스 해수도에 대응하고 핀테크 대시보드
)

# ---------------------------------------------------
# 2. 전역 애플리케이션 상태 관리 (State Mangement)
# ---------------------------------------------------
# 사용자가 페이지를 조작하거나 새로고침(Rerun) 히더라도, 현재 정렬 기준(State)이 초기화 되지 않고 유지되도록 Streamlit State 아키텍쳐를 이용하여 초기값 세팅
if "sort_by" not in st.session_state:
    st.session_state.sort_by = "trade_value"    #플랫폼 진입 시 '거래대금 상위 정렬'을 디폴트 상태로 바인딩
# ---------------------------------------------------
# 3. 디자인 시스템 및 웹 인젝션 스크립트
# ---------------------------------------------------
# Streamlit의 정형화된 관리자 페이지 스타일(격자 프레임)을 탈피하고, 일반 사용자가 친숙하게 느끼는 모바일 지향적의 커스터 테마를 Shadow DOM에 강제 주입 합니다
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

/* 선택 버튼 둥근 사각형 디자인 보정 */
div[data-testid="stHorizontalBlock"] div[data-testid="stButton"] button {
    background-color: #f2f4f6 !important; 
    border: none !important;
    border-radius: 8px !important;
    padding: 6px 14px !important;
    font-size: 13px !important;
    font-weight: 600 !important;
    color: #4e5937 !important;
    box-shadow: none !important;
    white-space: nowrap !important;
}

/* 현재 선택된 필터 버튼의 글씨와 배경색을 파란색으로 하이라이트 */
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
# 4. 상단 반응형 헤더 및 네비게이션 이키텍쳐 (BGM: Global Navigation Bar)
# ---------------------------------------------------
# 교수님 방어선: 화면 해상도 변화에 유연하게 대응하기 위해 가로 공간을 복합 그리드로 분할
# 전체 가로 비율 10을 기준으로 좌측 메뉴 탭 영역에 93%(`9.3`), 우측 팝오버 햄버거 메뉴에 7%(`0.7`)를 
# 정밀 배정하여, 모바일 뷰에서도 UI가 찌그러지거나 개행되지 않도록 그리드 시스템 최적화
top_col1, top_col2 = st.columns([9.3, 0.7])

# --- 4-1. 좌측 메인 카테고리 탭 (인라인 마크업 렌더링) ---
with top_col1:
    st.markdown("""
    <div class="sub-menu">
        <div class="active-tab">실시간 차트</div>
        <div>지금 뜨는 카테고리</div>
        <div>국내 투자자 동향</div>
    </div>
    """, unsafe_allow_html=True)

# --- 4-2. 우측 드롭다운 햄버거 메뉴 (세션 상태 기반 동적 인가 관리 시스템) ---
with top_col2:
    # 팝오버(Popover) 컴포넌트를 레이어로 띄워 불필요한 페이지 리로드 없이 부가 메뉴 인젝션
    with st.popover("☰"):

        # 인증 보안 제어션 A: 현재 세션에 'login_user' 키가 없는 경우 (= 비로그인 게스트 상태)
        if "login_user" not in st.session_state:
            st.markdown('<div class="menu-title">MENU</div>', unsafe_allow_html=True)

            # 레이아웃 일관성을 위해 컨테이너 너비에 100% 매칭하는 가득 찬 형태의 로그인 버튼 배치
            if st.button("login", use_container_width=True):
                st.switch_page("pages/login.py") #프레임워크 라우터 엔진을 호출하여 로그인 서브 페이지로 라우팅 전환

        # 인증 보안 제어션 B: 세션 상태에 사용자 토큰이 존재하는 경우(= 인증 완료된 회원 상태)
        else:
            # 세션에서 유저 이름을 안전하게 추출하되, 값이 누락되었을 때를 대비해 가상 풀백('사용자') 데이터 설계
            st.markdown(f'<div class="menu-title">👋 {st.session_state.get("user_name", "사용자")}님</div>', unsafe_allow_html=True)
            
            # --- 개인화 메뉴 그룹화 (라우팅 엔진 스위칭) ---

            # [메뉴 1] 계좌 자산 현황 조회 페이지 스위칭
            if st.button("📁 내 계좌", use_container_width=True):
                st.switch_page("pages/account.py")
            
            # [메뉴 2] 실시간 매매 내역 트래킹 트랜잭션 히스토리 페이지 스위칭
            if st.button("📜 거래 내역", use_container_width=True):
                st.switch_page("pages/history.py")

            # 시각적 계층 분리를 위한 연한 그레이 색상의 테마 구분선(Horizontal Rule) 강제 드로잉
            st.markdown("<hr style='margin: 10px 0; border: 0; border-top: 1px solid #eee;'>", unsafe_allow_html=True)

            # --- 세션 초기화 및 인증 해체 프로토콜 (로그아웃 처리) ---
            if st.button("로그아웃", use_container_width=True):
                # 브라우저 메모리에 가상으로 올라가 있는 유저 인증 세션 키들을 순차적으로 완전 삭제 파괴
                del st.session_state["login_user"]
                if "user_name" in st.session_state:
                    del st.session_state["user_name"]

                # 중대 사항: 세션 스토리지가 지워진 상태를 즉각 반영하여 헤더를 '비로그인 상태' UI로
                # 실시간 갱신하기 위해 프레임워크 코어 엔진의 Rerun(새로고침) 명령 강제 호출
                st.rerun()

# ---------------------------------------------------
# 5. 동적 상태 기반 컨텐츠 필터링 파트 (Dynamic Active Highlight button Group)
# ---------------------------------------------------
current_sort = st.session_state.sort_by

# 웹 가시성 향상을 위해 총합 10의 비율을 기준으로 필터 섹션을 조밀하게 수평 그리드 분할
f_col1, f_col2, f_col3, f_col4, f_col5, _ = st.columns(
    [1.0, 1.2, 1.2, 1.2, 1.2, 4.2]
)

with f_col1:
    st.markdown(
        '<div class="filter-wrapper"><div class="filter-label">국내 ∨</div></div>',
        unsafe_allow_html=True
    )

#--- [상태 제어 로직 구조] ---
# 현재 세션 상태와 매칭 되는단 하나의 버튼 객체에만 <div class="active-filter"> 마크업을 동적으로 인젝션(Wrap)하여, 프론트엔즈 상에서 시각화 활성화 피드백을 전달하는 반응형 제어문 설계를 적용
with f_col2:
    if current_sort == "trade_value": st.markdown('<div class="active-filter">', unsafe_allow_html=True)
    if st.button("거래대금", key="filter_val"):
        st.session_state.sort_by = "trade_value"
        st.rerun()  # 세션 데이터 변경 즉시 전체 도메인 트리를 동적으로 재설계하기 위해 코어 엔진 리런
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
# 6. 데이터 릴레이션 및 실시간 렌더링 서브루틴(Data Querying & Rendering Pipline)
# ---------------------------------------------------
def render_stock_list():
    current_sort = st.session_state.sort_by

    # 디폴트 쿼리 파라미터 매핑 상태 정의
    sort_column = "trade_value"
    is_desc = True

    # [ORM 동적 쿼리 분기 처리]: 사용자가 활성화한 세션 상태에 따라 백엔드 데이터베이스에 요청할 정렬 컬럼과 정렬 차수 스키마를 런타임 환경에서 유기적으로 밀드
    if current_sort == "trade_volume":
        sort_column = "trade_volume"
    elif current_sort == "change_rate_up":
        sort_column = "change_rate"
    elif current_sort == "change_rate_down":
        sort_column = "change_rate"
        is_desc = False # 급하락의 경우 오름차순 정렬 구조로 변환

    # Supabase 데이터베이스 엔진 연동 및 SQL 데이터 페칭(Fetching)트랜잭션 수행
    response = (
        supabase
        .table("stocks")
        .select("*")
        .order(sort_column, desc=is_desc)   #동적 바인딩된 변수를 파라미터로 주입하여 쿼리 효율성 극대화
        .limit(50)                          # 윈도우 페이징 기법: 무분별한 풀 스캔을 억제하고 데이터 전송 오버헤드를 줄이기 위한 상위 50개 레코드 제한 방어선
        .execute()
    )

    stocks = response.data

    # 예외 처리 가이드라인: 네트워크 단선 혹은 DB 세션 만료 등의 이슈로 데이터 셋이 공백(None)일 때 발생할 수 있는 NPE(아무것도 없는 빈 공간(null)'을 가리키는 객체를 마치 실제로 존재하는 것처럼 사용하려고 할 때 발생하는 에러) 사태를 사전에 리턴하여 애플리케이션 크래시 원천 차단
    if not stocks:
        st.warning("데이터가 없습니다.")
        return

    # 정렬 상태에 따른 가변형 컬럼 헤더 텍스트 스위칭
    value_header = (
        "거래량"
        if current_sort == "trade_volume"
        else "거래대금"
    )

    # 테이블 상단 서브 인덱스 레이벨 수평 렌더링
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

    # [메모리 최적화 및 렌더링 성능 고도화 기법] :
    # 루프문 안에서 st.markdown을 수십 번 단독 호출하면 매번 브라우저 DOM 객체를 갱신하여 웹 페이지 렌더링 성능이 극도로 저하 된다
    # 이를 해결하기 위해 메모리 버퍼 리스트를 생성하고 HTML 소스를 캐싱해 모은 뒤, 단 한 번의 조인(`.join()`) 명령으로 병합하여 단 1회만 DOM 트리 주입 처리를 수행(I/O 최적화 공법) 

    list_parts = ['<div class="stock-list">']

    for i, row in enumerate(stocks, 1):
        # 데이터 예외 방어선 1: 등랼률 파싱 및 Null 값 안전 보정 연산
        rate_raw = row.get("change_rate")
        rate = float(rate_raw) if rate_raw is not None else 0.0

        # 네이버 금융 등략률 크롤링 파싱 데이터 정합서 노이즈 보정 필터
        # (원시 데이터가 백분율 형태가 아닌 왜곡된 고수치로 입력될 경우의 스케일 축소 보정)
        if abs(rate) > 100:
            rate = rate / 100

        # 데이터 세맨틱 가이드: 연산 결과값 부호에 따른 조건부 웹 스타일링 분기
        if rate > 0:
            color_class = "red"
            sign = "+"
        elif rate < 0:
            color_class = "blue"
            sign = ""
        else:
            color_class = "gray"
            sign = ""

        # 데이터 예외 방어선 2: 현재가 데이터 무결성 보정
        price_raw = row.get('current_price')
        price_val = int(price_raw) if price_raw is not None else 0
        
        # 주식 개장 전 거래 정지 혹은 원시 데이터 장애로 인한 0원 표기 현상을 전형적인 금용권 가이드라인인 '-'로 마스킹 대체 처리
        price_str = f"{price_val:,}원" if price_val > 0 else "-"

        # 데이터 포맷 변환 엔진: 원시 정수형 데이터를 가독성 높은 금용 단위 문자열로 파싱 변환
        if current_sort == "trade_volume":
            volume_raw = row.get("trade_volume")
            volume_val = int(volume_raw) if volume_raw is not None else 0
            value_display = f"{volume_val:,}주"     # 천 단위 절삭 정규식 포맷팅(, 처리)
        else:
            value_raw = row.get("trade_value")
            value_val = int(value_raw) if value_raw is not None else 0

            # 실무 금융 대시보드 규격화: 숫자가 지나치게 길어져 레이아우이 밀리는 문제를 해결하기 위해 억/만 단위 화폐 압축 포맷 알고리즘 이식
            if value_val >= 100000000:
                value_display = f"{value_val // 100000000:,}억"
            else:
                value_display = f"{value_val // 10000:,}만"

        # 데이터 정제: 한국 거래소 원시 종목 코드 정보 접미사 추출 리포멧팅
        raw_id = row.get("id", "-")
        display_id = raw_id.split(".")[0] if "." in raw_id else raw_id

        # 메모리 버퍼 어레이에 압축 템플릿 스트링 순차 누적 적재
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

    # 분산 생성된 HTML 소스 덩어리들을 메모리 누수 없이 단일 가상 스트링 객체로 병합
    full_html = "".join(list_parts)
    
    # 렌더링 엔진 컨텍스트 최종 주입 후 화면 드로잉 완료
    st.markdown(full_html, unsafe_allow_html=True)

# ---------------------------------------------------
# 7. 메인 애플리케이션 엔트리 포인트
# ---------------------------------------------------
render_stock_list()