#!/usr/bin/env python3
"""Walk `wave_accounting_summary` over a generated domain of cohort-state values.

The domain's axes are derived from the guard's own conjuncts and record
predicates, not from a list of interesting cases. Three successive hand-written
state lists each omitted a reachable input, so the walk proves its own coverage
instead of asserting it: it evaluates the record predicates over the values it
generated and requires each reachable combination to be COUNTED in a present
summary, and it requires every other axis value to reach the outcome it forces.

Coverage of predicate combinations is not coverage of predicate branches. Two
record values can share an outcome while taking different arms — a string reason
outside the closed set and an unhashable non-string reason both classify as "not
a record" — so the record axis carries one value per branch, and the unhashable
reason is what reaches the arm `is_dispatch_record` guards against raising on.

Run with pytest.
"""

from __future__ import annotations

import importlib.util
import itertools
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[3] / ".apm" / "skills" / "work-loop" / "scripts"
GUARDS = SCRIPTS / "_loop_guards.py"

ABSENT = object()


def load_guards(path: Path = GUARDS, name: str = "_loop_guards_walk"):
    """Load a copy of the module the way production does — unregistered, by path."""
    spec = importlib.util.spec_from_file_location(name, str(path))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def g():
    return load_guards()


def test_wave_accounting_summary_is_present_for_a_readable_wave(g) -> None:
    waves = [["T1", "T2"]]
    decline = {"kind": g.DECLINE_KIND, "reason": g.DECLINE_REASONS[0]}
    state = {
        "schema_version": g.SCHEMA_VERSION,
        "schedule_waves": waves,
        "current_wave_index": 0,
        g.RECEIPTS_KEY: {
            g.partition_digest(waves): {"0": {"T1": dict(decline),
                                              "T2": dict(decline)}},
        },
    }
    assert g.wave_accounting_summary(state, 0) is not None


# ── the generated domain ───────────────────────────────────────────────────
#
# One axis per thing the guard actually branches on. `schedule_waves` is its own
# axis because the wave axis varies only the value AT the index and can never
# reach the `isinstance(waves, list)` conjunct.

_LIVE_WAVES = [["T1", "T2"], ["T3"]]

# The domain's expected axis values, declared as literals INDEPENDENTLY of the
# generators below. The assertion compares the generators against this table, so
# deleting a value from a generator reddens instead of shrinking the expectation
# with it. An earlier version read its expectations from the generators and
# could not fail for 16 of 22 values.
_EXPECTED_AXIS_VALUES = {
    "schedule": ("list", "sized-non-list", "unsized-non-list"),
    "container": ("absent", "empty", "superseded-digest", "non-mapping",
                  "malformed-at-digest", "malformed-at-wave", "well-formed"),
    "wave": ("well-formed", "non-list", "empty", "non-string-element",
             "duplicated-identifier"),
    "record": ("live-receipt", "live-decline", "superseded-true",
               "superseded-not-true", "bad-reason-string",
               "bad-reason-unhashable", "not-a-record", "no-record"),
    "index": ("in-range-0", "in-range-1", "out-of-range"),
}

# Values whose presence must FORCE an absent summary. Hardcoded, not derived.
_FORCES_ABSENT = frozenset({
    ("schedule", "sized-non-list"), ("schedule", "unsized-non-list"),
    ("container", "absent"), ("wave", "non-list"), ("wave", "empty"),
    ("wave", "non-string-element"), ("index", "out-of-range"),
})


def _containers(g, waves, subtree_by_wave=None):
    """Container values, keyed by the declared path rather than a literal depth."""
    digest = g.partition_digest(waves)
    return {
        "absent": ABSENT,
        "empty": {},
        "superseded-digest": {"0" * 64: {"0": {"T1": {"kind": g.RECEIPT_KIND}}}},
        "non-mapping": 5,
        "malformed-at-digest": {digest: 5},
        "malformed-at-wave": {digest: {"0": 5}},
        "well-formed": {digest: dict(subtree_by_wave or {})},
    }


