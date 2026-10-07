# SPDX-License-Identifier: LicenseRef-MOSAIC-Evaluation
"""Verify fail-closed request and package schema contracts."""

import copy
import json
from pathlib import Path

import pytest

from mosaic.schema_validation import validate_instance

REQUEST_PATH = Path(__file__).parents[1] / "examples" / "synthetic" / "request.json"


def load_request() -> dict[str, object]:
    with REQUEST_PATH.open(encoding="utf-8") as stream:
        request = json.load(stream)
    assert isinstance(request, dict)
    return request


def test_synthetic_request_matches_schema() -> None:
    validate_instance(load_request(), "intake-request.schema.json")


def test_schema_rejects_non_synthetic_identifier() -> None:
    request = copy.deepcopy(load_request())
    request["initiativeId"] = "LIVE-001"

    with pytest.raises(ValueError, match="intake-request.schema.json validation failed"):
        validate_instance(request, "intake-request.schema.json")


def test_schema_rejects_invalid_utc_timestamp() -> None:
    request = load_request()
    request["requestedAt"] = "not-a-timestampZ"

    with pytest.raises(ValueError, match="date-time"):
        validate_instance(request, "intake-request.schema.json")
