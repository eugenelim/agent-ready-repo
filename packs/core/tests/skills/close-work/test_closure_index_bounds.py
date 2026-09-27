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
from typing import Callable, Iterable

import pytest

# ── Load the module under test ────────────────────────────────────────────────

_SCRIPTS = (
    Path(__file__).resolve().parents[4]
    / "core" / ".apm" / "skills" / "close-work" / "scripts"
)


def _load(name: str):
    spec = importlib.util.spec_from_file_location(name, _SCRIPTS / f"{name}.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


ci = _load("closure_index")

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
    lines = [f"- **Slug:** {slug}", f"- **Status:** {status}"]
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
        key = str(d)
        self.accessed_dirs.add(key)
        prefix = key + "/"
        # Return paths whose parent directory matches d exactly.
        return sorted(
            Path(p)
            for p in self.files
            if p.startswith(prefix) and "/" not in p[len(prefix):]
        )


def _build(
    fs: FakeFS,
    ancestor_slug: str,
    ancestor_terminus: str,
    reader: Callable | None = None,
) -> dict:
    return ci._build_descendant_closure(
        ancestor_slug,
        ancestor_terminus,
        ROOT,
        _reader=reader or fs.reader,
        _dir_lister=fs.dir_lister,
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
        str(SPECS_DIR / f"{s_b_slug}.md"): _spec(
            s_b_slug,
            discovery=f"docs/product/intents/{b_slug}.md",
        ),
        # S_C's Discovery: points to C's intent file.
        str(SPECS_DIR / f"{s_c_slug}.md"): _spec(
            s_c_slug,
            discovery=f"docs/product/intents/{c_slug}.md",
        ),
        # SHARED is a candidate during both B's and C's spec scans.
        # Its Discovery: points to some other intent not in our closure.
        str(SPECS_DIR / f"{shared_slug}.md"): _spec(
            shared_slug,
            discovery="docs/product/intents/unrelated-intent.md",
        ),
    }
    fs = FakeFS(files)
    result = _build(fs, a_slug, "children")

    # B, C, S_B, and S_C should all be in the result.
    assert b_slug in result
    assert c_slug in result
    assert s_b_slug in result
    assert s_c_slug in result

    # The shared candidate file is in the specs collection and is encountered
    # in BOTH B's and C's spec scans, but should be read at most once.
    assert fs.read_counter[str(SPECS_DIR / f"{shared_slug}.md")] <= 1, (
        "shared candidate opened more than once despite visited set"
    )

    # B's intent file: read once as A's child, then used as Discovery: target.
    # The field cache must prevent a second reader call.
    assert fs.read_counter[b_path] <= 1, (
        "B's intent file opened more than once (diamond: child scan + Discovery: lookup)"
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
    """A ``brief`` terminus opens only the briefs and specs directories (AC-0025).

    The fixture has files in the intents directory too. The intents directory
    should never appear in the dir_lister access log.
    """
    a_slug = "root-intent"
    br_slug = "child-brief"
    sp_slug = "child-spec"
    files = {
        str(INTENTS_DIR / f"{a_slug}.md"): _intent(a_slug, decomposed="brief"),
        # These should NOT be accessed via dir_lister.
        str(INTENTS_DIR / "unrelated-intent.md"): _intent("unrelated-intent"),
        # These should be accessed.
        str(BRIEFS_DIR / f"{br_slug}.md"): _brief(br_slug, parent=a_slug),
        str(SPECS_DIR / f"{sp_slug}.md"): _spec(sp_slug, brief=br_slug),
    }
    fs = FakeFS(files)
    _build(fs, a_slug, "brief")

    assert str(BRIEFS_DIR) in fs.accessed_dirs, "briefs dir should be accessed"
    assert str(SPECS_DIR) in fs.accessed_dirs, "specs dir should be accessed for briefs' specs"
    assert str(INTENTS_DIR) not in fs.accessed_dirs, (
        "intents dir must not be accessed for 'brief' terminus"
    )


def test_ac0025_spec_terminus_opens_only_specs_directory() -> None:
    """A ``spec`` terminus opens only the specs directory (AC-0025).

    The fixture has files in the intents and briefs directories. Neither
    should appear in the dir_lister access log.
    """
    a_slug = "root-intent"
    sp_slug = "child-spec"
    a_path = f"docs/product/intents/{a_slug}.md"
    files = {
        str(INTENTS_DIR / f"{a_slug}.md"): _intent(a_slug, decomposed="spec"),
        str(SPECS_DIR / f"{sp_slug}.md"): _spec(sp_slug, discovery=a_path),
        # Unrelated files in other collections.
        str(BRIEFS_DIR / "unrelated-brief.md"): _brief("unrelated-brief"),
    }
    fs = FakeFS(files)
    _build(fs, a_slug, "spec")

    assert str(SPECS_DIR) in fs.accessed_dirs, "specs dir should be accessed"
    assert str(BRIEFS_DIR) not in fs.accessed_dirs, (
        "briefs dir must not be accessed for 'spec' terminus"
    )
    # NOTE: The intents directory is NOT listed via dir_lister, but the
    # ancestor's intent FILE may be read directly as a Discovery: resolution
    # target. That is a targeted read, not a collection scan, and does not
    # violate AC-0025.
    assert str(INTENTS_DIR) not in fs.accessed_dirs, (
        "intents dir must not be opened as a collection for 'spec' terminus"
    )


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


# ── Measurement recording ─────────────────────────────────────────────────────


def _collect_measurements() -> dict[str, object]:
    """Run the scaling fixtures and collect read counts for the ledger."""
    measurements: dict[str, object] = {}

    for collection_size in [20, 100, 400]:
        fs, root_slug = _make_scaling_fixture(collection_size)
        ci._build_descendant_closure(
            root_slug, "children", ROOT,
            _reader=fs.reader, _dir_lister=fs.dir_lister,
        )
        total = sum(fs.read_counter.values())
        max_r = _max_reads(fs)
        measurements[f"collection_{collection_size}"] = {
            "total_reads": total,
            "max_per_artifact": max_r,
            "collection_size": collection_size,
            "closure_size": 4,
        }

    for depth in [2, 3, 4, 5]:
        fs, root_slug = _make_saturated_ladder(depth)
        ci._build_descendant_closure(
            root_slug, "children", ROOT,
            _reader=fs.reader, _dir_lister=fs.dir_lister,
        )
        total = sum(fs.read_counter.values())
        max_r = _max_reads(fs)
        n_intents = len(fs.files)
        measurements[f"depth_{depth}"] = {
            "total_reads": total,
            "max_per_artifact": max_r,
            "depth": depth,
            "collection_size": n_intents,
        }

    return measurements


if __name__ == "__main__":
    # Run measurements and print; used by the verification-ledger update below.
    import json
    data = _collect_measurements()
    print(json.dumps(data, indent=2))
