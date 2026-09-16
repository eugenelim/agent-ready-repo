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
    _library_mirrors,
    _mirrored_pack_sources,
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


def test_library_mirrors_are_declared_and_identical() -> None:
    """Every hand-written mirror of a pack script is written by build-self.

    `catalogue_tooling/file_safety.py` sat outside the declared pairs and so was
    maintained by hand: two tests compared it after the fact, but nothing wrote
    it. Asserting the pair is declared — not merely that the bytes match today —
    is what keeps it on the `make build-self` path.
    """
    mirrors = _library_mirrors(ROOT)
    assert mirrors, "no declared library mirrors; this case has no floor"

    for source, mirror in mirrors:
        assert source.is_file(), f"mirror source missing: {source}"
        assert mirror.is_file(), f"mirror destination missing: {mirror}"
        assert mirror.read_bytes() == source.read_bytes(), (
            f"{mirror.relative_to(ROOT)} must be byte-identical to "
            f"{source.relative_to(ROOT)}; run `make build-self`"
        )

    assert (
        ROOT / "packages/agentbundle/agentbundle/catalogue_tooling/file_safety.py"
    ) in {mirror for _, mirror in mirrors}


def test_mirrored_pack_sources_is_the_union_the_gate_walks() -> None:
    """The writer and the drift gate see every pair, runtime and mirror alike.

    A mirror declared in its own list but left out of the union would be written
    by nothing and gated by nothing, which is the state this change removes.
    """
    union = _mirrored_pack_sources(ROOT)
    assert set(union) == set(_runtime_projections(ROOT)) | set(_library_mirrors(ROOT))
    assert len(union) == len(_runtime_projections(ROOT)) + len(_library_mirrors(ROOT))


def test_library_mirrors_stay_out_of_the_flat_data_layout() -> None:
    """A mirror is not a `_data/` sibling, so it carries no closure obligation.

    Pinned because the split is the claim: putting one of these in
    `_runtime_projections` would make the sibling-closure derivation reason about
    a module that is reached by import, not by path.
    """
    data_dir = ROOT / "packages/agentbundle/agentbundle/_data"
    for _, mirror in _library_mirrors(ROOT):
        assert mirror.parent != data_dir, (
            f"{mirror.relative_to(ROOT)} belongs in `_runtime_projections`"
        )
    for _, bundled in _runtime_projections(ROOT):
        assert bundled.parent == data_dir, (
            f"{bundled.relative_to(ROOT)} belongs in `_library_mirrors`"
        )
