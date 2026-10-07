# SPDX-License-Identifier: LicenseRef-MOSAIC-Evaluation
"""Verify usage units, missing-data boundaries and content-free operator diagnostics."""

import json
from copy import deepcopy

import pytest

from mosaic.observability import ProcessingRun, provider_observations


def call_event(identifier="one", **overrides):
    return {
        "type": "assistant.usage",
        "id": identifier,
        "data": {
            "model": "gpt-5.4",
            "inputTokens": 120,
            "outputTokens": 30,
            "cacheReadTokens": 40,
            "cacheWriteTokens": 0,
            "reasoningTokens": 5,
            "cost": 1.5,
            "copilotUsage": {"totalNanoAiu": 2_500_000_000},
            **overrides,
        },
    }


def terminal_event():
    return {
        "type": "result",
        "usage": {
            "premiumRequests": 1.5,
            "totalNanoAiu": 2_500_000_000,
            "totalApiDurationMs": 750,
            "modelMetrics": {
                "gpt-5.4": {
                    "requests": {"count": 1, "cost": 1.5},
                    "totalNanoAiu": 2_500_000_000,
                    "usage": {
                        "inputTokens": 120,
                        "outputTokens": 30,
                        "cacheReadTokens": 40,
                        "cacheWriteTokens": 0,
                        "reasoningTokens": 5,
                    },
                },
            },
        },
    }


def test_terminal_and_per_call_metrics_are_not_added_twice() -> None:
    result = provider_observations(
        [call_event(), deepcopy(call_event()), terminal_event()], complete=True
    )
    assert result["status"] == "reported"
    assert result["inputPlusOutputTokens"] == 150
    assert result["tokens"]["cacheReadTokens"] == 40
    assert result["tokens"]["reasoningTokens"] == 5
    assert result["reportedAICredits"] == 2.5
    assert result["creditValueUsd"] == 0.025
    assert result["legacyPremiumRequests"] == 1.5
    assert result["actualBilledUsd"] is None
    assert result["reportedProviderCalls"] == 1
    assert result["providerApiDurationMs"] == 750


def test_missing_usage_and_context_utilization_are_not_zero_or_billing() -> None:
    result = provider_observations(
        [
            {"type": "session.usage_info", "data": {"currentTokens": 1000, "tokenLimit": 200000}},
            {"type": "result", "usage": {"premiumRequests": 0}},
        ],
        complete=True,
    )
    assert result["status"] == "partial"
    assert result["legacyPremiumRequests"] == 0
    assert result["reportedAICredits"] is None
    assert result["creditValueUsd"] is None
    assert result["inputPlusOutputTokens"] is None
    assert all(value is None for value in result["tokens"].values())


@pytest.mark.parametrize("value", [-1, True, "120", 1.5, float("inf"), 10**100])
def test_invalid_token_counters_are_visible_and_not_defaulted(value) -> None:
    result = provider_observations([call_event(inputTokens=value)], complete=True)
    assert result["status"] == "partial"
    assert result["issues"]
    assert result["tokens"]["inputTokens"] is None
    assert result["inputPlusOutputTokens"] is None
    assert result["reportedAICredits"] == 2.5


def test_failed_or_truncated_calls_keep_known_usage_but_label_it_partial() -> None:
    result = provider_observations([call_event()], complete=False, malformed=True)
    assert result["status"] == "partial"
    assert result["completeOutput"] is False
    assert result["reportedAICredits"] == 2.5
    assert result["issues"]


def test_legacy_cost_never_becomes_ai_credits_or_dollars() -> None:
    result = provider_observations([call_event(copilotUsage=None, cost=30)], complete=True)
    assert result["legacyPremiumRequests"] == 30
    assert result["reportedAICredits"] is None
    assert result["creditValueUsd"] is None
    assert result["actualBilledUsd"] is None


def test_distinct_calls_are_summed_once_without_exposing_provider_identifiers() -> None:
    result = provider_observations(
        [call_event("first-private-request-id"), call_event("second-private-request-id")],
        complete=True,
    )
    assert result["reportedProviderCalls"] == 2
    assert result["reportedAICredits"] == 5
    assert result["inputPlusOutputTokens"] == 300
    assert "private-request-id" not in json.dumps(result)


def test_model_text_reasoning_quota_and_diagnostics_never_become_telemetry() -> None:
    secret = "PRIVATE-CANARY-DO-NOT-LOG"
    result = provider_observations(
        [
            {"type": "user.message", "data": {"content": secret}},
            {"type": "assistant.reasoning", "data": {"content": secret}},
            {"type": "session.error", "data": {"message": secret}},
            {
                "type": "assistant.message",
                "data": {"content": '{"totalNanoAiu":999999999999}', "reasoningText": secret},
            },
            call_event(quotaSnapshots={"account": secret}, apiCallId=secret),
        ],
        complete=True,
    )
    assert secret not in json.dumps(result)
    assert result["reportedAICredits"] == 2.5
    assert "999999999999" not in json.dumps(result)


def test_conflicting_duplicate_events_are_flagged_without_duplicate_charges() -> None:
    result = provider_observations([call_event(), call_event(outputTokens=45)], complete=True)
    assert result["status"] == "partial"
    assert result["reportedProviderCalls"] == 1
    assert result["reportedAICredits"] == 2.5
    assert any("Conflicting duplicate" in issue for issue in result["issues"])


@pytest.mark.parametrize("approval", ["2099-01-01T00:00:00Z", "invalid-timestamp"])
def test_inconsistent_timing_is_flagged_instead_of_zero(tmp_path, approval: str) -> None:
    run = ProcessingRun()
    state = {
        "jobId": "JOB-SYN-TIMING-" + "0" * 32,
        "state": "running",
        "createdAt": run.meta["startedAt"],
        "analysis": {"model": "test-model", "max_ai_credits": 30, "timeout_seconds": 600},
    }
    run.bind(
        tmp_path,
        state,
        {
            "intakeTranscript": {
                "entries": [
                    {"kind": "generation_approval", "timestamp": approval},
                ]
            }
        },
    )
    run.emit("job.execution", "started")
    metrics = run.snapshot()
    assert metrics["timing"]["approvalToEngineStartSeconds"] is None
    assert metrics["timingIssues"]
