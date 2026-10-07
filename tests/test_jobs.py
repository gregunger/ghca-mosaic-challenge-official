# SPDX-License-Identifier: LicenseRef-MOSAIC-Evaluation
"""Exercise local job integrity, bounded analysis, capture, recovery and browser handoff."""

import json
import os
import sys
import threading
from concurrent.futures import ThreadPoolExecutor
from contextlib import nullcontext
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from time import perf_counter
from types import SimpleNamespace

import pytest
import yaml
from jinja2 import UndefinedError
from markdown_it import MarkdownIt

from mosaic import copilot_runner, jobs
from mosaic.cli import DEFAULT_CUSTOMER, DEFAULT_EXAMPLE, PROJECT_ROOT
from mosaic.copilot_runner import CopilotLimits, restricted_command, restricted_environment
from mosaic.jobs import JobStore
from mosaic.observability import OPERATOR_FILES, provider_observations
from mosaic.stages import design, option


def queue(store: JobStore, **kwargs) -> dict:
    return store.submit(
        DEFAULT_EXAMPLE / "request.json",
        DEFAULT_EXAMPLE / "sources/catalog.json",
        DEFAULT_EXAMPLE / "source-policy.json",
        DEFAULT_CUSTOMER,
        reference=True,
        notify=False,
        **kwargs,
    )


def transcript_entry(sequence: int, role: str, kind: str, text: str | None, **kwargs) -> dict:
    return {
        "sequence": sequence,
        "role": role,
        "kind": kind,
        "text": text,
        "fidelity": "verbatim",
        "timestamp": None,
        "replyTo": None,
        "options": [],
        "selected": [],
        **kwargs,
    }


def deferred_transcript_entries() -> list[dict]:
    return [
        transcript_entry(1, "assistant", "question", "What business problem needs solving?"),
        transcript_entry(
            2, "user", "answer", "Travel policy is hard to find.\n  Keep this wording.", replyTo=1
        ),
        transcript_entry(
            3,
            "assistant",
            "question",
            "Who needs this first?",
            options=["End intake and generate report", "Field employees"],
            optionDescriptions={"Field employees": "People submitting travel claims."},
        ),
        transcript_entry(4, "user", "answer", None, replyTo=3, selected=["Field employees"]),
        transcript_entry(5, "user", "correction", "Correction: 250 field employees, not 200."),
        transcript_entry(
            6,
            "assistant",
            "question",
            "Which delivery date matters?",
            options=["End intake and generate report", "15 October; year unconfirmed"],
        ),
        transcript_entry(
            7,
            "user",
            "control",
            None,
            replyTo=6,
            controls=["End intake and generate report"],
        ),
        transcript_entry(
            8,
            "assistant",
            "generation_plan",
            "Generate a synthetic discussion draft only; no deployment or customer approval.",
        ),
        transcript_entry(9, "user", "generation_approval", "Yes, go ahead.", replyTo=8),
    ]


def app_shaped_transcript_entries() -> list[dict]:
    return [
        transcript_entry(
            1,
            "user",
            "control",
            "menu",
            controls=["Menu"],
        ),
        transcript_entry(
            2,
            "assistant",
            "message",
            "1. Submit a new intake request\n2. How it works",
            replyTo=1,
            options=["Submit a new intake request", "How it works"],
            optionDescriptions=["Share the business need.", "Review the process."],
        ),
        transcript_entry(
            3,
            "user",
            "control",
            "1",
            replyTo=2,
            controls=["Submit a new intake request"],
        ),
        transcript_entry(
            4,
            "assistant",
            "generation_plan",
            "Approve the bounded synthetic generation plan?",
            replyTo=3,
            options=["Approve and generate", "Do not generate"],
            optionDescriptions=[
                "Begin bounded generation.",
                "Do not generate documents.",
            ],
        ),
        transcript_entry(
            5,
            "user",
            "generation_approval",
            "1",
            replyTo=4,
            selected=["Approve and generate"],
        ),
    ]


@pytest.mark.parametrize("complete", [False, True])
def test_capture_batch_writes_once_and_preserves_exact_history(
    tmp_path: Path, monkeypatch, capsys, complete: bool
) -> None:
    initiative = "SYN-DEFERRED-CAPTURE"
    entries = deferred_transcript_entries()
    batch = tmp_path / "turns.json"
    batch.write_text(json.dumps({"entries": entries}), encoding="utf-8")
    root = tmp_path / "jobs"
    path = root / initiative / "intake-transcript.json"
    write = jobs._write_json
    writes = []

    def counted_write(destination, value):
        writes.append(destination)
        return write(destination, value)

    def unexpected(*args, **kwargs):
        pytest.fail("Capture must not perform analysis, acquire sources or generate documents")

    monkeypatch.setattr(jobs, "_write_json", counted_write)
    monkeypatch.setattr(jobs, "run_copilot", unexpected)
    monkeypatch.setattr(jobs, "run_demo", unexpected)
    monkeypatch.setattr(jobs.SyntheticSourceConnector, "acquire", unexpected)
    command = [
        "--root",
        str(root),
        "capture",
        "--initiative",
        initiative,
        "--batch",
        str(batch),
        "--quiet",
        *(["--complete"] if complete else ["--gap", "Opening menu payload unavailable."]),
    ]
    assert jobs.main(command) == 0
    assert capsys.readouterr().out == ""
    assert writes == [path]
    original = path.read_bytes()
    transcript = json.loads(original)
    assert transcript["entries"] == entries
    assert transcript["captureStatus"] == ("complete" if complete else "partial")
    assert transcript["startedAt"] <= transcript["endedAt"]
    assert not list(root.glob("SYN-*/JOB-*"))
    monkeypatch.setattr(jobs, "_now", lambda: pytest.fail("Retry must retain capture times"))
    assert jobs.main(command) == 0
    assert path.read_bytes() == original
    assert writes == [path]
    assert capsys.readouterr().out == ""
    with pytest.raises(ValueError, match="closed"):
        JobStore(root).capture_batch(
            initiative, [transcript_entry(10, "user", "message", "Another intake")]
        )


def test_capture_batch_canonicalizes_parallel_option_descriptions_losslessly(
    tmp_path: Path,
) -> None:
    initiative = "SYN-PARALLEL-DESCRIPTIONS"
    entries = deferred_transcript_entries()
    question = entries[2]
    expected = {
        "End intake and generate report": "Use the supplied answers.",
        "Field employees": "People submitting travel claims.",
    }
    question["optionDescriptions"] = [expected[option] for option in question["options"]]
    original = json.loads(json.dumps(entries))

    result = JobStore(tmp_path).capture_batch(initiative, entries, complete=True)

    transcript = json.loads((tmp_path / initiative / "intake-transcript.json").read_bytes())
    assert result["captureStatus"] == "complete"
    assert transcript["entries"][2]["optionDescriptions"] == expected
    assert entries == original


@pytest.mark.parametrize(
    ("options", "descriptions"),
    [
        (["One", "Two"], ["First"]),
        (["One", "Two"], ["First", 2]),
        (["One", "One"], ["First", "Duplicate"]),
        (["One", {"invalid": "label"}], ["First", "Invalid"]),
        (None, ["First"]),
    ],
)
def test_capture_batch_rejects_ambiguous_parallel_option_descriptions_before_writing(
    tmp_path: Path, options, descriptions
) -> None:
    entries = deferred_transcript_entries()
    entries[2]["options"] = options
    entries[2]["optionDescriptions"] = descriptions

    with pytest.raises(ValueError, match="one string for each unique option"):
        JobStore(tmp_path).capture_batch(
            "SYN-INVALID-PARALLEL-DESCRIPTIONS",
            entries,
            complete=True,
        )

    assert not (tmp_path / "SYN-INVALID-PARALLEL-DESCRIPTIONS").exists()


def test_capture_batch_accepts_menu_control_reply_to_option_bearing_message(
    tmp_path: Path,
) -> None:
    entries = app_shaped_transcript_entries()

    result = JobStore(tmp_path).capture_batch(
        "SYN-MENU-CONTROL",
        entries,
        complete=True,
    )

    assert result["captureStatus"] == "complete"
    saved = json.loads((tmp_path / "SYN-MENU-CONTROL" / "intake-transcript.json").read_bytes())
    assert saved["entries"][2]["controls"] == ["Submit a new intake request"]
    assert saved["entries"][1]["optionDescriptions"] == {
        "Submit a new intake request": "Share the business need.",
        "How it works": "Review the process.",
    }
    assert saved["entries"][3]["optionDescriptions"] == {
        "Approve and generate": "Begin bounded generation.",
        "Do not generate": "Do not generate documents.",
    }


def test_capture_batch_rejects_business_selection_on_menu_message(tmp_path: Path) -> None:
    entries = app_shaped_transcript_entries()
    entries[2]["selected"] = ["Submit a new intake request"]

    with pytest.raises(ValueError, match="question or generation plan"):
        JobStore(tmp_path).capture_batch(
            "SYN-MENU-BUSINESS-SELECTION",
            entries,
            complete=True,
        )

    assert not (tmp_path / "SYN-MENU-BUSINESS-SELECTION").exists()


@pytest.mark.parametrize(
    "defect",
    [
        "empty",
        "not_list",
        "not_object",
        "sequence",
        "reply",
        "overwrite",
        "after_approval",
        "summary_complete",
        "bad_selection",
        "bad_control",
        "too_many",
    ],
)
def test_capture_batch_rejects_invalid_history_atomically(tmp_path: Path, defect: str) -> None:
    initiative = "SYN-ATOMIC-CAPTURE"
    store = JobStore(tmp_path)
    entries = deferred_transcript_entries()
    store.capture(initiative, entries[0])
    path = tmp_path / initiative / "intake-transcript.json"
    original = path.read_bytes()
    if defect == "empty":
        entries = []
    elif defect == "not_list":
        entries = {"entries": entries}
    elif defect == "not_object":
        entries[2] = "Not a turn"
    elif defect == "sequence":
        entries[4]["sequence"] = 99
    elif defect == "reply":
        entries[3]["replyTo"] = 99
    elif defect == "overwrite":
        entries[0]["text"] = "Changed earlier question"
    elif defect == "after_approval":
        entries.append(transcript_entry(10, "user", "message", "Late message"))
    elif defect == "summary_complete":
        entries[1]["fidelity"] = "summary"
    elif defect == "bad_selection":
        entries[3]["selected"] = ["Never offered"]
    elif defect == "bad_control":
        entries[6]["controls"] = ["Never offered"]
    else:
        entries *= 56
    with pytest.raises(ValueError):
        store.capture_batch(initiative, entries, complete=True)
    assert path.read_bytes() == original


@pytest.mark.parametrize("start", [0, 1])
def test_capture_batch_overlapping_retry_extends_once(tmp_path: Path, start: int) -> None:
    store = JobStore(tmp_path)
    initiative = "SYN-OVERLAPPING-CAPTURE"
    entries = deferred_transcript_entries()
    store.capture_batch(initiative, entries[:2])
    path = tmp_path / initiative / "intake-transcript.json"
    started_at = json.loads(path.read_bytes())["startedAt"]
    result = store.capture_batch(initiative, entries[start:], complete=True)
    saved = path.read_bytes()
    assert result["entryCount"] == len(entries)
    assert json.loads(saved)["startedAt"] == started_at
    assert json.loads(saved)["entries"] == entries
    with pytest.raises(ValueError, match="skip or reorder"):
        store.capture_batch(initiative, list(reversed(entries[:2])), complete=True)
    assert path.read_bytes() == saved


@pytest.mark.parametrize("outcome", ["transient", "persistent", "permanent"])
def test_capture_batch_file_faults_preserve_previous_revision(
    tmp_path: Path, monkeypatch, outcome: str
) -> None:
    initiative = "SYN-CAPTURE-FAULT"
    store = JobStore(tmp_path)
    entries = deferred_transcript_entries()
    store.capture(initiative, entries[0])
    path = tmp_path / initiative / "intake-transcript.json"
    original = path.read_bytes()
    replace = Path.replace
    attempts = []
    delays = []

    def faulty_replace(source, target):
        if target == path:
            attempts.append(source)
            if outcome == "permanent":
                raise OSError("Non-transient synthetic storage failure")
            if outcome == "persistent" or len(attempts) == 1:
                error = PermissionError("Synthetic sharing violation")
                error.winerror = 32
                raise error
        return replace(source, target)

    monkeypatch.setattr(Path, "replace", faulty_replace)
    monkeypatch.setattr(jobs.time, "sleep", delays.append)
    if outcome == "transient":
        assert store.capture_batch(initiative, entries, complete=True)["entryCount"] == 9
        assert json.loads(path.read_bytes())["entries"] == entries
    else:
        with pytest.raises(OSError):
            store.capture_batch(initiative, entries, complete=True)
        assert path.read_bytes() == original
    assert len(attempts) == {"transient": 2, "persistent": 3, "permanent": 1}[outcome]
    assert delays == {"transient": [0.05], "persistent": [0.05, 0.1], "permanent": []}[outcome]
    assert not list(path.parent.glob("*.tmp"))


