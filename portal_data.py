import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import json
import os
import io
import re
import datetime
import hashlib
import urllib.parse
import requests
import openpyxl

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

# ---------------------------------------------------------
# 1. 인증 / 쿠키 / 커스텀 사이드바 ('🏠 홈' + 하단 '로그아웃')
# ---------------------------------------------------------
def make_token(user_id):
    secret = "laellyn_secret_2026"
    return f"{user_id}:{hashlib.sha256((user_id + secret).encode()).hexdigest()[:12]}"

def verify_token(token_str):
    if not token_str or ":" not in token_str:
        return None
    uid, _ = token_str.split(":", 1)
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
    try:
        cookies = st.context.cookies
        if cookies and "laellyn_auth" in cookies:
            uid = verify_token(cookies["laellyn_auth"])
            if uid:
                return uid
    except Exception:
        pass
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
    if 'logged_in' not in st.session_state:
        st.session_state['logged_in'] = False
    if 'role' not in st.session_state:
        st.session_state['role'] = None
    if 'user_name' not in st.session_state:
        st.session_state['user_name'] = ""

    if not st.session_state['logged_in'] and not st.session_state.get('just_logged_out', False):
        cookie_uid = get_cookie_user()
        if cookie_uid and cookie_uid in USERS:
            st.session_state['logged_in'] = True
            st.session_state['role'] = USERS[cookie_uid][1]
            st.session_state['user_name'] = USERS[cookie_uid][2]

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

    role = st.session_state['role']
    token = make_token(role)
    try:
        if st.query_params.get("auth") != token:
            st.query_params["auth"] = token
    except Exception:
        pass

    st.markdown("""
        <style>
        [data-testid="stSidebarNav"] {
            display: none !important;
        }
        </style>
    """, unsafe_allow_html=True)

    with st.sidebar:
        role_badge = "🎀 라엘" if role == "lael" else ("🌻 엘린" if role == "ellyn" else "👑 아빠(관리자)")
        st.markdown("### 🏰 Laellyn Portal")
        st.caption(f"현재 접속: **{role_badge}**")
        st.markdown("---")
        
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
# 2. 설정 / 숙제 / 로컬 시간표 입출력
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
# 3. 구글 스프레드시트 실시간 시간표 연동 엔진 (라엘YYMMDD / 엘린YYMMDD)
# ---------------------------------------------------------
def extract_sheet_id(sheet_url_or_id):
    if not sheet_url_or_id:
        return ""
    s = str(sheet_url_or_id).strip()
    if "여기에_" in s or len(s) < 15:
        return ""
    m = re.search(r'/spreadsheets/d/([a-zA-Z0-9-_]+)', s)
    if m:
        return m.group(1)
    if re.match(r'^[a-zA-Z0-9-_]{20,}$', s):
        return s
    return ""

def get_candidate_yymmdd_list():
    """오늘 기준으로 이번 주 월요일, 지난주 월요일, 다음 주 월요일 순으로 YYMMDD 후보 리스트를 반환합니다."""
    today = datetime.date.today()
    this_monday = today - datetime.timedelta(days=today.weekday())
    candidates = [
        this_monday,
        this_monday - datetime.timedelta(days=7),
        this_monday + datetime.timedelta(days=7),
        this_monday - datetime.timedelta(days=14)
    ]
    return [d.strftime("%y%m%d") for d in candidates]

@st.cache_data(ttl=300, show_spinner=False)
def fetch_gsheet_xlsx_bytes(sheet_id):
    """구글 시트를 xlsx 바이트로 다운로드하여 병합 셀, 배경색, 모든 탭 목록을 한 번에 가져옵니다."""
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=xlsx"
    resp = requests.get(url, timeout=12)
    if resp.status_code == 200 and resp.content[:2] == b'PK':
        return resp.content
    return None

def list_user_tabs_from_xlsx(xlsx_bytes, prefix):
    """엑셀 워크북 내에서 해당 아이(라엘/엘린)의 탭 목록을 최신 YYMMDD 순으로 정렬해 반환합니다."""
    try:
        wb = openpyxl.load_workbook(io.BytesIO(xlsx_bytes), data_only=True)
        all_tabs = [name for name in wb.sheetnames if name.startswith(prefix)]
        
        # YYMMDD 패턴이 있는 탭들을 날짜 역순(최신순)으로 정렬
        dated_tabs = []
        other_tabs = []
        for t in all_tabs:
            m = re.match(rf'^{re.escape(prefix)}(\d{{6}})$', t.strip())
            if m:
                dated_tabs.append((m.group(1), t))
            else:
                other_tabs.append(t)
        dated_tabs.sort(key=lambda x: x[0], reverse=True)
        return [t for _, t in dated_tabs] + other_tabs
    except Exception:
        return []

