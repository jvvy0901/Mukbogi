"""로그인 · 회원가입 화면 (PRD Q10 확정: Apple · 카카오 · 네이버 · Google · 휴대폰 번호).

uibowl 레퍼런스
- 로그인: 앳플리·메디코치(위쪽 가운데 로고, 아래쪽에 큰 버튼을 세로로 쌓고 "또는" 아래 원형 아이콘). 큰 버튼: 카카오 · 네이버 · 휴대폰 번호, 원형: Google · Apple,
  메가MCG커피(위 그래픽 + 아래 버튼 묶음), 써브웨이(한 줄 제목 + 브랜드 색 버튼).
- 회원가입: 더벤티(단계 표시 + "전체 약관 동의" 상자 + 필수/선택 목록), 패스오더·앳플리(한 화면에 한 입력칸).

흐름 (프로토타입: 실제 계정 연동 없이 누르면 연동된 것처럼 바로 가입으로 넘어간다)
  로그인 ─ 소셜 버튼 ─────────────┐
         └ 휴대폰 번호 → 인증번호 ─┴→ 약관 동의 → 아이디 정하기 → (가입 완료) → 온보딩

상태: session_state.auth_step (login / phone / terms / id), 가입이 끝나면 session_state.account.
전화번호는 확인에만 쓰고 저장하지 않는다.
"""

import re
from dataclasses import dataclass
from html import escape

import streamlit as st

from core.demo import ME_ID, USERS_BY_ID
from core.style import html, toast

# 규칙 ---------------------------------------------------------------------------

METHODS = {  # 로그인 방법 → 화면 이름
    "kakao": "카카오",
    "apple": "Apple",
    "naver": "네이버",
    "google": "Google",
    "phone": "휴대폰 번호",
}


@dataclass(frozen=True)
class Term:
    key: str
    label: str
    required: bool


# 약관 목록 (초안 — PRD Q20). 위치 기반 서비스는 걷기·달리기 거리 측정에 쓴다 (경로는 서버에 저장하지 않음)
TERMS: tuple[Term, ...] = (
    Term("service", "서비스 이용약관", True),
    Term("privacy", "개인정보 수집·이용", True),
    Term("location", "위치 기반 서비스 이용약관", True),
    Term("age", "만 14세 이상이에요", True),
    Term("marketing", "이벤트·혜택 알림 받기", False),
)

USER_ID_RULE = re.compile(r"^[a-z0-9_]{4,15}$")
PROTO_CODE_LEN = 6


def required_agreed(agreed: set[str]) -> bool:
    return all(t.key in agreed for t in TERMS if t.required)


def check_user_id(user_id: str) -> str:
    """ok / empty / format / taken. 영문 소문자·숫자·밑줄 4~15자, 다른 유저와 겹치지 않아야 한다."""
    uid = (user_id or "").strip().lstrip("@").lower()
    if not uid:
        return "empty"
    if not USER_ID_RULE.match(uid):
        return "format"
    if uid in USERS_BY_ID:
        return "taken"
    return "ok"


def normalize_phone(phone: str) -> str | None:
    """010으로 시작하는 11자리 휴대폰 번호면 숫자만 남겨 돌려준다. 아니면 None."""
    digits = re.sub(r"\D", "", phone or "")
    return digits if re.fullmatch(r"010\d{8}", digits) else None


def check_code(code: str) -> bool:
    """프로토타입: 아무 숫자 6자리면 통과한다 (실제 문자 인증 없음)."""
    return bool(re.fullmatch(rf"\d{{{PROTO_CODE_LEN}}}", (code or "").strip()))


def my_id() -> str:
    """화면에 보여 줄 내 아이디. 가입 전(테스트 등)에는 데모 아이디."""
    return st.session_state.get("account", {}).get("user_id", ME_ID)


def should_show() -> bool:
    ss = st.session_state
    return "account" not in ss and "profile" not in ss


