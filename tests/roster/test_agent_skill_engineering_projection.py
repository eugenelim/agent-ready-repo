"""AC17: declared skill boundaries survive the adapter projection.

This lives in the roster rather than the pack's own suite because it reads the
repository's `contracts/adapter.toml` and drives the build adapter — coverage
the pack-test boundary lint classifies as repository-level.

The pack's own `test_skill_boundaries_match_the_least_authority_contract`
asserts the `.apm/` source. That cannot see a projection which drops
`metadata`, which is exactly what AC17's "survive every supported projection
and are revalidated at the receiving surface" clause is about.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
PACK_ROOT = REPO_ROOT / "packs" / "agent-skill-engineering"
ROUTER_SKILL = "ase-okf-reference"
EXPECTED_BOUNDARIES = {
    "author-or-update-agent-skill": ["filesystem_read_untrusted", "filesystem_write"],
    "review-or-optimize-agent-skill": ["filesystem_read_untrusted", "filesystem_write"],
    ROUTER_SKILL: ["filesystem_read_untrusted"],
}


def _boundaries(path: Path) -> list[str]:
    _, raw, _ = path.read_text(encoding="utf-8").split("---\n", 2)
    parsed = yaml.safe_load(raw)
    assert isinstance(parsed, dict), path
    return list(parsed["metadata"]["boundaries"])


@pytest.fixture(scope="module")
def projected(tmp_path_factory: pytest.TempPathFactory) -> dict[str, Path]:
    """Project the pack once through the real claude-code adapter."""

    from agentbundle.build.adapters.claude_code import project
    from agentbundle.build.contract import load as load_contract

    out = tmp_path_factory.mktemp("ase-projection")
    project(PACK_ROOT, load_contract(REPO_ROOT / "contracts" / "adapter.toml"), out)
    return {path.parent.name: path for path in out.rglob("SKILL.md")}


def test_projection_emits_every_declared_skill(projected: dict[str, Path]) -> None:
    assert set(projected) == set(EXPECTED_BOUNDARIES)


@pytest.mark.parametrize("skill", sorted(EXPECTED_BOUNDARIES))
def test_declared_boundaries_survive_projection(
    skill: str, projected: dict[str, Path]
) -> None:
    assert _boundaries(projected[skill]) == EXPECTED_BOUNDARIES[skill]


def test_router_gains_no_write_authority_in_projection(
    projected: dict[str, Path],
) -> None:
    """The inert router must not acquire `filesystem_write` on the way out."""

    assert "filesystem_write" not in projected[ROUTER_SKILL].read_text(encoding="utf-8")
