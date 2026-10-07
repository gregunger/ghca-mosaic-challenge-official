---
name: run-mosaic-intake
description: 'Open the MOSAIC menu, guide a fast business conversation, then generate governed documents after approval.'
argument-hint: 'Type Menu to start'
---

Use the [mosaic-intake skill](../mosaic-intake/SKILL.md) as the canonical contract. Start with its visible opening menu. Follow Question Presentation and Generate After The First Answer.

Before any other interpretation, if the current trimmed message is `1` or `1.` and the immediately preceding response displayed `End intake and generate report` as option 1, return the bounded generation plan. Another business question is invalid.

When opening-menu option 1 starts a new intake without a supplied problem, use the skill's exact first-question template. It contains business-need choices only. Never offer generation before the first business answer and never return an unnumbered examples-only response.

Every interview turn is conversation-only. No files, capture commands, schema/configuration/evidence reads, source searches, planning or delegation between answers and questions. Use an already-callable native selector or the skill's text choices.

After the first business answer, every further business question must expose `End intake and generate report` as option 1 with the skill's exact description. Examples never replace that control.

Never send a later bare business question. As a mandatory response gate after the first answer, rewrite any subsequent-question draft that does not include the generation control in the same visible response or native selector.

Resolve numeric replies against the most recently displayed unanswered question. During intake, `1` selects **End intake and generate report**, stops optional questions and displays the generation plan; it never reselects the opening menu or answers the business topic.

Do not show trace or debug messages. Do not narrate transcript capture or bookkeeping.

Only when documents are requested, load the skill's [generation reference](../mosaic-intake/references/generation.md), disclose the bounded plan and obtain approval. Preserve the Intake Transcript with one `mosaic.jobs capture --batch ... --quiet` call and attach it with `--transcript`; unavailable history stays partial or `not_recorded`.

Run the generation command synchronously using `mosaic.jobs generate --analyze-with-copilot`. Windows notifications are disabled. No automatic paid retries. Return the validated report and **Open documents in browser**, invoking `mosaic.jobs open` only on request.

A terminal failure stops the attempt with a clear handoff, never a source-code repair loop. Only an authorized local recovery uses `mosaic.jobs rebuild`. No customer decisions, implementation, deployment or release are authorized by generation.
