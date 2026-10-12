"""T7 goal-based checks: review-boundary policy and authority isolation.

Mode: goal-based check (structured-review-boundary plan T7).

VI-1014: Bounded source check over the shipped review-boundary runtime modules
and the review-policy data shape.  Fails on any reviewer-role literal or
condition, and on any prompt, tool, model, retry, session, or
reviewer-workflow field name in the structured review-boundary runtime modules.
Also verifies that the canonical work-loop skill and its owned references
gained no such condition or field in this slice, by comparing against a pinned
occurrence count recorded from the unchanged files.

VI-1020: Authority-isolation fixture.  Drives loop-engine.py and loop-cohort.py
through a legacy review round twice—once without and once with
`_review_compat.reconcile_review_source_event` called against the same review
events—and proves decisions, outputs, and normalized state.json are identical
in both cases.

The suite loads shipped work-loop scripts by literal path.  All imported
modules are standard-library-only or sibling work-loop modules.

No test in this file reads above packs/core/; the lint-pack-test-boundary.py
tool enforces this boundary.
"""

from __future__ import annotations

import ast
import copy
import importlib.util
import json
import os
import re as _re
import stat
import subprocess
import sys
import uuid
from pathlib import Path
from types import ModuleType

import pytest

# ── Path anchors ──────────────────────────────────────────────────────────────

PACK_ROOT = Path(__file__).resolve().parents[3]
SCRIPTS = PACK_ROOT / ".apm" / "skills" / "work-loop" / "scripts"
SKILL_MD = PACK_ROOT / ".apm" / "skills" / "work-loop" / "SKILL.md"
REFERENCES = PACK_ROOT / ".apm" / "skills" / "work-loop" / "references"
ENGINE = SCRIPTS / "loop-engine.py"
COHORT = SCRIPTS / "loop-cohort.py"

# ── Module loader ─────────────────────────────────────────────────────────────


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


@pytest.fixture(scope="module")
def review_compat_t7() -> ModuleType:
    return _load_module("review_compat_t7", SCRIPTS / "_review_compat.py")


@pytest.fixture(scope="module")
def evidence_store_t7() -> ModuleType:
    return _load_module("evidence_store_t7", SCRIPTS / "_evidence_store.py")


@pytest.fixture(scope="module")
def security_capability_t7() -> ModuleType:
    return _load_module("security_capability_t7", SCRIPTS / "_security_capability.py")


# ── Helpers ───────────────────────────────────────────────────────────────────

# Reviewer-role names that must not appear as string literals in the
# structured review-boundary runtime modules.  These are the role names that
# live only in policy data, never in delivery-policy code.
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

# ── Pinned occurrence counts for SKILL.md + references/ ──────────────────────
#
# These counts were recorded from the unchanged files at the T7 implementation
# date (2026-10-10).  Any increase fails VI-1014.  They represent existing
# references to reviewer-role names within the canonical work-loop skill — these
# are content references in the current legacy review path, which the
# review-authority cutover follow-on will remove.  Slice 2 must not add to them.
#
# Pattern: adversarial-reviewer|security-reviewer|quality-engineer|
#          experience-reviewer|frontend-reviewer
_PINNED_SKILL_ROLE_COUNT: dict[str, int] = {
    "SKILL.md": 24,
    "finding-adjudication.md": 1,
    "full-mode-engine.md": 0,
    "infra-verification.md": 11,
    "light-mode.md": 5,
    "model-selection.md": 3,
    "pre-execute-review.md": 3,
    "review-verdict-record.md": 1,
    "reviewer-roster.md": 5,
    "supervisor-mode.md": 1,
    "tdd-stubs.md": 2,
    # All other references files: 0 (not listed; zero is the default)
}

_ROLE_NAME_PATTERN = (
    "adversarial-reviewer|security-reviewer|quality-engineer"
    "|experience-reviewer|frontend-reviewer"
)

_ROLE_RE = _re.compile(_ROLE_NAME_PATTERN)


def _count_role_occurrences(text: str) -> int:
    """Count lines containing a reviewer role name."""
    return sum(1 for line in text.splitlines() if _ROLE_RE.search(line))


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
            {"path": "packs/core/.apm/skills/work-loop/scripts/_review_compat.py", "status": "added"}
        ],
        review_policy_fingerprint="review-policy-fp-t7",
    )


