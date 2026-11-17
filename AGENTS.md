# AGENTS.md

Guidance for AI coding agents working with this repo.

## Installing for a user (not developing)

See [README → Install](README.md#install). In short:

```bash
uv --version || curl -LsSf https://astral.sh/uv/install.sh | sh
uv tool install git+https://github.com/interfaceconjurer/PyTone
pytone --help
```

For CLI behaviour (output paths, piping, exit codes), see
[README → Notes for Scripts and AI Agents](README.md#notes-for-scripts-and-ai-agents).

## Developing

```bash
uv venv && uv pip install -e ".[dev]"
uv run pytest
uv run ruff check .
```

- Python ≥3.11, single runtime dependency: Pillow ≥13.0.
- Package `pytone/`: `cli.py` (argparse entry point `pytone`), `core.py` (resize,
  grayscale, glyph mapping, color data), `color.py` (ANSI), `html_output.py`, `svg_output.py`.
- Tests live in `tests/`. Run them before and after changes.
- `design/` holds the scripts, source images and font that build the artwork in `docs/`; see
  [design/README.md](design/README.md). It isn't part of the package.
- `docs/identity/` is the PyTone brand set (mark, wordmark, lockups).
