#!/usr/bin/env python3
"""Validate agentbundle release artifacts at their test-content boundaries.

Wheels and zipapps must not carry executable test content.  Source
distributions must carry the complete engine suite and prove it can collect and
execute without repository-local catalogue content.
"""

from __future__ import annotations

import hashlib
import importlib.util
import os
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import zipfile
from pathlib import Path, PurePosixPath

_TEST_ENTRY = re.compile(
    r"(^|/)tests?(/|$)"
    r"|(^|/)(test_[^/]*|[^/]*_test|conftest)\.py$"
)
_EXEMPT = re.compile(r"^[^/]+/_data/catalogue-scaffold/")

MAX_MEMBERS = 10_000
MAX_MEMBER_SIZE = 32 * 1024 * 1024
MAX_TOTAL_SIZE = 256 * 1024 * 1024
MAX_EXPANSION_RATIO = 100
COLLECT_TIMEOUT_SECONDS = 120
EXECUTE_TIMEOUT_SECONDS = 900

_DRIVE_PATH = re.compile(r"^[A-Za-z]:")
_CACHE_DIRS = frozenset(
    {
        "__pycache__",
        ".pytest_cache",
        ".mypy_cache",
        ".ruff_cache",
        ".hypothesis",
        ".tox",
        ".nox",
        "htmlcov",
    }
)
_RESIDUE_NAMES = frozenset({".DS_Store", "coverage.xml"})
_DEPENDENCY_IMPORTS = ("pytest", "yaml", "jsonschema", "credbroker")
_SKIP_LINE = re.compile(
    r"^\s*SKIPPED\s+\[\d+\]\s+(?P<path>.*?\.py)(?::\d+)?:\s+(?P<reason>.*)$"
)
_FORBIDDEN_SKIP_CONTENT = re.compile(
    r"not installed|no module named|importorskip|not present in this checkout"
    r"|\b(?:packs|profiles|contracts|guides)\b|\bdist[/\\]apm\b",
    re.IGNORECASE,
)
_EXPECTED_SKIP_REASONS = tuple(
    re.compile(pattern, re.IGNORECASE)
    for pattern in (
        r"^symlinks? (?:creation )?"
        r"(?:requires?|needs|unsupported|unavailable|forbidden|test\b).*$",
        r"^NTFS refuses to materialise seeds/.*$",
        r"^cursor install returns rc=1 under concurrent execution on Windows;.*$",
        r"^POSIX mode bits; .*Windows.*$",
        r"^execute bits not supported on Windows$",
        r"^symlinks/execute bits not supported on Windows$",
        r"^st_nlink hard-link detection is POSIX-only$",
        r"^pwd module is POSIX-only$",
        r"^POSIX FIFOs only$",
        r"^POSIX concurrency test$",
        r"^Windows-only$",
        r"^hardcoded POSIX /tmp path$",
        r"^no seed primitives in core fixture; skip$",
    )
)
_EXPECTED_STUB_MODULE_HASHES = {
    "test_adapter_permissions_projection.py":
        "82143c96b5ce43f3c19156a5a32e7acb50ad541a87e4ec6cf074ff2a407d0cc6",
    "test_workspace_mcp_elicit.py":
        "dc4a4da5e0d8c8e23b1ac722dee195ed22400d41e7450515e59f0ad380cb13f4",
    "test_workspace_mcp_event_bridge.py":
        "2fa8cb47e33302a4ee5e9618a59e3854a3e05ac4d1109e9e3527707d8ce300d2",
    "test_workspace_mcp_git.py":
        "b3c2460c10d70c43933f415cf02a34ca3fad0574bfee8a078c9567ebd3ee6035",
    "test_workspace_mcp_stdin.py":
        "1b9996595f5d4c8efe2f3d2b1a51b7a2570a155e9ed99779e92a71c66ee21965",
    "test_workspace_mcp_tools.py":
        "1041a23bd0467dc88bf03cac468c35f70d4d95abb56e891a9cdae21c36bed654",
}


class ArtifactViolation(RuntimeError):
    """The artifact is readable but violates its release contract."""


