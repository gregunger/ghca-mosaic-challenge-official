# SPDX-License-Identifier: LicenseRef-MOSAIC-Evaluation
"""Atomic local text writes shared by job records and operator diagnostics."""

from __future__ import annotations

import os
from pathlib import Path
from uuid import uuid4


def atomic_write_text(path: Path, content: str) -> None:
    temporary = path.with_name(f".{path.name}.{uuid4().hex}.tmp")
    try:
        with temporary.open("x", encoding="utf-8", newline="\n") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)
