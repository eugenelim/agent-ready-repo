"""What the `regen` driver actually does to a merge and a rebase.

Two specs own criteria here, and both number theirs AC4 and AC5, so every test
below names its owning spec rather than a bare `ACn`:

- docs/specs/self-host-projection-merge-driver/spec.md -- AC2-AC5, the
  self-host projections: non-halting merge and rebase, pack sources still
  conflicting, `make build-self` convergence, and `bootstrap-git` idempotence.
- docs/specs/record-index-merge-driver/spec.md -- AC4-AC5, the record indexes:
  a contested index merge is driver-resolved rather than settled textually, and
  `index-records.py` recovers the row the resolution discarded.

These properties live in git's merge machinery, not in the attributes file, so
every test here drives a real `git merge` or `git rebase`. Asserting on
`.gitattributes` content would prove the file was written, never that git
honours it.

No test names a surviving side. Under `git merge` the driver keeps the local
side; under `git rebase` ours and theirs invert and it keeps upstream. The
content is regenerated either way, so the contract is non-halting plus
convergence.
"""

from __future__ import annotations

import os
import re
import shlex
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

# No sys.path mutation here: pyproject.toml's [tool.pytest.ini_options]
# pythonpath already pins `packages/agentbundle` for this suite, and inserting
# it again leaks a packaged source tree into the collecting process, which
# tools/test_import_time_path_leaks.py refuses.
from agentbundle.build.self_host import _runtime_projections  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[1]
AGENTBUNDLE = REPO_ROOT / "packages" / "agentbundle"

# Matches `.claude/**` in the repository's own .gitattributes.
DRIVER_PATH = Path(".claude/skills/probe/SKILL.md")
# Source of truth: must keep conflicting, because its merges carry decisions.
SOURCE_PATH = Path("packs/core/.apm/skills/probe/SKILL.md")
# Matched by no pattern. Carried by the replayed commit so its patch is
# non-empty and the rebase cannot be short-circuited as already-upstream.
NEUTRAL_PATH = Path("probe-notes.txt")

CONFLICT_MARKERS = ("<<<<<<<", "=======", ">>>>>>>")

# Read from the Makefile rather than repeated here. `make bootstrap-git` is the
# only thing that registers the driver for a real maintainer, so this parse is
# what joins that recipe to the `merge=regen` attribute `.gitattributes`
# declares. Restating the driver name instead would leave a typo in the recipe
# green here while every real merge fell back to conflicting.
# Scopes that would escape the scratch repository. The AC5 test runs the
# recipe's own commands, so a recipe that grew `--global` would otherwise
# rewrite the developer's and the runner's real config instead of failing.
_ESCAPING_SCOPES = ("--global", "--system", "--file", "--blob", "-f")
# Attached forms too: git accepts `--file=<path>` and the short `-f<path>`, and
# a whole-token check sees neither.
_ESCAPING_PREFIXES = ("--file=", "--blob=", "-f")
# `shlex` performs no make expansion, so a token carrying one would be written
# into the scratch repo verbatim while `make bootstrap-git` registers something
# else -- and the test would then compare that literal against DRIVER_COMMAND,
# which came from the same parse. Comparing a parse to itself proves nothing.
_UNEXPANDED = ("$(", "${")

_DRIVER_KEY = re.compile(r"^merge\.([A-Za-z0-9_-]+)\.driver$")


