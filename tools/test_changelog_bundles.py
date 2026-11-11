"""Bundle parts, cross-form identity, compact and retract (spec AC-B1 to AC-B11)."""
from __future__ import annotations

from pathlib import Path

from test_changelog import (
    VALID_ANCHOR,
    VALID_ID,
    _fragment_text,
    _write_fragment,
    changelog,
)

# ============================================================================
# T17: Monthly bundle parts, cross-form identity, compact, retract (AC-B2 – B11)
# ============================================================================

# ── helpers ──────────────────────────────────────────────────────────────────

VALID_ID_B = "22222222-2222-4222-8222-222222222222"
VALID_ANCHOR_B = "core300--2026-10-01-22222222222242228222222222222222"


def _bundle_fragment_text(
    *,
    fragment_id: str = VALID_ID_B,
    anchor: str = VALID_ANCHOR_B,
    date: str = "2026-10-01",
    packages: str = '[[packages]]\nname = "core"\nversion = "3.0.0"',
    body: str = "## Highlights\n- Bundle test highlight.\n",
) -> str:
    return (
        "+++\n"
        "schema = 1\n"
        f'id = "{fragment_id}"\n'
        f'anchor = "{anchor}"\n'
        f"date = {date}\n"
        f"{packages}\n"
        "+++\n"
        f"{body}"
    )


def _make_bundle_part(
    directory: Path,
    name: str,
    records: list[str],
) -> Path:
    """Write a bundle part file from a list of record-text strings."""
    content = b""
    for rec in records:
        content += changelog.BUNDLE_SEPARATOR_BYTES + rec.encode("utf-8")
    part = directory / name
    part.parent.mkdir(parents=True, exist_ok=True)
    part.write_bytes(content)
    return part


# ── AC-B2: container validation ───────────────────────────────────────────────


def test_bundle_part_refuses_missing_leading_separator(tmp_path: Path) -> None:
    """AC-B2: a part not starting with the separator is refused."""
    bundle_dir = tmp_path / "changelog.months"
    bundle_dir.mkdir()
    part = bundle_dir / "2026-10-00.bundle"
    part.write_bytes(b"schema = 1\n")
    try:
        changelog._parse_bundle_part(part, part.read_bytes())
    except changelog.FragmentValidationError as e:
        assert str(part) in str(e) and "separator" in str(e).lower()
    else:
        raise AssertionError("missing leading separator was accepted")


def test_bundle_part_refuses_empty_record(tmp_path: Path) -> None:
    """AC-B2: an empty record (two consecutive separators) is refused."""
    bundle_dir = tmp_path / "changelog.months"
    bundle_dir.mkdir()
    part = bundle_dir / "2026-10-00.bundle"
    # Two consecutive separators = one empty record.
    content = changelog.BUNDLE_SEPARATOR_BYTES + changelog.BUNDLE_SEPARATOR_BYTES
    part.write_bytes(content)
    try:
        changelog._parse_bundle_part(part, content)
    except changelog.FragmentValidationError as e:
        assert str(part) in str(e) and ("empty" in str(e).lower() or "record" in str(e).lower())
    else:
        raise AssertionError("empty record was accepted")


def test_bundle_part_refuses_record_without_final_lf(tmp_path: Path) -> None:
    """AC-B2: a record missing its final LF is refused."""
    bundle_dir = tmp_path / "changelog.months"
    bundle_dir.mkdir()
    # Record text without trailing newline.
    rec = _bundle_fragment_text().encode("utf-8").rstrip(b"\n")
    part = bundle_dir / "2026-10-00.bundle"
    content = changelog.BUNDLE_SEPARATOR_BYTES + rec
    part.write_bytes(content)
    try:
        changelog._parse_bundle_part(part, content)
    except changelog.FragmentValidationError as e:
        assert str(part) in str(e) and ("LF" in str(e) or "lf" in str(e).lower() or "record" in str(e).lower())
    else:
        raise AssertionError("record without final LF was accepted")


def test_bundle_part_refuses_bom(tmp_path: Path) -> None:
    """AC-B2: a part with a BOM is refused."""
    bundle_dir = tmp_path / "changelog.months"
    bundle_dir.mkdir()
    part = bundle_dir / "2026-10-00.bundle"
    rec = _bundle_fragment_text().encode("utf-8")
    content = b"\xef\xbb\xbf" + changelog.BUNDLE_SEPARATOR_BYTES + rec
    part.write_bytes(content)
    try:
        changelog._parse_bundle_part(part, content)
    except changelog.FragmentValidationError as e:
        assert str(part) in str(e) and ("bom" in str(e).lower() or "byte-order" in str(e).lower())
    else:
        raise AssertionError("BOM was accepted")


def test_bundle_part_refuses_cr(tmp_path: Path) -> None:
    """AC-B2: a part containing a CR is refused."""
    bundle_dir = tmp_path / "changelog.months"
    bundle_dir.mkdir()
    rec = _bundle_fragment_text().encode("utf-8")
    content = changelog.BUNDLE_SEPARATOR_BYTES + rec.replace(b"\n", b"\r\n")
    part = bundle_dir / "2026-10-00.bundle"
    part.write_bytes(content)
    try:
        changelog._parse_bundle_part(part, content)
    except changelog.FragmentValidationError as e:
        assert str(part) in str(e) and ("cr" in str(e).lower() or "lf" in str(e).lower() or "line" in str(e).lower())
    else:
        raise AssertionError("CR in bundle part was accepted")


def test_bundle_part_refuses_non_utf8(tmp_path: Path) -> None:
    """AC-B2: a part with non-UTF-8 bytes in a record is refused."""
    bundle_dir = tmp_path / "changelog.months"
    bundle_dir.mkdir()
    rec = b"\xff\xfe some garbage bytes\n"
    content = changelog.BUNDLE_SEPARATOR_BYTES + rec
    part = bundle_dir / "2026-10-00.bundle"
    part.write_bytes(content)
    try:
        changelog._parse_bundle_part(part, content)
    except changelog.FragmentValidationError as e:
        assert str(part) in str(e) and "utf" in str(e).lower()
    else:
        raise AssertionError("non-UTF-8 bytes were accepted")


def test_bundle_part_refuses_duplicate_ids(tmp_path: Path) -> None:
    """AC-B2: two records with equal canonical keys (same id) are refused."""
    bundle_dir = tmp_path / "changelog.months"
    bundle_dir.mkdir()
    rec1 = _bundle_fragment_text()
    rec2 = _bundle_fragment_text()  # same id = VALID_ID_B
    content = (
        changelog.BUNDLE_SEPARATOR_BYTES + rec1.encode("utf-8")
        + changelog.BUNDLE_SEPARATOR_BYTES + rec2.encode("utf-8")
    )
    part = bundle_dir / "2026-10-00.bundle"
    part.write_bytes(content)
    seen: set[str] = set()
    try:
        changelog._parse_bundle_part(part, content, seen_ids=seen)
    except changelog.FragmentValidationError as e:
        assert str(part) in str(e) and "duplicate" in str(e).lower()
    else:
        raise AssertionError("duplicate id was accepted")


def test_bundle_part_refuses_out_of_order_records(tmp_path: Path) -> None:
    """AC-B2: records out of canonical order are refused."""
    bundle_dir = tmp_path / "changelog.months"
    bundle_dir.mkdir()
    # rec_b is later by date, so it should come first in canonical order (date desc).
    id_a = "33333333-3333-4333-8333-333333333333"
    anchor_a = "core300--2026-10-01-33333333333343338333333333333333"
    id_b = "44444444-4444-4444-8444-444444444444"
    anchor_b = "core300--2026-10-02-44444444444444448444444444444444"
    # Put the earlier date first (wrong order for date desc).
    rec_a = _bundle_fragment_text(fragment_id=id_a, anchor=anchor_a, date="2026-10-01")
    rec_b = _bundle_fragment_text(fragment_id=id_b, anchor=anchor_b, date="2026-10-02")
    content = (
        changelog.BUNDLE_SEPARATOR_BYTES + rec_a.encode("utf-8")
        + changelog.BUNDLE_SEPARATOR_BYTES + rec_b.encode("utf-8")
    )
    part = bundle_dir / "2026-10-00.bundle"
    part.write_bytes(content)
    try:
        changelog._parse_bundle_part(part, content)
    except changelog.FragmentValidationError as e:
        assert str(part) in str(e) and ("order" in str(e).lower() or "canonical" in str(e).lower())
    else:
        raise AssertionError("out-of-order records were accepted")


