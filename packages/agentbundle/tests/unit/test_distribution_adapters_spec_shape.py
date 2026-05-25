"""T8: spec-shape tests for docs/specs/distribution-adapters/spec.md.

Two construction tests verify that the distribution-adapters spec carries
the AC17-mandated install-routes contract AC and Changelog line added by
docs/specs/claude-plugins-install-route/spec.md.

AC17 (claude-plugins-install-route spec): ``distribution-adapters/spec.md``
Acceptance Criteria and Changelog gain references to the v0.4 contract bump.
"""

from __future__ import annotations

from pathlib import Path

# Repo-relative anchor: this file lives at
# packages/agentbundle/tests/unit/test_distribution_adapters_spec_shape.py
_REPO_ROOT = Path(__file__).resolve().parents[4]
_SPEC = (
    _REPO_ROOT
    / "docs"
    / "specs"
    / "distribution-adapters"
    / "spec.md"
)


def _body() -> str:
    assert _SPEC.exists(), f"distribution-adapters spec not found at {_SPEC}"
    return _SPEC.read_text(encoding="utf-8")


def test_distribution_adapters_changelog_names_this_spec() -> None:
    """AC17: Changelog contains the spec name and amendment date."""
    body = _body()
    assert "claude-plugins-install-route" in body, (
        "docs/specs/distribution-adapters/spec.md Changelog must contain "
        "the literal string 'claude-plugins-install-route' (the spec that "
        "added the install-routes contract AC)."
    )
    assert "2026-05-24" in body, (
        "docs/specs/distribution-adapters/spec.md Changelog must contain "
        "the date '2026-05-24' on the install-routes amendment line."
    )


def test_distribution_adapters_has_install_routes_ac() -> None:
    """AC17: spec body contains at least one reference to 'install-routes'."""
    body = _body()
    count = body.count("install-routes")
    assert count >= 1, (
        "docs/specs/distribution-adapters/spec.md must contain at least one "
        "occurrence of 'install-routes' (the new AC20 body). "
        f"Found {count} occurrence(s)."
    )
