"""The active-template inventory and the spine the routed templates share.

`architect-design` authors from three scope-routed templates and keeps a fourth
asset as an unrouted compatibility pointer. Four properties here are the ones a
reading pass does not catch.

**Order, not membership.** The subsystem spine is fixed *in order*. A set
comparison passes when two sections are swapped, and a swapped spine is a
different document architecture.

**A declared domain, not a discovered one.** ``MODEL_BEARING`` lives in this
module, never in the assets. A domain read from the artifact under test lets the
artifact shrink its own coverage: "every section carrying both markers" excuses
a section the moment a marker is deleted, and a list kept in the template's own
header moves that same self-selection one level up rather than removing it.
``test_a_renamed_section_reds`` is what proves the domain is independent.

**Wrapped questions.** A section's opening question is read as a paragraph, not
a line. A question wrapped across two source lines is correct and would fail a
line-based check.

**C4 directives, scanned per asset.** ``architect-diagram`` legitimately ships
``C4Context`` in its own testdata, so a pack-wide scan would red on correct
content. The scan is scoped to the design assets, which is where the accidental
reuse would land.
"""

from __future__ import annotations

import re
import shutil
from pathlib import Path

PACK_ROOT = Path(__file__).resolve().parents[3]
ASSETS = PACK_ROOT / ".apm" / "skills" / "architect-design" / "assets"

SUBSYSTEM = ASSETS / "subsystem-design.md"
APPLICATION = ASSETS / "application-system-design.md"
CHANGE = ASSETS / "architecture-change-design.md"
POINTER = ASSETS / "design-doc.md"

ROUTED = (APPLICATION, SUBSYSTEM, CHANGE)

# Exactly the Markdown assets the skill ships: three routed templates, the
# Stage-0 concept, and the retained pointer. A fifth file fails here rather
# than becoming a fourth scope a reader mistakes for routed.
EXPECTED_ASSETS = {
    "application-system-design.md",
    "architecture-change-design.md",
    "concept.md",
    "design-doc.md",
    "subsystem-design.md",
}

SPINE = (
    "Scope and Context",
    "Structural Model",
    "Runtime Model",
    "Contracts and Invariants",
    "Data and State",
    "Deployment and Operations",
    "Quality Scenarios and Verification",
    "Implementation Mapping",
    "Decisions, Alternatives, and Risks",
    "Rollout, Migration, and Reversal",
    "Open Questions",
)

CHANGE_SPINE = (
    "Scope and Baseline",
    "Structural Change",
    "Runtime Change",
    "Contract and Invariant Change",
    "Data/State Migration",
    "Deployment/Operational Change",
    "Quality Regression and Verification",
    "Build Mapping",
)

# Declared here on purpose — see the module docstring.
MODEL_BEARING = {
    APPLICATION.name: SPINE[:8],
    SUBSYSTEM.name: SPINE[:8],
    CHANGE.name: CHANGE_SPINE,
}

CONTRACT_COLUMNS = (
    "semantic name",
    "parties",
    "inputs",
    "outputs",
    "identity",
    "compatibility",
    "failure semantics",
    "invariant",
    "enforcement",
    "verification",
)

SCENARIO_PARTS = (
    "source",
    "stimulus",
    "environment",
    "artifact",
    "response",
    "measurable target",
    "business consequence",
    "mechanism",
    "verification",
)

FORBIDDEN_DIRECTIVES = ("C4Context", "C4Container", "architecture-beta")


def _strip_comments(text: str) -> str:
    """Drop HTML comments, so a commented example is not read as content."""
    return re.sub(r"<!--.*?-->", "", text, flags=re.S)


def _fenced_blocks(body: str, info: str) -> list[str]:
    """Return the bodies of fenced blocks carrying the given info string.

    Written against the fence grammar rather than one literal opener: a
    trailing space after the info string, a longer backtick run, and a tilde
    fence are all valid and would each make a shipped diagram vanish from the
    check, turning a correct template into a failure.
    """
    out: list[str] = []
    fence: str | None = None
    collecting = False
    buf: list[str] = []
    for line in body.splitlines():
        stripped = line.strip()
        if fence is None:
            match = re.match(r"(`{3,}|~{3,})\s*(\S*)", stripped)
            if match:
                fence = match.group(1)
                collecting = match.group(2).lower() == info.lower()
                buf = []
            continue
        run = len(stripped) - len(stripped.lstrip(fence[0]))
        if run >= len(fence) and not stripped[run:].strip():
            if collecting:
                out.append("\n".join(buf))
            fence, collecting, buf = None, False, []
            continue
        if collecting:
            buf.append(line)
    return out


def _sections(text: str) -> list[tuple[str, str]]:
    """Return each `##` section as (name, body), numeric prefix stripped."""
    out: list[tuple[str, str]] = []
    for chunk in re.split(r"^## ", text, flags=re.M)[1:]:
        head, _, body = chunk.partition("\n")
        out.append((re.sub(r"^\d+[.)]\s*", "", head.strip()), body))
    return out


