#!/usr/bin/env bash
set -euo pipefail

mode=$1
theme_dir=$(realpath "$2")
out=$(realpath -m "$3")
script_dir=$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
stamp=${SOURCE_DATE_EPOCH:-0}
work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT

cd "$theme_dir"

xcursor() {
  python3 "$script_dir/build-xcursor.py" "$theme_dir" "$out"
  touch -h -d "@$stamp" "$out"/share/icons/*/index.theme "$out"/share/icons/*/cursors/*
}

hyprcursor() {
  local name src cursor target dir idx size delay file
  name=$(jq -r .hyprcursor.name theme.json)
  src=$work/src
  mkdir -p "$src/hyprcursors"

  {
    printf 'name = %s\n' "$name"
    printf 'description = %s\n' "$(jq -r .hyprcursor.description theme.json)"
    printf 'version = %s\n' "$(jq -r .hyprcursor.version theme.json)"
    printf 'cursors_directory = hyprcursors\n'
  } >"$src/manifest.hl"

  while read -r cursor target; do
    dir=$src/hyprcursors/$cursor
    mkdir -p "$dir"
    {
      printf 'resize_algorithm = %s\n' "$(jq -r .hyprcursor.resizeAlgorithm theme.json)"
      jq -r --arg c "$target" '
        .cursors[$c] as $f
        | ($f | map(.size) | max) as $max
        | ($f | map(select(.size == $max)) | .[0]) as $big
        | "hotspot_x = \($big.x / $big.size)",
          "hotspot_y = \($big.y / $big.size)"' theme.json
      idx=0
      while IFS=$'\t' read -r size delay file; do
        cp "$theme_dir/$file" "$dir/${size}-${idx}.png"
        printf 'define_size = %s, %s-%s.png, %s\n' "$size" "$size" "$idx" "$delay"
        idx=$((idx + 1))
      done < <(jq -r --arg c "$target" '.cursors[$c][] | "\(.size)\t\(.delay)\t\(.file)"' theme.json)
      touch -d "@$stamp" "$dir"/*
    } >"$dir/meta.hl"
    touch -d "@$stamp" "$dir/meta.hl"
  done < <(
    jq -r '.cursors | to_entries[] | "\(.key) \(.key)"' theme.json
    jq -r '.aliases | to_entries[] | "\(.key) \(.value)"' theme.json
  )
  touch -d "@$stamp" "$src/manifest.hl"

  mkdir -p "$work/hlcs"
  hyprcursor-util --create "$src" --output "$work/hlcs" >/dev/null
  mkdir -p "$out/share/icons/$name"
  cp -r "$work/hlcs/theme_$name/hyprcursors" "$out/share/icons/$name/"
  cp "$work/hlcs/theme_$name/manifest.hl" "$out/share/icons/$name/manifest.hl"
  find "$out/share/icons/$name" -exec touch -h -d "@$stamp" {} +
}

case $mode in
xcursor) xcursor ;;
hyprcursor) hyprcursor ;;
*)
  echo "unknown mode: $mode" >&2
  exit 1
  ;;
esac
