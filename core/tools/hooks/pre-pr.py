#!/usr/bin/env python3
"""Pre-PR hook (adopter-facing): the work-loop's mechanical termination
check, plus a place to wire *your* project's gate.

Most agent tools fire no pre-PR / pre-push event, so wire this via a Git
``pre-push`` hook (``.git/hooks/pre-push``) or run it by hand before opening
a PR — the same way regardless of which agent tool you use:

    python tools/hooks/pre-pr.py

What it runs:
  - ``loop-cohort.py check <spec-dir>`` for each ``docs/specs/*/state.json``,
    in ``--phase implement`` and ``--phase review`` — the work-loop's
    iteration/stasis caps. The script ships with the work-loop skill; this
    hook finds it under whichever skills directory your agent tool installed
    into (``.claude/``, ``.agents/``, ``.kiro/`` …). Skipped cleanly when
    there are no active specs (or the work-loop isn't installed).

It deliberately runs **none** of the source project's own artifact linters —
those enforce that project's conventions on its own tree and
don't apply to your repo. Wire your project's lint/typecheck/test commands
into the stub below instead (or let the ``adapt-to-project`` skill do it).

This hook degrades gracefully: a missing tool is a skip with a notice, never
a hard failure.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


# The work-loop skill ships with `core` but lands under different roots
# depending on which agent tool the pack was installed for — so probe the
# known adapter skill directories rather than assuming Claude Code's `.claude/`.
_SKILL_ROOTS = (
    ".claude/skills",  # Claude Code
    ".agents/skills",  # Codex
    ".kiro/skills",    # Kiro
    ".apm/skills",     # APM (and the pack's own source layout)
)


def _find_loop_cohort() -> Path | None:
    """Locate the work-loop's ``loop-cohort.py`` under whichever adapter skill
    root it was installed into. Returns ``None`` when the work-loop isn't
    present (caps check is then skipped, not failed)."""
    for root in _SKILL_ROOTS:
        candidate = Path(root) / "work-loop" / "scripts" / "loop-cohort.py"
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
        result = subprocess.run(argv, capture_output=True, text=True, check=False)
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


def main() -> int:
    repo_root = _repo_root()
    os.chdir(repo_root)

    py = sys.executable  # use the parent interpreter for child scripts

    # --- Work-loop caps gate (ships with `core`) -----------------------------
    loop_cohort = _find_loop_cohort()
    state_files = sorted(Path("docs/specs").glob("*/state.json"))
    if loop_cohort is None:
        print("pre-pr: — loop-cohort.py not found — skipping work-loop caps check")
    elif not state_files:
        print("pre-pr: (no active state.json — skipping loop-cohort check)")
    else:
        for state in state_files:
            spec_dir = state.parent
            for phase in ("implement", "review"):
                result = subprocess.run(
                    [py, str(loop_cohort), "check", str(spec_dir), "--phase", phase],
                    capture_output=True, text=True, check=False,
                )
                if result.returncode != 0:
                    if result.stdout:
                        sys.stdout.write(result.stdout)
                    if result.stderr:
                        sys.stderr.write(result.stderr)
                    print(
                        f"pre-pr: ✖ loop-cohort check {spec_dir} --phase {phase} failed",
                        file=sys.stderr,
                    )
                    sys.exit(1)
                print(f"pre-pr: ✓ loop-cohort check {spec_dir} ({phase})")

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