def _bootstrap_git_recipe() -> list[list[str]]:
    """The `git config` commands `make bootstrap-git` runs, in order.

    Reads the recipe as make does -- every tab-indented line until the rule
    ends -- rather than splitting on a blank line, which make ignores inside a
    recipe and which would silently drop a command from the tested set.
    Tokenised with `shlex` so a driver command containing spaces (every real
    driver takes `%O %A %B`) round-trips intact.
    """
    body = (REPO_ROOT / "Makefile").read_text(encoding="utf-8")
    parts = body.split("\nbootstrap-git:", 1)
    assert len(parts) == 2, "Makefile has no bootstrap-git target"

    commands: list[list[str]] = []
    for line in parts[1].splitlines()[1:]:
        if not line.startswith("\t"):
            if line.strip() and not line.startswith("#"):
                break  # the rule ended
            continue
        stripped = line.lstrip("\t").lstrip("@-").strip()
        if not stripped.startswith("git config "):
            continue
        tokens = shlex.split(stripped)
        escaping = [
            t for t in tokens
            if t in _ESCAPING_SCOPES or t.startswith(_ESCAPING_PREFIXES)
        ]
        assert not escaping, (
            f"bootstrap-git runs `git config {escaping[0]}`, which writes "
            "outside the repository; the AC5 test executes these commands and "
            "would rewrite real developer config"
        )
        unexpanded = [t for t in tokens if any(m in t for m in _UNEXPANDED)]
        assert not unexpanded, (
            f"bootstrap-git command carries an unexpanded make reference "
            f"{unexpanded[0]!r}; this parser cannot reproduce what make runs, "
            "so executing it would assert a literal against itself"
        )
        commands.append(tokens)
    assert commands, "bootstrap-git runs no git config command"
    return commands


def _driver_from_makefile() -> tuple[str, str]:
    """The driver name and command the recipe registers.

    Derived from the same parse the AC5 test executes, so the two cannot
    disagree about what the recipe says.
    """
    for tokens in _bootstrap_git_recipe():
        # `git config <key> <value>`
        if len(tokens) < 4:
            continue
        match = _DRIVER_KEY.match(tokens[2])
        if match:
            return match.group(1), tokens[3]
    raise AssertionError("bootstrap-git registers no merge.<name>.driver")


DRIVER_NAME, DRIVER_COMMAND = _driver_from_makefile()


def _git(*args: str, cwd: Path, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", *args], cwd=cwd, capture_output=True, text=True, check=check
    )


def _write(root: Path, relative: Path, text: str) -> None:
    target = root / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8")


def _configure_identity(root: Path) -> None:
    """Give the repo its own commit identity, and nothing else.

    `git merge` and `git rebase` create commits too, and receive no `-c` flags.
    A runner with no global identity aborts them with `unable to auto-detect
    email address`, so identity set per-commit would pass here and fail in CI.

    Separate from driver registration because the record-index case needs a
    clone that has an identity and has *not* registered the driver: its first
    merge must halt.
    """
    _git("config", "user.email", "fixture@example.invalid", cwd=root)
    _git("config", "user.name", "merge driver fixture", cwd=root)


def _register_driver(root: Path) -> None:
    """Register the driver the Makefile recipe registers."""
    _git("config", f"merge.{DRIVER_NAME}.driver", DRIVER_COMMAND, cwd=root)


def _configure(root: Path) -> None:
    """Identity plus driver registration, the state most tests here need."""
    _configure_identity(root)
    _register_driver(root)


def _commit(root: Path, message: str, *, allow_empty: bool = False) -> None:
    """Commit staged work.

    `allow_empty` is opt-in, and only the clone fixture needs it: the block it
    copies is already in HEAD once this change has landed. Everywhere else a
    commit that carried nothing is a fixture failure, because it degrades the
    merge under test into a fast-forward that never invokes the driver.
    """
    _git("add", "-A", cwd=root)
    if not _git("status", "--porcelain", cwd=root).stdout.strip():
        assert allow_empty, (
            f"nothing to commit for {message!r}; the fixture did not change "
            "what it meant to, and the merge under test would fast-forward"
        )
        return
    _git("commit", "-qm", message, cwd=root)


@pytest.fixture
def synthetic_repo(tmp_path: Path) -> Path:
    """A scratch repo carrying the repository's real .gitattributes.

    The attributes file is copied from the working tree rather than authored
    here, so the test exercises the block that actually ships. The driver is
    registered locally because git config is per-clone.
    """
    root = tmp_path / "synthetic"
    root.mkdir()
    _git("init", "-q", "-b", "main", ".", cwd=root)
    _configure(root)
    shutil.copy2(REPO_ROOT / ".gitattributes", root / ".gitattributes")
    _write(root, DRIVER_PATH, "BASE\n")
    _write(root, SOURCE_PATH, "BASE\n")
    _write(root, NEUTRAL_PATH, "BASE\n")
    _commit(root, "base")
    return root


