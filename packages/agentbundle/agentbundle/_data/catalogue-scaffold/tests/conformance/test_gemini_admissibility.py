"""Portable Gemini adapter rules over every pack in a catalogue."""

from __future__ import annotations

import tomllib
from importlib.resources import files
from pathlib import Path

CATALOGUE_ROOT = Path(__file__).resolve().parents[2]
PACKS_DIR = CATALOGUE_ROOT / "packs"


def _adapter_contract() -> dict:
    """Load the runtime adapter contract from the installed engine data."""
    resource = files("agentbundle").joinpath("_data", "adapter.toml")
    return tomllib.loads(resource.read_text(encoding="utf-8"))


def _pack_dirs() -> list[Path]:
    return sorted(
        path
        for path in PACKS_DIR.iterdir()
        if path.is_dir()
        and not path.name.startswith("_")
        and (path / "pack.toml").is_file()
    )


def test_every_declared_agent_tool_is_mapped() -> None:
    declared: set[str] = set()
    for agent_path in PACKS_DIR.glob("*/.apm/agents/*.md"):
        for line in agent_path.read_text(encoding="utf-8").splitlines():
            if line.startswith("tools:"):
                declared.update(
                    item.strip()
                    for item in line.split(":", 1)[1].split(",")
                    if item.strip()
                )
    if not declared:
        return
    contract = _adapter_contract()
    values = contract["frontmatter-mapping"]["gemini-agent-frontmatter"]["tools"][
        "values"
    ]
    assert declared <= set(values), f"unmapped agent tools: {declared - set(values)}"


def test_every_compatible_pack_admits_gemini_in_both_scopes() -> None:
    from agentbundle.commands.install import _resolve_target_adapter

    for pack_dir in _pack_dirs():
        data = tomllib.loads((pack_dir / "pack.toml").read_text(encoding="utf-8"))
        pack = data["pack"]
        allowed = pack.get("install", {}).get("allowed-adapters")
        if allowed is not None and "gemini" not in allowed:
            continue
        contract_version = pack.get("adapter-contract", {}).get("version", "0.13")
        for scope in ("repo", "user"):
            resolved = _resolve_target_adapter(
                pack_dir,
                scope=scope,
                adapter="gemini",
                allowed_adapters=allowed,
                contract_version=contract_version,
                command_name="install",
            )
            assert resolved == "gemini", f"{pack_dir.name} @ {scope}"
