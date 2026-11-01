import streamlit as st
import pandas as pd
import random
import re
import os
import datetime

# 로그인 및 권한 체크
if not st.session_state.get('logged_in'):
    st.warning("🔒 먼저 메인 화면에서 로그인해 주세요!")
    st.stop()

if st.session_state.get('role') not in ['ellyn', 'admin']:
    st.warning("🌻 이 페이지는 엘린이와 아빠만 들어올 수 있는 단어장이에요!")
    st.stop()

# 스타일 적용: 입력창 폰트 크기 키우기 (기존 ellynvoca.py 100% 보존)
st.markdown("""
    <style>
    .stTextInput input {
        font-size: 28px !important;
        padding: 15px !important;
        line-height: 1.5 !important;
    }
    </style>
    """, unsafe_allow_html=True)

# ------------------ 세션 상태 초기화 (ellyn_ 접두사 적용) ------------------
if 'ellyn_quiz_state' not in st.session_state:
    st.session_state.ellyn_quiz_state = 'setup'
if 'ellyn_current_q_idx' not in st.session_state:
    st.session_state.ellyn_current_q_idx = 0
if 'ellyn_score' not in st.session_state:
    st.session_state.ellyn_score = 0
if 'ellyn_quiz_data' not in st.session_state:
    st.session_state.ellyn_quiz_data = []
if 'ellyn_incorrect_questions' not in st.session_state:
    st.session_state.ellyn_incorrect_questions = []
if 'ellyn_feedback_msg' not in st.session_state:
    st.session_state.ellyn_feedback_msg = None
if 'ellyn_input_value' not in st.session_state:
    st.session_state.ellyn_input_value = ""
if 'ellyn_selected_lesson' not in st.session_state:
    st.session_state.ellyn_selected_lesson = ""
if 'ellyn_history_saved' not in st.session_state:
    st.session_state.ellyn_history_saved = False

VOCAB_FILE = "ellyn_vocab.csv" if os.path.exists("ellyn_vocab.csv") else "vocab.csv"

@st.cache_data
def load_ellyn_data(file_path):
    try:
        df = pd.read_csv(file_path, encoding='utf-8-sig')
        df.columns = df.columns.str.strip()
        return df
    except Exception as e:
        st.error(f"CSV 파일을 읽을 수 없습니다: {e}")
        return pd.DataFrame()

def submit_ellyn_answer():
    idx = st.session_state.ellyn_current_q_idx
    q_data = st.session_state.ellyn_quiz_data[idx]
    user_input = st.session_state.ellyn_input_value.strip()
    
    if user_input.lower() == q_data['answer'].lower():
        st.session_state.ellyn_score += 1
        st.session_state.ellyn_feedback_msg = ("correct", f"⭕ 정답입니다! ({q_data['answer']})")
    else:
        st.session_state.ellyn_feedback_msg = ("wrong", f"❌ 틀렸습니다! 정답은 **{q_data['answer']}** 였습니다.")
        st.session_state.ellyn_incorrect_questions.append(q_data)
    
    st.session_state.ellyn_current_q_idx += 1
    st.session_state.ellyn_input_value = ""

# ------------------ 메인 UI ------------------
st.title("😁엘린이의 단어 시험❤️")

df = load_ellyn_data(VOCAB_FILE)
if df.empty:
    st.stop()

