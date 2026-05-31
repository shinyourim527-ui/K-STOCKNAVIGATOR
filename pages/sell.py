import streamlit as st
from core.database import supabase

# ---------------------------------------------------
# 1. 페이지 글로벌 레이아웃 설정
# ---------------------------------------------------
st.set_page_config(
    page_title="주식 매도",
    layout="wide"  # 정보를 좌우로 넓게 배치하여 시각적 피로도를 줄임
)

# ---------------------------------------------------
# 2. 전역 인증 보안 가드 (Authentication Guard)
# ---------------------------------------------------
# 세션에 로그인 정보가 없으면 매도 기능에 접근할 수 없도록 원천 차단합니다.
if st.session_state.get("login_user") is None:
    st.warning("로그인이 필요한 서비스입니다.")
    if st.button("로그인 하러가기"):
        st.switch_page("pages/login.py")
    st.stop()  # 인증 실패 시 스크립트 실행 즉시 중단

# 인증을 통과한 유저의 고유 식별 ID 바인딩
login_id = st.session_state.get("login_user")

# ---------------------------------------------------
# 3. 헤더 및 섹션 소개
# ---------------------------------------------------
st.title("📉 주식 매도하기")
st.caption("보유 중인 주식을 시장가로 매도하여 예수금으로 전환합니다.")
st.markdown("---")

# ---------------------------------------------------
# 4. 데이터베이스 연동 (사용자 자산 및 포지션 실시간 스캔)
# ---------------------------------------------------
# [STEP 4-1] 예수금 합산을 위해 현재 유저의 기존 잔액(balance) 조회
user_response = supabase.table("users").select("balance").eq("id", login_id).single().execute()
user_balance = user_response.data.get("balance") or 0

# [STEP 4-2] 현재 유저가 보유 중인 모든 주식 포지션(positions) 레코드 조회
position_response = (
    supabase
    .table("positions")
    .select("*")
    .eq("user_id", login_id)
    .execute()
)
positions = position_response.data

# ---------------------------------------------------
# 5. 매도 제어 화면 비즈니스 로직
# ---------------------------------------------------
if not positions:
    # 예외 처리: 들고 있는 주식이 아예 없는 경우 화면 인터페이스 차단
    st.info("현재 보유 중인 주식이 없습니다. 매도할 종목이 없습니다.")
else:
    # 스트림릿 셀렉트박스(st.selectbox)에 주입할 동적 옵션 딕셔너리 생성
    stock_options = {}
    
    # 보유한 종목들을 순회하며 실시간 시장가(Current Price) 매칭 루프 가동
    for pos in positions:
        stock_id = pos.get("stock_id")
        stock_name = pos.get("stock_name")
        quantity = pos.get("quantity")
        
        # [실시간 시세 동기화] 포지션에 기록된 과거 가격이 아닌, stocks 테이블의 '진짜 현재가'를 긁어옵니다.
        stock_response = supabase.table("stocks").select("current_price").eq("id", stock_id).single().execute()
        current_price = stock_response.data.get("current_price") or 0
        
        # 데이터 무결성 검증: 보유 수량이 0주 이하인 유령 데이터는 매도 리스트에서 원천 제외
        if quantity > 0:
            # 사용자가 가독성 좋게 선택할 수 있도록 문자열 포맷팅 라벨 생성
            label = f"{stock_name} ({stock_id}) | 보유: {quantity}주 | 현재가: {current_price:,}원"
            
            # 딕셔너리에 라벨을 Key로, 하위 상세 데이터를 Value로 저장
            stock_options[label] = {
                "position_id": pos.get("id"), 
                "stock_id": stock_id,
                "stock_name": stock_name,
                "owned_qty": quantity,
                "current_price": current_price
            }

    # 보유는 하고 있으나 수량이 모두 0인 특수 상황 방어
    if not stock_options:
        st.info("매도 가능한 주식이 없습니다.")
        st.stop()

    # ---------------------------------------------------
    # 6. 매도 주문 UI 레이아웃 빌드 (Interactive UI)
    # ---------------------------------------------------
    # 사용자가 종목을 선택하면 딕셔너리에서 해당 종목의 금융 메타데이터를 역참조합니다.
    selected_label = st.selectbox("매도할 종목을 선택하세요", list(stock_options.keys()))
    selected_stock = stock_options[selected_label]

    # 화면을 2분할(5:5)하여 좌측에는 종목 정보, 우측에는 주문 제어판 배치
    col1, col2 = st.columns(2)
    
    # ---- [좌측 컬럼] 선택된 주식 요약 브리핑 ----
    with col1:
        st.info(
            f"""
            ### 선택한 종목 정보
            * **종목명:** {selected_stock['stock_name']}
            * **보유 수량:** {selected_stock['owned_qty']}주
            * **현재 가격:** {selected_stock['current_price']:,}원
            """
        )

    # ---- [우측 컬럼] 수량 입력 및 정산 대금 계산기 ----
    with col2:
        # [핵심 가드 코드] max_value를 현재 보유 수량으로 강제 결착시켜 
        # 자기가 가진 주식보다 더 많이 매도하는 주문 실수(오버 매도)를 프론트 단에서 원천 봉쇄합니다.
        sell_qty = st.number_input(
            "매도할 수량을 입력하세요",
            min_value=1,
            max_value=selected_stock['owned_qty'],
            value=1,
            step=1
        )
        
        # 실시간 예상 예수금 유입 대금 연산
        total_sell_price = sell_qty * selected_stock['current_price']
        st.metric("💵 예상 체결 금액", f"{total_sell_price:,}원")

    st.markdown("---")

    # ---------------------------------------------------
    # 7. 🔴 시장가 매도 트랜잭션 단행 구역
    # ---------------------------------------------------
    if st.button("🔴 시장가 매도 확정", use_container_width=True):
        try:
            # [STEP 7-1] 유저 자산 업데이트: 기존 잔액 + 매도 체결금액
            new_balance = user_balance + total_sell_price
            supabase.table("users").update({"balance": new_balance}).eq("id", login_id).execute()

            # [STEP 7-2] 보유 수량 차감 및 청산 분기 처리
            remain_qty = selected_stock['owned_qty'] - sell_qty
            
            if remain_qty == 0:
                # 분기 A [전량 매도 / 완판]: 잔고 수량이 0이므로 DB 포지션 테이블에서 레코드 완전 삭제(Delete)
                supabase.table("positions").delete().eq("user_id", login_id).eq("stock_id", selected_stock['stock_id']).execute()
                st.success(f"🎉 {selected_stock['stock_name']} 전량 매도 완료!")
            else:
                # 분기 B [부분 매도 / 털기]: 남은 수량이 존재하므로 DB 포지션 테이블의 수량 컬럼만 차감(Update)
                supabase.table("positions").update({"quantity": remain_qty}).eq("user_id", login_id).eq("stock_id", selected_stock['stock_id']).execute()
                st.success(f"✅ {selected_stock['stock_name']} {sell_qty}주 매도 완료! (남은 수량: {remain_qty}주)")

            # [STEP 7-3] 데이터 동기화 리로드
            # 모든 DB 트랜잭션이 성공하면 화면을 즉시 새로고침하여 
            # 바뀐 예수금 잔액과 갱신된 보유 주식 상태를 대시보드에 즉각 반영합니다.
            st.rerun()

        except Exception as e:
            # 네트워크 통신 장애 또는 Supabase RLS 권한 위반 등 에러 발생 시 예외 롤백 메시지 출력
            st.error(f"❌ 매도 처리 중 오류가 발생했습니다: {e}")