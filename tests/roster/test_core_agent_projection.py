"""Repository-level drift coverage for every projected `packs/core` agent.

`.claude/agents/*.md` and `.codex/agents/*.toml` are *transformed* projections,
not byte copies of their `packs/core/.apm/agents/*.md` sources: the Claude
surface drops the `metadata:` frontmatter block and inserts an H1, and the Codex
surface is TOML. So no source-to-projection byte pin can express the invariant —
editing a source agent and skipping `make build-self` left both trees stale with
every gate green. The check renders the adapters from the current source and
compares that output instead.

Lives in `tests/roster/` rather than beside the pack because it reaches outside
`packs/core`: it loads the repository adapter contract, imports
`agentbundle.build`, and reads the projected `.claude/` and `.codex/` trees.
`pack-tests-stay-in-pack` rejects all three from a pack-local test.
"""

from __future__ import annotations

from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
PACK_ROOT = REPOSITORY_ROOT / "packs/core"
CONTRACT_PATH = (
    REPOSITORY_ROOT
    / "packages/agentbundle/agentbundle/_data/adapter.toml"
)


def test_self_hosted_agent_projections_match_current_core_sources(
    tmp_path: Path,
) -> None:
    """Require committed core-agent projections to match the adapter output."""
    from agentbundle.build import self_host
    from agentbundle.build.adapters import claude_code, codex
    from agentbundle.build.contract import load as load_contract

    assert PACK_ROOT.name in self_host.SELF_HOST_PACKS
    source_agents = {
        source.stem for source in (PACK_ROOT / ".apm/agents").glob("*.md")
    }
    assert source_agents

    contract = load_contract(CONTRACT_PATH)
    rendered_root = tmp_path / "rendered"
    for adapter in (claude_code, codex):
        adapter.project(PACK_ROOT, contract, rendered_root)

    for committed_dir, rendered_dir, extension in (
        (
            REPOSITORY_ROOT / ".claude/agents",
            rendered_root / ".claude/agents",
            ".md",
        ),
        (
            REPOSITORY_ROOT / ".codex/agents",
            rendered_root / ".codex/agents",
            ".toml",
        ),
    ):
        committed_agents = {path.stem for path in committed_dir.glob(f"*{extension}")}
        assert committed_agents == source_agents, committed_dir
        for agent in source_agents:
            committed = committed_dir / f"{agent}{extension}"
            rendered = rendered_dir / f"{agent}{extension}"
            assert committed.read_bytes() == rendered.read_bytes(), (
                f"{committed.relative_to(REPOSITORY_ROOT)} is stale; "
                "run: make build-self"
            )
