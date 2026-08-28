#!/usr/bin/env python3
"""Shared self-test driver for the workflow posture harnesses.

Four posture tests — ci-security, pack-evals, build-check-windows and CodeQL —
carried a byte-identical copy of this driver. The duplication was created by the
change that gave them mutation matrices in the first place, so it is that
change's debt to pay rather than a pre-existing condition to register and leave.

**Scope, deliberately narrow.** Only the driver moves: the baseline-clean
precondition, the no-op rejection, the expected-label check, family accounting,
the failure and success reports. Every `audit`, `_MUTATIONS` and per-file
predicate stays in its own module, because those are what each harness is *for*
and sharing them would couple four unrelated workflow contracts.

**Not converged here, and not this change's debt:** `tools/test-pages-workflow.py`
and `tools/test-build-check-workflow.py` predate that change and carry different
shapes — build-check has a bash differential and a shape-stable fixture, pages
has crafted-input predicates — and `tools/test-pages-concurrency.py` uses a
four-element mutation tuple with no family rule at all. Converging those means
changing three already-working harnesses and is registered separately.

**Import contract.** The callers run as scripts (`python tools/test-x.py`,
including from `tools/repo/build_gate_chain.py`), so `sys.path[0]` is `tools/`
and a plain `import posture_harness` resolves. It deliberately does not insert
anything on `sys.path`: `tools/test_import_time_path_leaks.py` exists because an
import-time insert here once made a suite's result depend on file order. If the
import ever fails, the caller fails loudly rather than skipping its self-test.

Pure stdlib, as required for new ``tools/`` additions.
"""

from __future__ import annotations

import re
import sys
from collections.abc import Callable, Sequence
from pathlib import Path

# (mutation id, expected violation label, text transform)
Mutation = tuple[str, str, Callable[[str], str]]


def family(label: str) -> str:
    """Collapse repeated indexed assertions into one mutation family."""
    return re.sub(r"\[.*\]$", "[*]", label)


def replace_once(text: str, old: str, new: str, workflow: str) -> str:
    """Substitute exactly one occurrence, or raise.

    Driver-shaped, not a per-file predicate: it enforces the same
    mutate-or-prove-nothing contract as the no-op rule below. A compound
    transform whose other half still fires is not a no-op, so without this a
    drifted literal reports "caught" while proving nothing.
    """
    if text.count(old) != 1:
        raise AssertionError(
            f"mutation literal is not present exactly once ({text.count(old)}x): "
            f"{old!r} — re-pin it against {workflow}"
        )
    return text.replace(old, new, 1)


def run(
    *,
    workflow: Path,
    baseline: Callable[[], str],
    audit: Callable[..., list[str]],
    mutations: Sequence[Mutation],
    extra_failures: Callable[[], list[str]] | None = None,
    extra_summary: Callable[[], str] | None = None,
) -> int:
    """Prove the real baseline and every assertion family it evaluates.

    Returns 0 when the baseline is clean, every mutation is caught for the
    reason it names, and every family the baseline evaluated carries at least
    one mutation.

    ``extra_failures`` lets a caller append checks the driver knows nothing
    about — build-check-windows uses it for a differential against bash — and
    ``extra_summary`` lets that caller say so on the success line, so a check
    that did not run cannot read as one that passed.
    """
    failures: list[str] = []
    good = baseline()
    evaluated: list[str] = []

    baseline_violations = audit(good, evaluated)
    if baseline_violations:
        # Return before the matrix. Every transform is pinned to the real
        # workflow's text, so a dirty or missing baseline turns each one into a
        # no-op — or, where a transform asserts its literal, into an exception —
        # burying the one true cause under a wall of derived noise that names
        # neither the cause nor the file to edit.
        print(
            f"✖ self-test: {workflow} is not clean; "
            f"{len(baseline_violations)} posture violation(s) before any mutation:",
            file=sys.stderr,
        )
        for violation in baseline_violations:
            print(f"  - {violation}", file=sys.stderr)
        return 1

    for mutation_id, expected, transform in mutations:
        try:
            mutated = transform(good)
        except AssertionError as exc:
            # A pinned literal drifted. Report it in this harness's own verdict
            # format rather than letting the exception escape as a traceback,
            # and keep going so every drifted literal is listed at once.
            failures.append(f"{mutation_id}: {exc}")
            continue
        if mutated == good:
            failures.append(
                f"{mutation_id}: transform was a no-op against {workflow.name} — "
                "proves nothing; re-pin its literal against that file"
            )
            continue
        got = audit(mutated)
        if expected not in got:
            failures.append(f"{mutation_id}: expected {expected!r}, got {got}")

    covered = {family(expected) for _, expected, _ in mutations}
    uncovered = sorted({family(label) for label in evaluated} - covered)
    if uncovered:
        failures.append(f"assertion families evaluated but unmutated: {uncovered}")

    if extra_failures is not None:
        failures.extend(extra_failures())

    if failures:
        print(f"✖ self-test: {len(failures)} problem(s):", file=sys.stderr)
        for failure in failures:
            print(f"  - {failure}", file=sys.stderr)
        return 1

    summary = (
        f"✓ self-test: baseline clean; {len(mutations)} mutations each caught; "
        f"every one of {len(covered)} assertion families has ≥1 mutation"
    )
    if extra_summary is not None:
        summary += f"; {extra_summary()}"
    print(summary)
    return 0
