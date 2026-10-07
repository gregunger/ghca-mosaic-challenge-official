# SPDX-License-Identifier: LicenseRef-MOSAIC-Evaluation
"""Generate three contrasting, evidence-aware architecture options."""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from typing import Any


def execute(request: Mapping[str, Any]) -> dict[str, Any]:
    if request.get("inputMode") == "conversation":
        draft = request.get("optionDraft")
        if not isinstance(draft, Mapping):
            raise ValueError(
                "Conversational intake requires its own optionDraft; no seeded fallback."
            )
        return deepcopy(dict(draft))
    options = [
        {
            "id": "OPT-A",
            "name": "Managed low-code agent",
            "pattern": "Managed agent platform with approved content connectors",
            "bestWhen": "Rapid adoption and managed lifecycle controls outweigh bespoke behavior.",
            "strengths": ["Fastest path to pilot", "Managed authoring and channel lifecycle"],
            "tradeoffs": [
                "Less control over custom orchestration",
                "Connector fit requires validation",
            ],
            "conditions": ["Approved connector coverage", "Tenant governance configured"],
            "disqualifiers": ["Required behavior exceeds extension model"],
            "criterionAssessments": {
                "Outcome alignment": "Validate policy answers and human escalation in a pilot.",
                "Evidence and grounding": "Check managed connector coverage and citation behavior.",
                "Identity and data boundary": "Verify source permissions survive retrieval.",
                "Extensibility": "Stay within the platform's supported extension model.",
                "Lifecycle governance": "Use managed publishing with approved change controls.",
                "Operating ownership": "Assign platform and content owners.",
                "Cost and adoption": "Estimate licensing and configuration effort; not measured.",
            },
        },
        {
            "id": "OPT-B",
            "name": "Custom governed application",
            "pattern": "Custom application with explicit API and retrieval boundaries",
            "bestWhen": "Custom orchestration, evaluation, and integration control are primary.",
            "strengths": [
                "Maximum extensibility",
                "Fine-grained evaluation and integration control",
            ],
            "tradeoffs": ["Higher engineering and operating burden", "Longer controlled rollout"],
            "conditions": ["Product engineering ownership", "Approved model and region"],
            "disqualifiers": ["No funded operations owner"],
            "criterionAssessments": {
                "Outcome alignment": "Engineer and evaluate policy answers and escalation.",
                "Evidence and grounding": "Own retrieval, citation, and evaluation behavior.",
                "Identity and data boundary": "Implement and test user-context authorization.",
                "Extensibility": "Custom orchestration within approved service limits.",
                "Lifecycle governance": "Own releases, regression checks, and monitoring.",
                "Operating ownership": "Requires a funded product engineering and service team.",
                "Cost and adoption": "Estimate build and operating costs; not measured.",
            },
        },
        {
            "id": "OPT-C",
            "name": "Hybrid governed experience",
            "pattern": (
                "Managed conversational surface with policy and retrieval services behind "
                "typed APIs"
            ),
            "bestWhen": "Managed adoption and custom policy enforcement are both required.",
            "strengths": ["Balanced extensibility", "Separates experience from governed services"],
            "tradeoffs": ["More integration boundaries", "Requires clear dual-platform ownership"],
            "conditions": ["API ownership", "Identity propagation design", "Joint lifecycle model"],
            "disqualifiers": ["Cross-platform ownership cannot be assigned"],
            "criterionAssessments": {
                "Outcome alignment": "Validate the managed experience and custom policy service.",
                "Evidence and grounding": "Expose approved evidence through typed retrieval APIs.",
                "Identity and data boundary": "Test authorization across both platform boundaries.",
                "Extensibility": "Extend policy services without replacing the whole experience.",
                "Lifecycle governance": "Coordinate API and experience releases and checks.",
                "Operating ownership": "Needs clear ownership across both platform teams.",
                "Cost and adoption": "Estimate both platforms and integration; not measured.",
            },
        },
    ]
    return {
        "options": options,
        "assessmentBasis": (
            "Seeded qualitative scenario analysis, not a scored product evaluation. "
            "Product fit, costs, and prioritization require qualified review."
        ),
        "recommendation": {
            "label": "recommendation",
            "optionId": "OPT-C",
            "text": (
                "Advance the hybrid pattern to discovery validation, subject to the listed "
                "unknowns and human selection."
            ),
            "evidenceIds": ["EVD-003", "EVD-004"],
        },
        "selectionState": "awaiting_authorized_customer_selection",
        "evaluationCriteria": request.get("optionCriteria", []),
    }
