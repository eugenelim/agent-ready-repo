"""Roster check: the shipped skill text names `workspace-status` as repair only.

Two layers. The retired-token, description and phrase checks are the contract.
The sentence pin is design: it keeps a status question from being routed to
`workspace-status` in the skill text that sends readers there.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SKILLS = REPO_ROOT / "packs" / "core" / ".apm" / "skills"

RETIRED_TOKENS = (
    "workspace-status status",
    "workspace-status reconcile",
    "workspace-status explain",
    "selected-membership",
    "retirement-candidates",
    "repair-rollback",
    "--migration-selection",
    "prune --select",
)
RETIRED_DESCRIPTION_WORDS = (
    "orient",
    "what's ready",
    "session start",
    "show the queue",
    "prune",
)
PIN_WORDS = (
    "status",
    "queue",
    "orient",
    "orientation",
    "ready",
    "next",
    "eligibility",
    "reconciliation",
    "backlog",
)

OWN_SKILL = SKILLS / "workspace-status" / "SKILL.md"
OWN_MUTATE = SKILLS / "workspace-status" / "references" / "mutate.md"
OTHER_MARKDOWN = (
    SKILLS / "work-loop" / "SKILL.md",
    SKILLS / "work-intake" / "SKILL.md",
    SKILLS / "work-intake" / "references" / "lifecycle-index.md",
    SKILLS / "navigate-intents" / "SKILL.md",
    SKILLS / "close-work" / "SKILL.md",
    SKILLS / "intake-intent" / "SKILL.md",
    SKILLS / "author-delivery-brief" / "SKILL.md",
    SKILLS / "new-spec" / "references" / "spec-and-plan-contract.md",
)
LISTED_MARKDOWN = (OWN_SKILL, OWN_MUTATE, *OTHER_MARKDOWN)


def _collapse(text: str) -> str:
    return " ".join(text.split())


def _json_strings(value: object):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for item in value.values():
            yield from _json_strings(item)
    elif isinstance(value, list):
        for item in value:
            yield from _json_strings(item)


def retired_tokens_in(text: str) -> list[str]:
    collapsed = _collapse(text)
    return [token for token in RETIRED_TOKENS if token in collapsed]


def eval_json_files() -> list[Path]:
    return sorted(SKILLS.glob("*/evals/*.json"))


_BOUNDARY_LINE = re.compile(r"^\s*(#{1,6}\s|[-*+]\s|\d+[.)]\s)")
_SENTENCE_END = re.compile(r"(?<=[.!?])\s+")
_NAME = re.compile(r"(?<![A-Za-z0-9_-])workspace-status(?![A-Za-z0-9_-])")


def sentences(text: str) -> list[str]:
    """Split raw text at sentence ends, blank lines, headings and list items."""
    chunks: list[list[str]] = [[]]
    for line in text.splitlines():
        if not line.strip() or _BOUNDARY_LINE.match(line):
            chunks.append([])
        if line.strip():
            chunks[-1].append(line)
    found: list[str] = []
    for chunk in chunks:
        for part in _SENTENCE_END.split("\n".join(chunk)):
            collapsed = _collapse(part)
            if collapsed:
                found.append(collapsed)
    return found


def status_routing_sentences(text: str) -> list[str]:
    """Return sentences naming `workspace-status` beside a listed word."""
    words = re.compile(
        r"(?<![A-Za-z0-9_-])(?:" + "|".join(PIN_WORDS) + r")(?![A-Za-z0-9_-])",
        re.IGNORECASE,
    )
    return [s for s in sentences(text) if _NAME.search(s) and words.search(s)]


def description_of(skill_md: str) -> str:
    match = re.search(r"^description:\s*(.+)$", skill_md, flags=re.MULTILINE)
    assert match, "SKILL.md carries no description line"
    return match.group(1)


@pytest.mark.parametrize("path", LISTED_MARKDOWN, ids=lambda p: str(p.relative_to(SKILLS)))
def test_no_retired_token_in_markdown(path: Path) -> None:
    assert retired_tokens_in(path.read_text(encoding="utf-8")) == []


def test_no_retired_token_in_any_eval_string() -> None:
    files = eval_json_files()
    assert files, "no eval JSON found"
    offenders = [
        (str(path.relative_to(SKILLS)), token)
        for path in files
        for value in _json_strings(json.loads(path.read_text(encoding="utf-8")))
        for token in retired_tokens_in(value)
    ]
    assert offenders == []


def test_description_names_no_orientation_phrase() -> None:
    description = _collapse(description_of(OWN_SKILL.read_text(encoding="utf-8"))).lower()
    assert [w for w in RETIRED_DESCRIPTION_WORDS if w in description] == []


def test_work_loop_names_the_captured_listing() -> None:
    assert "dispatch.py --captured" in _collapse(
        (SKILLS / "work-loop" / "SKILL.md").read_text(encoding="utf-8")
    )


def test_work_intake_routes_status_to_navigate_intents() -> None:
    assert "Route status directly to `navigate-intents`" in _collapse(
        (SKILLS / "work-intake" / "SKILL.md").read_text(encoding="utf-8")
    )


@pytest.mark.parametrize("path", OTHER_MARKDOWN, ids=lambda p: str(p.relative_to(SKILLS)))
def test_no_sentence_routes_a_status_question_to_workspace_status(path: Path) -> None:
    assert status_routing_sentences(path.read_text(encoding="utf-8")) == []


# The checks above must fail on the text they replace.


def test_token_check_fails_on_a_base_sentence() -> None:
    base = "Run `workspace-status\nreconcile` to list stale entries."
    assert retired_tokens_in(base) == ["workspace-status reconcile"]
    assert retired_tokens_in("Run `prune --select docs/x`.") == ["prune --select"]


def test_description_check_fails_on_a_base_description() -> None:
    base = "description: Use this skill to orient at session start."
    assert "orient" in description_of(base).lower()


def test_pin_fails_on_base_sentences() -> None:
    assert status_routing_sentences("Run `workspace-status`\nto see open backlog items.")
    assert status_routing_sentences("- Route status directly to `workspace-status`.")
    assert status_routing_sentences("`workspace-status` reconciliation matches it.")


def test_pin_passes_repair_sentences_and_joined_words() -> None:
    assert not status_routing_sentences("Send it to the `workspace-status` `intent-brief-drop` repair.")
    assert not status_routing_sentences("Use `workspace-status` for the next-step list. Status is elsewhere.")
    assert not status_routing_sentences("Use workspace-status-extra for queue order.")
    assert not status_routing_sentences("- Repair with `workspace-status`.\n- The queue is elsewhere.")


# Records and release (AC-0019 to AC-0026): each check reads the record that
# owns the fact and fails if the named text is missing.

RFC_0106 = REPO_ROOT / "docs/rfc/0106-stop-registering-derivable-work.md"
RFC_0083 = REPO_ROOT / "docs/rfc/0083-work-intake-and-artifact-routing.md"
RECORD = REPO_ROOT / "docs/specs/workspace-retirement/retirement-record.md"
INVENTORY = REPO_ROOT / "docs/specs/workspace-retirement/inventory.toml"
BRIEF = REPO_ROOT / "docs/product/briefs/workspace-registry-retirement-delivery.md"
LEDGER = REPO_ROOT / "docs/specs/repair-only-workspace-status/notes/verification-ledger.md"
FRAGMENTS = REPO_ROOT / "docs/product/changelog.d"
ERRATA_LINK = "[RFC-0106 § Errata](../../rfc/0106-stop-registering-derivable-work.md#errata)"
SLUG = "repair-only-workspace-status"


def _flat(path: Path) -> str:
    return " ".join(path.read_text(encoding="utf-8").split())


def _section(text: str, heading: str) -> str:
    after = text.split(f"## {heading}", 1)[1]
    return after.split("\n## ", 1)[0]


def _errata_entry(path: Path, date: str) -> str:
    """The one errata bullet dated `date`."""
    section = _section(path.read_text(encoding="utf-8"), "Errata")
    bullets = [b for b in section.split("\n- ") if b.lstrip("*").startswith(date)]
    assert len(bullets) == 1, bullets
    return " ".join(bullets[0].split())


def test_ac0019_rfc0106_errata_names_every_removal() -> None:
    entry = _errata_entry(RFC_0106, "2026-11-02")
    for name in (
        "`status`", "`reconcile`", "`explain`", "`selected-membership`", "`prune`",
        "`retirement-candidates`", "`repair-rollback`", "`repair-plan --migration-selection`",
        "`[authorization.migration]`", "`contracts/jsonschema/spec-retirement-candidates.schema.json`",
        "`contracts/jsonschema/work-intake-migration-*.schema.json`", "`ini_slug`", "`shaping`",
        "`canonical`", "`<type>/<slug>`", "`unmigrated_workspace`",
    ):
        assert name in entry, name


def test_ac0020_rfc0083_points_to_the_rfc0106_entry() -> None:
    entry = _errata_entry(RFC_0083, "2026-11-02")
    assert "(0106-stop-registering-derivable-work.md#errata)" in entry
    assert "2026-11-02" in entry


_ROWS = {
    "the workspace-status orientation run": "accepted removal",
    "the delivery-artifact prune": "accepted removal",
    "the retirement-candidates report": "accepted removal",
    "the legacy migration apply and rollback": "accepted removal",
    "the MCP queue's initiative slug and shaping list": "accepted removal",
    "the MCP canonical reconciliation object": "accepted removal",
    "dispatch over unmigrated registry entries": "intended change",
    "dispatch from headers alone": "reproduced",
}


@pytest.mark.parametrize("case", sorted(_ROWS))
def test_ac0021_equivalence_row(case: str) -> None:
    rows = [
        [cell.strip() for cell in line.strip("|").split("|")]
        for line in _section(RECORD.read_text(encoding="utf-8"), "Equivalence").splitlines()
        if line.startswith(f"| `{case}` |")
    ]
    assert len(rows) == 1, rows
    _, slice_, result, _, authority = rows[0]
    expected = "none" if _ROWS[case] == "reproduced" else ERRATA_LINK
    assert (slice_, result, authority) == ("9", _ROWS[case], expected)


def test_ac0022_closure_entry_names_the_spec_and_the_replay() -> None:
    closure = " ".join(_section(RECORD.read_text(encoding="utf-8"), "Compatibility closure").split())
    entry = [b for b in closure.split("- **") if f"(../{SLUG}/spec.md)" in b]
    assert len(entry) == 1
    for name in ("`unmigrated_workspace`", "`[authorization.migration]`", "202 runs", "0 differing outputs"):
        assert name in entry[0], name


def test_ac0023_inventory_holds_the_contract_row() -> None:
    import tomllib

    rows = tomllib.loads(INVENTORY.read_text(encoding="utf-8"))["row"]
    mine = [r for r in rows if r["pattern"] == f"docs/specs/{SLUG}/*"]
    # Once the spec shipped, workspace-toml-deletion moved its row to the history set.
    assert [(r["class"], r["owner"]) for r in mine] == [("historical", "none")]


def test_ac0024_brief_names_the_spec_and_widens_the_non_goal() -> None:
    text = BRIEF.read_text(encoding="utf-8")
    assert f"\n| `{SLUG}` | <auto> |" in _section(text, "Spec map")
    after = text.split("**After the cutover:**", 1)[1]
    assert f"move the engine rules `dispatch.py` still needs into `work-loop` (`{SLUG}`);" in after
    assert f"shrink `workspace-status` to the repair (`{SLUG}`);" in after
    flat = " ".join(text.split())
    assert "re-points the bridge's pinned finding table, and the parity tests that pin it, to `work-loop`'s finding table" in flat
    assert "re-points the queue redirect in `navigate-intents`'s SKILL.md" in flat


def test_ac0025_ledger_records_each_approval_with_its_digest() -> None:
    rows = [
        line for line in _section(LEDGER.read_text(encoding="utf-8"), "Approvals").splitlines()
        if line.startswith("| 2026-")
    ]
    for record in (
        "docs/rfc/0106-stop-registering-derivable-work.md",
        "docs/rfc/0083-work-intake-and-artifact-routing.md",
        "docs/product/briefs/workspace-registry-retirement-delivery.md",
        "docs/specs/workspace-retirement/retirement-record.md",
    ):
        mine = [r for r in rows if f"`{record}`" in r and "eugenelim" in r]
        assert mine and re.search(r"`[0-9a-f]{64}`", mine[-1]), record
    assert any("readiness hand-over" in r and "eugenelim" in r for r in rows)


def test_ac0026_fragment_names_both_packages_and_the_changes() -> None:
    import tomllib

    matches = []
    for path in sorted(FRAGMENTS.glob("*.md")):
        head, _, body = path.read_text(encoding="utf-8").partition("+++\n")[2].partition("+++\n")
        packages = {(p["name"], p["version"]) for p in tomllib.loads(head)["packages"]}
        if "unmigrated_workspace" in body and {name for name, _ in packages} >= {"core", "agentbundle"}:
            matches.append((packages, " ".join(body.split())))
    assert len(matches) == 1, [m[0] for m in matches]
    packages, body = matches[0]
    versions = dict(packages)
    assert versions["core"].startswith("4.0.") and versions["agentbundle"].endswith(".0")
    for name in ("`unmigrated_workspace`", "`repair-plan`", "`repair-rollback` removal", "`ini_slug`"):
        assert name in body, name
