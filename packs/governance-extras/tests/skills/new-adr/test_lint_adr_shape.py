"""Pack-local tests for the confinement helper (T1) and the ADR shape lint (T2, T3).

This suite is gated by name in the gate chain (T8 adds the build-check.yml
step).  It may not read above its own pack — lint-pack-test-boundary.py
check 8 enforces that boundary.

T1 cases cover:
- helper loading (all required entry points present)
- every load-failure mode produces a detectable refusal rather than a silent
  fallback (a path that does not resolve, an exec_module that raises, a None
  spec or loader, and a module missing an entry point)
- list_candidate_entries refuses a symlinked supplied directory and accepts an
  ordinary directory nested under a symlinked ancestor
- classify_entry identifies symlinks, FIFOs, directories, and regular files
- read_confined reads a regular single-link file; refuses a hard link
- the hard-link case is the load-bearing proof that read_confined is stricter
  than the lstat-then-read_text idiom the scripts previously carried

T2 cases cover lint-adr-shape.py against synthetic fixtures:
- clean conforming directory: zero findings, exit 0 (AC-0001 floor)
- parametrised over all fifteen codes: each mutation declares its expected
  code set; the ID list is asserted equal to the fifteen codes (AC-0001)
- exit 1 on any finding (AC-0002)
- absent/empty directory exits 1 with a refusal message, no findings (AC-0003)
- ADR-S010 mutation: findings attributed to both record paths (AC-0004)
- refused + unreadable entries exit non-zero without a finding (AC-0031)
- Signal as indented block and Revisit if as blank-line+list: no finding (AC-0008)

T3 cases cover lint-adr-shape.py against hostile fixture trees built in
tmp_path (symlinks and FIFOs cannot be committed to the repository):
- symlinked .md, FIFO, binary file, and a conforming anchor: each lands in
  exactly one bucket; "refused" and "unreadable" are distinct labels and the
  conforming record is still read and checked (AC-0006)
- hard link to a record outside the scan directory: refused and named in the
  output; retains a behavioural owner for the helper guarantee (AC-0006, AC-0031)
- path outside the scan root refused directly by read_confined: retains a
  behavioural owner for the helper's containment guarantee (AC-0006, AC-0031)
"""
from __future__ import annotations

import contextlib
import importlib.util
import io
import os
import pathlib
import re
import sys
import types

import pytest

sys.dont_write_bytecode = True

SCRIPTS = pathlib.Path(__file__).resolve().parents[3] / ".apm/skills/new-adr/scripts"
_HELPER_PATH = SCRIPTS / "_record_paths.py"
_LINT_PATH = SCRIPTS / "lint-adr-shape.py"

# Committed synthetic fixtures for the T2 conforming-floor test
_FIXTURES_DIR = pathlib.Path(__file__).resolve().parent / "fixtures" / "conforming"


def _load_helper() -> types.ModuleType:
    """Load _record_paths.py using the same pattern the sibling scripts use.

    Loaded by path via importlib.util.spec_from_file_location, never by bare
    name, matching the packs/AGENTS.md requirement and the precedent in
    check-spec-status.py:69-114.
    """
    spec = importlib.util.spec_from_file_location(
        "new_adr_record_paths_test", str(_HELPER_PATH)
    )
    assert spec is not None and spec.loader is not None, (
        f"no import spec for {_HELPER_PATH}"
    )
    mod = importlib.util.module_from_spec(spec)
    prev = sys.dont_write_bytecode
    try:
        sys.dont_write_bytecode = True
        spec.loader.exec_module(mod)  # type: ignore[union-attr]
    finally:
        sys.dont_write_bytecode = prev
    return mod  # type: ignore[return-value]


# ── Helper loading ─────────────────────────────────────────────────────────────


def test_helper_loads_and_exposes_entry_points() -> None:
    """The helper loads cleanly and exposes all three required entry points."""
    rp = _load_helper()
    assert hasattr(rp, "list_candidate_entries"), "missing list_candidate_entries"
    assert hasattr(rp, "classify_entry"), "missing classify_entry"
    assert hasattr(rp, "read_confined"), "missing read_confined"
    assert hasattr(rp, "EntryRefused"), "missing EntryRefused exception class"


def test_load_from_nonexistent_path_raises(tmp_path: pathlib.Path) -> None:
    """A path that does not resolve raises rather than returning a usable module.

    spec_from_file_location may return a spec for a missing file, but
    exec_module raises at load time.  The loading code in the scripts must
    propagate that exception rather than falling back to a direct scan.
    """
    missing = tmp_path / "nonexistent.py"
    spec = importlib.util.spec_from_file_location("missing_helper", str(missing))
    if spec is None or spec.loader is None:
        # None spec is already a refusal — the caller can detect and refuse.
        return
    mod = importlib.util.module_from_spec(spec)
    with pytest.raises((FileNotFoundError, OSError, ImportError)):
        spec.loader.exec_module(mod)  # type: ignore[union-attr]


def test_load_when_exec_module_raises_propagates(tmp_path: pathlib.Path) -> None:
    """A module body that raises during exec_module propagates the exception.

    The loading code in the scripts wraps this in _HelperUnavailable and
    returns 1 rather than proceeding with a partial or absent helper.
    """
    bad = tmp_path / "bad.py"
    bad.write_text("raise RuntimeError('deliberate failure')\n", encoding="utf-8")
    spec = importlib.util.spec_from_file_location("bad_helper", str(bad))
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    with pytest.raises(RuntimeError, match="deliberate failure"):
        spec.loader.exec_module(mod)  # type: ignore[union-attr]


def test_none_spec_for_non_python_extension(tmp_path: pathlib.Path) -> None:
    """spec_from_file_location returns None for a file with no Python loader.

    The loading code must check for None before calling exec_module and refuse
    rather than raising AttributeError or proceeding with a missing loader.
    """
    not_python = tmp_path / "helper.txt"
    not_python.write_text("not python\n", encoding="utf-8")
    spec = importlib.util.spec_from_file_location("helper_txt", str(not_python))
    # No loader handles .txt files; the spec is None.
    assert spec is None


def test_module_missing_entry_points_is_detectable(tmp_path: pathlib.Path) -> None:
    """A module that loads but lacks entry points is distinguishable from one that has them.

    The loading code checks hasattr for each required entry point after
    exec_module succeeds, and refuses rather than letting callers hit
    AttributeError at the use site.
    """
    incomplete = tmp_path / "incomplete.py"
    incomplete.write_text("# no entry points here\n", encoding="utf-8")
    spec = importlib.util.spec_from_file_location("incomplete_helper", str(incomplete))
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    assert not hasattr(mod, "list_candidate_entries")
    assert not hasattr(mod, "classify_entry")
    assert not hasattr(mod, "read_confined")


# ── list_candidate_entries ─────────────────────────────────────────────────────


