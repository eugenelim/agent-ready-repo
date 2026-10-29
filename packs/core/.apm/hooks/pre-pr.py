#!/usr/bin/env python3
"""Pre-PR hook (adopter-facing): the work-loop's mechanical termination
check, plus a place to wire *your* project's gate.

Most agent tools fire no pre-PR / pre-push event, so wire this via a Git
``pre-push`` hook (``.git/hooks/pre-push``) or run it by hand before opening
a PR — the same way regardless of which agent tool you use:

    python tools/hooks/pre-pr.py

What it runs:
  - ``lint-knowledge.py`` over ``docs/knowledge/patterns.jsonl`` — the
    knowledge base the work-loop's Capture step appends to. The
    file is yours and the gate that validates it ships with it, so there is
    nothing to wire. Skipped cleanly when the file is absent.
  - ``work-supervisor.py status <spec-dir> --check`` for each
    ``docs/specs/*/delivery/approvals.jsonl`` — the supervisor's own readiness
    check. Runs are found from that committed file, not from the deletable
    ``.supervisor/run.json``. Fails on any non-zero exit, and fails (rather
    than skips) when an approved run exists but the supervisor script cannot be
    found. Passes when no spec holds an ``approvals.jsonl``.
  - The work-loop scripts ship with the work-loop skill; this hook finds
    them under whichever skills directory your agent tool installed into
    (``.claude/``, ``.agents/``, ``.kiro/`` …) — same for ``lint-knowledge.py``
    above.

It deliberately runs **none** of the source project's own artifact linters —
those enforce that project's conventions on its own tree and
don't apply to your repo. Wire your project's lint/typecheck/test commands
into the stub below instead (or let the ``adapt-to-project`` skill do it).

This hook degrades gracefully: a missing tool is a skip with a notice, never
a hard failure. The one exception is the supervisor check: when an approved
run exists but ``work-supervisor.py`` cannot be found, the hook fails.
"""

from __future__ import annotations

import os
import stat
import subprocess
import sys
from pathlib import Path

# Windows cp1252 guard — reconfigure stdout/stderr to UTF-8 before any print.
sys.stdout.reconfigure(encoding="utf-8", errors="strict")
sys.stderr.reconfigure(encoding="utf-8", errors="backslashreplace")


# The work-loop skill ships with `core` but lands under different roots
# depending on which agent tool the pack was installed for — so probe the
# known adapter skill directories rather than assuming Claude Code's `.claude/`.
_SKILL_ROOTS = (
    ".claude/skills",  # Claude Code
    ".agents/skills",  # Codex
    ".kiro/skills",    # Kiro
    ".apm/skills",     # APM (and the pack's own source layout)
)


def _find_work_loop_script(name: str) -> Path | None:
    """Locate one of the work-loop's ``scripts/`` under whichever adapter skill
    root the pack was installed into. Returns ``None`` when the work-loop isn't
    present (the dependent check is then skipped, not failed)."""
    for root in _SKILL_ROOTS:
        candidate = Path(root) / "work-loop" / "scripts" / name
        if candidate.is_file():
            return candidate
    return None


def _repo_root() -> Path:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True, text=True, check=False,
        )
        if result.returncode == 0 and result.stdout.strip():
            return Path(result.stdout.strip())
    except FileNotFoundError:
        pass
    return Path.cwd()


def _run(label: str, argv: list[str]) -> None:
    """Run *argv*; on non-zero exit, surface the tool's output, print the
    failure line, and ``sys.exit(1)``. On success, print the success line.

    A missing executable/script is treated as a **skip** (not a failure) so a
    fresh adopter tree that hasn't wired a given gate yet doesn't hard-crash.
    """
    try:
        result = subprocess.run(
            argv, capture_output=True, text=True, encoding="utf-8", check=False
        )
    except FileNotFoundError:
        # To stderr (not stdout) so a *wired-but-mistyped* tool is visually
        # distinct from a passing check and doesn't scroll past as a ✓.
        print(f"pre-pr: — {label} skipped (not found: {argv[0]})", file=sys.stderr)
        return
    if result.returncode != 0:
        if result.stdout:
            sys.stdout.write(result.stdout)
        if result.stderr:
            sys.stderr.write(result.stderr)
        print(f"pre-pr: ✖ {label} failed", file=sys.stderr)
        sys.exit(1)
    print(f"pre-pr: ✓ {label}")


