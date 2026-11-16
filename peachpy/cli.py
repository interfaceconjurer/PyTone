"""Command-line interface for PeachPy (`peachpy`)."""

import argparse
import os
import re
import sys
from pathlib import Path

from PIL import Image

from .color import render_colored
from .contracts import RGB, character_ramp, finite_number, positive_int
from .core import (
    DEFAULT_CHARS,
    HTML_ROW_FACTOR,
    SVG_CELL_ASPECT,
    SVG_ROW_FACTOR,
    TERMINAL_ROW_FACTOR,
    get_color_data,
    image_to_ascii,
)
from .html_output import render_html
from .output import write_text
from .svg_output import render_svg


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="peachpy",
        description="Generate ASCII art from images.",
    )
    parser.add_argument("image", type=Path, help="Path to the input image")
    parser.add_argument(
        "-w",
        "--width",
        type=int,
        default=120,
        help="Output width in characters (default: %(default)s)",
    )
    parser.add_argument(
        "-c",
        "--chars",
        type=str,
        default=DEFAULT_CHARS,
        help='Character ramp from dark to light (default: "B S#&@$%%*!:. ")',
    )
    parser.add_argument(
        "-m",
        "--mode",
        choices=["plain", "color", "html", "svg"],
        default="color",
        help="Output mode (default: color)",
    )
    parser.add_argument(
        "--color-mode",
        choices=["auto", "truecolor", "256", "none"],
        default="auto",
        help="Terminal color mode (default: auto-detect)",
    )
    parser.add_argument(
        "-s",
        "--saturation",
        type=float,
        default=1.0,
        help="Saturation multiplier for color modes (default: 1.0, try 1.5-2.0 for more vibrant)",
    )
    parser.add_argument(
        "-b",
        "--brightness",
        type=float,
        default=1.0,
        help="Brightness multiplier for color modes (default: 1.0, try 1.2-1.5 for brighter)",
    )
    parser.add_argument(
        "--pixel-width",
        type=int,
        default=None,
        help="Output width in pixels for HTML or SVG mode",
    )
    parser.add_argument(
        "--invert",
        action="store_true",
        help="Invert the image colors (black becomes white, white becomes black)",
    )
    effects = parser.add_mutually_exclusive_group()
    effects.add_argument(
        "--rainbow",
        action="store_true",
        help="Apply rainbow gradient colors instead of original image colors",
    )
    effects.add_argument(
        "--gradient",
        type=str,
        default=None,
        help="Apply custom gradient from top-left to bottom-right with 2+ colors (e.g., '#FF0000,#0000FF' or '#3D1A4D,#9B59B6,#FFD700,#B8860B')",
    )
    parser.add_argument(
        "-o", "--output", type=Path, default=None, help="Save output to file instead of stdout"
    )
    return parser


def parse_gradient(gradient_str: str) -> list[RGB]:
    """Parse two or more comma-separated six-digit hex colors, with optional #."""
    parts = gradient_str.split(",")
    if len(parts) < 2:
        raise ValueError("gradient must have at least 2 colors separated by commas")
    colors = []
    for part in parts:
        value = part.strip().removeprefix("#")
        if re.fullmatch(r"[0-9a-fA-F]{6}", value) is None:
            raise ValueError(f"invalid hex color {part!r}: expected six hex digits")
        colors.append((int(value[:2], 16), int(value[2:4], 16), int(value[4:], 16)))
    return colors


def _convert(args: argparse.Namespace, gradient: list[RGB] | None) -> str:
    output_path = args.output
    if output_path is None and args.mode in {"html", "svg"}:
        output_path = Path(f"peachpy.{args.mode}")
    if output_path is not None and (
        output_path.resolve() == args.image.resolve()
        or (output_path.exists() and output_path.samefile(args.image))
    ):
        raise ValueError("output path must not refer to the input image")

    if args.mode == "plain":
        result = image_to_ascii(args.image, width=args.width, chars=args.chars, invert=args.invert)
    else:
        row_factors = {"html": HTML_ROW_FACTOR, "svg": SVG_ROW_FACTOR}
        rows = get_color_data(
            args.image,
            width=args.width,
            chars=args.chars,
            saturation=args.saturation,
            brightness=args.brightness,
            invert=args.invert,
            rainbow=args.rainbow,
            gradient=gradient,
            row_factor=row_factors.get(args.mode, TERMINAL_ROW_FACTOR),
        )
        if args.mode == "color":
            color_mode = args.color_mode
            if color_mode == "auto":
                color_mode = "none" if output_path is not None else None
            result = render_colored(rows, mode=color_mode)
        elif args.mode == "html":
            result = render_html(rows, title=args.image.stem, pixel_width=args.pixel_width)
        else:
            char_width = args.pixel_width / args.width if args.pixel_width is not None else 10.0
            result = render_svg(
                rows,
                title=args.image.stem,
                char_width=char_width,
                char_height=char_width * SVG_CELL_ASPECT,
            )

    if output_path is None:
        return result
    write_text(output_path, result)
    label = f" {args.mode.upper()}" if args.mode in {"html", "svg"} else ""
    return f"Saved{label} to {output_path}"


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        positive_int(args.width, "width")
        character_ramp(args.chars)
        finite_number(args.saturation, "saturation")
        finite_number(args.brightness, "brightness")
        if args.pixel_width is not None:
            positive_int(args.pixel_width, "pixel_width")
    except ValueError as error:
        parser.error(str(error))

    # Parse and validate gradient parameter
    try:
        gradient = parse_gradient(args.gradient) if args.gradient is not None else None
        result = _convert(args, gradient)
    except (OSError, ValueError, OverflowError, Image.DecompressionBombError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1

    # Keep stdout failures outside conversion error handling. Windows can report
    # a closed pipe as OSError(EINVAL), rather than BrokenPipeError.
    print(result, flush=True)
    return 0


def entrypoint() -> int:
    """Run the process CLI, including clean shutdown when a pipe reader exits."""
    try:
        try:
            return main()
        finally:
            # Also flush argparse output before its SystemExit (--help).
            sys.stdout.flush()
    except OSError:
        # Prevent Python from retrying the failed stdout flush during shutdown.
        with open(os.devnull, "w") as sink:
            os.dup2(sink.fileno(), sys.stdout.fileno())
        return 1
