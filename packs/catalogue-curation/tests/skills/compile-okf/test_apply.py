"""Apply/check tests for compile-okf generated output ownership."""

from __future__ import annotations

import json
import re
import shutil
import sys
from collections.abc import Mapping
from dataclasses import replace
from pathlib import Path

import pytest

SCRIPT_ROOT = (
    Path(__file__).resolve().parents[3]
    / ".apm"
    / "skills"
    / "compile-okf"
    / "scripts"
)
sys.path.insert(0, str(SCRIPT_ROOT))

import okf_compiler  # noqa: E402
from okf_compiler import (  # noqa: E402
    PACK_TOML_MAX_BYTES,
    PRIOR_MANIFEST_MAX_BYTES,
    compile_pack,
    review_projection_digest,
)

FIXTURE_ROOT = Path(__file__).parent / "fixtures" / "render" / "rich"


class _ReparseStat:
    def __init__(self, wrapped: object) -> None:
        self._wrapped = wrapped
        self.st_file_attributes = 0x400

    def __getattr__(self, name: str) -> object:
        return getattr(self._wrapped, name)


def _make_catalogue(tmp_path: Path) -> Path:
    root = tmp_path / "catalogue"
    bundle = root / "packs" / "demo" / "okf" / "rich"
    shutil.copytree(FIXTURE_ROOT, bundle)
    (bundle / "empty").mkdir(exist_ok=True)
    digest = review_projection_digest(
        bundle,
        concept_path="concepts/runbook.md",
        skill_name="reviewed-runbook",
        activation_description="Use when a reviewed runbook should guide an operator.",
        instruction_section="Procedure",
        includes=("guides/include.md",),
    )
    (root / "packs" / "demo" / "pack.toml").write_text(
        "\n".join(
            [
                "[pack]",
                'name = "demo"',
                "",
                "[pack.metadata.okf]",
                'profile = "agentbundle-okf/v1"',
                "",
                "[[pack.metadata.okf.bundles]]",
                'id = "rich"',
                'path = "okf/rich"',
                '"router-skill" = "rich-router"',
                "",
                "[[pack.metadata.okf.bundles.projected-concepts]]",
                'path = "concepts/runbook.md"',
                f'"reviewed-projection-digest" = "{digest}"',
                "",
            ]
        ),
        encoding="utf-8",
    )
    return root


def _add_second_bundle(root: Path, *, router_skill: str = "second-router") -> None:
    source = root / "packs" / "demo" / "okf" / "rich"
    second = root / "packs" / "demo" / "okf" / "second"
    shutil.copytree(source, second)
    pack_toml = root / "packs" / "demo" / "pack.toml"
    pack_toml.write_text(
        pack_toml.read_text(encoding="utf-8")
        + "\n".join(
            [
                "",
                "[[pack.metadata.okf.bundles]]",
                'id = "second"',
                'path = "okf/second"',
                f'"router-skill" = "{router_skill}"',
                "",
            ]
        ),
        encoding="utf-8",
    )


def _snapshot(root: Path) -> dict[str, bytes]:
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def test_write_mode_applies_only_selected_pack_outputs(tmp_path: Path) -> None:
    root = _make_catalogue(tmp_path)

    result = compile_pack(root, "demo", check=False)

    assert result.exit_code == 0
    pack = root / "packs" / "demo"
    assert (pack / ".apm" / "skills" / "rich-router" / "SKILL.md").is_file()
    assert (pack / ".apm" / "skills" / "reviewed-runbook" / "SKILL.md").is_file()
    assert (pack / ".okf-generated.json").is_file()
    manifest = json.loads((pack / ".okf-generated.json").read_text(encoding="utf-8"))
    assert manifest["profile"] == "agentbundle-okf/v1"
    assert not (root / "packs" / "other").exists()


@pytest.mark.parametrize("drift", ["extra-key", "same-keys-different-bytes"])
def test_repeated_compile_mismatch_returns_okf012_without_mutation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    drift: str,
) -> None:
    # STUB: AC4 — the repeated-render guard is observable before pack mutation.
    # Both drift shapes matter. `extra-key` alone would leave the guard's value
    # comparison unpinned: narrowing `first.files != second.files` to
    # `set(first.files) != set(second.files)` keeps a key-only test green while
    # deleting half the contract. `same-keys-different-bytes` is also the likelier
    # real nondeterminism — an embedded timestamp or a digest over an unordered set.
    root = _make_catalogue(tmp_path)
    before = _snapshot(root)
    real_render = okf_compiler.render_okf_bundle
    calls = 0

    def render_differently_on_second_call(
        bundle_root: Path,
        *,
        bundle_id: str,
        router_skill: str,
        projected_concepts: Mapping[str, str],
    ) -> okf_compiler.RenderResult:
        nonlocal calls
        calls += 1
        rendered = real_render(
            bundle_root,
            bundle_id=bundle_id,
            router_skill=router_skill,
            projected_concepts=projected_concepts,
        )
        if calls != 2:
            return rendered
        if drift == "extra-key":
            files = {**rendered.files, "nondeterministic.md": b"second render\n"}
        else:
            mutated = dict(rendered.files)
            key = sorted(mutated)[0]
            mutated[key] = mutated[key] + b"\n<!-- second render -->\n"
            assert set(mutated) == set(rendered.files)
            files = mutated
        return replace(rendered, files=files)

    monkeypatch.setattr(okf_compiler, "render_okf_bundle", render_differently_on_second_call)

    result = compile_pack(root, "demo", check=False)

    assert result.exit_code == 2
    assert [diagnostic.code for diagnostic in result.diagnostics] == ["OKF012"]
    assert _snapshot(root) == before


