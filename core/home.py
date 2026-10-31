"""홈 화면과 하단 탭. PRD.md Epic 3 (Story 3.1 ~ 3.7) + Story 6.1(광고 자리)을 구현한다.

- 움직임 감지는 PRD 프로토타입 대체 표대로 "활동(걷기/달리기) + 거리 버튼"으로 흉내 낸다.
- 백그라운드 측정·푸시·햅틱은 프로토타입에 없다.
- 주문하기는 홈 확인용 임시 화면이다 (추천·카테고리는 Epic 2에서 만든다).
- 냉장고 화면은 core/fridge.py, 커뮤니티 탭은 자리만 있다.
"""

from datetime import datetime
from html import escape

import streamlit as st

from core import fridge, gift, meal
from core.data import FOODS, FOODS_BY_ID
from core.demo import FRIENDS
from core.images import food_bitten, food_thumb, profile_thumb
from core.korean import eul_reul, i_ga
from core.style import html, toast

TABS = (("home", "홈"), ("fridge", "냉장고"), ("community", "커뮤니티"), ("my", "내정보"))
TABS_WITHOUT_PAGE = {"my"}  # 메뉴만 있고 화면은 아직 없는 탭
DISTANCES = (0.5, 1.0, 3.0)


# 상태 ------------------------------------------------------------------------


def _init_state() -> None:
    ss = st.session_state
    ss.setdefault("screen", "home")
    ss.setdefault("meal", meal.MealState())
    ss.setdefault("activity", "걷기")
    ss.setdefault("celebrate", [])
    ss.setdefault("order_pick", None)


def _state() -> meal.MealState:
    return st.session_state.meal


def _weight() -> float | None:
    return st.session_state.profile.get("weight_kg")


def _today_target() -> int:
    return st.session_state.profile["daily_target_kcal"]


# 콜백 ------------------------------------------------------------------------


def _go(screen: str) -> None:
    if screen == "order" and st.session_state.screen != "order":
        # 주문 화면의 "이전"은 들어오기 전 화면(홈·냉장고)으로 돌아간다
        st.session_state.order_from = st.session_state.screen
    st.session_state.screen = screen
    st.session_state.order_pick = None


def _start() -> None:
    meal.start(_state())


def _stop() -> None:
    meal.stop(_state())


def _set_activity(activity: str) -> None:
    st.session_state.activity = activity


def _move(distance_km: float) -> None:
    state = _state()
    before = state.current.bites_eaten if state.current else 0
    current_id = state.current.food_id if state.current else None
    done = meal.move(state, distance_km, st.session_state.activity, _weight(), datetime.now())
    if done:
        st.session_state.celebrate = done
    elif state.current and state.current.food_id == current_id and state.current.bites_eaten > before:
        cur = state.current
        # 다음 화면 그리기에서 "한 입 먹는" 애니메이션을 한 번 보여 준다
        st.session_state.just_bit = (cur.food_id, before, cur.bites_eaten)
        toast(f"냠! {cur.food.name} 한 입 먹었어요 ({cur.bites_eaten}/{cur.food.bites})")


def _close_celebration(next_screen: str) -> None:
    st.session_state.celebrate = []
    if next_screen == "next" and _state().current is None:
        _go("order")
    elif next_screen == "fridge":
        _go("fridge")


def _pick_order(food_id: str) -> None:
    st.session_state.order_pick = food_id


def _place_order() -> None:
    food_id = st.session_state.order_pick
    if food_id and meal.order(_state(), food_id):
        toast(f"{eul_reul(FOODS_BY_ID[food_id].name)} 주문했어요")
        _go("home")


# 공통 조각 -------------------------------------------------------------------


def _tab(key: str) -> None:
    if key in TABS_WITHOUT_PAGE:
        # 화면이 아직 없으므로 이동하지 않고 알려만 준다
        label = dict(TABS)[key]
        toast(f"{label}는 준비 중이에요")
        return
    _go(key)


def _tab_bar(active: str) -> None:
    html(f"<style>.st-key-tab_{active} button {{ color: var(--ink) !important; }}</style>")
    with st.container(key="bar_tabs"):
        for key, label in TABS:
            st.button(label, key=f"tab_{key}", type="tertiary", on_click=_tab, args=(key,))


