# Employee Policy Guidance: Human Review Record

## Use Case Context

**Use case:** Employee Policy Guidance

**Business problem:** Employees cannot reliably find current policy answers across distributed content, creating repeated service inquiries, inconsistent guidance, and slow escalation to accountable policy owners.

**Assessment scope:** Scope requires confirmation with the customer.

**Affected users:** Employees seeking policy guidance; Service desk analysts handling repeated inquiries; Policy owners accountable for authoritative interpretation

> **Release blocked** | Decision `pending` | Status `waiting_for_human`

## Authority Boundary

The customer's configured workflow owns architecture selection and approval of the exact design revision. Pull-request review supports that decision; it does not replace it. Automation cannot approve policy, architecture, commitments or release.

## Required Customer Roles

- Business owner
- Policy owner
- Qualified solution architect
- Security reviewer

Policy configuration: `contoso-public-services-synthetic-1.0.0`.
Roles are policy requirements, not assignments to people or evidence of their authorization.

## Two Customer Decisions

| Gate | State | Required authoritative evidence |
| --- | --- | --- |
| Architecture selection | `pending` | Customer workflow decision, authorized role, chosen option and exact alternatives revision |
| Design-package approval | `blocked_pending_selection` | After selection: customer workflow decision against the exact completed dossier revision |

Request reference: `github://synthetic/mosaic-demo/issues/1`. This demonstration uses a fictional
reference; it does not query a live customer workflow or record either decision.

## Blocking Unknowns

- **UNK-001:** Who is the final production data owner?
- **UNK-002:** What production identity and authorization model is approved?
- **UNK-003:** What retention period applies to prompts, evidence, and review records?
- **UNK-004:** Which model, deployment region, and acceptance thresholds are approved?

## Allowed Decisions

- approve
- correct
- reject
- request_evidence

No approval has been recorded. A pull request carries proposed changes and review evidence;
it is not customer design approval unless the customer's authorized workflow explicitly
establishes that mapping. Final dossier synthesis requires architecture selection first.
This reference emits an unselected discussion draft and stops before either decision.

## Evidence Required At Each Gate

| Gate | Evidence to review | Record required |
| --- | --- | --- |
| Architecture selection | Corrected scope, option comparison, entry conditions, disqualifiers and disposition of blockers. | Authorized selection or deferral, rationale and exact alternatives revision. |
| Design-package approval | Selected full dossier, linked requirements, design/security/operating reviews and remaining exceptions. | Separate authorized approval of the exact completed dossier revision. |

## Review Worklist

| Blocking question | Issue to resolve | Plans referencing it |
| --- | --- | --- |
| UNK-001 | Who is the final production data owner? | PLAN-001; PLAN-004; PLAN-007 |
| UNK-002 | What production identity and authorization model is approved? | PLAN-001; PLAN-002; PLAN-003; PLAN-004; PLAN-005; PLAN-006 |
| UNK-003 | What retention period applies to prompts, evidence, and review records? | PLAN-002; PLAN-005; PLAN-007 |
| UNK-004 | Which model, deployment region, and acceptance thresholds are approved? | PLAN-001; PLAN-003; PLAN-005; PLAN-006; PLAN-007 |

## Review Recording Contract

Record the customer decision reference, authorized role and named reviewer, exact report/dossier
revision, evidence considered, rationale, conditions and agreed follow-up for each disposition.
No person, due date, consent or approval is inferred from this role list or from generation.
