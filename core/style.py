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

import base64
import json
from html import escape
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

_BRAND_DIR = Path(__file__).resolve().parent.parent / "assets" / "img" / "brand"


def _brand_uri(name: str) -> str:
    """assets/img/brand/의 PNG를 data URI로 (tools/extract_brand_assets.py가 브랜드 가이드에서 잘라 만든 파일)."""
    data = (_BRAND_DIR / f"{name}.png").read_bytes()
    return "data:image/png;base64," + base64.b64encode(data).decode()

_CHECK_WHITE = (
    "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'>"
    "<path d='M5 12.5l4.5 4.5L19 7.5' fill='none' stroke='white' stroke-width='3' "
    "stroke-linecap='round' stroke-linejoin='round'/></svg>"
)

_CSS = """
<style>
@import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.min.css');

:root {
  /* 브랜드 가이드 색 (assets/img/Brand_Guide/mukbogibrand.png) */
  --brand: #FF8A3D;      /* 주황: 주요 버튼·포인트 (글자는 남색 #222 — 흰 글자는 대비 2.3:1이라 쓰지 않음) */
  /* 주요 버튼 글로우: 주황 빛이 버튼 아래로 은은하게 번진다 (보통 · 마우스 올림 · 누름) */
  --glow: 0 4px 14px rgba(255, 138, 61, .45), 0 0 0 1px rgba(255, 138, 61, .15);
  --glow-strong: 0 6px 22px rgba(255, 138, 61, .6), 0 0 0 3px rgba(255, 138, 61, .18);
  --glow-press: 0 2px 8px rgba(255, 138, 61, .4);
  --brand-soft: #FFE3CC; /* 연주황: 큰 보조 버튼 채움 (검정 글자 대비 14:1) */
  --yellow: #FFD166;     /* 노랑: 강조 알약(목표 달성·플러스) */
  --cream: #FFF7EE;      /* 크림: 화면 바탕 */
  --green: #8CC084;      /* 초록: 움직임·소화 진행, 현재 탭 아이콘 */
  --line: #E5E5E5;       /* 회색: 구분선·테두리 */
  --ink: #222222;        /* 검정: 글자·선택 표시 */
  /* 가이드 색에서 파생 */
  --soft: #FFFFFF;       /* 카드 바탕 (크림 위 흰 카드) */
  --fill: #FFF7EE;       /* 흰 카드 안 작은 칸 */
  --track: #F2E8DC;      /* 크림 위 세그먼트 틀 */
  --line-2: #CCCCCC;     /* 빈 선택 원 테두리 */
  --sub: #666666;        /* 보조 글자 (크림 대비 5.4:1 · 흰 바탕 5.7:1) */
  --shadow: 0 1px 2px rgba(34, 34, 34, .04), 0 4px 14px rgba(34, 34, 34, .05);
  --gap-in: 10px;        /* 같은 묶음 안 */
  --danger: #B42318;     /* 오류 글자·테두리 (흰 바탕 대비 6.3:1) */
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
.stApp { background: var(--cream); color: var(--ink); word-break: keep-all; overflow-wrap: break-word; }  /* 한국어는 낱말 단위로 줄바꿈 */

/* 스크롤바 숨기기: 아이폰처럼 스크롤은 되지만 막대는 보이지 않게 (미리보기·데스크톱 브라우저 포함) */
html, body, [data-testid="stMain"], [data-testid="stAppViewContainer"] { scrollbar-width: none !important; -ms-overflow-style: none; }
html::-webkit-scrollbar, body::-webkit-scrollbar,
[data-testid="stMain"]::-webkit-scrollbar, [data-testid="stAppViewContainer"]::-webkit-scrollbar { display: none !important; width: 0 !important; height: 0 !important; }

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
.mk-progress span.on { background: var(--brand); }
.mk-step { width: 44px; text-align: right; font-size: 13px; font-weight: 600; color: var(--sub); }
/* 이전 버튼: 44×44 아이콘. 글자 "이전"은 크기 0으로 숨겨 스크린리더만 읽게 한다 */
.st-key-nav_row .stButton button { width: 44px; height: 44px; min-height: 44px; padding: 0; justify-content: flex-start; }
.st-key-nav_row .stButton button p { font-size: 0 !important; }
.st-key-nav_row .stButton button p::before { content: "‹"; font-size: 34px; font-weight: 400; line-height: 1; color: var(--ink); }

/* ---------- 머리말 (제목 + 설명) ---------- */
.mk-header { padding: 8px 0 calc(var(--gap-out) - var(--gap-in)); }
.mk-title { font-size: 26px; font-weight: 700; line-height: 1.3; letter-spacing: -0.02em; color: var(--ink); }
.mk-sub { font-size: 15px; line-height: 1.5; color: var(--sub); margin-top: 8px; }
/* 로고: 브랜드 가이드 로고(마스코트 얼굴이 O 자리) 이미지. 글자는 크기 0으로 남겨 스크린리더가 "MUKBOGI"로 읽는다 */
.stApp .mk-wordmark {
  display: inline-block; vertical-align: middle; font-size: 0 !important; color: transparent;
  width: 102px; height: 28px; background: url("BRAND_LOGO") left center / contain no-repeat;
}
.mk-section { font-size: 18px; font-weight: 700; color: var(--ink); padding-top: calc(var(--gap-out) - var(--gap-in)); }  /* typography.section-header */
.mk-count { font-size: 13px; font-weight: 600; color: var(--sub); }

/* ---------- 버튼 ---------- */
.stButton button p { font-size: inherit; font-weight: inherit; }
[data-testid="stBaseButton-primary"] {
  min-height: 52px; border-radius: 14px; border: 0;
  background: var(--brand); color: var(--ink); font-size: 17px; font-weight: 700;
  box-shadow: var(--glow);
}
@media (hover: hover) and (pointer: fine) {
  [data-testid="stBaseButton-primary"]:not(:disabled):hover { background: var(--brand); color: var(--ink); box-shadow: var(--glow-strong); }
}
.stApp [data-testid="stBaseButton-primary"]:not(:disabled):active { box-shadow: var(--glow-press); }
[data-testid="stBaseButton-primary"]:disabled { background: var(--line); color: var(--sub); opacity: 1; box-shadow: none; }
/* 작은 알약 버튼(수락 · 친구 요청)은 글로우도 작게 */
[class*="st-key-urow_"] [data-testid="stBaseButton-primary"]:not(:disabled) { box-shadow: 0 2px 8px rgba(255, 138, 61, .4); }
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
[class*="st-key-tap_"]:has(button:focus-visible) .mk-card { outline: 3px solid var(--ink); outline-offset: 2px; }

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
.mk-type-ex { font-size: 13px; color: var(--sub); line-height: 1.4; min-height: 2.8em; word-break: keep-all; }  /* 음식 이름이 두 줄인 카드가 있어도 세 카드 높이를 맞춘다 */

/* ---------- 2단계: 음식 3열 그리드 ---------- */
[class*="st-key-grid_"] {
  display: grid !important; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: var(--gap-in) !important;
}
.mk-food { display: flex; flex-direction: column; align-items: center; padding: 16px 6px 12px; text-align: center; }
.mk-food .mk-pick { position: absolute; top: 6px; right: 6px; width: 22px; height: 22px; }
.mk-food img { width: 64px; height: 64px; object-fit: contain; filter: drop-shadow(0 3px 4px rgba(30, 37, 48, .14)); }
.mk-food-name { font-size: 15px; font-weight: 600; margin-top: 10px; line-height: 1.3; word-break: keep-all; }
/* 좁은 화면(SE)에서는 "후라이드치킨"처럼 긴 이름이 두 줄이 되므로, 모든 칸이 두 줄 자리를 잡아 줄 높이를 맞춘다 */
@media (max-width: 359px) { .mk-food-name { min-height: 2.6em; display: flex; align-items: center; justify-content: center; } }
.mk-food-kcal { font-size: 13px; color: var(--sub); line-height: 1.4; }

/* ---------- 3단계: 성별·키·몸무게 입력 (라벨 · 입력칸 한 묶음씩, 단위는 칸 안 오른쪽) ---------- */
:is(.st-key-ob_weight, .st-key-ob_height) label p { font-size: 15px; font-weight: 600; color: var(--ink); }
:is(.st-key-ob_weight, .st-key-ob_height) [data-testid="stNumberInputContainer"] {
  position: relative; border-radius: 14px; background: var(--soft);
  border: 2px solid transparent; min-height: 56px;
}
:is(.st-key-ob_weight, .st-key-ob_height) [data-testid="stNumberInputContainer"]:focus-within { border-color: var(--ink); background: #FFFFFF; }
:is(.st-key-ob_weight, .st-key-ob_height) [data-testid="stNumberInputContainer"]::after {
  content: "kg"; position: absolute; right: 16px; top: 50%; transform: translateY(-50%);
  font-size: 17px; font-weight: 600; color: var(--sub); pointer-events: none;
}
:is(.st-key-ob_weight, .st-key-ob_height) input:focus-visible { outline: none !important; }  /* 포커스는 입력칸 테두리로 표시 */
:is(.st-key-ob_weight, .st-key-ob_height) input { font-size: 22px; font-weight: 700; color: var(--ink); background: transparent; padding-right: 48px; }
/* 안내 문구는 입력한 숫자보다 작고 가볍게 */
:is(.st-key-ob_weight, .st-key-ob_height) input::placeholder { font-size: 16px; font-weight: 400; color: var(--sub); opacity: 1; }
:is(.st-key-ob_weight, .st-key-ob_height) [data-testid="stNumberInputStepDown"],
:is(.st-key-ob_weight, .st-key-ob_height) [data-testid="stNumberInputStepUp"],
:is(.st-key-ob_weight, .st-key-ob_height) [data-testid="InputInstructions"] { display: none; }
:is(.st-key-ob_height) [data-testid="stNumberInputContainer"]::after { content: "cm"; }
.mk-field-label { font-size: 15px; font-weight: 600; color: var(--ink); line-height: 1.4; }
/* 근접: 라벨–칸은 붙이고(4px), 묶음 사이는 넓게(20px) */
.stElementContainer:has(.mk-field-label) { margin-bottom: -6px; }
.st-key-ob_height, .st-key-ob_weight { margin-top: 10px; }
.mk-note { font-size: 13px; color: var(--sub); line-height: 1.5; margin-top: -4px; }
.mk-error { font-size: 13px; font-weight: 600; color: var(--danger); margin-top: -4px; }

/* ---------- 하단 고정 버튼 영역 ---------- */
.st-key-bar_footer {
  position: fixed; left: 50%; bottom: 0; transform: translateX(-50%);
  width: min(100%, 430px); z-index: 100; gap: 6px !important;
  padding: 10px 16px calc(16px + var(--safe-bottom));
  background: var(--cream);
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
.mk-fav img { width: 48px; height: 48px; border-radius: 50%; object-fit: cover; display: block; margin: 0 auto 6px; background: var(--fill); }


/* ---------- 보조 버튼 (멈추기, 냉장고 보기, 움직임 흉내 버튼) ---------- */
[data-testid="stBaseButton-secondary"] {
  min-height: 44px; border-radius: 12px; border: 1.5px solid var(--line);
  background: #FFFFFF; color: var(--ink); font-size: 15px; font-weight: 600;
}
@media (hover: hover) and (pointer: fine) {
  [data-testid="stBaseButton-secondary"]:hover { border-color: var(--ink); color: var(--ink); background: #FFFFFF; }
}
/* 큰 보조 버튼(멈추기·냉장고 보기·플러스 해지): 주요 버튼과 같은 크기, 연주황 채움 + 검정 글자로 색만 다르게 */
.st-key-bar_footer [data-testid="stBaseButton-secondary"],
.st-key-sheet_done [data-testid="stBaseButton-secondary"],
.st-key-plus_box [data-testid="stBaseButton-secondary"] {
  min-height: 52px; border-radius: 14px; border: 0; background: var(--brand-soft); color: var(--ink);
  font-size: 17px; font-weight: 700;
}
@media (hover: hover) and (pointer: fine) {
  .st-key-bar_footer [data-testid="stBaseButton-secondary"]:hover,
  .st-key-sheet_done [data-testid="stBaseButton-secondary"]:hover,
  .st-key-plus_box [data-testid="stBaseButton-secondary"]:hover { background: var(--brand-soft); color: var(--ink); filter: brightness(.97); }
}

/* 홈 멈추기: 측정 중임을 또렷하게 — 검정 #212121 채움 + 흰 글자 (대비 16:1). 크기는 식사시작과 같다 */
.st-key-bar_footer .st-key-home_stop [data-testid="stBaseButton-secondary"] { background: #212121; color: #FFFFFF; }
@media (hover: hover) and (pointer: fine) {
  .st-key-bar_footer .st-key-home_stop [data-testid="stBaseButton-secondary"]:hover { background: #212121; color: #FFFFFF; filter: brightness(1.15); }
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
/* 홈 식사시작·멈추기: 바탕 띠 없이 버튼만 떠 있게. 버튼 밖은 터치가 뒤 내용으로 지나간다 */
.stApp .st-key-bar_footer:has(.st-key-home_start, .st-key-home_stop) { background: transparent; pointer-events: none; }
.st-key-bar_footer .st-key-home_start button,
.st-key-bar_footer .st-key-home_stop button { pointer-events: auto; box-shadow: 0 6px 16px rgba(34, 34, 34, .18); }
/* 식사시작은 다른 주요 버튼과 같은 주황 글로우 (마우스 올림·누름은 공통 규칙이 이어받는다) */
.st-key-bar_footer .st-key-home_start [data-testid="stBaseButton-primary"] { box-shadow: var(--glow); }
@media (hover: hover) and (pointer: fine) {
  .st-key-bar_footer .st-key-home_start [data-testid="stBaseButton-primary"]:hover { box-shadow: var(--glow-strong); }
}
.stApp .st-key-bar_footer .st-key-home_start [data-testid="stBaseButton-primary"]:active { box-shadow: var(--glow-press); }
.stApp:has(.st-key-bar_tabs) [data-testid="stMainBlockContainer"] { padding-bottom: calc(220px + var(--safe-bottom)) !important; }

/* ---------- 홈: 상단 줄 ---------- */
.mk-topbar { display: flex; justify-content: space-between; align-items: center; min-height: 44px; }
/* GNB: 스크롤해도 화면 맨 위(상태 표시줄 바로 아래)에 붙어 있게 한다.
   탭 화면의 로고 줄(.mk-topbar)과, 이전 버튼이 있는 화면의 [이전][제목·진행 막대][자리] 줄(nav_row:
   배달 보내기 · 주문하기 · 다른 유저 · 온보딩 · 회원가입)이 같은 규칙을 쓴다.
   nav_row는 높이가 같은 래퍼(stLayoutWrapper)에 싸여 있어, sticky는 그 래퍼에 건다 (안쪽에 걸면 움직일 공간이 없다) */
[data-testid="stElementContainer"]:has(.mk-topbar), [data-testid="stLayoutWrapper"]:has(> .st-key-nav_row) {
  position: sticky; top: var(--safe-top); z-index: 90; background: var(--cream);
  /* 좌우 16px 여백까지 덮어, 아래 카드 그림자가 양옆으로 비치지 않게 화면 폭 전체로 넓힌다 */
  margin-left: -16px; margin-right: -16px; padding-left: 16px; padding-right: 16px; width: calc(100% + 32px) !important; min-width: calc(100% + 32px) !important; max-width: none !important; box-sizing: border-box;
  /* 상태 표시줄 뒤와 위쪽 틈도 흰색으로 덮는다 (상단 줄 높이 44px < 상태 표시줄 47px라 두 겹) */
  box-shadow: 0 calc(-1 * var(--safe-top)) 0 var(--cream), 0 -12px 0 var(--cream);
}
/* 스크롤하면 GNB 아래에 1px 구분선이 생긴다 (iOS처럼, 맨 위에서는 없음). 스크롤 위치에 따라 움직이므로 곡선·시간 없이 linear.
   scroll-timeline을 못 쓰는 브라우저에서는 선 없이 그대로 */
@supports (animation-timeline: scroll()) {
  [data-testid="stElementContainer"]:has(.mk-topbar), [data-testid="stLayoutWrapper"]:has(> .st-key-nav_row) {
    animation: mk-gnb-line linear both; animation-timeline: scroll(nearest); animation-range: 0 16px;
  }
  @keyframes mk-gnb-line {
    to { box-shadow: 0 calc(-1 * var(--safe-top)) 0 var(--cream), 0 -12px 0 var(--cream), 0 1px 0 var(--line); }
  }
}
.mk-today { font-size: 13px; font-weight: 600; color: var(--sub); background: var(--soft); border-radius: 999px; padding: 6px 12px; }
.mk-today b { color: var(--ink); }

/* ---------- 홈: 빈 상태 (문구 + 버튼을 한 카드로) ---------- */
.st-key-empty_box {
  background: var(--soft); border-radius: 16px; padding: 32px 16px 16px; gap: 20px !important; text-align: center;
  margin-top: calc(var(--gap-out) - var(--gap-in));
}
.mk-empty-title { font-size: 22px; font-weight: 700; color: var(--ink); }

/* ---------- 홈: 이번 주 소화 (음식 몇 개만큼) ---------- */
.mk-nowrap { white-space: nowrap; }
.mk-week { background: var(--soft); border-radius: 16px; padding: 16px; }
.mk-week-head { display: flex; align-items: center; gap: 12px; }
.mk-week-head img { flex: 0 0 56px; width: 56px; height: 56px; object-fit: contain; filter: drop-shadow(0 3px 4px rgba(34, 34, 34, .12)); }
.mk-week-head > div { min-width: 0; }
.mk-week-title { font-size: 16px; font-weight: 700; line-height: 1.4; color: var(--ink); text-wrap: balance; }
.mk-week-title b { font-size: 18px; font-weight: 800; font-variant-numeric: tabular-nums; }
.mk-week-sub { font-size: 13px; color: var(--sub); margin-top: 4px; }
.mk-week-sub b { color: var(--ink); font-variant-numeric: tabular-nums; }
.mk-week-empty .mk-week-head img { opacity: .45; filter: grayscale(.4); }
.mk-week-empty .mk-week-title { font-size: 15px; font-weight: 600; }
.mk-week-alt { display: flex; flex-wrap: wrap; align-items: center; gap: 6px; margin-top: 12px; }
.mk-week-alt-label { font-size: 12px; font-weight: 600; color: var(--sub); margin-right: 2px; }
/* 기준 음식이 더 높은 칼로리 음식으로 바뀐 순간: 사진·문구가 한 번 톡 튀어 오른다 */
.mk-week-swap .mk-week-head img { animation: mk-week-swap 420ms var(--ease-pop) both; }
.mk-week-swap .mk-week-title { animation: mk-week-fade 320ms var(--ease-enter) both; }
@keyframes mk-week-swap { from { transform: scale(.6) rotate(-8deg); opacity: 0; } }
@keyframes mk-week-fade { from { opacity: 0; transform: translateY(4px); } }
@media (prefers-reduced-motion: reduce) {
  .mk-week-swap .mk-week-head img, .mk-week-swap .mk-week-title { animation-name: mk-week-fade-only; }
  @keyframes mk-week-fade-only { from { opacity: 0; } }
}
/* 좁은 화면(SE): 칩 하나만 아랫줄로 떨어지지 않게 안내 문구를 윗줄로 따로 둔다 */
@media (max-width: 360px) { .mk-week-alt-label { flex-basis: 100%; } }
.mk-week-chip { display: inline-flex; align-items: center; gap: 4px; font-size: 13px; color: var(--ink); background: var(--fill); border-radius: 999px; padding: 4px 10px 4px 4px; white-space: nowrap; }
.mk-week-chip img { width: 22px; height: 22px; object-fit: contain; }
.mk-week-chip b { font-variant-numeric: tabular-nums; }
.mk-week-days { display: grid; grid-template-columns: repeat(7, 1fr); gap: 6px; margin-top: 14px; padding-top: 12px; border-top: 1px solid var(--line); }
.mk-wd { display: flex; flex-direction: column; align-items: center; gap: 4px; }
.mk-wd-track { position: relative; width: 100%; max-width: 28px; height: 44px; border-radius: 6px; background: var(--fill); overflow: hidden; }
.mk-wd-track i { position: absolute; left: 0; right: 0; bottom: 0; background: var(--green); border-radius: 6px; }
.mk-wd span { font-size: 12px; font-weight: 500; color: var(--sub); }
.mk-wd.today .mk-wd-track i { background: var(--brand); }
.mk-wd.today span { color: var(--ink); font-weight: 700; }
.mk-wd.later .mk-wd-track { background: transparent; border: 1px dashed var(--line); }
.mk-wd.later span { color: var(--sub); opacity: .6; }

/* ---------- 홈: 소화 중인 음식 카드 ---------- */
.mk-meal { background: var(--soft); border-radius: 16px; padding: 16px; margin-top: calc(var(--gap-out) - var(--gap-in) - 8px); }
.mk-meal-top { display: flex; justify-content: space-between; align-items: center; }
.mk-chip { display: inline-flex; align-items: center; gap: 6px; font-size: 13px; font-weight: 600; background: var(--fill); border-radius: 999px; padding: 5px 10px; }
.mk-chip i { width: 8px; height: 8px; border-radius: 50%; background: var(--line-2); }
.mk-chip.on i { background: var(--green); animation: mk-pulse 1.6s ease-in-out infinite; }
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
.mk-stat { background: var(--fill); border-radius: 12px; padding: 10px 12px; }
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
.mk-q-add { background: transparent; border: 1.5px dashed var(--line-2); font-size: 13px; font-weight: 600; gap: 4px; }
.mk-q-add span { font-size: 26px; font-weight: 400; line-height: 1; }

.mk-row-scroll { display: flex; gap: var(--gap-in); overflow-x: auto; margin: 0 -16px; padding: 0 16px 4px; scrollbar-width: none; }
.mk-row-scroll::-webkit-scrollbar, .st-key-row_queue::-webkit-scrollbar { display: none; }
.mk-fr { flex: 0 0 148px; background: var(--soft); border-radius: 14px; padding: 12px; }
.mk-fr-head { display: flex; align-items: center; gap: 8px; font-size: 14px; font-weight: 600; }
.mk-avatar { position: relative; overflow: hidden; width: 32px; height: 32px; border-radius: 50%; object-fit: cover; flex: none; }
/* 프로필 사진(core/avatar.py)은 이름 첫 글자 원 위에 CSS 배경으로 겹친다. 사진을 못 불러오면 배경이 비어 첫 글자가 보인다 */
.mk-avatar-photo { position: absolute; inset: 0; border-radius: inherit; background: center / cover no-repeat; }
.mk-avatar-initial { display: grid; place-items: center; background: var(--yellow); color: var(--ink); font-size: 13px; font-weight: 700; }
.mk-fr-food { display: flex; align-items: center; gap: 8px; font-size: 13px; margin-top: 12px; }
.mk-fr-food img { width: 40px; height: 40px; object-fit: contain; filter: drop-shadow(0 2px 3px rgba(30, 37, 48, .14)); }
.mk-bar { height: 6px; border-radius: 3px; background: var(--line); overflow: hidden; margin-top: 10px; }
.mk-bar i { display: block; height: 100%; background: var(--green); border-radius: inherit; }
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
.mk-fz-goal { font-size: 12px; font-weight: 700; color: var(--ink); background: var(--yellow); border-radius: 999px; padding: 3px 8px; }
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
/* 가로 캐러셀 공통(친구·조리 중): 화면 양끝까지 넓혀 다음 카드가 끝에서 살짝 보이게 하고(더 있다는 신호),
   손을 떼면 카드 시작점에 딱 맞춰 멈춘다. 마우스 휠·끌기 스크롤은 style.enable_drag_scroll()이 붙인다 */
.st-key-row_friends, .st-key-row_queue {
  width: calc(100% + 32px) !important; max-width: none !important; box-sizing: border-box;
  scroll-snap-type: x mandatory; scroll-padding-inline: 16px; overscroll-behavior-x: contain;
  -webkit-overflow-scrolling: touch; touch-action: pan-x pan-y;
}
.st-key-row_friends > *, .st-key-row_queue > * { scroll-snap-align: start; }
.st-key-row_friends.mk-dragging, .st-key-row_queue.mk-dragging { scroll-snap-type: none; cursor: grabbing; user-select: none; }
@media (hover: hover) and (pointer: fine) { .st-key-row_friends, .st-key-row_queue { cursor: grab; } }
/* 마지막 카드 뒤에도 16px 여백이 남게 (flex 끝 padding은 스크롤 영역에 안 잡히므로 빈 칸으로) */
.st-key-row_friends::after, .st-key-row_queue::after { content: ""; flex: 0 0 6px; }
.st-key-row_friends::-webkit-scrollbar { display: none; }
.st-key-row_friends > * { flex: 0 0 148px !important; width: 148px !important; }
.st-key-row_friends .mk-fr { height: 100%; }
.mk-fr.mk-card { border-width: 2px; }
.mk-fr-head { position: relative; }
.mk-fr-gift {
  margin-left: auto; font-size: 11px; font-weight: 700; color: #FFFFFF; background: var(--ink);
  border-radius: 999px; padding: 2px 7px; white-space: nowrap;
}
.mk-q-from { font-size: 11px; font-weight: 700; color: #FFFFFF; background: var(--ink); border-radius: 999px; padding: 2px 7px; margin-top: 6px; }

/* ---------- 배달 보내기: 받는 친구 ---------- */
.mk-gift-to { display: flex; align-items: center; gap: 12px; background: var(--soft); border-radius: 16px; padding: 12px 14px; }
.mk-avatar-lg { width: 44px; height: 44px; font-size: 16px; }
.mk-gift-name { font-size: 16px; font-weight: 700; color: var(--ink); }
.mk-gift-doing { font-size: 13px; color: var(--sub); margin-top: 2px; }
.mk-gift-to .mk-fr-gift { margin-left: auto; }

/* ---------- 세그먼트 컨트롤 (커뮤니티 탭 · 랭킹 범위) ---------- */
[class*="st-key-seg_"] {
  background: var(--track); border-radius: 12px; padding: 3px; gap: 2px !important; flex-wrap: nowrap !important;
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
  background: var(--brand); color: var(--ink); font-size: 10px; font-weight: 700; line-height: 16px; text-align: center;
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
/* 친구 목록: 배달하기 오른쪽 위 동그란 숫자 배지 (보낸 배달 수, 내용은 화면에서 넣는다) */
/* 친구 요청 수락·거절: 결과를 그 줄 안에서 보여 준 뒤 옆으로 밀어내고 줄 높이를 접는다 (다음 그리기에서 사라짐).
   수락 = "친구가 됐어요" 알약이 톡 → 잠깐 머문 뒤 오른쪽으로 (새 친구는 친구 목록에 왼쪽에서 들어온다)
   거절 = 바로 왼쪽으로. 마지막 요청이면 목록 카드·섹션 제목째 접힌다 */
.mk-ghost-row { display: flex; align-items: center; gap: 8px; min-height: 64px; padding: 8px 0; }
.mk-ghost-row > .mk-u { flex: 1 1 auto; min-width: 0; }
.mk-ghost-pill { flex: none; display: inline-flex; align-items: center; gap: 6px; min-height: 44px; padding: 0 14px;
  border-radius: 999px; font-size: 14px; font-weight: 600; white-space: nowrap; background: var(--fill); color: var(--sub); }
.mk-ghost-pill.ok { background: var(--green); color: var(--ink); animation: mk-pop .28s var(--ease-pop) both; }
.mk-ghost-pill.ok i { width: 14px; height: 14px; background: currentColor;
  -webkit-mask: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'><path fill='none' stroke='black' stroke-width='3' stroke-linecap='round' stroke-linejoin='round' d='M5 12.5l4.5 4.5L19 7.5'/></svg>") center / contain no-repeat;
          mask: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'><path fill='none' stroke='black' stroke-width='3' stroke-linecap='round' stroke-linejoin='round' d='M5 12.5l4.5 4.5L19 7.5'/></svg>") center / contain no-repeat; }
[class*="st-key-list_"] > [data-testid="stElementContainer"]:has(.mk-ghost) { overflow: hidden; max-height: 81px; }
[class*="st-key-list_"] > [data-testid="stElementContainer"]:has(.mk-ghost-acc:not(.last)) {
  animation: mk-ghost-right .28s var(--ease-move) .56s both, mk-ghost-fold .2s var(--ease-move) .82s both; }
[class*="st-key-list_"] > [data-testid="stElementContainer"]:has(.mk-ghost-dec:not(.last)) {
  animation: mk-ghost-left .24s var(--ease-move) both, mk-ghost-fold .18s var(--ease-move) .22s both; }
/* 마지막 요청: 줄만이 아니라 목록 카드와 섹션 제목까지 접는다 (빈 "친구 요청" 칸이 남지 않게) */
[class*="st-key-list_"]:has(.mk-ghost-acc.last) { overflow: hidden;
  animation: mk-ghost-right .28s var(--ease-move) .56s both, mk-ghost-fold-box .22s var(--ease-move) .82s both; }
[class*="st-key-list_"]:has(.mk-ghost-dec.last) { overflow: hidden;
  animation: mk-ghost-left .24s var(--ease-move) both, mk-ghost-fold-box .2s var(--ease-move) .22s both; }
.stApp:has(.mk-ghost-acc.last) [data-testid="stElementContainer"]:has(> * .mk-ghost-headline) { overflow: hidden;
  animation: mk-ghost-fold-box .22s var(--ease-move) .82s both; }
.stApp:has(.mk-ghost-dec.last) [data-testid="stElementContainer"]:has(> * .mk-ghost-headline) { overflow: hidden;
  animation: mk-ghost-fold-box .2s var(--ease-move) .22s both; }
/* 맨 위 줄이 접히면 그다음 줄이 맨 위가 되므로, 그 줄의 위 구분선도 같이 지운다 */
[class*="st-key-list_"] > :first-child:has(.mk-ghost-acc) + * { animation: mk-line-out .2s var(--ease-move) .82s both; }
[class*="st-key-list_"] > :first-child:has(.mk-ghost-dec) + * { animation: mk-line-out .18s var(--ease-move) .22s both; }
@keyframes mk-line-out { to { border-top-color: transparent; } }
@keyframes mk-ghost-right { to { transform: translateX(104%); opacity: 0; } }
@keyframes mk-ghost-left { to { transform: translateX(-104%); opacity: 0; } }
@keyframes mk-ghost-fold { to { max-height: 0; border-top-color: transparent; } }
@keyframes mk-ghost-fold-box { from { max-height: 200px; } to { max-height: 0; padding-top: 0; padding-bottom: 0; margin-bottom: calc(-1 * var(--gap-in)); } }
@keyframes mk-friend-in { from { transform: translateX(-24px); opacity: 0; } }
@media (prefers-reduced-motion: reduce) {
  /* 옆으로 미는 이동만 끄고, 사라짐·접힘과 결과 알약은 남긴다 */
  @keyframes mk-ghost-right { to { opacity: 0; } }
  @keyframes mk-ghost-left { to { opacity: 0; } }
  @keyframes mk-friend-in { from { opacity: 0; } }
}
.st-key-list_friends [class*="st-key-gift_to_"] button { position: relative; overflow: visible; }
.st-key-list_friends [class*="st-key-gift_to_"] button::after {
  position: absolute; top: -6px; right: -4px; min-width: 20px; height: 20px; padding: 0 4px; box-sizing: border-box;
  border-radius: 999px; border: 2px solid var(--soft); background: var(--ink); color: #FFFFFF;
  font-size: 11px; font-weight: 700; line-height: 16px; text-align: center; font-variant-numeric: tabular-nums;
}
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
.mk-doing-bar i { display: block; height: 100%; background: var(--green); border-radius: inherit; }
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
/* 찾기: #212121 채움 + 흰 글자 (대비 16:1). 수락은 기본 주요 버튼(주황 #FF8A3D + 검정 글자) */
.st-key-cm_search [data-testid="stBaseButton-primary"] { background: #212121; color: #FFFFFF; box-shadow: 0 4px 12px rgba(33, 33, 33, .25); }
@media (hover: hover) and (pointer: fine) {
  .st-key-cm_search [data-testid="stBaseButton-primary"]:not(:disabled):hover { background: #212121; color: #FFFFFF; filter: brightness(1.15); box-shadow: 0 6px 18px rgba(33, 33, 33, .32); }
}
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
.mk-me-pill { font-size: 11px; font-weight: 700; color: var(--ink); background: var(--brand); border-radius: 999px; padding: 2px 7px; }
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
/* 프로필 머리: 아바타 56px + 이름. 요약은 한 장의 흰 카드 안 3칸(숫자 위, 이름 아래, 칸 사이 선) */
.mk-my-head .mk-prof { gap: 14px; padding: 4px 0 0; }
.mk-my-head .mk-avatar-xl { width: 56px; height: 56px; font-size: 20px; }
.mk-my-head .mk-prof-name { font-size: 20px; }
.mk-my-stats {
  display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 0; margin: 20px 0 0;
  background: var(--soft); border-radius: 16px; padding: 16px 0;
}
.mk-my-stats .mk-stat {
  display: flex; flex-direction: column-reverse; align-items: center; gap: 4px;
  background: transparent; border-radius: 0; padding: 0 6px; min-width: 0; text-align: center;
}
.mk-my-stats .mk-stat + .mk-stat { border-left: 1px solid var(--line); }
.mk-my-stats .mk-stat dt { white-space: nowrap; }
.mk-my-stats .mk-stat dd { font-size: clamp(17px, 5.2vw, 20px); margin: 0; white-space: nowrap; }  /* 좁은 화면에서도 다섯 자리 kcal이 한 줄에 */
.mk-my-note { font-size: 13px; color: var(--sub); line-height: 1.5; }
.mk-my-note b { color: var(--ink); }
.mk-plus-pill { font-size: 11px; font-weight: 700; color: var(--ink); background: var(--yellow); border-radius: 999px; padding: 3px 9px; }
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
.mk-plus-badge { font-size: 12px; font-weight: 700; color: var(--sub); background: var(--fill); border: 1px solid var(--line); border-radius: 999px; padding: 4px 10px; }
.mk-plus-badge.on { color: var(--ink); background: var(--yellow); border-color: var(--yellow); }
.mk-plus-title { font-size: 17px; font-weight: 700; color: var(--ink); line-height: 1.35; }
/* 혜택 목록: 흰 카드 안 [아이콘 원 | 이름 | (준비 중)] 줄 */
.mk-plus-perks { list-style: none; margin: 16px 0 0 !important; padding: 0 14px !important; background: var(--fill); border-radius: 14px; }
.mk-plus-perks li { margin: 0 !important; padding: 0 !important; display: flex; align-items: center; gap: 12px; min-height: 56px; font-size: 15px; font-weight: 600; color: var(--ink); }
.mk-plus-perks li + li { border-top: 1px solid var(--line); }
.mk-perk-ico { flex: none; width: 36px; height: 36px; border-radius: 50%; background: var(--soft); position: relative; }
.mk-perk-ico::before {
  content: ""; position: absolute; inset: 8px; background: var(--ink);
  -webkit-mask: var(--icon) center / contain no-repeat; mask: var(--icon) center / contain no-repeat;
}
.mk-plus-perks .mk-soon { margin-left: auto; }
.mk-ico-noad { --icon: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'><rect x='3' y='5' width='18' height='14' rx='3'/><path d='M4 4l16 16'/></svg>"); }
.mk-ico-report { --icon: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'><rect x='4' y='3' width='16' height='18' rx='2'/><path d='M8 16v-3M12 16V9M16 16v-5'/></svg>"); }
.mk-soon { font-size: 11px; font-weight: 700; color: var(--sub); background: var(--soft); border-radius: 999px; padding: 3px 8px; white-space: nowrap; }
/* 플러스 시작·해지 버튼은 같은 크기 (높이 52px · 모서리 14px · 17px/700). 해지는 연주황 채움 */
.st-key-plus_box .stButton button { height: 52px; min-height: 52px; border-radius: 14px; font-size: 17px; font-weight: 700; box-sizing: border-box; }
.mk-plus-note { font-size: 12px; color: var(--sub); text-align: center; margin-top: -10px; }
.st-key-reset_ask [data-testid="stBaseButton-secondary"] { min-height: 48px; border-radius: 14px; }

/* ---------- 광고 자리 ---------- */
.mk-ad {
  height: 56px; border-radius: 12px; border: 1.5px dashed var(--line-2); background: transparent;
  display: grid; place-items: center; font-size: 12px; color: var(--sub);
  margin-top: calc(var(--gap-out) - var(--gap-in));
}

/* ---------- 소화 완료 연출 (전체 화면) ---------- */
.st-key-sheet_done {
  position: fixed; top: 0; bottom: 0; left: 50%; transform: translateX(-50%);
  width: min(100%, 430px); z-index: 300; background: var(--cream);
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
  width: min(100%, 430px); z-index: 400; background: var(--brand);
  justify-content: center; align-items: center; gap: 0 !important; padding: 0 16px;
}
.st-key-sheet_splash > [data-testid="stElementContainer"]:has(.stButton) {
  position: absolute; inset: 0; z-index: 2; margin: 0; width: 100% !important; height: 100% !important; max-width: none !important;
}
.st-key-sheet_splash .stButton, .st-key-sheet_splash .stButton button { width: 100%; height: 100%; min-height: 0; }
.st-key-sheet_splash .stButton button { opacity: 0; cursor: pointer; }
/* 스플래시: 브랜드 가이드 앱 화면처럼 주황 바탕 + 흰 마스코트 */
.stApp .mk-splash-logo { display: block; margin: 0 auto; width: 128px; height: 125px; background-image: url("MASCOT_WHITE"); background-position: center; }

/* ---------- 로그인 · 회원가입 (PRD Q10: 큰 버튼 카카오 · 네이버 · 휴대폰 번호 / 원형 Google · Apple) ----------
   레퍼런스: 앳플리(브랜드 버튼 세로 쌓기 + "또는" 아래 원형 아이콘) · 메가MCG커피(위 그래픽 + 아래 버튼 묶음) · 써브웨이 */
/* 로그인 화면 배치: 화면 전체 높이를 쓰고, 로고 묶음은 남는 위쪽 공간의 정가운데, 버튼 묶음은 아래(엄지가 닿는 곳)에 붙인다 */
.stApp:has(.mk-login-hero) [data-testid="stMainBlockContainer"] { padding-bottom: calc(20px + var(--safe-bottom)) !important; }
.stApp:has(.mk-login-hero) [data-testid="stMainBlockContainer"] > [data-testid="stVerticalBlock"] {
  min-height: calc(100dvh - 24px - var(--safe-top) - var(--safe-bottom));
}
[data-testid="stElementContainer"]:has(.mk-login-hero) { flex: 1 1 auto; display: flex; align-items: center; justify-content: center; }
.mk-login-hero { text-align: center; padding: 24px 0; }
@media (max-height: 700px) {  /* SE 등 낮은 화면: 스크롤 없이 한 화면에 */
  .mk-login-hero { padding: 0; }
  .stApp:has(.mk-login-hero) [data-testid="stMainBlockContainer"] { padding-bottom: calc(8px + var(--safe-bottom)) !important; }
  .stApp:has(.mk-login-hero) [data-testid="stMainBlockContainer"] > [data-testid="stVerticalBlock"] { min-height: calc(100dvh - 12px - var(--safe-top) - var(--safe-bottom)); }
}
.stApp .mk-login-logo { width: 196px; height: 54px; background-position: center; }
.mk-login-copy { font-size: 16px; line-height: 1.5; color: var(--sub); margin-top: 12px; }
.mk-login-note { font-size: 12px; color: var(--sub); text-align: center; margin-top: 6px; }
/* 큰 브랜드 버튼: 높이 52px · 모서리 14px · 16px/700. 아이콘은 왼쪽 18px에 고정, 글자는 가운데 */
.st-key-auth_btns { gap: 10px !important; }
.st-key-auth_kakao button, .st-key-auth_naver button, .st-key-auth_phone button {
  position: relative; height: 52px; min-height: 52px; border-radius: 14px; font-size: 16px; font-weight: 700; box-sizing: border-box;
}
.st-key-auth_kakao button::before, .st-key-auth_apple button::before, .st-key-auth_phone button::before,
.st-key-auth_naver button::before, .st-key-auth_google button::before {
  content: ""; width: 22px; height: 22px; background: var(--icon) center / contain no-repeat;
}
.st-key-auth_kakao button::before, .st-key-auth_naver button::before, .st-key-auth_phone button::before {
  position: absolute; left: 18px; top: 50%; transform: translateY(-50%);
}
.st-key-auth_kakao button { background: #FEE500; color: rgba(0, 0, 0, .85); border: 0; }
.st-key-auth_kakao { --icon: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'><path fill='%23191919' d='M12 3C6.48 3 2 6.48 2 10.8c0 2.78 1.86 5.22 4.66 6.6l-.95 3.48c-.08.3.26.55.52.38l4.15-2.74c.53.06 1.07.09 1.62.09 5.52 0 10-3.49 10-7.8S17.52 3 12 3z'/></svg>"); }
.st-key-auth_apple { --icon: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'><path fill='white' d='M16.37 1.43c0 1.14-.49 2.27-1.18 3.08-.74.9-1.99 1.57-2.99 1.57-.12 0-.23-.02-.3-.03-.01-.06-.04-.22-.04-.39 0-1.15.57-2.27 1.21-2.98.8-.94 2.14-1.64 3.25-1.68.03.13.05.28.05.43zm4.56 15.71c-.03.07-.46 1.58-1.52 3.12-.94 1.34-1.94 2.71-3.43 2.71-1.52 0-1.9-.88-3.63-.88-1.7 0-2.3.91-3.67.91-1.38 0-2.33-1.26-3.43-2.8C4 18.38 2.96 15.57 2.96 12.92c0-4.28 2.8-6.55 5.55-6.55 1.45 0 2.68.95 3.6.95.87 0 2.22-1.01 3.9-1.01.61 0 2.89.06 4.37 2.19-.13.09-2.38 1.37-2.38 4.19 0 3.26 2.85 4.42 2.95 4.45z'/></svg>"); }
.st-key-auth_phone button { background: #FFFFFF; color: var(--ink); border: 1.5px solid var(--line); }
.st-key-auth_phone { --icon: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%231E2530' stroke-width='1.8' stroke-linecap='round'><rect x='6.5' y='2.5' width='11' height='19' rx='2.6'/><path d='M10.5 18.3h3'/></svg>"); }
.st-key-auth_naver button { background: #03C75A; color: #FFFFFF; border: 0; }
/* "또는" 구분선 + 원형 아이콘 버튼 52px (Google 흰색 · Apple 검정). 글자는 숨기고 스크린리더만 읽는다 */
.mk-or { display: flex; align-items: center; gap: 12px; font-size: 13px; color: var(--sub); margin: 10px 0 2px; }
.mk-or::before, .mk-or::after { content: ""; flex: 1; height: 1px; background: var(--line); }
.st-key-auth_more { justify-content: center; gap: 16px !important; flex-wrap: nowrap !important; }
.st-key-auth_more > [data-testid="stElementContainer"] { width: auto !important; flex: none !important; }
.st-key-auth_google button, .st-key-auth_apple button {
  width: 52px; height: 52px; min-height: 52px; padding: 0; border-radius: 50%; box-sizing: border-box;
}
.st-key-auth_google button, .st-key-auth_apple button { justify-content: center; }
/* 글자 칸은 화면에서 빼서(스크린리더만 읽음) 아이콘이 원 정가운데에 오게 한다 */
.st-key-auth_google button > div, .st-key-auth_apple button > div {
  position: absolute; width: 1px; height: 1px; overflow: hidden; clip: rect(0 0 0 0); white-space: nowrap;
}
.st-key-auth_apple button { background: #000000; border: 0; }
.st-key-auth_naver { --icon: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'><path fill='white' d='M15.6 12.8 8.2 2.5H3v19h5.4V11.2l7.4 10.3H21v-19h-5.4z'/></svg>"); }
.st-key-auth_naver button::before { width: 18px; height: 18px; left: 20px; }
.st-key-auth_google button { background: #FFFFFF; border: 1.5px solid var(--line); }
.st-key-auth_google { --icon: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 48 48'><path fill='%23EA4335' d='M24 9.5c3.54 0 6.71 1.22 9.21 3.6l6.85-6.85C35.9 2.38 30.47 0 24 0 14.62 0 6.51 5.38 2.56 13.22l7.98 6.19C12.43 13.72 17.74 9.5 24 9.5z'/><path fill='%234285F4' d='M46.98 24.55c0-1.57-.15-3.09-.38-4.55H24v9.02h12.94c-.58 2.96-2.26 5.48-4.78 7.18l7.73 6c4.51-4.18 7.09-10.36 7.09-17.65z'/><path fill='%23FBBC05' d='M10.53 28.59c-.48-1.45-.76-2.99-.76-4.59s.27-3.14.76-4.59l-7.98-6.19C.92 16.46 0 20.12 0 24c0 3.88.92 7.54 2.56 10.78l7.97-6.19z'/><path fill='%2334A853' d='M24 48c6.48 0 11.93-2.13 15.89-5.81l-7.73-6c-2.15 1.45-4.92 2.3-8.16 2.3-6.26 0-11.57-4.22-13.47-9.91l-7.98 6.19C6.51 42.62 14.62 48 24 48z'/></svg>"); }
/* 회원가입 입력칸: 온보딩 몸무게 칸과 같은 모양 (56px · 14px · 연회색 → 포커스 시 흰색 + 남색 테두리) */
[class*="st-key-auth_in_"] [data-testid="stTextInputRootElement"] {
  height: 56px; min-height: 56px; border-radius: 14px; background: var(--soft); border: 2px solid transparent; box-sizing: border-box;
}
[class*="st-key-auth_in_"] [data-testid="stTextInputRootElement"]:focus-within { border-color: var(--ink); background: #FFFFFF; }
[class*="st-key-auth_in_"] input { height: 100%; min-height: 0; padding: 0 16px; font-size: 18px; font-weight: 600; color: var(--ink); background: transparent; }
[class*="st-key-auth_in_"] input::placeholder { font-size: 16px; font-weight: 400; color: var(--sub); }
[class*="st-key-auth_in_"] input:focus-visible { outline: none !important; }
[class*="st-key-auth_in_"] [data-testid="InputInstructions"] { display: none; }
/* 약관: "전체 동의" 카드(선택 시 흰색 + 남색 테두리) 아래, 연회색 목록 카드 안에 [선택 원 · 필수/선택 · 약관 이름] 줄 */
.mk-term-all { display: flex; align-items: center; gap: 12px; padding: 16px; }
.mk-term-all-title { font-size: 17px; font-weight: 700; color: var(--ink); }
.mk-term-all-sub { font-size: 13px; color: var(--sub); margin-top: 2px; }
.mk-card.mk-term, .mk-card.mk-term.sel { display: flex; align-items: center; gap: 10px; min-height: 52px; padding: 4px 0; background: transparent; border-color: transparent; }
.mk-term-tag { flex: none; font-size: 12px; font-weight: 700; color: var(--sub); border: 1px solid var(--line); border-radius: 999px; padding: 2px 8px; background: #FFFFFF; }
.mk-term-tag.req { color: var(--ink); border-color: var(--ink); }
.mk-term-label { font-size: 15px; color: var(--ink); min-width: 0; }
.st-key-list_terms { padding: 2px 14px !important; }

/* ---------- 로그인 · 회원가입 인터랙션 ---------- */
/* 브랜드 버튼은 hover·누름에서도 제 색을 지킨다 (기본 보조 버튼 hover가 흰 바탕으로 바꾸던 문제) */
@media (hover: hover) and (pointer: fine) {
  .st-key-auth_kakao button:hover { background: #FEE500; color: rgba(0, 0, 0, .85); border-color: transparent; filter: brightness(.97); }
  .st-key-auth_naver button:hover { background: #03C75A; color: #FFFFFF; border-color: transparent; filter: brightness(.97); }
  .st-key-auth_apple button:hover { background: #000000; border-color: transparent; }
  .st-key-auth_google button:hover, .st-key-auth_phone button:hover { background: #FFFFFF; border-color: var(--ink); }
}
/* 스플래시 다음 첫 화면: 위치 이동 없이 그림·로고 → 버튼 순으로 서서히 (스플래시와의 뚝 끊김을 잇는다) */
.mk-login-hero.mk-login-first { animation: mk-fade .24s ease-out both; }
.stApp:has(.mk-login-first) .st-key-auth_btns > * { animation: mk-fade .24s ease-out both; }
.stApp:has(.mk-login-first) .st-key-auth_btns > :nth-child(1) { animation-delay: .06s; }
.stApp:has(.mk-login-first) .st-key-auth_btns > :nth-child(2) { animation-delay: .1s; }
.stApp:has(.mk-login-first) .st-key-auth_btns > :nth-child(3) { animation-delay: .14s; }
.stApp:has(.mk-login-first) .st-key-auth_btns > :nth-child(n+4) { animation-delay: .18s; }
.mk-login-hero.mk-back { animation: mk-in-back .24s var(--ease-move); }
/* 인증번호 칸: "인증번호 받기"를 누르면 휴대폰 칸 아래에서 살짝 올라오며 나타난다 */
.st-key-auth_in_code { animation: mk-rise .24s var(--ease-enter); }
/* 오류: 칸 테두리 빨강 + 좌우 흔들림(실패할 때마다 다시: 같은 모양 키프레임 두 개를 번갈아 씀) + 문구는 서서히 */
@keyframes mk-shake-0 { 20%, 60% { transform: translateX(-4px); } 40%, 80% { transform: translateX(4px); } }
@keyframes mk-shake-1 { 20%, 60% { transform: translateX(-4px); } 40%, 80% { transform: translateX(4px); } }
.mk-error-in { animation: mk-fade .15s ease-out; }
/* 전체 동의를 켜면 목록 체크가 위에서 아래로 35ms 간격으로 차례로 (전체 175ms) */
.mk-term.mk-cascade.sel .mk-pick { animation-delay: calc(var(--i) * 35ms); animation-fill-mode: both; }
@media (prefers-reduced-motion: reduce) {
  .mk-login-hero.mk-back, .st-key-auth_in_code { animation: mk-fade .15s linear both; }
  .stApp:has(.mk-login-first) .st-key-auth_btns > :nth-child(n) { animation-delay: 0s; }
  [class*="st-key-auth_in_"] [data-testid="stTextInputRootElement"] { animation: none !important; }  /* 흔들림 대신 빨간 테두리만 */
  .mk-term.mk-cascade.sel .mk-pick { animation-delay: 0s; }
}

/* ---------- 브랜드 표면: 크림 바탕 위 흰 카드 + 은은한 그림자 ---------- */
.mk-card, .mk-summary, .mk-favs, .st-key-empty_box, .mk-meal, .mk-q:not(.mk-q-add), .mk-fr, .mk-fz-list, .mk-gift-to,
[class*="st-key-list_"], .mk-empty-line, .mk-note-box, .mk-idcard, .st-key-confirm_box, .mk-lock, .mk-my-stats,
.mk-gift-stats .mk-stat, .st-key-plus_box, .mk-today, .mk-rel,
.st-key-ob_weight [data-testid="stNumberInputContainer"], .st-key-ob_height [data-testid="stNumberInputContainer"], .st-key-my_weight [data-testid="stNumberInputContainer"],
.st-key-cm_query [data-testid="stTextInputRootElement"], [class*="st-key-auth_in_"] [data-testid="stTextInputRootElement"] { box-shadow: var(--shadow); }
.mk-card.mk-term, .mk-q.mk-q-add { box-shadow: none; }
/* 빈 상태(홈 "주문하러 가요" · 냉장고 · 배달): 카드 위에 빼꼼 내다보는 마스코트 */
.st-key-empty_box::before {
  content: ""; display: block; align-self: center; width: 112px; height: 86px; margin-bottom: -6px;
  background: url("MASCOT_PEEK") center bottom / contain no-repeat;
}

/* 가로 캐러셀 마우스 스크롤 스크립트 칸: 배치에 자리를 차지하지 않게 */
.st-key-js_dragscroll { position: absolute !important; width: 0; height: 0; overflow: hidden; }

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

:focus-visible { outline: 3px solid var(--ink) !important; outline-offset: 2px; }
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
  content: ""; position: absolute; inset: 0; border-radius: inherit; background: var(--brand);
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
"""
for _token, _value in (
    ("CHECK_WHITE", _CHECK_WHITE),
    ("BRAND_LOGO", _brand_uri("logo")),
    ("MASCOT_WHITE", _brand_uri("mascot_white")),
    ("MASCOT_PEEK", _brand_uri("mascot_peek")),
):
    _CSS = _CSS.replace(_token, _value)


