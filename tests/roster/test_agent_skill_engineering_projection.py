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

import importlib
import tomllib
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


def _declared_adapters() -> list[str]:
    """The adapters `pack.toml` actually declares.

    Resolved from the manifest rather than hard-coded, so widening
    `allowed-adapters` cannot outrun the boundary check AC17 attaches to it.
    """

    manifest = tomllib.loads((PACK_ROOT / "pack.toml").read_text(encoding="utf-8"))
    return list(manifest["pack"]["install"]["allowed-adapters"])


def _project(adapter: str, out: Path) -> dict[str, Path]:
    from agentbundle.build.contract import load as load_contract

    module = importlib.import_module(
        f"agentbundle.build.adapters.{adapter.replace('-', '_')}"
    )
    module.project(PACK_ROOT, load_contract(REPO_ROOT / "contracts" / "adapter.toml"), out)
    return {path.parent.name: path for path in out.rglob("SKILL.md")}


def test_every_declared_adapter_has_a_projector() -> None:
    """A declared adapter with no importable projector is an unprovable claim."""

    for adapter in _declared_adapters():
        importlib.import_module(
            f"agentbundle.build.adapters.{adapter.replace('-', '_')}"
        )


@pytest.mark.parametrize("adapter", _declared_adapters())
def test_projection_emits_every_declared_skill(
    adapter: str, tmp_path: Path
) -> None:
    assert set(_project(adapter, tmp_path)) == set(EXPECTED_BOUNDARIES)


@pytest.mark.parametrize("adapter", _declared_adapters())
def test_declared_boundaries_survive_projection(
    adapter: str, tmp_path: Path
) -> None:
    projected = _project(adapter, tmp_path)
    for skill, expected in EXPECTED_BOUNDARIES.items():
        assert _boundaries(projected[skill]) == expected, (adapter, skill)


@pytest.mark.parametrize("adapter", _declared_adapters())
def test_router_gains_no_write_authority_in_projection(
    adapter: str, tmp_path: Path
) -> None:
    """The inert router must not acquire `filesystem_write` on the way out."""

    projected = _project(adapter, tmp_path)
    assert "filesystem_write" not in projected[ROUTER_SKILL].read_text(encoding="utf-8")
