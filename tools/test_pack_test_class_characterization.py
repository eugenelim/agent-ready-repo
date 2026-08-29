"""Characterize declared grouped pack-test collection safely.

AC16 (skip/xfail dispositions) and AC18 (failure injection) deliberately stay
out of this test: exercising them requires executing the suites, which would
roughly double the cost of ``make test``. Their implementation-time evidence is
recorded in the feature plan. This module instead uses collection-only pytest
processes to check AC15, AC17, and AC19 cheaply on every declared class.
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
from collections.abc import Sequence
from pathlib import Path

import pytest

from tools.pack_test_compatibility import CLASSES, CompatibilityClass

ROOT = Path(__file__).resolve().parent.parent
_COLLECTION_ERROR_MARKER = re.compile(r"(?m)^(?:=+ ERRORS =+|ERROR(?:\s|$))")
_EXPECTED_NODE_ID_COUNTS = {
    "agent-skill-engineering-contract": 78,
    "architect-contract": 71,
    "converters-invocation-contract": 12,
    "desk-research-content": 17,
    "linear-intake": 32,
}


class CollectedNodeIds(list[str]):
    """Collected pytest node IDs together with their command's combined output."""

    def __init__(self, node_ids: list[str], output: str) -> None:
        super().__init__(node_ids)
        self.output = output


def collect_node_ids(
    members: Sequence[str], import_mode: str | None
) -> tuple[int, CollectedNodeIds]:
    """Collect *members* and return pytest's exit code and collected node IDs."""

    argv = [
        sys.executable,
        "-m",
        "pytest",
        "--collect-only",
        "-q",
        "-p",
        "no:cacheprovider",
    ]
    if import_mode is not None:
        argv.append(f"--import-mode={import_mode}")
    argv.extend(members)
    completed = subprocess.run(
        argv,
        cwd=ROOT,
        check=False,
        env=os.environ | {"PYTHONDONTWRITEBYTECODE": "1"},
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    node_ids = [
        line
        for raw_line in completed.stdout.splitlines()
        if (line := raw_line.strip()).startswith("packs/") and "::" in line
    ]
    return completed.returncode, CollectedNodeIds(node_ids, completed.stdout)


def _assert_success(
    compatibility_class: CompatibilityClass,
    description: str,
    exit_code: int,
    node_ids: CollectedNodeIds,
) -> None:
    """Assert a collection command succeeded, preserving its output on failure."""

    assert exit_code == 0, (
        f"{compatibility_class.identifier}: {description} collection exited "
        f"{exit_code}; captured output:\n{node_ids.output}"
    )


def _assert_unique(
    compatibility_class: CompatibilityClass,
    description: str,
    node_ids: CollectedNodeIds,
) -> None:
    """Assert that a collection output contains each node ID no more than once."""

    assert len(node_ids) == len(set(node_ids)), (
        f"{compatibility_class.identifier}: {description} collection contains "
        f"duplicate node IDs: {node_ids}"
    )


def _assert_same_nodes(
    compatibility_class: CompatibilityClass,
    description: str,
    expected: CollectedNodeIds,
    actual: CollectedNodeIds,
) -> None:
    """Assert node-ID set equality with an actionable symmetric difference."""

    expected_set = set(expected)
    actual_set = set(actual)
    symmetric_difference = sorted(expected_set ^ actual_set)
    assert expected_set == actual_set, (
        f"{compatibility_class.identifier}: {description} node-ID sets differ; "
        f"symmetric difference: {symmetric_difference}"
    )


@pytest.mark.parametrize("compatibility_class", CLASSES, ids=lambda item: item.identifier)
def test_declared_class_collection_characterization(
    compatibility_class: CompatibilityClass,
) -> None:
    """Keep every declared class's grouped collection equivalent and load-bearing."""

    isolated_node_ids = CollectedNodeIds([], "")
    for member in compatibility_class.members:
        exit_code, member_node_ids = collect_node_ids((member,), compatibility_class.import_mode)
        _assert_success(compatibility_class, f"isolated {member}", exit_code, member_node_ids)
        isolated_node_ids.extend(member_node_ids)

    forward_exit_code, forward_node_ids = collect_node_ids(
        compatibility_class.members, compatibility_class.import_mode
    )
    _assert_success(compatibility_class, "grouped forward", forward_exit_code, forward_node_ids)
    assert forward_node_ids, (
        f"{compatibility_class.identifier}: grouped forward collection produced no node IDs; "
        f"captured output:\n{forward_node_ids.output}"
    )
    assert len(forward_node_ids) == _EXPECTED_NODE_ID_COUNTS[compatibility_class.identifier]
    _assert_unique(compatibility_class, "isolated", isolated_node_ids)
    _assert_unique(compatibility_class, "grouped forward", forward_node_ids)
    _assert_same_nodes(
        compatibility_class,
        "isolated union and grouped forward",
        isolated_node_ids,
        forward_node_ids,
    )

    output = forward_node_ids.output
    assert not _COLLECTION_ERROR_MARKER.search(output) and "import file mismatch" not in output.lower(), (
        f"{compatibility_class.identifier}: grouped forward collection reported an "
        f"error marker; captured output:\n{forward_node_ids.output}"
    )

    reverse_exit_code, reverse_node_ids = collect_node_ids(
        tuple(reversed(compatibility_class.members)), compatibility_class.import_mode
    )
    _assert_success(compatibility_class, "grouped reverse", reverse_exit_code, reverse_node_ids)
    _assert_unique(compatibility_class, "grouped reverse", reverse_node_ids)
    _assert_same_nodes(
        compatibility_class,
        "grouped forward and reverse",
        forward_node_ids,
        reverse_node_ids,
    )

    if compatibility_class.import_mode == "importlib":
        unflagged_exit_code, unflagged_node_ids = collect_node_ids(
            compatibility_class.members, None
        )
        assert (
            unflagged_exit_code != 0 or len(unflagged_node_ids) < len(forward_node_ids)
        ), (
            f"{compatibility_class.identifier}: removing --import-mode=importlib "
            "still succeeded without collecting fewer node IDs; the flag is not "
            f"load-bearing. Captured output:\n{unflagged_node_ids.output}"
        )
