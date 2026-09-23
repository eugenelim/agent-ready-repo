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
    # The node_modules probes run in every shard so missing deps always fail early.
    "test -d docs-site/node_modules ",
    "test -d web/node_modules ",
    # The httpx import probe runs in every shard before any HTTP-backed suite.
    '-c "import httpx"',
)

# Per-invocation durations in seconds, MEASURED on ubuntu-latest by workflow run
# 34793156321 and harvested from its `shard-timing` lines. Only invocations at or
# above 5s are listed; everything below shares DEFAULT_WEIGHT, and lumping them
# costs nothing because all 42 of them together total 37.8s -- less than a
# quarter of the single heaviest entry.
#
# These are a snapshot and they WILL drift. Refresh them rather than guessing:
#   gh workflow run test-corpus.yml --ref <branch>
#   gh run view <id> --job <job-id> --log | grep shard-timing
#
# The first entry is the floor: no shard count makes the slowest shard faster
# than the longest single invocation, because an invocation is never split.
WEIGHTS: dict[str, float] = {
    "packages/agentbundle/tests/": 174.7,
    "packs/core/tests/skills/work-loop/": 150.6,
    "tools/test_check_artifact_contents.py": 132.3,
    "tests/": 90.5,
    "tools/test_build_gate_chain.py": 59.7,
    "tools/test_workspace_status.py": 33.0,
    "packages/credbroker/": 29.6,
    "tools/test_lint_agents_md_diataxis_block.py": 27.1,
    "packs/core/tests/skills/project-knowledge/": 21.9,
    "packs/core/tests/skills/workspace-status/": 11.3,
    "tools/test_with_lease_cli.py": 9.4,
    "tools/test_import_time_path_leaks.py": 9.3,
    "packs/core/tests/skills/close-work/": 6.1,
    "packs/core/tests/skills/new-spec/": 6.1,
    "packs/core/tests/pack/": 6.0,
    "packs/catalogue-curation/tests/skills/compile-okf/": 5.9,
}

# Mean of the 42 measured invocations below 5s (37.8s over 42), from the same
# run. Derived from measurement, not chosen: an earlier value of 6.1s was a
# back-of-envelope figure that put `packages/agentbundle/tests/` -- 174.7s of
# real work -- in the same weight class as a 0.5s linter, and shard 3 of run
# 34791356312 duly came in at 6.37 minutes against a 3.55-minute prediction.
DEFAULT_WEIGHT = 0.9


# Set in every child environment so a nested selector fails loudly instead of
# recursing. Nothing legitimately runs a shard inside a shard.
REENTRY_MARKER = "SHARD_TEST_ROSTER_ACTIVE"

# Stable, greppable prefix for the per-unit durations that refresh WEIGHTS.
TIMING_PREFIX = "shard-timing"

# One definition, because `classify` and `unit_key` must agree on it. The first
# decides that a line is work; the second derives the WEIGHTS key for that same
# line. Two copies of this pattern that drifted apart would classify a unit as
# work and then key it under a name no WEIGHTS entry carries -- a silent
# fall-through to DEFAULT_WEIGHT that degrades balance without failing anything.
INTERPRETER = re.compile(r"python(?:\d+(?:\.\d+)*)?")


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
        cwd: Path,
        check: bool,
    ) -> subprocess.CompletedProcess[bytes]:
        """Execute ``command`` and return its process result."""


def unit_key(line: str) -> str:
    """Return the first non-flag path argument, or the normalized command.

    The interpreter token is normalized out of the fallback form. ``$(PYTHON)``
    expands to an absolute path that differs per environment
    (``/opt/hostedtoolcache/...`` on a runner, a pyenv shim locally), so a key
    built from the whole command would not match the same invocation across
    machines -- a silent WEIGHTS miss that degrades balance and reads as a
    different unit when comparing a local roster against a harvested one.
    """
    tokens = line.split()
    for index, token in enumerate(tokens):
        if index == 0 and INTERPRETER.fullmatch(Path(token).name):
            continue
        if "/" in token and not token.startswith("-"):
            return token
    if tokens and INTERPRETER.fullmatch(Path(tokens[0]).name):
        return " ".join(["python", *tokens[1:]])
    return " ".join(tokens)


