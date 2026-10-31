"""화면 공통 스타일. 값은 DESIGN.md를 따른다.

- 색: primary-dark #1E2530(1차 버튼·텍스트), signature-cyan #00D4EA(브랜드 표면),
  white, neutral-50 #F4F5FB, neutral-200 #D6D9E1, neutral-600 #515160
- 글꼴: Pretendard 스택 (fonts.font-sans)
- 좌우 여백: 16px (spacing.screen-horizontal)
- 섹션 헤더: 18px / 700 (typography.section-header)
버튼·체크박스 색은 .streamlit/config.toml 테마로 지정한다.
"""

import streamlit as st

_CSS = """
<style>
@import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.min.css');

html, body, [class*="st-"], button, input {
  font-family: "Pretendard Variable", Pretendard, -apple-system, "Apple SD Gothic Neo", system-ui, sans-serif;
}

/* 휴대폰 폭에 맞춘 한 열 레이아웃, 좌우 16px */
.block-container {
  max-width: 480px;
  padding-left: 16px;
  padding-right: 16px;
}

.mk-wordmark { font-size: 20px; font-weight: 800; letter-spacing: -0.01em; color: #1E2530; }
.mk-step { font-size: 13px; font-weight: 600; color: #515160; }
.mk-section { font-size: 18px; font-weight: 700; color: #1E2530; margin: 0; }
.mk-help { font-size: 14px; color: #515160; margin-top: 4px; }
.mk-kcal { font-size: 15px; font-weight: 700; color: #1E2530; }
.mk-badge {
  display: inline-block; font-size: 12px; font-weight: 700; color: #1E2530;
  background: #00D4EA; border-radius: 999px; padding: 2px 10px;
}

/* 버튼 터치 영역 44px 이상 */
.stButton button { min-height: 48px; }

:focus-visible { outline: 3px solid #00D4EA !important; outline-offset: 2px; }

@media (prefers-reduced-motion: reduce) {
  * { animation: none !important; transition: none !important; }
}
</style>
"""


def inject() -> None:
    st.markdown(_CSS, unsafe_allow_html=True)


def wordmark() -> None:
    st.markdown('<p class="mk-wordmark">MUKBOGI</p>', unsafe_allow_html=True)
