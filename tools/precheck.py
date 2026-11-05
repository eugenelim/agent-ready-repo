#!/usr/bin/env python3
"""Path-triggered precheck: run only the local checks the changed paths call for.

Changed paths are the union of ``git diff --name-only <base>...HEAD`` and the
working-tree changes. Each path is mapped to the checks that guard it; a check
whose tool is not installed in this interpreter prints ``skipped: <tool> not
installed`` and leaves the exit status alone. Pack pytest suites run only with
``--with-tests``; otherwise the command is printed.

Run: python3 tools/precheck.py [--base <ref>] [--with-tests]
Exit 0 = every run check passed, non-zero = a check failed, 2 = base or git unusable.
"""

from __future__ import annotations

import argparse
import importlib.machinery
import importlib.util
import os
import re
import subprocess  # nosec B404  # list argv, no shell
import sys
from collections.abc import Callable, Mapping
from pathlib import Path
from types import ModuleType

REPO_ROOT = Path(__file__).resolve().parent.parent
GATE_SCRIPT = REPO_ROOT / "tools" / "run-bandit-gate.py"
DEFAULT_BASE = "origin/main"

# (exit status, captured text). `capture` is "none", "stderr" or "stdout".
Executor = Callable[[list[str], str], tuple[int, str]]

# The Makefile's PYTHONPATH (l.16): how this checkout makes agentbundle importable.
CHECKOUT_PYTHONPATH = tuple(
    str(REPO_ROOT / "packages" / name)
    for name in ("agentbundle", "credbroker", "jsonl-otlp-exporter")
)


class GitError(Exception):
    """A git command the run depends on exited non-zero."""


_PACK_RE = re.compile(r"^packs/([^/]+)/")
_APM_RE = re.compile(r"^packs/[^/]+/\.apm/")
_CORE_RELEASE_RE = re.compile(
    r"^packs/core/(seeds/|\.apm/)|^packs/core/(pack\.toml|\.claude-plugin/plugin\.json)$"
)
_DISPLAY = {"agentbundle": "agentbundle", "yaml": "PyYAML", "bandit": "bandit"}


def subprocess_executor(argv: list[str], capture: str) -> tuple[int, str]:
    """Run `argv` from the repo root; stream output except what `capture` names."""
    proc = subprocess.run(  # nosec B603  # list argv, no shell; argv built by this module
        argv,
        cwd=REPO_ROOT,
        env=child_env(os.environ),
        stdout=subprocess.PIPE if capture == "stdout" else None,
        stderr=subprocess.PIPE if capture == "stderr" else None,
        text=True,
        check=False,
    )
    return proc.returncode, (proc.stdout if capture == "stdout" else proc.stderr) or ""


def child_env(base_env: Mapping[str, str]) -> dict[str, str]:
    """`base_env` with the checkout's package paths ahead of any existing PYTHONPATH."""
    env = dict(base_env)
    existing = [env["PYTHONPATH"]] if env.get("PYTHONPATH") else []
    env["PYTHONPATH"] = os.pathsep.join([*CHECKOUT_PYTHONPATH, *existing])
    return env


def _installed(module: str) -> bool:
    """True when `module` is importable here or from the checkout's package paths."""
    if importlib.util.find_spec(module) is not None:
        return True
    return importlib.machinery.PathFinder.find_spec(module, list(CHECKOUT_PYTHONPATH)) is not None


