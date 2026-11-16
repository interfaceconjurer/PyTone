"""End-to-end tests for the CLI output modes."""

import re
from pathlib import Path

import pytest
from PIL import Image

from peachpy.cli import main


@pytest.fixture
def square_image(tmp_path: Path) -> Path:
    img = Image.new("RGB", (200, 200), color=(200, 200, 200))
    path = tmp_path / "square.png"
    img.save(path)
    return path


def _svg_size(path: Path) -> tuple[float, float]:
    head = path.read_text(encoding="utf-8")[:500]
    m = re.search(r'width="([\d.]+)" height="([\d.]+)"', head)
    assert m, head
    return float(m.group(1)), float(m.group(2))


@pytest.mark.parametrize("pixel_width", [None, 800])
def test_svg_preserves_aspect_ratio(square_image: Path, tmp_path: Path, pixel_width):
    out = tmp_path / "out.svg"
    argv = [str(square_image), "-m", "svg", "-w", "100", "-o", str(out)]
    if pixel_width:
        argv += ["--pixel-width", str(pixel_width)]
    assert main(argv) == 0
    w, h = _svg_size(out)
    # Square in, square out (within one row of rounding).
    assert abs(h / w - 1.0) < 0.02


def test_svg_default_cell_size_unchanged(square_image: Path, tmp_path: Path):
    out = tmp_path / "out.svg"
    assert main([str(square_image), "-m", "svg", "-w", "10", "-o", str(out)]) == 0
    w, _ = _svg_size(out)
    assert w == 100.0  # 10 columns × 10px
    assert "font-size: 14px" in out.read_text(encoding="utf-8")


def test_plain_mode_keeps_terminal_aspect(square_image: Path, tmp_path: Path):
    out = tmp_path / "out.txt"
    assert main([str(square_image), "-m", "plain", "-w", "100", "-o", str(out)]) == 0
    assert len(out.read_text(encoding="utf-8").splitlines()) == 55


def test_html_mode_writes_file(square_image: Path, tmp_path: Path):
    out = tmp_path / "out.html"
    assert main([str(square_image), "-m", "html", "-w", "100", "-o", str(out)]) == 0
    body = out.read_text(encoding="utf-8")
    assert body.count("\n") >= 60  # 0.6 row factor → 60 rows


def test_bad_gradient_is_an_error(square_image: Path, tmp_path: Path):
    out = tmp_path / "out.svg"
    assert main([str(square_image), "-m", "svg", "--gradient", "#FFF,#000", "-o", str(out)]) == 1
