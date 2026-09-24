#!/usr/bin/env python3
"""Committed oracle for the repair-round verdict, and for the row movement it causes.

Two rules, inherited deliberately from `wave-complete-dispatch-receipts`'s
`notes/walk_verdict_partition.py`:

1. The predicates below are transcribed from the SPEC'S WORDS, not from the
   implementation. This script imports nothing from `_loop_guards`, because that
   walk states a notes script under `docs/` should not, and routes the coupling
   to a test instead. The coupling here is
   `packs/core/tests/skills/work-loop/test_repair_round_predicate_parity.py`,
   which drives this transcription and the shipped predicate over this same
   domain and refuses any state they disagree on. Import the implementation here
   and the oracle becomes a mirror of the code it exists to check.
2. Container values are generated from the declared key path rather than
   hand-built at a literal depth, so the walk cannot ratify the shape its author
   happened to construct.

What it establishes:

- the repair-round verdict refuses on exactly the states carrying a live record
  for the current wave, and passes on every other state it is reached for;
- the states it is never reached for are the read refusals, decided upstream;
- superseding every record in the current wave moves that state from the
  wave-exit verdict's R7 to its R8, and moves nothing else.

Run: python3 docs/specs/repair-round-dispatch-assertion/notes/walk_reopen_partition.py
"""

from __future__ import annotations

import hashlib
import itertools
import json

SUPPORTED_SCHEMA = 1
RECEIPTS_KEY = "dispatch_receipts"
SUPERSEDED_KEY = "superseded"
DECLINE_REASONS = ("no-implementer-installed", "human-directed")
KEY_PATH = ("partition digest", "wave index", "task identifier")
DEPTH = len(KEY_PATH)
ABSENT = object()
READ_OUTCOMES = (True, False)  # two-valued: no row discriminates refusal kinds


def digest_of(waves) -> str:
    payload = json.dumps(waves, sort_keys=True, separators=(",", ":"), default=repr)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def is_record(value) -> bool:
    """Transcribed: a mapping whose kind is receipt, or decline with a closed reason."""
    if not isinstance(value, dict):
        return False
    kind = value.get("kind")
    if kind == "receipt":
        return True
    if kind == "decline":
        reason = value.get("reason")
        return isinstance(reason, str) and reason in DECLINE_REASONS
    return False


def accounts(value) -> bool:
    """Transcribed from the spec: a record accounts unless it is superseded."""
    return is_record(value) and value.get(SUPERSEDED_KEY) is not True


def nest(leaf, depth):
    for _ in range(depth):
        leaf = {"k": leaf}
    return leaf


def container_well_formed(container, depth=DEPTH) -> bool:
    if depth == 0:
        return is_record(container)
    if not isinstance(container, dict):
        return False
    return all(container_well_formed(v, depth - 1) for v in container.values())


def keyed_container(waves, index, tasks, *, record=None, digest=None):
    """A container built from the DECLARED key path, never at a literal depth."""
    record = record or {"kind": "receipt"}
    leaves = {task: dict(record) for task in tasks}
    node = leaves
    for key in reversed((digest or digest_of(waves), str(index))):
        node = {key: node}
    return node


def wave_well_formed(wave) -> bool:
    return isinstance(wave, list) and bool(wave) and all(isinstance(t, str) for t in wave)


def pointer_ok(state, waves):
    idx = state["idx"]
    if idx is ABSENT:
        idx = 0
    if isinstance(idx, bool) or not isinstance(idx, int) or idx < 0:
        return None
    return idx if idx < len(waves) else None


def materialise(state) -> dict:
    out = {}
    if state["schema"] is not ABSENT:
        out["schema_version"] = state["schema"]
    if state["sw"] is not ABSENT:
        out["schedule_waves"] = state["sw"]
    if state["cont"] is not ABSENT:
        out[RECEIPTS_KEY] = state["cont"]
    if state["idx"] is not ABSENT:
        out["current_wave_index"] = state["idx"]
    return out


def live_tasks(state):
    """Tasks in the current wave whose record still accounts. None when unreachable."""
    doc = materialise(state)
    waves = doc.get("schedule_waves", [])
    if not isinstance(waves, list) or not waves:
        return None
    idx = pointer_ok(state, waves)
    if idx is None:
        return None
    wave = waves[idx]
    if not wave_well_formed(wave):
        return None
    held = doc.get(RECEIPTS_KEY)
    for key in (digest_of(waves), str(idx)):
        held = held.get(key) if isinstance(held, dict) else None
    if not isinstance(held, dict):
        return []
    return [t for t in wave if accounts(held.get(t))]


