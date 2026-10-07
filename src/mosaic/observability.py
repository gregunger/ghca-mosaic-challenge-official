# SPDX-License-Identifier: LicenseRef-MOSAIC-Evaluation
"""Local operator metrics and observable pipeline events, never model-authored billing."""

from __future__ import annotations

import hashlib
import json
import math
import os
import re
import time
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from copy import deepcopy
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, StrictUndefined, select_autoescape

from mosaic.storage import atomic_write_text

Observer = Callable[[str, str, dict[str, Any]], None]
TOKEN_FIELDS = (
    "inputTokens",
    "outputTokens",
    "cacheReadTokens",
    "cacheWriteTokens",
    "reasoningTokens",
)
OPERATOR_FILES = ("processing-report.json", "processing-report.html", "pipeline-trace.jsonl")
USAGE_SOURCE = "https://github.com/github/copilot-sdk/blob/main/docs/features/usage-and-billing.md"
PRICING_SOURCE = "https://docs.github.com/en/copilot/reference/copilot-billing/models-and-pricing"
_TEMPLATES = Environment(
    loader=FileSystemLoader(Path(__file__).resolve().parents[2] / "templates"),
    undefined=StrictUndefined,
    autoescape=select_autoescape(default=True),
)


def _now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _encoded(value: Any) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"))


def _hash(value: Any) -> str:
    return hashlib.sha256(_encoded(value).encode("utf-8")).hexdigest()


@contextmanager
def observed_step(observer: Observer | None, step: str, **details: Any) -> Iterator[None]:
    if observer is None:
        yield
        return
    observer(step, "started", details)
    started = time.perf_counter()
    try:
        yield
    except BaseException as error:
        observer(
            step,
            "canceled" if type(error).__name__ == "AnalysisCanceled" else "failed",
            {"durationSeconds": time.perf_counter() - started, "errorType": type(error).__name__},
        )
        raise
    else:
        observer(step, "completed", {"durationSeconds": time.perf_counter() - started})


def _number(
    value: Any, field: str, issues: list[str], *, integer: bool = False
) -> int | float | None:
    if value is None:
        return None
    if (
        type(value) not in (int, float)
        or value > 2**53 - 1
        or not math.isfinite(value)
        or value < 0
        or integer
        and int(value) != value
    ):
        issues.append(f"Invalid non-negative numeric field: {field}.")
        return None
    return int(value) if integer else value


def _sum_known(values: list[int | float | None]) -> int | float | None:
    return (
        sum(value for value in values if value is not None)
        if values and all(value is not None for value in values)
        else None
    )


def _model(value: Any, issues: list[str]) -> str | None:
    if value is None:
        return None
    if (
        not isinstance(value, str)
        or re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,99}", value) is None
    ):
        issues.append("An invalid reported model identifier was omitted.")
        return None
    return value


def recovery_metadata(state: dict[str, Any]) -> dict[str, Any] | None:
    recovery = state.get("recovery")
    if not isinstance(recovery, dict):
        return None
    return {
        name: deepcopy(recovery.get(name)) for name in ("mode", "sourceJobId", "modelCallRepeated")
    }


