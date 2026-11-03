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

from core.data import FOODS, Food

WORK_PX = 640  # 배경 처리용 축소 크기 (긴 변)
FOOD_PAD = 0.06  # 상자 안 여백 비율 (한쪽)
FOOD_AREA_RATIO = 0.70  # 보이는 면적의 제곱근 ÷ 상자 안쪽 한 변 — 음식 크기를 고르게 맞추는 기준
BG_MAX_SPREAD = 5  # 배경(체크무늬)으로 볼 R·G·B 최대 차이 — 무채색만
PROFILE_CROP = 0.62
PROFILE_TOP = 0.06  # 위에서부터 자르기 시작하는 위치 (높이 비율)


def _background_mask(im: Image.Image) -> np.ndarray:
    """사진 가장자리에서 이어지는 체크무늬 배경 = True.

    체크무늬는 무채색(흰색 253~255, 회색 223/223/225)이라 R·G·B 차이가 거의 없다(≤ 2).
    차이를 14까지 배경으로 보면 후라이드치킨의 흰 종이 상자(따뜻한 흰색, 예: 232/221/218)가
    배경과 이어져 상자 일부가 투명하게 뚫렸다 → 차이 5 이하만 배경으로 본다."""
    a = np.asarray(im).astype(np.int16)
    h, w, _ = a.shape
    is_bg = (a.max(axis=2) - a.min(axis=2) <= BG_MAX_SPREAD) & (a.min(axis=2) > 190)

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