def test_capture_batch_is_sealed_and_reaches_all_transcript_formats(tmp_path: Path) -> None:
    brief, response = model_input_parts()
    store = JobStore(tmp_path / "jobs")
    entries = deferred_transcript_entries()
    store.capture_batch(brief["initiativeId"], entries, complete=True)
    transcript_path = store.root / brief["initiativeId"] / "intake-transcript.json"
    captured = json.loads(transcript_path.read_bytes())
    request = tmp_path / "request.json"
    request.write_text(json.dumps({**brief, **response}), encoding="utf-8")
    queued = store.submit(
        request,
        DEFAULT_EXAMPLE / "sources/catalog.json",
        DEFAULT_EXAMPLE / "source-policy.json",
        DEFAULT_CUSTOMER,
        notify=False,
        transcript_path=transcript_path,
    )
    completed = store.execute(queued["jobId"])
    assert completed["state"] == "completed"
    report = store.directory(queued["jobId"]) / f"report-{completed['reportRevision'][:16]}"
    assert json.loads((report / "intake-transcript.json").read_bytes()) == captured
    for suffix in ("html", "md"):
        text = (report / f"intake-transcript.{suffix}").read_text(encoding="utf-8")
        assert entries[1]["text"] in text
        assert entries[4]["text"] in text
    assert completed["releaseAuthorized"] is False


def test_app_shaped_capture_and_brief_reach_report_publication(tmp_path: Path, monkeypatch) -> None:
    brief, response = model_input_parts()
    brief["releaseAudience"] = ["Employee Services lead", "Finance lead", "IT lead"]
    request = tmp_path / "brief.json"
    request.write_text(json.dumps(brief), encoding="utf-8")
    store = JobStore(tmp_path / "jobs")
    store.capture_batch(
        brief["initiativeId"],
        app_shaped_transcript_entries(),
        complete=True,
    )
    transcript_path = store.root / brief["initiativeId"] / "intake-transcript.json"
    model_calls = []

    def model(*args, **kwargs):
        model_calls.append(True)
        return response

    monkeypatch.setattr(jobs, "run_copilot", model)
    queued = store.submit(
        request,
        DEFAULT_EXAMPLE / "sources/catalog.json",
        DEFAULT_EXAMPLE / "source-policy.json",
        DEFAULT_CUSTOMER,
        notify=False,
        transcript_path=transcript_path,
        copilot=CopilotLimits("test-model"),
        copilot_executable=Path(sys.executable),
    )
    completed = store.execute(queued["jobId"])

    assert model_calls == [True]
    assert completed["state"] == "completed"
    assert completed["artifactCount"] == 23
    assert completed["reviewState"] == "awaiting_human_review"
    assert completed["releaseAuthorized"] is False
    report = store.directory(queued["jobId"]) / f"report-{completed['reportRevision'][:16]}"
    transcript = json.loads((report / "intake-transcript.json").read_bytes())
    package = json.loads((report / "package.json").read_bytes())["package"]
    assert transcript["entries"][1]["optionDescriptions"] == {
        "Submit a new intake request": "Share the business need.",
        "How it works": "Review the process.",
    }
    assert package["engagementPackage"]["releaseAudience"] == brief["releaseAudience"]


@pytest.mark.parametrize("conflicting", [False, True])
def test_concurrent_capture_batches_cannot_mix_or_overwrite_history(
    tmp_path: Path, conflicting: bool
) -> None:
    store = JobStore(tmp_path)
    initiative = "SYN-CONCURRENT-CAPTURE"
    first = deferred_transcript_entries()
    second = deferred_transcript_entries()
    if conflicting:
        second[1]["text"] = "A different answer from the competing capture."
    barrier = threading.Barrier(2)

    def capture(entries):
        barrier.wait(timeout=5)
        return store.capture_batch(initiative, entries, complete=True)

    successes = []
    errors = []
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(capture, entries) for entries in (first, second)]
        for future in futures:
            try:
                successes.append(future.result(timeout=20))
            except ValueError as error:
                errors.append(str(error))
    assert len(successes) == (1 if conflicting else 2), errors
    assert len(errors) == int(conflicting)
    if errors:
        assert "cannot be overwritten" in errors[0]
    saved = json.loads((tmp_path / initiative / "intake-transcript.json").read_bytes())
    assert saved["entries"] in (first, second)
    assert saved["captureStatus"] == "complete"
    assert all(result["entryCount"] == 9 for result in successes)


@pytest.mark.parametrize("redirect", ["root", "initiative", "transcript"])
def test_capture_batch_rejects_redirected_storage(
    tmp_path: Path, monkeypatch, redirect: str
) -> None:
    root = tmp_path / "jobs"
    store = JobStore(root)
    initiative = "SYN-REDIRECTED-CAPTURE"
    directory = root / initiative
    path = directory / "intake-transcript.json"
    target = {"root": root, "initiative": directory, "transcript": path}[redirect]
    outside = tmp_path / "outside"
    resolve = Path.resolve

    def redirected(candidate, *args, **kwargs):
        return outside if candidate == target else resolve(candidate, *args, **kwargs)

    monkeypatch.setattr(Path, "resolve", redirected)
    with pytest.raises(ValueError, match="cannot be redirected"):
        store.capture_batch(initiative, deferred_transcript_entries(), complete=True)
    assert not path.exists()
    assert not outside.exists()


@pytest.mark.parametrize("flags", [[], ["--entry", "turn.json", "--batch", "turns.json"]])
def test_capture_cli_requires_exactly_one_input_form(tmp_path: Path, capsys, flags) -> None:
    root = tmp_path / "jobs"
    with pytest.raises(SystemExit) as error:
        jobs.main(["--root", str(root), "capture", "--initiative", "SYN-INPUT-FORM", *flags])
    assert error.value.code == 2
    assert "error:" in capsys.readouterr().err
    assert not root.exists()


@pytest.mark.parametrize("count", [500, 501])
def test_capture_batch_enforces_exact_entry_limit(tmp_path: Path, count: int) -> None:
    entries = [
        transcript_entry(number, "user", "message", f"Synthetic turn {number}")
        for number in range(1, count - 1)
    ]
    entries += [
        transcript_entry(count - 1, "assistant", "generation_plan", "Generate a draft only."),
        transcript_entry(count, "user", "generation_approval", "Approved.", replyTo=count - 1),
    ]
    store = JobStore(tmp_path)
    initiative = "SYN-CAPTURE-LIMIT"
    if count == 500:
        started = perf_counter()
        result = store.capture_batch(initiative, entries, complete=True)
        assert perf_counter() - started < 2.0, "A maximum-size capture exceeded two seconds"
        assert result["entryCount"] == count
        assert result["captureStatus"] == "complete"
    else:
        with pytest.raises(ValueError, match="between 1 and 500"):
            store.capture_batch(initiative, entries, complete=True)
        assert not (tmp_path / initiative).exists()


@pytest.mark.parametrize(
    "payload",
    [
        "{}",
        '{"entries": null}',
        '{"entries": []}',
        '{"entries": [42]}',
        '{"entries": [], "startedAt": "2026-09-01T00:00:00Z"}',
        '{"entries": [',
    ],
)
def test_capture_batch_cli_rejects_invalid_input_without_a_record(
    tmp_path: Path, capsys, payload: str
) -> None:
    batch = tmp_path / "turns.json"
    batch.write_text(payload, encoding="utf-8")
    root = tmp_path / "jobs"
    assert (
        jobs.main(
            [
                "--root",
                str(root),
                "capture",
                "--initiative",
                "SYN-BAD-BATCH",
                "--batch",
                str(batch),
                "--quiet",
            ]
        )
        == 1
    )
    assert json.loads(capsys.readouterr().out)["status"] == "fail"
    assert not root.exists()


@pytest.mark.parametrize(
    "generate_label",
    [
        "End intake and generate report",
        "Generate documentation now",
    ],
)
def test_transcript_capture_is_sequential_idempotent_and_closed(
    tmp_path: Path,
    capsys,
    generate_label: str,
) -> None:
    store = JobStore(tmp_path)
    initiative = "SYN-TRANSCRIPT-001"
    question = transcript_entry(
        1,
        "assistant",
        "question",
        "Which sources?",
        options=[
            generate_label,
            "ServiceNow",
            "SharePoint",
        ],
    )
    entry_path = tmp_path / "turn.json"
    entry_path.write_text(json.dumps(question), encoding="utf-8")
    command = [
        "--root",
        str(tmp_path),
        "capture",
        "--initiative",
        initiative,
        "--entry",
        str(entry_path),
    ]
    assert jobs.main(command) == 0
    captured = json.loads(capsys.readouterr().out)
    assert captured["entryCount"] == 1
    assert jobs.main(command) == 0
    assert json.loads(capsys.readouterr().out)["entryCount"] == 1
    assert jobs.main([*command, "--quiet"]) == 0
    assert capsys.readouterr().out == ""
    with pytest.raises(ValueError, match="overwritten"):
        store.capture(initiative, {**question, "text": "Rewritten question"})
    with pytest.raises(ValueError, match="sequential"):
        store.capture(initiative, {**question, "sequence": 3})
    answer = transcript_entry(
        2,
        "user",
        "answer",
        "Use both.\n  Keep spaces.",
        replyTo=1,
        selected=["ServiceNow", "SharePoint"],
        controls=[generate_label],
    )
    store.capture(initiative, answer)
    plan = transcript_entry(
        3,
        "assistant",
        "generation_plan",
        "Generate a draft only.",
        options=["Approve and generate documentation", "Revise"],
    )
    store.capture(initiative, plan)
    approval = transcript_entry(
        4,
        "user",
        "generation_approval",
        None,
        replyTo=3,
        selected=["Approve and generate documentation"],
    )
    result = store.capture(initiative, approval, complete=True)
    assert result["captureStatus"] == "complete"
    assert store.capture(initiative, approval, complete=True) == result
    with pytest.raises(ValueError, match="closed"):
        store.capture(initiative, transcript_entry(5, "user", "message", "Another intake"))
    document = json.loads(
        (tmp_path / initiative / "intake-transcript.json").read_text(
            encoding="utf-8",
        )
    )
    assert document["entries"] == [question, answer, plan, approval]


@pytest.mark.parametrize("complete", [False, True])
def test_transcript_capture_records_stable_session_times(
    tmp_path: Path,
    monkeypatch,
    complete: bool,
) -> None:
    store = JobStore(tmp_path)
    initiative = "SYN-TRANSCRIPT-TIMING"
    path = tmp_path / initiative / "intake-transcript.json"
    started_at = "2026-09-17T18:20:30.123456Z"
    ended_at = "2026-09-17T18:25:45.654321Z"
    monkeypatch.setattr(jobs, "_now", lambda: started_at)
    plan = transcript_entry(
        1,
        "assistant",
        "generation_plan",
        "Generate a synthetic discussion draft only.",
        options=["Approve and generate documentation"],
    )
    store.capture(initiative, plan, gap=None if complete else "Earlier messages are unavailable.")
    initial = path.read_bytes()
    document = json.loads(initial)
    assert document["startedAt"] == started_at
    assert document["endedAt"] is None
    monkeypatch.setattr(jobs, "_now", lambda: ended_at)
    store.capture(initiative, plan)
    assert path.read_bytes() == initial
    approval = transcript_entry(
        2,
        "user",
        "generation_approval",
        None,
        replyTo=1,
        selected=["Approve and generate documentation"],
    )
    result = store.capture(initiative, approval, complete=complete)
    closed = path.read_bytes()
    document = json.loads(closed)
    assert document["startedAt"] == started_at
    assert document["endedAt"] == ended_at
    assert document["entries"] == [plan, approval]
    assert document["captureStatus"] == ("complete" if complete else "partial")
    monkeypatch.setattr(jobs, "_now", lambda: pytest.fail("Retries must retain recorded times."))
    assert store.capture(initiative, approval, complete=complete) == result
    assert path.read_bytes() == closed
    with pytest.raises(ValueError, match="closed"):
        store.capture(initiative, transcript_entry(3, "user", "message", "A later change"))


def test_legacy_transcript_retry_does_not_invent_session_times(tmp_path: Path, monkeypatch) -> None:
    initiative = "SYN-LEGACY-TIMING"
    question = transcript_entry(1, "assistant", "question", "Who needs this first?")
    path = tmp_path / initiative / "intake-transcript.json"
    path.parent.mkdir()
    jobs._write_json(
        path,
        {
            "schemaVersion": "1.0.0",
            "initiativeId": initiative,
            "classification": "SYNTHETIC",
            "captureStatus": "partial",
            "gaps": [],
            "entries": [question],
        },
    )
    original = path.read_bytes()
    monkeypatch.setattr(jobs, "_now", lambda: pytest.fail("Do not infer historical session times."))
    JobStore(tmp_path).capture(initiative, question)
    assert path.read_bytes() == original


@pytest.mark.parametrize("defect", ["format", "order", "unfinished", "missing_end", "not_recorded"])
def test_transcript_timing_rejects_misleading_dates(defect: str) -> None:
    initiative = "SYN-TRANSCRIPT-TIMING"
    transcript = {
        "schemaVersion": "1.0.0",
        "initiativeId": initiative,
        "classification": "SYNTHETIC",
        "captureStatus": "complete",
        "gaps": [],
        "startedAt": "2026-09-17T18:20:30Z",
        "endedAt": "2026-09-17T18:25:45Z",
        "entries": [
            transcript_entry(1, "assistant", "generation_plan", "Generate a draft only."),
            transcript_entry(
                2,
                "user",
                "generation_approval",
                "Approved for generation.",
                replyTo=1,
            ),
        ],
    }
    if defect == "format":
        transcript["startedAt"] = "2026-09-17 18:20:30"
    elif defect == "order":
        transcript["endedAt"] = "2026-09-17T18:19:00Z"
    elif defect == "unfinished":
        transcript["entries"].pop()
        transcript["captureStatus"] = "partial"
    elif defect == "missing_end":
        transcript["endedAt"] = None
    else:
        transcript["captureStatus"] = "not_recorded"
        transcript["entries"] = []
    with pytest.raises(ValueError):
        jobs.validate_transcript(transcript, initiative)


