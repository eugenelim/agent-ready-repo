"""Walk coverage: full closure (AC-0019) and cross-kind walk (AC-0020).

T3: Mode TDD. Tests for the closure walk being a full transitive closure (not
one hop) and crossing artifact kinds (intent → brief → spec, intent → spec via
Discovery:).

Two failure shapes T2 hit — avoided here:
1. Green suite over a dead branch: ``test_real_filesystem_brief_terminus_walk``
   runs with no injected seams under ``tmp_path``, exercising the default
   confined reader.
2. Unconfined path: all path derivation stays inside the module; no new
   field-value-to-path construction bypasses the confined reader.

Covers AC-0019 and AC-0020 of ``docs/specs/closure-eligibility-check/``.
Also asserts the Always-do rail on Slug: identity (slug ≠ filename stem).
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from typing import Any

# ── Load the module under test ─────────────────────────────────────────────────
# Unique sys.modules key to isolate this suite from T2 (test_closure_index_bounds).

_SCRIPTS = (
    Path(__file__).resolve().parents[3]
    / ".apm" / "skills" / "close-work" / "scripts"
)

# Literal paths: the pack-boundary lint cannot prove a computed join stays
# inside the owning pack, and it is right not to try.
_MODULE_PATHS = {
    "closure_index": _SCRIPTS / "closure_index.py",
    "closure_terminality": _SCRIPTS / "closure_terminality.py",
}


def _load(name: str, key: str):
    """Load a close-work script by absolute path under a unique sys.modules key."""
    spec = importlib.util.spec_from_file_location(key, _MODULE_PATHS[name])
    assert spec and spec.loader, f"no module at {_MODULE_PATHS[name]}"
    module = importlib.util.module_from_spec(spec)
    sys.modules[key] = module
    spec.loader.exec_module(module)
    return module


ci = _load("closure_index", "closure_index__walk_t3")

_fx_spec = importlib.util.spec_from_file_location(
    "closure_graph_fixture__walk", Path(__file__).resolve().parent / "closure_graph_fixture.py"
)
assert _fx_spec and _fx_spec.loader
_fx = importlib.util.module_from_spec(_fx_spec)
sys.modules["closure_graph_fixture__walk"] = _fx
_fx_spec.loader.exec_module(_fx)

# ── Fake root paths ────────────────────────────────────────────────────────────

ROOT = Path("/fake/root")
INTENTS_DIR = ROOT / "docs" / "product" / "intents"
BRIEFS_DIR = ROOT / "docs" / "product" / "briefs"
SPECS_DIR = ROOT / "docs" / "specs"


# ── Snapshot helpers for snapshot_provider injection ─────────────────────────


def _snapshot(
    *,
    relations: list[dict[str, Any]] | None = None,
    provenance: list[dict[str, Any]] | None = None,
    diagnostics: list[dict[str, Any]] | None = None,
    artifacts: dict[str, str] | None = None,
    classifications: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Build a minimal valid delivery snapshot for test injection.

    When *artifacts* is omitted, the dict is auto-populated from the spec and
    brief identifiers present in *relations* using the canonical path grammar.
    """
    _rels = relations or []
    if artifacts is None:
        _arts: dict[str, str] = {}
        for _rel in _rels:
            for _id_key, _prefix, _path_tmpl in (
                ("spec", "spec:", "docs/specs/{slug}/spec.md"),
                ("brief", "brief:", "docs/product/briefs/{slug}.md"),
            ):
                _val = _rel.get(_id_key, "")
                if _val.startswith(_prefix) and _val not in _arts:
                    _slug = _val[len(_prefix):]
                    _arts[_val] = _path_tmpl.format(slug=_slug)
    else:
        _arts = artifacts
    return {
        "schema_version": 1,
        "complete": True,
        "relations": _rels,
        "classifications": classifications or [],
        "provenance": provenance or [],
        "diagnostics": diagnostics or [],
        "artifacts": _arts,
    }


def _direct(intent_slug: str, spec_slug: str) -> dict[str, Any]:
    """Build a direct-delivery relation record."""
    return {
        "type": "direct-delivery",
        "route": "spec",
        "intent": f"intent:{intent_slug}",
        "spec": f"spec:{spec_slug}",
        "basis": {"intent": "Decomposed", "spec": "Discovery"},
    }


