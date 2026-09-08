"""RFC-0096 Wave 7b — read-free parent scope for a cooled child.

Governing contract: `docs/specs/cooling-brief-child-scope-closure/spec.md`.
The decision and its accepted limitation are recorded in
`docs/adr/0106-cooled-child-scope-is-declared-on-the-entry-not-inferred-from-absence.md`.

Fixtures are named, not numbered, and match the spec's shared-fixture table:
**Declared**, **Empty** and **Absent** differ only in the child entry's raw
`source.parent` and the child body's brief link. Every case states the axes it
changes from one of those three.

The engine is loaded from source by path so a stale editable install cannot
satisfy this suite.
"""

import importlib.util
import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
ENGINE_PATH = ROOT / "packs/core/.apm/skills/workspace-status/scripts/workspace_status_engine.py"
SKILL_PATH = ROOT / "packs/core/.apm/skills/workspace-status/SKILL.md"
STATUS_SCRIPT = ROOT / "packs/core/.apm/skills/workspace-status/scripts/workspace_status.py"
SCHEMA_GUIDE = ROOT / "guides/core/reference/workspace-toml-schema.md"
CLOSEOUT_GUIDE = ROOT / "guides/core/how-to/close-and-disposition-work.md"

sys.path.insert(0, str(ROOT / "tests/roster"))
import test_status_projection_and_context_exclusion as wave6  # noqa: E402

BRIEF_PATH = wave6.BRIEF_PATH
CHILD_PATH = "docs/specs/child/spec.md"
DEPENDANT_PATH = "docs/specs/dependant/spec.md"
OTHER_PATH = "docs/specs/other/spec.md"
SECOND_PATH = "docs/specs/second/spec.md"
CODE = "cooled_child_scope_unknown"


