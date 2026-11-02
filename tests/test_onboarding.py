"""온보딩 흐름 테스트 (PRD Story 1.1 ~ 1.3 Acceptance Criteria)."""

import re
from pathlib import Path

from streamlit.testing.v1 import AppTest

APP = str(Path(__file__).resolve().parent.parent / "app.py")


def _start():
    at = AppTest.from_file(APP, default_timeout=60)
    at.session_state["splash_seen"] = True  # 스플래시는 tests/test_splash.py에서 따로 확인한다
    at.session_state["account"] = {"user_id": "tester", "method": "kakao", "marketing": False}  # 가입은 tests/test_auth.py
    at.run()
    assert not at.exception
    return at


def _click(at, key):
    at.button(key=key).click().run()
    assert not at.exception


def _markdown(at):
    """화면 글자만 비교하도록 HTML 태그를 뺀다."""
    return re.sub(r"<[^>]+>", "", " ".join(m.value for m in at.markdown))


def test_step1_shows_three_types_and_next_disabled_until_chosen():
    at = _start()
    labels = [b.label for b in at.button]
    for t in ("대식가", "중식가", "소식가"):
        assert f"{t} 선택하기" in labels
    md = _markdown(at)
    for kcal in (733, 308, 160):
        assert f"하루 목표 {kcal}kcal" in md
    assert at.button(key="ob_next_0").disabled

    _click(at, "ob_pick_mid")
    assert at.session_state["ob_type"] == "중식가"
    assert not at.button(key="ob_next_0").disabled


def test_step2_requires_at_least_one_food_and_toggles():
    at = _start()
    _click(at, "ob_pick_big")
    _click(at, "ob_next_0")

    food_buttons = [b for b in at.button if (b.key or "").startswith("ob_food_")]
    assert len(food_buttons) == 10
    assert at.button(key="ob_next_1").disabled

    _click(at, "ob_food_pasta")
    _click(at, "ob_food_tanghuru")
    assert at.session_state["ob_foods"] == ["tanghuru", "pasta"]
    assert at.button(key="ob_food_pasta").label == "파스타 빼기"
    assert not at.button(key="ob_next_1").disabled

    _click(at, "ob_food_pasta")
    assert at.session_state["ob_foods"] == ["tanghuru"]


def _to_step3(at):
    _click(at, "ob_pick_small")
    _click(at, "ob_next_0")
    _click(at, "ob_food_mocci")
    _click(at, "ob_next_1")


def test_skip_weight_uses_default():
    at = _start()
    _to_step3(at)
    _click(at, "ob_skip")

    assert at.session_state["profile"] == {
        "eater_type": "소식가",
        "daily_target_kcal": 160,
        "favorite_food_ids": ["mocci"],
        "weight_kg": None,
        "gender": None,
        "height_cm": None,
    }
    assert "주문하러 가요" in _markdown(at)  # 온보딩이 끝나면 홈으로 간다


def test_start_without_weight_shows_error():
    at = _start()
    _to_step3(at)
    _click(at, "ob_start")
    assert "profile" not in at.session_state
    assert "몸무게를 입력하거나 건너뛰기를 눌러 주세요" in _markdown(at)


def test_entered_weight_is_saved():
    at = _start()
    _to_step3(at)
    at.number_input(key="ob_weight").set_value(55.5).run()
    _click(at, "ob_start")
    assert at.session_state["profile"]["weight_kg"] == 55.5


def test_gender_and_height_are_saved_and_optional():
    at = _start()
    _to_step3(at)
    assert "성별" in _markdown(at)
    _click(at, "gen_female")
    _click(at, "gen_male")  # 다른 쪽을 누르면 바뀐다
    at.number_input(key="ob_height").set_value(168.0).run()
    at.number_input(key="ob_weight").set_value(60.0).run()
    _click(at, "ob_start")
    p = at.session_state["profile"]
    assert p["gender"] == "male" and p["height_cm"] == 168.0 and p["weight_kg"] == 60.0


def test_gender_tap_again_clears():
    at = _start()
    _to_step3(at)
    _click(at, "gen_female")
    _click(at, "gen_female")
    assert at.session_state["ob_gender"] is None


def test_back_keeps_previous_choice():
    at = _start()
    _to_step3(at)
    _click(at, "ob_back_2")
    assert at.button(key="ob_food_mocci").label == "과일모찌 빼기"


def test_weight_kept_after_going_back():
    at = _start()
    _to_step3(at)
    at.number_input(key="ob_weight").set_value(70.0).run()
    _click(at, "ob_back_2")
    _click(at, "ob_next_1")
    assert at.number_input(key="ob_weight").value == 70.0


def test_step_header_slides_in_matching_direction():
    """처음 열 때는 움직이지 않고, 다음 단계는 오른쪽에서·이전 단계는 왼쪽에서 들어온다."""
    at = _start()
    header = lambda: next(m.value for m in at.markdown if 'class="mk-header' in m.value)
    assert 'class="mk-header"' in header()
    _click(at, "ob_pick_mid")
    _click(at, "ob_next_0")
    assert "mk-header mk-fwd" in header()
    assert 'class="on now"' in next(m.value for m in at.markdown if "mk-progress" in m.value and "<span" in m.value)
    _click(at, "ob_back_1")
    assert "mk-header mk-back" in header()
