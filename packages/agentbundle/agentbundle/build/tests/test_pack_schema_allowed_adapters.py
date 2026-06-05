"""T3 tests for `[pack.install] allowed-adapters` validation
(RFC-0011 / pack-allowed-adapters AC3, AC7, AC22).

Two surfaces under test:

  - the JSONSchema admits the optional `allowed-adapters` field (shape
    check; the schema does NOT hardcode the adapter enum);
  - the Python cross-field check `_validate_allowed_adapters` enforces
    contract-shipped + user-scope-capable membership.

Plus the `_kiro_target_adapters` literal-gate fix: v0.6 packs no longer
silently skip the rail.
"""

from __future__ import annotations

import json
import tomllib
import unittest
from pathlib import Path

from agentbundle.commands.validate import (
    _kiro_target_adapters,
    _validate_allowed_adapters,
)

REPO_ROOT = Path(__file__).resolve().parents[5]
SCHEMA_PATH = (
    REPO_ROOT
    / "packages"
    / "agentbundle"
    / "agentbundle"
    / "_data"
    / "pack.schema.json"
)


def _load_schema() -> dict:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def _v06_pack(install: dict | None = None, pack_extras: dict | None = None) -> dict:
    """Build a minimal valid v0.6 pack dict for schema validation."""
    pack = {
        "name": "demo",
        "version": "0.1.0",
        "adapter-contract": {"version": "0.6"},
    }
    if install is not None:
        pack["install"] = install
    if pack_extras:
        pack.update(pack_extras)
    return {"pack": pack}


# ---------------------------------------------------------------------------
# Schema-shape tests (JSONSchema admits the field)
# ---------------------------------------------------------------------------


class TestSchemaShapeAllowedAdapters(unittest.TestCase):
    def test_allowed_adapters_is_optional(self) -> None:
        from agentbundle.build.validate import validate

        # v0.6 pack omitting allowed-adapters: schema accepts.
        pack = _v06_pack(install={"default-scope": "repo"})
        errors = validate(pack, _load_schema())
        self.assertEqual(errors, [])

    def test_allowed_adapters_array_of_strings(self) -> None:
        from agentbundle.build.validate import validate

        pack = _v06_pack(
            install={
                "default-scope": "user",
                "allowed-scopes": ["user"],
                "allowed-adapters": ["claude-code", "kiro", "codex"],
            }
        )
        errors = validate(pack, _load_schema())
        self.assertEqual(errors, [])

    def test_allowed_adapters_empty_array_refused_by_schema(self) -> None:
        from agentbundle.build.validate import validate

        pack = _v06_pack(
            install={
                "default-scope": "repo",
                "allowed-adapters": [],
            }
        )
        errors = validate(pack, _load_schema())
        self.assertTrue(errors)

    def test_allowed_adapters_duplicates_refused_by_cross_field(self) -> None:
        # The bundled validator doesn't enforce JSONSchema uniqueItems;
        # the cross-field check catches duplicates with a refuse message.
        pack = _v06_pack(
            install={
                "default-scope": "repo",
                "allowed-adapters": ["claude-code", "claude-code"],
            }
        )
        msg = _validate_allowed_adapters(pack)
        self.assertIsNotNone(msg)
        self.assertIn("duplicate", msg)


# ---------------------------------------------------------------------------
# Cross-field check (`_validate_allowed_adapters`)
# ---------------------------------------------------------------------------


