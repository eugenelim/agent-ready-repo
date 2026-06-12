"""T12: integration tests for ``agentbundle upgrade``.

Coverage:
  - Whole-pack upgrade: 0.1.0 → 0.2.0; installed-version updated; file content is 0.2.0.
  - Per-primitive upgrade (parametrised over all five flags): only matching files change.
  - Mixed-version surfacing: upgrade --skill first, then whole-pack → stderr has warning.
  - Primitive-not-found: --skill foo where foo not in pack → exit non-zero with message.
  - Hook-extension preservation: .sh stays .sh; .py stays .py after upgrade.
"""

from __future__ import annotations

import types
from pathlib import Path

import pytest

# Fixture catalogue directories.
FIXTURE_ROOT = Path(__file__).parent.parent / "fixtures" / "upgrade"
CAT_V1 = FIXTURE_ROOT / "catalogue_v1"
CAT_V2 = FIXTURE_ROOT / "catalogue_v2"
CAT_V3 = FIXTURE_ROOT / "catalogue_v3"

PACK_V1 = CAT_V1 / "packs" / "core"
PACK_V2 = CAT_V2 / "packs" / "core"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _args_upgrade(
    pack: str,
    catalogue: str,
    to_version: str,
    root: str = ".",
    skill: str | None = None,
    agent: str | None = None,
    hook: str | None = None,
    seed: str | None = None,
    command: str | None = None,
    dry_run: bool = False,
) -> types.SimpleNamespace:
    return types.SimpleNamespace(
        pack=pack,
        catalogue=catalogue,
        to_version=to_version,
        root=root,
        skill=skill,
        agent=agent,
        hook=hook,
        seed=seed,
        command=command,
        dry_run=dry_run,
    )


def _args_install(pack: str, catalogue: str, output: str) -> types.SimpleNamespace:
    # RFC-0012: dist-tree fixtures need `emit_install_routes=True`.
    return types.SimpleNamespace(
        pack=pack, catalogue=catalogue, output=output,
        emit_install_routes=True,
    )


def _run_upgrade(**kwargs) -> int:
    from agentbundle.commands.upgrade import run
    return run(_args_upgrade(**kwargs))


def _run_install(pack: str, catalogue: str, output: str) -> int:
    from agentbundle.commands.install import run
    return run(_args_install(pack, catalogue, output))


def _install_v1(root: Path) -> int:
    """Helper: install core 0.1.0 into root."""
    return _run_install("core", str(CAT_V1), str(root))


# ---------------------------------------------------------------------------
# 1. Whole-pack upgrade: installed-version updated; files are 0.2.0 content
# ---------------------------------------------------------------------------


def test_whole_pack_upgrade_updates_version_and_content(tmp_path):
    """Whole-pack upgrade from 0.1.0 to 0.2.0 must update installed-version and
    rewrite every Tier-1 projected file to the 0.2.0 content."""
    from agentbundle.config import load_state
    from agentbundle.render import render_pack

    rc = _install_v1(tmp_path)
    assert rc == 0, "install of 0.1.0 must succeed"

    rc = _run_upgrade(
        pack="core",
        catalogue=str(CAT_V2),
        to_version="0.2.0",
        root=str(tmp_path),
    )
    assert rc == 0, "whole-pack upgrade must succeed"

    # installed-version must be updated.
    state = load_state(tmp_path / ".agentbundle-state.toml")
    assert state.packs["core"].installed_version == "0.2.0"

    # All projected files must now have 0.2.0 content.
    v2_projection = render_pack(PACK_V2)
    for relpath, expected_bytes in v2_projection.items():
        on_disk = tmp_path / relpath
        assert on_disk.exists(), f"expected {relpath!r} to exist after upgrade"
        assert on_disk.read_bytes() == expected_bytes, (
            f"file {relpath!r} must contain 0.2.0 content"
        )


