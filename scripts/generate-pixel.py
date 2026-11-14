#!/usr/bin/env python3

import json
import struct
import sys
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
THEMES = ROOT / "themes"
NOMINALS = [32, 40, 48, 64]
DELAY = 50

ART = {
    "default": [
        "###",
        "#o#",
        "###",
    ],
    "pointer": [
        "##o",
        "###",
        "###",
    ],
    "text": [
        "#o#",
        "#o#",
        "#o#",
    ],
    "vertical-text": [
        "ooo",
        "###",
        "ooo",
    ],
    "crosshair": [
        "#o#",
        "ooo",
        "#o#",
    ],
    "move": [
        "#o#",
        "o#o",
        "#o#",
    ],
    "grab": [
        "ooo",
        "o#o",
        "ooo",
    ],
    "grabbing": [
        "ooo",
        "ooo",
        "ooo",
    ],
    "not-allowed": [
        "o##",
        "#o#",
        "##o",
    ],
    "progress": [
        "###",
        "o#o",
        "###",
    ],
    "wait": [
        "###",
        "ooo",
        "###",
    ],
    "help": [
        "#o#",
        "###",
        "#o#",
    ],
    "context-menu": [
        "ooo",
        "###",
        "###",
    ],
}

NAME_ART = {
    "alias": "pointer",
    "all-resize": "move",
    "all-scroll": "move",
    "arrow": "default",
    "bd_double_arrow": "move",
    "bottom_left_corner": "move",
    "bottom_right_corner": "move",
    "bottom_side": "move",
    "cell": "move",
    "center_ptr": "default",
    "circle": "not-allowed",
    "closedhand": "grabbing",
    "col-resize": "move",
    "color-picker": "crosshair",
    "context-menu": "context-menu",
    "copy": "grabbing",
    "cross": "crosshair",
    "crossed_circle": "not-allowed",
    "crosshair": "crosshair",
    "default": "default",
    "dnd-ask": "help",
    "dnd-copy": "grabbing",
    "dnd-link": "pointer",
    "dnd-move": "grabbing",
    "dnd-none": "grabbing",
    "dnd-no-drop": "not-allowed",
    "down-arrow": "move",
    "draft": "move",
    "e-resize": "move",
    "ew-resize": "move",
    "fd_double_arrow": "move",
    "fleur": "move",
    "forbidden": "not-allowed",
    "grab": "grab",
    "grabbing": "grabbing",
    "h_double_arrow": "move",
    "half-busy": "progress",
    "hand1": "pointer",
    "hand2": "pointer",
    "help": "help",
    "ibeam": "text",
    "left-arrow": "move",
    "left_ptr": "default",
    "left_ptr_help": "help",
    "left_ptr_watch": "progress",
    "left_side": "move",
    "link": "pointer",
    "ll_angle": "move",
    "lr_angle": "move",
    "move": "move",
    "n-resize": "move",
    "ne-resize": "move",
    "nesw-resize": "move",
    "no-drop": "not-allowed",
    "not-allowed": "not-allowed",
    "ns-resize": "move",
    "nw-resize": "move",
    "nwse-resize": "move",
    "openhand": "grab",
    "pencil": "text",
    "pirate": "not-allowed",
    "plus": "cell",
    "pointer": "pointer",
    "pointing_hand": "pointer",
    "progress": "progress",
    "question_arrow": "help",
    "right-arrow": "move",
    "right_ptr": "default",
    "right_side": "move",
    "row-resize": "move",
    "s-resize": "move",
    "sb_h_double_arrow": "move",
    "sb_v_double_arrow": "move",
    "se-resize": "move",
    "size_all": "move",
    "size_bdiag": "move",
    "size_fdiag": "move",
    "size_hor": "move",
    "size_ver": "move",
    "split_h": "move",
    "split_v": "move",
    "sw-resize": "move",
    "text": "text",
    "top_left_corner": "move",
    "top_right_corner": "move",
    "top_side": "move",
    "ul_angle": "move",
    "up-arrow": "move",
    "ur_angle": "move",
    "v_double_arrow": "move",
    "vertical-text": "vertical-text",
    "wait": "wait",
    "watch": "wait",
    "wayland-cursor": "default",
    "whats_this": "help",
    "x-cursor": "default",
    "xterm": "text",
    "zoom-in": "move",
    "zoom-out": "move",
}

