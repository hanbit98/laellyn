import streamlit as st
import pandas as pd
import random
import os
import datetime

# 로그인 및 권한 체크
from portal_data import check_auth_and_render_sidebar
st.set_page_config(page_title="라엘 단어장 - Laellyn Portal", page_icon="🎀", layout="wide")
check_auth_and_render_sidebar()

if st.session_state.get('role') not in ['lael', 'admin']:
    st.warning("🎀 이 페이지는 라엘이와 아빠만 들어올 수 있는 단어장이에요!")
    st.stop()

# --- UI 커스텀 CSS (기존 laelapp.py 스타일 100% 보존) ---
st.markdown("""
    <style>
    div[data-baseweb="input"] input {
        font-size: 28px !important;
        font-weight: bold !important;
        padding: 15px !important;
    }
    div[data-testid="stNotification"] div[data-testid="stMarkdownContainer"] p {
        font-size: 24px !important;
        font-weight: bold !important;
        line-height: 1.4 !important;
    }
    .exam-sentence {
        font-size: 22px;
        font-weight: bold;
        margin-bottom: 10px;
        white-space: pre-wrap;
    }
    .english-def {
        font-size: 22px;
        font-weight: bold;
        color: #d9534f;
        margin-bottom: 10px;
        padding: 15px;
        background-color: #f9f2f4;
        border-radius: 10px;
    }
    .korean-translation {
        font-size: 18px;
        color: #0066cc;
        margin-bottom: 20px;
    }
    </style>
""", unsafe_allow_html=True)

# 세션 상태 초기화 (lael_ 접두사로 엘린 단어장과 충돌 방지)
if 'lael_quiz_state' not in st.session_state:
    st.session_state['lael_quiz_state'] = 'SETUP'
if 'lael_current_index' not in st.session_state:
    st.session_state['lael_current_index'] = 0
if 'lael_score' not in st.session_state:
    st.session_state['lael_score'] = 0
if 'lael_wrong_answers' not in st.session_state:
    st.session_state['lael_wrong_answers'] = []
if 'lael_quiz_data' not in st.session_state:
    st.session_state['lael_quiz_data'] = []
if 'lael_last_feedback' not in st.session_state:
    st.session_state['lael_last_feedback'] = None
if 'lael_selected_day' not in st.session_state:
    st.session_state['lael_selected_day'] = ""
if 'lael_history_saved' not in st.session_state:
    st.session_state['lael_history_saved'] = False

VOCAB_FILE = "lael_vocab.csv" if os.path.exists("lael_vocab.csv") else "vocab.csv"

@st.cache_data
def load_lael_data(file_path):
    try:
        df = pd.read_csv(file_path, encoding='utf-8-sig')
        if 'Day' not in df.columns:
            df = pd.read_csv(file_path, header=None, names=['Day', '순서', '유형', '정답 단어', '예문', '한글 해석', '영영 뜻'], encoding='utf-8-sig')
        else:
            df.columns = ['Day', '순서', '유형', '정답 단어', '예문', '한글 해석', '영영 뜻']
        df = df.fillna('')
        df['정답 단어'] = df['정답 단어'].astype(str).str.strip()
        return df
    except FileNotFoundError:
        return pd.DataFrame()
    except Exception as e:
        st.error(f"데이터 로드 중 오류 발생: {e}")
        return pd.DataFrame()

df = load_lael_data(VOCAB_FILE)

