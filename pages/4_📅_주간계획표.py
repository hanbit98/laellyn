import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import json
import os
import datetime

if not st.session_state.get('logged_in'):
    st.warning("🔒 먼저 메인 화면에서 로그인해 주세요!")
    st.stop()

SCHED_FILE = "schedule.csv"
CONFIG_FILE = "portal_config.json"

def load_sched():
    if os.path.exists(SCHED_FILE):
        return pd.read_csv(SCHED_FILE, encoding="utf-8-sig")
    return pd.DataFrame(columns=['user', 'day', 'events'])

def save_sched(df):
    df.to_csv(SCHED_FILE, index=False, encoding="utf-8-sig")

def load_cfg():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

df_sched = load_sched()
cfg = load_cfg()
role = st.session_state.get('role')

st.title("📅 주간 시간표 & 구글 캘린더")

target_user = role
if role == 'admin':
    target_user = st.radio("확인/수정할 아이 선택", ["lael", "ellyn"], horizontal=True, format_func=lambda x: "🎀 라엘 시간표" if x == "lael" else "🌻 엘린 시간표")

days_order = ["월 (Mon)", "화 (Tue)", "수 (Wed)", "목 (Thu)", "금 (Fri)", "토 (Sat)", "일 (Sun)"]
today_idx = datetime.datetime.today().weekday()

st.subheader(f"🗓️ {'라엘' if target_user == 'lael' else '엘린'}이의 주간 고정 시간표")
cols = st.columns(7)
u_sched = df_sched[df_sched['user'] == target_user]

for i, d_name in enumerate(days_order):
    with cols[i]:
        if i == today_idx:
            st.markdown(f"<div style='background-color:#ffe6e6; padding:10px; border-radius:8px; text-align:center; font-weight:bold; color:#d9534f;'>🔥 {d_name} (오늘)</div>", unsafe_allow_html=True)
        else:
            st.markdown(f"<div style='background-color:#f0f2f6; padding:10px; border-radius:8px; text-align:center; font-weight:bold;'>{d_name}</div>", unsafe_allow_html=True)
        
        row = u_sched[u_sched['day'] == d_name]
        if not row.empty:
            items = str(row.iloc[0]['events']).split("|")
            for it in items:
                if it.strip():
                    st.markdown(f"<div style='margin-top:8px; padding:6px; background:#ffffff; border:1px solid #e0e0e0; border-radius:6px; font-size:14px;'>▪️ {it.strip()}</div>", unsafe_allow_html=True)

st.markdown("---")
st.subheader("📅 구글 캘린더 일정")
cal_mode = st.radio("캘린더 보기 모드", ["주간 (WEEK)", "월간 (MONTH)", "일정목록 (AGENDA)"], horizontal=True)
mode_param = "WEEK" if "WEEK" in cal_mode else ("MONTH" if "MONTH" in cal_mode else "AGENDA")

base_url = cfg.get(target_user, {}).get("calendar_url", "")
if base_url:
    if "mode=" in base_url:
        import re
        final_url = re.sub(r'mode=[A-Z]+', f'mode={mode_param}', base_url)
    else:
        sep = "&" if "?" in base_url else "?"
        final_url = f"{base_url}{sep}mode={mode_param}"
    components.html(f'<iframe src="{final_url}" style="border: 1px solid #ddd; border-radius: 10px;" width="100%" height="600" frameborder="0" scrolling="no"></iframe>', height=610)
else:
    st.info("구글 캘린더 URL이 설정되지 않았습니다.")

# 시간표 수정 기능
st.markdown("---")
with st.expander("✏️ 요일별 고정 시간표 수정하기 (각 일정은 | 기호로 구분)"):
    with st.form("edit_sched_form"):
        updated_events = {}
        for d_name in days_order:
            row = u_sched[u_sched['day'] == d_name]
            cur_val = str(row.iloc[0]['events']) if not row.empty else ""
            updated_events[d_name] = st.text_input(f"{d_name}", value=cur_val)
        
        if st.form_submit_button("💾 시간표 저장하기", use_container_width=True):
            for d_name, ev_str in updated_events.items():
                mask = (df_sched['user'] == target_user) & (df_sched['day'] == d_name)
                if mask.any():
                    df_sched.loc[mask, 'events'] = ev_str
                else:
                    new_r = pd.DataFrame([{'user': target_user, 'day': d_name, 'events': ev_str}])
                    df_sched = pd.concat([df_sched, new_r], ignore_index=True)
            save_sched(df_sched)
            st.success("주간 시간표가 업데이트되었습니다!")
            st.rerun()
