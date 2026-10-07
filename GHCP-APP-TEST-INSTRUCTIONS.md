# GitHub Copilot App Test Instructions

## Purpose

MOSAIC is AI-first business process automation for solution engineering. A user describes a business problem in plain language, the App asks relevant questions, and an approved generation run produces a governed 23-artifact solution dossier for human decisions. Use this exact test to verify that experience in the GitHub Copilot App. The test covers:

- the opening menu;
- the required **End intake and generate report** control;
- the numeric `1` regression;
- bounded-plan approval;
- optional end-to-end generation;
- the 23-artifact report handoff;
- human-review and release safeguards.

The scenario is fictional and contains no real customer or employee data.

## Required Version And Setup

1. Confirm the repository is on the latest `origin/main`. The current contract's first business question begins with **Reduce manual work** and does not offer generation.
2. Close and reopen the GitHub Copilot App, or start a completely new App session after updating the repository. Do not reuse a session that loaded an older revision.
3. Open this repository as the active workspace.
4. Select **MOSAIC Orchestrator** in the agent picker.
5. Use a regular or medium reasoning setting. Record the actual App model and reasoning setting used.
6. Keep the PC and App running for the entire test.
7. Do not use real names, customer records, tenant IDs, subscription IDs, credentials or restricted screenshots.

## Concrete Fictional Use Case

**Organization:** Contoso Public Services  
**Business area:** Employee Services and Finance  
**Users:** 250 fictional field employees  
**Problem:** Employees rely on conflicting travel-policy documents and submit avoidable noncompliant claims.  
**Desired outcome:** One trusted way to find current, cited travel guidance and route exceptions to Finance.  
**Current system:** SharePoint  
**Initial-work ceiling:** $30,000  
**Proposal date:** 15 October 2026  
**Scope boundary:** Proposal and design only; no implementation or deployment  
**Primary risk:** Giving employees an incorrect policy answer  
**Baseline:** Unknown and must remain unknown

## Test A: Numeric End-Intake Regression

This test does not approve generation and should not invoke the separate analysis model.

### Step 1: Open The Menu

Start a new MOSAIC Orchestrator session and enter:

```text
Menu
```

### Expected Result

The App must immediately display:

```text
MOSAIC
Solution Engineering Process Automation

1. Submit a new intake request
2. How it works
```

Fail the test if the App reads files, searches the repository, runs commands, shows debug output or asks a business question before displaying the menu.

### Step 2: Start A New Intake

Enter:

```text
1
```

### Expected Result

The App must ask:

```text
What business problem or opportunity would you like help with?
```

The first question must contain only business-need choices, such as:

```text
1. Reduce manual work
2. Find trusted guidance
3. Improve an experience
4. Something else
```

The first question must not offer **End intake and generate report** because no business need has been supplied yet.

Fail the test if the first business question offers generation, shows only unnumbered examples or performs setup work.

### Step 3: Provide The Concrete Business Need

Paste this exact fictional request:

```text
I run Employee Services at fictional Contoso Public Services. Our 250 fictional field employees keep finding conflicting mileage, hotel and overnight-travel guidance across SharePoint pages, PDFs and saved email replies. Some claims are rejected after employees have already spent the money, and Employee Services and Finance repeatedly answer the same questions.

I want one trusted way for employees to ask questions such as "Can I claim mileage for this trip?" and "Who approves an overnight stay?" and receive an answer linked to the current policy. Anything requiring an exception must go to Finance instead of receiving a guessed answer.

Keep this to a proposal and design for travel-policy guidance; do not implement or deploy anything. SharePoint is the current system. Finance owns the policy. There is up to $30,000 for initial work, and I need the proposal by 15 October 2026. The biggest risk is giving someone the wrong answer. We do not yet have a reliable baseline for rejected claims or repeat questions.
```

### Expected Result

The App may briefly reflect the request, then ask no more than one relevant business question at a time.

Starting with this question after the first business answer, every business question must include **End intake and generate report** as option 1 in the visible response or native selector. A later bare question without the control is a failure.

### Step 4: Select Option 1

At the first business question after the request, enter exactly:

```text
1
```

### Required Result

The App must stop asking optional business questions and display a bounded generation plan.

The plan must:

- summarize the supplied fictional problem and constraints;
- preserve the unknown baseline as unknown;
- identify missing details as unknown rather than inventing them;
- request explicit approval before generation.

The App must not:

- interpret `1` as an answer to the business topic;
- return to the opening menu;
- ask another business question;
- capture files or call the analysis model before approval.

**Test A passes only if the next response is the bounded plan and approval request.**