def test_bundle_part_accepts_fenced_diff_line(tmp_path: Path) -> None:
    """AC-B2: a fenced `+++ b/path` line in a body is accepted."""
    bundle_dir = tmp_path / "changelog.months"
    bundle_dir.mkdir()
    # Body with a diff header inside a fenced code block.
    body = "## Highlights\n- Has a diff.\n\n```diff\n+++ b/some/path\n```\n"
    rec = _bundle_fragment_text(body=body)
    content = changelog.BUNDLE_SEPARATOR_BYTES + rec.encode("utf-8")
    part = bundle_dir / "2026-10-00.bundle"
    part.write_bytes(content)
    # Should not raise.
    result = changelog._parse_bundle_part(part, content)
    assert len(result) == 1


# ── AC-B2a: bundle-ready fragment validation ──────────────────────────────────


def test_validate_fragment_refuses_non_utf8(tmp_path: Path) -> None:
    """AC-B2a: a fragment holding a byte that is not UTF-8 is refused by path."""
    text = _fragment_text(fragment_id=VALID_ID, anchor=VALID_ANCHOR)
    path = tmp_path / f"{VALID_ID}.md"
    path.write_bytes(text.encode("utf-8").replace(b"Adds", b"Ad\x80ds", 1))
    assert b"\x80" in path.read_bytes(), "fixture lost its non-UTF-8 byte"
    try:
        changelog.validate_fragment(path, enforce_immutability=False)
    except changelog.FragmentValidationError as e:
        assert str(path) in str(e) and "utf-8" in str(e).lower()
    else:
        raise AssertionError("a non-UTF-8 byte was accepted")


def test_validate_fragment_refuses_bom(tmp_path: Path) -> None:
    """AC-B2a: a fragment with a BOM is refused."""
    frag_id = VALID_ID
    anchor = VALID_ANCHOR
    text = _fragment_text(fragment_id=frag_id, anchor=anchor)
    path = tmp_path / f"{frag_id}.md"
    path.write_bytes(b"\xef\xbb\xbf" + text.encode("utf-8"))
    try:
        changelog.validate_fragment(path, enforce_immutability=False)
    except changelog.FragmentValidationError as e:
        assert str(path) in str(e) and ("bom" in str(e).lower() or "byte-order" in str(e).lower())
    else:
        raise AssertionError("BOM was accepted")


def test_validate_fragment_refuses_cr(tmp_path: Path) -> None:
    """AC-B2a: a fragment with a CR is refused."""
    frag_id = VALID_ID
    text = _fragment_text()
    path = tmp_path / f"{frag_id}.md"
    path.write_bytes(text.encode("utf-8").replace(b"\n", b"\r\n"))
    try:
        changelog.validate_fragment(path, enforce_immutability=False)
    except changelog.FragmentValidationError as e:
        assert str(path) in str(e) and ("cr" in str(e).lower() or "lf" in str(e).lower())
    else:
        raise AssertionError("CR in fragment was accepted")


def test_validate_fragment_refuses_missing_final_lf(tmp_path: Path) -> None:
    """AC-B2a: a fragment without a final LF is refused."""
    frag_id = VALID_ID
    text = _fragment_text().rstrip("\n")
    path = tmp_path / f"{frag_id}.md"
    path.write_bytes(text.encode("utf-8"))
    try:
        changelog.validate_fragment(path, enforce_immutability=False)
    except changelog.FragmentValidationError as e:
        assert str(path) in str(e) and "final" in str(e).lower()
    else:
        raise AssertionError("missing final LF was accepted")


def test_validate_fragment_refuses_separator_line(tmp_path: Path) -> None:
    """AC-B2a: a fragment containing a separator line is refused."""
    frag_id = VALID_ID
    body = f"## Highlights\n- OK.\n{changelog.BUNDLE_SEPARATOR_LINE}\n"
    text = _fragment_text(body=body)
    path = tmp_path / f"{frag_id}.md"
    path.write_text(text, encoding="utf-8")
    try:
        changelog.validate_fragment(path, enforce_immutability=False)
    except changelog.FragmentValidationError as e:
        assert str(path) in str(e) and "separator" in str(e).lower()
    else:
        raise AssertionError("separator line in fragment was accepted")


# ── AC-B3: part names ─────────────────────────────────────────────────────────


def test_validate_bundle_part_name_accepts_valid_name(tmp_path: Path) -> None:
    """AC-B3: a valid YYYY-MM-NN.bundle name is accepted."""
    part = tmp_path / "2026-10-00.bundle"
    yyyy, mm, nn = changelog._validate_bundle_part_name(part, tmp_path)
    assert yyyy == "2026" and mm == "10" and nn == "00"


def test_validate_bundle_part_name_refuses_bad_format(tmp_path: Path) -> None:
    """AC-B3: a name not matching YYYY-MM-NN.bundle is refused."""
    for bad in ("2026-10.bundle", "2026-10-001.bundle", "2026-10-0.bundle",
                "notadate.bundle", "2026-13-00.bundle"):
        part = tmp_path / bad
        try:
            changelog._validate_bundle_part_name(part, tmp_path)
        except changelog.FragmentValidationError:
            pass
        else:
            raise AssertionError(f"bad name {bad!r} was accepted")


def test_bundle_part_refuses_record_date_mismatch(tmp_path: Path) -> None:
    """AC-B3: a record whose date month differs from the part month is refused."""
    bundle_dir = tmp_path / "changelog.months"
    bundle_dir.mkdir()
    # Record is dated 2026-09 but part is for 2026-10.
    id_a = "55555555-5555-4555-8555-555555555555"
    anchor_a = "core300--2026-09-01-55555555555545558555555555555555"
    rec = _bundle_fragment_text(fragment_id=id_a, anchor=anchor_a, date="2026-09-01")
    content = changelog.BUNDLE_SEPARATOR_BYTES + rec.encode("utf-8")
    part = bundle_dir / "2026-10-00.bundle"
    part.write_bytes(content)
    try:
        changelog._parse_bundle_part(part, content, part_month="2026-10")
    except changelog.FragmentValidationError as e:
        assert str(part) in str(e) and "month" in str(e).lower()
    else:
        raise AssertionError("date-month mismatch was accepted")


# ── AC-B3a: read confinement ──────────────────────────────────────────────────


def test_bundle_dir_confinement_refuses_symlink(tmp_path: Path) -> None:
    """AC-B3a: a symlink in the bundle directory is refused."""
    bundle_dir = tmp_path / "changelog.months"
    bundle_dir.mkdir()
    target = tmp_path / "real_file.bundle"
    target.write_bytes(changelog.BUNDLE_SEPARATOR_BYTES + _bundle_fragment_text().encode())
    link = bundle_dir / "2026-10-00.bundle"
    link.symlink_to(target)
    fs = changelog._file_safety()
    try:
        changelog._collect_bundle_records(bundle_dir, fs)
    except (changelog.FragmentValidationError, fs.UnsafeContentError):
        pass
    else:
        raise AssertionError("symlink in bundle dir was accepted")


def test_retraction_list_confinement_refuses_symlink(tmp_path: Path) -> None:
    """AC-B3a: a symlink at the retraction list path is refused."""
    real = tmp_path / "real_retractions.toml"
    real.write_text("", encoding="utf-8")
    retraction_path = tmp_path / "changelog-retractions.toml"
    retraction_path.symlink_to(real)
    fs = changelog._file_safety()
    try:
        changelog._read_retraction_list(retraction_path, fs)
    except (changelog.FragmentValidationError, fs.UnsafeContentError):
        pass  # symlink correctly refused
    else:
        raise AssertionError(
            "symlink at retraction list path was accepted; expected "
            "FragmentValidationError or UnsafeContentError"
        )


# ── AC-B4: cross-form identity (seam-level) ───────────────────────────────────


