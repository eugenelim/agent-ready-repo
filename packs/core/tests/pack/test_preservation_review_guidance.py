"""Content pins for the typed-report section and the preservation lens checks.

Pins the two reviewer files only; the guide sentence is checked outside the
pack, because a pack test may not read above ``packs/core``.

Spec: docs/specs/grounding-preservation-review/spec.md
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

AGENTS = Path(__file__).resolve().parents[2] / ".apm" / "agents"
ADVERSARIAL = AGENTS / "adversarial-reviewer.md"
QUALITY = AGENTS / "quality-engineer.md"
REVIEWERS = [ADVERSARIAL, QUALITY]

FINDING_FIELDS = (
    "schema_version", "finding_id", "rule_ref", "observation",
    "reachable_path", "actual_failure", "affected_acceptance_criteria",
    "evidence_refs", "material",
)
CALLER_FIELDS = ("schema_version", "report_id", "role", "subject", "lineage")
STATUSES = ("clean", "findings", "unable", "indeterminate")
FORBIDDEN_WORDS = ("preservation finding", "adapt-to-project", "code intelligence")
SECTION_RE = re.compile(r"^## Typed report\n.*?(?=^## )", re.S | re.M)


def _read(path: Path) -> str:
    """Return the file text."""
    return path.read_text(encoding="utf-8")


def _section(path: Path) -> str:
    """Return the typed-report section of a reviewer file, or fail."""
    match = SECTION_RE.search(_read(path))
    assert match, f"{path.name} has no typed-report section"
    return match.group(0)


def _flat(text: str) -> str:
    """Collapse whitespace so wrapped sentences match."""
    return " ".join(text.split())


def _check(path: Path, heading: str, number: int) -> str:
    """Return the text of numbered check ``number`` inside ``heading``'s block."""
    text = _read(path)
    start = text.index(heading)
    nxt = re.search(r"^#{2,3} ", text[start + len(heading):], re.M)
    block = text[start: start + len(heading) + (nxt.start() if nxt else len(text))]
    match = re.search(rf"^{number}\. .*?(?=^\d+\. |\Z)", block, re.S | re.M)
    assert match, f"{path.name}: check {number} missing under {heading!r}"
    return match.group(0)


@pytest.mark.parametrize("path", REVIEWERS, ids=lambda p: p.stem)
def test_ac0001_one_section_per_file(path: Path) -> None:
    """AC-0001: exactly one typed-report section, placed before the vague-feedback head."""
    text = _read(path)
    assert len(re.findall(r"^## Typed report$", text, re.M)) == 1
    assert _section(path).endswith("\n\n")
    assert text.index("## Typed report") < text.index("## Vague feedback is unhelpful feedback")
    assert re.search(r"\n\n## Typed report\n", text)
    assert _section(path) + "## Vague feedback" in text


def test_ac0001_sections_identical() -> None:
    """AC-0001: the two sections are byte-identical."""
    assert _section(ADVERSARIAL) == _section(QUALITY)


@pytest.mark.parametrize("path", REVIEWERS, ids=lambda p: p.stem)
def test_ac0002_fields_and_statuses(path: Path) -> None:
    """AC-0002: finding fields, four statuses, and caller fields are named."""
    sec = _section(path)
    for name in (*FINDING_FIELDS, *STATUSES, *CALLER_FIELDS):
        assert f"`{name}`" in sec, name
    assert "caller fills" in _flat(sec)


@pytest.mark.parametrize("path", REVIEWERS, ids=lambda p: p.stem)
def test_ac0003_return_rules(path: Path) -> None:
    """AC-0003: typed return, override, no-spec rule, gate, and kept sentence."""
    sec = _flat(_section(path))
    assert "only one fenced `json` block holding `terminal_status` and `findings`" in sec
    assert "instead of the findings block or the clean line" in sec
    assert "overrides the findings-only return" in sec
    assert "Without a request for a typed report, the findings block or the clean line" in sec
    assert "governs only the modes in this file that return a findings block" in sec
    assert "Before any review work, check that the request names a spec" in sec
    assert "names none returns `indeterminate` with no findings" in sec
    assert "status never changes the outcome" in sec
    assert "is not this file's review-complete gate" in sec
    assert "obligation decision governs it" in sec
    assert "Return **only** the findings block above" in _read(path)


@pytest.mark.parametrize("path", REVIEWERS, ids=lambda p: p.stem)
def test_ac0004_material_definition(path: Path) -> None:
    """AC-0004: material finding definition, only-material rule, clean rule."""
    sec = _flat(_section(path))
    assert (
        "A material finding is a Blocker or Concern whose defect something outside "
        "the finding establishes: code, a test, a lint, a schema, a resolvable "
        "reference, or a stated constraint disagrees with the target." in sec
    )
    assert "Every other finding is not material." in sec
    assert "carries only material findings" in sec
    assert "completes with no material finding returns `clean`" in sec
    assert "asks for the findings block instead" in sec


@pytest.mark.parametrize("path", REVIEWERS, ids=lambda p: p.stem)
def test_ac0005_affected_criteria(path: Path) -> None:
    """AC-0005: criteria come from the caller-named spec; none means indeterminate."""
    sec = _flat(_section(path))
    assert "identifiers the caller-named spec contains" in sec
    assert "the spec under review is the caller-named spec" in sec
    assert "has no identifier in the caller-named spec to name, the status is `indeterminate` with no findings" in sec


def test_ac0006_adversarial_checks() -> None:
    """AC-0006: check 6 in spec-stage, check 10 in implementation-stage."""
    c6 = _flat(_check(ADVERSARIAL, "### Spec-stage checks", 6))
    for phrase in (
        "adds or alters a member of a model, registry, graph, index, schema, namespace, or collection",
        "generic operations observe without opt-in",
        "each reachable consumer class",
        "preservation criterion in the spec under review",
        "affected criteria name the criterion that covers the class",
        "the criterion whose change reaches the consumer",
        "the fix is an amendment",
        "explicit filter raises no finding",
    ):
        assert phrase in c6, phrase
    c10 = _flat(_check(ADVERSARIAL, "### Implementation-stage checks", 10))
    assert "Apply check 6" in c10
    assert "consumers the diff reaches" in c10


def test_ac0007_quality_check() -> None:
    """AC-0007: check 35 sits in a Preservation evidence subsection of review mode."""
    text = _read(QUALITY)
    assert text.index("### Performance ergonomics") < text.index("### Preservation evidence")
    assert text.index("### Preservation evidence") < text.index("## Test-author mode")
    c35 = _flat(_check(QUALITY, "### Preservation evidence", 35))
    for phrase in (
        "each preservation criterion in the spec under review",
        "is current",
        "independent of the code under test",
        "fails on a named mutation",
        "Missing, stale, tautological, or feature-only evidence",
        "affected criteria name that criterion",
    ):
        assert phrase in c35, phrase


@pytest.mark.parametrize("path", REVIEWERS, ids=lambda p: p.stem)
def test_ac0008_portability(path: Path) -> None:
    """AC-0008: added text names no internal path or optional-pack term."""
    sec = _section(path)
    added = sec
    if path == ADVERSARIAL:
        added += _check(path, "### Spec-stage checks", 6)
        added += _check(path, "### Implementation-stage checks", 10)
    else:
        added += _check(path, "### Preservation evidence", 35)
    for word in FORBIDDEN_WORDS:
        assert word not in added, word
    assert not re.search(r"\bPi\b", added)
    assert not re.search(r"\b(docs|contracts)/", added)
    assert "preservation" not in sec.lower()
