# Contributing To MOSAIC

MOSAIC is AI-first business process automation and orchestration for solution engineering. This guide covers the maintained GitHub Copilot App contest reference that automates preparation from business intake through governed dossier generation and human-review handoff. Start with the [README](README.md), [repository instructions](.github/copilot-instructions.md), and [security policy](SECURITY.md). A passing build supports human review; it does not approve the contest submission, a customer architecture, implementation, deployment, or release.

## Development Setup

Use an editable checkout, Python 3.12 or later, and Node.js 22 or later. The Python package locates schemas, templates and examples relative to the repository; a standalone wheel is not the supported runtime.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev,mcp]"
npm ci
npx playwright install chromium
```

On macOS or Linux, activate with `source .venv/bin/activate`. The optional `.[windows]` extra is needed only for the explicitly requested notification compatibility path. The default offline reference needs no account, model call or customer connection.

Live analysis is separate: an operator must configure and authenticate the dedicated Copilot CLI profile and approve its displayed model, credit cap, deadline and data boundary. Tests must not spend credits, trigger sign-in, widen tool access or retry inference automatically.

## Workspace Map

| Location                  | Maintained responsibility                                                           |
| ------------------------- | ----------------------------------------------------------------------------------- |
| `src/mosaic/`             | Runtime contracts, orchestration, validation, bounded model adapter and local jobs  |
| `src/mosaic/connectors/`  | Read-only approved-evidence acquisition                                             |
| `src/mosaic/stages/`      | The eight ordered workflow stages                                                   |
| `tests/`                  | Behavioral, security-boundary and regression tests                                  |
| `schemas/`                | Versioned request, configuration, evidence and package contracts                    |
| `templates/`              | Report views, offline assets and preserved third-party notices                      |
| `config/`                 | Synthetic customer configuration and policy examples                                |
| `examples/synthetic/`     | Reusable reference inputs, source evidence and generated canonical output           |
| `.github/`                | Workflow instructions, agents, skill, prompts, issue/PR templates and CI            |
| `scripts/`                | Local demonstration and validation entry points                                     |
| `docs/`                   | Architecture, governance, adoption, evaluation and operating guidance               |
| `mcp/`                    | Portable read-only MCP setup guidance                                               |
| `submission/`             | Contest requirements, evidence status and owner-controlled submission text          |
| `presentation/`, `video/` | Current contest presentation sources, generated deck formats and narrated media     |
| `build/`                  | Ignored local jobs, reports, captures, validation results and private configuration |

Installed dependencies, bytecode, test caches and editable-install metadata are ignored and hidden in the shared Explorer settings. They are not source artifacts. Keep the current published intake path stable; do not move or rewrite completed report revisions to tidy the tree.

## Source Standards

- Use UTF-8, the line endings in [.editorconfig](.editorconfig), four-space Python indentation and two-space JavaScript/JSON/YAML indentation. Preserve the CRLF bytes of the approved synthetic source documents.
- Use Ruff for Python and the pinned Prettier version for maintained Markdown, JSON, YAML, JavaScript and CSS. Markdown prose remains paragraph-based; intentional hard line breaks are preserved.
- Give Python modules and test modules a short purpose docstring. Give executable scripts and browser assets an equivalent file overview. Document non-obvious public contracts and security-sensitive behavior, not each assignment.
- Use descriptive names. Keep comments focused on why a boundary, retry, ordering rule or escaping decision exists. Avoid decorative banners, repeated author blocks, commented-out code and change histories inside source files.
- Reference the existing evaluation terms with `SPDX-License-Identifier: LicenseRef-MOSAIC-Evaluation` in first-party code headers. This identifier maps to [LICENSE](LICENSE); original-work and dependency attribution remains in [NOTICE.md](NOTICE.md). It grants no additional rights. Preserve third-party notices unchanged and do not invent ownership, contributors or approvals.
- Keep JSON files valid JSON. Do not add comments or attribution fields to requests/configuration that their schemas do not permit. Generated reports and vendored assets retain their own generation or third-party attribution.
- Preserve public contracts and supplied intake values. Keep report-generation time separate from the supplied intake timestamp and transcript-capture start/end times. A display name, including the John Doe default, is not verified identity or customer authority.

## Formatting And Checks

```powershell
python -m ruff format src tests scripts
npm run format
python -m ruff check .
python -m ruff format --check src tests scripts
npm run format:check
python -m pytest
python -m mosaic.cli --output build/validation/reference
npm run test:reports -- build/validation/reference
python scripts/validate_submission.py --output build/validation/readiness-report.json
```

The formatter excludes private output, approved source bytes, generated canonical reports, vendored icon data and held presentation/media files. Do not bypass those exclusions for cosmetic changes. Run a focused test immediately after a behavioral edit; run the full gates once the changed areas are ready. Do not rebuild presentations or call the live model merely to validate documentation or formatting.

The two optional installed-Copilot tests use a local fake provider, not paid inference. To include them, set `MOSAIC_TEST_COPILOT_EXE` to the operator's installed native executable for that test process only. A Windows environment without unprivileged symlink support skips the corresponding real-symlink test; report that skip honestly.

## Canonical Reference Outputs

The fixed reference consists of 23 files: ten HTML pages, nine Markdown reports and four JSON records. Regenerate it from source, never by editing its HTML or JSON by hand:

```powershell
python -m mosaic.cli --output examples/synthetic/expected
python scripts/validate_submission.py --output build/validation/readiness-report.json
```

Review the complete generated diff. The canonical validator reuses only the reference's recorded report-rendering time in a disposable comparison run; it still compares every output byte. Live generation continues to record the real current time. A reference without captured conversation history must say `not_recorded`, not manufacture a transcript.

Never use canonical regeneration to overwrite a conversational job, its sealed input, evidence, transcript or published revision. A requested local report refresh must create a new revision from verified retained analysis; new paid inference needs its own approved plan.

## Workflow Customizations

Edit the owning layer and keep the entry points consistent:

- [.github/copilot-instructions.md](.github/copilot-instructions.md): repository-wide safety, mission, workflow and review requirements.
- [.github/skills/mosaic-intake/SKILL.md](.github/skills/mosaic-intake/SKILL.md): the conversation, capture, generation and delivery contract.
- [.github/agents/](.github/agents/): bounded roles and allowed tools, not invented platform capabilities.
- [.github/prompts/](.github/prompts/): focused entry points that reuse the skill rather than duplicating its procedure.

Preserve YAML frontmatter at the beginning of customization files. Keep question choices descriptive, the end-intake control alongside business answers, successful capture quiet, and generation approval separate from customer decisions. Test the applicable instruction contract after changes.

## Review And Publication

Use the [pull-request template](.github/pull_request_template.md) to state the change, evidence, tests, remaining unknowns and required human decisions. Do not commit unrelated local output, credentials, protected screenshots or another intake's data. Do not erase existing work or rewrite history during cleanup.

CI checks are engineering evidence, not an enforced customer approval workflow or proof of branch protection. Architecture selection and exact-revision dossier approval remain with authorized customer roles; the reference stops at `awaiting_human_review` with release disabled.

The [submission checklist](submission/OPEN-ITEMS.md) tracks every contest requirement with a passed, pending or blocked state. Local validation surfaces incomplete rows as required follow-up; `--release` fails while any remain unresolved. A declared passed row is not independently verified customer or organizer approval. Presentation work stays on hold until explicitly released. Repository visibility, rights clearance, final submission and release are owner actions, not consequences of passing local checks.
