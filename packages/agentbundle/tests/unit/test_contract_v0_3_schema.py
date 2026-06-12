"""T1: adapter contract v0.3 schema acceptances and refusals.

Note: the contract version was bumped from "0.3" to "0.4" by T2 (spec
claude-plugins-install-route / RFC-0008), then to "0.5" by T2 of spec
apm-install-route-parity / RFC-0010. The v0.3 structural tests below
remain valid under v0.5 (all v0.3 fields are preserved); only AC7's
version assertion is updated.

Covers spec ACs:
  AC1 — `[adapter.kiro.scope]` with `allowed-prefixes.user = [".kiro/", ".agentbundle/"]`.
  AC2 — `[adapter.kiro.projections.hook-wiring]` with `mode = "merge-into-agent-json"`,
        `managed-key = "hooks"`, five-event `agent-event-vocabulary`. Legacy
        `degraded-info-log` entry removed.
  AC3 — `[adapter."claude-code".projections.hook-wiring]` with `mode.repo = "merge-json"`,
        `mode.user = "user-merge-json"`, scope-conditional `target`,
        `managed-key.user = "hooks"`.
  AC4 — `[adapter."claude-code".projections.hook-body]` and
        `[adapter.kiro.projections.hook-body]` with scope-conditional `target` values.
  AC5 — `pack.schema.json` accepts `[pack.install] user-scope-hooks = true` and refuses
        any non-boolean value; absent value remains accepted.
  AC7 — contract `version = "0.5"` (originally "0.3"; bumped by T2 of
        claude-plugins-install-route to "0.4"; bumped by T2 of
        apm-install-route-parity to "0.5").

Tests load the shipped `docs/contracts/{adapter,pack}.{toml,schema.json}` and call
the project's stdlib-only validator. Mirrored copies under
`packages/agentbundle/agentbundle/_data/` ship inside the zipapp; the two trees are
kept in sync manually (both excluded from self-host drift comparison).
"""

from __future__ import annotations

import copy
import json
import tomllib
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
CONTRACT_PATH = REPO_ROOT / "docs" / "contracts" / "adapter.toml"
ADAPTER_SCHEMA_PATH = REPO_ROOT / "docs" / "contracts" / "adapter.schema.json"
PACK_SCHEMA_PATH = REPO_ROOT / "docs" / "contracts" / "pack.schema.json"
PLUGIN_MANIFEST_SCHEMA_PATH = REPO_ROOT / "docs" / "contracts" / "plugin-manifest.schema.json"
PLUGIN_MANIFEST_DERIVED_SCHEMA_PATH = REPO_ROOT / "docs" / "contracts" / "plugin-manifest.derived.schema.json"

KIRO_EVENTS = ["agentSpawn", "userPromptSubmit", "preToolUse", "postToolUse", "stop"]


def _load_adapter_schema() -> dict:
    return json.loads(ADAPTER_SCHEMA_PATH.read_text(encoding="utf-8"))


def _load_pack_schema() -> dict:
    return json.loads(PACK_SCHEMA_PATH.read_text(encoding="utf-8"))


def _load_contract() -> dict:
    return tomllib.loads(CONTRACT_PATH.read_text(encoding="utf-8"))


def _parse_pack(toml_text: str) -> dict:
    return tomllib.loads(toml_text)


# ---------------------------------------------------------------------------
# AC7 — contract version
# ---------------------------------------------------------------------------


class ContractVersionTests(unittest.TestCase):
    def test_contract_version_is_0_5(self) -> None:
        # T2 of apm-install-route-parity bumped the contract to v0.5;
        # RFC-0011 / pack-allowed-adapters bumped it to v0.6;
        # RFC-0012 / repo-scope-per-adapter-projection and RFC-0013 /
        # credential-broker-contract co-bumped it to v0.7;
        # docs/specs/dropped-primitives-coverage bumped it to v0.8;
        # RFC-0022 / kiro-adapter-split bumped it to v0.9 (this assertion was
        # left stale at "0.8" then — this CI-only root isn't in `make
        # build-check`, so the drift didn't surface); docs/specs/copilot-full-
        # parity bumped it to v0.10; RFC-0026 / cursor-full-parity bumps it to v0.11.
        self.assertEqual(_load_contract()["contract"]["version"], "0.11")


# ---------------------------------------------------------------------------
# AC1 — Kiro [scope] table
# ---------------------------------------------------------------------------


