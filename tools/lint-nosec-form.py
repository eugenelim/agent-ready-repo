#!/usr/bin/env python3
"""Enforce the bandit suppression-comment form. Rules and rationale: bandit.yaml.

`tools/run-bandit-gate.py` fails `make sast` on any bandit stderr, which catches
every malformed suppression bandit *warns* about. It cannot catch a directive
that resolves to no test id: bandit's `core/tester.py` treats an empty resolved
set as "nosec without test number" and skips **every** test on the statement,
printing nothing. Fail-open and silent — this linter is that backstop.

It reproduces bandit's own detection rather than grepping, because only parity
is safe in both directions. `core/manager.py` tokenises each file and hands
every COMMENT token to `_parse_nosec_comment`, which runs

    NOSEC_COMMENT = re.compile(r"#\\s*nosec:?\\s*(?P<tests>[^#]+)?#?")

as a `search`. So a directive inside a string literal is not one (tokenize),
and `# noseclike` IS one (no word boundary — the captured id list is `like`,
which resolves to nothing). The same applies to prose: a comment *quoting* the
directive form is a directive.

Four violation kinds, each a distinct way a suppression covers more than it says:

  blanket      no id at all -> skips every test on the statement, silently.
  not-an-id    prose or a test *name* reached the id list.
  lossy-comma  `B404,B603` -> bandit keeps only `B603` (see _COMMA_RUN).
  unknown-id   `B999` has an id's shape but resolves to nothing -> blanket.

Run: python3 tools/lint-nosec-form.py [<root> ...]
Exit 0 = every suppression well-formed, 1 = violations, 2 = usage/tool error
(including a scan that matched no files — a silent no-op is not a pass).
Proven by tools/test-lint-nosec-form.py.
"""

from __future__ import annotations

import io
import re
import subprocess  # nosec B404  # list argv, no shell; argv[0] is the literal "git"
import sys
import tokenize
from pathlib import Path
from typing import Callable

# Windows cp1252 guard — reconfigure stdout/stderr to UTF-8 before any print.
sys.stdout.reconfigure(encoding="utf-8", errors="strict")
sys.stderr.reconfigure(encoding="utf-8", errors="backslashreplace")

REPO_ROOT = Path(__file__).resolve().parent.parent

# Kept byte-identical to bandit/core/manager.py's NOSEC_COMMENT (1.9.4). A
# bandit upgrade that changes it must change this too — ADR-0084's `Revisit if`
# trigger, pinned by a self-test case rather than left to memory.
NOSEC_COMMENT = re.compile(r"#\s*nosec:?\s*(?P<tests>[^#]+)?#?")

# The repo's documented id form. Narrower than bandit's, which also accepts a
# test *name* (`assert_used`); bandit.yaml requires the numeric ID.
TEST_ID = re.compile(r"^B\d+$")

# How the captured id list is broken into tokens. Bandit does NOT split: it runs
# NOSEC_COMMENT_TESTS = r"(?:(B\d+|[a-z\d_]+),?)+" as a `finditer`, whose
# repeated group keeps only its LAST capture per match — so `B404,B603` yields
# `{'B603'}` (measured on 1.9.4) while `B404, B603` yields both. Splitting on
# whitespace-or-comma here is deliberately *wider* than bandit's matcher: it
# must see every token bandit could, plus the ones it cannot.
_ID_SEPARATOR = re.compile(r"[,\s]+")

# Two ids joined by a bare comma — the shape bandit's repeated capture group
# collapses. Deliberately NOT `,\S`: measured on 1.9.4, `B404,,B603` and
# `,B404` both resolve fully, so reporting them as lossy would be false.
_COMMA_RUN = re.compile(r"B\d+,B\d+")

# The scanned roots are the Makefile's SAST_DIRS, read at runtime rather than
# copied. Makefile:185 exists so consumers read that variable "instead of
# hard-coding the lists, so the workflow predicate can't drift from them and
# silently skip the scan on a newly-added scannable dir" — a second copy here
# would be the exact drift it warns about. Parsed rather than shelled out to
# `make`, because this chain is deliberately make-free (Windows).
_SAST_DIRS_RE = re.compile(r"^SAST_DIRS\s*[:+?]*=\s*(.+)$", re.MULTILINE)

BLANKET = "blanket"
NOT_AN_ID = "not-an-id"
LOSSY_COMMA = "lossy-comma"
UNKNOWN_ID = "unknown-id"


class LintError(RuntimeError):
    """A tool-level failure: the scan could not be performed as specified."""


