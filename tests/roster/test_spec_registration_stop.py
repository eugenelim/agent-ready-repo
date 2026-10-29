#!/usr/bin/env python3
"""Instruction roster for the spec registration stop and the readiness bridge's input.

Spec: docs/specs/spec-registration-stop/spec.md
Spec: docs/specs/readiness-bridge-dispatch-input/spec.md

Each task of those two plans adds its own rows here: closed lists of files and
phrases a writer, guide or instruction must no longer hold (each present at
commit ``dfa3fe067``, so an absence cannot come from a typo in the list), the
phrases they must hold, the governing errata and amendments, and the ledger rows.
Standard library only; the checks read files and git history and write nothing.
"""

from __future__ import annotations

import ast
import subprocess
from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parents[2]
_BASELINE = "dfa3fe067"

# file -> phrases it must not hold (each present at the baseline).
_ABSENT: dict[str, tuple[str, ...]] = {
    # T2 (AC-0024): the Type 1 sentences.
    "packs/core/.apm/skills/workspace-status/references/reconcile.md": (
        "finds work nobody registered",
        "without being added to `workspace.toml`",
    ),
    "packs/core/.apm/skills/workspace-status/SKILL.md": (
        "run `reconcile` to also check for untracked live specs",
        "Full audit: find untracked live specs",
        "also finds untracked live specs (Type 1)",
        "untracked live specs (empty in status/explain",
        "add to [work].queue through `work-intake`",
    ),
}

# file -> phrases it must hold.
_COOLED_CHILD_ACTION = (
    "Set parent on the spec's lifecycle record: a resolving brief path, or none only "
    "when that spec has no parent brief; a tracker-origin entry declares source.parent "
    "instead."
)

_PRESENT: dict[str, tuple[str, ...]] = {
    # T2 (AC-0005): the owner-approved cooled-child next action.
    "packs/core/.apm/skills/workspace-status/SKILL.md": (_COOLED_CHILD_ACTION,),
    "guides/core/reference/workspace-toml-schema.md": (_COOLED_CHILD_ACTION,),
}

# AC-0003: no file in these trees holds the retired finding code.
_RETIRED_CODE = "unregistered_work"
_RETIRED_CODE_TREES = (
    "packs/core/.apm/skills",
    "packages/agentbundle/agentbundle/_data",
)
_RETIRED_CODE_FILES = ("guides/core/reference/workspace-toml-schema.md",)

# AC-0005: the three Python tables that hold the next action.
_NEXT_ACTION_TABLES = (
    (
        "packs/core/.apm/skills/workspace-status/scripts/workspace_status_engine.py",
        "_FINDING_NEXT_ACTIONS",
    ),
    ("packages/agentbundle/agentbundle/_data/workspace_status_engine.py", "_FINDING_NEXT_ACTIONS"),
    ("packs/core/.apm/skills/navigate-intents/scripts/intent_readiness.py", "_KNOWN_FINDINGS"),
)


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


def test_roster_lists_are_well_formed() -> None:
    for table in (_ABSENT, _PRESENT):
        for rel, phrases in table.items():
            assert (_REPO / rel).is_file(), rel
            assert phrases and all(isinstance(p, str) and p for p in phrases), rel


@pytest.mark.parametrize("rel", sorted(_ABSENT))
def test_no_listed_phrase_remains(rel: str) -> None:
    flat = _flat(rel)
    for phrase in _ABSENT[rel]:
        assert phrase not in flat, f"{rel} holds {phrase!r}"


@pytest.mark.parametrize("rel", sorted(_ABSENT))
def test_every_banned_phrase_was_present_at_the_baseline(rel: str) -> None:
    flat = _baseline(rel)
    for phrase in _ABSENT[rel]:
        assert phrase in flat, f"{rel} did not hold {phrase!r} at {_BASELINE}"


@pytest.mark.parametrize("rel", sorted(_PRESENT))
def test_every_required_phrase_is_present(rel: str) -> None:
    flat = _flat(rel)
    for phrase in _PRESENT[rel]:
        assert phrase in flat, f"{rel} lacks {phrase!r}"


def test_retired_finding_code_is_gone_from_shipped_trees() -> None:
    """AC-0003: no shipped file holds ``unregistered_work``."""
    files = [_REPO / rel for rel in _RETIRED_CODE_FILES]
    for tree in _RETIRED_CODE_TREES:
        files.extend(p for p in (_REPO / tree).rglob("*") if p.is_file())
    holders = []
    for path in files:
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        if _RETIRED_CODE in text:
            holders.append(path.relative_to(_REPO).as_posix())
    assert holders == []


