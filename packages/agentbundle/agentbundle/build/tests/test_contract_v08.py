"""Tests for adapter-contract v0.8 (docs/specs/dropped-primitives-coverage).

Verifies the T1 contract edits:

  - ``[contract] version == "0.8"`` in both the runtime data file
    (`_data/adapter.toml`) and the docs mirror.
  - Codex `agent` projection: ``mode == "codex-agent-toml"``,
    ``target-path == ".codex/agents/"``,
    ``frontmatter-mapping == "codex-agent-frontmatter-v0.8"``.
  - Codex `hook-wiring` projection: ``mode == "merge-json"``,
    ``target-path == ".codex/hooks.json"``, ``managed-key == "hooks"``.
  - Codex `command` projection: stays `dropped` (no upstream target).
  - ``[adapter.codex.scope].allowed-prefixes.repo`` and ``.user`` each
    include ``".codex/"``.
  - ``[frontmatter-mapping."codex-agent-frontmatter-v0.8"]`` declares
    per-key sub-tables for ``name`` and ``description``; no ``body``
    sub-table (body-to-``developer_instructions`` is a mode-level
    convention, not a rename rule).
  - Schema admits ``"codex-agent-toml"`` at every site that currently
    enumerates ``"dropped"``.
  - Schema validates the v0.8 contract end-to-end.
  - Property invariants for claude-code (all 5 primitives projected) and
    kiro (4 of 5 with `command: dropped`) survive the codex changes
    untouched. Copilot's 3 dropped entries unchanged.
"""

from __future__ import annotations

import json
import tomllib
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[5]
DATA_CONTRACT_PATH = (
    REPO_ROOT / "packages" / "agentbundle" / "agentbundle" / "_data" / "adapter.toml"
)
DOCS_CONTRACT_PATH = REPO_ROOT / "docs" / "contracts" / "adapter.toml"
DATA_SCHEMA_PATH = (
    REPO_ROOT
    / "packages"
    / "agentbundle"
    / "agentbundle"
    / "_data"
    / "adapter.schema.json"
)


def _codex_projection(contract: dict, primitive: str) -> dict:
    """Find the [[adapter.codex.projection]] entry for ``primitive``."""
    for entry in contract["adapter"]["codex"]["projection"]:
        if entry["primitive"] == primitive:
            return entry
    raise AssertionError(f"codex projection for primitive {primitive!r} not found")


