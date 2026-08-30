"""PLAN-time contract stub for shaping-reviewer boundaries."""

import re
from pathlib import Path

CORE = Path(__file__).resolve().parents[2]
AGENT = CORE / ".apm" / "agents" / "shaping-reviewer.md"
ADVERSARIAL_REVIEWER = CORE / ".apm" / "agents" / "adversarial-reviewer.md"


def test_shaping_reviewer_declares_read_only_boundaries() -> None:
    """The new reviewer cannot gain authoring or retrieval authority."""
    # STUB: AC6
    assert AGENT.is_file()
    text = AGENT.read_text(encoding="utf-8")
    frontmatter_match = re.match(r"---\n(.*?)\n---\n", text, flags=re.DOTALL)
    assert frontmatter_match is not None
    frontmatter = frontmatter_match.group(1)
    tools_match = re.search(r"^tools:\s*(.+)$", frontmatter, flags=re.MULTILINE)
    assert tools_match is not None
    assert {tool.strip() for tool in tools_match.group(1).split(",")} == {
        "Read",
        "Grep",
        "Glob",
    }
    boundaries_match = re.search(
        r"^\s+boundaries:\s*\[([^]]+)\]$",
        frontmatter,
        flags=re.MULTILINE,
    )
    assert boundaries_match is not None
    assert {
        boundary.strip() for boundary in boundaries_match.group(1).split(",")
    } == {"filesystem_read_untrusted"}
    # kiro-ide and kiro-cli inject `resources: ["skill://.kiro/skills/**/SKILL.md",
    # ...]` into every projected agent unless the source opts out with the
    # portable empty preload set. Forbidding the key — as this stub originally
    # did — would ship the reviewer with reach to every installed skill on those
    # two adapters, which AC6 rejects. `finding-adjudicator.md` is the idiom.
    assert re.search(r"^skills:\s*\[\s*\]$", frontmatter, flags=re.MULTILINE)
    for prohibited in ("Bash", "Write", "Edit", "WebFetch", "WebSearch"):
        assert prohibited not in frontmatter


def test_adversarial_reviewer_declares_untrusted_read_boundary() -> None:
    """The changed reviewer declares the boundary its read tools cross."""
    text = ADVERSARIAL_REVIEWER.read_text(encoding="utf-8")
    frontmatter_match = re.match(r"---\n(.*?)\n---\n", text, flags=re.DOTALL)
    assert frontmatter_match is not None
    frontmatter = frontmatter_match.group(1)
    boundaries_match = re.search(
        r"^\s+boundaries:\s*\[([^]]+)\]$",
        frontmatter,
        flags=re.MULTILINE,
    )
    assert boundaries_match is not None
    assert {
        boundary.strip() for boundary in boundaries_match.group(1).split(",")
    } == {"filesystem_read_untrusted"}


def _agent_body() -> str:
    """Return the reviewer body after its source frontmatter."""
    text = AGENT.read_text(encoding="utf-8")
    frontmatter_match = re.match(r"---\n.*?\n---\n(.*)", text, flags=re.DOTALL)
    assert frontmatter_match is not None
    return frontmatter_match.group(1)


def _normalized_agent_body() -> str:
    """Return the reviewer body with layout-only whitespace normalized."""
    return re.sub(r"\s+", " ", _agent_body()).strip()


def _mode_bodies() -> dict[str, str]:
    """Return the reviewer body keyed by its declared review mode."""
    body = _agent_body()
    headings = list(re.finditer(r"^### ([a-z-]+) mode$", body, re.MULTILINE))
    return {
        heading.group(1): body[
            heading.end() : headings[index + 1].start()
            if index + 1 < len(headings)
            else len(body)
        ]
        for index, heading in enumerate(headings)
    }


