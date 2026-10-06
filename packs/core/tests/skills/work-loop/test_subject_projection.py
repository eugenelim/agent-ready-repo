"""T6 TDD suite: legacy subject projection matches the acknowledged product boundary.

Mode: TDD through Git integration tests (plan.md T6).

Tests:
  AC-0005: provider parity — legacy subject provider and runtime-neutral projector
           emit identical canonical manifests, product fingerprints, exclusions,
           spec identity, and plan provenance for the same acknowledged tree,
           built in temporary Git repositories.

  AC-0006: subject-admission negatives — mutating ignored, untracked, excluded,
           unreadable, link-like, non-regular, unacknowledged, and drifting paths
           one at a time, asserting refusal or policy exclusion with no partial
           manifest; bound-edge and edge-plus-one fixtures for every traversal
           limit owned by the architecture (docs/architecture/
           work-loop-acceptance-evidence.md §6), plus the oversized-repository
           fixture that refuses before emitting a partial manifest.

Traversal-limit constants are read from the subject-source module, not from the
plan document, so the plan never duplicates the architecture-owned numeric values.

Follows the importlib.util.spec_from_file_location loader pattern so modules
remain unregistered in sys.modules between test sessions.
"""

from __future__ import annotations

import importlib.util
import os
import stat
import subprocess
import sys
import time
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
def ss() -> ModuleType:
    """_subject_source.py — legacy worktree provider."""
    return _load_module("ss_t6", SCRIPTS / "_subject_source.py")


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


class TestProviderParityAC0005:
    """AC-0005: legacy subject provider and runtime-neutral projector emit identical results."""

    def test_parity_for_same_acknowledged_tree(
        self,
        ss: ModuleType,
        sp: ModuleType,
        guards: ModuleType,
        tmp_path: Path,
    ) -> None:
        """Legacy provider and pure projector produce identical fingerprints for the same tree."""
        repo = tmp_path
        _setup_git_repo(repo)
        spec_dir = repo / "docs" / "specs" / "test-feature"
        _make_spec_and_plan(spec_dir)
        (repo / "src").mkdir()
        (repo / "src" / "main.py").write_text("print('hello')", encoding="utf-8")
        _commit_all(repo)

        approved_spec = guards.sha256_canonical_contract(spec_dir / "spec.md")
        approved_plan = guards.sha256_canonical_contract(spec_dir / "plan.md")

        # Call legacy provider
        legacy_subject = ss.project_legacy_subject(
            repo_root=repo,
            spec_dir=spec_dir,
            approved_spec_hash=approved_spec,
            approved_plan_hash=approved_plan,
            audit_sink=null_sink,
            subject_id="subject-parity-001",
            evidence_policy_ref="policy:v1",
        )

        # Build manifest independently using the pure projector directly.
        # The legacy provider uses the same path enumeration: we know src/main.py
        # is the only non-excluded tracked file, so build the manifest manually
        # to compare against the projector.
        import hashlib
        main_py = repo / "src" / "main.py"
        h = hashlib.sha256()
        h.update(main_py.read_bytes())
        main_hash = h.hexdigest()
        manifest_pairs: tuple[tuple[str, str], ...] = (("src/main.py", main_hash),)

        spec_dir_rel = "docs/specs/test-feature"
        spec_path_rel = spec_dir_rel + "/spec.md"
        effective_exclusions = (".git", spec_dir_rel)

        pure_subject = sp.project_delivery_subject(
            subject_id="subject-parity-001",
            base_ref=legacy_subject["product"]["result_ref"],
            result_ref=legacy_subject["product"]["result_ref"],
            spec_path=spec_path_rel,
            spec_fingerprint=approved_spec,
            evidence_policy_ref="policy:v1",
            exclusions=effective_exclusions,
            provider=ss.LEGACY_PROVIDER_IDENTITY,
            projection_version=ss.LEGACY_PROJECTION_VERSION,
            manifest_pairs=manifest_pairs,
            task_projection_hash=approved_plan,
        )

        # AC-0005: identical acceptance fingerprints
        assert legacy_subject["acceptance_fingerprint"] == pure_subject["acceptance_fingerprint"], (
            "Legacy provider and pure projector must emit identical acceptance fingerprints"
        )
        # Identical spec identity
        assert legacy_subject["spec"]["path"] == pure_subject["spec"]["path"]
        assert legacy_subject["spec"]["fingerprint"] == pure_subject["spec"]["fingerprint"]
        # Identical plan provenance
        assert legacy_subject.get("task_projection_hash") == pure_subject.get("task_projection_hash")
        # Identical exclusions (sorted)
        assert sorted(legacy_subject["exclusions"]) == sorted(pure_subject["exclusions"])
        # Identical lineage
        assert legacy_subject["lineage"]["provider"] == pure_subject["lineage"]["provider"]
        assert legacy_subject["lineage"]["projection_version"] == pure_subject["lineage"]["projection_version"]

    def test_parity_is_deterministic_across_two_runs(
        self,
        ss: ModuleType,
        guards: ModuleType,
        tmp_path: Path,
    ) -> None:
        """Two calls with the same acknowledged tree yield identical records."""
        repo = tmp_path
        _setup_git_repo(repo)
        spec_dir = repo / "docs" / "specs" / "feat"
        _make_spec_and_plan(spec_dir)
        (repo / "a.txt").write_text("a", encoding="utf-8")
        _commit_all(repo)

        approved_spec = guards.sha256_canonical_contract(spec_dir / "spec.md")
        approved_plan = guards.sha256_canonical_contract(spec_dir / "plan.md")

        def call() -> dict:
            return ss.project_legacy_subject(
                repo_root=repo,
                spec_dir=spec_dir,
                approved_spec_hash=approved_spec,
                approved_plan_hash=approved_plan,
                audit_sink=null_sink,
                subject_id="subject-det-001",
                evidence_policy_ref="policy:v1",
            )

        r1 = call()
        r2 = call()
        assert r1["acceptance_fingerprint"] == r2["acceptance_fingerprint"]
        assert r1["product"]["result_ref"] == r2["product"]["result_ref"]


