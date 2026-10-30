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
import json
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
        "Register or reconcile the canonical entry explicitly",
        "Autonomous dispatch consumers must use `canonical.ready` as the ready set",
        "`canonical.ready` is the only queue-ready set and `canonical.active` the only resumable one",
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
    # T8 (AC-0023, AC-0025): repo-origin specs need no entry; dispatch.py is the source.
    "packs/core/.apm/skills/work-intake/SKILL.md": ("tracker-origin", "spec-entry-drop"),
    # T2 (AC-0005): the owner-approved cooled-child next action.
    "packs/core/.apm/skills/workspace-status/SKILL.md": (_COOLED_CHILD_ACTION,),
    "guides/core/reference/workspace-toml-schema.md": (
        _COOLED_CHILD_ACTION,
        "tracker-origin",
        "spec-entry-drop",
    ),
}
_PRESENT["packs/core/.apm/skills/workspace-status/SKILL.md"] += (
    "tracker-origin",
    "spec-entry-drop",
    "`dispatch.py`",
)
_ABSENT.update({
    # T8 (AC-0023, AC-0024, AC-0026): writer, deferral and guide text.
    "packs/core/.apm/skills/work-intake/SKILL.md": (
        "A spec is registered, including when remembered",
        "register an already-materialized spec",
    ),
    "guides/core/reference/workspace-toml-schema.md": (
        "Register or reconcile the canonical entry explicitly",
    ),
    "packs/core/.apm/skills/new-spec/SKILL.md": ("The workspace entry for a",),
    "packs/repo-governance/.apm/skills/new-rfc/SKILL.md": ("for queue registration",),
    "packs/core/.apm/skills/new-spec/references/spec-and-plan-contract.md": (
        "resolve to an entry in `workspace.toml [backlog].open`",
    ),
    "packs/core/.apm/agents/adversarial-reviewer.md": (
        "resolves to a slug entry in `workspace.toml [backlog].open`",
    ),
    "guides/core/tutorials/your-first-workspace.md": ("Move the entry in `workspace.toml` from",),
    "guides/core/explanation/role-journeys.md": (
        "moves the spec from `[work].active` to `[work].shipped`",
        "routes them to `[work].queue`",
    ),
    "guides/core/explanation/two-room-model.md": ("The spec's path enters the build room's `queue`",),
    "guides/core/how-to/start-or-remember-work.md": ("then adds the `workspace.toml`",),
    "guides/_shared/reference/work-intake-routing-and-lifecycle.md": (
        "`work.queue` only after approval and sibling plan",
    ),
    "guides/catalogue-curation/tutorials/your-first-skill.md": (
        "registers a spec or tracker-origin item",
        "into specs in `[work].queue`",
    ),
    "guides/core/how-to/close-and-disposition-work.md": (
        "declare source.parent on its workspace entry",
    ),
    "docs/product/journeys/engineer-runs-work-loop.md": (
        "canonical ready/active spec from `workspace-status`",
    ),
})

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

_WORK_LOOP = "packs/core/.apm/skills/work-loop/SKILL.md"
_WORK_LOOP_EVALS = "packs/core/.apm/skills/work-loop/evals/evals.json"
_ABSENT[_WORK_LOOP] = (
    # T8 (AC-0024): historical deferral anchors resolve beyond [backlog].open.
    "historical deferral anchors in `[backlog].open`",
    "anchors still resolve in `[backlog].open`",
    # T6 (AC-0001): Step 0 dispatches from dispatch.py, not canonical.* lists.
    "canonical.ready",
    "canonical.active",
    "canonical.blocked",
    "select only the first",
    "If `workspace.toml` is present, read it and Surface",
    "If `workspace.toml` is absent, an explicit current request",
)
_PRESENT[_WORK_LOOP] = ("scripts/dispatch.py", "decision", "candidates", "--start", "--resume")

_DISPATCH_EVAL_IDS = (
    "step0-dispatch-start",
    "step0-dispatch-resume",
    "step0-dispatch-ask",
    "step0-dispatch-none",
    "step0-dispatch-refuse",
    "step0-supplied-path-start",
    "step0-supplied-path-resume-refused",
    "step0-explicit-request-conflict",
    "step0-no-registry-start",
)
_RETIRED_EVAL_PHRASES = (
    "canonical.ready",
    "canonical.active",
    "canonical workspace-status preflight",
    "untracked live specs",
)


