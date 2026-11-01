"""내정보 화면 (하단 탭 "내정보"). PRD Q17 초안 구성.

- 프로필 요약: 내 아이디, 이번 주 소화 칼로리, 지금까지 소화한 음식 수, 친구 수
- 식사량 유형 (Story 1.1 "이후 설정에서 바꿀 수 있다") — 바꾸면 하루 목표 칼로리가 바로 바뀐다
- 몸무게 (Story 1.3 "설정에서 수정할 수 있다") — 입력 전에는 60kg 기준, 나만 볼 수 있다
- 내 냉장고 공개 범위 (Story 5.3) — 전체 / 친구만(기본) / 비공개
- MUKBOGI 플러스 (Story 6.2, 프로토타입: 결제 없이 켜고 끄기) — 켜면 광고가 사라진다
- 온보딩 다시 하기 (프로토타입 전용, 확인 후 모든 기록을 지운다)
"""

from datetime import datetime
from html import escape

import streamlit as st

from core import meal, social
from core.data import FOODS
from core.demo import ME_ID, ME_NAME
from core.rules import DEFAULT_WEIGHT_KG, EATER_TYPES, daily_targets
from core.style import html, toast

TYPE_KEYS = {"대식가": "big", "중식가": "mid", "소식가": "small"}
VISIBILITY = (("all", "전체"), ("friends", "친구만"), ("private", "비공개"))
VISIBILITY_HELP = {
    "전체": "누구나 내 냉장고를 볼 수 있어요.",
    "친구만": "친구만 내 냉장고를 볼 수 있어요.",
    "비공개": "아무도 내 냉장고를 볼 수 없어요. 랭킹에는 그대로 나와요.",
}


# 상태 · 콜백 ------------------------------------------------------------------


def _profile() -> dict:
    p = st.session_state.profile
    p.setdefault("fridge_visibility", "친구만")  # PRD Q6 초안
    return p


def _set_type(eater_type: str) -> None:
    p = _profile()
    p["eater_type"] = eater_type
    p["daily_target_kcal"] = daily_targets(FOODS)[eater_type]
    toast(f"{eater_type}로 바꿨어요 · 하루 목표 {p['daily_target_kcal']}kcal")


def _save_weight() -> None:
    w = st.session_state.get("my_weight")
    if w is None:
        return
    _profile()["weight_kg"] = w
    toast("몸무게를 저장했어요")


def _set_visibility(label: str) -> None:
    _profile()["fridge_visibility"] = label
    toast(f"내 냉장고를 '{label}'로 바꿨어요")


def _set_plus(on: bool) -> None:
    st.session_state.plus = on
    toast("MUKBOGI 플러스를 시작했어요 · 광고가 사라져요" if on else "MUKBOGI 플러스를 해지했어요")


def _ask_reset(on: bool) -> None:
    st.session_state.confirm_reset = on


def _reset_all() -> None:
    """프로토타입 전용: 모든 기록을 지우고 온보딩부터 다시 한다."""
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.session_state.splash_seen = True  # 스플래시는 앱을 처음 열 때만 보인다


# 화면 조각 -------------------------------------------------------------------


def _segment(container_key: str, prefix: str, items, active_key: str, on_click) -> None:
    html(
        f"<style>.st-key-{prefix}_{active_key} button {{ background: #FFFFFF !important; color: var(--ink) !important; "
        "box-shadow: 0 1px 3px rgba(30, 37, 48, .14); }</style>"
    )
    with st.container(key=container_key, horizontal=True):
        for key, label, arg in items:
            st.button(label, key=f"{prefix}_{key}", type="tertiary", on_click=on_click, args=(arg,))


def _section(title: str) -> None:
    html(f'<div class="mk-section" role="heading" aria-level="2">{title}</div>')


def _header(state: meal.MealState) -> None:
    now = datetime.now()
    week_kcal = social.weekly_kcal(state.fridge, now.date())
    friends = len(st.session_state.social.friends) if "social" in st.session_state else 0
    plus = '<span class="mk-plus-pill">플러스</span>' if st.session_state.get("plus") else ""
    html(
        '<div class="mk-prof">'
        f'<span class="mk-avatar mk-avatar-xl mk-avatar-initial" aria-hidden="true">{ME_NAME}</span>'
        '<div class="mk-u-text">'
        f'<div class="mk-prof-name">{ME_NAME}{plus}</div>'
        f'<div class="mk-u-id">@{ME_ID}</div>'
        "</div></div>"
        '<dl class="mk-stats mk-my-stats">'
        f'<div class="mk-stat"><dt>이번 주</dt><dd>{week_kcal:,}<small>kcal</small></dd></div>'
        f'<div class="mk-stat"><dt>소화한 음식</dt><dd>{len(state.fridge)}<small>개</small></dd></div>'
        f'<div class="mk-stat"><dt>친구</dt><dd>{friends}<small>명</small></dd></div>'
        "</dl>"
    )


