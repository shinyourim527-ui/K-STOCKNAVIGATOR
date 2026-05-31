import streamlit as st
from core.database import supabase
from datetime import datetime, timedelta

# ---------------------------------------------------
# 1. 페이지 초기 설정 및 UI 레이아웃 선언
# ---------------------------------------------------
st.set_page_config(
    page_title="거래 내역",
    layout="wide"  # 4분할 계좌 지표 출력을 위해 와이드 레이아웃 적용
)

# ---------------------------------------------------
# 2. 전역 인증 보안 가드 (Authentication Guard)
# ---------------------------------------------------
# 비로그인 사용자가 주소창을 통해 직접 진입하는 것을 차단합니다.
if st.session_state.get("login_user") is None:
    st.warning("로그인이 필요한 서비스입니다.")
    if st.button("로그인 하러가기"):
        st.switch_page("pages/login.py")
    st.stop()  # 로그인하지 않았다면 이 아래쪽 코드는 아예 실행하지 않고 인터프리터 중지

# 인증을 통과한 사용자의 고유 내부 ID 세션 추출
login_id = st.session_state.get("login_user")

# ---------------------------------------------------
# 3. 타이틀 및 섹션 소개
# ---------------------------------------------------
st.title("📜 나의 거래 내역")
st.caption("과거에 체결된 매수 및 매도 기록을 최신순으로 확인합니다.")
st.markdown("---")

# ---------------------------------------------------
# 4. 데이터베이스 연동 및 2단계 교차 조회 (Data Pipeline)
# ---------------------------------------------------
with st.spinner("거래 내역을 불러오는 중..."):
    try:
        # [STEP 4-1] 유저 메타데이터 매핑
        # trades 테이블이 세션 UUID 대신 '유저 이름'을 식별자로 사용하는 구조적 문제를 해결하기 위해
        # 현재 로그인된 ID에 매칭되는 실제 사용자 이름('user_name')을 교차 조회합니다.
        user_response = (
            supabase
            .table("users")
            .select("user_name")
            .eq("id", login_id)
            .single()
            .execute()
        )
        user_name = user_response.data.get("user_name") if user_response.data else None

        # [STEP 4-2] 🚨 [핵심 보정 Query] 
        # 추출된 'user_name'(예: 신유림)을 기준으로 거래 로그(trades) 테이블을 조회합니다.
        history_response = (
            supabase
            .table("trades")
            .select("*")
            .eq("user_id", user_name)  # ID 세션 변수가 아닌 한글 이름을 파라미터로 바인딩
            .order("trade_date", desc=True) # 최신 거래 기록이 무조건 위로 오도록 역순 정렬
            .execute()
        )
        trade_history = history_response.data
    except Exception as e:
        # DB 서버 다운, 세션 만료 등의 트래픽 예외를 캐치하여 크래시 방지
        st.error(f"데이터를 가져오는 중 오류가 발생했습니다: {e}")
        st.stop()

# ---------------------------------------------------
# 5. 프론트엔드 데이터 필터링 및 전처리 (UI Filtering)
# ---------------------------------------------------
if not trade_history:
    st.info("결제 및 거래 내역이 존재하지 않습니다.")
