#!/usr/bin/env python3
"""Relabel xcursor frame nominal sizes to their true pixel size.

The deepin-derived themes (deepin-dark, deepin-light, ssb) ship frames whose
bitmaps are 4/3 of the declared size (nominal 24 -> 32x32 pixels). Cursor
consumers select by nominal size but blit raw pixels, so every cursor renders
~1.33x too large. This script relabels every frame's nominal size to its true
pixel width (hotspots are stored in pixel coordinates already, so they stay
put). Animation frame groups and per-frame delays are preserved verbatim, as
are the raw pixels. Symlinked aliases are left untouched.

No resampling and no synthesized sizes are produced; the file otherwise keeps
the exact Xcursor format.

Usage: fix-xcursor-nominal-sizes.py THEME_CURSOR_DIR...
"""

import os
import struct
import sys

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


def fix_file(path):
    frames = parse(path)
    if frames is None:
        return False
    for f in frames:
        f["nominal"] = f["w"]
    write(path, frames)
    return True


def main():
    for d in sys.argv[1:]:
        fixed = 0
        for name in sorted(os.listdir(d)):
            p = os.path.join(d, name)
            if os.path.islink(p) or not os.path.isfile(p):
                continue
            if fix_file(p):
                fixed += 1
        print(f"{d}: relabeled {fixed} files")


if __name__ == "__main__":
    main()
