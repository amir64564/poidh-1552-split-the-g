#!/usr/bin/env python3
"""Original poster for poidh #1552: splitting a G-clef on the G line.

The G-clef outline is adapted from Wikimedia Commons File:GClef.svg
(public domain, author っ, 27 April 2006). The poster composition,
typography, colour, and the split along the G line are original.
"""
from __future__ import annotations

import io
import random
from pathlib import Path

import cairosvg
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "proof"
OUT.mkdir(exist_ok=True)

W, H = 1600, 2000
CX = 760
G = 1020
S = 62

FONT_DIR = Path("/usr/share/fonts/truetype/sand-box/google")
PLAYFAIR = FONT_DIR / "Playfair Display/PlayfairDisplay-VariableFont_wght.ttf"
PLAYFAIR_I = FONT_DIR / "Playfair Display/PlayfairDisplay-Italic-VariableFont_wght.ttf"
CINZEL = FONT_DIR / "Cinzel/Cinzel-VariableFont_wght.ttf"
EB = FONT_DIR / "EB Garamond/EBGaramond-VariableFont_wght.ttf"

BG = (22, 16, 12)
CREAM = (243, 230, 200)
GOLD = (212, 176, 114)
GOLD_BRIGHT = (232, 205, 146)

# Original viewBox of File:GClef.svg
SRC_W, SRC_H = 15.186, 40.768
# Public-domain path from File:GClef.svg (Wikimedia Commons).
CLEF_D = (
    "m12.049 3.5296c0.305 3.1263-2.019 5.6563-4.0772 7.7014-0.9349 0.897-0.155 "
    "0.148-0.6437 0.594-0.1022-0.479-0.2986-1.731-0.2802-2.11 0.1304-2.6939 "
    "2.3198-6.5875 4.2381-8.0236 0.309 0.5767 0.563 0.6231 0.763 1.8382zm0.651 "
    "16.142c-1.232-0.906-2.85-1.144-4.3336-0.885-0.1913-1.255-0.3827-2.51-0.574-3.764 "
    "2.3506-2.329 4.9066-5.0322 5.0406-8.5394 0.059-2.232-0.276-4.6714-1.678-6.4836"
    "-1.7004 0.12823-2.8995 2.156-3.8019 3.4165-1.4889 2.6705-1.1414 5.9169-0.57 "
    "8.7965-0.8094 0.952-1.9296 1.743-2.7274 2.734-2.3561 2.308-4.4085 5.43-4.0046 "
    "8.878 0.18332 3.334 2.5894 6.434 5.8702 7.227 1.2457 0.315 2.5639 0.346 "
    "3.8241 0.099 0.2199 2.25 1.0266 4.629 0.0925 6.813-0.7007 1.598-2.7875 "
    "3.004-4.3325 2.192-0.5994-0.316-0.1137-0.051-0.478-0.252 1.0698-0.257 "
    "1.9996-1.036 2.26-1.565 0.8378-1.464-0.3998-3.639-2.1554-3.358-2.262 0.046"
    "-3.1904 3.14-1.7356 4.685 1.3468 1.52 3.833 1.312 5.4301 0.318 1.8125-1.18 "
    "2.0395-3.544 1.8325-5.562-0.07-0.678-0.403-2.67-0.444-3.387 0.697-0.249 "
    "0.209-0.059 1.193-0.449 2.66-1.053 4.357-4.259 3.594-7.122-0.318-1.469"
    "-1.044-2.914-2.302-3.792zm0.561 5.757c0.214 1.991-1.053 4.321-3.079 4.96"
    "-0.136-0.795-0.172-1.011-0.2626-1.475-0.4822-2.46-0.744-4.987-1.116-7.481 "
    "1.6246-0.168 3.4576 0.543 4.0226 2.184 0.244 0.577 0.343 1.197 0.435 1.812z"
    "m-5.1486 5.196c-2.5441 0.141-4.9995-1.595-5.6343-4.081-0.749-2.153-0.5283"
    "-4.63 0.8207-6.504 1.1151-1.702 2.6065-3.105 4.0286-4.543 0.183 1.127 "
    "0.366 2.254 0.549 3.382-2.9906 0.782-5.0046 4.725-3.215 7.451 0.5324 0.764 "
    "1.9765 2.223 2.7655 1.634-1.102-0.683-2.0033-1.859-1.8095-3.227-0.0821-1.282 "
    "1.3699-2.911 2.6513-3.198 0.4384 2.869 0.9413 6.073 1.3797 8.943-0.5054 "
    "0.1-1.0211 0.143-1.536 0.143z"
)


