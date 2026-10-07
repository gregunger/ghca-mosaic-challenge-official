# Governance, Security, And Responsible AI

## Governing Principle

Automate the repeatable solution-engineering process; retain accountable judgment. MOSAIC is AI-first business process automation spanning adaptive intake, evidence collection, normalization, analysis, option drafting, proposed design, delivery-readiness planning, document generation, audit records and deterministic checks. It does not delegate source authorization, customer facts, policy exceptions, risk acceptance, architecture selection, customer commitments, acceptance, implementation authority, deployment authority, or release.

This document combines local controls with proposed production practices. The generator accepts the explicit prewritten reference, prepared conversational analysis, or an approved current brief analyzed through the bounded Copilot CLI adapter. All paths end with a blocked review record. Default generation is synchronous, with no model tools or automatic paid retries. Hosted customer review, enterprise requester identity, production telemetry/retention and GitHub branch protection are not implemented by the CLI. Prompt instructions are guidance, not a substitute for runtime enforcement.

## Visible Control Gates

### 1. Source Gate

- explicit source-policy ID and recorded policy version; Git review separately controls changes
- allowlisted evidence IDs and classifications
- approved flag, owner, revision, retrieval time, contained path, and SHA-256
- read-only local MCP tools with no arbitrary path or network access
- fail-closed handling for missing, unapproved, misclassified, or extra sources

### 2. Claim Gate

- six labels: fact, assumption, unknown, risk, recommendation, decision
- facts, recommendations, and decisions require valid evidence IDs
- assumptions and unknowns remain visibly unverified
- citation validation checks ID presence and membership for material claims, requirements, the option recommendation and seven draft readiness plans; plans also resolve their requirement and blocking-question references. It does not establish semantic entailment or verify every free-text statement
- generated design maturity remains `proposed`
- design selection remains `unselected_discussion_draft`; ten-area coverage is not a completed selected dossier
- implementation status remains `not_started`

### 3. Quality Gate

- request, customer configuration, evidence manifest, and package schemas
- exact eight-stage order and exactly three uniquely identified options assessed against common criteria; the conditional recommendation and discussion design must reference the same existing option
- machine payload metadata and audit events
- twenty-three artifacts (ten HTML, nine Markdown, four JSON), including the intake transcript, and a 30-minute agenda; unsupported customer-required documents fail before output is written
- shared offline HTML templates, escaped untrusted text, inactive images/external Markdown links and protected script/style/SVG handling
- unique nonempty customer reviewer roles are applied to the package, Markdown and HTML; role policy changes affect run identity
- secret, identifier, link, content, and placeholder scans
- scans are heuristic; images, recordings, hidden account details, and all possible secrets still require qualified inspection

### 4. Human Authority Gate

- release state is false after all automated checks pass
- blocking unknowns are named in the review record
- declared human dispositions are `approve`, `correct`, `reject`, and `request_evidence`; the CLI never sets an approval
- two customer decisions remain unrecorded: architecture selection, then approval of the exact selected dossier revision
- the customer workflow owns these decisions; PR review supports them but is not implicit customer approval
- the selected full dossier requires prior authorized architecture selection; the reference emits only a discussion draft
- schema and runtime checks reject fabricated selection, approval and PR-based authority; agent review returns advisory findings, never approval
- retain conversational input snapshots and completed report revisions in ignored local job storage, never public Git; submit a new job for revisions. The reference CLI can overwrite its output directory and is not an append-only audit service

### 5. Local Job Gate

- one customer identity per local store; in-repository job roots must stay under ignored build storage
- exact input/source snapshots and engine digests checked before generation; source policy may tighten, not weaken, baseline restrictions
- completed reports published by atomic rename and identified by a manifest of artifact hashes; browser opening and optional notifications verify that exact revision
- failed or canceled work does not expose a partial report; eligible local recovery creates a new job from verified retained input or an integrity-bound response that passes the corrected contract, not an invented durable resume
- recognized temporary local file errors receive at most three bounded attempts; validation, evidence and authorization failures do not receive blind retries
- notifications are disabled in foreground generation; optional compatibility notices disclose no intake or failure details and do not establish acknowledgment

