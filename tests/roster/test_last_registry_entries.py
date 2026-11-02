#!/usr/bin/env python3
"""Roster for last-registry-entries.

Spec: docs/specs/last-registry-entries/spec.md

AC-0012: the retirement record's Equivalence table holds the three accepted
removals at slice 9, each citing the RFC-0106 errata.
AC-0013: RFC-0106 Errata holds the 2026-10-31 entry naming those removals and
``.work-intake.toml``.
AC-0014: the refresh-policy text names ``.work-intake.toml`` and no file places
``[authorization.refresh]`` in ``workspace.toml``; the workspace-status text names
both repair steps; the anchor rules name the captured-item file.
AC-0016: the verification ledger's Approvals table holds eugenelim rows for the
errata entry, the brief, the closure entry, the QA matrix copy and the repair plan,
each with a 64-hex SHA-256, the captured file's SHA matching its bytes, and the
errata row before the repair-plan row.
AC-0017: the retirement record's Compatibility closure holds one bullet linking the
spec and naming the repairs, ``.work-intake.toml`` and the run's counts.
AC-0018: the delivery brief's Spec map lists the spec and the two after-cutover
items name it, with the rest of each item's text unchanged.

The checks read files and write nothing.
"""

from __future__ import annotations

import hashlib
import re
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
_RECORD = "docs/specs/workspace-retirement/retirement-record.md"
_RFC = "docs/rfc/0106-stop-registering-derivable-work.md"
_BRIEF = "docs/product/briefs/workspace-registry-retirement-delivery.md"
_SLUG = "last-registry-entries"
_LEDGER = "docs/specs/last-registry-entries/notes/verification-ledger.md"
_CAPTURED = "docs/product/captured/credential-broker-contract-manual-qa.md"
_PLAN = ".workspace-repair-plan.json"
_ERRATA_LINK = "[RFC-0106 § Errata](../../rfc/0106-stop-registering-derivable-work.md#errata)"
_CASES = (
    "the registered captured item's kind",
    "the defect settled by backlog.closed",
    "the registered captured item's own findings and edges",
)
_POLICY_FILES = (
    "guides/_shared/how-to/use-work-intake.md",
    "guides/_shared/reference/work-intake-routing-and-lifecycle.md",
    "guides/core/reference/workspace-toml-schema.md",
    "packs/core/.apm/skills/work-intake/SKILL.md",
    "packs/core/.apm/skills/work-intake/references/lifecycle-index.md",
)
# Each phrase is the base text that placed the policy in `workspace.toml` (or the
# registry), kept literal so the check fails if it comes back.
_STALE_POLICY_PHRASES = {
    "guides/_shared/how-to/use-work-intake.md": "declare its closed role policy:",
    "guides/core/reference/workspace-toml-schema.md": "role policy outside initiative entries",
    "packs/core/.apm/skills/work-intake/SKILL.md": "so the registry digest stays bound",
}
_STATUS_FILES = (
    "packs/core/.apm/skills/workspace-status/SKILL.md",
    "packs/core/.apm/skills/workspace-status/references/mutate.md",
)
_ANCHOR_FILES = {
    "packs/core/.apm/skills/work-loop/SKILL.md": "deferral anchors resolving through `[backlog].",
    "packs/core/.apm/skills/new-spec/references/spec-and-plan-contract.md":
        "resolve through an entry in `workspace.toml [backlog].open`",
    "packs/core/.apm/agents/adversarial-reviewer.md":
        "resolves through a `workspace.toml [backlog].open` entry",
    "docs/architecture/loop-contract.md":
        "`workspace.toml` `[backlog].open` is the sole authoritative register",
    "docs/architecture/work-intake-and-artifact-routing.md":
        "spec's deferral marker is the loop contract's",
}


def _read(path: str) -> str:
    return (_REPO / path).read_text(encoding="utf-8")


def _flat(path: str) -> str:
    """The file's text with every whitespace run collapsed to one space."""
    return " ".join(_read(path).split())


def _section(text: str, heading: str) -> str:
    """The body of the level-2 section `heading`, up to the next level-2 heading."""
    body = text.split(f"\n## {heading}\n", 1)[1]
    return re.split(r"\n## ", body, maxsplit=1)[0]


def test_ac0012_record_holds_three_accepted_removals() -> None:
    """Each case has one `accepted removal` row at slice 9 citing the errata."""
    table = _section(_read(_RECORD), "Equivalence")
    for case in _CASES:
        rows = [r for r in table.splitlines() if r.startswith(f"| `{case}` |")]
        assert len(rows) == 1, case
        cells = [c.strip() for c in rows[0].strip().strip("|").split("|")]
        assert cells[1] == "9", case
        assert cells[2] == "accepted removal", case
        assert cells[4] == _ERRATA_LINK, case


