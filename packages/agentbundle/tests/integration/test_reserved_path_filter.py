"""Reserved authoring asset filter: any immediate child of packs/ or profiles/
whose name begins with `_` must be invisible to all catalogue-payload surfaces.

Surfaces tested (spec § Bucket 2 — Reserved `_` asset convention):
- discover_packs (build.main)
- _discover_pack_dirs (commands.list_packs)
- lint_catalogue (catalogue_tooling.lint)
- verify_catalogue (catalogue_tooling.verify)
- list_profiles (commands.profile)
- _scan_content (catalogue_tooling.package) — packs and profiles
"""

from __future__ import annotations

import json
from pathlib import Path

# ---------------------------------------------------------------------------
# Fixture builders
# ---------------------------------------------------------------------------


def _write_pack(root: Path, name: str, version: str = "0.1.0") -> Path:
    d = root / "packs" / name
    (d / ".apm" / "skills" / f"{name}-skill").mkdir(parents=True)
    (d / ".claude-plugin").mkdir(parents=True, exist_ok=True)
    (d / "pack.toml").write_text(
        f'[pack]\nname = "{name}"\nversion = "{version}"\n'
        'description = "fixture"\n'
        '[pack.adapter-contract]\nversion = "0.6"\n'
        '[pack.install]\ndefault-scope = "repo"\nallowed-scopes = ["repo"]\n',
        encoding="utf-8",
    )
    (d / ".claude-plugin" / "plugin.json").write_text(
        json.dumps({"name": name, "version": version, "description": "fixture"}),
        encoding="utf-8",
    )
    return d


def _write_marketplace(root: Path, packs: list[str]) -> None:
    mp = root / ".claude-plugin" / "marketplace.json"
    mp.parent.mkdir(parents=True, exist_ok=True)
    plugins = [{"name": p, "version": "0.1.0", "description": "fixture"} for p in packs]
    mp.write_text(
        json.dumps({"name": "fixture", "description": "fixture",
                    "owner": {"name": "fixture"}, "plugins": plugins}),
        encoding="utf-8",
    )


# ---------------------------------------------------------------------------
# discover_packs
# ---------------------------------------------------------------------------


def test_discover_packs_excludes_underscore_dirs(tmp_path):
    from agentbundle.build.main import discover_packs

    _write_pack(tmp_path, "real-pack")
    _write_pack(tmp_path, "_example")
    _write_marketplace(tmp_path, ["real-pack"])

    packs = discover_packs(tmp_path / "packs")
    names = [p.name for p in packs]
    assert "real-pack" in names
    assert "_example" not in names, "_example should be excluded from discover_packs"


# ---------------------------------------------------------------------------
# list_packs._discover_pack_dirs
# ---------------------------------------------------------------------------


def test_discover_pack_dirs_excludes_underscore(tmp_path):
    from agentbundle.commands.list_packs import _discover_pack_dirs

    _write_pack(tmp_path, "visible-pack")
    _write_pack(tmp_path, "_scaffold")

    dirs = _discover_pack_dirs(tmp_path)
    names = [d.name for d in dirs]
    assert "visible-pack" in names
    assert "_scaffold" not in names, "_scaffold should be excluded from _discover_pack_dirs"


# ---------------------------------------------------------------------------
# lint_catalogue
# ---------------------------------------------------------------------------


def test_lint_excludes_underscore_pack(tmp_path):
    from agentbundle.catalogue_tooling.lint import lint_catalogue

    _write_pack(tmp_path, "good-pack")
    _write_pack(tmp_path, "_example")
    _write_marketplace(tmp_path, ["good-pack"])

    result = lint_catalogue(tmp_path)
    pack_names_with_errors = {d.pack for d in result.diagnostics if d.severity.name == "ERROR"}
    assert "_example" not in pack_names_with_errors, \
        "_example should be invisible to lint"


# ---------------------------------------------------------------------------
# verify_catalogue
# ---------------------------------------------------------------------------


def test_verify_excludes_underscore_pack(tmp_path):
    from agentbundle.catalogue_tooling.verify import verify_catalogue

    _write_pack(tmp_path, "solid-pack")
    _write_pack(tmp_path, "_template")
    _write_marketplace(tmp_path, ["solid-pack"])

    result = verify_catalogue(tmp_path)
    pack_names_with_errors = {d.pack for d in result.diagnostics if d.severity.name == "ERROR"}
    assert "_template" not in pack_names_with_errors, \
        "_template should be invisible to verify"


