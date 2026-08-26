#!/usr/bin/env python3
"""Cut the six hand-drawn pointer arrows out of the source sheet and emit game-ready sprites.

The sheet (`arrow-assets/_source/arrow-sheet.png`) is a screenshot: black ink over a
transparency checkerboard, with no real alpha. We key the ink out by luminance, split it into
connected components — one per arrow — and write each as a flat-orange PNG whose alpha carries
the stroke.

Each sprite is masked to its OWN component, not just cropped to its bounding box. The arrows are
hand-arranged on the sheet closely enough that their boxes interlock — `curve` is tall and narrow,
so its box brackets the right arrowhead of `double` and the middle of `squiggle` — and a plain
rectangular crop bakes that foreign ink into the sprite.

It also measures, per arrow, the two numbers index.html needs to aim it:

  tip  the arrowhead's point, as (u, v) within the sprite, v DOWN. Found by taking a rough
       hand-placed estimate and sliding it to whichever ink pixel nearby reaches furthest along
       (estimate - centroid), i.e. the true extremity of the head.
  aim  the direction that point indicates, in degrees (0 = right, +90 = down). Taken from the
       arrowhead's OWN mass: the barbs sit behind the point, so head-centroid -> point is the
       direction the arrow reads as indicating. Using the whole sprite's centroid instead gets
       the curved arrows badly wrong.

Paste the printed ARROWS rows into index.html if the art is ever re-cut.

Run:  pip install pillow numpy  &&  python3 gameV2/tools/gen_arrows.py
"""

import math
import os
from collections import deque

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ARROWS = os.path.normpath(os.path.join(HERE, "..", "sceneAssets", "arrow-assets"))
SHEET = os.path.join(ARROWS, "_source", "arrow-sheet.png")

ORANGE = (242, 135, 46)   # --orange (#f2872e) from the game's CSS
INK_HI = 235.0            # luminance at/above which a pixel is background
INK_LO = 60.0             # …and at/below which it is solid ink; between the two is the AA ramp
SOLID = 0.35              # alpha above this counts as ink for component-finding and measuring
MIN_PX = 400              # ignore specks smaller than this
MASK_GROW = 3             # px the per-arrow mask is grown by before it is applied — see main()

# Reading order across the sheet, with a rough hand-placed guess at each arrowhead's point
# (u, v within that arrow's own crop). The guess only has to land ON the head — snap_tip()
# slides it to the true extremity from there.
PROPS = [
    ("loop",     (0.96, 0.10)),
    ("straight", (0.99, 0.56)),
    ("double",   (0.99, 0.55)),   # two heads; we aim with the right-hand one
    ("curve",    (0.17, 0.04)),
    ("hook",     (0.94, 0.19)),
    ("squiggle", (0.95, 0.60)),
]

SNAP_R = 0.16    # radius (x longest edge) searched around the estimate when snapping the tip
HEAD_R = 0.22    # radius (x longest edge) of the arrowhead region used to derive `aim`
PAD = 6          # px of transparent margin kept around each cut-out


