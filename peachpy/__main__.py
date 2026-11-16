"""Entry point for `python -m peachpy`."""

import sys

from .cli import entrypoint

if __name__ == "__main__":
    sys.exit(entrypoint())
