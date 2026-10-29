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
