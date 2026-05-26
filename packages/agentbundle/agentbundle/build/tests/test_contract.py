"""Tests for adapter.toml + adapter.schema.json (T1b).

Verifies:
  - adapter.toml validates against adapter.schema.json (AC 1).
  - Every (5 primitives × 4 adapters) = 20 pairs is present — no missing,
    no extra (AC 1).
  - The mode enum in adapter.schema.json contains exactly the seven RFC-0001 modes;
    unknown modes are rejected (AC 2).
  - Every projection entry carries an on-conflict value from the legal set,
    matching the per-mode default — except for degraded-info-log and dropped
    which are no-write/no-output and carry no on-conflict (AC 2).
  - hook-wiring primitive's source-path is .apm/hook-wiring/.
  - command primitive's source-path is .apm/commands/; Claude Code projects
    direct-file; Copilot/Codex/Kiro are dropped.
  - frontmatter-mapping table for kiro-agent-frontmatter-v0.9 validates
    against schema; frontmatter-default table for copilot-instruction
    validates and is structurally distinct.
"""

from __future__ import annotations

import json
import tomllib
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[5]
CONTRACT_PATH = REPO_ROOT / "docs" / "contracts" / "adapter.toml"
SCHEMA_PATH = REPO_ROOT / "docs" / "contracts" / "adapter.schema.json"

# All seven RFC-0001 projection modes.
SEVEN_RFC_MODES = {
    "direct-directory",
    "direct-file",
    "merge-json",
    "instruction-file",
    "managed-block-inline",
    "degraded-info-log",
    "dropped",
}

# Legal on-conflict values.
LEGAL_ON_CONFLICT = {
    "prompt-then-preserve",
    "prompt-then-overwrite",
    "preserve-outside-block",
    "merge-managed-key-only",
    "overwrite-without-prompt",
}

# Per-mode default on-conflict values (no-write modes have no on-conflict).
MODE_DEFAULT_ON_CONFLICT = {
    "direct-directory": "prompt-then-preserve",
    "direct-file": "prompt-then-preserve",
    "merge-json": "merge-managed-key-only",
    "instruction-file": "prompt-then-overwrite",
    "managed-block-inline": "preserve-outside-block",
    # degraded-info-log and dropped carry no on-conflict
}

# Modes that are no-write / no-output — they do not require an on-conflict.
NO_WRITE_MODES = {"degraded-info-log", "dropped"}

# All five primitive names.
ALL_PRIMITIVES = {"skill", "agent", "hook-body", "hook-wiring", "command"}

# All four reference adapter names.
ALL_ADAPTERS = {"claude-code", "kiro", "copilot", "codex"}


def _load_contract() -> dict:
    return tomllib.loads(CONTRACT_PATH.read_bytes().decode("utf-8"))


def _load_schema() -> dict:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


class ContractSchemaValidationTests(unittest.TestCase):
    """adapter.toml must validate against adapter.schema.json (AC 1)."""

    def test_contract_validates_against_schema(self) -> None:
        from agentbundle.build.validate import validate

        contract = _load_contract()
        schema = _load_schema()
        errors = validate(contract, schema)
        self.assertEqual(
            errors,
            [],
            f"adapter.toml failed schema validation:\n" + "\n".join(errors),
        )


