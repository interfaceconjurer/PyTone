"""Atomic UTF-8 file output shared by the CLI and document renderers."""

import os
import tempfile
from pathlib import Path


def write_text(path: str | Path, content: str) -> Path:
    """Replace a file only after the complete content has been written successfully.

    Follow existing symlinks, as Path.write_text does. A failed write or replacement
    leaves the existing destination intact and removes the temporary file.
    """
    path = Path(path)
    destination = path.resolve()
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            newline="\n",
            dir=destination.parent,
            prefix=f".{destination.name}.",
            suffix=".tmp",
            delete=False,
        ) as stream:
            temporary = Path(stream.name)
            stream.write(content)
        if destination.exists():
            temporary.chmod(destination.stat().st_mode & 0o777)
        os.replace(temporary, destination)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
    return path
