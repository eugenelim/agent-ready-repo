"""Make-free, cross-platform self-host gate chains.

`make build-self` and `make build-check` orchestrate the self-host gate steps
in bash; on Windows there is no `make`, so a contributor had to invoke each
`python -m agentbundle.build` subcommand by hand and remember the order. This
module chains those steps into two subcommands — `build-self` and
`build-check` — that run identically on every platform.

Single source of truth: each chain *calls the existing handlers* — `cmd_lint_packs`,
`cmd_build`, `cmd_check`, `cmd_self` — and spawns the repo-relative scripts
(`tools/pre-pr-catalogue.py` and the projected `lint-spec-status` /
`brief-coverage` self-test+lint pairs) via ``sys.executable``. No gate logic is
reimplemented here. The `Makefile` `build-self` / `build-check` targets route
through these subcommands so the step lists exist once and cannot drift.

Windows-clean by construction: pure stdlib, no bash / ``sh`` / ``.sh`` /
``shell=True``, and every spawned-script path is built with `pathlib` (no
hardcoded ``/`` separators). The Windows-incompatible SAST leg (Semgrep) is
*not* chained here — it stays appended after `build-check` in the Makefile, per
the spec's leg-inclusion discriminator (a step belongs in a subcommand iff it is
Windows-clean *and* unconditional).
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path
from typing import Callable

from agentbundle.build.lint_packs import cmd_lint_packs
from agentbundle.build.main import cmd_build
from agentbundle.build.self_host import cmd_check, cmd_self

# A chain step: a human label plus a zero-arg thunk returning an exit code.
Step = tuple[str, Callable[[], int]]


def _run_chain(steps: list[Step]) -> int:
    """Run *steps* in order; stop at the first non-zero and return its code.

    The chain's exit code is the first failing step's code (0 when all pass),
    so a make-free run is as legible as a failed `make` target. Later steps do
    not run once a step fails.
    """
    for label, step in steps:
        rc = int(step())
        if rc != 0:
            print(f"build chain: ✖ {label} failed (exit {rc})", file=sys.stderr)
            return rc
    return 0


def _handler_step(label: str, func: Callable[[argparse.Namespace], int], **ns_kwargs) -> Step:
    """Wrap an in-process handler call as a chain step.

    *ns_kwargs* must carry **every** attribute *func* reads off its args
    namespace — there is no argparse default fallback here. Bind via a default
    argument so each thunk captures its own namespace, not the loop variable.
    """
    def _thunk(func=func, ns=argparse.Namespace(**ns_kwargs)) -> int:
        return int(func(ns))

    return (label, _thunk)


def _script_step(label: str, *path_parts: str) -> Step:
    """Wrap a repo-relative Python script as a chain step.

    Spawns ``[sys.executable, <pathlib path>]`` with ``check=False`` — no shell,
    no bash, no ``shell=True``. The path is built with `pathlib` so it resolves
    cwd-relative on every OS (the chain is a repo-dev gate, run from repo root,
    matching the Makefile and `cmd_self` / `cmd_check`). A missing script makes
    the interpreter exit non-zero, which propagates as this step's code.
    """
    script = Path(*path_parts)

    def _thunk(script=script) -> int:
        return subprocess.run([sys.executable, str(script)], check=False).returncode

    return (label, _thunk)


def cmd_build_self(args: argparse.Namespace) -> int:
    """`build-self` chain: lint-packs → self (mirrors `make build-self`).

    `self` is reached through `cmd_self`, so its `_refuse_fixture_packs_dir`
    guard and the `ALLOW_FIXTURE_PACKS` override fire unchanged.
    """
    packs_dir = args.packs_dir
    steps: list[Step] = [
        _handler_step("lint-packs", cmd_lint_packs, packs_dir=packs_dir),
        _handler_step(
            "self",
            cmd_self,
            packs_dir=packs_dir,
            output_dir=".",
            dry_run=args.dry_run,
            force=args.force,
            no_symlink=args.no_symlink,
        ),
    ]
    return _run_chain(steps)


def cmd_build_check(args: argparse.Namespace) -> int:
    """`build-check` chain: every Windows-clean step of `make build-check`.

    lint-packs → build → check → pre-pr-catalogue → lint-spec-status
    (self-test + lint) → brief-coverage (self-test + lint), in that order. The
    SAST leg is intentionally omitted (Semgrep has no Windows support and is
    conditional) — it stays Makefile-appended after this subcommand.
    """
    packs_dir = args.packs_dir
    steps: list[Step] = [
        _handler_step("lint-packs", cmd_lint_packs, packs_dir=packs_dir),
        _handler_step(
            "build",
            cmd_build,
            packs_dir=packs_dir,
            output_dir=args.output_dir,
            recipe=None,
            pack=None,
        ),
        _handler_step("check", cmd_check, packs_dir=packs_dir, output_dir="."),
        _script_step("pre-pr-catalogue", "tools", "pre-pr-catalogue.py"),
        _script_step(
            "test-lint-spec-status",
            ".claude", "skills", "work-loop", "scripts", "test-lint-spec-status.py",
        ),
        _script_step(
            "lint-spec-status",
            ".claude", "skills", "work-loop", "scripts", "lint-spec-status.py",
        ),
        _script_step(
            "test-lint-brief-coverage",
            ".claude", "skills", "receive-brief", "scripts", "test-lint-brief-coverage.py",
        ),
        _script_step(
            "lint-brief-coverage",
            ".claude", "skills", "receive-brief", "scripts", "lint-brief-coverage.py",
        ),
    ]
    return _run_chain(steps)
