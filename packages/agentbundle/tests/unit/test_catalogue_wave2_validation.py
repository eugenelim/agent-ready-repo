"""Stub: Wave 2 integration-validation tests (Task 2 TDD).

All tests in this file fail (ImportError at collection) until
_step_integration_validation is added to verify.py. A passing test suite here
is Task 2's Done-when criterion.
"""

from __future__ import annotations

from pathlib import Path

import pytest

# This import fails until Task 2 adds _step_integration_validation — that IS the red stub.
from agentbundle.catalogue_tooling.verify import _step_integration_validation, verify_catalogue

# ── Fixtures / helpers ────────────────────────────────────────────────────────


def _write_pack_toml(pack_dir: Path, name: str, integrations: list[dict] | None = None) -> None:
    lines = [f'[pack]\nname = "{name}"\nversion = "1.0.0"']
    if integrations:
        for entry in integrations:
            lines.append("\n[[pack.integrations]]")
            for k, v in entry.items():
                if isinstance(v, list):
                    formatted = "[" + ", ".join(f'"{x}"' for x in v) + "]"
                    lines.append(f"{k} = {formatted}")
                else:
                    lines.append(f'{k} = "{v}"')
    (pack_dir / "pack.toml").write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def _make_pack(root: Path, name: str, integrations: list[dict] | None = None) -> Path:
    pack_dir = root / "packs" / name
    pack_dir.mkdir(parents=True)
    _write_pack_toml(pack_dir, name, integrations)
    return pack_dir


def _add_skill(pack_dir: Path, name: str) -> None:
    skill_dir = pack_dir / ".apm" / "skills" / name
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text("# s\n", encoding="utf-8", newline="\n")


def _add_agent(pack_dir: Path, name: str) -> None:
    agents_dir = pack_dir / ".apm" / "agents"
    agents_dir.mkdir(parents=True, exist_ok=True)
    (agents_dir / f"{name}.md").write_text("# a\n", encoding="utf-8", newline="\n")


def _add_command(pack_dir: Path, name: str) -> None:
    cmds_dir = pack_dir / ".apm" / "commands"
    cmds_dir.mkdir(parents=True, exist_ok=True)
    (cmds_dir / f"{name}.md").write_text("# cmd\n", encoding="utf-8", newline="\n")


def _add_hook(pack_dir: Path, name: str, ext: str = ".py") -> None:
    hooks_dir = pack_dir / ".apm" / "hooks"
    hooks_dir.mkdir(parents=True, exist_ok=True)
    (hooks_dir / f"{name}{ext}").write_text("# hook\n", encoding="utf-8", newline="\n")


def _valid_entry(**overrides) -> dict:
    base = {
        "id": "test-int",
        "pack": "other-pack",
        "kind": "input",
        "role": "Test role",
        "consumers": ["skill:consumer-skill"],
        "providers": ["skill:provider-skill"],
        "when": "When active.",
        "purpose": "For testing.",
        "fallback": "Skips gracefully.",
    }
    return {**base, **overrides}


# ── Tests ─────────────────────────────────────────────────────────────────────


# STUB: AC5 — duplicate integration IDs within one pack error
def test_verify_duplicate_integration_id_errors(tmp_path):
    pack_dir = _make_pack(tmp_path, "declaring", [
        _valid_entry(id="dupe"),
        _valid_entry(id="dupe"),
    ])
    _add_skill(pack_dir, "consumer-skill")
    result = _step_integration_validation(tmp_path, None, None, tmp_path)
    assert any("CAT-V-019" in d.code and "duplicate" in d.message.lower() for d in result)


# STUB: AC7 — skill consumer ref missing in declaring pack errors
def test_verify_consumer_skill_ref_missing_errors(tmp_path):
    _make_pack(tmp_path, "declaring", [_valid_entry()])
    # Intentionally NOT creating .apm/skills/consumer-skill
    result = _step_integration_validation(tmp_path, None, None, tmp_path)
    assert any("CAT-V-019" in d.code for d in result)


