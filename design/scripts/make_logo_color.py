"""Color studies for the README logo (S3: stacked lockup, circles ramp, 130 columns).

Every variant runs the real tool on the same source image with the same width and ramp;
only the color flags change. The tool's gradient runs diagonally, top-left to bottom-right,
and is modulated by brightness, so dim glyphs stay dim and the shape still reads.

Run from the repo root:  python3 design/scripts/make_logo_color.py
"""
import colorsys
import os
import shutil
import subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # repo root
OUT = os.path.join(ROOT, "design", "build", "logo-color")
SRC = os.path.join(ROOT, "design", "sources", "lockup-stack.png")
SIDE_SRC = os.path.join(ROOT, "design", "sources", "lockup-side.png")  # side lockup, rasterized
BASE = ["-m", "svg", "-w", "130", "-c", " ·∘○◯●", "--pixel-width", "880"]

# (code, name, note, dark-theme flags, light-theme flags)
VARIANTS = [
    ("C1", "Snake spectrum",
     "The original seven section colors, tail to head: teal, green, yellow, orange, pink, purple, blue.",
     ["--gradient", "#2ec4b6,#5ccf6a,#f2c94c,#f2994a,#ff6f91,#b678f0,#4d9dff"],
     ["--gradient", "#0fa3a3,#2f9e44,#e0a800,#e8590c,#e64980,#8e44d6,#1c7ed6"]),
    ("C2", "Python blue and gold",
     "The Python logo's two colors, a nod to the Py in the name.",
     ["--gradient", "#4b8bbe,#ffd43b"],
     ["--gradient", "#306998,#d4a800"]),
    ("C3", "Print CMY",
     "Halftone printing inks: cyan, magenta, yellow.",
     ["--gradient", "#00b7eb,#ec008c,#ffe600"],
     ["--gradient", "#0092c7,#c8007a,#d6b800"]),
    ("C4", "Ember",
     "Warm: crimson through orange to gold, for a single-hue-family feel.",
     ["--gradient", "#e63946,#f4a261,#ffd166"],
     ["--gradient", "#c1121f,#e76f51,#e9a400"]),
    ("C5", "Deep sea",
     "Cool: violet through blue to mint.",
     ["--gradient", "#7b5cff,#3a86ff,#2ee6a6"],
     ["--gradient", "#5a3fd6,#1f6feb,#12a87a"]),
    ("C6", "Neon terminal",
     "Phosphor green to cyan, like an old terminal screen.",
     ["--gradient", "#39ff88,#00e5ff"],
     ["--gradient", "#0a9b4a,#0088a8"]),
    ("C7", "Single ink, peach",
     "One color, the old peach as a callback. Calm and print-like.",
     ["--gradient", "#ffa66b,#ffa66b"],
     ["--gradient", "#b3400b,#b3400b"]),
    ("C8", "Rainbow",
     "The tool's own rainbow mode: hue follows the column. Loudest of the set.",
     ["--rainbow", "-b", "1.1"],
     ["--rainbow", "-b", "0.75", "-s", "1.2"]),
]


def _lum(rgb):
    c = [v / 255 for v in rgb]
    c = [v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4 for v in c]
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]


def contrast(rgb, bg=(255, 255, 255)):
    a, b = sorted((_lum(rgb), _lum(bg)), reverse=True)
    return (a + 0.05) / (b + 0.05)


def deepen(hexc, target=4.5):
    """Lower a color's lightness, keeping its hue and saturation, until it reaches `target`
    contrast against white. The brightest glyphs take the stop colors at full strength, so
    this bounds the whole render's contrast on a light page."""
    rgb = tuple(int(hexc[i:i + 2], 16) for i in (1, 3, 5))
    h, l, s = colorsys.rgb_to_hls(*(v / 255 for v in rgb))
    while contrast(rgb) < target and l > 0:
        l = max(0.0, l - 0.005)
        rgb = tuple(round(v * 255) for v in colorsys.hls_to_rgb(h, l, s))
    return "#%02x%02x%02x" % rgb


def light_flags(flags):
    if "--gradient" not in flags:
        return flags
    i = flags.index("--gradient") + 1
    stops = ",".join(deepen(c) for c in flags[i].split(","))
    return flags[:i] + [stops] + flags[i + 1:]


def side(codes=("C2",), widths=(150, 190)):
    """The side-by-side lockup with the same ramp and colors. It is wider than tall, so it
    needs more columns than the stack for the snake to keep the same detail."""
    os.makedirs(OUT, exist_ok=True)
    src = os.path.join(OUT, "side", "PyTone.png")
    os.makedirs(os.path.dirname(src), exist_ok=True)
    shutil.copyfile(SIDE_SRC, src)
    table = {c: (dark, light) for c, _, _, dark, light in VARIANTS}
    for code in codes:
        dark, light = table[code]
        for w in widths:
            for theme, flags in (("dark", dark), ("light", light_flags(light))):
                out = os.path.join(OUT, "side", f"{code}-side-{w}-{theme}.svg")
                base = [a if a != "130" else str(w) for a in BASE]
                subprocess.run(["uv", "run", "--project", ROOT, "pytone", src, *base, *flags, "-o", out],
                               check=True, capture_output=True, cwd=ROOT)
            print(code, "side", w)


def main():
    os.makedirs(OUT, exist_ok=True)
    # The tool titles an SVG after its source file, so render from a file named for the brand.
    src = os.path.join(OUT, "PyTone.png")
    shutil.copyfile(SRC, src)
    for code, name, _, dark, light in VARIANTS:
        for theme, flags in (("dark", dark), ("light", light_flags(light))):
            out = os.path.join(OUT, f"{code}-{theme}.svg")
            subprocess.run(["uv", "run", "--project", ROOT, "pytone", src, *BASE, *flags, "-o", out],
                           check=True, capture_output=True, cwd=ROOT)
        print(code, name, " light stops:", light_flags(light)[light_flags(light).index("--gradient") + 1] if "--gradient" in light else "rainbow")


if __name__ == "__main__":
    import sys
    side() if "--side" in sys.argv else main()
