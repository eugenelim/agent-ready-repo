"""Scaffold projection contract: the _data/catalogue-scaffold/ tree must be
byte-identical to the repo-root scaffold sources.

Also verifies:
- scaffold_root() returns a readable directory.
- packs/AGENTS.md in the _data copy is the portable version (no `make build-self`).
- profiles/AGENTS.md is present and non-empty.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
_DATA_SCAFFOLD = (
    Path(__file__).resolve().parents[2] / "agentbundle" / "_data" / "catalogue-scaffold"
)


def _load_sync_tool():
    """Read the pair list from the tool itself.

    This list used to be restated here and had drifted to 11 entries against
    the tool's 13 — so the gate was blind to drift in the two files it omitted,
    including the authoring standards. One source, no copy.
    """
    path = _REPO_ROOT / "tools" / "catalogue" / "sync_authoring_scaffold.py"
    spec = importlib.util.spec_from_file_location("sync_authoring_scaffold", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_SYNC_PAIRS: list[tuple[str, str]] = [
    (str(src.relative_to(_REPO_ROOT)), dst) for src, dst in _load_sync_tool()._SYNC_PAIRS
]


def test_scaffold_root_is_directory():
    from agentbundle.scaffold import scaffold_root

    root = scaffold_root()
    assert root.is_dir(), f"scaffold_root() returned non-directory: {root}"


def test_data_scaffold_exists():
    assert _DATA_SCAFFOLD.is_dir(), (
        f"_data/catalogue-scaffold/ not found at {_DATA_SCAFFOLD}; "
        "run: python3 tools/catalogue/sync_authoring_scaffold.py --write"
    )


def test_projection_byte_identical_to_repo_root():
    drifts: list[str] = []
    for repo_rel, scaffold_rel in _SYNC_PAIRS:
        src = _REPO_ROOT / repo_rel
        dst = _DATA_SCAFFOLD / scaffold_rel
        if not src.exists():
            drifts.append(f"MISSING source: {repo_rel}")
            continue
        if not dst.exists():
            drifts.append(f"MISSING in _data: {scaffold_rel}")
            continue
        if src.read_bytes() != dst.read_bytes():
            drifts.append(f"DRIFT: {scaffold_rel}")
    assert not drifts, (
        "scaffold projection is out of sync with repo root:\n"
        + "\n".join(f"  {d}" for d in drifts)
        + "\nRun: python3 tools/catalogue/sync_authoring_scaffold.py --write"
    )


def test_packs_agents_md_is_portable():
    agents_md = _DATA_SCAFFOLD / "packs" / "AGENTS.md"
    assert agents_md.exists(), "_data/catalogue-scaffold/packs/AGENTS.md missing"
    text = agents_md.read_text(encoding="utf-8")
    # The portable copy must not reference Make-only host commands.
    assert "make build-self" not in text.lower(), (
        "packs/AGENTS.md in _data/ references 'make build-self' — this is host-specific"
    )
    assert "FORCE=1" not in text, (
        "packs/AGENTS.md in _data/ references FORCE=1 — this is host-specific"
    )
    assert "docs/product/changelog.md" not in text, (
        "packs/AGENTS.md in _data/ references docs/product/changelog.md — this is host-specific"
    )


def test_profiles_agents_md_present_and_non_empty():
    agents_md = _DATA_SCAFFOLD / "profiles" / "AGENTS.md"
    assert agents_md.exists(), "_data/catalogue-scaffold/profiles/AGENTS.md missing"
    assert agents_md.stat().st_size > 0, "_data/catalogue-scaffold/profiles/AGENTS.md is empty"


def test_example_pack_toml_name_matches_plugin_json():
    import json
    import tomllib

    pack_toml = _DATA_SCAFFOLD / "packs" / "_example" / "pack.toml"
    plugin_json = _DATA_SCAFFOLD / "packs" / "_example" / ".claude-plugin" / "plugin.json"
    assert pack_toml.exists()
    assert plugin_json.exists()

    pack = tomllib.loads(pack_toml.read_text(encoding="utf-8"))
    plugin = json.loads(plugin_json.read_text(encoding="utf-8"))

    assert pack["pack"]["name"] == plugin["name"], (
        "pack name mismatch between pack.toml and plugin.json"
    )
    assert pack["pack"]["version"] == plugin["version"], (
        "version mismatch between pack.toml and plugin.json"
    )


def test_manifest_present_and_lists_all_files():
    from agentbundle.scaffold import list_files, load_manifest

    manifest = load_manifest()
    assert manifest.get("version") == 1, "manifest version must be 1"
    files = list_files()
    assert len(files) >= len(_SYNC_PAIRS), (
        f"manifest has fewer files ({len(files)}) than expected ({len(_SYNC_PAIRS)})"
    )
    for _, scaffold_rel in _SYNC_PAIRS:
        assert scaffold_rel in files, f"'{scaffold_rel}' missing from manifest"


def test_manifest_hashes_pass_verify():
    from agentbundle.scaffold import verify_hashes

    assert verify_hashes(), (
        "scaffold.verify_hashes() returned False — _data/ files don't match manifest"
    )


def test_scaffold_module_read_file():
    from agentbundle.scaffold import read_file

    content = read_file("packs/README.md")
    assert len(content) > 0, "read_file('packs/README.md') returned empty bytes"
    assert b"pack" in content.lower(), "packs/README.md should mention 'pack'"


def test_materialize_to_copies_all_files(tmp_path):
    from agentbundle.scaffold import list_files, materialize_to

    materialize_to(tmp_path)
    for rel in list_files():
        assert (tmp_path / rel).exists(), f"materialize_to did not copy '{rel}'"
