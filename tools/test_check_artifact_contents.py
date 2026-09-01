#!/usr/bin/env python3
"""Tests for `tools/check-artifact-contents.py` and the zipapp builder's
test exclusion (RFC-0082 AC3, AC4, AC8).

A gate is worth exactly what its negative case is worth, so every case here
builds an artifact that *should* fail and asserts it does.
"""
from __future__ import annotations

import gzip
import importlib.util
import io
import subprocess
import sys
import tarfile
import zipfile
from pathlib import Path
from types import SimpleNamespace

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


def _tar(path: Path, entries: list[tuple[str, bytes]]) -> Path:
    with tarfile.open(path, "w:gz") as tf:
        for name, data in entries:
            info = tarfile.TarInfo(name)
            info.size = len(data)
            tf.addfile(info, io.BytesIO(data))
    return path


def _valid_sdist(path: Path) -> Path:
    return _tar(
        path,
        [
            ("pkg-1.0/pyproject.toml", b"[build-system]\n"),
            ("pkg-1.0/tests/test_ok.py", b"def test_ok(): pass\n"),
        ],
    )


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


def test_pytest_suffix_naming_is_caught(tmp_path):
    """pytest's default `python_files` is `test_*.py *_test.py`, and this repo
    carries a `**/*_test.py` per-file-ignore, so the suffix form is in use."""
    whl = _zip(tmp_path / "p-1.0-py3-none-any.whl", ["pkg/__init__.py", "pkg/adapters_test.py"])
    assert gate.main(["prog", str(whl)]) == 1


def test_exemption_does_not_whitelist_a_nested_test_tree(tmp_path):
    """The carve-out is anchored at the top-level package's own `_data/`. An
    unanchored match would exempt a real test tree inside the package purely
    because a directory further down is named `catalogue-scaffold`."""
    whl = _zip(
        tmp_path / "p-1.0-py3-none-any.whl",
        ["pkg/__init__.py", "pkg/build/tests/_data/catalogue-scaffold/test_p.py"],
    )
    assert gate.main(["prog", str(whl)]) == 1


# ── argument handling ────────────────────────────────────────────────────


def test_sdist_is_dispatched_to_execution_gate(tmp_path, monkeypatch):
    sd = _valid_sdist(tmp_path / "p-1.0.tar.gz")
    seen = []

    def _check(path):
        seen.append(path)
        return (2, 1)

    monkeypatch.setattr(gate, "check_sdist", _check)
    assert gate.main(["prog", str(sd)]) == 0
    assert seen == [sd]


@pytest.mark.parametrize(
    "name",
    [
        "/absolute",
        "../escape",
        "a/../../escape",
        r"..\escape",
        r"C:\absolute",
        "C:drive-relative",
        "./C:drive-relative",
        r"\\server\share\file",
    ],
)
def test_sdist_portable_name_refusals(name):
    with pytest.raises(gate.ArtifactViolation):
        gate._safe_member_name(name)


def test_sdist_stream_validation_accepts_engine_tests(tmp_path):
    sd = _valid_sdist(tmp_path / "p-1.0.tar.gz")
    assert gate._validate_sdist(sd) == (2, 1)


@pytest.mark.parametrize(
    "name",
    [
        "pkg/tests/__pycache__/test_ok.cpython-313.pyc",
        "pkg/tests/.pytest_cache/v/cache/nodeids",
        "pkg/tests/test_ok.pyc",
        "pkg/templates/.DS_Store",
    ],
)
def test_sdist_refuses_build_and_cache_residue(tmp_path, name):
    sd = _tar(
        tmp_path / "p-1.0.tar.gz",
        [("pkg/tests/test_ok.py", b"def test_ok(): pass\n"), (name, b"residue")],
    )
    with pytest.raises(gate.ArtifactViolation, match="residue refused"):
        gate._validate_sdist(sd)


