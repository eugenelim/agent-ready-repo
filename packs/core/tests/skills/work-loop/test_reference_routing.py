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


def _outside_fences(text: str) -> list[str]:
    """Lines outside fenced code blocks.

    SKILL.md embeds shell blocks whose `# comment` lines would otherwise read as
    ATX headings — nine of them today. Counting those as anchors would let a
    dangling link resolve against a bash comment, so the control would stop
    being able to fail.
    """
    lines, in_fence = [], False
    for line in text.splitlines():
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            continue
        if not in_fence:
            lines.append(line)
    return lines


def _heading_anchors(text: str) -> set[str]:
    """GitHub-style slugs for the ATX headings in *text*, duplicates included.

    GitHub disambiguates repeated headings by appending `-1`, `-2`, … so a link
    to the second occurrence is legitimate and must not be reported dangling.
    """
    anchors: set[str] = set()
    seen: dict[str, int] = {}
    for line in _outside_fences(text):
        if not line.startswith("#"):
            continue
        title = line.lstrip("#").strip()
        slug = re.sub(r"\s+", "-", re.sub(r"[^a-z0-9\s-]", "", title.lower()).strip())
        if not slug:
            continue
        count = seen.get(slug, 0)
        anchors.add(slug if count == 0 else f"{slug}-{count}")
        seen[slug] = count + 1
    return anchors


def test_same_document_anchors_resolve_inside_skill_md() -> None:
    """Extracting a section must not leave a `](#…)` link pointing at the hole.

    This is the control for the defect class progressive disclosure creates:
    the heading moves to `references/`, the in-document link stays behind, and
    the reader reaches a dead anchor at the moment the rule applies.
    """
    skill = _skill_text()
    anchors = _heading_anchors(skill)
    prose = "\n".join(_outside_fences(skill))
    dangling = sorted(
        target for target in _SAME_DOC_ANCHOR.findall(prose) if target not in anchors
    )
    assert not dangling, (
        f"SKILL.md links to same-document anchors with no matching heading: "
        f"{dangling}. If the section moved to references/, retarget the link at "
        f"references/<file>.md#<anchor>."
    )


def test_reference_anchors_resolve_in_their_target_file() -> None:
    """A cross-file `](references/x.md#anchor)` must name a heading that exists.

    The anchor index is built by globbing this skill's own `references/`, so the
    check never joins a path out of link text — pack tests must stay anchored
    inside their owning pack.
    """
    index = {
        path.name: _heading_anchors(path.read_text(encoding="utf-8"))
        for path in sorted(REFERENCES.glob("*.md"))
    }
    prose = "\n".join(_outside_fences(_skill_text()))
    dangling = []
    for relative, anchor in _REFERENCE_ANCHOR.findall(prose):
        name = relative.rsplit("/", 1)[-1]
        if name not in index:
            dangling.append(f"{relative} (no such reference file)")
        elif anchor not in index[name]:
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