def test_write_mode_fails_closed_without_safe_dir_fd_and_check_remains_read_only(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = _make_catalogue(tmp_path)
    assert compile_pack(root, "demo", check=False).exit_code == 0
    before = _snapshot(root)
    monkeypatch.setattr(okf_compiler, "_SAFE_DIR_FD_SUPPORTED", False)

    write_result = compile_pack(root, "demo", check=False)
    check_result = compile_pack(root, "demo", check=True)

    assert write_result.exit_code == 1
    assert [item.code for item in write_result.diagnostics] == ["OKF010"]
    assert "safe managed output writes are unavailable" in write_result.stderr
    assert check_result.exit_code == 0
    assert check_result.diagnostics == ()
    assert _snapshot(root) == before


@pytest.mark.parametrize("original", [None, b"original bytes"])
def test_rollback_fails_closed_without_safe_dir_fd_before_mutation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    original: bytes | None,
) -> None:
    root = _make_catalogue(tmp_path)
    pack = root / "packs" / "demo"
    relative_path = ".apm/skills/example/SKILL.md"
    target = pack / relative_path
    target.parent.mkdir(parents=True)
    target.write_bytes(b"current bytes")
    before = _snapshot(root)
    monkeypatch.setattr(okf_compiler, "_SAFE_DIR_FD_SUPPORTED", False)

    with pytest.raises(ValueError, match="safe managed output"):
        okf_compiler._restore_managed_outputs(pack, {relative_path: original})

    assert _snapshot(root) == before


@pytest.mark.parametrize(
    "pack",
    [
        "/demo",
        "../demo",
        "nested/demo",
        "nested\\demo",
        "CON",
        "demo.",
        "demo ",
    ],
)
def test_cli_pack_name_must_be_one_safe_direct_child_segment(
    tmp_path: Path,
    pack: str,
) -> None:
    root = _make_catalogue(tmp_path)
    before = _snapshot(root)

    result = compile_pack(root, pack, check=False)

    assert result.exit_code == 1
    assert [diagnostic.code for diagnostic in result.diagnostics] == ["OKF001"]
    assert _snapshot(root) == before


def test_pack_root_symlink_is_rejected_before_read_or_mutation(tmp_path: Path) -> None:
    root = _make_catalogue(tmp_path)
    link = root / "packs" / "linked-demo"
    link.symlink_to(root / "packs" / "demo", target_is_directory=True)
    before = _snapshot(root)

    result = compile_pack(root, "linked-demo", check=False)

    assert result.exit_code == 1
    assert [diagnostic.code for diagnostic in result.diagnostics] == ["OKF004"]
    assert _snapshot(root) == before


@pytest.mark.parametrize(
    ("relative_path", "expected_code"),
    [
        ("pack.toml", "OKF001"),
        (".okf-generated.json", "OKF010"),
    ],
)
def test_metadata_symlink_is_rejected_before_read_or_mutation(
    tmp_path: Path,
    relative_path: str,
    expected_code: str,
) -> None:
    root = _make_catalogue(tmp_path)
    pack = root / "packs" / "demo"
    if relative_path == ".okf-generated.json":
        assert compile_pack(root, "demo", check=False).exit_code == 0
    target = pack / relative_path
    outside = tmp_path / f"outside-{target.name}"
    outside.write_bytes(target.read_bytes())
    target.unlink()
    target.symlink_to(outside)
    before = _snapshot(root)

    result = compile_pack(root, "demo", check=False)

    assert result.exit_code == 1
    assert [item.code for item in result.diagnostics] == [expected_code]
    assert target.is_symlink()
    assert target.read_bytes() == outside.read_bytes()
    assert _snapshot(root) == before


@pytest.mark.parametrize(
    ("relative_path", "expected_code"),
    [
        ("pack.toml", "OKF001"),
        (".okf-generated.json", "OKF010"),
    ],
)
def test_metadata_hardlink_is_rejected_before_read_or_mutation(
    tmp_path: Path,
    relative_path: str,
    expected_code: str,
) -> None:
    root = _make_catalogue(tmp_path)
    pack = root / "packs" / "demo"
    if relative_path == ".okf-generated.json":
        assert compile_pack(root, "demo", check=False).exit_code == 0
    target = pack / relative_path
    outside = tmp_path / f"outside-{target.name}"
    target.replace(outside)
    target.hardlink_to(outside)
    before = _snapshot(root)

    result = compile_pack(root, "demo", check=False)

    assert result.exit_code == 1
    assert [item.code for item in result.diagnostics] == [expected_code]
    assert _snapshot(root) == before


@pytest.mark.parametrize(
    ("relative_path", "expected_code"),
    [
        ("pack.toml", "OKF001"),
        (".okf-generated.json", "OKF010"),
    ],
)
def test_metadata_swap_between_inspection_and_open_is_rejected(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    relative_path: str,
    expected_code: str,
) -> None:
    root = _make_catalogue(tmp_path)
    pack = root / "packs" / "demo"
    if relative_path == ".okf-generated.json":
        assert compile_pack(root, "demo", check=False).exit_code == 0
    target = pack / relative_path
    outside = tmp_path / f"outside-{target.name}"
    outside.write_bytes(target.read_bytes())
    original_open = okf_compiler.os.open
    swapped = False

    def swap_then_open(path: object, flags: int) -> int:
        nonlocal swapped
        if Path(path) == target and not swapped:
            swapped = True
            target.unlink()
            target.symlink_to(outside)
        return original_open(path, flags)

    monkeypatch.setattr(okf_compiler.os, "open", swap_then_open)

    result = compile_pack(root, "demo", check=False)

    assert swapped
    assert result.exit_code == 1
    assert [item.code for item in result.diagnostics] == [expected_code]
    assert target.is_symlink()
    assert outside.is_file()


@pytest.mark.parametrize(
    ("relative_path", "max_bytes", "expected_code"),
    [
        ("pack.toml", PACK_TOML_MAX_BYTES, "OKF001"),
        (".okf-generated.json", PRIOR_MANIFEST_MAX_BYTES, "OKF010"),
    ],
)
def test_metadata_reads_reject_oversized_files_before_allocation(
    tmp_path: Path,
    relative_path: str,
    max_bytes: int,
    expected_code: str,
) -> None:
    root = _make_catalogue(tmp_path)
    pack = root / "packs" / "demo"
    if relative_path == ".okf-generated.json":
        assert compile_pack(root, "demo", check=False).exit_code == 0
    target = pack / relative_path
    target.write_bytes(b"x" * (max_bytes + 1))
    before = _snapshot(root)

    result = compile_pack(root, "demo", check=False)

    assert result.exit_code == 1
    assert [item.code for item in result.diagnostics] == [expected_code]
    assert _snapshot(root) == before


