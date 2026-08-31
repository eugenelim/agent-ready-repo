#!/usr/bin/env python3
"""Self-test for tools/lint-nosemgrep-form.py."""

from __future__ import annotations

import importlib.util
import os
import subprocess  # nosec B404  # list argv, no shell; argv[0] is sys.executable or "git"
import sys
import tempfile
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="strict")
sys.stderr.reconfigure(encoding="utf-8", errors="backslashreplace")

_HERE = Path(__file__).resolve().parent
_LINTER = _HERE / "lint-nosemgrep-form.py"
_SPEC = importlib.util.spec_from_file_location("lint_nosemgrep_form", _LINTER)
assert _SPEC and _SPEC.loader
_MOD = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_MOD)

FAILURES: list[str] = []
_TOKEN = "no" + "semgrep"
_ALIAS = "no" + "sem"


def check(label: str, condition: bool, detail: str = "") -> None:
    """Record one self-test assertion."""
    if condition:
        print(f"  ok   {label}")
    else:
        FAILURES.append(f"{label}{': ' + detail if detail else ''}")
        print(f"  FAIL {label} {detail}")


def kinds(source: str, path: str) -> list[str]:
    """Return violation kinds from one in-memory source file."""
    return [violation.kind for violation in _MOD.scan_source(source, path)]


def run(
    args: list[str], env: dict[str, str] | None = None
) -> subprocess.CompletedProcess[str]:
    """Invoke the linter as a process for its exit-status contract."""
    return subprocess.run(  # nosec B603  # list argv, no shell; argv[0] is sys.executable
        [sys.executable, str(_LINTER), *args], capture_output=True, text=True, check=False, env=env
    )


def git_repo(tmp: Path, files: dict[str, str | bytes]) -> Path:
    """Create and track a small throwaway repository."""
    for name, body in files.items():
        target = tmp / name
        target.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(body, bytes):
            target.write_bytes(body)
        else:
            target.write_text(body, encoding="utf-8")
    for argv in (["git", "init", "-q"], ["git", "add", "-A"]):
        subprocess.run(argv, cwd=tmp, check=True, capture_output=True)  # nosec B603  # list argv, no shell; argv[0] is "git"
    return tmp


def report() -> int:
    """Render the run's verdict and return the harness exit status.

    The only exit path. The forced-failure child below reaches this same
    function, so a mutation here is caught rather than shadowed by a second
    hardcoded return.
    """
    print()
    if FAILURES:
        print(f"lint-nosemgrep-form self-test: {len(FAILURES)} case(s) failed.")
        return 1
    print("lint-nosemgrep-form self-test: all cases passed.")
    return 0


