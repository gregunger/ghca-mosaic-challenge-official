# SPDX-License-Identifier: LicenseRef-MOSAIC-Evaluation
"""Identify gaps, risks, dependencies, assumptions, and questions."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any


def execute(request: Mapping[str, Any]) -> dict[str, Any]:
    analysis = request.get("analysisSeed", {})
    return {
        "gaps": analysis.get("gaps", []),
        "risks": analysis.get("risks", []),
        "dependencies": analysis.get("dependencies", []),
        "assumptions": analysis.get("assumptions", []),
        "unknowns": analysis.get("unknowns", []),
        "customerQuestions": analysis.get("customerQuestions", []),
    }