def _food_canvas(path: str, px: int) -> Image.Image:
    """음식을 같은 크기로 보이게 정사각형 투명 캔버스 가운데에 놓는다."""
    obj = _cutout(path)
    inner = px * (1 - 2 * FOOD_PAD)
    visible = int((np.asarray(obj.getchannel("A")) > 127).sum())
    scale = min(FOOD_AREA_RATIO * inner / np.sqrt(visible), inner / max(obj.size))
    obj = obj.resize((max(1, round(obj.width * scale)), max(1, round(obj.height * scale))), Image.LANCZOS)
    canvas = Image.new("RGBA", (px, px), (0, 0, 0, 0))
    canvas.paste(obj, ((px - obj.width) // 2, (px - obj.height) // 2), obj)
    return canvas


@st.cache_data(show_spinner=False)
def _food_uri(path: str, px: int) -> str:
    return _png_uri(_food_canvas(path, px))


# 한 입 자국 ---------------------------------------------------------------------
# 한 입마다 음식 가장자리를 "이빨 자국" 모양(큰 원 + 안쪽으로 볼록한 작은 원 5개)으로 베어 낸다.
# 한 입이 지우는 넓이 = 원래 음식 넓이 ÷ 입 수 (이분 탐색으로 자국 크기를 맞춘다).
# 자국 위치는 음식 중심에서 황금각(137.5°)씩 돌아가며 정해 골고루 베어 먹은 것처럼 보이게 한다.
BITE_START_DEG = -40.0  # 첫 입: 오른쪽 위
BITE_STEP_DEG = 137.5
BITE_TEETH = 5
BITE_TOOTH_RATIO = 0.22  # 이빨 자국 원 반지름 ÷ 한 입 반지름


def _bite_region(xx, yy, bx: float, by: float, r: float, cx: float, cy: float) -> np.ndarray:
    region = np.hypot(xx - bx, yy - by) <= r
    toward_center = np.arctan2(cy - by, cx - bx)
    for a in np.linspace(-0.95, 0.95, BITE_TEETH):
        tx = bx + r * np.cos(toward_center + a)
        ty = by + r * np.sin(toward_center + a)
        region |= np.hypot(xx - tx, yy - ty) <= r * BITE_TOOTH_RATIO
    return region


def _largest_piece(mask: np.ndarray, grid: int = 120) -> np.ndarray:
    """가장 큰 덩어리만 남긴다 (떨어져 나간 부스러기는 먹은 것으로 친다). 속도를 위해 축소해서 찾는다."""
    h, w = mask.shape
    small = np.asarray(Image.fromarray((mask * 255).astype(np.uint8)).resize((grid, grid), Image.NEAREST)) > 127
    labels = np.zeros((grid, grid), dtype=np.int32)
    best, best_size, n = 0, 0, 0
    for y0, x0 in zip(*np.nonzero(small)):
        if labels[y0, x0]:
            continue
        n += 1
        labels[y0, x0] = n
        queue, size = deque([(y0, x0)]), 0
        while queue:
            y, x = queue.popleft()
            size += 1
            for ny, nx in ((y + 1, x), (y - 1, x), (y, x + 1), (y, x - 1)):
                if 0 <= ny < grid and 0 <= nx < grid and small[ny, nx] and not labels[ny, nx]:
                    labels[ny, nx] = n
                    queue.append((ny, nx))
        if size > best_size:
            best, best_size = n, size
    keep_small = (labels == best).astype(np.uint8) * 255
    # 경계에서 잘리지 않도록 한 칸 넓혀서 원래 크기로 되돌린다
    keep = Image.fromarray(keep_small).filter(ImageFilter.MaxFilter(3)).resize((w, h), Image.NEAREST)
    return mask & (np.asarray(keep) > 127)


@st.cache_data(show_spinner=False)
def _bitten_uris(path: str, px: int, bites: int) -> tuple[list[str], list[tuple[float, float] | None]]:
    """0입 ~ (입 수 - 1)입 먹은 모습. 마지막 입을 먹으면 음식이 다 사라지므로 그림이 필요 없다.

    돌려주는 값: (각 단계 이미지 data URI 목록, 각 단계에서 방금 베어 문 자리(0~1 비율) 목록)
    """
    canvas = _food_canvas(path, px)
    alpha = np.asarray(canvas.getchannel("A")).astype(np.float32)
    solid = alpha > 127
    total = int(solid.sum())
    yy, xx = np.mgrid[0:px, 0:px]
    cy, cx = float(yy[solid].mean()), float(xx[solid].mean())

    uris, centers = [_png_uri(canvas)], [None]
    removed = np.zeros((px, px), dtype=bool)
    for k in range(1, bites):
        remaining = solid & ~removed
        theta = np.radians(BITE_START_DEG + BITE_STEP_DEG * (k - 1))
        ts = np.arange(px * 2) * 0.5
        rx = np.clip((cx + np.cos(theta) * ts).astype(int), 0, px - 1)
        ry = np.clip((cy + np.sin(theta) * ts).astype(int), 0, px - 1)
        hits = np.nonzero(remaining[ry, rx])[0]
        if hits.size:
            bx, by = float(rx[hits[-1]]), float(ry[hits[-1]])
        else:  # 그 방향에 남은 음식이 없으면, 남은 부분 중 중심에서 가장 먼 곳을 문다
            ys, xs = np.nonzero(remaining)
            i = int(np.argmax(np.hypot(xs - cx, ys - cy)))
            bx, by = float(xs[i]), float(ys[i])

        target = total * k / bites
        lo, hi = 1.0, float(px)
        for _ in range(18):
            mid = (lo + hi) / 2
            if ((removed | _bite_region(xx, yy, bx, by, mid, cx, cy)) & solid).sum() >= target:
                hi = mid
            else:
                lo = mid
        removed |= _bite_region(xx, yy, bx, by, hi, cx, cy)
        removed |= solid & ~_largest_piece(solid & ~removed)

        soft = Image.fromarray((removed * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.9))
        keep = 1.0 - np.asarray(soft).astype(np.float32) / 255.0
        # 남은 음식 바로 주변만 보이게 해서, 지운 자리에 반투명 윤곽선이 남지 않게 한다
        near = Image.fromarray(((solid & ~removed) * 255).astype(np.uint8))
        near = near.filter(ImageFilter.MaxFilter(5)).filter(ImageFilter.GaussianBlur(0.9))
        keep *= np.asarray(near).astype(np.float32) / 255.0
        bitten = canvas.copy()
        bitten.putalpha(Image.fromarray((alpha * keep).astype(np.uint8)))
        uris.append(_png_uri(bitten))
        centers.append((bx / px, by / px))
    return uris, centers


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


def warm_thumbs() -> None:
    """기본 크기 음식 썸네일을 모두 만들어 캐시에 넣는다. 이미 있으면 바로 끝난다."""
    for food in FOODS:
        food_thumb(food)


def food_bitten(food: Food, bites_eaten: int, px: int = 480) -> tuple[str, tuple[float, float] | None]:
    """bites_eaten입 먹은 모습(투명 PNG)과 마지막으로 베어 문 자리(0~1 비율, 없으면 None)."""
    uris, centers = _bitten_uris(str(food.image_path), px, food.bites)
    k = max(0, min(bites_eaten, food.bites - 1))
    return uris[k], centers[k]


def profile_thumb(path: Path, px: int = 128) -> str:
    return _profile_uri(str(path), px)
