"""Content pins for the grant path in author-delivery-brief continue mode."""

import json
from pathlib import Path

CORE = Path(__file__).resolve().parents[3]
SKILL_DIR = CORE / ".apm" / "skills" / "author-delivery-brief"
SKILL = SKILL_DIR / "SKILL.md"
EVALS = SKILL_DIR / "evals" / "evals.json"


def _grant_section() -> str:
    """The folded text of continue stage 5, the grant path."""
    text = " ".join(SKILL.read_text(encoding="utf-8").split())
    return text.split("### 5. Offer the grant path", 1)[1].split("## Delivery map", 1)[0]


def test_default_path_commit_rule_and_stays_default() -> None:
    """Default path lands the Spec map change in its own change; separate stops stay default."""
    text = " ".join(SKILL.read_text(encoding="utf-8").split())
    assert "holding only that brief edit and the added rows' new `Draft` `spec.md` and `Drafting` `plan.md`" in text
    assert "A knowledge capture lands in its own change" in text
    assert "The separate stops above stay the default" in _grant_section()


def test_three_separate_answers_and_write_outcomes() -> None:
    """One stop, three yes-or-no questions, and the write outcome for each no."""
    s = _grant_section()
    assert "shaping review's `Clean` covers the proposed slice cut" in s
    assert "three separate yes-or-no questions" in s
    assert "A \"no\" writes nothing" in s
    assert "A \"no\" writes `Status: Ready` only" in s
    assert "A \"no\" writes `Status: Ready` and the confirmed Spec map rows only" in s
    assert "No answer on the grant path invokes `new-spec`" in s
    assert "Only confirmed slices enter the Spec map" in s
    assert "already `Ready` or `Executing`" in s and "asks only the grant question" in s
    assert "first added or renewed" in s


def test_display_disclosures_and_write_order() -> None:
    """The display list, grant-file format, every limit, and the write discipline."""
    s = _grant_section()
    for phrase in (
        "full brief text the grant will bind to, its Spec map included",
        "docs/product/run-grants/<slug>.toml",
        "schema_version", "confirmed_by", "confirmed_at", "expires_at", "done_when", "slices",
        "retry_budget", "max_slices_in_flight = 1", "held_actions",
        "at most 14 days after confirmed_at",
        "standing orders, or that there are none",
        "fixed human-only list", "held actions",
        "spend is unbounded", "expiry follows the runner host's clock",
        "only after a reviewed merge of a change holding only grant changes",
        "can move the base and remove or rewrite the grant",
        "required check that the change cannot edit",
        "nothing guards grant changes",
        "Direct pushes and bypassed checks skip the guard",
        "can redefine what a grant is",
        "bound unless the reviewer catches it",
        "re-binds",
        "judged by its own copy",
        "Name no repository-specific workflow",
        "byte for byte",
        "Write the grant file before the brief",
        "- **Run grant:** required (confirmed YYYY-MM-DDTHH:MM:SSZ)",
        "non-dispatchable reconciliation finding",
    ):
        assert phrase in s, phrase
    assert "build-check" not in s


def test_evals_cover_grant_path_and_renewal() -> None:
    """The eval file carries the grant-path and renewal cases."""
    cases = {c["id"]: c for c in json.loads(EVALS.read_text(encoding="utf-8"))["evals"]}
    path = " ".join(cases["grant-path-three-answers-and-disclosures"]["assertions"])
    assert "three separate" in path and "no grant file" in path
    renewal = " ".join(cases["grant-renewal-on-executing-brief"]["assertions"])
    assert "full brief text" in renewal and "only the grant question" in renewal
