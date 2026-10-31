"""친구·요청·랭킹·공개 범위 규칙 테스트 (PRD Story 5.1 ~ 5.3)."""

from datetime import datetime

from core import social
from core.demo import ME_ID, USERS_BY_ID
from core.meal import FridgeEntry

NOW = datetime(2026, 10, 31, 20, 0)  # 토요일


def test_find_user_exact_id_only():
    assert social.find_user("@Doyun ").id == "doyun"
    assert social.find_user("doy") is None
    assert social.find_user("") is None
    assert social.find_user(ME_ID) == ME_ID


def test_request_flow_and_messages():
    s = social.SocialState()
    assert social.send_request(s, "haneul") == "friend"
    assert social.send_request(s, "doyun") == "received"  # 이미 나에게 요청함
    assert social.send_request(s, "nobody") == "missing"
    assert social.send_request(s, ME_ID) == "me"
    assert social.send_request(s, "seoyeon") == "ok"
    assert social.send_request(s, "seoyeon") == "sent"
    social.cancel_request(s, "seoyeon")
    assert social.relation(s, "seoyeon") == "none"


def test_accept_decline_remove():
    s = social.SocialState()
    social.accept(s, "doyun")
    assert "doyun" in s.friends and "doyun" not in s.received
    s.received.append("jiho")
    social.decline(s, "jiho")
    assert social.relation(s, "jiho") == "none"
    social.remove_friend(s, "haneul")
    assert social.relation(s, "haneul") == "none"


def test_fridge_visibility():
    s = social.SocialState()
    assert social.can_view_fridge(s, USERS_BY_ID["jun"])  # 전체
    assert social.can_view_fridge(s, USERS_BY_ID["haneul"])  # 친구만 + 친구
    assert not social.can_view_fridge(s, USERS_BY_ID["jiho"])  # 친구만 + 친구 아님
    assert not social.can_view_fridge(s, USERS_BY_ID["min"])  # 비공개 (친구여도)


def test_week_starts_monday_and_weekly_kcal():
    assert social.week_start(NOW.date()).isoformat() == "2026-10-26"
    entries = [
        FridgeEntry("pasta", 600, 1, datetime(2026, 10, 26, 0, 0)),  # 월요일 00:00 → 이번 주
        FridgeEntry("pasta", 600, 1, datetime(2026, 10, 25, 23, 59)),  # 지난주 일요일
    ]
    assert social.weekly_kcal(entries, NOW.date()) == 600


def test_ranking_order_scope_and_ties():
    s = social.SocialState()
    me = [FridgeEntry("pasta", 600, 1, datetime(2026, 10, 31, 9, 0))]
    rows = social.ranking(s, me, NOW, "전체")
    kcals = [r.kcal for r in rows]
    assert kcals == sorted(kcals, reverse=True)
    assert sum(r.is_me for r in rows) == 1
    friends = social.ranking(s, me, NOW, "친구")
    assert {r.user_id for r in friends} == {"haneul", "jun", "sua", "min", ME_ID}
    for a, b in zip(rows, rows[1:]):  # 같은 칼로리는 같은 순위
        if a.kcal == b.kcal:
            assert a.rank == b.rank
