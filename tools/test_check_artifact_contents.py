#!/usr/bin/env python3
"""Tests for `tools/check-artifact-contents.py` and the zipapp builder's
test exclusion (RFC-0082 AC3, AC4, AC8).

A gate is worth exactly what its negative case is worth, so every case here
builds an artifact that *should* fail and asserts it does.
"""
from __future__ import annotations

import importlib.util
import subprocess
import sys
import zipfile
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
GATE = REPO_ROOT / "tools" / "check-artifact-contents.py"
ZIPAPP_BUILDER = REPO_ROOT / "tools" / "build_zipapp.py"


def _load_gate():
    spec = importlib.util.spec_from_file_location("_gate", GATE)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


gate = _load_gate()


def _zip(path: Path, names: list[str]) -> Path:
    with zipfile.ZipFile(path, "w") as zf:
        for n in names:
            zf.writestr(n, "x\n")
    return path


# ── the absence assertion ────────────────────────────────────────────────


def test_clean_wheel_passes(tmp_path):
    whl = _zip(tmp_path / "p-1.0-py3-none-any.whl", ["pkg/__init__.py", "pkg/cli.py"])
    assert gate.offending_entries(whl) == []
    assert gate.main(["prog", str(whl)]) == 0


def test_nested_test_tree_is_caught(tmp_path):
    """The defect RFC-0082 measured: 45 test entries nested inside the package,
    which `check-wheel-contents`' library-toplevel check never sees."""
    whl = _zip(
        tmp_path / "p-1.0-py3-none-any.whl",
        ["pkg/__init__.py", "pkg/build/tests/__init__.py", "pkg/build/tests/test_x.py"],
    )
    assert gate.offending_entries(whl) == [
        "pkg/build/tests/__init__.py",
        "pkg/build/tests/test_x.py",
    ]
    assert gate.main(["prog", str(whl)]) == 1


def test_toplevel_test_dir_is_caught(tmp_path):
    whl = _zip(tmp_path / "p-1.0-py3-none-any.whl", ["pkg/__init__.py", "tests/test_x.py"])
    assert gate.main(["prog", str(whl)]) == 1


def test_stray_conftest_is_caught(tmp_path):
    """conftest.py is test content even with no `tests` component in the path."""
    whl = _zip(tmp_path / "p-1.0-py3-none-any.whl", ["pkg/__init__.py", "pkg/conftest.py"])
    assert gate.main(["prog", str(whl)]) == 1


def test_zipapp_is_checked_too(tmp_path):
    pyz = _zip(tmp_path / "app.pyz", ["pkg/__init__.py", "pkg/tests/test_x.py"])
    assert gate.main(["prog", str(pyz)]) == 1


# ── the scaffold carve-out ───────────────────────────────────────────────


def test_scaffold_template_is_exempt(tmp_path):
    """Bundled scaffold content is inert template material and ships in the
    wheel by design. Without this the carve-out spec's `tests/conformance/`
    template would turn an already-released gate red on a correct artifact."""
    whl = _zip(
        tmp_path / "p-1.0-py3-none-any.whl",
        ["pkg/__init__.py", "pkg/_data/catalogue-scaffold/tests/conformance/test_t.py"],
    )
    assert gate.offending_entries(whl) == []
    assert gate.main(["prog", str(whl)]) == 0


def test_same_path_outside_the_scaffold_still_fails(tmp_path):
    """The exemption is scoped to the scaffold, not to the filename."""
    whl = _zip(
        tmp_path / "p-1.0-py3-none-any.whl",
        ["pkg/__init__.py", "pkg/_data/other/tests/conformance/test_t.py"],
    )
    assert gate.main(["prog", str(whl)]) == 1


# ── argument handling ────────────────────────────────────────────────────


def test_sdist_is_refused_as_out_of_scope(tmp_path):
    """The sdist's rule is the inverse and lands with the carve-out spec.
    Silently accepting it here would invite an absence assertion that later
    rejects a correct artifact."""
    sd = tmp_path / "p-1.0.tar.gz"
    sd.write_bytes(b"")
    assert gate.main(["prog", str(sd)]) == 2


def test_no_arguments_is_usage_error():
    assert gate.main(["prog"]) == 2


# ── the real artifacts ───────────────────────────────────────────────────


@pytest.mark.skipif(
    not (REPO_ROOT / "packages" / "agentbundle").is_dir(),
    reason="engine package not present",
)
def test_real_zipapp_carries_no_engine_tests(tmp_path):
    """AC4, first half — build the real zipapp and check it."""
    subprocess.run(
        [sys.executable, str(ZIPAPP_BUILDER), str(tmp_path)],
        cwd=REPO_ROOT, check=True, capture_output=True,
    )
    assert gate.offending_entries(tmp_path / "agentbundle.pyz") == []


def test_zipapp_retains_scaffold_test_template(tmp_path, monkeypatch):
    """AC4, second half — the builder must not strip a scaffold `tests/`
    template. `shutil.ignore_patterns` matches basenames at any depth, so a
    bare `"tests"` entry would silently delete it and `catalogue init` would
    then abort on scaffold-manifest verification."""
    src = tmp_path / "src" / "packages" / "agentbundle" / "agentbundle"
    scaffold = src / "_data" / "catalogue-scaffold" / "tests" / "conformance"
    scaffold.mkdir(parents=True)
    (scaffold / "test_t.py").write_text("def test_x():\n    pass\n", encoding="utf-8")
    (src / "__init__.py").write_text("", encoding="utf-8")
    (src / "cli.py").write_text("def main():\n    return 0\n", encoding="utf-8")

    out = tmp_path / "out"
    monkeypatch.chdir(tmp_path / "src")
    subprocess.run(
        [sys.executable, str(ZIPAPP_BUILDER), str(out)],
        check=True, capture_output=True,
    )
    with zipfile.ZipFile(out / "agentbundle.pyz") as zf:
        names = zf.namelist()
    assert any("catalogue-scaffold/tests/conformance/test_t.py" in n for n in names), (
        "the scaffold test template was stripped from the zipapp"
    )