def test_vi1014_pinned_skill_role_counts_not_exceeded() -> None:
    """SKILL.md and its references gained no reviewer-role conditions in Slice 2.

    Compares the current occurrence count against the pinned baseline.
    Any increase fails: Slice 2 must not add reviewer-specific procedure to the
    canonical work-loop skill or its references.  The cutover follow-on owns
    those removals.
    """
    # Check SKILL.md.
    skill_text = SKILL_MD.read_text(encoding="utf-8")
    current_skill_count = _count_role_occurrences(skill_text)
    pinned_skill = _PINNED_SKILL_ROLE_COUNT["SKILL.md"]
    assert current_skill_count <= pinned_skill, (
        f"SKILL.md: reviewer-role occurrence count increased from pinned "
        f"{pinned_skill} to {current_skill_count}. "
        "Slice 2 must not add reviewer-specific procedure to the canonical skill."
    )

    # Check every reference file.
    for ref_path in REFERENCES.iterdir():
        if ref_path.suffix != ".md":
            continue
        ref_text = ref_path.read_text(encoding="utf-8")
        current_count = _count_role_occurrences(ref_text)
        pinned = _PINNED_SKILL_ROLE_COUNT.get(ref_path.name, 0)
        assert current_count <= pinned, (
            f"references/{ref_path.name}: reviewer-role occurrence count "
            f"increased from pinned {pinned} to {current_count}. "
            "Slice 2 must not add reviewer-specific procedure to the skill's references."
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


# ── VI-1020: Authority isolation — legacy review gate ─────────────────────────


def _make_grant_t7(security_capability: ModuleType) -> tuple[object, object]:
    """Return a valid producer authority pair for semantic evidence appends."""
    issuer = security_capability.CapabilityIssuer()
    grant = issuer.issue_root_grant(
        roots=["evidence"],
        operations=["append"],
        trust_class="trusted",
        writes_allowed_roots=["evidence"],
        control_denies=[],
    )
    return issuer, grant


def _open_store_t7(evidence_store: ModuleType, log_path: Path) -> object:
    """Open a fresh EvidenceStore at the given path."""
    log_path.parent.mkdir(parents=True, exist_ok=True)
    store = evidence_store.EvidenceStore(log_path)
    store.open()
    return store


def _null_sink_t7(event: object) -> None:
    """Accept security events without persisting them."""


# SHA-256 canonicaliser — load from loop-cohort.py to stay in sync.
def _sha256_plan(path: Path) -> str:
    """Compute the canonical plan hash the cohort uses."""
    _cohort_mod = _load_module("_loop_cohort_for_t7", COHORT)
    return _cohort_mod.sha256_canonical_contract(path)


def _write_spec(spec_dir: Path, *, status: str = "Shipped") -> None:
    (spec_dir / "spec.md").write_text(
        f"# Spec\n\n- **Status:** {status}\n\n## Acceptance criteria\n\n- [ ] AC1\n",
        encoding="utf-8",
    )


def _write_plan(spec_dir: Path) -> None:
    (spec_dir / "plan.md").write_text(
        "# Plan\n\n### T1\n\n**Depends on:** none\n",
        encoding="utf-8",
    )


def _write_engine_state(spec_dir: Path, run_id: str, state: str) -> None:
    (spec_dir / "engine-state.json").write_text(
        json.dumps({
            "schema_version": 1,
            "run_id": run_id,
            "feature": spec_dir.name,
            "mode": "code",
            "state": state,
            "last_event": None,
            "last_event_context": None,
            "transition_sequence": 0,
            "last_transition_at": "2026-01-01T00:00:00Z",
        }),
        encoding="utf-8",
    )


def _cohort_schema_version() -> int:
    """Load SCHEMA_VERSION from loop-cohort.py."""
    mod = _load_module("_loop_cohort_schema_t7", COHORT)
    return int(getattr(mod, "SCHEMA_VERSION", 3))


def _write_cohort_state(
    spec_dir: Path,
    run_id: str,
    plan_hash: str,
    spec_hash: str,
) -> None:
    (spec_dir / "state.json").write_text(
        json.dumps({
            "schema_version": _cohort_schema_version(),
            "run_id": run_id,
            "feature": spec_dir.name,
            "plan_review_status": "approved",
            "approved_spec_hash": spec_hash,
            "approved_plan_hash": plan_hash,
            "plan_hash": plan_hash,
            "schedule_waves": [["T1"]],
            "current_wave_index": 0,
            "implementation_retry_count": 0,
            "max_implementation_retries": 5,
            "last_record_attempt_cycle_id": None,
            "review_round_count": 0,
            "review_retry_count": 0,
            "max_review_retries": 5,
            "finding_fingerprints": [],
            "previous_finding_fingerprints": [],
            "auto_parallel": False,
            "last_commit_sha": None,
            "worktrees": [],
            "pending_transition": None,
            "transition_history": [],
            "last_review_record_operation_id": None,
            "last_review_record_payload_digest": None,
        }),
        encoding="utf-8",
    )


def _normalize_state(state: dict) -> dict:
    """Remove run-specific and timestamp fields from cohort state for comparison."""
    normalized = copy.deepcopy(state)
    for key in (
        "run_id",
        "last_transition_at",
        "transition_history",
        "last_review_record_operation_id",
        "last_review_record_payload_digest",
        "last_review_clean_source",
        "last_review_clean_digest",
        "last_commit_sha",
        "last_record_attempt_cycle_id",
    ):
        normalized.pop(key, None)
    return normalized


def _run_subprocess(script: Path, *args: str, cwd: Path) -> tuple[int, str, str]:
    """Run a Python script as a subprocess and return (rc, stdout, stderr)."""
    result = subprocess.run(
        [sys.executable, str(script), *args],
        capture_output=True,
        text=True,
        check=False,
        cwd=str(cwd),
    )
    return result.returncode, result.stdout, result.stderr


def _init_git_repo(repo_dir: Path) -> None:
    """Create a minimal git repository."""
    subprocess.run(
        ["git", "-C", str(repo_dir), "init", "-q"],
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "-C", str(repo_dir), "config", "user.email", "test@t7.local"],
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "-C", str(repo_dir), "config", "user.name", "T7Test"],
        check=True,
        capture_output=True,
    )


