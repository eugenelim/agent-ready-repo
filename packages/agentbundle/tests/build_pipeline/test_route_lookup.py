"""Construction tests for contract-derived distribution-route behavior."""

from __future__ import annotations

import re
import tomllib
from dataclasses import replace
from importlib import import_module
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

PACKAGE_ROOT = Path(__file__).resolve().parents[2]
ROUTE_CONTRACT_PATH = PACKAGE_ROOT / "agentbundle" / "_data" / "distribution-routes.toml"
FIXTURE_PACKS = Path(__file__).resolve().parent / "fixtures" / "packs"


def _contract() -> dict[str, Any]:
    """Load the bundled route declaration used by the running build."""
    return tomllib.loads(ROUTE_CONTRACT_PATH.read_text(encoding="utf-8"))


def _lookup() -> Any:
    """Import the internal lookup at assertion time so absence is a test failure."""
    return import_module("agentbundle.build.route_lookup")


def test_lookup_resolves_every_declared_route_from_contract() -> None:
    """Return one behavior whose declared controls match each contract route."""
    contract = _contract()
    behaviors = _lookup().resolve_route_behaviors(contract)

    assert set(behaviors) == set(contract["route"])
    assert len({behavior.__class__ for behavior in behaviors.values()}) == len(behaviors)
    for route_name, declaration in contract["route"].items():
        behavior = behaviors[route_name]
        manifest = declaration["manifest-projector"]
        expected_adapter = manifest["adapter-projector"]
        assert behavior.expected_admission_policy == manifest["admission-policy"]
        assert behavior.expected_adapter_projector == (
            None if expected_adapter == "none" else expected_adapter
        )


def test_each_route_owns_its_existing_discovery_control() -> None:
    """Keep generic discovery separate from the confined portable-route path."""
    behaviors = _lookup().resolve_route_behaviors(_contract())
    calls: list[str] = []

    def generic(_packs_dir: Path) -> list[str]:
        calls.append("generic")
        return ["generic"]

    def confined(_packs_dir: Path) -> list[str]:
        calls.append("confined")
        return ["confined"]

    operations = SimpleNamespace(
        discover_generic=generic,
        discover_confined=confined,
    )
    expected = {
        "apm": ["generic"],
        "claude-plugins": ["generic"],
        "agent-plugin": ["confined"],
    }

    for route_name, behavior in behaviors.items():
        calls.clear()
        assert behavior.discover_packs(Path("packs"), operations) == expected[route_name]
        assert calls == expected[route_name]


