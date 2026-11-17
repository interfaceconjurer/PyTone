"""Core ASCII art conversion logic."""

import colorsys
from pathlib import Path

from PIL import Image, ImageOps

from .contracts import RGB, ColorRows, character_ramp, finite_number, positive_int, rgb_color

# Default character ramp: dark → light
DEFAULT_CHARS = "B S#&@$%*!:. "

# Rows per column of source pixels. Terminal cells are roughly 1:1.8 (width:height),
# so 0.55 keeps terminal output in proportion.
TERMINAL_ROW_FACTOR = 0.55
# SVG cells are char_width x char_width*1.6, so rows must be sampled at 1/1.6.
SVG_CELL_ASPECT = 1.6
SVG_ROW_FACTOR = 1 / SVG_CELL_ASPECT
# HTML uses Courier New (advance width 0.6em) with line-height 1.0, a 0.6:1 cell.
HTML_ROW_FACTOR = 0.6


def load_image(path: str | Path) -> Image.Image:
    """Load the first frame as detached RGB, applying orientation and a black matte.

    The source file is always closed before returning, including for multi-frame
    images and decode failures. Pillow's decompression-bomb protections stay enabled.
    """
    with Image.open(path) as source:
        oriented = ImageOps.exif_transpose(source)
        if "A" not in oriented.getbands() and "transparency" not in oriented.info:
            return oriented.convert("RGB")
        rgba = oriented.convert("RGBA")
        background = Image.new("RGBA", rgba.size, (0, 0, 0, 255))
        return Image.alpha_composite(background, rgba).convert("RGB")


def resize_image(
    img: Image.Image, new_width: int = 120, row_factor: float = TERMINAL_ROW_FACTOR
) -> Image.Image:
    """Resize image while preserving aspect ratio.

    ``row_factor`` compensates for character cells being taller than wide. It should be
    the cell's width/height ratio: 0.55 for terminals (default), 1/1.6 for SVG output.
    """
    positive_int(new_width, "width")
    finite_number(row_factor, "row_factor", positive=True)
    width, height = img.size
    if width == 0 or height == 0:
        raise ValueError("image dimensions must be positive")
    aspect_ratio = height / width
    new_height = max(1, int(aspect_ratio * new_width * row_factor))
    return img.resize((new_width, new_height), resample=Image.Resampling.BICUBIC)


def adjust_color(
    r: int, g: int, b: int, saturation: float = 1.0, brightness: float = 1.0
) -> tuple[int, int, int]:
    """Adjust the saturation and brightness of an RGB color.

    Args:
        r, g, b: RGB values (0-255).
        saturation: Saturation multiplier (1.0 = no change, >1.0 = more saturated).
        brightness: Brightness multiplier (1.0 = no change, >1.0 = brighter).

    Returns:
        Adjusted (r, g, b) tuple.
    """
    rgb_color((r, g, b))
    finite_number(saturation, "saturation")
    finite_number(brightness, "brightness")
    if saturation == 1.0 and brightness == 1.0:
        return (r, g, b)

    # Convert RGB to HSV
    h, s, v = colorsys.rgb_to_hsv(r / 255.0, g / 255.0, b / 255.0)

    # Adjust saturation and brightness, clamp to [0, 1]
    s = min(s * saturation, 1.0)
    v = min(v * brightness, 1.0)

    # Convert back to RGB
    r_new, g_new, b_new = colorsys.hsv_to_rgb(h, s, v)
    return (int(r_new * 255), int(g_new * 255), int(b_new * 255))


