"""A plan-resident consumer map is disposable: losing it cannot move the verdict.

new-spec's shared-substrate preservation reference keeps the consumer map in
the plan, never in ``spec.md``. This pins the behavior that rule relies on: the
file-based subject projector leaves the spec directory out of the product
manifest and admits ``spec.md`` only through its approved digest, so deleting,
rebuilding, or reordering a map in ``plan.md`` keeps the acceptance fingerprint
and the verdict, while the same map in ``spec.md`` stales every receipt.

Spec: docs/specs/grounding-preservation-authoring/spec.md
"""

from __future__ import annotations

import importlib.util
import os
import stat
import subprocess
import sys
from pathlib import Path
from types import ModuleType

import pytest

SCRIPTS = Path(__file__).resolve().parents[3] / ".apm" / "skills" / "work-loop" / "scripts"

PROPERTY_ID = "ordinary-calls-no-synthetic-targets"
TERM = "differential-resolver"

SPEC_TEXT = (
    "# Spec\n\n- **Status:** Approved\n\n## Acceptance Criteria\n\n"
    "- [ ] AC-0001. Ordinary calls resolve to no synthetic value.\n"
)
PLAN_HEAD = "# Plan\n\n- **Status:** Approved\n\n## Design (LLD)\n\n"
PLAN_TAIL = "\n## Tasks\n\n### T1: Preserve call resolution\n\n- [ ] Done.\n"
MAP_ROWS = (
    "| selection and resolution | src/consumers.py:4 | AC-0001 |",
    "| default search | src/consumers.py:9 | AC-0002 |",
    "| lifecycle and cleanup | src/lifecycle.py:9 | AC-0003 |",
)
MAP_HEADER = "| Class | Consumer evidence | Criterion or gap |\n| --- | --- | --- |\n"


def _map(rows: tuple[str, ...]) -> str:
    """Render a consumer map table from *rows*."""
    return MAP_HEADER + "\n".join(rows) + "\n"


PLAN_WITH_MAP = PLAN_HEAD + _map(MAP_ROWS) + PLAN_TAIL
PLAN_WITHOUT_MAP = PLAN_HEAD + PLAN_TAIL
PLAN_REBUILT_MAP = PLAN_HEAD + _map(tuple(reversed(MAP_ROWS))) + PLAN_TAIL
SPEC_WITH_MAP = SPEC_TEXT + "\n## Consumer map\n\n" + _map(MAP_ROWS)


def _load_module(name: str, path: Path) -> ModuleType:
    """Load an unregistered copy of a scripts module by path under *name*."""
    info = os.lstat(path)
    assert stat.S_ISREG(info.st_mode), f"not a regular file: {path}"
    previous = sys.dont_write_bytecode
    try:
        sys.dont_write_bytecode = True
        spec = importlib.util.spec_from_file_location(name, str(path))
        assert spec is not None and spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        try:
            spec.loader.exec_module(module)
        finally:
            sys.modules.pop(name, None)
        return module
    finally:
        sys.dont_write_bytecode = previous


@pytest.fixture(scope="module")
def ss() -> ModuleType:
    """_subject_source.py: the file-based legacy subject projector."""
    return _load_module("core_work_loop_ss_consumer_map", SCRIPTS / "_subject_source.py")


@pytest.fixture(scope="module")
def acc() -> ModuleType:
    """_acceptance.py: the verdict evaluator."""
    return _load_module("core_work_loop_acc_consumer_map", SCRIPTS / "_acceptance.py")


@pytest.fixture(scope="module")
def guards() -> ModuleType:
    """_loop_guards.py: the approved-digest function the projector checks against."""
    return _load_module("core_work_loop_guards_consumer_map", SCRIPTS / "_loop_guards.py")


def _git(root: Path, *args: str) -> None:
    """Run one git command in *root*, failing the test on a non-zero exit."""
    subprocess.run(["git", *args], cwd=str(root), capture_output=True, check=True)


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    """A git repository with one product file and a committed spec directory."""
    _git(tmp_path, "init", "-q")
    _git(tmp_path, "config", "user.email", "test@example.invalid")
    _git(tmp_path, "config", "user.name", "Test")
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "consumers.py").write_text("def resolve_call():\n    pass\n", "utf-8")
    return tmp_path


