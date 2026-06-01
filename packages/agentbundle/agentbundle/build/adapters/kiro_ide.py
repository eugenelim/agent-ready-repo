"""kiro-ide adapter — projects primitives for the Kiro VS Code-fork IDE.

Targets the Kiro IDE, not the `kiro` CLI binary. Key differences from kiro-cli:
- Agents project as `.md` (body-as-prompt via gray-matter), using the
  `kiro-ide-agent-frontmatter-v0.9` mapping table with IDE tool ids.
- kiro-ide-hook is activated (event hooks via `.kiro.hook` files).
- hook-wiring is dropped — the IDE loader silently drops any agent
  carrying a `hooks` key (RFC-0022 E2).
- No CLI-only fields (`hooks`, `allowedTools`, `toolsSettings`,
  `mcpServers`) in agent output.

The deprecated `kiro` adapter is an alias for this module (T4).

--- CONTRACT GATE ---
T1 activation requires the Q6 probe outcome to be recorded in
`docs/specs/kiro-ide-hook/probes.md` before the contract version is
bumped to 0.9 and this adapter's projection is enabled. Until Q6 is
recorded, this module stub-delegates to kiro.py's JSON projection as
a placeholder (same observable behavior as the legacy `kiro` adapter).
Once Q6 is run:
  1. Record Q6 outcome in probes.md.
  2. Implement `.md` projection here (replace the delegation below).
  3. Bump `[contract] version` to `"0.9"` and add `[adapter.kiro-ide]`
     in `adapter.toml` (T1).
"""

from __future__ import annotations

import logging
from pathlib import Path

from agentbundle.build.adapters import kiro as _kiro

_LOG = logging.getLogger(__name__)


def project(pack_path: Path, contract: dict, output_root: Path) -> None:
    """Single-pack convenience wrapper. Delegates to `project_packs`."""
    project_packs([pack_path], contract, output_root)


def project_packs(pack_paths: list[Path], contract: dict, output_root: Path) -> None:
    """Project every pack in `pack_paths` using the kiro-ide adapter.

    NOTE: This is a pre-T1 stub. The Q6 probe gate has not yet been
    cleared; projection delegates to the existing kiro adapter behavior
    (JSON projection with IDE tool ids). When T1 lands (post-Q6), this
    function will be replaced with a proper .md projection implementation
    using `kiro-ide-agent-frontmatter-v0.9`.
    """
    _kiro.project_packs(pack_paths, contract, output_root)
