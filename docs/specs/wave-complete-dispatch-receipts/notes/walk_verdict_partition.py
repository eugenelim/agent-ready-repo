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

import hashlib
import itertools
import json
from collections import Counter

ABSENT = object()

# --- the spec's declarations, transcribed once ------------------------------
DECLINE_REASONS = frozenset({"no-implementer-installed", "human-directed"})
KEY_PATH = ("partition digest", "wave index", "task identifier")
DEPTH = len(KEY_PATH)
SUPPORTED_SCHEMA = 1

# Read outcomes. `parses` records whether the FILE parses, which is not the
# same as the read succeeding: a non-object root parses and the read refuses it.
# The guard acquires state through spec-directory resolution AND the state
# read, so both vocabularies belong here. The rows do not discriminate among
# refusal kinds — row 1 fires for any of them — so this axis is deliberately
# two-valued for the partition, with the vocabulary listed for the row-1
# wording it must cover. Enumerating each kind as a separate axis value would
# inflate the state count without adding a distinction any predicate makes.
ACQUISITION_REFUSALS = (
    "spec-dir cannot be examined", "spec-dir is not a directory",
    "missing", "unparseable", "non-object-root", "non-regular-file",
    "changed-while-opening", "changed-while-reading", "could-not-be-read-safely",
    "invalid-utf8", "malformed", "nested-too-deeply", "oversized",
    "non-finite-number",
)
READ_OUTCOMES = ("ok", "refuses")


def is_record(value) -> bool:
    """A record: kind in {receipt, decline}, a decline carrying a closed reason.

    Total over any value, which the docstring alone did not make it: round 10
    added a hostile leaf whose `reason` was a list, and `x in frozenset` raises
    `TypeError` for an unhashable `x`. The spec criterion claims the predicate
    is total over every value a position can hold, so a raise here falsifies
    the criterion rather than merely crashing the walk. The `isinstance` guard
    is the fix, not a `try`: a non-string reason is *not* in the closed set, and
    that is an answer, not an error.
    """
    if not isinstance(value, dict):
        return False
    kind = value.get("kind")
    if kind == "receipt":
        return True
    if kind == "decline":
        reason = value.get("reason")
        return isinstance(reason, str) and reason in DECLINE_REASONS
    return False


def container_well_formed(container, depth: int = DEPTH) -> bool:
    """Total over any value. Depth comes from KEY_PATH, never from a literal."""
    if depth == 0:
        return is_record(container)
    if not isinstance(container, dict):
        return False
    return all(container_well_formed(v, depth - 1) for v in container.values())


def partition_digest(schedule_waves) -> str:
    """A stable function of the partition value alone, as the spec declares."""
    return hashlib.sha256(
        json.dumps(schedule_waves, sort_keys=True, default=repr).encode()
    ).hexdigest()[:16]


def nest(value, depth: int):
    """Wrap `value` in `depth` mapping levels, for SHAPE cases only.

    Shape cases probe well-formedness, which is depth- and leaf-typed. They
    deliberately use a placeholder key, so they must never be used to probe
    accounting: a container built this way holds no record at the declared key
    path. Accounting cases go through `keyed_container`.
    """
    for _ in range(depth):
        value = {"k": value}
    return value


def keyed_container(schedule_waves, index, tasks, *, record=None,
                    digest=None, wave_key=None, order=("d", "w", "t")) -> dict:
    """A container keyed by the DECLARED path: digest, decimal index, task.

    `digest`, `wave_key` and `order` exist so a walk can construct the
    wrong-key, wrong-form and wrong-order containers a mis-implemented lookup
    would produce. Defaults build the correct shape.
    """
    record = record or {"kind": "receipt"}
    d = digest if digest is not None else partition_digest(schedule_waves)
    w = wave_key if wave_key is not None else str(index)
    leaves = {task: dict(record) for task in tasks}
    parts = {"d": d, "w": w}
    outer, inner = (parts[order[0]], parts[order[1]])
    return {outer: {inner: leaves}}


def partition_of(state) -> object:
    """`schedule_waves` read with its default, as the spec words it."""
    return [] if state["sw"] is ABSENT else state["sw"]


def readable(state) -> bool:
    return state["read"] == "ok"


def schema_supported(state) -> bool:
    return state["schema"] == SUPPORTED_SCHEMA


def state_well_formed(state) -> bool:
    """Non-empty partition, and a container that is absent or correctly shaped.

    The partition must be non-empty: an empty one is unreachable through the
    engine (the `plan-locked` guard refuses it), so at this exit it is malformed
    state rather than a passing case.
    """
    part = partition_of(state)
    if not isinstance(part, list) or not part:
        return False
    return state["cont"] is ABSENT or container_well_formed(state["cont"])


