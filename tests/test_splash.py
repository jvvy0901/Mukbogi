"""스플래시 화면 테스트: 새 세션에서 한 번 보이고, 누르면 온보딩으로 넘어간다."""

from pathlib import Path

from streamlit.testing.v1 import AppTest

APP = str(Path(__file__).resolve().parent.parent / "app.py")


def test_splash_shows_logo_only_then_tap_goes_to_login():
    at = AppTest.from_file(APP, default_timeout=60)
    at.run()
    assert not at.exception
    splash = [m.value for m in at.markdown if "mk-splash-logo" in m.value and "<div" in m.value]
    assert len(splash) == 1 and ">MUKBOGI<" in splash[0]
    assert not any(b.key == "auth_kakao" for b in at.button)  # 아직 로그인 화면이 아니다

    at.button(key="splash_skip").click().run()
    assert not at.exception
    assert at.session_state["splash_seen"] is True
    assert any(b.key == "auth_kakao" for b in at.button)  # 스플래시 다음은 로그인


def test_splash_not_shown_when_profile_exists():
    at = AppTest.from_file(APP, default_timeout=60)
    at.session_state["profile"] = {"eater_type": "중식가", "daily_target_kcal": 365, "foods": ["pasta"], "weight_kg": None}
    at.run()
    assert not at.exception
    assert not any(b.key == "splash_skip" for b in at.button)
