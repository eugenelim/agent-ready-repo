"""Source checks for the switched skill: verbs, role pairings, close step, evals, links.

Facts of the tree, not of a run. Each engine-owned action names a supervisor verb,
no skill file other than the rules file and the light-mode reference pairs a
reviewer role with its condition, the close step names the work-item capture, and
every eval file and relative link in the work-loop and new-spec skills holds.
"""

from __future__ import annotations

import ast
import json
import os
import re
from pathlib import Path

import pytest

PACK_ROOT = Path(__file__).resolve().parents[3]
WORK_LOOP = PACK_ROOT / ".apm" / "skills" / "work-loop"
NEW_SPEC = PACK_ROOT / ".apm" / "skills" / "new-spec"
SKILL = WORK_LOOP / "SKILL.md"
SUPERVISOR_REFERENCE = WORK_LOOP / "references" / "supervisor.md"
VERBS = ("start", "next", "report", "status", "resolve-effect")

# The spec's list of engine-owned actions (run initialization, phase transitions, plan
# approval and locking, scheduling, wave advance, attempt and dispatch recording,
# full-mode review recording, status, identity, and reset). Each names the row of the
# supervisor reference's action table that homes it, the verb that row must name, and
# the verb-specific statement the row must keep: removing the statement fails the check.
ENGINE_ACTIONS = (
    ("Run initialization", "start", "start"),
    ("plan approval", "start", "start"),
    ("plan locking", "start", "start"),
    ("Phase transitions", "next", "derives the one current action from committed facts"),
    ("scheduling", "next", "task scheduling in dependency order"),
    ("wave advance", "next", "no wave or phase is set by hand"),
    ("Attempt and dispatch recording", "next", "`next` opens the attempt, `report` closes it"),
    ("Attempt and dispatch recording", "report", "`next` opens the attempt, `report` closes it"),
    (
        "Full-mode review recording", "report",
        "`report` of a selection, a review report, an assessment, or a human decision",
    ),
    ("Status", "status", "which prints the run id, stage, and retry count"),
    ("identity", "status", "which prints the run id, stage, and retry count"),
    ("Reset", "start", "a run is never reset"),
)
# The verb reference the skill itself must carry for each verb it routes to.
SKILL_VERB_COMMANDS = ("start", "next", "report", "status")


def _flat(text: str) -> str:
    return " ".join(text.split())


def _action_rows() -> dict[str, str]:
    rows: dict[str, str] = {}
    text = SUPERVISOR_REFERENCE.read_text(encoding="utf-8")
    block = text.split("Each action a procedure engine would own", 1)[1].split("Exit codes:", 1)[0]
    for line in block.splitlines():
        if line.startswith("|") and not line.startswith(("| Action", "| ---")):
            action, verb = (cell.strip() for cell in line.strip("|").split("|", 1))
            rows[action] = verb
    return rows


def _check_actions(rows: dict[str, str]) -> list[str]:
    """Return one finding per engine-owned action whose home row is missing or unspecific."""
    findings = []
    for fragment, verb, statement in ENGINE_ACTIONS:
        homes = [f"{action} | {cell}" for action, cell in rows.items()
                 if fragment.lower() in action.lower()]
        if not homes:
            findings.append(f"no row for the action {fragment!r}")
        elif not any(f"`{verb}" in home for home in homes):
            findings.append(f"{fragment!r} does not name `{verb}`")
        elif not any(statement in home for home in homes):
            findings.append(f"{fragment!r} lost its statement {statement!r}")
    return findings


def test_each_engine_owned_action_names_a_supervisor_verb() -> None:
    assert _check_actions(_action_rows()) == []
    reference = SUPERVISOR_REFERENCE.read_text(encoding="utf-8")
    for verb in VERBS:
        assert f"`{verb}" in reference, verb
    skill = SKILL.read_text(encoding="utf-8")
    for verb in SKILL_VERB_COMMANDS:
        assert f"work-supervisor.py' {verb}" in skill, verb


def _without(rows: dict[str, str], text: str) -> dict[str, str]:
    """*rows* with *text* removed from every action and verb cell."""
    return {a.replace(text, ""): c.replace(text, "") for a, c in rows.items()}


