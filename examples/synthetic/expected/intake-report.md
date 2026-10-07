# Employee Policy Guidance: Initial Technical Intake Assessment

## Use Case Context

**Use case:** Employee Policy Guidance

**Business problem:** Employees cannot reliably find current policy answers across distributed content, creating repeated service inquiries, inconsistent guidance, and slow escalation to accountable policy owners.

**Assessment scope:** Scope requires confirmation with the customer.

**Affected users:** Employees seeking policy guidance; Service desk analysts handling repeated inquiries; Policy owners accountable for authoritative interpretation

> **Synthetic demonstration** | Initiative `SYN-001` | State `awaiting_human_review`

## Original Request

Employees cannot reliably find current policy answers across distributed content, creating repeated service inquiries, inconsistent guidance, and slow escalation to accountable policy owners.

## Executive Summary

This assessment defines the initial business and technical context for **Employee Policy Guidance**.
It records the affected users, intended outcomes, proposed success measures, constraints,
requirements, risks and unresolved questions that must inform solution selection.

## Business Problem

Employees cannot reliably find current policy answers across distributed content, creating repeated service inquiries, inconsistent guidance, and slow escalation to accountable policy owners.


## Target Users

- Employees seeking policy guidance
- Service desk analysts handling repeated inquiries
- Policy owners accountable for authoritative interpretation

## Desired Outcomes

- Give employees evidence-linked answers from approved policy sources
- Route ambiguity and sensitive decisions to accountable humans
- Create a repeatable audit trail for evidence, risks, options, and approvals

## Success Measures

- At least 95 percent of factual statements cite approved evidence in the controlled benchmark
- Zero unsupported material claims released during the controlled benchmark
- Every ambiguous or policy-sensitive request is routed to a named human-owned queue
- Qualified reviewers accept or return every package against an immutable revision

## Requirements And Acceptance Basis

Customer-supplied measures above are proposed acceptance criteria, not measured results.

| Requirement | Text | Evidence |
| --- | --- | --- |
| REQ-001 | Answers must cite an approved policy source. | EVD-001, EVD-002 |
| REQ-002 | Restricted data must not enter the synthetic demonstration. | EVD-003 |
| REQ-003 | Architecture and release decisions require qualified human approval. | EVD-002, EVD-004 |
| REQ-004 | The workflow must preserve evidence and decision traceability. | EVD-004 |

## Constraints

- Use synthetic data and offline sources in the default demonstration
- Do not make production identity, region, retention, or model decisions
- Keep enterprise connectors read-only and optional
- Stop before customer-facing release or implementation

## Gaps

- **GAP-001:** No approved production content inventory or freshness owner is recorded.
- **GAP-002:** No baseline inquiry volume or answer-quality sample is approved.

## Risks

| Risk | Severity | Concern | Evidence basis |
| --- | --- | --- | --- |
| RSK-001 | high | Outdated source content may be presented as current guidance. | EVD-002, EVD-004 |
| RSK-002 | high | Identity propagation errors may expose content beyond a user's authorization. | EVD-002, EVD-003 |
| RSK-003 | medium | Users may treat generated guidance as an authoritative policy decision. | EVD-001, EVD-002 |

## Dependencies

- **DEP-001:** Approved source inventory and accountable content owners
- **DEP-002:** Security-approved identity and access design
- **DEP-003:** Customer-owned acceptance rubric and benchmark cases

## Assumptions

- **ASM-001:** Employees have workforce identities that can be propagated to approved sources.

## Unknowns

- **UNK-001:** Who is the final production data owner?
- **UNK-002:** What production identity and authorization model is approved?
- **UNK-003:** What retention period applies to prompts, evidence, and review records?
- **UNK-004:** Which model, deployment region, and acceptance thresholds are approved?

## Questions For Review

- **Q-001:** Which content owners can approve the initial source inventory and freshness SLA?
- **Q-002:** Which policy questions must always escalate without a generated answer?
- **Q-003:** Which identity claims and source permissions must be preserved end to end?
- **Q-004:** What benchmark defines a correct, useful, and safely escalated response?

## Discovery Worklist

- Confirm the affected people, first-release inclusions and exclusions against the original conversation.
- For each proposed success measure, establish the baseline, target, measurement method and customer acceptance owner.
- Test constraints and dependencies with the accountable customer roles; do not assume budget, timing or source access.
- Resolve blocking unknowns before carrying their assumptions into architecture selection.
- Carry reviewed corrections into the [option comparison](option-matrix.md) and retain their provenance in the [transcript](intake-transcript.md).

This is a proposed review worklist, not assigned work or evidence that discovery is complete.
