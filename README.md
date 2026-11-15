<div align="center">

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="docs/hero_dark.svg">
  <source media="(prefers-color-scheme: light)" srcset="docs/hero_light.svg">
  <img src="docs/hero_dark.svg" alt="PeachPy: a peach above bubble lettering, rendered in blossom glyphs by this tool" width="50%">
</picture>

</div>

[Python 3.10+](https://www.python.org/downloads/) • [License: MIT](LICENSE) • [Pillow](https://python-pillow.org)

_Turn any image into text • Terminal, HTML or SVG • Gradients, rainbows and any glyph ramp you like_

**A small Python CLI that turns images into ASCII art.** Point it at a photo, painting or logo and get plain text, truecolor terminal output, a self-contained HTML page, or a scalable SVG you can drop straight into a README. The hero above was made with it.

**Try it in one line** (needs [uv](#prerequisite-uv)):

```bash
uvx --from git+https://github.com/interfaceconjurer/ascii-image-generator ascii-art path/to/image.jpg
```

&nbsp;

## Table of Contents

- [How It Works](#how-it-works)
- [Gallery](#gallery)
  - [Old Masters in Light](#old-masters-in-light)
  - [Space](#space)
  - [Iconic Photography](#iconic-photography)
- [Install](#install)
  - [Prerequisite: uv](#prerequisite-uv)
  - [Try It Without Installing](#try-it-without-installing)
  - [Install the `ascii-art` Command](#install-the-ascii-art-command)
  - [Notes for Scripts and AI Agents](#notes-for-scripts-and-ai-agents)
- [Usage](#usage)
  - [Output Modes](#output-modes)
  - [Character Ramps](#character-ramps)
  - [Color: Gradients and Rainbow](#color-gradients-and-rainbow)
  - [Density](#density)
- [Options](#options)
- [Python API](#python-api)
- [Tips and Known Quirks](#tips-and-known-quirks)
- [Development](#development)
- [Credits](#credits)
- [License](#license)

&nbsp;

## How It Works

```text
image ─▶ resize ─▶ grayscale ─▶ glyph ramp ─▶ color ─▶ text · ANSI · HTML · SVG
```

1. **Resize.** The image is scaled to `--width` columns. Rows are squashed to match the
   shape of a character cell, so circles stay circles: 0.55 for terminals and 1/1.6 for SVG.
2. **Grayscale.** Each cell's brightness (0–255) is computed.
3. **Glyph ramp.** Brightness picks a character from `--chars`, ordered dark → light.
   The ramp can be anything: ASCII, Unicode dots, block shading, emoji.
4. **Color.** Each glyph keeps its source pixel's color, or is recolored by a diagonal
   `--gradient` or a horizontal `--rainbow`. Both are modulated by the image's brightness
   so the shape still reads.
5. **Render.** The result is written as plain text, ANSI truecolor or 256-color, an HTML
   `<pre>`, or an SVG of positioned `<text>` glyphs.

```bash
# One command, end to end
ascii-art photo.jpg -m svg -w 110 -c " ·∘○◯●" -o photo.svg
```

&nbsp;

&nbsp;

## Gallery

Every piece below is a single command. Expand **Command** under any image to copy it.

### Old Masters in Light

Circles grow with brightness, so the painting's light falls in rings of `· ∘ ○ ◯ ●`.

<!-- GALLERY:old-masters -->
<table>
  <tr>
    <td width="33%" align="center">
      <img src="docs/gallery/TODO.svg" alt="TODO" width="100%"><br>
      <sub><b>Title</b> · Artist, year</sub>
      <details><summary>Command</summary>

```bash
ascii-art source.jpg -m svg -c " ·∘○◯●" -w 110 --pixel-width 715 -s 1.4 -b 1.9 -o out.svg
```

</details>
    </td>
    <td width="33%" align="center">…</td>
    <td width="33%" align="center">…</td>
  </tr>
</table>
<!-- /GALLERY:old-masters -->

### Space

Glyph ramps chosen to match the subject: Saturn drawn in rings, the Moon in moon phases.

<!-- GALLERY:space -->
<table>
  <tr>
    <td width="33%" align="center">…</td>
    <td width="33%" align="center">…</td>
    <td width="33%" align="center">…</td>
  </tr>
</table>
<!-- /GALLERY:space -->

### Iconic Photography

Halftone dots in a single ink, `-c " ·•●" --gradient "#F2E8D5,#F2E8D5"`, plus a pop-art quad.

<!-- GALLERY:photography -->
<table>
  <tr>
    <td width="33%" align="center">…</td>
    <td width="33%" align="center">…</td>
    <td width="33%" align="center">…</td>
  </tr>
</table>
<!-- /GALLERY:photography -->

&nbsp;

&nbsp;

## Install

### Prerequisite: uv

[uv](https://docs.astral.sh/uv/) is a fast Python package and tool manager. It also
downloads Python 3.10+ automatically if it's missing, so you don't need Python first.

Check whether you have it:

```bash
uv --version
```

If that fails, install uv with **one** of these:

```bash
# macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh
```

```bash
# macOS with Homebrew
brew install uv
```

```powershell
# Windows (PowerShell)
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

Then open a new terminal so `uv` is on your PATH. For other options, see the
[uv installation docs](https://docs.astral.sh/uv/getting-started/installation/).

### Try It Without Installing

```bash
uvx --from git+https://github.com/interfaceconjurer/ascii-image-generator ascii-art path/to/image.jpg
```

uv builds a cached, throwaway environment and runs the tool. Nothing stays installed.

### Install the `ascii-art` Command

```bash
uv tool install git+https://github.com/interfaceconjurer/ascii-image-generator
```

Verify:

```bash
ascii-art --help
```

If you get `command not found`, run `uv tool update-shell` and open a new terminal.

Upgrade with `uv tool upgrade ascii-art`. Uninstall with `uv tool uninstall ascii-art`.

<details>
<summary>Without uv (pipx or pip)</summary>

```bash
pipx install git+https://github.com/interfaceconjurer/ascii-image-generator
```

```bash
pip install git+https://github.com/interfaceconjurer/ascii-image-generator
```

These need Python 3.10+ already installed.

</details>

### Notes for Scripts and AI Agents

- **Command:** `ascii-art <image> [options]`. `python -m ascii_art` is equivalent.
- **Inputs:** any image Pillow can open (JPEG, PNG, GIF, WebP, …).
- **Output location:**
  - `-m color` (default) and `-m plain` print to stdout, or write to `-o FILE`.
  - `-m html` and `-m svg` always write a file: `-o FILE`, or `./ascii_art.html` /
    `./ascii_art.svg` in the current directory, overwriting any existing file. They print
    `Saved HTML to <path>` / `Saved SVG to <path>`.
- **Color when piped:** `--color-mode auto` (default) drops ANSI escapes when stdout isn't a
  terminal, so piped or redirected output is clean text.
- **Exit codes:** `0` success · `1` input file not found or invalid `--gradient` · `2` invalid arguments.
- **Full options:** `ascii-art --help` or the [Options](#options) table.
- **Working on the code?** See [Development](#development) and [AGENTS.md](AGENTS.md).

&nbsp;

&nbsp;

## Usage

### Output Modes

```bash
# Colored terminal output (default; auto-detects truecolor / 256-color)
ascii-art image.jpg

# Plain text
ascii-art image.jpg -m plain -w 80

# Self-contained HTML page
ascii-art image.jpg -m html -o art.html

# Scalable SVG, 1200px wide
ascii-art image.jpg -m svg --pixel-width 1200 -o art.svg
```

When stdout isn't a terminal, color mode falls back to plain text. Use
`--color-mode truecolor` to force escapes, for example `ascii-art image.jpg --color-mode truecolor > art.ans`.

### Character Ramps

`--chars` is ordered **dark → light**. The default ramp is `"B S#&@$%*!:. "`. Ramps that
read well:

| Ramp                 | Look                         |
| -------------------- | ---------------------------- |
| `" .:-=+*#%@"`       | Classic ASCII                |
| `" ·∘○◯●"`           | Circles that grow with light |
| `" ·•●"`             | Halftone dots                |
| `" ░▒▓█"`            | Block shading                |
| `" ·+✦★"`            | Stars                        |
| `" 🌑🌒🌓🌔🌕"`       | Moon phases                  |

```bash
ascii-art image.jpg -m svg -c " ░▒▓█" -o blocks.svg
ascii-art image.jpg --invert -c " ·•●"
```

### Color: Gradients and Rainbow

```bash
# Diagonal gradient, top-left → bottom-right, 2 or more 6-digit hex stops
ascii-art image.jpg -m svg --gradient "#3D1A4D,#9B59B6,#FFD700,#B8860B" -o gold.svg

# A single-ink look: use the same color twice
ascii-art image.jpg -m svg -c " ·•●" --gradient "#F2E8D5,#F2E8D5" -o ink.svg

# Horizontal rainbow, brighter
ascii-art image.jpg -m svg --rainbow -b 1.5 -o rainbow.svg

# Punchier source colors
ascii-art image.jpg -m svg -s 1.6 -b 1.3 -o vivid.svg
```

### Density

In SVG mode, glyphs are always drawn at 14px and `--pixel-width` only sets the spacing
between them. A large `--pixel-width` gives airy, separate glyphs. At around 6–8 px per
column the glyphs overlap and fuse into texture, and many of the gallery pieces rely on
exactly that.

```bash
ascii-art image.jpg -m svg -w 110 -c " ·∘○◯●" --pixel-width 1500 -o airy.svg
ascii-art image.jpg -m svg -w 110 -c " ·∘○◯●" --pixel-width 715  -o dense.svg
```

&nbsp;

&nbsp;

## Options

| Flag               | Default         | Description                                                    |
| ------------------ | --------------- | -------------------------------------------------------------- |
| `-w, --width`      | `120`           | Output width in characters                                     |
| `-m, --mode`       | `color`         | `plain`, `color`, `html` or `svg`                              |
| `-c, --chars`      | `B S#&@$%*!:. ` | Character ramp, dark → light                                   |
| `-s, --saturation` | `1.0`           | Saturation multiplier (color, HTML, SVG)                       |
| `-b, --brightness` | `1.0`           | Brightness multiplier (color, HTML, SVG)                       |
| `--pixel-width`    | –               | Output width in pixels (HTML, SVG). See [Density](#density)    |
| `--invert`         | off             | Invert brightness: dark areas get the light glyphs             |
| `--rainbow`        | off             | Recolor with a horizontal rainbow                              |
| `--gradient`       | –               | Recolor with a diagonal gradient, e.g. `"#FF0000,#0000FF"`     |
| `--color-mode`     | `auto`          | `auto`, `truecolor`, `256` or `none`                           |
| `-o, --output`     | stdout          | Output file (HTML and SVG default to `ascii_art.html` / `.svg`) |

&nbsp;

&nbsp;

## Python API

```python
from ascii_art import image_to_ascii, get_color_data

# Plain text
print(image_to_ascii("photo.jpg", width=100))

# Per-character color data, for your own renderer
rows = get_color_data("photo.jpg", width=100, chars=" ·•●", rainbow=True)
for row in rows:
    for char, (r, g, b) in row:
        ...

# Gradient stops as RGB tuples
rows = get_color_data("photo.jpg", width=100, gradient=[(61, 26, 77), (255, 215, 0)])
```

&nbsp;

&nbsp;

## Tips and Known Quirks

- **Pick sources with strong shapes.** Silhouettes, hard light and a wide tonal range
  read best. Busy mid-gray images turn to mush.
- **The default ramp has a space in second place**, which punches holes in dark areas.
  For photos, try one of the [ramps above](#character-ramps).
- **Transparent PNG areas render black.** Flatten onto a background first if you need white.
- **`-s` and `-b` don't affect `plain` mode**, which has no color.
- **Ramps can be any length.** Ramps longer than 256 characters are spread evenly across the gray levels.

&nbsp;

&nbsp;

## Development

```bash
git clone https://github.com/interfaceconjurer/ascii-image-generator.git
cd ascii-image-generator
uv venv && uv pip install -e ".[dev]"
source .venv/bin/activate
pytest
ruff check .
```

&nbsp;

&nbsp;

## Credits

<!-- CREDITS -->

**Hero.** The peach is the [Noto Emoji](https://github.com/googlefonts/noto-emoji) 3D peach
(Apache 2.0, Google). The lettering is set in [Modak](https://fonts.google.com/specimen/Modak)
(SIL Open Font License). Both were rendered with this tool using the blossom ramp `" ⁖⁘⁙❁✿"`.

Based on [Generating ASCII art from colored image using Python](https://dev.to/anuragrana/generating-ascii-art-from-colored-image-using-python-4ace)
by Anurag Rana, extended with color, HTML and SVG output, gradients, rainbow and custom ramps.

&nbsp;

&nbsp;

## License

MIT. See [LICENSE](LICENSE).