def test_list_candidate_entries_refuses_symlinked_directory(
    tmp_path: pathlib.Path,
) -> None:
    """list_candidate_entries refuses a directory that is itself a symlink."""
    real = tmp_path / "real"
    real.mkdir()
    link = tmp_path / "link"
    try:
        link.symlink_to(real)
    except OSError:
        pytest.skip("symlinks unavailable on this filesystem")
    rp = _load_helper()
    with pytest.raises(rp.EntryRefused, match="symlink"):
        rp.list_candidate_entries(link)


def test_list_candidate_entries_accepts_ordinary_dir_under_symlinked_ancestor(
    tmp_path: pathlib.Path,
) -> None:
    """An ordinary directory under a symlinked ancestor is accepted.

    macOS resolves /var through a symlink to /private/var.  The only check is
    on the supplied directory itself; an ancestor symlink is ordinary and must
    not cause a refusal.
    """
    real = tmp_path / "real"
    real.mkdir()
    inner = real / "records"
    inner.mkdir()
    link = tmp_path / "link"
    try:
        link.symlink_to(real)
    except OSError:
        pytest.skip("symlinks unavailable on this filesystem")
    rp = _load_helper()
    # link/records is a real directory; its ancestor link is a symlink.
    # list_candidate_entries checks only the supplied path, not ancestors.
    entries = rp.list_candidate_entries(link / "records")
    assert isinstance(entries, list)


# ── classify_entry ─────────────────────────────────────────────────────────────


def test_classify_entry_returns_symlink_for_symlink(tmp_path: pathlib.Path) -> None:
    """A symlink entry is classified as "symlink", not as its target's type."""
    target = tmp_path / "target.md"
    target.write_text("content\n", encoding="utf-8")
    link = tmp_path / "link.md"
    try:
        link.symlink_to(target)
    except OSError:
        pytest.skip("symlinks unavailable on this filesystem")
    rp = _load_helper()
    entries = rp.list_candidate_entries(tmp_path)
    link_entry = next(e for e in entries if e.name == "link.md")
    assert rp.classify_entry(link_entry) == "symlink"


def test_classify_entry_returns_directory_for_directory(
    tmp_path: pathlib.Path,
) -> None:
    """A directory entry is classified as "directory"."""
    subdir = tmp_path / "subdir"
    subdir.mkdir()
    rp = _load_helper()
    entries = rp.list_candidate_entries(tmp_path)
    dir_entry = next(e for e in entries if e.name == "subdir")
    assert rp.classify_entry(dir_entry) == "directory"


def test_classify_entry_returns_other_for_fifo(tmp_path: pathlib.Path) -> None:
    """A FIFO entry is classified as "other" (not regular and not a symlink)."""
    if not hasattr(os, "mkfifo"):
        pytest.skip("FIFOs not supported on this platform")
    fifo = tmp_path / "pipe.md"
    os.mkfifo(fifo)
    rp = _load_helper()
    entries = rp.list_candidate_entries(tmp_path)
    fifo_entry = next(e for e in entries if e.name == "pipe.md")
    assert rp.classify_entry(fifo_entry) == "other"


def test_classify_entry_returns_regular_for_regular_file(
    tmp_path: pathlib.Path,
) -> None:
    """A regular file entry is classified as "regular"."""
    f = tmp_path / "file.md"
    f.write_text("content\n", encoding="utf-8")
    rp = _load_helper()
    entries = rp.list_candidate_entries(tmp_path)
    file_entry = next(e for e in entries if e.name == "file.md")
    assert rp.classify_entry(file_entry) == "regular"


# ── read_confined ──────────────────────────────────────────────────────────────


def test_read_confined_reads_a_regular_file(tmp_path: pathlib.Path) -> None:
    """read_confined returns the bytes of a regular, single-link file."""
    f = tmp_path / "record.md"
    f.write_bytes(b"hello, world\n")
    rp = _load_helper()
    assert rp.read_confined(tmp_path, f) == b"hello, world\n"


def test_read_confined_refuses_hard_link(tmp_path: pathlib.Path) -> None:
    """read_confined refuses a hard link; lstat-then-read_bytes does not.

    This case is load-bearing: it proves the descriptor-based implementation
    is strictly stronger than the lstat-then-read_text idiom the scripts
    previously used, and that extracting the idiom into a helper introduced
    real confinement value.  Without this case every other helper case is also
    passed by the weaker idiom already shipped, and the extraction proves
    nothing.

    A hard link has st_nlink > 1.  The naive idiom reads it successfully.
    read_confined checks st_nlink before and after open and raises EntryRefused.
    """
    original = tmp_path / "original.md"
    original.write_bytes(b"some content")
    hard_link = tmp_path / "hard-link.md"
    try:
        os.link(original, hard_link)
    except OSError:
        pytest.skip("hard links not supported on this filesystem")

    # The naive implementation succeeds — reading a hard link with read_bytes
    # works, and this assertion makes the test self-proving: if hard links were
    # unavailable the skip above would have fired.
    assert hard_link.read_bytes() == b"some content"

    # The descriptor-based implementation refuses the hard link.
    rp = _load_helper()
    with pytest.raises(rp.EntryRefused, match="hard link"):
        rp.read_confined(tmp_path, hard_link)


# ═══════════════════════════════════════════════════════════════════════════════
# T2: lint-adr-shape.py against synthetic fixtures
# ═══════════════════════════════════════════════════════════════════════════════


def _load_lint() -> types.ModuleType:
    """Load lint-adr-shape.py by path (cached per process).

    Mirrors the loader in test_index_records.py: by-path via
    importlib.util.spec_from_file_location, never by bare name.
    """
    name = "lint_adr_shape_t2"
    if name in sys.modules:
        return sys.modules[name]  # type: ignore[return-value]
    spec = importlib.util.spec_from_file_location(name, str(_LINT_PATH))
    assert spec is not None and spec.loader is not None, (
        f"no import spec for {_LINT_PATH}"
    )
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    prev = sys.dont_write_bytecode
    try:
        sys.dont_write_bytecode = True
        spec.loader.exec_module(mod)  # type: ignore[union-attr]
    finally:
        sys.dont_write_bytecode = prev
    return mod  # type: ignore[return-value]


def _run(directory: pathlib.Path) -> tuple[int, str, str]:
    """Run lint main([str(directory)]) and return (exit_code, stdout, stderr).

    Uses redirect_stdout / redirect_stderr so the lint's reconfigure() guard
    (which skips streams lacking .reconfigure) leaves the StringIO untouched.
    """
    lint = _load_lint()
    out = io.StringIO()
    err = io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = lint.main([str(directory)])
    return code, out.getvalue(), err.getvalue()


def _extract_codes(output: str) -> set[str]:
    """Return the set of ADR-Snnn codes present in a finding stream."""
    return set(re.findall(r"\bADR-S\d{3}\b", output))


def _write_dir(tmp_path: pathlib.Path, files: dict[str, str]) -> pathlib.Path:
    """Write {name: content} to a fresh subdirectory and return its path."""
    d = tmp_path / "adr"
    d.mkdir()
    for name, content in files.items():
        (d / name).write_text(content, encoding="utf-8")
    return d


