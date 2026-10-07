# MOSAIC Project Instructions

## Mission

MOSAIC means **Multi-customer Orchestration System for Adaptive Intake and Continuous Delivery**: a provider-neutral, AI-first business process automation and orchestration system for solution engineering. It turns a plain-language business need into a governed, evidence-grounded solution dossier and accountable human handoff. This repository is its synthetic GitHub Copilot App contest reference, not the full product boundary or an implementation/deployment authority.

Make high-quality solution engineering repeatable at customer scale. The Microsoft value proposition is reusable field expertise, less duplicated effort and rework, and a shorter path from business intent to governed technical delivery. Treat economic, quality, and cycle-time benefits as evaluation targets until measured.

The active reference turns an eligible synthetic solution initiative into an evidence-grounded, reviewable discussion draft and ends at qualified human review. Preparing proposed implementation, verification, interfaces, security, deployment/rollback, operations/adoption and measurement documentation is design scope. Executing IaC, pipelines, testing of the designed solution, operations, training, handover or deployment is an extension roadmap, not authorization. Do not implement or deploy the designed solution.

## Workflow Contract

1. Execute `Discover -> Acquire -> Normalize -> Analyze -> Option -> Design -> Prepare -> Review` in order.
2. In Plan mode, identify the data boundary, source IDs, intended outputs, tools, and stop conditions before generation.
3. Acquire only sources allowed by `examples/synthetic/source-policy.json`. Use `mosaic-synthetic-evidence` read-only MCP tools when available.
4. Label assertions as `fact`, `assumption`, `unknown`, `risk`, `recommendation`, or `decision`. Facts, recommendations, and decisions require valid evidence IDs.
5. Produce exactly three contrasting architecture options using common criteria.
6. Run the CLI and tests before declaring a pull request ready.
7. Stop at `awaiting_human_review`. Never approve policy, security, architecture, customer facts, commitments, or release.
8. Preserve two customer decisions: authorized architecture selection before the selected full dossier, then exact-revision dossier approval in the customer's workflow. A PR is review evidence, not implicit customer approval. This reference records neither decision and labels the design `unselected_discussion_draft`.
9. Keep each customer installation isolated. Customer policy may tighten, never weaken, baseline controls. Reviewer roles are policy requirements, not people assignments or evidence of consent. Do not invent adapter capabilities, live authority checks or durable resume behavior.

## Safety

- Use only `SYN-` initiative IDs, fictional organizations, `.example` endpoints, and unusable credentials.
- Do not add customer names, customer records, personal data, tenant or subscription IDs, tokens, secrets, or restricted screenshots.
- Do not claim measured savings, production deployment, implementation, or customer approval.
- Describe SOC 2, applicable NIST publications, and ITIL 4 as customer-specific alignment targets, not established compliance or certification. Do not claim universal customer fit, human-performance superiority, or superiority to Microsoft's product portfolio without comparative evidence.
- Treat optional enterprise connectors as read-only and disabled until independently authorized.
- Verify current product and cloud claims against official documentation.

## Build And Test

```powershell
python -m mosaic.cli
python -m pytest
```

Generated outputs must include the evidence manifest, three-option comparison, validation report, audit ledger, engagement package, and blocked human-review record.

## Contest Acceptance (Submission Work Only)

Treat the FY27 Q1 GitHub Copilot App Enterprise Challenge brief supplied by the owner as the submission acceptance contract. These criteria govern the contest package, not an extra questionnaire or release requirement for each business intake.

- Keep the GitHub Copilot App central to the demonstrated workflow. Supporting code, CLI workers and connected tools are implementation components, not substitutes for genuine App use. Do not claim an explicit organizer ruling on CLI eligibility without one.
- Lead with the business problem, customer/user persona, repeatable before-and-after workflow and business value. Make effort, cost, rework and cycle-time benefits prominent; label illustrative estimates, assumptions, retained human effort and incremental costs. Never present unmeasured savings as results.
- Address every rubric area with inspectable evidence: enterprise relevance and customer value (35 points); repeatability and field usability (20); governance, security, Responsible AI and human-in-the-loop design (20); demonstrated competitive positioning against Claude Code (15); storytelling and demo clarity (10); observed App product feedback (5 bonus). Full coverage is a target, not a self-awarded score or a guarantee of winning.
- Show actual GitHub integration, delegated work, connected context and human review where relevant. Separate configured, tested, demonstrated and proposed behavior. A supporting single-model call is not proof of native multi-agent collaboration; a local test is not App footage or user acceptance. Ground competitive claims in demonstrated differences.
- Required package: project summary at most 150 words; workflow-in-action video at most 3 minutes; reusable repository assets; README covering roles, prerequisites, governance, human review and success measures where applicable; 1-3 slide architecture/workflow deck with relevant App screenshots; one competitive-positioning paragraph. Include firsthand product feedback for the bonus. Explain setup, customer scenario, adoption path and field reuse. Production readiness and net-new product invention are not required.
- Preserve originality and license compatibility: identify starting material and substantial contributions. Use authentic authorized screenshots and footage. Verify judges can access the exact repository, video and deck links. No more than three team members; include all confirmed team contacts without inventing membership.
- Keep the implementation sequence: working workflow and local validation, then owner hands-on testing, then updated submission documents, deck and video after workflow acceptance. Do not refresh those presentation assets while the owner has them on hold.
- Track each requirement against current evidence and an explicit passed, pending or blocked state in the existing submission checklist. Do not declare the entry fully aligned or ready while mandatory evidence, owner review or access checks remain open. Required local tests are necessary but insufficient. Repository visibility and actual contest submission remain owner actions.
- Submission deadline: October 9, 2026 at 11:59 p.m. Pacific Time. Finish with review and access-verification time remaining; do not invent extensions or treat a draft form as submitted.