# The outcome literals AC-0002 lists per case id: (in expected_output, in assertions).
_STOP_FIELDS = ("`code`", "`path`", "`next_action`")
_SPEC_PLAN_PLAN = ("spec.md", "plan.md", "PLAN")
_DISPATCH_OUTCOME_LITERALS: dict[str, tuple[tuple[str, ...], tuple[str, ...]]] = {
    "step0-dispatch-start": (("`start`", *_SPEC_PLAN_PLAN), ("`start`", *_SPEC_PLAN_PLAN)),
    "step0-dispatch-resume": (("`resume`", *_SPEC_PLAN_PLAN), ("`resume`", *_SPEC_PLAN_PLAN)),
    "step0-dispatch-ask": (
        ("`ask`", "`candidates`", "feature-a", "feature-b"),
        ("`candidates`", "feature-a", "feature-b"),
    ),
    "step0-dispatch-none": (("`none`", "stop", *_STOP_FIELDS), ("stop", *_STOP_FIELDS)),
    "step0-dispatch-refuse": (("`refuse`", "stop", *_STOP_FIELDS), ("stop", *_STOP_FIELDS)),
    "step0-supplied-path-start": (
        ("`dispatch.py --start`", "my-feature/spec.md", "PLAN"),
        ("`dispatch.py --start`", "my-feature/spec.md", "PLAN"),
    ),
    "step0-supplied-path-resume-refused": (
        ("`dispatch.py --resume`", "stop", *_STOP_FIELDS),
        ("stops", *_STOP_FIELDS),
    ),
    "step0-explicit-request-conflict": (
        ("exporter-retries/spec.md", "direct-light"),
        ("exporter-retries/spec.md", "direct-light"),
    ),
    "step0-no-registry-start": (
        ("my-feature/spec.md", "workspace.toml", "PLAN"),
        ("Response starts", "my-feature/spec.md", "workspace.toml"),
    ),
}


def test_work_loop_evals_hold_the_dispatch_cases_and_no_retired_phrase() -> None:
    """AC-0002 and AC-0043: the nine dispatch cases exist; no case holds a retired phrase."""
    payload = json.loads((_REPO / _WORK_LOOP_EVALS).read_text(encoding="utf-8"))
    cases = {case["id"]: case for case in payload["evals"]}
    for case_id in _DISPATCH_EVAL_IDS:
        case = cases[case_id]
        assert str(case["expected_output"]).strip(), case_id
        assert case["assertions"] and all(str(a).strip() for a in case["assertions"]), case_id
        in_output, in_assertions = _DISPATCH_OUTCOME_LITERALS[case_id]
        for literal in in_output:
            assert literal in case["expected_output"], (case_id, literal)
        joined = "\n".join(case["assertions"])
        for literal in in_assertions:
            assert literal in joined, (case_id, literal)
    # AC-0002 "starting it": the start verb is directly followed by the spec path.
    assert any(
        re.search(r"Response starts \S*my-feature/spec\.md", a)
        for a in cases["step0-no-registry-start"]["assertions"]
    ), "no step0-no-registry-start assertion has the start verb directly before the spec path"
    for case in payload["evals"]:
        for field in ("prompt", "expected_output", "assertions"):
            text = json.dumps(case.get(field, ""), ensure_ascii=False).lower()
            for phrase in _RETIRED_EVAL_PHRASES:
                assert phrase not in text, f"{case['id']}.{field} holds {phrase!r}"


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


def _approval_rows(rel: str) -> list[tuple[str, str, str]]:
    rows = []
    for line in (_REPO / rel).read_text(encoding="utf-8").splitlines():
        match = re.search(r"eugenelim \(owner\), (\d{4}-\d{2}-\d{2}T\d{2}:\d{2}[+-]\d{2}:\d{2})", line)
        target = re.match(r"\| `([^`]+)`", line)
        if match and target:
            rows.append((target.group(1), match.group(1), line))
    return rows


def _first_author_date(rel: str, literal: str) -> str | None:
    """The author date of the earliest commit that added ``literal`` to ``rel``."""
    result = subprocess.run(
        ["git", "log", "--reverse", "--format=%aI", "-S", literal, "--", rel],
        cwd=_REPO, capture_output=True, text=True, check=False,
    )
    dates = result.stdout.split()
    return dates[0] if dates else None


# A re-approval row names its own changed text, checked against the commit that added it.
_REAPPROVED = ("The tracker-origin spec entries",)

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

    rows = [row for row in _approval_rows(ledger) if row[0] in _APPROVED_LITERAL]
    assert rows, f"{ledger} holds no approval rows"
    for target, stamp, line in rows:
        literal = next((lit for lit in _REAPPROVED if lit in line), _APPROVED_LITERAL[target])
        added = _first_author_date(target, literal)
        if added is None:
            pytest.skip("history unavailable in this checkout")
        assert datetime.fromisoformat(stamp) < datetime.fromisoformat(added), (target, stamp, added)


# --- AC-0022: the equivalence fixtures stay byte-identical to the baseline ---

