# SPDX-License-Identifier: LicenseRef-MOSAIC-Evaluation
"""Validate and render locally captured intake history, never model-authored history."""

from __future__ import annotations

import json
import re
from datetime import UTC, datetime
from typing import Any

from jsonschema import Draft202012Validator

from mosaic.schema_validation import SCHEMA_DIRECTORY


def validate_transcript(transcript: dict[str, Any], initiative_id: str) -> None:
    schema = json.loads(
        (SCHEMA_DIRECTORY / "intake-request.schema.json").read_text(
            encoding="utf-8",
        )
    )["properties"]["intakeTranscript"]
    validator = Draft202012Validator(schema, format_checker=Draft202012Validator.FORMAT_CHECKER)
    error = next(validator.iter_errors(transcript), None)
    if error:
        raise ValueError(f"Intake transcript is invalid: {error.message}")
    if transcript["initiativeId"] != initiative_id:
        raise ValueError("Intake transcript belongs to another initiative.")
    entries = transcript["entries"]
    started_at, ended_at = transcript.get("startedAt"), transcript.get("endedAt")
    if ended_at and (not entries or entries[-1]["kind"] != "generation_approval"):
        raise ValueError("Transcript end time requires a final generation approval.")
    if (
        started_at
        and ended_at
        and datetime.fromisoformat(ended_at)
        < datetime.fromisoformat(
            started_at,
        )
    ):
        raise ValueError("Transcript end time cannot precede its start time.")
    if started_at and transcript["captureStatus"] == "complete" and not ended_at:
        raise ValueError("A completed timed transcript requires an end time.")
    if transcript["captureStatus"] == "not_recorded" and (started_at or ended_at):
        raise ValueError("An unrecorded transcript cannot claim session times.")
    for sequence, entry in enumerate(entries, 1):
        if entry["sequence"] != sequence:
            raise ValueError("Intake transcript sequences must be contiguous and chronological.")
        reply_to = entry["replyTo"]
        if reply_to is not None and not 0 < reply_to < sequence:
            raise ValueError("Intake transcript replies must reference an earlier entry.")
        if entry["kind"] in {"question", "generation_plan"} and entry["role"] != "assistant":
            raise ValueError("Intake questions and generation plans must be assistant entries.")
        if entry["kind"] in {"question", "generation_plan"} and not entry["text"]:
            raise ValueError("Record the actual question or generation plan text.")
        if (
            entry["kind"] in {"answer", "correction", "generation_approval", "control"}
            and entry["role"] != "user"
        ):
            raise ValueError("Intake answers and controls must be user entries.")
        if not set(entry.get("optionDescriptions", {})).issubset(entry["options"]):
            raise ValueError("Choice descriptions must match their recorded option labels.")
        if (entry["selected"] or entry.get("controls")) and entry["role"] != "user":
            raise ValueError("Only user entries can record selected choices or controls.")
        if entry["selected"] and reply_to is not None:
            target = entries[reply_to - 1]
            if target["kind"] not in {"question", "generation_plan"}:
                raise ValueError("Selected choices must reference a question or generation plan.")
        if entry.get("controls") and reply_to is not None:
            target = entries[reply_to - 1]
            allowed_target = target["kind"] in {"question", "generation_plan"} or (
                target["kind"] == "message" and target["role"] == "assistant" and target["options"]
            )
            if not allowed_target:
                raise ValueError("Controls must reference an option-bearing assistant prompt.")
        if entry["selected"] and (
            reply_to is None
            or not set(entry["selected"]).issubset(entries[reply_to - 1]["options"])
        ):
            raise ValueError("Selected transcript choices must match their recorded question.")
        if (
            entry.get("controls")
            and reply_to is not None
            and not set(entry["controls"]).issubset(entries[reply_to - 1]["options"])
        ):
            raise ValueError("Transcript controls must match their recorded prompt.")
        if set(entry["selected"]) & {
            "End intake and generate report",
            "Generate documentation now",
        }:
            raise ValueError(
                "Record end-intake generation choices as controls, not business answers."
            )
        if entry["kind"] == "generation_approval" and (
            reply_to is None or entries[reply_to - 1]["kind"] != "generation_plan"
        ):
            raise ValueError("Generation approval must reference its recorded generation plan.")
    if transcript["captureStatus"] == "not_recorded" and entries:
        raise ValueError("A not-recorded transcript cannot contain reconstructed entries.")
    if transcript["captureStatus"] == "complete" and (
        not entries
        or transcript["gaps"]
        or any(entry["fidelity"] != "verbatim" for entry in entries)
        or entries[-1]["kind"] != "generation_approval"
    ):
        raise ValueError("Complete capture requires verbatim history through generation approval.")


