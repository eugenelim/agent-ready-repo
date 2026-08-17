#!/usr/bin/env python3
"""Refuses a direct `git check-ignore` subprocess outside the approved helper.

`tools/lint_git_ignore.py` exists so that one process answers for a whole
candidate set. That only holds while nothing else builds its own probe, and the
per-path loop this repository used to carry was easy to write and invisible in
review — it cost 337 subprocesses and 32 seconds per lint run.

**This gate is a drift guard, not a proof.** An AST allowlist cannot see
`"check-" "ignore"` assembled at runtime, `shlex.split`, or starred args. The
strong property is the runtime process count asserted in
`tools/test-lint-boundary-structural.py`; what this adds is that the *obvious*
way to reintroduce the pattern fails loudly in CI.

Two decisions worth stating, because either one done differently leaves the gate
looking green while enforcing nothing:

**`check-ignore` is matched anywhere in an argv sequence.** Not only at position
one. `["git", "-C", root, "check-ignore", …]` is the idiomatic form and would
otherwise pass untouched.

**Exemptions are an explicit file allowlist, never a filename pattern.** In this
repository `tools/test-*.py` files *are* CI gates — `docs.yml` runs one as the
boundary-lint gate and says so — so a `test-*` pattern would carve out precisely
the class being policed. Each exemption is named, with its reason.

The scanned set comes from `git ls-files --cached --others --exclude-standard`,
not a filesystem walk: an editable install under `packages/` would otherwise pull
vendored third-party sources in and make the floor drift per machine, while
tracked-only would let an author add a violating file and see the gate pass right
up until they commit it. A file that cannot be read or parsed **fails** rather
than being skipped, since a silent skip is a self-inflicted bypass.
"""

from __future__ import annotations

import argparse
import ast
import os
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

import lint_git_ignore  # tools/ is sys.path[0] for a script run

sys.stdout.reconfigure(encoding="utf-8", errors="strict")
sys.stderr.reconfigure(encoding="utf-8", errors="backslashreplace")

ROOT = Path(__file__).resolve().parents[1]

#: Roots whose sources are policed. `.github` and the root `Makefile` are in
#: here because both drive the lint targets, so both are plausible sites for a
#: reintroduced per-path loop — and because the non-Python disposition below
#: claims to cover them. An earlier version claimed the coverage without
#: scanning either.
SCAN_ROOTS = ("tools", "packs", "packages", ".github", "Makefile")

#: Files exempt from the rule, each with the reason it is exempt. A filename
#: pattern is deliberately not used — see the module docstring.
ALLOWLIST: dict[str, str] = {
    "tools/lint_git_ignore.py":
        "the approved batch resolver — this is the one place the call belongs",
    "tools/lint-no-direct-check-ignore.py":
        "this gate; its detection fixtures contain the pattern by construction",
    "tools/test-lint-no-direct-check-ignore.py":
        "the gate's own self-test; its fixtures contain the pattern on purpose",
    # tools/test-pre-pr.sh is deliberately NOT here: it only mentions the probe
    # in a comment, which scan_text already skips, and an allowlist entry would
    # hide a future real invocation in that script.
    "tools/test-run-pack-evals.py":
        "asserts a genuine .gitignore fact about one single path, not an "
        "ignore-query loop over candidates",
}

#: Lowest acceptable number of scanned files. A gate that silently stops
#: scanning is worse than no gate, and "inventory is non-empty" is too weak a
#: floor to notice. Recorded in the spec's audit note.
SCANNED_FLOOR = 700

#: Non-Python gate surfaces are covered by a textual search rather than an AST
#: walk. Recorded here so the coverage boundary is explicit rather than implied.
NON_PYTHON_DISPOSITION = (
    "shell, Makefile and workflow surfaces are searched textually; they carry "
    "no argv structure for an AST walk to inspect"
)

_TEXT_SUFFIXES = (".sh", ".yml", ".yaml", ".mk")
_TEXT_NAMES = ("Makefile",)