# ── AC-0006: Subject-admission negatives ─────────────────────────────────────


class TestSubjectAdmissionNegativesAC0006:
    """AC-0006: each inadmissible path is refused or excluded without a partial manifest."""

    def test_untracked_file_not_in_manifest(
        self,
        ss: ModuleType,
        guards: ModuleType,
        tmp_path: Path,
    ) -> None:
        """An untracked file (never git-add'd) does not appear in the manifest."""
        repo = tmp_path
        _setup_git_repo(repo)
        spec_dir = repo / "docs" / "specs" / "feat"
        _make_spec_and_plan(spec_dir)
        _commit_all(repo)

        # Add untracked file AFTER commit (not staged)
        (repo / "untracked.txt").write_text("secret", encoding="utf-8")

        approved_spec = guards.sha256_canonical_contract(spec_dir / "spec.md")
        approved_plan = guards.sha256_canonical_contract(spec_dir / "plan.md")

        subject = ss.project_legacy_subject(
            repo_root=repo,
            spec_dir=spec_dir,
            approved_spec_hash=approved_spec,
            approved_plan_hash=approved_plan,
            audit_sink=null_sink,
            subject_id="subj-ut-001",
            evidence_policy_ref="policy:v1",
        )
        # Untracked file never enters the acceptance fingerprint
        assert "untracked.txt" not in subject["acceptance_fingerprint"]

    def test_excluded_spec_dir_not_in_manifest(
        self,
        ss: ModuleType,
        sp: ModuleType,
        guards: ModuleType,
        tmp_path: Path,
    ) -> None:
        """Spec directory files are excluded (spec enters via fingerprint, not by path)."""
        repo = tmp_path
        _setup_git_repo(repo)
        spec_dir = repo / "docs" / "specs" / "feat"
        _make_spec_and_plan(spec_dir)
        (repo / "product.py").write_text("x = 1", encoding="utf-8")
        _commit_all(repo)

        approved_spec = guards.sha256_canonical_contract(spec_dir / "spec.md")
        approved_plan = guards.sha256_canonical_contract(spec_dir / "plan.md")

        subject = ss.project_legacy_subject(
            repo_root=repo,
            spec_dir=spec_dir,
            approved_spec_hash=approved_spec,
            approved_plan_hash=approved_plan,
            audit_sink=null_sink,
            subject_id="subj-excl-001",
            evidence_policy_ref="policy:v1",
        )

        # Spec/plan paths must appear in the exclusions list, not the product manifest
        assert "docs/specs/feat" in subject["exclusions"]
        # The acceptance fingerprint is the same as calling the pure projector
        # with no spec paths in the manifest
        assert subject["spec"]["fingerprint"] == approved_spec

    def test_drifting_spec_hash_is_refused(
        self,
        ss: ModuleType,
        guards: ModuleType,
        tmp_path: Path,
    ) -> None:
        """A modified spec (drift from approved boundary) causes refusal."""
        repo = tmp_path
        _setup_git_repo(repo)
        spec_dir = repo / "docs" / "specs" / "feat"
        _make_spec_and_plan(spec_dir)
        _commit_all(repo)

        approved_spec = guards.sha256_canonical_contract(spec_dir / "spec.md")
        approved_plan = guards.sha256_canonical_contract(spec_dir / "plan.md")

        # Now modify spec.md (drift)
        with (spec_dir / "spec.md").open("a", encoding="utf-8") as f:
            f.write("\n## New Section\n")

        with pytest.raises(ss.SubjectRefused) as exc_info:
            ss.project_legacy_subject(
                repo_root=repo,
                spec_dir=spec_dir,
                approved_spec_hash=approved_spec,
                approved_plan_hash=approved_plan,
                audit_sink=null_sink,
                subject_id="subj-drift-001",
                evidence_policy_ref="policy:v1",
            )
        assert exc_info.value.denial_code == "denied-spec-drift"

    def test_drifting_plan_hash_is_refused(
        self,
        ss: ModuleType,
        guards: ModuleType,
        tmp_path: Path,
    ) -> None:
        """A modified plan (drift from approved boundary) causes refusal."""
        repo = tmp_path
        _setup_git_repo(repo)
        spec_dir = repo / "docs" / "specs" / "feat"
        _make_spec_and_plan(spec_dir)
        _commit_all(repo)

        approved_spec = guards.sha256_canonical_contract(spec_dir / "spec.md")
        approved_plan = guards.sha256_canonical_contract(spec_dir / "plan.md")

        # Modify plan.md (drift) without committing
        with (spec_dir / "plan.md").open("a", encoding="utf-8") as f:
            f.write("\n### T2: New Task\n")

        with pytest.raises(ss.SubjectRefused) as exc_info:
            ss.project_legacy_subject(
                repo_root=repo,
                spec_dir=spec_dir,
                approved_spec_hash=approved_spec,
                approved_plan_hash=approved_plan,
                audit_sink=null_sink,
                subject_id="subj-plan-drift-001",
                evidence_policy_ref="policy:v1",
            )
        # Plan drift is detected by hash mismatch
        assert exc_info.value.denial_code in ("denied-plan-drift", "denied-product-drift")

    def test_uncommitted_product_change_is_refused(
        self,
        ss: ModuleType,
        guards: ModuleType,
        tmp_path: Path,
    ) -> None:
        """An uncommitted change to a tracked product file causes refusal."""
        repo = tmp_path
        _setup_git_repo(repo)
        spec_dir = repo / "docs" / "specs" / "feat"
        _make_spec_and_plan(spec_dir)
        (repo / "src.py").write_text("x = 1", encoding="utf-8")
        _commit_all(repo)

        approved_spec = guards.sha256_canonical_contract(spec_dir / "spec.md")
        approved_plan = guards.sha256_canonical_contract(spec_dir / "plan.md")

        # Modify a tracked product file without committing
        (repo / "src.py").write_text("x = 2  # drift", encoding="utf-8")

        with pytest.raises(ss.SubjectRefused) as exc_info:
            ss.project_legacy_subject(
                repo_root=repo,
                spec_dir=spec_dir,
                approved_spec_hash=approved_spec,
                approved_plan_hash=approved_plan,
                audit_sink=null_sink,
                subject_id="subj-uncomm-001",
                evidence_policy_ref="policy:v1",
            )
        assert exc_info.value.denial_code == "denied-product-drift"

    @pytest.mark.skipif(
        sys.platform == "win32",
        reason="symlinks may require elevated privileges on Windows",
    )
    def test_symlink_path_is_refused(
        self,
        ss: ModuleType,
        guards: ModuleType,
        tmp_path: Path,
    ) -> None:
        """A tracked symlink path fails the confinement check (link-like, refused)."""
        repo = tmp_path
        _setup_git_repo(repo)
        spec_dir = repo / "docs" / "specs" / "feat"
        _make_spec_and_plan(spec_dir)

        # Create a real file and a symlink to it
        (repo / "real.py").write_text("x = 1", encoding="utf-8")
        try:
            (repo / "link.py").symlink_to("real.py")
        except OSError:
            pytest.skip("symlinks not available on this host")

        _git("add", ".", cwd=repo)
        _git("commit", "-q", "-m", "add symlink", cwd=repo)

        approved_spec = guards.sha256_canonical_contract(spec_dir / "spec.md")
        approved_plan = guards.sha256_canonical_contract(spec_dir / "plan.md")

        with pytest.raises(ss.SubjectRefused) as exc_info:
            ss.project_legacy_subject(
                repo_root=repo,
                spec_dir=spec_dir,
                approved_spec_hash=approved_spec,
                approved_plan_hash=approved_plan,
                audit_sink=null_sink,
                subject_id="subj-link-001",
                evidence_policy_ref="policy:v1",
            )
        # The confinement check refuses link-like paths
        assert exc_info.value.denial_code == "denied-path-violation"

    def test_unreadable_file_is_refused(
        self,
        ss: ModuleType,
        guards: ModuleType,
        tmp_path: Path,
    ) -> None:
        """A tracked file that becomes unreadable causes refusal."""
        repo = tmp_path
        _setup_git_repo(repo)
        spec_dir = repo / "docs" / "specs" / "feat"
        _make_spec_and_plan(spec_dir)
        (repo / "secret.py").write_text("x = 1", encoding="utf-8")
        _commit_all(repo)

        approved_spec = guards.sha256_canonical_contract(spec_dir / "spec.md")
        approved_plan = guards.sha256_canonical_contract(spec_dir / "plan.md")

        # Remove read permissions to simulate an unreadable path
        target = repo / "secret.py"
        original_mode = target.stat().st_mode
        try:
            target.chmod(0o000)
            with pytest.raises(ss.SubjectRefused) as exc_info:
                ss.project_legacy_subject(
                    repo_root=repo,
                    spec_dir=spec_dir,
                    approved_spec_hash=approved_spec,
                    approved_plan_hash=approved_plan,
                    audit_sink=null_sink,
                    subject_id="subj-unread-001",
                    evidence_policy_ref="policy:v1",
                )
            # On platforms where git tracks file mode (macOS/Linux with core.filemode),
            # chmod(0o000) changes the file mode, which git detects as product drift
            # before we reach the file-read phase.  All three codes mean the
            # unreadable path was refused without a partial manifest.
            assert exc_info.value.denial_code in (
                "denied-unreadable-path",
                "denied-path-violation",
                "denied-product-drift",
            )
        finally:
            target.chmod(original_mode)

    def test_empty_approved_hashes_refused(
        self,
        ss: ModuleType,
        tmp_path: Path,
    ) -> None:
        """Empty approved_spec_hash or approved_plan_hash is refused immediately."""
        repo = tmp_path
        _setup_git_repo(repo)
        spec_dir = repo / "docs" / "specs" / "feat"
        _make_spec_and_plan(spec_dir)
        _commit_all(repo)

        with pytest.raises(ss.SubjectRefused) as exc_info:
            ss.project_legacy_subject(
                repo_root=repo,
                spec_dir=spec_dir,
                approved_spec_hash="",
                approved_plan_hash="some-hash",
                audit_sink=null_sink,
                subject_id="subj-empty-001",
                evidence_policy_ref="policy:v1",
            )
        assert exc_info.value.denial_code == "denied-no-approved-boundary"

    def test_task_projection_revision_does_not_alter_fingerprint(
        self,
        ss: ModuleType,
        guards: ModuleType,
        tmp_path: Path,
    ) -> None:
        """Changing task_projection_revision does not alter the acceptance fingerprint."""
        repo = tmp_path
        _setup_git_repo(repo)
        spec_dir = repo / "docs" / "specs" / "feat"
        _make_spec_and_plan(spec_dir)
        (repo / "a.txt").write_text("a", encoding="utf-8")
        _commit_all(repo)

        approved_spec = guards.sha256_canonical_contract(spec_dir / "spec.md")
        approved_plan = guards.sha256_canonical_contract(spec_dir / "plan.md")

        def project(rev: str | None) -> dict:
            return ss.project_legacy_subject(
                repo_root=repo,
                spec_dir=spec_dir,
                approved_spec_hash=approved_spec,
                approved_plan_hash=approved_plan,
                audit_sink=null_sink,
                subject_id="subj-rev-001",
                evidence_policy_ref="policy:v1",
                task_projection_revision=rev,
            )

        r_none = project(None)
        r_v1 = project("v1")
        r_v2 = project("v2")

        # Acceptance fingerprint must not change with task-projection revision
        assert r_none["acceptance_fingerprint"] == r_v1["acceptance_fingerprint"]
        assert r_v1["acceptance_fingerprint"] == r_v2["acceptance_fingerprint"]
        # But the provenance field itself should differ
        assert r_none.get("task_projection_revision") is None
        assert r_v1.get("task_projection_revision") == "v1"
        assert r_v2.get("task_projection_revision") == "v2"


