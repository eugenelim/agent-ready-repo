"""T10 (credential-broker-contract): documentation surface presence
checks for the governance surface (ADR, the credentialed-skill contract,
backlog, guide, sibling
spec amendments).
"""

from __future__ import annotations

import pathlib

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]


def test_ac40_adr_exists():
    """An ADR records the four-broker decision."""
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
    """The credentialed-skill contract names the four
    brokers and `metadata.auth`."""
    contract = (
        REPO_ROOT / "guides" / "credential-brokers" / "how-to"
        / "add-a-credentialed-skill.md"
    ).read_text(encoding="utf-8")
    # Locate the Credentialed skills section.
    start = contract.find("## The credentialed-skill contract")
    assert start > 0, "the how-to is missing § The credentialed-skill contract"
    # The reader picks a broker before the example uses one (spec/docs-job-pages).
    declare = contract.find("## Declare the credential")
    assert declare == -1 or start < declare, "broker choice must come before the example"
    end = contract.find("\n## ", start + 1)
    section = contract[start:end] if end > 0 else contract[start:]
    assert "metadata.auth" in section
    for broker in ("env", "cli", "creds", "sso-cookie"):
        assert f"`{broker}`" in section, f"section missing broker id {broker!r}"


def test_ac42_roadmap_entry_carries_manual_qa_matrix():
    """The captured item tracks the six manual-QA rows."""
    item = REPO_ROOT / "docs/product/captured/credential-broker-contract-manual-qa.md"
    text = item.read_text(encoding="utf-8")
    assert "- **Status:**" in text, f"{item} is not a captured item"
    # Six rows: creds × {macOS, Windows, Linux} and sso-cookie × {macOS, Windows, Linux}.
    for combo in (
        "`creds` × macOS",
        "`creds` × Windows",
        "`creds` × Linux",
        "`sso-cookie` × macOS",
        "`sso-cookie` × Windows",
        "`sso-cookie` × Linux",
    ):
        assert combo in text, f"captured item missing manual-QA row: {combo}"


def test_ac44_skill_secrets_footer_present():
    """The skill-secrets spec carries the verbatim footer pointing the
    inheritance invariants at the new shim."""
    spec = (REPO_ROOT / "docs" / "specs" / "skill-secrets" / "spec.md").read_text(encoding="utf-8")
    assert "AC34 and AC35 inheritance invariants" in spec
    assert "credentials_shim" in spec
    assert "shared-libs" in spec
    assert "(credential-broker-contract)" in spec


def test_ac45_distribution_adapters_changelog_bullet_present():
    """The distribution-adapters spec carries the
    new dated bullet naming the two new primitive classes."""
    spec = (
        REPO_ROOT / "docs" / "specs" / "distribution-adapters" / "spec.md"
    ).read_text(encoding="utf-8")
    # Locate the Changelog section.
    start = spec.find("## Changelog")
    assert start > 0
    section = spec[start:]
    # The bullet names both new primitive classes and the spec by name.
    assert "credential-broker-contract" in section
    assert "`shared-libs/`" in section
    assert "`adapter-root-bins/`" in section
    assert "RFC-0013" in section
