# SPDX-License-Identifier: LicenseRef-MOSAIC-Evaluation
"""Shared contracts for deterministic MOSAIC workflow runs."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class StageResult:
    name: str
    status: str
    control_objective: str
    metadata: dict[str, str]
    output: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class WorkflowResult:
    run_id: str
    initiative_id: str
    state: str
    generated_at: str
    metadata: dict[str, str]
    stages: tuple[StageResult, ...]
    package: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "runId": self.run_id,
            "initiativeId": self.initiative_id,
            "state": self.state,
            "generatedAt": self.generated_at,
            "metadata": self.metadata,
            "stages": [stage.to_dict() for stage in self.stages],
            "package": self.package,
        }