def _conforming() -> dict[str, str]:
    """Return {filename: content} for the three conforming fixture records."""
    return {
        name: (_FIXTURES_DIR / name).read_text(encoding="utf-8")
        for name in ("0001-basic.md", "0002-superseder.md", "0003-superseded.md")
    }


# ── T2: conforming floor ───────────────────────────────────────────────────────


def test_conforming_directory_has_zero_findings(tmp_path: pathlib.Path) -> None:
    """A directory with three conforming records reports no findings and exits 0.

    This is the floor every mutation case is measured against.
    """
    d = _write_dir(tmp_path, _conforming())
    code, out, _err = _run(d)
    codes = _extract_codes(out)
    assert codes == set(), f"unexpected findings in conforming dir: {out!r}"
    assert code == 0, f"expected exit 0 for conforming dir, got {code}\n{out}"


# ── T2: mutation parametrisation ─────────────────────────────────────────────


def _mutate(base: dict[str, str], name: str, old: str, new: str) -> dict[str, str]:
    """Return a copy of base with one substring replacement in file `name`."""
    d = dict(base)
    assert old in d[name], f"pattern not found in {name!r}: {old!r}"
    d[name] = d[name].replace(old, new, 1)
    return d


# Each entry: (files_dict, expected_code_set)
# The `id` in pytest.param is the single check class code this case names.
# ADR-S008 declares {ADR-S008, ADR-S010} because its mutation adds an
# unmirrored entry (RFC-0102 § 3 field-specific mirroring).
_MUTATION_CASES: list[pytest.param] = [  # type: ignore[type-arg]
    pytest.param(
        lambda b: _mutate(b, "0001-basic.md",
                          "- **Status:** Accepted",
                          "- **Status:** InProgress"),
        {"ADR-S001"},
        id="ADR-S001",
    ),
    pytest.param(
        lambda b: _mutate(b, "0001-basic.md",
                          "- **Date:** 2026-01-15",
                          "- **Date:** not-a-date"),
        {"ADR-S002"},
        id="ADR-S002",
    ),
    pytest.param(
        lambda b: _mutate(b, "0001-basic.md",
                          "- **Areas:** tooling, infrastructure",
                          "- **Areas:**"),
        {"ADR-S003"},
        id="ADR-S003",
    ),
    pytest.param(
        lambda b: _mutate(b, "0001-basic.md",
                          "- **Areas:** tooling, infrastructure",
                          "- **Areas:** a, b, c, d"),
        {"ADR-S004"},
        id="ADR-S004",
    ),
    pytest.param(
        lambda b: _mutate(b, "0001-basic.md",
                          "- **Areas:** tooling, infrastructure",
                          "- **Areas:** TOOLING, infrastructure"),
        {"ADR-S005"},
        id="ADR-S005",
    ),
    pytest.param(
        lambda b: _mutate(b, "0001-basic.md",
                          "- **Reversibility:** low",
                          "- **Reversibility:** medium"),
        {"ADR-S006"},
        id="ADR-S006",
    ),
    pytest.param(
        lambda b: _mutate(b, "0001-basic.md",
                          "- **Superseded by:** none\n",
                          ""),
        {"ADR-S007"},
        id="ADR-S007",
    ),
    # ADR-S008 mutation adds ADR-0003 to Supersedes in part on ADR-0002, so
    # ADR-0003 appears in both Supersedes and Supersedes in part — S008 fires.
    # The added entry has no mirror on ADR-0003 — S010 also fires (RFC-0102 § 3).
    pytest.param(
        lambda b: _mutate(b, "0002-superseder.md",
                          "- **Supersedes in part:** none",
                          "- **Supersedes in part:** ADR-0003 D1"),
        {"ADR-S008", "ADR-S010"},
        id="ADR-S008",
    ),
    # ADR-S009: add partial supersession between ADR-0001 and ADR-0003 citing
    # D99, which does not exist in either record (both define only D1/D2).
    # Mirrors are present so ADR-S010 does not fire.
    pytest.param(
        lambda b: {
            **_mutate(b, "0001-basic.md",
                      "- **Supersedes in part:** none",
                      "- **Supersedes in part:** ADR-0003 D99"),
            "0003-superseded.md": _mutate(b, "0003-superseded.md",
                                          "- **Superseded in part:** none",
                                          "- **Superseded in part:** ADR-0001 D99")[
                "0003-superseded.md"
            ],
        },
        {"ADR-S009"},
        id="ADR-S009",
    ),
    # ADR-S010: remove the Superseded by mirror on ADR-0003 so ADR-0002's
    # Supersedes: ADR-0003 has no counterpart.  Finding attributed to both paths.
    pytest.param(
        lambda b: _mutate(b, "0003-superseded.md",
                          "- **Superseded by:** ADR-0002",
                          "- **Superseded by:** none"),
        {"ADR-S010"},
        id="ADR-S010",
    ),
    pytest.param(
        lambda b: _mutate(b, "0001-basic.md",
                          "- **D2:** All services read configuration at startup from the shared store.",
                          "- **D3:** All services read configuration at startup from the shared store."),
        {"ADR-S011"},
        id="ADR-S011",
    ),
    pytest.param(
        lambda b: _mutate(b, "0001-basic.md",
                          "**Revisit if:** The store becomes unavailable or introduces unacceptable latency.",
                          "**Revisit if:**"),
        {"ADR-S012"},
        id="ADR-S012",
    ),
    pytest.param(
        lambda b: _mutate(b, "0001-basic.md",
                          "- **Mode:** reviewer-checked\n",
                          ""),
        {"ADR-S013"},
        id="ADR-S013",
    ),
    pytest.param(
        lambda b: _mutate(b, "0001-basic.md",
                          "- **Per-service config files:** Rejected because it causes drift between services.\n"
                          "- **Environment variables only:** Rejected because secrets management becomes complex.",
                          ""),
        {"ADR-S014"},
        id="ADR-S014",
    ),
    pytest.param(
        lambda b: _mutate(b, "0001-basic.md",
                          "## Errata",
                          "## Amendments"),
        {"ADR-S015"},
        id="ADR-S015",
    ),
]

_ALL_CODES = [f"ADR-S{n:03d}" for n in range(1, 16)]


def test_parametrization_ids_equal_fifteen_codes() -> None:
    """The parametrised case IDs are exactly the fifteen check class codes.

    A class added without a case makes this test red.
    """
    ids = [c.id for c in _MUTATION_CASES]
    assert ids == _ALL_CODES


@pytest.mark.parametrize("mutate_fn,expected_codes", _MUTATION_CASES)
def test_mutation_reports_expected_codes(
    tmp_path: pathlib.Path,
    mutate_fn: object,
    expected_codes: set[str],
) -> None:
    """Each mutation causes exactly the declared code set to be reported.

    Verifies AC-0001 for all fifteen check classes.  The expected_codes set
    is declared by the fixture, not read back from the output.
    """
    import typing
    base = _conforming()
    files = typing.cast(
        "dict[str, str]",
        mutate_fn(base),  # type: ignore[operator]
    )
    d = _write_dir(tmp_path, files)
    code, out, _err = _run(d)
    actual = _extract_codes(out)
    assert actual == expected_codes, (
        f"expected {expected_codes!r}, got {actual!r}\nstdout:\n{out}"
    )
    assert code == 1, f"expected exit 1 when findings reported, got {code}"


