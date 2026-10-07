# SPDX-License-Identifier: LicenseRef-MOSAIC-Evaluation
"""Verify generated reports, conversation fidelity, attribution and offline markup."""

import json
from datetime import UTC, datetime
from html import escape
from html.parser import HTMLParser
from pathlib import Path

import pytest

from mosaic.cli import DEFAULT_CUSTOMER, DEFAULT_EXAMPLE, run_demo
from mosaic.reports import GlossaryMarkup, report_analytics
from mosaic.stages import design
from mosaic.stages import option as option_stage


def test_glossary_does_not_modify_scripts_styles_or_browser_title() -> None:
    parser = GlossaryMarkup({"AI": "Artificial intelligence"})
    source = "<!doctype html><title>AI report</title><style>a>b{color:red}</style>"
    source += '<script>if (true && false) { console.log("AI"); }</script><p>AI</p>'
    parser.feed(source)
    output = "".join(parser.parts)
    assert "<title>AI report</title>" in output
    assert "<style>a>b{color:red}</style>" in output
    assert '<script>if (true && false) { console.log("AI"); }</script>' in output
    assert "<!doctype html>" in output
    assert output.count("<abbr ") == 1


def test_glossary_preserves_hidden_text_and_whole_identifiers() -> None:
    parser = GlossaryMarkup({"AI": "Artificial intelligence", "RUN": "Run identifier"})
    parser.feed(
        '<span aria-hidden="true"><span>AI</span></span><p>RUN-SYN-TRAVEL-001-A123B456C789</p>'
    )
    output = "".join(parser.parts)
    assert '<span aria-hidden="true"><span>AI</span></span>' in output
    assert output.count("<abbr ") == 1
    assert 'data-definition="Run identifier"' in output
    assert "Abbreviation in the supplied text" not in output


def test_glossary_preserves_message_markers_and_classification_labels() -> None:
    glossary_path = Path(__file__).resolve().parents[1] / "templates" / "report-glossary.json"
    glossary = json.loads(glossary_path.read_text(encoding="utf-8"))
    parser = GlossaryMarkup(glossary)
    parser.feed("<p>USER1-USER2 USER3 USER12 PUBLIC-SUMMARY</p>")
    output = "".join(parser.parts)
    assert "<p>USER1-USER2 USER3 USER12 <abbr " in output
    assert output.count("<abbr ") == 1
    assert ">PUBLIC-SUMMARY</abbr>" in output
    assert parser.used == {"PUBLIC-SUMMARY": glossary["PUBLIC-SUMMARY"]}
    parser.feed("<p>ZZQ</p>")
    assert parser.used["ZZQ"].startswith("Abbreviation in the supplied text")


