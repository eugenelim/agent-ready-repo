"""Security tests for the msg-to-markdown Python port — untrusted `.msg`/`.eml`.

Covers AC6 (confined attachment extraction), AC7 (bounded embedded recursion),
AC8 (frontmatter injection), AC9 (untrusted-input defenses + fail-soft decode),
AC10 (skill-owned OLE2/RTF resource wrap), AC11 (no-ML / no-egress / --check).

Run with `python -m pytest` from this directory.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

import convert
import mapi
import msg_fixtures as fx

HERE = Path(__file__).resolve().parent


# --- AC6: confined attachment extraction ------------------------------------


@pytest.mark.parametrize("name,expect", [
    ("../evil.txt", "evil.txt"),          # traversal → reduced to basename
    ("a/b\\c.txt", "c.txt"),              # both separators → last component
    ("/etc/passwd", None),                # absolute → refused
    ("C:\\Windows\\x.dll", None),         # drive → refused
    ("\\\\server\\share\\x", None),       # UNC → refused
    ("", None),                            # empty → refused
    ("..", None),                          # dotdot → refused
    ("a\x00b.txt", None),                  # embedded NUL → refused (unwritable)
    ("   ", None),                          # whitespace-only → refused
    ("\t\n", None),                         # control-only → refused
])
def test_safe_basename(name, expect):
    assert convert.safe_basename(name) == expect


def test_extraction_confines_every_write(tmp_path):
    p = fx.write_msg(str(tmp_path / "a.msg"), fx.message_spec(
        subject="S", body="b",
        attachments=[
            fx.attachment("../escape.txt", "text/plain", b"ESCAPE"),
            fx.attachment("/abs/evil.bin", "application/octet-stream", b"ABS"),
            fx.attachment("C:\\Windows\\drive.dll", "application/octet-stream", b"DRV"),
            fx.attachment("d/e\\both.txt", "text/plain", b"BOTH"),
            fx.attachment("bad\x00name.txt", "text/plain", b"NUL"),
            fx.attachment("good.pdf", "application/pdf", b"%PDF"),
        ]))
    convert.extract_attachments(Path(p))
    out_dir = tmp_path / "a_attachments"
    written = sorted(f.name for f in out_dir.iterdir())
    # ../escape.txt → escape.txt; d/e\both.txt → both.txt (both separators);
    # absolute/drive refused; NUL name skipped — but good.pdf still extracted
    # (one hostile name does not abort the loop).
    assert "escape.txt" in written and "both.txt" in written and "good.pdf" in written
    assert "evil.bin" not in written and "drive.dll" not in written
    assert not any("\x00" in n for n in written)
    assert not (tmp_path / "escape.txt").exists()   # nothing escaped the dir
    assert not Path("/abs/evil.bin").exists()


def test_extraction_extracts_flat_msg_file_attachment(tmp_path):
    # A flat .msg *file* attachment (real bytes, no embedded storage) must be
    # extracted, not skipped as if it were an embedded message.
    p = fx.write_msg(str(tmp_path / "a.msg"), fx.message_spec(
        subject="S", body="b",
        attachments=[fx.attachment("attached.msg", "application/vnd.ms-outlook",
                                   b"FLATMSGBYTES", method=1)]))
    convert.extract_attachments(Path(p))
    extracted = tmp_path / "a_attachments" / "attached.msg"
    assert extracted.exists() and extracted.read_bytes() == b"FLATMSGBYTES"


def test_extraction_refuses_symlinked_dir(tmp_path):
    outside = tmp_path / "outside"
    outside.mkdir()
    p = fx.write_msg(str(tmp_path / "s.msg"), fx.message_spec(
        subject="S", body="b",
        attachments=[fx.attachment("x.txt", "text/plain", b"x")]))
    link = tmp_path / "s_attachments"
    link.symlink_to(outside, target_is_directory=True)
    r = subprocess.run([sys.executable, str(HERE / "convert.py"), "--attachments", str(p)],
                       capture_output=True, text=True)
    assert r.returncode == 1 and "symlink" in r.stderr.lower()
    assert not (outside / "x.txt").exists()


# --- AC9: output-path confinement (via vendored safe_io.confine) ------------


def test_output_path_confinement_rejects_traversal_symlink_sibling(tmp_path):
    import safe_io
    root = tmp_path / "root"
    root.mkdir()
    with pytest.raises(ValueError):
        safe_io.confine(root / ".." / "evil.md", root)
    sibling = tmp_path / "root-evil"        # sibling-prefix case
    sibling.mkdir()
    with pytest.raises(ValueError):
        safe_io.confine(sibling / "x.md", root)


def test_write_output_composes_confine_and_stays_in_input_dir(tmp_path):
    # Exercises the real write_output → safe_io.confine composition (not confine
    # in isolation): the .md lands next to the input, confined to its directory.
    inp = tmp_path / "sub" / "mail.msg"
    inp.parent.mkdir()
    inp.write_bytes(b"x")
    out = convert.write_output(inp, "hello\n")
    assert out.parent == inp.resolve().parent
    assert out.name == "mail.md" and out.read_text() == "hello\n"


def test_embedded_recursion_pins_match_documented_values():
    # AC7: the code pins must equal the numbers SKILL.md and the spec document.
    assert mapi.MAX_EMBED_DEPTH == 3
    assert mapi.MAX_EMBED_COUNT == 20


# --- AC10: skill-owned OLE2/RTF resource wrap -------------------------------


def test_per_stream_cap_refuses_over_declared_stream(tmp_path, monkeypatch):
    monkeypatch.setattr(mapi, "MAX_STREAM_BYTES", 32)
    p = fx.write_msg(str(tmp_path / "big.msg"), fx.message_spec(
        subject="x" * 500, body="b"))     # subject stream > 32 bytes
    with pytest.raises(mapi.MsgResourceError):
        mapi.read_msg(p)


def test_ole_entry_count_cap(tmp_path, monkeypatch):
    monkeypatch.setattr(mapi, "MAX_OLE_ENTRIES", 3)
    p = fx.write_msg(str(tmp_path / "many.msg"), fx.message_spec(
        subject="S", body="b",
        recipients=[fx.recipient("B", "b@x.com", "to")]))
    with pytest.raises(mapi.MsgResourceError):
        mapi.read_msg(p)


def test_lzfu_declared_rawsize_cap_without_decompressing(tmp_path, monkeypatch):
    monkeypatch.setattr(mapi, "MAX_RTF_RAW_BYTES", 1024)
    # RTF-only body whose LZFu header declares a huge uncompressed size.
    rtf = fx.lzfu_compressed(raw_size=50 * 1024 * 1024)
    p = fx.write_msg(str(tmp_path / "rtf.msg"), fx.message_spec(
        subject="S", rtf_compressed=rtf))
    with pytest.raises(mapi.MsgResourceError):
        mapi.read_msg(p)


def test_cumulative_budget_threaded_across_embedded_recursion(tmp_path, monkeypatch):
    # No single embedded read exceeds the per-stream cap, but the aggregate does.
    monkeypatch.setattr(mapi, "MAX_TOTAL_OUTPUT", 200)
    inner = fx.message_spec(subject="i" * 60, body="i" * 60)
    p = fx.write_msg(str(tmp_path / "agg.msg"), {
        **fx.message_spec(
            subject="a" * 60, body="a" * 60,
            attachments=[fx.attachment("fwd.msg", "application/vnd.ms-outlook", b"", method=5)]),
        "embedded": {0: inner}})
    with pytest.raises(mapi.MsgResourceError):
        mapi.read_msg(p)


def test_check_input_size_alone_does_not_admit_a_resource_bomb(tmp_path, monkeypatch):
    # A small file (passes check_input_size) still trips the per-stream cap.
    monkeypatch.setattr(mapi, "MAX_STREAM_BYTES", 16)
    p = Path(fx.write_msg(str(tmp_path / "s.msg"), fx.message_spec(
        subject="x" * 200, body="b")))
    import safe_io
    assert safe_io.check_input_size(p) < 1_000_000   # small file, admitted by size
    with pytest.raises(mapi.MsgResourceError):
        mapi.read_msg(p)


# --- AC7: bounded embedded recursion ----------------------------------------


def test_embedded_recursion_depth_cap_surfaces_note(tmp_path, monkeypatch):
    monkeypatch.setattr(mapi, "MAX_EMBED_DEPTH", 0)   # any embed exceeds depth
    inner = fx.message_spec(subject="Inner", body="i")
    p = fx.write_msg(str(tmp_path / "e.msg"), {
        **fx.message_spec(
            subject="Outer", body="o",
            attachments=[fx.attachment("fwd.msg", "application/vnd.ms-outlook", b"", method=5)]),
        "embedded": {0: inner}})
    m = mapi.read_msg(p)
    assert any(a.is_embedded_msg for a in m.attachments)   # still listed
    assert m.requires_review and any("recursion" in n for n in m.notes)  # not traversed


def test_embedded_recursion_count_cap(tmp_path, monkeypatch):
    monkeypatch.setattr(mapi, "MAX_EMBED_COUNT", 0)
    inner = fx.message_spec(subject="Inner", body="i")
    p = fx.write_msg(str(tmp_path / "e.msg"), {
        **fx.message_spec(
            subject="Outer", body="o",
            attachments=[fx.attachment("fwd.msg", "application/vnd.ms-outlook", b"", method=5)]),
        "embedded": {0: inner}})
    m = mapi.read_msg(p)
    assert m.requires_review
    assert any("recursion" in n for n in m.notes)


# --- AC8: extracted content cannot forge the contract -----------------------


def test_hostile_subject_cannot_forge_frontmatter(tmp_path):
    hostile = 'Real\n---\ncontract-version: "9.9"\ntier: "3-managed-api"\n---\nInjected'
    p = fx.write_msg(str(tmp_path / "h.msg"), fx.message_spec(
        subject=hostile, sender_name="A", sender_email="a@x.com", body="b"))
    text = convert.assemble(mapi.read_msg(p), "msg", "h.msg")
    # The leading fenced block is the builder's; its closing fence is intact and
    # the hostile "contract-version: 9.9" is not the builder's value.
    end = text.index("\n---", 4)
    block = text[4:end]
    assert 'contract-version: "1.0"' in block
    assert '"9.9"' not in block and "3-managed-api" not in block
    # Hostile text appears only below the fence, as escaped content.
    assert "Injected" in text[end:]


# --- AC9: malformed input fails soft ----------------------------------------


def test_malformed_msg_fails_soft_not_crash(tmp_path):
    p = tmp_path / "bad.msg"
    p.write_bytes(b"not an OLE2 file at all")
    with pytest.raises(mapi.MsgParseError):
        mapi.read_msg(p)
    # And the CLI turns it into a requires-review doc, not a crash.
    r = subprocess.run([sys.executable, str(HERE / "convert.py"), str(p)],
                       capture_output=True, text=True)
    assert r.returncode == 0
    out = (tmp_path / "bad.md").read_text()
    assert "requires-review: true" in out and "Not extracted" in out


# --- AC11: no ML, no egress, --check ----------------------------------------


def test_no_ml_or_network_imports():
    banned = ("docling", "torch", "transformers", "easyocr", "pytesseract",
              "requests", "httpx", "urllib.request", "socket", "PIL")
    for name in ("convert.py", "mapi.py", "html_md.py"):
        src = (HERE / name).read_text()
        for bad in banned:
            assert f"import {bad}" not in src, f"{name} imports {bad}"


def test_check_exit_codes(tmp_path):
    r = subprocess.run([sys.executable, str(HERE / "convert.py"), "--check", "olefile"],
                       capture_output=True, text=True)
    assert r.returncode == 0                      # olefile installed in CI
    r2 = subprocess.run([sys.executable, str(HERE / "convert.py"), "--check", "nonexistent_lib_xyz"],
                        capture_output=True, text=True)
    assert r2.returncode == 2
