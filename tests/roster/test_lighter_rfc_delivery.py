"""This repository adopts the lighter-RFC starter and keeps its copies equal.

The seeds under `packs/repo-governance/seeds/` are excluded from self-host, so
nothing syncs the repository's own copies. These tests compare them directly.
"""
from __future__ import annotations

import pathlib

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[2]
SEEDS = ROOT / "packs/repo-governance/seeds/docs"
MAINTAINER = "eugenelim"  # Owner named in docs/specs/lighter-rfc-delivery/spec.md


@pytest.mark.parametrize("name", ["rfc.py", "file_safety.py", "template.md.tmpl"])
def test_rfc_copies_are_byte_identical_to_seeds(name: str) -> None:
    """AC-0054: the repository's RFC tooling copies equal the shipped seeds."""
    assert (ROOT / "docs/rfc" / name).read_bytes() == (SEEDS / "rfc" / name).read_bytes()


def test_governance_names_the_owner_and_has_no_placeholder() -> None:
    """AC-0055: no placeholder remains and the spec Owner is a listed maintainer."""
    text = (ROOT / "docs/GOVERNANCE.md").read_text(encoding="utf-8")
    assert "<maintainer-handle>" not in text
    assert f"- @{MAINTAINER}\n" in text


def test_pack_layout_lists_governance_as_repository_owned() -> None:
    """AC-0057: the architecture page lists the seeded governance path."""
    text = (ROOT / "docs/architecture/pack-layout.md").read_text(encoding="utf-8")
    assert "`docs/GOVERNANCE.md`" in text


GUIDE = ROOT / "guides/repo-governance/how-to/new-rfc.md"
SIX_SECTIONS = ["Summary", "Motivation", "Proposal", "Costs and what could go wrong", "Alternatives", "How we will know it works"]


def test_guide_names_six_sections_and_no_retired_terms() -> None:
    """AC-0072: the how-to names the six required sections and drops the retired ones."""
    text = GUIDE.read_text(encoding="utf-8")
    for term in ("Approver", "Reviewer brief", "The ask"):
        assert term not in text, term
    for name in SIX_SECTIONS:
        assert f"**{name}.**" in text, name
    assert "python3 -I docs/rfc/rfc.py next" in text
    assert "Experiment / validation" not in text


def test_guide_runs_rfc_py_only_in_isolated_mode() -> None:
    """AC-0046: every `rfc.py` command line in the how-to uses `python3 -I`."""
    lines = [
        line
        for line in GUIDE.read_text(encoding="utf-8").splitlines()
        if line.lstrip().startswith(("python", "$ python")) and "rfc.py" in line
    ]
    assert lines
    assert all("python3 -I " in line for line in lines), lines


ADR_0161 = next((ROOT / "docs/adr").glob("0161-*.md"))
SUPERSEDED_SPECS = ("new-rfc-two-humans", "new-rfc-readability", "new-rfc-governance")


def _superseded_rows() -> list[tuple[str, str]]:
    """Return (spec, criterion) pairs from the 'Superseded by the ADR' table."""
    notes = (ROOT / "docs/rfc/0114-notes/superseded-criteria.md").read_text(encoding="utf-8")
    section = notes.split("## Superseded by the ADR", 1)[1].split("\n## ", 1)[0]
    rows = []
    for line in section.splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if line.startswith("|") and len(cells) == 3 and cells[0].startswith("`"):
            rows.append((cells[0].strip("`"), cells[1]))
    return rows


def test_adr_lists_each_superseded_criterion() -> None:
    """AC-0074: the ADR names each criterion the notes list as superseded."""
    adr = ADR_0161.read_text(encoding="utf-8")
    rows = _superseded_rows()
    assert len(rows) == 8
    assert "RFC-0114" in adr
    for spec, criterion in rows:
        assert spec in adr
        token = criterion.split(",")[0].split(" and ")[0].strip()
        if token.startswith("AC"):
            assert token in adr, (spec, token)
    assert "AC-0065" in adr and "governance draft" in adr


@pytest.mark.parametrize("spec", SUPERSEDED_SPECS)
def test_spec_status_points_to_the_adr(spec: str) -> None:
    """AC-0075: each affected spec's Status line carries a scoped pointer to the ADR."""
    lines = (ROOT / f"docs/specs/{spec}/spec.md").read_text(encoding="utf-8").splitlines()
    status = next(line for line in lines if line.startswith("- **Status:**"))
    assert f"../../adr/{ADR_0161.name}" in status
    assert "superseded in part" in status
    wanted = {"new-rfc-governance": "AC-0065"}.get(spec, "AC3" if spec == "new-rfc-readability" else "AC2")
    assert wanted in status


CAPTURED = ROOT / "docs/product/captured"


def test_seed_upgrade_follow_on_is_captured_with_an_owner() -> None:
    """AC-0081: the seed-upgrade item exists, is owned by the maintainer and states the gap."""
    text = (CAPTURED / "fix-seed-upgrades.md").read_text(encoding="utf-8")
    assert text.startswith("# ")
    assert "- **Status:** Open" in text
    assert MAINTAINER in text
    assert "neither refreshes nor adds seeded files" in text
    assert "guides say it does" in text
    for slug in ("re-sync-approver-wording-is-stale", "desk-research-guide-rfc-mapping-is-stale"):
        assert (CAPTURED / f"{slug}.md").is_file(), slug


def test_changelog_fragment_states_new_installs_only_and_recopy_route() -> None:
    """AC-0079: the fragment names new-rfc and states the seeded-files limit and the re-copy route."""
    text = (ROOT / "docs/product/changelog.d/419f6fb4-b4a5-4df5-b4a2-f8bd3e1869ce.md").read_text(
        encoding="utf-8"
    )
    assert "`new-rfc`" in text and "`rfc.py`" in text and "issue template" in text
    assert "Seeded files reach new installs only" in text
    assert "only by re-copying the script" in text


def test_release_notes_name_self_host_and_lint_changes() -> None:
    """AC-0077: the package notes name the self-host and catalogue lint changes."""
    for name in ("README-pypi.md", "CHANGELOG.md"):
        text = (ROOT / "packages/agentbundle" / name).read_text(encoding="utf-8")
        section = text.split("0.60.2", 1)[1].split("0.60.1", 1)[0]
        assert "docs/GOVERNANCE.md" in section and "repository-owned" in section, name
        assert "seed shapes" in section, name
    assert "RFC-0" not in (ROOT / "packages/agentbundle/README-pypi.md").read_text(
        encoding="utf-8"
    ).split("0.60.2", 1)[1].split("0.60.1", 1)[0]


def test_governance_guide_sample_starts_like_the_starter() -> None:
    """AC-0048: the sample preview of the default draft has no Decision model line."""
    guide = (ROOT / "guides/repo-governance/how-to/set-up-governance.md").read_text(encoding="utf-8")
    sample = guide.split("--- content ---\n", 1)[1].split("```", 1)[0]
    assert sample.startswith("# Governance\n\n## Maintainers\n")
    assert "Decision model" not in sample