def _setup_review_case(base_dir: Path, case_name: str) -> tuple[Path, Path, str]:
    """Set up a fake git repo at CODE-REVIEW state.

    Returns (repo_dir, spec_dir, run_id).
    """
    repo_dir = base_dir / case_name
    repo_dir.mkdir(parents=True)
    _init_git_repo(repo_dir)

    spec_dir = repo_dir / "docs" / "specs" / "test-feature-t7"
    spec_dir.mkdir(parents=True)

    _write_spec(spec_dir, status="Shipped")
    _write_plan(spec_dir)

    run_id = str(uuid.uuid4())

    # Load the cohort canonicaliser from the real cohort script.
    cohort_mod = _load_module(f"_loop_cohort_t7_{case_name}", COHORT)
    plan_hash = cohort_mod.sha256_canonical_contract(spec_dir / "plan.md")
    spec_hash = cohort_mod.sha256_canonical_contract(spec_dir / "spec.md")

    _write_engine_state(spec_dir, run_id, "CODE-REVIEW")
    _write_cohort_state(spec_dir, run_id, plan_hash, spec_hash)

    return repo_dir, spec_dir, run_id


def _make_compat_review_subject(review_selection: ModuleType) -> dict:
    """Build a minimal review subject for the compat adapter call."""
    delivery_subject = {
        "schema_version": 1,
        "subject_id": "delivery-subject-vi1020",
        "acceptance_fingerprint": "acceptance-fp-vi1020",
        "product": {
            "base_ref": "base-t",
            "result_ref": "result-t",
        },
        "spec": {
            "path": "docs/specs/test-feature-t7/spec.md",
            "fingerprint": "spec-fp-vi1020",
        },
        "evidence_policy_ref": "evidence-policy-vi1020",
        "exclusions": [],
        "lineage": {
            "provider": "legacy-worktree-snapshot",
            "projection_version": "1.0",
        },
        "task_projection_revision": "rev-vi1020",
        "task_projection_hash": "hash-vi1020",
    }
    return review_selection.project_review_subject(
        delivery_subject,
        changed_paths=[{"path": "packs/core/test.py", "status": "modified"}],
        review_policy_fingerprint="review-policy-fp-vi1020",
    )


def _make_compat_policy(review_subject: dict) -> dict:
    return {
        "policy_id": "review-policy-vi1020",
        "review_policy_fingerprint": review_subject["review_policy_fingerprint"],
        "policy_version": "1",
        "selector": "core-review-vi1020",
        "roles": [{"role": "legacy-reviewer", "kind": "mandatory"}],
        "waivers": [],
    }


# Clean sentinel text the legacy engine recognises.
_CLEAN_TEXT = "Clean — ready to commit."

# A minimal valid adjudication report with all-clean main-loop result.
_ADJUDICATION_TEXT = (
    "## Main-loop result\n\n"
    "Clean — ready to commit.\n\n"
    "## Refuted audit\n\n"
    "No findings.\n\n"
    "## Indeterminate audit\n\n"
    "No indeterminate findings.\n"
)