ID_MESSAGES = {
    "empty": "아이디를 입력해 주세요.",
    "format": "영문 소문자·숫자·밑줄(_)로 4~15자를 써 주세요.",
    "taken": "이미 쓰고 있는 아이디예요. 다른 아이디를 골라 주세요.",
}


# 상태 · 콜백 -------------------------------------------------------------------


def _init() -> None:
    ss = st.session_state
    ss.setdefault("auth_step", "login")
    ss.setdefault("auth_method", None)
    ss.setdefault("auth_agreed", set())
    ss.setdefault("auth_code_sent", False)
    ss.setdefault("auth_error", None)


STEP_ORDER = ("login", "phone", "terms", "id")


def _go(step: str) -> None:
    ss = st.session_state
    # 단계 전환 방향: 앞으로 가면 오른쪽에서, 이전으로 가면 왼쪽에서 머리말이 들어온다
    ss.auth_dir = "fwd" if STEP_ORDER.index(step) > STEP_ORDER.index(ss.auth_step) else "back"
    ss.auth_step = step
    ss.auth_error = None


def _social(method: str) -> None:
    # 프로토타입: 계정 연동에 성공한 것으로 보고 바로 가입(약관 동의)으로 넘어간다
    st.session_state.auth_method = method
    _go("terms")


def _phone_back() -> None:
    st.session_state.auth_code_sent = False
    _go("login")


def _fail(kind: str) -> None:
    """입력 오류: 문구를 띄우고, 매번 칸이 살짝 흔들리도록 횟수를 센다 (같은 오류를 또 내도 다시 흔들림)."""
    ss = st.session_state
    ss.auth_error = kind
    ss.auth_err_n = ss.get("auth_err_n", 0) + 1


def _send_code() -> None:
    ss = st.session_state
    if normalize_phone(ss.get("auth_in_phone", "")) is None:
        _fail("phone")
        return
    ss.auth_error = None
    ss.auth_code_sent = True
    toast("인증번호를 보냈어요")


def _verify_code() -> None:
    ss = st.session_state
    if normalize_phone(ss.get("auth_in_phone", "")) is None:
        _fail("phone")
        return
    if not check_code(ss.get("auth_in_code", "")):
        _fail("code")
        return
    ss.auth_method = "phone"
    ss.auth_code_sent = False
    _go("terms")


def _toggle_term(key: str) -> None:
    agreed = set(st.session_state.auth_agreed)
    agreed ^= {key}
    st.session_state.auth_agreed = agreed


def _toggle_all() -> None:
    ss = st.session_state
    every = {t.key for t in TERMS}
    turning_on = not ss.auth_agreed >= every
    ss.auth_agreed = every if turning_on else set()
    ss.auth_cascade = turning_on  # 켤 때만 위에서 아래로 차례로 체크된다 (한 번만)


def _sign_up() -> None:
    ss = st.session_state
    result = check_user_id(ss.get("auth_in_id", ""))
    if result != "ok":
        _fail(result)
        return
    user_id = ss.auth_in_id.strip().lstrip("@").lower()
    ss.account = {
        "user_id": user_id,
        "method": ss.auth_method,
        "marketing": "marketing" in ss.auth_agreed,
    }
    for key in [k for k in ss.keys() if str(k).startswith("auth_")]:
        del ss[key]
    ss.ob_dir = "fwd"  # 온보딩 첫 단계가 가입 흐름에 이어 오른쪽에서 들어온다
    toast(f"@{user_id}님, 반가워요! 먹고 싶은 걸 골라 볼까요?")


# 화면 조각 ---------------------------------------------------------------------


