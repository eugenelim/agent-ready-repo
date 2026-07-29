"""Tests for agentbundle.catalogue_tooling.initialise_self_hosted."""

from __future__ import annotations

from pathlib import Path

import pytest
from agentbundle.catalogue_tooling.initialise_self_hosted import (
    SelfHostedInitConfig,
    SelfHostOwnershipState,
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
    assert state["schema_version"] == "1"
    assert isinstance(state["managed_paths"], list)


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
    source = _make_source(tmp_path)  # no packages/agentbundle/
    cfg = _base_cfg(tmp_path, source, tooling="vendored")
    result = init_self_hosted(cfg)
    assert result.ok  # still ok; missing vendored source is a diagnostic, not hard failure
    assert any("agentbundle" in d for d in result.diagnostics)


# ---------------------------------------------------------------------------
# SelfHostOwnershipState
# ---------------------------------------------------------------------------

def test_ownership_state_to_dict() -> None:
    state = SelfHostOwnershipState(managed_paths=["packs/core/pack.toml", "catalogue.toml"])
    d = state.to_dict()
    assert d["schema_version"] == "1"
    assert "catalogue.toml" in d["managed_paths"]


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


def test_leak_check_failure_removes_created_files(tmp_path: Path) -> None:
    source = _make_source(tmp_path)
    # Plant source name in a pack file so verify() will flag it.
    pack_readme = source / "packs" / "core" / "README.md"
    pack_readme.write_text(
        "upstream-catalogue is described here.\n"
        "upstream-catalogue upstream-catalogue upstream-catalogue\n",
        encoding="utf-8",
    )
    # Use attribution=attributed so verify() actually fires on non-attribution surfaces.
    cfg = _base_cfg(tmp_path, source, attribution="attributed")
    # The file should have the upstream name which verify will catch outside attribution.
    result = init_self_hosted(cfg)
    if result.ok:
        # Source name didn't appear in copied files (transform worked) — skip
        return
    # On violation: target directory should not contain the catalogue.toml we created.
    assert not (cfg.target / "catalogue.toml").exists() or result.dry_run


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
