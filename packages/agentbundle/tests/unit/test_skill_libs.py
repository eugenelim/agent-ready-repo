"""Tests for the skill-libs build primitive (ADR-0074).

Projects a stdlib-only package module into a skill's scripts/ dir so one
authored source serves both the package and the skill. The drift gate is what
makes the projected copy safe to trust: a hand-edit becomes a build failure
rather than a silent fork.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from agentbundle.build import skill_libs


def _fake_repo(tmp_path: Path, *, body: str = "x = 1\n") -> tuple[Path, Path, Path]:
    """A minimal repo laid out the way the real one is.

    Returns (packs_dir, source, target) for the single declared row.
    """
    source_rel, target_rel = skill_libs.PROJECTIONS[0]
    source = tmp_path / source_rel
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_text(body, encoding="utf-8")
    packs_dir = tmp_path / "packs"
    packs_dir.mkdir(exist_ok=True)
    return packs_dir, source, packs_dir / target_rel


class TestProjection:
    def test_writes_target_byte_identically(self, tmp_path: Path) -> None:
        packs_dir, source, target = _fake_repo(tmp_path, body="# lock\nY = 2\n")
        skill_libs.apply_projection(packs_dir)
        assert target.read_bytes() == source.read_bytes()

    def test_creates_missing_parent_dirs(self, tmp_path: Path) -> None:
        packs_dir, _source, target = _fake_repo(tmp_path)
        assert not target.parent.exists()
        skill_libs.apply_projection(packs_dir)
        assert target.is_file()

    def test_is_idempotent(self, tmp_path: Path) -> None:
        packs_dir, _source, target = _fake_repo(tmp_path)
        skill_libs.apply_projection(packs_dir)
        first = target.read_bytes()
        skill_libs.apply_projection(packs_dir)
        assert target.read_bytes() == first
        assert skill_libs.check_drift(packs_dir) == []

    def test_overwrites_a_hand_edited_target(self, tmp_path: Path) -> None:
        """Edit the source, never the projection — build-self restores it."""
        packs_dir, source, target = _fake_repo(tmp_path)
        skill_libs.apply_projection(packs_dir)
        target.write_text("# hand-edited\n", encoding="utf-8")
        skill_libs.apply_projection(packs_dir)
        assert target.read_bytes() == source.read_bytes()

    def test_no_op_outside_the_monorepo(self, tmp_path: Path) -> None:
        """Package source absent: nothing to project, nothing to compare.

        The target IS PRESENT here, which is the whole point: outside the
        monorepo the committed copy ships with the pack while the package tree
        is absent. An earlier version of this case left the target out, so
        `not target.exists()` short-circuited the orphan branch and the case
        passed vacuously — while every real fixture packs dir was reported as
        orphaned, breaking three build-check integration tests.
        """
        _source_rel, target_rel = skill_libs.PROJECTIONS[0]
        packs_dir = tmp_path / "packs"
        target = packs_dir / target_rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("# shipped with the pack\n", encoding="utf-8")

        assert skill_libs.compute_projections(packs_dir) == []
        skill_libs.apply_projection(packs_dir)  # must not raise
        assert skill_libs.check_drift(packs_dir) == [], (
            "a committed target with no package tree is the non-monorepo shape, "
            "not drift"
        )
        assert target.read_text(encoding="utf-8") == "# shipped with the pack\n"


class TestDriftGate:
    def test_clean_when_projected(self, tmp_path: Path) -> None:
        packs_dir, _source, _target = _fake_repo(tmp_path)
        skill_libs.apply_projection(packs_dir)
        assert skill_libs.check_drift(packs_dir) == []

    def test_reports_missing(self, tmp_path: Path) -> None:
        packs_dir, _source, target = _fake_repo(tmp_path)
        drifts = skill_libs.check_drift(packs_dir)
        assert len(drifts) == 1
        assert "[skill-libs] missing" in drifts[0]
        assert target.name in drifts[0]
        assert "make build-self" in drifts[0]

    def test_reports_modified(self, tmp_path: Path) -> None:
        packs_dir, _source, target = _fake_repo(tmp_path)
        skill_libs.apply_projection(packs_dir)
        target.write_text("# hand-edited\n", encoding="utf-8")
        drifts = skill_libs.check_drift(packs_dir)
        assert len(drifts) == 1
        assert "[skill-libs] modified" in drifts[0]
        # The message must point the reader at the source, not the copy.
        assert "edit the source, not the projection" in drifts[0]
        assert "make build-self" in drifts[0]

    def test_reports_orphaned_when_source_retired(self, tmp_path: Path) -> None:
        """A committed target whose source row is gone is drift, not silence."""
        packs_dir, source, target = _fake_repo(tmp_path)
        skill_libs.apply_projection(packs_dir)
        source.unlink()
        drifts = skill_libs.check_drift(packs_dir)
        assert len(drifts) == 1
        assert "[skill-libs] orphaned" in drifts[0]
        assert target.name in drifts[0]

    def test_messages_are_repo_relative(self, tmp_path: Path) -> None:
        packs_dir, _source, _target = _fake_repo(tmp_path)
        drifts = skill_libs.check_drift(packs_dir)
        assert str(tmp_path) not in drifts[0], "leaked an absolute path"


class TestDeclaredRows:
    def test_the_state_lock_row_is_declared(self) -> None:
        """The row this primitive was introduced for (ADR-0074)."""
        rows = {(s.as_posix(), t.as_posix()) for s, t in skill_libs.PROJECTIONS}
        assert (
            "packages/agentbundle/agentbundle/statelock_core.py",
            "core/.apm/skills/work-loop/scripts/_statelock.py",
        ) in rows

    @pytest.mark.parametrize("source_rel,target_rel", skill_libs.PROJECTIONS)
    def test_every_row_is_a_single_python_file(
        self, source_rel: Path, target_rel: Path
    ) -> None:
        assert source_rel.suffix == ".py"
        assert target_rel.suffix == ".py"

    def test_live_projection_is_current(self) -> None:
        """The real tree's committed copy matches its source.

        This is the gate `make build-check` runs; asserting it here means a
        source edit without `make build-self` fails the package suite too,
        rather than only at build-check time.
        """
        # parents[4], not [3]: [1] is tests/, [2] is agentbundle/, [3] is
        # packages/, [4] is the repo root. Off by one and this case skips
        # itself forever — a silent pass in the gate meant to prevent silent
        # forks, so the repo root is asserted rather than assumed.
        repo_root = Path(__file__).resolve().parents[4]
        packs_dir = repo_root / "packs"
        if not (repo_root / ".git").exists():  # pragma: no cover — sdist/wheel
            pytest.skip("not in the monorepo")
        assert packs_dir.is_dir(), f"{packs_dir} missing — check the parents[] depth"
        assert skill_libs.check_drift(packs_dir) == []