class KiroScopeBlockTests(unittest.TestCase):
    def test_kiro_scope_present(self) -> None:
        scope = _load_contract()["adapter"]["kiro"].get("scope")
        self.assertIsNotNone(scope, "[adapter.kiro.scope] block missing")
        self.assertEqual(scope["repo"], ".")
        self.assertEqual(scope["user"], "~")

    def test_kiro_allowed_prefixes_user(self) -> None:
        prefixes = _load_contract()["adapter"]["kiro"]["scope"]["allowed-prefixes"]["user"]
        self.assertEqual(prefixes, [".kiro/", ".agentbundle/"])

    def test_contract_validates(self) -> None:
        from agentbundle.build.validate import validate

        errors = validate(_load_contract(), _load_adapter_schema())
        self.assertEqual(errors, [], f"v0.3 contract did not validate: {errors}")

    def test_schema_rejects_kiro_root_prefix(self) -> None:
        """Rail-A constraints carry forward: `/`, `..` segments, empty entries refused."""
        from agentbundle.build.validate import validate

        for bad in (["/"], [""], ["../"]):
            with self.subTest(prefixes=bad):
                contract = _load_contract()
                contract["adapter"]["kiro"]["scope"]["allowed-prefixes"]["user"] = bad
                errors = validate(contract, _load_adapter_schema())
                self.assertTrue(
                    errors,
                    f"schema accepted allowed-prefixes.user = {bad!r}",
                )


# ---------------------------------------------------------------------------
# AC2 — Kiro hook-wiring merge-into-agent-json + agent-event-vocabulary
# ---------------------------------------------------------------------------


class KiroHookWiringTableTests(unittest.TestCase):
    def test_kiro_hook_wiring_uses_new_table(self) -> None:
        contract = _load_contract()
        projections = contract["adapter"]["kiro"].get("projections", {})
        self.assertIn("hook-wiring", projections)
        entry = projections["hook-wiring"]
        self.assertEqual(entry["mode"], "merge-into-agent-json")
        self.assertEqual(entry["managed-key"], "hooks")
        self.assertEqual(entry["agent-event-vocabulary"], KIRO_EVENTS)

    def test_legacy_degraded_info_log_entry_removed(self) -> None:
        """AC2: legacy `[[adapter.kiro.projection]] degraded-info-log` is gone."""
        contract = _load_contract()
        legacy = contract["adapter"]["kiro"].get("projection", [])
        for entry in legacy:
            self.assertNotEqual(
                entry.get("primitive"),
                "hook-wiring",
                "legacy kiro hook-wiring entry still present in projection array",
            )
            self.assertNotEqual(
                entry.get("mode"),
                "degraded-info-log",
                "degraded-info-log entry still present in kiro projection array",
            )


# ---------------------------------------------------------------------------
# AC3 — Claude Code hook-wiring scope-conditional mode/target/managed-key
# ---------------------------------------------------------------------------


class ClaudeCodeHookWiringTableTests(unittest.TestCase):
    """AC3 mandates the new table form be *declared*; it does not require the
    legacy array entry to be removed simultaneously (compare AC2's explicit
    removal of kiro `degraded-info-log`). The legacy entry stays as the
    pipeline-of-record until T5/T7 land — see adapter.toml comment."""

    def test_claude_code_hook_wiring_scope_conditional(self) -> None:
        contract = _load_contract()
        entry = contract["adapter"]["claude-code"]["projections"]["hook-wiring"]
        self.assertEqual(entry["mode"]["repo"], "merge-json")
        self.assertEqual(entry["mode"]["user"], "user-merge-json")
        self.assertEqual(entry["target"]["repo"], ".claude/settings.local.json")
        self.assertEqual(entry["target"]["user"], ".claude/settings.json")
        self.assertEqual(entry["managed-key"]["user"], "hooks")

    def test_managed_key_is_user_only(self) -> None:
        """AC3 names `managed-key.user`; repo scope's `merge-json` carries its
        managed-key contract implicitly (legacy array entry). A `managed-key.repo`
        appearing here would silently duplicate or override that contract."""
        entry = _load_contract()["adapter"]["claude-code"]["projections"]["hook-wiring"]
        self.assertNotIn(
            "repo",
            entry["managed-key"],
            "managed-key.repo unexpectedly present — repo-scope managed-key is "
            "the legacy array entry's concern, not the v0.3 table's",
        )


