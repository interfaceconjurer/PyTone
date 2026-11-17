"""Bake "ghost cards" for the README gallery.

Each card is an SVG: transparent padding (1rem at display size), the ASCII art, then the
title, the artist/date and the command in muted monospace. No border and no background,
except the art's own dark ground.

Every card uses the same coordinate width (CARD_W), so text in the SVG keeps a consistent
on-screen size relative to the tile. Rows in the README then scale each card to fill its
share of the column.

Input:  docs/gallery/<slug>.svg (the art, with its bg rect)
Output: docs/gallery/cards/<slug>.svg
"""
import html
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # repo root
G = os.path.join(ROOT, "docs", "gallery")
OUT = os.path.join(G, "cards")
M = {p["slug"]: p for p in json.load(open(os.path.join(ROOT, "design", "publish_manifest.json")))}

CARD_W = 600.0          # card coordinate width
PAD = 24.0              # ~1rem at a typical tile width (tile ~280–420px => 600 units ≈ 1.5–2.1 units/px)
TITLE_PX, META_PX, CMD_PX = 26.0, 19.0, 17.0
LINE = 1.35
# Caption colours per page theme. Light-mode values are close to GitHub light's own text
# colours (fg.default #1f2328, fg.muted #59636e) so titles read near-black on white.
THEMES = {
    "dark":  {"title": "#c9d1d9", "muted": "#9198a1", "cmd": "#8b949e", "dir": ""},
    "light": {"title": "#1f2328", "muted": "#59636e", "cmd": "#57606a", "dir": "light"},
}
CMD_CHARS = 54          # wrap width for the command, in monospace characters


def art_dims(svg):
    m = re.search(r'<svg\b[^>]*\bwidth="([\d.]+)"[^>]*\bheight="([\d.]+)"', svg)
    return float(m[1]), float(m[2])


def wrap_cmd(c, width):
    toks = re.findall(r'"[^"]*"|\S+', c)
    parts, i = [], 0
    while i < len(toks):
        t = toks[i]
        if t.startswith("-") and i + 1 < len(toks) and not toks[i + 1].startswith("-"):
            parts.append(t + " " + toks[i + 1]); i += 2
        else:
            parts.append(t); i += 1
    lines, cur = [], ""
    for p in parts:
        if cur and len(cur) + 1 + len(p) > width:
            lines.append(cur); cur = "  " + p
        else:
            cur = (cur + " " + p) if cur else p
    lines.append(cur)
    return lines


def card(p, card_w=None, theme="dark"):
    CARD_W = card_w or globals()['CARD_W']
    T = THEMES[theme]
    TITLE, MUTED, CMD = T["title"], T["muted"], T["cmd"]
    src = open(os.path.join(G, p["slug"] + ".svg"), encoding="utf-8").read()
    aw, ah = art_dims(src)
    pad = PAD * CARD_W / 600.0
    scale = (CARD_W - 2 * pad) / aw
    art_h = ah * scale
    inner = re.sub(r"^.*?<svg\b[^>]*>", "", src, count=1, flags=re.S)
    inner = re.sub(r"</svg>\s*$", "", inner, flags=re.S)
    inner = inner.replace('<rect id="bg" width="100%" height="100%"', f'<rect id="bg" width="{aw}" height="{ah}"', 1)
    # the art's <style> targets every `text`; scope it to the art so card text keeps its own fonts
    inner = re.sub(r"(<style>\s*)text(\s*\{)", r"\1.art text\2", inner, count=1)

    cmd = f'pytone {p["slug"]}.jpg -m svg {p["args"]} -o {p["slug"]}.svg'
    cmd_lines = wrap_cmd(cmd, int(CMD_CHARS * CARD_W / 600.0))
    y = pad + art_h + 18
    text = []
    title_px = min(TITLE_PX, (CARD_W - 2 * pad) / (0.56 * len(p["title"])))
    text.append(f'<text x="{pad}" y="{y:.1f}" font-family="-apple-system,BlinkMacSystemFont,Segoe UI,Helvetica,Arial,sans-serif" '
                f'font-size="{title_px:.1f}" font-weight="600" fill="{TITLE}" dominant-baseline="hanging">{html.escape(p["title"])}</text>')
    y += TITLE_PX * LINE
    text.append(f'<text x="{pad}" y="{y:.1f}" font-family="-apple-system,BlinkMacSystemFont,Segoe UI,Helvetica,Arial,sans-serif" '
                f'font-size="{META_PX}" fill="{MUTED}" dominant-baseline="hanging">{html.escape(p["by"])}</text>')
    y += META_PX * LINE + 12
    for ln in cmd_lines:
        text.append(f'<text x="{pad}" y="{y:.1f}" font-family="ui-monospace,SFMono-Regular,Menlo,Consolas,monospace" '
                    f'font-size="{CMD_PX}" fill="{CMD}" dominant-baseline="hanging" xml:space="preserve">{html.escape(ln)}</text>')
        y += CMD_PX * LINE
    total_h = y + pad - CMD_PX * (LINE - 1)

    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {CARD_W:g} {total_h:.1f}" '
           f'width="{CARD_W:g}" height="{total_h:.1f}">'
           f'<title>{html.escape(p["title"])}</title>'
           f'<svg class="art" x="{pad}" y="{pad}" width="{aw * scale:.2f}" height="{art_h:.2f}" viewBox="0 0 {aw} {ah}">{inner}</svg>'
           + "".join(text) + "</svg>")
    return svg, total_h


def main():
    os.makedirs(OUT, exist_ok=True)
    heights = {}
    # highlights tile at ~half the column, grid cards at ~a third: give grid cards a narrower
    # coordinate width so the same font sizes read larger once the card is scaled down
    hi = {"pearl-earring", "virgin-annunciate", "whirlpool-galaxy", "ring-nebula", "baldwin-iv", "migrant-mother"}
    for theme, t in THEMES.items():
        out = os.path.join(OUT, t["dir"]) if t["dir"] else OUT
        os.makedirs(out, exist_ok=True)
        for slug, p in M.items():
            svg, h = card(p, 600.0 if slug in hi else 400.0, theme)
            open(os.path.join(out, slug + ".svg"), "w", encoding="utf-8").write(svg)
            heights[slug] = round(h, 1)
        print(f"wrote {len(M)} {theme} cards to {out}")
    return heights


if __name__ == "__main__":
    main()
