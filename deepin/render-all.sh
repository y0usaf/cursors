#!/usr/bin/env sh
set -eu
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)

"$ROOT/render.sh" black-inner-white-outer
"$ROOT/render.sh" white-inner-black-outer
"$ROOT/render.sh" red-inner-white-outer
"$ROOT/render.sh" pastel-blue-inner-black-outer
