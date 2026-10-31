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


/* ---------- 보조 버튼 (멈추기, 냉장고 보기, 움직임 흉내 버튼) ---------- */
[data-testid="stBaseButton-secondary"] {
  min-height: 44px; border-radius: 12px; border: 1.5px solid var(--line);
  background: #FFFFFF; color: var(--ink); font-size: 15px; font-weight: 600;
}
[data-testid="stBaseButton-secondary"]:hover { border-color: var(--ink); color: var(--ink); background: #FFFFFF; }
.st-key-bar_footer [data-testid="stBaseButton-secondary"],
.st-key-sheet_done [data-testid="stBaseButton-secondary"] {
  min-height: 52px; border-radius: 14px; border: 2px solid var(--ink); font-size: 17px; font-weight: 700;
}

/* ---------- 하단 탭 ---------- */
.st-key-bar_tabs {
  position: fixed; left: 50%; bottom: 0; transform: translateX(-50%);
  width: min(100%, 430px); z-index: 110;
  display: grid !important; grid-template-columns: repeat(4, 1fr); gap: 0 !important;
  padding: 4px 8px calc(4px + env(safe-area-inset-bottom));
  background: #FFFFFF; border-top: 1px solid var(--line);
}
.st-key-bar_tabs > [data-testid="stElementContainer"] { width: 100% !important; }
.st-key-bar_tabs .stButton, .st-key-bar_tabs .stButton button { width: 100%; }
.st-key-bar_tabs .stButton button {
  min-height: 52px; padding: 4px 0; flex-direction: column; gap: 2px; color: var(--sub);
}
.st-key-bar_tabs .stButton button p { font-size: 11px !important; font-weight: 600; }
.st-key-bar_tabs .stButton button::before {
  content: ""; width: 24px; height: 24px; background: currentColor;
  -webkit-mask: var(--icon) center / contain no-repeat; mask: var(--icon) center / contain no-repeat;
}
.st-key-bar_tabs .stButton button:hover { text-decoration: none; }
.st-key-tab_home { --icon: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'><path d='M3 10.5 12 3l9 7.5V20a1 1 0 0 1-1 1h-5v-6h-6v6H4a1 1 0 0 1-1-1z'/></svg>"); }
.st-key-tab_fridge { --icon: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'><rect x='5' y='2' width='14' height='20' rx='2'/><path d='M5 9h14M9 5v2M9 12v4'/></svg>"); }
.st-key-tab_community { --icon: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'><circle cx='9' cy='8' r='3.5'/><path d='M2.5 20c.6-3.5 3.3-5.5 6.5-5.5s5.9 2 6.5 5.5'/><circle cx='17' cy='9' r='2.5'/><path d='M17.5 14.5c2.2.3 3.6 2 4 4.5'/></svg>"); }
.st-key-tab_my { --icon: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'><circle cx='12' cy='8' r='4'/><path d='M4 21c.8-4 4-6.5 8-6.5s7.2 2.5 8 6.5'/></svg>"); }
/* 탭이 있는 화면: 주요 버튼은 탭 바로 위에 붙인다 */
.stApp:has(.st-key-bar_tabs) .st-key-bar_footer { bottom: calc(61px + env(safe-area-inset-bottom)); border-top: 0; padding-bottom: 10px; }
.stApp:has(.st-key-bar_tabs) [data-testid="stMainBlockContainer"] { padding-bottom: 220px !important; }

/* ---------- 홈: 상단 줄 ---------- */
.mk-topbar { display: flex; justify-content: space-between; align-items: center; min-height: 44px; }
/* 스크롤해도 상단 줄이 화면 맨 위에 붙어 있게 한다 */
[data-testid="stElementContainer"]:has(.mk-topbar) {
  position: sticky; top: 0; z-index: 90; background: #FFFFFF;
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
.mk-dots { display: flex; justify-content: center; gap: 6px; margin-top: 12px; }
.mk-dots span { width: 10px; height: 10px; border-radius: 50%; background: var(--line); }
.mk-dots span.on { background: var(--ink); }
.mk-meal-prog { display: flex; justify-content: space-between; font-size: 14px; color: var(--sub); margin-top: 16px; }
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
  padding: 24px 16px calc(24px + env(safe-area-inset-bottom));
}
.mk-done { text-align: center; padding-bottom: calc(var(--gap-out) - var(--gap-in)); }
.mk-done img { width: 200px; height: 200px; object-fit: contain; filter: drop-shadow(0 14px 14px rgba(30, 37, 48, .18)); animation: mk-pop .5s ease-out; }
@keyframes mk-pop { from { transform: scale(.6); opacity: 0; } }
.mk-done-title { font-size: 26px; font-weight: 700; line-height: 1.35; margin-top: 20px; }
.mk-done-meta { font-size: 14px; color: var(--sub); margin-top: 8px; }

/* ---------- 토스트 (iOS식: 화면 맨 위 로고 줄에 작은 알약, 2.5초 뒤 저절로 사라짐, 터치를 막지 않음)
   누를 버튼이 없는 상단에 띄워, 연달아 누르는 버튼(움직임·주문)을 가리지 않는다. ---------- */
.mk-toast {
  position: fixed; left: 50%; top: calc(6px + env(safe-area-inset-top)); z-index: 250;
  max-width: min(358px, calc(100% - 32px)); width: max-content;
  padding: 10px 18px; border-radius: 999px;
  background: var(--ink); color: #FFFFFF; font-size: 14px; font-weight: 600; line-height: 1.4; text-align: center;
  box-shadow: 0 6px 20px rgba(30, 37, 48, .18); pointer-events: none;
  transform: translateX(-50%); opacity: 0;
  animation: mk-toast 2.6s ease forwards;
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
@media (prefers-reduced-motion: reduce) {
  *:not(.mk-toast) { animation: none !important; transition: none !important; }
}
</style>
""".replace("CHECK_WHITE", _CHECK_WHITE)


def inject() -> None:
    st.markdown(_CSS, unsafe_allow_html=True)


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
