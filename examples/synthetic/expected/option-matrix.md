# Employee Policy Guidance: Architecture Option Matrix

## Use Case Context

**Use case:** Employee Policy Guidance

**Business problem:** Employees cannot reliably find current policy answers across distributed content, creating repeated service inquiries, inconsistent guidance, and slow escalation to accountable policy owners.

**Assessment scope:** Scope requires confirmation with the customer.

**Affected users:** Employees seeking policy guidance; Service desk analysts handling repeated inquiries; Policy owners accountable for authoritative interpretation

> Options are proposed analysis, not an authorized customer decision.

Seeded qualitative scenario analysis, not a scored product evaluation. Product fit, costs, and prioritization require qualified review.

| ID | Option | Pattern | Best when |
| --- | --- | --- | --- |
| OPT-A | Managed low-code agent | Managed agent platform with approved content connectors | Rapid adoption and managed lifecycle controls outweigh bespoke behavior. |
| OPT-B | Custom governed application | Custom application with explicit API and retrieval boundaries | Custom orchestration, evaluation, and integration control are primary. |
| OPT-C | Hybrid governed experience | Managed conversational surface with policy and retrieval services behind typed APIs | Managed adoption and custom policy enforcement are both required. |

## Common Criteria

| Criterion | OPT-A | OPT-B | OPT-C |
| --- | --- | --- | --- |
| Outcome alignment | Validate policy answers and human escalation in a pilot. | Engineer and evaluate policy answers and escalation. | Validate the managed experience and custom policy service. |
| Evidence and grounding | Check managed connector coverage and citation behavior. | Own retrieval, citation, and evaluation behavior. | Expose approved evidence through typed retrieval APIs. |
| Identity and data boundary | Verify source permissions survive retrieval. | Implement and test user-context authorization. | Test authorization across both platform boundaries. |
| Extensibility | Stay within the platform's supported extension model. | Custom orchestration within approved service limits. | Extend policy services without replacing the whole experience. |
| Lifecycle governance | Use managed publishing with approved change controls. | Own releases, regression checks, and monitoring. | Coordinate API and experience releases and checks. |
| Operating ownership | Assign platform and content owners. | Requires a funded product engineering and service team. | Needs clear ownership across both platform teams. |
| Cost and adoption | Estimate licensing and configuration effort; not measured. | Estimate build and operating costs; not measured. | Estimate both platforms and integration; not measured. |

## Tradeoffs And Entry Conditions

### OPT-A: Managed low-code agent

**Strengths to validate:**

- Fastest path to pilot
- Managed authoring and channel lifecycle

**Tradeoffs to discuss:**

- Less control over custom orchestration
- Connector fit requires validation

**Entry conditions to verify:**

- Approved connector coverage
- Tenant governance configured

**Disqualifiers to test:**

- Required behavior exceeds extension model

### OPT-B: Custom governed application

**Strengths to validate:**

- Maximum extensibility
- Fine-grained evaluation and integration control

**Tradeoffs to discuss:**

- Higher engineering and operating burden
- Longer controlled rollout

**Entry conditions to verify:**

- Product engineering ownership
- Approved model and region

**Disqualifiers to test:**

- No funded operations owner

### OPT-C: Hybrid governed experience

**Strengths to validate:**

- Balanced extensibility
- Separates experience from governed services

**Tradeoffs to discuss:**

- More integration boundaries
- Requires clear dual-platform ownership

**Entry conditions to verify:**

- API ownership
- Identity propagation design
- Joint lifecycle model

**Disqualifiers to test:**

- Cross-platform ownership cannot be assigned

## Recommendation

**OPT-C**: Advance the hybrid pattern to discovery validation, subject to the listed unknowns and human selection.  
Evidence: EVD-003, EVD-004

## Decision State

`awaiting_authorized_customer_selection`

## Selection Readiness

| Blocking question | Issue to resolve | Plans referencing it |
| --- | --- | --- |
| UNK-001 | Who is the final production data owner? | PLAN-001; PLAN-004; PLAN-007 |
| UNK-002 | What production identity and authorization model is approved? | PLAN-001; PLAN-002; PLAN-003; PLAN-004; PLAN-005; PLAN-006 |
| UNK-003 | What retention period applies to prompts, evidence, and review records? | PLAN-002; PLAN-005; PLAN-007 |
| UNK-004 | Which model, deployment region, and acceptance thresholds are approved? | PLAN-001; PLAN-003; PLAN-005; PLAN-006; PLAN-007 |

Verify each option's entry conditions and challenge its disqualifiers. Cost, effort and product-fit
statements remain qualitative unless the evidence supplies a validated estimate. No numerical
ranking or weighted score is established here. Resolve blocking questions before selection.

## Architecture Decision Record

Record the selected option or explicit deferral, alternatives considered, business rationale,
tradeoffs accepted, outstanding conditions, authorized decision-maker, supporting evidence and
exact comparison revision in the customer's workflow.

An informal preference is not selection. Only an authorized selection permits the selected full
dossier to proceed; its exact-revision approval remains a later decision.
