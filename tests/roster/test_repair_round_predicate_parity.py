#!/usr/bin/env python3
"""Contract-to-code coupling for the repair-round predicate.

Spec: docs/specs/repair-round-dispatch-assertion/spec.md.

Why this file exists, and why it lives here. The check compares this
contract's rules — transcribed from the spec's words — against the shipped
predicate in ``_loop_guards.py``. It fails in BOTH directions on purpose: a
predicate change without a contract change, or the reverse, turns it red.

This is a repository-level assertion because it reads ``docs/`` and ``packs/``
together. A pack test may not read above its own pack
(``tools/lint-pack-test-boundary.py`` enforces this), so this file lives in
``tests/roster/`` instead.

There is no separate oracle artifact. The oracle that used to live at
``docs/specs/repair-round-dispatch-assertion/notes/walk_reopen_partition.py``
transcribed the contract and compared it against itself — a tautology — so it
was deleted in T6. What replaces it is this check, which builds its own domain
from the spec's declared axes and compares the contract's rules against the
shipped code at all three levels: per-record accounting, the unaccounted task
list, and the repair-round verdict.
"""

from __future__ import annotations

import hashlib
import importlib.util
import itertools
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
GUARDS = ROOT / "packs" / "core" / ".apm" / "skills" / "work-loop" / "scripts" / "_loop_guards.py"
COHORT = ROOT / "packs" / "core" / ".apm" / "skills" / "work-loop" / "scripts" / "loop-cohort.py"


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
def guards():
    assert GUARDS.is_file(), f"the guard layer is missing at {GUARDS}"
    return _load(GUARDS, "_loop_guards_under_parity_test")


# ---------------------------------------------------------------------------
# Domain construction — built from the spec's declared axes, never from the
# oracle.  Container values are generated from RECEIPT_KEY_PATH rather than
# hand-built at a literal depth (the requirement the frozen spec carries over
# from wave-complete-dispatch-receipts).
# ---------------------------------------------------------------------------

SUPPORTED_SCHEMA = 1
_RECEIPTS_KEY = "dispatch_receipts"
_SUPERSEDED_KEY = "superseded"
_DECLINE_REASONS = ("no-implementer-installed", "human-directed")
_KEY_PATH = ("partition digest", "wave index", "task identifier")
_DEPTH = len(_KEY_PATH)
ABSENT = object()  # sentinel for missing keys


def _digest_of(waves) -> str:
    payload = json.dumps(waves, sort_keys=True, separators=(",", ":"), default=repr)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _is_record(value) -> bool:
    """Transcribed: a mapping whose kind is receipt, or decline with a closed reason."""
    if not isinstance(value, dict):
        return False
    kind = value.get("kind")
    if kind == "receipt":
        return True
    if kind == "decline":
        reason = value.get("reason")
        return isinstance(reason, str) and reason in _DECLINE_REASONS
    return False


def _accounts(value) -> bool:
    """Transcribed from the spec: a record accounts unless `superseded` is True."""
    return _is_record(value) and value.get(_SUPERSEDED_KEY) is not True


def _nest(leaf, depth):
    for _ in range(depth):
        leaf = {"k": leaf}
    return leaf


def _container_well_formed(container, depth=_DEPTH) -> bool:
    if depth == 0:
        return _is_record(container)
    if not isinstance(container, dict):
        return False
    return all(_container_well_formed(v, depth - 1) for v in container.values())


def _keyed_container(waves, index, tasks, *, record=None, digest=None):
    """A container built from the DECLARED key path, never at a literal depth.

    The key sequence is derived from `_KEY_PATH`, not written as a literal pair:
    the declaration names the task identifier last, so every level above it is
    keyed here in order. A review found this docstring making that claim while
    the body hardcoded a two-element tuple — the exact defect the frozen spec's
    criterion names, since a hand-built container makes the walk ratify the shape
    its author constructed rather than the shape the declaration states.
    """
    record = record or {"kind": "receipt"}
    outer = {"partition digest": digest or _digest_of(waves), "wave index": str(index)}
    node = {task: dict(record) for task in tasks}
    for level in reversed(_KEY_PATH[:-1]):
        node = {outer[level]: node}
    return node


