# SPDX-License-Identifier: LicenseRef-MOSAIC-Evaluation
"""Local, integrity-checked jobs with optional bounded analysis. No customer approvals."""

from __future__ import annotations

import argparse
import errno
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time
import traceback
import webbrowser
from collections.abc import Callable, Iterator, Sequence
from contextlib import contextmanager
from copy import deepcopy
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from mosaic.cli import DEFAULT_CUSTOMER, DEFAULT_EXAMPLE, PROJECT_ROOT, run_demo
from mosaic.connectors import SyntheticSourceConnector
from mosaic.copilot_runner import (
    AnalysisCanceled,
    CopilotLimits,
    build_prompt,
    prepare_request,
    restricted_command,
    run_copilot,
    runtime_hashes,
    validate_brief,
    validate_cli_home,
)
from mosaic.observability import OPERATOR_FILES, ProcessingRun, observed_step, recovery_metadata
from mosaic.reports import render_job_status
from mosaic.schema_validation import validate_instance
from mosaic.storage import atomic_write_text
from mosaic.transcript import validate_transcript

DEFAULT_JOB_ROOT = PROJECT_ROOT / "build" / "intake"
TERMINAL_STATES = {"completed", "failed", "canceled"}
JOB_PATTERN = re.compile(r"JOB-(SYN-[A-Za-z0-9][A-Za-z0-9-]*)-([a-f0-9]{32})")


def _now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_bytes())
    if not isinstance(value, dict):
        raise ValueError("Job input must be a JSON object.")
    return value


def _write_json(path: Path, value: dict[str, Any]) -> None:
    atomic_write_text(path, json.dumps(value, indent=2, ensure_ascii=True) + "\n")
    if path.name == "status.json":
        atomic_write_text(path.with_name("status.html"), render_job_status(value))


def _digest(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode("utf-8")).hexdigest()


def _canonicalize_capture_entries(entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    canonical = deepcopy(entries)
    for entry in canonical:
        descriptions = entry.get("optionDescriptions")
        if not isinstance(descriptions, list):
            continue
        options = entry.get("options")
        if (
            not isinstance(options, list)
            or len(descriptions) != len(options)
            or any(not isinstance(option, str) for option in options)
            or len(set(options)) != len(options)
            or any(not isinstance(description, str) for description in descriptions)
        ):
            raise ValueError(
                "Parallel optionDescriptions must contain one string for each unique option."
            )
        entry["optionDescriptions"] = dict(zip(options, descriptions, strict=True))
    return canonical


def _new_transcript(initiative_id: str) -> dict[str, Any]:
    return {
        "schemaVersion": "1.0.0",
        "initiativeId": initiative_id,
        "classification": "SYNTHETIC",
        "captureStatus": "partial",
        "startedAt": _now(),
        "endedAt": None,
        "gaps": [],
        "entries": [],
    }


def _merge_capture_batch(
    transcript: dict[str, Any],
    entries: list[dict[str, Any]],
    *,
    gap: str | None,
    complete: bool,
) -> bool:
    changed = False
    previous_sequence = None
    for entry in entries:
        sequence = entry.get("sequence")
        if (
            type(sequence) is not int
            or not 1 <= sequence <= len(transcript["entries"]) + 1
            or previous_sequence is not None
            and sequence != previous_sequence + 1
        ):
            raise ValueError("Capture the next sequential turn; do not skip or reorder entries.")
        previous_sequence = sequence
        if sequence <= len(transcript["entries"]):
            if transcript["entries"][sequence - 1] != entry:
                raise ValueError("Captured turns cannot be overwritten; append a correction.")
        else:
            if transcript["captureStatus"] == "complete" or transcript.get("endedAt"):
                raise ValueError("This transcript is closed; start a separate intake revision.")
            transcript["entries"].append(entry)
            changed = True
            if entry.get("kind") == "generation_approval":
                transcript["endedAt"] = _now()
    if gap and gap not in transcript["gaps"]:
        transcript["gaps"].append(gap)
        changed = True
    if complete and transcript["captureStatus"] != "complete":
        transcript["captureStatus"] = "complete"
        changed = True
    return changed


def _retry_local_io(
    operation: Callable[[], Any],
    on_retry: Callable[[int], None] | None = None,
) -> Any:
    for attempt in range(3):
        try:
            return operation()
        except OSError as error:
            transient = getattr(error, "winerror", None) in {5, 32, 33} or error.errno in {
                errno.EAGAIN,
                errno.EBUSY,
                errno.EINTR,
            }
            if not transient or attempt == 2:
                raise
            if on_retry:
                on_retry(attempt + 2)
            time.sleep(0.05 * (attempt + 1))


def _publish_directory(source: Path, destination: Path) -> None:
    _retry_local_io(lambda: source.rename(destination))


def _file_hashes(directory: Path) -> dict[str, str]:
    files = {}
    for path in sorted(directory.rglob("*")):
        if path.is_symlink() or not path.resolve().is_relative_to(directory.resolve()):
            raise ValueError("Job snapshots and reports cannot contain redirected paths.")
        if path.is_file():
            files[path.relative_to(directory).as_posix()] = hashlib.sha256(
                path.read_bytes()
            ).hexdigest()
    return files


def _engine_digest() -> str:
    paths = [
        *sorted((PROJECT_ROOT / "src/mosaic").rglob("*.py")),
        *sorted((PROJECT_ROOT / "schemas").glob("*.json")),
        *sorted(path for path in (PROJECT_ROOT / "templates").iterdir() if path.is_file()),
    ]
    return _digest(
        {
            path.relative_to(PROJECT_ROOT).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in paths
        }
    )


def send_windows_notification(title: str, message: str, launch_uri: str) -> str:
    if os.name != "nt":
        return "unsupported_platform"
    import winreg

    from windows_toasts import InteractableWindowsToaster, Toast
    from winrt.windows.ui.notifications import NotificationSetting

    application_id = "MOSAIC.LocalReports"
    registry_path = rf"SOFTWARE\Classes\AppUserModelId\{application_id}"
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, registry_path):
            pass
    except FileNotFoundError:
        with winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, registry_path) as application_key:
            winreg.SetValueEx(application_key, "DisplayName", 0, winreg.REG_SZ, "MOSAIC")
    toaster = InteractableWindowsToaster("MOSAIC", notifierAUMID=application_id)
    try:
        if toaster.toastNotifier.setting != NotificationSetting.ENABLED:
            return "blocked_by_settings"
    except OSError as error:
        if error.winerror != -2147023728:
            raise
    toast = Toast([title, message], launch_action=launch_uri)
    toast.group = "mosaic-local-reports"
    toaster.show_toast(toast)
    return "submitted_to_windows"