@pytest.mark.parametrize(
    "number",
    [
        pytest.param("NaN", id="nan"),
        pytest.param("Infinity", id="positive-infinity"),
        pytest.param("-Infinity", id="negative-infinity"),
        pytest.param("1e999", id="overflowing-float"),
        pytest.param("9" * 129, id="oversized-integer"),
    ],
)
def test_prior_manifest_rejects_non_finite_and_oversized_numbers_stably(
    tmp_path: Path,
    number: str,
) -> None:
    root = _make_catalogue(tmp_path)
    assert compile_pack(root, "demo", check=False).exit_code == 0
    manifest = root / "packs" / "demo" / ".okf-generated.json"
    original = manifest.read_text(encoding="utf-8")
    manifest.write_text(original.replace("{", f'{{"probe":{number},', 1), encoding="utf-8")
    before = _snapshot(root)

    result = compile_pack(root, "demo", check=True)

    assert result.exit_code == 1
    assert result.stderr == (
        "OKF010 packs/demo/.okf-generated.json invalid or unsafe manifest\n"
    )
    assert _snapshot(root) == before


@pytest.mark.parametrize(
    ("target_kind", "expected_code"),
    [
        ("pack-toml", "OKF001"),
        ("bundle-directory", "OKF004"),
        ("output-directory", "OKF010"),
    ],
)
def test_real_reparse_stat_attribute_is_rejected_at_compiler_boundaries(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    target_kind: str,
    expected_code: str,
) -> None:
    root = _make_catalogue(tmp_path)
    pack = root / "packs" / "demo"
    if target_kind == "output-directory":
        assert compile_pack(root, "demo", check=False).exit_code == 0
    targets = {
        "pack-toml": pack / "pack.toml",
        "bundle-directory": pack / "okf" / "rich",
        "output-directory": pack / ".apm" / "skills" / "rich-router",
    }
    suspicious = targets[target_kind]
    original_lstat = Path.lstat

    def mark_reparse(path: Path) -> object:
        info = original_lstat(path)
        return _ReparseStat(info) if path == suspicious else info

    monkeypatch.setattr(Path, "lstat", mark_reparse)

    result = compile_pack(root, "demo", check=False)

    assert result.exit_code == 1
    assert [item.code for item in result.diagnostics] == [expected_code]


def test_bundle_root_symlink_component_is_rejected_before_scan_or_mutation(
    tmp_path: Path,
) -> None:
    root = _make_catalogue(tmp_path)
    bundle = root / "packs" / "demo" / "okf" / "rich"
    real = root / "real-bundle"
    shutil.move(str(bundle), real)
    bundle.symlink_to(real, target_is_directory=True)
    before = _snapshot(root)

    result = compile_pack(root, "demo", check=False)

    assert result.exit_code == 1
    assert [diagnostic.code for diagnostic in result.diagnostics] == ["OKF004"]
    assert _snapshot(root) == before


def test_pack_manifest_derives_generic_paths_digests_and_kinds(tmp_path: Path) -> None:
    root = tmp_path / "catalogue"
    bundle = root / "packs" / "cost-engineering" / "okf" / "cost-engineering"
    bundle.mkdir(parents=True)
    (bundle / "index.md").write_text(
        '---\nokf_version: "0.2"\n---\n'
        "<!-- agentbundle-managed: profile=agentbundle-okf/v1 kind=okf-index -->\n"
        "# Cost engineering\n",
        encoding="utf-8",
    )
    concepts = bundle / "concepts"
    concepts.mkdir()
    (concepts / "unit-economics.md").write_text(
        "---\n"
        'title: "Unit economics"\n'
        'type: "Reference"\n'
        'status: "Active"\n'
        "---\n"
        "# Unit economics\n",
        encoding="utf-8",
    )
    (root / "packs" / "cost-engineering" / "pack.toml").write_text(
        "\n".join(
            [
                "[pack]",
                'name = "cost-engineering"',
                "",
                "[pack.metadata.okf]",
                'profile = "agentbundle-okf/v1"',
                "",
                "[[pack.metadata.okf.bundles]]",
                'id = "cost-engineering"',
                'path = "okf/cost-engineering"',
                '"router-skill" = "cost-engineering"',
                "",
            ]
        ),
        encoding="utf-8",
    )

    result = compile_pack(root, "cost-engineering", check=False)

    assert result.exit_code == 0
    manifest = json.loads(
        (root / "packs" / "cost-engineering" / ".okf-generated.json").read_text(
            encoding="utf-8"
        )
    )
    records = {record["output_path"]: record for record in manifest["managed"]}
    router = records[".apm/skills/cost-engineering/SKILL.md"]
    concept = records[
        ".apm/skills/cost-engineering/references/okf/concepts/unit-economics.md"
    ]

    assert router["kind"] == "okf-router"
    assert router["source_path"] == "okf/cost-engineering"
    assert router["source_digest"].startswith("sha256:")
    assert router["source_digest"] != "sha256:" + "0" * 64
    assert concept["kind"] == "okf-reference"
    assert concept["source_path"] == "okf/cost-engineering/concepts/unit-economics.md"
    assert concept["source_digest"] == concept["digest"]