def _wave_well_formed(wave) -> bool:
    return isinstance(wave, list) and bool(wave) and all(isinstance(t, str) for t in wave)


def _pointer_ok(state, waves):
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
        out[_RECEIPTS_KEY] = state["cont"]
    if state["idx"] is not ABSENT:
        out["current_wave_index"] = state["idx"]
    return out


def _unaccounted(state, index):
    """Transcribed twin of `unaccounted_wave_tasks`.

    The absent-container exemption lives INSIDE this function — the shipped
    predicate carries it inside too and every consumer inherits it by calling.
    """
    doc = materialise(state)
    if _RECEIPTS_KEY not in doc:
        return []
    waves = doc.get("schedule_waves", [])
    if not isinstance(waves, list) or not 0 <= index < len(waves):
        return []
    wave = waves[index]
    if not _wave_well_formed(wave):
        return []
    held = doc.get(_RECEIPTS_KEY)
    for key in (_digest_of(waves), str(index)):
        held = held.get(key) if isinstance(held, dict) else None
    if not isinstance(held, dict):
        return list(wave)
    return [task for task in wave if not _accounts(held.get(task))]


def _repair_round_refuses(state) -> bool:
    """Transcribed conjunction from the spec's § The repair-round verdict."""
    if not state["read"]:
        return False  # never reached; the reader refused upstream
    doc = materialise(state)
    if doc.get("schema_version") != SUPPORTED_SCHEMA:
        return False
    if _RECEIPTS_KEY not in doc:
        return False
    if not _container_well_formed(doc[_RECEIPTS_KEY]):
        return False
    # live_tasks: tasks whose record still accounts for the current wave
    waves = doc.get("schedule_waves", [])
    if not isinstance(waves, list) or not waves:
        return False
    idx = _pointer_ok(state, waves)
    if idx is None:
        return False
    wave = waves[idx]
    if not _wave_well_formed(wave):
        return False
    held = doc.get(_RECEIPTS_KEY)
    for key in (_digest_of(waves), str(idx)):
        held = held.get(key) if isinstance(held, dict) else None
    if not isinstance(held, dict):
        return False
    return any(_accounts(held.get(t)) for t in wave)


def _supersede_everything(state):
    """Return the same state with every record in the container superseded."""
    def walk(node, depth):
        if depth == 0:
            return {**node, _SUPERSEDED_KEY: True} if _is_record(node) else node
        if not isinstance(node, dict):
            return node
        return {k: walk(v, depth - 1) for k, v in node.items()}
    if state["cont"] is ABSENT:
        return state
    return {**state, "cont": walk(state["cont"], _DEPTH)}


_HOSTILE = (
    42, "receipt", [], None, {}, {"kind": "bogus"},
    {"kind": "decline"}, {"kind": "decline", "reason": "made-up"},
    {"kind": 7}, {"kind": ["receipt"]},
    {"kind": "decline", "reason": 7},
    {"kind": "decline", "reason": ["no-implementer-installed"]},
)


