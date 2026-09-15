"""Tests for agentbundle.catalogue_tooling.initialise_self_hosted."""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import tomllib
from pathlib import Path

import pytest
from agentbundle.catalogue_tooling.initialise_self_hosted import (
    _VENDORED_ENGINE_EXCLUDE,
    _VENDORED_PACK_EXCLUDE,
    SelfHostedInitConfig,
    SelfHostOwnershipState,
    SelfHostPin,
    _collect_dir_bytes,
    _generate_catalogue_toml,
    _transform_recipe_string,
    init_self_hosted,
    select_packs,
    validate_fields,
)
from agentbundle.scaffold import scaffold_root

PACKAGE_ROOT = Path(__file__).resolve().parents[2]

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_source(tmp_path: Path, packs: list[str] | None = None) -> Path:
    """Create a minimal valid source catalogue tree."""
    source = tmp_path / "source"
    source.mkdir()
    (source / "catalogue.toml").write_text(
        '[catalogue]\nname = "upstream-catalogue"\ndisplay_name = "Upstream Catalogue"\n'
        'description = "The upstream."\n'
        'maintainers = [{name = "Upstream Maintainer", email = "upstream@example.com"}]\n'
        '[catalogue.links]\n'
        'homepage = "https://upstream.example.com"\n'
        'repository = "https://upstream.example.com/catalogue"\n',
        encoding="utf-8",
    )
    packs_dir = source / "packs"
    packs_dir.mkdir()
    for name in packs or ["core", "governance-extras"]:
        p = packs_dir / name
        p.mkdir()
        (p / "pack.toml").write_text(
            f'[pack]\nname = "{name}"\nversion = "0.1.0"\n'
            'readme = "README.md"\nlicense = "Apache-2.0"\n'
            'categories = ["testing"]\nkeywords = ["testing"]\n'
            'maintainers = [{name = "Example Maintainer"}]\n'
            '[pack.links]\nrepository = "https://example.com/catalogue"\n',
            encoding="utf-8",
        )
        (p / "README.md").write_text(f"# {name}\n", encoding="utf-8")
    (source / "profiles").mkdir()
    (source / "profiles" / "default.toml").write_text(
        '[profile]\nname = "default"\n', encoding="utf-8"
    )
    shutil.copytree(
        scaffold_root() / "tests" / "conformance",
        source / "tests" / "conformance",
    )
    roster = source / "tests" / "roster"
    roster.mkdir()
    (roster / "sentinel.txt").write_text("must not ship\n", encoding="utf-8")
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


def _assert_materialised_conformance_passes(
    target: Path, *, tooling: str = "external"
) -> None:
    """Execute the exact conformance suite copied into a self-hosted target."""
    env = os.environ.copy()
    if tooling == "vendored":
        vendored_project = target / ".agentbundle" / "tooling" / "agentbundle"
        current = env.get("PYTHONPATH")
        env["PYTHONPATH"] = (
            str(vendored_project)
            if not current
            else str(vendored_project) + os.pathsep + current
        )
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/conformance", "-q"],
        cwd=target,
        env=env,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def _run_self_hosted_cli(
    source: Path, target: Path, *, tooling: str
) -> subprocess.CompletedProcess[str]:
    """Invoke the public self-hosted init route from the source package."""
    env = os.environ.copy()
    current = env.get("PYTHONPATH")
    env["PYTHONPATH"] = (
        str(PACKAGE_ROOT)
        if not current
        else str(PACKAGE_ROOT) + os.pathsep + current
    )
    return subprocess.run(
        [
            sys.executable,
            "-m",
            "agentbundle",
            "catalogue",
            "init",
            str(target),
            "--preset",
            "self-hosted",
            "--tooling",
            tooling,
            "--source",
            str(source),
            "--name",
            "cli-catalogue",
            "--display-name",
            "CLI Catalogue",
            "--description",
            "A CLI lifecycle fixture.",
            "--owner-name",
            "Example Maintainer",
            "--owner-email",
            "maintainer@example.com",
            "--preferred-adapter",
            "claude-code",
            "--guides",
            "none",
        ],
        cwd=PACKAGE_ROOT,
        env=env,
        capture_output=True,
        text=True,
    )


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
    assert (cfg.target / "tests" / "conformance" / "test_pack_metadata.py").exists()
    assert not (cfg.target / "tests" / "roster").exists()
    _assert_materialised_conformance_passes(cfg.target)


