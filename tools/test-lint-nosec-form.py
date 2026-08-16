#!/usr/bin/env python3
"""Self-test for tools/lint-nosec-form.py.

The risk this guards is not "does it spot a bare `# nosec`" — that is the easy
half. It is that a linter written to catch malformed suppressions goes quiet:
by drifting off bandit's detection, by having its scan scope collapse, or by
being simplified until no input can make it fail. A gate that is silent when it
works and equally silent when it has been broken into a no-op is the shape
ADR-0084 and tools/test-sast-stderr-gate.py exist to refuse.

So the cases below come in three layers:

  * `classify` / `scan_source` — the detection contract, asserted on the *kind*
    of violation, never merely on "something was reported".
  * `main` as a process, against a throwaway git repo — the exit contract
    (0/1/2). Two mutations that a pure-function suite cannot see are covered
    here: a collapsed scan scope reporting success, and a `main` that can never
    return 1.
  * parity with the installed bandit, so an upgrade that moves the parser turns
    the build red instead of silently un-syncing the two.
"""

from __future__ import annotations

import importlib.util
import subprocess  # nosec B404  # list argv, no shell; argv[0] is sys.executable or "git"
import sys
import tempfile
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="strict")
sys.stderr.reconfigure(encoding="utf-8", errors="backslashreplace")

_HERE = Path(__file__).resolve().parent
_LINTER = _HERE / "lint-nosec-form.py"
_SPEC = importlib.util.spec_from_file_location("lint_nosec_form", _LINTER)
assert _SPEC and _SPEC.loader
_MOD = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_MOD)

FAILURES: list[str] = []


def check(label: str, condition: bool, detail: str = "") -> None:
    if condition:
        print(f"  ok   {label}")
    else:
        FAILURES.append(f"{label}{': ' + detail if detail else ''}")
        print(f"  FAIL {label} {detail}")


def kinds(source: str, known=None) -> list[str]:
    return [v.kind for v in _MOD.scan_source(source, "f.py", known)]


