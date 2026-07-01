# Deepin Minimal SVG Design System

Tiny Google_Cursor-style theming for the minimized Deepin SVG cursors.

## Source tokens

`src/*.svg` uses exact sentinel colours:

- `#00ff00` = `base` / inner cursor body (former black/default fill)
- `#0000ff` = `outline` / outer cursor contrast (former white fill/stroke)

Other colours are semantic accents (`danger`, `action`, `busy_base`,
`busy_highlight`, `success`, `warning`, `orange`) listed in `tokens.json`.

## Render themes

```sh
cd tmp/deepin-minimal-system
./render-all.sh
# or one at a time:
./render.sh black-inner-white-outer
./render.sh white-inner-black-outer
./render.sh red-inner-white-outer
./render.sh pastel-blue-inner-black-outer
```

Outputs go to `themes/<theme>/svg/`.

This is intentionally dependency-free shell + `sed`; no Python, Node, npm, or bitmap
renderer is needed.
