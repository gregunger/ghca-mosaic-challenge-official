# Field Adoption Playbook

## Adoption Goal

MOSAIC is AI-first business process automation for solution engineering. Make Microsoft expertise reusable across customer engagements by automating the repeatable path from business problem through intake, approved evidence, structured analysis, options, proposed design, delivery-readiness preparation and human-review handoff. The intended human value is less repeated effort, more consistent and traceable solution dossiers, faster feedback and lifecycle handoffs, lower avoidable delivery cost, and stronger knowledge transfer. Evaluate those benefits across the lifecycle, not only the minutes needed to generate documents.

The core should remain stable while each customer supplies isolated systems, doctrine, identities, data boundaries, terminology, templates, owners, and approval evidence. Extensibility is a design objective; it is not proof that every use case is solved by changing a configuration file.

Current evidence includes the offline reference, local regressions and an explicitly scripted synthetic intake completed through bounded live model analysis. The CLI checks customer/source-policy identity and option count, applies required reviewer roles, and rejects unsupported required documents before writing. Tests prove that changed reviewer policy changes the generated JSON, Markdown, HTML and run identity. The report retains captured dialogue separately from model input and marks missing attribution or timing honestly. Native App hands-on acceptance, arbitrary terminology, template customization and live customer adapters remain unproven; these phases do not authorize implementation or deployment.

## Who Reuses What

| Field audience                     | Reusable entry point or output                                                                                                                                                                                  | Practical handoff and retained judgment                                                                                                                                   |
| ---------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Account teams                      | [Intake template](../.github/ISSUE_TEMPLATE/mosaic-intake.yml), [meeting request](../examples/synthetic/expected/meeting-request.md) and [discovery questions](../examples/synthetic/expected/intake-report.md) | Qualify the customer outcome, owners and unanswered questions; the account team retains customer commitments and shares the scoped request with specialists.              |
| Customer success                   | [Meeting agenda](../examples/synthetic/expected/meeting-agenda.md), [talk track](../examples/synthetic/expected/talk-track.md) and [human-review record](../examples/synthetic/expected/human-review.md)        | Run the decision workshop, surface dependencies and acceptance questions, and retain customer ownership of adoption and acceptance.                                       |
| Solution sales                     | [Three-option comparison](../examples/synthetic/expected/option-matrix.md) and [architecture brief](../examples/synthetic/expected/architecture-brief.md)                                                       | Explain product fit, tradeoffs and conditions with architects; do not turn a conditional recommendation into an approved design, quote or savings guarantee.              |
| Developers and solution architects | [Evidence appendix](../examples/synthetic/expected/evidence-appendix.md), [validation report](../examples/synthetic/expected/validation-report.json), schemas and tests                                         | Inspect traceability and design constraints, reproduce the reference, and propose versioned changes for qualified review before any separately authorized implementation. |

The existing [report](../examples/synthetic/expected/index.html) is directly inspectable without coding. Practitioners can reuse the method and manually adapt the templates, while a maintainer runs the reference and tests. The configured App workflow coordinates specialist responsibilities around that shared package; full multi-agent execution and reviewer correction still require demonstration. Do not copy another customer's data or imply that editing a configuration file automatically produces a correct new design.

## Customer-Specific Report Customization

The product design supports highly customized customer reporting while retaining a stable governed core. An isolated customer installation can define:

- organization branding, report titles and approved terminology;
- required document profiles and customer-specific sections;
- reusable Markdown and HTML templates;
- evidence classifications, source policies and control mappings;
- reviewer roles, decision language and approval rules;
- glossary entries, guidance text and engagement materials.

Customization may tighten presentation and policy but cannot remove evidence provenance, assumptions, unknowns, risks, decision state, proposed maturity, implementation status or human-authority controls. The contest reference proves a shared renderer, customer-configured reviewer roles, unsupported-document rejection, common report templates and manual template adaptation. It does not yet prove arbitrary customer-selected templates, branding controls or zero-code terminology mapping. Those capabilities require versioned configuration, regression tests and qualified customer review.

