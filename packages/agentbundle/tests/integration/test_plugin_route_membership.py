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

import contextlib
import io
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


# The repo-root marketplace's literal roster is asserted by
# `tools/lint-plugin-roster.py`, which runs in the required gate against the
# real file. Enumerating this repository's 14 published / 7 withheld packs here
# too would put a catalogue-roster claim in the engine tree — the same reason
# `test_install_core_smoke.py` routes its roster claim to `tools/`.


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


def test_upgrade_orphans_rather_than_removes_a_stale_route_tree(tmp_path) -> None:
    """What `upgrade` actually does with a pre-change `claude-plugins/<pack>/`.

    The changelog told adopters this tree was *deleted*. Driving the real
    `upgrade` — both the re-apply path and a genuine version bump — shows it is
    not: `upgrade` adds rendered relpaths to `state.files` and never prunes ones
    the render dropped, so the files stay on disk and stay listed.

    Pinned because the disclosure adopters read depends on it. If a future
    change starts pruning, this test fails and the changelog needs revisiting —
    which is the point.
    """
    import argparse
    import contextlib
    import io
    import re as _re
    import shutil

    from agentbundle.commands import install, upgrade

    catalogue = tmp_path / "cat"
    (catalogue / "packs").mkdir(parents=True)
    shutil.copytree(REPO_ROOT / "packs" / "core", catalogue / "packs" / "core",
                    symlinks=False)
    root = tmp_path / "adopter"
    root.mkdir()
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        install.run(argparse.Namespace(
            pack="core", catalogue=str(catalogue), output=str(root),
            scope=None, force=False,
        ))

    # What a pre-change dist-tree install left behind.
    stale_rel = "claude-plugins/core/skills/work-loop/SKILL.md"
    stale = root / stale_rel
    stale.parent.mkdir(parents=True, exist_ok=True)
    stale.write_text("previously installed\n", encoding="utf-8")
    # The version below is deliberately a *historical* one and must not be
    # updated to track `packs/core/pack.toml` — the point is that this entry
    # predates the change.
    state = root / ".agentbundle-state.toml"
    marker = "[pack.core.adapters.claude-code.files]"
    state.write_text(state.read_text(encoding="utf-8").replace(
        marker,
        marker + f'\n"{stale_rel}" = {{ from-pack-version = "2.5.2", '
        f'sha = "{"0" * 64}" }}',
        1,
    ), encoding="utf-8")

    # A genuine version bump, not just a re-apply.
    pack_toml = catalogue / "packs" / "core" / "pack.toml"
    pack_toml.write_text(
        _re.sub(r'^version = "[^"]+"', 'version = "99.0.0"',
                pack_toml.read_text(encoding="utf-8"), count=1, flags=_re.M),
        encoding="utf-8",
    )

    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        rc = upgrade.run(argparse.Namespace(
            pack="core", catalogue=str(catalogue), root=str(root), scope="repo",
            adapter=None, yes=True, dry_run=False, json=False, force=False,
            all=False, primitive=None,
        ))

    assert rc == 0
    # Prove *this upgrade run* took the dist-tree branch. `apm/core` will not
    # do: the install above already created it, so asserting it holds whichever
    # branch runs. The per-IDE branch is the one that writes `.claude/` into
    # the adopter root, and nothing before this point has — so its absence is
    # produced by the upgrade and by nothing else.
    assert not (root / ".claude").exists(), (
        "upgrade took the per-IDE branch, not the dist-tree branch — this test "
        "would then assert the orphan survives a path it never took"
    )
    assert stale.exists(), "upgrade does not delete the orphaned tree"
    assert stale_rel in state.read_text(encoding="utf-8"), (
        "the relpath stays listed in state — upgrade never prunes dropped renders"
    )
    # And the route itself is genuinely gone from the fresh render.
    from agentbundle.render import render_pack

    assert not any(k.startswith("claude-plugins/core/")
                   for k in render_pack(REPO_ROOT / "packs" / "core"))


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


