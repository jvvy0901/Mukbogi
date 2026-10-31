"""주문·소화·냉장고 상태와 규칙. Streamlit과 분리해 테스트할 수 있게 둔다.

PRD Story 2.3(대기열), 3.2(식사시작/멈추기), 3.3(한 입), 3.5(소화 완료·넘김)을 따른다.
"""

from dataclasses import dataclass, field
from datetime import date, datetime

from core.data import FOODS_BY_ID, Food
from core.rules import burned_kcal

MAX_WAITING = 5  # 대기열 최대 개수 (가설, PRD Q4). 소화 중인 음식은 세지 않는다.
_EPS = 1e-6


@dataclass
class Order:
    food_id: str
    eaten_kcal: float = 0.0
    distance_km: float = 0.0
    sender: str | None = None  # 친구가 배달로 보낸 음식이면 보낸 친구 이름

    @property
    def food(self) -> Food:
        return FOODS_BY_ID[self.food_id]

    @property
    def bite_kcal(self) -> float:
        """한 입 = 음식 칼로리 ÷ 입 수."""
        return self.food.kcal / self.food.bites

    @property
    def bites_eaten(self) -> int:
        return min(self.food.bites, int((self.eaten_kcal + _EPS) // self.bite_kcal))

    @property
    def remaining_kcal(self) -> float:
        return max(0.0, self.food.kcal - self.eaten_kcal)

    @property
    def progress(self) -> float:
        return min(1.0, self.eaten_kcal / self.food.kcal)


@dataclass
class FridgeEntry:
    food_id: str
    kcal: int
    distance_km: float
    completed_at: datetime


@dataclass
class MealState:
    orders: list[Order] = field(default_factory=list)  # [0] = 소화 중, 나머지 = 조리 중(대기)
    measuring: bool = False
    fridge: list[FridgeEntry] = field(default_factory=list)
    digested_by_day: dict[date, float] = field(default_factory=dict)

    @property
    def current(self) -> Order | None:
        return self.orders[0] if self.orders else None

    @property
    def waiting(self) -> list[Order]:
        return self.orders[1:]

    def digested_on(self, day: date) -> float:
        return self.digested_by_day.get(day, 0.0)


def can_order(state: MealState) -> bool:
    return state.current is None or len(state.waiting) < MAX_WAITING


def order(state: MealState, food_id: str, sender: str | None = None) -> bool:
    """음식을 주문한다(친구가 보낸 배달도 같은 길로 들어온다). 소화 중인 음식이 있으면 대기열 끝에 들어간다."""
    if food_id not in FOODS_BY_ID or not can_order(state):
        return False
    state.orders.append(Order(food_id, sender=sender))
    return True


def start(state: MealState) -> None:
    if state.current is not None:
        state.measuring = True


def stop(state: MealState) -> None:
    state.measuring = False


def move(
    state: MealState,
    distance_km: float,
    activity: str,
    weight_kg: float | None,
    now: datetime,
) -> list[FridgeEntry]:
    """움직인 만큼 소화한다. 다 소화한 음식은 냉장고로 옮기고 그 목록을 돌려준다.

    - 측정 중일 때만 반영한다.
    - 한 음식을 다 먹고 남은 칼로리는 대기열의 다음 음식으로 넘긴다.
    - 대기열까지 비면 측정을 멈추고, 남은 칼로리는 버린다.
    """
    if not state.measuring or state.current is None or distance_km <= 0:
        return []

    kcal_per_km = burned_kcal(1.0, activity, weight_kg)
    left = distance_km * kcal_per_km
    completed: list[FridgeEntry] = []

    while left > _EPS and state.current is not None:
        current = state.current
        take = min(current.remaining_kcal, left)
        current.eaten_kcal += take
        current.distance_km += take / kcal_per_km
        left -= take
        state.digested_by_day[now.date()] = state.digested_on(now.date()) + take

        if current.remaining_kcal <= _EPS:
            entry = FridgeEntry(current.food_id, current.food.kcal, current.distance_km, now)
            state.fridge.append(entry)
            state.orders.pop(0)
            completed.append(entry)

    if state.current is None:
        state.measuring = False
    return completed