def pointer_valid(state) -> bool:
    """Non-negative int, rejecting bool, read as zero when the key is absent."""
    index = 0 if state["idx"] is ABSENT else state["idx"]
    if isinstance(index, bool) or not isinstance(index, int) or index < 0:
        return False
    part = partition_of(state)
    return isinstance(part, list) and index < len(part)


def unaccounted_tasks(state) -> list[str]:
    """Tasks in the current wave with no record at the declared key path.

    Computed from the container, not varied as an axis. An earlier version of
    this script carried `accounted` as a free boolean, so no state in its
    domain held a record where the guard looks and the accounted/unaccounted
    split rested on a variable no predicate computed — which left a wrong-key,
    wrong-form or wrong-order lookup green with every row reachable.
    """
    index = 0 if state["idx"] is ABSENT else state["idx"]
    wave = partition_of(state)[index]
    container = state["cont"]
    digest = partition_digest(partition_of(state))
    holding = container.get(digest, {}).get(str(index), {})
    if not isinstance(holding, dict):
        return list(wave)
    return [task for task in wave if not is_record(holding.get(task))]


def current_wave_well_formed(state) -> bool:
    """A non-empty list of strings.

    Non-empty matters: `topological_waves` never emits an empty wave, and an
    empty one would make "every task accounted for" vacuously true over zero
    tasks and exit silent.
    """
    index = 0 if state["idx"] is ABSENT else state["idx"]
    wave = partition_of(state)[index]
    return (isinstance(wave, list) and bool(wave)
            and all(isinstance(t, str) for t in wave))


def matching_rows(state) -> list[str]:
    """Every row whose precondition the state satisfies, encoded from the spec."""
    hits = []
    container_present = state["cont"] is not ABSENT

    if not readable(state):
        hits.append("R1-read-refuses")
    if readable(state) and not schema_supported(state):
        hits.append("R2-schema-unsupported")

    live = readable(state) and schema_supported(state)
    well_formed = live and state_well_formed(state)
    if live and not well_formed:
        hits.append("R3-malformed")

    base = well_formed and container_present
    if well_formed and not container_present:
        hits.append("R4-container-absent")
    if base and not pointer_valid(state):
        hits.append("R5-pointer-invalid")
    if base and pointer_valid(state) and not current_wave_well_formed(state):
        hits.append("R6-wave-malformed")
    if base and pointer_valid(state) and current_wave_well_formed(state):
        hits.append(
            "R8-unaccounted" if unaccounted_tasks(state) else "R7-accounted"
        )
    return hits


ROWS = (
    "R1-read-refuses", "R2-schema-unsupported", "R3-malformed",
    "R4-container-absent", "R5-pointer-invalid", "R6-wave-malformed",
    "R7-accounted", "R8-unaccounted",
)

HOSTILE_VALUES = (
    42, "receipt", [], None, {}, {"kind": "bogus"},
    {"kind": "decline"}, {"kind": "decline", "reason": "made-up"},
    # The declared axes vary a record's `kind` and `reason` by presence, type
    # AND value. Round 10 found only presence and value covered: every leaf
    # above carries a string `kind` or omits it, so a predicate comparing
    # `kind` without a type check stayed green.
    {"kind": 7}, {"kind": ["receipt"]},
    {"kind": "decline", "reason": 7},
    {"kind": "decline", "reason": ["no-implementer-installed"]},
)


