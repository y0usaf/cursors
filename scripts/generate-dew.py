#!/usr/bin/env python3
import importlib.util
import json
import math
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
THEMES = ROOT / "themes"
NOMINALS = [32, 40, 48, 64]
DELAY = 60
SPIN_FRAMES = 8

VARIANTS = {
    "dew-dark": ("Dew-Dark-xcursor", "DEW liquid-glass cursor, pale glass for a dark desktop", dict(
        tint="#DCE2FF", rim="#FFFFFF", edge="#0D0E16", accent="#9AA6FF", warn="#FF7A70",
        shadow=0.30, hair=0.60, body=0.20, dim=0.45)),
    "dew-light": ("Dew-Light-xcursor", "DEW liquid-glass cursor, slate glass for a light desktop", dict(
        tint="#3A3E58", rim="#FFFFFF", edge="#2A2D42", accent="#5D68B8", warn="#D44E46",
        shadow=0.22, hair=0.75, body=0.16, dim=0.60)),
}
LIGHT = np.array([-0.55, -0.83])


def circle(x, y, cx, cy, r):
    return np.hypot(x - cx, y - cy) - r


def capsule(x, y, ax, ay, bx, by, r):
    px, py, bax, bay = x - ax, y - ay, bx - ax, by - ay
    h = np.clip((px * bax + py * bay) / (bax * bax + bay * bay), 0, 1)
    return np.hypot(px - bax * h, py - bay * h) - r


def polygon(x, y, pts, r=0.0):
    pts = [(float(a), float(b)) for a, b in pts]
    d = (x - pts[0][0]) ** 2 + (y - pts[0][1]) ** 2
    s = np.ones_like(x)
    for i in range(len(pts)):
        (vix, viy), (vjx, vjy) = pts[i], pts[i - 1]
        ex, ey = vjx - vix, vjy - viy
        wx, wy = x - vix, y - viy
        h = np.clip((wx * ex + wy * ey) / (ex * ex + ey * ey), 0, 1)
        bx, by = wx - ex * h, wy - ey * h
        d = np.minimum(d, bx * bx + by * by)
        c1, c2, c3 = y >= viy, y < vjy, ex * wy > ey * wx
        s = np.where((c1 & c2 & c3) | (~c1 & ~c2 & ~c3), -s, s)
    return s * np.sqrt(d) - r


def inset(pts, r):
    cx = sum(p[0] for p in pts) / len(pts)
    cy = sum(p[1] for p in pts) / len(pts)
    out = []
    for px, py in pts:
        dx, dy = px - cx, py - cy
        length = math.hypot(dx, dy) or 1
        out.append((px - dx / length * r * 1.4, py - dy / length * r * 1.4))
    return out


def smin(a, b, k):
    if k <= 0:
        return np.minimum(a, b)
    h = np.clip(0.5 + 0.5 * (b - a) / k, 0, 1)
    return b * (1 - h) + a * h - k * h * (1 - h)


def union(ds, k):
    d = ds[0]
    for e in ds[1:]:
        d = smin(d, e, k)
    return d


def rot(x, y, cx, cy, deg):
    a = math.radians(deg)
    dx, dy = x - cx, y - cy
    return cx + dx * math.cos(a) + dy * math.sin(a), cy - dx * math.sin(a) + dy * math.cos(a)


def head(x, y, tipx, tipy, dirx, diry, w=5.6, length=6.4, r=0.9):
    nx, ny = -diry, dirx
    bx, by = tipx - dirx * length, tipy - diry * length
    pts = [(tipx, tipy), (bx + nx * w, by + ny * w), (bx - nx * w, by - ny * w)]
    return polygon(x, y, inset(pts, r), r)


def double_arrow(x, y, k, half=12.5):
    shaft = capsule(x, y, 16, 16 - half + 5, 16, 16 + half - 5, 1.5)
    return union([shaft, head(x, y, 16, 16 - half, 0, -1), head(x, y, 16, 16 + half, 0, 1)], k)


def spinner(x, y, cx, cy, radius, t, frame):
    ang = 2 * math.pi * frame / SPIN_FRAMES
    track = np.abs(np.hypot(x - cx, y - cy) - radius) - t * 0.45
    drop = circle(x, y, cx + radius * math.sin(ang), cy - radius * math.cos(ang), t * 1.25)
    tails = [circle(x, y, cx + radius * math.sin(ang - s), cy - radius * math.cos(ang - s),
                    t * (1.05 - s * 0.55)) for s in (0.35, 0.7, 1.0)]
    return track, union([drop] + tails, t * 1.2)


