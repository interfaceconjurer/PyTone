"""Image decoding, normalization, and conversion boundary regressions."""

from pathlib import Path

import pytest
from PIL import Image

from pytone import core
from pytone.core import adjust_color, get_color_data, image_to_ascii, load_image


@pytest.mark.parametrize(
    "alpha, expected", [(0, (0, 0, 0)), (128, (100, 50, 25)), (255, (200, 100, 50))]
)
def test_alpha_is_composited_over_black(tmp_path, alpha, expected):
    path = tmp_path / "alpha.png"
    Image.new("RGBA", (4, 4), (200, 100, 50, alpha)).save(path)
    assert load_image(path).getpixel((0, 0)) == expected
    assert get_color_data(path, width=4)[0][0][1] == expected


def test_palette_transparency(tmp_path):
    image = Image.new("P", (4, 4), 0)
    image.putpalette([255, 255, 255] + [0] * 765)
    path = tmp_path / "palette.png"
    image.save(path, transparency=0)
    assert load_image(path).getpixel((0, 0)) == (0, 0, 0)


def test_palette_is_converted_before_resampling(tmp_path):
    image = Image.new("P", (2, 1))
    image.putpalette([0, 0, 0, 255, 255, 255] + [0] * 762)
    image.putpixel((1, 0), 1)
    path = tmp_path / "palette.png"
    image.save(path)
    color = get_color_data(path, width=1, row_factor=1)[0][0][1]
    assert all(0 < channel < 255 for channel in color)


def test_exif_orientation_is_applied(tmp_path):
    image = Image.new("RGB", (2, 3), "white")
    image.putpixel((0, 0), (255, 0, 0))
    exif = Image.Exif()
    exif[274] = 6  # 90 degrees clockwise
    path = tmp_path / "oriented.png"
    image.save(path, exif=exif)
    original = path.read_bytes()
    result = load_image(path)
    assert result.size == (3, 2)
    assert result.getpixel((2, 0)) == (255, 0, 0)
    assert path.read_bytes() == original


@pytest.mark.parametrize("fail_decode", [False, True])
def test_source_is_closed_even_for_multiframe_images(tmp_path, monkeypatch, fail_decode):
    path = tmp_path / "animated.gif"
    Image.new("RGB", (4, 4), "red").save(
        path, save_all=True, append_images=[Image.new("RGB", (4, 4), "blue")]
    )
    opened = []
    original_open = Image.open

    def tracked_open(*args, **kwargs):
        source = original_open(*args, **kwargs)
        opened.append(source)
        return source

    monkeypatch.setattr(core.Image, "open", tracked_open)
    if fail_decode:

        def fail(*args, **kwargs):
            raise OSError("decode failed")

        monkeypatch.setattr(core.ImageOps, "exif_transpose", fail)
        with pytest.raises(OSError, match="decode failed"):
            load_image(path)
    else:
        result = load_image(path)
        assert result.getpixel((0, 0)) == (255, 0, 0)
    assert len(opened) == 1
    assert opened[0].fp is None


@pytest.mark.parametrize("mode", ["1", "L", "LA", "P", "RGB", "RGBA", "CMYK"])
def test_common_image_modes(tmp_path, mode):
    path = tmp_path / "image.tiff"
    Image.new(mode, (4, 4)).save(path)
    result = load_image(path)
    assert result.mode == "RGB"
    assert result.size == (4, 4)


@pytest.fixture
def white_image(tmp_path: Path) -> Path:
    path = tmp_path / "white.png"
    Image.new("RGB", (4, 4), "white").save(path)
    return path


@pytest.mark.parametrize("width", [0, -1, 1.5, True])
@pytest.mark.parametrize("convert", [image_to_ascii, get_color_data])
def test_invalid_width_has_a_clear_error(white_image, width, convert):
    with pytest.raises(ValueError, match="width must be a positive integer"):
        convert(white_image, width=width)


@pytest.mark.parametrize("chars", ["", "a\nb", "\x1b[31m", "\t", "\ud800", "\u2028"])
@pytest.mark.parametrize("convert", [image_to_ascii, get_color_data])
def test_invalid_ramps_are_rejected(white_image, chars, convert):
    with pytest.raises(ValueError, match=r"chars|text"):
        convert(white_image, chars=chars)


@pytest.mark.parametrize("name", ["saturation", "brightness", "row_factor"])
@pytest.mark.parametrize("value", [-1, float("nan"), float("inf"), float("-inf")])
def test_color_parameters_must_be_finite(white_image, name, value):
    with pytest.raises(ValueError, match=name):
        get_color_data(white_image, **{name: value})


@pytest.mark.parametrize(
    "gradient",
    [
        [],
        [(0, 0, 0)],
        [(0, 0, -1), (0, 0, 0)],
        [(0, 0, 256), (0, 0, 0)],
        [(0.5, 0, 0), (0, 0, 0)],
        [(0, 0), (0, 0, 0)],
    ],
)
def test_invalid_gradient_is_rejected(white_image, gradient):
    with pytest.raises(ValueError, match=r"gradient|RGB"):
        get_color_data(white_image, gradient=gradient)


def test_conflicting_effects_are_rejected(white_image):
    with pytest.raises(ValueError, match="mutually exclusive"):
        get_color_data(white_image, rainbow=True, gradient=[(0, 0, 0), (255, 255, 255)])


@pytest.mark.parametrize("width, row_factor", [(4, 1), (1, 4), (4, 0.1)])
def test_gradient_reaches_both_stops_including_single_axes(white_image, width, row_factor):
    stops = [(255, 0, 0), (0, 255, 0), (0, 0, 255)]
    rows = get_color_data(white_image, width=width, row_factor=row_factor, gradient=stops)
    assert rows[0][0][1] == stops[0]
    assert rows[-1][-1][1] == stops[-1]


def test_black_gradient_stays_black_and_one_cell_uses_first_stop(white_image):
    rows = get_color_data(white_image, width=1, gradient=[(0, 0, 0), (0, 0, 0)])
    assert rows == [[(" ", (0, 0, 0))]]
    rows = get_color_data(white_image, width=1, gradient=[(255, 0, 0), (0, 0, 255)])
    assert rows[0][0][1] == (255, 0, 0)


def test_zero_adjustments_are_valid(white_image):
    rows = get_color_data(white_image, width=2, saturation=0, brightness=0)
    assert all(color == (0, 0, 0) for row in rows for _, color in row)
    assert adjust_color(255, 0, 0, saturation=0) == (255, 255, 255)


def test_plain_and_color_share_the_same_glyph_mapping(white_image):
    plain = image_to_ascii(white_image, width=4, invert=True)
    rows = get_color_data(white_image, width=4, invert=True)
    assert plain == "\n".join("".join(char for char, _ in row) for row in rows)
