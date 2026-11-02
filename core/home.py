"""홈 화면과 하단 탭. PRD.md Epic 3 (Story 3.1 ~ 3.7) + Story 6.1(광고 자리)을 구현한다.

- 움직임 감지는 PRD 프로토타입 대체 표대로 "활동(걷기/달리기) + 거리 버튼"으로 흉내 낸다.
- 백그라운드 측정·푸시·햅틱은 프로토타입에 없다.
- 주문하기는 홈 확인용 임시 화면이다 (추천·카테고리는 Epic 2에서 만든다).
- 냉장고 화면은 core/fridge.py, 커뮤니티 탭은 자리만 있다.
"""

from datetime import datetime
from html import escape

import streamlit as st

from core import community, fridge, gift, meal, mypage, rules, social
from core.avatar import user_avatar
from core.data import FOODS, FOODS_BY_ID
from core.images import food_bitten, food_thumb
from core.korean import eul_reul, i_ga
from core.style import html, toast

TABS = (("home", "홈"), ("fridge", "냉장고"), ("community", "커뮤니티"), ("my", "내정보"))
WEEKDAYS = ("월", "화", "수", "목", "금", "토", "일")
TABS_WITHOUT_PAGE: set[str] = set()  # 메뉴만 있고 화면은 아직 없는 탭
DISTANCES = (0.5, 1.0, 3.0)


# 상태 ------------------------------------------------------------------------


def _init_state() -> None:
    ss = st.session_state
    ss.setdefault("screen", "home")
    ss.setdefault("meal", meal.MealState())
    ss.setdefault("activity", "걷기")
    ss.setdefault("celebrate", [])
    ss.setdefault("order_pick", None)
    ss.setdefault("social", social.SocialState())


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
        st.session_state.just_added_id = id(_state().orders[-1])  # 들어간 자리에서 나타나게 (한 번만)
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


def _open_friends_tab() -> None:
    st.session_state.comm_tab = "friends"
    _go("community")


def _section_link(key: str, title: str, label: str, on_click, args=()) -> None:
    """오른쪽에 화살표가 붙은 섹션 제목. 제목 줄 전체(높이 44px)가 눌리고, 누르면 그 섹션의 전체 화면으로 간다."""
    with st.container(key=f"tap_sec_{key}"):
        html(f'<div class="mk-section mk-sec-link" role="heading" aria-level="2">{title}'
             '<span class="mk-sec-arrow" aria-hidden="true"></span></div>')
        st.button(label, key=f"sec_{key}", on_click=on_click, args=args)


