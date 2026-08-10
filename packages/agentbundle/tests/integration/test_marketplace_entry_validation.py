"""Red stubs for spec/claude-plugins-manifest-correctness.

Materialised at PLAN per docs/CONVENTIONS.md § Stub → EXECUTE handoff. Every
test here asserts a contract surface the spec's Acceptance Criteria determine;
none is a bare TODO. They are expected to FAIL until their task lands.

Task map:
  T0 → AC9   marketplace entries are validated, on both paths
  T1 → AC7   no assertion pins the old source shape
  T2 → AC1, AC5, AC8   source shape, envelope, schema
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

DATA = Path(__file__).resolve().parents[2] / "agentbundle" / "_data"


def _validate(instance: dict, schema: dict) -> list[str]:
    """Use the validator the BUILD gates on, not `jsonschema`.

    `agentbundle.build.validate` is stdlib-only and is what
    `build/main.py:31` and `verify.py:600` call. `jsonschema` is absent from
    `pyproject.toml` `dependencies = []` and from CI Gate A's install list, so
    an `importorskip` here would turn these into silent skips on CI — the exact
    looks-like-a-gate failure this spec exists to fix.
    """
    from agentbundle.build.validate import validate

    return validate(instance, schema)


def _assert_valid(instance: dict, schema: dict) -> None:
    errors = _validate(instance, schema)
    assert not errors, f"expected valid, got: {errors}"


def _assert_invalid(instance: dict, schema: dict) -> None:
    errors = _validate(instance, schema)
    assert errors, "expected rejection, but the validator accepted it"


GIT_SUBDIR_SOURCE = {
    "source": "git-subdir",
    "url": "https://github.com/eugenelim/agent-ready-repo.git",
    "path": "core",
    "ref": "claude-plugins-dist",
}
LEGACY_SOURCE = {
    "source": "github",
    "repo": "eugenelim/agent-ready-repo",
    "branch": "claude-plugins-dist",
    "directory": "core",
}


def _entry_schema() -> dict:
    """The marketplace-entry schema T0 introduces.

    Distinct from the derived plugin.json schema: an entry REQUIRES `source`
    and permits `category`, while plugin.json carries neither
    (build/main.py:545-546 pops both before validation).
    """
    path = DATA / "marketplace-entry.schema.json"
    if not path.exists():  # STUB: AC9 — T0 has not landed yet
        pytest.fail(
            "marketplace-entry schema absent: one schema cannot both forbid "
            "`source` (plugin.json) and require it (marketplace entry)"
        )
    return json.loads(path.read_text(encoding="utf-8"))


# --- T0 / AC9 -------------------------------------------------------------


def test_marketplace_entry_schema_constrains_source_when_present() -> None:
    """AC9 — `source` is deliberately NOT schema-required.

    `[pack.links].repository` is optional in pack.schema.json and the shipped
    scaffold `_example` pack omits it, so requiring `source` here would turn
    every scaffold-derived adopter's `catalogue verify` red. Absence is caught
    by an actionable diagnostic instead (see
    `test_missing_source_names_the_cause`). What the schema must do is
    constrain `source` whenever it IS present.
    """
    schema = _entry_schema()
    assert "source" not in schema.get("required", [])
    _assert_invalid({"name": "x", "version": "1.0.0", "description": "d",
                     "source": {"source": "git-subdir"}}, schema)
    _assert_valid({"name": "x", "version": "1.0.0", "description": "d",
                   "source": GIT_SUBDIR_SOURCE}, schema)


def test_marketplace_entry_schema_permits_category() -> None:
    """# STUB: AC9 — every live entry carries `category`.

    The derived schema forbids it under additionalProperties: false, which is
    the proof that entries have never been validated: all 21 would fail today.
    """
    schema = _entry_schema()
    assert "category" in schema.get("properties", {}), (
        "`category` must be admitted or the new gate rejects all 21 live entries"
    )


def _build_dist_marketplace(tmp_path: Path) -> dict:
    """Build the dist marketplace into tmp_path.

    `dist/` is gitignored (.gitignore:73) and CI Gate A runs no `make build`, so
    a test that reads the working tree silently SKIPS on CI — coverage that
    looks present and is not.
    """
    from agentbundle.build.main import Recipe, _run_aggregate

    plugin_dir = tmp_path / "claude-plugins" / "core"
    (plugin_dir / ".claude-plugin").mkdir(parents=True)
    (plugin_dir / ".claude-plugin" / "plugin.json").write_text(
        json.dumps({"name": "core", "version": "2.2.0", "description": "d",
                    "source": GIT_SUBDIR_SOURCE}), encoding="utf-8")
    (plugin_dir / "pack.toml").write_text(
        '[pack]\nname = "core"\n'
        '[pack.links]\nrepository = "https://github.com/eugenelim/agent-ready-repo"\n',
        encoding="utf-8")
    # A publishable source pack: `_run_aggregate` now resolves membership from
    # the source tree, so the dist directory alone is not enough.
    src_pack = tmp_path / "packs" / "core"
    (src_pack / ".claude-plugin").mkdir(parents=True)
    (src_pack / ".claude-plugin" / "plugin.json").write_text("{}", encoding="utf-8")
    (src_pack / "pack.toml").write_text(
        '[pack]\nname = "core"\nversion = "2.2.0"\n'
        '[pack.adapter-contract]\nversion = "0.3"\n'
        '[pack.install]\ndefault-scope = "repo"\nallowed-scopes = ["repo", "user"]\n',
        encoding="utf-8")

    recipe = Recipe(name="marketplace", type="aggregate", adapter=None,
                    output_subdir=None, input_subdir="claude-plugins",
                    output_file="marketplace.json", units=[],
                    fragment_path=None, manifest_path=None)
    # `packs` is required and drives the publishability filter — passing the
    # synthetic source pack keeps this exercising the envelope, not the filter.
    from agentbundle.build.main import Pack

    _run_aggregate(  # returns a summary; the payload is written
        recipe,
        tmp_path,
        packs=[Pack(name="core", path=src_pack)],
        aggregate_scope="catalogue",
    )
    return json.loads((tmp_path / "marketplace.json").read_text(encoding="utf-8"))


def test_dist_marketplace_entries_validate(tmp_path: Path) -> None:
    """# STUB: AC9 — built into tmp_path, never read from the gitignored tree."""
    payload = _build_dist_marketplace(tmp_path)
    entries = payload.get("plugins", [])
    assert len(entries) >= 1
    for entry in entries:
        _assert_valid(entry, _entry_schema())


