# Evaluation Plan

## Purpose

MOSAIC is AI-first business process automation for solution engineering. Determine whether its governed intake-to-dossier process makes Microsoft expertise more reusable for small businesses through large enterprises and increases delivery capacity with less effort, rework, elapsed lifecycle time, process complexity, and total cost, while improving structured-report consistency and preserving correctness, security, and human authority. The first study covers design preparation and review. Later, independently authorized studies can evaluate the broader SDLC extensions. This document does not report completed customer results.

The bundled seed and deterministic tests establish reproducibility and structural guardrails, not reasoning quality or time saved. A scripted synthetic intake has also completed bounded live model analysis; that single run is not customer evidence, native App execution or a comparative result. Before this study, collect qualified review and corrections against actual agent-produced analysis, and wire any scenario-specific configuration that the study depends on. Keep semantic source support distinct from citation-ID validity. No head-to-head Copilot/Claude benchmark has been run.

## Planning Economics

**Base planning case: 80 specialist hours returned per eligible intake/design request, about 83% less effort, and $16,000 of gross capacity value at an assumed $200/hour.** At an illustrative 100 eligible requests per year, that is 8,000 hours and $1.6 million of gross capacity value before additional costs. These are scenario estimates, not measured savings, a customer-volume forecast, cash budget reductions or staffing commitments.

The business opportunity is reusable solution-engineering capacity across customers and field roles. The source engagement was a test case, not the scope of MOSAIC or evidence that the same savings apply to every customer. The scope of this model is intake, research, design preparation and review, not implementation or the entire delivery lifecycle.

### Inputs And Provenance

`ECO-001` is the entrant-provided internal leadership brief, reviewed September 16, 2026, with economic inputs on pages 4, 13-15 and 21-22. The original is marked confidential/internal and remains outside Git. No source screenshots, customer identities, records, contacts or implementation claims are reproduced here. This is an internal planning model for the contest entry, separate from the four `EVD-` sources used by the synthetic design demonstration. External distribution remains subject to the owner's rights and disclosure review.

| Input                      | Planning value                                            | Interpretation                                                                                                                    |
| -------------------------- | --------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------- |
| Manual intake              | 8-24 hours per item                                       | Source planning range, not a measured sample                                                                                      |
| Manual solution design     | 40-120 hours per item                                     | Source planning range for preparation before implementation                                                                       |
| Combined manual effort     | 48-144 hours; 96-hour midpoint                            | Midpoint is not an observed average                                                                                               |
| Retained human validation  | 16 hours in the base case; 8 and 24 hours for sensitivity | Assumptions to measure, not demonstrated review times                                                                             |
| Loaded labor value         | $200/hour                                                 | Illustrative midpoint of the source's $175-$225 planning range; not a quoted Microsoft price or customer billing rate             |
| Additional retained effort | Zero in the displayed base calculation                    | Add any coordination, corrections or exception handling not already included in the 16 hours; do not assume these costs disappear |
| Annual eligible volume     | 100 items in the pitch illustration                       | Normalized example, not a workload forecast; the source also illustrates 24, 72 and 144 items                                     |

The source's under-five-minute initial generation figure is itself a planning claim and excludes review and engagement. It is not an end-to-end completion time or a measured performance result for this repository. Machine generation duration is not interchangeable with specialist labor hours.

### Reproducible Arithmetic

```text
Returned specialist hours/item = manual hours - retained review hours - other retained hours
Base returned hours/item       = 96 - 16 - 0 = 80
Base effort reduction          = 80 / 96 = 83.33%
Gross capacity value/item      = 80 hours * $200/hour = $16,000
Gross annual capacity value    = eligible annual items * returned hours/item * loaded hourly value
Illustrative annual capacity   = 100 * 80 = 8,000 hours; 100 * $16,000 = $1,600,000
Net economic value             = gross capacity value - additional platform, integration,
                                 governance, support and operating costs
```