def font(path: Path, size: int, weight: int | None = None) -> ImageFont.FreeTypeFont:
    f = ImageFont.truetype(str(path), size=size)
    if weight is not None:
        try:
            f.set_variation_by_axes([weight])
        except Exception:
            pass
    return f


def find_spiral_center(im: Image.Image) -> tuple[float, float]:
    """Locate the inner eye of the G-clef (the hole the spiral wraps)."""
    alpha = im.split()[-1]
    w, h = im.size
    # The eye is a transparent region fully enclosed, in the middle third.
    # Scan rows for internal transparent runs that are bounded by ink on both sides
    # and have ink above and below — then take the centroid of the largest such blob.
    px = alpha.load()
    # flood-fill all transparent pixels connected to the border, what's left
    # that's transparent and not background is holes.
    from collections import deque
    visited = [[False] * w for _ in range(h)]
    q = deque()
    def is_clear(x, y):
        return px[x, y] < 40
    for x in range(w):
        if is_clear(x, 0):
            q.append((x, 0)); visited[0][x] = True
        if is_clear(x, h - 1):
            q.append((x, h - 1)); visited[h - 1][x] = True
    for y in range(h):
        if is_clear(0, y):
            q.append((0, y)); visited[y][0] = True
        if is_clear(w - 1, y):
            q.append((w - 1, y)); visited[y][w - 1] = True
    while q:
        x, y = q.popleft()
        for nx, ny in ((x-1,y),(x+1,y),(x,y-1),(x,y+1)):
            if 0 <= nx < w and 0 <= ny < h and not visited[ny][nx] and is_clear(nx, ny):
                visited[ny][nx] = True
                q.append((nx, ny))
    # remaining clear, unvisited pixels are holes
    holes = []
    for y in range(h):
        for x in range(w):
            if not visited[y][x] and is_clear(x, y):
                # flood this hole
                cells = []
                q.append((x, y))
                visited[y][x] = True
                while q:
                    cx, cy = q.popleft()
                    cells.append((cx, cy))
                    for nx, ny in ((cx-1,cy),(cx+1,cy),(cx,cy-1),(cx,cy+1)):
                        if 0 <= nx < w and 0 <= ny < h and not visited[ny][nx] and is_clear(nx, ny):
                            visited[ny][nx] = True
                            q.append((nx, ny))
                holes.append(cells)
    if not holes:
        raise SystemExit("no inner eye found in clef")
    holes.sort(key=len, reverse=True)
    cells = holes[0]
    cx = sum(x for x, _ in cells) / len(cells)
    cy = sum(y for _, y in cells) / len(cells)
    print(f"spiral eye at ({cx:.1f},{cy:.1f}) pixels={len(cells)} n_holes={len(holes)} sizes={[len(h) for h in holes[:5]]}")
    return cx, cy


def render_clef_layer() -> Image.Image:
    """Render the PD outline in cream, scaled and placed so the eye sits on the G line at CX."""
    # High-res monochrome render of the original SVG, then we'll measure the eye
    # and compute a transform into canvas space.
    scale_probe = 40  # 15.186*40 ≈ 607 px wide, 40.768*40 ≈ 1630 px tall
    svg = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="{SRC_W}" height="{SRC_H}" viewBox="0 0 {SRC_W} {SRC_H}">
  <path d="{CLEF_D}" fill="#ffffff"/>
