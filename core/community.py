"""커뮤니티 화면. PRD.md Epic 5를 구현한다.

탭 3개 (iOS 세그먼트 컨트롤)
- 친구 (Story 5.1): 내 아이디, 아이디로 친구 찾기, 친구 요청 수락·거절, 보낸 요청 취소, 친구 목록(냉장고 보기 · 배달 보내기)
- 랭킹 (Story 5.2): 이번 주 소화 완료 칼로리 순위, 전체 / 친구 범위, 하단에 내 순위 고정
- 배달 (Story 5.4 관리): 이번 주 보낸·받은 배달 요약, 받은 배달(상태 + 답례 보내기), 보낸 배달(또 보내기)
다른 유저 화면 (Story 5.3): 프로필 · 관계에 맞는 버튼 · 공개 범위에 따른 냉장고 · 친구 삭제(확인 후)
"""

from datetime import datetime, timedelta
from html import escape

import streamlit as st

from core import auth, fridge, gift, meal, social
from core.avatar import user_avatar
from core.data import FOODS_BY_ID
from core.demo import ME_ID, USERS_BY_ID, User
from core.images import food_thumb
from core.korean import eul_reul, i_ga, wa_gwa
from core.style import html, toast

TABS = (("friends", "친구"), ("rank", "랭킹"), ("gift", "배달"))
RANK_SCOPES = (("all", "전체"), ("friends", "친구"))


# 상태 · 콜백 ------------------------------------------------------------------


def _ss():
    return st.session_state


def _soc() -> social.SocialState:
    return st.session_state.social


def _init() -> None:
    ss = _ss()
    ss.setdefault("social", social.SocialState())
    ss.setdefault("comm_tab", "friends")
    ss.setdefault("rank_scope", "all")
    ss.setdefault("cm_result", None)  # 마지막으로 찾은 아이디
    ss.setdefault("view_user", None)
    ss.setdefault("user_from", "community")
    ss.setdefault("confirm_remove", None)
    gift.init_state()


def _set_tab(tab: str) -> None:
    _ss().comm_tab = tab


def _set_scope(scope: str) -> None:
    _ss().rank_scope = scope


def _search() -> None:
    _ss().cm_result = (_ss().get("cm_query") or "").strip()


def _request(uid: str) -> None:
    result = social.send_request(_soc(), uid)
    name = USERS_BY_ID[uid].name if uid in USERS_BY_ID else uid
    toast({
        "ok": f"{name}에게 친구 요청을 보냈어요",
        "friend": f"이미 {wa_gwa(name)} 친구예요",
        "sent": f"{name}에게 이미 요청을 보냈어요",
        "received": f"{i_ga(name)} 먼저 요청했어요. 친구 요청에서 수락해 주세요",
    }.get(result, "요청을 보내지 못했어요"))


def _cancel(uid: str) -> None:
    social.cancel_request(_soc(), uid)
    toast("친구 요청을 취소했어요")


def _accept(uid: str) -> None:
    social.accept(_soc(), uid)
    toast(f"{wa_gwa(USERS_BY_ID[uid].name)} 친구가 됐어요")


def _decline(uid: str) -> None:
    social.decline(_soc(), uid)
    toast("요청을 거절했어요")  # 상대에게는 알리지 않는다


def _answer_in_list(uid: str, accepted: bool) -> None:
    """친구 요청 목록에서 수락·거절: 결과를 그 줄 안에서 보여 주고 옆으로 밀어낸다(토스트 없이).
    다음 한 번의 그리기에서만 쓰는 표시라 app.py 끝에서 지운다."""
    soc = _soc()
    index = soc.received.index(uid) if uid in soc.received else 0
    if accepted:
        social.accept(soc, uid)
    else:
        social.decline(soc, uid)  # 상대에게는 알리지 않는다
    st.session_state.just_answered = {"uid": uid, "accepted": accepted, "index": index}


def _ask_remove(uid: str | None) -> None:
    _ss().confirm_remove = uid