def _first_paragraph(body: str) -> str:
    """Return the first non-blank paragraph, whitespace collapsed."""
    for block in re.split(r"\n\s*\n", body.strip()):
        if block.strip():
            return " ".join(block.split())
    return ""


def _section_body(path: Path, name: str) -> str:
    """Return one named section's body from a template."""
    for found, body in _sections(path.read_text(encoding="utf-8")):
        if found == name:
            return body
    raise AssertionError(f"{path.name} has no section {name!r}")


def test_the_assets_directory_holds_exactly_the_shipped_set() -> None:
    """Three routed templates, the concept, and the retained pointer."""
    found = {path.name for path in ASSETS.glob("*.md")}
    assert found == EXPECTED_ASSETS


def test_the_pointer_says_what_it_is_and_routes_nowhere() -> None:
    """A reader cannot mistake the retained asset for a fourth scope."""
    text = " ".join(POINTER.read_text(encoding="utf-8").split())
    assert "not routed" in text.lower()
    for routed in (APPLICATION, SUBSYSTEM, CHANGE):
        assert routed.name in text, routed.name


def test_the_subsystem_spine_is_carried_in_order() -> None:
    """Order is the assertion; a swapped spine is a different architecture."""
    found = tuple(name for name, _ in _sections(SUBSYSTEM.read_text(encoding="utf-8")))
    assert found == SPINE


def test_the_application_template_shares_the_spine() -> None:
    """Scope changes the zoom and the omissions, never the section set."""
    found = tuple(name for name, _ in _sections(APPLICATION.read_text(encoding="utf-8")))
    assert found == SPINE


def test_the_change_template_is_delta_shaped() -> None:
    """An architecture change records deltas, not a second current state."""
    found = tuple(name for name, _ in _sections(CHANGE.read_text(encoding="utf-8")))
    assert found == CHANGE_SPINE


def test_every_section_leads_with_its_named_question() -> None:
    """Read as a paragraph: a wrapped question is correct and must pass."""
    for path in ROUTED:
        for name, body in _sections(path.read_text(encoding="utf-8")):
            opening = _first_paragraph(body)
            assert opening.endswith("?"), (path.name, name, opening[:70])


def _assert_model_first(path: Path, sections: tuple[str, ...]) -> None:
    """The model-first contract itself, callable against any copy.

    Extracted so the mutation tests below drive *this* assertion rather than
    re-deriving what they expect. Re-derived mutation checks stay green when
    the production assertion is weakened or deleted, which makes them evidence
    about themselves rather than about the control.
    """
    text = path.read_text(encoding="utf-8")
    for name in sections:
        body = _section_body(path, name)
        assert body.count("<!-- model -->") == 1, (path.name, name)
        assert body.count("<!-- rationale -->") == 1, (path.name, name)
        assert body.index("<!-- model -->") < body.index("<!-- rationale -->"), (
            path.name,
            name,
        )
    assert text.count("<!-- model -->") == len(sections)


def test_every_model_bearing_section_puts_its_model_first() -> None:
    """Exactly one marker each, model first, over a domain declared here."""
    for path in ROUTED:
        _assert_model_first(path, MODEL_BEARING[path.name])


def test_a_renamed_section_reds(tmp_path: Path) -> None:
    """The domain is independent of the asset, so the asset cannot shrink it.

    Renaming a model-bearing heading must fail. If the check read its domain
    from the template, the rename would quietly remove that section from the
    domain and the suite would stay green with the model-first rule unproven.
    """
    copy = tmp_path / SUBSYSTEM.name
    shutil.copy(SUBSYSTEM, copy)
    # Renamed by pattern, not by one literal heading: hardcoding
    # `## 3. Runtime Model` means a renumbered or unnumbered template leaves
    # the mutation unapplied, and the test then reds for the wrong reason.
    renamed, count = re.subn(
        r"^## (\d+[.)]\s*)?Runtime Model\s*$",
        lambda m: f"## {m.group(1) or ''}Runtime Behaviour",
        copy.read_text(encoding="utf-8"),
        count=1,
        flags=re.M,
    )
    assert count == 1, "the mutation did not apply; the heading moved"
    copy.write_text(renamed, encoding="utf-8")
    try:
        _assert_model_first(copy, MODEL_BEARING[SUBSYSTEM.name])
    except AssertionError:
        return
    raise AssertionError("a renamed model-bearing section did not fail")


