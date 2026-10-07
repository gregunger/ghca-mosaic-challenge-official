# SPDX-License-Identifier: LicenseRef-MOSAIC-Evaluation
"""Protect submission validation, content boundaries and reproducible reference checks."""

import json
import zipfile
from pathlib import Path

import pytest

from scripts import validate_submission as submission


@pytest.mark.parametrize(
    "state, release_mode, severity",
    [
        ("Passed", False, None),
        ("Pending", False, "human-action"),
        ("Blocked", False, "human-action"),
        ("Pending", True, "error"),
        ("Blocked", True, "error"),
    ],
)
def test_contest_gaps_are_not_reported_as_full_readiness(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    state: str,
    release_mode: bool,
    severity: str | None,
) -> None:
    directory = tmp_path / "submission"
    directory.mkdir()
    rows = ["| ID | Requirement | State | Evidence |", "| --- | --- | --- | --- |"]
    rows.extend(
        f"| {identifier} | Synthetic requirement | "
        f"{state if identifier == 'CR-01' else 'Passed'} | Synthetic test evidence |"
        for identifier in sorted(submission.CONTEST_ACCEPTANCE_IDS)
    )
    (directory / "OPEN-ITEMS.md").write_text("\n".join(rows), encoding="utf-8")
    monkeypatch.setattr(submission, "PROJECT_ROOT", tmp_path)
    readiness = submission.Readiness(release_mode)

    submission.validate_acceptance_register(readiness)

    assert "contest_acceptance_register:17_requirements" in readiness.passed_checks
    if severity is None:
        assert not readiness.findings
    else:
        assert len(readiness.findings) == 1
        assert readiness.findings[0].severity == severity
        assert readiness.findings[0].check == "contest_acceptance"
        assert "declared_contest_requirement:CR-01" not in readiness.passed_checks


@pytest.mark.parametrize("defect", ["missing", "duplicate", "state", "evidence"])
def test_incomplete_or_ambiguous_contest_register_fails_closed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    defect: str,
) -> None:
    directory = tmp_path / "submission"
    directory.mkdir()
    rows = ["| ID | Requirement | State | Evidence |", "| --- | --- | --- | --- |"]
    rows.extend(
        f"| {identifier} | Synthetic requirement | Passed | Synthetic test evidence |"
        for identifier in sorted(submission.CONTEST_ACCEPTANCE_IDS)
    )
    if defect == "missing":
        rows.pop()
    elif defect == "duplicate":
        rows.append(rows[-1])
    elif defect == "state":
        rows[-1] = rows[-1].replace("Passed", "Ready")
    else:
        rows[-1] = rows[-1].replace("Synthetic test evidence", "")
    (directory / "OPEN-ITEMS.md").write_text("\n".join(rows), encoding="utf-8")
    monkeypatch.setattr(submission, "PROJECT_ROOT", tmp_path)
    readiness = submission.Readiness(False)

    submission.validate_acceptance_register(readiness)

    assert len(readiness.findings) == 1
    assert readiness.findings[0].check == "contest_acceptance_register"
    assert readiness.findings[0].severity == "error"
    assert not readiness.passed_checks


