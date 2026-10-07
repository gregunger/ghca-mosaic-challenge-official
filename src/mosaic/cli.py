# SPDX-License-Identifier: LicenseRef-MOSAIC-Evaluation
"""Command-line entry point for the offline synthetic demonstration."""

from __future__ import annotations

import argparse
import json
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from mosaic.connectors import SyntheticSourceConnector
from mosaic.observability import Observer, observed_step
from mosaic.orchestrator import run_workflow
from mosaic.render import write_run
from mosaic.schema_validation import validate_instance
from mosaic.validators import require_valid

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_EXAMPLE = PROJECT_ROOT / "examples" / "synthetic"
DEFAULT_CUSTOMER = PROJECT_ROOT / "config" / "customers" / "contoso-public-services.synthetic.json"


def _load_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as stream:
        value = json.load(stream)
    if not isinstance(value, dict):
        raise ValueError(f"Expected a JSON object in {path}")
    return value


def run_demo(
    request_path: Path,
    catalog_path: Path,
    policy_path: Path,
    customer_path: Path,
    output_directory: Path,
    *,
    on_event: Observer | None = None,
) -> dict[str, Any]:
    with observed_step(on_event, "validation.request_and_customer"):
        request = _load_json(request_path)
        validate_instance(request, "intake-request.schema.json")
        customer = _load_json(customer_path)
        validate_instance(customer, "customer-config.schema.json")
    if customer["customerId"] != request["customerId"]:
        raise ValueError("Customer configuration does not match the request customerId.")
    if customer["requiredOptionCount"] != 3:
        raise ValueError("The active MOSAIC contract requires exactly three architecture options.")
    catalog = _load_json(catalog_path)
    policy = _load_json(policy_path)
    if customer["sourcePolicyId"] != policy.get("policyId"):
        raise ValueError("Customer configuration does not reference the active source policy.")
    connector = SyntheticSourceConnector(catalog, policy, catalog_path.parent)
    result = run_workflow(request, connector, customer=customer, on_event=on_event)
    with observed_step(on_event, "validation.output_schemas"):
        validate_instance(result.package["evidenceManifest"], "evidence-manifest.schema.json")
        validate_instance(result.to_dict(), "intake-package.schema.json")
    with observed_step(on_event, "validation.governance_and_citations"):
        validation_report = require_valid(result)
    written = write_run(
        result,
        validation_report,
        output_directory,
        required_artifacts=customer["requiredArtifacts"],
        on_event=on_event,
    )
    return {
        "runId": result.run_id,
        "initiativeId": result.initiative_id,
        "state": result.state,
        "validation": validation_report["status"],
        "customerConfiguration": customer["configurationId"],
        "outputDirectory": str(output_directory.resolve()),
        "artifactCount": len(written),
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="mosaic", description="Run the synthetic MOSAIC intake-to-decision workflow."
    )
    parser.add_argument("--request", type=Path, default=DEFAULT_EXAMPLE / "request.json")
    parser.add_argument(
        "--catalog", type=Path, default=DEFAULT_EXAMPLE / "sources" / "catalog.json"
    )
    parser.add_argument("--policy", type=Path, default=DEFAULT_EXAMPLE / "source-policy.json")
    parser.add_argument("--customer", type=Path, default=DEFAULT_CUSTOMER)
    parser.add_argument("--output", type=Path, default=PROJECT_ROOT / "demo-output" / "SYN-001")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        summary = run_demo(args.request, args.catalog, args.policy, args.customer, args.output)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(json.dumps({"status": "fail", "error": str(error)}, indent=2))
        return 1
    print(json.dumps({"status": "pass", **summary}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
