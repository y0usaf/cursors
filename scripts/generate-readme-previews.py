#!/usr/bin/env python3
"""Generate README cursor previews.

Stdlib-only by default, with optional `xcur2png` support when it is installed.

Input priority per theme:
  1. SVG sources: <theme>/svg/*.svg, <theme>/cursor.svg, <theme>/xcursor/cursor.svg
  2. PNG sources: <theme>/*.png, <theme>/xcursor/src/*.png
  3. Xcursor binaries: <theme>/xcursor/cursors/*

The generated previews are SVG contact sheets under docs/previews/, and the README
section between <!-- previews:start --> and <!-- previews:end --> is replaced.
"""

from __future__ import annotations

import argparse
import base64
import dataclasses
import html
import re
import shutil
import struct
import subprocess
import sys
import tempfile
import zlib
from pathlib import Path
from typing import Iterable

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

PREFERRED_PNG_PATTERNS = [
    "*dark*.png",
    "*bw*.png",
    "normal_0.png",
    "normal_1.png",
    "normal_2.png",
    "normal_3.png",
    "normal_4.png",
    "forbid_0.png",
    "forbid_1.png",
    "forbid_2.png",
    "forbid_3.png",
    "forbid_4.png",
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

SVG_OPEN_RE = re.compile(r"<svg\b(?P<attrs>[^>]*)>", re.IGNORECASE | re.DOTALL)
ATTR_RE = re.compile(r"([:\w-]+)\s*=\s*(['\"])(.*?)\2", re.DOTALL)
LENGTH_RE = re.compile(r"^\s*([0-9.]+)")
XC_IMAGE_TYPE = 0xFFFD0002


@dataclasses.dataclass(frozen=True)
class Source:
    kind: str  # svg | png | xcursor
    path: Path
    label: str


@dataclasses.dataclass(frozen=True)
class Theme:
    dir: Path
    slug: str
    title: str
    sources: list[Source]


def slug_to_title(slug: str) -> str:
    special = {"ssb": "SSB"}
    return " ".join(special.get(part, part.capitalize()) for part in slug.split("-"))


def read_theme_name(theme_dir: Path) -> str:
    index = theme_dir / "xcursor" / "index.theme"
    if index.exists():
        for line in index.read_text(encoding="utf-8", errors="replace").splitlines():
            if line.startswith("Name="):
                return line.split("=", 1)[1].strip()
    manifest = theme_dir / "hyprcursor" / "manifest.hl"
    if manifest.exists():
        for line in manifest.read_text(encoding="utf-8", errors="replace").splitlines():
            if line.startswith("name ="):
                return line.split("=", 1)[1].strip()
    return slug_to_title(theme_dir.name)


def ordered_by_preference(paths: Iterable[Path], preferred: Iterable[str]) -> list[Path]:
    by_stem = {p.stem: p for p in paths}
    ordered = [by_stem[name] for name in preferred if name in by_stem]
    ordered_set = set(ordered)
    for path in sorted(paths):
        if path not in ordered_set:
            ordered.append(path)
    return ordered


def svg_sources(theme_dir: Path) -> list[Source]:
    svg_dir = theme_dir / "svg"
    if svg_dir.is_dir():
        paths = ordered_by_preference(svg_dir.glob("*.svg"), PREFERRED_CURSORS)[:12]
        return [Source("svg", p, p.stem) for p in paths]

    for candidate in (theme_dir / "cursor.svg", theme_dir / "xcursor" / "cursor.svg"):
        if candidate.is_file():
            return [Source("svg", candidate, candidate.stem)]

    return []


def png_sources(theme_dir: Path) -> list[Source]:
    candidates: list[Path] = []
    for pattern in PREFERRED_PNG_PATTERNS:
        candidates.extend(theme_dir.glob(pattern))
        candidates.extend((theme_dir / "xcursor" / "src").glob(pattern))

    if not candidates:
        candidates.extend(theme_dir.glob("*.png"))
        candidates.extend((theme_dir / "xcursor" / "src").glob("*.png"))

    seen: set[Path] = set()
    paths: list[Path] = []
    for path in candidates:
        if path.is_file() and path not in seen:
            seen.add(path)
            paths.append(path)
        if len(paths) >= 12:
            break
    return [Source("png", p, p.stem) for p in paths]


def xcursor_sources(theme_dir: Path) -> list[Source]:
    cursor_dir = theme_dir / "xcursor" / "cursors"
    if not cursor_dir.is_dir():
        return []
    files = [p for p in cursor_dir.iterdir() if p.is_file() and not p.is_symlink()]
    paths = ordered_by_preference(files, PREFERRED_CURSORS)[:12]
    return [Source("xcursor", p, p.name) for p in paths]


def is_theme_dir(path: Path) -> bool:
    return (path / "xcursor").is_dir() or (path / "hyprcursor").is_dir()


def nested_theme_dirs(path: Path) -> list[Path]:
    return sorted(p for p in path.rglob("*") if p.is_dir() and is_theme_dir(p))


def theme_dirs(root: Path) -> list[Path]:
    ignored = {".git", "docs", "scripts", "themes"}
    dirs: list[Path] = []

    # New organized layout: themes/<family>/<variant>/.
    themes_root = root / "themes"
    if themes_root.is_dir():
        dirs.extend(nested_theme_dirs(themes_root))

    # Legacy top-level layouts kept while the repo is migrated family-by-family.
    for child in sorted(p for p in root.iterdir() if p.is_dir() and p.name not in ignored):
        # Popucom stores one theme per color below popucom/<color>/.
        if child.name == "popucom":
            dirs.extend(sorted(p for p in child.iterdir() if p.is_dir() and is_theme_dir(p)))
        elif is_theme_dir(child):
            dirs.append(child)
    return dirs


def theme_slug(root: Path, theme_dir: Path) -> str:
    rel = theme_dir.relative_to(root)
    parts = rel.parts[1:] if rel.parts and rel.parts[0] == "themes" else rel.parts
    return "-".join(parts)


def theme_sort_key(root: Path, theme_dir: Path) -> tuple[int, int, str]:
    slug = theme_slug(root, theme_dir)
    family, _, variant = slug.partition("-")
    return (FAMILY_ORDER.get(family, 99), VARIANT_ORDER.get((family, variant), 99), slug)


def discover_themes(root: Path) -> list[Theme]:
    themes: list[Theme] = []
    for theme_dir in sorted(theme_dirs(root), key=lambda path: theme_sort_key(root, path)):
        sources = svg_sources(theme_dir) or png_sources(theme_dir) or xcursor_sources(theme_dir)
        if not sources:
            continue
        slug = theme_slug(root, theme_dir)
        themes.append(Theme(theme_dir, slug, read_theme_name(theme_dir), sources))
    return themes


def parse_attrs(svg_text: str) -> dict[str, str]:
    match = SVG_OPEN_RE.search(svg_text)
    if not match:
        return {}
    return {m.group(1): m.group(3) for m in ATTR_RE.finditer(match.group("attrs"))}


def svg_inner(svg_text: str) -> str:
    match = SVG_OPEN_RE.search(svg_text)
    if not match:
        raise ValueError("missing <svg> root")
    end = svg_text.lower().rfind("</svg>")
    if end == -1:
        raise ValueError("missing </svg> root")
    return svg_text[match.end() : end].strip()


def parse_length(value: str | None, default: float) -> float:
    if not value:
        return default
    match = LENGTH_RE.match(value)
    return float(match.group(1)) if match else default


def view_box(attrs: dict[str, str]) -> str:
    if attrs.get("viewBox"):
        return attrs["viewBox"]
    width = parse_length(attrs.get("width"), 64)
    height = parse_length(attrs.get("height"), 64)
    return f"0 0 {width:g} {height:g}"


def namespace_svg_ids(svg_fragment: str, prefix: str) -> str:
    ids = re.findall(r'\bid\s*=\s*(["\'])(.*?)\1', svg_fragment)
    if not ids:
        return svg_fragment
    names = {name for _, name in ids if name}
    out = svg_fragment
    for name in sorted(names, key=len, reverse=True):
        escaped = re.escape(name)
        replacement = f"{prefix}-{name}"
        out = re.sub(rf'(\bid\s*=\s*(["\'])){escaped}(\2)', rf'\1{replacement}\3', out)
        out = re.sub(rf'url\(\s*#{escaped}\s*\)', f'url(#{replacement})', out)
        out = re.sub(rf'((?:href|xlink:href)\s*=\s*(["\']))#{escaped}(\2)', rf'\1#{replacement}\3', out)
        out = re.sub(rf'((?:begin|end)\s*=\s*(["\'])){escaped}([.;])', rf'\1{replacement}\3', out)
    return out


def png_dimensions(data: bytes) -> tuple[int, int]:
    if data[:8] != b"\x89PNG\r\n\x1a\n" or data[12:16] != b"IHDR":
        return (64, 64)
    return struct.unpack(">II", data[16:24])


def png_chunk(kind: bytes, data: bytes) -> bytes:
    return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)