# [State 1] 설정 화면
if st.session_state.ellyn_quiz_state == 'setup':
    st.subheader("시험 범위를 선택하세요")
    
    if len(df.columns) > 0:
        lesson_col = df.columns[0]
        lesson_list = sorted(df[lesson_col].astype(str).unique())
        selected_lesson = st.selectbox("Lesson 선택", lesson_list)
    else:
        st.error("CSV 파일에 데이터가 없습니다.")
        st.stop()
    
    if st.button("시험 시작하기 (Start)", type="primary", use_container_width=True):
        lesson_df = df[df[lesson_col].astype(str) == selected_lesson]
        
        if lesson_df.empty:
            st.error("선택한 레슨에 단어가 없습니다.")
        else:
            quiz_list = []

            for _, row in lesson_df.iterrows():
                word = str(row.iloc[2]).replace('nan', '').strip() if len(row) > 2 else ''
                part = str(row.iloc[3]).replace('nan', '').strip() if len(row) > 3 else ''
                meaning = str(row.iloc[4]).replace('nan', '').strip() if len(row) > 4 else ''
                example = str(row.iloc[5]).replace('nan', '').strip() if len(row) > 5 else ''

                if not word:
                    continue

                # Type A (뜻 문제)
                if meaning:
                    fmt_mean = meaning.replace('\r\n', '<br>').replace('\n', '<br>')
                    fmt_mean = re.sub(r'\b(n|v|adj|adv|prep|conj|pron|phrase)\.\s+(\d+\.)', r'\1.#SPACE#\2', fmt_mean)
                    fmt_mean = re.sub(r'\s+(?=(?:n|v|adj|adv|prep|conj|pron|phrase)\.|\d+\.)', '<br>', fmt_mean)
                    fmt_mean = fmt_mean.replace('#SPACE#', ' ')
                    if fmt_mean.startswith('<br>'):
                        fmt_mean = fmt_mean[4:]
                    
                    quiz_list.append({
                        'type': 'A',
                        'question': fmt_mean,
                        'answer': word,
                        'hint': part,
                        'display_hint': "뜻을 보고 단어를 쓰세요"
                    })
                
                # Type B (예문 문제)
                if example:
                    target = word
                    pattern = re.compile(re.escape(target), re.IGNORECASE)
                    hidden_ex = pattern.sub("______", example)
                    fmt_ex = hidden_ex.replace('\r\n', '<br>').replace('\n', '<br>')
                    fmt_ex = re.sub(r'\b(n|v|adj|adv|prep|conj|pron|phrase)\.\s+(\d+\.)', r'\1.#SPACE#\2', fmt_ex)
                    fmt_ex = re.sub(r'\s+(?=(?:n|v|adj|adv|prep|conj|pron|phrase)\.|\d+\.)', '<br><br>', fmt_ex)
                    fmt_ex = fmt_ex.replace('#SPACE#', ' ')
                    if fmt_ex.startswith('<br><br>'):
                        fmt_ex = fmt_ex[8:]
                    
                    quiz_list.append({
                        'type': 'B',
                        'question': fmt_ex,
                        'answer': target,
                        'hint': part,
                        'display_hint': "빈칸에 알맞은 단어를 쓰세요"
                    })
            
            if not quiz_list:
                st.error("문제를 생성할 수 없습니다. 데이터가 있는지 확인해주세요.")
            else:
                random.shuffle(quiz_list)
                st.session_state.ellyn_quiz_data = quiz_list
                st.session_state.ellyn_total_q = len(quiz_list)
                st.session_state.ellyn_current_q_idx = 0
                st.session_state.ellyn_score = 0
                st.session_state.ellyn_incorrect_questions = []
                st.session_state.ellyn_feedback_msg = None
                st.session_state.ellyn_selected_lesson = selected_lesson
                st.session_state.ellyn_history_saved = False
                st.session_state.ellyn_quiz_state = 'quiz'
                st.rerun()

# [State 2] 퀴즈 진행
elif st.session_state.ellyn_quiz_state == 'quiz':
    current_idx = st.session_state.ellyn_current_q_idx
    total_q = st.session_state.ellyn_total_q
    
    if current_idx >= total_q:
        st.session_state.ellyn_quiz_state = 'result'
        st.rerun()

    if st.session_state.ellyn_feedback_msg:
        msg_type, msg_text = st.session_state.ellyn_feedback_msg
        if msg_type == "correct":
            st.success(msg_text)
        else:
            st.error(msg_text)
    else:
        st.info("준비되면 아래 빈칸에 정답을 쓰고 Enter를 치세요!")

    q_data = st.session_state.ellyn_quiz_data[current_idx]
    st.markdown(f"### Q{current_idx + 1}. {q_data['display_hint']}")
    
    display_question = q_data['question']
    hint_html = ""
    if q_data['hint']:
        hint_html = f'<br><br><span style="color:blue; font-size:16px;">(힌트: {q_data["hint"]})</span>'

    st.markdown(f"""
        <div style="background-color:#f0f2f6; padding:20px; border-radius:10px; font-size:20px; margin-bottom:20px; line-height: 1.6;">
            <b>{display_question}</b>
            {hint_html}
        </div>
    """, unsafe_allow_html=True)
    
    st.text_input(
        label="정답 입력",
        key="ellyn_input_value",
        on_change=submit_ellyn_answer,
        label_visibility="collapsed",
        placeholder="여기에 정답을 입력하세요"
    )
    
    st.progress((current_idx) / total_q)

