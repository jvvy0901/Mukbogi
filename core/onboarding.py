"""온보딩 화면. PRD.md Epic 1 (Story 1.1 ~ 1.3)을 구현한다.

1단계: 식사량 유형 선택 (Story 1.1)
2단계: 소화하고 싶은 음식 선택 (Story 1.2)
3단계: 체중 입력, 건너뛸 수 있음 (Story 1.3)

Story 1.4(움직임 측정 권한 안내)는 프로토타입 대체 방식이 PRD에 정해지지 않아 아직 넣지 않았다.
"""

from html import escape

import streamlit as st

from core.data import FOODS, FOODS_BY_ID
from core.images import food_thumb
from core.rules import DEFAULT_WEIGHT_KG, EATER_TYPES, daily_targets, food_groups
from core.style import html

TOTAL_STEPS = 3
TYPE_KEYS = {"대식가": "big", "중식가": "mid", "소식가": "small"}

# Streamlit은 화면에 그려지지 않은 위젯의 값을 지운다. 그래서 단계를 오가도 선택이 남도록
# 고른 값은 위젯 키(ob_weight)와 별도인 키(ob_foods, ob_weight_saved)에 저장한다.


def _init_state() -> None:
    ss = st.session_state
    ss.setdefault("ob_step", 0)
    ss.setdefault("ob_type", None)
    ss.setdefault("ob_foods", [])
    ss.setdefault("ob_weight_saved", None)
    ss.setdefault("ob_weight_error", False)


# 상태 변경 콜백 ---------------------------------------------------------------


def _go(step: int) -> None:
    st.session_state.ob_step = step


def _choose_type(eater_type: str) -> None:
    st.session_state.ob_type = eater_type


def _toggle_food(food_id: str) -> None:
    selected = set(st.session_state.ob_foods)
    selected ^= {food_id}
    st.session_state.ob_foods = [f.id for f in FOODS if f.id in selected]


def _save_weight() -> None:
    st.session_state.ob_weight_saved = st.session_state.ob_weight
    st.session_state.ob_weight_error = False


def _finish(weight_kg: float | None) -> None:
    ss = st.session_state
    targets = daily_targets(FOODS)
    ss.profile = {
        "eater_type": ss.ob_type,
        "daily_target_kcal": targets[ss.ob_type],
        "favorite_food_ids": list(ss.ob_foods),
        "weight_kg": weight_kg,  # None이면 기본값으로 계산
    }


def _start_with_weight() -> None:
    weight = st.session_state.get("ob_weight")
    if weight is None:
        st.session_state.ob_weight_error = True
        return
    st.session_state.ob_weight_saved = weight
    _finish(weight)


def _skip_weight() -> None:
    _finish(None)


# 공통 조각 -------------------------------------------------------------------


def _top(step: int, title: str, sub: str) -> None:
    """상단 내비게이션 줄 + 머리말. 모든 단계에서 같은 위치·높이로 그린다 (연속성)."""
    bars = "".join(f'<span class="{"on" if i <= step else ""}"></span>' for i in range(TOTAL_STEPS))
    with st.container(key="nav_row", horizontal=True, vertical_alignment="center"):
        if step == 0:
            html('<div class="mk-nav-slot"></div>')
        else:
            st.button("이전", key=f"ob_back_{step}", type="tertiary", on_click=_go, args=(step - 1,))
        html(f'<div class="mk-progress" aria-hidden="true">{bars}</div>')
        html(f'<p class="mk-step" aria-label="{TOTAL_STEPS}단계 중 {step + 1}단계">{step + 1}/{TOTAL_STEPS}</p>')
    html(
        '<div class="mk-header">'
        f'<div class="mk-title" role="heading" aria-level="1">{title}</div>'
        f'<p class="mk-sub">{sub}</p>'
        "</div>"
    )


# 1단계 ---------------------------------------------------------------------


def _step_type() -> None:
    _top(0, "하루에 얼마나<br>먹고 싶어요?", "고른 유형에 맞춰 하루 목표 칼로리가 정해져요.")

    groups = food_groups(FOODS)
    targets = daily_targets(FOODS)
    chosen = st.session_state.ob_type

    for eater_type in EATER_TYPES:
        foods = groups[eater_type]
        thumbs = "".join(f'<img src="{food_thumb(f)}" alt="">' for f in foods)
        names = " · ".join(f.name for f in foods)
        sel = " sel" if chosen == eater_type else ""
        with st.container(key=f"tap_type_{TYPE_KEYS[eater_type]}"):
            html(
                f'<div class="mk-card mk-type{sel}">'
                f'<div class="mk-thumbs">{thumbs}</div>'
                f'<div class="mk-type-text">'
                f'<div class="mk-type-name">{eater_type}</div>'
                f'<div class="mk-type-goal">하루 목표 <b>{targets[eater_type]}kcal</b></div>'
                f'<div class="mk-type-ex">{names}</div>'
                f"</div>"
                f'<div class="mk-pick" aria-hidden="true"></div>'
                f"</div>"
            )
            st.button(
                f"{eater_type} 선택하기",
                key=f"ob_pick_{TYPE_KEYS[eater_type]}",
                on_click=_choose_type,
                args=(eater_type,),
            )

    with st.container(key="bar_footer"):
        if chosen is None:
            html('<p class="mk-hint">유형을 하나 골라 주세요</p>')
        st.button(
            "다음",
            key="ob_next_0",
            type="primary",
            width="stretch",
            disabled=chosen is None,
            on_click=_go,
            args=(1,),
        )