def rgba_to_png(width: int, height: int, rgba: bytes) -> bytes:
    raw = b"".join(b"\x00" + rgba[y * width * 4 : (y + 1) * width * 4] for y in range(height))
    return (
        b"\x89PNG\r\n\x1a\n"
        + png_chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0))
        + png_chunk(b"IDAT", zlib.compress(raw, 9))
        + png_chunk(b"IEND", b"")
    )


def decode_xcursor_first_image(path: Path) -> tuple[int, int, bytes] | None:
    data = path.read_bytes()
    if len(data) < 16 or data[:4] != b"Xcur":
        return None
    _magic, _hlen, _version, ntoc = struct.unpack_from("<4sIII", data, 0)
    entries = []
    for i in range(ntoc):
        typ, subtype, pos = struct.unpack_from("<III", data, 16 + i * 12)
        if typ == XC_IMAGE_TYPE:
            entries.append((subtype, pos))
    if not entries:
        return None
    # Smallest size is enough for a README thumbnail.
    _subtype, pos = sorted(entries)[0]
    if pos + 36 > len(data):
        return None
    header, typ, _subtype, _version, width, height, _xhot, _yhot, _delay = struct.unpack_from("<IIIIIIIII", data, pos)
    if typ != XC_IMAGE_TYPE or width <= 0 or height <= 0 or pos + header + width * height * 4 > len(data):
        return None
    rgba = bytearray()
    off = pos + header
    for j in range(width * height):
        pixel, = struct.unpack_from("<I", data, off + j * 4)
        a = (pixel >> 24) & 0xFF
        r = (pixel >> 16) & 0xFF
        g = (pixel >> 8) & 0xFF
        b = pixel & 0xFF
        rgba.extend((r, g, b, a))
    return width, height, bytes(rgba)