### 6. Analysis, Transcript And Attribution Gate

- the approved plan names the separately authenticated model connection, allowed synthetic brief/evidence, model, credit cap and deadline before inference
- the worker verifies configured CLI/runtime hashes, restricts the child environment/profile, exposes no model tools and permits no automatic paid retry or provider switch
- transcript entries preserve available text, choices, corrections, controls and generation-only approval; summaries and missing history are labeled, never reconstructed
- the transcript remains local and is excluded from the analysis-model prompt; the supplied brief still carries the actual business answers and corrections
- session-capture start/end times, original message timestamps, supplied intake metadata and real report-generation time are distinct records
- John Doe is the labeled default when no submitter name is supplied; any display name remains unverified and is not an owner assignment, reviewer identity or customer consent
- final generation approval closes capture, not either customer decision; completed reports and captured history must not be rewritten to conceal later changes

These controls assume a trusted local user. They are not OS-enforced immutable storage, a signature, encrypted multi-user isolation or customer authorization. The [durable private-runner design](architecture.md) is documentation only.

## Authority Matrix

| Decision                | Agent may prepare                                            | Human must authorize                                                                                    |
| ----------------------- | ------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------- |
| Evidence plan           | Source proposal and provenance check                         | Source purpose, access, sensitivity, and use                                                            |
| Customer facts          | Extraction and normalization                                 | Accuracy and completeness                                                                               |
| Risk                    | Identification, evidence, and possible treatment             | Acceptance, exception, or escalation                                                                    |
| Architecture            | Options, tradeoffs, conditions, recommendation               | Selection and product fit                                                                               |
| Selected design dossier | Draft coverage and proposed delivery-readiness documentation | After architecture selection: approval of the exact immutable dossier revision in the customer workflow |
| Communication           | Draft questions, agenda, and talk track                      | Customer-facing commitments and delivery                                                                |
| Release                 | Validation evidence and exact revision                       | Approval or rejection                                                                                   |

## Threat Model

| Threat                       | Example                                                      | Preventive control                                                                                          | Detective or recovery control                                                              |
| ---------------------------- | ------------------------------------------------------------ | ----------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------ |
| Unauthorized retrieval       | Agent follows an unapproved path or source link              | Allowlisted IDs, contained paths, read-only connector                                                       | Acquisition failure and source-policy finding                                              |
| Cross-customer leakage       | Content from another account enters an intake                | Synthetic-only reference; one customer per local job store, with hardened deployment isolation still future | Configuration mismatch rejection, heuristic identifier scan and reviewer inspection        |
| Prompt injection in evidence | Source asks the agent to ignore policy                       | Evidence is data, not instructions; repository contract has precedence                                      | Citation review and unexpected-output checks                                               |
| Unsupported claim            | Plausible statement lacks evidence                           | Claim labels and required evidence IDs                                                                      | Validation failure and reviewer correction                                                 |
| Stale evidence               | Policy revision changes after generation                     | Source revision and hash pinned to the run                                                                  | Evidence-refresh workflow and semantic diff                                                |
| Over-automation              | Agent treats passing tests or PR review as customer approval | Pending decision objects and `releaseAuthorized=false` are schema- and runtime-enforced                     | Qualified customer roles, authoritative decision references and blocked state              |
| Secret exposure              | Token appears in issue, fixture, log, or deck                | No-secret instructions and local synthetic path                                                             | Repository scan and human inspection; hosted secret scanning must be separately configured |
| Path traversal               | Tool receives `../` or an absolute path                      | MCP accepts an evidence ID, connector rejects unsafe paths                                                  | Unit tests and failed tool call                                                            |
| Misleading maturity          | Proposed design appears deployed                             | Allowed maturity and implementation-state constants                                                         | Schema validation and release review                                                       |
| Evaluation bias              | Handpicked cases overstate quality                           | Approved sampling and blind rubric                                                                          | Error analysis, retained failures, second-customer test                                    |