def test_catalogue_build_warns_and_continues_when_the_filter_empties_it(
    tmp_path, capsys
) -> None:
    """AC12, driven through `_run_aggregate` rather than a pure helper.

    This raised until round thirteen. It broke `agentbundle catalogue build`
    for any adopter whose packs are all repo-scoped — including the
    catalogue-tooling smoke gate's own fixture, which went red on this branch
    with no local target covering it. Warn-and-continue now, matching the
    self-host writer; this repository's roster is guarded far more precisely
    by `tools/lint-plugin-roster.py`.
    """
    from agentbundle.build.main import Pack, _run_aggregate

    _synth_pack(tmp_path, "repoonly", user=False)
    result = _run_aggregate(
        _recipe(), tmp_path,
        packs=[Pack(name="repoonly", path=tmp_path / "packs" / "repoonly")],
        aggregate_scope="catalogue",
    )
    assert result["entries"] == 0
    err = capsys.readouterr().err
    assert "the marketplace is empty" in err and "valid state" in err


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


# --- AC1 / AC12: the disclosure clauses --------------------------------------
#
# "named on stderr so an exclusion is never silent" and "warns loudly and
# continues" are claims about output. Deleting all four print blocks left every
# other test in this module, `test_plugin_scope_filter.py`, the self-host tests
# and all five route lints green — and made `_skip_reason` dead code nothing
# noticed. These pin the wordings.


def test_every_exclusion_is_named_on_stderr(tmp_path) -> None:
    """`_build` runs a subprocess, so its own stream is the one to read —
    `redirect_stderr` in this process captures nothing from it."""
    result = subprocess.run(
        [sys.executable, "-m", "agentbundle.build", "build",
         "--packs-dir", str(FIXTURES), "--output-dir", str(tmp_path / "dist")],
        capture_output=True, text=True, cwd=REPO_ROOT,
    )
    assert result.returncode == 0, result.stderr
    err = result.stderr
    for slug in sorted(EXPECTED_WITHHELD):
        assert f"claude-plugins: skipping {slug} —" in err, (
            f"{slug} was dropped without saying so — AC1's disclosure clause. "
            f"stderr was:\n{err}"
        )
    # The aggregate's own summary is deliberately NOT asserted here: on a
    # clean build the per-pack step has already dropped the pack, so nothing
    # unpublishable reaches `dist/claude-plugins/` and `excluded` is empty.
    # That line fires only over a stale tree — covered below.


def test_the_aggregate_names_what_it_drops_from_a_stale_tree(tmp_path, capsys) -> None:
    """`make build` has no `clean`, so a dropped pack's dist dir survives.

    That is the one path on which the aggregate's own exclusion summary
    fires — and it is the path where staying silent would publish a
    marketplace keyed to packs the source no longer offers.
    """
    from agentbundle.build.main import Pack, Recipe, _run_aggregate

    for slug in ("wide", "stale"):
        plugin_dir = tmp_path / "claude-plugins" / slug
        (plugin_dir / ".claude-plugin").mkdir(parents=True)
        (plugin_dir / ".claude-plugin" / "plugin.json").write_text(
            json.dumps({"name": slug, "version": "1.0.0", "description": "d"}),
            encoding="utf-8")
        (plugin_dir / "pack.toml").write_text(
            f'[pack]\nname = "{slug}"\nversion = "1.0.0"\n', encoding="utf-8")

    # Only `wide` still exists in source, and only it is user-capable.
    src = tmp_path / "packs" / "wide"
    (src / ".claude-plugin").mkdir(parents=True)
    (src / ".claude-plugin" / "plugin.json").write_text("{}", encoding="utf-8")
    (src / "pack.toml").write_text(
        '[pack]\nname = "wide"\nversion = "1.0.0"\n'
        '[pack.adapter-contract]\nversion = "0.3"\n'
        '[pack.install]\nallowed-scopes = ["repo", "user"]\n', encoding="utf-8")

    recipe = Recipe(name="marketplace", type="aggregate", adapter=None,
                    output_subdir=None, input_subdir="claude-plugins",
                    output_file="marketplace.json", units=[],
                    fragment_path=None, manifest_path=None)
    _run_aggregate(recipe, tmp_path, packs=[Pack(name="wide", path=src)],
                   aggregate_scope="catalogue")

    err = capsys.readouterr().err
    assert "stale" in err, f"the stale directory was dropped silently: {err!r}"
    # The reason must be the one that actually held. A directory whose source
    # pack is gone is not a scope refusal, and saying so sends the reader to a
    # `pack.toml` that no longer exists.
    assert "no longer present in the source tree" in err
    assert "not installable at user scope" not in err, (
        "a stale directory was reported as a scope refusal"
    )


