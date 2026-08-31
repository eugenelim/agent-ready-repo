"""Runtime capability-claim lifecycle: state resolution, roll-up, and the ledger.

The state function and the roll-up are pure over supplied values. No assertion
here reads the wall clock: a suite that did would redden unrelated work roughly
ninety days after the last verification, which is a failure mode this repository
already carries elsewhere.
"""

import copy
import json
from datetime import date
from pathlib import Path

import pytest

PACK = Path(__file__).resolve().parents[2]
LEDGER = PACK / "tests" / "fixtures" / "runtime-capability-ledger.json"

# Transcribed from RFC-0097 D3's profile table. Held as module literals rather
# than read from the fixture, so editing the fixture's own transcription cannot
# also move the standard it is checked against.
REQUIRED_SOURCE_REF = "docs/rfc/0097-agent-skill-engineering.md:D3"
REQUIRED_COUNT = 7

STATES = ("verified", "experimental", "stale", "unavailable")
ROLL_UPS = ("complete-current", "needs-revalidation", "incomplete")
MAXIMUM_WINDOW_DAYS = 90


class LedgerError(ValueError):
    """Carries a stable diagnostic code so a rejection names its own reason."""

    def __init__(self, code: str, detail: str = "") -> None:
        super().__init__(f"{code}: {detail}" if detail else code)
        self.code = code


def _parse_date(value: object, field: str) -> date:
    if not isinstance(value, str):
        raise LedgerError("malformed_date", field)
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise LedgerError("malformed_date", f"{field}={value!r}") from exc


def validate_row(row: dict) -> None:
    """Reject a row that cannot be honestly classified, naming the reason."""
    sources = row.get("sources")
    if not isinstance(sources, list) or not sources:
        raise LedgerError("empty_sources", row.get("capability", "<unnamed>"))
    for source in sources:
        url = source.get("url", "")
        if not isinstance(url, str) or not url.startswith(("http://", "https://")):
            raise LedgerError("relative_or_internal_url", url)
        if not source.get("title"):
            raise LedgerError("missing_source_title", url)
        if not source.get("source_version"):
            raise LedgerError("missing_source_version", url)
        _parse_date(source.get("retrieved_at"), "retrieved_at")
    for field in ("scope", "surface", "os", "revalidation_trigger"):
        if not row.get(field):
            raise LedgerError("missing_provenance_field", field)
    last_verified = _parse_date(row.get("last_verified"), "last_verified")
    if last_verified > window_base(row):
        raise LedgerError("verification_ahead_of_retrieval", row["capability"])
    probe = row.get("probe")
    if probe is not None:
        if not probe.get("gesture") or not probe.get("outcome"):
            raise LedgerError("probe_missing_outcome", row["capability"])
        if not isinstance(probe.get("passed"), bool):
            raise LedgerError("probe_missing_result", row["capability"])


def window_base(row: dict) -> date:
    """The date the window runs from: the most recently acquired source.

    RFC-0097 D3 conditions `verified` on a source *acquired* inside the window,
    so the base is a retrieval date. Running the window from `last_verified`
    instead would let a verification date be advanced with no fresh retrieval.
    """
    return max(_parse_date(s.get("retrieved_at"), "retrieved_at") for s in row["sources"])


def resolve_state(row: dict, reference_date: date, window_days: int) -> str:
    """Resolve one row's lifecycle state by first matching guard."""
    if window_days > MAXIMUM_WINDOW_DAYS:
        raise LedgerError("window_exceeds_maximum", str(window_days))
    if row.get("recorded_unavailable"):
        return "unavailable"
    if (reference_date - window_base(row)).days > window_days:
        return "stale"
    probe = row.get("probe")
    if probe is not None and probe.get("passed") is True:
        return "verified"
    return "experimental"


def resolve_rollup(profile: dict, required: list, reference_date: date) -> str:
    """Roll a profile up from its required rows only."""
    window = profile["declared_window_days"]
    present = {row["capability"]: row for row in profile["capabilities"]}
    if any(name not in present for name in required):
        return "incomplete"
    states = [resolve_state(present[name], reference_date, window) for name in required]
    if "stale" in states:
        return "needs-revalidation"
    return "complete-current"


# ── fixtures ──────────────────────────────────────────────────────────────


@pytest.fixture(name="ledger")
def _ledger() -> dict:
    return json.loads(LEDGER.read_text(encoding="utf-8"))


def _row(**overrides) -> dict:
    row = {
        "capability": "example-capability",
        "scope": "An example scope.",
        "surface": "CLI",
        "os": "macOS",
        "last_verified": "2026-08-31",
        "revalidation_trigger": "An example trigger.",
        "sources": [
            {
                "title": "Example",
                "url": "https://example.invalid/docs",
                "retrieved_at": "2026-08-31",
                "source_version": "none exposed",
            }
        ],
        "probe": {"gesture": "g", "outcome": "o", "passed": True},
    }
    row.update(overrides)
    return row