class TestValidateAllowedAdaptersCrossField(unittest.TestCase):
    def test_returns_none_when_field_absent(self) -> None:
        pack = _v06_pack(install={"default-scope": "repo"})
        self.assertIsNone(_validate_allowed_adapters(pack))

    def test_repo_only_pack_admits_copilot(self) -> None:
        """Copilot is shipped but lacks user-scope; a repo-only pack
        legitimately declares it."""
        pack = _v06_pack(
            install={
                "default-scope": "repo",
                "allowed-adapters": ["copilot"],
            }
        )
        self.assertIsNone(_validate_allowed_adapters(pack))

    def test_user_scope_pack_accepts_copilot(self) -> None:
        # RFC-0024 / docs/specs/copilot-full-parity: copilot is now a
        # user-scope-capable adapter (`[adapter.copilot.scope].user`), so a
        # user-scope pack declaring it is **accepted** — the inverse of the
        # repo-only refusal RFC-0012 recorded. (`research`, a user-scope-default
        # pack, ships exactly this.)
        pack = _v06_pack(
            install={
                "default-scope": "user",
                "allowed-scopes": ["user"],
                "allowed-adapters": ["copilot"],
            }
        )
        msg = _validate_allowed_adapters(pack)
        self.assertIsNone(msg, f"copilot should be accepted at user scope: {msg}")

    def test_unknown_adapter_refused(self) -> None:
        pack = _v06_pack(
            install={
                "default-scope": "repo",
                "allowed-adapters": ["windsurf"],
            }
        )
        msg = _validate_allowed_adapters(pack)
        self.assertIsNotNone(msg)
        self.assertIn("'windsurf'", msg)
        self.assertIn("not a shipped adapter", msg)


# ---------------------------------------------------------------------------
# `_kiro_target_adapters` literal-gate fix (semantic predicate)
# ---------------------------------------------------------------------------


class TestKiroTargetAdaptersV06Gate(unittest.TestCase):
    def _make_pack_tree(self, tmp_path: Path, *, with_agents: bool, with_wiring: bool):
        apm = tmp_path / ".apm"
        apm.mkdir(parents=True)
        if with_agents:
            (apm / "agents").mkdir()
            (apm / "agents" / "a.md").write_text("dummy", encoding="utf-8")
        if with_wiring:
            (apm / "hook-wiring").mkdir()
            (apm / "hook-wiring" / "w.toml").write_text("event = 'PreToolUse'\n", encoding="utf-8")
        return tmp_path

    def test_v06_pack_with_on_disk_shape_no_allowed_adapters_fires_rail(self) -> None:
        """The case the round-1 literal `version != \"0.3\"` gate broke:
        a v0.6 pack shipping agents + wiring without allowed-adapters
        should still fire the rail through the on-disk inference path."""
        import tempfile

        with tempfile.TemporaryDirectory() as td:
            pack_path = self._make_pack_tree(
                Path(td), with_agents=True, with_wiring=True
            )
            pack_data = _v06_pack(install={"default-scope": "repo"})
            result = _kiro_target_adapters(pack_data, pack_path)
            self.assertEqual(result, {"kiro"})

    def test_v06_pack_excluding_kiro_returns_empty(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as td:
            pack_path = self._make_pack_tree(
                Path(td), with_agents=True, with_wiring=True
            )
            pack_data = _v06_pack(
                install={
                    "default-scope": "user",
                    "allowed-scopes": ["user"],
                    "allowed-adapters": ["claude-code"],
                }
            )
            result = _kiro_target_adapters(pack_data, pack_path)
            self.assertEqual(result, set())

    def test_v06_pack_including_kiro_returns_kiro(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as td:
            pack_path = self._make_pack_tree(
                Path(td), with_agents=False, with_wiring=False  # not even on-disk
            )
            pack_data = _v06_pack(
                install={
                    "default-scope": "user",
                    "allowed-scopes": ["user"],
                    "allowed-adapters": ["kiro"],
                }
            )
            result = _kiro_target_adapters(pack_data, pack_path)
            self.assertEqual(result, {"kiro"})

    def test_v03_pack_unchanged(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as td:
            pack_path = self._make_pack_tree(
                Path(td), with_agents=True, with_wiring=True
            )
            pack_data = {
                "pack": {
                    "name": "demo",
                    "adapter-contract": {"version": "0.3"},
                }
            }
            result = _kiro_target_adapters(pack_data, pack_path)
            self.assertEqual(result, {"kiro"})

    def test_v02_pack_skips_rail(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as td:
            pack_path = self._make_pack_tree(
                Path(td), with_agents=True, with_wiring=True
            )
            pack_data = {
                "pack": {
                    "name": "demo",
                    "adapter-contract": {"version": "0.2"},
                }
            }
            result = _kiro_target_adapters(pack_data, pack_path)
            self.assertEqual(result, set())


if __name__ == "__main__":
    unittest.main()