# ── T2: exit contract (AC-0002) ────────────────────────────────────────────────


def test_exit_0_on_no_findings_and_all_read(tmp_path: pathlib.Path) -> None:
    """Exits 0 only when there are no findings and every candidate was read.

    Verifies AC-0002 (finding half): conforming dir exits 0.
    The mutation parametrisation covers the exit-1-on-finding half.
    """
    d = _write_dir(tmp_path, _conforming())
    code, out, _err = _run(d)
    assert code == 0
    assert _extract_codes(out) == set()


# ── T2: absent and empty directory (AC-0003) ───────────────────────────────────


def test_absent_directory_exits_1_with_message_and_no_findings(
    tmp_path: pathlib.Path,
) -> None:
    """An absent target directory exits 1, prints a message, and has no finding codes.

    Verifies AC-0003 (absent-directory path).
    """
    missing = tmp_path / "does_not_exist"
    code, out, _err = _run(missing)
    assert code == 1, f"expected exit 1 for absent dir, got {code}"
    assert _extract_codes(out) == set(), f"unexpected ADR codes in output: {out!r}"
    assert out.strip(), "expected a message naming the absent-directory case"


def test_empty_candidate_listing_exits_1_with_message_and_no_findings(
    tmp_path: pathlib.Path,
) -> None:
    """A directory with no *.md candidates exits 1, names the case, has no findings.

    Verifies AC-0003 (empty-listing path).  A directory with only non-.md files
    or no files produces an empty candidate listing.
    """
    d = tmp_path / "empty_adr"
    d.mkdir()
    # Write a non-candidate file so the directory exists but has no .md records
    (d / "README.md").write_text("# index\n", encoding="utf-8")
    code, out, _err = _run(d)
    assert code == 1, f"expected exit 1 for empty listing, got {code}"
    assert _extract_codes(out) == set(), f"unexpected ADR codes in output: {out!r}"
    assert out.strip(), "expected a message naming the empty-listing case"


# ── T2: mirrored-pair attribution (AC-0004) ───────────────────────────────────


def test_s010_findings_attributed_to_both_record_paths(
    tmp_path: pathlib.Path,
) -> None:
    """ADR-S010 findings name both the record that has the entry and the one missing the mirror.

    Verifies AC-0004: a missing counterpart in a mirrored pair is reported
    against both records, not just the one that triggered the check.
    """
    base = _conforming()
    # Remove the Superseded by mirror from ADR-0003
    files = _mutate(base, "0003-superseded.md",
                    "- **Superseded by:** ADR-0002",
                    "- **Superseded by:** none")
    d = _write_dir(tmp_path, files)
    code, out, _err = _run(d)

    # Both records must appear in the ADR-S010 finding lines
    s010_lines = [line for line in out.splitlines() if "ADR-S010" in line]
    assert len(s010_lines) >= 2, (
        f"expected findings on both records; got:\n{out}"
    )
    paths_in_findings = {line.split(":")[0] for line in s010_lines}
    names_in_findings = {pathlib.Path(p).name for p in paths_in_findings}
    assert "0002-superseder.md" in names_in_findings, (
        f"ADR-0002 (the record with Supersedes: ADR-0003) missing from findings:\n{out}"
    )
    assert "0003-superseded.md" in names_in_findings, (
        f"ADR-0003 (the record missing its mirror) missing from findings:\n{out}"
    )
    assert code == 1


# ── T2: refused and unreadable entries fail the run (AC-0031) ─────────────────


def test_refused_and_unreadable_entries_exit_nonzero(
    tmp_path: pathlib.Path,
) -> None:
    """A directory with one refused and one undecodable entry exits non-zero.

    Verifies AC-0031: unchecked entries fail the gate even without findings.
    The entry in the refused bucket is a directory named like a record.
    The entry in the unreadable bucket is a binary file that is not UTF-8.
    """
    d = tmp_path / "adr"
    d.mkdir()
    # Refused: a directory named like a record (classify returns "directory")
    dir_record = d / "0001-refused.md"
    dir_record.mkdir()
    # Unreadable: a binary file with non-UTF-8 bytes
    (d / "0002-binary.md").write_bytes(b"\xff\xfe not utf-8 \x00\x01")

    code, out, err = _run(d)
    assert code != 0, (
        f"expected non-zero exit with refused+unreadable entries, got {code}"
    )
    # There should be no ADR-S finding lines (these are bucket entries, not parsed)
    assert _extract_codes(out) == set(), (
        f"unexpected finding codes; refused/unreadable should not produce ADR codes:\n{out}"
    )


# ── T2: continuation-block field values (AC-0008) ─────────────────────────────


_SIGNAL_INDENTED_BLOCK = """\
# ADR-0010: Use indented signal block

- **Status:** Accepted
- **Date:** 2026-04-01
- **Areas:** tooling
- **Reversibility:** low
- **Decision-makers:** alice
- **Supersedes:** none
- **Supersedes in part:** none
- **Superseded by:** none
- **Superseded in part:** none

## Context

Modelled on ADR-0070 in the real corpus, whose Signal is an indented block.

## Decision

We test the indented-block Signal form.

- **D1:** Signal values may span multiple indented lines.

## Consequences

Positive: the parser handles both corpus forms.

**Revisit if:** The corpus shifts to a different Signal shape.

## Confirmation

- **Mode:** reviewer-checked
- **Signal:**
  - The integration test suite passes.
  - No regression in existing checks.
- **Owner:** alice

## Alternatives considered

- **Same-line Signal:** Accepted for the simple case; both are supported.
"""

_REVISIT_BLANK_LINE_LIST = """\
# ADR-0011: Use blank-line Revisit if list

- **Status:** Accepted
- **Date:** 2026-04-02
- **Areas:** tooling
- **Reversibility:** low
- **Decision-makers:** alice
- **Supersedes:** none
- **Supersedes in part:** none
- **Superseded by:** none
- **Superseded in part:** none

## Context

Modelled on ADR-0070's Revisit if form: blank line then unindented list.

## Decision

We test the blank-line-then-list Revisit if form.

- **D1:** Revisit if values may be a blank-line-separated unindented list.

## Consequences

Positive: the parser handles both corpus Revisit if forms.

**Revisit if:**

- The store becomes unavailable.
- Performance degrades beyond acceptable thresholds.

## Confirmation

- **Mode:** reviewer-checked
- **Signal:** All tests green.
- **Owner:** alice

## Alternatives considered

- **Same-line Revisit if:** Accepted for the simple case; both are supported.
"""