def main() -> int:
    """Exercise Semgrep parity, form rules, scan scope, and exit codes."""
    print("lint-nosemgrep-form self-test")

    # The forced-failure child records one failure and returns through `report()`
    # so the control exercises the real exit path. It must NOT fall through to the
    # spawn below, or each child spawns another one without bound.
    if os.environ.get("LINT_NOSEMGREP_FORM_TEST_FORCE_FAILURE"):
        check("forced harness failure", False, "controlled self-test mutation")
        return report()

    expected_ids = r"(?:[:=][\s]?(?P<ids>([^,\s](?:[,\s]+)?)+))?"
    check(
        "pinned Semgrep core inline regex text",
        _MOD.SEM_INLINE_RE.pattern == " " + "no" + r"sem(?:grep)?" + expected_ids,
    )
    check(
        "pinned Semgrep core previous-line regex text",
        _MOD.SEM_PREVIOUS_LINE_RE.pattern
        == r"^[^a-zA-Z0-9]* *" + "no" + r"sem(?:grep)?" + expected_ids,
    )
    check("bare pragma fires", kinds("x = 1 # " + _TOKEN + "\n", "x.py") == [_MOD.BLANKET])
    check(
        "id without reason fires",
        kinds("x = 1 # " + _TOKEN + ": rule.id\n", "x.py") == [_MOD.NO_REASON],
    )
    check(
        "id plus reason is silent",
        kinds("x = 1 # " + _TOKEN + ": rule.id # bounded input\n", "x.py") == [],
    )
    check(
        "mid-comment detection is retained",
        kinds("x = 1 # TODO " + _TOKEN + ": rule.id\n", "x.py") == [_MOD.NO_REASON],
    )
    check(
        "prefix detection has no word boundary",
        kinds("x = 1 # " + _TOKEN + "py\n", "x.py") == [_MOD.BLANKET],
    )
    check(
        "case-insensitive detection",
        kinds("x = 1 # " + _TOKEN.upper() + ": rule.id # reason\n", "x.py") == [],
    )
    check(
        "leading-space requirement rejects a non-space prefix",
        kinds("x = 1 # x" + _TOKEN + ": rule.id\n", "x.py") == [],
    )
    check("alias detection", kinds("x = 1 # " + _ALIAS + ": rule.id\n", "x.py") == [_MOD.NO_REASON])
    check(
        "string occurrence is accidental",
        kinds("value = ' " + _TOKEN + "/" + _ALIAS + " comment'; x()\n", "x.py")
        == [_MOD.ACCIDENTAL],
    )
    check(
        "identifier occurrence is accidental",
        kinds("if " + "NO" + "SEMGREP_COMMENT.search(line): x()\n", "x.py")
        == [_MOD.ACCIDENTAL],
    )
    check("slash form", kinds("x(); // " + _TOKEN + "\n", "x.js") == [_MOD.BLANKET])
    check("html form", kinds("<!-- " + _TOKEN + " -->\n", "x.html") == [_MOD.BLANKET])
    check(
        "block-comment form is not accidental",
        kinds("/* " + _TOKEN + ": rule.id */\n", "x.js") == [_MOD.NO_REASON],
    )
    check(
        "previous-line hash pragma fires",
        kinds("#" + _TOKEN + "\nx = 1\n", "x.py") == [_MOD.BLANKET],
    )
    check(
        "previous-line slash pragma fires",
        kinds("//" + _TOKEN + "\nx();\n", "x.js") == [_MOD.BLANKET],
    )
    check(
        "previous-line tab pragma needs a reason",
        kinds("#\t" + _TOKEN + ": rule.id\nx = 1\n", "x.py") == [_MOD.NO_REASON],
    )
    check(
        "comma in reason fires",
        kinds(
            "x = 1 # " + _TOKEN + ": alpha # noisy, beta is fine\n", "x.py"
        )
        == [_MOD.NO_REASON],
    )
    check(
        "line-start identifier is accidental",
        kinds("_NO" + "SEMGREP_COMMENT = 1\n", "x.py") == [_MOD.ACCIDENTAL],
    )

    empty = run(["definitely-not-a-root"])
    check("empty scan exits 2", empty.returncode == 2, f"rc={empty.returncode}")

    clean_tree = run([])
    scanned_match = _MOD.re.search(r"in (\d+) UTF-8 text file\(s\)", clean_tree.stdout)
    scanned_count = int(scanned_match.group(1)) if scanned_match else 0
    # The current tree has 2,731 files and its largest SAST_DIRS root has 217.
    # 2,000 rejects a one-root collapse while retaining roughly 27% churn headroom.
    check("real-tree scan remains broad", scanned_count >= 2000, f"count={scanned_count}")
    check("real-tree lint is clean", clean_tree.returncode == 0, f"rc={clean_tree.returncode}")

    with tempfile.TemporaryDirectory() as raw:
        sandbox = git_repo(Path(raw) / "violation", {
            "Makefile": "SAST_DIRS := src\n",
            "src/bad.js": "x(); // " + _TOKEN + ": rule.id\n",
            "tools/lint-nosemgrep-form.py": _LINTER.read_text(encoding="utf-8"),
        })
        dirty = subprocess.run(  # nosec B603  # list argv, no shell; argv[0] is sys.executable
            [sys.executable, str(sandbox / "tools" / "lint-nosemgrep-form.py")],
            capture_output=True,
            text=True,
            check=False,
        )
        check("a real violation exits 1", dirty.returncode == 1, f"rc={dirty.returncode}")
        check("the violation is named", "src/bad.js" in dirty.stderr, dirty.stderr[:160])

    with tempfile.TemporaryDirectory() as raw:
        binary = git_repo(Path(raw) / "binary", {
            "Makefile": "SAST_DIRS := src\n",
            "src/good.py": "x = 1\n",
            "src/sample.bin": b"\x00\xaa",
            "tools/lint-nosemgrep-form.py": _LINTER.read_text(encoding="utf-8"),
        })
        clean = subprocess.run(  # nosec B603  # list argv, no shell; argv[0] is sys.executable
            [sys.executable, str(binary / "tools" / "lint-nosemgrep-form.py")],
            capture_output=True,
            text=True,
            check=False,
        )
        check("non-UTF-8 file is skipped", clean.returncode == 0, f"rc={clean.returncode}")
        check("non-UTF-8 skip is reported", "skipped 1 non-UTF-8 file(s)" in clean.stdout, clean.stdout[:160])

    with tempfile.TemporaryDirectory() as raw:
        only_binary = git_repo(Path(raw) / "only-binary", {
            "Makefile": "SAST_DIRS := src\n",
            "src/sample.bin": b"\x00\xaa",
            "tools/lint-nosemgrep-form.py": _LINTER.read_text(encoding="utf-8"),
        })
        empty_text = subprocess.run(  # nosec B603  # list argv, no shell; argv[0] is sys.executable
            [sys.executable, str(only_binary / "tools" / "lint-nosemgrep-form.py")],
            capture_output=True,
            text=True,
            check=False,
        )
        check("all-binary scan exits 2", empty_text.returncode == 2, f"rc={empty_text.returncode}")
        check("all-binary scan says why", "refusing to report success" in empty_text.stderr, empty_text.stderr[:160])

    with tempfile.TemporaryDirectory() as raw:
        appended = Path(raw)
        (appended / "Makefile").write_text("SAST_DIRS := tools\nSAST_DIRS += packs\n", encoding="utf-8")
        try:
            _MOD.sast_dirs(appended)
        except _MOD.LintError as exc:
            check("SAST_DIRS append fails loudly", "expected exactly one" in str(exc), str(exc))
        else:
            check("SAST_DIRS append fails loudly", False, "silently narrowed scan scope")

    forced_failure = subprocess.run(  # nosec B603  # list argv, no shell; argv[0] is sys.executable
        [sys.executable, str(Path(__file__).resolve())],
        capture_output=True,
        text=True,
        check=False,
        env={**os.environ, "LINT_NOSEMGREP_FORM_TEST_FORCE_FAILURE": "1"},
    )
    check(
        "a failing harness case exits 1",
        forced_failure.returncode == 1,
        f"rc={forced_failure.returncode}",
    )

    return report()


if __name__ == "__main__":
    raise SystemExit(main())