class AllPairsEnumeratedTests(unittest.TestCase):
    """Every (primitive × adapter) pair must be present — no missing, no extra."""

    def setUp(self) -> None:
        self.contract = _load_contract()

    def test_all_adapters_present(self) -> None:
        adapters = set(self.contract["adapter"].keys())
        self.assertEqual(adapters, ALL_ADAPTERS, f"adapter keys differ: {adapters}")

    def test_every_primitive_covered_per_adapter(self) -> None:
        """Every (primitive × adapter) pair must be declared in *some* form.

        Under v0.3 (RFC-0005), kiro's `hook-wiring` no longer appears in the
        legacy `projection` array — it lives in the new
        `projections.<primitive>` table. The coverage union walks both forms.
        """
        missing: list[str] = []
        extra: list[str] = []
        for adapter_name, adapter_block in self.contract["adapter"].items():
            array_form = {p["primitive"] for p in adapter_block.get("projection", [])}
            table_form = set(adapter_block.get("projections", {}).keys())
            primitives_in_adapter = array_form | table_form
            for prim in ALL_PRIMITIVES:
                if prim not in primitives_in_adapter:
                    missing.append(f"({prim}, {adapter_name})")
            for prim in primitives_in_adapter:
                if prim not in ALL_PRIMITIVES:
                    extra.append(f"({prim}, {adapter_name})")
        self.assertEqual(missing, [], f"missing pairs: {missing}")
        self.assertEqual(extra, [], f"extra unknown primitives: {extra}")

    def test_exactly_twenty_pairs_total(self) -> None:
        """Twenty (primitive × adapter) pairs — counted across array + table forms.

        Pairs that appear in BOTH forms (the transitional hook-body declarations
        on claude-code/kiro and the claude-code hook-wiring legacy entry that
        coexists with its v0.3 table) count once per adapter, matching the
        "primitive coverage" semantic.
        """
        total = 0
        for adapter_block in self.contract["adapter"].values():
            array_form = {p["primitive"] for p in adapter_block.get("projection", [])}
            table_form = set(adapter_block.get("projections", {}).keys())
            total += len(array_form | table_form)
        self.assertEqual(total, 20, f"expected 20 pairs total, got {total}")


class ModeEnumTests(unittest.TestCase):
    """adapter.schema.json mode enum: seven RFC-0001 modes plus the two
    v0.3 additions from RFC-0005 (`user-merge-json`, `merge-into-agent-json`)."""

    def test_mode_enum_contains_expected_modes(self) -> None:
        schema = _load_schema()
        # Navigate to the mode enum inside projection items.
        projection_items = (
            schema["properties"]["adapter"]["additionalProperties"]["properties"][
                "projection"
            ]["items"]
        )
        mode_enum = set(projection_items["properties"]["mode"]["enum"])
        expected = SEVEN_RFC_MODES | {"user-merge-json", "merge-into-agent-json"}
        self.assertEqual(
            mode_enum,
            expected,
            f"schema mode enum differs from RFC-0001+RFC-0005 set: {mode_enum}",
        )

    def test_schema_rejects_unknown_mode(self) -> None:
        from agentbundle.build.validate import validate

        schema = _load_schema()
        bad_contract = {
            "contract": {"version": "0.1"},
            "primitive": {
                "skill": {"source-path": ".apm/skills/"},
                "agent": {"source-path": ".apm/agents/"},
                "hook-body": {"source-path": ".apm/hooks/"},
                "hook-wiring": {"source-path": ".apm/hook-wiring/"},
                "command": {"source-path": ".apm/commands/"},
            },
            "adapter": {
                "claude-code": {
                    "projection": [
                        {
                            "primitive": "skill",
                            "mode": "not-a-real-mode",
                            "target-path": ".claude/skills/",
                            "on-conflict": "prompt-then-preserve",
                        }
                    ]
                }
            },
        }
        errors = validate(bad_contract, schema)
        self.assertTrue(errors, "schema accepted an unknown projection mode")


