"""Build the "How It Works" infographics (docs/pipeline/*.svg and docs/pipeline/light/*.svg).

Every glyph grid and number in the diagrams is produced by the real pytone code on a
single subject (see SUBJECTS below), so the diagrams can't drift from the tool.

Run from the repo root:  uv run python design/scripts/make_pipeline.py
"""

import base64
import io
import os
import re
import subprocess
import tempfile
from collections import Counter

from PIL import Image, ImageDraw

from pytone.contracts import RGB
from pytone.core import (
    DEFAULT_CHARS,
    HTML_ROW_FACTOR,
    SVG_ROW_FACTOR,
    TERMINAL_ROW_FACTOR,
    get_color_data,
    load_image,
    pixels_to_ascii,
    resize_image,
)

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # repo root
DESIGN = os.path.join(ROOT, "design")
# Subject for every diagram, plus the color boost it uses in the gallery (-s / -b), so the
# colored stages look as rich as the gallery pieces. Override with PYTONE_SUBJECT.
SUBJECTS = {
    "earth": (os.path.join(DESIGN, "sources", "bluemarble.jpg"), "bluemarble.jpg", dict(saturation=1.5, brightness=1.4)),
    "sun": (os.path.join(DESIGN, "sources", "sun.png"), "sun.png", dict(saturation=1.5, brightness=1.8)),
    "helix": (os.path.join(DESIGN, "sources", "helix.png"), "helix.png", dict(saturation=1.5, brightness=1.5)),
    "jupiter": (os.path.join(DESIGN, "sources", "jupiter.png"), "jupiter.png", dict(saturation=1.6, brightness=1.4)),
}
SUBJECT = os.environ.get("PYTONE_SUBJECT", "jupiter")
SRC, SRC_NAME, BOOST = SUBJECTS[SUBJECT]
OUT = os.environ.get("PYTONE_OUT") or os.path.join(ROOT, "docs", "pipeline")

W = 880
M = 1  # outer margin: content runs edge to edge (1px keeps 1px borders from clipping)
CW = W - 2 * M

SANS = '-apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif'
MONO = '"SFMono-Regular", Menlo, Consolas, "Liberation Mono", monospace'
ART = '"Courier New", Courier, monospace'

THEMES = {
    "dark": dict(
        bg="#0d1117", panel="#161b22", border="#30363d", text="#e6edf3", muted="#9198a1",
        accent="#c8a58e", chip="#21262d", screen="#010409", screen_text="#c9d1d9",
        good="#56d364", bad="#ff7b72", dir="",
    ),
    "light": dict(
        bg="#ffffff", panel="#f6f8fa", border="#d0d7de", text="#1f2328", muted="#59636e",
        accent="#8a5a42", chip="#eaeef2", screen="#0d1117", screen_text="#c9d1d9",
        good="#116329", bad="#cf222e", dir="light",
    ),
}

STAGES = ["image", "resize", "grayscale", "glyph ramp", "color", "output"]
CIRCLES = " ·∘○◯●"


def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def f(n: float) -> str:
    return f"{n:.1f}".rstrip("0").rstrip(".")


# ----------------------------------------------------------------------------- data

IMG = load_image(SRC)


def data_uri(im: Image.Image, fmt: str = "JPEG", **kw) -> str:
    buf = io.BytesIO()
    im.save(buf, fmt, **kw)
    mime = "image/jpeg" if fmt == "JPEG" else "image/png"
    return f"data:{mime};base64," + base64.b64encode(buf.getvalue()).decode()


def thumb(width: int) -> Image.Image:
    return IMG.resize((width, round(IMG.height * width / IMG.width)), Image.Resampling.LANCZOS)


def grid(width: int, rf: float, chars: str = CIRCLES, **kw):
    """Real color data, straight from get_color_data."""
    return get_color_data(SRC, width=width, chars=chars, row_factor=rf, **{**BOOST, **kw})


def gray_rows(width: int, rf: float, chars: str = CIRCLES, im: Image.Image | None = None):
    im = resize_image(im or IMG, width, rf).convert("L")
    s = pixels_to_ascii(im, chars)
    return [s[i : i + width] for i in range(0, len(s), width)]


def hexc(c: RGB) -> str:
    return "#%02x%02x%02x" % tuple(c)


# ----------------------------------------------------------------------------- drawing


