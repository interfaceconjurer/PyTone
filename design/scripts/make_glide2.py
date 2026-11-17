"""py-tone mark: Glide round 2.

  glide-original   The round-3 Glide restored (23 x 23 screen, original S curve, body width
                   ramp), with the snake-shaped head in place of the circle.
  wave-6           Wave on a 6 x 6 screen; the snake's dots are larger and merge along the body.
  wave-9-screen    Wave on a 9 x 9 screen; the body is its own finer halftone, angled 45
                   degrees like a print screen, so its dots don't line up with the grid.
  wave-9-rows      Wave on a 9 x 9 screen; the body is rows of dots laid along the snake,
                   following its curve.

Run from the repo root:  python3 design/scripts/make_glide2.py
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from make_glide import INK, SIZE, f, fit, head_outline, inside, poly_dist, seg_dist, shape_wave, svg  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # repo root
OUT = os.path.join(ROOT, "design", "build", "glide2")


def dot(x, y, r, fill):
    return f'<circle cx="{f(x)}" cy="{f(y)}" r="{f(r)}" fill="{fill}"/>'


def catmull(points, steps=30):
    pts = [points[0]] + points + [points[-1]]
    out = []
    for i in range(1, len(pts) - 2):
        p0, p1, p2, p3 = pts[i - 1], pts[i], pts[i + 1], pts[i + 2]
        for k in range(steps):
            t = k / steps
            out.append(tuple(0.5 * ((2 * p1[j]) + (-p0[j] + p2[j]) * t + (2 * p0[j] - 5 * p1[j] + 4 * p2[j] - p3[j]) * t * t
                                    + (-p0[j] + 3 * p1[j] - 3 * p2[j] + p3[j]) * t ** 3) for j in (0, 1)))
    out.append(points[-1])
    return out


def taper(n, w, start=0.15, reach=0.55):
    return [w * (start + (1 - start) * min(1.0, i / (n * reach)) ** 0.8) for i in range(n)]


# Tongue styles (all but "straight" are parameters for Head._tongue):
#   length  stalk length, in head widths      amp/waves  how far and how often the stalk flicks
#   fork    fork length                        spread     how far the forks splay at the split
#   curl    how much the forks keep turning outward toward their tips
#   hw0/hw1 stalk half-width at the mouth / at the split
TONGUES = {
    "wave": dict(),  # T1: one gentle S-flick (the current tongue)
    "arc": dict(length=1.35, amp=-0.3, waves=0.5, fork=0.62, spread=0.55, curl=0.35),  # T2: one upward arc (the pick)
    "double": dict(length=1.95, amp=0.12, waves=2.0, fork=0.6, spread=0.55, curl=0.35),  # T3: two flicks, longer
    "hook": dict(length=1.05, amp=0.0, fork=0.8, spread=0.3, curl=1.25),  # T4: straight stalk, hooked forks
    "splay": dict(length=0.6, amp=0.0, fork=1.05, spread=0.72, curl=0.5),  # T5: short stalk, long splayed forks
    "lash": dict(length=2.2, amp=0.2, waves=1.25, fork=0.42, spread=0.5, curl=0.25, hw0=0.1, hw1=0.05),  # T6: thin whip
    "straight": None,  # T7: the original straight Y, for reference
}


class Head:
    """The snake-shaped head at the end of a centerline, plus what screen dots must avoid."""

    def __init__(self, c, w, tongue="arc"):
        hx, hy = c[-1]
        bx, by = c[max(0, len(c) - 6)]
        m = math.hypot(hx - bx, hy - by) or 1
        self.ux, self.uy = (hx - bx) / m, (hy - by) / m
        self.w = w
        self.poly, (self.cx, self.cy, self.L, self.R, vx, vy) = head_outline(hx, hy, self.ux, self.uy, w)
        self.up = min(((vx, vy), (-vx, -vy)), key=lambda v: (round(v[1], 3), v[0]))
        self.tx, self.ty = self.cx + self.ux * self.L * 0.97, self.cy + self.uy * self.L * 0.97
        self.tongue = self._straight(w) if tongue == "straight" else self._tongue(w, **TONGUES[tongue])
        # Kept for callers that read the old straight-tongue points (bounds, crop).
        self.fx, self.fy = self.tongue[0][-1][0]
        self.forks = [line[-1][0] for line in self.tongue[1:]]

    def _straight(self, w):
        """The original tongue: a straight stalk and a straight Y fork, constant width."""
        ux, uy = self.ux, self.uy
        hw = w * 0.11
        fx, fy = self.tx + ux * w * 0.9, self.ty + uy * w * 0.9
        ang, arm = math.atan2(uy, ux), w * 0.55
        stalk = [((self.tx, self.ty), hw), ((fx, fy), hw)]
        return [stalk] + [[((fx, fy), hw), ((fx + math.cos(ang + sd_) * arm, fy + math.sin(ang + sd_) * arm), hw)]
                          for sd_ in (-0.6, 0.6)]

    def _tongue(self, w, length=1.3, amp=0.13, waves=1.0, fork=0.62, spread=0.62, curl=0.35, hw0=0.14, hw1=0.09):
        """A serpentine tongue: a stalk that flicks in one gentle S-wave, splitting into two
        forks that flare apart and curl outward at their tips.
        Returns centerlines as lists of ((x, y), half_width)."""
        ux, uy = self.ux, self.uy
        nx, ny = -uy, ux
        stalk_len, fork_len = w * length, w * fork
        base_hw, tip_hw = w * hw0, w * hw1
        stalk = []
        n = 28
        for k in range(n + 1):
            t = k / n
            along = stalk_len * t
            # Sine wave that starts flat at the mouth and grows toward the fork.
            off = w * amp * math.sin(2 * math.pi * waves * t) * t ** 0.8
            hw = base_hw + (tip_hw * 1.25 - base_hw) * t
            stalk.append(((self.tx + ux * along + nx * off, self.ty + uy * along + ny * off), hw))
        (fx, fy), fhw = stalk[-1]
        # Direction of the stalk at its end, so the forks continue the flick.
        (ax, ay), _ = stalk[-3]
        dx, dy = fx - ax, fy - ay
        m = math.hypot(dx, dy) or 1
        dx, dy = dx / m, dy / m
        base = math.atan2(dy, dx)
        lines = [stalk]
        for side in (-1, 1):
            pts = []
            for k in range(n + 1):
                t = k / n
                # Each fork leaves at +/- spread and keeps turning outward (curl), like a hook.
                a = base + side * (spread * t ** 0.6 + curl * t ** 2.2)
                if k == 0:
                    x, y = fx, fy
                else:
                    x, y = pts[-1][0]
                    seg = fork_len / n
                    x, y = x + math.cos(a) * seg, y + math.sin(a) * seg
                hw = fhw * (1 - t) + w * 0.03 * t  # taper to a fine point
                pts.append(((x, y), hw))
            lines.append(pts)
        return lines

    def blocks(self, x, y, r, gap, body=False):
        if inside(self.poly, x, y):
            return True
        if not body and poly_dist(self.poly, x, y) < r + gap:
            return True
        t = min(seg_dist(x, y, *p0, *p1) - h1
                for line in self.tongue for (p0, _), (p1, h1) in zip(line, line[1:]))
        return t < r + gap

    def svg(self, ink, paper, eye="dot"):
        w = self.w
        ex = self.cx + self.ux * self.L * 0.22 + self.up[0] * self.R * 0.42
        ey = self.cy + self.uy * self.L * 0.22 + self.up[1] * self.R * 0.42
        head = f'<path d="M{" L".join(f"{f(a)} {f(b)}" for a, b in self.poly)} Z" fill="{ink}"/>'
        tongue = "".join(
            f'<line x1="{f(p0[0])}" y1="{f(p0[1])}" x2="{f(p1[0])}" y2="{f(p1[1])}" stroke="{ink}" '
            f'stroke-width="{f(2 * h1)}" stroke-linecap="round"/>'
            for line in self.tongue for (p0, _), (p1, h1) in zip(line, line[1:]))
        return head + self.eye(ex, ey, ink, paper, eye) + tongue

    def _reptile(self, ex, ey, ink, paper, tilt):
        """A reptile eye, after the reference: a large almond, pointed at both corners and
        tilted, holding a tall slit pupil that nearly spans it, with a small highlight
        notched into the pupil's upper edge.
        tilt > 0 raises the corner toward the snout; tilt < 0 lowers it (a harder look)."""
        w = self.w
        ua, up = (self.ux, self.uy), self.up
        ex, ey = ex - ua[0] * w * 0.06, ey - ua[1] * w * 0.06

        def place(a, b, deg):
            t = math.radians(deg)
            a, b = a * math.cos(t) - b * math.sin(t), a * math.sin(t) + b * math.cos(t)
            return ex + ua[0] * a + up[0] * b, ey + ua[1] * a + up[1] * b

        def path(pts):
            return "M" + " L".join(f"{f(x)} {f(y)}" for x, y in pts) + " Z"

        def lens(half_a, half_b, lower=1.0, k_top=0.8, k_bot=0.8, n=48):
            top = [(-half_a + 2 * half_a * i / n, half_b * math.sin(math.pi * i / n) ** k_top) for i in range(n + 1)]
            bot = [(half_a - 2 * half_a * i / n, -half_b * lower * math.sin(math.pi * i / n) ** k_bot) for i in range(1, n)]
            return top + bot

        eye = lens(w * 0.52, w * 0.3, lower=0.92)
        # Pupil: a vertical lens the full height of the eye, slightly forward of centre.
        ph, pw = w * 0.29, w * 0.13
        pupil = [(b, a) for a, b in lens(ph, pw, k_top=0.9, k_bot=0.9)]
        px = w * 0.06
        lean = tilt * 0.5
        hx, hy = place(px + pw * 0.38, ph * 0.5, lean)
        return (f'<path d="{path([place(a, b, tilt) for a, b in eye])}" fill="{paper}"/>'
                f'<path d="{path([place(a + px, b, lean) for a, b in pupil])}" fill="{ink}"/>'
                + dot(hx, hy, pw * 0.3, paper))

    def eye(self, ex, ey, ink, paper, style):
        """Eye styles, all knocked out of the solid head:
          dot      a round dot (the original)
          ring     a round eye with an ink pupil
          slit     a round eye with a vertical slit pupil, like a viper
          almond   a pointed almond aligned to the head, with a slit pupil
          lid      a hooded eye: round, its top cut flat by a brow
          line     a short closed-eye line
          halftone three dots shrinking toward the snout, echoing the screen"""
        w, ux, uy = self.w, self.ux, self.uy
        ang = math.degrees(math.atan2(uy, ux))
        if style == "dot":
            return dot(ex, ey, w * 0.24, paper)
        if style == "ring":
            return dot(ex, ey, w * 0.3, paper) + dot(ex + ux * w * 0.07, ey + uy * w * 0.07, w * 0.15, ink)
        if style == "slit":
            r = w * 0.3
            return (dot(ex, ey, r, paper)
                    + f'<ellipse cx="{f(ex)}" cy="{f(ey)}" rx="{f(r * 0.22)}" ry="{f(r * 0.84)}" fill="{ink}" '
                      f'transform="rotate({f(ang)} {f(ex)} {f(ey)})"/>')
        if style == "almond":
            L, R = w * 0.42, w * 0.2
            pts = []
            for k in range(40):
                t = 2 * math.pi * k / 40
                along, across = L * math.cos(t), R * math.sin(t) * (1 - 0.35 * abs(math.cos(t)) ** 2)
                pts.append((ex + ux * along - uy * across, ey + uy * along + ux * across))
            almond = f'<path d="M{" L".join(f"{f(a)} {f(b)}" for a, b in pts)} Z" fill="{paper}"/>'
            pupil = (f'<ellipse cx="{f(ex + ux * w * 0.05)}" cy="{f(ey + uy * w * 0.05)}" rx="{f(R * 0.34)}" '
                     f'ry="{f(R * 0.95)}" fill="{ink}" transform="rotate({f(ang)} {f(ex + ux * w * 0.05)} {f(ey + uy * w * 0.05)})"/>')
            return almond + pupil
        if style == "lid":
            r = w * 0.3
            cid = f"lid{int(ex)}{int(ey)}"
            # Keep the lower 70% of a round eye: the brow cuts across its top at the head's angle.
            nx, ny = -uy, ux
            up = self.up
            cut_x, cut_y = ex + up[0] * r * 0.4, ey + up[1] * r * 0.4
            big = r * 4
            keep = (f"M{f(cut_x - ux * big)} {f(cut_y - uy * big)} L{f(cut_x + ux * big)} {f(cut_y + uy * big)} "
                    f"L{f(cut_x + ux * big - up[0] * big)} {f(cut_y + uy * big - up[1] * big)} "
                    f"L{f(cut_x - ux * big - up[0] * big)} {f(cut_y - uy * big - up[1] * big)} Z")
            return (f'<clipPath id="{cid}"><path d="{keep}"/></clipPath>'
                    f'<circle cx="{f(ex)}" cy="{f(ey)}" r="{f(r)}" fill="{paper}" clip-path="url(#{cid})"/>')
        if style == "line":
            L = w * 0.3
            dy = w * 0.05
            x0, y0 = ex - ux * L, ey - uy * L
            x1, y1 = ex + ux * L, ey + uy * L
            mx, my = ex + self.up[0] * dy * 3, ey + self.up[1] * dy * 3
            return (f'<path d="M{f(x0)} {f(y0)} Q{f(mx)} {f(my)} {f(x1)} {f(y1)}" fill="none" stroke="{paper}" '
                    f'stroke-width="{f(w * 0.12)}" stroke-linecap="round"/>')
        if style in ("reptile", "reptile-down"):
            return self._reptile(ex, ey, ink, paper, tilt=18 if style == "reptile" else -16)
        if style == "halftone":
            out = ""
            for i, r in enumerate((0.24, 0.15, 0.08)):
                out += dot(ex + ux * w * 0.42 * i - ux * w * 0.1, ey + uy * w * 0.42 * i - uy * w * 0.1, w * r, paper)
            return out
        raise ValueError(style)


def sd(samples, x, y):
    """Signed distance to the body edge: negative inside."""
    return min(math.hypot(x - a, y - b) - w for (a, b), w in samples)


def coverage(samples, x0, y0, size, ss=6):
    hit = 0
    for sy in range(ss):
        for sx in range(ss):
            if sd(samples, x0 + (sx + 0.5) * size / ss, y0 + (sy + 0.5) * size / ss) < 0:
                hit += 1
    return hit / (ss * ss)


def wave_line():
    return [(x * SIZE, y * SIZE) for x, y in fit(shape_wave())]


# ----------------------------------------------------------------------------- variants


def glide_original(ink, paper, n=23, bg=0.2, body=0.46):
    k = SIZE / 512
    c = catmull([(x * k, y * k) for x, y in [(96, 446), (220, 446), (330, 432), (372, 392), (344, 350), (256, 334), (168, 318),
                                             (140, 276), (168, 236), (256, 222), (330, 204), (356, 164), (350, 118)]])
    L = len(c)
    widths = [(4 + 30 * min(1.0, i / (L * 0.9)) ** 0.7) * k for i in range(L)]
    samples = list(zip(c[::2], widths[::2]))
    head = Head(c, widths[-1])
    p = SIZE / n
    out = []
    for gy in range(n):
        for gx in range(n):
            x, y = (gx + 0.5) * p, (gy + 0.5) * p
            t = max(0.0, min(1.0, 0.5 - sd(samples, x, y) / p))  # the round-3 ramp across the edge
            r = (bg + (body - bg) * t) * p
            if head.blocks(x, y, r, 0.14 * p, body=t > 0.35):
                continue
            out.append(dot(x, y, r, ink))
    return "".join(out) + head.svg(ink, paper)


def wave_6(ink, paper, n=6, bg=0.2, body=0.6, half=0.085):
    """Larger snake dots: full body dots are 1.2 pitches across, so neighbours merge."""
    c = wave_line()
    widths = taper(len(c), half * SIZE)
    samples = list(zip(c[::2], widths[::2]))
    head = Head(c, widths[-1])
    p = SIZE / n
    out = []
    for gy in range(n):
        for gx in range(n):
            x, y = (gx + 0.5) * p, (gy + 0.5) * p
            cov = coverage(samples, gx * p, gy * p, p)
            r = p * math.sqrt(bg * bg + (body * body - bg * bg) * cov)
            if head.blocks(x, y, r, 0.12 * p, body=cov > 0.3):
                continue
            out.append(dot(x, y, r, ink))
    return "".join(out) + head.svg(ink, paper)


def screen_dots(samples, head, n, bg, clear):
    """The n x n background screen, kept clear of the body by `clear` pixels."""
    p = SIZE / n
    out = []
    for gy in range(n):
        for gx in range(n):
            x, y = (gx + 0.5) * p, (gy + 0.5) * p
            r = bg * p
            if sd(samples, x, y) < r + clear or head.blocks(x, y, r, 0.14 * p):
                continue
            out.append(dot(x, y, r, ""))
    return out, p


def wave_9_screen(ink, paper, n=9, bg=0.2, half=0.072, density=2.7, angle=45):
    """The body is its own fine halftone at a print-screen angle; dot area tracks coverage."""
    c = wave_line()
    widths = taper(len(c), half * SIZE, start=0.1)
    samples = list(zip(c[::2], widths[::2]))
    head = Head(c, widths[-1])
    bgd, p = screen_dots(samples, head, n, bg, 0.12 * SIZE / n)
    q = p / density
    a = math.radians(angle)
    ca, sa = math.cos(a), math.sin(a)
    out = [d.replace('fill=""', f'fill="{ink}"') for d in bgd]
    span = int(SIZE * 1.5 / q)
    for i in range(-span, span):
        for j in range(-span, span):
            u, v = (i + 0.5) * q, (j + 0.5) * q
            x, y = SIZE / 2 + u * ca - v * sa, SIZE / 2 + u * sa + v * ca
            if not (0 <= x <= SIZE and 0 <= y <= SIZE) or sd(samples, x, y) > q:
                continue
            cov = coverage(samples, x - q / 2, y - q / 2, q)
            r = q * 0.5 * math.sqrt(cov) * 1.08
            if r < q * 0.12 or head.blocks(x, y, r, 0.06 * q, body=True):
                continue
            out.append(dot(x, y, r, ink))
    return "".join(out) + head.svg(ink, paper)


def wave_9_rows(ink, paper, n=9, bg=0.2, half=0.072, density=2.7):
    """The body is rows of dots laid across the snake at even steps along its length."""
    c = wave_line()
    widths = taper(len(c), half * SIZE, start=0.1)
    samples = list(zip(c[::2], widths[::2]))
    head = Head(c, widths[-1])
    bgd, p = screen_dots(samples, head, n, bg, 0.12 * SIZE / n)
    q = p / density
    out = [d.replace('fill=""', f'fill="{ink}"') for d in bgd]
    acc, placed, nxt = 0.0, [], 0.0
    for i in range(1, len(c)):
        (x0, y0), (x1, y1) = c[i - 1], c[i]
        acc += math.hypot(x1 - x0, y1 - y0)
        if acc < nxt:
            continue
        nxt += q
        dx, dy = x1 - x0, y1 - y0
        m = math.hypot(dx, dy) or 1
        nx, ny = -dy / m, dx / m
        w = widths[i]
        k = max(1, round(2 * w / q))  # dots across at this point of the body
        r = min(q * 0.46, w / k * 0.96)
        for j in range(k):
            o = (j - (k - 1) / 2) * (2 * w / k)
            x, y = x1 + nx * o, y1 + ny * o
            if any(math.hypot(x - a, y - b) < (r + rb) * 0.86 for a, b, rb in placed[-60:]):
                continue  # the inside of a bend crowds; drop dots that would collide
            if head.blocks(x, y, r, 0.06 * q, body=True):
                continue
            placed.append((x, y, r))
    out += [dot(x, y, r, ink) for x, y, r in placed]
    return "".join(out) + head.svg(ink, paper)


VARIANTS = {"glide-original": glide_original, "wave-6": wave_6, "wave-9-screen": wave_9_screen, "wave-9-rows": wave_9_rows}


def main():
    os.makedirs(OUT, exist_ok=True)
    for name, fn in VARIANTS.items():
        for theme, (ink, paper) in INK.items():
            open(os.path.join(OUT, f"{name}-{theme}.svg"), "w").write(svg(fn(ink, paper), paper, f"py-tone mark: {name}"))
        print("built", name)


if __name__ == "__main__":
    main()
