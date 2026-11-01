import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import json
import os
import datetime

st.set_page_config(page_title="Laellyn Learning Portal", page_icon="🏰", layout="wide")

# ---------------------------------------------------------
# 데이터 및 설정 로드/저장 헬퍼 함수
# ---------------------------------------------------------
CONFIG_FILE = "portal_config.json"
HW_FILE = "homework.csv"
SCHED_FILE = "schedule.csv"
HISTORY_FILE = "quiz_history.csv"

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {
        "lael": {
            "weekly_goal": "단어 시험 Day 15까지 완벽 마스터하기! 주말에 아빠랑 스플렌더 한 판 🎲",
            "calendar_url": "https://calendar.google.com/calendar/embed?src=ko.south_korea%23holiday%40group.v.calendar.google.com&ctz=Asia%2FSeoul&mode=WEEK",
            "stickers": 12,
            "reward_goal": 20,
            "reward_item": "아이브(IVE) 포토카드 세트 또는 소원권 1장 🎁"
        },
        "ellyn": {
            "weekly_goal": "이번 주 영어 단어 시험 100점 맞기! 수학 연산 밀리지 않기 🌟",
            "calendar_url": "https://calendar.google.com/calendar/embed?src=ko.south_korea%23holiday%40group.v.calendar.google.com&ctz=Asia%2FSeoul&mode=WEEK",
            "stickers": 15,
            "reward_goal": 20,
            "reward_item": "주말 맛있는 디저트 & 보드게임 소원권 1장 🍰"
        },
        "admin": {
            "calendar_url": "https://calendar.google.com/calendar/embed?src=ko.south_korea%23holiday%40group.v.calendar.google.com&ctz=Asia%2FSeoul&mode=WEEK"
        },
        "vitamins": []
    }

def save_config(cfg):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)

def load_homework():
    if os.path.exists(HW_FILE):
        df = pd.read_csv(HW_FILE, encoding="utf-8-sig")
        df['done'] = df['done'].astype(bool)
        return df
    return pd.DataFrame(columns=['id', 'user', 'category', 'task', 'due_date', 'done'])

def save_homework(df):
    df.to_csv(HW_FILE, index=False, encoding="utf-8-sig")

def load_schedule():
    if os.path.exists(SCHED_FILE):
        return pd.read_csv(SCHED_FILE, encoding="utf-8-sig")
    return pd.DataFrame(columns=['user', 'day', 'events'])

# ---------------------------------------------------------
# 1. 사용자 계정 및 세션 초기화
# ---------------------------------------------------------
USERS = {
    "lael": ["1234", "lael", "라엘"],
    "ellyn": ["1234", "ellyn", "엘린"],
    "admin": ["0000", "admin", "아빠(관리자)"]
}

if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if 'role' not in st.session_state:
    st.session_state['role'] = None
if 'user_name' not in st.session_state:
    st.session_state['user_name'] = ""

# 역할별 사이드바 메뉴 숨김 처리 (라엘 로그인 시 엘린단어장 숨김, 엘린 로그인 시 라엘단어장 숨김)
if not st.session_state['logged_in']:
    st.markdown("""<style>[data-testid="stSidebar"] { display: none; }</style>""", unsafe_allow_html=True)
elif st.session_state['role'] == 'lael':
    st.markdown("""
        <style>
        [data-testid="stSidebarNav"] li:nth-child(3) { display: none; }
        </style>
    """, unsafe_allow_html=True)
elif st.session_state['role'] == 'ellyn':
    st.markdown("""
        <style>
        [data-testid="stSidebarNav"] li:nth-child(2) { display: none; }
        </style>
    """, unsafe_allow_html=True)

