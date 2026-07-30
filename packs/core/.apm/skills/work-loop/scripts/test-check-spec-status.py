#!/usr/bin/env python3
"""Self-test for check-spec-status.py.

Runs the script as a subprocess against fixture directories in a tempdir —
the same shape the loop-engine guard uses.
"""
from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent / "check-spec-status.py"


def run(arg: str | Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), str(arg)],
        capture_output=True,
        text=True,
    )


def write_spec(tmp: Path, status: str) -> Path:
    spec = tmp / "spec.md"
    spec.write_text(
        f"# Spec\n\n**Status:** {status}\n\n## Acceptance Criteria\n",
        encoding="utf-8",
    )
    return spec


def test_exits_0_when_shipped(tmp: Path) -> None:
    write_spec(tmp, "Shipped")
    r = run(tmp)
    assert r.returncode == 0, f"expected 0, got {r.returncode}: {r.stderr}"
    print("  PASS: exits 0 when Status is Shipped")


def test_exits_nonzero_when_implementing(tmp: Path) -> None:
    write_spec(tmp, "Implementing")
    r = run(tmp)
    assert r.returncode != 0
    assert r.stderr.strip()
    print("  PASS: exits non-zero when Status is Implementing")


def test_exits_nonzero_when_draft(tmp: Path) -> None:
    write_spec(tmp, "Draft")
    r = run(tmp)
    assert r.returncode != 0
    print("  PASS: exits non-zero when Status is Draft")


def test_exits_nonzero_when_approved(tmp: Path) -> None:
    write_spec(tmp, "Approved")
    r = run(tmp)
    assert r.returncode != 0
    print("  PASS: exits non-zero when Status is Approved")


def test_exits_nonzero_when_archived(tmp: Path) -> None:
    write_spec(tmp, "Archived")
    r = run(tmp)
    assert r.returncode != 0
    print("  PASS: exits non-zero when Status is Archived")


def test_exits_nonzero_when_spec_absent(tmp: Path) -> None:
    r = run(tmp)
    assert r.returncode != 0
    assert r.stderr.strip()
    print("  PASS: exits non-zero when spec.md absent")


def test_exits_nonzero_when_no_status_line(tmp: Path) -> None:
    (tmp / "spec.md").write_text("# Spec\n\nNo status here.\n", encoding="utf-8")
    r = run(tmp)
    assert r.returncode != 0
    print("  PASS: exits non-zero when no **Status:** line")


def test_file_path_resolves_to_parent(tmp: Path) -> None:
    write_spec(tmp, "Shipped")
    r = run(tmp / "spec.md")
    assert r.returncode == 0, f"expected 0 when passing file path: {r.stderr}"
    print("  PASS: file path resolves to parent dir")


def test_file_path_fails_correctly(tmp: Path) -> None:
    write_spec(tmp, "Draft")
    r = run(tmp / "spec.md")
    assert r.returncode != 0
    print("  PASS: file path with non-Shipped status returns non-zero")


def main() -> None:
    tests = [
        test_exits_0_when_shipped,
        test_exits_nonzero_when_implementing,
        test_exits_nonzero_when_draft,
        test_exits_nonzero_when_approved,
        test_exits_nonzero_when_archived,
        test_exits_nonzero_when_spec_absent,
        test_exits_nonzero_when_no_status_line,
        test_file_path_resolves_to_parent,
        test_file_path_fails_correctly,
    ]
    failed = 0
    for t in tests:
        with tempfile.TemporaryDirectory() as td:
            try:
                t(Path(td))
            except AssertionError as e:
                print(f"  FAIL: {t.__name__}: {e}")
                failed += 1
    if failed:
        print(f"\n{failed} test(s) failed.")
        sys.exit(1)
    print(f"\n{len(tests)} test(s) passed.")


if __name__ == "__main__":
    main()
