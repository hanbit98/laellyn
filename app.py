import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import os
from portal_data import (
    check_auth_and_render_sidebar,
    load_config,
    save_config,
    load_homework,
    save_homework,
    load_timetable,
    render_timetable_html,
    HISTORY_FILE
)

st.set_page_config(page_title="Laellyn Learning Portal", page_icon="🏰", layout="wide")

# 모든 페이지 공통: 로그인/쿠키 점검 및 좌측 사이드바('🏠 홈' 메뉴 + 하단 '로그아웃' 버튼) 렌더링
check_auth_and_render_sidebar()

cfg = load_config()
hw_df = load_homework()
tt_df = load_timetable()
role = st.session_state['role']

# 상단 헤더
if role == 'lael':
    st.markdown("<h1>🎀 안녕, 보석같은 라엘! 오늘의 학습 대시보드</h1>", unsafe_allow_html=True)
elif role == 'ellyn':
    st.markdown("<h1>🌻 안녕, 비타민 엘린! 오늘의 학습 대시보드</h1>", unsafe_allow_html=True)
else:
    st.markdown("<h1>👑 Laellyn 통합 관리자(아빠) 컨트롤 타워</h1>", unsafe_allow_html=True)

st.markdown("---")

# =========================================================
# [A] 라엘 / 엘린 개인화 대시보드 (시간표 조회 전용)
# =========================================================
if role in ['lael', 'ellyn']:
    user_cfg = cfg.get(role, {})
    user_hw = hw_df[hw_df['user'] == role].copy()

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

    # 주간 고정 시간표 (Timetable Grid - 조회 전용)
    st.subheader(f"🗓️ {st.session_state['user_name']}이의 주간 시간표")
    render_timetable_html(role, cfg, tt_df)

    st.markdown("---")

    # 구글 캘린더 임베드
    st.subheader(f"📅 {st.session_state['user_name']}이의 구글 캘린더")
    cal_url = user_cfg.get("calendar_url", "")
    if cal_url:
        components.html(
            f'<iframe src="{cal_url}" style="border: 1px solid #ddd; border-radius: 10px;" width="100%" height="550" frameborder="0" scrolling="no"></iframe>',
            height=560
        )
    else:
        st.warning("아직 구글 캘린더 주소가 등록되지 않았습니다.")

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
            
            cur_st = cfg[child_key].get('stickers', 0)
            goal_st = cfg[child_key].get('reward_goal', 20)
            st.write(f"**칭찬 스티커:** ⭐ {cur_st} / {goal_st} 개")
            b1, b2, _ = st.columns([1, 1, 2])
            with b1:
                if st.button("➕ 스티커 +1", key=f"add_st_{child_key}"):
                    cfg[child_key]['stickers'] = cur_st + 1
                    save_config(cfg)
                    st.rerun()
            with b2:
                if st.button("➖ 스티커 -1", key=f"sub_st_{child_key}"):
                    cfg[child_key]['stickers'] = max(0, cur_st - 1)
                    save_config(cfg)
                    st.rerun()

    st.markdown("---")
    st.subheader("🗓️ 라엘 & 엘린 주간 시간표 미리보기 (수정은 좌측 '📅 주간 계획표' 메뉴에서 가능)")
    t_ellyn, t_lael = st.tabs(["🌻 엘린이 시간표", "🎀 라엘이 시간표"])
    with t_ellyn:
        render_timetable_html("ellyn", cfg, tt_df)
    with t_lael:
        render_timetable_html("lael", cfg, tt_df)

    st.markdown("---")
    st.subheader("📝 최근 단어 시험 응시 기록")
    if os.path.exists(HISTORY_FILE):
        hist_df = pd.read_csv(HISTORY_FILE, encoding="utf-8-sig")
        st.dataframe(hist_df.tail(10).iloc[::-1], use_container_width=True)
    else:
        st.info("아직 응시한 단어 시험 기록이 없습니다. 아이들이 단어 시험을 완료하면 이곳에 자동 기록됩니다.")

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

    st.markdown("---")
    st.subheader("📅 통합 구글 캘린더 뷰")
    tab_fam, tab_l, tab_e = st.tabs(["👑 가족 마스터 캘린더", "🎀 라엘 캘린더", "🌻 엘린 캘린더"])
    with tab_fam:
        components.html(f'<iframe src="{cfg["admin"].get("calendar_url", "")}" style="border:0" width="100%" height="550" frameborder="0" scrolling="no"></iframe>', height=560)
    with tab_l:
        components.html(f'<iframe src="{cfg["lael"].get("calendar_url", "")}" style="border:0" width="100%" height="550" frameborder="0" scrolling="no"></iframe>', height=560)
    with tab_e:
        components.html(f'<iframe src="{cfg["ellyn"].get("calendar_url", "")}" style="border:0" width="100%" height="550" frameborder="0" scrolling="no"></iframe>', height=560)
