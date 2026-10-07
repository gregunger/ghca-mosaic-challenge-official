# SPDX-License-Identifier: LicenseRef-MOSAIC-Evaluation
"""Validate local contest assets and required form answers, not publication approval."""

from __future__ import annotations

import argparse
import json
import re
import sys
import tempfile
import zipfile
from collections.abc import Iterable, Sequence
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from unittest.mock import patch
from urllib.parse import unquote, urlsplit

from markdown_it import MarkdownIt

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from mosaic.cli import DEFAULT_CUSTOMER, DEFAULT_EXAMPLE, run_demo  # noqa: E402

TEXT_SUFFIXES = {
    "",
    ".css",
    ".example",
    ".html",
    ".j2",
    ".js",
    ".json",
    ".md",
    ".ps1",
    ".py",
    ".sh",
    ".toml",
    ".tpl",
    ".txt",
    ".vtt",
    ".yaml",
    ".yml",
}
EXCLUDED_DIRECTORIES = {
    ".git",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "__pycache__",
    "build",
    "demo-output",
    "dist",
    "node_modules",
    "recordings",
    "rendered",
}
EXCLUDED_FILES = {".mcp.json", "docs/contest-info.json"}
CONTEST_ACCEPTANCE_IDS = {f"CR-{number:02}" for number in range(1, 18)}
ALLOWED_EMAILS = {"gregunger@microsoft.com"}
ALLOWED_ABSOLUTE_PATH_FILES = {"tests/test_mcp_server.py"}
SCANNER_DEFINITION_FILES = {"scripts/validate_submission.py"}
REQUIRED_README_HEADINGS = {
    "## The Enterprise Problem",
    "## Eight-Stage Workflow",
    "## GitHub Copilot App Pattern",
    "## Roles And Decision Rights",
    "## Prerequisites",
    "## Five-Minute Quick Start",
    "## App Customizations",
    "## Inputs And Outputs",
    "## Governance, Security, Privacy, And Responsible AI",
    "## Customer Portability",
    "## Success Measures",
    "## Tests And Validation",
    "## Repository Structure",
    "## Demo And Submission Assets",
    "## Limitations And Non-Goals",
    "## Troubleshooting",
    "## Originality And Attribution",
    "## Adoption And Release Model",
}
REQUIRED_PATHS = {
    "README.md",
    "CONTRIBUTING.md",
    ".editorconfig",
    ".prettierrc.json",
    ".prettierignore",
    "SECURITY.md",
    "NOTICE.md",
    "LICENSE",
    ".github/copilot-instructions.md",
    ".github/mcp.json",
    ".github/agents/mosaic-orchestrator.agent.md",
    ".github/skills/mosaic-intake/SKILL.md",
    ".github/skills/run-mosaic-intake/SKILL.md",
    ".github/skills/review-mosaic-package/SKILL.md",
    ".github/skills/refresh-mosaic-evidence/SKILL.md",
    ".github/prompts/run-mosaic-intake.prompt.md",
    ".github/ISSUE_TEMPLATE/mosaic-intake.yml",
    ".github/pull_request_template.md",
    ".vscode/mcp.json",
    "config/customers/contoso-public-services.synthetic.json",
    "examples/synthetic/request.json",
    "examples/synthetic/source-policy.json",
    "examples/synthetic/expected/package.json",
    "examples/synthetic/expected/validation-report.json",
    "docs/architecture.md",
    "docs/governance-and-rai.md",
    "docs/adoption-playbook.md",
    "docs/evaluation-plan.md",
    "docs/demo-runbook.md",
    "submission/project-summary.txt",
    "submission/competitive-positioning.txt",
    "submission/form-response.json",
    "submission/OPEN-ITEMS.md",
    "package-lock.json",
    "package.json",
    "presentation/build_deck.js",
    "presentation/mosaic-challenge-deck.html",
    "presentation/mosaic-challenge-deck.pdf",
    "presentation/mosaic-challenge-deck.pptx",
    "presentation/mosaic-output.png",
    "presentation/assets/copilot-app-session.png",
    "presentation/assets/copilot-app-detail.png",
    "video/README.md",
    "video/shot-list.md",
    "video/recording-checklist.md",
}


@dataclass(frozen=True)
class Finding:
    severity: str
    check: str
    message: str
    path: str | None = None