def test_missing_git_binary_refuses_rather_than_passing(tmp_path: Path) -> None:
    """AC-B4/AC4 fail-closed: a missing git binary must refuse, not silently skip.

    When the git runner raises FileNotFoundError (git not on PATH), identity
    enforcement must raise FragmentValidationError rather than treating the
    situation as 'not a git repository' (which would disable enforcement).
    """
    frag_dir = tmp_path / "changelog.d"
    frag_dir.mkdir()
    bundle_dir = tmp_path / "changelog.months"
    bundle_dir.mkdir()
    retraction_path = tmp_path / "changelog-retractions.toml"

    def git_raises_file_not_found(cwd: Path, *args: str) -> None:
        raise FileNotFoundError("git: No such file or directory")

    try:
        changelog.validate_changelog_cross_form_identity(
            fragment_dir=frag_dir,
            bundle_dir=bundle_dir,
            retraction_path=retraction_path,
            git_runner=git_raises_file_not_found,
        )
    except changelog.FragmentValidationError as e:
        assert "git" in str(e).lower(), (
            f"expected git-related error, got: {e}"
        )
    else:
        raise AssertionError(
            "missing git binary was treated as 'not a repo' (fail-open); "
            "expected FragmentValidationError"
        )


def test_compute_git_object_id_sha1_matches_known_hash() -> None:
    """AC-B4: object id is computed as git's blob hash (SHA-1)."""
    import hashlib as _hashlib
    data = b"hello world\n"
    header = b"blob " + str(len(data)).encode() + b"\0"
    expected = _hashlib.sha1(header + data, usedforsecurity=False).hexdigest()
    result = changelog._compute_git_object_id(data, "sha1")
    assert result == expected


def test_compute_git_object_id_sha256_matches_known_hash() -> None:
    """AC-B4: object id uses SHA-256 when the repo uses it."""
    import hashlib as _hashlib
    data = b"hello world\n"
    header = b"blob " + str(len(data)).encode() + b"\0"
    expected = _hashlib.sha256(header + data).hexdigest()
    result = changelog._compute_git_object_id(data, "sha256")
    assert result == expected


def test_collect_changelog_records_returns_two_lists(tmp_path: Path) -> None:
    """AC-B8: collect_changelog_records returns (loose, bundled) lists."""
    frag_dir = tmp_path / "changelog.d"
    frag_dir.mkdir()
    bundle_dir = tmp_path / "changelog.months"
    bundle_dir.mkdir()
    # Write one loose fragment.
    _write_fragment(frag_dir)
    loose, bundled = changelog.collect_changelog_records(
        fragment_dir=frag_dir,
        bundle_dir=bundle_dir,
        retraction_path=tmp_path / "changelog-retractions.toml",
    )
    assert len(loose) == 1
    assert len(bundled) == 0


def test_collect_changelog_records_includes_bundle_records(tmp_path: Path) -> None:
    """AC-B8: bundled records are returned in the second list."""
    frag_dir = tmp_path / "changelog.d"
    frag_dir.mkdir()
    bundle_dir = tmp_path / "changelog.months"
    bundle_dir.mkdir()
    rec = _bundle_fragment_text()
    content = changelog.BUNDLE_SEPARATOR_BYTES + rec.encode("utf-8")
    (bundle_dir / "2026-10-00.bundle").write_bytes(content)
    loose, bundled = changelog.collect_changelog_records(
        fragment_dir=frag_dir,
        bundle_dir=bundle_dir,
        retraction_path=tmp_path / "changelog-retractions.toml",
    )
    assert len(loose) == 0
    assert len(bundled) == 1
    assert bundled[0].id == VALID_ID_B


# ── AC-B5: raw bytes ──────────────────────────────────────────────────────────


def test_raw_bytes_comparison_detects_cr_in_moved_record() -> None:
    """AC-B5: raw-byte comparison detects a CR introduced in a moved record."""
    # The object id of bytes-with-CR will differ from bytes-without-CR.
    data_clean = b"hello\n"
    data_dirty = b"hello\r\n"
    id_clean = changelog._compute_git_object_id(data_clean, "sha1")
    id_dirty = changelog._compute_git_object_id(data_dirty, "sha1")
    assert id_clean != id_dirty


# ── AC-B7: bounds ─────────────────────────────────────────────────────────────


def test_bundle_part_refused_if_over_size_limit(tmp_path: Path) -> None:
    """AC-B7: a part over 1,048,576 bytes is refused by the reader."""
    bundle_dir = tmp_path / "changelog.months"
    bundle_dir.mkdir()
    # Create a bundle part that is just over the size limit.
    part = bundle_dir / "2026-10-00.bundle"
    # Write a file that's too big (content does not matter; testing the byte bound).
    part.write_bytes(b"x" * (changelog.MAX_BUNDLE_BYTES + 1))
    fs = changelog._file_safety()
    try:
        changelog._collect_bundle_records(bundle_dir, fs)
    except (changelog.FragmentValidationError, fs.UnsafeContentError) as exc:
        assert (
            str(changelog.MAX_BUNDLE_BYTES) in str(exc)
            or "bound" in str(exc).lower()
            or "bytes" in str(exc).lower()
            or "size" in str(exc).lower()
        ), f"error message does not reference the byte bound: {exc}"
    else:
        raise AssertionError(
            "over-size bundle part was accepted; expected FragmentValidationError "
            "or UnsafeContentError naming the byte bound"
        )


def test_record_count_cap_is_enforced(tmp_path: Path, monkeypatch) -> None:
    """AC-B7: more than 65,536 records across both forms is refused.

    Constant check: the cap is set to the specified value.

    Behavioural check: monkeypatches ``MAX_RECORD_COUNT`` to 3, builds a
    mixed record set (1 loose fragment + 1 bundle part holding 3 records = 4
    total), asserts the reader raises ``BundleValidationError`` naming the
    bound; and that a set of exactly 3 records (1 loose + 1 part with 2
    records) is accepted.
    """
    assert changelog.MAX_RECORD_COUNT == 65_536

    monkeypatch.setattr(changelog, "MAX_RECORD_COUNT", 3)

    frag_dir = tmp_path / "changelog.d"
    frag_dir.mkdir()
    bundle_dir = tmp_path / "changelog.months"
    bundle_dir.mkdir()
    retraction_path = tmp_path / "changelog-retractions.toml"

    SEPARATOR = "+++ record +++\n"

    # Loose fragment (counts as 1).
    frag_id = "11111111-1111-4111-8111-111111111111"
    anchor = changelog._compose_fragment_anchor(
        [{"name": "core", "version": "3.0.0"}], "2026-10-01", frag_id
    )
    frag_text = _fragment_text(fragment_id=frag_id, anchor=anchor, date="2026-10-01")
    (frag_dir / f"{frag_id}.md").write_text(frag_text, encoding="utf-8")

    # Bundle part with 3 records (counts as 3 more = total 4 → over the cap).
    # All bundled records use version "3.0.0" to match _fragment_text's default
    # packages string so the anchor recomputation inside the validator agrees.
    def _bundled(idx: int) -> str:
        bid = f"2222222{idx}-2222-4222-8222-222222222222"
        banc = changelog._compose_fragment_anchor(
            [{"name": "core", "version": "3.0.0"}], "2026-09-01", bid
        )
        return _fragment_text(fragment_id=bid, anchor=banc, date="2026-09-01")

    part_content = SEPARATOR + _bundled(0) + SEPARATOR + _bundled(1) + SEPARATOR + _bundled(2)
    (bundle_dir / "2026-09-01.bundle").write_text(part_content, encoding="utf-8")

    # 4 total (1 loose + 3 bundled) > cap of 3 → must refuse with a diagnostic.
    try:
        changelog.collect_changelog_records(
            fragment_dir=frag_dir,
            bundle_dir=bundle_dir,
            retraction_path=retraction_path,
        )
    except changelog.FragmentValidationError as exc:
        msg = str(exc)
        assert "3" in msg, (
            f"FragmentValidationError does not name the bound (3): {msg!r}"
        )
    else:
        raise AssertionError(
            "collect_changelog_records did not refuse 4 records when cap=3"
        )

    # 3 total (1 loose + 2 bundled) == cap → must accept.
    part_content_2 = SEPARATOR + _bundled(0) + SEPARATOR + _bundled(1)
    (bundle_dir / "2026-09-01.bundle").write_text(part_content_2, encoding="utf-8")
    loose, bundled = changelog.collect_changelog_records(
        fragment_dir=frag_dir,
        bundle_dir=bundle_dir,
        retraction_path=retraction_path,
    )
    assert len(loose) + len(bundled) == 3, (
        f"collect_changelog_records refused exactly-3 records: got {len(loose) + len(bundled)}"
    )