def _records(g):
    """One value per BRANCH of the two record predicates, not per outcome."""
    return {
        "live-receipt": {"kind": g.RECEIPT_KIND},
        "live-decline": {"kind": g.DECLINE_KIND, "reason": g.DECLINE_REASONS[0]},
        "superseded-true": {"kind": g.RECEIPT_KIND, g.SUPERSEDED_KEY: True},
        # Live: the declared check is `is not True`, not truthiness.
        "superseded-not-true": {"kind": g.RECEIPT_KIND, g.SUPERSEDED_KEY: "yes"},
        "bad-reason-string": {"kind": g.DECLINE_KIND, "reason": "not-in-set"},
        # Reaches the `isinstance(reason, str)` arm; `x in frozenset` would raise
        # on an unhashable value, which is why that guard exists.
        "bad-reason-unhashable": {"kind": g.DECLINE_KIND, "reason": ["nope"]},
        "not-a-record": 5,
        "no-record": ABSENT,
    }


def _schedules(g):
    """`schedule_waves` shapes. `list` is built per-case in `_domain`.

    A Sized non-list is absorbed by the range check, so only a NON-Sized value
    makes the `isinstance(waves, list)` conjunct load-bearing.
    """
    return {"list": None, "sized-non-list": "not-a-list", "unsized-non-list": 5}


def _indices(g):
    """Wave indices. `in-range-1` is what pins the container walk's wave key."""
    return {"in-range-0": 0, "in-range-1": 1, "out-of-range": 9}


def _waves_at_index(g):
    """One value per conjunct of `wave_is_well_formed`: list, non-empty, all str."""
    return {
        "well-formed": ["T1", "T2"],
        "non-list": "T1",
        "empty": [],
        "non-string-element": ["T1", 7],
        "duplicated-identifier": ["T1", "T1"],
    }


# Index 1's wave, and the records filed under it. Distinct from wave 0's in BOTH
# task names and record kind, so a summary that reads wave 0's subtree for index
# 1 reports different figures and the walk reddens. Without this the container
# walk's wave-index key is unpinned: replacing `str(wave_index)` with "0" left
# the whole suite green.
_WAVE_ONE = ["W1", "W2", "W3"]


def _domain(g):
    """Every axis combination, as (labels, state, index, read_at)."""
    schedules = _schedules(g)
    indices = _indices(g)
    out = []
    for sched, wave_label, cont_label, rec_label, idx_label in itertools.product(
        schedules, _waves_at_index(g), _EXPECTED_AXIS_VALUES["container"],
        _records(g), indices,
    ):
        wave = _waves_at_index(g)[wave_label]
        index = indices[idx_label]
        if sched != "list":
            # The wave axis does not vary here: `schedule_waves` is not a list,
            # so no wave value is ever reached.
            waves = schedules[sched]
            container = _containers(g, [])[cont_label]
        else:
            waves = [wave, _WAVE_ONE]
            # Wave 0 gets the record under test at its FIRST DISTINCT task, and
            # every other position a plain live receipt. Wave 1 gets all live
            # declines under its own task names. Placing at the first distinct
            # task stops a duplicated identifier from overwriting the record.
            sub0, placed = {}, False
            for task in wave if isinstance(wave, list) else []:
                if not isinstance(task, str):
                    continue
                if not placed:
                    value = _records(g)[rec_label]
                    if value is not ABSENT:
                        sub0[task] = value
                    placed = True
                elif task not in sub0:
                    sub0[task] = {"kind": g.RECEIPT_KIND}
            sub1 = {t: {"kind": g.DECLINE_KIND, "reason": g.DECLINE_REASONS[0]}
                    for t in _WAVE_ONE}
            container = _containers(g, waves, {"0": sub0, "1": sub1})[cont_label]
        state = {
            "schema_version": g.SCHEMA_VERSION,
            "schedule_waves": waves,
            "current_wave_index": 0,
        }
        if container is not ABSENT:
            state[g.RECEIPTS_KEY] = container
        labels = {"schedule": sched, "wave": wave_label, "container": cont_label,
                  "record": rec_label, "index": idx_label}
        # The record value the summary would actually read at this index, or
        # None when this state files no record under test. Credit is taken from
        # THIS, not from the label.
        read_at = None
        if sched == "list" and cont_label == "well-formed" and index == 0:
            held = container.get(g.partition_digest(waves), {}).get("0")
            if isinstance(held, dict) and isinstance(wave, list):
                for task in wave:
                    if isinstance(task, str):
                        read_at = held.get(task, ABSENT)
                        break
        out.append((labels, state, index, read_at))
    return out


