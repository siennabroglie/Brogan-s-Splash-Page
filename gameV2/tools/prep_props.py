#!/usr/bin/env python3
"""Prepare the gameV2 prop art for loading.

The delivered art is drawn at one common scale (pixel size is proportional to real-world
size), which is what keeps the props in proportion to each other in-game — see SCENE_PROPS in
gameV2/index.html. But it also arrives large: Babylon pads non-power-of-two textures up to the
next power of two to build mipmaps, so a 4033px-wide barn becomes a 4096x4096 (~67 MB) GPU
texture, which is a real problem on phones.

This script archives each delivered PNG under `_originals/` once, then rewrites the working
copy so its long edge is at most MAX_EDGE. It is idempotent: a prop already archived is left
alone, so re-running never re-downscales an already-capped file. Drop a fresh export in over
the working copy, delete its `_originals/` entry, and re-run to re-cap it.

In-game scale is NOT affected by what this does — SCENE_PROPS records each prop's ORIGINAL
pixel size, so re-capping at a different MAX_EDGE never changes how big a prop reads.

Run:  pip install pillow  &&  python3 gameV2/tools/prep_props.py
"""

import os
import shutil

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.normpath(os.path.join(HERE, "..", "sceneAssets", "interactive-assets"))
ORIGINALS = os.path.join(ASSETS, "_originals")   # the delivered art, kept untouched
MAX_EDGE = 2048           # cap the shipped PNGs' long edge (see the mipmap note above)

# Prop art the game loads, one entry per SCENE_PROPS row in index.html.
SOURCES = ["barn", "boat", "haystack", "routeCellar", "toxicBarrels",
           "tractor", "tree", "wheelBarrow"]


def cap_sources():
    os.makedirs(ORIGINALS, exist_ok=True)
    for name in SOURCES:
        src = os.path.join(ASSETS, name + ".png")
        keep = os.path.join(ORIGINALS, name + ".png")
        if not os.path.exists(src):
            print(f"  {name:14s} MISSING  {src}")
            continue
        if os.path.exists(keep):
            w, h = Image.open(src).size
            print(f"  {name:14s} already capped  ({w}x{h})")
            continue
        shutil.copy2(src, keep)                      # preserve the art as delivered
        im = Image.open(src)
        w, h = im.size
        if max(w, h) <= MAX_EDGE:
            print(f"  {name:14s} {w}x{h} under cap  -> archived, left as-is")
            continue
        k = MAX_EDGE / max(w, h)
        nw, nh = max(1, round(w * k)), max(1, round(h * k))
        im.convert("RGBA").resize((nw, nh), Image.LANCZOS).save(src)
        print(f"  {name:14s} {w}x{h} -> {nw}x{nh}")


if __name__ == "__main__":
    print("Capping prop art in", ASSETS)
    cap_sources()
    print("Done.")
