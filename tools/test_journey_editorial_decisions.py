"""Enforce the approved journey decision mapping against canonical sources."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "docs/specs/journey-page-completion/editorial-decisions.md"
PACKS = ROOT / "packs"
ROW = re.compile(
    r"^\| `(?P<journey>[^`]+)` \| `[^`]+` \| `(?P<identifier>[^`]+)` \| "
    r"(?P<label>[^|]+?) \|$"
)


def _frontmatter(path: Path) -> list[str]:
    lines = path.read_text(encoding="utf-8").splitlines()
    assert lines[0] == "---", f"{path}: missing frontmatter fence"
    return lines[1 : lines.index("---", 1)]


def _scalar(value: str) -> str:
    return value.strip().strip('"').strip("'")


def _ledger_mapping() -> dict[str, list[tuple[str, str]]]:
    mapping: dict[str, list[tuple[str, str]]] = {}
    in_table = False
    for line in LEDGER.read_text(encoding="utf-8").splitlines():
        if line == "## Approved migration mapping":
            in_table = True
            continue
        if in_table and line.startswith("## "):
            break
        if not in_table:
            continue
        match = ROW.match(line)
        if match:
            mapping.setdefault(match["journey"], []).append(
                (match["identifier"], match["label"].strip())
            )
    return mapping


def _pack_mapping(journey: str) -> list[tuple[str, str]]:
    lines = _frontmatter(PACKS / journey / "JOURNEY.md")
    gates: list[tuple[str, str]] = []
    in_gates = False
    current_id: str | None = None
    for line in lines:
        if line == "humanGates:":
            in_gates = True
            continue
        if in_gates and line and not line[0].isspace():
            break
        if not in_gates:
            continue
        id_match = re.match(r"  - id:\s*(.+)$", line)
        if id_match:
            current_id = _scalar(id_match[1])
            continue
        label_match = re.match(r"    label:\s*(.+)$", line)
        if label_match:
            assert current_id is not None, f"{journey}: label without gate ID"
            gates.append((current_id, _scalar(label_match[1])))
            current_id = None
    return gates


def test_editorial_mapping_matches_every_canonical_human_gate() -> None:
    """The approved ledger is the single source for canonical IDs and labels."""
    expected = _ledger_mapping()

    assert sum(len(gates) for gates in expected.values()) == 39
    assert set(expected) == {path.parent.name for path in PACKS.glob("*/JOURNEY.md")}

    actual = {journey: _pack_mapping(journey) for journey in expected}
    assert actual == expected


PRIORITY = ("core", "product-engineering", "release-engineering")
# `atlassian` carried a `goodOutputDescription` before this spec. It is named here
# so the absence check stays exact: grandfathered copy is tolerated, a transcript
# newly added to any other non-priority journey is not.
GRANDFATHERED_TRANSCRIPTS = frozenset({"atlassian"})
EYEBROW_ROW = re.compile(r"^Eyebrow: \*\*(?P<eyebrow>.+)\*\*$")
BLOCK_INDENT = "  "


def _ledger_editorial() -> dict[str, tuple[str, list[str]]]:
    """Parse each priority journey's approved eyebrow and transcript."""
    editorial: dict[str, tuple[str, list[str]]] = {}
    journey: str | None = None
    eyebrow: str | None = None
    transcript: list[str] = []
    in_section = False

    def flush() -> None:
        if journey is None:
            return
        assert eyebrow is not None, f"{journey}: ledger section states no eyebrow"
        assert transcript, f"{journey}: ledger section states no transcript"
        editorial[journey] = (eyebrow, _chomp(list(transcript)))

    for line in LEDGER.read_text(encoding="utf-8").splitlines():
        if line == "## Priority journeys":
            in_section = True
            continue
        if in_section and line.startswith("## "):
            break
        if not in_section:
            continue
        if line.startswith("### "):
            flush()
            journey = line[4:].strip().lower().replace(" ", "-")
            eyebrow, transcript = None, []
            continue
        match = EYEBROW_ROW.match(line)
        if match:
            eyebrow = match["eyebrow"]
            continue
        # Strip exactly the blockquote marker, then only a Markdown HARD BREAK,
        # which is two or more trailing spaces. A single trailing space is not a
        # hard break -- it renders as ordinary spacing the block scalar could have
        # carried -- so it is preserved and will fail the comparison. Leading
        # indentation and interior blank lines are preserved on both sides.
        if line.startswith(">"):
            quoted = line[2:] if line.startswith("> ") else line[1:]
            without_trailing = quoted.rstrip(" ")
            trailing = len(quoted) - len(without_trailing)
            transcript.append(without_trailing if trailing >= 2 else quoted)
    flush()
    return editorial


def _chomp(lines: list[str]) -> list[str]:
    """Drop trailing blank lines, mirroring YAML's `|-` strip chomping."""
    end = len(lines)
    while end and not lines[end - 1]:
        end -= 1
    return lines[:end]


def _pack_editorial(journey: str) -> tuple[str, list[str]]:
    lines = _frontmatter(PACKS / journey / "JOURNEY.md")
    eyebrow: str | None = None
    transcript: list[str] = []
    in_block = False
    for line in lines:
        if in_block:
            if line and not line.startswith(BLOCK_INDENT):
                in_block = False
            else:
                # Only the base indent belongs to YAML; anything deeper is content.
                # No rstrip here. Trailing spaces are YAML content, and the ledger
                # cannot express them, so a stray one in canonical source must fail
                # rather than be normalised away.
                transcript.append(line[len(BLOCK_INDENT):] if line else "")
                continue
        eyebrow_match = re.match(r"eyebrow:\s*(.+)$", line)
        if eyebrow_match:
            eyebrow = _scalar(eyebrow_match[1])
            continue
        if re.match(r"goodOutputDescription:\s*\|-?\s*$", line):
            in_block = True
    assert eyebrow is not None, f"{journey}: canonical frontmatter states no eyebrow"
    assert transcript, f"{journey}: canonical frontmatter states no transcript"
    return eyebrow, _chomp(transcript)


def test_priority_pages_emit_the_approved_eyebrow_and_transcript() -> None:
    """The ledger is the single source for priority eyebrow and transcript copy."""
    expected = _ledger_editorial()

    assert set(expected) == set(PRIORITY)

    actual = {journey: _pack_editorial(journey) for journey in expected}
    assert actual == expected


def test_editorial_copy_is_confined_to_the_priority_journeys() -> None:
    """No other journey gains an eyebrow or transcript through this spec."""
    with_eyebrow: set[str] = set()
    with_transcript: set[str] = set()
    for path in sorted(PACKS.glob("*/JOURNEY.md")):
        lines = _frontmatter(path)
        if any(re.match(r"eyebrow:", line) for line in lines):
            with_eyebrow.add(path.parent.name)
        if any(re.match(r"goodOutputDescription:", line) for line in lines):
            with_transcript.add(path.parent.name)

    # Eyebrows are exact: this spec created all three and no others exist.
    assert with_eyebrow == set(PRIORITY)
    # Transcripts are a subset check, not equality. The ledger's claim is that no
    # journey *gains* one through this spec, so a new transcript anywhere outside
    # the allowed set must fail — but deleting the grandfathered `atlassian` copy
    # is not this spec's business, and equality would wrongly pin it in place.
    # The priority three are proved present by the comparison test above.
    assert with_transcript <= set(PRIORITY) | GRANDFATHERED_TRANSCRIPTS
