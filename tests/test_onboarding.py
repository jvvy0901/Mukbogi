"""온보딩 흐름 테스트 (PRD Story 1.1 ~ 1.3 Acceptance Criteria)."""

from pathlib import Path

from streamlit.testing.v1 import AppTest

APP = str(Path(__file__).resolve().parent.parent / "app.py")


def _button(at, key):
    return at.button(key=key)


def _start():
    at = AppTest.from_file(APP, default_timeout=30)
    at.run()
    assert not at.exception
    return at


def test_step1_shows_three_types_and_next_disabled_until_chosen():
    at = _start()
    labels = [b.label for b in at.button]
    for t in ("대식가", "중식가", "소식가"):
        assert f"{t} 선택하기" in labels
    md = " ".join(m.value for m in at.markdown)
    for kcal in (600, 365, 165):
        assert f"하루 목표 {kcal}kcal" in md
    assert _button(at, "ob_next_0").disabled

    _button(at, "ob_pick_중식가").click().run()
    assert not _button(at, "ob_next_0").disabled


def test_step2_requires_at_least_one_food():
    at = _start()
    _button(at, "ob_pick_대식가").click().run()
    _button(at, "ob_next_0").click().run()

    assert len(at.checkbox) == 6
    assert _button(at, "ob_next_1").disabled

    at.checkbox(key="ob_food_pasta").check().run()
    at.checkbox(key="ob_food_tanghuru").check().run()
    assert not _button(at, "ob_next_1").disabled


def _to_step3(at):
    _button(at, "ob_pick_소식가").click().run()
    _button(at, "ob_next_0").click().run()
    at.checkbox(key="ob_food_mocci").check().run()
    _button(at, "ob_next_1").click().run()


def test_skip_weight_uses_default():
    at = _start()
    _to_step3(at)
    _button(at, "ob_skip").click().run()

    profile = at.session_state["profile"]
    assert profile == {
        "eater_type": "소식가",
        "daily_target_kcal": 165,
        "favorite_food_ids": ["mocci"],
        "weight_kg": None,
    }
    assert any("준비 끝났어요" in m.value for m in at.markdown)


def test_entered_weight_is_saved():
    at = _start()
    _to_step3(at)
    assert _button(at, "ob_start").disabled

    at.number_input(key="ob_weight").set_value(55.5).run()
    _button(at, "ob_start").click().run()
    assert at.session_state["profile"]["weight_kg"] == 55.5


def test_back_keeps_previous_choice():
    at = _start()
    _to_step3(at)
    _button(at, "ob_back_2").click().run()
    assert at.checkbox(key="ob_food_mocci").value is True


def test_weight_kept_after_going_back():
    at = _start()
    _to_step3(at)
    at.number_input(key="ob_weight").set_value(70.0).run()
    _button(at, "ob_back_2").click().run()
    _button(at, "ob_next_1").click().run()
    assert at.number_input(key="ob_weight").value == 70.0
