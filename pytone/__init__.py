"""PyTone: generate ASCII art from images.

Usage:
    from pytone import image_to_ascii, get_color_data

    # Plain text ASCII art
    art = image_to_ascii("photo.jpg", width=100)

    # With color data for custom rendering
    rows = get_color_data("photo.jpg", width=100)
"""

from .core import DEFAULT_CHARS, get_color_data, image_to_ascii

__all__ = ["DEFAULT_CHARS", "get_color_data", "image_to_ascii"]
__version__ = "0.1.0"
