"""Entry point for `python -m pytone`."""

import sys

from .cli import entrypoint

if __name__ == "__main__":
    sys.exit(entrypoint())