def test_compile_pack_merges_every_declared_bundle_deterministically(tmp_path: Path) -> None:
    root = _make_catalogue(tmp_path)
    _add_second_bundle(root)

    first = compile_pack(root, "demo", check=False)
    first_snapshot = _snapshot(root)
    clean = compile_pack(root, "demo", check=True)
    second = compile_pack(root, "demo", check=False)

    assert first.exit_code == 0
    assert clean.exit_code == 0
    assert second.exit_code == 0
    assert _snapshot(root) == first_snapshot
    pack = root / "packs" / "demo"
    assert (pack / ".apm" / "skills" / "rich-router" / "SKILL.md").is_file()
    assert (pack / ".apm" / "skills" / "second-router" / "SKILL.md").is_file()
    manifest = json.loads((pack / ".okf-generated.json").read_text(encoding="utf-8"))
    records = {record["output_path"]: record for record in manifest["managed"]}
    assert records[".apm/skills/rich-router/SKILL.md"]["source_path"] == "okf/rich"
    assert records[".apm/skills/second-router/SKILL.md"]["source_path"] == "okf/second"


def test_compile_pack_hands_a_renamed_router_back_to_its_author(tmp_path: Path) -> None:
    root = _make_catalogue(tmp_path)
    pack = root / "packs" / "demo"
    assert compile_pack(root, "demo", check=False).exit_code == 0

    former_router = pack / ".apm" / "skills" / "rich-router" / "SKILL.md"
    former_router.write_text(
        f"{okf_compiler.ROUTER_HANDOFF_MARKER}\n# Hand-authored routing authority\n",
        encoding="utf-8",
    )
    direct_reference = former_router.parent / "references" / "direct-routing.md"
    direct_reference.write_text("# Direct routing reference\n", encoding="utf-8")
    manifest = pack / "pack.toml"
    manifest.write_text(
        manifest.read_text(encoding="utf-8").replace(
            '"router-skill" = "rich-router"',
            '"router-skill" = "rich-router-okf"',
        ),
        encoding="utf-8",
    )

    result = compile_pack(root, "demo", check=False)

    assert result.exit_code == 0
    assert former_router.read_text(encoding="utf-8") == (
        f"{okf_compiler.ROUTER_HANDOFF_MARKER}\n# Hand-authored routing authority\n"
    )
    assert direct_reference.read_text(encoding="utf-8") == "# Direct routing reference\n"
    assert not (former_router.parent / "references" / "okf").exists()
    assert (pack / ".apm" / "skills" / "rich-router-okf" / "SKILL.md").is_file()
    assert compile_pack(root, "demo", check=True).exit_code == 0


def test_router_handoff_refuses_to_remove_modified_generated_references(tmp_path: Path) -> None:
    root = _make_catalogue(tmp_path)
    pack = root / "packs" / "demo"
    assert compile_pack(root, "demo", check=False).exit_code == 0

    former_router = pack / ".apm" / "skills" / "rich-router" / "SKILL.md"
    former_router.write_text(
        f"{okf_compiler.ROUTER_HANDOFF_MARKER}\n# Hand-authored routing authority\n",
        encoding="utf-8",
    )
    stale_reference = former_router.parent / "references" / "okf" / "concepts" / "runbook.md"
    stale_reference.write_text("modified generated reference\n", encoding="utf-8")
    manifest = pack / "pack.toml"
    manifest.write_text(
        manifest.read_text(encoding="utf-8").replace(
            '"router-skill" = "rich-router"',
            '"router-skill" = "rich-router-okf"',
        ),
        encoding="utf-8",
    )

    result = compile_pack(root, "demo", check=False)

    assert result.exit_code == 1
    assert [diagnostic.code for diagnostic in result.diagnostics] == ["OKF010"]
    assert stale_reference.read_text(encoding="utf-8") == "modified generated reference\n"


def test_router_handoff_requires_an_explicit_author_marker(tmp_path: Path) -> None:
    root = _make_catalogue(tmp_path)
    pack = root / "packs" / "demo"
    assert compile_pack(root, "demo", check=False).exit_code == 0

    former_router = pack / ".apm" / "skills" / "rich-router" / "SKILL.md"
    former_router.write_text("# Corrupted generated router\n", encoding="utf-8")
    manifest = pack / "pack.toml"
    manifest.write_text(
        manifest.read_text(encoding="utf-8").replace(
            '"router-skill" = "rich-router"',
            '"router-skill" = "rich-router-okf"',
        ),
        encoding="utf-8",
    )

    result = compile_pack(root, "demo", check=False)

    assert result.exit_code == 1
    assert [diagnostic.code for diagnostic in result.diagnostics] == ["OKF010"]
    assert former_router.read_text(encoding="utf-8") == "# Corrupted generated router\n"


def test_router_handoff_refuses_a_removed_source(tmp_path: Path) -> None:
    """A deleted bundle source is not a rename; its managed output must not be ceded.

    `current_routers.get(source_path)` returns None once a source is no longer
    declared. Comparing that to the former router with `!=` reads a removal as a
    rename, so the old marked SKILL.md would be handed to the author and escape
    ownership cleanup.
    """
    root = _make_catalogue(tmp_path)
    _add_second_bundle(root)
    pack = root / "packs" / "demo"
    assert compile_pack(root, "demo", check=False).exit_code == 0

    former_router = pack / ".apm" / "skills" / "rich-router" / "SKILL.md"
    former_router.write_text(
        f"{okf_compiler.ROUTER_HANDOFF_MARKER}\n# Hand-authored routing authority\n",
        encoding="utf-8",
    )
    manifest = pack / "pack.toml"
    prefix, separator, bundles = manifest.read_text(encoding="utf-8").partition(
        "\n[[pack.metadata.okf.bundles]]\n"
    )
    _, second_separator, second_bundle = bundles.partition(
        "\n[[pack.metadata.okf.bundles]]\n"
    )
    assert separator and second_separator
    manifest.write_text(prefix + second_separator + second_bundle, encoding="utf-8")

    result = compile_pack(root, "demo", check=False)

    assert result.exit_code == 1
    assert [diagnostic.code for diagnostic in result.diagnostics] == ["OKF010"]
    assert former_router.read_text(encoding="utf-8") == (
        f"{okf_compiler.ROUTER_HANDOFF_MARKER}\n# Hand-authored routing authority\n"
    )