# ---------------------------------------------------------------------------
# AC4 — hook-body scope-conditional target on both adapters
# ---------------------------------------------------------------------------


class HookBodyScopeConditionalTests(unittest.TestCase):
    """AC4 mandates the new table-form declaration of `hook-body` for both
    adapters. AC4 does not demand removal of the legacy array entries; those
    stay as pipeline-of-record until T5/T7."""

    def test_claude_code_hook_body_scope_conditional(self) -> None:
        entry = _load_contract()["adapter"]["claude-code"]["projections"]["hook-body"]
        self.assertEqual(entry["mode"], "direct-file")
        self.assertIn("repo", entry["target"])
        self.assertIn("user", entry["target"])
        self.assertEqual(entry["target"]["user"], ".claude/hooks/<name>.{sh,py}")

    def test_kiro_hook_body_scope_conditional(self) -> None:
        entry = _load_contract()["adapter"]["kiro"]["projections"]["hook-body"]
        self.assertEqual(entry["mode"], "direct-file")
        self.assertEqual(entry["target"]["user"], ".kiro/hooks/<name>.{sh,py}")


# ---------------------------------------------------------------------------
# Schema-level acceptance / refusal of new shapes (string-or-scope-map)
# ---------------------------------------------------------------------------


def _v03_skeleton() -> dict:
    """A minimal v0.3 contract with just the fields the schema requires.

    Tests mutate the projection entry under test and run the validator. Other
    adapters are pruned so the test focuses on the field-shape under scrutiny.
    """
    return {
        "contract": {"version": "0.3"},
        "primitive": {
            "skill": {"source-path": ".apm/skills/"},
            "agent": {"source-path": ".apm/agents/"},
            "hook-body": {"source-path": ".apm/hooks/"},
            "hook-wiring": {"source-path": ".apm/hook-wiring/"},
            "command": {"source-path": ".apm/commands/"},
        },
        "adapter": {
            "kiro": {
                "projection": [
                    {"primitive": "skill", "mode": "direct-directory",
                     "target-path": ".kiro/skills/", "on-conflict": "prompt-then-preserve"},
                    {"primitive": "agent", "mode": "direct-file",
                     "target-path": ".kiro/agents/", "on-conflict": "prompt-then-preserve"},
                    {"primitive": "command", "mode": "dropped"},
                ],
                "projections": {
                    "hook-body": {
                        "mode": "direct-file",
                        "target": {"repo": "tools/hooks/<name>.{sh,py}",
                                   "user": ".kiro/hooks/<name>.{sh,py}"},
                    },
                    "hook-wiring": {
                        "mode": "merge-into-agent-json",
                        "target": {"repo": ".kiro/agents/<attach-to-agent>.json",
                                   "user": ".kiro/agents/<attach-to-agent>.json"},
                        "managed-key": "hooks",
                        "agent-event-vocabulary": list(KIRO_EVENTS),
                    },
                },
            },
        },
    }


class ScopeConditionalTargetSchemaTests(unittest.TestCase):
    """The new `projections.<primitive>` table accepts bare-string and scope-map `target`."""

    def test_accepts_bare_string_target(self) -> None:
        from agentbundle.build.validate import validate

        skeleton = _v03_skeleton()
        skeleton["adapter"]["kiro"]["projections"]["hook-body"]["target"] = ".kiro/hooks/<name>.{sh,py}"
        errors = validate(skeleton, _load_adapter_schema())
        self.assertEqual(errors, [], f"bare-string target rejected: {errors}")

    def test_accepts_scope_map_target(self) -> None:
        from agentbundle.build.validate import validate

        # _v03_skeleton already uses scope-map; just validate as-is.
        errors = validate(_v03_skeleton(), _load_adapter_schema())
        self.assertEqual(errors, [], f"scope-map target rejected: {errors}")

    def test_refuses_target_with_unknown_key(self) -> None:
        from agentbundle.build.validate import validate

        skeleton = _v03_skeleton()
        skeleton["adapter"]["kiro"]["projections"]["hook-body"]["target"] = {
            "repo": "tools/hooks/<name>.{sh,py}",
            "user": ".kiro/hooks/<name>.{sh,py}",
            "global": "/etc/hooks/",
        }
        errors = validate(skeleton, _load_adapter_schema())
        self.assertTrue(errors, "schema accepted target with non-{repo,user} key")

    def test_refuses_target_of_wrong_type(self) -> None:
        from agentbundle.build.validate import validate

        skeleton = _v03_skeleton()
        skeleton["adapter"]["kiro"]["projections"]["hook-body"]["target"] = 42
        errors = validate(skeleton, _load_adapter_schema())
        self.assertTrue(errors, "schema accepted integer target")


