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
        "catalogue-manifest.schema.json",
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
    assert len(rows) == 21
    releases, corrections = _generator().load_releases(REPO_ROOT / "contracts")
    assert [row.version for row in releases] == ["0.1"]
    assert corrections == []


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
    (data / "catalogue-members.txt").write_text("a.schema.json\n", encoding="utf-8")
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


# --- release and correction rows -------------------------------------------

_HEX = "a" * 64
_HEX2 = "b" * 64


def _release(version: str = "0.1", members: str | None = None, pages: str | None = None) -> str:
    members = (
        members if members is not None else f'"a.schema.json" = "{_HEX}"\n"b.toml" = "{_HEX}"'
    )
    pages = pages if pages is not None else f'"overview.md" = "{_HEX}"'
    return (
        f'\n[[release]]\nversion = "{version}"\ndate = "2026-10-23"\n'
        f'adapter_contract = "0.18"\n[release.members]\n{members}\n[release.pages]\n{pages}\n'
    )


def _correction(
    supersedes: str = "0.1",
    date: str = "2026-11-01",
    version: str = "0.1",
    pages: str | None = None,
    extra: str = "",
) -> str:
    pages = pages if pages is not None else f'"overview.md" = "{_HEX2}"'
    return (
        f'\n[[correction]]\nversion = "{version}"\ndate = "{date}"\nnote = "typo"\n'
        f'supersedes = "{supersedes}"\n{extra}[correction.pages]\n{pages}\n'
    )


def _released(tmp_path: Path, rows: str, versions: tuple[str, ...] = ("0.1",)) -> Path:
    """A fixture whose manifest is `rows` appended after two member rows, snapshots staged."""
    contracts = _fixture(
        tmp_path,
        _row("a.schema.json") + _row("b.toml"),
    )
    for version in versions:
        snap = contracts / "releases" / "catalogue" / version
        (snap / "sub").mkdir(parents=True)
        for name in ("a.schema.json", "b.toml", "overview.md"):
            (snap / name).write_text("x", encoding="utf-8")
    manifest = contracts / "catalogue-spec.toml"
    text = manifest.read_text(encoding="utf-8")
    manifest.write_text(
        (text + rows) if "[[release]]" in rows else ("release = []\n" + text),
        encoding="utf-8",
    )
    return contracts


def _load(tmp_path: Path, rows: str, versions: tuple[str, ...] = ("0.1",)):
    return _generator().load_releases(_released(tmp_path, rows, versions))


def test_release_row_keeps_members_and_pages_separate(tmp_path: Path) -> None:
    releases, corrections = _load(tmp_path, _release())
    (row,) = releases
    assert (row.version, row.date, row.adapter_contract) == ("0.1", "2026-10-23", "0.18")
    assert set(row.members) == {"a.schema.json", "b.toml"}
    assert set(row.pages) == {"overview.md"}
    assert corrections == []


@pytest.mark.parametrize(
    ("rows", "needle"),
    [
        pytest.param(
            _release(members=f'"a.schema.json" = "{_HEX}"'),
            "lacks a digest for b.toml",
            id="missing-member-digest",
        ),
        pytest.param(
            _release(
                members=f'"a.schema.json" = "{_HEX}"\n"b.toml" = "{_HEX}"\n"zz.json" = "{_HEX}"'
            ),
            "zz.json",
            id="unknown-path",
        ),
        pytest.param(
            _release(members=f'"a.schema.json" = 5\n"b.toml" = "{_HEX}"'),
            "digest",
            id="non-string",
        ),
        pytest.param(_release(version="0.1.2"), "MAJOR.MINOR", id="bad-version"),
        pytest.param(_release(version="../x"), "MAJOR.MINOR", id="version-escape"),
        pytest.param(
            _release(version="0.01") + _release(),
            "duplicate of release row",
            id="numeric-duplicate",
        ),
        pytest.param(
            _release(pages=f'"overview.md" = "{_HEX}"\n"./a.schema.json" = "{_HEX}"'),
            "share key",
            id="members-pages-alias",
        ),
    ],
)
def test_release_row_rejections_name_the_row(tmp_path: Path, rows: str, needle: str) -> None:
    generator = _generator()
    contracts = _released(tmp_path, rows, ("0.1", "0.01"))
    with pytest.raises(generator.ManifestError, match=r"release row \d") as info:
        generator.load_releases(contracts)
    assert needle in str(info.value)


