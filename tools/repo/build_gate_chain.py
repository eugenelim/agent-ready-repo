#!/usr/bin/env python3
"""Make-free, cross-platform self-host gate chains (repo-native).

`make build-self` / `make build-check` orchestrate the self-host gates; on
Windows there is no `make`, so contributors invoke this script instead:

    python tools/repo/build_gate_chain.py build-self
    python tools/repo/build_gate_chain.py build-check

**Why it lives in `tools/repo/`, not the shipped `agentbundle` package.** It
orchestrates *this repo's* gates: `build-check` spawns repo-native scripts —
`tools/catalogue/pre_pr_catalogue.py` (explicitly never projected to adopters)
and the projected `.claude/skills/.../*.py` linters — that do not exist in a
`pip install agentbundle` consumer's tree. The reusable engine (`catalogue
lint` / `build` / `verify` / `self-host`) is the public `agentbundle catalogue`
surface; this is the repo-specific wiring. Putting it here keeps the published
package's CLI surface unchanged (no release) and avoids baking repo-only paths
into the wheel.

The Windows-incompatible SAST leg (Semgrep) is intentionally NOT chained here
— it stays Makefile-appended.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path
from typing import Callable

# Windows cp1252 guard — reconfigure stdout/stderr to UTF-8 before any print.
sys.stdout.reconfigure(encoding="utf-8", errors="strict")
sys.stderr.reconfigure(encoding="utf-8", errors="backslashreplace")

# tools/repo/ → tools/ → repo root
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
# Make packages/agentbundle importable in-process (for any future in-process use).
_AGENTBUNDLE_PATH = str(REPO_ROOT / "packages" / "agentbundle")
sys.path.insert(0, _AGENTBUNDLE_PATH)

# A chain step: a human label plus a zero-arg thunk returning an exit code.
Step = tuple[str, Callable[[], int]]


def _agentbundle_env() -> dict:
    """Env with packages/agentbundle on PYTHONPATH for subprocess agentbundle calls."""
    env = os.environ.copy()
    pp = env.get("PYTHONPATH", "")
    parts = [p for p in pp.split(os.pathsep) if p]
    if _AGENTBUNDLE_PATH not in parts:
        env["PYTHONPATH"] = os.pathsep.join([_AGENTBUNDLE_PATH] + parts)
    return env


def _run_chain(steps: list[Step]) -> int:
    """Run *steps* in order; stop at the first non-zero and return its code."""
    for label, step in steps:
        rc = int(step())
        if rc != 0:
            print(f"build chain: ✖ {label} failed (exit {rc})", file=sys.stderr)
            return rc
    return 0


def _handler_step(label: str, func: Callable[[argparse.Namespace], int], **ns_kwargs) -> Step:
    """Wrap an in-process handler call as a chain step."""
    def _thunk(func=func, ns=argparse.Namespace(**ns_kwargs)) -> int:  # noqa: B008
        return int(func(ns))

    return (label, _thunk)


def _script_step(label: str, *path_parts: str) -> Step:
    """Wrap a repo-relative Python script as a chain step."""
    script = Path(*path_parts)

    def _thunk(script=script) -> int:
        return subprocess.run([sys.executable, str(script)], check=False).returncode

    return (label, _thunk)


def _module_step(label: str, *cmd_args: str) -> Step:
    """Run ``python -m agentbundle <cmd_args>`` as a chain step.

    Propagates PYTHONPATH so packages/agentbundle is importable in the
    subprocess regardless of the caller's environment.
    """
    env = _agentbundle_env()

    def _thunk(env=env) -> int:
        return subprocess.run(
            [sys.executable, "-m", "agentbundle"] + list(cmd_args),
            check=False,
            env=env,
        ).returncode

    return (label, _thunk)


def build_self(args: argparse.Namespace) -> int:
    """`build-self` chain: agentbundle catalogue self-host --write (mirrors `make build-self`)."""
    op_args: list[str]
    if args.dry_run:
        op_args = ["--check"]
        label = "catalogue self-host --check"
    else:
        op_args = ["--write"] + (["--force"] if args.force else [])
        label = "catalogue self-host --write"

    steps: list[Step] = [
        _module_step(label, "catalogue", "self-host", "--root", ".", *op_args),
    ]
    return _run_chain(steps)


def build_check(args: argparse.Namespace) -> int:
    """`build-check` chain: every Windows-clean step after `agentbundle catalogue verify`.

    The portable verify (lint, build, schema, self-host drift) runs before this
    chain is invoked — via `make build-check` or the caller. This chain handles
    the repo-specific gates: build output for manifest validation, the manifest
    validator itself, the catalogue pre-PR aggregator, and the spec/traceability
    policy linters.

    The SAST leg is intentionally omitted (Semgrep has no Windows support and
    is conditional) — it stays Makefile-appended after this chain.
    """
    steps: list[Step] = [
        _module_step(
            "catalogue-build",
            "catalogue", "build", "--root", ".", "--output", args.output_dir,
        ),
        _script_step("pre-pr-catalogue", "tools", "catalogue", "pre_pr_catalogue.py"),
        _script_step(
            "check-contract-parity",
            "tools", "catalogue", "check_contract_parity.py",
        ),
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
        _script_step(
            "test-loop-engine",
            ".claude", "skills", "work-loop", "scripts", "test-loop-engine.py",
        ),
        _script_step(
            "test-check-spec-status",
            ".claude", "skills", "work-loop", "scripts", "test-check-spec-status.py",
        ),
    ]
    return _run_chain(steps)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="build_gate_chain",
        description="Make-free self-host gate chains (mirrors the Makefile targets).",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    bs = sub.add_parser("build-self", help="catalogue self-host (write or check).")
    bs.add_argument("--dry-run", action="store_true", help="Check mode (read-only).")
    bs.add_argument("--force", action="store_true", help="Force overwrite existing projections.")
    bs.add_argument(
        "--no-symlink", action="store_true",
        help="Ignored (handled by agentbundle internally).",
    )
    bs.add_argument("--packs-dir", default="packs", help="Ignored (resolved via --root .).")
    bs.set_defaults(func=build_self)

    bc = sub.add_parser(
        "build-check",
        help="catalogue build, validate-manifests, pre-pr-catalogue, spec-status, "
             "brief-coverage, traceability (no portable verify, no SAST).",
    )
    bc.add_argument("--packs-dir", default="packs", help="Ignored (resolved via --root .).")
    bc.add_argument(
        "--output-dir",
        default="dist",
        help="Artifact dir for the catalogue build leg (default: dist/).",
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
