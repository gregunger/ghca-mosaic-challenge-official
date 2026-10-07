# SPDX-License-Identifier: LicenseRef-MOSAIC-Evaluation
"""Offline, templated reports from the same records used by the Markdown package."""

from __future__ import annotations

import html
import json
import re
from collections import Counter
from datetime import UTC, datetime
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from xml.etree import ElementTree

from jinja2 import Environment, FileSystemLoader, StrictUndefined, select_autoescape
from markdown_it import MarkdownIt
from markupsafe import Markup

from mosaic.models import WorkflowResult
from mosaic.transcript import missing_transcript, transcript_turns

TEMPLATES = Path(__file__).resolve().parents[2] / "templates"
REPORTS = (
    (
        "index",
        "Initial Technical Intake Assessment",
        "Start with the operator's use case, business problem, scope, affected users and desired outcomes.",
    ),
    (
        "intake-report",
        "Use Case Detail",
        "Review the business need, scope, requirements, measures, risks and open questions.",
    ),
    (
        "intake-transcript",
        "Intake Transcript",
        "Review captured questions, answers, corrections and generation approval.",
    ),
    ("option-matrix", "Solution Options", "Compare three approaches against the same criteria."),
    (
        "architecture-brief",
        "Design & Readiness",
        "Inspect the proposed design and delivery questions.",
    ),
    ("evidence-appendix", "Evidence & Claims", "Trace claims to approved, versioned sources."),
    (
        "human-review",
        "Decisions & Review",
        "See what remains with authorized human decision-makers.",
    ),
    ("meeting-request", "Discussion Brief", "Bring the right people to the next decision."),
    ("meeting-agenda", "Meeting Agenda", "Allocate the discussion to outcomes and decisions."),
    ("talk-track", "Facilitator Notes", "Prepare questions and a consistent discussion sequence."),
)
REPORT_GUIDANCE = {
    "index": {
        "definition": "An initial technical intake assessment centered on the operator's use case.",
        "problem": "The customer's problem, affected users, scope, desired outcomes, constraints and unresolved questions must be clear before solution selection.",
        "workingOutput": "Align business and technical reviewers on the use case and the evidence needed for the next decision.",
    },
    "intake-report": {
        "definition": "The detailed business and technical intake for this use case.",
        "problem": "The team needs a shared view of the customer's current problem, users, scope, requirements, constraints, risks and missing information.",
        "workingOutput": "Correct the intake record and resolve the questions that materially affect solution fit and effort.",
    },
    "intake-transcript": {
        "definition": "The available request conversation and corrections for this use case.",
        "problem": "The assessment can drift from the operator's intent when original wording, corrections or missing history are not visible.",
        "workingOutput": "Compare the assessment with the available request record and correct any misinterpretation.",
    },
    "option-matrix": {
        "definition": "Three alternative ways to address this business problem, compared on the same criteria.",
        "problem": "A technology preference can outrun the use case when alternatives, tradeoffs, prerequisites and disqualifiers are not compared consistently.",
        "workingOutput": "Determine which option merits deeper validation and what evidence could change that conclusion.",
    },
    "architecture-brief": {
        "definition": "A proposed technical direction for this use case, including responsibilities, boundaries and delivery considerations.",
        "problem": "A high-level concept can appear viable while omitting interfaces, verification, security, deployment and operating requirements.",
        "workingOutput": "Test the proposed direction against the customer's requirements and identify what must be decided before design completion.",
    },
    "evidence-appendix": {
        "definition": "The sources and claim traceability supporting this use-case assessment.",
        "problem": "Business and technical conclusions are difficult to challenge when their source basis, assumptions and unknowns are not visible.",
        "workingOutput": "Confirm which conclusions are supported, which remain assumptions and what customer evidence is still needed.",
    },
    "human-review": {
        "definition": "The unresolved business and technical decisions for this use case.",
        "problem": "The customer cannot select a responsible path while material evidence, ownership, security or operating questions remain open.",
        "workingOutput": "Resolve or explicitly defer the blocking questions, then record the customer's architecture decision and later design approval.",
    },
    "meeting-request": {
        "definition": "A proposed working-session brief for the people needed to advance this use case.",
        "problem": "The business problem will remain unresolved if the right owners arrive without a shared scope, evidence request or decision objective.",
        "workingOutput": "Bring the right customer roles together with the information needed to resolve the highest-priority questions.",
    },
    "meeting-agenda": {
        "definition": "A time-boxed working plan for resolving this use case's scope, evidence and option questions.",
        "problem": "An unstructured discussion can consume the session without improving the customer's problem definition or decision readiness.",
        "workingOutput": "Leave with corrected scope, explicit decisions or deferrals, and customer-owned evidence actions.",
    },
    "talk-track": {
        "definition": "Facilitator prompts for discussing this specific business problem and its solution choices.",
        "problem": "The discussion can drift into generic technology claims instead of testing the customer's needs, assumptions, risks and decision criteria.",
        "workingOutput": "Keep the session anchored to the customer's use case and confirm only the decisions and actions actually agreed.",
    },
}
SECTION_HELP = {
    "Original Request": "The business problem as supplied for this intake. Use it as the reference point when checking whether the assessment preserves the requester's intent.",
    "Executive Summary": "A concise technical interpretation of the use case, affected users, desired outcomes and decision context. Correct it before evaluating solution fit.",
    "Business Problem": "The problem this initiative should solve. Check the framing before choosing technology.",
    "Target Users": "The people affected by the problem. Use this to set first-release scope and adoption needs.",
    "Desired Outcomes": "The changes the business wants. These outcomes guide comparisons; they are not achieved results.",
    "Success Measures": "Proposed ways to test usefulness. Confirm the baseline, target and accountable owner before treating them as commitments.",
    "Requirements And Acceptance Basis": "What a solution must satisfy and which evidence supports it. Missing evidence must stay visible.",
    "Constraints": "Limits on the proposal, including scope, budget, time or access. Unknown limits are not permission to invent them.",
    "Gaps": "Missing information that may change the proposal. Use these gaps to target the next evidence request.",
    "Risks": "Potential adverse outcomes. Severity describes the source assessment, not a measured probability.",
    "Unknowns": "Unanswered questions. A draft may carry them, but blocking questions must be resolved before the relevant decision.",
    "Claims": "Statements separated by their evidence status. A citation establishes traceability, not automatic truth.",
    "Common Criteria": "The same evaluation dimensions applied to all options. These are qualitative assessments, not numerical rankings.",
    "Tradeoffs And Entry Conditions": "The advantages, costs, prerequisites and disqualifiers of each option. Check the conditions before preferring an approach.",
    "Recommendation": "A conditional proposal based on the cited evidence. It is not customer selection or design approval.",
    "Decision State": "The actual recorded selection status. Draft generation never grants implementation authority.",
    "Proposed Components": "The responsibilities in the discussion design. These are proposed components, not deployed services.",
    "Trust Boundaries": "Where identity, information or authority crosses a boundary. Each crossing needs explicit controls.",
    "Required Decisions": "Choices reserved for accountable people. Record authorization in the customer workflow, not by changing a report label.",
    "Ten-Part Dossier Coverage": "Where each design area is discussed. Coverage is not completeness, approval or delivery progress.",
    "Authority Boundary": "Which system and role can authorize a decision. A review comment does not replace customer authority.",
    "Required Customer Roles": "Roles required by customer policy. They are not assignments, identities or evidence of consent.",
    "Two Customer Decisions": "Architecture selection comes first. Approval of the exact completed design revision is a separate later decision.",
    "Blocking Unknowns": "Questions that prevent the next authorized decision. Draft availability does not resolve these questions.",
    "Allowed Decisions": "Responses a qualified reviewer may record in the authorized workflow. These are not clickable approval actions.",
    "Report Purpose": "Understand what this report is, which review problem it addresses and the working output it should produce for the technology reviewer and customer.",
    "Dependencies": "Identify prerequisites that other people, systems or evidence must supply. Use these to sequence discovery without assuming another team has completed its work.",
    "Assumptions": "Confirm, correct or retain each provisional statement explicitly. Do not silently promote an assumption to a fact or a delivery commitment.",
    "Questions For Review": "Obtain the customer information most likely to change the proposal. Record the answer, source and resulting scope or design change.",
    "Intake Decisions And Constraints": "Check what the requester supplied and what remains unknown. Distinguish conversational assumptions from reviewed evidence before setting expectations.",
    "Analysis Preparation": "Trace model preparation to its input, prompt and response revisions. Structural validation does not establish semantic correctness or customer approval.",
    "Discovery Worklist": "Target follow-up on acceptance measures, constraints and missing evidence before carrying assumptions into option selection.",
    "Source Verification Worklist": "Check source ownership, currency, access scope and support for the cited statement. A valid hash binds bytes but does not prove truth or applicability.",
    "Requirement Evidence Trace": "Locate the source basis for each requirement. Inspect where support is absent or concentrated; citation IDs do not replace reading the source.",
    "Claim Review And Disposition": "Decide what to confirm, correct, reject or leave uncertain. Preserve the previous revision and record the evidence and rationale behind a change.",
    "Selection Readiness": "Identify open questions that can change option fit. Resolve blocking evidence and verify customer authority before recording a selected architecture.",
    "Architecture Decision Record": "Capture selection or deferral, alternatives, rationale, evidence revision and authorized decision-maker. This is a recording contract, not a customer decision.",
    "Design Review Worklist": "Check each plan's proposed approach, required evidence and blocking questions. Define a test or review method before treating an area as delivery-ready.",
    "Requirement To Plan Trace": "Follow requirements into proposed readiness plans. A reference shows intended coverage, not implementation or verification.",
    "Evidence Required At Each Gate": "Separate the evidence needed for architecture selection from the evidence needed to approve the completed design. Earlier discussion cannot satisfy a later approval gate.",
    "Review Worklist": "Read unresolved questions beside the plans they affect. Prioritize shared blockers and obtain a customer-named owner and closure evidence.",
    "Review Recording Contract": "Record reviewer, authority, decision, rationale, evidence and exact revision. Do not infer consent from attendance, generation or repository activity.",
    "Invitation Draft": "Adapt this proposed message to approved participants and logistics. It explains the meeting ask without claiming it was sent or accepted.",
    "Participant Responsibilities": "Confirm named people and delegated authority for the required roles. Policy roles are not automatic attendance or work assignments.",
    "Pre-Read And Evidence To Bring": "Connect meeting preparation to unresolved customer questions. Identify which documents to inspect and which answers or source records to bring.",
    "Decision Request And Boundaries": "State the decision the session can support and what it cannot authorize. Missing evidence or authority requires deferral, not presumed approval.",
    "Logistics And Follow-Up": "Complete customer-owned invitation details and define how corrections and actions will be captured. Dates, attendance and commitments are not invented.",
    "Purpose And Meeting Outcome": "Align the participants on why the workshop exists and the records it should produce. These are proposed outputs, not outcomes already achieved.",
    "Participants And Preparation": "Confirm customer authority and focused pre-work so the session can address decisions. Preparation guidance does not establish attendance or approval.",
    "Time-Boxed Working Agenda": "Allocate discussion time to concrete review tasks and outputs. These are meeting time boxes, not solution delivery estimates.",
    "Outcome And Scope Confirmation": "Test the business framing before technology discussion. Capture corrections, exclusions, baselines and the accountable acceptance owner.",
    "Priority Questions And Blockers": "Protect the decision from missing evidence. Agree follow-up with the customer and identify what would close each unresolved question.",
    "Option Discussion Prompts": "Challenge fit, conditions and disqualifiers consistently. Ask what evidence would change a preference rather than treating a recommendation as selection.",
    "Decision And Action Record": "Capture the actual decision, correction, deferral or evidence request with its revision, authority, rationale and agreed follow-up.",
    "Meeting Exit Criteria": "Check for corrected understanding, explicit decision status and owned follow-up. Do not close the session by implying missing decisions were made.",
    "Follow-Up And Next Gate": "Carry reviewed evidence into the next lifecycle step. Authorized architecture selection precedes a selected dossier and its separate revision approval.",
    "Facilitation Preparation": "Prepare the problem reflection, evidence challenges and authority boundaries. These are facilitator prompts, never scripted customer answers.",
    "Handling Uncertainty And Disagreement": "Separate disputed facts, business priorities and risk acceptance. Identify the evidence or authority needed instead of forcing premature consensus.",
    "Close-Out Readback": "Repeat only agreed decisions and actions with rationale, owner, date and next checkpoint. Keep deferrals and unassigned work explicit.",
}


