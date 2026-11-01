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

from html import escape

import streamlit as st

_CHECK_WHITE = (
    "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'>"
    "<path d='M5 12.5l4.5 4.5L19 7.5' fill='none' stroke='white' stroke-width='3' "
    "stroke-linecap='round' stroke-linejoin='round'/></svg>"
)

_CSS = """
<style>
@import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.min.css');
/* 로고 전용 글꼴: Pilcrow Rounded Heavy(900), Fontshare */
@import url('https://api.fontshare.com/v2/css?f[]=pilcrow-rounded@900&display=swap');

:root {
  --ink: #1E2530;        /* colors.primary-dark */
  --cyan: #00D4EA;       /* colors.signature-cyan */
  --soft: #F4F5FB;       /* colors.neutral-50 */
  --line: #D6D9E1;       /* colors.neutral-200 */
  --line-2: #C0C4CD;     /* colors.neutral-300 */
  --sub: #515160;        /* colors.neutral-600 */
  --gap-in: 10px;        /* 같은 묶음 안 */
  /* 움직임 곡선 (ui-animation 스킬 기준값) */
  --ease-press: cubic-bezier(.25, .46, .45, .94);  /* 누름에서 돌아올 때 */
  --ease-enter: cubic-bezier(.22, 1, .36, 1);      /* 나타남 */
  --ease-move: cubic-bezier(.25, 1, .5, 1);        /* 옆으로 이동·채움 */
  --ease-pop: cubic-bezier(.34, 1.56, .64, 1);     /* 살짝 튀는 선택·축하 (드물게) */
  --gap-out: 28px;       /* 묶음과 묶음 사이 */
  --safe-bottom: max(env(safe-area-inset-bottom), var(--sim-safe-bottom, 0px));  /* 홈 인디케이터 영역 */
  --safe-top: max(env(safe-area-inset-top), var(--sim-safe-top, 0px));  /* 상태 표시줄 영역 */
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
  padding: calc(4px + var(--safe-top)) 16px 168px !important;
}
[data-testid="stVerticalBlock"] { gap: var(--gap-in); }
/* Streamlit 텍스트 요소의 기본 음수 여백을 없애 카드·문단이 겹치지 않게 한다 */
.stMarkdown, [data-testid="stMarkdownContainer"] { margin: 0 !important; }
.stMarkdown p { margin: 0; }

/* ---------- 상단 내비게이션 줄: [이전] [진행 표시] [1/3] ---------- */
.st-key-nav_row { min-height: 44px; flex-wrap: nowrap !important; gap: 8px !important; }
.st-key-nav_row > [data-testid="stElementContainer"] { width: auto !important; flex: none; }
.st-key-nav_row > [data-testid="stElementContainer"]:has(.mk-progress),
.st-key-nav_row > [data-testid="stElementContainer"]:has(.mk-nav-title) { flex: 1 1 auto; min-width: 0; }
.mk-nav-title { text-align: center; font-size: 17px; font-weight: 700; color: var(--ink); }
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
/* 로고: Pilcrow Rounded Heavy(900) + 남색(#1E2530). 전체 글꼴(Pretendard) 규칙보다 우선한다 */
.stApp .mk-wordmark {
  font-family: "Pilcrow Rounded", "Pretendard Variable", Pretendard, -apple-system, sans-serif !important;
  font-size: 22px; font-weight: 900; letter-spacing: 0.01em; color: var(--ink); line-height: 44px;
}
.mk-section { font-size: 18px; font-weight: 700; color: var(--ink); padding-top: calc(var(--gap-out) - var(--gap-in)); }  /* typography.section-header */
.mk-count { font-size: 13px; font-weight: 600; color: var(--sub); }

/* ---------- 버튼 ---------- */
.stButton button p { font-size: inherit; font-weight: inherit; }
[data-testid="stBaseButton-primary"] {
  min-height: 52px; border-radius: 14px; border: 0;
  background: var(--ink); color: #FFFFFF; font-size: 17px; font-weight: 700;
}
@media (hover: hover) and (pointer: fine) {
  [data-testid="stBaseButton-primary"]:hover { background: var(--ink); color: #FFFFFF; opacity: .92; }
}
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
.mk-card.sel .mk-pick { border-color: var(--ink); background: var(--ink) url("CHECK_WHITE") center / 15px no-repeat; animation: mk-check .22s var(--ease-pop); }
@keyframes mk-check { from { transform: scale(.6); } }

/* ---------- 1단계: 유형 카드 (한 줄 = 사진 · 정보 · 선택 표시) ---------- */
.mk-type { display: flex; align-items: center; gap: 14px; padding: 16px; }
.mk-thumbs { display: flex; flex: none; }
.mk-thumbs img { width: 46px; height: 46px; object-fit: contain; filter: drop-shadow(0 2px 3px rgba(30, 37, 48, .14)); }
.mk-thumbs img + img { margin-left: -8px; }
.mk-type-text { flex: 1; min-width: 0; }
.mk-type-name { font-size: 17px; font-weight: 700; line-height: 1.3; }
.mk-type-goal { font-size: 14px; color: var(--sub); line-height: 1.4; margin-top: 4px; }
.mk-type-goal b { font-size: 15px; font-weight: 700; color: var(--ink); }
.mk-type-ex { font-size: 13px; color: var(--sub); line-height: 1.4; }

/* ---------- 2단계: 음식 3열 그리드 ---------- */
[class*="st-key-grid_"] {
  display: grid !important; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: var(--gap-in) !important;
}
.mk-food { display: flex; flex-direction: column; align-items: center; padding: 16px 6px 12px; text-align: center; }
.mk-food .mk-pick { position: absolute; top: 6px; right: 6px; width: 22px; height: 22px; }
.mk-food img { width: 64px; height: 64px; object-fit: contain; filter: drop-shadow(0 3px 4px rgba(30, 37, 48, .14)); }
.mk-food-name { font-size: 15px; font-weight: 600; margin-top: 10px; line-height: 1.3; }
.mk-food-kcal { font-size: 13px; color: var(--sub); line-height: 1.4; }

/* ---------- 3단계: 몸무게 입력 (라벨 · 입력칸 · 도움말을 한 묶음으로) ---------- */
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
/* 안내 문구는 입력한 숫자보다 작고 가볍게 */
.st-key-ob_weight input::placeholder { font-size: 16px; font-weight: 400; color: var(--sub); opacity: 1; }
.st-key-ob_weight [data-testid="stNumberInputStepDown"],
.st-key-ob_weight [data-testid="stNumberInputStepUp"],
.st-key-ob_weight [data-testid="InputInstructions"] { display: none; }
.mk-note { font-size: 13px; color: var(--sub); line-height: 1.5; margin-top: -4px; }
.mk-error { font-size: 13px; font-weight: 600; color: #B42318; margin-top: -4px; }

/* ---------- 하단 고정 버튼 영역 ---------- */
.st-key-bar_footer {
  position: fixed; left: 50%; bottom: 0; transform: translateX(-50%);
  width: min(100%, 430px); z-index: 100; gap: 6px !important;
  padding: 10px 16px calc(16px + var(--safe-bottom));
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


/* ---------- 보조 버튼 (멈추기, 냉장고 보기, 움직임 흉내 버튼) ---------- */
[data-testid="stBaseButton-secondary"] {
  min-height: 44px; border-radius: 12px; border: 1.5px solid var(--line);
  background: #FFFFFF; color: var(--ink); font-size: 15px; font-weight: 600;
}
@media (hover: hover) and (pointer: fine) {
  [data-testid="stBaseButton-secondary"]:hover { border-color: var(--ink); color: var(--ink); background: #FFFFFF; }
}
.st-key-bar_footer [data-testid="stBaseButton-secondary"],
.st-key-sheet_done [data-testid="stBaseButton-secondary"] {
  min-height: 52px; border-radius: 14px; border: 2px solid var(--ink); font-size: 17px; font-weight: 700;
}

/* ---------- 하단 탭 ---------- */
.st-key-bar_tabs {
  position: fixed; left: 50%; bottom: 0; transform: translateX(-50%);
  width: min(100%, 430px); z-index: 110;
  display: grid !important; grid-template-columns: repeat(4, 1fr); gap: 0 !important;
  padding: 4px 8px calc(4px + var(--safe-bottom));
  background: #FFFFFF; border-top: 1px solid var(--line);
}
.st-key-bar_tabs > [data-testid="stElementContainer"] { width: 100% !important; }
.st-key-bar_tabs .stButton, .st-key-bar_tabs .stButton button { width: 100%; }
.st-key-bar_tabs .stButton button {
  min-height: 52px; padding: 4px 0; flex-direction: column; gap: 2px; color: var(--sub);
}
.st-key-bar_tabs .stButton button p { font-size: 11px !important; font-weight: 500; letter-spacing: -0.01em; }
.st-key-bar_tabs .stButton button::before {
  content: ""; width: 24px; height: 24px; background: currentColor;
  -webkit-mask: var(--icon) center / contain no-repeat; mask: var(--icon) center / contain no-repeat;
}
.st-key-bar_tabs .stButton button:hover { text-decoration: none; }
/* 탭 아이콘: --icon = 선(다른 탭), --icon-on = 채움(현재 탭). 24×24, 선 1.8 · 둥근 끝 */
.st-key-tab_home { --icon: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'><path fill='none' stroke='black' stroke-width='1.8' stroke-linecap='round' stroke-linejoin='round' d='M4 10.3 12 4l8 6.3v8.7a1.5 1.5 0 0 1-1.5 1.5H15v-5.2a1 1 0 0 0-1-1h-4a1 1 0 0 0-1 1v5.2H5.5A1.5 1.5 0 0 1 4 19z'/></svg>"); --icon-on: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'><path fill='black' stroke='black' stroke-width='1.2' stroke-linejoin='round' fill-rule='evenodd' d='M11.4 3.6a1 1 0 0 1 1.2 0l7.7 6.05a1.6 1.6 0 0 1 .6 1.25V19a1.8 1.8 0 0 1-1.8 1.8H15.2v-5.3a1.2 1.2 0 0 0-1.2-1.2h-4a1.2 1.2 0 0 0-1.2 1.2v5.3H5.1A1.8 1.8 0 0 1 3.3 19v-8.1a1.6 1.6 0 0 1 .6-1.25z'/></svg>"); }
.st-key-tab_fridge { --icon: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'><rect fill='none' stroke='black' stroke-width='1.8' stroke-linecap='round' stroke-linejoin='round' x='5.5' y='2.75' width='13' height='18.5' rx='2.75'/><path fill='none' stroke='black' stroke-width='1.8' stroke-linecap='round' stroke-linejoin='round' d='M5.5 10h13M8.75 5.75v1.75M8.75 12.75v3.5'/></svg>"); --icon-on: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'><path fill='black' fill-rule='evenodd' d='M8.25 2.4h7.5a3.1 3.1 0 0 1 3.1 3.1v13a3.1 3.1 0 0 1-3.1 3.1h-7.5a3.1 3.1 0 0 1-3.1-3.1v-13a3.1 3.1 0 0 1 3.1-3.1zM5.15 9.2h13.7v1.7H5.15z M7.85 5h1.9v3.1h-1.9z M7.85 12.4h1.9v4.4h-1.9z'/></svg>"); }
.st-key-tab_community { --icon: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'><circle fill='none' stroke='black' stroke-width='1.8' stroke-linecap='round' stroke-linejoin='round' cx='9' cy='8.25' r='3.25'/><path fill='none' stroke='black' stroke-width='1.8' stroke-linecap='round' stroke-linejoin='round' d='M3.25 19.5c.45-3.3 2.9-5.4 5.75-5.4s5.3 2.1 5.75 5.4'/><circle fill='none' stroke='black' stroke-width='1.8' stroke-linecap='round' stroke-linejoin='round' cx='16.75' cy='9' r='2.5'/><path fill='none' stroke='black' stroke-width='1.8' stroke-linecap='round' stroke-linejoin='round' d='M16.9 14.1c2.3.2 3.9 2 4.3 4.6'/></svg>"); --icon-on: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'><circle fill='black' stroke='black' stroke-width='1.2' stroke-linejoin='round' fill-rule='evenodd' cx='9' cy='8.25' r='3.6'/><path fill='black' stroke='black' stroke-width='1.2' stroke-linejoin='round' fill-rule='evenodd' d='M2.6 19.6c.4-3.7 3.1-6.2 6.4-6.2s6 2.5 6.4 6.2a.9.9 0 0 1-.9 1H3.5a.9.9 0 0 1-.9-1z'/><circle fill='black' stroke='black' stroke-width='1.2' stroke-linejoin='round' fill-rule='evenodd' cx='16.75' cy='9' r='2.85'/><path fill='black' stroke='black' stroke-width='1.2' stroke-linejoin='round' fill-rule='evenodd' d='M16.4 13.5c3 .1 5.2 2.3 5.4 5.3a.9.9 0 0 1-.9.95h-3.4c0-2.45-.4-4.5-1.1-6.25z'/></svg>"); }
.st-key-tab_my { --icon: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'><circle fill='none' stroke='black' stroke-width='1.8' stroke-linecap='round' stroke-linejoin='round' cx='12' cy='8' r='3.75'/><path fill='none' stroke='black' stroke-width='1.8' stroke-linecap='round' stroke-linejoin='round' d='M4.75 20c.7-3.7 3.6-6.1 7.25-6.1s6.55 2.4 7.25 6.1'/></svg>"); --icon-on: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'><circle fill='black' stroke='black' stroke-width='1.2' stroke-linejoin='round' fill-rule='evenodd' cx='12' cy='8' r='4.1'/><path fill='black' stroke='black' stroke-width='1.2' stroke-linejoin='round' fill-rule='evenodd' d='M4.2 19.8c.7-4 3.9-6.5 7.8-6.5s7.1 2.5 7.8 6.5a1 1 0 0 1-1 1.2H5.2a1 1 0 0 1-1-1.2z'/></svg>"); }
/* 탭이 있는 화면: 주요 버튼은 탭 바로 위에 붙인다 */
.stApp:has(.st-key-bar_tabs) .st-key-bar_footer { bottom: calc(61px + var(--safe-bottom)); border-top: 0; padding-bottom: 10px; }
.stApp:has(.st-key-bar_tabs) [data-testid="stMainBlockContainer"] { padding-bottom: calc(220px + var(--safe-bottom)) !important; }

/* ---------- 홈: 상단 줄 ---------- */
.mk-topbar { display: flex; justify-content: space-between; align-items: center; min-height: 44px; }
/* 스크롤해도 상단 줄이 화면 맨 위에 붙어 있게 한다 */
[data-testid="stElementContainer"]:has(.mk-topbar) {
  position: sticky; top: var(--safe-top); z-index: 90; background: #FFFFFF;
  /* 상태 표시줄 뒤와 위쪽 틈도 흰색으로 덮는다 (상단 줄 높이 44px < 상태 표시줄 47px라 두 겹) */
  box-shadow: 0 calc(-1 * var(--safe-top)) 0 #FFFFFF, 0 -12px 0 #FFFFFF;
}
.mk-today { font-size: 13px; font-weight: 600; color: var(--sub); background: var(--soft); border-radius: 999px; padding: 6px 12px; }
.mk-today b { color: var(--ink); }

/* ---------- 홈: 빈 상태 (문구 + 버튼을 한 카드로) ---------- */
.st-key-empty_box {
  background: var(--soft); border-radius: 16px; padding: 32px 16px 16px; gap: 20px !important; text-align: center;
  margin-top: calc(var(--gap-out) - var(--gap-in));
}
.mk-empty-title { font-size: 22px; font-weight: 700; color: var(--ink); }

/* ---------- 홈: 소화 중인 음식 카드 ---------- */
.mk-meal { background: var(--soft); border-radius: 16px; padding: 16px; margin-top: calc(var(--gap-out) - var(--gap-in) - 8px); }
.mk-meal-top { display: flex; justify-content: space-between; align-items: center; }
.mk-chip { display: inline-flex; align-items: center; gap: 6px; font-size: 13px; font-weight: 600; background: #FFFFFF; border-radius: 999px; padding: 5px 10px; }
.mk-chip i { width: 8px; height: 8px; border-radius: 50%; background: var(--line-2); }
.mk-chip.on i { background: var(--cyan); animation: mk-pulse 1.6s ease-in-out infinite; }
@keyframes mk-pulse { 50% { transform: scale(1.5); opacity: .5; } }
.mk-bites-label { font-size: 13px; font-weight: 600; color: var(--sub); }
/* 소화 중인 음식: 틀 없이 음식만 떠 있고 크기는 그대로. 먹은 입만큼 이빨 자국으로 베어져 있다.
   바닥 그림자는 남은 양(--r)만큼 작아진다. 측정 중엔 위아래로 살짝 떠다닌다 */
.mk-hero { position: relative; height: 216px; display: grid; place-items: center; margin-top: 4px; }
.mk-hero::after {
  content: ""; position: absolute; bottom: 10px; left: 50%; width: 132px; height: 16px;
  transform: translateX(-50%) scale(calc(.35 + .65 * var(--r)));
  border-radius: 50%; background: rgba(30, 37, 48, .12); filter: blur(6px); transition: transform .4s ease;
}
.mk-float { position: relative; z-index: 1; }
.mk-hero.on .mk-float { animation: mk-float 2.8s ease-in-out infinite; }
@keyframes mk-float { 50% { transform: translateY(-6px); } }
.mk-plate { position: relative; width: 200px; height: 200px; }
.mk-plate img {
  position: absolute; inset: 0; width: 100%; height: 100%; object-fit: contain;
  filter: drop-shadow(0 10px 12px rgba(30, 37, 48, .16));
}
/* 한 입 먹는 순간: 직전 모습이 흐려지며 새 자국이 드러나고, 음식이 "앙" 눌렸다 돌아오고, 부스러기가 튄다 */
.mk-bite-prev { animation: mk-bite-reveal .45s ease-out forwards; }
@keyframes mk-bite-reveal { 0%, 25% { opacity: 1; } 100% { opacity: 0; } }
.mk-plate.chomp { animation: mk-chomp .38s ease-out; }
@keyframes mk-chomp { 0% { transform: scale(1); } 35% { transform: scale(.94) rotate(-2deg); } 70% { transform: scale(1.02); } 100% { transform: scale(1); } }
.mk-crumb {
  position: absolute; z-index: 2; width: 7px; height: 7px; margin: -3.5px 0 0 -3.5px; border-radius: 50%;
  background: #E2B37A; opacity: 0; animation: mk-crumb .6s ease-out forwards;
}
.mk-crumb-0 { --dx: -26px; --dy: -18px; }
.mk-crumb-1 { --dx: 22px; --dy: -24px; width: 5px; height: 5px; }
.mk-crumb-2 { --dx: 30px; --dy: 6px; }
.mk-crumb-3 { --dx: -20px; --dy: 16px; width: 5px; height: 5px; }
.mk-crumb-4 { --dx: 4px; --dy: -32px; width: 4px; height: 4px; }
@keyframes mk-crumb {
  0% { opacity: 1; transform: translate(0, 0) scale(1); }
  100% { opacity: 0; transform: translate(var(--dx), calc(var(--dy) + 14px)) scale(.6); }
}
@media (prefers-reduced-motion: reduce) {
  /* 움직임 없이 새 자국만 바로 보여 준다 */
  .mk-bite-prev, .mk-crumb { display: none; }
}
.mk-meal-name { text-align: center; font-size: 20px; font-weight: 700; margin-top: 12px; }
.mk-meal-kcal { text-align: center; font-size: 14px; color: var(--sub); }
.mk-meal-prog { text-align: center; font-size: 14px; color: var(--sub); margin-top: 12px; }
.mk-meal-prog b { color: var(--ink); }
.mk-stats { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin: 10px 0 0; }
.mk-stat { background: #FFFFFF; border-radius: 12px; padding: 10px 12px; }
.mk-stat dt { font-size: 12px; color: var(--sub); }
.mk-stat dd { font-size: 22px; font-weight: 700; margin: 2px 0 0; font-variant-numeric: tabular-nums; }
.mk-stat dd small { font-size: 13px; font-weight: 600; margin-left: 2px; }
.mk-hint-inline { font-size: 13px; color: var(--sub); text-align: center; }

/* ---------- 홈: 움직임 흉내 내기 (프로토타입 전용 — 점선 테두리로 실제 UI와 구분) ---------- */
.st-key-sim_box { border: 1.5px dashed var(--line-2); border-radius: 16px; padding: 12px; gap: 8px !important; }
.mk-sim-title { font-size: 13px; font-weight: 700; color: var(--sub); }
.st-key-sim_activity, .st-key-sim_dist { gap: 8px !important; flex-wrap: nowrap !important; }
.st-key-sim_activity > [data-testid="stElementContainer"],
.st-key-sim_dist > [data-testid="stElementContainer"] { flex: 1 1 0 !important; width: auto !important; min-width: 0; }
.st-key-sim_activity [data-testid="stBaseButton-primary"] { min-height: 44px; border-radius: 12px; font-size: 15px; }

/* ---------- 홈: 가로 스크롤 목록 (조리 중 · 친구) ---------- */
.st-key-row_queue {
  display: flex !important; flex-direction: row !important; flex-wrap: nowrap !important;
  overflow-x: auto; gap: var(--gap-in) !important; margin: 0 -16px; padding: 0 16px 4px; scrollbar-width: none;
}
.st-key-row_queue > * { flex: 0 0 88px !important; width: 88px !important; }
.mk-q {
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  min-height: 124px; padding: 12px 6px; border-radius: 14px; background: var(--soft); text-align: center;
}
.mk-q img { width: 56px; height: 56px; object-fit: contain; filter: drop-shadow(0 3px 4px rgba(30, 37, 48, .14)); }
.mk-q-name { font-size: 13px; font-weight: 600; margin-top: 8px; }
.mk-q-kcal { font-size: 12px; color: var(--sub); }
.mk-q-add { background: #FFFFFF; border: 1.5px dashed var(--line-2); font-size: 13px; font-weight: 600; gap: 4px; }
.mk-q-add span { font-size: 26px; font-weight: 400; line-height: 1; }

.mk-row-scroll { display: flex; gap: var(--gap-in); overflow-x: auto; margin: 0 -16px; padding: 0 16px 4px; scrollbar-width: none; }
.mk-row-scroll::-webkit-scrollbar, .st-key-row_queue::-webkit-scrollbar { display: none; }
.mk-fr { flex: 0 0 148px; background: var(--soft); border-radius: 14px; padding: 12px; }
.mk-fr-head { display: flex; align-items: center; gap: 8px; font-size: 14px; font-weight: 600; }
.mk-avatar { width: 32px; height: 32px; border-radius: 50%; object-fit: cover; flex: none; }
.mk-avatar-initial { display: grid; place-items: center; background: var(--ink); color: #FFFFFF; font-size: 13px; font-weight: 700; }
.mk-fr-food { display: flex; align-items: center; gap: 8px; font-size: 13px; margin-top: 12px; }
.mk-fr-food img { width: 40px; height: 40px; object-fit: contain; filter: drop-shadow(0 2px 3px rgba(30, 37, 48, .14)); }
.mk-bar { height: 6px; border-radius: 3px; background: var(--line); overflow: hidden; margin-top: 10px; }
.mk-bar i { display: block; height: 100%; background: var(--ink); border-radius: inherit; }
.mk-fr-pct { font-size: 12px; font-weight: 600; color: var(--sub); margin-top: 4px; }
.mk-fr-rest { font-size: 13px; color: var(--sub); margin-top: 12px; }

/* ---------- 냉장고: 날짜 묶음 (날짜 머리줄 + 그날 음식 카드를 한 덩어리로) ---------- */
.mk-fz-day { margin-top: calc(var(--gap-out) - var(--gap-in)); }
.mk-fz-day.first { margin-top: 0; }
.mk-fz-head { display: flex; justify-content: space-between; align-items: center; gap: 8px; padding: 0 2px 8px; }
.mk-fz-date { font-size: 15px; font-weight: 700; color: var(--ink); }
.mk-fz-total { display: flex; align-items: center; gap: 8px; font-size: 13px; color: var(--sub); white-space: nowrap; }
.mk-fz-sum { font-size: 13px; color: var(--sub); }
.mk-fz-sum b { font-size: 17px; font-weight: 700; color: var(--ink); margin-right: 2px; }
.mk-fz-goal { font-size: 12px; font-weight: 700; color: #FFFFFF; background: var(--ink); border-radius: 999px; padding: 3px 8px; }
.mk-fz-list { background: var(--soft); border-radius: 16px; padding: 4px 16px; }
.mk-fz-row { display: flex; align-items: center; gap: 12px; min-height: 64px; padding: 8px 0; }
.mk-fz-row + .mk-fz-row { border-top: 1px solid var(--line); }
.mk-fz-row img { width: 48px; height: 48px; flex: none; object-fit: contain; filter: drop-shadow(0 2px 3px rgba(30, 37, 48, .14)); }
.mk-fz-text { flex: 1; min-width: 0; }
.mk-fz-name { font-size: 16px; font-weight: 600; color: var(--ink); }
.mk-fz-meta { font-size: 13px; color: var(--sub); margin-top: 2px; font-variant-numeric: tabular-nums; }
.mk-fz-kcal { font-size: 15px; font-weight: 700; color: var(--ink); white-space: nowrap; }

/* ---------- 친구 카드 (누르면 배달 보내기) · 배달 표시 ---------- */
.st-key-row_friends {
  display: flex !important; flex-direction: row !important; flex-wrap: nowrap !important;
  overflow-x: auto; gap: var(--gap-in) !important; margin: 0 -16px; padding: 0 16px 4px; scrollbar-width: none;
}
.st-key-row_friends::-webkit-scrollbar { display: none; }
.st-key-row_friends > * { flex: 0 0 148px !important; width: 148px !important; }
.st-key-row_friends .mk-fr { height: 100%; }
.mk-fr.mk-card { border-width: 2px; }
.mk-fr-head { position: relative; }
.mk-fr-gift {
  margin-left: auto; font-size: 11px; font-weight: 700; color: #FFFFFF; background: var(--ink);
  border-radius: 999px; padding: 2px 7px; white-space: nowrap;
}
.mk-q-from { font-size: 11px; font-weight: 700; color: var(--ink); background: #FFFFFF; border-radius: 999px; padding: 2px 7px; margin-top: 6px; }

/* ---------- 배달 보내기: 받는 친구 ---------- */
.mk-gift-to { display: flex; align-items: center; gap: 12px; background: var(--soft); border-radius: 16px; padding: 12px 14px; }
.mk-avatar-lg { width: 44px; height: 44px; font-size: 16px; }
.mk-gift-name { font-size: 16px; font-weight: 700; color: var(--ink); }
.mk-gift-doing { font-size: 13px; color: var(--sub); margin-top: 2px; }
.mk-gift-to .mk-fr-gift { margin-left: auto; }

/* ---------- 세그먼트 컨트롤 (커뮤니티 탭 · 랭킹 범위) ---------- */
[class*="st-key-seg_"] {
  background: var(--soft); border-radius: 12px; padding: 3px; gap: 2px !important; flex-wrap: nowrap !important;
}
[class*="st-key-seg_"] > [data-testid="stElementContainer"] { flex: 1 1 0 !important; width: auto !important; min-width: 0; }
[class*="st-key-seg_"] .stButton, [class*="st-key-seg_"] .stButton button { width: 100%; }
[class*="st-key-seg_"] .stButton button {
  position: relative; min-height: 44px; border-radius: 10px; padding: 0 8px;
  color: var(--sub); font-size: 15px; font-weight: 600;
}
[class*="st-key-seg_"] .stButton button:hover { text-decoration: none; }
@media (hover: hover) and (pointer: fine) { [class*="st-key-seg_"] .stButton button:hover { color: var(--ink); } }
[class*="st-key-seg_"] .stButton button::after {  /* 친구 요청 수 배지 (내용은 화면에서 넣는다) */
  position: absolute; top: 7px; right: calc(50% - 34px); min-width: 16px; height: 16px; padding: 0 4px; border-radius: 999px;
  background: var(--ink); color: #FFFFFF; font-size: 10px; font-weight: 700; line-height: 16px; text-align: center;
}

/* ---------- 목록 카드 + 유저 한 줄 [정보 | 버튼] ---------- */
[class*="st-key-list_"] { background: var(--soft); border-radius: 16px; padding: 2px 14px; gap: 0 !important; }
[class*="st-key-list_"] > * + * { border-top: 1px solid var(--line); }
[class*="st-key-urow_"] { flex-wrap: nowrap !important; gap: 8px !important; min-height: 64px; padding: 8px 0; }
[class*="st-key-urow_"] > * { flex: none !important; width: auto !important; }
[class*="st-key-urow_"] > :first-child { flex: 1 1 auto !important; min-width: 0; }
[class*="st-key-urow_"] .stButton button { min-height: 44px; border-radius: 999px; padding: 0 14px; font-size: 14px; white-space: nowrap; }
[class*="st-key-urow_"] [data-testid="stBaseButton-primary"] { font-size: 14px; }
[class*="st-key-urow_"] [class*="st-key-tap_"] .stButton button { border-radius: 0; padding: 0; }
.mk-u { display: flex; align-items: center; gap: 10px; min-width: 0; }
.mk-u-text { min-width: 0; flex: 1; }
.mk-u-name { display: flex; align-items: center; gap: 6px; font-size: 15px; font-weight: 600; color: var(--ink); white-space: nowrap; }
.mk-u-id { font-size: 12px; font-weight: 500; color: var(--sub); overflow: hidden; text-overflow: ellipsis; }
.mk-u-sub { font-size: 13px; color: var(--sub); margin-top: 2px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.mk-u-sub b { color: var(--ink); font-weight: 700; }
/* 친구 상태 한 줄 (다른 목록 줄과 같은 두 줄 높이 유지):
   [음식 소화 중 — 남는 폭, 길면 …] [진행 막대 48px + % 34px — 고정 폭, 글자 칸 오른쪽 끝]
   → 막대·%가 모든 줄에서 같은 위치에 세로로 맞는다 */
.mk-doing { display: flex; align-items: center; gap: 8px; min-width: 0; margin-top: 2px; }
.mk-doing-food { flex: 1 1 auto; min-width: 0; font-size: 13px; color: var(--sub); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.mk-doing-prog { flex: none; display: flex; align-items: center; gap: 6px; }
.mk-doing-bar { flex: none; width: 48px; height: 5px; border-radius: 3px; background: var(--line); overflow: hidden; }
.mk-doing-bar i { display: block; height: 100%; background: var(--ink); border-radius: inherit; }
.mk-doing-pct { flex: none; width: 34px; text-align: right; font-size: 13px; font-weight: 700; color: var(--ink); font-variant-numeric: tabular-nums; }
@media (max-width: 359px) { .mk-doing-bar { display: none; } }  /* 좁은 화면(SE 등): 막대를 숨기고 음식 이름에 자리를 준다 (%는 같은 자리에 그대로) */
/* 화면에는 안 보이고 스크린리더만 읽는 글자 */
.mk-sr { position: absolute; width: 1px; height: 1px; overflow: hidden; clip: rect(0 0 0 0); white-space: nowrap; }
.mk-gift-to .mk-u-text, .mk-gift-to > div:nth-child(2) { flex: 1; min-width: 0; }
.mk-u-food { width: 44px; height: 44px; flex: none; object-fit: contain; filter: drop-shadow(0 2px 3px rgba(30, 37, 48, .14)); }
.mk-avatar-md { width: 40px; height: 40px; font-size: 14px; }
.mk-avatar-xl { width: 64px; height: 64px; font-size: 22px; }
.mk-section-n { margin-left: 6px; color: var(--sub); font-weight: 600; }
.mk-empty-line { font-size: 14px; color: var(--sub); background: var(--soft); border-radius: 16px; padding: 16px; }
.mk-note-box { font-size: 14px; color: var(--ink); background: var(--soft); border-radius: 12px; padding: 12px 14px; }

/* ---------- 친구 탭: 내 아이디 · 찾기 ---------- */
.mk-idcard { display: flex; justify-content: space-between; align-items: center; gap: 12px; background: var(--soft); border-radius: 16px; padding: 14px 16px; }
.mk-idcard-label { font-size: 12px; color: var(--sub); }
.mk-idcard-id { font-size: 18px; font-weight: 700; color: var(--ink); }
.mk-idcard-hint { font-size: 12px; color: var(--sub); text-align: right; line-height: 1.45; }
.st-key-cm_search_row { flex-wrap: nowrap !important; gap: 8px !important; }
.st-key-cm_search_row > :first-child { flex: 1 1 auto !important; width: auto !important; min-width: 0; }
.st-key-cm_search_row > :last-child { flex: none !important; width: auto !important; }
/* 검색창과 찾기 버튼: 높이 48px · 모서리 12px로 맞춘다 (보이는 틀은 stTextInputRootElement) */
.st-key-cm_search_row { align-items: stretch !important; }
.st-key-cm_search_row [data-testid="stBaseButton-primary"] { height: 48px; min-height: 48px; padding: 0 18px; border-radius: 12px; font-size: 15px; }
.st-key-cm_query [data-testid="stTextInputRootElement"] {
  height: 48px; min-height: 48px; border-radius: 12px; background: var(--soft); border: 2px solid transparent; box-sizing: border-box;
}
.st-key-cm_query [data-testid="stTextInputRootElement"]:focus-within { border-color: var(--ink); background: #FFFFFF; }
.st-key-cm_query input { height: 100%; min-height: 0; padding: 0 12px; font-size: 16px; background: transparent; }
.st-key-cm_query input:focus-visible { outline: none !important; }  /* 포커스는 틀 테두리로 표시 */
.st-key-cm_query [data-testid="InputInstructions"] { display: none; }

/* ---------- 랭킹 ---------- */
[class*="st-key-tap_rk_"] + [class*="st-key-tap_rk_"] { border-top: 1px solid var(--line); }
.mk-rk { display: flex; align-items: center; gap: 10px; min-height: 60px; padding: 8px 0; }
.mk-rk-n { width: 26px; flex: none; text-align: center; font-size: 15px; font-weight: 700; color: var(--sub); font-variant-numeric: tabular-nums; }
.mk-rk-n.top { color: var(--ink); font-size: 18px; }
.mk-rk-name { display: flex; align-items: center; gap: 6px; font-size: 15px; font-weight: 600; color: var(--ink); }
.mk-rk-kcal { margin-left: auto; font-size: 15px; font-weight: 700; color: var(--ink); font-variant-numeric: tabular-nums; }
.mk-rk-kcal small { font-size: 12px; font-weight: 500; color: var(--sub); margin-left: 2px; }
.mk-me-pill { font-size: 11px; font-weight: 700; color: #FFFFFF; background: var(--ink); border-radius: 999px; padding: 2px 7px; }
.mk-rk.me .mk-rk-name { font-weight: 700; }
.mk-myrank {
  display: flex; align-items: baseline; gap: 8px; background: var(--ink); color: #FFFFFF;
  border-radius: 14px; padding: 14px 16px; min-height: 52px;
}
.mk-myrank-label { font-size: 13px; opacity: .8; }
.mk-myrank-n { font-size: 20px; font-weight: 700; }
.mk-myrank-of { font-size: 13px; opacity: .8; }
.mk-myrank-kcal { margin-left: auto; font-size: 16px; font-weight: 700; font-variant-numeric: tabular-nums; }

/* ---------- 배달 탭 ---------- */
.mk-gift-stats { margin: 0; }
.mk-gift-stats .mk-stat { background: var(--soft); }

/* ---------- 다른 유저 화면 ---------- */
.mk-prof { display: flex; align-items: center; gap: 14px; padding: 8px 0 4px; }
.mk-prof-name { display: flex; align-items: center; gap: 8px; font-size: 22px; font-weight: 700; color: var(--ink); }
.mk-rel { font-size: 12px; font-weight: 700; color: var(--ink); background: var(--soft); border-radius: 999px; padding: 3px 9px; }
.st-key-user_actions, .st-key-confirm_btns { gap: 8px !important; flex-wrap: nowrap !important; }
.st-key-user_actions > *, .st-key-confirm_btns > * { flex: 1 1 0 !important; width: auto !important; }
.st-key-user_actions .stButton button, .st-key-confirm_btns .stButton button { width: 100%; min-height: 48px; border-radius: 14px; font-size: 15px; }
.st-key-confirm_box { background: var(--soft); border-radius: 16px; padding: 16px; gap: 10px !important; }
.mk-confirm-title { font-size: 16px; font-weight: 700; color: var(--ink); }
.mk-confirm-sub { font-size: 13px; color: var(--sub); line-height: 1.5; margin-top: 4px; }
.mk-lock { background: var(--soft); border-radius: 16px; padding: 28px 16px; text-align: center; }
.mk-lock-title { font-size: 17px; font-weight: 700; color: var(--ink); margin-bottom: 4px; }

/* ---------- 내정보 ---------- */
.mk-my-stats { grid-template-columns: repeat(3, 1fr); margin-top: 4px; }
.mk-my-stats .mk-stat { background: var(--soft); }
.mk-my-stats .mk-stat dd { font-size: 20px; }
.mk-my-note { font-size: 13px; color: var(--sub); line-height: 1.5; }
.mk-my-note b { color: var(--ink); }
.mk-plus-pill { font-size: 11px; font-weight: 700; color: var(--ink); background: var(--cyan); border-radius: 999px; padding: 3px 9px; }
/* 몸무게 입력칸은 온보딩 몸무게칸과 같은 모양 */
.st-key-my_weight [data-testid="stNumberInputContainer"] {
  position: relative; border-radius: 14px; background: var(--soft); border: 2px solid transparent; min-height: 56px;
}
.st-key-my_weight [data-testid="stNumberInputContainer"]:focus-within { border-color: var(--ink); background: #FFFFFF; }
.st-key-my_weight [data-testid="stNumberInputContainer"]::after {
  content: "kg"; position: absolute; right: 16px; top: 50%; transform: translateY(-50%);
  font-size: 17px; font-weight: 600; color: var(--sub); pointer-events: none;
}
.st-key-my_weight input { font-size: 20px; font-weight: 700; color: var(--ink); background: transparent; padding-right: 48px; }
.st-key-my_weight input:focus-visible { outline: none !important; }
.st-key-my_weight [data-testid="stNumberInputStepDown"], .st-key-my_weight [data-testid="stNumberInputStepUp"],
.st-key-my_weight [data-testid="InputInstructions"] { display: none; }
/* 플러스 카드 */
/* 근접: 머리말(배지+제목) 안 8px · 머리말→혜택 16px · 혜택→버튼 16px · 버튼→안내 6px (안내는 버튼에 붙는다)
   위계: 섹션 제목 18px > 카드 제목 17px > 혜택 15px > 안내 12px */
.st-key-plus_box { background: var(--soft); border-radius: 16px; padding: 20px 16px 16px; gap: 16px !important; }
.mk-plus-head { display: flex; flex-direction: column; align-items: flex-start; gap: 8px; }
.mk-plus-badge { font-size: 12px; font-weight: 700; color: var(--sub); background: #FFFFFF; border: 1px solid var(--line); border-radius: 999px; padding: 4px 10px; }
.mk-plus-badge.on { color: var(--ink); background: var(--cyan); border-color: var(--cyan); }
.mk-plus-title { font-size: 17px; font-weight: 700; color: var(--ink); line-height: 1.35; }
/* 혜택 목록: 흰 카드 안 [아이콘 원 | 이름 | (준비 중)] 줄 */
.mk-plus-perks { list-style: none; margin: 16px 0 0 !important; padding: 0 14px !important; background: #FFFFFF; border-radius: 14px; }
.mk-plus-perks li { margin: 0 !important; padding: 0 !important; display: flex; align-items: center; gap: 12px; min-height: 56px; font-size: 15px; font-weight: 600; color: var(--ink); }
.mk-plus-perks li + li { border-top: 1px solid var(--soft); }
.mk-perk-ico { flex: none; width: 36px; height: 36px; border-radius: 50%; background: var(--soft); position: relative; }
.mk-perk-ico::before {
  content: ""; position: absolute; inset: 8px; background: var(--ink);
  -webkit-mask: var(--icon) center / contain no-repeat; mask: var(--icon) center / contain no-repeat;
}
.mk-plus-perks .mk-soon { margin-left: auto; }
.mk-ico-noad { --icon: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'><rect x='3' y='5' width='18' height='14' rx='3'/><path d='M4 4l16 16'/></svg>"); }
.mk-ico-report { --icon: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'><rect x='4' y='3' width='16' height='18' rx='2'/><path d='M8 16v-3M12 16V9M16 16v-5'/></svg>"); }
.mk-soon { font-size: 11px; font-weight: 700; color: var(--sub); background: var(--soft); border-radius: 999px; padding: 3px 8px; white-space: nowrap; }
/* 플러스 시작·해지 버튼은 같은 크기 (높이 52px · 모서리 14px · 17px/700). 해지는 흰 채움 + 남색 2px 테두리 */
.st-key-plus_box .stButton button { height: 52px; min-height: 52px; border-radius: 14px; font-size: 17px; font-weight: 700; box-sizing: border-box; }
.st-key-plus_box [data-testid="stBaseButton-secondary"] { border: 2px solid var(--ink); background: #FFFFFF; color: var(--ink); }
.mk-plus-note { font-size: 12px; color: var(--sub); text-align: center; margin-top: -10px; }
.st-key-reset_ask [data-testid="stBaseButton-secondary"] { min-height: 48px; border-radius: 14px; }

/* ---------- 광고 자리 ---------- */
.mk-ad {
  height: 56px; border-radius: 12px; border: 1px solid var(--line); background: #FFFFFF;
  display: grid; place-items: center; font-size: 12px; color: var(--sub);
  margin-top: calc(var(--gap-out) - var(--gap-in));
}

/* ---------- 소화 완료 연출 (전체 화면) ---------- */
.st-key-sheet_done {
  position: fixed; top: 0; bottom: 0; left: 50%; transform: translateX(-50%);
  width: min(100%, 430px); z-index: 300; background: #FFFFFF;
  justify-content: center; gap: 10px !important;
  padding: 24px 16px calc(24px + var(--safe-bottom));
}
.mk-done { text-align: center; padding-bottom: calc(var(--gap-out) - var(--gap-in)); }
.mk-done img { width: 200px; height: 200px; object-fit: contain; filter: drop-shadow(0 14px 14px rgba(30, 37, 48, .18)); animation: mk-pop .45s var(--ease-pop); }
@keyframes mk-pop { from { transform: scale(.6); opacity: 0; } }
.mk-done-title, .mk-done-meta, .st-key-sheet_done .stButton { animation: mk-rise .26s var(--ease-enter) both; }
.mk-done-title { animation-delay: .14s; }
.mk-done-meta { animation-delay: .18s; }
.st-key-sheet_done .stButton { animation-delay: .22s; }
@keyframes mk-rise { from { opacity: 0; transform: translateY(8px); } }
.mk-done-title { font-size: 26px; font-weight: 700; line-height: 1.35; margin-top: 20px; }
.mk-done-meta { font-size: 14px; color: var(--sub); margin-top: 8px; }

/* ---------- 스플래시 (앱 실행 직후 1.8초): 남색 바탕 가운데 흰 텍스트 로고만 ---------- */
.st-key-sheet_splash {
  position: fixed; top: 0; bottom: 0; left: 50%; transform: translateX(-50%);
  width: min(100%, 430px); z-index: 400; background: #1E2530;
  justify-content: center; align-items: center; gap: 0 !important; padding: 0 16px;
}
.st-key-sheet_splash > [data-testid="stElementContainer"]:has(.stButton) {
  position: absolute; inset: 0; z-index: 2; margin: 0; width: 100% !important; height: 100% !important; max-width: none !important;
}
.st-key-sheet_splash .stButton, .st-key-sheet_splash .stButton button { width: 100%; height: 100%; min-height: 0; }
.st-key-sheet_splash .stButton button { opacity: 0; cursor: pointer; }
.stApp .mk-splash-logo { font-size: 44px; line-height: 1.1; letter-spacing: 0.02em; color: #FFFFFF; text-align: center; }

/* ---------- 토스트 (iOS식: 화면 맨 위 로고 줄에 작은 알약, 2.5초 뒤 저절로 사라짐, 터치를 막지 않음)
   누를 버튼이 없는 상단에 띄워, 연달아 누르는 버튼(움직임·주문)을 가리지 않는다. ---------- */
.mk-toast {
  position: fixed; left: 50%; top: calc(6px + var(--safe-top)); z-index: 250;
  max-width: min(358px, calc(100% - 32px)); width: max-content;
  padding: 10px 18px; border-radius: 999px;
  background: var(--ink); color: #FFFFFF; font-size: 14px; font-weight: 600; line-height: 1.4; text-align: center;
  box-shadow: 0 6px 20px rgba(30, 37, 48, .18); pointer-events: none;
  transform: translateX(-50%); opacity: 0;
  animation: mk-toast 2.6s var(--ease-enter) forwards;
}
@keyframes mk-toast {
  0% { opacity: 0; transform: translate(-50%, -8px); }
  10%, 80% { opacity: 1; transform: translate(-50%, 0); }
  100% { opacity: 0; transform: translate(-50%, 0); visibility: hidden; }
}
@media (prefers-reduced-motion: reduce) {
  /* 움직임 없이 나타났다 사라지기만 한다 */
  .mk-toast { animation: mk-toast-still 2.6s steps(1, end) forwards !important; opacity: 1; }
  @keyframes mk-toast-still { to { opacity: 0; visibility: hidden; } }
}

:focus-visible { outline: 3px solid var(--cyan) !important; outline-offset: 2px; }
/* ---------- 인터랙션 (ui-animation 스킬 기준) ----------
   누름: 0ms로 바로 97%, 손을 떼면 160ms로 돌아온다. 상태 색은 150ms. 터치 기본 회색 깜빡임·두 번 탭 확대는 끈다 */
.stApp .stButton button, [class*="st-key-tap_"] { -webkit-tap-highlight-color: transparent; touch-action: manipulation; }
.stApp .stButton button {
  transition: transform .16s var(--ease-press), background-color .15s ease, border-color .15s ease, color .15s ease, opacity .15s ease, box-shadow .15s ease;
}
.stApp .stButton button:not(:disabled):active { transform: scale(.97); transition-duration: 0s; }
.stApp .stButton button:disabled { cursor: not-allowed; }
.mk-card { transition: transform .16s var(--ease-press); }
[class*="st-key-tap_"]:has(button:active) .mk-card { transform: scale(.97); transition-duration: 0s; }
/* 온보딩 단계: 앞으로 가면 오른쪽에서, 이전으로 가면 왼쪽에서 들어온다 (공간 방향과 같게). 진행 막대는 새 칸만 왼쪽부터 찬다 */
.mk-header.mk-fwd { animation: mk-in-fwd .24s var(--ease-move); }
.mk-header.mk-back { animation: mk-in-back .24s var(--ease-move); }
@keyframes mk-in-fwd { from { opacity: 0; transform: translateX(16px); } }
@keyframes mk-in-back { from { opacity: 0; transform: translateX(-16px); } }
.mk-progress span.now { position: relative; background: var(--line); }
.mk-progress span.now::after {
  content: ""; position: absolute; inset: 0; border-radius: inherit; background: var(--ink);
  transform-origin: left; animation: mk-fill .3s var(--ease-move) both;
}
@keyframes mk-fill { from { transform: scaleX(0); } }
/* 방금 주문한 음식(또는 도착한 배달): 들어간 자리에서 살짝 커지며 나타난다 */
.mk-new { animation: mk-new .26s var(--ease-enter); }
@keyframes mk-new { from { opacity: 0; transform: scale(.94); } }
/* 배달 수 알약: 방금 보낸 친구 카드에서 톡 튄다 */
.mk-fr-gift.mk-bump { animation: mk-bump .3s var(--ease-pop); }
@keyframes mk-bump { from { transform: scale(.5); opacity: 0; } }

/* 동작 줄이기: 위치·크기 이동(떠다님·튀어나옴·밀려옴·누름 축소)은 끄고, 색·투명도 피드백은 남긴다 */
@media (prefers-reduced-motion: reduce) {
  .mk-hero.on .mk-float, .mk-chip.on i { animation-play-state: paused; }
  .mk-plate.chomp { animation: none; }
  .mk-card.sel .mk-pick, .mk-done img, .mk-done-title, .mk-done-meta, .st-key-sheet_done .stButton,
  .mk-header.mk-fwd, .mk-header.mk-back, .mk-new, .mk-fr-gift.mk-bump { animation: mk-fade .15s linear both; }
  .mk-progress span.now::after { animation: none; }
  .stApp .stButton button:not(:disabled):active { transform: none; opacity: .7; }
  [class*="st-key-tap_"]:has(button:active) .mk-card { transform: none; opacity: .7; }
}
@keyframes mk-fade { from { opacity: 0; } }
</style>
""".replace("CHECK_WHITE", _CHECK_WHITE)


