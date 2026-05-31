# 로그인 화면
import streamlit as st
from core.database import supabase

# ---------------------------------------------------
# 1. 페이지 초기 설정 및 UI 레이아웃 선언
# ---------------------------------------------------
# 로그인 화면은 복잡한 지표가 없으므로 'centered'(중앙 집중형) 레이아웃으로 설정하여 시선의 분산을 막습니다.
st.set_page_config(page_title="로그인", layout="centered")

# 앱 전체를 관통하는 메인 타이틀 출력
st.title("K-STOCKNAVIGATOR")

# [UI 컴포넌트] 한 화면에서 로그인과 회원가입을 깔끔하게 오갈 수 있도록 상단 탭 메뉴를 생성합니다.
tab1, tab2 = st.tabs(["로그인", "회원가입"])

# ===================================================
# 🔑 로그인 탭 (tab1) 비즈니스 로직
# ===================================================
with tab1:
    st.subheader("로그인")

    # 유저 입력창 생성 (비밀번호는 type="password"를 지정하여 문자가 마스킹 처리되도록 보안 적용)
    login_id = st.text_input("아이디", key="login_id")
    login_pw = st.text_input("비밀번호", type="password", key="login_pw")

    if st.button("로그인"):

        # [1단계 방어 코드] 사용자가 입력을 빠뜨렸는지 빈칸 유효성 체크
        if not login_id or not login_pw:
            st.error("아이디와 비밀번호를 입력하세요.")

        else:
            try:
                # [2단계 DB 조회] 입력한 아이디와 정확히 일치하는 유저 레코드가 데이터베이스에 존재하는지 스캔
                response = supabase.table("users") \
                    .select("*") \
                    .eq("id", login_id) \
                    .execute()

                user_data = response.data

                # [3단계 예외 처리] 조회된 데이터 배열의 길이가 0이면 회원 정보가 없다는 뜻
                if len(user_data) == 0:
                    st.error("존재하지 않는 아이디입니다.")

                else:
                    # 배열의 첫 번째 요소에서 매칭된 유저 오브젝트를 꺼냅니다.
                    user = user_data[0]

                    # [4단계 비밀번호 해싱 검증 부재 우회] DB 내부의 비밀번호와 사용자가 입력한 문자열이 일치하는지 대조
                    if user["user_pw"] == login_pw:
                        st.success(f"{user['user_name']}님 로그인 성공!")

                        # ---------------------------------------------------
                        # 🔥 [핵심 전역 관리] 로그인 인증 상태 메모리 세이브
                        # ---------------------------------------------------
                        # 다른 페이지(잔고 조회, 주식 거래 등)에서 이 사람이 누구인지 계속해서 기억할 수 있도록
                        # 세션 스테이트(st.session_state) 전역 저장소에 유저 식별값과 이름을 박아둡니다.
                        st.session_state["login_user"] = user["id"]
                        st.session_state["user_name"] = user["user_name"]

                        # 로그인 장벽이 해제되었으므로 메인 대시보드 페이지("main.py")로 유저를 리다이렉트합니다.
                        st.switch_page("main.py")

                    else:
                        st.error("비밀번호가 틀렸습니다.")

            except Exception as e:
                # 데이터베이스 서버 타임아웃 등 예기치 못한 에러 캐치
                st.error(f"오류 발생: {e}")


# ===================================================
# 📝 회원가입 탭 (tab2) 비즈니스 로직
# ===================================================
with tab2:
    st.subheader("회원가입")

    # 회원가입에 필요한 신규 데이터 수집 입력 폼 구성
    # (주의: tab1의 로그인 입력창과 key값이 충돌하지 않도록 signup_ 식별자 바인딩 필수)
    new_id = st.text_input("아이디", key="signup_id")
    new_name = st.text_input("이름", key="signup_name")
    new_pw = st.text_input("비밀번호", type="password", key="signup_pw")

    if st.button("회원가입"):

        # [1단계 무결성 검증] 셋 중 하나라도 입력을 누락했다면 에러 피드백을 주고 프로세스 중단
        if not new_id or not new_name or not new_pw:
            st.error("모든 항목을 입력하세요.")

        else:
            try:
                # [2단계 중복 회원 가입 방지] 무작정 DB에 들이밀지 않고, 이미 해당 아이디를 쓰는 선점 유저가 있는지 체크쿼리 실행
                check_user = supabase.table("users") \
                    .select("*") \
                    .eq("id", new_id) \
                    .execute()

                if len(check_user.data) > 0:
                    st.error("이미 존재하는 아이디입니다.")

                else:
                    # [3단계 레코드 영속화] 중복 통과 시, 신규 회원으로 Supabase 데이터베이스 테이블에 최종 인서트
                    supabase.table("users").insert({
                        "id": new_id,
                        "user_pw": new_pw,
                        "user_name": new_name,
                        "seed_money": 0  # 초기 자산(시드머니)은 0원으로 안전하게 세팅하여 데이터 결손(Null) 방지
                    }).execute()

                    st.success("회원가입 완료! 이제 로그인 탭에서 로그인을 진행해주세요.")

            except Exception as e:
                st.error(f"오류 발생: {e}")