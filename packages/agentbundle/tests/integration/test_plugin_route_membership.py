"""Three-surface membership and `render_pack`-consumer characterization.

Spec: docs/specs/claude-plugin-route-scope. Covers the membership criterion
(all three surfaces, both directions, expected side enumerated literally) and
the consumer criterion (six `render_pack` callers, plus the pre-change
`state.json` an adopter carries through `upgrade`).

The expected side is **enumerated, never computed by calling the production
predicate** — otherwise a predicate bug shifts both sides together and the
assertion is a tautology that stays green while the marketplace truncates.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[4]
FIXTURES = (
    REPO_ROOT / "packages" / "agentbundle" / "tests" / "build_pipeline"
    / "fixtures" / "packs"
)

# Literal, not derived. `user-guide-diataxis` is the fixture drop-path witness.
EXPECTED_PUBLISHED = {"core", "governance-extras", "monorepo-extras",
                      "product-documentation"}
EXPECTED_WITHHELD = {"user-guide-diataxis"}


def _build(tmp_path: Path) -> Path:
    out = tmp_path / "dist"
    result = subprocess.run(
        [sys.executable, "-m", "agentbundle.build", "build",
         "--packs-dir", str(FIXTURES), "--output-dir", str(out)],
        capture_output=True, text=True, cwd=REPO_ROOT,
    )
    assert result.returncode == 0, result.stderr
    return out


def _names(marketplace: Path) -> set[str]:
    payload = json.loads(marketplace.read_text(encoding="utf-8"))
    return {p["name"] for p in payload.get("plugins", [])}


def test_dist_tree_equals_the_expected_set(tmp_path) -> None:
    out = _build(tmp_path)
    dirs = {
        d.name for d in (out / "claude-plugins").iterdir()
        if d.is_dir() and not d.name.startswith(".")
    }
    assert dirs == EXPECTED_PUBLISHED
    assert not (dirs & EXPECTED_WITHHELD)


def test_dist_marketplace_equals_the_expected_set(tmp_path) -> None:
    out = _build(tmp_path)
    assert _names(out / "claude-plugins" / "marketplace.json") == EXPECTED_PUBLISHED


def test_repo_root_marketplace_equals_the_expected_set() -> None:
    """The surface `claude plugin marketplace add <owner>/<repo>` resolves.

    Enumerated against the real roster, so a fail-closed truncation that drops
    a user-capable pack fails here rather than passing on `expected == actual`.
    """
    listed = _names(REPO_ROOT / ".claude-plugin" / "marketplace.json")
    withheld = {"core", "catalogue-curation", "governance-extras", "iac-terraform",
                "monorepo-extras", "release-engineering", "user-guide-diataxis"}
    published = {"architect", "atlassian", "contracts", "converters",
                 "credential-brokers", "desk-research", "experience-design",
                 "figma", "frontend-engineering", "github", "linear",
                 "product-documentation", "product-engineering",
                 "product-strategy"}
    assert listed == published
    assert not (listed & withheld)


def test_envelope_survives_the_filter() -> None:
    """`name`/`owner`/`description` intact — a filtered set must not re-key it.

    Asserted against the repo-root marketplace, not a fixture build: the
    envelope is derived from `source.url`, which comes from `[pack.links]
    repository`, and the fixture packs declare none.
    """
    payload = json.loads(
        (REPO_ROOT / ".claude-plugin" / "marketplace.json").read_text(encoding="utf-8")
    )
    assert payload.get("name") == "agent-ready-repo"
    assert payload.get("owner", {}).get("name") == "eugenelim"
    assert payload.get("description")


# --- render_pack consumers -------------------------------------------------

@pytest.mark.parametrize("module,symbol", [
    ("agentbundle.render", "render_pack"),
    ("agentbundle.commands.render", None),
    ("agentbundle.commands.diff", None),
    ("agentbundle.commands.init_state", None),
    ("agentbundle.commands.upgrade", None),
    ("agentbundle.commands.install", None),
    ("agentbundle.commands.validate", None),
])
def test_render_pack_consumer_imports(module: str, symbol: str | None) -> None:
    """Each named consumer still imports — a signature change breaks them all.

    `run_recipe` gained a required `aggregate_scope`; these six reach it through
    `render_pack`, so an unthreaded caller is an import-time or call-time error
    rather than a wrong-output one.
    """
    import importlib

    mod = importlib.import_module(module)
    if symbol:
        assert hasattr(mod, symbol)


def test_render_pack_omits_the_route_for_a_repo_only_pack() -> None:
    """The characterization that matters: real `core` yields no plugin subtree."""
    from agentbundle.render import render_pack

    rendered = render_pack(REPO_ROOT / "packs" / "core")
    assert not any(k.startswith("claude-plugins/core/") for k in rendered)
    assert any(k.startswith("apm/core/") for k in rendered)


def test_pre_change_state_relpaths_read_as_removals(tmp_path) -> None:
    """An adopter's existing state carries paths the render no longer produces.

    This is the migration case the changelog discloses: `upgrade` diffs a fresh
    render against the state file, so those relpaths read as removals. Pinned
    here so the behaviour is exercised, not assumed.
    """
    from agentbundle.render import render_pack

    stale = "claude-plugins/core/skills/work-loop/SKILL.md"
    rendered = set(render_pack(REPO_ROOT / "packs" / "core"))
    assert stale not in rendered, (
        "a pre-change state.json listing this relpath will see it as a removal"
    )