# ---------------------------------------------------------
# 2. 로그인 화면
# ---------------------------------------------------------
if not st.session_state['logged_in']:
    st.markdown("<h1 style='text-align: center; margin-top: 30px;'>🏰 Laellyn Learning Portal</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; font-size: 18px; color: #666;'>라엘 & 엘린 맞춤형 스마트 학습 포털</p>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        with st.form("login_form"):
            input_id = st.text_input("아이디 (lael / ellyn / admin)")
            input_pw = st.text_input("비밀번호", type="password")
            submitted = st.form_submit_button("로그인 🚀", use_container_width=True)
            
            if submitted:
                uid = input_id.strip().lower()
                if uid in USERS and USERS[uid][0] == input_pw.strip():
                    st.session_state['logged_in'] = True
                    st.session_state['role'] = USERS[uid][1]
                    st.session_state['user_name'] = USERS[uid][2]
                    st.rerun()
                else:
                    st.error("아이디나 비밀번호가 틀렸습니다. 다시 확인해 주세요!")

# ---------------------------------------------------------
# 3. 로그인 성공 후 메인 대시보드
# ---------------------------------------------------------
else:
    cfg = load_config()
    hw_df = load_homework()
    sched_df = load_schedule()
    role = st.session_state['role']

    # 상단 공통 헤더
    h_col1, h_col2 = st.columns([8.5, 1.5])
    with h_col1:
        if role == 'lael':
            st.markdown("<h1>🎀 안녕, 보석같은 라엘! 오늘의 학습 대시보드</h1>", unsafe_allow_html=True)
        elif role == 'ellyn':
            st.markdown("<h1>🌻 안녕, 비타민 엘린! 오늘의 학습 대시보드</h1>", unsafe_allow_html=True)
        else:
            st.markdown("<h1>👑 Laellyn 통합 관리자(아빠) 컨트롤 타워</h1>", unsafe_allow_html=True)
    with h_col2:
        st.write("")
        if st.button("로그아웃 🔓", use_container_width=True):
            st.session_state['logged_in'] = False
            st.session_state['role'] = None
            st.rerun()

    st.markdown("---")

    # =========================================================
    # [A] 라엘 또는 엘린 개인화 대시보드
    # =========================================================
    if role in ['lael', 'ellyn']:
        user_cfg = cfg.get(role, {})
        user_hw = hw_df[hw_df['user'] == role].copy()

        # 1) 상단 요약: 오늘의 할 일 & 이번 주 목표 + 칭찬 스티커
        col1, col2 = st.columns([1.2, 1])
        
        with col1:
            st.subheader("📌 오늘 해야 할 학원 숙제 & 할 일")
            if user_hw.empty:
                st.success("🎉 등록된 숙제가 없습니다! 자유시간을 즐기세요!")
            else:
                done_count = int(user_hw['done'].sum())
                total_count = len(user_hw)
                progress_ratio = done_count / total_count if total_count > 0 else 0.0
                st.progress(progress_ratio, text=f"숙제 달성률: {done_count} / {total_count} 완료 ({int(progress_ratio*100)}%)")
                
                changed = False
                for idx, row in user_hw.iterrows():
                    label = f"**[{row['category']}]** {row['task']} (마감: {row['due_date']})"
                    is_checked = st.checkbox(label, value=bool(row['done']), key=f"dash_hw_{row['id']}")
                    if is_checked != bool(row['done']):
                        hw_df.loc[hw_df['id'] == row['id'], 'done'] = is_checked
                        changed = True
                if changed:
                    save_homework(hw_df)
                    st.rerun()

        with col2:
            st.subheader("🎯 이번 주 목표 & 칭찬 스티커")
            st.info(f"**이번 주 목표:**\n\n{user_cfg.get('weekly_goal', '')}")
            
            stickers = user_cfg.get('stickers', 0)
            goal_stickers = user_cfg.get('reward_goal', 20)
            reward_item = user_cfg.get('reward_item', '소원권 1장')
            st.write(f"⭐ **모은 칭찬 스티커:** `{stickers} / {goal_stickers}개`")
            st.progress(min(stickers / max(goal_stickers, 1), 1.0))
            st.caption(f"🎁 목표 달성 보상: {reward_item}")

        st.markdown("---")

        # 2) 이번 주 요일별 시간표 보드
        st.subheader("🗓️ 이번 주 요일별 시간표")
        days_order = ["월 (Mon)", "화 (Tue)", "수 (Wed)", "목 (Thu)", "금 (Fri)", "토 (Sat)", "일 (Sun)"]
        today_idx = datetime.datetime.today().weekday()
        cols = st.columns(7)
        user_sched = sched_df[sched_df['user'] == role]

        for i, d_name in enumerate(days_order):
            with cols[i]:
                if i == today_idx:
                    st.markdown(f"<div style='background-color:#ffe6e6; padding:8px; border-radius:8px; text-align:center; font-weight:bold; color:#d9534f;'>🔥 {d_name}<br>(오늘)</div>", unsafe_allow_html=True)
                else:
                    st.markdown(f"<div style='background-color:#f0f2f6; padding:8px; border-radius:8px; text-align:center; font-weight:bold;'>{d_name}</div>", unsafe_allow_html=True)
                
                day_row = user_sched[user_sched['day'] == d_name]
                if not day_row.empty:
                    events = str(day_row.iloc[0]['events']).split("|")
                    for ev in events:
                        if ev.strip():
                            st.markdown(f"<div style='font-size:14px; margin-top:6px; padding:4px; border-left:3px solid #4a90e2;'>{ev.strip()}</div>", unsafe_allow_html=True)

        st.markdown("---")

        # 3) 구글 캘린더 임베드
        st.subheader(f"📅 {st.session_state['user_name']}이의 구글 캘린더")
        cal_url = user_cfg.get("calendar_url", "")
        if cal_url:
            components.html(
                f'<iframe src="{cal_url}" style="border: 1px solid #ddd; border-radius: 10px;" width="100%" height="550" frameborder="0" scrolling="no"></iframe>',
                height=560
            )
        else:
            st.warning("아직 구글 캘린더 주소가 등록되지 않았습니다. 아빠(admin) 계정에서 설정할 수 있어요!")

    # =========================================================
    # [B] 아빠(Admin) 컨트롤 타워 대시보드
    # =========================================================
    elif role == 'admin':
        st.subheader("📊 라엘 & 엘린 실시간 학습 현황")
        col_lael, col_ellyn = st.columns(2)

        for child_key, child_name, emoji, col_obj in [('lael', '라엘', '🎀', col_lael), ('ellyn', '엘린', '🌻', col_ellyn)]:
            with col_obj:
                st.markdown(f"### {emoji} {child_name}이 현황")
                c_hw = hw_df[hw_df['user'] == child_key]
                done_c = int(c_hw['done'].sum()) if not c_hw.empty else 0
                tot_c = len(c_hw)
                ratio_c = done_c / tot_c if tot_c > 0 else 0.0
                st.write(f"**숙제 완료율:** {done_c} / {tot_c} 건 ({int(ratio_c*100)}%)")
                st.progress(ratio_c)
                
                # 칭찬 스티커 빠른 관리
                cur_st = cfg[child_key].get('stickers', 0)
                goal_st = cfg[child_key].get('reward_goal', 20)
                st.write(f"**칭찬 스티커:** ⭐ {cur_st} / {goal_st} 개")
                b1, b2, _ = st.columns([1, 1, 2])
                with b1:
                    if st.button(f"➕ 스티커 +1", key=f"add_st_{child_key}"):
                        cfg[child_key]['stickers'] = cur_st + 1
                        save_config(cfg)
                        st.rerun()
                with b2:
                    if st.button(f"➖ 스티커 -1", key=f"sub_st_{child_key}"):
                        cfg[child_key]['stickers'] = max(0, cur_st - 1)
                        save_config(cfg)
                        st.rerun()

        # 최근 단어 시험 기록 표시
        st.markdown("---")
        st.subheader("📝 최근 단어 시험 응시 기록")
        if os.path.exists(HISTORY_FILE):
            hist_df = pd.read_csv(HISTORY_FILE, encoding="utf-8-sig")
            st.dataframe(hist_df.tail(10).iloc[::-1], use_container_width=True)
        else:
            st.info("아직 응시한 단어 시험 기록이 없습니다. 아이들이 단어 시험을 완료하면 이곳에 자동 기록됩니다.")

        # 목표 및 구글 캘린더 URL 설정창
        st.markdown("---")
        with st.expander("⚙️ 주간 목표 & 구글 캘린더 URL 설정 (클릭하여 열기)", expanded=False):
            with st.form("admin_config_form"):
                st.markdown("#### 🎀 라엘 설정")
                lael_goal = st.text_input("라엘 이번 주 목표", value=cfg['lael'].get('weekly_goal', ''))
                lael_cal = st.text_input("라엘 구글 캘린더 Embed URL (src 주소)", value=cfg['lael'].get('calendar_url', ''))
                lael_reward = st.text_input("라엘 스티커 달성 보상", value=cfg['lael'].get('reward_item', ''))
                
                st.markdown("#### 🌻 엘린 설정")
                ellyn_goal = st.text_input("엘린 이번 주 목표", value=cfg['ellyn'].get('weekly_goal', ''))
                ellyn_cal = st.text_input("엘린 구글 캘린더 Embed URL (src 주소)", value=cfg['ellyn'].get('calendar_url', ''))
                ellyn_reward = st.text_input("엘린 스티커 달성 보상", value=cfg['ellyn'].get('reward_item', ''))

                st.markdown("#### 👑 가족 마스터 캘린더 설정")
                admin_cal = st.text_input("아빠/가족 통합 구글 캘린더 Embed URL", value=cfg['admin'].get('calendar_url', ''))

                if st.form_submit_button("💾 설정 저장하기", use_container_width=True):
                    cfg['lael']['weekly_goal'] = lael_goal
                    cfg['lael']['calendar_url'] = lael_cal
                    cfg['lael']['reward_item'] = lael_reward
                    cfg['ellyn']['weekly_goal'] = ellyn_goal
                    cfg['ellyn']['calendar_url'] = ellyn_cal
                    cfg['ellyn']['reward_item'] = ellyn_reward
                    cfg['admin']['calendar_url'] = admin_cal
                    save_config(cfg)
                    st.success("설정이 성공적으로 저장되었습니다!")
                    st.rerun()

        # 캘린더 탭 뷰
        st.markdown("---")
        st.subheader("📅 통합 구글 캘린더 뷰")
        tab_fam, tab_l, tab_e = st.tabs(["👑 가족 마스터 캘린더", "🎀 라엘 캘린더", "🌻 엘린 캘린더"])
        with tab_fam:
            components.html(f'<iframe src="{cfg["admin"].get("calendar_url", "")}" style="border:0" width="100%" height="550" frameborder="0" scrolling="no"></iframe>', height=560)
        with tab_l:
            components.html(f'<iframe src="{cfg["lael"].get("calendar_url", "")}" style="border:0" width="100%" height="550" frameborder="0" scrolling="no"></iframe>', height=560)
        with tab_e:
            components.html(f'<iframe src="{cfg["ellyn"].get("calendar_url", "")}" style="border:0" width="100%" height="550" frameborder="0" scrolling="no"></iframe>', height=560)