def arrow(x, y, k):
    tip = polygon(x, y, inset([(4, 2.5), (4, 24.5), (20.5, 18)], 1.0), 1.0)
    tail = capsule(x, y, 10.5, 19, 14.8, 27.5, 2.6)
    return union([tip, tail], k * 1.4)


def badge(x, y, d, cx=24.5, cy=24.5, r=7.0):
    return np.maximum(d, -circle(x, y, cx, cy, r))


ARROW_TIP = (4.6, 3.6)
CENTRE = (16, 16)


def geometry(name, x, y, k, frame=0):
    if name == "default":
        return arrow(x, y, k), None, ARROW_TIP, False
    if name == "progress":
        track, drop = spinner(x, y, 24.5, 24.5, 4.2, 1.3, frame)
        return np.minimum(badge(x, y, arrow(x, y, k)), track), drop, ARROW_TIP, False
    if name == "help":
        hook = np.abs(np.hypot(x - 24.5, y - 21.6) - 2.7) - 1.1
        hook = np.where((y > 21.6) & (x < 24.5), 1e3, hook)
        stem = capsule(x, y, 25.2, 24.2, 24.5, 25.6, 1.1)
        dot = circle(x, y, 24.5, 28.6, 1.3)
        return badge(x, y, arrow(x, y, k)), np.minimum(np.minimum(hook, stem), dot), ARROW_TIP, False
    if name == "context-menu":
        bars = [capsule(x, y, 21.0, cy, 28.0, cy, 1.05) for cy in (20.6, 24.5, 28.4)]
        return badge(x, y, arrow(x, y, k)), union(bars, 0), ARROW_TIP, False
    if name == "wait":
        track, drop = spinner(x, y, 16, 16, 10, 2.1, frame)
        return track, drop, CENTRE, False
    if name in ("text", "vertical-text"):
        if name == "vertical-text":
            x, y = rot(x, y, 16, 16, 90)
        stem = capsule(x, y, 16, 8.5, 16, 23.5, 1.25)
        caps = [capsule(x, y, 11.2, 5.8, 15.0, 6.6, 1.15), capsule(x, y, 20.8, 5.8, 17.0, 6.6, 1.15),
                capsule(x, y, 11.2, 26.2, 15.0, 25.4, 1.15), capsule(x, y, 20.8, 26.2, 17.0, 25.4, 1.15)]
        return union([stem] + caps, 1.4 + k * 0.4), None, CENTRE, False
    if name == "pointer":
        kk = max(k, 0.6)
        index = capsule(x, y, 12.2, 4.6, 12.2, 17, 2.55)
        fingers = union([capsule(x, y, 16.9, 12.4, 16.9, 18, 2.35),
                         capsule(x, y, 21.3, 13.6, 21.3, 19, 2.25),
                         capsule(x, y, 25.4, 15.2, 25.4, 20.5, 2.05)], kk * 0.35)
        d = union([index, fingers], kk * 0.45)
        d = union([d, capsule(x, y, 13.5, 21.5, 22.5, 22.5, 6.2)], kk * 1.2)
        d = union([d, capsule(x, y, 5.6, 16.8, 10.6, 23.2, 2.4)], kk * 1.0)
        return np.maximum(d, y - 29.5), None, (12.2, 2.2), False
    if name == "grab":
        kk = max(k, 0.6)
        fingers = union([capsule(x, y, 11.0, 7.4, 11.0, 17, 2.25),
                         capsule(x, y, 15.4, 5.2, 15.4, 17, 2.35),
                         capsule(x, y, 19.8, 6.0, 19.8, 17, 2.3),
                         capsule(x, y, 24.0, 8.6, 24.0, 18, 2.05)], kk * 0.35)
        d = union([fingers, capsule(x, y, 13.2, 21.0, 21.6, 21.6, 6.0)], kk * 1.2)
        d = union([d, capsule(x, y, 5.2, 14.6, 9.8, 21.6, 2.3)], kk * 1.0)
        return np.maximum(d, y - 29.0), None, CENTRE, False
    if name == "grabbing":
        kk = max(k, 0.6)
        knuckles = union([circle(x, y, cx, 12.8, 2.55) for cx in (11.4, 15.6, 19.8, 23.6)], kk * 0.35)
        d = union([knuckles, capsule(x, y, 12.6, 18.6, 21.8, 19.0, 6.0)], kk * 1.2)
        d = union([d, capsule(x, y, 7.0, 16.4, 11.4, 21.0, 2.3)], kk * 1.0)
        return np.maximum(d, y - 27.0), None, CENTRE, False
    if name in ("ns-resize", "ew-resize", "nwse-resize", "nesw-resize"):
        deg = {"ns-resize": 0, "ew-resize": 90, "nwse-resize": -45, "nesw-resize": 45}[name]
        rx, ry = rot(x, y, 16, 16, deg)
        return double_arrow(rx, ry, k, 12.5 if deg % 90 == 0 else 13.5), None, CENTRE, False
    if name == "move":
        ds = [capsule(x, y, 16, 8, 16, 24, 1.5), capsule(x, y, 8, 16, 24, 16, 1.5)]
        for dx, dy in ((0, -1), (0, 1), (-1, 0), (1, 0)):
            ds.append(head(x, y, 16 + dx * 13.5, 16 + dy * 13.5, dx, dy, w=4.6, length=5.4))
        return union(ds, k), None, CENTRE, False
    if name == "crosshair":
        ds = [capsule(x, y, 16, 3.5, 16, 12.2, 1.05), capsule(x, y, 16, 19.8, 16, 28.5, 1.05),
              capsule(x, y, 3.5, 16, 12.2, 16, 1.05), capsule(x, y, 19.8, 16, 28.5, 16, 1.05)]
        return union(ds, 0), circle(x, y, 16, 16, 1.35), CENTRE, False
    if name == "not-allowed":
        ring = np.abs(np.hypot(x - 16, y - 16) - 10.2) - 2.1
        slash = np.maximum(capsule(x, y, 9.4, 9.4, 22.6, 22.6, 2.0), circle(x, y, 16, 16, 10.8))
        return union([ring, slash], k * 0.8), None, CENTRE, True
    raise KeyError(name)


