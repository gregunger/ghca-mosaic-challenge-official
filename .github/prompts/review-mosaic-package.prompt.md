---
name: 'Review MOSAIC Package'
description: 'Review a generated MOSAIC package for source authorization, citation coverage, risk visibility, option quality, release safety, and the human approval boundary.'
argument-hint: 'Reference the pull request or generated output directory'
agent: 'agent'
tools: [read, search, execute]
---

Review the referenced package as a skeptical assistant to the qualified human reviewer.

1. Run the repository validation command and tests.
2. Confirm every acquired source is allowlisted, classified, revisioned, and hashed.
3. Trace each material fact and recommendation to evidence IDs.
4. Confirm the three options are meaningfully contrasting and use common criteria.
5. Check that unknowns, high risks, and required human decisions are prominent.
6. Confirm no file claims implementation, deployment, customer approval, measured savings, or release authorization.
7. Verify two distinct customer decisions: architecture selection is pending; exact-revision design approval is blocked pending selection. The design is an unselected discussion draft, not the selected full dossier. Required reviewer roles come from customer policy.
8. Return findings ordered by severity and an advisory status: `ready_for_human_review`, `correction_required`, or `evidence_required`. Never return or write an approval decision.

Your recommendation informs the human reviewer; it is not approval or risk acceptance.
Customer decisions belong in the configured customer workflow. A PR review is supporting
evidence, not customer authorization unless customer policy explicitly maps that authority.
