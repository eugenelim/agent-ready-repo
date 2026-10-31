#!/usr/bin/env python3
"""Roster for pre-cutover-closure.

Spec: docs/specs/pre-cutover-closure/spec.md

AC-0005: the Status line of docs/specs/closure-eligibility-check/spec.md still
begins ``Shipped``, keeps its earlier supersession note, and records the
supersession by pre-cutover-closure (criterion 0031, the packet's registry
field).
AC-0006: close-work's eval file holds one case whose assertions require that the
closure packet names no ``workspace.toml`` entry.

Standard library and pytest only; the checks read files and write nothing.
"""

from __future__ import annotations

import json
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
_SPEC = "docs/specs/closure-eligibility-check/spec.md"
_EVALS = "packs/core/.apm/skills/close-work/evals/evals.json"
_CASE_ID = "eligible-packet-names-no-registry-entry"


def _status_line() -> str:
    """Return the ``- **Status:**`` line of the closure-eligibility-check spec."""
    for line in (_REPO / _SPEC).read_text(encoding="utf-8").splitlines():
        if line.startswith("- **Status:**"):
            return line
    raise AssertionError(f"no Status line in {_SPEC}")


def test_ac0005_status_records_supersession() -> None:
    """The Status line stays Shipped and names pre-cutover-closure's criterion 0031."""
    status = _status_line()
    assert status.removeprefix("- **Status:**").strip().startswith("Shipped")
    assert "close-work-intent-graph-convergence" in status
    assert "(../pre-cutover-closure/spec.md)" in status
    assert "0031" in status


def test_ac0006_eval_case_requires_no_registry_entry() -> None:
    """Exactly one eval case asserts the packet names no `workspace.toml` entry."""
    cases = json.loads((_REPO / _EVALS).read_text(encoding="utf-8"))["evals"]
    matching = [c for c in cases if c["id"] == _CASE_ID]
    assert len(matching) == 1
    hits = [
        a
        for a in matching[0]["assertions"]
        if "`workspace.toml`" in a and "names no" in a
    ]
    assert len(hits) == 1
