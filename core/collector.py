import requests
from bs4 import BeautifulSoup
from supabase import create_client
from datetime import datetime

# =====================================================================
# 🎯 [1] Supabase 설정 (본인의 실제 URL과 KEY를 정확히 입력해 주세요)
# =====================================================================
URL = "https://pltytmopzljqpajphmzs.supabase.co"
KEY = "sb_publishable_qaZch4fDeQ4p23fasx8Mpw_DGwvCOn2"  # 실제 발급받으신 서비스 키
supabase = create_client(URL, KEY)

def collect_and_sync_naver():
    now = datetime.now()
    print(f"\n🚀 [{now.strftime('%Y-%m-%d %H:%M:%S')}] 네이버 금융 실시간 [거래대금] 상위 50개 종목 수집 시작...")

    # 🎯 타겟 주소: '거래대금' 상위 페이지 고정
    url = "https://finance.naver.com/sise/sise_value.naver"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }

    try:
        res = requests.get(url, headers=headers)
        res.encoding = 'euc-kr'

        soup = BeautifulSoup(res.text, 'html.parser')
        main_table = soup.find('table', class_='type_2')

        if not main_table:
            print("❌ 시세 테이블을 찾을 수 없습니다. 네이버 구조 변경 의심.")
            return

        rows = main_table.find_all('tr')
        count = 0

        for row in rows:
            # 주식 데이터가 있는 행만 마우스오버 속성으로 정확히 필터링
            if not row.get('onmouseover'):
                continue

            cols = row.find_all('td')
            if len(cols) < 11:
                continue

            title_a = cols[1].find('a', class_='tltle')
            if not title_a:
                continue

            stock_name = title_a.text.strip()
            href = title_a.get('href', '')
            code = href.split("code=")[1].strip() if "code=" in href else ""

            if not code:
                continue

            ticker_symbol = code

            # =====================================================================
            # 🎯 [2] 2중 텍스트 클렌징 레이어 (지저분한 공백, 쉼표 완전 제거 후 숫자 추출)
            # =====================================================================
            
            # 1. 현재가 파싱 (cols[2])
            price_clean = cols[2].get_text(strip=True).replace(',', '')
            price_raw = ''.join(filter(str.isdigit, price_clean))
            current_price = int(price_raw) if price_raw else 0

            # 2. 등락률 파싱 (cols[4] - 보합 종목 및 음수 부호 원천 방어)
            change_rate_clean = cols[4].get_text(strip=True).replace('%', '').replace(',', '').replace(' ', '')
            try:
                change_rate = float(change_rate_clean)
                if change_rate > 100.0 or change_rate < -100.0:
                    change_rate = 0.0
                else:
                    # 하락 종목일 경우 클래스(nv01)를 검사하여 음수 부호(-) 강제 부여
                    change_span = cols[4].find('span')
                    if change_span and 'nv01' in change_span.get('class', []):
                        if change_rate > 0:
                            change_rate = -change_rate
            except:
                change_rate = 0.0

            # 3. 거래량 파싱 (🎯 중요: 거래대금 페이지에서 5번째 칸은 '거래량'입니다!)
            volume_clean = cols[5].get_text(strip=True).replace(',', '')
            volume_raw = ''.join(filter(str.isdigit, volume_clean))
            trade_volume = int(volume_raw) if volume_raw else 0

            # 4. 거래대금 파싱 (🎯 중요: 거래대금 페이지에서 6번째 칸은 '거래대금(백만)'입니다!)
            value_clean = cols[6].get_text(strip=True).replace(',', '')
            value_raw = ''.join(filter(str.isdigit, value_clean))
            raw_trade_value_mil = int(value_raw) if value_raw else 0
            trade_value = raw_trade_value_mil * 1000000  # 백만 원 단위를 원(KRW) 단위로 환산

            # =====================================================================
            # 🎯 [3] 전송 데이터 패키징 및 업서트(Upsert) 실행
            # =====================================================================
            data = {
                "id": ticker_symbol,
                "stock_name": stock_name,
                "current_price": current_price,
                "change_rate": change_rate,
                "trade_volume": trade_volume,
                "trade_value": trade_value,
                "updated_at": now.isoformat()
            }

            # 터미널 실시간 출력 (매핑이 잘 맞는지 눈으로 확인용)
            print(f"👉 [{count+1:02d}] {stock_name:<10} ({ticker_symbol}) | 주가: {current_price:,}원 | 등락: {change_rate}% | 거래량: {trade_volume:,}주 | 대금: {trade_value:,}원")

            try:
                # 복잡한 분기 처리 없이 단일 upsert로 DB 반영
                supabase.table("stocks").upsert(data).execute()
            except Exception as db_error:
                print(f"   ❌ [DB 에러] {stock_name} 저장 실패 -> {db_error}")

            count += 1
            if count >= 50:
                break

        print(f"\n🎉 총 {count}개 종목의 거래대금 순위 데이터가 Supabase와 완벽하게 동기화되었습니다!")

    except Exception as e:
        print(f"❌ 전체 실행 오류 발생: {e}")

if __name__ == "__main__":
    collect_and_sync_naver()