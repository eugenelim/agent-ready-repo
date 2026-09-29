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


def _containers(g, waves):
    """Container values, keyed by the declared path rather than a literal depth."""
    digest = g.partition_digest(waves)

    def keyed(subtree):
        return {digest: {"0": subtree}}
    return {
        "absent": ABSENT,
        "empty": {},
        "superseded-digest": {"0" * 64: {"0": {"T1": {"kind": g.RECEIPT_KIND}}}},
        "non-mapping": 5,
        "malformed-at-digest": {digest: 5},
        "malformed-at-wave": keyed(5),
        "well-formed": keyed({}),
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


def _waves_at_index(g):
    """One value per conjunct of `wave_is_well_formed`: list, non-empty, all str."""
    return {
        "well-formed": ["T1", "T2"],
        "non-list": "T1",
        "empty": [],
        "non-string-element": ["T1", 7],
        "duplicated-identifier": ["T1", "T1"],
    }


def _domain(g):
    """Every axis combination, as (labels, state)."""
    schedule_axis = {"list": "list", "non-list": "non-list"}
    index_axis = {"in-range": 0, "out-of-range": 9}
    out = []
    for sched, wave_label, cont_label, rec_label, idx_label in itertools.product(
        schedule_axis, _waves_at_index(g), _containers(g, _LIVE_WAVES),
        _records(g), index_axis,
    ):
        wave = _waves_at_index(g)[wave_label]
        waves = wave if sched == "non-list" else [wave, ["T3"]]
        if sched == "non-list":
            waves = "not-a-list"
        container = _containers(g, waves if isinstance(waves, list) else [])[cont_label]
        record = _records(g)[rec_label]
        # Place the record at the wave's own first position so it is reachable
        # when the container and wave are both well-formed.
        if cont_label == "well-formed" and isinstance(waves, list) and isinstance(wave, list):
            subtree = {}
            for pos, task in enumerate(wave):
                if not isinstance(task, str):
                    continue
                value = record if pos == 0 else {"kind": g.RECEIPT_KIND}
                if value is not ABSENT:
                    subtree[task] = value
            container = {g.partition_digest(waves): {"0": subtree}}
        state = {
            "schema_version": g.SCHEMA_VERSION,
            "schedule_waves": waves,
            "current_wave_index": 0,
        }
        if container is not ABSENT:
            state[g.RECEIPTS_KEY] = container
        out.append(
            ({"schedule": sched, "wave": wave_label, "container": cont_label,
              "record": rec_label, "index": idx_label}, state,
             index_axis[idx_label]))
    return out


# ── the assertions ─────────────────────────────────────────────────────────


def test_domain_is_non_empty_and_reaches_both_outcomes(g) -> None:
    """A vacuous domain would make every claim below true and prove nothing."""
    outcomes = {s is not None
                for _, st, i in _domain(g)
                for s in (g.wave_accounting_summary(st, i),)}
    assert outcomes == {True, False}, f"both outcomes must be reached; got {outcomes}"


def test_no_generated_state_raises(g) -> None:
    for labels, state, index in _domain(g):
        try:
            g.wave_accounting_summary(state, index)
        except Exception as exc:  # noqa: BLE001 — totality is the property
            raise AssertionError(f"{labels} raised {exc!r}") from exc


def test_summary_is_present_exactly_when_the_precondition_holds(g) -> None:
    """AC-0002's biconditional, over the whole domain."""
    for labels, state, index in _domain(g):
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
    for labels, state, index in _domain(g):
        s = g.wave_accounting_summary(state, index)
        if s is None:
            continue
        seen += 1
        assert s["receipts"] + s["declines"] + s["unaccounted"] == s["tasks"], (
            f"{labels}: {s}")
    assert seen, "no present summary was generated"


def test_present_summaries_agree_with_the_guard_outstanding_count(g) -> None:
    """AC-0005, over every present summary the walk generates."""
    for labels, state, index in _domain(g):
        s = g.wave_accounting_summary(state, index)
        if s is None:
            continue
        assert s["unaccounted"] == len(g.unaccounted_wave_tasks(state, index)), labels
        assert s["superseded"] == len(g.superseded_wave_tasks(state, index)), labels


def test_absent_summaries_coincide_with_nothing_outstanding(g) -> None:
    """The drift control: the helper must not call unreadable what the guard reads."""
    for labels, state, index in _domain(g):
        if g.wave_accounting_summary(state, index) is not None:
            continue
        assert g.unaccounted_wave_tasks(state, index) == [], (
            f"{labels}: summary absent but the guard reports outstanding tasks")


def test_every_record_class_is_counted_in_some_present_summary(g) -> None:
    """Coverage the walk proves rather than asserts.

    Requires each record value to be COUNTED — read through a mapping subtree and
    classified — not merely to appear in a state whose summary is present. An
    empty, superseded-digest or non-mapping container yields a present summary in
    which no record is read at all, so appearing only there would leave the value
    unclassified and AC-0004/AC-0005 vacuous for it.
    """
    counted = set()
    for labels, state, index in _domain(g):
        if labels["container"] != "well-formed" or labels["wave"] == "empty":
            continue
        if g.wave_accounting_summary(state, index) is None:
            continue
        counted.add(labels["record"])
    missing = sorted(set(_records(g)) - counted)
    assert not missing, f"record classes never counted in a present summary: {missing}"


def test_every_reachable_predicate_combination_is_counted(g) -> None:
    """Combination coverage, derived from the predicates rather than declared."""
    reachable = {(g.is_dispatch_record(v), g.accounts_for_task(v))
                 for v in _records(g).values() if v is not ABSENT}
    assert reachable == {(True, True), (True, False), (False, False)}, (
        f"the record axis no longer reaches every combination: {sorted(reachable)}")


def test_every_axis_value_reaches_the_outcome_it_forces(g) -> None:
    """Per axis VALUE, not per axis: an axis that drops all but one value passes
    a per-axis check unchanged."""
    forces_absent = {
        ("schedule", "non-list"), ("container", "absent"), ("wave", "non-list"),
        ("wave", "empty"), ("wave", "non-string-element"),
        ("index", "out-of-range"),
    }
    seen_absent, seen_any = set(), set()
    for labels, state, index in _domain(g):
        absent = g.wave_accounting_summary(state, index) is None
        for axis, value in labels.items():
            seen_any.add((axis, value))
            if absent:
                seen_absent.add((axis, value))
    for axis, values in (("schedule", ("list", "non-list")),
                         ("container", tuple(_containers(g, _LIVE_WAVES))),
                         ("wave", tuple(_waves_at_index(g))),
                         ("record", tuple(_records(g))),
                         ("index", ("in-range", "out-of-range"))):
        for value in values:
            assert (axis, value) in seen_any, f"axis value never generated: {axis}={value}"
    missing = sorted(forces_absent - seen_absent)
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
