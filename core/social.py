"""친구·친구 요청·먹보 랭킹·냉장고 공개 범위 규칙. Streamlit과 분리해 테스트할 수 있게 둔다.

PRD Story 5.1(친구 등록, 상호 수락), 5.2(먹보 랭킹), 5.3(다른 유저 냉장고 공개 범위)를 따른다.
"""

from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta

from core.data import FOODS_BY_ID
from core.demo import INITIAL_FRIENDS, INITIAL_RECEIVED_REQUESTS, ME_ID, ME_NAME, USERS, USERS_BY_ID, User
from core.meal import FridgeEntry


@dataclass
class SocialState:
    friends: list[str] = field(default_factory=lambda: list(INITIAL_FRIENDS))
    sent: list[str] = field(default_factory=list)  # 내가 보낸 요청 (상대 수락 대기)
    received: list[str] = field(default_factory=lambda: list(INITIAL_RECEIVED_REQUESTS))  # 받은 요청


# 친구 -------------------------------------------------------------------------


def find_user(query: str, my_id: str = ME_ID) -> User | None | str:
    """아이디를 정확히 입력해야 찾는다 (앞의 @·공백·대소문자는 무시).
    내 아이디(가입 때 정한 아이디 my_id 또는 데모 아이디)면 ME_ID를 돌려준다."""
    q = query.strip().lstrip("@").strip().lower()
    if not q:
        return None
    if q in (ME_ID, my_id.lower()):
        return ME_ID
    return USERS_BY_ID.get(q)


def relation(state: SocialState, user_id: str) -> str:
    """me / friend / sent(요청 중) / received(나에게 요청함) / none"""
    if user_id == ME_ID:
        return "me"
    if user_id in state.friends:
        return "friend"
    if user_id in state.sent:
        return "sent"
    if user_id in state.received:
        return "received"
    return "none"


def send_request(state: SocialState, user_id: str) -> str:
    """결과: ok / friend / sent / received / me / missing"""
    if user_id != ME_ID and user_id not in USERS_BY_ID:
        return "missing"
    rel = relation(state, user_id)
    if rel != "none":
        return rel
    state.sent.append(user_id)
    return "ok"


def cancel_request(state: SocialState, user_id: str) -> None:
    if user_id in state.sent:
        state.sent.remove(user_id)


def accept(state: SocialState, user_id: str) -> None:
    if user_id in state.received:
        state.received.remove(user_id)
        if user_id not in state.friends:
            state.friends.append(user_id)


def decline(state: SocialState, user_id: str) -> None:
    """거절해도 상대에게 따로 알리지 않는다."""
    if user_id in state.received:
        state.received.remove(user_id)


def remove_friend(state: SocialState, user_id: str) -> None:
    if user_id in state.friends:
        state.friends.remove(user_id)


def friend_users(state: SocialState) -> list[User]:
    return [USERS_BY_ID[i] for i in state.friends if i in USERS_BY_ID]


# 냉장고 공개 범위 -------------------------------------------------------------


def can_view_fridge(state: SocialState, user: User) -> bool:
    if user.fridge_visibility == "전체":
        return True
    if user.fridge_visibility == "친구만":
        return user.id in state.friends
    return False


def user_fridge(user: User, now: datetime) -> list[FridgeEntry]:
    """더미 유저의 냉장고 기록을 오늘 기준 날짜로 만든다. 다른 유저의 거리는 공개하지 않으므로 0으로 둔다."""
    entries = []
    for food_id, days_ago, hour, minute in user.history:
        when = (now - timedelta(days=days_ago)).replace(hour=hour, minute=minute, second=0, microsecond=0)
        entries.append(FridgeEntry(food_id, FOODS_BY_ID[food_id].kcal, 0.0, when))
    return entries


# 먹보 랭킹 --------------------------------------------------------------------


def week_start(today: date) -> date:
    """주간 랭킹은 월요일 00:00에 초기화된다."""
    return today - timedelta(days=today.weekday())


def weekly_kcal(entries: Sequence[FridgeEntry], today: date) -> int:
    start = week_start(today)
    return sum(e.kcal for e in entries if start <= e.completed_at.date() <= today)


@dataclass(frozen=True)
class RankRow:
    rank: int
    user_id: str
    name: str
    kcal: int
    is_me: bool


def ranking(state: SocialState, my_entries: Sequence[FridgeEntry], now: datetime, scope: str = "전체") -> list[RankRow]:
    """이번 주 소화 완료 총 칼로리 순위. scope: 전체 / 친구 (친구 + 나). 같은 칼로리는 같은 순위."""
    today = now.date()
    users = USERS if scope == "전체" else friend_users(state)
    scores = [(weekly_kcal(user_fridge(u, now), today), u.id, u.name, False) for u in users]
    scores.append((weekly_kcal(my_entries, today), ME_ID, ME_NAME, True))
    scores.sort(key=lambda s: (-s[0], not s[3], s[2]))

    rows, prev_kcal, prev_rank = [], None, 0
    for i, (kcal, uid, name, is_me) in enumerate(scores, start=1):
        rank = prev_rank if kcal == prev_kcal else i
        rows.append(RankRow(rank, uid, name, kcal, is_me))
        prev_kcal, prev_rank = kcal, rank
    return rows
