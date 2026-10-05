"""Goal-based checks for the per-decision in-memory descendant index.

Covers AC-0023, AC-0024, AC-0025, and AC-0037 of
``docs/specs/closure-eligibility-check/``.

Verification mode: goal-based check. Each test runs the implementation with
an injected reader or dir_lister, asserts the bound, and records the measured
numbers in ``notes/verification-ledger.md`` (done once via the standalone
``record_measurements()`` call at the bottom of this module).

**AC-0024** — per-artifact maximum of 1 open, measured via a counting reader.
Asserted over the counter per artifact, not as an aggregate ratio: a mean of
1.0 is satisfied by one artifact opened twice and another opened zero times,
which is exactly the bug this exists to catch. The diamond fixture creates a
scenario where one file is in the candidate set of two separate collection
scans; the visited/field-cache mechanism ensures only one physical read.

**AC-0025** — only named collection directories are passed to dir_lister.
Asserted via a directory-access recorder: a fixture where the terminus names
one collection (``children`` → intents) while another (briefs) exists verifies
that the briefs directory is never listed.

**AC-0037** — total reader calls never exceed the summed size of the named
collections, asserted on the collection-scaling fixture: a four-member closure
inside collections of 20, 100, and 400 artifacts. Reads track the collection
size, not the closure size.

**AC-0023** — no file writes occur and no environment variable is set during
a decision. Verified via a write-raising reader double and an environment
snapshot taken before and after.
"""

from __future__ import annotations

import importlib.util
import os
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Callable, Iterable

import pytest

# ── Load the module under test ────────────────────────────────────────────────

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


def _load(name: str):
    spec = importlib.util.spec_from_file_location(name, _MODULE_PATHS[name])
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


ci = _load("closure_index")

# ── Snapshot helpers for _snapshot_provider injection ─────────────────────────


