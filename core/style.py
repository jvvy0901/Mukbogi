"""화면 공통 스타일 (iOS 앱처럼 보이도록).

색·글꼴·좌우 여백은 DESIGN.md (A) 정확값을 따르고,
DESIGN.md에 없던 값은 DESIGN.md "MUKBOGI 적용값" 절에 기록해 두었다.

게슈탈트 원리로 정한 배치 규칙
- 근접: 간격 단계 8 / 12 / 28px. 한 덩어리 안은 좁게(8~12), 덩어리 사이는 넓게(28).
- 유사: "선택됨"은 어디서나 같은 모양 — 흰 카드 + 남색 테두리 + 남색 원 안의 흰 체크.
        청록은 선택 표시에 쓰지 않고 포커스 표시에만 쓴다.
- 공통 영역: 선택 표시는 사진이 아니라 카드 오른쪽 위/오른쪽에 붙인다. 관련 정보는 한 카드 안에 묶는다.
- 연속성: 상단 내비게이션 줄(이전 · 진행 표시 · 단계)은 모든 단계에서 같은 높이·위치에 둔다.
- 전경/배경: 고르지 않은 카드는 연회색, 고른 카드는 흰색 + 테두리로 떠오르게 한다.

탭 영역 패턴: key가 "tap_"으로 시작하는 컨테이너는 안의 st.button을 투명하게 카드 전체에
덮어서, 카드 어디를 눌러도 버튼이 눌리게 한다 (버튼 라벨은 스크린리더가 읽는다).
"""

import streamlit as st

_CHECK_WHITE = (
    "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'>"
    "<path d='M5 12.5l4.5 4.5L19 7.5' fill='none' stroke='white' stroke-width='3' "
    "stroke-linecap='round' stroke-linejoin='round'/></svg>"
)

