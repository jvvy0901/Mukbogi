"""온보딩 화면. PRD.md Epic 1 (Story 1.1 ~ 1.3)을 구현한다.

1단계: 식사량 유형 선택 (Story 1.1)
2단계: 소화하고 싶은 음식 선택 (Story 1.2)
3단계: 체중 입력, 건너뛸 수 있음 (Story 1.3)

Story 1.4(움직임 측정 권한 안내)는 프로토타입 대체 방식이 PRD에 정해지지 않아 아직 넣지 않았다.
"""

import streamlit as st

from core.data import FOODS, FOODS_BY_ID
from core.rules import DEFAULT_WEIGHT_KG, EATER_TYPES, daily_targets, food_groups

TOTAL_STEPS = 3


# Streamlit은 화면에 그려지지 않은 위젯의 값을 지운다. 그래서 단계를 오가도 선택이 남도록
# 고른 값은 위젯 키(ob_food_*, ob_weight)와 별도인 키(ob_foods, ob_weight_saved)에 저장한다.


def _init_state() -> None:
    ss = st.session_state
    ss.setdefault("ob_step", 0)
    ss.setdefault("ob_type", None)
    ss.setdefault("ob_foods", [])
    ss.setdefault("ob_weight_saved", None)


def _go(step: int) -> None:
    st.session_state.ob_step = step


def _choose_type(eater_type: str) -> None:
    st.session_state.ob_type = eater_type


def _toggle_food(food_id: str) -> None:
    ss = st.session_state
    checked = ss[f"ob_food_{food_id}"]
    selected = set(ss.ob_foods)
    if checked:
        selected.add(food_id)
    else:
        selected.discard(food_id)
    ss.ob_foods = [f.id for f in FOODS if f.id in selected]


def _save_weight() -> None:
    st.session_state.ob_weight_saved = st.session_state.ob_weight


def _selected_food_ids() -> list[str]:
    return list(st.session_state.ob_foods)


def _finish(weight_kg: float | None) -> None:
    ss = st.session_state
    targets = daily_targets(FOODS)
    ss.profile = {
        "eater_type": ss.ob_type,
        "daily_target_kcal": targets[ss.ob_type],
        "favorite_food_ids": _selected_food_ids(),
        "weight_kg": weight_kg,  # None이면 기본값으로 계산
    }


def _header(step: int, title: str, help_text: str) -> None:
    st.markdown(
        f'<p class="mk-step">{step + 1} / {TOTAL_STEPS}단계</p>',
        unsafe_allow_html=True,
    )
    st.progress((step + 1) / TOTAL_STEPS)
    st.markdown(f'<h1 class="mk-section">{title}</h1>', unsafe_allow_html=True)
    st.markdown(f'<p class="mk-help">{help_text}</p>', unsafe_allow_html=True)


# 1단계 ---------------------------------------------------------------------


def _step_type() -> None:
    _header(0, "하루에 얼마나 먹고 싶어요?", "고른 유형에 맞춰 하루 목표 칼로리가 정해져요.")

    groups = food_groups(FOODS)
    targets = daily_targets(FOODS)
    chosen = st.session_state.ob_type

    for eater_type in EATER_TYPES:
        is_chosen = chosen == eater_type
        with st.container(border=True):
            top_left, top_right = st.columns([3, 2], vertical_alignment="center")
            with top_left:
                st.markdown(f"**{eater_type}**")
                st.markdown(
                    f'<span class="mk-kcal">하루 목표 {targets[eater_type]}kcal</span>',
                    unsafe_allow_html=True,
                )
            with top_right:
                if is_chosen:
                    st.markdown('<span class="mk-badge">선택했어요</span>', unsafe_allow_html=True)

            examples = groups[eater_type]
            img_cols = st.columns(len(examples))
            for col, food in zip(img_cols, examples):
                with col:
                    st.image(str(food.image_path), caption=f"{food.name} {food.kcal}kcal", width="stretch")

            st.button(
                f"{eater_type} 선택하기",
                key=f"ob_pick_{eater_type}",
                type="primary" if is_chosen else "secondary",
                width="stretch",
                on_click=_choose_type,
                args=(eater_type,),
            )

    st.button(
        "다음",
        key="ob_next_0",
        type="primary",
        width="stretch",
        disabled=chosen is None,
        on_click=_go,
        args=(1,),
    )
    if chosen is None:
        st.caption("유형을 하나 골라야 다음으로 넘어갈 수 있어요.")


