"""Opt-in pytest collection floor enforced by the real test execution.

Load this plugin explicitly with ``-p tools.pytest_collection_floor`` and pass
both ``--minimum-collected`` and ``--collection-floor-suite``.  Ordinary pytest
runs do not load this module and remain unaffected.
"""

from __future__ import annotations

import sys
from collections.abc import Sequence
from typing import Protocol


class _OptionGroup(Protocol):
    """The pytest option-group surface used by this pure-stdlib plugin."""

    def addoption(self, *names: str, **kwargs: object) -> None:
        """Register one command-line option."""


class _Parser(Protocol):
    """The pytest parser surface used during plugin registration."""

    def getgroup(self, name: str) -> _OptionGroup:
        """Return a named option group."""


class _Config(Protocol):
    """The pytest configuration surface used during collection."""

    def getoption(self, name: str) -> object:
        """Return a parsed option value."""


class _Session(Protocol):
    """The pytest session state needed for native failure precedence."""

    testsfailed: int
    Failed: type[BaseException]


def pytest_addoption(parser: _Parser) -> None:
    """Register collection-floor options without changing default pytest runs."""
    group = parser.getgroup("collection floor")
    group.addoption(
        "--minimum-collected",
        action="store",
        type=int,
        default=None,
        help="fail before test execution when fewer than this many items collect",
    )
    group.addoption(
        "--collection-floor-suite",
        action="store",
        default=None,
        help="stable suite label shown by a collection-floor failure",
    )


def pytest_collection_modifyitems(
    session: _Session,
    config: _Config,
    items: Sequence[object],
) -> None:
    """Fail a requested low collection before pytest enters the runtest phase."""
    minimum_value = config.getoption("minimum_collected")
    if minimum_value is None:
        return
    if not isinstance(minimum_value, int):
        raise TypeError("--minimum-collected must be parsed as an integer")
    minimum = minimum_value
    if session.testsfailed:
        # Native collection errors own the outcome and diagnostics.  Replacing
        # them with a low-count failure can turn a broken import into a false
        # attribution and changes pytest's exit status.
        return

    actual = len(items)
    if actual >= minimum:
        return
    suite_value = config.getoption("collection_floor_suite")
    suite = str(suite_value or "pytest suite")
    message = (
        f"{suite}: collected {actual} test(s), expected at least {minimum}"
    )
    print(message, file=sys.stderr)
    raise session.Failed(message)
