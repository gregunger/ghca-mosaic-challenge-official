# Generation, Capture And Recovery

Load this reference only after the requester chooses to generate documents. Interview answers must not trigger file reads, capture commands, evidence retrieval or analysis. Existing repository safety and stage requirements continue to apply.

## Read Once, Then Disclose

Read the [configured synthetic customer](../../../../config/customers/contoso-public-services.synthetic.json), [source policy](../../../../examples/synthetic/source-policy.json) and [approved source catalog](../../../../examples/synthetic/sources/catalog.json) once. Read the [stage contracts](stage-contracts.md) and [claim/evidence rules](claim-and-evidence-rules.md) once. Do not import the reference request's answers or analysis into this intake. Do not inspect application source, search for metadata definitions, run `--help`, install packages or run regression tests during a normal business intake.

Obtain the operator's non-secret model settings:

```powershell
& '.\.venv\Scripts\python.exe' -E -s -B -m mosaic.jobs copilot-settings
```

If setup or authentication is missing, stop with that prerequisite; do not silently switch providers, authenticate, increase limits or use prepared-input mode. This engine uses a separately authenticated Copilot CLI, not this chat's sign-in or a native App specialist fleet.

Summarize the supplied business need and missing information, then disclose a bounded generation plan:

- Current fictional brief and policy-allowed evidence IDs/classifications. This reference permits only EVD-001 through EVD-004; customer policy may further restrict them.
- Read-only, offline evidence acquisition. Use `mosaic-synthetic-evidence` when available. Independent authorized source reads may run together; do not reread unchanged sources repeatedly in chat. The engine still independently validates and seals its own source bytes.
- One Copilot CLI analysis call with the exact configured model, AI credit cap and deadline. Do not promise a fixed completion time.
- The local transcript is stored with the documents and excluded from the analysis prompt. The business brief still contains the supplied answers and corrections.
- Exactly three comparable options and 23 files: ten HTML pages, nine Markdown reports and four JSON records, including the transcript.
- A separate local operator cost/performance report and pipeline trace. App usage may be unavailable; limits are not charges, and no additional analysis call is made for these records.
- Windows notifications disabled; no customer connectors, external writes, implementation, deployment or automatic paid retries.
- Stop at `awaiting_human_review`; neither architecture selection nor exact-revision design approval is recorded.

Obtain approval for this plan without reopening optional questions. A request to generate only approves a plan already disclosed. If the host requires an execution-mode change, retain the same conversation and approval.

## Brief Recipe

After approval, allocate a new `SYN-` initiative ID for this intake. Never reuse another request's ID or answers. Prepare the local brief under `build\intake\<SYN-initiative-id>\brief.json`. This is agent work, not a form or developer task for the requester.

Use these fields; do not discover them by reading runtime source:

| Field                                               | Required content                                                                                                                                                                                                 |
| --------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `schemaVersion`, `workflowVersion`, `policyVersion` | Versions from the configured local contracts, not invented product versions.                                                                                                                                     |
| `inputMode`                                         | `conversation`                                                                                                                                                                                                   |
| `customerId`                                        | The configured synthetic customer identity.                                                                                                                                                                      |
| `initiativeId`                                      | The new `SYN-` ID for this intake.                                                                                                                                                                               |
| `correlationId`                                     | A local correlation identifier for this run.                                                                                                                                                                     |
| `sourceTicketRef`                                   | An explicitly local conversation reference, not an invented customer ticket.                                                                                                                                     |
| `requestedAt`                                       | Available UTC intake metadata ending in `Z`; never invent a historical message time.                                                                                                                             |
| `classification`                                    | `SYNTHETIC`                                                                                                                                                                                                      |
| `initiativeTitle`                                   | Concise customer-language use case, 5-200 characters.                                                                                                                                                            |
| `businessProblem`                                   | Actual supplied problem and impact; retain corrections and uncertainty. The schema requires at least 40 characters. If no problem was supplied, state that it is unknown rather than filling it from an example. |
| `targetUsers`, `desiredOutcomes`, `successMeasures` | Arrays of supplied information or explicit unknown/proposed statements. Each requires at least one entry; these are not measured results.                                                                        |
| `intakeContext`                                     | All seven keys: `scope`, `exclusions`, `budget`, `timeline`, `systems`, `ownership`, `baseline`. Strings for supplied information, JSON `null` for unanswered details.                                           |
| `submittedBy`                                       | Optional volunteered fictional name; omit rather than asking for one.                                                                                                                                            |
| `constraints`                                       | Optional strings; no assumed budgets, dates, permissions or commitments.                                                                                                                                         |
| `stakeholders`                                      | Optional role-name strings or `{ "role": "...", "authority": "..." }` records. Do not invent authority for a role name.                                                                                          |
| `preservedTerms`, `optionCriteria`                  | Optional arrays of supplied strings only when needed to preserve language or compare options consistently.                                                                                                       |
| `releaseAudience`                                   | Optional nonempty string naming one audience, or a nonempty unique array of supplied role labels. Do not invent recipients or approval authority.                                                                |