# ── AC-B8: single reader and ceiling ─────────────────────────────────────────


def test_file_safety_helper_loads_once_for_collect_changelog_records(
    tmp_path: Path, monkeypatch,
) -> None:
    """AC-B1 extended: one helper load for collect_changelog_records."""
    frag_dir = tmp_path / "changelog.d"
    frag_dir.mkdir()
    bundle_dir = tmp_path / "changelog.months"
    bundle_dir.mkdir()
    _write_fragment(frag_dir)
    loads = 0
    original = changelog._file_safety

    def counted():
        nonlocal loads
        loads += 1
        return original()

    monkeypatch.setattr(changelog, "_file_safety", counted)
    changelog.collect_changelog_records(
        fragment_dir=frag_dir,
        bundle_dir=bundle_dir,
        retraction_path=tmp_path / "no-retractions.toml",
    )
    assert loads == 1


# ── AC-B6: compaction ────────────────────────────────────────────────────────


def test_compact_requires_real_month(tmp_path: Path) -> None:
    """AC-B6: compact refuses a non-real month."""
    try:
        changelog.compact_month(
            "2026-13",
            fragment_dir=tmp_path / "d",
            bundle_dir=tmp_path / "m",
        )
    except changelog.FragmentValidationError as e:
        assert "month" in str(e).lower() or "YYYY-MM" in str(e)
    else:
        raise AssertionError("invalid month was accepted")


def test_compact_does_not_read_clock(tmp_path: Path, monkeypatch) -> None:
    """AC-B6: compact must not read the wall clock; the month is the only time source.

    Creates real released fragments for 2026-10, patches every clock entry
    point reachable from changelog.compact_month (date.today via the module's
    ``date`` attribute, and time.time/time.localtime within the module
    namespace), runs compaction, and asserts it succeeded. The patched wrappers
    raise AssertionError on any clock call, so the test fails if compact ever
    queries the wall time.
    """
    import datetime as _dt

    frag_dir = tmp_path / "changelog.d"
    frag_dir.mkdir()
    bundle_dir = tmp_path / "changelog.months"
    bundle_dir.mkdir()

    # Write a real released fragment for 2026-10.
    frag_id = "cccccccc-cccc-4ccc-8ccc-cccccccccccc"
    anchor = changelog._compose_fragment_anchor(
        [{"name": "core", "version": "3.0.0"}], "2026-10-01", frag_id
    )
    text = _fragment_text(
        fragment_id=frag_id,
        anchor=anchor,
        date="2026-10-01",
    )
    (frag_dir / f"{frag_id}.md").write_text(text, encoding="utf-8")

    # Build a proxy for the `date` class that raises if any clock method is called.
    # The metaclass overrides __instancecheck__ so that isinstance(x, _NoClock)
    # accepts any real datetime.date instance; without this, the fragment validator's
    # ``isinstance(data["date"], date)`` check would always fail once date is patched.
    real_date = _dt.date

    class _NoClockMeta(type(real_date)):
        def __instancecheck__(cls, instance: object) -> bool:
            return isinstance(instance, real_date)

    class _NoClock(real_date, metaclass=_NoClockMeta):
        @classmethod
        def today(cls):  # type: ignore[override]
            raise AssertionError("compact_month called date.today() — clock read forbidden")

        @classmethod
        def fromtimestamp(cls, *a, **kw):  # type: ignore[override]
            raise AssertionError(
                "compact_month called date.fromtimestamp() — clock read forbidden"
            )

    # Patch changelog.date with our no-clock proxy.
    monkeypatch.setattr(changelog, "date", _NoClock)

    # Also intercept time module if compact somehow reaches it.
    import time as _time

    def _no_time(*a, **kw):
        raise AssertionError("compact_month called time.time() — clock read forbidden")

    def _no_localtime(*a, **kw):
        raise AssertionError("compact_month called time.localtime() — clock read forbidden")

    monkeypatch.setattr(_time, "time", _no_time)
    monkeypatch.setattr(_time, "localtime", _no_localtime)

    # Run the real compaction — it must move the fragment without reading the clock.
    created, deleted = changelog.compact_month(
        "2026-10",
        fragment_dir=frag_dir,
        bundle_dir=bundle_dir,
        released_versions={"core": {"3.0.0"}},
    )

    assert len(created) == 1, f"expected 1 bundle part created, got {created}"
    assert len(deleted) == 1, f"expected 1 fragment deleted, got {deleted}"
    assert not (frag_dir / f"{frag_id}.md").exists(), "fragment should have been deleted"
    # Verify the bundle part contains the moved record.
    part_bytes = created[0].read_bytes()
    records = changelog._parse_bundle_part(created[0], part_bytes)
    assert len(records) == 1 and records[0][1].id == frag_id, (
        "bundle part does not contain the expected record"
    )


def test_compact_moves_released_fragment_to_bundle(tmp_path: Path) -> None:
    """AC-B6: compact moves a released fragment into a bundle part."""
    frag_dir = tmp_path / "changelog.d"
    frag_dir.mkdir()
    bundle_dir = tmp_path / "changelog.months"
    bundle_dir.mkdir()
    # Write a fragment dated 2026-10.
    frag_id = "66666666-6666-4666-8666-666666666666"
    anchor = "core300--2026-10-01-66666666666646668666666666666666"
    text = _fragment_text(
        fragment_id=frag_id,
        anchor=anchor,
        date="2026-10-01",
    )
    (frag_dir / f"{frag_id}.md").write_text(text, encoding="utf-8")
    created, deleted = changelog.compact_month(
        "2026-10",
        fragment_dir=frag_dir,
        bundle_dir=bundle_dir,
        released_versions={"core": {"3.0.0"}},
    )
    assert len(created) == 1
    assert len(deleted) == 1
    assert not (frag_dir / f"{frag_id}.md").exists()
    # Bundle part should contain the record.
    part_bytes = created[0].read_bytes()
    records = changelog._parse_bundle_part(created[0], part_bytes)
    assert len(records) == 1
    assert records[0][1].id == frag_id


def test_compact_leaves_pending_fragment(tmp_path: Path) -> None:
    """AC-B6: compact does not move an unreleased (pending) fragment."""
    frag_dir = tmp_path / "changelog.d"
    frag_dir.mkdir()
    bundle_dir = tmp_path / "changelog.months"
    bundle_dir.mkdir()
    frag_id = "77777777-7777-4777-8777-777777777777"
    anchor = "core400--2026-10-01-77777777777747778777777777777777"
    text = _fragment_text(
        fragment_id=frag_id,
        anchor=anchor,
        date="2026-10-01",
        packages='[[packages]]\nname = "core"\nversion = "4.0.0"',
    )
    (frag_dir / f"{frag_id}.md").write_text(text, encoding="utf-8")
    # core 4.0.0 is NOT in the released inventory.
    created, deleted = changelog.compact_month(
        "2026-10",
        fragment_dir=frag_dir,
        bundle_dir=bundle_dir,
        released_versions={"core": {"3.0.0"}},
    )
    assert len(created) == 0
    assert len(deleted) == 0
    assert (frag_dir / f"{frag_id}.md").exists()


