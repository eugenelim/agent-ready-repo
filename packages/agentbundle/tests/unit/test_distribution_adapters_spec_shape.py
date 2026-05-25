"""T8: spec-shape tests for docs/specs/distribution-adapters/spec.md.

Two construction tests verify that the distribution-adapters spec carries
the AC17-mandated install-routes contract AC and Changelog line added by
docs/specs/claude-plugins-install-route/spec.md.

AC17 (claude-plugins-install-route spec): ``distribution-adapters/spec.md``
Acceptance Criteria and Changelog gain references to the v0.4 contract bump.

Concern-10: tests use anchored regex patterns rather than loose substring
checks so a stray occurrence of the expected string in the wrong section
would not satisfy the assertion.
"""

from __future__ import annotations

import re
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
    """AC17: Changelog contains a dated line naming claude-plugins-install-route.

    Anchored regex: asserts a line of the form
    ``- 2026-05-24: ...claude-plugins-install-route...``
    so the string must appear as part of a changelog bullet with the correct date,
    not merely anywhere in the document (Concern-10 anchored grep).
    """
    body = _body()
    pattern = r"^- 2026-05-24:.*claude-plugins-install-route"
    assert re.search(pattern, body, re.MULTILINE), (
        "docs/specs/distribution-adapters/spec.md Changelog must contain a "
        "bullet dated 2026-05-24 that includes 'claude-plugins-install-route'. "
        f"Pattern: {pattern!r}"
    )


def test_distribution_adapters_has_install_routes_ac() -> None:
    """AC17: spec body contains an AC entry referencing install-routes.

    Anchored regex: asserts a line of the form
    ``- [ ] **(RFC-0008)** ...install-routes...``
    so the string must appear as a checkbox AC entry in the Acceptance Criteria
    section with the RFC-NNNN tag style the file uses elsewhere (the
    distribution-adapters spec tags its ACs by RFC, not by sequential AC
    number — same convention as the surrounding RFC-0004 and RFC-0005 v0.4
    entries).
    """
    body = _body()
    # Match across newlines — the AC's opening line `- [ ] **(RFC-0008)**`
    # often wraps before `install-routes` appears. `re.DOTALL` so `.`
    # spans line boundaries; cap at ~400 chars so a stray match in the
    # Changelog doesn't satisfy the assertion.
    pattern = r"^- \[ \] \*\*\(RFC-0008\)\*\*.{0,400}?install-routes"
    assert re.search(pattern, body, re.MULTILINE | re.DOTALL), (
        "docs/specs/distribution-adapters/spec.md must contain an AC entry "
        "matching '- [ ] **(RFC-0008)** ...install-routes...' "
        "(the AC17-mandated install-routes conformance AC). "
        f"Pattern: {pattern!r}"
    )