class ScopeConditionalModeSchemaTests(unittest.TestCase):
    def test_accepts_bare_string_mode(self) -> None:
        from agentbundle.build.validate import validate

        # hook-body uses bare-string mode by default; validates against schema.
        errors = validate(_v03_skeleton(), _load_adapter_schema())
        self.assertEqual(errors, [], f"v0.3 skeleton rejected: {errors}")

    def test_accepts_scope_map_mode_with_known_modes(self) -> None:
        from agentbundle.build.validate import validate

        skeleton = _v03_skeleton()
        skeleton["adapter"]["kiro"]["projections"]["hook-wiring"]["mode"] = {
            "repo": "merge-json",
            "user": "user-merge-json",
        }
        errors = validate(skeleton, _load_adapter_schema())
        self.assertEqual(errors, [], f"scope-map mode rejected: {errors}")

    def test_refuses_unknown_mode_in_bare_string(self) -> None:
        from agentbundle.build.validate import validate

        skeleton = _v03_skeleton()
        skeleton["adapter"]["kiro"]["projections"]["hook-body"]["mode"] = "not-a-real-mode"
        errors = validate(skeleton, _load_adapter_schema())
        self.assertTrue(errors, "schema accepted unknown bare-string mode")

    def test_refuses_unknown_mode_in_scope_map(self) -> None:
        from agentbundle.build.validate import validate

        skeleton = _v03_skeleton()
        skeleton["adapter"]["kiro"]["projections"]["hook-wiring"]["mode"] = {
            "repo": "merge-json",
            "user": "fictional-mode",
        }
        errors = validate(skeleton, _load_adapter_schema())
        self.assertTrue(errors, "schema accepted unknown mode under scope-map.user")


class AgentEventVocabularySchemaTests(unittest.TestCase):
    def test_accepts_list_of_strings(self) -> None:
        from agentbundle.build.validate import validate

        skeleton = _v03_skeleton()
        skeleton["adapter"]["kiro"]["projections"]["hook-wiring"][
            "agent-event-vocabulary"
        ] = ["one", "two", "three"]
        errors = validate(skeleton, _load_adapter_schema())
        self.assertEqual(errors, [], f"valid vocabulary rejected: {errors}")

    def test_refuses_non_string_event(self) -> None:
        from agentbundle.build.validate import validate

        skeleton = _v03_skeleton()
        skeleton["adapter"]["kiro"]["projections"]["hook-wiring"][
            "agent-event-vocabulary"
        ] = ["agentSpawn", 42]
        errors = validate(skeleton, _load_adapter_schema())
        self.assertTrue(errors, "schema accepted non-string event")

    def test_refuses_non_array(self) -> None:
        from agentbundle.build.validate import validate

        skeleton = _v03_skeleton()
        skeleton["adapter"]["kiro"]["projections"]["hook-wiring"][
            "agent-event-vocabulary"
        ] = "agentSpawn"
        errors = validate(skeleton, _load_adapter_schema())
        self.assertTrue(errors, "schema accepted string instead of array")

    def test_refuses_empty_vocabulary(self) -> None:
        """A `merge-into-agent-json` projection without any event vocabulary
        would let any wiring TOML's event keys through `validate` — defeating
        the per-adapter vocabulary gate the field exists to enforce."""
        from agentbundle.build.validate import validate

        skeleton = _v03_skeleton()
        skeleton["adapter"]["kiro"]["projections"]["hook-wiring"][
            "agent-event-vocabulary"
        ] = []
        errors = validate(skeleton, _load_adapter_schema())
        self.assertTrue(errors, "schema accepted empty agent-event-vocabulary")


# ---------------------------------------------------------------------------
# AC5 — pack.install user-scope-hooks boolean
# ---------------------------------------------------------------------------


