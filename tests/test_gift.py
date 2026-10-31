"""음식 배달 보내기 테스트."""

import re
from pathlib import Path

from streamlit.testing.v1 import AppTest

from core.korean import eul_reul, i_ga
from core.meal import MAX_WAITING

APP = str(Path(__file__).resolve().parent.parent / "app.py")
PROFILE = {"eater_type": "중식가", "daily_target_kcal": 365, "favorite_food_ids": ["pasta"], "weight_kg": None}


def test_korean_particles():
    assert [i_ga(w) for w in ("하늘", "준", "수아", "마라탕", "파스타")] == ["하늘이", "준이", "수아가", "마라탕이", "파스타가"]
    assert [eul_reul(w) for w in ("떡볶이", "마라탕")] == ["떡볶이를", "마라탕을"]


def _start():
    at = AppTest.from_file(APP, default_timeout=60)
    at.session_state["profile"] = dict(PROFILE)
    at.run()
    assert not at.exception
    return at


def _click(at, key):
    at.button(key=key).click().run()
    assert not at.exception


def _text(at):
    return re.sub(r"<[^>]+>", "", " ".join(m.value for m in at.markdown))


def _arrive_now(at):
    for g in at.session_state["gift_replies"]:
        g["due"] = 0
    at.run()
    assert not at.exception


def test_only_digesting_friends_are_tappable():
    at = _start()
    keys = {b.key for b in at.button}
    assert {"friend_0", "friend_1", "friend_2"} <= keys  # 하늘·준·수아는 소화 중
    assert "friend_3" not in keys  # 민은 쉬는 중
    assert at.button(key="friend_0").label == "하늘에게 음식 배달 보내기"


def test_send_food_to_friend():
    at = _start()
    _click(at, "friend_0")
    assert at.session_state["screen"] == "gift"
    text = _text(at)
    assert "하늘에게" in text and "무엇을 보낼까요?" in text and "마라탕을 소화 중이에요" in text
    assert at.button(key="gift_send").disabled
    _click(at, "gift_ttuckbokki")
    assert at.button(key="gift_send").label == "떡볶이 보내기"
    _click(at, "gift_send")
    assert at.session_state["screen"] == "home"
    assert at.session_state["gifts_sent"] == {"하늘": ["ttuckbokki"]}
    text = _text(at)
    assert "하늘에게 떡볶이를 보냈어요" in text
    assert "배달 1" in text


def test_friend_reply_arrives_in_my_cooking_list():
    at = _start()
    # 내가 파스타를 먹는 중이어야 답례가 "조리 중인 음식"에 들어간다
    _click(at, "home_order")
    _click(at, "ord_pasta")
    _click(at, "order_submit")
    _click(at, "friend_0")
    _click(at, "gift_tanghuru")
    _click(at, "gift_send")
    assert len(at.session_state["meal"].waiting) == 0  # 아직 도착 전

    _arrive_now(at)
    waiting = at.session_state["meal"].waiting
    assert [(o.food_id, o.sender) for o in waiting] == [("maratang", "하늘")]  # 하늘이 먹던 마라탕을 답례로
    text = _text(at)
    assert "하늘이 보낸 마라탕이 도착했어요" in text
    assert "하늘이 보냄" in text
    assert at.session_state["gift_replies"] == []


def test_back_from_gift_screen_returns_home_without_sending():
    at = _start()
    _click(at, "friend_1")
    _click(at, "gift_pasta")
    _click(at, "gift_back")
    assert at.session_state["screen"] == "home"
    assert at.session_state["gifts_sent"] == {}


def test_friend_list_full():
    at = _start()
    at.session_state["gifts_sent"] = {"준": ["pasta"] * MAX_WAITING}
    at.run()
    _click(at, "friend_1")
    _click(at, "gift_pasta")
    assert at.button(key="gift_send").disabled
    assert "준의 조리 중인 음식이 가득 찼어요" in _text(at)