def test_transcript_capture_is_sealed_and_not_sent_to_model(tmp_path: Path, monkeypatch) -> None:
    brief, response = model_input_parts()
    store = JobStore(tmp_path / "jobs")
    entry = transcript_entry(1, "user", "message", "Private transcript marker <script> & spaces")
    store.capture(brief["initiativeId"], entry, gap="Earlier questions were not captured.")
    transcript_path = store.root / brief["initiativeId"] / "intake-transcript.json"
    original = transcript_path.read_bytes()
    brief_path = tmp_path / "brief.json"
    brief_path.write_text(json.dumps(brief), encoding="utf-8")
    queued = store.submit(
        brief_path,
        DEFAULT_EXAMPLE / "sources/catalog.json",
        DEFAULT_EXAMPLE / "source-policy.json",
        DEFAULT_CUSTOMER,
        notify=False,
        transcript_path=transcript_path,
        copilot=CopilotLimits("test-model"),
        copilot_executable=Path(sys.executable),
    )
    model_calls = []

    def model(prompt, *args, **kwargs):
        model_calls.append(True)
        assert "Private transcript marker" not in prompt
        return response

    monkeypatch.setattr(jobs, "run_copilot", model)
    store.capture(brief["initiativeId"], transcript_entry(2, "user", "correction", "Later change"))
    completed = store.execute(queued["jobId"])
    assert completed["state"] == "completed"
    assert completed["artifactCount"] == 23
    assert model_calls == [True]
    directory = store.directory(queued["jobId"])
    assert (directory / "snapshot/intake-transcript.json").read_bytes() == original
    report = directory / f"report-{completed['reportRevision'][:16]}"
    saved = json.loads((report / "intake-transcript.json").read_text(encoding="utf-8"))
    assert saved == json.loads(original)
    assert (report / "intake-transcript.html").exists()
    assert completed["releaseAuthorized"] is False


@pytest.mark.parametrize(
    "defect",
    [
        "initiative",
        "sequence",
        "reply",
        "selection",
        "control",
        "legacy_control",
        "approval",
        "complete",
        "role",
    ],
)
def test_transcript_contract_rejects_misleading_history(defect: str) -> None:
    question = transcript_entry(
        1,
        "assistant",
        "question",
        "Which sources?",
        options=["SharePoint"],
    )
    answer = transcript_entry(2, "user", "answer", None, replyTo=1, selected=["SharePoint"])
    transcript = {
        "schemaVersion": "1.0.0",
        "initiativeId": "SYN-TRANSCRIPT-001",
        "classification": "SYNTHETIC",
        "captureStatus": "partial",
        "gaps": [],
        "entries": [question, answer],
    }
    if defect == "initiative":
        transcript["initiativeId"] = "SYN-OTHER-001"
    elif defect == "sequence":
        answer["sequence"] = 1
    elif defect == "reply":
        answer["replyTo"] = 2
    elif defect == "selection":
        answer["selected"] = ["Unasked source"]
    elif defect in {"control", "legacy_control"}:
        generate_label = (
            "End intake and generate report"
            if defect == "control"
            else "Generate documentation now"
        )
        question["options"].append(generate_label)
        answer["selected"] = [generate_label]
    elif defect == "approval":
        answer["kind"] = "generation_approval"
    elif defect == "complete":
        transcript["captureStatus"] = "complete"
    else:
        answer["role"] = "assistant"
    with pytest.raises(ValueError):
        jobs.validate_transcript(transcript, "SYN-TRANSCRIPT-001")


@pytest.mark.parametrize("outcome", ["transient", "persistent", "other"])
def test_atomic_publication_has_bounded_windows_retries(
    tmp_path: Path,
    monkeypatch,
    outcome: str,
) -> None:
    source = tmp_path / "staging"
    destination = tmp_path / "published"
    source.mkdir()
    attempts = []
    delays = []
    rename = Path.rename

    def interrupted(path, target):
        attempts.append(True)
        if outcome == "transient" and len(attempts) == 3:
            return rename(path, target)
        error = PermissionError("Publication blocked")
        error.winerror = 13 if outcome == "other" else 5
        raise error

    monkeypatch.setattr(Path, "rename", interrupted)
    monkeypatch.setattr(jobs.time, "sleep", delays.append)
    if outcome == "transient":
        jobs._publish_directory(source, destination)
        assert destination.is_dir() and not source.exists()
    else:
        with pytest.raises(PermissionError):
            jobs._publish_directory(source, destination)
        assert source.is_dir() and not destination.exists()
    assert len(attempts) == (1 if outcome == "other" else 3)
    assert delays == ([] if outcome == "other" else [0.05, 0.1])


def render_instruction_markdown(text: str) -> str:
    """Include rendered menu examples without depending on equivalent Markdown markers."""
    parser = MarkdownIt()
    examples = [
        token.content
        for token in parser.parse(text)
        if token.type == "fence" and token.info.strip() == "markdown"
    ]
    return parser.render(text) + "".join(parser.render(example) for example in examples)


def test_intake_prompt_inherits_the_executable_orchestrator_tools() -> None:
    prompt = (PROJECT_ROOT / ".github/prompts/run-mosaic-intake.prompt.md").read_text(
        encoding="utf-8",
    )
    header = yaml.safe_load(prompt.split("---", 2)[1])
    assert header["agent"] == "MOSAIC Orchestrator"
    assert "tools" not in header
    assert "Run the generation command synchronously" in prompt
    agent = (PROJECT_ROOT / ".github/agents/mosaic-orchestrator.agent.md").read_text(
        encoding="utf-8",
    )
    assert "vscode/askQuestions" in yaml.safe_load(agent.split("---", 2)[1])["tools"]


@pytest.mark.parametrize(
    "relative_path",
    [
        ".github/skills/mosaic-intake/SKILL.md",
        ".github/agents/mosaic-orchestrator.agent.md",
        ".github/prompts/run-mosaic-intake.prompt.md",
    ],
)
def test_intake_entry_points_include_visible_help_and_guided_answers(relative_path: str) -> None:
    entrypoint = (PROJECT_ROOT / relative_path).read_text(encoding="utf-8")
    skill_path = PROJECT_ROOT / ".github/skills/mosaic-intake/SKILL.md"
    if (PROJECT_ROOT / relative_path) != skill_path:
        assert "[mosaic-intake skill](../skills/mosaic-intake/SKILL.md)" in entrypoint
        assert "generation reference" in entrypoint
    assert "interview turn is conversation-only" in entrypoint
    assert "before advancing" not in entrypoint
    instructions = skill_path.read_text(encoding="utf-8")
    rendered = render_instruction_markdown(instructions)
    assert "opening menu" in instructions.lower()
    assert "before any business question" in instructions
    assert "<strong>MOSAIC</strong>" in rendered
    assert "<em>Solution Engineering Process Automation</em>" in rendered
    assert "**Submit a new intake request**" in instructions
    assert "**Continue intake**" not in instructions
    assert "**Resume current intake**" not in instructions
    assert "**Pause**" not in instructions
    assert "**Pause intake**" not in instructions
    assert "**Start an intake**" not in instructions
    assert instructions.index("**Submit a new intake request**") < instructions.index(
        "**How it works**",
    )
    assert "How it works" in instructions
    assert "examples" in instructions
    assert "free text" in instructions
    assert "Something else" in instructions
    assert "**Not sure yet**" not in instructions
    assert "**Skip this question**" not in instructions
    assert "Do not offer uncertainty or skip choices" in instructions
    assert "Do not display navigation menus during intake" in instructions
    assert "**End intake and generate report**" in instructions
    assert "`End intake and generate report` as the first selectable option" in instructions
    assert "Do not display a standalone generate command" in instructions
    assert "question before its options" in instructions
    assert "Question Presentation" in instructions
    assert "everyday business language" in instructions
    assert "**Generate documentation now**" not in instructions
    assert "bold generate callout" not in instructions


def test_intake_help_preserves_state_and_does_not_authorize_generation() -> None:
    instructions = (PROJECT_ROOT / ".github/skills/mosaic-intake/SKILL.md").read_text(
        encoding="utf-8",
    )
    opening = instructions.split("## Opening Menu", 1)[1].split("## Conversational Intake", 1)[0]
    assert "Do not put the first business question into the opening-menu carousel" in opening
    assert (
        "<p><strong>MOSAIC</strong>\n<em>Solution Engineering Process Automation</em></p>"
        in render_instruction_markdown(opening)
    )
    assert opening.index("**MOSAIC**") < opening.index("1. **Submit a new intake request**")
    assert "same title and subtitle when redisplaying the opening menu after Help" in opening
    markdown_blocks = opening.split("```markdown\n")
    opening_menu = markdown_blocks[1].split("\n```", 1)[0]
    first_question = markdown_blocks[2].split("\n```", 1)[0]
    assert "1. **Submit a new intake request**" in opening_menu
    assert "2. **How it works**" in opening_menu
    assert "use this exact first-question text layout" in opening
    assert "**What business problem or opportunity would you like help with?**" in opening
    assert "1. **Reduce manual work**" in first_question
    assert "**End intake and generate report**" not in first_question
    assert "Do not offer the generation control before any business need" in opening
    assert "do not replace it with an unnumbered examples-only response" in opening
    assert "\n3. **" not in opening_menu
    assert "\n1. **Continue intake**" not in opening_menu
    assert "single new-request flow for the contest" in opening
    assert "Never carry over another request's answers or generation approval" in opening
    assert "If Help was requested from the opening screen" in opening
    assert "retain the current question and answers without displaying a menu" in opening
    assert "Help never starts generation, submits or retries a job, records approval" in opening
    assert "An answer advances the current intake directly" in instructions
    intake = instructions.split("## Conversational Intake", 1)[1].split(
        "## Current-Intake Documents",
        1,
    )[0]
    assert "The first business-problem question intentionally has no generation control" in intake
    assert "After at least one business answer has been supplied" in intake
    presentation = intake.split("### Question Presentation", 1)[1].split(
        "### Generate After The First Answer",
        1,
    )[0]
    assert "**mandatory response gate**" in presentation
    assert "A later bare question, an examples-only response" in presentation
    assert "rewrite it before sending" in presentation
    assert "Give each option a short label and a useful description" in presentation
    assert "Accept corrections and volunteered details" in presentation
    assert "not a fixed questionnaire" in presentation
    assert "Do not ask another optional business question at this point" in intake
    assert "Your intake report is ready" in instructions
    generate = intake.split("### Generate After The First Answer", 1)[1]
    menu = generate.split("```markdown\n", 1)[1].split("\n```", 1)[0]
    labels = [
        "End intake and generate report",
        "Procurement staff",
        "Employees",
        "Both groups",
        "Something else",
    ]
    descriptions = [
        "Use your answers so far; missing details stay clearly marked.",
        "People answering purchasing questions.",
        "People looking for purchasing guidance.",
        "Procurement staff and employees.",
        "Describe who you have in mind.",
    ]
    expected_menu = "**Who needs this first?**\n\n**Options**\n\n" + "\n".join(
        f"{number}. **{label}**: {description}"
        for number, (label, description) in enumerate(zip(labels, descriptions, strict=True), 1)
    )
    assert MarkdownIt().render(menu) == MarkdownIt().render(expected_menu)
    assert "Keep the explanation inside that option's description" in generate
    assert f"description `{descriptions[0]}`" in generate
    assert "Treat the selection as a control action, never as a business answer" in intake
    assert "preserve those supplied values first" in intake
    assert "remove the control label from the recorded answers" in intake
    assert "If selected alone, retain all earlier answers" in intake
    assert "Beyond the initial business need, do not require another question" in intake
    assert "Immediately stop optional questions" in intake
    assert "Keep generation approval as a separate confirmation step" in intake
    assert "submit once without asking for redundant confirmation" in intake
    assert "unresolved optional fields remain unknown or null" in intake.lower()
    assert "Include **Something else** within the five-business-answer limit" in intake
    assert "\n1. **Generate draft with current information**" not in intake
    assert "\n2. **How it works**" not in intake
    assert 'If they only say "stop" or "pause", stop without generating' in instructions
    assert "allowFreeformInput: true" in instructions
    assert "Do not preselect a business answer" in instructions
    assert "A business-answer selection is not permission to generate" in instructions