# 진입 -------------------------------------------------------------------------


def render(state: meal.MealState) -> None:
    ss = st.session_state
    ss.setdefault("social", social.SocialState())
    ss.setdefault("plus", False)
    ss.setdefault("confirm_reset", False)
    p = _profile()

    html('<div class="mk-topbar"><span class="mk-wordmark">MUKBOGI</span></div>')
    html('<div class="mk-header"><div class="mk-title" role="heading" aria-level="1">내정보</div></div>')
    _header(state)

    # 식사량 유형
    _section("식사량 유형")
    targets = daily_targets(FOODS)
    _segment("seg_mytype", "mtype", [(TYPE_KEYS[t], t, t) for t in EATER_TYPES], TYPE_KEYS[p["eater_type"]], _set_type)
    html(f'<div class="mk-my-note">하루 목표 <b>{targets[p["eater_type"]]}kcal</b> · 바꾸면 바로 적용돼요</div>')

    # 몸무게
    _section("몸무게")
    st.number_input(
        "몸무게", min_value=20.0, max_value=250.0, step=0.5, format="%.1f",
        value=p.get("weight_kg"), placeholder=f"예: {DEFAULT_WEIGHT_KG}",
        key="my_weight", on_change=_save_weight, label_visibility="collapsed",
    )
    html(
        f'<div class="mk-my-note">소모 칼로리를 계산할 때만 써요. 입력하지 않으면 {DEFAULT_WEIGHT_KG}kg 기준으로 계산하고, '
        "나만 볼 수 있어요.</div>"
    )

    # 내 냉장고 공개 범위
    _section("내 냉장고 공개 범위")
    vis = p["fridge_visibility"]
    active = next(k for k, label in VISIBILITY if label == vis)
    _segment("seg_myvis", "mvis", [(k, label, label) for k, label in VISIBILITY], active, _set_visibility)
    html(f'<div class="mk-my-note">{escape(VISIBILITY_HELP[vis])}</div>')

    # MUKBOGI 플러스
    _section("MUKBOGI 플러스")
    plus_on = ss.plus
    with st.container(key="plus_box"):
        state = '<span class="mk-plus-badge on">이용 중</span>' if plus_on else '<span class="mk-plus-badge">무료 이용 중</span>'
        title = "광고 없이 쓰고 있어요" if plus_on else "광고 없이 소화에만 집중해요"
        html(
            f'<div class="mk-plus-head">{state}<div class="mk-plus-title">{title}</div></div>'
            '<ul class="mk-plus-perks">'
            '<li><i class="mk-perk-ico mk-ico-noad" aria-hidden="true"></i>'
            '<span>광고 없이 쓰기</span></li>'
            '<li><i class="mk-perk-ico mk-ico-report" aria-hidden="true"></i>'
            "<span>주간·월간 소화 리포트</span><span class='mk-soon'>준비 중</span></li>"
            "</ul>"
        )
        if plus_on:
            st.button("플러스 해지하기", key="plus_off", type="secondary", width="stretch", on_click=_set_plus, args=(False,))
        else:
            st.button("플러스 시작하기", key="plus_on", type="primary", width="stretch", on_click=_set_plus, args=(True,))
        html('<div class="mk-plus-note">프로토타입이라 실제로 결제되지 않아요.</div>')

    # 프로토타입 전용
    _section("프로토타입")
    if ss.confirm_reset:
        with st.container(key="confirm_box"):
            html(
                '<div class="mk-confirm-title">온보딩부터 다시 할까요?</div>'
                '<div class="mk-confirm-sub">주문·냉장고·친구·배달 기록이 모두 지워져요.</div>'
            )
            with st.container(key="confirm_btns", horizontal=True):
                st.button("다시 하기", key="reset_ok", type="primary", on_click=_reset_all)
                st.button("취소", key="reset_no", type="secondary", on_click=_ask_reset, args=(False,))
    else:
        st.button("온보딩 다시 하기", key="reset_ask", type="secondary", width="stretch", on_click=_ask_reset, args=(True,))