def test_malformed_source_is_rejected() -> None:
    """# STUB: AC9 — the negative case; without this the gate proves nothing."""
    bad = {"name": "x", "version": "1.0.0", "description": "d",
           "source": {"source": "git-subdir"}}  # no url, no path, no ref/sha
    _assert_invalid(bad, _entry_schema())


# --- T2 / AC8 -------------------------------------------------------------


@pytest.mark.parametrize("schema_path", [
    DATA / "plugin-manifest.derived.schema.json",
    DATA / "plugin-manifest.schema.json",
])
def test_all_four_schemas_drop_legacy_source_keys(schema_path: Path) -> None:
    """# STUB: AC8 — all four copies, including the byte-equality-gated twins."""
    text = schema_path.read_text(encoding="utf-8")
    assert '"branch"' not in text, f"{schema_path.name} still declares `branch`"
    assert '"directory"' not in text, f"{schema_path.name} still declares `directory`"


def test_source_requires_ref_or_sha() -> None:
    """# STUB: AC8 — a ref-less, sha-less payload silently fetches the default
    branch, which is the original defect wearing a valid shape."""
    schema = json.loads(
        (DATA / "plugin-manifest.derived.schema.json").read_text(encoding="utf-8")
    )
    unpinned = dict(GIT_SUBDIR_SOURCE)
    unpinned.pop("ref")
    _assert_invalid(unpinned, schema["properties"]["source"])


@pytest.mark.parametrize("bad_url", [
    "http://github.com/eugenelim/agent-ready-repo.git",   # scheme
    "https://gitlab.com/eugenelim/agent-ready-repo.git",  # host
])
def test_source_url_is_constrained(bad_url: str) -> None:
    """# STUB: AC8 — git-subdir moves the fetch host from the schema into data."""
    schema = json.loads(
        (DATA / "plugin-manifest.derived.schema.json").read_text(encoding="utf-8")
    )
    payload = dict(GIT_SUBDIR_SOURCE, url=bad_url)
    _assert_invalid(payload, schema["properties"]["source"])