def inject() -> None:
    st.markdown(_CSS, unsafe_allow_html=True)
    # 아이폰 미리보기(preview/iphone14.html)는 iframe이라 기기의 안전 영역 값을 받지 못한다.
    # 미리보기가 ?safe_bottom=34 처럼 알려 주면 그만큼 하단 탭·버튼 아래를 비운다 (홈 인디케이터 자리).
    # ?safe_top=47 은 상태 표시줄 높이: 앱이 화면 맨 위까지 그려지고(스플래시 등), 내용은 그 아래부터 시작한다.
    for param, var, cap in (("safe_bottom", "--sim-safe-bottom", 60), ("safe_top", "--sim-safe-top", 80)):
        v = st.query_params.get(param, "")
        if v.isdigit():
            st.markdown(f"<style>:root {{ {var}: {min(int(v), cap)}px; }}</style>", unsafe_allow_html=True)


def html(markup: str) -> None:
    """한 줄 HTML 조각을 그린다. (들여쓰기가 있으면 마크다운 코드 블록이 되므로 줄을 합친다)"""
    st.markdown("".join(line.strip() for line in markup.splitlines()), unsafe_allow_html=True)


def toast(message: str) -> None:
    """다음 화면 그리기에서 한 번 보여 줄 토스트를 예약한다 (콜백 안에서 호출)."""
    st.session_state["_toast"] = message


def render_toast() -> None:
    """예약된 토스트를 한 번 그리고 지운다. 화면 맨 끝에서 호출한다."""
    message = st.session_state.pop("_toast", None)
    if message:
        html(f'<div class="mk-toast" role="status" aria-live="polite">{escape(message)}</div>')