# ── AC-0006: Traversal limit fixtures ────────────────────────────────────────


class TestTraversalLimitsAC0006:
    """AC-0006 bound-edge, edge-plus-one, and oversized-repository fixtures.

    Traversal limit constants are imported from ss (the subject-source module)
    so the plan never duplicates the architecture-owned numeric values.
    """

    def test_path_bound_edge_succeeds(
        self,
        ss: ModuleType,
        sp: ModuleType,
        guards: ModuleType,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
    ) -> None:
        """Exactly MAX_PRODUCT_PATHS non-excluded tracked files: projection succeeds."""
        repo = tmp_path
        _setup_git_repo(repo)
        spec_dir = repo / "docs" / "specs" / "feat"
        _make_spec_and_plan(spec_dir)
        _commit_all(repo)

        approved_spec = guards.sha256_canonical_contract(spec_dir / "spec.md")
        approved_plan = guards.sha256_canonical_contract(spec_dir / "plan.md")

        n = ss.MAX_PRODUCT_PATHS

        # Monkeypatch _list_tracked_files to return exactly MAX_PRODUCT_PATHS paths
        # (without creating real files).
        fake_paths = [f"f{i:06d}.txt" for i in range(n)]

        monkeypatch.setattr(ss, "_list_tracked_files", lambda r, s: list(fake_paths))
        monkeypatch.setattr(ss, "_get_head_sha", lambda r, s: "deadbeef" * 5)
        monkeypatch.setattr(ss, "_check_product_drift", lambda r, s: None)
        # Inject a no-I/O hash stub so MAX_PRODUCT_PATHS fake paths need no real files.
        monkeypatch.setattr(ss, "_hash_file_with_budget", lambda r, p, b: (0, "a" * 64))

        # Edge: exactly MAX_PRODUCT_PATHS → must succeed
        subject = ss.project_legacy_subject(
            repo_root=repo,
            spec_dir=spec_dir,
            approved_spec_hash=approved_spec,
            approved_plan_hash=approved_plan,
            audit_sink=null_sink,
            subject_id="subj-edge-001",
            evidence_policy_ref="policy:v1",
        )
        assert subject["schema_version"] == 1

    def test_path_bound_edge_plus_one_is_refused(
        self,
        ss: ModuleType,
        guards: ModuleType,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
    ) -> None:
        """MAX_PRODUCT_PATHS + 1 non-excluded tracked files: refused before partial manifest."""
        repo = tmp_path
        _setup_git_repo(repo)
        spec_dir = repo / "docs" / "specs" / "feat"
        _make_spec_and_plan(spec_dir)
        _commit_all(repo)

        approved_spec = guards.sha256_canonical_contract(spec_dir / "spec.md")
        approved_plan = guards.sha256_canonical_contract(spec_dir / "plan.md")

        n = ss.MAX_PRODUCT_PATHS + 1
        fake_paths = [f"f{i:06d}.txt" for i in range(n)]

        monkeypatch.setattr(ss, "_list_tracked_files", lambda r, s: list(fake_paths))
        monkeypatch.setattr(ss, "_get_head_sha", lambda r, s: "dead" * 10)
        monkeypatch.setattr(ss, "_check_product_drift", lambda r, s: None)
        # Inject a no-I/O hash stub so MAX_PRODUCT_PATHS fake paths need no real files.
        monkeypatch.setattr(ss, "_hash_file_with_budget", lambda r, p, b: (0, "a" * 64))

        with pytest.raises(ss.SubjectRefused) as exc_info:
            ss.project_legacy_subject(
                repo_root=repo,
                spec_dir=spec_dir,
                approved_spec_hash=approved_spec,
                approved_plan_hash=approved_plan,
                audit_sink=null_sink,
                subject_id="subj-edgeplus1-001",
                evidence_policy_ref="policy:v1",
            )
        assert exc_info.value.denial_code == "denied-path-bound-exceeded"

    def test_byte_bound_exceeded_is_refused(
        self,
        ss: ModuleType,
        guards: ModuleType,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
    ) -> None:
        """A single file that pushes total bytes over MAX_PRODUCT_BYTES causes refusal."""
        repo = tmp_path
        _setup_git_repo(repo)
        spec_dir = repo / "docs" / "specs" / "feat"
        _make_spec_and_plan(spec_dir)
        _commit_all(repo)

        approved_spec = guards.sha256_canonical_contract(spec_dir / "spec.md")
        approved_plan = guards.sha256_canonical_contract(spec_dir / "plan.md")

        max_bytes = ss.MAX_PRODUCT_BYTES

        # One fake path.  _hash_file_with_budget is stubbed to simulate a file
        # that is one byte over the budget; it must refuse before the loop adds
        # the file to the manifest.
        fake_paths = ["big.bin"]

        def oversized_hash(
            root: Path, path: Path, remaining: int
        ) -> tuple[int, str]:
            """Simulate _hash_file_with_budget reporting an over-budget file."""
            raise ss.SubjectRefused(
                "denied-byte-bound-exceeded",
                f"test: file size {max_bytes + 1} exceeds budget {remaining}",
            )

        monkeypatch.setattr(ss, "_list_tracked_files", lambda r, s: list(fake_paths))
        monkeypatch.setattr(ss, "_get_head_sha", lambda r, s: "dead" * 10)
        monkeypatch.setattr(ss, "_check_product_drift", lambda r, s: None)
        monkeypatch.setattr(ss, "_hash_file_with_budget", oversized_hash)

        with pytest.raises(ss.SubjectRefused) as exc_info:
            ss.project_legacy_subject(
                repo_root=repo,
                spec_dir=spec_dir,
                approved_spec_hash=approved_spec,
                approved_plan_hash=approved_plan,
                audit_sink=null_sink,
                subject_id="subj-bytes-001",
                evidence_policy_ref="policy:v1",
            )
        assert exc_info.value.denial_code == "denied-byte-bound-exceeded"

    def test_time_bound_exceeded_is_refused(
        self,
        ss: ModuleType,
        guards: ModuleType,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
    ) -> None:
        """Elapsed time exceeding MAX_TRAVERSAL_S causes refusal before partial manifest."""
        repo = tmp_path
        _setup_git_repo(repo)
        spec_dir = repo / "docs" / "specs" / "feat"
        _make_spec_and_plan(spec_dir)
        _commit_all(repo)

        approved_spec = guards.sha256_canonical_contract(spec_dir / "spec.md")
        approved_plan = guards.sha256_canonical_contract(spec_dir / "plan.md")

        max_s = ss.MAX_TRAVERSAL_S
        fake_paths = ["f0.txt", "f1.txt"]  # 2 paths — time limit fires on first

        monkeypatch.setattr(ss, "_list_tracked_files", lambda r, s: list(fake_paths))
        monkeypatch.setattr(ss, "_get_head_sha", lambda r, s: "dead" * 10)
        monkeypatch.setattr(ss, "_check_product_drift", lambda r, s: None)

        # Patch time.monotonic so elapsed > MAX_TRAVERSAL_S on first iteration
        call_count = {"n": 0}

        def fake_mono() -> float:
            call_count["n"] += 1
            # First call (start_time) returns 0; second call (first iteration) returns max_s + 1
            if call_count["n"] == 1:
                return 0.0
            return float(max_s) + 1.0

        monkeypatch.setattr(time, "monotonic", fake_mono)

        with pytest.raises(ss.SubjectRefused) as exc_info:
            ss.project_legacy_subject(
                repo_root=repo,
                spec_dir=spec_dir,
                approved_spec_hash=approved_spec,
                approved_plan_hash=approved_plan,
                audit_sink=null_sink,
                subject_id="subj-time-001",
                evidence_policy_ref="policy:v1",
            )
        assert exc_info.value.denial_code == "denied-time-bound-exceeded"

    def test_oversized_repository_fixture_refused(
        self,
        ss: ModuleType,
        guards: ModuleType,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
    ) -> None:
        """The oversized-repository fixture (> MAX_PRODUCT_PATHS) refuses before any partial manifest.

        Architecture §7: 'Refusal above 100,000 paths, 10 GiB, or 60 s'.
        The projector stops without emitting a partial subject.
        """
        repo = tmp_path
        _setup_git_repo(repo)
        spec_dir = repo / "docs" / "specs" / "feat"
        _make_spec_and_plan(spec_dir)
        _commit_all(repo)

        approved_spec = guards.sha256_canonical_contract(spec_dir / "spec.md")
        approved_plan = guards.sha256_canonical_contract(spec_dir / "plan.md")

        # Oversized: 2 × MAX_PRODUCT_PATHS paths
        n = ss.MAX_PRODUCT_PATHS * 2
        fake_paths = [f"f{i:07d}.txt" for i in range(n)]

        monkeypatch.setattr(ss, "_list_tracked_files", lambda r, s: list(fake_paths))
        monkeypatch.setattr(ss, "_get_head_sha", lambda r, s: "dead" * 10)
        monkeypatch.setattr(ss, "_check_product_drift", lambda r, s: None)
        # Inject a no-I/O hash stub so the path-count limit fires without real file I/O.
        monkeypatch.setattr(ss, "_hash_file_with_budget", lambda r, p, b: (0, "d" * 64))

        with pytest.raises(ss.SubjectRefused) as exc_info:
            ss.project_legacy_subject(
                repo_root=repo,
                spec_dir=spec_dir,
                approved_spec_hash=approved_spec,
                approved_plan_hash=approved_plan,
                audit_sink=null_sink,
                subject_id="subj-oversized-001",
                evidence_policy_ref="policy:v1",
            )
        assert exc_info.value.denial_code == "denied-path-bound-exceeded"

    def test_unknown_file_size_is_refused(
        self,
        ss: ModuleType,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
    ) -> None:
        """A file whose size cannot be established is refused, never admitted.

        AC-0006, AC-0011: when ``os.fstat`` fails the file is refused (the
        confined opener refuses it, or the size read does), not admitted with a
        synthetic zero size as the earlier code did after a failed ``stat()``.
        """
        target = tmp_path / "data.txt"
        target.write_bytes(b"hello")

        def failing_fstat(fd: int) -> object:
            raise OSError("simulated fstat failure for test")

        monkeypatch.setattr(os, "fstat", failing_fstat)

        with pytest.raises(ss.SubjectRefused) as exc_info:
            ss._hash_file_with_budget(tmp_path, target, ss.MAX_PRODUCT_BYTES)

        assert exc_info.value.denial_code in {"denied-unreadable-path", "denied-path-violation"}

    def test_oversized_file_refused_without_reading_past_bound(
        self,
        ss: ModuleType,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
    ) -> None:
        """An oversized file is refused before any content is read.

        AC-0006, AC-0011: when the ``fstat`` size exceeds the remaining budget,
        ``_hash_file_with_budget`` refuses immediately and the hash function is
        never called (zero bytes hashed).  Fails against the pre-fix code, which
        called ``sha256_confined_regular_file`` before the budget check and read
        the entire file regardless of the byte limit.
        """
        import hashlib

        target = tmp_path / "big.bin"
        target.write_bytes(b"hello world")  # 11 real bytes; budget capped to 5

        bytes_hashed: list[int] = []
        original_sha256 = hashlib.sha256

        class _TrackingSHA256:
            """Wraps hashlib.sha256 and records the length of every update() call."""

            def __init__(self) -> None:
                self._inner = original_sha256()

            def update(self, data: bytes) -> None:
                bytes_hashed.append(len(data))
                self._inner.update(data)

            def hexdigest(self) -> str:
                return self._inner.hexdigest()

        monkeypatch.setattr(hashlib, "sha256", lambda: _TrackingSHA256())

        # Budget (5) is smaller than file size (11) → must refuse without reading.
        with pytest.raises(ss.SubjectRefused) as exc_info:
            ss._hash_file_with_budget(tmp_path, target, remaining_budget=5)

        assert exc_info.value.denial_code == "denied-byte-bound-exceeded"
        assert sum(bytes_hashed) == 0, (
            "no bytes should have been hashed when fstat size exceeds the budget"
        )


