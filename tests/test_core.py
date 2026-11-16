"""Tests for peachpy core functionality."""

from pathlib import Path

import pytest
from PIL import Image

from peachpy.core import (
    DEFAULT_CHARS,
    SVG_CELL_ASPECT,
    SVG_ROW_FACTOR,
    get_color_data,
    image_to_ascii,
    pixels_to_ascii,
    resize_image,
)


@pytest.fixture
def sample_image(tmp_path: Path) -> Path:
    """Create a small solid-color test image."""
    img = Image.new("RGB", (100, 100), color=(128, 64, 200))
    path = tmp_path / "test.png"
    img.save(path)
    return path


@pytest.fixture
def gradient_image(tmp_path: Path) -> Path:
    """Create a horizontal gradient test image (black → white)."""
    img = Image.new("RGB", (256, 10))
    for x in range(256):
        for y in range(10):
            img.putpixel((x, y), (x, x, x))
    path = tmp_path / "gradient.png"
    img.save(path)
    return path


class TestResizeImage:
    def test_preserves_target_width(self):
        img = Image.new("RGB", (400, 200))
        resized = resize_image(img, new_width=80)
        assert resized.width == 80

    def test_aspect_ratio_correction(self):
        img = Image.new("RGB", (400, 400))
        resized = resize_image(img, new_width=100)
        # Height should be ~55 due to 0.55 correction factor
        assert resized.height == 55


class TestPixelsToAscii:
    def test_output_length_matches_pixels(self):
        img = Image.new("L", (10, 10), color=128)
        result = pixels_to_ascii(img)
        assert len(result) == 100

    def test_dark_pixels_use_early_chars(self):
        img = Image.new("L", (1, 1), color=0)
        result = pixels_to_ascii(img, chars="AB")
        assert result == "A"

    def test_bright_pixels_use_late_chars(self):
        img = Image.new("L", (1, 1), color=255)
        result = pixels_to_ascii(img, chars="AB")
        assert result == "B"

    def test_custom_chars(self):
        img = Image.new("L", (1, 1), color=0)
        result = pixels_to_ascii(img, chars="XY")
        assert result == "X"


class TestImageToAscii:
    def test_returns_multiline_string(self, sample_image: Path):
        result = image_to_ascii(sample_image, width=40)
        lines = result.split("\n")
        assert len(lines) > 1
        assert all(len(line) == 40 for line in lines)

    def test_file_not_found(self):
        with pytest.raises(FileNotFoundError):
            image_to_ascii("/nonexistent/image.png")

    def test_custom_width(self, sample_image: Path):
        for width in [20, 60, 150]:
            result = image_to_ascii(sample_image, width=width)
            first_line = result.split("\n")[0]
            assert len(first_line) == width


class TestGetColorData:
    def test_returns_rows_of_tuples(self, sample_image: Path):
        rows = get_color_data(sample_image, width=40)
        assert len(rows) > 0
        assert len(rows[0]) == 40

        char, color = rows[0][0]
        assert isinstance(char, str) and len(char) == 1
        assert len(color) == 3
        assert all(0 <= c <= 255 for c in color)

    def test_gradient_produces_varied_chars(self, gradient_image: Path):
        rows = get_color_data(gradient_image, width=80)
        # Flatten chars and check we get more than one unique character
        chars = {char for row in rows for char, _ in row}
        assert len(chars) > 1


class TestRowFactor:
    def test_default_row_factor_unchanged(self):
        img = Image.new("RGB", (400, 400))
        assert resize_image(img, new_width=100).height == 55

    def test_svg_row_factor_matches_cell_aspect(self):
        img = Image.new("RGB", (400, 400))
        resized = resize_image(img, new_width=100, row_factor=SVG_ROW_FACTOR)
        # 100 columns × 1.6 cell height ≈ 100 cell widths: a square stays square.
        assert resized.height == 62
        assert abs(resized.height * SVG_CELL_ASPECT - 100) < SVG_CELL_ASPECT

    def test_tiny_image_has_at_least_one_row(self):
        img = Image.new("RGB", (1000, 1))
        assert resize_image(img, new_width=10).height == 1


class TestLongRamps:
    @staticmethod
    def _ramp_image() -> Image.Image:
        img = Image.new("L", (256, 1))
        for x in range(256):
            img.putpixel((x, 0), x)
        return img

    def test_ramp_longer_than_256_does_not_crash(self):
        chars = "".join(chr(0x4E00 + i) for i in range(300))
        result = pixels_to_ascii(self._ramp_image(), chars=chars)
        assert len(result) == 256
        assert result[0] == chars[0]
        assert result[-1] == chars[(255 * 300) // 256]

    def test_short_ramp_bucketing_unchanged(self):
        # Regression guard: ramps of ≤256 chars keep the original 256 // n bucketing.
        chars = DEFAULT_CHARS
        divisor = 256 // len(chars)
        expected = "".join(chars[min(p // divisor, len(chars) - 1)] for p in range(256))
        assert pixels_to_ascii(self._ramp_image(), chars=chars) == expected


class TestInvertWithColorEffects:
    @pytest.fixture
    def white_on_black(self, tmp_path: Path) -> Path:
        """Black image with a white square in the middle."""
        img = Image.new("RGB", (40, 40), color=(0, 0, 0))
        for x in range(10, 30):
            for y in range(10, 30):
                img.putpixel((x, y), (255, 255, 255))
        path = tmp_path / "square.png"
        img.save(path)
        return path

    # Constant-hue gradient and a fixed column, so only the shape modulation differs.
    @pytest.mark.parametrize(
        "kwargs", [{"gradient": [(255, 0, 0), (255, 0, 0)]}, {"rainbow": True}]
    )
    def test_invert_flips_color_modulation(self, white_on_black: Path, kwargs):
        normal = get_color_data(white_on_black, width=20, **kwargs)
        inverted = get_color_data(white_on_black, width=20, invert=True, **kwargs)
        x, edge, centre = 10, 0, len(normal) // 2  # top edge is black, centre is white
        assert normal[centre][x][1] != normal[edge][x][1]
        # With invert, the white square should take the black background's colour and
        # vice versa, so the subject (not the background) ends up bright.
        assert inverted[centre][x][1] == normal[edge][x][1]
        assert inverted[edge][x][1] == normal[centre][x][1]
        # Glyphs still invert as before.
        assert inverted[centre][x][0] == normal[edge][x][0]
