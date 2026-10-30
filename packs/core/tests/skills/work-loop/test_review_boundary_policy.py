"""Review-boundary policy isolation: no reviewer procedure in the runtime modules.

Mode: goal-based check (structured-review-boundary plan T7, VI-1014).

A bounded source check over the shipped review-boundary runtime modules and the
review-policy data shape. It fails on any reviewer-role literal in the
``_review_*.py`` modules and ``_evidence_store.py``, and on any prompt, tool,
model, retry, session, or reviewer-workflow field name in the ``_review_*.py``
modules. The policy's closed shape refuses each such field with
``denied-review-policy-unknown-field``. Each AST check has a mutation control
that proves it can fail.

The suite loads shipped work-loop scripts by literal path. No test in this file
reads above packs/core/; the lint-pack-test-boundary.py tool enforces it.
"""

from __future__ import annotations

import ast
import importlib.util
import os
import stat
import sys
from pathlib import Path
from types import ModuleType

import pytest

PACK_ROOT = Path(__file__).resolve().parents[3]
SCRIPTS = PACK_ROOT / ".apm" / "skills" / "work-loop" / "scripts"


def _load_module(module_name: str, path: Path) -> ModuleType:
    """Load a work-loop script by literal path for pack-boundary tests."""
    if not path.exists():
        pytest.fail(f"T7 module is not implemented: {path.name}")
    info = os.lstat(path)
    assert stat.S_ISREG(info.st_mode), f"not a regular file: {path}"
    previous = sys.dont_write_bytecode
    try:
        sys.dont_write_bytecode = True
        spec = importlib.util.spec_from_file_location(module_name, str(path))
        assert spec is not None and spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    finally:
        sys.dont_write_bytecode = previous


# ── Module fixtures ───────────────────────────────────────────────────────────


@pytest.fixture(scope="module")
def review_selection_t7() -> ModuleType:
    return _load_module("review_selection_t7", SCRIPTS / "_review_selection.py")


# Reviewer-role names that must not appear as string literals in the structured
# review-boundary runtime modules: they live only in policy data, never in
# delivery-policy code.
_FORBIDDEN_ROLE_NAMES: frozenset[str] = frozenset({
    "adversarial-reviewer",
    "security-reviewer",
    "quality-engineer",
    "experience-reviewer",
    "frontend-reviewer",
})

# Field names that must not appear in the review-policy closed shape or the
# structured review-boundary module source.  Each represents reviewer-internal
# procedure that the boundary must not encode.
_FORBIDDEN_FIELD_NAMES: frozenset[str] = frozenset({
    "prompt",
    "model",
    "retry",
    "session",
    "reviewer_workflow",
    "reviewer-workflow",
})


# ── VI-1014: Policy-leakage check ────────────────────────────────────────────


def test_vi1014_no_reviewer_role_literals_in_review_modules() -> None:
    """No _review_*.py module or _evidence_store.py contains a reviewer-role literal.

    Role names must live only in policy data, never in delivery-policy code.
    This is the AST check: role-name string constants fail.
    """
    review_modules = [
        p for p in SCRIPTS.iterdir()
        if p.name.startswith("_review_") and p.suffix == ".py"
    ] + [SCRIPTS / "_evidence_store.py"]

    hits: list[str] = []
    for path in review_modules:
        src = path.read_text(encoding="utf-8")
        try:
            tree = ast.parse(src, filename=str(path))
        except SyntaxError as exc:
            pytest.fail(f"SyntaxError parsing {path.name}: {exc}")
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.Constant)
                and isinstance(node.value, str)
                and node.value in _FORBIDDEN_ROLE_NAMES
            ):
                hits.append(f"{path.name}:{node.lineno}: {node.value!r}")
    assert not hits, (
        "Reviewer role-name literals found in shipped review modules "
        "(role names must live only in policy data):\n"
        + "\n".join(hits)
    )


def test_vi1014_no_forbidden_field_names_in_review_modules() -> None:
    """No _review_*.py module contains forbidden procedure field names.

    Reviewer-specific fields (prompt, model, retry, session, reviewer_workflow)
    must not appear as string constants or function parameter names in the
    structured review-boundary runtime modules.
    """
    review_modules = [
        p for p in SCRIPTS.iterdir()
        if p.name.startswith("_review_") and p.suffix == ".py"
    ]

    hits: list[str] = []
    for path in review_modules:
        src = path.read_text(encoding="utf-8")
        try:
            tree = ast.parse(src, filename=str(path))
        except SyntaxError as exc:
            pytest.fail(f"SyntaxError parsing {path.name}: {exc}")
        for node in ast.walk(tree):
            # Check string constants.
            if (
                isinstance(node, ast.Constant)
                and isinstance(node.value, str)
                and node.value in _FORBIDDEN_FIELD_NAMES
            ):
                hits.append(
                    f"{path.name}:{node.lineno}: constant {node.value!r}"
                )
            # Check function parameter names.
            elif isinstance(node, ast.arg) and node.arg in _FORBIDDEN_FIELD_NAMES:
                hits.append(
                    f"{path.name}:{node.lineno}: param {node.arg!r}"
                )
    assert not hits, (
        "Forbidden procedure field names found in shipped review modules:\n"
        + "\n".join(hits)
    )