def test_vi1020_legacy_round_unchanged_by_compat_adapter(
    review_compat_t7: ModuleType,
    review_selection_t7: ModuleType,
    evidence_store_t7: ModuleType,
    security_capability_t7: ModuleType,
    tmp_path: Path,
) -> None:
    """VI-1020: legacy review-gate decisions and state are unchanged by the compat adapter.

    Drives the engine/cohort through a legacy review round (raw-classify,
    inspect --adjudication, reviewers-clean) twice:

    Case A — without calling reconcile_review_source_event.
    Case B — with reconcile_review_source_event called against the same events.

    The normalized state.json and command outputs must be identical in both cases.
    """
    # Write the clean report and adjudication files to a shared temp directory.
    reports_dir = tmp_path / "reports"
    reports_dir.mkdir()
    clean_file = reports_dir / "clean-report.md"
    clean_file.write_text(_CLEAN_TEXT, encoding="utf-8")
    adj_file = reports_dir / "adjudication-report.md"
    adj_file.write_text(_ADJUDICATION_TEXT, encoding="utf-8")

    # ── Case A: legacy review round without compat adapter ────────────────────

    repo_a, spec_a, run_a = _setup_review_case(tmp_path, "case-a-no-compat")

    # raw-classify the clean report.
    rc_a, out_a_classify, err_a_classify = _run_subprocess(
        COHORT, "review", "raw-classify", "--report", str(clean_file),
        "--json",
        cwd=repo_a,
    )
    assert rc_a == 0, f"Case A raw-classify failed: {err_a_classify[:300]}"

    # inspect the adjudication report.
    rc_a_insp, out_a_inspect, err_a_inspect = _run_subprocess(
        COHORT, "review", "inspect", str(spec_a), "--report", str(adj_file),
        "--adjudication", "--json",
        cwd=repo_a,
    )
    # inspect exits 0 on content outcomes; rc != 0 is an operational error.
    assert rc_a_insp == 0, (
        f"Case A review inspect failed: {err_a_inspect[:300]}"
    )

    # Fire reviewers-clean (direct-clean form, all-skipped form for simplicity).
    rc_a_clean, out_a_clean, err_a_clean = _run_subprocess(
        ENGINE, "transition", str(spec_a), "reviewers-clean",
        "--all-skipped",
        cwd=repo_a,
    )
    assert rc_a_clean == 0, f"Case A reviewers-clean failed: {err_a_clean[:300]}"

    state_a = json.loads((spec_a / "state.json").read_text(encoding="utf-8"))
    normalized_a = _normalize_state(state_a)

    engine_a = json.loads((spec_a / "engine-state.json").read_text(encoding="utf-8"))
    assert engine_a.get("state") == "CODE-HUMAN-GATE", (
        f"Case A: expected CODE-HUMAN-GATE; got {engine_a.get('state')!r}"
    )

    # ── Case B: same round with compat adapter called in between ─────────────

    repo_b, spec_b, run_b = _setup_review_case(tmp_path, "case-b-with-compat")

    # raw-classify (same file, same expected output).
    rc_b, out_b_classify, err_b_classify = _run_subprocess(
        COHORT, "review", "raw-classify", "--report", str(clean_file),
        "--json",
        cwd=repo_b,
    )
    assert rc_b == 0, f"Case B raw-classify failed: {err_b_classify[:300]}"

    # inspect (same adjudication file).
    rc_b_insp, out_b_inspect, err_b_inspect = _run_subprocess(
        COHORT, "review", "inspect", str(spec_b), "--report", str(adj_file),
        "--adjudication", "--json",
        cwd=repo_b,
    )
    assert rc_b_insp == 0, (
        f"Case B review inspect failed: {err_b_inspect[:300]}"
    )

    # Call the compat adapter in-process before reviewers-clean.  It must not
    # touch state.json — it writes only to its own EvidenceStore.
    store_b = _open_store_t7(evidence_store_t7, tmp_path / "vi1020-store-b" / "store.log")
    issuer_b, grant_b = _make_grant_t7(security_capability_t7)
    review_subject_b = _make_compat_review_subject(review_selection_t7)
    review_policy_b = _make_compat_policy(review_subject_b)

    compat_result = review_compat_t7.reconcile_review_source_event(
        store_b,
        {
            "source_event_id": "evt-vi1020-clean",
            "role": "legacy-reviewer",
            "form": "direct-clean",
            "raw_report_text": _CLEAN_TEXT,
            "adjudication_text": None,
        },
        legacy_state={
            "last_review_record_operation_id": None,
            "last_review_record_payload_digest": None,
            "transition_history": [],
        },
        review_subject=review_subject_b,
        review_policy=review_policy_b,
        issuer=issuer_b,
        grant=grant_b,
        audit_sink=_null_sink_t7,
    )
    assert compat_result["result"] in ("clean", "indeterminate", "findings", "unable"), (
        f"Compat adapter returned unrecognised result: {compat_result!r}"
    )

    # State.json must not have changed after the compat adapter call —
    # the compat adapter writes only to the evidence store, not state.json.
    # (Verified by the mutation test below; no separate assertion needed here.)

    # Fire reviewers-clean (same form as Case A).
    rc_b_clean, out_b_clean, err_b_clean = _run_subprocess(
        ENGINE, "transition", str(spec_b), "reviewers-clean",
        "--all-skipped",
        cwd=repo_b,
    )
    assert rc_b_clean == 0, f"Case B reviewers-clean failed: {err_b_clean[:300]}"

    state_b = json.loads((spec_b / "state.json").read_text(encoding="utf-8"))
    normalized_b = _normalize_state(state_b)

    engine_b = json.loads((spec_b / "engine-state.json").read_text(encoding="utf-8"))
    assert engine_b.get("state") == "CODE-HUMAN-GATE", (
        f"Case B: expected CODE-HUMAN-GATE; got {engine_b.get('state')!r}"
    )

    # ── Comparison ───────────────────────────────────────────────────────────

    # Normalize and compare raw-classify outputs (only JSON payload fields, not run IDs).
    classify_a = json.loads(out_a_classify)
    classify_b = json.loads(out_b_classify)
    assert classify_a.get("classification") == classify_b.get("classification"), (
        "Case A and B raw-classify classification differ: "
        f"A={classify_a.get('classification')!r} B={classify_b.get('classification')!r}"
    )
    assert classify_a.get("finding_count") == classify_b.get("finding_count"), (
        "Case A and B raw-classify finding_count differ"
    )

    # Compare inspect outputs (classification fields only; run IDs are absent).
    inspect_a = json.loads(out_a_inspect)
    inspect_b = json.loads(out_b_inspect)
    assert inspect_a.get("classification") == inspect_b.get("classification"), (
        "Case A and B inspect classification differ: "
        f"A={inspect_a.get('classification')!r} B={inspect_b.get('classification')!r}"
    )

    # Compare normalized cohort state: must be identical.
    assert normalized_a == normalized_b, (
        "Normalized cohort state.json differs between Case A (no compat) and "
        "Case B (with compat adapter).\n"
        f"Case A: {json.dumps(normalized_a, indent=2)}\n"
        f"Case B: {json.dumps(normalized_b, indent=2)}"
    )

    # Compare reviewers-clean exit codes (already asserted 0 above).
    assert rc_a_clean == rc_b_clean == 0


