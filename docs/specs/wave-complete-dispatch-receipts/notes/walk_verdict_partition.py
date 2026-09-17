#!/usr/bin/env python3
"""Walk the wave-exit verdict table's preconditions over a constructed domain.

This is the generator for the partition results the verification ledger records.
Earlier walks were ad-hoc scripts whose output was read by eye, which is unsafe
in a specific way: the pass verdict is "no state matched two rows and no state
matched none", and both are vacuously true of an empty domain. This script
asserts instead of printing, so a generator that produces nothing fails rather
than reporting success.

Two rules this file exists to enforce, both learned from earlier walks that were
green and wrong:

1. The row predicates are encoded from the spec's WORDS, not from the author's
   intent. A precondition the spec does not state must not appear here. The
   fourth walk hid a real overlap because its row-3 encoding carried a schema
   clause the spec text did not have.
2. The container domain is generated from the declared key path, not hand-built
   at a literal depth. The fifth walk was green while the predicate rejected
   every valid container, because both were built two keys deep while the data
   model declared three.

Usage, from the repository root:

    python3 docs/specs/wave-complete-dispatch-receipts/notes/walk_verdict_partition.py

Exit 0 means: the domain is non-empty, every constructed state matches exactly
one row, and every row is matched by at least one state. Any other outcome
raises.
"""

from __future__ import annotations

import itertools
from collections import Counter

ABSENT = object()

# --- the spec's declarations, transcribed once ------------------------------
DECLINE_REASONS = frozenset({"no-implementer-installed", "human-directed"})
KEY_PATH = ("partition digest", "wave index", "task identifier")
DEPTH = len(KEY_PATH)
SUPPORTED_SCHEMA = 1

# Read outcomes. `parses` records whether the FILE parses, which is not the
# same as the read succeeding: a non-object root parses and the read refuses it.
READ_OUTCOMES = {
    "ok": True,
    "missing": False,
    "unparseable": False,
    "non-object-root": True,
    "non-regular-file": False,
    "changed-while-reading": False,
    "oversized": False,
    "non-finite-number": True,
}


def is_record(value) -> bool:
    """A record: kind in {receipt, decline}, a decline carrying a closed reason."""
    if not isinstance(value, dict):
        return False
    kind = value.get("kind")
    if kind == "receipt":
        return True
    if kind == "decline":
        return value.get("reason") in DECLINE_REASONS
    return False


def container_well_formed(container, depth: int = DEPTH) -> bool:
    """Total over any value. Depth comes from KEY_PATH, never from a literal."""
    if depth == 0:
        return is_record(container)
    if not isinstance(container, dict):
        return False
    return all(container_well_formed(v, depth - 1) for v in container.values())


def nest(value, depth: int):
    """Wrap `value` in `depth` mapping levels, mirroring the declared key path."""
    for _ in range(depth):
        value = {"k": value}
    return value


def partition_of(state) -> object:
    """`schedule_waves` read with its default, as the spec words it."""
    return [] if state["sw"] is ABSENT else state["sw"]


def readable(state) -> bool:
    return state["read"] == "ok"


def schema_supported(state) -> bool:
    return state["schema"] == SUPPORTED_SCHEMA


def state_well_formed(state) -> bool:
    if not isinstance(partition_of(state), list):
        return False
    return state["cont"] is ABSENT or container_well_formed(state["cont"])


def pointer_valid(state) -> bool:
    """Non-negative int, rejecting bool, read as zero when the key is absent."""
    index = 0 if state["idx"] is ABSENT else state["idx"]
    if isinstance(index, bool) or not isinstance(index, int) or index < 0:
        return False
    part = partition_of(state)
    return isinstance(part, list) and index < len(part)


def current_wave_well_formed(state) -> bool:
    index = 0 if state["idx"] is ABSENT else state["idx"]
    wave = partition_of(state)[index]
    return isinstance(wave, list) and all(isinstance(t, str) for t in wave)