def test_the_action_check_fails_when_a_statement_or_a_row_is_removed() -> None:
    rows = _action_rows()
    scheduling = _check_actions(_without(rows, "task scheduling in dependency order"))
    assert any("'scheduling'" in f for f in scheduling), scheduling
    wave = _check_actions(_without(rows, "no wave or phase is set by hand"))
    assert any("'wave advance'" in f for f in wave), wave
    reset = _check_actions({a: c for a, c in rows.items() if "reset" not in a.lower()})
    assert any("'Reset'" in f for f in reset), reset
    wrong_verb = _check_actions({a: c.replace("`start`", "`next`") for a, c in rows.items()})
    assert any("'Run initialization'" in f for f in wrong_verb), wrong_verb


_ITEM_START = re.compile(r"\s*(\||[-*] |\d+\. )")
_EXEMPT = {"review-rules.json", "light-mode.md"}
_TEXT_SUFFIXES = {".md", ".json", ".toml", ".py", ".txt", ".yaml", ".yml"}


def _items(path: Path) -> list[tuple[int, str]]:
    """The table rows and list items of a Markdown file, or every line of any other text file.

    A list item runs on through its wrapped lines until a blank line or the next item.
    """
    lines = path.read_text(encoding="utf-8").splitlines()
    if path.suffix != ".md":
        return list(enumerate(lines, 1))
    found: list[tuple[int, str]] = []
    current: list[str] = []
    start = 0
    for number, line in enumerate(lines, 1):
        if _ITEM_START.match(line):
            if current:
                found.append((start, " ".join(current)))
            current, start = [line], number
        elif current and line.strip() and not line.startswith("#"):
            current.append(line)
        else:
            if current:
                found.append((start, " ".join(current)))
            current = []
    if current:
        found.append((start, " ".join(current)))
    return found


def _role_pattern(role: str) -> re.Pattern[str]:
    """The role name quoted, backticked, or bare, never inside a longer name."""
    return re.compile(rf"(?<![\w-]){re.escape(role)}(?![\w-])", re.IGNORECASE)


def _pairings(text_by_item: list[tuple[str, int, str]], roles: list[dict]) -> list[str]:
    """Every item that names a role together with its condition or boundary words."""
    offenders = []
    for name, number, item in text_by_item:
        flat = _flat(item).lower()
        for role in roles:
            if not _role_pattern(role["role"]).search(flat):
                continue
            condition = _flat(role["condition"]).strip("*()").lower()
            words = _flat(role["boundary"]).lower().split()
            runs = {" ".join(words[i : i + 6]) for i in range(max(len(words) - 5, 0))}
            if condition in flat or any(run in flat for run in runs):
                offenders.append(f"{name}:{number}: {role['role']}")
    return offenders


def _skill_items() -> list[tuple[str, int, str]]:
    found = []
    for path in sorted(WORK_LOOP.rglob("*")):
        if (
            not path.is_file()
            or path.name in _EXEMPT
            or path.suffix not in _TEXT_SUFFIXES
            or "__pycache__" in path.parts
        ):
            continue
        rel = path.relative_to(WORK_LOOP).as_posix()
        found.extend((rel, number, item) for number, item in _items(path))
    return found


def _roles() -> list[dict]:
    """Every role in the rules file, the always-run roles included."""
    return json.loads((WORK_LOOP / "review-rules.json").read_text(encoding="utf-8"))["roles"]


def test_no_file_pairs_a_reviewer_role_with_its_condition_or_boundary() -> None:
    roles = _roles()
    assert {r["kind"] for r in roles} >= {"always", "conditional"}
    assert _pairings(_skill_items(), roles) == []


def test_the_pairing_check_sees_a_planted_pairing_in_each_role_spelling() -> None:
    """Positive control: a planted pairing is found for every role, quoted or not."""
    roles = _roles()
    for role in roles:
        condition = _flat(role["condition"]).strip("*()")
        for spelling in (f"`{role['role']}`", f'"{role["role"]}"', role["role"]):
            planted = [("planted.md", 1, f"- {spelling} runs when {condition}")]
            assert _pairings(planted, roles) == ["planted.md:1: " + role["role"]], (role, spelling)
    boundary = " ".join(roles[1]["boundary"].split()[:8])
    assert _pairings([("p.json", 3, f'"{roles[1]["role"]} {boundary}"')], roles)
    assert _pairings([("p.md", 2, f"- {roles[1]['role']} alone")], roles) == []


