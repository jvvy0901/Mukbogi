"""화면용 작은 썸네일.

원본 음식 사진은 1,000px 이상이고, 투명 배경 대신 체크무늬가 그림으로 그려져 있다.
그래서 화면에 넣기 전에
  1) 사진 가장자리에서 이어지는 체크무늬(채도 낮은 밝은 회색·흰색)를 흰색으로 채우고
  2) 가운데를 정사각형으로 잘라 작게 줄인 뒤
  3) data URI로 넘긴다. (원본 파일은 바꾸지 않는다)
"""

import base64
import io
from collections import deque

import numpy as np
import streamlit as st
from PIL import Image

from core.data import Food

THUMB_PX = 192  # 화면 최대 72pt × 레티나 2~3배
WORK_PX = 512  # 배경 처리용 축소 크기 (긴 변)
CENTER_CROP = 0.78  # 짧은 변 대비 가운데 영역 비율


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


@st.cache_data(show_spinner=False)
def _thumb_data_uri(path: str) -> str:
    with Image.open(path) as src:
        im = src.convert("RGB")
    im.thumbnail((WORK_PX, WORK_PX), Image.LANCZOS)
    im = _whiten_checkerboard(im)

    w, h = im.size
    side = int(min(w, h) * CENTER_CROP)
    left, top = (w - side) // 2, (h - side) // 2
    im = im.crop((left, top, left + side, top + side)).resize((THUMB_PX, THUMB_PX), Image.LANCZOS)

    buf = io.BytesIO()
    im.save(buf, format="JPEG", quality=85)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()


def food_thumb(food: Food) -> str:
    return _thumb_data_uri(str(food.image_path))