def _fingerprint(ss: ModuleType, guards: ModuleType, repo: Path, spec: str, plan: str) -> str:
    """Commit *spec* and *plan*, project the subject, and return its acceptance fingerprint."""
    spec_dir = repo / "docs" / "specs" / "shared-substrate-change"
    spec_dir.mkdir(parents=True, exist_ok=True)
    (spec_dir / "spec.md").write_text(spec, "utf-8")
    (spec_dir / "plan.md").write_text(plan, "utf-8")
    _git(repo, "add", ".")
    _git(repo, "commit", "-q", "--allow-empty", "-m", "variant")
    subject = ss.project_legacy_subject(
        repo_root=repo,
        spec_dir=spec_dir,
        approved_spec_hash=guards.sha256_canonical_contract(spec_dir / "spec.md"),
        approved_plan_hash=guards.sha256_canonical_contract(spec_dir / "plan.md"),
        audit_sink=lambda event: None,
        subject_id="subject:shared-substrate-change",
        evidence_policy_ref="evidence-policy:v1",
    )
    return str(subject["acceptance_fingerprint"])


def _property() -> dict:
    """One acceptance-property.v1 record with a single required test term."""
    return {
        "schema_version": 1,
        "property_id": PROPERTY_ID,
        "spec_ref": "docs/specs/shared-substrate-change/spec.md",
        "authority_ref": "approval:spec-policy:v1",
        "subject_selector": {"paths_or_artifacts": ["src/"], "fingerprint_algorithm": "sha256"},
        "required_observations": [
            {
                "term": TERM,
                "observation_type": "test-result",
                "producer_class": "ci-runner",
                "outcomes": ["pass"],
            }
        ],
        "freshness_scope": "exact-subject",
        "satisfaction_rule": {"expression": "all"},
        "contradiction_rule": {"expression": "supported-review-failure"},
        "policy_version": "v1",
    }


def _receipt(fingerprint: str) -> dict:
    """One passing evidence-receipt.v1 for the property's term, bound to *fingerprint*."""
    return {
        "schema_version": 1,
        "receipt_id": f"{PROPERTY_ID}:{TERM}",
        "acceptance_fingerprint": fingerprint,
        "lineage": {"criterion_ref": PROPERTY_ID},
        "selector": {"term": TERM},
        "freshness_mode": "exact-subject",
        "observation": {"type": "test-result"},
        "outcome": "pass",
        "producer": {"class": "ci-runner", "identity": "runner-generic"},
    }


def _verdict(acc: ModuleType, receipt_fingerprint: str, current_fingerprint: str) -> str:
    """Evaluate the property against one receipt and return the verdict string."""
    result = acc.evaluate_verdict(
        property_record=_property(),
        receipts=[_receipt(receipt_fingerprint)],
        current_acceptance_fingerprint=current_fingerprint,
        adapter="sequential-reference",
    )
    return str(result["verdict"])


def test_plan_resident_map_is_disposable(
    ss: ModuleType, acc: ModuleType, guards: ModuleType, repo: Path
) -> None:
    """Deleting or rebuilding the map in plan.md keeps one fingerprint and a supported verdict."""
    bound = _fingerprint(ss, guards, repo, SPEC_TEXT, PLAN_WITH_MAP)
    variants = {
        "with map": bound,
        "map deleted": _fingerprint(ss, guards, repo, SPEC_TEXT, PLAN_WITHOUT_MAP),
        "map rebuilt": _fingerprint(ss, guards, repo, SPEC_TEXT, PLAN_REBUILT_MAP),
    }

    assert set(variants.values()) == {bound}, variants
    for name, current in variants.items():
        assert _verdict(acc, bound, current) == "supported", name


def test_spec_resident_map_stales_the_receipt(
    ss: ModuleType, acc: ModuleType, guards: ModuleType, repo: Path
) -> None:
    """The same map written into spec.md moves the fingerprint and decides insufficient."""
    bound = _fingerprint(ss, guards, repo, SPEC_TEXT, PLAN_WITH_MAP)
    moved = _fingerprint(ss, guards, repo, SPEC_WITH_MAP, PLAN_WITHOUT_MAP)

    assert moved != bound
    assert _verdict(acc, bound, moved) == "insufficient"