def _remove(uid: str) -> None:
    social.remove_friend(_soc(), uid)
    _ss().confirm_remove = None
    toast(f"{eul_reul(USERS_BY_ID[uid].name)} 친구에서 삭제했어요")


def _open_user(uid: str) -> None:
    ss = _ss()
    if uid == ME_ID:  # 내 냉장고는 냉장고 탭에서 본다
        ss.screen = "fridge"
        return
    ss.view_user = uid
    ss.user_from = ss.screen
    ss.confirm_remove = None
    ss.screen = "user"


def _back_from_user() -> None:
    ss = _ss()
    ss.screen = ss.get("user_from", "community")
    ss.confirm_remove = None


# 공통 조각 -------------------------------------------------------------------


def _me_avatar(cls: str = "mk-avatar") -> str:
    return auth.my_avatar(cls)


def _user_info(user: User, sub: str, extra: str = "", avatar_cls: str = "mk-avatar mk-avatar-md",
               sub_html: str | None = None) -> str:
    """sub_html이 있으면 상태 줄을 그 조각으로 그린다 (예: 소화 중 + 진행률). 둘 다 비면 이름 줄만 그린다."""
    if sub_html is not None:
        sub_part = sub_html
    else:
        sub_part = f'<div class="mk-u-sub">{escape(sub)}</div>' if sub else ""
    return (
        '<div class="mk-u">'
        f"{user_avatar(user, avatar_cls)}"
        '<div class="mk-u-text">'
        f'<div class="mk-u-name">{escape(user.name)}<span class="mk-u-id">@{escape(user.id)}</span>{extra}</div>'
        f"{sub_part}"
        "</div></div>"
    )


def _user_row(key: str, user: User, sub: str, actions, extra: str = "", openable: bool = True,
              sub_html: str | None = None) -> None:
    """한 줄: [아바타 · 이름 · 상태(누르면 그 유저 화면)] [버튼들]"""
    info = _user_info(user, sub, extra, sub_html=sub_html)
    with st.container(key=f"urow_{key}", horizontal=True, vertical_alignment="center"):
        if openable:
            with st.container(key=f"tap_u_{key}"):
                html(info)
                st.button(f"{user.name} 프로필 보기", key=f"open_{key}", on_click=_open_user, args=(user.id,))
        else:
            html(info)
        for label, bkey, btype, cb, args in actions:
            st.button(label, key=bkey, type=btype, on_click=cb, args=args)


def _segment(container_key: str, items, active: str, on_click, prefix: str, counts: dict | None = None) -> None:
    counts = counts or {}
    styles = [f".st-key-{prefix}_{active} button {{ background: #FFFFFF !important; color: var(--ink) !important; "
              "box-shadow: 0 1px 3px rgba(30, 37, 48, .14); }"]
    for key, n in counts.items():
        if n:
            styles.append(f'.st-key-{prefix}_{key} button::after {{ content: "{n}"; }}')
    html(f"<style>{' '.join(styles)}</style>")
    with st.container(key=container_key, horizontal=True):
        for key, label in items:
            st.button(label, key=f"{prefix}_{key}", type="tertiary", on_click=on_click, args=(key,))


def _section(title: str, count: int | None = None) -> None:
    num = f'<span class="mk-section-n">{count}</span>' if count is not None else ""
    html(f'<div class="mk-section" role="heading" aria-level="2">{title}{num}</div>')


def _when(at: datetime) -> str:
    today = datetime.now().date()
    if at.date() == today:
        return f"오늘 {at:%H:%M}"
    if at.date() == today - timedelta(days=1):
        return f"어제 {at:%H:%M}"
    return f"{at.month}월 {at.day}일 {at:%H:%M}"


# 친구 탭 ---------------------------------------------------------------------


