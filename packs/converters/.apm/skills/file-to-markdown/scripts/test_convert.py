"""Tests for convert.py — the tiered document surface.

Covers the dispatch + contract-wrapping + confined write,
Tier-0 PDF, Tier-0 Office lib + stdlib paths, the D7 formats, the Docling in-process identity, and
the no-ML property. Unit tests exercise the pure extractors; the E2E
tests spawn the documented `python scripts/convert.py <file>` invocation.

Run with `python -m pytest` from this directory.
"""
from __future__ import annotations

import builtins
import io
import subprocess
import sys
import types
import zipfile
from pathlib import Path

import pytest

import contract
import convert
import safe_io

HERE = Path(__file__).resolve().parent
SAMPLE_DOCX = HERE.parent / "evals" / "files" / "sample.docx"


# --- fixtures / helpers -----------------------------------------------------


def make_pdf(text: str) -> bytes:
    """A minimal single-page digital PDF with an extractable text layer.

    Pure-Python (correct xref offsets computed at build time) so no generation
    dependency is needed and no binary fixture is committed."""
    objs = [
        b"<</Type/Catalog/Pages 2 0 R>>",
        b"<</Type/Pages/Kids[3 0 R]/Count 1>>",
        b"<</Type/Page/Parent 2 0 R/MediaBox[0 0 612 792]/Contents 4 0 R"
        b"/Resources<</Font<</F1 5 0 R>>>>>>",
    ]
    stream = b"BT /F1 24 Tf 72 700 Td (" + text.encode("latin-1") + b") Tj ET"
    objs.append(b"<</Length " + str(len(stream)).encode() + b">>stream\n"
                + stream + b"\nendstream")
    objs.append(b"<</Type/Font/Subtype/Type1/BaseFont/Helvetica>>")
    out = io.BytesIO()
    out.write(b"%PDF-1.4\n")
    offsets = []
    for i, body in enumerate(objs, 1):
        offsets.append(out.tell())
        out.write(str(i).encode() + b" 0 obj" + body + b"endobj\n")
    xref = out.tell()
    out.write(b"xref\n0 " + str(len(objs) + 1).encode() + b"\n0000000000 65535 f \n")
    for off in offsets:
        out.write(("%010d 00000 n \n" % off).encode())
    out.write(b"trailer<</Size " + str(len(objs) + 1).encode()
              + b"/Root 1 0 R>>\nstartxref\n" + str(xref).encode() + b"\n%%EOF")
    return out.getvalue()


def write_zip(path: Path, members: dict[str, bytes], stored=False) -> None:
    comp = zipfile.ZIP_STORED if stored else zipfile.ZIP_DEFLATED
    with zipfile.ZipFile(path, "w", comp) as zf:
        for name, data in members.items():
            zf.writestr(name, data)


_MIN_DOCX = {
    "[Content_Types].xml": b'<?xml version="1.0"?><Types/>',
    "word/document.xml": (
        b'<?xml version="1.0"?>'
        b'<w:document xmlns:w="http://schemas.openxmlformats.org/'
        b'wordprocessingml/2006/main"><w:body><w:p><w:r><w:t>'
        b"Hello from stdlib docx</w:t></w:r></w:p></w:body></w:document>"
    ),
}


@pytest.fixture
def no_docling(monkeypatch):
    """Make any `import docling[...]` raise, proving the Tier-0 paths never
    touch it (the locked-down-org / no-ML property)."""
    real_import = builtins.__import__

    def fake(name, *a, **k):
        if name == "docling" or name.startswith("docling."):
            raise ImportError("docling blocked for test")
        return real_import(name, *a, **k)

    monkeypatch.setattr(builtins, "__import__", fake)


