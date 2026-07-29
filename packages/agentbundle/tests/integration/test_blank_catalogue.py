"""Blank catalogue validity: 0 packs + 0 profiles must pass lint, verify,
list-packs, and list-profiles without error.

AC (spec § Bucket 6 — Blank catalogue validity):
- lint_catalogue returns ok=True, no ERROR diagnostics.
- verify_catalogue returns ok=True, no ERROR diagnostics.
- discover_packs returns an empty list.
- list_profiles returns an empty list.
"""

from __future__ import annotations

from pathlib import Path

BLANK_FIXTURE = (
    Path(__file__).parent.parent / "fixtures" / "blank_catalogue"
)


def test_blank_lint_passes():
    from agentbundle.catalogue_tooling.lint import lint_catalogue

    result = lint_catalogue(BLANK_FIXTURE)
    errors = [d for d in result.diagnostics if d.severity.name == "ERROR"]
    assert result.ok, f"lint failed on blank catalogue: {errors}"
    assert not errors, f"unexpected errors: {errors}"


def test_blank_verify_passes():
    from agentbundle.catalogue_tooling.verify import verify_catalogue

    result = verify_catalogue(BLANK_FIXTURE)
    errors = [d for d in result.diagnostics if d.severity.name == "ERROR"]
    assert result.ok, f"verify failed on blank catalogue: {errors}"
    assert not errors, f"unexpected errors: {errors}"


def test_blank_discover_packs_empty():
    from agentbundle.build.main import discover_packs

    packs = discover_packs(BLANK_FIXTURE / "packs")
    assert packs == [], f"expected no packs, got {packs}"


def test_blank_list_profiles_empty():
    from agentbundle.commands.profile import list_profiles

    profiles = list_profiles(BLANK_FIXTURE)
    assert profiles == [], f"expected no profiles, got {profiles}"


def test_blank_deep_lint_passes():
    from agentbundle.catalogue_tooling.lint import lint_catalogue

    result = lint_catalogue(BLANK_FIXTURE, deep=True)
    errors = [d for d in result.diagnostics if d.severity.name == "ERROR"]
    assert result.ok, f"deep lint failed on blank catalogue: {errors}"
    assert not errors, f"unexpected errors in deep lint: {errors}"
