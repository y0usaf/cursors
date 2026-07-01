#!/usr/bin/env sh
set -eu

ROOT=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
SRC="$ROOT/src"
THEMES="$ROOT/themes"

usage() {
  cat <<'EOF'
Usage:
  ./render.sh <theme>
  ./render.sh all
  ./render.sh --list

Themes:
  black-inner-white-outer
  white-inner-black-outer
  red-inner-white-outer
  pastel-blue-inner-black-outer
EOF
}

set_palette() {
  case "$1" in
    black-inner-white-outer)
      BASE="#000000"; OUTLINE="#ffffff"
      DANGER="#fa1919"; ACTION="#1e82ff"; BUSY_BASE="#025ee8"; BUSY_HIGHLIGHT="#2ca7f8"
      SUCCESS="#32aa32"; WARNING="#ffc800"; ORANGE="#f67400"
      ;;
    white-inner-black-outer)
      BASE="#ffffff"; OUTLINE="#000000"
      DANGER="#fa1919"; ACTION="#1e82ff"; BUSY_BASE="#025ee8"; BUSY_HIGHLIGHT="#2ca7f8"
      SUCCESS="#32aa32"; WARNING="#ffc800"; ORANGE="#f67400"
      ;;
    red-inner-white-outer)
      BASE="#ff0000"; OUTLINE="#ffffff"
      DANGER="#ff0000"; ACTION="#1e82ff"; BUSY_BASE="#025ee8"; BUSY_HIGHLIGHT="#2ca7f8"
      SUCCESS="#32aa32"; WARNING="#ffc800"; ORANGE="#f67400"
      ;;
    pastel-blue-inner-black-outer)
      BASE="#a7c7e7"; OUTLINE="#000000"
      DANGER="#e84f68"; ACTION="#4aa3ff"; BUSY_BASE="#3d7dd8"; BUSY_HIGHLIGHT="#89d6ff"
      SUCCESS="#76c893"; WARNING="#ffd166"; ORANGE="#f4a261"
      ;;
    *)
      echo "Unknown theme: $1" >&2
      usage >&2
      exit 1
      ;;
  esac
}

render_one() {
  name="$1"
  set_palette "$name"
  out="$THEMES/$name/svg"
  rm -rf "$out"
  mkdir -p "$out"

  for svg in "$SRC"/*.svg; do
    [ -f "$svg" ] || continue
    sed \
      -e "s|#00ff00|$BASE|g" \
      -e "s|#0000ff|$OUTLINE|g" \
      -e "s|#fa1919|$DANGER|g" \
      -e "s|#1e82ff|$ACTION|g" \
      -e "s|#025ee8|$BUSY_BASE|g" \
      -e "s|#2ca7f8|$BUSY_HIGHLIGHT|g" \
      -e "s|#32aa32|$SUCCESS|g" \
      -e "s|#ffc800|$WARNING|g" \
      -e "s|#f67400|$ORANGE|g" \
      "$svg" > "$out/$(basename "$svg")"
  done

  printf '%s\n' "themes/$name/svg"
}

case "${1:-}" in
  ""|-h|--help)
    usage
    ;;
  --list)
    printf '%s\n' \
      black-inner-white-outer \
      white-inner-black-outer \
      red-inner-white-outer \
      pastel-blue-inner-black-outer
    ;;
  all)
    "$ROOT/render-all.sh"
    ;;
  *)
    render_one "$1"
    ;;
esac