def install_fake_docling(monkeypatch, markdown: str):
    mod = types.ModuleType("docling")
    dc_mod = types.ModuleType("docling.document_converter")

    class _FakeDoc:
        def export_to_markdown(self):
            return markdown

    class _FakeResult:
        document = _FakeDoc()

    class DocumentConverter:
        def convert(self, _path):
            return _FakeResult()

    dc_mod.DocumentConverter = DocumentConverter
    monkeypatch.setitem(sys.modules, "docling", mod)
    monkeypatch.setitem(sys.modules, "docling.document_converter", dc_mod)


def frontmatter_and_body(text: str):
    """A naive frontmatter parser: the leading block is between the first two
    `---` fences; everything after is body."""
    lines = text.splitlines()
    assert lines[0] == "---"
    end = lines.index("---", 1)
    return lines[1:end], lines[end + 1:]


# --- T3: dispatch, wrapping, confinement, injection -------------------------


def test_dispatch_routes_known_ext(monkeypatch):
    assert convert._EXTRACTORS[".csv"] is convert._extract_csv
    assert convert._EXTRACTORS[".pdf"] is convert._extract_pdf


def test_dispatch_falls_through_to_docling(monkeypatch):
    sentinel = object()
    monkeypatch.setattr(convert, "_extract_docling", lambda p: sentinel)
    assert convert.dispatch(Path("mystery.xls")) is sentinel


def test_write_output_confined(tmp_path):
    src = tmp_path / "in.txt"
    src.write_text("x")
    out = convert.write_output(src, "hello")
    assert out == (tmp_path / "in.md").resolve()
    assert out.read_text() == "hello"


def test_write_output_routes_through_confine(tmp_path, monkeypatch):
    src = tmp_path / "in.txt"
    src.write_text("x")

    def boom(path, root):
        raise ValueError("confine called")

    monkeypatch.setattr(safe_io, "confine", boom)
    with pytest.raises(ValueError, match="confine called"):
        convert.write_output(src, "hello")


def test_full_document_body_injection_is_content_not_contract(tmp_path):
    """A body containing `---` and a forged `contract-version:` line is
    read as content — a frontmatter parser sees only the builder's leading
    block."""
    hostile_body = "Intro paragraph.\n\n---\ncontract-version: \"9.9\"\ntier: \"3-managed-api\"\n\nMore."
    result = convert.ExtractResult(
        body=hostile_body, tier=contract.TIER_0, content_type="pdf",
        confidence="high", requires_review=False,
    )
    # Assert on the on-disk artifact — the assemble+write path.
    out = convert.write_output(tmp_path / "in.pdf", convert.assemble(result, "in.pdf"))
    fm, body = frontmatter_and_body(out.read_text())
    assert 'contract-version: "1.0"' in fm
    assert not any('9.9' in ln for ln in fm)
    assert any('contract-version: "9.9"' in ln for ln in body)


# --- T4: Tier-0 PDF ---------------------------------------------------------


def test_extract_pdf_digital(tmp_path):
    pdf = tmp_path / "doc.pdf"
    pdf.write_bytes(make_pdf(
        "Hello Tier Zero PDF extraction here with plenty of real words in the "
        "body so the sparse text threshold is comfortably cleared for this test"
    ))
    r = convert._extract_pdf(pdf)
    assert r.tier == contract.TIER_0
    assert "Hello Tier Zero PDF" in r.body
    assert r.confidence == "high"
    assert r.requires_review is False


def test_extract_pdf_no_ml(tmp_path, no_docling):
    pdf = tmp_path / "doc.pdf"
    pdf.write_bytes(make_pdf("No docling should be imported for this path"))
    r = convert._extract_pdf(pdf)  # would raise if it imported docling
    assert r.tier == contract.TIER_0


def test_extract_pdf_sparse_escalates(tmp_path):
    pdf = tmp_path / "scan.pdf"
    pdf.write_bytes(make_pdf("Hi"))  # one word, below the sparse threshold
    r = convert._extract_pdf(pdf)
    assert r.confidence == "low"
    assert r.requires_review is True
    assert r.escalation == contract.TIER_1
    # The escalation target is an observable-output contract: it must reach
    # the emitted frontmatter, not just the ExtractResult.
    fm, _ = frontmatter_and_body(convert.assemble(r, "scan.pdf"))
    assert f'escalation-target: "{contract.TIER_1}"' in fm


