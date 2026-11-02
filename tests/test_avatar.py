"""프로필 사진 규칙 (core/avatar.py): profile_image 우선, 없으면 아이디로 고정된 Pravatar, 실패하면 첫 글자."""

from PIL import Image

from core import avatar
from core.demo import USERS


def test_pravatar_number_is_stable_and_in_range():
    for u in USERS:
        n = avatar.pravatar_number(u.id)
        assert 1 <= n <= 70
        assert n == avatar.pravatar_number(u.id)  # 몇 번을 불러도 같다
    assert avatar.pravatar_number(0) == 1
    assert avatar.pravatar_number(69) == 70
    assert avatar.pravatar_number(70) == 1
    assert avatar.pravatar_number("140") == 1  # 숫자 아이디는 id % 70 + 1


def test_demo_users_all_get_different_photos():
    numbers = [avatar.pravatar_number(u.id) for u in USERS]
    assert len(set(numbers)) == len(USERS)
    assert all(u.profile_image is None for u in USERS)  # 데모 사용자는 모두 Pravatar 더미 사진


def test_get_avatar_url_uses_pravatar_format_and_size():
    url = avatar.get_avatar_url("sua")
    assert url == f"https://i.pravatar.cc/150?img={avatar.pravatar_number('sua')}"
    assert avatar.get_avatar_url("sua", size=96).startswith("https://i.pravatar.cc/96?img=")


def test_profile_image_takes_priority(tmp_path):
    assert avatar.get_avatar_url("sua", profile_image="https://example.com/me.png") == "https://example.com/me.png"
    local = tmp_path / "me.png"  # 로컬 실제 사진 파일
    Image.new("RGB", (64, 64), (255, 138, 61)).save(local)
    assert avatar.get_avatar_url("haneul", profile_image=local).startswith("data:image/")
    # 경로가 없는 파일이면 Pravatar로 돌아간다
    assert avatar.get_avatar_url("x", profile_image="no/such/file.png").startswith("https://i.pravatar.cc/")


def test_avatar_html_has_initial_fallback_under_photo():
    html = avatar.avatar_html("sua", "수아", cls="mk-avatar mk-avatar-md")
    assert html.startswith('<span class="mk-avatar mk-avatar-md mk-avatar-initial" aria-hidden="true">수<span class="mk-avatar-photo"')
    assert "background-image:url(&#x27;https://i.pravatar.cc/150?img=" in html