def components(solid):
    """Label connected ink blobs (8-connected, with a 2px reach to bridge AA gaps).

    Returns (boxes, labels): one bounding box per kept blob in reading order, and an int image
    where every pixel of blob i carries the value i + 1. The labels are what let each sprite be
    masked to its own stroke — bounding boxes alone can't, because they overlap.
    """
    h, w = solid.shape
    seen = np.zeros_like(solid)
    out = []
    for y in range(h):
        for x in range(w):
            if not solid[y, x] or seen[y, x]:
                continue
            q = deque([(y, x)])
            seen[y, x] = True
            px = []
            while q:
                cy, cx = q.popleft()
                px.append((cy, cx))
                for ny in range(cy - 2, cy + 3):
                    for nx in range(cx - 2, cx + 3):
                        if 0 <= ny < h and 0 <= nx < w and solid[ny, nx] and not seen[ny, nx]:
                            seen[ny, nx] = True
                            q.append((ny, nx))
            if len(px) >= MIN_PX:
                ys = np.array([p[0] for p in px])
                xs = np.array([p[1] for p in px])
                out.append((xs.min(), ys.min(), xs.max(), ys.max(), ys, xs))
    out.sort(key=lambda c: (c[1] // 120, c[0]))     # rows top-to-bottom, then left-to-right
    # Paint the labels only after the sort, so a blob's label is its index in reading order.
    labels = np.zeros((h, w), np.int32)
    for i, c in enumerate(out):
        labels[c[4], c[5]] = i + 1
    return [c[:4] for c in out], labels


def grow(mask, r):
    """Grow a boolean mask by r px. Four-neighbour dilation, r times — numpy only, no scipy."""
    for _ in range(r):
        g = mask.copy()
        g[1:, :] |= mask[:-1, :]
        g[:-1, :] |= mask[1:, :]
        g[:, 1:] |= mask[:, :-1]
        g[:, :-1] |= mask[:, 1:]
        mask = g
    return mask


def snap_tip(xs, ys, est, shape):
    """Slide a rough estimate onto the ink pixel that reaches furthest out along it."""
    h, w = shape
    cx, cy = xs.mean(), ys.mean()
    ex, ey = est[0] * w, est[1] * h
    dx, dy = ex - cx, ey - cy
    n = math.hypot(dx, dy) or 1.0
    dx, dy = dx / n, dy / n
    r = SNAP_R * max(w, h)
    near = (xs - ex) ** 2 + (ys - ey) ** 2 <= r * r
    if not near.any():
        near = np.ones(len(xs), bool)
    k = int(np.argmax((xs[near] - cx) * dx + (ys[near] - cy) * dy))
    return float(xs[near][k]), float(ys[near][k])


def main():
    sheet = np.asarray(Image.open(SHEET).convert("RGB")).astype(np.float32)
    lum = sheet[..., 0] * 0.299 + sheet[..., 1] * 0.587 + sheet[..., 2] * 0.114
    alpha = np.clip((INK_HI - lum) / (INK_HI - INK_LO), 0, 1)

    boxes, labels = components(alpha > SOLID)
    if len(boxes) != len(PROPS):
        raise SystemExit(f"expected {len(PROPS)} arrows on the sheet, found {len(boxes)}")

    print("Writing sprites to", ARROWS)
    print("\n  // paste into index.html:")
    for i, ((name, est), (x0, y0, x1, y1)) in enumerate(zip(PROPS, boxes)):
        y0p, y1p = max(0, y0 - PAD), y1 + 1 + PAD
        x0p, x1p = max(0, x0 - PAD), x1 + 1 + PAD
        # Keep only THIS arrow's ink: the crop is a plain rectangle of the sheet, so without the
        # mask any neighbour whose box overlaps rides along. Grow the mask first — connectivity is
        # measured on the SOLID mask while the sprite carries the full anti-aliased ramp, so a
        # strict mask would shave the soft stroke edge into a hard, thin line.
        keep = grow(labels[y0p:y1p, x0p:x1p] == i + 1, MASK_GROW)
        sub = alpha[y0p:y1p, x0p:x1p] * keep
        h, w = sub.shape
        ys, xs = np.where(sub > SOLID)   # measured post-mask, so no stray ink drags the centroid

        tx, ty = snap_tip(xs, ys, est, sub.shape)
        r = HEAD_R * max(w, h)
        head = (xs - tx) ** 2 + (ys - ty) ** 2 <= r * r
        aim = math.degrees(math.atan2(ty - ys[head].mean(), tx - xs[head].mean()))

        rgba = np.zeros((h, w, 4), np.uint8)
        rgba[..., 0], rgba[..., 1], rgba[..., 2] = ORANGE
        rgba[..., 3] = (sub * 255).astype(np.uint8)
        Image.fromarray(rgba, "RGBA").save(os.path.join(ARROWS, f"arrow_{name}.png"))

        print(f"  {{ file: 'arrow_{name}.png',".ljust(34)
              + f"tip: [{tx / w:.3f}, {ty / h:.3f}], aim: {aim:7.1f}, ar: {w} / {h} }},")


if __name__ == "__main__":
    main()