def test_the_close_step_names_the_work_item_capture() -> None:
    text = SKILL.read_text(encoding="utf-8")
    capture = text.split("\n## Capture\n", 1)[1].split("\n## ", 1)[0]
    close = _flat(capture.split("**Close step.**", 1)[1])
    assert "`work-item` capture" in close
    assert "references/work-item-capture.md" in close


def _evals(skill: Path) -> list[dict]:
    data = json.loads((skill / "evals" / "evals.json").read_text(encoding="utf-8"))
    assert data["skill_name"] == skill.name
    return data["evals"]


@pytest.mark.parametrize("skill", [WORK_LOOP, NEW_SPEC], ids=lambda p: p.name)
def test_every_eval_is_well_formed_and_unique(skill: Path) -> None:
    evals = _evals(skill)
    ids = [e["id"] for e in evals]
    assert len(ids) == len(set(ids))
    for case in evals:
        assert case["prompt"].strip() and case["expected_output"].strip(), case["id"]
        assert case["assertions"] and all(
            isinstance(a, str) and a.strip() for a in case["assertions"]
        ), case["id"]


def test_the_work_loop_evals_teach_the_supervisor_and_no_retired_engine() -> None:
    rendered = json.dumps(_evals(WORK_LOOP))
    assert "work-supervisor.py" in rendered
    for retired in ("loop-engine", "loop-cohort", "dispatch-receipt", "wave-passed"):
        assert retired not in rendered, retired


def test_the_new_spec_evals_carry_the_post_lock_plan_routes() -> None:
    ids = {e["id"] for e in _evals(NEW_SPEC)}
    assert {
        "post-approval-plan-changes-amendment-or-working-plan",
        "implementation-discovered-grounding-goes-to-the-design",
    } <= ids


def _slug(heading: str) -> str:
    """The GitHub anchor for a heading: lowercase, punctuation dropped, spaces to hyphens."""
    text = re.sub(r"[`*_]", "", heading).strip().lower()
    return re.sub(r"\s", "-", re.sub(r"[^\w\s-]", "", text))


def _headings(path: Path) -> list[str]:
    in_fence = False
    found = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
        elif not in_fence and (m := re.match(r"#{1,6}\s+(.*?)\s*#*\s*$", line)):
            found.append(m.group(1))
    return found


_LINK = re.compile(r"\]\(([^)#\s]*)(?:#([^)\s]*))?\)(\s*§\s*\*([^*]+)\*)?")


def _broken_links(skill: Path) -> list[str]:
    broken = []
    for path in sorted(skill.rglob("*.md")):
        text = path.read_text(encoding="utf-8")
        for match in _LINK.finditer(text):
            target, fragment, _pointer, section = match.groups()
            if target.startswith(("http://", "https://", "mailto:")):
                continue
            resolved = path if not target else Path(os.path.normpath(path.parent / target))
            label = f"{path.relative_to(skill)} -> {target}"
            if not resolved.exists():
                broken.append(label)
                continue
            if resolved.suffix != ".md":
                continue
            headings = _headings(resolved)
            if fragment and fragment not in {_slug(h) for h in headings}:
                broken.append(f"{label}#{fragment}")
            if section and re.sub(r"[`*]", "", section).strip() not in {
                re.sub(r"[`*]", "", h) for h in headings
            }:
                broken.append(f"{label} § {section.strip()}")
    return broken


@pytest.mark.parametrize("skill", [WORK_LOOP, NEW_SPEC], ids=lambda p: p.name)
def test_every_relative_link_anchor_and_section_pointer_resolves(skill: Path) -> None:
    assert _broken_links(skill) == []


def test_the_link_check_fails_on_a_missing_anchor_and_a_missing_section(tmp_path: Path) -> None:
    skill = tmp_path / "skill"
    skill.mkdir()
    (skill / "target.md").write_text("# Title\n\n## The loop\n", encoding="utf-8")
    (skill / "page.md").write_text(
        "[ok](target.md#the-loop) [ok2](target.md) \u00a7 *The loop*\n"
        "[bad](target.md#no-such) [bad2](target.md) \u00a7 *No such section*\n"
        "[self](#nowhere)\n",
        encoding="utf-8",
    )
    broken = _broken_links(skill)
    assert broken == [
        "page.md -> target.md#no-such",
        "page.md -> target.md \u00a7 No such section",
        "page.md -> #nowhere",
    ]


