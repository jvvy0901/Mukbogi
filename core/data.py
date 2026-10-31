"""MVP 음식 데이터. 값은 PRD.md "음식 데이터 (MVP 기준값, 검증 필요)" 표를 따른다."""

from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FOOD_IMG_DIR = ROOT / "assets" / "img" / "food"


@dataclass(frozen=True)
class Food:
    id: str
    name: str
    category: str
    kcal: int
    bites: int
    image: str

    @property
    def image_path(self) -> Path:
        return FOOD_IMG_DIR / self.image


# 순서는 PRD Story 1.2의 음식 나열 순서를 따른다.
FOODS: tuple[Food, ...] = (
    Food("ttuckbokki", "떡볶이", "한식", 480, 10, "ttuckbokki.png"),
    Food("maratang", "마라탕", "중식", 600, 10, "maratang.png"),
    Food("tanghuru", "탕후루", "디저트", 150, 5, "tanghuru.png"),
    Food("mocci", "과일모찌", "디저트", 180, 5, "mocci.png"),
    Food("icecream", "아이스크림", "디저트", 250, 5, "icecream.png"),
    Food("pasta", "파스타", "양식", 600, 10, "pasta.png"),
)

FOODS_BY_ID: dict[str, Food] = {f.id: f for f in FOODS}
