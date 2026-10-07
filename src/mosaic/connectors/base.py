# SPDX-License-Identifier: LicenseRef-MOSAIC-Evaluation
"""Provider-neutral evidence connector contract."""

from __future__ import annotations

from typing import Any, Protocol


class SourceConnector(Protocol):
    def acquire(self) -> list[dict[str, Any]]:
        """Return approved evidence records with immutable content hashes."""
        ...