def classify(line: str) -> str:
    """Classify one expanded roster line, refusing unknown command shapes."""
    stripped = line.strip()
    if not stripped or stripped.startswith("#"):
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
        and INTERPRETER.fullmatch(Path(tokens[0]).name)
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


# Stands in for a masked `define` body line during the rule scan. It is
# non-empty and untabbed, so it matches no rule and terminates a recipe, which
# is what keeps a macro's tab-indented continuation lines from being read as
# the recipe of whichever rule happens to precede the macro.
MASKED_LINE = "\x00"


def _logical_lines(makefile_text: str) -> list[str]:
    """Join backslash-newline continuations the way Make reads them.

    A continued rule line carries its later prerequisites on physical lines of
    their own, and those are conventionally tab-indented -- which a
    physical-line scan reads as the rule's recipe, so the targets named there
    never enter the closure at all. Make joins first and splits prerequisites
    afterwards, so this walk has to do the same.

    Outside a recipe Make replaces the backslash-newline and the next line's
    leading whitespace with a single space, which is what this reproduces. A
    joined recipe line is not what Make hands the shell -- it keeps the
    continuation -- but the hazard check only searches the line for ``$(MAKE)``
    and reads the prefix run at its start, and joining changes neither.
    """
    logical: list[str] = []
    pending: str | None = None
    for line in makefile_text.splitlines():
        if pending is not None:
            line = f"{pending} {line.lstrip()}"
            pending = None
        if line.endswith("\\"):
            pending = line[:-1].rstrip()
            continue
        logical.append(line)
    if pending is not None:
        logical.append(pending)
    return logical


def _masked_lines(makefile_text: str) -> list[str]:
    """Return logical Makefile lines with ``define`` bodies masked out.

    One level deep: the flag clears at the first ``endef``, so a nested
    ``define`` leaves the rest of its outer body exposed.
    ``_extract_closure_recipes`` records that bound and its consequence.
    """
    masked: list[str] = []
    inside = False
    for line in _logical_lines(makefile_text):
        if inside:
            masked.append(MASKED_LINE)
            inside = line.strip() != "endef"
            continue
        if re.match(r"^(?:override\s+)?define\s+\S+", line):
            masked.append(MASKED_LINE)
            inside = True
            continue
        masked.append(line)
    return masked


def _parse_rule_tail(tail: str) -> tuple[list[str], list[str]]:
    """Split a rule tail into prerequisite names and an inline recipe.

    One left-to-right scan, because separate ad-hoc checks for comments,
    semicolons and whitespace each re-derive the same escaping rules and two of
    them got it wrong: a backslash escapes the character after it, so whether a
    ``#`` opens a comment or a space separates two names depends on the PARITY
    of the backslash run before it. ``dep\\\\# note`` is the prerequisite
    ``dep\\\\`` followed by a comment; ``dep\\# note`` is the single
    prerequisite ``dep\\#`` and then ``note``.

    Whichever of ``#`` or ``;`` the scan reaches first decides the remainder. A
    ``#`` ends the line, so Make reads no further prerequisite and no recipe
    after it. A ``;`` starts an inline recipe, and everything after it is
    recipe text where ``#`` is NOT a comment -- Make hands the line to the
    shell, so ``guard: ; @echo "#"; $(MAKE) x`` really does run ``$(MAKE)``
    under ``-n``.

    Names keep their backslashes. The rule that defines a name spells it the
    same way the prerequisite referencing it does, and the lookup matches that
    text, so unescaping here would make the two stop matching.
    """
    names: list[str] = []
    current = ""
    index = 0
    while index < len(tail):
        char = tail[index]
        if char == "\\" and index + 1 < len(tail):
            current += tail[index : index + 2]
            index += 2
            continue
        if char == "#":
            break
        if char == ";":
            if current:
                names.append(current)
            return names, [tail[index + 1 :]]
        if char.isspace():
            if current:
                names.append(current)
                current = ""
            index += 1
            continue
        current += char
        index += 1
    if current:
        names.append(current)
    return names, []


