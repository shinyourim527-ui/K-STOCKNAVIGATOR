# 실시간 주식 거래
import streamlit as st
from core.database import supabase

# ---------------------------------------------------
# 페이지 설정 (UI 전역 설정)
# ---------------------------------------------------
st.set_page_config(
    page_title="K-STOCKNAVIGATOR",
    layout="wide"  # 화면을 좌우로 넓게 사용하여 대시보드 가독성 향상
)

# ---------------------------------------------------
# 세션 상태 관리 (로그인 세션 확인)
# ---------------------------------------------------
# 현재 앱에 로그인한 사용자의 고유 ID(또는 이메일 등)를 전역 변수에서 가져옵니다.
login_user = st.session_state.get("login_user")

# ---------------------------------------------------
# CSS 스타일 정의 (토스 스타일의 커스텀 UI 레이아웃)
# ---------------------------------------------------
st.markdown("""
<style>
.stock-card {
    background-color:#ffffff;
    border:1px solid #eef2f6;
    border-radius:20px;
    padding:24px;
    margin-bottom:20px;
    box-shadow:0 4px 12px rgba(0,0,0,0.04);
}
.stock-name {
    font-size:24px;
    font-weight:bold;
    color:#191f28;
}
.stock-code {
    font-size:13px;
    color:#8b95a1;
}
.price {
    font-size:28px;
    font-weight:bold;
    margin-top:10px;
}
/* 등락률에 따른 한국식 주식 색상 정의 (상승: 빨강, 하락: 파랑, 보합: 회색) */
.red { color:#f44336; }
.blue { color:#1e88e5; }
.gray { color:#999; }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------
# 대시보드 상단 타이틀
# ---------------------------------------------------
st.title("📈 실시간 주식 거래")
st.markdown("---")

# ---------------------------------------------------
# 사용자 실시간 잔액 표시 (로그인 시에만 활성화)
# ---------------------------------------------------
if login_user:
    # 쿼리: 유저 테이블에서 현재 로그인된 사용자의 잔액(balance)만 실시간 조회
    user_response = (
        supabase
        .table("users")
        .select("balance")
        .eq("id", login_user)
        .single()
        .execute()
    )
    user_data = user_response.data
    balance = user_data.get("balance") or 0

    # 현재 투자 가능 자산을 가독성 좋게 대형 메트릭으로 출력
    st.metric(
        "💰 현재 잔액",
        f"{balance:,}원"
    )
    st.markdown("---")

# ---------------------------------------------------
# 주식 데이터 원본 조회 (Market Data Fetching)
# ---------------------------------------------------
# 거래대금(trade_value)이 높은 순으로 시장에서 가장 핫한 상위 30개 종목을 빌드업합니다.
response = (
    supabase
    .table("stocks")
    .select("*")
    .order("trade_value", desc=True)
    .limit(30)
    .execute()
)
stocks = response.data

# ---------------------------------------------------
# 주식 카드 리스트 출력 루프 (Dynamic UI Render)
# ---------------------------------------------------
for row in stocks:
    stock_id = row.get("id")
    stock_name = row.get("stock_name")
    current_price = row.get("current_price") or 0
    change_rate = row.get("change_rate") or 0
    trade_value = row.get("trade_value") or 0

    # [UI 조건문] 등락률 상태에 따른 색상 클래스 및 부호(+, -) 분기 처리
    if change_rate > 0:
        color_class = "red"
        sign = "+"
    elif change_rate < 0:
        color_class = "blue"
        sign = ""  # 음수는 변수 자체에 마이너스가 포함되어 있으므로 공백 처리
    else:
        color_class = "gray"
        sign = ""

    # ---------------------------------------------------
    # 주식 정보 개별 카드 (Border Container)
    # ---------------------------------------------------
    with st.container(border=True):
        # 비율 분할: 왼쪽 정보 구역(7) vs 오른쪽 매수/로그인 제어 구역(3)
        col1, col2 = st.columns([7, 3])

        # ---- [왼쪽] 주식 시세 정보 구역 ----
        with col1:
            st.markdown(f"""
            <div class="stock-name">{stock_name}</div>
            <div class="stock-code">{stock_id}</div>
            <div class="price">{current_price:,}원</div>
            <div class="{color_class}">{sign}{change_rate:.2f}%</div>
            """, unsafe_allow_html=True)
            
            st.caption(f"거래대금: {trade_value:,}원")

        # ---- [오른쪽] 거래 제어 및 세션 핸들링 구역 ----
        with col2:
            # 예외 처리: 비로그인 유저인 경우 매수 차단 및 로그인 페이지 유도
            if login_user is None:
                st.warning("로그인 필요")
                if st.button("로그인", key=f"login_{stock_id}"):
                    st.switch_page("pages/login.py")
            
            # 로그인 유저인 경우 정상 거래 활성화
            else:
                # 사용자가 직접 입력할 수 있는 수량 스핀박스
                buy_qty = st.number_input(
                    "수량",
                    min_value=1,
                    step=1,
                    key=f"qty_{stock_id}"
                )
                total_price = current_price * buy_qty
                st.write(f"총 금액: {total_price:,}원")

                # ---------------------------------------------------
                # 🤝 추천 포트폴리오 데이터 자동 연동 엔진 (장바구니 기능과 유사)
                # ---------------------------------------------------
                # 이전 페이지(추천 포트폴리오)에서 '그대로 구매하기'를 누르고 온 경우 데이터가 세션에 남아있습니다.
                recommend_data = st.session_state.get("recommend_buy")

                if recommend_data:
                    for item in recommend_data:
                        # 세션에 저장된 종목 ID와 현재 카드의 종목 ID가 일치하는지 스캔
                        if item["stock_id"] == stock_id:
                            buy_qty = item["qty"]  # 추천된 수량으로 변수 강제 오버라이딩
                            total_price = buy_qty * current_price  # 총 대금 재계산
                            
                            # 알림: 사용자에게 포트폴리오 수량이 자동 매칭되었음을 시각적으로 표시
                            st.success(f"추천 포트폴리오 적용됨: {buy_qty}주")

                # ---------------------------------------------------
                # 🛒 실제 매수 실행 프로세스 (DB 트랜잭션 구역)
                # ---------------------------------------------------
                if st.button("🛒 매수하기", key=f"buy_{stock_id}", use_container_width=True):
                    
                    # 1단계: 동시성 처리를 위해 매수 클릭 직전의 사용자 잔액 실시간 조회
                    user_response = (
                        supabase
                        .table("users")
                        .select("balance")
                        .eq("id", login_user)
                        .single()
                        .execute()
                    )
                    user_data = user_response.data
                    current_balance = user_data.get("balance") or 0

                    # 2단계: 구매 한도 초과 검증 (주식 앱의 기본 방어 코드)
                    if current_balance < total_price:
                        st.error("잔액이 부족합니다.")
                    else:
                        # 3단계: 유저 잔액 차감 업데이트
                        new_balance = current_balance - total_price
                        (
                            supabase
                            .table("users")
                            .update({"balance": new_balance})
                            .eq("id", login_user)
                            .execute()
                        )

                        # 4단계: 기존에 사둔 동일 주식이 잔고에 있는지 포지션 확인 조회
                        pos_response = (
                            supabase
                            .table("positions")
                            .select("*")
                            .eq("user_id", login_user)
                            .eq("stock_id", stock_id)
                            .execute()
                        )
                        existing = pos_response.data

                        # 분기 A: 이미 보유 중인 종목인 경우 -> [물타기/불타기 평단가 가중평균 계산]
                        if existing:
                            old_qty = existing[0]["quantity"]
                            old_avg = existing[0]["avg_price"]
                            
                            new_qty = old_qty + buy_qty  # 보유 수량 합산
                            
                            # [금융 공식] 평단가 계산식 = ((기존수량 * 기존평단) + 이번투자금) / 총수량
                            new_avg = int(((old_qty * old_avg) + total_price) / new_qty)

                            # 계산된 수량과 새로운 평단가로 포지션 테이블 업데이트
                            (
                                supabase
                                .table("positions")
                                .update({
                                    "quantity": new_qty,
                                    "avg_price": new_avg
                                })
                                .eq("id", existing[0]["id"])
                                .execute()
                            )

                        # 분기 B: 생전 처음 사는 신규 종목인 경우 -> [신규 포지션 생성]
                        else:
                            (
                                supabase
                                .table("positions")
                                .insert({
                                    "user_id": login_user,
                                    "stock_id": stock_id,
                                    "stock_name": stock_name,
                                    "quantity": buy_qty,
                                    "avg_price": current_price  # 현재 산 가격이 곧 평단가가 됨
                                })
                                .execute()
                            )

                        # 5단계: 감사(Audit) 및 로그 관리를 위한 거래 히스토리(trades) 저장
                        (
                            supabase
                            .table("trades")
                            .insert({
                                "user_id": login_user,
                                "stock_id": stock_id,
                                "stock_name": stock_name,
                                "quantity": buy_qty,
                                "price": current_price,
                                "trade_type": "BUY"  # 매수로그 명시
                            })
                            .execute()
                        )

                        # 6단계: 성공 피드백 전달 및 연동 세션 초기화 후 화면 청소
                        st.success(f"{stock_name} {buy_qty}주 매수 완료!")

                        # 구매가 끝났으므로 추천 포트폴리오 임시 세션은 메모리에서 삭제하여 다음 거래에 혼선 방지
                        if "recommend_buy" in st.session_state:
                            del st.session_state["recommend_buy"]

                        # 즉시 대시보드를 새로고침하여 차감된 잔액과 포지션 상태를 화면에 동기화
                        st.rerun()