def _friends_tab() -> None:
    soc = _soc()
    html(
        '<div class="mk-idcard">'
        '<div><div class="mk-idcard-label">내 아이디</div>'
        f'<div class="mk-idcard-id">@{escape(auth.my_id())}</div></div>'
        '<div class="mk-idcard-hint">친구에게 알려 주면<br>나를 찾을 수 있어요</div>'
        "</div>"
    )

    _section("아이디로 친구 찾기")
    with st.container(key="cm_search_row", horizontal=True, vertical_alignment="bottom"):
        st.text_input(
            "친구 아이디", key="cm_query", placeholder="아이디를 정확히 입력해 주세요",
            label_visibility="collapsed", on_change=_search,
        )
        st.button("찾기", key="cm_search", type="primary", on_click=_search)
    _search_result()

    answered = st.session_state.get("just_answered")
    if soc.received or answered:
        last = answered is not None and not soc.received  # 마지막 요청이면 섹션째 접힌다
        if last:
            html('<div class="mk-section mk-ghost-headline" role="heading" aria-level="2">친구 요청</div>')
        else:
            _section("친구 요청", len(soc.received))
        with st.container(key="list_received"):
            rows = list(soc.received)
            if answered:
                rows.insert(min(answered["index"], len(rows)), None)  # 방금 답한 줄은 원래 자리에
            for uid in rows:
                if uid is None:
                    _answered_row(answered, last)
                    continue
                u = USERS_BY_ID[uid]
                _user_row(f"rq_{uid}", u, "", [
                    ("수락", f"acc_{uid}", "primary", _answer_in_list, (uid, True)),
                    ("거절", f"dec_{uid}", "secondary", _answer_in_list, (uid, False)),
                ])

    if soc.sent:
        _section("보낸 요청", len(soc.sent))
        with st.container(key="list_sent"):
            for uid in soc.sent:
                u = USERS_BY_ID[uid]
                _user_row(f"sq_{uid}", u, "수락을 기다리고 있어요", [
                    ("요청 취소", f"cnl_{uid}", "secondary", _cancel, (uid,)),
                ])

    friends = social.friend_users(soc)
    if answered and answered["accepted"]:
        # 방금 수락한 친구는 요청 줄이 빠져나간 뒤 친구 목록에 옆에서 들어온다
        html(f"<style>.st-key-urow_fr_{answered['uid']} {{ animation: mk-friend-in .34s var(--ease-move) .62s both; }}</style>")
    _section("친구", len(friends))
    if not friends:
        html('<div class="mk-empty-line">아직 친구가 없어요. 아이디로 친구를 찾아 보세요.</div>')
        return
    # 보낸 배달 수는 배달하기 버튼 오른쪽 위 동그란 숫자로 (버튼 글자는 그대로, 숫자는 CSS로 붙인다)
    styles = []
    for u in friends:
        n = gift.sent_count(u.id)
        if n:
            bump = " animation: mk-bump .3s var(--ease-pop);" if st.session_state.get("just_gifted") == u.id else ""
            styles.append(f'.st-key-gift_to_{u.id} button::after {{ content: "{n}";{bump} }}')
    if styles:
        html(f"<style>{' '.join(styles)}</style>")
    with st.container(key="list_friends"):
        for u in friends:
            n = gift.sent_count(u.id)
            sr = f'<span class="mk-sr">배달 {n}번 보냄</span>' if n else ""
            _user_row(f"fr_{u.id}", u, "", sub_html=gift.doing_html(u), actions=[
                ("배달하기", f"gift_to_{u.id}", "secondary", gift.open_for, (u.id, "community")),
            ], extra=sr)


def _answered_row(answered: dict, last: bool) -> None:
    """방금 수락·거절한 요청 줄 (버튼 없는 그림). 수락은 "친구가 됐어요"를 잠깐 보여 준 뒤 오른쪽으로,
    거절은 바로 왼쪽으로 밀려 나가고 줄 높이가 접힌다. 다음 그리기에서는 사라진다."""
    user = USERS_BY_ID[answered["uid"]]
    if answered["accepted"]:
        pill = '<span class="mk-ghost-pill ok"><i aria-hidden="true"></i>친구가 됐어요</span>'
        live = f"{wa_gwa(user.name)} 친구가 됐어요"
    else:
        pill = '<span class="mk-ghost-pill">거절했어요</span>'
        live = f"{user.name}의 요청을 거절했어요"
    kind = "acc" if answered["accepted"] else "dec"
    html(
        f'<div class="mk-ghost mk-ghost-{kind}{" last" if last else ""}">'
        f'<div class="mk-ghost-row">{_user_info(user, "")}{pill}</div>'
        f'<span class="mk-sr" role="status">{escape(live)}</span>'
        "</div>"
    )