def test_private_configuration_and_generated_metadata_are_not_submission_files(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    private_paths = [
        ".mcp.json",
        ".env",
        ".env.local",
        "__pycache__/local.json",
        "src/synthetic.egg-info/PKG-INFO",
        "build/run/record.json",
        "docs/contest-info.json",
    ]
    public_paths = ["README.md", ".env.example", ".env.sample"]
    for relative_path in [*private_paths, *public_paths]:
        path = tmp_path / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("Synthetic fixture.\n", encoding="utf-8")
    monkeypatch.setattr(submission, "PROJECT_ROOT", tmp_path)

    actual = {path.relative_to(tmp_path).as_posix() for path in submission.project_files()}

    assert actual == set(public_paths)


@pytest.mark.parametrize("change", ["none", "document", "missing_time", "invalid_time"])
def test_reference_comparison_freezes_only_the_render_clock(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    change: str,
) -> None:
    expected = tmp_path / "examples" / "synthetic" / "expected"
    submission.run_demo(
        submission.DEFAULT_EXAMPLE / "request.json",
        submission.DEFAULT_EXAMPLE / "sources" / "catalog.json",
        submission.DEFAULT_EXAMPLE / "source-policy.json",
        submission.DEFAULT_CUSTOMER,
        expected,
    )
    if change == "document":
        (expected / "intake-report.md").write_text("Changed report content.\n", encoding="utf-8")
    elif change in {"missing_time", "invalid_time"}:
        package_path = expected / "package.json"
        package = json.loads(package_path.read_text(encoding="utf-8"))
        metadata = package["package"]["reportMetadata"]
        if change == "missing_time":
            del metadata["generatedAt"]
        else:
            metadata["generatedAt"] = "not-a-time"
        package_path.write_text(json.dumps(package), encoding="utf-8")
    monkeypatch.setattr(submission, "PROJECT_ROOT", tmp_path)
    readiness = submission.Readiness(release_mode=False)

    submission.validate_expected_package(readiness)

    if change == "none":
        assert not readiness.findings
        assert readiness.passed_checks == ["deterministic_package:23_artifacts"]
    else:
        assert len(readiness.findings) == 1
        assert readiness.findings[0].check == "deterministic_package"
        assert not readiness.passed_checks


@pytest.mark.parametrize("suffix", [".html", ".js", ".css"])
def test_submission_scans_presentation_sources(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, suffix: str
) -> None:
    presentation_file = tmp_path / f"presentation{suffix}"
    unapproved_address = "@".join(("synthetic.person", "unapproved.example"))
    presentation_file.write_text(f"Contact: {unapproved_address}", encoding="utf-8")
    monkeypatch.setattr(submission, "PROJECT_ROOT", tmp_path)

    readiness = submission.Readiness(release_mode=False)
    submission.validate_content_safety(readiness)

    assert any(finding.check == "content_safety" for finding in readiness.findings)


@pytest.mark.parametrize("value", ["not a URL", "http://github.com/test", "https://mosaic.example"])
def test_invalid_submission_destinations_are_rejected(value: str) -> None:
    readiness = submission.Readiness(release_mode=True)

    submission.validate_submission_urls(
        readiness, {"fields": [{"number": number, "response": value} for number in (2, 3, 4)]}
    )

    assert len(readiness.findings) == 3
    assert not readiness.passed_checks


def test_internal_contest_reference_is_not_a_submission_artifact(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    reference = tmp_path / "docs" / "contest-info.json"
    reference.parent.mkdir()
    reference.write_text("Private local source, not a submitted JSON artifact.", encoding="utf-8")
    monkeypatch.setattr(submission, "PROJECT_ROOT", tmp_path)
    readiness = submission.Readiness(release_mode=True)

    submission.validate_json_files(readiness)

    assert list(submission.project_files()) == []
    assert not readiness.findings


def test_required_form_answers_cannot_be_omitted() -> None:
    readiness = submission.Readiness(release_mode=True)

    submission.validate_form_answers(readiness, {"fields": []})

    assert len(readiness.findings) == 3
    assert all(finding.check == "form_answers" for finding in readiness.findings)
    assert all(finding.severity == "error" for finding in readiness.findings)


@pytest.mark.parametrize("include_optional_field", [False, True])
def test_product_feedback_is_optional(include_optional_field: bool) -> None:
    fields = [
        {"number": 1, "response": "A synthetic enterprise workflow."},
        {"number": 5, "response": "A single competitive paragraph."},
        {"number": 7, "response": "synthetic@example.com"},
    ]
    if include_optional_field:
        fields.append({"number": 6, "response": ""})
    readiness = submission.Readiness(release_mode=True)

    submission.validate_form_answers(readiness, {"fields": fields})

    assert not readiness.findings
    assert readiness.passed_checks == ["form_answer:1", "form_answer:5", "form_answer:7"]


@pytest.mark.parametrize("feedback", ["", None])
def test_selected_feedback_bonus_cannot_be_blank(feedback: str | None) -> None:
    readiness = submission.Readiness(release_mode=True)

    submission.validate_form_answers(
        readiness,
        {
            "includeProductFeedback": True,
            "fields": [
                {"number": 1, "response": "A synthetic enterprise workflow."},
                {"number": 5, "response": "A single competitive paragraph."},
                {"number": 6, "response": feedback},
                {"number": 7, "response": "synthetic@example.com"},
            ],
        },
    )

    assert len(readiness.findings) == 1
    assert "selected product-feedback bonus" in readiness.findings[0].message
    assert readiness.findings[0].severity == "error"
    assert "form_answer:6" not in readiness.passed_checks


def test_submission_keeps_feedback_bonus_selected() -> None:
    directory = Path(__file__).parents[1] / "submission"
    form = json.loads((directory / "form-response.json").read_text(encoding="utf-8"))
    assert form["includeProductFeedback"] is True
    feedback_field = next(field for field in form["fields"] if field["number"] == 6)
    feedback = (directory / feedback_field["responseFile"]).read_text(encoding="utf-8")
    for heading in ("Strengths:", "Limitations encountered:", "Suggested improvement:"):
        assert heading in feedback
    readiness = submission.Readiness(release_mode=True)

    submission.validate_form_answers(readiness, form)

    assert not readiness.findings
    assert "form_answer:6" in readiness.passed_checks


def test_competitive_response_must_be_one_paragraph() -> None:
    readiness = submission.Readiness(release_mode=True)

    submission.validate_form_answers(
        readiness,
        {
            "fields": [
                {"number": 1, "response": "A synthetic enterprise workflow."},
                {"number": 5, "response": "First paragraph.\n\nSecond paragraph."},
                {"number": 7, "response": "synthetic@example.com"},
            ]
        },
    )

    assert len(readiness.findings) == 1
    assert readiness.findings[0].check == "competitive_positioning"


@pytest.mark.parametrize("page_count", [1, 2, 3])
def test_private_entry_needs_no_external_license_or_approval_form(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, page_count: int
) -> None:
    presentation = tmp_path / "presentation"
    captures = presentation / "assets"
    captures.mkdir(parents=True)
    (captures / "copilot-app-test.png").touch()
    with zipfile.ZipFile(presentation / "mosaic-challenge-deck.pptx", "w") as archive:
        for slide in range(1, page_count + 1):
            archive.writestr(f"ppt/slides/slide{slide}.xml", "<slide/>")
    (presentation / "mosaic-challenge-deck.pdf").write_bytes(
        b"%PDF-1.4\n" + b"/Type /Page\n" * page_count
    )
    (tmp_path / "README.md").write_text("Private challenge entry.", encoding="utf-8")
    (tmp_path / "LICENSE").write_text("CHALLENGE EVALUATION NOTICE", encoding="utf-8")
    form_directory = tmp_path / "submission"
    form_directory.mkdir()
    (form_directory / "competitive.txt").write_text("One competitive paragraph.", encoding="utf-8")
    fields = [
        {"number": 1, "response": "A synthetic enterprise workflow."},
        {"number": 5, "responseFile": "competitive.txt"},
        {"number": 7, "response": "synthetic@example.com"},
        *[
            {"number": number, "response": "https://github.com/example/mosaic"}
            for number in (2, 3, 4)
        ],
    ]
    (form_directory / "form-response.json").write_text(
        json.dumps({"fields": fields}), encoding="utf-8"
    )
    monkeypatch.setattr(submission, "PROJECT_ROOT", tmp_path)
    readiness = submission.Readiness(release_mode=True)

    submission.validate_media_and_urls(readiness)

    assert not readiness.findings
    assert f"deck_slide_count:{page_count}" in readiness.passed_checks
    assert f"deck_pdf_page_count:{page_count}" in readiness.passed_checks
