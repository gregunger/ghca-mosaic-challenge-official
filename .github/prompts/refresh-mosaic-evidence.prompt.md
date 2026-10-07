---
name: 'Refresh MOSAIC Evidence'
description: 'Plan a deterministic MOSAIC rerun after an approved synthetic source, policy, prompt, or workflow version changes.'
argument-hint: 'Identify the changed source or version'
agent: 'plan'
tools: [read, edit, search, execute]
---

Compare the current evidence manifest and package with the approved change.

1. Verify that the changed source remains allowlisted and release-safe.
2. Identify affected claims, requirements, risks, options, design elements, and artifacts.
3. Propose a bounded rerun plan and wait for approval.
4. After approval, regenerate outputs, run tests and validation, and summarize semantic changes.
5. Preserve the prior run; never rewrite its audit record.
6. Return the new package to `awaiting_human_review` even if all checks pass.