def _target_rule(
    masked: Sequence[str], target: str
) -> tuple[list[str], list[str]] | None:
    """Return one target's prerequisites and recipe, or ``None`` if unruled.

    ``::?(?!=)`` accepts a single- or double-colon rule and rejects
    ``target:=``, a variable assignment that would otherwise read as a rule
    with no prerequisites. It does NOT reject ``target::=``: the pattern
    backtracks to one colon there and matches. That is deliberate rather than
    overlooked, because ``::=`` means different things to the two Makes this
    repository runs on -- simple assignment to GNU Make 4.x on the runners, a
    ``::`` rule to the GNU Make 3.81 macOS ships, which refuses the file
    outright with "target file has both : and :: entries". Reading it as a rule
    matches the older Make and keeps the refusal fail-closed, so no single
    anchoring would be correct on both.

    ``_parse_rule_tail`` owns the tail, including the inline ``target: ;
    recipe`` form -- Make executes an inline recipe exactly as it executes a
    tab-indented one, including under ``-n`` when forced.

    Leading spaces are allowed before the target name because Make accepts a
    space-indented rule; a leading TAB is not, because that is a recipe line,
    and admitting it would promote a ``guard:`` inside some other rule's recipe
    into a rule of its own.

    Collection skips blank and comment-only lines throughout rather than only
    before the first recipe line. Make ignores them and still associates the
    tab-indented lines that follow, so stopping at one drops the rest of a
    recipe -- measured: ``guard:`` then ``# note`` then a tab ``+echo x`` runs
    under ``-n``.

    Prerequisites and recipe lines accumulate across every rule line naming the
    target, because Make allows a target's prerequisites and its recipe to be
    stated apart.
    """
    pattern = re.compile(rf"^ *{re.escape(target)}\s*::?(?!=)\s*(.*)$")
    prerequisites: list[str] = []
    recipe: list[str] = []
    ruled = False
    for index, line in enumerate(masked):
        match = pattern.match(line)
        if match is None:
            continue
        ruled = True
        names, inline_recipe = _parse_rule_tail(match.group(1))
        prerequisites.extend(names)
        recipe.extend(inline_recipe)
        for candidate in masked[index + 1 :]:
            if candidate.startswith("\t"):
                recipe.append(candidate[1:])
                continue
            if not candidate.strip() or candidate.lstrip().startswith("#"):
                continue
            break
    return (prerequisites, recipe) if ruled else None