def matching_rows(state) -> list[str]:
    """Every row whose precondition the state satisfies, encoded from the spec."""
    hits = []
    part = partition_of(state)
    container_present = state["cont"] is not ABSENT

    if not readable(state):
        hits.append("R1-read-refuses")
    if readable(state) and not schema_supported(state):
        hits.append("R2-schema-unsupported")

    live = readable(state) and schema_supported(state)
    well_formed = live and state_well_formed(state)
    if live and not well_formed:
        hits.append("R3-malformed")

    base = well_formed and part != [] and container_present
    if well_formed and part == []:
        hits.append("R4-empty-partition")
    if well_formed and part != [] and not container_present:
        hits.append("R5-container-absent")
    if base and not pointer_valid(state):
        hits.append("R6-pointer-invalid")
    if base and pointer_valid(state) and not current_wave_well_formed(state):
        hits.append("R7-wave-malformed")
    if base and pointer_valid(state) and current_wave_well_formed(state):
        hits.append("R8-accounted" if state["acct"] else "R9-unaccounted")
    return hits


ROWS = (
    "R1-read-refuses", "R2-schema-unsupported", "R3-malformed",
    "R4-empty-partition", "R5-container-absent", "R6-pointer-invalid",
    "R7-wave-malformed", "R8-accounted", "R9-unaccounted",
)

HOSTILE_VALUES = (
    42, "receipt", [], None, {}, {"kind": "bogus"},
    {"kind": "decline"}, {"kind": "decline", "reason": "made-up"},
)


def build_domain() -> list[dict]:
    """Construct the state domain. Container values derive from KEY_PATH."""
    containers = [
        ABSENT,
        nest({"kind": "receipt"}, DEPTH),
        nest({"kind": "decline", "reason": "human-directed"}, DEPTH),
    ]
    # Mutate a correctly nested instance at every depth with every hostile
    # value, so a depth mismatch between predicate and domain is exhibitable.
    containers += [
        nest(value, depth)
        for depth in range(DEPTH + 1)
        for value in HOSTILE_VALUES
    ]
    schedules = [
        ABSENT, [], [["T1"]], "notalist", [123], [["T1", 2]],
        [["T1"], ["T2"]], {"a": 1},
    ]
    pointers = [ABSENT, 0, 1, -1, True, "x", 1.0]
    return [
        {"read": read, "sw": sw, "cont": cont, "idx": idx,
         "acct": acct, "schema": schema}
        for read, sw, cont, idx, acct, schema in itertools.product(
            READ_OUTCOMES, schedules, containers, pointers, (True, False),
            (SUPPORTED_SCHEMA, 99, None),
        )
    ]


def main() -> int:
    domain = build_domain()

    # The assertion the earlier ad-hoc walks lacked: a silent generator must
    # fail, not pass. Every verdict below is vacuous on an empty domain.
    assert domain, "the domain generator produced no states"

    # Partition properties alone do not constrain the predicate's correctness:
    # an empty mapping is vacuously well-formed at any depth, so every row can
    # stay reachable while the predicate rejects every real record. These three
    # anchors are the discriminating positive and negative cases that pin the
    # declared depth. Without them, a predicate bounded one key short of
    # KEY_PATH passes every check below.
    good = nest({"kind": "receipt"}, DEPTH)
    assert container_well_formed(good), (
        "a container nested to the declared key-path depth must be well-formed; "
        "the predicate is bounded at the wrong depth"
    )
    assert not container_well_formed(nest({"kind": "receipt"}, DEPTH - 1)), (
        "a container one key short of the declared depth must be rejected"
    )
    canonical = {"read": "ok", "sw": [["T1"]], "cont": good, "idx": 0,
                 "acct": True, "schema": SUPPORTED_SCHEMA}
    assert matching_rows(canonical) == ["R8-accounted"], (
        f"the canonical accounted state must match R8 alone, got "
        f"{matching_rows(canonical)}"
    )

    hits = [(state, matching_rows(state)) for state in domain]
    overlapping = [(s, r) for s, r in hits if len(r) > 1]
    uncovered = [s for s, r in hits if not r]
    reached = Counter(row for _, rows in hits for row in rows)

    print(f"states walked        : {len(domain)}")
    print(f"overlapping          : {len(overlapping)}")
    print(f"uncovered            : {len(uncovered)}")
    print("row reachability     :")
    for row in ROWS:
        print(f"    {row:<24} {reached[row]}")

    if overlapping:
        sample = {tuple(r) for _, r in overlapping}
        raise AssertionError(f"rows overlap: {sorted(sample)}")
    if uncovered:
        raise AssertionError(f"{len(uncovered)} states match no row")
    unreached = [row for row in ROWS if not reached[row]]
    if unreached:
        raise AssertionError(f"rows never reached: {unreached}")

    print("\nOK: domain non-empty, exactly one row per state, every row reached.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