class GlossaryMarkup(HTMLParser):
    """Annotate visible prose without changing links, code, hidden regions or SVG text."""

    def __init__(self, glossary: dict[str, str]) -> None:
        super().__init__(convert_charrefs=False)
        self.glossary = glossary
        self.parts: list[str] = []
        self.stack: list[str] = []
        self.hidden_depth: int | None = None
        self.used: dict[str, str] = {}
        # Match complete identifiers and longest terms before shorter abbreviations.
        terms = "|".join(re.escape(term) for term in sorted(glossary, key=len, reverse=True))
        identifiers = r"(?:RUN|SYN|EVD|REQ|UNK|RSK|GAP|ASM|CLM|DEP|OPT|DOS|PLAN)-[A-Z0-9-]+"
        self.pattern = re.compile(
            r"\b(?:" + identifiers + "|" + terms + r"|[A-Z][A-Z0-9]{1,}(?:-[0-9]+)?)\b"
        )

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.parts.append(self.get_starttag_text())
        if tag not in {"area", "base", "br", "col", "hr", "img", "input", "link", "meta", "wbr"}:
            self.stack.append(tag)
            if self.hidden_depth is None and dict(attrs).get("aria-hidden") == "true":
                self.hidden_depth = len(self.stack)

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.parts.append(self.get_starttag_text())

    def handle_endtag(self, tag: str) -> None:
        self.parts.append(f"</{tag}>")
        if tag in self.stack:
            self.stack = self.stack[: len(self.stack) - 1 - self.stack[::-1].index(tag)]
        if self.hidden_depth is not None and len(self.stack) < self.hidden_depth:
            self.hidden_depth = None

    def handle_data(self, data: str) -> None:
        if set(self.stack) & {"script", "style"}:
            self.parts.append(data)
            return
        if self.hidden_depth is not None or set(self.stack) & {
            "a",
            "button",
            "abbr",
            "svg",
            "pre",
            "code",
            "title",
            "option",
        }:
            self.parts.append(html.escape(data))
            return

        def explain(match: re.Match[str]) -> str:
            term = match.group()
            if re.fullmatch(r"[A-F0-9]{12,64}|USER[0-9]+", term):
                return term
            definition = self.glossary.get(term) or self.glossary.get(term.split("-")[0])
            if not definition:
                definition = (
                    "Abbreviation in the supplied text; confirm its meaning with the source owner."
                )
            self.used[term] = definition
            return (
                f'<abbr tabindex="0" data-definition="{html.escape(definition, quote=True)}" '
                f'aria-label="{html.escape(term + ": " + definition, quote=True)}">'
                f"{html.escape(term)}</abbr>"
            )

        self.parts.append(self.pattern.sub(explain, html.escape(data)))

    def handle_entityref(self, name: str) -> None:
        self.parts.append(f"&{name};")

    def handle_charref(self, name: str) -> None:
        self.parts.append(f"&#{name};")

    def handle_decl(self, decl: str) -> None:
        self.parts.append(f"<!{decl}>")