# --- T2 / AC1 + AC5 -------------------------------------------------------


def test_derive_projectable_subset_emits_git_subdir() -> None:
    """# STUB: AC1 — the generator is `derive_projectable_subset`, main.py:199."""
    from agentbundle.build.main import derive_projectable_subset

    derived = derive_projectable_subset({
        "pack": {
            "name": "core",
            "links": {"repository": "https://github.com/eugenelim/agent-ready-repo"},
        }
    })
    assert derived["source"] == GIT_SUBDIR_SOURCE


def test_http_repository_link_is_rejected_not_upgraded() -> None:
    """# STUB: AC1 — _GITHUB_URL_RE (main.py:49-51) is `^https?://` today, so an
    http:// link matches and would be silently emitted as https://."""
    from agentbundle.build.main import derive_projectable_subset

    with pytest.raises(ValueError):
        derive_projectable_subset({
            "pack": {
                "name": "core",
                "links": {"repository": "http://github.com/eugenelim/agent-ready-repo"},
            }
        })


def test_dist_envelope_survives_repo_key_removal(tmp_path: Path) -> None:
    """# STUB: AC5 — main.py:705-717 splits src["repo"] to derive name/owner;
    git-subdir has no `repo`, so both would silently drop."""
    payload = _build_dist_marketplace(tmp_path)
    for key in ("name", "owner", "description"):
        assert key in payload, f"dist marketplace envelope lost `{key}`"


# --- AC9: the GATE runs, not merely the schema --------------------------


def _write_marketplace(path: Path, entries: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(
        {"name": "t", "owner": {"name": "o"}, "plugins": entries}
    ), encoding="utf-8")


_BAD_ENTRY = {"name": "bad", "version": "1.0.0", "description": "d",
              "source": {"source": "git-subdir"}}  # no url/path/ref


def test_gate_rejects_malformed_source_in_dist_marketplace(tmp_path: Path) -> None:
    """The dist path is gated."""
    from agentbundle.catalogue_tooling.verify import _step_plugin_manifests

    tmpdir = tmp_path / "t"
    _write_marketplace(tmpdir / "dist" / "claude-plugins" / "marketplace.json", [_BAD_ENTRY])
    diags = _step_plugin_manifests(tmp_path / "root", None, None, tmpdir)
    assert any(d.code == "CAT-V-013" for d in diags), "dist marketplace is ungated"


def test_gate_rejects_malformed_source_in_root_marketplace_without_dist(tmp_path: Path) -> None:
    """The ROOT path is gated *independently of dist*.

    Regression pin for a defect this change shipped and caught by hand: the
    early return `if not dist_dir.exists(): return []` sat above the root
    check, making it unreachable whenever `dist/` is absent — which is how CI
    runs. `catalogue verify` reported ok while checking nothing. Reinstating
    that early return must fail this test.
    """
    from agentbundle.catalogue_tooling.verify import _step_plugin_manifests

    root = tmp_path / "root"
    _write_marketplace(root / ".claude-plugin" / "marketplace.json", [_BAD_ENTRY])
    diags = _step_plugin_manifests(root, None, None, tmp_path / "no-dist")
    assert any(d.code == "CAT-V-013" for d in diags), (
        "root marketplace ungated when dist/ is absent"
    )


def test_gate_fails_closed_when_a_schema_is_unresolvable(tmp_path: Path, monkeypatch) -> None:
    """An unreadable schema must produce a diagnostic, never a silent pass."""
    from agentbundle.catalogue_tooling import verify as verify_mod

    root = tmp_path / "root"
    _write_marketplace(root / ".claude-plugin" / "marketplace.json", [_BAD_ENTRY])

    import importlib

    # `agentbundle.build.main` resolves to a *function* via build/__init__.py,
    # so neither attribute access nor `import ... as` reaches the module.
    build_main = importlib.import_module("agentbundle.build.main")

    def _boom(name: str) -> str:
        raise FileNotFoundError(name)

    monkeypatch.setattr(build_main, "_read_bundled", _boom)
    diags = verify_mod._step_plugin_manifests(root, None, None, tmp_path / "no-dist")
    assert any("unavailable" in d.message for d in diags), (
        "a missing schema silently disabled the whole step"
    )