@pytest.fixture()
def engine():
    """Load the source engine, never an installed projection."""
    spec = importlib.util.spec_from_file_location("wave7b_engine", ENGINE_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    try:
        spec.loader.exec_module(module)
    finally:
        sys.modules.pop(spec.name, None)
    return module


def _fixture(root, engine, *, parent, body_brief="none", cool=True,
             include_dependant=True):
    """Build one named fixture and reconcile it.

    `parent` is the raw `source.parent` for the child entry, or None to omit the
    key — the distinction under test. `body_brief` is the child's body-declared
    link, which a read-free implementation must never consult.
    """
    root.mkdir(parents=True, exist_ok=True)
    wave6._brief_body(root, status="Shipped")
    wave6._child_spec(root, status="Shipped", brief=body_brief)
    # `_child_spec` writes no sibling plan; every fixture in spec.md pins one,
    # and `_append_plan_findings` runs after the cooled early return, so an
    # uncooled arm would draw `missing_plan` and falsify its criterion.
    (root / "docs/specs/child/plan.md").write_text(
        "# Plan\n\n- **Status:** Done\n", encoding="utf-8"
    )
    if include_dependant:
        wave6._spec(root, "dependant", status="Approved", brief="none")
    wave6._brief_workspace(
        root,
        child_collection="shipped",
        child_source_parent=parent,
        brief_collection="shipped",
        include_dependant=include_dependant,
    )
    if cool:
        wave6._cool_child(root)
    return wave6._reconcile_canonical(root, engine)


def _cool(root, slug):
    """Write a Cooling record for an arbitrary slug alongside any others."""
    directory = root / "docs/lifecycle"
    directory.mkdir(parents=True, exist_ok=True)
    record = wave6._record(delivery_id=slug, locator=f"docs/specs/{slug}/spec.md")
    (directory / f"{slug}.json").write_text(json.dumps(record), encoding="utf-8")


def _multi_workspace(root, *, specs, brief_collection="shipped"):
    """Write workspace.toml for the cases needing more than one child entry.

    `specs` is a list of (path, collection, parent, needs) tuples, where parent
    is the raw `source.parent` string or None to omit the key. The emitted shape
    mirrors the Wave 6 helper's output rather than inventing one, because that
    is the shape the parser is exercised against everywhere else.
    """
    def entry(path, parent, needs, kind="spec"):
        clause = f', parent = "{parent}"' if parent is not None else ""
        return (
            f'{{path = "{path}", kind = "{kind}", '
            f'source = {{mode = "repo-origin"{clause}}}, '
            f'summary = "fixture", needs = {needs}}}'
        )

    collections = {"shipped": [], "active": [], "queue": []}
    for path, collection, parent, needs in specs:
        collections[collection].append(entry(path, parent, needs))

    brief_queues = dict.fromkeys(
        ("draft", "ready", "executing", "shipped", "withdrawn", "cancelled"), "[]"
    )
    brief_queues[brief_collection] = "[" + entry(BRIEF_PATH, None, "[]", kind="brief") + "]"

    lines = [
        '["ini-002"]',
        'name = "Cooling fixture"',
        'status = "active"',
        'milestone = "M1"',
        "",
        '["ini-002".work]',
    ]
    for name in ("queue", "active", "shipped"):
        lines.append(f'{name} = [{", ".join(collections[name])}]')
    lines += ["", '["ini-002".shaping_queue]', "active = []", "backlog = []",
              "", '["ini-002".brief_queue]']
    for name, value in brief_queues.items():
        lines.append(f"{name} = {value}")
    (root / "workspace.toml").write_text("\n".join(lines) + "\n", encoding="utf-8")


def _ready(result):
    return {e.entry.path for e in result.evaluations if e.dispatchable}


def _codes(result, code):
    return [f for f in result.findings if f.code == code]


# --- the three named fixtures ------------------------------------------------

def test_a_declared_resolving_parent_marks_its_brief(tmp_path, engine) -> None:
    """*AC1*: the Declared fixture refuses, and without the record it does not."""
    declared = _fixture(tmp_path / "declared", engine, parent=BRIEF_PATH,
                        body_brief=BRIEF_PATH)
    assert DEPENDANT_PATH not in _ready(declared)
    assert any(
        f.code == "unsatisfied_dependency" and f.path == BRIEF_PATH
        for f in declared.findings
    )

    uncooled = _fixture(tmp_path / "uncooled", engine, parent=BRIEF_PATH,
                        body_brief=BRIEF_PATH, cool=False)
    assert DEPENDANT_PATH in _ready(uncooled), (
        "control never dispatched; the refusal above proves nothing"
    )
    assert uncooled.findings == []


def test_a_declared_empty_parent_marks_nothing(tmp_path, engine) -> None:
    """*AC2*: the Empty fixture dispatches and raises nothing."""
    result = _fixture(tmp_path / "empty", engine, parent="none")
    assert DEPENDANT_PATH in _ready(result)
    assert result.findings == []


def test_an_absent_parent_on_a_cooled_entry_is_named(tmp_path, engine) -> None:
    """*AC3*: the entry to repair is named, not merely refused."""
    result = _fixture(tmp_path / "absent", engine, parent=None)
    found = _codes(result, CODE)
    assert len(found) == 1
    assert found[0].path == CHILD_PATH


def test_unestablished_scope_refuses_a_brief_dependency(tmp_path, engine) -> None:
    """*AC4*: fail closed, with the Empty fixture as the escapable control."""
    absent = _fixture(tmp_path / "absent", engine, parent=None)
    assert DEPENDANT_PATH not in _ready(absent)
    assert any(
        f.code == "unsatisfied_dependency" and f.path == BRIEF_PATH
        for f in absent.findings
    )

    empty = _fixture(tmp_path / "empty", engine, parent="none")
    assert DEPENDANT_PATH in _ready(empty), (
        "control never dispatched; the refusal above proves nothing"
    )
    assert not _codes(empty, CODE)


def test_the_parent_is_read_from_the_entry_not_the_body(tmp_path, engine) -> None:
    """*AC5*: the criterion a body-reading implementation fails.

    The dependant entry is absent, so the only observable is the finding — an
    implementation that opened the body would attribute the brief and emit
    nothing.
    """
    result = _fixture(tmp_path / "bodyonly", engine, parent=None,
                      body_brief=BRIEF_PATH, include_dependant=False)
    found = _codes(result, CODE)
    assert len(found) == 1
    assert found[0].path == CHILD_PATH


def test_a_declared_parent_resolving_to_no_membership_is_unestablished(
    tmp_path, engine
) -> None:
    """*AC6*: a case variant names no registered brief, so scope is unknown."""
    result = _fixture(tmp_path / "variant", engine,
                      parent="docs/product/briefs/Brief-1.md")
    found = _codes(result, CODE)
    assert len(found) == 1
    assert found[0].path == CHILD_PATH


def test_the_answer_is_per_entry(tmp_path, engine) -> None:
    """*AC7*: two cooled children, one declared empty — only the other is named."""
    root = tmp_path / "peritem"
    root.mkdir(parents=True, exist_ok=True)
    wave6._brief_body(root, status="Shipped")
    for slug in ("child", "other"):
        wave6._spec(root, slug, status="Shipped", brief="none")
        _cool(root, slug)
    _multi_workspace(root, specs=[
        (CHILD_PATH, "shipped", "none", "[]"),
        (OTHER_PATH, "shipped", None, "[]"),
    ])
    result = wave6._reconcile_canonical(root, engine)
    found = _codes(result, CODE)
    assert len(found) == 1
    assert found[0].path == OTHER_PATH


def test_unestablished_scope_does_not_refuse_a_non_brief_dependency(
    tmp_path, engine
) -> None:
    """*AC8*: the refusal is scoped to `kind = "brief"`, not every dependency."""
    root = tmp_path / "specdep"
    root.mkdir(parents=True, exist_ok=True)
    wave6._brief_body(root, status="Shipped")
    wave6._spec(root, "child", status="Shipped", brief="none")
    wave6._spec(root, "second", status="Approved", brief="none")
    _cool(root, "child")
    needs = f'[{{type = "local", kind = "spec", path = "{CHILD_PATH}"}}]'
    _multi_workspace(root, specs=[
        (CHILD_PATH, "shipped", None, "[]"),
        (SECOND_PATH, "queue", None, needs),
    ])
    result = wave6._reconcile_canonical(root, engine)
    assert SECOND_PATH in _ready(result)
    assert len(_codes(result, CODE)) == 1


def test_a_cooled_brief_is_satisfied_ahead_of_the_refusal(tmp_path, engine) -> None:
    """*AC11*: the cooled-brief precedence returns True before the refusal."""
    root = tmp_path / "cooledbrief"
    result = _fixture(root, engine, parent=None)
    assert DEPENDANT_PATH not in _ready(result)
    # Now cool the brief itself; its own lifecycle record satisfies the
    # dependency ahead of the unknown-scope refusal.
    directory = root / "docs/lifecycle"
    record = wave6._record(delivery_id="brief-1", locator=BRIEF_PATH)
    (directory / "brief-1.json").write_text(json.dumps(record), encoding="utf-8")
    after = wave6._reconcile_canonical(root, engine)
    assert DEPENDANT_PATH in _ready(after)


def test_an_uncooled_entry_disagreeing_with_its_body_is_named(
    tmp_path, engine
) -> None:
    """*AC12*: the uncooled control — provenance_mismatch, never this code."""
    for label, parent in (("omitted", None), ("declared-none", "none")):
        result = _fixture(tmp_path / label, engine, parent=parent,
                          body_brief=BRIEF_PATH, cool=False)
        assert len(_codes(result, "provenance_mismatch")) == 1
        assert not _codes(result, CODE)


def test_an_uncooled_entry_agreeing_with_its_body_is_not_named(
    tmp_path, engine
) -> None:
    """*AC13*: the Empty fixture uncooled raises no provenance finding."""
    result = _fixture(tmp_path / "agree", engine, parent="none", cool=False)
    assert not _codes(result, "provenance_mismatch")


# --- the documentation contract ----------------------------------------------

def _documented_finding_rows(text: str) -> dict[str, tuple[str, str]]:
    """Parse finding rows exactly as the shipped projection gate parses them."""
    rows: dict[str, tuple[str, str]] = {}
    for code, reason, action in re.findall(
        r"^\| `([^`]+)` \| ([^|]+) \| ([^|]+) \|$", text, flags=re.MULTILINE
    ):
        rows[code] = (reason.strip(), action.strip())
    return rows


def test_the_code_is_documented_where_the_gate_looks(engine) -> None:
    """*AC18*: both homes carry a row for the code, with reason and action."""
    assert CODE in engine._FINDING_NEXT_ACTIONS
    for path in (SKILL_PATH, SCHEMA_GUIDE):
        rows = _documented_finding_rows(path.read_text(encoding="utf-8"))
        assert CODE in rows, f"{path.name} carries no row for {CODE}"
        reason, action = rows[CODE]
        assert reason and action


def test_the_next_action_says_when_the_empty_answer_is_correct(engine) -> None:
    """*AC19*: the register value and both rows carry the literal.

    Presence of a row is not the contract — the row has to tell a maintainer
    when `none` is the right answer, which is the whole escape hatch.
    """
    literal = "only when that spec has no parent brief"
    assert literal in engine._FINDING_NEXT_ACTIONS[CODE]
    for path in (SKILL_PATH, SCHEMA_GUIDE):
        rows = _documented_finding_rows(path.read_text(encoding="utf-8"))
        assert literal in rows[CODE][1], f"{path.name} next action omits the literal"


def test_the_adopter_closeout_procedure_states_the_precondition() -> None:
    """*AC24*: the `cool-30-days` row names the obligation before cooling."""
    text = CLOSEOUT_GUIDE.read_text(encoding="utf-8")
    assert "declare source.parent on its workspace entry" in text


def test_the_parent_field_reference_states_the_cooling_interaction() -> None:
    """*AC26*: the `parent` row names what cooling does to an undeclared value."""
    text = SCHEMA_GUIDE.read_text(encoding="utf-8")
    assert "unestablished once the spec has cooled" in text


def test_the_shipped_command_emits_the_finding(tmp_path, engine) -> None:
    """*AC25*: the shipped CLI, run from inside the checkout, emits the code.

    Driven as a subprocess rather than in process because the run location is
    part of the observable — the script under test is the projected artifact an
    adopter invokes, not the module the rest of this suite imports. Probe 16
    established that exit 0 holds whether or not a finding is present, so the
    exit code is asserted as a constant rather than inferred from the payload.
    """
    root = tmp_path / "shipped"
    _fixture(root, engine, parent=None)

    completed = subprocess.run(
        [sys.executable, str(STATUS_SCRIPT), "reconcile", "--root", str(root)],
        capture_output=True,
        text=True,
        cwd=str(ROOT),
        check=False,
        timeout=120,
    )
    assert completed.returncode == 0, (
        f"exited {completed.returncode}: {completed.stderr}"
    )
    payload = json.loads(completed.stdout)
    codes = [
        (f["code"], f["path"]) for f in payload["canonical"]["findings"]
    ]
    assert (CODE, CHILD_PATH) in codes, codes
