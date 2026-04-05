from PIL import Image
import os

SRC_DIR = "/home/y0usaf/Dev/cursors/raccoin"
OUT_DIR = "/home/y0usaf/Dev/cursors/raccoin/xcursor/src"
os.makedirs(OUT_DIR, exist_ok=True)

sources = {
    "default": os.path.join(SRC_DIR, "raccoin_default.png"),
    "progress": os.path.join(SRC_DIR, "raccoin_bw.png"),
    "wait": os.path.join(SRC_DIR, "raccoin_black_outline.png"),
}

sizes = [32, 48, 64, 96]

for name, path in sources.items():
    img = Image.open(path).convert("RGBA")
    print(f"Loaded {name}: {img.size} from {path}")
    for size in sizes:
        resized = img.resize((size, size), Image.NEAREST)
        out_path = os.path.join(OUT_DIR, f"{name}_{size}.png")
        resized.save(out_path)
        print(f"  Saved {out_path}")

print("Done upscaling.")