def test_cli_run_generates_complete_validated_package(tmp_path: Path) -> None:
    catalog_path = DEFAULT_EXAMPLE / "sources" / "catalog.json"
    before_generation = datetime.now(UTC)

    summary = run_demo(
        DEFAULT_EXAMPLE / "request.json",
        catalog_path,
        DEFAULT_EXAMPLE / "source-policy.json",
        DEFAULT_CUSTOMER,
        tmp_path,
    )

    assert summary["state"] == "awaiting_human_review"
    assert summary["validation"] == "pass"
    assert summary["artifactCount"] == 23
    assert len(list(tmp_path.iterdir())) == 23
    transcript = json.loads((tmp_path / "intake-transcript.json").read_text(encoding="utf-8"))
    assert transcript["captureStatus"] == "not_recorded"
    assert transcript["entries"] == []
    assert "No dialogue was reconstructed" in (tmp_path / "intake-transcript.md").read_text(
        encoding="utf-8",
    )
    for report_path in tmp_path.glob("*.html"):
        report = report_path.read_text(encoding="utf-8")
        assert "<span>Technical intake assessment</span>" in report
        assert "Employee Policy Guidance" in report
        assert "Solution definition" not in report
        assert 'aria-label="Report navigation"' in report
        assert 'id="report-search"' not in report
        assert "Find a report" not in report
        assert 'href="index.html"' in report
        assert 'id="report-tooltip"' in report
        assert "data-definition=" in report
        assert "Content-Security-Policy" in report
    with (tmp_path / "validation-report.json").open(encoding="utf-8") as stream:
        validation = json.load(stream)
    assert validation["status"] == "pass"
    with (tmp_path / "package.json").open(encoding="utf-8") as stream:
        package = json.load(stream)
    report_metadata = package["package"]["reportMetadata"]
    assert report_metadata["preparedBy"] == "MOSAIC"
    report_time = datetime.fromisoformat(report_metadata["generatedAt"])
    assert before_generation <= report_time <= datetime.now(UTC)
    assert package["package"]["discovery"]["submittedBy"] == {
        "displayName": "John Doe",
        "basis": "default_placeholder",
        "identityVerified": False,
    }
    index = (tmp_path / "index.html").read_text(encoding="utf-8")
    heading = index.split('<div class="page-heading">', 1)[1].split("<section", 1)[0]
    assert heading.index("</h1>") < heading.index("Report generated")
    assert f'datetime="{report_metadata["generatedAt"]}"' in heading
    assert f'datetime="{package["metadata"]["timestamp"]}"' in heading
    assert "Intake received" in heading
    assert "Submitted by" in heading
    assert "John Doe" in heading
    assert "Default name; identity not verified" in heading
    assert len(package["package"]["optionAnalysis"]["options"]) == 3
    assert package["package"]["humanReview"]["releaseAuthorized"] is False
    options = package["package"]["optionAnalysis"]
    matrix = (tmp_path / "option-matrix.md").read_text(encoding="utf-8")
    assert "Seeded qualitative scenario analysis" in matrix
    for option in options["options"]:
        assert "weightedScore" not in option
        assert set(option["criterionAssessments"]) == set(options["evaluationCriteria"])
        for tradeoff in option["tradeoffs"]:
            assert tradeoff in matrix
        for disqualifier in option["disqualifiers"]:
            assert disqualifier in matrix
    architecture = (tmp_path / "architecture-brief.md").read_text(encoding="utf-8")
    assert "Employee with workforce identity" in architecture
    assert "Approved policy sources" in architecture
    assert "Prewritten discussion draft" in architecture
    design = package["package"]["proposedDesign"]
    assert len(design["dossierCoverage"]) == 10
    assert len(design["readinessPlans"]) == 7
    assert "not ten completed or" in architecture
    for plan in design["readinessPlans"]:
        assert f"## {plan['title']}" in architecture
        assert plan["requiredEvidence"] in architecture
        for reference in [
            *plan["evidenceIds"],
            *plan["requirementIds"],
            *plan["blockingUnknownIds"],
        ]:
            assert reference in architecture
    review = (tmp_path / "human-review.md").read_text(encoding="utf-8")
    assert "Architecture selection" in review
    assert "Design-package approval" in review
    assert "not customer design approval" in review


def test_customer_reviewer_policy_changes_output_and_identity(tmp_path: Path) -> None:
    customer = json.loads(DEFAULT_CUSTOMER.read_text(encoding="utf-8"))
    arguments = (
        DEFAULT_EXAMPLE / "request.json",
        DEFAULT_EXAMPLE / "sources" / "catalog.json",
        DEFAULT_EXAMPLE / "source-policy.json",
    )
    original = run_demo(*arguments, DEFAULT_CUSTOMER, tmp_path / "original")
    customer["requiredReviewerRoles"] = ["Synthetic portfolio owner", "Synthetic design board"]
    customer["configurationId"] = "synthetic-review-policy-2.0.0"
    customer_path = tmp_path / "customer.json"
    customer_path.write_text(json.dumps(customer), encoding="utf-8")

    changed = run_demo(*arguments, customer_path, tmp_path / "changed")

    package = json.loads((tmp_path / "changed" / "package.json").read_text(encoding="utf-8"))
    review = package["package"]["humanReview"]
    assert changed["runId"] != original["runId"]
    assert review["requiredReviewerRoles"] == customer["requiredReviewerRoles"]
    assert review["policyConfigurationId"] == customer["configurationId"]
    assert review["releaseAuthorized"] is False
    for name in ("human-review.md", "index.html"):
        rendered = (tmp_path / "changed" / name).read_text(encoding="utf-8")
        assert all(role in rendered for role in customer["requiredReviewerRoles"])