def png_from_xcur2png(path: Path) -> bytes | None:
    exe = shutil.which("xcur2png")
    if not exe:
        return None
    with tempfile.TemporaryDirectory() as tmp:
        tmpdir = Path(tmp)
        proc = subprocess.run([exe, str(path)], cwd=tmpdir, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if proc.returncode != 0:
            return None
        pngs = sorted(tmpdir.glob("*.png"))
        return pngs[0].read_bytes() if pngs else None


def xcursor_to_png(path: Path) -> bytes | None:
    external = png_from_xcur2png(path)
    if external:
        return external
    decoded = decode_xcursor_first_image(path)
    if not decoded:
        return None
    width, height, rgba = decoded
    return rgba_to_png(width, height, rgba)


def image_href(data: bytes) -> str:
    return "data:image/png;base64," + base64.b64encode(data).decode("ascii")


def embedded_source(source: Source, x: int, y: int, size: int, prefix: str) -> str:
    if source.kind == "svg":
        text = source.path.read_text(encoding="utf-8", errors="replace")
        attrs = parse_attrs(text)
        inner = namespace_svg_ids(svg_inner(text), prefix)
        vb = html.escape(view_box(attrs), quote=True)
        return (
            f'<svg x="{x}" y="{y}" width="{size}" height="{size}" '
            f'viewBox="{vb}" preserveAspectRatio="xMidYMid meet">\n{inner}\n</svg>'
        )

    data = source.path.read_bytes() if source.kind == "png" else xcursor_to_png(source.path)
    if not data:
        return f'<text class="label" x="{x + size / 2:g}" y="{y + size / 2:g}">unavailable</text>'
    width, height = png_dimensions(data)
    href = image_href(data)
    return (
        f'<image x="{x}" y="{y}" width="{size}" height="{size}" '
        f'viewBox="0 0 {width} {height}" preserveAspectRatio="xMidYMid meet" href="{href}"/>'
    )


def generate_preview(theme: Theme, out_path: Path) -> None:
    cols = min(4, max(1, len(theme.sources)))
    rows = (len(theme.sources) + cols - 1) // cols
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
        f'<text class="title" x="{pad}" y="34">{html.escape(theme.title)}</text>',
    ]

    for i, source in enumerate(theme.sources):
        col = i % cols
        row = i // cols
        x = pad + col * tile_w
        y = header_h + row * tile_h
        parts.append(f'<rect class="card" x="{x}" y="{y}" width="112" height="102" rx="12"/>')
        parts.append(embedded_source(source, x + 24, y + 14, icon, f"{theme.slug}-{i}"))
        parts.append(f'<text class="label" x="{x + 56}" y="{y + 88}">{html.escape(source.label)}</text>')

    parts.append("</svg>\n")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(parts), encoding="utf-8")


