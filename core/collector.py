import yfinance as yf
from supabase import create_client
from datetime import datetime

# Supabase 설정 (유림님의 정보 입력)
URL = "https://pltytmopzljqpajphmzs.supabase.co"
KEY = "sb_publishable_qaZch4fDeQ4p23fasx8Mpw_DGwvCOn2"
supabase = create_client(URL, KEY)

# 시장의 상태를 보여줄 핵심 지수 리스트
MARKET_INDICES = [
    ("^KS11", "코스피"),
    ("^KQ11", "코스닥"),
    ("^IXIC", "나스닥"),
    ("005930.KS", "삼성전자") # 기준점용
]

def sync_market_status():
    now = datetime.now()
    print(f"[{now.strftime('%H:%M:%S')}] 🌏 주요 시장 지수 업데이트 중...")

    for ticker_symbol, name in MARKET_INDICES:
        try:
            ticker = yf.Ticker(ticker_symbol)
            df = ticker.history(period="2d")
            
            if len(df) < 2: continue

            current_price = float(df['Close'].iloc[-1])
            prev_price = float(df['Close'].iloc[-2])
            change_rate = round(((current_price - prev_price) / prev_price) * 100, 2)

            data = {
                "id": ticker_symbol,
                "stock_name": name,
                "current_price": current_price,
                "change_rate": change_rate,
                "updated_at": now.isoformat()
            }

            # 'market_indices'라는 별도의 테이블에 저장하면 더 깔끔해요!
            supabase.table("stocks").upsert(data).execute()
            print(f" ✅ {name} 업데이트 완료")

        except Exception as e:
            print(f" ❌ {name} 오류: {e}")

if __name__ == "__main__":
    sync_market_status()