def test_sdist_completeness_compares_modules_fixtures_and_bytes(tmp_path):
    source = tmp_path / "source"
    extracted = tmp_path / "extracted"
    (source / "fixtures").mkdir(parents=True)
    (extracted / "tests" / "fixtures").mkdir(parents=True)
    (source / "test_ok.py").write_text("def test_ok(): pass\n", encoding="utf-8")
    (source / "fixtures" / "data.toml").write_text("value = 1\n", encoding="utf-8")
    (extracted / "tests" / "test_ok.py").write_text(
        "def test_ok(): pass\n", encoding="utf-8"
    )

    with pytest.raises(gate.ArtifactViolation, match="fixtures/data.toml"):
        gate._assert_complete_engine_tests(extracted, source)

    (extracted / "tests" / "fixtures" / "data.toml").write_text(
        "value = 2\n", encoding="utf-8"
    )
    with pytest.raises(gate.ArtifactViolation, match="changed: fixtures/data.toml"):
        gate._assert_complete_engine_tests(extracted, source)

    (extracted / "tests" / "fixtures" / "data.toml").write_text(
        "value = 1\n", encoding="utf-8"
    )
    gate._assert_complete_engine_tests(extracted, source)


@pytest.mark.parametrize("member_type", [tarfile.SYMTYPE, tarfile.LNKTYPE, tarfile.FIFOTYPE])
def test_sdist_refuses_links_and_special_files(tmp_path, member_type):
    sd = tmp_path / "p-1.0.tar.gz"
    with tarfile.open(sd, "w:gz") as tf:
        test = tarfile.TarInfo("pkg/tests/test_ok.py")
        test.size = 0
        tf.addfile(test, io.BytesIO())
        bad = tarfile.TarInfo("pkg/bad")
        bad.type = member_type
        bad.linkname = "pkg/tests/test_ok.py"
        tf.addfile(bad)
    with pytest.raises(gate.ArtifactViolation):
        gate._validate_sdist(sd)


def test_sdist_refuses_member_over_32_mib_from_header(tmp_path):
    sd = tmp_path / "p-1.0.tar.gz"
    info = tarfile.TarInfo("pkg/tests/test_big.py")
    info.size = gate.MAX_MEMBER_SIZE + 1
    with gzip.open(sd, "wb") as stream:
        stream.write(info.tobuf())
        stream.write(b"\0" * 1024)
    with pytest.raises(gate.ArtifactViolation, match="member exceeds"):
        gate._validate_sdist(sd)


def test_sdist_refuses_10001st_streamed_header(tmp_path):
    sd = tmp_path / "p-1.0.tar.gz"
    with tarfile.open(sd, "w:gz") as tf:
        for index in range(gate.MAX_MEMBERS + 1):
            info = tarfile.TarInfo(f"pkg/tests/test_{index}.py")
            info.size = 0
            tf.addfile(info, io.BytesIO())
    with pytest.raises(gate.ArtifactViolation, match="tar members"):
        gate._validate_sdist(sd)


def test_sdist_refuses_aggregate_expansion_over_100_to_1(tmp_path):
    sd = _tar(
        tmp_path / "p-1.0.tar.gz",
        [("pkg/tests/test_compressible.py", b"0" * (1024 * 1024))],
    )
    with pytest.raises(gate.ArtifactViolation, match="expansion"):
        gate._validate_sdist(sd)


def test_sdist_refuses_total_size_before_extraction(tmp_path, monkeypatch):
    monkeypatch.setattr(gate, "MAX_TOTAL_SIZE", 10)
    sd = _tar(
        tmp_path / "p-1.0.tar.gz",
        [("pkg/tests/test_a.py", b"123456"), ("pkg/tests/test_b.py", b"123456")],
    )
    with pytest.raises(gate.ArtifactViolation, match="uncompressed bytes"):
        gate._validate_sdist(sd)


def test_sdist_validator_never_materialises_all_headers():
    source = GATE.read_text(encoding="utf-8")
    assert ".getmembers(" not in source


@pytest.mark.parametrize(
    "reason",
    [
        "missing: No module named 'x'",
        "packs/core not present in this checkout",
        "packs/core missing",
        "profiles/default missing",
        "contracts/adapter.toml absent",
        "guides/reference unavailable",
        "dist/apm was not built",
        "pytest.importorskip dependency",
        "an unrecognised feature skip",
        "STUB: packs/core missing",
        "STUB: dependency not installed",
        "STUB: deferred construction test",
        "STUB (deferred): deferred construction test",
        "symlinks unsupported on this platform: No module named x",
        "POSIX mode bits; No module named x on Windows",
    ],
)
def test_sdist_skip_integrity_refuses_unrecognised_reasons(reason):
    with pytest.raises(gate.ArtifactViolation, match="explicit expected policy"):
        gate._check_skip_integrity(f"SKIPPED [1] tests/test_x.py:12: {reason}")