Do not subtract the same retained review labor twice: it is already deducted in returned hours. Capture additional human effort in the hours model or as a cost, not both. Capacity has economic value only if the organization can productively redeploy it or avoid expenditure; gross capacity is not automatically realized financial savings.

### Review-Time Sensitivity

The following holds the manual baseline at 96 hours, the hourly value at $200, and other retained effort at zero. Actual results must also account for baseline variation and case complexity.

| Retained review | Hours returned per item | Effort reduction | Gross capacity value per item |
| --------------- | ----------------------: | ---------------: | ----------------------------: |
| 24 hours        |                      72 |            75.0% |                       $14,400 |
| 16 hours        |                      80 |            83.3% |                       $16,000 |
| 8 hours         |                      88 |            91.7% |                       $17,600 |

### Scale And Cost Thresholds

| Illustrative eligible items/year | Hours returned/year | Gross capacity value/year |
| -------------------------------: | ------------------: | ------------------------: |
|                               24 |               1,920 |                  $384,000 |
|                               72 |               5,760 |                $1,152,000 |
|                              100 |               8,000 |                $1,600,000 |
|                              144 |              11,520 |                $2,304,000 |

At $16,000 of gross capacity per item and zero additional per-item cost, illustrative annual cost envelopes of $100,000, $250,000 and $500,000 require 7, 16 and 32 eligible items respectively to exceed the cost in capacity-equivalent value. These are not cash break-even guarantees. With an additional per-item cost, use `ceil(annual fixed cost / (gross capacity per item - additional per-item cost))`; no finite threshold exists in this model when the denominator is nonpositive.

The pilot must measure retained review and exception effort, quality, actual eligible volume and total operating cost. That tests the economic proposition without claiming the planning figures are already achieved. Explain the business problem and the preparation work first, then quantify the opportunity; the qualifications should travel with the numbers.

## Hypotheses

1. MOSAIC increases requirements and evidence coverage compared with the existing preparation method.
2. MOSAIC reduces active document-assembly time while preserving or improving qualified review quality.
3. Claim labeling and evidence manifests reduce unsupported material statements.
4. A second customer configuration can reuse the core workflow without code redesign.
5. An independently authorized delivery extension reduces lead time and handover defects without weakening acceptance, security, or operating readiness.

## Study Design

- **Sample:** 10-20 sanitized historical requests selected under an approved sampling plan.
- **Window:** A proposed six-week controlled discovery.
- **Comparison:** Existing package versus MOSAIC package, reviewed using the same rubric.
- **Blinding:** Reviewers should not know which package is expected to perform better when practical.
- **Stratification:** Include simple, incomplete, high-risk, and cross-system requests.
- **Retention:** Preserve failures, corrections, excluded cases, prompt/model versions, and adjudication notes.
- **Safety:** No live customer action follows from benchmark output.

## Measures

