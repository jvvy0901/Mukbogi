"""스플래시 화면 (앱을 처음 열 때 잠깐 보이는 화면).

남색(#1E2530) 바탕 가운데에 흰 MUKBOGI 텍스트 로고만 둔다.

- 프로필이 없는 새 세션에서 한 번만 보인다 (실제 앱의 "앱 실행 직후"를 흉내).
- SPLASH_SECONDS 뒤 저절로 넘어가고, 화면 아무 곳이나 누르면 바로 넘어간다.
"""

import time

import streamlit as st

from core.style import html

SPLASH_SECONDS = 1.8


def should_show() -> bool:
    ss = st.session_state
    return not ss.get("splash_seen") and "profile" not in ss


def _done() -> None:
    st.session_state.splash_seen = True


def render() -> None:
    st.session_state.setdefault("splash_at", time.time())

    with st.container(key="sheet_splash"):
        html('<div class="mk-splash-logo mk-wordmark" role="img" aria-label="MUKBOGI">MUKBOGI</div>')
        # 화면 전체를 덮는 투명 버튼: 누르면 바로 넘어간다 (스크린리더에는 "시작하기"로 읽힌다)
        st.button("시작하기", key="splash_skip", on_click=_done)

    @st.fragment(run_every=0.4)
    def _tick() -> None:
        if time.time() - st.session_state.get("splash_at", 0) >= SPLASH_SECONDS:
            _done()
            st.rerun()

    _tick()
