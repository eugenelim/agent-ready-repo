"""Fixture builders for the candidate-mode and quarantine suites.

Feeds real delivery fact pages, produced by the shipped work-loop feed over
evidence logs written by the shipped Slice 1 and Slice 2 writers, into the
project-knowledge candidate mode.  Loads the work-loop fixture support by path
under a unique name, so the two skills stay independent of each other's
``scripts/`` directories.  Standard library only; no runner collects this file.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

_WORK_LOOP_TESTS = Path(__file__).resolve().parents[1] / "work-loop"
ENABLED = {"WORK_LOOP_SHADOW_SERVICES": "1"}


def _load(alias: str, path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(alias, str(path))
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[alias] = module
    spec.loader.exec_module(module)
    return module


_SUPPORT = _load("pk_candidate_feed_support", _WORK_LOOP_TESTS / "delivery_feed_support.py")
FeedRepo = _SUPPORT.FeedRepo
_FEED = _SUPPORT.load_script("pk_candidate_delivery_feed", "_delivery_feed.py")


def feed_pages(root: Path) -> list[bytes]:
    """Return every rendered feed page for the repository, following continuations."""
    pages: list[bytes] = []
    token: str | None = None
    while True:
        page = _FEED.feed_page(root, continuation=token, environ=ENABLED)
        pages.append(_FEED.render_page(page))
        token = page["continuation"]
        if token is None:
            return pages


def first_page(root: Path) -> bytes:
    """Return the first rendered feed page for the repository."""
    return feed_pages(root)[0]


def tree_bytes(root: Path) -> dict[str, bytes]:
    """Return every regular file under *root* (excluding .git), keyed by relative path."""
    found: dict[str, bytes] = {}
    for path in sorted(root.rglob("*")):
        if path.is_file() and not path.is_symlink() and ".git" not in path.relative_to(root).parts:
            found[path.relative_to(root).as_posix()] = path.read_bytes()
    return found


def text_field(field: str, value: str) -> dict[str, Any]:
    """Return an untrusted-data wrapper for *field*."""
    return {
        "schema_version": 1,
        "record_id": "knowledge-observation-record-1",
        "field_path": field,
        "policy_version": "content-policy-v1",
        "value": value,
    }


def sample_observation(index: int = 0, **overrides: Any) -> dict[str, Any]:
    """Return a schema-valid observation whose identity varies with *index*."""
    digest = f"{index:064x}"
    observation: dict[str, Any] = {
        "schema_version": 1,
        "observation_id": f"knowledge-observation-sha256-{digest}",
        "kind": "gotcha",
        "projection_policy_version": "projection-v1",
        "content_policy_version": "content-policy-v1",
        "source": {
            "spec_path": "docs/specs/example",
            "transaction_id": f"tx-{index}",
            "receipt_id": f"review-failure-sha256-{digest}",
            "report_id": f"report-{index}",
            "finding_id": f"finding-{index}",
            "criterion_ref": "AC-0001",
            "acceptance_fingerprint": "acceptance-fp-1",
            "review_policy_fingerprint": "review-policy-1",
        },
        "scope_paths": ["packs/core/example/module.py"],
        "rule_ref": text_field("rule_ref", "AC-0001"),
        "observed": text_field("observed", "The writer accepts input without validation."),
        "reachable_path": text_field("reachable_path", "A caller reaches the writer directly."),
        "actual_failure": text_field("actual_failure", "Invalid input is persisted."),
    }
    observation.update(overrides)
    return observation


def fact_entry(index: int, observation: dict[str, Any] | None = None) -> dict[str, Any]:
    """Return a fact entry at *index* carrying *observation* (a fresh sample by default)."""
    observation = observation or sample_observation(index)
    return {
        "entry_kind": "fact",
        "ordinal": index,
        "source": {
            "spec_path": observation["source"]["spec_path"],
            "transaction_id": observation["source"]["transaction_id"],
            "record_kind": "evidence-receipt.v1",
            "record_id": observation["source"]["receipt_id"],
            "predecessor_schema_version": 1,
        },
        "observation": observation,
        "none_reason": None,
    }


def sample_page(*entries: dict[str, Any]) -> dict[str, Any]:
    """Return a schema-valid hand-built page holding *entries* (one fact by default)."""
    return {
        "schema_version": 1,
        "snapshot_id": "snapshot-sha256-" + "b" * 64,
        "shadow_services": "enabled",
        "first_ordinal": 0,
        "entries": list(entries) or [fact_entry(0)],
        "continuation": None,
    }