class OnConflictTests(unittest.TestCase):
    """Every write-mode projection must carry a legal on-conflict matching the default."""

    def setUp(self) -> None:
        self.contract = _load_contract()

    def test_write_mode_projections_carry_on_conflict(self) -> None:
        for adapter_name, adapter_block in self.contract["adapter"].items():
            for projection in adapter_block["projection"]:
                mode = projection["mode"]
                if mode in NO_WRITE_MODES:
                    # no-write modes must NOT be required to carry on-conflict
                    continue
                self.assertIn(
                    "on-conflict",
                    projection,
                    f"({projection['primitive']}, {adapter_name}) mode={mode} missing on-conflict",
                )

    def test_on_conflict_values_are_legal(self) -> None:
        for adapter_name, adapter_block in self.contract["adapter"].items():
            for projection in adapter_block["projection"]:
                if "on-conflict" in projection:
                    self.assertIn(
                        projection["on-conflict"],
                        LEGAL_ON_CONFLICT,
                        f"({projection['primitive']}, {adapter_name}) illegal on-conflict: "
                        f"{projection['on-conflict']!r}",
                    )

    def test_on_conflict_matches_mode_default(self) -> None:
        for adapter_name, adapter_block in self.contract["adapter"].items():
            for projection in adapter_block["projection"]:
                mode = projection["mode"]
                if mode in NO_WRITE_MODES:
                    continue
                expected = MODE_DEFAULT_ON_CONFLICT.get(mode)
                if expected is None:
                    continue  # mode has no default; explicit override required
                self.assertEqual(
                    projection.get("on-conflict"),
                    expected,
                    f"({projection['primitive']}, {adapter_name}) mode={mode}: "
                    f"expected on-conflict={expected!r}, got {projection.get('on-conflict')!r}",
                )

    def test_no_write_modes_have_no_on_conflict(self) -> None:
        for adapter_name, adapter_block in self.contract["adapter"].items():
            for projection in adapter_block["projection"]:
                mode = projection["mode"]
                if mode in NO_WRITE_MODES:
                    self.assertNotIn(
                        "on-conflict",
                        projection,
                        f"({projection['primitive']}, {adapter_name}) mode={mode} "
                        f"should not carry on-conflict",
                    )


class SourcePathTests(unittest.TestCase):
    """Primitive source-path values must match the spec."""

    def setUp(self) -> None:
        self.contract = _load_contract()

    def test_hook_wiring_source_path(self) -> None:
        self.assertEqual(
            self.contract["primitive"]["hook-wiring"]["source-path"],
            ".apm/hook-wiring/",
        )

    def test_command_source_path(self) -> None:
        self.assertEqual(
            self.contract["primitive"]["command"]["source-path"],
            ".apm/commands/",
        )


class CommandProjectionTests(unittest.TestCase):
    """command primitive: Claude Code = direct-file; Kiro/Copilot/Codex = dropped."""

    def setUp(self) -> None:
        self.contract = _load_contract()

    def _projection_for(self, adapter: str, primitive: str) -> dict:
        for p in self.contract["adapter"][adapter]["projection"]:
            if p["primitive"] == primitive:
                return p
        self.fail(f"projection for ({primitive}, {adapter}) not found")

    def test_claude_code_command_is_direct_file(self) -> None:
        proj = self._projection_for("claude-code", "command")
        self.assertEqual(proj["mode"], "direct-file")
        self.assertEqual(proj["target-path"], ".claude/commands/")

    def test_kiro_command_is_dropped(self) -> None:
        proj = self._projection_for("kiro", "command")
        self.assertEqual(proj["mode"], "dropped")

    def test_copilot_command_is_dropped(self) -> None:
        proj = self._projection_for("copilot", "command")
        self.assertEqual(proj["mode"], "dropped")

    def test_codex_command_is_dropped(self) -> None:
        proj = self._projection_for("codex", "command")
        self.assertEqual(proj["mode"], "dropped")


