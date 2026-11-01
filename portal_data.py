import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import json
import os
import datetime
import hashlib

CONFIG_FILE = "portal_config.json"
HW_FILE = "homework.csv"
TT_FILE = "timetable.csv"
HISTORY_FILE = "quiz_history.csv"

USERS = {
    "lael": ["1234", "lael", "라엘"],
    "ellyn": ["1234", "ellyn", "엘린"],
    "admin": ["0000", "admin", "아빠(관리자)"]
}

COLOR_PRESETS = {
    "#ffffff": "⬜ 흰색 박스 (학교/셔틀/기본)",
    "#ead1dc": "🟣 연보라/핑크 (셈율/수학 등)",
    "#a4c2f4": "🔵 파랑 (피아노 등)",
    "#c9daf8": "🩵 하늘 (수영 등)",
    "#fff2cc": "🟡 연노랑 (CREO/영어 등)",
    "#f9cb9c": "🟠 살구/주황 (바이올린 등)",
    "#efefef": "🩶 연회색 (숙제/자습 등)",
    "#d0e0e3": "🧊 민트그레이 (인라인 등)",
    "#b6d7a8": "🟢 연초록 (골프/체육 등)",
    "#ffe599": "🟨 진노랑 (YJY/주말활동 등)",
    "transparent_red": "🔴 테두리 없음 + 빨간 글씨 강조 (★빠작/숙제 알림)"
}

TIME_SLOTS = [
    ("10:00", "오전 10시"),
    ("10:30", "오전 10시 30분"),
    ("11:00", "오전 11시"),
    ("11:30", "오전 11시 30분"),
    ("12:00", "오후 12시"),
    ("12:30", "오후 12시 30분"),
    ("13:00", "오후 1시"),
    ("13:30", "오후 1시 30분"),
    ("14:00", "오후 2시"),
    ("14:30", "오후 2시 30분"),
    ("15:00", "오후 3시"),
    ("15:30", "오후 3시 30분"),
    ("16:00", "오후 4시"),
    ("16:30", "오후 4시 30분"),
    ("17:00", "오후 5시"),
    ("17:30", "오후 5시 30분"),
    ("18:00", "오후 6시"),
    ("18:30", "오후 6시 30분"),
    ("19:00", "오후 7시"),
    ("19:30", "오후 7시 30분"),
    ("20:00", "오후 8:00"),
    ("20:30", "오후 8시 30분"),
    ("21:00", "오후 9:00"),
    ("21:30", "오후 9시 30분")
]

DAYS_SHORT = ["월", "화", "수", "목", "금", "토", "일"]
DAYS_FULL = ["월요일", "화요일", "수요일", "목요일", "금요일", "토요일", "일요일"]

def make_token(user_id):
    secret = "laellyn_secret_2026"
    return f"{user_id}:{hashlib.sha256((user_id + secret).encode()).hexdigest()[:12]}"

def verify_token(token_str):
    if not token_str or ":" not in token_str:
        return None
    uid, sig = token_str.split(":", 1)
    if uid in USERS and make_token(uid) == token_str:
        return uid
    return None

def set_browser_cookie(name, value, days=7):
    js = f"""
    <script>
    const d = new Date();
    d.setTime(d.getTime() + ({days}*24*60*60*1000));
    let expires = "expires="+ d.toUTCString();
    parent.document.cookie = "{name}=" + "{value}" + ";" + expires + ";path=/;SameSite=Lax";
    </script>
    """
    components.html(js, height=0, width=0)

def clear_browser_cookie(name):
    js = f"""
    <script>
    parent.document.cookie = "{name}=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;SameSite=Lax";
    </script>
    """
    components.html(js, height=0, width=0)

def get_cookie_user():
    # 1. Try Streamlit 1.37+ native st.context.cookies
    try:
        cookies = st.context.cookies
        if cookies and "laellyn_auth" in cookies:
            uid = verify_token(cookies["laellyn_auth"])
            if uid:
                return uid
    except Exception:
        pass
    # 2. Try query_params fallback
    try:
        qp = st.query_params
        if "auth" in qp:
            uid = verify_token(qp["auth"])
            if uid:
                return uid
    except Exception:
        pass
    return None

