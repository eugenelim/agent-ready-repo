#!/usr/bin/env python3
"""Construction tests for canonical pack npm manifest/lockfile parity."""

from __future__ import annotations

import json
import pathlib
import subprocess
import sys
import tempfile

from selftest_harness import CaseFailures

_ROOT = pathlib.Path(__file__).resolve().parents[1]
_LINT = _ROOT / "tools" / "lint-pack-npm-projects.py"
_CHECKS = CaseFailures("test-lint-pack-npm-projects")
_PACKAGE_RECORD = {
    "version": "1.3.0",
    "resolved": "https://registry.npmjs.org/left-pad/-/left-pad-1.3.0.tgz",
    "integrity": "sha512-fixture",
}


def _valid_lock(*, package: str = "left-pad", version: str = "1.3.0") -> dict[str, object]:
    """Build one supported lockfile with one valid non-root package record."""
    return {
        "lockfileVersion": 3,
        "packages": {
            "": {"name": "fixture"},
            f"node_modules/{package}": {
                "version": version,
                "resolved": (
                    f"https://registry.npmjs.org/{package}/-/"
                    f"{package.rsplit('/', 1)[-1]}-{version}.tgz"
                ),
                "integrity": "sha512-fixture",
            },
        },
    }


def _lock_with(**record: object) -> dict[str, object]:
    """Build a supported lockfile after replacing one package record."""
    lock = _valid_lock()
    package = dict(_PACKAGE_RECORD)
    package.update(record)
    lock["packages"] = {"": {}, "node_modules/left-pad": package}
    return lock


def _project(
    root: pathlib.Path,
    name: str,
    *,
    manifest: bool,
    lockfile: bool,
    lock_data: dict[str, object] | None = None,
) -> pathlib.Path:
    """Create one canonical project fixture with the selected sibling files."""
    directory = root / "packs" / "fixture" / ".apm" / "skills" / name
    directory.mkdir(parents=True)
    if manifest:
        (directory / "package.json").write_text("{}\n", encoding="utf-8")
    if lockfile:
        (directory / "package-lock.json").write_text(
            json.dumps(lock_data if lock_data is not None else _valid_lock()),
            encoding="utf-8",
        )
    return directory


def _run(root: pathlib.Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(_LINT), "--root", str(root)],
        capture_output=True,
        text=True,
        check=False,
        cwd=str(_ROOT / "tools"),
    )


def _check(name: str, root: pathlib.Path, expected: int, needle: str) -> None:
    """Assert a fixture's stable exit status and path-bearing diagnostic."""
    result = _run(root)
    output = result.stdout + result.stderr
    _CHECKS.check(name, result.returncode == expected, output)
    _CHECKS.check(f"{name}-diagnostic", needle in output, output)
    _CHECKS.check(f"{name}-path", str(root) in output, output)


def main() -> int:
    with tempfile.TemporaryDirectory() as raw:
        root = pathlib.Path(raw)
        empty = root / "zero"
        empty.mkdir()
        _check("zero-projects", empty, 2, "no canonical")
        _check("unusable-root", root / "absent", 2, "unusable root")

        missing = root / "missing"
        _project(missing, "one", manifest=True, lockfile=False)
        _check("missing-lock", missing, 1, "missing sibling package-lock.json")

        orphan = root / "orphan"
        _project(orphan, "one", manifest=False, lockfile=True)
        _check("orphan-lock", orphan, 1, "missing sibling package.json")

        matched = root / "matched"
        _project(matched, "one", manifest=True, lockfile=True)
        _project(matched, "future", manifest=True, lockfile=True)
        _check("matched-and-future-project", matched, 0, "checked 2 canonical")

        hidden = root / "hidden"
        (hidden / ".scratch").mkdir(parents=True)
        _check("unrelated-hidden-project", hidden, 2, "no canonical")

        linked = root / "linked"
        target = linked / "target"
        _project(target, "one", manifest=True, lockfile=True)
        skill = linked / "packs" / "fixture" / ".apm" / "skills" / "one"
        skill.parent.mkdir(parents=True)
        skill.symlink_to(
            target / "packs" / "fixture" / ".apm" / "skills" / "one",
            target_is_directory=True,
        )
        _check("linked-canonical-segment", linked, 2, "linked path component")

        provenance = root / "provenance"
        cases = {
            "approved-registry": (_valid_lock(), 0, "checked 1 canonical"),
            "git": (
                _lock_with(resolved="git+https://example.invalid/repo.git"),
                1,
                "resolved URL",
            ),
            "file": (_lock_with(resolved="file:../left-pad"), 1, "resolved URL"),
            "link": (_lock_with(link=True), 1, "linked package"),
            "non-https": (
                _lock_with(
                    resolved="http://registry.npmjs.org/left-pad/-/left-pad-1.3.0.tgz"
                ),
                1,
                "resolved URL",
            ),
            "another-host": (
                _lock_with(
                    resolved="https://example.invalid/left-pad/-/left-pad-1.3.0.tgz"
                ),
                1,
                "resolved URL",
            ),
            "missing-locator": (_lock_with(resolved=None), 1, "missing resolved"),
            "missing-integrity": (_lock_with(integrity=None), 1, "sha512 integrity"),
            "weak-integrity": (_lock_with(integrity="sha1-fixture"), 1, "sha512 integrity"),
            "wrong-package": (
                _lock_with(
                    resolved="https://registry.npmjs.org/right-pad/-/right-pad-1.3.0.tgz"
                ),
                1,
                "does not name left-pad@1.3.0",
            ),
            "wrong-version": (
                _lock_with(
                    resolved="https://registry.npmjs.org/left-pad/-/left-pad-9.9.9.tgz"
                ),
                1,
                "does not name left-pad@1.3.0",
            ),
            "unsupported-version": (
                {"lockfileVersion": 1, "packages": _valid_lock()["packages"]},
                1,
                "unsupported lockfileVersion",
            ),
            "absent-packages": ({"lockfileVersion": 3}, 1, "packages must be an object"),
            "root-only": (
                {"lockfileVersion": 3, "packages": {"": {}}},
                1,
                "no non-root package records",
            ),
            "dependencies-only": (
                {"lockfileVersion": 3, "dependencies": {"left-pad": {}}},
                1,
                "packages must be an object",
            ),
        }
        for name, (lock_data, expected, needle) in cases.items():
            fixture = provenance / name
            _project(fixture, "one", manifest=True, lockfile=True, lock_data=lock_data)
            _check(f"provenance-{name}", fixture, expected, needle)

        npmrc = root / "npmrc"
        _project(npmrc, "one", manifest=True, lockfile=True)
        secret = "do-not-read-this-npmrc"
        for name, location in {
            "root": npmrc / ".npmrc",
            "dot-directory": npmrc / ".hidden" / ".npmrc",
            "node-modules": npmrc / "node_modules" / ".npmrc",
        }.items():
            location.parent.mkdir(parents=True, exist_ok=True)
            location.write_text(secret, encoding="utf-8")
            result = _run(npmrc)
            output = result.stdout + result.stderr
            _CHECKS.check(f"npmrc-{name}-exit", result.returncode == 1, output)
            _CHECKS.check(f"npmrc-{name}-path", str(location) in output, output)
            _CHECKS.check(f"npmrc-{name}-does-not-read", secret not in output, output)
            location.unlink()

        linked_scan = root / "linked-scan"
        _project(linked_scan, "one", manifest=True, lockfile=True)
        target = linked_scan / "target"
        target.mkdir()
        (linked_scan / "linked").symlink_to(target, target_is_directory=True)
        _check("npmrc-linked-directory", linked_scan, 2, "refused linked directory")

        outside_scan = root / "outside-scan"
        _project(outside_scan, "one", manifest=True, lockfile=True)
        outside_target = root.parent / f"{root.name}-outside"
        outside_target.mkdir()
        try:
            (outside_scan / "outside").symlink_to(outside_target, target_is_directory=True)
            _check("npmrc-outside-directory", outside_scan, 2, "outside repository root")
        finally:
            outside_target.rmdir()

        unreadable = root / "unreadable"
        _project(unreadable, "one", manifest=True, lockfile=True)
        blocked = unreadable / "blocked"
        blocked.mkdir()
        blocked.chmod(0o000)
        try:
            _check(
                "npmrc-unreadable-directory",
                unreadable,
                2,
                "cannot read npm configuration directory",
            )
        finally:
            blocked.chmod(0o700)

        unreadable_lock = root / "unreadable-lock"
        project = _project(unreadable_lock, "one", manifest=True, lockfile=True)
        lock = project / "package-lock.json"
        lock.chmod(0o000)
        try:
            _check("unreadable-lockfile", unreadable_lock, 2, "cannot read lockfile")
        finally:
            lock.chmod(0o600)
    return _CHECKS.report()


if __name__ == "__main__":
    raise SystemExit(main())
