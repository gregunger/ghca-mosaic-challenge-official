# SPDX-License-Identifier: LicenseRef-MOSAIC-Evaluation
"""Offline evidence connector constrained by a synthetic source policy."""

from __future__ import annotations

import hashlib
from collections.abc import Mapping
from pathlib import Path
from typing import Any


class SyntheticSourceConnector:
    def __init__(
        self,
        catalog: Mapping[str, Any],
        policy: Mapping[str, Any],
        catalog_directory: Path,
    ) -> None:
        self._catalog = catalog
        self._policy = policy
        self._catalog_directory = catalog_directory

    def acquire(self) -> list[dict[str, Any]]:
        allowed_ids = set(self._policy.get("allowedSourceIds", []))
        allowed_classifications = set(self._policy.get("allowedClassifications", []))
        evidence: list[dict[str, Any]] = []
        seen_ids: set[str] = set()
        catalog_root = self._catalog_directory.resolve()

        for source in self._catalog.get("sources", []):
            source_id = source.get("id")
            classification = source.get("classification")
            if source_id not in allowed_ids:
                raise ValueError(f"Source {source_id!r} is not allowlisted.")
            if source_id in seen_ids:
                raise ValueError(f"Duplicate evidence source {source_id!r}.")
            seen_ids.add(source_id)
            if classification not in allowed_classifications:
                raise ValueError(
                    f"Source {source_id!r} has disallowed classification {classification!r}."
                )
            if source.get("approved") is not True:
                raise ValueError(f"Source {source_id!r} is not approved.")

            relative_path = Path(str(source.get("file", "")))
            if relative_path.is_absolute() or ".." in relative_path.parts:
                raise ValueError(f"Source {source_id!r} must use a contained relative path.")
            source_path = (catalog_root / relative_path).resolve()
            if not source_path.is_relative_to(catalog_root):
                raise ValueError(f"Source {source_id!r} must resolve to a contained path.")
            if not source_path.is_file():
                raise FileNotFoundError(
                    f"Approved source {source_id!r} is missing: {relative_path}"
                )

            content = source_path.read_bytes()
            evidence.append(
                {
                    "id": source_id,
                    "title": source["title"],
                    "classification": classification,
                    "owner": source["owner"],
                    "revision": source["revision"],
                    "retrievedAt": source["retrievedAt"],
                    "sourcePath": relative_path.as_posix(),
                    "sha256": hashlib.sha256(content).hexdigest(),
                    "facts": source.get("facts", []),
                }
            )

        if set(item["id"] for item in evidence) != allowed_ids:
            missing = sorted(allowed_ids - set(item["id"] for item in evidence))
            raise ValueError(f"Allowlisted sources are absent from the catalog: {missing}")
        return evidence