def _nav(step_no: int, total: int, on_back, back_args=()) -> None:
    """[이전] [진행 막대] [n/total] — 온보딩 상단 줄과 같은 모양·자리 (연속성)."""
    direction = st.session_state.get("auth_dir")
    bars = "".join(
        f'<span class="{"on" if i <= step_no else ""}{" now" if i == step_no and direction == "fwd" else ""}"></span>'
        for i in range(total)
    )
    with st.container(key="nav_row", horizontal=True, vertical_alignment="center"):
        st.button("이전", key=f"auth_back_{st.session_state.auth_step}", type="tertiary", on_click=on_back, args=back_args)
        html(f'<div class="mk-progress" aria-hidden="true">{bars}</div>')
        html(f'<div class="mk-step" aria-label="{total}단계 중 {step_no + 1}단계">{step_no + 1}/{total}</div>')


def _field_error(field_key: str, message: str) -> None:
    """오류 난 칸: 빨간 테두리 + 좌우로 살짝 흔들림(실패할 때마다 다시) + 칸 바로 아래 문구."""
    n = st.session_state.get("auth_err_n", 0)
    html(
        f"<style>.st-key-{field_key} [data-testid='stTextInputRootElement']"
        f"{{ border-color: var(--danger) !important; animation: mk-shake-{n % 2} .32s var(--ease-move); }}</style>"
        f'<div class="mk-error mk-error-in" role="alert">{message}</div>'
    )


def _header(title: str, sub: str) -> None:
    direction = st.session_state.get("auth_dir")
    html(
        f'<div class="mk-header{" mk-" + direction if direction else ""}">'
        f'<div class="mk-title" role="heading" aria-level="1">{title}</div>'
        f'<div class="mk-sub">{sub}</div>'
        "</div>"
    )


def _login() -> None:
    direction = st.session_state.get("auth_dir")
    # 스플래시 바로 다음(처음 볼 때)은 투명도만 서서히, 다른 단계에서 돌아올 때는 왼쪽에서 밀려온다
    enter = " mk-back" if direction == "back" else (" mk-login-first" if direction is None else "")
    html(
        f'<div class="mk-login-hero{enter}">'
        '<div class="mk-wordmark mk-login-logo" role="heading" aria-level="1">MUKBOGI</div>'
        '<div class="mk-login-copy">먹고 싶은 걸 골라 두고,<br>걸어서 소화해요</div>'
        "</div>"
    )
    with st.container(key="auth_btns"):
        st.button("카카오로 계속하기", key="auth_kakao", width="stretch", on_click=_social, args=("kakao",))
        st.button("네이버로 계속하기", key="auth_naver", width="stretch", on_click=_social, args=("naver",))
        st.button("휴대폰 번호로 계속하기", key="auth_phone", width="stretch", on_click=_go, args=("phone",))
        html('<div class="mk-or" role="separator"><span>또는</span></div>')
        with st.container(key="auth_more", horizontal=True):
            st.button("Google로 계속하기", key="auth_google", on_click=_social, args=("google",))
            st.button("Apple로 계속하기", key="auth_apple", on_click=_social, args=("apple",))
    html('<div class="mk-login-note">프로토타입이라 실제 계정과 연결되지 않아요.</div>')


def _phone() -> None:
    ss = st.session_state
    _nav(0, 3, _phone_back)
    _header("휴대폰 번호를<br>알려 주세요", "가입 확인에만 쓰고, 다른 사람에게는 보이지 않아요.")
    st.text_input(
        "휴대폰 번호", key="auth_in_phone", placeholder="010-0000-0000", max_chars=13,
        label_visibility="collapsed",
    )
    if ss.auth_error == "phone":
        _field_error("auth_in_phone", "010으로 시작하는 11자리 번호를 입력해 주세요.")
    if ss.auth_code_sent:
        st.text_input(
            "인증번호", key="auth_in_code", placeholder="인증번호 6자리", max_chars=PROTO_CODE_LEN,
            label_visibility="collapsed",
        )
        if ss.auth_error == "code":
            _field_error("auth_in_code", "인증번호 6자리를 입력해 주세요.")
        html('<div class="mk-note">프로토타입: 아무 숫자 6자리나 입력하면 돼요.</div>')
    with st.container(key="bar_footer"):
        if ss.auth_code_sent:
            st.button("인증번호 다시 받기", key="auth_resend", type="tertiary", width="stretch", on_click=_send_code)
            st.button("확인", key="auth_verify", type="primary", width="stretch", on_click=_verify_code)
        else:
            st.button("인증번호 받기", key="auth_send", type="primary", width="stretch", on_click=_send_code)