def offending_entries(artifact: Path) -> list[str]:
    """Return forbidden test-content entries in a wheel or zipapp."""
    with zipfile.ZipFile(artifact) as zf:
        names = zf.namelist()
    return sorted(
        name for name in names if _TEST_ENTRY.search(name) and not _EXEMPT.search(name)
    )


def _safe_member_name(raw_name: str) -> str:
    """Return a portable relative POSIX member name or refuse it."""
    if not raw_name or "\x00" in raw_name:
        raise ArtifactViolation("empty or NUL-containing tar member name")
    portable = raw_name.replace("\\", "/")
    if portable.startswith(("/", "//")):
        raise ArtifactViolation(f"absolute or drive-qualified tar member: {raw_name!r}")
    parts = PurePosixPath(portable).parts
    if any(part == ".." for part in parts):
        raise ArtifactViolation(f"traversing tar member: {raw_name!r}")
    clean = "/".join(part for part in parts if part not in ("", "."))
    if not clean:
        raise ArtifactViolation(f"empty tar member path: {raw_name!r}")
    if _DRIVE_PATH.match(clean):
        raise ArtifactViolation(f"absolute or drive-qualified tar member: {raw_name!r}")
    return clean


def _is_build_residue(name: str) -> bool:
    """Return whether a portable archive path is generated local residue."""
    path = PurePosixPath(name)
    return (
        any(part in _CACHE_DIRS for part in path.parts)
        or path.name in _RESIDUE_NAMES
        or path.name == ".coverage"
        or path.name.startswith(".coverage.")
        or path.suffix in {".pyc", ".pyo"}
    )


def _validate_sdist(artifact: Path) -> tuple[int, int]:
    """Stream and validate all tar headers without retaining the member list."""
    member_count = 0
    total_size = 0
    test_modules = 0
    try:
        with tarfile.open(artifact, mode="r|gz") as tf:
            for member in tf:
                member_count += 1
                if member_count > MAX_MEMBERS:
                    raise ArtifactViolation(
                        f"sdist exceeds {MAX_MEMBERS:,} tar members"
                    )
                name = _safe_member_name(member.name)
                if _is_build_residue(name):
                    raise ArtifactViolation(f"sdist build/cache residue refused: {name}")
                if member.issym() or member.islnk():
                    raise ArtifactViolation(f"sdist link member refused: {name}")
                if not (member.isdir() or member.isreg()):
                    raise ArtifactViolation(f"sdist special-file member refused: {name}")
                if member.isreg():
                    if member.size > MAX_MEMBER_SIZE:
                        raise ArtifactViolation(
                            f"sdist member exceeds {MAX_MEMBER_SIZE} bytes: {name}"
                        )
                    total_size += member.size
                    if total_size > MAX_TOTAL_SIZE:
                        raise ArtifactViolation(
                            f"sdist exceeds {MAX_TOTAL_SIZE} uncompressed bytes"
                        )
                    if re.search(r"(^|/)tests/test[^/]*\.py$", name) or re.search(
                        r"(^|/)tests/.*/test[^/]*\.py$", name
                    ):
                        test_modules += 1
    except (OSError, tarfile.TarError, EOFError) as exc:
        raise ArtifactViolation(f"unreadable sdist tar archive: {exc}") from exc

    compressed_size = artifact.stat().st_size
    if compressed_size <= 0:
        raise ArtifactViolation("empty sdist archive")
    if total_size > compressed_size * MAX_EXPANSION_RATIO:
        raise ArtifactViolation(
            f"sdist expansion exceeds {MAX_EXPANSION_RATIO}:1 "
            f"({total_size} bytes from {compressed_size})"
        )
    if test_modules == 0:
        raise ArtifactViolation("sdist carries no executable engine test modules")
    return member_count, test_modules


def _extract_sdist(artifact: Path, destination: Path) -> None:
    """Extract an already-validated sdist without tarfile's extract helpers."""
    root = destination.resolve()
    with tarfile.open(artifact, mode="r|gz") as tf:
        for member in tf:
            name = _safe_member_name(member.name)
            target = (root / name).resolve()
            try:
                target.relative_to(root)
            except ValueError as exc:
                raise ArtifactViolation(f"tar member escapes extraction root: {name}") from exc
            if member.isdir():
                target.mkdir(parents=True, exist_ok=True)
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            source = tf.extractfile(member)
            if source is None:
                raise ArtifactViolation(f"could not read regular tar member: {name}")
            with source, target.open("xb") as output:
                shutil.copyfileobj(source, output, length=1024 * 1024)


def _project_root(extracted: Path) -> Path:
    """Return the one extracted project root with the required engine tests."""
    candidates = [p.parent for p in extracted.rglob("pyproject.toml")]
    if len(candidates) != 1:
        raise ArtifactViolation(
            f"sdist must contain exactly one pyproject.toml; found {len(candidates)}"
        )
    root = candidates[0]
    if not (root / "tests").is_dir():
        raise ArtifactViolation("sdist project root has no tests/ directory")
    if (root / "tests" / "live-catalogue").exists():
        raise ArtifactViolation("sdist contains forbidden tests/live-catalogue rail")
    return root


def _engine_test_files(root: Path) -> dict[str, bytes]:
    """Return authored regular files in an engine test tree, keyed relatively."""
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in root.rglob("*")
        if path.is_file()
        and not path.is_symlink()
        and not _is_build_residue(path.relative_to(root).as_posix())
        and "live-catalogue" not in path.relative_to(root).parts
    }


def _assert_complete_engine_tests(project_root: Path, source_tests: Path) -> None:
    """Prove the archive test tree is byte-complete against the source tree."""
    if not source_tests.is_dir():
        raise ArtifactViolation(f"engine test source tree not found: {source_tests}")
    expected = _engine_test_files(source_tests)
    actual = _engine_test_files(project_root / "tests")
    missing = sorted(expected.keys() - actual.keys())
    extra = sorted(actual.keys() - expected.keys())
    changed = sorted(
        name
        for name in expected.keys() & actual.keys()
        if expected[name] != actual[name]
    )
    if missing or extra or changed:
        details = []
        if missing:
            details.append("missing: " + ", ".join(missing[:10]))
        if extra:
            details.append("unexpected: " + ", ".join(extra[:10]))
        if changed:
            details.append("changed: " + ", ".join(changed[:10]))
        raise ArtifactViolation(
            "sdist engine test tree is incomplete (" + "; ".join(details) + ")"
        )


def _stage_checkout_shape(project_root: Path, temporary_root: Path) -> Path:
    """Place sdist content at ``packages/agentbundle`` for path-stable tests."""
    staged = temporary_root / "workspace" / "packages" / "agentbundle"
    staged.parent.mkdir(parents=True)
    shutil.copytree(project_root, staged)
    return staged


def _preflight_dependencies() -> None:
    """Fail before pytest when a retained engine-test dependency is absent."""
    missing = [name for name in _DEPENDENCY_IMPORTS if importlib.util.find_spec(name) is None]
    if missing:
        raise ArtifactViolation(
            "sdist test dependency preflight failed: " + ", ".join(missing)
        )


def _run_pytest(project_root: Path, *args: str, timeout: int) -> str:
    """Run the extracted suite with a bounded argv-form pytest subprocess."""
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    existing = env.get("PYTHONPATH")
    env["PYTHONPATH"] = (
        str(project_root) if not existing else str(project_root) + os.pathsep + existing
    )
    try:
        proc = subprocess.run(
            [sys.executable, "-m", "pytest", "tests", *args],
            cwd=project_root,
            env=env,
            text=True,
            capture_output=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired as exc:
        raise ArtifactViolation(f"sdist pytest timed out after {timeout}s") from exc
    output = proc.stdout + proc.stderr
    if proc.returncode != 0:
        raise ArtifactViolation(
            f"sdist pytest exited {proc.returncode}:\n{output[-8000:]}"
        )
    return output


def _is_expected_stub_skip(path: str, reason: str, project_root: Path | None) -> bool:
    """Accept only construction skips from byte-pinned, pre-existing modules."""
    if project_root is None or not reason.startswith("STUB"):
        return False
    portable = path.replace("\\", "/")
    if not portable.startswith("tests/"):
        return False
    relative = portable.removeprefix("tests/")
    expected = _EXPECTED_STUB_MODULE_HASHES.get(relative)
    if expected is None:
        return False
    module = project_root / "tests" / relative
    try:
        actual = hashlib.sha256(module.read_bytes()).hexdigest()
    except OSError:
        return False
    return actual == expected


def _check_skip_integrity(output: str, project_root: Path | None = None) -> None:
    """Refuse every reported skip outside the explicit expected policy."""
    bad = []
    for line in output.splitlines():
        if not line.lstrip().startswith("SKIPPED"):
            continue
        match = _SKIP_LINE.match(line)
        if match is None:
            bad.append(line)
            continue
        reason = match.group("reason")
        expected = _is_expected_stub_skip(
            match.group("path"), reason, project_root
        ) or any(pattern.fullmatch(reason) for pattern in _EXPECTED_SKIP_REASONS)
        if _FORBIDDEN_SKIP_CONTENT.search(reason) or not expected:
            bad.append(line)
    if bad:
        raise ArtifactViolation(
            "sdist suite used skips outside the explicit expected policy:\n"
            + "\n".join(bad)
        )


def check_sdist(artifact: Path) -> tuple[int, int]:
    """Validate, extract, collect, and execute one source distribution."""
    counts = _validate_sdist(artifact)
    with tempfile.TemporaryDirectory(prefix="agentbundle-sdist-gate-") as tmp:
        extracted = Path(tmp)
        _extract_sdist(artifact, extracted)
        extracted_project = _project_root(extracted)
        source_tests = (
            Path(__file__).resolve().parents[1]
            / "packages"
            / "agentbundle"
            / "tests"
        )
        _assert_complete_engine_tests(extracted_project, source_tests)
        root = _stage_checkout_shape(extracted_project, extracted)
        _preflight_dependencies()
        _run_pytest(
            root,
            "--collect-only",
            "-q",
            timeout=COLLECT_TIMEOUT_SECONDS,
        )
        output = _run_pytest(
            root,
            "-q",
            "-r",
            "s",
            timeout=EXECUTE_TIMEOUT_SECONDS,
        )
        _check_skip_integrity(output, root)
    return counts


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print(
            f"usage: {argv[0]} <artifact.whl|artifact.pyz|artifact.tar.gz> [...]",
            file=sys.stderr,
        )
        return 2

    failed = False
    bad_args = False
    for raw in argv[1:]:
        artifact = Path(raw)
        try:
            if artifact.name.endswith(".tar.gz"):
                members, tests = check_sdist(artifact)
                print(
                    f"check-artifact-contents: {artifact.name} clean "
                    f"({members} members, {tests} engine test modules executed)"
                )
                continue
            if artifact.suffix not in (".whl", ".pyz"):
                print(
                    f"check-artifact-contents: {artifact.name}: expected .whl, "
                    ".pyz, or .tar.gz",
                    file=sys.stderr,
                )
                bad_args = True
                continue
            entries = offending_entries(artifact)
        except ArtifactViolation as exc:
            failed = True
            print(f"check-artifact-contents: {artifact.name}: {exc}", file=sys.stderr)
            continue
        except (OSError, zipfile.BadZipFile) as exc:
            print(
                f"check-artifact-contents: {artifact.name}: unreadable artifact ({exc})",
                file=sys.stderr,
            )
            bad_args = True
            continue
        if entries:
            failed = True
            print(
                f"check-artifact-contents: {artifact.name} carries "
                f"{len(entries)} forbidden test entries:",
                file=sys.stderr,
            )
            for entry in entries:
                print(f"  {entry}", file=sys.stderr)
        else:
            print(f"check-artifact-contents: {artifact.name} clean")

    if failed:
        return 1
    if bad_args:
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
