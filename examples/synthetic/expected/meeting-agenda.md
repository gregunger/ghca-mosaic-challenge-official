# Employee Policy Guidance: Customer Solutioning Workshop Agenda

## Use Case Context

**Use case:** Employee Policy Guidance

**Business problem:** Employees cannot reliably find current policy answers across distributed content, creating repeated service inquiries, inconsistent guidance, and slow escalation to accountable policy owners.

**Assessment scope:** Scope requires confirmation with the customer.

**Affected users:** Employees seeking policy guidance; Service desk analysts handling repeated inquiries; Policy owners accountable for authoritative interpretation

## Purpose And Meeting Outcome

This is a proposed 30-minute working agenda for the
technology SME and customer reviewers. It turns the current intake, evidence and three-option
comparison into a focused decision conversation, rather than a document walkthrough.

**Business problem:** Employees cannot reliably find current policy answers across distributed content, creating repeated service inquiries, inconsistent guidance, and slow escalation to accountable policy owners.

**Meeting objective:** Validate evidence, resolve priority unknowns, and choose the next design action.

Leave with corrected scope, an explicit next design action, prioritized evidence requests and
customer-assigned follow-up. These are proposed meeting outputs, not decisions already made.

## Participants And Preparation

Required reviewer roles: Business owner, Policy owner, Qualified solution architect, Security reviewer. The customer must identify
the people and their decision authority; this report assigns neither attendance nor approval.

Before the session:

- Review [Problem & Scope](intake-report.md) and identify corrections to users, outcomes, constraints and measures.
- Check [Evidence & Claims](evidence-appendix.md) for source support, assumptions and evidence freshness.
- Read all three [Solution Options](option-matrix.md), including their conditions and disqualifiers.
- Bring answers or source references for the priority questions below. Do not turn missing evidence into an assumed fact.
- Confirm who may select an architecture and where the customer's authoritative decision will be recorded.

## Time-Boxed Working Agenda

| Time | Topic | Facilitator focus | Working output | Pre-read |
| --- | --- | --- | --- | --- |
| 00:00-04:00 | Outcome and current-state confirmation | Confirm the problem, affected users, first-release boundary and proposed measures. | A corrected problem statement and an explicit list of scope changes. | [Problem & Scope](intake-report.md) |
| 04:00-12:00 | Evidence, gaps, and risk review | Separate source-backed statements from assumptions; identify questions that block a decision. | Priority evidence requests, unresolved risks and a decision on what must wait. | [Evidence & Claims](evidence-appendix.md) |
| 12:00-22:00 | Three-option comparison | Compare all three options against the same criteria, conditions and disqualifiers. | Customer feedback on tradeoffs and the evidence needed for an authorized selection. | [Solution Options](option-matrix.md) |
| 22:00-27:00 | Decision and evidence requests | Confirm whether an authorized architecture decision is possible or further discovery is needed. | A recorded next action and its rationale; no inferred architecture or design approval. | [Decisions & Review](human-review.md) |
| 27:00-30:00 | Owners and next steps | Agree who will obtain missing evidence, when it is due and how it will be reviewed. | Customer-assigned actions and the next review checkpoint against an exact revision. | [Design & Readiness](architecture-brief.md) |

## Outcome And Scope Confirmation

**Affected people:**

- Employees seeking policy guidance
- Service desk analysts handling repeated inquiries
- Policy owners accountable for authoritative interpretation

**Proposed outcomes to confirm:**

- Give employees evidence-linked answers from approved policy sources
- Route ambiguity and sensitive decisions to accountable humans
- Create a repeatable audit trail for evidence, risks, options, and approvals

**Measures to test with the customer:**

- At least 95 percent of factual statements cite approved evidence in the controlled benchmark
- Zero unsupported material claims released during the controlled benchmark
- Every ambiguous or policy-sensitive request is routed to a named human-owned queue
- Qualified reviewers accept or return every package against an immutable revision

Ask which outcome matters first, what falls outside the initial release, how the current baseline
will be established, and who accepts the result. Record corrections without erasing the original intake.
These measures are proposed targets, not achieved results.

## Priority Questions And Blockers

- **Q-001:** Which content owners can approve the initial source inventory and freshness SLA?
- **Q-002:** Which policy questions must always escalate without a generated answer?
- **Q-003:** Which identity claims and source permissions must be preserved end to end?
- **Q-004:** What benchmark defines a correct, useful, and safely escalated response?

| Unknown | Question to resolve | Decision impact |
| --- | --- | --- |
| UNK-001 | Who is the final production data owner? | Blocks the next decision |
| UNK-002 | What production identity and authorization model is approved? | Blocks the next decision |
| UNK-003 | What retention period applies to prompts, evidence, and review records? | Blocks the next decision |
| UNK-004 | Which model, deployment region, and acceptance thresholds are approved? | Blocks the next decision |

For each unresolved item, identify the evidence needed, a customer-named owner, an agreed due date
and the reviewer who can close it. None of those assignments or dates has been recorded here.

## Option Discussion Prompts

| Option | Fit to test | Condition to verify | Disqualifier to challenge |
| --- | --- | --- | --- |
| OPT-A: Managed low-code agent | Rapid adoption and managed lifecycle controls outweigh bespoke behavior. | Approved connector coverage; Tenant governance configured | Required behavior exceeds extension model |
| OPT-B: Custom governed application | Custom orchestration, evaluation, and integration control are primary. | Product engineering ownership; Approved model and region | No funded operations owner |
| OPT-C: Hybrid governed experience | Managed adoption and custom policy enforcement are both required. | API ownership; Identity propagation design; Joint lifecycle model | Cross-platform ownership cannot be assigned |

Use the common criteria: Outcome alignment; Evidence and grounding; Identity and data boundary; Extensibility; Lifecycle governance; Operating ownership; Cost and adoption.
Ask what evidence would change the customer's preference and what tradeoff is unacceptable.
The recorded recommendation remains conditional, not an authorized selection.

## Decision And Action Record

| Record | Current state | What to capture during the meeting |
| --- | --- | --- |
| Architecture selection | pending | Authorized decision-maker, chosen option or reason to defer, rationale and evidence revision. |
| Design-package approval | blocked_pending_selection | Separate approval only after selection and preparation of the exact completed dossier. |
| Evidence actions | Proposed; not assigned | Linked unknown/risk, requested evidence, customer-named owner, due date and closure check. |

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
