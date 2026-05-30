"""Integration tests for issue #190 Finding 2: first-install-over-existing files.

A brownfield install over hand-authored files at *projection* paths must drop
`*.upstream.<ext>` companions (Step 9), not be misclassified as an interrupted-
install orphan and refused/deleted. Genuine stale crumbs — files under a
shipped-primitive directory that the current projection does NOT include — stay
guarded by the (reworded) orphan refusal.

Covers AC3 (edited collision → companion), AC4 (identical → clean), AC5 (non-
projection crumb → orphan guard fires; `--force` removes), AC6 (message wording).
"""

from __future__ import annotations

import argparse
import contextlib
import io
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
WORK_LOOP_SKILL = ".claude/skills/work-loop/SKILL.md"


def _install_core(target: Path, *, force: bool = False) -> tuple[int, str, str]:
    from agentbundle.commands.install import run as install_run

    args = argparse.Namespace(
        pack="core",
        catalogue=str(REPO_ROOT),
        output=str(target),
        scope="repo",
        emit_install_routes=False,
        force=force,
    )
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        rc = install_run(args)
    return rc, out.getvalue(), err.getvalue()


def _reset_inband_cache() -> None:
    from agentbundle.commands import install as install_mod

    install_mod._clear_inband_detection_seen()


def test_first_install_over_edited_primitive_drops_companion(tmp_path):
    """AC3: an edited file at a projection path → companion, no refusal."""
    target = tmp_path / "repo"
    (target / ".claude" / "skills" / "work-loop").mkdir(parents=True)
    edited = b"# my hand-authored work-loop, do not delete\n"
    (target / WORK_LOOP_SKILL).write_bytes(edited)

    rc, _out, err = _install_core(target)
    assert rc == 0, f"first install over an edited primitive must not refuse: {err}"
    assert (target / WORK_LOOP_SKILL).read_bytes() == edited, (
        "the adopter's hand-authored skill must be left byte-unchanged"
    )
    assert (target / ".claude" / "skills" / "work-loop" / "SKILL.upstream.md").exists(), (
        "the collision must drop a SKILL.upstream.md companion, not delete the file"
    )


def test_first_install_over_identical_primitive_is_clean(tmp_path):
    """AC4: a byte-identical file at a projection path (no state) → no companion."""
    target = tmp_path / "repo"
    target.mkdir()
    rc, _out, err = _install_core(target)
    assert rc == 0, err
    # Simulate a brownfield repo whose files already match the projection but
    # carry no state: drop state, clear the per-process detection cache.
    (target / ".agentbundle-state.toml").unlink()
    _reset_inband_cache()

    rc, _out, err = _install_core(target)
    assert rc == 0, err
    assert not (target / ".claude" / "skills" / "work-loop" / "SKILL.upstream.md").exists(), (
        "an identical file must be a clean Tier-1 no-op, not a companion"
    )


def test_non_projection_crumb_still_refused(tmp_path):
    """AC5/AC6: a stale crumb not in the projection still triggers the (reworded) guard."""
    target = tmp_path / "repo"
    (target / ".claude" / "skills" / "work-loop").mkdir(parents=True)
    # Matches the `work-loop` primitive-name heuristic but is NOT a projected file.
    crumb = target / ".claude" / "skills" / "work-loop" / "STALE-EXTRA.md"
    crumb.write_bytes(b"leftover\n")

    rc, _out, err = _install_core(target)
    assert rc == 1, "a non-projection crumb must still be refused without --force"
    assert crumb.exists(), "refusal must not delete anything"
    assert "prior install interrupted" not in err, (
        "AC6: the message must not assert 'prior install interrupted' as fact"
    )
    assert "your own files" in err, "AC6: the message must acknowledge adopter-authored files"


def test_non_projection_crumb_removed_with_force(tmp_path):
    """AC5: `--force` removes the genuine non-projection crumb and proceeds."""
    target = tmp_path / "repo"
    (target / ".claude" / "skills" / "work-loop").mkdir(parents=True)
    crumb = target / ".claude" / "skills" / "work-loop" / "STALE-EXTRA.md"
    crumb.write_bytes(b"leftover\n")

    rc, _out, err = _install_core(target, force=True)
    assert rc == 0, f"--force must clean the crumb and reinstall: {err}"
    assert not crumb.exists(), "--force must remove the genuine orphan crumb"
