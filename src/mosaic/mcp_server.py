# SPDX-License-Identifier: LicenseRef-MOSAIC-Evaluation
"""Read-only MCP tools for the allowlisted synthetic evidence catalog."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from mcp.server import MCPServer

from mosaic.connectors import SyntheticSourceConnector

PROJECT_ROOT = Path(__file__).resolve().parents[2]
EXAMPLE_DIRECTORY = PROJECT_ROOT / "examples" / "synthetic"
CATALOG_PATH = EXAMPLE_DIRECTORY / "sources" / "catalog.json"
POLICY_PATH = EXAMPLE_DIRECTORY / "source-policy.json"


def _load_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as stream:
        value = json.load(stream)
    if not isinstance(value, dict):
        raise ValueError(f"Expected a JSON object in {path.name}")
    return value


def _approved_evidence() -> list[dict[str, Any]]:
    connector = SyntheticSourceConnector(
        _load_json(CATALOG_PATH),
        _load_json(POLICY_PATH),
        CATALOG_PATH.parent,
    )
    return connector.acquire()


def list_approved_sources() -> dict[str, Any]:
    """List metadata for every source approved by the synthetic source policy."""
    sources = _approved_evidence()
    return {
        "mode": "read-only",
        "dataBoundary": "synthetic",
        "networkAccess": False,
        "sources": [
            {
                "id": source["id"],
                "title": source["title"],
                "classification": source["classification"],
                "owner": source["owner"],
                "revision": source["revision"],
                "sha256": source["sha256"],
            }
            for source in sources
        ],
    }


def read_approved_source(source_id: str) -> dict[str, Any]:
    """Read one allowlisted synthetic source by evidence ID; arbitrary paths are rejected."""
    evidence = {source["id"]: source for source in _approved_evidence()}
    if source_id not in evidence:
        raise ValueError(f"Evidence source {source_id!r} is not approved.")
    source = evidence[source_id]
    source_path = CATALOG_PATH.parent / source["sourcePath"]
    return {
        "id": source["id"],
        "title": source["title"],
        "classification": source["classification"],
        "revision": source["revision"],
        "sha256": source["sha256"],
        "content": source_path.read_text(encoding="utf-8"),
        "provenance": "allowlisted synthetic fixture",
    }


server = MCPServer(
    "mosaic-synthetic-evidence",
    title="MOSAIC Synthetic Evidence",
    description="Read-only access to the release-safe evidence used by the MOSAIC demo.",
    instructions=(
        "Use only for the bundled synthetic scenario. List approved sources before reading one. "
        "Do not treat this server as production authorization or customer evidence."
    ),
    version="1.0.0",
)
server.tool(structured_output=True)(list_approved_sources)
server.tool(structured_output=True)(read_approved_source)


def main() -> None:
    server.run(transport="stdio")


if __name__ == "__main__":
    main()