def select_best_tab(available_tabs, prefix):
    """1순위: 이번 주 월요일(YYMMDD) 탭 -> 2순위: 가장 최근 YYMMDD 탭 -> 3순위: 첫 번째 매칭 탭"""
    if not available_tabs:
        return None
    today = datetime.date.today()
    this_monday_str = (today - datetime.timedelta(days=today.weekday())).strftime("%y%m%d")
    target_this_week = f"{prefix}{this_monday_str}"
    if target_this_week in available_tabs:
        return target_this_week
    return available_tabs[0]

def infer_color_from_text(text):
    """배경색이 지정되지 않았거나 기본값일 때 과목/일정 키워드로 파스텔 배경색을 자동 추론합니다."""
    t = str(text)
    if ("★" in t or "빠작" in t or "↓" in t) and "교시" not in t and "종료" not in t and len(t) < 35:
        return "transparent_red"
    if any(k in t for k in ["셈율", "수학", "늘푸른"]):
        return "#ead1dc"
    if "피아노" in t:
        return "#a4c2f4"
    if any(k in t for k in ["수영", "아쿠아스타"]) and "셔틀" not in t:
        return "#c9daf8"
    if any(k in t for k in ["CREO", "최선", "영어", "DYB"]) and "라이드" not in t and "셔틀" not in t and "↓" not in t:
        return "#fff2cc"
    if "바이올린" in t:
        return "#f9cb9c"
    if "숙제 하고" in t or "늘푸른 숙제" in t:
        return "#efefef"
    if "인라인" in t or "줄넘기" in t:
        return "#d0e0e3"
    if "골프" in t:
        return "#b6d7a8"
    if any(k in t for k in ["YJY", "댄스", "KEENS"]):
        return "#ffe599"
    return "#ffffff"

def style_multiline_cell_text(raw_text, is_red_only=False):
    """셀 내부 텍스트를 줄 단위로 분석하여 점심시간/빠작/숙제는 빨간색, 종료/과목명은 굵게 렌더링합니다."""
    lines = str(raw_text).replace("\r\n", "\n").split("\n")
    out = []
    for line in lines:
        s = line.strip()
        if not s:
            continue
        clean_s = s.replace("[빨강]", "").replace("[굵게]", "")
        if is_red_only or s.startswith("[빨강]") or any(k in clean_s for k in ["점심시간", "★", "빠작", "↓"]):
            out.append(f"<div style='color:#e60000; font-weight:800; font-size:13px; line-height:1.35;'>{clean_s}</div>")
        elif s.startswith("[굵게]") or "종료" in clean_s:
            sz = "16px" if "종료" in clean_s else "14.5px"
            out.append(f"<div style='color:#111111; font-weight:800; font-size:{sz}; margin:2px 0; line-height:1.35;'>{clean_s}</div>")
        elif any(k in clean_s for k in ["셈율", "피아노", "바이올린", "CREO", "수영", "인라인", "골프", "YJY", "최선어학원", "늘푸른 수학원", "KEENS"]):
            out.append(f"<div style='color:#111111; font-weight:800; font-size:14px; line-height:1.35;'>{clean_s}</div>")
        else:
            out.append(f"<div style='color:#222222; font-size:12.5px; line-height:1.35;'>{clean_s}</div>")
    return "".join(out)

