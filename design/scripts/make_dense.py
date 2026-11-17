"""py-tone mark: Zig with a dense halftone body, like the original Glide.

The body is several dots across: full dots in the core, ramping down to screen size
across the edge (Glide's rule: t = clamp(0.5 - distance / pitch)), on a tapered body.

  fine-N     one grid of N columns for everything (as in the original Glide)
  over-11    an 11-column background screen, with the body drawn on a 3x finer subgrid,
             so the body has more dots than the screen around it

Each is cropped to a band of whole cells around the snake. Run from the repo root:
    python3 design/scripts/make_dense.py
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from make_glide import INK, SHAPES, SIZE, f, fit  # noqa: E402
from make_glide2 import Head, dot  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # repo root
OUT = os.path.join(ROOT, "design", "build", "dense")
BG, FULL = 0.2, 0.46  # dot radius as a fraction of pitch: screen, full body


def zig(half):
    c = [(x * SIZE, y * SIZE) for x, y in fit(SHAPES["zig"]())]
    N = len(c)
    w = half * SIZE
    widths = [w * (0.1 + 0.9 * min(1.0, i / (N * 0.6)) ** 0.8) for i in range(N)]
    return c, widths, list(zip(c[::2], widths[::2]))


def sd(samples, x, y):
    return min(math.hypot(x - a, y - b) - w for (a, b), w in samples)


# The snake starts whole at the head and dissolves into dots toward the tail:
#   SOLID  fraction of the body length, from the head, drawn as one solid shape
#   FADE   fraction after that over which the body dots shrink from merged back to halftone
#   BOOST  how much larger than a full halftone dot the body dots are at the solid end
SOLID, FADE, BOOST = 0.12, 0.24, 0.55


def from_head(c):
    """Fraction of the body length between each centerline point and the head (head = 0)."""
    acc, out = 0.0, [0.0]
    for (x0, y0), (x1, y1) in zip(c, c[1:]):
        acc += math.hypot(x1 - x0, y1 - y0)
        out.append(acc)
    return [(acc - v) / acc for v in out]


def indexed(c, widths, step=2):
    return [(c[i][0], c[i][1], widths[i], i) for i in range(0, len(c), step)]


def nearest(idx, x, y):
    """Signed distance to the body edge and the nearest centerline index."""
    best = min(idx, key=lambda e: math.hypot(x - e[0], y - e[1]) - e[2])
    return math.hypot(x - best[0], y - best[1]) - best[2], best[3]


def merge(h):
    """1 inside the solid neck, easing to 0 by the end of the fade."""
    if h <= SOLID:
        return 1.0
    u = min(1.0, (h - SOLID) / FADE)
    return 1 - u * u * (3 - 2 * u)


def neck(c, widths, hf, ink):
    """The solid stretch behind the head. It narrows at its back end so the dots grow out of it."""
    pts = [i for i in range(len(c)) if hf[i] <= SOLID]
    if len(pts) < 2:
        return ""
    i0 = pts[0]
    span = max(1, len(pts) - 1)
    out = []
    for a, b in zip(pts[::2], pts[2::2] + [pts[-1]]):
        u = (b - i0) / span
        ramp = 0.35 + 0.5 * min(1.0, u / 0.6) ** 0.9
        (x0, y0), (x1, y1) = c[a], c[b]
        out.append(f'<line x1="{f(x0)}" y1="{f(y0)}" x2="{f(x1)}" y2="{f(y1)}" stroke="{ink}" '
                   f'stroke-width="{f(2 * widths[b] * ramp)}" stroke-linecap="round"/>')
    return "".join(out)


def bounds(c, widths, head):
    xs = [x - w for (x, _), w in zip(c, widths)] + [x + w for (x, _), w in zip(c, widths)]
    ys = [y - w for (_, y), w in zip(c, widths)] + [y + w for (_, y), w in zip(c, widths)]
    for x, y in head.poly + [pt for line in head.tongue for pt, _ in line]:
        xs.append(x)
        ys.append(y)
    return min(xs), min(ys), max(xs), max(ys)


def band(box, p, n, margin, trim_top=0):
    """Crop to whole cells around the snake; trim_top drops that many screen rows from the top."""
    x0, y0, x1, y1 = box
    c0, r0 = max(0, int(x0 // p) - margin), max(0, int(y0 // p) - margin) + trim_top
    c1, r1 = min(n, int(x1 // p) + 1 + margin), min(n, int(y1 // p) + 1 + margin)
    return c0 * p, r0 * p, (c1 - c0) * p, (r1 - r0) * p


def fine(n, half=0.062, margin=2, ink="#000", paper="#fff", eye="dot", tongue="arc"):
    """One grid for everything: the body is the same screen, ramped up, merging into a solid
    neck at the head."""
    c, widths, samples = zig(half)
    hf = from_head(c)
    idx = indexed(c, widths)
    head = Head(c, widths[-1], tongue)
    p = SIZE / n
    out = []
    for gy in range(n):
        for gx in range(n):
            x, y = (gx + 0.5) * p, (gy + 0.5) * p
            d, i = nearest(idx, x, y)
            t = max(0.0, min(1.0, 0.5 - d / p))
            # Toward the head, dots well inside the body swell until they overlap; dots on
            # the edge keep their halftone size, so the snake's outline doesn't bulge.
            core = max(0.0, min(1.0, -d / (0.5 * p)))
            k = merge(hf[i]) * core
            r = (BG + (FULL - BG) * t) * p * (1 + BOOST * k)
            if head.blocks(x, y, r, 0.14 * p, body=t > 0.35):
                continue
            out.append(dot(x, y, r, ink))
    body = "".join(out) + neck(c, widths, hf, ink) + head.svg(ink, paper, eye)
    return body, band(bounds(c, widths, head), p, n, margin)


def over(n=11, sub=3, half=0.062, margin=1, ink="#000", paper="#fff", trim_top=0, eye="dot", tongue="arc"):
    """Coarse screen behind; the body is a finer screen aligned to a subdivision of it."""
    c, widths, samples = zig(half)
    head = Head(c, widths[-1], tongue)
    p, q = SIZE / n, SIZE / (n * sub)
    out = []
    for gy in range(n):  # background, cleared around the body
        for gx in range(n):
            x, y = (gx + 0.5) * p, (gy + 0.5) * p
            r = BG * p
            if sd(samples, x, y) < r + 0.2 * p or head.blocks(x, y, r, 0.14 * p):
                continue
            out.append(dot(x, y, r, ink))
    hf = from_head(c)
    idx = indexed(c, widths)
    for gy in range(n * sub):  # body
        for gx in range(n * sub):
            x, y = (gx + 0.5) * q, (gy + 0.5) * q
            d, i = nearest(idx, x, y)
            t = max(0.0, min(1.0, 0.5 - d / q))
            if t <= 0:
                continue
            core = max(0.0, min(1.0, -d / (0.6 * q)))
            k = merge(hf[i]) * core
            r = FULL * q * math.sqrt(t) * (1 + BOOST * 1.2 * k)
            if r < q * 0.12 or head.blocks(x, y, r, 0.05 * q, body=True):
                continue
            out.append(dot(x, y, r, ink))
    out.append(neck(c, widths, hf, ink))
    vb = band(bounds(c, widths, head), p, n, margin, trim_top)
    return "".join(out) + head.svg(ink, paper, eye), vb


VARIANTS = {
    "fine-19": lambda ink, paper: fine(19, ink=ink, paper=paper),
    "fine-23": lambda ink, paper: fine(23, ink=ink, paper=paper),
    "fine-27": lambda ink, paper: fine(27, ink=ink, paper=paper),
    "over-11": lambda ink, paper: over(ink=ink, paper=paper, trim_top=1),
    "fine-23-slim": lambda ink, paper: fine(23, half=0.05, ink=ink, paper=paper),
}


EYES = ["dot", "lid"]
SHORTLIST = {"3": lambda **k: fine(27, **k), "2": lambda **k: fine(23, **k), "5": lambda **k: over(trim_top=1, **k)}


def write(path, body, vb, paper):
    vx, vy, vw, vh = vb
    k = 560 / vw
    open(path, "w").write(
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{f(vx)} {f(vy)} {f(vw)} {f(vh)}" '
        f'width="{vw * k:.0f}" height="{vh * k:.0f}" role="img" aria-label="py-tone mark">'
        f'<title>py-tone mark</title><rect x="{f(vx)}" y="{f(vy)}" width="{f(vw)}" height="{f(vh)}" fill="{paper}"/>{body}</svg>')


TONGUE_ORDER = ["wave", "arc", "splay"]


def head_box(head, pad):
    pts = head.poly + [pt for line in head.tongue for pt, _ in line]
    xs, ys = [x for x, _ in pts], [y for _, y in pts]
    return min(xs) - pad, min(ys) - pad, max(xs) - min(xs) + 2 * pad, max(ys) - min(ys) + 2 * pad


def tongues():
    """Each tongue on all three shortlisted marks, plus a close-up of option 2's head."""
    os.makedirs(os.path.join(OUT, "tongues"), exist_ok=True)
    for tongue in TONGUE_ORDER:
        for num, fn in SHORTLIST.items():
            for theme, (ink, paper) in INK.items():
                body, vb = fn(ink=ink, paper=paper, tongue=tongue)
                write(os.path.join(OUT, "tongues", f"{num}-{tongue}-{theme}.svg"), body, vb, paper)
        c, widths, _ = zig(0.062)
        head = Head(c, widths[-1], tongue)
        x, y, w, h = head_box(head, widths[-1] * 0.6)
        side = max(w, h * 1.6)
        box = (x + w / 2 - side / 2, y + h / 2 - side / 3.2, side, side / 1.6)
        for theme, (ink, paper) in INK.items():
            body, _ = fine(23, ink=ink, paper=paper, tongue=tongue)
            write(os.path.join(OUT, "tongues", f"close-{tongue}-{theme}.svg"), body, box, paper)
    print("built tongues:", len(TONGUE_ORDER), "styles")


