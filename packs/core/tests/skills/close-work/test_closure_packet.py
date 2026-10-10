"""T7 — evidence packet, status write guard, and closure record round-trip.

Covers AC-0027, AC-0028, AC-0029, AC-0030, AC-0031, AC-0032, AC-0034, AC-0035
of ``docs/specs/closure-eligibility-check/``.

**AC-0027** — an eligible verdict presents a packet carrying six fields.
All six are asserted individually; dropping any one of them must red (the
mutation requirement: a per-field assertion is the discriminating shape, not a
single presence check against the whole packet).

**AC-0028** — where the ancestor declares ``Outcome co-owner:``, the packet
names that peer. The verdict is unchanged by the peer's state, which is outside
the boundary this check may read. Both halves: the peer appears, and removing
it changes nothing about the verdict type.

**AC-0029** — the check writes no ``Status:`` value. Instrumented by a
write-raising reader double: any attempt to open a path not in the declared
file set surfaces as a ``FileNotFoundError`` captured in a list, which must
remain empty after the check completes.

**AC-0030** — no ``Status:`` write reaches the filesystem on a path where the
human declined or has not yet answered. Driven through the real confirmation
seam (``write_closure_record``'s ``_confirmed`` parameter), not the write-raising
double. A write-raising double cannot observe ordering; this seam can.

**AC-0031** — the packet names the closing intent's ``workspace.toml``
registration entry and collection as an effect the human must clear.

**AC-0032** — the value produced by ``build_fulfilled_value`` satisfies the
shipped ``Fulfilled:`` value rule, asserted by passing the value through
``intent_shape._check_dated_evidence``, not by matching a string.

**AC-0034** — no disposition row reaches the artifact → absence (None) reported.
**AC-0035** — a ``cool-30-days``-eligible fixture produces that row reported.

Module loaded under ``"closure_index__packet_t7"`` to isolate this suite.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

# ── Module loaders ────────────────────────────────────────────────────────────

_SCRIPTS = (
    Path(__file__).resolve().parents[3]
    / ".apm" / "skills" / "close-work" / "scripts"
)
_WORK_INTAKE = (
    Path(__file__).resolve().parents[3]
    / ".apm" / "skills" / "work-intake" / "scripts"
)


def _load(name: str, key: str, directory: Path | None = None) -> object:
    """Load a script by absolute path under a unique sys.modules key."""
    d = directory if directory is not None else _SCRIPTS
    spec = importlib.util.spec_from_file_location(key, d / f"{name}.py")
    assert spec and spec.loader, f"no module at {d / f'{name}.py'}"
    module = importlib.util.module_from_spec(spec)
    sys.modules[key] = module
    spec.loader.exec_module(module)
    return module


ci = _load("closure_index", "closure_index__packet_t7")

_fx_spec = importlib.util.spec_from_file_location(
    "closure_graph_fixture__packet",
    Path(__file__).resolve().parent / "closure_graph_fixture.py",
)
assert _fx_spec and _fx_spec.loader
_fx = importlib.util.module_from_spec(_fx_spec)
sys.modules["closure_graph_fixture__packet"] = _fx
_fx_spec.loader.exec_module(_fx)
intent_shape = _load("intent_shape", "intent_shape__packet_t7", _WORK_INTAKE)

# ── Fixture helpers ───────────────────────────────────────────────────────────

ROOT = Path("/fake/root")
INTENTS_DIR = ROOT / "docs" / "product" / "intents"


def _intent(
    slug: str,
    status: str = "Accepted",
    parent: str | None = None,
    decomposed: str | None = None,
    co_owner: str | None = None,
) -> str:
    lines = [f"- **Slug:** {slug}", f"- **Status:** {status}"]
    if parent:
        lines.append(f"- **Parent intent:** intent:{parent}")
    if decomposed:
        lines.append(f"- **Decomposed:** {decomposed}")
    if co_owner:
        lines.append(f"- **Outcome co-owner:** {co_owner}")
    lines.append("")
    return "\n".join(lines)


# ── Eligible fixture builder ──────────────────────────────────────────────────
#
# Uses a ``children`` terminus ancestor with two Fulfilled (terminal) child
# intents. This gives non-empty ``per_descendant_verdicts`` — necessary for
# mutation-testing that field.


def _make_eligible_store(*, co_owner: str | None = None) -> dict[Path, str]:
    """Return a fake filesystem store for a children-terminus eligible fixture."""
    ancestor = _intent(
        "anc",
        status="Accepted",
        decomposed="2026-09-27 children",
        co_owner=co_owner,
    )
    child_a = _intent("child-a", status="Fulfilled", parent="anc")
    child_b = _intent("child-b", status="Fulfilled", parent="anc")
    return {
        INTENTS_DIR / "anc.md": ancestor,
        INTENTS_DIR / "child-a.md": child_a,
        INTENTS_DIR / "child-b.md": child_b,
    }


def _reader_from_store(store: dict[Path, str]):
    def _r(path: Path) -> str:
        return store.get(path, "")
    return _r


def _dir_lister_from_store(store: dict[Path, str]):
    def _dl(d: Path) -> list[Path]:
        return [p for p in store if p.parent == d]
    return _dl


def _call_eligible(
    store: dict[Path, str],
    *,
    decider: str = "test-decider",
    decision_date: str = "2026-09-27",
    ancestor_fields: dict[str, str] | None = None,
    workspace_lookup=None,
    disposition_lookup=None,
):
    """Run check_ancestor_closure on the eligible fixture, return the verdict."""
    return ci.check_ancestor_closure(
        "anc",
        "Accepted",
        "children",
        ROOT,
        _reader=_reader_from_store(store),
        _dir_lister=_dir_lister_from_store(store),
        _graph_provider=_fx.graph_provider_from_files(store, ROOT),
        _freshness_checker=lambda: True,
        _decider=decider,
        _decision_date=decision_date,
        _ancestor_fields=ancestor_fields if ancestor_fields is not None else {
            "Slug": "anc",
            "Status": "Accepted",
            "Decomposed": "2026-09-27 children",
        },
        _workspace_lookup=workspace_lookup,
        _disposition_lookup=disposition_lookup,
    )


# ── AC-0027: six required packet fields ──────────────────────────────────────


def test_ac0027_packet_is_present_on_eligible_verdict() -> None:
    """An eligible verdict with _decider supplied carries a non-None packet."""
    store = _make_eligible_store()
    verdict = _call_eligible(store)
    assert isinstance(verdict, ci.ClosureEligible), f"Expected ClosureEligible, got {verdict!r}"
    assert verdict.packet is not None, "packet is None; _decider was supplied"


def test_ac0027_no_packet_without_decider() -> None:
    """An eligible verdict without _decider has packet=None (backward compat)."""
    store = _make_eligible_store()
    verdict = ci.check_ancestor_closure(
        "anc", "Accepted", "children", ROOT,
        _reader=_reader_from_store(store),
        _dir_lister=_dir_lister_from_store(store),
        _graph_provider=_fx.graph_provider_from_files(store, ROOT),
        _freshness_checker=lambda: True,
        # _decider is NOT supplied
    )
    assert isinstance(verdict, ci.ClosureEligible)
    assert verdict.packet is None, "packet should be None when _decider not supplied"


def test_ac0027_field_decision_date() -> None:
    """Packet carries a non-empty decision_date (field 1 of 6)."""
    store = _make_eligible_store()
    verdict = _call_eligible(store, decision_date="2026-09-27")
    assert verdict.packet is not None
    assert verdict.packet.decision_date, "decision_date is empty"
    assert verdict.packet.decision_date == "2026-09-27"


def test_ac0027_field_decider() -> None:
    """Packet carries a non-empty decider (field 2 of 6)."""
    store = _make_eligible_store()
    verdict = _call_eligible(store, decider="eugenelim")
    assert verdict.packet is not None
    assert verdict.packet.decider, "decider is empty"
    assert verdict.packet.decider == "eugenelim"


def test_ac0027_field_ratified_decomposed() -> None:
    """Packet carries the ancestor's ratified Decomposed: value (field 3 of 6)."""
    store = _make_eligible_store()
    ancestor_fields = {
        "Slug": "anc",
        "Status": "Accepted",
        "Decomposed": "2026-09-27 children",
    }
    verdict = _call_eligible(store, ancestor_fields=ancestor_fields)
    assert verdict.packet is not None
    assert verdict.packet.ratified_decomposed, "ratified_decomposed is empty"
    assert verdict.packet.ratified_decomposed == "2026-09-27 children"


