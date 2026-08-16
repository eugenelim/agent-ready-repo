"""Shared helpers for project-knowledge construction tests."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

PACK_ROOT = Path(__file__).resolve().parents[3]
PROJECT_KNOWLEDGE_SCRIPT = (
    PACK_ROOT
    / ".apm"
    / "skills"
    / "project-knowledge"
    / "scripts"
    / "project_knowledge.py"
)
KNOWLEDGE_STORE_SCRIPT = (
    PACK_ROOT
    / ".apm"
    / "skills"
    / "project-knowledge"
    / "scripts"
    / "knowledge_store.py"
)


def load_project_knowledge_module():
    spec = importlib.util.spec_from_file_location(
        "project_knowledge_under_test", PROJECT_KNOWLEDGE_SCRIPT
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def load_knowledge_store_module():
    spec = importlib.util.spec_from_file_location(
        "knowledge_store_under_test", KNOWLEDGE_STORE_SCRIPT
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def valid_capture_request(**overrides: Any) -> dict[str, Any]:
    request: dict[str, Any] = {
        "contract_version": "knowledge-captured-observation.v1",
        "lesson": "Prefer the repo-owned contract before adding a local format.",
        "kind": "pattern",
        "project_scope": {"paths": ["packs/core"], "audience": "project"},
        "competency_facets": ["CQ-DESIGN", "CQ-VERIFY"],
        "destination_hint": {
            "type": "topic",
            "path": "docs/knowledge/topics/contracts/public-contracts.json",
        },
        "producer": {
            "workflow": "work-loop",
            "workflow_version": "2.5.9",
        },
        "semantic_gate": {
            "name": "verified-slice",
            "artifact": "docs/specs/example/plan.md",
        },
        "provenance": {
            "sources": [
                {
                    "path": "packs/core/.apm/skills/work-loop/SKILL.md",
                    "line_start": 10,
                    "line_end": 20,
                }
            ]
        },
        "freshness_anchor": {
            "path": "contracts/jsonschema/normalized-intake.schema.json",
            "digest": {
                "kind": "sha256-bytes-v1",
                "sha256": "a" * 64,
                "byte_length": 100,
            },
        },
        "observed_at": "2026-08-13T12:34:56Z",
        "privacy_attestation": {
            "reviewed": True,
            "contains_private_data": False,
            "contains_secrets": False,
            "contains_instructions": False,
        },
        "friction": {
            "failed_attempts": 3,
            "summary": "The correct contract authority took several attempts to locate.",
        },
        "verification_route": {
            "command": "python3 tools/catalogue/check_contract_parity.py",
            "path": "tools/catalogue/check_contract_parity.py",
        },
    }
    request.update(overrides)
    return request


def initialize_empty_v1_repo(repo: Path, store: Any) -> Path:
    """Create the committed empty v1 activation snapshot used by writer tests."""

    (repo / "docs" / "knowledge").mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "user@example.com"],
        cwd=repo,
        check=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Example User"],
        cwd=repo,
        check=True,
    )
    store.rebuild_topic_map(repo)
    subprocess.run(["git", "add", "docs/knowledge/topics.index.json"], cwd=repo, check=True)
    subprocess.run(
        ["git", "commit", "-m", "test: activate empty knowledge"],
        cwd=repo,
        check=True,
        capture_output=True,
    )
    return repo


def assert_strictly_rejected(case: Any) -> None:
    module = load_project_knowledge_module()
    if isinstance(case, bytes):
        with pytest.raises(ValueError):
            module.parse_capture_request(case)
        return

    with pytest.raises(ValueError):
        module.validate_capture_request(case)


def capture_request_with_unknown_field() -> dict[str, Any]:
    request = valid_capture_request()
    request["extra"] = "refuse"
    return request


def capture_request_with_duplicate_key_bytes() -> bytes:
    return (
        b'{"contract_version":"knowledge-captured-observation.v1",'
        b'"contract_version":"knowledge-captured-observation.v1"}'
    )


def capture_request_with_non_finite_number_bytes() -> bytes:
    request = valid_capture_request()
    request["friction"] = {
        "summary": "A bounded construction-test fixture.",
        "failed_attempts": 0,
    }
    raw = json.dumps(request, separators=(",", ":")).encode("utf-8")
    return raw.replace(b'"failed_attempts":0', b'"failed_attempts":NaN')


def capture_request_with_unsafe_unicode() -> dict[str, Any]:
    return valid_capture_request(lesson="unsafe \u202e text")


def capture_request_with_producer_supplied_capture_id() -> dict[str, Any]:
    request = valid_capture_request()
    request["capture_id"] = "kco-202608-" + ("0" * 64)
    return request


def capture_request_without_provenance() -> dict[str, Any]:
    request = valid_capture_request()
    del request["provenance"]
    return request


def capture_request_with_oversized_lesson() -> dict[str, Any]:
    return valid_capture_request(lesson="x" * 2001)