def test_init_self_hosted_refuses_hard_linked_conformance(tmp_path: Path) -> None:
    """Self-hosted init rejects conformance bytes linked from outside source."""
    source = _make_source(tmp_path)
    conformance = source / "tests" / "conformance" / "test_pack_metadata.py"
    conformance.unlink()
    outside = tmp_path / "outside.py"
    outside.write_text("def test_outside(): pass\n", encoding="utf-8")
    try:
        os.link(outside, conformance)
    except OSError:
        pytest.skip("st_nlink hard-link detection is POSIX-only")

    result = init_self_hosted(_base_cfg(tmp_path, source))

    assert not result.ok
    assert any("hard link not allowed" in item for item in result.diagnostics)


def test_init_self_hosted_prunes_conformance_build_residue(tmp_path: Path) -> None:
    """Materialization never copies cache bytes that embed checkout paths."""
    source = _make_source(tmp_path)
    cache = source / "tests" / "conformance" / "__pycache__"
    cache.mkdir()
    (cache / "test_pack_metadata.cpython-313.pyc").write_bytes(
        b"/Users/example/private-checkout"
    )

    cfg = _base_cfg(tmp_path, source)
    result = init_self_hosted(cfg)

    assert result.ok, result.diagnostics
    assert not (cfg.target / "tests" / "conformance" / "__pycache__").exists()


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
    # Schema 3 retains schema 2's managed_paths shape.
    assert state["schema_version"] == "3"
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
    # Add a real importable agentbundle runtime tree to the source.
    agentbundle_src = source / "packages" / "agentbundle" / "agentbundle"
    agentbundle_src.parent.mkdir(parents=True)
    shutil.copytree(PACKAGE_ROOT / "agentbundle", agentbundle_src)
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
    assert (cfg.target / "tests" / "conformance" / "test_pack_metadata.py").exists()
    assert not (cfg.target / "tests" / "roster").exists()
    _assert_materialised_conformance_passes(cfg.target, tooling="vendored")


@pytest.mark.parametrize("tooling", ["external", "vendored"])
def test_self_hosted_init_cli_materialises_runnable_conformance(
    tmp_path: Path, tooling: str
) -> None:
    """Both public self-hosted CLI modes deliver their runnable suite."""
    source = _make_source(tmp_path)
    if tooling == "vendored":
        agentbundle_src = source / "packages" / "agentbundle" / "agentbundle"
        agentbundle_src.parent.mkdir(parents=True)
        shutil.copytree(PACKAGE_ROOT / "agentbundle", agentbundle_src)
        curation = source / "packs" / "catalogue-curation"
        curation.mkdir()
        (curation / "pack.toml").write_text(
            '[pack]\nname = "catalogue-curation"\nversion = "0.2.0"\n',
            encoding="utf-8",
        )
    target = tmp_path / f"target-{tooling}"

    result = _run_self_hosted_cli(source, target, tooling=tooling)

    assert result.returncode == 0, result.stdout + result.stderr
    _assert_materialised_conformance_passes(target, tooling=tooling)


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
    # Schema 3 retains schema 2's managed_paths shape.
    state = SelfHostOwnershipState(
        managed_paths=[
            {"path": "packs/core/pack.toml", "sha256": "abc123"},
            {"path": "catalogue.toml", "sha256": "def456"},
        ]
    )
    d = state.to_dict()
    assert d["schema_version"] == "3"
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

