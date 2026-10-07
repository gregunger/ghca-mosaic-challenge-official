# SPDX-License-Identifier: LicenseRef-MOSAIC-Evaluation
"""Prepare the customer engagement and decision package."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any


def execute(request: Mapping[str, Any], analysis: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "meeting": {
            "durationMinutes": 30,
            "objective": (
                "Validate evidence, resolve priority unknowns, and choose the next design action."
            ),
            "agenda": [
                {"minutes": 4, "topic": "Outcome and current-state confirmation"},
                {"minutes": 8, "topic": "Evidence, gaps, and risk review"},
                {"minutes": 10, "topic": "Three-option comparison"},
                {"minutes": 5, "topic": "Decision and evidence requests"},
                {"minutes": 3, "topic": "Owners and next steps"},
            ],
        },
        "priorityQuestions": analysis.get("customerQuestions", []),
        "releaseAudience": request.get("releaseAudience", "synthetic-demo-reviewers"),
        "artifacts": [
            "intake-report.md",
            "evidence-appendix.md",
            "option-matrix.md",
            "architecture-brief.md",
            "meeting-request.md",
            "meeting-agenda.md",
            "talk-track.md",
            "human-review.md",
        ],
    }
