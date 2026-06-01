"""kiro-cli adapter — projects primitives for the `kiro` terminal binary.

Targets the `kiro` CLI, not the Kiro IDE. Key differences from kiro-ide:
- Agents project as `.json` with CLI short-name tool tokens
  (`read`, `grep`, `glob`, `write`, `shell`, `web_fetch`, `web_search`).
- hook-wiring is retained via `merge-into-agent-json` (same as the
  legacy `kiro` adapter).
- kiro-ide-hook is dropped (IDE-only primitive).

Projection logic is identical to the kiro adapter — the only difference
is the adapter contract block (`kiro-cli`) and frontmatter mapping table
(`kiro-cli-agent-frontmatter-v1.0`). This module adapts the contract so
kiro.py's projection functions run unchanged, rather than duplicating them.
"""

from __future__ import annotations

from pathlib import Path

from agentbundle.build.adapters import kiro as _kiro


def project(pack_path: Path, contract: dict, output_root: Path) -> None:
    """Single-pack convenience wrapper. Delegates to `project_packs`."""
    project_packs([pack_path], contract, output_root)


def project_packs(pack_paths: list[Path], contract: dict, output_root: Path) -> None:
    """Project every pack in `pack_paths` using the kiro-cli adapter block.

    Adapts the contract so kiro.py's projection functions read from
    `[adapter.kiro-cli]` rather than `[adapter.kiro]`. The frontmatter
    mapping table reference in the adapter block (`kiro-cli-agent-
    frontmatter-v1.0`) is preserved so CLI short-name tool tokens are
    emitted instead of the IDE ids.
    """
    adapted = _adapt_contract(contract)
    _kiro.project_packs(pack_paths, adapted, output_root)


def _adapt_contract(contract: dict) -> dict:
    """Return a shallow copy of *contract* where `adapter["kiro"]` is
    replaced by `adapter["kiro-cli"]`.

    This lets kiro.py's projection functions (which key on the "kiro"
    adapter block) run unchanged for the kiro-cli target without
    duplicating the projection logic.
    """
    adapted_adapter = dict(contract["adapter"])
    adapted_adapter["kiro"] = contract["adapter"]["kiro-cli"]
    adapted = dict(contract)
    adapted["adapter"] = adapted_adapter
    return adapted