# 가로 캐러셀(친구·조리 중)을 마우스로도 넘길 수 있게 하는 스크립트. 터치(아이폰)는 원래 손가락으로 넘어가므로 손대지 않는다.
# - 세로 휠·트랙패드 → 가로로 넘김 (캐러셀 끝에 닿으면 페이지 스크롤로 넘김)
# - 마우스로 끌기 → 넘김, 5px 넘게 끌었으면 손을 뗄 때 카드가 눌리지 않게 클릭을 막는다
# Streamlit이 다시 그려도 새로 생긴 줄에 붙도록 MutationObserver로 지켜본다. 부모 문서에 한 번만 설치한다.
_DRAG_SCROLL_CODE = """
(() => {
  if (window.__mkDragScroll) return;
  window.__mkDragScroll = true;
  const SEL = '.st-key-row_friends, .st-key-row_queue';
  const bind = (row) => {
    if (row.dataset.mkDrag) return;
    row.dataset.mkDrag = '1';
    row.addEventListener('wheel', (e) => {
      if (Math.abs(e.deltaX) > Math.abs(e.deltaY)) return;  // 이미 가로 스크롤(트랙패드)
      const max = row.scrollWidth - row.clientWidth;
      if (max <= 0) return;
      const atStart = row.scrollLeft <= 0 && e.deltaY < 0, atEnd = row.scrollLeft >= max - 1 && e.deltaY > 0;
      if (atStart || atEnd) return;  // 캐러셀 끝이면 페이지 스크롤로 넘긴다
      row.scrollBy({ left: e.deltaY, behavior: 'smooth' });
      e.preventDefault();
    }, { passive: false });
    let startX = 0, startLeft = 0, moved = false, down = false;
    row.addEventListener('pointerdown', (e) => {
      if (e.pointerType !== 'mouse' || e.button !== 0) return;
      down = true; moved = false; startX = e.clientX; startLeft = row.scrollLeft;
    });
    window.addEventListener('pointermove', (e) => {
      if (!down) return;
      const dx = e.clientX - startX;
      if (!moved && Math.abs(dx) > 5) { moved = true; row.classList.add('mk-dragging'); }
      if (moved) row.scrollLeft = startLeft - dx;
    });
    window.addEventListener('pointerup', () => {
      if (!down) return;
      down = false;
      if (moved) {
        row.classList.remove('mk-dragging');  // 끌기가 끝나면 다시 카드 시작점에 맞춰 멈춘다
        setTimeout(() => { moved = false; }, 0);
      }
    });
    row.addEventListener('click', (e) => {
      if (moved) { e.preventDefault(); e.stopPropagation(); }
    }, true);
  };
  const scan = () => document.querySelectorAll(SEL).forEach(bind);
  scan();
  new MutationObserver(scan).observe(document.body, { childList: true, subtree: true });
})();
"""
# 컴포넌트 iframe은 화면이 바뀌면 사라지므로, 코드를 부모 문서에 <script>로 넣어 부모 쪽에서 계속 돌게 한다
_DRAG_SCROLL_JS = (
    "<script>(() => { const d = window.parent.document;"
    " if (d.getElementById('mk-drag-scroll')) return;"
    " const s = d.createElement('script'); s.id = 'mk-drag-scroll'; s.textContent = "
    + json.dumps(_DRAG_SCROLL_CODE)
    + "; d.head.appendChild(s); })();</script>"
)


def enable_drag_scroll() -> None:
    """가로 캐러셀에 마우스 휠·끌기 스크롤을 붙인다 (app.py에서 매번 부른다. 설치는 한 번만 된다)."""
    with st.container(key="js_dragscroll"):
        components.html(_DRAG_SCROLL_JS, height=0)


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