def provider_observations(
    events: list[dict[str, Any]], *, complete: bool, malformed: bool = False
) -> dict[str, Any]:
    """Whitelist CLI/SDK counters; ignore prompt, reasoning, account and diagnostic payloads."""
    issues = ["Some CLI event data was incomplete or invalid."] if malformed else []
    calls: dict[str, dict[str, Any]] = {}
    summaries = []
    timeline = []
    seen: dict[str, str] = {}
    for event in events:
        kind = event.get("type")
        data = event.get("data")
        if not isinstance(data, dict):
            data = {}
        identifier = event.get("id")
        if isinstance(identifier, str):
            digest = _hash(event)
            if identifier in seen:
                if seen[identifier] != digest:
                    issues.append("Conflicting duplicate CLI event identifiers.")
                continue
            seen[identifier] = digest
        if kind in {"model.call_start", "assistant.turn_start", "assistant.turn_end"}:
            moment = event.get("timestamp")
            try:
                valid_time = (
                    isinstance(moment, str)
                    and len(moment) < 40
                    and moment.endswith("Z")
                    and datetime.fromisoformat(moment).tzinfo is not None
                )
            except ValueError:
                valid_time = False
            timeline.append(
                {
                    "step": f"provider.{kind}",
                    "reportedAt": moment if valid_time else None,
                    "model": _model(data.get("model"), issues),
                }
            )
        if isinstance(kind, str) and kind.startswith("tool."):
            timeline.append({"step": "provider.unexpected_tool_activity"})
        if kind == "assistant.usage":
            call_id = data.get("apiCallId", identifier)
            if not isinstance(call_id, str) or not call_id:
                issues.append("Unidentified per-call usage was not included in totals.")
                continue
            usage = {
                name: _number(data.get(name), name, issues, integer=True) for name in TOKEN_FIELDS
            }
            credits = data.get("copilotUsage")
            usage.update(
                {
                    "model": _model(data.get("model"), issues),
                    "totalNanoAiu": _number(
                        credits.get("totalNanoAiu") if isinstance(credits, dict) else None,
                        "copilotUsage.totalNanoAiu",
                        issues,
                    ),
                    "legacyPremiumRequests": _number(data.get("cost"), "cost", issues),
                }
            )
            key = hashlib.sha256(call_id.encode("utf-8")).hexdigest()
            if key in calls and calls[key] != usage:
                issues.append("Conflicting usage for one provider call; totals are incomplete.")
                complete = False
            calls[key] = usage
        if kind == "result" and isinstance(event.get("usage"), dict):
            summaries.append(event["usage"])
        elif kind == "session.shutdown":
            summaries.append(data)
    summary = summaries[-1] if summaries else {}
    if len(summaries) > 1 and any(value != summary for value in summaries):
        issues.append("Multiple terminal usage summaries were reported; the last was retained.")
    models = []
    raw_models = summary.get("modelMetrics")
    if raw_models is not None and not isinstance(raw_models, dict):
        issues.append("Invalid terminal per-model usage.")
    if isinstance(raw_models, dict):
        for name, metric in raw_models.items():
            if not isinstance(metric, dict) or not isinstance(metric.get("usage"), dict):
                issues.append("Incomplete terminal per-model usage.")
                continue
            models.append(
                {
                    "model": _model(name, issues),
                    **{
                        field: _number(metric["usage"].get(field), field, issues, integer=True)
                        for field in TOKEN_FIELDS
                    },
                    "totalNanoAiu": _number(metric.get("totalNanoAiu"), "totalNanoAiu", issues),
                    "requestCount": _number(
                        metric.get("requests", {}).get("count")
                        if isinstance(metric.get("requests"), dict)
                        else None,
                        "requests.count",
                        issues,
                        integer=True,
                    ),
                    "legacyPremiumRequests": _number(
                        metric.get("requests", {}).get("cost")
                        if isinstance(metric.get("requests"), dict)
                        else None,
                        "requests.cost",
                        issues,
                    ),
                }
            )
    selected = models or list(calls.values())
    tokens = {name: _sum_known([item[name] for item in selected]) for name in TOKEN_FIELDS}
    nano = _number(summary.get("totalNanoAiu"), "totalNanoAiu", issues)
    if nano is None:
        nano = _sum_known([item["totalNanoAiu"] for item in selected])
    legacy = _number(
        summary.get("premiumRequests", summary.get("totalPremiumRequestCost")),
        "legacyPremiumRequests",
        issues,
    )
    if legacy is None:
        legacy = _sum_known([item["legacyPremiumRequests"] for item in selected])
    credits = float(Decimal(str(nano)) / Decimal(1_000_000_000)) if nano is not None else None
    reported = any(value is not None for value in (*tokens.values(), credits, legacy))
    api_duration = _number(summary.get("totalApiDurationMs"), "totalApiDurationMs", issues)
    provider_calls = _sum_known([item["requestCount"] for item in models])
    if provider_calls is None and calls:
        provider_calls = len(calls)
    return {
        "status": "reported"
        if reported
        and complete
        and not issues
        and tokens["inputTokens"] is not None
        and tokens["outputTokens"] is not None
        and credits is not None
        else "partial"
        if reported
        else "not_reported",
        "completeOutput": complete,
        "source": "copilot-cli-jsonl",
        "models": selected,
        "tokens": tokens,
        "inputPlusOutputTokens": _sum_known([tokens["inputTokens"], tokens["outputTokens"]]),
        "reportedAICredits": credits,
        "creditValueUsd": float(Decimal(str(credits)) / 100) if credits is not None else None,
        "actualBilledUsd": None,
        "legacyPremiumRequests": legacy,
        "reportedProviderCalls": provider_calls,
        "observedModelCallStarts": sum(
            item["step"] == "provider.model.call_start" for item in timeline
        ),
        "providerApiDurationMs": api_duration,
        "issues": issues,
        "timeline": timeline,
    }