## Adoption Phases

| Phase                   | Scope                                                                     | Exit evidence                                                                    |
| ----------------------- | ------------------------------------------------------------------------- | -------------------------------------------------------------------------------- |
| 0. Synthetic proof      | Run the bundled request with no network or customer data                  | Tests pass, package validates, release remains blocked                           |
| 1. Controlled benchmark | Evaluate 10-20 sanitized historical cases over a proposed six-week window | Approved sample, blind rubric, measured errors, no material access failure       |
| 2. Portability proof    | Configure a second isolated customer pattern with different doctrine      | Core reused without redesign; boundaries and operating cost understood           |
| 3. Controlled rollout   | Enable approved read-only connectors for a limited cohort                 | Owners, SLOs, thresholds, support, rollback, privacy, security, and RAI approval |
| 4. Scale decision       | Expand scenarios or teams only after evidence supports it                 | Benefits and risks reviewed; capacity and governance funded                      |

Durations and sample sizes are proposals, not completed evaluation evidence.

## Governed SDLC Extension

**Preparing delivery-readiness documentation is current design scope; executing delivery is an extension.** MOSAIC's full name is Multi-customer Orchestration System for Adaptive Intake and Continuous Delivery. Continuous Delivery describes direction, not a claim that this reference deploys solutions. Architecture selection in the customer's workflow precedes the selected full dossier. Final design approval refers to its exact immutable repository revision. This reference supplies an unselected draft with all ten coverage areas and seven traceable plans, then stops before either customer decision.

The following execution roadmap is not implemented capability or permission to act. Preserve evidence and decisions across stages, but require fresh authority for each consequential action.

| Extension                                  | Intended output                                                                                                | Required entry/exit gate                                                                                                                            |
| ------------------------------------------ | -------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------- |
| Application and infrastructure engineering | Application scaffolding, infrastructure-as-code modules, configuration contracts, build instructions           | Approved design, isolated development scope, code review, static checks, and provider-specific plan/validation evidence                             |
| Delivery pipelines                         | Build/test/deployment pipelines, environment promotion rules, artifact provenance, rollback procedures         | Approved identities and least privilege, immutable artifacts, pipeline tests, and explicit release ownership                                        |
| Automated quality engineering              | Unit, integration, end-to-end, security, performance, resilience, and quality-assurance tests                  | Requirement-to-test traceability, independently reviewed expected results, and approved thresholds; generated tests cannot self-certify correctness |
| User validation                            | User acceptance scenarios, test scripts, usability evidence, acceptance records                                | Representative users and an accountable customer acceptance owner; no agent-supplied customer sign-off                                              |
| Staging and production                     | Promotion plans, readiness evidence, staged rollout, rollback and recovery checks                              | Separately approved environment access and change/release decisions; passing design checks never authorizes deployment                              |
| Operational documentation                  | Runbooks, service expectations, monitoring/alert response, incident and recovery procedures, support ownership | Operations review, exercised recovery paths, approved retention and service measures                                                                |
| Operations staff training, turnover        | Role-based training, exercises, knowledge-transfer packages, escalation paths, handover records                | Receiving team's demonstrated readiness and explicit operational acceptance                                                                         |

Each extension should have a versioned input/output schema, approved evidence boundary, producer, validation suite, artifact contract, and accountable decision owner. Carry the originating requirement, evidence, architecture decision, test result, and human disposition together so handover does not depend on reconstructing a chat transcript. This describes the target architecture; those additional producers and integrations still need implementation and evaluation.

Plans for those activities belong in the design dossier now: business outcome, requirements and acceptance, feasibility and risks, alternatives and decision, threat model and data flow, proposed implementation and verification, proposed interfaces, security and dependency requirements, proposed deployment and rollback, and proposed operations/adoption/measurement. Planning an operations handover does not perform the handover; planning a release does not authorize it.

## Customization Model

Customer variation belongs in approved source profiles, terminology, control objectives, role/decision mappings, artifact contracts, integration adapters, and evaluation cases. A portability exercise must show which changes are configuration-only and which require a producer or connector change. The fixed reference renderer does not yet consume all of these fields.

