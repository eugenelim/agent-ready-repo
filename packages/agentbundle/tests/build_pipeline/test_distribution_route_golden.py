"""Golden-oracle construction tests for Phase 0 distribution routes."""

from __future__ import annotations

import base64
import json
import os
import shutil
import stat
import tomllib
from pathlib import Path

from agentbundle.build.main import _read_bundled, run_default_build

FIXTURE_ROOT = Path(__file__).resolve().parents[1] / "fixtures" / "distribution-routes"
SOURCE_PACKS = Path(__file__).resolve().parent / "fixtures" / "packs"


def _route_output_subdirectories() -> dict[str, str]:
    """Return each declared route and its contract-owned output directory.

    Read through the packaged loader rather than the repository `contracts/`
    copy: this test tree ships inside the sdist, where only the packaged copy
    exists. The contract-parity gate keeps the two byte-identical.
    """
    contract = tomllib.loads(_read_bundled("distribution-routes.toml"))
    return {
        route_name: route["package-layout"]["output-subdir"]
        for route_name, route in contract["route"].items()
    }


def _inventory(root: Path) -> dict[str, dict[str, object]]:
    """Return a lossless, deterministic inventory of regular files and links."""
    inventory: dict[str, dict[str, object]] = {}
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root).as_posix()
        metadata = path.lstat()
        mode = stat.S_IMODE(metadata.st_mode)
        if path.is_symlink():
            inventory[relative] = {
                "type": "symlink",
                # POSIX symlink permission bits are not portable (macOS reports
                # the umask while Linux reports 0777); link identity and target
                # are the stable package contract.
                "mode": 0o777,
                "target": os.readlink(path),
            }
        elif path.is_file():
            inventory[relative] = {
                "type": "file",
                "mode": mode,
                "bytes-base64": base64.b64encode(path.read_bytes()).decode("ascii"),
            }
    return inventory


def _fixture_packs(root: Path) -> Path:
    """Create route witnesses, including one eligible for skills-only output."""
    packs = root / "packs"
    publishable = packs / "publishable"
    repo_only = packs / "repo-only"
    portable = packs / "portable"
    shutil.copytree(SOURCE_PACKS / "core", publishable)
    shutil.copytree(SOURCE_PACKS / "user-guide-diataxis", repo_only)
    shutil.copytree(FIXTURE_ROOT / "witness-packs" / "portable", portable)

    publishable_pack = publishable / "pack.toml"
    publishable_pack.write_text(
        publishable_pack.read_text(encoding="utf-8").replace(
            'name = "core"', 'name = "publishable"'
        ),
        encoding="utf-8",
        newline="\n",
    )
    manifest = publishable / ".claude-plugin" / "plugin.json"
    manifest_data = json.loads(manifest.read_text(encoding="utf-8"))
    manifest_data["name"] = "publishable"
    manifest.write_text(
        json.dumps(manifest_data, indent=2) + "\n", encoding="utf-8", newline="\n"
    )
    repo_only_pack = repo_only / "pack.toml"
    repo_only_pack.write_text(
        repo_only_pack.read_text(encoding="utf-8").replace(
            'name = "user-guide-diataxis"', 'name = "repo-only"'
        ),
        encoding="utf-8",
        newline="\n",
    )

    (publishable / "README.md").write_text(
        "# Publishable fixture\n", encoding="utf-8", newline="\n"
    )
    seeds = publishable / "seeds"
    seeds.mkdir()
    (seeds / "AGENTS.md").write_text(
        "# Fixture agent context\n", encoding="utf-8", newline="\n"
    )
    skill = publishable / ".apm" / "skills" / "example"
    payload = skill / "payload.txt"
    payload.write_text("linked payload\n", encoding="utf-8", newline="\n")
    (skill / "payload-link.txt").symlink_to("payload.txt")
    return packs


def _build_inventories(root: Path) -> dict[str, dict[str, dict[str, object]]]:
    """Build the characterization fixture and inventory every route root."""
    packs = _fixture_packs(root)
    output = root / "dist"
    run_default_build(packs, output)
    return {
        route_name: _inventory(output / output_subdirectory)
        for route_name, output_subdirectory in _route_output_subdirectories().items()
    }