class FrontmatterTableTests(unittest.TestCase):
    """frontmatter-mapping and frontmatter-default tables validate and are distinct."""

    def setUp(self) -> None:
        self.contract = _load_contract()
        self.schema = _load_schema()

    def test_kiro_frontmatter_mapping_present(self) -> None:
        mapping = self.contract.get("frontmatter-mapping", {})
        self.assertIn(
            "kiro-agent-frontmatter-v0.9",
            mapping,
            "frontmatter-mapping.kiro-agent-frontmatter-v0.9 not found in contract",
        )

    def test_kiro_frontmatter_mapping_validates_against_schema(self) -> None:
        from agentbundle.build.validate import validate

        errors = validate(self.contract, self.schema)
        self.assertEqual(
            errors,
            [],
            f"contract with frontmatter-mapping failed validation:\n"
            + "\n".join(errors),
        )

    def test_copilot_frontmatter_default_present(self) -> None:
        defaults = self.contract.get("frontmatter-default", {})
        self.assertIn(
            "copilot-instruction",
            defaults,
            "frontmatter-default.copilot-instruction not found in contract",
        )

    def test_copilot_frontmatter_default_has_apply_to(self) -> None:
        default = self.contract["frontmatter-default"]["copilot-instruction"]
        self.assertIn("applyTo", default)
        self.assertEqual(default["applyTo"], "**")

    def test_frontmatter_mapping_and_default_are_structurally_distinct(self) -> None:
        # mapping = rewrite rules (nested objects with rename/normalize/default fields)
        # default = inject-when-missing (flat string→string map)
        mapping = self.contract.get("frontmatter-mapping", {})
        defaults = self.contract.get("frontmatter-default", {})

        # They must be under different top-level keys.
        self.assertNotEqual(
            set(mapping.keys()).intersection(set(defaults.keys())),
            set(mapping.keys()),
            "frontmatter-mapping and frontmatter-default share the same sub-keys",
        )

        # frontmatter-mapping entries are nested objects (rewrite rules).
        for key, mapping_table in mapping.items():
            self.assertIsInstance(
                mapping_table,
                dict,
                f"frontmatter-mapping.{key} should be a dict of rewrite rules",
            )
            for field, rule in mapping_table.items():
                self.assertIsInstance(
                    rule,
                    dict,
                    f"frontmatter-mapping.{key}.{field} should be a dict (rewrite rule)",
                )

        # frontmatter-default entries are flat string→string maps.
        for key, default_table in defaults.items():
            self.assertIsInstance(
                default_table,
                dict,
                f"frontmatter-default.{key} should be a dict",
            )
            for field, value in default_table.items():
                self.assertIsInstance(
                    value,
                    str,
                    f"frontmatter-default.{key}.{field} should be a string",
                )


class ContractV05Tests(unittest.TestCase):
    """T2 (apm-install-route-parity AC9): contract-version assertion.

    Originally pinned v0.5; bumped to v0.6 by RFC-0011 and to v0.7 by
    RFC-0013 / credential-broker-contract. Class name preserved to avoid
    needless diff churn against the next bump.
    """

    def setUp(self) -> None:
        self.contract = _load_contract()
        self.schema = _load_schema()

    def test_contract_version_is_v05(self) -> None:
        """tomllib.loads of adapter.toml returns contract.version == "0.7"
        (bumped from "0.6" by RFC-0013 / credential-broker-contract).
        """
        self.assertEqual(
            self.contract["contract"]["version"],
            "0.7",
            "adapter.toml [contract] version must be '0.7' after RFC-0013 bump",
        )

    def test_claude_code_install_routes_includes_apm(self) -> None:
        """[adapter."claude-code"] carries install-routes == ["cli", "claude-plugins", "apm"]."""
        routes = self.contract["adapter"]["claude-code"].get("install-routes")
        self.assertEqual(
            routes,
            ["cli", "claude-plugins", "apm"],
            f"expected install-routes=['cli', 'claude-plugins', 'apm'], got {routes!r}",
        )

    def test_other_adapters_have_no_install_routes(self) -> None:
        """Kiro, Copilot, and Codex do not declare install-routes (regression guard:
        the v0.4 → v0.5 bump must not silently extend the field's surface to those
        adapters; per-adapter optionality / default ['cli'] on read is unchanged)."""
        for adapter_name in ("kiro", "copilot", "codex"):
            adapter_block = self.contract["adapter"].get(adapter_name, {})
            self.assertNotIn(
                "install-routes",
                adapter_block,
                f"adapter '{adapter_name}' must not carry install-routes (only claude-code does)",
            )

    def test_adapter_schema_accepts_apm_enum_value(self) -> None:
        """Round-trip: the v0.5 contract validates; "apm" is admitted; a value
        outside the three-value enum is rejected."""
        from agentbundle.build.validate import validate

        # Full contract validates (includes "apm" on install-routes).
        errors = validate(self.contract, self.schema)
        self.assertEqual(
            errors,
            [],
            f"adapter.toml with apm install-route failed schema validation:\n"
            + "\n".join(errors),
        )

        # Omitting install-routes is also valid (field is optional).
        minimal_contract = {
            "contract": {"version": "0.5"},
            "primitive": {
                "skill": {"source-path": ".apm/skills/"},
                "agent": {"source-path": ".apm/agents/"},
                "hook-body": {"source-path": ".apm/hooks/"},
                "hook-wiring": {"source-path": ".apm/hook-wiring/"},
                "command": {"source-path": ".apm/commands/"},
            },
            "adapter": {
                "claude-code": {}
            },
        }
        errors = validate(minimal_contract, self.schema)
        self.assertEqual(
            errors,
            [],
            f"adapter without install-routes (optional) should validate:\n"
            + "\n".join(errors),
        )

        # install-routes value outside the enum must be rejected (regression guard
        # for the enum extension: adding "apm" must not have widened the field to
        # any string).
        bad_contract = {
            "contract": {"version": "0.5"},
            "primitive": {
                "skill": {"source-path": ".apm/skills/"},
                "agent": {"source-path": ".apm/agents/"},
                "hook-body": {"source-path": ".apm/hooks/"},
                "hook-wiring": {"source-path": ".apm/hook-wiring/"},
                "command": {"source-path": ".apm/commands/"},
            },
            "adapter": {
                "claude-code": {
                    "install-routes": ["foo"],
                }
            },
        }
        errors = validate(bad_contract, self.schema)
        self.assertTrue(
            errors,
            "schema must reject install-routes value outside the three-value enum",
        )

        # install-routes as a string (not array) must still be rejected.
        bad_contract_str = {
            "contract": {"version": "0.5"},
            "primitive": {
                "skill": {"source-path": ".apm/skills/"},
                "agent": {"source-path": ".apm/agents/"},
                "hook-body": {"source-path": ".apm/hooks/"},
                "hook-wiring": {"source-path": ".apm/hook-wiring/"},
                "command": {"source-path": ".apm/commands/"},
            },
            "adapter": {
                "claude-code": {
                    "install-routes": "cli",
                }
            },
        }
        errors = validate(bad_contract_str, self.schema)
        self.assertTrue(
            errors,
            "schema must reject install-routes as a string (must be an array)",
        )
