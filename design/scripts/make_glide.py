"""py-tone mark: Glide, the halftone snake, on small dot grids.

The mark is a square n x n dot grid. Each dot's area is the share of its cell covered by
the snake's body (a true halftone): full dots inside, partial dots along the edge, a
visible screen dot everywhere else. The head is a solid, slightly pointed oval with a
knocked-out eye and a forked tongue, overlapping the neck so it grows out of the body.

Shapes are built from straight runs and circular arcs in artboard units (0..1), so the
same snake sits on every grid; finer grids just render its edges more smoothly.
Run from the repo root:  python3 design/scripts/make_glide.py
"""
import math
import os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # repo root
OUT = os.path.join(ROOT, "design", "build", "glide")
INK = {"light": ("#000000", "#ffffff"), "dark": ("#ffffff", "#000000")}  # (ink, paper)
SIZE = 528
BG, BODY = 0.2, 0.47  # screen and full-body dot radius, as a fraction of the pitch
GRIDS = (9, 11, 13)
HALF = 0.05  # body half-width at the neck, artboard units (~1 cell wide on 9x9)


def f(n):
    return f"{n:.2f}".rstrip("0").rstrip(".")


class Path:
    """Turtle-style centerline: straight runs and arcs, sampled densely."""

    def __init__(self, x, y, heading_deg):
        self.pts = [(x, y)]
        self.a = math.radians(heading_deg)

    def run(self, d, step=0.004):
        x, y = self.pts[-1]
        n = max(1, int(d / step))
        for k in range(1, n + 1):
            self.pts.append((x + math.cos(self.a) * d * k / n, y + math.sin(self.a) * d * k / n))
        return self

    def turn(self, r, deg, step=0.004):
        """Arc of radius r; positive deg turns clockwise on screen (y down)."""
        x, y = self.pts[-1]
        sgn = 1 if deg > 0 else -1
        cx, cy = x + math.cos(self.a + sgn * math.pi / 2) * r, y + math.sin(self.a + sgn * math.pi / 2) * r
        a0 = math.atan2(y - cy, x - cx)
        sweep = math.radians(deg)
        n = max(2, int(abs(sweep) * r / step))
        for k in range(1, n + 1):
            t = a0 + sweep * k / n
            self.pts.append((cx + math.cos(t) * r, cy + math.sin(t) * r))
        self.a += sweep
        return self


# Up is -90 degrees, right is 0. Positive turns are clockwise on screen.
def shape_s():
    return Path(0.14, 0.78, 0).run(0.5).turn(0.13, -180).run(0.44).turn(0.13, 180).run(0.4).pts


def shape_rise():
    return Path(0.12, 0.8, 0).run(0.44).turn(0.18, -90).run(0.2).turn(0.12, 45).run(0.06).pts


def shape_wave():
    return Path(0.1, 0.62, -30).turn(0.2, 60).turn(0.2, -120).turn(0.2, 120).turn(0.2, -90).run(0.04).pts


def shape_hook():
    return Path(0.86, 0.8, 180).run(0.5).turn(0.17, 180).run(0.32).turn(0.1, 90).run(0.02).pts


def shape_zig():
    return Path(0.1, 0.8, -50).run(0.2).turn(0.1, 100).run(0.28).turn(0.1, -100).run(0.28).turn(0.1, 100).run(0.1).turn(0.08, -50).pts


SHAPES = {"s": shape_s, "rise": shape_rise, "wave": shape_wave, "hook": shape_hook, "zig": shape_zig}


ARROW = 0.35  # 0 = the plain oval head; 1 = a clear arrowhead. Subtle by default.


def _smooth(pts, passes=3):
    """Chaikin corner cutting on a closed outline: rounds the jaw and snout corners."""
    for _ in range(passes):
        nxt = []
        for (x0, y0), (x1, y1) in zip(pts, pts[1:] + pts[:1]):
            nxt.append((0.75 * x0 + 0.25 * x1, 0.75 * y0 + 0.25 * y1))
            nxt.append((0.25 * x0 + 0.75 * x1, 0.25 * y0 + 0.75 * y1))
        pts = nxt
    return pts