def missing_transcript(initiative_id: str) -> dict[str, Any]:
    return {
        "schemaVersion": "1.0.0",
        "initiativeId": initiative_id,
        "classification": "SYNTHETIC",
        "captureStatus": "not_recorded",
        "gaps": [
            "No intake transcript was recorded for this input. No dialogue was reconstructed.",
        ],
        "entries": [],
    }


def transcript_turns(
    transcript: dict[str, Any], submitted_by: str = "John Doe"
) -> list[dict[str, Any]]:
    """Project captured entries for display without changing or inventing conversation data."""
    speakers = {
        entry["sequence"]: submitted_by if entry["role"] == "user" else "MOSAIC"
        for entry in transcript["entries"]
    }
    answered = {
        entry["replyTo"]
        for entry in transcript["entries"]
        if entry["kind"] in {"answer", "correction"} and (entry["text"] or entry["selected"])
    }
    labels = {
        "correction": "Correction",
        "summary": "Intake summary",
        "generation_plan": "Generation plan",
        "generation_approval": "Generation approval",
        "control": "Action",
    }
    return [
        {
            **entry,
            "speaker": speakers[entry["sequence"]],
            "label": labels.get(entry["kind"]),
            "replySpeaker": speakers.get(entry["replyTo"]),
            "unanswered": entry["kind"] == "question" and entry["sequence"] not in answered,
        }
        for entry in transcript["entries"]
    ]


def render_transcript(transcript: dict[str, Any], submitted_by: str = "John Doe") -> str:
    def display_time(value: str | None) -> str:
        if value is None:
            return "Not recorded"
        return datetime.fromisoformat(value).astimezone(UTC).strftime("%d %b %Y, %H:%M:%S UTC")

    def display_name(value: str) -> str:
        return re.sub(r"([\\`*{}\[\]<>()#+.!_|~-])", r"\\\1", " ".join(value.splitlines()))

    def literal(text: str) -> str:
        fence = "~" * max(3, max((len(run) + 1 for run in re.findall(r"~+", text)), default=0))
        return f"{fence}transcript\n{text}\n{fence}"

    started_at, ended_at = transcript.get("startedAt"), transcript.get("endedAt")
    lines = [
        "# Intake Transcript",
        "",
        "## Session",
        "",
        f"**Participants:** {display_name(submitted_by)} and MOSAIC",
        "",
        f"**Capture:** {transcript['captureStatus'].replace('_', ' ').title()}",
        "",
    ]
    if started_at:
        lines.extend([f"**Started:** {display_time(started_at)}  ", ""])
    if ended_at:
        lines.extend([f"**Ended:** {display_time(ended_at)}", ""])
    elif started_at and transcript["captureStatus"] == "partial":
        lines.extend(["**Ended:** In progress", ""])
    lines.extend(
        [
            "Messages are verbatim unless marked as a summary. Session dates describe capture, "
            "not original message times. Display names are not verified identities.",
            "",
            "Generation approval covers document creation only, not architecture selection "
            "or design approval.",
            "",
            "[Structured transcript](intake-transcript.json)",
        ]
    )
    if transcript["gaps"]:
        lines.extend(["", "### Missing History", ""])
        lines.extend(literal(gap) for gap in transcript["gaps"])
    if transcript["entries"]:
        lines.extend(["", "## Conversation"])
    for entry in transcript_turns(transcript, submitted_by):
        lines.extend(
            [
                "",
                f"### {entry['sequence']}. {display_name(entry['speaker'])}",
                "",
            ]
        )
        if entry["label"]:
            lines.extend([f"**{entry['label']}**", ""])
        if entry["fidelity"] == "summary":
            lines.extend(["**Summary:** This entry is not a verbatim message.", ""])
        if entry["replyTo"] is not None:
            lines.extend(
                [
                    f"**Reply to:** {display_name(entry['replySpeaker'])}, "
                    f"message {entry['replyTo']}",
                    "",
                ]
            )
        if entry["timestamp"]:
            lines.extend([f"**Message time:** {display_time(entry['timestamp'])}", ""])
        if entry["text"] is not None:
            lines.append(literal(entry["text"]))
        if entry.get("context"):
            lines.extend(["", literal(entry["context"])])
        for name, title in (
            ("options", "Choices offered"),
            (
                "selected",
                "Approval" if entry["kind"] == "generation_approval" else "Selected",
            ),
            ("controls", "Action"),
        ):
            if entry.get(name):
                if name == "options" or entry["text"] or (name == "controls" and entry["selected"]):
                    lines.extend(["", f"**{title}:**", ""])
                for value in entry[name]:
                    lines.append(literal(value))
                    if name == "options" and entry.get("optionDescriptions", {}).get(value):
                        lines.extend(["", literal(entry["optionDescriptions"][value])])
        if entry["unanswered"]:
            lines.extend(["", "**Unanswered.**"])
    return "\n".join(lines) + "\n"
