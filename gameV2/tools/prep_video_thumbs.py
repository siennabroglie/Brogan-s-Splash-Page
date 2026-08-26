#!/usr/bin/env python3
"""Re-encode the pop-up video thumbnails as WebP.

The delivered thumbnails are lossless PNGs of video frames — ~1500x825, a median
of 1.6 MB each, 97 MB across the 58 of them. Three things are wrong with that for
art whose only job is to fill a grid cell:

  * PNG is a lossless format built for flat colour and line art. These are
    photographs. WebP carries the same frame at roughly 1/40th the bytes.
  * Every one is RGBA with a fully opaque alpha channel — a whole extra channel
    of nothing.
  * They are ~1500px wide and the grid renders them around 247px
    (`#photo-popup .grid` is `min(86vw, 1100px)` wide with `minmax(200px, 1fr)`
    columns), so ~6x more pixels are shipped than are ever drawn.

MAX_WIDTH is set to about 3x the drawn size so the art still resolves on a hi-dpi
screen, where the same cell is backed by 2-3x the device pixels.

The PNGs are REPLACED, not archived: they are already in git history, so an
original is `git show <sha>:gameV2/videoAssets/<Folder>/<name>.png` away, and
keeping a copy in the tree would leave all 97 MB in every future clone for no
gain. Contrast prep_props.py, which does keep `_originals/` — the prop art there
is re-capped as the look is tuned, so the source is reached for often.

Idempotent: a PNG whose .webp already exists is skipped, so re-running is a
no-op. To force a re-encode (say, at a different QUALITY), delete that folder's
.webp files first — but note the PNG is gone by then, so pull it from git.

Filenames are preserved byte-for-byte apart from the extension, curly
apostrophes and colons included; index.html reaches them through
gen_video_collections.py, which reads the same directory.

Run:  pip install pillow  &&  python3 gameV2/tools/prep_video_thumbs.py
Then: python3 gameV2/tools/gen_video_collections.py   (regenerates the JS block)
"""

import os

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.normpath(os.path.join(HERE, "..", "videoAssets"))

MAX_WIDTH = 800    # ~3x the ~247px the grid draws, so hi-dpi still resolves
QUALITY = 80       # WebP quality; 80 holds up at full size on this material
METHOD = 6         # slowest/best WebP search — these are encoded once


def convert_folder(folder):
    """Re-encode one collection. Returns (before_bytes, after_bytes, n_done, n_skipped)."""
    path = os.path.join(ASSETS, folder)
    before = after = done = skipped = 0
    for name in sorted(os.listdir(path)):
        if not name.lower().endswith(".png"):
            continue
        src = os.path.join(path, name)
        dst = os.path.join(path, os.path.splitext(name)[0] + ".webp")
        if os.path.exists(dst):
            skipped += 1
            continue

        src_bytes = os.path.getsize(src)
        im = Image.open(src)
        # Drop the alpha channel — measured fully opaque on every one of these.
        im = im.convert("RGB")
        w, h = im.size
        if w > MAX_WIDTH:                       # never upscale the already-small ones
            im = im.resize((MAX_WIDTH, round(h * MAX_WIDTH / w)), Image.LANCZOS)
        im.save(dst, "WEBP", quality=QUALITY, method=METHOD)

        os.remove(src)
        before += src_bytes
        after += os.path.getsize(dst)
        done += 1
    return before, after, done, skipped


def main():
    if not os.path.isdir(ASSETS):
        raise SystemExit(f"videoAssets not found: {ASSETS}")

    folders = sorted(f for f in os.listdir(ASSETS)
                     if os.path.isdir(os.path.join(ASSETS, f)))
    tot_before = tot_after = tot_done = tot_skipped = 0
    print(f"Re-encoding to WebP (max {MAX_WIDTH}px wide, quality {QUALITY})\n")
    for folder in folders:
        before, after, done, skipped = convert_folder(folder)
        tot_before += before; tot_after += after
        tot_done += done; tot_skipped += skipped
        note = f"{done} converted" + (f", {skipped} already done" if skipped else "")
        if done:
            print(f"  {folder:32s} {before/1048576:6.1f} MB -> {after/1048576:5.2f} MB   {note}")
        else:
            print(f"  {folder:32s} {'':6s}    {'':5s}      {note or 'nothing to do'}")

    print()
    if tot_done:
        print(f"  {'TOTAL':32s} {tot_before/1048576:6.1f} MB -> {tot_after/1048576:5.2f} MB "
              f"({tot_before/max(1, tot_after):.0f}x smaller, {tot_done} files)")
    else:
        # tot_skipped only counts PNGs still sitting next to a .webp; once a run has finished
        # there are none, so report what is actually on disk instead of a misleading zero.
        have = sum(len([f for f in os.listdir(os.path.join(ASSETS, d)) if f.lower().endswith(".webp")])
                   for d in folders)
        print(f"  nothing to do — all {have} thumbnails are already WebP")
    print("\nNext: python3 gameV2/tools/gen_video_collections.py")


if __name__ == "__main__":
    main()
