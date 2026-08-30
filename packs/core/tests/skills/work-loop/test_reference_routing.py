from __future__ import annotations

import re
from pathlib import Path

PACK_ROOT = Path(__file__).resolve().parents[3]
WORK_LOOP_SKILL = PACK_ROOT / ".apm" / "skills" / "work-loop" / "SKILL.md"
REFERENCES = WORK_LOOP_SKILL.parent / "references"

# `[label](#anchor)` and `[label](references/file.md#anchor)`.
_SAME_DOC_ANCHOR = re.compile(r"\]\(#([a-z0-9][a-z0-9-]*)\)")
_REFERENCE_ANCHOR = re.compile(r"\]\((references/[a-z0-9-]+\.md)#([a-z0-9][a-z0-9-]*)\)")


def _skill_text() -> str:
    return WORK_LOOP_SKILL.read_text(encoding="utf-8")


def _heading_anchors(text: str) -> set[str]:
    """GitHub-style slugs for every ATX heading in *text*."""
    anchors = set()
    for line in text.splitlines():
        if not line.startswith("#"):
            continue
        title = line.lstrip("#").strip()
        slug = re.sub(r"[^a-z0-9\s-]", "", title.lower())
        anchors.add(re.sub(r"\s+", "-", slug.strip()))
    return anchors


def test_same_document_anchors_resolve_inside_skill_md() -> None:
    """Extracting a section must not leave a `](#…)` link pointing at the hole.

    This is the control for the defect class progressive disclosure creates:
    the heading moves to `references/`, the in-document link stays behind, and
    the reader reaches a dead anchor at the moment the rule applies.
    """
    skill = _skill_text()
    anchors = _heading_anchors(skill)
    dangling = sorted(
        target for target in _SAME_DOC_ANCHOR.findall(skill) if target not in anchors
    )
    assert not dangling, (
        f"SKILL.md links to same-document anchors with no matching heading: "
        f"{dangling}. If the section moved to references/, retarget the link at "
        f"references/<file>.md#<anchor>."
    )


def test_reference_anchors_resolve_in_their_target_file() -> None:
    """A cross-file `](references/x.md#anchor)` must name a heading that exists."""
    dangling = []
    for relative, anchor in _REFERENCE_ANCHOR.findall(_skill_text()):
        target = WORK_LOOP_SKILL.parent / relative
        if not target.is_file():
            dangling.append(f"{relative} (missing file)")
        elif anchor not in _heading_anchors(target.read_text(encoding="utf-8")):
            dangling.append(f"{relative}#{anchor}")
    assert not dangling, f"unresolvable reference anchors from SKILL.md: {dangling}"


def test_supervisor_mode_pointer_routes_fan_out_rules() -> None:
    skill = _skill_text()
    assert "[Supervisor and fan-out procedure](references/supervisor-mode.md)" in skill
    reference = (REFERENCES / "supervisor-mode.md").read_text(encoding="utf-8")
    for statement in (
        "single message (one Agent use per target)",
        "Barrier-wait",
        "missing report = `failed`",
        "parallel fan-out",
        "those verbs exit non-zero",
        "wave-complete",
    ):
        assert statement in reference


def test_unattended_loops_pointer_routes_eligibility_rules() -> None:
    skill = _skill_text()
    assert "[Unattended-loop eligibility](references/unattended-loops.md)" in skill
    reference = (REFERENCES / "unattended-loops.md").read_text(encoding="utf-8")
    for statement in (
        "fully mechanical",
        "single-context-window items",
        "verification is reliable",
        "in-session loop at least once",
        "sensitive surface",
        "hard caps",
        "review every commit after",
    ):
        assert statement in reference