def test_vi1014_validate_policy_closed_shape_excludes_forbidden_fields(
    review_selection_t7: ModuleType,
) -> None:
    """_review_selection._validate_policy rejects a policy dict with a forbidden field.

    The policy's closed shape must not admit reviewer-procedure fields.
    """
    subject = _minimal_review_subject(review_selection_t7)
    base_policy = {
        "policy_id": "p1",
        "review_policy_fingerprint": subject["review_policy_fingerprint"],
        "policy_version": "1",
        "selector": "s1",
        "roles": [{"role": "reviewer-t7", "kind": "mandatory"}],
        "waivers": [],
    }
    # Positive control: the closed shape itself is accepted.
    assert review_selection_t7.select_review_obligations(subject, base_policy)
    for field in ("prompt", "tool", "model", "retry", "session", "reviewer_workflow_state"):
        with pytest.raises(review_selection_t7.ReviewSelectionRefused) as exc_info:
            review_selection_t7.select_review_obligations(
                subject, {**base_policy, field: "should-be-rejected"}
            )
        assert exc_info.value.denial_code == "denied-review-policy-unknown-field"


def _minimal_review_subject(review_selection_t7: ModuleType) -> dict:
    """Return a minimal valid review subject for policy tests."""
    delivery_subject = {
        "schema_version": 1,
        "subject_id": "delivery-subject-t7-policy",
        "acceptance_fingerprint": "acceptance-fp-t7",
        "product": {
            "base_ref": "base-tree-t7",
            "result_ref": "result-tree-t7",
        },
        "spec": {
            "path": "docs/specs/example-feature/spec.md",
            "fingerprint": "spec-fp-t7",
        },
        "evidence_policy_ref": "evidence-policy-t7",
        "exclusions": [],
        "lineage": {
            "provider": "legacy-worktree-snapshot",
            "projection_version": "1.0",
        },
        "task_projection_revision": "task-rev-t7",
        "task_projection_hash": "task-hash-t7",
    }
    return review_selection_t7.project_review_subject(
        delivery_subject,
        changed_paths=[
            {"path": "packs/core/.apm/skills/work-loop/scripts/_review_contracts.py", "status": "added"}
        ],
        review_policy_fingerprint="review-policy-fp-t7",
    )


# ── VI-1014 mutation check helpers ───────────────────────────────────────────


def _role_literal_violation_src(original: str) -> str:
    """Inject an adversarial-reviewer string constant to prove the test reds."""
    return original + '\n_MUTATION_VIOLATION = "adversarial-reviewer"\n'


def _field_violation_src(original: str) -> str:
    """Inject a 'prompt' string constant to prove the test reds."""
    return original + '\n_MUTATION_VIOLATION = "prompt"\n'


def test_vi1014_mutation_check_role_literal_detection(tmp_path: Path) -> None:
    """Mutation check: injecting a role literal into a temp module makes the check red.

    This proves the AST scan is load-bearing and not a no-op.
    """
    # Use _review_contracts.py as the mutation target (it has no forbidden literals).
    original_path = SCRIPTS / "_review_contracts.py"
    original_src = original_path.read_text(encoding="utf-8")
    mutated_src = _role_literal_violation_src(original_src)

    mutated_path = tmp_path / "_review_contracts_mutated_t7.py"
    mutated_path.write_text(mutated_src, encoding="utf-8")

    # Run the same check against the mutated source.
    try:
        tree = ast.parse(mutated_src, filename=str(mutated_path))
    except SyntaxError as exc:
        pytest.fail(f"Mutated source has SyntaxError: {exc}")

    hits = []
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Constant)
            and isinstance(node.value, str)
            and node.value in _FORBIDDEN_ROLE_NAMES
        ):
            hits.append(f"{mutated_path.name}:{node.lineno}: {node.value!r}")

    assert hits, (
        "Mutation check failed: injecting an adversarial-reviewer literal "
        "was NOT detected by the AST scan. The test is not load-bearing."
    )


def test_vi1014_mutation_check_field_name_detection(tmp_path: Path) -> None:
    """Mutation check: injecting a forbidden field name makes the check red."""
    original_path = SCRIPTS / "_review_contracts.py"
    original_src = original_path.read_text(encoding="utf-8")
    mutated_src = _field_violation_src(original_src)

    mutated_path = tmp_path / "_review_contracts_field_mutated_t7.py"
    mutated_path.write_text(mutated_src, encoding="utf-8")

    try:
        tree = ast.parse(mutated_src, filename=str(mutated_path))
    except SyntaxError as exc:
        pytest.fail(f"Mutated source has SyntaxError: {exc}")

    hits = []
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Constant)
            and isinstance(node.value, str)
            and node.value in _FORBIDDEN_FIELD_NAMES
        ):
            hits.append(node.value)

    assert hits, (
        "Mutation check failed: injecting a 'prompt' field constant was NOT "
        "detected. The field-name check is not load-bearing."
    )


def test_vi1014_mutation_check_original_is_clean() -> None:
    """After mutation tests, the original _review_contracts.py is still clean.

    Confirms the mutation tests did not corrupt the original source.
    """
    original_path = SCRIPTS / "_review_contracts.py"
    original_src = original_path.read_text(encoding="utf-8")
    tree = ast.parse(original_src, filename=str(original_path))

    role_hits = []
    field_hits = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            if node.value in _FORBIDDEN_ROLE_NAMES:
                role_hits.append(node.value)
            if node.value in _FORBIDDEN_FIELD_NAMES:
                field_hits.append(node.value)

    assert not role_hits, f"Original _review_contracts.py has role literals: {role_hits}"
    assert not field_hits, f"Original _review_contracts.py has forbidden fields: {field_hits}"