def load_gate() -> ModuleType:
    """Import tools/run-bandit-gate.py by path so FLOOR and CONFIG are not copied."""
    spec = importlib.util.spec_from_file_location("run_bandit_gate", GATE_SCRIPT)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {GATE_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def scan_roots() -> list[str]:
    """The gate's scan roots: the Makefile's `SAST_DIRS` (the gate takes them as argv)."""
    text = (REPO_ROOT / "Makefile").read_text(encoding="utf-8")
    match = re.search(r"^SAST_DIRS\s*:=\s*(.+)$", text, re.M)
    if match is None:
        raise ValueError("Makefile defines no SAST_DIRS")
    return match.group(1).split()


def changed_paths(base: str, executor: Executor) -> list[str]:
    """Union of committed (`base...HEAD`) and working-tree changes, in first-seen order."""
    paths: list[str] = []
    diff_argv = ["git", "-c", "core.quotePath=false", "diff", "--name-only", "--no-renames", "-z"]
    diff_argv.append(f"{base}...HEAD")
    code, diff = executor(diff_argv, "stdout")
    if code != 0:
        raise GitError(f"`{' '.join(diff_argv)}` exited {code} (base {base!r})")
    paths.extend(name for name in diff.split("\0") if name)
    status_argv = ["git", "status", "--porcelain", "-z", "--untracked-files=all"]
    code, status = executor(status_argv, "stdout")
    if code != 0:
        raise GitError(f"`{' '.join(status_argv)}` exited {code} (base {base!r})")
    entries = iter(status.split("\0"))
    for entry in entries:
        if len(entry) < 4:
            continue
        paths.append(entry[3:])
        if "R" in entry[:2] or "C" in entry[:2]:  # either column: source is the next entry
            paths.append(next(entries, ""))
    return list(dict.fromkeys(p for p in paths if p))


def touched_packs(paths: list[str]) -> list[str]:
    """Pack names with at least one changed path, sorted."""
    return sorted({m.group(1) for p in paths if (m := _PACK_RE.match(p))})


def _skip(label: str, tool: str) -> None:
    print(f"precheck: {label}: skipped: {_DISPLAY[tool]} not installed")


def _run_check(
    label: str,
    argv: list[str],
    needs: tuple[str, ...],
    executor: Executor,
    is_installed: Callable[[str], bool],
) -> int:
    """Run one check, or print a named skip per missing tool and return 0."""
    missing = [tool for tool in needs if not is_installed(tool)]
    if missing:
        for tool in missing:
            _skip(label, tool)
        return 0
    print(f"precheck: {label}: {' '.join(argv)}")
    status, _ = executor(argv, "none")
    return status


def _run_bandit(
    files: list[str], python: str, executor: Executor, is_installed: Callable[[str], bool]
) -> int:
    """Bandit at the gate's floor and config; any stderr is a failure."""
    if not is_installed("bandit"):
        _skip("bandit", "bandit")
        return 0
    gate = load_gate()
    argv = [python, "-m", "bandit", *files, "-c", gate.CONFIG, *gate.FLOOR]
    print(f"precheck: bandit: {' '.join(argv)}")
    status, stderr = executor(argv, "stderr")
    if stderr.strip():
        sys.stderr.write(stderr if stderr.endswith("\n") else stderr + "\n")
        return status or 1
    return status


def run_checks(
    paths: list[str],
    *,
    base: str,
    python: str,
    with_tests: bool,
    executor: Executor,
    is_installed: Callable[[str], bool] = _installed,
    file_exists: Callable[[str], bool] | None = None,
    dir_exists: Callable[[str], bool] | None = None,
) -> int:
    """Run every check the changed `paths` trigger; return the worst exit status."""
    exists = file_exists or (lambda p: (REPO_ROOT / p).is_file())
    has_dir = dir_exists or (lambda p: (REPO_ROOT / p).is_dir())
    results: list[int] = []
    ran = False

    if any(_APM_RE.match(p) for p in paths):
        ran = True
        argv = [python, "-m", "agentbundle", "catalogue", "self-host", "--root", ".", "--check"]
        results.append(_run_check("self-host", argv, ("agentbundle",), executor, is_installed))

    if any(p.startswith("packs/") and p.rsplit("/", 1)[-1] == "SKILL.md" for p in paths):
        ran = True
        argv = [python, "-m", "agentbundle", "catalogue", "lint", "--root", ".", "--deep"]
        needs = ("agentbundle", "yaml")
        results.append(_run_check("deep lint", argv, needs, executor, is_installed))

    if any(_CORE_RELEASE_RE.match(p) for p in paths):
        ran = True
        argv = [python, "tools/check-core-release.py", f"--base={base}"]
        results.append(_run_check("core release", argv, (), executor, is_installed))

    roots = tuple(f"{r}/" for r in scan_roots())
    files = [p for p in paths if p.endswith(".py") and p.startswith(roots) and exists(p)]
    if files:
        ran = True
        results.append(_run_bandit(files, python, executor, is_installed))

    for pack in touched_packs(paths):
        suite = f"packs/{pack}/tests"
        if not has_dir(suite):
            ran = True
            print(f"precheck: pack tests ({pack}): skipped: {suite} does not exist")
        elif with_tests:
            ran = True
            argv = [python, "-m", "pytest", suite, "-q"]
            results.append(_run_check("pack tests", argv, (), executor, is_installed))
        else:
            ran = True
            print(f"precheck: not run (pass --with-tests): python -m pytest {suite} -q")

    if not ran:
        print("no trigger matched")
    failed = [r for r in results if r != 0]
    # A signal-killed check returns negative; it must not hide behind a 0.
    return max((r for r in failed if r > 0), default=1 if failed else 0)


def parse_args(argv: list[str]) -> argparse.Namespace:
    """Parse the command line."""
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--base", default=DEFAULT_BASE, help=f"base ref (default {DEFAULT_BASE})")
    parser.add_argument(
        "--with-tests", action="store_true", help="run each touched pack's pytest suite"
    )
    return parser.parse_args(argv)


def main(
    argv: list[str] | None = None,
    *,
    executor: Executor = subprocess_executor,
    python: str = sys.executable,
) -> int:
    """Resolve the base, collect changed paths, run the triggered checks."""
    args = parse_args(sys.argv[1:] if argv is None else argv)
    try:
        status, _ = executor(["git", "rev-parse", "--verify", f"{args.base}^{{commit}}"], "stdout")
        if status != 0:
            print(f"precheck: base {args.base!r} does not resolve", file=sys.stderr)
            return 2
        paths = changed_paths(args.base, executor)
    except GitError as exc:
        print(f"precheck: {exc}", file=sys.stderr)
        return 2
    except OSError as exc:
        print(f"precheck: cannot run git: {exc}", file=sys.stderr)
        return 2
    return run_checks(
        paths, base=args.base, python=python, with_tests=args.with_tests, executor=executor
    )


if __name__ == "__main__":
    raise SystemExit(main())
