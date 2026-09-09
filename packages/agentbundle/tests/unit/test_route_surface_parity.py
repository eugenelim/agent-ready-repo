"""Contract parity and additive behavior for distribution-route CLI surfaces."""

from __future__ import annotations

import argparse
import tomllib
from collections.abc import Sequence
from importlib import import_module
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
from agentbundle import render as render_engine
from agentbundle.build.adapters import ADAPTERS
from agentbundle.catalogue_tooling import verify as verify_tooling
from agentbundle.commands import diff as diff_cmd
from agentbundle.commands import install as install_cmd
from agentbundle.commands import render as render_cmd
from agentbundle.commands import upgrade as upgrade_cmd
from agentbundle.commands import validate as validate_cmd

build_main = import_module("agentbundle.build.main")


# The pre-change route recipes, in the order the build ran them. Order is
# load-bearing — the aggregate reads what the per-pack recipes wrote — so this
# stays a tuple; a set would render it in an unspecified order.
_PRE_ROUTE_RECIPE_ORDER = (
    "per-pack-claude-plugin",
    "per-pack-apm-package",
    "marketplace",
)
_PRE_ROUTE_RECIPES = frozenset(_PRE_ROUTE_RECIPE_ORDER)
_PRE_ROUTE_IDENTITIES = frozenset({"claude-plugins", "apm"})
_PRE_OUTPUT_SUBDIRS = frozenset({"claude-plugins", "apm"})
_NON_ROUTE_RECIPES = frozenset(
    {"per-pack-overlay", "composite-agents-md", "composite-marketplace"}
)


def _contract() -> dict[str, Any]:
    """Read the bundled route contract used by the production package."""
    build_dir = Path(build_main.__file__).resolve().parent
    return tomllib.loads(
        (build_dir.parent / "_data" / "distribution-routes.toml").read_text(
            encoding="utf-8"
        )
    )


def _route_recipes() -> dict[str, str]:
    """Map every bundled route-bearing recipe to its declared route."""
    build_dir = Path(build_main.__file__).resolve().parent
    route_of: dict[str, str] = {}
    for path in sorted((build_dir / "recipes").glob("*.toml")):
        body = tomllib.loads(path.read_text(encoding="utf-8"))["recipe"]
        route = body.get("route")
        if isinstance(route, str):
            route_of[body["name"]] = route
    return route_of


def _routes_on(recipe_names: object) -> set[str]:
    """Return declared routes reached by an iterable of recipe names."""
    route_of = _route_recipes()
    return {route_of[name] for name in recipe_names if name in route_of}


def _expected_recipe_order() -> tuple[str, ...]:
    """Rebuild the default recipe order from the recipe and route declarations.

    Independent of `DEFAULT_RECIPES`: aggregates run last because they read what
    the per-pack recipes wrote, and within the per-pack group the route's own
    declared build order decides, so a refusing route precedes a writing one.
    """
    from agentbundle.build import route_lookup

    build_dir = Path(build_main.__file__).resolve().parent
    orders = {
        identity: behavior.build_order
        for identity, behavior in route_lookup.resolve_route_behaviors(
            _contract()
        ).items()
    }
    declarations = []
    for path in sorted((build_dir / "recipes").glob("*.toml")):
        body = tomllib.loads(path.read_text(encoding="utf-8"))["recipe"]
        if isinstance(body.get("route"), str):
            declarations.append(body)
    declarations.sort(
        key=lambda body: (
            body["type"] == "aggregate",
            orders[body["route"]],
            body["name"],
        )
    )
    return tuple(body["name"] for body in declarations)


def _declared_output_subdirs() -> set[str]:
    """Return every output subdirectory declared by the route contract."""
    return {
        body["package-layout"]["output-subdir"]
        for body in _contract()["route"].values()
    }


def _portable_route() -> tuple[str, str, str]:
    """Return the newly admitted route identity, recipe, and output subtree."""
    declared = set(_contract()["route"])
    (identity,) = declared - _PRE_ROUTE_IDENTITIES
    (recipe,) = {
        name for name, route in _route_recipes().items() if route == identity
    }
    output_subdir = _contract()["route"][identity]["package-layout"]["output-subdir"]
    return identity, recipe, output_subdir


