#!/usr/bin/env python3
"""Self-test for ``tools/lint-npm-allow-scripts.py``.

Runs the real checker through subprocess against synthetic repositories, then
against the real repository. Exit 0 means every case passed; exit 1 means at
least one assertion failed.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="strict")
sys.stderr.reconfigure(encoding="utf-8", errors="backslashreplace")

ROOT = Path(__file__).resolve().parents[1]
CHECKER = ROOT / "tools" / "lint-npm-allow-scripts.py"

FAILURES: list[str] = []


def check(name: str, condition: bool, detail: str = "") -> None:
    """Record one assertion without aborting the remaining mutation cases."""
    if condition:
        print(f"  ok   {name}")
        return
    FAILURES.append(f"{name}: {detail}" if detail else name)
    print(f"  FAIL {name}: {detail}")


def run(root: Path) -> subprocess.CompletedProcess[str]:
    """Invoke the checker exactly as the build chain does, with a fixture root."""
    return subprocess.run(
        [sys.executable, str(CHECKER), "--root", str(root)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )


def write_project(
    root: Path,
    *,
    project: str = "site",
    packages: dict[str, object] | None = None,
    allow_scripts: dict[str, object] | None = None,
) -> Path:
    """Write one minimal npm project and return its directory."""
    project_dir = root / project
    project_dir.mkdir(parents=True, exist_ok=True)
    lock = {
        "name": project,
        "lockfileVersion": 3,
        "packages": packages
        if packages is not None
        else {
            "": {"name": project, "version": "1.0.0"},
            "node_modules/esbuild": {
                "version": "0.28.1",
                "hasInstallScript": True,
            },
        },
    }
    package = {
        "name": project,
        "version": "1.0.0",
        "private": True,
        "allowScripts": allow_scripts
        if allow_scripts is not None
        else {"esbuild@0.28.1": True},
    }
    (project_dir / "package-lock.json").write_text(
        json.dumps(lock), encoding="utf-8", newline="\n"
    )
    (project_dir / "package.json").write_text(
        json.dumps(package), encoding="utf-8", newline="\n"
    )
    return project_dir


def fixture_root(prefix: str) -> Path:
    """Create a fixture root whose cleanup cannot mask successful assertions."""
    return Path(tempfile.mkdtemp(prefix=prefix))


def combined(proc: subprocess.CompletedProcess[str]) -> str:
    """Return both streams for concise diagnostic assertions."""
    return f"{proc.stdout}\n{proc.stderr}"


def main() -> int:
    print("test-lint-npm-allow-scripts:")

    root = fixture_root("npm-allow-clean-")
    try:
        write_project(root)
        proc = run(root)
        check("clean fixture exits 0", proc.returncode == 0, combined(proc))
        check(
            "clean verdict names the checked lockfile",
            "site/package-lock.json" in combined(proc),
            combined(proc),
        )
    finally:
        # This environment may deny os.rmdir during TemporaryDirectory cleanup.
        # Best-effort cleanup must not turn already-passed assertions into errors.
        shutil.rmtree(root, ignore_errors=True)

    root = fixture_root("npm-allow-unallowlisted-")
    try:
        write_project(
            root,
            packages={
                "": {"name": "site", "version": "1.0.0"},
                "node_modules/fsevents": {
                    "version": "2.3.3",
                    "hasInstallScript": True,
                },
            },
            allow_scripts={},
        )
        proc = run(root)
        check(
            "unallowlisted install script exits 1",
            proc.returncode == 1,
            combined(proc),
        )
        check(
            "unallowlisted diagnostic names the offender",
            "fsevents@2.3.3" in combined(proc),
            combined(proc),
        )
    finally:
        shutil.rmtree(root, ignore_errors=True)

    root = fixture_root("npm-allow-stale-")
    try:
        write_project(
            root,
            packages={"": {"name": "site", "version": "1.0.0"}},
            allow_scripts={"fsevents@2.3.3": True},
        )
        proc = run(root)
        check("stale allowScripts entry exits 1", proc.returncode == 1, combined(proc))
        check(
            "stale diagnostic names the permission",
            "fsevents@2.3.3" in combined(proc),
            combined(proc),
        )
    finally:
        shutil.rmtree(root, ignore_errors=True)

    root = fixture_root("npm-allow-nested-")
    try:
        write_project(
            root,
            packages={
                "": {"name": "site", "version": "1.0.0"},
                "node_modules/a/node_modules/b": {
                    "version": "4.5.6",
                    "hasInstallScript": True,
                },
            },
            allow_scripts={"b@4.5.6": True},
        )
        proc = run(root)
        check(
            "nested dependency uses the last node_modules segment",
            proc.returncode == 0,
            combined(proc),
        )
        check(
            "nested verdict names b@4.5.6",
            "b@4.5.6" in combined(proc),
            combined(proc),
        )
    finally:
        shutil.rmtree(root, ignore_errors=True)

    root = fixture_root("npm-allow-scoped-")
    try:
        write_project(
            root,
            packages={
                "": {"name": "site", "version": "1.0.0"},
                "node_modules/@scope/pkg": {
                    "version": "7.8.9",
                    "hasInstallScript": True,
                },
            },
            allow_scripts={"@scope/pkg@7.8.9": True},
        )
        proc = run(root)
        check("scoped package name is preserved", proc.returncode == 0, combined(proc))
        check(
            "scoped verdict names @scope/pkg@7.8.9",
            "@scope/pkg@7.8.9" in combined(proc),
            combined(proc),
        )
    finally:
        shutil.rmtree(root, ignore_errors=True)

    root = fixture_root("npm-allow-alias-")
    try:
        write_project(
            root,
            packages={
                "": {"name": "site", "version": "1.0.0"},
                "node_modules/myfse": {
                    "name": "fsevents",
                    "version": "2.3.3",
                    "hasInstallScript": True,
                },
            },
            allow_scripts={"fsevents@2.3.3": True},
        )
        proc = run(root)
        check("npm alias uses the entry name", proc.returncode == 0, combined(proc))
        check(
            "npm alias verdict names fsevents@2.3.3",
            "fsevents@2.3.3" in proc.stdout and "myfse@2.3.3" not in combined(proc),
            combined(proc),
        )
    finally:
        shutil.rmtree(root, ignore_errors=True)

    root = fixture_root("npm-allow-root-script-")
    try:
        write_project(
            root,
            packages={
                "": {
                    "name": "lockfile-name-is-not-authoritative",
                    "version": "9.9.9",
                    "hasInstallScript": True,
                }
            },
            allow_scripts={"site@1.0.0": True},
        )
        proc = run(root)
        check(
            "project install script exits 0 when allowed",
            proc.returncode == 0,
            combined(proc),
        )
        check(
            "project install script uses manifest identity",
            "site@1.0.0" in proc.stdout,
            combined(proc),
        )
    finally:
        shutil.rmtree(root, ignore_errors=True)

    root = fixture_root("npm-allow-no-lock-")
    try:
        proc = run(root)
        check("no discovered lockfile exits 2", proc.returncode == 2, combined(proc))

        missing = root / "no-such-root"
        proc = run(missing)
        check("nonexistent --root exits 2", proc.returncode == 2, combined(proc))
        check(
            "nonexistent --root names the path",
            missing.name in combined(proc),
            combined(proc),
        )
        check(
            "nonexistent --root has no traceback",
            "Traceback" not in combined(proc),
            combined(proc),
        )

        not_a_directory = root / "not-a-directory"
        not_a_directory.write_text("fixture", encoding="utf-8")
        proc = run(not_a_directory)
        check("file-valued --root exits 2", proc.returncode == 2, combined(proc))
        check(
            "file-valued --root names the path",
            not_a_directory.name in combined(proc),
            combined(proc),
        )
        check(
            "file-valued --root has no traceback",
            "Traceback" not in combined(proc),
            combined(proc),
        )
    finally:
        shutil.rmtree(root, ignore_errors=True)

    root = fixture_root("npm-allow-false-")
    try:
        write_project(
            root,
            packages={
                "": {"name": "site", "version": "1.0.0"},
                "node_modules/evil": {
                    "version": "1.0.0",
                    "hasInstallScript": True,
                },
            },
            allow_scripts={"evil@1.0.0": False},
        )
        proc = run(root)
        check(
            "false allowScripts value exits 1",
            proc.returncode == 1,
            combined(proc),
        )
        check(
            "false allowScripts value does not permit the package",
            "unallowlisted install-script entry evil@1.0.0" in combined(proc),
            combined(proc),
        )
    finally:
        shutil.rmtree(root, ignore_errors=True)

    root = fixture_root("npm-allow-non-boolean-")
    try:
        write_project(root, allow_scripts={"esbuild@0.28.1": "yes"})
        proc = run(root)
        check(
            "non-boolean allowScripts value exits 2",
            proc.returncode == 2,
            combined(proc),
        )
        check(
            "non-boolean allowScripts diagnostic names the key",
            "esbuild@0.28.1" in combined(proc),
            combined(proc),
        )
    finally:
        shutil.rmtree(root, ignore_errors=True)

    root = fixture_root("npm-allow-invalid-utf8-")
    try:
        project = write_project(root)
        (project / "package-lock.json").write_bytes(b"\xff\xfe")
        proc = run(root)
        check("unreadable JSON exits 2", proc.returncode == 2, combined(proc))
    finally:
        shutil.rmtree(root, ignore_errors=True)

    root = fixture_root("npm-allow-bad-package-json-")
    try:
        project = write_project(root)
        (project / "package.json").write_text("{not-json", encoding="utf-8")
        proc = run(root)
        check("unparseable package.json exits 2", proc.returncode == 2, combined(proc))
    finally:
        shutil.rmtree(root, ignore_errors=True)

    root = fixture_root("npm-allow-missing-package-json-")
    try:
        project = write_project(root)
        (project / "package.json").unlink()
        proc = run(root)
        check(
            "missing sibling package.json exits 2",
            proc.returncode == 2,
            combined(proc),
        )
    finally:
        shutil.rmtree(root, ignore_errors=True)

    root = fixture_root("npm-allow-no-packages-")
    try:
        project = write_project(root)
        (project / "package-lock.json").write_text(
            json.dumps({"lockfileVersion": 3}), encoding="utf-8", newline="\n"
        )
        proc = run(root)
        check("lockfile without packages exits 2", proc.returncode == 2, combined(proc))
    finally:
        shutil.rmtree(root, ignore_errors=True)

    root = fixture_root("npm-allow-no-allow-scripts-")
    try:
        project = write_project(root)
        (project / "package.json").write_text(
            json.dumps({"name": "site", "private": True}),
            encoding="utf-8",
            newline="\n",
        )
        proc = run(root)
        check(
            "package.json without allowScripts exits 2",
            proc.returncode == 2,
            combined(proc),
        )
    finally:
        shutil.rmtree(root, ignore_errors=True)

    root = fixture_root("npm-allow-pruning-")
    try:
        write_project(root)
        ignored = root / "node_modules" / "dependency"
        hidden = root / ".cache" / "fixture"
        violating_packages = {
            "": {"name": "pruned", "version": "1.0.0"},
            "node_modules/evil": {
                "version": "1.0.0",
                "hasInstallScript": True,
            },
        }
        ignored_project = write_project(
            ignored, packages=violating_packages, allow_scripts={}
        )
        hidden_project = write_project(
            hidden, packages=violating_packages, allow_scripts={}
        )
        proc = run(root)
        check(
            "node_modules and dot-directories are pruned",
            proc.returncode == 0,
            combined(proc),
        )
        check(
            "pruned project paths are absent from stdout",
            all(
                project.relative_to(root).as_posix() not in proc.stdout
                for project in (ignored_project, hidden_project)
            ),
            combined(proc),
        )
    finally:
        shutil.rmtree(root, ignore_errors=True)

    proc = run(ROOT)
    check("real repository exits 0", proc.returncode == 0, combined(proc))
    check(
        "real repository covers web and docs-site",
        "web/package-lock.json" in proc.stdout
        and "docs-site/package-lock.json" in proc.stdout,
        combined(proc),
    )

    if FAILURES:
        for failure in FAILURES:
            print(f"FAIL {failure}", file=sys.stderr)
        print(
            f"test-lint-npm-allow-scripts: FAIL ({len(FAILURES)} assertion(s))",
            file=sys.stderr,
        )
        return 1
    print("test-lint-npm-allow-scripts: ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