### Stop Point For Regression-Only Testing

If testing only the numeric regression, do not approve the plan. End the session here and record:

- App model;
- reasoning setting;
- whether the first question omitted the generation control;
- whether option 1 appeared on every subsequent question;
- whether the final `1` opened the generation plan;
- elapsed time from the final `1` to the plan;
- screenshot or transcript of the final selection and plan.

## Test B: Full End-To-End Generation

Continue only when a paid, bounded generation run is intended.

### Step 5: Inspect The Plan

Before approving, verify that the plan discloses:

- the four allowlisted synthetic evidence sources: `EVD-001` synthetic intake, `EVD-002` synthetic architecture standard, `EVD-003` synthetic security standard and `EVD-004` synthetic data policy;
- the enabled read-only synthetic evidence tools;
- the separately authenticated Copilot CLI analysis connection;
- the configured AI-credit cap and deadline;
- local transcript capture after approval;
- exclusion of the transcript from the analysis prompt;
- exactly three architecture options;
- 23 output artifacts;
- a separate processing cost and pipeline trace report;
- no customer connectors, external writes, implementation or deployment;
- no automatic paid retry;
- the stop at `awaiting_human_review`;
- `releaseAuthorized=false`.

Do not approve if any boundary is missing or if the App claims customer approval, production deployment, measured savings or established compliance.

### Step 6: Approve The Exact Plan

Enter:

```text
Approve and generate
```

If the displayed approval label differs, select the exact approval label shown by the App rather than using a number.

### Expected Result

The App should:

1. capture the available conversation once;
2. acquire only the four allowlisted synthetic sources;
3. run one bounded analysis call;
4. execute `Discover -> Acquire -> Normalize -> Analyze -> Option -> Design -> Prepare -> Review`;
5. validate and publish one report revision;
6. stop at human review.

A brief **Preparing your documents...** message is acceptable. Repeated progress claims, optional intake questions, a second generation attempt or an indefinite wait after a terminal failure are failures.

Do not close the App or turn off the PC while generation is running.

## Completion Checks

### Required App Handoff

Successful completion must begin with:

```text
Your intake report is ready
```

The response must include:

- a clickable report index;
- **Open documents in browser**;
- **Processing cost & pipeline trace (operator report)** when processing records are ready.

The completed job must report:

```text
artifactCount: 23
reviewState: awaiting_human_review
releaseAuthorized: false
```

### Step 7: Open The Customer Documents

Enter:

```text
Open documents in browser
```

Verify the browser opens the report index, not a status page.

Check that the package contains:

- ten HTML pages;
- nine Markdown reports;
- four JSON records;
- the preserved intake transcript;
- exactly three contrasting architecture options;
- evidence citations and an evidence manifest;
- unresolved questions and risks;
- a validation report;
- an audit ledger;
- an engagement package;
- a blocked human-review record.

Verify the design is labeled `unselected_discussion_draft`. No architecture selection or exact-revision customer approval should be recorded.

### Step 8: Open The Operator Report

Request:

```text
Open the processing cost and pipeline trace report in the browser
```

Verify the operator report shows:

- measured stage and total timings;
- ordered pipeline steps;
- artifact publication events;
- recorded model usage when available;
- unavailable App usage or billing values as unavailable, not zero;
- no invented token, cost or invoice values.

## Pass/Fail Record

Record each result:

| Check                                                    | Pass/Fail | Notes |
| -------------------------------------------------------- | --------- | ----- |
| New session loaded current revision                      |           |       |
| Opening menu appeared immediately                        |           |       |
| First business question omitted premature generation     |           |       |
| Later business question included generation as option 1  |           |       |
| Bare `1` stopped intake                                  |           |       |
| Bounded plan appeared next                               |           |       |
| No separate analysis-model call occurred before approval |           |       |
| Plan disclosed all required boundaries                   |           |       |
| One approved generation run completed                    |           |       |
| 23 artifacts were published                              |           |       |
| Exactly three options were present                       |           |       |
| Browser report opened successfully                       |           |       |
| Operator report and trace were available                 |           |       |
| `awaiting_human_review` was preserved                    |           |       |
| `releaseAuthorized=false` was preserved                  |           |       |

## Failure Handling

- If option 1 is missing, a bare `1` asks another question, or the App returns to the menu, stop and save the visible transcript.
- If generation fails, do not approve another paid attempt automatically.
- Record the terminal error and whether input or analysis was retained.
- Use **Retry generation** only after the cause is corrected and the retained-input recovery path is explicitly authorized.
- Never treat a pull request, report generation or browser launch as customer approval.