def _render_to(
    output: Path, fixture: Path, recipes: Sequence[str]
) -> dict[str, bytes]:
    """Render to a test-owned directory and return its regular-file bytes."""
    render_engine.render_pack_to_dir(fixture, output, recipes=recipes)
    rendered = {
        path.relative_to(output).as_posix(): path.read_bytes()
        for path in output.rglob("*")
        if path.is_file()
    }
    for path in output.rglob("*"):
        path.chmod(0o755 if path.is_dir() else 0o644)
    return rendered


def test_every_declared_route_reaches_the_recipe_surfaces() -> None:
    """Pack validation and install emission match route-bearing recipes."""
    declared = set(_contract()["route"])

    assert _routes_on(validate_cmd.valid_recipes()) == declared
    assert set(validate_cmd.valid_recipes()) - set(_route_recipes()) == _NON_ROUTE_RECIPES
    assert _routes_on(install_cmd._legacy_install_route_recipes()) == declared
    # Pin emission order against the recipes themselves, not against the
    # accessor install delegates to: that would compare a function's result
    # against itself rather than against the declarations.
    assert tuple(install_cmd._legacy_install_route_recipes()) == _expected_recipe_order()


def test_every_declared_output_subdir_reaches_install_subtree_surfaces(
    tmp_path: Path,
) -> None:
    """Discovery, pack paths, roots, and iteration share the declared subdirs."""
    declared = _declared_output_subdirs()
    assert set(install_cmd._distribution_output_subdirs()) == declared

    subtrees = install_cmd._dist_tree_pack_subtrees(tmp_path, "demo")
    assert {path.parent.name for path in subtrees} == declared
    for subtree in subtrees:
        subtree.mkdir(parents=True)
        (subtree / "artifact.txt").write_text("x", encoding="utf-8", newline="\n")

    discovered = install_cmd._scan_dist_tree_artifacts(tmp_path, "demo")
    assert {path.parents[1].name for path in discovered} == declared
    assert {path.parent for path in discovered} == set(subtrees)
    # The artifact scan feeds a deletion prompt, so it stays path-sorted for
    # determinism rather than following the build order the messages use.
    assert list(discovered) == sorted(discovered)


def test_every_declared_output_subdir_reaches_each_dist_tree_detection() -> None:
    """Install, diff, and upgrade independently recognise every route prefix."""
    declared = _declared_output_subdirs()
    detected_by_install = {
        subdir
        for subdir in declared
        if install_cmd._is_dist_tree_path(f"{subdir}/demo/file.txt")
    }
    detected_by_diff = {
        subdir
        for subdir in declared
        if diff_cmd._was_dist_tree_install(
            SimpleNamespace(files={f"{subdir}/demo/file.txt": object()})
        )
    }
    detected_by_upgrade = {
        subdir
        for subdir in declared
        if upgrade_cmd._was_dist_tree_install(
            SimpleNamespace(files={f"{subdir}/demo/file.txt": object()})
        )
    }

    assert detected_by_install == declared
    assert detected_by_diff == declared
    assert detected_by_upgrade == declared
    assert install_cmd._is_dist_tree_path("marketplace.json")
    assert diff_cmd._was_dist_tree_install(SimpleNamespace(files={"marketplace.json": {}}))
    assert upgrade_cmd._was_dist_tree_install(
        SimpleNamespace(files={"marketplace.json": {}})
    )


def test_render_targets_match_declared_selectable_routes_and_adapters() -> None:
    """Route targets come from the route accessor; adapter targets stay admitted."""
    route_targets = build_main.selectable_render_target_recipes()

    # Rebuild the expectation from the contract and the recipe declarations.
    # Comparing `_select_recipes` against the accessor it delegates to would be
    # the same function on both sides of the assertion.
    route_of = _route_recipes()
    expected: dict[str, set[str]] = {}
    for route_identity, body in _contract()["route"].items():
        target = body["manifest-projector"].get("adapter-projector")
        if target == "none":
            target = route_identity
        expected[target] = {
            name for name, route in route_of.items() if route == route_identity
        }
    assert {target: set(names) for target, names in route_targets.items()} == expected

    for target in route_targets:
        assert render_cmd._canonicalise_target(target) == target
        assert set(render_cmd._select_recipes(target)) == expected[target]

    adapter_only_targets = set(ADAPTERS) - set(route_targets)
    assert adapter_only_targets
    for target in adapter_only_targets:
        assert render_cmd._canonicalise_target(target) == target
        assert render_cmd._select_recipes(target) == []