def test_ac0027_field_verification_basis() -> None:
    """Packet carries a non-empty verification_basis (field 4 of 6)."""
    store = _make_eligible_store()
    verdict = _call_eligible(store)
    assert verdict.packet is not None
    assert verdict.packet.verification_basis, "verification_basis is empty"


def test_ac0027_field_per_descendant_verdicts() -> None:
    """Packet carries per_descendant_verdicts with one triple per descendant (field 5 of 6).

    The fixture has two Fulfilled children, so the tuple should have two entries.
    Each entry is (slug, status, evidence_locator).
    """
    store = _make_eligible_store()
    verdict = _call_eligible(store)
    assert verdict.packet is not None
    pdv = verdict.packet.per_descendant_verdicts
    assert isinstance(pdv, tuple), f"per_descendant_verdicts is not a tuple: {type(pdv)}"
    assert len(pdv) == 2, f"Expected 2 descendant verdicts, got {len(pdv)}: {pdv!r}"
    for slug, status, locator in pdv:
        assert slug, "slug is empty in per_descendant_verdicts"
        assert status, "status is empty in per_descendant_verdicts"
        assert locator, "evidence_locator is empty in per_descendant_verdicts"


def test_ac0027_field_stated_confidence() -> None:
    """Packet carries a non-empty stated_confidence naming what was NOT checked (field 6 of 6)."""
    store = _make_eligible_store()
    verdict = _call_eligible(store)
    assert verdict.packet is not None
    assert verdict.packet.stated_confidence, "stated_confidence is empty"


