#!/usr/bin/env python3
"""Instruction roster for the intent and brief registration stop (AC-0021 to AC-0026, AC-0029 to AC-0031).

Spec: docs/specs/intent-brief-registration-stop/spec.md

AC-0021: with each run of whitespace read as one space, none of four writer
skills holds the registration phrase listed for it.
AC-0022: each of those skills names ``tracker-origin`` and ``intent-brief-drop``.
AC-0023: neither the ``workspace-status`` skill nor the schema guide holds
``names no registered brief``.
AC-0024: a closed list of guides, architecture and maintainer pages and two pack
pages holds none of the phrases listed for it.
Every AC-0021, AC-0023 and AC-0024 phrase is present in its file at commit
``ff33d0dcc``, so an absence above cannot come from a typo in the list.
AC-0025: each governing record's Errata section holds a dated entry that links
RFC-0106 and holds each listed literal.
AC-0026: each intent holds a dated owner amendment that links RFC-0106 and holds
each listed literal.
AC-0029: the ledger's T1 section records the registry comparison, its exit code
``0``, the commit, and the merge base.
AC-0030: this repository's ``workspace.toml`` holds no repo-origin intent entry
under ``docs/product/intents/`` and no repo-origin brief entry under
``docs/product/briefs/``.
AC-0031: the ledger's T7 section records the plan and the apply that removed
them, with the counts of intent and brief operations and of entries removed.
Standard library only; the checks read files and git history and write nothing.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parents[2]
_BASELINE = "ff33d0dcc"
_MIN_DATE = "2026-10-27"
_SKILLS = "packs/core/.apm/skills/"

# AC-0021, AC-0023 and AC-0024: file -> phrases it must not hold.
_ABSENT: dict[str, tuple[str, ...]] = {
    _SKILLS + "author-delivery-brief/SKILL.md": (
        "Register one schema-valid Draft pointer",
        "Move the complete structured brief entry",
        "Move an entry between the matching",
    ),
    _SKILLS + "close-work/SKILL.md": ("moving its exact workspace entry",),
    _SKILLS + "work-intake/SKILL.md": (
        "Registering an intent, a brief, or a spec",
        "intent path (registered)",
    ),
    _SKILLS + "intake-intent/SKILL.md": ("register one non-dispatchable pointer",),
    _SKILLS + "workspace-status/SKILL.md": ("names no registered brief",),
    "guides/core/reference/workspace-toml-schema.md": ("names no registered brief",),
    "guides/core/how-to/intake-an-external-brief.md": ("then registers the structured Draft entry",),
    "guides/core/how-to/capture-work.md": ("Draft artifact, registers a",),
    "guides/_shared/how-to/use-work-intake.md": ("Draft artifact, registers a",),
    "guides/_shared/reference/work-intake-routing-and-lifecycle.md": (
        "| brief | `brief_queue.draft` |",
        "registers it after the artifact exists",
    ),
    "guides/core/reference/work-intake-routing-and-lifecycle.md": (
        "matching `brief_queue` collection",
        "Write and register a Draft, non-dispatchable artifact",
    ),
    "guides/core/tutorials/your-first-workspace.md": ("then registers a schema-valid",),
    "guides/core/explanation/two-room-model.md": ("registers its lifecycle state",),
    "guides/core/explanation/role-journeys.md": ("a DoR-ready brief in `[brief_queue]`.",),
    "guides/catalogue-curation/tutorials/your-first-skill.md": (
        "Pulls confirmed slices from `[brief_queue]`",
    ),
    "guides/product-engineering/how-to/hand-an-intent-to-build.md": (
        "registers it in `workspace.toml`,",
    ),
    "guides/product-engineering/how-to/rename-an-intent.md": ("source-unregistered",),
    "docs/architecture/work-intake-and-artifact-routing.md": (
        "its `brief_queue` membership carry the same state",
        "the artifact and `brief_queue`",
    ),
    "docs/guides/reference/work-intake-maintenance.md": ("its `brief_queue` collection identical",),
    "web/src/content/packs/github.md": ("when `receive-brief` registers the brief",),
    "web/src/content/packs/linear.md": ("updated when the brief enters the queue",),
}

# AC-0022: the four AC-0021 skills each name both literals.
_AC22_FILES = tuple(rel for rel in _ABSENT if rel.startswith(_SKILLS) and "workspace-status" not in rel)
_AC22_LITERALS = ("tracker-origin", "intent-brief-drop")

# AC-0025: record -> literals its dated RFC-0106 errata entry holds.
_ERRATA: dict[str, tuple[str, ...]] = {
    "docs/adr/0119-retire-the-initiative-ladder-into-the-recursive-intent-graph.md": ("D4",),
    "docs/adr/0134-intent-rename-sealed-identity-bound-transaction.md": ("D4", "Applies to", "lock"),
    "docs/adr/0110-cooled-child-scope-is-declared-on-the-entry-not-inferred-from-absence.md": (
        "D2",
        "D4",
        "D7",
        "D9",
    ),
    "docs/rfc/0064-ini-001-ai-native-ecosystem.md": (
        "[brief_queue]",
        "receive-brief",
        "author-brief",
        "M1",
    ),
    "docs/rfc/0083-work-intake-and-artifact-routing.md": ("§ 6", "§ 8", "brief_queue.executing"),
    "docs/rfc/0106-stop-registering-derivable-work.md": (
        "the unregistered intent or brief's own dependencies",
        "the waiter's dependency cycle through an unregistered intent or brief",
        "the entry-derived findings of an intent or brief target",
        "the child-state check on a brief that never had an entry",
        "the cooled child of a brief that never had an entry",
        "tracker-origin",
    ),
}
_ADR_0119 = "docs/adr/0119-retire-the-initiative-ladder-into-the-recursive-intent-graph.md"

# AC-0026: intent -> literals its dated owner amendment holds.
_AMENDMENTS: dict[str, tuple[str, ...]] = {
    "docs/product/intents/FEAT-0001-intent-identity-and-registration.md": ("C3",),
    "docs/product/intents/FEAT-0005-lifecycle-and-closure.md": ("Boundary", "item 7", "brief"),
    "docs/product/intents/FEAT-0007-work-item-promotion-routing.md": ("Opportunity", "remember route"),
}

_RFC_LINK = "0106-stop-registering-derivable-work"


def _flat_text(text: str) -> str:
    """The text with each run of whitespace, line breaks included, read as one space."""
    return " ".join(text.split())


def _flat(rel: str) -> str:
    return _flat_text((_REPO / rel).read_text(encoding="utf-8"))


def _baseline(rel: str) -> str:
    """The file's text at the baseline commit, whitespace-normalised."""
    result = subprocess.run(
        ["git", "show", f"{_BASELINE}:{rel}"],
        cwd=_REPO,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        pytest.skip(f"commit {_BASELINE} is not available in this checkout")
    return _flat_text(result.stdout)


@pytest.mark.parametrize("rel", sorted(_ABSENT))
def test_no_registration_phrase_remains(rel: str) -> None:
    flat = _flat(rel)
    for phrase in _ABSENT[rel]:
        assert phrase not in flat, f"{rel} holds {phrase!r}"


@pytest.mark.parametrize("rel", sorted(_ABSENT))
def test_every_listed_phrase_was_present_at_the_baseline(rel: str) -> None:
    flat = _baseline(rel)
    for phrase in _ABSENT[rel]:
        assert phrase in flat, f"{rel} did not hold {phrase!r} at {_BASELINE}"


@pytest.mark.parametrize("rel", _AC22_FILES)
def test_writer_skill_names_the_tracker_origin_limit_and_the_repair(rel: str) -> None:
    flat = _flat(rel)
    for literal in _AC22_LITERALS:
        assert literal in flat, f"{rel} lacks {literal!r}"


def _dated_entries(rel: str) -> list[tuple[str, str]]:
    """Each dated bullet of the record's ``## Errata`` section, as (date, flat text)."""
    text = (_REPO / rel).read_text(encoding="utf-8")
    section = text[text.index("\n## Errata") + 1 :]
    following = re.search(r"\n## (?!Errata)", section)
    if following:
        section = section[: following.start()]
    entries = []
    for entry in re.split(r"\n(?=- )", section):
        match = re.match(r"- \**(\d{4}-\d{2}-\d{2})", entry)
        if match and match.group(1) >= _MIN_DATE:
            entries.append((match.group(1), _flat_text(entry)))
    return entries


@pytest.mark.parametrize("rel", sorted(_ERRATA))
def test_errata_entry_links_the_rfc_and_holds_each_literal(rel: str) -> None:
    problems = []
    for date, flat in _dated_entries(rel):
        # RFC-0106's own entry sits inside RFC-0106, so it cannot link itself.
        missing = [lit for lit in _ERRATA[rel] if lit not in flat]
        links = _RFC_LINK in flat or rel.endswith(_RFC_LINK + ".md")
        if links and not missing:
            return
        problems.append(f"{date}: links RFC-0106={links}, missing {missing}")
    raise AssertionError(f"{rel}: no qualifying errata entry; {problems}")


def test_adr_0119_names_the_superseded_part() -> None:
    text = (_REPO / _ADR_0119).read_text(encoding="utf-8")
    lines = text.splitlines()
    related = [line for line in lines if line.startswith("- **Related:**")]
    assert related, "ADR-0119 has no Related line"
    assert "RFC-0106 D1" in related[0]
    # The ADR metadata lint accepts only ADR references in this field.
    assert "- **Superseded in part:** none" in lines


@pytest.mark.parametrize("rel", sorted(_AMENDMENTS))
def test_intent_amendment_is_dated_owner_approved_and_holds_each_literal(rel: str) -> None:
    text = (_REPO / rel).read_text(encoding="utf-8")
    paragraphs = [p for p in re.split(r"\n\s*\n", text) if p.startswith("**Amendment, ")]
    problems = []
    for paragraph in paragraphs:
        flat = _flat_text(paragraph)
        match = re.match(r"\*\*Amendment, (\d{4}-\d{2}-\d{2})", flat)
        if not match or match.group(1) < _MIN_DATE:
            continue
        missing = [lit for lit in _AMENDMENTS[rel] if lit not in flat]
        if "eugenelim (owner)" in flat and _RFC_LINK in flat and not missing:
            return
        problems.append(f"{match.group(1)}: missing {missing}")
    raise AssertionError(f"{rel}: no qualifying amendment; {problems}")


_LEDGER = "docs/specs/intent-brief-registration-stop/notes/verification-ledger.md"


def _ledger_section(heading: str) -> str:
    """Return the ledger text under one ``## `` heading, up to the next one."""
    text = (_REPO / _LEDGER).read_text(encoding="utf-8")
    start = text.index(f"\n## {heading}")
    end = text.find("\n## ", start + 1)
    return text[start:] if end < 0 else text[start:end]


def test_ac0029_ledger_records_the_comparison_before_the_stop() -> None:
    section = _ledger_section("T1: the registry comparison before the stop")
    assert "tools/compare-registry.py --root" in section
    assert "**Exit code:** `0`" in section
    assert re.search(r"\*\*Commit:\*\* `[0-9a-f]{40}`", section)
    assert re.search(r"\*\*Merge base with `origin/main`:\*\* `[0-9a-f]{40}`", section)
    assert "registry comparison: pass" in section


def _repo_origin_intent_and_brief_entries(node: object) -> list[str]:
    """Return every repo-origin intent or brief entry path in a parsed registry."""
    found: list[str] = []
    if isinstance(node, dict):
        path, kind = node.get("path"), node.get("kind")
        mode = node.get("source", {}).get("mode") if isinstance(node.get("source"), dict) else None
        if isinstance(path, str) and mode == "repo-origin" and (
            (kind == "intent" and path.startswith("docs/product/intents/"))
            or (kind == "brief" and path.startswith("docs/product/briefs/"))
        ):
            found.append(path)
        for value in node.values():
            found.extend(_repo_origin_intent_and_brief_entries(value))
    elif isinstance(node, list):
        for value in node:
            found.extend(_repo_origin_intent_and_brief_entries(value))
    return found


def test_ac0030_registry_holds_no_repo_origin_intent_or_brief_entry() -> None:
    import tomllib

    data = tomllib.loads((_REPO / "workspace.toml").read_text(encoding="utf-8"))
    assert _repo_origin_intent_and_brief_entries(data) == []


def test_ac0030_detector_finds_a_planted_entry() -> None:
    planted = {"backlog": {"open": [{
        "path": "docs/product/intents/x.md", "kind": "intent",
        "source": {"mode": "repo-origin"},
    }]}}
    assert _repo_origin_intent_and_brief_entries(planted) == ["docs/product/intents/x.md"]


def test_ac0031_ledger_records_the_repair_run() -> None:
    section = _ledger_section("T7: the repair on this repository")
    for literal in ("repair-plan", "repair-apply", "95 for intents and 23 for briefs",
                    "`operations_applied: 118`", "**Entries removed:** 118",
                    "holds no `intent-brief-drop` operation"):
        assert literal in section, literal
