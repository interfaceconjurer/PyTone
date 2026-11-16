"""Shared data types and validation at conversion and rendering boundaries."""

import math
import unicodedata

RGB = tuple[int, int, int]
ColorRows = list[list[tuple[str, RGB]]]


def positive_int(value: int, name: str) -> None:
    if type(value) is not int or value <= 0:
        raise ValueError(f"{name} must be a positive integer")


def finite_number(value: float, name: str, *, positive: bool = False) -> None:
    if (
        type(value) not in (int, float)
        or not math.isfinite(value)
        or (value <= 0 if positive else value < 0)
    ):
        domain = "positive" if positive else "nonnegative"
        raise ValueError(f"{name} must be a finite {domain} number")


def character_ramp(chars: str) -> None:
    if not isinstance(chars, str) or not chars:
        raise ValueError("chars must be a nonempty string")
    document_text(chars)
    if any(unicodedata.category(char) in {"Cc", "Zl", "Zp"} for char in chars):
        raise ValueError("chars must not contain control characters or line separators")


def rgb_color(color: RGB) -> None:
    if len(color) != 3 or any(type(c) is not int or not 0 <= c <= 255 for c in color):
        raise ValueError("colors must contain three integer RGB channels in the range 0-255")


def document_text(text: str) -> None:
    """Reject characters that cannot be represented in XML 1.0 / UTF-8 documents."""
    for char in text:
        value = ord(char)
        if not (
            char in "\t\n\r"
            or 0x20 <= value <= 0xD7FF
            or 0xE000 <= value <= 0xFFFD
            or 0x10000 <= value <= 0x10FFFF
        ):
            raise ValueError("text contains characters invalid in XML or UTF-8")


def color_rows(rows: ColorRows) -> None:
    """Accept empty art, or a rectangular grid of single glyphs and RGB colors."""
    width = len(rows[0]) if rows else 0
    for row in rows:
        if len(row) != width:
            raise ValueError("color rows must form a rectangular grid")
        for char, color in row:
            character_ramp(char)
            if len(char) != 1:
                raise ValueError("each cell must contain exactly one Unicode code point")
            rgb_color(color)