def _sections(
    markdown: str, title: str, purpose: str, help_overrides: dict[str, str] | None = None
) -> list[dict[str, Any]]:
    parser = MarkdownIt("commonmark", {"html": False}).enable("table").disable("image")
    allowed_links = {
        f"{report[0]}.{extension}" for report in REPORTS for extension in ("md", "html")
    }
    allowed_links.update(
        {
            "package.json",
            "validation-report.json",
            "audit-ledger.json",
            "intake-transcript.json",
        }
    )
    parser.validateLink = lambda destination: (
        destination.startswith("#") or destination in allowed_links
    )
    tokens = parser.parse(markdown)
    for token in tokens:
        for child in token.children or []:
            if child.type == "link_open":
                destination = child.attrGet("href") or ""
                stem = destination.removesuffix(".md")
                if stem in {report[0] for report in REPORTS}:
                    child.attrSet("href", f"{stem}.html")
    if tokens and tokens[0].type == "heading_open" and tokens[0].tag == "h1":
        tokens = tokens[3:]
    groups: list[tuple[str, list[Any]]] = []
    current_title, current = "At a Glance", []
    position = 0
    while position < len(tokens):
        token = tokens[position]
        if token.type == "heading_open" and token.tag in {"h2", "h3"}:
            if current:
                groups.append((current_title, current))
            current_title, current = tokens[position + 1].content, []
            position += 3
        else:
            current.append(token)
            position += 1
    if current:
        groups.append((current_title, current))

    def fence(tokens: list[Any], index: int, options: Any, env: Any) -> str:
        content = html.escape(tokens[index].content)
        if tokens[index].info.strip() == "transcript":
            return (
                f'<pre class="transcript-text"><code>{content.removesuffix(chr(10))}</code></pre>'
            )
        if tokens[index].info.strip() == "mermaid":
            return f"<details><summary>Diagram source</summary><pre>{content}</pre></details>"
        return f"<pre><code>{content}</code></pre>"

    parser.renderer.rules["fence"] = fence
    return [
        {
            "id": f"section-{index}",
            "title": heading,
            "purpose": (help_overrides or {}).get(heading)
            or SECTION_HELP.get(
                heading,
                f"{purpose} Review the recorded {heading.lower()} and identify the evidence, correction or customer decision needed before relying on it.",
            ),
            "body": Markup(parser.renderer.render(body, parser.options, {})),
        }
        for index, (heading, body) in enumerate(groups, 1)
    ]