def unaccounted(state, index):
    """Transcribed twin of the shared accounting predicate, `unaccounted_wave_tasks`.

    The absent-container exemption is carried INSIDE this function rather than
    beside it, because the shipped predicate carries it inside too and every
    consumer inherits it by calling — a transcription that lifted the exemption
    out would disagree with the code for exactly the oldest state class the
    receipts design deliberately tolerates.
    """
    doc = materialise(state)
    if RECEIPTS_KEY not in doc:
        return []
    waves = doc.get("schedule_waves", [])
    if not isinstance(waves, list) or not 0 <= index < len(waves):
        return []
    wave = waves[index]
    if not wave_well_formed(wave):
        return []
    held = doc.get(RECEIPTS_KEY)
    for key in (digest_of(waves), str(index)):
        held = held.get(key) if isinstance(held, dict) else None
    if not isinstance(held, dict):
        return list(wave)
    return [task for task in wave if not accounts(held.get(task))]


def repair_round_refuses(state) -> bool:
    """Transcribed conjunction from the spec's § The repair-round verdict."""
    if not state["read"]:
        return False  # never reached; the reader refused upstream
    doc = materialise(state)
    if doc.get("schema_version") != SUPPORTED_SCHEMA:
        return False
    if RECEIPTS_KEY not in doc:
        return False
    if not container_well_formed(doc[RECEIPTS_KEY]):
        return False
    return bool(live_tasks(state))


def wave_exit_row(state) -> str:
    """Transcribed from the frozen spec's eight-row table, for the movement check."""
    if not state["read"]:
        return "R1-read-refuses"
    doc = materialise(state)
    if doc.get("schema_version") != SUPPORTED_SCHEMA:
        return "R2-schema-unsupported"
    waves = doc.get("schedule_waves", [])
    if not isinstance(waves, list) or not waves:
        return "R3-malformed"
    if RECEIPTS_KEY in doc and not container_well_formed(doc[RECEIPTS_KEY]):
        return "R3-malformed"
    if RECEIPTS_KEY not in doc:
        return "R4-container-absent"
    idx = pointer_ok(state, waves)
    if idx is None:
        return "R5-pointer-invalid"
    if not wave_well_formed(waves[idx]):
        return "R6-wave-malformed"
    return "R8-unaccounted" if len(live_tasks(state)) < len(waves[idx]) else "R7-accounted"


HOSTILE = (
    42, "receipt", [], None, {}, {"kind": "bogus"},
    {"kind": "decline"}, {"kind": "decline", "reason": "made-up"},
    {"kind": 7}, {"kind": ["receipt"]},
    {"kind": "decline", "reason": 7},
    {"kind": "decline", "reason": ["no-implementer-installed"]},
)


def build_domain():
    live_sw = [["T1"], ["T2"]]
    idx0, tasks = 0, live_sw[0]
    stale_sw = [["T1"], ["T2"], ["T3"]]
    gone = {"kind": "receipt", SUPERSEDED_KEY: True}

    containers = [ABSENT, nest({"kind": "receipt"}, DEPTH)]
    containers += [nest(v, d) for d in range(DEPTH + 1) for v in HOSTILE]
    containers += [
        keyed_container(live_sw, idx0, tasks),
        keyed_container(live_sw, idx0, tasks, record=gone),
        keyed_container(live_sw, idx0, tasks,
                        record={"kind": "decline", "reason": "human-directed"}),
        keyed_container(live_sw, idx0, tasks,
                        record={"kind": "decline", "reason": "human-directed",
                                SUPERSEDED_KEY: True}),
        # the superseded axis, varied by type and value as well as presence:
        # only `True` supersedes, so a truthy non-True must leave the record live
        keyed_container(live_sw, idx0, tasks, record={"kind": "receipt",
                                                      SUPERSEDED_KEY: "yes"}),
        keyed_container(live_sw, idx0, tasks, record={"kind": "receipt",
                                                      SUPERSEDED_KEY: False}),
        keyed_container(live_sw, idx0, [], ),
        keyed_container(live_sw, idx0, tasks, digest=digest_of(stale_sw)),
    ]
    schedules = [ABSENT, [], [["T1"]], "notalist", [123], [["T1", 2]],
                 live_sw, {"a": 1}, [[]], [[], ["T2"]], [["T1"], []]]
    pointers = [ABSENT, 0, 1, -1, True, "x", 1.0]
    schemas = (SUPPORTED_SCHEMA, 99, None, ABSENT)
    return [
        {"read": r, "sw": sw, "cont": c, "idx": i, "schema": s}
        for r, sw, c, i, s in itertools.product(
            READ_OUTCOMES, schedules, containers, pointers, schemas)
    ]