# ---------------------------------------------------------------------------
# 2. Per-primitive upgrade — parametrised over the five flag types
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "flag_attr, prim_name, prim_type, src_dir",
    [
        ("skill",   "work-loop",  "skill",        "skills"),
        ("agent",   "reviewer",   "agent",        "agents"),
        ("hook",    "pre-commit", "hook-body",    "hooks"),
        ("seed",    None,         "seed",         "seeds"),   # skip; no seeds in fixture
        ("command", "deploy",     "command",      "commands"),
    ],
)
def test_per_primitive_upgrade_moves_only_matching_files(
    tmp_path, flag_attr, prim_name, prim_type, src_dir
):
    """A per-primitive upgrade must update only files matching the primitive
    and record the override in state under [pack.core.<ptype>.<pname>]."""
    if prim_name is None:
        pytest.skip("no seed primitives in core fixture; skip")

    from agentbundle.commands.upgrade import _filter_for_primitive
    from agentbundle.config import load_state
    from agentbundle.render import render_pack
    from agentbundle import safety

    rc = _install_v1(tmp_path)
    assert rc == 0

    v1_projection = render_pack(PACK_V1)
    v2_projection = render_pack(PACK_V2)
    prim_paths = set(_filter_for_primitive(v2_projection, prim_name, src_dir).keys())
    # --hook co-moves the matching hook-wiring of the same name (spec AC #10).
    if flag_attr == "hook":
        prim_paths |= set(
            _filter_for_primitive(v2_projection, prim_name, "hook-wiring").keys()
        )
    non_prim_paths = set(v1_projection.keys()) - prim_paths

    # Capture v1 content for non-matching paths before upgrade.
    non_prim_before = {
        rp: (tmp_path / rp).read_bytes()
        for rp in non_prim_paths
        if (tmp_path / rp).exists()
    }

    kwargs: dict = dict(pack="core", catalogue=str(CAT_V2), to_version="0.2.0", root=str(tmp_path))
    kwargs[flag_attr] = prim_name
    rc = _run_upgrade(**kwargs)
    assert rc == 0, f"per-primitive upgrade --{flag_attr} {prim_name} must succeed"

    # Matching files must be 0.2.0 content.
    for relpath in sorted(prim_paths):
        on_disk = tmp_path / relpath
        assert on_disk.exists(), f"expected {relpath!r} after upgrade"
        assert on_disk.read_bytes() == v2_projection[relpath], (
            f"{relpath!r} must contain 0.2.0 content"
        )

    # Non-matching files must be 0.1.0 content (unchanged).
    for rp, before_bytes in non_prim_before.items():
        assert (tmp_path / rp).read_bytes() == before_bytes, (
            f"non-primitive file {rp!r} must not change"
        )

    # State must have primitive_versions entry.
    state = load_state(tmp_path / ".agentbundle-state.toml")
    pv = state.packs["core"].primitive_versions
    assert prim_type in pv, f"primitive_versions must contain {prim_type!r}"
    assert pv[prim_type].get(prim_name) == "0.2.0", (
        f"primitive_versions[{prim_type!r}][{prim_name!r}] must be '0.2.0'"
    )

    # Pack-level installed-version must NOT be updated on per-primitive upgrade.
    assert state.packs["core"].installed_version == "0.1.0", (
        "installed-version must stay at 0.1.0 for a per-primitive upgrade"
    )


# ---------------------------------------------------------------------------
# 3. Mixed-version warning: per-primitive upgrade then whole-pack → warning
# ---------------------------------------------------------------------------


def test_mixed_version_warning_on_whole_pack_after_per_primitive(tmp_path, capsys):
    """After upgrading --skill to 0.2.0, a whole-pack upgrade to 0.3.0 must
    print a warning to stderr about mixed-version primitives before proceeding."""
    rc = _install_v1(tmp_path)
    assert rc == 0

    # Per-primitive upgrade of skill to 0.2.0.
    rc = _run_upgrade(
        pack="core",
        catalogue=str(CAT_V2),
        to_version="0.2.0",
        root=str(tmp_path),
        skill="work-loop",
    )
    assert rc == 0

    # Clear captured output before the whole-pack upgrade.
    capsys.readouterr()

    # Whole-pack upgrade to 0.3.0 — must warn.
    rc = _run_upgrade(
        pack="core",
        catalogue=str(CAT_V3),
        to_version="0.3.0",
        root=str(tmp_path),
    )
    assert rc == 0

    captured = capsys.readouterr()
    assert "mixed-version" in captured.err, (
        "stderr must contain 'mixed-version' when pack has per-primitive overrides"
    )
    assert "work-loop" in captured.err, (
        "stderr must name the mixed-version primitive"
    )