def build_domain() -> list[dict]:
    """Construct the state domain.

    Two families. SHAPE cases probe well-formedness and use placeholder keys.
    ACCOUNTING cases are keyed by the declared path, and include the containers
    a wrong-key, wrong-form or wrong-order lookup would produce, so such a
    lookup is exhibitable rather than invisible.
    """
    live_sw = [["T1"], ["T2"]]
    live_idx = 0
    tasks = live_sw[live_idx]
    stale_sw = [["T1"], ["T2"], ["T3"]]

    shape_containers = [
        ABSENT,
        nest({"kind": "receipt"}, DEPTH),
        nest({"kind": "decline", "reason": "human-directed"}, DEPTH),
    ]
    shape_containers += [
        nest(value, depth)
        for depth in range(DEPTH + 1)
        for value in HOSTILE_VALUES
    ]

    accounting_containers = [
        keyed_container(live_sw, live_idx, tasks),
        keyed_container(live_sw, live_idx, tasks,
                        record={"kind": "decline", "reason": "human-directed"}),
        keyed_container(live_sw, live_idx, []),
        keyed_container(live_sw, live_idx, tasks,
                        digest=partition_digest(stale_sw)),
        keyed_container(live_sw, live_idx, tasks, wave_key=live_idx),
        keyed_container(live_sw, live_idx, tasks, wave_key="wave-0"),
        keyed_container(live_sw, live_idx, tasks, order=("w", "d", "t")),
    ]

    schedules = [
        ABSENT, [], [["T1"]], "notalist", [123], [["T1", 2]],
        live_sw, {"a": 1}, [[]], [[], ["T2"]], [["T1"], []],
    ]
    pointers = [ABSENT, 0, 1, -1, True, "x", 1.0]
    schemas = (SUPPORTED_SCHEMA, 99, None, ABSENT)

    return [
        {"read": read, "sw": sw, "cont": cont, "idx": idx, "schema": schema}
        for read, sw, cont, idx, schema in itertools.product(
            READ_OUTCOMES, schedules,
            shape_containers + accounting_containers, pointers, schemas,
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
    live_sw = [["T1"], ["T2"]]
    canonical = {
        "read": "ok", "sw": live_sw, "idx": 0, "schema": SUPPORTED_SCHEMA,
        "cont": keyed_container(live_sw, 0, live_sw[0]),
    }
    assert matching_rows(canonical) == ["R7-accounted"], (
        f"a record at the declared key path must account for its task, got "
        f"{matching_rows(canonical)}"
    )
    # The negative half: the same record under a wrong-form wave key must NOT
    # account. Without this, a lookup using the integer index passes.
    wrong_form = dict(canonical)
    wrong_form["cont"] = keyed_container(live_sw, 0, live_sw[0], wave_key=0)
    assert matching_rows(wrong_form) == ["R8-unaccounted"], (
        "a record keyed by the integer wave index must not account for its "
        f"task; the declared form is the decimal string. got "
        f"{matching_rows(wrong_form)}"
    )
    wrong_order = dict(canonical)
    wrong_order["cont"] = keyed_container(live_sw, 0, live_sw[0],
                                          order=("w", "d", "t"))
    assert matching_rows(wrong_order) == ["R8-unaccounted"], (
        "a record keyed wave-then-digest must not account for its task; the "
        f"declared order is digest, wave, task. got {matching_rows(wrong_order)}"
    )

    # Verdict anchors for the two vacuous passes round 8 found. A partition
    # walk cannot catch these on its own: a wrong verdict is neither an overlap
    # nor a gap, so only a declared expected verdict reddens.
    empty_part = {"read": "ok", "sw": [], "cont": ABSENT, "idx": 0,
                  "schema": SUPPORTED_SCHEMA}
    assert matching_rows(empty_part) == ["R3-malformed"], (
        f"an empty partition must be malformed, not a pass; got "
        f"{matching_rows(empty_part)}"
    )
    empty_wave_sw = [[], ["T2"]]
    empty_wave = {"read": "ok", "sw": empty_wave_sw, "idx": 0,
                  "schema": SUPPORTED_SCHEMA,
                  "cont": keyed_container(empty_wave_sw, 0, [])}
    assert matching_rows(empty_wave) == ["R6-wave-malformed"], (
        "an empty current wave must be malformed, not a vacuous pass over zero "
        f"tasks; got {matching_rows(empty_wave)}"
    )

    # ACQUISITION_REFUSALS was an inert constant a review caught: the read axis
    # is two-valued, so nothing read the vocabulary and its presence read as
    # coverage it did not provide. It now carries the row-1 scope claim as an
    # assertion: every kind LISTED here lands on row 1 and nowhere else.
    #
    # Bound, stated because the assertion looks stronger than it is: the list is
    # maintained by hand against the reader's source, so deleting an entry, or
    # the reader growing a refusal kind nobody adds here, leaves this green.
    # What is proved is that the two-valued collapse loses no case AMONG THE
    # LISTED KINDS — not that the list is the reader's whole vocabulary. Closing
    # that would mean deriving the vocabulary from `_loop_guards` itself, which
    # a notes script under `docs/` should not import; the completeness half is
    # T1's survey obligation instead.
    assert ACQUISITION_REFUSALS, "the acquisition vocabulary is empty"
    assert "ok" not in ACQUISITION_REFUSALS, (
        "'ok' is the success value; listing it as a refusal kind would make "
        "readable() true for a state row 1 must claim"
    )
    for kind in ACQUISITION_REFUSALS:
        refused = {"read": kind, "sw": live_sw, "idx": 0,
                   "schema": SUPPORTED_SCHEMA,
                   "cont": keyed_container(live_sw, 0, live_sw[0])}
        assert matching_rows(refused) == ["R1-read-refuses"], (
            f"acquisition refusal {kind!r} must classify to the read-refusal "
            f"row alone; got {matching_rows(refused)}"
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
