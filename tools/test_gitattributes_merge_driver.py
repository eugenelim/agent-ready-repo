"""AC1: the `merge=regen` set equals the gate-covered projection set.

Spec: docs/specs/self-host-projection-merge-driver/spec.md

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

import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
AGENTBUNDLE = REPO_ROOT / "packages" / "agentbundle"
sys.path.insert(0, str(AGENTBUNDLE))

from agentbundle.build.self_host import (  # noqa: E402
    _runtime_projections,
    _self_host_projection_paths,
)

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
        # copy-then-mutate costs roughly four times a single write.
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
    return (behavioural | special | runtime) & _tracked_regular_files(root)


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