def _coord(intent_slug: str, brief_slug: str, spec_slug: str) -> dict[str, Any]:
    """Build a coordinated-delivery relation record."""
    return {
        "type": "coordinated-delivery",
        "route": "brief",
        "intent": f"intent:{intent_slug}",
        "brief": f"brief:{brief_slug}",
        "spec": f"spec:{spec_slug}",
        "basis": {"brief": "Parent intent", "intent": "Decomposed", "spec": "Brief"},
    }


# ── Preamble content builders ──────────────────────────────────────────────────
# These produce minimal preamble strings for in-memory fixtures.
# Same contract as T2 helpers; redeclared here because test files are not
# importable as modules across suites.


def _intent(
    slug: str,
    status: str = "Accepted",
    parent: str | None = None,
    decomposed: str | None = None,
) -> str:
    """Build a minimal intent preamble."""
    lines = [f"- **Slug:** {slug}", f"- **Status:** {status}"]
    if parent:
        lines.append(f"- **Parent intent:** intent:{parent}")
    if decomposed:
        lines.append(f"- **Decomposed:** 2026-09-19 {decomposed}")
    lines.append("")
    return "\n".join(lines)


def _brief(
    slug: str,
    status: str = "Executing",
    parent: str | None = None,
) -> str:
    """Build a minimal brief preamble."""
    lines = [f"- **Slug:** {slug}", f"- **Status:** {status}"]
    if parent:
        lines.append(f"- **Parent intent:** intent:{parent}")
    lines.append("")
    return "\n".join(lines)


def _spec(
    slug: str,
    status: str = "Implementing",
    brief: str | None = None,
    discovery: str | None = None,
) -> str:
    """Build a minimal spec preamble."""
    # A spec carries no ``Slug:``: 0 of 487 in the corpus do. Its
    # identity is its directory name, per the shipped convention.
    lines = [f"- **Status:** {status}"]
    if brief:
        lines.append(f"- **Brief:** brief:{brief}")
    if discovery:
        lines.append(f"- **Discovery:** {discovery}")
    lines.append("")
    return "\n".join(lines)


# ── In-memory filesystem ───────────────────────────────────────────────────────


class FakeFS:
    """In-memory filesystem for injectable seams.

    The real-filesystem tests use ``tmp_path`` with proper nested layout.
    """

    def __init__(self, files: dict[str, str]):
        self.files = files

    def reader(self, path: Path) -> str:
        key = str(path)
        if key not in self.files:
            raise FileNotFoundError(path)
        return self.files[key]


def _build(
    fs: FakeFS,
    ancestor_slug: str,
    ancestor_terminus: str,
    snapshot_provider=None,
) -> dict:
    """Invoke the module-private closure builder with injected seams."""
    return ci._build_descendant_closure(
        ancestor_slug,
        ancestor_terminus,
        ROOT,
        _reader=fs.reader,
        _snapshot_provider=snapshot_provider,
        _graph_provider=_fx.graph_provider_from_files(fs.files, ROOT),
    )


# ── AC-0019: Full transitive closure, not one hop ─────────────────────────────


