# SPDX-License-Identifier: LicenseRef-MOSAIC-Evaluation
"""Prepare a proposed architecture without claiming implementation."""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from typing import Any


def execute(
    option_output: Mapping[str, Any], *, request: Mapping[str, Any] | None = None
) -> dict[str, Any]:
    if request is not None and request.get("inputMode") == "conversation":
        draft = request.get("designDraft")
        if not isinstance(draft, Mapping):
            raise ValueError(
                "Conversational intake requires its own designDraft; no seeded fallback."
            )
        return deepcopy(dict(draft))
    recommendation = option_output["recommendation"]
    return {
        "maturity": "proposed",
        "selectedForDiscovery": recommendation["optionId"],
        "selectionStatus": "unselected_discussion_draft",
        "assessmentBasis": (
            "Prewritten discussion draft for the fictional policy assistant, not a "
            "customer-selected design. The full dossier requires authorized architecture "
            "selection first. Product fit and production controls remain unvalidated."
        ),
        "architecture": {
            "experience": "Managed employee policy assistant surface",
            "identity": "Workforce identity with user-context propagation",
            "policyBoundary": "Typed policy API and approved-source manifest",
            "knowledgeBoundary": ("Read-only retrieval over approved, access-trimmed content"),
            "audit": (
                "Versioned evidence and access records with human-owned retention and review"
            ),
        },
        "trustBoundaries": [
            "Employee identity to managed conversational experience",
            "Conversational experience to authorized policy API",
            "Policy API to permission-preserving retrieval over approved sources",
            "Ambiguous or sensitive requests to an accountable policy owner",
        ],
        "implementationStatus": "not_started",
        "requiredDecisions": [
            "Confirm production data owner",
            "Approve identity and authorization model",
            "Approve retention period, model, and deployment region",
            "Confirm measurable acceptance criteria",
        ],
        "dossierCoverage": [
            {
                "id": "DOS-001",
                "area": "Business problem and outcomes",
                "artifact": "intake-report.md",
            },
            {
                "id": "DOS-002",
                "area": "Requirements and acceptance",
                "artifact": "intake-report.md",
            },
            {
                "id": "DOS-003",
                "area": "Feasibility and risk",
                "artifact": "architecture-brief.md",
            },
            {
                "id": "DOS-004",
                "area": "Alternatives and decision",
                "artifact": "option-matrix.md",
            },
            {
                "id": "DOS-005",
                "area": "Threat model and data flow",
                "artifact": "architecture-brief.md",
            },
            {
                "id": "DOS-006",
                "area": "Implementation and verification plan",
                "artifact": "architecture-brief.md",
            },
            {
                "id": "DOS-007",
                "area": "API and integration specifications",
                "artifact": "architecture-brief.md",
            },
            {
                "id": "DOS-008",
                "area": "Security and dependency requirements",
                "artifact": "architecture-brief.md",
            },
            {
                "id": "DOS-009",
                "area": "Deployment and rollback plan",
                "artifact": "architecture-brief.md",
            },
            {
                "id": "DOS-010",
                "area": "Operations, adoption and measurement",
                "artifact": "architecture-brief.md",
            },
        ],
        "readinessPlans": [
            {
                "id": "PLAN-001",
                "title": "Feasibility And Delivery Risk",
                "label": "recommendation",
                "requirementIds": ["REQ-001", "REQ-003"],
                "evidenceIds": ["EVD-001", "EVD-004"],
                "blockingUnknownIds": ["UNK-001", "UNK-002", "UNK-004"],
                "proposal": (
                    "Before selecting an option, test whether approved sources can provide "
                    "current policy answers without losing user permissions. Compare connector "
                    "coverage, content ownership, escalation capacity, operating cost and "
                    "delivery dependencies using the same three-option criteria."
                ),
                "requiredEvidence": (
                    "Customer-owned source inventory, supported integration evidence, named "
                    "operating roles, cost inputs and delivery constraints. No feasibility "
                    "rating, budget or completion date has been validated."
                ),
            },
            {
                "id": "PLAN-002",
                "title": "Threat Model And Data Flow",
                "label": "recommendation",
                "requirementIds": ["REQ-001", "REQ-002", "REQ-003"],
                "evidenceIds": ["EVD-001", "EVD-002", "EVD-003"],
                "blockingUnknownIds": ["UNK-002", "UNK-003"],
                "proposal": (
                    "Trace employee identity through the conversational surface, policy API "
                    "and source retrieval. Assess forged identity, source prompt injection, "
                    "stale evidence and sensitive-response leakage. Treat retrieved text as "
                    "data, preserve source authorization, and escalate ambiguity to a policy "
                    "owner instead of inventing an authoritative answer."
                ),
                "requiredEvidence": (
                    "Security-reviewed identity and permission propagation, prohibited-data "
                    "tests, freshness ownership and approved retention. This is a threat "
                    "analysis starting point, not a completed security assessment."
                ),
            },
            {
                "id": "PLAN-003",
                "title": "Proposed Implementation And Verification",
                "label": "recommendation",
                "requirementIds": ["REQ-001", "REQ-002", "REQ-003", "REQ-004"],
                "evidenceIds": ["EVD-001", "EVD-002", "EVD-003", "EVD-004"],
                "blockingUnknownIds": ["UNK-002", "UNK-004"],
                "proposal": (
                    "After customer selection and a separate implementation authorization, "
                    "validate one synthetic source-to-answer path before broadening coverage. "
                    "Plan checks for permitted and denied access, missing or stale citations, "
                    "unsupported answers, ambiguity and human escalation. Tie each acceptance "
                    "check to its requirement and retain failures and corrections."
                ),
                "requiredEvidence": (
                    "Customer-approved acceptance thresholds, representative cases and "
                    "independent review. No employee-assistant code is generated here; the "
                    "proposed solution tests have not been executed."
                ),
            },
            {
                "id": "PLAN-004",
                "title": "Proposed Interfaces And Integrations",
                "label": "recommendation",
                "requirementIds": ["REQ-001", "REQ-002", "REQ-004"],
                "evidenceIds": ["EVD-001", "EVD-003", "EVD-004"],
                "blockingUnknownIds": ["UNK-001", "UNK-002"],
                "proposal": (
                    "Define requests with verified user context, a question and correlation "
                    "ID; responses with answer status, source IDs and revisions, or a "
                    "human-escalation reference. Source adapters must enforce access before "
                    "returning content. An API caller cannot assert its own permission scope."
                ),
                "requiredEvidence": (
                    "Authorized integration owners, source API contracts, identity mappings "
                    "and access tests. Endpoint selection and executable API specifications "
                    "remain pending customer architecture selection."
                ),
            },
            {
                "id": "PLAN-005",
                "title": "Security Controls And Dependency Requirements",
                "label": "recommendation",
                "requirementIds": ["REQ-002", "REQ-003", "REQ-004"],
                "evidenceIds": ["EVD-002", "EVD-003", "EVD-004"],
                "blockingUnknownIds": ["UNK-002", "UNK-003", "UNK-004"],
                "proposal": (
                    "Specify least-privileged identities, approved-source boundaries, "
                    "evidence integrity, protected review records and customer-owned "
                    "retention. For later implementation, plan a dependency inventory, "
                    "license review and software-bill-of-materials evidence before release."
                ),
                "requiredEvidence": (
                    "Selected-platform controls, customer-approved risk disposition and "
                    "actual dependency provenance. This draft is not an SBOM, certification "
                    "or proof of implemented production controls."
                ),
            },
            {
                "id": "PLAN-006",
                "title": "Proposed Deployment And Rollback",
                "label": "recommendation",
                "requirementIds": ["REQ-002", "REQ-003", "REQ-004"],
                "evidenceIds": ["EVD-002", "EVD-003", "EVD-004"],
                "blockingUnknownIds": ["UNK-002", "UNK-004"],
                "proposal": (
                    "Document separate non-production and production change decisions. "
                    "Before future rollout, require the configuration revision, access and "
                    "answer-quality acceptance, limited exposure, rollback triggers and a "
                    "change owner. A failed control should stop rollout and restore an "
                    "approved prior configuration where supported."
                ),
                "requiredEvidence": (
                    "Selected-platform promotion and rollback capabilities, approved "
                    "regions, recovery objectives and a tested recovery procedure. No "
                    "pipeline, environment, deployment or rollback is executed here."
                ),
            },
            {
                "id": "PLAN-007",
                "title": "Proposed Operations, Adoption And Measurement",
                "label": "recommendation",
                "requirementIds": ["REQ-001", "REQ-003", "REQ-004"],
                "evidenceIds": ["EVD-001", "EVD-002", "EVD-004"],
                "blockingUnknownIds": ["UNK-001", "UNK-003", "UNK-004"],
                "proposal": (
                    "Assign content freshness, service support and policy escalation in "
                    "the customer's workflow. Plan onboarding, support training and review "
                    "of failures. Compare answer coverage, unresolved inquiries, review "
                    "effort, rework and total cost against customer-provided baselines "
                    "without logging sensitive content."
                ),
                "requiredEvidence": (
                    "Named customer owners, inquiry baseline, success thresholds, adoption "
                    "plan and approved telemetry/retention. No service handover, operational "
                    "monitoring or measured outcome is claimed."
                ),
            },
        ],
    }
