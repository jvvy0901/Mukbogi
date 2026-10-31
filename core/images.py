"""화면용 작은 썸네일.

음식: 원본은 1,000px 이상이고, 투명 배경 대신 체크무늬가 그림으로 그려져 있다.
  1) 사진 가장자리에서 이어지는 체크무늬(채도 낮은 밝은 회색·흰색)를 흰색으로 채우고
  2) 가운데를 정사각형으로 잘라 작게 줄인 뒤
  3) data URI로 넘긴다.
프로필: 얼굴이 위쪽 가운데에 있으므로 그 부분을 정사각형으로 자른다.
원본 파일은 바꾸지 않는다.
"""

import base64
import io
from collections import deque
from pathlib import Path

import numpy as np
import streamlit as st
from PIL import Image

from core.data import Food

WORK_PX = 512  # 배경 처리용 축소 크기 (긴 변)
FOOD_CROP = 0.78  # 짧은 변 대비 가운데 영역 비율
PROFILE_CROP = 0.62
PROFILE_TOP = 0.06  # 위에서부터 자르기 시작하는 위치 (높이 비율)


def _whiten_checkerboard(im: Image.Image) -> Image.Image:
    a = np.asarray(im).astype(np.int16)
    h, w, _ = a.shape
    is_bg = (a.max(axis=2) - a.min(axis=2) < 14) & (a.min(axis=2) > 190)

    seen = np.zeros((h, w), dtype=bool)
    queue: deque[tuple[int, int]] = deque()
    edges = [(y, x) for x in range(w) for y in (0, h - 1)] + [
        (y, x) for y in range(h) for x in (0, w - 1)
    ]
    for y, x in edges:
        if is_bg[y, x] and not seen[y, x]:
            seen[y, x] = True
            queue.append((y, x))
    while queue:
        y, x = queue.popleft()
        for ny, nx in ((y + 1, x), (y - 1, x), (y, x + 1), (y, x - 1)):
            if 0 <= ny < h and 0 <= nx < w and is_bg[ny, nx] and not seen[ny, nx]:
                seen[ny, nx] = True
                queue.append((ny, nx))

    out = a.copy()
    out[seen] = 255
    return Image.fromarray(out.astype(np.uint8))


def _to_data_uri(im: Image.Image) -> str:
    buf = io.BytesIO()
    im.save(buf, format="JPEG", quality=85)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()


@st.cache_data(show_spinner=False)
def _food_uri(path: str, px: int) -> str:
    with Image.open(path) as src:
        im = src.convert("RGB")
    im.thumbnail((WORK_PX, WORK_PX), Image.LANCZOS)
    im = _whiten_checkerboard(im)
    w, h = im.size
    side = int(min(w, h) * FOOD_CROP)
    left, top = (w - side) // 2, (h - side) // 2
    im = im.crop((left, top, left + side, top + side)).resize((px, px), Image.LANCZOS)
    return _to_data_uri(im)


@st.cache_data(show_spinner=False)
def _profile_uri(path: str, px: int) -> str:
    with Image.open(path) as src:
        im = src.convert("RGB")
    w, h = im.size
    side = int(min(w, h) * PROFILE_CROP)
    left, top = (w - side) // 2, int(h * PROFILE_TOP)
    im = im.crop((left, top, left + side, top + side)).resize((px, px), Image.LANCZOS)
    return _to_data_uri(im)


def food_thumb(food: Food, px: int = 192) -> str:
    """px: 화면 크기(pt) × 2~3배."""
    return _food_uri(str(food.image_path), px)


def profile_thumb(path: Path, px: int = 128) -> str:
    return _profile_uri(str(path), px)
