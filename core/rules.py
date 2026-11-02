"""계산 규칙. CLAUDE.md "핵심 규칙"과 PRD.md "유형별 하루 목표 칼로리 산정"을 따른다.

프로토타입이어도 정식 앱과 같은 규칙으로 계산한다.
"""

from collections.abc import Sequence

from core.data import Food

# 칼로리 높은 그룹부터. 대식가 = 높은 그룹, 중식가 = 적당한 그룹, 소식가 = 낮은 그룹.
EATER_TYPES: tuple[str, ...] = ("대식가", "중식가", "소식가")

DEFAULT_WEIGHT_KG = 60

# 소모 칼로리(초안) = 몸무게(kg) × 거리(km) × 활동 계수. 계수는 PRD Q9에서 확정 예정.
ACTIVITY_FACTORS: dict[str, float] = {"걷기": 0.5, "달리기": 1.0}


def burned_kcal(distance_km: float, activity: str, weight_kg: float | None = None) -> float:
    weight = DEFAULT_WEIGHT_KG if weight_kg is None else weight_kg
    return weight * distance_km * ACTIVITY_FACTORS[activity]


def food_groups(foods: Sequence[Food]) -> dict[str, list[Food]]:
    """음식을 칼로리 오름차순으로 정렬해 낮은/적당한/높은 3그룹으로 똑같이 나눈다.

    3으로 나누어떨어지지 않으면 남는 음식은 적당한 그룹(중식가)에 넣는다.
    """
    if len(foods) < 3:
        raise ValueError("유형별 목표를 정하려면 음식이 3개 이상 필요해요.")

    ordered = sorted(foods, key=lambda f: f.kcal)
    n = len(ordered)
    k = n // 3
    return {
        "소식가": ordered[:k],
        "중식가": ordered[k : n - k],
        "대식가": ordered[n - k :],
    }


def daily_targets(foods: Sequence[Food]) -> dict[str, int]:
    """유형별 하루 목표 칼로리 = 해당 그룹 칼로리 평균 (소수점은 반올림)."""
    targets = {}
    for eater_type, group in food_groups(foods).items():
        mean = sum(f.kcal for f in group) / len(group)
        targets[eater_type] = int(mean + 0.5)
    return targets


def food_count(kcal: float, food: Food) -> float:
    """소화한 칼로리가 음식 몇 개만큼인지 (예: 720kcal ÷ 떡볶이 480kcal = 1.5개)."""
    return max(0.0, kcal) / food.kcal


def format_count(count: float) -> str:
    """음식 개수 표시: 소수점 없이 반올림한 정수 (1.4 → 1, 1.5 → 2, 0.9 → 1).
    조금이라도 소화했으면 0개로 보이지 않게 최소 1개로 보여 준다."""
    if count <= 0:
        return "0"
    return str(max(1, int(count + 0.5)))


# 이번 주 소화 기준 음식이 더 높은 칼로리 음식으로 바뀌는 지점 (초안, PRD Story 3.8):
# 그 음식 칼로리의 90%까지 소화하면 "거의 한 개"이므로 그 음식으로 센다.
LEVEL_UP_RATIO = 0.9


def week_compare_food(total_kcal: float, base: Food, foods: Sequence[Food]) -> Food:
    """이번 주 소화를 셀 기준 음식.

    처음에는 base(온보딩에서 고른 첫 음식)로 세다가, 소화한 칼로리가 base보다 칼로리가 높은 음식의
    LEVEL_UP_RATIO(90%)에 다다르면 그 음식으로 바꾼다. 다다른 음식이 여럿이면 가장 높은 칼로리 음식.
    (칼로리가 같으면 음식 목록 앞쪽)"""
    reached = [f for f in foods if f.kcal > base.kcal and total_kcal >= f.kcal * LEVEL_UP_RATIO]
    if not reached:
        return base
    top = max(f.kcal for f in reached)
    return next(f for f in reached if f.kcal == top)
