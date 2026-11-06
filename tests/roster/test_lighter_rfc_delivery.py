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
    assert f"- {MAINTAINER}\n" in text


def test_pack_layout_lists_governance_as_repository_owned() -> None:
    """AC-0057: the architecture page lists the seeded governance path."""
    text = (ROOT / "docs/architecture/pack-layout.md").read_text(encoding="utf-8")
    assert "`docs/GOVERNANCE.md`" in text
