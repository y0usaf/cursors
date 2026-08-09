#!/usr/bin/env python3
"""Repair xcursor files whose nominal (advertised) size lies about the bitmap.

The deepin-derived themes (deepin-dark, deepin-light, ssb) ship frames whose
bitmaps are 4/3 of the declared size (nominal 24 -> 32x32 pixels). Cursor
consumers select by nominal size but blit raw pixels, so every cursor renders
~1.33x too large. This script:

  1. relabels every frame's nominal size to its true pixel size
     (hotspots are stored in pixel coordinates already, so they stay put);
  2. synthesizes the requested extra sizes (default 18, 24) by Lanczos-
     downscaling the smallest available frame group. Xcursor pixels are
     premultiplied ARGB, so per-channel resampling is correct as-is.

Animation frame groups and per-frame delays are preserved. Comment chunks are
dropped. Symlinked aliases are left untouched (they resolve to fixed files).

Usage: fix-xcursor-nominal-sizes.py [--sizes 18,24] THEME_CURSOR_DIR...
"""

import argparse
import os
import struct
import sys

from PIL import Image

XCUR_MAGIC = b"Xcur"
CHUNK_IMAGE = 0xFFFD0002
IMAGE_HEADER_SIZE = 36


def parse(path):
    """-> list of frames: dict(nominal, w, h, xhot, yhot, delay, pixels)."""
    data = open(path, "rb").read()
    if data[:4] != XCUR_MAGIC:
        return None
    ntoc = struct.unpack("<I", data[12:16])[0]
    frames = []
    off = 16
    for _ in range(ntoc):
        typ, sub, pos = struct.unpack("<III", data[off : off + 12])
        off += 12
        if typ != CHUNK_IMAGE:
            continue  # comment chunk: dropped
        hsz, ctyp, csub, ver, w, h, xhot, yhot, delay = struct.unpack(
            "<9I", data[pos : pos + IMAGE_HEADER_SIZE]
        )
        pixels = data[pos + IMAGE_HEADER_SIZE : pos + IMAGE_HEADER_SIZE + w * h * 4]
        frames.append(
            dict(nominal=sub, w=w, h=h, xhot=xhot, yhot=yhot, delay=delay, pixels=pixels)
        )
    return frames


def write(path, frames):
    frames = sorted(frames, key=lambda f: f["nominal"])
    ntoc = len(frames)
    toc_end = 16 + 12 * ntoc
    body = bytearray()
    toc = bytearray()
    pos = toc_end
    for f in frames:
        toc += struct.pack("<III", CHUNK_IMAGE, f["nominal"], pos)
        chunk = struct.pack(
            "<9I",
            IMAGE_HEADER_SIZE,
            CHUNK_IMAGE,
            f["nominal"],
            1,
            f["w"],
            f["h"],
            f["xhot"],
            f["yhot"],
            f["delay"],
        ) + f["pixels"]
        body += chunk
        pos += len(chunk)
    header = struct.pack("<4sIII", XCUR_MAGIC, 16, 0x10000, ntoc)
    open(path, "wb").write(header + toc + body)


def scale_frame(f, target):
    """Downscale one frame to nominal/pixel size 'target' (square-ish)."""
    img = Image.frombytes("RGBA", (f["w"], f["h"]), f["pixels"], "raw", "BGRA")
    factor = target / f["w"]
    nw, nh = target, max(1, round(f["h"] * factor))
    img = img.resize((nw, nh), Image.LANCZOS)
    return dict(
        nominal=target,
        w=nw,
        h=nh,
        xhot=min(nw - 1, round(f["xhot"] * factor)),
        yhot=min(nh - 1, round(f["yhot"] * factor)),
        delay=f["delay"],
        pixels=img.tobytes("raw", "BGRA"),
    )


def fix_file(path, extra_sizes):
    frames = parse(path)
    if frames is None:
        return False
    # 1. relabel: nominal := true pixel width
    for f in frames:
        f["nominal"] = f["w"]
    # 2. synthesize extra sizes from the smallest frame group
    smallest = min(f["nominal"] for f in frames)
    source_group = [f for f in frames if f["nominal"] == smallest]
    have = {f["nominal"] for f in frames}
    for target in extra_sizes:
        if target in have or target >= smallest:
            continue
        frames += [scale_frame(f, target) for f in source_group]
    write(path, frames)
    return True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sizes", default="18,24")
    ap.add_argument("dirs", nargs="+", help="theme 'cursors' directories")
    args = ap.parse_args()
    extra = sorted(int(s) for s in args.sizes.split(","))
    for d in args.dirs:
        fixed = 0
        for name in sorted(os.listdir(d)):
            p = os.path.join(d, name)
            if os.path.islink(p) or not os.path.isfile(p):
                continue
            if fix_file(p, extra):
                fixed += 1
        print(f"{d}: fixed {fixed} files (added sizes {extra})")


if __name__ == "__main__":
    main()