@pytest.mark.parametrize(("rel", "table"), _NEXT_ACTION_TABLES)
def test_cooled_child_next_action_sentence(rel: str, table: str) -> None:
    """AC-0005: each Python table holds the approved sentence for the finding."""
    tree = ast.parse((_REPO / rel).read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        value = None
        if isinstance(node, ast.Assign) and any(
            isinstance(t, ast.Name) and t.id == table for t in node.targets
        ) or isinstance(node, ast.AnnAssign) and getattr(node.target, "id", "") == table:
            value = node.value
        if value is not None:
            actions = ast.literal_eval(value)
            assert actions["cooled_child_scope_unknown"] == _COOLED_CHILD_ACTION
            assert _RETIRED_CODE not in actions
            return
    pytest.fail(f"{rel} has no {table}")


# --- Governance (spec-registration-stop AC-0027 to AC-0031, AC-0045; bridge AC-0022 to AC-0024, AC-0027) ---

import re  # noqa: E402

_MIN_DATE = "2026-10-29"
_RFC_LINK = "0106-stop-registering-derivable-work"

# record -> literals its dated errata entry holds.
_ERRATA: dict[str, tuple[str, ...]] = {
    "docs/rfc/0105-artifact-derived-navigation-and-workspace-retirement.md": ("D3", "navigate-intents", "dispatch.py"),
    "docs/rfc/0108-skill-html-view-standard.md": ("D3", "dispatch.py", "argless"),
    "docs/rfc/0106-stop-registering-derivable-work.md": (
        "the spec entry removal",
        "spec-entry-drop",
        "tracker-origin",
        "the readiness bridge's first-ready mark",
    ),
    "docs/adr/0110-cooled-child-scope-is-declared-on-the-entry-not-inferred-from-absence.md": (
        "Revisit if",
        "parent",
        "lifecycle record",
    ),
    "docs/adr/0076-briefs-persist-dispatch-starts-from-specs.md": ("dispatch.py", "Brief:"),
}
_RFC_0064 = "docs/rfc/0064-ini-001-ai-native-ecosystem.md"
_RFC_0064_LITERALS = ("D4", "[work]", "work-loop", "M1")

_AMENDMENTS: dict[str, tuple[str, ...]] = {
    "docs/product/intents/FEAT-0005-lifecycle-and-closure.md": ("item 7", "spec"),
    "docs/product/intents/FEAT-0007-work-item-promotion-routing.md": ("spec", "remember route"),
}

_ABSENT.update({
    "docs/product/AGENTS.md": ("Registered spec membership in `workspace.toml`",),
    "docs/product/briefs/agent-skill-engineering.md": (
        "registered under `ini-009`",
        "register the spec under `ini-009`",
        "register approved specs in `workspace.toml`",
    ),
    "docs/product/briefs/workspace-registry-retirement-delivery.md": (
        "when a slice adds a finding code, as the bridge's parity test requires",
    ),
})
_PRESENT.update({
    "docs/product/AGENTS.md": ("A spec's own `Brief:` header is the confirmation evidence",),
    "docs/product/briefs/workspace-registry-retirement-delivery.md": (
        "when a slice adds, removes or rewords a finding code",
    ),
})

_LEDGERS = (
    "docs/specs/spec-registration-stop/notes/verification-ledger.md",
    "docs/specs/readiness-bridge-dispatch-input/notes/verification-ledger.md",
)


def _section(rel: str, heading: str) -> str:
    text = (_REPO / rel).read_text(encoding="utf-8")
    start = text.index(f"\n## {heading}") + 1
    following = re.search(r"\n## (?!" + re.escape(heading) + ")", text[start:])
    return text[start : start + following.start()] if following else text[start:]


def _dated_entries(rel: str) -> list[str]:
    entries = []
    for entry in re.split(r"\n(?=- )", _section(rel, "Errata")):
        match = re.match(r"- \**(\d{4}-\d{2}-\d{2})", entry)
        if match and match.group(1) >= _MIN_DATE:
            entries.append(_flat_text(entry))
    return entries


@pytest.mark.parametrize("rel", sorted(_ERRATA))
def test_errata_entry_links_the_rfc_and_holds_each_literal(rel: str) -> None:
    for flat in _dated_entries(rel):
        links = _RFC_LINK in flat or rel.endswith(_RFC_LINK + ".md")
        if links and all(lit in flat for lit in _ERRATA[rel]):
            return
    raise AssertionError(f"{rel}: no 2026-10-29-or-later errata entry links RFC-0106 with {_ERRATA[rel]}")


def test_rfc_0064_current_state_and_history_hold_the_entry() -> None:
    section = _section(_RFC_0064, "Errata")
    table = [line for line in section.splitlines() if line.startswith("| ") and _MIN_DATE in line]
    history = [_flat_text(e) for e in re.split(r"\n(?=- )", section) if e.startswith(f"- **{_MIN_DATE}")]
    for rows in (table, history):
        assert any(_RFC_LINK in r and all(lit in r for lit in _RFC_0064_LITERALS) for r in rows), rows


@pytest.mark.parametrize("rel", sorted(_AMENDMENTS))
def test_intent_amendment_is_dated_owned_and_linked(rel: str) -> None:
    text = (_REPO / rel).read_text(encoding="utf-8")
    for para in text.split("\n\n"):
        match = re.match(r"\*\*Amendment, (\d{4}-\d{2}-\d{2}), eugenelim \(owner\)", para)
        if match and match.group(1) >= _MIN_DATE:
            flat = _flat_text(para)
            if _RFC_LINK in flat and all(lit in flat for lit in _AMENDMENTS[rel]):
                return
    raise AssertionError(f"{rel}: no qualifying owner amendment")


def _approval_rows(rel: str) -> list[tuple[str, str]]:
    rows = []
    for line in (_REPO / rel).read_text(encoding="utf-8").splitlines():
        match = re.search(r"eugenelim \(owner\), (\d{4}-\d{2}-\d{2}T\d{2}:\d{2}[+-]\d{2}:\d{2})", line)
        target = re.match(r"\| `([^`]+)`", line)
        if match and target:
            rows.append((target.group(1), match.group(1)))
    return rows


def _first_author_date(rel: str, literal: str) -> str | None:
    """The author date of the earliest commit that added ``literal`` to ``rel``."""
    result = subprocess.run(
        ["git", "log", "--reverse", "--format=%aI", "-S", literal, "--", rel],
        cwd=_REPO, capture_output=True, text=True, check=False,
    )
    dates = result.stdout.split()
    return dates[0] if dates else None


_APPROVED_LITERAL = {
    "docs/rfc/0064-ini-001-ai-native-ecosystem.md": "Spec writer rows stop registering repo-origin specs",
    "docs/rfc/0106-stop-registering-derivable-work.md": "FEAT-0034's spec registration stop",
    "docs/adr/0110-cooled-child-scope-is-declared-on-the-entry-not-inferred-from-absence.md": "Revisit if (1) met",
    "docs/adr/0076-briefs-persist-dispatch-starts-from-specs.md": "read through a spec's own headers",
    "docs/product/intents/FEAT-0005-lifecycle-and-closure.md": "no terminal registration move for a repo-origin spec",
    "docs/product/intents/FEAT-0007-work-item-promotion-routing.md": "register no repo-origin spec",
    "docs/product/AGENTS.md": "A spec's own `Brief:` header is the confirmation evidence",
    "docs/product/briefs/agent-skill-engineering.md": "approved specs carry this brief's",
    "docs/product/briefs/workspace-registry-retirement-delivery.md": "adds, removes or rewords a finding code",
    "docs/rfc/0105-artifact-derived-navigation-and-workspace-retirement.md": "ends the 2026-10-12 D3 exception",
    "docs/rfc/0108-skill-html-view-standard.md": "D3's bridge reads `work-loop`'s argless",
}


@pytest.mark.parametrize("ledger", _LEDGERS)
def test_each_approval_precedes_the_commit_that_adds_its_text(ledger: str) -> None:
    from datetime import datetime

    rows = [(t, ts) for t, ts in _approval_rows(ledger) if t in _APPROVED_LITERAL]
    assert rows, f"{ledger} holds no approval rows"
    for target, stamp in rows:
        added = _first_author_date(target, _APPROVED_LITERAL[target])
        if added is None:
            pytest.skip("history unavailable in this checkout")
        assert datetime.fromisoformat(stamp) < datetime.fromisoformat(added), (target, stamp, added)