class TestContractV08(unittest.TestCase):
    def setUp(self) -> None:
        self.contract = tomllib.loads(DATA_CONTRACT_PATH.read_text(encoding="utf-8"))
        self.docs_contract = tomllib.loads(
            DOCS_CONTRACT_PATH.read_text(encoding="utf-8")
        )
        self.schema = json.loads(DATA_SCHEMA_PATH.read_text(encoding="utf-8"))

    def test_contract_version_is_08(self) -> None:
        # v0.8 features are present; exact version check lives in test_contract.py.
        # The v0.8 features (codex-agent-toml, codex-agent-frontmatter-v0.8) must
        # survive future bumps — verify via the codex-specific tests below.
        version = self.contract["contract"]["version"]
        self.assertGreaterEqual(version, "0.8", "contract version must be >= 0.8")

    def test_docs_contract_version_is_08(self) -> None:
        version = self.docs_contract["contract"]["version"]
        self.assertGreaterEqual(version, "0.8", "docs contract version must be >= 0.8")

    def test_codex_agent_projection(self) -> None:
        entry = _codex_projection(self.contract, "agent")
        self.assertEqual(entry["mode"], "codex-agent-toml")
        self.assertEqual(entry["target-path"], ".codex/agents/")
        self.assertEqual(
            entry["frontmatter-mapping"], "codex-agent-frontmatter-v0.8"
        )
        self.assertEqual(entry["on-conflict"], "prompt-then-preserve")

    def test_codex_hook_wiring_projection(self) -> None:
        entry = _codex_projection(self.contract, "hook-wiring")
        self.assertEqual(entry["mode"], "merge-json")
        self.assertEqual(entry["target-path"], ".codex/hooks.json")
        self.assertEqual(entry["managed-key"], "hooks")
        self.assertEqual(entry["on-conflict"], "merge-managed-key-only")

    def test_codex_command_still_dropped(self) -> None:
        entry = _codex_projection(self.contract, "command")
        self.assertEqual(entry["mode"], "dropped")

    def test_codex_skill_projection_unchanged(self) -> None:
        """Non-regression — codex skill projection at `.agents/skills/` unchanged."""
        entry = _codex_projection(self.contract, "skill")
        self.assertEqual(entry["mode"], "direct-directory")
        self.assertEqual(entry["target-path"], ".agents/skills/")

    def test_codex_hook_body_projection_unchanged(self) -> None:
        """Non-regression — codex hook-body projection at `tools/hooks/` unchanged."""
        entry = _codex_projection(self.contract, "hook-body")
        self.assertEqual(entry["mode"], "direct-file")
        self.assertEqual(entry["target-path"], "tools/hooks/")

    def test_codex_allowed_prefixes_includes_codex_dir(self) -> None:
        scope = self.contract["adapter"]["codex"]["scope"]
        self.assertIn(".codex/", scope["allowed-prefixes"]["repo"])
        self.assertIn(".codex/", scope["allowed-prefixes"]["user"])

    def test_codex_allowed_prefixes_preserves_existing_entries(self) -> None:
        """Non-regression — `.agents/skills/`, `.agentbundle/`, `tools/hooks/` still present."""
        repo = self.contract["adapter"]["codex"]["scope"]["allowed-prefixes"]["repo"]
        user = self.contract["adapter"]["codex"]["scope"]["allowed-prefixes"]["user"]
        for entry in (".agents/skills/", ".agentbundle/"):
            self.assertIn(entry, repo)
            self.assertIn(entry, user)
        self.assertIn("tools/hooks/", repo)

    def test_codex_frontmatter_mapping_table(self) -> None:
        mapping = self.contract["frontmatter-mapping"]["codex-agent-frontmatter-v0.8"]
        # Required per-key sub-tables.
        self.assertIn("name", mapping)
        self.assertEqual(mapping["name"]["rename"], "name")
        self.assertIn("description", mapping)
        self.assertEqual(mapping["description"]["rename"], "description")
        # No `body` sub-table — body-to-`developer_instructions` is a
        # mode-level convention per spec AC4, not a frontmatter rename.
        self.assertNotIn("body", mapping)
        self.assertNotIn("developer_instructions", mapping)

    def test_schema_admits_codex_agent_toml_mode_at_every_dropped_site(self) -> None:
        """Walk the schema; every enum array containing "dropped" must also
        contain "codex-agent-toml". Discovered dynamically so a future schema
        edit that adds a fifth enum site doesn't silently drift this AC."""

        def walk(node, path):
            if isinstance(node, dict):
                for k, v in node.items():
                    if k == "enum" and isinstance(v, list) and "dropped" in v:
                        self.assertIn(
                            "codex-agent-toml",
                            v,
                            f"schema enum at {path} admits 'dropped' but not "
                            f"'codex-agent-toml': {v!r}",
                        )
                    walk(v, f"{path}.{k}")
            elif isinstance(node, list):
                for i, v in enumerate(node):
                    walk(v, f"{path}[{i}]")

        walk(self.schema, "$")

    def test_schema_loads_v08_contract(self) -> None:
        """End-to-end: load schema, validate v0.8 contract; no errors. This
        is load-bearing — it pins that codex's new `codex-agent-toml` mode
        and the codex `merge-json` reuse both validate at the codex array
        site (the projection-mode enum is global across adapters, so
        `merge-json` already validates without per-site enum edits)."""
        from agentbundle.build.validate import validate

        errors = validate(self.contract, self.schema)
        self.assertEqual(
            errors,
            [],
            "v0.8 adapter.toml failed schema validation:\n" + "\n".join(errors),
        )

    def test_claude_code_unchanged_post_v08(self) -> None:
        """Property invariant — claude-code projects all 5 primitives."""
        primitives = {
            entry["primitive"]: entry
            for entry in self.contract["adapter"]["claude-code"]["projection"]
        }
        self.assertEqual(
            set(primitives), {"skill", "agent", "hook-body", "hook-wiring", "command"}
        )
        for primitive, entry in primitives.items():
            self.assertNotEqual(
                entry["mode"],
                "dropped",
                f"claude-code {primitive} unexpectedly dropped at v0.8",
            )

    def test_kiro_unchanged_post_v08(self) -> None:
        """Property invariant — kiro projects 4 of 5 primitives; command dropped."""
        primitives = {
            entry["primitive"]: entry
            for entry in self.contract["adapter"]["kiro"]["projection"]
        }
        self.assertEqual(primitives["command"]["mode"], "dropped")
        for primitive in ("skill", "agent", "hook-body"):
            self.assertNotEqual(
                primitives[primitive]["mode"],
                "dropped",
                f"kiro {primitive} unexpectedly dropped at v0.8",
            )

    def test_copilot_unchanged_post_v08(self) -> None:
        """Property invariant — copilot has 3 dropped primitives unchanged."""
        primitives = {
            entry["primitive"]: entry
            for entry in self.contract["adapter"]["copilot"]["projection"]
        }
        for primitive in ("agent", "hook-wiring", "command"):
            self.assertEqual(
                primitives[primitive]["mode"],
                "dropped",
                f"copilot {primitive} should still be dropped at v0.8",
            )
        for primitive in ("skill", "hook-body"):
            self.assertNotEqual(
                primitives[primitive]["mode"],
                "dropped",
                f"copilot {primitive} unexpectedly dropped at v0.8",
            )


if __name__ == "__main__":
    unittest.main()
