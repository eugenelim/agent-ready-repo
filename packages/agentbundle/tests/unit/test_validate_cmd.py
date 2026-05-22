"""T2: Tests for the `agentbundle validate` subcommand.

Verification mode: TDD (plan.md § T2).

Each test drives a slice of the contract:
  - Happy path — valid pack exits 0.
  - Sad path — malformed pack.toml exits 1 with a one-line stderr.
  - Recipe gate — unknown recipe exits 1 naming the recipe.
  - Strict gate (fixtures absent) — --strict warns and exits 0.
  - Version-mismatch gate — major mismatch exits 1 naming both versions.
"""

from __future__ import annotations

import argparse
import io
import sys
from pathlib import Path
from unittest import mock

import pytest

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

FIXTURES = Path(__file__).resolve().parent.parent / "fixtures" / "validate"


def _args(pack_path: Path, strict: bool = False) -> argparse.Namespace:
    ns = argparse.Namespace()
    ns.pack_path = str(pack_path)
    ns.strict = strict
    return ns


def _run(pack_path: Path, strict: bool = False):
    """Import and invoke validate.run; returns (exit_code, stderr_text)."""
    from agentbundle.commands import validate as validate_mod

    captured = io.StringIO()
    with mock.patch("sys.stderr", captured):
        rc = validate_mod.run(_args(pack_path, strict=strict))
    return rc, captured.getvalue()


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------


def test_valid_pack_exits_0():
    rc, stderr = _run(FIXTURES / "valid_pack")
    assert rc == 0, f"Expected exit 0, got {rc}. stderr: {stderr!r}"
    assert stderr == "", f"Unexpected stderr: {stderr!r}"


# ---------------------------------------------------------------------------
# Sad path — malformed pack.toml
# ---------------------------------------------------------------------------


def test_malformed_pack_toml_exits_1(capsys):
    """A pack with invalid TOML exits 1 and emits a one-line stderr reason."""
    from agentbundle.commands import validate as validate_mod

    rc = validate_mod.run(_args(FIXTURES / "malformed_pack"))
    captured = capsys.readouterr()
    assert rc == 1
    lines = [ln for ln in captured.err.splitlines() if ln.strip()]
    assert len(lines) == 1, f"Expected exactly one stderr line, got: {captured.err!r}"
    assert "TOML" in lines[0] or "not valid" in lines[0], lines[0]


# ---------------------------------------------------------------------------
# Missing pack.toml
# ---------------------------------------------------------------------------


def test_missing_pack_toml_exits_1(tmp_path, capsys):
    from agentbundle.commands import validate as validate_mod

    rc = validate_mod.run(_args(tmp_path))
    captured = capsys.readouterr()
    assert rc == 1
    assert "pack.toml not found" in captured.err


# ---------------------------------------------------------------------------
# Schema sad path — structurally invalid pack (missing required fields)
# ---------------------------------------------------------------------------


def test_schema_invalid_pack_exits_1(tmp_path, capsys):
    """A pack.toml that is valid TOML but fails the schema exits 1."""
    from agentbundle.commands import validate as validate_mod

    (tmp_path / "pack.toml").write_text(
        '[not_the_right_key]\nfoo = "bar"\n', encoding="utf-8"
    )
    rc = validate_mod.run(_args(tmp_path))
    captured = capsys.readouterr()
    assert rc == 1
    lines = [ln for ln in captured.err.splitlines() if ln.strip()]
    assert len(lines) == 1, f"Expected one-line stderr, got: {captured.err!r}"
    assert "schema error" in lines[0].lower() or "missing required" in lines[0].lower()


# ---------------------------------------------------------------------------
# Recipe gate
# ---------------------------------------------------------------------------


def test_unknown_recipe_exits_1_naming_recipe(capsys):
    """A pack declaring an unknown recipe exits 1 and names the recipe."""
    from agentbundle.commands import validate as validate_mod

    rc = validate_mod.run(_args(FIXTURES / "bad_recipe_pack"))
    captured = capsys.readouterr()
    assert rc == 1
    assert "bogus-recipe" in captured.err, f"Offending recipe not named: {captured.err!r}"


def test_known_recipe_passes(tmp_path):
    """A pack declaring a known recipe exits 0."""
    (tmp_path / "pack.toml").write_text(
        '[pack]\nname = "r"\nversion = "0.1"\nrecipes = ["per-pack-claude-plugin"]\n',
        encoding="utf-8",
    )
    rc, stderr = _run(tmp_path)
    assert rc == 0, f"Expected 0, got {rc}. stderr: {stderr!r}"


# ---------------------------------------------------------------------------
# Strict gate — fixtures absent → warn + exit 0
# ---------------------------------------------------------------------------


def test_strict_without_fixtures_warns_and_exits_0(tmp_path, capsys):
    """--strict warns on stderr and exits 0 when conformance fixtures are absent."""
    from agentbundle.commands import validate as validate_mod

    (tmp_path / "pack.toml").write_text(
        '[pack]\nname = "s"\nversion = "0.1"\n', encoding="utf-8"
    )

    # Patch _conformance_fixtures_dir to return a non-existent path.
    absent = tmp_path / "conformance_does_not_exist"
    with mock.patch.object(validate_mod, "_conformance_fixtures_dir", return_value=absent):
        rc = validate_mod.run(_args(tmp_path, strict=True))

    captured = capsys.readouterr()
    assert rc == 0, f"Expected 0, got {rc}. stderr: {captured.err!r}"
    assert "conformance fixtures not present" in captured.err, captured.err


# ---------------------------------------------------------------------------
# Version-mismatch gate
# ---------------------------------------------------------------------------


def test_version_mismatch_exits_1_naming_both_versions(capsys):
    """A pack declaring adapter-contract v99.0 is refused with both versions in stderr."""
    from agentbundle.commands import validate as validate_mod

    rc = validate_mod.run(_args(FIXTURES / "version_mismatch_pack"))
    captured = capsys.readouterr()
    assert rc == 1
    # Both the pack's version and the CLI's SPEC_VERSION must appear in stderr.
    assert "99.0" in captured.err, f"Pack version not in stderr: {captured.err!r}"
    from agentbundle.version import SPEC_VERSION
    assert SPEC_VERSION in captured.err, f"CLI spec version not in stderr: {captured.err!r}"


def test_version_mismatch_uses_common_helper():
    """`check_spec_version_gate` returns 1 on major mismatch."""
    from agentbundle.commands._common import check_spec_version_gate
    import io

    pack_data = {"pack": {"name": "x", "version": "0.1", "adapter-contract": {"version": "99.0"}}}
    captured = io.StringIO()
    with mock.patch("sys.stderr", captured):
        result = check_spec_version_gate(pack_data)
    assert result == 1
    assert "99" in captured.getvalue()


def test_version_match_passes_common_helper():
    """`check_spec_version_gate` returns None when major versions match."""
    from agentbundle.commands._common import check_spec_version_gate

    pack_data = {"pack": {"name": "x", "version": "0.1", "adapter-contract": {"version": "0.9"}}}
    assert check_spec_version_gate(pack_data) is None


def test_no_adapter_contract_version_passes():
    """A pack without [pack.adapter-contract] version is accepted (gate is opt-in)."""
    from agentbundle.commands._common import check_spec_version_gate

    pack_data = {"pack": {"name": "x", "version": "0.1"}}
    assert check_spec_version_gate(pack_data) is None