def head_outline(x, y, ux, uy, w, arrow=None):
    """Snake head: fuller at the back, tapering to the snout. (x, y) is the end of the neck;
    the back of the head overlaps the neck by about half a body width.

    arrow blends the oval toward an arrowhead (a rounded triangle): the widest point moves
    back to the jaw, which flares slightly, and the sides run straight to a rounded snout."""
    a_ = ARROW if arrow is None else arrow
    vx, vy = -uy, ux
    L, R = w * 1.75, w * 1.3
    cx, cy = x + ux * w * 0.55, y + uy * w * 0.55
    # The arrowhead as a polygon in (along, across) head units: rounded back, a jaw corner,
    # straight sides to the snout. It is then blended with the oval sample-for-sample.
    jaw_u, jaw_w, snout_w = -0.2, 1.04, 0.16
    def arrow_half(u):
        if u >= jaw_u:
            s_ = (u - jaw_u) / (1 - jaw_u)
            return jaw_w * (1 - s_) + snout_w * s_
        b = (jaw_u - u) / (1 + jaw_u)
        return jaw_w * math.sqrt(max(0.0, 1 - b ** 2.4))
    out = []
    n = 120
    for k in range(n):
        t = 2 * math.pi * k / n
        ca, sa = math.cos(t), math.sin(t)
        along = L * ca * (1.0 if ca < 0 else 0.95)
        oval = abs(sa) * (1 - 0.3 * max(0.0, ca) ** 1.6)
        across = R * ((1 - a_) * oval + a_ * arrow_half(ca) * min(1.0, abs(sa) * 6)) * (1 if sa >= 0 else -1)
        out.append((cx + ux * along + vx * across, cy + uy * along + vy * across))
    return _smooth(out, passes=4), (cx, cy, L, R, vx, vy)


def inside(poly, x, y):
    hit = False
    for (x0, y0), (x1, y1) in zip(poly, poly[1:] + poly[:1]):
        if (y0 > y) != (y1 > y) and x < x0 + (y - y0) * (x1 - x0) / (y1 - y0):
            hit = not hit
    return hit


def seg_dist(px, py, ax, ay, bx, by):
    dx, dy = bx - ax, by - ay
    t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / ((dx * dx + dy * dy) or 1)))
    return math.hypot(px - ax - t * dx, py - ay - t * dy)


def poly_dist(poly, x, y):
    return min(seg_dist(x, y, *a, *b) for a, b in zip(poly, poly[1:] + poly[:1]))


def fit(pts, margin=0.14):
    """Scale and centre a centerline into the artboard, leaving room for the body and head.
    The bounds include where the head and tongue reach past the end of the path."""
    (ax, ay), (bx, by) = pts[-6], pts[-1]
    d = math.hypot(bx - ax, by - ay) or 1
    reach = HALF * 4.2 / max(0.3, 1 - 2 * margin)  # head + tongue, roughly, before scaling
    tip = (bx + (bx - ax) / d * reach, by + (by - ay) / d * reach)
    xs, ys = [x for x, _ in pts + [tip]], [y for _, y in pts + [tip]]
    w, h = max(xs) - min(xs), max(ys) - min(ys)
    k = (1 - 2 * margin) / max(w, h)
    ox = 0.5 - (min(xs) + max(xs)) / 2 * k
    oy = 0.5 - (min(ys) + max(ys)) / 2 * k
    return [(x * k + ox, y * k + oy) for x, y in pts]


