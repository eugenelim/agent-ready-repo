"""T13: behavior-pinning grep tests for the adapt-to-project skill body.

Co-locating skill-body tests under the CLI's tests/ tree is a
deliberate Concern-13 deferral (plan.md, line ~50): a pack-level
test harness lands in a future spec. Until then these tests sit
alongside CLI tests so a single `pytest packages/agentbundle/`
covers them.

Per AC1: the body must contain five behavior-pinning literal strings.
Per AC23 / T17 (split-into-two prompt): two additional literal
phrases pin the cross-scope restructure contract.

The body is asserted against `packs/core/.apm/skills/adapt-to-project/SKILL.md`
(the source-of-truth). The projected copy at
`.claude/skills/adapt-to-project/SKILL.md` is verified byte-identical
under `make build-self` / `make build-check`.
"""

from __future__ import annotations

from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).parent.parent.parent.parent.parent
SKILL_BODY = (
    REPO_ROOT
    / "packs"
    / "core"
    / ".apm"
    / "skills"
    / "adapt-to-project"
    / "SKILL.md"
)


@pytest.fixture(scope="module")
def body() -> str:
    assert SKILL_BODY.exists(), (
        f"adapt-to-project SKILL.md not found at {SKILL_BODY}"
    )
    return SKILL_BODY.read_text(encoding="utf-8")


# ── AC1 grep set ─────────────────────────────────────────────────────────────


def test_body_names_shell_out_command(body):
    """AC1 grep #1: literal shell-out command."""
    assert (
        "agentbundle adapt --values-from <repo>/.adapt-discovery.toml"
        in body
    )


def test_body_names_doctrinal_self_check(body):
    """AC1 grep #2: literal doctrinal self-check command."""
    assert (
        "python3 -c \"import tomllib; tomllib.loads(open('<path>').read())\""
        in body
    )


def test_body_names_path_jail_rule(body):
    """AC1 grep #3: literal per-scope jail rule."""
    assert "never write outside the adopter's per-scope jail" in body.lower()


def test_body_names_dirty_state_command(body):
    """AC1 grep #4: literal repo-scope dirty-state escalation command."""
    assert "git status --porcelain" in body


def test_body_pre_flight_section_references_user_scope_state(body):
    """AC1 grep #5: Pre-flight section names ~/.agent-ready/, state.toml,
    and Tier-2 (multi-token behavioural check)."""
    # Locate the Pre-flight section bounded by the next H2 heading.
    lower = body
    start = lower.find("## Pre-flight")
    assert start >= 0, "Pre-flight section missing"
    # End at next H2 heading.
    end = lower.find("\n## ", start + 1)
    section = lower[start:end] if end >= 0 else lower[start:]
    assert "~/.agent-ready/" in section
    assert "state.toml" in section
    assert "Tier-2" in section


# ── AC23 / T17 grep set ───────────────────────────────────────────────────────


def test_body_names_split_into_two_prompt(body):
    """T17: SKILL.md body contains the literal phrase
    `split into two same-scope operations` exactly once and within
    the Class 3 section bounded by the next H2 (tightened per
    quality-review concern 11)."""
    assert body.count("split into two same-scope operations") == 1
    start = body.find("## Class 3")
    assert start >= 0, "Class 3 section missing"
    end = body.find("\n## ", start + 1)
    section = body[start:end] if end >= 0 else body[start:]
    assert "split into two same-scope operations" in section


def test_body_forbids_cross_scope_execution(body):
    """T17: SKILL.md body contains the literal phrase
    `cross-scope restructure is never executed as a single move`."""
    assert "cross-scope restructure is never executed as a single move" in body


def test_body_pre_flight_names_v01_migration_prereq(body):
    """Quality-review pin for AC22 v0.1 detection sub-clause:
    the SKILL.md body's Pre-flight section names
    `agentbundle init-state --migrate` as the prereq for write
    operations against legacy state files."""
    start = body.find("## Pre-flight")
    assert start >= 0, "Pre-flight section missing"
    end = body.find("\n## ", start + 1)
    section = body[start:end] if end >= 0 else body[start:]
    assert "agentbundle init-state --migrate" in section


# ── Class-2 four-outcome contract (spec ↔ body coherence guard) ──────────────


