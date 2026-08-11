"""Construction tests for the claude-plugin-route-scope spec.

Two kinds of assertion, deliberately:

* **Green now** — pins behaviour the spec *depends on* and did not author
  (`_allowed_scopes`' real gate; the three-resolver implication). If these ever
  go red the spec's premises have moved.
* **Red now** — drives the not-yet-existing publish filter by name. These fail
  with ImportError/AttributeError until it lands, which is the point: a stub
  that imports nothing cannot signal an under-specified criterion.

No `xfail`. An unconditionally-raising body under `xfail(strict=True)` exits 0,
can never XPASS, and stays green after the feature ships — the shape
docs/CONVENTIONS.md forbids.

Traces to docs/specs/claude-plugin-route-scope/spec.md.
"""

from __future__ import annotations

import tomllib

import pytest
from agentbundle.commands.validate import _allowed_scopes


def _pack(contract_version: str | None, allowed: list[str] | None) -> dict:
    src = '[pack]\nname = "p"\nversion = "1.0.0"\n'
    if contract_version is not None:
        src += f'[pack.adapter-contract]\nversion = "{contract_version}"\n'
    if allowed is not None:
        rendered = ", ".join(f'"{s}"' for s in allowed)
        src += f'[pack.install]\ndefault-scope = "repo"\nallowed-scopes = [{rendered}]\n'
    return tomllib.loads(src)


# --- AC2: the real gate is [pack.adapter-contract].version, not [pack.install] ---


@pytest.mark.parametrize("contract_version", [None, "0.1"])
def test_absent_or_legacy_contract_resolves_repo_regardless_of_install_table(
    contract_version: str | None,
) -> None:
    """The trap the spec names: declaring allowed-scopes is not enough."""
    assert _allowed_scopes(_pack(contract_version, ["repo", "user"])) == ["repo"]


def test_declared_contract_honours_the_install_table() -> None:
    assert _allowed_scopes(_pack("0.3", ["repo", "user"])) == ["repo", "user"]


# --- AC21: user-membership implication, NOT subset ---


def test_subset_is_false_so_the_property_must_be_implication() -> None:
    """Guards the disproved formulation from being reintroduced."""
    pack = _pack(None, ["user"])
    assert _allowed_scopes(pack) == ["repo"]
    # Against the sibling resolvers, not a literal: comparing the canonical
    # output to `{"user"}` can only fail if the line above already failed.
    # What disproves the subset formulation is that a pack *declaring* only
    # `user` still resolves to `repo` when no contract version is declared.
    assert "user" in pack["pack"]["install"]["allowed-scopes"]
    assert not set(_allowed_scopes(pack)) <= set(
        pack["pack"]["install"]["allowed-scopes"]
    ), "declared ⊉ resolved — subset would have made this pack publishable"


@pytest.mark.parametrize(
    "contract_version", [None, "0.1", "0.2", "0.3", "0.17", "0.18"]
)
@pytest.mark.parametrize("declared", [None, ["repo"], ["user"], ["repo", "user"]])
def test_user_membership_implication_holds(
    contract_version: str | None, declared: list[str] | None
) -> None:
    from agentbundle.catalogue_tooling.lint import _profile_allowed_scopes
    from agentbundle.commands.install import _resolved_allowed_scopes

    pack = _pack(contract_version, declared)
    if "user" in _allowed_scopes(pack):
        # Both conjuncts. The three resolvers take different argument shapes:
        # the whole pack dict, the [pack.install] table, and the parsed TOML.
        assert "user" in _profile_allowed_scopes(pack)
        assert "user" in _resolved_allowed_scopes(
            pack.get("pack", {}).get("install", {})
        )


# --- Red until the filter lands: driven by name, not by a raise ---


def _predicate():
    from agentbundle.build.main import is_publishable  # noqa: PLC0415

    return is_publishable


