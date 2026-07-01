"""Tests for the msg-to-markdown Python port — contract shape, .msg/.eml field
extraction, the HTML→Markdown reducer, and the .eml/MIME fold-in (incl. the
cross-path frontmatter-parity with file-to-markdown's flat .eml route).

Covers AC1, AC4, AC5. Unit tests exercise the extractors + reducer; the E2E
tests spawn the documented `python scripts/convert.py <file>` invocation.

Run with `python -m pytest` from this directory.
"""
from __future__ import annotations

import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import convert
import html_md
import mapi
import msg_fixtures as fx

HERE = Path(__file__).resolve().parent


# --- helpers ----------------------------------------------------------------


def _frontmatter(text: str) -> dict:
    """Parse the leading ---fenced block into a flat dict (nested keys dotted)."""
    assert text.startswith("---\n")
    end = text.index("\n---", 4)
    block = text[4:end]
    out, prefix = {}, ""
    for line in block.splitlines():
        if not line.strip():
            continue
        indent = len(line) - len(line.lstrip())
        key, _, val = line.strip().partition(":")
        val = val.strip().strip('"')
        if val == "":
            prefix = key + "."
        else:
            out[(prefix if indent else "") + key] = val
            if not indent:
                prefix = ""
    return out


# --- AC1: contract shape via the shared builder -----------------------------


def test_msg_frontmatter_carries_unified_contract(tmp_path):
    p = fx.write_msg(str(tmp_path / "m.msg"), fx.message_spec(
        subject="S", sender_name="A", sender_email="a@x.com", body="hi",
        recipients=[fx.recipient("B", "b@x.com", "to")]))
    text = convert.assemble(mapi.read_msg(p), "msg", "m.msg")
    fm = _frontmatter(text)
    for key in ("contract-version", "tier", "source-file", "content-type",
                "ingestion-date", "ingestion-quality.extraction-confidence",
                "ingestion-quality.requires-review"):
        assert key in fm, key
    assert fm["tier"] == "0-no-ml"
    assert fm["content-type"] == "msg"
    assert fm["ingestion-quality.extraction-confidence"] in ("high", "medium", "low")


