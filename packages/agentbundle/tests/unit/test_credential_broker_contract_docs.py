"""T10 (credential-broker-contract): documentation surface presence
checks for AC40-AC45 (ADR, CONVENTIONS, backlog, guide, sibling
spec amendments).
"""

from __future__ import annotations

import pathlib


REPO_ROOT = pathlib.Path(__file__).resolve().parents[4]


def test_ac40_adr_exists():
    """AC40: docs/adr/ gains a new ADR recording the four-broker decision."""
    adr = REPO_ROOT / "docs" / "adr" / "0003-credential-broker-contract.md"
    assert adr.is_file(), f"missing ADR: {adr}"
    body = adr.read_text(encoding="utf-8")
    # Rejection of alternatives B / D / E / F / G / H / I / J recorded.
    for alt in ("(B)", "(D)", "(E)", "(F)", "(G)", "(H)", "(I)", "(J)"):
        assert alt in body, f"ADR missing rejection of alternative {alt}"
    # Binding choices named.
    for choice in (
        "four broker",
        "two transports",
        "credential-setup",
        "shared-libs",
        "adapter-root-bins",
    ):
        assert choice in body, f"ADR missing binding choice keyword {choice!r}"


def test_ac41_conventions_credentialed_section_names_brokers():
    """AC41: docs/CONVENTIONS.md § Credentialed skills names the four
    brokers and `metadata.auth`."""
    conventions = (REPO_ROOT / "docs" / "CONVENTIONS.md").read_text(encoding="utf-8")
    # Locate the Credentialed skills section.
    start = conventions.find("## Credentialed skills")
    assert start > 0, "CONVENTIONS.md missing § Credentialed skills"
    end = conventions.find("\n## ", start + 1)
    section = conventions[start:end] if end > 0 else conventions[start:]
    assert "metadata.auth" in section
    for broker in ("env", "cli", "creds", "sso-cookie"):
        assert f"`{broker}`" in section, f"section missing broker id {broker!r}"


def test_ac42_roadmap_entry_carries_manual_qa_matrix():
    """AC42: backlog entry tracks the six manual-QA rows."""
    roadmap = (REPO_ROOT / "docs" / "backlog.md").read_text(encoding="utf-8")
    start = roadmap.find("## `credential-broker-contract`")
    assert start > 0, "backlog missing credential-broker-contract entry"
    end = roadmap.find("\n## ", start + 1)
    section = roadmap[start:end] if end > 0 else roadmap[start:]
    # Six rows: creds × {macOS, Windows, Linux} and sso-cookie × {macOS, Windows, Linux}.
    for combo in (
        "`creds` × macOS",
        "`creds` × Windows",
        "`creds` × Linux",
        "`sso-cookie` × macOS",
        "`sso-cookie` × Windows",
        "`sso-cookie` × Linux",
    ):
        assert combo in section, f"backlog missing manual-QA row: {combo}"


def test_ac43_guide_walks_broker_first():
    """AC43: the how-to guide replaces 'pick a primitive class' with
    'pick a broker' as the first step."""
    guide = (REPO_ROOT / "docs" / "guides" / "credential-brokers" / "how-to" / "add-a-credentialed-skill.md").read_text(encoding="utf-8")
    pick_broker_idx = guide.find("## Step 1 — Pick a broker")
    assert pick_broker_idx > 0, "guide does not start with 'Pick a broker'"
    # Primitive-class step still exists but comes later (as orthogonal).
    pick_class_idx = guide.find("Pick a primitive class")
    assert pick_class_idx > pick_broker_idx, "primitive-class step must follow broker step"
    # All four brokers named.
    for broker in ("`env`", "`cli`", "`creds`", "`sso-cookie`"):
        assert broker in guide


def test_ac44_skill_secrets_footer_present():
    """AC44: docs/specs/skill-secrets/spec.md carries the verbatim footer
    pointing AC34/AC35 invariants to the new shim."""
    spec = (REPO_ROOT / "docs" / "specs" / "skill-secrets" / "spec.md").read_text(encoding="utf-8")
    assert "AC34 and AC35 inheritance invariants" in spec
    assert "credentials_shim" in spec
    assert "shared-libs" in spec
    assert "(credential-broker-contract)" in spec


def test_ac45_distribution_adapters_changelog_bullet_present():
    """AC45: docs/specs/distribution-adapters/spec.md carries the
    new dated bullet naming the two new primitive classes."""
    spec = (REPO_ROOT / "docs" / "specs" / "distribution-adapters" / "spec.md").read_text(encoding="utf-8")
    # Locate the Changelog section.
    start = spec.find("## Changelog")
    assert start > 0
    section = spec[start:]
    # The bullet names both new primitive classes and the spec by name.
    assert "credential-broker-contract" in section
    assert "`shared-libs/`" in section
    assert "`adapter-root-bins/`" in section
    assert "RFC-0013" in section