REFERENCE = date(2026, 8, 31)


# ── each state is produced by a distinct named input ──────────────────────


def test_verified_requires_a_passing_probe_inside_the_window() -> None:
    assert resolve_state(_row(), REFERENCE, 90) == "verified"


def test_absent_probe_resolves_experimental() -> None:
    row = _row()
    del row["probe"]
    assert resolve_state(row, REFERENCE, 90) == "experimental"


def test_failed_probe_resolves_experimental_not_verified() -> None:
    """The mutation that matters: a probe that ran and failed is not a pass.

    Branching on probe presence alone computes `verified` here, which inverts
    the honesty property the ledger exists to carry.
    """
    row = _row(probe={"gesture": "g", "outcome": "the capability was absent", "passed": False})
    assert resolve_state(row, REFERENCE, 90) == "experimental"


def test_elapsed_window_resolves_stale() -> None:
    assert resolve_state(_row(), date(2026, 12, 31), 90) == "stale"


def test_recorded_unavailable_resolves_unavailable() -> None:
    assert resolve_state(_row(recorded_unavailable=True), REFERENCE, 90) == "unavailable"


def test_every_state_is_reachable_and_no_two_inputs_named_here_agree() -> None:
    """Anti-vacuity: the four states are each produced, by four stated inputs."""
    passing = _row()
    absent = _row()
    del absent["probe"]
    produced = {
        "verified": resolve_state(passing, REFERENCE, 90),
        "experimental": resolve_state(absent, REFERENCE, 90),
        "stale": resolve_state(passing, date(2026, 12, 31), 90),
        "unavailable": resolve_state(_row(recorded_unavailable=True), REFERENCE, 90),
    }
    assert produced == {name: name for name in STATES}


# ── precedence between co-occurring entry conditions ──────────────────────


def test_recorded_unavailable_short_circuits_an_elapsed_window() -> None:
    row = _row(recorded_unavailable=True)
    assert resolve_state(row, date(2026, 12, 31), 90) == "unavailable"


def test_elapsed_window_decides_a_failed_probe_past_its_window() -> None:
    """The pair AC9's qualification exists for: elapsed beats failed-probe."""
    row = _row(probe={"gesture": "g", "outcome": "absent", "passed": False})
    assert resolve_state(row, date(2026, 12, 31), 90) == "stale"


def test_advancing_only_the_reference_date_flips_verified_to_stale() -> None:
    """Killing mutation for window elapse: one input moves, nothing else."""
    row = _row()
    assert resolve_state(row, REFERENCE, 90) == "verified"
    assert resolve_state(row, REFERENCE.replace(month=12, day=31), 90) == "stale"


def test_window_runs_from_retrieval_not_from_the_verification_date() -> None:
    """A verification date advanced without a fresh retrieval must not help."""
    row = _row(last_verified="2026-08-31")
    row["sources"][0]["retrieved_at"] = "2026-01-01"
    assert window_base(row) == date(2026, 1, 1)
    assert resolve_state(row, REFERENCE, 90) == "stale"


# ── roll-up ───────────────────────────────────────────────────────────────


def _profile(rows: list, roll_up: str = "complete-current") -> dict:
    return {
        "runtime": "example",
        "topic": "example",
        "declared_window_days": 90,
        "roll_up": roll_up,
        "capabilities": rows,
    }


def test_rollup_is_complete_current_when_every_required_row_is_present() -> None:
    rows = [_row(capability="a"), _row(capability="b")]
    assert resolve_rollup(_profile(rows), ["a", "b"], REFERENCE) == "complete-current"


def test_a_missing_required_row_makes_the_profile_incomplete() -> None:
    rows = [_row(capability="a")]
    assert resolve_rollup(_profile(rows), ["a", "b"], REFERENCE) == "incomplete"


def test_a_stale_required_row_makes_the_profile_need_revalidation() -> None:
    stale = _row(capability="b")
    stale["sources"][0]["retrieved_at"] = "2026-01-01"
    rows = [_row(capability="a"), stale]
    assert resolve_rollup(_profile(rows), ["a", "b"], REFERENCE) == "needs-revalidation"


def test_an_unavailable_row_does_not_prevent_complete_current() -> None:
    """An honestly absent capability is an enterprise delta, not a gap."""
    rows = [_row(capability="a"), _row(capability="b", recorded_unavailable=True)]
    assert resolve_rollup(_profile(rows), ["a", "b"], REFERENCE) == "complete-current"


def test_a_stale_non_required_row_does_not_change_the_rollup() -> None:
    stale = _row(capability="extra")
    stale["sources"][0]["retrieved_at"] = "2026-01-01"
    rows = [_row(capability="a"), stale]
    assert resolve_rollup(_profile(rows), ["a"], REFERENCE) == "complete-current"


# ── rejections, each naming its own diagnostic ────────────────────────────