# 2단계 ---------------------------------------------------------------------


def _step_foods() -> None:
    _top(1, "어떤 음식을<br>소화하고 싶어요?", "여러 개 골라도 돼요. 고른 음식은 주문할 때 먼저 추천해 드려요.")

    selected = st.session_state.ob_foods
    html(f'<p class="mk-count" aria-live="polite">{len(selected)}개 골랐어요</p>')

    with st.container(key="grid_food"):
        for food in FOODS:
            is_sel = food.id in selected
            with st.container(key=f"tap_food_{food.id}"):
                html(
                    f'<div class="mk-card mk-food{" sel" if is_sel else ""}">'
                    f'<div class="mk-pick" aria-hidden="true"></div>'
                    f'<img src="{food_thumb(food)}" alt="">'
                    f'<div class="mk-food-name">{escape(food.name)}</div>'
                    f'<div class="mk-food-kcal">{food.kcal}kcal</div>'
                    f"</div>"
                )
                st.button(
                    f"{food.name} {'빼기' if is_sel else '고르기'}",
                    key=f"ob_food_{food.id}",
                    on_click=_toggle_food,
                    args=(food.id,),
                )

    with st.container(key="bar_footer"):
        if not selected:
            html('<p class="mk-hint">음식을 1개 이상 골라 주세요</p>')
        st.button(
            "다음",
            key="ob_next_1",
            type="primary",
            width="stretch",
            disabled=not selected,
            on_click=_go,
            args=(2,),
        )


# 3단계 ---------------------------------------------------------------------


def _step_weight() -> None:
    _top(
        2,
        "칼로리를 더 정확하게<br>계산할게요",
        "체중을 알려 주면 움직인 만큼 소모한 칼로리를 더 정확하게 계산해요.",
    )

    st.number_input(
        "체중",
        min_value=20.0,
        max_value=250.0,
        step=0.5,
        format="%.1f",
        value=st.session_state.ob_weight_saved,
        placeholder=f"예: {DEFAULT_WEIGHT_KG}",
        key="ob_weight",
        on_change=_save_weight,
    )
    if st.session_state.ob_weight_error:
        html('<p class="mk-error" role="alert">체중을 입력하거나 건너뛰기를 눌러 주세요.</p>')
    html(
        f'<p class="mk-note">체중은 나만 볼 수 있어요. '
        f"건너뛰면 {DEFAULT_WEIGHT_KG}kg 기준으로 계산하고, 나중에 설정에서 바꿀 수 있어요.</p>"
    )

    with st.container(key="bar_footer"):
        st.button(
            "MUKBOGI 시작하기",
            key="ob_start",
            type="primary",
            width="stretch",
            on_click=_start_with_weight,
        )
        st.button("건너뛰기", key="ob_skip", type="tertiary", width="stretch", on_click=_skip_weight)


_STEPS = (_step_type, _step_foods, _step_weight)


def render() -> None:
    _init_state()
    _STEPS[st.session_state.ob_step]()


# 완료 -------------------------------------------------------------------------


def render_done() -> None:
    """온보딩 결과 확인 화면. 홈 화면을 만들기 전까지 임시로 쓴다."""
    profile = st.session_state.profile
    weight = profile["weight_kg"]
    weight_text = f"{weight:g}kg" if weight is not None else f"입력 안 함 ({DEFAULT_WEIGHT_KG}kg 기준)"
    favs = "".join(
        f'<div class="mk-fav"><img src="{food_thumb(FOODS_BY_ID[i])}" alt="">{escape(FOODS_BY_ID[i].name)}</div>'
        for i in profile["favorite_food_ids"]
    )

    # 상단 줄은 온보딩 단계와 같은 높이(44px)에 둔다 (연속성)
    html('<p class="mk-wordmark">MUKBOGI</p>')
    html(
        '<div class="mk-header">'
        '<div class="mk-title" role="heading" aria-level="1">준비 끝났어요!</div>'
        '<p class="mk-sub">이제 먹고 싶은 음식을 주문하고 움직여서 소화해 봐요.</p>'
        "</div>"
    )
    html(
        '<div class="mk-summary">'
        f'<div class="mk-row"><span>식사량 유형</span><span>{profile["eater_type"]}</span></div>'
        f'<div class="mk-row"><span>하루 목표</span><span>{profile["daily_target_kcal"]}kcal</span></div>'
        f'<div class="mk-row"><span>체중</span><span>{weight_text}</span></div>'
        "</div>"
    )
    # 섹션 제목과 음식 목록을 한 영역으로 묶는다 (공통 영역)
    html('<p class="mk-section">소화하고 싶은 음식</p>')
    html(f'<div class="mk-favs">{favs}</div>')

    with st.container(key="bar_footer"):
        html('<p class="mk-hint">홈 화면은 다음 단계에서 만들어요</p>')
        st.button("온보딩 다시 하기", key="ob_reset", type="tertiary", width="stretch", on_click=reset)


def reset() -> None:
    for key in list(st.session_state.keys()):
        if key.startswith("ob_") or key == "profile":
            del st.session_state[key]
