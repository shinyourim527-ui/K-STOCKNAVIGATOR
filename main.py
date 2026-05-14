import streamlit as st
from core.database import supabase
import time

# 1. 페이지 설정
st.set_page_config(page_title="K-STOCKNAVIGATOR", layout="wide")

# 2. CSS 스타일 (파란색 언더라인 제거 및 디자인 최적화)
st.markdown("""<style>
    .main { background-color: white; }
    /* 상단 메뉴: 파란색 선을 제거하고 글자색으로만 표시 */
    .sub-menu { display: flex; gap: 25px; font-size: 18px; font-weight: bold; padding-bottom: 15px; border-bottom: 1px solid #ddd; }
    .active-tab { color: #1e88e5; }
    .filter-bar { display: flex; gap: 20px; font-size: 13px; color: #666; padding: 15px 0; }
    
    /* 리스트 아이템 레이아웃 */
    .stock-item { display: flex; align-items: center; padding: 15px 0; border-bottom: 1px solid #f2f2f2; }
    .heart { width: 35px; color: #eee; font-size: 18px; }
    .rank { width: 30px; font-size: 15px; font-weight: bold; color: #333; }
    .name-box { width: 200px; }
    .name { font-size: 16px; font-weight: 600; display: block; }
    .code { font-size: 11px; color: #999; }
    
    /* 수치 정렬 및 간격 */
    .data-container { flex: 1; display: flex; justify-content: flex-end; align-items: center; gap: 40px; }
    .price { width: 120px; text-align: right; font-size: 15px; }
    .change { width: 100px; text-align: right; font-size: 15px; font-weight: bold; }
    .value { width: 140px; text-align: right; font-size: 15px; font-weight: 600; color: #333; }
    
    .red { color: #f44336; }
    .blue { color: #1e88e5; }
</style>""", unsafe_allow_html=True)

# 3. 상단 네비게이션
st.markdown('<div class="sub-menu"><div class="active-tab">실시간 차트</div><div>지금 뜨는 카테고리</div><div>국내 투자자 동향</div></div>', unsafe_allow_html=True)
st.markdown('<div class="filter-bar"><div style="font-weight:bold; color:black;">국내 ∨</div><div style="color:#1e88e5; font-weight:bold;">거래대금</div><div>거래량</div><div>급상승</div><div>급하락</div></div>', unsafe_allow_html=True)

# 4. 데이터 호출 (거래대금 trade_value 기준 내림차순 정렬)
# 주의: DB의 trade_value 컬럼이 '숫자' 타입이어야 정확히 정렬됩니다.
response = supabase.table("stocks").select("*").order("trade_value", desc=True).limit(50).execute()
stocks = response.data

if stocks:
    # 헤더 라벨
    st.markdown('<div style="display:flex; justify-content: flex-end; font-size:12px; color:#999; margin-bottom:5px; padding-right:10px;"><span style="width:120px; text-align:right;">현재가</span><span style="width:100px; text-align:right;">등락률</span><span style="width:140px; text-align:right;">거래대금</span></div>', unsafe_allow_html=True)

    list_html = '<div class="stock-list">'
    for i, row in enumerate(stocks, 1):
        # 등락률 가공 및 보정
        rate = row.get('change_rate', 0)
        display_rate = rate / 100 if abs(rate) > 100 else rate # +12000% 같은 수치 방어
        
        color_class = "red" if display_rate > 0 else "blue" if display_rate < 0 else ""
        sign = "+" if display_rate > 0 else ""
        
        price_str = f"{int(row.get('current_price', 0)):,}원"
        # 거래대금 단위 환산 (원 -> 억)
        value_billion = f"{int(row.get('trade_value', 0) // 100000000):,}억"

        # HTML 깨짐 방지를 위해 모든 태그를 한 줄로 결합
        item_html = f'<div class="stock-item"><div class="heart">♡</div><div class="rank">{i}</div><div class="name-box"><span class="name">{row["stock_name"]}</span><span class="code">{row["id"]}</span></div><div class="data-container"><div class="price">{price_str}</div><div class="change {color_class}">{sign}{display_rate:.2f}%</div><div class="value">{value_billion}</div></div></div>'
        list_html += item_html
    
    list_html += '</div>'
    st.markdown(list_html, unsafe_allow_html=True)

# 5. 실시간 반영을 위한 자동 갱신 (10초 주기)
time.sleep(10)
st.rerun()