def _top_bar() -> None:
    today = int(_state().digested_on(datetime.now().date()))
    html(
        '<div class="mk-topbar">'
        '<span class="mk-wordmark">MUKBOGI</span>'
        f'<span class="mk-today" aria-label="오늘 {today}킬로칼로리 소화, 하루 목표 {_today_target()}킬로칼로리">'
        f"오늘 <b>{today}</b> / {_today_target()}kcal</span>"
        "</div>"
    )


def _avatar(friend) -> str:
    if friend.photo is not None and friend.photo.exists():
        return f'<img class="mk-avatar" src="{profile_thumb(friend.photo)}" alt="">'
    return f'<span class="mk-avatar mk-avatar-initial" aria-hidden="true">{escape(friend.name[0])}</span>'


# 홈 ---------------------------------------------------------------------------


def _hero(order: meal.Order, measuring: bool) -> str:
    """틀 없이 떠 있는 음식. 크기는 그대로이고, 먹은 입만큼 이빨 자국으로 베어져 있다.

    방금 한 입 먹었다면 직전 모습을 위에 겹쳐 흐려지게 해서 새 자국이 드러나게 하고,
    음식이 살짝 눌렸다 돌아오며 베어 문 자리에서 부스러기가 튄다.
    """
    food = order.food
    now_uri, spot = food_bitten(food, order.bites_eaten)
    just = st.session_state.pop("just_bit", None)
    animate = just is not None and just[0] == food.id and just[2] == order.bites_eaten
    layers = f'<img class="mk-bite-now" src="{now_uri}" alt="{escape(food.name)}, {food.bites}입 중 {order.bites_eaten}입 먹음">'
    if animate:
        prev_uri, _ = food_bitten(food, just[1])
        layers += f'<img class="mk-bite-prev" src="{prev_uri}" alt="" aria-hidden="true">'
        if spot is not None:
            x, y = spot[0] * 100, spot[1] * 100
            layers += "".join(
                f'<i class="mk-crumb mk-crumb-{i}" style="left:{x:.1f}%;top:{y:.1f}%" aria-hidden="true"></i>'
                for i in range(5)
            )
    remaining = 1 - order.bites_eaten / food.bites
    return (
        f'<div class="mk-hero{" on" if measuring else ""}" style="--r:{remaining:.3f}">'
        f'<div class="mk-float"><div class="mk-plate{" chomp" if animate else ""}">{layers}</div></div>'
        "</div>"
    )


def _meal_card(order: meal.Order, measuring: bool) -> None:
    food = order.food
    chip = (
        '<span class="mk-chip on"><i></i>소화 중이에요</span>'
        if measuring
        else '<span class="mk-chip"><i></i>멈춰 있어요</span>'
    )
    html(
        '<div class="mk-meal">'
        f'<div class="mk-meal-top">{chip}<span class="mk-bites-label">한 입 {order.bites_eaten}/{food.bites}</span></div>'
        + _hero(order, measuring)
        + f'<div class="mk-meal-name">{escape(food.name)}</div>'
        f'<div class="mk-meal-kcal">{food.kcal}kcal</div>'
        f'<div class="mk-meal-prog">남은 <b>{round(order.remaining_kcal)}kcal</b></div>'
        '<dl class="mk-stats">'
        f'<div class="mk-stat"><dt>움직인 거리</dt><dd>{order.distance_km:.2f}<small>km</small></dd></div>'
        f'<div class="mk-stat"><dt>소모 칼로리</dt><dd>{round(order.eaten_kcal)}<small>kcal</small></dd></div>'
        "</dl>"
        "</div>"
    )


def _simulator() -> None:
    """움직임 흉내 내기 (프로토타입 전용)."""
    with st.container(key="sim_box"):
        html('<div class="mk-sim-title">움직임 흉내 내기 · 프로토타입</div>')
        with st.container(key="sim_activity", horizontal=True):
            for activity in ("걷기", "달리기"):
                chosen = st.session_state.activity == activity
                st.button(
                    activity,
                    key=f"act_{'walk' if activity == '걷기' else 'run'}",
                    type="primary" if chosen else "secondary",
                    width="stretch",
                    on_click=_set_activity,
                    args=(activity,),
                )
        with st.container(key="sim_dist", horizontal=True):
            for km in DISTANCES:
                st.button(
                    f"+{km:g}km",
                    key=f"move_{str(km).replace('.', '_')}",
                    width="stretch",
                    on_click=_move,
                    args=(km,),
                )