def test_router_handoff_supports_a_renamed_router_in_a_multi_bundle_pack(
    tmp_path: Path,
) -> None:
    root = _make_catalogue(tmp_path)
    _add_second_bundle(root)
    pack = root / "packs" / "demo"
    assert compile_pack(root, "demo", check=False).exit_code == 0

    former_router = pack / ".apm" / "skills" / "rich-router" / "SKILL.md"
    former_router.write_text(
        f"{okf_compiler.ROUTER_HANDOFF_MARKER}\n# Hand-authored routing authority\n",
        encoding="utf-8",
    )
    manifest = pack / "pack.toml"
    manifest.write_text(
        manifest.read_text(encoding="utf-8").replace(
            '"router-skill" = "rich-router"',
            '"router-skill" = "rich-router-reference"',
        ),
        encoding="utf-8",
    )

    result = compile_pack(root, "demo", check=False)

    assert result.exit_code == 0
    assert former_router.is_file()
    assert (pack / ".apm" / "skills" / "rich-router-reference" / "SKILL.md").is_file()
    assert (pack / ".apm" / "skills" / "second-router" / "SKILL.md").is_file()


def test_compile_pack_removes_an_unmodified_router_after_a_rename(tmp_path: Path) -> None:
    root = _make_catalogue(tmp_path)
    pack = root / "packs" / "demo"
    assert compile_pack(root, "demo", check=False).exit_code == 0

    manifest = pack / "pack.toml"
    manifest.write_text(
        manifest.read_text(encoding="utf-8").replace(
            '"router-skill" = "rich-router"',
            '"router-skill" = "rich-router-reference"',
        ),
        encoding="utf-8",
    )

    result = compile_pack(root, "demo", check=False)

    assert result.exit_code == 0
    assert not (pack / ".apm" / "skills" / "rich-router").exists()
    assert (pack / ".apm" / "skills" / "rich-router-reference" / "SKILL.md").is_file()


def test_compile_pack_rejects_cross_bundle_router_collision_without_mutation(
    tmp_path: Path,
) -> None:
    root = _make_catalogue(tmp_path)
    _add_second_bundle(root, router_skill="rich-router")
    before = _snapshot(root)

    result = compile_pack(root, "demo", check=False)

    assert result.exit_code == 1
    assert [diagnostic.code for diagnostic in result.diagnostics] == ["OKF006"]
    assert _snapshot(root) == before


def test_compile_pack_rejects_router_procedure_collision_without_mutation(
    tmp_path: Path,
) -> None:
    root = _make_catalogue(tmp_path)
    pack_toml = root / "packs" / "demo" / "pack.toml"
    pack_toml.write_text(
        pack_toml.read_text(encoding="utf-8").replace(
            '"router-skill" = "rich-router"',
            '"router-skill" = "reviewed-runbook"',
        ),
        encoding="utf-8",
    )
    before = _snapshot(root)

    result = compile_pack(root, "demo", check=False)

    assert result.exit_code == 1
    assert [diagnostic.code for diagnostic in result.diagnostics] == ["OKF006"]
    assert _snapshot(root) == before


def test_compile_pack_rejects_colliding_include_basenames_without_mutation(
    tmp_path: Path,
) -> None:
    root = _make_catalogue(tmp_path)
    bundle = root / "packs" / "demo" / "okf" / "rich"
    duplicate = bundle / "other" / "include.md"
    duplicate.parent.mkdir()
    duplicate.write_text("duplicate basename\n", encoding="utf-8")
    concept = bundle / "concepts" / "runbook.md"
    concept.write_text(
        concept.read_text(encoding="utf-8").replace(
            "      - guides/include.md",
            "      - guides/include.md\n      - other/include.md",
        ),
        encoding="utf-8",
    )
    digest = review_projection_digest(
        bundle,
        concept_path="concepts/runbook.md",
        skill_name="reviewed-runbook",
        activation_description="Use when a reviewed runbook should guide an operator.",
        instruction_section="Procedure",
        includes=("guides/include.md", "other/include.md"),
    )
    pack_toml = root / "packs" / "demo" / "pack.toml"
    pack_toml.write_text(
        re.sub(
            r'"reviewed-projection-digest" = "sha256:[0-9a-f]{64}"',
            f'"reviewed-projection-digest" = "{digest}"',
            pack_toml.read_text(encoding="utf-8"),
        ),
        encoding="utf-8",
    )
    before = _snapshot(root)

    result = compile_pack(root, "demo", check=False)

    assert result.exit_code == 1
    assert [diagnostic.code for diagnostic in result.diagnostics] == ["OKF006"]
    assert _snapshot(root) == before


def test_invalid_pack_profile_contract_fails_before_mutation(tmp_path: Path) -> None:
    root = _make_catalogue(tmp_path)
    pack_toml = root / "packs" / "demo" / "pack.toml"
    pack_toml.write_text(
        pack_toml.read_text(encoding="utf-8").replace('path = "okf/rich"', 'path = "../rich"'),
        encoding="utf-8",
    )
    before = _snapshot(root)

    result = compile_pack(root, "demo", check=False)

    assert result.exit_code == 1
    assert [diagnostic.code for diagnostic in result.diagnostics] == ["OKF001"]
    assert _snapshot(root) == before


def test_invalid_agentbundle_extension_fails_before_mutation(tmp_path: Path) -> None:
    root = _make_catalogue(tmp_path)
    concept = root / "packs" / "demo" / "okf" / "rich" / "concepts" / "runbook.md"
    concept.write_text(
        concept.read_text(encoding="utf-8").replace("name: reviewed-runbook", "name: ../escape"),
        encoding="utf-8",
    )
    before = _snapshot(root)

    result = compile_pack(root, "demo", check=False)

    assert result.exit_code == 1
    assert [diagnostic.code for diagnostic in result.diagnostics] == ["OKF007"]
    assert _snapshot(root) == before


