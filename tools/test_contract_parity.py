"""Tests for catalogue/check_contract_parity.py."""

from __future__ import annotations

import importlib.util
import shutil
import subprocess
import sys
from pathlib import Path
from types import ModuleType

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
PARITY_TOOL = REPO_ROOT / "tools" / "catalogue" / "check_contract_parity.py"
GENERATOR_TOOL = REPO_ROOT / "tools" / "catalogue" / "sync_contract_inventory.py"


def test_check_contract_parity_tool_exits_0() -> None:
    result = subprocess.run(
        [sys.executable, str(PARITY_TOOL)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    assert "ok" in result.stdout


def test_check_contract_parity_rejects_stale_public_inventory(
    tmp_path: Path,
) -> None:
    staged = tmp_path / "staged"
    staged_tool = staged / "tools" / "catalogue" / PARITY_TOOL.name
    staged_tool.parent.mkdir(parents=True)
    shutil.copy2(PARITY_TOOL, staged_tool)
    # The gate loads the canonical contract scan from the generator so the two
    # cannot diverge, so the generator has to be staged alongside it.
    shutil.copy2(GENERATOR_TOOL, staged_tool.parent / GENERATOR_TOOL.name)
    shutil.copytree(REPO_ROOT / "contracts", staged / "contracts")
    staged_data = staged / "packages" / "agentbundle" / "agentbundle" / "_data"
    shutil.copytree(
        REPO_ROOT / "packages" / "agentbundle" / "agentbundle" / "_data",
        staged_data,
    )
    (staged_data / "public-contracts.txt").write_text("pack.schema.json\n", encoding="utf-8")

    result = subprocess.run(
        [sys.executable, str(staged_tool)],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1
    assert "public-contracts.txt inventory is stale" in result.stderr


def test_sync_contract_inventory_check_matches_the_parity_gate() -> None:
    """The generator and the gate must agree on the canonical contract set.

    `check_contract_parity.py` imports `_render` from the generator so the
    two cannot drift; this pins that they stay wired together and that the
    generator's own `--check` mode agrees with the committed inventory.
    """
    result = subprocess.run(
        [sys.executable, "tools/catalogue/sync_contract_inventory.py", "--check"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr


def test_sync_contract_inventory_check_rejects_a_stale_inventory(
    tmp_path: Path,
) -> None:
    """`--check` must fail when the committed inventory is out of date."""
    inventory = (
        REPO_ROOT / "packages" / "agentbundle" / "agentbundle" / "_data" / "public-contracts.txt"
    )
    original = inventory.read_bytes()
    try:
        inventory.write_text("zzz-not-a-contract.json\n", encoding="utf-8")
        result = subprocess.run(
            [sys.executable, "tools/catalogue/sync_contract_inventory.py", "--check"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
        )
        assert result.returncode != 0
    finally:
        inventory.write_bytes(original)


INVENTORY = (
    REPO_ROOT / "packages" / "agentbundle" / "agentbundle" / "_data" / "public-contracts.txt"
)
VENDOR_ID = "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json"


def _generator() -> ModuleType:
    spec = importlib.util.spec_from_file_location("sync_contract_inventory", GENERATOR_TOOL)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _fixture(tmp_path: Path, manifest: str) -> Path:
    contracts = tmp_path / "contracts"
    (contracts / "sub").mkdir(parents=True)
    (contracts / "a.schema.json").write_text("{}", encoding="utf-8")
    (contracts / "b.toml").write_text("x = 1\n", encoding="utf-8")
    (contracts / "sub" / "a.schema.json").write_text("{}", encoding="utf-8")
    (contracts / "v.json").write_text(f'{{"$id": "{VENDOR_ID}"}}', encoding="utf-8")
    (contracts / "catalogue-spec.toml").write_text(manifest, encoding="utf-8")
    return contracts


def _row(path: str, role: str = "member", upstream: str | None = None) -> str:
    text = f'\n[[contract]]\npath = "{path}"\nrole = "{role}"\n'
    return text + (f'upstream = "{upstream}"\n' if upstream else "")


def test_manifest_repository_rows_match_the_specification() -> None:
    rows = _generator().load_manifest(REPO_ROOT / "contracts")
    by_role: dict[str, list[str]] = {"member": [], "bundled": [], "vendored": []}
    for row in rows:
        by_role[row.role].append(row.path)
    assert by_role["member"] == [
        "pack.schema.json", "catalogue.schema.json", "profile.schema.json",
        "skill.schema.json", "skill-manifest.schema.json", "target-vocab.toml",
        "catalogue-index.schema.json", "adapter.toml", "adapter.schema.json",
    ]  # fmt: skip
    assert sorted(by_role["bundled"]) == sorted([
        "marketplace-entry.schema.json", "plugin-manifest.schema.json",
        "plugin-manifest.derived.schema.json", "distribution-routes.toml",
        "distribution-routes.schema.json", "agent-plugin-extension-namespaces.toml",
        "agent-plugin-extension-namespaces.schema.json", "guide.schema.json",
        "jsonschema/knowledge-captured-observation.schema.json",
    ])  # fmt: skip
    assert sorted(by_role["vendored"]) == [
        "vendor/agent-plugins/1.0.0/mcp.schema.json",
        "vendor/agent-plugins/1.0.0/plugin.schema.json",
    ]
    assert len(rows) == 20
    assert "release = []" in (REPO_ROOT / "contracts" / "catalogue-spec.toml").read_text()


_REJECTIONS = [
    pytest.param("[spec]\n" + _row("a.schema.json"), "release", id="release-missing"),
    pytest.param('release = "x"\n' + _row("a.schema.json"), "release", id="release-not-array"),
    pytest.param("release = []\n" + _row("a.schema.json", "bogus"), "role", id="unknown-role"),
    pytest.param("release = []\n" + _row("a.schema.json") * 2, "duplicate", id="duplicate-path"),
    pytest.param("release = []\n" + _row("/etc/passwd"), "/etc/passwd", id="absolute"),
    pytest.param("release = []\n" + _row("sub/../a.schema.json"), "..", id="dotdot"),
    pytest.param("release = []\n" + _row("sub\\\\a.schema.json"), "backslash", id="backslash"),
    pytest.param("release = []\n" + _row("C:a.schema.json"), "drive", id="drive-letter"),
    pytest.param("release = []\n" + _row("missing.json"), "missing.json", id="missing-file"),
    pytest.param("release = []\n" + _row("sub"), "regular file", id="directory"),
    pytest.param("release = []\n" + _row("v.json", "vendored"), "https://", id="vendored-no-upstream"),
    pytest.param(
        "release = []\n" + _row("v.json", "vendored", "http://example.invalid/x"),
        "https://",
        id="vendored-http-upstream",
    ),
    pytest.param(
        "release = []\n" + _row("v.json", "vendored", "https://example.invalid/x"),
        "$id",
        id="vendored-id-mismatch",
    ),
    pytest.param(
        "release = []\n" + _row("a.schema.json") + _row("sub/a.schema.json", "bundled"),
        "a.schema.json",
        id="same-file-name",
    ),
]  # fmt: skip


@pytest.mark.parametrize(("manifest", "needle"), _REJECTIONS)
def test_manifest_rejects_invalid_manifest(tmp_path: Path, manifest: str, needle: str) -> None:
    generator = _generator()
    contracts = _fixture(tmp_path, manifest)
    with pytest.raises(
        generator.ManifestError, match=needle.replace("$", r"\$").replace(".", r"\.")
    ):
        generator.load_manifest(contracts)


def test_manifest_rejects_symlink_escaping_contracts(tmp_path: Path) -> None:
    generator = _generator()
    contracts = _fixture(tmp_path, "release = []\n" + _row("link.json"))
    outside = tmp_path / "outside.json"
    outside.write_text("{}", encoding="utf-8")
    try:
        (contracts / "link.json").symlink_to(outside)
    except (OSError, NotImplementedError):
        pytest.skip("symlinks unavailable")
    with pytest.raises(generator.ManifestError, match="link.json"):
        generator.load_manifest(contracts)


def test_inventory_write_emits_sorted_member_and_bundled_names(tmp_path: Path) -> None:
    generator = _generator()
    manifest = (
        "release = []\n"
        + _row("b.toml", "bundled")
        + _row("a.schema.json")
        + _row("v.json", "vendored", VENDOR_ID)
    )
    contracts = _fixture(tmp_path, manifest)
    inventory = tmp_path / "inv.txt"
    before = INVENTORY.read_bytes()
    assert generator.main(["--write"], contracts_dir=contracts, inventory=inventory) == 0
    assert inventory.read_text(encoding="utf-8") == "a.schema.json\nb.toml\n"
    assert INVENTORY.read_bytes() == before


def _parity() -> ModuleType:
    spec = importlib.util.spec_from_file_location("check_contract_parity", PARITY_TOOL)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_README_TEXT = """# contracts

## Files

### Specification members

| File | What it pins | CLI data |
| --- | --- | --- |
| `a.schema.json` | a | yes |

### Bundled, not members

| File | What it pins | CLI data |
| --- | --- | --- |
| `b.toml` | b | yes |

### Vendored

| File | What it pins | CLI data |
| --- | --- | --- |
| `v.json` | v | yes |

### Vendored notices

| File | What it pins | CLI data |
| --- | --- | --- |

### Repository only

| File | What it pins | CLI data |
| --- | --- | --- |
| `catalogue-spec.toml` | manifest | no |

## Next
"""


def _tree(tmp_path: Path) -> tuple[Path, Path, Path]:
    """A consistent tmp contracts/, _data/ and README that passes the gate."""
    manifest = (
        "release = []\n"
        + _row("a.schema.json")
        + _row("b.toml", "bundled")
        + _row("v.json", "vendored", VENDOR_ID)
    )
    contracts = _fixture(tmp_path, manifest)
    (contracts / "sub" / "a.schema.json").unlink()
    (contracts / "sub").rmdir()
    data = tmp_path / "_data"
    data.mkdir()
    for name in ("a.schema.json", "b.toml"):
        shutil.copyfile(contracts / name, data / name)
    (data / "public-contracts.txt").write_text("a.schema.json\nb.toml\n", encoding="utf-8")
    readme = tmp_path / "README.md"
    readme.write_text(_README_TEXT, encoding="utf-8")
    return contracts, data, readme


def _run(tree: tuple[Path, Path, Path], capsys: pytest.CaptureFixture[str]) -> tuple[int, str]:
    contracts, data, readme = tree
    code = _parity().main(contracts_dir=contracts, data_dir=data, readme=readme)
    return code, capsys.readouterr().err


def test_parity_passes_on_a_consistent_tree(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert _run(_tree(tmp_path), capsys) == (0, "")


def test_parity_rejects_a_missing_data_copy(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    tree = _tree(tmp_path)
    (tree[1] / "b.toml").unlink()
    code, err = _run(tree, capsys)
    assert code == 1 and "MISSING in _data: contracts/b.toml" in err


def test_parity_rejects_a_one_byte_difference(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    tree = _tree(tmp_path)
    (tree[1] / "a.schema.json").write_text("{ }", encoding="utf-8")
    code, err = _run(tree, capsys)
    assert code == 1 and "DIFFER: contracts/a.schema.json" in err


def test_parity_rejects_a_stale_inventory(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    tree = _tree(tmp_path)
    (tree[1] / "public-contracts.txt").write_text("a.schema.json\n", encoding="utf-8")
    code, err = _run(tree, capsys)
    assert code == 1 and "inventory is stale" in err


def test_parity_rejects_an_unlisted_top_level_contract(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    tree = _tree(tmp_path)
    (tree[0] / "extra.json").write_text("{}", encoding="utf-8")
    code, err = _run(tree, capsys)
    assert code == 1 and "UNLISTED: contracts/extra.json" in err


def test_parity_rejects_a_row_under_the_wrong_role_section(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    tree = _tree(tmp_path)
    text = _README_TEXT.replace("| `b.toml` | b | yes |\n", "")
    text = text.replace(
        "| `a.schema.json` | a | yes |\n",
        "| `a.schema.json` | a | yes |\n| `b.toml` | b | yes |\n",
    )
    tree[2].write_text(text, encoding="utf-8")
    code, err = _run(tree, capsys)
    assert code == 1
    assert "b.toml (bundled) is missing from 'Bundled, not members'" in err
    assert "b.toml under 'Specification members' is not a member row" in err


def test_parity_rejects_a_row_missing_from_its_section(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    tree = _tree(tmp_path)
    tree[2].write_text(_README_TEXT.replace("| `v.json` | v | yes |\n", ""), encoding="utf-8")
    code, err = _run(tree, capsys)
    assert code == 1 and "v.json (vendored) is missing from 'Vendored'" in err


def test_parity_rejects_a_non_manifest_path_under_members(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    tree = _tree(tmp_path)
    text = _README_TEXT.replace(
        "| `a.schema.json` | a | yes |\n",
        "| `a.schema.json` | a | yes |\n| `zzz.json` | z | yes |\n",
    )
    tree[2].write_text(text, encoding="utf-8")
    code, err = _run(tree, capsys)
    assert code == 1 and "zzz.json under 'Specification members' is not a member row" in err
