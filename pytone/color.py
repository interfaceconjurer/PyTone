"""ANSI color output for terminal rendering."""

import os
import sys

from .contracts import ColorRows, color_rows, rgb_color


def supports_truecolor() -> bool:
    """Detect whether the terminal supports 24-bit truecolor."""
    colorterm = os.environ.get("COLORTERM", "").lower()
    return colorterm in ("truecolor", "24bit")


def supports_256color() -> bool:
    """Detect whether the terminal supports 256 colors."""
    term = os.environ.get("TERM", "")
    return "256color" in term or supports_truecolor()


def detect_color_mode() -> str:
    """Auto-detect the best color mode for the current terminal.

    Returns:
        'truecolor', '256', or 'none'
    """
    if not sys.stdout.isatty():
        return "none"
    if supports_truecolor():
        return "truecolor"
    if supports_256color():
        return "256"
    return "none"


def rgb_to_ansi_truecolor(r: int, g: int, b: int) -> str:
    """Return ANSI escape code for 24-bit truecolor foreground."""
    rgb_color((r, g, b))
    return f"\033[38;2;{r};{g};{b}m"


def rgb_to_ansi_256(r: int, g: int, b: int) -> str:
    """Convert RGB to the nearest ANSI 256-color and return escape code.

    Compare the 6x6x6 color cube and grayscale ramp using squared RGB distance.
    The first 16 colors are terminal-defined, so they cannot be matched reliably.
    """
    rgb_color((r, g, b))
    levels = (0, 95, 135, 175, 215, 255)
    r_idx, g_idx, b_idx = (
        min(range(6), key=lambda i: abs(channel - levels[i])) for channel in (r, g, b)
    )
    color_index = 16 + 36 * r_idx + 6 * g_idx + b_idx
    cube_distance = sum(
        (channel - levels[index]) ** 2
        for channel, index in zip((r, g, b), (r_idx, g_idx, b_idx), strict=True)
    )
    gray_index = max(0, min(23, round(((r + g + b) / 3 - 8) / 10)))
    gray_value = 8 + gray_index * 10
    gray_distance = sum((channel - gray_value) ** 2 for channel in (r, g, b))
    if gray_distance < cube_distance:
        color_index = 232 + gray_index
    return f"\033[38;5;{color_index}m"


RESET = "\033[0m"


def colorize_char(char: str, r: int, g: int, b: int, mode: str = "truecolor") -> str:
    """Wrap a character in ANSI color escape codes.

    Args:
        char: The ASCII character.
        r, g, b: RGB color values (0-255).
        mode: 'truecolor', '256', or 'none'.
    """
    if mode == "truecolor":
        return f"{rgb_to_ansi_truecolor(r, g, b)}{char}{RESET}"
    elif mode == "256":
        return f"{rgb_to_ansi_256(r, g, b)}{char}{RESET}"
    elif mode == "none":
        return char
    raise ValueError(f"unknown color mode: {mode!r}")


def render_colored(
    rows: ColorRows,
    mode: str | None = None,
) -> str:
    """Render color data as an ANSI-colored string.

    Args:
        rows: Output from core.get_color_data().
        mode: 'truecolor', '256', 'none', or None for auto-detect.

    Returns:
        Multi-line string with ANSI escape codes.
    """
    color_rows(rows)
    if mode is None:
        mode = detect_color_mode()
    if mode not in {"truecolor", "256", "none"}:
        raise ValueError(f"unknown color mode: {mode!r}")

    lines = []
    for row in rows:
        line = "".join(colorize_char(char, *color, mode=mode) for char, color in row)
        lines.append(line)
    return "\n".join(lines)
