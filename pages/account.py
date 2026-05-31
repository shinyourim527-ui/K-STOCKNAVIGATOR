import streamlit as st
from core.database import supabase
from datetime import datetime  # 📌 날짜 기록을 위해 상단에 추가

# ---------------------------------------------------
# 1. 전역 웹 페이지 메타 데이터 설정(내 계좌 대시보드 환경 초기화)
# ---------------------------------------------------
st.set_page_config(
    page_title="내 계좌",
    layout="wide"
)

# ---------------------------------------------------
# [인증 인가 보안 가드라인]
# ---------------------------------------------------
# 세션 상태 스토리지를 검사하여 비인가 유저(임의로 URL을 입력해 침입한 게스트)를 스크리닝한다
if st.session_state.get("login_user") is None:
    st.warning("로그인이 필요한 서비스입니다.") # 인라인 경고 알림 렌더링

    # 비인증 사용자를 인증 폼 페이지로 안전하게 리다이렉션하기 위한 인터페이스
    if st.button("로그인 하러가기"):
        st.switch_page("pages/login.py")    # 프레임워크 자체 라우팅 엔진을 호출하여 로그인 페이지로 강제 컨텍스트 스위칭
    st.stop()   #핵심 보안 인프라: 세션 토큰이 없는 경우, 하단의 민감한 개인 정보 조회 및 DB 쿼리 코드가 실행되지 않도록 즉각 실행 흐름을 완전 인터럽트(런타임 차단) 한다

# ---------------------------------------------------
# [세션 토큰 맵핑 및 프로필 추출 데이터 레이어]
# ---------------------------------------------------
# 전역 세선에서 암호화되거나 검증된 고유 사용자 식별자 (PK: Primary Key 역할을 하는 고유 ID)를 로컬 변수에 바인딩
login_id = st.session_state.get("login_user")


# ---------------------------------------------------
# [데이터베이스 커넥션 및 단일 레코드 페칭]
# ---------------------------------------------------
#Supabase ORM(Object-Relational Mapping) 인터페이스를 통해 'users' 테이블에서 현재 로그인한 유저의 식별자의 일치하는 데이터 스캔
response = (
    supabase
    .table("users")
    .select("*")
    .eq("id", login_id) #쿼리 필터링: SQL의 WHERM id = login_id 조건질과 매칭되는 인덱스 스캔 실행 
    .single()
    .execute()
)

user_data = response.data

if not user_data:
    st.error("사용자 정보를 불러올 수 없습니다.")
    st.stop()

# ---------------------------------------------------
# 사용자 정보 불러오기 및 예외 처리
# ---------------------------------------------------
# user_data 딕셔너리에서 값을 가져오되, 데이터가 없거나 비어있을 경우를 대비해 'or' 연산자를 사용하여 안전하게 기본값을 설정
user_name = user_data.get("user_name") or "사용자"  # 이름이 없으면 "사용자"로 지정
seed_money = user_data.get("seed_money") or 0       # 시드머니가 없으면 0원으로 지정
balance = user_data.get("balance") or 0             # 현재 잔액이 없으면 0원으로 지정

# ---------------------------------------------------
# 대시보드 메인 타이틀
# ---------------------------------------------------
st.title("📁 내 계좌")      # 웹페이지 최상단에 가장 큰 폰트로 제목 표시
st.markdown("---")          # 섹션 구분을 위한 깔끔한 가로 분할선(구분선) 삽입

# ---------------------------------------------------
# 개인화된 부제목 표시
# ---------------------------------------------------
# f-string을 활용해 사용자 이름을 문자열에 동적으로 삽입합니다.
st.subheader(f"👋 {user_name}님의 계좌")

# ---------------------------------------------------
# 2단 레이아웃 구성을 위한 컬럼 생성 (Layout)
# ---------------------------------------------------
# 화면의 가로 공간을 1:1 비율로 정확히 반으로 쪼개어 2개의 열(Column)을 만듭니다.
col1, col2 = st.columns(2)

# --- 왼쪽 첫 번째 칸 (col1): 현재 잔액 대시보드 ---
with col1:
    st.metric(
        "💰 현재 잔액",     # 지표의 이름(라벨)
        f"{balance:,}원"    # 천 단위 쉼표(,) 포맷팅 적용 후 '원' 접미사 추가
    )