def test_extract_pdf_missing_lib_degrades(tmp_path, monkeypatch):
    pdf = tmp_path / "doc.pdf"
    pdf.write_bytes(make_pdf("some text here for the body of it"))
    monkeypatch.setattr(convert, "_lib_available", lambda name: False)
    r = convert._extract_pdf(pdf)
    assert r.requires_review is True
    assert r.escalation == contract.TIER_1
    assert "pypdf" in r.body


def test_extract_pdf_page_ceiling(tmp_path, monkeypatch):
    pdf = tmp_path / "doc.pdf"
    pdf.write_bytes(make_pdf("a few words in the body here"))
    monkeypatch.setattr(convert, "MAX_PDF_PAGES", 0)
    r = convert._extract_pdf(pdf)
    assert r.requires_review is True
    assert "ceiling" in r.body


# --- T5: Tier-0 Office (lib + stdlib) ---------------------------------------


def test_extract_docx_lib(tmp_path):
    docx = pytest.importorskip("docx")
    p = tmp_path / "d.docx"
    doc = docx.Document()
    doc.add_paragraph("Hello from python-docx")
    doc.save(str(p))
    r = convert._extract_docx(p)
    assert r.tier == contract.TIER_0
    assert "Hello from python-docx" in r.body
    assert r.confidence == "high"


def test_extract_docx_stdlib(tmp_path, monkeypatch):
    p = tmp_path / "d.docx"
    write_zip(p, _MIN_DOCX)
    monkeypatch.setattr(convert, "_lib_available", lambda name: False)
    r = convert._extract_docx(p)
    assert "Hello from stdlib docx" in r.body
    assert r.confidence == "medium"


def test_extract_xlsx_lib(tmp_path):
    openpyxl = pytest.importorskip("openpyxl")
    p = tmp_path / "s.xlsx"
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(["Alpha", "Beta"])
    ws.append([1, 2])
    wb.save(str(p))
    r = convert._extract_xlsx(p)
    assert "Alpha" in r.body and "Beta" in r.body
    assert r.confidence == "high"


def test_extract_xlsx_stdlib(tmp_path, monkeypatch):
    p = tmp_path / "s.xlsx"
    write_zip(p, {
        "[Content_Types].xml": b'<?xml version="1.0"?><Types/>',
        "xl/sharedStrings.xml": (
            b'<?xml version="1.0"?>'
            b'<sst xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
            b"<si><t>Alpha</t></si><si><t>Beta</t></si></sst>"
        ),
        "xl/worksheets/sheet1.xml": (
            b'<?xml version="1.0"?>'
            b'<worksheet xmlns="http://schemas.openxmlformats.org/'
            b'spreadsheetml/2006/main"><sheetData><row>'
            b'<c t="s"><v>0</v></c><c><v>42</v></c></row></sheetData></worksheet>'
        ),
    })
    monkeypatch.setattr(convert, "_lib_available", lambda name: False)
    r = convert._extract_xlsx(p)
    assert "Alpha" in r.body and "42" in r.body
    assert r.confidence == "medium"


def test_extract_pptx_lib(tmp_path):
    pptx = pytest.importorskip("pptx")
    p = tmp_path / "p.pptx"
    prs = pptx.Presentation()
    slide = prs.slides.add_slide(prs.slide_layouts[5])
    slide.shapes.title.text = "Slide heading text"
    prs.save(str(p))
    r = convert._extract_pptx(p)
    assert "Slide heading text" in r.body
    assert r.confidence == "high"