def test_body_class_2_section_names_all_four_outcomes(body):
    """The skill body's Class 2 section MUST enumerate all four
    outcomes — accept / edit / skip / decline.

    Background: an earlier version of `spec.md` Boundaries § class 2
    listed only three outcomes (accept / edit / skip, with skip
    recording under `[[findings.declined]]`); the SKILL.md body had
    the more nuanced four-outcome model (skip = leave on disk no
    recording, decline = record). The matrix's class-2 simulated
    captures exposed the drift; the spec was amended to match the
    body. This grep guards against silent re-divergence: any future
    edit to the Class 2 section that drops an outcome or conflates
    skip with decline trips this test.

    Scope is tightened to the Class 2 section (bounded by next H2)
    so an outcome word mentioned elsewhere doesn't satisfy the grep
    by accident.
    """
    start = body.find("## Class 2")
    assert start >= 0, "Class 2 section missing"
    end = body.find("\n## ", start + 1)
    section = body[start:end] if end >= 0 else body[start:]

    for outcome in ("accept", "edit", "skip", "decline"):
        assert outcome in section.lower(), (
            f"Class 2 section is missing the `{outcome}` outcome; "
            f"all four (accept / edit / skip / decline) must be "
            f"documented per spec.md Boundaries § class 2."
        )


def test_body_class_2_skip_and_decline_are_distinct(body):
    """The skill body's Class 2 section MUST distinguish *skip*
    (leave on disk, no recording, re-surface next session) from
    *decline* (leave on disk, record under `[[findings.declined]]`,
    don't re-propose).

    Background: same root cause as
    `test_body_class_2_section_names_all_four_outcomes` — the spec
    used to conflate them. A literal grep on the body's skip-clause
    + decline-clause guards against conflation; the recording-rule
    distinction is the load-bearing semantic difference between
    "decide later" and "never offer this again".
    """
    start = body.find("## Class 2")
    assert start >= 0, "Class 2 section missing"
    end = body.find("\n## ", start + 1)
    section = body[start:end] if end >= 0 else body[start:]

    # skip clause: leave on disk, no recording.
    assert "leave companion on disk" in section.lower(), (
        "Class 2 section must document skip as leaving the companion "
        "on disk for a future session"
    )
    # decline clause: recording under [[findings.declined]].
    assert "findings.declined" in section, (
        "Class 2 section must document decline as recording under "
        "[[findings.declined]] in that scope's discovery file"
    )


# ── AC15 / AC26 proactive cache-scan grep set (T6) ───────────────────────────


def test_skill_body_names_proactive_cache_scan_heading(body):
    """AC15 grep #1: literal heading `Proactive cache scan.`
    (case- and punctuation-sensitive) must appear in the skill body."""
    assert "Proactive cache scan." in body


def test_skill_body_names_cache_path(body):
    """AC15 grep #2: literal path `~/.claude/plugins/cache/` must
    appear verbatim in the skill body."""
    assert "~/.claude/plugins/cache/" in body


def test_skill_body_names_idempotence_clause(body):
    """AC15 grep #3: literal phrase `do not double-adapt` must appear
    verbatim in the skill body."""
    assert "do not double-adapt" in body


def test_skill_body_names_dedupe_rule(body):
    """AC15 grep #4: operative dedupe rule must appear verbatim —
    pins the text the LLM reads so a future SKILL.md rewrite cannot
    drift past it."""
    assert (
        "if a marker entry is present, do not synthesise a second adaptation"
        in body
    )


def test_skill_body_names_stale_entry_drop(body):
    """AC26 grep: literal phrase `silently drops the entry` must appear
    verbatim in the skill body (stale-entry drop-on-read contract)."""
    assert "silently drops the entry" in body


def test_skill_body_preflight_section_carries_six_steps(body):
    """Behavioural: the Pre-flight section numbered list must have
    exactly six top-level numbered items (1-5 existing + new step 6).
    Guards against accidentally dropping one of the existing five
    while editing."""
    import re

    start = body.find("## Pre-flight")
    assert start >= 0, "Pre-flight section missing"
    end = body.find("\n## ", start + 1)
    section = body[start:end] if end >= 0 else body[start:]
    numbered = re.findall(r"^\d+\.\s+\*\*", section, re.MULTILINE)
    assert len(numbered) == 6, (
        f"Expected 6 numbered steps in Pre-flight section, found "
        f"{len(numbered)}: {numbered}\nSection head: {section[:200]!r}"
    )