HOTSPOT_LEFT = {"text"}

VARIANTS = {
    "pixel-dark": ("Pixel-Dark-xcursor", "Pixel square cursor, dark variant", (0, 0, 0), (255, 255, 255)),
    "pixel-light": ("Pixel-Light-xcursor", "Pixel square cursor, light variant", (255, 255, 255), (0, 0, 0)),
}


def masks(grid):
    height = len(grid)
    width = len(grid[0])
    shape = {(x, y) for y in range(height) for x in range(width) if grid[y][x] != "."}
    marks = {(x, y) for x, y in shape if grid[y][x] == "o"}
    return shape, marks, width, height


def grid_span():
    return max(max(max(len(row) for row in art), len(art)) for art in ART.values())


def render(grid, nominal, fill, contrast, left_hotspot):
    shape, marks, width, height = masks(grid)
    scale = min(max(1, nominal * 7 // 32), (nominal - 2) // grid_span())
    ink_w = width * scale + 2
    ink_h = height * scale + 2
    left = (nominal - ink_w) // 2
    top = (nominal - ink_h) // 2
    pixels = bytearray(nominal * nominal * 4)
    for py in range(ink_h):
        for px in range(ink_w):
            cell_x = (px - 1) // scale
            cell_y = (py - 1) // scale
            inside = px not in (0, ink_w - 1) and py not in (0, ink_h - 1)
            if inside and (cell_x, cell_y) in shape:
                color = contrast if (cell_x, cell_y) in marks else fill
            else:
                color = contrast
            offset = ((top + py) * nominal + left + px) * 4
            pixels[offset : offset + 4] = bytes(color) + b"\xff"
    hotspot_x = left if left_hotspot else nominal // 2
    return nominal, hotspot_x, nominal // 2, bytes(pixels)


def write_png(path, width, height, pixels):
    stride = width * 4
    raw = b"".join(b"\x00" + pixels[y * stride : (y + 1) * stride] for y in range(height))
    chunks = [
        (b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)),
        (b"IDAT", zlib.compress(raw, 9)),
        (b"IEND", b""),
    ]
    data = bytearray(b"\x89PNG\r\n\x1a\n")
    for kind, body in chunks:
        data += struct.pack(">I", len(body)) + kind + body
        data += struct.pack(">I", zlib.crc32(kind + body) & 0xFFFFFFFF)
    path.write_bytes(data)


def standard_names():
    names = set(NAME_ART)
    for meta_path in sorted(THEMES.glob("*/theme.json")):
        if meta_path.parent.name.startswith("pixel-"):
            continue
        meta = json.loads(meta_path.read_text())
        names.update(meta.get("cursors", {}))
        names.update(meta.get("aliases", {}))
    return sorted(names)


def names_of(cursors, aliases):
    for name in sorted(set(cursors) | set(aliases)):
        value = cursors.get(name, aliases.get(name))
        if value is None:
            raise SystemExit(f"{name}: unresolved")


def main():
    aliases = {}
    for name in standard_names():
        art = NAME_ART.get(name, "default")
        if name in ART:
            continue
        aliases[name] = art
    for slug, (name, comment, fill, contrast) in VARIANTS.items():
        theme_dir = THEMES / slug
        theme_dir.mkdir(parents=True, exist_ok=True)
        for stale in theme_dir.glob("*.png"):
            stale.unlink()
        cursors = {}
        for art, grid in ART.items():
            frames = []
            for nominal in NOMINALS:
                size, x, y, pixels = render(grid, nominal, fill, contrast, art in HOTSPOT_LEFT)
                file = f"{art}-{size}.png"
                write_png(theme_dir / file, size, size, pixels)
                frames.append({"size": size, "x": x, "y": y, "delay": DELAY, "file": file})
            cursors[art] = frames
        names_of(cursors, aliases)
        meta = {
            "name": name,
            "comment": comment,
            "cursors": cursors,
            "aliases": aliases,
        }
        (theme_dir / "theme.json").write_text(json.dumps(meta, indent=2, sort_keys=True) + "\n")
        print(f"{slug}: {len(cursors)} cursors, {len(aliases)} aliases")


if __name__ == "__main__":
    sys.exit(main())
