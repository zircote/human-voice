"""Shared I/O utilities for the human-voice plugin.

Provides atomic JSON writing and timestamp helpers used across multiple
modules to avoid duplication.
"""

from __future__ import annotations

import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path


def atomic_write_json(path: Path, data: dict) -> None:
    """Write *data* as JSON to *path* atomically via temp-file + rename.

    Uses a temporary file in the same directory so that
    :func:`os.replace` is atomic on POSIX systems.
    """
    fd, tmp = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            f.write("\n")
        os.replace(tmp, path)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def now_iso() -> str:
    """Return the current time as an ISO-8601 string in UTC."""
    return datetime.now(timezone.utc).isoformat()
