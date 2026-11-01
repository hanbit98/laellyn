import streamlit as st
import json
import os
import datetime

from portal_data import check_auth_and_render_sidebar
st.set_page_config(page_title="오늘의 비타민 - Laellyn Portal", page_icon="🎁", layout="wide")
check_auth_and_render_sidebar()

CONFIG_FILE = "portal_config.json"
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

def load_cfg():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"vitamins": []}

def save_cfg(cfg):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)

cfg = load_cfg()
role = st.session_state.get('role')

st.title("🎁 오늘의 비타민 & 칭찬 스티커 보드")
st.write("열심히 공부한 라엘이와 엘린이를 위한 아빠의 깜짝 사진첩 & 응원 공간이에요! ❤️")

# 1. 아빠(Admin) 전용 사진 업로드 섹션
if role == 'admin':
    with st.expander("📸 [아빠 전용] 새로운 아이돌 사진 / 응원 메시지 올리기", expanded=True):
        with st.form("vitamin_upload_form"):
            v_target = st.selectbox("보여줄 대상", ["전체", "lael", "ellyn"], format_func=lambda x: "👨‍👩‍👧‍👧 라엘 & 엘린 전체" if x == "전체" else ("🎀 라엘 전용" if x == "lael" else "🌻 엘린 전용"))
            v_title = st.text_input("제목 (예: 🎀 오늘 단어 만점 기념 장원영 & 이서 포토!)")
            v_caption = st.text_area("아빠의 응원 한마디")
            v_file = st.file_uploader("사진 파일 업로드 (JPG, PNG, WEBP)", type=["jpg", "jpeg", "png", "webp"])
            v_url = st.text_input("또는 이미지 웹 주소(URL) 직접 입력 (선택사항)")
            
            if st.form_submit_button("🎁 비타민 등록하기", use_container_width=True):
                img_path = ""
                if v_file is not None:
                    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                    img_path = os.path.join(UPLOAD_DIR, f"{ts}_{v_file.name}")
                    with open(img_path, "wb") as f:
                        f.write(v_file.getbuffer())
                elif v_url.strip():
                    img_path = v_url.strip()

                vitamins = cfg.get("vitamins", [])
                new_id = max([v.get("id", 0) for v in vitamins], default=0) + 1
                vitamins.insert(0, {
                    "id": new_id,
                    "target": v_target,
                    "title": v_title if v_title else "🎁 오늘의 깜짝 비타민!",
                    "caption": v_caption,
                    "image_path": img_path,
                    "date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                })
                cfg["vitamins"] = vitamins
                save_cfg(cfg)
                st.success("새로운 비타민 게시물이 등록되었습니다!")
                st.rerun()

st.markdown("---")

# 2. 비타민 피드 출력
vitamins = cfg.get("vitamins", [])
if role in ['lael', 'ellyn']:
    vitamins = [v for v in vitamins if v.get("target") in ["전체", role]]

if not vitamins:
    st.info("아직 등록된 비타민 사진이 없어요! 아빠에게 아이브 사진을 올려달라고 요청해 보세요 😊")
else:
    cols = st.columns(2)
    for idx, item in enumerate(vitamins):
        with cols[idx % 2]:
            with st.container(border=True):
                st.markdown(f"### {item.get('title', '')}")
                st.caption(f"📅 등록일: {item.get('date', '')}")
                img_p = item.get("image_path", "")
                if img_p:
                    if img_p.startswith("http") or os.path.exists(img_p):
                        st.image(img_p, use_container_width=True)
                if item.get("caption"):
                    st.info(item.get("caption"))
                if role == 'admin':
                    if st.button("🗑️ 삭제", key=f"del_vit_{item.get('id', idx)}"):
                        cfg["vitamins"] = [v for v in cfg["vitamins"] if v.get("id") != item.get("id")]
                        save_cfg(cfg)
                        st.rerun()
