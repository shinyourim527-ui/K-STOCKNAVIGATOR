import streamlit as st
from core.database import supabase

# ---------------------------------------------------
# 페이지 설정
# ---------------------------------------------------
st.set_page_config(
    page_title="내 계좌 - K-STOCKNAVIGATOR",
    layout="wide"
)

# ---------------------------------------------------
# 토스 스타일 CSS 커스텀 디자인 (구조 최적화)
# ---------------------------------------------------
st.markdown("""
<style>
.main {
    background-color: #f9fafb;
}
.account-title {
    font-size: 24px;
    font-weight: 700;
    color: #191f28;
}
/* 총 자산 카드 스타일 */
.asset-card {
    background-color: white;
    border-radius: 16px;
    padding: 24px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.02);
    margin-bottom: 20px;
}
.asset-label {
    font-size: 14px;
    color: #8b95a1;
    margin-bottom: 8px;
}
.asset-amount {
    font-size: 32px;
    font-weight: 700;
    color: #191f28;
    margin-bottom: 8px;
}
.asset-profit {
    font-size: 16px;
    font-weight: 600;
}
/* 예수금 라인 */
.sub-info-box {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 16px 24px;
    background-color: white;
    border-radius: 16px;
    margin-bottom: 30px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.02);
}
.sub-info-label {
    font-size: 15px;
    color: #4e5937;
    font-weight: 600;
}
.sub-info-val {
    font-size: 16px;
    font-weight: 600;
    color: #191f28;
}
/* 보유 주식 리스트 */
.section-title {
    font-size: 18px;
    font-weight: 700;
    color: #191f28;
    margin-bottom: 15px;
    padding-left: 4px;
}
.holding-list-container {
    background-color: white;
    border-radius: 16px;
    padding: 10px 24px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.02);
}
.holding-item {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 18px 0;
    border-bottom: 1px solid #f2f3f5;
}
.name-box {
    width: 220px;
}
.name {
    font-size: 16px;
    font-weight: 600;
    color: #191f28;
    display: block;
}
.qty-avg {
    font-size: 12px;
    color: #8b95a1;
    margin-top: 2px;
}
.data-container {
    display: flex;
    justify-content: flex-end;
    align-items: center;
    gap: 50px;
}
.eval-price {
    width: 130px;
    text-align: right;
    font-size: 16px;
    font-weight: 500;
    color: #191f28;
}
.holding-change {
    width: 110px;
    text-align: right;
    font-size: 15px;
    font-weight: bold;
}
/* 색상 클래스 */
.red { color: #f44336; }
.blue { color: #1e88e5; }
.gray { color: #8b95a1; }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------
# 상단 내비게이션
# ---------------------------------------------------
nav_col1, nav_col2 = st.columns([8.5, 1.5])
with nav_col1:
    st.markdown('<div class="account-title">내 계좌</div>', unsafe_allow_html=True)
with nav_col2:
    if st.button("← 메인으로", use_container_width=True):
        st.switch_page("main.py")

st.markdown("<br>", unsafe_allow_html=True)

# ---------------------------------------------------
# 💰 [시드머니 300만 원 매칭 자산 계산 데이터 세트]
# ---------------------------------------------------
# 초기 투자금 3,000,000원에 맞게 보유 주식 수량과 평단가를 현실적으로 수정했습니다.
my_stocks = [
    {"name": "삼성전자", "code": "005930", "qty": 20, "avg_price": 68000, "current_price": 71200},
    {"name": "SK하이닉스", "code": "006660", "qty": 5, "avg_price": 165000, "current_price": 174500},
    {"name": "현대차", "code": "005380", "qty": 3, "avg_price": 245000, "current_price": 238000}
]

# 예수금 (300만 원 중 주식을 사고 남은 현금 잔액 현황)
cash_balance = 345000  

total_purchase_price = 0  # 총 매수 금액
total_eval_price = 0      # 총 평가 금액

# 각 종목별 실시간 평가금 및 수익 계산 루프
for stock in my_stocks:
    purchase_val = stock["qty"] * stock["avg_price"]         # 매수금액
    eval_val = stock["qty"] * stock["current_price"]          # 평가금액
    
    stock["purchase_value"] = purchase_val
    stock["eval_value"] = eval_val
    stock["profit"] = eval_val - purchase_val                # 종목별 수익금
    stock["rate"] = (stock["profit"] / purchase_val) * 100 if purchase_val > 0 else 0.0
    
    total_purchase_price += purchase_val
    total_eval_price += eval_val

# 🎯 총 자산 = 현재 보유한 주식 가치 전체 + 남은 현금(예수금)
total_asset = total_eval_price + cash_balance
# 🎯 총 수익금 = 총 평가금액 - 총 매수금액
total_profit = total_eval_price - total_purchase_price
# 🎯 총 수익률
profit_rate = (total_profit / total_purchase_price) * 100 if total_purchase_price > 0 else 0.0

# 자산 수익률에 따른 디자인 색상 분기
color_class = "red" if total_profit > 0 else ("blue" if total_profit < 0 else "gray")
sign = "+" if total_profit > 0 else ""

# 1. 총 자산 카드 렌더링
st.markdown(f"""
<div class="asset-card">
    <div class="asset-label">보유 자산 (시드머니: 300만 원)</div>
    <div class="asset-amount">{total_asset:,}원</div>
    <div class="asset-profit {color_class}">총 수익 {sign}{total_profit:,}원 ({sign}{profit_rate:.2f}%)</div>
</div>
""", unsafe_allow_html=True)

# 2. 예수금 카드 렌더링
st.markdown(f"""
<div class="sub-info-box">
    <div class="sub-info-label">주문 가능 현금 (예수금)</div>
    <div class="sub-info-val">{cash_balance:,}원</div>
</div>
""", unsafe_allow_html=True)

# ---------------------------------------------------
# 3. 보유 주식 리스트 섹션 (Streamlit 안전 렌더링 방식으로 정정)
# ---------------------------------------------------
st.markdown('<div class="section-title">보유 주식</div>', unsafe_allow_html=True)

# 외부 감싸는 큰 흰색 박스 열기
st.markdown('<div class="holding-list-container">', unsafe_allow_html=True)

# 개별 종목을 루프 돌며 안전하게 하나씩 바인딩하여 렌더링
for stock in my_stocks:
    s_color = "red" if stock["profit"] > 0 else ("blue" if stock["profit"] < 0 else "gray")
    s_sign = "+" if stock["profit"] > 0 else ""
    
    item_html = f"""
    <div class="holding-item">
        <div class="name-box">
            <span class="name">{stock['name']}</span>
            <span class="qty-avg">{stock['qty']}주 · 평단 {stock['avg_price']:,}원</span>
        </div>
        <div class="data-container">
            <div class="eval-price">{stock['eval_value']:,}원</div>
            <div class="holding-change {s_color}">{s_sign}{stock['rate']:.2f}%</div>
        </div>
    </div>
    """
    # 리스트에 모으지 않고 즉시 화면에 독립 드로잉하여 브라우저 파싱 버그를 원천 차단합니다.
    st.markdown(item_html, unsafe_allow_html=True)

# 외부 감싸는 큰 박스 닫기
st.markdown('</div>', unsafe_allow_html=True)