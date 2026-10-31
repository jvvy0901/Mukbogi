"""음식 배달 보내기·받기 (PRD Story 5.4).

흐름
1) 홈의 소화 중인 친구 카드, 또는 커뮤니티(친구 목록·배달 기록·친구 냉장고)에서 배달 보내기 화면으로 간다.
2) 음식을 하나 골라 보내면, 그 음식은 친구의 조리 중인 음식에 들어간다.
   (프로토타입은 친구 화면이 없으므로, 내 화면에 "배달 N" 표시와 보낸 기록만 남는다.)
3) 프로토타입 전용: 잠시 뒤 친구가 답례로 보낸 음식이 내 조리 중인 음식에 들어오고
   "OO이 보낸 OO이 도착했어요" 토스트가 뜬다. 답례 음식 = 그 친구가 지금 소화 중인 음식(쉬는 중이면 내가 보낸 음식).
4) 보낸·받은 배달은 기록(gift_log)에 남아 커뮤니티 "배달" 탭에서 상태와 함께 볼 수 있다.
"""

import time
from datetime import datetime
from html import escape

import streamlit as st

from core import meal
from core.data import FOODS, FOODS_BY_ID
from core.demo import USERS_BY_ID, User
from core.images import food_thumb, profile_thumb
from core.korean import eul_reul, i_ga
from core.style import html, toast

REPLY_DELAY_S = 3.0  # 답례 배달이 도착하기까지 (프로토타입 흉내)


# 상태 ------------------------------------------------------------------------


def init_state() -> None:
    ss = st.session_state
    ss.setdefault("gifts_sent", {})  # 친구 아이디 → 보낸 음식 id 목록 (친구의 조리 중 목록)
    ss.setdefault("gift_replies", [])  # 도착 예정인 답례: {"user_id", "food_id", "due"}
    ss.setdefault("gift_log", [])  # 배달 기록: {"id", "dir": sent|received, "user_id", "food_id", "at", "missed"}
    ss.setdefault("gift_to", None)  # 배달 보내기 화면에서 받는 친구 아이디
    ss.setdefault("gift_from", "home")  # 배달 보내기 화면을 닫으면 돌아갈 화면
    ss.setdefault("gift_pick", None)


def sent_count(user_id: str) -> int:
    return len(st.session_state.get("gifts_sent", {}).get(user_id, []))


def friend_can_receive(user_id: str) -> bool:
    return sent_count(user_id) < meal.MAX_WAITING


def open_for(user_id: str, back_to: str = "home") -> None:
    ss = st.session_state
    ss.gift_to = user_id
    ss.gift_from = back_to
    ss.gift_pick = None
    ss.screen = "gift"


def _log(direction: str, user_id: str, food_id: str, missed: bool = False) -> int:
    log = st.session_state.gift_log
    gift_id = len(log) + 1
    log.append({"id": gift_id, "dir": direction, "user_id": user_id, "food_id": food_id,
                "at": datetime.now(), "missed": missed})
    return gift_id


def _pick(food_id: str) -> None:
    st.session_state.gift_pick = food_id


def _back() -> None:
    ss = st.session_state
    ss.screen = ss.get("gift_from", "home")
    ss.gift_pick = None


def _send() -> None:
    ss = st.session_state
    user = USERS_BY_ID[ss.gift_to]
    food_id = ss.gift_pick
    if food_id is None or not friend_can_receive(user.id):
        return
    ss.gifts_sent.setdefault(user.id, []).append(food_id)
    _log("sent", user.id, food_id)
    reply = user.food_id or food_id
    ss.gift_replies.append({"user_id": user.id, "food_id": reply, "due": time.time() + REPLY_DELAY_S})
    toast(f"{user.name}에게 {eul_reul(FOODS_BY_ID[food_id].name)} 보냈어요")
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
        user = USERS_BY_ID[g["user_id"]]
        food = FOODS_BY_ID[g["food_id"]]
        if meal.can_order(state):
            gift_id = _log("received", user.id, food.id)
            meal.order(state, food.id, sender=user.name, gift_id=gift_id)
            toast(f"{i_ga(user.name)} 보낸 {i_ga(food.name)} 도착했어요")
        else:
            _log("received", user.id, food.id, missed=True)
            toast(f"조리 중인 음식이 가득 차서 {i_ga(user.name)} 보낸 {eul_reul(food.name)} 받지 못했어요")