def test_numeric_first_option_stops_intake_and_opens_generation_plan() -> None:
    skill = (PROJECT_ROOT / ".github/skills/mosaic-intake/SKILL.md").read_text(
        encoding="utf-8",
    )
    agent = (PROJECT_ROOT / ".github/agents/mosaic-orchestrator.agent.md").read_text(
        encoding="utf-8",
    )
    prompt = (PROJECT_ROOT / ".github/prompts/run-mosaic-intake.prompt.md").read_text(
        encoding="utf-8",
    )

    assert "most recently displayed unanswered question" in skill
    assert "Mandatory first check on every intake reply" in skill
    assert "The next response must be the bounded generation plan" in skill
    assert "Asking any business question in that case is invalid" in skill
    assert "This precedence overrides the opening menu's `1` mapping" in skill
    assert "`1`, `1.`, `option 1` and `first option`" in skill
    assert "never ask another business question after it" in skill
    assert "Display the bounded generation plan next" in skill
    assert "`1` starts intake only while that displayed opening menu" in agent
    assert "render the skill's exact first-question template" in agent
    assert "never offer generation before the first business answer" in agent
    assert "never substitute an unnumbered examples-only response" in agent
    assert "**Mandatory first check:**" in agent
    assert "the only valid next response is the bounded generation plan" in agent
    assert "After the first business answer, every further business question" in agent
    assert (
        "Business examples are additional choices and never replace or hide this control" in agent
    )
    assert "**Mandatory response gate after the first answer:**" in agent
    assert "never send a later bare business question" in agent
    assert "rewrite the response before sending it" in agent
    assert "never the opening menu" in agent
    assert "must stop optional questions and display the generation plan next" in agent
    assert "After the first business answer, every further business question" in prompt
    assert "use the skill's exact first-question template" in prompt
    assert "Never offer generation before the first business answer" in prompt
    assert "never return an unnumbered examples-only response" in prompt
    assert "Before any other interpretation" in prompt
    assert "Another business question is invalid" in prompt
    assert "Examples never replace that control" in prompt
    assert "Never send a later bare business question" in prompt
    assert "rewrite any subsequent-question draft" in prompt
    assert "most recently displayed unanswered question" in prompt
    assert "it never reselects the opening menu or answers the business topic" in prompt


@pytest.mark.parametrize(
    "relative_path",
    [
        ".github/skills/mosaic-intake/SKILL.md",
        ".github/agents/mosaic-orchestrator.agent.md",
        ".github/prompts/run-mosaic-intake.prompt.md",
    ],
)
def test_intake_generation_waits_and_offers_browser_handoff(relative_path: str) -> None:
    instructions = (PROJECT_ROOT / relative_path).read_text(encoding="utf-8")
    assert "synchronously" in instructions
    assert "mosaic.jobs generate" in instructions
    assert "mosaic.jobs open" in instructions
    assert "mosaic.jobs rebuild" in instructions
    assert "**Open documents in browser**" in instructions
    assert "Windows notifications are disabled" in instructions
    assert "No automatic paid retries" in instructions
    assert "Intake Transcript" in instructions
    assert "mosaic.jobs capture" in instructions
    assert "--transcript" in instructions
    assert "not_recorded" in instructions
    assert "Do not show trace or debug messages" in instructions
    assert "Do not narrate transcript capture" in instructions
    assert "--quiet" in instructions
    assert "Return the actual job ID and status link promptly" not in instructions


def test_intake_defers_all_processing_and_loads_one_generation_contract() -> None:
    skill = (PROJECT_ROOT / ".github/skills/mosaic-intake/SKILL.md").read_text(encoding="utf-8")
    generation = (PROJECT_ROOT / ".github/skills/mosaic-intake/references/generation.md").read_text(
        encoding="utf-8"
    )
    fast_path = skill.split("## Interview Fast Path", 1)[1].split(
        "## Customer-Facing Conversation", 1
    )[0]
    for operation in (
        "transcript capture",
        "write files",
        "allocate identifiers",
        "inspect schemas",
        "read configuration or evidence",
        "search",
        "delegate",
        "invoke the analysis engine",
    ):
        assert operation in fast_path
    assert "only after generation-plan approval, before any analysis call" in fast_path
    assert "already-callable native question selector" in fast_path
    assert "do not discover tools just to display choices" in fast_path
    assert "./references/generation.md" in skill
    assert "--batch" in generation
    assert "one atomic write" in generation
    assert "before the analysis call" in generation
    assert "never a source-code repair loop" in (
        PROJECT_ROOT / ".github/prompts/run-mosaic-intake.prompt.md"
    ).read_text(encoding="utf-8")


def test_job_publishes_exact_revision_from_sealed_snapshot(tmp_path: Path) -> None:
    store = JobStore(tmp_path)
    queued = queue(store)
    assert queued["state"] == "queued"
    completed = store.execute(queued["jobId"])
    assert completed["state"] == "completed"
    assert completed["reviewState"] == "awaiting_human_review"
    assert completed["releaseAuthorized"] is False
    assert completed["artifactCount"] == 23
    assert len(completed["reportRevision"]) == 64
    assert completed["reportRevision"][:16] in completed["reportPath"]
    assert [event["state"] for event in completed["history"]] == ["queued", "running", "completed"]
    assert store.execute(queued["jobId"]) == completed
    assert store.cancel(queued["jobId"]) == completed


@pytest.mark.parametrize("failure", [False, True])
def test_generate_waits_for_terminal_result_without_detaching_or_notifying(
    tmp_path: Path,
    monkeypatch,
    capsys,
    failure: bool,
) -> None:
    calls = []
    render = jobs.run_demo

    def generate(*args, **kwargs):
        calls.append(True)
        if failure:
            raise ValueError("Synthetic generation failure")
        return render(*args, **kwargs)

    def unexpected(*args, **kwargs):
        pytest.fail("Foreground generation must not detach or send a notification")

    monkeypatch.setattr(jobs, "run_demo", generate)
    monkeypatch.setattr(JobStore, "start", unexpected)
    monkeypatch.setattr(jobs, "send_windows_notification", unexpected)
    exit_code = jobs.main(
        [
            "--root",
            str(tmp_path),
            "generate",
            "--request",
            str(DEFAULT_EXAMPLE / "request.json"),
            "--reference",
        ]
    )
    output = capsys.readouterr()
    result = json.loads(output.out)
    assert exit_code == (1 if failure else 0)
    assert calls == [True]
    assert "Generating and validating" in output.err
    assert ("Publishing the validated" in output.err) is not failure
    assert result["state"] == ("failed" if failure else "completed")
    assert result["notification"] == {"requested": False, "status": "disabled"}
    assert "launchPid" not in result
    assert result["releaseAuthorized"] is False
    if failure:
        assert result["reportPath"] is None
        assert result["error"]["message"] == (
            "A validation or integrity check blocked generation. Saved input is "
            "preserved; review the cause before choosing recovery."
        )
        assert result["error"]["nextAction"] == "review_failure"
    else:
        assert result["artifactCount"] == 23
        assert result["reviewState"] == "awaiting_human_review"
        assert result["reportRevision"][:16] in result["reportPath"]


def test_copilot_worker_command_and_environment_are_restricted(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("COPILOT_ALLOW_ALL", "true")
    monkeypatch.setenv("COPILOT_PROVIDER_BASE_URL", "https://unapproved.example")
    monkeypatch.setenv("COPILOT_PROVIDER_API_KEY_COMMAND", "unapproved-command")
    monkeypatch.setenv("COPILOT_CUSTOM_INSTRUCTIONS_DIRS", str(tmp_path / "unapproved"))
    monkeypatch.setenv("NODE_OPTIONS", "--require=unapproved")
    monkeypatch.setenv("OTEL_EXPORTER_OTLP_ENDPOINT", "https://unapproved.example")
    environment = restricted_environment(tmp_path / "home")
    assert environment["COPILOT_ALLOW_ALL"] == "false"
    assert environment["COPILOT_HOME"] == str(tmp_path / "home")
    assert environment["USERPROFILE"] == str(tmp_path / "home")
    assert environment["HOME"] == str(tmp_path / "home")
    assert environment["GH_CONFIG_DIR"] == str(tmp_path / "home" / "gh")
    assert environment["XDG_CONFIG_HOME"] == str(tmp_path / "home" / ".config")
    assert not any(key.startswith("COPILOT_PROVIDER_") for key in environment)
    assert "COPILOT_CUSTOM_INSTRUCTIONS_DIRS" not in environment
    assert "NODE_OPTIONS" not in environment
    assert "OTEL_EXPORTER_OTLP_ENDPOINT" not in environment
    command = restricted_command(
        tmp_path / "copilot.exe",
        CopilotLimits("test-model"),
        "Return only synthetic draft JSON.",
        tmp_path,
    )
    assert "--available-tools=__mosaic_no_tools__" in command
    assert "--available-tools=" not in command
    assert command[command.index("--deny-tool") + 1 : command.index("--disable-builtin-mcps")] == [
        "shell",
        "write",
        "url",
    ]
    assert command[command.index("--max-ai-credits") + 1] == "30"
    assert command[command.index("--output-format") + 1] == "json"
    assert "--no-auto-login" not in command
    assert all(
        flag in command
        for flag in (
            "--no-custom-instructions",
            "--disable-builtin-mcps",
            "--no-ask-user",
            "--no-remote",
            "--no-remote-export",
        )
    )
    assert not set(command) & {"--allow-all", "--allow-all-tools", "--allow-all-paths", "--yolo"}


@pytest.mark.parametrize(
    "overrides",
    [
        {"model": "auto"},
        {"model": "--unsafe"},
        {"max_ai_credits": 0},
        {"max_ai_credits": float("inf")},
        {"max_ai_credits": 301},
        {"timeout_seconds": 1801},
    ],
)
def test_copilot_limits_fail_closed(overrides: dict) -> None:
    with pytest.raises(ValueError):
        CopilotLimits(**{"model": "test-model", **overrides})


def test_copilot_command_rejects_oversized_input(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="prompt size"):
        restricted_command(
            tmp_path / "copilot.exe",
            CopilotLimits("test-model"),
            "input" * 10000,
            tmp_path,
        )


@pytest.mark.parametrize("response", [b"[]", b"{} trailing", b'{"a":1,"a":2}', b'{"a":NaN}'])
def test_copilot_response_rejects_ambiguous_json(response: bytes) -> None:
    with pytest.raises(ValueError):
        copilot_runner.parse_response(response)


@pytest.mark.parametrize("defect", [None, "multiple", "tool", "invalid"])
def test_copilot_structured_output_separates_usage_from_answer(defect: str | None) -> None:
    answer = {"type": "assistant.message", "data": {"content": '{"analysisSeed":{}}'}}
    events = [
        answer,
        {
            "type": "session.info",
            "data": {
                "infoType": "session_limits",
                "message": "Session limits: 19.79/30 AI credits used.",
            },
        },
    ]
    if defect == "multiple":
        events.append(answer)
    elif defect == "tool":
        events.append({"type": "tool.execution_start", "data": {}})
    elif defect == "invalid":
        answer["data"]["content"] = "{} trailing"
    content = "\n".join(json.dumps(event) for event in events).encode("utf-8")
    if defect:
        with pytest.raises(ValueError):
            copilot_runner.parse_cli_output(content)
    else:
        assert copilot_runner.parse_cli_output(content) == {"analysisSeed": {}}


@pytest.mark.parametrize("behavior", ["success", "failure", "oversized", "timeout", "cancel"])
def test_copilot_process_is_bounded_without_model_calls(
    tmp_path: Path,
    monkeypatch,
    behavior: str,
) -> None:
    snippets = {
        "success": 'import json; print(json.dumps({"type":"assistant.message",'
        '"data":{"content":"{\\"analysisSeed\\":{}}"}}))',
        "failure": "raise SystemExit(3)",
        "oversized": f"print('x' * {copilot_runner.MAX_OUTPUT_BYTES + 1})",
        "timeout": "import threading; threading.Event().wait(30)",
        "cancel": "import threading; threading.Event().wait(30)",
    }
    monkeypatch.setattr(
        copilot_runner,
        "restricted_command",
        lambda *args: [sys.executable, "-E", "-s", "-B", "-c", snippets[behavior]],
    )
    checks = []
    processes = []
    popen = copilot_runner.subprocess.Popen

    def tracked_process(*args, **kwargs):
        process = popen(*args, **kwargs)
        processes.append(process)
        return process

    monkeypatch.setattr(copilot_runner.subprocess, "Popen", tracked_process)
    started = perf_counter()

    def canceled():
        checks.append(True)
        return behavior == "cancel" and perf_counter() - started >= 0.2

    if behavior == "success":
        assert copilot_runner.run_copilot(
            "Synthetic test",
            CopilotLimits("test-model"),
            Path(sys.executable),
            tmp_path / "home",
            canceled,
        ) == {"analysisSeed": {}}
    else:
        expected = (
            copilot_runner.AnalysisCanceled
            if behavior == "cancel"
            else TimeoutError
            if behavior == "timeout"
            else ValueError
        )
        with pytest.raises(expected):
            copilot_runner.run_copilot(
                "Synthetic test",
                CopilotLimits("test-model", timeout_seconds=1),
                Path(sys.executable),
                tmp_path / "home",
                canceled,
            )
    elapsed = perf_counter() - started
    assert elapsed < 4.0, f"{behavior} took {elapsed:.3f}s instead of stopping promptly"
    if behavior == "timeout":
        assert elapsed >= 1.0
    assert processes
    assert all(process.poll() is not None for process in processes)


def model_input_parts() -> tuple[dict, dict]:
    request = json.loads((DEFAULT_EXAMPLE / "request.json").read_text(encoding="utf-8"))
    request["optionDraft"] = option.execute(request)
    request["designDraft"] = design.execute(request["optionDraft"])
    request["inputMode"] = "conversation"
    request["intakeContext"] = {
        "scope": "Travel claims",
        "exclusions": "No deployment",
        "budget": "$30,000 ceiling",
        "timeline": "Proposal by 15 October; year unknown",
        "systems": "SharePoint",
        "ownership": "Finance",
        "baseline": None,
    }
    request["optionDraft"]["options"][0]["name"] = "Test-authored travel search"
    for dependency in request["analysisSeed"]["dependencies"]:
        dependency["label"] = "assumption"
    response = {name: request.pop(name) for name in copilot_runner.RESPONSE_FIELDS}
    return request, response


@pytest.mark.parametrize(
    "audience",
    [
        "Finance and IT reviewers",
        ["Employee Services lead", "Finance lead", "IT lead"],
    ],
)
def test_conversation_brief_accepts_named_or_role_list_release_audience(audience) -> None:
    brief, _ = model_input_parts()
    brief["releaseAudience"] = audience

    copilot_runner.validate_brief(brief)


@pytest.mark.parametrize("audience", ["", [], ["Finance lead", "Finance lead"], ["Finance", 3]])
def test_conversation_brief_rejects_invalid_release_audience(audience) -> None:
    brief, _ = model_input_parts()
    brief["releaseAudience"] = audience

    with pytest.raises(ValueError, match="releaseAudience"):
        copilot_runner.validate_brief(brief)


@pytest.mark.skipif(
    not os.environ.get("MOSAIC_TEST_COPILOT_EXE"),
    reason="Set MOSAIC_TEST_COPILOT_EXE for the optional local-only native CLI contract check.",
)
@pytest.mark.parametrize("mode", ["probe", "workflow"])
def test_installed_copilot_cli_exposes_no_tools(tmp_path: Path, monkeypatch, mode: str) -> None:
    requests = []
    brief, response = model_input_parts()
    content = json.dumps(response) if mode == "workflow" else '{"localProbe":true}'

    class Provider(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_POST(self):
            payload = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            requests.append(payload)
            if payload.get("stream"):
                chunk = {
                    "id": "local-test",
                    "object": "chat.completion.chunk",
                    "choices": [
                        {
                            "index": 0,
                            "delta": {"role": "assistant", "content": content},
                            "finish_reason": None,
                        },
                    ],
                }
                body = "data: " + json.dumps(chunk) + "\n\n"
                chunk["choices"] = [{"index": 0, "delta": {}, "finish_reason": "stop"}]
                chunk["usage"] = {
                    "prompt_tokens": 120,
                    "completion_tokens": 30,
                    "total_tokens": 150,
                    "prompt_tokens_details": {"cached_tokens": 40},
                    "completion_tokens_details": {"reasoning_tokens": 5},
                }
                body += "data: " + json.dumps(chunk) + "\n\ndata: [DONE]\n\n"
                content_type = "text/event-stream"
            else:
                body = json.dumps(
                    {
                        "id": "local-test",
                        "object": "chat.completion",
                        "choices": [
                            {
                                "index": 0,
                                "message": {"role": "assistant", "content": content},
                                "finish_reason": "stop",
                            },
                        ],
                        "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
                    }
                )
                content_type = "application/json"
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body.encode())))
            self.end_headers()
            self.wfile.write(body.encode())

    with ThreadingHTTPServer(("127.0.0.1", 0), Provider) as server:
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        original_environment = copilot_runner.restricted_environment

        def local_environment(home):
            environment = original_environment(home)
            for name in ("COPILOT_GITHUB_TOKEN", "GH_TOKEN", "GITHUB_TOKEN"):
                environment.pop(name, None)
            environment.update(
                {
                    "COPILOT_OFFLINE": "true",
                    "COPILOT_PROVIDER_TYPE": "openai",
                    "COPILOT_PROVIDER_BASE_URL": f"http://127.0.0.1:{server.server_port}/v1",
                    "COPILOT_PROVIDER_WIRE_API": "completions",
                }
            )
            return environment

        monkeypatch.setattr(copilot_runner, "restricted_environment", local_environment)
        try:
            if mode == "workflow":
                path = tmp_path / "brief.json"
                path.write_text(json.dumps(brief), encoding="utf-8")
                store = JobStore(tmp_path / "jobs")
                queued = store.submit(
                    path,
                    DEFAULT_EXAMPLE / "sources/catalog.json",
                    DEFAULT_EXAMPLE / "source-policy.json",
                    DEFAULT_CUSTOMER,
                    notify=False,
                    copilot=CopilotLimits("test-model", timeout_seconds=45),
                    copilot_executable=Path(os.environ["MOSAIC_TEST_COPILOT_EXE"]),
                )
                result = store.execute(queued["jobId"])
                assert result["state"] == "completed", (
                    store.directory(queued["jobId"]) / "failure.json"
                ).read_text(encoding="utf-8")
                assert result["artifactCount"] == 23
                assert result["releaseAuthorized"] is False
                assert result["analysis"]["status"] == "completed"
            else:
                result = copilot_runner.run_copilot(
                    'Return exactly {"localProbe":true}. Do not use any tools.',
                    CopilotLimits("test-model", timeout_seconds=45),
                    Path(os.environ["MOSAIC_TEST_COPILOT_EXE"]),
                    tmp_path / "home",
                    lambda: False,
                )
                assert result == {"localProbe": True}
        except copilot_runner.CopilotInvocationError as error:
            raise AssertionError(error.diagnostic) from error
        finally:
            server.shutdown()
            thread.join(timeout=5)
    assert len(requests) == 1
    assert not requests[0].get("tools")


