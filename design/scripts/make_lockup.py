"""py-tone: the mark (option 2, 23 columns, tongue T2, eye A) with the PyTone wordmark.

Type is converted to vector outlines (no font dependency in the SVG). Lockups:
  side     mark left, word right, the word's cap height centred on the mark
  stack    mark above, word centred below
  inline   word set on the mark's band, to the right of the head, sharing the dot screen

Run from the repo root:  uv run --with fonttools python design/scripts/make_lockup.py
"""
import os
import sys

from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from make_dense import INK, fine, f  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # repo root
OUT = os.path.join(ROOT, "design", "build", "lockup")
FONTS = {
    "F1": ("Space Grotesk Bold", os.path.join(ROOT, "design", "fonts", "SpaceGrotesk-Bold.ttf"), 0),
}
WORD = "PyTone"
_cache = {}


def word(key, text=WORD):
    """Outlines for the word at 1 unit = 1 em; returns (path_d, ink_box, cap_height)."""
    if key not in _cache:
        _cache[key] = TTFont(FONTS[key][1])
    ft = _cache[key]
    track = FONTS[key][2]
    upm = ft["head"].unitsPerEm
    cmap, gs, hmtx = ft.getBestCmap(), ft.getGlyphSet(), ft["hmtx"]
    cap = getattr(ft["OS/2"], "sCapHeight", 0) or 0.7 * upm
    s = 1 / upm
    x, parts, box = 0.0, [], None
    for ch in text:
        g = cmap[ord(ch)]
        pen = SVGPathPen(gs)
        gs[g].draw(TransformPen(pen, (s, 0, 0, -s, x, 0)))
        parts.append(pen.getCommands())
        bp = BoundsPen(gs)
        gs[g].draw(TransformPen(bp, (s, 0, 0, s, x, 0)))
        if bp.bounds:
            b = bp.bounds
            box = b if box is None else (min(box[0], b[0]), min(box[1], b[1]), max(box[2], b[2]), max(box[3], b[3]))
        x += hmtx[g][0] * s + track
    return " ".join(parts), box, cap / upm


def mark(theme):
    ink, paper = INK[theme]
    body, vb = fine(23, ink=ink, paper=paper, eye="dot", tongue="arc")
    return body, vb


def svg(w, h, inner, paper, title):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {f(w)} {f(h)}" width="{f(w)}" height="{f(h)}" '
            f'role="img" aria-label="{title}"><title>{title}</title><rect width="{f(w)}" height="{f(h)}" fill="{paper}"/>{inner}</svg>')


def place_mark(body, vb, x, y, height):
    vx, vy, vw, vh = vb
    k = height / vh
    clip = f"m{int(x)}{int(y)}"
    return (f'<clipPath id="{clip}"><rect x="{f(x)}" y="{f(y)}" width="{f(vw * k)}" height="{f(height)}"/></clipPath>'
            f'<g clip-path="url(#{clip})"><g transform="translate({f(x - vx * k)} {f(y - vy * k)}) scale({f(k)})">{body}</g></g>'), vw * k


def place_word(key, ink, left, baseline, cap_px):
    d, box, cap = word(key)
    k = cap_px / cap
    return (f'<path d="{d}" fill="{ink}" transform="translate({f(left - box[0] * k)} {f(baseline)}) scale({f(k)})"/>',
            (box[2] - box[0]) * k)


def side(key, theme, mh=120, pad=28):
    ink, paper = INK[theme]
    body, vb = mark(theme)
    m, mw = place_mark(body, vb, pad, pad, mh)
    cap_px = mh * 0.42
    gap = mh * 0.22
    baseline = pad + mh / 2 + cap_px / 2
    w_, ww = place_word(key, ink, pad + mw + gap, baseline, cap_px)
    W = pad + mw + gap + ww + pad
    return svg(W, mh + 2 * pad, m + w_, paper, "PyTone")


def stack(key, theme, mw_target=360, pad=32):
    ink, paper = INK[theme]
    body, vb = mark(theme)
    mh = mw_target * vb[3] / vb[2]
    cap_px = mh * 0.34
    _, ww = place_word(key, ink, 0, 0, cap_px)
    W = max(mw_target, ww) + 2 * pad
    m, mw = place_mark(body, vb, (W - mw_target) / 2, pad, mh)
    gap = cap_px * 0.75
    baseline = pad + mh + gap + cap_px
    w_, _ = place_word(key, ink, (W - ww) / 2, baseline, cap_px)
    return svg(W, baseline + pad + cap_px * 0.25, m + w_, paper, "PyTone")


FINAL = "F1"  # Space Grotesk Bold


def final():
    """The chosen brand set: mark, wordmark and both lockups, dark and light."""
    d = os.path.join(ROOT, "docs", "identity")
    os.makedirs(d, exist_ok=True)
    for theme in INK:
        ink, paper = INK[theme]
        body, vb = mark(theme)
        vx, vy, vw, vh = vb
        k = 560 / vw
        open(os.path.join(d, f"pytone-mark-{theme}.svg"), "w").write(
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{f(vx)} {f(vy)} {f(vw)} {f(vh)}" '
            f'width="{vw * k:.0f}" height="{vh * k:.0f}" role="img" aria-label="PyTone"><title>PyTone</title>'
            f'<rect x="{f(vx)}" y="{f(vy)}" width="{f(vw)}" height="{f(vh)}" fill="{paper}"/>{body}</svg>')
        for kind, fn in (("lockup-side", side), ("lockup-stack", stack)):
            open(os.path.join(d, f"pytone-{kind}-{theme}.svg"), "w").write(fn(FINAL, theme))
        src = open(os.path.join(OUT, f"word-{FINAL}-{theme}.svg")).read()
        open(os.path.join(d, f"pytone-wordmark-{theme}.svg"), "w").write(src)
    print("brand set ->", d)


def main():
    os.makedirs(OUT, exist_ok=True)
    for key in FONTS:
        for theme in INK:
            open(os.path.join(OUT, f"side-{key}-{theme}.svg"), "w").write(side(key, theme))
            open(os.path.join(OUT, f"stack-{key}-{theme}.svg"), "w").write(stack(key, theme))
            ink, paper = INK[theme]
            d, box, cap = word(key)
            k = 60 / cap
            ww = (box[2] - box[0]) * k
            inner = f'<path d="{d}" fill="{ink}" transform="translate({f(24 - box[0] * k)} {f(24 + 60)}) scale({f(k)})"/>'
            open(os.path.join(OUT, f"word-{key}-{theme}.svg"), "w").write(svg(ww + 48, 60 + 48 + 60 * 0.3, inner, paper, "PyTone"))
        print("built", key, FONTS[key][0])


if __name__ == "__main__":
    main()
    final()