def test_unsupported_customer_document_stops_before_writing(tmp_path: Path) -> None:
    customer = json.loads(DEFAULT_CUSTOMER.read_text(encoding="utf-8"))
    customer["requiredArtifacts"].append("custom-production-design.md")
    customer_path = tmp_path / "customer.json"
    customer_path.write_text(json.dumps(customer), encoding="utf-8")
    output = tmp_path / "output"

    with pytest.raises(ValueError, match="unsupported.*custom-production-design.md"):
        run_demo(
            DEFAULT_EXAMPLE / "request.json",
            DEFAULT_EXAMPLE / "sources" / "catalog.json",
            DEFAULT_EXAMPLE / "source-policy.json",
            customer_path,
            output,
        )

    assert not output.exists()


def conversation_request() -> dict:
    request = json.loads((DEFAULT_EXAMPLE / "request.json").read_text(encoding="utf-8"))
    option_draft = option_stage.execute(request)
    design_draft = design.execute(option_draft)
    option_draft["options"][0]["name"] = "Test-authored travel search improvement"
    option_draft["assessmentBasis"] = "Test-authored comparison for the current intake."
    design_draft["architecture"]["experience"] = "Test-authored travel policy search"
    design_draft["assessmentBasis"] = "Test-authored unselected discussion design."
    request.update(
        {
            "inputMode": "conversation",
            "businessProblem": (
                "Contoso staff face rejected travel claims after following outdated guidance."
            ),
            "intakeContext": {
                "scope": "Travel claims for 250 field staff",
                "exclusions": "No deployment",
                "budget": "$30,000 initial work ceiling",
                "timeline": "Proposal by 15 October",
                "systems": "SharePoint",
                "ownership": "Finance",
                "baseline": None,
            },
            "optionDraft": option_draft,
            "designDraft": design_draft,
        }
    )
    return request


def test_conversation_answers_and_authored_analysis_reach_all_formats(tmp_path: Path) -> None:
    request = conversation_request()
    request_path = tmp_path / "request.json"
    request_path.write_text(json.dumps(request), encoding="utf-8")
    output = tmp_path / "reports"
    run_demo(
        request_path,
        DEFAULT_EXAMPLE / "sources/catalog.json",
        DEFAULT_EXAMPLE / "source-policy.json",
        DEFAULT_CUSTOMER,
        output,
    )
    package = json.loads((output / "package.json").read_text(encoding="utf-8"))["package"]
    assert package["discovery"]["intakeContext"] == request["intakeContext"]
    for name in ("intake-report.md", "intake-report.html"):
        content = (output / name).read_text(encoding="utf-8")
        for value in request["intakeContext"].values():
            if value:
                assert value in content
        assert "Unknown" in content
    for name in ("option-matrix.md", "option-matrix.html"):
        content = (output / name).read_text(encoding="utf-8")
        assert "Test-authored travel search improvement" in content
    for name in ("architecture-brief.md", "architecture-brief.html"):
        content = (output / name).read_text(encoding="utf-8")
        assert "Test-authored travel policy search" in content
        assert "A[Employee with workforce identity]" not in content
    assert package["humanReview"]["releaseAuthorized"] is False


