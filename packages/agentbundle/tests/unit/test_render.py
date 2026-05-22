"""T1c: render wrapper over agentbundle.build."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import Mapping

from agentbundle import render

REPO_ROOT = Path(__file__).resolve().parents[4]
PACKS_DIR = REPO_ROOT / "packs"


def test_list_adapters_matches_runtime_registry():
    from agentbundle.build import adapters

    assert isinstance(adapters.registry, Mapping)
    assert set(adapters.registry).issuperset(
        {"claude_code", "kiro", "copilot", "codex"}
    )
    assert tuple(render.list_adapters()) == tuple(sorted(adapters.registry.keys()))


def test_render_pack_returns_bytes_dict_for_core(tmp_path):
    """The library-first invariant: render returns the same bytes that
    `agentbundle.build.run_recipe` would write to disk."""
    pack_path = PACKS_DIR / "core"
    rendered = render.render_pack(pack_path)
    assert isinstance(rendered, dict)
    assert all(isinstance(v, bytes) for v in rendered.values())
    # The three RFC-0001 recipes leave the marketplace + per-pack outputs.
    assert any("marketplace.json" in k for k in rendered)
    assert any(k.startswith("claude-plugins/core/") for k in rendered)
    assert any(k.startswith("apm/core/") for k in rendered)


def test_render_pack_to_dir_byte_identical_to_make_build(tmp_path):
    """F-build parity: `render_pack_to_dir(core)` ↔ `make build PACK=core`."""
    pack_path = PACKS_DIR / "core"
    via_render = tmp_path / "via-render"
    render.render_pack_to_dir(pack_path, via_render)

    # Drive `make build PACK=core OUTPUT_DIR=<tmp>` so the two outputs
    # share the same recipe set.
    via_make = tmp_path / "via-make"
    via_make.mkdir()
    env = {"PATH": "/usr/bin:/bin:/usr/local/bin"}
    proc = subprocess.run(
        [
            "make",
            "-C",
            str(REPO_ROOT),
            "build",
            f"OUTPUT_DIR={via_make}",
            "PACK=core",
        ],
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stderr

    via_render_tree = _tree(via_render)
    via_make_tree = _tree(via_make)
    # `make build` writes for every pack — restrict comparison to core's
    # subtree under each top-level recipe directory.
    via_make_core = {
        k: v for k, v in via_make_tree.items()
        if "/core/" in k or k.endswith("/core") or k == "claude-plugins/marketplace.json"
    }
    via_render_core = {
        k: v for k, v in via_render_tree.items()
        if "/core/" in k or k.endswith("/core") or k == "claude-plugins/marketplace.json"
    }
    # Render only ran on one pack, so marketplace.json may have a single
    # entry vs make's multi-entry. Compare per-pack outputs separately.
    drop_marketplace = lambda d: {k: v for k, v in d.items() if k != "claude-plugins/marketplace.json"}
    assert drop_marketplace(via_render_core) == drop_marketplace(via_make_core)


def _tree(root: Path) -> dict[str, bytes]:
    out: dict[str, bytes] = {}
    for p in sorted(root.rglob("*")):
        if p.is_file():
            out[p.relative_to(root).as_posix()] = p.read_bytes()
    return out
