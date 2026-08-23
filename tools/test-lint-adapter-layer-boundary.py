#!/usr/bin/env python3
"""Self-test the adapter/projection dependency-boundary lint."""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="strict")
sys.stderr.reconfigure(encoding="utf-8", errors="backslashreplace")

LINT = Path(__file__).with_name("lint-adapter-layer-boundary.py")


def write(root: Path, relative: str, source: str) -> None:
    """Create one fixture file, including its parent directories."""
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(source, encoding="utf-8")


# The lint reads target-runtime roots from the adapter contract rather than a
# fixed list, so a fixture needs one. Two adapters and a merged config file keep
# the shape honest: `.claude/` is reached through the parent of a config *file*,
# and `.agents/skills/` through a directory target.
FIXTURE_CONTRACT = """\
[adapter."claude-code"]

[[adapter."claude-code".projection]]
primitive = "skill"
mode = "direct-directory"
target-path = ".claude/skills/"

[[adapter."claude-code".projection]]
primitive = "hook-wiring"
mode = "merge-json"
target-path = ".claude/settings.local.json"

[adapter.codex]

[[adapter.codex.projection]]
primitive = "skill"
mode = "direct-directory"
target-path = ".agents/skills/"
"""


def baseline(root: Path) -> None:
    """Add the smallest non-vacuous adapter and projection package pair."""
    write(root, "packages/agentbundle/agentbundle/build/adapters/__init__.py", "")
    write(root, "packages/agentbundle/agentbundle/build/projections/__init__.py", "")
    write(root, "contracts/adapter.toml", FIXTURE_CONTRACT)


def run_case(name: str, build: callable, expected_code: int,
             expected: str, stdout_expected: str = "") -> None:
    """Run one isolated fixture; failures name the case and captured output."""
    with tempfile.TemporaryDirectory() as directory:
        fixture = Path(directory)
        build(fixture)
        env = os.environ.copy()
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        proc = subprocess.run(
            [sys.executable, "-B", "-I", str(LINT), "--root", str(fixture)],
            capture_output=True,
            text=True,
            env=env,
            check=False,
        )
    output = proc.stdout + proc.stderr
    if proc.returncode != expected_code or expected not in output or (
            stdout_expected and stdout_expected not in proc.stdout):
        raise AssertionError(
            f"{name}: exit={proc.returncode}, expected={expected_code}; "
            f"output={output!r}"
        )


def clean(root: Path) -> None:
    baseline(root)
    write(root, "packages/agentbundle/agentbundle/build/projections/output.py", "x = 1\n")
    write(root, "packages/agentbundle/agentbundle/build/adapters/use_output.py",
          "from agentbundle.build.projections.output import x\n")


def absolute_r1(root: Path) -> None:
    baseline(root)
    write(root, "packages/agentbundle/agentbundle/build/projections/bad.py",
          "from agentbundle.build.adapters.codex import x\n")


def relative_r1(root: Path) -> None:
    baseline(root)
    write(root, "packages/agentbundle/agentbundle/build/projections/bad.py",
          "from ..adapters.codex import x\n")


def pack_r2(root: Path) -> None:
    baseline(root)
    write(root, "packs/demo/.apm/skills/s/scripts/x.py",
          "import agentbundle.build.adapters.codex\n")


def excluded_pack_test(root: Path) -> None:
    baseline(root)
    write(root, "packs/demo/tests/test_x.py",
          "import agentbundle.build.adapters.codex\n")


def runtime_r3(root: Path) -> None:
    baseline(root)
    write(root, ".claude/skills/s/scripts/x.py",
          "import agentbundle.build.projections.direct_directory\n")


def prose(root: Path) -> None:
    baseline(root)
    write(root, "notes.md", "packages/agentbundle/agentbundle/build/adapters/codex.py\n")
    write(root, "example.toml", "# agentbundle.build.adapters.codex\n")


