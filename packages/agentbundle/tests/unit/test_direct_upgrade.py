"""AC30: direct upgrade capability re-consent, in both directions."""

from __future__ import annotations

import pytest
from agentbundle.direct_source_state import (
    UNDECLARED_TOOLS,
    Capabilities,
    DirectStateError,
    accept_capability_pin,
    capability_pin,
    compare_capabilities,
)

DIGEST_A = "sha256-1:" + "aa" * 32
DIGEST_B = "sha256-1:" + "bb" * 32


def _caps(**overrides) -> Capabilities:
    base = {
        "allowed_tools": frozenset({"Read"}),
        "skill_digest": DIGEST_A,
        "skill_identities": frozenset({"alpha"}),
        "payload_digests": {"scripts/run.py": DIGEST_A},
        "boundaries": frozenset({"filesystem_read"}),
        "credentialed": False,
    }
    base.update(overrides)
    return Capabilities(**base)


def test_capability_reconsent_directions():
    # AC30 — every listed field triggers re-consent, in either direction, and
    # an unchanged surface triggers none.
    baseline = _caps()
    assert compare_capabilities(baseline, _caps()).requires_reconsent is False

    cases = {
        "allowed-tools added": _caps(allowed_tools=frozenset({"Read", "Bash"})),
        "allowed-tools removed": _caps(allowed_tools=frozenset()),
        "SKILL.md digest": _caps(skill_digest=DIGEST_B),
        "skills added": _caps(skill_identities=frozenset({"alpha", "beta"})),
        "skills removed": _caps(skill_identities=frozenset()),
        "payload changed": _caps(payload_digests={"scripts/run.py": DIGEST_B}),
        "payload added": _caps(
            payload_digests={"scripts/run.py": DIGEST_A, "evals/e.md": DIGEST_B}
        ),
        "payload removed": _caps(payload_digests={}),
        "boundaries widened": _caps(
            boundaries=frozenset({"filesystem_read", "network"})
        ),
        "boundaries narrowed": _caps(boundaries=frozenset()),
        "credentialed changed": _caps(credentialed=True),
        "credentialed absent": _caps(credentialed=None),
    }
    for label, candidate in cases.items():
        delta = compare_capabilities(baseline, candidate)
        assert delta.requires_reconsent, label
        assert delta.differences, label


def test_declared_to_undeclared_is_named_as_a_widening():
    # AC30 — absence is the `undeclared (unrestricted)` state, and it is named
    # in the addition set. Treating it as "no tools" would report the widest
    # possible change as a narrowing.
    delta = compare_capabilities(_caps(), _caps(allowed_tools=None))
    joined = " ".join(delta.differences)
    assert UNDECLARED_TOOLS in joined
    assert "added" in joined, "losing the declaration widens, it does not narrow"

    # And the reverse direction is a narrowing that is still re-consented.
    reverse = compare_capabilities(_caps(allowed_tools=None), _caps())
    assert reverse.requires_reconsent
    assert UNDECLARED_TOOLS in " ".join(reverse.differences)


def test_only_changed_tools_are_named():
    # AC30 — name every difference and no unchanged tool.
    delta = compare_capabilities(
        _caps(allowed_tools=frozenset({"Read", "Grep"})),
        _caps(allowed_tools=frozenset({"Read", "Bash"})),
    )
    joined = " ".join(delta.differences)
    assert "Bash" in joined and "Grep" in joined
    assert "Read" not in joined, "an unchanged tool is never listed"


def test_unknown_drift_refuses_even_with_the_flag():
    # AC30 — when the installed projection cannot be read back losslessly the
    # answer is `unknown`, not "no change". A comparison against data we could
    # not read would approve anything.
    delta = compare_capabilities(None, _caps())
    assert delta.unknown is True
    assert delta.requires_reconsent is True
    with pytest.raises(DirectStateError) as raised:
        accept_capability_pin(delta, "any", "any")
    assert "einstall" in str(raised.value)


def test_the_pin_ties_acceptance_to_the_displayed_changes():
    # AC30 — a local accepting run supplies the refusal-printed pin and refuses
    # if the recomputed pin differs. Without that tie, a flag typed after
    # reading one refusal accepts whatever the source holds on the next run.
    first = compare_capabilities(_caps(), _caps(allowed_tools=frozenset({"Read", "Bash"})))
    second = compare_capabilities(_caps(), _caps(allowed_tools=frozenset({"Read", "Shell"})))
    pin_first = capability_pin(first)
    pin_second = capability_pin(second)
    assert pin_first != pin_second

    accept_capability_pin(first, pin_first, pin_first)
    with pytest.raises(DirectStateError) as raised:
        accept_capability_pin(first, pin_first, pin_second)
    assert "does not match" in str(raised.value)

    # The pin is stable for an unchanged difference set.
    assert capability_pin(first) == pin_first


def test_unchanged_capabilities_need_no_flag():
    # AC30 — unchanged capabilities proceed under the applicable confirmation
    # rule without the flag.
    delta = compare_capabilities(_caps(), _caps())
    assert delta.requires_reconsent is False
    assert delta.differences == ()
