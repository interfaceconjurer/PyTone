<div align="center">

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="docs/hero_dark.svg">
  <source media="(prefers-color-scheme: light)" srcset="docs/hero_light.svg">
  <img src="docs/hero_dark.svg" alt="PyTone: a snake made of halftone dots crossing a dot screen, beside the PyTone wordmark, rendered in circle glyphs by this tool" width="100%">
</picture>

</div>

[Python 3.11+](https://www.python.org/downloads/) • [License: MIT](LICENSE) • [Pillow](https://python-pillow.org)

_Turn any image into text • Terminal, HTML or SVG • Gradients, rainbows and any glyph ramp you like_

**PyTone is a small Python CLI that turns images into ASCII art.** Point it at a photo, painting or logo and get plain text, truecolor terminal output, a self-contained HTML page, or a scalable SVG you can drop straight into a README. The hero above was made with it.

**Try it in one line** (needs [uv](#prerequisite-uv)):

```bash
uvx --from git+https://github.com/interfaceconjurer/ascii-image-generator pytone path/to/image.jpg
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
  - [Install the `pytone` Command](#install-the-pytone-command)
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

<p align="center"><picture><source media="(prefers-color-scheme: light)" srcset="docs/pipeline/light/00-pipeline.svg"><img src="docs/pipeline/00-pipeline.svg" alt="The PyTone pipeline in six stages: image, resize, grayscale, glyph ramp, color and output. Each stage shows the real result of that step on a photo of Earth, with the flags that control it." width="100%"></picture></p>

```bash
# One command, end to end
pytone earth.jpg -w 110 -c " ·∘○◯●" --gradient "#3D1A4D,#FFD700" -m svg -o earth.svg
```

**Stage by stage.** Open any step for what it does, why it matters, and what to know.

<details>
<summary><b>1. Image</b></summary>

The file is opened and normalized: EXIF rotation applied, first frame only, transparency flattened onto black, converted to RGB.

<p align="center"><picture><source media="(prefers-color-scheme: light)" srcset="docs/pipeline/light/01-image.svg"><img src="docs/pipeline/01-image.svg" alt="Step 1, Image. PyTone opens the file and normalizes it: EXIF rotation applied, first frame only, transparency flattened onto black, converted to RGB. Includes advice on choosing a source with a wide tonal range." width="100%"></picture></p>

</details>

<details>
<summary><b>2. Resize</b></summary>

The image is scaled to `--width` columns. Rows are squashed to match the shape of a character cell, so circles stay circles: 0.55 for terminals and 1/1.6 for SVG.

<p align="center"><picture><source media="(prefers-color-scheme: light)" srcset="docs/pipeline/light/02-resize.svg"><img src="docs/pipeline/02-resize.svg" alt="Step 2, Resize. The image is scaled to the chosen number of columns. Rows are squashed by a row factor of 0.55 for terminals, 0.6 for HTML and 0.625 for SVG so circles stay round. Shows the same picture at 16, 32 and 64 columns." width="100%"></picture></p>

</details>

<details>
<summary><b>3. Grayscale</b></summary>

Each cell's brightness (0–255) is computed.

<p align="center"><picture><source media="(prefers-color-scheme: light)" srcset="docs/pipeline/light/03-grayscale.svg"><img src="docs/pipeline/03-grayscale.svg" alt="Step 3, Grayscale. Each cell becomes one brightness from 0 to 255 using luma weights of 0.299 red, 0.587 green and 0.114 blue. Different colors with the same brightness pick the same glyph." width="100%"></picture></p>

</details>

<details>
<summary><b>4. Glyph ramp</b></summary>

Brightness picks a character from `--chars`, ordered dark → light. The ramp can be anything: ASCII, Unicode dots, block shading, emoji.

<p align="center"><picture><source media="(prefers-color-scheme: light)" srcset="docs/pipeline/light/04-glyph-ramp.svg"><img src="docs/pipeline/04-glyph-ramp.svg" alt="Step 4, Glyph ramp. Brightness is split into equal buckets, one per character in the ramp, ordered dark to light. Shows four ramps on the same picture and how to match a ramp to a dark or light background." width="100%"></picture></p>

</details>

<details>
<summary><b>5. Color</b></summary>

Each glyph keeps its source pixel's color, or is recolored by a diagonal `--gradient` or a horizontal `--rainbow`. Both are modulated by the image's brightness so the shape still reads.

<p align="center"><picture><source media="(prefers-color-scheme: light)" srcset="docs/pipeline/light/05-color.svg"><img src="docs/pipeline/05-color.svg" alt="Step 5, Color. Glyphs keep their source color, or take a diagonal gradient or a horizontal rainbow, then saturation and brightness multipliers are applied." width="100%"></picture></p>

</details>

<details>
<summary><b>6. Output</b></summary>

The result is written as plain text, ANSI truecolor or 256-color, an HTML `<pre>`, or an SVG of positioned `<text>` glyphs.

<p align="center"><picture><source media="(prefers-color-scheme: light)" srcset="docs/pipeline/light/06-output.svg"><img src="docs/pipeline/06-output.svg" alt="Step 6, Output. The same glyph grid written as plain text, ANSI, HTML or SVG, with the strengths, trade-offs and real file size of each at 100 columns." width="100%"></picture></p>

</details>

<details>
<summary><b>Choosing an output</b></summary>

<p align="center"><picture><source media="(prefers-color-scheme: light)" srcset="docs/pipeline/light/07-choosing-output.svg"><img src="docs/pipeline/07-choosing-output.svg" alt="A decision guide for picking an output: ANSI for the terminal, text for pasting, HTML for sending a file, SVG for READMEs and docs, with a side-by-side comparison table." width="100%"></picture></p>

</details>

&nbsp;

&nbsp;

## Gallery

Every piece below is a single command, printed under its image. All of a section's commands are in the box under its grid; tap a piece to jump there.

### Old Masters in Light

Circles grow with brightness, so the painting's light falls in rings of `· ∘ ○ ◯ ●`.

<!-- GALLERY:old-masters -->
<p align="left"><a href="#old-masters-commands"><picture><source media="(prefers-color-scheme: light)" srcset="docs/gallery/cards/light/pearl-earring.svg"><img src="docs/gallery/cards/pearl-earring.svg" alt="Girl with a Pearl Earring, Johannes Vermeer, c. 1665" title="Girl with a Pearl Earring · Johannes Vermeer, c. 1665" width="52.17%"></picture></a><a href="#old-masters-commands"><picture><source media="(prefers-color-scheme: light)" srcset="docs/gallery/cards/light/virgin-annunciate.svg"><img src="docs/gallery/cards/virgin-annunciate.svg" alt="Virgin Annunciate, Antonello da Messina, c. 1475" title="Virgin Annunciate · Antonello da Messina, c. 1475" width="47.67%"></picture></a><br><a href="#old-masters-commands"><picture><source media="(prefers-color-scheme: light)" srcset="docs/gallery/cards/light/rembrandt-self-portrait.svg"><img src="docs/gallery/cards/rembrandt-self-portrait.svg" alt="Self-Portrait, Rembrandt, 1659" title="Self-Portrait · Rembrandt, 1659" width="34.83%"></picture></a><a href="#old-masters-commands"><picture><source media="(prefers-color-scheme: light)" srcset="docs/gallery/cards/light/magdalene-smoking-flame.svg"><img src="docs/gallery/cards/magdalene-smoking-flame.svg" alt="Magdalene with the Smoking Flame, Georges de La Tour, c. 1640" title="Magdalene with the Smoking Flame · Georges de La Tour, c. 1640" width="32.75%"></picture></a><a href="#old-masters-commands"><picture><source media="(prefers-color-scheme: light)" srcset="docs/gallery/cards/light/mona-lisa.svg"><img src="docs/gallery/cards/mona-lisa.svg" alt="Mona Lisa, Leonardo da Vinci, c. 1503–1519" title="Mona Lisa · Leonardo da Vinci, c. 1503–1519" width="32.1%"></picture></a><br><a href="#old-masters-commands"><picture><source media="(prefers-color-scheme: light)" srcset="docs/gallery/cards/light/lady-with-an-ermine.svg"><img src="docs/gallery/cards/lady-with-an-ermine.svg" alt="Lady with an Ermine, Leonardo da Vinci, c. 1490" title="Lady with an Ermine · Leonardo da Vinci, c. 1490" width="32.69%"></picture></a><a href="#old-masters-commands"><picture><source media="(prefers-color-scheme: light)" srcset="docs/gallery/cards/light/man-in-a-red-turban.svg"><img src="docs/gallery/cards/man-in-a-red-turban.svg" alt="Portrait of a Man (Self-Portrait?), Jan van Eyck, 1433" title="Portrait of a Man (Self-Portrait?) · Jan van Eyck, 1433" width="32.45%"></picture></a><a href="#old-masters-commands"><picture><source media="(prefers-color-scheme: light)" srcset="docs/gallery/cards/light/david-goliath.svg"><img src="docs/gallery/cards/david-goliath.svg" alt="David with the Head of Goliath, Caravaggio, 1610" title="David with the Head of Goliath · Caravaggio, 1610" width="34.54%"></picture></a></p>

<a id="old-masters-commands"></a>

```bash
# Girl with a Pearl Earring
pytone pearl-earring.jpg -m svg -w 110 --pixel-width 715 -c " ·∘○◯●" -s 1.4 -b 1.9 -o pearl-earring.svg
# Virgin Annunciate   (prep: auto-level, -level 10%,100%, gamma 1.3)
pytone virgin-annunciate.jpg -m svg -w 110 --pixel-width 715 -c " ·∘○◯●" -s 1.4 -b 1.9 -o virgin-annunciate.svg
# Self-Portrait   (prep: auto-level, gamma 1.2)
pytone rembrandt-self-portrait.jpg -m svg -w 110 --pixel-width 715 -c " ·∘○◯●" -s 1.4 -b 1.9 -o rembrandt-self-portrait.svg
# Magdalene with the Smoking Flame   (prep: auto-level, gamma 1.5)
pytone magdalene-smoking-flame.jpg -m svg -w 110 --pixel-width 715 -c " ·∘○◯●" -s 1.4 -b 1.9 -o magdalene-smoking-flame.svg
# Mona Lisa   (prep: auto-level, gamma 1.3)
pytone mona-lisa.jpg -m svg -w 110 --pixel-width 715 -c " ·∘○◯●" -s 1.4 -b 1.9 -o mona-lisa.svg
# Lady with an Ermine   (prep: auto-level, gamma 1.2)
pytone lady-with-an-ermine.jpg -m svg -w 110 --pixel-width 715 -c " ·∘○◯●" -s 1.4 -b 1.9 -o lady-with-an-ermine.svg
# Portrait of a Man (Self-Portrait?)   (prep: auto-level, gamma 1.2)
pytone man-in-a-red-turban.jpg -m svg -w 110 --pixel-width 715 -c " ·∘○◯●" -s 1.4 -b 1.9 -o man-in-a-red-turban.svg
# David with the Head of Goliath
pytone david-goliath.jpg -m svg -w 110 --pixel-width 715 -c " ·∘○◯●" -s 1.4 -b 1.9 -o david-goliath.svg
```
<!-- /GALLERY:old-masters -->

### Space

NASA and ESA imagery. Where it fits, the ramp matches the subject: Saturn in rings, the Moon in moon phases, Jupiter in bands.

<!-- GALLERY:space -->
<p align="left"><a href="#space-commands"><picture><source media="(prefers-color-scheme: light)" srcset="docs/gallery/cards/light/whirlpool-galaxy.svg"><img src="docs/gallery/cards/whirlpool-galaxy.svg" alt="Whirlpool Galaxy (M51), NASA, ESA, S. Beckwith (STScI), Hubble Heritage Team" title="Whirlpool Galaxy (M51) · NASA, ESA, S. Beckwith (STScI), Hubble Heritage Team" width="49.98%"></picture></a><a href="#space-commands"><picture><source media="(prefers-color-scheme: light)" srcset="docs/gallery/cards/light/ring-nebula.svg"><img src="docs/gallery/cards/ring-nebula.svg" alt="Ring Nebula (M57), JWST, NASA, ESA, CSA, M. Barlow, N. Cox, R. Wesson" title="Ring Nebula (M57), JWST · NASA, ESA, CSA, M. Barlow, N. Cox, R. Wesson" width="49.86%"></picture></a><br><a href="#space-commands"><picture><source media="(prefers-color-scheme: light)" srcset="docs/gallery/cards/light/saturn.svg"><img src="docs/gallery/cards/saturn.svg" alt="Saturn in rings, NASA/JPL/Space Science Institute (Cassini), 2008" title="Saturn in rings · NASA/JPL/Space Science Institute (Cassini), 2008" width="39.26%"></picture></a><a href="#space-commands"><picture><source media="(prefers-color-scheme: light)" srcset="docs/gallery/cards/light/moon.svg"><img src="docs/gallery/cards/moon.svg" alt="The Moon, in moon phases, Rendered from NASA SVS CGI Moon Kit (LRO color + LOLA elevation)" title="The Moon, in moon phases · Rendered from NASA SVS CGI Moon Kit (LRO color + LOLA elevation)" width="29.63%"></picture></a><a href="#space-commands"><picture><source media="(prefers-color-scheme: light)" srcset="docs/gallery/cards/light/pleiades.svg"><img src="docs/gallery/cards/pleiades.svg" alt="The Pleiades, in stars, NASA, ESA, AURA/Caltech, Palomar Observatory" title="The Pleiades, in stars · NASA, ESA, AURA/Caltech, Palomar Observatory" width="30.8%"></picture></a><br><a href="#space-commands"><picture><source media="(prefers-color-scheme: light)" srcset="docs/gallery/cards/light/jupiter.svg"><img src="docs/gallery/cards/jupiter.svg" alt="Jupiter, in cloud bands, NASA, ESA, A. Simon (GSFC), OPAL, 2024" title="Jupiter, in cloud bands · NASA, ESA, A. Simon (GSFC), OPAL, 2024" width="33.67%"></picture></a><a href="#space-commands"><picture><source media="(prefers-color-scheme: light)" srcset="docs/gallery/cards/light/sun.svg"><img src="docs/gallery/cards/sun.svg" alt="The Sun, SDO/AIA, NASA/GSFC/SDO, Oct 2014" title="The Sun, SDO/AIA · NASA/GSFC/SDO, Oct 2014" width="33.67%"></picture></a><a href="#space-commands"><picture><source media="(prefers-color-scheme: light)" srcset="docs/gallery/cards/light/blue-marble.svg"><img src="docs/gallery/cards/blue-marble.svg" alt="The Blue Marble, NASA / Apollo 17 crew, 1972" title="The Blue Marble · NASA / Apollo 17 crew, 1972" width="32.34%"></picture></a><br><a href="#space-commands"><picture><source media="(prefers-color-scheme: light)" srcset="docs/gallery/cards/light/helix-nebula.svg"><img src="docs/gallery/cards/helix-nebula.svg" alt="Helix Nebula (NGC 7293), NASA, ESA, C.R. O'Dell (Vanderbilt)" title="Helix Nebula (NGC 7293) · NASA, ESA, C.R. O'Dell (Vanderbilt)" width="32.28%"></picture></a><a href="#space-commands"><picture><source media="(prefers-color-scheme: light)" srcset="docs/gallery/cards/light/m87.svg"><img src="docs/gallery/cards/m87.svg" alt="M87* black hole, in rings, Event Horizon Telescope Collaboration, 2019" title="M87* black hole, in rings · Event Horizon Telescope Collaboration, 2019" width="33.8%"></picture></a><a href="#space-commands"><picture><source media="(prefers-color-scheme: light)" srcset="docs/gallery/cards/light/pluto.svg"><img src="docs/gallery/cards/pluto.svg" alt="Pluto, NASA/JHUAPL/SwRI (New Horizons), 2015" title="Pluto · NASA/JHUAPL/SwRI (New Horizons), 2015" width="33.61%"></picture></a></p>

<a id="space-commands"></a>

```bash
# Whirlpool Galaxy (M51)   (prep: -level 12%,100% -clahe 25x25%+128+3 -sigmoidal-contrast 4x45%)
pytone whirlpool-galaxy.jpg -m svg -w 130 --pixel-width 715 -c " ·∘○◯●" -s 1.6 -b 1.4 -o whirlpool-galaxy.svg
# Ring Nebula (M57), JWST   (prep: center crop, -level 8%,100% -sigmoidal-contrast 4x40%)
pytone ring-nebula.jpg -m svg -w 120 --pixel-width 720 -c " ·∘○◯●" -s 1.5 -b 1.5 -o ring-nebula.svg
# Saturn in rings
pytone saturn.jpg -m svg -w 160 --pixel-width 800 -c " ·∘○◯" -s 1.4 -b 1.5 -o saturn.svg
# The Moon, in moon phases   (prep: CGI lit sphere; 1.19× wide for emoji)
pytone moon.jpg -m svg -w 108 --pixel-width 1188 -c " 🌑🌒🌓🌔🌕" -o moon.svg
# The Pleiades, in stars   (prep: crop, -level 10%,100%, gamma 1.3)
pytone pleiades.jpg -m svg -w 130 --pixel-width 845 -c "  ·∘+✦★" -s 1.7 -b 2.0 -o pleiades.svg
# Jupiter, in cloud bands   (prep: -modulate 100,220 -sigmoidal-contrast 7x50%)
pytone jupiter.jpg -m svg -w 120 --pixel-width 720 -c " -=≡" -s 1.8 -b 1.6 -o jupiter.svg
# The Sun, SDO/AIA   (prep: auto-level, gamma 2.2)
pytone sun.jpg -m svg -w 120 --pixel-width 720 -c " ·∘○◯●" -s 1.5 -b 1.8 -o sun.svg
# The Blue Marble   (prep: -sigmoidal-contrast 3x50%)
pytone blue-marble.jpg -m svg -w 120 --pixel-width 720 -c " ·∘○◯●" -s 1.5 -b 1.4 -o blue-marble.svg
# Helix Nebula (NGC 7293)   (prep: center crop, -level 8%,100% -sigmoidal-contrast 4x40%)
pytone helix-nebula.jpg -m svg -w 120 --pixel-width 720 -c " ·∘○◯●" -s 1.5 -b 1.5 -o helix-nebula.svg
# M87* black hole, in rings   (prep: center crop, gamma 1.2)
pytone m87.jpg -m svg -w 100 --pixel-width 650 -c " ·∘○◎◉" -s 1.3 -b 1.5 -o m87.svg
# Pluto   (prep: -sigmoidal-contrast 4x55% -level 8%,100%, gamma 0.9)
pytone pluto.jpg -m svg -w 120 --pixel-width 720 -c " ·∘○◯●" -s 1.4 -b 1.3 -o pluto.svg
```
<!-- /GALLERY:space -->

### Iconic Photography

Halftone dots in a single ink, `-c " ·•●" --gradient "#F2E8D5,#F2E8D5"`, plus pop-art color variants.

<!-- GALLERY:photography -->
<p align="left"><a href="#photography-commands"><picture><source media="(prefers-color-scheme: light)" srcset="docs/gallery/cards/light/baldwin-iv.svg"><img src="docs/gallery/cards/baldwin-iv.svg" alt="Baldwin IV, the Leper King, Film still, Kingdom of Heaven (2005)" title="Baldwin IV, the Leper King · Film still, Kingdom of Heaven (2005)" width="53.0%"></picture></a><a href="#photography-commands"><picture><source media="(prefers-color-scheme: light)" srcset="docs/gallery/cards/light/migrant-mother.svg"><img src="docs/gallery/cards/migrant-mother.svg" alt="Migrant Mother, Dorothea Lange, 1936" title="Migrant Mother · Dorothea Lange, 1936" width="46.84%"></picture></a><br><a href="#photography-commands"><picture><source media="(prefers-color-scheme: light)" srcset="docs/gallery/cards/light/abraham-lincoln.svg"><img src="docs/gallery/cards/abraham-lincoln.svg" alt="Abraham Lincoln, Alexander Gardner, 1863" title="Abraham Lincoln · Alexander Gardner, 1863" width="33.29%"></picture></a><a href="#photography-commands"><picture><source media="(prefers-color-scheme: light)" srcset="docs/gallery/cards/light/billie-holiday.svg"><img src="docs/gallery/cards/billie-holiday.svg" alt="Billie Holiday, William P. Gottlieb, c. 1947" title="Billie Holiday · William P. Gottlieb, c. 1947" width="33.17%"></picture></a><a href="#photography-commands"><picture><source media="(prefers-color-scheme: light)" srcset="docs/gallery/cards/light/audrey-hepburn.svg"><img src="docs/gallery/cards/audrey-hepburn.svg" alt="Audrey Hepburn, Bud Fraker (Paramount), 1953" title="Audrey Hepburn · Bud Fraker (Paramount), 1953" width="33.23%"></picture></a><br><a href="#photography-commands"><picture><source media="(prefers-color-scheme: light)" srcset="docs/gallery/cards/light/einstein-pop.svg"><img src="docs/gallery/cards/einstein-pop.svg" alt="Einstein, pop (magenta → amber), Orren Jack Turner, 1947" title="Einstein, pop (magenta → amber) · Orren Jack Turner, 1947" width="33.25%"></picture></a><a href="#photography-commands"><picture><source media="(prefers-color-scheme: light)" srcset="docs/gallery/cards/light/muhammad-ali.svg"><img src="docs/gallery/cards/muhammad-ali.svg" alt="Muhammad Ali, Ira Rosenberg (NYWTS), 1967" title="Muhammad Ali · Ira Rosenberg (NYWTS), 1967" width="33.25%"></picture></a><a href="#photography-commands"><picture><source media="(prefers-color-scheme: light)" srcset="docs/gallery/cards/light/greta-garbo.svg"><img src="docs/gallery/cards/greta-garbo.svg" alt="Greta Garbo, Clarence Sinclair Bull, 1931" title="Greta Garbo · Clarence Sinclair Bull, 1931" width="33.18%"></picture></a><br><a href="#photography-commands"><picture><source media="(prefers-color-scheme: light)" srcset="docs/gallery/cards/light/nikola-tesla.svg"><img src="docs/gallery/cards/nikola-tesla.svg" alt="Nikola Tesla, Napoleon Sarony, c. 1890" title="Nikola Tesla · Napoleon Sarony, c. 1890" width="34.52%"></picture></a><a href="#photography-commands"><picture><source media="(prefers-color-scheme: light)" srcset="docs/gallery/cards/light/frida-kahlo.svg"><img src="docs/gallery/cards/frida-kahlo.svg" alt="Frida Kahlo, Guillermo Kahlo, 1932" title="Frida Kahlo · Guillermo Kahlo, 1932" width="30.49%"></picture></a><a href="#photography-commands"><picture><source media="(prefers-color-scheme: light)" srcset="docs/gallery/cards/light/marilyn-pop-a.svg"><img src="docs/gallery/cards/marilyn-pop-a.svg" alt="Marilyn, pop (yellow → magenta), Frank Powolny, 1953" title="Marilyn, pop (yellow → magenta) · Frank Powolny, 1953" width="34.68%"></picture></a></p>

<a id="photography-commands"></a>

```bash
# Baldwin IV, the Leper King   (prep: crop to figure, -clahe 12x12%+128+3 -level 10%,100%)
pytone baldwin-iv.jpg -m svg -w 130 --pixel-width 845 -c " ·•●" -s 1.4 -b 1.15 -o baldwin-iv.svg
# Migrant Mother
pytone migrant-mother.jpg -m svg -w 100 --pixel-width 840 -c " ·•●" --gradient "#F2E8D5,#F2E8D5" -o migrant-mother.svg
# Abraham Lincoln   (prep: crop, -level 10%,100% -gamma 1.2 -sigmoidal-contrast 3x45%)
pytone abraham-lincoln.jpg -m svg -w 110 --pixel-width 715 -c " ·•●" --gradient "#F2E8D5,#F2E8D5" -o abraham-lincoln.svg
# Billie Holiday   (prep: crop)
pytone billie-holiday.jpg -m svg -w 130 --pixel-width 845 -c " ·•●" --gradient "#F2E8D5,#F2E8D5" -o billie-holiday.svg
# Audrey Hepburn   (prep: crop, -level 20%,100% -gamma 1.8 -sigmoidal-contrast 3x40%)
pytone audrey-hepburn.jpg -m svg -w 120 --pixel-width 780 -c " ·•●" --gradient "#F2E8D5,#F2E8D5" -o audrey-hepburn.svg
# Einstein, pop (magenta → amber)   (prep: same prep as Einstein)
pytone einstein-pop.jpg -m svg -w 110 --pixel-width 770 -c " ·•●" --gradient "#FF006E,#FFBE0B" -o einstein-pop.svg
# Muhammad Ali   (prep: crop, -sigmoidal-contrast 3x50%)
pytone muhammad-ali.jpg -m svg -w 110 --pixel-width 715 -c " ·•●" --gradient "#F2E8D5,#F2E8D5" -o muhammad-ali.svg
# Greta Garbo   (prep: crop, -level 15%,100%)
pytone greta-garbo.jpg -m svg -w 120 --pixel-width 780 -c " ·•●" --gradient "#F2E8D5,#F2E8D5" -o greta-garbo.svg
# Nikola Tesla   (prep: crop)
pytone nikola-tesla.jpg -m svg -w 100 --pixel-width 650 -c " ·•●" --gradient "#F2E8D5,#F2E8D5" -o nikola-tesla.svg
# Frida Kahlo   (prep: auto-level, gamma 1.4, -sigmoidal-contrast 4x50%)
pytone frida-kahlo.jpg -m svg -w 100 --pixel-width 840 -c " ·•●" --gradient "#F2E8D5,#F2E8D5" -o frida-kahlo.svg
# Marilyn, pop (yellow → magenta)   (prep: auto-level, gamma 1.15)
pytone marilyn-pop-a.jpg -m svg -w 120 --pixel-width 840 -c " ·•●" --gradient "#FFD60A,#FF006E" -o marilyn-pop-a.svg
```
<!-- /GALLERY:photography -->

&nbsp;

&nbsp;

## Install

### Prerequisite: uv

[uv](https://docs.astral.sh/uv/) is a fast Python package and tool manager. It also
downloads Python 3.11+ automatically if it's missing, so you don't need Python first.

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
uvx --from git+https://github.com/interfaceconjurer/ascii-image-generator pytone path/to/image.jpg
```

uv builds a cached, throwaway environment and runs the tool. Nothing stays installed.

### Install the `pytone` Command

```bash
uv tool install git+https://github.com/interfaceconjurer/ascii-image-generator
```

Verify:

```bash
pytone --help
```

If you get `command not found`, run `uv tool update-shell` and open a new terminal.

Upgrade with `uv tool upgrade py-tone`. Uninstall with `uv tool uninstall py-tone`.

<details>
<summary>Without uv (pipx or pip)</summary>

```bash
pipx install git+https://github.com/interfaceconjurer/ascii-image-generator
```

```bash
pip install git+https://github.com/interfaceconjurer/ascii-image-generator
```

These need Python 3.11+ already installed.

</details>

### Notes for Scripts and AI Agents

- **Command:** `pytone <image> [options]`. `python -m pytone` is equivalent.
- **Runtime:** Python 3.11+ with Pillow 13.0+ (the dependency floor includes upstream decoder security fixes).
- **Inputs:** any image Pillow can open (JPEG, PNG, GIF, WebP, …). EXIF orientation is
  applied; animated images use their first frame. Transparency is composited over black.
- **Output location:**
  - `-m color` (default) and `-m plain` print to stdout, or write to `-o FILE`.
  - `-m html` and `-m svg` always write a file: `-o FILE`, or `./pytone.html` /
    `./pytone.svg` in the current directory, overwriting any existing file. They print
    `Saved HTML to <path>` / `Saved SVG to <path>`.
- **Color when piped:** `--color-mode auto` (default) drops ANSI escapes when stdout isn't a
  terminal. Files written with `-o` also contain clean text unless color is explicitly requested.
- **File integrity:** output cannot refer to the input image, including symbolic and hard
  links. Files are replaced atomically after a successful write; failed writes preserve
  existing output. Parent directories must already exist.
- **Exit codes:** `0` success · `1` image/file errors, invalid `--gradient`, or a closed
  stdout pipe · `2` invalid arguments. Expected errors go to stderr without a traceback.
- **Full options:** `pytone --help` or the [Options](#options) table.
- **Working on the code?** See [Development](#development) and [AGENTS.md](AGENTS.md).

&nbsp;

&nbsp;

## Usage

### Output Modes

```bash
# Colored terminal output (default; auto-detects truecolor / 256-color)
pytone image.jpg

# Plain text
pytone image.jpg -m plain -w 80

# Self-contained HTML page
pytone image.jpg -m html -o art.html

# Scalable SVG, 1200px wide
pytone image.jpg -m svg --pixel-width 1200 -o art.svg
```

When stdout isn't a terminal, color mode falls back to plain text. Use
`--color-mode truecolor` to force escapes, for example `pytone image.jpg --color-mode truecolor > art.ans`.

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
pytone image.jpg -m svg -c " ░▒▓█" -o blocks.svg
pytone image.jpg --invert -c " ·•●"
```

### Color: Gradients and Rainbow

```bash
# Diagonal gradient, top-left → bottom-right, 2 or more 6-digit hex stops
pytone image.jpg -m svg --gradient "#3D1A4D,#9B59B6,#FFD700,#B8860B" -o gold.svg

# A single-ink look: use the same color twice
pytone image.jpg -m svg -c " ·•●" --gradient "#F2E8D5,#F2E8D5" -o ink.svg

# Horizontal rainbow, brighter
pytone image.jpg -m svg --rainbow -b 1.5 -o rainbow.svg

# Punchier source colors
pytone image.jpg -m svg -s 1.6 -b 1.3 -o vivid.svg
```

### Density

In SVG mode, glyphs are always drawn at 14px and `--pixel-width` only sets the spacing
between them. A large `--pixel-width` gives airy, separate glyphs. At around 6–8 px per
column the glyphs overlap and fuse into texture, and many of the gallery pieces rely on
exactly that.

```bash
pytone image.jpg -m svg -w 110 -c " ·∘○◯●" --pixel-width 1500 -o airy.svg
pytone image.jpg -m svg -w 110 -c " ·∘○◯●" --pixel-width 715  -o dense.svg
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
| `-o, --output`     | stdout          | Output file (HTML and SVG default to `pytone.html` / `.svg`) |

&nbsp;

&nbsp;

## Python API

```python
from pytone import image_to_ascii, get_color_data

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
- **Each ramp entry is one Unicode code point.** Wide characters, combining marks and
  multi-code-point emoji can affect alignment; terminal display widths vary. Empty ramps,
  control characters and line separators are rejected.
- **Dimensions must be positive integers.** Saturation and brightness must be finite and
  nonnegative. `--rainbow` and `--gradient` are mutually exclusive.

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
ruff format --check .
python -m build
```

CI checks Python 3.11–3.14, the minimum Pillow version, macOS and Windows, and builds
and installs the distribution. See [Architecture and engineering review](docs/architecture.md)
for module responsibilities, regression evidence and known limitations.

&nbsp;

&nbsp;

## Credits

<!-- CREDITS -->

**Gallery sources.** Renders are by this tool. Sources are public domain or CC0 unless noted.

<details><summary>All gallery credits</summary>

| Piece | Creator | Source | License |
|---|---|---|---|
| Girl with a Pearl Earring | Johannes Vermeer, c. 1665 | [source](https://commons.wikimedia.org/wiki/File:1665_Girl_with_a_Pearl_Earring.jpg) | Public domain |
| Lady with an Ermine | Leonardo da Vinci, c. 1490 | [source](https://commons.wikimedia.org/wiki/File:Lady_with_an_Ermine_-_Leonardo_da_Vinci_-_Google_Art_Project.jpg) | Public domain |
| Portrait of a Man (Self-Portrait?) | Jan van Eyck, 1433 | [source](https://commons.wikimedia.org/wiki/File:Portrait_of_a_Man_in_a_Turban_%28Jan_van_Eyck%29.jpg) | Public domain |
| Magdalene with the Smoking Flame | Georges de La Tour, c. 1640 | [source](https://commons.wikimedia.org/wiki/File:Georges_de_La_Tour_007.jpg) | Public domain |
| Self-Portrait | Rembrandt, 1659 | [source](https://commons.wikimedia.org/wiki/File:Rembrandt_self_portrait.jpg) | Public domain |
| Mona Lisa | Leonardo da Vinci, c. 1503–1519 | [source](https://commons.wikimedia.org/wiki/File:Mona_Lisa%2C_by_Leonardo_da_Vinci%2C_from_C2RMF_retouched.jpg) | Public domain |
| David with the Head of Goliath | Caravaggio, 1610 | [source](https://commons.wikimedia.org/wiki/File:David_with_the_Head_of_Goliath-Caravaggio_%281610%29.jpg) | Public domain |
| Virgin Annunciate | Antonello da Messina, c. 1475 | [source](https://commons.wikimedia.org/wiki/File:Antonello_da_Messina_-_Virgin_Annunciate_-_Galleria_Regionale_della_Sicilia%2C_Palermo.jpg) | Public domain |
| Saturn in rings | NASA/JPL/Space Science Institute (Cassini), 2008 | [source](https://commons.wikimedia.org/wiki/File:Saturn_during_Equinox.jpg) | Public domain |
| The Moon, in moon phases | Rendered from NASA SVS CGI Moon Kit (LRO color + LOLA elevation) | [source](https://svs.gsfc.nasa.gov/4720) | Public domain (NASA) |
| Jupiter, in cloud bands | NASA, ESA, A. Simon (GSFC), OPAL, 2024 | [source](https://commons.wikimedia.org/wiki/File:Jupiter_OPAL_2.png) | Public domain |
| Whirlpool Galaxy (M51) | NASA, ESA, S. Beckwith (STScI), Hubble Heritage Team | [source](https://commons.wikimedia.org/wiki/File:Messier51_sRGB.jpg) | Public domain |
| Ring Nebula (M57), JWST | NASA, ESA, CSA, M. Barlow, N. Cox, R. Wesson | [source](https://commons.wikimedia.org/wiki/File:Ring_Nebula_%28NIRCam_Image%29.png) | Public domain (NASA); ESA copy CC BY 4.0 |
| The Sun, SDO/AIA | NASA/GSFC/SDO, Oct 2014 | [source](https://commons.wikimedia.org/wiki/File:Halloween_Sun_2014.tiff) | Public domain |
| The Blue Marble | NASA / Apollo 17 crew, 1972 | [source](https://commons.wikimedia.org/wiki/File:The_Blue_Marble_%28remastered%29.jpg) | Public domain |
| Helix Nebula (NGC 7293) | NASA, ESA, C.R. O'Dell (Vanderbilt) | [source](https://commons.wikimedia.org/wiki/File:NGC7293_%282004%29.jpg) | Public domain |
| The Pleiades, in stars | NASA, ESA, AURA/Caltech, Palomar Observatory | [source](https://commons.wikimedia.org/wiki/File:Pleiades_large.jpg) | Public domain |
| M87* black hole, in rings | Event Horizon Telescope Collaboration, 2019 | [source](https://commons.wikimedia.org/wiki/File:Black_hole_-_Messier_87_crop_max_res.jpg) | CC BY 4.0 (credit: EHT Collaboration) |
| Pluto | NASA/JHUAPL/SwRI (New Horizons), 2015 | [source](https://commons.wikimedia.org/wiki/File:Pluto_in_True_Color_-_High-Res.jpg) | Public domain |
| Marilyn, pop (yellow → magenta) | Frank Powolny, 1953 | [source](https://commons.wikimedia.org/wiki/File:Monroe_1953_publicity_%28cropped%29.jpg) | Public domain |
| Migrant Mother | Dorothea Lange, 1936 | [source](https://commons.wikimedia.org/wiki/File:Lange-MigrantMother02.jpg) | Public domain |
| Frida Kahlo | Guillermo Kahlo, 1932 | [source](https://commons.wikimedia.org/wiki/File:Frida_Kahlo%2C_by_Guillermo_Kahlo.jpg) | Public domain |
| Abraham Lincoln | Alexander Gardner, 1863 | [source](https://commons.wikimedia.org/wiki/File:Abraham_Lincoln_O-77_matte_collodion_print.jpg) | Public domain |
| Billie Holiday | William P. Gottlieb, c. 1947 | [source](https://commons.wikimedia.org/wiki/File:Billie_Holiday_0001_original.jpg) | Public domain |
| Greta Garbo | Clarence Sinclair Bull, 1931 | [source](https://commons.wikimedia.org/wiki/File:Greta_Garbo_in_1931_by_Clarence_Sinclair_Bull.jpg) | Public domain |
| Nikola Tesla | Napoleon Sarony, c. 1890 | [source](https://commons.wikimedia.org/wiki/File:Tesla_Sarony.jpg) | Public domain |
| Muhammad Ali | Ira Rosenberg (NYWTS), 1967 | [source](https://commons.wikimedia.org/wiki/File:Muhammad_Ali_NYWTS.jpg) | Public domain |
| Audrey Hepburn | Bud Fraker (Paramount), 1953 | [source](https://commons.wikimedia.org/wiki/File:AudreyKHepburn.jpg) | Public domain |
| Baldwin IV, the Leper King | Film still, Kingdom of Heaven (2005) | — | © 20th Century Studios, used for illustration |
| Einstein, pop (magenta → amber) | Orren Jack Turner, 1947 | [source](https://commons.wikimedia.org/wiki/File:Albert_Einstein_Head.jpg) | Public domain |

</details>

<!-- /CREDITS -->

**Hero.** The snake is drawn as halftone dots crossing a dot screen. The wordmark is set in
[Space Grotesk](https://fonts.google.com/specimen/Space+Grotesk) (SIL Open Font License). The
lockup was rendered with this tool using the circles ramp `" ·∘○◯●"` and a gradient in the
Python logo's blue and gold.

Based on [Generating ASCII art from colored image using Python](https://dev.to/anuragrana/generating-ascii-art-from-colored-image-using-python-4ace)
by Anurag Rana, extended with color, HTML and SVG output, gradients, rainbow and custom ramps.

&nbsp;

&nbsp;

## License

MIT. See [LICENSE](LICENSE).