# ---------------------------------------------------------------------------
# 4. Primitive-not-found: exit non-zero with expected message
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "flag_attr",
    ["skill", "agent", "hook", "seed", "command"],
)
def test_primitive_not_found_exits_nonzero(tmp_path, capsys, flag_attr):
    """``--<flag> foo`` where foo is not in the pack must exit non-zero with
    a one-line stderr ``primitive 'foo' not in pack core``."""
    rc = _install_v1(tmp_path)
    assert rc == 0

    kwargs = dict(
        pack="core",
        catalogue=str(CAT_V2),
        to_version="0.2.0",
        root=str(tmp_path),
    )
    kwargs[flag_attr] = "foo"
    rc = _run_upgrade(**kwargs)
    assert rc != 0, f"--{flag_attr} foo must exit non-zero"
    captured = capsys.readouterr()
    assert "primitive 'foo' not in pack core" in captured.err, (
        f"stderr must say \"primitive 'foo' not in pack core\"; got: {captured.err!r}"
    )


# ---------------------------------------------------------------------------
# 5. Hook-extension preservation: .sh stays .sh; .py stays .py
# ---------------------------------------------------------------------------


def test_hook_extension_preservation_sh(tmp_path):
    """Upgrading a .sh hook retains the .sh extension."""
    rc = _install_v1(tmp_path)
    assert rc == 0

    rc = _run_upgrade(
        pack="core",
        catalogue=str(CAT_V2),
        to_version="0.2.0",
        root=str(tmp_path),
        hook="pre-commit",
    )
    assert rc == 0

    # pre-commit.sh must exist on disk (not .sh.py or any other extension).
    sh_files = list(tmp_path.rglob("pre-commit.sh"))
    assert sh_files, "pre-commit.sh must still exist after --hook upgrade"

    # Must not have mutated extension.
    for f in sh_files:
        assert f.suffix == ".sh", f"expected .sh extension, got {f.suffix}"


def test_hook_upgrade_co_moves_wiring(tmp_path):
    """`--hook <name>` is atomic over hook-body AND matching hook-wiring.

    Per spec AC #10 the wiring co-moves with its body so a per-hook
    upgrade can never land a torn pair (a new hook script paired with
    the previous matcher/event wiring). The v1→v2 fixture diff includes
    a wiring change (`matcher = "Bash"` → `matcher = "Bash|Edit"`); a
    successful `--hook pre-commit --to 0.2.0` must produce the v2
    wiring content on disk.
    """
    rc = _install_v1(tmp_path)
    assert rc == 0

    rc = _run_upgrade(
        pack="core",
        catalogue=str(CAT_V2),
        to_version="0.2.0",
        root=str(tmp_path),
        hook="pre-commit",
    )
    assert rc == 0

    # The hook-wiring file is projected under `apm/core/.apm/hook-wiring/`.
    wiring_files = list(tmp_path.rglob("hook-wiring/pre-commit.toml"))
    assert wiring_files, "hook-wiring/pre-commit.toml must be co-moved"
    contents = wiring_files[0].read_text(encoding="utf-8")
    assert 'matcher = "Bash|Edit"' in contents, (
        f"--hook pre-commit must co-move wiring; got:\n{contents}"
    )


def test_hook_extension_preservation_py(tmp_path):
    """Upgrading a .py hook retains the .py extension."""
    rc = _install_v1(tmp_path)
    assert rc == 0

    rc = _run_upgrade(
        pack="core",
        catalogue=str(CAT_V2),
        to_version="0.2.0",
        root=str(tmp_path),
        hook="lint",
    )
    assert rc == 0

    py_files = list(tmp_path.rglob("lint.py"))
    assert py_files, "lint.py must still exist after --hook lint upgrade"
    for f in py_files:
        assert f.suffix == ".py", f"expected .py extension, got {f.suffix}"


# ---------------------------------------------------------------------------
# 6. Pack-not-installed: exit non-zero with message
# ---------------------------------------------------------------------------


def test_pack_not_installed_exits_nonzero(tmp_path, capsys):
    """Upgrading a pack that was never installed must exit non-zero."""
    # No install — empty state.
    rc = _run_upgrade(
        pack="core",
        catalogue=str(CAT_V2),
        to_version="0.2.0",
        root=str(tmp_path),
    )
    assert rc != 0
    captured = capsys.readouterr()
    assert "not installed" in captured.err


# ---------------------------------------------------------------------------
# 7. Success recap — upgrade must print a one-line recap to stdout on
#    success, mirroring install/uninstall. Regression: shipped silent in
#    cd4f3e58; users couldn't tell whether an upgrade had taken effect.
# ---------------------------------------------------------------------------