| Measure                      | Definition                                                                                                      | Direction                                                               |
| ---------------------------- | --------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------- |
| Requirements coverage        | Required rubric items present and usable / applicable rubric items                                              | Higher is better                                                        |
| Evidence coverage            | Material factual claims with valid approved evidence / material factual claims                                  | Higher is better                                                        |
| Unsupported-claim rate       | Material claims without valid support / material claims                                                         | Lower is better                                                         |
| Factual correction rate      | Material factual statements changed by reviewers / material factual statements                                  | Lower is better                                                         |
| Omission rate                | Required findings absent / applicable required findings                                                         | Lower is better                                                         |
| Risk and dependency coverage | Reviewer-confirmed material risks and dependencies surfaced / total confirmed                                   | Higher is better                                                        |
| Active preparation time      | Human minutes spent collecting and assembling before review                                                     | Lower is better                                                         |
| Qualified review time        | Human minutes from review start to disposition, excluding waits                                                 | Report separately                                                       |
| Post-design rework           | Human effort attributable to missing, incorrect, or ambiguous upstream information                              | Lower is better; avoid double-counting in total cost                    |
| Delivery lead time           | Elapsed time from agreed problem definition to accepted operational readiness in an authorized end-to-end pilot | Lower only when scope and quality are comparable; report external waits |
| Field delivery capacity      | Independently accepted packages per practitioner-period, stratified by case complexity                          | Higher without shifting hidden work to reviewers or operations          |
| Operational readiness        | Approved service, recovery, support, training, and handover criteria actually exercised and accepted            | Higher; document presence alone is insufficient                         |
| Content retention            | Generated content retained after review / generated content reviewed                                            | Diagnostic, not a goal alone                                            |
| Package acceptance           | Packages approved or conditionally approved / packages reviewed                                                 | Higher only when defect thresholds hold                                 |
| Access or policy exceptions  | Unauthorized, over-broad, or policy-breaking retrieval events                                                   | Must remain zero                                                        |
| Cost per package             | Model, connector, compute, and reviewer cost attributed to one run                                              | Understand before scale                                                 |

## Proposed Guardrail Thresholds

Thresholds require owner approval before the study. Initial proposals are:

- zero unauthorized source access or secret exposure
- zero self-authorized architecture or release decisions
- 100 percent valid citations for facts, recommendations, and recorded decisions
- 100 percent visibility of reviewer-confirmed critical risks and blocking unknowns
- no statistically or operationally material quality regression against the existing method

Do not optimize time or acceptance rate at the expense of these guardrails.

## Live Agent Behavior Regression

The opt-in regression in `tests/test_agent_behavior.py` runs the real MOSAIC custom agent through this exact sequence:

1. `Menu`
2. `1` to start a new intake
3. A fictional travel-guidance business problem
4. `1` to select **End intake and generate report**

It passes only when the first business-problem question omits the premature generation control, subsequent business questions expose it, and the final numeric selection stops intake, returns a bounded plan and requests approval instead of asking another business question. It accepts either text-rendered choices or the native question selector.

This regression consumes GitHub Copilot requests and is therefore excluded from routine offline tests. Run it deliberately with the configured executable:

```powershell
$configuration = Get-Content -LiteralPath 'build\intake\copilot-worker.json' -Raw | ConvertFrom-Json
$env:MOSAIC_TEST_LIVE_AGENT_EXE = $configuration.executable
python -m pytest -o addopts='' -q tests\test_agent_behavior.py
```

The test stops at plan approval and does not authorize document generation.

## Evidence Collection

For each case record:

- sanitized case ID and inclusion rationale
- input revision, source manifest, policy, workflow, prompt, model, schema, and template versions
- generation time and cost
- validation report and tool failures
- blind reviewer rubric and comments
- final corrections, disposition, and retained content
- safety, access, privacy, or policy exceptions

## Analysis

Report distributions and paired differences, not only averages. Separate automated generation time, active human work, and waiting time. Review high-severity misses individually. Small samples support operational learning, not broad causal claims.

Compare the entire work system, including expert review, correction, integration, platform operation, maintenance, and downstream rework. Recovered staff capacity is not automatically cash savings; identify redeployment or actual expenditure changes separately. Do not extrapolate a single seeded package into enterprise-wide financial savings, or treat document volume as proof of quality. Test output caliber with blind, independently adjudicated comparisons against appropriate human-prepared packages; no better-than-human conclusion is established today.

## Portability Test

Configure a second isolated fictitious or authorized sanitized scenario with different terminology, evidence policy, templates, and reviewer roles. Pass only if the core stage and validation code remains unchanged; configuration additions and connector implementations are expected.

## Decision Record

At the end of the study, accountable owners choose one of: stop, correct and repeat, continue a bounded pilot, or prepare production readiness. Document evidence, risks, exceptions, cost, support ownership, and the exact version approved. A favorable benchmark does not authorize production by itself.