def test_ac0019_three_level_fixture_returns_all_levels() -> None:
    """The descendant set is the full transitive closure, not one hop (AC-0019).

    Fixture models the work-item-capture-and-disposition tree (measured
    2026-09-26): Accepted ancestor with ``children`` terminus → four child
    intents each Accepted with ``spec`` terminus → four grandchild specs via
    ``Discovery:``.  A one-hop implementation stops at the four children and
    misses the four grandchild specs, producing 4 descendants instead of 8.

    Three node levels, two artifact kinds (intent and spec), two edges traversed.
    """
    ancestor_slug = "work-item-capture-and-disposition"

    # Four children, each with spec terminus.
    children: list[tuple[str, str]] = [
        ("work-item-capture", "Shipped"),      # terminal
        ("work-item-prioritisation", "Accepted"),
        ("work-item-delegation", "Accepted"),
        ("work-item-closeout", "Accepted"),
    ]
    # Four grandchild specs, one per child (one-to-one direct-delivery).
    grandchildren: list[tuple[str, str, str]] = [
        ("spec-capture", "Shipped", "work-item-capture"),
        ("spec-prioritisation", "Implementing", "work-item-prioritisation"),
        ("spec-delegation", "Implementing", "work-item-delegation"),
        ("spec-closeout", "Implementing", "work-item-closeout"),
    ]

    files: dict[str, str] = {
        str(INTENTS_DIR / f"{ancestor_slug}.md"): _intent(
            ancestor_slug, decomposed="children"
        ),
    }
    for child_slug, child_status in children:
        files[str(INTENTS_DIR / f"{child_slug}.md")] = _intent(
            child_slug, status=child_status, parent=ancestor_slug, decomposed="spec"
        )
    for spec_slug, spec_status, child_slug in grandchildren:
        discovery = f"docs/product/intents/{child_slug}.md"
        files[str(SPECS_DIR / spec_slug / "spec.md")] = _spec(
            spec_slug, status=spec_status, discovery=discovery
        )

    expected_children = {slug for slug, _ in children}
    expected_specs = {slug for slug, _, _ in grandchildren}
    expected_all = expected_children | expected_specs

    fs = FakeFS(files)
    # Inject a snapshot that maps each child intent to its one grandchild spec.
    snap = _snapshot(relations=[
        _direct("work-item-capture", "spec-capture"),
        _direct("work-item-prioritisation", "spec-prioritisation"),
        _direct("work-item-delegation", "spec-delegation"),
        _direct("work-item-closeout", "spec-closeout"),
    ])
    result = _build(fs, ancestor_slug, "children", snapshot_provider=lambda _r: snap)

    assert {slug for _, slug in result} == expected_all, (
        f"expected {sorted(expected_all)}, got {sorted(result)}\n"
        "a one-hop implementation would stop at the 4 children and miss the 4 specs"
    )
    assert len(result) == 8, f"expected 8 descendants, got {len(result)}"

    # Kind check: children are intents, grandchildren are specs.
    for child_slug, _ in children:
        assert result[("intent", child_slug)].kind == "intent", (
            f"child '{child_slug}' should be kind='intent'"
        )
    for spec_slug, _, _ in grandchildren:
        assert result[("spec", spec_slug)].kind == "spec", (
            f"grandchild '{spec_slug}' should be kind='spec'"
        )


# ── AC-0020: Cross-kind walk ───────────────────────────────────────────────────


def test_ac0020_brief_terminus_inverts_parent_intent_over_briefs() -> None:
    """The ``brief`` terminus inverts ``Parent intent:`` over briefs (AC-0020 phase 1).

    Finds briefs whose ``Parent intent:`` matches the ancestor, not by reading
    a body table. Unrelated briefs (different parent) must not appear.
    """
    ancestor_slug = "lifecycle-and-closure"
    brief_slug = "intent-lifecycle-and-closure"
    unrelated_slug = "unrelated-brief"

    files: dict[str, str] = {
        str(INTENTS_DIR / f"{ancestor_slug}.md"): _intent(
            ancestor_slug, decomposed="brief"
        ),
        str(BRIEFS_DIR / f"{brief_slug}.md"): _brief(
            brief_slug, parent=ancestor_slug
        ),
        str(BRIEFS_DIR / f"{unrelated_slug}.md"): _brief(
            unrelated_slug, parent="some-other-intent"
        ),
    }

    fs = FakeFS(files)
    # Inject a snapshot with one coordinated-delivery relation for the matching
    # brief. The spec slug is a placeholder; the spec file does not exist in
    # FakeFS, so _get_fields returns {} and no spec is added to the result.
    snap = _snapshot(relations=[
        _coord(ancestor_slug, brief_slug, "placeholder-spec"),
    ])
    result = _build(fs, ancestor_slug, "brief", snapshot_provider=lambda _r: snap)

    assert ("brief", brief_slug) in result, f"expected brief '{brief_slug}' in closure"
    assert ("brief", unrelated_slug) not in result, (
        "brief with a different Parent intent: must not appear"
    )
    assert result[("brief", brief_slug)].kind == "brief"


