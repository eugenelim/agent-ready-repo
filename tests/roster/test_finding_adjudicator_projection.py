"""Repository-level projection coverage for the `finding-adjudicator` agent.

Lives in `tests/roster/` rather than beside the pack because it reaches outside
`packs/core`: the seven-adapter construction matrix loads the repository adapter
contract and imports `agentbundle.build`, and the self-host assertions read the
projected `.claude/`, `.codex/`, and `.agents/` trees. `pack-tests-stay-in-pack`
rejects both from a pack-local test. Pack-local contract coverage for the same
primitive stays in
`packs/core/tests/pack/test_finding_adjudication_contract.py`.
"""

from __future__ import annotations

import json
import re
import shutil
import tomllib
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
PACK_ROOT = REPOSITORY_ROOT / "packs/core"
AGENT = PACK_ROOT / ".apm/agents/finding-adjudicator.md"
CONTRACT_PATH = (
    REPOSITORY_ROOT
    / "packages/agentbundle/agentbundle/_data/adapter.toml"
)
FINDING_ADJUDICATION = (
    PACK_ROOT / ".apm/skills/work-loop/references/finding-adjudication.md"
)


def _frontmatter_text(path: Path) -> str:
    """Return the projected markdown agent's frontmatter block."""
    text = path.read_text(encoding="utf-8")
    parts = text.split("---", 2)
    assert len(parts) == 3
    return parts[1]


def test_finding_adjudicator_projects_read_only_across_all_adapters(
    tmp_path: Path,
) -> None:
    """Project the real source agent and pin each adapter's capability shape."""
    from agentbundle.build.adapters import (
        claude_code,
        codex,
        copilot,
        cursor,
        gemini,
        kiro_cli,
        kiro_ide,
    )
    from agentbundle.build.contract import load as load_contract

    pack = tmp_path / "pack"
    agent_dir = pack / ".apm" / "agents"
    agent_dir.mkdir(parents=True)
    shutil.copyfile(AGENT, agent_dir / AGENT.name)
    contract = load_contract(CONTRACT_PATH)

    outputs: dict[str, Path] = {}
    for name, adapter in (
        ("claude", claude_code),
        ("kiro-ide", kiro_ide),
        ("kiro-cli", kiro_cli),
        ("copilot", copilot),
        ("codex", codex),
        ("cursor", cursor),
        ("gemini", gemini),
    ):
        output = tmp_path / f"out-{name}"
        adapter.project(pack, contract, output)
        outputs[name] = output

    claude = _frontmatter_text(
        outputs["claude"] / ".claude/agents/finding-adjudicator.md"
    )
    # Anchored to the whole line: an unterminated `in` substring is satisfied by
    # a widened `tools: Read, Grep, Bash`, which AC16 requires this matrix to
    # fail on.
    assert re.search(r"^tools: Read, Grep$", claude, re.M), claude
    # claude-code projects agents byte-for-byte, so the portable `skills: []`
    # opt-out is the only thing that may appear here; Kiro's consumer-native
    # `resources` would be invalid Claude Code frontmatter.
    assert "skills: []" in claude
    assert "resources" not in claude

    kiro_ide_agent = _frontmatter_text(
        outputs["kiro-ide"] / ".kiro/agents/finding-adjudicator.md"
    )
    assert "tools: [read_file, grep_search]" in kiro_ide_agent
    assert "resources:" not in kiro_ide_agent
    # `skills` is Claude Code frontmatter Kiro cannot read; it is consumed as
    # the injection opt-out and must not pass through to the projected agent.
    assert "skills" not in kiro_ide_agent

    kiro_cli_agent = json.loads(
        (
            outputs["kiro-cli"]
            / ".kiro/agents/finding-adjudicator.json"
        ).read_text(encoding="utf-8")
    )
    assert kiro_cli_agent["tools"] == ["read", "grep"]
    assert "resources" not in kiro_cli_agent
    assert "skills" not in kiro_cli_agent

    copilot_agent = _frontmatter_text(
        outputs["copilot"]
        / ".github/agents/finding-adjudicator.agent.md"
    )
    assert re.search(r"^tools: Read, Grep$", copilot_agent, re.M), copilot_agent

    codex_agent = tomllib.loads(
        (
            outputs["codex"] / ".codex/agents/finding-adjudicator.toml"
        ).read_text(encoding="utf-8")
    )
    assert codex_agent["sandbox_mode"] == "read-only"
    assert codex_agent["features"]["shell_tool"] is True
    assert codex_agent["web_search"] == "disabled"
    assert "tools" not in codex_agent
    assert (
        "whichever read-only capabilities you have"
        in codex_agent["developer_instructions"]
    )
    assert (
        "Never run project code, an evidence gate"
        in codex_agent["developer_instructions"]
    )
    assert re.search(
        r"instruction-level prohibition that\s+binds you whatever your capabilities are",
        codex_agent["developer_instructions"],
    )

    cursor_agent = _frontmatter_text(
        outputs["cursor"] / ".cursor/agents/finding-adjudicator.md"
    )
    assert "readonly: true" in cursor_agent
    assert "tools:" not in cursor_agent

    gemini_agent = _frontmatter_text(
        outputs["gemini"] / ".gemini/agents/finding-adjudicator.md"
    )
    assert "tools: [read_file, grep_search]" in gemini_agent

    # No consumer but Claude Code carries `skills`, and none may gain a skill
    # or resource surface from this primitive. copilot/codex/cursor/gemini drop
    # it by iterating the contract mapping; both Kiro flavors consume it as the
    # injection opt-out. Assert the emitted shape rather than the mechanism so
    # a future adapter that starts passing frontmatter through still fails here.
    for adapter_name, emitted in (
        ("kiro-ide", kiro_ide_agent),
        ("copilot", copilot_agent),
        ("cursor", cursor_agent),
        ("gemini", gemini_agent),
    ):
        assert "skills" not in emitted, adapter_name
        assert "resources" not in emitted, adapter_name
    assert "skills" not in codex_agent
    assert "resources" not in codex_agent


def test_self_hosted_adjudicator_projections_exist() -> None:
    """Require source regeneration to publish the new primitive locally."""
    assert (REPOSITORY_ROOT / ".claude/agents/finding-adjudicator.md").is_file()
    assert (REPOSITORY_ROOT / ".codex/agents/finding-adjudicator.toml").is_file()
    for adapter_root in (".agents", ".claude"):
        projected = (
            REPOSITORY_ROOT
            / adapter_root
            / "skills/work-loop/references/finding-adjudication.md"
        )
        assert projected.read_bytes() == FINDING_ADJUDICATION.read_bytes()
