"""프로토타입용 더미 데이터 (PRD 프로토타입 대체 표: "친구·랭킹·다른 유저 냉장고 → 미리 준비한 더미 데이터").

프로필 사진은 assets/img/profile/에 있는 파일만 쓰고, 같은 사진을 두 번 쓰지 않는다.
사진이 없는 친구는 이름 첫 글자 아바타로 보여 준다.
"""

from dataclasses import dataclass
from pathlib import Path

from core.data import ROOT

PROFILE_DIR = ROOT / "assets" / "img" / "profile"


@dataclass(frozen=True)
class Friend:
    name: str
    photo: Path | None
    food_id: str | None  # None이면 쉬는 중
    progress: float  # 0~1


FRIENDS: tuple[Friend, ...] = (
    Friend("하늘", PROFILE_DIR / "포근한 분위기의 셀카 초상.png", "maratang", 0.62),
    Friend("준", PROFILE_DIR / "손에 기대어 찍은 편안한 셀카.png", "icecream", 0.30),
    Friend("수아", None, "mocci", 0.85),
    Friend("민", None, None, 0.0),
)
