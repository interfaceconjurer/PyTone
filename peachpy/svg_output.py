"""SVG output renderer for colored ASCII art."""

import xml.etree.ElementTree as ET
from pathlib import Path

from .contracts import ColorRows, color_rows, document_text, finite_number
from .output import write_text


def render_svg(
    rows: ColorRows,
    title: str = "ASCII Art",
    char_width: float = 10.0,
    char_height: float = 16.0,
) -> str:
    """Render color data as an SVG document.

    Args:
        rows: Output from core.get_color_data().
        title: SVG title.
        char_width: Width of each character in pixels.
        char_height: Height of each character (line height) in pixels.

    Returns:
        Complete SVG document as a string.
    """
    color_rows(rows)
    document_text(title)
    finite_number(char_width, "char_width", positive=True)
    finite_number(char_height, "char_height", positive=True)

    width = len(rows[0]) if rows else 0
    height = len(rows)
    svg_width = width * char_width
    svg_height = height * char_height

    # Create SVG root element
    svg = ET.Element(
        "svg",
        xmlns="http://www.w3.org/2000/svg",
        viewBox=f"0 0 {svg_width} {svg_height}",
        width=str(svg_width),
        height=str(svg_height),
    )

    # Add title
    title_elem = ET.SubElement(svg, "title")
    title_elem.text = title

    # Add style for monospace font
    style = ET.SubElement(svg, "style")
    style.text = """
        text {
            font-family: "Courier New", Courier, monospace;
            font-size: 14px;
            dominant-baseline: hanging;
        }
    """

    # Add text elements for each character
    for y, row in enumerate(rows):
        for x, (char, (r, g, b)) in enumerate(row):
            if char.strip():  # Skip pure whitespace
                text = ET.SubElement(
                    svg,
                    "text",
                    x=str(x * char_width),
                    y=str(y * char_height),
                    fill=f"rgb({r},{g},{b})",
                )
                text.text = char

    # Convert to string with XML declaration
    return ET.tostring(svg, encoding="unicode", xml_declaration=True)


def save_svg(
    rows: ColorRows,
    output_path: str | Path,
    title: str = "ASCII Art",
    char_width: float = 10.0,
    char_height: float = 16.0,
) -> Path:
    """Render and save colored ASCII art as an SVG file.

    Returns the path to the saved file.
    """
    svg_content = render_svg(rows, title=title, char_width=char_width, char_height=char_height)
    return write_text(output_path, svg_content)
