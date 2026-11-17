# Design sources

Everything needed to rebuild the artwork in this repo. The finished files live in `docs/`;
this folder holds the scripts, source images and font that produce them.

```text
design/
├── scripts/              generators (run from the repo root)
├── sources/              source images the generators read
├── fonts/                Space Grotesk Bold, for the wordmark (SIL OFL 1.1, see OFL.txt)
├── publish_manifest.json the gallery: title, credit, license and command for each piece
└── build/                scratch output, git-ignored
```

## What builds what

| Output | Script | Notes |
| --- | --- | --- |
| `docs/pipeline/*.svg` (16 How It Works diagrams) | `scripts/make_pipeline.py` | Renders the real tool on `sources/jupiter.png`. Set `PYTONE_SUBJECT=earth`, `sun` or `helix` to try another subject. |
| `docs/identity/*.svg` (mark, wordmark, lockups) | `scripts/make_lockup.py` | Needs `fonttools`. Draws the mark with `make_dense.py`, which builds on `make_glide.py` and `make_glide2.py`. |
| `docs/hero_dark.svg`, `docs/hero_light.svg` | `scripts/make_logo_color.py` | Runs the tool on `sources/lockup-stack.png`. The README hero is variant `C2`, copied from `build/logo-color/C2-{dark,light}.svg`. |
| `sources/lockup-stack.png`, `sources/lockup-side.png` | `scripts/make_readme_logo.py` | The lockups rasterized for the tool to read. Only needed if the mark or wordmark changes. |
| `docs/gallery/cards/*.svg` | `scripts/make_cards.py` | Wraps each `docs/gallery/<slug>.svg` in a captioned card, using `publish_manifest.json`. |

```bash
uv run python design/scripts/make_pipeline.py
uv run --with fonttools python design/scripts/make_lockup.py
python3 design/scripts/make_logo_color.py
python3 design/scripts/make_cards.py
```

Each script writes intermediate files to `design/build/` and final files to `docs/`.

## Rebuilding the gallery art

The gallery's art SVGs (`docs/gallery/<slug>.svg`) were rendered from prepped source images that
aren't kept here. To redo a piece, download the original from the source URL in the README's
credits, apply the prep noted in `publish_manifest.json`, and run the command shown in the
README gallery section.

## Utilities

- `scripts/tree.py` prints the project tree marked tracked, untracked or ignored. `scripts/tree-pane.sh` redraws it every few seconds.
- `scripts/chrome.sh` renders an SVG to PNG with headless Chrome, for checking how a file looks.