def sast_dirs(root: Path | None = None) -> list[str]:
    """Return the Makefile's SAST_DIRS as a list of roots."""
    makefile = (root or REPO_ROOT) / "Makefile"
    try:
        text = makefile.read_text(encoding="utf-8")
    except OSError as exc:
        raise LintError(f"could not read {makefile}: {exc}") from None
    matches = _SAST_DIRS_RE.findall(text)
    if not matches:
        raise LintError(f"no `SAST_DIRS :=` assignment in {makefile}")
    if len(matches) > 1:
        # A later `SAST_DIRS +=` would be invisible to a first-match parse, and
        # invisible means a NARROWER gate than the scan — the exact drift this
        # derivation exists to prevent. Fail loudly instead.
        raise LintError(
            f"{len(matches)} `SAST_DIRS` assignments in {makefile}; expected exactly one"
        )
    roots = matches[0].split("#", 1)[0].split()
    if not roots:
        raise LintError(f"`SAST_DIRS` in {makefile} is empty")
    return roots


def id_checker() -> Callable[[str], bool] | None:
    """Return bandit's own `check_id`, or None when bandit is absent.

    `check_id` rather than `plugins_by_id`: the B3xx range is bandit's
    *blacklist* registry, not its plugin registry, so a plugins-only lookup
    reports every `# nosec B310` in this repo as unknown. `check_id` consults
    plugins, blacklist and builtins — it is the same predicate bandit applies
    when resolving a directive, which is the only thing worth matching.

    Optional by design. AGENTS.md requires this script to be pure stdlib, so it
    must do its job with no third-party import — but where bandit *is* installed
    (any environment that runs `make sast`) its registry is the only way to
    catch a well-formed id that does not exist. `# nosec B999  # typo` has the
    shape of an id, resolves to nothing, and is therefore a blanket
    suppression; a one-character typo is the likeliest real instance of exactly
    the failure class this gate exists for.
    """
    try:
        from bandit.core import extension_loader  # noqa: PLC0415

        return extension_loader.MANAGER.check_id
    except Exception:  # noqa: BLE001
        # Not just ImportError: importing builds MANAGER from installed entry
        # points, so a broken plugin distribution or an API move raises
        # something else. Falling back to "registry unavailable" keeps that a
        # degraded scan rather than a traceback with exit 1 — a status this
        # tool's contract reserves for "violations found".
        return None


class Violation:
    """One malformed suppression, with the text needed to fix it."""

    def __init__(self, path: str, line: int, kind: str, comment: str, detail: str):
        self.path = path
        self.line = line
        self.kind = kind
        self.comment = comment
        self.detail = detail

    def render(self) -> str:
        return f"  {self.path}:{self.line}: {self.detail}\n      {self.comment.strip()}"


def classify(
    comment: str, known_ids: Callable[[str], bool] | None = None
) -> tuple[str, str] | None:
    """Return `(kind, detail)` for a malformed suppression, or None if fine.

    None covers both "well-formed directive" and "not a directive at all"; the
    caller does not need to tell those apart, only whether to report.
    """
    match = NOSEC_COMMENT.search(comment)
    if not match:
        return None

    tests = (match.group("tests") or "").strip()
    if not tests:
        return (
            BLANKET,
            "`# nosec` with no test ID suppresses EVERY test on this statement, "
            "and bandit reports nothing. Write the ID, reason after a second `#`",
        )

    tokens = [token for token in _ID_SEPARATOR.split(tests) if token]

    if not tokens:
        # `tests` was non-empty but held only separators: a directive whose id
        # list is nothing but commas and whitespace. Bandit resolves every such
        # form to an empty set (measured on 1.9.4), so they are blanket
        # suppressions — and the earlier `not tests` guard does not see them,
        # because `.strip()` removes the whitespace but leaves the comma.
        # (Spelled in prose, not quoted: a comment quoting a directive is one.)
        return (
            BLANKET,
            "the id list is punctuation only, which bandit resolves to no test "
            "— so this suppresses EVERY test on the statement, silently. Write "
            "the ID, reason after a second `#`",
        )

    stray = [token for token in tokens if not TEST_ID.match(token)]

    if stray:
        # Deliberately does not claim which consequence follows. Bandit also
        # resolves test *names* (`assert_used` -> B101), and a stdlib-only
        # linter cannot know that registry, so `assert_used` is certainly a form
        # violation but is NOT a blanket one. Naming both outcomes and asserting
        # neither is the only honest message.
        return (
            NOT_AN_ID,
            f"{', '.join(stray)} reached bandit's test-id parser — text after "
            "`# nosec` is read as a list of test IDs up to the next `#`. A word "
            "that collides with a real test name silently widens the "
            "suppression; if no word resolves at all, bandit suppresses EVERY "
            "test on the statement. Put the reason after a SECOND `#`",
        )

    if _COMMA_RUN.search(tests):
        return (
            LOSSY_COMMA,
            "a comma with no following space drops every id but the last — "
            "bandit keeps only the final capture of a comma run, so `B404,B603` "
            "suppresses B603 alone. Separate ids with `, ` (comma AND space)",
        )

    if known_ids is not None:
        unknown = [token for token in tokens if not known_ids(token)]
        if unknown:
            return (
                UNKNOWN_ID,
                f"{', '.join(unknown)} is not a bandit test ID. It has the shape "
                "of one, so it reads as correct, but bandit resolves it to "
                "nothing — and a directive resolving to no id suppresses EVERY "
                "test on the statement",
            )

    return None