def _assert_real_merge(root: Path) -> None:
    """HEAD must be a merge commit, not a fast-forward.

    A fast-forward exits 0, leaves the other side's content in place and writes
    no markers -- indistinguishable from a driver-resolved merge by every other
    assertion here, and it never invokes the driver at all.
    """
    parents = _git("rev-list", "--parents", "-n1", "HEAD", cwd=root).stdout.split()
    assert len(parents) >= 3, (
        "HEAD has one parent: the merge fast-forwarded, so no three-way merge "
        "ran and the driver was never exercised"
    )


def _assert_no_markers(root: Path, relative: Path) -> None:
    body = (root / relative).read_text(encoding="utf-8")
    present = [m for m in CONFLICT_MARKERS if m in body]
    assert not present, f"{relative} carries conflict markers {present}: {body!r}"


def test_merge_settles_a_projection_without_halting(synthetic_repo: Path) -> None:
    """docs/specs/self-host-projection-merge-driver/spec.md AC2, merge half."""
    root = synthetic_repo
    _git("checkout", "-qb", "feature", cwd=root)
    _write(root, DRIVER_PATH, "FEATURE\n")
    _commit(root, "feature edits the projection")
    _git("checkout", "-q", "main", cwd=root)
    _write(root, DRIVER_PATH, "MAIN\n")
    _commit(root, "main edits the projection")

    merge = _git("merge", "--no-edit", "feature", cwd=root, check=False)
    assert merge.returncode == 0, (
        "merge halted on a merge=regen path:\n" + merge.stdout + merge.stderr
    )
    _assert_real_merge(root)
    _assert_no_markers(root, DRIVER_PATH)


def test_rebase_settles_a_projection_without_halting(synthetic_repo: Path) -> None:
    """docs/specs/self-host-projection-merge-driver/spec.md AC2, rebase half — and the replay is real, not a dropped patch.

    A commit touching only projections becomes empty once the driver resolves
    to upstream, and git drops it with `patch contents already upstream`. That
    path exercises no driver at all, so the replayed commit also carries
    NEUTRAL_PATH, edited on this side only so it cannot itself conflict.
    """
    root = synthetic_repo
    _git("checkout", "-qb", "feature", cwd=root)
    _write(root, DRIVER_PATH, "FEATURE\n")
    _write(root, NEUTRAL_PATH, "FEATURE-ONLY\n")
    _commit(root, "replayed: projection plus a neutral file")
    _git("checkout", "-q", "main", cwd=root)
    _write(root, DRIVER_PATH, "MAIN\n")
    _commit(root, "main edits the projection")
    _git("checkout", "-q", "feature", cwd=root)

    rebase = _git("rebase", "main", cwd=root, check=False)
    assert rebase.returncode == 0, (
        "rebase halted on a merge=regen path:\n" + rebase.stdout + rebase.stderr
    )
    _assert_no_markers(root, DRIVER_PATH)

    subjects = _git("log", "--format=%s", "main..HEAD", cwd=root).stdout
    assert "replayed: projection plus a neutral file" in subjects, (
        "the replayed commit was dropped as already-upstream, so no merge ran "
        "and the driver was never exercised:\n" + rebase.stdout + rebase.stderr
    )


def test_pack_source_still_conflicts(synthetic_repo: Path) -> None:
    """docs/specs/self-host-projection-merge-driver/spec.md AC3: sources carry decisions, so their merges must reach a human."""
    root = synthetic_repo
    _git("checkout", "-qb", "feature", cwd=root)
    _write(root, SOURCE_PATH, "FEATURE\n")
    _commit(root, "feature edits the source")
    _git("checkout", "-q", "main", cwd=root)
    _write(root, SOURCE_PATH, "MAIN\n")
    _commit(root, "main edits the source")

    merge = _git("merge", "--no-edit", "feature", cwd=root, check=False)
    assert merge.returncode != 0, (
        "merge of divergent pack sources did not halt; git may have "
        "fast-forwarded or auto-merged:\n" + merge.stdout + merge.stderr
    )
    body = (root / SOURCE_PATH).read_text(encoding="utf-8")
    assert all(m in body for m in CONFLICT_MARKERS), (
        f"pack source lacks conflict markers after a halted merge: {body!r}"
    )


