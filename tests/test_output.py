"""File integrity under actual write and replacement failures."""

import os
from contextlib import contextmanager

import pytest

from pytone import output


@pytest.mark.parametrize("existing", [False, True])
@pytest.mark.parametrize("stage", ["write", "replace"])
def test_failed_save_preserves_destination_and_cleans_up(tmp_path, monkeypatch, existing, stage):
    path = tmp_path / "output.txt"
    if existing:
        path.write_text("original", encoding="utf-8")
    if stage == "replace":

        def fail_replace(*args):
            raise OSError("replacement failed")

        monkeypatch.setattr(output.os, "replace", fail_replace)
    else:
        original_tempfile = output.tempfile.NamedTemporaryFile

        @contextmanager
        def failing_tempfile(*args, **kwargs):
            with original_tempfile(*args, **kwargs) as stream:

                def fail_write(content):
                    stream.file.write(content[:3])
                    raise OSError("write failed")

                monkeypatch.setattr(stream, "write", fail_write)
                yield stream

        monkeypatch.setattr(output.tempfile, "NamedTemporaryFile", failing_tempfile)
    with pytest.raises(OSError, match="failed"):
        output.write_text(path, "replacement")
    assert path.exists() is existing
    if existing:
        assert path.read_text(encoding="utf-8") == "original"
    assert list(tmp_path.iterdir()) == ([path] if existing else [])


def test_successful_save_is_utf8_and_cleans_up(tmp_path):
    path = tmp_path / "output.txt"
    assert output.write_text(path, "桃\n") == path
    assert path.read_bytes() == "桃\n".encode()
    assert list(tmp_path.iterdir()) == [path]


@pytest.mark.skipif(os.name == "nt", reason="POSIX permission bits")
def test_replacement_preserves_file_permissions(tmp_path):
    path = tmp_path / "output.txt"
    path.write_text("original")
    path.chmod(0o640)
    output.write_text(path, "new")
    assert path.stat().st_mode & 0o777 == 0o640


@pytest.mark.skipif(os.name == "nt", reason="symlinks require extra privileges on Windows")
def test_save_follows_existing_symlink(tmp_path):
    target = tmp_path / "target.txt"
    target.write_text("original")
    link = tmp_path / "link.txt"
    link.symlink_to(target)
    output.write_text(link, "new")
    assert link.is_symlink()
    assert target.read_text() == "new"
