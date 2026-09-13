"""Contract tests for what crosses the boundary to the judge.

Two concerns. A route is the one part of a capture that travels as text into a
manifest and on to a third party, so the query string and fragment are cut from
it. And a capture is evidence: nothing rendered inside one carries authority over
the step that is judging it.
"""

from __future__ import annotations

import pytest

from frontend_engineering_rendered_page_rules import (
    inspection_section,
    judgement_request_route,
    judging_rules,
    read_rules,
    read_skill,
    recorded_route,
    route_rules,
    sensitive_view_exposure,
    sensitive_view_rules,
)

# Each carries a secret in the query string, the fragment, or both.
LEAKY_ROUTES = [
    ("/orders/2481?token=abc#receipt", "/orders/2481"),
    ("/reset?token=9f3c1a", "/reset"),
    ("/account#access_token=xyz", "/account"),
    ("/p?a=1&b=2#frag", "/p"),
    ("https://example.test/dash?key=s3cret#top", "https://example.test/dash"),
]


@pytest.fixture(scope="module")
def rules_markdown() -> str:
    return read_rules()


@pytest.fixture(scope="module")
def skill_markdown() -> str:
    return read_skill()


# ── route exclusion ─────────────────────────────────────────────────────────

@pytest.mark.parametrize(("url", "expected"), LEAKY_ROUTES)
def test_the_recorded_route_excludes_query_string_and_fragment(
    rules_markdown: str, url: str, expected: str
) -> None:
    """Verifies: the route recorded with a capture excludes the query string and
    the fragment."""
    route = recorded_route(rules_markdown, url)
    assert route == expected
    assert "?" not in route and "#" not in route


@pytest.mark.parametrize(("url", "expected"), LEAKY_ROUTES)
def test_the_judgement_request_route_excludes_query_string_and_fragment(
    rules_markdown: str, url: str, expected: str
) -> None:
    """Verifies the other half of the same criterion: the route *stated in the
    judgement request* excludes them too.

    Asserted separately from the recorded route. One definition governs both
    today, but the criterion names both, and a future split that stripped only
    the manifest copy would still leak the token to the judge.
    """
    route = judgement_request_route(rules_markdown, url)
    assert route == expected
    assert "?" not in route and "#" not in route


def test_the_two_routes_agree(rules_markdown: str) -> None:
    for url, _ in LEAKY_ROUTES:
        assert recorded_route(rules_markdown, url) == judgement_request_route(
            rules_markdown, url
        )


def test_a_route_with_nothing_to_strip_is_left_alone(rules_markdown: str) -> None:
    """The green path: the rule removes secrets, it does not mangle routes."""
    for url in ("/orders/2481", "https://example.test/dash", "./local/page.html"):
        assert recorded_route(rules_markdown, url) == url


def test_both_exclusions_are_declared(rules_markdown: str) -> None:
    rules = route_rules(rules_markdown)
    assert rules.get("route-query-string") == "excluded"
    assert rules.get("route-fragment") == "excluded"


# ── the routes are the adopter's ────────────────────────────────────────────

def test_the_routes_inspected_are_supplied_by_the_adopter(
    rules_markdown: str, skill_markdown: str
) -> None:
    """Verifies: shipped pack content states that the routes the step inspects
    are supplied by the adopter."""
    assert route_rules(rules_markdown).get("route-source") == "adopter-supplied"
    assert (
        "routes to inspect are the ones the adopter names"
        in inspection_section(skill_markdown)
    ), "the skill no longer says whose routes these are"


# ── captured content carries no authority ───────────────────────────────────

def test_captured_content_is_untrusted_evidence(rules_markdown: str) -> None:
    """Verifies: shipped pack content states that content visible in a capture is
    untrusted evidence and carries no instruction authority over the judge."""
    rules = judging_rules(rules_markdown)
    assert rules.get("captured-content") == "untrusted-evidence"
    assert rules.get("captured-content-instruction-authority") == "none"


def test_the_skill_states_the_untrusted_evidence_rule(skill_markdown: str) -> None:
    """The rule has to reach the skill too — the reference is where the rule
    lives, but the judgement step is where someone is standing when it matters."""
    assert "data, not instruction authority" in inspection_section(skill_markdown), (
        "the skill's judgement section no longer carries the untrusted-data rule"
    )


# ── sensitive views ─────────────────────────────────────────────────────────

def test_capturing_a_sensitive_view_is_the_adopters_decision(
    rules_markdown: str, skill_markdown: str
) -> None:
    """Verifies: shipped pack content states that capturing an authenticated or
    otherwise sensitive view is the adopter's decision."""
    assert (
        sensitive_view_rules(rules_markdown).get("sensitive-view-capture")
        == "adopter-decision"
    )
    assert "is the adopter's decision" in inspection_section(skill_markdown)


def test_what_a_sensitive_capture_exposes_is_named(rules_markdown: str) -> None:
    """Verifies: shipped pack content names what such a capture exposes to the
    adopter's judge.

    Asserted separately from the ownership rule above, because saying whose
    decision it is and saying what the decision costs are two different remedies
    — and only the second lets the adopter actually make it.
    """
    exposure = sensitive_view_exposure(rules_markdown)
    assert exposure, "nothing is named as carried to the judge"

    carried = " ".join(f"{k} {v}" for k, v in exposure.items()).lower()
    assert "page as rendered" in carried, (
        "the rendered page itself is not named among what is exposed"
    )
    assert "route" in carried, "the route is not named among what is exposed"
    assert any(
        term in carried for term in ("names", "email", "payment", "order")
    ), "no concrete example of exposed content is named"