@pytest.mark.parametrize("include", ["guides/missing.md", "guides"])
def test_projected_includes_resolve_from_scanned_regular_files_without_mutation(
    tmp_path: Path,
    include: str,
) -> None:
    root = _make_catalogue(tmp_path)
    concept = root / "packs" / "demo" / "okf" / "rich" / "concepts" / "runbook.md"
    concept.write_text(
        concept.read_text(encoding="utf-8").replace(
            "      - guides/include.md",
            f"      - {include}",
        ),
        encoding="utf-8",
    )
    before = _snapshot(root)

    result = compile_pack(root, "demo", check=False)

    assert result.exit_code == 1
    assert [diagnostic.code for diagnostic in result.diagnostics] == ["OKF004"]
    assert _snapshot(root) == before


def test_projected_procedure_requires_playbook_concept_without_mutation(tmp_path: Path) -> None:
    root = _make_catalogue(tmp_path)
    concept = root / "packs" / "demo" / "okf" / "rich" / "concepts" / "runbook.md"
    concept.write_text(
        concept.read_text(encoding="utf-8").replace("type: Playbook", "type: Reference"),
        encoding="utf-8",
    )
    before = _snapshot(root)

    result = compile_pack(root, "demo", check=False)

    assert result.exit_code == 1
    assert [diagnostic.code for diagnostic in result.diagnostics] == ["OKF007"]
    assert _snapshot(root) == before


def test_check_mode_reports_drift_without_mutation(tmp_path: Path) -> None:
    root = _make_catalogue(tmp_path)
    before = _snapshot(root)

    result = compile_pack(root, "demo", check=True)

    assert result.exit_code == 2
    assert [diagnostic.code for diagnostic in result.diagnostics] == ["OKF011"]
    assert _snapshot(root) == before


def test_clean_check_passes_after_write_and_repeated_write_is_identical(tmp_path: Path) -> None:
    root = _make_catalogue(tmp_path)

    first = compile_pack(root, "demo", check=False)
    first_snapshot = _snapshot(root)
    second = compile_pack(root, "demo", check=False)
    clean_check = compile_pack(root, "demo", check=True)

    assert first.exit_code == 0
    assert second.exit_code == 0
    assert clean_check.exit_code == 0
    assert _snapshot(root) == first_snapshot


def test_generated_output_drift_is_exit_2_and_check_is_read_only(tmp_path: Path) -> None:
    root = _make_catalogue(tmp_path)
    compile_pack(root, "demo", check=False)
    target = root / "packs" / "demo" / ".apm" / "skills" / "rich-router" / "SKILL.md"
    target.write_text(target.read_text(encoding="utf-8") + "\nmanual drift\n", encoding="utf-8")
    before = _snapshot(root)

    result = compile_pack(root, "demo", check=True)

    assert result.exit_code == 2
    assert [diagnostic.code for diagnostic in result.diagnostics] == ["OKF011"]
    assert _snapshot(root) == before


@pytest.mark.parametrize(
    ("check", "expected_code"),
    [(True, "OKF011"), (False, "OKF010")],
)
def test_managed_output_swap_between_inspection_and_open_is_rejected(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    check: bool,
    expected_code: str,
) -> None:
    root = _make_catalogue(tmp_path)
    assert compile_pack(root, "demo", check=False).exit_code == 0
    target = root / "packs" / "demo" / ".apm" / "skills" / "rich-router" / "SKILL.md"
    outside = tmp_path / "outside-managed-output"
    outside.write_bytes(target.read_bytes())
    original_open = okf_compiler.os.open
    swapped = False

    def swap_then_open(path: object, flags: int, *args: object, **kwargs: object) -> int:
        nonlocal swapped
        if Path(path) == target and not swapped:
            swapped = True
            target.unlink()
            target.symlink_to(outside)
        return original_open(path, flags, *args, **kwargs)

    monkeypatch.setattr(okf_compiler.os, "open", swap_then_open)

    result = compile_pack(root, "demo", check=check)

    assert swapped
    assert result.exit_code == (2 if check else 1)
    assert [item.code for item in result.diagnostics] == [expected_code]
    assert target.is_symlink()
    assert outside.is_file()


@pytest.mark.parametrize(
    ("check", "expected_code"),
    [(True, "OKF011"), (False, "OKF010")],
)
def test_managed_output_reads_reject_oversized_files(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    check: bool,
    expected_code: str,
) -> None:
    root = _make_catalogue(tmp_path)
    assert compile_pack(root, "demo", check=False).exit_code == 0
    target = root / "packs" / "demo" / ".apm" / "skills" / "rich-router" / "SKILL.md"
    monkeypatch.setattr(okf_compiler, "MANAGED_OUTPUT_MAX_BYTES", 1024 * 1024)
    target.write_bytes(b"x" * (okf_compiler.MANAGED_OUTPUT_MAX_BYTES + 1))
    expected_size = target.stat().st_size

    result = compile_pack(root, "demo", check=check)

    assert result.exit_code == (2 if check else 1)
    assert [item.code for item in result.diagnostics] == [expected_code]
    assert target.stat().st_size == expected_size


def test_ownership_conflict_stops_before_mutation(tmp_path: Path) -> None:
    root = _make_catalogue(tmp_path)
    pack = root / "packs" / "demo"
    target = pack / ".apm" / "skills" / "rich-router" / "SKILL.md"
    target.parent.mkdir(parents=True)
    target.write_text("manual skill\n", encoding="utf-8")
    before = _snapshot(root)

    result = compile_pack(root, "demo", check=False)

    assert result.exit_code == 1
    assert [diagnostic.code for diagnostic in result.diagnostics] == ["OKF010"]
    assert _snapshot(root) == before


