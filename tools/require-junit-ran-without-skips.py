#!/usr/bin/env python3
"""Fail unless a JUnit report shows at least one test, and no skip, error, or failure.

Usage: require-junit-ran-without-skips.py <junit.xml>

A module that skips itself off its target platform would otherwise pass as an
empty success on the platform it exists to cover.
"""

from __future__ import annotations

import sys
import xml.etree.ElementTree as ET  # noqa: S405  # nosec B405  # parses the JUnit report this workflow's own pytest step writes
from pathlib import Path


def check(report: Path) -> list[str]:
    """Return the reasons the report does not prove the suite ran, or an empty list."""
    try:
        root = ET.parse(report).getroot()  # noqa: S314  # nosec B314  # parses the JUnit report this workflow's own pytest step writes
    except (OSError, ET.ParseError) as exc:
        return [f"cannot read {report}: {exc}"]
    cases = list(root.iter("testcase"))
    problems = []
    if not cases:
        problems.append("no tests were collected")
    for case in cases:
        name = f"{case.get('classname', '')}::{case.get('name', '')}"
        for tag in ("skipped", "error", "failure"):
            if case.find(tag) is not None:
                problems.append(f"{tag}: {name}")
    # A module-level skip can be counted on the suite without a skipped child.
    for suite in root.iter("testsuite"):
        for counter in ("skipped", "errors", "failures"):
            try:
                count = int(suite.get(counter, "0"))
            except ValueError:
                count = 1
            if count:
                problems.append(f"suite {suite.get('name', '')!r} reports {counter}={count}")
    return problems


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage: require-junit-ran-without-skips.py <junit.xml>", file=sys.stderr)
        return 2
    problems = check(Path(argv[1]))
    for problem in problems:
        print(problem, file=sys.stderr)
    if not problems:
        print("JUnit report: tests ran, none skipped")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
