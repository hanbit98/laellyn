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
    render_timetable_section,
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
        "👑 [관리자 모드] 확인할 시간표 대상 선택",
        ["ellyn", "lael"],
        horizontal=True,
        format_func=lambda x: "🌻 엘린이 시간표" if x == "ellyn" else "🎀 라엘이 시간표"
    )

# 1. 구글 시트 연동 시간표 (라엘YYMMDD / 엘린YYMMDD 자동 탐색 및 원본 병합/색상 렌더링)
render_timetable_section(target_user, cfg, df_tt, allow_tab_picker=True, key_suffix="sched_page")

# 2. Admin 전용: 구글 스프레드시트 주소 연결 및 로컬 예비 시간표 편집기
if role == 'admin':
    st.markdown("---")
    with st.expander("🔗 [관리자 전용] 구글 스프레드시트 시간표 연동 설정", expanded=False):
        st.markdown("""
        **사용 방법:**
        1. 시간표 구글 스프레드시트 우측 상단의 **[공유]** 버튼 클릭 ➔ 일반 액세스를 **'링크가 있는 모든 사용자 (뷰어)'**로 설정합니다.
        2. 아래 입력창에 구글 스프레드시트 주소(URL)를 붙여넣고 저장합니다.
        3. 매주 구글 시트에서 `라엘261026`, `엘린261026`처럼 **`이름 + 해당 주 월요일(YYMMDD)`** 형태로 탭을 만드시면 포털이 자동으로 이번 주(또는 가장 최신) 탭을 찾아 병합 셀과 배경색까지 그대로 불러옵니다!
        """)
        with st.form("gsheet_url_form"):
            new_sheet_url = st.text_input("시간표 구글 스프레드시트 URL", value=cfg.get("timetable_sheet_url", ""))
            if st.form_submit_button("💾 구글 시트 주소 저장 및 즉시 동기화", type="primary"):
                cfg["timetable_sheet_url"] = new_sheet_url.strip()
                save_config(cfg)
                st.cache_data.clear()
                st.success("구글 시트 주소가 저장되었습니다! 시간표를 즉시 불러옵니다.")
                st.rerun()

    with st.expander("🛠️ [관리자 전용] 내장 시간표 직접 편집 (구글 시트 미사용 시 예비용)", expanded=False):
        tab_add, tab_edit = st.tabs([
            "➕ 새 일정 블록 넣기 (추가/덮어쓰기)",
            "🗑️ 등록된 일정 수정 및 빼기 (삭제)"
        ])

        slot_codes = [t[0] for t in TIME_SLOTS]
        slot_labels = {t[0]: f"{t[1]} ({t[0]})" for t in TIME_SLOTS}

        with tab_add:
            with st.form("add_timetable_block_form"):
                c1, c2, c3, c4 = st.columns([1.5, 1, 1, 1.8])
                with c1:
                    selected_days = st.multiselect("요일 선택", DAYS_SHORT, default=["월"])
                with c2:
                    st_sel = st.selectbox("시작 시간", slot_codes[:-1], index=9, format_func=lambda x: slot_labels[x])
                with c3:
                    et_sel = st.selectbox("종료 시간", slot_codes[1:], index=11, format_func=lambda x: slot_labels[x])
                with c4:
                    color_sel = st.selectbox("배경 색상 / 스타일", list(COLOR_PRESETS.keys()), index=1, format_func=lambda k: COLOR_PRESETS[k])

                content_input = st.text_area("시간표 칸에 들어갈 내용", height=100)

                if st.form_submit_button("➕ 내장 시간표에 일정 넣기", use_container_width=True):
                    if selected_days and slot_codes.index(et_sel) > slot_codes.index(st_sel) and content_input.strip():
                        s_idx = slot_codes.index(st_sel)
                        e_idx = slot_codes.index(et_sel)
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
                        st.success("내장 시간표에 일정이 반영되었습니다!")
                        st.rerun()

        with tab_edit:
            u_tt = df_tt[df_tt['user'] == target_user].copy()
            day_order_map = {d: i for i, d in enumerate(DAYS_SHORT)}
            u_tt['day_num'] = u_tt['day'].map(lambda x: day_order_map.get(x, 99))
            u_tt = u_tt.sort_values(['day_num', 'start_time']).drop(columns=['day_num'])

            edited_u_tt = st.data_editor(
                u_tt,
                num_rows="dynamic",
                use_container_width=True,
                hide_index=True,
                key=f"tt_editor_{target_user}"
            )

            if st.button("💾 내장 시간표 변경사항 저장하기", use_container_width=True):
                other_df = df_tt[df_tt['user'] != target_user].copy()
                edited_u_tt['user'] = target_user
                combined = pd.concat([other_df, edited_u_tt], ignore_index=True)
                combined['id'] = range(1, len(combined) + 1)
                save_timetable(combined)
                st.success("변경사항이 저장되었습니다!")
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
