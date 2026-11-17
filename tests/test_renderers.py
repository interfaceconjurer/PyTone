"""Renderer contracts, escaping, and terminal palette regressions."""

import xml.etree.ElementTree as ET
from html.parser import HTMLParser

import pytest

from pytone.color import detect_color_mode, render_colored, rgb_to_ansi_256
from pytone.html_output import render_html, save_html
from pytone.svg_output import render_svg, save_svg

RENDERERS = [render_colored, render_html, render_svg]


@pytest.mark.parametrize("render", [render_html, render_svg])
@pytest.mark.parametrize("title", ["\x00", "\ud800", "\uffff"])
def test_invalid_document_text_is_rejected(render, title):
    with pytest.raises(ValueError, match="invalid"):
        render([], title=title)


@pytest.mark.parametrize("render", RENDERERS)
@pytest.mark.parametrize("rows", [[], [[]]])
def test_empty_art_is_renderable(render, rows):
    result = render(rows)
    if render is render_svg:
        root = ET.fromstring(result)
        assert root.tag == "{http://www.w3.org/2000/svg}svg"
        assert root.attrib["width"] == "0.0"


@pytest.mark.parametrize("render", RENDERERS)
@pytest.mark.parametrize(
    "rows",
    [
        [[("a", (0, 0, 0))], []],
        [[("ab", (0, 0, 0))]],
        [[("\x1b", (0, 0, 0))]],
        [[("a", (-1, 0, 0))]],
        [[("a", (0, 256, 0))]],
    ],
)
def test_malformed_art_is_rejected(render, rows):
    with pytest.raises(ValueError):
        render(rows)


def test_html_escapes_glyphs_and_title():
    class TextParser(HTMLParser):
        def __init__(self):
            super().__init__()
            self.in_art = False
            self.art = ""

        def handle_starttag(self, tag, attrs):
            if tag == "pre":
                self.in_art = True

        def handle_endtag(self, tag):
            if tag == "pre":
                self.in_art = False

        def handle_data(self, data):
            if self.in_art:
                self.art += data

    chars = '<&"桃'
    result = render_html([[(char, (10, 20, 30)) for char in chars]], title="</title><script>")
    assert "<title>&lt;/title&gt;&lt;script&gt;</title>" in result
    assert "<script>" not in result
    parser = TextParser()
    parser.feed(result)
    assert parser.art == chars


def test_svg_escapes_glyphs_and_title_without_global_namespace_changes():
    other = ET.Element("{http://www.w3.org/2000/svg}other")
    before = ET.tostring(other)
    chars = '<&"桃'
    result = render_svg([[(char, (10, 20, 30)) for char in chars]], title="</title><script>")
    root = ET.fromstring(result)
    ns = {"s": "http://www.w3.org/2000/svg"}
    assert root.find("s:title", ns).text == "</title><script>"
    assert "".join(node.text for node in root.findall("s:text", ns)) == chars
    assert ET.tostring(other) == before


@pytest.mark.parametrize("value", [0, -1, float("nan"), float("inf")])
def test_svg_rejects_invalid_cell_dimensions(value):
    with pytest.raises(ValueError, match="char_width"):
        render_svg([], char_width=value)
    with pytest.raises(ValueError, match="char_height"):
        render_svg([], char_height=value)


@pytest.mark.parametrize("value", [0, -1, 1.5])
def test_html_rejects_invalid_pixel_width(value):
    with pytest.raises(ValueError, match="pixel_width"):
        render_html([], pixel_width=value)


@pytest.mark.parametrize("save, suffix", [(save_html, ".html"), (save_svg, ".svg")])
def test_document_save_helpers_use_utf8(tmp_path, save, suffix):
    path = tmp_path / ("output" + suffix)
    assert save([[("桃", (1, 2, 3))]], path, title="桃") == path
    assert "桃" in path.read_text(encoding="utf-8")


@pytest.mark.parametrize(
    "color, expected",
    [
        ((0, 0, 0), 16),
        ((255, 255, 255), 231),
        ((95, 0, 0), 52),
        ((128, 128, 128), 244),
        ((8, 8, 8), 232),
    ],
)
def test_ansi_256_uses_actual_cube_levels_and_grays(color, expected):
    assert rgb_to_ansi_256(*color) == f"\x1b[38;5;{expected}m"


@pytest.mark.parametrize("mode", ["truecolor", "256", "none"])
def test_ansi_modes_preserve_glyphs(mode):
    rows = [[("A", (255, 0, 0)), ("桃", (0, 255, 0))]]
    result = render_colored(rows, mode=mode)
    if mode == "none":
        assert result == "A桃"
    else:
        assert result.endswith("桃\x1b[0m")


def test_ansi_unknown_mode_is_an_error():
    with pytest.raises(ValueError, match="unknown color mode"):
        render_colored([], mode="typo")


@pytest.mark.parametrize(
    "tty, colorterm, term, expected",
    [
        (False, "truecolor", "xterm-256color", "none"),
        (True, "truecolor", "xterm", "truecolor"),
        (True, "24bit", "xterm", "truecolor"),
        (True, "", "xterm-256color", "256"),
        (True, "", "dumb", "none"),
    ],
)
def test_terminal_detection(monkeypatch, tty, colorterm, term, expected):
    monkeypatch.setattr("sys.stdout.isatty", lambda: tty)
    monkeypatch.setenv("COLORTERM", colorterm)
    monkeypatch.setenv("TERM", term)
    assert detect_color_mode() == expected