def test_whole_pack_upgrade_prints_success_recap(tmp_path, capsys):
    """A successful whole-pack upgrade must emit a one-line recap on stdout
    naming the pack and the target version. Regression test for the
    silent-success bug — stdout must not be empty on the happy path."""
    rc = _install_v1(tmp_path)
    assert rc == 0
    capsys.readouterr()  # drop install output

    rc = _run_upgrade(
        pack="core",
        catalogue=str(CAT_V2),
        to_version="0.2.0",
        root=str(tmp_path),
    )
    assert rc == 0

    captured = capsys.readouterr()
    assert captured.out.strip(), (
        "whole-pack upgrade must print a non-empty recap to stdout"
    )
    last = captured.out.strip().splitlines()[-1]
    assert last.startswith("upgraded:"), (
        f"recap must start with 'upgraded:'; got: {last!r}"
    )
    assert "core" in last and "0.2.0" in last, (
        f"recap must name pack and target version; got: {last!r}"
    )


def test_per_primitive_upgrade_prints_success_recap(tmp_path, capsys):
    """A successful per-primitive upgrade must emit a one-line recap on stdout
    naming the pack, the primitive, and the target version."""
    rc = _install_v1(tmp_path)
    assert rc == 0
    capsys.readouterr()

    rc = _run_upgrade(
        pack="core",
        catalogue=str(CAT_V2),
        to_version="0.2.0",
        root=str(tmp_path),
        skill="work-loop",
    )
    assert rc == 0

    captured = capsys.readouterr()
    assert captured.out.strip(), (
        "per-primitive upgrade must print a non-empty recap to stdout"
    )
    last = captured.out.strip().splitlines()[-1]
    assert last.startswith("upgraded:"), (
        f"recap must start with 'upgraded:'; got: {last!r}"
    )
    assert "core" in last and "work-loop" in last and "0.2.0" in last, (
        f"recap must name pack, primitive, and target version; got: {last!r}"
    )


def test_filter_for_primitive_refuses_ambiguous_name():
    """If a pack would project both `<src_dir>/<name>/...` and
    `<src_dir>/<name>.<ext>` for the same primitive name, `_filter_for_primitive`
    refuses with ValueError — F-build's `validate_pack_uniqueness` already
    rejects this shape at build time, but the upgrade boundary checks again."""
    from agentbundle.commands.upgrade import _filter_for_primitive

    projection = {
        "apm/core/.apm/skills/foo/SKILL.md": b"dir form",
        "apm/core/.apm/skills/foo.md": b"file form",
    }
    import pytest
    with pytest.raises(ValueError, match="ambiguous"):
        _filter_for_primitive(projection, "foo", "skills")


# ---------------------------------------------------------------------------
# 8. Tier-2 companion-drop visibility (upgrade-companion-visibility spec)
#    A file edited since install is detected Tier-2 on upgrade: the adopter's
#    edit is preserved, the upstream goes to a `.upstream.<ext>` companion, and
#    the operator is TOLD (count + companion path) on stderr — closing the
#    silent-companion diagnosability gap. Regression-paired with the
#    test_tier_invariants.py harness (never-clobber + companion-exists).
# ---------------------------------------------------------------------------

# Anchor on the production-unique header phrase so the positive and negative
# tests bind to the same load-bearing string (they drift together if reworded).
_COMPANION_NOTICE = "were modified since install and kept as *.upstream.<ext> companions"


def _first_projected_on_disk(root: Path, pack_dir: Path) -> str:
    """Pick a relpath the pack projects that exists on disk after install."""
    from agentbundle.render import render_pack

    for relpath in sorted(render_pack(pack_dir)):
        if (root / relpath).exists():
            return relpath
    raise AssertionError("no projected file found on disk after install")