def test_compact_reruns_complete_deletion(tmp_path: Path) -> None:
    """AC-B6: a rerun of compact for a month that was partially deleted completes."""
    frag_dir = tmp_path / "changelog.d"
    frag_dir.mkdir()
    bundle_dir = tmp_path / "changelog.months"
    bundle_dir.mkdir()
    frag_id = "88888888-8888-4888-8888-888888888888"
    anchor = "core300--2026-10-01-88888888888848888888888888888888"
    text = _fragment_text(fragment_id=frag_id, anchor=anchor, date="2026-10-01")
    frag_path = frag_dir / f"{frag_id}.md"
    frag_path.write_text(text, encoding="utf-8")
    # First compact: creates the bundle part.
    created, _ = changelog.compact_month(
        "2026-10",
        fragment_dir=frag_dir,
        bundle_dir=bundle_dir,
        released_versions={"core": {"3.0.0"}},
    )
    assert len(created) == 1
    # Simulate the fragment NOT being deleted (simulating a crash).
    frag_path.write_text(text, encoding="utf-8")
    # Rerun: the fragment is already bundled, so it should be deleted.
    created2, deleted2 = changelog.compact_month(
        "2026-10",
        fragment_dir=frag_dir,
        bundle_dir=bundle_dir,
        released_versions={"core": {"3.0.0"}},
    )
    # The spec (AC-B6) is unambiguous: the rerun completes the deletion.
    assert not frag_path.exists()


def test_compact_leaves_view_byte_identical(tmp_path: Path) -> None:
    """AC-B6: the complete view is byte-identical after compaction."""
    frag_dir = tmp_path / "changelog.d"
    frag_dir.mkdir()
    bundle_dir = tmp_path / "changelog.months"
    bundle_dir.mkdir()
    frag_id = "99999999-9999-4999-8999-999999999999"
    anchor = "core300--2026-10-01-99999999999949998999999999999999"
    text = _fragment_text(fragment_id=frag_id, anchor=anchor, date="2026-10-01")
    (frag_dir / f"{frag_id}.md").write_text(text, encoding="utf-8")
    baseline = "# Changelog\n\n## [1.0.0] — 2020-01-01\n\n### Highlights\n- Old.\n"
    released = {"core": {"3.0.0"}}
    # Assemble before compact.
    loose_before = changelog.collect_validated_fragments(
        frag_dir, enumerator=lambda _: [frag_dir / f"{frag_id}.md"]
    )
    view_before = changelog.assemble_changelog(baseline, loose_before, released_versions=released)
    # Compact.
    changelog.compact_month(
        "2026-10",
        fragment_dir=frag_dir,
        bundle_dir=bundle_dir,
        released_versions=released,
    )
    # Assemble after compact.
    loose_after, bundled_after = changelog.collect_changelog_records(
        fragment_dir=frag_dir,
        bundle_dir=bundle_dir,
        retraction_path=tmp_path / "no-retractions.toml",
    )
    all_records = loose_after + bundled_after
    view_after = changelog.assemble_changelog(baseline, all_records, released_versions=released)
    assert view_before == view_after


# ── AC-B4a: retraction ────────────────────────────────────────────────────────


def test_retract_removes_record_and_appends_list_entry(tmp_path: Path) -> None:
    """AC-B4a: retract removes the record from its part and appends to the list."""
    bundle_dir = tmp_path / "changelog.months"
    bundle_dir.mkdir()
    retraction_path = tmp_path / "changelog-retractions.toml"
    rec = _bundle_fragment_text()
    content = changelog.BUNDLE_SEPARATOR_BYTES + rec.encode("utf-8")
    (bundle_dir / "2026-10-00.bundle").write_bytes(content)
    changelog.retract_record(
        VALID_ID_B, "other",
        bundle_dir=bundle_dir,
        retraction_path=retraction_path,
    )
    # Part should be deleted (only record removed).
    assert not (bundle_dir / "2026-10-00.bundle").exists()
    # Retraction list should exist and contain the entry.
    assert retraction_path.exists()
    import tomllib as _tomllib
    data = _tomllib.loads(retraction_path.read_text(encoding="utf-8"))
    retractions = data.get("retraction", [])
    assert any(e.get("category") == "other" for e in retractions)


def test_retract_rerun_completes_when_record_already_removed(tmp_path: Path) -> None:
    """AC-B4a: rerunning retract for an already-retracted id completes."""
    bundle_dir = tmp_path / "changelog.months"
    bundle_dir.mkdir()
    retraction_path = tmp_path / "changelog-retractions.toml"
    rec = _bundle_fragment_text()
    content = changelog.BUNDLE_SEPARATOR_BYTES + rec.encode("utf-8")
    (bundle_dir / "2026-10-00.bundle").write_bytes(content)
    # First retraction.
    changelog.retract_record(
        VALID_ID_B, "credential",
        bundle_dir=bundle_dir,
        retraction_path=retraction_path,
    )
    # Rerun should not raise.
    changelog.retract_record(
        VALID_ID_B, "credential",
        bundle_dir=bundle_dir,
        retraction_path=retraction_path,
    )


def test_retract_last_record_deletes_part(tmp_path: Path) -> None:
    """AC-B4a: retracting the last record of a part deletes the part."""
    bundle_dir = tmp_path / "changelog.months"
    bundle_dir.mkdir()
    retraction_path = tmp_path / "changelog-retractions.toml"
    rec = _bundle_fragment_text()
    part_path = bundle_dir / "2026-10-00.bundle"
    part_path.write_bytes(changelog.BUNDLE_SEPARATOR_BYTES + rec.encode("utf-8"))
    changelog.retract_record(
        VALID_ID_B, "legal",
        bundle_dir=bundle_dir,
        retraction_path=retraction_path,
    )
    assert not part_path.exists(), "part should be deleted after retracting last record"


def test_retraction_list_entry_has_required_fields(tmp_path: Path) -> None:
    """AC-B4a: each retraction list entry has a UUIDv4 id and a valid category."""
    bundle_dir = tmp_path / "changelog.months"
    bundle_dir.mkdir()
    retraction_path = tmp_path / "changelog-retractions.toml"
    rec = _bundle_fragment_text()
    (bundle_dir / "2026-10-00.bundle").write_bytes(
        changelog.BUNDLE_SEPARATOR_BYTES + rec.encode("utf-8")
    )
    changelog.retract_record(
        VALID_ID_B, "personal-data",
        bundle_dir=bundle_dir,
        retraction_path=retraction_path,
    )
    import tomllib as _tomllib
    data = _tomllib.loads(retraction_path.read_text(encoding="utf-8"))
    for entry in data.get("retraction", []):
        assert "id" in entry and "category" in entry
        from uuid import UUID as _UUID
        parsed = _UUID(entry["id"], version=4)
        assert parsed.version == 4
        assert entry["category"] in changelog._RETRACTION_CATEGORIES


def test_validate_retraction_list_refuses_unknown_fields(tmp_path: Path) -> None:
    """AC-B4a: retraction list entries with unknown fields are refused."""
    path = tmp_path / "changelog-retractions.toml"
    path.write_text(
        '[[retraction]]\nid = "11111111-1111-4111-8111-111111111111"\n'
        'category = "other"\nextra = "not allowed"\n',
        encoding="utf-8",
    )
    try:
        changelog._validate_retraction_list(path, [
            {"id": "11111111-1111-4111-8111-111111111111",
             "category": "other", "extra": "not allowed"}
        ])
    except changelog.FragmentValidationError as e:
        assert str(path) in str(e) and "known" in str(e).lower()
    else:
        raise AssertionError("unknown field was accepted")


def test_validate_retraction_list_refuses_duplicate_ids(tmp_path: Path) -> None:
    """AC-B4a: duplicate retraction ids are refused."""
    path = tmp_path / "changelog-retractions.toml"
    try:
        changelog._validate_retraction_list(path, [
            {"id": "11111111-1111-4111-8111-111111111111", "category": "other"},
            {"id": "11111111-1111-4111-8111-111111111111", "category": "credential"},
        ])
    except changelog.FragmentValidationError as e:
        assert str(path) in str(e) and "unique" in str(e).lower()
    else:
        raise AssertionError("duplicate retraction id was accepted")


# ── AC-B4b: retraction procedure text is present ─────────────────────────────


def test_retraction_procedure_text_in_agents_md() -> None:
    """AC-B4b: docs/product/AGENTS.md states the retraction procedure."""
    agents_md = Path(__file__).resolve().parent.parent / "docs/product/AGENTS.md"
    text = agents_md.read_text(encoding="utf-8")
    # Three required statements.
    assert "contain" in text.lower() or "rotate" in text.lower(), (
        "AGENTS.md does not say to contain/rotate a leaked credential first"
    )
    assert "diff" in text.lower() or "git history" in text.lower(), (
        "AGENTS.md does not mention that the diff/history still discloses"
    )
    assert "history rewrite" in text.lower() or "separate decision" in text.lower(), (
        "AGENTS.md does not state that any history rewrite is a separate decision"
    )