</svg>'''
    png = cairosvg.svg2png(bytestring=svg.encode(), output_width=int(SRC_W * scale_probe))
    probe = Image.open(io.BytesIO(png)).convert("RGBA")
    eye_x, eye_y = find_spiral_center(probe)
    # We want the eye at (CX, G) on the canvas, and the outer spiral roughly
    # 1.15 staff spaces in radius. Estimate radius from the hole + surrounding ink.
    # The visual width of the spiral body is about 8 units in src (~8/15 of width).
    # Target: spiral width ≈ 2.4 staff spaces (typical engraving).
    # From the probe, measure ink bbox around the midsection.
    # Simpler: set scale so SRC_H maps to about 8.2 staff spaces (standard clef height).
    target_height = 8.15 * S
    canvas_scale = target_height / probe.height  # probe px -> canvas px
    # But also verify eye maps to G. After scaling, paste so eye -> (CX, G).
    new_w = max(1, int(round(probe.width * canvas_scale)))
    new_h = max(1, int(round(probe.height * canvas_scale)))
    # Recolor cream: render white, then tint
    scaled = probe.resize((new_w, new_h), Image.Resampling.LANCZOS)
    # tint white glyph to cream
    cream = Image.new("RGBA", scaled.size, CREAM + (0,))
    # use alpha of scaled
    r, g, b, a = scaled.split()
    cream.putalpha(a)
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    paste_x = int(round(CX - eye_x * canvas_scale))
    paste_y = int(round(G - eye_y * canvas_scale))
    print(f"clef paste at ({paste_x},{paste_y}) size {new_w}x{new_h} scale={canvas_scale:.4f}")
    layer.paste(cream, (paste_x, paste_y), cream)
    return layer


def grain(size, rng_seed=1552, alpha=22) -> Image.Image:
    rng = random.Random(rng_seed)
    n = Image.new("L", size, 0)
    px = n.load()
    w, h = size
    for _ in range(w * h // 8):
        px[rng.randrange(w), rng.randrange(h)] = rng.randint(0, 255)
    n = n.filter(ImageFilter.GaussianBlur(0.6))
    return Image.merge("RGBA", (n, n, n, Image.new("L", size, alpha)))


def draw_tracked(draw, text, y, fnt, fill, tracking=10):
    widths = []
    for ch in text:
        bb = draw.textbbox((0, 0), ch, font=fnt)
        widths.append(bb[2] - bb[0])
    total = sum(widths) + tracking * (len(text) - 1)
    x = (W - total) / 2
    for ch, w_ in zip(text, widths):
        draw.text((x, y), ch, font=fnt, fill=fill)
        x += w_ + tracking


def paste_shadow(base, layer, xy, offset=(5, 7)):
    alpha = layer.split()[-1].filter(ImageFilter.GaussianBlur(8))
    shadow = Image.new("RGBA", layer.size, (0, 0, 0, 0))
    shadow.putalpha(alpha.point(lambda a: int(a * 0.40)))
    base.paste(shadow, (xy[0] + offset[0], xy[1] + offset[1]), shadow)
    base.paste(layer, xy, layer)


def main():
    img = Image.new("RGB", (W, H), BG)
    # vignette
    vig = Image.new("L", (W, H), 0)
    vd = ImageDraw.Draw(vig)
    for i in range(40, 0, -1):
        pad = i * 14
        vd.rounded_rectangle([pad, pad, W - pad, H - pad], radius=20, outline=int(i * 3.2), width=18)
    vig = vig.filter(ImageFilter.GaussianBlur(40))
    dark = Image.new("RGB", (W, H), (8, 6, 5))
    img = Image.composite(dark, img, ImageChops.multiply(vig, Image.new("L", (W, H), 140)))
    d = ImageDraw.Draw(img, "RGBA")

    m = 64
    d.rectangle([m, m, W - m, H - m], outline=GOLD + (220,), width=2)
    d.rectangle([m + 10, m + 10, W - m - 10, H - m - 10], outline=GOLD + (110,), width=1)

    staff_left, staff_right = 220, W - 220
    lines = [("F", G - 3 * S), ("D", G - 2 * S), ("B", G - S), ("G", G), ("E", G + S)]
    for name, y in lines:
        if name == "G":
            continue
        d.line([(staff_left, y), (staff_right, y)], fill=GOLD + (78,), width=3)

    clef = render_clef_layer()

    # A narrow kerf so the clef still reads as a G-clef, clearly opened on the G line.
    gap = 14
    shift_x = 11
    shift_y = 8
    top = clef.crop((0, 0, W, G))
    bot = clef.crop((0, G, W, H))

    canvas = img.convert("RGBA")
    paste_shadow(canvas, top, (-shift_x, -shift_y - gap // 2))
    paste_shadow(canvas, bot, (shift_x, G + shift_y + gap // 2))
    img = canvas
    d = ImageDraw.Draw(img, "RGBA")

    cut_y = G
    d.line([(staff_left - 30, cut_y), (staff_right + 30, cut_y)], fill=GOLD_BRIGHT + (255,), width=4)
    d.line([(staff_left - 30, cut_y - 3), (staff_right + 30, cut_y - 3)], fill=(255, 236, 190, 80), width=1)
    d.line([(staff_left - 30, cut_y + 3), (staff_right + 30, cut_y + 3)], fill=(40, 24, 10, 120), width=1)

    # Whole note on the G line, right of the clef
    nx, ny = 1180, G
    note = Image.new("RGBA", (160, 120), (0, 0, 0, 0))
    nd = ImageDraw.Draw(note)
    nd.ellipse([20, 24, 140, 96], outline=CREAM + (255,), width=8)
    note = note.rotate(22, resample=Image.Resampling.BICUBIC, expand=True)
    img.paste(note, (nx - note.width // 2, ny - note.height // 2), note)
    d = ImageDraw.Draw(img, "RGBA")
    flab = font(CINZEL, 28, 500)
    d.text((nx + 70, ny + 28), "G", font=flab, fill=GOLD_BRIGHT)

    kicker = font(CINZEL, 26, 500)
    title = font(PLAYFAIR, 118, 600)
    draw_tracked(d, "THE TREBLE CLEF IS A G-CLEF", 160, kicker, GOLD, tracking=14)

    t = "SPLITTING THE G"
    bb = d.textbbox((0, 0), t, font=title)
    tw = bb[2] - bb[0]
    if tw > W - 180:
        title = font(PLAYFAIR, 100, 600)
        bb = d.textbbox((0, 0), t, font=title)
        tw = bb[2] - bb[0]
    d.text(((W - tw) / 2 - bb[0], 210), t, font=title, fill=CREAM)

    rule_y = 360
    d.line([(W // 2 - 160, rule_y), (W // 2 + 160, rule_y)], fill=GOLD + (200,), width=2)
    dx, dy = W // 2, rule_y
    d.polygon([(dx, dy - 6), (dx + 6, dy), (dx, dy + 6), (dx - 6, dy)], fill=GOLD)

    sb = font(PLAYFAIR_I, 40, 500)
    sub = "We opened it on the line it was named for."
    bb = d.textbbox((0, 0), sub, font=sb)
    d.text(((W - (bb[2] - bb[0])) / 2 - bb[0], 1488), sub, font=sb, fill=CREAM)

    cb = font(EB, 30, 500)
    caption = "Not a pint. A G-clef takes its name from the G line it wraps."
    bb = d.textbbox((0, 0), caption, font=cb)
    d.text(((W - (bb[2] - bb[0])) / 2 - bb[0], 1558), caption, font=cb, fill=GOLD)

    foot = font(CINZEL, 18, 400)
    draw_tracked(d, "ORIGINAL ILLUSTRATION  ·  POIDH  #1552", 1788, foot, GOLD, tracking=6)

    gimg = grain((W, H), alpha=22)
    img = Image.alpha_composite(img.convert("RGBA"), gimg)
    final = img.convert("RGB").filter(ImageFilter.UnsharpMask(radius=1.2, percent=80, threshold=3))
    dest = OUT / "split-the-g.png"
    final.save(dest, "PNG", optimize=True)
    print("wrote", dest, "size", dest.stat().st_size, "px", final.size)


if __name__ == "__main__":
    main()