def render_gsheet_tab_html(xlsx_bytes, tab_name, fallback_title="시간표"):
    """구글 시트의 특정 탭(예: 라엘261026, 엘린261026)을 원본 병합 셀, 배경색, 날짜 헤더 그대로 HTML 테이블로 렌더링합니다."""
    wb = openpyxl.load_workbook(io.BytesIO(xlsx_bytes), data_only=True)
    if tab_name not in wb.sheetnames:
        return False
    ws = wb[tab_name]

    # 1. '월요일'이 위치한 헤더 행과 열 자동 탐색
    day_row_idx = None
    mon_col_idx = None
    for r in range(1, min(10, ws.max_row + 1)):
        for c in range(1, min(12, ws.max_column + 1)):
            val = str(ws.cell(r, c).value or "").strip()
            if val in ["월요일", "월"]:
                day_row_idx = r
                mon_col_idx = c
                break
        if day_row_idx:
            break

    if not day_row_idx or not mon_col_idx:
        return False

    time_col_idx = max(1, mon_col_idx - 1)
    date_row_idx = day_row_idx - 1 if day_row_idx > 1 else None

    # 상단 배너 제목 및 주 시작일 추출
    sheet_title = fallback_title
    week_start_str = ""
    for r in range(1, day_row_idx):
        for c in range(1, mon_col_idx + 4):
            v = ws.cell(r, c).value
            if v is not None:
                vs = str(v).strip()
                if "시간표" in vs:
                    sheet_title = vs
                elif isinstance(v, (datetime.datetime, datetime.date)):
                    week_start_str = f"{v.month}월 {v.day}일"
                elif re.search(r'\d+월\s*\d+일', vs) and r < date_row_idx:
                    week_start_str = vs

    # 요일 및 날짜 헤더 추출
    day_headers = []
    for i in range(7):
        col_c = mon_col_idx + i
        d_name = str(ws.cell(day_row_idx, col_c).value or DAYS_FULL[i]).strip()
        d_date_str = ""
        if date_row_idx:
            dv = ws.cell(date_row_idx, col_c).value
            if isinstance(dv, (datetime.datetime, datetime.date)):
                d_date_str = f"{dv.month}월 {dv.day}일"
            elif dv is not None:
                d_date_str = str(dv).strip()
        day_headers.append((d_date_str, d_name))

    if not week_start_str and day_headers and day_headers[0][0]:
        week_start_str = day_headers[0][0]

    # 2. 병합 셀(Merged Cells) 맵 구성
    merged_lookup = {}
    for m_range in ws.merged_cells.ranges:
        min_c, min_r, max_c, max_r = m_range.bounds
        for r in range(min_r, max_r + 1):
            for c in range(min_c, max_c + 1):
                if r == min_r and c == min_c:
                    merged_lookup[(r, c)] = {
                        "type": "top_left",
                        "rowspan": max_r - min_r + 1,
                        "colspan": max_c - min_c + 1
                    }
                else:
                    merged_lookup[(r, c)] = {"type": "spanned"}

    # 3. 시간표 본문 시작~끝 행 찾기
    start_r = day_row_idx + 1
    end_r = ws.max_row
    # 하단 빈 행 제거
    while end_r >= start_r:
        has_any = False
        for c in range(time_col_idx, mon_col_idx + 7):
            if ws.cell(end_r, c).value is not None or (end_r, c) in merged_lookup:
                has_any = True
                break
        if has_any:
            break
        end_r -= 1

    # 4. HTML 조립
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
        display: flex;
        justify-content: space-between;
        align-items: center;
    }}
    .tt-banner-title {{
        font-size: 24px;
        font-weight: 800;
        color: #111111;
        margin-bottom: 2px;
    }}
    .tt-banner-sub {{
        font-size: 14px;
        color: #333333;
        font-weight: 600;
    }}
    .tt-badge {{
        background: #ffffff;
        border: 1px solid #d6b656;
        border-radius: 20px;
        padding: 4px 12px;
        font-size: 12.5px;
        font-weight: 700;
        color: #555555;
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
            <div>
                <div class="tt-banner-title">{sheet_title}</div>
                <div class="tt-banner-sub">주 시작일: &nbsp;<b>{week_start_str}</b></div>
            </div>
            <div class="tt-badge">🟢 구글 시트 연동 ({tab_name})</div>
        </div>
        <table class="tt-table">
            <thead>
                <tr>
                    <th class="time-col"></th>
    """
    for d_date_str, d_full_str in day_headers:
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

    for r in range(start_r, end_r + 1):
        t_val = ws.cell(r, time_col_idx).value
        if isinstance(t_val, datetime.time):
            hr = t_val.hour
            mn = t_val.minute
            ampm = "오전" if hr < 12 else "오후"
            disp_h = hr if hr <= 12 else hr - 12
            if disp_h == 0:
                disp_h = 12
            t_str = f"{ampm} {disp_h}시" if mn == 0 else f"{ampm} {disp_h}시 {mn}분"
        else:
            t_str = str(t_val or "").strip()

        html += f"<tr><td class='tt-time-cell'>{t_str}</td>"

        for i in range(7):
            c = mon_col_idx + i
            m_info = merged_lookup.get((r, c))
            if m_info and m_info["type"] == "spanned":
                continue

            rowspan = m_info["rowspan"] if m_info else 1
            colspan = m_info["colspan"] if m_info else 1
            cell = ws.cell(r, c)
            val = cell.value
            val_str = str(val).strip() if val is not None else ""

            if not val_str and rowspan == 1 and colspan == 1:
                html += "<td class='tt-empty-cell'></td>"
                continue

            # 셀 배경색 추출 (openpyxl RGB -> 미지정 시 키워드 색상 추론)
            bg_hex = None
            try:
                if cell.fill and cell.fill.fill_type == "solid" and cell.fill.start_color:
                    rgb = str(cell.fill.start_color.rgb or "")
                    if len(rgb) == 8 and rgb != "00000000":
                        cand = "#" + rgb[2:].lower()
                        if cand != "#ffffff":
                            bg_hex = cand
                    elif len(rgb) == 6:
                        cand = "#" + rgb.lower()
                        if cand != "#ffffff":
                            bg_hex = cand
            except Exception:
                pass

            if not bg_hex:
                bg_hex = infer_color_from_text(val_str)

            # 폰트 빨간색 여부 확인
            is_font_red = False
            try:
                if cell.font and cell.font.color and cell.font.color.rgb:
                    frgb = str(cell.font.color.rgb).upper()
                    if frgb.endswith("FF0000") or frgb.endswith("E60000") or frgb.endswith("CC0000"):
                        is_font_red = True
            except Exception:
                pass

            span_attr = f" rowspan='{rowspan}'" if rowspan > 1 else ""
            if colspan > 1:
                span_attr += f" colspan='{colspan}'"

            if bg_hex == "transparent_red" or (is_font_red and rowspan == 1 and bg_hex == "#ffffff"):
                inner = style_multiline_cell_text(val_str, is_red_only=True)
                html += f"<td class='tt-red-text-cell'{span_attr}>{inner}</td>"
            else:
                inner = style_multiline_cell_text(val_str, is_red_only=False)
                html += f"<td class='tt-block-cell'{span_attr} style='background-color:{bg_hex};'>{inner}</td>"

        html += "</tr>"

    html += """
            </tbody>
        </table>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)
    return True

# ---------------------------------------------------------
# 4. 로컬 CSV 기반 시간표 렌더링 (폴백 및 직접 편집용)
# ---------------------------------------------------------
def render_local_timetable_html(target_user, cfg, df_tt):
    user_title = "엘린이 시간표" if target_user == "ellyn" else "라엘이 시간표"
    u_cfg = cfg.get(target_user, {})
    
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

    display_slots = TIME_SLOTS[:-1]
    slot_times = [t[0] for t in TIME_SLOTS]
    u_df = df_tt[df_tt['user'] == target_user].copy()

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
        r_end = slot_times.index(et_time) if et_time in slot_times else r_start + 1
        span = max(1, min(r_end - r_start, n_rows - r_start))

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

    for r_idx, (_, t_label) in enumerate(display_slots):
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
                    inner_html = style_multiline_cell_text(raw_content, is_red_only=True)
                    html += f"<td class='tt-red-text-cell' rowspan='{span}'>{inner_html}</td>"
                else:
                    inner_html = style_multiline_cell_text(raw_content, is_red_only=False)
                    html += f"<td class='tt-block-cell' rowspan='{span}' style='background-color:{bg_hex if (bg_hex:=bg_color) else "#ffffff"};'>{inner_html}</td>"
        html += "</tr>"

    html += """
            </tbody>
        </table>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)

def render_timetable_section(target_user, cfg, df_tt, allow_tab_picker=True, key_suffix="main"):
    """
    구글 스프레드시트 URL이 설정되어 있으면 시트에서 '라엘YYMMDD' / '엘린YYMMDD' 탭을 자동으로 찾아 렌더링하고,
    연동 전이거나 오프라인일 때는 내장된 timetable.csv 시간표를 렌더링합니다.
    """
    sheet_url = cfg.get("timetable_sheet_url", "")
    sheet_id = extract_sheet_id(sheet_url)
    prefix = "라엘" if target_user == "lael" else "엘린"
    fallback_title = "라엘이 시간표" if target_user == "lael" else "엘린이 시간표"

    if sheet_id:
        xlsx_bytes = fetch_gsheet_xlsx_bytes(sheet_id)
        if xlsx_bytes:
            user_tabs = list_user_tabs_from_xlsx(xlsx_bytes, prefix)
            if user_tabs:
                default_tab = select_best_tab(user_tabs, prefix)
                selected_tab = default_tab
                if allow_tab_picker:
                    c_sel, c_btn = st.columns([4, 1])
                    with c_sel:
                        idx = user_tabs.index(default_tab) if default_tab in user_tabs else 0
                        selected_tab = st.selectbox(
                            f"📑 구글 시트 탭 선택 ({prefix}+YYMMDD 자동 인식)",
                            user_tabs,
                            index=idx,
                            key=f"gsheet_tab_sel_{target_user}_{key_suffix}"
                        )
                    with c_btn:
                        st.write("")
                        if st.button("🔄 시트 새로고침", key=f"gsheet_refresh_{target_user}_{key_suffix}", use_container_width=True):
                            st.cache_data.clear()
                            st.rerun()
                ok = render_gsheet_tab_html(xlsx_bytes, selected_tab, fallback_title=fallback_title)
                if ok:
                    return
        else:
            st.warning("⚠️ 구글 시트에 접근할 수 없습니다. 구글 스프레드시트 우측 상단 **[공유] ➔ '링크가 있는 모든 사용자(뷰어)'**로 설정되어 있는지 확인해 주세요. (현재는 기본 저장된 시간표를 표시합니다.)")

    # 구글 시트 URL 미설정 또는 로드 실패 시 내장 시간표 렌더링
    render_local_timetable_html(target_user, cfg, df_tt)