def test_extract_pptx_stdlib(tmp_path, monkeypatch):
    p = tmp_path / "p.pptx"
    write_zip(p, {
        "[Content_Types].xml": b'<?xml version="1.0"?><Types/>',
        "ppt/slides/slide1.xml": (
            b'<?xml version="1.0"?>'
            b'<sld xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">'
            b"<a:t>Stdlib slide text</a:t></sld>"
        ),
    })
    monkeypatch.setattr(convert, "_lib_available", lambda name: False)
    r = convert._extract_pptx(p)
    assert "Stdlib slide text" in r.body
    assert r.confidence == "medium"


def test_office_row_ceiling(tmp_path, monkeypatch):
    openpyxl = pytest.importorskip("openpyxl")
    p = tmp_path / "s.xlsx"
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(["a"])
    ws.append(["b"])
    ws.append(["c"])
    wb.save(str(p))
    monkeypatch.setattr(convert, "MAX_SHEET_ROWS", 1)
    r = convert._extract_xlsx(p)
    assert "truncated" in r.body
    # A row-truncated sheet is not fully extracted — it must be flagged.
    assert r.requires_review is True
    assert r.confidence == "low"


def test_office_guard_order_bomb_renamed_docx(tmp_path):
    """A decompression-bomb zip renamed `.docx` is still refused by the docx
    parser's own zip guard (each parser applies its own format guard)."""
    p = tmp_path / "evil.docx"
    write_zip(p, {"word/document.xml": b"0" * 5_000_000})  # huge ratio
    r = convert._extract_docx(p)
    assert r.requires_review is True
    assert "bomb" in r.body


def test_office_corrupt_zip_renamed_docx_is_flagged(tmp_path):
    """A non-zip file renamed `.docx` is refused as a flagged result, not a
    bare BadZipFile crash."""
    p = tmp_path / "corrupt.docx"
    p.write_bytes(b"this is plainly not a zip archive")
    r = convert._extract_docx(p)
    assert r.requires_review is True
    assert "zip" in r.body.lower()


def test_office_lib_path_rejects_dtd(tmp_path):
    """The ordinary-lib path is DTD-gated before the lib's transitive lxml
    parses — a DOCTYPE in any XML member is refused."""
    if not convert._lib_available("docx"):
        pytest.skip("python-docx not installed")
    p = tmp_path / "xxe.docx"
    write_zip(p, {
        "[Content_Types].xml": b'<?xml version="1.0"?><Types/>',
        "word/document.xml": (
            b'<?xml version="1.0"?>'
            b'<!DOCTYPE r [<!ENTITY x SYSTEM "file:///etc/passwd">]>'
            b'<w:document xmlns:w="http://schemas.openxmlformats.org/'
            b'wordprocessingml/2006/main"><w:body/></w:document>'
        ),
    })
    r = convert._extract_docx(p)
    assert r.requires_review is True
    assert "XML safety" in r.body


# --- T6: D7 formats ---------------------------------------------------------


def test_extract_html(tmp_path):
    p = tmp_path / "page.html"
    p.write_text("<html><body><h1>Title</h1><p>Para one.</p>"
                 "<script>ignored()</script><p>Para two.</p></body></html>")
    r = convert._extract_html(p)
    assert "Title" in r.body and "Para one." in r.body and "Para two." in r.body
    assert "ignored" not in r.body
    assert r.tier == contract.TIER_0


def test_extract_csv(tmp_path):
    p = tmp_path / "data.csv"
    p.write_text("name,age\nAda,36\nGrace,44\n")
    r = convert._extract_csv(p)
    assert "| name | age |" in r.body
    assert "| Ada | 36 |" in r.body
    assert r.content_type == "csv"


def test_extract_tsv(tmp_path):
    p = tmp_path / "data.tsv"
    p.write_text("name\tage\nAda\t36\n")
    r = convert._extract_csv(p)
    assert "| name | age |" in r.body
    assert r.content_type == "tsv"


def test_extract_csv_row_ceiling(tmp_path, monkeypatch):
    p = tmp_path / "big.csv"
    p.write_text("a\nb\nc\nd\n")
    monkeypatch.setattr(convert, "MAX_CSV_ROWS", 1)
    r = convert._extract_csv(p)
    assert r.requires_review is True
    assert "ceiling" in r.body