def test_ac0020_brief_terminus_inverts_brief_field_over_specs() -> None:
    """The ``brief`` terminus also inverts ``Brief:`` over specs (AC-0020 phase 2).

    After finding the brief via ``Parent intent:``, finds specs whose ``Brief:``
    field points to that brief slug. Does not read a body table. Specs pointing
    to a different brief must not appear.
    """
    ancestor_slug = "lifecycle-and-closure"
    brief_slug = "intent-lifecycle-and-closure"
    spec_slugs = ["closure-eligibility-check", "lifecycle-state-contract"]
    unrelated_spec_slug = "unrelated-spec"

    files: dict[str, str] = {
        str(INTENTS_DIR / f"{ancestor_slug}.md"): _intent(
            ancestor_slug, decomposed="brief"
        ),
        str(BRIEFS_DIR / f"{brief_slug}.md"): _brief(
            brief_slug, parent=ancestor_slug
        ),
        str(SPECS_DIR / unrelated_spec_slug / "spec.md"): _spec(
            unrelated_spec_slug, brief="other-brief"
        ),
    }
    for spec_slug in spec_slugs:
        files[str(SPECS_DIR / spec_slug / "spec.md")] = _spec(
            spec_slug, brief=brief_slug
        )

    fs = FakeFS(files)
    # Inject a snapshot with two coordinated-delivery relations — one per spec
    # under the brief. The unrelated spec has no relation, so it is excluded.
    snap = _snapshot(relations=[
        _coord(ancestor_slug, brief_slug, spec_slugs[0]),
        _coord(ancestor_slug, brief_slug, spec_slugs[1]),
    ])
    result = _build(fs, ancestor_slug, "brief", snapshot_provider=lambda _r: snap)

    assert ("brief", brief_slug) in result, f"brief '{brief_slug}' must be in closure"
    for spec_slug in spec_slugs:
        assert ("spec", spec_slug) in result, f"spec '{spec_slug}' must be in closure"
    assert ("spec", unrelated_spec_slug) not in result, (
        "spec with a different Brief: must not appear in closure"
    )
    # 1 brief + 2 specs = 3 descendants.
    assert len(result) == 3, (
        f"expected 3 descendants, got {len(result)}: {sorted(result)}"
    )
    for spec_slug in spec_slugs:
        assert result[("spec", spec_slug)].kind == "spec"


def test_ac0020_spec_terminus_inverts_discovery_over_specs() -> None:
    """The ``spec`` terminus finds only specs named in the snapshot (AC-0020).

    The snapshot names one spec for the ancestor; a second spec in the
    filesystem with a different Discovery: target is excluded because it is
    not in the snapshot.  This confirms that close-work does not scan the
    specs collection itself — membership comes from the snapshot alone.
    """
    ancestor_slug = "spec-driven-intent"
    spec_slug = "alpha-spec"
    unrelated_spec_slug = "gamma-spec"

    ancestor_path = f"docs/product/intents/{ancestor_slug}.md"
    other_path = "docs/product/intents/other-intent.md"

    files: dict[str, str] = {
        str(INTENTS_DIR / f"{ancestor_slug}.md"): _intent(
            ancestor_slug, decomposed="spec"
        ),
        str(INTENTS_DIR / "other-intent.md"): _intent("other-intent"),
        str(SPECS_DIR / spec_slug / "spec.md"): _spec(
            spec_slug, discovery=ancestor_path
        ),
        str(SPECS_DIR / unrelated_spec_slug / "spec.md"): _spec(
            unrelated_spec_slug, discovery=other_path
        ),
    }

    fs = FakeFS(files)
    # Snapshot names only alpha-spec; gamma-spec has no relation, so it is excluded.
    snap = _snapshot(relations=[_direct(ancestor_slug, spec_slug)])
    result = _build(fs, ancestor_slug, "spec", snapshot_provider=lambda _r: snap)

    assert ("spec", spec_slug) in result, f"spec '{spec_slug}' must be in closure via snapshot"
    assert ("spec", unrelated_spec_slug) not in result, (
        "spec not in snapshot must not appear"
    )
    assert len(result) == 1, (
        f"expected 1 descendant, got {len(result)}: {sorted(result)}"
    )


# ── Intents-only control: makes AC-0020 load-bearing ──────────────────────────