class PackInstallUserScopeHooksTests(unittest.TestCase):
    def test_accepts_true(self) -> None:
        from agentbundle.build.validate import validate

        instance = _parse_pack(
            """
[pack]
name = "demo"
version = "0.1.0"

[pack.adapter-contract]
version = "0.3"

[pack.install]
default-scope = "user"
allowed-scopes = ["user"]
user-scope-hooks = true
"""
        )
        errors = validate(instance, _load_pack_schema())
        self.assertEqual(errors, [], f"user-scope-hooks=true rejected: {errors}")

    def test_accepts_false(self) -> None:
        from agentbundle.build.validate import validate

        instance = _parse_pack(
            """
[pack]
name = "demo"
version = "0.1.0"

[pack.adapter-contract]
version = "0.3"

[pack.install]
default-scope = "user"
allowed-scopes = ["user"]
user-scope-hooks = false
"""
        )
        errors = validate(instance, _load_pack_schema())
        self.assertEqual(errors, [], f"user-scope-hooks=false rejected: {errors}")

    def test_refuses_non_boolean(self) -> None:
        from agentbundle.build.validate import validate

        for bad in ("yes", 1, ["true"]):
            with self.subTest(value=bad):
                instance = {
                    "pack": {
                        "name": "demo",
                        "version": "0.1.0",
                        "adapter-contract": {"version": "0.3"},
                        "install": {
                            "default-scope": "user",
                            "allowed-scopes": ["user"],
                            "user-scope-hooks": bad,
                        },
                    }
                }
                errors = validate(instance, _load_pack_schema())
                self.assertTrue(
                    errors,
                    f"schema accepted user-scope-hooks={bad!r}",
                )

    def test_absent_is_accepted(self) -> None:
        """AC5: absent value is accepted (defaults to false at consumption time)."""
        from agentbundle.build.validate import validate

        instance = _parse_pack(
            """
[pack]
name = "demo"
version = "0.1.0"

[pack.adapter-contract]
version = "0.3"

[pack.install]
default-scope = "repo"
allowed-scopes = ["repo"]
"""
        )
        errors = validate(instance, _load_pack_schema())
        self.assertEqual(
            errors,
            [],
            f"v0.3 pack without user-scope-hooks rejected: {errors}",
        )

    def test_v03_pack_accepted(self) -> None:
        """The v0.2 install-required invariant extends to v0.3."""
        from agentbundle.build.validate import validate

        instance = _parse_pack(
            """
[pack]
name = "demo"
version = "0.1.0"

[pack.adapter-contract]
version = "0.3"

[pack.install]
default-scope = "repo"
allowed-scopes = ["repo"]
"""
        )
        errors = validate(instance, _load_pack_schema())
        self.assertEqual(errors, [], f"v0.3 pack with install rejected: {errors}")

    def test_v03_pack_without_install_refused(self) -> None:
        """The v0.2 invariant — install required when adapter-contract.version is current — applies to v0.3."""
        from agentbundle.build.validate import validate

        instance = _parse_pack(
            """
[pack]
name = "demo"
version = "0.1.0"

[pack.adapter-contract]
version = "0.3"
"""
        )
        errors = validate(instance, _load_pack_schema())
        self.assertTrue(errors, "v0.3 pack without [pack.install] was accepted")


# ---------------------------------------------------------------------------
# Cross-cutting: zipapp-bundled and dev-checkout copies must be byte-identical.
# ---------------------------------------------------------------------------


class DualFormDriftTests(unittest.TestCase):
    """Path B (additive) keeps the legacy `[[adapter.X.projection]]` array
    entry alongside the new `[adapter.X.projections.<primitive>]` table for
    the same primitive — claude-code hook-body, claude-code hook-wiring,
    kiro hook-body. If T5/T6/T7 evolve one form's `mode` without updating
    the other, the pipeline silently diverges. Pin the invariant here.
    """

    def _repo_mode(self, entry: dict) -> str:
        """A v0.3 table entry's repo-scope mode — bare string or `.repo`."""
        mode = entry["mode"]
        return mode["repo"] if isinstance(mode, dict) else mode

    def test_legacy_and_v0_3_agree_on_repo_mode(self) -> None:
        contract = _load_contract()
        for adapter_name, adapter_block in contract["adapter"].items():
            array_entries = {
                p["primitive"]: p for p in adapter_block.get("projection", [])
            }
            for primitive, table_entry in adapter_block.get("projections", {}).items():
                if primitive not in array_entries:
                    continue  # primitive only declared in new form (e.g. kiro hook-wiring)
                with self.subTest(adapter=adapter_name, primitive=primitive):
                    legacy_mode = array_entries[primitive]["mode"]
                    table_mode = self._repo_mode(table_entry)
                    self.assertEqual(
                        legacy_mode,
                        table_mode,
                        f"({adapter_name}, {primitive}): legacy array mode {legacy_mode!r} "
                        f"diverges from v0.3 table repo mode {table_mode!r}",
                    )


