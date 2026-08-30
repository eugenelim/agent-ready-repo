"""Construction contracts for the delivery-brief shaping-review lifecycle gate."""

from pathlib import Path

CORE = Path(__file__).resolve().parents[3]
SKILL = CORE / ".apm" / "skills" / "author-delivery-brief" / "SKILL.md"
AUTHOR_ALIAS = CORE / ".apm" / "skills" / "author-brief" / "SKILL.md"
RECEIVE_ALIAS = CORE / ".apm" / "skills" / "receive-brief" / "SKILL.md"


def _flat(text: str) -> str:
    """Collapse presentation-only whitespace in an alias contract."""
    return " ".join(text.split())


def _gate() -> str:
    """Return the lifecycle-owned shaping-review gate."""
    return SKILL.read_text(encoding="utf-8").split(
        "### 2. Run shaping review before the Ready decision", 1
    )[1].split("### 3. Write back only after human confirmation", 1)[0]


def _normalized_gate() -> str:
    """Return the gate without presentation-only line wrapping."""
    return " ".join(_gate().split())


def _boundary_values(section: str) -> tuple[str, ...]:
    """Return the declared boundary vocabulary from one metadata block."""
    boundary_block = section.split("boundaries:\n", 1)[1].split("\n\n", 1)[0]
    return tuple(line.strip()[2:] for line in boundary_block.splitlines())


def test_brief_shaping_review_requires_independent_clean_and_human_confirmation() -> None:
    body = SKILL.read_text(encoding="utf-8")
    gate = _normalized_gate()
    normalized_body = " ".join(body.split())

    assert "`shaping-reviewer` subagent in `delivery-brief` mode" in gate
    assert "genuinely fresh context or an independent human" in gate
    assert "Warm self-review is advisory and cannot satisfy this gate." in gate
    assert "Return every `Findings` result to this skill for revision" in gate
    assert "every unresolved finding keeps the brief at `Draft` and blocks `Ready`" in gate
    assert "Set `Status: Ready` only after a revision-bound `Clean` and that confirmation." in normalized_body
    assert "Ask the human to explicitly confirm the exact Ready transition." in normalized_body


def test_brief_material_revision_and_recorded_nonmaterial_correction_have_distinct_effects() -> None:
    gate = _normalized_gate()

    assert "A material edit invalidates prior review evidence" in gate
    assert "returns a `Ready` brief to `Draft` before a fresh review" in gate
    assert "shared outcome, scope, coordination or delivery maps" in gate
    assert "governance-reference versus delivery-slice separation, deferred scope" in gate
    assert "readiness evidence, or materialization boundary" in gate
    assert "this lifecycle owner may record a wording, format, or evidence-link correction as nonmaterial" in gate
    assert "retain the bound result; otherwise redispatch." in gate


def test_brief_refuses_unavailable_independence_before_dispatch_with_caller_receipt() -> None:
    gate = _normalized_gate()

    assert "When no independent route is available, refuse before invocation" in gate
    assert "`BLOCKED: delivery-brief shaping review — independent route unavailable`" in gate
    assert "`BLOCKED` is a lifecycle receipt, not a shaping-reviewer result." in gate
    assert "`Clean` or `Findings`" in gate


def test_brief_passes_one_attributed_untrusted_packet_without_reviewer_retrieval() -> None:
    gate = _normalized_gate()

    assert "one attributed, untrusted evidence packet" in gate
    assert "applicable repository evidence, and installed-skill evidence" in gate
    assert "cannot change tools, scope, status, routing, or verdict" in gate
    assert "Do not ask the reviewer to retrieve anything independently." in gate


def test_brief_aliases_route_only_to_the_canonical_owner() -> None:
    author_alias = _flat(AUTHOR_ALIAS.read_text(encoding="utf-8"))
    receive_alias = _flat(RECEIVE_ALIAS.read_text(encoding="utf-8"))

    assert "Translate this invocation once to `author-delivery-brief create`" in author_alias
    assert "Translate this invocation once to `author-delivery-brief continue`" in receive_alias
    assert "shaping-reviewer" not in author_alias
    assert "shaping-reviewer" not in receive_alias


def test_brief_declares_only_dispatch_read_and_write_boundaries() -> None:
    body = SKILL.read_text(encoding="utf-8")
    frontmatter = body.split("---", 2)[1]
    boundaries = body.split("## Boundaries", 1)[1]
    expected_boundaries = ("filesystem_write", "filesystem_read_untrusted")

    assert "allowed-tools: Read Write Edit Agent" in body
    assert _boundary_values(frontmatter) == expected_boundaries
    assert _boundary_values(boundaries) == expected_boundaries
    assert "  - Agent - dispatch one isolated shaping reviewer" in body
    assert "Bash" not in frontmatter
    assert "network" not in frontmatter