class GitListingError(RuntimeError):
    """`git ls-files` failed. Distinct from "the tree has no sources".

    Reported by its real cause rather than as an empty inventory: the previous
    message said "no tracked sources found to scan", which names the wrong thing
    at 3am.
    """


@dataclass
class AuditResult:
    """What was inspected, and what was wrong with it."""

    scanned: list[Path] = field(default_factory=list)
    skipped_allowlisted: list[Path] = field(default_factory=list)
    findings: list[str] = field(default_factory=list)


def _argv_strings(node: ast.AST) -> list[str]:
    """String constants in a list/tuple literal, in order."""
    if not isinstance(node, (ast.List, ast.Tuple)):
        return []
    return [
        element.value for element in node.elts
        if isinstance(element, ast.Constant) and isinstance(element.value, str)
    ]


def scan_source(rel: str, source: str) -> list[str]:
    """Findings for one Python source. Unparseable input is a finding."""
    findings: list[str] = []
    try:
        tree = ast.parse(source, filename=rel)
    except (SyntaxError, ValueError) as exc:
        return [
            f"{rel}: cannot be parsed ({exc}); the gate refuses to skip a file "
            f"it cannot inspect"
        ]

    # Track list literals bound to names, so an argv assembled one line earlier
    # is still seen.
    bound: dict[str, list[str]] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            target = node.targets[0]
            if isinstance(target, ast.Name):
                strings = _argv_strings(node.value)
                if strings:
                    bound[target.id] = strings

    def flag(lineno: int, shape: str) -> None:
        findings.append(
            f"{rel}:{lineno}: builds a `git check-ignore` subprocess directly "
            f"({shape}). Route it through tools/lint_git_ignore.py so one "
            f"process answers for the whole candidate set."
        )

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = ""
        try:
            func = ast.unparse(node.func)
        except Exception:  # noqa: BLE001 — an unparseable callee is not our concern
            continue

        is_spawn = (
            func.startswith("subprocess.")
            or func in {"os.system", "os.popen", "system", "popen"}
        )
        if not is_spawn:
            continue

        for argument in node.args:
            # argv list/tuple, anywhere in the sequence
            strings = _argv_strings(argument)
            if "check-ignore" in strings:
                flag(node.lineno, "argv sequence")
                break
            # argv bound to a name on an earlier line
            if (isinstance(argument, ast.Name)
                    and "check-ignore" in bound.get(argument.id, [])):
                flag(node.lineno, f"argv via `{argument.id}`")
                break
            # shell string, f-string or concatenation
            rendered = ""
            try:
                rendered = ast.unparse(argument)
            except Exception:  # noqa: BLE001
                rendered = ""
            if "check-ignore" in rendered and not isinstance(
                argument, (ast.List, ast.Tuple)
            ):
                flag(node.lineno, "shell string")
                break
    return findings


#: `git … check-ignore` on one line, permitting intervening arguments such as
#: `-C "$root"` or `--no-pager` (quoted values included). Deliberately not a bare
#: "check-ignore" substring: that matched this gate's own script name in a `run:`
#: line, six false positives on the first run against `.github`.
_TEXT_INVOCATION = re.compile(r"\bgit\b[^\n]{0,120}?\bcheck-ignore\b")

#: A YAML step label is prose, not a command — `- name: No direct git
#: check-ignore outside the helper` describes the rule rather than breaking it.
_YAML_LABEL = re.compile(r"^-?\s*name:\s")


def scan_text(rel: str, source: str) -> list[str]:
    """Findings for a non-Python gate surface, by textual search.

    Shell, Makefile and workflow lines carry no argv structure for an AST walk,
    so this is a regex over the command form. Matching the *command* rather than
    the substring matters: a step named "No direct git check-ignore …" or a
    `run:` line naming this gate's own script is a reference, not a use.
    """
    findings: list[str] = []
    for lineno, line in enumerate(source.splitlines(), 1):
        stripped = line.strip()
        if stripped.startswith("#"):
            continue                      # a comment about the rule is not a use
        if _YAML_LABEL.match(stripped):
            continue                      # a step label names the rule, not a use
        if _TEXT_INVOCATION.search(stripped):
            findings.append(
                f"{rel}:{lineno}: invokes `git check-ignore` directly. Route it "
                f"through tools/lint_git_ignore.py."
            )
    return findings