def check_lael_answer():
    current_idx = st.session_state['lael_current_index']
    data = st.session_state['lael_quiz_data']
    if current_idx >= len(data):
        return

    current_word = data[current_idx]
    user_input = st.session_state.lael_user_input
    correct_answer = str(current_word['정답 단어'])

    if user_input.strip().lower() == correct_answer.strip().lower():
        st.session_state['lael_score'] += 1
        st.session_state['lael_last_feedback'] = (f"⭕ 정답! '{correct_answer}'", True)
    else:
        question_text = current_word.get('예문', '') if current_word.get('유형', '') == '예문빈칸' else current_word.get('영영 뜻', '')
        st.session_state['lael_wrong_answers'].append({
            '정답 단어': correct_answer,
            '나의 답': user_input,
            '문제(예문/영영)': question_text,
            '한글 해석': current_word.get('한글 해석', '')
        })
        st.session_state['lael_last_feedback'] = (f"❌ 땡! 정답은 '{correct_answer}' (입력: {user_input})", False)

    st.session_state['lael_current_index'] += 1
    st.session_state.lael_user_input = ""

# 타이틀
st.markdown("<h2 style='font-size: 30px;'>❤️보석같은 라엘❤️ 단어시험 뽀개기😁</h2>", unsafe_allow_html=True)

# (A) 설정 화면
if st.session_state['lael_quiz_state'] == 'SETUP':
    if not df.empty:
        st.info("엔터키를 치면 바로 채점하고 다음 문제로 넘어갑니다!")
        if 'Day' in df.columns:
            days = df['Day'].unique()
            selected_day = st.selectbox("Day 선택", days)
        else:
            st.error("CSV 파일 구조에 문제가 있습니다. 파일 형식을 확인해주세요.")
            st.stop()
        
        if st.button("시험 시작하기!", type="primary"):
            day_data = df[df['Day'] == selected_day]
            st.session_state['lael_quiz_data'] = day_data.sample(frac=1).reset_index(drop=True).to_dict('records')
            st.session_state['lael_selected_day'] = selected_day
            st.session_state['lael_quiz_state'] = 'TESTING'
            st.session_state['lael_current_index'] = 0
            st.session_state['lael_score'] = 0
            st.session_state['lael_wrong_answers'] = []
            st.session_state['lael_last_feedback'] = None
            st.session_state['lael_history_saved'] = False
            st.rerun()
    else:
        st.error("'lael_vocab.csv' 파일을 넣어주세요. (컬럼: Day, 순서, 유형, 정답 단어, 예문, 한글 해석, 영영 뜻)")

# (B) 시험 화면
elif st.session_state['lael_quiz_state'] == 'TESTING':
    total_q = len(st.session_state['lael_quiz_data'])
    current_idx = st.session_state['lael_current_index']

    if current_idx >= total_q:
        st.session_state['lael_quiz_state'] = 'FINISHED'
        st.rerun()

    current_word = st.session_state['lael_quiz_data'][current_idx]
    st.progress(current_idx / total_q)
    
    if st.session_state['lael_last_feedback']:
        msg, is_correct = st.session_state['lael_last_feedback']
        if is_correct:
            st.success(msg)
        else:
            st.error(msg)
    else:
        st.write("시작해볼까요? 화이팅!")

    st.markdown("---")
    st.markdown(f"#### 문제 {current_idx + 1}/{total_q}")
    
    quiz_type = current_word.get('유형', '예문빈칸')
    if quiz_type == '영영사전':
        st.markdown(f"<div class='english-def'>📖 English Definition:<br>{current_word.get('영영 뜻', '')}</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='korean-translation'>💡 뜻: {current_word.get('한글 해석', '')}</div>", unsafe_allow_html=True)
    else:
        exam_text = str(current_word.get('예문', '')).replace('( )', '( &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; )').replace('()', '( &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; )')
        st.markdown(f"<div class='exam-sentence'>{exam_text}</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='korean-translation'>💡 힌트: {current_word.get('한글 해석', '')}</div>", unsafe_allow_html=True)

    st.text_input(
        label="정답 영어 단어를 입력하고 Enter를 치세요",
        key="lael_user_input",
        on_change=check_lael_answer
    )

