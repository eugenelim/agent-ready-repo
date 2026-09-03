#!/usr/bin/env python3
"""Enforce Semgrep suppression form without weakening Semgrep's detection.

Run: python3 tools/lint-nosemgrep-form.py [<root> ...]
Exit 0 = clean, 1 = violations, 2 = usage/tool error (including an empty scan).

The scan roots come from Makefile's SAST_DIRS. It makes one bounded pass over
the UTF-8 text files below those roots — tracked *and* untracked-but-unignored,
matching what the semgrep gate's directory walk would see — and it never asks
Git about individual files. The scan is deliberately not suffix-filtered:
Semgrep's configured languages can change, while its raw-line suppression
matcher is language-independent. Scanning this small superset prevents a new
recognised source suffix from becoming a fail-open gap.

Cost, measured 2026-08-31 on darwin 25.5.0 / Python 3.13.13: 3.56 s over ~2,700
files, one bounded pass, zero ignore queries. Recorded here rather than in
`docs/specs/lint-performance-p0/notes/lint-inventory.md`, which is a frozen
dated capture: `docs/CONVENTIONS.md` rule 4 keeps the operative figure in a
Living file at the point of use instead of patching the historical record.
"""

from __future__ import annotations

import re
import subprocess  # nosec B404  # list argv, no shell; argv[0] is the literal "git"
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="strict")
sys.stderr.reconfigure(encoding="utf-8", errors="backslashreplace")

REPO_ROOT = Path(__file__).resolve().parent.parent
_SAST_DIRS_RE = re.compile(r"^SAST_DIRS\s*[:+?]*=\s*(.+)$", re.MULTILINE)

# These are Semgrep 1.175.0's live core-binary strings, extracted from
# `semgrep/bin/semgrep-core` beside `OSS/src/reporting/Nosemgrep.ml`.
# `semgrep/constants.py` is not the live matcher: its only live suppression
# constant is `NOSEM_INLINE_COMMENT_RE`, used by `rule_match.py` for fingerprint
# normalisation. Note the previous-line pattern allows ZERO spaces, where
# `constants.py` requires one — copying the Python constant is a fail-open bug.
#
# The self-test compares these literals against its own copy, so it catches a
# local edit. It cannot catch upstream drift: `tools/requirements-sast.txt` pins
# `semgrep>=1.174,<2`, a floating range, so an upstream change to the accepted
# suppression form would not be caught here.
#
# The identifiers above are backticked and the literals below are split on
# purpose: this file must never contain the directive token in a shape Semgrep
# honours, or its own source becomes a real suppression that this lint reports.
# Note backticking is NOT sufficient at the start of a comment line, because the
# previous-line pattern's `[^a-zA-Z0-9]*` consumes the marker and the backtick
# alike. Keep the spelled token out of this file entirely.
CORE_RULE_IDS_PATTERN = r"(?:[:=][\s]?(?P<ids>([^,\s](?:[,\s]+)?)+))?"
CORE_INLINE_PATTERN = " " + r"nosem(?:grep)?"
CORE_PREVIOUS_LINE_PATTERN = r"^[^a-zA-Z0-9]* *" + r"nosem(?:grep)?"
SEM_INLINE_RE = re.compile(CORE_INLINE_PATTERN + CORE_RULE_IDS_PATTERN, re.IGNORECASE)
SEM_PREVIOUS_LINE_RE = re.compile(
    CORE_PREVIOUS_LINE_PATTERN + CORE_RULE_IDS_PATTERN, re.IGNORECASE
)

_COMMENT_MARKER_RE = re.compile(r"#|//|<!--|/\*")
_DIRECTIVE_TOKEN_RE = re.compile(r"nosem(?:grep)?", re.IGNORECASE)

BLANKET = "blanket"
NO_REASON = "no-reason"
ACCIDENTAL = "accidental"


class LintError(RuntimeError):
    """A tool-level failure: the requested scan could not be completed."""


class Violation:
    """One risky Semgrep suppression and the information needed to fix it."""

    def __init__(self, path: str, line: int, kind: str, text: str, detail: str):
        self.path = path
        self.line = line
        self.kind = kind
        self.text = text
        self.detail = detail

    def render(self) -> str:
        """Render this violation for the command-line report."""
        return f"  {self.path}:{self.line}: {self.detail}\n      {self.text.strip()}"


def sast_dirs(root: Path | None = None) -> list[str]:
    """Return the Makefile's SAST_DIRS roots without invoking make."""
    makefile = (root or REPO_ROOT) / "Makefile"
    try:
        text = makefile.read_text(encoding="utf-8")
    except OSError as exc:
        raise LintError(f"could not read {makefile}: {exc}") from None
    matches = _SAST_DIRS_RE.findall(text)
    if not matches:
        raise LintError(f"no `SAST_DIRS :=` assignment in {makefile}")
    if len(matches) != 1:
        raise LintError(
            f"{len(matches)} `SAST_DIRS` assignments in {makefile}; expected exactly one"
        )
    roots = matches[0].split("#", 1)[0].split()
    if not roots:
        raise LintError(f"`SAST_DIRS` in {makefile} is empty")
    return roots