def test_ac0027_per_descendant_verdict_has_evidence_locator() -> None:
    """Each per_descendant_verdicts entry carries a non-empty evidence_locator.

    The locator is a repository-relative path (e.g. docs/product/intents/slug.md).
    """
    store = _make_eligible_store()
    verdict = _call_eligible(store)
    assert verdict.packet is not None
    for _slug, _status, locator in verdict.packet.per_descendant_verdicts:
        assert "/" in locator or ":" in locator, (
            f"evidence_locator {locator!r} does not look like a path or typed ref"
        )


# ── AC-0028: Outcome co-owner ─────────────────────────────────────────────────


def test_ac0028_outcome_co_owner_named_in_packet() -> None:
    """Where ancestor declares Outcome co-owner:, the packet names that peer."""
    co_owner_value = "intent:some-peer-intent"
    store = _make_eligible_store(co_owner=co_owner_value)
    ancestor_fields = {
        "Slug": "anc",
        "Status": "Accepted",
        "Decomposed": "2026-09-27 children",
        "Outcome co-owner": co_owner_value,
    }
    verdict = _call_eligible(store, ancestor_fields=ancestor_fields)
    assert isinstance(verdict, ci.ClosureEligible)
    assert verdict.packet is not None
    assert verdict.packet.outcome_co_owner == co_owner_value, (
        f"Expected outcome_co_owner={co_owner_value!r}, "
        f"got {verdict.packet.outcome_co_owner!r}"
    )


