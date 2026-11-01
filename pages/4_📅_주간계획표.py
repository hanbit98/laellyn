import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import datetime
import re
from portal_data import (
    check_auth_and_render_sidebar,
    load_config,
    save_config,
    load_timetable,
    save_timetable,
    render_timetable_html,
    COLOR_PRESETS,
    TIME_SLOTS,
    DAYS_SHORT
)

st.set_page_config(page_title="주간 계획표 - Laellyn Portal", page_icon="📅", layout="wide")
check_auth_and_render_sidebar()

cfg = load_config()
df_tt = load_timetable()
role = st.session_state.get('role')

st.title("📅 주간 시간표 & 구글 캘린더")

target_user = role
if role == 'admin':
    target_user = st.radio(
        "👑 [관리자 모드] 확인 및 편집할 시간표 대상 선택",
        ["ellyn", "lael"],
        horizontal=True,
        format_func=lambda x: "🌻 엘린이 시간표" if x == "ellyn" else "🎀 라엘이 시간표"
    )

# 1. 실제 Timetable 그리드 출력 (첨부 이미지와 동일한 디자인)
render_timetable_html(target_user, cfg, df_tt)

# 2. Admin 전용: 시간표 일정 추가 / 수정 / 삭제 컨트롤 패널 (lael, ellyn에게는 보이지 않음)
if role == 'admin':
    st.markdown("---")
    st.subheader(f"🛠️ [관리자 전용] {'엘린이' if target_user == 'ellyn' else '라엘이'} 시간표 관리")

    tab_add, tab_edit, tab_date = st.tabs([
        "➕ 새 일정 블록 넣기 (추가/덮어쓰기)",
        "🗑️ 등록된 일정 수정 및 빼기 (삭제)",
        "📆 주 시작일(날짜) 설정"
    ])

    slot_codes = [t[0] for t in TIME_SLOTS]
    slot_labels = {t[0]: f"{t[1]} ({t[0]})" for t in TIME_SLOTS}

    with tab_add:
        st.caption("💡 팁: 줄 앞에 `[굵게]`를 붙이면 굵고 크게, `[빨강]`을 붙이면 빨간 글씨로 표시됩니다. 같은 요일·시간대에 이미 일정이 있으면 새 일정으로 덮어씁니다.")
        with st.form("add_timetable_block_form"):
            c1, c2, c3, c4 = st.columns([1.5, 1, 1, 1.8])
            with c1:
                selected_days = st.multiselect("요일 선택 (여러 요일 동시 선택 가능)", DAYS_SHORT, default=["월"])
            with c2:
                st_sel = st.selectbox("시작 시간", slot_codes[:-1], index=9, format_func=lambda x: slot_labels[x])
            with c3:
                et_sel = st.selectbox("종료 시간", slot_codes[1:], index=11, format_func=lambda x: slot_labels[x])
            with c4:
                color_sel = st.selectbox("배경 색상 / 스타일", list(COLOR_PRESETS.keys()), index=1, format_func=lambda k: COLOR_PRESETS[k])

            content_input = st.text_area(
                "시간표 칸에 들어갈 내용 (엔터로 줄바꿈 가능)",
                placeholder="예시:\n[굵게]➕ 셈율(수학) ➖\n(2:30~4:00)",
                height=100
            )

            if st.form_submit_button("➕ 시간표에 일정 넣기", type="primary", use_container_width=True):
                if not selected_days:
                    st.error("요일을 하나 이상 선택해 주세요.")
                elif slot_codes.index(et_sel) <= slot_codes.index(st_sel):
                    st.error("종료 시간은 시작 시간보다 뒤여야 합니다.")
                elif not content_input.strip():
                    st.error("일정 내용을 입력해 주세요.")
                else:
                    s_idx = slot_codes.index(st_sel)
                    e_idx = slot_codes.index(et_sel)
                    
                    # 겹치는 시간대 기존 블록 제거 후 새 블록 추가
                    rows_to_drop = []
                    for idx, r in df_tt[df_tt['user'] == target_user].iterrows():
                        if r['day'] in selected_days and r['start_time'] in slot_codes and r['end_time'] in slot_codes:
                            rs = slot_codes.index(r['start_time'])
                            re_idx = slot_codes.index(r['end_time'])
                            if max(s_idx, rs) < min(e_idx, re_idx):
                                rows_to_drop.append(idx)
                    if rows_to_drop:
                        df_tt = df_tt.drop(rows_to_drop).reset_index(drop=True)

                    next_id = int(df_tt['id'].max() + 1) if not df_tt.empty else 1
                    new_entries = []
                    for d_s in selected_days:
                        new_entries.append({
                            'id': next_id,
                            'user': target_user,
                            'day': d_s,
                            'start_time': st_sel,
                            'end_time': et_sel,
                            'content': content_input.strip(),
                            'color': color_sel
                        })
                        next_id += 1
                    df_tt = pd.concat([df_tt, pd.DataFrame(new_entries)], ignore_index=True)
                    save_timetable(df_tt)
                    st.success("시간표에 일정이 반영되었습니다!")
                    st.rerun()

    with tab_edit:
        st.caption("표를 직접 더블클릭해 시간·내용·색상을 수정하거나, 왼쪽 체크박스를 선택해 행을 삭제(`Delete` 키 또는 휴지통 아이콘)한 뒤 **[💾 변경사항 저장]** 버튼을 누르세요.")
        u_tt = df_tt[df_tt['user'] == target_user].copy()
        day_order_map = {d: i for i, d in enumerate(DAYS_SHORT)}
        u_tt['day_num'] = u_tt['day'].map(lambda x: day_order_map.get(x, 99))
        u_tt = u_tt.sort_values(['day_num', 'start_time']).drop(columns=['day_num'])

        edited_u_tt = st.data_editor(
            u_tt,
            num_rows="dynamic",
            use_container_width=True,
            hide_index=True,
            column_config={
                "id": None,
                "user": None,
                "day": st.column_config.SelectboxColumn("요일", options=DAYS_SHORT, required=True, width="small"),
                "start_time": st.column_config.SelectboxColumn("시작 시간", options=slot_codes[:-1], required=True, width="small"),
                "end_time": st.column_config.SelectboxColumn("종료 시간", options=slot_codes[1:], required=True, width="small"),
                "content": st.column_config.TextColumn("일정 내용 (줄바꿈은 \n)", required=True, width="large"),
                "color": st.column_config.SelectboxColumn("배경 색상 코드", options=list(COLOR_PRESETS.keys()), required=True, width="medium")
            },
            key=f"tt_editor_{target_user}"
        )

        if st.button("💾 수정/삭제한 시간표 저장하기", type="primary", use_container_width=True):
            other_df = df_tt[df_tt['user'] != target_user].copy()
            edited_u_tt['user'] = target_user
            # ID 재부여
            combined = pd.concat([other_df, edited_u_tt], ignore_index=True)
            combined['id'] = range(1, len(combined) + 1)
            save_timetable(combined)
            st.success("시간표 변경사항이 저장되었습니다!")
            st.rerun()

    with tab_date:
        u_cfg = cfg.get(target_user, {})
        cur_auto = bool(u_cfg.get("auto_week_date", False))
        raw_d = u_cfg.get("week_start_date", "2026-10-26")
        try:
            default_d = datetime.datetime.strptime(raw_d, "%Y-%m-%d").date()
        except Exception:
            default_d = datetime.date(2026, 10, 26)

        with st.form(f"week_date_form_{target_user}"):
            auto_chk = st.checkbox("매주 오늘 기준 이번 주 월요일 날짜로 자동 표시", value=cur_auto)
            picked_d = st.date_input("수동 설정 시 주 시작일(월요일) 선택", value=default_d)
            if st.form_submit_button("📆 주 시작일 저장"):
                # 선택한 날짜가 포함된 주의 월요일로 맞춤
                monday_d = picked_d - datetime.timedelta(days=picked_d.weekday())
                cfg[target_user]["auto_week_date"] = auto_chk
                cfg[target_user]["week_start_date"] = str(monday_d)
                save_config(cfg)
                st.success(f"주 시작일이 {monday_d}로 저장되었습니다!")
                st.rerun()

# 3. 구글 캘린더 연동 섹션
st.markdown("---")
st.subheader("📅 구글 캘린더 일정")
cal_mode = st.radio("캘린더 보기 모드", ["주간 (WEEK)", "월간 (MONTH)", "일정목록 (AGENDA)"], horizontal=True)
mode_param = "WEEK" if "WEEK" in cal_mode else ("MONTH" if "MONTH" in cal_mode else "AGENDA")

base_url = cfg.get(target_user, {}).get("calendar_url", "")
if base_url:
    if "mode=" in base_url:
        final_url = re.sub(r'mode=[A-Z]+', f'mode={mode_param}', base_url)
    else:
        sep = "&" if "?" in base_url else "?"
        final_url = f"{base_url}{sep}mode={mode_param}"
    components.html(
        f'<iframe src="{final_url}" style="border: 1px solid #ddd; border-radius: 10px;" width="100%" height="600" frameborder="0" scrolling="no"></iframe>',
        height=610
    )
else:
    st.info("구글 캘린더 URL이 설정되지 않았습니다.")
