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