class Doc:
    def __init__(self, t: dict, name: str, title: str, desc: str):
        self.t, self.name, self.title, self.desc = t, name, title, desc
        self.parts: list[str] = []

    def add(self, s: str):
        self.parts.append(s)

    # --- primitives
    def rect(self, x, y, w, h, fill="none", stroke=None, rx=0, sw=1, extra=""):
        s = f' stroke="{stroke}" stroke-width="{sw}"' if stroke else ""
        self.add(f'<rect x="{f(x)}" y="{f(y)}" width="{f(w)}" height="{f(h)}" rx="{rx}" fill="{fill}"{s} {extra}/>')

    def line(self, x1, y1, x2, y2, stroke, sw=1.5, extra=""):
        self.add(f'<line x1="{f(x1)}" y1="{f(y1)}" x2="{f(x2)}" y2="{f(y2)}" stroke="{stroke}" stroke-width="{sw}" {extra}/>')

    def arrow(self, x1, y1, x2, y2, color=None, sw=2):
        c = color or self.t["muted"]
        self.line(x1, y1, x2 - 7, y2, c, sw)
        self.add(f'<path d="M{f(x2)} {f(y2)} l-9 -5.5 v11 z" fill="{c}"/>')

    def text(self, x, y, s, size=15, fill=None, weight=400, anchor="start", family=SANS, spacing=None):
        fill = fill or self.t["text"]
        ls = f' letter-spacing="{spacing}"' if spacing else ""
        self.add(
            f'<text x="{f(x)}" y="{f(y)}" font-size="{size}" font-weight="{weight}" fill="{fill}" '
            f'text-anchor="{anchor}" font-family=\'{family}\'{ls}>{esc(s)}</text>'
        )

    # --- rich text with **bold** and `code`, greedy word wrap. Returns y after the block.
    def rich(self, x, y, width, markup, size=15, fill=None, gap=1.45, anchor="start", dry=False):
        fill = fill or self.t["text"]
        words = self._words(markup)
        lines, cur, cur_w = [], [], 0.0
        space = size * 0.3
        for w in words:
            ww = sum(len(txt) * size * (0.62 if st == "c" else 0.585 if st == "b" else 0.55) for txt, st in w)
            if cur and cur_w + space + ww > width:
                lines.append(cur)
                cur, cur_w = [], 0.0
            cur_w += (space if cur else 0) + ww
            cur.append(w)
        if cur:
            lines.append(cur)
        if dry:
            return y + len(lines) * size * gap
        for i, ln in enumerate(lines):
            spans = []
            for j, w in enumerate(ln):
                for txt, st in w:
                    a = {"n": "", "b": f' font-weight="700"', "c": f' font-family=\'{MONO}\' fill="{self.t["accent"]}"'}[st]
                    spans.append(f"<tspan{a}>{esc(txt)}</tspan>")
                if j < len(ln) - 1:
                    spans.append("<tspan> </tspan>")
            self.add(
                f'<text x="{f(x)}" y="{f(y + i * size * gap)}" font-size="{size}" fill="{fill}" '
                f'text-anchor="{anchor}" xml:space="preserve" font-family=\'{SANS}\'>{"".join(spans)}</text>'
            )
        return y + len(lines) * size * gap

    @staticmethod
    def _words(markup):
        segs = re.findall(r"\*\*.+?\*\*|`.+?`|[^*`]+", markup)
        words, cur = [], []
        for seg in segs:
            if seg.startswith("**"):
                st, body = "b", seg[2:-2]
            elif seg.startswith("`"):
                st, body = "c", seg[1:-1]
            else:
                st, body = "n", seg
            if st == "c":
                cur.append((body, st))
                continue
            for part in re.split(r"(\s+)", body):
                if not part:
                    continue
                if part.isspace():
                    if cur:
                        words.append(cur)
                        cur = []
                else:
                    cur.append((part, st))
        if cur:
            words.append(cur)
        return words

    # --- composites
    def panel(self, x, y, w, h, label=None, fill=None):
        self.rect(x, y, w, h, fill or self.t["panel"], self.t["border"], rx=10)
        if label:
            self.text(x + 18, y + 28, label, 13, self.t["accent"], 700, spacing=1.2)

    def open(self, x, y, w, label=None):
        """Start a panel whose height is decided once its content is drawn."""
        self.parts.append("")
        idx = len(self.parts) - 1
        if label:
            self.text(x + 18, y + 28, label, 13, self.t["accent"], 700, spacing=1.2)
        return (idx, x, y, w)

    def close(self, p, bottom, pad=18, h=None):
        idx, x, y, w = p
        h = h if h is not None else bottom - y + pad
        self.parts[idx] = (
            f'<rect x="{f(x)}" y="{f(y)}" width="{f(w)}" height="{f(h)}" rx="10" '
            f'fill="{self.t["panel"]}" stroke="{self.t["border"]}"/>'
        )
        return h

    def chip(self, x, y, s, size=13, pad=8, fill=None, color=None):
        w = len(s) * size * 0.62 + 2 * pad
        self.rect(x, y, w, size + 10, fill or self.t["chip"], rx=5)
        self.add(
            f'<text x="{f(x + pad)}" y="{f(y + size + 1)}" font-size="{size}" fill="{color or self.t["accent"]}" '
            f"font-family='{MONO}' xml:space=\"preserve\">{esc(s)}</text>"
        )
        return w

    def screen(self, x, y, w, rows, rf, colored=True, fg=None, pad=8, bar=None, frame=True):
        """Draw glyph rows on a dark 'screen'. rows: list of [(char,(r,g,b))] or list[str].
        Cell shape follows rf (cell width/height), so the art has the proportion it has in its medium."""
        ncols = len(rows[0])
        cw = (w - 2 * pad) / ncols
        ch = cw / rf
        bar_h = 24 if bar else 0
        h = len(rows) * ch + 2 * pad + bar_h
        if frame:
            self.rect(x, y, w, h, self.t["screen"], self.t["border"], rx=8)
        if bar:
            self.line(x, y + bar_h, x + w, y + bar_h, self.t["border"], 1)
            for k, col in enumerate(("#ff5f56", "#ffbd2e", "#27c93f")):
                self.add(f'<circle cx="{f(x + 14 + k * 14)}" cy="{f(y + 12)}" r="4" fill="{col}"/>')
            self.text(x + w - 10, y + 16, bar, 12, "#9198a1", anchor="end", family=MONO)
        y = y + bar_h
        fs = cw / 0.6
        fg = fg or self.t["screen_text"]
        for r, row in enumerate(rows):
            cy = y + pad + r * ch + ch / 2
            xs, spans = [], []
            for c, cell in enumerate(row):
                ch_, col = (cell if colored and not isinstance(cell, str) else (cell, None))
                if ch_.strip() == "":
                    continue
                xs.append(f(x + pad + c * cw + cw / 2))
                spans.append(f'<tspan fill="{hexc(col)}">{esc(ch_)}</tspan>' if col else esc(ch_))
            if xs:
                self.add(
                    f'<text x="{" ".join(xs)}" y="{f(cy + fs * 0.33)}" font-size="{f(fs)}" fill="{fg}" '
                    f"text-anchor=\"middle\" font-family='{ART}'>{''.join(spans)}</text>"
                )
        return h

    def image(self, x, y, w, h, uri, rx=6, extra="", pix=False):
        cid = f"c{len(self.parts)}"
        self.add(f'<clipPath id="{cid}"><rect x="{f(x)}" y="{f(y)}" width="{f(w)}" height="{f(h)}" rx="{rx}"/></clipPath>')
        style = ' style="image-rendering:pixelated"' if pix else ""
        self.add(
            f'<image x="{f(x)}" y="{f(y)}" width="{f(w)}" height="{f(h)}" href="{uri}" '
            f'clip-path="url(#{cid})" preserveAspectRatio="none"{style} {extra}/>'
        )

    def badge(self, cx, cy, n, r=11, fill=None):
        self.add(f'<circle cx="{f(cx)}" cy="{f(cy)}" r="{r}" fill="{fill or self.t["accent"]}"/>')
        self.add(
            f'<text x="{f(cx)}" y="{f(cy + 4.5)}" font-size="13" font-weight="700" text-anchor="middle" '
            f"fill=\"{self.t['bg']}\" font-family='{SANS}'>{n}</text>"
        )

    def header(self, step, title, sub, tracker=True, kicker=None):
        t = self.t
        up = 0 if step else -34  # the overview has no kicker line, so everything moves up
        if step:
            self.text(M, 50, kicker or f"STEP {step} OF 6", 13, t["accent"], 700, spacing=1.5)
        self.text(M, 92 + up, title, 32, t["text"], 700)
        y = self.rich(M, 124 + up, CW, sub, size=17, fill=t["muted"], gap=1.4)
        if tracker and step:
            x0, y0, gap = W - M - 8 - 5 * 30, 46, 30
            self.line(x0, y0, x0 + 5 * gap, y0, t["border"], 2)
            for i in range(6):
                cx = x0 + i * gap
                if i + 1 == step:
                    self.add(f'<circle cx="{cx}" cy="{y0}" r="8" fill="{t["accent"]}"/>')
                else:
                    self.add(f'<circle cx="{cx}" cy="{y0}" r="5" fill="{t["bg"]}" stroke="{t["muted"]}" stroke-width="1.5"/>')
        return y + 16

    def footer(self, y, s):
        self.text(M, y + 4, s, 13, self.t["muted"], family=MONO)
        return y + 60

    def render(self, height) -> str:
        # No canvas background: the diagrams are transparent so they sit on whatever page
        # embeds them (the README picks the light/dark file via prefers-color-scheme).
        head = (
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {f(height)}" width="{W}" height="{f(height)}" '
            f'role="img" aria-labelledby="t d"><title id="t">{esc(self.title)}</title><desc id="d">{esc(self.desc)}</desc>'
        )
        return head + "".join(self.parts) + "</svg>"


def bullets(d: Doc, x, y, width, items, size=15, gap=10, mark=None, color=None):
    mark = mark or d.t["accent"]
    for it in items:
        d.add(f'<circle cx="{f(x + 4)}" cy="{f(y - size * 0.32)}" r="3" fill="{color or mark}"/>')
        y = d.rich(x + 18, y, width - 18, it, size=size) + gap
    return y


# ----------------------------------------------------------------------------- steps

GAP = 16