The current reference uses `schemaVersion=1.0.0`, `workflowVersion=1.0.0` and `policyVersion=contoso-synthetic-1.0.0`. These are contract metadata, not answers to copy from the example. Use local identifiers such as `CORR-<SYN-initiative-id>` and `local-conversation:<SYN-initiative-id>`. For `requestedAt`, retain an available UTC intake timestamp; otherwise use the engine's captured `startedAt` as local receipt time, not a claimed original message time.

Omit `requirements`, `claims`, `analysisSeed`, `optionDraft`, `designDraft` and `analysisProvenance` from a model-analysis brief. The configured engine authors or records these. Do not write the transcript into the brief; attach the separate validated capture with `--transcript`.

Preserve partial dates, such as `15 October; year unconfirmed`, and unknown baselines. Conversation statements remain assumptions with conversation provenance. Approved synthetic sources do not verify those statements or current product fit, pricing, licensing, travel rules or customer authority.

## Transcript Batch

Persist the available conversation after plan approval, before the analysis call, using one batch rather than per-answer commands. Copy only this intake's actual visible messages and returned native-choice payloads. Do not export editor sessions, reconstruct missing dialogue or let the analysis model author the transcript.

Prepare `build\intake\<SYN-initiative-id>\turns.json` with one property, `entries`, containing ordered turn objects. Each turn has:

- `sequence`: contiguous integer starting at 1.
- `role`: `user` or `assistant`.
- `kind`: `message`, `question`, `answer`, `correction`, `summary`, `generation_plan`, `generation_approval` or `control`.
- `fidelity`: `verbatim` only for exact available text; otherwise `summary`.
- `text`: exact text or JSON `null` for a choice-only response.
- `timestamp`: supplied message timestamp or JSON `null`; no inference from file writes.
- `replyTo`: actual earlier question/plan sequence, or JSON `null`.
- `options`: labels actually offered, or `[]`.
- `selected`: business choices actually selected, or `[]`.
- Optional `context` preserves actual supporting text.
- Optional `optionDescriptions` is a JSON object mapping each exact option label to its exact description, for example `"optionDescriptions": {"Field staff": "Employees who travel regularly."}`. It is not an array.
- Optional `controls` is an array of selected control labels.

Capture whitespace, corrections, unanswered questions and actual reply relationships. A generation control belongs in `controls`, never in selected business answers. Keep the offered `End intake and generate report` label, or its historical `Generate documentation now` spelling, exactly as displayed. Preserve co-selected business answers separately. Natural-language generation requests use `kind=control`. The assistant's exact bounded plan uses `generation_plan`; the user's approval uses `generation_approval` linked to that plan.

Record the opening menu as an assistant `message` with its offered labels in `options`. Record the user's menu choice as a user `control` whose `replyTo` points to that message and whose `controls` contains the exact selected label.

Run:

```powershell
& '.\.venv\Scripts\python.exe' -E -s -B -m mosaic.jobs capture --initiative <SYN-initiative-id> --batch 'build\intake\<SYN-initiative-id>\turns.json' --complete --quiet
```

Use `--complete` only when the entire intake through generation approval is available verbatim with no gaps. Otherwise omit it and supply a concrete `--gap` explanation; summaries and unavailable history remain visibly partial. Never manufacture missing words or backfill them from the brief, examples, model output or another intake.

The engine validates the whole batch before one atomic write. Invalid turns do not partially replace an earlier capture. Identical retries preserve content and timestamps; overwritten, skipped or reordered entries are rejected. A final generation approval closes capture. Later changes require a separate revision. Batches and complete transcripts are limited to 500 entries; exceeding that limit is an actionable failure, not permission to truncate.

For compatibility, capture losslessly canonicalizes a parallel `optionDescriptions` string array only when it has exactly one description for every unique label in `options`. Mismatched, duplicate-label or non-string arrays fail before any transcript write. New batches must use the object form above.

The command writes `build\intake\<SYN-initiative-id>\intake-transcript.json`. `startedAt` and `endedAt` are engine-recorded storage times, not original message times or interview duration; never author them in the batch. This record is local, synthetic and unverified, not authenticated authorship or durable App resume. No model call is made by capture.

The older `--entry` command remains compatible for explicit incremental-recording integrations. It is not the conversational default. Do not place it between interview questions.

## One Synchronous Generation

After capture succeeds, run:

```powershell
& '.\.venv\Scripts\python.exe' -E -s -B -m mosaic.jobs generate --request 'build\intake\<SYN-initiative-id>\brief.json' --transcript 'build\intake\<SYN-initiative-id>\intake-transcript.json' --analyze-with-copilot
```

Use this exact initiative's paths. The engine validates input before inference, makes one bounded call without model tools, validates structured analysis and citations, executes the ordered stages, then publishes an exact report revision. Schema and citation checks do not prove semantic truth.

Stay attached to that execution. If the host backgrounds it, follow its completion notification; do not start another run, poll, sleep or rely on Windows notifications. Share only actual progress. Do not run full regression tests while the requester waits. They belong to development/PR checks.

Use `status <job-id>` or `cancel <job-id>` only for an actual status or cancellation request. `submit` is the older explicitly requested background compatibility path, not the default. The PC and generation process must remain running. No automatic resume or unsolicited callback is promised.

## Completion And Browser Handoff

Before delivery inspect the exact job's `validation-report.json`, `audit-ledger.json`, evidence manifest, three options, blocking questions and release state. A successful job contains 23 files, remains `awaiting_human_review` and has `releaseAuthorized=false`.

Lead with **Your intake report is ready**, its exact clickable report index and **Open documents in browser**. Do not substitute another request's report or a status page. A workspace-file link may open an editor, not a browser.

When `processingStatus=ready`, also provide the separate `processingReportPath` as **Processing cost & pipeline trace (operator report)**. Keep it outside the customer's assessment and do not paste diagnostic events into the business conversation. The engine generates and seals it without another model call; do not reread the full trace or recalculate usage as a routine handoff requirement. App usage, unknown counters and actual billed amounts remain visibly unreported rather than guessed.

On an explicit request to open the operator report, run:

```powershell
& '.\.venv\Scripts\python.exe' -E -s -B -m mosaic.jobs open <job-id> --processing
```

This is also available for a failed or canceled job whose operator records finalized successfully. Older jobs and incomplete/tampered records are not backfilled or presented as verified diagnostics.

If a native selector is callable, offer a completion action with `Documents ready`, `Open your documents in the default browser?`, and choices `Open documents in browser` and `Not now`. Otherwise offer the same action in text. Open only on the user's selection or direct request:

```powershell
& '.\.venv\Scripts\python.exe' -E -s -B -m mosaic.jobs open <job-id>
```

This verifies the report revision and requests the OS default browser; it does not generate, start a server or change file associations. `browser.status=requested` is not evidence of viewing or approval. A browser-launch failure needs only an open retry, not another generation.

## Fault Recovery

The engine retries only recognized temporary local file errors, at most three attempts with bounded delays. It discards incomplete staging output, preserves saved analysis and checks cancellation before publication. Validation, evidence, authorization, integrity and programming failures are not transient faults.

When generation returns `failed`, it has stopped. Read its safe error and, if needed, private `failure.json` once. Explain whether input/analysis were retained and the next action; do not expose diagnostics. Do not search or edit source, schemas or templates, install dependencies or run tests inside the business intake. A programming defect requires a separate engineering repair, not an indefinite "preparing documents" message.

If saved input is available and an operator has corrected the cause, or the user explicitly requests a retry of a temporary assembly failure, use one integrity-checked recovery:

```powershell
& '.\.venv\Scripts\python.exe' -E -s -B -m mosaic.jobs rebuild <failed-job-id>
```

Explain that this preserves the failed job and creates a new report job without a model call. It rechecks snapshots, retained input, source policy, schemas and report gates. Never edit retained answers, evidence or analysis to pass validation. Do not loop over failed rebuilds.

If no validated analysis is retained, a new bounded model call needs fresh approval of its model, credit cap and deadline. Never assume a failed or timed-out call consumed no credits. Authentication requires operator action, not automatic login or provider changes. No automatic paid retries or increased limits.

## Prepared Input And Human Authority

Use prepared-input mode only when explicitly chosen or a complete authored request already exists. It must include evidence-linked requirements and labeled claims, analysis, exactly three comparable options, and an unselected design covering ten dossier areas and seven evidence-linked readiness plans. Run `generate` without the analysis flag. This assembles existing analysis; never call it new inference or an undisclosed fallback.

Architecture selection by an authorized customer role precedes the selected full dossier. Exact-revision design approval is a separate later customer decision. This reference records neither and uses `unselected_discussion_draft`. Reviewer roles do not establish named people, delegated authority or consent. A PR is review evidence, not customer approval.

Plans for verification, interfaces, security, deployment/rollback, operations/adoption and measurement are documentation, not permission to execute them. Unsupported evidence, classification, document requirements, adapter capability or authority must stop visibly. Optional missing business details may remain unknown in a discussion draft. Customer policy can tighten, never weaken, baseline controls.