DATA_CONTRACT_PATH = (
    REPO_ROOT
    / "packages"
    / "agentbundle"
    / "agentbundle"
    / "_data"
    / "adapter.toml"
)
SEED_AGENTS_MD_PATH = REPO_ROOT / "packs" / "core" / "seeds" / "AGENTS.md"


class TestCodexSkillDirectDirectory(unittest.TestCase):
    """RFC-0009 / codex-native-skills contract flip.

    AC1: Codex `skill` is `direct-directory` projecting to
         `.agents/skills/` with `on-conflict = "prompt-then-preserve"`;
         no managed-block delimiter keys remain on the entry.
    AC2: `docs/contracts/adapter.toml` and the bundled `_data/adapter.toml`
         are byte-identical.
    AC15: The seed AGENTS.md no longer carries the legacy delimiter pair.
    """

    def test_codex_skill_projection_is_direct_directory(self) -> None:
        contract = tomllib.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
        codex_entries = contract["adapter"]["codex"]["projection"]
        skill_entries = [e for e in codex_entries if e["primitive"] == "skill"]
        self.assertEqual(len(skill_entries), 1)
        entry = skill_entries[0]
        self.assertEqual(entry["mode"], "direct-directory")
        self.assertEqual(entry["target-path"], ".agents/skills/")
        self.assertEqual(entry["on-conflict"], "prompt-then-preserve")
        self.assertNotIn("managed-block-delimiter-start", entry)
        self.assertNotIn("managed-block-delimiter-end", entry)

    def test_contract_files_byte_identical(self) -> None:
        self.assertEqual(
            CONTRACT_PATH.read_bytes(),
            DATA_CONTRACT_PATH.read_bytes(),
        )

    def test_seed_agents_md_has_no_legacy_delimiters(self) -> None:
        text = SEED_AGENTS_MD_PATH.read_text(encoding="utf-8")
        self.assertNotIn("<!-- agent-skills:start -->", text)
        self.assertNotIn("<!-- agent-skills:end -->", text)


if __name__ == "__main__":
    unittest.main()