def test_intents_only_walk_returns_empty_for_brief_terminus_fixture() -> None:
    """An intents-only walk returns empty for a brief-terminus ancestor — wrong answer.

    This is the control that makes the cross-kind step load-bearing rather than
    decorative. If the walk only searches the intents collection, it finds no
    descendants for an ancestor whose only child is a brief. An empty result
    would be misclassified as eligible (no live descendants to block closure).

    The correct cross-kind walk finds the brief and its mapped spec — non-empty,
    with live descendants, correctly returning not-eligible.

    Fixture: one intent ancestor (brief terminus) → one brief (Executing) →
    one spec (Implementing). No intent is a descendant of the ancestor.
    """
    ancestor_slug = "lifecycle-and-closure"
    brief_slug = "intent-lifecycle-and-closure"
    spec_slug = "closure-eligibility-check"

    files: dict[str, str] = {
        str(INTENTS_DIR / f"{ancestor_slug}.md"): _intent(
            ancestor_slug, decomposed="brief"
        ),
        str(BRIEFS_DIR / f"{brief_slug}.md"): _brief(
            brief_slug, parent=ancestor_slug
        ),
        str(SPECS_DIR / spec_slug / "spec.md"): _spec(
            spec_slug, brief=brief_slug
        ),
    }

    fs = FakeFS(files)

    # ── Empty-snapshot walk (the wrong-but-plausible implementation) ──────────
    # An empty snapshot (no delivery relations) causes the brief terminus to find
    # no descendants, mimicking a plausible implementation that checks delivery
    # records but finds none. An implementation that stops here would report
    # "eligible" — wrong, because the brief and its spec are live.
    empty_snap = _snapshot()
    wrong_result = ci._build_descendant_closure(
        ancestor_slug,
        "brief",
        ROOT,
        _reader=fs.reader,
        _snapshot_provider=lambda _r: empty_snap,
        _graph_provider=_fx.graph_provider_from_files(fs.files, ROOT),
    )

    # The empty-snapshot walk finds nothing. This demonstrates that snapshot
    # content — not directory scanning — drives the brief terminus.
    assert len(wrong_result) == 0, (
        f"empty-snapshot walk should return empty closure for brief-terminus ancestor, "
        f"but got {sorted(wrong_result)} — expected the empty (false-eligible) answer"
    )

    # ── Cross-kind walk (the correct implementation) ───────────────────────────
    # Inject a snapshot with both the brief and its spec.
    correct_snap = _snapshot(relations=[
        _coord(ancestor_slug, brief_slug, spec_slug),
    ])
    correct_result = _build(
        fs, ancestor_slug, "brief", snapshot_provider=lambda _r: correct_snap
    )

    assert ("brief", brief_slug) in correct_result, (
        "correct walk must find the live brief"
    )
    assert ("spec", spec_slug) in correct_result, (
        "correct walk must find the live spec via snapshot coordinated-delivery"
    )
    assert len(correct_result) == 2, (
        f"correct walk: expected 2 descendants, got {len(correct_result)}: "
        f"{sorted(correct_result)}"
    )
    # Both are live, so the correct verdict is not-eligible (not eligible).
    # We assert non-empty here; the verdict logic is T4's territory.
    assert len(correct_result) > 0, (
        "correct walk must return non-empty closure (live brief + live spec)"
    )


# ── Identity from Slug:, not filename stem ────────────────────────────────────