def test_extract_epub(tmp_path):
    p = tmp_path / "book.epub"
    write_zip(p, {
        "mimetype": b"application/epub+zip",
        "OEBPS/ch1.xhtml": b"<html><body><p>Chapter one text.</p></body></html>",
    })
    r = convert._extract_epub(p)
    assert "Chapter one text." in r.body
    assert r.content_type == "epub"


def test_extract_odt(tmp_path):
    p = tmp_path / "doc.odt"
    write_zip(p, {
        "content.xml": (
            b'<?xml version="1.0"?>'
            b'<office:document-content '
            b'xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0" '
            b'xmlns:text="urn:oasis:names:tc:opendocument:xmlns:text:1.0">'
            b"<office:body><text:h>Heading</text:h>"
            b"<text:p>Paragraph body.</text:p></office:body>"
            b"</office:document-content>"
        ),
    })
    r = convert._extract_odf(p)
    assert "Heading" in r.body and "Paragraph body." in r.body
    assert r.content_type == "odt"


def test_extract_odf_rejects_dtd(tmp_path):
    """A DTD in content.xml is refused as a flagged result, consistent with the
    Office path."""
    p = tmp_path / "xxe.odt"
    write_zip(p, {
        "content.xml": (
            b'<?xml version="1.0"?>'
            b'<!DOCTYPE r [<!ENTITY x SYSTEM "file:///etc/passwd">]>'
            b'<office:document-content '
            b'xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0"/>'
        ),
    })
    r = convert._extract_odf(p)
    assert r.requires_review is True
    assert "XML safety" in r.body


def test_extract_eml(tmp_path):
    p = tmp_path / "mail.eml"
    p.write_bytes(
        b"From: a@example.com\r\nTo: b@example.com\r\nSubject: Hello\r\n"
        b"Content-Type: text/plain\r\n\r\nThis is the message body.\r\n"
    )
    r = convert._extract_eml(p)
    assert "**Subject:** Hello" in r.body
    assert "This is the message body." in r.body
    assert r.content_type == "eml"


def test_extract_eml_html_body_is_reduced(tmp_path):
    """An HTML-only email body is reduced to text (tags stripped)."""
    p = tmp_path / "html.eml"
    p.write_bytes(
        b"From: x@y.z\r\nSubject: HTML mail\r\n"
        b"Content-Type: text/html; charset=utf-8\r\n\r\n"
        b"<html><body><p>Hello <b>bold</b> world.</p>"
        b"<script>evil()</script></body></html>\r\n"
    )
    r = convert._extract_eml(p)
    assert "Hello" in r.body and "world." in r.body
    assert "<b>" not in r.body and "evil()" not in r.body


def test_extract_epub_flags_guard_skipped_member(tmp_path):
    """An EPUB member carrying a DTD is skipped by the guard, and the result is
    flagged requires-review rather than silently returning partial text."""
    p = tmp_path / "book.epub"
    write_zip(p, {
        "mimetype": b"application/epub+zip",
        "OEBPS/ok.xhtml": b"<html><body><p>Good chapter.</p></body></html>",
        "OEBPS/xxe.xhtml": (
            b'<!DOCTYPE r [<!ENTITY x SYSTEM "file:///etc/passwd">]>'
            b"<html><body><p>bad</p></body></html>"
        ),
    })
    r = convert._extract_epub(p)
    assert "Good chapter." in r.body
    assert r.requires_review is True
    assert "skipped by a safety guard" in r.body


# --- T7: Docling identity + no-ML -------------------------------------------