SHAPES = {
    "default": 1, "progress": SPIN_FRAMES, "help": 1, "context-menu": 1, "wait": SPIN_FRAMES,
    "text": 1, "vertical-text": 1, "pointer": 1, "grab": 1, "grabbing": 1, "ns-resize": 1,
    "ew-resize": 1, "nwse-resize": 1, "nesw-resize": 1, "move": 1, "crosshair": 1,
    "not-allowed": 1,
}

RESIZE = {
    "ew-resize": "e-resize w-resize col-resize sb_h_double_arrow h_double_arrow left_side right_side size_hor split_h left-arrow right-arrow",
    "ns-resize": "n-resize s-resize row-resize sb_v_double_arrow v_double_arrow top_side bottom_side size_ver split_v up-arrow down-arrow",
    "nwse-resize": "nw-resize se-resize top_left_corner bottom_right_corner ul_angle lr_angle fd_double_arrow size_fdiag",
    "nesw-resize": "ne-resize sw-resize top_right_corner bottom_left_corner ur_angle ll_angle bd_double_arrow size_bdiag",
}


def field(name, size, k, frame):
    g = (np.arange(size) + 0.5) * (32.0 / size)
    x, y = np.meshgrid(g, g)
    d, acc, hs, warn = geometry(name, x, y, k, frame)
    per = 32.0 / size
    return d / per, (None if acc is None else acc / per), (hs[0] / per, hs[1] / per), warn


def cov(d):
    return np.clip(0.5 - d, 0, 1)


def gauss_blur(a, r):
    k = np.arange(-int(3 * r), int(3 * r) + 1)
    w = np.exp(-(k ** 2) / (2 * r * r))
    w /= w.sum()
    pad = len(k) // 2
    b = np.pad(a, ((pad, pad), (0, 0)), mode="edge")
    a = sum(w[i] * b[i:i + a.shape[0]] for i in range(len(k)))
    b = np.pad(a, ((0, 0), (pad, pad)), mode="edge")
    return sum(w[i] * b[:, i:i + a.shape[1]] for i in range(len(k)))


def shift(a, dx, dy):
    out = np.zeros_like(a)
    h, w = a.shape
    dx, dy = int(round(dx)), int(round(dy))
    ys, yd = (slice(0, h - dy), slice(dy, h)) if dy >= 0 else (slice(-dy, h), slice(0, h + dy))
    xs, xd = (slice(0, w - dx), slice(dx, w)) if dx >= 0 else (slice(-dx, w), slice(0, w + dx))
    out[yd, xd] = a[ys, xs]
    return out


def over(dst_rgb, dst_a, src_rgb, src_a):
    return src_rgb * src_a[..., None] + dst_rgb * (1 - src_a)[..., None], src_a + dst_a * (1 - src_a)


def hexc(h):
    h = h.lstrip("#")
    return np.array([int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)])


def gradient(d):
    gy, gx = np.gradient(d)
    length = np.hypot(gx, gy) + 1e-6
    return gx / length, gy / length


