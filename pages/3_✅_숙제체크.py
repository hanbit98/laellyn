import streamlit as st
import pandas as pd
import os
import datetime

from portal_data import check_auth_and_render_sidebar
st.set_page_config(page_title="숙제 체크 - Laellyn Portal", page_icon="✅", layout="wide")
check_auth_and_render_sidebar()

HW_FILE = "homework.csv"

def load_hw():
    if os.path.exists(HW_FILE):
        df = pd.read_csv(HW_FILE, encoding="utf-8-sig")
        df['done'] = df['done'].astype(bool)
        return df
    return pd.DataFrame(columns=['id', 'user', 'category', 'task', 'due_date', 'done'])

def save_hw(df):
    df.to_csv(HW_FILE, index=False, encoding="utf-8-sig")

df = load_hw()
role = st.session_state.get('role')

st.title("✅ 수학/영어 학원 숙제 체크리스트")

def render_user_homework(target_user, display_name, emoji):
    st.subheader(f"{emoji} {display_name}이의 숙제 보드")
    u_df = df[df['user'] == target_user].copy()
    
    if u_df.empty:
        st.info("등록된 숙제가 없습니다!")
        return

    done_cnt = int(u_df['done'].sum())
    tot_cnt = len(u_df)
    ratio = done_cnt / tot_cnt if tot_cnt > 0 else 0.0
    
    st.progress(ratio, text=f"전체 달성률: {done_cnt} / {tot_cnt} 완료 ({int(ratio*100)}%)")
    if done_cnt == tot_cnt and tot_cnt > 0:
        st.success(f"🎉 와우! {display_name}이 오늘 숙제를 100% 모두 끝냈어요! 최고!")

    categories = ["수학학원", "영어학원", "학교/기타"]
    cols = st.columns(3)
    changed = False

    for i, cat in enumerate(categories):
        with cols[i]:
            st.markdown(f"#### 📚 {cat}")
            cat_df = u_df[u_df['category'] == cat]
            if cat_df.empty:
                st.caption("숙제 없음")
            else:
                for _, row in cat_df.iterrows():
                    chk = st.checkbox(
                        f"{row['task']} (~{row['due_date']})",
                        value=bool(row['done']),
                        key=f"hw_page_{row['id']}"
                    )
                    if chk != bool(row['done']):
                        df.loc[df['id'] == row['id'], 'done'] = chk
                        changed = True

    if changed:
        save_hw(df)
        st.rerun()

if role == 'lael':
    render_user_homework('lael', '라엘', '🎀')
elif role == 'ellyn':
    render_user_homework('ellyn', '엘린', '🌻')
elif role == 'admin':
    tab1, tab2 = st.tabs(["🎀 라엘 숙제 현황", "🌻 엘린 숙제 현황"])
    with tab1:
        render_user_homework('lael', '라엘', '🎀')
    with tab2:
        render_user_homework('ellyn', '엘린', '🌻')

st.markdown("---")
with st.expander("➕ 새로운 숙제 추가 / 완료된 숙제 정리하기", expanded=(role == 'admin')):
    with st.form("add_hw_form"):
        c1, c2, c3 = st.columns(3)
        with c1:
            if role == 'admin':
                target_u = st.selectbox("대상 선택", ["lael", "ellyn"], format_func=lambda x: "🎀 라엘" if x == "lael" else "🌻 엘린")
            else:
                target_u = role
                st.write(f"대상: **{st.session_state.get('user_name')}**")
        with c2:
            cat_sel = st.selectbox("과목/분류", ["수학학원", "영어학원", "학교/기타"])
        with c3:
            due_sel = st.date_input("마감일", value=datetime.date.today())
        
        task_input = st.text_input("숙제 내용 입력 (예: 쎈 수학 B단계 p.30~35 풀기)")
        if st.form_submit_button("숙제 등록하기 📌", use_container_width=True):
            if task_input.strip():
                new_id = int(df['id'].max() + 1) if not df.empty else 1
                new_row = pd.DataFrame([{
                    'id': new_id,
                    'user': target_u,
                    'category': cat_sel,
                    'task': task_input.strip(),
                    'due_date': str(due_sel),
                    'done': False
                }])
                df = pd.concat([df, new_row], ignore_index=True)
                save_hw(df)
                st.success("새로운 숙제가 등록되었습니다!")
                st.rerun()

    if st.button("🗑️ 완료(체크)된 숙제 일괄 삭제하기"):
        if role == 'admin':
            df = df[~df['done']]
        else:
            df = df[~((df['user'] == role) & (df['done']))]
        save_hw(df)
        st.success("완료된 숙제를 깔끔하게 정리했습니다!")
        st.rerun()