# (C) 결과 화면
elif st.session_state['lael_quiz_state'] == 'FINISHED':
    score = st.session_state['lael_score']
    total = len(st.session_state['lael_quiz_data'])
    
    # 응시 기록 자동 저장
    if not st.session_state.get('lael_history_saved'):
        hist_file = "quiz_history.csv"
        new_row = pd.DataFrame([{
            "일시": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
            "이름": "라엘",
            "범위": st.session_state.get('lael_selected_day', '재시험'),
            "점수": f"{score} / {total}",
            "오답수": len(st.session_state['lael_wrong_answers'])
        }])
        if os.path.exists(hist_file):
            old_df = pd.read_csv(hist_file, encoding="utf-8-sig")
            pd.concat([old_df, new_row], ignore_index=True).to_csv(hist_file, index=False, encoding="utf-8-sig")
        else:
            new_row.to_csv(hist_file, index=False, encoding="utf-8-sig")
        st.session_state['lael_history_saved'] = True

    st.balloons()
    st.header(f"끝! 점수: {score} / {total}")

    if st.session_state['lael_last_feedback']:
        msg, is_correct = st.session_state['lael_last_feedback']
        if is_correct:
            st.success(f"마지막 문제: {msg}")
        else:
            st.error(f"마지막 문제: {msg}")

    if st.session_state['lael_wrong_answers']:
        st.markdown("### 🚨 틀린 단어 확인하기")
        wrong_df = pd.DataFrame(st.session_state['lael_wrong_answers'])
        wrong_df.index = wrong_df.index + 1
        st.table(wrong_df)
        
        st.warning("👇 틀린 문제만 모아서 다시 시험 볼 수 있어요!")
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🔥 틀린 문제만 다시 풀기"):
                retry_data = st.session_state['lael_wrong_answers'].copy()
                formatted_retry_data = []
                for item in retry_data:
                    is_english_def = "a " in str(item['문제(예문/영영)']) or "to " in str(item['문제(예문/영영)']) and " " not in str(item['정답 단어'])
                    formatted_retry_data.append({
                        '정답 단어': item['정답 단어'],
                        '유형': '영영사전' if is_english_def else '예문빈칸',
                        '예문': item['문제(예문/영영)'] if not is_english_def else '',
                        '영영 뜻': item['문제(예문/영영)'] if is_english_def else '',
                        '한글 해석': item['한글 해석']
                    })
                random.shuffle(formatted_retry_data)
                st.session_state['lael_quiz_data'] = formatted_retry_data
                st.session_state['lael_selected_day'] = f"{st.session_state.get('lael_selected_day', '')} (오답재시험)"
                st.session_state['lael_quiz_state'] = 'TESTING'
                st.session_state['lael_current_index'] = 0
                st.session_state['lael_score'] = 0
                st.session_state['lael_wrong_answers'] = []
                st.session_state['lael_last_feedback'] = None
                st.session_state['lael_history_saved'] = False
                st.rerun()
        
        with col2:
            if st.button("🏠 처음으로 돌아가기"):
                st.session_state['lael_quiz_state'] = 'SETUP'
                st.session_state['lael_last_feedback'] = None
                st.rerun()
    else:
        st.success("완벽합니다! 틀린 문제가 하나도 없네요! 🎉")
        if st.button("🏠 처음으로 돌아가기"):
            st.session_state['lael_quiz_state'] = 'SETUP'
            st.session_state['lael_last_feedback'] = None
            st.rerun()

# 아빠(관리자) 전용 단어장 CSV 업로드 기능
if st.session_state.get('role') == 'admin':
    st.markdown("---")
    with st.expander("👑 관리자 전용: 라엘 단어장(lael_vocab.csv) 업데이트"):
        uploaded_csv = st.file_uploader("새로운 lael_vocab.csv 파일 업로드", type=["csv"])
        if uploaded_csv is not None:
            if st.button("단어장 덮어쓰기 저장"):
                with open("lael_vocab.csv", "wb") as f:
                    f.write(uploaded_csv.getbuffer())
                st.cache_data.clear()
                st.success("lael_vocab.csv 파일이 업데이트되었습니다!")
                st.rerun()
