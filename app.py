"""MUKBOGI Streamlit 프로토타입 진입 파일.

실행: streamlit run app.py
"""

import streamlit as st

from core import home, onboarding, splash, style

st.set_page_config(page_title="MUKBOGI", layout="centered")
style.inject()

if splash.should_show():
    splash.render()
elif "profile" not in st.session_state:
    onboarding.render()
else:
    home.render()

style.render_toast()
