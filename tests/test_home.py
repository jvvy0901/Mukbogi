"""홈 화면 흐름 테스트 (PRD Story 3.1 ~ 3.7, 6.1)."""

import re
from pathlib import Path

from streamlit.testing.v1 import AppTest

APP = str(Path(__file__).resolve().parent.parent / "app.py")
PROFILE = {"eater_type": "중식가", "daily_target_kcal": 365, "favorite_food_ids": ["pasta"], "weight_kg": None}


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


def _order(at, food_id):
    _click(at, "ord_" + food_id)
    _click(at, "order_submit")


def test_empty_home_shows_order_prompt_and_tabs():
    at = _start()
    text = _text(at)
    assert "주문하러 가요" in text
    assert "오늘 0 / 365kcal" in text
    assert "광고 자리" in text
    for key in ("tab_home", "tab_fridge", "tab_community", "tab_my"):
        at.button(key=key)
    _click(at, "home_order")
    assert at.session_state["screen"] == "order"


def test_order_requires_pick_then_returns_home():
    at = _start()
    _click(at, "home_order")
    assert at.button(key="order_submit").disabled
    _click(at, "ord_tanghuru")
    assert at.button(key="order_submit").label == "탕후루 주문하기"
    _click(at, "order_submit")
    assert at.session_state["screen"] == "home"
    assert at.button(key="home_start").label == "식사시작"
    assert "탕후루" in _text(at)


def test_start_stop_and_digest_by_bites():
    at = _start()
    _click(at, "home_order")
    _order(at, "pasta")  # 600kcal, 10입
    assert "한 입 0/10" in _text(at)

    _click(at, "home_start")
    assert at.button(key="home_stop").label == "멈추기"
    _click(at, "act_run")
    _click(at, "move_1_0")  # 달리기 1km = 60kcal = 1입
    text = _text(at)
    assert "한 입 1/10" in text
    assert "소화했어요" not in text  # 진행률은 한 입 수와 남은 칼로리로만 보여 준다
    assert "남은 540kcal" in text
    assert "1.00km" in text

    _click(at, "home_stop")
    assert not any((b.key or "").startswith("move_") for b in at.button)  # 멈추면 움직임이 반영되지 않는다
    assert "한 입 1/10" in _text(at)  # 진행 상황은 저장된 채 그대로
    assert at.button(key="home_start").label == "식사시작"


def test_waiting_queue_shows_in_order_and_more_tile():
    at = _start()
    _click(at, "home_order")
    _order(at, "pasta")
    assert at.button(key="home_more").label == "더 주문하기"
    _click(at, "home_more")
    _order(at, "ttuckbokki")
    _click(at, "home_more")
    _order(at, "icecream")
    text = _text(at)
    assert text.index("떡볶이") < text.index("아이스크림")


def test_finish_shows_celebration_and_overflow_goes_to_next():
    at = _start()
    _click(at, "home_order")
    _order(at, "tanghuru")  # 150kcal
    _click(at, "home_more")
    _order(at, "mocci")  # 180kcal
    _click(at, "home_start")
    _click(at, "act_run")
    _click(at, "move_3_0")  # 180kcal → 탕후루 완료 + 30kcal 넘김

    text = _text(at)
    assert "다 소화시켰다!" in text and "내 냉장고에 등록됐다" in text
    meal = at.session_state["meal"]
    assert [e.food_id for e in meal.fridge] == ["tanghuru"]
    assert round(meal.current.eaten_kcal) == 30

    _click(at, "done_next")
    assert "과일모찌" in _text(at)
    assert "오늘 180 / 365kcal" in _text(at)


def test_finish_last_food_then_fridge():
    at = _start()
    _click(at, "home_order")
    _order(at, "tanghuru")
    _click(at, "home_start")
    _click(at, "act_run")
    _click(at, "move_3_0")
    _click(at, "done_fridge")
    assert at.session_state["screen"] == "fridge"
    assert "지금까지 1개, 모두 150kcal를 소화했어요" in _text(at)
    _click(at, "tab_home")
    assert "주문하러 가요" in _text(at)


def test_friends_section_shows_progress_and_resting():
    at = _start()
    text = _text(at)
    assert "친구들이 소화 중이에요" in text
    assert "마라탕" in text and "62%" in text
    assert "쉬는 중이에요" in text


def test_toast_shows_once_then_disappears():
    at = _start()
    _click(at, "home_order")
    _order(at, "tanghuru")
    assert "탕후루를 주문했어요" in _text(at)
    assert not at.toast  # Streamlit 기본 팝업 토스트는 쓰지 않는다
    _click(at, "home_start")
    assert "탕후루를 주문했어요" not in _text(at)


def test_bite_toast():
    at = _start()
    _click(at, "home_order")
    _order(at, "pasta")
    _click(at, "home_start")
    _click(at, "act_run")
    _click(at, "move_1_0")
    assert "냠! 파스타 한 입 먹었어요 (1/10)" in _text(at)


def test_bite_mark_animation_plays_once_and_food_keeps_size():
    at = _start()
    _click(at, "home_order")
    _order(at, "pasta")
    _click(at, "home_start")
    _click(at, "act_run")
    _click(at, "move_1_0")  # 1입
    md = " ".join(m.value for m in at.markdown)
    assert 'class="mk-bite-prev"' in md and 'class="mk-plate chomp"' in md  # 방금 먹은 순간에만
    assert "10입 중 1입 먹음" in md
    assert "--s:" not in md  # 음식을 작게 줄이지 않는다
    _click(at, "act_walk")  # 다른 동작으로 다시 그리면 애니메이션은 없다
    md = " ".join(m.value for m in at.markdown)
    assert 'class="mk-bite-prev"' not in md and 'class="mk-plate"' in md and "10입 중 1입 먹음" in md