def test_a_deleted_model_marker_reds(tmp_path: Path) -> None:
    """The presence half is load-bearing, not incidental to the ordering."""
    copy = tmp_path / SUBSYSTEM.name
    shutil.copy(SUBSYSTEM, copy)
    copy.write_text(
        copy.read_text(encoding="utf-8").replace("<!-- model -->", "", 1),
        encoding="utf-8",
    )
    try:
        _assert_model_first(copy, MODEL_BEARING[SUBSYSTEM.name])
    except AssertionError:
        return
    raise AssertionError("a deleted model marker did not fail")


def test_the_contract_table_carries_every_column() -> None:
    """A contract with an unnamed identity or failure mode is not specified."""
    body = _section_body(SUBSYSTEM, "Contracts and Invariants")
    header = next(
        line for line in body.splitlines() if line.strip().startswith("|")
    ).lower()
    cells = {cell.strip() for cell in header.strip("| ").split("|")}
    for column in CONTRACT_COLUMNS:
        # Matched against the header's own cells, so a column named only in
        # the rationale prose below the table does not satisfy the check.
        assert any(column in cell for cell in cells), (column, sorted(cells))


def test_the_runtime_model_requires_a_failure_path() -> None:
    """One normal path and one failure-or-recovery path, both sequenced."""
    for path in (SUBSYSTEM, APPLICATION):
        body = _section_body(path, "Runtime Model")
        blocks = _fenced_blocks(body, "mermaid")
        sequences = [b for b in blocks if "sequenceDiagram" in b]
        assert len(sequences) >= 2, (path.name, len(sequences))
        # Two distinct diagrams, not one that mentions both words. A single
        # block naming "normal" and "failure" satisfies a whole-section
        # substring search while sequencing only one path.
        normal = [b for b in sequences if "normal" in b.lower()]
        recovery = [
            b
            for b in sequences
            if "failure" in b.lower() or "recovery" in b.lower()
        ]
        assert normal, path.name
        assert recovery, path.name
        assert set(map(id, normal)) != set(map(id, recovery)), path.name


def test_the_quality_section_carries_the_full_scenario_model() -> None:
    """Six scenario parts plus consequence, mechanism, and verification."""
    body = _section_body(SUBSYSTEM, "Quality Scenarios and Verification").lower()
    for part in SCENARIO_PARTS:
        assert part in body, part


def test_state_is_declared_rather_than_left_implied() -> None:
    """`stateless` is written, so an absent row cannot mean either thing."""
    body = _section_body(SUBSYSTEM, "Data and State").lower()
    assert "stateless" in body


def test_the_application_template_stays_at_its_own_zoom() -> None:
    """Person, System, Container — and none of the subsystem-level detail."""
    catalogue = _strip_comments(_section_body(APPLICATION, "Structural Model"))
    rows = [
        line for line in catalogue.splitlines()
        if line.strip().startswith("|") and "---" not in line
    ]
    types = " ".join(rows)
    for element in ("Person", "System", "Container"):
        # Scoped to the element-catalogue rows: a match anywhere in the file
        # is satisfied by prose or an authoring comment.
        assert element in types, element
    lowered = APPLICATION.read_text(encoding="utf-8").lower()
    for omitted in ("ports and adapters", "ports/adapters", "module mapping"):
        assert omitted not in lowered, omitted


def test_every_template_offers_the_header_fields_the_rubric_checks() -> None:
    """The rubric's header check has something to check.

    `design-doc-rubric.md` replaced the retired TL;DR sentence-count with a
    check on the structured header fields. A rubric checking a field no
    template provides is the same homeless-check defect in the other
    direction, and neither file's own suite would notice: the rubric's test
    reads the rubric, and the template's test read only its sections.
    """
    for path in ROUTED:
        header = path.read_text(encoding="utf-8").split("## ", 1)[0]
        assert "Decision sought" in header, path.name
        # The Title is the level-1 heading. Matched with re.M rather than
        # startswith: a template may open with an authoring comment block.
        assert re.search(r"^# \S", header, re.M), path.name


def test_the_change_template_names_its_baseline() -> None:
    """A delta is meaningless without the artifact it is a delta from."""
    header = CHANGE.read_text(encoding="utf-8").split("## ", 1)[0].lower()
    assert "current architecture" in header or "current-architecture" in header


def test_no_routed_template_carries_an_appendix() -> None:
    """Evidence cites or links; the general appendix is where it piles up."""
    for path in ROUTED:
        names = [name for name, _ in _sections(path.read_text(encoding="utf-8"))]
        assert not any(name.lower().startswith("appendix") for name in names), path.name


def test_no_routed_template_uses_experimental_mermaid_directives() -> None:
    """C4 semantics, standard Mermaid syntax.

    Scoped to the design assets: the diagram skill ships `C4Context` in its own
    testdata legitimately, and a pack-wide scan would red on that correct file.
    """
    for path in ROUTED:
        text = path.read_text(encoding="utf-8")
        for directive in FORBIDDEN_DIRECTIVES:
            assert directive not in text, (path.name, directive)