@pytest.fixture(scope="module")
def clone_repo(tmp_path_factory) -> Path:
    """A real clone: `make build-self` needs the Makefile, packs/ and agentbundle.

    A clone carries HEAD, not the working tree, so the .gitattributes block is
    copied across and committed here — otherwise the fixture would exercise a
    tree with no `merge=regen` pattern at all. The driver is registered inside
    the clone because git config is per-clone, not per-worktree.
    """
    root = tmp_path_factory.mktemp("convergence") / "clone"
    _git("clone", "--quiet", "--local", str(REPO_ROOT), str(root), cwd=REPO_ROOT.parent)
    _configure(root)
    # A clone carries HEAD, so the block is already here once this change has
    # landed and is absent while it is still a working-tree delta. Copy either
    # way; `_commit` is a no-op when there is nothing to carry across. Treating
    # "nothing to commit" as a failure would make this fixture pass only while
    # the block stayed uncommitted -- green now, red on the run that lands it.
    shutil.copy2(REPO_ROOT / ".gitattributes", root / ".gitattributes")
    _commit(root, "carry the merge=regen block into the fixture", allow_empty=True)
    assert _git("check-attr", "merge", "--", ".claude/skills/work-loop/SKILL.md",
                cwd=root).stdout.strip().endswith(f"merge: {DRIVER_NAME}"), (
        f"the clone does not resolve merge={DRIVER_NAME}; the fixture would "
        "measure a tree without the block"
    )
    yield root
    shutil.rmtree(root.parent, ignore_errors=True)


def test_build_self_converges_after_an_auto_resolved_merge(clone_repo: Path) -> None:
    """docs/specs/self-host-projection-merge-driver/spec.md AC4: regeneration reaches a fixed point, whichever side the merge kept.

    Asserted as a fixed point rather than a no-op: `make build-self` is
    *expected* to write here, because the side git kept was generated from one
    branch's sources and the merged sources differ. That is why the documented
    workflow ends in `commit --amend`. What must hold afterwards is that the
    gates report nothing.
    """
    root = clone_repo
    projection = root / ".claude" / "skills" / "work-loop" / "SKILL.md"
    assert projection.is_file(), "fixture lost its projection"

    _git("checkout", "-qb", "divergent", cwd=root)
    projection.write_text(projection.read_text(encoding="utf-8") + "\ndivergent\n",
                          encoding="utf-8")
    _commit(root, "divergent edit to a projection")
    _git("checkout", "-q", "-", cwd=root)
    projection.write_text(projection.read_text(encoding="utf-8") + "\nmainline\n",
                          encoding="utf-8")
    _commit(root, "mainline edit to the same projection")

    merge = _git("merge", "--no-edit", "divergent", cwd=root, check=False)
    assert merge.returncode == 0, (
        "merge halted on a projection inside the clone fixture:\n"
        + merge.stdout + merge.stderr
    )
    _assert_real_merge(root)

    build = subprocess.run(
        ["make", "build-self"], cwd=root, capture_output=True, text=True,
    )
    assert build.returncode == 0, (
        "make build-self failed in the clone:\n" + build.stdout[-3000:] + build.stderr[-3000:]
    )

    # The self-host drift comparison is reachable only through the dry run --
    # `run_build_check_drift_gates` does not contain it, resolves `dist/`, and
    # measures REPO_ROOT rather than the clone.
    check = subprocess.run(
        [sys.executable, "-m", "agentbundle", "catalogue", "self-host",
         "--root", str(root), "--check"],
        cwd=REPO_ROOT, capture_output=True, text=True,
        env=dict(os.environ, PYTHONPATH=str(AGENTBUNDLE), PYTHONUTF8="1"),
    )
    assert check.returncode == 0, (
        "self-host reports drift after build-self converged:\n"
        + check.stdout[-3000:] + check.stderr[-3000:]
    )

    # Second half of AC4: the dry run says it skips these, so compare directly.
    # Absence must red rather than skip -- a loop that compares zero pairs is
    # exactly the state this half exists to catch.
    pairs = _runtime_projections(root)
    assert pairs, "no packaged runtime pairs to compare; AC4 has no floor"
    for source, bundled in pairs:
        assert source.is_file(), f"packaged runtime source missing: {source}"
        assert bundled.is_file(), f"packaged runtime target missing: {bundled}"
        assert source.read_bytes() == bundled.read_bytes(), (
            f"packaged runtime drift after convergence: {bundled.name}"
        )