@pytest.mark.parametrize(
    "key",
    [
        "/etc/passwd",
        "../a.schema.json",
        "sub\\\\a.schema.json",
        "C:a.schema.json",
        "sub",
        "missing.md",
    ],
)
@pytest.mark.parametrize("table", ["members", "pages"])
def test_release_path_keys_are_confined_to_the_snapshot(
    tmp_path: Path, key: str, table: str
) -> None:
    generator = _generator()
    entry = f'"{key}" = "{_HEX}"'
    rows = (
        _release(members=entry + f'\n"a.schema.json" = "{_HEX}"')
        if table == "members"
        else _release(pages=entry)
    )
    contracts = _released(tmp_path, rows)
    with pytest.raises(generator.ManifestError, match=r"release row 0 \(0\.1\)"):
        generator.load_releases(contracts)


def test_release_path_outside_snapshot_root_is_rejected(tmp_path: Path) -> None:
    generator = _generator()
    contracts = _released(tmp_path, _release(pages=f'"overview.md" = "{_HEX}"'))
    (contracts / "outside.md").write_text("x", encoding="utf-8")
    rows = _release(pages=f'"overview.md" = "{_HEX}"\n"../outside.md" = "{_HEX}"')
    manifest = contracts / "catalogue-spec.toml"
    manifest.write_text(manifest.read_text().split("[[release]]")[0] + rows, encoding="utf-8")
    with pytest.raises(generator.ManifestError, match="outside.md"):
        generator.load_releases(contracts)


def test_version_ordering_is_numeric() -> None:
    generator = _generator()
    assert generator.version_key("0.10") > generator.version_key("0.9")
    assert generator.version_key("0.01") == generator.version_key("0.1")


def test_latest_release_ignores_corrections(tmp_path: Path) -> None:
    generator = _generator()
    contracts = _released(
        tmp_path,
        _release("0.9") + _release("0.10") + _correction(version="0.9", supersedes="0.9"),
        ("0.9", "0.10"),
    )
    releases, _ = generator.load_releases(contracts)
    assert generator.latest_release(releases).version == "0.10"


@pytest.mark.parametrize(
    ("rows", "needle"),
    [
        pytest.param(
            _correction(extra=f'members = {{"a.schema.json" = "{_HEX}"}}\n'),
            "members",
            id="members-table",
        ),
        pytest.param(
            _correction(pages=f'"a.schema.json" = "{_HEX}"'),
            "not a release page source",
            id="outside-pages",
        ),
        pytest.param(_correction(version="0.2"), "no release row", id="unknown-version"),
        pytest.param(_correction(supersedes="2020-01-01"), "dangling", id="dangling"),
        pytest.param(
            _correction() + _correction(date="2026-11-02"),
            "duplicated supersedes",
            id="duplicated",
        ),
        pytest.param(
            _correction(supersedes="2026-11-02")
            + _correction(supersedes="2026-11-01", date="2026-11-02"),
            "not rooted",
            id="cyclic",
        ),
    ],
)
def test_correction_row_rejections(tmp_path: Path, rows: str, needle: str) -> None:
    generator = _generator()
    contracts = _released(tmp_path, _release() + rows)
    with pytest.raises(generator.ManifestError) as info:
        generator.load_releases(contracts)
    assert needle in str(info.value)


def test_correction_without_supersedes_is_rejected(tmp_path: Path) -> None:
    generator = _generator()
    row = _correction().replace('supersedes = "0.1"\n', "")
    with pytest.raises(generator.ManifestError, match="supersedes"):
        generator.load_releases(_released(tmp_path, _release() + row))


def test_governing_correction_is_the_chain_head_whatever_the_order(tmp_path: Path) -> None:
    generator = _generator()
    first = _correction()
    second = _correction(supersedes="2026-11-01", date="2026-11-02")
    for rows in (first + second, second + first):
        releases, corrections = generator.load_releases(
            _released(tmp_path / str(len(rows) + rows.index("2026-11-02")), _release() + rows)
        )
        assert generator.governing_correction(corrections, "0.1").date == "2026-11-02"


def test_correction_with_in_set_pages_is_accepted(tmp_path: Path) -> None:
    _, corrections = _load(tmp_path, _release() + _correction())
    assert [row.supersedes for row in corrections] == ["0.1"]