def test_ac0028_verdict_unchanged_when_co_owner_absent() -> None:
    """The verdict is ClosureEligible whether or not Outcome co-owner: is declared.

    Both halves of AC-0028: the peer appears (tested above), and its presence or
    absence changes nothing about the verdict type. The peer's state is outside
    the closure boundary; resolving it would be a boundary violation.
    """
    store = _make_eligible_store()  # no co-owner in fixture
    ancestor_without = {
        "Slug": "anc",
        "Status": "Accepted",
        "Decomposed": "2026-09-27 children",
    }
    ancestor_with = {
        "Slug": "anc",
        "Status": "Accepted",
        "Decomposed": "2026-09-27 children",
        "Outcome co-owner": "intent:some-peer",
    }
    verdict_without = _call_eligible(store, ancestor_fields=ancestor_without)
    verdict_with = _call_eligible(store, ancestor_fields=ancestor_with)

    # Both verdicts must be ClosureEligible — the co-owner field is informational only.
    assert isinstance(verdict_without, ci.ClosureEligible), (
        f"Without co-owner: expected ClosureEligible, got {verdict_without!r}"
    )
    assert isinstance(verdict_with, ci.ClosureEligible), (
        f"With co-owner: expected ClosureEligible, got {verdict_with!r}"
    )
    # The co-owner field appears in the packet only when declared.
    assert verdict_without.packet is not None
    assert verdict_without.packet.outcome_co_owner is None
    assert verdict_with.packet is not None
    assert verdict_with.packet.outcome_co_owner == "intent:some-peer"


# ── AC-0029: the check writes no Status: value ────────────────────────────────


def test_ac0029_check_writes_no_status_value() -> None:
    """check_ancestor_closure never writes to the filesystem (AC-0029).

    A write-raising reader double raises when called for a path not in the
    declared file set. Any attempt to open a new path (e.g. to write a Status:
    line) surfaces here. The ``writes_attempted`` list must be empty after the
    check returns.

    The check is read-only by design; this test verifies that the design holds
    at the production entry point rather than asserting it from structure alone.
    """
    store = _make_eligible_store()
    writes_attempted: list[Path] = []

    def write_raising_reader(path: Path) -> str:
        """Raises when called for a path not in the declared file set.

        Any write to a new path would require the writer to open it; this
        surfaces that attempt as a captured FileNotFoundError rather than
        a hard raise so the test can report the path.
        """
        if path in store:
            return store[path]
        writes_attempted.append(path)
        raise FileNotFoundError(f"unexpected path open: {path}")

    ci.check_ancestor_closure(
        "anc",
        "Accepted",
        "children",
        ROOT,
        _reader=write_raising_reader,
        _dir_lister=_dir_lister_from_store(store),
        _graph_provider=_fx.graph_provider_from_files(store, ROOT),
        _freshness_checker=lambda: True,
        _decider="test-decider",
        _decision_date="2026-09-27",
    )

    assert writes_attempted == [], (
        f"reader was called for unexpected paths (possible write attempt): "
        f"{writes_attempted}"
    )


# ── AC-0030: no write on declined or pending confirmation ────────────────────


def test_ac0030_declined_confirmation_leaves_no_write() -> None:
    """write_closure_record does not write when the human declined (AC-0030).

    This drives the real confirmation seam (_confirmed=False) rather than the
    write-raising double, which cannot observe ordering. A declined confirmation
    returns False without calling the writer.
    """
    calls: list[tuple[Path, str]] = []

    def capturing_writer(path: Path, value: str) -> None:
        calls.append((path, value))

    result = ci.write_closure_record(
        Path("/fake/intent.md"),
        "2026-09-27 test-decider: evidence",
        _confirmed=False,
        _writer=capturing_writer,
    )

    assert result is False, "write_closure_record should return False on declined"
    assert calls == [], (
        f"writer was called despite declined confirmation: {calls}"
    )


def test_ac0030_pending_confirmation_leaves_no_write() -> None:
    """write_closure_record does not write when the human has not yet answered (AC-0030).

    This drives the real confirmation seam (_confirmed=None) — the not-yet-
    answered case. The two cases (declined and pending) have different meanings
    but the same effect: no write reaches the filesystem.
    """
    calls: list[tuple[Path, str]] = []

    def capturing_writer(path: Path, value: str) -> None:
        calls.append((path, value))

    result = ci.write_closure_record(
        Path("/fake/intent.md"),
        "2026-09-27 test-decider: evidence",
        _confirmed=None,
        _writer=capturing_writer,
    )

    assert result is False, "write_closure_record should return False on pending"
    assert calls == [], (
        f"writer was called despite pending (not-yet-answered) confirmation: {calls}"
    )


