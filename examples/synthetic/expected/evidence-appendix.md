# Employee Policy Guidance: Evidence Appendix

## Use Case Context

**Use case:** Employee Policy Guidance

**Business problem:** Employees cannot reliably find current policy answers across distributed content, creating repeated service inquiries, inconsistent guidance, and slow escalation to accountable policy owners.

**Assessment scope:** Scope requires confirmation with the customer.

**Affected users:** Employees seeking policy guidance; Service desk analysts handling repeated inquiries; Policy owners accountable for authoritative interpretation

> Only allowlisted synthetic sources were acquired. Hashes bind this run to exact source content.

| ID | Title | Classification | Revision | SHA-256 |
| --- | --- | --- | --- | --- |
| EVD-001 | Synthetic employee policy assistant intake | SYNTHETIC | 1.0 | 62e02b10d1f8fc6cec12ac6069fc89bc7e2588dfbe90cc3924ba7a3434d566e5 |
| EVD-002 | Synthetic AI security standard | SYNTHETIC | 2.1 | 0421ea4a9cf5958c17ec134db78156f8d555de9a4839e892dc4b567812388db6 |
| EVD-003 | Synthetic data classification policy | SYNTHETIC | 3.0 | 7a7faa59714094c2c9502070b51e539937bd7934179200bf83e7c94d2215f602 |
| EVD-004 | Synthetic architecture and evidence standard | SYNTHETIC | 1.4 | a345a006ac9957fdc6959cb5251fc0f717bb876c11856b131ff3a5b6c145fa58 |

## Claims

| ID | Label | Statement | Evidence |
| --- | --- | --- | --- |
| CLM-001 | fact | The synthetic intake requires evidence-linked policy responses. | EVD-001 |
| CLM-002 | fact | The synthetic security standard requires human review for architecture and release decisions. | EVD-002 |
| CLM-003 | assumption | A managed conversational surface may reduce adoption friction. | N/A |
| CLM-004 | unknown | The final production identity model has not been selected. | N/A |
| CLM-005 | risk | Stale policy content could produce plausible but outdated guidance. | EVD-002, EVD-004 |

## Source Verification Worklist

| Source | Source owner | Recorded retrieval | Verification task |
| --- | --- | --- | --- |
| EVD-001 | Synthetic Business Services | 2026-09-15T16:00:00Z | Confirm revision currency, permitted scope and support for the cited statement. |
| EVD-002 | Synthetic Security Office | 2026-09-15T16:00:00Z | Confirm revision currency, permitted scope and support for the cited statement. |
| EVD-003 | Synthetic Data Governance Council | 2026-09-15T16:00:00Z | Confirm revision currency, permitted scope and support for the cited statement. |
| EVD-004 | Synthetic Architecture Review Board | 2026-09-15T16:00:00Z | Confirm revision currency, permitted scope and support for the cited statement. |

Retrieval dates and hashes describe this captured evidence set. They are not live freshness checks,
source-owner approval or proof that a claim is semantically supported.

## Requirement Evidence Trace

| Requirement | Requirement statement | Sources to inspect |
| --- | --- | --- |
| REQ-001 | Answers must cite an approved policy source. | EVD-001, EVD-002 |
| REQ-002 | Restricted data must not enter the synthetic demonstration. | EVD-003 |
| REQ-003 | Architecture and release decisions require qualified human approval. | EVD-002, EVD-004 |
| REQ-004 | The workflow must preserve evidence and decision traceability. | EVD-004 |

## Claim Review And Disposition

Read the cited passage for each material claim and test its wording and scope. Preserve the
distinction between fact, assumption, unknown, risk, recommendation and decision. A valid source ID
alone is insufficient.

Record corrections with the claim ID, original revision, supporting evidence, reviewer rationale
and resulting change to the intake, options or design. Keep unsupported statements uncertain or
reject them; never manufacture a citation or broaden source access to fill a gap.