def test_catalogue_verification_roots_match_declared_output_subdirs() -> None:
    """Output-drift verification includes every declared route subtree."""
    assert verify_tooling._distribution_output_subdirs() == _declared_output_subdirs()
    marketplace_roots = {
        body["package-layout"]["output-subdir"]
        for body in _contract()["route"].values()
        if body["marketplace-projector"] != "none"
    }
    assert set(verify_tooling._marketplace_projected_output_subdirs()) == marketplace_roots


def test_portable_recipe_changes_validation_from_rejected_to_accepted(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """The already-declared portable recipe is the only validation addition."""
    _identity, portable_recipe, _output_subdir = _portable_route()
    (tmp_path / "pack.toml").write_text(
        '[pack]\nname = "portable"\nversion = "0.1"\n'
        f'recipes = ["{portable_recipe}"]\n',
        encoding="utf-8",
        newline="\n",
    )
    args = argparse.Namespace(pack_path=str(tmp_path), strict=False)

    with monkeypatch.context() as context:
        context.setattr(
            validate_cmd,
            "valid_recipes",
            lambda: _PRE_ROUTE_RECIPES | _NON_ROUTE_RECIPES,
        )
        assert validate_cmd.run(args) == 1
        assert f"unknown recipe {portable_recipe!r}" in capsys.readouterr().err

    assert validate_cmd.run(args) == 0
    assert capsys.readouterr().err == ""


def test_install_route_emission_is_additive_and_preserves_existing_bytes(
    tmp_path: Path,
) -> None:
    """Portable output is added without changing any pre-existing rendered byte."""
    _identity, _recipe, output_subdir = _portable_route()
    fixture = (
        Path(__file__).resolve().parent.parent
        / "fixtures"
        / "distribution-routes"
        / "witness-packs"
        / "portable"
    )
    before = _render_to(tmp_path / "before", fixture, _PRE_ROUTE_RECIPE_ORDER)
    after = _render_to(
        tmp_path / "after", fixture, install_cmd._legacy_install_route_recipes()
    )

    assert before
    assert all(after[path] == content for path, content in before.items())
    assert not any(path.startswith(f"{output_subdir}/") for path in before)
    assert any(path.startswith(f"{output_subdir}/") for path in after)


def test_ordered_install_messages_gain_the_declared_output_subdir() -> None:
    """Both user-visible ordered messages change purely by appending."""
    after_subdirs = list(install_cmd._distribution_output_subdirs())
    before_subdirs = ["claude-plugins", "apm"]
    # The change is additive only if the routes that existed before keep both
    # their membership and their positions in what an adopter reads.
    assert after_subdirs[: len(before_subdirs)] == before_subdirs

    before_route_paths = [f"/repo/{subdir}/demo/" for subdir in before_subdirs]
    after_route_paths = [f"/repo/{subdir}/demo/" for subdir in after_subdirs]

    assert install_cmd._emitted_install_routes_line("demo", before_route_paths) == (
        "emitted install routes for demo at /repo/claude-plugins/demo/ "
        "and /repo/apm/demo/"
    )
    assert install_cmd._emitted_install_routes_line("demo", after_route_paths) == (
        "emitted install routes for demo at /repo/claude-plugins/demo/, "
        "/repo/apm/demo/, and /repo/agent-plugins/demo/"
    )
    assert install_cmd._dist_tree_removal_lines(
        [f"{subdir}/demo" for subdir in before_subdirs]
    ) == [
        "install --force will REMOVE pre-RFC-0012 dist-tree subtree: "
        "claude-plugins/demo/ (recursively)",
        "install --force will REMOVE pre-RFC-0012 dist-tree subtree: "
        "apm/demo/ (recursively)",
    ]
    assert install_cmd._dist_tree_removal_lines(
        [f"{subdir}/demo" for subdir in after_subdirs]
    ) == [
        "install --force will REMOVE pre-RFC-0012 dist-tree subtree: "
        "claude-plugins/demo/ (recursively)",
        "install --force will REMOVE pre-RFC-0012 dist-tree subtree: "
        "apm/demo/ (recursively)",
        "install --force will REMOVE pre-RFC-0012 dist-tree subtree: "
        "agent-plugins/demo/ (recursively)",
    ]


def test_catalogue_drift_starts_reporting_the_portable_tree(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A planted portable-tree defect changes from ignored to reported."""
    _identity, _recipe, output_subdir = _portable_route()
    root = tmp_path / "catalogue"
    configured = root / "dist" / output_subdir / "portable" / "artifact.txt"
    configured.parent.mkdir(parents=True)
    configured.write_text("stale", encoding="utf-8", newline="\n")
    fresh_tmp = tmp_path / "fresh"
    (fresh_tmp / "dist").mkdir(parents=True)
    config = SimpleNamespace(paths=SimpleNamespace(build_output="dist"))

    with monkeypatch.context() as context:
        context.setattr(
            verify_tooling,
            "_distribution_output_subdirs",
            lambda: _PRE_OUTPUT_SUBDIRS,
        )
        assert verify_tooling._step_output_drift(root, config, None, fresh_tmp) == []

    diagnostics = verify_tooling._step_output_drift(root, config, None, fresh_tmp)
    assert [(item.code, item.path) for item in diagnostics] == [
        ("CAT-V-014", f"dist/{output_subdir}/portable/artifact.txt")
    ]


def test_portable_dist_tree_path_changes_each_detection_from_false_to_true() -> None:
    """The new output prefix is additive for all three detection surfaces."""
    _identity, _recipe, output_subdir = _portable_route()
    relpath = f"{output_subdir}/portable/artifact.txt"
    before_prefixes = tuple(f"{subdir}/" for subdir in sorted(_PRE_OUTPUT_SUBDIRS))
    state = SimpleNamespace(files={relpath: object()})

    assert not relpath.startswith(before_prefixes)
    assert install_cmd._is_dist_tree_path(relpath)
    assert diff_cmd._was_dist_tree_install(state)
    assert upgrade_cmd._was_dist_tree_install(state)


def test_manifest_verification_reports_an_unusable_route_contract(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """An unreadable route contract is a diagnostic, never a silent pass.

    The subtree this step validates is read from the contract, so losing the
    contract disables the whole step — which is exactly the looks-like-a-gate
    failure the step's own fail-closed rail exists to prevent.
    """
    def _boom() -> tuple[str, ...]:
        raise OSError("contract unavailable")

    monkeypatch.setattr(
        verify_tooling, "_marketplace_projected_output_subdirs", _boom
    )
    root = tmp_path / "root"
    (root / ".claude-plugin").mkdir(parents=True)
    (root / ".claude-plugin" / "marketplace.json").write_text(
        '{"plugins": []}', encoding="utf-8", newline="\n"
    )

    diagnostics = verify_tooling._step_plugin_manifests(root, None, None, tmp_path)

    assert [item.code for item in diagnostics] == ["CAT-V-013"]
    assert "unavailable" in diagnostics[0].message


def test_build_check_reports_an_unusable_route_contract(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """The drift gate names an unusable contract instead of raising through."""
    from agentbundle.build import self_host

    packs_dir = tmp_path / "packs"
    (packs_dir / "demo").mkdir(parents=True)
    (packs_dir / "demo" / "pack.toml").write_text(
        '[pack]\nname = "demo"\nversion = "0.1"\n', encoding="utf-8", newline="\n"
    )

    def _boom() -> dict[str, object]:
        raise ValueError("contract is not readable")

    monkeypatch.setattr(self_host, "_load_distribution_route_contract", _boom)
    rc = self_host.run_build_check_drift_gates(tmp_path / "out", packs_dir)

    assert rc != 0
    assert "distribution route contract is unusable" in capsys.readouterr().err