def run(args: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(  # nosec B603  # list argv, no shell; argv[0] is sys.executable
        [sys.executable, str(_LINTER), *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
    )


def _git_repo(tmp: Path, files: dict[str, str]) -> Path:
    """Create a throwaway git repo containing `files`, and track them."""
    for name, body in files.items():
        target = tmp / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(body, encoding="utf-8")
    for argv in (["git", "init", "-q"], ["git", "add", "-A"]):
        subprocess.run(argv, cwd=tmp, check=True, capture_output=True)  # nosec B603  # list argv, no shell; argv[0] is "git"
    return tmp


def main() -> int:
    print("lint-nosec-form self-test")

    # ---- detection contract -------------------------------------------------

    # The hole this linter exists for. Bandit treats both as "nosec without
    # test number", skips every test on the statement, and prints nothing — so
    # the stderr gate cannot see them.
    check("bare `# nosec` fires", kinds("x = eval(s)  # nosec\n") == [_MOD.BLANKET])
    check(
        "id-less `# nosec  # reason` fires",
        kinds("x = eval(s)  # nosec  # trusted input\n") == [_MOD.BLANKET],
        "this is the shape the two-`#` form makes look well-formed",
    )

    # The form ADR-0084 reversed. Bandit warns about these, so the stderr gate
    # catches them too — this catches them without a scan, on diffs where
    # SKIP_SAST is set.
    check("em-dash reason fires", kinds("x = eval(s)  # nosec B307 — t\n") == [_MOD.NOT_AN_ID])
    check("hyphen reason fires", kinds("x = eval(s)  # nosec B307 - t\n") == [_MOD.NOT_AN_ID])
    check("bare prose reason fires", kinds("x = eval(s)  # nosec trusted\n") == [_MOD.NOT_AN_ID])

    # Bandit's regex has no word boundary, so this IS a directive with an id
    # list of `like`, resolving to nothing. Parity beats intuition.
    check("`# noseclike` fires", kinds("x = eval(s)  # noseclike\n") == [_MOD.NOT_AN_ID])

    # A test *name* is a form violation but NOT a blanket one — bandit resolves
    # `assert_used` to B101. The message must not claim otherwise.
    name_form = _MOD.scan_source("assert x  # nosec assert_used\n", "f.py")
    check("test-name form fires", [v.kind for v in name_form] == [_MOD.NOT_AN_ID])
    check(
        "test-name message does not overclaim",
        bool(name_form) and "if no word resolves at all" in name_form[0].detail,
        "must state the blanket consequence conditionally",
    )

    # `B404,B603` resolves to {'B603'} alone in bandit 1.9.4 — the comma run
    # collapses to its last capture. Legal-looking and lossy.
    check(
        "comma with no space fires",
        kinds("import subprocess  # nosec B404,B603  # list argv\n") == [_MOD.LOSSY_COMMA],
    )
    check(
        "comma WITH space is silent",
        kinds("import subprocess  # nosec B404, B603  # list argv\n") == [],
    )

    # A separator-only id list. `.strip()` leaves the comma, so the
    # empty-`tests` guard does not see these — bandit resolves all four to an
    # empty set, i.e. blanket. The last is the spec's own dangerous example
    # with one stray comma added.
    for text in ("x = eval(s)  # nosec,\n", "x = eval(s)  # nosec ,\n",
                 "x = eval(s)  # nosec,,\n", "x = eval(s)  # nosec,  # trusted\n"):
        check(f"separator-only id list fires: {text.split('#', 1)[1].strip()!r}",
              kinds(text) == [_MOD.BLANKET], str(kinds(text)))

    # A well-formed id that does not exist resolves to nothing -> blanket.
    # Needs bandit's registry, so it is conditional on bandit being installed.
    ids = _MOD.id_checker()
    if ids is None:
        print("  skip unknown-id cases (bandit not installed)")
    else:
        check("`# nosec B999` fires", kinds("x = eval(s)  # nosec B999  # typo\n", ids) == [_MOD.UNKNOWN_ID])
        check("real id is silent", kinds("x = eval(s)  # nosec B307  # ok\n", ids) == [])

    # Well-formed shapes stay silent.
    check("id alone is silent", kinds("x = eval(s)  # nosec B307\n") == [])
    check("id + second-# reason is silent", kinds("x = eval(s)  # nosec B307  # t\n") == [])
    check("bandit's colon form is silent", kinds("x = eval(s)  # nosec: B307  # ok\n") == [])

    # Not directives. The first is verbatim from tier3.py:43; a word-grep
    # linter would fire on it.
    check(
        "prose mentioning nosec is silent",
        kinds("# hence the name. Bound to its own statement so the nosec covers one value;\nx = 1\n") == [],
    )
    check("`# nosec` inside a string is silent", kinds("s = '# nosec'\n") == [])
    check("`# nosec` inside a docstring is silent", kinds('"""See # nosec."""\nx = 1\n') == [])

    # A form feed is a str.splitlines boundary but not a tokenize one; line
    # numbers must follow tokenize, or the report points at the wrong line.
    located = _MOD.scan_source("x = 1\n\f\ny = eval(s)  # nosec\n", "f.py")
    check("line number survives a form feed", bool(located) and located[0].line == 3,
          str(located[0].line) if located else "no violation")

    # ---- exit contract, as a process ---------------------------------------

    # A scan matching no files must not report success. This is the mutation
    # "collapse DEFAULT_ROOTS to something that matches nothing", which a
    # pure-function suite cannot see at all.
    empty = run(["definitely-not-a-root"])
    check("empty scan exits 2, not 0", empty.returncode == 2,
          f"rc={empty.returncode} {empty.stdout.strip()[:120]}")
    check("empty scan says why", "refusing to report success" in empty.stderr, empty.stderr[:160])

    # A tracked-but-deleted file is skipped, not fatal: `git ls-files` reads the
    # index, and a mid-rebase worktree is not a reason to abort the gate.
    with tempfile.TemporaryDirectory() as raw:
        repo = _git_repo(Path(raw), {"Makefile": "SAST_DIRS := src\n",
                                     "src/a.py": "x = 1  # nosec B101  # fine\n"})
        (repo / "src" / "a.py").unlink()
        listed = _MOD.tracked_python_files(["src"], repo)
        check("a deleted tracked file is still listed by git", listed == [Path("src/a.py")], str(listed))

    # ...and skipping it must not turn the scan into a silent success. `files`
    # is non-empty here while `scanned` falls to 0, which is how the skip
    # re-opened the empty-scan hole the case above guards.
    with tempfile.TemporaryDirectory() as raw:
        gone = _git_repo(Path(raw) / "gone", {
            "Makefile": "SAST_DIRS := src\n",
            "src/only.py": "x = 1  # nosec B101  # fine\n",
            "tools/lint-nosec-form.py": _LINTER.read_text(encoding="utf-8"),
        })
        (gone / "src" / "only.py").unlink()
        result = subprocess.run(  # nosec B603  # list argv, no shell; argv[0] is sys.executable
            [sys.executable, str(gone / "tools" / "lint-nosec-form.py")],
            capture_output=True, text=True, check=False,
        )
        check("all-files-deleted scan exits 2, not 0", result.returncode == 2,
              f"rc={result.returncode} {result.stdout.strip()[:120]}")

    # A surviving file is still scanned when a sibling is missing.
    with tempfile.TemporaryDirectory() as raw:
        partial = _git_repo(Path(raw) / "partial", {
            "Makefile": "SAST_DIRS := src\n",
            "src/missing.py": "x = 1\n",
            "src/bad.py": "y = 1  # nosec\n",
            "tools/lint-nosec-form.py": _LINTER.read_text(encoding="utf-8"),
        })
        (partial / "src" / "missing.py").unlink()
        result = subprocess.run(  # nosec B603  # list argv, no shell; argv[0] is sys.executable
            [sys.executable, str(partial / "tools" / "lint-nosec-form.py")],
            capture_output=True, text=True, check=False,
        )
        check("a missing sibling does not abort the scan", result.returncode == 1,
              f"rc={result.returncode} {(result.stderr or result.stdout)[:160]}")
        check("the surviving file is the one reported", "src/bad.py" in result.stderr,
              result.stderr[:160])

    # A real violation must exit 1. Run against a throwaway repo carrying its
    # own copy of the linter, so REPO_ROOT resolves there: this exercises the
    # whole path — Makefile parsing, `git ls-files`, tokenising, the exit code —
    # without writing to the real repo's index, which a crash between setup and
    # teardown would otherwise leave dirty.
    with tempfile.TemporaryDirectory() as raw:
        sandbox = _git_repo(Path(raw) / "violation", {
            "Makefile": "SAST_DIRS := src\n",
            "src/bad.py": "x = 1  # nosec\n",
            "tools/lint-nosec-form.py": _LINTER.read_text(encoding="utf-8"),
        })
        dirty = subprocess.run(  # nosec B603  # list argv, no shell; argv[0] is sys.executable
            [sys.executable, str(sandbox / "tools" / "lint-nosec-form.py")],
            capture_output=True, text=True, check=False,
        )
        check("a real violation exits 1", dirty.returncode == 1,
              f"rc={dirty.returncode} — a linter that cannot fail is not a gate")
        check("the violation is named on stderr", "src/bad.py" in dirty.stderr,
              dirty.stderr[:200])
        check("the sandbox roots came from its own Makefile",
              _MOD.sast_dirs(sandbox) == ["src"], str(_MOD.sast_dirs(sandbox)))

    # ---- scope and parity ---------------------------------------------------

    # The scan scope is read from the Makefile, not copied. If that ever
    # regresses to a literal, this case is what notices.
    # `SAST_DIRS +=` must be SEEN, so the multiple-assignment guard fires. An
    # earlier pattern missed `+=` entirely, which silently NARROWED the gate
    # relative to the scan — the drift this derivation exists to prevent.
    with tempfile.TemporaryDirectory() as raw:
        appended = Path(raw)
        (appended / "Makefile").write_text("SAST_DIRS := tools packs\nSAST_DIRS += web\n",
                                           encoding="utf-8")
        try:
            _MOD.sast_dirs(appended)
        except _MOD.LintError as exc:
            check("`SAST_DIRS +=` fails loudly", "expected exactly one" in str(exc), str(exc))
        else:
            check("`SAST_DIRS +=` fails loudly", False, "silently ignored the append")

    # Deliberately NOT asserted against a literal list — a third copy of
    # SAST_DIRS is the drift this derivation exists to prevent, and widening
    # the Makefile would red an unrelated file. The sandbox case above proves
    # the derivation; this proves it resolves against the real Makefile.
    roots = _MOD.sast_dirs()
    check("roots derive from the real Makefile", bool(roots) and all(
        (_MOD.REPO_ROOT / r).is_dir() for r in roots), str(roots))

    # ADR-0084's `Revisit if` made mechanical: a bandit upgrade that moves
    # either pattern turns the build red rather than silently un-syncing.
    try:
        from bandit.core import manager  # noqa: PLC0415
    except ImportError:
        print("  skip bandit regex parity (bandit not installed)")
    else:
        check("regex matches bandit's NOSEC_COMMENT",
              _MOD.NOSEC_COMMENT.pattern == manager.NOSEC_COMMENT.pattern,
              f"ours={_MOD.NOSEC_COMMENT.pattern!r} bandit={manager.NOSEC_COMMENT.pattern!r}")
        # The comma-run finding depends on this second pattern; pin it too.
        check("bandit still collapses a comma run",
              manager._parse_nosec_comment("# nosec B404,B603") == {"B603"},
              str(manager._parse_nosec_comment("# nosec B404,B603")))

    # The clean tree passes, and reports a plausible file count — a scope
    # collapse that still finds *some* files would slip past the empty check.
    clean = run([])
    check("clean repo exits 0", clean.returncode == 0, (clean.stderr or clean.stdout)[:300])
    digits = [int(s) for s in clean.stdout.replace("(", " ").split() if s.isdigit()]
    # 500, not 100: the tree has ~790 tracked .py under SAST_DIRS and the
    # largest single root (`packages`) holds ~407, so a collapse to any one
    # root fails this. A floor of 100 would have passed a collapse to `tools`.
    check("clean run scanned a plausible number of files", bool(digits) and max(digits) >= 500,
          clean.stdout.strip()[:160])

    print()
    if FAILURES:
        print(f"lint-nosec-form self-test: {len(FAILURES)} case(s) failed.")
        return 1
    print("lint-nosec-form self-test: all cases passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
