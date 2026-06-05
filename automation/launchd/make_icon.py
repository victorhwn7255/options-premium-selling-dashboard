#!/usr/bin/env python3
"""Generate AppIcon.icns for Theta Harvest.app.

Renders the brand mark (matches assets/favicon.svg): a cream theta on a terracotta
rounded square, at every macOS icon size, then packs them into an .icns via iconutil.

Usage:  make_icon.py <output_icns_path>
Requires Pillow (present in the framework python3 the automation already uses).
"""
import os
import shutil
import subprocess
import sys
import tempfile

from PIL import Image, ImageDraw, ImageFont

TERRACOTTA = (196, 123, 90, 255)   # #C47B5A  — brand primary
CREAM = (250, 247, 244, 255)       # #FAF7F4  — brand cream
GLYPH = "θ"                    # θ
CORNER = 0.2234                     # 28/128, from favicon.svg
GLYPH_HEIGHT_FRAC = 0.56           # θ height as a fraction of the tile

# Mono first (matches the favicon's mono θ); the rest are Unicode-complete fallbacks.
FONT_CANDIDATES = [
    ("/System/Library/Fonts/Menlo.ttc", 0),
    ("/System/Library/Fonts/Supplemental/Arial Unicode.ttf", 0),
    ("/System/Library/Fonts/Helvetica.ttc", 0),
]


def load_font(px: int) -> ImageFont.FreeTypeFont:
    for path, idx in FONT_CANDIDATES:
        if not os.path.exists(path):
            continue
        try:
            font = ImageFont.truetype(path, px, index=idx)
            if font.getbbox(GLYPH):  # glyph present and non-empty
                return font
        except Exception:
            continue
    raise SystemExit("make_icon: no system font with a theta glyph found")


def render(size: int) -> Image.Image:
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle(
        [0, 0, size - 1, size - 1], radius=round(size * CORNER), fill=TERRACOTTA
    )

    # Size the font so the rendered theta is GLYPH_HEIGHT_FRAC of the tile, then center
    # it precisely using its actual bounding box (font metrics alone are not centered).
    px = size
    font = load_font(px)
    _, top, _, bottom = draw.textbbox((0, 0), GLYPH, font=font)
    glyph_h = (bottom - top) or 1
    px = max(8, round(px * (size * GLYPH_HEIGHT_FRAC) / glyph_h))
    font = load_font(px)

    left, top, right, bottom = draw.textbbox((0, 0), GLYPH, font=font)
    x = (size - (right - left)) / 2 - left
    y = (size - (bottom - top)) / 2 - top
    draw.text((x, y), GLYPH, font=font, fill=CREAM)
    return img


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("usage: make_icon.py <output_icns_path>")
    out = sys.argv[1]

    # iconset name -> pixel size (each unique size rendered once)
    layout = {
        16: ["icon_16x16"],
        32: ["icon_16x16@2x", "icon_32x32"],
        64: ["icon_32x32@2x"],
        128: ["icon_128x128"],
        256: ["icon_128x128@2x", "icon_256x256"],
        512: ["icon_256x256@2x", "icon_512x512"],
        1024: ["icon_512x512@2x"],
    }

    tmp = tempfile.mkdtemp()
    try:
        iconset = os.path.join(tmp, "AppIcon.iconset")
        os.makedirs(iconset)
        for px, names in layout.items():
            tile = render(px)
            for name in names:
                tile.save(os.path.join(iconset, f"{name}.png"))
        subprocess.run(["iconutil", "-c", "icns", iconset, "-o", out], check=True)
        print("make_icon: wrote", out)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
