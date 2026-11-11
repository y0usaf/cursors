#!/usr/bin/env python3
"""Write an Xcursor theme from theme.json and its PNG frames.

Frames are stored in PNG form as the exact RGBA bytes an Xcursor image chunk
holds, so the output decodes to the same pixels, hotspots and delays as the
recorded source. Nominal size and pixel size are always equal; consumers pick a
frame by nominal size and blit its bitmaps without rescaling.
"""

import json
import struct
import sys
import zlib
from pathlib import Path

IMAGE_TYPE = 0xFFFD0002
IMAGE_VERSION = 1
HEADER_SIZE = 16
IMAGE_HEADER_SIZE = 36


def read_png(path):
    data = path.read_bytes()
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise SystemExit(f"{path}: not a PNG")
    pos = 8
    width = height = None
    idat = bytearray()
    while pos < len(data):
        (length,) = struct.unpack_from(">I", data, pos)
        kind = data[pos + 4 : pos + 8]
        body = data[pos + 8 : pos + 8 + length]
        pos += 12 + length
        if kind == b"IHDR":
            width, height, depth, color, _, _, interlace = struct.unpack(">IIBBBBB", body)
            if (depth, color, interlace) != (8, 6, 0):
                raise SystemExit(f"{path}: expected non-interlaced 8-bit RGBA")
        elif kind == b"IDAT":
            idat += body
        elif kind == b"IEND":
            break
    raw = zlib.decompress(bytes(idat))
    stride = width * 4
    out = bytearray()
    prev = bytearray(stride)
    off = 0
    for _ in range(height):
        filter_type = raw[off]
        row = bytearray(raw[off + 1 : off + 1 + stride])
        off += 1 + stride
        for i in range(stride):
            left = row[i - 4] if i >= 4 else 0
            up = prev[i]
            upleft = prev[i - 4] if i >= 4 else 0
            if filter_type == 1:
                row[i] = (row[i] + left) & 0xFF
            elif filter_type == 2:
                row[i] = (row[i] + up) & 0xFF
            elif filter_type == 3:
                row[i] = (row[i] + (left + up) // 2) & 0xFF
            elif filter_type == 4:
                p = left + up - upleft
                pa, pb, pc = abs(p - left), abs(p - up), abs(p - upleft)
                pred = left if pa <= pb and pa <= pc else (up if pb <= pc else upleft)
                row[i] = (row[i] + pred) & 0xFF
            elif filter_type != 0:
                raise SystemExit(f"{path}: bad PNG filter {filter_type}")
        out += row
        prev = row
    return width, height, bytes(out)


def main(theme_dir, out):
    theme_dir = Path(theme_dir)
    meta = json.loads((theme_dir / "theme.json").read_text())
    name = meta["name"]
    dest = Path(out) / "share" / "icons" / name
    cursors = dest / "cursors"
    cursors.mkdir(parents=True)

    lines = ["[Icon Theme]", f"Name={name}"]
    for key, field in (("comment", "Comment"), ("inherits", "Inherits")):
        if key in meta:
            lines.append(f"{field}={meta[key]}")
    (dest / "index.theme").write_text("\n".join(lines) + "\n")

    for cursor, frames in sorted(meta["cursors"].items()):
        images = []
        for frame in frames:
            width, height, pixels = read_png(theme_dir / frame["file"])
            if width != frame["size"]:
                raise SystemExit(f"{frame['file']}: width {width} != nominal size {frame['size']}")
            rgba = bytearray(len(pixels))
            rgba[0::4] = pixels[2::4]
            rgba[1::4] = pixels[1::4]
            rgba[2::4] = pixels[0::4]
            rgba[3::4] = pixels[3::4]
            images.append(
                (frame["size"], struct.pack("<9I", IMAGE_HEADER_SIZE, IMAGE_TYPE, frame["size"], IMAGE_VERSION, width, height, frame["x"], frame["y"], frame["delay"]) + bytes(rgba))
            )
        body = bytearray()
        toc = bytearray()
        pos = HEADER_SIZE + 12 * len(images)
        for size, chunk in images:
            toc += struct.pack("<III", IMAGE_TYPE, size, pos)
            body += chunk
            pos += len(chunk)
        header = struct.pack("<4sIII", b"Xcur", HEADER_SIZE, 0x10000, len(images))
        (cursors / cursor).write_bytes(header + toc + body)

    for alias, target in sorted(meta["aliases"].items()):
        (cursors / alias).symlink_to(target)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