def check_auth_and_render_sidebar():
    """모든 페이지 최상단에서 로그인 세션/쿠키를 점검하고, 좌측 사이드바('🏠 홈' 메뉴 + 하단 '로그아웃' 버튼)를 렌더링합니다."""
    if 'logged_in' not in st.session_state:
        st.session_state['logged_in'] = False
    if 'role' not in st.session_state:
        st.session_state['role'] = None
    if 'user_name' not in st.session_state:
        st.session_state['user_name'] = ""

    # 세션이 비어있다면 브라우저 쿠키 또는 URL 토큰으로 자동 복원 시도
    if not st.session_state['logged_in'] and not st.session_state.get('just_logged_out', False):
        cookie_uid = get_cookie_user()
        if cookie_uid and cookie_uid in USERS:
            st.session_state['logged_in'] = True
            st.session_state['role'] = USERS[cookie_uid][1]
            st.session_state['user_name'] = USERS[cookie_uid][2]

    # 비로그인 상태일 경우 로그인 화면 표시 후 실행 중단
    if not st.session_state['logged_in']:
        st.markdown("""<style>[data-testid="stSidebar"] { display: none !important; }</style>""", unsafe_allow_html=True)
        st.markdown("<h1 style='text-align: center; margin-top: 30px;'>🏰 Laellyn Learning Portal</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; font-size: 18px; color: #666;'>라엘 & 엘린 맞춤형 스마트 학습 포털</p>", unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([1, 1.5, 1])
        with col2:
            with st.form("global_login_form"):
                input_id = st.text_input("아이디 (lael / ellyn / admin)")
                input_pw = st.text_input("비밀번호", type="password")
                remember = st.checkbox("로그인 상태 유지 (쿠키 저장)", value=True)
                submitted = st.form_submit_button("로그인 🚀", use_container_width=True)
                
                if submitted:
                    uid = input_id.strip().lower()
                    if uid in USERS and USERS[uid][0] == input_pw.strip():
                        st.session_state['logged_in'] = True
                        st.session_state['role'] = USERS[uid][1]
                        st.session_state['user_name'] = USERS[uid][2]
                        st.session_state['just_logged_out'] = False
                        token = make_token(uid)
                        if remember:
                            set_browser_cookie("laellyn_auth", token, days=14)
                            try:
                                st.query_params["auth"] = token
                            except Exception:
                                pass
                        st.rerun()
                    else:
                        st.error("아이디나 비밀번호가 틀렸습니다. 다시 확인해 주세요!")
        st.stop()

    # 로그인 완료 상태: 쿠키/쿼리 파라미터 유지 및 커스텀 사이드바 렌더링
    role = st.session_state['role']
    token = make_token(role)
    try:
        if st.query_params.get("auth") != token:
            st.query_params["auth"] = token
    except Exception:
        pass

    # 기본 stSidebarNav('app'으로 뜨는 기본 메뉴)를 숨기고 깔끔한 커스텀 메뉴 + 하단 로그아웃 버튼 표시
    st.markdown("""
        <style>
        /* 기본 멀티페이지 네비게이션 숨김 (커스텀 '🏠 홈' 네비게이션 사용) */
        [data-testid="stSidebarNav"] {
            display: none !important;
        }
        </style>
    """, unsafe_allow_html=True)

    with st.sidebar:
        role_badge = "🎀 라엘" if role == "lael" else ("🌻 엘린" if role == "ellyn" else "👑 아빠(관리자)")
        st.markdown(f"### 🏰 Laellyn Portal")
        st.caption(f"현재 접속: **{role_badge}**")
        st.markdown("---")
        
        # 좌측 메뉴 (첫 번째 메뉴를 'app' 대신 '🏠 홈'으로 표시)
        st.page_link("app.py", label="홈", icon="🏠")
        if role in ["lael", "admin"]:
            st.page_link("pages/1_🎀_라엘단어장.py", label="라엘 단어장", icon="🎀")
        if role in ["ellyn", "admin"]:
            st.page_link("pages/2_🌻_엘린단어장.py", label="엘린 단어장", icon="🌻")
        st.page_link("pages/3_✅_숙제체크.py", label="숙제 체크", icon="✅")
        st.page_link("pages/4_📅_주간계획표.py", label="주간 계획표", icon="📅")
        st.page_link("pages/5_🎁_오늘의비타민.py", label="오늘의 비타민", icon="🎁")

        st.markdown("---")
        st.write("")
        if st.button("🔓 로그아웃", key="sidebar_logout_btn", use_container_width=True):
            st.session_state['logged_in'] = False
            st.session_state['role'] = None
            st.session_state['user_name'] = ""
            st.session_state['just_logged_out'] = True
            clear_browser_cookie("laellyn_auth")
            try:
                st.query_params.clear()
            except Exception:
                pass
            st.rerun()

# ---------------------------------------------------------
# 설정 / 숙제 / 시간표 데이터 입출력 헬퍼
# ---------------------------------------------------------
def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

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

def load_timetable():
    if os.path.exists(TT_FILE):
        df = pd.read_csv(TT_FILE, encoding="utf-8-sig")
        df = df.fillna("")
        return df
    return pd.DataFrame(columns=['id', 'user', 'day', 'start_time', 'end_time', 'content', 'color'])

def save_timetable(df):
    df.to_csv(TT_FILE, index=False, encoding="utf-8-sig")

# ---------------------------------------------------------
# 실제 시간표 (Timetable Grid) HTML 렌더링 함수
# ---------------------------------------------------------
def format_cell_text(raw_text, is_transparent_red=False):
    lines = str(raw_text).split("\n")
    formatted_lines = []
    for line in lines:
        line_s = line.strip()
        if not line_s:
            continue
        if is_transparent_red:
            clean_l = line_s.replace("[빨강]", "").replace("[굵게]", "")
            formatted_lines.append(f"<div style='color:#e60000; font-weight:800; font-size:13.5px;'>{clean_l}</div>")
        elif line_s.startswith("[빨강]"):
            clean_l = line_s.replace("[빨강]", "")
            formatted_lines.append(f"<div style='color:#e60000; font-weight:800; font-size:13px;'>{clean_l}</div>")
        elif line_s.startswith("[굵게]"):
            clean_l = line_s.replace("[굵게]", "")
            formatted_lines.append(f"<div style='color:#111111; font-weight:800; font-size:15px; margin:2px 0;'>{clean_l}</div>")
        else:
            formatted_lines.append(f"<div style='color:#222222; font-size:13px; line-height:1.35;'>{line_s}</div>")
    return "".join(formatted_lines)

def render_timetable_html(target_user, cfg, df_tt):
    user_title = "엘린이 시간표" if target_user == "ellyn" else "라엘이 시간표"
    u_cfg = cfg.get(target_user, {})
    
    # 주 시작일(월요일) 계산
    auto_date = u_cfg.get("auto_week_date", False)
    if auto_date:
        today = datetime.date.today()
        monday_date = today - datetime.timedelta(days=today.weekday())
    else:
        raw_d = u_cfg.get("week_start_date", "2026-10-26")
        try:
            monday_date = datetime.datetime.strptime(raw_d, "%Y-%m-%d").date()
        except Exception:
            monday_date = datetime.date(2026, 10, 26)

    week_start_label = f"{monday_date.month}월 {monday_date.day}일"
    day_headers = []
    for i, d_full in enumerate(DAYS_FULL):
        cur_d = monday_date + datetime.timedelta(days=i)
        day_headers.append((DAYS_SHORT[i], f"{cur_d.month}월 {cur_d.day}일", d_full))

    # 시간 인덱스 매핑 (10:00 ~ 21:00, 총 23개 행 표시)
    display_slots = TIME_SLOTS[:-1] # 10:00 ~ 21:00
    slot_times = [t[0] for t in TIME_SLOTS] # 10:00 ~ 21:30

    u_df = df_tt[df_tt['user'] == target_user].copy()

    # 그리드 상태 초기화: grid[row_idx][day_short]
    n_rows = len(display_slots)
    grid = {r: {d: {"type": "empty"} for d in DAYS_SHORT} for r in range(n_rows)}

    for _, row in u_df.iterrows():
        d_short = str(row['day']).strip()
        st_time = str(row['start_time']).strip()
        et_time = str(row['end_time']).strip()
        if d_short not in DAYS_SHORT or st_time not in slot_times:
            continue
        r_start = slot_times.index(st_time)
        if r_start >= n_rows:
            continue
        if et_time in slot_times:
            r_end = slot_times.index(et_time)
        else:
            r_end = r_start + 1
        span = max(1, min(r_end - r_start, n_rows - r_start))

        # 이미 위쪽 블록이 차지한 칸이면 건너뜀
        if grid[r_start][d_short]["type"] != "empty":
            continue

        grid[r_start][d_short] = {
            "type": "block",
            "span": span,
            "content": str(row['content']),
            "color": str(row['color']).strip() if str(row['color']).strip() else "#ffffff"
        }
        for s_idx in range(1, span):
            if r_start + s_idx < n_rows:
                grid[r_start + s_idx][d_short] = {"type": "spanned"}

    # HTML 테이블 조립
    html = f"""
    <style>
    .tt-wrapper {{
        font-family: 'Pretendard', 'Malgun Gothic', 'Apple SD Gothic Neo', sans-serif;
        border: 1px solid #cccccc;
        border-radius: 6px;
        overflow-x: auto;
        background: #ffffff;
        box-shadow: 0 2px 6px rgba(0,0,0,0.05);
        margin-bottom: 16px;
    }}
    .tt-banner {{
        background-color: #fff2cc;
        padding: 12px 20px;
        border-bottom: 1px solid #d6b656;
    }}
    .tt-banner-title {{
        font-size: 24px;
        font-weight: 800;
        color: #111111;
        margin-bottom: 4px;
    }}
    .tt-banner-sub {{
        font-size: 14px;
        color: #333333;
        font-weight: 600;
    }}
    .tt-table {{
        width: 100%;
        border-collapse: collapse;
        table-layout: fixed;
        min-width: 850px;
    }}
    .tt-table th.time-col {{
        width: 95px;
        background: #ffffff;
        border-bottom: 1.5px solid #222222;
        border-right: 1.5px solid #222222;
    }}
    .tt-table th.day-col {{
        background: #ffffff;
        padding: 8px 4px;
        text-align: center;
        border-bottom: 1.5px solid #222222;
        border-right: 1px solid #e0e0e0;
    }}
    .tt-date-text {{
        font-size: 12.5px;
        color: #666666;
        font-weight: 500;
        margin-bottom: 3px;
    }}
    .tt-day-text {{
        font-size: 15px;
        color: #111111;
        font-weight: 800;
    }}
    .tt-time-cell {{
        text-align: right;
        padding: 4px 10px 4px 4px;
        font-size: 12.5px;
        color: #444444;
        background-color: #fafafa;
        border-right: 1.5px solid #222222;
        border-bottom: 1px solid #e2e2e2;
        height: 30px;
        white-space: nowrap;
    }}
    .tt-empty-cell {{
        border-right: 1px solid #ebebeb;
        border-bottom: 1px solid #ebebeb;
        height: 30px;
        background-color: #ffffff;
    }}
    .tt-block-cell {{
        text-align: center;
        vertical-align: middle;
        padding: 6px 4px;
        border: 1.5px solid #222222 !important;
        word-break: keep-all;
    }}
    .tt-red-text-cell {{
        text-align: center;
        vertical-align: middle;
        padding: 4px 2px;
        border-right: 1px solid #ebebeb;
        border-bottom: 1px solid #ebebeb;
        background-color: #ffffff;
    }}
    </style>
    <div class="tt-wrapper">
        <div class="tt-banner">
            <div class="tt-banner-title">{user_title}</div>
            <div class="tt-banner-sub">주 시작일: &nbsp;<b>{week_start_label}</b></div>
        </div>
        <table class="tt-table">
            <thead>
                <tr>
                    <th class="time-col"></th>
    """
    for _, d_date_str, d_full_str in day_headers:
        html += f"""
                    <th class="day-col">
                        <div class="tt-date-text">{d_date_str}</div>
                        <div class="tt-day-text">{d_full_str}</div>
                    </th>
        """
    html += """
                </tr>
            </thead>
            <tbody>
    """

    for r_idx, (t_code, t_label) in enumerate(display_slots):
        html += f"<tr><td class='tt-time-cell'>{t_label}</td>"
        for d_short in DAYS_SHORT:
            cell_info = grid[r_idx][d_short]
            ctype = cell_info["type"]
            if ctype == "spanned":
                continue
            elif ctype == "empty":
                html += "<td class='tt-empty-cell'></td>"
            elif ctype == "block":
                span = cell_info["span"]
                bg_color = cell_info["color"]
                raw_content = cell_info["content"]
                if bg_color == "transparent_red":
                    inner_html = format_cell_text(raw_content, is_transparent_red=True)
                    html += f"<td class='tt-red-text-cell' rowspan='{span}'>{inner_html}</td>"
                else:
                    inner_html = format_cell_text(raw_content, is_transparent_red=False)
                    html += f"<td class='tt-block-cell' rowspan='{span}' style='background-color:{bg_color};'>{inner_html}</td>"
        html += "</tr>"

    html += """
            </tbody>
        </table>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)
