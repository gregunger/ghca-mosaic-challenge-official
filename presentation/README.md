# Challenge Deck

The deliverable is a three-slide, 16:9 deck:

1. **MOSAIC** - lead with the workflow architecture: business user, GitHub Copilot App, governed analysis, 23-file dossier and retained human decisions.
2. **One governed flow, proven in the App.** - show authentic frames from the current contest recording: adaptive intake in GitHub Copilot App and the generated travel-policy dossier awaiting human review. Separate customer architecture selection from later exact-revision design approval.
3. **Adoption motion and expected value.** - explain the synthetic-proof-to-governed-scale adoption path, customer-specific reports and controls, the 96-hour manual baseline, 16-hour retained review, 80-hour / 83% effort opportunity, $16,000 gross capacity per request and illustrative $1.6M annual scale.

The mission is to help Microsoft deliver better solutions to more customers with less repeated work. MOSAIC automates the governed business process from plain-language need through adaptive intake, approved evidence, structured analysis, three options, proposed design, delivery-readiness planning, validation and human-review handoff. The dossier is the durable process output, not the product definition. This provider-neutral system is represented here by its GitHub Copilot App contest implementation. The [economic assumptions and sensitivity](../docs/evaluation-plan.md#planning-economics) are not measured outcomes, cash savings or workload forecasts. Customer selection and exact-revision dossier approval remain unrecorded. Executing code, tests of the designed solution, rollout, training or handover requires separate future authority. This project does not establish compliance or superiority to another product.

## Readability

Each slide makes one main point in ordinary language. A viewer should understand the business problem, workflow architecture, inputs, automated process, outputs, human authority, adoption model, customization and value without speaker notes. Bahnschrift typography, neutral backgrounds, cyan/coral/yellow accents and full-width emphasis bands support that hierarchy. PowerPoint body text is at least 20 points except for image captions and compact workflow labels. Text does not shrink automatically to fit. The authentic evidence is preserved; the recording frames are cropped but not recreated or enhanced into invented content.

The current App and report frames use ordinary business language. UNK in supporting reports means an unknown. Use the definitions below when discussing technical supporting files. Do not read code identifiers or an unexplained list of initials aloud.

The [published 2 minute 55.57 second workflow video](https://youtu.be/RP4CeCYt4VE) was produced
from the authentic recording retained under the ignored `video/recordings/` workspace. The deck
uses two lossless crops from that recording.

## Plain-Language Glossary

### Names And Screen Labels

| Term | Plain meaning |
| --- | --- |
| MOSAIC | Multi-customer Orchestration System for Adaptive Intake and Continuous Delivery. AI-first business process automation and orchestration for solution engineering; this reference automates preparation through human-review handoff, not delivery execution. |
| App | Application: a software program. Here it means the GitHub Copilot App. |
| Skill | Saved instructions that an assistant can use for a particular task. |
| EVD | Evidence. An EVD label identifies an approved information source. |
| ID | Identifier: a label that distinguishes one item from another. |
| UNK | Unknown: a question that still needs an answer. |
| SYN | Synthetic: a fictional example, not real customer data. |
| Read-only | A tool can look at information but cannot change it. |
| Human review | A qualified person checks the work and makes the decision; an automated check cannot approve it. |

### Engineering And Review

| Term | Full name and plain meaning |
| --- | --- |
| AI | Artificial intelligence: software that can perform tasks such as generating text. Its output still needs checking. |
| MCP | Model Context Protocol: a standard way for an assistant to connect to tools and data. |
| SDLC | Software development lifecycle: the work from an initial idea through design, building, testing, release, and support. |
| IaC | Infrastructure as code: files that describe how to set up servers, networks, and other technology resources. |
| API | Application programming interface: a defined way for one program to request information or actions from another. |
| CLI | Command-line interface: running a tool by typing a command. |
| PR | Pull request: a proposed set of changes that other people can review before it is added to the shared project. |
| CI | Continuous integration: automated checks run when people propose or combine code changes. |
| QA | Quality assurance: planned checks that the work meets agreed expectations. |
| Repository | The shared project files and their change history. |
| Pipeline | A sequence of automated steps, such as building, testing, and releasing software. |
| Acceptance test | A check that the result does what its intended users need. |
| Runbook | Written steps for operating a service or handling a problem. |
| Prewritten analysis | The example's conclusions are prepared in advance so the same checks can be repeated; this is not proof of reasoning about any new request. |

### Standards And Guidance

| Term | Full name and plain meaning |
| --- | --- |
| SOC 2 | System and Organization Controls 2: an independent examination of a service organization's controls, performed by a qualified accountant. MOSAIC does not provide that examination. |
| NIST | National Institute of Standards and Technology: the United States standards body that publishes guidance, including security and artificial-intelligence risk frameworks. The customer must choose the applicable publications. |
| ITIL 4 | Information Technology Infrastructure Library, version 4: guidance for managing technology services. Using its practices is not a certification of MOSAIC. |

These are possible customer-specific alignment targets, not a claim that MOSAIC or its output is compliant. See the [standards mapping](../docs/governance-and-rai.md#standards-mapping) for scope and official sources.

### Files And Verification

| Term | Full name and plain meaning |
| --- | --- |
| HTML | HyperText Markup Language: the format used for the browser version of the slides and report. |
| CSS | Cascading Style Sheets: rules that control a web page's appearance. |
| PDF | Portable Document Format: a fixed-layout version for viewing and sharing. |
| PPTX | The file extension for a modern PowerPoint presentation. |
| PNG | Portable Network Graphics: the lossless image format used for the screenshots. |
| JSON | JavaScript Object Notation: a text format for named values that software can read. |
| SHA-256 | Secure Hash Algorithm with a 256-bit result: a file fingerprint used to detect changed bytes. It does not prove the content is true. |

## Build

From the repository root:

```powershell
npm ci
npx playwright install chromium
npm audit --audit-level=high
npm run capture:report
npm run build:deck
npm run test:presentation
npm run export:deck
python scripts/validate_submission.py
```

[The deck generator](build_deck.js) produces [the PowerPoint deck](mosaic-challenge-deck.pptx) and [HTML companion](mosaic-challenge-deck.html) from one shared story. On Windows, `npm run export:deck` runs the [native PowerPoint exporter](../scripts/export_presentation.ps1), checks text and image bounds, updates [the PDF deck](mosaic-challenge-deck.pdf), and renders 1280 by 720 plus 3840 by 2160 frames. It requires desktop PowerPoint and closes only the presentation it opened. HTML supports `?slide=1`, `?slide=2`, or `?slide=3`; desktop is 16:9 and smaller screens reflow.

The report capture comes from the real generated report, not a mock dashboard. The browser capture script verifies its actual viewport and pixel ratio before producing [mosaic-output.png](mosaic-output.png). Presentation checks cover word counts, text size, image loading, horizontal overflow, overlapping sections, text width, viewing one slide at a time, and JavaScript errors at 1440, 1024, 768, and 390 pixels. PowerPoint checks cover actual text bounds and text overlapping images. Outputs are retained under the ignored build directory. These checks supplement visual and human privacy review; they do not prove universal accessibility or judge access.

Authentic GitHub Copilot App captures belong under [the asset directory](assets/) with names beginning `copilot-app-`; do not substitute a mock interface. Slide 2 uses the lossless detail and links to the unchanged original in HTML, as described in [the capture provenance record](assets/README.md). Both App assets and the report image used by the media package are required inputs; missing images fail the build.

The capture proves only that the local application loaded saved instructions and used the approved-source tools. An online request, complete planning session, proposed code changes, and reviewer corrections have not been captured; the refreshed deck does not claim they have. The configured flow and current 23-file reference are separately reproducible.

## Contest Delivery

The supplied rules require a 1-3-slide deck showing the workflow architecture or flow and relevant App screenshots, with proper file access. The current three-slide revision is built and locally verified from the 23-artifact workflow. The entrant has resolved the disclosure concern and retains final media and judge-access review. No separate contest approval form or public-license change is required. See [the scoring priorities and remaining steps](../submission/OPEN-ITEMS.md).