The governing customer policy package is immutable and versioned. Lower layers may add constraints but may not weaken the baseline. Keep provider-specific ticket, grounding, revision-control and identity/secret behavior behind canonical adapters with declared capabilities. Missing capability must surface as a finding and wait, never an invented result. Keep customer decisions in the customer's authoritative workflow; do not add a parallel MOSAIC approval inbox.

Use customer-selected SOC 2 control objectives, specific NIST publications, and ITIL 4 practices as mapping inputs. Record scope, version, control owner, required evidence, test/review method, exceptions, and the actual assessor's disposition. Merely naming a framework or producing a document does not establish compliance. See the [official-source mapping](governance-and-rai.md#standards-mapping).

## Customer Configuration Workshop

Complete these decisions before connecting data:

1. Define the eligible request class and authoritative request system.
2. Name business, policy, architecture, security, data, service, and release owners.
3. Inventory source purposes, owners, classifications, revisions, access models, and freshness expectations.
4. Map customer terminology to canonical MOSAIC contracts.
5. Define required documents, templates, stage gates, and reviewer roles.
6. Approve identity, least-privilege scopes, network paths, retention, deletion, audit, and disable procedures.
7. Define benchmark cases, correctness rubric, risk thresholds, and stop criteria.
8. Pin the initial policy, workflow, prompt, model, schema, and template releases.

## Reusable Core Versus Customer Configuration

| Reusable core                                       | Customer-owned configuration                                  |
| --------------------------------------------------- | ------------------------------------------------------------- |
| Eight stage contracts                               | Phase names and upstream state mappings                       |
| Claim labels and evidence semantics                 | Approved doctrine, sources, classifications, and terminology  |
| JSON schemas and deterministic checks               | Additional required fields and thresholds                     |
| GitHub issue, branch, PR, check, and review pattern | Repository location, permissions, branch and review rules     |
| Specialist roles and prompt structure               | Named human roles and authorization evidence                  |
| Artifact and audit contracts                        | Templates, retention, legal, privacy, and audit requirements  |
| Fail-closed source connector interface              | Identity, scopes, rate limits, network, and disable procedure |

## Field Kit

A customer-ready engagement includes:

- one release-safe synthetic demonstration
- one approved scenario and persona statement
- customer configuration and source-policy drafts
- data-flow and trust-boundary review
- connector purpose and least-privilege worksheet
- benchmark plan and scoring rubric
- human decision-rights matrix
- support, rollback, and incident model
- explicit non-goals and claims register

## Go Or No-Go Criteria

Proceed to controlled data access only when:

- the use case is eligible and the business owner is accountable
- data purpose, sources, identities, classifications, and retention are approved
- required reviewers and authoritative decision records are configured
- benchmark cases and stop thresholds are approved
- connector failure cannot silently broaden access or produce uncited content
- support, monitoring, cost, disable, correction, and incident ownership exist

Stop when evidence is insufficient, policy conflicts, identity cannot preserve source authorization, material risks lack owners, or the customer cannot define acceptance.

## Operating Model

| Role                       | Accountable outcome                                     |
| -------------------------- | ------------------------------------------------------- |
| Capability owner           | Product roadmap, funding, adoption scope, value review  |
| Service owner              | Availability, support, incidents, capacity, releases    |
| Policy owner               | Doctrine currency, exceptions, source approval          |
| Data owner                 | Purpose, access, classification, retention, deletion    |
| Architecture owner         | Pattern approval and technical integrity                |
| Security and RAI reviewers | Control, risk, evaluation, and monitoring approval      |
| Field practitioner         | Intake quality, customer discovery, correction feedback |

## Scale Without Diluting Control

For a future implementation, add scenarios through versioned configuration and tests after proving the required fields are actually consumed. Add customers through independently authorized isolated installations. Add automation only after bounded evidence shows that the next delegated action is deterministic, reversible, observable, and covered by an accountable review model.