def test_existing_output_symlink_to_outside_is_rejected_without_mutation(
    tmp_path: Path,
) -> None:
    root = _make_catalogue(tmp_path)
    compile_pack(root, "demo", check=False)
    target = root / "packs" / "demo" / ".apm" / "skills" / "rich-router" / "SKILL.md"
    outside = tmp_path / "outside.md"
    outside.write_text("outside sentinel\n", encoding="utf-8")
    target.unlink()
    target.symlink_to(outside)
    before = _snapshot(root)

    result = compile_pack(root, "demo", check=False)

    assert result.exit_code == 1
    assert [diagnostic.code for diagnostic in result.diagnostics] == ["OKF010"]
    assert outside.read_text(encoding="utf-8") == "outside sentinel\n"
    assert target.is_symlink()
    assert _snapshot(root) == before


def test_dangling_output_symlink_is_rejected_without_outside_mutation(
    tmp_path: Path,
) -> None:
    root = _make_catalogue(tmp_path)
    target = root / "packs" / "demo" / ".apm" / "skills" / "rich-router" / "SKILL.md"
    target.parent.mkdir(parents=True)
    outside = tmp_path / "missing-outside.md"
    target.symlink_to(outside)
    before = _snapshot(root)

    result = compile_pack(root, "demo", check=False)

    assert result.exit_code == 1
    assert [diagnostic.code for diagnostic in result.diagnostics] == ["OKF010"]
    assert target.is_symlink()
    assert not outside.exists()
    assert _snapshot(root) == before


def test_dangling_output_parent_symlink_is_rejected_without_outside_mutation(
    tmp_path: Path,
) -> None:
    root = _make_catalogue(tmp_path)
    parent = root / "packs" / "demo" / ".apm" / "skills" / "rich-router"
    parent.parent.mkdir(parents=True)
    outside = tmp_path / "missing-outside-directory"
    parent.symlink_to(outside, target_is_directory=True)
    before = _snapshot(root)

    result = compile_pack(root, "demo", check=False)

    assert result.exit_code == 1
    assert [diagnostic.code for diagnostic in result.diagnostics] == ["OKF010"]
    assert parent.is_symlink()
    assert not outside.exists()
    assert _snapshot(root) == before


def test_stale_managed_output_is_removed_only_when_manifest_matches(tmp_path: Path) -> None:
    root = _make_catalogue(tmp_path)
    compile_pack(root, "demo", check=False)
    stale = root / "packs" / "demo" / ".apm" / "skills" / "old-generated" / "SKILL.md"
    stale.parent.mkdir()
    stale.write_text(
        "---\nname: old-generated\ndescription: old\nmetadata:\n  generated-by: compile-okf agentbundle-okf/v1\n---\n\n# Old\n",
        encoding="utf-8",
    )
    manifest_path = root / "packs" / "demo" / ".okf-generated.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["managed"].append(
        {
            "digest": "sha256:" + "0" * 64,
            "kind": "okf-procedure-skill",
            "marker": "generated-by: compile-okf agentbundle-okf/v1",
            "output_path": ".apm/skills/old-generated/SKILL.md",
            "source_digest": "sha256:" + "0" * 64,
            "source_path": "okf/rich",
        }
    )
    manifest_path.write_text(json.dumps(manifest, sort_keys=True) + "\n", encoding="utf-8")

    result = compile_pack(root, "demo", check=False)

    assert result.exit_code == 1
    assert [diagnostic.code for diagnostic in result.diagnostics] == ["OKF010"]
    assert stale.is_file()


def test_check_rejects_dangling_stale_managed_output(tmp_path: Path) -> None:
    root = _make_catalogue(tmp_path)
    assert compile_pack(root, "demo", check=False).exit_code == 0
    stale = root / "packs" / "demo" / ".apm" / "skills" / "old-generated" / "SKILL.md"
    stale.parent.mkdir()
    stale.symlink_to(tmp_path / "missing-stale.md")
    manifest_path = root / "packs" / "demo" / ".okf-generated.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["managed"].append(
        {
            "digest": "sha256:" + "0" * 64,
            "kind": "okf-procedure-skill",
            "marker": "generated-by: compile-okf agentbundle-okf/v1",
            "output_path": ".apm/skills/old-generated/SKILL.md",
            "source_digest": "sha256:" + "0" * 64,
            "source_path": "okf/rich",
        }
    )
    manifest_path.write_text(json.dumps(manifest, sort_keys=True) + "\n", encoding="utf-8")

    result = compile_pack(root, "demo", check=True)

    assert result.exit_code == 2
    assert [diagnostic.code for diagnostic in result.diagnostics] == ["OKF010"]
    assert stale.is_symlink()


def test_extra_file_in_prior_managed_skill_directory_blocks_stale_cleanup(
    tmp_path: Path,
) -> None:
    root = _make_catalogue(tmp_path)
    compile_pack(root, "demo", check=False)
    extra = root / "packs" / "demo" / ".apm" / "skills" / "rich-router" / "manual.md"
    extra.write_text("manual addition\n", encoding="utf-8")
    before = _snapshot(root)

    result = compile_pack(root, "demo", check=False)

    assert result.exit_code == 1
    assert [diagnostic.code for diagnostic in result.diagnostics] == ["OKF010"]
    assert _snapshot(root) == before


def test_dangling_extra_in_prior_managed_skill_directory_blocks_apply(
    tmp_path: Path,
) -> None:
    root = _make_catalogue(tmp_path)
    assert compile_pack(root, "demo", check=False).exit_code == 0
    extra = root / "packs" / "demo" / ".apm" / "skills" / "rich-router" / "dangling.md"
    outside = tmp_path / "missing-extra.md"
    extra.symlink_to(outside)
    before = _snapshot(root)

    result = compile_pack(root, "demo", check=False)

    assert result.exit_code == 1
    assert [diagnostic.code for diagnostic in result.diagnostics] == ["OKF010"]
    assert extra.is_symlink()
    assert not outside.exists()
    assert _snapshot(root) == before