def test_signal_indented_block_reports_no_s013(tmp_path: pathlib.Path) -> None:
    """A Signal value written as an indented block is read as non-empty.

    Modelled on ADR-0070 in the real corpus.  A line-scoped reader would see
    the Signal field as empty and report ADR-S013; AC-0008 requires it to pass.
    """
    d = _write_dir(tmp_path, {"0010-signal-block.md": _SIGNAL_INDENTED_BLOCK})
    code, out, _err = _run(d)
    assert "ADR-S013" not in out, (
        f"ADR-S013 reported for indented-block Signal; parser did not read the block:\n{out}"
    )
    assert code == 0, f"expected exit 0 for conforming indented-block fixture:\n{out}"


def test_revisit_if_blank_line_list_reports_no_s012(tmp_path: pathlib.Path) -> None:
    """A Revisit if value written as a blank-line+list is read as non-empty.

    Modelled on ADR-0070 in the real corpus.  A line-scoped reader would see
    the Revisit if field as empty and report ADR-S012; AC-0008 requires it to pass.
    """
    d = _write_dir(tmp_path, {"0011-revisit-list.md": _REVISIT_BLANK_LINE_LIST})
    code, out, _err = _run(d)
    assert "ADR-S012" not in out, (
        f"ADR-S012 reported for blank-line+list Revisit if; parser did not read the list:\n{out}"
    )
    assert code == 0, f"expected exit 0 for conforming blank-line+list fixture:\n{out}"


# ── Regression guards for two defects the fixture suite could not see ────────


