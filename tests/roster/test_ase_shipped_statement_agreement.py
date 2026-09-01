"""Shipped statements about the agent-skill-engineering corpus agree with it.

Repository-level rather than pack-level on purpose: the criterion binds the
pack's marketing page under `web/`, and the pack-test boundary lint refuses a
pack test that reaches outside its own pack.

The surfaces are reached by walking named roots rather than by consulting a
hand-maintained file list, so a new file under a bound root is covered the day
it lands instead of the day someone remembers to add it.
"""

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
PACK = ROOT / "packs" / "agent-skill-engineering"
MARKETING = ROOT / "web" / "src" / "content" / "packs" / "agent-skill-engineering.md"
COMPILED_CONCEPTS = (
    PACK / ".apm" / "skills" / "ase-okf-reference" / "references" / "okf" / "concepts"
)

COUNT_WORDS = {
    7: "Seven", 12: "Twelve", 13: "Thirteen", 14: "Fourteen",
    15: "Fifteen", 16: "Sixteen", 17: "Seventeen", 18: "Eighteen",
}
COUNT_STATEMENT = re.compile(r"(\w+) governed (?:foundation )?topics")

# Statements this slice makes false. Closed and slice-scoped: each names a
# capability the corpus now carries, so none can be revived by a later slice
# without that slice removing the capability. The register's surviving
# "reserved for the later slice" entries describe the SEVEN profiles this slice
# does not ship and must not match, which is why no pattern mentions them.
FORBIDDEN_ABSENCE_CLAIMS = (
    "Three governed foundation topics",
    "Twelve governed topics",
    "runtime profiles, plugins, hooks, subagents, installation",
    "composition floors described above are not implemented",
)


def _bound_files() -> list[Path]:
    """Every file under the roots the criterion names."""
    files: list[Path] = []
    for root in (PACK / ".apm", PACK / "okf"):
        files.extend(path for path in root.rglob("*") if path.is_file())
    files.append(PACK / "README.md")
    files.append(MARKETING)
    return files


def _admitted() -> set[str]:
    return {path.stem for path in COMPILED_CONCEPTS.glob("*.md")} - {"index"}


def test_the_bound_roots_reach_the_surfaces_the_criterion_names() -> None:
    """Anti-vacuity: an empty or mis-rooted walk would pass every scan below."""
    files = _bound_files()
    assert MARKETING in files and MARKETING.is_file()
    assert (PACK / "README.md") in files
    assert any(p.suffix == ".md" and ".apm" in p.parts for p in files)
    assert any(p.suffix == ".md" and "okf" in p.parts for p in files)
    assert len(files) > 40, len(files)


def test_every_shipped_topic_count_matches_the_admitted_set() -> None:
    admitted = _admitted()
    expected = COUNT_WORDS.get(len(admitted))
    assert expected is not None, (
        f"admitted topic count {len(admitted)} has no word form; "
        f"extend COUNT_WORDS when the corpus grows past {max(COUNT_WORDS)}"
    )
    seen = 0
    for path in _bound_files():
        if path.suffix not in {".md", ".json", ".toml"}:
            continue
        text = " ".join(path.read_text(encoding="utf-8", errors="replace").split())
        for stated in COUNT_STATEMENT.findall(text):
            seen += 1
            assert stated == expected, (
                f"{path.relative_to(ROOT)} states {stated!r} governed topics; "
                f"the admitted set has {len(admitted)} ({expected})"
            )
    assert seen, "no shipped surface states a governed-topic count"


def test_no_shipped_surface_claims_an_absence_this_slice_filled() -> None:
    for path in _bound_files():
        if path.suffix not in {".md", ".json", ".toml"}:
            continue
        text = " ".join(path.read_text(encoding="utf-8", errors="replace").split())
        for claim in FORBIDDEN_ABSENCE_CLAIMS:
            assert claim not in text, (path.relative_to(ROOT), claim)


@pytest.mark.parametrize("claim", FORBIDDEN_ABSENCE_CLAIMS)
def test_each_forbidden_claim_would_be_caught(claim) -> None:
    """Per-member control: a scan asserting only that *some* claim matches is
    satisfied by one member and says nothing about the rest."""
    planted = f"prefix {claim} suffix"
    matched = [c for c in FORBIDDEN_ABSENCE_CLAIMS if c in planted]
    assert claim in matched


def test_the_forbidden_claim_set_is_pinned() -> None:
    """Erosion control: dropping a member would silently narrow the scan."""
    assert len(FORBIDDEN_ABSENCE_CLAIMS) == 4
    assert len(set(FORBIDDEN_ABSENCE_CLAIMS)) == 4


def test_the_absence_register_entries_for_later_slices_are_not_matched() -> None:
    """The register still records seven runtime profiles as reserved. Those are
    true absences and must survive the scan above."""
    register = (
        PACK / "okf" / "agent-skill-engineering-foundation" / "concepts"
        / "declared-absent" / "unpopulated-leaves.md"
    ).read_text(encoding="utf-8")
    assert "Reserved for the later slice that covers runtime composition" in register
    for claim in FORBIDDEN_ABSENCE_CLAIMS:
        assert claim not in " ".join(register.split())
