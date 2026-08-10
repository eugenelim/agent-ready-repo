"""T1c: render wrapper over agentbundle.build."""

from __future__ import annotations

from pathlib import Path
from typing import Mapping

from agentbundle import render

PACKS_DIR = Path(__file__).resolve().parents[1] / "build_pipeline" / "fixtures" / "packs"


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
    # The three default recipes leave the marketplace + per-pack outputs.
    assert any("marketplace.json" in k for k in rendered)
    assert any(k.startswith("claude-plugins/core/") for k in rendered)
    assert any(k.startswith("apm/core/") for k in rendered)


def test_render_pack_to_dir_matches_rendered_bytes(tmp_path):
    """The directory API writes exactly the bytes returned by the memory API."""
    pack_path = PACKS_DIR / "core"
    via_render = tmp_path / "via-render"
    render.render_pack_to_dir(pack_path, via_render)
    assert _tree(via_render) == render.render_pack(pack_path)


def _tree(root: Path) -> dict[str, bytes]:
    out: dict[str, bytes] = {}
    for p in sorted(root.rglob("*")):
        if p.is_file():
            out[p.relative_to(root).as_posix()] = p.read_bytes()
    return out
