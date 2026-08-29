"""Unit tests for catalogue OKF discovery extraction."""

from __future__ import annotations

import hashlib
import json
import os
import socket
import stat
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
from agentbundle.catalogue_tooling import okf_discovery


def _canonical_json_bytes(value: Any) -> bytes:
    return (
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")


def _bytes_digest(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def _tree_digest(files: dict[str, bytes]) -> str:
    payload = [
        {"path": path, "sha256": _bytes_digest(data)}
        for path, data in sorted(files.items(), key=lambda item: item[0].encode("utf-8"))
    ]
    return _bytes_digest(_canonical_json_bytes(payload))


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def _base_pack(root: Path, *, okf: bool = True) -> Path:
    pack = root / "packs" / "demo"
    okf_block = ""
    if okf:
        okf_block = (
            "\n[pack.metadata.okf]\n"
            'profile = "agentbundle-okf/v1"\n'
            "\n[[pack.metadata.okf.bundles]]\n"
            'id = "demo"\n'
            'path = "okf/demo"\n'
            '"router-skill" = "demo-router"\n'
        )
    _write(
        pack / "pack.toml",
        "[pack]\n"
        'name = "demo"\n'
        'version = "1.0.0"\n'
        'license = "MIT"\n'
        'categories = ["tools", "Tools", "okf"]\n'
        'keywords = ["demo", "okf"]\n'
        f"{okf_block}",
    )
    _write(
        pack / ".apm" / "skills" / "manual-skill" / "SKILL.md",
        "---\n"
        "name: manual-skill\n"
        "description: Manual skill\n"
        "license: MIT\n"
        "compatibility:\n"
        "  adapter: claude-code\n"
        "  stable: true\n"
        "  max: 9007199254740991\n"
        "  modes: [repo, false, -9007199254740991]\n"
        "metadata:\n"
        "  boundaries:\n"
        "    - filesystem_read_untrusted\n"
        "---\n"
        "# Manual\n",
    )
    if okf:
        _write_okf_bundle(pack)
        _write_generated_router(pack)
    return pack


def _write_okf_bundle(pack: Path) -> None:
    _write(
        pack / "okf" / "demo" / "index.md",
        "---\n"
        'okf_version: "0.2"\n'
        'license: "Apache-2.0"\n'
        "---\n"
        "<!-- agentbundle-managed: profile=agentbundle-okf/v1 kind=okf-index -->\n"
        "# Demo\n",
    )
    _write(
        pack / "okf" / "demo" / "concepts" / "alpha.md",
        "---\n"
        'title: "Alpha"\n'
        'type: "Reference"\n'
        'status: "Active"\n'
        "---\n"
        "# Alpha\n",
    )
    _write(
        pack / "okf" / "demo" / "concepts" / "beta.md",
        "---\n"
        'title: "Beta"\n'
        'type: "Reference"\n'
        'status: "Active"\n'
        "---\n"
        "# Beta\n",
    )
    _write(
        pack / "okf" / "demo" / "concepts" / "index.md",
        "<!-- generated index, not a concept -->\n",
    )


def _write_generated_router(pack: Path) -> None:
    source_files = {
        path.relative_to(pack / "okf" / "demo").as_posix(): path.read_bytes()
        for path in (pack / "okf" / "demo").rglob("*")
        if path.is_file()
    }
    source_digest = _tree_digest(source_files)
    skill = pack / ".apm" / "skills" / "demo-router" / "SKILL.md"
    _write(
        skill,
        "---\n"
        "name: demo-router\n"
        "description: Generated router\n"
        "metadata:\n"
        "  boundaries: [filesystem_read_untrusted]\n"
        "  generated-by: compile-okf agentbundle-okf/v1\n"
        "  source-path: okf/demo\n"
        f"  source-digest: {source_digest}\n"
        "---\n"
        "# Router\n",
    )
    manifest = {
        "profile": "agentbundle-okf/v1",
        "router_skill": "demo-router",
        "managed": [
            {
                "digest": _bytes_digest(skill.read_bytes()),
                "kind": "okf-router",
                "marker": "generated-by: compile-okf agentbundle-okf/v1",
                "output_path": ".apm/skills/demo-router/SKILL.md",
                "source_digest": source_digest,
                "source_path": "okf/demo",
            }
        ],
    }
    (pack / ".okf-generated.json").write_text(
        json.dumps(manifest, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )


def test_discovers_pack_skill_and_knowledge_metadata_from_live_bytes(tmp_path: Path) -> None:
    pack = _base_pack(tmp_path)

    record = okf_discovery.discover_pack(pack)

    assert record.pack_metadata == {
        "categories": ["okf", "tools"],
        "keywords": ["demo", "okf"],
        "license": "MIT",
    }
    assert [item["name"] for item in record.skill_metadata] == [
        "demo-router",
        "manual-skill",
    ]
    router = record.skill_metadata[0]
    assert router["generated_from"] == "okf/demo"
    assert router["profile"] == "agentbundle-okf/v1"
    assert router["digest"] == record.knowledge[0]["digest"]
    manual = record.skill_metadata[1]
    assert manual["compatibility"]["max"] == 9007199254740991
    assert manual["boundaries"] == ["filesystem_read_untrusted"]
    assert record.knowledge == [
        {
            "id": "demo",
            "format": "okf",
            "okf_version": "0.2",
            "router_skill": "demo-router",
            "content_license": "Apache-2.0",
            "concept_count": 2,
            "digest": record.knowledge[0]["digest"],
        }
    ]


def test_no_okf_pack_returns_empty_knowledge_and_live_skill_edits(tmp_path: Path) -> None:
    pack = _base_pack(tmp_path, okf=False)

    first = okf_discovery.discover_pack(pack)
    assert first.knowledge == []

    skill = pack / ".apm" / "skills" / "manual-skill" / "SKILL.md"
    skill.write_text(
        skill.read_text(encoding="utf-8").replace("Manual skill", "Edited skill"),
        encoding="utf-8",
    )
    second = okf_discovery.discover_pack(pack)
    assert second.skill_metadata[0]["description"] == "Edited skill"


def test_frontmatter_description_allows_ordinary_yaml_punctuation(tmp_path: Path) -> None:
    pack = _base_pack(tmp_path, okf=False)
    skill = pack / ".apm" / "skills" / "manual-skill" / "SKILL.md"
    skill.write_text(
        skill.read_text(encoding="utf-8").replace(
            "Manual skill", "R&D analysis! Match * only when requested"
        ),
        encoding="utf-8",
    )

    record = okf_discovery.discover_pack(pack)

    assert record.skill_metadata[0]["description"] == (
        "R&D analysis! Match * only when requested"
    )


@pytest.mark.parametrize("value", ["!tag value", "&anchor value", "*alias"])
def test_frontmatter_rejects_yaml_tokens_in_syntactic_positions(
    tmp_path: Path, value: str
) -> None:
    pack = _base_pack(tmp_path, okf=False)
    skill = pack / ".apm" / "skills" / "manual-skill" / "SKILL.md"
    skill.write_text(
        skill.read_text(encoding="utf-8").replace(
            "description: Manual skill", f"description: {value}"
        ),
        encoding="utf-8",
    )

    with pytest.raises(okf_discovery.DiscoveryError) as exc:
        okf_discovery.discover_pack(pack)

    assert "YAML tags and aliases are not allowed" in exc.value.diagnostic


@pytest.mark.parametrize("value", [
    "x" * 1024,
    True,
    False,
    9007199254740991,
    -9007199254740991,
    ["x" * 1024, True, False, 9007199254740991, -9007199254740991],
])
def test_frontmatter_parser_accepts_bounded_compatibility_values(
    tmp_path: Path, value: Any
) -> None:
    pack = _base_pack(tmp_path, okf=False)
    text = json.dumps(value)
    skill = pack / ".apm" / "skills" / "manual-skill" / "SKILL.md"
    _write(
        skill,
        "---\n"
        "name: manual-skill\n"
        "description: Manual skill\n"
        "compatibility:\n"
        f"  target: {text}\n"
        "---\n"
        "# Manual\n",
    )

    assert okf_discovery.discover_pack(pack).skill_metadata[0]["compatibility"] == {
        "target": value
    }


@pytest.mark.parametrize("snippet", [
    "compatibility:\n  target: 9007199254740992\n",
    "compatibility:\n  target: -9007199254740992\n",
    "compatibility:\n  target: 1.5\n",
    "compatibility:\n  target:\n    nested: value\n",
    "compatibility:\n  target: [ok, {nested: value}]\n",
    "compatibility:\n  target: [" + ", ".join(["ok"] * 257) + "]\n",
])
def test_frontmatter_parser_rejects_unbounded_or_nested_compatibility(
    tmp_path: Path, snippet: str
) -> None:
    pack = _base_pack(tmp_path, okf=False)
    _write(
        pack / ".apm" / "skills" / "manual-skill" / "SKILL.md",
        "---\n"
        "name: manual-skill\n"
        "description: Manual skill\n"
        f"{snippet}"
        "---\n"
        "# Manual\n",
    )

    with pytest.raises(okf_discovery.DiscoveryError) as exc:
        okf_discovery.discover_pack(pack)
    assert "manual-skill/SKILL.md" in exc.value.diagnostic


def test_bounds_depth_and_count_limits_fail_with_safe_diagnostics(tmp_path: Path) -> None:
    pack = _base_pack(tmp_path, okf=False)
    limits = okf_discovery.DiscoveryLimits(max_skill_dirs=0)

    with pytest.raises(okf_discovery.DiscoveryError) as exc:
        okf_discovery.discover_pack(pack, limits=limits)
    assert exc.value.diagnostic == ".apm/skills: too many Skill directories"

    limits = okf_discovery.DiscoveryLimits(max_frontmatter_depth=1)
    with pytest.raises(okf_discovery.DiscoveryError) as exc:
        okf_discovery.discover_pack(pack, limits=limits)
    assert "frontmatter exceeds depth limit" in exc.value.diagnostic


@pytest.mark.parametrize(("relative", "diagnostic"), [
    ("okf/../escape", "unsafe OKF bundle path"),
    ("okf/Demo", "case-folded path collision"),
])
def test_declared_path_safety_and_collisions_fail(
    tmp_path: Path, relative: str, diagnostic: str
) -> None:
    pack = _base_pack(tmp_path)
    text = (pack / "pack.toml").read_text(encoding="utf-8")
    (pack / "pack.toml").write_text(
        text.replace('path = "okf/demo"', f'path = "{relative}"'),
        encoding="utf-8",
    )

    with pytest.raises(okf_discovery.DiscoveryError) as exc:
        okf_discovery.discover_pack(pack)
    assert diagnostic in exc.value.diagnostic


def test_unicode_normalization_collision_fails(tmp_path: Path) -> None:
    pack = _base_pack(tmp_path)
    text = (pack / "pack.toml").read_text(encoding="utf-8")
    (pack / "pack.toml").write_text(
        text
        + "\n[[pack.metadata.okf.bundles]]\n"
        + 'id = "demo\\u0301"\n'
        + 'path = "okf/other"\n'
        + '"router-skill" = "other-router"\n',
        encoding="utf-8",
    )
    (pack / "pack.toml").write_text(
        (pack / "pack.toml").read_text(encoding="utf-8").replace(
            'id = "demo"', 'id = "dem\u00f3"'
        ),
        encoding="utf-8",
    )

    with pytest.raises(okf_discovery.DiscoveryError) as exc:
        okf_discovery.discover_pack(pack)
    assert "duplicate OKF bundle id" in exc.value.diagnostic


def test_generated_markers_must_match_manifest_and_file_digest(tmp_path: Path) -> None:
    pack = _base_pack(tmp_path)
    manifest = pack / ".okf-generated.json"
    data = json.loads(manifest.read_text(encoding="utf-8"))
    data["managed"][0]["source_digest"] = "sha256:" + "0" * 64
    manifest.write_text(json.dumps(data, sort_keys=True), encoding="utf-8")

    with pytest.raises(okf_discovery.DiscoveryError) as exc:
        okf_discovery.discover_pack(pack)
    assert "manifest disagrees with generated Skill markers" in exc.value.diagnostic


@pytest.mark.parametrize("mutation", ["missing", "authored"])
def test_knowledge_requires_live_manifest_matching_generated_router(
    tmp_path: Path, mutation: str
) -> None:
    pack = _base_pack(tmp_path)
    router_dir = pack / ".apm" / "skills" / "demo-router"
    if mutation == "missing":
        (router_dir / "SKILL.md").unlink()
        router_dir.rmdir()
    else:
        _write(
            router_dir / "SKILL.md",
            "---\nname: demo-router\ndescription: Authored replacement\n---\n# Router\n",
        )

    with pytest.raises(okf_discovery.DiscoveryError) as exc:
        okf_discovery.discover_pack(pack)

    assert "demo-router/SKILL.md" in exc.value.diagnostic
    assert "generated router" in exc.value.diagnostic


def test_source_digest_matches_generic_compiler_vector(tmp_path: Path) -> None:
    pack = _base_pack(tmp_path)
    files = {
        path.relative_to(pack / "okf" / "demo").as_posix(): path.read_bytes()
        for path in (pack / "okf" / "demo").rglob("*")
        if path.is_file()
    }

    assert okf_discovery.discover_pack(pack).knowledge[0]["digest"] == _tree_digest(files)


@pytest.mark.parametrize(
    "relative",
    [
        "other/demo",
        "okf//demo",
        "okf/demo/",
        "okf/de:mo",
        "okf/CON/demo",
    ],
)
def test_declared_okf_root_matches_compiler_portable_path_contract(
    tmp_path: Path, relative: str
) -> None:
    pack = _base_pack(tmp_path)
    pack_toml = pack / "pack.toml"
    pack_toml.write_text(
        pack_toml.read_text(encoding="utf-8").replace(
            'path = "okf/demo"', f'path = "{relative}"'
        ),
        encoding="utf-8",
    )

    with pytest.raises(okf_discovery.DiscoveryError) as exc:
        okf_discovery.discover_pack(pack)

    assert exc.value.diagnostic == "pack.toml: unsafe OKF bundle path"


def test_rejects_symlinked_bundle_root_before_tree_traversal(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    pack = _base_pack(tmp_path)
    bundle_root = pack / "okf" / "demo"
    outside = tmp_path / "outside-bundle"
    bundle_root.rename(outside)
    try:
        bundle_root.symlink_to(outside, target_is_directory=True)
    except OSError:
        pytest.skip("directory symlinks are not available")

    original_rglob = Path.rglob

    def refuse_bundle_traversal(path: Path, pattern: str):
        if path == bundle_root:
            raise AssertionError("symlinked bundle root was traversed")
        return original_rglob(path, pattern)

    monkeypatch.setattr(Path, "rglob", refuse_bundle_traversal)

    with pytest.raises(okf_discovery.DiscoveryError) as exc:
        okf_discovery.discover_pack(pack)

    assert "directory boundary is unsafe" in exc.value.diagnostic


def test_rejects_symlinked_bundle_parent_before_tree_traversal(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    pack = _base_pack(tmp_path)
    okf_root = pack / "okf"
    outside = tmp_path / "outside-okf"
    okf_root.rename(outside)
    try:
        okf_root.symlink_to(outside, target_is_directory=True)
    except OSError:
        pytest.skip("directory symlinks are not available")

    original_rglob = Path.rglob

    def refuse_bundle_traversal(path: Path, pattern: str):
        if path == okf_root or path == okf_root / "demo":
            raise AssertionError("symlinked bundle parent was traversed")
        return original_rglob(path, pattern)

    monkeypatch.setattr(Path, "rglob", refuse_bundle_traversal)

    with pytest.raises(okf_discovery.DiscoveryError) as exc:
        okf_discovery.discover_pack(pack)

    assert "directory boundary is unsafe" in exc.value.diagnostic


def test_inline_array_depth_is_rejected_before_json_parser(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    pack = _base_pack(tmp_path, okf=False)
    skill = pack / ".apm" / "skills" / "manual-skill" / "SKILL.md"
    nested = "[" * 21 + "true" + "]" * 21
    _write(
        skill,
        "---\n"
        "name: manual-skill\n"
        "description: Manual skill\n"
        "compatibility:\n"
        f"  target: {nested}\n"
        "---\n"
        "# Manual\n",
    )
    original_loads = okf_discovery.json.loads

    def refuse_nested_parser(value: str, *args: object, **kwargs: object) -> Any:
        if value == nested:
            raise AssertionError("deep inline array reached json.loads")
        return original_loads(value, *args, **kwargs)

    monkeypatch.setattr(okf_discovery.json, "loads", refuse_nested_parser)

    with pytest.raises(okf_discovery.DiscoveryError) as exc:
        okf_discovery.discover_pack(pack)

    assert "frontmatter exceeds depth limit" in exc.value.diagnostic


@pytest.mark.parametrize("failure", [RecursionError(), MemoryError(), OverflowError()])
def test_inline_array_parser_resource_failures_have_stable_diagnostic(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    failure: BaseException,
) -> None:
    pack = _base_pack(tmp_path, okf=False)
    original_loads = okf_discovery.json.loads

    def fail_inline_array(value: str, *args: object, **kwargs: object) -> Any:
        if value == "[repo, false, -9007199254740991]":
            raise failure
        return original_loads(value, *args, **kwargs)

    monkeypatch.setattr(okf_discovery.json, "loads", fail_inline_array)

    with pytest.raises(okf_discovery.DiscoveryError) as exc:
        okf_discovery.discover_pack(pack)

    assert exc.value.diagnostic == (
        ".apm/skills/manual-skill/SKILL.md: inline list cannot be parsed safely"
    )


@pytest.mark.parametrize("constant", ["NaN", "Infinity", "-Infinity", "1e999"])
def test_manifest_rejects_non_finite_json_constants(
    tmp_path: Path, constant: str
) -> None:
    pack = _base_pack(tmp_path)
    manifest = pack / ".okf-generated.json"
    manifest.write_text(
        manifest.read_text(encoding="utf-8").replace(
            '{"managed":', f'{{"unsafe":{constant},"managed":'
        ),
        encoding="utf-8",
    )

    with pytest.raises(okf_discovery.DiscoveryError) as exc:
        okf_discovery.discover_pack(pack)

    assert exc.value.diagnostic == ".okf-generated.json: cannot be parsed safely"


def test_manifest_rejects_huge_json_integer_with_stable_diagnostic(
    tmp_path: Path,
) -> None:
    pack = _base_pack(tmp_path)
    manifest = pack / ".okf-generated.json"
    manifest.write_text(
        manifest.read_text(encoding="utf-8").replace(
            '{"managed":', '{"unsafe":' + "9" * 5000 + ',"managed":'
        ),
        encoding="utf-8",
    )

    with pytest.raises(okf_discovery.DiscoveryError) as exc:
        okf_discovery.discover_pack(pack)

    assert exc.value.diagnostic == ".okf-generated.json: cannot be parsed safely"


@pytest.mark.parametrize(
    "value", ["NaN", "Infinity", "-Infinity", "1e999", "9" * 5000]
)
def test_inline_list_rejects_non_interoperable_json_values(
    tmp_path: Path, value: str
) -> None:
    pack = _base_pack(tmp_path, okf=False)
    skill = pack / ".apm" / "skills" / "manual-skill" / "SKILL.md"
    _write(
        skill,
        "---\n"
        "name: manual-skill\n"
        "description: Manual skill\n"
        "compatibility:\n"
        f"  target: [{value}]\n"
        "---\n"
        "# Manual\n",
    )

    with pytest.raises(okf_discovery.DiscoveryError) as exc:
        okf_discovery.discover_pack(pack)

    assert exc.value.diagnostic == (
        ".apm/skills/manual-skill/SKILL.md: inline list cannot be parsed safely"
    )


def test_scalar_huge_integer_has_stable_diagnostic(tmp_path: Path) -> None:
    pack = _base_pack(tmp_path, okf=False)
    skill = pack / ".apm" / "skills" / "manual-skill" / "SKILL.md"
    _write(
        skill,
        "---\n"
        "name: manual-skill\n"
        "description: Manual skill\n"
        "compatibility:\n"
        f"  target: {'9' * 5000}\n"
        "---\n"
        "# Manual\n",
    )

    with pytest.raises(okf_discovery.DiscoveryError) as exc:
        okf_discovery.discover_pack(pack)

    assert exc.value.diagnostic == (
        ".apm/skills/manual-skill/SKILL.md: unsupported numeric value"
    )


def test_confined_read_rejects_fstat_oversize_before_file_allocation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = tmp_path / "source.md"
    source.write_bytes(b"four")

    def refuse_fdopen(*args: object, **kwargs: object) -> None:
        raise AssertionError("oversized descriptor reached file allocation")

    monkeypatch.setattr(os, "fdopen", refuse_fdopen)

    with pytest.raises(okf_discovery.file_safety.UnsafeContentError) as exc:
        okf_discovery.file_safety.read_confined_regular_file(
            tmp_path, source, max_bytes=3
        )

    assert "exceeds byte limit" in str(exc.value)


def test_confined_read_bounded_read_rejects_file_growth(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = tmp_path / "source.md"
    source.write_bytes(b"four")
    original_fstat = os.fstat

    def report_pre_growth_size(descriptor: int) -> SimpleNamespace:
        inspected = original_fstat(descriptor)
        return SimpleNamespace(
            st_mode=inspected.st_mode,
            st_nlink=inspected.st_nlink,
            st_dev=inspected.st_dev,
            st_ino=inspected.st_ino,
            st_size=3,
            st_file_attributes=getattr(inspected, "st_file_attributes", 0),
        )

    monkeypatch.setattr(os, "fstat", report_pre_growth_size)

    with pytest.raises(okf_discovery.file_safety.UnsafeContentError) as exc:
        okf_discovery.file_safety.read_confined_regular_file(
            tmp_path, source, max_bytes=3
        )

    assert "changed beyond byte limit" in str(exc.value)


def test_discovery_applies_explicit_caps_to_every_confined_read(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    pack = _base_pack(tmp_path)
    original_read = okf_discovery.file_safety.read_confined_regular_file
    observed: dict[str, int | None] = {}

    def observe(
        root: Path,
        path: Path,
        *,
        max_bytes: int | None = None,
    ) -> bytes:
        observed[path.relative_to(root).as_posix()] = max_bytes
        return original_read(root, path, max_bytes=max_bytes)

    monkeypatch.setattr(
        okf_discovery.file_safety, "read_confined_regular_file", observe
    )

    okf_discovery.discover_pack(pack)

    assert observed["pack.toml"] == okf_discovery.DiscoveryLimits().max_pack_toml_bytes
    assert observed[".okf-generated.json"] == (
        okf_discovery.DiscoveryLimits().max_manifest_bytes
    )
    assert observed[".apm/skills/demo-router/SKILL.md"] == (
        okf_discovery.DiscoveryLimits().max_skill_bytes
    )
    assert observed["okf/demo/index.md"] is not None
    assert all(limit is not None for limit in observed.values())


@pytest.mark.parametrize("descriptor_walk", (False, True))
def test_direct_read_rejects_windows_reparse_attribute(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, descriptor_walk: bool
) -> None:
    """Reject a reparse-flagged leaf on both leaf-inspection branches.

    "Windows" names the simulated attribute, not the branch. The confined read
    inspects the leaf through `Path.lstat` on the fallback branch Windows
    takes, and through `os.stat` bound to the parent descriptor everywhere
    else, so each branch needs its own stand-in or the simulated attribute
    never reaches the guard under test.
    """
    if descriptor_walk:
        if os.name == "nt":
            pytest.skip("Windows never binds path components to directory descriptors")
        # Keyed on the platform, not the capability: a regression in
        # `_supports_descriptor_walk` must fail here rather than skip away the
        # only coverage of the branch this platform actually runs.
        assert okf_discovery.file_safety._supports_descriptor_walk()
    source = tmp_path / "source.md"
    source.write_bytes(b"safe")
    root_inode = tmp_path.stat().st_ino
    reparse_flag = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)

    def as_reparse(inspected: os.stat_result) -> SimpleNamespace:
        return SimpleNamespace(
            st_mode=inspected.st_mode,
            st_nlink=inspected.st_nlink,
            st_dev=inspected.st_dev,
            st_ino=inspected.st_ino,
            st_size=inspected.st_size,
            st_file_attributes=reparse_flag,
        )

    if descriptor_walk:
        original_stat = okf_discovery.file_safety.os.stat

        def reparse_stat(
            path: Any, *args: Any, dir_fd: int | None = None, **kwargs: Any
        ) -> os.stat_result | SimpleNamespace:
            inspected = original_stat(path, *args, dir_fd=dir_fd, **kwargs)
            # The patch lands on the process-global `os`, so bind the
            # injection to this test's own leaf under this test's own parent.
            # `str` accepts every argument shape `os.stat` takes, including an
            # int descriptor, where `os.fspath` would raise.
            if (
                dir_fd is not None
                and str(path) == source.name
                and os.fstat(dir_fd).st_ino == root_inode
            ):
                return as_reparse(inspected)
            return inspected

        monkeypatch.setattr(okf_discovery.file_safety.os, "stat", reparse_stat)
    else:
        original_lstat = Path.lstat

        def reparse_lstat(path: Path) -> os.stat_result | SimpleNamespace:
            inspected = original_lstat(path)
            if path != source:
                return inspected
            return as_reparse(inspected)

        monkeypatch.setattr(Path, "lstat", reparse_lstat)

    monkeypatch.setattr(
        okf_discovery.file_safety,
        "_supports_descriptor_walk",
        lambda: descriptor_walk,
    )

    with pytest.raises(okf_discovery.file_safety.UnsafeContentError) as exc:
        okf_discovery.file_safety.read_confined_regular_file(
            tmp_path, source, max_bytes=4
        )

    assert "reparse point" in str(exc.value)


def test_bundle_root_rejects_windows_reparse_attribute_before_traversal(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    pack = _base_pack(tmp_path)
    bundle_root = pack / "okf" / "demo"
    original_lstat = Path.lstat
    original_rglob = Path.rglob
    reparse_flag = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)

    def reparse_lstat(path: Path) -> os.stat_result | SimpleNamespace:
        inspected = original_lstat(path)
        if path != bundle_root:
            return inspected
        return SimpleNamespace(
            st_mode=inspected.st_mode,
            st_file_attributes=reparse_flag,
        )

    def refuse_bundle_traversal(path: Path, pattern: str):
        if path == bundle_root:
            raise AssertionError("reparse bundle root was traversed")
        return original_rglob(path, pattern)

    monkeypatch.setattr(Path, "lstat", reparse_lstat)
    monkeypatch.setattr(Path, "rglob", refuse_bundle_traversal)

    with pytest.raises(okf_discovery.DiscoveryError) as exc:
        okf_discovery.discover_pack(pack)

    assert "directory boundary is unsafe" in exc.value.diagnostic


def test_rejects_hardlinks_symlinks_broken_links_and_open_swaps(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    pack = _base_pack(tmp_path, okf=False)
    skill = pack / ".apm" / "skills" / "manual-skill" / "SKILL.md"
    hardlink = pack / ".apm" / "skills" / "manual-skill" / "hardlink.md"
    hardlink.hardlink_to(skill)

    with pytest.raises(okf_discovery.DiscoveryError) as exc:
        okf_discovery.discover_pack(pack)
    assert "hard link not allowed" in exc.value.diagnostic

    hardlink.unlink()
    (pack / ".apm" / "skills" / "manual-skill" / "link.md").symlink_to(skill)
    with pytest.raises(okf_discovery.DiscoveryError) as exc:
        okf_discovery.discover_pack(pack)
    assert "not a regular file" in exc.value.diagnostic

    (pack / ".apm" / "skills" / "manual-skill" / "link.md").unlink()
    (pack / ".apm" / "skills" / "manual-skill" / "broken.md").symlink_to(
        pack / "missing.md"
    )
    with pytest.raises(okf_discovery.DiscoveryError) as exc:
        okf_discovery.discover_pack(pack)
    assert "not a regular file" in exc.value.diagnostic

    (pack / ".apm" / "skills" / "manual-skill" / "broken.md").unlink()

    original_read = okf_discovery.file_safety.read_confined_regular_file

    def swapped(
        root: Path,
        path: Path,
        *,
        max_bytes: int | None = None,
    ) -> bytes:
        if path.name == "SKILL.md":
            raise okf_discovery.file_safety.UnsafeContentError(
                "source file changed while opening: .apm/skills/manual-skill/SKILL.md"
            )
        return original_read(root, path, max_bytes=max_bytes)

    monkeypatch.setattr(okf_discovery.file_safety, "read_confined_regular_file", swapped)
    with pytest.raises(okf_discovery.DiscoveryError) as exc:
        okf_discovery.discover_pack(pack)
    assert "source file changed while opening" in exc.value.diagnostic


def test_discovery_uses_no_network_process_writes_or_yaml(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    pack = _base_pack(tmp_path)

    def fail(*args: object, **kwargs: object) -> None:
        raise AssertionError("forbidden side effect")

    monkeypatch.setattr(socket, "socket", fail)
    monkeypatch.setattr(subprocess, "run", fail)
    monkeypatch.setattr(Path, "write_text", fail)
    monkeypatch.setattr(Path, "write_bytes", fail)
    monkeypatch.setitem(sys.modules, "yaml", None)

    assert okf_discovery.discover_pack(pack).knowledge[0]["id"] == "demo"
