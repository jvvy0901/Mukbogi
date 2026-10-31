"""내정보 화면 테스트."""

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
    at.button(key="tab_my").click().run()
    assert not at.exception
    return at


def _click(at, key):
    at.button(key=key).click().run()
    assert not at.exception


def _has_ad(at):
    return any('aria-label="광고 자리"' in m.value for m in at.markdown)


def _text(at):
    return re.sub(r"<[^>]+>", "", " ".join(m.value for m in at.markdown))


def test_my_tab_opens_page_with_profile_summary():
    at = _start()
    assert at.session_state["screen"] == "my"
    text = _text(at)
    assert "내정보" in text and "@mukbo_me" in text
    assert "친구4명" in text.replace(" ", "")
    assert "하루 목표 365kcal" in text
    assert "소화하고 싶은 음식" not in text  # 내정보에서는 선호 음식을 바꾸지 않는다


def test_change_eater_type_updates_daily_target():
    at = _start()
    _click(at, "mtype_big")
    assert at.session_state["profile"]["eater_type"] == "대식가"
    assert at.session_state["profile"]["daily_target_kcal"] == 600
    assert "하루 목표 600kcal" in _text(at)


def test_weight_save_without_clear_button():
    at = _start()
    at.number_input(key="my_weight").set_value(55.0).run()
    assert at.session_state["profile"]["weight_kg"] == 55.0
    assert "체중을 저장했어요" in _text(at)
    assert not any("지우기" in (b.label or "") for b in at.button)  # 체중 지우기 버튼은 없다


def test_fridge_visibility_default_and_change():
    at = _start()
    assert at.session_state["profile"]["fridge_visibility"] == "친구만"
    _click(at, "mvis_private")
    assert at.session_state["profile"]["fridge_visibility"] == "비공개"
    assert "아무도 내 냉장고를 볼 수 없어요" in _text(at)


def test_plus_toggle_hides_home_ad():
    at = _start()
    _click(at, "plus_on")
    assert at.session_state["plus"] is True
    _click(at, "tab_home")
    assert not _has_ad(at)
    _click(at, "tab_my")
    _click(at, "plus_off")
    _click(at, "tab_home")
    assert _has_ad(at)


def test_reset_asks_first_then_returns_to_onboarding():
    at = _start()
    _click(at, "reset_ask")
    assert "온보딩부터 다시 할까요?" in _text(at)
    _click(at, "reset_no")
    assert "profile" in at.session_state
    _click(at, "reset_ask")
    _click(at, "reset_ok")
    assert "profile" not in at.session_state
    assert "하루에 얼마나" in _text(at)