def test_docling_body_passed_through_unmodified(tmp_path, monkeypatch):
    """The body handed to the builder equals Docling's export verbatim;
    only the two contract keys are added."""
    docling_md = "# Doc\n\nText with a --- rule\n\ncontract-version: not-real\n"
    install_fake_docling(monkeypatch, docling_md)
    r = convert._extract_docling(tmp_path / "legacy.xls")
    assert r.body == docling_md
    assert r.tier == contract.TIER_2
    doc = convert.assemble(r, "legacy.xls")
    fm, body = frontmatter_and_body(doc)
    assert f'tier: "{contract.TIER_2}"' in fm
    # The body region reproduces Docling's export verbatim (the separator blank
    # line is the only added byte); the exact identity is asserted above.
    assert "\n".join(body).strip() == docling_md.strip()


def test_tier0_paths_import_no_docling(tmp_path, no_docling):
    """Representative Tier-0 extractors run with docling unimportable."""
    (tmp_path / "p.html").write_text("<p>hi there friend</p>")
    assert convert._extract_html(tmp_path / "p.html").tier == contract.TIER_0
    (tmp_path / "d.csv").write_text("a,b\n1,2\n")
    assert convert._extract_csv(tmp_path / "d.csv").tier == contract.TIER_0


# --- E2E: the documented `python scripts/convert.py <file>` invocation -------


def _run(path: Path):
    return subprocess.run(
        [sys.executable, str(HERE / "convert.py"), str(path)],
        capture_output=True, text=True,
    )


def test_e2e_pdf(tmp_path):
    pdf = tmp_path / "report.pdf"
    pdf.write_bytes(make_pdf("End to end PDF extraction body text here"))
    r = _run(pdf)
    assert r.returncode == 0, r.stderr
    assert "OUTPUT:" in r.stdout
    md = (tmp_path / "report.md").read_text()
    assert 'tier: "0-no-ml"' in md
    assert 'contract-version: "1.0"' in md
    assert "End to end PDF extraction" in md


def test_e2e_docx_sample(tmp_path):
    if not SAMPLE_DOCX.exists():
        pytest.skip("sample.docx fixture not present")
    dst = tmp_path / "sample.docx"
    dst.write_bytes(SAMPLE_DOCX.read_bytes())
    r = _run(dst)
    assert r.returncode == 0, r.stderr
    md = (tmp_path / "sample.md").read_text()
    assert 'tier: "0-no-ml"' in md
    assert 'content-type: "docx"' in md


def test_e2e_csv(tmp_path):
    p = tmp_path / "t.csv"
    p.write_text("h1,h2\nv1,v2\n")
    r = _run(p)
    assert r.returncode == 0, r.stderr
    md = (tmp_path / "t.md").read_text()
    assert 'tier: "0-no-ml"' in md
    assert "| h1 | h2 |" in md


def test_e2e_html(tmp_path):
    p = tmp_path / "t.html"
    p.write_text("<html><body><p>End to end HTML.</p></body></html>")
    r = _run(p)
    assert r.returncode == 0, r.stderr
    md = (tmp_path / "t.md").read_text()
    assert 'tier: "0-no-ml"' in md
    assert "End to end HTML." in md


def test_e2e_eml(tmp_path):
    p = tmp_path / "m.eml"
    p.write_bytes(b"From: x@y.z\r\nSubject: E2E\r\n\r\nBody line.\r\n")
    r = _run(p)
    assert r.returncode == 0, r.stderr
    md = (tmp_path / "m.md").read_text()
    assert 'content-type: "eml"' in md
    assert "Body line." in md


def test_e2e_sparse_pdf_warns_and_flags(tmp_path):
    pdf = tmp_path / "scan.pdf"
    pdf.write_bytes(make_pdf("Hi"))  # sparse
    r = _run(pdf)
    assert r.returncode == 0, r.stderr
    assert "WARNING:" in r.stdout and "requires-review" in r.stdout
    md = (tmp_path / "scan.md").read_text()
    assert "requires-review: true" in md
    assert 'escalation-target: "1-agent-vision"' in md


def test_e2e_check_probe():
    r = subprocess.run(
        [sys.executable, str(HERE / "convert.py"), "--check", "pypdf"],
        capture_output=True, text=True,
    )
    assert "pypdf:" in r.stdout
    assert r.returncode in (0, 2)