def test_release_rejection_label_is_caller_supplied() -> None:
    generator = _generator()
    with pytest.raises(generator.ManifestError, match="release row 3 .0.9."):
        generator._check_path(0, "nope", REPO_ROOT, "release row 3 (0.9)")


def test_inventory_member_set_comes_from_the_shared_predicate(tmp_path: Path) -> None:
    generator = _generator()
    source = GENERATOR_TOOL.read_text(encoding="utf-8")
    assert source.count('endswith(".json")') == 1
    contracts = _fixture(tmp_path, "release = []\n" + _row("a.schema.json") + _row("b.toml"))
    assert generator._render_members(contracts) == "a.schema.json\n"
    (contracts / "c.schema.json").write_text("{}", encoding="utf-8")
    manifest = contracts / "catalogue-spec.toml"
    manifest.write_text(manifest.read_text() + _row("c.schema.json"), encoding="utf-8")
    assert generator._render_members(contracts) == "a.schema.json\nc.schema.json\n"


def test_real_members_inventory_is_the_json_schema_members() -> None:
    generator = _generator()
    listed = (
        (INVENTORY.with_name("catalogue-members.txt")).read_text(encoding="utf-8").splitlines()
    )
    derived = [row.data_name for row in generator.json_schema_members(REPO_ROOT / "contracts")]
    assert sorted(listed) == sorted(derived) and len(listed) == 8
    assert "adapter.toml" not in listed and "target-vocab.toml" not in listed


@pytest.mark.parametrize("content", ["", "a.schema.json\nextra.json\n", "b.toml\n"])
def test_parity_rejects_a_drifted_members_inventory(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], content: str
) -> None:
    tree = _tree(tmp_path)
    (tree[1] / "catalogue-members.txt").write_text(content, encoding="utf-8")
    code, err = _run(tree, capsys)
    assert code == 1 and "catalogue-members.txt" in err


def test_parity_rejects_a_reordered_members_inventory(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    tree = _tree(tmp_path)
    contracts = tree[0]
    (contracts / "c.schema.json").write_text("{}", encoding="utf-8")
    manifest = contracts / "catalogue-spec.toml"
    manifest.write_text(manifest.read_text() + _row("c.schema.json"), encoding="utf-8")
    shutil.copyfile(contracts / "c.schema.json", tree[1] / "c.schema.json")
    (tree[1] / "public-contracts.txt").write_text(
        "a.schema.json\nb.toml\nc.schema.json\n", encoding="utf-8"
    )
    (tree[1] / "catalogue-members.txt").write_text(
        "c.schema.json\na.schema.json\n", encoding="utf-8"
    )
    code, err = _run(tree, capsys)
    assert code == 1 and "catalogue-members.txt" in err


def test_real_snapshot_matches_the_release_row() -> None:
    generator = _generator()
    contracts = REPO_ROOT / "contracts"
    (row,) = generator.load_releases(contracts)[0]
    snap = generator.snapshot_dir(contracts, row.version)
    assert len(row.members) == 10
    for table in (row.members, row.pages):
        for name, digest in table.items():
            assert generator.sha256_of(snap / name) == digest
    assert set(row.pages) == {
        p.name for p in (REPO_ROOT / "docs-site" / "spec-src" / "catalogue").iterdir()
    }
    on_disk = {p.relative_to(snap).as_posix() for p in snap.rglob("*") if p.is_file()}
    assert on_disk == set(row.members) | set(row.pages)
    for name in row.members:
        assert (snap / name).read_bytes() == (contracts / name).read_bytes()


def test_overview_is_final_before_the_snapshot_and_reads_right_at_both_paths() -> None:
    text = (REPO_ROOT / "docs-site" / "spec-src" / "catalogue" / "overview.md").read_text(
        encoding="utf-8"
    )
    lowered = text.lower()
    assert "draft of the" not in lowered and "is the draft" not in lowered
    assert "no released version" not in lowered
    for needle in (
        "pin a versioned url",
        "latest/",
        "draft/",
        "record each digest in your own repository",
        "`_data/` copy in the matching pypi wheel",
        "`agentbundle-v*` tag",
        "vendor the file",
        "same deploy",
    ):
        assert needle in lowered, needle
