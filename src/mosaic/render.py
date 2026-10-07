# SPDX-License-Identifier: LicenseRef-MOSAIC-Evaluation
"""Render machine-readable and human-readable workflow artifacts."""

from __future__ import annotations

import json
from collections.abc import Iterable, Mapping
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from mosaic.models import WorkflowResult
from mosaic.observability import Observer, observed_step
from mosaic.reports import render_html_reports
from mosaic.transcript import missing_transcript, render_transcript


def _json(value: Any) -> str:
    return json.dumps(value, indent=2, sort_keys=True) + "\n"


def _bullets(items: Iterable[Any]) -> str:
    values = list(items)
    if not values:
        return "- None recorded."
    lines = []
    for item in values:
        if isinstance(item, Mapping):
            label = item.get("id") or item.get("name") or item.get("topic") or "Item"
            text = item.get("text") or item.get("statement") or item.get("description") or ""
            lines.append(f"- **{label}:** {text}".rstrip())
        else:
            lines.append(f"- {item}")
    return "\n".join(lines)


def _table(headers: list[str], rows: Iterable[Iterable[Any]]) -> str:
    def cell(value: Any) -> str:
        return (
            str(value)
            .replace("\\", "\\\\")
            .replace("|", r"\|")
            .replace("\r\n", "\n")
            .replace("\r", "\n")
            .replace("\n", " ")
        )

    header = "| " + " | ".join(headers) + " |"
    divider = "| " + " | ".join("---" for _ in headers) + " |"
    body = ["| " + " | ".join(cell(value) for value in row) + " |" for row in rows]
    return "\n".join([header, divider, *body])


