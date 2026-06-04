"""Atomically insert a new dated entry at the top of a history file (newest-on-top),
idempotently. Never touches git.
"""
from __future__ import annotations

import os
import re
import tempfile
from pathlib import Path

from .parser import has_entry

_FIRST_ENTRY = re.compile(r"^##\s+\d{4}-\d{2}-\d{2}\b", re.M)
# Fallback anchor for an empty log: the protocol's "New entries go … below this line." + "---"
_MARKER = re.compile(r"New entries go immediately below this line\.\n+---\n", re.M)


class AlreadyLogged(Exception):
    pass


def insert_entry(path: str | Path, iso_date: str, block_md: str) -> None:
    """Splice `block_md` (a full `## date …` entry, no trailing separator) at the top of the log.

    Result places the block directly above the most-recent existing entry, separated by the
    standard `\\n\\n---\\n\\n`. Idempotent: raises AlreadyLogged if the date is already present.
    Atomic: writes to a temp file in the same dir and os.replace()s it in.
    """
    path = Path(path)
    text = path.read_text()
    if has_entry(path, iso_date):
        raise AlreadyLogged(f"{path.name} already has an entry for {iso_date}")

    block = block_md.rstrip("\n")
    m = _FIRST_ENTRY.search(text)
    if m:
        pos = m.start()
        new_text = text[:pos] + block + "\n\n---\n\n" + text[pos:]
    else:
        # No existing entries — insert right after the protocol marker.
        mk = _MARKER.search(text)
        if not mk:
            raise ValueError(f"{path.name}: could not locate insertion anchor")
        pos = mk.end()
        new_text = text[:pos] + "\n" + block + "\n\n---\n" + text[pos:]

    _atomic_write(path, new_text)


def append_to_entry(path: str | Path, iso_date: str, text: str) -> None:
    """Append `text` to the end of an existing dated entry (e.g. the CPS `**Notable:**`
    paragraph after the table), before that entry's closing `---` separator. Atomic."""
    path = Path(path)
    content = path.read_text()
    m = re.search(rf"^##\s+{re.escape(iso_date)}\b.*?$", content, re.M)
    if not m:
        raise ValueError(f"{path.name}: no entry for {iso_date}")
    sep = content.find("\n---\n", m.end())
    if sep == -1:
        raise ValueError(f"{path.name}: no closing separator for {iso_date} entry")
    before = content[:sep].rstrip("\n")
    new_text = before + "\n\n" + text.rstrip("\n") + "\n" + content[sep:]
    _atomic_write(path, new_text)


def _atomic_write(path: Path, content: str) -> None:
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), prefix=f".{path.name}.", suffix=".tmp")
    try:
        with os.fdopen(fd, "w") as f:
            f.write(content)
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise
