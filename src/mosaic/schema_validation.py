# SPDX-License-Identifier: LicenseRef-MOSAIC-Evaluation
"""JSON Schema validation for inputs and generated workflow contracts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

SCHEMA_DIRECTORY = Path(__file__).resolve().parents[2] / "schemas"


def validate_instance(instance: Any, schema_name: str) -> None:
    schema_path = SCHEMA_DIRECTORY / schema_name
    with schema_path.open(encoding="utf-8") as stream:
        schema = json.load(stream)
    errors = sorted(
        Draft202012Validator(
            schema, format_checker=Draft202012Validator.FORMAT_CHECKER
        ).iter_errors(instance),
        key=lambda error: [str(part) for part in error.absolute_path],
    )
    if not errors:
        return
    details = []
    for error in errors:
        location = ".".join(str(part) for part in error.absolute_path) or "$"
        details.append(f"{location}: {error.message}")
    raise ValueError(f"{schema_name} validation failed: {'; '.join(details)}")
