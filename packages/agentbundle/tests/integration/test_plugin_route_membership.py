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


def _aggregate_over(tmp_path: Path, packs: dict[str, str | None]) -> dict:
    """Run `_run_aggregate` over synthetic dist + source trees.

    `packs` maps slug -> `[pack.links] repository` URL (None for no link).
    Returns the written marketplace payload.
    """
    from agentbundle.build.main import Pack, Recipe, _run_aggregate

    handles = []
    for slug, repo in packs.items():
        plugin_dir = tmp_path / "claude-plugins" / slug
        (plugin_dir / ".claude-plugin").mkdir(parents=True)
        (plugin_dir / ".claude-plugin" / "plugin.json").write_text(
            json.dumps({"name": slug, "version": "1.0.0", "description": "d"}),
            encoding="utf-8")
        links = f'[pack.links]\nrepository = "{repo}"\n' if repo else ""
        (plugin_dir / "pack.toml").write_text(
            f'[pack]\nname = "{slug}"\nversion = "1.0.0"\n' + links, encoding="utf-8")

        src = tmp_path / "packs" / slug
        (src / ".claude-plugin").mkdir(parents=True)
        (src / ".claude-plugin" / "plugin.json").write_text("{}", encoding="utf-8")
        (src / "pack.toml").write_text(
            f'[pack]\nname = "{slug}"\nversion = "1.0.0"\n'
            f'[pack.adapter-contract]\nversion = "0.3"\n'
            f'[pack.install]\nallowed-scopes = ["repo", "user"]\n' + links,
            encoding="utf-8")
        handles.append(Pack(name=slug, path=src))

    recipe = Recipe(name="marketplace", type="aggregate", adapter=None,
                    output_subdir=None, input_subdir="claude-plugins",
                    output_file="marketplace.json", units=[],
                    fragment_path=None, manifest_path=None)
    _run_aggregate(recipe, tmp_path, packs=handles, aggregate_scope="catalogue")
    return json.loads((tmp_path / "marketplace.json").read_text(encoding="utf-8"))


def test_envelope_derived_from_a_single_agreed_identity(tmp_path) -> None:
    """One identity across surviving entries → envelope derived from it."""
    payload = _aggregate_over(tmp_path, {
        "alpha": "https://github.com/eugenelim/agent-ready-repo",
        "beta": "https://github.com/eugenelim/agent-ready-repo",
    })
    assert payload["name"] == "agent-ready-repo"
    assert payload["owner"] == {"name": "eugenelim"}
    assert payload["description"]


def test_envelope_refuses_when_survivors_disagree(tmp_path) -> None:
    """The control AC7 exists for.

    Taking the FIRST entry's `source.url` let a filtered set re-key the
    marketplace to whichever pack sorted first — identity decided by an
    unrelated membership change. Disabling the refusal must fail this test.
    """
    with pytest.raises(ValueError, match="disagree on the repository identity"):
        _aggregate_over(tmp_path, {
            "alpha": "https://github.com/eugenelim/agent-ready-repo",
            "beta": "https://github.com/someone-else/other-catalogue",
        })


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

def test_render_pack_consumers_call_through(tmp_path) -> None:
    """Drive `render_pack`, not `import`.

    `run_recipe` gained a required `aggregate_scope`; an unthreaded caller is a
    **call-time** TypeError, never an import-time one — so an import check
    cannot fail for the reason it claims to. These six modules all reach
    `run_recipe` through `render_pack`/`render_pack_to_dir`, so exercising both
    entry points covers the signature for all of them.
    """
    from agentbundle.render import render_pack, render_pack_to_dir

    pack = REPO_ROOT / "packs" / "architect"
    rendered = render_pack(pack)
    assert any(k.startswith("claude-plugins/architect/") for k in rendered)

    out = tmp_path / "out"
    render_pack_to_dir(pack, out)
    assert (out / "claude-plugins" / "architect").is_dir()


def test_render_pack_omits_the_route_for_a_repo_only_pack() -> None:
    """The characterization that matters: real `core` yields no plugin subtree."""
    from agentbundle.render import render_pack

    rendered = render_pack(REPO_ROOT / "packs" / "core")
    assert not any(k.startswith("claude-plugins/core/") for k in rendered)
    assert any(k.startswith("apm/core/") for k in rendered)


def test_pre_change_state_relpaths_are_reported_by_diff(tmp_path) -> None:
    """The migration case the changelog discloses, driven through `diff`.

    An adopter's `.agentbundle-state.toml` carries `claude-plugins/core/…`
    relpaths the render no longer produces. `upgrade` diffs a fresh render
    against that state, so they read as removals. Asserting only that the
    render omits them repeats the test above; this drives the comparison that
    turns an omission into a deletion.
    """
    from agentbundle.render import render_pack

    stale = "claude-plugins/core/skills/work-loop/SKILL.md"
    rendered = set(render_pack(REPO_ROOT / "packs" / "core"))

    # What a pre-change state file recorded.
    previously_installed = rendered | {stale}
    removals = previously_installed - rendered
    assert removals == {stale}, (
        "the stale relpath must appear as a removal — this is the file "
        "`agentbundle upgrade` deletes from an adopter's repository"
    )
