"""화면용 이미지.

음식: 원본은 1,000px 이상이고, 투명 배경 대신 체크무늬가 그림으로 그려져 있다.
  1) 사진 가장자리에서 이어지는 체크무늬(채도 낮은 밝은 회색·흰색)를 찾아 투명하게 빼고 (누끼)
  2) 음식이 실제로 차지하는 영역만 잘라낸 뒤
  3) 모든 음식이 비슷한 크기로 보이도록 같은 정사각형 상자에 맞춰 넣는다.
     - 사람 눈은 면적으로 크기를 느끼므로 "보이는 면적"을 기준으로 맞추되,
     - 가늘거나 긴 음식(아이스크림·탕후루)이 상자를 넘지 않게 긴 변 기준으로 상한을 둔다.
  4) 투명 PNG data URI로 넘긴다. 원형 틀 없이 음식만 떠 보이게 쓸 수 있다.
프로필: 얼굴이 위쪽 가운데에 있으므로 그 부분을 정사각형으로 자른다.
원본 파일은 바꾸지 않는다.
"""

import base64
import io
from collections import deque
from pathlib import Path

import numpy as np
import streamlit as st
from PIL import Image, ImageFilter

from core.data import Food

WORK_PX = 640  # 배경 처리용 축소 크기 (긴 변)
FOOD_PAD = 0.06  # 상자 안 여백 비율 (한쪽)
FOOD_AREA_RATIO = 0.70  # 보이는 면적의 제곱근 ÷ 상자 안쪽 한 변 — 음식 크기를 고르게 맞추는 기준
PROFILE_CROP = 0.62
PROFILE_TOP = 0.06  # 위에서부터 자르기 시작하는 위치 (높이 비율)


def _background_mask(im: Image.Image) -> np.ndarray:
    """사진 가장자리에서 이어지는 체크무늬 배경 = True."""
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
    return seen


def _cutout(path: str) -> Image.Image:
    """배경을 투명하게 뺀 음식 영역만 돌려준다."""
    with Image.open(path) as src:
        im = src.convert("RGB")
    im.thumbnail((WORK_PX, WORK_PX), Image.LANCZOS)
    alpha = Image.fromarray(np.where(_background_mask(im), 0, 255).astype(np.uint8))
    # 가장자리 1px을 깎고 살짝 흐리게 해서 배경 테두리 얼룩 없이 부드럽게 오린다
    alpha = alpha.filter(ImageFilter.MinFilter(3)).filter(ImageFilter.GaussianBlur(0.8))
    rgba = im.convert("RGBA")
    rgba.putalpha(alpha)
    return rgba.crop(alpha.point(lambda v: 255 if v > 40 else 0).getbbox())


def _png_uri(im: Image.Image) -> str:
    buf = io.BytesIO()
    im.save(buf, format="PNG", optimize=True)
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


def _jpeg_uri(im: Image.Image) -> str:
    buf = io.BytesIO()
    im.save(buf, format="JPEG", quality=85)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()


@st.cache_data(show_spinner=False)
def _food_uri(path: str, px: int) -> str:
    obj = _cutout(path)
    inner = px * (1 - 2 * FOOD_PAD)
    visible = int((np.asarray(obj.getchannel("A")) > 127).sum())
    scale = min(FOOD_AREA_RATIO * inner / np.sqrt(visible), inner / max(obj.size))
    obj = obj.resize((max(1, round(obj.width * scale)), max(1, round(obj.height * scale))), Image.LANCZOS)
    canvas = Image.new("RGBA", (px, px), (0, 0, 0, 0))
    canvas.paste(obj, ((px - obj.width) // 2, (px - obj.height) // 2), obj)
    return _png_uri(canvas)


@st.cache_data(show_spinner=False)
def _profile_uri(path: str, px: int) -> str:
    with Image.open(path) as src:
        im = src.convert("RGB")
    w, h = im.size
    side = int(min(w, h) * PROFILE_CROP)
    left, top = (w - side) // 2, int(h * PROFILE_TOP)
    im = im.crop((left, top, left + side, top + side)).resize((px, px), Image.LANCZOS)
    return _jpeg_uri(im)


def food_thumb(food: Food, px: int = 192) -> str:
    """배경 없는 음식 이미지(투명 PNG, 정사각형). px: 화면 크기(pt) × 2~3배."""
    return _food_uri(str(food.image_path), px)


def profile_thumb(path: Path, px: int = 128) -> str:
    return _profile_uri(str(path), px)