class AdapterBlockCoverageTests(unittest.TestCase):
    """An adapter block declaring neither `projection` nor `projections` would
    project nothing — yet the relaxed v0.3 schema (no `required: [projection]`)
    accepts it. Catch this at the test layer until the stdlib validator gains
    an `anyOf` or equivalent. AC1 implicitly requires every reference adapter
    to cover all five primitives via one form or the other."""

    def test_every_adapter_declares_at_least_one_form(self) -> None:
        contract = _load_contract()
        for adapter_name, adapter_block in contract["adapter"].items():
            with self.subTest(adapter=adapter_name):
                has_array = bool(adapter_block.get("projection"))
                has_table = bool(adapter_block.get("projections"))
                self.assertTrue(
                    has_array or has_table,
                    f"adapter {adapter_name!r} declares neither `projection` array "
                    "nor `projections` table — nothing would project",
                )


class BundledCopiesMatchTests(unittest.TestCase):
    """`_data/` ships in the zipapp; `docs/contracts/` is the dev-checkout
    fallback per build/main.py § resolution chain. Both are excluded from the
    self-host drift check, so we assert identity here to catch divergence."""

    def _data_dir(self) -> Path:
        return REPO_ROOT / "packages" / "agentbundle" / "agentbundle" / "_data"

    def test_adapter_toml_copies_match(self) -> None:
        a = (self._data_dir() / "adapter.toml").read_bytes()
        b = CONTRACT_PATH.read_bytes()
        self.assertEqual(a, b, "_data/adapter.toml and docs/contracts/adapter.toml differ")

    def test_adapter_schema_copies_match(self) -> None:
        a = (self._data_dir() / "adapter.schema.json").read_bytes()
        b = ADAPTER_SCHEMA_PATH.read_bytes()
        self.assertEqual(a, b, "_data/adapter.schema.json and docs/contracts/adapter.schema.json differ")

    def test_pack_schema_copies_match(self) -> None:
        a = (self._data_dir() / "pack.schema.json").read_bytes()
        b = PACK_SCHEMA_PATH.read_bytes()
        self.assertEqual(a, b, "_data/pack.schema.json and docs/contracts/pack.schema.json differ")

    def test_plugin_manifest_schema_copies_match(self) -> None:
        a = (self._data_dir() / "plugin-manifest.schema.json").read_bytes()
        b = PLUGIN_MANIFEST_SCHEMA_PATH.read_bytes()
        self.assertEqual(
            a, b,
            "_data/plugin-manifest.schema.json and docs/contracts/plugin-manifest.schema.json differ",
        )

    def test_plugin_manifest_derived_schema_copies_match(self) -> None:
        a = (self._data_dir() / "plugin-manifest.derived.schema.json").read_bytes()
        b = PLUGIN_MANIFEST_DERIVED_SCHEMA_PATH.read_bytes()
        self.assertEqual(
            a, b,
            "_data/plugin-manifest.derived.schema.json and "
            "docs/contracts/plugin-manifest.derived.schema.json differ",
        )

    def test_install_marker_template_copies_match(self) -> None:
        """AC20 / Blocker-1 drift gate: _data/install-marker.py and
        templates/install-marker.py must be byte-identical.

        ``_read_install_marker_template`` (build/main.py) reads _data/ first
        (zipapp path) and falls back to templates/ in a dev checkout.
        Both copies are excluded from the self-host drift check, so this
        test is the only mechanical gate keeping them in sync.
        """
        templates_dir = REPO_ROOT / "packages" / "agentbundle" / "templates"
        a = (self._data_dir() / "install-marker.py").read_bytes()
        b = (templates_dir / "install-marker.py").read_bytes()
        self.assertEqual(
            a, b,
            "_data/install-marker.py and templates/install-marker.py differ; "
            "run 'cp templates/install-marker.py agentbundle/_data/install-marker.py' "
            "to re-sync",
        )


if __name__ == "__main__":
    unittest.main()