def _search_result() -> None:
    q = _ss().cm_result
    if not q:
        return
    found = social.find_user(q, auth.my_id())
    if found is None:
        html(f'<div class="mk-note-box">‘{escape(q)}’ 아이디를 찾지 못했어요. 정확히 입력했는지 확인해 주세요.</div>')
        return
    if found == ME_ID:
        html('<div class="mk-note-box">내 아이디예요.</div>')
        return
    rel = social.relation(_soc(), found.id)
    actions = {
        "none": [("친구 요청", f"req_{found.id}", "primary", _request, (found.id,))],
        "sent": [("요청 취소", f"scnl_{found.id}", "secondary", _cancel, (found.id,))],
        "received": [("수락", f"sacc_{found.id}", "primary", _accept, (found.id,))],
        "friend": [],
    }[rel]
    sub = {"none": "아직 친구가 아니에요", "sent": "요청 중이에요", "received": "나에게 친구 요청을 보냈어요",
           "friend": "이미 친구예요"}[rel]
    with st.container(key="list_search"):
        _user_row(f"srch_{found.id}", found, sub, actions)


# 랭킹 탭 ---------------------------------------------------------------------


def _rank_tab(state: meal.MealState) -> None:
    now = datetime.now()
    scope = _ss().rank_scope
    _segment("seg_scope", RANK_SCOPES, scope, _set_scope, "rscope")
    start = social.week_start(now.date())
    html(
        f'<div class="mk-count">이번 주 {start.month}월 {start.day}일(월)부터 소화한 칼로리예요. '
        "매주 월요일 00:00에 새로 시작해요.</div>"
    )

    rows = social.ranking(_soc(), state.fridge, now, "전체" if scope == "all" else "친구", my_name=auth.my_name())
    with st.container(key="list_rank"):
        for r in rows:
            top = " top" if r.rank <= 3 else ""
            if r.is_me:
                info = (
                    f'<div class="mk-rk me"><span class="mk-rk-n{top}">{r.rank}</span>'
                    f'{_me_avatar("mk-avatar mk-avatar-md")}'
                    f'<div class="mk-rk-name">{escape(r.name)}<span class="mk-me-pill">나</span></div>'
                    f'<div class="mk-rk-kcal">{r.kcal:,}<small>kcal</small></div></div>'
                )
                label = "내 냉장고 보기"
            else:
                u = USERS_BY_ID[r.user_id]
                info = (
                    f'<div class="mk-rk"><span class="mk-rk-n{top}">{r.rank}</span>'
                    f'{user_avatar(u, "mk-avatar mk-avatar-md")}'
                    f'<div class="mk-rk-name">{escape(u.name)}</div>'
                    f'<div class="mk-rk-kcal">{r.kcal:,}<small>kcal</small></div></div>'
                )
                label = f"{u.name} 냉장고 보기"
            with st.container(key=f"tap_rk_{r.user_id}"):
                html(info)
                st.button(label, key=f"rk_{r.user_id}", on_click=_open_user, args=(r.user_id,))

    me = next(r for r in rows if r.is_me)
    with st.container(key="bar_footer"):
        html(
            '<div class="mk-myrank" role="status">'
            '<span class="mk-myrank-label">내 순위</span>'
            f'<span class="mk-myrank-n">{me.rank}위</span>'
            f'<span class="mk-myrank-of">/ {len(rows)}명</span>'
            f'<span class="mk-myrank-kcal">{me.kcal:,}kcal</span>'
            "</div>"
        )


