"""The runtime-neutral subject projector refuses each class of schema-invalid record.

Follows the importlib.util.spec_from_file_location loader pattern so modules
remain unregistered in sys.modules between test sessions.
"""

from __future__ import annotations

import importlib.util
import os
import stat
import subprocess
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

# ── Path anchor ───────────────────────────────────────────────────────────────
#
# parents[3] = packs/core  (test lives in packs/core/tests/skills/work-loop/)

SCRIPTS = (
    Path(__file__).resolve().parents[3]
    / ".apm"
    / "skills"
    / "work-loop"
    / "scripts"
)


# ── Module loader ─────────────────────────────────────────────────────────────


def _load_module(name: str, path: Path) -> ModuleType:
    """Load an unregistered copy of a scripts module via importlib."""
    info = os.lstat(path)
    assert stat.S_ISREG(info.st_mode), f"not a regular file: {path}"
    previous = sys.dont_write_bytecode
    try:
        sys.dont_write_bytecode = True
        sp = importlib.util.spec_from_file_location(name, str(path))
        assert sp is not None and sp.loader is not None
        mod = importlib.util.module_from_spec(sp)
        sys.modules[name] = mod
        try:
            sp.loader.exec_module(mod)  # type: ignore[union-attr]
        finally:
            sys.modules.pop(name, None)
        return mod
    finally:
        sys.dont_write_bytecode = previous


@pytest.fixture(scope="module")
def sp() -> ModuleType:
    """_subject_projection.py — runtime-neutral pure projector."""
    return _load_module("sp_t6", SCRIPTS / "_subject_projection.py")


@pytest.fixture(scope="module")
def guards() -> ModuleType:
    """_loop_guards.py — for sha256_canonical_contract (used in test setup)."""
    return _load_module("guards_t6", SCRIPTS / "_loop_guards.py")


# ── Fixtures ──────────────────────────────────────────────────────────────────


def _git(*args: str, cwd: Path) -> subprocess.CompletedProcess:  # type: ignore[type-arg]
    """Run a git command in *cwd*; raise CalledProcessError on failure."""
    return subprocess.run(
        ["git"] + list(args),
        cwd=str(cwd),
        capture_output=True,
        check=True,
    )


def _setup_git_repo(root: Path) -> None:
    """Initialise a minimal Git repo in *root* with identity configured."""
    _git("init", "-q", cwd=root)
    _git("config", "user.email", "test@example.com", cwd=root)
    _git("config", "user.name", "Test User", cwd=root)


def _commit_all(root: Path, message: str = "init") -> str:
    """Stage all changes and commit; return the HEAD commit SHA."""
    _git("add", ".", cwd=root)
    _git("commit", "-q", "-m", message, cwd=root)
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=str(root),
        capture_output=True,
        check=True,
    )
    return result.stdout.decode().strip()


def _make_spec_and_plan(spec_dir: Path) -> None:
    """Write minimal spec.md and plan.md with Approved status."""
    spec_dir.mkdir(parents=True, exist_ok=True)
    (spec_dir / "spec.md").write_text(
        "# Spec\n\n- **Status:** Approved\n\n## Acceptance Criteria\n\n- [ ] AC-0001.\n",
        encoding="utf-8",
    )
    (spec_dir / "plan.md").write_text(
        "# Plan\n\n- **Status:** Approved\n\n## Tasks\n\n### T1: Task\n\n- [ ] Done.\n",
        encoding="utf-8",
    )


def null_sink(event: Any) -> None:
    """No-op audit sink for tests."""


# ── AC-0005: Provider parity ──────────────────────────────────────────────────


# ── AC-0006: Subject-admission negatives ─────────────────────────────────────


# ── AC-0006: Traversal limit fixtures ────────────────────────────────────────


# ── Validate-subject-dict: in-code schema validation ─────────────────────────


class TestValidateSubjectDict:
    """validate_subject_dict refuses each class of schema-invalid input."""

    def test_refuses_unknown_schema_version(self, sp: ModuleType) -> None:
        ok, code = sp.validate_subject_dict({"schema_version": 99})
        assert not ok
        assert code == "denied-unknown-schema-version"

    def test_refuses_missing_required_field(self, sp: ModuleType) -> None:
        record = {
            "schema_version": 1,
            # subject_id omitted
            "acceptance_fingerprint": "fp",
            "product": {"base_ref": "b", "result_ref": "r"},
            "spec": {"path": "p", "fingerprint": "f"},
            "evidence_policy_ref": "p",
            "exclusions": [],
            "lineage": {"provider": "x", "projection_version": "1"},
        }
        ok, code = sp.validate_subject_dict(record)
        assert not ok
        assert code == "denied-missing-required-field"

    def test_refuses_unknown_authority_field(self, sp: ModuleType) -> None:
        record = {
            "schema_version": 1,
            "subject_id": "x",
            "acceptance_fingerprint": "fp",
            "product": {"base_ref": "b", "result_ref": "r"},
            "spec": {"path": "p", "fingerprint": "f"},
            "evidence_policy_ref": "pol",
            "exclusions": [],
            "lineage": {"provider": "x", "projection_version": "1"},
            "inject_escalation": "bypass",
        }
        ok, code = sp.validate_subject_dict(record)
        assert not ok
        assert code == "denied-unknown-authority-field"

    def test_accepts_valid_record(self, sp: ModuleType) -> None:
        record = sp.project_delivery_subject(
            subject_id="test-valid-001",
            base_ref="abc",
            result_ref="abc",
            spec_path="docs/specs/test/spec.md",
            spec_fingerprint="fp-test",
            evidence_policy_ref="policy:v1",
            exclusions=(".git", "docs/specs/test/"),
            provider="legacy-worktree-snapshot",
            projection_version="1.0",
            manifest_pairs=(("src/x.py", "sha256:abc"),),
        )
        ok, code = sp.validate_subject_dict(record)
        assert ok
        assert code == "ok"