# --- 오른쪽 두 번째 칸 (col2): 시드머니 대시보드 ---
with col2:
    st.metric(
        "🏦 시드머니",      # 지표의 이름(라벨)
        f"{seed_money:,}원" # 마찬가지로 천 단위 쉼표 포맷팅을 적용해 가독성 향상
    )

# ---------------------------------------------------
# 화면 하단 마감
# ---------------------------------------------------
st.markdown("---")  # 자산 정보 시각화가 끝났음을 알리는 하단 가로 구분선

# ---------------------------------------------------
# 섹션 부제목 및 기본값 설정
# ---------------------------------------------------
st.subheader("💵 시드머니 설정")    # 화면에 'H3' 크기의 부제목 표시

# 기존 seed_money사 존재하면 정수(int)로 변환하고, 없거나 0이면 기본값 5,000,000원으로 설정
# (단, 현재 아래 input_seed의 value가 0으로 고정되어 있어 이 변수는 현재 코드에서 사용되지 않고 있습니다)
default_seed = int(seed_money) if seed_money else 5000000

# ---------------------------------------------------
# 사용자 금액 입력 컴포넌트
# ---------------------------------------------------
input_seed = st.number_input(
    "시드머니를 입력하세요",
    min_value=0,                #음수 입력 방지(최소값 0)
    value=0,                    #페이지 처음 로딩 시 기본 표시값 (0원)
    step=100000,                # 버튼을 누르거나 조절할 때 10만원 단위로 증감
    format="%d"
)

# ---------------------------------------------------
# 저장 버튼 클릭 시 동작 (DB 업데이트 로직)
# ---------------------------------------------------
# use_container_width=True: 버튼을 가로 화면에 꽉 차게 확장 시킴
if st.button("저장", use_container_width=True):
    try:
        # 사용자가 입력한 금액을 정수형태로 안전하게 변환
        add_money = int(input_seed)

        # ---------------------------------------------------
        # [중요] 동시성 이슈 방지를 위한 최신 데이터 재조회 (Race Condition 방지)
        # ---------------------------------------------------
        # 사용자가 버튼을 누른 '그 순간'의 가장 정확한 잔액과 시드머니를 Supabase DB에서 가져온다
        latest_user = (
            supabase
            .table("users")                 #'users'테이블 선택
            .select("seed_money, balance")  # 조회할 컬럼 지정
            .eq("id", login_id)             # 현재 로그인한 사용자의 ID와 일치하는 조건
            .single()                       # 단건의 데이터만 반환하도록 지정
            .execute()                      # 쿼리 실행
        )

        # 데이터베이스에서 가져온 JSON 결과 값을 파이썬 딕셔너리로 추출
        latest_data = latest_user.data

        # 만약 DB에 값이 비어있다면(None) 에러 방지를 위해 0으로 초기화
        current_seed = latest_data.get("seed_money") or 0
        current_balance = latest_data.get("balance") or 0

        # ---------------------------------------------------
        # 누적 계산 (기존 자산 + 새로 추가할 금액)
        # ---------------------------------------------------
        # 시드머니를 새로 덮어쓰는 것이 아니라, 기존 금액에 '더해주는(누적)' 방식입니다.
        new_seed = current_seed + add_money
        new_balance = current_balance + add_money

        # ---------------------------------------------------
        # 데이터베이스(DB) 업데이트 수행
        # ---------------------------------------------------
        (
            supabase
            .table("users")
            .update({
                "seed_money": new_seed,     # 계산된 새로운 시드머니 반영
                "balance": new_balance      # 계산된 새로운 현재 잔액 반영
            })
            .eq("id", login_id)             # 해당 사용자의 데이터만 변경
            .execute()
        )

        # ---------------------------------------------------
        # 성공 메시지 출력 및 화면 새로고침
        # ---------------------------------------------------
        st.success("✅ 시드머니가 추가되었습니다!")     # 초록색 성공 알림창 표시
        st.rerun()                                     # 변경된 자산 데이터가 화면에 바로 반영되도록 앱 재실행  

    except Exception as e:
        # DB 연결 실패, 쿼리 오류 등 예외 발생 시 에러 메시지를 화면에 빨간색으로 표시
        st.error(f"❌ 저장 실패: {e}")

# ---------------------------------------------------
# 추천 포트폴리오 색션 헤더 (UI Section)
# ---------------------------------------------------
st.markdown("---")                  # 이전 섹션과 시각화 구분을 위한 가로선
st.header("📈 추천 투자 포트폴리오")    # 대시보드에 큰 폰트 (H2 크기)로 섹션 제목 표시

