"""T1: AdaptDiscovery typed schema tests.

TDD construction tests for:
  - Finding and AdaptDiscovery dataclasses
  - load_adapt_discovery_typed (scope-aware typed loader)
  - finding_id_for (deterministic SHA-1 prefix)
  - adapt_discovery_to_toml (round-trip serialiser)

Per docs/specs/adapt-to-project/plan.md T1 and spec.md AC2/AC8/AC9/AC16.
"""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from pathlib import Path

import pytest

from agentbundle.config import (
    AdaptDiscovery,
    ConfigError,
    Finding,
    adapt_discovery_to_toml,
    finding_id_for,
    load_adapt_discovery_typed,
)


# ---------------------------------------------------------------------------
# Fixtures (inline TOML strings)
# ---------------------------------------------------------------------------

_REPO_SCOPE_TOML = """\
discovery-schema-version = "0.1"

[markers]
project-name = "agent-ready-repo"
owner        = "eugenelim"

[[findings.accepted]]
finding-id       = "core/restructure:7a3f2c91"
kind             = "restructure"
source-path      = "DESIGN.md"
destination-path = "docs/CHARTER.md"
action           = "move-and-merge"
accepted-at      = 2026-05-22T10:00:00Z

[[findings.declined]]
finding-id       = "user-guide-diataxis/restructure:b819e2d4"
kind             = "restructure"
source-path      = "docs/howto/"
destination-path = "docs/guides/how-to/"
declined-at      = 2026-05-22T10:01:00Z
"""

_USER_SCOPE_TOML = """\
discovery-schema-version = "0.1"

[[findings.accepted]]
finding-id       = "core/companion-merge:c4d12f8a"
kind             = "companion-merge"
source-path      = "~/.claude/agents/old-bot.md"
destination-path = "~/.claude/agents/bot.md"
action           = "merge-companion"
accepted-at      = 2026-05-23T15:00:00Z
"""

_USER_SCOPE_WITH_MARKERS_TOML = """\
discovery-schema-version = "0.1"

[markers]
project-name = "should-be-refused"

[[findings.accepted]]
finding-id       = "core/restructure:7a3f2c91"
kind             = "restructure"
source-path      = "DESIGN.md"
destination-path = "docs/CHARTER.md"
accepted-at      = 2026-05-22T10:00:00Z
"""

_LEGACY_ACCEPTED_TOML = """\
[accepted]
project-name = "myproj"
"""

_LEGACY_ADAPT_TOML = """\
[adapt]
project-name = "myproj"
"""

_UNKNOWN_VERSION_TOML = """\
discovery-schema-version = "9.9"

[markers]
foo = "bar"
"""

_INVALID_KIND_TOML = """\
discovery-schema-version = "0.1"

[[findings.accepted]]
finding-id       = "core/bogus:aabbccdd"
kind             = "bogus"
source-path      = "x.md"
destination-path = "y.md"
accepted-at      = 2026-05-22T10:00:00Z
"""


def _write_toml(tmp_path: Path, content: str) -> Path:
    p = tmp_path / ".adapt-discovery.toml"
    p.write_text(content, encoding="utf-8")
    return p


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_canonical_schema_parses_repo_scope(tmp_path):
    """Repo-scope fixture with markers + two findings parses cleanly."""
    p = _write_toml(tmp_path, _REPO_SCOPE_TOML)
    d = load_adapt_discovery_typed(p, scope="repo")

    assert isinstance(d, AdaptDiscovery)
    assert d.schema_version == "0.1"
    assert d.markers == {"project-name": "agent-ready-repo", "owner": "eugenelim"}

    assert len(d.findings_accepted) == 1
    acc = d.findings_accepted[0]
    assert isinstance(acc, Finding)
    assert acc.finding_id == "core/restructure:7a3f2c91"
    assert acc.kind == "restructure"
    assert acc.source_path == "DESIGN.md"
    assert acc.destination_path == "docs/CHARTER.md"
    assert acc.action == "move-and-merge"
    assert acc.accepted is True

    assert len(d.findings_declined) == 1
    dec = d.findings_declined[0]
    assert dec.kind == "restructure"
    assert dec.accepted is False
    assert dec.action is None


def test_canonical_schema_parses_user_scope(tmp_path):
    """User-scope fixture without markers parses; markers == {}."""
    p = _write_toml(tmp_path, _USER_SCOPE_TOML)
    d = load_adapt_discovery_typed(p, scope="user")

    assert d.markers == {}
    assert len(d.findings_accepted) == 1
    assert d.findings_accepted[0].kind == "companion-merge"
    assert d.findings_declined == []


def test_user_scope_with_markers_refused(tmp_path):
    """User-scope file with [markers] raises ConfigError naming RFC-0004."""
    p = _write_toml(tmp_path, _USER_SCOPE_WITH_MARKERS_TOML)
    with pytest.raises(ConfigError, match="markers are repo-only per RFC-0004"):
        load_adapt_discovery_typed(p, scope="user")


def test_legacy_accepted_refused(tmp_path):
    """File with top-level [accepted] table raises ConfigError."""
    p = _write_toml(tmp_path, _LEGACY_ACCEPTED_TOML)
    with pytest.raises(ConfigError, match="legacy \\[accepted\\] table"):
        load_adapt_discovery_typed(p, scope="repo")


