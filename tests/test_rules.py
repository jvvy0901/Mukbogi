import pytest

from core.data import FOODS, Food
from core.rules import daily_targets, food_groups


def _food(kcal: int) -> Food:
    return Food(f"f{kcal}", f"음식{kcal}", "테스트", kcal, 10, "x.png")


def test_mvp_targets_match_prd():
    # 10종: 소식가 (150+150+180)/3=160, 중식가 (200+250+300+480)/4=307.5→308, 대식가 (600+600+1000)/3=733.3→733
    assert daily_targets(FOODS) == {"대식가": 733, "중식가": 308, "소식가": 160}


def test_mvp_groups_match_prd():
    names = {t: {f.name for f in g} for t, g in food_groups(FOODS).items()}
    assert names == {
        "대식가": {"마라탕", "파스타", "후라이드치킨"},
        "중식가": {"군고구마", "아이스크림", "어묵탕", "떡볶이"},  # 남는 1개는 적당한 그룹
        "소식가": {"탕후루", "붕어빵", "과일모찌"},
    }


def test_remainder_goes_to_middle_group():
    groups = food_groups([_food(k) for k in (100, 200, 300, 400, 500, 600, 700)])
    assert [f.kcal for f in groups["소식가"]] == [100, 200]
    assert [f.kcal for f in groups["중식가"]] == [300, 400, 500]
    assert [f.kcal for f in groups["대식가"]] == [600, 700]


def test_target_rounds_half_up():
    targets = daily_targets([_food(k) for k in (100, 101, 200, 201, 300, 301)])
    assert targets == {"소식가": 101, "중식가": 201, "대식가": 301}


def test_needs_at_least_three_foods():
    with pytest.raises(ValueError):
        food_groups([_food(100), _food(200)])