def tracked_source_files(roots: list[str], root: Path | None = None) -> list[Path]:
    """Return sorted scannable files in the configured Semgrep roots.

    `--cached --others --exclude-standard` deliberately, not bare `ls-files`.
    The gate this mirrors (`run-semgrep-gate.py ... $(SAST_DIRS)`) walks the
    directories, so it honours a suppression in a file that is not committed
    yet. A tracked-only listing cannot see the files a change *adds*, which is
    exactly when an author needs the answer — and it hid a real blanket
    suppression in this lint's own source until the file was staged.
    `--exclude-standard` keeps gitignored build output out.
    """
    completed = subprocess.run(  # nosec B603, B607  # list argv, no shell; "git" from PATH, roots from the Makefile
        ["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard", "--", *roots],
        cwd=root or REPO_ROOT,
        capture_output=True,
        encoding="utf-8",
        errors="surrogateescape",
        check=False,
    )
    if completed.returncode != 0:
        raise LintError(completed.stderr.strip() or "git ls-files failed")
    return sorted(Path(name) for name in completed.stdout.split("\0") if name)


def classify(
    line: str, match: re.Match[str], *, previous_line: bool
) -> tuple[str, str] | None:
    """Classify one Semgrep match, or return None for an approved form."""
    token = _DIRECTIVE_TOKEN_RE.search(line, match.start())
    if token is None:
        raise LintError("suppression match did not contain its directive token")
    if not _COMMENT_MARKER_RE.search(line[:token.start()]):
        if previous_line:
            return (
                ACCIDENTAL,
                "a line-start Semgrep suppression token applies to the next line; "
                "rename this identifier so it contains no suppression token, because "
                "adding punctuation before it can still form a next-line pragma",
            )
        return (
            ACCIDENTAL,
            "raw code or prose contains a Semgrep suppression token; Semgrep will "
            "silently suppress every matching rule on this line. Break the token "
            "with a non-space character before it",
        )
    target = " on the next line" if previous_line else " on this line"
    ids = (match.group("ids") or "").strip()
    if not ids:
        return (
            BLANKET,
            "a Semgrep suppression with no rule ID can suppress every matching rule"
            f"{target}; "
            "name the rule and add a reason after a second comment marker without commas",
        )
    reason_marker = _COMMENT_MARKER_RE.search(line[token.end():])
    if not reason_marker:
        return (
            NO_REASON,
            f"a Semgrep suppression{target} needs a reason after a second comment marker; "
            "that marker does not terminate Semgrep's rule-id parser",
        )
    reason = line[token.end() + reason_marker.end():]
    if not reason.strip():
        return (
            NO_REASON,
            f"a Semgrep suppression{target} has a comment marker but no reason after it; "
            "the prose is the requirement, not the delimiter",
        )
    if "," in reason:
        return (
            NO_REASON,
            f"a comma in the reason extends Semgrep's rule-id list{target}, silently widening "
            "the suppression; remove the comma or rewrite the reason",
        )
    return None


def scan_source(source: str, path: str) -> list[Violation]:
    """Return violations found by one raw-line pass through a source file."""
    violations: list[Violation] = []
    for number, line in enumerate(source.split("\n"), 1):
        # A core previous-line pragma suppresses the following raw line.
        previous_line_match = SEM_PREVIOUS_LINE_RE.search(line)
        match = previous_line_match or SEM_INLINE_RE.search(line)
        if match is None:
            continue
        verdict = classify(line, match, previous_line=previous_line_match is not None)
        if verdict is None:
            continue
        kind, detail = verdict
        violations.append(Violation(path, number, kind, line, detail))
    return violations


def main(argv: list[str]) -> int:
    """Run the repository form lint and return its documented exit status."""
    base = REPO_ROOT
    try:
        roots = argv[1:] or sast_dirs(base)
        files = tracked_source_files(roots, base)
    except (LintError, OSError, UnicodeDecodeError) as exc:
        print(f"lint-nosemgrep-form: {exc}", file=sys.stderr)
        return 2
    if not files:
        print(
            f"lint-nosemgrep-form: no tracked sources under {' '.join(roots)} "
            "— refusing to report success on an empty scan",
            file=sys.stderr,
        )
        return 2

    violations: list[Violation] = []
    scanned = 0
    skipped = 0
    try:
        for relative in files:
            absolute = base / relative
            if not absolute.exists():
                continue
            try:
                source = absolute.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                skipped += 1
                continue
            except OSError as exc:
                print(f"lint-nosemgrep-form: could not read {relative}: {exc}", file=sys.stderr)
                return 2
            violations.extend(scan_source(source, relative.as_posix()))
            scanned += 1
    except LintError as exc:
        print(f"lint-nosemgrep-form: {exc}", file=sys.stderr)
        return 2

    if scanned == 0:
        print(
            "lint-nosemgrep-form: no UTF-8 text sources were available "
            f"({skipped} non-UTF-8 file(s) skipped) — refusing to report success on an empty scan",
            file=sys.stderr,
        )
        return 2
    if violations:
        print(
            f"lint-nosemgrep-form: FAIL — {len(violations)} malformed suppression(s) "
            f"in {scanned} UTF-8 text file(s); skipped {skipped} non-UTF-8 file(s):",
            file=sys.stderr,
        )
        for violation in violations:
            print(violation.render(), file=sys.stderr)
        return 1
    print(
        f"lint-nosemgrep-form: OK — every suppression in {scanned} UTF-8 text file(s) "
        f"carries a rule-id list and a comma-free second-comment reason; "
        f"skipped {skipped} non-UTF-8 file(s)."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
