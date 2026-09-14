"""Select test shards from the Makefile-owned roster.

The Makefile remains the single test roster.  This module only expands that
roster, selects one disjoint slice, and executes its commands unchanged.
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
import tempfile
import time
from collections.abc import Sequence
from pathlib import Path
from typing import Protocol

REPO_ROOT = Path(__file__).resolve().parent.parent
MAKEFILE = REPO_ROOT / "Makefile"


class RosterError(RuntimeError):
    """Report a roster or selector shape that cannot be executed safely."""


PRECONDITION_MARKERS = (
    # The editable-install guard runs in every shard so none resolves stale code.
    "tools/repo/editable_install_guard.py",
    # The npm runtime probe runs in every shard so each can fail before plugin work.
    "command -v npm ",
    # The node_modules probe runs in every shard so missing deps always fail early.
    "test -d docs-site/node_modules ",
    # The httpx import probe runs in every shard before any HTTP-backed suite.
    '-c "import httpx"',
)

# Measured invocation durations from workflow run 34779996081.
WEIGHTS: dict[str, float] = {
    "tools/test_check_artifact_contents.py": 174.7,
    "packs/core/tests/skills/work-loop/": 147.2,
    "tests/": 91.0,
    "tools/test_build_gate_chain.py": 54.2,
    "tools/test_workspace_status.py": 31.4,
    "tools/test_lint_agents_md_diataxis_block.py": 27.1,
}

# 843s total make test less 525.6s measured, spread over 52 unmeasured work units.
DEFAULT_WEIGHT = 6.1


# Set in every child environment so a nested selector fails loudly instead of
# recursing. Nothing legitimately runs a shard inside a shard.
REENTRY_MARKER = "SHARD_TEST_ROSTER_ACTIVE"

# Stable, greppable prefix for the per-unit durations that refresh WEIGHTS.
TIMING_PREFIX = "shard-timing"


def child_environment() -> dict[str, str]:
    """Return an environment that cannot re-select a shard.

    Make exports command-line variables to sub-makes through ``MAKEFLAGS``, so a
    roster command that itself runs ``make test`` -- the Makefile harnesses in
    tools/test_local_ci_shared_test_deduplication.py do exactly that -- would
    inherit ``SHARD``/``SHARDS``, take the sharded branch, and run this selector
    again. Run 34789473362 shard 4 recursed that way until the job was killed at
    its timeout, having produced no output at all.

    Stripping the pair from both the environment and ``MAKEFLAGS`` makes a
    nested ``make test`` resolve to the ordinary serial branch, which is what
    those harnesses expect.

    The residual is named rather than guarded: a nested ``make test`` now
    resolves to the FULL serial roster. Every such caller in the roster today is
    a harness that stubs ``test-unleased`` to an echo, so nothing real runs. A
    future roster command that invoked an unstubbed ``make test`` would run the
    whole corpus inside one shard -- slow, but not wrong, and it cannot drop or
    duplicate a suite. Refusing a nested ``make test`` outright is NOT the
    answer: it would break the harnesses that legitimately drive it.
    """
    env = dict(os.environ)
    env.pop("SHARD", None)
    env.pop("SHARDS", None)
    makeflags = env.get("MAKEFLAGS")
    if makeflags is not None:
        kept = [
            token
            for token in makeflags.split()
            if not token.startswith(("SHARD=", "SHARDS="))
        ]
        env["MAKEFLAGS"] = " ".join(kept)
    env[REENTRY_MARKER] = "1"
    return env


class Executor(Protocol):
    """Run one unchanged roster command as its own process."""

    def __call__(
        self,
        command: str,
        *,
        shell: bool,
        cwd: Path,
        check: bool,
    ) -> subprocess.CompletedProcess[bytes]:
        """Execute ``command`` and return its process result."""


def unit_key(line: str) -> str:
    """Return the first non-flag path argument, or the normalized command."""
    tokens = line.split()
    for index, token in enumerate(tokens):
        if index == 0 and re.fullmatch(
            r"python(?:\d+(?:\.\d+)*)?", Path(token).name
        ):
            continue
        if "/" in token and not token.startswith("-"):
            return token
    return " ".join(tokens)


def classify(line: str) -> str:
    """Classify one expanded roster line, refusing unknown command shapes."""
    stripped = line.strip()
    if not stripped or stripped.startswith("#"):
        return "ignore"
    # Make's own recursion diagnostics, never roster content. `--no-print-
    # directory` above suppresses the common one; this stays as the second
    # layer, matched narrowly on the `make[N]:` prefix so a real roster line
    # can never be swallowed by it.
    if re.match(r"^make\[\d+\]: ", stripped):
        return "ignore"
    # Unambiguous runner shapes are decided FIRST. A precondition marker is a
    # substring test, so a future suite whose path merely CONTAINS a marker --
    # `-m pytest tools/repo/editable_install_guard.py`, say -- would otherwise
    # be classified as a precondition: dropped from the union's work multiset
    # and silently run in every shard instead of exactly one.
    if "-m pytest " in stripped or stripped.startswith("npm run "):
        return "work"
    if any(marker in stripped for marker in PRECONDITION_MARKERS):
        return "precondition"

    tokens = stripped.split()
    if (
        len(tokens) >= 2
        and re.fullmatch(r"python(?:\d+(?:\.\d+)*)?", Path(tokens[0]).name)
        and tokens[1].endswith(".py")
    ):
        return "work"
    raise RosterError(f"unclassified roster line: {line}")


def _extract_define_body(makefile_text: str) -> list[str]:
    """Extract the ``run-test-suite`` define body from Makefile text."""
    lines = makefile_text.splitlines()
    start = next(
        (
            index + 1
            for index, line in enumerate(lines)
            if re.fullmatch(r"(?:override\s+)?define\s+run-test-suite\s*", line)
        ),
        None,
    )
    if start is None:
        raise RosterError("Makefile has no run-test-suite define body")
    for end in range(start, len(lines)):
        if lines[end].strip() == "endef":
            return lines[start:end]
    raise RosterError("Makefile run-test-suite define body has no endef")


def _extract_target_recipe(makefile_text: str) -> list[str]:
    """Extract recipe lines belonging to the ``test-unleased`` target."""
    lines = makefile_text.splitlines()
    start = next(
        (
            index + 1
            for index, line in enumerate(lines)
            if re.match(r"^test-unleased\s*:", line)
        ),
        None,
    )
    if start is None:
        raise RosterError("Makefile has no test-unleased target")

    recipe: list[str] = []
    for line in lines[start:]:
        if line.startswith("\t"):
            recipe.append(line[1:])
            continue
        if not line.strip() and not recipe:
            continue
        break
    if not recipe:
        raise RosterError("Makefile test-unleased target has no recipe")
    return recipe


def _refuse_recursive_make(lines: Sequence[str]) -> None:
    """Refuse roster lines GNU Make would execute despite ``-n``."""
    for line in lines:
        # GNU Make recipe-control prefixes are `@`, `-` and `+`, in any order
        # and repetition, so `@+cmd` and `-+cmd` force execution just as `+cmd`
        # does. Strip the whole prefix run and look for `+` anywhere in it.
        prefix = line[: len(line) - len(line.lstrip("@-+\t "))]
        if "$(MAKE)" in line or "${MAKE}" in line or "+" in prefix:
            raise RosterError(f"unsafe dry-run roster line: {line}")


def _expand_roster(makefile_path: Path) -> list[str]:
    """Expand ``test-unleased`` from one already-inspected Makefile."""
    try:
        result = subprocess.run(
            [
                "make",
                # This runs from inside a make recipe, so MAKELEVEL is already
                # non-zero and GNU Make announces "Entering directory ..." on
                # STDOUT -- interleaved with the roster it is meant to emit.
                # macOS make stayed quiet and CI did not; the classifier refused
                # the line rather than dropping a suite, which is the designed
                # behaviour, but the roster must not carry it in the first place.
                "--no-print-directory",
                "-f",
                str(makefile_path),
                "-n",
                "test-unleased",
                f"PYTHON={sys.executable}",
            ],
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
            check=False,
            env=child_environment(),
        )
    except OSError as error:
        raise RosterError(f"cannot expand test roster: {error}") from error
    if result.returncode != 0:
        raise RosterError(
            f"make -n test-unleased failed with status {result.returncode}"
        )
    return result.stdout.splitlines()


def roster_lines(makefile_text: str | None = None) -> list[str]:
    """Return the expanded roster after checking dry-run recipe hazards."""
    if makefile_text is None:
        try:
            text = MAKEFILE.read_text(encoding="utf-8")
        except OSError as error:
            raise RosterError(f"cannot read {MAKEFILE}: {error}") from error
    else:
        text = makefile_text

    define_body = _extract_define_body(text)
    target_recipe = _extract_target_recipe(text)
    _refuse_recursive_make((*define_body, *target_recipe))

    if makefile_text is None:
        return _expand_roster(MAKEFILE)
    with tempfile.TemporaryDirectory(prefix="shard-test-roster-") as directory:
        makefile_path = Path(directory) / "Makefile"
        makefile_path.write_text(text, encoding="utf-8")
        return _expand_roster(makefile_path)


def _unit_weight(line: str) -> float:
    """Return the measured weight for a unit, or the derived default."""
    return WEIGHTS.get(unit_key(line), DEFAULT_WEIGHT)


def partition(units: list[str], shards: int) -> list[list[str]]:
    """Partition units with deterministic longest-processing-time-first."""
    if shards <= 0:
        raise RosterError("shards must be a positive integer")

    assignments: list[list[tuple[int, str]]] = [[] for _ in range(shards)]
    loads = [0.0] * shards
    ordered = sorted(
        enumerate(units),
        key=lambda item: (-_unit_weight(item[1]), item[0]),
    )
    for roster_index, unit in ordered:
        shard_index = min(range(shards), key=lambda index: (loads[index], index))
        assignments[shard_index].append((roster_index, unit))
        loads[shard_index] += _unit_weight(unit)

    return [
        [unit for _, unit in sorted(assignment)] for assignment in assignments
    ]


def _selector(argv: Sequence[str]) -> tuple[int, int]:
    """Parse and validate the one-based ``--shard N --shards M`` selector.

    Parsed by hand rather than through ``argparse`` because Make cannot
    distinguish an unset variable from an empty one: ``make test SHARD=1``
    reaches here as ``--shard 1 --shards ''``.  That one-sided form must be
    refused, and ``argparse`` would accept the empty string as a present value.
    """
    values: dict[str, str] = {}
    remaining = list(argv)
    while remaining:
        flag = remaining.pop(0)
        if flag not in ("--shard", "--shards") or not remaining:
            raise RosterError(f"unexpected selector argument: {flag}")
        if flag in values:
            raise RosterError(f"{flag} given more than once")
        values[flag] = remaining.pop(0)

    if set(values) != {"--shard", "--shards"}:
        raise RosterError("both --shard and --shards are required")
    if not values["--shard"].strip() or not values["--shards"].strip():
        raise RosterError("--shard and --shards must both be non-empty")
    try:
        shard = int(values["--shard"])
        shards = int(values["--shards"])
    except ValueError as error:
        raise RosterError("shard and shards must be integers") from error
    if shard <= 0 or shards <= 0:
        raise RosterError("shard and shards must be positive integers")
    if shard > shards:
        raise RosterError("shard cannot exceed shards")
    return shard, shards


def _default_executor(
    command: str,
    *,
    shell: bool,
    cwd: Path,
    check: bool,
) -> subprocess.CompletedProcess[bytes]:
    """Execute one roster command without combining it with another."""
    return subprocess.run(
        command, shell=shell, cwd=cwd, check=check, env=child_environment()
    )


def main(argv: Sequence[str], executor: Executor = _default_executor) -> int:
    """Execute one validated shard, with every precondition first."""
    try:
        if os.environ.get(REENTRY_MARKER):
            raise RosterError(
                "refusing to run a shard inside a shard — a nested selector "
                "recurses until the job is killed; see child_environment()"
            )
        shard, shards = _selector(argv)
        preconditions: list[str] = []
        work_units: list[str] = []
        for line in roster_lines():
            kind = classify(line)
            if kind == "precondition":
                preconditions.append(line)
            elif kind == "work":
                work_units.append(line)
        if shards > len(work_units):
            raise RosterError(
                f"shards ({shards}) exceeds work-unit count ({len(work_units)})"
            )
        selected = partition(work_units, shards)[shard - 1]
    except RosterError as error:
        print(f"shard test roster: {error}", file=sys.stderr)
        return 2

    for command in (*preconditions, *selected):
        started = time.monotonic()
        result = executor(command, shell=True, cwd=REPO_ROOT, check=False)
        elapsed = time.monotonic() - started
        # One line per unit, on stderr so it never mixes into the roster any
        # other tool reads. This is how WEIGHTS above is refreshed: the table is
        # a snapshot, and without a way to re-measure it silently rots into the
        # round-robin it exists to avoid. Harvest with:
        #   gh run view <id> --job <id> --log | grep shard-timing
        print(
            f"{TIMING_PREFIX} {elapsed:8.2f}s {unit_key(command)}",
            file=sys.stderr,
            flush=True,
        )
        if result.returncode != 0:
            return result.returncode
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