def report_analytics(package: dict[str, Any], turns: list[dict[str, Any]]) -> dict[str, Any]:
    """Count recorded references and relationships, never infer scores or completed work."""
    requirements = package["normalizedIntake"]["requirements"]
    claims = package["normalizedIntake"]["claims"]
    plans = package["proposedDesign"]["readinessPlans"]
    sources = [
        {
            "id": source["id"],
            "title": source["title"],
            "requirements": sum(source["id"] in item["evidenceIds"] for item in requirements),
            "claims": sum(source["id"] in item.get("evidenceIds", []) for item in claims),
        }
        for source in package["evidenceManifest"]["sources"]
    ]
    options = [
        {
            "id": option["id"],
            "name": option["name"],
            "conditions": len(option["conditions"]),
            "disqualifiers": len(option["disqualifiers"]),
        }
        for option in package["optionAnalysis"]["options"]
    ]
    blockers = [
        {
            **unknown,
            "planIds": [
                plan["id"] for plan in plans if unknown["id"] in plan["blockingUnknownIds"]
            ],
        }
        for unknown in package["analysis"]["unknowns"]
        if unknown["id"] in package["humanReview"]["blockingUnknownIds"]
    ]
    blockers.sort(key=lambda item: (-len(item["planIds"]), item["id"]))
    kinds = Counter(turn["kind"] for turn in turns)
    kind_labels = {
        "message": "Messages",
        "question": "Questions",
        "answer": "Answers",
        "correction": "Corrections",
        "summary": "Intake summaries",
        "generation_plan": "Generation plans",
        "generation_approval": "Generation approvals",
        "control": "Actions",
    }
    conversation = [
        {"label": label, "count": kinds[kind]} for kind, label in kind_labels.items() if kinds[kind]
    ]
    return {
        "sources": sources,
        "sourceMaximum": max(
            (max(item["requirements"], item["claims"]) for item in sources), default=1
        )
        or 1,
        "options": options,
        "optionMaximum": max(
            (max(item["conditions"], item["disqualifiers"]) for item in options), default=1
        )
        or 1,
        "blockers": blockers,
        "conversation": conversation,
        "conversationMaximum": max(kinds.values(), default=1),
        "questions": kinds["question"],
        "unanswered": sum(turn["unanswered"] for turn in turns),
    }