class Readiness:
    def __init__(self, release_mode: bool) -> None:
        self.release_mode = release_mode
        self.findings: list[Finding] = []
        self.passed_checks: list[str] = []

    def pass_check(self, name: str) -> None:
        self.passed_checks.append(name)

    def error(self, check: str, message: str, path: Path | str | None = None) -> None:
        self.findings.append(Finding("error", check, message, relative(path)))

    def human_action(self, check: str, message: str, path: Path | str | None = None) -> None:
        severity = "error" if self.release_mode else "human-action"
        self.findings.append(Finding(severity, check, message, relative(path)))


def relative(path: Path | str | None) -> str | None:
    if path is None:
        return None
    value = Path(path)
    try:
        return value.resolve().relative_to(PROJECT_ROOT).as_posix()
    except (OSError, ValueError):
        return str(path)


def project_files() -> Iterable[Path]:
    """Yield maintained artifacts, excluding private state and generated install metadata."""
    for path in PROJECT_ROOT.rglob("*"):
        if not path.is_file():
            continue
        relative_path = path.relative_to(PROJECT_ROOT)
        if relative_path.as_posix() in EXCLUDED_FILES:
            continue
        if any(
            part in EXCLUDED_DIRECTORIES or part.endswith(".egg-info")
            for part in relative_path.parts
        ):
            continue
        if (path.name == ".env" or path.name.startswith(".env.")) and path.name not in {
            ".env.example",
            ".env.sample",
        }:
            continue
        yield path


def text_files() -> Iterable[Path]:
    for path in project_files():
        if path.suffix.lower() in TEXT_SUFFIXES or path.name == "LICENSE":
            yield path


def validate_required_paths(readiness: Readiness) -> None:
    missing = sorted(path for path in REQUIRED_PATHS if not (PROJECT_ROOT / path).exists())
    if missing:
        for path in missing:
            readiness.error("required_paths", "Required repository artifact is missing.", path)
        return
    readiness.pass_check("required_paths")


def validate_json_files(readiness: Readiness) -> None:
    failures = 0
    for path in project_files():
        if path.suffix.lower() != ".json":
            continue
        try:
            with path.open(encoding="utf-8") as stream:
                json.load(stream)
        except (OSError, json.JSONDecodeError) as error:
            failures += 1
            readiness.error("json_parse", str(error), path)
    if failures == 0:
        readiness.pass_check("json_parse")


def validate_readme(readiness: Readiness) -> None:
    path = PROJECT_ROOT / "README.md"
    content = path.read_text(encoding="utf-8")
    missing = sorted(REQUIRED_README_HEADINGS - set(content.splitlines()))
    if missing:
        readiness.error("readme_sections", f"Missing headings: {', '.join(missing)}", path)
    else:
        readiness.pass_check("readme_sections")


def validate_summary(readiness: Readiness) -> None:
    path = PROJECT_ROOT / "submission" / "project-summary.txt"
    words = re.findall(r"\b[\w'-]+\b", path.read_text(encoding="utf-8"))
    if len(words) > 150:
        readiness.error(
            "project_summary_limit", f"Summary has {len(words)} words; limit is 150.", path
        )
    elif not words:
        readiness.error("project_summary_limit", "Summary is empty.", path)
    else:
        readiness.pass_check(f"project_summary_limit:{len(words)}_words")


def validate_acceptance_register(readiness: Readiness) -> None:
    """Surface declared contest gaps without treating a local check as human approval."""
    path = PROJECT_ROOT / "submission" / "OPEN-ITEMS.md"
    try:
        tokens = MarkdownIt("commonmark").enable("table").parse(path.read_text(encoding="utf-8"))
    except OSError as error:
        readiness.error("contest_acceptance_register", str(error), path)
        return
    rows: list[list[str]] = []
    current_row: list[str] | None = None
    for token in tokens:
        if token.type == "tr_open":
            current_row = []
        elif token.type == "inline" and current_row is not None:
            current_row.append(token.content.strip())
        elif token.type == "tr_close":
            if current_row and current_row[0].startswith("CR-"):
                rows.append(current_row)
            current_row = None
    identifiers = [row[0] for row in rows]
    if set(identifiers) != CONTEST_ACCEPTANCE_IDS or len(identifiers) != len(set(identifiers)):
        readiness.error(
            "contest_acceptance_register",
            "The register must contain each requirement CR-01 through CR-17 exactly once.",
            path,
        )
        return
    if any(
        len(row) != 4 or not row[1] or not row[3] or row[2] not in {"Passed", "Pending", "Blocked"}
        for row in rows
    ):
        readiness.error(
            "contest_acceptance_register",
            "Every requirement needs its description, Passed/Pending/Blocked state and evidence.",
            path,
        )
        return
    readiness.pass_check(f"contest_acceptance_register:{len(rows)}_requirements")
    for identifier, requirement, state, _evidence in rows:
        if state == "Passed":
            readiness.pass_check(f"declared_contest_requirement:{identifier}")
        elif state != "Passed":
            readiness.human_action(
                "contest_acceptance",
                f"{identifier} {state.lower()}: {requirement}.",
                path,
            )


