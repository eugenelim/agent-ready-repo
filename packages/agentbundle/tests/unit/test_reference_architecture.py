"""Goal-based presence / invariant checks for the reference-architecture feature.

Covers, per the spec's Testing Strategy:
  - T1: the arc42 template asset exists, is arc42-shaped, stack-neutral,
    carries the fill-only guidance, and is adopter-clean.
  - T3: the `adapt-to-project` SKILL.md documents the Class-3
    reference-architecture harvest, and the harvest subsection is adopter-clean.
  - T4: the CONVENTIONS seed seats `reference.md` in the document-hierarchy
    diagram, and the lines this feature added are adopter-clean.
  - T5: the four user guides exist, every intra-repo relative link in them
    resolves on disk (file + anchor), the reference guide states all four
    stack-pack-contract clauses, and the guides are adopter-clean.

"Adopter-clean" = no internal-repo reference: no ``RFC-NNNN`` / ``ADR-NNNN``
token and no ``docs/(specs|rfc|adr)/`` path string. ``lint-catalogue-seeds`` enforces only
RFC-number absence and only under ``packs/*/seeds/**`` — it covers neither the
``.apm/`` template/SKILL nor the ``docs/guides/`` files — so these checks carry
the invariant for the surfaces lint misses.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]

ADAPT_SKILL_DIR = REPO_ROOT / "packs" / "core" / ".apm" / "skills" / "adapt-to-project"
TEMPLATE = ADAPT_SKILL_DIR / "assets" / "reference.md"
SKILL = ADAPT_SKILL_DIR / "SKILL.md"
CONVENTIONS_SEED = REPO_ROOT / "packs" / "core" / "seeds" / "docs" / "CONVENTIONS.md"

GUIDES_DIR = REPO_ROOT / "docs" / "guides"
GUIDES = {
    "tutorial": GUIDES_DIR / "architect" / "tutorials" / "create-your-reference-architecture.md",
    "how-to": GUIDES_DIR / "architect" / "how-to" / "establish-reference-architecture.md",
    "explanation": GUIDES_DIR / "core" / "explanation" / "foundation-vs-map.md",
    "reference": GUIDES_DIR / "architect" / "reference" / "reference-architecture.md",
}

# No RFC-NNNN / ADR-NNNN token, no docs/(specs|rfc|adr)/ path string.
_INTERNAL_REF = re.compile(r"RFC-\d{4}|ADR-\d{4}|docs/(?:specs|rfc|adr)/")
# Markdown inline links: [text](target). Anchors and titles handled downstream.
_LINK = re.compile(r"\]\(([^)]+)\)")


def _assert_adopter_clean(text: str, where: str) -> None:
    hits = _INTERNAL_REF.findall(text)
    assert not hits, f"{where} leaks internal-repo reference(s): {hits}"


def _slugify(heading: str) -> str:
    """GitHub-flavoured heading -> anchor slug.

    A deliberately incomplete subset: it does NOT dedupe colliding headings
    (GitHub appends ``-1``/``-2``) and strips punctuation more bluntly. Valid
    only for the simple kebab headings the current guides use; revisit if a
    guide adds duplicate or punctuation-heavy headings.
    """
    slug = heading.strip().lower()
    slug = slug.replace("`", "")
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"\s+", "-", slug)
    return slug


def _heading_slugs(md_path: Path) -> set[str]:
    slugs: set[str] = set()
    for line in md_path.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^#{1,6}\s+(.*)$", line)
        if m:
            slugs.add(_slugify(m.group(1)))
    return slugs


# --- T1: template asset ---------------------------------------------------

ARC42_SECTIONS = (
    "## Constraints",
    "## Solution strategy",
    "## Building-block view / component catalogue",
    "## Crosscutting concepts / standards",
)


def test_template_exists() -> None:
    assert TEMPLATE.is_file(), f"Expected arc42 template at {TEMPLATE}"


def test_template_has_four_arc42_sections() -> None:
    body = TEMPLATE.read_text(encoding="utf-8")
    for heading in ARC42_SECTIONS:
        assert f"\n{heading}\n" in f"\n{body}\n", f"missing section: {heading}"


def test_template_is_stack_neutral() -> None:
    body = TEMPLATE.read_text(encoding="utf-8").lower()
    # Collision-resistant framework tokens, word-boundary anchored.
    tokens = ["react", "spring", "django", "fastapi", "express.js", "postgresql"]
    for tok in tokens:
        assert not re.search(rf"\b{re.escape(tok)}\b", body), (
            f"template names a specific framework ({tok!r}) — must stay stack-neutral"
        )


def test_template_carries_fill_only_guidance() -> None:
    body = TEMPLATE.read_text(encoding="utf-8")
    assert "only when you have real architecture decisions" in body


def test_template_is_adopter_clean() -> None:
    _assert_adopter_clean(TEMPLATE.read_text(encoding="utf-8"), str(TEMPLATE))


# --- T3: adapt-to-project harvest ----------------------------------------


def _harvest_subsection() -> str:
    body = SKILL.read_text(encoding="utf-8")
    start_marker = "**Reference-architecture harvest.**"
    end_marker = "## Class 4"
    assert start_marker in body, (
        f"harvest heading {start_marker!r} moved — update this slice"
    )
    start = body.index(start_marker)
    assert end_marker in body[start:], (
        f"Class-4 boundary {end_marker!r} moved — update this slice"
    )
    end = body.index(end_marker, start)
    return body[start:end]


def test_skill_documents_reference_architecture_harvest() -> None:
    section = _harvest_subsection()
    lowered = section.lower()
    # detect -> instantiate -> propose draft -> repo-scope path-jail ->
    # per-finding accept/edit/decline, never authoritative pre-confirmation.
    assert "detect" in lowered
    assert "instantiate" in lowered
    assert "docs/architecture/reference.md" in section
    assert "repo-scope path-jail" in section
    assert "accept / edit / decline" in section.lower() or "accept/edit/decline" in lowered
    assert "never" in lowered and "confirm" in lowered


def test_harvest_subsection_is_adopter_clean() -> None:
    _assert_adopter_clean(_harvest_subsection(), "adapt-to-project harvest subsection")


# --- T4: CONVENTIONS diagram ---------------------------------------------


def _conventions_added_block() -> str:
    """The diagram node children + the descriptive/normative gloss this feature
    added — the lines the adopter-clean grep must be scoped to (the document at
    large legitimately names RFC/ADR/docs paths elsewhere)."""
    body = CONVENTIONS_SEED.read_text(encoding="utf-8")
    start_marker = "Inside `architecture/`, the two docs play opposite roles"
    end_marker = "The bottom layers cite the upper layers"
    assert start_marker in body, (
        f"CONVENTIONS gloss {start_marker!r} moved — update this slice"
    )
    start = body.index(start_marker)
    assert end_marker in body[start:], (
        f"CONVENTIONS marker {end_marker!r} moved — update this slice"
    )
    end = body.index(end_marker, start)
    return body[start:end]


def test_conventions_seats_reference_md() -> None:
    body = CONVENTIONS_SEED.read_text(encoding="utf-8")
    assert "reference.md (golden" in body, "diagram does not seat reference.md"
    assert "overview.md (map" in body, "diagram should enumerate overview.md too"
    gloss = _conventions_added_block()
    assert "**normative**" in gloss and "**descriptive**" in gloss


def test_conventions_added_block_is_adopter_clean() -> None:
    _assert_adopter_clean(_conventions_added_block(), "CONVENTIONS diagram edit")


def test_conventions_diagram_rows_aligned() -> None:
    """The architecture/product double-box is fixed-width ASCII; the rows this
    feature added are hand-aligned. Guard against a silent column break: every
    row of the box (top border through bottom border) must be the same width.
    """
    lines = CONVENTIONS_SEED.read_text(encoding="utf-8").splitlines()
    # The box top border is the line with two top-corners; bottom is two
    # bottom-corners. The architecture/product boxes are the first such pair.
    top = next(
        i for i, ln in enumerate(lines)
        if ln.startswith("   ┌") and ln.count("┐") == 2
    )
    bottom = next(
        i for i, ln in enumerate(lines[top:], start=top)
        if ln.startswith("   └") and ln.count("┘") == 2
    )
    box_rows = lines[top : bottom + 1]
    widths = {len(r) for r in box_rows}
    assert len(widths) == 1, (
        "architecture/product diagram rows are not equal width — a box column "
        f"broke: row widths seen = {sorted(widths)}"
    )


# --- T5: user guides ------------------------------------------------------


def test_four_guides_exist() -> None:
    for quadrant, path in GUIDES.items():
        assert path.is_file(), f"missing {quadrant} guide at {path}"


def test_guide_intra_repo_links_resolve() -> None:
    for path in GUIDES.values():
        body = path.read_text(encoding="utf-8")
        for target in _LINK.findall(body):
            target = target.strip()
            if target.startswith(("http://", "https://", "mailto:")):
                continue
            if target.startswith("#"):
                # same-file anchor
                anchor = target[1:]
                assert anchor in _heading_slugs(path), (
                    f"{path.name}: same-file anchor #{anchor} has no heading"
                )
                continue
            file_part, _, anchor = target.partition("#")
            resolved = (path.parent / file_part).resolve()
            assert resolved.is_file(), (
                f"{path.name}: link target {target!r} does not resolve to a file"
            )
            if anchor:
                assert anchor in _heading_slugs(resolved), (
                    f"{path.name}: anchor #{anchor} not found in {resolved.name}"
                )


def test_reference_guide_states_four_contract_clauses() -> None:
    body = GUIDES["reference"].read_text(encoding="utf-8").lower()
    # 1. sole-producer => no collision
    assert "sole producer" in body or "sole-producer" in body
    assert "no collision" in body
    # 2. two-producer => .upstream companion + merge
    assert ".upstream" in body
    assert "merge" in body
    # 3. never overview.md
    assert "never `overview.md`" in body or "never overview.md" in body
    # 4. no bundler override field
    assert "no bundler override field" in body or "no override field" in body


def test_guides_are_adopter_clean() -> None:
    for quadrant, path in GUIDES.items():
        _assert_adopter_clean(path.read_text(encoding="utf-8"), f"{quadrant} guide")


def test_ride_along_links_to_reference_page_resolve() -> None:
    """The reference-page index entry and the reverse cross-link added to the
    pre-existing sibling both point at the new reference guide; guard them so a
    future rename of the page doesn't silently break these two inbound links.
    """
    # Post per-pack migration (ADR-0020), the reference page and its two
    # inbound links live in three different homes: the page under
    # `architect/`, the quadrant index under `_shared/`, the sibling
    # cross-link under `core/`.
    ref_page = GUIDES_DIR / "architect" / "reference" / "reference-architecture.md"
    for src in (
        GUIDES_DIR / "_shared" / "reference" / "README.md",
        GUIDES_DIR / "core" / "reference" / "spec-shape-and-lld.md",
    ):
        body = src.read_text(encoding="utf-8")
        assert "reference-architecture.md" in body, (
            f"{src.name} should link to reference-architecture.md"
        )
        assert ref_page.is_file(), (
            "reference-architecture.md link target does not resolve"
        )
