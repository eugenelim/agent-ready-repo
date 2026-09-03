"""Guard cooled exclusion over non-canonical ``work.*`` entry classes.

This is the overflow home for cooled-exclusion criteria covering non-canonical
``work.*`` entry classes. It is separate because ``cooling-scope-closure`` AC13
pins the sibling module's ``test_`` function-name set.
"""

import importlib.util
import sys
from pathlib import Path

import pytest

# A bare sibling import resolves only under pytest's prepend import mode; this suite
# must not depend on the collector's mode.
_HELPERS_PATH = Path(__file__).with_name("test_status_projection_and_context_exclusion.py")
_helpers_spec = importlib.util.spec_from_file_location("cooled_work_entry_helpers", _HELPERS_PATH)
assert _helpers_spec is not None and _helpers_spec.loader is not None
_helpers_module = importlib.util.module_from_spec(_helpers_spec)
sys.modules[_helpers_spec.name] = _helpers_module
try:
    _helpers_spec.loader.exec_module(_helpers_module)
finally:
    sys.modules.pop(_helpers_spec.name, None)

ENGINE_PATH = _helpers_module.ENGINE_PATH
_reconcile_json = _helpers_module._reconcile_json
_record = _helpers_module._record
_spec = _helpers_module._spec
_tree = _helpers_module._tree
_workspace = _helpers_module._workspace


# Define this locally because Ruff rejects an imported fixture shadowed by a test parameter.
@pytest.fixture()
def engine():
    """Load the source engine without depending on an installed projection."""
    spec = importlib.util.spec_from_file_location("wave6_engine", ENGINE_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    try:
        spec.loader.exec_module(module)
    finally:
        sys.modules.pop(spec.name, None)
    return module


def test_cooled_legacy_work_entry_is_excluded_from_both_closeout_consumers(
    tmp_path, engine
) -> None:
    """A cooled `spec/<slug>` membership changes both closeout consumers.

    The no-lifecycle control proves the legacy membership would otherwise count,
    while the resolved cooled set proves the lifecycle record did not vanish
    before the closeout assertions ran.
    """
    control = _tree(tmp_path / "control", lifecycle=False, specs=())
    cooled = _tree(tmp_path / "cooled", records=[_record()], specs=())
    for root in (control, cooled):
        _spec(root, "alpha")
        _workspace(root, queue='"spec/alpha"')

    control_projection = _reconcile_json(control, engine)
    cooled_projection = _reconcile_json(cooled, engine)
    cooled_paths, findings = engine._resolve_cooled_state(cooled)

    assert findings == ()
    assert cooled_paths == {(cooled / "docs/specs/alpha/spec.md").resolve()}
    assert control_projection["closeout"]["all_specs_shipped"] is False
    assert control_projection["initiatives"][0]["queue_empty"] is False
    assert cooled_projection["closeout"]["all_specs_shipped"] is True
    assert cooled_projection["initiatives"][0]["queue_empty"] is True


def test_cooled_bare_work_slug_remains_a_closeout_member(tmp_path, engine) -> None:
    """A cooled artifact's bare work slug remains unsupported and counted.

    More than one structural fact holds this membership out of cooling: it is
    unsupported and does not name the artifact. The falsifiable assertion is
    therefore the unsupported classification plus the resolved, live cooled
    set, while both closeout consumers remain blocked.
    """
    control = _tree(tmp_path / "control", lifecycle=False, specs=())
    cooled = _tree(tmp_path / "cooled", records=[_record()], specs=())
    for root in (control, cooled):
        _spec(root, "alpha")
        _workspace(root, queue='"alpha"')

    control_projection = _reconcile_json(control, engine)
    cooled_projection = _reconcile_json(cooled, engine)
    cooled_paths, findings = engine._resolve_cooled_state(cooled)

    assert findings == ()
    assert cooled_paths == {(cooled / "docs/specs/alpha/spec.md").resolve()}
    assert control_projection["closeout"]["all_specs_shipped"] is False
    assert control_projection["initiatives"][0]["queue_empty"] is False
    assert cooled_projection["closeout"]["all_specs_shipped"] is False
    assert cooled_projection["initiatives"][0]["queue_empty"] is False
    assert ("unsupported_legacy", "alpha") in {
        (finding["code"], finding["path"])
        for finding in cooled_projection["canonical"]["findings"]
    }


def test_alias_cools_legacy_work_membership_for_both_closeout_consumers(
    tmp_path, engine
) -> None:
    """An alias naming a legacy entry's artifact cools its membership.

    The control keeps the same legacy entry live, so the cooled closeout result
    specifically proves alias resolution rather than locator-based cooling.
    """
    control = _tree(tmp_path / "control", lifecycle=False, specs=())
    cooled = _tree(
        tmp_path / "cooled",
        records=[_record(locator="docs/specs/retired/spec.md", aliases=["docs/specs/alpha/spec.md"])],
        specs=(),
    )
    for root in (control, cooled):
        _spec(root, "alpha")
        _workspace(root, queue='"spec/alpha"')

    control_projection = _reconcile_json(control, engine)
    cooled_projection = _reconcile_json(cooled, engine)
    cooled_paths, findings = engine._resolve_cooled_state(cooled)

    assert findings == ()
    assert cooled_paths == {(cooled / "docs/specs/alpha/spec.md").resolve()}
    assert control_projection["closeout"]["all_specs_shipped"] is False
    assert control_projection["initiatives"][0]["queue_empty"] is False
    assert cooled_projection["closeout"]["all_specs_shipped"] is True
    assert cooled_projection["initiatives"][0]["queue_empty"] is True