# ── the assertions ─────────────────────────────────────────────────────────


def test_domain_is_non_empty_and_reaches_both_outcomes(g) -> None:
    """A vacuous domain would make every claim below true and prove nothing."""
    outcomes = {g.wave_accounting_summary(st, i) is not None
                for _, st, i, _ in _domain(g)}
    assert outcomes == {True, False}, f"both outcomes must be reached; got {outcomes}"


def test_no_generated_state_raises(g) -> None:
    for labels, state, index, _ in _domain(g):
        try:
            g.wave_accounting_summary(state, index)
        except Exception as exc:  # noqa: BLE001 — totality is the property
            raise AssertionError(f"{labels} raised {exc!r}") from exc


def test_summary_is_present_exactly_when_the_precondition_holds(g) -> None:
    """AC-0002's biconditional, over the whole domain."""
    for labels, state, index, _ in _domain(g):
        waves = state.get("schedule_waves")
        expected = (
            g.RECEIPTS_KEY in state
            and isinstance(waves, list)
            and 0 <= index < len(waves)
            and g.wave_is_well_formed(waves[index])
        )
        got = g.wave_accounting_summary(state, index) is not None
        assert got == expected, f"{labels}: present={got}, precondition={expected}"


def test_present_summaries_hold_the_arithmetic_invariant(g) -> None:
    """AC-0004, over every present summary the walk generates."""
    seen = 0
    for labels, state, index, _ in _domain(g):
        s = g.wave_accounting_summary(state, index)
        if s is None:
            continue
        seen += 1
        assert s["receipts"] + s["declines"] + s["unaccounted"] == s["tasks"], (
            f"{labels}: {s}")
    assert seen, "no present summary was generated"


def test_present_summaries_agree_with_the_guard_outstanding_count(g) -> None:
    """AC-0005, over every present summary the walk generates."""
    for labels, state, index, _ in _domain(g):
        s = g.wave_accounting_summary(state, index)
        if s is None:
            continue
        assert s["unaccounted"] == len(g.unaccounted_wave_tasks(state, index)), labels
        assert s["superseded"] == len(g.superseded_wave_tasks(state, index)), labels


def test_absent_summaries_coincide_with_nothing_outstanding(g) -> None:
    """The drift control: the helper must not call unreadable what the guard reads."""
    for labels, state, index, _ in _domain(g):
        if g.wave_accounting_summary(state, index) is not None:
            continue
        assert g.unaccounted_wave_tasks(state, index) == [], (
            f"{labels}: summary absent but the guard reports outstanding tasks")


def test_a_summary_reads_its_own_wave_not_wave_zero(g) -> None:
    """The container walk's wave-index key is load-bearing.

    Wave 1 carries different task names and a different record kind from wave 0,
    so a summary that descends to `"0"` for index 1 reports wave 0's figures.
    Without this the whole suite stayed green with `str(wave_index)` replaced by
    the literal `"0"`.
    """
    checked = 0
    for labels, state, index, _ in _domain(g):
        if index != 1:
            continue
        s = g.wave_accounting_summary(state, 1)
        if s is None:
            continue
        checked += 1
        assert s["tasks"] == len(_WAVE_ONE), (
            f"{labels}: index 1 reported {s['tasks']} tasks, wave 1 has "
            f"{len(_WAVE_ONE)} — the summary read another wave's subtree")
        if labels["container"] == "well-formed":
            assert s["declines"] == len(_WAVE_ONE) and s["receipts"] == 0, (
                f"{labels}: wave 1 is all declines; got {s}")
    assert checked, "no present summary at index 1 — the axis stopped generating"