def render_markdown_documents(result: WorkflowResult) -> dict[str, str]:
    package = result.package
    discovery = package["discovery"]
    evidence = package["evidenceManifest"]["sources"]
    analysis = package["analysis"]
    option_analysis = package["optionAnalysis"]
    design = package["proposedDesign"]
    engagement = package["engagementPackage"]
    review = package["humanReview"]
    current_intake = discovery.get("intakeContext")
    initiative_title = discovery["initiativeTitle"]
    intake_details = ""
    if current_intake is not None:
        intake_details = (
            "\n## Intake Decisions And Constraints\n\n"
            "User-reported statements are assumptions from this conversation, not independently "
            "approved evidence. Unanswered details remain unknown.\n\n"
            + _table(
                ["Topic", "Current information", "Basis"],
                (
                    (key.title(), value or "Unknown", "assumption" if value else "unknown")
                    for key, value in current_intake.items()
                ),
            )
            + "\n"
        )
        provenance = discovery.get("analysisProvenance")
        if provenance:
            intake_details += (
                "\n## Analysis Preparation\n\n"
                "Prepared through the opt-in Copilot CLI worker. Automated checks validate "
                "structure and references, not semantic truth. Customer selection and "
                "design approval remain unrecorded.\n\n"
                + _table(
                    ["Preparation record", "Value"],
                    (
                        (label, provenance[key])
                        for label, key in (
                            ("Model", "model"),
                            ("Input revision", "inputDigest"),
                            ("Prompt revision", "promptDigest"),
                            ("Response revision", "responseDigest"),
                        )
                    ),
                )
                + "\n"
            )

    intake = f"""# Initial Technical Intake Assessment

> **Synthetic demonstration** | Initiative `{result.initiative_id}` | State `{result.state}`

## Original Request

{discovery["businessProblem"]}

## Executive Summary

This assessment defines the initial business and technical context for **{initiative_title}**.
It records the affected users, intended outcomes, proposed success measures, constraints,
requirements, risks and unresolved questions that must inform solution selection.

## Business Problem

{discovery["businessProblem"]}
{intake_details}

## Target Users

{_bullets(discovery["targetUsers"])}

## Desired Outcomes

{_bullets(discovery["desiredOutcomes"])}

## Success Measures

{_bullets(discovery["successMeasures"])}

## Requirements And Acceptance Basis

Customer-supplied measures above are proposed acceptance criteria, not measured results.

{
        _table(
            ["Requirement", "Text", "Evidence"],
            (
                (item["id"], item["text"], ", ".join(item["evidenceIds"]))
                for item in package["normalizedIntake"]["requirements"]
            ),
        )
    }

## Constraints

{_bullets(discovery["constraints"])}

## Gaps

{_bullets(analysis["gaps"])}

## Risks

{
        _table(
            ["Risk", "Severity", "Concern", "Evidence basis"],
            (
                (item["id"], item["severity"], item["text"], ", ".join(item.get("evidenceIds", [])))
                for item in analysis["risks"]
            ),
        )
    }

## Dependencies

{_bullets(analysis["dependencies"])}

## Assumptions

{_bullets(analysis["assumptions"])}

## Unknowns

{_bullets(analysis["unknowns"])}

## Questions For Review

{_bullets(analysis["customerQuestions"])}
"""

    evidence_appendix = f"""# Evidence Appendix

> Only allowlisted synthetic sources were acquired. Hashes bind this run to exact source content.

{
        _table(
            ["ID", "Title", "Classification", "Revision", "SHA-256"],
            (
                (
                    item["id"],
                    item["title"],
                    item["classification"],
                    item["revision"],
                    item["sha256"],
                )
                for item in evidence
            ),
        )
    }

## Claims

{
        _table(
            ["ID", "Label", "Statement", "Evidence"],
            (
                (
                    claim["id"],
                    claim["label"],
                    claim["statement"],
                    ", ".join(claim.get("evidenceIds", [])) or "N/A",
                )
                for claim in package["normalizedIntake"]["claims"]
            ),
        )
    }
"""

    option_details = "\n\n".join(
        f"### {item['id']}: {item['name']}\n\n"
        f"**Strengths to validate:**\n\n{_bullets(item['strengths'])}\n\n"
        f"**Tradeoffs to discuss:**\n\n{_bullets(item['tradeoffs'])}\n\n"
        f"**Entry conditions to verify:**\n\n{_bullets(item['conditions'])}\n\n"
        f"**Disqualifiers to test:**\n\n{_bullets(item['disqualifiers'])}"
        for item in option_analysis["options"]
    )
    option_matrix = f"""# Architecture Option Matrix

> Options are proposed analysis, not an authorized customer decision.

{option_analysis["assessmentBasis"]}

{
        _table(
            ["ID", "Option", "Pattern", "Best when"],
            (
                (item["id"], item["name"], item["pattern"], item["bestWhen"])
                for item in option_analysis["options"]
            ),
        )
    }

## Common Criteria

{
        _table(
            ["Criterion", *(item["id"] for item in option_analysis["options"])],
            (
                [
                    criterion,
                    *(
                        item["criterionAssessments"].get(
                            criterion, "Not assessed; request evidence."
                        )
                        for item in option_analysis["options"]
                    ),
                ]
                for criterion in option_analysis["evaluationCriteria"]
            ),
        )
    }

## Tradeoffs And Entry Conditions

{option_details}

## Recommendation

**{option_analysis["recommendation"]["optionId"]}**: {option_analysis["recommendation"]["text"]}{
        "  "
    }
Evidence: {", ".join(option_analysis["recommendation"]["evidenceIds"])}

## Decision State

`{option_analysis["selectionState"]}`
"""

    readiness_plans = "\n\n".join(
        f"## {plan['title']}\n\n"
        f"**{plan['id']} | {plan['label']} | discussion draft**\n\n"
        f"{plan['proposal']}\n\n"
        f"**Evidence still required:** {plan['requiredEvidence']}\n\n"
        f"Requirements: {', '.join(plan['requirementIds'])} | "
        f"Evidence basis: {', '.join(plan['evidenceIds'])} | "
        f"Blocking questions: {', '.join(plan['blockingUnknownIds'])}"
        for plan in design["readinessPlans"]
    )
    diagram = (
        ""
        if current_intake is not None
        else """```mermaid
flowchart LR
    A[Employee with workforce identity] --> B[Managed conversational experience]
    B --> C[Typed policy API and authorization]
    C --> D[Permission-preserving retrieval]
    D --> E[Approved policy sources]
    E -->|Cited evidence| C
    C -->|Evidence-linked response| B
    C -->|Ambiguous or sensitive request| F[Accountable policy owner]
```"""
    )
    architecture = f"""# Proposed Architecture Brief

> Maturity: `{design["maturity"]}` | Implementation: `{design["implementationStatus"]}`

{design["assessmentBasis"]}

{diagram}

This is the proposed {
        "solution" if current_intake is not None else "employee-assistant"
    } design, not an implemented service. MOSAIC prepares
and validates this document; its own workflow is described in the repository architecture guide.

## Proposed Components

{_table(["Concern", "Proposed design"], design["architecture"].items())}

## Trust Boundaries

{_bullets(design["trustBoundaries"])}

## Required Decisions

{_bullets(design["requiredDecisions"])}

## Ten-Part Dossier Coverage

These are draft coverage areas across the existing reference files, not ten completed or
approved documents. The final dossier requires customer architecture selection first.
Each plan below is a recommendation derived from the cited synthetic requirements and
evidence, not a source fact or a tested implementation. Missing customer evidence remains explicit.

{
        _table(
            ["ID", "Documentation area", "Draft location"],
            (
                (item["id"], item["area"], f"[{item['artifact']}]({item['artifact']})")
                for item in design["dossierCoverage"]
            ),
        )
    }

{readiness_plans}
"""

    agenda = engagement["meeting"]["agenda"]
    meeting_request = f"""# Meeting Request

**Subject:** Decision workshop for {result.initiative_id}{"" if current_intake is not None else " synthetic policy assistant"}

**Business problem:** {discovery["businessProblem"]}

**Duration:** {engagement["meeting"]["durationMinutes"]} minutes

**Objective:** {engagement["meeting"]["objective"]}

Please review the evidence appendix, option matrix, and blocking unknowns before the session. No production decision or customer commitment is requested outside the qualified review process.
"""
    agenda_focus = [
        (
            "Confirm the problem, affected users, first-release boundary and proposed measures.",
            "A corrected problem statement and an explicit list of scope changes.",
            "[Problem & Scope](intake-report.md)",
        ),
        (
            "Separate source-backed statements from assumptions; identify questions that block a decision.",
            "Priority evidence requests, unresolved risks and a decision on what must wait.",
            "[Evidence & Claims](evidence-appendix.md)",
        ),
        (
            "Compare all three options against the same criteria, conditions and disqualifiers.",
            "Customer feedback on tradeoffs and the evidence needed for an authorized selection.",
            "[Solution Options](option-matrix.md)",
        ),
        (
            "Confirm whether an authorized architecture decision is possible or further discovery is needed.",
            "A recorded next action and its rationale; no inferred architecture or design approval.",
            "[Decisions & Review](human-review.md)",
        ),
        (
            "Agree who will obtain missing evidence, when it is due and how it will be reviewed.",
            "Customer-assigned actions and the next review checkpoint against an exact revision.",
            "[Design & Readiness](architecture-brief.md)",
        ),
    ]
    elapsed = 0
    agenda_rows = []
    for item, (focus, output, pre_read) in zip(agenda, agenda_focus, strict=True):
        end = elapsed + item["minutes"]
        agenda_rows.append((f"{elapsed:02}:00-{end:02}:00", item["topic"], focus, output, pre_read))
        elapsed = end
    meeting_agenda = f"""# Customer Solutioning Workshop Agenda

## Purpose And Meeting Outcome

This is a proposed {engagement["meeting"]["durationMinutes"]}-minute working agenda for the
technology SME and customer reviewers. It turns the current intake, evidence and three-option
comparison into a focused decision conversation, rather than a document walkthrough.

**Business problem:** {discovery["businessProblem"]}

**Meeting objective:** {engagement["meeting"]["objective"]}

Leave with corrected scope, an explicit next design action, prioritized evidence requests and
customer-assigned follow-up. These are proposed meeting outputs, not decisions already made.

## Participants And Preparation

Required reviewer roles: {", ".join(review["requiredReviewerRoles"])}. The customer must identify
the people and their decision authority; this report assigns neither attendance nor approval.

Before the session:

- Review [Problem & Scope](intake-report.md) and identify corrections to users, outcomes, constraints and measures.
- Check [Evidence & Claims](evidence-appendix.md) for source support, assumptions and evidence freshness.
- Read all three [Solution Options](option-matrix.md), including their conditions and disqualifiers.
- Bring answers or source references for the priority questions below. Do not turn missing evidence into an assumed fact.
- Confirm who may select an architecture and where the customer's authoritative decision will be recorded.

## Time-Boxed Working Agenda

{_table(["Time", "Topic", "Facilitator focus", "Working output", "Pre-read"], agenda_rows)}

## Outcome And Scope Confirmation

**Affected people:**

{_bullets(discovery["targetUsers"])}

**Proposed outcomes to confirm:**

{_bullets(discovery["desiredOutcomes"])}

**Measures to test with the customer:**

{_bullets(discovery["successMeasures"])}

Ask which outcome matters first, what falls outside the initial release, how the current baseline
will be established, and who accepts the result. Record corrections without erasing the original intake.
These measures are proposed targets, not achieved results.

## Priority Questions And Blockers

{_bullets(engagement["priorityQuestions"])}

{
        _table(
            ["Unknown", "Question to resolve", "Decision impact"],
            (
                (
                    item["id"],
                    item["text"],
                    "Blocks the next decision" if item.get("blocking") else "Needs clarification",
                )
                for item in analysis["unknowns"]
            ),
        )
    }

For each unresolved item, identify the evidence needed, a customer-named owner, an agreed due date
and the reviewer who can close it. None of those assignments or dates has been recorded here.

## Option Discussion Prompts

{
        _table(
            ["Option", "Fit to test", "Condition to verify", "Disqualifier to challenge"],
            (
                (
                    f"{item['id']}: {item['name']}",
                    item["bestWhen"],
                    "; ".join(item["conditions"]),
                    "; ".join(item["disqualifiers"]),
                )
                for item in option_analysis["options"]
            ),
        )
    }

Use the common criteria: {"; ".join(option_analysis["evaluationCriteria"])}.
Ask what evidence would change the customer's preference and what tradeoff is unacceptable.
The recorded recommendation remains conditional, not an authorized selection.

## Decision And Action Record

{
        _table(
            ["Record", "Current state", "What to capture during the meeting"],
            [
                (
                    "Architecture selection",
                    review["architectureSelection"]["decision"],
                    "Authorized decision-maker, chosen option or reason to defer, rationale and evidence revision.",
                ),
                (
                    "Design-package approval",
                    review["designPackageApproval"]["decision"],
                    "Separate approval only after selection and preparation of the exact completed dossier.",
                ),
                (
                    "Evidence actions",
                    "Proposed; not assigned",
                    "Linked unknown/risk, requested evidence, customer-named owner, due date and closure check.",
                ),
            ],
        )
    }

Record decisions in the customer's authoritative workflow and refer to this exact report revision.
Meeting attendance, a preferred option or a repository review does not itself establish approval.

## Meeting Exit Criteria

- Confirm the business problem, scope corrections and proposed measures with the accountable owner.
- Record which questions are resolved, still open or blocking, with their evidence references.
- Capture the actual next action: further discovery, an authorized architecture decision, or deferral.
- Read back customer-assigned evidence actions, due dates and the next review checkpoint.
- Keep architecture selection and exact-revision design approval distinct; no implementation is authorized.

## Follow-Up And Next Gate

Update the intake and evidence record with reviewed corrections, then revisit the option comparison
where new evidence changes its conditions. Prepare a selected full dossier only after authorized
architecture selection. Bring that exact dossier revision back for the separate design-approval gate.
See [Design & Readiness](architecture-brief.md) for the proposed plans and [Decisions & Review](human-review.md)
for the current blocked authority state.
"""
    talk_track = f"""# 30-Minute Talk Track

## 0:00-4:00 - Confirm the outcome

Restate the synthetic business problem, affected users, desired outcomes, and customer-owned measures. Ask the owner to correct any framing before option discussion.

## 4:00-12:00 - Test the evidence

Review the allowlisted evidence manifest, then distinguish facts from assumptions, unknowns, and risks. Resolve or assign the priority questions below.

{_bullets(engagement["priorityQuestions"])}

## 12:00-22:00 - Compare three options

Compare {", ".join(item["name"] for item in option_analysis["options"])} using the same criteria. The recommendation is analysis, not a decision.

## 22:00-27:00 - Record decisions and evidence requests

Ask the authorized owner to select a next action, identify missing evidence, and name accountable owners in the authoritative workflow.

## 27:00-30:00 - Confirm next steps

Read back owners, evidence requests, due dates, and the exact repository revision subject to review.
"""
    human_review = f"""# Human Review Record

> **Release blocked** | Decision `{review["decision"]}` | Status `{review["status"]}`

## Authority Boundary

{review["authorityStatement"]}

## Required Customer Roles

{_bullets(review["requiredReviewerRoles"])}

Policy configuration: `{review["policyConfigurationId"] or "unconfigured-reference"}`.
Roles are policy requirements, not assignments to people or evidence of their authorization.

## Two Customer Decisions

| Gate | State | Required authoritative evidence |
| --- | --- | --- |
| Architecture selection | `{review["architectureSelection"]["decision"]}` | Customer workflow decision, authorized role, chosen option and exact alternatives revision |
| Design-package approval | `{review["designPackageApproval"]["decision"]}` | After selection: customer workflow decision against the exact completed dossier revision |

Request reference: `{result.metadata["sourceTicketRef"]}`. This demonstration uses a fictional
reference; it does not query a live customer workflow or record either decision.

## Blocking Unknowns

{_bullets(item for item in analysis["unknowns"] if item["id"] in review["blockingUnknownIds"])}

## Allowed Decisions

{_bullets(review["allowedDecisions"])}

No approval has been recorded. A pull request carries proposed changes and review evidence;
it is not customer design approval unless the customer's authorized workflow explicitly
establishes that mapping. Final dossier synthesis requires architecture selection first.
This reference emits an unselected discussion draft and stops before either decision.
"""

    blocking_questions = [
        item for item in analysis["unknowns"] if item["id"] in review["blockingUnknownIds"]
    ]
    review_worklist = _table(
        ["Blocking question", "Issue to resolve", "Plans referencing it"],
        (
            (
                item["id"],
                item["text"],
                "; ".join(
                    plan["id"]
                    for plan in design["readinessPlans"]
                    if item["id"] in plan["blockingUnknownIds"]
                )
                or "Package-level blocker; no plan reference recorded.",
            )
            for item in blocking_questions
        ),
    )
    intake += """
## Discovery Worklist

- Confirm the affected people, first-release inclusions and exclusions against the original conversation.
- For each proposed success measure, establish the baseline, target, measurement method and customer acceptance owner.
- Test constraints and dependencies with the accountable customer roles; do not assume budget, timing or source access.
- Resolve blocking unknowns before carrying their assumptions into architecture selection.
- Carry reviewed corrections into the [option comparison](option-matrix.md) and retain their provenance in the [transcript](intake-transcript.md).

This is a proposed review worklist, not assigned work or evidence that discovery is complete.
"""
    evidence_appendix += f"""
## Source Verification Worklist

{
        _table(
            ["Source", "Source owner", "Recorded retrieval", "Verification task"],
            (
                (
                    item["id"],
                    item["owner"],
                    item["retrievedAt"],
                    "Confirm revision currency, permitted scope and support for the cited statement.",
                )
                for item in evidence
            ),
        )
    }

Retrieval dates and hashes describe this captured evidence set. They are not live freshness checks,
source-owner approval or proof that a claim is semantically supported.

## Requirement Evidence Trace

{
        _table(
            ["Requirement", "Requirement statement", "Sources to inspect"],
            (
                (item["id"], item["text"], ", ".join(item["evidenceIds"]))
                for item in package["normalizedIntake"]["requirements"]
            ),
        )
    }

## Claim Review And Disposition

Read the cited passage for each material claim and test its wording and scope. Preserve the
distinction between fact, assumption, unknown, risk, recommendation and decision. A valid source ID
alone is insufficient.

Record corrections with the claim ID, original revision, supporting evidence, reviewer rationale
and resulting change to the intake, options or design. Keep unsupported statements uncertain or
reject them; never manufacture a citation or broaden source access to fill a gap.
"""
    option_matrix += f"""
## Selection Readiness

{review_worklist}

Verify each option's entry conditions and challenge its disqualifiers. Cost, effort and product-fit
statements remain qualitative unless the evidence supplies a validated estimate. No numerical
ranking or weighted score is established here. Resolve blocking questions before selection.

## Architecture Decision Record

Record the selected option or explicit deferral, alternatives considered, business rationale,
tradeoffs accepted, outstanding conditions, authorized decision-maker, supporting evidence and
exact comparison revision in the customer's workflow.

An informal preference is not selection. Only an authorized selection permits the selected full
dossier to proceed; its exact-revision approval remains a later decision.
"""
    architecture += f"""
## Requirement To Plan Trace

{
        _table(
            ["Requirement", "Proposed plan coverage", "Review question"],
            (
                (
                    item["id"],
                    "; ".join(
                        f"{plan['id']}: {plan['title']}"
                        for plan in design["readinessPlans"]
                        if item["id"] in plan["requirementIds"]
                    )
                    or "No plan reference recorded",
                    "Does the proposed coverage define sufficient design, evidence and verification work?",
                )
                for item in package["normalizedIntake"]["requirements"]
            ),
        )
    }

## Design Review Worklist

- Review responsibilities and trust boundaries with the customer system, data and security owners.
- For each plan, confirm the linked requirement, proposed approach, required evidence and blocking questions.
- Define how interfaces, authorization, failure handling and acceptance behavior will be verified after separate implementation authorization.
- Challenge dependency assumptions, operating ownership, rollback, adoption and measurement before treating the package as delivery-ready.
- After architecture selection, complete the selected dossier and obtain approval of its exact revision. This draft does not authorize building or deployment.
"""
    meeting_request += f"""
## Participant Responsibilities

Required reviewer roles: {", ".join(review["requiredReviewerRoles"])}.
Ask the customer to identify the named participants, their authority and any additional business,
data, integration or operating owners needed for this problem. These roles are requirements, not
confirmed attendees or delegated authority.

## Pre-Read And Evidence To Bring

{
        _table(
            ["Pre-read", "Preparation task", "Expected contribution"],
            [
                (
                    "[Problem & Scope](intake-report.md)",
                    "Check the problem, users, constraints and measures.",
                    "Corrections, first-release boundaries and baseline evidence.",
                ),
                (
                    "[Evidence & Claims](evidence-appendix.md)",
                    "Read source support and challenge assumptions.",
                    "Authorized source references and ownership questions.",
                ),
                (
                    "[Solution Options](option-matrix.md)",
                    "Compare the same criteria for all three options.",
                    "Conditions to validate, unacceptable tradeoffs and selection questions.",
                ),
                (
                    "[Decisions & Review](human-review.md)",
                    "Check blockers and required authority.",
                    "The correct decision-makers and missing evidence.",
                ),
            ],
        )
    }

Priority customer questions:

{_bullets(engagement["priorityQuestions"])}

## Decision Request And Boundaries

Confirm scope, challenge option fit and determine the next authorized design action.
Architecture selection is `{review["architectureSelection"]["decision"]}`;
design-package approval is `{review["designPackageApproval"]["decision"]}`.
Defer when evidence or authority is missing. The invitation and meeting authorize no implementation,
purchase, release or delivery commitment.

## Logistics And Follow-Up

The sender must confirm the date, time zone, channel, named attendees and pre-read revision before
sending. Those logistics are not supplied here and no invitation has been sent.
Use the [working agenda](meeting-agenda.md) and [facilitator notes](talk-track.md).
After the session, capture only actual decisions, corrections and agreed actions.
"""
    talk_track += f"""
## Facilitation Preparation

These are proposed prompts, not a meeting transcript or scripted customer replies. Keep the current
[agenda](meeting-agenda.md), [option comparison](option-matrix.md) and [decision record](human-review.md)
available. Confirm who can make which decisions before asking for one.

**Problem to reflect back:** {discovery["businessProblem"]}

**Measures to challenge:**

{_bullets(discovery["successMeasures"])}

Ask which outcome matters first, what falls outside the initial release, what baseline evidence
exists and who accepts the result. Capture corrections instead of presuming agreement.

## Option Discussion Prompts

{
        _table(
            ["Option", "Fit to test aloud", "Challenge before proceeding"],
            (
                (item["name"], item["bestWhen"], "; ".join(item["disqualifiers"]))
                for item in option_analysis["options"]
            ),
        )
    }

Ask: "Which condition have we not demonstrated? Which tradeoff is unacceptable? What evidence would
change your preference?" Compare the same criteria for all three options. Do not turn qualitative
conditions into a score or interpret a preference as an authorized decision.

## Handling Uncertainty And Disagreement

- For a disputed fact, identify the source and reviewer needed; retain uncertainty until reviewed.
- For competing priorities, ask the business owner to clarify outcome importance and acceptable tradeoffs.
- For unclear risk acceptance or authority, pause that decision and route it to the qualified customer role.
- When time expires, record the unresolved question and agreed follow-up rather than implying consensus.

## Close-Out Readback

Read back corrected scope, the actual decision or deferral, supporting rationale, linked evidence
requests, customer-named owners, agreed dates and next checkpoint. Ask participants to correct
the record, and record only their actual responses. Keep architecture selection, dossier approval
and any later implementation or release authority separate.
"""
    human_review += f"""
## Evidence Required At Each Gate

{
        _table(
            ["Gate", "Evidence to review", "Record required"],
            [
                (
                    "Architecture selection",
                    "Corrected scope, option comparison, entry conditions, disqualifiers and disposition of blockers.",
                    "Authorized selection or deferral, rationale and exact alternatives revision.",
                ),
                (
                    "Design-package approval",
                    "Selected full dossier, linked requirements, design/security/operating reviews and remaining exceptions.",
                    "Separate authorized approval of the exact completed dossier revision.",
                ),
            ],
        )
    }

## Review Worklist

{review_worklist}

## Review Recording Contract

Record the customer decision reference, authorized role and named reviewer, exact report/dossier
revision, evidence considered, rationale, conditions and agreed follow-up for each disposition.
No person, due date, consent or approval is inferred from this role list or from generation.
"""

    documents = {
        "intake-report.md": intake,
        "intake-transcript.md": render_transcript(
            discovery.get("intakeTranscript", missing_transcript(result.initiative_id)),
            discovery["submittedBy"]["displayName"],
        ),
        "evidence-appendix.md": evidence_appendix,
        "option-matrix.md": option_matrix,
        "architecture-brief.md": architecture,
        "meeting-request.md": meeting_request,
        "meeting-agenda.md": meeting_agenda,
        "talk-track.md": talk_track,
        "human-review.md": human_review,
    }
    for filename, document in documents.items():
        title, _, body = document.partition("\n")
        report_name = title.removeprefix("# ").strip()
        scope = (
            current_intake.get("scope")
            if current_intake
            else "Scope requires confirmation with the customer."
        )
        context = (
            "\n\n## Use Case Context\n\n"
            f"**Use case:** {initiative_title}\n\n"
            f"**Business problem:** {discovery['businessProblem']}\n\n"
            f"**Assessment scope:** {scope or 'Scope requires confirmation with the customer.'}\n\n"
            f"**Affected users:** {'; '.join(discovery['targetUsers'])}\n"
        )
        documents[filename] = f"# {initiative_title}: {report_name}" + context + body
    return documents