# STUB: AC7 — agent consumer ref missing in declaring pack errors
def test_verify_consumer_agent_ref_missing_errors(tmp_path):
    entry = _valid_entry(consumers=["agent:my-agent"])
    _make_pack(tmp_path, "declaring", [entry])
    # Intentionally NOT creating .apm/agents/my-agent.md
    result = _step_integration_validation(tmp_path, None, None, tmp_path)
    assert any("CAT-V-019" in d.code for d in result)


# STUB: AC7 — skill consumer ref resolved when file exists → passes
def test_verify_consumer_skill_ref_present_passes(tmp_path):
    pack_dir = _make_pack(tmp_path, "declaring", [_valid_entry(pack="absent-pack")])
    _add_skill(pack_dir, "consumer-skill")
    # "absent-pack" is not in the catalogue — AC11 says that's ok
    result = _step_integration_validation(tmp_path, None, None, tmp_path)
    assert result == []


# STUB: AC9 — self-target (entry.pack == declaring pack name) errors
def test_verify_self_target_errors(tmp_path):
    entry = _valid_entry(pack="declaring")  # targets itself
    pack_dir = _make_pack(tmp_path, "declaring", [entry])
    _add_skill(pack_dir, "consumer-skill")
    result = _step_integration_validation(tmp_path, None, None, tmp_path)
    assert any("CAT-V-019" in d.code and "self" in d.message.lower() for d in result)


# STUB: AC10 (accept) — valid semver ranges pass
@pytest.mark.parametrize("v", [
    "^1.0.0",
    ">=2.0.0 <3.0.0",
    "1.2.3",
    "~1.2",
    "1.0.0 - 2.0.0",
    "1.0.0 || 2.0.0",
])
def test_verify_valid_version_range_passes(tmp_path, v):
    entry = _valid_entry(version=v, pack="absent-pack")
    pack_dir = _make_pack(tmp_path, "declaring", [entry])
    _add_skill(pack_dir, "consumer-skill")
    result = _step_integration_validation(tmp_path, None, None, tmp_path)
    version_errors = [
        d for d in result if "CAT-V-019" in d.code and "version" in d.message.lower()
    ]
    assert version_errors == []


# STUB: AC10 (reject) — invalid version strings error
@pytest.mark.parametrize("v", ["latest", "@1", "not-a-version"])
def test_verify_invalid_version_range_errors(tmp_path, v):
    entry = _valid_entry(version=v, pack="absent-pack")
    pack_dir = _make_pack(tmp_path, "declaring", [entry])
    _add_skill(pack_dir, "consumer-skill")
    result = _step_integration_validation(tmp_path, None, None, tmp_path)
    assert any("CAT-V-019" in d.code and "version" in d.message.lower() for d in result)


# STUB: AC11 — absent target pack does NOT produce an error
def test_verify_absent_target_pack_passes(tmp_path):
    # "other-pack" doesn't exist in this catalogue
    pack_dir = _make_pack(tmp_path, "declaring", [_valid_entry(pack="other-pack")])
    _add_skill(pack_dir, "consumer-skill")
    result = _step_integration_validation(tmp_path, None, None, tmp_path)
    assert result == []


# STUB: AC12 — provider ref missing when target is present in catalogue errors
def test_verify_present_target_provider_ref_missing_errors(tmp_path):
    entry = _valid_entry(pack="target-pack")
    declaring_dir = _make_pack(tmp_path, "declaring", [entry])
    _add_skill(declaring_dir, "consumer-skill")
    # Create target-pack but WITHOUT the declared provider skill "provider-skill"
    _make_pack(tmp_path, "target-pack", [])
    result = _step_integration_validation(tmp_path, None, None, tmp_path)
    assert any("CAT-V-019" in d.code for d in result)


# STUB: happy path — all refs resolve, target present with provider → passes
def test_verify_valid_integration_full_resolution_passes(tmp_path):
    entry = _valid_entry(pack="target-pack")
    declaring_dir = _make_pack(tmp_path, "declaring", [entry])
    _add_skill(declaring_dir, "consumer-skill")
    target_dir = _make_pack(tmp_path, "target-pack", [])
    _add_skill(target_dir, "provider-skill")
    result = _step_integration_validation(tmp_path, None, None, tmp_path)
    assert result == []


