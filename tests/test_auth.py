"""로그인 · 회원가입 테스트 (PRD Q10: 카카오 · Apple · 네이버 · Google · 휴대폰 번호)."""

import re
from pathlib import Path

from streamlit.testing.v1 import AppTest

from core import auth, social
from core.demo import ME_ID

APP = str(Path(__file__).resolve().parent.parent / "app.py")


def _start():
    at = AppTest.from_file(APP, default_timeout=60)
    at.session_state["splash_seen"] = True
    at.run()
    assert not at.exception
    return at


def _click(at, key):
    at.button(key=key).click().run()
    assert not at.exception


def _text(at):
    return re.sub(r"<[^>]+>", "", " ".join(m.value for m in at.markdown if "<div" in m.value))


# 규칙 --------------------------------------------------------------------------


def test_user_id_rules():
    assert auth.check_user_id("") == "empty"
    assert auth.check_user_id("ab") == "format"          # 4자 미만
    assert auth.check_user_id("Mukbo-Lover") == "format"  # 하이픈
    assert auth.check_user_id("haneul") == "taken"        # 더미 유저와 겹침
    assert auth.check_user_id("@Mukbo_Lover") == "ok"     # 앞 @·대문자는 정리해서 본다


def test_nickname_rules():
    assert auth.check_nickname("") == "empty"
    assert auth.check_nickname("나") == "format"           # 1자
    assert auth.check_nickname("떡볶이 요정") == "format"   # 띄어쓰기
    assert auth.check_nickname("먹보!") == "format"         # 특수문자
    assert auth.check_nickname("가나다라마바사아자차카") == "format"  # 11자
    assert auth.check_nickname("떡볶이요정") == "ok"
    assert auth.check_nickname("Mukbo99") == "ok"


def test_nickname_shows_on_my_page_and_ranking():
    at = AppTest.from_file(APP, default_timeout=60)
    at.session_state["account"] = {"user_id": "mukbo_lover", "nickname": "떡볶이요정", "method": "kakao", "marketing": False}
    at.session_state["profile"] = {"eater_type": "중식가", "daily_target_kcal": 308, "favorite_food_ids": ["pasta"], "weight_kg": None}
    at.session_state["screen"] = "my"
    at.run()
    assert not at.exception
    assert "떡볶이요정" in _text(at)
    at.session_state["screen"] = "community"
    at.session_state["comm_tab"] = "rank"
    at.run()
    assert not at.exception
    assert any('class="mk-rk-name">떡볶이요정<span class="mk-me-pill">나</span>' in m.value for m in at.markdown)


def test_phone_and_code_rules():
    assert auth.normalize_phone("010-1234-5678") == "01012345678"
    assert auth.normalize_phone("01112345678") is None
    assert auth.normalize_phone("010-123-456") is None
    assert auth.check_code("123456") and not auth.check_code("12345") and not auth.check_code("abcdef")


def test_required_terms():
    required = {t.key for t in auth.TERMS if t.required}
    assert not auth.required_agreed(set())
    assert auth.required_agreed(required)           # 선택(마케팅)은 없어도 된다
    assert "marketing" not in required


def test_find_user_recognizes_my_signed_up_id():
    assert social.find_user("mukbo_lover", "mukbo_lover") == ME_ID


# 화면 흐름 ----------------------------------------------------------------------


def test_login_shows_five_methods():
    at = _start()
    keys = {b.key for b in at.button}
    assert {"auth_kakao", "auth_apple", "auth_phone", "auth_naver", "auth_google"} <= keys
    assert "MUKBOGI" in _text(at)


