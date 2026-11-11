"""Bundle edge cases and acceptance fixtures added through review (AC-B2 to AC-B8a)."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from test_changelog import (
    _HISTORICAL_CHANGELOG,
    _OS,
    _SCRIPT,
    VALID_ID,
    _fragment_text,
    _git,
    _run_render,
    changelog,
)
from test_changelog_bundles import VALID_ANCHOR_B, VALID_ID_B, _bundle_fragment_text

# =============================================================================
# Review-finding fixes: A-G (sustained, adjudication 2026-10-11)
# =============================================================================

# ---------------------------------------------------------------------------
# Fix F — AC-B2 trailing bytes after the last record
# ---------------------------------------------------------------------------


def test_bundle_part_refused_if_trailing_bytes(tmp_path: Path) -> None:
    """Fix F / AC-B2: trailing bytes after the last record are refused.

    A bundle part whose content is SEP + valid_record + extra_LF must be
    refused with a diagnostic naming the 'trailing bytes' invariant.
    """
    bundle_dir = tmp_path / "changelog.months"
    bundle_dir.mkdir()
    part = bundle_dir / "2026-10-00.bundle"
    rec = _bundle_fragment_text()
    # Add one extra LF after the valid record — this is the 'trailing bytes' case.
    content = changelog.BUNDLE_SEPARATOR_BYTES + rec.encode("utf-8") + b"\n"
    part.write_bytes(content)
    try:
        changelog._parse_bundle_part(part, content)
    except changelog.FragmentValidationError as exc:
        msg = str(exc).lower()
        assert "trailing" in msg or "separator" in msg, (
            f"error does not name trailing bytes: {exc}"
        )
    else:
        raise AssertionError(
            "bundle part with trailing bytes was accepted; expected FragmentValidationError"
        )


# ---------------------------------------------------------------------------
# Fix C — git merge-base non-zero exit handling
# ---------------------------------------------------------------------------


def test_validate_cross_form_raises_on_merge_base_exit_128(tmp_path: Path) -> None:
    """Fix C: git merge-base exit 128 raises FragmentValidationError (not a skip).

    Exit 1 + 'no merge base' is the only allowed skip; any other non-zero exit
    (e.g., 128 for a repository error) must refuse fail-closed.
    """
    frag_dir = tmp_path / "changelog.d"
    frag_dir.mkdir()
    bundle_dir = tmp_path / "changelog.months"
    retraction_path = tmp_path / "changelog-retractions.toml"

    _GitResult = changelog._GitResult

    def fake_git(cwd, *args):
        if args[0] == "rev-parse" and "--show-toplevel" in args:
            return _GitResult(0, str(tmp_path) + "\n", "")
        if args[0] == "merge-base":
            # Simulate a repository error (e.g., unresolvable remote ref).
            return _GitResult(128, "", "fatal: ambiguous argument 'origin/main'")
        return _GitResult(0, "", "")

    try:
        changelog.validate_changelog_cross_form_identity(
            fragment_dir=frag_dir,
            bundle_dir=bundle_dir,
            retraction_path=retraction_path,
            git_runner=fake_git,
        )
    except changelog.FragmentValidationError as exc:
        assert "128" in str(exc) or "merge-base" in str(exc).lower() or "fatal" in str(exc).lower(), (
            f"error does not describe the merge-base failure: {exc}"
        )
    else:
        raise AssertionError(
            "exit-128 from git merge-base was silently skipped; "
            "expected FragmentValidationError"
        )


# ---------------------------------------------------------------------------
# Fix D — malformed merge-base retraction TOML raises instead of pass
# ---------------------------------------------------------------------------


def test_validate_cross_form_raises_on_malformed_base_retraction_toml(
    tmp_path: Path, monkeypatch
) -> None:
    """Fix D: a malformed merge-base retraction list raises FragmentValidationError.

    When the merge-base blob for the retraction list is not valid UTF-8 TOML,
    the append-only check must fail closed rather than silently passing.
    """
    frag_dir = tmp_path / "changelog.d"
    frag_dir.mkdir()
    bundle_dir = tmp_path / "changelog.months"
    retraction_path = tmp_path / "changelog-retractions.toml"

    # Write a current retraction list that differs from the base (triggers the comparison).
    new_entry = '[[retraction]]\nid = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"\ncategory = "other"\n'
    retraction_path.write_text(new_entry, encoding="utf-8")

    # Compute a fake object id for the base retraction blob.
    import hashlib as _hashlib
    malformed_blob = b"\xff\xfe not valid utf-8 TOML"  # invalid UTF-8
    header = b"blob " + str(len(malformed_blob)).encode() + b"\0"
    base_retract_obj = _hashlib.sha1(header + malformed_blob, usedforsecurity=False).hexdigest()

    # Valid current retraction content differs from malformed base,
    # so the startswith check fails and we try to parse the base TOML.
    retract_rel = "changelog-retractions.toml"
    ls_tree_output = f"100644 blob {base_retract_obj}\t{retract_rel}\n"

    _GitResult = changelog._GitResult

    def fake_git(cwd, *args):
        if args[0] == "rev-parse" and "--show-toplevel" in args:
            return _GitResult(0, str(tmp_path) + "\n", "")
        if args[0] == "merge-base":
            return _GitResult(0, "deadbeef" * 5 + "\n", "")
        if args[0] == "rev-parse" and "--show-object-format" in args:
            return _GitResult(0, "sha1\n", "")
        if args[0] == "ls-tree":
            return _GitResult(0, ls_tree_output, "")
        return _GitResult(128, "", f"unexpected: {args}")

    def fake_bytes(repo, *args):
        if args[0] == "cat-file" and args[1] == "-s":
            return (0, str(len(malformed_blob)).encode() + b"\n", "")
        if args[0] == "cat-file" and args[1] == "blob":
            return (0, malformed_blob, "")
        return (128, b"", "unexpected")

    monkeypatch.setattr(changelog, "_git_runner_bytes", fake_bytes)

    try:
        changelog.validate_changelog_cross_form_identity(
            fragment_dir=frag_dir,
            bundle_dir=bundle_dir,
            retraction_path=retraction_path,
            git_runner=fake_git,
        )
    except changelog.FragmentValidationError as exc:
        msg = str(exc).lower()
        assert "toml" in msg or "utf" in msg or "malformed" in msg or "retraction" in msg, (
            f"error does not name the malformed TOML issue: {exc}"
        )
    else:
        raise AssertionError(
            "malformed merge-base retraction TOML was silently passed; "
            "expected FragmentValidationError"
        )


# ---------------------------------------------------------------------------
# Fix B — edited retraction entry is refused
# ---------------------------------------------------------------------------


def test_validate_cross_form_refuses_edited_retraction_entry(
    tmp_path: Path, monkeypatch
) -> None:
    """Fix B / AC-B4a: an edited retraction entry (same id, changed category) is refused.

    When a base entry's category is changed in the current list, validation
    must refuse by name rather than only checking id presence.
    """
    frag_dir = tmp_path / "changelog.d"
    frag_dir.mkdir()
    bundle_dir = tmp_path / "changelog.months"
    retraction_path = tmp_path / "changelog-retractions.toml"

    # Base retraction list: entry with category 'other'.
    base_content = (
        '[[retraction]]\n'
        'id = "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb"\n'
        'category = "other"\n'
    )
    # Current list: same id, different category → edited entry.
    current_content = (
        '[[retraction]]\n'
        'id = "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb"\n'
        'category = "credential"\n'
    )
    retraction_path.write_text(current_content, encoding="utf-8")

    import hashlib as _hashlib
    blob_data = base_content.encode("utf-8")
    header = b"blob " + str(len(blob_data)).encode() + b"\0"
    base_retract_obj = _hashlib.sha1(header + blob_data, usedforsecurity=False).hexdigest()

    # The current content doesn't start with the base (different category line),
    # so the startswith check fails and we fall into per-entry comparison.
    retract_rel = "changelog-retractions.toml"
    ls_tree_output = f"100644 blob {base_retract_obj}\t{retract_rel}\n"

    _GitResult = changelog._GitResult

    def fake_git(cwd, *args):
        if args[0] == "rev-parse" and "--show-toplevel" in args:
            return _GitResult(0, str(tmp_path) + "\n", "")
        if args[0] == "merge-base":
            return _GitResult(0, "badbadba" * 5 + "\n", "")
        if args[0] == "rev-parse" and "--show-object-format" in args:
            return _GitResult(0, "sha1\n", "")
        if args[0] == "ls-tree":
            return _GitResult(0, ls_tree_output, "")
        return _GitResult(128, "", f"unexpected: {args}")

    def fake_bytes(repo, *args):
        if args[0] == "cat-file" and args[1] == "-s":
            return (0, str(len(blob_data)).encode() + b"\n", "")
        if args[0] == "cat-file" and args[1] == "blob":
            return (0, blob_data, "")
        return (128, b"", "unexpected")

    monkeypatch.setattr(changelog, "_git_runner_bytes", fake_bytes)

    try:
        changelog.validate_changelog_cross_form_identity(
            fragment_dir=frag_dir,
            bundle_dir=bundle_dir,
            retraction_path=retraction_path,
            git_runner=fake_git,
        )
    except changelog.FragmentValidationError as exc:
        assert "edited" in str(exc).lower() or "changed" in str(exc).lower() or "bbbbbbbb" in str(exc), (
            f"error does not name the edited entry: {exc}"
        )
    else:
        raise AssertionError(
            "edited retraction entry (changed category) was accepted; "
            "expected FragmentValidationError"
        )


def test_validate_cross_form_refuses_deleted_retraction_list(
    tmp_path: Path, monkeypatch
) -> None:
    """AC-B4a: deleting a retraction list the merge base holds is refused.

    Without the list, a retracted id has nothing to collide with, so the
    record could be re-published.
    """
    frag_dir = tmp_path / "changelog.d"
    frag_dir.mkdir()
    bundle_dir = tmp_path / "changelog.months"
    retraction_path = tmp_path / "changelog-retractions.toml"
    base_content = (
        '[[retraction]]\n'
        'id = "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb"\n'
        'category = "credential"\n'
    )
    blob_data = base_content.encode("utf-8")
    header = b"blob " + str(len(blob_data)).encode() + b"\0"
    base_retract_obj = __import__("hashlib").sha1(header + blob_data, usedforsecurity=False).hexdigest()
    ls_tree_output = f"100644 blob {base_retract_obj}\tchangelog-retractions.toml\n"
    _GitResult = changelog._GitResult

    def fake_git(cwd, *args):
        if args[0] == "rev-parse" and "--show-toplevel" in args:
            return _GitResult(0, str(tmp_path) + "\n", "")
        if args[0] == "merge-base":
            return _GitResult(0, "badbadba" * 5 + "\n", "")
        if args[0] == "rev-parse" and "--show-object-format" in args:
            return _GitResult(0, "sha1\n", "")
        if args[0] == "ls-tree":
            return _GitResult(0, ls_tree_output, "")
        return _GitResult(128, "", f"unexpected: {args}")

    def fake_bytes(repo, *args):
        if args[0] == "cat-file" and args[1] == "-s":
            return (0, str(len(blob_data)).encode() + b"\n", "")
        if args[0] == "cat-file" and args[1] == "blob":
            return (0, blob_data, "")
        return (128, b"", "unexpected")

    monkeypatch.setattr(changelog, "_git_runner_bytes", fake_bytes)

    try:
        changelog.validate_changelog_cross_form_identity(
            fragment_dir=frag_dir,
            bundle_dir=bundle_dir,
            retraction_path=retraction_path,
            git_runner=fake_git,
        )
    except changelog.FragmentValidationError as exc:
        assert "present while the merge base lists retractions" in str(exc), (
            f"refused for the wrong reason: {exc}"
        )
    else:
        raise AssertionError("a deleted retraction list was accepted")


# ---------------------------------------------------------------------------
# Fix A — AC-B4 merge-base record set reconstruction (four cases)
# ---------------------------------------------------------------------------

# ── Helper for validate_changelog_cross_form_identity tests ──────────────────

def _fake_validate_git_runner(repo_path: Path, merge_base: str, ls_tree_lines: list):
    """Return a fake git_runner for cross-form identity tests."""
    _GitResult = changelog._GitResult
    ls_output = "\n".join(ls_tree_lines)

    def fake_git(cwd, *args):
        if args[0] == "rev-parse" and "--show-toplevel" in args:
            return _GitResult(0, str(repo_path) + "\n", "")
        if args[0] == "merge-base":
            return _GitResult(0, merge_base + "\n", "")
        if args[0] == "rev-parse" and "--show-object-format" in args:
            return _GitResult(0, "sha1\n", "")
        if args[0] == "ls-tree":
            return _GitResult(0, ls_output + "\n" if ls_output else "", "")
        return _GitResult(128, "", f"unexpected git call: {' '.join(str(a) for a in args)}")

    return fake_git


def _sha1_obj_id(data: bytes) -> str:
    """Compute the git SHA-1 blob object id for raw bytes."""
    import hashlib as _hashlib
    header = b"blob " + str(len(data)).encode() + b"\0"
    return _hashlib.sha1(header + data, usedforsecurity=False).hexdigest()


# ── Test A-1: new id added directly to a part ────────────────────────────────

def test_validate_cross_form_refuses_new_id_added_to_part(tmp_path: Path) -> None:
    """Fix A / AC-B4: a new id added directly to a bundle part is refused.

    The merge base has no records anywhere. The current state has a bundle
    part containing a record whose id was not at the merge base as a loose
    fragment or a bundled record — so the id was authored directly into the
    part, bypassing the loose-fragment authoring step.
    """
    frag_dir = tmp_path / "changelog.d"
    frag_dir.mkdir()
    bundle_dir = tmp_path / "changelog.months"
    bundle_dir.mkdir()
    retraction_path = tmp_path / "changelog-retractions.toml"

    # Write a bundle part with a record whose id has no merge-base presence.
    brand_new_id = "cccccccc-cccc-4ccc-8ccc-cccccccccccc"
    brand_new_anchor = changelog._compose_fragment_anchor(
        [{"name": "core", "version": "3.0.0"}], "2026-10-01", brand_new_id
    )
    rec = _bundle_fragment_text(
        fragment_id=brand_new_id, anchor=brand_new_anchor, date="2026-10-01"
    )
    part_content = changelog.BUNDLE_SEPARATOR_BYTES + rec.encode("utf-8")
    (bundle_dir / "2026-10-00.bundle").write_bytes(part_content)

    # Merge-base ls-tree: empty — no fragments or bundle parts at base.
    fake_git = _fake_validate_git_runner(tmp_path, "abc1234" * 5, [])

    try:
        changelog.validate_changelog_cross_form_identity(
            fragment_dir=frag_dir,
            bundle_dir=bundle_dir,
            retraction_path=retraction_path,
            git_runner=fake_git,
        )
    except changelog.FragmentValidationError as exc:
        msg = str(exc).lower()
        assert brand_new_id in str(exc) or "new id" in msg or "directly" in msg, (
            f"error does not name the new-id violation: {exc}"
        )
    else:
        raise AssertionError(
            "new id added directly to a bundle part was accepted; "
            "expected FragmentValidationError"
        )


# ── Test A-2: removed months directory ───────────────────────────────────────

def test_validate_cross_form_refuses_removed_months_directory(
    tmp_path: Path, monkeypatch
) -> None:
    """Fix A / AC-B4: removing the months directory drops all bundled records.

    The merge base has a bundle part. The current state has no months directory.
    Validation must refuse because the bundled ids are absent from current forms.
    """
    frag_dir = tmp_path / "changelog.d"
    frag_dir.mkdir()
    bundle_dir = tmp_path / "changelog.months"
    # Do NOT create bundle_dir — simulates a removed directory.
    retraction_path = tmp_path / "changelog-retractions.toml"

    # Build the merge-base bundle part content.
    base_id = "dddddddd-dddd-4ddd-8ddd-dddddddddddd"
    base_anchor = changelog._compose_fragment_anchor(
        [{"name": "core", "version": "3.0.0"}], "2026-10-01", base_id
    )
    rec = _bundle_fragment_text(fragment_id=base_id, anchor=base_anchor, date="2026-10-01")
    base_part_bytes = changelog.BUNDLE_SEPARATOR_BYTES + rec.encode("utf-8")
    base_obj = _sha1_obj_id(base_part_bytes)

    bundle_rel = "changelog.months"
    part_rel = f"{bundle_rel}/2026-10-00.bundle"
    ls_lines = [f"100644 blob {base_obj}\t{part_rel}"]

    fake_git = _fake_validate_git_runner(tmp_path, "def5678" * 5, ls_lines)

    def fake_bytes(repo, *args):
        if args[0] == "cat-file" and args[1] == "-s":
            return (0, str(len(base_part_bytes)).encode() + b"\n", "")
        if args[0] == "cat-file" and args[1] == "blob":
            return (0, base_part_bytes, "")
        return (128, b"", "unexpected")

    monkeypatch.setattr(changelog, "_git_runner_bytes", fake_bytes)

    try:
        changelog.validate_changelog_cross_form_identity(
            fragment_dir=frag_dir,
            bundle_dir=bundle_dir,
            retraction_path=retraction_path,
            git_runner=fake_git,
        )
    except changelog.FragmentValidationError as exc:
        msg = str(exc).lower()
        assert base_id in str(exc) or "bundled" in msg or "absent" in msg or "missing" in msg, (
            f"error does not name the missing bundled record: {exc}"
        )
    else:
        raise AssertionError(
            "removed months directory (bundled record absent) was accepted; "
            "expected FragmentValidationError"
        )


# ── Test A-3: part-adding change drops an unbundled merge-base fragment ───────

def test_validate_cross_form_refuses_part_adding_drops_fragment(tmp_path: Path) -> None:
    """Fix A / AC-B4: in a part-adding change, dropping a merge-base fragment is refused.

    The merge base has TWO loose fragments (A and B). The current change bundles
    fragment A into a new part (which is correctly in the merge-base ls-tree as
    a loose fragment so check 1 passes for it). Fragment B is gone from the
    current state entirely — not bundled, not retracted. The part-adding check
    must refuse because B is absent.
    """
    frag_dir = tmp_path / "changelog.d"
    frag_dir.mkdir()
    bundle_dir = tmp_path / "changelog.months"
    bundle_dir.mkdir()
    retraction_path = tmp_path / "changelog-retractions.toml"

    # Fragment A: was loose at merge base, now bundled into the new part.
    frag_a_id = "aaaabbbb-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
    frag_a_anchor = changelog._compose_fragment_anchor(
        [{"name": "core", "version": "3.0.0"}], "2026-10-01", frag_a_id
    )
    rec_a = _bundle_fragment_text(
        fragment_id=frag_a_id, anchor=frag_a_anchor, date="2026-10-01"
    )

    # Fragment B: was loose at merge base, now GONE (not bundled, not retracted).
    frag_b_id = "bbbbcccc-bbbb-4bbb-8bbb-bbbbbbbbbbbb"

    # Current state: new bundle part containing only fragment A.
    part_content = changelog.BUNDLE_SEPARATOR_BYTES + rec_a.encode("utf-8")
    (bundle_dir / "2026-10-00.bundle").write_bytes(part_content)

    # Merge-base ls-tree: both A and B were loose fragments.
    # Fragment A's id is in base_frag_ids → check 1 passes for it.
    # Fragment B's id is in base_frag_ids → check 3 fires (not in current forms).
    frag_a_obj = "a" * 40  # fake object id
    frag_b_obj = "b" * 40  # fake object id
    ls_lines = [
        f"100644 blob {frag_a_obj}\tchangelog.d/{frag_a_id}.md",
        f"100644 blob {frag_b_obj}\tchangelog.d/{frag_b_id}.md",
    ]

    fake_git = _fake_validate_git_runner(tmp_path, "fedc1234" * 5, ls_lines)

    try:
        changelog.validate_changelog_cross_form_identity(
            fragment_dir=frag_dir,
            bundle_dir=bundle_dir,
            retraction_path=retraction_path,
            git_runner=fake_git,
        )
    except changelog.FragmentValidationError as exc:
        msg = str(exc).lower()
        assert (
            frag_b_id in str(exc)
            or "drops" in msg
            or "part-adding" in msg
            or "unbundled" in msg
            or "missing" in msg
        ), f"error does not name the dropped fragment B: {exc}"
    else:
        raise AssertionError(
            "part-adding change that drops a merge-base fragment was accepted; "
            "expected FragmentValidationError"
        )


# ── Test A-4: merge-base bundled id missing (part deleted, not dir removed) ───

def test_validate_cross_form_refuses_missing_bundled_id_part_deleted(
    tmp_path: Path, monkeypatch
) -> None:
    """Fix A / AC-B4: a merge-base bundled id is refused when its part is deleted.

    The merge base has a bundle part. The current months directory exists but
    that specific part file has been deleted (not the whole directory). The
    bundled record's id is no longer in any current form.
    """
    frag_dir = tmp_path / "changelog.d"
    frag_dir.mkdir()
    bundle_dir = tmp_path / "changelog.months"
    bundle_dir.mkdir()
    retraction_path = tmp_path / "changelog-retractions.toml"

    # Build the merge-base part (now deleted from current state).
    gone_id = "12345678-1234-4234-8234-123456789012"
    gone_anchor = changelog._compose_fragment_anchor(
        [{"name": "core", "version": "3.0.0"}], "2026-09-01", gone_id
    )
    rec = _bundle_fragment_text(
        fragment_id=gone_id, anchor=gone_anchor, date="2026-09-01"
    )
    gone_part_bytes = changelog.BUNDLE_SEPARATOR_BYTES + rec.encode("utf-8")
    gone_obj = _sha1_obj_id(gone_part_bytes)

    # The part file does NOT exist in the current months directory.
    part_rel = "changelog.months/2026-09-00.bundle"
    ls_lines = [f"100644 blob {gone_obj}\t{part_rel}"]

    fake_git = _fake_validate_git_runner(tmp_path, "cafebabe" * 5, ls_lines)

    def fake_bytes(repo, *args):
        if args[0] == "cat-file" and args[1] == "-s":
            return (0, str(len(gone_part_bytes)).encode() + b"\n", "")
        if args[0] == "cat-file" and args[1] == "blob":
            return (0, gone_part_bytes, "")
        return (128, b"", "unexpected")

    monkeypatch.setattr(changelog, "_git_runner_bytes", fake_bytes)

    try:
        changelog.validate_changelog_cross_form_identity(
            fragment_dir=frag_dir,
            bundle_dir=bundle_dir,
            retraction_path=retraction_path,
            git_runner=fake_git,
        )
    except changelog.FragmentValidationError as exc:
        msg = str(exc).lower()
        assert gone_id in str(exc) or "bundled" in msg or "absent" in msg or "missing" in msg, (
            f"error does not name the missing bundled record: {exc}"
        )
    else:
        raise AssertionError(
            "deleted bundle part with unretracked record was accepted; "
            "expected FragmentValidationError"
        )


# ---------------------------------------------------------------------------
# Fix E — confinement: symlink in bundle directory refused during NN enumeration
# ---------------------------------------------------------------------------


def test_compact_refuses_symlink_in_bundle_dir_during_nn_enumeration(
    tmp_path: Path,
) -> None:
    """Fix E / AC-B3a: compact refuses a symlink in the bundle directory.

    When enumerating existing NN values to determine the next part number,
    compact_month must refuse symlinks in the bundle directory via the blessed
    confined helper rather than using iterdir() which would follow them.
    """
    frag_dir = tmp_path / "changelog.d"
    frag_dir.mkdir()
    bundle_dir = tmp_path / "changelog.months"
    bundle_dir.mkdir()

    # Write a real fragment to compact.
    frag_id = "abcdef01-0001-4001-8001-000000000001"
    anchor = changelog._compose_fragment_anchor(
        [{"name": "core", "version": "3.0.0"}], "2026-11-01", frag_id
    )
    text = _fragment_text(fragment_id=frag_id, anchor=anchor, date="2026-11-01")
    (frag_dir / f"{frag_id}.md").write_text(text, encoding="utf-8")

    # Put a symlink in the bundle directory with a valid bundle name.
    real_target = tmp_path / "elsewhere.bundle"
    real_target.write_bytes(changelog.BUNDLE_SEPARATOR_BYTES + _bundle_fragment_text().encode())
    link = bundle_dir / "2026-11-00.bundle"
    link.symlink_to(real_target)

    # compact_month should refuse because the blessed helper rejects the symlink.
    try:
        changelog.compact_month(
            "2026-11",
            fragment_dir=frag_dir,
            bundle_dir=bundle_dir,
            released_versions={"core": {"3.0.0"}},
        )
    except (changelog.FragmentValidationError, Exception) as exc:
        # Accept any error: the confined helper raises UnsafeContentError which
        # compact_month wraps into FragmentValidationError, or it may propagate
        # the UnsafeContentError directly.
        error_text = str(exc).lower()
        assert (
            "confined" in error_text
            or "symlink" in error_text
            or "unsafe" in error_text
            or "link" in error_text
            or "regular" in error_text
        ), f"error does not name the confinement violation: {exc}"
    else:
        raise AssertionError(
            "compact_month accepted a symlink in the bundle directory "
            "during NN enumeration; expected a confinement error"
        )


# ---------------------------------------------------------------------------
# Fix B / QE-F3 — retract intermediate state: injected-failure fixture
# ---------------------------------------------------------------------------


def test_retract_intermediate_state_refused_by_validation(tmp_path: Path, monkeypatch) -> None:
    """Fix B / AC-B4a / QE-F3: intermediate state after part rewrite but before list append.

    Constructs the intermediate state manually (part rewritten without the
    matching list entry), asserts that validate_changelog_cross_form_identity
    refuses it as an unlisted removal, and that a subsequent retract_record
    call with the same id and category completes the retraction.
    """
    frag_dir = tmp_path / "changelog.d"
    frag_dir.mkdir()
    bundle_dir = tmp_path / "changelog.months"
    bundle_dir.mkdir()
    retraction_path = tmp_path / "changelog-retractions.toml"

    # Write a bundle part with two records: one to retract, one to keep.
    rec_id = VALID_ID_B
    rec_anchor = VALID_ANCHOR_B
    rec_text = _bundle_fragment_text(fragment_id=rec_id, anchor=rec_anchor, date="2026-10-01")

    keep_id = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
    keep_anchor = changelog._compose_fragment_anchor(
        [{"name": "core", "version": "3.0.0"}], "2026-10-02", keep_id
    )
    keep_text = _bundle_fragment_text(
        fragment_id=keep_id, anchor=keep_anchor, date="2026-10-02"
    )

    part_path = bundle_dir / "2026-10-00.bundle"
    # Sort in canonical order (date desc then id asc): rec_id date="2026-10-01" < keep_id date="2026-10-02"
    # canonical order: date descending → keep_id (2026-10-02) first, then rec_id (2026-10-01)
    original_content = (
        changelog.BUNDLE_SEPARATOR_BYTES + keep_text.encode("utf-8")
        + changelog.BUNDLE_SEPARATOR_BYTES + rec_text.encode("utf-8")
    )
    part_path.write_bytes(original_content)

    # Simulate intermediate state: part rewritten without rec_id, but NO list entry.
    new_part_content = changelog.BUNDLE_SEPARATOR_BYTES + keep_text.encode("utf-8")
    part_path.write_bytes(new_part_content)
    # The retraction list does NOT have rec_id yet — this is the "crashed between writes" state.

    # Build base state: the original part (with both records) was at merge base.
    orig_obj = _sha1_obj_id(original_content)
    part_rel = "changelog.months/2026-10-00.bundle"
    ls_lines = [f"100644 blob {orig_obj}\t{part_rel}"]

    _GitResult = changelog._GitResult

    def fake_git(cwd, *args):
        if args[0] == "rev-parse" and "--show-toplevel" in args:
            return _GitResult(0, str(tmp_path) + "\n", "")
        if args[0] == "merge-base":
            return _GitResult(0, "1234abcd" * 5 + "\n", "")
        if args[0] == "rev-parse" and "--show-object-format" in args:
            return _GitResult(0, "sha1\n", "")
        if args[0] == "ls-tree":
            return _GitResult(0, "\n".join(ls_lines) + "\n", "")
        return _GitResult(128, "", f"unexpected: {args}")

    # Monkeypatch _git_runner_bytes so blob reads return the original part content.
    def fake_bytes(repo, *args):
        if args[0] == "cat-file" and args[1] == "-s":
            return (0, str(len(original_content)).encode() + b"\n", "")
        if args[0] == "cat-file" and args[1] == "blob":
            return (0, original_content, "")
        return (128, b"", f"unexpected bytes call: {args}")

    monkeypatch.setattr(changelog, "_git_runner_bytes", fake_bytes)

    # Validation should refuse the intermediate state: rec_id removed but not listed.
    try:
        changelog.validate_changelog_cross_form_identity(
            fragment_dir=frag_dir,
            bundle_dir=bundle_dir,
            retraction_path=retraction_path,
            git_runner=fake_git,
        )
    except changelog.FragmentValidationError as exc:
        # Good — the intermediate state is correctly refused.
        assert rec_id in str(exc) or "removed" in str(exc).lower() or "retract" in str(exc).lower(), (
            f"error does not name the missing retraction: {exc}"
        )
    else:
        raise AssertionError(
            "intermediate state (part rewritten, list not yet appended) "
            "was accepted; expected FragmentValidationError"
        )

    # Now rerun retract_record to complete the retraction.
    changelog.retract_record(
        rec_id, "other",
        bundle_dir=bundle_dir,
        retraction_path=retraction_path,
    )

    # The retraction list should now have rec_id.
    import tomllib as _tomllib
    data = _tomllib.loads(retraction_path.read_text(encoding="utf-8"))
    listed_ids = {e["id"] for e in data.get("retraction", [])}
    assert rec_id in listed_ids, (
        f"retract_record rerun did not add {rec_id} to the list; got: {listed_ids}"
    )
    # The part should still have keep_id only.
    assert part_path.exists()
    remaining = changelog._parse_bundle_part(part_path, part_path.read_bytes())
    remaining_ids = {f.id for _, f in remaining}
    assert keep_id in remaining_ids and rec_id not in remaining_ids


# ---------------------------------------------------------------------------
# Fix G — compact injected-failure fixtures (QE-F2)
# ---------------------------------------------------------------------------


def test_compact_second_part_write_failure_rolls_back_first_part(
    tmp_path: Path, monkeypatch
) -> None:
    """J1 / AC-B6: a failure writing the second bundle part removes all created parts.

    Two fragments are forced into separate parts by patching MAX_BUNDLE_BYTES to
    exactly one record's size.  The first write_bundle_part call succeeds; the
    second raises.  After the exception:
    - compact_month propagates the failure (raises).
    - The first (already-created) part is removed from disk (pre-deletion cleanup).
    - Both original fragment files still exist (no data loss before deletion phase).
    """
    frag_dir = tmp_path / "changelog.d"
    frag_dir.mkdir()
    bundle_dir = tmp_path / "changelog.months"
    bundle_dir.mkdir()

    id1 = "c1000001-0001-4001-8001-100000000001"
    id2 = "c2000002-0002-4002-8002-200000000002"

    for fid in (id1, id2):
        anchor = changelog._compose_fragment_anchor(
            [{"name": "core", "version": "3.0.0"}], "2026-12-01", fid
        )
        text = _fragment_text(
            fragment_id=fid,
            anchor=anchor,
            date="2026-12-01",
            packages='[[packages]]\nname = "core"\nversion = "3.0.0"',
        )
        (frag_dir / f"{fid}.md").write_text(text, encoding="utf-8")

    # Measure the raw fragment bytes so the byte bound allows exactly one record per part.
    one_raw = (frag_dir / f"{id1}.md").read_bytes()
    one_record_size = len(changelog.BUNDLE_SEPARATOR_BYTES) + len(one_raw)
    monkeypatch.setattr(changelog, "MAX_BUNDLE_BYTES", one_record_size)

    # Fail on the second write_bundle_part call (first write succeeds, creating one part).
    call_count = [0]
    original_write = changelog.write_bundle_part

    def _failing_write(records, directory, part_name, raw_bytes_map=None):
        call_count[0] += 1
        if call_count[0] >= 2:
            raise RuntimeError("injected second-write failure")
        return original_write(records, directory, part_name, raw_bytes_map)

    monkeypatch.setattr(changelog, "write_bundle_part", _failing_write)

    raised = False
    try:
        changelog.compact_month(
            "2026-12",
            fragment_dir=frag_dir,
            bundle_dir=bundle_dir,
            released_versions={"core": {"3.0.0"}},
        )
    except RuntimeError:
        raised = True

    assert raised, "compact_month did not propagate the injected second-write failure"
    assert call_count[0] >= 2, (
        "write_bundle_part was not called a second time; the split did not produce two parts"
    )

    # Pre-deletion cleanup: the first created part must be gone.
    remaining_parts = list(bundle_dir.iterdir())
    assert not remaining_parts, (
        f"created parts were not removed after second-write failure: "
        f"{[p.name for p in remaining_parts]}"
    )

    # No data loss: both original fragment files must still exist.
    assert (frag_dir / f"{id1}.md").exists(), (
        "fragment 1 was deleted despite write failure"
    )
    assert (frag_dir / f"{id2}.md").exists(), (
        "fragment 2 was deleted despite write failure"
    )


def test_compact_deletion_failure_is_completed_by_rerun(
    tmp_path: Path, monkeypatch
) -> None:
    """J2 / AC-B6: a failure partway through deletion is finished by a rerun.

    The failed run leaves its part and every record present in at least one
    form, refuses visibly, and the rerun deletes the leftover fragment without
    bundling it a second time.
    """
    frag_dir = tmp_path / "changelog.d"
    frag_dir.mkdir()
    bundle_dir = tmp_path / "changelog.months"
    bundle_dir.mkdir()
    id1 = "d1000001-0001-4001-8001-100000000001"
    id2 = "d2000002-0002-4002-8002-200000000002"
    for fid in (id1, id2):
        anchor = changelog._compose_fragment_anchor(
            [{"name": "core", "version": "3.0.0"}], "2026-11-01", fid
        )
        (frag_dir / f"{fid}.md").write_text(
            _fragment_text(
                fragment_id=fid,
                anchor=anchor,
                date="2026-11-01",
                packages='[[packages]]\nname = "core"\nversion = "3.0.0"',
            ),
            encoding="utf-8",
        )
    inventory = {"core": {"3.0.0"}}
    original_unlink = Path.unlink

    def failing_unlink(self, *args, **kwargs):
        if self.name == f"{id2}.md":
            raise OSError("injected deletion failure")
        return original_unlink(self, *args, **kwargs)

    monkeypatch.setattr(Path, "unlink", failing_unlink)
    try:
        changelog.compact_month(
            "2026-11", fragment_dir=frag_dir, bundle_dir=bundle_dir,
            released_versions=inventory,
        )
    except changelog.FragmentValidationError as exc:
        assert "rerun compact" in str(exc), f"refused for the wrong reason: {exc}"
    else:
        raise AssertionError("a partial deletion was reported as success")
    monkeypatch.setattr(Path, "unlink", original_unlink)

    parts = sorted(p.name for p in bundle_dir.iterdir())
    assert len(parts) == 1, f"expected the one written part to remain: {parts}"
    bundled = {ff.id for _, _, _, ff in changelog._collect_bundle_records(
        bundle_dir, changelog._file_safety()
    )}
    assert bundled == {id1, id2}
    assert (frag_dir / f"{id2}.md").exists() and not (frag_dir / f"{id1}.md").exists()
    try:
        changelog.collect_changelog_records(fragment_dir=frag_dir, bundle_dir=bundle_dir)
    except changelog.FragmentValidationError as exc:
        assert "duplicate id" in str(exc).lower()
    else:
        raise AssertionError("the interrupted state was accepted despite a duplicate id")

    changelog.compact_month(
        "2026-11", fragment_dir=frag_dir, bundle_dir=bundle_dir,
        released_versions=inventory,
    )
    assert sorted(p.name for p in bundle_dir.iterdir()) == parts, (
        "the rerun wrote a new part instead of finishing the deletion"
    )
    assert not list(frag_dir.glob("*.md")), "a fragment of the month is still loose"
    loose, bundled_records = changelog.collect_changelog_records(
        fragment_dir=frag_dir, bundle_dir=bundle_dir
    )
    assert sorted(r.id for r in [*loose, *bundled_records]) == sorted([id1, id2])


def test_compact_rerun_refuses_a_retracted_id_in_the_interrupted_state(
    tmp_path: Path, monkeypatch
) -> None:
    """AC-B4a / AC-B6: rerun recovery applies the reader's retraction refusal.

    A record retracted while it sits in both forms after an interrupted
    compaction must make the rerun refuse, not report success while the
    retracted bytes stay in the part.
    """
    frag_dir = tmp_path / "changelog.d"
    frag_dir.mkdir()
    bundle_dir = tmp_path / "changelog.months"
    bundle_dir.mkdir()
    retraction_path = tmp_path / "changelog-retractions.toml"
    id1 = "d1000001-0001-4001-8001-100000000001"
    id2 = "d2000002-0002-4002-8002-200000000002"
    for fid in (id1, id2):
        anchor = changelog._compose_fragment_anchor(
            [{"name": "core", "version": "3.0.0"}], "2026-11-01", fid
        )
        (frag_dir / f"{fid}.md").write_text(
            _fragment_text(
                fragment_id=fid,
                anchor=anchor,
                date="2026-11-01",
                packages='[[packages]]\nname = "core"\nversion = "3.0.0"',
            ),
            encoding="utf-8",
        )
    inventory = {"core": {"3.0.0"}}
    original_unlink = Path.unlink

    def failing_unlink(self, *args, **kwargs):
        if self.name == f"{id2}.md":
            raise OSError("injected deletion failure")
        return original_unlink(self, *args, **kwargs)

    monkeypatch.setattr(Path, "unlink", failing_unlink)
    try:
        changelog.compact_month(
            "2026-11", fragment_dir=frag_dir, bundle_dir=bundle_dir,
            retraction_path=retraction_path, released_versions=inventory,
        )
    except changelog.FragmentValidationError:
        pass
    else:
        raise AssertionError("a partial deletion was reported as success")
    monkeypatch.setattr(Path, "unlink", original_unlink)
    assert (frag_dir / f"{id2}.md").exists(), "setup did not leave the interrupted state"

    retraction_path.write_text(
        f'[[retraction]]\nid = "{id2}"\ncategory = "credential"\n', encoding="utf-8"
    )
    try:
        changelog.compact_month(
            "2026-11", fragment_dir=frag_dir, bundle_dir=bundle_dir,
            retraction_path=retraction_path, released_versions=inventory,
        )
    except changelog.FragmentValidationError as exc:
        message = str(exc)
        assert "retracted id" in message and id2 in message, message
    else:
        raise AssertionError("the rerun accepted a retracted id present in both forms")
    assert (frag_dir / f"{id2}.md").exists(), "the refused rerun still deleted the fragment"


def test_compact_rerun_counts_a_record_in_both_forms_once_toward_the_cap(
    tmp_path: Path, monkeypatch
) -> None:
    """AC-B6 / AC-B7: a rerun at exactly the cap's unique count is not refused.

    Mid-compaction one record sits loose and bundled; counting it twice would
    refuse the very rerun AC-B6 requires to finish the move.
    """
    frag_dir = tmp_path / "changelog.d"
    frag_dir.mkdir()
    bundle_dir = tmp_path / "changelog.months"
    bundle_dir.mkdir()
    id1 = "d1000001-0001-4001-8001-100000000001"
    id2 = "d2000002-0002-4002-8002-200000000002"
    for fid in (id1, id2):
        anchor = changelog._compose_fragment_anchor(
            [{"name": "core", "version": "3.0.0"}], "2026-11-01", fid
        )
        (frag_dir / f"{fid}.md").write_text(
            _fragment_text(
                fragment_id=fid,
                anchor=anchor,
                date="2026-11-01",
                packages='[[packages]]\nname = "core"\nversion = "3.0.0"',
            ),
            encoding="utf-8",
        )
    inventory = {"core": {"3.0.0"}}
    original_unlink = Path.unlink

    def failing_unlink(self, *args, **kwargs):
        if self.name == f"{id2}.md":
            raise OSError("injected deletion failure")
        return original_unlink(self, *args, **kwargs)

    monkeypatch.setattr(Path, "unlink", failing_unlink)
    try:
        changelog.compact_month(
            "2026-11", fragment_dir=frag_dir, bundle_dir=bundle_dir,
            released_versions=inventory,
        )
    except changelog.FragmentValidationError:
        pass
    else:
        raise AssertionError("a partial deletion was reported as success")
    monkeypatch.setattr(Path, "unlink", original_unlink)
    assert (frag_dir / f"{id2}.md").exists(), "setup did not leave the interrupted state"

    # Two unique records, three physical copies: the cap admits exactly two.
    monkeypatch.setattr(changelog, "MAX_RECORD_COUNT", 2)
    changelog.compact_month(
        "2026-11", fragment_dir=frag_dir, bundle_dir=bundle_dir,
        released_versions=inventory,
    )
    assert not (frag_dir / f"{id2}.md").exists(), "the rerun did not finish the move"

# ---------------------------------------------------------------------------
# Fix QE-F6 — zero blob reads for unchanged bundle in cross-form identity
# ---------------------------------------------------------------------------


def test_validate_cross_form_reads_zero_blobs_for_unchanged_bundle(tmp_path: Path) -> None:
    """QE-F6 / ADR-0143 confirmation: unchanged bundle reads no blobs.

    When the merge-base object id of a bundle part matches the current computed
    object id, validate_changelog_cross_form_identity skips the git show call.
    """
    frag_dir = tmp_path / "changelog.d"
    frag_dir.mkdir()
    bundle_dir = tmp_path / "changelog.months"
    bundle_dir.mkdir()
    retraction_path = tmp_path / "changelog-retractions.toml"

    # Write a bundle part.
    rec = _bundle_fragment_text()
    part_content = changelog.BUNDLE_SEPARATOR_BYTES + rec.encode("utf-8")
    part_path = bundle_dir / "2026-10-00.bundle"
    part_path.write_bytes(part_content)

    # Compute the actual SHA-1 object id for this part.
    actual_obj = _sha1_obj_id(part_content)

    # The base tree reports the SAME object id → no blob read should occur.
    bundle_rel = "changelog.months/2026-10-00.bundle"
    ls_lines = [f"100644 blob {actual_obj}\t{bundle_rel}"]

    fake_git = _fake_validate_git_runner(tmp_path, "00abcdef" * 5, ls_lines)

    blob_read_calls: list[str] = []

    def counting_bytes(repo, *args):
        if args[0] == "cat-file" and args[1] == "blob":
            blob_read_calls.append(str(args))
        # Delegate to the captured original, never to this patched name.
        return original(repo, *args)

    # Monkeypatch is NOT available here (no monkeypatch fixture), so patch manually.
    original = changelog._git_runner_bytes
    changelog._git_runner_bytes = counting_bytes
    try:
        changelog.validate_changelog_cross_form_identity(
            fragment_dir=frag_dir,
            bundle_dir=bundle_dir,
            retraction_path=retraction_path,
            git_runner=fake_git,
        )
    finally:
        changelog._git_runner_bytes = original

    assert blob_read_calls == [], (
        f"expected 0 blob reads for unchanged bundle, got {len(blob_read_calls)}: "
        f"{blob_read_calls}"
    )


# ---------------------------------------------------------------------------
# AC-B4a: a retracted id may never reappear, and a failed retract lists nothing
# ---------------------------------------------------------------------------


def _write_released_fragment(frag_dir: Path, fragment_id: str, day: str) -> Path:
    """Write one valid released core 3.0.0 fragment and return its path."""
    anchor = changelog._compose_fragment_anchor(
        [{"name": "core", "version": "3.0.0"}], day, fragment_id
    )
    path = frag_dir / f"{fragment_id}.md"
    path.write_text(
        _fragment_text(
            fragment_id=fragment_id,
            anchor=anchor,
            date=day,
            packages='[[packages]]\nname = "core"\nversion = "3.0.0"',
        ),
        encoding="utf-8",
    )
    return path


def _retraction_list_text(record_id: str) -> str:
    """Return a one-entry retraction list naming record_id."""
    return f'[[retraction]]\nid = "{record_id}"\ncategory = "credential"\n'


def test_listed_retracted_id_present_as_fragment_is_refused(tmp_path: Path) -> None:
    """AC-B4a: a retracted id re-added as a loose fragment is refused, not hidden."""
    frag_dir = tmp_path / "changelog.d"
    frag_dir.mkdir()
    bundle_dir = tmp_path / "changelog.months"
    bundle_dir.mkdir()
    record_id = "e1000001-0001-4001-8001-100000000001"
    _write_released_fragment(frag_dir, record_id, "2026-11-01")
    retraction_path = tmp_path / "changelog-retractions.toml"
    retraction_path.write_text(_retraction_list_text(record_id), encoding="utf-8")
    try:
        changelog.collect_changelog_records(
            fragment_dir=frag_dir, bundle_dir=bundle_dir, retraction_path=retraction_path
        )
    except changelog.FragmentValidationError as exc:
        assert record_id in str(exc) and "retracted id" in str(exc), exc
    else:
        raise AssertionError("a retracted id present as a fragment was accepted")


def test_listed_retracted_id_present_in_part_is_refused(tmp_path: Path) -> None:
    """AC-B4a: a retracted id still inside a bundle part is refused, not hidden."""
    frag_dir = tmp_path / "changelog.d"
    frag_dir.mkdir()
    bundle_dir = tmp_path / "changelog.months"
    bundle_dir.mkdir()
    record_id = "e2000002-0002-4002-8002-200000000002"
    _write_released_fragment(frag_dir, record_id, "2026-11-02")
    changelog.compact_month(
        "2026-11", fragment_dir=frag_dir, bundle_dir=bundle_dir,
        released_versions={"core": {"3.0.0"}},
    )
    retraction_path = tmp_path / "changelog-retractions.toml"
    retraction_path.write_text(_retraction_list_text(record_id), encoding="utf-8")
    try:
        changelog.collect_changelog_records(
            fragment_dir=frag_dir, bundle_dir=bundle_dir, retraction_path=retraction_path
        )
    except changelog.FragmentValidationError as exc:
        assert record_id in str(exc) and "retracted id" in str(exc), exc
    else:
        raise AssertionError("a retracted id still present in a part was accepted")


def test_retract_rename_failure_raises_and_lists_nothing(
    tmp_path: Path, monkeypatch
) -> None:
    """AC-B4a: a failed part removal stops retract before the list is written."""
    frag_dir = tmp_path / "changelog.d"
    frag_dir.mkdir()
    bundle_dir = tmp_path / "changelog.months"
    bundle_dir.mkdir()
    record_id = "e3000003-0003-4003-8003-300000000003"
    _write_released_fragment(frag_dir, record_id, "2026-11-03")
    changelog.compact_month(
        "2026-11", fragment_dir=frag_dir, bundle_dir=bundle_dir,
        released_versions={"core": {"3.0.0"}},
    )
    retraction_path = tmp_path / "changelog-retractions.toml"
    parts_before = {p.name: p.read_bytes() for p in bundle_dir.iterdir()}

    def failing_rename(self, target):
        raise OSError("injected rename failure")

    monkeypatch.setattr(Path, "rename", failing_rename)
    try:
        changelog.retract_record(
            record_id, "credential", bundle_dir=bundle_dir, retraction_path=retraction_path
        )
    except OSError:
        pass
    else:
        raise AssertionError("retract reported success although the part was not removed")
    monkeypatch.undo()
    assert not retraction_path.exists() or record_id not in retraction_path.read_text(
        encoding="utf-8"
    ), "the record was listed as retracted while it stays published"
    assert {p.name: p.read_bytes() for p in bundle_dir.iterdir()} == parts_before


def test_validate_cli_with_absent_record_directories(tmp_path: Path) -> None:
    """AC-B11: the gate's command passes with no record directories, yet still compares.

    A repository before cutover has neither `changelog.d/` nor
    `changelog.months/`. The required gate must pass there, and an absent
    directory must not skip the merge-base comparison: deleting a months
    directory the merge base holds is refused.
    """
    repo = tmp_path / "repo"
    repo.mkdir()
    env = {**__import__("os").environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@example.invalid",
           "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@example.invalid"}

    def git(*args: str) -> str:
        return subprocess.run(
            ["git", *args], cwd=repo, env=env, check=True, capture_output=True, text=True
        ).stdout.strip()

    def validate() -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, str(_SCRIPT), "validate"],
            cwd=repo, env=env, capture_output=True, text=True,
        )

    git("init", "-q", "-b", "main")
    (repo / "README.md").write_text("base\n", encoding="utf-8")
    git("add", "-A")
    git("commit", "-qm", "base")
    git("update-ref", "refs/remotes/origin/main", git("rev-parse", "HEAD"))
    result = validate()
    assert result.returncode == 0, f"validate refused an empty repository: {result.stderr}"

    frag_dir = repo / "docs/product/changelog.d"
    frag_dir.mkdir(parents=True)
    bundle_dir = repo / "docs/product/changelog.months"
    _write_released_fragment(frag_dir, "f1000001-0001-4001-8001-100000000001", "2026-11-01")
    changelog.compact_month(
        "2026-11", fragment_dir=frag_dir, bundle_dir=bundle_dir,
        released_versions={"core": {"3.0.0"}},
    )
    git("add", "-A")
    git("commit", "-qm", "compacted")
    git("update-ref", "refs/remotes/origin/main", git("rev-parse", "HEAD"))
    assert validate().returncode == 0
    git("rm", "-rq", "docs/product/changelog.months")
    git("commit", "-qm", "drop months")
    result = validate()
    assert result.returncode == 1, "deleting a merge-base months directory was accepted"
    assert "f1000001-0001-4001-8001-100000000001" in result.stderr, result.stderr


def test_compact_cli_moves_released_fragment(tmp_path: Path) -> None:
    """Fix 4 / AC-B6: compact CLI auto-discovers the released-version inventory.

    The compact subcommand must derive the released-version inventory from
    the repository's pack manifests and the historical changelog — the same
    sources the site build uses — so it moves exactly the fragments the build
    would classify as released.  A CLI test in a minimal temp layout confirms
    that `compact --month YYYY-MM` moves a released fragment without any
    additional argument.
    """
    repo = tmp_path / "repo"
    repo.mkdir()

    # Pack manifest: core 3.0.0 is the current released version.
    pack_dir = repo / "packs" / "core"
    pack_dir.mkdir(parents=True)
    (pack_dir / "pack.toml").write_text(
        "[pack]\n"
        'name = "core"\n'
        'version = "3.0.0"\n',
        encoding="utf-8",
    )
    (repo / "site.toml").write_text(
        "[[groups]]\n"
        'label = "Foundation"\n'
        'packs = ["core"]\n',
        encoding="utf-8",
    )

    # Historical changelog: core 3.0.0 is released.
    product_dir = repo / "docs" / "product"
    product_dir.mkdir(parents=True)
    (product_dir / "changelog.md").write_text(
        "# Changelog\n\n"
        "## [core][3.0.0] — 2026-09-28\n\n"
        "### Highlights\n\n"
        "- Historical release.\n",
        encoding="utf-8",
    )

    # One fragment for core 3.0.0 in the target month.
    frag_id = "cc111111-1111-4111-8111-111111111111"
    frag_dir = product_dir / "changelog.d"
    frag_dir.mkdir()
    anchor = changelog._compose_fragment_anchor(
        [{"name": "core", "version": "3.0.0"}], "2026-09-15", frag_id
    )
    (frag_dir / f"{frag_id}.md").write_text(
        _fragment_text(
            fragment_id=frag_id,
            anchor=anchor,
            date="2026-09-15",
            packages='[[packages]]\nname = "core"\nversion = "3.0.0"',
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, str(_SCRIPT), "compact", "--month", "2026-09"],
        cwd=repo,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"compact CLI failed:\nstdout: {result.stdout}\nstderr: {result.stderr}"
    )
    # The loose fragment must be gone and a bundle part must exist.
    assert not (frag_dir / f"{frag_id}.md").exists(), (
        "compact CLI did not delete the loose fragment"
    )
    bundle_parts = list((product_dir / "changelog.months").glob("*.bundle"))
    assert len(bundle_parts) == 1, (
        f"expected one bundle part, got: {bundle_parts}"
    )


def test_compact_cli_rerun_completes_interrupted_state(tmp_path: Path) -> None:
    """Fix A / AC-B6: compact CLI rerun completes a partially-compacted state.

    The CLI must not call collect_changelog_records itself before compact_month,
    because in the interrupted state (bundle part written, loose fragment still
    present) that raises DuplicateRecordIdError and the CLI exits 1 before
    compact_month's internal rerun-recovery path can run.

    The test constructs the interrupted state directly — both fragments are
    compacted (first CLI run succeeds), then one loose fragment is restored
    byte-exactly — and confirms that a second CLI run exits 0 and deletes the
    remaining fragment without creating a second bundle part.

    Mutation proof: restoring a pre-call to collect_changelog_records in the CLI
    compact branch causes DuplicateRecordIdError to propagate and the CLI to
    exit 1, failing the returncode == 0 assertion.
    """
    repo = tmp_path / "repo"
    repo.mkdir()

    pack_dir = repo / "packs" / "core"
    pack_dir.mkdir(parents=True)
    (pack_dir / "pack.toml").write_text(
        "[pack]\nname = \"core\"\nversion = \"3.0.0\"\n",
        encoding="utf-8",
    )
    (repo / "site.toml").write_text(
        "[[groups]]\nlabel = \"Foundation\"\npacks = [\"core\"]\n",
        encoding="utf-8",
    )
    product_dir = repo / "docs" / "product"
    product_dir.mkdir(parents=True)
    (product_dir / "changelog.md").write_text(
        "# Changelog\n\n## [core][3.0.0] — 2026-09-28\n\n### Highlights\n\n- Historical release.\n",
        encoding="utf-8",
    )

    frag_dir = product_dir / "changelog.d"
    frag_dir.mkdir()
    bundle_dir = product_dir / "changelog.months"
    bundle_dir.mkdir()

    id1 = "f1000001-0001-4001-8001-100000000001"
    id2 = "f2000002-0002-4002-8002-200000000002"

    def _make_text(fid: str) -> str:
        anchor = changelog._compose_fragment_anchor(
            [{"name": "core", "version": "3.0.0"}], "2026-10-01", fid
        )
        return _fragment_text(
            fragment_id=fid,
            anchor=anchor,
            date="2026-10-01",
            packages='[[packages]]\nname = "core"\nversion = "3.0.0"',
        )

    id2_text = _make_text(id2)
    for fid in (id1, id2):
        (frag_dir / f"{fid}.md").write_text(_make_text(fid), encoding="utf-8")

    # First compact run: bundles both fragments and deletes them.
    result1 = subprocess.run(
        [sys.executable, str(_SCRIPT), "compact", "--month", "2026-10"],
        cwd=repo,
        capture_output=True,
        text=True,
    )
    assert result1.returncode == 0, (
        f"first compact CLI run failed:\nstdout: {result1.stdout}\nstderr: {result1.stderr}"
    )
    assert not (frag_dir / f"{id2}.md").exists(), "first run did not delete id2"

    # Construct the interrupted state: restore id2 as a loose fragment (byte-exact copy).
    (frag_dir / f"{id2}.md").write_text(id2_text, encoding="utf-8")

    # Verify the interrupted state raises DuplicateRecordIdError on strict collection.
    try:
        changelog.collect_changelog_records(fragment_dir=frag_dir, bundle_dir=bundle_dir)
    except changelog.DuplicateRecordIdError:
        pass
    else:
        raise AssertionError("interrupted state was not detected as a duplicate")

    parts_before = sorted(p.name for p in bundle_dir.glob("*.bundle"))

    # Rerun: the CLI must complete the deletion and exit 0.
    result2 = subprocess.run(
        [sys.executable, str(_SCRIPT), "compact", "--month", "2026-10"],
        cwd=repo,
        capture_output=True,
        text=True,
    )
    assert result2.returncode == 0, (
        f"compact CLI rerun failed:\nstdout: {result2.stdout}\nstderr: {result2.stderr}"
    )
    assert not (frag_dir / f"{id2}.md").exists(), "rerun did not delete the loose fragment"
    parts_after = sorted(p.name for p in bundle_dir.glob("*.bundle"))
    assert parts_after == parts_before, (
        f"rerun created a second bundle part: {parts_after}"
    )


def test_render_cli_includes_bundled_records(tmp_path: Path) -> None:
    """D10 / AC-B8: `render` reads bundled records through the one reader.

    The same records render byte-identically whether loose or compacted into a
    part, including when compaction leaves no `changelog.d/` behind.
    """
    repo = tmp_path / "repo"
    product = repo / "docs/product"
    frag_dir = product / "changelog.d"
    frag_dir.mkdir(parents=True)
    (product / "changelog.md").write_text(
        _HISTORICAL_CHANGELOG.read_text(encoding="utf-8"), encoding="utf-8"
    )
    (repo / ".gitignore").write_text("build/\n", encoding="utf-8")
    ids = ["a7000001-0001-4001-8001-100000000001", "a7000002-0002-4002-8002-200000000002"]
    for fid in ids:
        _write_released_fragment(frag_dir, fid, "2026-11-04")
    _git(repo, "init", "-b", "main")
    _git(repo, "config", "user.name", "Test Author")
    _git(repo, "config", "user.email", "test.invalid")
    _git(repo, "add", ".")
    _git(repo, "commit", "-m", "loose")
    _git(repo, "update-ref", "refs/remotes/origin/main", "HEAD")

    loose_out = repo / "build/loose.md"
    result = _run_render(repo, loose_out)
    assert result.returncode == 0, result.stderr
    loose_text = loose_out.read_text(encoding="utf-8")
    assert all(fid.replace("-", "") in loose_text for fid in ids)

    changelog.compact_month(
        "2026-11", fragment_dir=frag_dir, bundle_dir=product / "changelog.months",
        released_versions={"core": {"3.0.0"}},
    )
    if frag_dir.exists() and not any(frag_dir.iterdir()):
        frag_dir.rmdir()
    assert not frag_dir.exists(), "compaction should leave no loose fragment"
    bundled_out = repo / "build/bundled.md"
    result = _run_render(repo, bundled_out)
    assert result.returncode == 0, result.stderr
    assert bundled_out.read_text(encoding="utf-8") == loose_text, (
        "render output changed when the records moved into a bundle part"
    )


# ---------------------------------------------------------------------------
# T14: Dependency and privacy posture
#
# Two checks per § 7 Dependency and privacy posture:
#   1. Static: no third-party import added to any touched tools/ entry point.
#   2. Offline: the Python projection runs with socket.connect blocked.
# ---------------------------------------------------------------------------


def test_no_third_party_import_added_by_delivery() -> None:
    """T14 static check: no third-party import added to any touched tools/ entry point.

    For files this delivery creates (untracked in Git) every import must be
    standard library.  For files that already existed only imports absent from
    the merge-base version count as violations.  Pre-existing third-party
    imports in existing files are out of scope.
    """
    import ast

    ROOT = _SCRIPT.parent.parent
    STDLIB = sys.stdlib_module_names

    # Closed set from T14's Touches fields (all touched tools/ files, test
    # suites included — tools/AGENTS.md's pure-stdlib rule binds new additions
    # without distinguishing a suite from an entry point).
    CLOSED_SET = [
        ROOT / "tools/changelog.py",
        ROOT / "tools/build-site.py",
        ROOT / "tools/check-core-release.py",
        ROOT / "tools/repo/check_release_impact.py",
        ROOT / "tools/measure-changelog-fragment-merges.py",
        ROOT / "tools/measure-changelog-anchor-drift.py",
        ROOT / "tools/test-pages-workflow.py",
        ROOT / "tools/test_build_site_routing.py",
        ROOT / "tools/test_check_core_release.py",
        ROOT / "tools/test_check_release_impact.py",
        ROOT / "tools/lint-ci-parity.py",
        ROOT / "tools/test_changelog.py",
    ]

    def _top_level(name: str) -> str:
        return name.split(".")[0]

    def _collect_imports(source: str) -> set[str]:
        """Return every top-level module name imported anywhere in source."""
        tree = ast.parse(source)
        names: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    names.add(_top_level(alias.name))
            elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
                names.add(_top_level(node.module))
        return names

    def _is_local(name: str) -> bool:
        """True when name maps to a .py file inside the repository."""
        for candidate in [
            ROOT / "tools" / f"{name}.py",
            ROOT / "tools" / "repo" / f"{name}.py",
            ROOT / f"{name}.py",
        ]:
            if candidate.is_file():
                return True
        return False

    def _third_party(imports: set[str]) -> set[str]:
        return {n for n in imports if n not in STDLIB and not _is_local(n)}

    base_result = subprocess.run(
        ["git", "merge-base", "origin/main", "HEAD"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert base_result.returncode == 0, f"git merge-base: {base_result.stderr}"
    merge_base = base_result.stdout.strip()

    # Identify untracked paths — those are files this delivery created.
    status_result = subprocess.run(
        ["git", "status", "--short"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    untracked: set[str] = set()
    for line in status_result.stdout.splitlines():
        if line.startswith("??"):
            rel = line[3:].strip().rstrip("/")
            untracked.add(str((ROOT / rel).resolve()))

    violations: list[str] = []

    for path in CLOSED_SET:
        if not path.exists():
            violations.append(f"MISSING: {path}")
            continue
        current_imports = _collect_imports(path.read_text(encoding="utf-8"))
        current_third = _third_party(current_imports)

        if str(path.resolve()) in untracked:
            # File created by this delivery — every import must be stdlib.
            if current_third:
                violations.append(
                    f"CREATED {path.relative_to(ROOT)}: "
                    f"third-party imports: {sorted(current_third)}"
                )
        else:
            # Existing file — only newly added third-party imports are violations.
            rel = str(path.relative_to(ROOT))
            show = subprocess.run(
                ["git", "show", f"{merge_base}:{rel}"],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            if show.returncode != 0:
                # Absent at merge base — treat as created.
                if current_third:
                    violations.append(
                        f"ADDED {rel}: third-party imports: {sorted(current_third)}"
                    )
                continue
            base_third = _third_party(_collect_imports(show.stdout))
            added = current_third - base_third
            if added:
                violations.append(
                    f"MODIFIED {rel}: new third-party imports: {sorted(added)}"
                )

    assert not violations, "Third-party import violations:\n" + "\n".join(violations)


def test_offline_build_runs_without_network_access(tmp_path: Path) -> None:
    """T14 offline check: end-to-end Python projection completes with socket blocked.

    A wrapper script patches socket.connect to raise before loading the
    changelog module, then exercises the render view (T5) and the /now/
    projection (T7 Python path).  A sentinel file records any connection
    attempt; the test asserts none was made.
    """
    import textwrap

    sentinel = tmp_path / "connection_attempted.txt"
    wrapper = tmp_path / "offline_runner.py"
    baseline = tmp_path / "docs" / "product" / "changelog.md"
    baseline.parent.mkdir(parents=True)
    baseline.write_text("# Changelog\n", encoding="utf-8")
    output = tmp_path / "build" / "product-changelog.md"
    # Point --fragments at a path that does not exist so that
    # collect_changelog_records returns ([], []) without any git or I/O calls.
    fragments = tmp_path / "nonexistent_changelog.d"

    wrapper.write_text(
        textwrap.dedent(
            f"""\
            import socket as _sock
            _sentinel = {str(sentinel)!r}
            def _blocked(self, address):
                with open(_sentinel, "a", encoding="utf-8") as _f:
                    _f.write(f"connect {{address!r}}\\n")
                raise OSError(f"T14 offline guard: connection to {{address!r}} blocked")
            _sock.socket.connect = _blocked

            import importlib.util as _ilu
            import sys
            _spec = _ilu.spec_from_file_location("product_changelog", {str(_SCRIPT)!r})
            assert _spec is not None and _spec.loader is not None
            _mod = _ilu.module_from_spec(_spec)
            sys.modules[_spec.name] = _mod
            _spec.loader.exec_module(_mod)

            # T5: render the complete changelog view.
            rc = _mod.main([
                "render",
                "--output", {str(output)!r},
                "--baseline", {str(baseline)!r},
                "--fragments", {str(fragments)!r},
            ])
            assert rc == 0, f"render returned {{rc}}"

            # T7 Python path: project the /now/ payload from zero fragments.
            result = _mod.project_fragment_now_highlights([], {{}})
            assert isinstance(result, dict)

            print("offline-ok")
            """
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, str(wrapper)],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, f"Offline build failed:\n{result.stderr}"
    assert "offline-ok" in result.stdout, (
        f"Wrapper did not complete successfully:\n{result.stdout}"
    )
    assert not sentinel.exists(), (
        "Network connection attempted during offline build:\n"
        + sentinel.read_text(encoding="utf-8")
    )


# ---------------------------------------------------------------------------
# Fix 1 — validate CLI enforces historical-baseline refusal (T14 repair)
# ---------------------------------------------------------------------------


def test_validate_cli_refuses_edited_historical_release_section(tmp_path: Path) -> None:
    """Fix 1 / spec AC: the required validate gate refuses an edited release section.

    A change that edits a historical release section in docs/product/changelog.md
    must be refused by a gate naming the edited heading, and the required gate
    is `python3 tools/changelog.py validate` (AC-B11).
    """
    import os as _os

    repo = tmp_path / "repo"
    repo.mkdir()
    env = {
        **_os.environ,
        "GIT_AUTHOR_NAME": "t",
        "GIT_AUTHOR_EMAIL": "t@example.invalid",
        "GIT_COMMITTER_NAME": "t",
        "GIT_COMMITTER_EMAIL": "t@example.invalid",
    }

    def git(*args: str) -> str:
        return subprocess.run(
            ["git", *args], cwd=repo, env=env, check=True,
            capture_output=True, text=True,
        ).stdout.strip()

    def validate() -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, str(_SCRIPT), "validate"],
            cwd=repo, env=env, capture_output=True, text=True,
        )

    # Baseline changelog with one historical release section.
    # Use the TOML-style heading format [name][version] that _parse_release_identity
    # recognises, so _historical_release_sections returns a non-empty list.
    changelog_dir = repo / "docs" / "product"
    changelog_dir.mkdir(parents=True)
    changelog_path = changelog_dir / "changelog.md"
    heading = "## [core][3.0.0] — 2026-01-15"
    changelog_path.write_text(
        f"# Changelog\n\n{heading}\n\n### Highlights\n- Initial release.\n",
        encoding="utf-8",
    )
    git("init", "-q", "-b", "main")
    git("add", "docs/product/changelog.md")
    git("commit", "-qm", "base")
    git("update-ref", "refs/remotes/origin/main", git("rev-parse", "HEAD"))

    # Edit the historical release section body (working tree only, not committed).
    changelog_path.write_text(
        f"# Changelog\n\n{heading}\n\n### Highlights\n- EDITED initial release.\n",
        encoding="utf-8",
    )

    result = validate()
    assert result.returncode == 1, (
        f"validate accepted an edited historical release section (exit 0):\n{result.stderr}"
    )
    # The error names the heading text (without the "## " prefix — the field in
    # _fragment_error is the extracted title, not the full Markdown heading line).
    heading_text = heading.lstrip("# ").strip()
    assert heading_text in result.stderr, (
        f"validate did not name the edited heading in its error:\n{result.stderr}"
    )


# ---------------------------------------------------------------------------
# Fix 2 — _base_blob_text fail-closed (T14 repair)
# ---------------------------------------------------------------------------


def test_base_blob_text_raises_on_exit_128(tmp_path: Path) -> None:
    """Fix 2: _base_blob_text raises FragmentValidationError on unexpected git failure.

    A non-zero exit that is NOT exit 1 with "no merge base" must refuse
    fail-closed rather than silently disabling the historical-baseline check.
    """
    _GitResult = changelog._GitResult
    baseline = tmp_path / "docs" / "product" / "changelog.md"
    baseline.parent.mkdir(parents=True)
    baseline.write_text("# Changelog\n", encoding="utf-8")

    def fake_git(cwd, *args):
        if args[0] == "rev-parse" and "--show-toplevel" in args:
            return _GitResult(0, str(tmp_path) + "\n", "")
        if args[0] == "merge-base":
            # Simulate a repository or network error.
            return _GitResult(128, "", "fatal: not a git repository")
        return _GitResult(128, "", f"unexpected: {args}")

    try:
        changelog._base_blob_text(baseline, git_runner=fake_git)
    except changelog.FragmentValidationError as exc:
        assert "128" in str(exc) or "merge-base" in str(exc), (
            f"error does not name exit code or context: {exc}"
        )
    else:
        raise AssertionError(
            "_base_blob_text returned None for a git exit-128 failure "
            "instead of raising FragmentValidationError"
        )


def test_base_blob_text_returns_none_for_no_merge_base(tmp_path: Path) -> None:
    """Fix 2: exit 1 with 'no merge base' in stderr returns None (orphan branch).

    validate_historical_changelog_baseline must silently return when there is
    no common ancestor, consistent with validate_changelog_cross_form_identity.
    """
    _GitResult = changelog._GitResult
    baseline = tmp_path / "docs" / "product" / "changelog.md"
    baseline.parent.mkdir(parents=True)
    baseline.write_text("# Changelog\n\n## [core 3.0.0] — 2026-01-15\n\n- Original.\n",
                        encoding="utf-8")

    def fake_git(cwd, *args):
        if args[0] == "rev-parse" and "--show-toplevel" in args:
            return _GitResult(0, str(tmp_path) + "\n", "")
        if args[0] == "merge-base":
            return _GitResult(1, "", "fatal: no merge base")
        return _GitResult(128, "", f"unexpected: {args}")

    # Should return None → validate_historical_changelog_baseline returns silently.
    try:
        changelog.validate_historical_changelog_baseline(baseline, git_runner=fake_git)
    except changelog.FragmentValidationError as exc:
        raise AssertionError(
            f"validate_historical_changelog_baseline raised for an orphan branch: {exc}"
        ) from exc


# ---------------------------------------------------------------------------
# Fix 3 — typed rerun dispatch in compact_month (T14 repair)
# ---------------------------------------------------------------------------


def test_compact_two_bundle_parts_with_same_id_raises(tmp_path: Path) -> None:
    """Fix 3b: the same id in two bundle parts raises from the rerun-recovery path.

    When compact_month catches DuplicateRecordIdError from the initial
    collect_changelog_records (cross-form duplicate), the recovery path calls
    _collect_bundle_records with seen_ids=set().  A duplicate id across two
    bundle parts then raises DuplicateRecordIdError again, which is not caught
    by the recovery handler and propagates out of compact_month.
    """
    frag_dir = tmp_path / "changelog.d"
    frag_dir.mkdir()
    bundle_dir = tmp_path / "changelog.months"
    bundle_dir.mkdir()

    dup_id = "ffffffff-ffff-4fff-8fff-ffffffffffff"
    anchor = changelog._compose_fragment_anchor(
        [{"name": "core", "version": "3.0.0"}], "2026-11-01", dup_id
    )
    rec = _bundle_fragment_text(fragment_id=dup_id, anchor=anchor, date="2026-11-01")

    # Also write the same id as a loose fragment to trigger the initial
    # cross-form DuplicateRecordIdError so the recovery path is entered.
    (frag_dir / f"{dup_id}.md").write_text(
        _fragment_text(
            fragment_id=dup_id,
            anchor=anchor,
            date="2026-11-01",
            packages='[[packages]]\nname = "core"\nversion = "3.0.0"',
        ),
        encoding="utf-8",
    )

    # Put the same id into two separate bundle parts.
    (bundle_dir / "2026-11-00.bundle").write_bytes(
        changelog.BUNDLE_SEPARATOR_BYTES + rec.encode("utf-8")
    )
    (bundle_dir / "2026-11-01.bundle").write_bytes(
        changelog.BUNDLE_SEPARATOR_BYTES + rec.encode("utf-8")
    )

    try:
        changelog.compact_month(
            "2026-11",
            fragment_dir=frag_dir,
            bundle_dir=bundle_dir,
            released_versions={"core": {"3.0.0"}},
        )
    except changelog.FragmentValidationError as exc:
        assert "duplicate id" in str(exc).lower(), (
            f"expected 'duplicate id' in the error, got: {exc}"
        )
    else:
        raise AssertionError(
            "compact_month accepted two bundle parts with the same id"
        )


def test_compact_non_duplicate_fragment_validation_error_is_reraised(
    tmp_path: Path, monkeypatch
) -> None:
    """Fix 3c: a FragmentValidationError that is not DuplicateRecordIdError is re-raised.

    A generic FragmentValidationError whose message happens to contain 'duplicate id'
    (but whose type is not DuplicateRecordIdError) must not be swallowed by the
    rerun-recovery handler.
    """
    frag_dir = tmp_path / "changelog.d"
    frag_dir.mkdir()
    bundle_dir = tmp_path / "changelog.months"
    bundle_dir.mkdir()

    sentinel_error = changelog.FragmentValidationError(
        "duplicate id in some other context"
    )

    def fake_collect(*args, **kwargs):
        raise sentinel_error

    monkeypatch.setattr(changelog, "collect_changelog_records", fake_collect)

    try:
        changelog.compact_month(
            "2026-11",
            fragment_dir=frag_dir,
            bundle_dir=bundle_dir,
            released_versions={"core": {"3.0.0"}},
        )
    except changelog.FragmentValidationError as exc:
        assert exc is sentinel_error, (
            f"a different error was raised instead of the injected one: {exc}"
        )
    else:
        raise AssertionError(
            "compact_month swallowed a non-DuplicateRecordIdError FragmentValidationError"
        )


# ---------------------------------------------------------------------------
# Fix 6 — AC-B4 ride-along acceptance fixture (T14 repair / adversarial F1)
# ---------------------------------------------------------------------------


def test_validate_cross_form_accepts_part_adding_with_new_fragment(
    tmp_path: Path,
) -> None:
    """Fix 6 / AC-B4: a part-adding change that also adds a new fragment passes.

    Merge base: one loose fragment (A).
    Current state: fragment A compacted into a new bundle part (loose file deleted);
    a fresh loose fragment (B) absent at the merge base and not bundled also present.
    validate_changelog_cross_form_identity must raise nothing.

    Mutation check: if Refusal 3 also fired for non-base fragment ids, this
    fixture would fail because B is not in base_frag_ids.
    """
    frag_dir = tmp_path / "changelog.d"
    frag_dir.mkdir()
    bundle_dir = tmp_path / "changelog.months"
    bundle_dir.mkdir()
    retraction_path = tmp_path / "changelog-retractions.toml"

    # Fragment A: was loose at merge base, now bundled (loose file deleted).
    frag_a_id = "aabbccdd-aabb-4aab-8aab-aabbccddaabb"
    frag_a_anchor = changelog._compose_fragment_anchor(
        [{"name": "core", "version": "3.0.0"}], "2026-10-01", frag_a_id
    )
    rec_a = _bundle_fragment_text(
        fragment_id=frag_a_id, anchor=frag_a_anchor, date="2026-10-01"
    )

    # Fragment B: absent at merge base, not bundled — a genuine new contribution.
    frag_b_id = "11223344-1122-4112-8112-112233441122"
    frag_b_anchor = changelog._compose_fragment_anchor(
        [{"name": "core", "version": "3.0.0"}], "2026-10-02", frag_b_id
    )
    frag_b_path = frag_dir / f"{frag_b_id}.md"
    frag_b_path.write_text(
        _fragment_text(
            fragment_id=frag_b_id,
            anchor=frag_b_anchor,
            date="2026-10-02",
            packages='[[packages]]\nname = "core"\nversion = "3.0.0"',
        ),
        encoding="utf-8",
    )

    # Current bundle part: contains only fragment A (byte-exact copy).
    part_content = changelog.BUNDLE_SEPARATOR_BYTES + rec_a.encode("utf-8")
    (bundle_dir / "2026-10-00.bundle").write_bytes(part_content)

    # Merge-base ls-tree: only fragment A was present (loose); fragment B is new.
    frag_a_obj = "a" * 40
    merge_base = "12345678" * 5
    ls_lines = [f"100644 blob {frag_a_obj}\tchangelog.d/{frag_a_id}.md"]

    _GitResult = changelog._GitResult

    def fake_git(cwd, *args):
        """Extended fake git runner that also handles diff/ls-files for fragment validation."""
        if args[0] == "rev-parse" and "--show-toplevel" in args:
            return _GitResult(0, str(tmp_path) + "\n", "")
        if args[0] == "merge-base":
            return _GitResult(0, merge_base + "\n", "")
        if args[0] == "rev-parse" and "--show-object-format" in args:
            return _GitResult(0, "sha1\n", "")
        if args[0] == "ls-tree":
            ls_output = "\n".join(ls_lines)
            return _GitResult(0, ls_output + "\n" if ls_output else "", "")
        if args[0] == "diff" and "--name-status" in args:
            # Fragment B is newly added; fragment A is gone (deleted then bundled).
            diff_out = f"A\tchangelog.d/{frag_b_id}.md\n"
            return _GitResult(0, diff_out, "")
        if args[0] == "ls-files":
            # Only fragment B is tracked in the current working tree.
            return _GitResult(0, f"changelog.d/{frag_b_id}.md\n", "")
        return _GitResult(128, "", f"unexpected git call: {' '.join(str(a) for a in args)}")

    # Because the bundle part's object id differs from the base ls-tree,
    # the validator reads the merge-base blob for A to compare bytes.
    original_bytes_runner = changelog._git_runner_bytes

    def fake_bytes(repo, *args):
        if args[0] == "cat-file" and args[1] == "-s":
            # Return the size of the loose fragment A bytes.
            return (0, str(len(rec_a.encode("utf-8"))).encode() + b"\n", "")
        if args[0] == "cat-file" and args[1] == "blob":
            # Return the base loose fragment A bytes (plain, not bundled).
            return (0, rec_a.encode("utf-8"), "")
        return original_bytes_runner(repo, *args)

    changelog._git_runner_bytes = fake_bytes
    try:
        changelog.validate_changelog_cross_form_identity(
            fragment_dir=frag_dir,
            bundle_dir=bundle_dir,
            retraction_path=retraction_path,
            git_runner=fake_git,
        )
    except changelog.FragmentValidationError as exc:
        raise AssertionError(
            f"ride-along acceptance fixture raised unexpectedly: {exc}"
        ) from exc
    finally:
        changelog._git_runner_bytes = original_bytes_runner


# ============================================================================
# T14 repair round: eight acceptance fixtures (QE adjudication round 6)
# Fixtures F1–F8 add the missing coverage identified in the adjudication.
# ============================================================================


def test_bundle_part_refuses_separator_line_in_record_body(tmp_path: Path) -> None:
    """F1 (AC-B2): a separator line in a bundled record body causes refusal.

    The part is split on the separator line, so an embedded separator yields
    an extra element instead of reaching any in-body check. Here it ends the
    body, so the guard that fires is the "empty record" check on the trailing
    zero-byte element the split produces.
    """
    bundle_dir = tmp_path / "changelog.months"
    bundle_dir.mkdir()
    # Body ends with the separator line; after split, the second element is empty.
    body = "## Highlights\n- OK.\n" + changelog.BUNDLE_SEPARATOR_LINE + "\n"
    rec = _bundle_fragment_text(body=body)
    content = changelog.BUNDLE_SEPARATOR_BYTES + rec.encode("utf-8")
    part = bundle_dir / "2026-10-00.bundle"
    part.write_bytes(content)
    try:
        changelog._parse_bundle_part(part, content)
    except changelog.FragmentValidationError as exc:
        msg = str(exc)
        assert str(part) in msg, f"part path not in error: {msg}"
        # "record 1" names the spurious second element from the split.
        assert "record" in msg.lower(), f"record position not in error: {msg}"
    else:
        raise AssertionError(
            "bundle part with separator line in record body was accepted; "
            "expected FragmentValidationError"
        )


def test_collect_bundle_records_refuses_duplicate_nn(tmp_path: Path) -> None:
    """F2 (AC-B3): duplicate month+NN is refused through _collect_bundle_records.

    A duplicate NN cannot occur through the real ``list_confined_regular_files``
    helper because two files with the same name cannot coexist in one directory.
    This fixture stubs the helper to return two paths sharing the same name,
    which produces the same month+NN pair and triggers the guard at
    ``changelog.py`` lines 1893-1898.
    """
    bundle_dir = tmp_path / "changelog.months"
    bundle_dir.mkdir()

    class _StubSafety:
        class UnsafeContentError(Exception):
            pass

        def list_confined_directories(self, root, directory):  # noqa: ANN001
            return []

        def list_confined_regular_files(self, root, directory, **kwargs):  # noqa: ANN001
            # Two paths with the same name → same month+NN.
            return [directory / "2026-10-00.bundle", directory / "2026-10-00.bundle"]

        def read_confined_regular_file(self, root, path, *, max_bytes=None):  # noqa: ANN001
            raise AssertionError("read should not be reached before the NN check")

    try:
        changelog._collect_bundle_records(bundle_dir, _StubSafety())
    except changelog.FragmentValidationError as exc:
        msg = str(exc)
        assert "2026-10-00.bundle" in msg, f"part path not in error: {msg}"
        assert (
            "duplicate" in msg.lower() or "nn" in msg.lower()
        ), f"duplicate NN not named in error: {msg}"
    else:
        raise AssertionError(
            "duplicate month+NN was accepted; expected FragmentValidationError"
        )


def test_collect_bundle_records_refuses_stray_non_bundle_file(tmp_path: Path) -> None:
    """F3 (AC-B3): a non-.bundle regular file in the bundle directory is refused.

    ``list_confined_regular_files`` returns regular files regardless of
    extension; ``_validate_bundle_part_name`` then refuses names that do not
    fullmatch ``YYYY-MM-NN.bundle``, naming the stray path.
    """
    bundle_dir = tmp_path / "changelog.months"
    bundle_dir.mkdir()
    stray = bundle_dir / "README.txt"
    stray.write_text("stray content\n", encoding="utf-8")
    fs = changelog._file_safety()
    try:
        changelog._collect_bundle_records(bundle_dir, fs)
    except changelog.FragmentValidationError as exc:
        msg = str(exc)
        assert str(stray) in msg or "README.txt" in msg, (
            f"stray file path not in error: {msg}"
        )
        # The name-validation error names "name" in the field; a downstream
        # content-parsing error says "record 0".  This distinguishes the two.
        assert "name" in msg or "YYYY-MM-NN" in msg, (
            f"name-validation field not in error (got downstream guard instead): {msg}"
        )
    else:
        raise AssertionError(
            "stray non-.bundle file in bundle directory was accepted; "
            "expected FragmentValidationError"
        )


# ── F4 (AC-B3a): hard link and FIFO fixtures for bundle dir and retraction list ──


def test_bundle_dir_confinement_refuses_hard_link(tmp_path: Path) -> None:
    """F4 (AC-B3a): a hard link in the bundle directory is refused by path.

    A hard-linked file has ``st_nlink > 1``.  ``list_confined_regular_files``
    does not check link counts and returns the path; ``_read_bundle_part`` then
    calls ``read_confined_regular_file``, which detects the hard link and raises
    ``UnsafeContentError``.
    """
    bundle_dir = tmp_path / "changelog.months"
    bundle_dir.mkdir()
    src = tmp_path / "source.bundle"
    src.write_bytes(changelog.BUNDLE_SEPARATOR_BYTES + _bundle_fragment_text().encode())
    target = bundle_dir / "2026-10-00.bundle"
    _OS.link(src, target)  # target.stat().st_nlink == 2
    fs = changelog._file_safety()
    try:
        changelog._collect_bundle_records(bundle_dir, fs)
    except (changelog.FragmentValidationError, fs.UnsafeContentError) as exc:
        msg = str(exc)
        assert "2026-10-00.bundle" in msg or "hard link" in msg.lower(), (
            f"offending path not named in error: {msg}"
        )
    else:
        raise AssertionError(
            "hard link in bundle directory was accepted; expected refusal"
        )


def test_bundle_dir_confinement_refuses_fifo(tmp_path: Path) -> None:
    """F4 (AC-B3a): a FIFO in the bundle directory is refused by path.

    ``walk_confined_regular_files`` rejects non-regular, non-directory,
    non-link entries (the ``else`` branch at ``file_safety.py`` line 206)
    and raises ``UnsafeContentError`` naming the FIFO's relative path.
    """
    if not hasattr(_OS, "mkfifo"):
        return  # platform does not support FIFOs
    bundle_dir = tmp_path / "changelog.months"
    bundle_dir.mkdir()
    fifo = bundle_dir / "2026-10-00.bundle"
    _OS.mkfifo(fifo)
    fs = changelog._file_safety()
    try:
        changelog._collect_bundle_records(bundle_dir, fs)
    except (changelog.FragmentValidationError, fs.UnsafeContentError) as exc:
        msg = str(exc)
        assert "2026-10-00.bundle" in msg or "regular" in msg.lower(), (
            f"offending path not named in error: {msg}"
        )
    else:
        fifo.unlink()
        raise AssertionError(
            "FIFO in bundle directory was accepted; expected refusal"
        )
    if fifo.exists():
        fifo.unlink()


def test_retraction_list_confinement_refuses_hard_link(tmp_path: Path) -> None:
    """F4 (AC-B3a): a hard link at the retraction-list path is refused.

    ``read_confined_regular_file`` detects ``st_nlink > 1`` and raises
    ``UnsafeContentError``, which ``_read_retraction_list`` wraps into
    ``FragmentValidationError``.
    """
    src = tmp_path / "source-retractions.toml"
    src.write_text("", encoding="utf-8")
    retraction_path = tmp_path / "changelog-retractions.toml"
    _OS.link(src, retraction_path)  # retraction_path.stat().st_nlink == 2
    fs = changelog._file_safety()
    try:
        changelog._read_retraction_list(retraction_path, fs)
    except (changelog.FragmentValidationError, fs.UnsafeContentError) as exc:
        msg = str(exc)
        assert "changelog-retractions.toml" in msg or "hard link" in msg.lower(), (
            f"offending path not named in error: {msg}"
        )
    else:
        raise AssertionError(
            "hard link at retraction list path was accepted; expected refusal"
        )


def test_retraction_list_confinement_refuses_fifo(tmp_path: Path) -> None:
    """F4 (AC-B3a): a FIFO at the retraction-list path is refused.

    ``read_confined_regular_file`` checks ``S_ISREG`` before opening; a FIFO
    fails that check and raises ``UnsafeContentError``.
    """
    if not hasattr(_OS, "mkfifo"):
        return  # platform does not support FIFOs
    retraction_path = tmp_path / "changelog-retractions.toml"
    _OS.mkfifo(retraction_path)
    fs = changelog._file_safety()
    try:
        changelog._read_retraction_list(retraction_path, fs)
    except (changelog.FragmentValidationError, fs.UnsafeContentError) as exc:
        msg = str(exc)
        assert "changelog-retractions.toml" in msg or "regular" in msg.lower(), (
            f"offending path not named in error: {msg}"
        )
    else:
        if retraction_path.exists():
            retraction_path.unlink()
        raise AssertionError(
            "FIFO at retraction list path was accepted; expected refusal"
        )
    if retraction_path.exists():
        retraction_path.unlink()


# ── F5 (AC-B4 ident) ─────────────────────────────────────────────────────────


def test_ident_expanded_bundle_part_is_refused(tmp_path: Path) -> None:
    """F5 (AC-B4 ident): a bundle part expanded by git's ident filter is refused.

    AC-B4 requires "changed" to be decided by an object id over the exact loaded
    filesystem bytes, with no ident filter conversion.  After ``git checkout``
    applies the smudge filter (``$Id$`` → ``$Id: <blob-sha>$``), the working-tree
    bytes differ from the stored blob bytes.  The validator reads filesystem bytes
    directly, computes their sha1, finds it differs from the stored blob sha, reads
    the blob, compares bytes, and refuses.

    Mutation that kills this test: replace ``_compute_git_object_id(part_raw, ...)``
    with ``git hash-object --path=<part>`` (which applies the clean filter, strips
    the expansion, and recomputes the original hash) → no refusal, assertion
    fails.
    """
    import os as _os_f5
    import subprocess as _sp_f5

    _GIT_REDIRECTS = (
        "GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE",
        "GIT_OBJECT_DIRECTORY", "GIT_ALTERNATE_OBJECT_DIRECTORIES",
    )
    env_f5 = {k: v for k, v in _os_f5.environ.items() if k not in _GIT_REDIRECTS}
    env_f5.update({
        "GIT_AUTHOR_NAME": "changelog-f5-test",
        "GIT_AUTHOR_EMAIL": "test@invalid",
        "GIT_COMMITTER_NAME": "changelog-f5-test",
        "GIT_COMMITTER_EMAIL": "test@invalid",
        "GIT_AUTHOR_DATE": "2026-01-01T00:00:00+00:00",
        "GIT_COMMITTER_DATE": "2026-01-01T00:00:00+00:00",
    })

    def _run_f5(*args: str) -> str:
        r = _sp_f5.run(
            ["git", "-C", str(tmp_path), *args],
            capture_output=True, text=True, env=env_f5,
        )
        if r.returncode != 0:
            raise RuntimeError(f"git {' '.join(args)}: {r.stderr.strip()}")
        return r.stdout.strip()

    _run_f5("init")
    _run_f5("config", "user.email", "test@invalid")
    _run_f5("config", "user.name", "changelog-f5-test")

    # Enable git's ident attribute for bundle files.
    (tmp_path / ".gitattributes").write_text("*.bundle ident\n", encoding="utf-8")

    bundle_dir = tmp_path / "changelog.months"
    bundle_dir.mkdir()
    frag_dir = tmp_path / "changelog.d"
    frag_dir.mkdir()
    retraction_path = tmp_path / "changelog-retractions.toml"

    # Bundle part body contains the bare $Id$ token that git will expand on
    # checkout (smudge filter replaces $Id$ with $Id: <blob-sha>$).
    body_with_ident = "## Highlights\n- $Id$\n"
    rec = _bundle_fragment_text(body=body_with_ident)
    part_content_unexpanded = changelog.BUNDLE_SEPARATOR_BYTES + rec.encode("utf-8")
    part_path = bundle_dir / "2026-10-00.bundle"
    part_path.write_bytes(part_content_unexpanded)

    _run_f5("add", ".")
    _run_f5("commit", "-m", "base")
    base_sha = _run_f5("rev-parse", "HEAD")
    _run_f5("update-ref", "refs/remotes/origin/main", base_sha)

    # Check the part out afresh so the smudge filter expands $Id$; a checkout
    # of an up-to-date path would leave the file untouched.
    part_path.unlink()
    _run_f5("checkout", "--", "changelog.months/2026-10-00.bundle")
    assert b"$Id: " in part_path.read_bytes(), "git did not apply the ident filter"

    # Edit the part inside the keyword. Git's filtered view collapses any
    # $Id: ... $ back to $Id$, so it reports no change; raw bytes differ.
    part_path.write_bytes(
        part_content_unexpanded.replace(b"$Id$", b"$Id: 0000000000 $")
    )
    hidden = _sp_f5.run(
        ["git", "-C", str(tmp_path), "diff", "--quiet"], env=env_f5
    )
    assert hidden.returncode == 0, "fixture no longer hides the edit from git diff"
    try:
        changelog.validate_changelog_cross_form_identity(
            fragment_dir=frag_dir,
            bundle_dir=bundle_dir,
            retraction_path=retraction_path,
        )
    except changelog.FragmentValidationError as exc:
        msg = str(exc)
        assert "2026-10-00.bundle" in msg or str(bundle_dir) in msg, (
            f"part path not in error: {msg}"
        )
        assert VALID_ID_B in msg or "bytes changed" in msg.lower(), (
            f"record id or diagnostic not in error: {msg}"
        )
    else:
        raise AssertionError(
            "ident-expanded bundle part was accepted as unchanged; the "
            "comparator must use raw filesystem bytes, not git-filtered bytes "
            "(AC-B4)"
        )


# ── F6 (AC-B4 SHA-256) ───────────────────────────────────────────────────────


def test_sha256_unchanged_part_passes_without_blob_read(tmp_path: Path) -> None:
    """F6 (AC-B4 SHA-256): in a sha256 repo, an unchanged bundle part passes via
    the sha256 early-exit optimisation (no blob read required).

    Mutation that kills this test: hard-code sha1 in ``_compute_git_object_id``
    → the computed sha1 does not match the stored sha256 blob id → the validator
    falls through to read the blob → the counting runner below records the call
    → the ``cat_file_blob_calls == 0`` assertion fails.
    """
    import os as _os_f6
    import subprocess as _sp_f6

    _GIT_REDIRECTS = (
        "GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE",
        "GIT_OBJECT_DIRECTORY", "GIT_ALTERNATE_OBJECT_DIRECTORIES",
    )
    env_f6 = {k: v for k, v in _os_f6.environ.items() if k not in _GIT_REDIRECTS}
    env_f6.update({
        "GIT_AUTHOR_NAME": "changelog-f6-test",
        "GIT_AUTHOR_EMAIL": "test@invalid",
        "GIT_COMMITTER_NAME": "changelog-f6-test",
        "GIT_COMMITTER_EMAIL": "test@invalid",
        "GIT_AUTHOR_DATE": "2026-01-01T00:00:00+00:00",
        "GIT_COMMITTER_DATE": "2026-01-01T00:00:00+00:00",
    })

    probe = _sp_f6.run(
        ["git", "-C", str(tmp_path), "init", "--object-format=sha256"],
        capture_output=True, text=True, env=env_f6,
    )
    if probe.returncode != 0:
        return  # sha256 not supported; skip gracefully

    def _run_f6(*args: str) -> str:
        r = _sp_f6.run(
            ["git", "-C", str(tmp_path), *args],
            capture_output=True, text=True, env=env_f6,
        )
        if r.returncode != 0:
            raise RuntimeError(f"git {' '.join(args)}: {r.stderr.strip()}")
        return r.stdout.strip()

    _run_f6("config", "user.email", "test@invalid")
    _run_f6("config", "user.name", "changelog-f6-test")

    bundle_dir = tmp_path / "changelog.months"
    bundle_dir.mkdir()
    frag_dir = tmp_path / "changelog.d"
    frag_dir.mkdir()
    retraction_path = tmp_path / "changelog-retractions.toml"

    rec = _bundle_fragment_text()
    part_content = changelog.BUNDLE_SEPARATOR_BYTES + rec.encode("utf-8")
    part_path = bundle_dir / "2026-10-00.bundle"
    part_path.write_bytes(part_content)

    _run_f6("add", ".")
    _run_f6("commit", "-m", "base")
    base_sha = _run_f6("rev-parse", "HEAD")
    _run_f6("update-ref", "refs/remotes/origin/main", base_sha)

    # Patch _git_runner_bytes to count cat-file blob calls.  With correct sha256
    # handling, the early-exit optimisation fires and no blob is read.
    original_bytes_runner = changelog._git_runner_bytes
    cat_file_blob_calls: list[int] = [0]

    def _counting_runner(repo, *args):  # type: ignore[no-untyped-def]
        if args and args[0] == "cat-file" and len(args) >= 2 and args[1] == "blob":
            cat_file_blob_calls[0] += 1
        return original_bytes_runner(repo, *args)

    changelog._git_runner_bytes = _counting_runner
    try:
        changelog.validate_changelog_cross_form_identity(
            fragment_dir=frag_dir,
            bundle_dir=bundle_dir,
            retraction_path=retraction_path,
        )
    except changelog.FragmentValidationError as exc:
        raise AssertionError(
            f"unchanged sha256 bundle part was unexpectedly refused: {exc}"
        ) from exc
    finally:
        changelog._git_runner_bytes = original_bytes_runner

    assert cat_file_blob_calls[0] == 0, (
        f"cat-file blob was called {cat_file_blob_calls[0]} time(s) on an unchanged "
        "part; the sha256 early-exit optimisation did not fire — check that "
        "_compute_git_object_id uses the repo's object format, not hard-coded sha1"
    )


def test_sha256_changed_part_is_refused(tmp_path: Path) -> None:
    """F6 (AC-B4 SHA-256): a one-byte change to a bundle part in a sha256 repo
    is detected and refused via ``validate_changelog_cross_form_identity``."""
    import os as _os_f6b
    import subprocess as _sp_f6b

    _GIT_REDIRECTS = (
        "GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE",
        "GIT_OBJECT_DIRECTORY", "GIT_ALTERNATE_OBJECT_DIRECTORIES",
    )
    env_f6b = {k: v for k, v in _os_f6b.environ.items() if k not in _GIT_REDIRECTS}
    env_f6b.update({
        "GIT_AUTHOR_NAME": "changelog-f6b-test",
        "GIT_AUTHOR_EMAIL": "test@invalid",
        "GIT_COMMITTER_NAME": "changelog-f6b-test",
        "GIT_COMMITTER_EMAIL": "test@invalid",
        "GIT_AUTHOR_DATE": "2026-01-01T00:00:00+00:00",
        "GIT_COMMITTER_DATE": "2026-01-01T00:00:00+00:00",
    })

    probe = _sp_f6b.run(
        ["git", "-C", str(tmp_path), "init", "--object-format=sha256"],
        capture_output=True, text=True, env=env_f6b,
    )
    if probe.returncode != 0:
        return  # sha256 not supported

    def _run_f6b(*args: str) -> str:
        r = _sp_f6b.run(
            ["git", "-C", str(tmp_path), *args],
            capture_output=True, text=True, env=env_f6b,
        )
        if r.returncode != 0:
            raise RuntimeError(f"git {' '.join(args)}: {r.stderr.strip()}")
        return r.stdout.strip()

    _run_f6b("config", "user.email", "test@invalid")
    _run_f6b("config", "user.name", "changelog-f6b-test")

    bundle_dir = tmp_path / "changelog.months"
    bundle_dir.mkdir()
    frag_dir = tmp_path / "changelog.d"
    frag_dir.mkdir()
    retraction_path = tmp_path / "changelog-retractions.toml"

    rec = _bundle_fragment_text()
    part_content = changelog.BUNDLE_SEPARATOR_BYTES + rec.encode("utf-8")
    part_path = bundle_dir / "2026-10-00.bundle"
    part_path.write_bytes(part_content)

    _run_f6b("add", ".")
    _run_f6b("commit", "-m", "base")
    base_sha = _run_f6b("rev-parse", "HEAD")
    _run_f6b("update-ref", "refs/remotes/origin/main", base_sha)

    # Introduce a one-byte change.
    changed = part_content.replace(b"- Bundle test", b"- Changed!!!")
    assert changed != part_content, "replacement did not change the content"
    part_path.write_bytes(changed)

    try:
        changelog.validate_changelog_cross_form_identity(
            fragment_dir=frag_dir,
            bundle_dir=bundle_dir,
            retraction_path=retraction_path,
        )
    except changelog.FragmentValidationError as exc:
        msg = str(exc)
        assert "bytes changed" in msg.lower() or VALID_ID_B in msg, (
            f"error does not name the byte change or record id: {msg}"
        )
    else:
        raise AssertionError(
            "one-byte change to a sha256 bundle part was accepted; "
            "expected FragmentValidationError"
        )


# ── F7 (AC-B4 moved bundled record) ──────────────────────────────────────────


def test_validate_cross_form_refuses_bundled_record_moved_with_date_changed(
    tmp_path: Path,
) -> None:
    """F7 (AC-B4): a bundled record moved into a new added part with its date
    changed is refused, naming the record id and both the original and new part paths.

    This test drove a production fix: the first loop in
    ``validate_changelog_cross_form_identity`` only checks byte immutability for
    parts that still exist at the same path.  A record moved from an old part to
    a newly-added part with changed bytes (e.g. a different ``date``) slipped
    through without refusal.  The fix adds Refusal 1b, which compares record bytes
    in new parts against the merge-base blob record bytes collected during the
    second loop's blob-reading path.
    """
    frag_dir = tmp_path / "changelog.d"
    frag_dir.mkdir()
    bundle_dir = tmp_path / "changelog.months"
    bundle_dir.mkdir()
    retraction_path = tmp_path / "changelog-retractions.toml"

    # Merge-base: old bundle part containing VALID_ID_B with date=2026-10-01.
    old_rec = _bundle_fragment_text()  # VALID_ID_B, date=2026-10-01
    old_part_bytes = changelog.BUNDLE_SEPARATOR_BYTES + old_rec.encode("utf-8")
    # The old part is ABSENT from the current state (not written to bundle_dir).

    # Current state: new bundle part with VALID_ID_B but date=2026-11-01 (changed).
    new_anchor = changelog._compose_fragment_anchor(
        [{"name": "core", "version": "3.0.0"}], "2026-11-01", VALID_ID_B
    )
    new_rec = _bundle_fragment_text(anchor=new_anchor, date="2026-11-01")
    new_part_bytes = changelog.BUNDLE_SEPARATOR_BYTES + new_rec.encode("utf-8")
    new_part = bundle_dir / "2026-11-00.bundle"
    new_part.write_bytes(new_part_bytes)

    old_part_sha = _sha1_obj_id(old_part_bytes)
    merge_base = "deadbeef" * 5

    _GitResult = changelog._GitResult

    def _fake_git_f7(cwd, *args):  # type: ignore[no-untyped-def]
        if args[0] == "rev-parse" and "--show-toplevel" in args:
            return _GitResult(0, str(tmp_path) + "\n", "")
        if args[0] == "merge-base":
            return _GitResult(0, merge_base + "\n", "")
        if args[0] == "rev-parse" and "--show-object-format" in args:
            return _GitResult(0, "sha1\n", "")
        if args[0] == "ls-tree":
            # Base has only the old part at 2026-10-00.bundle.
            line = (
                f"100644 blob {old_part_sha}\t"
                "changelog.months/2026-10-00.bundle"
            )
            return _GitResult(0, line + "\n", "")
        return _GitResult(
            128, "", f"unexpected git call: {' '.join(str(a) for a in args)}"
        )

    original_bytes_runner = changelog._git_runner_bytes

    def _fake_bytes_f7(repo, *args):  # type: ignore[no-untyped-def]
        if args[0] == "cat-file" and args[1] == "-s" and args[2] == old_part_sha:
            return (0, str(len(old_part_bytes)).encode() + b"\n", "")
        if args[0] == "cat-file" and args[1] == "blob" and args[2] == old_part_sha:
            return (0, old_part_bytes, "")
        return original_bytes_runner(repo, *args)

    changelog._git_runner_bytes = _fake_bytes_f7
    try:
        changelog.validate_changelog_cross_form_identity(
            fragment_dir=frag_dir,
            bundle_dir=bundle_dir,
            retraction_path=retraction_path,
            git_runner=_fake_git_f7,
        )
    except changelog.FragmentValidationError as exc:
        msg = str(exc)
        assert VALID_ID_B in msg, (
            f"record id {VALID_ID_B!r} not in error: {msg}"
        )
        assert "2026-11-00.bundle" in msg, (
            f"new part path not in error: {msg}"
        )
        assert "2026-10-00.bundle" in msg, (
            f"original part path not in error: {msg}"
        )
    else:
        raise AssertionError(
            "bundled record moved to a new part with its date changed was accepted; "
            "expected FragmentValidationError naming the record id and both part paths"
        )
    finally:
        changelog._git_runner_bytes = original_bytes_runner


def _validate_against_fake_base(
    tmp_path: Path, base_entries: dict[str, bytes]
) -> None:
    """Run cross-form validation against a fake merge base holding base_entries.

    ``base_entries`` maps repo-relative paths to their merge-base blob bytes;
    the current state is whatever the test wrote under ``tmp_path``.
    """
    _GitResult = changelog._GitResult
    blobs = {_sha1_obj_id(data): data for data in base_entries.values()}
    tree = "".join(
        f"100644 blob {_sha1_obj_id(data)}\t{path}\n"
        for path, data in sorted(base_entries.items())
    )

    def fake_git(cwd, *args):  # type: ignore[no-untyped-def]
        if args[0] == "rev-parse" and "--show-toplevel" in args:
            return _GitResult(0, str(tmp_path) + "\n", "")
        if args[0] == "merge-base":
            return _GitResult(0, "deadbeef" * 5 + "\n", "")
        if args[0] == "rev-parse" and "--show-object-format" in args:
            return _GitResult(0, "sha1\n", "")
        if args[0] == "ls-tree":
            return _GitResult(0, tree, "")
        return _GitResult(128, "", f"unexpected git call: {' '.join(map(str, args))}")

    original_bytes_runner = changelog._git_runner_bytes

    def fake_bytes(repo, *args):  # type: ignore[no-untyped-def]
        if args[0] == "cat-file" and args[2] in blobs:
            data = blobs[args[2]]
            if args[1] == "-s":
                return (0, str(len(data)).encode() + b"\n", "")
            if args[1] == "blob":
                return (0, data, "")
        return original_bytes_runner(repo, *args)

    changelog._git_runner_bytes = fake_bytes
    try:
        changelog.validate_changelog_cross_form_identity(
            fragment_dir=tmp_path / "changelog.d",
            bundle_dir=tmp_path / "changelog.months",
            retraction_path=tmp_path / "changelog-retractions.toml",
            git_runner=fake_git,
        )
    finally:
        changelog._git_runner_bytes = original_bytes_runner


def test_validate_cross_form_accepts_byte_exact_move_of_a_bundled_record(
    tmp_path: Path,
) -> None:
    """AC-B4: a bundled record moved byte-exactly into an added part is accepted.

    Pins the accepting side of Refusal 1b, so the moved-record check cannot
    start refusing a move whose record bytes are unchanged.
    """
    (tmp_path / "changelog.d").mkdir()
    bundle_dir = tmp_path / "changelog.months"
    bundle_dir.mkdir()
    record = changelog.BUNDLE_SEPARATOR_BYTES + _bundle_fragment_text().encode("utf-8")
    (bundle_dir / "2026-10-01.bundle").write_bytes(record)
    _validate_against_fake_base(
        tmp_path, {"changelog.months/2026-10-00.bundle": record}
    )


def test_validate_cross_form_accepts_loose_fragment_deletion_without_a_part(
    tmp_path: Path,
) -> None:
    """AC-B4: deleting a loose fragment in a change that adds no part is accepted."""
    (tmp_path / "changelog.d").mkdir()
    (tmp_path / "changelog.months").mkdir()
    fragment = _fragment_text().encode("utf-8")
    _validate_against_fake_base(tmp_path, {f"changelog.d/{VALID_ID}.md": fragment})


def test_validate_cross_form_refuses_duplicate_id_inside_a_merge_base_part(
    tmp_path: Path,
) -> None:
    """AC-B4: an id twice within one merge-base part is refused, not overwritten.

    Without the refusal the later copy silently replaces the earlier one in
    the moved-record comparison, which then checks the wrong bytes.
    """
    (tmp_path / "changelog.d").mkdir()
    bundle_dir = tmp_path / "changelog.months"
    bundle_dir.mkdir()
    # Distinct dates keep the part in canonical order, so only an id check
    # can catch the repeat.
    first = _bundle_fragment_text(
        date="2026-10-02",
        anchor=changelog._compose_fragment_anchor(
            [{"name": "core", "version": "3.0.0"}], "2026-10-02", VALID_ID_B
        ),
    )
    second = _bundle_fragment_text()
    base_part = b"".join(
        changelog.BUNDLE_SEPARATOR_BYTES + text.encode("utf-8") for text in (first, second)
    )
    (bundle_dir / "2026-10-01.bundle").write_bytes(
        changelog.BUNDLE_SEPARATOR_BYTES + second.encode("utf-8")
    )
    try:
        _validate_against_fake_base(
            tmp_path, {"changelog.months/2026-10-00.bundle": base_part}
        )
    except changelog.FragmentValidationError as exc:
        message = str(exc)
        assert "2026-10-00.bundle" in message, message
        cause = exc.__cause__
        assert isinstance(cause, changelog.DuplicateRecordIdError), message
        assert VALID_ID_B in str(cause), str(cause)
    else:
        raise AssertionError("a merge-base part holding one id twice was accepted")

# ── F8 (AC-B6 oversized fragment) ────────────────────────────────────────────


def test_compact_leaves_oversized_fragment_loose(tmp_path: Path, monkeypatch) -> None:
    """F8 (AC-B6): compact_month reports a fragment too large for a part and
    leaves it as a loose file rather than bundling it.

    Patches ``MAX_BUNDLE_BYTES`` to one byte below the fragment's record size so
    the oversized check at ``changelog.py`` lines 2783-2791 fires.  The fragment
    must still exist afterwards, no part may be written, and stderr must name the
    fragment as oversized.
    """
    import io as _io_f8

    frag_dir = tmp_path / "changelog.d"
    frag_dir.mkdir()
    bundle_dir = tmp_path / "changelog.months"
    bundle_dir.mkdir()

    fid = "f8000001-0001-4001-8001-f80000000001"
    anchor = changelog._compose_fragment_anchor(
        [{"name": "core", "version": "3.0.0"}], "2026-12-01", fid
    )
    text = _fragment_text(
        fragment_id=fid,
        anchor=anchor,
        date="2026-12-01",
        packages='[[packages]]\nname = "core"\nversion = "3.0.0"',
    )
    frag_path = frag_dir / f"{fid}.md"
    frag_path.write_text(text, encoding="utf-8")

    raw = frag_path.read_bytes()
    record_size = len(changelog.BUNDLE_SEPARATOR_BYTES) + len(raw)
    # Set the bound one byte below the record's own size.
    monkeypatch.setattr(changelog, "MAX_BUNDLE_BYTES", record_size - 1)

    captured_stderr = _io_f8.StringIO()
    monkeypatch.setattr(sys, "stderr", captured_stderr)

    created, deleted = changelog.compact_month(
        "2026-12",
        fragment_dir=frag_dir,
        bundle_dir=bundle_dir,
        released_versions={"core": {"3.0.0"}},
    )

    stderr_text = captured_stderr.getvalue()

    assert frag_path.exists(), (
        "oversized fragment was deleted despite being too large for a bundle part"
    )
    assert not list(bundle_dir.iterdir()), (
        "a bundle part was written even though every fragment is oversized"
    )
    assert created == [] and deleted == [], (
        f"compact_month returned non-empty lists for an all-oversized run: "
        f"created={created!r}, deleted={deleted!r}"
    )
    assert (
        fid in stderr_text or "too large" in stderr_text or "oversized" in stderr_text
    ), (
        f"oversized fragment not reported in stderr: {stderr_text!r}"
    )