def test_bootstrap_git_registers_the_driver_idempotently(tmp_path: Path) -> None:
    """docs/specs/self-host-projection-merge-driver/spec.md AC5: the recipe registers `merge.<driver>.driver` and a rerun is a no-op.

    Runs the Makefile recipe's own commands against a scratch repository rather
    than invoking `make bootstrap-git`, which would write into the developer's
    real git config. Reading them from the Makefile keeps the two joined: a
    recipe that stopped registering the driver reds here.
    """
    root = tmp_path / "bootstrap"
    root.mkdir()
    _git("init", "-q", "-b", "main", ".", cwd=root)

    commands = _bootstrap_git_recipe()
    for _ in range(2):
        for command in commands:
            _git(*command[1:], cwd=root)

    probe = _git("config", "--local", "--get", f"merge.{DRIVER_NAME}.driver",
                 cwd=root, check=False)
    assert probe.returncode == 0, (
        f"the recipe registered no merge.{DRIVER_NAME}.driver; expected "
        f"{DRIVER_COMMAND!r}"
    )
    driver = probe.stdout.strip()
    assert driver == DRIVER_COMMAND, (
        f"merge.{DRIVER_NAME}.driver is {driver!r}, expected {DRIVER_COMMAND!r}"
    )
    # Set semantics make a rerun idempotent with no guard; a recipe that grew an
    # append (`--add`) would leave two values and fail `--get`.
    # `--local`: without it this reads the developer's global and system scopes
    # too, so a maintainer who registered the driver globally instead of per
    # clone fails with "a second run changed the value" -- a cause that did not
    # happen.
    repeated = _git("config", "--local", "--get-all", f"merge.{DRIVER_NAME}.driver",
                    cwd=root, check=False)
    assert repeated.stdout.strip().splitlines() == [DRIVER_COMMAND], (
        "a second run changed the value: " + repeated.stdout
    )
    # The attribute the block declares must name the driver the recipe registers.
    declared = (REPO_ROOT / ".gitattributes").read_text(encoding="utf-8")
    assert f"merge={DRIVER_NAME}" in declared, (
        f".gitattributes declares no merge={DRIVER_NAME}; the recipe registers a "
        "driver nothing uses"
    )


# --- docs/specs/record-index-merge-driver AC4-AC5 -----------------------------

INDEX_SCRIPT = REPO_ROOT / ".claude/skills/new-adr/scripts/index-records.py"
RECORD_DIR = Path("docs/adr")
RECORD_INDEX = RECORD_DIR / "README.md"


def _record(ordinal: str, day: str) -> str:
    return (
        f"# ADR-{ordinal}: Record {ordinal}\n\n"
        "- **Status:** Accepted\n"
        f"- **Date:** 2026-01-{day}\n\n"
        "Body.\n"
    )


def _regenerate_index(root: Path) -> subprocess.CompletedProcess:
    """Run the script `check-adr-index` runs, against the scratch tree."""
    return subprocess.run(
        [sys.executable, str(INDEX_SCRIPT), str(root / RECORD_DIR)],
        cwd=REPO_ROOT, capture_output=True, text=True,
    )


