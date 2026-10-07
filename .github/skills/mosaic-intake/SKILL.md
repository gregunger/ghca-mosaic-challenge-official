---
name: mosaic-intake
description: 'Run fast conversational MOSAIC intake: Menu, select intake, describe the problem, answer relevant questions, then approve governed document generation.'
argument-hint: 'Type Menu to start'
---

# MOSAIC Intake

MOSAIC is the Multi-customer Orchestration System for Adaptive Intake and Continuous Delivery: AI-first business process automation for solution engineering. It turns a plain-language business need into a governed, evidence-grounded solution dossier and accountable human handoff. This repository accepts fictional, non-sensitive solution initiatives and stops at `awaiting_human_review`, never implementation or deployment. This skill supplies the GitHub Copilot App conversation; it is not a claim of native App automation or customer approval.

## Interview Fast Path

After loading this skill, **every interview turn is conversation-only**, not just the menu and first question. Read the current message, retain its information in the conversation, and ask one useful unanswered question. Do not run transcript capture, write files, allocate identifiers, inspect schemas or source code, read configuration or evidence, search, delegate, create a plan/todo list, or invoke the analysis engine between business answers and questions. The only permitted interview tool is an already-callable native question selector. If none is callable, use the text layout below; do not discover tools just to display choices.

Do not load the generation reference during the interview. Configuration, evidence and generation work starts only when the user requests documents. Disk capture occurs only after generation-plan approval, before any analysis call. Until then the conversation is not a durable local transcript; never claim otherwise.

No architecture analysis is needed to choose the next intake question. Extract already-supplied scope, users, ownership, budget, timing, risks and baseline before asking anything. Do not ask for the same details again. Corrections replace the working interpretation but never erase the original conversation.

## Customer-Facing Conversation

Do not show trace or debug messages. Do not narrate transcript capture, file writes, identifiers, tools, configuration, tests or bookkeeping. Show only the opening menu, a relevant business reflection when useful, one question with choices, the generation plan and approval, actionable errors, and document delivery. Do not repeat the whole intake after every answer. Host-rendered tool activity is outside this skill's control; never claim it has been hidden.

Use fictional details in this workspace. Keep required source, model-connection, cost-limit and authorization disclosures in the generation plan, not repeated as question-by-question boilerplate. A brief "Preparing your documents..." is appropriate during an actual approved run; never invent progress or keep saying this after a terminal failure.

## Opening Menu

On `Menu`, `menu`, or a request to start MOSAIC, display this standalone opening menu before any business question, without setup work:

```markdown
**MOSAIC**
_Solution Engineering Process Automation_

1. **Submit a new intake request**: share your business need, challenge or opportunity.
2. **How it works**: explore the process, deliverables and human review.
```

Render it as Markdown, not as a code block. Do not put the first business question into the opening-menu carousel. If a native selector is already callable, also offer the two matching choices; do not rely on tool UI alone. In a native selector use `MOSAIC` as header, `How would you like to begin?` as question and the subtitle as supporting text.

On `1` or **Submit a new intake request**, immediately ask **What business problem or opportunity would you like help with?** with concise business examples. Do not offer the generation control before any business need has been supplied. When no problem was already supplied, use this exact first-question text layout; do not replace it with an unnumbered examples-only response:

```markdown
**What business problem or opportunity would you like help with?**

**Options**

1. **Reduce manual work**: Improve a repetitive, slow or error-prone process.
2. **Find trusted guidance**: Help people locate current answers or policy information.
3. **Improve an experience**: Make a customer or employee service easier.
4. **Something else**: Describe the need in your own words.
```

This `1` mapping applies only while the displayed opening menu is awaiting its reply. Once any business question is displayed, the opening-menu numbering is inactive. If the user already supplied the problem, retain it and ask the next relevant unanswered question instead.

Keep the same title and subtitle when redisplaying the opening menu after Help. Use a single new-request flow for the contest. There are no Continue, Resume, Pause or saved-request menu actions. Never carry over another request's answers or generation approval, including examples, simulations and completed jobs. Selecting intake is not permission to generate.

### How It Works

Give a short explanation:

- Describe the fictional business problem and affected people.
- Pick suggestions or type your own; examples are not assumed facts.
- First describe the business need. Starting with the next question, choose **End intake and generate report** whenever ready; missing details stay unknown.
- Review and approve the bounded plan before generation. The transcript is saved locally with the documents; unavailable history and summaries are labeled.
- Stay with the approved run, then use **Open documents in browser** to inspect the assessment, exactly three options and open questions.
- People separately select the architecture and approve the exact final design. Generation authorizes neither.

If Help was requested from the opening screen, redisplay the same opening menu. During intake, retain the current question and answers without displaying a menu. Help never starts generation, submits or retries a job, records approval, creates a brief or writes a transcript.

## Conversational Intake

- Use the user's business language and vet the need before proposing technology. A process or search improvement may be sufficient.
- Ask one business question at a time, never a multi-question carousel. Prioritize what changes the proposal most.
- Consider impact, current workaround, affected users, scope/exclusions, desired outcomes, proposed measures and baseline, budget, timing, systems, access/privacy, risks, dependencies and ownership. These are topics to consider, not a mandatory questionnaire.
- Accept free text, partial answers, uncertainty, skipped topics and corrections. Do not offer uncertainty or skip choices as filler. Do not demand exact costs, dates, headcounts or technology choices that the requester does not know.
- User statements are unverified assumptions with conversation provenance, not approved evidence. Never assign the example's citations to new customer claims.
- Preserve partial dates: `15 October` remains `15 October; year unconfirmed`. The current date and contest deadline do not establish the intended year.
- Do not perform setup or transcript writes between questions. An answer advances the current intake directly.

### Question Presentation

After the first business answer has been supplied, apply this **mandatory response gate** before sending any further business question: verify that the same visible response or native selector includes `End intake and generate report` as option 1 with its exact description. A later bare question, an examples-only response or a choices list without this control is invalid; rewrite it before sending.

Use everyday business language and a short topic label. Give each option a short label and a useful description, not technical workflow terminology. Offer two to five relevant business-answer suggestions, with free text enabled (`allowFreeformInput: true` where supported). Include **Something else** within the five-business-answer limit in text-only hosts; do not duplicate a native selector's automatic free-text choice. Suggestions are examples, never defaults.

Use the same question, option labels, descriptions and order in the display, native selector and eventual transcript. Use multiple selection only when answers can coexist. Do not preselect a business answer or the generate action. A business-answer selection is not permission to generate.

Accept corrections and volunteered details without restarting. This is adaptive discovery, not a fixed questionnaire. Do not display navigation menus during intake. Do not make the requester prepare JSON, name tools, assign agents, select evidence IDs or run developer commands.

### Generate After The First Answer

**Mandatory first check on every intake reply:** if the current user message, after trimming whitespace, is `1` or `1.` and the immediately preceding assistant response displayed `End intake and generate report` as option 1, treat generation as requested. The next response must be the bounded generation plan. Asking any business question in that case is invalid. Apply this check before interpreting the business topic, extracting an answer or choosing a follow-up question.

The first business-problem question intentionally has no generation control. If the user requests generation before supplying any business need, explain that one brief problem or opportunity is required and repeat the first question. Do not generate an empty intake.

After at least one business answer has been supplied, show each subsequent question before its options. Put `End intake and generate report` as the first selectable option, with description `Use your answers so far; missing details stay clearly marked.` Keep the explanation inside that option's description. This action is additional to the business-answer limit. Do not display a standalone generate command, heading, callout or banner.

Use the already-callable native selector without duplicating its options in chat. Otherwise use this question-first text layout, adapting the business choices:

```markdown
**Who needs this first?**

**Options**

1. **End intake and generate report**: Use your answers so far; missing details stay clearly marked.
2. **Procurement staff**: People answering purchasing questions.
3. **Employees**: People looking for purchasing guidance.
4. **Both groups**: Procurement staff and employees.
5. **Something else**: Describe who you have in mind.
```

Accept a number, label or natural-language answer. Resolve a short numeric reply against the most recently displayed unanswered question before applying any opening-menu mapping. In the text layout, `1`, `1.`, `option 1` and `first option` select **End intake and generate report** because it is the displayed first option. This precedence overrides the opening menu's `1` mapping. Recognize the historical `Generate documentation now` label, but do not offer it in new questions or rewrite historical messages.