# ---------------------------------------------------
# Supabase DB에서 주식 데이터 조회
# ---------------------------------------------------
# 거래대금이 가장 높은 상위 20개 종목을 실시간으로 가져온다
stock_response = (
    supabase
    .table("stocks")                    # 'stocks'(주식 정보) 테이블 선택
    .select("*")                        # 해당 테이브르이 모든 컬럼(*) 조회
    .order("trade_value", desc=True)    # 거래대금 (trade_valye) 기준 내림차순(desc=True) 정렬 (거래 활발한 순)
    .limit(20)                          # 상위 20개 종목만 잘라서 (Limit) 가져옴
    .execute()                          # 쿼리 실행
)

# 응답 객체에서 실제 주식 데이터 리스트 (딕셔너리 배열 형태) 추출
stocks = stock_response.data

# ---------------------------------------------------
# 데이터 정제 및 추천용 종목 리스트 생성
# ---------------------------------------------------
# DB에서 가져온 원본 데이터 중, 화면에 표시하거나 계산에 사용할 수 있는 '유효한 주식'만 선별한다
valid_stocks = []

for s in stocks:
    # 딕셔너리에서 현재가(current_price)를 가져오되, 데이터가 없거나 결측치(None)이면 0으로 처리
    price = s.get("current_price") or 0

    # 예외 처리: 현재가가 0보다 큰 정상적인 종목만 필터링 (상장폐지, 거래정지, 데이터 오류 종목 제외)
    if price > 0:
        # 필터링을 거친 안전한 데이터만 key값을 깔끔하게 재정의하여 리스트에 추가(Append)
        valid_stocks.append({
            "id": s.get("id"),              # 주식 고유 ID(예: 종목코드 등)
        "name": s.get("stock_name"),        # 주식 종목명 (예: 삼성전자)
            "price": int(price)             # 소수점 제거 및 정수형(int)반환으로 금액 가독성 확보
        })

# ---------------------------------------------------
# 데이터 부족 방어 코드
# ---------------------------------------------------
# 방법 4에서 최소 5개의 종목(index 0~4)을 사용하기 때문에, 
# 정제된 주식 데이터가 5개 미만이면 추천을 진행하지 않고 경고 메시지를 띄운다
if len(valid_stocks) < 5:
    st.warning("추천용 데이터가 부족합니다.")
