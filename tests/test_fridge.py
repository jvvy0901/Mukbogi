"""냉장고 테스트 (PRD Story 4.1, 4.2)."""

import re
from datetime import date, datetime
from pathlib import Path

from streamlit.testing.v1 import AppTest

from core.fridge import day_label, group_by_day
from core.meal import FridgeEntry, MealState

APP = str(Path(__file__).resolve().parent.parent / "app.py")
TODAY = date(2026, 10, 31)  # 토요일


def _e(food_id, kcal, when):
    return FridgeEntry(food_id, kcal, 1.0, when)


ENTRIES = [
    _e("tanghuru", 150, datetime(2026, 10, 30, 9, 0)),
    _e("pasta", 600, datetime(2026, 10, 31, 8, 30)),
    _e("mocci", 180, datetime(2026, 10, 30, 20, 15)),
    _e("icecream", 250, datetime(2026, 10, 31, 18, 40)),
    _e("ttuckbokki", 480, datetime(2026, 10, 28, 12, 0)),
]


def test_day_labels():
    assert day_label(date(2026, 10, 31), TODAY) == "오늘 · 10월 31일 (토)"
    assert day_label(date(2026, 10, 30), TODAY) == "어제 · 10월 30일 (금)"
    assert day_label(date(2026, 10, 28), TODAY) == "10월 28일 (수)"
    assert day_label(date(2025, 12, 31), TODAY) == "2025년 12월 31일 (수)"


def test_groups_newest_day_first_with_totals_and_newest_item_first():
    groups = group_by_day(ENTRIES, TODAY, daily_target_kcal=365)
    assert [g.day for g in groups] == [date(2026, 10, 31), date(2026, 10, 30), date(2026, 10, 28)]
    assert [g.total_kcal for g in groups] == [850, 330, 480]
    assert [e.food_id for e in groups[0].entries] == ["icecream", "pasta"]
    assert [e.food_id for e in groups[1].entries] == ["mocci", "tanghuru"]


def test_goal_met_when_total_reaches_daily_target():
    groups = group_by_day(ENTRIES, TODAY, daily_target_kcal=365)
    assert [g.goal_met for g in groups] == [True, False, True]


def _text(at):
    return re.sub(r"<[^>]+>", "", " ".join(m.value for m in at.markdown))


def _app(entries):
    at = AppTest.from_file(APP, default_timeout=60)
    at.session_state["profile"] = {
        "eater_type": "중식가", "daily_target_kcal": 365, "favorite_food_ids": ["pasta"], "weight_kg": None,
    }
    at.session_state["meal"] = MealState(fridge=list(entries))
    at.session_state["screen"] = "fridge"
    at.run()
    assert not at.exception
    return at


def test_empty_fridge_shows_message_and_order_button():
    at = _app([])
    assert "아직 냉장고가 비어 있어요" in _text(at)
    at.button(key="fridge_order").click().run()
    assert at.session_state["screen"] == "order"


def test_fridge_lists_days_items_and_goal_badge():
    at = _app(ENTRIES)
    text = _text(at)
    assert "지금까지 5개, 모두 1660kcal를 소화했어요" in text
    assert text.index("10월 31일") < text.index("10월 30일") < text.index("10월 28일")
    assert "목표 달성" in text
    for name, time in (("아이스크림", "18:40"), ("파스타", "08:30"), ("과일모찌", "20:15")):
        assert name in text and time in text


def test_fixed_order_button_goes_to_order_and_back_returns_to_fridge():
    at = _app(ENTRIES)
    assert at.button(key="fridge_more").label == "더 주문하러 가기"
    at.button(key="fridge_more").click().run()
    assert at.session_state["screen"] == "order"
    at.button(key="order_back").click().run()
    assert at.session_state["screen"] == "fridge"


def test_empty_fridge_has_no_fixed_button():
    at = _app([])
    assert not any(b.key == "fridge_more" for b in at.button)