def _tracked_files(root: Path) -> list[Path]:
    """Files under the scanned roots that Git would carry.

    `git ls-files` rather than a filesystem walk: an editable install under
    `packages/` leaves build and vendored content on disk that would inflate the
    scanned set and make the floor drift from machine to machine.

    `--others --exclude-standard` includes files that are new but not ignored.
    Tracked-only would let an author add a violating file and see the gate pass
    until the moment they commit it, which is the wrong time to find out.
    """
    proc = subprocess.run(
        ["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard",
         *SCAN_ROOTS],
        cwd=str(root), capture_output=True, check=False,
        # The shared scrub: without it a host `core.excludesFile` filters the
        # `--others` half, so an author whose global ignore matches a newly
        # added file watches this gate skip it and pass.
        env=lint_git_ignore.hermetic_git_env(os.environ),
    )
    if proc.returncode != 0:
        raise GitListingError(
            f"`git ls-files` exited {proc.returncode}: "
            f"{proc.stderr.decode('utf-8', 'replace').strip()[:400]}"
        )
    return [
        root / name for name in
        (chunk.decode("utf-8", "surrogateescape")
         for chunk in proc.stdout.split(b"\0") if chunk)
    ]


def audit(root: Path) -> AuditResult:
    """Inspect every tracked source under the scanned roots."""
    result = AuditResult()
    for path in sorted(_tracked_files(root)):
        try:
            rel = str(path.relative_to(root))
        except ValueError:
            continue
        if rel in ALLOWLIST:
            result.skipped_allowlisted.append(path)
            # Still count it as scanned: "exempt" must not mean "never looked at",
            # so the self-test can prove the helper was in the inventory.
            result.scanned.append(path)
            continue
        is_python = path.suffix == ".py"
        is_text = path.suffix in _TEXT_SUFFIXES or path.name in _TEXT_NAMES
        if not (is_python or is_text):
            continue
        result.scanned.append(path)
        try:
            source = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            result.findings.append(
                f"{rel}: cannot be read ({exc}); the gate refuses to skip a "
                f"file it cannot inspect"
            )
            continue
        if is_python:
            result.findings.extend(scan_source(rel, source))
        else:
            result.findings.extend(scan_text(rel, source))
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Refuse a direct `git check-ignore` outside the approved "
                    "batch helper.",
    )
    parser.add_argument("--root", default=None, metavar="PATH",
                        help="repository root to audit (default: this repository)")
    args = parser.parse_args(argv)
    root = ROOT if args.root is None else Path(args.root).resolve()

    try:
        result = audit(root)
    except GitListingError as exc:
        print(f"✖ {exc}", file=sys.stderr)
        return 1

    if not result.scanned:
        print("✖ no tracked sources found to scan — this must not pass "
              "vacuously", file=sys.stderr)
        return 1

    # Only enforce the floor for the real repository; a fixture root is small
    # on purpose.
    if args.root is None and len(result.scanned) < SCANNED_FLOOR:
        print(f"✖ scanned only {len(result.scanned)} files, below the recorded "
              f"floor of {SCANNED_FLOOR}. Either the scan silently narrowed or "
              f"the floor needs a deliberate update.", file=sys.stderr)
        return 1

    if result.findings:
        for finding in result.findings:
            print(f"FAIL: {finding}", file=sys.stderr)
        print(f"✖ lint-no-direct-check-ignore: {len(result.findings)} "
              f"violation(s) across {len(result.scanned)} scanned file(s)",
              file=sys.stderr)
        return 1

    print(f"ok   [no-direct-check-ignore] ({len(result.scanned)} files scanned, "
          f"{len(result.skipped_allowlisted)} allowlisted)")
    print("✓ lint-no-direct-check-ignore: passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