else:
    # 현재 투자 가능한 예산을 안전하게 정수형으로 가져온다
    budget = int(balance)

    # 생성된 4가지 투자 전략 포트폴리오를 담을 마스터 리스트
    recommend_list = []
    
    # ---------------------------------------------------
    # [방법 1] 🔥 공격형 몰빵 투자 전략
    # ---------------------------------------------------
    # - 특징: 거래대금이 가장 많은 1위 종목에 가진 모든 예산을 올인
    stock1 = valid_stocks[0]            # 거래대금 1위 종목 선택
    qty1 = budget // stock1["price"]    # '//' (몫 연산자)를 사용해 살 수 있는 최대 수량 계산
    recommend_list.append({
        "title": "🔥 공격형 몰빵 투자",
        "desc": "거래대금 최상위 종목 중심의 전략",
        "items": [
            {
                "stock_id": stock1["id"],
                "name": stock1["name"],
                "qty": qty1,
                "price": stock1["price"]
            }
        ]
    })

    # ---------------------------------------------------
    # [방법 2] ⚡ 인기 종목 분산 투자 전략
    # ---------------------------------------------------
    # - 특징: 예산을 정확히 반반(50% : 50%)씩 나누어 1위, 2위 종목에 분산 투자
    stock2 = valid_stocks[1]                    # 거래대금 2위 종목 선택
    qty_a = (budget // 2) // stock1["price"]    # 예산의 50%로 1위 종목 매수 가능한 수량
    qty_b = (budget // 2) // stock2["price"]    # 예산의 50%로 2위 종목 매수 가능한 수량
    recommend_list.append({
        "title": "⚡ 인기 종목 분산 투자",
        "desc": "인기 종목 2개를 균형 있게 분산",
        "items": [
            {
                "stock_id": stock1["id"],
                "name": stock1["name"],
                "qty": qty_a,
                "price": stock1["price"]
            },
            {
                "stock_id": stock2["id"],
                "name": stock2["name"],
                "qty": qty_b,
                "price": stock2["price"]
            }
        ]
    })

    # ---------------------------------------------------
    # [방법 3] 🛡️ 안정형 분산 투자 전략
    # ---------------------------------------------------
    # - 특징: 3개 종목에 자산을 [40% : 30% : 30%] 비율로 쪼개어 리스크를 낮춘다
    stock3 = valid_stocks[2]                  # 거래대금 3위 종목 선택
    stock4 = valid_stocks[3]                  # 거래대금 4위 종목 선택

    # 비율 계산 시 금액이 소수점이 되지 않도록 먼저 곱한 후 정수 몫(//) 연산을 수행
    qty_a = (budget * 40 // 100) // stock1["price"] # 예산의 40% 투입
    qty_b = (budget * 30 // 100) // stock3["price"] # 예산의 30% 투입
    qty_c = (budget * 30 // 100) // stock4["price"] # 예산의 30% 투입
    recommend_list.append({
        "title": "안정형 분산 투자",
        "desc": "리스크를 줄이는 분산 투자",
        "items": [
            {
                "stock_id": stock1["id"],
                "name": stock1["name"],
                "qty": qty_a,
                "price": stock1["price"]
            },
            {
                "stock_id": stock3["id"],
                "name": stock3["name"],
                "qty": qty_b,
                "price": stock3["price"]
            },
            {
                "stock_id": stock4["id"],
                "name": stock4["name"],
                "qty": qty_c,
                "price": stock4["price"]
            }
        ]
    })

   # ---------------------------------------------------
    # [방법 4] 🎯 균등 분할 투자 전략
    # ---------------------------------------------------
    stock5 = valid_stocks[4]            # 거래대금 5위 종목 선택
    qty_each = budget // 5              # 종목 한 개당 배정될 균등 예산(20%)

    recommend_list.append({
        "title": "균등 분할 투자",
        "desc": "여러 종목을 균등하게 투자",
        "items": [
            # 배정된 동일한 예산을 각 주식의 현재가로 나누어 수량을 각각 구함
            {
                "stock_id": stock1["id"],
                "name": stock1["name"],
                "qty": qty_each // stock1["price"],
                "price": stock1["price"]
            },
            {
                "stock_id": stock2["id"],
                "name": stock2["name"],
                "qty": qty_each // stock2["price"],
                "price": stock2["price"]
            },
            {
                "stock_id": stock3["id"],
                "name": stock3["name"],
                "qty": qty_each // stock3["price"],
                "price": stock3["price"]
            },
            {
                "stock_id": stock4["id"],
                "name": stock4["name"],
                "qty": qty_each // stock4["price"],
                "price": stock4["price"]
            },
            {
                "stock_id": stock5["id"],
                "name": stock5["name"],
                "qty": qty_each // stock5["price"],
                "price": stock5["price"]
            }
        ]
    })

# ---------------------------------------------------
# 추천 포트폴리오 리스트 순회 및 카드(컨테이너) 생성
# ---------------------------------------------------
# enumerate(..., 1)을 사용하여 1번부터 시작하는 인덱스(idx)와 포트폴리오 데이터(rec)를 하나씩 꺼낸다
    for idx, rec in enumerate(recommend_list, 1):

        # st.container(border=True): 각 투자 방법을 시각적으로 깔끔하게 묶어주는 외곽 테두리(상자)를 만든다
        with st.container(border=True):
            # 포트폴리오 제목 (예: 방법 1 공격형 몰빵 투자)과 부연 설명 출력
            st.subheader(f"방법 {idx}. {rec['title']}")
            st.caption(rec["desc"])

        # ---------------------------------------------------
        # 종목별 동적 컬럼(레이아웃) 생성 및 계산
        # ---------------------------------------------------
            total_cost = 0  # 이 포트폴리오를 구성하는 데 드는 총 필요 자금을 저장할 변수

            # [핵심] 포함된 종목 수(len)만큼 가로 칸(Column)을 동적으로 쪼갭니다
        # 예: 종목이 1개면 1칸, 3개면 3칸의 레이아웃이 자동으로 생성
            cols = st.columns(len(rec["items"]))

            # zip 함수를 활용해 쪼개진 스트림릿 컬럼(col)과 실제 종목 데이터(item)를 1:1로 매칭하며 순화함
            for col, item in zip(cols, rec["items"]):
                name = item["name"]     # 종목명
                qty = item["qty"]       # 추천 매수 수량
                price = item["price"]   # 종목 현재가
                cost = qty * price      # 해당 종목을 사는 데 필요한 금액 (수량 X 가격)
                total_cost += cost      # 포토폴리오 총 누적 금액에 합산

                # 쪼개진 가로 칸 (col) 내부에 종목 정보를 파란색 정보 상자 (st.info)로 렌더링 
                with col:
                    st.info(f"### {name}\n\n📦 {qty}주\n\n💰 {cost:,}원")

        # ---------------------------------------------------
        # 투자 결과 요약 (총 투자금 및 잔돈 계산)
        # ---------------------------------------------------
            remain = budget - total_cost    # 전체 예산에서 총 투자금을 차감한 '남은 잔액' 계산

            # 하단에 요약 정보를 보여줄 2단 컬럼 레이아웃 생성
            col1, col2 = st.columns(2)
            with col1:
                st.metric("💰 총 투자금", f"{total_cost:,}원")
            with col2:
                st.metric("🪙 남은 금액", f"{remain:,}원")

        # ---------------------------------------------------
        # 구매 버튼 처리 및 페이지 이동 (State & Navigation)
        # ---------------------------------------------------
        # 버튼의 key가 중복되면 스트림릿 오류가 발생하므로 f"recommend_buy_{idx}"로 고유한 Key를 부여
            if st.button(f"🛒 방법 {idx} 그대로 구매하기", key=f"recommend_buy_{idx}", use_container_width=True):

                # 사용자가 선택한 포트폴리오의 종목 리스트(`rec["items"]`)를 세션 스테이트에 임시 저장
                # 이렇게 저장해두면 다른 페이지로 이동해도 이 데이터를 기억하고 사용할 수 있음
                st.session_state["recommend_buy"] = rec["items"]

                # 주식 주문이나 자산 현황을 처리하는 대시보드 페이지 ("pages/dashboard.py")로 화면을 전환
                st.switch_page("pages/dashboard.py")

# ---------------------------------------------------
# 보유 주식 섹션 헤더 및 데이터베이스 조회
# ---------------------------------------------------
st.markdown("---")          # 이전 섹션과 시각적 구분을 위한 가로선
st.header("📦 보유 주식")   # 화면에 큰 폰트 (H2 크기)로 섹션 제목 표시

# 현재 로그인한 사용자(login_id)가 보유하고 있는 모든 주식 포지션 데이터 Supabase에서 가져온다
position_response = (
    supabase
    .table("positions")
    .select("*")
    .eq("user_id", login_id)
    .execute()
)
positions = position_response.data

# ---------------------------------------------------
# 2. 자산 평가 및 수익률 계산 프로세스 
# --------------------------------------------------
# 모든 종목을 순회하며 '총 보유 주식 자산'의 합계를 출력하기 전(상단)에 미리 계산해 두기 위한 누적 변수
total_stock_asset = 0

if not positions:
    st.info("보유 중인 주식이 없습니다.")   # 보유 포지션이 비어있을 때 알림
else:
    # 각 종목을 분석하여 화면에 출력할 정보만 정제해 담아둘 임시 버퍼 리스트
    display_items = []

    for pos in positions:
        stock_name = pos.get("stock_name")
        quantity = pos.get("quantity")
        avg_price = pos.get("avg_price")
        stock_id = pos.get("stock_id")

        # 예외 처리: 데이터 정합성 오류로 인해 수량이 0 이하인 비정상 데이터는 계산에서 제외
        if quantity <= 0:
            continue

        # 해당 종목의 가장 최신 실시간 현재가를 'stocks' 테이블에서 개별 조회
        stock_response = (
            supabase
            .table("stocks")
            .select("current_price")
            .eq("id", stock_id)
            .single()               # 단건 조회를 명시하여 딕셔너리 형태로 바로 반환받음
            .execute()
        )
        stock_data = stock_response.data
        current_price = stock_data.get("current_price") or 0

        # [금융 계산 공식]
        eval_price = current_price * quantity   # 현재 가치 기준 평가 금액 (현재가 x 수량)
        total_stock_asset += eval_price         # 전체 주식 자산 총합에 누적 합산

        buy_price = avg_price * quantity        # 내가 처음에 샀던 원금 기준 매수 금액 (평균단가 x 수량)
        profit = eval_price - buy_price         # 평가 손익 금액 (평가 금액 - 매수 금액)

        #수익률 계산: 분모가 0이 되어 프로그램이 튕기는 현상을 방지하는 삼황 연산자
        profit_rate = ((profit / buy_price) * 100) if buy_price > 0 else 0

        # UI 렌더링 루프에서 가독성 있게 꺼내 쓸 수 있도록 데이터 패킹
        display_items.append({
            "name": stock_name,
            "id": stock_id,
            "quantity": quantity,
            "eval_price": eval_price,
            "current_price": current_price,
            "profit": profit,
            "profit_rate": profit_rate
        })

    # ---------------------------------------------------
    # 계산 완료 후 총 자산 현황 먼저 출력
    # ---------------------------------------------------
    # 데이터 정제 루프가 완전히 끝났으므로, 최상단에 총 자산 지표를 당당하게 먼저 표기할 수 있음
    st.metric(
        "📈 총 보유 주식 자산",
        f"{total_stock_asset:,}원"      # 천 단위 쉼표 포맷팅
    )
    st.markdown("---")

    # ---------------------------------------------------
    # 종목별 대시보드 카드 생성 및 렌더링 (UI 4분할 레이아웃)
    # ---------------------------------------------------
    for idx, item in enumerate(display_items):
        # 개별 종목 정보를 감싸는 깔끔한 박스 테두리 컨테이너 생성
        with st.container(border=True):
            # 가로 레이아웃을 1:1:1:1 비율로 4칸 쪼개기
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.subheader(item["name"])      # 종목 이름 (큰 글씨)
                st.caption(item["id"])          # 종목 코드 또는 고유 ID (작은 부면 설명)
            with col2:
                st.metric("보유 수량", f"{item['quantity']}주")
            with col3:
                # st.metric의 3번째 인지(delta)를 상세 계산식 가이드 텍스트로 활용하는 센스 있는 연출
                st.metric(
                    "총 보유금액", 
                    f"{item['eval_price']:,}원", 
                    f"{item['current_price']:,}원 × {item['quantity']}주"
                )
            with col4:
                # 평가 손익 금액과 수익률(소수점 둘째 자리까지 지정: .2f)을 함께 표기
                st.metric(
                    "평가 손익", 
                    f"{item['profit']:,}원", 
                    f"{item['profit_rate']:.2f}%"
                )
            
            # ---------------------------------------------------
            # 종목별 실시간 매도 기능 토글 (Expander 내장 접이식 메뉴)
            # ---------------------------------------------------
            # 클릭하면 아래로 스르륵 열리는 아코디언 메뉴를 카드 내부에 내장
            with st.expander(f"📉 {item['name']} 매도"):
                sell_col1, sell_col2 = st.columns(2)        # 매도 창 내부를 다시 좌우 2단 분할
                
                with sell_col1:
                    # 매도할 수량을 정하는 숫자 입력창 생성
                    sell_qty = st.number_input(
                        "매도 수량을 입력하세요",
                        min_value=1,                # 최소 1주부터 매도 가능
                        max_value=item["quantity"], # 자신이 가진 보유 수량까지만 매도 제한 (오버 트레이당 방지)
                        value=1,                    # 기본 입력값 초기화
                        step=1,                     # 1주 단위 정수 증감
                        # [매우 중요] 반복문 내에서 컴포넌트 ID가 충돌하지 않도록 종목 ID와 인덱스를 조합해 고유 key 부여
                        key=f"sell_qty_{item['id']}_{idx}"
                    )
                
                with sell_col2:
                    # 사용자가 입력한 매도 수량과 현재 실시간 가격을 즉시 곱해서 예상 정산 금액을 보여준다
                    expected_cash = sell_qty * item["current_price"]
                    st.metric("💵 예상 정산 금액 (잔액 반영)", f"{expected_cash:,}원")
                
                # ---------------------------------------------------
                # 시장가 매도 확정 버튼 클릭 시 동작
                # ---------------------------------------------------
                # 중복 방지를 위한 고유 Key를 적용하고, 버튼을 가로로 꽉 차게 배치합니다.
                if st.button("🔴 시장가 매도 확정", key=f"sell_btn_{item['id']}_{idx}", use_container_width=True):
                    try:
                        # ---------------------------------------------------
                        # STEP 1: 유저의 최신 잔액(Balance) 갱신
                        # ---------------------------------------------------
                        # 동시성 이슈를 방지하기 위해 매도 직전 Supabase에서 최신 잔액을 다시 조회
                        user_latest = supabase.table("users").select("balance").eq("id", login_id).single().execute()
                        latest_balance = user_latest.data.get("balance") or 0

                        # 새로운 잔액 = 기존 잔액 + 이번 매도로 얻은 예상 정산 금액
                        updated_balance = latest_balance + expected_cash
                        

                        # 계산된 새로운 잔액을 유저 테이블에 업데이트
                        supabase.table("users").update({"balance": updated_balance}).eq("id", login_id).execute()
                        
                        # ---------------------------------------------------
                        # 보유 포지션(Positions) 수량 업데이트 또는 삭제
                        # ---------------------------------------------------
                        # 남은 수량 = 기존 보유 수량 - 이번에 매도한 수량
                        remain_qty = item["quantity"] - sell_qty

                        if remain_qty == 0:
                            # 전량 매도인 경우: 포지션 테이블에서 해당 종목 레코드를 완전히 삭제
                            supabase.table("positions").delete().eq("user_id", login_id).eq("stock_id", item["id"]).execute()
                        else:
                            # 부분 메도인 경우: 남은 수량으로 포지션 테이블을 업데이트
                            supabase.table("positions").update({"quantity": remain_qty}).eq("user_id", login_id).eq("stock_id", item["id"]).execute()
                        
                        # ---------------------------------------------------
                        # [제약조건 자동 매칭 연동 엔진 구현]
                        # ---------------------------------------------------
                        # DB 테이블의 'trade_type' 컬럼에 걸려있을 수 있는 Check 제약조건(예: 대소문자 구분, 한글 등)으로 인한
                        # 인서트 에러를 우회하기 위한 '유연한 폴백 알고리즘'
                        inserted = False

                        # 후보 단어인 ["SELL", "sell", "매도"]를 차례대로 대입하며 인서트를 시도
                        for type_candidate in ["SELL", "sell", "매도"]:
                            try:
                                supabase.table("trades").insert({
                                    "user_id": login_id,
                                    "stock_id": item["id"],
                                    "stock_name": item["name"],
                                    "trade_type": type_candidate,       # 후보 단어 투입
                                    "quantity": sell_qty,
                                    "price": item["current_price"],
                                    "trade_date": datetime.utcnow().isoformat()     # UTC 기준 표준 ISO 시간 포맷 저장
                                }).execute()
                                inserted = True     # 저장 성공 시 플래그 True로 변경
                                break               # 성공했으므로 다음 후보 단어 루프는 건너뛰고 탈출
                            except Exception:
                                continue            # 특정 단어에서 DB 제약조건 오류가 나면 무시하고 다음 후보 단어로 재시도 
                        
                        # 만약 위 3가지 후보 단어가 시스템 제약조건과 맞지 않아 모두 실패했을 때를 대비한 최종 풀백(안전장치)
                        if not inserted:
                            supabase.table("trades").insert({
                                "user_id": login_id,
                                "stock_id": item["id"],
                                "stock_name": item["name"],
                                "trade_type": "매도",               # 기본값인 '매도'로 마지막 강제 인서트 시도
                                "quantity": sell_qty,
                                "price": item["current_price"],
                                "trade_date": datetime.utcnow().isoformat()
                            }).execute()
                        
                        # ---------------------------------------------------
                        # 성공 피드백 및 화면 새로고침 (UI 갱신)
                        # ---------------------------------------------------
                        # 전량 매도와 부분 매도 상황에 맞는 맞춤형 초록색 성공 알림창(st.success)을 출력
                        if remain_qty == 0:
                            st.success(f"🎉 {item['name']} 종목이 전량 매도되어 거래 내역이 기록되었습니다!")
                        else:
                            st.success(f"✅ {item['name']} {sell_qty}주 매도 완료 및 거래 내역 기록! (남은 수량: {remain_qty}주)")
                        
                        # 중요: DB 작업 및 사용자 알림이 완벽히 끝난 최하단 시점에서 rerun을 호출하여 
                        # 갱신된 잔액과 보유 주식 현황이 화면에 즉시 반영되도록 대시보드를 리로드 
                        st.rerun() 

                       
                    except Exception as e:
                        # 네트워크 단절, Supabase 권한 오류 등 트랜잭션 과정에서 에러 발생 시 빨간색 에러 창으로 예외 처리
                        st.error(f"❌ 매도 처리 중 에러 발생: {e}")