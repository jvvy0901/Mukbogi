"""음식 배달 보내기 (친구에게 음식 선물).

흐름
1) 홈에서 소화 중인 친구 카드를 누르면 "배달 보내기" 화면으로 간다.
2) 음식을 하나 골라 보내면, 그 음식은 친구의 조리 중인 음식에 들어간다.
   (프로토타입은 친구 화면이 없으므로, 내 홈의 친구 카드에 "배달 N" 표시만 붙는다.)
3) 프로토타입 전용: 잠시 뒤 친구가 답례로 보낸 음식이 내 조리 중인 음식에 들어오고
   "OO이 보낸 OO이 도착했어요" 토스트가 뜬다. 답례 음식 = 그 친구가 지금 소화 중인 음식.
"""

import time
from html import escape

import streamlit as st

from core import meal
from core.data import FOODS, FOODS_BY_ID
from core.demo import FRIENDS, Friend
from core.images import food_thumb, profile_thumb
from core.korean import eul_reul, i_ga
from core.style import html, toast

REPLY_DELAY_S = 3.0  # 답례 배달이 도착하기까지 (프로토타입 흉내)


# 상태 ------------------------------------------------------------------------


def init_state() -> None:
    ss = st.session_state
    ss.setdefault("gifts_sent", {})  # 친구 이름 → 보낸 음식 id 목록 (친구의 조리 중 목록)
    ss.setdefault("gift_replies", [])  # 도착 예정인 답례: {"friend", "food_id", "due"}
    ss.setdefault("gift_to", None)  # 배달 보내기 화면에서 받는 친구 (FRIENDS 순번)
    ss.setdefault("gift_pick", None)


def sent_count(friend: Friend) -> int:
    return len(st.session_state.gifts_sent.get(friend.name, []))


def friend_can_receive(friend: Friend) -> bool:
    return sent_count(friend) < meal.MAX_WAITING


def open_for(friend_idx: int) -> None:
    st.session_state.gift_to = friend_idx
    st.session_state.gift_pick = None
    st.session_state.screen = "gift"


def _pick(food_id: str) -> None:
    st.session_state.gift_pick = food_id


def _back() -> None:
    st.session_state.screen = "home"
    st.session_state.gift_pick = None


def _send() -> None:
    ss = st.session_state
    friend = FRIENDS[ss.gift_to]
    food_id = ss.gift_pick
    if food_id is None or not friend_can_receive(friend):
        return
    ss.gifts_sent.setdefault(friend.name, []).append(food_id)
    reply = friend.food_id or food_id
    ss.gift_replies.append({"friend": friend.name, "food_id": reply, "due": time.time() + REPLY_DELAY_S})
    toast(f"{friend.name}에게 {eul_reul(FOODS_BY_ID[food_id].name)} 보냈어요")
    _back()


def deliver_due(state: meal.MealState, now: float | None = None) -> None:
    """도착 시간이 된 답례 배달을 내 조리 중인 음식에 넣는다."""
    now = time.time() if now is None else now
    pending = st.session_state.get("gift_replies", [])
    due = [g for g in pending if g["due"] <= now]
    if not due:
        return
    st.session_state.gift_replies = [g for g in pending if g["due"] > now]
    for g in due:
        food = FOODS_BY_ID[g["food_id"]]
        if meal.order(state, g["food_id"], sender=g["friend"]):
            toast(f"{i_ga(g['friend'])} 보낸 {i_ga(food.name)} 도착했어요")
        else:
            toast(f"조리 중인 음식이 가득 차서 {i_ga(g['friend'])} 보낸 {eul_reul(food.name)} 받지 못했어요")


def timer() -> None:
    """답례가 기다리는 동안 1초마다 확인해서, 도착하면 화면 전체를 다시 그린다."""
    if not st.session_state.get("gift_replies"):
        return

    @st.fragment(run_every=1.0)
    def _tick() -> None:
        if any(g["due"] <= time.time() for g in st.session_state.get("gift_replies", [])):
            st.rerun()

    _tick()


# 배달 보내기 화면 -------------------------------------------------------------


def _avatar(friend: Friend, cls: str = "mk-avatar") -> str:
    if friend.photo is not None and friend.photo.exists():
        return f'<img class="{cls}" src="{profile_thumb(friend.photo)}" alt="">'
    return f'<span class="{cls} mk-avatar-initial" aria-hidden="true">{escape(friend.name[0])}</span>'


def render_send() -> None:
    ss = st.session_state
    friend = FRIENDS[ss.gift_to]
    pick = ss.gift_pick

    with st.container(key="nav_row", horizontal=True, vertical_alignment="center"):
        st.button("이전", key="gift_back", type="tertiary", on_click=_back)
        html('<div class="mk-nav-title">배달 보내기</div>')
        html('<div class="mk-nav-slot"></div>')

    html(
        '<div class="mk-header">'
        f'<div class="mk-title" role="heading" aria-level="1">{escape(friend.name)}에게<br>무엇을 보낼까요?</div>'
        f'<div class="mk-sub">보낸 음식은 {escape(friend.name)}의 조리 중인 음식에 들어가요.</div>'
        "</div>"
    )

    if friend.food_id:
        now_food = FOODS_BY_ID[friend.food_id]
        doing = f"지금 {eul_reul(now_food.name)} 소화 중이에요 · {round(friend.progress * 100)}%"
    else:
        doing = "지금은 쉬는 중이에요"
    count = sent_count(friend)
    html(
        '<div class="mk-gift-to">'
        f"{_avatar(friend, 'mk-avatar mk-avatar-lg')}"
        f'<div><div class="mk-gift-name">{escape(friend.name)}</div><div class="mk-gift-doing">{escape(doing)}</div></div>'
        + (f'<span class="mk-fr-gift">배달 {count}</span>' if count else "")
        + "</div>"
    )

    with st.container(key="grid_gift"):
        for food in FOODS:
            sel = " sel" if pick == food.id else ""
            with st.container(key=f"tap_gift_{food.id}"):
                html(
                    f'<div class="mk-card mk-food{sel}">'
                    '<div class="mk-pick" aria-hidden="true"></div>'
                    f'<img src="{food_thumb(food)}" alt="">'
                    f'<div class="mk-food-name">{escape(food.name)}</div>'
                    f'<div class="mk-food-kcal">{food.kcal}kcal</div>'
                    "</div>"
                )
                st.button(f"{food.name} 고르기", key=f"gift_{food.id}", on_click=_pick, args=(food.id,))

    can = friend_can_receive(friend)
    with st.container(key="bar_footer"):
        if not can:
            html(f'<div class="mk-hint">{escape(friend.name)}의 조리 중인 음식이 가득 찼어요 ({meal.MAX_WAITING}개)</div>')
        elif pick is None:
            html('<div class="mk-hint">보낼 음식을 하나 골라 주세요</div>')
        label = f"{FOODS_BY_ID[pick].name} 보내기" if pick else "보내기"
        st.button(label, key="gift_send", type="primary", width="stretch", disabled=pick is None or not can, on_click=_send)