# ── AC-B8: ceiling thresholds ─────────────────────────────────────────────────


def test_ceiling_constants_match_adr_0143() -> None:
    """AC-B8: the threshold constants match ADR-0143 D9."""
    assert changelog.LOOSE_RELEASED_WARN_THRESHOLD == 375
    assert changelog.LOOSE_RELEASED_REFUSE_THRESHOLD == 500
    assert changelog.PENDING_WARN_THRESHOLD == 250


# ── AC-B8a: release evidence rules ───────────────────────────────────────────


# (AC-B8a tests live in test_check_release_impact.py — see below.)


# ── AC-B8b: release checklist compact step ───────────────────────────────────


def test_release_checklist_mentions_compact_step() -> None:
    """AC-B8b: packs/AGENTS.local.md states the compact step in the checklist."""
    agents_local = (
        Path(__file__).resolve().parent.parent / "packs" / "AGENTS.local.md"
    )
    text = agents_local.read_text(encoding="utf-8")
    assert "compact" in text.lower(), (
        "packs/AGENTS.local.md does not mention the compact step"
    )


# ── AC-B11: validate command exists ──────────────────────────────────────────


def test_validate_command_exits_zero_outside_git(tmp_path: Path) -> None:
    """AC-B11: `changelog.py validate` exits 0 when not in a git repo."""
    import subprocess as _subprocess
    result = _subprocess.run(
        [
            "python3",
            str(Path(__file__).resolve().parent / "changelog.py"),
            "validate",
        ],
        capture_output=True,
        cwd=str(tmp_path),  # not a git repo
    )
    assert result.returncode == 0


# ── AC-B9: merge replay with bundle parts on base ────────────────────────────


def test_bundle_merge_properties(tmp_path: Path) -> None:
    """AC-B9: bundle parts on the base do not conflict with fragment-adding branches.

    Replays five scenarios with ``git merge-tree --write-tree --name-only
    --merge-base=<base>`` in a throwaway git repository in tmp_path using
    Git's default merge behaviour (no merge.renames override):

    1. Twenty fragment-adding branches built on a base that contains a bundle
       part: all 190 unordered pairs are clean (0 conflicts, 0 errors).
    2. A fragment-adding branch (new file) vs a compaction commit (deletes a
       different fragment, creates a bundle part): clean merge.
    3. A body edit to a fragment vs a compaction that bundles it together with
       two other records (3-record part): modify/delete conflict (rc=1).
    3a. A body edit to a fragment vs a compaction into a 1-record part: either
        rc=1 (git detects the conflict), OR the merged bundle bytes are
        identical to the original compact bytes (the edit did not land). If
        git rename-merges silently AND the bundle content changed, the test
        fails — the edit would have landed without any conflict.
    4. Two concurrent compactions of the same month that each write the same
       bundle-part path with different content: add/add conflict (rc=1).
    """
    import itertools
    import os
    import subprocess

    _GIT_REDIRECTS = (
        "GIT_DIR",
        "GIT_WORK_TREE",
        "GIT_INDEX_FILE",
        "GIT_OBJECT_DIRECTORY",
        "GIT_ALTERNATE_OBJECT_DIRECTORIES",
    )
    env: dict[str, str] = {
        k: v for k, v in os.environ.items() if k not in _GIT_REDIRECTS
    }
    env.update(
        {
            "GIT_AUTHOR_NAME": "changelog-b9-test",
            "GIT_AUTHOR_EMAIL": "test@invalid",
            "GIT_COMMITTER_NAME": "changelog-b9-test",
            "GIT_COMMITTER_EMAIL": "test@invalid",
            "GIT_AUTHOR_DATE": "2026-01-01T00:00:00+00:00",
            "GIT_COMMITTER_DATE": "2026-01-01T00:00:00+00:00",
        }
    )

    def _run(*args: str) -> str:
        result = subprocess.run(
            ["git", "-C", str(tmp_path), *args],
            capture_output=True,
            text=True,
            env=env,
        )
        if result.returncode != 0:
            raise RuntimeError(
                f"git {' '.join(args)}: {result.stderr.strip()}"
            )
        return result.stdout.strip()

    def _merge_tree(
        base: str, ours: str, theirs: str
    ) -> tuple[int, str, tuple[str, ...]]:
        """Return (returncode, raw_stdout, named_paths)."""
        result = subprocess.run(
            [
                "git",
                "-C",
                str(tmp_path),
                "merge-tree",
                "--write-tree",
                "--name-only",
                f"--merge-base={base}",
                ours,
                theirs,
            ],
            capture_output=True,
            text=True,
            env=env,
        )
        paths = tuple(line for line in result.stdout.splitlines() if line)
        return result.returncode, result.stdout, paths

    # ── Initialise repository (default Git merge behaviour, no renames override) ─
    _run("init")
    _run("config", "user.email", "test@invalid")
    _run("config", "user.name", "changelog-b9-test")

    bundle_dir = tmp_path / "docs" / "product" / "changelog.months"
    bundle_dir.mkdir(parents=True)
    frag_dir = tmp_path / "docs" / "product" / "changelog.d"
    frag_dir.mkdir(parents=True)

    SEPARATOR = "+++ record +++\n"

    # Base: a bundle part for 2026-08 (already released) plus two loose
    # fragments for 2026-09.  fragment-X will be compacted; fragment-W is a
    # bystander that keeps changelog.d/ non-empty after compaction.
    (bundle_dir / "2026-08-01.bundle").write_text(
        SEPARATOR
        + "## Released\n\n### core 2.0.0 — 2026-08-01\n- base entry\n"
        + "<!-- aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa -->\n",
        encoding="utf-8",
    )

    frag_x_id = "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb"
    frag_x_path = frag_dir / f"{frag_x_id}.md"
    frag_x_content = (
        "## Released\n\n### core 3.0.0 — 2026-09-01\n- feature X\n"
        f"<!-- {frag_x_id} -->\n"
    )
    frag_x_path.write_text(frag_x_content, encoding="utf-8")

    frag_w_id = "dddddddd-dddd-4ddd-8ddd-dddddddddddd"
    frag_w_path = frag_dir / f"{frag_w_id}.md"
    (frag_w_path).write_text(
        "## Released\n\n### core 3.0.1 — 2026-09-02\n- feature W\n"
        f"<!-- {frag_w_id} -->\n",
        encoding="utf-8",
    )

    _run("add", ".")
    _run("commit", "-m", "base")
    base_sha = _run("rev-parse", "HEAD")

    def _checkout_base() -> None:
        _run("checkout", "--detach", base_sha)

    # ── Scenario 1: twenty fragment-adding branches on a base with bundle part ─
    # All 190 unordered pairs must merge cleanly (0 conflicts, 0 errors).

    BRANCH_COUNT = 20
    fragment_shas: list[str] = []
    for idx in range(BRANCH_COUNT):
        _checkout_base()
        branch = f"add-frag-{idx:02d}"
        _run("checkout", "-b", branch)
        new_frag_id = f"cc{idx:06d}00-cccc-4ccc-8ccc-cccccccccccc"
        frag_content = (
            "## Released\n\n### core 3.1.0 — 2026-09-15\n"
            f"- feature {idx}\n<!-- {new_frag_id} -->\n"
        )
        (frag_dir / f"{new_frag_id}.md").write_text(frag_content, encoding="utf-8")
        _run("add", ".")
        _run("commit", "-m", f"add fragment {idx:02d}")
        fragment_shas.append(_run("rev-parse", "HEAD"))

    pairs = list(itertools.combinations(fragment_shas, 2))
    assert len(pairs) == BRANCH_COUNT * (BRANCH_COUNT - 1) // 2 == 190
    clean_1 = conflicts_1 = errors_1 = 0
    for sha_a, sha_b in pairs:
        rc, _, _ = _merge_tree(base_sha, sha_a, sha_b)
        if rc == 0:
            clean_1 += 1
        elif rc == 1:
            conflicts_1 += 1
        else:
            errors_1 += 1

    assert errors_1 == 0, (
        f"Scenario 1: {errors_1} harness errors in {len(pairs)} fragment-adding pairs"
    )
    assert conflicts_1 == 0, (
        f"Scenario 1: {conflicts_1} of {len(pairs)} fragment-adding pairs conflicted"
    )
    assert clean_1 == 190

    # ── Scenario 2: fragment-adding branch vs compaction → clean ─────────────

    _checkout_base()
    _run("checkout", "-b", "compact-a")
    compact_bundle_path = bundle_dir / "2026-09-01.bundle"
    # 1-record part: contains only frag-X.
    compact_1rec_bytes = (SEPARATOR + frag_x_content).encode("utf-8")
    compact_bundle_path.write_bytes(compact_1rec_bytes)
    frag_x_path.unlink()
    _run("add", ".")
    _run("commit", "-m", "compact 2026-09 (1-record)")
    compact_sha = _run("rev-parse", "HEAD")

    rc_2, _, paths_2 = _merge_tree(base_sha, fragment_shas[0], compact_sha)
    assert rc_2 == 0, (
        f"Scenario 2: fragment-adding vs compaction conflicted "
        f"(rc={rc_2}, paths={paths_2})"
    )

    # Build the edit-sha used by Scenario 3 (and documented end-to-end in
    # test_one_record_bundle_edit_caught_by_validator for Scenario 3a).
    _checkout_base()
    _run("checkout", "-b", "edit-x")
    frag_x_path.write_text(
        frag_x_content.replace("feature X", "feature X — updated"),
        encoding="utf-8",
    )
    _run("add", ".")
    _run("commit", "-m", "edit fragment X body")
    edit_sha = _run("rev-parse", "HEAD")

    # ── Scenario 3: body edit vs 3-record compaction → modify/delete conflict ─
    # A bundle with three records drops below git's rename-similarity threshold
    # so git treats the delete as a true delete, not a rename.

    _checkout_base()
    _run("checkout", "-b", "compact-3rec")
    pad1 = (
        "## Released\n\n### core 3.0.2 — 2026-09-03\n- pad 1\n"
        "<!-- eeeeeeee-eeee-4eee-8eee-eeeeeeeeeeee -->\n"
    )
    pad2 = (
        "## Released\n\n### core 3.0.3 — 2026-09-04\n- pad 2\n"
        "<!-- ffffffff-ffff-4fff-8fff-ffffffffffff -->\n"
    )
    compact_bundle_path.write_text(
        SEPARATOR + frag_x_content + SEPARATOR + pad1 + SEPARATOR + pad2,
        encoding="utf-8",
    )
    frag_x_path.unlink()
    _run("add", ".")
    _run("commit", "-m", "compact 2026-09 (3-record)")
    compact_3rec_sha = _run("rev-parse", "HEAD")

    rc_3, _, paths_3 = _merge_tree(base_sha, edit_sha, compact_3rec_sha)
    assert rc_3 == 1, (
        f"Scenario 3: body-edit vs 3-record compaction did not produce a conflict "
        f"(rc={rc_3}, paths={paths_3})"
    )

    # ── Scenario 4: two compactions of the same month → conflict ─────────────
    # Both branches compact frag-X into 2026-09-01.bundle but include different
    # padding records so the two bundles are distinct and cannot be resolved by
    # a textual 3-way merge.  Three-record bundles also fall below git's
    # rename-similarity threshold so git treats each as an independent ADD (not
    # a rename of frag-X), producing a true add/add conflict.

    pad3 = (
        "## Released\n\n### core 3.0.4 — 2026-09-05\n- pad 3\n"
        "<!-- gggggggg-gggg-4ggg-8ggg-gggggggggggg -->\n"
    )
    pad4 = (
        "## Released\n\n### core 3.0.5 — 2026-09-06\n- pad 4\n"
        "<!-- hhhhhhhh-hhhh-4hhh-8hhh-hhhhhhhhhhhh -->\n"
    )

    _checkout_base()
    _run("checkout", "-b", "compact-4a")
    compact_bundle_path.write_text(
        SEPARATOR + frag_x_content + SEPARATOR + pad1 + SEPARATOR + pad2,
        encoding="utf-8",
    )
    frag_x_path.unlink()
    _run("add", ".")
    _run("commit", "-m", "compact 2026-09 (4a: frag-X+pad1+pad2)")
    compact_4a_sha = _run("rev-parse", "HEAD")

    _checkout_base()
    _run("checkout", "-b", "compact-4b")
    compact_bundle_path.write_text(
        SEPARATOR + frag_x_content + SEPARATOR + pad3 + SEPARATOR + pad4,
        encoding="utf-8",
    )
    frag_x_path.unlink()
    _run("add", ".")
    _run("commit", "-m", "compact 2026-09 (4b: frag-X+pad3+pad4)")
    compact_4b_sha = _run("rev-parse", "HEAD")

    rc_4, _, paths_4 = _merge_tree(base_sha, compact_4a_sha, compact_4b_sha)
    assert rc_4 == 1, (
        f"Scenario 4: two concurrent compactions did not conflict "
        f"(rc={rc_4}, paths={paths_4})"
    )


