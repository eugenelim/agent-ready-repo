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


# --- Relocated full-mode engine sequences -----------------------------------
#
# The `loop-engine` / `loop-cohort` sequences moved out of SKILL.md into
# `references/full-mode-engine.md`. Every control over their CONTENT now reads
# the reference, so none of them can see the reference go unreachable: delete a
# step's pointer and the commands are still present, still correct, and no
# longer findable from the step that fires them.
#
# Per owning step, not per file. A file-wide search stays green while one
# step's pointer is deleted, because the other steps carry the same
# destination.
_ENGINE_REFERENCE = "](references/full-mode-engine.md)"

_RELOCATED_SEQUENCES = (
    # (owning step start, step end, section cue named by the pointer)
    ("10. **Full mode:** run the init pair", "11. **Run every fired",
     "PLAN — init pair, or resume"),
    ("Transitions for this step:", "12. **Full mode:**",
     "PLAN — pre-EXECUTE review transitions"),
    ("12. **Full mode:** the **G-plan sequence**", "### Project-knowledge integration",
     "PLAN — the G-plan sequence"),
    ("**Full mode — wave routing.**", "**Pre-existing failure triage.**",
     "GATES — wave routing"),
    ("**A spec-backed run** normally writes", "**A direct-light run**",
     "REVIEW and the human gate"),
)

# A pointer summarises the sequence it replaces, and a summary is new prose --
# which is where an obligation silently widens or narrows. These are the
# qualifiers whose loss changes what the step requires, pinned per owning step.
# Narrow phrases, not a byte-pin: the surrounding wording stays editable.
_LOAD_BEARING_QUALIFIERS = (
    ("**A spec-backed run** normally writes", "**A direct-light run**",
     "if at least one reviewer produced a clean report"),
    ("10. **Full mode:** run the init pair", "11. **Run every fired",
     "the destructive reset pair"),
)


def _flatten(text: str) -> str:
    return re.sub(r"\s+", " ", text)


def test_every_relocated_sequence_is_reachable_from_its_owning_step() -> None:
    raw = _skill_text()
    for start, end, cue in _RELOCATED_SEQUENCES:
        assert start in raw, f"owning-step anchor vanished: {start!r}"
        assert end in raw, f"owning-step end anchor vanished: {end!r}"
        step = _flatten(raw[raw.index(start) : raw.index(end, raw.index(start))])
        assert _ENGINE_REFERENCE in step, f"{start!r} no longer routes to the engine reference"
        assert cue in step, f"{start!r} no longer names its section: {cue!r}"


def test_every_named_engine_section_exists_in_the_reference() -> None:
    """A pointer naming a section the reference lacks is a dead end.

    Paired with the arm above: that one proves the step points somewhere, this
    one proves the somewhere is real.
    """
    body = (REFERENCES / "full-mode-engine.md").read_text(encoding="utf-8")
    headings = [ln.lstrip("# ").strip() for ln in body.splitlines() if ln.startswith("## ")]
    for _, _, cue in _RELOCATED_SEQUENCES:
        assert any(h.startswith(cue) for h in headings), f"no section for cue {cue!r}"


def test_each_pointer_keeps_its_load_bearing_qualifier() -> None:
    """Unconditional prose in a pointer is how a relocated rule loses its edge.

    Dropping "if at least one reviewer produced a clean report" makes recording
    look mandatory when a run satisfied by deferred Nits must record nothing;
    widening "the destructive reset pair" to any reset gates unrelated work.
    Both shipped during this relocation and were caught only by review.
    """
    raw = _skill_text()
    for start, end, qualifier in _LOAD_BEARING_QUALIFIERS:
        step = _flatten(raw[raw.index(start) : raw.index(end, raw.index(start))])
        assert qualifier in step, f"{start!r} lost its qualifier: {qualifier!r}"


# --- Relocated skill-engineering provider handoff ----------------------------
#
# The provider handshake moved out of Step 1 PLAN into
# `references/skill-engineering-provider.md`. Unlike the engine relocation
# above, what moved is a containment control over untrusted provider text, so
# the entrypoint keeps a fail-closed guard: no provider is reached before the
# reference is loaded. These arms pin the guard and the rules the two pack
# suites in `test_work_loop_skill_engineering_reference_boundary.py` and
# `test_reviewer_project_knowledge_boundary.py` do not already cover.

_PROVIDER_REFERENCE = "references/skill-engineering-provider.md"


def test_no_provider_envelope_survives_in_skill_md() -> None:
    """The envelope's only home is the reference.

    Counted rather than asserted through a shell `grep`: `grep -c` exits
    non-zero when it matches nothing, so the passing case would read as a
    failure.
    """
    assert _skill_text().count("knowledge-evidence") == 0


def test_the_entrypoint_guard_fails_closed_before_the_link() -> None:
    """A predicate that only routes would let a mis-read reach provider text.

    The guard is what makes a mis-evaluated predicate yield *no* provider
    contact rather than ungoverned contact, so it must be stated, and stated
    before the reader is handed the link.
    """
    step = _flatten(_skill_text())
    guard = (
        "Do not resolve, invoke, or read any provider before that reference is "
        "loaded"
    )
    assert guard in step
    assert step.index(guard) < step.index("it carries the selection")


def test_the_entrypoint_keeps_its_consumer_declaration() -> None:
    """These four literals are read off this file by the roster consumer suite.

    Moving them into the reference would leave that suite reading a file its
    predicate may never load.
    """
    body = _skill_text()
    for literal in (
        "agent-skill-engineering-reference/v1",
        "skill-authoring",
        "skill-eval-ci",
        "knowledge provider unavailable",
    ):
        assert literal in body, literal
    for unassigned in ("skill-review", "agent-extension-design"):
        assert unassigned not in body, unassigned


def test_the_predicate_names_every_task_shape_it_covers() -> None:
    """A narrowed predicate silently un-governs the shapes it drops."""
    step = _flatten(_skill_text())
    assert (
        "Only when the task concerns a skill, a skill script or evaluation, "
        "agent-loop orchestration, a hook, or a plugin, follow"
    ) in step
    assert _PROVIDER_REFERENCE in step


def test_the_provider_reference_is_routed_exactly_once() -> None:
    rows = [
        line
        for line in _outside_fences(_skill_text())
        if line.startswith("|") and _PROVIDER_REFERENCE in line
    ]
    assert len(rows) == 1, rows


def test_the_reference_carries_the_rules_the_pack_suites_do_not_reach() -> None:
    """Coverage seam, stated so it cannot drift.

    The two pack suites assert containment ordering, the envelope, the
    refusal sentence and the seven-member closed set. Nothing asserted the
    selection, request-shape and do-not-locate rules, which would have moved
    unnoticed.
    """
    reference = _flatten((REFERENCES / "skill-engineering-provider.md").read_text(encoding="utf-8"))
    for rule in (
        "Before invoking or reading provider text, close selection.",
        "no call is made and no provider text is read until selection succeeds",
        "Make one call with no refinement",
        '"contract_version":"agent-skill-engineering-reference/v1"',
        "Do not locate the provider's implementation, generated router path, persistence, or corpus",
    ):
        assert rule in reference, rule