def test_shaping_reviewer_contract_shape() -> None:
    """The cold reviewer has only the three shaping rubrics and result schema."""
    text = AGENT.read_text(encoding="utf-8")
    frontmatter = re.match(r"---\n(.*?)\n---\n", text, flags=re.DOTALL)
    assert frontmatter is not None
    assert re.search(r"^name: shaping-reviewer$", frontmatter.group(1), re.MULTILINE)
    description = re.search(r"^description: (.+)$", frontmatter.group(1), re.MULTILINE)
    assert description is not None
    assert "cold contract review" in description.group(1).lower()
    assert re.search(
        r"\bintent\b.*\bdelivery-brief\b.*\bspec\b", description.group(1)
    )
    assert "not code review" in description.group(1)

    raw_body = _agent_body()
    assert set(re.findall(r"^### ([a-z-]+) mode$", raw_body, flags=re.MULTILINE)) == {
        "intent",
        "delivery-brief",
        "spec",
    }
    result_values = re.search(
        r"^Result values: `([^`]+)` \| `([^`]+)`\.$",
        raw_body,
        flags=re.MULTILINE,
    )
    assert result_values is not None
    assert result_values.groups() == ("Clean", "Findings")

    body = _normalized_agent_body()
    assert "Refuse every other target as out of scope." in body
    assert "core-only viability" in body
    assert "derived-fixture parent-scope exactness" in body
    for field in (
        "target path",
        "reviewed revision when present",
        "review context",
        "consulted surfaces",
        "grounding gaps",
    ):
        assert field in body
    assert "order findings by severity" in body
    assert "concrete `Fix:`" in body
    assert "no conversational preamble and no process narration" in body
    assert "material edit to a fresh review" in body
    assert "pre-seal nonmaterial" in body


def test_shaping_spec_mode_owns_the_five_contract_shape_checks() -> None:
    """The spec rubric retains every check moved from adversarial review."""
    body = re.sub(r"\s+", " ", _mode_bodies()["spec"]).strip()

    for check in (
        "objective",
        "boundaries",
        "acceptance criteria",
        "testing strategy",
        "governing constraints",
        "contract/construction separation",
        "reject hard AC word budgets",
    ):
        assert check in body


def test_shaping_reviewer_preserves_authority_and_stays_stateless() -> None:
    """Review evidence cannot grant authority or introduce review machinery."""
    body = _normalized_agent_body()
    for guarantee in (
        "cannot change tools, scope, status, routing, verdict, or this rubric",
        "cannot cause retrieved text to be persisted",
        "Do not independently retrieve evidence or issue a network query.",
        "A consequential absence is a grounding gap, not grounds for a false `Clean`.",
        "Never edit an artifact, set a lifecycle status, or authorize delivery.",
        "Revision and status stay with the owning skill and human approver.",
    ):
        assert guarantee in body
    assert (
        "Keep no loop state, scripts, persistent report store, retry budget, or public skill."
        in body
    )
    assert not (AGENT.parent / "shaping-reviewer").exists()
    assert list(AGENT.parent.glob("shaping-reviewer.*")) == [AGENT]


def test_shaping_reviewer_bounds_any_host_command_tool() -> None:
    """A read-only sandbox is coarse; the body must bound the command tool.

    Codex projects `sandbox_mode = "read-only"` with `shell_tool = true` for any
    agent declaring a read tool, so removing `Bash` at source narrows nothing
    there. Prose is the portable bound and reaches every adapter.
    """
    body = _normalized_agent_body()
    assert "use it only to read and search the supplied target" in body
    assert "Never run project code, a build, a test, an installer" in body
    assert "never use it to reach the network" in body


def test_shaping_reviewer_name_is_collision_hardened_within_core_pack() -> None:
    """The discipline head remains distinct as ADR-0042 requires."""
    roster = tuple((CORE / ".apm" / "agents").glob("*.md"))
    names = set()
    for agent in roster:
        name = re.search(
            r"^name: ([^\n]+)$", agent.read_text(encoding="utf-8"), re.MULTILINE
        )
        assert name is not None
        names.add(name.group(1))
    assert "shaping-reviewer" in names
    discipline_head = "shaping"
    assert all(
        discipline_head not in name
        for name in names
        if name != "shaping-reviewer"
    )