@pytest.mark.parametrize(
    "stakeholders",
    [
        None,
        [],
        ["Employee Services business owner", "Finance <policy> owner"],
        [{"role": "Finance policy owner", "authority": "Supplied policy responsibility"}],
        [
            "Employee Services business owner",
            {"role": "Finance policy owner", "authority": "Supplied policy responsibility"},
        ],
    ],
    ids=["omitted", "empty", "role-names", "role-records", "mixed"],
)
def test_reports_accept_supported_stakeholder_shapes(
    tmp_path: Path, stakeholders: list[str | dict[str, str]] | None
) -> None:
    request = conversation_request()
    if stakeholders is None:
        request.pop("stakeholders", None)
    else:
        request["stakeholders"] = stakeholders
    request_path = tmp_path / "request.json"
    request_path.write_text(json.dumps(request), encoding="utf-8")
    output = tmp_path / "reports"

    summary = run_demo(
        request_path,
        DEFAULT_EXAMPLE / "sources/catalog.json",
        DEFAULT_EXAMPLE / "source-policy.json",
        DEFAULT_CUSTOMER,
        output,
    )

    assert summary["artifactCount"] == 23
    assert summary["validation"] == "pass"
    assert summary["state"] == "awaiting_human_review"
    package = json.loads((output / "package.json").read_text(encoding="utf-8"))["package"]
    assert package["normalizedIntake"]["stakeholders"] == (stakeholders or [])
    assert package["humanReview"]["releaseAuthorized"] is False
    overview = (output / "index.html").read_text(encoding="utf-8")
    for stakeholder in stakeholders or []:
        if isinstance(stakeholder, str):
            assert escape(stakeholder) in overview
            assert "Unknown; no authority supplied." in overview
        else:
            assert stakeholder["role"] in overview
            assert stakeholder["authority"] in overview
    if not stakeholders:
        assert "No stakeholder roles were supplied." in overview
    assert "Finance <policy> owner" not in overview


def test_meeting_agenda_supports_a_customer_decision_workshop(tmp_path: Path) -> None:
    run_demo(
        DEFAULT_EXAMPLE / "request.json",
        DEFAULT_EXAMPLE / "sources/catalog.json",
        DEFAULT_EXAMPLE / "source-policy.json",
        DEFAULT_CUSTOMER,
        tmp_path,
    )
    package = json.loads((tmp_path / "package.json").read_text(encoding="utf-8"))["package"]
    agenda = (tmp_path / "meeting-agenda.md").read_text(encoding="utf-8")
    assert package["discovery"]["businessProblem"] in agenda
    assert "## Participants And Preparation" in agenda
    assert "## Decision And Action Record" in agenda
    assert "## Meeting Exit Criteria" in agenda
    assert "27:00-30:00" in agenda
    for role in package["humanReview"]["requiredReviewerRoles"]:
        assert role in agenda
    for unknown in package["analysis"]["unknowns"]:
        assert unknown["id"] in agenda
    for option in package["optionAnalysis"]["options"]:
        assert option["name"] in agenda
    assert "customer-named owner" in agenda
    assert "None of those assignments or dates has been recorded" in agenda
    assert "no implementation is authorized" in agenda
    for filename in tmp_path.glob("*.md"):
        report = filename.read_text(encoding="utf-8")
        assert report.startswith("# Employee Policy Guidance:")
        assert "## Use Case Context" in report
        assert package["discovery"]["businessProblem"] in report
        assert "MOSAIC Intake Report" not in report
        assert "## Report Purpose" not in report
        assert "**Problem it solves:**" not in report
        assert "**Working outcome:**" not in report
    overview = (tmp_path / "index.html").read_text(encoding="utf-8")
    assert (
        "<title>Employee Policy Guidance - Initial Technical Intake Assessment</title>" in overview
    )
    assert "Original Request" in overview
    assert "Executive Summary" in overview
    assert "Requestor, Users and Stakeholders" in overview
    assert "Scope and Boundaries" in overview
    assert "Current Environment and Delivery Context" in overview
    assert "Requirements and Proposed Success Measures" in overview
    assert "Data Sources and Evidence" in overview
    assert "Unknowns, Dependencies and Risks" in overview
    assert "Conditional assessment recommendation" in overview
    assert "Recommended Next Steps and Decisions" in overview
    assert "Where the Work Stands" not in overview
    assert "Purpose &amp; Use" not in overview
    assert "Problem it solves" not in overview
    option_page = (tmp_path / "option-matrix.html").read_text(encoding="utf-8")
    assert "<title>Employee Policy Guidance - Solution Options</title>" in option_page
    expected_sections = {
        "intake-report.md": "Discovery Worklist",
        "evidence-appendix.md": "Source Verification Worklist",
        "option-matrix.md": "Architecture Decision Record",
        "architecture-brief.md": "Requirement To Plan Trace",
        "human-review.md": "Review Worklist",
        "meeting-request.md": "Pre-Read And Evidence To Bring",
        "talk-track.md": "Handling Uncertainty And Disagreement",
    }
    for filename, section in expected_sections.items():
        assert f"## {section}" in (tmp_path / filename).read_text(encoding="utf-8")
    analytics = report_analytics(package, [])
    for source in analytics["sources"]:
        assert source["requirements"] == sum(
            source["id"] in item["evidenceIds"]
            for item in package["normalizedIntake"]["requirements"]
        )
    for option, counts in zip(
        package["optionAnalysis"]["options"], analytics["options"], strict=True
    ):
        assert counts["conditions"] == len(option["conditions"])
        assert counts["disqualifiers"] == len(option["disqualifiers"])
    for blocker in analytics["blockers"]:
        assert blocker["planIds"] == [
            plan["id"]
            for plan in package["proposedDesign"]["readinessPlans"]
            if blocker["id"] in plan["blockingUnknownIds"]
        ]
    assert analytics["conversation"] == []


