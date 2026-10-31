"""냉장고 화면. PRD.md Epic 4 (Story 4.1 날짜·시간별 기록, 4.2 하루 목표 달성 표시)를 구현한다.

- 소화를 끝낸 음식(core.meal.FridgeEntry)을 날짜별로 묶어 최신 날짜부터 보여 준다.
- 날짜 묶음마다 그날 소화한 총 칼로리를 보여 주고, 하루 목표 이상이면 "목표 달성"을 붙인다.
- 한 날짜 안에서는 최근에 소화한 음식이 위로 온다.
- 기록이 있으면 하단 탭 위에 "더 주문하러 가기" 버튼을 고정한다 (빈 상태에는 가운데 "주문하기" 버튼이 있다).
"""

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import date, timedelta
from html import escape

import streamlit as st

from core.data import FOODS_BY_ID
from core.images import food_thumb
from core.meal import FridgeEntry
from core.style import html

WEEKDAYS = "월화수목금토일"


@dataclass(frozen=True)
class DayGroup:
    day: date
    label: str
    total_kcal: int
    goal_met: bool
    entries: list[FridgeEntry]


def day_label(day: date, today: date) -> str:
    """오늘 · 10월 31일 (토) / 어제 · 10월 30일 (금) / 10월 29일 (목)"""
    base = f"{day.month}월 {day.day}일 ({WEEKDAYS[day.weekday()]})"
    if day == today:
        return f"오늘 · {base}"
    if day == today - timedelta(days=1):
        return f"어제 · {base}"
    if day.year != today.year:
        return f"{day.year}년 {base}"
    return base


def group_by_day(entries: Sequence[FridgeEntry], today: date, daily_target_kcal: int) -> list[DayGroup]:
    by_day: dict[date, list[FridgeEntry]] = {}
    for e in entries:
        by_day.setdefault(e.completed_at.date(), []).append(e)
    groups = []
    for day in sorted(by_day, reverse=True):
        items = sorted(by_day[day], key=lambda e: e.completed_at, reverse=True)
        total = sum(e.kcal for e in items)
        groups.append(DayGroup(day, day_label(day, today), total, total >= daily_target_kcal, items))
    return groups


def _row(entry: FridgeEntry, show_distance: bool = True) -> str:
    """show_distance=False: 다른 유저의 냉장고에서는 거리를 숨긴다 (개인정보)."""
    food = FOODS_BY_ID[entry.food_id]
    meta = f"{entry.completed_at:%H:%M}" + (f" · {entry.distance_km:.2f}km" if show_distance else "")
    if entry.sender:
        meta += f" · {escape(entry.sender)}의 배달"
    return (
        '<div class="mk-fz-row" role="listitem">'
        f'<img src="{food_thumb(food)}" alt="">'
        '<div class="mk-fz-text">'
        f'<div class="mk-fz-name">{escape(food.name)}</div>'
        f'<div class="mk-fz-meta">{meta}</div>'
        "</div>"
        f'<div class="mk-fz-kcal">{entry.kcal}kcal</div>'
        "</div>"
    )


def render_days(
    entries: Sequence[FridgeEntry], today: date, daily_target_kcal: int | None, show_distance: bool = True
) -> None:
    """날짜별 묶음 목록. daily_target_kcal이 None이면(다른 유저) 목표 달성 표시를 하지 않는다."""
    target = daily_target_kcal if daily_target_kcal is not None else 10**9
    for idx, g in enumerate(group_by_day(entries, today, target)):
        badge = '<span class="mk-fz-goal">목표 달성</span>' if g.goal_met else ""
        rows = "".join(_row(e, show_distance) for e in g.entries)
        html(
            f'<section class="mk-fz-day{" first" if idx == 0 else ""}" aria-label="{escape(g.label)}, {g.total_kcal}킬로칼로리">'
            '<div class="mk-fz-head">'
            f'<div class="mk-fz-date" role="heading" aria-level="2">{escape(g.label)}</div>'
            f'<div class="mk-fz-total">{badge}<span class="mk-fz-sum"><b>{g.total_kcal}</b>kcal</span></div>'
            "</div>"
            f'<div class="mk-fz-list" role="list">{rows}</div>'
            "</section>"
        )


def render(entries: Sequence[FridgeEntry], today: date, daily_target_kcal: int, go: Callable[[str], None]) -> None:
    html('<div class="mk-topbar"><span class="mk-wordmark">MUKBOGI</span></div>')

    if not entries:
        html(
            '<div class="mk-header">'
            '<div class="mk-title" role="heading" aria-level="1">냉장고</div>'
            '<div class="mk-sub">다 소화한 음식이 날짜별로 여기에 모여요.</div>'
            "</div>"
        )
        with st.container(key="empty_box"):
            html(
                '<div class="mk-empty-title" role="heading" aria-level="2">아직 냉장고가 비어 있어요</div>'
                '<div class="mk-sub">먹고 싶은 음식을 주문하고 움직여서 소화하면 여기에 넣어 둘게요.</div>'
            )
            st.button("주문하기", key="fridge_order", type="primary", width="stretch", on_click=go, args=("order",))
        return

    total_kcal = sum(e.kcal for e in entries)
    html(
        '<div class="mk-header">'
        '<div class="mk-title" role="heading" aria-level="1">냉장고</div>'
        f'<div class="mk-sub">지금까지 {len(entries)}개, 모두 {total_kcal}kcal를 소화했어요.</div>'
        "</div>"
    )

    render_days(entries, today, daily_target_kcal)

    # 하단 고정: 냉장고를 보다가 바로 다음 음식을 주문하러 간다
    with st.container(key="bar_footer"):
        st.button("더 주문하러 가기", key="fridge_more", type="primary", width="stretch", on_click=go, args=("order",))