def _with_report_metadata(result: WorkflowResult) -> WorkflowResult:
    """Attach render time without changing deterministic identity or the original result."""
    return replace(
        result,
        package={
            **result.package,
            "reportMetadata": {
                "generatedAt": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
                "preparedBy": "MOSAIC",
            },
        },
    )


def render_html(result: WorkflowResult) -> str:
    report_result = _with_report_metadata(result)
    return render_html_reports(report_result, render_markdown_documents(report_result))[
        "index.html"
    ]


def write_run(
    result: WorkflowResult,
    validation_report: Mapping[str, Any],
    output_directory: Path,
    *,
    required_artifacts: Iterable[str] = (),
    on_event: Observer | None = None,
) -> list[Path]:
    with observed_step(on_event, "report.prepare_content"):
        result = _with_report_metadata(result)
        markdown_documents = render_markdown_documents(result)
    with observed_step(on_event, "report.render_html"):
        html_documents = render_html_reports(result, markdown_documents)
    files: dict[str, str] = {
        "package.json": _json(result.to_dict()),
        "intake-transcript.json": _json(
            result.package["discovery"].get(
                "intakeTranscript",
                missing_transcript(result.initiative_id),
            )
        ),
        "validation-report.json": _json(validation_report),
        "audit-ledger.json": _json(
            {
                "schemaVersion": "1.0.0",
                "runId": result.run_id,
                "events": [
                    {
                        **stage.metadata,
                        "stage": stage.name,
                        "status": stage.status,
                    }
                    for stage in result.stages
                ],
            }
        ),
        **html_documents,
        **markdown_documents,
    }
    unsupported = set(required_artifacts) - files.keys()
    if unsupported:
        raise ValueError(
            "Customer document requirements are unsupported by this reference: "
            + ", ".join(sorted(unsupported))
        )
    written: list[Path] = []
    with observed_step(on_event, "report.write_files"):
        output_directory.mkdir(parents=True, exist_ok=True)
        for name, content in files.items():
            path = output_directory / name
            path.write_text(content, encoding="utf-8", newline="\n")
            written.append(path)
            if on_event:
                on_event(
                    "report.artifact",
                    "completed",
                    {"file": name, "bytes": len(content.encode("utf-8"))},
                )
    return written
