# SPDX-License-Identifier: LicenseRef-MOSAIC-Evaluation
"""Deterministic orchestration for the synthetic MOSAIC workflow."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from typing import Any

from mosaic.connectors.base import SourceConnector
from mosaic.models import StageResult, WorkflowResult
from mosaic.observability import Observer, observed_step
from mosaic.schema_validation import validate_instance
from mosaic.stages import acquire, analyze, design, discover, normalize, option, prepare, review

STAGE_NAMES = (
    "discover",
    "acquire",
    "normalize",
    "analyze",
    "option",
    "design",
    "prepare",
    "review",
)

STAGE_OBJECTIVES = {
    "discover": "problem_validation",
    "acquire": "approved_evidence_boundary",
    "normalize": "structured_intake_integrity",
    "analyze": "gap_risk_and_dependency_analysis",
    "option": "contrasting_solution_options",
    "design": "proposed_design_readiness",
    "prepare": "customer_engagement_readiness",
    "review": "qualified_human_authority",
}

METADATA_FIELDS = (
    "customerId",
    "initiativeId",
    "sourceTicketRef",
    "workflowVersion",
    "policyVersion",
    "correlationId",
)


def _metadata(request: Mapping[str, Any], control_objective: str) -> dict[str, str]:
    missing = [field for field in METADATA_FIELDS if not request.get(field)]
    if missing:
        raise ValueError(f"Request is missing workflow metadata: {', '.join(missing)}")
    timestamp = str(request.get("requestedAt", ""))
    if not timestamp.endswith("Z"):
        raise ValueError("requestedAt must be an explicit UTC timestamp ending in 'Z'.")
    return {
        **{field: str(request[field]) for field in METADATA_FIELDS},
        "controlObjective": control_objective,
        "timestamp": timestamp,
    }


def _run_id(request: Mapping[str, Any], package: Mapping[str, Any]) -> str:
    stable_inputs = json.dumps(
        {"request": request, "package": package}, sort_keys=True, separators=(",", ":")
    )
    digest = hashlib.sha256(stable_inputs.encode("utf-8")).hexdigest()[:12].upper()
    return f"RUN-{request['initiativeId']}-{digest}"


def run_workflow(
    request: Mapping[str, Any],
    connector: SourceConnector,
    *,
    customer: Mapping[str, Any] | None = None,
    on_event: Observer | None = None,
) -> WorkflowResult:
    """Run all automated stages and stop before the non-delegable release decision."""
    if customer is not None:
        validate_instance(customer, "customer-config.schema.json")
        if customer["customerId"] != request["customerId"]:
            raise ValueError("Customer configuration does not match the request customerId.")
    with observed_step(on_event, "workflow.discover"):
        discover_output = discover.execute(request)
    with observed_step(on_event, "workflow.acquire"):
        acquire_output = acquire.execute(connector)
    with observed_step(on_event, "workflow.normalize"):
        normalize_output = normalize.execute(request, acquire_output["sources"])
    with observed_step(on_event, "workflow.analyze"):
        analyze_output = analyze.execute(request)
    with observed_step(on_event, "workflow.option"):
        option_output = option.execute(request)
    with observed_step(on_event, "workflow.design"):
        design_output = design.execute(option_output, request=request)
    with observed_step(on_event, "workflow.prepare"):
        prepare_output = prepare.execute(request, analyze_output)
    with observed_step(on_event, "workflow.review"):
        review_output = review.execute(
            analyze_output,
            reviewer_roles=(
                customer["requiredReviewerRoles"] if customer else ("Qualified solution architect",)
            ),
            configuration_id=customer["configurationId"] if customer else None,
        )
    if on_event:
        on_event("governance.human_review", "blocked", {"releaseAuthorized": False})

    outputs = (
        discover_output,
        acquire_output,
        normalize_output,
        analyze_output,
        option_output,
        design_output,
        prepare_output,
        review_output,
    )
    stages = tuple(
        StageResult(
            name=stage_name,
            status="waiting_for_human" if stage_name == "review" else "completed",
            control_objective=STAGE_OBJECTIVES[stage_name],
            metadata=_metadata(request, STAGE_OBJECTIVES[stage_name]),
            output=output,
        )
        for stage_name, output in zip(STAGE_NAMES, outputs, strict=True)
    )
    package = {
        "discovery": discover_output,
        "evidenceManifest": acquire_output,
        "normalizedIntake": normalize_output,
        "analysis": analyze_output,
        "optionAnalysis": option_output,
        "proposedDesign": design_output,
        "engagementPackage": prepare_output,
        "humanReview": review_output,
    }
    return WorkflowResult(
        run_id=_run_id(request, package),
        initiative_id=str(request["initiativeId"]),
        state="awaiting_human_review",
        stages=stages,
        generated_at=str(request["requestedAt"]),
        metadata=_metadata(request, "governed_intake_to_decision"),
        package=package,
    )