def test_ownership_state_schema3_fields(tmp_path: Path) -> None:
    import json
    source = _make_source(tmp_path)
    cfg = _base_cfg(tmp_path, source)
    result = init_self_hosted(cfg)
    assert result.ok
    state = json.loads(
        (cfg.target / ".agentbundle" / "self-host-state.json").read_text(encoding="utf-8")
    )
    assert state["schema_version"] == "3"
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
    # The shipped build-pipeline package. Its name collides with setuptools'
    # build *output*, so a name-at-any-depth prune removes it and leaves an
    # engine that cannot import. Present here so that over-pruning reddens.
    (eng / "agentbundle" / "build" / "adapters").mkdir(parents=True)
    (eng / "agentbundle" / "build" / "self_host.py").write_text("x\n", encoding="utf-8")
    (eng / "agentbundle" / "build" / "adapters" / "cursor.py").write_text("x\n", encoding="utf-8")
    # ...and setuptools output at the collect root, which must go.
    (eng / "build" / "lib").mkdir(parents=True)
    (eng / "build" / "lib" / "stale.py").write_text("x\n", encoding="utf-8")
    (eng / "tests" / "build_pipeline").mkdir(parents=True)
    (eng / "tests" / "build_pipeline" / "test_x.py").write_text("x\n", encoding="utf-8")
    (eng / "conftest.py").write_text("x\n", encoding="utf-8")
    # Build residue a maintainer's working tree always carries. The .pyc embeds
    # an absolute build path — a real username — which AGENTS.md § Privacy
    # forbids committing, and .pytest_cache lists engine test node IDs.
    (eng / "agentbundle" / "__pycache__").mkdir()
    (eng / "agentbundle" / "__pycache__" / "cli.cpython-311.pyc").write_bytes(b"\x00/Users/someone/x")
    (eng / "agentbundle" / "__pycache__" / "cli.cpython-311.pyo").write_bytes(b"\x00/Users/someone/x")
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
    assert any(k.endswith("agentbundle/build/self_host.py") for k in fb), (
        "the shipped agentbundle/build/ package was pruned — the vendored "
        "engine would not import"
    )
    assert any(k.endswith("build/adapters/cursor.py") for k in fb)
    assert not [k for k in fb if "/build/lib/" in k], (
        "setuptools build output at the collect root was vendored"
    )
    # The residue half. Without these the prune could be disabled outright and
    # the suite would stay green — and this is the half that writes a real
    # username into an adopter's repo via a .pyc's embedded build path.
    residue = [
        k
        for k in fb
        if "__pycache__" in k
        or ".pytest_cache" in k
        or ".egg-info" in k
        or k.endswith((".pyc", ".pyo"))
    ]
    assert not residue, f"vendored engine carries build residue: {residue}"
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
    # The shipped build-pipeline package — must survive the residue prune.
    (eng / "agentbundle" / "build").mkdir()
    (eng / "agentbundle" / "build" / "self_host.py").write_text("x\n", encoding="utf-8")
    # Residue, so this test's residue clauses are live rather than inert.
    (eng / "agentbundle" / "__pycache__").mkdir()
    (eng / "agentbundle" / "__pycache__" / "cli.cpython-311.pyc").write_bytes(b"\x00")
    (eng / "agentbundle.egg-info").mkdir()
    (eng / "agentbundle.egg-info" / "SOURCES.txt").write_text("x\n", encoding="utf-8")
    # ...and setuptools output at the collect root — must not.
    (eng / "build" / "lib").mkdir(parents=True)
    (eng / "build" / "lib" / "stale.py").write_text("x\n", encoding="utf-8")
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
    # `build`/`dist` are checked at the vendored ROOT only. Matching them at any
    # depth is the rule that deleted the shipped `agentbundle/build/` package —
    # asserting it here would re-encode the bug as the contract.
    any_depth = {"__pycache__", ".pytest_cache"}
    leaked = []
    for f in vendored.rglob("*"):
        if not f.is_file():
            continue
        parts = f.relative_to(vendored).parts
        if (
            "tests" in parts
            or f.name == "conftest.py"
            or any_depth & set(parts)
            or f.suffix in {".pyc", ".pyo"}
            or any(part.endswith(".egg-info") for part in parts)
            # root-relative: <vendored>/agentbundle/{build,dist}/ is setuptools
            # output; <vendored>/agentbundle/agentbundle/build/ is the package.
            or parts[:2] in {("agentbundle", "build"), ("agentbundle", "dist")}
        ):
            leaked.append(f.relative_to(cfg.target).as_posix())
    assert not leaked, f"vendored payload carries test content or build residue: {leaked}"

    # ...and the shipped build-pipeline package survived.
    shipped = vendored / "agentbundle" / "agentbundle" / "build" / "self_host.py"
    assert shipped.exists(), "the shipped agentbundle/build/ package was pruned"

    # ...while the adopter's own catalogue keeps its pack tests (ADR-0071).
    own = cfg.target / "packs" / "core" / "tests" / "test_own.py"
    assert own.exists(), "the adopter's own pack lost its tests"
    guided = cfg.target / "guides" / "_shared" / "tests" / "test_g.py"
    assert guided.exists(), "the guides call site stopped carrying test content"