def markdown_for(previews: Iterable[tuple[str, Path]]) -> str:
    rows = ["## Previews", "", "Generated with `scripts/generate-readme-previews.py`.", ""]
    items = list(previews)
    for i in range(0, len(items), 2):
        pair = items[i : i + 2]
        rows.append("| " + " | ".join(title for title, _ in pair) + (" |" if len(pair) == 2 else " | |"))
        rows.append("| " + " | ".join("---" for _ in pair) + (" |" if len(pair) == 2 else " | --- |"))
        rows.append(
            "| "
            + " | ".join(
                f'<img src="{path.as_posix()}" alt="{html.escape(title)} preview" width="360">'
                for title, path in pair
            )
            + (" |" if len(pair) == 2 else " | |")
        )
        rows.append("")
    return "\n".join(rows).rstrip() + "\n"


def update_readme(block: str) -> None:
    text = README.read_text(encoding="utf-8") if README.exists() else "# Cursors\n"
    replacement = f"{START}\n{block}{END}"
    if START in text and END in text:
        text = re.sub(re.escape(START) + r".*?" + re.escape(END), replacement, text, flags=re.DOTALL)
    else:
        if not text.endswith("\n"):
            text += "\n"
        text += "\n" + replacement + "\n"
    README.write_text(text, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="fail if generated previews/README would change")
    parser.add_argument("--no-readme", action="store_true", help="only generate docs/previews/*.svg")
    args = parser.parse_args()

    before: dict[Path, bytes | None] = {}
    watch = [README]
    if PREVIEW_DIR.exists():
        watch.extend(PREVIEW_DIR.glob("*.svg"))
    for path in watch:
        before[path] = path.read_bytes() if path.exists() else None

    themes = discover_themes(ROOT)
    previews: list[tuple[str, Path]] = []
    for theme in themes:
        out = PREVIEW_DIR / f"{theme.slug}.svg"
        generate_preview(theme, out)
        previews.append((theme.title, out.relative_to(ROOT)))

    if not args.no_readme:
        update_readme(markdown_for(previews))

    if args.check:
        after_paths = set(before)
        if PREVIEW_DIR.exists():
            after_paths.update(PREVIEW_DIR.glob("*.svg"))
        changed = []
        for path in sorted(after_paths):
            old = before.get(path)
            new = path.read_bytes() if path.exists() else None
            if old != new:
                changed.append(path.relative_to(ROOT))
        if changed:
            print("Generated files are out of date:", file=sys.stderr)
            for path in changed:
                print(f"  {path}", file=sys.stderr)
            return 1

    print(f"Generated {len(previews)} preview(s) in {PREVIEW_DIR.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
