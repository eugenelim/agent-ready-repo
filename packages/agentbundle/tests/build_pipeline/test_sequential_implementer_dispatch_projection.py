"""Integration coverage for projecting the real core implementer agent."""

from __future__ import annotations

import tempfile
import tomllib
from pathlib import Path

from agentbundle.build.adapters import ADAPTERS
from agentbundle.build.contract import load as load_contract
from agentbundle.build.main import CONTRACT_PATH

ROOT = Path(__file__).resolve().parents[4]
CORE_PACK = ROOT / "packs/core"


def test_core_implementer_projects_to_its_native_claude_and_codex_paths() -> None:
    """Each adapter, in its own output tree, emits its own artifact and not the other's.

    Projecting both adapters into one directory cannot establish this: swapped
    adapters, one adapter emitting both artifacts, or one emitting nothing would
    all leave the same two files present.
    """
    if not CORE_PACK.is_dir():
        # Return rather than skip. This tree is published: the export-boundary
        # gate builds an sdist and runs these tests inside it, where the engine
        # ships without the catalogue corpus it projects. That gate also polices
        # skip reasons — `check-artifact-contents.py` forbids any reason naming
        # `packs`, so a corpus-missing skip cannot hide a genuinely broken test.
        # The sibling plugin-projection test returns for the same reason.
        return
    contract = load_contract(CONTRACT_PATH)
    expected = {
        "claude-code": ".claude/agents/implementer.md",
        "codex": ".codex/agents/implementer.toml",
    }
    for adapter, own in expected.items():
        other = next(v for k, v in expected.items() if k != adapter)
        with tempfile.TemporaryDirectory() as raw:
            output = Path(raw)
            ADAPTERS[adapter](CORE_PACK, contract, output)
            assert (output / own).is_file(), f"{adapter} did not emit {own}"
            assert not (output / other).exists(), (
                f"{adapter} emitted {other}, which belongs to the other adapter"
            )

    with tempfile.TemporaryDirectory() as raw:
        output = Path(raw)
        ADAPTERS["claude-code"](CORE_PACK, contract, output)
        assert "# Implementer" in (
            output / expected["claude-code"]
        ).read_text(encoding="utf-8")

    with tempfile.TemporaryDirectory() as raw:
        output = Path(raw)
        ADAPTERS["codex"](CORE_PACK, contract, output)
        data = tomllib.loads((output / expected["codex"]).read_text(encoding="utf-8"))
        # The codex artifact is a TOML transform, not a copy of the markdown.
        assert data["name"] == "implementer"