_FIXTURES = (
    "packs/core/tests/skills/work-loop/fixtures/header-derived-dispatch/expected.json",
    "packs/core/tests/skills/workspace-status/fixtures/depends-on-headers/expected.json",
    "packs/core/tests/skills/workspace-status/fixtures/depends-on-headers/expected-cooled-brief.json",
    "packs/core/tests/skills/workspace-status/fixtures/captured-item-files/expected.json",
)


@pytest.mark.parametrize("rel", _FIXTURES)
def test_equivalence_fixture_is_byte_identical_to_the_baseline(rel: str) -> None:
    result = subprocess.run(
        ["git", "show", f"{_BASELINE}:{rel}"], cwd=_REPO, capture_output=True, check=False
    )
    if result.returncode != 0:
        pytest.skip(f"commit {_BASELINE} is not available in this checkout")
    assert (_REPO / rel).read_bytes() == result.stdout


def test_close_guide_names_the_lifecycle_record_parent() -> None:
    """AC-0026: the cooled spec's declared parent is the lifecycle record's `parent`."""
    flat = _flat("guides/core/how-to/close-and-disposition-work.md")
    assert "lifecycle record's `parent`" in flat
    assert "spec's `Brief:` header" in flat


# spec-registration-stop AC-0013: the four tracker intake matrices are untouched
# (a pack test may not read above its own pack, so this repository-level check lives here).
_TRACKER_MATRICES = (
    "packs/atlassian/.apm/skills/jira-brief-intake/evals/files/intake/matrix.json",
    "packs/atlassian/.apm/skills/jira-align-brief-intake/evals/files/intake/matrix.json",
    "packs/github/.apm/skills/github-brief-intake/evals/files/intake/matrix.json",
    "packs/linear/.apm/skills/linear-brief-intake/evals/files/intake/matrix.json",
)


@pytest.mark.parametrize("rel", _TRACKER_MATRICES)
def test_tracker_matrices_are_byte_identical_to_the_base(rel: str) -> None:
    result = subprocess.run(
        ["git", "show", f"{_BASELINE}:{rel}"], cwd=_REPO, capture_output=True, check=False
    )
    if result.returncode != 0:
        pytest.skip(f"commit {_BASELINE} is not available in this checkout")
    assert (_REPO / rel).read_bytes() == result.stdout


# readiness-bridge-dispatch-input AC-0019 to AC-0021: the bridge's input is argless dispatch output.
_NAVIGATE_SKILL = "packs/core/.apm/skills/navigate-intents/SKILL.md"
_NAVIGATE_GUIDE = "guides/core/how-to/navigate-intents.md"
_NAVIGATE_EVALS = "packs/core/.apm/skills/navigate-intents/evals/eval_queries.json"
_DESIGN = "packs/core/DESIGN.md"
_PIPE = "scripts/dispatch.py' --root"

# (file, section heading or paragraph opening, banned tokens, required phrases).
_BRIDGE_INPUT: tuple[tuple[str, str, tuple[str, ...], tuple[str, ...]], ...] = (
    (
        _NAVIGATE_SKILL,
        "## Export an offline view",
        (
            "workspace-status",
            "workspace_status.py",
            "no ``workspace.toml``",
            "not ``status`` output",
            "a finding about the item that would be picked",
        ),
        (_PIPE, "--readiness -"),
    ),
    (
        _NAVIGATE_SKILL,
        "## Safety controls",
        ("workspace-status",),
        ("dispatch.py",),
    ),
    (
        _NAVIGATE_GUIDE,
        "### Show what is ready to work on",
        (
            "workspace-status",
            "workspace_status.py",
            "the repository has no",
            "a finding about the item it would pick",
            "Pipe only the `status` subcommand",
        ),
        (_PIPE, "--readiness -"),
    ),
    (
        _DESIGN,
        "The export has one piped input",
        ("workspace-status", "status mode", "strict status object"),
        ("dispatch.py",),
    ),
)


def _scoped(text: str, opening: str) -> str:
    """The whitespace-normalised section, or paragraph, that begins at ``opening``."""
    if opening.startswith("#"):
        level = len(opening) - len(opening.lstrip("#"))
        lines, taken, fenced = text.splitlines(), [], False
        for line in lines:
            if line.lstrip().startswith("```"):
                fenced = not fenced
            heading = not fenced and re.match(rf"#{{1,{level}}} ", line)
            if taken and heading:
                break
            if taken or line == opening:
                taken.append(line)
        body = "\n".join(taken)
        assert taken, opening
    else:
        start = text.index(opening)
        end = text.find("\n\n", start)
        body = text[start:] if end == -1 else text[start:end]
    return _flat_text(body)


