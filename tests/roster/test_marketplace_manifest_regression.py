"""Repository-specific marketplace roster assertions."""

from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def _marketplace() -> dict:
    path = REPO_ROOT / ".claude-plugin" / "marketplace.json"
    assert path.exists(), f"missing {path} — run make build-self first"
    return json.loads(path.read_text(encoding="utf-8"))


def test_name_is_agent_ready_repo() -> None:
    assert _marketplace()["name"] == "agent-ready-repo"


def test_every_plugin_has_source() -> None:
    missing = [
        plugin["name"]
        for plugin in _marketplace()["plugins"]
        if "source" not in plugin
    ]
    assert not missing, f"Plugins missing source: {missing}"