def _use_case_context(package: dict[str, Any]) -> dict[str, Any]:
    discovery = package["discovery"]
    intake = discovery.get("intakeContext") or {}
    normalized = package["normalizedIntake"]
    scope = intake.get("scope")
    exclusions = intake.get("exclusions")
    return {
        "title": discovery["initiativeTitle"],
        "assessmentTitle": f"{discovery['initiativeTitle']} - Initial Technical Intake Assessment",
        "businessProblem": discovery["businessProblem"],
        "originalRequest": discovery["businessProblem"],
        "targetUsers": discovery["targetUsers"],
        "desiredOutcomes": discovery["desiredOutcomes"],
        "successMeasures": discovery["successMeasures"],
        "constraints": discovery["constraints"],
        "scope": scope or "The initial scope has not yet been confirmed with the customer.",
        "exclusions": exclusions
        or "Explicit exclusions have not yet been confirmed with the customer.",
        "budget": intake.get("budget") or "No customer budget or funding range was supplied.",
        "timeline": intake.get("timeline") or "No customer target date was supplied.",
        "systems": intake.get("systems")
        or "Current systems and integration boundaries are unknown.",
        "ownership": intake.get("ownership")
        or "Business and technical ownership has not yet been confirmed.",
        "baseline": intake.get("baseline")
        or "No approved current-state performance baseline was supplied.",
        "stakeholders": [
            {"role": stakeholder, "authority": "Unknown; no authority supplied."}
            if isinstance(stakeholder, str)
            else stakeholder
            for stakeholder in normalized["stakeholders"]
        ],
        "requirements": normalized["requirements"],
    }


