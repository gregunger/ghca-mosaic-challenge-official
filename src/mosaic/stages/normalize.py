# SPDX-License-Identifier: LicenseRef-MOSAIC-Evaluation
"""Normalize source language without inventing missing customer facts."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any


def execute(request: Mapping[str, Any], evidence: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    known_evidence = {item["id"] for item in evidence}
    claims = list(request.get("claims", []))
    for claim in claims:
        for evidence_id in claim.get("evidenceIds", []):
            if evidence_id not in known_evidence:
                raise ValueError(
                    f"Claim {claim.get('id')!r} cites unknown evidence {evidence_id!r}."
                )

    return {
        "objectives": request["desiredOutcomes"],
        "stakeholders": request.get("stakeholders", []),
        "requirements": request.get("requirements", []),
        "constraints": request.get("constraints", []),
        "claims": claims,
        "preservedTerms": request.get("preservedTerms", []),
    }