def _base_text(rel: str) -> str:
    result = subprocess.run(
        ["git", "show", f"{_BASELINE}:{rel}"], cwd=_REPO, capture_output=True, text=True, check=False
    )
    if result.returncode != 0:
        pytest.skip(f"commit {_BASELINE} is not available in this checkout")
    return result.stdout


@pytest.mark.parametrize(("rel", "opening", "banned", "required"), _BRIDGE_INPUT)
def test_bridge_input_instructions_name_dispatch(
    rel: str, opening: str, banned: tuple[str, ...], required: tuple[str, ...]
) -> None:
    head = _scoped((_REPO / rel).read_text(encoding="utf-8"), opening)
    base = _scoped(_base_text(rel), opening)
    for phrase in banned:
        assert phrase in base, f"{rel} {opening}: {phrase!r} absent at the baseline"
        assert phrase not in head, f"{rel} {opening} still holds {phrase!r}"
    for phrase in required:
        assert phrase in head, f"{rel} {opening} lacks {phrase!r}"


def test_navigate_evals_name_dispatch_not_workspace_status() -> None:
    """AC-0020: the retired readiness query is gone and a dispatch query triggers."""
    text = (_REPO / _NAVIGATE_EVALS).read_text(encoding="utf-8")
    assert "readiness from workspace-status" in _base_text(_NAVIGATE_EVALS)
    assert "readiness from workspace-status" not in text
    cases = json.loads(text)
    cases = cases if isinstance(cases, list) else next(v for v in cases.values() if isinstance(v, list))
    assert any(
        c["should_trigger"] is True and "work-loop" in c["query"] and "dispatch" in c["query"]
        for c in cases
    )


_RECORD = "docs/specs/workspace-retirement/retirement-record.md"
_INVENTORY = "docs/specs/workspace-retirement/inventory.toml"
_OWNER_8_PREFIXES = (
    "docs/specs/spec-registration-stop/",
    "docs/specs/readiness-bridge-dispatch-input/",
    "packs/core/.apm/skills/navigate-intents/",
    "packs/core/tests/skills/navigate-intents/",
    ".claude/skills/navigate-intents/",
    ".agents/skills/navigate-intents/",
    "docs/specs/intent-view-readiness-handover/",
    "docs/specs/intent-navigation/",
    "docs/specs/intent-navigation-export/",
)
_OWNER_8_EXACT = (
    "guides/core/how-to/navigate-intents.md",
    "docs/rfc/0108-skill-html-view-standard.md",
)


def test_no_inventory_row_is_owner_8_outside_the_two_spec_directories() -> None:
    """AC-0034 and the bridge's AC-0026: only the two contract rows keep owner 8."""
    import tomllib

    rows = tomllib.loads((_REPO / _INVENTORY).read_text(encoding="utf-8"))["row"]
    left = sorted(r["pattern"] for r in rows if r["owner"] == 8)
    assert left == [
        "docs/specs/readiness-bridge-dispatch-input/*",
        "docs/specs/spec-registration-stop/*",
    ]
    assert all(r["class"] == "contract" for r in rows if r["owner"] == 8)
    # Rows the bridge spec disposes are named by AC-0034; none may stay at 8.
    for r in rows:
        p = r["pattern"]
        if p in _OWNER_8_EXACT or (
            p.startswith(_OWNER_8_PREFIXES[2:]) and not p.startswith(_OWNER_8_PREFIXES[0])
        ):
            assert r["owner"] != 8, p


def test_disposition_owner_8_is_only_the_coverage_evidence_row_with_home_nothing() -> None:
    """AC-0033."""
    text = (_REPO / _RECORD).read_text(encoding="utf-8")
    section = text.split("\n## Disposition", 1)[1].split("\n## ", 1)[0]
    owner_8 = []
    for line in section.splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if line.startswith("|") and len(cells) == 5 and cells[3] == "8":
            owner_8.append(cells)
    assert [c[0] for c in owner_8] == ["`spec registration as brief coverage evidence`"]
    assert owner_8[0][2] == "nothing"


def test_equivalence_holds_the_two_slice_8_rows() -> None:
    """AC-0032 and the bridge's AC-0024."""
    text = (_REPO / _RECORD).read_text(encoding="utf-8")
    section = text.split("\n## Equivalence", 1)[1].split("\n## ", 1)[0]
    rows = {}
    for line in section.splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if line.startswith("|") and len(cells) == 5:
            rows[cells[0].strip("`")] = cells
    assert rows["the spec entry removal"][1:3] == ["8", "reproduced"]
    assert rows["the spec entry removal"][4] == "none"
    mark = rows["the readiness bridge's first-ready mark"]
    assert mark[1:3] == ["8", "accepted removal"]
    assert "0106-stop-registering-derivable-work.md#errata" in mark[4]
