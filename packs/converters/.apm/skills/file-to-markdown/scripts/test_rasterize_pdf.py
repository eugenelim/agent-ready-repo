"""Tests for rasterize_pdf.py — Tier-1 PDF-page rasterization (AC3, AC4, AC10, AC11).

The rasterizer wraps pdf2image, which is not a repo dependency, so these tests
inject a fake ``pdf2image`` module. The vision read itself is the model's job and
is not unit-tested; everything deterministic around it is.

Run with `python -m pytest` from this directory.
"""
from __future__ import annotations

import importlib.machinery
import sys
import types
from pathlib import Path

import rasterize_pdf as rp


class _FakeImage:
    def __init__(self, nbytes: int = 16, size=(100, 120)):
        self._nbytes = nbytes
        self.size = size

    def save(self, path, format=None):
        Path(path).write_bytes(b"\x89PNG\r\n" + b"0" * self._nbytes)


def _fake_pdf2image(*, pages: int = 3, nbytes: int = 16, record: dict | None = None,
                    size=(100, 120), empty: tuple[int, ...] = ()):
    mod = types.ModuleType("pdf2image")
    mod.__spec__ = importlib.machinery.ModuleSpec("pdf2image", None)

    def pdfinfo_from_path(path, **kw):
        return {"Pages": pages}

    def convert_from_path(path, dpi=200, first_page=None, last_page=None,
                          fmt="ppm", **kw):
        if record is not None:
            record["dpi"] = dpi
        if first_page in empty:
            return []                       # a page that failed to render
        return [_FakeImage(nbytes, size)]

    mod.pdfinfo_from_path = pdfinfo_from_path
    mod.convert_from_path = convert_from_path
    return mod


def _pdf(tmp_path: Path) -> Path:
    p = tmp_path / "scan.pdf"
    p.write_bytes(b"%PDF-1.4 fake")
    return p


# --- AC4: pip-on-demand probe + honest absent-lib degradation --------------


def test_check_reports_absent(monkeypatch, capsys):
    monkeypatch.setattr(rp, "_lib_available", lambda name="pdf2image": False)
    assert rp.cmd_check([]) == 2
    err = capsys.readouterr().err
    assert "pdf2image" in err and "poppler" in err


def test_check_reports_present(monkeypatch):
    monkeypatch.setattr(rp, "_lib_available", lambda name="pdf2image": True)
    assert rp.cmd_check([]) == 0


def test_absent_lib_degrades_no_crash(monkeypatch, tmp_path):
    """AC4: rasterizer absent → status 'unavailable', a clear message naming
    pdf2image + poppler, and no exception. Retaining the Tier-0 output is the
    agent's job, so the script asserts only the no-crash message."""
    monkeypatch.setattr(rp, "_lib_available", lambda name="pdf2image": False)
    res = rp.rasterize(_pdf(tmp_path), tmp_path / "work", output_root=tmp_path)
    assert res.status == "unavailable"
    assert "pdf2image" in res.message and "poppler" in res.message
    # main() surfaces it as a non-crash warning (exit 3)
    rc = rp.main(["--input", str(_pdf(tmp_path)),
                  "--output-dir", str(tmp_path / "work"),
                  "--output-root", str(tmp_path)])
    assert rc == 3


# --- AC3: one image per page ------------------------------------------------


def test_one_image_per_page(monkeypatch, tmp_path):
    monkeypatch.setitem(sys.modules, "pdf2image", _fake_pdf2image(pages=3))
    work = tmp_path / "work"
    res = rp.rasterize(_pdf(tmp_path), work, output_root=tmp_path)
    assert res.status == "ok"
    assert len(res.page_paths) == 3
    assert all(p.exists() and p.parent == work.resolve() for p in res.page_paths)
    manifest = res.manifest_path.read_text()
    assert '"page-0001"' in manifest and '"rasterized-pdf"' in manifest


# --- AC10: multi-axis ceiling ----------------------------------------------