def _tab_bar(active: str) -> None:
    # 현재 탭: 초록 채움 아이콘(브랜드 가이드) + 검정 굵은 라벨 / 다른 탭: 회색 선 아이콘 + 보통 라벨
    html(
        "<style>"
        f".st-key-tab_{active} button {{ color: var(--ink) !important; }}"
        f".st-key-tab_{active} button::before {{ background: var(--green) !important; -webkit-mask-image: var(--icon-on) !important; mask-image: var(--icon-on) !important; }}"
        f".st-key-tab_{active} button p {{ font-weight: 700 !important; }}"
        "</style>"
    )
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
    new = " mk-new" if st.session_state.get("just_added_id") == id(order) else ""
    html(
        f'<div class="mk-meal{new}">'
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
                f'<div class="mk-q{" mk-q-gift" if o.sender else ""}{" mk-new" if st.session_state.get("just_added_id") == id(o) else ""}">'
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


def _favorite_foods() -> list:
    """온보딩에서 고른 음식 먼저, 그 뒤에 나머지 음식을 음식 목록 순서로."""
    picked = [FOODS_BY_ID[i] for i in st.session_state.profile.get("favorite_food_ids", []) if i in FOODS_BY_ID]
    return picked + [f for f in FOODS if f not in picked]


def _week_section(state: meal.MealState) -> None:
    """이번 주 소화: 월요일부터 움직여 소화한 칼로리를 '떡볶이 2개 만큼'처럼 음식으로 보여 준다.

    음식은 소화한 칼로리에 가장 가까운 음식으로 고른다(rules.week_compare_foods) — 150kcal면 탕후루 1개.
    고른 음식이 바뀌는 순간에만 사진·문구가 살짝 튀어 오른다."""
    today = datetime.now().date()
    days = state.week_by_day(today)
    total = round(sum(days))
    favorites = _favorite_foods()
    if total > 0:
        main, *others = rules.week_compare_foods(total, FOODS, favorites)[:3]
    else:
        main, others = favorites[0], []
    monday = social.week_start(today)
    since = f"{monday.month}월 {monday.day}일(월)부터"

    prev = st.session_state.get("week_food")
    st.session_state.week_food = main.id
    swapped = " mk-week-swap" if prev is not None and prev != main.id else ""

    if total > 0 and rules.match_error(total, main) > rules.MATCH_TOLERANCE + 1e-9 and total < main.kcal:
        # 가장 작은 음식 1개에도 못 미치면(예: 50kcal) 억지로 "1개"라고 하지 않고 남은 칼로리를 알려 준다
        title = f'{escape(main.name)} <span class="mk-nowrap"><b>1개</b>까지</span> {main.kcal - total:,}kcal 남았어요'
        sub = f"{since} <b>{total:,}</b>kcal"
        alt_row = ""
    elif total > 0:
        count = rules.format_count(rules.food_count(total, main))
        title = f'{escape(main.name)} <span class="mk-nowrap"><b>{count}개</b> 만큼</span> 소화했어요'
        sub = f"{since} <b>{total:,}</b>kcal"
        alts = "".join(
            f'<span class="mk-week-chip"><img src="{food_thumb(f, 96)}" alt="">{escape(f.name)} '
            f'<b>{rules.format_count(rules.food_count(total, f))}개</b></span>'
            for f in others
        )
        alt_row = f'<div class="mk-week-alt"><span class="mk-week-alt-label">다른 음식으로는</span>{alts}</div>'
    else:
        title = "이번 주는 아직 소화한 음식이 없어요"
        sub = "식사시작을 누르고 움직이면 여기에 쌓여요"
        alt_row = ""

    top = max(days) or 1
    bars = "".join(
        f'<div class="mk-wd{" today" if i == today.weekday() else ""}{" later" if i > today.weekday() else ""}">'
        f'<div class="mk-wd-track"><i style="height:{0 if v <= 0 else max(8, round(v / top * 100))}%"></i></div>'
        f"<span>{WEEKDAYS[i]}</span></div>"
        for i, v in enumerate(days)
    )
    spoken = ", ".join(f"{WEEKDAYS[i]} {round(v)}킬로칼로리" for i, v in enumerate(days) if i <= today.weekday())

    _section_link("week", "이번 주 소화 칼로리", "냉장고 보기", _go, ("fridge",))
    html(
        f'<div class="mk-week{" mk-week-empty" if total <= 0 else ""}{swapped}">'
        '<div class="mk-week-head">'
        f'<img src="{food_thumb(main, 192)}" alt="">'
        f'<div><div class="mk-week-title">{title}</div><div class="mk-week-sub">{sub}</div></div>'
        "</div>"
        f"{alt_row}"
        f'<div class="mk-week-days" role="img" aria-label="요일별 소화 칼로리: {spoken}">{bars}</div>'
        "</div>"
    )


def _friends_section() -> None:
    _section_link("friends", "친구들이 소화 중이에요", "친구 목록 보기", _open_friends_tab)
    friends = social.friend_users(st.session_state.social)
    if not friends:
        with st.container(key="friends_empty"):
            html('<div class="mk-sub">친구를 추가해 보세요</div>')
            st.button("커뮤니티 가기", key="home_community", on_click=_go, args=("community",))
        return
    html('<div class="mk-count mk-sec-hint">친구를 누르면 음식을 배달할 수 있어요</div>')
    with st.container(key="row_friends"):
        for f in friends:
            sent = gift.sent_count(f.id)
            bump = " mk-bump" if st.session_state.get("just_gifted") == f.id else ""
            badge = f'<span class="mk-fr-gift{bump}">배달 {sent}</span>' if sent else ""
            head = f'<div class="mk-fr-head">{user_avatar(f)}<span>{escape(f.name)}</span>{badge}</div>'
            if f.food_id is None:
                html(f'<div class="mk-fr">{head}<div class="mk-fr-rest">쉬는 중이에요</div></div>')
                continue
            food = FOODS_BY_ID[f.food_id]
            pct = round(f.progress * 100)
            with st.container(key=f"tap_friend_{f.id}"):
                html(
                    '<div class="mk-card mk-fr">'
                    f"{head}"
                    f'<div class="mk-fr-food"><img src="{food_thumb(food)}" alt="">{escape(food.name)}</div>'
                    f'<div class="mk-bar" role="img" aria-label="{escape(f.name)} {escape(food.name)} {pct}% 소화">'
                    f'<i style="width:{pct}%"></i></div>'
                    f'<div class="mk-fr-pct">{pct}%</div>'
                    "</div>"
                )
                st.button(f"{f.name}에게 음식 배달 보내기", key=f"friend_{f.id}", on_click=gift.open_for, args=(f.id, "home"))


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

    _week_section(state)
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


def _fridge() -> None:
    fridge.render(_state().fridge, datetime.now().date(), _today_target(), _go)


def _community() -> None:
    community.render(_state())


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
    elif screen == "user":
        community.render_user(_state())
    else:
        {"home": _home, "fridge": _fridge, "community": _community, "my": lambda: mypage.render(_state())}[screen]()
        _tab_bar(screen)

    gift.timer()