# 배달 탭 ---------------------------------------------------------------------


def _gift_tab(state: meal.MealState) -> None:
    ss = _ss()
    log = ss.gift_log
    week = social.week_start(datetime.now().date())
    this_week = [g for g in log if g["at"].date() >= week]
    n_sent = sum(g["dir"] == "sent" for g in this_week)
    n_recv = sum(g["dir"] == "received" and not g["missed"] for g in this_week)
    html(
        '<dl class="mk-stats mk-gift-stats">'
        f'<div class="mk-stat"><dt>이번 주 보낸 배달</dt><dd>{n_sent}<small>개</small></dd></div>'
        f'<div class="mk-stat"><dt>이번 주 받은 배달</dt><dd>{n_recv}<small>개</small></dd></div>'
        "</dl>"
    )
    for g in ss.gift_replies:
        html(f'<div class="mk-note-box">{escape(USERS_BY_ID[g["user_id"]].name)}의 답례 배달이 오고 있어요…</div>')

    if not log:
        with st.container(key="empty_box"):
            html(
                '<div class="mk-empty-title" role="heading" aria-level="2">아직 주고받은 배달이 없어요</div>'
                '<div class="mk-sub">친구에게 먹을 음식을 보내 응원해 보세요.</div>'
            )
            st.button("친구 목록 보기", key="gift_empty_friends", type="primary", width="stretch",
                      on_click=_set_tab, args=("friends",))
        return

    received = [g for g in reversed(log) if g["dir"] == "received"]
    sent = [g for g in reversed(log) if g["dir"] == "sent"]

    _section("받은 배달", len(received))
    if not received:
        html('<div class="mk-empty-line">친구가 보낸 음식이 도착하면 여기에 보여요.</div>')
    else:
        with st.container(key="list_got"):
            for g in received:
                u = USERS_BY_ID[g["user_id"]]
                food = FOODS_BY_ID[g["food_id"]]
                status = gift.received_status(state, g)
                with st.container(key=f"urow_got_{g['id']}", horizontal=True, vertical_alignment="center"):
                    html(
                        '<div class="mk-u">'
                        f'<img class="mk-u-food" src="{food_thumb(food)}" alt="">'
                        '<div class="mk-u-text">'
                        f'<div class="mk-u-name">{escape(i_ga(u.name))} 보낸 {escape(food.name)}</div>'
                        f'<div class="mk-u-sub">{_when(g["at"])} · {escape(status)}</div>'
                        "</div></div>"
                    )
                    st.button("답례 보내기", key=f"thx_{g['id']}", type="secondary",
                              on_click=gift.open_for, args=(u.id, "community"))

    _section("보낸 배달", len(sent))
    if not sent:
        html('<div class="mk-empty-line">친구에게 보낸 음식이 여기에 보여요.</div>')
    else:
        with st.container(key="list_gave"):
            for g in sent:
                u = USERS_BY_ID[g["user_id"]]
                food = FOODS_BY_ID[g["food_id"]]
                with st.container(key=f"urow_gave_{g['id']}", horizontal=True, vertical_alignment="center"):
                    html(
                        '<div class="mk-u">'
                        f'<img class="mk-u-food" src="{food_thumb(food)}" alt="">'
                        '<div class="mk-u-text">'
                        f'<div class="mk-u-name">{escape(u.name)}에게 {escape(food.name)}</div>'
                        f'<div class="mk-u-sub">{_when(g["at"])} · 조리 중 목록에 넣었어요</div>'
                        "</div></div>"
                    )
                    st.button("또 보내기", key=f"again_{g['id']}", type="secondary",
                              on_click=gift.open_for, args=(u.id, "community"))


# 진입 -------------------------------------------------------------------------


