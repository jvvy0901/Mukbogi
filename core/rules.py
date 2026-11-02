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


# 이번 주 소화를 음식으로 셀 때 "거의 맞는다"고 보는 차이 (초안, PRD Story 3.8):
# 음식 개수 × 칼로리가 실제 소화 칼로리와 10% 안으로 차이 나면 맞는 음식으로 본다.
MATCH_TOLERANCE = 0.1


def _rounded_count(total_kcal: float, food: Food) -> int:
    return max(1, int(total_kcal / food.kcal + 0.5))


def match_error(total_kcal: float, food: Food) -> float:
    """화면에 보이는 개수(정수)로 바꿨을 때 실제 칼로리와의 차이 비율. 150kcal를 마라탕 1개(600)로 보이면 3.0."""
    return abs(_rounded_count(total_kcal, food) * food.kcal - total_kcal) / total_kcal


def week_compare_foods(total_kcal: float, foods: Sequence[Food], favorites: Sequence[Food] = ()) -> list[Food]:
    """이번 주 소화 칼로리에 가장 잘 맞는 음식 순서 (첫 번째가 큰 문구, 다음이 "다른 음식으로는" 칩).

    1. 정수 개수로 바꿨을 때 차이가 10% 안인 음식이 먼저. 그중에서는 개수가 적은(= 칼로리가 큰) 음식부터 —
       "떡볶이 3개"가 "탕후루 10개"보다 한눈에 들어온다.
    2. 10% 안인 음식이 없으면 차이가 작은 음식부터.
    같으면 차이가 작은 쪽 → 온보딩에서 고른 음식 → 음식 목록 순서.
    예: 150kcal → 탕후루 1개, 360kcal → 과일모찌 2개, 900kcal → 후라이드치킨 1개, 1500kcal → 떡볶이 3개."""
    fav_rank = {f.id: i for i, f in enumerate(favorites)}
    order = {f.id: i for i, f in enumerate(foods)}

    def key(f: Food):
        err = match_error(total_kcal, f)
        close = err <= MATCH_TOLERANCE + 1e-9
        primary = _rounded_count(total_kcal, f) if close else err
        return (0 if close else 1, primary, err, fav_rank.get(f.id, len(fav_rank)), order[f.id])

    return sorted(foods, key=key) if total_kcal > 0 else list(foods)
