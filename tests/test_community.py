"""커뮤니티 화면 흐름 테스트 (PRD Story 5.1 ~ 5.4)."""

import re
from pathlib import Path

from streamlit.testing.v1 import AppTest

APP = str(Path(__file__).resolve().parent.parent / "app.py")
PROFILE = {"eater_type": "중식가", "daily_target_kcal": 365, "favorite_food_ids": ["pasta"], "weight_kg": None}


def _start(tab=None):
    at = AppTest.from_file(APP, default_timeout=60)
    at.session_state["profile"] = dict(PROFILE)
    at.session_state["screen"] = "community"
    if tab:
        at.session_state["comm_tab"] = tab
    at.run()
    assert not at.exception
    return at


def _click(at, key):
    at.button(key=key).click().run()
    assert not at.exception


def _text(at):
    return re.sub(r"<[^>]+>", "", " ".join(m.value for m in at.markdown))


def _search(at, q):
    at.text_input(key="cm_query").set_value(q).run()
    _click(at, "cm_search")


# 친구 (5.1) -------------------------------------------------------------------


def test_friends_tab_shows_my_id_requests_and_friends():
    at = _start()
    text = _text(at)
    assert "@mukbo_me" in text
    assert "친구 요청" in text and "도윤" in text
    assert "받은 요청" not in text
    for name in ("하늘", "준", "수아", "민"):
        assert name in text
    assert at.button(key="gift_to_haneul").label == "배달하기"


def test_search_and_send_then_cancel_request():
    at = _start()
    _search(at, "@Seoyeon")
    assert "아직 친구가 아니에요" in _text(at)
    _click(at, "req_seoyeon")
    assert "서연에게 친구 요청을 보냈어요" in _text(at)
    assert "seoyeon" in at.session_state["social"].sent
    assert "보낸 요청" in _text(at)
    _click(at, "cnl_seoyeon")
    assert at.session_state["social"].sent == []


def test_search_messages():
    at = _start()
    _search(at, "nobody")
    assert "‘nobody’ 아이디를 찾지 못했어요" in _text(at)
    _search(at, "mukbo_me")
    assert "내 아이디예요" in _text(at)
    _search(at, "haneul")
    assert "이미 친구예요" in _text(at)


def test_accept_and_decline_requests():
    at = _start()
    _click(at, "acc_doyun")
    assert "도윤과 친구가 됐어요" in _text(at)
    assert "doyun" in at.session_state["social"].friends
    at.session_state["social"].received.append("jiho")
    at.run()
    _click(at, "dec_jiho")
    assert at.session_state["social"].received == []


# 다른 유저 냉장고 (5.3) · 친구 삭제 ------------------------------------------


def test_open_friend_fridge_and_remove_friend_with_confirm():
    at = _start()
    _click(at, "open_fr_jun")
    assert at.session_state["screen"] == "user"
    text = _text(at)
    assert "준의 냉장고" in text and "kcal" in text
    assert "km" not in text.split("준의 냉장고")[1]  # 다른 유저의 거리는 숨긴다
    assert at.button(key="u_gift").label == "배달하기"
    _click(at, "u_remove")
    assert "준을 친구에서 삭제할까요?" in _text(at)
    _click(at, "u_remove_ok")
    assert "jun" not in at.session_state["social"].friends
    assert at.button(key="u_request").label == "친구 요청"


def test_private_and_friends_only_fridges_are_locked():
    at = _start(tab="rank")
    _click(at, "rk_yerin")  # 비공개
    assert "비공개 냉장고예요" in _text(at)
    _click(at, "user_back")
    _click(at, "rk_jiho")  # 친구만 + 친구 아님
    assert "친구만 볼 수 있는 냉장고예요" in _text(at)


# 랭킹 (5.2) -------------------------------------------------------------------


def test_ranking_scopes_and_my_rank_footer():
    at = _start(tab="rank")
    text = _text(at)
    assert "내 순위" in text and "/ 9명" in text  # 더미 유저 8명 + 나
    _click(at, "rscope_friends")
    assert "/ 5명" in _text(at)  # 친구 4명 + 나


# 배달 관리 (5.4) -------------------------------------------------------------


def test_gift_tab_lists_sent_and_received_with_status():
    at = _start(tab="gift")
    assert "아직 주고받은 배달이 없어요" in _text(at)
    at.session_state["comm_tab"] = "friends"
    at.run()
    _click(at, "gift_to_sua")
    _click(at, "gift_tanghuru")
    _click(at, "gift_send")
    assert at.session_state["screen"] == "community"  # 커뮤니티에서 보냈으면 커뮤니티로 돌아온다
    for g in at.session_state["gift_replies"]:
        g["due"] = 0
    at.session_state["comm_tab"] = "gift"
    at.run()
    text = _text(at)
    assert "수아에게 탕후루" in text
    assert "수아가 보낸 과일모찌" in text  # 수아가 소화 중인 과일모찌를 답례로
    assert "소화 중이에요" in text  # 내 음식이 없었으므로 바로 소화 중
    _click(at, [b.key for b in at.button if (b.key or "").startswith("thx_")][0])
    assert at.session_state["screen"] == "gift" and at.session_state["gift_to"] == "sua"


def test_friend_status_is_one_line_with_compact_progress():
    at = _start()
    md = " ".join(m.value for m in at.markdown)
    # [음식 이름 (스크린리더: 소화 중)] [막대][%] — 한 줄, 다른 목록 줄과 같은 높이
    assert '<div class="mk-doing-food">마라탕<span class="mk-sr"> 소화 중</span></div><div class="mk-doing-prog">' in md
    assert '<b class="mk-doing-pct">62%</b>' in md
    assert '<div class="mk-doing-food">쉬는 중이에요</div>' in md  # 민 (막대 없음)


def test_answered_request_slides_out_in_place_then_disappears():
    at = _start()
    at.session_state["social"].received.append("jiho")  # 요청 2개: 도윤, 지호
    at.run()
    _click(at, "acc_doyun")
    ghosts = [m.value for m in at.markdown if 'class="mk-ghost ' in m.value]
    assert len(ghosts) == 1 and "mk-ghost-acc" in ghosts[0] and " last" not in ghosts[0]
    assert "친구가 됐어요" in ghosts[0]  # 결과를 그 줄 안에서 보여 준다 (토스트 대신)
    assert not any(b.key == "acc_doyun" for b in at.button)  # 남은 그림에는 버튼이 없다
    assert any(".st-key-urow_fr_doyun" in m.value and "mk-friend-in" in m.value for m in at.markdown)
    at.run()  # 다음 그리기에서는 사라진다
    assert not any('class="mk-ghost ' in m.value for m in at.markdown)

    _click(at, "dec_jiho")  # 마지막 요청은 섹션째 접힌다
    ghost = next(m.value for m in at.markdown if 'class="mk-ghost ' in m.value)
    assert "mk-ghost-dec last" in ghost and "거절했어요" in ghost
    assert any("mk-ghost-headline" in m.value for m in at.markdown)
    at.run()
    assert not any(m.value.startswith('<div class="mk-section"') and "친구 요청" in m.value for m in at.markdown)