def scan_source(
    source: str, path: str, known_ids: Callable[[str], bool] | None = None
) -> list[Violation]:
    """Return every malformed suppression in `source`.

    Tokenises as bandit does, so a `# nosec` inside a string literal is not a
    directive. `io.StringIO(...).readline` rather than `str.splitlines`: the
    latter also breaks on \\v, \\f, \\x1c-\\x1e, \\x85, \\u2028 and \\u2029,
    which desynchronises the token stream from real line numbers and can abort
    a file bandit tokenises cleanly.
    """
    violations: list[Violation] = []
    for token in tokenize.generate_tokens(io.StringIO(source).readline):
        if token.type != tokenize.COMMENT:
            continue
        verdict = classify(token.string, known_ids)
        if verdict is None:
            continue
        kind, detail = verdict
        violations.append(Violation(path, token.start[0], kind, token.string, detail))
    return violations


def tracked_python_files(roots: list[str], root: Path | None = None) -> list[Path]:
    """Return git-tracked `*.py` under `roots`, repo-relative, sorted.

    Tracked-only because `packages/agentbundle/build/lib/` holds gitignored
    copies of tracked modules: bandit does read them when they exist, so a
    report there is a duplicate of one already raised against the real file.
    """
    completed = subprocess.run(  # nosec B603, B607  # list argv, no shell; "git" from PATH, roots from the Makefile
        ["git", "ls-files", "-z", "--", *roots],
        cwd=root or REPO_ROOT,
        capture_output=True,
        encoding="utf-8",
        errors="surrogateescape",
        check=False,
    )
    if completed.returncode != 0:
        raise LintError(completed.stderr.strip() or "git ls-files failed")
    return sorted(Path(name) for name in completed.stdout.split("\0") if name.endswith(".py"))


def main(argv: list[str]) -> int:
    base = REPO_ROOT
    try:
        roots = argv[1:] or sast_dirs(base)
        files = tracked_python_files(roots, base)
    except (LintError, OSError, UnicodeDecodeError) as exc:
        print(f"lint-nosec-form: {exc}", file=sys.stderr)
        return 2

    if not files:
        # A scan that reads nothing must not look like a scan that found
        # nothing: a typo'd or renamed root is the cheapest way to turn this
        # gate into a silent no-op.
        print(
            f"lint-nosec-form: no tracked *.py under {' '.join(roots)} — "
            "refusing to report success on an empty scan",
            file=sys.stderr,
        )
        return 2

    known_ids = id_checker()
    caveat = "" if known_ids is not None else " (bandit absent: IDs not resolved)"
    violations: list[Violation] = []
    scanned = 0
    for relative in files:
        absolute = base / relative
        if not absolute.exists():
            # Tracked in the index but absent from the worktree (mid-rebase,
            # partial checkout). Skipping beats aborting the whole gate.
            continue
        try:
            # tokenize.open honours the BOM and PEP 263 coding cookies, as
            # bandit's own reader does; read_text(encoding="utf-8") would
            # reject a file bandit scans cleanly.
            with tokenize.open(absolute) as handle:
                source = handle.read()
        except (OSError, UnicodeDecodeError, SyntaxError) as exc:
            print(f"lint-nosec-form: could not read {relative}: {exc}", file=sys.stderr)
            return 2
        try:
            violations.extend(scan_source(source, relative.as_posix(), known_ids))
        except (tokenize.TokenError, IndentationError, SyntaxError) as exc:
            print(f"lint-nosec-form: could not tokenise {relative}: {exc}", file=sys.stderr)
            return 2
        scanned += 1

    if scanned == 0:
        # `files` being non-empty is not enough: every listed file can be absent
        # from the worktree, and the skip below would then report a clean scan
        # of nothing. This guard and the `not files` one above look redundant
        # and are not — the skip re-opened exactly the hole that one closes.
        print(
            f"lint-nosec-form: {len(files)} file(s) tracked under "
            f"{' '.join(roots)} but none present on disk — refusing to report "
            "success on an empty scan",
            file=sys.stderr,
        )
        return 2

    if violations:
        print(
            f"lint-nosec-form: FAIL — {len(violations)} malformed suppression(s) "
            f"in {scanned} tracked file(s){caveat}:",
            file=sys.stderr,
        )
        for violation in violations:
            print(violation.render(), file=sys.stderr)
        print(
            "\nThe ID is mandatory and any reason goes after a second `#`.\n"
            "See bandit.yaml's header comment and ADR-0084.",
            file=sys.stderr,
        )
        return 1

    print(
        f"lint-nosec-form: OK — every suppression in {scanned} tracked file(s) "
        f"carries a test ID, with any reason behind a second `#`{caveat}."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