## Standards Mapping

Standards-aware engineering is part of the value proposition, but the distinction matters: MOSAIC can structure customer-approved control objectives and evidence; it cannot confer compliance by generating artifacts. No completed SOC 2 examination, NIST conformity assessment, ITIL practice implementation assessment, or ISO certification is established by this repository.

Official terminology checked on 2026-09-15: [AICPA SOC resources](https://www.aicpa-cima.com/resources/landing/system-and-organization-controls-soc-suite-of-services) describe CPA assurance services and scoped control examinations; [NIST AI RMF](https://www.nist.gov/itl/ai-risk-management-framework) is a voluntary risk-management framework; [PeopleCert ITIL 4 Foundation](https://www.peoplecert.org/browse-certifications/it-governance-and-service-management/ITIL-1/itil-4-foundation-2565) describes service-management practices, governance, the service value system, and continual improvement. "NIST" must identify the applicable publication and scope, not stand in for a universal compliance label. [ISO/IEC 42001](https://www.iso.org/standard/81230.html) remains a separate management-system reference.

The mapping below is conceptual. Measures and human approvals are proposed unless recorded independently; no clause-level coverage or completed production control is implied.

| Practice                           | MOSAIC evidence                                                                                                              |
| ---------------------------------- | ---------------------------------------------------------------------------------------------------------------------------- |
| NIST AI RMF GOVERN                 | Named owners, policy versions, decision rights, review records                                                               |
| NIST AI RMF MAP                    | Business context, users, data boundary, dependencies, harms, unknowns                                                        |
| NIST AI RMF MEASURE                | Coverage, unsupported claims, correction rate, review time, access exceptions                                                |
| NIST AI RMF MANAGE                 | Fail-closed gates, evidence requests, correction path, release decision                                                      |
| ISO/IEC 42001-informed management  | Versioned controls, traceability, accountability, evaluation, change records                                                 |
| SOC 2-informed change control      | Pull requests, checks, reviewer evidence, least privilege, immutable revisions                                               |
| ITIL 4-informed service management | Proposed change, knowledge, service-level, incident, and continual-improvement evidence carried into operations and handover |

For an actual customer mapping, record the framework/version, scoped requirement, accountable control owner, implementation, evidence, test or review result, exception, and qualified assessor disposition. Customer authorization is required before importing restricted standards or internal policies. Public terminology research is not an addition to the synthetic design evidence allowlist.

## Privacy And Data Protection

The contest scenario contains no personal or customer data. A production assessment must define purpose limitation, data minimization, lawful authority, classification, residency, encryption, user authorization, retention, deletion, legal hold, audit access, and incident handling before retrieval is enabled.

Retrieval must preserve source-system permissions. An agent's ability to find content does not grant the right to use, retain, summarize, or disclose it.

## Model And Prompt Governance

A production workflow pins approved prompt, skill, model, policy, schema, and template versions. Model changes trigger regression evaluation against retained benchmark cases. Prompts cannot weaken deterministic source, schema, identity, or approval controls. Model output is treated as proposed analysis until checks and qualified review complete.

## Monitoring And Audit

The minimum production telemetry plan separates:

- workflow latency from human wait time
- tool invocation, source access, and connector failures
- model and prompt versions
- evidence coverage and unsupported claims
- corrections, review outcomes, and retained content
- cost per package and rate-limit behavior
- access, privacy, safety, and policy exceptions

Telemetry must not capture source content or personal data by default. Audit export and retention follow customer policy.

## Incident And Correction Path

1. Stop the affected workflow and disable the connector when needed.
2. Preserve the run ID, revision, tool activity, and evidence hashes.
3. Route the incident through the approved security or privacy process.
4. Correct the source, policy, prompt, or producer rather than editing generated evidence.
5. Create a new versioned run and compare semantic changes.
6. Require fresh qualified review; prior approval does not carry forward automatically.
