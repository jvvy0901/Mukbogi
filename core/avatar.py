"""프로필 사진 (프로토타입: Pravatar 더미 사진).

- 사용자 데이터에 profile_image(파일 경로 또는 URL)가 있으면 그걸 먼저 쓰고, 없을 때만 Pravatar를 쓴다.
  → 나중에 실제 프로필 사진이 생기면 profile_image만 채우면 된다.
- Pravatar 번호(1~70)는 사용자 아이디로 고정해서, 같은 사람은 항상 같은 사진이 나온다(그릴 때마다 바뀌지 않음).
  아이디가 숫자면 `id % 70 + 1`, 글자면 md5(아이디) % 70 + 1. (파이썬 hash()는 실행할 때마다 달라져 쓰지 않는다.
  crc32는 데모 사용자 준·수아가 같은 번호가 나와서 md5를 쓴다 — tests/test_avatar.py가 데모 사용자 8명이 서로 다른지 확인)
- 사진을 못 불러오면(오프라인 등) 이름 첫 글자 원이 보인다: 글자 원 위에 사진을 CSS 배경으로 겹쳐 두어,
  못 불러온 배경은 아무것도 그리지 않는다(<img>는 깨진 이미지 아이콘이 남아서 쓰지 않음).
"""

import hashlib
from html import escape
from pathlib import Path

from core.images import profile_thumb

PRAVATAR_URL = "https://i.pravatar.cc/{size}?img={number}"
PRAVATAR_COUNT = 70


def pravatar_number(user_id: int | str) -> int:
    """사용자 아이디 → Pravatar 사진 번호(1~70). 같은 아이디는 항상 같은 번호."""
    if isinstance(user_id, int) or str(user_id).isdigit():
        return int(user_id) % PRAVATAR_COUNT + 1
    return int(hashlib.md5(str(user_id).encode("utf-8")).hexdigest(), 16) % PRAVATAR_COUNT + 1


def pravatar_url(number: int, size: int = 150) -> str:
    """Pravatar 사진 번호(1~70)를 직접 골라 쓸 때의 주소."""
    return PRAVATAR_URL.format(size=size, number=number)


def get_avatar_url(user_id: int | str, size: int = 150, profile_image: str | Path | None = None) -> str:
    """프로필 사진 주소. profile_image(실제 사진)가 있으면 그것, 없으면 Pravatar 더미 사진."""
    if profile_image:
        if isinstance(profile_image, Path) or not str(profile_image).startswith(("http://", "https://", "data:")):
            path = Path(profile_image)
            if path.exists():
                return profile_thumb(path)
        else:
            return str(profile_image)
    return pravatar_url(pravatar_number(user_id), size)


def avatar_html(user_id: int | str, name: str, profile_image: str | Path | None = None,
                cls: str = "mk-avatar", size: int = 150) -> str:
    """원형 프로필: 이름 첫 글자 원 위에 사진을 겹친다. 사진을 못 불러오면 첫 글자가 보인다.
    이름이 바로 옆에 있으므로 스크린리더에는 숨긴다(aria-hidden)."""
    initial = escape(name[:1]) if name else "?"
    url = get_avatar_url(user_id, size, profile_image).replace("'", "%27")
    photo = escape(f"background-image:url('{url}')", quote=True)
    return (
        f'<span class="{cls} mk-avatar-initial" aria-hidden="true">{initial}'
        f'<span class="mk-avatar-photo" style="{photo}"></span></span>'
    )


def user_avatar(user, cls: str = "mk-avatar") -> str:
    """데모 사용자(core.demo.User)의 원형 프로필."""
    return avatar_html(user.id, user.name, user.profile_image, cls)
