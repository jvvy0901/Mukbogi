"""MUKBOGI Streamlit 프로토타입 진입 파일.

실행: streamlit run app.py
"""

import streamlit as st

from core import onboarding, style

st.set_page_config(page_title="MUKBOGI", layout="centered")
style.inject()
style.wordmark()

if "profile" not in st.session_state:
    onboarding.render()
else:
    onboarding.render_done()
