"""한국어 조사 붙이기. 마지막 글자의 받침 유무로 고른다."""


def _has_batchim(word: str) -> bool | None:
    last = word[-1] if word else ""
    if "가" <= last <= "힣":
        return (ord(last) - ord("가")) % 28 != 0
    return None  # 한글이 아니면 알 수 없음


def eul_reul(word: str) -> str:
    """떡볶이를 / 마라탕을"""
    b = _has_batchim(word)
    return word + ("을(를)" if b is None else "을" if b else "를")


def i_ga(word: str) -> str:
    """하늘이 / 수아가 / 마라탕이 / 파스타가"""
    b = _has_batchim(word)
    return word + ("이(가)" if b is None else "이" if b else "가")


def wa_gwa(word: str) -> str:
    """도윤과 / 하늘과 / 수아와"""
    b = _has_batchim(word)
    return word + ("와(과)" if b is None else "과" if b else "와")
