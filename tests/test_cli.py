"""End-to-end tests for the CLI output modes."""

import os
import re
import subprocess
import sys
import sysconfig
from pathlib import Path

import pytest
from PIL import Image

from peachpy.cli import main, parse_gradient

CONSOLE_SCRIPT = str(
    Path(sysconfig.get_path("scripts")) / ("peachpy.exe" if os.name == "nt" else "peachpy")
)


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
    assert w == 100.0  # 10 columns x 10px
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


@pytest.mark.parametrize(
    "options",
    [
        ["--width", "0"],
        ["--width", "-1"],
        ["--chars", ""],
        ["--chars", "a\nb"],
        ["--saturation", "nan"],
        ["--brightness", "inf"],
        ["--saturation", "-1"],
        ["--pixel-width", "0"],
        ["--pixel-width", "-1"],
        ["--rainbow", "--gradient", "#000000,#FFFFFF"],
    ],
)
def test_invalid_options_are_usage_errors(square_image, capsys, options):
    with pytest.raises(SystemExit) as error:
        main([str(square_image), *options])
    assert error.value.code == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "error:" in captured.err
    assert "Traceback" not in captured.err


@pytest.mark.parametrize("mode", ["plain", "color", "html", "svg"])
@pytest.mark.parametrize("kind", ["missing", "corrupt", "directory", "truncated"])
def test_input_failures_are_reported_cleanly(tmp_path, capsys, mode, kind):
    path = tmp_path / "input.png"
    if kind == "corrupt":
        path.write_bytes(b"not an image")
    elif kind == "directory":
        path.mkdir()
    elif kind == "truncated":
        Image.new("RGB", (200, 200), "red").save(path)
        path.write_bytes(path.read_bytes()[:50])
    out = tmp_path / "out.txt"
    assert main([str(path), "-m", mode, "-o", str(out)]) == 1
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "Error:" in captured.err
    assert "Traceback" not in captured.err
    assert not out.exists()


@pytest.mark.parametrize("mode", ["plain", "color", "html", "svg"])
def test_output_cannot_replace_source_image(square_image, capsys, mode):
    original = square_image.read_bytes()
    assert main([str(square_image), "-m", mode, "-o", str(square_image)]) == 1
    assert square_image.read_bytes() == original
    assert "input image" in capsys.readouterr().err


@pytest.mark.skipif(os.name == "nt", reason="symlinks require extra privileges on Windows")
@pytest.mark.parametrize("link_kind", ["symbolic", "hard"])
def test_output_alias_cannot_replace_source_image(square_image, tmp_path, link_kind):
    alias = tmp_path / "alias.png"
    if link_kind == "symbolic":
        alias.symlink_to(square_image)
    else:
        os.link(square_image, alias)
    original = square_image.read_bytes()
    assert main([str(square_image), "-m", "plain", "-o", str(alias)]) == 1
    assert alias.read_bytes() == original
    assert square_image.read_bytes() == original


@pytest.mark.parametrize("mode", ["html", "svg"])
def test_default_document_filename_cannot_replace_source(tmp_path, monkeypatch, mode):
    path = tmp_path / f"peachpy.{mode}"
    Image.new("RGB", (4, 4), "red").save(path, format="PNG")
    original = path.read_bytes()
    monkeypatch.chdir(tmp_path)
    assert main([str(path), "-m", mode]) == 1
    assert path.read_bytes() == original


@pytest.mark.parametrize("mode", ["plain", "color", "html", "svg"])
def test_missing_output_directory_is_a_clean_error(square_image, tmp_path, capsys, mode):
    out = tmp_path / "missing" / "out.txt"
    assert main([str(square_image), "-m", mode, "-w", "4", "-o", str(out)]) == 1
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "Error:" in captured.err
    assert "Traceback" not in captured.err


@pytest.mark.parametrize("mode", ["html", "svg"])
def test_document_default_outputs(square_image, tmp_path, monkeypatch, mode):
    monkeypatch.chdir(tmp_path)
    assert main([str(square_image), "-m", mode, "-w", "4"]) == 0
    assert (tmp_path / f"peachpy.{mode}").is_file()


def test_file_auto_color_does_not_depend_on_stdout_terminal(square_image, tmp_path, monkeypatch):
    monkeypatch.setattr("sys.stdout.isatty", lambda: True)
    monkeypatch.setenv("COLORTERM", "truecolor")
    out = tmp_path / "out.txt"
    assert main([str(square_image), "-w", "4", "-o", str(out)]) == 0
    assert "\x1b" not in out.read_text()
    assert main([str(square_image), "-w", "4", "--color-mode", "truecolor", "-o", str(out)]) == 0
    assert "\x1b[38;2;" in out.read_text()


def test_piped_auto_output_has_no_status_or_ansi(square_image, capsys):
    assert main([str(square_image), "-w", "4"]) == 0
    captured = capsys.readouterr()
    assert captured.err == ""
    assert "Saved" not in captured.out
    assert "\x1b" not in captured.out
    assert all(len(line) == 4 for line in captured.out.splitlines())


@pytest.mark.parametrize(
    "value",
    [
        "",
        "#FFFFFF",
        "#FFF,#000",
        "##000000,#FFFFFF",
        "+00000,#FFFFFF",
        "#GG0000,#FFFFFF",
        "#000000,",
    ],
)
def test_gradient_parser_rejects_malformed_stops(value):
    with pytest.raises(ValueError):
        parse_gradient(value)


def test_gradient_parser_accepts_optional_hashes_and_surrounding_spaces():
    assert parse_gradient(" #ff0000,00FF00, #0000ff ") == [(255, 0, 0), (0, 255, 0), (0, 0, 255)]


def test_empty_gradient_is_not_silently_ignored(square_image, capsys):
    assert main([str(square_image), "--gradient", ""]) == 1
    assert "gradient" in capsys.readouterr().err


def test_width_exceeding_pillow_limits_is_a_clean_error(square_image, capsys):
    assert main([str(square_image), "-w", str(10**100)]) == 1
    captured = capsys.readouterr()
    assert "Error:" in captured.err
    assert "Traceback" not in captured.err


def test_decompression_bomb_protection_is_preserved(square_image, monkeypatch, capsys):
    monkeypatch.setattr(Image, "MAX_IMAGE_PIXELS", 1)
    assert main([str(square_image)]) == 1
    captured = capsys.readouterr()
    assert "Error:" in captured.err
    assert "Traceback" not in captured.err


@pytest.mark.parametrize("command", [[sys.executable, "-m", "peachpy"], [CONSOLE_SCRIPT]])
def test_installed_entrypoints_work_outside_the_repo(square_image, tmp_path, command):
    result = subprocess.run(
        [*command, str(square_image), "-m", "plain", "-w", "4"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0
    assert result.stderr == ""
    assert all(len(line) == 4 for line in result.stdout.splitlines())


@pytest.mark.parametrize("command", [[sys.executable, "-m", "peachpy"], [CONSOLE_SCRIPT]])
@pytest.mark.parametrize("options", [["-m", "plain"], ["--help"]])
def test_closed_stdout_pipe_is_a_clean_process_exit(square_image, command, options):
    read_fd, write_fd = os.pipe()
    os.close(read_fd)
    with os.fdopen(write_fd, "wb") as pipe:
        result = subprocess.run(
            [*command, str(square_image), *options],
            stdout=pipe,
            stderr=subprocess.PIPE,
            timeout=30,
        )
    assert result.returncode == 1
    assert result.stderr == b""
