"""Scaffold projection contract: the _data/catalogue-scaffold/ tree must be
byte-identical to the repo-root scaffold sources.

Also verifies:
- scaffold_root() returns a readable directory.
- packs/AGENTS.md in the _data copy is the portable version (no `make build-self`).
- packs/AGENTS.md and profiles/AGENTS.md cite only paths the scaffold ships.
- profiles/AGENTS.md is present and non-empty.
"""

from __future__ import annotations

import re
from pathlib import Path

_DATA_SCAFFOLD = (
    Path(__file__).resolve().parents[2] / "agentbundle" / "_data" / "catalogue-scaffold"
)
_ROOTED_CITATION = re.compile(
    r"(?<![\w/])((?:\.\./|\./)?(?:tools|docs|contracts|guides|packs|profiles)/"
    r"(?:[A-Za-z0-9_.-]+/)*[A-Za-z0-9_.-]+/?(?:#[A-Za-z0-9_.-]+)?)"
)


def test_scaffold_root_is_directory():
    from agentbundle.scaffold import scaffold_root

    root = scaffold_root()
    assert root.is_dir(), f"scaffold_root() returned non-directory: {root}"


def test_data_scaffold_exists():
    assert _DATA_SCAFFOLD.is_dir(), (
        f"_data/catalogue-scaffold/ not found at {_DATA_SCAFFOLD}; "
        "run: python3 tools/catalogue/sync_authoring_scaffold.py --write"
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


def _assert_cites_only_shipped_paths(relative_path: str) -> None:
    """Every path this file points an adopter at must exist in their tree.

    The scaffold is what `catalogue init` writes, so a reference to a
    catalogue-local tool, governance doc, or unshipped guide dangles the moment
    it lands in an adopter's repo — they read a rule enforced by a linter they
    do not have, or a pointer to a file they cannot open. The rule itself has to
    carry its own weight in the shipped copy.
    """
    text = (_DATA_SCAFFOLD / relative_path).read_text(encoding="utf-8")
    shipped = {
        str(p.relative_to(_DATA_SCAFFOLD)).replace("\\", "/")
        for p in _DATA_SCAFFOLD.rglob("*")
        if p.is_file()
    }
    # Prefixes that name a real location rather than a per-pack template
    # fragment (`pack.toml`, `evals/evals.json`, `.apm/skills/<name>/…`).
    rooted = ("tools/", "docs/", "contracts/", "guides/", "packs/", "profiles/")
    # `AGENTS.local.md` is the documented host-override hook: absent by design,
    # and every reference to it is conditional on the adopter having created one.
    optional_by_design = {"packs/AGENTS.local.md"}
    cited = {
        ref.split("#", 1)[0].rstrip("/").lstrip("./").removeprefix("../")
        for ref in _ROOTED_CITATION.findall(text)
    }
    dangling = sorted(
        ref for ref in cited
        if ref.startswith(rooted)
        and "<" not in ref
        and ref not in shipped
        and ref not in optional_by_design
    )
    assert not dangling, (
        f"{relative_path} points an adopter at paths the scaffold does not ship: "
        + ", ".join(dangling)
        + "\nState the rule without the citation, or ship the file."
    )


def test_packs_agents_md_cites_only_paths_it_ships():
    _assert_cites_only_shipped_paths("packs/AGENTS.md")


def test_profiles_agents_md_cites_only_paths_it_ships():
    _assert_cites_only_shipped_paths("profiles/AGENTS.md")


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
    assert files, "scaffold manifest must list materialised files"


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