# ---------------------------------------------------------------------------
# credbroker package source travels with the credential-brokers pack
#
# `user_libs` resolves its source of truth at `packs_dir.parent /
# packages/credbroker/credbroker`. A derived catalogue that omits it reaches
# the documented whole-package-retirement branch by accident: both consumers of
# `compute_projections` become silent no-ops, so `catalogue self-host` writes no
# floor and `check_drift` reports clean over nothing.
# ---------------------------------------------------------------------------


def _add_credbroker_source(source: Path) -> None:
    """Add a minimal `packages/credbroker/` project to a source tree."""
    pkg_root = source / "packages" / "credbroker"
    (pkg_root / "credbroker").mkdir(parents=True)
    (pkg_root / "pyproject.toml").write_text(
        '[project]\nname = "credbroker"\nversion = "0.1.0"\n', encoding="utf-8"
    )
    (pkg_root / "credbroker" / "__init__.py").write_text(
        "from ._core import resolve\n\n__all__ = ['resolve']\n", encoding="utf-8"
    )
    (pkg_root / "credbroker" / "_core.py").write_text(
        "def resolve(name: str) -> str:\n    return name\n", encoding="utf-8"
    )
    # Test content, to prove the derived catalogue does not carry it.
    (pkg_root / "tests" / "unit").mkdir(parents=True)
    (pkg_root / "tests" / "unit" / "test_core.py").write_text(
        "def test_x() -> None:\n    assert True\n", encoding="utf-8"
    )


def _with_credbroker_pack(tmp_path: Path) -> Path:
    """A source catalogue carrying the credential-brokers pack and its source."""
    source = _make_source(tmp_path, packs=["core", "credential-brokers"])
    _add_credbroker_source(source)
    # The pack-vendored copy the build pipeline projects alongside the floor.
    vendored = source / "packs" / "credential-brokers" / ".apm" / "user-libs"
    (vendored / "credbroker").mkdir(parents=True)
    for leaf in ("__init__.py", "_core.py"):
        shutil.copyfile(
            source / "packages" / "credbroker" / "credbroker" / leaf,
            vendored / "credbroker" / leaf,
        )
    return source


@pytest.mark.parametrize("tooling", ["external", "vendored"])
def test_credbroker_source_travels_in_both_tooling_modes(
    tmp_path: Path, tooling: str
) -> None:
    """The copy is keyed on the pack, not on --tooling.

    credbroker is a build input resolved by relative path, unlike
    `packages/agentbundle/`, which is an install source and therefore vendored
    to `.agentbundle/tooling/` in vendored mode only.
    """
    source = _with_credbroker_pack(tmp_path)
    if tooling == "vendored":
        # Same shape as test_init_self_hosted_vendored_copies_tooling: the
        # importable runtime tree only, not the engine's own project docs.
        agentbundle_src = source / "packages" / "agentbundle" / "agentbundle"
        agentbundle_src.parent.mkdir(parents=True)
        shutil.copytree(PACKAGE_ROOT / "agentbundle", agentbundle_src)
    cfg = _base_cfg(tmp_path, source, tooling=tooling)
    result = init_self_hosted(cfg)
    assert result.ok, result.diagnostics

    # Exactly the path `user_libs._package_source_dir` resolves.
    landed = cfg.target / "packages" / "credbroker" / "credbroker" / "_core.py"
    assert landed.is_file(), (
        f"credbroker source absent under tooling={tooling}; the user-libs "
        "projection and its drift gate are inert in this derived catalogue"
    )
    assert (
        landed.read_bytes()
        == (source / "packages" / "credbroker" / "credbroker" / "_core.py").read_bytes()
    )
    assert (cfg.target / "packages" / "credbroker" / "pyproject.toml").is_file()
    # It is NOT ALSO vendored as an install source.
    assert not (
        cfg.target / ".agentbundle" / "tooling" / "packages" / "credbroker"
    ).exists()


def test_credbroker_copy_carries_no_test_content(tmp_path: Path) -> None:
    source = _with_credbroker_pack(tmp_path)
    cfg = _base_cfg(tmp_path, source)
    assert init_self_hosted(cfg).ok
    assert not (cfg.target / "packages" / "credbroker" / "tests").exists()