def eyes():
    os.makedirs(os.path.join(OUT, "eyes"), exist_ok=True)
    for num, fn in SHORTLIST.items():
        for eye in EYES:
            for theme, (ink, paper) in INK.items():
                body, vb = fn(ink=ink, paper=paper, eye=eye)
                write(os.path.join(OUT, "eyes", f"{num}-{eye}-{theme}.svg"), body, vb, paper)
    print("built eyes:", len(SHORTLIST) * len(EYES) * 2, "files")


def main():
    os.makedirs(OUT, exist_ok=True)
    for name, fn in VARIANTS.items():
        for theme, (ink, paper) in INK.items():
            body, (vx, vy, vw, vh) = fn(ink, paper)
            k = 560 / vw
            svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{f(vx)} {f(vy)} {f(vw)} {f(vh)}" '
                   f'width="{vw * k:.0f}" height="{vh * k:.0f}" role="img" aria-label="py-tone mark">'
                   f'<title>py-tone mark</title><rect x="{f(vx)}" y="{f(vy)}" width="{f(vw)}" height="{f(vh)}" fill="{paper}"/>{body}</svg>')
            open(os.path.join(OUT, f"zig-{name}-{theme}.svg"), "w").write(svg)
        print("built", name)


if __name__ == "__main__":
    main()
    eyes()
    tongues()
