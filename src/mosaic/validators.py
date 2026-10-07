# SPDX-License-Identifier: LicenseRef-MOSAIC-Evaluation
"""Fail-closed checks for workflow structure, traceability, and human authority."""

from __future__ import annotations

from typing import Any

from mosaic.models import WorkflowResult
from mosaic.orchestrator import METADATA_FIELDS, STAGE_NAMES

ALLOWED_CLAIM_LABELS = {"fact", "assumption", "unknown", "risk", "recommendation", "decision"}


def validate_workflow(result: WorkflowResult) -> dict[str, Any]:
    checks: list[dict[str, str]] = []
    errors: list[str] = []

    def check(name: str, condition: bool, failure: str) -> None:
        checks.append({"name": name, "status": "pass" if condition else "fail"})
        if not condition:
            errors.append(failure)

    stage_names = tuple(stage.name for stage in result.stages)
    check("eight_stages_in_order", stage_names == STAGE_NAMES, "Eight stages are not in order.")
    check(
        "seven_automated_stages_complete",
        all(stage.status == "completed" for stage in result.stages[:-1]),
        "One or more automated stages did not complete.",
    )
    check(
        "human_review_waiting",
        result.stages[-1].status == "waiting_for_human" and result.state == "awaiting_human_review",
        "Workflow did not stop at human review.",
    )
    check(
        "release_not_self_authorized",
        result.package["humanReview"].get("releaseAuthorized") is False,
        "Automation self-authorized release.",
    )
    review = result.package["humanReview"]
    check(
        "customer_authority_preserved",
        review.get("decision") == "pending"
        and review.get("status") == "waiting_for_human"
        and review.get("authoritySystem") == "customer_workflow"
        and review.get("pullRequestReviewIsCustomerApproval") is False,
        "Customer decisions must remain pending in the authoritative customer workflow.",
    )
    check(
        "architecture_selection_not_recorded",
        result.package["optionAnalysis"].get("selectionState")
        == "awaiting_authorized_customer_selection"
        and review.get("architectureSelection")
        == {"decision": "pending", "selectedOptionId": None, "sourceDecisionRef": None},
        "The reference must not record or imply customer architecture selection.",
    )
    check(
        "design_approval_blocked_pending_selection",
        review.get("designPackageApproval")
        == {
            "decision": "blocked_pending_selection",
            "approvedRevision": None,
            "sourceDecisionRef": None,
        },
        "Exact-revision design approval must remain blocked pending customer selection.",
    )
    proposed_design = result.package["proposedDesign"]
    check(
        "design_is_unselected_discussion_draft",
        proposed_design.get("selectionStatus") == "unselected_discussion_draft"
        and proposed_design.get("maturity") == "proposed"
        and proposed_design.get("implementationStatus") == "not_started",
        "The generated design must remain an unselected, unimplemented discussion draft.",
    )

    options = result.package["optionAnalysis"].get("options", [])
    check("exactly_three_options", len(options) == 3, "Exactly three options are required.")
    option_ids = {item.get("id") for item in options}
    check(
        "option_ids_unique",
        len(option_ids) == 3 and all(isinstance(value, str) and value for value in option_ids),
        "Architecture option IDs must be present and unique.",
    )
    criteria = result.package["optionAnalysis"].get("evaluationCriteria", [])
    check(
        "options_use_common_criteria",
        bool(criteria)
        and len(set(criteria)) == len(criteria)
        and all(set(item.get("criterionAssessments", {})) == set(criteria) for item in options),
        "Every option must assess the same non-empty, unique evaluation criteria.",
    )
    recommended_id = result.package["optionAnalysis"].get("recommendation", {}).get("optionId")
    check(
        "recommendation_matches_discussion_design",
        recommended_id in option_ids
        and proposed_design.get("selectedForDiscovery") == recommended_id,
        "The recommendation and unselected discussion design must reference an existing option.",
    )

    evidence = result.package["evidenceManifest"].get("sources", [])
    evidence_ids = {item.get("id") for item in evidence}
    check(
        "evidence_ids_unique",
        len(evidence_ids) == len(evidence) and None not in evidence_ids,
        "Evidence IDs must be present and unique.",
    )
    check(
        "evidence_hashed",
        all(len(str(item.get("sha256", ""))) == 64 for item in evidence),
        "Every evidence source must have a SHA-256 hash.",
    )

    claims = [
        *result.package["normalizedIntake"].get("claims", []),
        result.package["optionAnalysis"].get("recommendation", {}),
        *proposed_design.get("readinessPlans", []),
    ]
    labels_valid = all(claim.get("label") in ALLOWED_CLAIM_LABELS for claim in claims)
    check("claim_labels_valid", labels_valid, "A claim has an invalid or missing label.")
    cited_claims_valid = True
    for claim in claims:
        cited_ids = set(claim.get("evidenceIds", []))
        if claim.get("label") in {"fact", "recommendation", "decision"} and not cited_ids:
            cited_claims_valid = False
        if not cited_ids.issubset(evidence_ids):
            cited_claims_valid = False
    for requirement in result.package["normalizedIntake"].get("requirements", []):
        cited_ids = set(requirement.get("evidenceIds", []))
        if not cited_ids or not cited_ids.issubset(evidence_ids):
            cited_claims_valid = False
    check(
        "material_claims_traceable",
        cited_claims_valid,
        "A material claim, requirement, or recommendation is missing valid evidence citations.",
    )
    plans = proposed_design.get("readinessPlans", [])
    requirement_ids = {
        item["id"] for item in result.package["normalizedIntake"].get("requirements", [])
    }
    unknown_ids = {item["id"] for item in result.package["analysis"].get("unknowns", [])}
    check(
        "readiness_plans_traceable",
        len(plans) == 7
        and len({plan.get("id") for plan in plans}) == 7
        and all(
            plan.get("label") == "recommendation"
            and bool(plan.get("proposal"))
            and bool(plan.get("requiredEvidence"))
            and bool(plan.get("requirementIds"))
            and set(plan["requirementIds"]).issubset(requirement_ids)
            and bool(plan.get("blockingUnknownIds"))
            and set(plan["blockingUnknownIds"]).issubset(unknown_ids)
            for plan in plans
        ),
        "Draft readiness plans require valid requirements, evidence and blocking questions.",
    )
    coverage = proposed_design.get("dossierCoverage", [])
    check(
        "ten_dossier_areas_visible",
        len(coverage) == 10
        and {item.get("id") for item in coverage}
        == {f"DOS-{number:03d}" for number in range(1, 11)},
        "All ten dossier areas must have explicit draft coverage.",
    )

    required_metadata = {*METADATA_FIELDS, "controlObjective", "timestamp"}
    metadata_valid = required_metadata.issubset(result.metadata) and all(
        required_metadata.issubset(stage.metadata) for stage in result.stages
    )
    check(
        "machine_payload_metadata_complete",
        metadata_valid,
        "Machine-consumed payload metadata is incomplete.",
    )

    return {
        "schemaVersion": "1.0.0",
        "runId": result.run_id,
        "initiativeId": result.initiative_id,
        "generatedAt": result.generated_at,
        "status": "pass" if not errors else "fail",
        "checks": checks,
        "errors": errors,
    }


def require_valid(result: WorkflowResult) -> dict[str, Any]:
    report = validate_workflow(result)
    if report["status"] != "pass":
        raise ValueError("Workflow validation failed: " + "; ".join(report["errors"]))
    return report