def test_slug_field_not_filename_stem_determines_identity() -> None:
    """Slug:, not the filename stem, determines artifact identity (Always-do rail).

    Asserted on a fixture where filename stem ≠ slug. 22 of 153 real intent
    filenames carry an ordinal prefix (measured 2026-09-26); a stem-keyed
    lookup would silently mis-resolve those 22.

    The ancestor file is named ``001-my-intent.md`` but declares
    ``Slug: my-intent``.  Children declare ``Parent intent: intent:my-intent``
    (the slug, not the stem). An implementation using the stem
    ``001-my-intent`` as the parent token would find no children.

    A child also uses a prefixed filename (``002-my-child.md``, slug
    ``my-child``) to confirm the result keyed on slug, not stem.
    """
    ancestor_filename = "001-my-intent.md"
    ancestor_slug = "my-intent"  # slug ≠ stem

    child_filename_prefixed = "002-my-child.md"
    child_slug_prefixed = "my-child"  # slug ≠ stem

    child_filename_plain = "plain-child.md"
    child_slug_plain = "plain-child"

    files: dict[str, str] = {
        str(INTENTS_DIR / ancestor_filename): _intent(
            ancestor_slug, decomposed="children"
        ),
        str(INTENTS_DIR / child_filename_prefixed): _intent(
            child_slug_prefixed,
            parent=ancestor_slug,  # parent token = slug, not filename stem
        ),
        str(INTENTS_DIR / child_filename_plain): _intent(
            child_slug_plain, parent=ancestor_slug
        ),
    }

    fs = FakeFS(files)
    result = _build(fs, ancestor_slug, "children")

    # Children must appear under their Slug: values, not filename stems.
    assert ("intent", child_slug_prefixed) in result, (
        f"'{child_slug_prefixed}' not found; implementation may be using "
        f"filename stem '002-my-child' instead of Slug:"
    )
    assert ("intent", child_slug_plain) in result, f"'{child_slug_plain}' not found"

    # Filename stems must not appear as keys.
    assert ("intent", "001-my-intent") not in result, (
        "ancestor filename stem must not be used as identity"
    )
    assert ("intent", "002-my-child") not in result, (
        "child filename stem must not be used as identity"
    )

    assert len(result) == 2, (
        f"expected 2 descendants, got {len(result)}: {sorted(result)}"
    )


# ── Real filesystem (no injected seams) under tmp_path ────────────────────────


def test_real_filesystem_brief_terminus_walk(tmp_path: Path) -> None:
    """The cross-kind walk runs against the real filesystem with no injected seams.

    Closes the 'green suite over a dead branch' gap: every other test in this
    file injects a reader; this one passes none, so the module's
    default confined reader runs against
    on-disk files.

    Three node levels (ancestor intent → brief → spec), two artifact kinds.
    The spec is nested one level under ``docs/specs/<feature>/spec.md``.
    """
    intents_dir = tmp_path / "docs" / "product" / "intents"
    briefs_dir = tmp_path / "docs" / "product" / "briefs"
    specs_dir = tmp_path / "docs" / "specs"
    intents_dir.mkdir(parents=True)
    briefs_dir.mkdir(parents=True)
    specs_dir.mkdir(parents=True)

    ancestor_slug = "real-fs-ancestor"
    brief_slug = "real-fs-brief"
    # A spec's identity is its directory name, so the expectation is the
    # directory, not a field. Naming them differently here is deliberate: if
    # the walk ever went back to reading a ``Slug:`` field, this would red.
    spec_slug = "real-fs-feature"

    (intents_dir / f"{ancestor_slug}.md").write_text(
        _intent(ancestor_slug, decomposed="brief"), encoding="utf-8"
    )
    (briefs_dir / f"{brief_slug}.md").write_text(
        _brief(brief_slug, parent=ancestor_slug), encoding="utf-8"
    )
    # Spec: nested one level deep.
    spec_feature = specs_dir / spec_slug
    spec_feature.mkdir()
    (spec_feature / "spec.md").write_text(
        _spec(spec_slug, brief=brief_slug), encoding="utf-8"
    )
    # Unrelated spec in a different brief — must not appear.
    other_feature = specs_dir / "other-feature"
    other_feature.mkdir()
    (other_feature / "spec.md").write_text(
        _spec("other-feature", brief="some-other-brief"), encoding="utf-8"
    )

    # No _reader: the default seam executes against the real tree.
    # _snapshot_provider is injected because the real resolver subprocess is not
    # installed in tmp_path. This test targets the default reader
    # seams (the real filesystem path), not the resolver subprocess; a dedicated
    # subprocess test lives in test_closure_delivery_snapshot.py (VI-1101/1103).
    snap = _snapshot(relations=[
        _coord(ancestor_slug, brief_slug, spec_slug),
    ])
    result = ci._build_descendant_closure(
        ancestor_slug,
        "brief",
        tmp_path,
        _snapshot_provider=lambda _r: snap,
    )

    assert ("brief", brief_slug) in result, (
        "real-filesystem walk must find the brief"
    )
    assert ("spec", spec_slug) in result, (
        "real-filesystem walk must find the nested spec"
    )
    assert ("spec", "other-feature") not in result, (
        "spec not in snapshot must not appear"
    )
    assert len(result) == 2, (
        f"expected 2 descendants (brief + spec), got {len(result)}: {sorted(result)}"
    )
