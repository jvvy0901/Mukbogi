"""MUKBOGI Streamlit 프로토타입 진입 파일.

실행: streamlit run app.py
"""

import streamlit as st

from core import auth, home, images, onboarding, splash, style

st.set_page_config(page_title="MUKBOGI", layout="centered")
style.inject()

if splash.should_show():
    splash.render()
elif auth.should_show():
    auth.render()
elif "profile" not in st.session_state:
    onboarding.render()
else:
    home.render()

style.enable_drag_scroll()
style.render_toast()
images.warm_thumbs()  # 화면을 다 보낸 뒤에 음식 썸네일을 미리 만들어 둔다 (배달 화면을 처음 열 때 멈칫하지 않게)

# 한 번만 보여 주는 연출 표시(방금 주문한 음식, 방금 보낸 배달, 방금 답한 친구 요청)는 그린 뒤 지운다
for _key in ("just_added_id", "just_gifted", "just_answered"):
    st.session_state.pop(_key, None)