def test_copilot_response_preserves_input_and_builds_a_bounded_prompt(tmp_path: Path) -> None:
    brief, response = model_input_parts()
    del response["designDraft"]["implementationStatus"]
    prepared = copilot_runner.prepare_request(
        brief,
        response,
        {f"EVD-{n:03d}" for n in range(1, 5)},
    )
    assert all(prepared[key] == value for key, value in brief.items())
    assert prepared["designDraft"]["implementationStatus"] == "not_started"
    assert "optionDraft" not in brief
    catalog = json.loads((DEFAULT_EXAMPLE / "sources/catalog.json").read_text(encoding="utf-8"))
    evidence = [
        {
            "id": source["id"],
            "content": (DEFAULT_EXAMPLE / "sources" / source["file"]).read_text(
                encoding="utf-8",
            ),
        }
        for source in catalog["sources"]
    ]
    prompt = copilot_runner.build_prompt(brief, evidence)
    assert '"baseline":null' in prompt
    assert "The engine owns designDraft.maturity" in prompt
    assert "No solution code" in prompt
    restricted_command(Path(sys.executable), CopilotLimits("test-model"), prompt, tmp_path)


@pytest.mark.parametrize(
    ("name", "invalid"),
    [
        ("maturity", "implemented"),
        ("selectionStatus", "selected"),
        ("implementationStatus", "in_progress"),
    ],
)
def test_copilot_response_rejects_invalid_engine_owned_status(name: str, invalid: str) -> None:
    brief, response = model_input_parts()
    response["designDraft"][name] = invalid

    with pytest.raises(ValueError, match="Copilot analysis response"):
        copilot_runner.prepare_request(
            brief,
            response,
            {f"EVD-{n:03d}" for n in range(1, 5)},
        )


@pytest.mark.parametrize("defect", [None, "alias", "missing", "extra", "headings"])
def test_copilot_comparison_schema_binds_exact_criterion_names(defect: str | None) -> None:
    brief, response = model_input_parts()
    criteria = ["Policy accuracy and citations", "Mobile usability"]
    brief["optionCriteria"] = criteria
    response["optionDraft"]["evaluationCriteria"] = criteria.copy()
    for candidate in response["optionDraft"]["options"]:
        candidate["criterionAssessments"] = {
            name: "Proposed assessment; evidence and validation remain required."
            for name in criteria
        }
    assessment = response["optionDraft"]["options"][0]["criterionAssessments"]
    if defect == "alias":
        assessment["mobileUsability"] = assessment.pop("Mobile usability")
    elif defect == "missing":
        del assessment["Mobile usability"]
    elif defect == "extra":
        assessment["Unexpected criterion"] = "Unsupported extra comparison."
    elif defect == "headings":
        response["optionDraft"]["evaluationCriteria"][1] = "Another heading"
    schema = copilot_runner.response_schema(criteria)
    option_properties = schema["properties"]["optionDraft"]["properties"]
    assert option_properties["evaluationCriteria"]["const"] == criteria
    if defect:
        with pytest.raises(ValueError, match="Copilot analysis response"):
            copilot_runner.prepare_request(brief, response, {f"EVD-{n:03d}" for n in range(1, 5)})
    else:
        prepared = copilot_runner.prepare_request(
            brief,
            response,
            {f"EVD-{n:03d}" for n in range(1, 5)},
        )
        assert prepared["optionDraft"]["evaluationCriteria"] == criteria


def test_copilot_brief_accepts_supplied_role_names_without_inventing_authority() -> None:
    brief, response = model_input_parts()
    brief["stakeholders"] = ["Employee Services business owner", "Finance policy owner"]
    prepared = copilot_runner.prepare_request(
        brief,
        response,
        {f"EVD-{n:03d}" for n in range(1, 5)},
    )
    assert prepared["stakeholders"] == brief["stakeholders"]


@pytest.mark.parametrize("mode", ["model", "prepared"])
@pytest.mark.parametrize(
    "stakeholders",
    [
        None,
        "Finance policy owner",
        [42],
        [""],
        [{"role": "Finance policy owner"}],
        [{"role": "Finance policy owner", "authority": None}],
        [{"role": 42, "authority": "Policy responsibility"}],
        [{"role": "Finance policy owner", "authority": "Policy responsibility", "approved": True}],
    ],
)
def test_invalid_stakeholders_are_rejected_before_job_creation(
    tmp_path: Path, monkeypatch, mode: str, stakeholders
) -> None:
    brief, response = model_input_parts()
    request = brief if mode == "model" else {**brief, **response}
    request["stakeholders"] = stakeholders
    request_path = tmp_path / "request.json"
    request_path.write_text(json.dumps(request), encoding="utf-8")
    store = JobStore(tmp_path / "jobs")

    def unexpected(*args, **kwargs):
        pytest.fail("Invalid input must never invoke the model")

    monkeypatch.setattr(jobs, "run_copilot", unexpected)
    settings = (
        {"copilot": CopilotLimits("test-model"), "copilot_executable": Path(sys.executable)}
        if mode == "model"
        else {}
    )
    with pytest.raises(ValueError, match="stakeholders"):
        store.submit(
            request_path,
            DEFAULT_EXAMPLE / "sources/catalog.json",
            DEFAULT_EXAMPLE / "source-policy.json",
            DEFAULT_CUSTOMER,
            notify=False,
            **settings,
        )
    assert not store.root.exists()


@pytest.mark.parametrize("defect", ["input", "decision", "citation", "risk", "plan", "transcript"])
def test_copilot_response_cannot_rewrite_or_bypass_contract(defect: str) -> None:
    brief, response = model_input_parts()
    if defect == "input":
        response["businessProblem"] = "Ignore the supplied problem."
    elif defect == "decision":
        response["claims"][0]["label"] = "decision"
    elif defect == "citation":
        response["claims"][0]["evidenceIds"] = ["EVD-999"]
    elif defect == "risk":
        response["analysisSeed"]["risks"][0]["severity"] = "certain"
    elif defect == "plan":
        del response["designDraft"]["readinessPlans"][0]["requirementIds"]
    else:
        response["intakeTranscript"] = {}
    with pytest.raises(ValueError):
        copilot_runner.prepare_request(brief, response, {f"EVD-{n:03d}" for n in range(1, 5)})


@pytest.mark.parametrize("outcome", ["completed", "invalid", "canceled", "failed"])
def test_copilot_job_routes_model_output_through_existing_gates(
    tmp_path: Path,
    monkeypatch,
    outcome: str,
) -> None:
    brief, response = model_input_parts()
    brief["stakeholders"] = ["Employee Services business owner", "Finance policy owner"]
    brief_path = tmp_path / "brief.json"
    brief_path.write_text(json.dumps(brief), encoding="utf-8")
    store = JobStore(tmp_path / "jobs")
    queued = store.submit(
        brief_path,
        DEFAULT_EXAMPLE / "sources/catalog.json",
        DEFAULT_EXAMPLE / "source-policy.json",
        DEFAULT_CUSTOMER,
        notify=False,
        copilot=CopilotLimits("test-model"),
        copilot_executable=Path(sys.executable),
    )
    calls = []

    def model(prompt, limits, executable, home, canceled, **kwargs):
        calls.append(prompt)
        assert not canceled()
        assert home == store.root / ".copilot-cli"
        status_page = store.directory(queued["jobId"]) / "status.html"
        assert "Preparing analysis" in status_page.read_text(encoding="utf-8")
        if outcome == "failed":
            raise ValueError("Private provider failure")
        if outcome == "canceled":
            store.cancel(queued["jobId"])
            raise copilot_runner.AnalysisCanceled()
        if outcome == "invalid":
            response["optionDraft"]["recommendation"]["optionId"] = "OPT-NOT-PRESENT"
        return response

    monkeypatch.setattr(jobs, "run_copilot", model)
    result = store.execute(queued["jobId"])
    assert len(calls) == 1
    assert result["state"] == ("failed" if outcome == "invalid" else outcome)
    assert result["releaseAuthorized"] is False
    if outcome == "completed":
        assert result["artifactCount"] == 23
        authored_path = store.directory(queued["jobId"]) / "analysis-request.json"
        authored = json.loads(authored_path.read_text(encoding="utf-8"))
        assert all(authored[key] == value for key, value in brief.items())
        assert authored["analysisProvenance"]["model"] == "test-model"
        report = store.directory(queued["jobId"]) / f"report-{result['reportRevision'][:16]}"
        report_text = (report / "intake-report.html").read_text(encoding="utf-8")
        assert "Analysis Preparation" in report_text
        assert authored["analysisProvenance"]["responseDigest"] in report_text
    else:
        assert result["reportPath"] is None
        assert not list(store.directory(queued["jobId"]).glob("report-*"))
        if outcome != "canceled":
            assert result["error"]["localRebuildAvailable"] is (outcome == "invalid")
            assert result["error"]["nextAction"] == "review_failure"
    if outcome in {"completed", "invalid"}:
        captured = store.directory(queued["jobId"]) / "analysis-response.json"
        assert json.loads(captured.read_text(encoding="utf-8")) == response
    assert "Private provider failure" not in json.dumps(result)