def _index_rows(root: Path) -> set[str]:
    """The record ordinals the index table carries."""
    text = (root / RECORD_INDEX).read_text(encoding="utf-8")
    return set(re.findall(r"^\| (\d{4}) \|", text, flags=re.MULTILINE))


@pytest.fixture
def record_index_repo(tmp_path: Path) -> Path:
    """A scratch repo with a real index, an identity, and NO driver registered.

    Withholding the driver is the point: AC4's first half needs a merge that
    halts, and `_configure` would have registered it. The repository's real
    `.gitattributes` is copied in, so the declared block is the shipped one.
    """
    root = tmp_path / "records"
    root.mkdir()
    _git("init", "-q", "-b", "main", ".", cwd=root)
    _configure_identity(root)
    shutil.copy2(REPO_ROOT / ".gitattributes", root / ".gitattributes")
    _write(root, RECORD_DIR / "0001-first.md", _record("0001", "01"))
    assert _regenerate_index(root).returncode == 0
    _commit(root, "base")

    unset = _git("config", "--get", f"merge.{DRIVER_NAME}.driver",
                 cwd=root, check=False)
    assert unset.returncode != 0, (
        "merge.regen.driver resolves in the fixture before the test registers "
        f"it ({unset.stdout.strip()!r}); an inherited --global value would let "
        "the halting half pass without proving anything"
    )
    return root


def _diverge(root: Path) -> None:
    """Two branches, each adding a distinct record and regenerating the index."""
    for branch, ordinal, day in (("side", "0002", "02"), ("main", "0003", "03")):
        _git("checkout", "-q", "main", cwd=root)
        if branch != "main":
            _git("checkout", "-q", "-b", branch, cwd=root)
        _write(root, RECORD_DIR / f"{ordinal}-r.md", _record(ordinal, day))
        assert _regenerate_index(root).returncode == 0
        _commit(root, f"add {ordinal}")


def test_record_index_merge_is_driver_resolved_not_textual(record_index_repo: Path) -> None:
    """docs/specs/record-index-merge-driver AC4.

    Differential, because the driver's effect is an absence. A merge that does
    not halt is indistinguishable from one that never needed resolving -- a
    fast-forward, or a divergence git settles textually -- and both satisfy
    "completes without halting" with the driver deleted. Running the same
    starting state with the driver unset is what makes this false when the
    driver is absent or irrelevant.
    """
    root = record_index_repo
    _diverge(root)

    halted = _git("merge", "--no-edit", "side", cwd=root, check=False)
    assert halted.returncode != 0, (
        "the merge completed with no driver registered, so git settled the "
        "index textually and the driver is not what resolves it:\n"
        + halted.stdout + halted.stderr
    )
    conflicted = _git("diff", "--name-only", "--diff-filter=U", cwd=root).stdout.split()
    assert RECORD_INDEX.as_posix() in conflicted, conflicted

    _git("merge", "--abort", cwd=root)
    _register_driver(root)

    resolved = _git("merge", "--no-edit", "side", cwd=root, check=False)
    assert resolved.returncode == 0, resolved.stdout + resolved.stderr
    _assert_no_markers(root, RECORD_INDEX)
    _assert_real_merge(root)


def test_record_index_regeneration_recovers_the_discarded_row(
    record_index_repo: Path,
) -> None:
    """docs/specs/record-index-merge-driver AC5.

    The falsifier is the row belonging to the side the driver discarded. AC4's
    halting half is what guarantees it exists: a merge that halts without the
    driver is one whose rows genuinely collide, so the resolution drops one.
    Re-running `--check` against the file the generator just wrote would be
    self-comparing and would hold for any generator at all.
    """
    root = record_index_repo
    _diverge(root)
    _register_driver(root)
    assert _git("merge", "--no-edit", "side", cwd=root, check=False).returncode == 0

    after_merge = _index_rows(root)
    assert after_merge != {"0001", "0002", "0003"}, (
        "the merged table already carries every row, so the driver discarded "
        "nothing and this test would pass without regeneration"
    )

    assert _regenerate_index(root).returncode == 0
    assert _index_rows(root) == {"0001", "0002", "0003"}