else:
    # [컴포넌트 1] 상단 가로형 라디오 버튼 탭 필터 인터페이스 구현
    filter_type = st.radio("거래 종류 필터", ["전체", "매수", "매도"], horizontal=True)
    st.markdown("---")
    
    # 사용자가 선택한 필터(매수/매도/전체)에 부합하는 레코드만 선별해 보관할 리스트
    filtered_history = []
    
    for trade in trade_history:
        # 데이터베이스 표준화: 문자열 변환 -> 양끝 공백 제거 -> 대문자화로 비교 정합성 확보
        raw_type = str(trade.get("trade_type", "")).strip().upper() 
        
        # 다중 규격 방어 필터링 조건 분기 (영문 로그 'BUY/SELL'과 국문 로그 '매수/매도' 모두 호환 지원)
        if filter_type == "매수" and raw_type not in ["BUY", "매수"]:
            continue  # 매수 탭인데 매도가 들어오면 걸러내고 다음 루프로 스킵
        elif filter_type == "매도" and raw_type not in ["SELL", "매도"]:
            continue  # 매도 탭인데 매수가 들어오면 걸러내고 다음 루프로 스킵
            
        filtered_history.append(trade)

    # ---------------------------------------------------
    # 6. 정제 데이터 기반 동적 카드 UI 렌더링 (Data Presentation)
    # ---------------------------------------------------
    if not filtered_history:
        st.info(f"해당하는 {filter_type} 내역이 없습니다.")
    else:
        # 필터링이 완료된 거래 내역을 하나씩 순회하며 개별 컨테이너 카드 생성
        for idx, trade in enumerate(filtered_history):
            raw_type = str(trade.get("trade_type", "")).strip().upper()
            stock_name = trade.get("stock_name")
            stock_id = trade.get("stock_id")
            qty = trade.get("quantity")
            price = trade.get("price")
            
            # --- 🛡️ [방어 코드] NoneType 에러 핸들링 ---
            # 수량이나 단가가 Null(None)값으로 들어올 경우 연산 오류(TypeError)가 나므로 안전하게 0으로 치환
            safe_qty = qty if qty is not None else 0
            safe_price = price if price is not None else 0
            total_price = safe_qty * safe_price  # 총 정산 대금 계산   
            
            # --- 🕒 [시차 보정] 국제 표준시(UTC) -> 한국 표준시(KST) 전환 ---
            raw_date = trade.get("trade_date")     
            try:
                if raw_date:
                    # ISO 포맷 문자열 분석 (Z 기호를 표준 오프셋+00:00 형태로 문자열 치환 가공)
                    date_obj = datetime.fromisoformat(raw_date.replace("Z", "+00:00"))
                    # 한국 서버/클라이언트 환경에 맞추어 영국 시간(UTC)에 정확히 9시간 가산 연산
                    kst_date = date_obj + timedelta(hours=9) 
                    formatted_date = kst_date.strftime("%Y-%m-%d %H:%M:%S")
                else:
                    formatted_date = "날짜 정보 없음"
            except:
                # 파싱 포맷이 깨진 비규격 날짜가 들어올 경우 시스템 다운을 막기 위해 원본 문자열 그대로 출력하는 폴백
                formatted_date = raw_date
                
            # [시각 효과] 거래 유형(매수/매도)에 따른 컬러 텍스트 배지 지정
            if raw_type in ["BUY", "매수"]:
                type_badge = "🔴 매수"
            else:
                type_badge = "🔵 매도"
                
            # ---- [UI] 영수증 형태의 종목별 거래 내역 박스 카드 배치 ----
            with st.container(border=True):
                # 1.5 : 1 : 1.5 : 1.5 자산 정보 밀도 비중에 맞춘 컬럼 너비 분할 설정
                col1, col2, col3, col4 = st.columns([1.5, 1, 1.5, 1.5])
                
                # 1열: 종목의 기본 식별 명칭 정보
                with col1:
                    st.markdown(f"### {stock_name}")
                    st.caption(f"종목 코드: {stock_id}  |  **{type_badge}**")
                    
                # 2열: 거래 볼륨 지표
                with col2:
                    st.metric("거래 수량", f"{safe_qty:,}주")
                    
                # 3열: 가격 및 최종 단가
                with col3:
                    st.metric("체결 단가", f"{safe_price:,}원")
                    st.caption(f"총 체결 금액: **{total_price:,}원**")
                    
                # 4열: 우측 정렬된 타임스탬프 (HTML 인라인 스타일 결합)
                with col4:
                    st.markdown(
                        f"""
                        <div style='text-align: right; margin-top: 15px;'>
                            <span style='color: gray; font-size: 0.85rem;'>📅 체결 일시</span><br>
                            <span style='font-weight: bold; font-size: 1rem;'>{formatted_date}</span>
                        </div>
                        """, 
                        unsafe_allow_html=True
                    )