def render(state: meal.MealState) -> None:
    _init()
    ss = _ss()
    html('<div class="mk-topbar"><span class="mk-wordmark">MUKBOGI</span></div>')
    html(
        '<div class="mk-header">'
        '<div class="mk-title" role="heading" aria-level="1">커뮤니티</div>'
        '<div class="mk-sub">친구와 함께 먹고, 움직이고, 음식을 주고받아요.</div>'
        "</div>"
    )
    _segment("seg_comm", TABS, ss.comm_tab, _set_tab, "ctab",
             counts={"friends": len(_soc().received)})
    {"friends": _friends_tab, "rank": lambda: _rank_tab(state), "gift": lambda: _gift_tab(state)}[ss.comm_tab]()


def render_user(state: meal.MealState) -> None:
    """다른 유저 화면: 프로필 · 관계 버튼 · 냉장고 (Story 5.3)."""
    _init()
    ss = _ss()
    user = USERS_BY_ID[ss.view_user]
    soc = _soc()
    rel = social.relation(soc, user.id)
    now = datetime.now()

    with st.container(key="nav_row", horizontal=True, vertical_alignment="center"):
        st.button("이전", key="user_back", type="tertiary", on_click=_back_from_user)
        html(f'<div class="mk-nav-title">{escape(user.name)}</div>')
        html('<div class="mk-nav-slot"></div>')

    rel_text = {"friend": "친구", "sent": "요청 중", "received": "나에게 요청함", "none": "친구 아님"}[rel]
    entries = social.user_fridge(user, now)
    week_kcal = social.weekly_kcal(entries, now.date())
    html(
        '<div class="mk-prof">'
        f"{user_avatar(user, 'mk-avatar mk-avatar-xl')}"
        '<div class="mk-u-text">'
        f'<div class="mk-prof-name">{escape(user.name)}<span class="mk-rel">{rel_text}</span></div>'
        f'<div class="mk-u-id">@{escape(user.id)}</div>'
        f"{gift.doing_html(user)}"
        f'<div class="mk-u-sub">이번 주 <b>{week_kcal:,}kcal</b> 소화</div>'
        "</div></div>"
    )

    with st.container(key="user_actions", horizontal=True):
        if rel == "friend":
            st.button("배달하기", key="u_gift", type="primary", on_click=gift.open_for, args=(user.id, "user"))
            st.button("친구 삭제", key="u_remove", type="secondary", on_click=_ask_remove, args=(user.id,))
        elif rel == "none":
            st.button("친구 요청", key="u_request", type="primary", on_click=_request, args=(user.id,))
        elif rel == "sent":
            st.button("요청 취소", key="u_cancel", type="secondary", on_click=_cancel, args=(user.id,))
        else:
            st.button("수락", key="u_accept", type="primary", on_click=_accept, args=(user.id,))
            st.button("거절", key="u_decline", type="secondary", on_click=_decline, args=(user.id,))

    if ss.confirm_remove == user.id:
        with st.container(key="confirm_box"):
            html(
                f'<div class="mk-confirm-title">{eul_reul(escape(user.name))} 친구에서 삭제할까요?</div>'
                '<div class="mk-confirm-sub">삭제해도 상대에게 알리지 않아요. 다시 친구가 되려면 요청을 보내야 해요.</div>'
            )
            with st.container(key="confirm_btns", horizontal=True):
                st.button("삭제", key="u_remove_ok", type="primary", on_click=_remove, args=(user.id,))
                st.button("취소", key="u_remove_no", type="secondary", on_click=_ask_remove, args=(None,))

    _section(f"{escape(user.name)}의 냉장고")
    if not social.can_view_fridge(soc, user):
        title, sub = (
            ("비공개 냉장고예요", f"{escape(i_ga(user.name))} 냉장고를 공개하지 않았어요.")
            if user.fridge_visibility == "비공개"
            else ("친구만 볼 수 있는 냉장고예요", "친구가 되면 볼 수 있어요.")
        )
        html(f'<div class="mk-lock"><div class="mk-lock-title">{title}</div><div class="mk-sub">{sub}</div></div>')
        return
    if not entries:
        html('<div class="mk-empty-line">아직 냉장고가 비어 있어요.</div>')
        return
    fridge.render_days(entries, now.date(), None, show_distance=False)
