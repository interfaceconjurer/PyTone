"""README logo: the PyTone stack lockup rendered by the tool itself (circles ramp, as L3).

The mark is a dot screen, and the tool lays its own glyph grid over the image. When the two
grids don't line up they beat, so rows of dots come out uneven. Here the source image is
composed so every screen dot lands on a fixed number of tool cells:

  A3  3 columns x 2 rows per screen dot: about one glyph per dot (L3's look, without beating).
      An SVG cell is 1 x 1.6, so this grid is 3 : 3.2; the mark is stretched 6.7% vertically.
  A5  5 columns x 3 rows per screen dot: 5 : 4.8, within 4% of square; small glyph clusters.
  A8  8 columns x 5 rows per screen dot: exactly square, each dot becomes a cluster of glyphs.

Run from the repo root:  uv run --with fonttools python design/scripts/make_readme_logo.py
"""
import math
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from make_dense import SIZE  # noqa: E402
from make_lockup import FINAL, f, mark, word  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # repo root
OUT = os.path.join(ROOT, "design", "build", "readme-logo")
RAMP = " ·∘○◯●"
PITCH = SIZE / 23  # screen pitch in mark units
THEMES = {"dark": "#ffffff", "light": "#000000"}
GRIDS = {"A8": dict(c=10, ph=8, pv=5)}


def compose(name, c, ph, pv):
    """Source PNG (white on black) sized and offset so the screen sits on the tool's cells."""
    h = 1.6 * c  # tool row height in source px
    pitch_x, pitch_y = ph * c, pv * h
    body, vb = mark("dark")
    vx, vy, vw, vh = vb
    kx, ky = pitch_x / PITCH, pitch_y / PITCH
    mw, mh = vw * kx, vh * ky
    # Dot centres must fall on cell centres: centre = x0 + pitch/2 + j * pitch.
    x0 = 2 * c + ((0.5 * c - pitch_x / 2) % c)
    y0 = 2 * h + ((0.5 * h - pitch_y / 2) % h)
    d, box, cap = word(FINAL)
    cap_px = mh * 0.3
    k = cap_px / cap
    ww = (box[2] - box[0]) * k
    cols = math.ceil((x0 * 2 + mw) / c)
    W = cols * c
    gap = cap_px * 0.8
    base = y0 + mh + gap + cap_px
    rows = math.ceil((base + cap_px * 0.35 + 2 * h) / h)
    H = rows * h
    wx = (W - ww) / 2 - box[0] * k
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{f(W)}" height="{f(H)}" viewBox="0 0 {f(W)} {f(H)}">'
           f'<rect width="{f(W)}" height="{f(H)}" fill="#000"/>'
           f'<clipPath id="m"><rect x="{f(x0)}" y="{f(y0)}" width="{f(mw)}" height="{f(mh)}"/></clipPath>'
           f'<g clip-path="url(#m)"><g transform="translate({f(x0 - vx * kx)} {f(y0 - vy * ky)}) scale({f(kx)} {f(ky)})">{body}</g></g>'
           f'<path d="{d}" fill="#fff" transform="translate({f(wx)} {f(base)}) scale({f(k)})"/></svg>')
    src_svg = os.path.join(OUT, f"src-{name}.svg")
    open(src_svg, "w").write(svg)
    png = os.path.join(OUT, f"src-{name}.png")
    subprocess.run(["rsvg-convert", src_svg, "-o", png], check=True)
    return png, cols, rows


def main():
    os.makedirs(OUT, exist_ok=True)
    for name, g in GRIDS.items():
        png, cols, rows = compose(name, **g)
        for theme, ink in THEMES.items():
            out = os.path.join(OUT, f"stack-{name}-{theme}.svg")
            subprocess.run(["uv", "run", "--project", ROOT, "pytone", png, "-m", "svg", "-w", str(cols), "-c", RAMP,
                            "--gradient", f"{ink},{ink}", "--pixel-width", "880", "-o", out],
                           check=True, capture_output=True, cwd=ROOT)
        n = open(out).read().count("<text")
        print(f"{name}: {cols} x {rows} cells, {n} glyphs, {os.path.getsize(out) // 1000} KB")


if __name__ == "__main__":
    main()
