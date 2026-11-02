"""브랜드 가이드 이미지(assets/img/Brand_Guide/mukbogibrand.png)에서 로고·마스코트를 잘라 assets/img/brand/에 저장한다.

실행: .venv/bin/python tools/extract_brand_assets.py
- 가이드 패널의 밝은 바탕은 테두리에서 이어진 부분만 투명하게 뺀다(마스코트 안쪽 크림색은 검은 외곽선에 막혀 남는다).
- 주황 앱 아이콘의 흰 마스코트는 주황 바탕을 투명하게 빼서, 어떤 주황 바탕 위에도 올릴 수 있게 한다(눈은 구멍으로 남아 바탕색이 비친다).
가이드 이미지가 바뀌면 아래 좌표(BOXES)를 다시 맞춘다.
"""

from collections import deque
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "assets" / "img" / "Brand_Guide" / "mukbogibrand.png"
OUT = ROOT / "assets" / "img" / "brand"

# (왼, 위, 오른, 아래) — 1536×1024 가이드 기준
BOXES = {
    "logo": (55, 105, 630, 275),          # 마스코트 얼굴이 O 자리에 들어간 로고 (검정)
    "mascot_outline": (1075, 120, 1210, 260),  # 크림 바탕 + 검은 외곽선 얼굴
    "mascot_peek": (500, 725, 650, 845),  # 빼꼼 내다보는 마스코트
    "mascot_back": (680, 710, 830, 860),  # 뒷모습
    "mascot_run": (860, 690, 1020, 870),  # 달리는 마스코트
}
ICON_BOX = (775, 118, 940, 282)  # 주황 앱 아이콘 안쪽 (흰 마스코트)


def _transparent_edges(im: Image.Image, tol: int = 16) -> Image.Image:
    """테두리에서 시작해 바탕색과 비슷한 픽셀을 이어서 투명하게 만든다."""
    rgb = np.asarray(im.convert("RGB")).astype(int)
    h, w, _ = rgb.shape
    bg = np.median(np.concatenate([rgb[0], rgb[-1], rgb[:, 0], rgb[:, -1]]), axis=0)
    close = np.abs(rgb - bg).max(axis=2) <= tol
    mask = np.zeros((h, w), bool)
    q = deque((y, x) for y in range(h) for x in (0, w - 1)) + deque((y, x) for x in range(w) for y in (0, h - 1))
    while q:
        y, x = q.popleft()
        if 0 <= y < h and 0 <= x < w and close[y, x] and not mask[y, x]:
            mask[y, x] = True
            q.extend(((y + 1, x), (y - 1, x), (y, x + 1), (y, x - 1)))
    rgba = np.dstack([rgb, np.where(mask, 0, 255)]).astype(np.uint8)
    return _trim(Image.fromarray(rgba, "RGBA"))


def _knock_out_orange(im: Image.Image) -> Image.Image:
    """주황 바탕을 빼고 흰 부분만 남긴다. 주황과 흰색 사이 경계는 거리 비율로 반투명 처리."""
    rgb = np.asarray(im.convert("RGB")).astype(float)
    orange = np.median(rgb[:6, :6].reshape(-1, 3), axis=0)
    white = np.array([255.0, 250.0, 242.0])
    t = np.clip(((rgb - orange) @ (white - orange)) / ((white - orange) @ (white - orange)), 0, 1)
    alpha = np.clip((t - 0.25) / 0.6, 0, 1) * 255
    rgba = np.dstack([np.broadcast_to(white, rgb.shape), alpha]).astype(np.uint8)
    return _trim(Image.fromarray(rgba, "RGBA"))


def _trim(im: Image.Image, pad: int = 4) -> Image.Image:
    box = im.getchannel("A").getbbox()
    if not box:
        return im
    l, t, r, b = box
    return im.crop((max(l - pad, 0), max(t - pad, 0), min(r + pad, im.width), min(b + pad, im.height)))


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    guide = Image.open(SRC)
    for name, box in BOXES.items():
        _transparent_edges(guide.crop(box)).save(OUT / f"{name}.png")
    _knock_out_orange(guide.crop(ICON_BOX)).save(OUT / "mascot_white.png")
    for p in sorted(OUT.glob("*.png")):
        print(p.relative_to(ROOT), Image.open(p).size)


if __name__ == "__main__":
    main()