def supersede_everything(state):
    """The same state with every record in the container marked superseded."""
    def walk(node, depth):
        if depth == 0:
            return {**node, SUPERSEDED_KEY: True} if is_record(node) else node
        if not isinstance(node, dict):
            return node
        return {k: walk(v, depth - 1) for k, v in node.items()}
    if state["cont"] is ABSENT:
        return state
    return {**state, "cont": walk(state["cont"], DEPTH)}


def main() -> int:
    """Properties that can fail.

    Deliberately NOT asserted here: that the verdict equals the conjunction it is
    written from. That comparison restates the function's own body inline and can
    never fail — the trap this repository has paid for before. The verdict's
    agreement with the SHIPPED predicate is falsifiable, and it is asserted in
    `packs/core/tests/skills/work-loop/test_repair_round_predicate_parity.py`,
    which drives both over this same domain. What is left here is what a
    transcription can honestly decide on its own.
    """
    domain = build_domain()
    reached = refused = unreached = 0
    moved = stayed = 0
    rows: dict[str, int] = {}
    cleared_by_supersede = 0

    for state in domain:
        row = wave_exit_row(state)
        rows[row] = rows.get(row, 0) + 1

        if not state["read"]:
            unreached += 1
            # P1. The read refusal is decided upstream, so the verdict is never
            # reached for such a state — the criterion the spec states separately.
            assert not repair_round_refuses(state), (
                "a state the reader refuses must never reach the verdict")
            continue

        reached += 1
        refuses = repair_round_refuses(state)
        refused += refuses

        # P2. A refusal names a real obligation: some task in the current wave
        # holds a record that still accounts. Independent of how the verdict is
        # written — it reads the container, not the predicate.
        if refuses:
            assert live_tasks(state), (
                f"refused a state with no live record: {state}")

        # P3. Round trip. Superseding every record must clear the refusal, and
        # must do so for every refusing state rather than for the ones an
        # example set happened to pick. This is the verb's contract, checked
        # against the guard's, and either one moving alone breaks it.
        after = supersede_everything(state)
        if refuses:
            assert not repair_round_refuses(after), (
                f"superseding failed to clear a refusal: {state}")
            cleared_by_supersede += 1
        else:
            assert not repair_round_refuses(after), (
                "superseding must never create a refusal")

        # P4. The row movement the superseded clause causes at the wave exit:
        # exactly R7 moves, and it moves to R8.
        before_row = wave_exit_row(state)
        after_row = wave_exit_row(after)
        if before_row == "R7-accounted":
            assert after_row == "R8-unaccounted", (
                f"superseding must move R7 to R8, got {after_row}")
            moved += 1
        else:
            assert after_row == before_row, (
                f"superseding moved {before_row} to {after_row}; only R7 may move")
            stayed += 1

    # P5. Domain adequacy. A walk whose domain exhibits only one side of a
    # predicate proves nothing about the other, so both sides are required to be
    # non-empty and every wave-exit row is required to be reached.
    assert refused, "no state in the domain refuses; the walk cannot fail"
    assert reached - refused, "no reached state passes; the walk cannot fail"
    assert cleared_by_supersede == refused, "P3 did not cover every refusal"
    for row in ("R1-read-refuses", "R2-schema-unsupported", "R3-malformed",
                "R4-container-absent", "R5-pointer-invalid", "R6-wave-malformed",
                "R7-accounted", "R8-unaccounted"):
        assert rows.get(row), f"no state reaches {row}; the domain is too narrow"

    print(f"states walked           : {len(domain)}")
    print(f"  verdict reached       : {reached}")
    print(f"  reader refused        : {unreached}")
    print(f"  verdict refuses       : {refused}")
    print(f"  refusals cleared      : {cleared_by_supersede}")
    print("wave-exit rows          :")
    for row in sorted(rows):
        print(f"    {row:<24} {rows[row]}")
    print(f"  R7 -> R8 on supersede : {moved}")
    print(f"  unmoved               : {stayed}")
    print("\nOK: read refusals never reach the verdict; every refusal names a live "
          "record and is cleared by superseding; only R7 moves, and it moves to R8.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
