# AGENTS.md

Guidance for AI coding agents working with this repo.

## Installing for a user (not developing)

See [README → Install](README.md#install). In short:

```bash
uv --version || curl -LsSf https://astral.sh/uv/install.sh | sh
uv tool install git+https://github.com/interfaceconjurer/ascii-image-generator
ascii-art --help
```

For CLI behaviour (output paths, piping, exit codes), see
[README → Notes for Scripts and AI Agents](README.md#notes-for-scripts-and-ai-agents).

## Developing

```bash
uv venv && uv pip install -e ".[dev]"
uv run pytest
uv run ruff check .
```

- Python ≥3.10, single runtime dependency: Pillow.
- Package `ascii_art/`: `cli.py` (argparse entry point `ascii-art`), `core.py` (resize,
  grayscale, glyph mapping, color data), `color.py` (ANSI), `html_output.py`, `svg_output.py`.
- Tests live in `tests/`. Run them before and after changes.
- `scratch/` holds local working files and isn't part of the package.
