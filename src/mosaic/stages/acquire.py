# SPDX-License-Identifier: LicenseRef-MOSAIC-Evaluation
"""Acquire approved evidence through a constrained connector."""

from __future__ import annotations

from typing import Any

from mosaic.connectors.base import SourceConnector


def execute(connector: SourceConnector) -> dict[str, Any]:
    evidence = connector.acquire()
    return {
        "sourceCount": len(evidence),
        "sources": evidence,
        "boundary": "allowlisted_synthetic_sources_only",
    }