def validate_frontmatter(readiness: Readiness) -> None:
    files = [
        *sorted((PROJECT_ROOT / ".github" / "agents").glob("*.agent.md")),
        *sorted((PROJECT_ROOT / ".github" / "prompts").glob("*.prompt.md")),
        PROJECT_ROOT / ".github" / "skills" / "mosaic-intake" / "SKILL.md",
    ]
    failures = 0
    for path in files:
        content = path.read_text(encoding="utf-8")
        if not content.startswith("---\n") or "\n---\n" not in content[4:]:
            failures += 1
            readiness.error(
                "customization_frontmatter", "Missing YAML frontmatter delimiters.", path
            )
            continue
        frontmatter = content.split("---", 2)[1]
        if not re.search(r"(?m)^description:\s*.+$", frontmatter):
            failures += 1
            readiness.error("customization_frontmatter", "Missing description field.", path)
        if path.name == "SKILL.md" and "name: mosaic-intake" not in frontmatter:
            failures += 1
            readiness.error("customization_frontmatter", "Skill name must match its folder.", path)
    if failures == 0:
        readiness.pass_check(f"customization_frontmatter:{len(files)}_files")


def validate_local_links(readiness: Readiness) -> None:
    failures = 0
    link_pattern = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
    for path in text_files():
        if path.suffix.lower() not in {".md", ".tpl"}:
            continue
        content = path.read_text(encoding="utf-8")
        for target in link_pattern.findall(content):
            target = target.strip().split("#", 1)[0]
            if not target or re.match(r"^(?:https?://|mailto:)", target):
                continue
            destination = (path.parent / unquote(target)).resolve()
            try:
                destination.relative_to(PROJECT_ROOT)
            except ValueError:
                failures += 1
                readiness.error("local_links", f"Link escapes the repository: {target}", path)
                continue
            if not destination.exists():
                failures += 1
                readiness.error("local_links", f"Link target does not exist: {target}", path)
    if failures == 0:
        readiness.pass_check("local_links")


def validate_content_safety(readiness: Readiness) -> None:
    failures = 0
    prohibited = {
        "restricted_customer_identifier": re.compile(r"\b(?:VA|Veterans Affairs)\b", re.IGNORECASE),
        "controlled_marking": re.compile(r"\bCUI\b", re.IGNORECASE),
        "secret_token": re.compile(
            r"(?:github_pat_|ghp_[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{16}|"
            r"BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY)"
        ),
        "tenant_guid": re.compile(
            r"\b[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}\b",
            re.IGNORECASE,
        ),
    }
    email_pattern = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE)
    windows_path_pattern = re.compile(r"(?<![A-Za-z0-9])(?:[A-Za-z]:\\\\|[A-Za-z]:\\)[^\s\"']+")

    for path in text_files():
        content = path.read_text(encoding="utf-8", errors="strict")
        relative_path = path.relative_to(PROJECT_ROOT).as_posix()
        if relative_path not in SCANNER_DEFINITION_FILES:
            for name, pattern in prohibited.items():
                if pattern.search(content):
                    failures += 1
                    readiness.error("content_safety", f"Matched {name} pattern.", path)
        for email in email_pattern.findall(content):
            if email.lower() not in ALLOWED_EMAILS and not email.lower().endswith("@example.com"):
                failures += 1
                readiness.error("content_safety", f"Unapproved email address: {email}", path)
        if relative_path not in ALLOWED_ABSOLUTE_PATH_FILES and windows_path_pattern.search(
            content
        ):
            failures += 1
            readiness.error("content_safety", "Absolute Windows path found.", path)
    if failures == 0:
        readiness.pass_check("content_safety")