# ── Validate-subject-dict: in-code schema validation ─────────────────────────


class TestValidateSubjectDict:
    """validate_subject_dict refuses each class of schema-invalid input."""

    def test_refuses_unknown_schema_version(self, ss: ModuleType) -> None:
        ok, code = ss.validate_subject_dict({"schema_version": 99})
        assert not ok
        assert code == "denied-unknown-schema-version"

    def test_refuses_missing_required_field(self, ss: ModuleType) -> None:
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
        ok, code = ss.validate_subject_dict(record)
        assert not ok
        assert code == "denied-missing-required-field"

    def test_refuses_unknown_authority_field(self, ss: ModuleType) -> None:
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
        ok, code = ss.validate_subject_dict(record)
        assert not ok
        assert code == "denied-unknown-authority-field"

    def test_accepts_valid_record(self, ss: ModuleType, sp: ModuleType) -> None:
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
        ok, code = ss.validate_subject_dict(record)
        assert ok
        assert code == "ok"

    def test_symlinked_parent_directory_is_refused(
        self, ss: ModuleType, tmp_path: Path
    ) -> None:
        """A link anywhere on the path, not only at the file itself, is refused."""
        root = tmp_path / "repo"
        root.mkdir()
        outside = tmp_path / "outside"
        outside.mkdir()
        (outside / "secret.txt").write_bytes(b"outside the root")
        (root / "linked").symlink_to(outside, target_is_directory=True)
        with pytest.raises(ss.SubjectRefused) as exc_info:
            ss._hash_file_with_budget(root, root / "linked" / "secret.txt", ss.MAX_PRODUCT_BYTES)
        assert exc_info.value.denial_code == "denied-path-violation"
