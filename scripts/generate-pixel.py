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
        "##....",
        "#.....",
        "..####",
        "..####",
        "..####",
        "..####",
    ],
    "progress": [
        "##....",
        "#.....",
        "..####",
        "..####",
        "..####",
        "..###.",
    ],
    "pointer": [
        ".#.....",
        ".#.....",
        ".#.....",
        ".#.###.",
        "#######",
        ".#####.",
        "..###..",
    ],
    "help": [
        ".####",
        "#...#",
        "....#",
        "...##",
        "..#..",
        ".....",
        "..#..",
    ],
    "context-menu": [
        "#####",
        ".....",
        "#####",
        ".....",
        "#####",
    ],
    "text": [
        "###",
        ".#.",
        ".#.",
        ".#.",
        "###",
    ],
    "vertical-text": [
        "#.....#",
        "#######",
        "#.....#",
    ],
    "crosshair": [
        "..#..",
        "..#..",
        "#####",
        "..#..",
        "..#..",
    ],
    "move": [
        "...#...",
        "..###..",
        "...#...",
        "#######",
        "...#...",
        "..###..",
        "...#...",
    ],
    "grab": [
        ".##.##.",
        ".##.##.",
        ".##.##.",
        "#######",
        "#######",
        ".#####.",
    ],
    "grabbing": [
        ".####.",
        "######",
        "######",
        "######",
        ".####.",
    ],
    "not-allowed": [
        ".####..",
        "####..#",
        "###..##",
        "##..###",
        "#..####",
        "..#####",
        ".#####.",
    ],
    "wait": [
        "#####",
        "#####",
        ".###.",
        "..#..",
        ".###.",
        "#####",
        "#####",
    ],
}

TIP_CORNER = {"default", "progress", "help", "context-menu"}
TIP_CELL = {"pointer": (1, 0)}

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

VARIANTS = {
    "pixel-dark": ("Pixel-Dark-xcursor", "Pixel cursor, cube and corner tick, dark variant", (0, 0, 0), (255, 255, 255)),
    "pixel-light": ("Pixel-Light-xcursor", "Pixel cursor, cube and corner tick, light variant", (255, 255, 255), (0, 0, 0)),
}

def masks(grid):
    height = len(grid)
    width = len(grid[0])
    shape = {(x, y) for y in range(height) for x in range(width) if grid[y][x] != "."}
    return shape, width, height

def cell_size(nominal):
    return max(1, (nominal + 4) // 8)

def render(name, grid, nominal, fill, contrast):
    shape, width, height = masks(grid)
    cell = cell_size(nominal)
    pixels = {(x * cell + dx, y * cell + dy) for x, y in shape for dy in range(cell) for dx in range(cell)}
    min_x = min(p[0] for p in pixels)
    min_y = min(p[1] for p in pixels)
    max_x = max(p[0] for p in pixels)
    max_y = max(p[1] for p in pixels)
    ink_w = max_x - min_x + 3
    ink_h = max_y - min_y + 3
    if ink_w > nominal or ink_h > nominal:
        raise SystemExit(f"{name}: {ink_w}x{ink_h} ink does not fit nominal {nominal}")
    origin_x = (nominal - ink_w) // 2 - min_x + 1
    origin_y = (nominal - ink_h) // 2 - min_y + 1
    buffer = bytearray(nominal * nominal * 4)
    painted = set()
    for py in range(min_y - 1, max_y + 2):
        for px in range(min_x - 1, max_x + 2):
            if (px, py) in pixels:
                color = fill
            elif any((px + dx, py + dy) in pixels for dy in (-1, 0, 1) for dx in (-1, 0, 1)):
                color = contrast
            else:
                continue
            offset = ((py + origin_y) * nominal + px + origin_x) * 4
            buffer[offset : offset + 4] = bytes(color) + b"\xff"
            painted.add((px + origin_x, py + origin_y))
    on_ink = True
    if name in TIP_CELL:
        cell_x, cell_y = TIP_CELL[name]
        hotspot = (origin_x + cell_x * cell + 1, origin_y + cell_y * cell - 1)
    elif name in TIP_CORNER:
        hotspot = min(painted, key=lambda point: (point[1], point[0]))
    else:
        on_ink = False
        hotspot = (
            origin_x + min_x - 1 + (ink_w - 1) // 2,
            origin_y + min_y - 1 + (ink_h - 1) // 2,
        )
    hotspot_x, hotspot_y = hotspot
    if not (0 <= hotspot_x < nominal and 0 <= hotspot_y < nominal):
        raise SystemExit(f"{name}: hotspot {hotspot} outside nominal {nominal}")
    offset = (hotspot_y * nominal + hotspot_x) * 4
    if on_ink and buffer[offset + 3] == 0:
        raise SystemExit(f"{name}: hotspot {hotspot} is transparent at nominal {nominal}")
    return nominal, hotspot_x, hotspot_y, bytes(buffer)

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
                size, x, y, pixels = render(art, grid, nominal, fill, contrast)
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