def validate_expected_package(readiness: Readiness) -> None:
    """Compare the reference bytes using its recorded report-rendering time."""
    expected = PROJECT_ROOT / "examples" / "synthetic" / "expected"
    catalog = DEFAULT_EXAMPLE / "sources" / "catalog.json"
    try:
        recorded = json.loads((expected / "package.json").read_text(encoding="utf-8"))
        generated_at = recorded["package"]["reportMetadata"]["generatedAt"]
        if not isinstance(generated_at, str) or not generated_at.endswith("Z"):
            raise ValueError("Report-generation time must be recorded in UTC.")
        report_time = datetime.fromisoformat(generated_at)
    except (OSError, KeyError, TypeError, ValueError) as error:
        readiness.error(
            "deterministic_package",
            f"Refresh the canonical reference with the current CLI: {error}",
            expected,
        )
        return
    with (
        tempfile.TemporaryDirectory(prefix="mosaic-validation-") as directory,
        patch("mosaic.render.datetime", wraps=datetime) as render_clock,
    ):
        render_clock.now.return_value = report_time
        generated = Path(directory)
        summary = run_demo(
            DEFAULT_EXAMPLE / "request.json",
            catalog,
            DEFAULT_EXAMPLE / "source-policy.json",
            DEFAULT_CUSTOMER,
            generated,
        )
        expected_names = sorted(path.name for path in expected.iterdir() if path.is_file())
        generated_names = sorted(path.name for path in generated.iterdir() if path.is_file())
        if expected_names != generated_names:
            readiness.error(
                "deterministic_package",
                f"Artifact sets differ: expected {expected_names}, generated {generated_names}.",
                expected,
            )
            return
        differences = [
            name
            for name in expected_names
            if (expected / name).read_bytes() != (generated / name).read_bytes()
        ]
        if differences:
            readiness.error(
                "deterministic_package",
                f"Canonical outputs differ: {', '.join(differences)}.",
                expected,
            )
            return
        if summary["validation"] != "pass" or summary["state"] != "awaiting_human_review":
            readiness.error(
                "deterministic_package", "Generated package did not pass in blocked state."
            )
            return
    readiness.pass_check(f"deterministic_package:{len(expected_names)}_artifacts")


def deck_slide_count(path: Path) -> int:
    with zipfile.ZipFile(path) as archive:
        return len(
            [
                name
                for name in archive.namelist()
                if re.fullmatch(r"ppt/slides/slide[0-9]+\.xml", name)
            ]
        )


def pdf_page_count(path: Path) -> int:
    content = path.read_bytes()
    if not content.startswith(b"%PDF-"):
        raise ValueError("File does not have a PDF header.")
    return len(re.findall(rb"/Type\s*/Page\b", content))


def validate_submission_urls(readiness: Readiness, form: dict[str, Any]) -> None:
    fields = {field.get("number"): field for field in form.get("fields", [])}
    for number in (2, 3, 4):
        value = str(fields.get(number, {}).get("response", "")).strip()
        if not value or "<REQUIRED_HUMAN_INPUT:" in value:
            readiness.human_action("submission_urls", f"Form URL field {number} is unresolved.")
            continue
        try:
            parsed = urlsplit(value)
            hostname = parsed.hostname or ""
            valid = (
                parsed.scheme == "https"
                and "." in hostname
                and not hostname.endswith((".example", ".invalid", ".test", ".localhost"))
                and hostname not in {"example.com", "example.org", "example.net", "127.0.0.1"}
                and not parsed.username
                and not parsed.password
                and not any(character.isspace() for character in value)
            )
        except ValueError:
            valid = False
        if valid:
            readiness.pass_check(f"submission_url_syntax:{number}")
        else:
            readiness.error("submission_urls", f"Form field {number} requires a real HTTPS URL.")


def validate_form_answers(readiness: Readiness, form: dict[str, Any]) -> None:
    fields = {field.get("number"): field for field in form.get("fields", [])}
    submission_directory = (PROJECT_ROOT / "submission").resolve()
    selected_fields = (1, 5, 6, 7) if form.get("includeProductFeedback") else (1, 5, 7)
    for number in selected_fields:
        field = fields.get(number, {})
        response = field.get("response")
        answer = response.strip() if isinstance(response, str) else ""
        path = submission_directory / "form-response.json"
        if not answer and field.get("responseFile"):
            path = (submission_directory / field["responseFile"]).resolve()
            if not path.is_relative_to(submission_directory):
                readiness.error("form_answers", "Answer file escapes the submission directory.")
                continue
            try:
                answer = path.read_text(encoding="utf-8").strip()
            except OSError as error:
                readiness.error("form_answers", f"Cannot read form field {number}: {error}", path)
                continue
        if not answer or "<REQUIRED_HUMAN_INPUT:" in answer:
            message = (
                "The selected product-feedback bonus needs a nonempty answer."
                if number == 6
                else f"Required form field {number} is empty."
            )
            readiness.human_action("form_answers", message, path)
        elif number == 1 and len(re.findall(r"\b[\w'-]+\b", answer)) > 150:
            readiness.error("form_answers", "Project summary must be at most 150 words.", path)
        elif number == 5 and len(re.split(r"\n\s*\n", answer)) != 1:
            readiness.error(
                "competitive_positioning", "Competitive response must be one paragraph.", path
            )
        else:
            readiness.pass_check(f"form_answer:{number}")