def test_supplied_submitter_replaces_default_without_claiming_verified_identity(
    tmp_path: Path,
) -> None:
    request = conversation_request()
    request["submittedBy"] = "Jane Doe <synthetic>"
    request_path = tmp_path / "request.json"
    request_path.write_text(json.dumps(request), encoding="utf-8")
    output = tmp_path / "reports"
    run_demo(
        request_path,
        DEFAULT_EXAMPLE / "sources/catalog.json",
        DEFAULT_EXAMPLE / "source-policy.json",
        DEFAULT_CUSTOMER,
        output,
    )
    package = json.loads((output / "package.json").read_text(encoding="utf-8"))["package"]
    assert package["discovery"]["submittedBy"] == {
        "displayName": request["submittedBy"],
        "basis": "user_provided",
        "identityVerified": False,
    }
    index = (output / "index.html").read_text(encoding="utf-8")
    assert escape(request["submittedBy"]) in index
    assert "John Doe" not in index
    assert "Provided name; identity not verified" in index
    assert "<synthetic>" not in index
    assert package["humanReview"]["releaseAuthorized"] is False


@pytest.mark.parametrize(
    "timed, submitted_by, fidelity",
    [
        (False, None, "summary"),
        (True, None, "verbatim"),
        (True, "Jane Doe <synthetic>", "verbatim"),
    ],
)
def test_conversation_transcript_is_preserved_in_report_data(
    tmp_path: Path, timed: bool, submitted_by: str | None, fidelity: str
) -> None:
    request = conversation_request()
    if submitted_by:
        request["submittedBy"] = submitted_by
    transcript = {
        "schemaVersion": "1.0.0",
        "initiativeId": request["initiativeId"],
        "classification": "SYNTHETIC",
        "captureStatus": "partial",
        "gaps": ["Earlier questions and answers were not captured."],
        "entries": [
            {
                "sequence": 1,
                "role": "user",
                "kind": "correction",
                "fidelity": fidelity,
                "text": "Correction: 180 staff, not 250.\n  Preserve this spacing.",
                "timestamp": None,
                "replyTo": None,
                "options": [],
                "selected": [],
            },
            {
                "sequence": 2,
                "role": "assistant",
                "kind": "question",
                "fidelity": "verbatim",
                "text": "Which knowledge sources should be considered?",
                "timestamp": None,
                "context": "Choose all that apply, or provide another source.",
                "replyTo": None,
                "options": ["Generate documentation now", "SharePoint"],
                "optionDescriptions": {"SharePoint": "Sites and document libraries"},
                "selected": [],
            },
            {
                "sequence": 3,
                "role": "user",
                "kind": "answer",
                "fidelity": "verbatim",
                "text": "\n Keep <script>alert(1)</script> literal & unchanged.\r\n"
                "[Do not link](https://unapproved.example)\n~~~\nC:\\Synthetic\\Policies",
                "timestamp": None,
                "replyTo": 2,
                "options": [],
                "selected": ["SharePoint"],
            },
            {
                "sequence": 4,
                "role": "assistant",
                "kind": "question",
                "fidelity": "verbatim",
                "text": "What budget should the proposal respect?",
                "timestamp": None,
                "replyTo": None,
                "options": ["Generate documentation now", "$30,000"],
                "selected": [],
            },
            {
                "sequence": 5,
                "role": "user",
                "kind": "control",
                "fidelity": "verbatim",
                "text": None,
                "timestamp": None,
                "replyTo": 4,
                "options": [],
                "selected": [],
                "controls": ["Generate documentation now"],
            },
            {
                "sequence": 6,
                "role": "assistant",
                "kind": "generation_plan",
                "fidelity": "verbatim",
                "text": "Synthetic test plan: use approved local evidence to generate discussion "
                "documents only. No implementation, architecture selection or design approval.",
                "timestamp": None,
                "replyTo": None,
                "options": ["Approve and generate documentation", "Revise"],
                "selected": [],
            },
            {
                "sequence": 7,
                "role": "user",
                "kind": "generation_approval",
                "fidelity": "verbatim",
                "text": None,
                "timestamp": None,
                "replyTo": 6,
                "options": [],
                "selected": ["Approve and generate documentation"],
            },
        ],
    }
    if timed:
        transcript.update(
            {
                "startedAt": "2026-09-17T18:20:30Z",
                "endedAt": "2026-09-17T18:25:45Z",
            }
        )
    request["intakeTranscript"] = transcript
    request_path = tmp_path / "request.json"
    request_path.write_text(json.dumps(request), encoding="utf-8")
    output = tmp_path / "reports"
    run_demo(
        request_path,
        DEFAULT_EXAMPLE / "sources/catalog.json",
        DEFAULT_EXAMPLE / "source-policy.json",
        DEFAULT_CUSTOMER,
        output,
    )
    package = json.loads((output / "package.json").read_text(encoding="utf-8"))["package"]
    assert package["discovery"]["intakeTranscript"] == transcript
    assert json.loads((output / "intake-transcript.json").read_text(encoding="utf-8")) == transcript
    markdown = (output / "intake-transcript.md").read_text(encoding="utf-8")
    assert transcript["entries"][0]["text"] in markdown
    assert "**Capture:** Partial" in markdown
    assert "Earlier questions and answers were not captured." in markdown
    assert "**Unanswered.**" in markdown
    assert "**Action**" in markdown
    assert "**Generation approval**" in markdown
    if submitted_by:
        assert "### 1. Jane Doe \\<synthetic\\>" in markdown
    else:
        assert "### 1. John Doe" in markdown
    assert "### 2. MOSAIC" in markdown
    assert "**Reply to:** MOSAIC, message 2" in markdown
    assert "Not recorded" not in markdown
    assert "**Fidelity:**" not in markdown
    assert "No free-text message recorded." not in markdown
    assert markdown.count("**Summary:**") == (1 if fidelity == "summary" else 0)
    html = (output / "intake-transcript.html").read_text(encoding="utf-8")
    assert html.count('class="transcript-turn transcript-') == len(transcript["entries"])
    assert html.count('class="transcript-reply"') == 3
    assert 'href="#transcript-entry-2"' in html
    assert html.count('class="transcript-fidelity"') == (1 if fidelity == "summary" else 0)
    assert html.count('class="transcript-choices"') == 3
    assert "<summary>Choices offered (2)</summary>" in html
    assert "No free-text message recorded" not in html
    assert "No capture gaps declared" not in html
    assert "Fidelity:" not in html
    assert "Not recorded" not in html
    assert f">{escape(submitted_by or 'John Doe')}</a></h3>" in html
    for content in (markdown, html):
        assert "Session" in content
        if timed:
            assert "17 Sep 2026, 18:20:30" in content
            assert "17 Sep 2026, 18:25:45" in content
        else:
            assert "**Started:**" not in content
            assert "**Ended:**" not in content
            assert "17 Sep 2026, 18:20:30" not in content
    assert "**Timestamp:** Unknown" not in markdown
    assert "<script>alert(1)</script>" not in html
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in html
    assert 'href="https://unapproved.example"' not in html
    assert '<pre class="transcript-text"><code>\n Keep ' in html
    assert 'href="intake-transcript.html"' in (output / "index.html").read_text(encoding="utf-8")
    assert package["humanReview"]["releaseAuthorized"] is False