def _queue_section(state: meal.MealState) -> None:
    html('<div class="mk-section">조리 중인 음식</div>')
    with st.container(key="row_queue"):
        for idx, o in enumerate(state.waiting):
            html(
                f'<div class="mk-q{" mk-q-gift" if o.sender else ""}">'
                f'<img src="{food_thumb(o.food)}" alt="">'
                f'<div class="mk-q-name">{escape(o.food.name)}</div>'
                f'<div class="mk-q-kcal">{o.food.kcal}kcal</div>'
                + (f'<div class="mk-q-from">{escape(i_ga(o.sender))} 보냄</div>' if o.sender else "")
                + "</div>"
            )
        if meal.can_order(state):
            with st.container(key="tap_queue_add"):
                html('<div class="mk-card mk-q mk-q-add"><span aria-hidden="true">+</span>더 주문하기</div>')
                st.button("더 주문하기", key="home_more", on_click=_go, args=("order",))
    if not meal.can_order(state):
        html(f'<div class="mk-count">조리 중인 음식은 {meal.MAX_WAITING}개까지 담을 수 있어요</div>')


def _friends_section() -> None:
    html('<div class="mk-section">친구들이 소화 중이에요</div>')
    if not FRIENDS:
        with st.container(key="friends_empty"):
            html('<div class="mk-sub">친구를 추가해 보세요</div>')
            st.button("커뮤니티 가기", key="home_community", on_click=_go, args=("community",))
        return
    html('<div class="mk-count">소화 중인 친구 카드를 누르면 음식을 배달할 수 있어요</div>')
    with st.container(key="row_friends"):
        for idx, f in enumerate(FRIENDS):
            sent = gift.sent_count(f)
            badge = f'<span class="mk-fr-gift">배달 {sent}</span>' if sent else ""
            head = f'<div class="mk-fr-head">{_avatar(f)}<span>{escape(f.name)}</span>{badge}</div>'
            if f.food_id is None:
                html(f'<div class="mk-fr">{head}<div class="mk-fr-rest">쉬는 중이에요</div></div>')
                continue
            food = FOODS_BY_ID[f.food_id]
            pct = round(f.progress * 100)
            with st.container(key=f"tap_friend_{idx}"):
                html(
                    '<div class="mk-card mk-fr">'
                    f"{head}"
                    f'<div class="mk-fr-food"><img src="{food_thumb(food)}" alt="">{escape(food.name)}</div>'
                    f'<div class="mk-bar" role="img" aria-label="{escape(f.name)} {escape(food.name)} {pct}% 소화">'
                    f'<i style="width:{pct}%"></i></div>'
                    f'<div class="mk-fr-pct">{pct}%</div>'
                    "</div>"
                )
                st.button(f"{f.name}에게 음식 배달 보내기", key=f"friend_{idx}", on_click=gift.open_for, args=(idx,))


def _ad_slot() -> None:
    # 프로토타입: 실제 광고 없이 자리만 표시. MUKBOGI 플러스(구독) 사용자에게는 숨긴다.
    if not st.session_state.get("plus", False):
        html('<div class="mk-ad" aria-label="광고 자리">광고 자리 · 프로토타입</div>')


def _celebration() -> None:
    entry = st.session_state.celebrate[-1]
    food = FOODS_BY_ID[entry.food_id]
    more = len(st.session_state.celebrate) - 1
    with st.container(key="sheet_done"):
        html(
            '<div class="mk-done" role="alert">'
            f'<img src="{food_thumb(food, 480)}" alt="{escape(food.name)}">'
            '<div class="mk-done-title">다 소화시켰다!<br>내 냉장고에 등록됐다</div>'
            f'<div class="mk-done-meta">{escape(food.name)} · {entry.kcal}kcal · {entry.distance_km:.2f}km · '
            f'{entry.completed_at:%H:%M}</div>'
            + (f'<div class="mk-done-meta">이번에 {more}개를 더 소화했어요</div>' if more else "")
            + "</div>"
        )
        st.button(
            "다음 음식 먹기",
            key="done_next",
            type="primary",
            width="stretch",
            on_click=_close_celebration,
            args=("next",),
        )
        st.button(
            "냉장고 보기",
            key="done_fridge",
            type="secondary",
            width="stretch",
            on_click=_close_celebration,
            args=("fridge",),
        )