# ---------------------------------------------------------------------------
# list_profiles — underscore subdirs are never globbed as *.toml at root
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# _scan_content — packs and profiles
# ---------------------------------------------------------------------------


def test_scan_content_excludes_underscore_packs(tmp_path):
    from agentbundle.catalogue_tooling.package import _scan_content

    _write_pack(tmp_path, "shipped-pack")
    _write_pack(tmp_path, "_example")
    _write_marketplace(tmp_path, ["shipped-pack"])

    paths = _scan_content(tmp_path)
    posix = [p.relative_to(tmp_path).as_posix() for p in paths]
    assert any(s.startswith("packs/shipped-pack/") for s in posix), \
        "shipped-pack should appear in scan content"
    assert not any(s.startswith("packs/_example/") for s in posix), \
        "packs/_example/ must not appear in scan content"


def test_scan_content_excludes_underscore_profiles(tmp_path):
    from agentbundle.catalogue_tooling.package import _scan_content

    profiles_dir = tmp_path / "profiles"
    profiles_dir.mkdir()
    (profiles_dir / "_example").mkdir()
    (profiles_dir / "_example" / "profile.toml").write_text(
        'scope = "repo"\ndescription = "example"\n[[packs]]\npack = "example-pack"\n',
        encoding="utf-8",
    )
    _write_marketplace(tmp_path, [])

    paths = _scan_content(tmp_path)
    posix = [p.relative_to(tmp_path).as_posix() for p in paths]
    assert not any(s.startswith("profiles/_example/") for s in posix), \
        "profiles/_example/ must not appear in scan content"


def test_scan_content_pack_include_excludes_underscore_profiles(tmp_path):
    from agentbundle.catalogue_tooling.package import _scan_content

    _write_pack(tmp_path, "included-pack")
    profiles_dir = tmp_path / "profiles"
    profiles_dir.mkdir()
    (profiles_dir / "_example").mkdir()
    (profiles_dir / "_example" / "profile.toml").write_text(
        'scope = "repo"\ndescription = "example"\n[[packs]]\npack = "example-pack"\n',
        encoding="utf-8",
    )
    _write_marketplace(tmp_path, ["included-pack"])

    paths = _scan_content(tmp_path, pack_include=["packs/included-pack"])
    posix = [p.relative_to(tmp_path).as_posix() for p in paths]
    assert not any(s.startswith("profiles/_example/") for s in posix), \
        "profiles/_example/ must not appear in scan content when pack_include is set"


# ---------------------------------------------------------------------------
# _validate_content — reserved profile subdir with malformed TOML must not fail
# ---------------------------------------------------------------------------


def test_validate_content_ignores_malformed_toml_in_reserved_profile_subdir(tmp_path):
    from agentbundle.catalogue_tooling.package import _scan_content, _validate_content

    # Valid installable pack + marketplace so _scan_content and _validate_content pass.
    _write_pack(tmp_path, "good-pack")
    _write_marketplace(tmp_path, ["good-pack"])

    # Reserved subdir containing intentionally malformed TOML.
    profiles_dir = tmp_path / "profiles"
    profiles_dir.mkdir()
    (profiles_dir / "_example").mkdir()
    (profiles_dir / "_example" / "profile.toml").write_text(
        "THIS IS NOT VALID TOML ::::",
        encoding="utf-8",
    )

    content_paths = _scan_content(tmp_path)
    error = _validate_content(tmp_path, content_paths)
    assert error is None, (
        "malformed TOML in reserved profiles/_example/ must not fail _validate_content: "
        + repr(error)
    )


def test_list_profiles_ignores_underscore_subdirs(tmp_path):
    from agentbundle.commands.profile import list_profiles

    profiles_dir = tmp_path / "profiles"
    profiles_dir.mkdir()
    # A real profile at the root level.
    (profiles_dir / "dev.toml").write_text(
        'scope = "repo"\ndescription = "dev profile"\n[[packs]]\npack = "real-pack"\n',
        encoding="utf-8",
    )
    # Reserved subdir — must not appear.
    (profiles_dir / "_example").mkdir()
    (profiles_dir / "_example" / "profile.toml").write_text(
        'scope = "repo"\ndescription = "example"\n[[packs]]\npack = "example-pack"\n',
        encoding="utf-8",
    )
    _write_pack(tmp_path, "real-pack")
    _write_marketplace(tmp_path, ["real-pack"])

    profiles = list_profiles(tmp_path)
    ids = [p.id for p in profiles]
    assert "dev" in ids
    assert "_example" not in ids, "_example subdir must not appear as a profile"