@pytest.mark.parametrize(
    ("code", "mutate"),
    [
        ("empty_sources", lambda r: r.update(sources=[])),
        ("relative_or_internal_url", lambda r: r["sources"][0].update(url="../docs/x.md")),
        ("missing_source_title", lambda r: r["sources"][0].update(title="")),
        ("missing_source_version", lambda r: r["sources"][0].update(source_version="")),
        ("malformed_date", lambda r: r["sources"][0].update(retrieved_at="31-08-2026")),
        ("missing_provenance_field", lambda r: r.update(surface="")),
        ("probe_missing_outcome", lambda r: r["probe"].update(outcome="")),
        ("probe_missing_result", lambda r: r["probe"].pop("passed")),
        (
            "verification_ahead_of_retrieval",
            lambda r: r.update(last_verified="2026-09-30"),
        ),
    ],
)
def test_each_rejection_names_its_own_diagnostic(code, mutate) -> None:
    row = _row()
    mutate(row)
    with pytest.raises(LedgerError) as excinfo:
        validate_row(row)
    assert excinfo.value.code == code


def test_a_window_above_the_permitted_maximum_is_rejected() -> None:
    with pytest.raises(LedgerError) as excinfo:
        resolve_state(_row(), REFERENCE, MAXIMUM_WINDOW_DAYS + 1)
    assert excinfo.value.code == "window_exceeds_maximum"


def test_a_valid_row_is_accepted() -> None:
    """Control: the rejection sweep above would pass vacuously on a row that
    could never validate, so the unmutated row must survive it."""
    validate_row(_row())


# ── the shipped ledger ────────────────────────────────────────────────────


def test_the_required_set_transcribes_the_authority_it_names(ledger) -> None:
    required = ledger["required_capabilities"]
    assert required["source_ref"] == REQUIRED_SOURCE_REF
    assert required["expected_count"] == REQUIRED_COUNT
    assert len(required["claude-code"]) == REQUIRED_COUNT
    assert len(set(required["claude-code"])) == REQUIRED_COUNT


def test_every_shipped_row_validates(ledger) -> None:
    rows = [row for profile in ledger["profiles"] for row in profile["capabilities"]]
    assert rows, "the ledger carries no rows, so this sweep would prove nothing"
    for row in rows:
        validate_row(row)


def test_every_shipped_row_state_equals_its_computed_state(ledger) -> None:
    """A recorded state edited away from its computed value must fail."""
    evaluated_at = date.fromisoformat(ledger["evaluated_at"])
    checked = 0
    for profile in ledger["profiles"]:
        window = profile["declared_window_days"]
        for row in profile["capabilities"]:
            assert row["state"] == resolve_state(row, evaluated_at, window), row["capability"]
            checked += 1
    assert checked, "no row was compared"


def test_every_shipped_rollup_equals_its_recomputed_rollup(ledger) -> None:
    evaluated_at = date.fromisoformat(ledger["evaluated_at"])
    for profile in ledger["profiles"]:
        required = ledger["required_capabilities"][profile["runtime"]]
        assert profile["roll_up"] == resolve_rollup(profile, required, evaluated_at)
        assert profile["roll_up"] in ROLL_UPS


def test_a_hand_edited_row_state_is_caught(ledger) -> None:
    """Mutation proof for the row-level comparison: without it, a stored state
    is a claim nothing verifies."""
    evaluated_at = date.fromisoformat(ledger["evaluated_at"])
    mutated = copy.deepcopy(ledger)
    row = mutated["profiles"][0]["capabilities"][0]
    window = mutated["profiles"][0]["declared_window_days"]
    row["state"] = "verified" if row["state"] != "verified" else "experimental"
    assert row["state"] != resolve_state(row, evaluated_at, window)


def test_a_hand_edited_rollup_is_caught(ledger) -> None:
    evaluated_at = date.fromisoformat(ledger["evaluated_at"])
    mutated = copy.deepcopy(ledger)
    profile = mutated["profiles"][0]
    required = mutated["required_capabilities"][profile["runtime"]]
    profile["roll_up"] = "complete-current" if profile["roll_up"] != "complete-current" else "incomplete"
    assert profile["roll_up"] != resolve_rollup(profile, required, evaluated_at)


def test_evaluated_at_is_no_earlier_than_the_latest_retrieval(ledger) -> None:
    """Otherwise the projection could be validated at a date that guarantees no
    row is ever stale."""
    evaluated_at = date.fromisoformat(ledger["evaluated_at"])
    latest = max(
        date.fromisoformat(source["retrieved_at"])
        for profile in ledger["profiles"]
        for row in profile["capabilities"]
        for source in row["sources"]
    )
    assert evaluated_at >= latest


def test_declared_windows_are_within_the_permitted_maximum(ledger) -> None:
    for profile in ledger["profiles"]:
        assert profile["declared_window_days"] <= MAXIMUM_WINDOW_DAYS