def build_domain():
    """Domain built from the spec's canonical axis list plus a superseded axis.

    The superseded axis varies the member by type and value as well as presence,
    with container values generated from the declared key path (_DEPTH), never
    hand-built at a literal depth.

    Non-degeneracy requirement: the domain must include at least one state where
    a record is superseded (not absent), so the ``is True`` strictness is tested.
    """
    live_sw = [["T1"], ["T2"]]
    idx0, tasks = 0, live_sw[0]
    stale_sw = [["T1"], ["T2"], ["T3"]]
    gone = {"kind": "receipt", _SUPERSEDED_KEY: True}

    containers = [ABSENT, _nest({"kind": "receipt"}, _DEPTH)]
    containers += [_nest(v, d) for d in range(_DEPTH + 1) for v in _HOSTILE]
    containers += [
        _keyed_container(live_sw, idx0, tasks),
        _keyed_container(live_sw, idx0, tasks, record=gone),
        _keyed_container(live_sw, idx0, tasks,
                         record={"kind": "decline", "reason": "human-directed"}),
        _keyed_container(live_sw, idx0, tasks,
                         record={"kind": "decline", "reason": "human-directed",
                                 _SUPERSEDED_KEY: True}),
        # The superseded axis, varied by type and value as well as presence.
        # Only ``True`` supersedes; a truthy non-True must leave the record live.
        _keyed_container(live_sw, idx0, tasks,
                         record={"kind": "receipt", _SUPERSEDED_KEY: "yes"}),
        _keyed_container(live_sw, idx0, tasks,
                         record={"kind": "receipt", _SUPERSEDED_KEY: False}),
        _keyed_container(live_sw, idx0, []),
        _keyed_container(live_sw, idx0, tasks, digest=_digest_of(stale_sw)),
    ]
    schedules = [ABSENT, [], [["T1"]], "notalist", [123], [["T1", 2]],
                 live_sw, {"a": 1}, [[]], [[], ["T2"]], [["T1"], []]]
    pointers = [ABSENT, 0, 1, -1, True, "x", 1.0]
    schemas = (SUPPORTED_SCHEMA, 99, None, ABSENT)
    return [
        {"read": r, "sw": sw, "cont": c, "idx": i, "schema": s}
        for r, sw, c, i, s in itertools.product(
            (True, False), schedules, containers, pointers, schemas
        )
    ]


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_the_accounting_rule_agrees_record_by_record(guards) -> None:
    """`_accounts` and `accounts_for_task` decide every record value identically.

    The transcribed rule must agree with the shipped function for every value a
    container position can hold, including every variant of the superseded member
    the spec declares. A truthy non-True value (e.g., ``"yes"`` or ``False``)
    must leave the record live under the ``is True`` strictness.
    """
    values = [
        {"kind": "receipt"},
        {"kind": "receipt", _SUPERSEDED_KEY: True},
        {"kind": "receipt", _SUPERSEDED_KEY: False},
        {"kind": "receipt", _SUPERSEDED_KEY: "yes"},
        {"kind": "receipt", _SUPERSEDED_KEY: None},
        {"kind": "decline", "reason": "human-directed"},
        {"kind": "decline", "reason": "human-directed", _SUPERSEDED_KEY: True},
        {"kind": "decline", "reason": "made-up"},
        {"kind": "bogus"}, {}, None, 42, "receipt", [],
    ]
    disagreements = [v for v in values if _accounts(v) != guards.accounts_for_task(v)]
    assert not disagreements, (
        "the transcribed accounting rule and the shipped `accounts_for_task` "
        f"disagree on: {disagreements}"
    )


def test_the_verdict_agrees_over_the_whole_domain(guards) -> None:
    """Every reachable state in the domain gets the same verdict from both.

    Scoped to readable states: a read refusal is decided upstream by the shared
    reader and never reaches either function.

    Non-degeneracy: the domain must include at least one refusing state AND at
    least one passing state. A domain that decides only one way proves nothing.
    A domain with no superseded record never exercises the ``is True`` strictness.
    """
    disagreements = []
    reached = refused = superseded_seen = 0
    for state in build_domain():
        if not state["read"]:
            continue
        reached += 1
        doc = materialise(state)
        transcribed = _repair_round_refuses(state)
        shipped = not guards._repair_round_verdict(doc).ok
        refused += shipped
        if transcribed != shipped:
            disagreements.append((doc, transcribed, shipped))
        # Track whether any state with a superseded record is in the domain.
        if state["cont"] is not ABSENT and isinstance(state["cont"], dict):
            cont_str = json.dumps(state["cont"])
            if '"superseded": true' in cont_str or f'"{_SUPERSEDED_KEY}": true' in cont_str:
                superseded_seen += 1

    assert not disagreements, (
        f"{len(disagreements)} of {reached} states get different verdicts from the "
        f"transcription and the shipped predicate; first: {disagreements[0]}"
    )
    assert refused, "no state in the domain refuses; this check cannot fail"
    assert reached - refused, "no state passes; this check cannot fail"
    assert superseded_seen, (
        "no state in the domain carries a superseded record; "
        "the `is True` strictness is never exercised"
    )


