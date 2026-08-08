"""Tests for agentbundle.catalogue_tooling.initialise_self_hosted."""

from __future__ import annotations

from pathlib import Path

import pytest
from agentbundle.catalogue_tooling.initialise_self_hosted import (
    _VENDORED_ENGINE_EXCLUDE,
    _VENDORED_PACK_EXCLUDE,
    SelfHostedInitConfig,
    SelfHostOwnershipState,
    _collect_dir_bytes,
    init_self_hosted,
    select_packs,
    validate_fields,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_source(tmp_path: Path, packs: list[str] | None = None) -> Path:
    """Create a minimal valid source catalogue tree."""
    source = tmp_path / "source"
    source.mkdir()
    (source / "catalogue.toml").write_text(
        '[catalogue]\nname = "upstream-catalogue"\ndisplay_name = "Upstream Catalogue"\n'
        'description = "The upstream."\n',
        encoding="utf-8",
    )
    packs_dir = source / "packs"
    packs_dir.mkdir()
    for name in packs or ["core", "governance-extras"]:
        p = packs_dir / name
        p.mkdir()
        (p / "pack.toml").write_text(
            f'[pack]\nname = "{name}"\nversion = "0.1.0"\n', encoding="utf-8"
        )
    (source / "profiles").mkdir()
    (source / "profiles" / "default.toml").write_text(
        '[profile]\nname = "default"\n', encoding="utf-8"
    )
    return source


def _base_cfg(tmp_path: Path, source: Path, **kwargs) -> SelfHostedInitConfig:
    defaults: dict = {
        "target": tmp_path / "target",
        "source": source,
        "name": "my-catalogue",
        "display_name": "My Catalogue",
        "description": "A test catalogue.",
        "owner_name": "Test Owner",
        "owner_email": "owner@example.com",
        "preferred_adapter": "claude-code",
    }
    defaults.update(kwargs)
    return SelfHostedInitConfig(**defaults)


# ---------------------------------------------------------------------------
# select_packs()
# ---------------------------------------------------------------------------

def test_select_packs_all(tmp_path: Path) -> None:
    source = _make_source(tmp_path, packs=["core", "governance-extras"])
    packs = select_packs(source, None)
    assert "core" in packs
    assert "governance-extras" in packs
    assert "catalogue-curation" not in packs


def test_select_packs_excludes_tooling(tmp_path: Path) -> None:
    source = _make_source(tmp_path, packs=["core"])
    (source / "packs" / "catalogue-curation").mkdir()
    packs = select_packs(source, None)
    assert "catalogue-curation" not in packs


def test_select_packs_explicit_filter(tmp_path: Path) -> None:
    source = _make_source(tmp_path, packs=["core", "governance-extras"])
    packs = select_packs(source, ["core"])
    assert packs == ["core"]


def test_select_packs_missing_explicit_raises(tmp_path: Path) -> None:
    source = _make_source(tmp_path, packs=["core"])
    with pytest.raises(ValueError, match="not found in source"):
        select_packs(source, ["nonexistent-pack"])


def test_select_packs_no_packs_dir(tmp_path: Path) -> None:
    source = tmp_path / "empty-source"
    source.mkdir()
    packs = select_packs(source, None)
    assert packs == []


# ---------------------------------------------------------------------------
# validate_fields()
# ---------------------------------------------------------------------------

def test_validate_fields_valid(tmp_path: Path) -> None:
    source = _make_source(tmp_path)
    cfg = _base_cfg(tmp_path, source)
    assert validate_fields(cfg) == []


def test_validate_fields_bad_name(tmp_path: Path) -> None:
    source = _make_source(tmp_path)
    cfg = _base_cfg(tmp_path, source, name="bad name!")
    errors = validate_fields(cfg)
    assert any("name" in e for e in errors)


def test_validate_fields_bad_url(tmp_path: Path) -> None:
    source = _make_source(tmp_path)
    cfg = _base_cfg(tmp_path, source, repository_url="not-a-url")
    errors = validate_fields(cfg)
    assert any("repository-url" in e for e in errors)


def test_validate_fields_bad_email(tmp_path: Path) -> None:
    source = _make_source(tmp_path)
    cfg = _base_cfg(tmp_path, source, owner_email="not-an-email")
    errors = validate_fields(cfg)
    assert any("owner-email" in e for e in errors)


def test_validate_fields_valid_url_and_email(tmp_path: Path) -> None:
    source = _make_source(tmp_path)
    cfg = _base_cfg(
        tmp_path, source,
        repository_url="https://example.com/repo",
        owner_email="user@example.com",
    )
    assert validate_fields(cfg) == []


# ---------------------------------------------------------------------------
# init_self_hosted() — external mode
# ---------------------------------------------------------------------------

def test_init_self_hosted_external_creates_packs(tmp_path: Path) -> None:
    source = _make_source(tmp_path)
    cfg = _base_cfg(tmp_path, source)
    result = init_self_hosted(cfg)
    assert result.ok, result.diagnostics
    assert (cfg.target / "packs" / "core" / "pack.toml").exists()
    assert (cfg.target / "catalogue.toml").exists()


def test_init_self_hosted_external_excludes_catalogue_curation(tmp_path: Path) -> None:
    source = _make_source(tmp_path, packs=["core"])
    (source / "packs" / "catalogue-curation").mkdir()
    (source / "packs" / "catalogue-curation" / "pack.toml").write_text(
        '[pack]\nname = "catalogue-curation"\nversion = "0.2.0"\n', encoding="utf-8"
    )
    cfg = _base_cfg(tmp_path, source)
    result = init_self_hosted(cfg)
    assert result.ok
    assert not (cfg.target / "packs" / "catalogue-curation").exists()


def test_init_self_hosted_writes_catalogue_toml_with_target_identity(tmp_path: Path) -> None:
    source = _make_source(tmp_path)
    cfg = _base_cfg(tmp_path, source, name="my-org-catalogue")
    result = init_self_hosted(cfg)
    assert result.ok
    content = (cfg.target / "catalogue.toml").read_text(encoding="utf-8")
    assert "my-org-catalogue" in content


def test_init_self_hosted_dry_run_no_files(tmp_path: Path) -> None:
    source = _make_source(tmp_path)
    cfg = _base_cfg(tmp_path, source, dry_run=True)
    result = init_self_hosted(cfg)
    assert result.dry_run is True
    assert not (cfg.target / "catalogue.toml").exists()
    assert result.files_written  # plan still populated


def test_init_self_hosted_invalid_source(tmp_path: Path) -> None:
    cfg = _base_cfg(tmp_path, tmp_path / "nonexistent")
    result = init_self_hosted(cfg)
    assert not result.ok
    assert result.diagnostics


def test_init_self_hosted_white_label_scrubs_source_name(tmp_path: Path) -> None:
    source = _make_source(tmp_path)
    # Plant the source catalogue name in a pack file.
    pack_readme = source / "packs" / "core" / "README.md"
    pack_readme.write_text(
        "This pack is part of upstream-catalogue.", encoding="utf-8"
    )
    cfg = _base_cfg(tmp_path, source, attribution="white-label")
    result = init_self_hosted(cfg)
    assert result.ok
    copied_readme = cfg.target / "packs" / "core" / "README.md"
    content = copied_readme.read_text(encoding="utf-8")
    assert "upstream-catalogue" not in content


def test_init_self_hosted_writes_ownership_state(tmp_path: Path) -> None:
    source = _make_source(tmp_path)
    cfg = _base_cfg(tmp_path, source)
    result = init_self_hosted(cfg)
    assert result.ok
    state_path = cfg.target / ".agentbundle" / "self-host-state.json"
    assert state_path.exists()
    import json
    state = json.loads(state_path.read_text(encoding="utf-8"))
    # Schema 2: managed_paths is list of {path, sha256} dicts.
    assert state["schema_version"] == "2"
    assert isinstance(state["managed_paths"], list)
    assert all(
        isinstance(e, dict) and "path" in e and "sha256" in e
        for e in state["managed_paths"]
    )


def test_init_self_hosted_profiles_copied(tmp_path: Path) -> None:
    source = _make_source(tmp_path)
    cfg = _base_cfg(tmp_path, source)
    result = init_self_hosted(cfg)
    assert result.ok
    assert (cfg.target / "profiles" / "default.toml").exists()


# ---------------------------------------------------------------------------
# init_self_hosted() — vendored mode
# ---------------------------------------------------------------------------

def test_init_self_hosted_vendored_copies_tooling(tmp_path: Path) -> None:
    source = _make_source(tmp_path)
    # Add agentbundle source tree to source.
    agentbundle_src = source / "packages" / "agentbundle" / "agentbundle"
    agentbundle_src.mkdir(parents=True)
    (agentbundle_src / "__init__.py").write_text("", encoding="utf-8")
    # Add catalogue-curation to source packs.
    cc = source / "packs" / "catalogue-curation"
    cc.mkdir()
    (cc / "pack.toml").write_text(
        '[pack]\nname = "catalogue-curation"\nversion = "0.2.0"\n', encoding="utf-8"
    )

    cfg = _base_cfg(tmp_path, source, tooling="vendored")
    result = init_self_hosted(cfg)
    assert result.ok, result.diagnostics
    assert (cfg.target / ".agentbundle" / "tooling" / "agentbundle").is_dir()
    assert (cfg.target / ".agentbundle" / "tooling" / "packs" / "catalogue-curation").is_dir()


def test_init_self_hosted_vendored_missing_agentbundle_diagnostic(tmp_path: Path) -> None:
    # B3: non-self-hosted source refused for vendored mode.
    source = _make_source(tmp_path)  # no packages/agentbundle/
    cfg = _base_cfg(tmp_path, source, tooling="vendored")
    result = init_self_hosted(cfg)
    assert not result.ok
    assert any("agentbundle" in d for d in result.diagnostics)


# ---------------------------------------------------------------------------
# SelfHostOwnershipState
# ---------------------------------------------------------------------------

def test_ownership_state_to_dict() -> None:
    # Schema 2: managed_paths is list of {path, sha256} dicts.
    state = SelfHostOwnershipState(
        managed_paths=[
            {"path": "packs/core/pack.toml", "sha256": "abc123"},
            {"path": "catalogue.toml", "sha256": "def456"},
        ]
    )
    d = state.to_dict()
    assert d["schema_version"] == "2"
    paths = [e["path"] for e in d["managed_paths"]]
    assert "catalogue.toml" in paths
    assert "packs/core/pack.toml" in paths


# ---------------------------------------------------------------------------
# next_steps
# ---------------------------------------------------------------------------

def test_init_self_hosted_next_steps_external(tmp_path: Path) -> None:
    source = _make_source(tmp_path)
    cfg = _base_cfg(tmp_path, source, tooling="external")
    result = init_self_hosted(cfg)
    assert result.ok
    assert result.next_steps
    assert any("catalogue-curation" in s for s in result.next_steps)


def test_init_self_hosted_to_dict(tmp_path: Path) -> None:
    source = _make_source(tmp_path)
    cfg = _base_cfg(tmp_path, source, dry_run=True)
    result = init_self_hosted(cfg)
    d = result.to_dict()
    assert d["operation"] == "self-hosted-init"
    assert "ok" in d
    assert "files_written" in d


# ---------------------------------------------------------------------------
# Security / correctness fixes (adversarial-reviewer findings F3, F4, F15, F16)
# ---------------------------------------------------------------------------

def test_validate_fields_rejects_credential_url(tmp_path: Path) -> None:
    source = _make_source(tmp_path)
    cfg = _base_cfg(
        tmp_path, source,
        repository_url="https://user:pass@example.com/my-catalogue",
    )
    errors = validate_fields(cfg)
    assert any("credential" in e for e in errors)


def test_validate_fields_accepts_clean_url(tmp_path: Path) -> None:
    source = _make_source(tmp_path)
    cfg = _base_cfg(
        tmp_path, source,
        repository_url="https://example.com/my-catalogue",
    )
    errors = validate_fields(cfg)
    assert not any("credential" in e for e in errors)


def test_generate_catalogue_toml_escapes_quotes(tmp_path: Path) -> None:
    from agentbundle.catalogue_tooling.initialise_self_hosted import (
        _generate_catalogue_toml,
    )
    source = _make_source(tmp_path)
    cfg = _base_cfg(
        tmp_path, source,
        display_name='My "Special" Catalogue',
        description='Has a "quoted" description',
        owner_name='O\'Reilly "Test"',
    )
    toml_content = _generate_catalogue_toml(cfg)
    import tomllib
    parsed = tomllib.loads(toml_content)
    assert parsed["catalogue"]["display_name"] == 'My "Special" Catalogue'
    assert '"quoted"' in parsed["catalogue"]["description"]


def test_leak_check_blocks_writes_on_attribution_violation(tmp_path: Path) -> None:
    """Leak check must fire before any target write; no files written on violation.

    Uses attribution=attributed so verify() does not strip anchors — the
    upstream catalogue name placed outside the attribution surface surfaces
    as a leak, and the init must fail with no files written to target.
    """
    source = _make_source(tmp_path)
    # Plant source catalogue name in a non-attribution-surface pack file.
    (source / "packs" / "core" / "README.md").write_text(
        "upstream-catalogue upstream-catalogue upstream-catalogue\n",
        encoding="utf-8",
    )
    cfg = _base_cfg(tmp_path, source, attribution="attributed")
    result = init_self_hosted(cfg)

    # The leak check is a pre-write preflight — target must be empty regardless.
    assert not result.ok
    assert result.violations
    assert not cfg.target.exists() or not list(cfg.target.iterdir())


def test_transform_covers_description_anchor(tmp_path: Path) -> None:
    from agentbundle.catalogue_tooling.initialise_self_hosted import (
        _build_anchors,
        _transform_text,
    )
    source_meta = {
        "catalogue": {
            "name": "upstream-name",
            "description": "The upstream description text here",
        }
    }
    anchors = _build_anchors(source_meta)
    assert "description" in anchors

    cfg = _base_cfg(tmp_path, tmp_path / "source", description="Our org description")
    result = _transform_text(
        "The upstream description text here is in this file.", anchors, cfg
    )
    assert "Our org description" in result
    assert "upstream description" not in result


# ---------------------------------------------------------------------------
# Phase 2 — B3: SelfHostedSource + vendored source validation
# ---------------------------------------------------------------------------

def test_resolve_source_returns_source_for_valid_dir(tmp_path: Path) -> None:
    from agentbundle.catalogue_tooling.initialise_self_hosted import resolve_source
    source = _make_source(tmp_path)
    sh_source, err = resolve_source(source, tooling="external")
    assert err is None
    assert sh_source is not None
    assert sh_source.name == "upstream-catalogue"


def test_resolve_source_error_for_missing_dir(tmp_path: Path) -> None:
    from agentbundle.catalogue_tooling.initialise_self_hosted import resolve_source
    sh_source, err = resolve_source(tmp_path / "nonexistent", tooling="external")
    assert err is not None
    assert sh_source is None


def test_resolve_source_vendored_refuses_missing_agentbundle(tmp_path: Path) -> None:
    from agentbundle.catalogue_tooling.initialise_self_hosted import resolve_source
    source = _make_source(tmp_path)  # no packages/agentbundle/
    sh_source, err = resolve_source(source, tooling="vendored")
    assert err is not None
    assert "vendored" in err or "agentbundle" in err
    assert sh_source is None


def test_selfhostsource_fields_accessible() -> None:
    from agentbundle.catalogue_tooling.initialise_self_hosted import SelfHostedSource
    src = SelfHostedSource(
        name="my-cat",
        display_name="My Cat",
        release="1.0.0",
        archive_uri="https://example.com/archive.tar.gz",
        sha256="abc123",
        revision="main",
    )
    assert src.name == "my-cat"
    assert src.archive_uri == "https://example.com/archive.tar.gz"
    assert src.revision == "main"


def test_validate_fields_rejects_credential_archive_uri(tmp_path: Path) -> None:
    source = _make_source(tmp_path)
    cfg = _base_cfg(
        tmp_path, source,
        archive_uri="https://user:token@example.com/archive.tar.gz",
    )
    errors = validate_fields(cfg)
    assert any("credential" in e for e in errors)


def test_validate_fields_accepts_clean_archive_uri(tmp_path: Path) -> None:
    source = _make_source(tmp_path)
    cfg = _base_cfg(
        tmp_path, source,
        archive_uri="https://example.com/archive.tar.gz",
    )
    errors = validate_fields(cfg)
    assert not any("credential" in e for e in errors)


# ---------------------------------------------------------------------------
# Phase 2 — B5: reuse conflict classifier + atomic commit
# ---------------------------------------------------------------------------

def test_conflict_detected_for_non_owned_existing_file(tmp_path: Path) -> None:
    """A new file that already exists with different content causes ok=False."""
    source = _make_source(tmp_path)
    target = tmp_path / "target"
    target.mkdir()
    # Pre-create a file with different content (not owned, so will CONFLICT).
    (target / "packs").mkdir()
    (target / "packs" / "core").mkdir()
    (target / "packs" / "core" / "pack.toml").write_text("conflict content", encoding="utf-8")
    cfg = _base_cfg(tmp_path, source, target=target)
    result = init_self_hosted(cfg)
    assert not result.ok


def test_owned_file_overwritten_on_rerun(tmp_path: Path) -> None:
    """Files owned by a previous run are overwritten (no conflict) on re-run."""
    source = _make_source(tmp_path)
    cfg = _base_cfg(tmp_path, source)
    result1 = init_self_hosted(cfg)
    assert result1.ok

    # Modify source pack.toml to simulate an upstream update.
    (source / "packs" / "core" / "pack.toml").write_text(
        '[pack]\nname = "core"\nversion = "0.2.0"\n', encoding="utf-8"
    )
    result2 = init_self_hosted(cfg)
    assert result2.ok  # owned path → overwrite, no conflict
    content = (cfg.target / "packs" / "core" / "pack.toml").read_text(encoding="utf-8")
    assert "0.2.0" in content


# ---------------------------------------------------------------------------
# Phase 2 — B6: vendored [catalogue.tooling] section
# ---------------------------------------------------------------------------

def test_generate_catalogue_toml_vendored_has_tooling_section(tmp_path: Path) -> None:
    import tomllib

    from agentbundle.catalogue_tooling.initialise_self_hosted import _generate_catalogue_toml
    source = _make_source(tmp_path)
    cfg = _base_cfg(tmp_path, source, tooling="vendored")
    cfg = cfg.__class__(
        target=cfg.target, source=cfg.source, tooling="vendored",
        name="my-cat", display_name="My Cat", description="Desc",
        owner_name="Owner", owner_email="o@example.com",
        preferred_adapter="claude-code",
    )
    content = _generate_catalogue_toml(cfg)
    parsed = tomllib.loads(content)
    assert "tooling" in parsed.get("catalogue", {})
    tooling = parsed["catalogue"]["tooling"]
    assert ".agentbundle/tooling/packs" in tooling["pack-roots"]
    assert "catalogue-curation" in tooling["self-host-packs"]
    assert "claude-code" in tooling["adapters"]


def test_vendored_catalogue_toml_parseable(tmp_path: Path) -> None:
    """After vendored init, catalogue.toml is valid TOML with [catalogue.tooling]."""
    source = _make_source(tmp_path)
    agentbundle_src = source / "packages" / "agentbundle" / "agentbundle"
    agentbundle_src.mkdir(parents=True)
    (agentbundle_src / "__init__.py").write_text("", encoding="utf-8")
    cc = source / "packs" / "catalogue-curation"
    cc.mkdir()
    (cc / "pack.toml").write_text(
        '[pack]\nname = "catalogue-curation"\nversion = "0.2.0"\n', encoding="utf-8"
    )
    cfg = _base_cfg(tmp_path, source, tooling="vendored")
    result = init_self_hosted(cfg)
    assert result.ok, result.diagnostics
    import tomllib
    cat_toml = (cfg.target / "catalogue.toml").read_text(encoding="utf-8")
    parsed = tomllib.loads(cat_toml)
    assert "tooling" in parsed.get("catalogue", {})


# ---------------------------------------------------------------------------
# Phase 2 — B7: export-catalogue refusal + curation planning
# ---------------------------------------------------------------------------

def test_source_with_export_catalogue_refused(tmp_path: Path) -> None:
    source = _make_source(tmp_path)
    # Plant outdated export-catalogue skill.
    export_cat = (
        source / "packs" / "catalogue-curation"
        / ".apm" / "skills" / "export-catalogue"
    )
    export_cat.mkdir(parents=True)
    (export_cat / "SKILL.md").write_text("# export-catalogue\n", encoding="utf-8")
    cfg = _base_cfg(tmp_path, source)
    result = init_self_hosted(cfg)
    assert not result.ok
    assert any("export-catalogue" in d for d in result.diagnostics)


def test_external_next_steps_has_install_command(tmp_path: Path) -> None:
    source = _make_source(tmp_path)
    cfg = _base_cfg(tmp_path, source, tooling="external")
    result = init_self_hosted(cfg)
    assert result.ok
    # B7: structured curation install command per adapter.
    assert any("agentbundle install catalogue-curation" in s for s in result.next_steps)
    assert any("--scope repo" in s for s in result.next_steps)


def test_external_next_steps_per_adapter(tmp_path: Path) -> None:
    source = _make_source(tmp_path)
    cfg = _base_cfg(tmp_path, source, tooling="external", adapters=["claude-code", "kiro-ide"])
    result = init_self_hosted(cfg)
    assert result.ok
    # One install command per adapter.
    claude_steps = [s for s in result.next_steps if "claude-code" in s and "install" in s]
    kiro_steps = [s for s in result.next_steps if "kiro-ide" in s and "install" in s]
    assert claude_steps
    assert kiro_steps


# ---------------------------------------------------------------------------
# Phase 2 — B9: ownership state enrichment + removal logic
# ---------------------------------------------------------------------------

def test_ownership_state_schema2_fields(tmp_path: Path) -> None:
    import json
    source = _make_source(tmp_path)
    cfg = _base_cfg(tmp_path, source)
    result = init_self_hosted(cfg)
    assert result.ok
    state = json.loads(
        (cfg.target / ".agentbundle" / "self-host-state.json").read_text(encoding="utf-8")
    )
    assert state["schema_version"] == "2"
    assert "adapters" in state
    assert "managed_target_path" in state
    assert "source_pack_identity" in state
    assert "source_root_kind" in state


def test_stale_path_removed_on_rerun(tmp_path: Path) -> None:
    """A file from a previous run not in the new plan is removed."""
    source = _make_source(tmp_path, packs=["core", "governance-extras"])
    cfg = _base_cfg(tmp_path, source)
    result1 = init_self_hosted(cfg)
    assert result1.ok
    assert (cfg.target / "packs" / "governance-extras" / "pack.toml").exists()

    # Second run: only core pack (governance-extras removed from source).
    src2_parent = tmp_path / "src2parent"
    src2_parent.mkdir()
    source2 = _make_source(src2_parent, packs=["core"])
    cfg2 = cfg.__class__(
        target=cfg.target, source=source2,
        name=cfg.name, display_name=cfg.display_name,
        description=cfg.description, owner_name=cfg.owner_name,
        owner_email=cfg.owner_email, preferred_adapter=cfg.preferred_adapter,
    )
    result2 = init_self_hosted(cfg2)
    assert result2.ok
    assert not (cfg.target / "packs" / "governance-extras" / "pack.toml").exists()
    assert (cfg.target / "packs" / "core" / "pack.toml").exists()


def test_user_modified_file_not_removed_on_rerun(tmp_path: Path) -> None:
    """A stale file modified by the user (sha256 mismatch) is skipped with a warning."""
    import json  # noqa: F401

    source = _make_source(tmp_path, packs=["core", "governance-extras"])
    cfg = _base_cfg(tmp_path, source)
    result1 = init_self_hosted(cfg)
    assert result1.ok

    # User modifies governance-extras/pack.toml.
    gov_path = cfg.target / "packs" / "governance-extras" / "pack.toml"
    gov_path.write_text(
        "[pack]\nname = \"governance-extras\"\nversion = \"user-edit\"\n",
        encoding="utf-8",
    )

    # Second run: only core (governance-extras is stale but user-modified).
    src2_parent = tmp_path / "src2parent"
    src2_parent.mkdir()
    source2 = _make_source(src2_parent, packs=["core"])
    cfg2 = cfg.__class__(
        target=cfg.target, source=source2,
        name=cfg.name, display_name=cfg.display_name,
        description=cfg.description, owner_name=cfg.owner_name,
        owner_email=cfg.owner_email, preferred_adapter=cfg.preferred_adapter,
    )
    result2 = init_self_hosted(cfg2)
    assert result2.ok
    assert gov_path.exists()  # user-modified → skipped
    assert any("modified" in d or "sha256" in d for d in result2.diagnostics)


def test_path_confinement_against_crafted_state(tmp_path: Path) -> None:
    """A crafted state entry with ../escape cannot escape target on removal."""
    import json
    source = _make_source(tmp_path)
    cfg = _base_cfg(tmp_path, source)
    result = init_self_hosted(cfg)
    assert result.ok

    # Craft the state file with a path traversal entry.
    state_path = cfg.target / ".agentbundle" / "self-host-state.json"
    state = json.loads(state_path.read_text(encoding="utf-8"))
    state["managed_paths"].append({"path": "../../escape.txt", "sha256": "fake"})
    state_path.write_text(json.dumps(state), encoding="utf-8")

    # Create the target file outside the target.
    escape_file = tmp_path / "escape.txt"
    escape_file.write_text("should not be removed", encoding="utf-8")

    # Re-run: only core (stale path is the traversal entry).
    result2 = init_self_hosted(cfg)
    assert result2.ok
    assert escape_file.exists()  # path confinement: traversal rejected


def test_external_skill_survives_self_hosting(tmp_path: Path) -> None:
    """Externally installed skills outside ownership state are not removed."""
    source = _make_source(tmp_path)
    cfg = _base_cfg(tmp_path, source)
    result1 = init_self_hosted(cfg)
    assert result1.ok

    # Install an external skill (not in ownership state).
    external_skill = cfg.target / ".claude" / "skills" / "my-custom-skill" / "SKILL.md"
    external_skill.parent.mkdir(parents=True, exist_ok=True)
    external_skill.write_text("# My Custom Skill\n", encoding="utf-8")

    # Re-run the same init (no changes).
    result2 = init_self_hosted(cfg)
    assert result2.ok
    assert external_skill.exists()  # external skill not removed


# ---------------------------------------------------------------------------
# Phase 2 — B12: JSON output field completeness
# ---------------------------------------------------------------------------

def test_to_dict_contains_all_phase2_fields(tmp_path: Path) -> None:
    source = _make_source(tmp_path)
    cfg = _base_cfg(tmp_path, source, dry_run=True)
    result = init_self_hosted(cfg)
    d = result.to_dict()
    assert d["preset"] == "self-hosted"
    assert "tooling_mode" in d
    assert "attribution_mode" in d
    assert "selected_packs" in d
    assert "selected_profiles" in d
    assert "selected_adapters" in d
    assert "field_collection_mode" in d
    assert "identity_replacements" in d
    assert "leak_scan_result" in d
    assert isinstance(d["leak_scan_result"], dict)
    assert "ok" in d["leak_scan_result"]
    # B12 source provenance and summary
    assert "source" in d
    assert d["source"] is not None
    assert "name" in d["source"]
    assert "summary" in d
    assert isinstance(d["summary"], str)


# ---------------------------------------------------------------------------
# RFC-0082: the vendored payload carries no test content
# ---------------------------------------------------------------------------
#
# `catalogue init --preset self-hosted --tooling vendored` copies the engine's
# source into the adopter's tree, where the emitted instruction tells them to
# `pip install -e` it. That makes it wheel-class (ADR-0075 D3), so it carries no
# test content — while the adopter's *own* catalogue keeps its tests, which
# ADR-0071 explicitly wants.


def _synthetic_source(root: Path) -> Path:
    """A source catalogue with test content on both sides of the boundary."""
    eng = root / "packages" / "agentbundle"
    (eng / "agentbundle").mkdir(parents=True)
    (eng / "agentbundle" / "cli.py").write_text("x\n", encoding="utf-8")
    (eng / "tests" / "build_pipeline").mkdir(parents=True)
    (eng / "tests" / "build_pipeline" / "test_x.py").write_text("x\n", encoding="utf-8")
    (eng / "conftest.py").write_text("x\n", encoding="utf-8")
    # Build residue a maintainer's working tree always carries. The .pyc embeds
    # an absolute build path — a real username — which AGENTS.md § Privacy
    # forbids committing, and .pytest_cache lists engine test node IDs.
    (eng / "agentbundle" / "__pycache__").mkdir()
    (eng / "agentbundle" / "__pycache__" / "cli.cpython-311.pyc").write_bytes(b"\x00/Users/someone/x")
    (eng / ".pytest_cache" / "v").mkdir(parents=True)
    (eng / ".pytest_cache" / "v" / "nodeids").write_text("[]\n", encoding="utf-8")
    (eng / "agentbundle.egg-info").mkdir()
    (eng / "agentbundle.egg-info" / "SOURCES.txt").write_text("x\n", encoding="utf-8")

    pack = root / "packs" / "catalogue-curation"
    (pack / ".apm").mkdir(parents=True)
    (pack / ".apm" / "s.md").write_text("x\n", encoding="utf-8")
    (pack / "tests").mkdir()
    (pack / "tests" / "test_y.py").write_text("x\n", encoding="utf-8")
    return root


def test_vendored_engine_carries_no_tests(tmp_path):
    src = _synthetic_source(tmp_path)
    fb: dict[str, bytes] = {}
    fk: dict[str, str] = {}
    _collect_dir_bytes(
        src / "packages" / "agentbundle",
        ".agentbundle/tooling/agentbundle",
        fb, fk, kind="vendored", exclude=_VENDORED_ENGINE_EXCLUDE,
    )
    assert any("cli.py" in k for k in fb), "engine code was dropped"
    leaked = [k for k in fb if "/tests/" in k or k.endswith("conftest.py")]
    assert not leaked, f"vendored engine carries test content: {leaked}"


def test_vendored_curation_pack_carries_no_tests(tmp_path):
    src = _synthetic_source(tmp_path)
    fb: dict[str, bytes] = {}
    fk: dict[str, str] = {}
    _collect_dir_bytes(
        src / "packs" / "catalogue-curation",
        ".agentbundle/tooling/packs/catalogue-curation",
        fb, fk, kind="vendored", exclude=_VENDORED_PACK_EXCLUDE,
    )
    assert any("s.md" in k for k in fb)
    assert not [k for k in fb if "/tests/" in k]


def test_adopter_packs_still_carry_tests(tmp_path):
    """The regression a careless fix causes. ADR-0071 wants catalogue archives
    to carry pack tests, so the non-vendored callers must keep copying them —
    which is why `exclude` defaults to empty and is passed only at the two
    vendored call sites."""
    src = _synthetic_source(tmp_path)
    fb: dict[str, bytes] = {}
    fk: dict[str, str] = {}
    _collect_dir_bytes(
        src / "packs" / "catalogue-curation", "packs/catalogue-curation",
        fb, fk, kind="pack",
    )
    assert [k for k in fb if "/tests/" in k], "the adopter's own pack lost its tests"


def test_init_self_hosted_vendored_emits_no_test_content(tmp_path: Path) -> None:
    """AC5 driven through the real entry point, not through `_collect_dir_bytes`.

    The unit tests above pass `exclude=` themselves, so they assert the routine
    plus the constants and would survive the wiring at the two vendored call
    sites being deleted. This one runs `init_self_hosted` end to end against a
    source that carries test content on both sides of the boundary, so removing
    either `exclude=` kwarg turns it red.
    """
    source = _make_source(tmp_path)
    eng = source / "packages" / "agentbundle"
    (eng / "agentbundle").mkdir(parents=True)
    (eng / "agentbundle" / "__init__.py").write_text("", encoding="utf-8")
    (eng / "tests" / "build_pipeline").mkdir(parents=True)
    (eng / "tests" / "build_pipeline" / "test_x.py").write_text("x\n", encoding="utf-8")
    (eng / "conftest.py").write_text("x\n", encoding="utf-8")

    cc = source / "packs" / "catalogue-curation"
    cc.mkdir()
    (cc / "pack.toml").write_text(
        '[pack]\nname = "catalogue-curation"\nversion = "0.2.0"\n', encoding="utf-8"
    )
    (cc / "tests").mkdir()
    (cc / "tests" / "test_y.py").write_text("x\n", encoding="utf-8")

    # ...and test content on the two non-vendored copy paths, which must
    # survive: ADR-0071 wants catalogue archives to carry tests.
    own_tests = source / "packs" / "core" / "tests"
    own_tests.mkdir()
    (own_tests / "test_own.py").write_text("x\n", encoding="utf-8")
    guide_tests = source / "guides" / "_shared" / "tests"
    guide_tests.mkdir(parents=True)
    (guide_tests / "test_g.py").write_text("x\n", encoding="utf-8")

    cfg = _base_cfg(tmp_path, source, tooling="vendored", guides="selected")
    result = init_self_hosted(cfg)
    assert result.ok, result.diagnostics

    vendored = cfg.target / ".agentbundle" / "tooling"
    assert vendored.is_dir(), "vendored tooling was not written"
    residue = {"__pycache__", ".pytest_cache", "build", "dist"}
    leaked = [
        p.relative_to(cfg.target).as_posix()
        for p in vendored.rglob("*")
        if p.is_file()
        and (
            "tests" in p.parts
            or p.name == "conftest.py"
            or residue & set(p.parts)
            or p.suffix in {".pyc", ".pyo"}
            or any(part.endswith(".egg-info") for part in p.parts)
        )
    ]
    assert not leaked, f"vendored payload carries test content or build residue: {leaked}"

    # ...while the adopter's own catalogue keeps its pack tests (ADR-0071).
    own = cfg.target / "packs" / "core" / "tests" / "test_own.py"
    assert own.exists(), "the adopter's own pack lost its tests"
    guided = cfg.target / "guides" / "_shared" / "tests" / "test_g.py"
    assert guided.exists(), "the guides call site stopped carrying test content"