def test_default_build_resolves_all_routes_before_touching_output(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A failure in the final declaration leaves an existing output root unchanged."""
    build_main = import_module("agentbundle.build.main")
    output_root = tmp_path / "dist"
    output_root.mkdir()
    sentinel = output_root / "sentinel.txt"
    sentinel.write_text("keep me\n", encoding="utf-8")
    before = {
        path.relative_to(output_root): path.read_bytes()
        for path in output_root.rglob("*")
        if path.is_file()
    }
    original_resolve = build_main._resolve_distribution_route
    declared_routes = set(_contract()["route"])
    visited: set[str] = set()

    def reject_final_route(recipe: Any, route_contract: dict[str, Any], **kwargs: Any) -> Any:
        visited.add(recipe.route)
        if visited == declared_routes:
            raise ValueError("unresolvable route behavior")
        return original_resolve(recipe, route_contract, **kwargs)

    monkeypatch.setattr(
        build_main,
        "_resolve_distribution_route",
        reject_final_route,
    )

    with pytest.raises(ValueError, match="unresolvable route behavior"):
        build_main.run_default_build(FIXTURE_PACKS, output_root)

    assert visited == declared_routes
    after = {
        path.relative_to(output_root): path.read_bytes()
        for path in output_root.rglob("*")
        if path.is_file()
    }
    assert after == before == {Path("sentinel.txt"): b"keep me\n"}


def test_default_build_discovers_packs_with_the_strictest_declared_control(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A default build applies the strictest route's discovery to every pack.

    One discovery pass serves the whole build, so the route with the strictest
    filesystem controls has to be the one that runs. This records which
    discovery implementation the build actually called rather than asserting a
    refusal: the confined pack-root checks are also re-applied per pack later,
    so a refusal alone stays green even when discovery has been downgraded.
    """
    build_main = import_module("agentbundle.build.main")
    called: list[str] = []
    original_operations = build_main._route_operations

    def recording_operations() -> Any:
        operations = original_operations()
        generic = operations.discover_generic
        confined = operations.discover_confined

        def record_generic(packs_dir: Any) -> Any:
            called.append("generic")
            return generic(packs_dir)

        def record_confined(packs_dir: Any) -> Any:
            called.append("confined")
            return confined(packs_dir)

        return replace(
            operations,
            discover_generic=record_generic,
            discover_confined=record_confined,
        )

    monkeypatch.setattr(build_main, "_route_operations", recording_operations)
    build_main.run_default_build(FIXTURE_PACKS, tmp_path / "out")

    assert called, "the default build performed no pack discovery"
    assert called[0] == "confined", (
        f"default-build discovery used {called[0]!r}; the strictest declared "
        "control must be the one applied"
    )


def test_explicit_recipe_build_accepts_a_recipe_that_declares_no_route(
    tmp_path: Path,
) -> None:
    """`--recipe` still builds a composite or overlay recipe.

    Route behavior now selects pack discovery, but `composite`, `overlay`, and
    self-host recipes declare no route and must keep the generic discovery and
    the exit-0 path they had before. Nothing else drives `cmd_build` with a
    routeless recipe, so without this a public CLI path can regress unseen.
    """
    build_main = import_module("agentbundle.build.main")
    routeless = [
        name
        for name in ("composite-agents-md", "composite-marketplace", "per-pack-overlay")
        if build_main.load_recipe(name).route is None
    ]
    assert routeless, "expected at least one bundled recipe with no declared route"

    for name in routeless:
        args = SimpleNamespace(
            recipe=name,
            packs_dir=str(FIXTURE_PACKS),
            output_dir=str(tmp_path / name),
            pack=None,
        )
        assert build_main.cmd_build(args) == 0, f"{name} must still build"


def test_default_recipe_order_is_derived_and_refusal_capable_route_runs_first() -> None:
    """Build order is declared, non-empty, and puts the refusing route first.

    The order is load-bearing: the Claude route refuses a pack that publishes
    hooks without consent, and that refusal has to precede any route's first
    write. An empty order map would silently fall back to name order, which is
    the ordering that let a refused build leave `output/` behind.
    """
    build_main = import_module("agentbundle.build.main")
    behaviors = _lookup().resolve_route_behaviors(_contract())

    orders = dict(build_main._route_build_orders())
    assert orders, "recipe ordering must not degrade to an empty map"
    assert set(orders) == set(behaviors)
    assert len(set(orders.values())) == len(orders), "build order must be a total order"

    per_pack = [
        name for name in build_main.default_recipes()
        if build_main.load_recipe(name).type != "aggregate"
    ]
    aggregates = [
        name for name in build_main.default_recipes()
        if build_main.load_recipe(name).type == "aggregate"
    ]
    assert list(build_main.default_recipes()) == per_pack + aggregates

    first_route = build_main.load_recipe(per_pack[0]).route
    assert orders[first_route] == min(orders.values())
    assert behaviors[first_route].expected_adapter_projector is not None, (
        "the route that runs first must be the one carrying the consent refusal"
    )


def test_lookup_refuses_a_contract_with_no_route_declarations() -> None:
    """A contract without a route table is refused, not read as empty."""
    lookup = _lookup()
    for reader in (lookup.resolve_route_behaviors, lookup.read_route_declarations):
        with pytest.raises(ValueError, match="no route declarations"):
            reader({})


def test_lookup_refuses_a_route_with_no_registered_behavior() -> None:
    """A declared route no module recognises is refused by name."""
    contract = _contract()
    contract["route"]["invented"] = dict(next(iter(contract["route"].values())))
    contract["route"]["invented"]["manifest-projector"] = {
        "name": "no-such-projector",
        "adapter-projector": "none",
        "admission-policy": "all-packs",
    }
    with pytest.raises(ValueError, match="no unique registered behavior"):
        _lookup().resolve_route_behaviors(contract)


def test_lookup_refuses_two_routes_claiming_one_identity() -> None:
    """A duplicated identity is a refusal, not a silent last-one-wins."""
    contract = _contract()
    first = next(iter(contract["route"]))
    contract["route"]["second-table-key"] = dict(contract["route"][first])
    with pytest.raises(ValueError, match="declared more than once"):
        _lookup().read_route_declarations(contract)


def test_build_order_refuses_rather_than_degrading(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An unreadable ordering source refuses; it must not fall back silently.

    The fallback this replaced returned an empty map, which name-sorted the
    portable route ahead of the refusing one — the ordering that let a refused
    build leave a partial output tree behind.
    """
    build_main = import_module("agentbundle.build.main")
    build_main._route_build_orders.cache_clear()
    monkeypatch.setattr(
        build_main, "_load_distribution_route_contract", lambda: {"route": {}}
    )
    try:
        with pytest.raises(ValueError, match="no route build order"):
            build_main._route_build_orders()
    finally:
        build_main._route_build_orders.cache_clear()


def test_bundled_recipe_declarations_refuse_a_malformed_recipe(
    tmp_path: Path,
) -> None:
    """Each malformed recipe shape is refused with the recipe named."""
    build_main = import_module("agentbundle.build.main")
    cases = [
        ('name = "x"\n', "has no [recipe] table", False),
        ('[recipe]\ntype = "per-pack"\nroute = "apm"\n', "invalid declaration", True),
        ('[recipe]\nname = "x"\ntype = "per-pack"\n', "field 'route' is required", True),
        (
            '[recipe]\nname = "x"\ntype = "composite"\nroute = "apm"\n',
            "field 'route' is not allowed",
            True,
        ),
        (
            '[recipe]\nname = "x"\ntype = "per-pack"\nroute = 3\n',
            "invalid route",
            True,
        ),
    ]
    for index, (body, message, _has_table) in enumerate(cases):
        recipes = tmp_path / f"case{index}"
        recipes.mkdir()
        (recipes / "r.toml").write_text(body, encoding="utf-8", newline="\n")
        with pytest.raises(ValueError, match=re.escape(message)):
            build_main._load_bundled_recipe_declarations(recipes)