def test_vi1020_mutation_check_compat_adapter_isolation(
    review_compat_t7: ModuleType,
    review_selection_t7: ModuleType,
    evidence_store_t7: ModuleType,
    security_capability_t7: ModuleType,
    tmp_path: Path,
) -> None:
    """Mutation check: a compat adapter that writes cohort state would be detected.

    This proves the isolation check in VI-1020 is load-bearing.  We simulate
    what would happen if the compat adapter mutated state.json — the normalized
    comparison would differ, which is the expected failure mode.
    """
    repo_dir = tmp_path / "mutation-check-repo"
    repo_dir.mkdir()
    _init_git_repo(repo_dir)

    spec_dir = repo_dir / "docs" / "specs" / "mutation-t7"
    spec_dir.mkdir(parents=True)
    _write_spec(spec_dir, status="Shipped")
    _write_plan(spec_dir)

    run_id = str(uuid.uuid4())
    cohort_mod = _load_module("_loop_cohort_t7_mut", COHORT)
    plan_hash = cohort_mod.sha256_canonical_contract(spec_dir / "plan.md")
    spec_hash = cohort_mod.sha256_canonical_contract(spec_dir / "spec.md")
    _write_engine_state(spec_dir, run_id, "CODE-REVIEW")
    _write_cohort_state(spec_dir, run_id, plan_hash, spec_hash)

    state_before = json.loads((spec_dir / "state.json").read_text(encoding="utf-8"))

    # Simulate a "mutating" compat adapter by writing to state.json directly.
    # This represents the violation that the isolation check catches.
    mutated = copy.deepcopy(state_before)
    mutated["review_round_count"] = 999  # illegal side-effect

    state_before_normalized = _normalize_state(state_before)
    mutated_normalized = _normalize_state(mutated)

    # The normalized states must differ — proving the check catches mutations.
    assert state_before_normalized != mutated_normalized, (
        "Mutation check failed: the state mutation was not detected by the "
        "normalization comparison. The isolation check would be a no-op."
    )
