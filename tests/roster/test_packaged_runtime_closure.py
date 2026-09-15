"""Repository-shaped checks on the packaged-runtime closure.

`packages/agentbundle/agentbundle/_data/` carries a copy of each core-pack
script the packaged CLI runs when no installed skill tree is present.
`_runtime_projections` declares those pairs by hand, and
`run_build_check_drift_gates` derives their sibling closure so a declared
runtime cannot load a helper nobody bundled.

These cases read the repository's own pack sources, so they live here rather
than beside the gate: `packages/agentbundle/tests/` is a published tree that
also runs from an sdist, which ships no `packs/`. The gate's behavioural cases
are synthetic and stay there.
"""

from __future__ import annotations

from pathlib import Path

from agentbundle.build.self_host import (
    _RUNTIME_SIBLING_EXEMPTIONS,
    _runtime_projections,
    _runtime_sibling_reaches,
)

ROOT = Path(__file__).parents[2]


def _observed_reaches() -> dict[str, set[str]]:
    """Map each bundled runtime to the sibling names it loads."""
    observed: dict[str, set[str]] = {}
    for source, bundled in _runtime_projections(ROOT):
        reaches, unreadable = _runtime_sibling_reaches(
            source.read_text(encoding="utf-8")
        )
        assert not unreadable, (
            f"{bundled.name} loads a sibling whose name is computed: {unreadable}"
        )
        observed[bundled.name] = reaches
    return observed


def test_runtime_sibling_reaches_derives_the_real_closure() -> None:
    """The derivation matches the repository's actual sibling graph.

    Walks every declared pair rather than one example: a predicate checked
    against a single case cannot show it separates siblings from reaches that
    leave the module's own directory.
    """
    pairs = _runtime_projections(ROOT)
    assert pairs, "no declared pairs; this case has no floor"

    observed = _observed_reaches()

    # Pinned because it is the claim: these are sibling loads under the flat
    # `_data/` layout. `refresh.py` (reached via the skill root) and
    # `surface_resolver.py` (reached via SKILLS_DIR) are deliberately absent —
    # they leave the module's own directory and cannot resolve when packaged.
    assert observed == {
        "workspace_status_engine.py": {"cooling.py", "work_intake_refresh.py"},
        "workspace_status_prune.py": {"workspace_status_engine.py"},
        "work_intake_refresh.py": {"intake_guard.py", "workspace_status_engine.py"},
        "cooling.py": {"close_work.py"},
        "close_work.py": {"file_safety.py"},
        "file_safety.py": set(),
    }

    reached = {name for names in observed.values() for name in names}
    assert "refresh.py" not in reached
    assert "surface_resolver.py" not in reached

    declared = {bundled.name for _, bundled in pairs}
    for owner, names in observed.items():
        for name in names:
            assert name in declared or (owner, name) in _RUNTIME_SIBLING_EXEMPTIONS, (
                f"{owner} loads {name}, which is neither bundled nor exempted"
            )


def test_packaged_runtime_sibling_exemptions_are_live() -> None:
    """No exemption outlives the reach it excuses.

    Liveness is a fact about this repository's sources, so it is asserted here
    rather than in the gate, which runs against whatever tree it is pointed at.
    """
    reached = {
        (owner, name)
        for owner, names in _observed_reaches().items()
        for name in names
    }

    stale = set(_RUNTIME_SIBLING_EXEMPTIONS) - reached
    assert not stale, f"exemptions no longer reached: {sorted(stale)}"
    for key, reason in _RUNTIME_SIBLING_EXEMPTIONS.items():
        assert reason.strip(), f"{key} is exempted without a reason"
