"""Tests for safe_io.py — the defensive parsing + confinement helpers.

Covers (XXE-safe XML; decompression-bomb guard on every axis; path-join /
traversal guard; no nested-archive recursion), (output-path confinement,
including the sibling-prefix case), and (input-size ceiling).

Run with `python -m pytest` from this directory.
"""
from __future__ import annotations

import os
import zipfile
from pathlib import Path

import pytest

import safe_io


# --- XXE-safe XML ------------------------------------------------------


def test_parse_xml_reads_plain_xml():
    root = safe_io.parse_xml(b"<r><a>hi</a></r>")
    assert root.find("a").text == "hi"


def test_parse_xml_refuses_external_entity_dtd():
    """An external-entity DTD (XXE) is refused before any resolution."""
    xxe = (
        b'<?xml version="1.0"?>'
        b'<!DOCTYPE r [<!ENTITY x SYSTEM "file:///etc/passwd">]>'
        b"<r>&x;</r>"
    )
    with pytest.raises(safe_io.XmlSafetyError):
        safe_io.parse_xml(xxe)


def test_parse_xml_refuses_internal_entity_dtd():
    """A billion-laughs-style internal-entity DTD is refused (no expansion)."""
    bomb = (
        b'<?xml version="1.0"?>'
        b'<!DOCTYPE lolz [<!ENTITY lol "lol"><!ENTITY lol2 "&lol;&lol;">]>'
        b"<r>&lol2;</r>"
    )
    with pytest.raises(safe_io.XmlSafetyError):
        safe_io.parse_xml(bomb)


def test_parse_xml_refuses_dtd_past_a_fixed_window():
    """A DOCTYPE padded past any fixed prolog window is still refused — the scan
    is whole-buffer, not the first 64 KB."""
    padded = (
        b'<?xml version="1.0"?>' + b"<!-- " + b" " * 200_000 + b" -->"
        + b'<!DOCTYPE r [<!ENTITY x SYSTEM "file:///etc/passwd">]><r/>'
    )
    with pytest.raises(safe_io.XmlSafetyError):
        safe_io.parse_xml(padded)


# --- decompression-bomb guard, per axis --------------------------------


def _write_zip(path: Path, members: dict[str, bytes], compression=zipfile.ZIP_DEFLATED):
    with zipfile.ZipFile(path, "w", compression) as zf:
        for name, data in members.items():
            zf.writestr(name, data)


def test_zip_entry_count_cap(tmp_path):
    z = tmp_path / "many.zip"
    _write_zip(z, {f"f{i}.txt": b"x" for i in range(5)})
    with pytest.raises(safe_io.ZipBombError):
        safe_io.open_safe_zip(z, max_entries=3)


def test_zip_cumulative_bytes_cap(tmp_path):
    z = tmp_path / "big.zip"
    _write_zip(z, {"a.txt": b"a" * 5000, "b.txt": b"b" * 5000})
    with pytest.raises(safe_io.ZipBombError):
        safe_io.open_safe_zip(z, max_total_uncompressed=1000)


def test_zip_ratio_cap(tmp_path):
    z = tmp_path / "bomb.zip"
    # Highly compressible payload → huge declared:compressed ratio.
    _write_zip(z, {"bomb.txt": b"0" * 5_000_000})
    with pytest.raises(safe_io.ZipBombError):
        safe_io.open_safe_zip(z, max_ratio=50)


def test_zip_valid_office_shape_passes(tmp_path):
    z = tmp_path / "ok.zip"
    _write_zip(z, {"word/document.xml": b"<r>hello</r>"})
    with safe_io.open_safe_zip(z) as sz:
        assert sz.read_member("word/document.xml") == b"<r>hello</r>"


def test_zip_read_member_traversal_name_refused(tmp_path):
    """A `../`-prefixed entry name never yields a filesystem path — refused."""
    z = tmp_path / "trav.zip"
    _write_zip(z, {"../evil": b"pwned"})
    with safe_io.open_safe_zip(z) as sz:
        with pytest.raises(safe_io.ZipBombError):
            sz.read_member("../evil")


def test_zip_read_member_nested_archive_refused(tmp_path):
    """The reader never recurses into an embedded archive member."""
    inner = tmp_path / "inner.zip"
    _write_zip(inner, {"a.txt": b"x"})
    z = tmp_path / "outer.zip"
    _write_zip(z, {"nested.zip": inner.read_bytes()}, compression=zipfile.ZIP_STORED)
    with safe_io.open_safe_zip(z) as sz:
        with pytest.raises(safe_io.ZipBombError):
            sz.read_member("nested.zip")