def parse_error(root: Path) -> None:
    baseline(root)
    write(root, "packages/agentbundle/agentbundle/build/projections/bad.py", "def nope(:\n")


def empty(root: Path) -> None:
    del root


def missing_contract(root: Path) -> None:
    """The adapter contract is absent, so no runtime root can be resolved.

    This must fail rather than fall back to a fixed list: a silent fallback
    would shrink the scanned set back to whatever was hard-coded, which is the
    hole reading the contract exists to close.
    """
    write(root, "packages/agentbundle/agentbundle/build/adapters/__init__.py", "")
    write(root, "packages/agentbundle/agentbundle/build/projections/__init__.py", "")
    write(root, "packages/agentbundle/agentbundle/build/projections/output.py", "x = 1\n")


def contract_only_runtime_root(root: Path) -> None:
    """An R3 violation under a root only the contract names.

    `.cursor/` is not one of the directories a fixed list would have carried, so
    this case fails if the runtime roots stop being read from the contract.
    """
    baseline(root)
    write(
        root,
        "contracts/adapter.toml",
        FIXTURE_CONTRACT
        + '\n[adapter.cursor]\n\n[[adapter.cursor.projection]]\n'
        'primitive = "skill"\nmode = "direct-directory"\n'
        'target-path = ".cursor/skills/"\n',
    )
    write(root, ".cursor/skills/s/scripts/x.py",
          "from agentbundle.build.projections.output import x\n")


def symlinked_pack_directory(root: Path) -> None:
    """A violating file reachable only through a symlinked directory.

    `Path.rglob` and `os.walk(followlinks=False)` both decline to descend a
    directory symlink, so the import below is invisible to the scan. The lint
    must refuse the link rather than scan around it, otherwise parking content
    outside the scanned set and linking to it is a silent bypass.
    """
    baseline(root)
    write(root, "packages/agentbundle/agentbundle/build/projections/output.py", "x = 1\n")
    write(root, "outside/evil.py",
          "from agentbundle.build.adapters.codex import x\n")
    (root / "packs" / "demo").mkdir(parents=True, exist_ok=True)
    (root / "packs" / "demo" / "linked").symlink_to(root / "outside")


def empty_contract_roots(root: Path) -> None:
    """A contract that parses but declares no target-path at all.

    R3 would then scan nothing and a target-runtime import would pass, so an
    empty resolution must fail rather than read as an empty rule.
    """
    write(root, "packages/agentbundle/agentbundle/build/adapters/__init__.py", "")
    write(root, "packages/agentbundle/agentbundle/build/projections/__init__.py", "")
    write(root, "packages/agentbundle/agentbundle/build/projections/output.py", "x = 1\n")
    write(root, "contracts/adapter.toml", '[adapter."claude-code"]\n')


def main() -> int:
    cases = [
        ("clean tree", clean, 0, "passed", "passed"),
        ("absolute projection adapter import", absolute_r1, 1, "R1", ""),
        ("relative projection adapter import", relative_r1, 1, "R1", ""),
        ("pack source adapter import", pack_r2, 1, "R2", ""),
        ("excluded pack test", excluded_pack_test, 0, "passed", "passed"),
        ("target runtime projection import", runtime_r3, 1, "R3", ""),
        ("prose is ignored", prose, 0, "passed", "passed"),
        ("parse failure", parse_error, 1, "bad.py", ""),
        ("empty inventory", empty, 1, "vacuously", ""),
        ("missing adapter contract", missing_contract, 1,
         "cannot resolve runtime roots", ""),
        ("runtime root named only by the contract",
         contract_only_runtime_root, 1, "R3", ""),
        ("symlinked directory in a scanned tree", symlinked_pack_directory, 1,
         "refusing to scan around it", ""),
        ("contract declares no target-path", empty_contract_roots, 1,
         "must not pass vacuously", ""),
    ]
    try:
        for case in cases:
            run_case(*case)
    except AssertionError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    print(f"ok — {len(cases)} cases passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
