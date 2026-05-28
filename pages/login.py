import streamlit as st
from core.database import supabase

st.set_page_config(page_title="로그인", layout="centered")

st.title("K-STOCKNAVIGATOR")

tab1, tab2 = st.tabs(["로그인", "회원가입"])

# =========================
# 로그인 탭
# =========================
with tab1:
    st.subheader("로그인")

    login_id = st.text_input("아이디", key="login_id")
    login_pw = st.text_input("비밀번호", type="password", key="login_pw")

    if st.button("로그인"):

        # 빈칸 체크
        if not login_id or not login_pw:
            st.error("아이디와 비밀번호를 입력하세요.")

        else:
            try:
                # users 테이블 조회
                response = supabase.table("users") \
                    .select("*") \
                    .eq("id", login_id) \
                    .execute()

                user_data = response.data

                # 아이디 존재 확인
                if len(user_data) == 0:
                    st.error("존재하지 않는 아이디입니다.")

                else:
                    user = user_data[0]

                    # 비밀번호 확인
                    if user["user_pw"] == login_pw:
                        st.success(f"{user['user_name']}님 로그인 성공!")

                        # 🔥 로그인 상태 저장 (핵심)
                        st.session_state["login_user"] = user["id"]
                        st.session_state["user_name"] = user["user_name"]

                        # 메인 이동
                        st.switch_page("main.py")

                    else:
                        st.error("비밀번호가 틀렸습니다.")

            except Exception as e:
                st.error(f"오류 발생: {e}")


# =========================
# 회원가입 탭
# =========================
with tab2:
    st.subheader("회원가입")

    new_id = st.text_input("아이디", key="signup_id")
    new_name = st.text_input("이름", key="signup_name")
    new_pw = st.text_input("비밀번호", type="password", key="signup_pw")

    if st.button("회원가입"):

        # 빈칸 체크
        if not new_id or not new_name or not new_pw:
            st.error("모든 항목을 입력하세요.")

        else:
            try:
                # 아이디 중복 체크
                check_user = supabase.table("users") \
                    .select("*") \
                    .eq("id", new_id) \
                    .execute()

                if len(check_user.data) > 0:
                    st.error("이미 존재하는 아이디입니다.")

                else:
                    # DB 저장
                    supabase.table("users").insert({
                        "id": new_id,
                        "user_pw": new_pw,
                        "user_name": new_name,
                        "seed_money": 0
                    }).execute()

                    st.success("회원가입 완료!")

            except Exception as e:
                st.error(f"오류 발생: {e}")