def received_status(state: meal.MealState, entry: dict) -> str:
    """받은 배달이 지금 어디에 있는지."""
    if entry["missed"]:
        return "가득 차서 못 받았어요"
    gid = entry["id"]
    if state.current is not None and state.current.gift_id == gid:
        return "소화 중이에요"
    if any(o.gift_id == gid for o in state.waiting):
        return "조리 중이에요"
    if any(e.gift_id == gid for e in state.fridge):
        return "다 먹었어요 · 냉장고"
    return ""


def timer() -> None:
    """답례가 기다리는 동안 1초마다 확인해서, 도착하면 화면 전체를 다시 그린다."""
    if not st.session_state.get("gift_replies"):
        return

    @st.fragment(run_every=1.0)
    def _tick() -> None:
        if any(g["due"] <= time.time() for g in st.session_state.get("gift_replies", [])):
            st.rerun()

    _tick()


# 공통 조각 -------------------------------------------------------------------


def avatar(user: User, cls: str = "mk-avatar") -> str:
    if user.photo is not None and user.photo.exists():
        return f'<img class="{cls}" src="{profile_thumb(user.photo)}" alt="">'
    return f'<span class="{cls} mk-avatar-initial" aria-hidden="true">{escape(user.name[0])}</span>'


def doing_html(user: User) -> str:
    """친구 상태 한 줄: [음식 이름 (남는 폭, 길면 …)] [진행 막대 48px] [%]  — "소화 중"은 막대가 보여 주므로 스크린리더에만 읽힌다.
    막대와 %는 고정 폭으로 글자 칸 오른쪽 끝에 붙어서, 목록의 모든 줄에서 같은 위치에 세로로 맞는다.
    """
    if not user.food_id:
        return '<div class="mk-doing"><div class="mk-doing-food">쉬는 중이에요</div></div>'
    pct = round(user.progress * 100)
    return (
        '<div class="mk-doing">'
        f'<div class="mk-doing-food">{escape(FOODS_BY_ID[user.food_id].name)}<span class="mk-sr"> 소화 중</span></div>'
        '<div class="mk-doing-prog">'
        f'<span class="mk-doing-bar" aria-hidden="true"><i style="width:{pct}%"></i></span>'
        f'<b class="mk-doing-pct">{pct}%</b>'
        "</div></div>"
    )


# 배달 보내기 화면 -------------------------------------------------------------


def render_send() -> None:
    ss = st.session_state
    user = USERS_BY_ID[ss.gift_to]
    pick = ss.gift_pick

    with st.container(key="nav_row", horizontal=True, vertical_alignment="center"):
        st.button("이전", key="gift_back", type="tertiary", on_click=_back)
        html('<div class="mk-nav-title">배달 보내기</div>')
        html('<div class="mk-nav-slot"></div>')

    html(
        '<div class="mk-header">'
        f'<div class="mk-title" role="heading" aria-level="1">{escape(user.name)}에게<br>무엇을 보낼까요?</div>'
        f'<div class="mk-sub">보낸 음식은 {escape(user.name)}의 조리 중인 음식에 들어가요.</div>'
        "</div>"
    )
    count = sent_count(user.id)
    html(
        '<div class="mk-gift-to">'
        f"{avatar(user, 'mk-avatar mk-avatar-lg')}"
        f'<div><div class="mk-gift-name">{escape(user.name)}</div>'
        f"{doing_html(user)}</div>"
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

    can = friend_can_receive(user.id)
    with st.container(key="bar_footer"):
        if not can:
            html(f'<div class="mk-hint">{escape(user.name)}의 조리 중인 음식이 가득 찼어요 ({meal.MAX_WAITING}개)</div>')
        elif pick is None:
            html('<div class="mk-hint">보낼 음식을 하나 골라 주세요</div>')
        label = f"{FOODS_BY_ID[pick].name} 보내기" if pick else "보내기"
        st.button(label, key="gift_send", type="primary", width="stretch", disabled=pick is None or not can, on_click=_send)