def test_every_record_class_is_read_and_classified(g) -> None:
    """Coverage the walk proves rather than asserts.

    Credit comes from the record the summary would actually READ at that index —
    computed from the subtree the generator built — never from the axis label.
    An earlier version credited the label, so a wave that overwrote the record
    under test still counted it as covered.
    """
    counted = set()
    for labels, state, index, read_at in _domain(g):
        if read_at is None:
            continue
        if g.wave_accounting_summary(state, index) is None:
            continue
        expected = _records(g)[labels["record"]]
        if (read_at is ABSENT and expected is ABSENT) or read_at == expected:
            counted.add(labels["record"])
    missing = sorted(set(_EXPECTED_AXIS_VALUES["record"]) - counted)
    assert not missing, f"record classes never read by a present summary: {missing}"


def test_every_reachable_predicate_combination_is_counted(g) -> None:
    """Combination coverage, derived from the predicates rather than declared."""
    reachable = {(g.is_dispatch_record(v), g.accounts_for_task(v))
                 for v in _records(g).values() if v is not ABSENT}
    assert reachable == {(True, True), (True, False), (False, False)}, (
        f"the record axis no longer reaches every combination: {sorted(reachable)}")


def test_the_generators_match_the_declared_axis_values(g) -> None:
    """The expectation is a literal table, not a read of the generator.

    Deleting a value from any of the five generators must redden here. An
    earlier version compared three generators against themselves and drove the
    other two straight off this table, so the table was both generator and
    expectation for them and their values were silently deletable.
    """
    actual = {
        "schedule": tuple(_schedules(g)),
        "container": tuple(_containers(g, _LIVE_WAVES)),
        "wave": tuple(_waves_at_index(g)),
        "record": tuple(_records(g)),
        "index": tuple(_indices(g)),
    }
    for axis, values in actual.items():
        assert set(values) == set(_EXPECTED_AXIS_VALUES[axis]), (
            f"{axis} generator no longer matches the declared domain: "
            f"missing {sorted(set(_EXPECTED_AXIS_VALUES[axis]) - set(values))}, "
            f"unexpected {sorted(set(values) - set(_EXPECTED_AXIS_VALUES[axis]))}")


def test_every_axis_value_reaches_the_outcome_it_forces(g) -> None:
    """Per axis VALUE, against the literal table above."""
    seen_any, seen_absent = set(), set()
    for labels, state, index, _ in _domain(g):
        absent = g.wave_accounting_summary(state, index) is None
        for axis, value in labels.items():
            seen_any.add((axis, value))
            if absent:
                seen_absent.add((axis, value))
    for axis, values in _EXPECTED_AXIS_VALUES.items():
        for value in values:
            assert (axis, value) in seen_any, f"axis value never generated: {axis}={value}"
    missing = sorted(_FORCES_ABSENT - seen_absent)
    assert not missing, f"values that force an absent summary never did: {missing}"


# ── named cases: the figures the walk does not pin ─────────────────────────
#
# The walk proves the partition and the invariants hold; it never proves any
# particular state reports the numbers a reader expects. These do.


def _state(g, waves, subtree):
    return {
        "schema_version": g.SCHEMA_VERSION,
        "schedule_waves": waves,
        "current_wave_index": 0,
        g.RECEIPTS_KEY: {g.partition_digest(waves): {"0": subtree}},
    }