def test_msg_e2e_documented_invocation(tmp_path):
    p = fx.write_msg(str(tmp_path / "report.msg"), fx.message_spec(
        subject="Q3", sender_name="A", sender_email="a@x.com", body="body text",
        recipients=[fx.recipient("B", "b@x.com", "to")]))
    r = subprocess.run([sys.executable, str(HERE / "convert.py"), str(p)],
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    assert "WROTE:" in r.stdout and "SUMMARY:" in r.stdout
    out = (tmp_path / "report.md").read_text()
    fm = _frontmatter(out)
    assert fm["tier"] == "0-no-ml" and fm["content-type"] == "msg"
    assert "# Q3" in out


# --- AC4: .msg field extraction (no ML) -------------------------------------


def test_sender_and_recipients_by_type(tmp_path):
    p = fx.write_msg(str(tmp_path / "m.msg"), fx.message_spec(
        subject="S", sender_name="Alice", sender_email="alice@x.com", body="b",
        recipients=[fx.recipient("Bob", "bob@x.com", "to"),
                    fx.recipient("Carol", "carol@x.com", "cc"),
                    fx.recipient("Dan", "dan@x.com", "bcc")]))
    m = mapi.read_msg(p)
    assert m.sender_name == "Alice" and m.sender_email == "alice@x.com"
    kinds = {r.email: r.kind for r in m.recipients}
    assert kinds == {"bob@x.com": "to", "carol@x.com": "cc", "dan@x.com": "bcc"}


def test_date_resolution_prefers_delivery_then_submit_then_creation(tmp_path):
    d = datetime(2024, 1, 1, tzinfo=timezone.utc)
    s = datetime(2024, 2, 2, tzinfo=timezone.utc)
    c = datetime(2024, 3, 3, tzinfo=timezone.utc)
    p = fx.write_msg(str(tmp_path / "d.msg"), fx.message_spec(
        subject="S", body="b", delivery=d, submit=s, creation=c))
    assert mapi.read_msg(p).date.startswith("2024-01-01")
    p2 = fx.write_msg(str(tmp_path / "d2.msg"), fx.message_spec(
        subject="S", body="b", submit=s, creation=c))
    assert mapi.read_msg(p2).date.startswith("2024-02-02")
    p3 = fx.write_msg(str(tmp_path / "d3.msg"), fx.message_spec(
        subject="S", body="b", creation=c))
    assert mapi.read_msg(p3).date.startswith("2024-03-03")


def test_importance_decoded(tmp_path):
    p = fx.write_msg(str(tmp_path / "i.msg"), fx.message_spec(
        subject="S", body="b", importance=2))
    assert mapi.read_msg(p).importance == "high"


def test_html_body_preferred_over_plain(tmp_path):
    p = fx.write_msg(str(tmp_path / "h.msg"), fx.message_spec(
        subject="S", body="plain fallback", html="<p>rich</p>"))
    m = mapi.read_msg(p)
    assert m.body_kind == "html" and "rich" in m.body_text


def test_mapi_property_type_decoding_int_time_string():
    # The exact types that crashed msg-parser on py3 (AC4/AC9).
    assert mapi._decode_int(b"\x02\x00\x00\x00") == 2
    assert mapi._decode_time(b"\x00" * 8) is None
    assert mapi._decode_str("Héllo".encode("utf-16-le"), "001F") == "Héllo"
    assert mapi._decode_str(b"caf\xe9", "001E") == "café"  # cp1252


def test_malformed_string_decode_is_non_raising():
    # Odd-length / truncated UTF-16 must degrade, never throw (AC9).
    assert isinstance(mapi._decode_str(b"\x41", "001F"), str)
    assert mapi._decode_int(b"\x01") is None
    assert mapi._decode_time(b"\x01\x02") is None


# --- AC4: HTML → Markdown reducer (stdlib html.parser, not regex) -----------


def test_html_reducer_covers_headings_emphasis_links_lists_tables_entities():
    md = html_md.html_to_markdown(
        "<h2>Title</h2><p><b>bold</b> <i>italic</i> "
        "<a href='http://e/x'>link</a> &amp; more</p>"
        "<ul><li>one</li><li>two</li></ul>"
        "<table><tr><th>A</th><th>B</th></tr><tr><td>1</td><td>2</td></tr></table>")
    assert "## Title" in md
    assert "**bold**" in md and "*italic*" in md
    assert "[link](http://e/x)" in md
    assert "& more" in md  # entity unescaped
    assert "- one" in md and "- two" in md
    assert "| A | B |" in md and "| 1 | 2 |" in md


def test_html_reducer_drops_script_and_style():
    md = html_md.html_to_markdown(
        "<style>.x{color:red}</style><p>keep</p><script>alert(1)</script>")
    assert "keep" in md and "color:red" not in md and "alert" not in md


# --- AC5: .eml / richer MIME + cross-path frontmatter parity ----------------


def _eml_bytes(subject="Notes", extra_headers="", body="Body here.",
               ctype="text/plain"):
    return (f"From: Alice <alice@x.com>\nTo: Bob <bob@x.com>\nCc: Carol <carol@x.com>\n"
            f"Subject: {subject}\nDate: Fri, 1 Mar 2024 12:30:00 +0000\n{extra_headers}"
            f"Content-Type: {ctype}; charset=utf-8\n\n{body}\n").encode("utf-8")


def test_eml_multipart_prefers_plain(tmp_path):
    raw = (b"From: A <a@x.com>\nTo: B <b@x.com>\nSubject: MP\n"
           b'Content-Type: multipart/alternative; boundary="bnd"\n\n'
           b"--bnd\nContent-Type: text/plain\n\nplain part\n"
           b"--bnd\nContent-Type: text/html\n\n<p>html part</p>\n--bnd--\n")
    p = tmp_path / "mp.eml"
    p.write_bytes(raw)
    m = convert.read_eml(p)
    assert m.body_kind == "plain" and "plain part" in m.body_text


def test_eml_nested_rfc822_detected(tmp_path):
    raw = (b"From: A <a@x.com>\nTo: B <b@x.com>\nSubject: Outer\n"
           b'Content-Type: multipart/mixed; boundary="bnd"\n\n'
           b"--bnd\nContent-Type: text/plain\n\nouter body\n"
           b"--bnd\nContent-Type: message/rfc822\n\n"
           b"From: C <c@x.com>\nSubject: Inner\n\ninner body\n--bnd--\n")
    p = tmp_path / "nest.eml"
    p.write_bytes(raw)
    m = convert.read_eml(p)
    assert any(a.is_embedded_msg for a in m.attachments)
    assert "Inner" in m.embedded_subjects


def test_eml_e2e_content_type(tmp_path):
    p = tmp_path / "n.eml"
    p.write_bytes(_eml_bytes())
    r = subprocess.run([sys.executable, str(HERE / "convert.py"), str(p)],
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    out = (tmp_path / "n.md").read_text()
    assert _frontmatter(out)["content-type"] == "eml"


def _load_floor_convert():
    """Load file-to-markdown's convert.py under a distinct module name (both
    skills name the module `convert`). Its sibling `import contract`/`import
    safe_io` resolve to this skill's vendored copies, which are byte-identical
    (AC2), so the contract builder is the same code."""
    import importlib.util

    floor_path = HERE.parent.parent / "file-to-markdown" / "scripts" / "convert.py"
    spec = importlib.util.spec_from_file_location("floor_convert", floor_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_cross_path_frontmatter_parity_with_floor_eml_route(tmp_path):
    """AC5: the same simple .eml through this skill and file-to-markdown's flat
    route yields identical contract frontmatter (ingestion-date excepted — it is
    a timestamp)."""
    floor = _load_floor_convert()
    p = tmp_path / "shared.eml"
    p.write_bytes(_eml_bytes(subject="Shared", body="Same body."))
    floor_text = floor.assemble(floor.dispatch(p), p.name)
    this_text = convert.assemble(convert.read_eml(p), "eml", p.name)

    def _fm_no_date(t):
        d = _frontmatter(t)
        d.pop("ingestion-date", None)
        return d

    assert _fm_no_date(this_text) == _fm_no_date(floor_text)
