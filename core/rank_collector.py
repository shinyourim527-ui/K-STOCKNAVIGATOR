import FinanceDataReader as fdr
import schedule
import time
import pandas as pd
import os
from datetime import datetime
from supabase import create_client

# =========================
# Supabase 설정 (중요)
# =========================
URL = "https://pltytmopzljqpajphmzs.supabase.co"

# 🔥 반드시 service_role 키로 변경해야 정상 작동
KEY = "sb_publishable_qaZch4fDeQ4p23fasx8Mpw_DGwvCOn2"

supabase = create_client(URL, KEY)


# =========================
# 데이터 수집 함수
# =========================
def collect_realtime_ranking():
    now = datetime.now()

    try:
        df = fdr.StockListing('KRX')

        sort_column = 'Amount' if 'Amount' in df.columns else 'MarCap'
        top_50 = df.sort_values(by=sort_column, ascending=False).head(50)

        supabase_data = []

        for _, row in top_50.iterrows():

            # 안전한 등락률 처리
            change_rate = 0.0
            for col in ['Chg', 'Changes', 'Rate']:
                if col in row and pd.notna(row[col]):
                    change_rate = float(row[col])
                    break

            data = {
                "id": str(row['Code']),
                "stock_name": str(row['Name']),
                "current_price": int(row['Close']) if pd.notna(row['Close']) else 0,
                "change_rate": change_rate,
                "trade_value": int(row['Amount']) if pd.notna(row.get('Amount', 0)) else 0,
                "updated_at": now.isoformat()
            }

            supabase_data.append(data)

        # =========================
        # 🔥 핵심 개선: bulk upsert
        # =========================
        supabase.table("stocks").upsert(supabase_data).execute()

        # =========================
        # 화면 출력
        # =========================
        os.system('cls' if os.name == 'nt' else 'clear')

        print(f"📊 K-STOCK NAVIGATOR | {now.strftime('%H:%M:%S')}")
        print("=" * 65)
        print(f"{'순위':<4} | {'종목명':<14} | {'현재가':>10} | {'등락률':>8} | {'거래대금(억)':>10}")
        print("-" * 65)

        for i, (_, row) in enumerate(top_50.head(10).iterrows(), 1):

            change_rate = 0.0
            for col in ['Chg', 'Changes', 'Rate']:
                if col in row and pd.notna(row[col]):
                    change_rate = float(row[col])
                    break

            sign = "▲" if change_rate > 0 else "▼" if change_rate < 0 else " "
            amount_krw = int(row['Amount']) // 100000000 if pd.notna(row.get('Amount', 0)) else 0

            print(f"{i:<5} | {row['Name']:<14} | {int(row['Close']):>10,}원 | {sign}{abs(change_rate):>6.2f}% | {amount_krw:>12,}억")

        print("-" * 65)
        print("✅ Supabase 동기화 완료")

    except Exception as e:
        print(f"❌ 오류 발생: {e}")


# =========================
# 실행 스케줄
# =========================
schedule.every(1).minutes.do(collect_realtime_ranking)

if __name__ == "__main__":
    collect_realtime_ranking()

    while True:
        schedule.run_pending()
        time.sleep(1)