def open_default_browser(uri: str) -> None:
    if os.name != "nt":
        if not webbrowser.open(uri, new=2):
            raise OSError("The default browser did not accept the document link.")
        return
    import ctypes
    from ctypes import wintypes

    query = ctypes.WinDLL("shlwapi").AssocQueryStringW
    query.argtypes = [
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.LPCWSTR,
        wintypes.LPCWSTR,
        wintypes.LPWSTR,
        ctypes.POINTER(wintypes.DWORD),
    ]
    query.restype = wintypes.LONG
    protocol_association = 0x1000
    executable_string = 2
    length = wintypes.DWORD()
    if (
        query(protocol_association, executable_string, "https", "open", None, ctypes.byref(length))
        != 1
        or not 1 < length.value <= 32768
    ):
        raise OSError("Configure a default desktop browser before opening documents.")
    buffer = ctypes.create_unicode_buffer(length.value)
    if (
        query(
            protocol_association, executable_string, "https", "open", buffer, ctypes.byref(length)
        )
        != 0
    ):
        raise OSError("The default browser association could not be read.")
    executable = Path(buffer.value)
    if (
        not executable.is_absolute()
        or not executable.is_file()
        or executable.suffix.lower() != ".exe"
    ):
        raise OSError("The default browser executable is unavailable.")
    subprocess.Popen(
        [str(executable), uri],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


@contextmanager
def _lock(path: Path, *, blocking: bool = True) -> Iterator[None]:
    """Hold an operating-system lock across the caller's critical section."""
    with path.open("a+b") as stream:
        if stream.tell() == 0:
            stream.write(b"0")
            stream.flush()
        stream.seek(0)
        if os.name == "nt":
            import msvcrt

            msvcrt.locking(stream.fileno(), msvcrt.LK_LOCK if blocking else msvcrt.LK_NBLCK, 1)
        else:
            import fcntl

            fcntl.flock(stream.fileno(), fcntl.LOCK_EX | (0 if blocking else fcntl.LOCK_NB))
        try:
            yield
        finally:
            stream.seek(0)
            if os.name == "nt":
                msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(stream.fileno(), fcntl.LOCK_UN)


class JobStore:
    """Manage one customer's local capture, job state and immutable report revisions."""

    def __init__(self, root: Path = DEFAULT_JOB_ROOT) -> None:
        self.root = root.resolve()
        if self.root.is_relative_to(PROJECT_ROOT) and not self.root.is_relative_to(
            PROJECT_ROOT / "build"
        ):
            raise ValueError("Local jobs inside this repository must stay under ignored build/.")

    def configure_copilot(self, executable: Path, limits: CopilotLimits) -> dict[str, Any]:
        executable = executable.resolve()
        if not executable.is_file() or executable.suffix.lower() in {".cmd", ".bat", ".ps1"}:
            raise ValueError("Configure the native Copilot executable, not a shell wrapper.")
        validate_cli_home(self.root / ".copilot-cli")
        configuration = {
            "provider": "copilot-cli",
            "executable": str(executable),
            "limits": asdict(limits),
            "runtimeFiles": runtime_hashes(executable),
        }
        self.root.mkdir(parents=True, exist_ok=True)
        _write_json(self.root / "copilot-worker.json", configuration)
        return configuration

    def copilot_configuration(self) -> dict[str, Any]:
        path = self.root / "copilot-worker.json"
        if not path.is_file() or path.resolve() != path:
            raise ValueError("Configure the local Copilot worker before requesting model analysis.")
        configuration = _read_json(path)
        CopilotLimits(**configuration["limits"])
        if runtime_hashes(Path(configuration["executable"])) != configuration["runtimeFiles"]:
            raise ValueError("Configured Copilot runtime changed; configure it again before use.")
        validate_cli_home(self.root / ".copilot-cli")
        return configuration

    def directory(self, job_id: str) -> Path:
        match = JOB_PATTERN.fullmatch(job_id)
        if not match:
            raise ValueError("Invalid local job ID.")
        directory = self.root / match[1] / job_id
        if directory.resolve() != directory:
            raise ValueError("Job paths cannot be redirected.")
        return directory

    def status(self, job_id: str) -> dict[str, Any]:
        return _read_json(self.directory(job_id) / "status.json")

    def capture(
        self,
        initiative_id: str,
        entry: dict[str, Any],
        *,
        gap: str | None = None,
        complete: bool = False,
    ) -> dict[str, Any]:
        return self.capture_batch(initiative_id, [entry], gap=gap, complete=complete)

    def capture_batch(
        self,
        initiative_id: str,
        entries: list[dict[str, Any]],
        *,
        gap: str | None = None,
        complete: bool = False,
    ) -> dict[str, Any]:
        if (
            not isinstance(entries, list)
            or not 1 <= len(entries) <= 500
            or any(not isinstance(entry, dict) for entry in entries)
        ):
            raise ValueError("Capture requires between 1 and 500 intake-turn objects.")
        entries = _canonicalize_capture_entries(entries)
        if re.fullmatch(r"SYN-[A-Z0-9-]+", initiative_id) is None:
            raise ValueError("Transcript capture requires a synthetic initiative ID.")
        directory = self.root / initiative_id
        path = directory / "intake-transcript.json"
        if self.root.resolve() != self.root:
            raise ValueError("Transcript capture paths cannot be redirected.")
        if not directory.exists():
            candidate = _new_transcript(initiative_id)
            _merge_capture_batch(candidate, entries, gap=gap, complete=complete)
            validate_transcript(candidate, initiative_id)
        directory.mkdir(parents=True, exist_ok=True)
        # Non-strict Windows resolution can race another directory creator.
        if directory.resolve(strict=True) != directory:
            raise ValueError("Transcript capture paths cannot be redirected.")
        with _lock(directory / ".transcript.lock"):
            if path.resolve() != path:
                raise ValueError("Transcript capture paths cannot be redirected.")
            changed = not path.exists()
            transcript = _read_json(path) if not changed else _new_transcript(initiative_id)
            validate_transcript(transcript, initiative_id)
            changed = (
                _merge_capture_batch(
                    transcript,
                    entries,
                    gap=gap,
                    complete=complete,
                )
                or changed
            )
            validate_transcript(transcript, initiative_id)
            if changed:
                _retry_local_io(lambda: _write_json(path, transcript))
        return {
            "status": "recorded",
            "initiativeId": initiative_id,
            "captureStatus": transcript["captureStatus"],
            "entryCount": len(transcript["entries"]),
            "nextSequence": len(transcript["entries"]) + 1,
            "transcriptPath": path.as_uri(),
        }

    def _finish_processing(
        self, directory: Path, state: dict[str, Any], target: str, tracing: ProcessingRun
    ) -> None:
        tracing.finish(state, target)
        self._seal_processing(directory, state, tracing)
        state["processingStatus"] = "ready"

    def _seal_processing(
        self, directory: Path, state: dict[str, Any], tracing: ProcessingRun
    ) -> None:
        expected = "".join(
            json.dumps(event, ensure_ascii=True, sort_keys=True, separators=(",", ":")) + "\n"
            for event in tracing.events
        ).encode("utf-8")
        if (directory / "pipeline-trace.jsonl").read_bytes() != expected:
            raise ValueError("Processing trace changed during execution.")
        files = {}
        for name in OPERATOR_FILES:
            path = directory / name
            if path.resolve() != path:
                raise ValueError("Operator artifacts cannot contain redirected paths.")
            files[name] = hashlib.sha256(path.read_bytes()).hexdigest()
        revision = _digest(files)
        _write_json(
            directory / "processing-manifest.json",
            {"jobId": state["jobId"], "revision": revision, "files": files},
        )
        state["processingRevision"] = revision

    def _verify_processing(self, directory: Path, state: dict[str, Any]) -> None:
        manifest_path = directory / "processing-manifest.json"
        if manifest_path.resolve() != manifest_path:
            raise ValueError("Operator manifest cannot be redirected.")
        manifest = _read_json(manifest_path)
        files = {}
        for name in OPERATOR_FILES:
            path = directory / name
            if path.resolve() != path:
                raise ValueError("Operator artifacts cannot contain redirected paths.")
            files[name] = hashlib.sha256(path.read_bytes()).hexdigest()
        if (
            manifest.get("jobId") != state["jobId"]
            or manifest.get("files") != files
            or manifest.get("revision") != _digest(files)
            or state.get("processingRevision") != manifest["revision"]
        ):
            raise ValueError("Operator report or trace integrity failed.")

    def _transition(
        self,
        directory: Path,
        state: dict[str, Any],
        target: str,
        tracing: ProcessingRun | None = None,
    ) -> None:
        if tracing is not None and target in TERMINAL_STATES:
            try:
                self._finish_processing(directory, state, target, tracing)
            except (OSError, ValueError) as error:
                state["processingStatus"] = "failed"
                state["processingError"] = {
                    "type": type(error).__name__,
                    "message": (
                        "Operator records could not be finalized; "
                        "do not rely on incomplete metrics."
                    ),
                }
                if target == "completed":
                    raise
        state["state"] = target
        state["updatedAt"] = _now()
        state["history"].append({"state": target, "at": state["updatedAt"]})
        if target in TERMINAL_STATES:
            state["finishedAt"] = state["updatedAt"]
        _write_json(directory / "status.json", state)

    def submit(
        self,
        request_path: Path,
        catalog_path: Path,
        policy_path: Path,
        customer_path: Path,
        *,
        reference: bool = False,
        notify: bool = True,
        transcript_path: Path | None = None,
        copilot: CopilotLimits | None = None,
        copilot_executable: Path | None = None,
        tracing: ProcessingRun | None = None,
    ) -> dict[str, Any]:
        tracing = tracing or ProcessingRun()
        tracing.emit("submission.inputs", "started")
        if bool(copilot) != bool(copilot_executable) or copilot and reference:
            raise ValueError(
                "Model analysis requires explicit limits and a native CLI, not reference mode."
            )
        payloads = {
            "request.json": request_path.read_bytes(),
            "sources/catalog.json": catalog_path.read_bytes(),
            "policy.json": policy_path.read_bytes(),
            "customer.json": customer_path.read_bytes(),
        }
        request = json.loads(payloads["request.json"])
        if transcript_path is not None:
            if transcript_path.resolve() != transcript_path.absolute():
                raise ValueError("The captured transcript path cannot be redirected.")
            content = transcript_path.read_bytes()
            transcript = json.loads(content)
            validate_transcript(transcript, request["initiativeId"])
            if "intakeTranscript" in request and request["intakeTranscript"] != transcript:
                raise ValueError("The captured transcript conflicts with the supplied request.")
            request["intakeTranscript"] = transcript
            payloads["request.json"] = json.dumps(request, ensure_ascii=True).encode("utf-8")
            payloads["intake-transcript.json"] = content
        if "intakeTranscript" in request:
            if request.get("inputMode") != "conversation":
                raise ValueError("Transcript capture belongs only to a conversational input.")
            validate_transcript(request["intakeTranscript"], request["initiativeId"])
            payloads.setdefault(
                "intake-transcript.json",
                json.dumps(
                    request["intakeTranscript"],
                    ensure_ascii=True,
                ).encode("utf-8"),
            )
        catalog = json.loads(payloads["sources/catalog.json"])
        policy = json.loads(payloads["policy.json"])
        customer = json.loads(payloads["customer.json"])
        tracing.emit("submission.inputs", "completed")
        tracing.emit("submission.schema_and_policy", "started")
        if copilot:
            validate_brief(request)
        else:
            validate_instance(request, "intake-request.schema.json")
        validate_instance(customer, "customer-config.schema.json")
        if request.get("inputMode") != "conversation" and not reference:
            raise ValueError(
                "An authored conversational request is required; reference mode is explicit."
            )
        if customer["customerId"] != request["customerId"]:
            raise ValueError("Customer configuration does not match the request customerId.")
        if customer["sourcePolicyId"] != policy.get("policyId"):
            raise ValueError("Customer configuration does not reference the active source policy.")
        baseline = _read_json(DEFAULT_EXAMPLE / "source-policy.json")
        if (
            not set(policy.get("allowedSourceIds", [])).issubset(baseline["allowedSourceIds"])
            or not set(policy.get("allowedClassifications", [])).issubset(
                baseline["allowedClassifications"]
            )
            or policy.get("networkAccess") is not False
            or policy.get("realCustomerDataAllowed") is not False
            or policy.get("defaultConnectorAccess") != "read-only"
            or policy.get("mode") != "fail-closed"
        ):
            raise ValueError("Job source policy cannot weaken the synthetic baseline.")
        tracing.emit("submission.schema_and_policy", "completed")
        tracing.emit("submission.evidence_snapshot", "started")
        evidence = SyntheticSourceConnector(catalog, policy, catalog_path.parent).acquire()
        for source in evidence:
            content = (catalog_path.parent / source["sourcePath"]).read_bytes()
            if hashlib.sha256(content).hexdigest() != source["sha256"]:
                raise ValueError("Approved evidence changed during snapshot capture.")
            payloads[f"sources/{source['sourcePath']}"] = content
            tracing.emit(
                "submission.evidence_source",
                "completed",
                {"evidenceId": source["id"], "sha256": source["sha256"], "bytes": len(content)},
            )
        tracing.emit("submission.evidence_snapshot", "completed", {"sourceCount": len(evidence)})
        if copilot:
            tracing.emit("submission.model_preflight", "started")
            executable = copilot_executable.resolve()
            if not executable.is_file() or executable.suffix.lower() in {".cmd", ".bat", ".ps1"}:
                raise ValueError("Configure the native Copilot executable, not a shell wrapper.")
            validate_cli_home(self.root / ".copilot-cli")
            prompt = build_prompt(
                request,
                [
                    {
                        "id": source["id"],
                        "title": source["title"],
                        "content": payloads[f"sources/{source['sourcePath']}"].decode("utf-8"),
                    }
                    for source in evidence
                ],
            )
            restricted_command(executable, copilot, prompt, self.root)
            payloads["model-config.json"] = json.dumps(
                {
                    "limits": asdict(copilot),
                    "executable": str(executable),
                    "runtimeFiles": runtime_hashes(executable),
                },
                sort_keys=True,
            ).encode("utf-8")
            tracing.emit(
                "submission.model_preflight",
                "completed",
                {
                    "model": copilot.model,
                    "creditCap": copilot.max_ai_credits,
                    "deadlineSeconds": copilot.timeout_seconds,
                },
            )
        job_id = f"JOB-{request['initiativeId']}-{uuid4().hex}"
        directory = self.directory(job_id)
        self.root.mkdir(parents=True, exist_ok=True)
        with _lock(self.root / ".installation.lock"):
            installation_path = self.root / "installation.json"
            if installation_path.exists():
                if _read_json(installation_path)["customerId"] != request["customerId"]:
                    raise ValueError("A local job installation belongs to exactly one customer.")
            else:
                _write_json(installation_path, {"customerId": request["customerId"]})
        staging = directory.with_name(f".new-{job_id}")
        snapshot = staging / "snapshot"
        tracing.emit("submission.seal_snapshot", "started")
        try:
            snapshot.mkdir(parents=True)
            for name, content in payloads.items():
                destination = snapshot / name
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_bytes(content)
            hashes = _file_hashes(snapshot)
            created_at = _now()
            state = {
                "schemaVersion": "1.0.0",
                "jobId": job_id,
                "initiativeId": request["initiativeId"],
                "customerId": request["customerId"],
                "state": "queued",
                "createdAt": created_at,
                "updatedAt": created_at,
                "finishedAt": None,
                "inputDigest": _digest(hashes),
                "workerPid": None,
                "engineDigest": _engine_digest(),
                "analysis": {"provider": "copilot-cli", **asdict(copilot), "status": "queued"}
                if copilot
                else None,
                "statusPath": (directory / "status.html").as_uri(),
                "cancellationRequested": False,
                "reportPath": None,
                "reportRevision": None,
                "processingReportPath": (directory / "processing-report.html").as_uri(),
                "tracePath": (directory / "pipeline-trace.jsonl").as_uri(),
                "processingStatus": "recording",
                "processingRevision": None,
                "reviewState": None,
                "releaseAuthorized": False,
                "error": None,
                "notification": {
                    "requested": notify,
                    "status": "pending" if notify else "disabled",
                },
                "history": [{"state": "queued", "at": created_at}],
            }
            _write_json(staging / "input-manifest.json", {"files": hashes})
            tracing.emit("submission.seal_snapshot", "completed", {"fileCount": len(hashes)})
            tracing.emit("job.queued", "completed")
            tracing.bind(staging, state, request)
            self._seal_processing(staging, state, tracing)
            _write_json(staging / "status.json", state)
            _publish_directory(staging, directory)
            tracing.directory = directory
        finally:
            if staging.exists():
                shutil.rmtree(staging)
        return state

    def cancel(self, job_id: str) -> dict[str, Any]:
        directory = self.directory(job_id)
        with _lock(directory / "state.lock"):
            state = self.status(job_id)
            if state["state"] not in TERMINAL_STATES:
                state["cancellationRequested"] = True
                if state["state"] == "queued":
                    tracing = (
                        ProcessingRun.load(directory, state)
                        if state.get("processingReportPath")
                        else None
                    )
                    if tracing:
                        tracing.emit("job.cancellation_requested", "observed")
                    self._transition(directory, state, "canceled", tracing)
                else:
                    _write_json(directory / "status.json", state)
        return state

    def execute(
        self,
        job_id: str,
        *,
        on_progress: Callable[[str], None] | None = None,
    ) -> dict[str, Any]:
        progress = on_progress or (lambda message: None)
        directory = self.directory(job_id)
        with _lock(directory / "worker.lock", blocking=False):
            with _lock(directory / "state.lock"):
                state = self.status(job_id)
                if state["state"] in TERMINAL_STATES:
                    return state
                if state["state"] != "queued":
                    raise ValueError("Interrupted jobs cannot resume; submit a new job.")
                state["workerPid"] = os.getpid()
                self._transition(directory, state, "running")
            staging = directory / ".working"
            tracing = None
            try:
                if state.get("processingReportPath"):
                    self._verify_processing(directory, state)
                tracing = ProcessingRun.load(directory, state)
                tracing.meta["state"] = "running"
                tracing.emit("job.execution", "started")
                if state.get("recovery"):
                    tracing.emit("recovery.retained_input", "observed", recovery_metadata(state))
                snapshot = directory / "snapshot"
                with observed_step(tracing.emit, "integrity.sealed_inputs_and_engine"):
                    hashes = _file_hashes(snapshot)
                    if (
                        _digest(hashes) != state["inputDigest"]
                        or hashes != _read_json(directory / "input-manifest.json")["files"]
                        or _engine_digest() != state["engineDigest"]
                    ):
                        raise ValueError("Input or engine integrity changed; submit a new job.")
                request_path = snapshot / "request.json"
                if (snapshot / "model-config.json").exists():
                    model_config = _read_json(snapshot / "model-config.json")
                    executable = Path(model_config["executable"])
                    if runtime_hashes(executable) != model_config["runtimeFiles"]:
                        raise ValueError("Copilot executable changed; submit a new job.")
                    with observed_step(tracing.emit, "analysis.acquire_sealed_evidence"):
                        evidence = SyntheticSourceConnector(
                            _read_json(snapshot / "sources/catalog.json"),
                            _read_json(snapshot / "policy.json"),
                            snapshot / "sources",
                        ).acquire()
                    brief = _read_json(request_path)
                    with observed_step(tracing.emit, "analysis.build_prompt"):
                        prompt = build_prompt(
                            brief,
                            [
                                {
                                    "id": source["id"],
                                    "title": source["title"],
                                    "content": (
                                        snapshot / "sources" / source["sourcePath"]
                                    ).read_text(
                                        encoding="utf-8",
                                    ),
                                }
                                for source in evidence
                            ],
                        )
                    with _lock(directory / "state.lock"):
                        state = self.status(job_id)
                        state["analysis"]["status"] = "running"
                        _write_json(directory / "status.json", state)
                    progress("Analyzing the approved brief with the configured model...")
                    with observed_step(
                        tracing.emit, "analysis.invoke", model=model_config["limits"]["model"]
                    ):
                        response = run_copilot(
                            prompt,
                            CopilotLimits(**model_config["limits"]),
                            executable,
                            self.root / ".copilot-cli",
                            lambda: self.status(job_id)["cancellationRequested"],
                            on_usage=tracing.receive_usage,
                        )
                        with tracing.buffered():
                            _write_json(directory / "analysis-response.json", response)
                            response_digest = _digest(response)
                            with _lock(directory / "state.lock"):
                                state = self.status(job_id)
                                state["analysis"]["responseDigest"] = response_digest
                                _write_json(directory / "status.json", state)
                            with observed_step(tracing.emit, "analysis.validate_response"):
                                authored = prepare_request(
                                    brief,
                                    response,
                                    {source["id"] for source in evidence},
                                )
                            authored["analysisProvenance"] = {
                                "provider": "copilot-cli",
                                "model": model_config["limits"]["model"],
                                "inputDigest": state["inputDigest"],
                                "responseDigest": response_digest,
                                "promptDigest": hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
                            }
                            request_path = directory / "analysis-request.json"
                            _write_json(request_path, authored)
                            with _lock(directory / "state.lock"):
                                state = self.status(job_id)
                                state["analysis"]["status"] = "completed"
                                state["reportInputDigest"] = hashlib.sha256(
                                    request_path.read_bytes()
                                ).hexdigest()
                                _write_json(directory / "status.json", state)
                else:
                    tracing.emit("analysis.invoke", "skipped", {"reason": "prepared_input"})
                request_digest = (
                    state.get("reportInputDigest")
                    or hashlib.sha256(request_path.read_bytes()).hexdigest()
                )
                with _lock(directory / "state.lock"):
                    state = self.status(job_id)
                    state["reportInputDigest"] = request_digest
                    _write_json(directory / "status.json", state)
                tracing.emit(
                    "analysis.retain_report_input", "completed", {"sha256": request_digest}
                )
                tracing.flush_usage()

                def generate_report() -> dict[str, Any]:
                    if self.status(job_id)["cancellationRequested"]:
                        raise AnalysisCanceled()
                    if staging.exists():
                        shutil.rmtree(staging)
                    return run_demo(
                        request_path,
                        snapshot / "sources/catalog.json",
                        snapshot / "policy.json",
                        snapshot / "customer.json",
                        staging,
                        on_event=tracing.emit,
                    )

                def retry_report(attempt: int) -> None:
                    tracing.emit(
                        "report.retry",
                        "retry",
                        {"attempt": attempt, "modelCallRepeated": False},
                    )
                    progress(
                        f"Temporary local file error; retrying reports (attempt {attempt}/3). "
                        "No additional model call."
                    )

                progress("Generating and validating the report package...")
                with observed_step(tracing.emit, "report.generate_and_validate"):
                    summary = _retry_local_io(generate_report, retry_report)
                with observed_step(tracing.emit, "integrity.before_publication"):
                    artifacts = _file_hashes(staging)
                    if (
                        _engine_digest() != state["engineDigest"]
                        or _file_hashes(snapshot) != hashes
                        or hashlib.sha256(request_path.read_bytes()).hexdigest() != request_digest
                        or (snapshot / "model-config.json").exists()
                        and runtime_hashes(Path(model_config["executable"]))
                        != model_config["runtimeFiles"]
                    ):
                        raise ValueError(
                            "Input or engine changed during generation; submit a new job."
                        )
                revision = _digest(artifacts)
                with _lock(directory / "state.lock"):
                    state = self.status(job_id)
                    if state["cancellationRequested"]:
                        tracing.emit("job.cancellation_requested", "observed")
                        self._transition(directory, state, "canceled", tracing)
                    else:
                        report_directory = directory / f"report-{revision[:16]}"
                        progress("Publishing the validated report revision...")
                        with observed_step(tracing.emit, "report.publish"):
                            _publish_directory(staging, report_directory)
                            _write_json(
                                directory / "report-manifest.json",
                                {
                                    "revision": revision,
                                    "files": artifacts,
                                },
                            )
                        state.update(
                            {
                                "reportPath": (report_directory / "index.html").as_uri(),
                                "reportRevision": revision,
                                "runId": summary["runId"],
                                "artifactCount": summary["artifactCount"],
                                "reviewState": summary["state"],
                            }
                        )
                        self._transition(directory, state, "completed", tracing)
            except AnalysisCanceled:
                with _lock(directory / "state.lock"):
                    state = self.status(job_id)
                    if state.get("analysis") and state["analysis"]["status"] != "completed":
                        state["analysis"]["status"] = "canceled"
                    self._transition(directory, state, "canceled", tracing)
            except Exception as error:
                _write_json(
                    directory / "failure.json",
                    {
                        "type": type(error).__name__,
                        "detail": str(error),
                        "at": _now(),
                        "localDiagnostic": getattr(error, "diagnostic", None),
                    },
                )
                with _lock(directory / "state.lock"):
                    state = self.status(job_id)
                    if state.get("analysis") and state["analysis"]["status"] != "completed":
                        state["analysis"]["status"] = "failed"
                    retained_input = bool(state.get("reportInputDigest"))
                    analysis_state = state.get("analysis") or {}
                    retained_response = bool(
                        analysis_state.get("responseDigest")
                        and (directory / "analysis-response.json").is_file()
                    )
                    retained = retained_input or retained_response
                    if retained_response and not retained_input:
                        message = (
                            "Model analysis was retained and integrity-bound before validation. "
                            "Review or correct the local contract, then rebuild without another "
                            "model call."
                        )
                    elif not retained:
                        message = (
                            "Generation failed before report input was retained. Review "
                            "the failure; a new model call requires fresh approval."
                        )
                    elif isinstance(error, ValueError):
                        message = (
                            "A validation or integrity check blocked generation. Saved input is "
                            "preserved; review the cause before choosing recovery."
                        )
                    else:
                        message = (
                            "Report assembly failed. Saved input is preserved; correct the "
                            "local cause, then rebuild without repeating analysis."
                        )
                    state["error"] = {
                        "type": type(error).__name__,
                        "message": message,
                        "localRebuildAvailable": retained,
                        "nextAction": (
                            "repair_then_rebuild"
                            if retained and not isinstance(error, ValueError)
                            else "review_failure"
                        ),
                    }
                    if tracing is None and state.get("processingReportPath"):
                        state["processingStatus"] = "failed"
                        state["processingError"] = {
                            "type": type(error).__name__,
                            "message": "Operator records could not be read or verified.",
                        }
                    self._transition(directory, state, "failed", tracing)
            finally:
                if staging.exists():
                    shutil.rmtree(staging)
            return self.status(job_id)

    def rebuild(
        self,
        job_id: str,
        *,
        expected_response_digest: str | None = None,
    ) -> dict[str, Any]:
        directory = self.directory(job_id)
        with _lock(directory / "worker.lock", blocking=False):
            state = self.status(job_id)
            if state["state"] != "failed":
                raise ValueError("Only a failed report job can be rebuilt.")
            snapshot = directory / "snapshot"
            hashes = _file_hashes(snapshot)
            if (
                _digest(hashes) != state["inputDigest"]
                or hashes != _read_json(directory / "input-manifest.json")["files"]
            ):
                raise ValueError("Retained input integrity failed; rebuilding is blocked.")
            recovery_mode = "retained-input"
            analysis = state.get("analysis")
            if analysis and analysis["status"] != "completed":
                response_path = directory / "analysis-response.json"
                if (
                    response_path.is_symlink()
                    or not response_path.is_file()
                    or not response_path.resolve().is_relative_to(directory)
                ):
                    raise ValueError(
                        "No validated or integrity-bound analysis is retained. "
                        "A new model call requires approval."
                    )
                response = _read_json(response_path)
                actual_response_digest = _digest(response)
                trusted_response_digest = analysis.get("responseDigest")
                if trusted_response_digest is None:
                    trusted_response_digest = expected_response_digest
                if (
                    not isinstance(trusted_response_digest, str)
                    or re.fullmatch(r"[a-f0-9]{64}", trusted_response_digest) is None
                    or actual_response_digest != trusted_response_digest
                ):
                    raise ValueError(
                        "Retained model response integrity is unverified; provide its exact "
                        "expected digest or obtain approval for a new model call."
                    )
                brief = _read_json(snapshot / "request.json")
                evidence = SyntheticSourceConnector(
                    _read_json(snapshot / "sources/catalog.json"),
                    _read_json(snapshot / "policy.json"),
                    snapshot / "sources",
                ).acquire()
                prompt = build_prompt(
                    brief,
                    [
                        {
                            "id": source["id"],
                            "title": source["title"],
                            "content": (snapshot / "sources" / source["sourcePath"]).read_text(
                                encoding="utf-8"
                            ),
                        }
                        for source in evidence
                    ],
                )
                authored = prepare_request(
                    brief,
                    response,
                    {source["id"] for source in evidence},
                )
                authored["analysisProvenance"] = {
                    "provider": "copilot-cli",
                    "model": analysis["model"],
                    "inputDigest": state["inputDigest"],
                    "responseDigest": actual_response_digest,
                    "promptDigest": hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
                }
                request_path = directory / "analysis-request.json"
                _write_json(request_path, authored)
                recovery_mode = "retained-response"
            else:
                request_path = (
                    directory / "analysis-request.json" if analysis else snapshot / "request.json"
                )
            if (
                request_path.is_symlink()
                or not request_path.resolve().is_relative_to(directory)
                or (
                    recovery_mode == "retained-input"
                    and hashlib.sha256(request_path.read_bytes()).hexdigest()
                    != state.get("reportInputDigest")
                )
            ):
                raise ValueError("Retained report input integrity failed; rebuilding is blocked.")
            queued = self.submit(
                request_path,
                snapshot / "sources/catalog.json",
                snapshot / "policy.json",
                snapshot / "customer.json",
                notify=False,
                reference=_read_json(request_path).get("inputMode") != "conversation",
            )
            queued["recovery"] = {
                "mode": recovery_mode,
                "sourceJobId": job_id,
                "modelCallRepeated": False,
            }
            _write_json(self.directory(queued["jobId"]) / "status.json", queued)
            return queued

    def verified_report_uri(self, job_id: str) -> str:
        directory = self.directory(job_id)
        state = self.status(job_id)
        revision = state.get("reportRevision")
        if (
            state["state"] != "completed"
            or not isinstance(revision, str)
            or re.fullmatch(r"[a-f0-9]{64}", revision) is None
        ):
            raise ValueError("No completed report is available to open.")
        report_directory = directory / f"report-{revision[:16]}"
        manifest_path = directory / "report-manifest.json"
        if (
            report_directory.resolve() != report_directory
            or manifest_path.resolve() != manifest_path
        ):
            raise ValueError("Completed report paths cannot be redirected.")
        manifest = _read_json(manifest_path)
        hashes = _file_hashes(report_directory)
        uri = (report_directory / "index.html").as_uri()
        if (
            "index.html" not in hashes
            or _digest(hashes) != revision
            or manifest.get("files") != hashes
            or manifest.get("revision") != revision
            or state.get("reportPath") != uri
        ):
            raise ValueError("Completed report integrity failed; opening is blocked.")
        return uri

    def processing_report_uri(self, job_id: str) -> str:
        directory = self.directory(job_id)
        state = self.status(job_id)
        path = directory / "processing-report.html"
        if not state.get("processingReportPath") or not path.is_file():
            raise ValueError(
                "No operator report was recorded for this job; history is not reconstructed."
            )
        if path.resolve() != path or state["processingReportPath"] != path.as_uri():
            raise ValueError("Operator report path integrity failed.")
        if state["state"] in TERMINAL_STATES:
            if state.get("processingStatus") != "ready":
                raise ValueError(
                    "Operator records are incomplete; inspect the reported processing error."
                )
            self._verify_processing(directory, state)
        return path.as_uri()

    def open_report(self, job_id: str, *, processing: bool = False) -> dict[str, Any]:
        uri = self.processing_report_uri(job_id) if processing else self.verified_report_uri(job_id)
        state = self.status(job_id)
        try:
            open_default_browser(uri)
            state["browser"] = {"status": "requested", "reportPath": uri}
        except (OSError, webbrowser.Error) as error:
            state["browser"] = {
                "status": "failed",
                "errorType": type(error).__name__,
                "reportPath": uri,
                "message": (
                    "Documents are ready, but the browser could not be opened. "
                    "Retry opening this report; do not regenerate it."
                ),
            }
        return state

    def notify(self, job_id: str, *, retry: bool = False) -> dict[str, Any]:
        directory = self.directory(job_id)
        with _lock(directory / "notification.lock"):
            state = self.status(job_id)
            delivery = state["notification"]["status"]
            retryable = {"failed", "blocked_by_settings", "unsupported_platform"}
            if state["state"] not in TERMINAL_STATES or not (
                delivery == "pending" or retry and delivery in retryable
            ):
                return state
            result = {"requested": True, "status": "sending", "attemptedAt": _now()}
            with _lock(directory / "state.lock"):
                state["notification"] = result
                _write_json(directory / "status.json", state)
            try:
                if state["state"] == "completed":
                    launch_uri = self.verified_report_uri(job_id)
                    title = "MOSAIC reports ready"
                    message = (
                        "Discussion draft ready for human review. "
                        "No approval or release authorized."
                    )
                else:
                    launch_uri = (directory / "status.html").as_uri()
                    title = f"MOSAIC report job {state['state']}"
                    message = "No completed report is available. Job details remain local."
                result["status"] = send_windows_notification(title, message, launch_uri)
            except Exception as error:
                result["status"] = "failed"
                result["errorType"] = type(error).__name__
                _write_json(
                    directory / "notification-error.json",
                    {
                        "type": type(error).__name__,
                        "detail": str(error),
                        "traceback": traceback.format_exc(),
                        "at": _now(),
                    },
                )
            with _lock(directory / "state.lock"):
                state = self.status(job_id)
                state["notification"] = result
                _write_json(directory / "status.json", state)
        return state

    def start(self, job_id: str) -> subprocess.Popen:
        directory = self.directory(job_id)
        with _lock(directory / "launch.lock"), _lock(directory / "state.lock"):
            state = self.status(job_id)
            if state["state"] != "queued" or state.get("launchPid"):
                raise ValueError("This job has already started or finished.")
            bootstrap = (
                f"import sys; sys.path.insert(0, {str(PROJECT_ROOT / 'src')!r}); "
                "from mosaic.jobs import main; raise SystemExit(main())"
            )
            command = [
                sys.executable,
                "-E",
                "-s",
                "-B",
                "-c",
                bootstrap,
                "--root",
                str(self.root),
                "_worker",
                job_id,
            ]
            environment = {
                **os.environ,
                "PYTHONPATH": str(PROJECT_ROOT / "src"),
                "PYTHONNOUSERSITE": "1",
            }
            try:
                with (directory / "worker.log").open("ab") as log:
                    process = subprocess.Popen(
                        command,
                        cwd=PROJECT_ROOT,
                        env=environment,
                        stdin=subprocess.DEVNULL,
                        stdout=log,
                        stderr=log,
                        creationflags=(
                            subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP
                        )
                        if os.name == "nt"
                        else 0,
                        start_new_session=os.name != "nt",
                    )
                state["launchPid"] = process.pid
                _write_json(directory / "status.json", state)
            except OSError as error:
                state["error"] = {
                    "type": type(error).__name__,
                    "message": "Worker could not start.",
                }
                tracing = None
                if state.get("processingReportPath"):
                    try:
                        tracing = ProcessingRun.load(directory, state)
                        tracing.emit("job.launch_failed", "failed")
                    except (OSError, ValueError) as error:
                        state["processingStatus"] = "failed"
                        state["processingError"] = {
                            "type": type(error).__name__,
                            "message": "Operator records for the failed launch are incomplete.",
                        }
                self._transition(directory, state, "failed", tracing)
                raise
        return process

    def inspect(self, job_id: str) -> dict[str, Any]:
        directory = self.directory(job_id)
        state = self.status(job_id)
        if state["state"] == "running":
            try:
                with (
                    _lock(directory / "worker.lock", blocking=False),
                    _lock(directory / "state.lock"),
                ):
                    state = self.status(job_id)
                    if state["state"] == "running":
                        state["error"] = {
                            "type": "InterruptedWorker",
                            "message": (
                                "Worker exited before publication. "
                                "Submit a new job; no automatic resume."
                            ),
                        }
                        tracing = None
                        if state.get("processingReportPath"):
                            try:
                                tracing = ProcessingRun.load(directory, state)
                                tracing.emit("job.interruption_detected", "failed")
                            except (OSError, ValueError) as error:
                                state["processingStatus"] = "failed"
                                state["processingError"] = {
                                    "type": type(error).__name__,
                                    "message": "Interrupted operator records are incomplete.",
                                }
                        self._transition(directory, state, "failed", tracing)
            except OSError:
                return state
        return state


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Local MOSAIC analysis and report jobs.")
    parser.add_argument("--root", type=Path, default=DEFAULT_JOB_ROOT)
    commands = parser.add_subparsers(dest="command", required=True)
    submit = commands.add_parser(
        "generate",
        aliases=["submit"],
        help="Generate reports in the foreground; submit uses a background worker instead.",
    )
    submit.add_argument("--request", type=Path, required=True)
    submit.add_argument("--transcript", type=Path)
    submit.add_argument("--catalog", type=Path, default=DEFAULT_EXAMPLE / "sources/catalog.json")
    submit.add_argument("--policy", type=Path, default=DEFAULT_EXAMPLE / "source-policy.json")
    submit.add_argument("--customer", type=Path, default=DEFAULT_CUSTOMER)
    submit.add_argument("--reference", action="store_true")
    submit.add_argument("--no-notify", action="store_true")
    submit.add_argument("--analyze-with-copilot", action="store_true")
    submit.add_argument("--copilot-executable", type=Path)
    submit.add_argument("--model")
    submit.add_argument("--max-ai-credits", type=int)
    submit.add_argument("--model-timeout", type=int)
    configure = commands.add_parser("configure-copilot", help="Save explicit local worker limits.")
    configure.add_argument("--copilot-executable", type=Path, required=True)
    configure.add_argument("--model", required=True)
    configure.add_argument("--max-ai-credits", type=int, default=30)
    configure.add_argument("--model-timeout", type=int, default=600)
    commands.add_parser("copilot-settings", help="Show non-secret local worker settings.")
    capture = commands.add_parser("capture", help="Atomically append exact local intake turns.")
    capture.add_argument("--initiative", required=True)
    capture_input = capture.add_mutually_exclusive_group(required=True)
    capture_input.add_argument("--entry", type=Path, help="One intake-turn JSON object.")
    capture_input.add_argument("--batch", type=Path, help="JSON object with an entries array.")
    capture.add_argument("--gap")
    capture.add_argument("--complete", action="store_true")
    capture.add_argument("--quiet", action="store_true", help="Suppress successful capture output.")
    for name in ("status", "cancel", "rebuild", "open", "_worker"):
        command = commands.add_parser(name)
        command.add_argument("job_id")
        if name == "rebuild":
            command.add_argument(
                "--expected-response-digest",
                help=(
                    "Exact SHA-256 digest required only for a legacy retained response that "
                    "predates automatic integrity binding."
                ),
            )
        if name == "open":
            command.add_argument(
                "--processing",
                action="store_true",
                help="Open the separate operator cost/performance report and pipeline trace.",
            )
    notification = commands.add_parser("notify", help="Retry an unsuccessful desktop notification.")
    notification.add_argument("job_id")
    notification.add_argument("--retry", action="store_true")
    args = parser.parse_args(argv)

    def progress(message: str) -> None:
        print(message, file=sys.stderr, flush=True)

    tracing = None
    try:
        store = JobStore(args.root)
        if args.command == "capture":
            payload = _read_json(args.batch or args.entry)
            if args.batch and set(payload) != {"entries"}:
                raise ValueError("A capture batch must contain only an entries array.")
            result = store.capture_batch(
                args.initiative,
                payload["entries"] if args.batch else [payload],
                gap=args.gap,
                complete=args.complete,
            )
            if not args.quiet:
                print(json.dumps(result, indent=2))
            return 0
        if args.command in {"configure-copilot", "copilot-settings"}:
            configuration = (
                store.configure_copilot(
                    args.copilot_executable,
                    CopilotLimits(args.model, args.max_ai_credits, args.model_timeout),
                )
                if args.command == "configure-copilot"
                else store.copilot_configuration()
            )
            print(json.dumps(configuration, indent=2))
            return 0
        if args.command in {"generate", "submit"}:
            tracing = ProcessingRun()
            tracing.emit("invocation.settings", "started")
            limits = None
            executable = None
            if not args.analyze_with_copilot and any(
                value is not None
                for value in (
                    args.model,
                    args.copilot_executable,
                    args.max_ai_credits,
                    args.model_timeout,
                )
            ):
                raise ValueError(
                    "Model settings require explicit --analyze-with-copilot authorization."
                )
            if args.analyze_with_copilot:
                if args.model is not None or args.copilot_executable is not None:
                    if not args.model or not args.copilot_executable:
                        raise ValueError("Provide both --model and --copilot-executable.")
                    values = asdict(CopilotLimits(args.model))
                    executable = args.copilot_executable
                else:
                    configuration = store.copilot_configuration()
                    values = configuration["limits"]
                    executable = Path(configuration["executable"])
                if args.max_ai_credits is not None:
                    values["max_ai_credits"] = args.max_ai_credits
                if args.model_timeout is not None:
                    values["timeout_seconds"] = args.model_timeout
                limits = CopilotLimits(**values)
            tracing.emit("invocation.settings", "completed")
            result = store.submit(
                args.request,
                args.catalog,
                args.policy,
                args.customer,
                reference=args.reference,
                notify=args.command == "submit" and not args.no_notify,
                transcript_path=args.transcript,
                copilot=limits,
                copilot_executable=executable,
                tracing=tracing,
            )
            if args.command == "generate":
                result = store.execute(result["jobId"], on_progress=progress)
            else:
                store.start(result["jobId"])
                result = store.status(result["jobId"])
        elif args.command == "status":
            result = store.inspect(args.job_id)
        elif args.command == "open":
            result = store.open_report(args.job_id, processing=args.processing)
        elif args.command == "rebuild":
            result = store.rebuild(
                args.job_id,
                expected_response_digest=args.expected_response_digest,
            )
            progress("Rebuilding reports from retained analysis; no additional model call.")
            result = store.execute(result["jobId"], on_progress=progress)
        elif args.command == "cancel":
            result = store.cancel(args.job_id)
            if result["state"] == "canceled":
                result = store.notify(args.job_id)
        elif args.command == "notify":
            result = store.notify(args.job_id, retry=args.retry)
        else:
            store.execute(args.job_id)
            result = store.notify(args.job_id)
    except (OSError, ValueError) as error:
        failure = {"status": "fail", "error": str(error)}
        if tracing is not None and tracing.directory is None:
            tracing.emit("submission.rejected", "failed", {"errorType": type(error).__name__})
            failure["trace"] = tracing.events
        print(json.dumps(failure, indent=2))
        return 1
    print(json.dumps(result, indent=2))
    if args.command == "open":
        return int(result["browser"]["status"] == "failed")
    return int(
        result["state"] == "failed"
        or args.command in {"generate", "rebuild"}
        and result["state"] == "canceled"
        or args.command == "open"
        and result["browser"]["status"] == "failed"
    )


if __name__ == "__main__":
    raise SystemExit(main())