class ProcessingRun:
    """One writer's local trace and separate operator report, outside customer artifacts."""

    def __init__(self) -> None:
        self.directory: Path | None = None
        self.events: list[dict[str, Any]] = []
        self.meta: dict[str, Any] = {
            "startedAt": _now(),
            "jobId": None,
            "state": "preflight",
            "model": None,
            "creditCap": None,
            "timeoutSeconds": None,
            "approvalAt": None,
            "recovery": None,
        }
        self.usage: dict[str, Any] | None = None
        self._flushed_usage = False
        self._step_starts: dict[str, float] = {}
        self._template = _TEMPLATES.get_template("processing.html.j2")

    @classmethod
    def load(cls, directory: Path, state: dict[str, Any]) -> ProcessingRun:
        run = cls()
        if not state.get("processingReportPath"):
            run.meta["legacyTraceGap"] = "Earlier steps were not instrumented for this job."
        else:
            for name in OPERATOR_FILES:
                path = directory / name
                if path.resolve() != path:
                    raise ValueError("Operator artifacts cannot contain redirected paths.")
            document = json.loads((directory / "processing-report.json").read_bytes())
            run.meta = document["metadata"]
            if run.meta["jobId"] != state["jobId"]:
                raise ValueError("Operator record belongs to a different job.")
            run.events = [
                json.loads(line)
                for line in (directory / "pipeline-trace.jsonl")
                .read_text(encoding="utf-8")
                .splitlines()
            ]
            previous = None
            for sequence, event in enumerate(run.events, 1):
                values = {key: value for key, value in event.items() if key != "hash"}
                if (
                    event.get("sequence") != sequence
                    or event.get("previousHash") != previous
                    or event.get("hash") != _hash(values)
                ):
                    raise ValueError("Processing trace integrity failed.")
                previous = event["hash"]
            checkpoint = document["traceHead"]
            valid_checkpoint = checkpoint is None or any(
                event["hash"] == checkpoint for event in run.events
            )
            if not valid_checkpoint or (state["state"] != "running" and checkpoint != previous):
                raise ValueError("Processing report and trace revisions differ.")
            run.usage = (
                document["workerUsage"]
                if document["workerUsage"]["status"] not in {"not_reported", "not_invoked"}
                else None
            )
        run.directory = directory
        run.meta.update(
            jobId=state["jobId"],
            state=state["state"],
            createdAt=state["createdAt"],
            recovery=recovery_metadata(state),
        )
        if state.get("recovery") or not state.get("analysis"):
            run.meta["approvalAt"] = None
        return run

    def bind(self, directory: Path, state: dict[str, Any], request: dict[str, Any]) -> None:
        self.directory = directory
        self.meta.update(
            jobId=state["jobId"],
            state=state["state"],
            createdAt=state["createdAt"],
            model=(state.get("analysis") or {}).get("model"),
            creditCap=(state.get("analysis") or {}).get("max_ai_credits"),
            timeoutSeconds=(state.get("analysis") or {}).get("timeout_seconds"),
            reusedPreparedAnalysis=bool(request.get("analysisProvenance")),
        )
        approvals = [
            entry.get("timestamp")
            for entry in request.get("intakeTranscript", {}).get("entries", [])
            if entry.get("kind") == "generation_approval"
        ]
        self.meta["originalIntakeApprovalAt"] = approvals[-1] if approvals else None
        self.meta["approvalAt"] = (
            self.meta["originalIntakeApprovalAt"] if state.get("analysis") else None
        )
        atomic_write_text(
            directory / "pipeline-trace.jsonl",
            "".join(_encoded(event) + "\n" for event in self.events),
        )
        self.persist()

    def emit(self, step: str, status: str, details: dict[str, Any] | None = None) -> None:
        details = deepcopy(details or {})
        if status == "started":
            self._step_starts[step] = time.perf_counter()
        elif step in self._step_starts and status in {"completed", "failed", "canceled"}:
            details.setdefault("durationSeconds", time.perf_counter() - self._step_starts.pop(step))
        event = {
            "sequence": len(self.events) + 1,
            "at": _now(),
            "step": step,
            "status": status,
            "details": details,
            "previousHash": self.events[-1]["hash"] if self.events else None,
        }
        event["hash"] = _hash(event)
        if self.directory is not None:
            path = self.directory / "pipeline-trace.jsonl"
            if path.resolve() != path:
                raise ValueError("Processing trace path cannot be redirected.")
            with path.open("a", encoding="utf-8", newline="\n") as stream:
                stream.write(_encoded(event) + "\n")
                stream.flush()
                os.fsync(stream.fileno())
        self.events.append(event)
        if self.directory is not None and (
            status in {"started", "failed", "canceled", "retry"} or step == "job.finished"
        ):
            self.persist()

    @contextmanager
    def buffered(self) -> Iterator[None]:
        """Retain completed analysis before diagnostic I/O can fail."""
        directory, start = self.directory, len(self.events)
        self.directory = None
        try:
            yield
        finally:
            self.directory = directory
            if directory is not None:
                path = directory / "pipeline-trace.jsonl"
                if path.resolve() != path:
                    raise ValueError("Processing trace path cannot be redirected.")
                with path.open("a", encoding="utf-8", newline="\n") as stream:
                    for event in self.events[start:]:
                        stream.write(_encoded(event) + "\n")
                    stream.flush()
                    os.fsync(stream.fileno())
                self.persist()

    def receive_usage(self, usage: dict[str, Any]) -> None:
        self.usage = usage

    def flush_usage(self) -> None:
        if self.usage is None or self._flushed_usage:
            return
        self._flushed_usage = True
        for event in self.usage["timeline"]:
            self.emit(
                event["step"],
                "observed",
                {key: value for key, value in event.items() if key != "step"},
            )
        self.emit(
            "analysis.usage",
            self.usage["status"],
            {"source": self.usage["source"], "issues": self.usage["issues"]},
        )

    def finish(self, state: dict[str, Any], outcome: str) -> None:
        self.flush_usage()
        self.meta.update(
            state=outcome,
            finishedAt=_now(),
            errorType=(state.get("error") or {}).get("type"),
            recovery=recovery_metadata(state),
        )
        self.emit("job.finished", outcome, {"releaseAuthorized": False})

    def snapshot(self) -> dict[str, Any]:
        timing_issues: list[str] = []

        def elapsed(start: str | None, end: str | None) -> float | None:
            if not start or not end:
                return None
            try:
                seconds = (
                    datetime.fromisoformat(end) - datetime.fromisoformat(start)
                ).total_seconds()
            except (TypeError, ValueError):
                timing_issues.append("An interval has invalid or incompatible timestamps.")
                return None
            if seconds < 0:
                timing_issues.append("An interval ends before it starts; no duration was inferred.")
                return None
            return round(seconds, 6)

        started = next(
            (event["at"] for event in self.events if event["step"] == "job.execution"), None
        )
        attempts = sum(
            event["step"] == "analysis.invoke" and event["status"] == "started"
            for event in self.events
        )
        worker = deepcopy(self.usage)
        if worker is None:
            worker = provider_observations([], complete=False)
            if self.meta["state"] in {"completed", "canceled", "failed"} and not attempts:
                worker.update(
                    status="not_invoked",
                    source="engine_no_inference",
                    reportedAICredits=0,
                    creditValueUsd=0,
                    inputPlusOutputTokens=0,
                    tokens={name: 0 for name in TOKEN_FIELDS},
                )
        cap = self.meta.get("creditCap")
        if (
            cap is not None
            and worker["reportedAICredits"] is not None
            and worker["reportedAICredits"] > cap
        ):
            worker["issues"].append("Reported usage exceeds the configured credit limit.")
        return {
            "schemaVersion": "1.0.0",
            "classification": "SYNTHETIC",
            "metadata": self.meta,
            "coverage": {
                "status": "partial",
                "app": "not_reported",
                "scope": "Local engine and emitted CLI metrics only; App calls, tokens, costs, "
                "human time and local hosting costs are not fully measured.",
                "trace": "Observable backend operations, not hidden reasoning or every OS call.",
                "wholeIntakeTokens": None,
                "wholeIntakeCostUsd": None,
            },
            "timing": {
                "approvalToEngineStartSeconds": elapsed(self.meta.get("approvalAt"), started),
                "preflightSeconds": elapsed(self.meta["startedAt"], self.meta.get("createdAt")),
                "queueSeconds": elapsed(self.meta.get("createdAt"), started),
                "backendSeconds": elapsed(started, self.meta.get("finishedAt")),
                "submissionToFinishSeconds": elapsed(
                    self.meta["startedAt"], self.meta.get("finishedAt")
                ),
                "approvalToPublicationSeconds": elapsed(
                    self.meta.get("approvalAt"),
                    self.meta.get("finishedAt") if self.meta["state"] == "completed" else None,
                ),
                "appHandoffSeconds": None,
            },
            "workerUsage": worker,
            "timingIssues": timing_issues,
            "counts": {
                "analysisInvocationAttempts": attempts,
                "localReportRetries": sum(event["status"] == "retry" for event in self.events),
                "traceEvents": len(self.events),
            },
            "costBasis": {
                "source": PRICING_SOURCE,
                "verifiedOn": "2026-09-28",
                "usdPerAICredit": 0.01,
                "meaning": "Published credit-equivalent value, not an invoice. Allowances and "
                "actual charges are not known. The configured credit cap is not consumption.",
                "usageSchemaSource": USAGE_SOURCE,
                "legacyMetric": "Legacy premium-request multipliers are not AI credits or dollars.",
            },
            "traceHead": self.events[-1]["hash"] if self.events else None,
            "lastStep": self.events[-1]["step"] if self.events else "Not recorded",
            "customerReleaseAuthorized": False,
        }

    def persist(self) -> None:
        if self.directory is None:
            return
        document = self.snapshot()
        for name in ("processing-report.json", "processing-report.html"):
            if (self.directory / name).resolve() != self.directory / name:
                raise ValueError("Operator report paths cannot be redirected.")
        atomic_write_text(
            self.directory / "processing-report.json",
            json.dumps(document, indent=2, ensure_ascii=True) + "\n",
        )
        atomic_write_text(
            self.directory / "processing-report.html",
            self._template.render(report=document, events=self.events),
        )