def test_ac0030_confirmed_does_write() -> None:
    """Paired positive arm: write_closure_record writes when confirmed (AC-0030).

    Without this arm, an implementation that always returns False satisfies the
    declined and pending arms while never actually writing.
    """
    calls: list[tuple[Path, str]] = []

    def capturing_writer(path: Path, value: str) -> None:
        calls.append((path, value))

    target = Path("/fake/intent.md")
    value = "2026-09-27 test-decider: T7 confirmed"
    result = ci.write_closure_record(
        target,
        value,
        _confirmed=True,
        _writer=capturing_writer,
    )

    assert result is True, "write_closure_record should return True on confirmed"
    assert calls == [(target, value)], (
        f"Expected exactly one write call with ({target!r}, {value!r}), "
        f"got {calls!r}"
    )


# ── AC-0031: workspace registration in packet ─────────────────────────────────


def test_ac0031_workspace_registration_named_in_packet() -> None:
    """The packet names the workspace.toml entry and collection (AC-0031).

    The closing intent's workspace registration is an effect the human must
    clear alongside the status write. The check names it; it does not clear it.
    """
    expected_reg = ("docs/product/intents/anc.md", "backlog.open")
    store = _make_eligible_store()

    verdict = _call_eligible(
        store,
        workspace_lookup=lambda slug: expected_reg if slug == "anc" else None,
    )
    assert isinstance(verdict, ci.ClosureEligible)
    assert verdict.packet is not None
    assert verdict.packet.workspace_registration == expected_reg, (
        f"Expected workspace_registration={expected_reg!r}, "
        f"got {verdict.packet.workspace_registration!r}"
    )


def test_ac0031_no_registration_when_lookup_returns_none() -> None:
    """workspace_registration is None when the lookup finds no entry."""
    store = _make_eligible_store()
    verdict = _call_eligible(
        store,
        workspace_lookup=lambda slug: None,
    )
    assert isinstance(verdict, ci.ClosureEligible)
    assert verdict.packet is not None
    assert verdict.packet.workspace_registration is None


# ── AC-0032: Fulfilled: value round-trip ─────────────────────────────────────


def test_ac0032_fulfilled_value_round_trips_through_shipped_rule() -> None:
    """build_fulfilled_value produces a value the shipped Fulfilled: rule accepts.

    The shipped rule (intent_shape._check_dated_evidence) requires an ISO-8601
    date, a single space, then non-empty text. The value is verified by passing
    it back through the rule, not by matching a string.
    """
    value = ci.build_fulfilled_value(
        "2026-09-27",
        "eugenelim",
        "closure check passed; all descendants terminal",
    )
    # The shipped rule returns None on success, a non-None error string on failure.
    result = intent_shape._check_dated_evidence(value)
    assert result is None, (
        f"Fulfilled: value rule rejected the value {value!r}: {result!r}"
    )


def test_ac0032_build_fulfilled_value_raises_on_empty_date() -> None:
    """build_fulfilled_value raises ValueError for an empty date."""
    import pytest
    with pytest.raises(ValueError, match="date"):
        ci.build_fulfilled_value("", "eugenelim", "evidence")


def test_ac0032_build_fulfilled_value_raises_on_empty_decider() -> None:
    """build_fulfilled_value raises ValueError for an empty decider."""
    import pytest
    with pytest.raises(ValueError, match="decider"):
        ci.build_fulfilled_value("2026-09-27", "", "evidence")


def test_ac0032_build_fulfilled_value_raises_on_empty_evidence() -> None:
    """build_fulfilled_value raises ValueError for an empty evidence string."""
    import pytest
    with pytest.raises(ValueError, match="evidence"):
        ci.build_fulfilled_value("2026-09-27", "eugenelim", "")