def test_legacy_adapt_refused(tmp_path):
    """File with top-level [adapt] table raises ConfigError."""
    p = _write_toml(tmp_path, _LEGACY_ADAPT_TOML)
    with pytest.raises(ConfigError, match="legacy \\[adapt\\] table"):
        load_adapt_discovery_typed(p, scope="repo")


def test_unknown_schema_version_refused(tmp_path):
    """Unknown discovery-schema-version raises ConfigError naming 0.1."""
    p = _write_toml(tmp_path, _UNKNOWN_VERSION_TOML)
    with pytest.raises(ConfigError, match="0\\.1"):
        load_adapt_discovery_typed(p, scope="repo")


def test_invalid_finding_kind_refused(tmp_path):
    """A finding with kind='bogus' raises ConfigError."""
    p = _write_toml(tmp_path, _INVALID_KIND_TOML)
    with pytest.raises(ConfigError):
        load_adapt_discovery_typed(p, scope="repo")


def test_finding_id_deterministic():
    """finding_id_for returns a stable string of shape <pack>/<kind>:<8hex>."""
    fid = finding_id_for("core", "restructure", ["DESIGN.md"], ["docs/CHARTER.md"])
    assert fid.startswith("core/restructure:")
    suffix = fid.split(":")[1]
    assert len(suffix) == 8
    assert all(c in "0123456789abcdef" for c in suffix)
    # Calling twice returns the same value.
    assert fid == finding_id_for("core", "restructure", ["DESIGN.md"], ["docs/CHARTER.md"])
    # Different inputs produce different ids.
    other = finding_id_for("core", "restructure", ["DIFFERENT.md"], ["docs/CHARTER.md"])
    assert fid != other


def test_finding_id_input_includes_pack_and_kind():
    """Pack and kind both contribute to the hashed input."""
    a = finding_id_for("a", "restructure", ["x"], ["y"])
    b = finding_id_for("b", "restructure", ["x"], ["y"])
    assert a != b, "pack 'a' vs 'b' should produce different ids"

    c = finding_id_for("a", "restructure", ["x"], ["y"])
    d = finding_id_for("a", "companion-merge", ["x"], ["y"])
    assert c != d, "kind 'restructure' vs 'companion-merge' should produce different ids"


def test_findings_round_trip_preserves_fields(tmp_path):
    """Build an AdaptDiscovery, serialise to TOML, reparse, assert field equality."""
    ts = datetime(2026, 5, 22, 10, 0, 0, tzinfo=timezone.utc)
    f_acc = Finding(
        finding_id="core/restructure:7a3f2c91",
        kind="restructure",
        source_path="DESIGN.md",
        destination_path="docs/CHARTER.md",
        action="move-and-merge",
        recorded_at=ts,
        accepted=True,
    )
    f_dec = Finding(
        finding_id="user-guide-diataxis/consolidate:b819e2d4",
        kind="consolidate",
        source_path="docs/howto/",
        destination_path="docs/guides/how-to/",
        action=None,
        recorded_at=ts,
        accepted=False,
    )
    original = AdaptDiscovery(
        schema_version="0.1",
        markers={"project-name": "myrepo", "owner": "alice"},
        findings_accepted=[f_acc],
        findings_declined=[f_dec],
    )

    toml_text = adapt_discovery_to_toml(original)
    p = tmp_path / ".adapt-discovery.toml"
    p.write_text(toml_text, encoding="utf-8")

    reparsed = load_adapt_discovery_typed(p, scope="repo")
    assert reparsed.schema_version == original.schema_version
    assert reparsed.markers == original.markers
    assert len(reparsed.findings_accepted) == 1
    assert len(reparsed.findings_declined) == 1

    ra = reparsed.findings_accepted[0]
    assert ra.finding_id == f_acc.finding_id
    assert ra.kind == f_acc.kind
    assert ra.source_path == f_acc.source_path
    assert ra.destination_path == f_acc.destination_path
    assert ra.action == f_acc.action
    assert ra.accepted is True

    rd = reparsed.findings_declined[0]
    assert rd.finding_id == f_dec.finding_id
    assert rd.kind == f_dec.kind
    assert rd.action is None
    assert rd.accepted is False


def test_marker_key_must_follow_lowercase_hyphen_grammar(tmp_path):
    """Spec § Canonical schemas: a repo-scope file with a marker key
    violating the lowercase-hyphen grammar is refused (adversarial-
    review concern 5)."""
    bad = tmp_path / "bad.toml"
    bad.write_text(
        'discovery-schema-version = "0.1"\n'
        '[markers]\nProjectName = "x"\n',  # UPPER prefix violates ^[a-z]...
        encoding="utf-8",
    )
    with pytest.raises(ConfigError, match="lowercase-hyphen grammar"):
        load_adapt_discovery_typed(bad, scope="repo")

    # Also rejects underscore-bearing keys (`_` not in [a-z0-9-]).
    bad2 = tmp_path / "bad2.toml"
    bad2.write_text(
        'discovery-schema-version = "0.1"\n'
        '[markers]\nproject_name = "x"\n',
        encoding="utf-8",
    )
    with pytest.raises(ConfigError, match="lowercase-hyphen grammar"):
        load_adapt_discovery_typed(bad2, scope="repo")
