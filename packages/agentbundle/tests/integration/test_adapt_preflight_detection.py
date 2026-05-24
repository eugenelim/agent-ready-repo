"""Pre-flight detection primitives for adapt-to-project (AC4a rows 17, 18).

The adapt-to-project skill's Pre-flight section delegates dirty-state
and Tier-2 detection to two deterministic primitives:

- Repo-scope dirty-state: `git status --porcelain` against the
  adopter's working tree (skill body line documented; pinned by
  AC1 grep #4 / `test_body_names_dirty_state_command`).
- User-scope Tier-2 / dirty-state: content-hash divergence between
  the current bytes of a tracked file and the SHA-256 recorded in
  `~/.agent-ready/state.toml` (skill body line documented; pinned
  by AC22 grep / `test_body_pre_flight_section_references_user_scope_state`).

These tests exercise the primitives end-to-end against fixtures
seeded with the corresponding state, so a regression to the
primitives' shape (e.g., a Python version that changes hashlib
output, or a git that stops emitting porcelain status for an
uncommitted edit) trips pytest rather than only being caught when
a human follows the SKILL.md body interactively.

What these tests **do** pin:
- `git status --porcelain` returns a non-empty payload naming the
  dirty path when the working tree carries an uncommitted edit
  (row 17 primitive).
- `agentbundle.safety.sha256_bytes(current) != recorded_sha` when
  a tracked file's bytes diverge from the recorded SHA-256
  (row 18 primitive).

What these tests do **not** pin (covered elsewhere):
- That the LLM following SKILL.md's Pre-flight narrates the
  finding correctly — pinned by AC1 grep #4 and AC22 grep tokens
  against the skill body.
- That the LLM halts the session and waits for adopter input —
  not currently mechanically testable; transcript captures
  attempted under AC4b rows 8–16 as preparatory evidence.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from agentbundle.safety import sha256_bytes


FIXTURES = Path(__file__).parent.parent / "fixtures"
BROWNFIELD = FIXTURES / "brownfield-adapt"
USER_HOME = FIXTURES / "brownfield-adapt-user-home"


def _init_git_repo(work: Path) -> None:
    """Init a tmp git repo, commit the brownfield fixture contents.

    Uses fresh `git init` + a single committed snapshot so
    `git status --porcelain` returns empty until we mutate the tree.
    Sets a local user.name / user.email so the commit doesn't fail
    on hosts without a global git identity (CI parity).
    """
    subprocess.run(
        ["git", "init", "--quiet", "--initial-branch=main", str(work)],
        check=True,
    )
    subprocess.run(
        ["git", "-C", str(work), "config", "user.name", "preflight-test"],
        check=True,
    )
    subprocess.run(
        ["git", "-C", str(work), "config", "user.email", "preflight@example.invalid"],
        check=True,
    )
    subprocess.run(
        ["git", "-C", str(work), "add", "-A"],
        check=True,
    )
    subprocess.run(
        ["git", "-C", str(work), "commit", "--quiet", "-m", "seed"],
        check=True,
    )


def _porcelain(work: Path) -> str:
    """Run `git status --porcelain` against `work`; return stdout text."""
    result = subprocess.run(
        ["git", "-C", str(work), "status", "--porcelain"],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout


def test_repo_scope_dirty_state_porcelain_detects_uncommitted_edit(tmp_path: Path):
    """Row 17 primitive: `git status --porcelain` flags an uncommitted
    edit to a Tier-1 file, returning a payload naming the dirty path.

    Mirrors the skill's repo-scope Pre-flight step:
    > Repo scope: run `git status --porcelain`. List every dirty
    > path under a `Repo scope:` sub-section and stop and wait …

    If this primitive regresses, the skill's pre-flight would never
    see the dirty path and would silently proceed against a tree
    the adopter hasn't committed.
    """
    work = tmp_path / "repo"
    shutil.copytree(BROWNFIELD, work)
    # EXPECTED_TREE.md is metadata — strip before the snapshot commit
    # so it doesn't appear as a tracked file in the dirty check below.
    (work / "EXPECTED_TREE.md").unlink()
    _init_git_repo(work)

    # Clean tree → porcelain is empty.
    assert _porcelain(work) == "", (
        "porcelain must be empty against a fresh-committed tree; "
        "regression in `git status --porcelain` semantics"
    )

    # Uncommitted edit → porcelain names the dirty path.
    target = work / "AGENTS.md"
    target.write_text(
        target.read_text(encoding="utf-8") + "\n# adopter-edited\n",
        encoding="utf-8",
    )
    dirty = _porcelain(work)
    assert dirty != "", (
        "porcelain must be non-empty after an uncommitted edit; "
        f"got empty output against {target}"
    )
    assert "AGENTS.md" in dirty, (
        f"porcelain must name AGENTS.md as the dirty path; got: {dirty!r}"
    )


def test_repo_scope_dirty_state_porcelain_lists_untracked_seed(tmp_path: Path):
    """Row 17 primitive, second arm: an untracked file at repo root
    is surfaced by `git status --porcelain` so the skill's repo-scope
    Pre-flight can name it under the `Repo scope:` sub-section.

    The skill body's contract is "List every dirty path"; an
    untracked file counts as dirty for pre-flight purposes (the
    adopter may have in-progress work the previous session didn't
    commit). If porcelain stops surfacing untracked entries, the
    skill would proceed against a tree carrying unreviewed adopter
    content.

    Asserts only that the dirty path is named — does NOT assert
    the `??` prefix shape, which is a porcelain-v1 detail; the
    skill body's contract is to *name the path*, not to depend
    on a specific porcelain format version.
    """
    work = tmp_path / "repo"
    shutil.copytree(BROWNFIELD, work)
    (work / "EXPECTED_TREE.md").unlink()
    _init_git_repo(work)

    (work / "NOTES.md").write_text("scratch\n", encoding="utf-8")
    dirty = _porcelain(work)
    assert "NOTES.md" in dirty, (
        f"porcelain must surface untracked files by path; got: {dirty!r}"
    )


def test_user_scope_tier2_content_hash_divergence_detected(tmp_path: Path):
    """Row 18 primitive: content-hash divergence between a tracked
    file's current bytes and the SHA-256 the skill body's Pre-flight
    holds (sourced from `state.toml`) is the deterministic Tier-2
    signal.

    Mirrors the skill's user-scope Pre-flight step:
    > User scope: ~/.agent-ready/ is not a git repo; dirty-detection
    > uses content-hash divergence — compare each tracked file's
    > current SHA-256 against the value recorded in
    > ~/.agent-ready/state.toml.

    The primitive is scope-agnostic: the same `sha256_bytes(actual)
    != recorded` comparison fires at repo scope (against
    `.agent-ready-state.toml`) and at user scope (against
    `~/.agent-ready/state.toml`). We exercise it once against the
    user-scope fixture path-jail.

    Deliberately does not round-trip the `recorded_sha` through
    `dump_state` / `load_state` — that symmetry is covered by
    `tests/unit/test_toml_emitters.py`. The Tier-2 contract under
    test here is the primitive comparison itself.
    """
    user_home = tmp_path / "user-home"
    shutil.copytree(USER_HOME, user_home)
    agent_ready = user_home / ".agent-ready"

    # Seed a tracked file under the user-scope path-jail. The path
    # mirrors the kind of primitive a user-scope pack would project
    # once one exists; the primitive being tested is path-agnostic.
    tracked = agent_ready / ".claude" / "agents" / "bot.md"
    tracked.parent.mkdir(parents=True, exist_ok=True)
    seeded_bytes = b"# bot\nseeded content\n"
    tracked.write_bytes(seeded_bytes)

    # The skill's Pre-flight reads the recorded SHA from state.toml;
    # we model that as a literal `recorded_sha` here (the value the
    # Pre-flight comparator would have in hand at session start).
    recorded_sha = sha256_bytes(seeded_bytes)

    # Baseline: unchanged file hashes equal to the recorded value
    # (no Tier-2 divergence).
    assert sha256_bytes(tracked.read_bytes()) == recorded_sha, (
        "baseline mismatch: tracked file hash differs from recorded "
        "sha before any mutation — primitive contract broken"
    )

    # Mutate → content-hash divergence is detected (the Tier-2
    # signal the Pre-flight surfaces).
    tracked.write_bytes(seeded_bytes + b"# adopter-appended\n")
    current_sha = sha256_bytes(tracked.read_bytes())
    assert current_sha != recorded_sha, (
        "Tier-2 detection primitive broken: post-mutation hash "
        f"still equals recorded sha {recorded_sha!r}"
    )
