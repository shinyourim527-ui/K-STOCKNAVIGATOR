import FinanceDataReader as fdr
import schedule
import time
import pandas as pd
from datetime import datetime
from supabase import create_client

# 1. Supabase 설정
URL = "https://pltytmopzljqpajphmzs.supabase.co"
KEY = "sb_publishable_qaZch4fDeQ4p23fasx8Mpw_DGwvCOn2"
supabase = create_client(URL, KEY)

def collect_realtime_ranking():
    now = datetime.now()
    print(f"\n[{now.strftime('%H:%M:%S')}] 📊 실시간 시장 순위 수집 시작...")

    try:
        # 2. KRX 전체 종목 시세 가져오기
        df = fdr.StockListing('KRX')

        # 3. 거래대금(Amount) 순으로 상위 50개 정렬
        # 컬럼명이 다를 수 있어 안전하게 처리합니다.
        sort_column = 'Amount' if 'Amount' in df.columns else 'MarCap' 
        top_50 = df.sort_values(by=sort_column, ascending=False).head(50)

        for _, row in top_50.iterrows():
            # [수정 포인트] 등락률 컬럼명 대응 (Chg, Changes, Rate 중 있는 것을 사용)
            # 장 마감 후나 데이터가 없을 경우를 대비해 기본값 0.0을 설정합니다.
            change_rate = 0.0
            for col in ['Chg', 'Changes', 'Rate']:
                if col in row and pd.notna(row[col]):
                    change_rate = float(row[col])
                    break

            # 4. 데이터 가공 및 Supabase 업서트
            data = {
                "id": str(row['Code']),
                "stock_name": str(row['Name']),
                "current_price": int(row['Close']) if pd.notna(row['Close']) else 0,
                "change_rate": change_rate,
                "trade_value": int(row['Amount']) if 'Amount' in row and pd.notna(row['Amount']) else 0,
                "updated_at": now.isoformat()
            }

            # DB 업데이트
            supabase.table("stocks").upsert(data).execute()

        print(f" ✅ 현재 거래대금 상위 50개 종목으로 DB 동기화 완료!")

    except Exception as e:
        print(f" ❌ 순위 수집 중 오류 발생: {e}")

# 1분마다 실행 예약
schedule.every(1).minutes.do(collect_realtime_ranking)

if __name__ == "__main__":
    print("🚀 K-STOCK NAVIGATOR 실시간 로봇 가동 중...")
    collect_realtime_ranking() # 시작 시 즉시 실행
    
    while True:
        schedule.run_pending()
        time.sleep(1)