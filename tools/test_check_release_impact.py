#!/usr/bin/env python3
"""Tests for Gate G's release-impact classification.

Runs under pytest; pure stdlib, no fixtures on disk. Covers the prefix table
directly (`is_release_impacting`) plus the indicator predicate, because the
gate's whole job is the classification — the git plumbing around it is
exercised by CI itself.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "repo"))

from check_release_impact import (  # noqa: E402
    has_release_indicator,
    is_release_impacting,
)


def test_contracts_tree_is_release_impacting() -> None:
    """The authored contract tree gates a release.

    Regression for a dead prefix: the table listed `docs/contracts/`, deleted
    by ADR-0055, and omitted `contracts/`. A contracts/-only change therefore
    classified as non-impacting unless the file happened to have a packaged
    twin listed separately.
    """
    assert is_release_impacting("contracts/catalogue.schema.json") is True
    assert is_release_impacting("contracts/guide.schema.json") is True
    assert is_release_impacting("contracts/adapter.toml") is True


def test_a_contracts_only_change_without_an_indicator_fails() -> None:
    """The end-to-end predicate pair Gate G composes: impacting + no indicator."""
    changed = ["contracts/catalogue.schema.json"]
    assert [f for f in changed if is_release_impacting(f)] == changed
    assert has_release_indicator(changed) is False


def test_a_contracts_only_change_with_an_indicator_passes() -> None:
    changed = [
        "contracts/catalogue.schema.json",
        "packages/agentbundle/pyproject.toml",
    ]
    assert [f for f in changed if is_release_impacting(f)]
    assert has_release_indicator(changed) is True


def test_changelog_alone_is_a_release_indicator() -> None:
    assert has_release_indicator(["docs/product/changelog.md"]) is True


def test_deleted_docs_contracts_prefix_is_gone() -> None:
    """`docs/` is governance; nothing under it should gate a release now."""
    from check_release_impact import RELEASE_IMPACTING_PREFIXES

    assert not any(p.startswith("docs/") for p in RELEASE_IMPACTING_PREFIXES)


def test_non_impacting_prefixes_still_win() -> None:
    """The explicit governance carve-outs are checked before the impacting
    table, so a path matching both is non-impacting."""
    assert is_release_impacting("docs/specs/foo/spec.md") is False
    assert is_release_impacting("packs/core/pack.toml") is False
    assert is_release_impacting("tools/repo/check_release_impact.py") is False


def test_catalogue_tooling_and_cli_remain_impacting() -> None:
    """Guard the entries this change did not touch."""
    assert is_release_impacting(
        "packages/agentbundle/agentbundle/catalogue_tooling/lint.py"
    ) is True
    assert is_release_impacting("packages/agentbundle/agentbundle/cli.py") is True
