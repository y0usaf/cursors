#!/usr/bin/env bash
set -euo pipefail

CURSORS_DIR="/home/y0usaf/Dev/cursors/raccoin/xcursor/cursors"
cd "$CURSORS_DIR"

# Symlinks to "default"
DEFAULT_LINKS=(
  arrow
  left_ptr
  pointer
  hand1
  hand2
  pointing_hand
  9d800788f1b08800ae810202380a0822
  e29285e634086352946a0e7090d73106
  text
  xterm
  ibeam
  help
  question_arrow
  whats_this
  left_ptr_help
  5c6cd98b3f3ebcb1f9c7f1c204630408
  d9ce0ab605698f320427677b458ad60b
  crosshair
  cross
  color-picker
  not-allowed
  circle
  crossed_circle
  03b6e0fcb3499374a867c041f52298f0
  all-scroll
  fleur
  size_all
  cell
  plus
  context-menu
  copy
  1081e37283d90000800003c07f3ef6bf
  6407b0e94181790501fd1e167b474872
  b66166c04f8c3109214a4fbd64a50fc8
  alias
  link
  3085a0e285430894940527032f8b26df
  640fb0e74195791501fd1ed57b41487f
  a2a266d0498c3104214a47bd64ab0fc8
  dnd-move
  move
  closedhand
  grabbing
  dnd-copy
  dnd-none
  4498f0e0c1937ffe01fd06f973665830
  9081237383d90e509aa00f00170e968f
  fcf21c00b30f7e3f83fe0dfd12e71cff
  dnd-no-drop
  no-drop
  forbidden
  openhand
  grab
  pencil
  draft
  pirate
  right_ptr
  center_ptr
  vertical-text
  zoom-in
  zoom-out
  size_hor
  col-resize
  e-resize
  w-resize
  h_double_arrow
  sb_h_double_arrow
  split_h
  size_ver
  row-resize
  n-resize
  s-resize
  v_double_arrow
  sb_v_double_arrow
  00008160000006810000408080010102
  size_bdiag
  nesw-resize
  size_fdiag
  nwse-resize
  top_left_corner
  nw-resize
  ul_angle
  top_right_corner
  ne-resize
  ur_angle
  bottom_left_corner
  sw-resize
  ll_angle
  bottom_right_corner
  se-resize
  lr_angle
  top_side
  bottom_side
  left_side
  left-arrow
  right_side
  right-arrow
  up-arrow
  down-arrow
  x-cursor
  wayland-cursor
  split_v
)

for link in "${DEFAULT_LINKS[@]}"; do
  ln -sf default "$link"
done

# Symlinks to "progress"
PROGRESS_LINKS=(
  half-busy
  left_ptr_watch
  00000000000000020006000e7e9ffc3f
  08e8e1c95fe2fc01f976f1e063a24ccd
  3ecb610c1bf2410f44200f48c40d3599
)

for link in "${PROGRESS_LINKS[@]}"; do
  ln -sf progress "$link"
done

# Symlinks to "wait"
WAIT_LINKS=(
  watch
)

for link in "${WAIT_LINKS[@]}"; do
  ln -sf wait "$link"
done

echo "Created symlinks successfully."
