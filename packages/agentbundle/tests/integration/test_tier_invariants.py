"""T15: cross-cutting Tier-1/2/3 invariant integration test.

This module is the single proof that every write-capable subcommand
honours the Tier contract on the same shared fixture. The per-command
tests (T2–T12) cover happy / sad paths; this test pins the **invariant
matrix**: for each write-capable subcommand, against the same
brownfield-ish fixture:

  - Tier-1 paths may change.
  - Tier-2 paths produce a `.upstream.<ext>` companion **and** the
    original is byte-identical before and after.
  - Tier-3 paths are byte-identical before and after.

The fixture is the upgrade catalogue's v1 `core` pack which carries one
`.sh` hook and one `.py` hook — pinning hook extension preservation
across `render` and `upgrade`.

Subcommands under test:
  scaffold, install, render, adapt, init-state, upgrade, uninstall
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path
from typing import Callable

import pytest

PACKAGE_ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = PACKAGE_ROOT.parent.parent
UPGRADE_CATALOGUE_V1 = (
    PACKAGE_ROOT
    / "tests"
    / "fixtures"
    / "upgrade"
    / "catalogue_v1"
)


# ---------------------------------------------------------------------------
# Shared fixture builder
# ---------------------------------------------------------------------------


# A relpath the upgrade fixture's `core` pack actually projects under both
# the `apm/` and `claude-plugins/` recipe trees — used to construct a
# realistic Tier-2 collision.
_TIER2_PROJECTED_PATH = "apm/core/.apm/agents/reviewer.md"


def _build_brownfield(tmp_path: Path) -> dict[str, bytes]:
    """Stage `tmp_path` as a brownfield adopter repo and return the
    pre-existing Tier-2/Tier-3 content for later byte-identity assertions.

    Layout:
      <root>/
        AGENTS.md                                 — Tier-3 (no projection
                                                    touches this)
        src/app.py                                — Tier-3
        docs/notes.md                             — Tier-3
        apm/core/.apm/agents/reviewer.md          — Tier-2 (adopter-edited
                                                    copy of a real projected
                                                    path; install/upgrade
                                                    must produce an
                                                    .upstream.<ext>
                                                    companion next to it)
    """
    pre = {
        "AGENTS.md": b"# adopter edits -- do not clobber\n",
        "src/app.py": b"print('adopter code')\n",
        "docs/notes.md": b"adopter docs\n",
        _TIER2_PROJECTED_PATH: b"# adopter-edited reviewer agent\n",
    }
    for relpath, content in pre.items():
        target = tmp_path / relpath
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
    return pre


def _snapshot_tree(root: Path) -> dict[str, bytes]:
    out: dict[str, bytes] = {}
    for p in sorted(root.rglob("*")):
        if p.is_file():
            out[p.relative_to(root).as_posix()] = p.read_bytes()
    return out


def _tier3_relpaths(pre: dict[str, bytes]) -> list[str]:
    """Tier-3 = paths that no pack projection touches."""
    return [p for p in pre if p in ("AGENTS.md", "src/app.py", "docs/notes.md")]


# ---------------------------------------------------------------------------
# Subcommand invocation helpers — each calls the command's `run(args)`
# directly so we can drive the shared fixture without subprocess overhead.
# ---------------------------------------------------------------------------


def _run_scaffold(root: Path, pack_dir: Path) -> int:
    from agentbundle.commands.scaffold import run

    args = argparse.Namespace(
        pack=pack_dir.name,
        packs_dir=str(pack_dir.parent),
        output=str(root),
    )
    return run(args)


def _run_install(root: Path, pack_dir: Path) -> int:
    from agentbundle.commands.install import run

    catalogue = str(pack_dir.parent.parent)  # catalogue_v1/
    args = argparse.Namespace(
        pack=pack_dir.name,
        catalogue=catalogue,
        output=str(root),
    )
    return run(args)


def _run_render(root: Path, pack_dir: Path) -> int:
    """Run `render` against `root` after installing once.

    Render's Tier-2 awareness triggers only when `--output` already has
    a `.agentbundle-state.toml` — the "self-host into adopter root" use
    case. Without that, render's contract is "write the projection
    wholesale" (the `make build` semantic). Chain install → render so
    the T15 row exercises the Tier-honouring branch.
    """
    from agentbundle.commands.install import run as install_run
    from agentbundle.commands.render import run

    install_args = argparse.Namespace(
        pack=pack_dir.name,
        catalogue=str(pack_dir.parent.parent),
        output=str(root),
    )
    install_run(install_args)

    args = argparse.Namespace(
        pack_path=str(pack_dir),
        output=str(root),
        target=None,
        self_host=True,
    )
    return run(args)


def _run_init_state(root: Path, pack_dir: Path) -> int:
    from agentbundle.commands.init_state import run

    args = argparse.Namespace(
        pack=pack_dir.name,
        packs_dir=str(pack_dir.parent),
        root=str(root),
    )
    return run(args)


def _run_adapt_no_values(root: Path, pack_dir: Path) -> int:
    """Negative-invariant row: `adapt` without --values-from must not
    touch Tier-1 content (only `.adapt-pending.md` may be written)."""
    from agentbundle.commands.adapt import run

    args = argparse.Namespace(
        values_from=None,
        ci=False,
        root=str(root),
    )
    return run(args)


def _run_uninstall(root: Path, pack_dir: Path) -> int:
    # uninstall presumes install ran first — chain it.
    from agentbundle.commands.install import run as install_run
    from agentbundle.commands.uninstall import run

    install_args = argparse.Namespace(
        pack=pack_dir.name,
        catalogue=str(pack_dir.parent.parent),
        output=str(root),
    )
    install_run(install_args)

    args = argparse.Namespace(
        pack=pack_dir.name,
        root=str(root),
    )
    return run(args)


def _run_upgrade(root: Path, pack_dir: Path) -> int:
    """upgrade presumes a prior install — chain v1 install then v2 upgrade."""
    from agentbundle.commands.install import run as install_run
    from agentbundle.commands.upgrade import run

    install_args = argparse.Namespace(
        pack=pack_dir.name,
        catalogue=str(pack_dir.parent.parent),  # catalogue_v1
        output=str(root),
    )
    install_run(install_args)

    catalogue_v2 = pack_dir.parent.parent.parent / "catalogue_v2"
    args = argparse.Namespace(
        pack=pack_dir.name,
        to_version="0.2.0",
        skill=None,
        agent=None,
        hook=None,
        seed=None,
        command=None,
        catalogue=str(catalogue_v2),
        root=str(root),
    )
    return run(args)


# ---------------------------------------------------------------------------
# Parametrised matrix
# ---------------------------------------------------------------------------


SubcommandRunner = Callable[[Path, Path], int]


WRITE_CAPABLE: list[tuple[str, SubcommandRunner]] = [
    ("scaffold", _run_scaffold),
    ("install", _run_install),
    ("render", _run_render),
    ("init-state", _run_init_state),
    ("uninstall", _run_uninstall),
    ("upgrade", _run_upgrade),
]


@pytest.mark.parametrize("name,runner", WRITE_CAPABLE, ids=[n for n, _ in WRITE_CAPABLE])
def test_tier_invariants_per_subcommand(tmp_path: Path, name: str, runner: SubcommandRunner):
    """For each write-capable subcommand on the shared brownfield fixture:

      - Tier-2 originals are byte-identical before and after.
      - Tier-3 paths are byte-identical before and after.
    """
    pack_dir = UPGRADE_CATALOGUE_V1 / "packs" / "core"
    pre = _build_brownfield(tmp_path)

    runner(tmp_path, pack_dir)

    # Tier-2: the projected path's adopter-edited original is byte-identical;
    # AND for commands that actually project this path, a `.upstream.<ext>`
    # companion exists next to it. Subcommands that don't write any
    # projection (init-state, uninstall on an empty install) are exempt
    # from the companion-exists clause but still must preserve the original.
    tier2_path = tmp_path / _TIER2_PROJECTED_PATH
    assert tier2_path.exists(), f"{name}: lost Tier-2 file {_TIER2_PROJECTED_PATH}"
    assert tier2_path.read_bytes() == pre[_TIER2_PROJECTED_PATH], (
        f"{name}: clobbered Tier-2 file {_TIER2_PROJECTED_PATH}"
    )
    if name in ("install", "render", "upgrade"):
        from agentbundle.safety import companion_path as _comp

        comp = tmp_path / _comp(Path(_TIER2_PROJECTED_PATH))
        assert comp.exists(), (
            f"{name}: Tier-2 collision did not produce companion {comp.name}"
        )

    # Tier-3: adopter-only files untouched.
    for relpath in _tier3_relpaths(pre):
        target = tmp_path / relpath
        assert target.exists(), f"{name}: lost Tier-3 file {relpath}"
        assert target.read_bytes() == pre[relpath], (
            f"{name}: modified Tier-3 file {relpath}"
        )


def test_adapt_without_values_makes_no_tier1_changes(tmp_path: Path):
    """Negative-invariant row: read-only `adapt` writes nothing except
    possibly `.adapt-pending.md` (which is itself a Tier-1 path)."""
    pack_dir = UPGRADE_CATALOGUE_V1 / "packs" / "core"
    pre = _build_brownfield(tmp_path)

    # Install so there's a projection to scan over.
    _run_install(tmp_path, pack_dir)
    after_install = _snapshot_tree(tmp_path)

    _run_adapt_no_values(tmp_path, pack_dir)
    after_adapt = _snapshot_tree(tmp_path)

    # Every file present after install is byte-identical after adapt,
    # except possibly `.adapt-pending.md` (which adapt may add or update).
    diffs = {
        k: (after_install.get(k), after_adapt.get(k))
        for k in set(after_install) | set(after_adapt)
        if after_install.get(k) != after_adapt.get(k)
    }
    assert set(diffs).issubset({".adapt-pending.md"}), (
        f"adapt without --values-from modified more than .adapt-pending.md: "
        f"{sorted(diffs)}"
    )


def test_hook_extension_preservation_through_install(tmp_path: Path):
    """`.sh` hooks remain `.sh`; `.py` hooks remain `.py`."""
    pack_dir = UPGRADE_CATALOGUE_V1 / "packs" / "core"
    _build_brownfield(tmp_path)
    _run_install(tmp_path, pack_dir)

    # F-build projects hooks under each per-pack recipe output —
    # `claude-plugins/<pack>/tools/hooks/` and `apm/<pack>/.apm/hooks/`.
    # Either path is acceptable; the invariant is that the extensions
    # round-trip from source.
    all_hooks = list(tmp_path.rglob("*"))
    hook_paths = [
        p for p in all_hooks
        if p.is_file() and ("/hooks/" in p.as_posix() or "/.apm/hooks/" in p.as_posix())
    ]
    extensions = sorted({p.suffix for p in hook_paths})
    assert ".sh" in extensions, f"expected a .sh hook; got {extensions}"
    assert ".py" in extensions, f"expected a .py hook; got {extensions}"


def test_path_jail_refuses_escape_to_parent_directory(tmp_path: Path):
    """A write whose resolved target escapes the configured root must be
    refused with `PathJailError` — the rail every command depends on."""
    from agentbundle.safety import PathJailError, write_jailed

    with pytest.raises(PathJailError, match="refusing to write outside"):
        write_jailed(tmp_path, "../escaped.txt", b"x")
