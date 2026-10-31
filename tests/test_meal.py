"""주문·소화 규칙 테스트 (PRD Story 2.3, 3.2, 3.3, 3.5)."""

from datetime import datetime

import pytest

from core import meal
from core.rules import burned_kcal

NOW = datetime(2026, 10, 31, 18, 0)


def _state(*food_ids, measuring=True):
    s = meal.MealState()
    for f in food_ids:
        assert meal.order(s, f)
    if measuring:
        meal.start(s)
    return s


def test_burned_kcal_formula():
    assert burned_kcal(1.0, "걷기") == pytest.approx(30)  # 60kg 기본
    assert burned_kcal(2.0, "달리기", 50) == pytest.approx(100)


def test_bite_is_kcal_divided_by_bites():
    o = meal.Order("pasta")  # 600kcal, 10입
    assert o.bite_kcal == 60
    o.eaten_kcal = 119
    assert o.bites_eaten == 1
    o.eaten_kcal = 120
    assert o.bites_eaten == 2


def test_no_progress_when_not_measuring():
    s = _state("pasta", measuring=False)
    assert meal.move(s, 1.0, "달리기", 60, NOW) == []
    assert s.current.eaten_kcal == 0


def test_start_requires_food():
    s = meal.MealState()
    meal.start(s)
    assert not s.measuring


def test_move_digests_and_tracks_distance():
    s = _state("pasta")
    meal.move(s, 2.0, "달리기", 60, NOW)  # 120kcal
    assert s.current.eaten_kcal == pytest.approx(120)
    assert s.current.distance_km == pytest.approx(2.0)
    assert s.current.bites_eaten == 2
    assert s.digested_on(NOW.date()) == pytest.approx(120)


def test_completion_moves_to_fridge_and_overflow_goes_to_next():
    s = _state("tanghuru", "mocci")  # 150kcal, 180kcal
    done = meal.move(s, 3.0, "달리기", 60, NOW)  # 180kcal
    assert [e.food_id for e in done] == ["tanghuru"]
    assert s.fridge[0].kcal == 150
    assert s.fridge[0].distance_km == pytest.approx(2.5)
    assert s.current.food_id == "mocci"
    assert s.current.eaten_kcal == pytest.approx(30)
    assert s.measuring


def test_measuring_stops_when_queue_empty_and_overflow_dropped():
    s = _state("tanghuru")
    done = meal.move(s, 10.0, "달리기", 60, NOW)  # 600kcal
    assert len(done) == 1
    assert s.current is None
    assert not s.measuring
    assert s.digested_on(NOW.date()) == pytest.approx(150)


def test_waiting_queue_limit():
    s = _state("pasta", measuring=False)
    for _ in range(meal.MAX_WAITING):
        assert meal.order(s, "tanghuru")
    assert not meal.can_order(s)
    assert not meal.order(s, "tanghuru")
    assert len(s.waiting) == meal.MAX_WAITING
