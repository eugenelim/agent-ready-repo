#!/usr/bin/env python3
"""Shared driver for the single-rule lints in ``tools/``.

Twelve lints each walked a file set, applied one rule, printed offenders and
chose an exit status. The walk, the report and the status were re-derived in
every one of them; the rule was the only part that differed. This module owns
the repeated half. Each lint keeps its own predicate, its own message text and
its own rationale, and hands them over as a :class:`Rule`.

Same split as ``tools/posture_harness.py``, for the same reason: what a check
is *for* stays in the check, so that sharing the plumbing does not couple
twelve unrelated contracts.

**Every observable difference between the lints is a field, not a default.**
That is deliberate and it is most of this module's design. Measured across the
twelve before any of them moved: seven exit 0 when the scan finds nothing and
five exit 2; eight distinguish a target directory that is *empty* from one that
is *absent*, three of them by exit status. A driver that answered either
question on its own behalf would silently change seven or eight lints. So
``empty_scan`` and ``absent_root`` are whole outcomes — stream, text and status
— supplied per rule, and ``files`` reports the two cases apart by returning
``None`` rather than an empty sequence.

**Import contract.** Callers run as scripts, so ``sys.path[0]`` is ``tools/``
and a plain ``import lint_harness`` resolves; the same holds under pytest,
which prepends the directory of a collected test because ``tools/`` is not a
package. This module inserts nothing on ``sys.path``:
``tools/test_import_time_path_leaks.py`` exists because an import-time insert
elsewhere once made a suite's result depend on file order.

Pure stdlib, as ``tools/AGENTS.md`` requires of additions to this directory.
"""

from __future__ import annotations

import sys
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

__all__ = ["Outcome", "Rule", "RuleAbort", "run"]


@dataclass(frozen=True)
class Outcome:
    """A terminal result: what to print, where, and what to exit with.

    Three fields rather than an exit code because the lints disagree on all
    three. ``lint-pack-descriptions`` answers an empty scan with a refusal on
    stderr and status 2; ``lint-journey-contract`` answers the same condition
    with a success line on stdout and status 0.
    """

    text: str
    exit: int
    stream: str = "stderr"


class RuleAbort(Exception):
    """Raised by a predicate to stop the walk and report its own outcome.

    ``lint-experience-agnostic`` returns 2 partway through its walk when a file
    will not decode. That is neither a violation nor an empty scan, and
    reporting it as a violation would both exit 1 and print the offenders
    gathered before it. The exception carries the whole outcome so the driver
    does not have to classify it.
    """

    def __init__(self, outcome: Outcome) -> None:
        super().__init__(outcome.text)
        self.outcome = outcome


@dataclass(frozen=True)
class Rule:
    """One lint, expressed as its inputs and its messages.

    ``files`` returns ``None`` when the rule's root is absent and a sequence —
    possibly empty — when it exists. The distinction is the return *type* and
    not emptiness, because ``if not targets`` is exactly the test that would
    merge the two cases that eight of the twelve lints answer differently.
    """

    parse: Callable[[list[str] | None], Any]
    files: Callable[[Any], Sequence[Path] | None]
    predicate: Callable[[Path], list[str]]
    pass_line: Callable[[Any, int], str | Outcome | None]
    empty_scan: Callable[[Any], Outcome]
    absent_root: Callable[[Any], Outcome]
    summary: Callable[[int], str] | None = None
    report: Callable[[Sequence[str]], None] | None = None


def _emit(outcome: Outcome) -> int:
    """Write one terminal outcome to its own stream and return its status."""
    if outcome.text:
        print(outcome.text, file=getattr(sys, outcome.stream))
    return outcome.exit


def run(rule: Rule, argv: list[str] | None = None) -> int:
    """Apply *rule* and return the process exit status.

    ``report``, when a rule supplies one, replaces the default emission rather
    than adding to it. ``lint-journey-contract`` prints a header *before* its
    findings and nothing after them, which the default order would reverse; a
    writer that could only append would not be able to express that.
    """
    try:
        root = rule.parse(argv)
        targets = rule.files(root)
    except RuleAbort as abort:
        return _emit(abort.outcome)

    if targets is None:
        return _emit(rule.absent_root(root))
    if not targets:
        return _emit(rule.empty_scan(root))

    violations: list[str] = []
    try:
        for target in targets:
            violations.extend(rule.predicate(target))
    except RuleAbort as abort:
        return _emit(abort.outcome)

    if violations:
        if rule.report is not None:
            rule.report(violations)
        else:
            for violation in violations:
                print(violation, file=sys.stderr)
            if rule.summary is not None:
                print(rule.summary(len(violations)), file=sys.stderr)
        return 1

    return _emit(_as_outcome(rule.pass_line(root, len(targets))))


def _as_outcome(result: str | Outcome | None) -> Outcome:
    """Normalise a rule's success result into an outcome.

    A plain string is the common case and lands on stdout. Two rules need the
    other two forms and neither is expressible as a string:
    ``lint_zone_violations`` prints *nothing* at all on a clean scan, and
    ``lint-sso-config`` writes its success line to stderr. Returning ``""``
    cannot mean silence — it still emits a newline — so ``None`` carries it.
    """
    if result is None:
        return Outcome("", 0, "stdout")
    if isinstance(result, Outcome):
        return result
    return Outcome(result, 0, "stdout")