def test_atomic_publish_replaces_leaf_swap_without_following_outside(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = _make_catalogue(tmp_path)
    assert compile_pack(root, "demo", check=False).exit_code == 0
    pack = root / "packs" / "demo"
    source = pack / "okf" / "rich" / "concepts" / "runbook.md"
    source.write_text(
        source.read_text(encoding="utf-8").replace(
            "title: Reviewed Runbook",
            "title: Updated Reviewed Runbook",
        ),
        encoding="utf-8",
    )
    target = pack / ".apm" / "skills" / "reviewed-runbook" / "SKILL.md"
    outside = tmp_path / "outside-leaf.md"
    outside.write_text("outside sentinel\n", encoding="utf-8")
    original_rename = okf_compiler.os.rename
    swapped = False

    def swap_leaf_then_rename(src: object, dst: object, **kwargs: object) -> None:
        nonlocal swapped
        if dst == "SKILL.md" and not swapped:
            swapped = True
            target.unlink()
            target.symlink_to(outside)
        original_rename(src, dst, **kwargs)

    monkeypatch.setattr(okf_compiler.os, "rename", swap_leaf_then_rename)

    result = compile_pack(root, "demo", check=False)

    assert swapped
    assert result.exit_code == 0
    assert outside.read_text(encoding="utf-8") == "outside sentinel\n"
    assert target.is_file() and not target.is_symlink()


def test_atomic_publish_parent_swap_fails_without_writing_outside(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = _make_catalogue(tmp_path)
    assert compile_pack(root, "demo", check=False).exit_code == 0
    pack = root / "packs" / "demo"
    source = pack / "okf" / "rich" / "concepts" / "runbook.md"
    source.write_text(
        source.read_text(encoding="utf-8").replace(
            "title: Reviewed Runbook",
            "title: Updated Reviewed Runbook",
        ),
        encoding="utf-8",
    )
    parent = pack / ".apm" / "skills" / "reviewed-runbook"
    moved = parent.with_name("reviewed-runbook-swapped")
    outside = tmp_path / "outside-parent"
    outside.mkdir()
    sentinel = outside / "sentinel.md"
    sentinel.write_text("outside sentinel\n", encoding="utf-8")
    original_rename = okf_compiler.os.rename
    swapped = False

    def swap_parent_then_rename(src: object, dst: object, **kwargs: object) -> None:
        nonlocal swapped
        if dst == "SKILL.md" and not swapped:
            swapped = True
            original_rename(parent, moved)
            parent.symlink_to(outside, target_is_directory=True)
        original_rename(src, dst, **kwargs)

    monkeypatch.setattr(okf_compiler.os, "rename", swap_parent_then_rename)

    result = compile_pack(root, "demo", check=False)

    assert swapped
    assert result.exit_code == 1
    assert [item.code for item in result.diagnostics] == ["OKF010"]
    assert sentinel.read_text(encoding="utf-8") == "outside sentinel\n"
    assert sorted(path.name for path in outside.iterdir()) == ["sentinel.md"]


def test_atomic_rollback_replaces_leaf_swap_without_following_outside(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = _make_catalogue(tmp_path)
    assert compile_pack(root, "demo", check=False).exit_code == 0
    pack = root / "packs" / "demo"
    target = pack / ".apm" / "skills" / "reviewed-runbook" / "SKILL.md"
    original = target.read_bytes()
    source = pack / "okf" / "rich" / "concepts" / "runbook.md"
    source.write_text(
        source.read_text(encoding="utf-8").replace(
            "title: Reviewed Runbook",
            "title: Updated Reviewed Runbook",
        ),
        encoding="utf-8",
    )
    outside = tmp_path / "outside-rollback.md"
    outside.write_text("outside sentinel\n", encoding="utf-8")
    original_rename = okf_compiler.os.rename
    rename_count = 0

    def swap_rollback_leaf(src: object, dst: object, **kwargs: object) -> None:
        nonlocal rename_count
        if dst == "SKILL.md":
            rename_count += 1
            if rename_count == 2:
                target.unlink()
                target.symlink_to(outside)
        original_rename(src, dst, **kwargs)

    monkeypatch.setattr(okf_compiler.os, "rename", swap_rollback_leaf)

    result = compile_pack(root, "demo", check=False, fail_after_operations=1)

    assert rename_count >= 2
    assert result.exit_code == 1
    assert target.read_bytes() == original
    assert not target.is_symlink()
    assert outside.read_text(encoding="utf-8") == "outside sentinel\n"


def test_malicious_manifest_stale_path_is_rejected_without_mutation(tmp_path: Path) -> None:
    root = _make_catalogue(tmp_path)
    compile_pack(root, "demo", check=False)
    manifest_path = root / "packs" / "demo" / ".okf-generated.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["managed"].append(
        {
            "digest": "sha256:" + "0" * 64,
            "kind": "okf-procedure-skill",
            "marker": "generated-by: compile-okf agentbundle-okf/v1",
            "output_path": "../escape/SKILL.md",
            "source_digest": "sha256:" + "0" * 64,
            "source_path": "okf/rich",
        }
    )
    manifest_path.write_text(json.dumps(manifest, sort_keys=True) + "\n", encoding="utf-8")
    before = _snapshot(root)

    result = compile_pack(root, "demo", check=False)

    assert result.exit_code == 1
    assert [diagnostic.code for diagnostic in result.diagnostics] == ["OKF010"]
    assert _snapshot(root) == before


def test_symlink_swap_and_partial_failure_leave_tree_unchanged(tmp_path: Path) -> None:
    root = _make_catalogue(tmp_path)
    assert compile_pack(root, "demo", check=False).exit_code == 0
    source = root / "packs" / "demo" / "okf" / "rich" / "concepts" / "runbook.md"
    source.write_text(
        source.read_text(encoding="utf-8").replace(
            "title: Reviewed Runbook",
            "title: Updated Reviewed Runbook",
        ),
        encoding="utf-8",
    )
    before = _snapshot(root)

    result = compile_pack(
        root,
        "demo",
        check=False,
        fail_after_operations=1,
    )

    assert result.exit_code == 1
    assert [diagnostic.code for diagnostic in result.diagnostics] == ["OKF010"]
    assert _snapshot(root) == before