def pixels_to_ascii(img: Image.Image, chars: str = DEFAULT_CHARS, invert: bool = False) -> str:
    """Map grayscale pixel values to ASCII characters.

    Args:
        img: A grayscale (mode 'L') image.
        chars: Character ramp from dark to light.
        invert: If True, invert the grayscale values (white becomes black, black becomes white).

    Returns:
        A single string of ASCII characters (no newlines).
    """
    character_ramp(chars)
    if img.mode != "L":
        raise ValueError("pixels_to_ascii requires a grayscale image in mode 'L'")
    # Raw L bytes contain one byte per pixel.
    pixels = img.tobytes()
    if invert:
        pixels = [255 - pixel for pixel in pixels]
    n = len(chars)
    if n > 256:
        # More glyphs than gray levels: spread pixels proportionally across the ramp.
        return "".join(chars[pixel * n // 256] for pixel in pixels)
    divisor = 256 // n
    return "".join(chars[min(pixel // divisor, n - 1)] for pixel in pixels)


def image_to_ascii(
    path: str | Path,
    width: int = 120,
    chars: str = DEFAULT_CHARS,
    invert: bool = False,
) -> str:
    """Convert an image file to plain ASCII art.

    Args:
        path: Path to the image file.
        width: Output width in characters.
        chars: Character ramp from dark to light.
        invert: If True, invert the grayscale values.

    Returns:
        Multi-line ASCII art string.
    """
    character_ramp(chars)
    positive_int(width, "width")
    img = load_image(path)
    img = resize_image(img, new_width=width)

    grayscale = img.convert("L")
    ascii_str = pixels_to_ascii(grayscale, chars, invert=invert)

    # Split into rows
    lines = [ascii_str[i : i + width] for i in range(0, len(ascii_str), width)]
    return "\n".join(lines)


def _gradient_color(stops: list[RGB], position: float, gray: float) -> RGB:
    """Interpolate every stop consistently, then preserve shape through HSV modulation."""
    scaled = position * (len(stops) - 1)
    segment = min(int(scaled), len(stops) - 2)
    fraction = scaled - segment
    first, second = stops[segment], stops[segment + 1]
    r, g, b = (
        (start + (end - start) * fraction) / 255.0 for start, end in zip(first, second, strict=True)
    )
    h, s, v = colorsys.rgb_to_hsv(r, g, b)
    # The power curve retains saturation in darker areas. Preserve the stop's
    # own brightness, scaling from 30% in shadows to 100% in highlights.
    r, g, b = colorsys.hsv_to_rgb(h, s * gray**0.5, v * (0.3 + 0.7 * gray))
    return (int(r * 255), int(g * 255), int(b * 255))


def get_color_data(
    path: str | Path,
    width: int = 120,
    chars: str = DEFAULT_CHARS,
    saturation: float = 1.0,
    brightness: float = 1.0,
    invert: bool = False,
    rainbow: bool = False,
    gradient: list[RGB] | None = None,
    row_factor: float = TERMINAL_ROW_FACTOR,
) -> ColorRows:
    """Convert an image to ASCII with per-character RGB color data.

    Args:
        path: Path to the image file.
        width: Output width in characters.
        chars: Character ramp from dark to light.
        saturation: Saturation multiplier (1.0 = no change, >1.0 = more vibrant).
        brightness: Brightness multiplier (1.0 = no change, >1.0 = brighter).
        invert: If True, invert the grayscale values for character mapping.
        rainbow: If True, apply rainbow gradient colors instead of original colors.
        gradient: If provided, apply custom gradient from top-left to bottom-right.
                 List of 2+ RGB tuples: [(r1,g1,b1), (r2,g2,b2), ...].
                 Colors are interpolated along the diagonal gradient path.
        row_factor: Cell width/height ratio used when resizing (see resize_image).

    Returns a list of rows, each row a list of (char, (r, g, b)) tuples.
    """
    positive_int(width, "width")
    character_ramp(chars)
    finite_number(saturation, "saturation")
    finite_number(brightness, "brightness")
    finite_number(row_factor, "row_factor", positive=True)
    if rainbow and gradient is not None:
        raise ValueError("rainbow and gradient are mutually exclusive")
    if gradient is not None:
        if len(gradient) < 2:
            raise ValueError("gradient must contain at least two colors")
        for color in gradient:
            rgb_color(color)

    img = load_image(path)
    img = resize_image(img, new_width=width, row_factor=row_factor)

    # Get RGB values from the resized image
    rgb_pixels = img.load()

    # Get ASCII characters from grayscale
    grayscale = img.convert("L")
    ascii_str = pixels_to_ascii(grayscale, chars, invert=invert)

    gray_pixels = grayscale.tobytes()

    # Pair each character with its color
    rows: ColorRows = []
    for y in range(img.height):
        row = []
        for x in range(img.width):
            idx = y * img.width + x
            char = ascii_str[idx]
            color: RGB = rgb_pixels[x, y]
            if invert:
                color = (255 - color[0], 255 - color[1], 255 - color[2])
            gray_val = gray_pixels[idx] / 255.0
            if invert:
                gray_val = 1.0 - gray_val

            # Apply rainbow gradient if requested
            if rainbow:
                # Create rainbow based on horizontal position
                hue = x / img.width
                # Use grayscale for saturation, keep brightness at maximum
                # Dark areas = less saturated (more white), bright areas = fully saturated
                r, g, b = colorsys.hsv_to_rgb(hue, gray_val, 1.0)
                color = (int(r * 255), int(g * 255), int(b * 255))

            elif gradient is not None:
                # Normalize only axes that have multiple cells. This reaches the
                # final stop for a single row/column, and uses the first for 1x1.
                axes = (img.width > 1) + (img.height > 1)
                t = (x / max(img.width - 1, 1) + y / max(img.height - 1, 1)) / max(axes, 1)
                color = _gradient_color(gradient, t, gray_val)

            # Apply color adjustments
            color = adjust_color(*color, saturation=saturation, brightness=brightness)
            row.append((char, color))
        rows.append(row)

    return rows