def test_page_cap_refused(monkeypatch, tmp_path):
    monkeypatch.setitem(sys.modules, "pdf2image", _fake_pdf2image(pages=999_999))
    res = rp.rasterize(_pdf(tmp_path), tmp_path / "work", output_root=tmp_path)
    assert res.status == "refused" and "page" in res.message.lower()


def test_cumulative_byte_cap_refused(monkeypatch, tmp_path):
    monkeypatch.setitem(sys.modules, "pdf2image",
                        _fake_pdf2image(pages=5, nbytes=1000))
    res = rp.rasterize(_pdf(tmp_path), tmp_path / "work", output_root=tmp_path,
                       max_total_bytes=1500)   # trips after ~2 pages
    assert res.status == "refused" and "cumulative" in res.message.lower()


def test_render_dpi_is_capped_via_cli(monkeypatch, tmp_path):
    """AC10: a higher --dpi is clamped down to RENDER_DPI before pdf2image runs."""
    rec: dict = {}
    monkeypatch.setitem(sys.modules, "pdf2image",
                        _fake_pdf2image(pages=1, record=rec))
    rc = rp.main(["--input", str(_pdf(tmp_path)),
                  "--output-dir", str(tmp_path / "work"),
                  "--output-root", str(tmp_path), "--dpi", "9999"])
    assert rc == 0
    assert rec["dpi"] == rp.RENDER_DPI


def test_render_dpi_capped_in_enforcement_function(monkeypatch, tmp_path):
    """AC10: the clamp lives in rasterize() itself — a non-CLI caller passing an
    over-cap dpi cannot bypass it (the guarantee the CLI test can't pin)."""
    rec: dict = {}
    monkeypatch.setitem(sys.modules, "pdf2image",
                        _fake_pdf2image(pages=1, record=rec))
    res = rp.rasterize(_pdf(tmp_path), tmp_path / "work", output_root=tmp_path,
                       dpi=9999)
    assert res.status == "ok"
    assert rec["dpi"] == rp.RENDER_DPI


def test_per_page_pixel_cap_refused(monkeypatch, tmp_path):
    """AC10 (dimension axis): a page whose rendered pixels exceed the per-page cap
    is refused (poppler decodes in a subprocess, so Pillow's own guard can't fire),
    and no partial page files are left behind."""
    monkeypatch.setitem(sys.modules, "pdf2image",
                        _fake_pdf2image(pages=2, size=(20000, 20000)))  # 400 MP
    work = tmp_path / "work"
    res = rp.rasterize(_pdf(tmp_path), work, output_root=tmp_path)
    assert res.status == "refused" and "per-page" in res.message.lower()
    assert not list(work.glob("page-*.png")), "partial pages not cleaned up"


def test_empty_page_render_is_skipped(monkeypatch, tmp_path):
    """A page that fails to render (pdf2image returns []) is skipped, not crashed —
    the run completes with fewer page_paths than total_pages."""
    monkeypatch.setitem(sys.modules, "pdf2image",
                        _fake_pdf2image(pages=3, empty=(2,)))
    res = rp.rasterize(_pdf(tmp_path), tmp_path / "work", output_root=tmp_path)
    assert res.status == "ok"
    assert len(res.page_paths) == 2


# --- AC11: work-dir confinement --------------------------------------------


def test_workdir_traversal_refused(monkeypatch, tmp_path):
    monkeypatch.setitem(sys.modules, "pdf2image", _fake_pdf2image(pages=1))
    root = tmp_path / "root"
    root.mkdir()
    res = rp.rasterize(_pdf(tmp_path), root / ".." / "escape",
                       output_root=root)
    assert res.status == "refused" and "confinement" in res.message.lower()


def test_workdir_sibling_prefix_refused(monkeypatch, tmp_path):
    monkeypatch.setitem(sys.modules, "pdf2image", _fake_pdf2image(pages=1))
    root = tmp_path / "root"
    root.mkdir()
    (tmp_path / "root-evil").mkdir()
    res = rp.rasterize(_pdf(tmp_path), tmp_path / "root-evil" / "w",
                       output_root=root)
    assert res.status == "refused"
