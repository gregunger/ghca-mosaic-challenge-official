# Notices And Attribution

## Original Work

The MOSAIC contest edition's workflow design, eight-stage orchestration, synthetic scenario, schemas, evidence controls, renderers, prompts, agents, skill, documentation, deck, and video production package were prepared as original work by Greg Unger in 2026.

No customer source document, customer screenshot, real work item, credential, tenant identifier, or restricted challenge source file is distributed in this repository.

First-party code headers use `SPDX-License-Identifier: LicenseRef-MOSAIC-Evaluation` to reference the existing [internal evaluation notice](LICENSE). This identifier is not a new license grant or a statement of intellectual-property ownership. Package metadata likewise identifies restricted evaluation use; it must not be read as permission for external distribution. Generated documents are attributed to MOSAIC, while submitter display names remain explicitly unverified.

## Third-Party Components

| Component                           | Project                                            | License                                                          | Use                                                                                                 |
| ----------------------------------- | -------------------------------------------------- | ---------------------------------------------------------------- | --------------------------------------------------------------------------------------------------- |
| Python                              | https://www.python.org/                            | Python Software Foundation License                               | Runtime                                                                                             |
| jsonschema                          | https://github.com/python-jsonschema/jsonschema    | MIT                                                              | JSON Schema validation                                                                              |
| json5                               | https://pypi.org/project/json5/                    | Apache-2.0; upstream benchmark data retains its separate notices | Parse the dedicated Copilot CLI's JSON-with-comments configuration; no benchmark data is copied     |
| rfc3339-validator                   | https://github.com/naimetti/rfc3339-validator      | MIT                                                              | JSON Schema UTC date-time checking                                                                  |
| Jinja2                              | https://github.com/pallets/jinja                   | BSD-3-Clause                                                     | Autoescaped shared HTML report and job templates                                                    |
| markdown-it-py                      | https://github.com/executablebooks/markdown-it-py  | MIT                                                              | Structured Markdown parsing for report sections and contest acceptance tables                       |
| Lucide                              | https://github.com/lucide-icons/lucide             | ISC; MIT for Feather-derived icons                               | Vendored offline report icons; full notices in [templates/lucide-LICENSE](templates/lucide-LICENSE) |
| Windows-Toasts                      | https://github.com/DatGuy1/Windows-Toasts          | MIT                                                              | Optional Windows desktop notification adapter; WinRT bindings retain their licenses                 |
| pytest                              | https://github.com/pytest-dev/pytest               | MIT                                                              | Test runner                                                                                         |
| PyYAML                              | https://pyyaml.org/                                | MIT                                                              | Parse agent and prompt frontmatter in development contract tests                                    |
| MCP Python SDK                      | https://github.com/modelcontextprotocol/python-sdk | MIT                                                              | Local read-only MCP server                                                                          |
| PptxGenJS                           | https://github.com/gitbrent/PptxGenJS              | MIT                                                              | Reproducible challenge deck generation                                                              |
| image-size                          | https://github.com/image-size/image-size           | MIT                                                              | Native image dimensions and aspect-ratio preservation                                               |
| Playwright Test                     | https://github.com/microsoft/playwright            | Apache-2.0                                                       | Headless report capture and responsive presentation checks                                          |
| axe-core and Playwright integration | https://github.com/dequelabs/axe-core-npm          | MPL-2.0                                                          | Automated report accessibility checks; not a certification                                          |
| ffprobe-static                      | https://github.com/joshwnj/ffprobe-static          | MIT wrapper; bundled FFmpeg binary licenses apply                | Local media metadata inspection                                                                     |
| Ruff                                | https://github.com/astral-sh/ruff                  | MIT                                                              | Python linting and formatting                                                                       |
| Prettier                            | https://prettier.io/                               | MIT                                                              | Consistent formatting of maintained documentation, configuration and browser assets                 |
| GitHub Actions                      | https://github.com/actions                         | Individual action licenses                                       | CI checkout, runtime setup, and artifact retention                                                  |

Dependencies and their transitive components retain their respective licenses and notices. This table records use; it does not replace the license texts shipped by those projects.

The current raw contest recording uses the entrant's own narration; it is not synthetic speech or a voice clone. No recording is sent to an online transcription service during repository validation. Bahnschrift and desktop PowerPoint are installed production tools; font files, application binaries, dependency binaries and raw speech caches are not distributed in this repository. Output-media publication remains subject to the applicable rights and competition rules.

## Product References

GitHub, GitHub Copilot, Microsoft, and Claude Code are referenced to describe workflow interoperability and documented product capabilities. Public competition stories are attributed in the [competition audit](submission/competition-audit.md); they are not MOSAIC outcome evidence. All trademarks belong to their respective owners.

## Publication Gate

External redistribution requires confirmation of ownership, the appropriate internal or public release approval, dependency review, and a license suitable for the chosen visibility. This does not assume the competition requires a public open-source repository. See [LICENSE](LICENSE) and [the remaining actions](submission/OPEN-ITEMS.md).
