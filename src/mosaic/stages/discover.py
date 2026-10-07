# SPDX-License-Identifier: LicenseRef-MOSAIC-Evaluation
"""Discover and qualify the business problem."""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from typing import Any

from mosaic.transcript import validate_transcript

REQUIRED_FIELDS = (
    "customerId",
    "initiativeId",
    "sourceTicketRef",
    "initiativeTitle",
    "businessProblem",
    "targetUsers",
    "desiredOutcomes",
    "successMeasures",
)


def execute(request: Mapping[str, Any]) -> dict[str, Any]:
    missing = [field for field in REQUIRED_FIELDS if not request.get(field)]
    if missing:
        raise ValueError(f"Request is missing required fields: {', '.join(missing)}")
    if not str(request["initiativeId"]).startswith("SYN-"):
        raise ValueError("Synthetic initiativeId must start with 'SYN-'.")

    result = {
        "eligibility": "eligible_solution_initiative",
        "initiativeTitle": request["initiativeTitle"],
        "businessProblem": request["businessProblem"],
        "targetUsers": request["targetUsers"],
        "desiredOutcomes": request["desiredOutcomes"],
        "successMeasures": request["successMeasures"],
        "constraints": request.get("constraints", []),
        "classification": request.get("classification", "SYNTHETIC"),
        "submittedBy": {
            "displayName": request.get("submittedBy", "John Doe"),
            "basis": "user_provided" if "submittedBy" in request else "default_placeholder",
            "identityVerified": False,
        },
    }
    if request.get("inputMode") == "conversation":
        result["intakeContext"] = request["intakeContext"]
        if "intakeTranscript" in request:
            validate_transcript(request["intakeTranscript"], request["initiativeId"])
            result["intakeTranscript"] = deepcopy(request["intakeTranscript"])
        if request.get("analysisProvenance"):
            result["analysisProvenance"] = request["analysisProvenance"]
    return result