def test_credbroker_source_absent_when_pack_not_selected(tmp_path: Path) -> None:
    """No pack that vendors it, no reason to carry its source."""
    source = _with_credbroker_pack(tmp_path)
    cfg = _base_cfg(tmp_path, source, packs=["core"])
    assert init_self_hosted(cfg).ok
    assert not (cfg.target / "packages" / "credbroker").exists()


def test_derived_catalogue_has_a_live_user_libs_projection(tmp_path: Path) -> None:
    """The defect's actual consequence: the gate resolves sources, not [].

    Asserted against `compute_projections` itself rather than a consequence of
    it, because `[]` is what makes BOTH consumers no-ops.
    """
    from agentbundle.build.user_libs import check_drift, compute_projections

    source = _with_credbroker_pack(tmp_path)
    cfg = _base_cfg(tmp_path, source)
    assert init_self_hosted(cfg).ok

    packs_dir = cfg.target / "packs"
    projections = compute_projections(cfg.target, packs_dir)
    assert projections, "compute_projections returned [] — the gate is silent"
    targets = {p.target for p in projections}
    assert cfg.target / ".agentbundle" / "lib" / "credbroker" / "_core.py" in targets

    # And the gate now *speaks*: the floor staging is not there yet, so a
    # freshly derived catalogue is told to build it rather than told it is clean.
    drifts = check_drift(cfg.target, packs_dir)
    assert any(
        "missing" in d and ".agentbundle/lib/credbroker" in d.replace("\\", "/")
        for d in drifts
    ), drifts


def test_user_libs_projection_is_silent_without_the_package_source(
    tmp_path: Path,
) -> None:
    """Differential control: the previous test passes for the stated reason.

    Removing only `packages/credbroker/` from the derived tree must collapse
    the projection to `[]` and the drift report to clean. Without this, the
    assertions above could hold for some unrelated reason.
    """
    from agentbundle.build.user_libs import check_drift, compute_projections

    source = _with_credbroker_pack(tmp_path)
    cfg = _base_cfg(tmp_path, source)
    assert init_self_hosted(cfg).ok

    shutil.rmtree(cfg.target / "packages" / "credbroker")
    packs_dir = cfg.target / "packs"
    assert compute_projections(cfg.target, packs_dir) == []
    assert check_drift(cfg.target, packs_dir) == []


# ---------------------------------------------------------------------------
# source_pack_identity must not leak upstream identity under white-label
#
# `verify()` allows the upstream catalogue name zero hits anywhere in
# white-label mode, but the leak check runs at step 9 over the planned
# `file_bytes` map and the state file is written at step 13, outside it.
# ---------------------------------------------------------------------------


def _read_state(target: Path) -> dict:
    import json

    return json.loads(
        (target / ".agentbundle" / "self-host-state.json").read_text(encoding="utf-8")
    )


def test_white_label_state_pins_the_derived_name(tmp_path: Path) -> None:
    source = _make_source(tmp_path)
    cfg = _base_cfg(tmp_path, source, attribution="white-label")
    assert init_self_hosted(cfg).ok
    assert _read_state(cfg.target)["source_pack_identity"] == "my-catalogue"


def test_attributed_state_keeps_the_upstream_pin(tmp_path: Path) -> None:
    """Attributed mode makes no anonymity promise; the accurate pin stays."""
    source = _make_source(tmp_path)
    cfg = _base_cfg(tmp_path, source, attribution="attributed")
    assert init_self_hosted(cfg).ok
    assert _read_state(cfg.target)["source_pack_identity"] == "upstream-catalogue"


def test_white_label_target_tree_carries_no_upstream_anchor(tmp_path: Path) -> None:
    """The property, scanned over what actually landed on disk.

    `_verify_bytes_in_tmpdir` scans the planned byte map; this scans the written
    target, which is the surface the adopter commits and ships. It is the only
    form of the check that can see a file written after step 9.
    """
    from agentbundle.catalogue_tooling.identity import verify
    from agentbundle.catalogue_tooling.initialise_self_hosted import _build_anchors

    source = _with_credbroker_pack(tmp_path)
    cfg = _base_cfg(tmp_path, source, attribution="white-label")
    assert init_self_hosted(cfg).ok

    anchors = _build_anchors(
        {
            "catalogue": {
                "name": "upstream-catalogue",
                "display_name": "Upstream Catalogue",
                "description": "The upstream.",
            }
        }
    )
    violations = verify(cfg.target, anchors, mode="white-label")
    assert not violations, [(v.path, v.anchor, v.line) for v in violations]


