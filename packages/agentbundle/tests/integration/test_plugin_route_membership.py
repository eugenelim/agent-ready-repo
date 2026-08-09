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


def test_stale_route_relpath_is_absent_from_a_fresh_render() -> None:
    """Half of the migration case, and only half — see the criterion.

    What this pins: a `claude-plugins/core/…` relpath a pre-change install
    recorded is absent from a fresh render. What it does **not** pin: that
    `upgrade` therefore deletes it. Two attempts to drive the production
    comparator failed — `diff.run` returns 0 and prints nothing even on a real
    divergence, so it is not the comparator `upgrade` uses, and the right entry
    point has not been identified.

    Recorded rather than papered over: the changelog tells adopters `upgrade`
    deletes these files, and that claim currently rests on reading the code.
    Slug `plugin-upgrade-removal-artifact`.
    """
    from agentbundle.render import render_pack

    stale = "claude-plugins/core/skills/work-loop/SKILL.md"
    assert stale not in set(render_pack(REPO_ROOT / "packs" / "core"))


# --- Controls that had no artifact until round five --------------------------


def _synth_pack(root: Path, slug: str, *, user: bool, repo: str | None = None) -> None:
    """A source pack plus its dist projection."""
    links = f'[pack.links]\nrepository = "{repo}"\n' if repo else ""
    scopes = '["repo", "user"]' if user else '["repo"]'
    src = root / "packs" / slug
    (src / ".claude-plugin").mkdir(parents=True)
    (src / "pack.toml").write_text(
        f'[pack]\nname = "{slug}"\nversion = "1.0.0"\n'
        f'[pack.adapter-contract]\nversion = "0.3"\n'
        f'[pack.install]\ndefault-scope = "repo"\nallowed-scopes = {scopes}\n' + links,
        encoding="utf-8")
    (src / ".claude-plugin" / "plugin.json").write_text(
        json.dumps({"name": slug, "version": "1.0.0", "description": "d"}), encoding="utf-8")
    dist = root / "claude-plugins" / slug
    (dist / ".claude-plugin").mkdir(parents=True)
    (dist / ".claude-plugin" / "plugin.json").write_text(
        json.dumps({"name": slug, "version": "1.0.0", "description": "d"}), encoding="utf-8")
    (dist / "pack.toml").write_text(
        f'[pack]\nname = "{slug}"\nversion = "1.0.0"\n' + links, encoding="utf-8")


def _recipe():
    from agentbundle.build.main import Recipe
    return Recipe(name="marketplace", type="aggregate", adapter=None,
                  output_subdir=None, input_subdir="claude-plugins",
                  output_file="marketplace.json", units=[],
                  fragment_path=None, manifest_path=None)


def test_catalogue_build_refuses_when_the_filter_empties_a_non_empty_set(tmp_path) -> None:
    """AC12's hard error, driven through `_run_aggregate` rather than the pure helper.

    `aggregate_exit_code` was previously the only thing tested — a pure function
    disconnected from its single caller, so `if rc:` could be deleted and the
    suite stayed green.
    """
    from agentbundle.build.main import Pack, _run_aggregate

    _synth_pack(tmp_path, "repoonly", user=False)
    with pytest.raises(ValueError, match="publishes no packs"):
        _run_aggregate(
            _recipe(), tmp_path,
            packs=[Pack(name="repoonly", path=tmp_path / "packs" / "repoonly")],
            aggregate_scope="catalogue",
        )


def test_blank_catalogue_is_not_an_error(tmp_path) -> None:
    """Emptiness is a defect only when the filter caused it."""
    from agentbundle.build.main import _run_aggregate

    (tmp_path / "claude-plugins").mkdir()
    result = _run_aggregate(_recipe(), tmp_path, packs=[], aggregate_scope="catalogue")
    assert result["entries"] == 0


def test_scope_resolves_from_source_not_a_stale_dist(tmp_path) -> None:
    """AC4's control: `make build` has no `clean`, so a stale dist survives.

    The dist copy keeps the OLD, user-capable declaration; the source has been
    narrowed. Resolving from dist would republish against current intent.
    """
    from agentbundle.build.main import Pack, _run_aggregate

    _synth_pack(tmp_path, "narrowed", user=True,
                repo="https://github.com/eugenelim/agent-ready-repo")
    _synth_pack(tmp_path, "keeper", user=True,
                repo="https://github.com/eugenelim/agent-ready-repo")
    # Narrow the SOURCE only — the dist projection still carries the old scopes.
    src = tmp_path / "packs" / "narrowed" / "pack.toml"
    src.write_text(src.read_text().replace('["repo", "user"]', '["repo"]'), encoding="utf-8")

    _run_aggregate(
        _recipe(), tmp_path,
        packs=[Pack(name=n, path=tmp_path / "packs" / n) for n in ("narrowed", "keeper")],
        aggregate_scope="catalogue",
    )
    listed = _names(tmp_path / "marketplace.json")
    assert listed == {"keeper"}, "a stale dist directory must not republish"


def test_pack_flag_refused_on_an_aggregate_recipe(tmp_path) -> None:
    """AC26 guard one: `--pack` truncated the shared marketplace and exited 0."""
    result = subprocess.run(
        [sys.executable, "-m", "agentbundle.build", "build",
         "--packs-dir", str(FIXTURES), "--output-dir", str(tmp_path / "d"),
         "--recipe", "marketplace", "--pack", "core"],
        capture_output=True, text=True, cwd=REPO_ROOT,
    )
    assert result.returncode == 1, result.stdout
    assert "not meaningful" in result.stderr


def test_run_recipe_rejects_an_unknown_scope_on_a_per_pack_recipe(tmp_path) -> None:
    """AC26 guard two, at the boundary a per-pack recipe actually reaches.

    Validating only inside `aggregate_exit_code` left per-pack call sites
    unchecked — the class the frozenset exists to close.
    """
    from agentbundle.build.contract import load as load_contract
    from agentbundle.build.main import CONTRACT_PATH, load_recipe, run_recipe

    with pytest.raises(ValueError, match="aggregate_scope must be one of"):
        run_recipe(
            load_recipe("per-pack-claude-plugin"), [], tmp_path,
            load_contract(CONTRACT_PATH), aggregate_scope="catalouge",
        )