def test_operator_report_covers_every_stage_and_keeps_customer_outputs_separate(
    tmp_path: Path, monkeypatch
) -> None:
    store = JobStore(tmp_path)
    queued = queue(store)
    monkeypatch.setattr(
        jobs, "run_copilot", lambda *args, **kwargs: pytest.fail("Unexpected paid inference")
    )
    state = store.execute(queued["jobId"])
    assert state["state"] == "completed"
    assert state["processingStatus"] == "ready"
    directory = store.directory(state["jobId"])
    report = directory / f"report-{state['reportRevision'][:16]}"
    assert len(list(report.iterdir())) == state["artifactCount"] == 23
    assert all((directory / name).is_file() for name in OPERATOR_FILES)
    assert not any((report / name).exists() for name in OPERATOR_FILES)
    metrics = json.loads((directory / "processing-report.json").read_bytes())
    events = [
        json.loads(line) for line in (directory / "pipeline-trace.jsonl").read_bytes().splitlines()
    ]
    assert [event["sequence"] for event in events] == list(range(1, len(events) + 1))
    assert [
        event["step"]
        for event in events
        if event["step"].startswith("workflow.") and event["status"] == "completed"
    ] == [
        f"workflow.{name}"
        for name in (
            "discover",
            "acquire",
            "normalize",
            "analyze",
            "option",
            "design",
            "prepare",
            "review",
        )
    ]
    assert len([event for event in events if event["step"] == "report.artifact"]) == 23
    assert events[-1]["step"] == "job.finished"
    assert metrics["coverage"]["wholeIntakeCostUsd"] is None
    assert metrics["coverage"]["wholeIntakeTokens"] is None
    assert metrics["workerUsage"]["status"] == "not_invoked"
    assert metrics["workerUsage"]["reportedAICredits"] == 0
    assert metrics["workerUsage"]["actualBilledUsd"] is None
    assert metrics["counts"]["analysisInvocationAttempts"] == 0
    assert metrics["customerReleaseAuthorized"] is False
    assert metrics["timing"]["backendSeconds"] >= 0
    assert store.processing_report_uri(state["jobId"]) == state["processingReportPath"]
    assert store.verified_report_uri(state["jobId"]) == state["reportPath"]
    problem = json.loads((DEFAULT_EXAMPLE / "request.json").read_bytes())["businessProblem"]
    operator_html = (directory / "processing-report.html").read_text(encoding="utf-8")
    assert problem not in operator_html
    assert "No new model usage in this run." in operator_html
    assert "Not reported" not in operator_html
    assert "Backend AI credits" not in operator_html
    assert "Backend token and cost details" not in operator_html
    assert "Recorded approval to worker start" not in operator_html


@pytest.mark.parametrize("outcome", ["completed", "timeout", "canceled"])
def test_operator_usage_survives_failures_without_turning_limits_into_charges(
    tmp_path: Path, monkeypatch, outcome: str
) -> None:
    brief, response = model_input_parts()
    brief["businessProblem"] += " PRIVATE-INTAKE-CANARY."
    request = tmp_path / "brief.json"
    request.write_text(json.dumps(brief), encoding="utf-8")
    store = JobStore(tmp_path / "jobs")
    queued = store.submit(
        request,
        DEFAULT_EXAMPLE / "sources/catalog.json",
        DEFAULT_EXAMPLE / "source-policy.json",
        DEFAULT_CUSTOMER,
        notify=False,
        copilot=CopilotLimits("test-model"),
        copilot_executable=Path(sys.executable),
    )
    usage = provider_observations(
        [
            {
                "type": "assistant.usage",
                "id": "synthetic-one",
                "data": {
                    "model": "test-model",
                    "inputTokens": 120,
                    "outputTokens": 30,
                    "cost": 1.5,
                    "copilotUsage": {"totalNanoAiu": 2_500_000_000},
                },
            }
        ],
        complete=outcome == "completed",
    )

    def model(*args, on_usage):
        on_usage(usage)
        if outcome == "timeout":
            raise TimeoutError("PRIVATE-DIAGNOSTIC-CANARY")
        if outcome == "canceled":
            store.cancel(queued["jobId"])
            raise copilot_runner.AnalysisCanceled("PRIVATE-DIAGNOSTIC-CANARY")
        return response

    monkeypatch.setattr(jobs, "run_copilot", model)
    state = store.execute(queued["jobId"])
    assert state["state"] == ("failed" if outcome == "timeout" else outcome)
    assert state["processingStatus"] == "ready"
    directory = store.directory(state["jobId"])
    metrics = json.loads((directory / "processing-report.json").read_bytes())
    assert metrics["metadata"]["creditCap"] == 30
    assert metrics["workerUsage"]["reportedAICredits"] == 2.5
    assert metrics["workerUsage"]["creditValueUsd"] == 0.025
    assert metrics["workerUsage"]["inputPlusOutputTokens"] == 150
    assert metrics["workerUsage"]["actualBilledUsd"] is None
    assert metrics["coverage"]["wholeIntakeCostUsd"] is None
    assert metrics["counts"]["analysisInvocationAttempts"] == 1
    assert store.processing_report_uri(state["jobId"]) == state["processingReportPath"]
    operator_html = (directory / "processing-report.html").read_text(encoding="utf-8")
    assert "Backend AI credits<strong>2.5</strong>" in operator_html
    assert "Recorded input + output tokens<strong>150</strong>" in operator_html
    assert "<dt>inputTokens</dt><dd>120</dd>" in operator_html
    assert "<dt>outputTokens</dt><dd>30</dd>" in operator_html
    assert "<dt>cacheWriteTokens</dt>" not in operator_html
    assert "Not reported" not in operator_html
    for name in OPERATOR_FILES:
        content = (directory / name).read_text(encoding="utf-8")
        assert "PRIVATE-INTAKE-CANARY" not in content
        assert "PRIVATE-DIAGNOSTIC-CANARY" not in content


@pytest.mark.parametrize("filename", OPERATOR_FILES)
def test_operator_tampering_blocks_operator_open_not_customer_report(
    tmp_path: Path, filename: str
) -> None:
    store = JobStore(tmp_path)
    state = store.execute(queue(store)["jobId"])
    path = store.directory(state["jobId"]) / filename
    path.write_text(path.read_text(encoding="utf-8") + "\nchanged", encoding="utf-8")
    with pytest.raises(ValueError, match="integrity"):
        store.processing_report_uri(state["jobId"])
    assert store.verified_report_uri(state["jobId"]) == state["reportPath"]


def test_operator_metrics_cannot_be_forged_before_model_execution(
    tmp_path: Path, monkeypatch
) -> None:
    store = JobStore(tmp_path)
    queued = queue(store)
    path = store.directory(queued["jobId"]) / "processing-report.json"
    data = json.loads(path.read_bytes())
    data["workerUsage"]["reportedAICredits"] = 0
    path.write_text(json.dumps(data), encoding="utf-8")
    monkeypatch.setattr(
        jobs, "run_demo", lambda *args, **kwargs: pytest.fail("Tampered job executed")
    )
    assert store.execute(queued["jobId"])["state"] == "failed"


def test_retained_intake_approval_is_not_reused_as_current_preparation_latency(
    tmp_path: Path,
) -> None:
    brief, response = model_input_parts()
    entries = deferred_transcript_entries()
    entries[-1]["timestamp"] = "2026-01-01T00:00:00Z"
    request = tmp_path / "request.json"
    request.write_text(
        json.dumps(
            {
                **brief,
                **response,
                "intakeTranscript": {
                    "schemaVersion": "1.0.0",
                    "initiativeId": brief["initiativeId"],
                    "classification": "SYNTHETIC",
                    "captureStatus": "complete",
                    "entries": entries,
                    "gaps": [],
                },
            }
        ),
        encoding="utf-8",
    )
    store = JobStore(tmp_path / "jobs")
    queued = store.submit(
        request,
        DEFAULT_EXAMPLE / "sources/catalog.json",
        DEFAULT_EXAMPLE / "source-policy.json",
        DEFAULT_CUSTOMER,
        notify=False,
    )
    state = store.execute(queued["jobId"])
    assert state["state"] == "completed"
    metrics = json.loads((store.directory(state["jobId"]) / "processing-report.json").read_bytes())
    assert metrics["metadata"]["originalIntakeApprovalAt"] == entries[-1]["timestamp"]
    assert metrics["timing"]["approvalToEngineStartSeconds"] is None
    assert metrics["timing"]["approvalToPublicationSeconds"] is None
    assert metrics["timing"]["backendSeconds"] >= 0


def test_operator_trace_storage_failure_is_explicit(tmp_path: Path, monkeypatch) -> None:
    from mosaic import observability

    store = JobStore(tmp_path)
    queued = queue(store)
    write = observability.atomic_write_text

    def fail_metrics(path, content):
        if path.name == "processing-report.json":
            raise OSError("Synthetic operator storage failure")
        return write(path, content)

    monkeypatch.setattr(observability, "atomic_write_text", fail_metrics)
    state = store.execute(queued["jobId"])
    assert state["state"] == "failed"
    assert state["processingStatus"] == "failed"
    assert state["processingError"]["type"] == "OSError"
    with pytest.raises(ValueError, match="incomplete"):
        store.processing_report_uri(state["jobId"])