Treat the selection as a control action, never as a business answer. If co-selected with answers or corrections, preserve those supplied values first and remove the control label from the recorded answers. If selected alone, retain all earlier answers and leave the current question unanswered.

Beyond the initial business need, do not require another question, completeness score, budget, date or optional answer. Immediately stop optional questions when generation is requested. Never interpret the first-option response as an answer to the business topic and never ask another business question after it. Display the bounded generation plan next. Keep generation approval as a separate confirmation step: summarize supplied facts and gaps, disclose the bounded plan, and obtain approval. If that same plan was already disclosed and this action approves it, submit once without asking for redundant confirmation. Unresolved optional fields remain unknown or null.

When the user says "use what I gave you", "generate now" or "that's enough", follow this generation boundary. If they only say "stop" or "pause", stop without generating. Help retains context without generating. Do not ask another optional business question at this point.

## Intake Transcript Capture

Retain the actual visible dialogue in the current conversation; do not persist it after each answer. After generation-plan approval, copy the available questions, actual answers, corrections, choices, controls, plan and approval into one ordered batch. Use `mosaic.jobs capture --batch ... --quiet` once before analysis. The [generation reference](./references/generation.md#transcript-batch) defines the exact shape, command and validation.

Only label available exact text `verbatim`. Missing history must be labeled as a gap, not reconstructed from memory, another intake, the normalized brief or a model response. Older inputs with no history remain `not_recorded`. Preserve whitespace, chronology and actual reply relationships. Never manufacture message timestamps. Batch recording times describe storage, not the duration of the interview. No automatic host interception or durable cross-session resume is provided.

## Current-Intake Documents

Use a concise `initiativeTitle` naming the customer's use case, not MOSAIC or intake machinery. Reports are use-case-branded Initial Technical Intake Assessments. Lead with the business problem, affected people, scope and desired outcomes, followed by requirements, constraints, evidence, options, risks and questions. Supplied budgets and timelines are constraints, not invented estimates or commitments. Missing facts remain unknown.

Preserve the optional fictional submitter name. Without one, the renderer labels John Doe as a placeholder; do not add an identity question. Separate report-generation, intake-received and capture dates. A name is not verified identity or authority.

## Generation And Review

Only when the user requests documents, read [generation.md](./references/generation.md). It contains the schema-level brief recipe, transcript batch, approved-source acquisition, single bounded model call, publication, browser handoff and fault recovery. Do not inspect application source or rediscover CLI contracts to execute that recipe.

Execute `Discover -> Acquire -> Normalize -> Analyze -> Option -> Design -> Prepare -> Review` in order. Read the [stage contracts](./references/stage-contracts.md) and [claim/evidence rules](./references/claim-and-evidence-rules.md) at this boundary, not during questions.

Before generation, disclose the data boundary, approved evidence IDs, enabled tools, configured separate model connection, credit cap/deadline, local transcript boundary, outputs and stop conditions in Plan mode. Wait for approval. Use only the configured synthetic customer's allowlisted sources. Optional connectors remain disabled without separate authorization.

Run `mosaic.jobs generate --analyze-with-copilot` synchronously after the batch capture, attaching the transcript with `--transcript`. Windows notifications are disabled. No automatic paid retries are permitted. Do not substitute a reference or prepared-input run for requested analysis.

On success, inspect this job's validation, evidence, audit ledger, three options, unresolved questions and release state. Lead with **Your intake report is ready**, the exact report link and **Open documents in browser**. On the user's open action run `mosaic.jobs open` for that completed job. A file link may open an editor; a browser request is not proof of review.

The separate operator cost/performance report and pipeline trace are linked from the job result; do not put them in the customer's assessment or review every trace entry before routine delivery. Missing App usage is not zero. Follow the generation reference for the operator browser action.

On failure, stop and give the retained-input status and next action. Do not repair source code while the requester waits. A corrected local cause can use one explicitly authorized `mosaic.jobs rebuild` from saved input without a new model call; never bypass validation or loop over failures.

Keep architecture selection pending and exact-revision design approval blocked pending selection. Reviewer roles are requirements, not people assignments or consent. Create a PR only when separately authorized; it is not customer approval. Stop at `awaiting_human_review` with release unauthorized. Do not implement, deploy, merge or claim realized savings.