def pair(d, y, lw, left, right, pad=18):
    """left/right: callables (panel, x, w) -> bottom y. Panels get the taller height."""
    rw = CW - lw - GAP
    p1 = d.open(M, y, lw, left[0])
    p2 = d.open(M + lw + GAP, y, rw, right[0])
    b1 = left[1](M, lw, y)
    b2 = right[1](M + lw + GAP, rw, y)
    h = max(b1, b2) - y + pad
    d.close(p1, 0, h=h)
    d.close(p2, 0, h=h)
    return y + h + GAP


def single(d, y, label, build, pad=18):
    p = d.open(M, y, CW, label)
    b = build(M, CW, y)
    d.close(p, b, pad)
    return b + pad + GAP


def know(d, y, left_items, right_items, label="KNOW BEFORE YOU RUN", size=14):
    def build(x, w, y0):
        colw = (w - 36 - 24) / 2
        b1 = bullets(d, x + 18, y0 + 58, colw, left_items, size=size, gap=8)
        b2 = bullets(d, x + 18 + colw + 24, y0 + 58, colw, right_items, size=size, gap=8)
        return max(b1, b2) - 8

    return single(d, y, label, build)


def disc_rows(width, rf):
    im = Image.new("RGB", (240, 240), "black")
    ImageDraw.Draw(im).ellipse((20, 20, 220, 220), fill="white")
    return gray_rows(width, rf, " +#", im=im)