def render(name, palette, size, frame):
    p = {key: hexc(value) for key, value in palette.items() if isinstance(value, str)}
    d, acc, hs, warn = field(name, size, 2.2, frame)
    u = size / 32
    if acc is not None:
        d = smin(d, acc, 1.2 * u) if name != "crosshair" else np.minimum(d, acc)
    depth = np.clip(-d / (4.0 * u), 0, 1)
    height = np.sqrt(np.clip(1 - (1 - depth) ** 2, 0, 1))
    gy, gx = np.gradient(height)
    body = cov(d)
    nx, ny = gradient(d)
    rim = np.clip(1 - np.abs(d + 1.0 * u) / (1.3 * u), 0, 1) * body
    facing = np.clip(nx * LIGHT[0] + ny * LIGHT[1], -1, 1)
    shape = d.shape + (3,)
    rgb, a = np.zeros(shape), np.zeros(d.shape)
    sh = gauss_blur(shift(body, 0.5 * u, 1.6 * u), 1.6 * u) * palette["shadow"]
    rgb, a = over(rgb, a, np.zeros(shape), sh)
    hair = cov(np.abs(d + 0.25) - 0.55) * palette["hair"]
    rgb, a = over(rgb, a, np.broadcast_to(p["edge"], shape), hair)
    tint = p["warn"] if warn else p["tint"]
    rgb, a = over(rgb, a, np.broadcast_to(tint, shape), body * (palette["body"] + 0.16 * (1 - height)))
    rgb, a = over(rgb, a, np.broadcast_to(p["rim"], shape), rim * np.clip(facing, 0, 1) * 0.95)
    rgb, a = over(rgb, a, np.broadcast_to(p["edge"], shape), rim * np.clip(-facing, 0, 1) * palette["dim"])
    spec = np.clip((gx * -LIGHT[0] + gy * -LIGHT[1]) * 2.2 * u - 0.35, 0, 1) * (height > 0.25) * body
    rgb, a = over(rgb, a, np.broadcast_to(p["rim"], shape), spec * 0.6)
    if acc is not None and name != "crosshair":
        rgb, a = over(rgb, a, np.broadcast_to(p["accent"], shape), cov(acc) * 0.55)
    if name == "crosshair":
        rgb, a = over(rgb, a, np.broadcast_to(p["rim"], shape), cov(acc) * 0.9)
    pixels = np.dstack([np.clip(rgb, 0, 1), np.clip(a, 0, 1)])
    pixels = (pixels * 255 + 0.5).astype(np.uint8)
    pixels[..., :3] = np.minimum(pixels[..., :3], pixels[..., 3:4])
    hx, hy = int(math.floor(hs[0])), int(math.floor(hs[1]))
    if not (0 <= hx < size and 0 <= hy < size):
        raise SystemExit(f"{name}: hotspot {hx},{hy} outside nominal {size}")
    return hx, hy, pixels.tobytes()


def load_pixel():
    spec = importlib.util.spec_from_file_location("pixel", ROOT / "scripts" / "generate-pixel.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def aliases():
    pixel = load_pixel()
    target = dict(pixel.NAME_ART)
    for shape, names in RESIZE.items():
        for alias in names.split():
            target[alias] = shape
    names = set(target)
    for meta_path in sorted(THEMES.glob("*/theme.json")):
        if meta_path.parent.name.startswith(("pixel-", "dew-")):
            continue
        meta = json.loads(meta_path.read_text())
        names.update(meta.get("cursors", {}))
        names.update(meta.get("aliases", {}))
    out = {}
    for name in sorted(names):
        if name in SHAPES:
            continue
        shape = target.get(name, "default")
        out[name] = shape if shape in SHAPES else "default"
    return out


def main():
    pixel = load_pixel()
    links = aliases()
    for slug, (name, comment, palette) in VARIANTS.items():
        theme_dir = THEMES / slug
        theme_dir.mkdir(parents=True, exist_ok=True)
        for stale in theme_dir.glob("*.png"):
            stale.unlink()
        cursors = {}
        for shape, frames in SHAPES.items():
            entries = []
            for size in NOMINALS:
                for frame in range(frames):
                    x, y, pixels = render(shape, palette, size, frame)
                    file = f"{shape}-{size}.png" if frames == 1 else f"{shape}-{size}-{frame}.png"
                    pixel.write_png(theme_dir / file, size, size, pixels)
                    entries.append({"size": size, "x": x, "y": y, "delay": DELAY, "file": file})
            cursors[shape] = entries
        meta = {"name": name, "comment": comment, "cursors": cursors, "aliases": links}
        (theme_dir / "theme.json").write_text(json.dumps(meta, indent=2, sort_keys=True) + "\n")
        print(f"{slug}: {len(cursors)} cursors, {len(links)} aliases")


if __name__ == "__main__":
    sys.exit(main())