_CSS = """
<style>
@import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.min.css');

:root {
  --ink: #1E2530;        /* colors.primary-dark */
  --cyan: #00D4EA;       /* colors.signature-cyan */
  --soft: #F4F5FB;       /* colors.neutral-50 */
  --line: #D6D9E1;       /* colors.neutral-200 */
  --line-2: #C0C4CD;     /* colors.neutral-300 */
  --sub: #515160;        /* colors.neutral-600 */
  --gap-in: 10px;        /* 같은 묶음 안 */
  --gap-out: 28px;       /* 묶음과 묶음 사이 */
}

html, body, .stApp, .stApp *:not([data-testid="stIconMaterial"]) {
  font-family: "Pretendard Variable", Pretendard, -apple-system, "Apple SD Gothic Neo", system-ui, sans-serif;
  -webkit-font-smoothing: antialiased;
}
.stApp { background: #FFFFFF; color: var(--ink); }

/* Streamlit 기본 화면 요소 숨기기 */
header[data-testid="stHeader"], [data-testid="stToolbar"], [data-testid="stDecoration"],
[data-testid="stStatusWidget"], #MainMenu, footer { display: none !important; }

/* 폰 폭 한 열, 좌우 16px (spacing.screen-horizontal), 하단 고정 버튼 자리 확보 */
[data-testid="stMainBlockContainer"], .block-container {
  max-width: 430px !important;
  padding: 4px 16px 168px !important;
}
[data-testid="stVerticalBlock"] { gap: var(--gap-in); }
/* Streamlit 텍스트 요소의 기본 음수 여백을 없애 카드·문단이 겹치지 않게 한다 */
.stMarkdown, [data-testid="stMarkdownContainer"] { margin: 0 !important; }
.stMarkdown p { margin: 0; }

/* ---------- 상단 내비게이션 줄: [이전] [진행 표시] [1/3] ---------- */
.st-key-nav_row { min-height: 44px; flex-wrap: nowrap !important; gap: 8px !important; }
.st-key-nav_row > [data-testid="stElementContainer"] { width: auto !important; flex: none; }
.st-key-nav_row > [data-testid="stElementContainer"]:has(.mk-progress) { flex: 1 1 auto; min-width: 0; }
.mk-nav-slot { width: 44px; height: 44px; }
.mk-progress { display: flex; gap: 6px; }
.mk-progress span { flex: 1; height: 4px; border-radius: 2px; background: var(--line); }
.mk-progress span.on { background: var(--ink); }
.mk-step { width: 44px; text-align: right; font-size: 13px; font-weight: 600; color: var(--sub); }
/* 이전 버튼: 44×44 아이콘. 글자 "이전"은 크기 0으로 숨겨 스크린리더만 읽게 한다 */
.st-key-nav_row .stButton button { width: 44px; height: 44px; min-height: 44px; padding: 0; justify-content: flex-start; }
.st-key-nav_row .stButton button p { font-size: 0 !important; }
.st-key-nav_row .stButton button p::before { content: "‹"; font-size: 34px; font-weight: 400; line-height: 1; color: var(--ink); }

/* ---------- 머리말 (제목 + 설명) ---------- */
.mk-header { padding: 8px 0 calc(var(--gap-out) - var(--gap-in)); }
.mk-title { font-size: 26px; font-weight: 700; line-height: 1.3; letter-spacing: -0.02em; color: var(--ink); }
.mk-sub { font-size: 15px; line-height: 1.5; color: var(--sub); margin-top: 8px; }
.mk-wordmark { font-size: 17px; font-weight: 800; letter-spacing: 0.02em; color: var(--ink); line-height: 44px; }
.mk-section { font-size: 18px; font-weight: 700; color: var(--ink); padding-top: calc(var(--gap-out) - var(--gap-in)); }  /* typography.section-header */
.mk-count { font-size: 13px; font-weight: 600; color: var(--sub); }

/* ---------- 버튼 ---------- */
.stButton button p { font-size: inherit; font-weight: inherit; }
[data-testid="stBaseButton-primary"] {
  min-height: 52px; border-radius: 14px; border: 0;
  background: var(--ink); color: #FFFFFF; font-size: 17px; font-weight: 700;
}
[data-testid="stBaseButton-primary"]:hover { background: var(--ink); color: #FFFFFF; opacity: .92; }
[data-testid="stBaseButton-primary"]:disabled { background: var(--line); color: var(--sub); opacity: 1; }
[data-testid="stBaseButton-tertiary"] {
  min-height: 44px; padding: 0 4px; color: var(--ink); font-size: 16px; font-weight: 600;
}
[data-testid="stBaseButton-tertiary"]:hover { color: var(--ink); }

/* ---------- 탭 영역 (카드 전체를 덮는 투명 버튼) ---------- */
[class*="st-key-tap_"] { position: relative; gap: 0 !important; }
/* Streamlit이 버튼 감싼 요소에 내용 폭(fit-content)을 주므로 폭·높이를 카드 전체로 강제한다 */
[class*="st-key-tap_"] > [data-testid="stElementContainer"]:has(.stButton) {
  position: absolute; inset: 0; z-index: 2; margin: 0;
  width: 100% !important; height: 100% !important; max-width: none !important;
}
[class*="st-key-tap_"] .stButton,
[class*="st-key-tap_"] .stButton button { width: 100%; height: 100%; min-height: 0; }
[class*="st-key-tap_"] .stButton button { opacity: 0; cursor: pointer; }
[class*="st-key-tap_"]:has(button:focus-visible) .mk-card { outline: 3px solid var(--cyan); outline-offset: 2px; }

/* ---------- 카드 공통 + 선택 표시 (유사성: 어디서나 같은 모양) ---------- */
.mk-card { position: relative; border-radius: 16px; background: var(--soft); border: 2px solid transparent; }
.mk-card.sel { background: #FFFFFF; border-color: var(--ink); }
.mk-pick {
  flex: none; width: 24px; height: 24px; border-radius: 50%;
  border: 2px solid var(--line-2); background: #FFFFFF;
}
.mk-card.sel .mk-pick { border-color: var(--ink); background: var(--ink) url("CHECK_WHITE") center / 15px no-repeat; }

/* ---------- 1단계: 유형 카드 (한 줄 = 사진 · 정보 · 선택 표시) ---------- */
.mk-type { display: flex; align-items: center; gap: 14px; padding: 16px; }
.mk-thumbs { display: flex; flex: none; }
.mk-thumbs img { width: 44px; height: 44px; border-radius: 50%; object-fit: cover; border: 2px solid var(--soft); background: #FFFFFF; }
.mk-card.sel .mk-thumbs img { border-color: #FFFFFF; }
.mk-thumbs img + img { margin-left: -14px; }
.mk-type-text { flex: 1; min-width: 0; }
.mk-type-name { font-size: 17px; font-weight: 700; line-height: 1.3; }
.mk-type-goal { font-size: 14px; color: var(--sub); line-height: 1.4; margin-top: 4px; }
.mk-type-goal b { font-size: 15px; font-weight: 700; color: var(--ink); }
.mk-type-ex { font-size: 13px; color: var(--sub); line-height: 1.4; }

/* ---------- 2단계: 음식 3열 그리드 ---------- */
.st-key-grid_food {
  display: grid !important; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: var(--gap-in) !important;
}
.mk-food { display: flex; flex-direction: column; align-items: center; padding: 16px 6px 12px; text-align: center; }
.mk-food .mk-pick { position: absolute; top: 6px; right: 6px; width: 22px; height: 22px; }
.mk-food img { width: 60px; height: 60px; border-radius: 50%; object-fit: cover; background: #FFFFFF; }
.mk-food-name { font-size: 15px; font-weight: 600; margin-top: 10px; line-height: 1.3; }
.mk-food-kcal { font-size: 13px; color: var(--sub); line-height: 1.4; }

/* ---------- 3단계: 체중 입력 (라벨 · 입력칸 · 도움말을 한 묶음으로) ---------- */
.st-key-ob_weight label p { font-size: 15px; font-weight: 600; color: var(--ink); }
.st-key-ob_weight [data-testid="stNumberInputContainer"] {
  position: relative; border-radius: 14px; background: var(--soft);
  border: 2px solid transparent; min-height: 56px;
}
.st-key-ob_weight [data-testid="stNumberInputContainer"]:focus-within { border-color: var(--ink); background: #FFFFFF; }
.st-key-ob_weight [data-testid="stNumberInputContainer"]::after {
  content: "kg"; position: absolute; right: 16px; top: 50%; transform: translateY(-50%);
  font-size: 17px; font-weight: 600; color: var(--sub); pointer-events: none;
}
.st-key-ob_weight input:focus-visible { outline: none !important; }  /* 포커스는 입력칸 테두리로 표시 */
.st-key-ob_weight input { font-size: 22px; font-weight: 700; color: var(--ink); background: transparent; padding-right: 48px; }
.st-key-ob_weight [data-testid="stNumberInputStepDown"],
.st-key-ob_weight [data-testid="stNumberInputStepUp"],
.st-key-ob_weight [data-testid="InputInstructions"] { display: none; }
.mk-note { font-size: 13px; color: var(--sub); line-height: 1.5; margin-top: -4px; }
.mk-error { font-size: 13px; font-weight: 600; color: #B42318; margin-top: -4px; }

/* ---------- 하단 고정 버튼 영역 ---------- */
.st-key-bar_footer {
  position: fixed; left: 50%; bottom: 0; transform: translateX(-50%);
  width: min(100%, 430px); z-index: 100; gap: 6px !important;
  padding: 10px 16px calc(16px + env(safe-area-inset-bottom));
  background: #FFFFFF; border-top: 1px solid var(--soft);
}
.mk-hint { font-size: 13px; color: var(--sub); text-align: center; }

/* ---------- 완료 화면 ---------- */
.mk-summary { border-radius: 16px; background: var(--soft); padding: 4px 16px; }
.mk-row { display: flex; justify-content: space-between; gap: 12px; padding: 14px 0; font-size: 15px; }
.mk-row + .mk-row { border-top: 1px solid var(--line); }
.mk-row span:first-child { color: var(--sub); }
.mk-row span:last-child { font-weight: 600; text-align: right; }
.mk-favs { display: flex; flex-wrap: wrap; gap: 12px; border-radius: 16px; background: var(--soft); padding: 16px; }
.mk-fav { width: 56px; text-align: center; font-size: 12px; color: var(--sub); }
.mk-fav img { width: 48px; height: 48px; border-radius: 50%; object-fit: cover; display: block; margin: 0 auto 6px; background: #FFFFFF; }

:focus-visible { outline: 3px solid var(--cyan) !important; outline-offset: 2px; }
@media (prefers-reduced-motion: reduce) {
  * { animation: none !important; transition: none !important; }
}
</style>
""".replace("CHECK_WHITE", _CHECK_WHITE)


def inject() -> None:
    st.markdown(_CSS, unsafe_allow_html=True)


def html(markup: str) -> None:
    """한 줄 HTML 조각을 그린다. (들여쓰기가 있으면 마크다운 코드 블록이 되므로 줄을 합친다)"""
    st.markdown("".join(line.strip() for line in markup.splitlines()), unsafe_allow_html=True)
