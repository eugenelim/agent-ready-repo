#!/usr/bin/env python3
"""Path-triggered precheck: run only the local checks the changed paths call for.

Changed paths are the union of ``git diff --name-only <base>...HEAD`` and the
working-tree changes. Each path is mapped to the checks that guard it; a check
whose tool is not installed in this interpreter prints ``skipped: <tool> not
installed`` and leaves the exit status alone. Pack pytest suites run only with
``--with-tests``; otherwise the command is printed.

Run: python3 tools/precheck.py [--base <ref>] [--with-tests]
Exit 0 = every run check passed, 1 = a check failed, 2 = base or git unusable.
"""

from __future__ import annotations

import argparse
import importlib.util
import re
import subprocess  # nosec B404  # list argv, no shell
import sys
from collections.abc import Callable
from pathlib import Path
from types import ModuleType

REPO_ROOT = Path(__file__).resolve().parent.parent
GATE_SCRIPT = REPO_ROOT / "tools" / "run-bandit-gate.py"
DEFAULT_BASE = "origin/main"

# (exit status, captured text). `capture` is "none", "stderr" or "stdout".
Executor = Callable[[list[str], str], tuple[int, str]]

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
        stdout=subprocess.PIPE if capture == "stdout" else None,
        stderr=subprocess.PIPE if capture == "stderr" else None,
        text=True,
        check=False,
    )
    return proc.returncode, (proc.stdout if capture == "stdout" else proc.stderr) or ""


def _installed(module: str) -> bool:
    """True when `module` is importable by this interpreter."""
    return importlib.util.find_spec(module) is not None


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
    _, diff = executor(["git", "diff", "--name-only", f"{base}...HEAD"], "stdout")
    paths.extend(line for line in diff.splitlines() if line)
    _, status = executor(["git", "status", "--porcelain", "-z", "--untracked-files=all"], "stdout")
    entries = iter(status.split("\0"))
    for entry in entries:
        if len(entry) < 4:
            continue
        paths.append(entry[3:])
        if entry[0] in "RC":  # a rename or copy lists its source as the next entry
            paths.append(next(entries, ""))
    return list(dict.fromkeys(p for p in paths if p))


def touched_packs(paths: list[str]) -> list[str]:
    """Pack names with at least one changed path, sorted."""
    return sorted({m.group(1) for p in paths if (m := _PACK_RE.match(p))})


def _skip(tool: str) -> None:
    print(f"skipped: {_DISPLAY[tool]} not installed")


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
            _skip(tool)
        return 0
    print(f"precheck: {label}: {' '.join(argv)}")
    status, _ = executor(argv, "none")
    return status


def _run_bandit(
    files: list[str], python: str, executor: Executor, is_installed: Callable[[str], bool]
) -> int:
    """Bandit at the gate's floor and config; any stderr is a failure."""
    if not is_installed("bandit"):
        _skip("bandit")
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
) -> int:
    """Run every check the changed `paths` trigger; return the worst exit status."""
    exists = file_exists or (lambda p: (REPO_ROOT / p).is_file())
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
        argv = [python, "tools/check-core-release.py", "--base", base]
        results.append(_run_check("core release", argv, (), executor, is_installed))

    roots = tuple(f"{r}/" for r in scan_roots())
    files = [p for p in paths if p.endswith(".py") and p.startswith(roots) and exists(p)]
    if files:
        ran = True
        results.append(_run_bandit(files, python, executor, is_installed))

    for pack in touched_packs(paths):
        suite = f"packs/{pack}/tests"
        if with_tests:
            ran = True
            argv = [python, "-m", "pytest", suite, "-q"]
            results.append(_run_check("pack tests", argv, (), executor, is_installed))
        else:
            ran = True
            print(f"precheck: not run (pass --with-tests): python -m pytest {suite} -q")

    if not ran:
        print("no trigger matched")
    return max(results, default=0)


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
    except OSError as exc:
        print(f"precheck: cannot run git: {exc}", file=sys.stderr)
        return 2
    return run_checks(
        paths, base=args.base, python=python, with_tests=args.with_tests, executor=executor
    )


if __name__ == "__main__":
    raise SystemExit(main())