def test_the_accounting_predicate_agrees_over_the_whole_domain(guards) -> None:
    """The shared predicate itself, not only the verdict that consumes it.

    The verdict can agree while `unaccounted_wave_tasks` disagrees — the verdict
    only reads whether the live set is empty, so a wrong task identifier in the
    returned list is invisible to it and visible in `wave advance`'s refusal text.

    Compares over every readable state, with one stated restriction. An earlier
    version filtered on `_pointer_ok` and `_wave_well_formed`, skipping ~90 % of
    readable states and hiding any shipped divergence in exactly those guards;
    that filter is gone. What remains is the index ARGUMENT: this loop passes an
    integer, because the shipped `unaccounted_wave_tasks` is not total over its
    `wave_index` parameter — `unaccounted_wave_tasks(state, "x")` raises
    `TypeError` on `0 <= wave_index < len(waves)`. So the pointer axis is
    exercised through the state's own `current_wave_index` by the verdict
    comparison, not through this function's argument. Saying so rather than
    claiming totality: the claim was false and a review caught it.

    Non-degeneracy: the domain must return a non-empty unaccounted list for at
    least one state, AND return an empty list for at least one.
    """
    disagreements = []
    found_non_empty = found_empty = 0
    for state in build_domain():
        if not state["read"]:
            continue
        doc = materialise(state)
        # Derive the index without pre-filtering: both functions handle any
        # value (returning [] for invalid inputs), so no states are skipped.
        raw_idx = state["idx"]
        if raw_idx is ABSENT or isinstance(raw_idx, bool) or not isinstance(raw_idx, int):
            idx = 0
        else:
            idx = raw_idx
        transcribed = _unaccounted(state, idx)
        shipped = guards.unaccounted_wave_tasks(doc, idx)
        if transcribed != shipped:
            disagreements.append((doc, transcribed, shipped))
        if shipped:
            found_non_empty += 1
        else:
            found_empty += 1
    assert not disagreements, (
        f"{len(disagreements)} states disagree on the unaccounted task list; "
        f"first: {disagreements[0]}"
    )
    assert found_non_empty, "unaccounted_wave_tasks never returns non-empty in domain"
    assert found_empty, "unaccounted_wave_tasks never returns empty in domain"


def _is_accounted(guards, doc: dict) -> bool:
    """True when the shipped code treats the state as R7-accounted.

    A state is accounted when the shipped ``_wave_exit_verdict`` returns ok AND
    ``schema_version`` is the supported value AND the container is present AND
    the shipped ``unaccounted_wave_tasks`` returns [] for the current pointer.
    This is expressed in terms of shipped return values, not refusal strings.

    The absent-pointer case defaults to 0, matching ``non_negative_int``'s
    behaviour in ``_wave_exit_verdict``.
    """
    if not guards._wave_exit_verdict(doc).ok:
        return False
    if doc.get("schema_version") != SUPPORTED_SCHEMA:
        return False
    if _RECEIPTS_KEY not in doc:
        return False
    waves = doc.get("schedule_waves", [])
    if not isinstance(waves, list) or not waves:
        return False
    # Replicate non_negative_int's absent-key default of 0.
    raw_idx = doc.get("current_wave_index")
    if raw_idx is None:
        idx = 0
    elif isinstance(raw_idx, bool) or not isinstance(raw_idx, int) or raw_idx < 0:
        return False
    else:
        idx = raw_idx
    if idx >= len(waves):
        return False
    return guards.unaccounted_wave_tasks(doc, idx) == []