def render_html_reports(result: WorkflowResult, documents: dict[str, str]) -> dict[str, str]:
    environment = Environment(
        loader=FileSystemLoader(TEMPLATES),
        undefined=StrictUndefined,
        autoescape=select_autoescape(default=True),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    environment.filters["display_time"] = lambda value: (
        datetime.fromisoformat(value)
        .astimezone(
            UTC,
        )
        .strftime("%d %b %Y, %H:%M:%S UTC")
    )
    icon_sources = json.loads((TEMPLATES / "report-icons.json").read_text(encoding="utf-8"))
    ElementTree.register_namespace("", "http://www.w3.org/2000/svg")

    def icon(name: str) -> Markup:
        root = ElementTree.fromstring(icon_sources[name])
        root.set("aria-hidden", "true")
        root.set("focusable", "false")
        root.set("class", "icon")
        return Markup(ElementTree.tostring(root, encoding="unicode"))

    environment.globals["icon"] = icon
    template = environment.get_template("report.html.j2")
    glossary = json.loads((TEMPLATES / "report-glossary.json").read_text(encoding="utf-8"))
    package = result.package
    use_case = _use_case_context(package)
    transcript = package["discovery"].get(
        "intakeTranscript", missing_transcript(result.initiative_id)
    )
    turns = transcript_turns(transcript, package["discovery"]["submittedBy"]["displayName"])
    analytics = report_analytics(package, turns)
    help_overrides = {
        f"{option['id']}: {option['name']}": "Test this option's strengths against the business outcome, examine its tradeoffs, verify every entry condition and challenge its disqualifiers. Use the same criteria as the other two options; this is not a rating or customer selection."
        for option in package["optionAnalysis"]["options"]
    }
    help_overrides.update(
        {
            plan[
                "title"
            ]: f"Review {plan['title'].lower()} against its linked requirements. Confirm the proposed approach, obtain the listed evidence and resolve its blocking questions before treating the area as ready. The plan does not implement or verify the solution."
            for plan in package["proposedDesign"]["readinessPlans"]
        }
    )
    help_overrides.update(
        {
            "0:00-4:00 - Confirm the outcome": "Establish a shared business framing before discussing technology. Ask for scope corrections and acceptance evidence; capture the customer's actual response rather than assuming agreement.",
            "4:00-12:00 - Test the evidence": "Challenge the source basis and identify which missing answers change the decision. Use the priority questions to request specific evidence and retain uncertainty where it remains unresolved.",
            "12:00-22:00 - Compare three options": "Give every option the same scrutiny. Test fit, entry conditions and disqualifiers against the customer's needs; keep the recommendation separate from an authorized selection.",
            "22:00-27:00 - Record decisions and evidence requests": "Ask the authorized customer owner for the actual next action, or an explicit deferral. Record rationale, evidence and authority without advancing the later design-approval gate.",
            "27:00-30:00 - Confirm next steps": "Read back only agreed owners, evidence actions, dates and the next checkpoint. Make unanswered questions and unassigned work explicit so the handoff is usable.",
        }
    )
    risks = package["analysis"]["risks"]
    risk_counts = Counter(item["severity"].lower() for item in risks)
    claims = Counter(item["label"] for item in package["normalizedIntake"]["claims"])
    reports = []
    for identifier, title, purpose in REPORTS:
        reports.append({"id": identifier, "title": title, "purpose": purpose})
    outputs = {}
    for report in reports:
        guidance = REPORT_GUIDANCE[report["id"]]
        if report["id"] == "intake-transcript":
            sections = [{"id": "transcript-session", "title": "Session"}]
            if turns:
                sections.append({"id": "transcript-conversation", "title": "Conversation"})
        else:
            sections = [
                section
                for section in _sections(
                    documents.get(f"{report['id']}.md", ""),
                    report["title"],
                    report["purpose"],
                    {
                        **help_overrides,
                        "Report Context": f"{guidance['problem']} Use this recorded context to {guidance['workingOutput'][0].lower() + guidance['workingOutput'][1:]}",
                    },
                )
                if section["title"] not in {"Report Purpose", "Use Case Context"}
            ]
        source = template.render(
            result=result,
            package=package,
            use_case=use_case,
            report=report,
            reports=reports,
            sections=sections,
            guidance=guidance,
            transcript=transcript,
            turns=turns,
            analytics=analytics,
            risks=risk_counts,
            risk_total=len(risks),
            claims=claims,
            claim_total=sum(claims.values()),
            glossary=glossary,
            css=(TEMPLATES / "report.css").read_text(encoding="utf-8"),
            script=(TEMPLATES / "report.js").read_text(encoding="utf-8"),
            license_text=(TEMPLATES / "lucide-LICENSE").read_text(encoding="utf-8"),
        )
        decorated = GlossaryMarkup(glossary)
        decorated.feed(source)
        outputs[f"{report['id']}.html"] = "".join(decorated.parts)
    return outputs


def render_job_status(state: dict[str, Any]) -> str:
    environment = Environment(
        loader=FileSystemLoader(TEMPLATES),
        undefined=StrictUndefined,
        autoescape=select_autoescape(default=True),
    )
    return environment.get_template("job.html.j2").render(
        state=state,
        css=Markup((TEMPLATES / "report.css").read_text(encoding="utf-8")),
    )