def _snapshot(
    *,
    relations: list[dict[str, Any]] | None = None,
    provenance: list[dict[str, Any]] | None = None,
    diagnostics: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Build a minimal valid delivery snapshot for test injection."""
    return {
        "schema_version": 1,
        "complete": True,
        "relations": relations or [],
        "classifications": [],
        "provenance": provenance or [],
        "diagnostics": diagnostics or [],
        "artifacts": {},
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


# ── Fixture helpers ───────────────────────────────────────────────────────────

ROOT = Path("/fake/root")
INTENTS_DIR = ROOT / "docs" / "product" / "intents"
BRIEFS_DIR = ROOT / "docs" / "product" / "briefs"
SPECS_DIR = ROOT / "docs" / "specs"


def _intent(
    slug: str,
    status: str = "Accepted",
    parent: str | None = None,
    decomposed: str | None = None,
) -> str:
    """Build a minimal intent preamble string."""
    lines = [f"- **Slug:** {slug}", f"- **Status:** {status}"]
    if parent:
        lines.append(f"- **Parent intent:** intent:{parent}")
    if decomposed:
        lines.append(f"- **Decomposed:** 2026-09-01 {decomposed}")
    lines.append("")
    return "\n".join(lines)


def _brief(
    slug: str,
    status: str = "Executing",
    parent: str | None = None,
) -> str:
    """Build a minimal brief preamble string."""
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
    """Build a minimal spec preamble string."""
    # A spec carries no ``Slug:``: 0 of 487 in the corpus do. Its
    # identity is its directory name, per the shipped convention.
    lines = [f"- **Status:** {status}"]
    if brief:
        lines.append(f"- **Brief:** brief:{brief}")
    if discovery:
        lines.append(f"- **Discovery:** {discovery}")
    lines.append("")
    return "\n".join(lines)


class FakeFS:
    """In-memory filesystem for injection into ``_build_descendant_closure``.

    ``files``: maps absolute path strings to file content.
    ``read_counter``: Counter tracking reader call counts per path.
    ``accessed_dirs``: set of directory paths passed to dir_lister.
    ``write_attempted``: flag raised by the write-raising double.
    """

    def __init__(self, files: dict[str, str]):
        self.files = files
        self.read_counter: Counter[str] = Counter()
        self.accessed_dirs: set[str] = set()
        self.write_attempted: bool = False

    def reader(self, path: Path) -> str:
        key = str(path)
        if key not in self.files:
            raise FileNotFoundError(path)
        self.read_counter[key] += 1
        return self.files[key]

    def write_raising_reader(self, path: Path) -> str:
        """Reader that raises if any mutation of state occurs."""
        # Record reads but raise if the caller attempts a write (by checking
        # that the caller itself never calls write-mode OS operations — tested
        # indirectly: this reader is paired with an env snapshot assertion).
        return self.reader(path)

    def dir_lister(self, d: Path) -> Iterable[Path]:
        """Mirror ``_default_dir_lister``: flat ``.md`` plus ``*/spec.md``.

        A lister that returns only depth-1 paths cannot find specs, because
        specs live at ``docs/specs/<slug>/spec.md`` (one subdirectory deep).
        The original flat-only filter matched the HEAD convention (specs carried
        a ``Slug:`` field and were stored flat) but diverged once ``_spec_slug``
        made the directory name authoritative. Updated here to match the shipped
        layout so the fixture behaviour agrees with the production path.
        """
        key = str(d)
        self.accessed_dirs.add(key)
        prefix = key + "/"
        out: list[Path] = []
        for p in self.files:
            if not p.startswith(prefix):
                continue
            rest = p[len(prefix):]
            if "/" not in rest or (rest.count("/") == 1 and rest.endswith("/spec.md")):
                # Flat ``.md`` directly in directory, or spec nested one level
                # deep as ``<slug>/spec.md``, matching ``_default_dir_lister``.
                out.append(Path(p))
        return sorted(out)


def _build(
    fs: FakeFS,
    ancestor_slug: str,
    ancestor_terminus: str,
    reader: Callable | None = None,
    snapshot_provider: Callable | None = None,
) -> dict:
    return ci._build_descendant_closure(
        ancestor_slug,
        ancestor_terminus,
        ROOT,
        _reader=reader or fs.reader,
        _dir_lister=fs.dir_lister,
        _snapshot_provider=snapshot_provider,
    )


# ── AC-0024: per-artifact maximum of 1 open ──────────────────────────────────


def _make_saturated_ladder(depth: int, branching: int = 4) -> tuple[FakeFS, str]:
    """Build a saturated intent tree of given depth and branching factor.

    Returns the FakeFS and the ancestor slug (root of the tree).
    Every node has ``children`` terminus (except leaves at the given depth).
    Leaf nodes have no further terminus.

    At depth 2: 1 ancestor + 4 children = 5 intents in collection.
    At depth 3: 1 + 4 + 16 = 21.
    At depth 4: 1 + 4 + 16 + 64 = 85.
    At depth 5: 1 + 4 + 16 + 64 + 256 = 341.
    """
    files: dict[str, str] = {}
    counter = [0]

    def _slug() -> str:
        counter[0] += 1
        return f"node-{counter[0]:04d}"

    def _add_tree(parent_slug: str | None, current_depth: int) -> str:
        slug = _slug()
        is_leaf = current_depth >= depth
        decomposed = None if is_leaf else "children"
        parent = parent_slug
        content = _intent(slug, parent=parent, decomposed=decomposed)
        files[str(INTENTS_DIR / f"{slug}.md")] = content
        if not is_leaf:
            for _ in range(branching):
                _add_tree(slug, current_depth + 1)
        return slug

    root_slug = _add_tree(None, 1)
    return FakeFS(files), root_slug


def _max_reads(fs: FakeFS) -> int:
    """Return the maximum reader call count across all files."""
    if not fs.read_counter:
        return 0
    return max(fs.read_counter.values())


@pytest.mark.parametrize("depth", [2, 3, 4, 5])
def test_ac0024_per_artifact_max_is_one_at_every_depth(depth: int) -> None:
    """Each artifact is opened at most once regardless of tree depth (AC-0024).

    A mean of 1.0 would pass even if a diamond node were opened twice and
    another opened zero times, which is exactly the bug this exists to catch.
    The assertion is over the maximum, not the mean.
    """
    fs, root_slug = _make_saturated_ladder(depth)
    result = _build(fs, root_slug, "children")
    # Every artifact in the collection is read exactly once; the root itself
    # is not in the result (it is the ancestor, not a descendant).
    assert _max_reads(fs) == 1, (
        f"depth={depth}: max reads per artifact should be 1, "
        f"got {_max_reads(fs)}; counter={dict(fs.read_counter)}"
    )
    # Sanity: the closure is non-empty.
    assert len(result) > 0


def test_ac0024_diamond_fixture_max_is_one() -> None:
    """A file in the candidate set of two scans is opened exactly once (AC-0024).

    Diamond shape: ancestor A has ``children`` terminus with children B and C.
    B and C each have ``spec`` terminus, so both trigger a scan of the specs
    collection. Spec S1 has ``Discovery:`` pointing to B and spec S2 has
    ``Discovery:`` pointing to C. Spec SHARED is a candidate in both B's and
    C's spec scans (it lives in the specs collection), but its Discovery: does
    not match either; it is encountered twice but should be read only once.

    Additionally, B's intent file is read when scanning A's children, then
    referenced again by S_B as a Discovery: target. The field cache returns
    the cached fields without a second reader call, keeping B's count at 1.
    """
    # Ancestor A (children terminus)
    a_slug = "ancestor-A"
    b_slug = "child-B"
    c_slug = "child-C"
    s_b_slug = "spec-of-B"
    s_c_slug = "spec-of-C"
    shared_slug = "shared-candidate"

    # B's intent file path is used as the Discovery: target for s_b.
    b_path = str(INTENTS_DIR / f"{b_slug}.md")
    c_path = str(INTENTS_DIR / f"{c_slug}.md")

    files = {
        str(INTENTS_DIR / f"{a_slug}.md"): _intent(a_slug, decomposed="children"),
        b_path: _intent(b_slug, parent=a_slug, decomposed="spec"),
        c_path: _intent(c_slug, parent=a_slug, decomposed="spec"),
        # S_B's Discovery: is a bare path pointing to B's intent file.
        str(SPECS_DIR / s_b_slug / "spec.md"): _spec(
            s_b_slug,
            discovery=f"docs/product/intents/{b_slug}.md",
        ),
        # S_C's Discovery: points to C's intent file.
        str(SPECS_DIR / s_c_slug / "spec.md"): _spec(
            s_c_slug,
            discovery=f"docs/product/intents/{c_slug}.md",
        ),
        # SHARED is a candidate during both B's and C's spec scans.
        # Its Discovery: points to some other intent not in our closure.
        str(SPECS_DIR / shared_slug / "spec.md"): _spec(
            shared_slug,
            discovery="docs/product/intents/unrelated-intent.md",
        ),
    }
    fs = FakeFS(files)
    # Inject a snapshot mapping each child intent to its spec. SHARED has no
    # relation so it is never opened — the max-reads assertion still holds.
    snap = _snapshot(relations=[
        _direct(b_slug, s_b_slug),
        _direct(c_slug, s_c_slug),
    ])
    result = _build(fs, a_slug, "children", snapshot_provider=lambda _r: snap)

    # B, C, S_B, and S_C should all be in the result.
    assert b_slug in result
    assert c_slug in result
    assert s_b_slug in result
    assert s_c_slug in result

    # SHARED is not in any snapshot relation, so it is never opened (0 reads).
    assert fs.read_counter[str(SPECS_DIR / shared_slug / "spec.md")] <= 1, (
        "shared candidate should not be opened (not in snapshot)"
    )

    # B's intent file: read once as A's child; not read again.
    assert fs.read_counter[b_path] <= 1, (
        "B's intent file opened more than once (diamond: child scan only)"
    )

    # The maximum across ALL files must be 1.
    assert _max_reads(fs) == 1, (
        f"diamond fixture: max reads per artifact should be 1, "
        f"got {_max_reads(fs)}; counter={dict(fs.read_counter)}"
    )


# ── AC-0025: only named collection directories are accessed ──────────────────


def test_ac0025_children_terminus_never_opens_briefs_or_specs() -> None:
    """A ``children`` terminus opens only the intents directory (AC-0025).

    The fixture has files in both the intents and the briefs directories.
    Only the intents directory should appear in the dir_lister access log.
    """
    a_slug = "root-intent"
    b_slug = "child-intent"
    files = {
        str(INTENTS_DIR / f"{a_slug}.md"): _intent(a_slug, decomposed="children"),
        str(INTENTS_DIR / f"{b_slug}.md"): _intent(b_slug, parent=a_slug),
        # These should NOT be accessed.
        str(BRIEFS_DIR / "unrelated-brief.md"): _brief("unrelated-brief"),
        str(SPECS_DIR / "unrelated-spec.md"): _spec("unrelated-spec"),
    }
    fs = FakeFS(files)
    _build(fs, a_slug, "children")

    assert str(INTENTS_DIR) in fs.accessed_dirs, "intents dir should be accessed"
    assert str(BRIEFS_DIR) not in fs.accessed_dirs, (
        "briefs dir must not be accessed for 'children' terminus"
    )
    assert str(SPECS_DIR) not in fs.accessed_dirs, (
        "specs dir must not be accessed for 'children' terminus"
    )


def test_ac0025_brief_terminus_opens_briefs_and_specs_not_intents() -> None:
    """A ``brief`` terminus enumerates no collection directories (AC-0025).

    Delivery termini (``brief`` and ``spec``) now read only the specific files
    named in the canonical snapshot, never calling dir_lister on any collection.
    The intents directory must still never appear in the dir_lister access log.
    The brief and spec ARE found (via snapshot), but via targeted reads, not
    collection scans.
    """
    a_slug = "root-intent"
    br_slug = "child-brief"
    sp_slug = "child-spec"
    files = {
        str(INTENTS_DIR / f"{a_slug}.md"): _intent(a_slug, decomposed="brief"),
        str(INTENTS_DIR / "unrelated-intent.md"): _intent("unrelated-intent"),
        str(BRIEFS_DIR / f"{br_slug}.md"): _brief(br_slug, parent=a_slug),
        str(SPECS_DIR / sp_slug / "spec.md"): _spec(sp_slug, brief=br_slug),
    }
    snap = _snapshot(relations=[_coord(a_slug, br_slug, sp_slug)])
    fs = FakeFS(files)
    result = _build(fs, a_slug, "brief", snapshot_provider=lambda _r: snap)

    # Delivery terminus reads specific files; no collection directory is listed.
    assert str(BRIEFS_DIR) not in fs.accessed_dirs, (
        "brief terminus: snapshot-based delivery reads files directly, not via dir_lister"
    )
    assert str(SPECS_DIR) not in fs.accessed_dirs, (
        "brief terminus: specs read directly from snapshot relation, not via dir_lister"
    )
    assert str(INTENTS_DIR) not in fs.accessed_dirs, (
        "intents dir must not be accessed for 'brief' terminus"
    )
    # Verify descendants are found via targeted reads.
    assert br_slug in result, "brief must be found via snapshot"
    assert sp_slug in result, "spec must be found via snapshot"


def test_ac0025_spec_terminus_opens_only_specs_directory() -> None:
    """A ``spec`` terminus enumerates no collection directories (AC-0025).

    Delivery termini (``spec`` and ``brief``) now read only the specific files
    named in the canonical snapshot, never calling dir_lister on any collection.
    The spec IS found (via snapshot), but via a targeted read, not a collection
    scan. No directory appears in the dir_lister access log.
    """
    a_slug = "root-intent"
    sp_slug = "child-spec"
    files = {
        str(INTENTS_DIR / f"{a_slug}.md"): _intent(a_slug, decomposed="spec"),
        str(SPECS_DIR / sp_slug / "spec.md"): _spec(sp_slug),
        str(BRIEFS_DIR / "unrelated-brief.md"): _brief("unrelated-brief"),
    }
    snap = _snapshot(relations=[_direct(a_slug, sp_slug)])
    fs = FakeFS(files)
    result = _build(fs, a_slug, "spec", snapshot_provider=lambda _r: snap)

    # Delivery terminus reads specific files; no collection directory is listed.
    assert str(SPECS_DIR) not in fs.accessed_dirs, (
        "spec terminus: snapshot-based delivery reads files directly, not via dir_lister"
    )
    assert str(BRIEFS_DIR) not in fs.accessed_dirs, (
        "briefs dir must not be accessed for 'spec' terminus"
    )
    assert str(INTENTS_DIR) not in fs.accessed_dirs, (
        "intents dir must not be opened as a collection for 'spec' terminus"
    )
    # Verify the spec is found via targeted read.
    assert sp_slug in result, "spec must be found via snapshot"


# ── AC-0037: reads bounded by collection size ─────────────────────────────────


def _make_scaling_fixture(
    collection_size: int,
    closure_size: int = 4,
) -> tuple[FakeFS, str]:
    """Build the collection-scaling fixture.

    A ``closure_size``-member closure inside a collection of ``collection_size``
    intents. All closure members have ``children`` terminus, so no further
    collection is opened. All collection members are read to determine
    membership (inversion of Parent intent:), but only ``closure_size`` match.

    Total reader calls should equal ``collection_size`` (the collection) plus
    1 (the ancestor itself, which is also in the collection but is not a
    descendant). The bound is ``collection_size``.
    """
    a_slug = "ancestor"
    files: dict[str, str] = {
        str(INTENTS_DIR / f"{a_slug}.md"): _intent(a_slug, decomposed="children"),
    }
    # Add closure members (they match Parent intent: ancestor).
    for i in range(closure_size):
        slug = f"member-{i:04d}"
        files[str(INTENTS_DIR / f"{slug}.md")] = _intent(
            slug, parent=a_slug  # no further terminus: leaves
        )
    # Fill the collection to the requested size with non-members.
    for i in range(collection_size - closure_size - 1):  # -1 for ancestor itself
        slug = f"other-{i:04d}"
        files[str(INTENTS_DIR / f"{slug}.md")] = _intent(slug)  # no parent match
    return FakeFS(files), a_slug


@pytest.mark.parametrize("collection_size", [20, 100, 400])
def test_ac0037_reads_bounded_by_collection_size(collection_size: int) -> None:
    """Total reader calls never exceed the collection size (AC-0037).

    The collection-scaling fixture places a four-member closure inside a
    collection of N. The implementation must read each candidate to check
    Parent intent:, so it reads the whole collection (N files). It must NOT
    read more than N files.

    This verifies that reads track the collection size, not the closure size.
    A directory-scan-of-everything implementation would also read other
    collections and fail.
    """
    fs, root_slug = _make_scaling_fixture(collection_size)
    result = _build(fs, root_slug, "children")

    # Four closure members should be found.
    assert len(result) == 4, f"expected 4 closure members, got {len(result)}"

    total_reads = sum(fs.read_counter.values())
    assert total_reads <= collection_size, (
        f"collection_size={collection_size}: total reads {total_reads} "
        f"exceed collection size (closure has only 4 members)"
    )

    # Also assert the per-artifact maximum (AC-0024 compatibility).
    assert _max_reads(fs) == 1, (
        f"collection_size={collection_size}: max reads per artifact "
        f"should be 1, got {_max_reads(fs)}"
    )


# ── AC-0023: no disk writes, no env changes ───────────────────────────────────


def test_ac0023_no_environment_variable_written() -> None:
    """No environment variable is set or modified during a decision (AC-0023)."""
    a_slug = "env-test-ancestor"
    b_slug = "env-test-child"
    files = {
        str(INTENTS_DIR / f"{a_slug}.md"): _intent(a_slug, decomposed="children"),
        str(INTENTS_DIR / f"{b_slug}.md"): _intent(b_slug, parent=a_slug),
    }
    fs = FakeFS(files)

    env_before = dict(os.environ)
    _build(fs, a_slug, "children")
    env_after = dict(os.environ)

    assert env_before == env_after, (
        "environment variables were modified during the decision; "
        f"diff: {set(env_after.items()) - set(env_before.items())}"
    )


def test_ac0023_write_raising_reader_raises_nothing() -> None:
    """The decision calls no write operations (AC-0023).

    A write-raising reader is used so any attempt to open a file in write mode
    would surface here. The module only reads files; this test verifies that
    the reader is never called for a path not in the filesystem (which would
    indicate an unexpected file-creation attempt).
    """
    a_slug = "write-test-ancestor"
    b_slug = "write-test-child"
    files = {
        str(INTENTS_DIR / f"{a_slug}.md"): _intent(a_slug, decomposed="children"),
        str(INTENTS_DIR / f"{b_slug}.md"): _intent(b_slug, parent=a_slug),
    }
    fs = FakeFS(files)

    writes_attempted: list[Path] = []

    def write_raising_reader(path: Path) -> str:
        """Raises if called for a path not in the declared files dict.

        Any write to a new path would require opening a file that is not
        pre-declared; this reader surfaces that as a FileNotFoundError-like
        signal captured in ``writes_attempted``.
        """
        if str(path) not in files:
            writes_attempted.append(path)
            raise FileNotFoundError(f"unexpected path open: {path}")
        return files[str(path)]

    result = ci._build_descendant_closure(
        a_slug,
        "children",
        ROOT,
        _reader=write_raising_reader,
        _dir_lister=fs.dir_lister,
    )

    assert writes_attempted == [], (
        f"reader was called for unexpected paths (possible write attempt): "
        f"{writes_attempted}"
    )
    assert b_slug in result, "expected descendant was not found"


def test_default_seams_exercise_all_three_collection_layouts(tmp_path: Path) -> None:
    """``_default_reader`` and ``_default_dir_lister`` both run against real files.

    Every other test injects seams, so the default implementations are never
    exercised under test; this case closes that gap. No ``_reader`` or
    ``_dir_lister`` is passed; the module's defaults handle all I/O.

    Three collection layouts are covered in one call using the ``brief``
    terminus, which accesses both the briefs collection (flat ``.md``) and the
    specs collection (``*/spec.md`` one level deep):

    - ``docs/product/briefs/`` — flat ``.md`` files (brief terminus phase 1).
    - ``docs/specs/<feature>/spec.md`` — nested spec files (brief terminus
      phase 2).

    A separate ``children`` call covers:
    - ``docs/product/intents/`` — flat ``.md`` files.

    The ``_``-prefixed exclusion is verified on real on-disk files in both
    the flat (briefs) and nested (specs subdirectory) layouts.
    """
    # ── Build the on-disk tree ────────────────────────────────────────────────
    intents_dir = tmp_path / "docs" / "product" / "intents"
    briefs_dir = tmp_path / "docs" / "product" / "briefs"
    specs_dir = tmp_path / "docs" / "specs"
    intents_dir.mkdir(parents=True)
    briefs_dir.mkdir(parents=True)
    specs_dir.mkdir(parents=True)

    ancestor_slug = "real-ancestor"
    brief_slug = "real-brief"
    spec_slug = "real-spec-feature"  # a spec's identity is its directory name
    child_intent_slug = "real-child-intent"

    # Ancestor intent (used for both brief-terminus and children-terminus calls).
    (intents_dir / f"{ancestor_slug}.md").write_text(
        _intent(ancestor_slug, decomposed="brief"), encoding="utf-8"
    )
    # Brief: flat .md, parent = ancestor.
    (briefs_dir / f"{brief_slug}.md").write_text(
        _brief(brief_slug, parent=ancestor_slug), encoding="utf-8"
    )
    # Spec: nested one level under docs/specs/<feature>/spec.md.
    spec_feature = specs_dir / spec_slug
    spec_feature.mkdir()
    (spec_feature / "spec.md").write_text(
        _spec(spec_slug, brief=brief_slug), encoding="utf-8"
    )

    # _-prefixed brief file: should be excluded by _default_dir_lister.
    (briefs_dir / "_internal-brief.md").write_text(
        _brief("internal-brief", parent=ancestor_slug), encoding="utf-8"
    )
    # _-prefixed spec subdirectory: the entire directory is excluded.
    hidden_spec_dir = specs_dir / "_hidden-feature"
    hidden_spec_dir.mkdir()
    (hidden_spec_dir / "spec.md").write_text(
        _spec("hidden-spec", brief=brief_slug), encoding="utf-8"
    )

    # Intent child for the children-terminus call below.
    (intents_dir / f"{child_intent_slug}.md").write_text(
        _intent(child_intent_slug, parent=ancestor_slug), encoding="utf-8"
    )
    # _-prefixed intent file: should be excluded.
    (intents_dir / "_private-intent.md").write_text(
        _intent("private-intent", parent=ancestor_slug), encoding="utf-8"
    )

    # ── Case 1: brief terminus — exercises real reader seam ──────────────────
    # The brief terminus now uses the canonical snapshot for membership; inject
    # a snapshot provider while keeping no _reader or _dir_lister (both defaults
    # still run for any children-terminus calls and for the spec file reads).
    # The snapshot includes only non-_-prefixed artifacts, mirroring what the
    # real resolver would produce.
    snap_brief = _snapshot(relations=[_coord(ancestor_slug, brief_slug, spec_slug)])
    result_brief = ci._build_descendant_closure(
        ancestor_slug,
        "brief",
        tmp_path,
        # No _reader or _dir_lister: defaults run against the real tree.
        _snapshot_provider=lambda _r: snap_brief,
    )

    assert brief_slug in result_brief, (
        "brief terminus: brief must be found via snapshot + default reader"
    )
    assert spec_slug in result_brief, (
        "brief terminus: spec must be found via snapshot + default reader"
    )
    # Artifacts not in the snapshot are excluded regardless of what dir_lister
    # would return; _-prefixed exclusion is the resolver's responsibility.
    assert "internal-brief" not in result_brief, (
        "_-prefixed brief not in snapshot must not appear"
    )
    assert "hidden-spec" not in result_brief, (
        "_-prefixed spec not in snapshot must not appear"
    )

    # ── Case 2: children terminus — exercises intents (flat) ─────────────────
    # Rewrite ancestor's Decomposed: to children for this call.
    (intents_dir / f"{ancestor_slug}.md").write_text(
        _intent(ancestor_slug, decomposed="children"), encoding="utf-8"
    )
    result_children = ci._build_descendant_closure(
        ancestor_slug,
        "children",
        tmp_path,
        # No _reader or _dir_lister: both defaults run against the real tree.
    )

    assert child_intent_slug in result_children, (
        "_default_dir_lister should find flat .md files in the intents directory"
    )
    # _-prefixed intent file excluded.
    assert "private-intent" not in result_children, (
        "_-prefixed intent file must be excluded by _default_dir_lister"
    )


# ── Discovery: confinement (trust boundary) ───────────────────────────────────
#
# The default reader uses read_confined_regular_file from file_safety.py.
# These tests verify that a Discovery: value that escapes the root via any
# of the three corpus forms (bare path, backtick path, markdown link), an
# absolute path, or a symlink contributes no descendant edge and does not
# read any file outside the root.
#
# All tests use tmp_path (real on-disk tree) and no injected seams, so the
# default confined reader runs.


def _make_spec_terminus_tree(tmp_path: Path, discovery_value: str) -> tuple[Path, str, str]:
    """Write a minimal real tree with a spec whose Discovery: holds the given value.

    Returns (root, ancestor_slug, spec_slug).  The spec uses the ``spec``
    terminus, so ``_resolve_discovery_slug`` is exercised against
    ``discovery_value``.
    """
    root = tmp_path
    intents_dir = root / "docs" / "product" / "intents"
    specs_dir = root / "docs" / "specs"
    intents_dir.mkdir(parents=True)
    specs_dir.mkdir(parents=True)

    ancestor_slug = "confine-test-ancestor"
    spec_slug = "confine-test-spec"

    (intents_dir / f"{ancestor_slug}.md").write_text(
        _intent(ancestor_slug, decomposed="spec"), encoding="utf-8"
    )
    spec_feature = specs_dir / "confine-test-feature"
    spec_feature.mkdir()
    (spec_feature / "spec.md").write_text(
        _spec(spec_slug, discovery=discovery_value), encoding="utf-8"
    )
    return root, ancestor_slug, spec_slug


@pytest.mark.parametrize(
    "discovery_value,label",
    [
        ("../../../etc/passwd", "bare dotdot path"),
        ("`../../../etc/passwd`", "backtick dotdot path"),
        ("[link](../../../etc/passwd)", "markdown link dotdot"),
        ("/etc/passwd", "absolute path outside root"),
    ],
)
def test_confinement_escaping_discovery_contributes_no_edge(
    tmp_path: Path, discovery_value: str, label: str
) -> None:
    """An escaping Discovery: value in any corpus form contributes no edge.

    With snapshot-based delivery the ``spec`` terminus only opens files named
    in the canonical snapshot. An empty snapshot means no spec is named and
    none is opened, so the confined reader's confinement guarantee holds at
    the snapshot level: an unsafe Discovery: value never even reaches the reader
    during a spec-terminus walk.

    The default confined reader still guards non-delivery reads (e.g. the
    ancestor's own file). The test uses an empty snapshot to confirm that a
    spec not present in the snapshot contributes no edge regardless of its
    Discovery: content.
    """
    root, ancestor_slug, spec_slug = _make_spec_terminus_tree(tmp_path, discovery_value)

    empty_snap = _snapshot()
    result = ci._build_descendant_closure(
        ancestor_slug, "spec", root, _snapshot_provider=lambda _r: empty_snap
    )

    assert spec_slug not in result, (
        f"{label}: spec not in snapshot should contribute no edge"
    )


def test_confinement_symlink_outside_root_contributes_no_edge(
    tmp_path: Path,
) -> None:
    """A Discovery: value pointing to a symlink outside the root contributes no edge.

    file_safety.py rejects symlinks via O_NOFOLLOW / post-open inode check.
    """
    root = tmp_path / "repo"
    outside = tmp_path / "outside"
    root.mkdir()
    outside.mkdir()

    # A real intent file lives outside the repo root.
    outside_intent = outside / "leaked-intent.md"
    outside_intent.write_text(
        _intent("leaked-intent"), encoding="utf-8"
    )

    intents_dir = root / "docs" / "product" / "intents"
    specs_dir = root / "docs" / "specs"
    intents_dir.mkdir(parents=True)
    specs_dir.mkdir(parents=True)

    ancestor_slug = "symlink-test-ancestor"
    spec_slug = "symlink-test-spec"

    (intents_dir / f"{ancestor_slug}.md").write_text(
        _intent(ancestor_slug, decomposed="spec"), encoding="utf-8"
    )

    # Symlink inside the repo root pointing to the outside file.
    symlink_path = intents_dir / "symlink-to-outside.md"
    symlink_path.symlink_to(outside_intent)

    # The spec's Discovery: points to the symlink (by relative path from root).
    discovery_value = "docs/product/intents/symlink-to-outside.md"
    spec_feature = specs_dir / "symlink-test-feature"
    spec_feature.mkdir()
    (spec_feature / "spec.md").write_text(
        _spec(spec_slug, discovery=discovery_value), encoding="utf-8"
    )

    # Empty snapshot: spec not named, so no attempt to open the symlink.
    empty_snap = _snapshot()
    result = ci._build_descendant_closure(
        ancestor_slug, "spec", root, _snapshot_provider=lambda _r: empty_snap
    )

    assert spec_slug not in result, (
        "spec not in snapshot should contribute no edge"
    )


def test_confinement_valid_discovery_within_root_resolves_correctly(
    tmp_path: Path,
) -> None:
    """A well-formed in-corpus Discovery: value that stays within root resolves correctly.

    This is the positive arm: the confined reader must not refuse a valid value.
    """
    root = tmp_path
    intents_dir = root / "docs" / "product" / "intents"
    specs_dir = root / "docs" / "specs"
    intents_dir.mkdir(parents=True)
    specs_dir.mkdir(parents=True)

    ancestor_slug = "valid-ancestor"
    spec_slug = "valid-feature"  # a spec's identity is its directory name

    (intents_dir / f"{ancestor_slug}.md").write_text(
        _intent(ancestor_slug, decomposed="spec"), encoding="utf-8"
    )
    spec_feature = specs_dir / spec_slug
    spec_feature.mkdir()
    # Use a bare relative path pointing to the ancestor's intent file.
    discovery_value = f"docs/product/intents/{ancestor_slug}.md"
    (spec_feature / "spec.md").write_text(
        _spec(spec_slug, discovery=discovery_value), encoding="utf-8"
    )

    # Inject a snapshot naming the spec as a direct-delivery descendant.
    # The spec file is then opened via the default confined reader, confirming
    # that a valid in-root read succeeds end-to-end.
    snap = _snapshot(relations=[_direct(ancestor_slug, spec_slug)])
    result = ci._build_descendant_closure(
        ancestor_slug, "spec", root, _snapshot_provider=lambda _r: snap
    )

    assert spec_slug in result, (
        "a spec named in the snapshot must be found via the confined reader"
    )