# ---------------------------------------------------------------------------
# AC-0017 — every value interpolated into the generated catalogue.toml is
# escaped for that sink.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "field,payload",
    [
        ("name", 'my-catalogue"\n[catalogue.links]\nrepository = "https://evil'),
        ("display_name", 'D"\n[catalogue.links]\nrepository = "https://evil'),
        ("description", 'X"\n[catalogue.links]\nrepository = "https://evil'),
        (
            "preferred_adapter",
            'claude-code"\n[catalogue.links]\nrepository = "https://evil',
        ),
        ("repository_url", 'https://x"\n[catalogue.tooling]\nadapters = ["evil'),
        ("owner_name", 'O"\n[catalogue.links]\nrepository = "https://evil'),
        ("owner_email", 'a@b."\n[catalogue.links]\nrepository = "https://evil'),
    ],
)
def test_no_interpolated_value_can_forge_a_catalogue_toml_table(
    tmp_path: Path, field: str, payload: str
) -> None:
    """A recorded value must not be able to open a table of its own.

    The field validators are not the control here: `_URL_RE` and `_EMAIL_RE`
    both admit a double quote, and `preferred_adapter` has no validator at all.
    The escaping at the sink is what holds.
    """
    kwargs = {"name": "my-catalogue"}
    kwargs[field] = payload
    cfg = SelfHostedInitConfig(
        target=tmp_path / "t", source=tmp_path / "s", **kwargs
    )
    parsed = tomllib.loads(_generate_catalogue_toml(cfg))
    assert parsed["catalogue"].get("links", {}).get("repository") != "https://evil"
    assert "tooling" not in parsed["catalogue"]


def test_vendored_adapter_entries_are_escaped(tmp_path: Path) -> None:
    """The adapter list is the fifth raw interpolation site."""
    cfg = SelfHostedInitConfig(
        target=tmp_path / "t",
        source=tmp_path / "s",
        name="my-catalogue",
        tooling="vendored",
        adapters=['claude-code"]\nevil = "yes'],
    )
    parsed = tomllib.loads(_generate_catalogue_toml(cfg))
    assert "evil" not in parsed["catalogue"]["tooling"]


def test_a_benign_value_still_produces_the_expected_tables(tmp_path: Path) -> None:
    """AC-0017's positive clause: escaping must not change a normal document."""
    cfg = SelfHostedInitConfig(
        target=tmp_path / "t",
        source=tmp_path / "s",
        name="my-catalogue",
        display_name="My Catalogue",
        description="A catalogue.",
        owner_name="Owner",
        owner_email="owner@example.com",
        repository_url="https://example.com/mine",
    )
    parsed = tomllib.loads(_generate_catalogue_toml(cfg))
    assert parsed["catalogue"]["name"] == "my-catalogue"
    assert parsed["catalogue"]["links"]["repository"] == "https://example.com/mine"
    assert parsed["catalogue"]["maintainers"][0]["email"] == "owner@example.com"


# ---------------------------------------------------------------------------
# Self-host state schema 3 — write path
# ---------------------------------------------------------------------------


def test_state_is_schema_three_with_both_groups(tmp_path: Path) -> None:
    source = _make_source(tmp_path)
    cfg = SelfHostedInitConfig(
        target=tmp_path / "derived", source=source, name="my-catalogue"
    )

    assert init_self_hosted(cfg).ok
    state = _read_state(cfg.target)

    assert state["schema_version"] == "3"
    assert set(state["recipe"]) == {
        "packs",
        "profiles",
        "guides",
        "attribution",
        "tooling",
        "name",
        "display_name",
        "description",
        "owner_name",
        "owner_email",
        "preferred_adapter",
        "repository_url",
    }
    assert {"source_revision", "archive_sha256", "synced_at"} <= set(
        state["pin"]
    )