@pytest.mark.parametrize("missing", ["optionDraft", "designDraft", "intakeContext", "inputMode"])
def test_conversation_never_falls_back_to_reference(tmp_path: Path, missing: str) -> None:
    request = conversation_request()
    del request[missing]
    request_path = tmp_path / "request.json"
    request_path.write_text(json.dumps(request), encoding="utf-8")
    with pytest.raises(ValueError, match=missing):
        run_demo(
            request_path,
            DEFAULT_EXAMPLE / "sources/catalog.json",
            DEFAULT_EXAMPLE / "source-policy.json",
            DEFAULT_CUSTOMER,
            tmp_path / "reports",
        )
    assert not (tmp_path / "reports").exists()


@pytest.mark.parametrize("defect", ["duplicate", "criteria", "recommendation", "design"])
def test_authored_options_keep_common_criteria_and_valid_references(
    tmp_path: Path,
    defect: str,
) -> None:
    request = conversation_request()
    draft = request["optionDraft"]
    if defect == "duplicate":
        draft["options"][1]["id"] = draft["options"][0]["id"]
    elif defect == "criteria":
        draft["options"][1]["criterionAssessments"] = {"Incomparable criterion": "Draft"}
    elif defect == "recommendation":
        draft["recommendation"]["optionId"] = "OPT-NOT-PRESENT"
    else:
        request["designDraft"]["selectedForDiscovery"] = "OPT-NOT-PRESENT"
    request_path = tmp_path / "request.json"
    request_path.write_text(json.dumps(request), encoding="utf-8")
    with pytest.raises(ValueError, match="Workflow validation failed"):
        run_demo(
            request_path,
            DEFAULT_EXAMPLE / "sources/catalog.json",
            DEFAULT_EXAMPLE / "source-policy.json",
            DEFAULT_CUSTOMER,
            tmp_path / "reports",
        )
    assert not (tmp_path / "reports").exists()