def _is_plain(path: Path, *, want_dir: bool) -> bool:
    """True when *path* is a real directory/regular file and not a link."""
    try:
        info = path.lstat()
    except OSError:
        return False
    reparse = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
    if stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & reparse:
        return False
    return stat.S_ISDIR(info.st_mode) if want_dir else stat.S_ISREG(info.st_mode)


def _supervised_spec_dirs() -> list[Path]:
    """Spec directories holding ``delivery/approvals.jsonl``, confined.

    Only entries that resolve inside the repository and cross no link count:
    a linked spec directory, ``delivery`` directory, or ``approvals.jsonl`` is
    not discovered. Stdlib only, because an adopter's hook interpreter need not
    be able to import ``agentbundle``.
    """
    root = Path.cwd()
    specs = root / "docs" / "specs"
    if not (_is_plain(root / "docs", want_dir=True) and _is_plain(specs, want_dir=True)):
        return []
    real_root = os.path.realpath(root)
    found: list[Path] = []
    try:
        spec_dirs = sorted(specs.iterdir())
    except OSError:
        return []
    for spec_dir in spec_dirs:
        approvals = spec_dir / "delivery" / "approvals.jsonl"
        if not (
            _is_plain(spec_dir, want_dir=True)
            and _is_plain(spec_dir / "delivery", want_dir=True)
            and _is_plain(approvals, want_dir=False)
        ):
            continue
        real = os.path.realpath(approvals)
        if os.path.commonpath([real_root, real]) != real_root:
            continue
        found.append(spec_dir)
    return found


def _supervisor_check() -> None:
    """Fail when any approved run's ``status --check`` exits non-zero."""
    spec_dirs = _supervised_spec_dirs()
    if not spec_dirs:
        print("pre-pr: (no delivery/approvals.jsonl — skipping supervisor check)")
        return
    supervisor = _find_work_loop_script("work-supervisor.py")
    if supervisor is None:
        print(
            "pre-pr: ✖ work-supervisor.py not found under any known skills root "
            "— an approved run exists and was NOT checked",
            file=sys.stderr,
        )
        sys.exit(1)
    root = Path.cwd()
    for found in spec_dirs:
        # The supervisor accepts only a repository-relative POSIX path.
        spec_dir = found.relative_to(root).as_posix()
        result = subprocess.run(
            [sys.executable, str(supervisor), "status", spec_dir, "--check"],
            cwd=root, capture_output=True, text=True, encoding="utf-8", check=False,
        )
        if result.returncode != 0:
            if result.stdout:
                sys.stdout.write(result.stdout)
            if result.stderr:
                sys.stderr.write(result.stderr)
            print(
                f"pre-pr: ✖ supervisor status {spec_dir} --check failed "
                f"(exit {result.returncode})",
                file=sys.stderr,
            )
            sys.exit(1)
        print(f"pre-pr: ✓ supervisor status {spec_dir}")


def main() -> int:
    repo_root = _repo_root()
    os.chdir(repo_root)

    py = sys.executable  # use the parent interpreter for child scripts

    # --- Knowledge-base gate (ships with `core`) -----------------------------
    # `docs/knowledge/patterns.jsonl` is seeded into your repo and appended to
    # by the work-loop's Capture step, so the gate that validates it
    # ships too — nothing to wire by hand.
    knowledge_file = Path("docs/knowledge/patterns.jsonl")
    lint_knowledge = _find_work_loop_script("lint-knowledge.py")
    if not knowledge_file.is_file():
        print("pre-pr: (no docs/knowledge/patterns.jsonl — skipping knowledge lint)")
    elif lint_knowledge is None:
        # stderr, not stdout: the knowledge base exists but nothing checked it.
        # A ✓-shaped line on stdout would scroll past as if it had been gated.
        print(
            "pre-pr: — lint-knowledge.py not found under any known skills root "
            "— docs/knowledge/patterns.jsonl was NOT checked",
            file=sys.stderr,
        )
    else:
        _run("knowledge lint", [py, str(lint_knowledge)])

    # --- Supervisor readiness gate (ships with `core`) -----------------------
    _supervisor_check()

    # --- Wire your own gate here ---------------------------------------------
    # This is your project's pre-PR gate. Add your lint / typecheck / test
    # commands as `_run(...)` calls — they run in repo-root, fail the hook on a
    # non-zero exit, and skip gracefully if the tool isn't present. Examples:
    #
    #   _run("lint", ["make", "lint"])
    #   _run("typecheck", ["npx", "tsc", "--noEmit"])
    #   _run("test", ["make", "test"])
    #
    # (The `adapt-to-project` skill can fill these in from your project's
    # detected build/test commands.)

    print("pre-pr: all checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
