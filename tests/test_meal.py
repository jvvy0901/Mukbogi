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


def test_week_by_day_counts_from_monday_and_partial_digestion():
    from datetime import date
    s = meal.MealState()
    s.digested_by_day = {date(2026, 10, 25): 999.0, date(2026, 11, 2): 120.0, date(2026, 11, 4): 300.5}
    days = s.week_by_day(date(2026, 11, 4))  # 수요일
    assert days == [120.0, 0.0, 300.5, 0.0, 0.0, 0.0, 0.0]  # 지난주 일요일(10/25)은 빠진다


def test_food_count_wording():
    from core import rules
    from core.data import FOODS_BY_ID
    assert rules.format_count(rules.food_count(720, FOODS_BY_ID["ttuckbokki"])) == "2"   # 1.5 → 반올림
    assert rules.format_count(rules.food_count(670, FOODS_BY_ID["ttuckbokki"])) == "1"   # 1.4 → 소수점 없이
    assert rules.format_count(rules.food_count(900, FOODS_BY_ID["chicken"])) == "1"      # 0.9 → 1
    assert rules.format_count(rules.food_count(5, FOODS_BY_ID["chicken"])) == "1"  # 조금이라도 먹었으면 0으로 안 보인다
    assert rules.format_count(rules.food_count(1600, FOODS_BY_ID["tanghuru"])) == "11"
    assert rules.format_count(0) == "0"


def test_week_compare_food_levels_up_near_higher_kcal_food():
    from core import rules
    from core.data import FOODS, FOODS_BY_ID
    pasta, chicken, tteok = FOODS_BY_ID["pasta"], FOODS_BY_ID["chicken"], FOODS_BY_ID["ttuckbokki"]
    assert rules.week_compare_food(600, pasta, FOODS) is pasta      # 파스타 1개
    assert rules.week_compare_food(899, pasta, FOODS) is pasta      # 치킨(1000)의 90% 전
    assert rules.week_compare_food(900, pasta, FOODS) is chicken    # 치킨 90% → 치킨으로
    assert rules.week_compare_food(3000, pasta, FOODS) is chicken   # 가장 높은 음식에서 멈춘다
    # 떡볶이(480)에서 시작하면 마라탕·파스타(600) 90%인 540에서 같은 칼로리 중 목록 앞쪽(마라탕)으로
    assert rules.week_compare_food(540, tteok, FOODS) is FOODS_BY_ID["maratang"]
    assert rules.week_compare_food(100, tteok, FOODS) is tteok       # 더 낮은 음식으로는 내려가지 않는다