def test_upgrade_tier2_collision_surfaces_companion_path(tmp_path, capsys):
    """A file edited since install must, on upgrade: stay byte-for-byte the
    adopter's (never clobbered), gain a `.upstream.<ext>` companion holding the
    upstream content, AND have its companion path named on stderr with the
    'kept as *.upstream.<ext> companions' notice. [AC1, AC2]"""
    from agentbundle import safety
    from agentbundle.render import render_pack

    rc = _install_v1(tmp_path)
    assert rc == 0
    capsys.readouterr()  # drop install output

    target_rel = _first_projected_on_disk(tmp_path, PACK_V2)
    adopter_bytes = b"# adopter edits -- do not clobber\n"
    (tmp_path / target_rel).write_bytes(adopter_bytes)  # forces Tier-2

    rc = _run_upgrade(
        pack="core", catalogue=str(CAT_V2), to_version="0.2.0", root=str(tmp_path)
    )
    assert rc == 0, "upgrade over a Tier-2 collision must still succeed"

    # Never clobbered: the adopter's edit survives at the original path.
    assert (tmp_path / target_rel).read_bytes() == adopter_bytes, (
        "Tier-2 file must not be clobbered on upgrade"
    )

    # Upstream content went to the `.upstream.<ext>` companion.
    companion_rel = safety.companion_path(Path(target_rel))
    companion_on_disk = tmp_path / companion_rel
    assert companion_on_disk.exists(), f"expected companion {companion_rel}"
    assert companion_on_disk.read_bytes() == render_pack(PACK_V2)[target_rel], (
        "companion must hold the upstream (v2) content"
    )

    # The operator is TOLD: notice + count + the companion path on stderr.
    err = capsys.readouterr().err
    assert _COMPANION_NOTICE in err, (
        f"upgrade must announce the companion-drop on stderr; got: {err!r}"
    )
    assert "1 file(s)" in err, f"notice must name the count; got: {err!r}"
    assert companion_rel.as_posix() in err, (
        f"upgrade must name the companion path on stderr; got: {err!r}"
    )


def test_upgrade_without_collision_emits_no_companion_notice(tmp_path, capsys):
    """A clean install→upgrade (no adopter edits) is all Tier-1: no companion
    is dropped and no companion notice is printed. [AC3]"""
    rc = _install_v1(tmp_path)
    assert rc == 0
    capsys.readouterr()  # drop install output

    rc = _run_upgrade(
        pack="core", catalogue=str(CAT_V2), to_version="0.2.0", root=str(tmp_path)
    )
    assert rc == 0

    err = capsys.readouterr().err
    assert _COMPANION_NOTICE not in err, (
        f"a collision-free upgrade must not print a companion notice; got: {err!r}"
    )


def test_upgrade_multiple_tier2_collisions_counts_and_lists_all(tmp_path, capsys):
    """Two files edited since install must both be preserved + companioned, and
    the notice must report the count (`2 file(s)`) and enumerate both companion
    paths — pins the count rendering and the plural-path branch. [AC2]"""
    from agentbundle import safety
    from agentbundle.render import render_pack

    rc = _install_v1(tmp_path)
    assert rc == 0
    capsys.readouterr()

    on_disk = [rp for rp in sorted(render_pack(PACK_V2)) if (tmp_path / rp).exists()]
    assert len(on_disk) >= 2, "fixture must project at least two files"
    targets = on_disk[:2]
    for rp in targets:
        (tmp_path / rp).write_bytes(f"# adopter edit of {rp}\n".encode())

    rc = _run_upgrade(
        pack="core", catalogue=str(CAT_V2), to_version="0.2.0", root=str(tmp_path)
    )
    assert rc == 0

    err = capsys.readouterr().err
    assert "2 file(s)" in err, f"notice must report count 2; got: {err!r}"
    for rp in targets:
        companion_rel = safety.companion_path(Path(rp)).as_posix()
        assert companion_rel in err, (
            f"notice must list every companion path; missing {companion_rel}\n{err!r}"
        )
        # And every original is preserved (never clobbered).
        assert (tmp_path / rp).read_bytes() == f"# adopter edit of {rp}\n".encode()


