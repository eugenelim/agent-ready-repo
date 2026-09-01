"""Contract tests for non-gating Nit review dispositions."""

import re
from pathlib import Path

PACK_ROOT = Path(__file__).resolve().parents[3]
WORK_LOOP = PACK_ROOT / ".apm/skills/work-loop/SKILL.md"
VERDICT = PACK_ROOT / ".apm/skills/work-loop/references/review-verdict-record.md"
ADJUDICATION = PACK_ROOT / ".apm/skills/work-loop/references/finding-adjudication.md"
REVIEWERS = (
    PACK_ROOT / ".apm/agents/adversarial-reviewer.md",
    PACK_ROOT / ".apm/agents/quality-engineer.md",
    PACK_ROOT / ".apm/agents/security-reviewer.md",
)


def _section(path: Path, heading: str) -> str:
    """Return exactly one Markdown section, refusing anything ambiguous.

    Every scoped assertion in this file depends on this helper, so it fails loudly
    rather than silently narrowing. A substring search would match the heading
    text in prose and would quietly pick the first of several duplicates — either
    would point every guard at the wrong region at once.
    """
    text = path.read_text(encoding="utf-8")
    level = len(heading) - len(heading.lstrip("#"))
    starts = [m.start() for m in re.finditer(rf"^{re.escape(heading)}\s*$", text, re.M)]
    assert len(starts) == 1, f"{path}: {heading!r} matched {len(starts)} heading lines"
    start = starts[0]
    # Close on a heading at the same level or shallower, so an H3 inside an H2
    # stays part of its parent section.
    nxt = re.search(rf"^#{{1,{level}}} ", text[start + len(heading):], re.M)
    return text[start:] if nxt is None else text[start : start + len(heading) + nxt.start()]


def test_unacted_nit_state_precedence_and_citation() -> None:
    precedence = _section(VERDICT, "## State precedence")
    eligibility = _section(VERDICT, "## Residual eligibility")
    shapes = _section(VERDICT, "## Nested shapes")

    # "Unacted Nit" must be defined, not assumed. Without both severities pinned,
    # a promoted Nit (`effective_severity: concern`) can be called an unacted Nit
    # and escape gating — which defeats the promotion rule entirely.
    assert "An **unacted Nit** is row 1 only: `status: deferred` with **both** `severity`" in precedence
    assert "and `effective_severity` equal to `nit`, carrying its citation." in precedence
    # The gating rows a promotion depends on.
    assert "| `deferred` | `blocker` or `concern` | any | `BLOCKED`" in precedence
    assert "| `unresolved` | `concern` | any | `CHANGES_REQUIRED` |" in precedence
    assert "| `deferred` | `nit` | **missing** | `BLOCKED` — silent suppression |" in precedence
    assert "`effective_severity` decides\ngating, never the reviewer's `severity`" in precedence
    # The un-narrowed rule must be gone, not merely supplemented. A contradictory
    # restatement elsewhere in the section is the realistic regression.
    assert "— a finding still requires action.\n" not in precedence

    # Residual eligibility defers to the table rather than restating it, so the
    # two cannot drift apart.
    assert "an unacted Nit\nas the disposition table defines it qualifies" in eligibility
    assert "or a Nit absent from the\nrecord or missing its citation never qualifies" in eligibility

    # A deferred Nit skips adjudication by design, so `findings[]` must admit it.
    # The unqualified adjudicator-only rule would make AC3.3 and AC3.5 impossible
    # to satisfy at the same time.
    assert "Only sustained findings from" not in shapes
    assert "Nit-only raw report deferred without dispatch enters it" in shapes
    assert "Every other non-clean report still reaches this array only through\n  adjudication." in shapes


def test_decide_promotes_a_mutated_nit_before_editing() -> None:
    decide = _section(WORK_LOOP, "## Step 5. DECIDE")
    verdict_schema = _section(VERDICT, "## Nested shapes")
    assert "**Nits** → never fix automatically." in decide
    # The superseded combined rule treated Nits exactly like Concerns. Re-adding
    # it beside the new one makes DECIDE contradictory without deleting anything.
    assert "**Concerns and Nits** → apply now only when their inclusion is authorized by" not in decide
    assert "adjudicate only when the thread intends to\n  mutate" in decide
    assert "Before any edit, promote `effective_severity` to at least Concern if\n  its intended repair changes behavior, architecture, dependencies, or more than one file." in decide
    assert "`effective_severity` equals it unless DECIDE\n  promotes a Nit before acting on a repair that crosses its blast-radius rule." in verdict_schema


def test_nit_only_report_skips_dispatch_unless_mutation_is_intended() -> None:
    gateway = _section(WORK_LOOP, "### Finding-adjudication gateway")
    protocol = _section(ADJUDICATION, "# Finding-adjudication path protocol")
    assert "unless the report is Nit-only and the\nthread does not intend to mutate" in gateway
    assert "An intended Nit mutation requires adjudication." in gateway
    assert "except a Nit-only\nreport the implementation thread does not intend to mutate" in protocol
    assert "intended Nit mutations require dispatch." in protocol
    # Both dispatch sites previously stated an unconditional rule. Either one
    # restored alongside the new text re-mandates dispatch for a deferred Nit.
    assert "`findings` dispatches\nthe adjudicator" not in gateway
    assert "Use this reference for every raw report classified `findings`. Pre-EXECUTE" not in protocol


def test_review_and_finish_allow_deferred_nits_but_not_unresolved_concerns() -> None:
    review = _section(WORK_LOOP, "## Step 4. REVIEW")
    finish = _section(WORK_LOOP, "## Finish checklist")
    assert "until no unresolved Blocker or Concern remains." in review
    # The eighth superseded site. Re-added beside the new line it restores the
    # deadlock, because a Nit-only report never returns the literal sentinel.
    assert (
        "iterate `adversarial-reviewer` until its direct or adjudicated "
        "main-loop result returns `Clean — ready to commit.`"
    ) not in review
    assert "has no unresolved Blocker or Concern" in finish
    assert "every unacted Nit is deferred with its citation" in finish
    # Finish and verdict mode semantics each carried a literal-clean condition a
    # Nit-only report can never satisfy.
    assert "returned `Clean — ready to commit.` or, only when non-mandatory" not in finish
    mode_semantics = _section(VERDICT, "## Mode semantics are unchanged")
    assert "Full mode still iterates every warranted reviewer to clean." not in mode_semantics
    assert "until no unresolved Blocker or\nConcern remains" in mode_semantics

    # The completion transition is the deadlock site: a Nit-only report
    # classifies `findings`, skips adjudication, and never becomes "clean", so a
    # transition keyed on "clean" can never fire for it.
    transition = _section(WORK_LOOP, "## Step 4. REVIEW")
    assert "carrying only deferred Nits recorded with their citations" in transition
    assert (
        "**When every warranted mandatory reviewer is clean and every "
        "non-mandatory reviewer is clean or a named skip**"
    ) not in transition


def test_every_reviewer_points_to_decide_for_nit_promotion() -> None:
    severity_starts = {
        "adversarial-reviewer.md": "Some orchestrators prefer",
        "quality-engineer.md": "## Severity guidance",
        "security-reviewer.md": "## When in doubt about severity",
    }
    for reviewer in REVIEWERS:
        text = reviewer.read_text(encoding="utf-8")
        severity_start = text.index(severity_starts[reviewer.name])
        severity_end = text.find("\n## ", severity_start + 1)
        severity = text[severity_start:] if severity_end == -1 else text[severity_start:severity_end]
        assert "For Nit repair severity promotion, follow `work-loop` SKILL.md § DECIDE." in severity