def test_the_skip_reason_names_the_condition_that_actually_held(tmp_path) -> None:
    """`_skip_reason`'s three branches, each against a pack shaped for it.

    Reporting a scope refusal for a manifest-less pack sends the reader to the
    wrong file, which is the whole reason this helper exists rather than one
    hard-coded string.
    """
    from agentbundle.build.main import _skip_reason

    bare = tmp_path / "bare"
    bare.mkdir()
    assert _skip_reason(bare) == "no pack.toml"

    no_manifest = tmp_path / "no_manifest"
    no_manifest.mkdir()
    (no_manifest / "pack.toml").write_text('[pack]\nname = "x"\n', encoding="utf-8")
    assert "no .claude-plugin/plugin.json" in _skip_reason(no_manifest)

    repo_only = tmp_path / "repo_only"
    (repo_only / ".claude-plugin").mkdir(parents=True)
    (repo_only / ".claude-plugin" / "plugin.json").write_text("{}", encoding="utf-8")
    (repo_only / "pack.toml").write_text(
        '[pack]\nname = "repo_only"\nversion = "1.0.0"\n'
        '[pack.adapter-contract]\nversion = "0.3"\n'
        '[pack.install]\nallowed-scopes = ["repo"]\n', encoding="utf-8")
    reason = _skip_reason(repo_only)
    assert "user" in reason and "pack.toml" not in reason, (
        f"a scope refusal must name the scope, not a missing file: {reason!r}"
    )


def test_self_host_warns_loudly_when_the_filter_empties_the_marketplace(tmp_path) -> None:
    """AC12's self-host bullet — warn and continue, never silently empty."""
    from agentbundle.build.self_host import _aggregate_marketplace

    packs_dir = tmp_path / "packs"
    pack = packs_dir / "narrow"
    (pack / ".claude-plugin").mkdir(parents=True)
    (pack / ".claude-plugin" / "plugin.json").write_text(
        json.dumps({"name": "narrow", "version": "1.0.0"}), encoding="utf-8")
    (pack / "pack.toml").write_text(
        '[pack]\nname = "narrow"\nversion = "1.0.0"\n'
        '[pack.adapter-contract]\nversion = "0.3"\n'
        '[pack.install]\nallowed-scopes = ["repo"]\n', encoding="utf-8")
    out = tmp_path / "out"
    out.mkdir()

    err = io.StringIO()
    with contextlib.redirect_stderr(err):
        _aggregate_marketplace(packs_dir, out)
    msg = err.getvalue()

    assert "every discovered pack was filtered out" in msg
    assert "agentbundle install" in msg, "the warning must name the other route"
    # ...and continues: the file is still written, because self-host runs after
    # adapters and seeds and must not leave a half-projected tree.
    assert (out / ".claude-plugin" / "marketplace.json").exists()


def test_a_single_pack_render_says_nothing_about_the_route(tmp_path) -> None:
    """AC12's single-pack clause — the silence is deliberate, so pin it.

    Deleting the `aggregate_scope == "catalogue"` gate would make
    `agentbundle install --pack core` start printing a route refusal on a
    command that succeeded, with nothing else going red.
    """
    result = subprocess.run(
        [sys.executable, "-c",
         "from pathlib import Path; from agentbundle.render import render_pack; "
         f"render_pack(Path({str(REPO_ROOT / 'packs' / 'core')!r}))"],
        capture_output=True, text=True, cwd=REPO_ROOT,
    )
    assert result.returncode == 0, result.stderr
    assert "claude-plugins: skipping" not in result.stderr, (
        "a single-pack render of a repo-only pack announced a route refusal — "
        f"stderr was:\n{result.stderr}"
    )