def step_overview(t):
    d = Doc(t, "00-pipeline", "The PyTone pipeline",
            "Six stages turn an image into text: image, resize, grayscale, glyph ramp, color, and output "
            "as text, ANSI, HTML or SVG. Each stage has its own flags.")
    y = d.header(0, "From picture to glyphs", "Six small stages, each with one job and its own flags. "
                 "Every picture below is the real output of that stage.", tracker=False)
    top = y + 6
    per_row, gap = 3, 14
    cw_ = (CW - (per_row - 1) * gap) / per_row
    cols = 24
    small = resize_image(IMG, cols, TERMINAL_ROW_FACTOR)
    inner = cw_ - 28
    # Fit the subject inside the image well: 224 tall at most, never wider than the well.
    aspect = IMG.height / IMG.width
    th = min(224.0, (inner - 20) * aspect)
    tw = th / aspect
    well_h = th + 20
    gray_g = gray_rows(cols, TERMINAL_ROW_FACTOR)
    col_g = grid(cols, TERMINAL_ROW_FACTOR)
    meta = [
        ("Image", "Open it and normalize it.", ["path"]),
        ("Resize", "Scale to a grid of columns.", ["-w"]),
        ("Grayscale", "One brightness per cell.", ["--invert"]),
        ("Glyph ramp", "Brightness picks a character.", ["-c"]),
        ("Color", "Give each glyph a color.", ["-s", "-b", "--gradient", "--rainbow"]),
        ("Output", "Write it where it will live.", ["-m", "-o", "--pixel-width"]),
    ]
    text_y = 48 + well_h + 28

    def card_bottom(what, flags):
        b = d.rich(0, text_y, inner, what, 15, gap=1.35, dry=True)
        return d.rich(0, b + 6, inner, " ".join(f"`{x}`" for x in flags), 13, gap=1.5, dry=True)

    chh = max(card_bottom(w_, f_) for _, w_, f_ in meta) + 18
    for i, (name, what, flags) in enumerate(meta):
        row, col = divmod(i, per_row)
        x0 = M + col * (cw_ + gap)
        ytop = top + row * (chh + gap)
        d.panel(x0, ytop, cw_, chh)
        d.badge(x0 + 22, ytop + 26, i + 1)
        d.text(x0 + 42, ytop + 32, name, 17, t["text"], 700)
        wx, wy = x0 + 14, ytop + 48
        d.rect(wx, wy, inner, well_h, t["screen"], t["border"], rx=8)
        ix, iy = wx + (inner - tw) / 2, wy + 10
        if i == 0:
            d.image(ix, iy, tw, th, data_uri(thumb(260), quality=82), rx=4)
        elif i == 1:
            d.image(ix, iy, tw, th, data_uri(small, "PNG"), rx=2, pix=True)
        elif i == 2:
            d.image(ix, iy, tw, th, data_uri(small.convert("L"), "PNG"), rx=2, pix=True)
        elif i == 3:
            d.screen(ix, iy, tw, gray_g, TERMINAL_ROW_FACTOR, colored=False, pad=3, frame=False)
        elif i == 4:
            d.screen(ix, iy, tw, col_g, TERMINAL_ROW_FACTOR, pad=3, frame=False)
        else:
            cell = (tw - 10) / 2
            for k, lab in enumerate(("Text", "ANSI", "HTML", "SVG")):
                bx = ix + (k % 2) * (cell + 10)
                by = iy + (k // 2) * (th / 2 + 2)
                d.rect(bx, by, cell, th / 2 - 2, t["bg"], t["accent"], rx=8)
                d.text(bx + cell / 2, by + th / 4 + 4, lab, 15, t["accent"], 700, "middle", MONO)
        yy = d.rich(x0 + 14, ytop + text_y, inner, what, 15, gap=1.35)
        d.rich(x0 + 14, yy + 6, inner, " ".join(f"`{x}`" for x in flags), 13, gap=1.5)
        if col < per_row - 1:
            d.add(f'<path d="M{f(x0 + cw_ + 3)} {f(ytop + 20)} l6 6 l-6 6" fill="none" stroke="{t["muted"]}" stroke-width="2"/>')
    y = top + 2 * chh + gap + GAP

    def build(x, w, y0):
        code = 'pytone jupiter.jpg -w 110 -c " ·∘○◯●" --gradient "#3D1A4D,#FFD700" -m svg -o jupiter.svg'
        d.rect(x + 18, y0 + 42, w - 36, 40, t["screen"], t["border"], rx=8)
        d.text(x + 34, y0 + 67, code, 14, "#e6edf3", family=MONO)
        segs = [("1", "jupiter.jpg"), ("2", "-w 110"), ("4", '-c " ·∘○◯●"'), ("5", "--gradient …"), ("6", "-m svg -o …")]
        lx = x + 18
        for num, s_ in segs:
            d.badge(lx + 9, y0 + 108, num, r=9)
            d.text(lx + 26, y0 + 113, s_, 13, t["text"], family=MONO)
            lx += 26 + len(s_) * 7.9 + 26
        return d.rich(x + 18, y0 + 146, w - 36, "Step 3 has no flag of its own, because brightness is always computed. "
                      "`--invert` flips it.", 13.5, t["muted"], gap=1.35)

    y = single(d, y, "ONE COMMAND, EVERY STAGE", build)
    # End flush with the last panel so nothing separates it from the README code block below.
    return d, y - GAP + 1


def step_image(t):
    d = Doc(t, "01-image", "Step 1: Image",
            "PyTone opens the source file and normalizes it: EXIF rotation applied, first frame only, "
            "transparency flattened onto black, converted to RGB.")
    y = d.header(1, "Image", "Pick a picture. PyTone opens it, then **normalizes it** so every later step sees "
                 "one upright, opaque, three-channel bitmap.")
    top = y + 4

    def src(x, w, y0):
        tw_ = 180
        th_ = tw_ * IMG.height / IMG.width
        d.image(x + (w - tw_) / 2, y0 + 44, tw_, th_, data_uri(thumb(220), quality=82))
        cy = y0 + 44 + th_
        d.text(x + w / 2, cy + 26, SRC_NAME, 14, t["text"], 600, "middle", MONO)
        d.text(x + w / 2, cy + 46, f"{IMG.width} × {IMG.height} px", 13, t["muted"], anchor="middle", family=MONO)
        d.text(x + w / 2, cy + 70, "JPEG · PNG · GIF · WebP · BMP", 13, t["muted"], anchor="middle")
        return cy + 70

    def fixes(x, w, y0):
        cards = [
            ("Orientation", "EXIF rotation is applied, so phone photos come in upright.", "rot"),
            ("One frame", "Animated GIFs and multi-frame files use the first frame only.", "frames"),
            ("Opaque", "Transparent pixels are composited onto black, never left empty.", "alpha"),
            ("RGB", "Every pixel becomes three 8-bit channels: red, green and blue.", "rgb"),
        ]
        cw_, chh = (w - 36 - 14) / 2, 134
        for i, (h, body, icon) in enumerate(cards):
            cx = x + 18 + (i % 2) * (cw_ + 14)
            cy = y0 + 46 + (i // 2) * (chh + 12)
            d.rect(cx, cy, cw_, chh, t["bg"], t["border"], rx=8)
            ix, iy = cx + 14, cy + 14
            if icon == "rot":
                d.rect(ix + 4, iy + 8, 20, 30, "none", t["muted"], rx=3, sw=2, extra=f'transform="rotate(90 {ix + 14} {iy + 23})"')
                d.add(f'<path d="M{ix + 36} {iy + 12} a14 14 0 0 1 0 22" fill="none" stroke="{t["accent"]}" stroke-width="2.5"/>')
                d.add(f'<path d="M{ix + 36} {iy + 38} l-6 -6 l9 -1 z" fill="{t["accent"]}"/>')
            elif icon == "frames":
                for k in range(3):
                    d.rect(ix + 14 - k * 6, iy + 6 + k * 6, 26, 26, t["bg"], t["accent"] if k == 2 else t["muted"], rx=3, sw=2)
            elif icon == "alpha":
                for a in range(3):
                    for b in range(3):
                        d.rect(ix + a * 9, iy + 8 + b * 9, 9, 9, "#8b949e" if (a + b) % 2 else "#d0d7de")
                d.arrow(ix + 32, iy + 21, ix + 48, iy + 21, t["muted"], 2)
                d.rect(ix + 52, iy + 8, 27, 27, "#000", t["muted"])
            else:
                for k, col in enumerate(("#ff5555", "#3fb950", "#4c8dff")):
                    d.rect(ix + k * 20, iy + 8 + k * 4, 18, 22, col, rx=3)
            d.text(cx + 100, cy + 40, h, 17, t["text"], 700)
            d.rich(cx + 14, cy + 78, cw_ - 28, body, 13.5, t["muted"], gap=1.35)
        return y0 + 46 + 2 * chh + 12

    y = pair(d, top, 250, ("THE SOURCE", src), ("load_image() FIXES FOUR THINGS", fixes))

    def why(x, w, y0):
        b = d.rich(x + 18, y0 + 56, w - 36, "Every later step is arithmetic on pixels. Settling the awkward cases once, "
                   "up front, means a sideways phone photo or a see-through logo can't quietly corrupt the glyph grid.", 15)
        b = d.rich(x + 18, b + 14, w - 36, "**The source is the biggest lever.** Glyphs only carry brightness, so "
                   "hard light, strong shapes and a wide tonal range read best.", 15)
        return d.rich(x + 18, b + 14, w - 36, "The only required argument is the image path.", 14, t["muted"])

    def contrast(x, w, y0):
        flat = IMG.point(lambda v: 100 + v * 0.22)
        sw_ = (w - 36 - 14) / 2
        hmax = 0
        for i, (im, lab, ok) in enumerate(((IMG, "Wide tonal range", True), (flat, "Flat mid-gray", False))):
            sx = x + 18 + i * (sw_ + 14)
            rows = gray_rows(30, SVG_ROW_FACTOR, CIRCLES, im=im)
            hmax = max(hmax, d.screen(sx, y0 + 46, sw_, rows, SVG_ROW_FACTOR, colored=False))
        for i, (lab, ok) in enumerate((("Wide tonal range", True), ("Flat mid-gray", False))):
            sx = x + 18 + i * (sw_ + 14)
            d.text(sx, y0 + 46 + hmax + 26, ("✓ " if ok else "✗ ") + lab, 15, t["good"] if ok else t["bad"], 700)
        return d.rich(x + 18, y0 + 46 + hmax + 52, w - 36, "Same picture, same ramp. With the tones squeezed "
                      "together, nearly every cell lands in the same glyph.", 13.5, t["muted"], gap=1.35)

    y = pair(d, y, 360, ("WHY IT MATTERS", why), ("CHOOSE A SOURCE WITH CONTRAST", contrast))
    y = know(d, y, [
        "**Transparent areas render black.** Flatten onto white first if you want a light ground.",
        "**Prep the source, not the flags.** There is no contrast option. Levels or gamma in an image editor "
        "do that work, as they did for the gallery pieces.",
    ], [
        "**Decoding is guarded.** Pillow's decompression-bomb check stays on, and unreadable files exit with code 1.",
        "**Your image is safe.** An output path that resolves to the input image is rejected.",
    ])
    y = d.footer(y - GAP + 22, "pytone/core.py · load_image()")
    return d, y


def step_resize(t):
    d = Doc(t, "02-resize", "Step 2: Resize",
            "The image is scaled to a grid of --width columns. Rows are squashed by a row factor "
            "because text cells are taller than wide.")
    y = d.header(2, "Resize", "One glyph per cell, so **the resized image is the glyph grid**. "
                 "Width sets the detail; a row factor keeps the shape right.")
    top = y + 4
    rf = TERMINAL_ROW_FACTOR
    sw, sh = IMG.size
    gw_, gh_ = resize_image(IMG, 60, rf).size

    def what(x, w, y0):
        srcw = 150
        srch = srcw * sh / sw
        sx, sy = x + 24, y0 + 46
        d.image(sx, sy, srcw, srch, data_uri(thumb(220), quality=80))
        d.text(sx + srcw / 2, sy + srch + 22, f"{sw} × {sh} px", 13, t["muted"], anchor="middle", family=MONO)
        d.text(sx + srcw / 2, sy + srch + 42, "source", 13, t["muted"], anchor="middle")
        ax = sx + srcw + 18
        d.arrow(ax, sy + 70, ax + 112, sy + 70, t["accent"], 2.5)
        d.text(ax + 56, sy + 52, "-w 60", 15, t["accent"], 700, "middle", MONO)
        d.text(ax + 56, sy + 98, "bicubic", 13, t["muted"], anchor="middle")
        gx0, gwid = ax + 138, 168
        cwid = gwid / gw_
        chei = cwid / rf
        d.image(gx0, sy, gwid, gh_ * chei, data_uri(resize_image(IMG, gw_, rf), "PNG"), rx=2, pix=True)
        for k in range(1, gh_):
            d.line(gx0, sy + k * chei, gx0 + gwid, sy + k * chei, "#00000066", 0.6)
        for k in range(1, gw_):
            d.line(gx0 + k * cwid, sy, gx0 + k * cwid, sy + gh_ * chei, "#00000066", 0.6)
        gb = sy + gh_ * chei
        d.text(gx0 + gwid / 2, gb + 22, f"{gw_} × {gh_} cells", 13, t["muted"], anchor="middle", family=MONO)
        d.text(gx0 + gwid / 2, gb + 42, "one glyph per cell", 13, t["muted"], anchor="middle")
        fx = gx0 + gwid + 28
        fw = x + w - 18 - fx
        d.text(fx, sy + 12, "Rows follow the width", 14, t["text"], 700)
        d.rect(fx, sy + 24, fw, 62, t["bg"], t["border"], rx=6)
        d.text(fx + 12, sy + 47, "rows = height ÷ width", 13, t["accent"], family=MONO)
        d.text(fx + 12, sy + 67, "       × columns × factor", 13, t["accent"], family=MONO)
        d.text(fx, sy + 112, f"{sh} ÷ {sw} × 60 × {rf}", 13, t["muted"], family=MONO)
        d.text(fx, sy + 136, f"= {gh_} rows", 16, t["text"], 700, family=MONO)
        d.rich(fx, sy + 166, fw, "Averaging source pixels gives each cell its region's color.", 13, t["muted"], gap=1.35)
        return max(gb + 42, sy + 166 + 40)

    y = single(d, top, "WHAT HAPPENS", what)

    def squash(x, w, y0):
        sw_ = 150
        n1 = len(disc_rows(16, 1.0))
        n2 = len(disc_rows(16, rf))
        hs = []
        for i, (fac, ok, n_) in enumerate(((1.0, False, n1), (rf, True, n2))):
            sx = x + 18 + i * (sw_ + 16)
            hs.append(d.screen(sx, y0 + 46, sw_, disc_rows(16, fac), rf, colored=False, pad=10))
        hb = max(hs)
        for i, (lab, ok, n_) in enumerate((("factor 1.0", False, n1), (f"factor {rf}", True, n2))):
            sx = x + 18 + i * (sw_ + 16)
            d.text(sx, y0 + 46 + hb + 26, ("✓ " if ok else "✗ ") + lab, 15, t["good"] if ok else t["bad"], 700)
            d.text(sx, y0 + 46 + hb + 46, f"{n_} rows", 13, t["muted"], family=MONO)
        return d.rich(x + 18, y0 + 46 + hb + 76, w - 36, "A terminal cell is about **1.8× taller than it is wide**, "
                      "so each row has to cover more of the picture. Without that, a circle stretches into an oval.", 13.5, t["muted"], gap=1.35)

    def factors(x, w, y0):
        rows_ = [
            ("plain, ANSI", f"{TERMINAL_ROW_FACTOR}", "terminal cell ≈ 1 : 1.8"),
            ("html", f"{HTML_ROW_FACTOR}", "Courier New, line-height 1"),
            ("svg", f"{SVG_ROW_FACTOR:g}", "cell is w × 1.6w, so 1 ÷ 1.6"),
        ]
        ry = y0 + 50
        for mode, val, why in rows_:
            d.rect(x + 18, ry, w - 36, 64, t["bg"], t["border"], rx=8)
            d.text(x + 32, ry + 27, mode, 15, t["text"], 700)
            d.text(x + w - 32, ry + 27, val, 18, t["accent"], 700, "end", MONO)
            fv = float(val)
            d.rect(x + w - 108 - 30 * fv, ry + 16, 30 * fv, 30, "none", t["accent"], rx=2, sw=2)
            d.text(x + 32, ry + 49, why, 13, t["muted"])
            ry += 76
        return d.rich(x + 18, ry + 12, w - 36, "Chosen for you by `-m`. A wrong factor turns circles into ovals.", 13.5, t["muted"], gap=1.35)

    y = pair(d, y, 410, ("WHY ROWS GET SQUASHED", squash), ("ROW FACTOR = CELL WIDTH ÷ HEIGHT", factors))

    def detail(x, w, y0):
        n = 3
        colw = (w - 36 - (n - 1) * 14) / n
        hs, sizes = [], (16, 32, 64)
        for i, wc in enumerate(sizes):
            hs.append(d.screen(x + 18 + i * (colw + 14), y0 + 46, colw, grid(wc, SVG_ROW_FACTOR), SVG_ROW_FACTOR, pad=6))
        hb = max(hs)
        for i, wc in enumerate(sizes):
            sx = x + 18 + i * (colw + 14)
            cnt = wc * len(grid(wc, SVG_ROW_FACTOR))
            d.text(sx, y0 + 46 + hb + 26, f"-w {wc}", 16, t["accent"], 700, family=MONO)
            d.text(sx, y0 + 46 + hb + 46, f"{cnt:,} glyphs", 13, t["muted"], family=MONO)
        return d.rich(x + 18, y0 + 46 + hb + 78, w - 36, "More columns means more glyphs and finer shapes, at the cost of a bigger file. "
                      "The default is **120**.", 14)

    y = single(d, y, "WIDTH IS DETAIL", detail)
    y = know(d, y, [
        "**Width is columns, not pixels.** A line longer than your terminal wraps, so check `tput cols`.",
        "**Going wider than the source** just upsamples. You get more glyphs, not more detail.",
    ], [
        "**HTML and SVG:** `-w` still sets the glyph count. `--pixel-width` only sets how large they are drawn.",
        "**At least one row,** however flat the picture is.",
    ])
    y = d.footer(y - GAP + 22, "pytone/core.py · resize_image()   flag: -w / --width")
    return d, y


def step_gray(t):
    d = Doc(t, "03-grayscale", "Step 3: Grayscale",
            "Each resized cell is reduced to one brightness value from 0 to 255 using luma weights, "
            "where green counts most and blue least.")
    y = d.header(3, "Grayscale", "Brightness is **the only signal that picks a glyph**. Everything else "
                 "about the color waits for step 5.")
    top = y + 4

    def what(x, w, y0):
        pw = 150
        ph = pw * IMG.height / IMG.width
        px0, py0 = x + 24, y0 + 46
        small = resize_image(IMG, 60, SVG_ROW_FACTOR)
        d.image(px0, py0, pw, ph, data_uri(small, "PNG"), pix=True)
        d.text(px0 + pw / 2, py0 + ph + 22, "RGB cells", 13, t["muted"], anchor="middle")
        d.arrow(px0 + pw + 14, py0 + ph / 2, px0 + pw + 132, py0 + ph / 2, t["accent"], 2.5)
        d.text(px0 + pw + 73, py0 + ph / 2 - 12, "convert(“L”)", 13, t["accent"], 700, "middle", MONO)
        gx0 = px0 + pw + 150
        d.image(gx0, py0, pw, ph, data_uri(small.convert("L"), "PNG"), pix=True)
        d.text(gx0 + pw / 2, py0 + ph + 22, "one number per cell", 13, t["muted"], anchor="middle")
        fx = gx0 + pw + 32
        fw = x + w - 18 - fx
        d.text(fx, py0 + 10, "Luma weights", 14, t["text"], 700)
        d.rect(fx, py0 + 22, fw, 78, t["bg"], t["border"], rx=6)
        for k, ln in enumerate(("L = 0.299 R", "  + 0.587 G", "  + 0.114 B")):
            d.text(fx + 12, py0 + 46 + k * 20, ln, 14, t["accent"], family=MONO)
        d.rich(fx, py0 + 128, fw, "The eye sees green as brightest and blue as darkest, so the math does too.", 13.5, t["muted"], gap=1.35)
        return py0 + ph + 22

    y = single(d, top, "WHAT HAPPENS", what)

    def swatches(x, w, y0):
        sw = [("pure red", (255, 0, 0)), ("dark green", (0, 130, 0)), ("pure green", (0, 255, 0)),
              ("pure blue", (0, 0, 255)), ("dark belt", (56, 47, 53)), ("bright zone", (139, 155, 168))]
        n = len(sw)
        cw_ = (w - 36 - (n - 1) * 12) / n
        for i, (lab, c) in enumerate(sw):
            gv = Image.new("RGB", (1, 1), c).convert("L").getpixel((0, 0))
            x0 = x + 18 + i * (cw_ + 12)
            d.rect(x0, y0 + 48, cw_, 52, hexc(c), t["border"], rx=6)
            d.add(f'<path d="M{f(x0 + cw_ / 2)} {y0 + 106} v14 m-5 -5 l5 5 l5 -5" fill="none" stroke="{t["muted"]}" stroke-width="2"/>')
            d.rect(x0, y0 + 128, cw_, 52, f"rgb({gv},{gv},{gv})", t["border"], rx=6)
            d.text(x0 + cw_ / 2, y0 + 208, str(gv), 20, t["accent"], 700, "middle", MONO)
            d.text(x0 + cw_ / 2, y0 + 230, lab, 13, t["muted"], anchor="middle")
        bx0, bx1 = x + 18, x + 18 + 2 * cw_ + 12
        d.add(f'<path d="M{f(bx0)} {y0 + 246} v8 h{f(bx1 - bx0)} v-8" fill="none" stroke="{t["accent"]}" stroke-width="2"/>')
        d.text((bx0 + bx1) / 2, y0 + 276, "Different colors, same value, same glyph", 13.5, t["accent"], 700, "middle")
        return y0 + 280

    y = single(d, y, "SAME MATH, REAL COLORS", swatches)

    def scale(x, w, y0):
        bx, bw = x + 18, w - 36
        for k in range(64):
            v = round(k * 255 / 63)
            d.rect(bx + k * bw / 64, y0 + 50, bw / 64 + 0.5, 32, f"rgb({v},{v},{v})")
        d.rect(bx, y0 + 50, bw, 32, "none", t["border"], rx=3)
        d.text(bx, y0 + 106, "0 darkest", 13, t["muted"], family=MONO)
        d.text(bx + bw, y0 + 106, "brightest 255", 13, t["muted"], anchor="end", family=MONO)
        for k in range(64):
            v = 255 - round(k * 255 / 63)
            d.rect(bx + k * bw / 64, y0 + 126, bw / 64 + 0.5, 32, f"rgb({v},{v},{v})")
        d.rect(bx, y0 + 126, bw, 32, "none", t["border"], rx=3)
        d.text(bx, y0 + 182, "--invert", 14, t["accent"], 700, family=MONO)
        d.text(bx + bw, y0 + 182, "v → 255 − v", 13, t["muted"], anchor="end", family=MONO)
        return y0 + 190

    def why(x, w, y0):
        return bullets(d, x + 18, y0 + 58, w - 36, [
            "**Color isn't lost.** The RGB cells are kept aside and come back in step 5.",
            "**Contrast is everything.** A narrow range of values fills only one or two glyphs.",
        ], size=14, gap=8) - 8

    y = pair(d, y, 480, ("THE 0–255 SCALE", scale), ("WHY IT MATTERS", why))
    y = know(d, y, [
        "**It runs after the resize,** so each value is the average of a small region, not one source pixel.",
        "**-s and -b never change which glyph is picked.** They adjust color later.",
    ], [
        "**--invert flips the glyph choice and the cell's color together.**",
        "**Saturated blues land near the dark end.** Pure blue is only 29 of 255, so deep blue shadows read as dark.",
    ])
    y = d.footer(y - GAP + 22, "pytone/core.py · img.convert(\"L\") · pixels_to_ascii()   flag: --invert")
    return d, y


def step_ramp(t):
    d = Doc(t, "04-glyph-ramp", "Step 4: Glyph ramp",
            "Brightness from 0 to 255 is divided into equal buckets, one per character in the ramp, "
            "ordered dark to light.")
    y = d.header(4, "Glyph ramp", "The ramp is a list of characters ordered **dark → light**. Each brightness "
                 "falls into one bucket, and the bucket's character is the glyph.")
    top = y + 4
    ramp, n = CIRCLES, len(CIRCLES)
    div = 256 // n
    g = resize_image(IMG, 80, SVG_ROW_FACTOR).convert("L")
    counts = Counter(g.tobytes())
    s = pixels_to_ascii(g, ramp)
    share, total = Counter(s), len(s)

    def buckets(x, w, y0):
        bx, bw = x + 24, w - 48
        bins = 64
        hist = [sum(counts.get(v, 0) for v in range(b * 256 // bins, (b + 1) * 256 // bins)) for b in range(bins)]
        hmax = max(hist[1:])
        hy, hh = y0 + 70, 88
        d.text(bx, y0 + 56, "Brightness of every cell in this render. The bar at 0 is black space and runs off the chart.", 13, t["muted"])
        for b, hv in enumerate(hist):
            bh = min(hh, hh * hv / hmax)
            d.rect(bx + b * bw / bins + 0.5, hy + hh - bh, bw / bins - 1, bh, t["muted"], rx=1)
        by = hy + hh + 14
        for k, ch_ in enumerate(ramp):
            lo = k * div
            hi = 255 if k == n - 1 else (k + 1) * div - 1
            x0, x1 = bx + lo * bw / 256, bx + (hi + 1) * bw / 256
            d.rect(x0 + 1, by, x1 - x0 - 2, 70, t["bg"], t["accent"], rx=6, sw=1.5)
            d.text((x0 + x1) / 2, by + 46, ch_ if ch_ != " " else "␣", 36, t["accent"] if ch_ != " " else t["muted"], 400, "middle", ART)
            d.text(x0 + 4, by + 92, f"{lo}", 13, t["muted"], family=MONO)
            d.text((x0 + x1) / 2, by + 122, f"{100 * share[ch_] / total:.0f}%", 15, t["text"], 700, "middle")
        d.text(bx + bw, by + 92, "255", 13, t["muted"], anchor="end", family=MONO)
        d.text(bx + bw, by + 148, "share of cells", 13, t["muted"], anchor="end")
        d.text(bx, by + 148, "index = min( gray ÷ (256 ÷ n), n − 1 )", 14, t["accent"], family=MONO)
        d.text(bx, by + 172, f"here n = {n}, so every bucket is {div} wide (the last takes the remainder)", 13, t["muted"])
        return by + 172

    y = single(d, top, "BRIGHTNESS → BUCKET → GLYPH", buckets)

    def ramps(x, w, y0):
        rs = [(" .:-=+*#%@", "classic"), (" ·∘○◯●", "circles"), (" ░▒▓█", "blocks"), (" ·+✦★", "stars")]
        colw = (w - 36 - 3 * 12) / 4
        hs = []
        for i, (r, lab) in enumerate(rs):
            hs.append(d.screen(x + 18 + i * (colw + 12), y0 + 46, colw, gray_rows(34, SVG_ROW_FACTOR, r), SVG_ROW_FACTOR, colored=False, pad=6))
        hb = max(hs)
        for i, (r, lab) in enumerate(rs):
            sx = x + 18 + i * (colw + 12)
            d.text(sx, y0 + 46 + hb + 26, lab, 15, t["text"], 700)
            d.text(sx, y0 + 46 + hb + 48, f'-c "{r}"', 13, t["accent"], family=MONO)
        return d.rich(x + 18, y0 + 46 + hb + 78, w - 36, "Same grid, same brightness values. Only the characters change, and with them the "
                      "texture. On a dark ground, **denser glyphs read as brighter**.", 14)

    y = single(d, y, "SAME PICTURE, DIFFERENT RAMP", ramps)

    def ground(x, w, y0):
        d.text(x + 18, y0 + 62, "Light glyphs on a dark ground", 14, t["text"], 700)
        d.text(x + 18, y0 + 94, " ·∘○◯●", 24, t["accent"], family=ART)
        d.text(x + w - 18, y0 + 92, "dark pixel → sparse", 13, t["muted"], anchor="end")
        d.text(x + 18, y0 + 144, "Dark glyphs on a light ground", 14, t["text"], 700)
        d.text(x + 18, y0 + 176, "B S#&@$%*!:. ", 24, t["accent"], family=ART)
        d.text(x + w - 18, y0 + 174, "dark pixel → dense", 13, t["muted"], anchor="end")
        return d.rich(x + 18, y0 + 214, w - 36, "Looks like a negative? Reverse the ramp, or add `--invert`. "
                      "The gallery uses the first; the default ramp is the second.", 13.5, t["muted"], gap=1.35)

    def rules(x, w, y0):
        return bullets(d, x + 18, y0 + 58, w - 36, [
            "**Any length.** More glyphs give smoother tones, fewer give bolder bands. Beyond 256 they spread evenly.",
            "**One code point each.** ZWJ emoji and combining marks break alignment; an empty ramp is rejected.",
            "**Spaces draw nothing.** A leading space gives clean shadows. The default ramp has one second, which punches holes.",
        ], size=14, gap=8) - 8

    y = pair(d, y, 410, ("MATCH THE RAMP TO THE GROUND", ground), ("RULES OF THE RAMP", rules))
    y = d.footer(y - GAP + 22, "pytone/core.py · pixels_to_ascii()   flags: -c / --chars, --invert")
    return d, y


def step_color(t):
    d = Doc(t, "05-color", "Step 5: Color",
            "Each glyph is colored from its source cell, a diagonal gradient, or a horizontal rainbow, "
            "then saturation and brightness multipliers are applied.")
    y = d.header(5, "Color", "The glyph carries the shape; **color puts back what grayscale threw away**. "
                 "Pick where it comes from, then tune it.")
    top = y + 4
    grad = [(155, 89, 182), (255, 215, 0)]
    opts = [
        ("Source colors", "default", {}, "Each glyph keeps its cell's average RGB."),
        ("Source, tuned", "-s 1.6 -b 1.5", dict(saturation=1.6, brightness=1.5), "Same colors, pushed. Both multipliers run last."),
        ("Gradient", "--gradient", dict(gradient=grad), "Two or more hex stops run top-left to bottom-right. Here, purple to gold."),
        ("Rainbow", "--rainbow", dict(rainbow=True), "Hue follows the column, so color changes left to right."),
    ]

    def srcs(x, w, y0):
        n = 4
        colw = (w - 36 - (n - 1) * 12) / n
        # Raw flags here, no subject boost: this panel is the one that demonstrates -s and -b.
        raw = dict(saturation=1.0, brightness=1.0)
        hs = [d.screen(x + 18 + i * (colw + 12), y0 + 46, colw, grid(28, SVG_ROW_FACTOR, CIRCLES, **{**raw, **kw}), SVG_ROW_FACTOR, pad=6)
              for i, (_, _, kw, _) in enumerate(opts)]
        hb = max(hs)
        bottoms = []
        for i, (lab, flag, kw, how) in enumerate(opts):
            sx = x + 18 + i * (colw + 12)
            d.text(sx, y0 + 46 + hb + 26, lab, 15, t["text"], 700)
            d.text(sx, y0 + 46 + hb + 48, flag, 13, t["accent"], family=MONO)
            bottoms.append(d.rich(sx, y0 + 46 + hb + 76, colw, how, 13.5, t["muted"], gap=1.35))
        b = max(bottoms)
        b = d.rich(x + 18, b + 14, w - 36, "Gradient and rainbow are **modulated by brightness**, so highlights stay bright and the shape still reads.", 14)
        return b

    y = single(d, top, "WHERE COLOR COMES FROM", srcs)

    def math(x, w, y0):
        items = [
            ("source", "RGB of the resized cell", "r, g, b"),
            ("gradient", "t = (x ÷ W + y ÷ H) ÷ 2, blended between stops", "sat × √gray,  value × (0.3 + 0.7 × gray)"),
            ("rainbow", "hue = column ÷ width", "sat = gray,  value = 1"),
        ]
        yy = y0 + 52
        for name, a, b in items:
            d.rect(x + 18, yy, w - 36, 54, t["bg"], t["border"], rx=8)
            d.text(x + 32, yy + 32, name, 15, t["text"], 700)
            d.text(x + 140, yy + 24, a, 13.5, t["accent"], family=MONO)
            d.text(x + 140, yy + 44, b, 13.5, t["muted"], family=MONO)
            yy += 64
        return d.rich(x + 18, yy + 10, w - 36, "-s and -b then multiply HSV saturation and value, clamped at the maximum. 1.0 changes nothing.", 13.5, t["muted"], gap=1.35)

    y = single(d, y, "THE MATH, SHORT VERSION", math)
    y = know(d, y, [
        "**plain has no color,** so -s, -b, --gradient and --rainbow do nothing there.",
        "**--rainbow and --gradient are exclusive.** Using both is an error.",
    ], [
        "**--invert flips the RGB too,** so colors invert along with the glyphs.",
        "**In a rainbow, shadows wash toward white** because saturation follows brightness.",
    ])
    y = d.footer(y - GAP + 22, "pytone/core.py · get_color_data()   flags: -s, -b, --gradient, --rainbow")
    return d, y


def file_sizes() -> dict:
    out = {}
    with tempfile.TemporaryDirectory() as tmp:
        def run(*a):
            return subprocess.run(["uv", "run", "--project", ROOT, "pytone", SRC, "-w", "100", *a], capture_output=True, text=True, cwd=ROOT, check=True).stdout
        out["text"] = len(run("-m", "plain").encode())
        out["ansi"] = len(run("-m", "color", "--color-mode", "truecolor").encode())
        for m in ("html", "svg"):
            p = os.path.join(tmp, f"o.{m}")
            run("-m", m, "-o", p)
            out[m] = os.path.getsize(p)
    return out


def kb(n):
    return f"{n / 1000:.0f} KB" if n >= 10000 else f"{n / 1000:.1f} KB"


def step_output(t):
    sizes = file_sizes()
    d = Doc(t, "06-output", "Step 6: Output",
            "The same colored glyph grid can be written as plain text, ANSI escape codes, a self-contained "
            "HTML page, or an SVG of positioned text.")
    y = d.header(6, "Output", "The glyph grid is finished. The last choice is **where it will live**, "
                 "and each of the four renderers is built for a different place.")
    top = y + 4
    cols = [
        dict(name="Text", flag="-m plain", bar=None, rf=TERMINAL_ROW_FACTOR, color=False, size=sizes["text"],
             tag="Just characters",
             pros=["Pipe it, redirect it, diff it", "Paste into code, chat or a commit", "Smallest by far"],
             cons=["No color at all"]),
        dict(name="ANSI", flag="-m color  (default)", bar="terminal", rf=TERMINAL_ROW_FACTOR, color=True, size=sizes["ansi"],
             tag="Color in the terminal",
             pros=["Instant: no file, no viewer", "24-bit color, with a 256-color fallback", "Drops to plain text when piped"],
             cons=["Needs a color terminal", "With -o it saves plain unless you force --color-mode"]),
        dict(name="HTML", flag="-m html", bar="pytone.html", rf=HTML_ROW_FACTOR, color=True, size=sizes["html"],
             tag="One file, any browser",
             pros=["Self-contained: no assets, no server", "Real text: select, copy, search", "Sized with --pixel-width"],
             cons=["A page, not an image, so it can't sit inline in a README", "Black page background built in"]),
        dict(name="SVG", flag="-m svg", bar="art.svg", rf=SVG_ROW_FACTOR, color=True, size=sizes["svg"],
             tag="Vector art for docs and pages",
             pros=["Sharp at any size", "Embeds like any image: README, docs, slides", "--pixel-width sets spacing, airy to fused"],
             cons=["Largest file: one element per glyph", "Transparent: bring your own background"]),
    ]
    n, gap = 4, 12
    cw_ = (CW - (n - 1) * gap) / n
    panels, bottoms, tails = [], [], []
    for i, c in enumerate(cols):
        x0 = M + i * (cw_ + gap)
        p = d.open(x0, top, cw_)
        d.text(x0 + 16, top + 36, c["name"], 22, t["text"], 700)
        d.text(x0 + 16, top + 58, c["flag"], 13, t["accent"], 700, family=MONO)
        w = cw_ - 32
        if c["color"]:
            rows = grid(24, c["rf"], CIRCLES)
        else:
            rows = gray_rows(24, c["rf"])
        h = d.screen(x0 + 16, top + 74, w, rows, c["rf"], colored=c["color"], pad=6, bar=c["bar"])
        yy = top + 74 + h + 28
        yy = d.rich(x0 + 16, yy, w, f"**{c['tag']}**", 14, gap=1.3) + 8
        for s_ in c["pros"]:
            d.text(x0 + 16, yy, "+", 14, t["good"], 700)
            yy = d.rich(x0 + 32, yy, w - 16, s_, 13.5, gap=1.3) + 4
        yy += 4
        for s_ in c["cons"]:
            d.text(x0 + 16, yy, "−", 14, t["bad"], 700)
            yy = d.rich(x0 + 32, yy, w - 16, s_, 13.5, t["muted"], gap=1.3) + 4
        panels.append((p, x0, c))
        bottoms.append(yy)
    ph = max(bottoms) - top + 70
    for p, x0, c in panels:
        d.close(p, 0, h=ph)
        d.line(x0 + 16, top + ph - 52, x0 + cw_ - 16, top + ph - 52, t["border"], 1)
        d.text(x0 + 16, top + ph - 22, kb(c["size"]), 19, t["accent"], 700, family=MONO)
        d.text(x0 + cw_ - 16, top + ph - 22, "at -w 100", 13, t["muted"], anchor="end")
    y = top + ph + 14
    y = d.rich(M, y + 10, CW, "File sizes are real: this image at `-w 100` with the default ramp, ANSI measured at truecolor.", 13.5, t["muted"], gap=1.3)
    y = d.footer(y + 4, "pytone/color.py · html_output.py · svg_output.py · core.py")
    return d, y


def step_choose(t):
    sizes = file_sizes()
    d = Doc(t, "07-choosing-output", "Choosing an output",
            "A decision guide: terminal, text pipeline, shareable file, or embedded image, and which "
            "pytone mode fits each.")
    y = d.header(6, "Choosing an output", "Start from **where the art will live**, not from how it looks. "
                 "The glyph grid is identical in all four.", kicker="STEP 6 OF 6 · CHOOSING")
    top = y + 4
    rows = [
        ("I want to see it right now", "In my terminal, over SSH, as a script banner.", "ANSI", "-m color  (the default)"),
        ("I'm pasting it somewhere", "A code comment, commit, chat, email, log or diff.", "Text", "-m plain"),
        ("I'm sending someone a file", "They open it in a browser and can copy the text.", "HTML", "-m html"),
        ("It goes in a README, deck or page", "Crisp at any size, no HTML wrapper needed.", "SVG", "-m svg"),
    ]
    rh = 88
    for i, (q, sub, tag, flag) in enumerate(rows):
        ry = top + i * (rh + 12)
        d.rect(M, ry, CW, rh, t["panel"], t["border"], rx=10)
        d.text(M + 22, ry + 38, q, 19, t["text"], 700)
        d.text(M + 22, ry + 64, sub, 14, t["muted"])
        ax = M + 470
        d.arrow(ax, ry + rh / 2, ax + 44, ry + rh / 2, t["accent"], 2.5)
        d.rect(ax + 58, ry + 20, 78, 48, t["bg"], t["accent"], rx=8, sw=1.5)
        d.text(ax + 58 + 39, ry + 51, tag, 18, t["accent"], 700, "middle")
        d.text(ax + 152, ry + 49, flag, 13, t["muted"], family=MONO)
    y = top + 4 * (rh + 12) + 4

    def table(x, w, y0):
        cx = [x + 18, x + 214, x + 394, x + 544, x + 690]
        for hx, h in zip(cx, ("", "Text", "ANSI", "HTML", "SVG")):
            d.text(hx, y0 + 62, h, 15, t["text"], 700)
        data = [
            ("Color", "none", "24-bit, 256 fallback", "24-bit", "24-bit"),
            ("Row factor", "0.55", "0.55", "0.6", "0.625"),
            ("Written to", "stdout or -o", "stdout or -o", "pytone.html", "pytone.svg"),
            ("Needs", "anything", "a color terminal", "a browser", "any image viewer"),
            ("Inline in a README", "as a code block", "no", "no", "yes, as an image"),
            ("Weight at -w 100", kb(sizes["text"]), kb(sizes["ansi"]), kb(sizes["html"]), kb(sizes["svg"])),
        ]
        for r, row in enumerate(data):
            ry = y0 + 94 + r * 36
            if r % 2 == 0:
                d.rect(x + 10, ry - 22, w - 20, 34, t["bg"], rx=6)
            d.text(cx[0], ry, row[0], 13.5, t["muted"], 600)
            for k in range(1, 5):
                d.text(cx[k], ry, row[k], 13.5, t["text"])
        return y0 + 94 + 6 * 36 - 18

    y = single(d, y, "SIDE BY SIDE", table)
    y = d.footer(y - GAP + 22, "Any mode: add -o to save to a file.")
    return d, y


STEPS = [step_overview, step_image, step_resize, step_gray, step_ramp, step_color, step_output, step_choose]


def lum(h):
    h = h.lstrip("#")
    c = [int(h[i : i + 2], 16) / 255 for i in (0, 2, 4)]
    c = [v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4 for v in c]
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]


def ratio(a, b):
    la, lb = sorted((lum(a), lum(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


def check_contrast():
    for name, t in THEMES.items():
        for fg in ("text", "muted", "accent", "good", "bad"):
            for bg in ("bg", "panel", "chip"):
                r = ratio(t[fg], t[bg])
                flag = "" if r >= 4.5 else "   <-- below 4.5"
                print(f"{name:5} {fg:6} on {bg:5} {r:5.1f}{flag}")
        print(f"{name:5} screen_text on screen {ratio(t['screen_text'], t['screen']):.1f}")


def main():
    check_contrast()
    for name, t in THEMES.items():
        folder = os.path.join(OUT, t["dir"])
        os.makedirs(folder, exist_ok=True)
        for step in STEPS:
            d, h = step(t)
            svg = d.render(h)
            path = os.path.join(folder, d.name + ".svg")
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(svg)
            print(f"{path}  {len(svg) / 1000:.0f} KB  {W}x{h:.0f}")


if __name__ == "__main__":
    main()