def test_a_relative_directory_argument_still_reads_every_record(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The gate chain passes `docs/adr`, not an absolute path.

    `os.scandir` echoes back whatever the caller supplied, so a relative
    argument yields relative entry paths while the confinement root is
    resolved; `read_confined`'s `relative_to(root)` then refuses every entry
    and the scan reads nothing. Every other case in this file passes an
    absolute `tmp_path`, so none of them can tell a working scan from that one.
    """
    d = _write_dir(tmp_path, _conforming())
    monkeypatch.chdir(tmp_path)
    code, out, err = _run(pathlib.Path(d.name))
    assert "refused: 0" in err or "refused: 0" in out, (
        f"relative argument refused entries:\n{err or out}"
    )
    assert "read: 3" in (err + out), f"expected 3 records read:\n{err or out}"
    assert code == 0, f"expected exit 0 on a conforming dir, got {code}"


def test_s009_resolves_the_d_id_owner_by_field_direction(
    tmp_path: pathlib.Path,
) -> None:
    """RFC-0102 :229 — in both halves the D-IDs belong to the superseded record.

    For `Supersedes in part` that is the named record; for `Superseded in part`
    it is the citing record. Resolving both to the named record reports a false
    positive on every correct `Superseded in part` entry — three exist in the
    real corpus, each citing a D-ID its own record defines. Only the second
    case below distinguishes the two readings.
    """
    records = _conforming()
    # 0001 defines D1 and D2; 0002 defines D1 only. Citing D2 therefore
    # distinguishes the two readings: it exists in the citing record and does
    # not exist in the named one, so the wrong resolution fires and the right
    # one stays silent.
    citing = records["0001-basic.md"].replace(
        "- **Superseded in part:** none",
        "- **Superseded in part:** ADR-0002 D2",
    )
    assert "- **D2:**" in citing, "fixture must define the D-ID it cites"
    records["0001-basic.md"] = citing
    named = records["0002-superseder.md"].replace(
        "- **Supersedes in part:** none",
        "- **Supersedes in part:** ADR-0001 D2",
    )
    assert "- **D2:**" not in named, "named record must not define it"
    records["0002-superseder.md"] = named
    d = _write_dir(tmp_path, records)
    codes = _extract_codes(_run(d)[1])
    assert "ADR-S009" not in codes, (
        "a `Superseded in part` entry citing the citing record's own D-ID is "
        f"conformant, but S009 fired: {codes}"
    )


# ═══════════════════════════════════════════════════════════════════════════════
# T3: hostile fixture trees — correct label attribution (AC-0006, AC-0031)
# ═══════════════════════════════════════════════════════════════════════════════

#: Minimal standalone conforming ADR for use as an anchor in T3 hostile-directory
#: tests.  All supersession fields are "none" so no other record is required.
#: Must pass all fifteen check classes on its own.
_T3_ANCHOR = """\
# ADR-0050: conforming anchor for hostile-directory tests

- **Status:** Accepted
- **Date:** 2026-09-01
- **Areas:** testing
- **Reversibility:** low
- **Supersedes:** none
- **Supersedes in part:** none
- **Superseded by:** none
- **Superseded in part:** none

## Context

Anchor record for T3 hostile-fixture tests.  Proves the lint continues
scanning past refused and unreadable entries and still checks conforming
records.

## Decision

We include a standalone conforming record alongside hostile entries.

- **D1:** The lint must continue past refused and unreadable entries and
  check all conforming records it can read.

## Consequences

The scan continues and conforming records are checked.

**Revisit if:** The lint changes its scan order or early-exit behaviour.

## Confirmation

- **Mode:** reviewer-checked
- **Signal:** read count is positive in the scan summary.
- **Owner:** test-author

## Alternatives considered

- **Abort on first bad entry:** Rejected; the lint must be exhaustive.
"""


def _parse_summary_counts(combined: str) -> dict[str, int]:
    """Return {'read': N, 'refused': N, 'unreadable': N} from a scan summary.

    The lint emits one summary line:  read: N  refused: N  unreadable: N
    Parses every (label, count) pair found anywhere in the combined output.
    """
    result: dict[str, int] = {}
    for m in re.finditer(r"(read|refused|unreadable):\s*(\d+)", combined):
        result[m.group(1)] = int(m.group(2))
    return result


def test_hostile_directory_labels_refused_and_unreadable_distinctly(
    tmp_path: pathlib.Path,
) -> None:
    """A symlinked .md, a FIFO, a binary file, and a conforming anchor each land
    in exactly one bucket; "refused" and "unreadable" are distinct labels and
    the conforming anchor is still read and checked.

    Also attempts to create a file with a non-UTF-8 filename; when that
    succeeds (Linux only) asserts the scan completes without aborting and
    accounts for the entry in a bucket.  macOS/APFS enforces UTF-8 filenames
    so that sub-case is skipped silently on that platform.

    Verifies AC-0006.
    """
    scan_dir = tmp_path / "adr"
    scan_dir.mkdir()

    # Conforming anchor — proves the scan continues past hostile entries.
    (scan_dir / "0050-conforming.md").write_text(_T3_ANCHOR, encoding="utf-8")

    # Entry 1: symlinked .md → refused (classify_entry returns "symlink").
    sym_target = tmp_path / "target.md"
    sym_target.write_text("target content\n", encoding="utf-8")
    sym_path = scan_dir / "0060-symlink.md"
    try:
        sym_path.symlink_to(sym_target)
    except OSError:
        pytest.skip("symlinks unavailable on this filesystem")

    # Entry 2: FIFO named like a record → refused (classify_entry returns "other").
    fifo_path = scan_dir / "0061-fifo.md"
    has_fifo = False
    if hasattr(os, "mkfifo"):
        try:
            os.mkfifo(fifo_path)
            has_fifo = True
        except OSError:
            pass  # some tmpfs variants refuse FIFOs; not a platform skip

    # Entry 3: file with non-UTF-8 bytes → unreadable (UTF-8 decode raises).
    (scan_dir / "0062-binary.md").write_bytes(b"\xff\xfe\x00\x01 non-utf-8")

    # Entry 4 (optional): file with a non-UTF-8 filename.
    # macOS/APFS enforces UTF-8 filenames; creation fails there.  On Linux
    # this entry will be read, refused, or unreadable depending on its content
    # (non-UTF-8 bytes → unreadable).  The key assertion is that the scan
    # completes without aborting and the entry is accounted for in a bucket.
    has_bad_name = False
    try:
        bad_name_b = os.fsencode(str(scan_dir)) + b"/0063-bad\xff.md"
        fd = os.open(bad_name_b, os.O_CREAT | os.O_WRONLY, 0o644)
        os.write(fd, b"\xff\xfe non-utf-8 content")  # non-UTF-8 → unreadable
        os.close(fd)
        has_bad_name = True
    except (OSError, ValueError, TypeError):
        pass  # filesystem rejected the non-UTF-8 name (macOS/APFS) — skip sub-case

    code, out, err = _run(scan_dir)
    combined = out + err
    summary = _parse_summary_counts(combined)

    # Conforming anchor is in the read bucket (proves scan continued).
    assert summary.get("read", 0) >= 1, (
        f"expected ≥1 read entry; summary: {combined!r}"
    )

    # Symlink lands in refused, not unreadable.
    assert summary.get("refused", 0) >= 1, (
        f"expected ≥1 refused entry (symlink); summary: {combined!r}"
    )

    # Binary file lands in unreadable, not refused.
    assert summary.get("unreadable", 0) >= 1, (
        f"expected ≥1 unreadable entry (binary); summary: {combined!r}"
    )

    # FIFO, when created, also lands in refused.
    if has_fifo:
        assert summary.get("refused", 0) >= 2, (
            f"FIFO expected in refused; refused={summary.get('refused', 0)}: "
            f"{combined!r}"
        )

    # AC-0006: "refused" and "unreadable" are distinct labels in the output.
    assert "refused:" in combined, f"'refused:' label absent: {combined!r}"
    assert "unreadable:" in combined, f"'unreadable:' label absent: {combined!r}"

    # Bad-name entry (Linux only): scan must have completed and the entry must
    # appear in some bucket (the total covers all candidates).
    if has_bad_name:
        total = sum(summary.values())
        # At minimum: conforming + symlink + binary + bad-name = 4.
        assert total >= 4, (
            f"bad-name entry unaccounted; total={total}: {combined!r}"
        )

    # Non-zero exit because of bad entries (AC-0031).
    assert code != 0, f"expected non-zero exit for hostile directory; got {code}"


def test_hard_link_to_outside_file_is_refused_and_named(
    tmp_path: pathlib.Path,
) -> None:
    """A hard link to a record outside the scan directory is refused and named.

    classify_entry returns "regular" for the hard link (it is a regular file);
    read_confined then refuses it because st_nlink > 1.  The entry appears in
    the refused bucket of the scan summary and its name appears in the output.

    Retains a behavioural owner for the hard-link helper guarantee that lost
    its structural gate owner when the delegation criterion was cut.
    Contributes to AC-0006 and AC-0031.
    """
    scan_dir = tmp_path / "adr"
    scan_dir.mkdir()

    # Conforming anchor — proves the scan continues past the refused entry.
    (scan_dir / "0050-conforming.md").write_text(_T3_ANCHOR, encoding="utf-8")

    # The original file lives outside the scan directory.
    original = tmp_path / "original.md"
    original.write_bytes(b"original content\n")

    # Hard link inside the scan directory: same inode, st_nlink > 1.
    # classify_entry returns "regular" (it IS a regular file), but
    # read_confined refuses it because st_nlink > 1.
    hard_link = scan_dir / "0099-hardlink.md"
    try:
        os.link(original, hard_link)
    except OSError:
        pytest.skip("hard links not supported on this filesystem")

    code, out, err = _run(scan_dir)
    combined = out + err
    summary = _parse_summary_counts(combined)

    # The hard link must land in the refused bucket (not unreadable).
    assert summary.get("refused", 0) >= 1, (
        f"hard link expected in refused bucket; summary: {combined!r}"
    )

    # The entry's name must appear in the output (it is "named").
    assert "0099-hardlink.md" in combined, (
        f"hard-link entry name absent from output: {combined!r}"
    )

    # Non-zero exit (AC-0031: refused entries fail the gate).
    assert code != 0, f"expected non-zero exit; got {code}"


def test_path_outside_scan_root_is_refused_by_helper(
    tmp_path: pathlib.Path,
) -> None:
    """read_confined refuses a path that lies outside its declared root.

    This check fires before any file I/O and cannot be triggered via the
    lint's normal scan flow (which always constructs root / entry.name).
    A direct unit test here gives it a behavioural owner so the guarantee
    is not unobserved.

    Contributes to AC-0006 and AC-0031.
    """
    rp = _load_helper()

    root = tmp_path / "scan-root"
    root.mkdir()

    # A regular file outside the declared root.
    outside = tmp_path / "outside.md"
    outside.write_bytes(b"outside content\n")

    # read_confined must refuse because outside is not relative_to(root).
    with pytest.raises(rp.EntryRefused, match="outside"):
        rp.read_confined(root, outside)


def test_streams_are_reconfigured_with_a_handler_that_survives_a_surrogate() -> None:
    """Naming an entry must never be the thing that aborts the scan.

    The hostile-directory case above cannot observe this. It builds a real
    file with a non-UTF-8 name, which macOS/APFS refuses outright, and it runs
    the lint through `redirect_stdout` onto a StringIO — which has no
    `reconfigure` at all and accepts surrogates regardless. So that case passes
    on every platform whether or not the handler is set.

    This one reads the arguments the lint actually passes, then proves the
    chosen handler survives the input it exists for: a filename Python has
    surfaced with surrogate escapes.
    """
    lint = _load_lint()
    recorded: dict[str, object] = {}

    class _Recorder:
        def reconfigure(self, **kwargs: object) -> None:
            recorded.update(kwargs)

        def write(self, _text: str) -> int:
            return 0

        def flush(self) -> None:
            return None

    rec = _Recorder()
    with contextlib.redirect_stdout(rec), contextlib.redirect_stderr(rec):
        lint.main([])          # argv error path: reconfigures, then returns
    assert recorded.get("encoding") == "utf-8", recorded
    handler = recorded.get("errors")
    assert handler not in (None, "strict"), (
        "streams reconfigured with the strict default; a surrogate filename "
        f"will raise from the print that names it. got {handler!r}"
    )

    probe = io.TextIOWrapper(io.BytesIO(), encoding="ascii")
    probe.reconfigure(encoding="utf-8", errors=str(handler))
    probe.write("warning: 0117-x\udcff.md: refused\n")
    probe.flush()


# ═══════════════════════════════════════════════════════════════════════════════
# T5: template content and conformance (AC-0017, AC-0018, AC-0019, AC-0020,
#     AC-0022)
# ═══════════════════════════════════════════════════════════════════════════════

#: Path to the shipped template — read by all T5 tests rather than a copy, so
#: the template and the lint cannot drift apart silently.
_TEMPLATE_PATH = (
    pathlib.Path(__file__).resolve().parents[3]
    / ".apm/skills/new-adr/assets/adr.md"
)


def test_template_declares_all_metadata_fields() -> None:
    """The template pre-declares Areas, Reversibility, and all four supersession
    fields; each supersession field carries the 'none' sentinel.

    Verifies AC-0017.
    """
    text = _TEMPLATE_PATH.read_text(encoding="utf-8")

    assert "**Areas:**" in text, "template missing Areas field"
    assert "**Reversibility:**" in text, "template missing Reversibility field"

    # All four supersession fields must be present with 'none' as the sentinel.
    for field in (
        "Supersedes",
        "Supersedes in part",
        "Superseded by",
        "Superseded in part",
    ):
        marker = f"**{field}:** none"
        assert marker in text, (
            f"template missing '{field}' field with 'none' sentinel; "
            f"looked for {marker!r}"
        )


def test_template_states_four_parse_tiers() -> None:
    """The template states the four parse tiers and which fields belong to each.

    The tier names must be written in full ('tier T1', not bare 'T1') to
    avoid colliding with plan task identifiers.  Verifies AC-0018.
    """
    text = _TEMPLATE_PATH.read_text(encoding="utf-8")

    for tier in ("tier T1", "tier T1-unchecked", "tier T2", "tier T3"):
        assert tier in text, (
            f"template does not state {tier!r}; "
            "all four parse tiers must be named in full"
        )

    # Each tier names at least one field that belongs to it.
    # tier T1 owns the mechanically checked fields.
    for field in ("Status", "Date", "Areas", "Reversibility"):
        assert field in text, f"expected tier T1 field {field!r} mentioned in template"

    # tier T1-unchecked owns Related.
    assert "Related" in text, "expected 'Related' mentioned under tier T1-unchecked"

    # tier T2 owns Alternatives considered.
    assert "Alternatives considered" in text, (
        "expected 'Alternatives considered' mentioned under tier T2"
    )


def test_template_states_authoring_transformation() -> None:
    """The template states the authoring transformation an author performs.

    The transformation is: substitute every placeholder, then delete all
    guidance comments.  Verifies AC-0019.
    """
    text = _TEMPLATE_PATH.read_text(encoding="utf-8")

    assert "substitute every placeholder" in text, (
        "template does not state 'substitute every placeholder'"
    )
    assert "delete" in text and "comment" in text, (
        "template does not state that guidance comments should be deleted"
    )


def test_template_states_related_shape_marked_unchecked_with_placeholder_ordinals() -> None:
    """The template states the suggested Related: shape, marked as not validated,
    with a worked example whose ordinals are all in the literal placeholder form
    used elsewhere in the template (ADR-NNNN, RFC-NNNN).

    The check is expressed against the literal placeholder form rather than
    against whether any ordinal resolves — a pack test may not read above its
    own pack to decide that (lint-pack-test-boundary.py check 8).

    Verifies AC-0020.
    """
    text = _TEMPLATE_PATH.read_text(encoding="utf-8")

    # The guidance must be marked as not validated.
    assert "not validated" in text, (
        "Related: guidance must be marked as 'not validated' (tier T1-unchecked)"
    )

    # The worked example must contain only placeholder ordinals.
    # ADR-NNNN and RFC-NNNN are the placeholder forms used elsewhere.
    assert "RFC-NNNN" in text, (
        "Related: worked example must use RFC-NNNN as the placeholder ordinal form"
    )
    assert "ADR-NNNN" in text, (
        "Related: worked example must use ADR-NNNN as the placeholder ordinal form"
    )

    # No real (digit-only) ordinals may appear in the template at all —
    # packs/AGENTS.md forbids citing internal governance records.
    import re as _re
    real_ordinals = _re.findall(r"\b(?:ADR|RFC)-\d{4}\b", text)
    assert real_ordinals == [], (
        f"template contains real ordinals {real_ordinals!r}; "
        "only placeholder forms (ADR-NNNN, RFC-NNNN) are permitted"
    )


def test_template_instantiation_passes_the_lint(tmp_path: pathlib.Path) -> None:
    """Instantiating the template by the transformation it documents produces a
    record the lint accepts with exit 0 and no findings.

    Transformation: strip HTML comment blocks, then substitute all placeholders
    (angle-bracket text and the YYYY-MM-DD sentinel) with valid values, then
    replace the initial 'Proposed' Status with 'Accepted'.

    Verifies AC-0022.
    """
    import re as _re

    text = _TEMPLATE_PATH.read_text(encoding="utf-8")

    # Step 1: delete all HTML comment blocks (<!-- … -->).
    text = _re.sub(r"<!--.*?-->", "", text, flags=_re.DOTALL)

    # Step 2: replace the date placeholder.
    text = text.replace("YYYY-MM-DD", "2026-01-01")

    # Step 3: set Status to a valid accepted token.
    text = _re.sub(r"(- \*\*Status:\*\*) Proposed", r"\1 Accepted", text)

    # Step 4: substitute all remaining angle-bracket placeholders with a
    # minimal non-empty string.  Every lint-checked field that requires a
    # specific token (Areas, Reversibility) must be substituted to a token
    # in its allowed set before this step.
    text = text.replace("<area-token>", "tooling")
    text = text.replace("<high|low>", "low")
    text = _re.sub(r"<[^>]+>", "test", text)

    # Write the instantiated record to a temp scan directory and run the lint.
    adr_dir = tmp_path / "adr"
    adr_dir.mkdir()
    (adr_dir / "0001-test-record.md").write_text(text, encoding="utf-8")

    code, out, _err = _run(adr_dir)
    assert code == 0, (
        f"Instantiated template failed the lint (exit {code}):\n{out}"
    )
    assert _extract_codes(out) == set(), (
        f"Instantiated template produced lint findings:\n{out}"
    )


def test_template_supersession_examples_parse_under_the_lints_grammar(
    tmp_path: pathlib.Path,
) -> None:
    """Every worked value the template shows must be one the lint accepts.

    The separators are easy to transpose: `;` divides entries and `,` divides
    D-IDs within an entry, so a two-entry example written with a comma reads
    naturally and is rejected. An author following the template then writes a
    record the blocking gate refuses, with nothing pointing back at the
    template that misled them. This walks the template's own comments rather
    than a copy of them, so a future edit to either side is caught.
    """
    template = _TEMPLATE_PATH.read_text(encoding="utf-8")
    examples: list[tuple[str, str]] = []
    for field in ("Supersedes", "Supersedes in part",
                  "Superseded by", "Superseded in part"):
        m = re.search(
            rf"^- \*\*{re.escape(field)}:\*\*.*?<!--\s*none,\s*or:\s*(.+?)\s*-->$",
            template, re.M,
        )
        if m:
            examples.append((field, m.group(1)))
    assert examples, "no supersession examples found in the template"

    base = _conforming()["0001-basic.md"]
    for field, raw in examples:
        # Resolve the placeholder ordinals the way an author does. The example
        # is guidance about SHAPE — separators, D-ID placement — so `NNNN`
        # standing in for digits is the convention, not a defect.
        value = raw.replace("NNNN", "0002").replace("MMMM", "0003")
        parent = tmp_path / field.replace(" ", "_")
        parent.mkdir()
        d = _write_dir(
            parent,
            {"0001-basic.md": base.replace(
                f"- **{field}:** none", f"- **{field}:** {value}")},
        )
        codes = _extract_codes(_run(d)[1])
        assert "ADR-S007" not in codes, (
            f"the template's {field!r} example {raw!r} is malformed under "
            f"the lint's own grammar: {codes}"
        )


def _partial_pair(a_entry: str, b_entry: str) -> dict[str, str]:
    """Two records forming a partial-supersession pair, each side given verbatim.

    Both halves cite D-IDs defined by the *superseded* record, so a conforming
    pair names the same D-ID set on both sides.
    """
    def rec(num: str, title: str, sip: str, sup_ip: str) -> str:
        return (
            f"# ADR-{num}: {title}\n\n"
            "- **Status:** Accepted\n"
            "- **Date:** 2026-09-17\n"
            "- **Areas:** governance\n"
            "- **Reversibility:** high\n"
            "- **Decision-makers:** someone\n"
            "- **Supersedes:** none\n"
            f"- **Supersedes in part:** {sip}\n"
            "- **Superseded by:** none\n"
            f"- **Superseded in part:** {sup_ip}\n\n"
            "## Decision\n\n"
            "- **D1:** first\n"
            "- **D2:** second\n"
        )
    return {
        "0001-a.md": rec("0001", "A", a_entry, "none"),
        "0002-b.md": rec("0002", "B", "none", b_entry),
    }


def test_s010_rejects_a_partial_mirror_whose_d_ids_disagree(tmp_path):
    """A present counterpart naming different D-IDs is not a mirror.

    The ordinals match, so an ordinal-only comparison passes this pair. The
    D-ID sets do not, and both halves cite D-IDs owned by the superseded
    record, so the sets must be equal rather than merely both non-empty.
    """
    d = _write_dir(tmp_path, _partial_pair("ADR-0002 D1", "ADR-0001 D2"))
    code, out, err = _run(d)
    combined = out + err
    assert code == 1, combined
    assert "ADR-S010" in _extract_codes(combined)
    # Attributed to both records: a broken pair is a defect in the pair, and
    # reporting one side only makes the finding depend on scan order.
    assert "0001-a.md" in combined and "0002-b.md" in combined, combined


def test_s010_accepts_a_partial_mirror_whose_d_ids_agree(tmp_path):
    """The discriminating negative: same pair, matching D-IDs, reports nothing.

    Without this the test above would also pass against a lint that rejected
    every partial pair.
    """
    d = _write_dir(tmp_path, _partial_pair("ADR-0002 D1", "ADR-0001 D1"))
    code, out, err = _run(d)
    assert "ADR-S010" not in _extract_codes(out + err), out + err


def test_s010_reverse_only_partial_entry_names_both_records(tmp_path):
    """A `Superseded in part` with no counterpart reports against both records.

    The forward direction already did this; the reverse direction attributed
    the finding to the scanned record only.
    """
    d = _write_dir(tmp_path, _partial_pair("none", "ADR-0001 D1"))
    code, out, err = _run(d)
    combined = out + err
    assert code == 1, combined
    assert "ADR-S010" in _extract_codes(combined)
    assert "0001-a.md" in combined and "0002-b.md" in combined, combined


def _minimal(extra: str = "") -> str:
    return (
        "# ADR-0001: T\n\n"
        "- **Status:** Accepted\n"
        "- **Date:** 2026-09-17\n"
        "- **Areas:** governance\n"
        "- **Reversibility:** high\n"
        "- **Decision-makers:** someone\n"
        "- **Supersedes:** none\n"
        "- **Supersedes in part:** none\n"
        "- **Superseded by:** none\n"
        "- **Superseded in part:** none\n\n"
        "## Decision\n\n- **D1:** a\n\n"
        "## Consequences\n\n- **Revisit if:** something changes\n"
        + extra
    )


def test_s015_sees_a_correction_section_under_an_unobserved_spelling(tmp_path):
    """A correction heading the matcher cannot see evades the class entirely.

    ADR-S015's subject is "a correction section", not "a recognised spelling".
    `## Corrections` appears in neither RFC-0102 § 5's observed set nor the
    corpus, and previously produced no finding at all.
    """
    d = _write_dir(tmp_path, {"0001-a.md": _minimal(
        "\n## Corrections\n\n- 2026-09-17 — a clarification\n")})
    code, out, err = _run(d)
    assert "ADR-S015" in _extract_codes(out + err), out + err
    assert code == 1


def test_s015_ignores_a_content_section_that_merely_starts_with_corrected(
        tmp_path):
    """The discriminating negative, taken from a real record.

    `docs/adr/0105-*.md` carries `## Corrected transition table` — a content
    section holding a corrected table, not a correction log. A stem matcher
    that accepted trailing words flagged it, reddening the real corpus.
    """
    d = _write_dir(tmp_path, {"0001-a.md": _minimal(
        "\n## Corrected transition table\n\n| a | b |\n| --- | --- |\n")})
    code, out, err = _run(d)
    assert "ADR-S015" not in _extract_codes(out + err), out + err


def test_s012_fires_when_the_consequences_section_is_renamed(tmp_path):
    """S012 is unconditional; S013 is the one scoped to a present section.

    The spec's class table says "a PRESENT `## Confirmation`" for S013 and
    leaves S012's subject unqualified, so renaming the section away must not
    retire the Revisit-if requirement with it.
    """
    body = _minimal().replace("## Consequences", "## Outcome")
    d = _write_dir(tmp_path, {"0001-a.md": body})
    code, out, err = _run(d)
    assert "ADR-S012" in _extract_codes(out + err), out + err
    assert code == 1


def test_an_oversized_d_id_is_reported_and_the_record_still_counted(tmp_path):
    """AC-0005 makes the three buckets exhaustive "including a classification
    that raised". An unbounded `int()` on a record-controlled digit run raised
    ValueError above Python's conversion limit, aborting the scan with the
    record in no bucket and no summary printed.

    Every D-ID here is oversized, so `d_ids` ends up empty — the case that
    would slip past a check placed inside the `if rec.d_ids:` block.
    """
    body = _minimal().replace("- **D1:** a", f"- **D{'9' * 5000}:** a")
    d = _write_dir(tmp_path, {"0001-a.md": body})
    code, out, err = _run(d)
    combined = out + err
    assert "Traceback" not in combined, combined
    assert "ADR-S011" in _extract_codes(combined), combined
    counts = _parse_summary_counts(combined)
    assert counts["read"] == 1, counts
    assert code == 1