# ── one owner per rule ────────────────────────────────────────────────────────

SCRIPTS = WORK_LOOP / "scripts"
# Codes built from a condition or a dynamic value, so no literal call carries them.
COMPUTED_REFUSAL_CODES = {"attempt-refused", "run-locked", "internal-error"}
_CODE = re.compile(r"[a-z]+(-[a-z0-9]+)+")


def _refusal_codes() -> set[str]:
    """Every code a supervisor script can refuse with, read from the sources."""
    codes = set(COMPUTED_REFUSAL_CODES)
    for path in [*sorted(SCRIPTS.glob("_supervisor_*.py")), SCRIPTS / "work-supervisor.py"]:
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if isinstance(node, ast.Call):
                func = node.func
                name = getattr(func, "id", None) or getattr(func, "attr", "")
                if name in {"Refusal", "ProjectionRefused", "_refusal", "SupervisorGitError"}:
                    first = node.args[0] if node.args else None
                    if isinstance(first, ast.Constant) and isinstance(first.value, str):
                        codes.add(first.value)
            elif isinstance(node, ast.Assign) and any(
                getattr(t, "id", "") in {"CHANGE_OWNERS", "TERMINAL_INTENT_CHANGE"}
                for t in node.targets
            ):
                for inner in ast.walk(node.value):
                    if isinstance(inner, ast.Tuple) and inner.elts:
                        head = inner.elts[0]
                        if isinstance(head, ast.Constant) and isinstance(head.value, str):
                            codes.add(head.value)
    return {c for c in codes if _CODE.fullmatch(c)}


def _refusal_section() -> str:
    text = SUPERVISOR_REFERENCE.read_text(encoding="utf-8")
    return text.split("\n## Refusals and their owners\n", 1)[1].split("\n## ", 1)[0]


def test_every_refusal_code_has_a_row_in_the_supervisor_reference() -> None:
    documented = set(re.findall(r"`([a-z]+(?:-[a-z0-9]+)+)`", _refusal_section()))
    codes = _refusal_codes()
    assert {"supervisor-changed", "recovery-leftovers", "replan-declined"} <= codes
    assert sorted(codes - documented) == []


def test_unsupported_git_version_is_a_usage_error_and_never_a_refusal() -> None:
    reference = SUPERVISOR_REFERENCE.read_text(encoding="utf-8")
    assert "`unsupported-git-version` is not a refusal" in reference
    row = [ln for ln in _refusal_section().splitlines() if "unsupported-git-config" in ln]
    assert row and "unsupported-git-version" not in row[0]
    assert "3 only from `status --check`" in _flat(reference)


def test_the_refusal_table_has_one_home() -> None:
    codes = _refusal_codes()
    elsewhere = []
    for path in sorted(WORK_LOOP.rglob("*.md")):
        if path == SUPERVISOR_REFERENCE:
            continue
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            first = re.match(r"\|\s*`([a-z]+(?:-[a-z0-9]+)+)`", line)
            if first and first.group(1) in codes:
                elsewhere.append(f"{path.relative_to(WORK_LOOP)}:{number}")
    assert elsewhere == []


OPEN_ATTEMPT_POINTERS = (
    "SKILL.md", "references/tdd-stubs.md", "references/delivery-contract-lifecycle.md",
)


def test_the_open_attempt_rule_has_one_owner_and_three_short_pointers() -> None:
    reference = _flat(SUPERVISOR_REFERENCE.read_text(encoding="utf-8"))
    assert "The open-attempt rule" in reference and "`attempt-residue`" in reference
    for relative in OPEN_ATTEMPT_POINTERS:
        text = (WORK_LOOP / relative).read_text(encoding="utf-8")
        statements = [ln for ln in text.splitlines() if "attempt is open" in ln]
        assert len(statements) == 1, (relative, statements)
        around = text[text.index(statements[0]) : text.index(statements[0]) + 400]
        assert "supervisor.md" in around, relative
        assert "attempt-residue" not in text, relative
