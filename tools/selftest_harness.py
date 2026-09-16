#!/usr/bin/env python3
"""Shared driver for the hand-run self-tests of the ``tools/`` lints.

Ten self-tests each re-implemented two things: an ``importlib`` loader, because
their subject's filename is hyphenated and cannot be imported by name, and a
case runner with a pass/fail protocol. The loader was copied verbatim; the
runners diverged into two shapes — a sweep over module-level ``test_*``
callables, and an accumulating ``_check`` writing into a ``FAILURES`` list.

Both runners are kept. Converting a self-test from one style to the other
changes that test, and this module exists to remove duplication, not to
re-litigate how ten suites spell an assertion.

**These files are not a pytest surface via a sweep.** ``pytest tools/``
collects none of ``tools/test-lint-*.py``: the default ``python_files`` glob is
``test_*.py`` and the hyphen fails it. Naming one explicitly does collect
whatever ``test_*`` functions it defines, so the two routes disagree and the
directory sweep is the one that silently reports nothing.

**Import contract.** Same as ``tools/lint_harness.py``: callers run as scripts,
``sys.path[0]`` is ``tools/``, and nothing here touches ``sys.path``.

Pure stdlib, as ``tools/AGENTS.md`` requires of additions to this directory.
"""

from __future__ import annotations

import importlib.util
import sys
from collections.abc import Callable, Iterable
from pathlib import Path
from types import ModuleType

__all__ = ["CaseFailures", "load", "run_cases"]

_HERE = Path(__file__).resolve().parent


def load(script_filename: str, *, module_name: str | None = None) -> ModuleType:
    """Import a sibling ``tools/`` script whose filename is not a module name.

    ``lint-pack-descriptions.py`` cannot be imported by name because of the
    hyphen, so every self-test built the same ``spec_from_file_location``
    dance. The module is executed, so anything it does at import time still
    happens — that is the point, since the subject's import is part of what is
    under test.
    """
    path = _HERE / script_filename
    name = module_name or path.stem.replace("-", "_")
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:  # pragma: no cover - defensive
        raise ImportError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class CaseFailures:
    """Accumulating checker for the self-tests built around a failure list.

    Replaces the per-file ``FAILURES`` list and ``_check`` helper. Collecting
    rather than raising is deliberate in those suites: one run lists every
    broken case instead of stopping at the first.
    """

    def __init__(self, label: str) -> None:
        self.label = label
        self.failures: list[str] = []

    def check(self, description: str, condition: bool, detail: str = "") -> None:
        """Record *description* as failed unless *condition* holds."""
        if not condition:
            self.failures.append(f"{description}{f': {detail}' if detail else ''}")

    def report(self) -> int:
        """Print this run's verdict and return its exit status."""
        if self.failures:
            print(f"{self.label}: FAIL ({len(self.failures)})", file=sys.stderr)
            for failure in self.failures:
                print(f"  - {failure}", file=sys.stderr)
            return 1
        print(f"{self.label}: ok")
        return 0


def case_names(namespace: dict[str, object]) -> list[str]:
    """Return the ``test_*`` case names in *namespace*, in definition order.

    Sorted by the source line they were defined on rather than alphabetically,
    so a run reports cases in the order a reader meets them in the file.
    """
    cases = [
        (value.__code__.co_firstlineno, name)
        for name, value in namespace.items()
        if name.startswith("test_") and callable(value) and hasattr(value, "__code__")
    ]
    return [name for _line, name in sorted(cases)]


def run_cases(
    namespace: dict[str, object],
    label: str,
    *,
    only: Iterable[str] | None = None,
) -> int:
    """Run every ``test_*`` callable in *namespace* and return an exit status.

    Replaces the ``for name, fn in sorted(globals().items())`` sweep. Each case
    is reported by name on failure: the sweep it replaces raised on the first
    failure, which named the case only through a traceback.
    """
    wanted = set(only) if only is not None else None
    names = [n for n in case_names(namespace) if wanted is None or n in wanted]
    failures: list[str] = []
    for name in names:
        case = namespace[name]
        assert isinstance(case, Callable)  # noqa: S101 - narrowing for type checkers
        try:
            case()
        except AssertionError as exc:
            failures.append(f"{name}: {exc}")
        except Exception as exc:  # noqa: BLE001 - a raising case is a failing case
            failures.append(f"{name}: {type(exc).__name__}: {exc}")

    if failures:
        print(f"{label}: FAIL ({len(failures)} of {len(names)})", file=sys.stderr)
        for failure in failures:
            print(f"  - {failure}", file=sys.stderr)
        return 1
    print(f"{label}: all {len(names)} cases passed.")
    return 0