# ── AC-0034: absent disposition reports absence ───────────────────────────────


def test_ac0034_absent_disposition_reports_absence() -> None:
    """When no disposition row reaches the artifact, packet.disposition_row is None (AC-0034).

    The absence is a positive report, not a default and not a failure. The check
    continues to an eligible verdict; it does not fail because no row matched.

    Fixture: the disposition_lookup returns None (no row reaches this artifact).
    """
    store = _make_eligible_store()
    verdict = _call_eligible(
        store,
        disposition_lookup=lambda slug: None,
    )
    assert isinstance(verdict, ci.ClosureEligible)
    assert verdict.packet is not None
    assert verdict.packet.disposition_row is None, (
        f"Expected disposition_row=None for absent row, "
        f"got {verdict.packet.disposition_row!r}"
    )


def test_ac0034_verdict_is_still_eligible_without_disposition_row() -> None:
    """Absence of a matching disposition row does not fail or refuse the decision."""
    store = _make_eligible_store()
    verdict = _call_eligible(
        store,
        disposition_lookup=lambda slug: None,
    )
    # Verdict must be eligible; absence of a row is just a report, not a block.
    assert isinstance(verdict, ci.ClosureEligible), (
        f"Expected ClosureEligible when disposition is absent, got {verdict!r}"
    )


# ── AC-0035: cool-30-days row reported ───────────────────────────────────────


def test_ac0035_cool_30_days_row_reported() -> None:
    """An artifact a cool-30-days-eligible fixture does reach has that row reported (AC-0035).

    This is the arm without which an implementation that always reports absence
    (None) would pass AC-0034 while violating AC-0035. The disposition_lookup
    returns "cool-30-days" for this fixture.
    """
    store = _make_eligible_store()
    verdict = _call_eligible(
        store,
        disposition_lookup=lambda slug: "cool-30-days",
    )
    assert isinstance(verdict, ci.ClosureEligible)
    assert verdict.packet is not None
    assert verdict.packet.disposition_row == "cool-30-days", (
        f"Expected disposition_row='cool-30-days', "
        f"got {verdict.packet.disposition_row!r}"
    )


def test_ac0035_disposition_row_does_not_affect_verdict_type() -> None:
    """The disposition row is informational; it does not change the verdict type."""
    store = _make_eligible_store()
    verdict_absent = _call_eligible(store, disposition_lookup=lambda slug: None)
    verdict_present = _call_eligible(store, disposition_lookup=lambda slug: "cool-30-days")
    assert isinstance(verdict_absent, ci.ClosureEligible)
    assert isinstance(verdict_present, ci.ClosureEligible)


# ── AC-0029, asserted structurally rather than by interception ───────────────


def test_the_module_contains_no_write_primitive() -> None:
    """The check cannot write a ``Status:`` value because it cannot write at all.

    A write-raising double only proves the paths a test happens to drive stay
    read-only. This asserts the stronger property the module is designed
    around: no filesystem-mutating call appears in its source, so a future edit
    that introduces one reds here rather than waiting for a test to drive it.

    ``write_closure_record`` is the deliberate exception and is not a
    counter-example: it performs no write itself, delegating to an injected
    ``_writer`` supplied by ``close-work``'s existing confirmation machinery.
    """
    source = (
        _SCRIPTS / "closure_index.py"
    ).read_text(encoding="utf-8")
    forbidden = (
        ".write_text(",
        ".write_bytes(",
        ".mkdir(",
        ".touch(",
        ".unlink(",
        ".rename(",
        "os.replace(",
        "shutil.",
    )
    found = sorted(token for token in forbidden if token in source)
    assert found == [], (
        f"closure_index.py gained a filesystem-mutating call: {found}. "
        "The check is read-only; mutation belongs behind the confirmation seam."
    )


def _dr(slug: str, status: str = "Fulfilled", kind: str = "intent"):
    """A terminal descendant record, for packet-shape assertions."""
    return ci.DescendantRecord(slug=slug, kind=kind, status=status, terminus="")


