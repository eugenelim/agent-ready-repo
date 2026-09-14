"""AC1: the `merge=regen` set equals the gate-covered set.

Spec: docs/specs/record-index-merge-driver/spec.md, which owns this equality.
It widened the covered set from the self-host pipeline alone to the union over
every required `gate-main` generator rail. The narrower form shipped in
docs/specs/self-host-projection-merge-driver/spec.md, whose AC1 this replaces
and whose frozen body still states it.

A path may carry the `regen` merge driver only where a required `gate-main`
check would catch a bad regeneration, because the driver discards one merge
side and the gate is the only thing that notices. The eligible set is derived
from the pipeline, never enumerated: an added or removed adapter moves the
expectation automatically.

The rail set is measured behaviourally rather than composed from the writers
`run_self_host` calls. Composition was tried and silently omitted
`_aggregate_marketplace`, which writes `.claude-plugin/marketplace.json` --
the failure mode a hand-maintained list always has.
"""

from __future__ import annotations

import argparse
import importlib.util
import os
import re
import shutil
import subprocess
import sys
from collections.abc import Iterable, Sequence
from pathlib import Path
from unittest import mock

import pytest

# No sys.path mutation here: pyproject.toml's [tool.pytest.ini_options]
# pythonpath already pins `packages/agentbundle` for this suite; inserting it
# again leaks a packaged source tree into the collecting process.
from agentbundle.build.self_host import (
    _runtime_projections,
    _self_host_projection_paths,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
AGENTBUNDLE = REPO_ROOT / "packages" / "agentbundle"

# `git ls-files -s` mode for a symlink. Git applies no content merge driver to
# a symlink blob, so declaring one would have no effect; both sides of the
# equality drop them.
SYMLINK_MODE = "120000"

# Pack trees are the source of truth, never a driver target. Two rails report a
# `packs/` path as their *target*: user-libs vendors
# `packages/credbroker/` into `packs/*/.apm/user-libs/` before projecting on to
# `.agentbundle/lib/`, so the middle hop of that chain names a source path.
SOURCE_PREFIX = "packs/"

DRIFT_HEADER = re.compile(r"found (\d+) drift\(s\):")
FIRST_QUOTED = re.compile(r'"([^"]+)"')


def _tracked_regular_files(root: Path) -> set[Path]:
    """Tracked paths excluding symlinks, as repo-relative paths."""
    out = subprocess.run(
        ["git", "ls-files", "-s"],
        cwd=root, capture_output=True, text=True, check=True,
    ).stdout
    paths: set[Path] = set()
    for line in out.splitlines():
        mode, _, rest = line.partition(" ")
        if mode == SYMLINK_MODE:
            continue
        paths.add(Path(rest.split("\t", 1)[1]))
    return paths


def _attribute_set(root: Path, candidates: set[Path]) -> set[Path]:
    """Paths git resolves to `merge=regen`, read through `git check-attr`.

    Uses `--stdin` because the tracked list is far past the argv limit, and
    asks git rather than reimplementing gitattributes precedence.
    """
    payload = "\n".join(sorted(str(p) for p in candidates))
    out = subprocess.run(
        ["git", "check-attr", "merge", "--stdin"],
        cwd=root, input=payload, capture_output=True, text=True, check=True,
    ).stdout
    found: set[Path] = set()
    for line in out.splitlines():
        path, _, attr = line.rpartition(": merge: ")
        if attr.strip() == "regen":
            found.add(Path(path))
    return found


def _mutated_scratch_tree(root: Path, destination: Path) -> None:
    """Copy the working tree to `destination` with every non-source file mutated.

    Copied from the working tree rather than extracted from HEAD so both sides
    of AC1's equality describe the same snapshot. `git check-attr` reads the
    working-tree `.gitattributes`, so an archive of HEAD would measure the
    declared set against a tree that does not contain a staged-but-uncommitted
    projection -- reporting a genuinely gated path as over-scope, the exact
    inverse of the truth, during the change most likely to be running this.

    `packs/` is copied unmutated so the projection the pipeline renders is the
    real one; every other regular file gains a trailing newline, a byte
    difference in every format the tree carries that leaves TOML, JSON and YAML
    valid. Symlinks are copied unmutated. `_tracked_regular_files` already drops
    mode `120000`, so the repository's three tracked symlinks never arrive here;
    the guard catches the skew case, where the index calls a path regular and
    the working tree has since made it a link, which would otherwise append
    through the link into its target.
    """
    destination.mkdir(parents=True, exist_ok=True)
    missing: list[Path] = []
    for relative in sorted(_tracked_regular_files(root)):
        source = root / relative
        if not source.exists():
            missing.append(relative)
            continue
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        if source.is_symlink() or str(relative).startswith(SOURCE_PREFIX):
            shutil.copy2(source, target, follow_symlinks=False)
            continue
        # One write, not a copy followed by an append: on a copy-on-write
        # filesystem the append forces the block copy that copy2 deferred, so
        # copy-then-mutate costs roughly four times a single write. This drops
        # permission bits, which copy2 preserved -- the drift comparison reads
        # content, so it does not matter today, but a mode-sensitive gate must
        # not read this as an intentional equivalence.
        target.write_bytes(source.read_bytes() + b"\n")
    assert not missing, (
        "tracked files absent from the working tree; the two sides of the "
        f"equality would describe different snapshots: {missing[:10]}"
    )


def _drifted_paths(scratch: Path) -> set[Path]:
    """Every path the self-host drift report names, however it names it.

    The report carries several message families -- `[drift]`,
    `[adapter-root-bins]`, its shim-companion variant, and `[user-libs]` -- and
    each leads with the offending path in quotes. Reading the first quoted
    token rather than matching prefixes means a family added later is picked up
    instead of silently dropped.

    A line the parser cannot read is a hard failure, not a smaller rail set.
    Silently dropping it would shrink the measured set and then report hundreds
    of paths as over-scope, pointing the reader at `.gitattributes` when what
    actually changed was a drift message.
    """
    result = subprocess.run(
        [sys.executable, "-m", "agentbundle", "catalogue", "self-host",
         "--root", str(scratch), "--check"],
        cwd=REPO_ROOT, capture_output=True, text=True,
        env=dict(os.environ, PYTHONPATH=str(AGENTBUNDLE), PYTHONUTF8="1"),
    )
    combined = result.stdout + result.stderr
    # The pipeline exits 1 on drift and 4/5 on a refusal. Only the first is a
    # measurement; the rest are crashes wearing a measurement's clothes.
    assert result.returncode in (0, 1), (
        f"self-host --check crashed (exit {result.returncode}) instead of "
        "reporting drift:\n" + combined[-3000:]
    )
    lines = combined.splitlines()
    header = next(
        ((i, m) for i, line in enumerate(lines)
         if (m := DRIFT_HEADER.search(line))), None
    )
    assert header is not None, (
        "self-host --check reported no drift block against a fully mutated "
        "tree; the fixture is not exercising the gate.\n" + combined[-3000:]
    )
    index, match = header
    declared_count = int(match.group(1))

    drifted: set[Path] = set()
    parsed = 0
    for line in lines[index + 1:]:
        if not line.startswith("  "):
            break
        parsed += 1
        quoted = FIRST_QUOTED.search(line)
        assert quoted, (
            "unparseable drift line -- the report format changed, so the rail "
            f"set can no longer be measured from it:\n  {line!r}"
        )
        drifted.add(Path(quoted.group(1)))
    assert parsed == declared_count, (
        f"drift block holds {parsed} lines but the header declared "
        f"{declared_count}; the report format changed.\n"
        + "\n".join(lines[index:index + min(parsed, 20) + 1])
    )
    return drifted


INDEX_SCRIPT_NAME = "index-records.py"


def _record_index_paths(argvs: Iterable[Sequence[str]]) -> set[Path]:
    """README paths the record-index gate steps cover, read from chain argv.

    Derived from the chain rather than listed, so removing or renaming a
    record-index gate step removes its README from the covered set and the AC1
    equality then reds as over-scope. A literal pair or a `docs/*/README.md`
    glob would stay green after the gate that justified the path was deleted --
    exactly the state the driver must never be left in.

    The record directory is the last positional: `index-records.py` takes one,
    and reading it positionally survives a flag being added ahead of it. The
    `[2:]` slice drops the `[interpreter, script]` prefix every `_script_step`
    argv carries; it is belt-and-braces today, since only the last positional is
    read, and it is what would need revisiting if a step form ever put a
    positional before the script path.
    """
    covered: set[Path] = set()
    for argv in argvs:
        parts = [str(part) for part in argv]
        if not any(part.endswith(INDEX_SCRIPT_NAME) for part in parts):
            continue
        if "--check" not in parts:
            continue
        positionals = [p for p in parts[2:] if not p.startswith("-")]
        if positionals:
            covered.add(Path(positionals[-1]) / "README.md")
    return covered


def _build_check_argv(root: Path) -> list[list[str]]:
    """Every argv `build_check` spawns, collected without running a step.

    `build_check` builds no in-process handler step, so faking `subprocess.run`
    intercepts the whole chain and nothing touches the tree. Same harness as
    `test_spawned_script_paths_in_order` in `tools/test_build_gate_chain.py`.
    """
    location = root / "tools" / "repo" / "build_gate_chain.py"
    spec = importlib.util.spec_from_file_location("_gate_chain_probe", location)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    seen: list[list[str]] = []

    def _fake_run(argv, check=False, env=None, cwd=None, **kwargs):
        seen.append([str(part) for part in argv])
        # No step reads stdout: every one is a subprocess whose return code is
        # the whole result, and `_pytest_step_cwd`'s collection floor is
        # enforced in the child by the `tools.pytest_collection_floor` plugin.
        return mock.Mock(returncode=0, stdout="", stderr="")

    with mock.patch.object(module.subprocess, "run", _fake_run):
        code = module.build_check(
            argparse.Namespace(packs_dir="packs", output_dir="dist")
        )
    # `_run_chain` stops at the first non-zero step. A short collection would
    # drop the record-index steps and red AC1 as over-scope, pointing the
    # reader at `.gitattributes` when the probe is what broke.
    assert code == 0, (
        f"the faked build-check chain exited {code}, so the collected argv is "
        "truncated and the record-index rail cannot be measured from it"
    )
    return seen


def rail_set(root: Path, scratch: Path) -> set[Path]:
    """Tracked regular files a required `gate-main` check covers."""
    behavioural = {
        p for p in _drifted_paths(scratch)
        if not str(p).startswith(SOURCE_PREFIX)
    }
    # The `.agentbundle/` rails report the middle hop of a two-hop chain, so a
    # target whose message named a `packs/` path is recovered here by target.
    special = {
        p for p in _self_host_projection_paths(root, root / "packs")
        if not str(p).startswith(SOURCE_PREFIX)
    }
    # Skipped by the dry run, which says so, and covered instead by the
    # packaged-runtime byte-identity gate in `make build-check`.
    runtime = {b.relative_to(root) for _, b in _runtime_projections(root)}
    # Second generator, second rail: the record indexes `index-records.py`
    # writes, which `_is_excluded` hides from every rail above.
    record_index = _record_index_paths(_build_check_argv(root))
    return (
        behavioural | special | runtime | record_index
    ) & _tracked_regular_files(root)


@pytest.fixture(scope="module")
def scratch_tree(tmp_path_factory) -> Path:
    destination = tmp_path_factory.mktemp("railprobe")
    _mutated_scratch_tree(REPO_ROOT, destination)
    yield destination
    shutil.rmtree(destination, ignore_errors=True)


def test_merge_regen_set_equals_gate_covered_set(scratch_tree: Path) -> None:
    """AC1: the two sets are equal, so neither over- nor under-scope survives.

    An over-scoped pattern puts the driver on a path no gate watches, where a
    merge silently discards a real edit. An under-scoped block leaves a
    projection conflicting for no reason. One equality catches both.
    """
    covered = rail_set(REPO_ROOT, scratch_tree)
    declared = _attribute_set(REPO_ROOT, _tracked_regular_files(REPO_ROOT))

    assert covered, "rail set is empty; the fixture is not measuring anything"
    assert declared, "no path resolves merge=regen; the .gitattributes block is missing"

    over_scoped = sorted(str(p) for p in declared - covered)
    under_scoped = sorted(str(p) for p in covered - declared)
    assert not over_scoped and not under_scoped, (
        "merge=regen must match the gate-covered set exactly.\n"
        f"declared but ungated ({len(over_scoped)}): {over_scoped[:20]}\n"
        f"gated but undeclared ({len(under_scoped)}): {under_scoped[:20]}"
    )


def test_pack_sources_never_carry_the_driver() -> None:
    """Sources must keep conflicting: their merges carry real decisions.

    Guards the trap that `_self_host_projection_paths` sets -- it reports six
    `packs/*/.apm/user-libs/` paths as rail targets, and wiring those into the
    block would put the driver on the source of truth.
    """
    tracked = _tracked_regular_files(REPO_ROOT)
    sources = {p for p in tracked if str(p).startswith(SOURCE_PREFIX)}
    assert sources, "no pack sources tracked; the query is not measuring anything"

    # A positive control in the same measurement. A reader that returned an
    # empty set for any input would satisfy the real assertion below without it.
    control = Path(".claude/skills/work-loop/SKILL.md")
    assert control in tracked, "control path moved; pick another declared path"
    probed = _attribute_set(REPO_ROOT, sources | {control})
    assert control in probed, (
        "the attribute reader returned nothing for a known merge=regen path; "
        "its empty result below would prove nothing"
    )

    assert not (probed - {control}), (
        "pack sources carry merge=regen: "
        + str(sorted(str(p) for p in probed - {control})[:20])
    )


def test_record_index_rail_is_empty_without_a_gate_step() -> None:
    """AC2: no `index-records.py --check` step contributes no path.

    The empty case is the one that matters: a derivation that fell back to a
    literal pair would return the two READMEs here, and the AC1 equality would
    then stay green after the gate justifying them was deleted.
    """
    assert _record_index_paths([]) == set()
    assert _record_index_paths([
        ["python", "tools/lint-build.py"],
        ["python", "-m", "pytest", "tools/test_build_gate_chain.py", "-q"],
        # Named but not checking: the write mode maintains no gate.
        ["python", ".claude/skills/new-adr/scripts/index-records.py", "docs/adr"],
    ]) == set()


def test_record_index_rail_follows_the_steps_it_is_given() -> None:
    """AC2: each checking step contributes its own directory's README."""
    argvs = [
        ["python", ".claude/skills/new-adr/scripts/index-records.py", "--check", "docs/adr"],
        ["python", ".claude/skills/new-rfc/scripts/index-records.py", "--check", "docs/rfc"],
        # A third record type wired later is picked up with no edit here.
        ["python", ".claude/skills/new-xyz/scripts/index-records.py", "--check", "docs/xyz"],
    ]
    assert _record_index_paths(argvs) == {
        Path("docs/adr/README.md"),
        Path("docs/rfc/README.md"),
        Path("docs/xyz/README.md"),
    }


def test_record_index_rail_reads_the_real_build_check_chain() -> None:
    """AC2: against the chain this repository actually runs."""
    assert _record_index_paths(_build_check_argv(REPO_ROOT)) == {
        Path("docs/adr/README.md"),
        Path("docs/rfc/README.md"),
    }


def _synthetic_record_dir(tmp_path: Path) -> Path:
    """One ADR carrying an explicit `Date:`, with its index generated.

    Explicit dates are load-bearing. `index-records.py` resolves a missing date
    from the record's add-commit, so a directory copied out of this repository
    reds regardless of its README -- a control with no passing state. A record
    with no date at all is the opposite trap: the empty cell renders on both
    sides of a generate-then-check, so the pair passes proving nothing. The
    date-cell assertion below is what distinguishes a fixture reading its own
    records from one that has silently degraded into either.
    """
    directory = tmp_path / "adr"
    directory.mkdir()
    (directory / "0001-a-synthetic-record.md").write_text(
        "# ADR-0001: A synthetic record\n\n"
        "- **Status:** Accepted\n"
        "- **Date:** 2026-01-01\n\n"
        "Body.\n",
        encoding="utf-8",
    )
    written = _index_records(directory)
    # Fail here, not three assertions later. A failed generation leaves no
    # README, which surfaces as AC3's clean case reporting a non-zero --check --
    # reading as a rail failure -- or as FileNotFoundError, in both cases with
    # the generator's own diagnosis unprinted and the scratch tree gone.
    assert written.returncode == 0, (
        f"index-records.py failed building the fixture (exit "
        f"{written.returncode}):\n" + written.stdout + written.stderr
    )
    return directory


def _index_records(directory: Path, *check: str) -> subprocess.CompletedProcess:
    """Run the projected script the `check-adr-index` gate step runs."""
    return subprocess.run(
        [sys.executable,
         str(REPO_ROOT / ".claude/skills/new-adr/scripts/index-records.py"),
         *check, str(directory)],
        cwd=REPO_ROOT, capture_output=True, text=True,
    )


def test_index_check_is_clean_when_the_readme_matches(tmp_path: Path) -> None:
    """AC3: the rail has a passing state, so its red means something."""
    directory = _synthetic_record_dir(tmp_path)
    result = _index_records(directory, "--check")
    assert result.returncode == 0, result.stdout + result.stderr


def test_both_projected_index_generators_are_the_same_program() -> None:
    """AC3 for the `docs/rfc` half, which no fixture exercises directly.

    AC3's clean/red pair runs the `new-adr` copy. The `docs/rfc` rail inherits
    that evidence only if `check-rfc-index` runs the same program, and nothing
    else required says so: `tests/roster/test_index_records.py` exercises
    behaviour but runs in the dispatch-only `test-roster.yml`. Without this, the
    rfc copy could stop reporting drift, `check-rfc-index` would pass forever,
    and `docs/rfc/README.md` would keep a driver that discards a merge side with
    nothing regenerating it. The sibling `next-ordinal.py` already carries a
    gated identity pin of this shape.
    """
    copies = [
        REPO_ROOT / ".claude/skills" / skill / "scripts/index-records.py"
        for skill in ("new-adr", "new-rfc")
    ]
    for copy in copies:
        assert copy.is_file(), f"projected generator missing: {copy}"
    adr, rfc = (c.read_bytes() for c in copies)
    assert adr == rfc, (
        "the projected index generators have diverged, so AC3's clean/red pair "
        "against the new-adr copy no longer establishes that check-rfc-index "
        "can fail; exercise the rfc copy directly or restore parity"
    )


def test_index_table_carries_the_records_own_date(tmp_path: Path) -> None:
    """AC3: the fixture reads its records rather than an empty fallback.

    Without this the suite cannot tell a sound fixture from one whose records
    lost their dates, because that degradation renders identically on both
    sides of the generate-then-check above.
    """
    directory = _synthetic_record_dir(tmp_path)
    table = (directory / "README.md").read_text(encoding="utf-8")
    assert "2026-01-01" in table, table


def test_index_check_reds_and_names_the_readme(tmp_path: Path) -> None:
    """AC3: the gate step's red names the path the driver is declared on."""
    directory = _synthetic_record_dir(tmp_path)
    readme = directory / "README.md"
    readme.write_text(readme.read_text(encoding="utf-8") + "drift\n", encoding="utf-8")

    result = _index_records(directory, "--check")
    assert result.returncode != 0, result.stdout + result.stderr
    combined = result.stdout + result.stderr
    assert str(readme) in combined, combined
