#!/usr/bin/env python3
"""Make-free, cross-platform self-host gate chains (repo-native).

`make build-self` / `make build-check` orchestrate the self-host gates in bash;
on Windows there is no `make`, so a contributor had to invoke each step by hand
and remember the order. This script chains the same steps so the whole gate runs
in one command on any platform:

    python tools/build_gate_chain.py build-self     # lint-packs -> self
    python tools/build_gate_chain.py build-check    # lint-packs -> build -> check
                                                     # -> pre-pr-catalogue
                                                     # -> spec-status (self-test+lint)
                                                     # -> brief-coverage (self-test+lint)
                                                     # -> traceability (self-test+lint)
                                                     # -> first-value-contract (self-test+lint)
                                                     # -> validate-claude-plugin-manifests

**Why it lives in `tools/`, not the shipped `agentbundle` package.** It
orchestrates *this repo's* gates: `build-check` spawns repo-native scripts —
`tools/pre-pr-catalogue.py` (explicitly never projected to adopters) and the
projected `.claude/skills/.../*.py` linters — that do not exist in a `pip
install agentbundle` consumer's tree, so the chain is meaningless (and would
crash) there. The reusable engine (`lint-packs` / `build` / `check` / `self`)
stays in the package as public subcommands; this is the repo-specific wiring,
a sibling of `tools/pre-pr-catalogue.py`. Putting it here keeps the published
package's CLI surface unchanged (no release) and avoids baking repo-only paths
into the wheel.

Single source of truth: the Makefile `build-self` / `build-check` targets route
through this script, and the Python-native steps call the existing
`cmd_lint_packs` / `cmd_build` / `cmd_check` / `cmd_self` handlers — no gate
logic is reimplemented. Pure stdlib; no bash / `sh` / `.sh` / `shell=True`;
paths built with `pathlib`. The Windows-incompatible SAST leg (Semgrep) is not
chained here — it stays Makefile-appended.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path
from typing import Callable

REPO_ROOT = Path(__file__).resolve().parent.parent
# Prefer this repo's source over any stale site-packages install, so a
# contributor needs no PYTHONPATH or editable-install setup — one command.
sys.path.insert(0, str(REPO_ROOT / "packages" / "agentbundle"))

from agentbundle.build.lint_packs import cmd_lint_packs  # noqa: E402
from agentbundle.build.main import cmd_build  # noqa: E402
from agentbundle.build.self_host import cmd_check, cmd_self  # noqa: E402

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
    namespace — there is no argparse default fallback here. Bind via default
    arguments so each thunk captures its own func and namespace.
    """
    def _thunk(func=func, ns=argparse.Namespace(**ns_kwargs)) -> int:
        return int(func(ns))

    return (label, _thunk)


def _script_step(label: str, *path_parts: str) -> Step:
    """Wrap a repo-relative Python script as a chain step.

    Spawns ``[sys.executable, <pathlib path>]`` with ``check=False`` — no shell,
    no bash, no ``shell=True``. The path is built with `pathlib`; `main` chdirs
    to the repo root first, so it resolves on every OS. A missing script makes
    the interpreter exit non-zero, which propagates as this step's code.
    """
    script = Path(*path_parts)

    def _thunk(script=script) -> int:
        return subprocess.run([sys.executable, str(script)], check=False).returncode

    return (label, _thunk)


def build_self(args: argparse.Namespace) -> int:
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


def build_check(args: argparse.Namespace) -> int:
    """`build-check` chain: every Windows-clean step of `make build-check`.

    lint-packs → build → check → pre-pr-catalogue → lint-spec-status
    (self-test + lint) → brief-coverage (self-test + lint) → traceability
    (self-test + lint) → first-value-contract (self-test + lint) →
    validate-claude-plugin-manifests, in that order. The SAST leg is
    intentionally omitted (Semgrep has no Windows support and is conditional)
    — it stays Makefile-appended after this chain.
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
        _script_step(
            "test-lint-traceability",
            ".claude", "skills", "work-loop", "scripts", "test-lint-traceability.py",
        ),
        _script_step(
            "lint-traceability",
            ".claude", "skills", "work-loop", "scripts", "lint-traceability.py",
        ),
        _script_step("test-lint-first-value-contract", "tools", "test-lint-first-value-contract.py"),
        _script_step("lint-first-value-contract", "tools", "lint-first-value-contract.py"),
        _script_step("validate-claude-plugin-manifests", "tools", "validate-claude-plugin-manifests.py"),
    ]
    return _run_chain(steps)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="build_gate_chain",
        description="Make-free self-host gate chains (mirrors the Makefile targets).",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    bs = sub.add_parser("build-self", help="lint-packs then self.")
    bs.add_argument("--dry-run", action="store_true")
    bs.add_argument("--force", action="store_true")
    bs.add_argument("--no-symlink", action="store_true")
    bs.add_argument("--packs-dir", default="packs")
    bs.set_defaults(func=build_self)

    bc = sub.add_parser(
        "build-check",
        help="lint-packs, build, check, pre-pr-catalogue, spec-status, brief-coverage, traceability, first-value-contract, validate-claude-plugin-manifests (no SAST).",
    )
    bc.add_argument("--packs-dir", default="packs")
    bc.add_argument(
        "--output-dir",
        default="dist",
        help="Artifact dir for the build leg (default: dist/); the check leg "
        "always projects against the working tree.",
    )
    bc.set_defaults(func=build_check)

    return parser


def main(argv: list[str] | None = None) -> int:
    # Resolve every repo-relative path (packs/, tools/, .claude/) against the
    # repo root regardless of where the script is invoked from.
    os.chdir(REPO_ROOT)
    args = _build_parser().parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    sys.exit(main())
