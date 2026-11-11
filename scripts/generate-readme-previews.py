#!/usr/bin/env python3
"""Generate README cursor previews from themes/<id>/theme.json.

Each theme's contact sheet embeds the largest PNG frame of up to twelve
cursors straight from the committed sources. The README section between
<!-- previews:start --> and <!-- previews:end --> is replaced in place.
"""

import base64
import html
import json
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"
PREVIEW_DIR = ROOT / "docs" / "previews"

START = "<!-- previews:start -->"
END = "<!-- previews:end -->"

PREFERRED_CURSORS = [
    "default",
    "pointer",
    "text",
    "wait",
    "progress",
    "crosshair",
    "not-allowed",
    "openhand",
    "size_hor",
    "size_ver",
    "copy",
    "zoom-in",
]

FAMILY_ORDER = {"deepin": 0, "earendil": 1, "popucom": 2, "raccoin": 3, "ssb": 4}
VARIANT_ORDER = {
    ("deepin", "dark"): 0,
    ("deepin", "light"): 1,
    ("earendil", "dark"): 0,
    ("earendil", "light"): 1,
    ("raccoin", "default"): 0,
    ("raccoin", "dark"): 1,
    ("raccoin", "bw"): 2,
    ("raccoin", "black-outline"): 3,
}


def discover():
    themes = []
    for theme_dir in sorted((ROOT / "themes").iterdir()):
        meta_path = theme_dir / "theme.json"
        if not meta_path.is_file():
            continue
        meta = json.loads(meta_path.read_text())
        themes.append((theme_dir.name, meta))
    themes.sort(key=lambda item: theme_sort_key(item[0]))
    return themes


def theme_sort_key(slug):
    family, _, variant = slug.partition("-")
    return (FAMILY_ORDER.get(family, 99), VARIANT_ORDER.get((family, variant), 99), slug)


def preview_frames(meta, theme_dir):
    cursors = meta["cursors"]
    names = [name for name in PREFERRED_CURSORS if name in cursors]
    names += [name for name in sorted(cursors) if name not in names]
    frames = []
    for name in names[:12]:
        frame = max(cursors[name], key=lambda f: f["size"])
        frames.append((name, (theme_dir / frame["file"]).read_bytes()))
    return frames


def png_dimensions(data):
    if data[:8] != b"\x89PNG\r\n\x1a\n" or data[12:16] != b"IHDR":
        return (64, 64)
    return struct.unpack(">II", data[16:24])


def generate_preview(title, frames, out_path):
    cols = min(4, max(1, len(frames)))
    rows = (len(frames) + cols - 1) // cols
    tile_w = 136
    tile_h = 124
    icon = 64
    pad = 24
    header_h = 52
    width = cols * tile_w + pad * 2
    height = header_h + rows * tile_h + pad

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        "<style>",
        ".bg{fill:#f6f8fa}.card{fill:#fff;stroke:#d0d7de;stroke-width:1}.title{font:600 20px sans-serif;fill:#24292f}.label{font:12px sans-serif;fill:#57606a;text-anchor:middle}",
        "@media (prefers-color-scheme: dark){.bg{fill:#0d1117}.card{fill:#161b22;stroke:#30363d}.title{fill:#f0f6fc}.label{fill:#8b949e}}",
        "</style>",
        f'<rect class="bg" width="{width}" height="{height}" rx="16"/>',
        f'<text class="title" x="{pad}" y="34">{html.escape(title)}</text>',
    ]

    for i, (name, data) in enumerate(frames):
        col = i % cols
        row = i // cols
        x = pad + col * tile_w
        y = header_h + row * tile_h
        png_w, png_h = png_dimensions(data)
        href = "data:image/png;base64," + base64.b64encode(data).decode("ascii")
        parts.append(f'<rect class="card" x="{x}" y="{y}" width="112" height="102" rx="12"/>')
        parts.append(
            f'<image x="{x + 24}" y="{y + 14}" width="{icon}" height="{icon}" '
            f'viewBox="0 0 {png_w} {png_h}" preserveAspectRatio="xMidYMid meet" href="{href}"/>'
        )
        parts.append(f'<text class="label" x="{x + 56}" y="{y + 88}">{html.escape(name)}</text>')

    parts.append("</svg>\n")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(parts), encoding="utf-8")


def main():
    previews = []
    for slug, meta in discover():
        frames = preview_frames(meta, ROOT / "themes" / slug)
        if not frames:
            continue
        out = PREVIEW_DIR / f"{slug}.svg"
        generate_preview(meta["name"], frames, out)
        previews.append((slug, meta["name"], out.relative_to(ROOT)))

    lines = [START, "## Previews", "", "Generated with `scripts/generate-readme-previews.py`.", ""]
    for i in range(0, len(previews), 2):
        pair = previews[i : i + 2]
        lines.append("| " + " | ".join(name for _, name, _ in pair) + " |")
        lines.append("| --- | --- |")
        cells = [
            f'<img src="{path.as_posix()}" alt="{name} preview" width="360">'
            for _, name, path in pair
        ]
        if len(cells) == 1:
            cells.append("")
        lines.append("| " + " | ".join(cells) + " |")
        lines.append("")
    lines.append(END)

    text = README.read_text(encoding="utf-8")
    start = text.index(START)
    end = text.index(END) + len(END)
    README.write_text(text[:start] + "\n".join(lines) + text[end:], encoding="utf-8")


if __name__ == "__main__":
    main()
