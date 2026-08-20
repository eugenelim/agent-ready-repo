"""Construction tests for lint-conformance-portability.py."""

from __future__ import annotations

import importlib.util
from pathlib import Path


def _load_linter():
    path = Path(__file__).with_name("lint-conformance-portability.py")
    spec = importlib.util.spec_from_file_location("lint_conformance_portability", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _seed_catalogue(tmp_path: Path, source: str) -> Path:
    manifest = tmp_path / "packs" / "named-pack" / "pack.toml"
    manifest.parent.mkdir(parents=True)
    manifest.write_text('[pack]\nname = "named-pack"\n', encoding="utf-8")
    test = tmp_path / "tests" / "conformance" / "test_rule.py"
    test.parent.mkdir(parents=True)
    test.write_text(source, encoding="utf-8")
    return tmp_path


def test_specific_pack_name_is_rejected(tmp_path: Path) -> None:
    root = _seed_catalogue(tmp_path, 'PACK = "named-pack"\n')
    assert _load_linter().find_violations(root)


def test_generic_rule_text_passes(tmp_path: Path) -> None:
    root = _seed_catalogue(tmp_path, 'PACKS_DIR = ROOT / "packs"\n')
    assert _load_linter().find_violations(root) == []


def test_repo_only_root_join_is_rejected(tmp_path: Path) -> None:
    """`CATALOGUE_ROOT / "packages"` names a directory no adopter catalogue has."""
    root = _seed_catalogue(
        tmp_path, 'BUNDLED = CATALOGUE_ROOT / "packages" / "agentbundle"\n'
    )
    assert _load_linter().find_repo_only_references(root)


def test_repo_only_path_literal_is_rejected(tmp_path: Path) -> None:
    """The same reach written as a bare literal is equally unrunnable."""
    root = _seed_catalogue(tmp_path, 'SCRIPT = "tools/lint-something.py"\n')
    assert _load_linter().find_repo_only_references(root)


def test_rule_shaped_paths_pass(tmp_path: Path) -> None:
    """`packs/` and `profiles/` exist in every catalogue, so they stay legal."""
    root = _seed_catalogue(
        tmp_path,
        'PACKS = CATALOGUE_ROOT / "packs"\nPROFILES = CATALOGUE_ROOT / "profiles"\n',
    )
    assert _load_linter().find_repo_only_references(root) == []