def test_social_signup_terms_then_id_then_nickname_then_onboarding():
    at = _start()
    _click(at, "auth_kakao")
    assert at.session_state["auth_step"] == "terms"
    assert "카카오 계정을 확인했어요" in _text(at)
    assert at.button(key="auth_terms_next").disabled  # 필수 동의 전에는 못 넘어간다
    _click(at, "auth_all")
    assert not at.button(key="auth_terms_next").disabled
    _click(at, "auth_terms_next")
    assert at.session_state["auth_step"] == "id"

    at.text_input(key="auth_in_id").input("haneul").run()
    _click(at, "auth_id_next")
    assert "이미 쓰고 있는 아이디예요" in _text(at)
    at.text_input(key="auth_in_id").input("mukbo_lover").run()
    _click(at, "auth_id_next")
    assert at.session_state["auth_step"] == "nick"
    assert "@mukbo_lover" in _text(at)  # 정한 아이디를 별명 화면에서도 보여 준다

    at.text_input(key="auth_in_nick").input("떡볶이 요정").run()  # 띄어쓰기는 안 된다
    _click(at, "auth_signup")
    assert "한글·영문·숫자로 2~10자" in _text(at)
    _click(at, "auth_back_nick")  # 이전으로 가도 아이디가 남아 있다
    assert at.text_input(key="auth_in_id").value == "mukbo_lover"
    _click(at, "auth_id_next")
    at.text_input(key="auth_in_nick").input("떡볶이요정").run()
    _click(at, "auth_signup")
    assert at.session_state["account"] == {
        "user_id": "mukbo_lover", "nickname": "떡볶이요정", "method": "kakao", "marketing": True,
    }
    assert any(b.key == "ob_next_0" for b in at.button)  # 가입하면 온보딩이 이어진다


def test_terms_toggle_individually_and_optional_is_optional():
    at = _start()
    _click(at, "auth_apple")
    for t in auth.TERMS:
        if t.required:
            _click(at, f"auth_term_{t.key}")
    assert not at.button(key="auth_terms_next").disabled
    _click(at, "auth_term_service")  # 필수 하나 해제
    assert at.button(key="auth_terms_next").disabled


def test_phone_verification_flow():
    at = _start()
    _click(at, "auth_phone")
    at.text_input(key="auth_in_phone").input("0101234").run()
    _click(at, "auth_send")
    assert "010으로 시작하는 11자리" in _text(at)
    at.text_input(key="auth_in_phone").input("010-1234-5678").run()
    _click(at, "auth_send")
    at.text_input(key="auth_in_code").input("12").run()
    _click(at, "auth_verify")
    assert "인증번호 6자리를 입력해 주세요" in _text(at)
    at.text_input(key="auth_in_code").input("123456").run()
    _click(at, "auth_verify")
    assert at.session_state["auth_step"] == "terms"
    assert "휴대폰 번호를 확인했어요" in _text(at)
    _click(at, "auth_back_terms")
    assert at.session_state["auth_step"] == "phone"


def test_my_id_shows_on_my_page_after_signup():
    at = AppTest.from_file(APP, default_timeout=60)
    at.session_state["account"] = {"user_id": "mukbo_lover", "method": "naver", "marketing": False}
    at.session_state["profile"] = {"eater_type": "중식가", "daily_target_kcal": 365, "favorite_food_ids": ["pasta"], "weight_kg": None}
    at.session_state["screen"] = "my"
    at.run()
    assert not at.exception
    assert "@mukbo_lover" in _text(at)


def test_errors_shake_again_on_each_failed_try_and_select_all_cascades():
    at = _start()
    _click(at, "auth_phone")
    at.text_input(key="auth_in_phone").input("0101").run()
    _click(at, "auth_send")
    first = next(m.value for m in at.markdown if "animation: mk-shake-" in m.value and "auth_in_phone" in m.value)
    _click(at, "auth_send")  # 같은 실수를 또 하면 다른 이름의 흔들림으로 바뀌어 다시 재생된다
    second = next(m.value for m in at.markdown if "animation: mk-shake-" in m.value and "auth_in_phone" in m.value)
    assert first != second

    at = _start()
    _click(at, "auth_kakao")
    _click(at, "auth_all")
    assert sum("mk-cascade" in m.value for m in at.markdown if "<div class=\"mk-card mk-term" in m.value) == len(auth.TERMS)
    _click(at, "auth_term_marketing")  # 하나만 바꿀 때는 차례 연출 없이 바로
    assert not any("mk-cascade" in m.value for m in at.markdown if "<div class=\"mk-card mk-term" in m.value)


def test_signup_slides_into_onboarding():
    at = _start()
    _click(at, "auth_naver")
    _click(at, "auth_all")
    _click(at, "auth_terms_next")
    at.text_input(key="auth_in_id").input("mukbo_lover").run()
    _click(at, "auth_id_next")
    at.text_input(key="auth_in_nick").input("먹보").run()
    _click(at, "auth_signup")
    assert any("mk-header mk-fwd" in m.value for m in at.markdown)