def test_untrusted_report_text_cannot_add_active_content_or_break_cells(tmp_path: Path) -> None:
    class SafetyParser(HTMLParser):
        def __init__(self) -> None:
            super().__init__()
            self.scripts = 0
            self.active_content = []

        def handle_starttag(self, tag, attributes):
            values = dict(attributes)
            self.scripts += tag == "script"
            if (
                tag in {"img", "iframe", "object"}
                or any(key.startswith("on") for key in values)
                or values.get("href", "").startswith(("https:", "javascript:", "data:"))
            ):
                self.active_content.append((tag, values))

    request = conversation_request()
    request["businessProblem"] += (
        " <script>window.untrusted = true</script>"
        " ![tracking](https://unsafe.example/pixel) [outside](https://unsafe.example/)"
        ' <img src="https://unsafe.example/pixel" onerror="alert(1)">'
    )
    request["intakeContext"]["budget"] = "Up to $30,000 | initial work\nNot approved"
    request_path = tmp_path / "request.json"
    request_path.write_text(json.dumps(request), encoding="utf-8")
    output = tmp_path / "reports"
    run_demo(
        request_path,
        DEFAULT_EXAMPLE / "sources/catalog.json",
        DEFAULT_EXAMPLE / "source-policy.json",
        DEFAULT_CUSTOMER,
        output,
    )
    for report in output.glob("*.html"):
        parser = SafetyParser()
        parser.feed(report.read_text(encoding="utf-8"))
        assert parser.scripts == 1
        assert parser.active_content == []
    intake = (output / "intake-report.html").read_text(encoding="utf-8")
    assert "Up to $30,000 | initial work Not approved" in intake
