# SPDX-License-Identifier: LicenseRef-MOSAIC-Evaluation
"""Enforce the read-only MCP evidence allowlist and contained source paths."""

from pathlib import Path

import pytest

from mosaic.connectors import SyntheticSourceConnector
from mosaic.mcp_server import list_approved_sources, read_approved_source


def test_mcp_tools_only_return_allowlisted_synthetic_evidence() -> None:
    catalog = list_approved_sources()

    assert catalog["mode"] == "read-only"
    assert catalog["dataBoundary"] == "synthetic"
    assert catalog["networkAccess"] is False
    assert [source["id"] for source in catalog["sources"]] == [
        "EVD-001",
        "EVD-002",
        "EVD-003",
        "EVD-004",
    ]
    assert read_approved_source("EVD-002")["classification"] == "SYNTHETIC"


@pytest.mark.parametrize("source_id", ["EVD-999", "../request.json", "C:\\secret.txt"])
def test_mcp_source_reader_fails_closed(source_id: str) -> None:
    with pytest.raises(ValueError, match="not approved"):
        read_approved_source(source_id)


def source_record(file: str) -> dict[str, object]:
    return {
        "id": "EVD-001",
        "file": file,
        "classification": "SYNTHETIC",
        "approved": True,
        "title": "Synthetic evidence",
        "owner": "Synthetic owner",
        "revision": "1.0",
        "retrievedAt": "2026-09-15T16:00:00Z",
        "facts": [],
    }


def test_connector_rejects_link_outside_evidence_boundary(tmp_path: Path) -> None:
    sources = tmp_path / "sources"
    sources.mkdir()
    outside = tmp_path / "outside.md"
    outside.write_text("Synthetic out-of-boundary evidence", encoding="utf-8")
    try:
        (sources / "linked.md").symlink_to(outside)
    except OSError:
        pytest.skip("This test requires unprivileged symlink support.")
    connector = SyntheticSourceConnector(
        {"sources": [source_record("linked.md")]},
        {"allowedSourceIds": ["EVD-001"], "allowedClassifications": ["SYNTHETIC"]},
        sources,
    )

    with pytest.raises(ValueError, match="contained"):
        connector.acquire()


def test_connector_rejects_duplicate_evidence_ids(tmp_path: Path) -> None:
    (tmp_path / "source.md").write_text("Synthetic evidence", encoding="utf-8")
    source = source_record("source.md")
    connector = SyntheticSourceConnector(
        {"sources": [source, source]},
        {"allowedSourceIds": ["EVD-001"], "allowedClassifications": ["SYNTHETIC"]},
        tmp_path,
    )

    with pytest.raises(ValueError, match="Duplicate"):
        connector.acquire()


def test_connector_rejects_resolved_path_escape(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source_path = tmp_path / "source.md"
    source_path.write_text("Synthetic evidence", encoding="utf-8")
    original_resolve = Path.resolve

    def resolve(path: Path, *args, **kwargs) -> Path:
        if path == source_path:
            return tmp_path.parent / "outside.md"
        return original_resolve(path, *args, **kwargs)

    monkeypatch.setattr(Path, "resolve", resolve)
    connector = SyntheticSourceConnector(
        {"sources": [source_record("source.md")]},
        {"allowedSourceIds": ["EVD-001"], "allowedClassifications": ["SYNTHETIC"]},
        tmp_path,
    )

    with pytest.raises(ValueError, match="contained"):
        connector.acquire()
