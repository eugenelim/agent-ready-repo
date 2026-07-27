#!/usr/bin/env python3
"""Bucket 14 contract tests for catalogue-tooling-docs (Wave 5b)."""
import pathlib
import re
import unittest

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent

_PACKS_AGENTS = REPO_ROOT / "packs" / "AGENTS.md"
_AGENTS_LOCAL = REPO_ROOT / "AGENTS.local.md"
_AGENTS_ROOT = REPO_ROOT / "AGENTS.md"
_SEEDS_AGENTS = REPO_ROOT / "packs" / "core" / "seeds" / "AGENTS.md"
_ADAPTER_TOML = REPO_ROOT / "contracts" / "adapter.toml"

_EXPECTED_GUIDES = [
    "docs/guides/reference/catalogue-toml.md",
    "docs/guides/reference/catalogue-commands.md",
    "docs/guides/reference/catalogue-migration.md",
    "docs/guides/reference/catalogue-archive.md",
    "docs/guides/how-to/create-external-catalogue.md",
    "docs/guides/how-to/enterprise-app-store.md",
    "docs/guides/how-to/flow-e-disconnected.md",
    "docs/guides/explanation/release-coupling.md",
]


class AgentsMdTest(unittest.TestCase):
    def setUp(self):
        self._text = _PACKS_AGENTS.read_text(encoding="utf-8")
        self._lines = self._text.splitlines()

    def test_line_count(self):
        self.assertLessEqual(len(self._lines), 150, f"packs/AGENTS.md is {len(self._lines)} lines; must be ≤ 150")

    def test_primitive_dirs(self):
        adapter_text = _ADAPTER_TOML.read_text(encoding="utf-8")
        source_paths = re.findall(r'source-path\s*=\s*"([^"]+)"', adapter_text)
        self.assertTrue(source_paths, "No source-path entries found in adapter.toml")
        for path in source_paths:
            self.assertIn(path, self._text, f"Primitive source path {path!r} missing from packs/AGENTS.md")

    def test_schema_tables(self):
        major_tables = (
            "adapter-contract",
            "recipes",
            "dependencies",
            "seeds",
            "layout",
            "first-value",
            "adaptation",
        )
        for table in major_tables:
            self.assertIn(table, self._text, f"Schema table {table!r} missing from packs/AGENTS.md")

    def test_canonical_commands(self):
        self.assertIn("agentbundle catalogue lint", self._text)
        self.assertIn("agentbundle catalogue verify", self._text)
        self.assertIn("agentbundle catalogue self-host", self._text)

    def test_pack_design_model(self):
        for word in ("intent", "journey", "capability"):
            self.assertIn(word, self._text, f"Design model word {word!r} missing from packs/AGENTS.md")


class AgentsLocalMdTest(unittest.TestCase):
    def setUp(self):
        self._text = _AGENTS_LOCAL.read_text(encoding="utf-8")

    def test_has_release_coupling(self):
        self.assertIn(
            "release coupling",
            self._text.lower(),
            "AGENTS.local.md must contain a Release Coupling section",
        )

    def test_projected_agents_no_release_coupling(self):
        for path in (_AGENTS_ROOT, _SEEDS_AGENTS):
            text = path.read_text(encoding="utf-8")
            self.assertNotIn(
                "Release Coupling",
                text,
                f"{path.relative_to(REPO_ROOT)} must NOT contain 'Release Coupling'",
            )


class GuideDocsTest(unittest.TestCase):
    def test_guide_files_exist(self):
        for rel in _EXPECTED_GUIDES:
            p = REPO_ROOT / rel
            self.assertTrue(p.exists(), f"Missing guide: {rel}")

    def test_flow_e_no_local_descriptor_claim(self):
        p = REPO_ROOT / "docs/guides/how-to/flow-e-disconnected.md"
        self.assertTrue(p.exists(), "flow-e-disconnected.md guide must exist")
        text = p.read_text(encoding="utf-8").lower()
        self.assertIn(
            "not supported",
            text,
            "Flow E guide must explicitly state that local channel-descriptor resolution is NOT supported",
        )

    def test_guide_uses_canonical_commands(self):
        old_patterns = (
            "agentbundle.build lint-packs",
            "agentbundle.build build",
            "agentbundle.build check",
        )
        for rel in _EXPECTED_GUIDES:
            p = REPO_ROOT / rel
            if not p.exists():
                continue
            if "migration" in rel:
                continue  # migration table is allowed to reference old commands
            text = p.read_text(encoding="utf-8")
            for old in old_patterns:
                self.assertNotIn(old, text, f"{rel} references old command {old!r}")


if __name__ == "__main__":
    unittest.main()