def test_operator_cli_opens_failed_job_diagnostics_without_regeneration(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    store = JobStore(tmp_path)
    queued = queue(store)
    store.cancel(queued["jobId"])
    opened = []
    monkeypatch.setattr(jobs, "open_default_browser", opened.append)
    assert jobs.main(["--root", str(tmp_path), "open", queued["jobId"], "--processing"]) == 0
    state = json.loads(capsys.readouterr().out)
    assert state["state"] == "canceled"
    assert opened == [state["processingReportPath"]]


def test_diagnostic_failure_after_inference_preserves_analysis_for_free_rebuild(
    tmp_path: Path, monkeypatch
) -> None:
    from mosaic import observability

    brief, response = model_input_parts()
    request = tmp_path / "brief.json"
    request.write_text(json.dumps(brief), encoding="utf-8")
    store = JobStore(tmp_path / "jobs")
    queued = store.submit(
        request,
        DEFAULT_EXAMPLE / "sources/catalog.json",
        DEFAULT_EXAMPLE / "source-policy.json",
        DEFAULT_CUSTOMER,
        notify=False,
        copilot=CopilotLimits("test-model"),
        copilot_executable=Path(sys.executable),
    )
    directory = store.directory(queued["jobId"])
    calls = []

    def model(*args, **kwargs):
        calls.append(True)
        return response

    write = observability.atomic_write_text

    def failing_metrics(path, content):
        if path.name == "processing-report.json" and (directory / "analysis-request.json").exists():
            raise OSError("Synthetic post-analysis diagnostic failure")
        return write(path, content)

    monkeypatch.setattr(jobs, "run_copilot", model)
    monkeypatch.setattr(observability, "atomic_write_text", failing_metrics)
    failed = store.execute(queued["jobId"])
    assert failed["state"] == "failed"
    assert failed["analysis"]["status"] == "completed"
    assert failed["error"]["localRebuildAvailable"] is True
    assert failed["processingStatus"] == "failed"
    monkeypatch.setattr(observability, "atomic_write_text", write)
    rebuilt = store.rebuild(queued["jobId"])
    assert store.execute(rebuilt["jobId"])["state"] == "completed"
    assert calls == [True]


@pytest.mark.parametrize("legacy", [False, True])
def test_response_validation_recovery_reuses_exact_model_output_without_inference(
    tmp_path: Path,
    monkeypatch,
    legacy: bool,
) -> None:
    brief, response = model_input_parts()
    del response["designDraft"]["implementationStatus"]
    request = tmp_path / "brief.json"
    request.write_text(json.dumps(brief), encoding="utf-8")
    store = JobStore(tmp_path / "jobs")
    queued = store.submit(
        request,
        DEFAULT_EXAMPLE / "sources/catalog.json",
        DEFAULT_EXAMPLE / "source-policy.json",
        DEFAULT_CUSTOMER,
        notify=False,
        copilot=CopilotLimits("test-model"),
        copilot_executable=Path(sys.executable),
    )
    calls = []
    prepare = jobs.prepare_request

    def model(*args, **kwargs):
        calls.append(True)
        return response

    def old_contract(*args, **kwargs):
        raise ValueError(
            "Copilot analysis response is invalid at designDraft: "
            "'implementationStatus' is a required property"
        )

    monkeypatch.setattr(jobs, "run_copilot", model)
    monkeypatch.setattr(jobs, "prepare_request", old_contract)
    failed = store.execute(queued["jobId"])
    assert failed["state"] == "failed"
    assert failed["analysis"]["responseDigest"] == jobs._digest(response)
    assert failed["error"]["localRebuildAvailable"] is True
    assert "without another model call" in failed["error"]["message"]

    expected_digest = None
    if legacy:
        state = store.status(queued["jobId"])
        expected_digest = state["analysis"].pop("responseDigest")
        jobs._write_json(store.directory(queued["jobId"]) / "status.json", state)
        monkeypatch.setattr(jobs, "prepare_request", prepare)
        with pytest.raises(ValueError, match="exact expected digest"):
            store.rebuild(queued["jobId"])
        with pytest.raises(ValueError, match="integrity is unverified"):
            store.rebuild(queued["jobId"], expected_response_digest="0" * 64)
    else:
        monkeypatch.setattr(jobs, "prepare_request", prepare)

    rebuilt = store.rebuild(
        queued["jobId"],
        expected_response_digest=expected_digest,
    )
    assert rebuilt["recovery"] == {
        "mode": "retained-response",
        "sourceJobId": queued["jobId"],
        "modelCallRepeated": False,
    }
    recovered = store.execute(rebuilt["jobId"])
    assert recovered["state"] == "completed"
    assert recovered["artifactCount"] == 23
    assert calls == [True]
    authored = json.loads(
        (store.directory(queued["jobId"]) / "analysis-request.json").read_text(encoding="utf-8")
    )
    assert authored["designDraft"]["implementationStatus"] == "not_started"
    metrics = json.loads(
        (store.directory(rebuilt["jobId"]) / "processing-report.json").read_text(encoding="utf-8")
    )
    assert metrics["counts"]["analysisInvocationAttempts"] == 0
    assert metrics["metadata"]["recovery"]["mode"] == "retained-response"


def test_rejected_cli_input_returns_a_safe_preflight_trace_without_a_job(
    tmp_path: Path, capsys
) -> None:
    request = tmp_path / "invalid.json"
    request.write_text('{"classification":"SYNTHETIC"}', encoding="utf-8")
    root = tmp_path / "jobs"
    assert (
        jobs.main(["--root", str(root), "generate", "--request", str(request), "--reference"]) == 1
    )
    result = json.loads(capsys.readouterr().out)
    assert result["trace"][-1]["step"] == "submission.rejected"
    assert result["trace"][-1]["status"] == "failed"
    assert not root.exists()


def test_copilot_settings_require_explicit_authorization(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="explicit"):
        queue(JobStore(tmp_path), copilot_executable=Path(sys.executable))


@pytest.mark.parametrize("outcome", ["transient", "persistent", "validation", "renderer"])
def test_report_retries_and_rebuild_never_repeat_model_analysis(
    tmp_path: Path,
    monkeypatch,
    capsys,
    outcome: str,
) -> None:
    brief, response = model_input_parts()
    brief["stakeholders"] = ["Employee Services business owner", "Finance policy owner"]
    brief_path = tmp_path / "brief.json"
    brief_path.write_text(json.dumps(brief), encoding="utf-8")
    store = JobStore(tmp_path / "jobs")
    queued = store.submit(
        brief_path,
        DEFAULT_EXAMPLE / "sources/catalog.json",
        DEFAULT_EXAMPLE / "source-policy.json",
        DEFAULT_CUSTOMER,
        notify=False,
        copilot=CopilotLimits("test-model"),
        copilot_executable=Path(sys.executable),
    )
    model_calls = []
    report_calls = []
    progress = []
    delays = []
    render = jobs.run_demo

    def model(*args, **kwargs):
        model_calls.append(True)
        return response

    def generate(*args, **kwargs):
        report_calls.append(True)
        if outcome == "transient" and len(report_calls) == 2:
            return render(*args, **kwargs)
        args[-1].mkdir()
        (args[-1] / "partial.html").write_text("partial", encoding="utf-8")
        if outcome == "validation":
            raise ValueError("Invalid report; must not retry validation errors automatically")
        if outcome == "renderer":
            raise UndefinedError("'str object' has no attribute 'role'")
        error = PermissionError("Synthetic temporary sharing violation")
        error.winerror = 32
        raise error

    monkeypatch.setattr(jobs, "run_copilot", model)
    monkeypatch.setattr(jobs, "run_demo", generate)
    monkeypatch.setattr(jobs.time, "sleep", delays.append)
    result = store.execute(queued["jobId"], on_progress=progress.append)
    assert model_calls == [True]
    assert (
        len(report_calls)
        == {
            "transient": 2,
            "persistent": 3,
            "validation": 1,
            "renderer": 1,
        }[outcome]
    )
    assert (
        delays
        == {
            "transient": [0.05],
            "persistent": [0.05, 0.1],
            "validation": [],
            "renderer": [],
        }[outcome]
    )
    assert sum("No additional model call" in message for message in progress) == len(delays)
    assert not (store.directory(queued["jobId"]) / ".working").exists()
    metrics = json.loads((store.directory(queued["jobId"]) / "processing-report.json").read_bytes())
    assert metrics["counts"]["localReportRetries"] == len(delays)
    assert metrics["counts"]["analysisInvocationAttempts"] == 1
    if outcome == "transient":
        assert result["state"] == "completed"
        assert result["artifactCount"] == 23
        return
    assert result["state"] == "failed"
    assert result["reportPath"] is None
    assert result["error"]["localRebuildAvailable"] is True
    assert result["error"]["nextAction"] == (
        "review_failure" if outcome == "validation" else "repair_then_rebuild"
    )
    assert "Saved input is preserved" in result["error"]["message"]
    assert ("review the cause" if outcome == "validation" else "local cause") in result["error"][
        "message"
    ]
    status_page = (store.directory(queued["jobId"]) / "status.html").read_text(encoding="utf-8")
    assert "Saved input is preserved" in status_page
    assert 'http-equiv="refresh"' not in status_page
    monkeypatch.setattr(jobs, "run_demo", render)
    assert jobs.main(["--root", str(store.root), "rebuild", queued["jobId"]]) == 0
    recovered = json.loads(capsys.readouterr().out)
    assert recovered["state"] == "completed"
    assert recovered["artifactCount"] == 23
    assert recovered["reviewState"] == "awaiting_human_review"
    assert recovered["releaseAuthorized"] is False
    assert recovered["notification"]["status"] == "disabled"
    assert recovered["recovery"] == {
        "mode": "retained-input",
        "sourceJobId": queued["jobId"],
        "modelCallRepeated": False,
    }
    assert recovered["jobId"] != queued["jobId"]
    assert store.status(queued["jobId"])["state"] == "failed"
    assert model_calls == [True]
    recovery_metrics = json.loads(
        (store.directory(recovered["jobId"]) / "processing-report.json").read_bytes()
    )
    assert recovery_metrics["workerUsage"]["reportedAICredits"] == 0
    assert recovery_metrics["counts"]["analysisInvocationAttempts"] == 0
    assert recovery_metrics["metadata"]["recovery"]["sourceJobId"] == queued["jobId"]


@pytest.mark.parametrize("defect", ["input", "evidence", "unvalidated", "retained"])
def test_rebuild_rejects_changed_or_unvalidated_input(
    tmp_path: Path,
    monkeypatch,
    defect: str,
) -> None:
    store = JobStore(tmp_path)
    queued = queue(store)

    def fail_generation(*args, **kwargs):
        raise ValueError("Synthetic report failure")

    monkeypatch.setattr(jobs, "run_demo", fail_generation)
    store.execute(queued["jobId"])
    directory = store.directory(queued["jobId"])
    if defect == "unvalidated":
        state = store.status(queued["jobId"])
        state["analysis"] = {
            "status": "failed",
            "model": "test-model",
            "max_ai_credits": 30,
        }
        jobs._write_json(directory / "status.json", state)
    elif defect == "retained":
        state = store.status(queued["jobId"])
        state["analysis"] = {
            "status": "completed",
            "model": "test-model",
            "max_ai_credits": 30,
        }
        jobs._write_json(directory / "status.json", state)
        (directory / "analysis-request.json").write_bytes(
            (directory / "snapshot/request.json").read_bytes() + b" ",
        )
    else:
        path = (
            directory
            / "snapshot"
            / ("request.json" if defect == "input" else "sources/synthetic-intake.md")
        )
        path.write_bytes(path.read_bytes() + b" ")
    with pytest.raises(ValueError, match="integrity|requires approval"):
        store.rebuild(queued["jobId"])
    assert len(list(tmp_path.glob("SYN-*/JOB-*"))) == 1


@pytest.mark.parametrize("mode", ["submit", "generate"])
def test_copilot_configured_cli_submits_only_with_explicit_opt_in(
    tmp_path: Path,
    monkeypatch,
    capsys,
    mode: str,
) -> None:
    root = tmp_path / "jobs"
    base = ["--root", str(root)]
    assert (
        jobs.main(
            [
                *base,
                "configure-copilot",
                "--copilot-executable",
                sys.executable,
                "--model",
                "test-model",
                "--max-ai-credits",
                "30",
            ]
        )
        == 0
    )
    configuration = json.loads(capsys.readouterr().out)
    assert configuration["limits"]["max_ai_credits"] == 30
    assert jobs.main([*base, "copilot-settings"]) == 0
    assert json.loads(capsys.readouterr().out) == configuration
    brief, response = model_input_parts()
    path = tmp_path / "brief.json"
    path.write_text(json.dumps(brief), encoding="utf-8")
    model_calls = []

    def model(*args, **kwargs):
        model_calls.append(True)
        return response

    monkeypatch.setattr(jobs, "run_copilot", model)
    monkeypatch.setattr(JobStore, "start", lambda *args: None)
    assert jobs.main([*base, mode, "--request", str(path), "--no-notify"]) == 1
    capsys.readouterr()
    assert (
        jobs.main([*base, mode, "--request", str(path), "--no-notify", "--analyze-with-copilot"])
        == 0
    )
    state = json.loads(capsys.readouterr().out)
    assert state["state"] == ("completed" if mode == "generate" else "queued")
    assert state["analysis"]["model"] == "test-model"
    assert state["analysis"]["max_ai_credits"] == 30
    assert model_calls == ([True] if mode == "generate" else [])


@pytest.mark.parametrize("failure", ["missing", "changed", "implicit_limits"])
def test_copilot_saved_configuration_fails_closed(
    tmp_path: Path,
    capsys,
    failure: str,
) -> None:
    store = JobStore(tmp_path / "jobs")
    executable = tmp_path / "copilot.exe"
    executable.write_bytes(b"fake executable; never launched")
    if failure != "missing":
        store.configure_copilot(executable, CopilotLimits("test-model"))
    if failure == "changed":
        executable.write_bytes(b"changed")
    if failure == "implicit_limits":
        assert (
            jobs.main(
                [
                    "--root",
                    str(store.root),
                    "submit",
                    "--request",
                    "unused.json",
                    "--max-ai-credits",
                    "30",
                ]
            )
            == 1
        )
        assert "explicit" in capsys.readouterr().out
    else:
        with pytest.raises(ValueError, match="[Cc]onfigure"):
            store.copilot_configuration()


@pytest.mark.parametrize("override", ["hooks", "plugins", "mcp-config.json", "config.json"])
def test_copilot_home_rejects_unapproved_automation(tmp_path: Path, override: str) -> None:
    (tmp_path / override).write_text('{"mcpServers":{}}', encoding="utf-8")
    with pytest.raises(ValueError, match="unapproved"):
        copilot_runner.validate_cli_home(tmp_path)


@pytest.mark.parametrize(
    "settings",
    [
        '// CLI configuration\n{"trusted_folders": [],}',
        '// CLI configuration\n{"mcpServers": {}}',
        '// CLI configuration\n{"trusted_folders": [], "trusted_folders": ["/"]}',
    ],
)
def test_copilot_jsonc_configuration_preserves_override_checks(
    tmp_path: Path,
    settings: str,
) -> None:
    (tmp_path / "config.json").write_text(settings, encoding="utf-8")
    if settings.count("trusted_folders") == 1:
        copilot_runner.validate_cli_home(tmp_path)
    else:
        with pytest.raises(ValueError):
            copilot_runner.validate_cli_home(tmp_path)


@pytest.mark.parametrize("when", ["before", "during"])
def test_copilot_job_rejects_changed_runtime(tmp_path: Path, monkeypatch, when: str) -> None:
    brief, response = model_input_parts()
    brief_path = tmp_path / "brief.json"
    brief_path.write_text(json.dumps(brief), encoding="utf-8")
    executable = tmp_path / "copilot.exe"
    executable.write_bytes(b"fake executable; never launched")
    entry = tmp_path / "app.js"
    entry.write_text("original", encoding="utf-8")
    store = JobStore(tmp_path / "jobs")
    queued = store.submit(
        brief_path,
        DEFAULT_EXAMPLE / "sources/catalog.json",
        DEFAULT_EXAMPLE / "source-policy.json",
        DEFAULT_CUSTOMER,
        notify=False,
        copilot=CopilotLimits("test-model"),
        copilot_executable=executable,
    )

    def model(*args, **kwargs):
        assert when == "during"
        entry.write_text("changed", encoding="utf-8")
        return response

    monkeypatch.setattr(jobs, "run_copilot", model)
    if when == "before":
        entry.write_text("changed", encoding="utf-8")
    result = store.execute(queued["jobId"])
    assert result["state"] == "failed"
    assert result["reportPath"] is None
    assert not list(store.directory(queued["jobId"]).glob("report-*"))


def test_cancel_before_work_never_generates(tmp_path: Path, monkeypatch) -> None:
    store = JobStore(tmp_path)
    queued = queue(store)
    monkeypatch.setattr(jobs, "run_demo", lambda *args: pytest.fail("Canceled work executed"))
    assert store.cancel(queued["jobId"])["state"] == "canceled"
    assert store.execute(queued["jobId"])["state"] == "canceled"
    assert store.status(queued["jobId"])["reportPath"] is None


def test_running_cancellation_discards_generated_report(tmp_path: Path, monkeypatch) -> None:
    store = JobStore(tmp_path)
    queued = queue(store)
    original = jobs.run_demo

    def cancel_during_generation(*args, **kwargs):
        assert store.cancel(queued["jobId"])["cancellationRequested"]
        return original(*args, **kwargs)

    monkeypatch.setattr(jobs, "run_demo", cancel_during_generation)
    assert store.execute(queued["jobId"])["state"] == "canceled"
    assert not list(store.directory(queued["jobId"]).glob("report-*"))


@pytest.mark.parametrize("tampered", ["request.json", "sources/synthetic-intake.md"])
def test_tampered_snapshot_fails_closed(tmp_path: Path, tampered: str) -> None:
    store = JobStore(tmp_path)
    queued = queue(store)
    snapshot = store.directory(queued["jobId"]) / "snapshot" / tampered
    snapshot.write_bytes(snapshot.read_bytes() + b" ")
    failed = store.execute(queued["jobId"])
    assert failed["state"] == "failed"
    assert failed["error"]["type"] == "ValueError"
    assert failed["reportPath"] is None


def test_generation_failure_never_publishes_partial_output(tmp_path: Path, monkeypatch) -> None:
    store = JobStore(tmp_path)
    queued = queue(store)

    def fail_generation(*args, **kwargs):
        args[-1].mkdir()
        (args[-1] / "partial.html").write_text("partial", encoding="utf-8")
        raise ValueError("private details must not appear in notifications")

    monkeypatch.setattr(jobs, "run_demo", fail_generation)
    failed = store.execute(queued["jobId"])
    assert failed["state"] == "failed"
    assert failed["reportPath"] is None
    assert "private details" not in json.dumps(failed)
    assert not (store.directory(queued["jobId"]) / ".working").exists()


def test_jobs_require_explicit_reference_and_private_containment(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="ignored build"):
        JobStore(PROJECT_ROOT / "published-jobs")
    store = JobStore(tmp_path)
    with pytest.raises(ValueError, match="conversational request"):
        store.submit(
            DEFAULT_EXAMPLE / "request.json",
            DEFAULT_EXAMPLE / "sources/catalog.json",
            DEFAULT_EXAMPLE / "source-policy.json",
            DEFAULT_CUSTOMER,
        )
    with pytest.raises(ValueError, match="Invalid local job"):
        store.status("../../outside")


def test_weakened_source_policy_is_rejected_before_queueing(tmp_path: Path) -> None:
    policy = json.loads((DEFAULT_EXAMPLE / "source-policy.json").read_text(encoding="utf-8"))
    policy["networkAccess"] = True
    policy_path = tmp_path / "policy.json"
    policy_path.write_text(json.dumps(policy), encoding="utf-8")
    store = JobStore(tmp_path / "jobs")
    with pytest.raises(ValueError, match="cannot weaken"):
        store.submit(
            DEFAULT_EXAMPLE / "request.json",
            DEFAULT_EXAMPLE / "sources/catalog.json",
            policy_path,
            DEFAULT_CUSTOMER,
            reference=True,
        )
    assert not store.root.exists()


def test_detached_worker_uses_this_checkout_and_finishes(tmp_path: Path, monkeypatch) -> None:
    store = JobStore(tmp_path)
    queued = queue(store)
    monkeypatch.setenv("PYTHONPATH", str(tmp_path / "other-checkout"))
    process = store.start(queued["jobId"])
    assert process.wait(timeout=30) == 0
    completed = store.status(queued["jobId"])
    assert completed["state"] == "completed"
    assert completed["launchPid"] == process.pid
    assert completed["workerPid"] > 0
    assert completed["workerPid"] != jobs.os.getpid()
    status_page = store.directory(queued["jobId"]) / "status.html"
    assert "Ready for review" in status_page.read_text(encoding="utf-8")
    with pytest.raises(ValueError, match="already started"):
        store.start(queued["jobId"])


@pytest.mark.parametrize("error_type", [None, OSError, jobs.webbrowser.Error])
def test_browser_handoff_can_retry_without_regenerating(
    tmp_path: Path,
    monkeypatch,
    capsys,
    error_type: type[Exception] | None,
) -> None:
    store = JobStore(tmp_path)
    queued = queue(store)
    completed = store.execute(queued["jobId"])
    opened = []

    def open_browser(uri):
        opened.append(uri)
        if error_type and len(opened) == 1:
            raise error_type("Synthetic browser launch failure")

    monkeypatch.setattr(jobs, "open_default_browser", open_browser)
    monkeypatch.setattr(jobs, "run_copilot", lambda *args: pytest.fail("Unexpected model call"))
    monkeypatch.setattr(jobs, "run_demo", lambda *args: pytest.fail("Unexpected generation"))
    command = ["--root", str(tmp_path), "open", queued["jobId"]]
    assert jobs.main(command) == int(error_type is not None)
    result = json.loads(capsys.readouterr().out)
    assert result["state"] == "completed"
    assert result["browser"]["status"] == ("failed" if error_type else "requested")
    assert result["reportPath"] == completed["reportPath"]
    assert store.status(queued["jobId"]) == completed
    assert jobs.main(command) == 0
    retried = json.loads(capsys.readouterr().out)
    assert retried["browser"]["status"] == "requested"
    assert opened == [completed["reportPath"], completed["reportPath"]]


@pytest.mark.parametrize("defect", ["queued", "report", "manifest", "link"])
def test_browser_handoff_rejects_unfinished_or_changed_reports(
    tmp_path: Path,
    monkeypatch,
    defect: str,
) -> None:
    store = JobStore(tmp_path)
    queued = queue(store)
    directory = store.directory(queued["jobId"])
    if defect != "queued":
        completed = store.execute(queued["jobId"])
        if defect == "report":
            path = directory / f"report-{completed['reportRevision'][:16]}" / "index.html"
            path.write_text("changed", encoding="utf-8")
        elif defect == "manifest":
            jobs._write_json(directory / "report-manifest.json", {})
        else:
            completed["reportPath"] = "https://unapproved.example"
            jobs._write_json(directory / "status.json", completed)
    monkeypatch.setattr(
        jobs,
        "open_default_browser",
        lambda *args: pytest.fail("Unverified report opened"),
    )
    with pytest.raises(ValueError, match="completed report|integrity"):
        store.open_report(queued["jobId"])


@pytest.mark.skipif(os.name != "nt", reason="Windows default-browser association")
@pytest.mark.parametrize("available", [True, False])
def test_windows_browser_opener_uses_https_handler_not_html_association(
    tmp_path: Path,
    monkeypatch,
    available: bool,
) -> None:
    import ctypes
    from ctypes import wintypes

    executable = tmp_path / "Default Browser.exe"
    executable.write_bytes(b"synthetic; never executed")
    uri = (tmp_path / "report with spaces" / "index.html").as_uri()
    launched = []

    class AssociationQuery:
        def __call__(self, flags, kind, association, verb, buffer, length):
            assert (flags, kind, association, verb) == (0x1000, 2, "https", "open")
            if not available:
                return -1
            ctypes.cast(length, ctypes.POINTER(wintypes.DWORD)).contents.value = (
                len(
                    str(executable),
                )
                + 1
            )
            if buffer is None:
                return 1
            buffer.value = str(executable)
            return 0

    monkeypatch.setattr(
        ctypes,
        "WinDLL",
        lambda *args: SimpleNamespace(AssocQueryStringW=AssociationQuery()),
    )
    monkeypatch.setattr(
        jobs.subprocess,
        "Popen",
        lambda command, **kwargs: launched.append((command, kwargs)),
    )
    if available:
        jobs.open_default_browser(uri)
        assert launched[0][0] == [str(executable), uri]
        assert not launched[0][1].get("shell")
    else:
        with pytest.raises(OSError, match="default desktop browser"):
            jobs.open_default_browser(uri)
        assert launched == []


@pytest.mark.parametrize("delivery", ["submitted_to_windows", "blocked_by_settings", "error"])
def test_notification_delivery_is_separate_and_exact(
    tmp_path: Path,
    monkeypatch,
    delivery: str,
) -> None:
    store = JobStore(tmp_path)
    queued = store.submit(
        DEFAULT_EXAMPLE / "request.json",
        DEFAULT_EXAMPLE / "sources/catalog.json",
        DEFAULT_EXAMPLE / "source-policy.json",
        DEFAULT_CUSTOMER,
        reference=True,
    )
    completed = store.execute(queued["jobId"])
    payloads = []

    def notify(title, message, uri):
        payloads.append((title, message, uri))
        if delivery == "error":
            raise OSError("Notification service unavailable")
        return delivery

    monkeypatch.setattr(jobs, "send_windows_notification", notify)
    result = store.notify(queued["jobId"])
    assert result["state"] == "completed"
    assert result["releaseAuthorized"] is False
    assert result["notification"]["status"] == ("failed" if delivery == "error" else delivery)
    assert payloads[0][2] == completed["reportPath"]
    assert "customerId" not in payloads[0][1]
    store.notify(queued["jobId"])
    assert len(payloads) == 1
    store.notify(queued["jobId"], retry=True)
    assert len(payloads) == (1 if delivery == "submitted_to_windows" else 2)


@pytest.mark.parametrize("outcome", ["failed", "canceled"])
def test_unsuccessful_job_notification_links_only_generic_status(
    tmp_path: Path,
    monkeypatch,
    outcome: str,
) -> None:
    store = JobStore(tmp_path)
    queued = store.submit(
        DEFAULT_EXAMPLE / "request.json",
        DEFAULT_EXAMPLE / "sources/catalog.json",
        DEFAULT_EXAMPLE / "source-policy.json",
        DEFAULT_CUSTOMER,
        reference=True,
    )
    if outcome == "canceled":
        store.cancel(queued["jobId"])
    else:

        def fail_generation(*args, **kwargs):
            raise ValueError("Private business details")

        monkeypatch.setattr(jobs, "run_demo", fail_generation)
        store.execute(queued["jobId"])
    payloads = []

    def notify(title, message, uri):
        payloads.append((title, message, uri))
        return "submitted_to_windows"

    monkeypatch.setattr(jobs, "send_windows_notification", notify)
    result = store.notify(queued["jobId"])
    assert result["state"] == outcome
    assert result["reportPath"] is None
    assert result["releaseAuthorized"] is False
    assert result["notification"]["status"] == "submitted_to_windows"
    assert payloads == [
        (
            f"MOSAIC report job {outcome}",
            "No completed report is available. Job details remain local.",
            (store.directory(queued["jobId"]) / "status.html").as_uri(),
        )
    ]
    assert "Private business details" not in json.dumps(result)


def test_interrupted_worker_is_visible_and_cannot_resume(tmp_path: Path) -> None:
    store = JobStore(tmp_path)
    queued = queue(store)
    directory = store.directory(queued["jobId"])
    store._transition(directory, queued, "running")
    interrupted = store.inspect(queued["jobId"])
    assert interrupted["state"] == "failed"
    assert interrupted["error"]["type"] == "InterruptedWorker"
    assert store.execute(queued["jobId"])["state"] == "failed"


@pytest.mark.parametrize("setting", ["enabled", "disabled", "not_found", "access_denied"])
def test_windows_preflight_preserves_settings_and_reports_only_submission(
    monkeypatch,
    setting,
) -> None:
    sent = []

    class Notifier:
        @property
        def setting(self):
            if setting in {"not_found", "access_denied"}:
                error = OSError("Windows notification preflight")
                error.winerror = -2147023728 if setting == "not_found" else -2147024891
                raise error
            return 0 if setting == "enabled" else 1

    toaster = SimpleNamespace(toastNotifier=Notifier(), show_toast=sent.append)
    registry = SimpleNamespace(HKEY_CURRENT_USER=0, OpenKey=lambda *args: nullcontext())
    library = SimpleNamespace(
        InteractableWindowsToaster=lambda *args, **kwargs: toaster,
        Toast=lambda fields, **kwargs: SimpleNamespace(text_fields=fields, **kwargs),
    )
    monkeypatch.setattr(jobs.os, "name", "nt")
    monkeypatch.setitem(sys.modules, "winreg", registry)
    monkeypatch.setitem(sys.modules, "windows_toasts", library)
    monkeypatch.setitem(
        sys.modules,
        "winrt.windows.ui.notifications",
        SimpleNamespace(
            NotificationSetting=SimpleNamespace(ENABLED=0),
        ),
    )
    if setting == "access_denied":
        with pytest.raises(OSError):
            jobs.send_windows_notification("MOSAIC", "Ready", "file:///C:/synthetic/index.html")
        assert sent == []
    else:
        result = jobs.send_windows_notification(
            "MOSAIC", "Ready", "file:///C:/synthetic/index.html"
        )
        expected = "blocked_by_settings" if setting == "disabled" else "submitted_to_windows"
        assert result == expected
        assert len(sent) == (0 if setting == "disabled" else 1)