def _home() -> None:
    state = _state()
    _top_bar()

    if state.current is None:
        # Story 3.1 — 음식 선택 전
        with st.container(key="empty_box"):
            html(
                '<div class="mk-empty-title" role="heading" aria-level="1">주문하러 가요</div>'
                '<div class="mk-sub">먹고 싶은 음식을 주문하면 여기에서 움직여서 소화할 수 있어요.</div>'
            )
            st.button("주문하기", key="home_order", type="primary", width="stretch", on_click=_go, args=("order",))
    else:
        _meal_card(state.current, state.measuring)
        if state.measuring:
            _simulator()
        else:
            html('<div class="mk-hint">식사시작을 누르고 움직이면 한 입씩 소화돼요</div>')
        _queue_section(state)

    _friends_section()
    _ad_slot()

    if state.current is not None:
        with st.container(key="bar_footer"):
            if state.measuring:
                st.button("멈추기", key="home_stop", type="secondary", width="stretch", on_click=_stop)
            else:
                st.button("식사시작", key="home_start", type="primary", width="stretch", on_click=_start)


# 주문하기 (임시) -------------------------------------------------------------


def _order() -> None:
    state = _state()
    pick = st.session_state.order_pick
    with st.container(key="nav_row", horizontal=True, vertical_alignment="center"):
        back_to = st.session_state.get("order_from", "home")
        st.button("이전", key="order_back", type="tertiary", on_click=_go, args=(back_to,))
        html('<div class="mk-nav-title">주문하기</div>')
        html('<div class="mk-nav-slot"></div>')
    sub = (
        f"지금 소화 중인 음식이 있어서 조리 중 목록에 들어가요. ({len(state.waiting)}/{meal.MAX_WAITING})"
        if state.current
        else "고른 음식은 홈에서 바로 소화할 수 있어요."
    )
    html(
        '<div class="mk-header">'
        '<div class="mk-title" role="heading" aria-level="1">무엇을 먹을까요?</div>'
        f'<div class="mk-sub">{sub}</div>'
        "</div>"
    )
    with st.container(key="grid_order"):
        for food in FOODS:
            sel = " sel" if pick == food.id else ""
            with st.container(key=f"tap_order_{food.id}"):
                html(
                    f'<div class="mk-card mk-food{sel}">'
                    '<div class="mk-pick" aria-hidden="true"></div>'
                    f'<img src="{food_thumb(food)}" alt="">'
                    f'<div class="mk-food-name">{escape(food.name)}</div>'
                    f'<div class="mk-food-kcal">{food.kcal}kcal</div>'
                    "</div>"
                )
                st.button(f"{food.name} 고르기", key=f"ord_{food.id}", on_click=_pick_order, args=(food.id,))

    can = meal.can_order(state)
    with st.container(key="bar_footer"):
        if not can:
            html(f'<div class="mk-hint">조리 중인 음식은 {meal.MAX_WAITING}개까지 담을 수 있어요</div>')
        elif pick is None:
            html('<div class="mk-hint">음식을 하나 골라 주세요</div>')
        label = f"{FOODS_BY_ID[pick].name} 주문하기" if pick else "주문하기"
        st.button(
            label,
            key="order_submit",
            type="primary",
            width="stretch",
            disabled=pick is None or not can,
            on_click=_place_order,
        )


# 아직 만들지 않은 탭 ----------------------------------------------------------


def _placeholder(title: str, sub: str) -> None:
    html('<div class="mk-topbar"><span class="mk-wordmark">MUKBOGI</span></div>')
    html(
        '<div class="mk-header">'
        f'<div class="mk-title" role="heading" aria-level="1">{title}</div>'
        f'<div class="mk-sub">{sub}</div>'
        "</div>"
    )


def _fridge() -> None:
    fridge.render(_state().fridge, datetime.now().date(), _today_target(), _go)


def _community() -> None:
    _placeholder("커뮤니티", "친구 등록·먹보 랭킹 화면은 다음 단계에서 만들어요.")


# 진입 -------------------------------------------------------------------------


def render() -> None:
    _init_state()
    gift.init_state()
    gift.deliver_due(_state())  # 도착 시간이 된 친구의 답례 배달을 조리 중인 음식에 넣는다
    screen = st.session_state.screen

    if st.session_state.celebrate:
        _celebration()
    elif screen == "order":
        _order()
    elif screen == "gift":
        gift.render_send()
    else:
        {"home": _home, "fridge": _fridge, "community": _community}[screen]()
        _tab_bar(screen)

    gift.timer()