# 2단계 ---------------------------------------------------------------------


def _step_foods() -> None:
    _header(
        1,
        "어떤 음식을 소화하고 싶어요?",
        "여러 개 골라도 돼요. 고른 음식은 주문할 때 먼저 추천해 드려요.",
    )

    for row_start in range(0, len(FOODS), 2):
        cols = st.columns(2)
        for col, food in zip(cols, FOODS[row_start : row_start + 2]):
            with col, st.container(border=True):
                st.image(str(food.image_path), width="stretch")
                st.checkbox(
                    f"{food.name} · {food.kcal}kcal",
                    key=f"ob_food_{food.id}",
                    value=food.id in st.session_state.ob_foods,
                    on_change=_toggle_food,
                    args=(food.id,),
                )

    has_selection = bool(_selected_food_ids())
    back, nxt = st.columns(2)
    with back:
        st.button("이전", key="ob_back_1", width="stretch", on_click=_go, args=(0,))
    with nxt:
        st.button(
            "다음",
            key="ob_next_1",
            type="primary",
            width="stretch",
            disabled=not has_selection,
            on_click=_go,
            args=(2,),
        )
    if not has_selection:
        st.caption("음식을 1개 이상 골라야 다음으로 넘어갈 수 있어요.")


# 3단계 ---------------------------------------------------------------------


def _step_weight() -> None:
    _header(
        2,
        "칼로리를 더 정확하게 계산할게요",
        f"체중을 알려 주면 움직인 만큼 소모한 칼로리를 더 정확하게 계산해요. "
        f"건너뛰면 {DEFAULT_WEIGHT_KG}kg 기준으로 계산해요. 체중은 나만 볼 수 있어요.",
    )

    weight = st.number_input(
        "체중 (kg)",
        min_value=20.0,
        max_value=250.0,
        step=0.5,
        value=st.session_state.ob_weight_saved,
        placeholder=f"예: {DEFAULT_WEIGHT_KG}",
        key="ob_weight",
        on_change=_save_weight,
    )

    st.button(
        "MUKBOGI 시작하기",
        key="ob_start",
        type="primary",
        width="stretch",
        disabled=weight is None,
        on_click=_finish,
        args=(weight,),
    )
    back, skip = st.columns(2)
    with back:
        st.button("이전", key="ob_back_2", width="stretch", on_click=_go, args=(1,))
    with skip:
        st.button("건너뛰기", key="ob_skip", width="stretch", on_click=_finish, args=(None,))


_STEPS = (_step_type, _step_foods, _step_weight)


def render() -> None:
    _init_state()
    _STEPS[st.session_state.ob_step]()


def render_done() -> None:
    """온보딩 결과 확인 화면. 홈 화면을 만들기 전까지 임시로 쓴다."""
    profile = st.session_state.profile
    st.markdown('<h1 class="mk-section">준비 끝났어요!</h1>', unsafe_allow_html=True)
    st.markdown(
        '<p class="mk-help">이제 먹고 싶은 음식을 주문하고 움직여서 소화해 봐요.</p>',
        unsafe_allow_html=True,
    )

    with st.container(border=True):
        st.markdown(f"**{profile['eater_type']}** · 하루 목표 {profile['daily_target_kcal']}kcal")
        weight = profile["weight_kg"]
        weight_text = f"{weight:g}kg" if weight is not None else f"입력 안 함 ({DEFAULT_WEIGHT_KG}kg 기준)"
        st.caption(f"체중: {weight_text}")

        st.markdown("**소화하고 싶은 음식**")
        foods = [FOODS_BY_ID[i] for i in profile["favorite_food_ids"]]
        cols = st.columns(3)
        for idx, food in enumerate(foods):
            with cols[idx % 3]:
                st.image(str(food.image_path), caption=food.name, width="stretch")

    st.info("홈 화면은 다음 단계에서 만들어요.")
    st.button("온보딩 다시 하기", key="ob_reset", width="stretch", on_click=reset)


def reset() -> None:
    for key in list(st.session_state.keys()):
        if key.startswith("ob_") or key == "profile":
            del st.session_state[key]