def test_bare_run_records_resolved_selections(tmp_path: Path) -> None:
    source = _make_source(tmp_path)
    cfg = SelfHostedInitConfig(
        target=tmp_path / "derived", source=source, name="my-catalogue"
    )

    assert init_self_hosted(cfg).ok
    recipe = _read_state(cfg.target)["recipe"]

    assert recipe["packs"] == ["core", "governance-extras"]
    assert recipe["profiles"] == ["default"]


def test_recipe_mode_fields_are_recorded_verbatim(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = _make_source(tmp_path)
    monkeypatch.setattr(
        "agentbundle.catalogue_tooling.initialise_self_hosted._verify_bytes_in_tmpdir",
        lambda *_args: ([], []),
    )
    metadata_path = source / "catalogue.toml"
    metadata_path.write_text(
        metadata_path.read_text(encoding="utf-8").replace(
            'name = "upstream-catalogue"', 'name = "extern"', 1
        ),
        encoding="utf-8",
    )
    cfg = _base_cfg(
        tmp_path,
        source,
        guides="selected",
        attribution="white-label",
        tooling="external",
    )

    assert init_self_hosted(cfg).ok
    recipe = _read_state(cfg.target)["recipe"]

    for field, expected in {
        "guides": "selected",
        "attribution": "white-label",
        "tooling": "external",
    }.items():
        assert recipe[field] == expected


def test_derived_tree_passes_leak_check_including_state_file(tmp_path: Path) -> None:
    """Use the production anchor builder and verifier over the written tree."""
    from agentbundle.catalogue_tooling.identity import verify
    from agentbundle.catalogue_tooling.initialise_self_hosted import _build_anchors

    source = _make_source(tmp_path)
    cfg = SelfHostedInitConfig(
        target=tmp_path / "derived", source=source, name="my-catalogue"
    )

    assert init_self_hosted(cfg).ok
    anchors = _build_anchors(
        tomllib.loads((source / "catalogue.toml").read_text(encoding="utf-8"))
    )

    assert verify(cfg.target, anchors) == []


def test_attributed_recipe_strings_keep_upstream_identity(tmp_path: Path) -> None:
    """Attributed recipe strings take the same no-transform branch as the tree."""
    source = _make_source(tmp_path)
    cfg = SelfHostedInitConfig(
        target=tmp_path / "derived",
        source=source,
        name="my-catalogue",
        attribution="attributed",
    )

    assert init_self_hosted(cfg).ok

    assert _read_state(cfg.target)["recipe"]["description"] == (
        "A self-hosted catalogue derived from upstream-catalogue."
    )


def test_attributed_recipe_transform_is_a_no_op(tmp_path: Path) -> None:
    cfg = SelfHostedInitConfig(
        target=tmp_path / "derived",
        source=tmp_path / "source",
        name="my-catalogue",
        attribution="attributed",
    )
    recorded = "A self-hosted catalogue derived from upstream-catalogue."

    assert _transform_recipe_string(
        recorded, {"name": "upstream-catalogue"}, cfg
    ) == recorded


@pytest.mark.parametrize(
    ("attribution", "has_source_uri"),
    [
        ("attributed", True),
        ("white-label", False),
        ("unexpected", False),
    ],
)
def test_pin_source_uri_is_attribution_gated(
    tmp_path: Path, attribution: str, has_source_uri: bool
) -> None:
    source = _make_source(tmp_path)
    cfg = _base_cfg(tmp_path, source, attribution=attribution)

    assert init_self_hosted(cfg).ok
    pin = _read_state(cfg.target)["pin"]

    assert ("source_uri" in pin) is has_source_uri
    if has_source_uri:
        assert pin["source_uri"] == str(source.resolve())


def test_self_host_pin_omits_unset_source_uri() -> None:
    pin = SelfHostPin(
        source_uri=None,
        source_revision=None,
        archive_sha256=None,
        synced_at="2026-09-14T12:34:56Z",
    )

    assert "source_uri" not in pin.to_dict()


def test_local_source_pin_has_empty_provenance_and_utc_timestamp(
    tmp_path: Path,
) -> None:
    source = _make_source(tmp_path)
    cfg = _base_cfg(tmp_path, source)

    assert init_self_hosted(cfg).ok
    pin = _read_state(cfg.target)["pin"]

    assert pin["source_revision"] is None
    assert pin["archive_sha256"] is None
    assert re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", pin["synced_at"])