def test_per_primitive_upgrade_surfaces_tier2_companion(tmp_path, capsys):
    """The companion notice also fires on a per-primitive (`--skill`) upgrade —
    the same shared walk handles both shapes. Edit a projected work-loop skill
    file, upgrade just that skill, and assert the companion + notice. [AC2]"""
    from agentbundle.commands.upgrade import _filter_for_primitive
    from agentbundle import safety
    from agentbundle.render import render_pack

    rc = _install_v1(tmp_path)
    assert rc == 0
    capsys.readouterr()

    skill_paths = [
        rp
        for rp in sorted(_filter_for_primitive(render_pack(PACK_V2), "work-loop", "skills"))
        if (tmp_path / rp).exists()
    ]
    assert skill_paths, "work-loop skill must project at least one file on disk"
    target_rel = skill_paths[0]
    (tmp_path / target_rel).write_bytes(b"# adopter-edited skill body\n")

    rc = _run_upgrade(
        pack="core", catalogue=str(CAT_V2), to_version="0.2.0",
        root=str(tmp_path), skill="work-loop",
    )
    assert rc == 0

    companion_rel = safety.companion_path(Path(target_rel))
    assert (tmp_path / companion_rel).exists(), "per-primitive upgrade must drop a companion"
    err = capsys.readouterr().err
    assert _COMPANION_NOTICE in err, f"per-primitive upgrade must announce it; got: {err!r}"
    assert companion_rel.as_posix() in err, f"must name the companion path; got: {err!r}"
    # Adopter edit preserved.
    assert (tmp_path / target_rel).read_bytes() == b"# adopter-edited skill body\n"


# ---------------------------------------------------------------------------
# Dry-run preview (projection-dry-run spec): read-only, writes nothing
# ---------------------------------------------------------------------------


def _snapshot_tree(root: Path) -> dict[str, bytes]:
    """Map every file under ``root`` to its bytes, for byte-identical asserts."""
    return {
        p.relative_to(root).as_posix(): p.read_bytes()
        for p in sorted(root.rglob("*"))
        if p.is_file()
    }


def test_dry_run_upgrade_tier2_collision_previews_companion_writes_nothing(
    tmp_path, capsys
):
    """AC1/AC4/AC6: a dry-run upgrade over an adopter-edited file previews the
    `companion`/tier-2 line (with the `-> *.upstream` target), exits 0, and
    leaves the tree + state byte-identical with no companion on disk."""
    from agentbundle import safety
    from agentbundle.commands.upgrade import _filter_for_primitive
    from agentbundle.render import render_pack

    rc = _install_v1(tmp_path)
    assert rc == 0
    capsys.readouterr()  # drain install output

    skill_paths = [
        rp
        for rp in sorted(_filter_for_primitive(render_pack(PACK_V1), "work-loop", "skills"))
        if (tmp_path / rp).exists()
    ]
    assert skill_paths, "work-loop skill must project at least one file on disk"
    target_rel = skill_paths[0]
    (tmp_path / target_rel).write_bytes(b"# adopter-edited skill body\n")

    before = _snapshot_tree(tmp_path)

    rc = _run_upgrade(
        pack="core", catalogue=str(CAT_V2), to_version="0.2.0",
        root=str(tmp_path), dry_run=True,
    )
    assert rc == 0, "dry-run upgrade must exit 0 even with a Tier-2 collision"

    out = capsys.readouterr().out
    companion_rel = safety.companion_path(Path(target_rel)).as_posix()
    assert "tier-2" in out, f"plan must use the greppable tier-2 label; got:\n{out}"
    assert "companion" in out, f"plan must name the companion action; got:\n{out}"
    assert f"{target_rel} -> {companion_rel}" in out, (
        f"Tier-2 line must show the companion target; got:\n{out}"
    )
    assert "Nothing written." in out, "summary must restate the no-write guarantee"

    # No-write invariant: tree + state byte-identical, no companion on disk.
    assert _snapshot_tree(tmp_path) == before, "dry-run upgrade must write nothing"
    assert not (tmp_path / companion_rel).exists(), (
        "dry-run must not drop the .upstream companion"
    )


def test_dry_run_upgrade_no_edits_previews_overwrite_writes_nothing(tmp_path, capsys):
    """AC1/AC3: a dry-run upgrade with no adopter edits lists the projected files
    with `overwrite`/tier-1 labels and target paths, exits 0, writes nothing."""
    rc = _install_v1(tmp_path)
    assert rc == 0
    capsys.readouterr()

    before = _snapshot_tree(tmp_path)

    rc = _run_upgrade(
        pack="core", catalogue=str(CAT_V2), to_version="0.2.0",
        root=str(tmp_path), dry_run=True,
    )
    assert rc == 0

    out = capsys.readouterr().out
    assert "overwrite" in out, f"unedited files must preview as overwrite; got:\n{out}"
    assert "tier-1" in out, f"plan must use the greppable tier-1 label; got:\n{out}"
    # A real projected path appears in the plan (the "where").
    state = __import__("agentbundle.config", fromlist=["load_state"]).load_state(
        tmp_path / ".agentbundle-state.toml"
    )
    a_path = sorted(state.packs["core"].files)[0]
    assert a_path in out, f"plan must show the target path {a_path!r}; got:\n{out}"

    assert _snapshot_tree(tmp_path) == before, "dry-run upgrade must write nothing"