def test_all_receipt_and_all_decline_waves_report_different_figures(g) -> None:
    """AC-0001 and the differential this defect is about, at the helper."""
    waves = [["T1", "T2"]]
    receipt = _state(g, waves, {t: {"kind": g.RECEIPT_KIND} for t in ("T1", "T2")})
    decline = _state(g, waves, {t: {"kind": g.DECLINE_KIND,
                                    "reason": g.DECLINE_REASONS[0]}
                                for t in ("T1", "T2")})
    rs = g.wave_accounting_summary(receipt, 0)
    ds = g.wave_accounting_summary(decline, 0)
    assert set(rs) == {"tasks", "receipts", "declines", "superseded", "unaccounted"}
    assert rs == {"tasks": 2, "receipts": 2, "declines": 0,
                  "superseded": 0, "unaccounted": 0}
    assert ds == {"tasks": 2, "receipts": 0, "declines": 2,
                  "superseded": 0, "unaccounted": 0}
    assert rs != ds, "an all-declined wave must not read as an implemented one"


def test_a_superseded_record_counts_as_superseded_and_unaccounted(g) -> None:
    """AC-0006: toward both, and toward neither receipts nor declines."""
    waves = [["T1"]]
    state = _state(g, waves, {"T1": {"kind": g.RECEIPT_KIND, g.SUPERSEDED_KEY: True}})
    assert g.wave_accounting_summary(state, 0) == {
        "tasks": 1, "receipts": 0, "declines": 0, "superseded": 1, "unaccounted": 1}


def test_counting_is_positional_not_key_based(g) -> None:
    """AC-0003: a duplicated identifier counts twice; an out-of-wave key counts
    for nothing."""
    dup = [["T1", "T1"]]
    state = _state(g, dup, {"T1": {"kind": g.RECEIPT_KIND}})
    assert g.wave_accounting_summary(state, 0) == {
        "tasks": 2, "receipts": 2, "declines": 0, "superseded": 0, "unaccounted": 0}

    waves = [["T1"]]
    extra = _state(g, waves, {"T1": {"kind": g.RECEIPT_KIND},
                              "T9": {"kind": g.RECEIPT_KIND}})
    plain = _state(g, waves, {"T1": {"kind": g.RECEIPT_KIND}})
    assert g.wave_accounting_summary(extra, 0) == g.wave_accounting_summary(plain, 0)


def test_unreadable_records_degrade_at_the_scope_they_occupy(g) -> None:
    """AC-0007: a non-mapping subtree loses the whole wave; a bad value at one
    key of an otherwise live subtree loses only that task."""
    waves = [["T1", "T2"]]
    whole = {"schema_version": g.SCHEMA_VERSION, "schedule_waves": waves,
             "current_wave_index": 0,
             g.RECEIPTS_KEY: {g.partition_digest(waves): {"0": 5}}}
    assert g.wave_accounting_summary(whole, 0) == {
        "tasks": 2, "receipts": 0, "declines": 0, "superseded": 0, "unaccounted": 2}

    one = _state(g, waves, {"T1": {"kind": g.RECEIPT_KIND}, "T2": 5})
    assert g.wave_accounting_summary(one, 0) == {
        "tasks": 2, "receipts": 1, "declines": 0, "superseded": 0, "unaccounted": 1}


def test_a_non_true_superseded_value_stays_live(g) -> None:
    """`accounts_for_task` tests `is not True`, not truthiness.

    The expected figures below are LITERALS. Every other oracle in this file
    routes through `accounts_for_task`, so a truthiness rewrite of that
    declaration moves both sides of those comparisons together and they stay
    green; only an independently written expectation can fail. A truthy read
    would report this record as superseded and unaccounted instead of live.
    """
    waves = [["T1"]]
    state = _state(g, waves, {"T1": {"kind": g.RECEIPT_KIND, g.SUPERSEDED_KEY: "yes"}})
    assert g.wave_accounting_summary(state, 0) == {
        "tasks": 1, "receipts": 1, "declines": 0, "superseded": 0, "unaccounted": 0}