# ── AC-B9 Scenario 3a: validator catches rename-merged bundle edit ────────────


def test_one_record_bundle_edit_caught_by_validator(tmp_path: Path) -> None:
    """AC-B9 Scenario 3a: validate_changelog_cross_form_identity catches a body
    edit that git silently applied to a one-record bundle via rename detection.

    Setup (throwaway git repo in ``tmp_path``):
    - Base commit: one released fragment (frag-X) plus a bystander (frag-W
      with an unreleased version, keeping ``changelog.d/`` non-empty after
      compaction).
    - ``compact`` branch: ``compact_month`` bundles frag-X into a one-record
      part and deletes the fragment.  Committed.  ``refs/remotes/origin/main``
      is set to this commit so the validator has a merge base.
    - ``edit-body`` branch: the fragment body is modified.  Committed.
    - Merge: ``git merge-tree`` merges edit-body into the compact commit and
      the result is materialised as a real merge commit (via ``commit-tree``).
      The merge is expected to be clean (rc=0) because git's rename detection
      treats the compaction as a rename and applies the edit to the bundle.
    - Validator: ``validate_changelog_cross_form_identity`` compares the
      bundle bytes at the merge-base (compact commit) against the bundle bytes
      at HEAD (merged result) and raises ``FragmentValidationError`` naming the
      record id and "bundled record bytes changed".
    """
    import os
    import subprocess

    _GIT_REDIRECTS = (
        "GIT_DIR",
        "GIT_WORK_TREE",
        "GIT_INDEX_FILE",
        "GIT_OBJECT_DIRECTORY",
        "GIT_ALTERNATE_OBJECT_DIRECTORIES",
    )
    env: dict[str, str] = {
        k: v for k, v in os.environ.items() if k not in _GIT_REDIRECTS
    }
    env.update(
        {
            "GIT_AUTHOR_NAME": "changelog-b9-test",
            "GIT_AUTHOR_EMAIL": "test@invalid",
            "GIT_COMMITTER_NAME": "changelog-b9-test",
            "GIT_COMMITTER_EMAIL": "test@invalid",
            "GIT_AUTHOR_DATE": "2026-01-01T00:00:00+00:00",
            "GIT_COMMITTER_DATE": "2026-01-01T00:00:00+00:00",
        }
    )

    def _run(*args: str) -> str:
        result = subprocess.run(
            ["git", "-C", str(tmp_path), *args],
            capture_output=True,
            text=True,
            env=env,
        )
        if result.returncode != 0:
            raise RuntimeError(f"git {' '.join(args)}: {result.stderr.strip()}")
        return result.stdout.strip()

    # ── Initialise throwaway repo ─────────────────────────────────────────────
    _run("init")
    _run("config", "user.email", "test@invalid")
    _run("config", "user.name", "changelog-b9-test")

    bundle_dir = tmp_path / "changelog.months"
    bundle_dir.mkdir()
    frag_dir = tmp_path / "changelog.d"
    frag_dir.mkdir()
    retraction_path = tmp_path / "changelog-retractions.toml"

    # ── Fragments ─────────────────────────────────────────────────────────────
    # frag-X: released (version 3.0.0), to be compacted.
    frag_x_id = "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb"
    frag_x_anchor = changelog._compose_fragment_anchor(
        [{"name": "core", "version": "3.0.0"}], "2026-09-01", frag_x_id
    )
    frag_x_text = _fragment_text(
        fragment_id=frag_x_id, anchor=frag_x_anchor, date="2026-09-01"
    )
    frag_x_path = frag_dir / f"{frag_x_id}.md"
    frag_x_path.write_text(frag_x_text, encoding="utf-8")

    # frag-W: bystander with version 3.0.1 (not in released_versions).
    # Keeps changelog.d/ non-empty after frag-X is deleted, preventing git's
    # directory rename heuristic from firing on the containing folder.
    frag_w_id = "dddddddd-dddd-4ddd-8ddd-dddddddddddd"
    frag_w_anchor = changelog._compose_fragment_anchor(
        [{"name": "core", "version": "3.0.1"}], "2026-09-02", frag_w_id
    )
    frag_w_text = _fragment_text(
        fragment_id=frag_w_id,
        anchor=frag_w_anchor,
        date="2026-09-02",
        packages='[[packages]]\nname = "core"\nversion = "3.0.1"',
    )
    (frag_dir / f"{frag_w_id}.md").write_text(frag_w_text, encoding="utf-8")

    # ── Base commit ───────────────────────────────────────────────────────────
    _run("add", ".")
    _run("commit", "-m", "base")
    base_sha = _run("rev-parse", "HEAD")

    # Set origin/main to base temporarily so collect_validated_fragments
    # can resolve the merge-base context when compact_month calls it.
    _run("update-ref", "refs/remotes/origin/main", base_sha)

    # ── Compact branch ────────────────────────────────────────────────────────
    _run("checkout", "-b", "compact")
    created, deleted = changelog.compact_month(
        "2026-09",
        fragment_dir=frag_dir,
        bundle_dir=bundle_dir,
        released_versions={"core": {"3.0.0"}},
    )
    assert len(created) == 1, f"compact_month should create 1 bundle part; got {created}"
    assert len(deleted) == 1, f"compact_month should delete 1 fragment; got {deleted}"
    _run("add", ".")
    _run("commit", "-m", "compact 2026-09")
    compact_sha = _run("rev-parse", "HEAD")

    # Update origin/main to the compact commit: this is the "merge base" the
    # validator will compare the merged bundle against.
    _run("update-ref", "refs/remotes/origin/main", compact_sha)

    # ── Edit-body branch ──────────────────────────────────────────────────────
    _run("checkout", "--detach", base_sha)
    _run("checkout", "-b", "edit-body")
    # Restore frag-X (checkout restores it from base_sha).
    edited_frag_x_text = frag_x_text.replace(
        "- Adds per-update changelog sources.",
        "- Adds per-update changelog sources.\n- EDITED",
    )
    frag_x_path.write_text(edited_frag_x_text, encoding="utf-8")
    _run("add", ".")
    _run("commit", "-m", "body edit to frag-X")
    edit_sha = _run("rev-parse", "HEAD")

    # ── Materialise the merge commit ──────────────────────────────────────────
    # git merge-tree (default rename detection) should merge cleanly (rc=0):
    # the compaction looks like a rename of frag-X into the bundle, and git
    # applies the body edit to the new bundle location.
    mt = subprocess.run(
        [
            "git",
            "-C",
            str(tmp_path),
            "merge-tree",
            "--write-tree",
            "--name-only",
            f"--merge-base={base_sha}",
            edit_sha,
            compact_sha,
        ],
        capture_output=True,
        text=True,
        env=env,
    )
    assert mt.returncode == 0, (
        f"Scenario 3a: expected clean rename-merge (rc=0) but got rc={mt.returncode}.\n"
        f"stdout: {mt.stdout!r}\nstderr: {mt.stderr!r}"
    )
    merged_tree_sha = next(ln for ln in mt.stdout.splitlines() if ln)

    # Create a real merge commit so git history contains the merge-base.
    merge_commit = _run(
        "commit-tree", merged_tree_sha,
        "-p", edit_sha,
        "-p", compact_sha,
        "-m", "merge edit-body into compact (rename-merged)",
    )

    # Check out the merge commit to update the working tree.
    _run("checkout", "-b", "on-merged", merge_commit)

    # ── Validator assertion ───────────────────────────────────────────────────
    # HEAD = merge_commit (parents: edit_sha, compact_sha).
    # origin/main = compact_sha.
    # git merge-base origin/main HEAD = compact_sha.
    # The validator compares the bundle bytes at compact_sha (original) against
    # the bundle bytes at HEAD (edited via rename-merge) and must raise.
    try:
        changelog.validate_changelog_cross_form_identity(
            fragment_dir=frag_dir,
            bundle_dir=bundle_dir,
            retraction_path=retraction_path,
        )
    except changelog.FragmentValidationError as exc:
        msg = str(exc)
        assert frag_x_id in msg, (
            f"FragmentValidationError does not name the record id {frag_x_id!r}: "
            f"{msg!r}"
        )
        assert "bundled record bytes changed" in msg, (
            f"FragmentValidationError does not say 'bundled record bytes changed': "
            f"{msg!r}"
        )
    else:
        raise AssertionError(
            "validate_changelog_cross_form_identity did not refuse the "
            "rename-merged bundle (edit landed without detection)"
        )