def test_dry_run_upgrade_per_primitive_scopes_to_that_primitive(tmp_path, capsys):
    """AC1: `--dry-run --skill work-loop` previews only that skill's files;
    `--dry-run --skill bogus` still exits non-zero (primitive-not-found)."""
    from agentbundle.commands.upgrade import _filter_for_primitive
    from agentbundle.render import render_pack

    rc = _install_v1(tmp_path)
    assert rc == 0
    capsys.readouterr()

    before = _snapshot_tree(tmp_path)

    rc = _run_upgrade(
        pack="core", catalogue=str(CAT_V2), to_version="0.2.0",
        root=str(tmp_path), skill="work-loop", dry_run=True,
    )
    assert rc == 0
    out = capsys.readouterr().out

    skill_files = set(_filter_for_primitive(render_pack(PACK_V2), "work-loop", "skills"))
    assert skill_files, "fixture must project a work-loop skill"
    for rp in skill_files:
        assert rp in out, f"per-primitive plan must list {rp!r}; got:\n{out}"
    # A non-skill file (the reviewer agent) must NOT appear.
    agent_files = set(_filter_for_primitive(render_pack(PACK_V2), "reviewer", "agents"))
    for rp in agent_files:
        assert rp not in out, f"per-primitive plan must exclude {rp!r}; got:\n{out}"

    assert _snapshot_tree(tmp_path) == before, "dry-run must write nothing"

    # Primitive-not-found passes through as a non-zero pre-render refusal.
    rc = _run_upgrade(
        pack="core", catalogue=str(CAT_V2), to_version="0.2.0",
        root=str(tmp_path), skill="bogus", dry_run=True,
    )
    assert rc != 0, "a --dry-run for a missing primitive must still exit non-zero"
    assert _snapshot_tree(tmp_path) == before


def test_format_plan_line_shape():
    """AC3: the shared formatter renders the documented action/tier/path shape,
    and appends the `-> companion` suffix only for a Tier-2 line."""
    from agentbundle.commands._common import (
        format_plan_line,
        plan_action,
        summarize_plan,
    )
    from agentbundle.safety import Tier

    create = format_plan_line("create", "tier-1", ".claude/agents/foo.md")
    assert create.split() == ["create", "tier-1", ".claude/agents/foo.md"]
    assert "->" not in create

    comp = format_plan_line("companion", "tier-2", "AGENTS.md", "AGENTS.upstream.md")
    assert comp.startswith("companion")
    assert "tier-2" in comp
    assert comp.endswith("AGENTS.md -> AGENTS.upstream.md")

    # Action mapping is shared and mirrors a real run's write decision.
    assert plan_action(Tier.TIER_2, on_disk=True) == "companion"
    assert plan_action(Tier.TIER_1, on_disk=True) == "overwrite"
    assert plan_action(Tier.TIER_1, on_disk=False) == "create"

    summary = summarize_plan(["create", "create", "companion"])
    assert "2 create" in summary and "1 companion" in summary
    assert summary.endswith("Nothing written.")


def test_dry_run_upgrade_preflight_path_jail_passthrough(tmp_path):
    """AC5: a path-jail-violating projection under `upgrade --dry-run` is refused
    (non-zero), matching the real run's `write_jailed` refusal, and nothing is
    written outside the root."""
    from unittest import mock

    rc = _install_v1(tmp_path)
    assert rc == 0

    before = _snapshot_tree(tmp_path)
    # The v1 install used the dist-tree shape, so upgrade renders via
    # `render_pack`; patch it to return a projection that escapes the root.
    malicious = {"../../evil_dry_run.txt": b"evil"}
    with mock.patch("agentbundle.render.render_pack", return_value=malicious):
        rc = _run_upgrade(
            pack="core", catalogue=str(CAT_V2), to_version="0.2.0",
            root=str(tmp_path), dry_run=True,
        )
    assert rc != 0, "dry-run must surface the path-jail pre-flight failure"
    assert not (tmp_path / ".." / ".." / "evil_dry_run.txt").resolve().exists(), (
        "the escaping file must not be written even under dry-run"
    )
    assert _snapshot_tree(tmp_path) == before, "nothing may change"