def test_predicate_exists_and_keys_on_the_derived_set() -> None:
    is_publishable = _predicate()
    assert is_publishable(_pack("0.3", ["repo", "user"]), slug="architect") is True
    assert is_publishable(_pack("0.3", ["repo"]), slug="core") is False
    # Derived-set condition 1: underscore-prefixed slugs are never publishable.
    assert is_publishable(_pack("0.3", ["repo", "user"]), slug="_example") is False


def test_aggregate_scope_is_required_with_no_default() -> None:
    """AC12's discriminator must be explicit — a default silently misclassifies
    `render_packs_to_dir` and `cmd_build --recipe`.

    Signature-only, and deliberately paired with the behavioural pins below:
    `inspect.signature` cannot notice the *branches* that read the parameter
    being deleted, which is what actually turns disclosure off.
    """
    import inspect

    from agentbundle.build.main import _run_aggregate, _run_per_pack, run_recipe

    for fn in (run_recipe, _run_aggregate, _run_per_pack):
        param = inspect.signature(fn).parameters["aggregate_scope"]
        assert param.default is inspect.Parameter.empty, fn.__name__
        assert param.kind is inspect.Parameter.KEYWORD_ONLY, fn.__name__


def test_an_all_repo_scope_catalogue_warns_and_writes_rather_than_failing(
    tmp_path, capsys
) -> None:
    """The asymmetry round thirteen removed.

    `contracts/pack.schema.json` makes `[pack.adapter-contract]` optional, so
    an adopter whose packs are all repo-scoped resolves to an empty plugin
    route through no fault of their own — the shape the catalogue-tooling
    smoke gate's own fixture has. This used to raise, which broke
    `agentbundle catalogue build` for them outright.
    """
    import json

    from agentbundle.build.main import Pack, Recipe, _run_aggregate

    plugin_dir = tmp_path / "claude-plugins" / "narrow"
    (plugin_dir / ".claude-plugin").mkdir(parents=True)
    (plugin_dir / ".claude-plugin" / "plugin.json").write_text(
        json.dumps({"name": "narrow", "version": "1.0.0", "description": "d"}),
        encoding="utf-8")
    (plugin_dir / "pack.toml").write_text(
        '[pack]\nname = "narrow"\nversion = "1.0.0"\n', encoding="utf-8")

    src = tmp_path / "packs" / "narrow"
    (src / ".claude-plugin").mkdir(parents=True)
    (src / ".claude-plugin" / "plugin.json").write_text("{}", encoding="utf-8")
    (src / "pack.toml").write_text(
        '[pack]\nname = "narrow"\nversion = "1.0.0"\n'
        '[pack.adapter-contract]\nversion = "0.3"\n'
        '[pack.install]\nallowed-scopes = ["repo"]\n', encoding="utf-8")

    recipe = Recipe(name="marketplace", type="aggregate", adapter=None,
                    output_subdir=None, input_subdir="claude-plugins",
                    output_file="marketplace.json", units=[],
                    fragment_path=None, manifest_path=None)
    _run_aggregate(recipe, tmp_path, packs=[Pack(name="narrow", path=src)],
                   aggregate_scope="catalogue")

    err = capsys.readouterr().err
    assert "the marketplace is empty" in err
    assert "valid state" in err, "an all-repo-scope catalogue is not a defect"
    assert "agentbundle install" in err, "the warning must name the other route"
    payload = json.loads(
        (tmp_path / "marketplace.json").read_text(encoding="utf-8"))
    assert payload["plugins"] == [], "the file is still written"


def test_unknown_aggregate_scope_raises() -> None:
    """A typo must fail, not silently take the wrong disclosure policy.

    The frozenset exists because an earlier `!= "catalogue"` form treated any
    unrecognised string as single-pack — so a misspelled scope at a call site
    would silence AC1's exclusion lines with no signal.
    """
    from agentbundle.build.main import run_recipe

    with pytest.raises(ValueError, match="aggregate_scope must be one of"):
        run_recipe(None, [], None, {}, aggregate_scope="catalouge")