# ── AC-B10: pages.yml triggers ───────────────────────────────────────────────


def test_pages_yml_triggers_on_bundle_paths() -> None:
    """AC-B10: pages.yml triggers on changelog.months and changelog-retractions.toml."""
    pages_yml = (
        Path(__file__).resolve().parent.parent / ".github/workflows/pages.yml"
    )
    text = pages_yml.read_text(encoding="utf-8")
    assert "changelog.months" in text, (
        "pages.yml does not trigger on docs/product/changelog.months/"
    )
    assert "changelog-retractions.toml" in text, (
        "pages.yml does not trigger on docs/product/changelog-retractions.toml"
    )


# ── inventory parity: compact and build classify the same fragments ───────────


def test_compact_and_collect_agree_on_released_fragments(tmp_path: Path) -> None:
    """AC-B6: compact uses the same released-inventory predicate as collect."""
    frag_dir = tmp_path / "changelog.d"
    frag_dir.mkdir()
    bundle_dir = tmp_path / "changelog.months"
    bundle_dir.mkdir()
    # Write two fragments: one released, one pending.
    released_id = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
    released_anchor = "core300--2026-10-01-aaaaaaaaaaaaaaaaa4aaa8aaaaaaaaaaaaaaaa"[:64]
    # Recompute proper anchor.
    released_anchor = changelog._compose_fragment_anchor(
        [{"name": "core", "version": "3.0.0"}], "2026-10-01", released_id
    )
    released_text = _fragment_text(
        fragment_id=released_id,
        anchor=released_anchor,
        date="2026-10-01",
    )
    (frag_dir / f"{released_id}.md").write_text(released_text, encoding="utf-8")

    pending_id = "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb"
    pending_anchor = changelog._compose_fragment_anchor(
        [{"name": "core", "version": "4.0.0"}], "2026-10-02", pending_id
    )
    pending_text = _fragment_text(
        fragment_id=pending_id,
        anchor=pending_anchor,
        date="2026-10-02",
        packages='[[packages]]\nname = "core"\nversion = "4.0.0"',
    )
    (frag_dir / f"{pending_id}.md").write_text(pending_text, encoding="utf-8")

    released_versions = {"core": {"3.0.0"}}
    inventory = changelog._normalize_released_versions(released_versions)
    loose_frags = changelog.collect_validated_fragments(frag_dir)
    released_by_collect = {
        f.id for f in loose_frags
        if changelog._fragment_in_released_inventory(f, inventory)
    }
    created, _ = changelog.compact_month(
        "2026-10",
        fragment_dir=frag_dir,
        bundle_dir=bundle_dir,
        released_versions=released_versions,
    )
    # compact should have bundled only the released fragment.
    if created:
        part_bytes = created[0].read_bytes()
        bundled_records = changelog._parse_bundle_part(created[0], part_bytes)
        bundled_ids = {f.id for _, f in bundled_records}
        assert bundled_ids == released_by_collect