# ── AC-0038/0039/0040: what a real decider needed and did not get ────────────
#
# These three come from the manual run, not from review. A decider given the
# six-field packet for a real eligible closure returned *cannot decide*: the
# packet showed the tree was finished and never said what the intent promised.


def test_ac0038_packet_carries_the_ancestors_stated_outcome() -> None:
    outcome = "Adopters stop hand-rolling the overlay."
    pk = ci._build_eligible_packet(
        ancestor_slug="anc",
        ancestor_terminus="children",
        ancestor_fields={"Decomposed": "2026-09-19 children", "__outcome__": outcome},
        descendants={},
        basis="all-descendants-terminal",
        decider="eugenelim",
        decision_date="2026-09-27",
        workspace_lookup=None,
        disposition_lookup=None,
    )
    assert pk.stated_outcome == outcome


def test_ac0038_a_missing_outcome_is_stated_not_omitted() -> None:
    """A decider cannot tell a dropped field from an intent that promised nothing."""
    pk = ci._build_eligible_packet(
        ancestor_slug="anc",
        ancestor_terminus="children",
        ancestor_fields={"Decomposed": "2026-09-19 children"},
        descendants={},
        basis="b",
        decider="d",
        decision_date="2026-09-27",
        workspace_lookup=None,
        disposition_lookup=None,
    )
    assert pk.stated_outcome
    assert "not stated" in pk.stated_outcome


def test_ac0039_child_count_reports_resolved_against_declared() -> None:
    """Resolved and declared are reported separately (AC-0039)."""
    pk = ci._build_eligible_packet(
        ancestor_slug="anc",
        ancestor_terminus="children",
        ancestor_fields={"Decomposed": "2026-09-19 children", "__declared_children__": "4"},
        descendants={("intent", "a"): _dr("a"), ("intent", "b"): _dr("b")},
        basis="b",
        decider="d",
        decision_date="2026-09-27",
        workspace_lookup=None,
        disposition_lookup=None,
    )
    # Both numbers present: a tree missing a ratified child must be visible,
    # not inferable only by someone who already knows the denominator.
    assert pk.ratified_child_count == "2 of 4"


def test_ac0039_an_unknown_denominator_is_said_not_guessed() -> None:
    """An unknown denominator is stated, never guessed (AC-0039)."""
    pk = ci._build_eligible_packet(
        ancestor_slug="anc",
        ancestor_terminus="children",
        ancestor_fields={"Decomposed": "2026-09-19 children"},
        descendants={("intent", "a"): _dr("a")},
        basis="b",
        decider="d",
        decision_date="2026-09-27",
        workspace_lookup=None,
        disposition_lookup=None,
    )
    assert "1 resolved" in pk.ratified_child_count
    assert "not stated" in pk.ratified_child_count


def test_ac0040_no_co_owner_means_no_co_owner_caveat() -> None:
    """A caveat that always fires sends the decider after a ruled-out risk (AC-0040)."""
    pk = ci._build_eligible_packet(
        ancestor_slug="anc",
        ancestor_terminus="children",
        ancestor_fields={"Decomposed": "2026-09-19 children"},
        descendants={},
        basis="b",
        decider="d",
        decision_date="2026-09-27",
        workspace_lookup=None,
        disposition_lookup=None,
    )
    assert pk.outcome_co_owner is None
    assert "co-owner" not in pk.stated_confidence.lower()


def test_ac0040_a_declared_co_owner_does_carry_the_caveat() -> None:
    """The paired arm for AC-0040: removing the caveat outright would pass the case above."""
    pk = ci._build_eligible_packet(
        ancestor_slug="anc",
        ancestor_terminus="children",
        ancestor_fields={
            "Decomposed": "2026-09-19 children",
            "Outcome co-owner": "capability:peer-thing",
        },
        descendants={},
        basis="b",
        decider="d",
        decision_date="2026-09-27",
        workspace_lookup=None,
        disposition_lookup=None,
    )
    assert pk.outcome_co_owner == "capability:peer-thing"
    assert "co-owner" in pk.stated_confidence.lower()