# STUB: AC7 — command consumer ref missing in declaring pack errors
def test_verify_consumer_command_ref_missing_errors(tmp_path):
    entry = _valid_entry(consumers=["command:my-cmd"])
    _make_pack(tmp_path, "declaring", [entry])
    # Intentionally NOT creating .apm/commands/my-cmd.md
    result = _step_integration_validation(tmp_path, None, None, tmp_path)
    assert any("CAT-V-019" in d.code for d in result)


# STUB: AC7 — command consumer ref present passes
def test_verify_consumer_command_ref_present_passes(tmp_path):
    entry = _valid_entry(consumers=["command:my-cmd"], pack="absent-pack")
    pack_dir = _make_pack(tmp_path, "declaring", [entry])
    _add_command(pack_dir, "my-cmd")
    result = _step_integration_validation(tmp_path, None, None, tmp_path)
    assert result == []


# STUB: AC7 — hook consumer ref missing (hooks dir absent) errors
def test_verify_consumer_hook_ref_missing_errors(tmp_path):
    entry = _valid_entry(consumers=["hook:post-install"])
    _make_pack(tmp_path, "declaring", [entry])
    # .apm/hooks/ dir does not exist
    result = _step_integration_validation(tmp_path, None, None, tmp_path)
    assert any("CAT-V-019" in d.code for d in result)


# STUB: AC7 — hook consumer ref present passes
def test_verify_consumer_hook_ref_present_passes(tmp_path):
    entry = _valid_entry(consumers=["hook:post-install"], pack="absent-pack")
    pack_dir = _make_pack(tmp_path, "declaring", [entry])
    _add_hook(pack_dir, "post-install", ".py")
    result = _step_integration_validation(tmp_path, None, None, tmp_path)
    assert result == []


# STUB: AC5 scope — two distinct packs may use the same id (seen_ids resets per pack)
def test_verify_same_id_in_different_packs_passes(tmp_path):
    # Both packs declare an integration with id="shared-id" — this is VALID (AC5 scopes to pack)
    entry = _valid_entry(id="shared-id", pack="absent-pack")
    pack_a = _make_pack(tmp_path, "pack-a", [entry])
    _add_skill(pack_a, "consumer-skill")
    pack_b = _make_pack(tmp_path, "pack-b", [entry])
    _add_skill(pack_b, "consumer-skill")
    result = _step_integration_validation(tmp_path, None, None, tmp_path)
    assert result == []


# STUB: no integrations → passes immediately
def test_verify_no_integrations_passes(tmp_path):
    _make_pack(tmp_path, "declaring", [])
    result = _step_integration_validation(tmp_path, None, None, tmp_path)
    assert result == []


# ── Pipeline-level tests (verify_catalogue wiring) ────────────────────────────
# These tests drive verify_catalogue() directly to confirm step 19 is wired
# into the pipeline. Deleting or un-registering the step would leave the unit
# tests above green while breaking these — the two test layers complement each other.


def test_pipeline_self_target_produces_cat_v_019(tmp_path):
    """verify_catalogue reports CAT-V-019 for a self-target integration."""
    entry = _valid_entry(pack="declaring")  # self-target
    pack_dir = _make_pack(tmp_path, "declaring", [entry])
    _add_skill(pack_dir, "consumer-skill")
    result = verify_catalogue(tmp_path)
    assert not result.ok
    codes = [d.code for d in result.diagnostics]
    assert any("CAT-V-019" in c for c in codes), codes


def test_pipeline_duplicate_id_produces_cat_v_019(tmp_path):
    """verify_catalogue reports CAT-V-019 for duplicate integration IDs in one pack."""
    pack_dir = _make_pack(tmp_path, "declaring", [
        _valid_entry(id="dupe", pack="absent-pack"),
        _valid_entry(id="dupe", pack="absent-pack"),
    ])
    _add_skill(pack_dir, "consumer-skill")
    result = verify_catalogue(tmp_path)
    assert not result.ok
    codes = [d.code for d in result.diagnostics]
    assert any("CAT-V-019" in c for c in codes), codes
