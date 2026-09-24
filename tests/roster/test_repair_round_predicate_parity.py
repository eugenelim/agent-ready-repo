#!/usr/bin/env python3
"""The repair-round oracle's transcription must agree with the shipped predicate.

Spec: docs/specs/repair-round-dispatch-assertion/spec.md.

Why this file exists, and why it lives here. The oracle at
`docs/specs/repair-round-dispatch-assertion/notes/walk_reopen_partition.py`
transcribes its predicates from the spec's words and imports nothing from
`_loop_guards` — the norm `wave-complete-dispatch-receipts`'s own walk states,
because an oracle that imports the implementation becomes a mirror of the code it
exists to check. That norm buys independence and costs coupling: nothing then
makes the transcription and the shipped code agree.

This is the coupling, and it is a repository-level assertion because it reads
`docs/` and `packs/` together. A pack test may not read above its own pack, so it
cannot live beside the guard tests.

It fails in BOTH directions on purpose. If the shipped predicate changes and the
transcription does not, the oracle has been silently certifying a rule the code
no longer implements. If the transcription changes and the code does not, the
oracle's conclusions no longer describe anything shipped.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
ORACLE = ROOT / "docs" / "specs" / "repair-round-dispatch-assertion" / "notes" / "walk_reopen_partition.py"
GUARDS = ROOT / "packs" / "core" / ".apm" / "skills" / "work-loop" / "scripts" / "_loop_guards.py"


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader, f"cannot load {path}"
    module = importlib.util.module_from_spec(spec)
    previous = sys.dont_write_bytecode
    sys.dont_write_bytecode = True
    try:
        spec.loader.exec_module(module)
    finally:
        sys.dont_write_bytecode = previous
    return module


@pytest.fixture(scope="module")
def oracle():
    assert ORACLE.is_file(), f"the repair-round oracle is missing at {ORACLE}"
    return _load(ORACLE, "walk_reopen_partition_under_test")


@pytest.fixture(scope="module")
def guards():
    assert GUARDS.is_file(), f"the guard layer is missing at {GUARDS}"
    return _load(GUARDS, "_loop_guards_under_parity_test")


def test_the_accounting_rule_agrees_record_by_record(oracle, guards) -> None:
    """`accounts` and `accounts_for_task` decide every record value identically."""
    values = [
        {"kind": "receipt"},
        {"kind": "receipt", oracle.SUPERSEDED_KEY: True},
        {"kind": "receipt", oracle.SUPERSEDED_KEY: False},
        {"kind": "receipt", oracle.SUPERSEDED_KEY: "yes"},
        {"kind": "receipt", oracle.SUPERSEDED_KEY: None},
        {"kind": "decline", "reason": "human-directed"},
        {"kind": "decline", "reason": "human-directed", oracle.SUPERSEDED_KEY: True},
        {"kind": "decline", "reason": "made-up"},
        {"kind": "bogus"}, {}, None, 42, "receipt", [],
    ]
    disagreements = [
        v for v in values
        if oracle.accounts(v) != guards.accounts_for_task(v)
    ]
    assert not disagreements, (
        "the oracle's transcribed accounting rule and the shipped "
        f"`accounts_for_task` disagree on: {disagreements}"
    )


def test_the_verdict_agrees_over_the_whole_oracle_domain(oracle, guards) -> None:
    """Every reachable state in the oracle's domain gets the same verdict from both.

    Scoped to the states the verdict is reached for: a read refusal is decided
    upstream by the shared reader and never reaches either function, so including
    it would compare an outcome neither produces.
    """
    disagreements = []
    reached = refused = 0
    for state in oracle.build_domain():
        if not state["read"]:
            continue
        reached += 1
        doc = oracle.materialise(state)
        transcribed = oracle.repair_round_refuses(state)
        shipped = not guards._repair_round_verdict(doc).ok
        refused += shipped
        if transcribed != shipped:
            disagreements.append((doc, transcribed, shipped))

    assert not disagreements, (
        f"{len(disagreements)} of {reached} states get different verdicts from the "
        f"transcription and the shipped predicate; first: {disagreements[0]}"
    )
    # Domain adequacy: a parity check over states that all pass proves nothing
    # about the refusing half.
    assert refused, "no state in the oracle's domain refuses; this check cannot fail"
    assert reached - refused, "no state passes; this check cannot fail"


def test_the_accounting_predicate_agrees_over_the_whole_oracle_domain(
    oracle, guards
) -> None:
    """The shared predicate itself, not only the verdict that consumes it.

    The verdict can agree while `unaccounted_wave_tasks` disagrees — the verdict
    only reads whether the live set is empty, so a wrong task identifier in the
    returned list is invisible to it and visible in `wave advance`'s refusal text.
    """
    disagreements = []
    for state in oracle.build_domain():
        if not state["read"]:
            continue
        doc = oracle.materialise(state)
        waves = doc.get("schedule_waves", [])
        if not isinstance(waves, list) or not waves:
            continue
        idx = oracle.pointer_ok(state, waves)
        if idx is None or not oracle.wave_well_formed(waves[idx]):
            continue
        transcribed = oracle.unaccounted(state, idx)
        shipped = guards.unaccounted_wave_tasks(doc, idx)
        if transcribed != shipped:
            disagreements.append((doc, transcribed, shipped))
    assert not disagreements, (
        f"{len(disagreements)} states disagree on the unaccounted task list; "
        f"first: {disagreements[0]}"
    )