def _extract_closure_recipes(makefile_text: str) -> list[str]:
    """Extract recipes for ``test-unleased`` and every prerequisite it reaches.

    ``make -n test-unleased`` walks the whole prerequisite closure and expands
    each reached recipe, so a hazard the dry run would execute for real can sit
    in a prerequisite rather than in the root recipe. Inspecting only the root
    would leave that unrefused.

    This reads Makefile TEXT, so its reach is the subset of GNU Make's grammar
    modelled below and no wider. The bound is stated here, not implied, because
    a walk described as complete is how the gap this function closes was
    shipped in the first place.

    Modelled: single- and double-colon rules, optionally space-indented;
    backslash-newline continuations; single-level ``define``/``endef`` bodies,
    masked out; comments, by backslash parity; the inline ``target: ; recipe``
    form; escaped whitespace inside a prerequisite name; a target whose
    prerequisites and recipe are stated on separate rule lines; blank and
    comment-only lines inside a recipe; and the transitive closure, order-only
    ``|`` prerequisites included.

    That list is closed. Every other Make construct is unmodelled, and rather
    than enumerate a grammar, the bound is stated by consequence -- which is
    the part a future editor needs.

    **Refused, loudly.** A prerequisite carrying a variable or function
    reference (``test-unleased: $(DEPS)``, or a ``$``-bearing
    target-specific assignment value). The closure cannot be enumerated from
    the text, and inspecting part of it would be the same overclaim this bound
    exists to retire.

    **Read anyway, so at worst a false refusal.** Both branches of an
    ``ifeq``/``ifdef`` are read, because none is evaluated. A nested ``define``
    exposes its outer body past the inner ``endef``. ``target::=`` matches as a
    SINGLE-colon rule leaving ``:=`` as a prerequisite name -- the text cannot
    decide better, since GNU Make 4.x reads that form as a simple assignment
    and the GNU Make 3.81 macOS ships reads it as a ``::`` rule; see
    ``_target_rule``. A literal ``target: VAR = value`` tokenizes into ``VAR``,
    ``=`` and ``value``, each looked up as a prerequisite name and skipped
    unless one collides with a real target. A prerequisite spelled differently
    in its rule than in the reference does not match. All of these fail closed:
    the refusal is loud, and no shard silently loses a suite.

    **Not reached at all, so a hazard there goes UNREFUSED.** This is the only
    fail-open group, and the one to check before adding a prerequisite:

    - A prerequisite with no explicit rule in this text -- including one
      satisfied by a ``%`` pattern rule, a multi-target rule, or an
      ``include``d makefile, none of which this repository's Makefile uses.
      Ordinarily Make then runs nothing, and no built-in implicit rule carries
      ``$(MAKE)`` or a ``+``. But ``.DEFAULT`` breaks that: measured on GNU
      Make 3.81, a ``.DEFAULT`` recipe of ``+echo x`` ran for real under ``-n``
      for an unruled prerequisite.
    - A recipe indented with a ``.RECIPEPREFIX`` other than a tab. Collection
      keys on the tab, so such a recipe is invisible. GNU Make 3.82 added the
      variable, so the runners' Make honours it and the macOS 3.81 does not.
    - A recipe reached through ``$(call)`` of any macro other than
      ``run-test-suite``, whose body this module does not read.
    """
    masked = _masked_lines(makefile_text)
    root = _target_rule(masked, "test-unleased")
    if root is None:
        raise RosterError("Makefile has no test-unleased target")
    prerequisites, recipe = root
    if not recipe:
        raise RosterError("Makefile test-unleased target has no recipe")

    collected = list(recipe)
    seen = {"test-unleased"}
    pending = list(prerequisites)
    while pending:
        name = pending.pop(0)
        if "$" in name:
            # An unexpanded variable or function reference. The closure cannot
            # be enumerated from the text, so refuse rather than inspect a
            # subset of it and treat the subset as the whole walk.
            raise RosterError(f"unexpandable test-unleased prerequisite: {name}")
        if name in seen:
            continue
        seen.add(name)
        nested = _target_rule(masked, name)
        if nested is None:
            continue
        collected.extend(nested[1])
        pending.extend(nested[0])
    return collected


def _refuse_recursive_make(lines: Sequence[str]) -> None:
    """Refuse supplied lines GNU Make would execute despite ``-n``.

    Scope is whatever the caller collected, never "every such line in the
    Makefile". ``_extract_closure_recipes`` owns that set and states its
    bound.
    """
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
    closure_recipes = _extract_closure_recipes(text)
    _refuse_recursive_make((*define_body, *closure_recipes))

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
    cwd: Path,
    check: bool,
) -> subprocess.CompletedProcess[bytes]:
    """Execute one roster command through a shell, without combining any two.

    A roster line IS a Make recipe line, and Make runs each one through
    ``/bin/sh -c``. Naming that shell explicitly reproduces Make's execution
    model rather than delegating to ``shell=True``, which resolves to ``sh`` on
    POSIX but ``cmd.exe`` on Windows -- a different interpreter for lines
    written against ``sh``.

    Stated plainly, because the alternative would be a suppression pretending
    otherwise: this does NOT reduce an injection surface. The commands come from
    the repository's own Makefile, at the same trust level as ``make`` running
    them, and anyone able to edit that file can already run anything through
    ``make test``. The explicit form is chosen for fidelity to Make, not safety.
    """
    return subprocess.run(
        ["sh", "-c", command], cwd=cwd, check=check, env=child_environment()
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
        result = executor(command, cwd=REPO_ROOT, check=False)
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
