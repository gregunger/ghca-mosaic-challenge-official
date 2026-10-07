"""Live behavioral regressions for the MOSAIC custom agent."""

import json
import os
import subprocess
import uuid

import pytest

from mosaic.cli import PROJECT_ROOT


def _run_agent_turn(executable: str, arguments: list[str]) -> tuple[str, list[dict]]:
    completed = subprocess.run(
        [executable, "-C", str(PROJECT_ROOT), *arguments],
        capture_output=True,
        check=False,
        encoding="utf-8",
        errors="replace",
        timeout=120,
    )
    assert completed.returncode == 0, completed.stderr or completed.stdout
    events = [
        json.loads(line) for line in completed.stdout.splitlines() if line.lstrip().startswith("{")
    ]
    messages = [event["data"] for event in events if event.get("type") == "assistant.message"]
    assert messages, completed.stdout
    delivered = messages[-1]
    assert not delivered.get("toolRequests")
    tool_requests = [
        request
        for message in messages
        for request in message.get("toolRequests", [])
        if request.get("name") != "skill"
    ]
    return delivered["content"], tool_requests


@pytest.mark.skipif(
    not os.environ.get("MOSAIC_TEST_LIVE_AGENT_EXE"),
    reason="Set MOSAIC_TEST_LIVE_AGENT_EXE to run the credit-consuming custom-agent regression.",
)
def test_numeric_first_option_stops_live_intake_and_opens_generation_plan() -> None:
    executable = os.environ["MOSAIC_TEST_LIVE_AGENT_EXE"]
    session_name = f"mosaic-numeric-end-intake-{uuid.uuid4().hex}"
    common = ["--allow-all-tools", "--output-format", "json"]

    menu, _ = _run_agent_turn(
        executable,
        [
            "--agent",
            "MOSAIC Orchestrator",
            "--model",
            "auto",
            "--name",
            session_name,
            *common,
            "-p",
            "Menu",
        ],
    )
    first_question, first_question_tools = _run_agent_turn(
        executable,
        ["-r", session_name, *common, "-p", "1"],
    )
    second_question, second_question_tools = _run_agent_turn(
        executable,
        [
            "-r",
            session_name,
            *common,
            "-p",
            (
                "Employees need one trusted place to find current travel policy guidance "
                "because they waste time searching conflicting documents."
            ),
        ],
    )
    generation_plan, generation_plan_tools = _run_agent_turn(
        executable,
        ["-r", session_name, *common, "-p", "1"],
    )

    assert "**MOSAIC**" in menu
    assert "1. **Submit a new intake request**" in menu
    assert "What business problem or opportunity would you like help with?" in first_question
    first_question_surface = first_question + json.dumps(first_question_tools)
    second_question_surface = second_question + json.dumps(second_question_tools)
    assert "End intake and generate report" not in first_question_surface
    assert "End intake and generate report" in second_question_surface
    assert not second_question_tools or "End intake and generate report" in json.dumps(
        second_question_tools
    )
    normalized_plan = generation_plan.lower()
    assert "plan" in normalized_plan
    assert "approve" in normalized_plan
    assert "report" in normalized_plan or "document" in normalized_plan
    assert "End intake and generate report" not in generation_plan
    assert not generation_plan_tools or "approve" in json.dumps(generation_plan_tools).lower()
