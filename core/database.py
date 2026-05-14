# Supabase 연결 및 DB 관련 함수들
# core/database.py

from supabase import create_client

# 본인 Supabase 정보 입력
SUPABASE_URL = "https://pltytmopzljqpajphmzs.supabase.co"
SUPABASE_KEY = "sb_publishable_qaZch4fDeQ4p23fasx8Mpw_DGwvCOn2"

supabase = create_client(
    SUPABASE_URL,
    SUPABASE_KEY
)