# SPDX-License-Identifier: LicenseRef-MOSAIC-Evaluation
"""Represent the non-delegable human review boundary."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any


def execute(
    analysis: Mapping[str, Any],
    *,
    reviewer_roles: Sequence[str] = ("Qualified solution architect",),
    configuration_id: str | None = None,
) -> dict[str, Any]:
    if not reviewer_roles or any(not role.strip() for role in reviewer_roles):
        raise ValueError("At least one nonempty customer reviewer role is required.")
    blockers = [item["id"] for item in analysis.get("unknowns", []) if item.get("blocking")]
    return {
        "decision": "pending",
        "status": "waiting_for_human",
        "policyConfigurationId": configuration_id,
        "requiredReviewerRoles": list(reviewer_roles),
        "authoritySystem": "customer_workflow",
        "pullRequestReviewIsCustomerApproval": False,
        "architectureSelection": {
            "decision": "pending",
            "selectedOptionId": None,
            "sourceDecisionRef": None,
        },
        "designPackageApproval": {
            "decision": "blocked_pending_selection",
            "approvedRevision": None,
            "sourceDecisionRef": None,
        },
        "requiredReviewerRole": "; ".join(reviewer_roles),
        "blockingUnknownIds": blockers,
        "allowedDecisions": ["approve", "correct", "reject", "request_evidence"],
        "releaseAuthorized": False,
        "authorityStatement": (
            "The customer's configured workflow owns architecture selection and approval of "
            "the exact design revision. Pull-request review supports that decision; it does "
            "not replace it. Automation cannot approve policy, architecture, commitments "
            "or release."
        ),
    }
