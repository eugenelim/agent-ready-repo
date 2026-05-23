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
    `split into two same-scope operations` exactly once."""
    assert body.count("split into two same-scope operations") == 1


def test_body_forbids_cross_scope_execution(body):
    """T17: SKILL.md body contains the literal phrase
    `cross-scope restructure is never executed as a single move`."""
    assert "cross-scope restructure is never executed as a single move" in body