def _assert_lossless_inventory(inventory: dict[str, object]) -> None:
    """Assert the checked-in oracle can distinguish every filesystem change."""
    assert inventory
    for relpath, raw_entry in inventory.items():
        assert relpath and not relpath.startswith("/") and ".." not in Path(relpath).parts
        assert isinstance(raw_entry, dict)
        entry = raw_entry
        assert entry.get("type") in {"file", "symlink"}
        assert isinstance(entry.get("mode"), int)
        if entry["type"] == "file":
            assert set(entry) == {"type", "mode", "bytes-base64"}
            assert base64.b64decode(entry["bytes-base64"], validate=True) is not None
        else:
            assert set(entry) == {"type", "mode", "target"}
            assert isinstance(entry["target"], str) and entry["target"]


def test_golden_oracle_declares_every_route_tree(tmp_path: Path) -> None:
    """Require a lossless inventory for every declared distribution route."""
    oracle_path = FIXTURE_ROOT / "golden.json"

    assert oracle_path.is_file(), "pre-migration distribution-route oracle is missing"
    oracle = json.loads(oracle_path.read_text(encoding="utf-8"))
    assert set(oracle) == set(_route_output_subdirectories())
    for inventory in oracle.values():
        assert isinstance(inventory, dict)
        _assert_lossless_inventory(inventory)

    apm_paths = set(oracle["apm"])
    claude_paths = set(oracle["claude-plugins"])
    for suffix in (
        "apm.yml",
        ".apm/skills/example/SKILL.md",
        ".apm/agents/bar.md",
        ".apm/commands/qux.md",
        ".apm/hooks/baz.py",
        ".apm/hook-wiring/baz.toml",
        ".apm/hooks/install-marker.py",
        ".apm/hooks/install-marker.json",
        "pack.toml",
        "README.md",
        "seeds/AGENTS.md",
    ):
        assert f"publishable/{suffix}" in apm_paths
    for suffix in (
        "skills/example/SKILL.md",
        "agents/bar.md",
        "commands/qux.md",
        "hooks/baz.py",
        ".claude-plugin/plugin.json",
        ".claude-plugin/scripts/install-marker.py",
        "pack.toml",
        "README.md",
        "seeds/AGENTS.md",
    ):
        assert f"publishable/{suffix}" in claude_paths
    assert "repo-only/apm.yml" in apm_paths
    assert not any(path.startswith("repo-only/") for path in claude_paths)
    assert "marketplace.json" in claude_paths
    assert oracle["agent-plugin"]
    assert "portable/plugin.json" in oracle["agent-plugin"]
    assert "portable/skills/example/SKILL.md" in oracle["agent-plugin"]
    assert _build_inventories(tmp_path) == oracle


def test_golden_oracle_preserves_safe_links_without_dereference() -> None:
    """Pin the existing non-dereferencing behavior on package routes."""
    oracle_path = FIXTURE_ROOT / "golden.json"
    assert oracle_path.is_file(), "pre-migration distribution-route oracle is missing"
    oracle = json.loads(oracle_path.read_text(encoding="utf-8"))

    expected_link = {"type": "symlink", "mode": 0o777, "target": "payload.txt"}
    assert oracle["apm"][
        "publishable/.apm/skills/example/payload-link.txt"
    ] == expected_link
    assert oracle["claude-plugins"][
        "publishable/skills/example/payload-link.txt"
    ] == expected_link


def test_golden_inventory_detects_byte_mode_and_link_mutations(tmp_path: Path) -> None:
    """Prove the oracle changes for every filesystem attribute it promises."""
    root = tmp_path / "tree"
    root.mkdir()
    file_path = root / "payload.txt"
    file_path.write_bytes(b"one\n")
    link_path = root / "payload-link.txt"
    link_path.symlink_to("payload.txt")
    baseline = _inventory(root)

    file_path.write_bytes(b"two\n")
    assert _inventory(root) != baseline
    file_path.write_bytes(b"one\n")
    file_path.chmod(0o744)
    assert _inventory(root) != baseline
    file_path.chmod(0o644)
    link_path.unlink()
    link_path.symlink_to("other.txt")
    assert _inventory(root) != baseline


def test_route_golden_build_is_deterministic(tmp_path: Path) -> None:
    """Pin repeatability independently of the checked-in expected inventory."""
    first = _build_inventories(tmp_path / "first")
    second = _build_inventories(tmp_path / "second")
    assert first == second