def test_ac0013_errata_entry_names_the_removals_and_the_policy_file() -> None:
    """RFC-0106 Errata holds one 2026-10-31 entry for this spec's three removals."""
    entries = [
        line
        for line in _section(_read(_RFC), "Errata").splitlines()
        if line.startswith("- 2026-10-31:") and "last registry entries" in line
    ]
    assert len(entries) == 1
    for phrase in (
        "the registered captured item's kind",
        "the defect settled by `backlog.closed`",
        "the registered captured item's own findings and edges",
        "`.work-intake.toml`",
    ):
        assert phrase in entries[0], phrase


def test_ac0014_policy_text_names_the_policy_file() -> None:
    """The five work-intake files name `.work-intake.toml` and drop the stale phrase."""
    for path in _POLICY_FILES:
        text = _flat(path)
        assert ".work-intake.toml" in text, path
        stale = _STALE_POLICY_PHRASES.get(path)
        if stale is not None:
            assert stale not in text, path


def test_ac0014_workspace_status_text_names_both_repair_steps() -> None:
    """`workspace-status` SKILL.md and mutate.md each name both new repair steps."""
    for path in _STATUS_FILES:
        text = _read(path)
        assert "captured-entry-drop" in text, path
        assert "refresh-policy-move" in text, path


def test_ac0014_anchor_rules_resolve_through_captured_files() -> None:
    """No anchor rule resolves through `[backlog].open`; each names the captured dir."""
    for path, stale in _ANCHOR_FILES.items():
        text = _flat(path)
        assert stale not in text, path
        assert "docs/product/captured/" in text, path


def test_ac0018_brief_lists_the_spec_and_names_it_beside_two_items() -> None:
    """The Spec map row, the two items' slug, and the 9A phrase."""
    text = _read(_BRIEF)
    assert f"\n| `{_SLUG}` | <auto> |" in _section(text, "Spec map")
    slices = _section(text, "Delivery slices")
    after = slices.split("**After the cutover:**", 1)[1]
    items = re.findall(r"^ {5}- (.*)$", after, re.M)
    named = [i for i in items if f"(`{_SLUG}`)" in i]
    assert len(named) == 2, named
    assert named[0].startswith("remove the legacy registry entries (the migrated captured")
    assert "from `[backlog].open` to captured-item files" in named[0]
    assert named[1] == (
        "give the `[authorization.refresh]` and `[authorization.migration]` "
        f"policy tables a home (`{_SLUG}`);"
    )


def _approval_rows() -> list[list[str]]:
    """The ledger's Approvals table rows as cell lists, backticks stripped."""
    rows = []
    for line in _section(_read(_LEDGER), "Approvals").splitlines():
        if line.startswith("|") and not line.startswith(("| Date", "| ---")):
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            rows.append([c.strip("`") for c in cells])
    return rows


def test_ac0016_ledger_approvals_hold_owner_rows_with_shas() -> None:
    """Owner rows exist per file, SHAs are well formed, order and captured SHA hold."""
    rows = _approval_rows()
    for path in (_RFC, _BRIEF, _RECORD, _CAPTURED, _PLAN):
        matching = [r for r in rows if path in r[3]]
        assert matching, path
        assert all(r[1] == "eugenelim" for r in matching), path
    for row in rows:
        assert re.fullmatch(r"[0-9a-f]{64}", row[4]), row
    captured = next(r for r in rows if _CAPTURED in r[3])
    digest = hashlib.sha256((_REPO / _CAPTURED).read_bytes()).hexdigest()
    assert captured[4] == digest
    files = [r[3] for r in rows]
    errata = next(i for i, f in enumerate(files) if _RFC in f)
    plan = next(i for i, f in enumerate(files) if _PLAN in f)
    assert errata < plan


def test_ac0017_closure_entry_names_the_run() -> None:
    """One closure bullet links the spec and names the repairs, file and counts."""
    bullets = [
        line
        for line in _section(_read(_RECORD), "Compatibility closure").splitlines()
        if "](../last-registry-entries/spec.md)" in line
    ]
    assert len(bullets) == 1
    text = bullets[0]
    for phrase in (
        "captured-entry-drop",
        "refresh-policy-move",
        ".work-intake.toml",
        "71 `captured-entry-drop`",
        "3 `needs-to-header`",
        "0 `refresh-policy-move`",
    ):
        assert phrase in text, phrase