def mark(shape, n, ink, paper, body=BODY, half=HALF, curve=0.5, bridge=0.0):
    """body: dot radius (fraction of pitch) for a fully covered cell. Above 0.5, neighbouring
    body dots overlap, so the snake reads as one connected shape.
    half: body half-width at the neck (artboard units).
    curve: coverage -> area curve exponent; below 1 pushes partly covered cells toward full.
    bridge: if > 0, join neighbouring body dots (including diagonals) with a bar this
    fraction of the smaller dot's diameter, so the body connects across the grid."""
    p = SIZE / n
    c = [(x * SIZE, y * SIZE) for x, y in fit(SHAPES[shape]())]
    N = len(c)
    w = half * SIZE
    widths = [w * (0.15 + 0.85 * min(1.0, i / (N * 0.55)) ** 0.8) for i in range(N)]
    samples = list(zip(c[::2], widths[::2]))
    hx, hy = c[-1]
    bx, by = c[max(0, N - 6)]
    ux, uy = hx - bx, hy - by
    m = math.hypot(ux, uy)
    ux, uy = ux / m, uy / m
    hpoly, (cx, cy, L, R, vx, vy) = head_outline(hx, hy, ux, uy, w)
    tx, ty = cx + ux * L * 0.97, cy + uy * L * 0.97
    fx, fy = tx + ux * w * 0.9, ty + uy * w * 0.9
    ang, arm = math.atan2(uy, ux), w * 0.55
    forks = [(fx + math.cos(ang + s) * arm, fy + math.sin(ang + s) * arm) for s in (-0.6, 0.6)]
    gap = 0.14 * p
    ss = 6
    out = []
    joints = {}
    for gy in range(n):
        for gx in range(n):
            x, y = (gx + 0.5) * p, (gy + 0.5) * p
            cov = 0
            for sy in range(ss):
                for sx in range(ss):
                    qx, qy = gx * p + (sx + 0.5) * p / ss, gy * p + (sy + 0.5) * p / ss
                    if min(math.hypot(qx - a, qy - b) - wd for (a, b), wd in samples) < 0:
                        cov += 1
            cov /= ss * ss
            r = p * math.sqrt(BG * BG + (body * body - BG * BG) * cov ** (curve * 2))  # dot area tracks coverage
            if inside(hpoly, x, y):
                continue
            # Screen dots stay clear of the head and tongue; body dots may touch the head.
            if cov < 0.35 and poly_dist(hpoly, x, y) < r + gap:
                continue
            tongue_d = min([seg_dist(x, y, tx, ty, fx, fy)] + [seg_dist(x, y, fx, fy, a, b) for a, b in forks])
            if tongue_d < r + gap + w * 0.12:
                continue
            out.append(f'<circle cx="{f(x)}" cy="{f(y)}" r="{f(r)}" fill="{ink}"/>')
            if cov > 0.3:
                joints[(gx, gy)] = (x, y, r)
    if bridge:
        for (gx, gy), (x, y, r) in joints.items():
            for dx, dy in ((1, 0), (0, 1), (1, 1), (1, -1)):
                nb = joints.get((gx + dx, gy + dy))
                if not nb:
                    continue
                # Diagonals only join when neither shared orthogonal neighbour is in the body,
                # so a filled 2 x 2 block doesn't sprout an X.
                if dx and dy and ((gx + dx, gy) in joints or (gx, gy + dy) in joints):
                    continue
                x2, y2, r2 = nb
                sw = 2 * min(r, r2) * bridge
                out.append(f'<line x1="{f(x)}" y1="{f(y)}" x2="{f(x2)}" y2="{f(y2)}" stroke="{ink}" '
                           f'stroke-width="{f(sw)}" stroke-linecap="round"/>')
    out.append(f'<path d="M{" L".join(f"{f(a)} {f(b)}" for a, b in hpoly)} Z" fill="{ink}"/>')
    nside = min(((vx, vy), (-vx, -vy)), key=lambda v: (round(v[1], 3), v[0]))  # the upper side
    ex, ey = cx + ux * L * 0.22 + nside[0] * R * 0.42, cy + uy * L * 0.22 + nside[1] * R * 0.42
    out.append(f'<circle cx="{f(ex)}" cy="{f(ey)}" r="{f(w * 0.24)}" fill="{paper}"/>')
    d = f"M{f(tx)} {f(ty)} L{f(fx)} {f(fy)}" + "".join(f" M{f(fx)} {f(fy)} L{f(a)} {f(b)}" for a, b in forks)
    out.append(f'<path d="{d}" fill="none" stroke="{ink}" stroke-width="{f(w * 0.22)}" stroke-linecap="round" stroke-linejoin="round"/>')
    margin = min(min(a, b, SIZE - a, SIZE - b) for a, b in forks + hpoly + c)
    return "".join(out), margin


def svg(body, paper, title):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {SIZE} {SIZE}" width="{SIZE}" height="{SIZE}" '
            f'role="img" aria-label="{title}"><title>{title}</title><rect width="{SIZE}" height="{SIZE}" fill="{paper}"/>{body}</svg>')


def main():
    os.makedirs(OUT, exist_ok=True)
    for shape in SHAPES:
        for n in GRIDS:
            for theme, (ink, paper) in INK.items():
                body, margin = mark(shape, n, ink, paper)
                open(os.path.join(OUT, f"{shape}-{n}-{theme}.svg"), "w").write(svg(body, paper, f"py-tone mark: {shape}, {n}x{n}"))
            print(f"{shape:5} {n:2}x{n:<2} edge margin {margin / SIZE:.3f}{'  <-- tight' if margin < SIZE * 0.03 else ''}")


if __name__ == "__main__":
    main()
