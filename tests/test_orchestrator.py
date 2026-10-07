# SPDX-License-Identifier: LicenseRef-MOSAIC-Evaluation
"""Protect ordered stages, traceable analysis, stable identity and human decision gates."""

import json
from copy import deepcopy
from pathlib import Path

import pytest

from mosaic.connectors import SyntheticSourceConnector
from mosaic.orchestrator import STAGE_NAMES, run_workflow
from mosaic.render import render_html
from mosaic.validators import validate_workflow

EXAMPLE_DIRECTORY = Path(__file__).parents[1] / "examples" / "synthetic"


def load_json(path: Path) -> dict[str, object]:
    with path.open(encoding="utf-8") as stream:
        value = json.load(stream)
    assert isinstance(value, dict)
    return value


def test_synthetic_workflow_stops_at_human_review() -> None:
    request = load_json(EXAMPLE_DIRECTORY / "request.json")
    catalog_path = EXAMPLE_DIRECTORY / "sources" / "catalog.json"
    connector = SyntheticSourceConnector(
        load_json(catalog_path),
        load_json(EXAMPLE_DIRECTORY / "source-policy.json"),
        catalog_path.parent,
    )

    result = run_workflow(request, connector)

    assert tuple(stage.name for stage in result.stages) == STAGE_NAMES
    assert tuple(stage.status for stage in result.stages[:-1]) == ("completed",) * 7
    assert result.stages[-1].status == "waiting_for_human"
    assert result.state == "awaiting_human_review"
    assert len(result.package["optionAnalysis"]["options"]) == 3
    assert result.package["humanReview"]["releaseAuthorized"] is False
    assert validate_workflow(result)["status"] == "pass"


def synthetic_workflow():
    request = load_json(EXAMPLE_DIRECTORY / "request.json")
    catalog_path = EXAMPLE_DIRECTORY / "sources" / "catalog.json"
    connector = SyntheticSourceConnector(
        load_json(catalog_path),
        load_json(EXAMPLE_DIRECTORY / "source-policy.json"),
        catalog_path.parent,
    )
    return request, connector


def test_html_preview_adds_attribution_without_mutating_workflow() -> None:
    request, connector = synthetic_workflow()
    result = run_workflow(request, connector)
    original = deepcopy(result.to_dict())
    preview = render_html(result)
    assert "Report generated:" in preview
    assert "Submitted by:" in preview
    assert "John Doe" in preview
    assert result.to_dict() == original


def test_evidence_revision_changes_run_identity(monkeypatch: pytest.MonkeyPatch) -> None:
    request, connector = synthetic_workflow()
    original_result = run_workflow(request, connector)
    changed_evidence = deepcopy(connector.acquire())
    changed_evidence[0]["revision"] = "audit-revision"
    monkeypatch.setattr(connector, "acquire", lambda: changed_evidence)

    changed_result = run_workflow(request, connector)

    assert original_result.run_id != changed_result.run_id


@pytest.mark.parametrize("target", ["requirement", "recommendation"])
def test_material_citations_reject_unknown_evidence(target: str) -> None:
    request, connector = synthetic_workflow()
    result = run_workflow(request, connector)
    if target == "requirement":
        result.package["normalizedIntake"]["requirements"][0]["evidenceIds"] = ["EVD-999"]
    else:
        result.package["optionAnalysis"]["recommendation"]["evidenceIds"] = ["EVD-999"]

    assert validate_workflow(result)["status"] == "fail"


def test_review_distinguishes_two_pending_customer_decisions() -> None:
    request, connector = synthetic_workflow()

    result = run_workflow(request, connector)

    review = result.package["humanReview"]
    assert review["authoritySystem"] == "customer_workflow"
    assert review["pullRequestReviewIsCustomerApproval"] is False
    assert review["architectureSelection"] == {
        "decision": "pending",
        "selectedOptionId": None,
        "sourceDecisionRef": None,
    }
    assert review["designPackageApproval"] == {
        "decision": "blocked_pending_selection",
        "approvedRevision": None,
        "sourceDecisionRef": None,
    }
    assert result.package["proposedDesign"]["selectionStatus"] == "unselected_discussion_draft"
    assert validate_workflow(result)["status"] == "pass"


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("decision", "approved"),
        ("status", "approved"),
        ("authoritySystem", "pull_request"),
        ("pullRequestReviewIsCustomerApproval", True),
    ],
)
def test_review_rejects_implicit_customer_approval(field: str, value: object) -> None:
    request, connector = synthetic_workflow()
    result = run_workflow(request, connector)
    result.package["humanReview"][field] = value

    assert validate_workflow(result)["status"] == "fail"


@pytest.mark.parametrize("gate", ["architectureSelection", "designPackageApproval"])
def test_reference_rejects_recorded_customer_decision(gate: str) -> None:
    request, connector = synthetic_workflow()
    result = run_workflow(request, connector)
    result.package["humanReview"][gate]["sourceDecisionRef"] = "synthetic-review-claim"

    assert validate_workflow(result)["status"] == "fail"


@pytest.mark.parametrize(
    ("field", "invalid_id"),
    [("evidenceIds", "EVD-999"), ("requirementIds", "REQ-999"), ("blockingUnknownIds", "UNK-999")],
)
def test_readiness_plans_require_existing_references(field: str, invalid_id: str) -> None:
    request, connector = synthetic_workflow()
    result = run_workflow(request, connector)
    result.package["proposedDesign"]["readinessPlans"][0][field] = [invalid_id]

    assert validate_workflow(result)["status"] == "fail"