@pytest.mark.parametrize(
    "reason",
    [
        "symlinks unsupported on this platform/filesystem",
        "symlink creation requires elevated privileges on Windows",
        "symlink creation needs privilege on Windows",
        "symlinks require Developer Mode on Windows",
        "symlink creation forbidden",
        "symlink test — POSIX only",
        "NTFS refuses to materialise seeds/CON.md; POSIX coverage is sufficient",
        "NTFS refuses to materialise seeds/NUL.md; POSIX coverage is sufficient",
        "cursor install returns rc=1 under concurrent execution on Windows; tracked",
        "POSIX mode bits; the DACL model differs on Windows",
        "execute bits not supported on Windows",
        "symlinks/execute bits not supported on Windows",
        "st_nlink hard-link detection is POSIX-only",
        "pwd module is POSIX-only",
        "POSIX FIFOs only",
        "POSIX concurrency test",
        "Windows-only",
        "hardcoded POSIX /tmp path",
        "no seed primitives in core fixture; skip",
        # Observed verbatim on a loaded macOS host, 2026-09-01.
        "wall-clock not asserted: load/core 2.8 exceeds 2.0. CPU (2.58s) "
        "and memory (27.4 MiB) were asserted unconditionally.",
    ],
)
def test_sdist_skip_integrity_accepts_explicit_policy(reason):
    gate._check_skip_integrity(f"SKIPPED [1] tests/test_x.py:12: {reason}")


def test_sdist_skip_integrity_accepts_only_byte_pinned_stub_modules():
    project_root = REPO_ROOT / "packages" / "agentbundle"
    reason = (
        "STUB (deferred): install core on clean tmp repo; parse "
        ".claude/settings.json; assert all 6 ids in permissions.allow"
    )
    gate._check_skip_integrity(
        "SKIPPED [1] tests/test_adapter_permissions_projection.py:19: " + reason,
        project_root,
    )
    with pytest.raises(gate.ArtifactViolation, match="explicit expected policy"):
        gate._check_skip_integrity(
            "SKIPPED [1] tests/test_unpinned_stub.py:1: STUB: unfinished",
            project_root,
        )


def test_sdist_skip_integrity_refuses_malformed_summary_line():
    with pytest.raises(gate.ArtifactViolation, match="explicit expected policy"):
        gate._check_skip_integrity("SKIPPED unparseable")


def test_sdist_skip_integrity_ignores_non_skip_output():
    for reason in (
        "SKIPPED [1] x.py: missing: No module named 'x'",
        "SKIPPED [1] x.py: packs/core not present in this checkout",
        "SKIPPED [1] x.py: pytest.importorskip dependency",
    ):
        gate._check_skip_integrity("not a summary line: " + reason)


def test_sdist_pytest_failure_and_timeout_are_fatal(tmp_path, monkeypatch):
    monkeypatch.setattr(
        gate.subprocess,
        "run",
        lambda *args, **kwargs: SimpleNamespace(returncode=1, stdout="failed", stderr=""),
    )
    with pytest.raises(gate.ArtifactViolation, match="exited 1"):
        gate._run_pytest(tmp_path, "-q", timeout=1)

    def _timeout(*args, **kwargs):
        raise subprocess.TimeoutExpired(args[0], 1)

    monkeypatch.setattr(gate.subprocess, "run", _timeout)
    with pytest.raises(gate.ArtifactViolation, match="timed out"):
        gate._run_pytest(tmp_path, "-q", timeout=1)


def test_no_arguments_is_usage_error():
    assert gate.main(["prog"]) == 2


def test_unreadable_archive_is_an_input_error_not_a_violation(tmp_path):
    """`release-agentbundle.yml` passes a shell glob, so an unmatched
    `dist/*.whl` arrives as a literal filename. Reporting that as exit 1 sends
    a triager hunting for offending entries that do not exist."""
    bogus = tmp_path / "p-1.0-py3-none-any.whl"
    bogus.write_text("not a zip\n", encoding="utf-8")
    assert gate.main(["prog", str(bogus)]) == 2


def test_a_real_violation_outranks_a_bad_argument(tmp_path):
    """An unreadable first artifact must not skip the rest, and must not mask a
    genuine violation behind exit 2 — a triager reading "bad glob" would walk
    past tests shipping in the wheel."""
    bogus = tmp_path / "a-1.0-py3-none-any.whl"
    bogus.write_text("not a zip\n", encoding="utf-8")
    dirty = _zip(tmp_path / "b.pyz", ["pkg/__init__.py", "pkg/tests/test_x.py"])
    assert gate.main(["prog", str(bogus), str(dirty)]) == 1