def validate_media_and_urls(readiness: Readiness) -> None:
    deck = PROJECT_ROOT / "presentation" / "mosaic-challenge-deck.pptx"
    if not deck.exists():
        readiness.human_action("deck", "Generate and visually inspect the three-slide deck.", deck)
    else:
        try:
            count = deck_slide_count(deck)
        except (OSError, zipfile.BadZipFile) as error:
            readiness.error("deck", f"Deck cannot be read: {error}", deck)
        else:
            if not 1 <= count <= 3:
                readiness.error("deck", f"Deck has {count} slides; allowed range is 1-3.", deck)
            else:
                readiness.pass_check(f"deck_slide_count:{count}")

    pdf = PROJECT_ROOT / "presentation" / "mosaic-challenge-deck.pdf"
    if pdf.exists():
        try:
            count = pdf_page_count(pdf)
        except (OSError, ValueError) as error:
            readiness.error("deck_pdf", f"Deck PDF cannot be read: {error}", pdf)
        else:
            if not 1 <= count <= 3:
                readiness.error(
                    "deck_pdf", f"Deck PDF has {count} pages; allowed range is 1-3.", pdf
                )
            else:
                readiness.pass_check(f"deck_pdf_page_count:{count}")

    app_captures = list((PROJECT_ROOT / "presentation" / "assets").glob("copilot-app-*.png"))
    if not app_captures:
        readiness.human_action(
            "app_capture", "Authentic release-safe Copilot App capture is required."
        )
    else:
        readiness.pass_check(f"app_capture_files_present:{len(app_captures)}")

    form_path = PROJECT_ROOT / "submission" / "form-response.json"
    form = json.loads(form_path.read_text(encoding="utf-8"))
    validate_submission_urls(readiness, form)
    validate_form_answers(readiness, form)

    readme_path = PROJECT_ROOT / "README.md"
    if "<FINAL_REPOSITORY_URL>" in readme_path.read_text(encoding="utf-8"):
        readiness.human_action("repository_url", "README clone URL is unresolved.", readme_path)
    else:
        readiness.pass_check("repository_url")


def build_report(release_mode: bool) -> tuple[dict[str, object], int]:
    readiness = Readiness(release_mode)
    validate_required_paths(readiness)
    validate_json_files(readiness)
    validate_readme(readiness)
    validate_summary(readiness)
    validate_acceptance_register(readiness)
    validate_frontmatter(readiness)
    validate_local_links(readiness)
    validate_content_safety(readiness)
    validate_expected_package(readiness)
    validate_media_and_urls(readiness)

    errors = [finding for finding in readiness.findings if finding.severity == "error"]
    human_actions = [
        finding for finding in readiness.findings if finding.severity == "human-action"
    ]
    status = "fail" if errors else "pass-with-human-actions" if human_actions else "pass"
    report: dict[str, object] = {
        "schemaVersion": "1.0.0",
        "generatedAt": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "mode": "release" if release_mode else "local",
        "scope": (
            "Local files and declared contest checklist state; native App execution, rights, "
            "team eligibility, judge access and actual submission are not independently verified."
        ),
        "status": status,
        "passedChecks": sorted(readiness.passed_checks),
        "findings": [asdict(finding) for finding in readiness.findings],
        "summary": {
            "passed": len(readiness.passed_checks),
            "errors": len(errors),
            "humanActions": len(human_actions),
        },
    }
    return report, 1 if errors else 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--release",
        action="store_true",
        help="Fail when a required local check or recorded contest acceptance item is unresolved.",
    )
    parser.add_argument("--output", type=Path, help="Optionally write the JSON report to a file.")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    report, exit_code = build_report(args.release)
    rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.output:
        output_path = args.output if args.output.is_absolute() else PROJECT_ROOT / args.output
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(rendered, encoding="utf-8", newline="\n")
    print(rendered, end="")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
