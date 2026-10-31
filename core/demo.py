"""프로토타입용 더미 데이터 (PRD 프로토타입 대체 표: "친구·랭킹·다른 유저 냉장고 → 미리 준비한 더미 데이터").

프로필 사진은 assets/img/profile/에 있는 파일만 쓰고, 같은 사진을 두 번 쓰지 않는다.
사진이 없는 유저는 이름 첫 글자 아바타로 보여 준다.
"""

from dataclasses import dataclass
from pathlib import Path

from core.data import ROOT

PROFILE_DIR = ROOT / "assets" / "img" / "profile"

ME_ID = "mukbo_me"  # 프로토타입의 "나" (로그인 대신)
ME_NAME = "나"


@dataclass(frozen=True)
class User:
    id: str  # 친구 검색에 쓰는 아이디
    name: str
    photo: Path | None
    food_id: str | None  # 지금 소화 중인 음식. None이면 쉬는 중
    progress: float  # 0~1
    fridge_visibility: str  # "전체" | "친구만" | "비공개"
    history: tuple[tuple[str, int, int, int], ...] = ()  # 냉장고 기록: (음식, 며칠 전, 시, 분)


USERS: tuple[User, ...] = (
    User("haneul", "하늘", PROFILE_DIR / "포근한 분위기의 셀카 초상.png", "maratang", 0.62, "친구만",
         (("pasta", 0, 8, 10), ("tanghuru", 1, 19, 40), ("maratang", 2, 12, 5), ("icecream", 3, 21, 0), ("ttuckbokki", 4, 18, 30))),
    User("jun", "준", PROFILE_DIR / "손에 기대어 찍은 편안한 셀카.png", "icecream", 0.30, "전체",
         (("ttuckbokki", 0, 7, 50), ("mocci", 1, 22, 15), ("pasta", 3, 20, 0))),
    User("sua", "수아", None, "mocci", 0.85, "친구만",
         (("icecream", 1, 13, 20), ("tanghuru", 2, 17, 0), ("mocci", 5, 9, 45))),
    User("min", "민", None, None, 0.0, "비공개",
         (("tanghuru", 2, 18, 0),)),
    User("doyun", "도윤", None, "pasta", 0.40, "전체",
         (("maratang", 0, 9, 0), ("pasta", 1, 19, 10), ("ttuckbokki", 2, 20, 30), ("maratang", 3, 18, 0), ("icecream", 4, 15, 0))),
    User("seoyeon", "서연", None, "ttuckbokki", 0.15, "전체",
         (("pasta", 1, 8, 30), ("mocci", 2, 21, 0), ("maratang", 4, 19, 30))),
    User("jiho", "지호", None, None, 0.0, "친구만",
         (("icecream", 0, 12, 0), ("tanghuru", 3, 16, 40))),
    User("yerin", "예린", None, "maratang", 0.70, "비공개",
         (("maratang", 0, 7, 0), ("pasta", 1, 20, 0), ("maratang", 2, 19, 0), ("ttuckbokki", 3, 18, 0), ("pasta", 4, 12, 0))),
)

USERS_BY_ID: dict[str, User] = {u.id: u for u in USERS}

INITIAL_FRIENDS = ("haneul", "jun", "sua", "min")
INITIAL_RECEIVED_REQUESTS = ("doyun",)  # 처음부터 와 있는 친구 요청