def _terms() -> None:
    ss = st.session_state
    from_phone = ss.auth_method == "phone"
    total, at = (3, 1) if from_phone else (2, 0)
    _nav(at, total, _go, ("phone" if from_phone else "login",))
    checked = "휴대폰 번호를" if from_phone else f"{METHODS.get(ss.auth_method or '', '')} 계정을"
    _header("MUKBOGI를 쓰려면<br>동의가 필요해요", f"{escape(checked)} 확인했어요. 이제 거의 다 왔어요.")
    agreed = ss.auth_agreed
    every = {t.key for t in TERMS}
    all_on = agreed >= every
    cascade = ss.pop("auth_cascade", False)
    with st.container(key="tap_terms_all"):
        html(
            f'<div class="mk-card mk-term-all{" sel" if all_on else ""}">'
            '<div class="mk-pick" aria-hidden="true"></div>'
            '<div><div class="mk-term-all-title">전체 동의</div>'
            '<div class="mk-term-all-sub">선택 항목(이벤트·혜택 알림)도 함께 동의해요</div></div>'
            "</div>"
        )
        st.button("전체 동의 " + ("해제" if all_on else "하기"), key="auth_all", on_click=_toggle_all)
    with st.container(key="list_terms"):
        for i, t in enumerate(TERMS):
            on = t.key in agreed
            with st.container(key=f"tap_term_{t.key}"):
                html(
                    f'<div class="mk-card mk-term{" sel" if on else ""}{" mk-cascade" if cascade else ""}" style="--i:{i + 1}">'
                    '<div class="mk-pick" aria-hidden="true"></div>'
                    f'<span class="mk-term-tag{" req" if t.required else ""}">{"필수" if t.required else "선택"}</span>'
                    f'<span class="mk-term-label">{escape(t.label)}</span>'
                    "</div>"
                )
                st.button(f"{t.label} {'동의 해제' if on else '동의'}", key=f"auth_term_{t.key}", on_click=_toggle_term, args=(t.key,))
    html('<div class="mk-note">약관 전문은 정식 앱에서 볼 수 있어요. (프로토타입)</div>')
    ok = required_agreed(agreed)
    with st.container(key="bar_footer"):
        if not ok:
            html('<div class="mk-hint">필수 항목에 모두 동의해 주세요</div>')
        st.button("동의하고 계속하기", key="auth_terms_next", type="primary", width="stretch", disabled=not ok, on_click=_go, args=("id",))


def _user_id() -> None:
    ss = st.session_state
    from_phone = ss.auth_method == "phone"
    total, at = (3, 2) if from_phone else (2, 1)
    _nav(at, total, _go, ("terms",))
    _header("친구가 찾을<br>아이디를 정해요", "친구는 이 아이디로 나를 찾아 친구 요청을 보내요.")
    st.text_input(
        "아이디", key="auth_in_id", placeholder="예: mukbo_lover", max_chars=15, label_visibility="collapsed",
    )
    err = ss.auth_error
    if err in ID_MESSAGES:
        _field_error("auth_in_id", ID_MESSAGES[err])
    else:
        html('<div class="mk-note">영문 소문자·숫자·밑줄(_) 4~15자</div>')
    with st.container(key="bar_footer"):
        st.button("가입하고 시작하기", key="auth_signup", type="primary", width="stretch", on_click=_sign_up)


# 진입 -------------------------------------------------------------------------


def render() -> None:
    _init()
    {"login": _login, "phone": _phone, "terms": _terms, "id": _user_id}[st.session_state.auth_step]()