def test_zip_member_byte_cap_catches_understated_size(tmp_path):
    # Incompressible payload so the ratio/cumulative axes pass and the read-time
    # per-member cap is what fires.
    z = tmp_path / "ok.zip"
    _write_zip(z, {"m.bin": os.urandom(10_000)}, compression=zipfile.ZIP_STORED)
    with safe_io.open_safe_zip(z, max_member_bytes=1000) as sz:
        with pytest.raises(safe_io.ZipBombError):
            sz.read_member("m.bin")


def test_zip_cumulative_actual_read_cap(tmp_path):
    """Many members each under the per-member cap but exceeding the cumulative
    cap when actually read are refused (understated-size, multi-member). Built
    on SafeZip directly so the *read-time* cap is what fires, not the declared
    central-directory cap (which open_safe_zip enforces separately)."""
    z = tmp_path / "many.zip"
    _write_zip(z, {f"m{i}.bin": os.urandom(2000) for i in range(5)},
               compression=zipfile.ZIP_STORED)
    sz = safe_io.SafeZip(zipfile.ZipFile(z), max_member_bytes=4000,
                         max_total_uncompressed=5000)
    with sz:
        with pytest.raises(safe_io.ZipBombError):
            for i in range(5):
                sz.read_member(f"m{i}.bin")


def test_harden_untrusted_reads_all_members_and_scans_dtd(tmp_path):
    z = tmp_path / "ok.zip"
    _write_zip(z, {
        "word/document.xml": b"<r>hi</r>",
        "docProps/app.xml": b"<Properties/>",
    })
    with safe_io.open_safe_zip(z) as sz:
        sz.harden_untrusted()  # clean archive: no raise


def test_harden_untrusted_refuses_dtd_in_any_member(tmp_path):
    z = tmp_path / "xxe.zip"
    _write_zip(z, {
        "word/document.xml": (
            b'<!DOCTYPE r [<!ENTITY x SYSTEM "file:///etc/passwd">]><r/>'
        ),
    })
    with safe_io.open_safe_zip(z) as sz:
        with pytest.raises(safe_io.XmlSafetyError):
            sz.harden_untrusted()


def test_harden_untrusted_enforces_member_cap(tmp_path):
    z = tmp_path / "bomb.zip"
    _write_zip(z, {"big.bin": os.urandom(10_000)}, compression=zipfile.ZIP_STORED)
    with safe_io.open_safe_zip(z, max_member_bytes=1000) as sz:
        with pytest.raises(safe_io.ZipBombError):
            sz.harden_untrusted()


# --- output-path confinement -----------------------------------------


def test_confine_accepts_in_root(tmp_path):
    root = tmp_path / "root"
    root.mkdir()
    assert safe_io.confine(root / "out.md", root) == (root / "out.md").resolve()


def test_confine_rejects_parent_traversal(tmp_path):
    root = tmp_path / "root"
    root.mkdir()
    with pytest.raises(ValueError):
        safe_io.confine(root / ".." / "evil.md", root)


def test_confine_rejects_symlink_escape(tmp_path):
    root = tmp_path / "root"
    root.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    link = root / "link"
    link.symlink_to(outside, target_is_directory=True)
    with pytest.raises(ValueError):
        safe_io.confine(link / "evil.md", root)


def test_confine_rejects_sibling_prefix(tmp_path):
    """`root-evil` shares a string prefix with `root` but is not contained —
    the case a naive str.startswith check passes and containment must reject."""
    root = tmp_path / "root"
    root.mkdir()
    sibling = tmp_path / "root-evil"
    sibling.mkdir()
    with pytest.raises(ValueError):
        safe_io.confine(sibling / "out.md", root)


# --- input-size ceiling -----------------------------------------------


def test_check_input_size_refuses_oversized(tmp_path):
    f = tmp_path / "big.bin"
    f.write_bytes(b"x" * 2048)
    with pytest.raises(safe_io.ResourceCeilingError):
        safe_io.check_input_size(f, max_bytes=1024)


def test_check_input_size_accepts_small(tmp_path):
    f = tmp_path / "small.bin"
    f.write_bytes(b"x" * 100)
    assert safe_io.check_input_size(f, max_bytes=1024) == 100