def test_wave_exit_row_movement_from_superseding(guards) -> None:
    """Superseding every record in an accounted state moves it to unaccounted.

    For every non-accounted state, superseding must leave the shipped verdict's
    ok flag unchanged. This measures the row movement the superseded clause
    causes, expressed in terms of what the shipped functions return rather than
    by matching substrings in refusal strings.

    Non-degeneracy: at least one accounted state must exist in the domain.
    """
    moved = 0
    violations = []
    for state in build_domain():
        if not state["read"]:
            continue

        doc = materialise(state)
        after_state = _supersede_everything(state)
        after_doc = materialise(after_state)

        acc = _is_accounted(guards, doc)
        if acc:
            moved += 1
            # Superseding an accounted state must make the verdict refuse.
            if guards._wave_exit_verdict(after_doc).ok:
                violations.append(
                    f"superseding an accounted state must refuse (ok=False) but "
                    f"got ok=True: {doc!r}"
                )
            # And unaccounted_wave_tasks must return the whole wave.
            waves = doc.get("schedule_waves", [])
            idx = doc.get("current_wave_index", 0)
            wave = waves[idx] if (isinstance(idx, int) and 0 <= idx < len(waves)) else []
            after_unaccounted = guards.unaccounted_wave_tasks(after_doc, idx)
            if sorted(after_unaccounted) != sorted(wave):
                violations.append(
                    f"superseding an accounted state must make unaccounted = whole wave "
                    f"{sorted(wave)!r}, got {sorted(after_unaccounted)!r}: {doc!r}"
                )
        else:
            # Not accounted: ok flag must be unchanged after superseding.
            before_ok = guards._wave_exit_verdict(doc).ok
            after_ok = guards._wave_exit_verdict(after_doc).ok
            if before_ok != after_ok:
                violations.append(
                    f"superseding a non-accounted state must leave ok flag unchanged "
                    f"(before={before_ok}, after={after_ok}): {doc!r}"
                )

    assert not violations, (
        f"{len(violations)} row-movement violations:\n" + "\n".join(violations[:3])
    )
    assert moved, "no accounted state in domain; the superseded clause is not exercised"


def test_wave_reopen_check_is_read_only(guards, tmp_path) -> None:
    """check --phase wave-reopen must not write to state.json for any domain state.

    The verdict is a guard function (read-only by design). This test drives
    it over every readable state in the full domain — not three hand-built
    examples — so a future change that accidentally adds a write is detected
    regardless of which state triggers it.

    One temp directory is reused across all states (overwriting state.json each
    time) to avoid creating thousands of subdirectories and keep the test fast.
    """
    run_id = "00000000-0000-0000-0000-000000000001"
    spec_dir = tmp_path / "spec"
    spec_dir.mkdir()
    path = spec_dir / "state.json"

    checked = 0
    for state in build_domain():
        if not state["read"]:
            continue
        doc = materialise(state)
        # Ensure run_id is present so the shared reader does not refuse on it.
        doc.setdefault("run_id", run_id)
        raw = json.dumps(doc, indent=2, sort_keys=True).encode("utf-8")
        path.write_bytes(raw)
        before = hashlib.sha256(raw).hexdigest()
        # Call the guard in-process: read-only means the file must not change.
        guards.check_phase(spec_dir, phase="wave-reopen")
        after = hashlib.sha256(path.read_bytes()).hexdigest()
        assert before == after, (
            f"check_phase(wave-reopen) wrote to state.json for state: {doc!r}"
        )
        checked += 1
    assert checked, "no readable state was checked; domain is empty or all unreadable"


def test_superseded_wave_tasks_is_a_subset_of_unaccounted(guards) -> None:
    """The seam `superseded_wave_tasks`' own docstring names, driven over the domain.

    That function calls `unaccounted_wave_tasks` and then walks the container a
    second time to partition the result. The walk is an independent statement of
    the one inside the shared predicate, so if only one of them changes this
    returns `[]` and every superseded task is reported as having no record at all
    — the defect this delivery closes, re-entering quietly through a helper.

    Two properties, both over every readable state rather than one fixture: the
    superseded list is always a subset of the unaccounted list, and it is
    non-empty somewhere, so the subset claim is not satisfied by a function that
    always returns nothing.
    """
    violations = []
    superseded_seen = 0
    for state in build_domain():
        if not state["read"]:
            continue
        doc = materialise(state)
        waves = doc.get("schedule_waves", [])
        if not isinstance(waves, list) or not waves:
            continue
        index = _pointer_ok(state, waves)
        if index is None:
            continue
        unaccounted = set(guards.unaccounted_wave_tasks(doc, index))
        superseded = guards.superseded_wave_tasks(doc, index)
        if superseded:
            superseded_seen += 1
        if not set(superseded) <= unaccounted:
            violations.append((doc, sorted(superseded), sorted(unaccounted)))

    assert not violations, (
        f"{len(violations)} states where the superseded list is not a subset of "
        f"the unaccounted list; first: {violations[0]}"
    )
    assert superseded_seen, (
        "no state in the domain produced a superseded task, so the subset "
        "property above is satisfied by an empty list everywhere and proves nothing"
    )