def test_bad_argument_alone_still_exits_two(tmp_path):
    bogus = tmp_path / "a-1.0-py3-none-any.whl"
    bogus.write_text("not a zip\n", encoding="utf-8")
    clean = _zip(tmp_path / "b.pyz", ["pkg/__init__.py"])
    assert gate.main(["prog", str(bogus), str(clean)]) == 2


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


@pytest.mark.skipif(
    not (REPO_ROOT / "packages" / "agentbundle").is_dir(),
    reason="engine package not present",
)
def test_real_wheel_carries_no_engine_tests(tmp_path):
    """AC3 — the headline criterion. Its only other enforcement is the CI step,
    so without this the claim rests entirely on a workflow nothing else pins."""
    # Probe the toolchain up front, then let a genuine build failure FAIL.
    # Catching CalledProcessError and skipping would report a real packaging
    # regression — malformed pyproject, broken package-data, missing backend —
    # as a green skip, which is the shape this gate exists to prevent.
    # `--no-isolation` needs the backend in-env too, so probe both.
    pytest.importorskip("build", reason="`build` not installed")
    pytest.importorskip("setuptools", reason="build backend not installed")
    subprocess.run(
        [sys.executable, "-m", "build", "--wheel", "--no-isolation",
         "--outdir", str(tmp_path), str(REPO_ROOT / "packages" / "agentbundle")],
        check=True, capture_output=True,
    )
    wheels = list(tmp_path.glob("*.whl"))
    assert wheels, "no wheel was produced"
    assert gate.offending_entries(wheels[0]) == []


@pytest.mark.skipif(
    not (REPO_ROOT / "packages" / "agentbundle").is_dir(),
    reason="engine package not present",
)
def test_real_sdist_carries_and_executes_complete_engine_suite(tmp_path):
    """AC9 — build the actual setuptools sdist and drive the release gate."""
    assert importlib.util.find_spec("build") is not None, "`build` not installed"
    assert importlib.util.find_spec("setuptools") is not None, (
        "build backend not installed"
    )
    subprocess.run(
        [
            sys.executable,
            "-m",
            "build",
            "--sdist",
            "--no-isolation",
            "--outdir",
            str(tmp_path),
            str(REPO_ROOT / "packages" / "agentbundle"),
        ],
        check=True,
        capture_output=True,
    )
    sdists = list(tmp_path.glob("*.tar.gz"))
    assert sdists, "no sdist was produced"
    members, test_modules = gate.check_sdist(sdists[0])
    assert members > test_modules > 0


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


# ── the wiring itself (AC9) ──────────────────────────────────────────────


def _release_workflow() -> str:
    return (REPO_ROOT / ".github" / "workflows" / "release-agentbundle.yml").read_text(
        encoding="utf-8"
    )


def test_gate_paths_are_in_the_pull_request_trigger():
    """AC9 as a parse assertion, not a human read. Both tools/ files are
    load-bearing for `release-agentbundle.yml`; without them in
    `on.pull_request.paths`, a PR changing only the gate never runs the gate.

    Scoped to the `pull_request.paths` block specifically — asserting the
    strings appear anywhere before `jobs:` would also pass if they sat in a
    comment or under `push:`."""
    wf = _release_workflow()
    trigger = wf.split("jobs:", 1)[0]
    block = trigger.split("pull_request:", 1)[1].split("paths:", 1)[1]
    for path in ("tools/check-artifact-contents.py", "tools/build_zipapp.py"):
        assert f"'{path}'" in block or f'"{path}"' in block, (
            f"{path} is missing from on.pull_request.paths; a PR touching only "
            "it would skip the gate"
        )


def test_the_gate_step_is_actually_invoked():
    """Nothing else pins this. `release-agentbundle.yml` is out of scope for
    `lint-ci-parity`, so deleting the gate step leaves every AC checked, `make
    ci` green, and the wheel free to regain tests on the next regression —
    verified by mutation. This test is the only thing that goes red."""
    wf = _release_workflow()
    assert "tools/check-artifact-contents.py" in wf.split("jobs:", 1)[1], (
        "the gate is never invoked in any job"
    )
    for artifact in ("dist/*.whl", "agentbundle.pyz", "dist/*.tar.gz"):
        assert artifact in wf, f"the gate is not pointed at {artifact}"