# [State 3] 결과
elif st.session_state.ellyn_quiz_state == 'result':
    score = st.session_state.ellyn_score
    total = st.session_state.ellyn_total_q
    incorrect_count = len(st.session_state.ellyn_incorrect_questions)

    if not st.session_state.get('ellyn_history_saved'):
        hist_file = "quiz_history.csv"
        new_row = pd.DataFrame([{
            "일시": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
            "이름": "엘린",
            "범위": st.session_state.get('ellyn_selected_lesson', '재시험'),
            "점수": f"{score} / {total}",
            "오답수": incorrect_count
        }])
        if os.path.exists(hist_file):
            old_df = pd.read_csv(hist_file, encoding="utf-8-sig")
            pd.concat([old_df, new_row], ignore_index=True).to_csv(hist_file, index=False, encoding="utf-8-sig")
        else:
            new_row.to_csv(hist_file, index=False, encoding="utf-8-sig")
        st.session_state.ellyn_history_saved = True

    if st.session_state.ellyn_feedback_msg:
        msg_type, msg_text = st.session_state.ellyn_feedback_msg
        st.markdown("### 마지막 문제 결과:")
        if msg_type == "correct":
            st.success(msg_text)
        else:
            st.error(msg_text)
        st.markdown("---")

    st.balloons()
    st.title("🎉 시험 종료!")
    st.metric(label="최종 점수", value=f"{score}점", delta=f"{total}문제 중 {score}개 정답")
    
    if score == total:
        st.success("완벽해요! 엘린이 최고! 💯")
    elif score >= total * 0.8:
        st.info("아주 잘했어요! 틀린 것만 다시 해볼까요? 🌟")
    else:
        st.warning("수고했어요! 틀린 문제를 복습해봐요! 💪")

    st.markdown("---")
    col1, col2 = st.columns(2)
    
    with col1:
        if incorrect_count > 0:
            if st.button(f"틀린 문제만 다시 풀기 ({incorrect_count}개)", type="primary", use_container_width=True):
                st.session_state.ellyn_quiz_data = st.session_state.ellyn_incorrect_questions.copy()
                random.shuffle(st.session_state.ellyn_quiz_data)
                st.session_state.ellyn_incorrect_questions = []
                st.session_state.ellyn_total_q = len(st.session_state.ellyn_quiz_data)
                st.session_state.ellyn_current_q_idx = 0
                st.session_state.ellyn_score = 0
                st.session_state.ellyn_feedback_msg = None
                st.session_state.ellyn_selected_lesson = f"{st.session_state.get('ellyn_selected_lesson', '')} (오답재시험)"
                st.session_state.ellyn_history_saved = False
                st.session_state.ellyn_quiz_state = 'quiz'
                st.rerun()
        else:
            st.write("틀린 문제가 없습니다! 👍")

    with col2:
        if st.button("처음으로 (레슨 선택)", use_container_width=True):
            st.session_state.ellyn_quiz_state = 'setup'
            st.session_state.ellyn_score = 0
            st.session_state.ellyn_current_q_idx = 0
            st.session_state.ellyn_incorrect_questions = []
            st.session_state.ellyn_feedback_msg = None
            st.rerun()

# 아빠(관리자) 전용 엘린 단어장 CSV 업로드 기능
if st.session_state.get('role') == 'admin':
    st.markdown("---")
    with st.expander("👑 관리자 전용: 엘린 단어장(ellyn_vocab.csv) 업데이트"):
        uploaded_csv = st.file_uploader("기존 엘린이 vocab.csv 파일을 업로드하면 ellyn_vocab.csv로 즉시 적용됩니다", type=["csv"])
        if uploaded_csv is not None:
            if st.button("엘린 단어장 덮어쓰기 저장"):
                with open("ellyn_vocab.csv", "wb") as f:
                    f.write(uploaded_csv.getbuffer())
                st.cache_data.clear()
                st.success("ellyn_vocab.csv 파일이 성공적으로 업데이트되었습니다!")
                st.rerun()