def test_missing_source_names_the_cause(tmp_path: Path) -> None:
    """`source` cannot be schema-required — [pack.links].repository is optional
    and the shipped scaffold pack omits it — so the gate must say WHY."""
    from agentbundle.catalogue_tooling.verify import _step_plugin_manifests

    root = tmp_path / "root"
    _write_marketplace(root / ".claude-plugin" / "marketplace.json",
                       [{"name": "nosrc", "version": "1.0.0", "description": "d"}])
    diags = _step_plugin_manifests(root, None, None, tmp_path / "no-dist")
    hits = [d for d in diags if "pack.links" in d.message]
    assert hits, "missing-source diagnostic must name [pack.links].repository"
    # Severity is load-bearing: an external catalogue may legitimately hold a
    # pack it does not publish for marketplace install (the Gate B smoke does
    # exactly that), so this must not hard-fail their build.
    from agentbundle.catalogue_tooling.results import Severity

    assert all(d.severity == Severity.WARN for d in hits), (
        "a pack without [pack.links].repository is a choice, not a defect"
    )


# --- AC3: per-route projection targets and sweep confinement -------------


def _contract_for(recipe_name: str) -> dict:
    import tomllib

    from agentbundle.build.main import CONTRACT_PATH, Recipe, _resolve_contract_for_route

    contract = tomllib.loads(Path(CONTRACT_PATH).read_text(encoding="utf-8"))
    recipe = Recipe(name=recipe_name, type="per-pack", adapter="claude-code",
                    output_subdir="x", input_subdir=None, output_file=None,
                    units=[], fragment_path=None, manifest_path=None)
    return _resolve_contract_for_route(contract, recipe)


def test_component_targets_differ_by_route() -> None:
    """# AC2 + AC3 — same source pack, different emitted paths per route."""
    plugins = {e["primitive"]: e["target-path"]
               for e in _contract_for("per-pack-claude-plugin")["adapter"]["claude-code"]["projection"]}
    other = {e["primitive"]: e["target-path"]
             for e in _contract_for("per-pack-overlay")["adapter"]["claude-code"]["projection"]}
    assert (plugins["skill"], plugins["agent"], plugins["command"]) == (
        "skills/", "agents/", "commands/")
    assert (other["skill"], other["agent"], other["command"]) == (
        ".claude/skills/", ".claude/agents/", ".claude/commands/")
    # Hook wiring is out of scope and must NOT move.
    assert plugins["hook-wiring"] == other["hook-wiring"] == ".claude/settings.local.json"


def test_sweep_target_follows_the_route(tmp_path: Path) -> None:
    """The orphan sweep `rmtree`s under its resolved target, so it must move
    with the projection. If the route reached the projection but not the sweep,
    the sweep would target a nonexistent directory on the plugins route — or,
    worse, an adopter-owned one."""
    from agentbundle.build.adapters.claude_code import _skill_direct_directory_target

    plugins_target = _skill_direct_directory_target(
        _contract_for("per-pack-claude-plugin"), tmp_path)
    other_target = _skill_direct_directory_target(
        _contract_for("per-pack-overlay"), tmp_path)
    assert plugins_target == tmp_path / "skills"
    assert other_target == tmp_path / ".claude" / "skills"


def test_decoy_at_plugin_root_survives_a_non_plugins_build(tmp_path: Path) -> None:
    """AC3: a decoy at `<root>/skills/` is outside the non-plugins sweep target,
    so a non-plugins build must leave it alone."""
    from agentbundle.build.adapters.claude_code import _skill_direct_directory_target

    decoy = tmp_path / "skills" / "decoy"
    decoy.mkdir(parents=True)
    target = _skill_direct_directory_target(_contract_for("per-pack-overlay"), tmp_path)
    assert target != tmp_path / "skills", (
        "non-plugins sweep target must not be the plugin-root skills/ dir"
    )
    assert decoy.exists()
