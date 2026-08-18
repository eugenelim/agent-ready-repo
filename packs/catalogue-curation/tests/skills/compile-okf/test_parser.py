"""Parser and input-safety tests for the OKF authoring compiler."""

from __future__ import annotations

import shutil
import sys
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

from okf_compiler import DEFAULT_LIMITS, validate_okf_bundle  # noqa: E402

FIXTURE_ROOT = Path(__file__).parent / "fixtures" / "parser"
DEEP_FRONTMATTER = "\n".join(f"{'  ' * depth}child:" for depth in range(21))
DEEP_FRONTMATTER += f"\n{'  ' * 21}value: leaf\n"
EXCESSIVELY_DEEP_FRONTMATTER = "value: " + "[" * 1_200 + "0" + "]" * 1_200 + "\n"


def _copy_fixture(tmp_path: Path, name: str = "simple") -> Path:
    bundle = tmp_path / "bundle"
    shutil.copytree(FIXTURE_ROOT / "valid" / name, bundle)
    return bundle


def _write_markdown(path: Path, frontmatter: str, body: str = "# Concept\n") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"---\n{frontmatter}---\n{body}", encoding="utf-8")


def _codes(bundle: Path) -> list[str]:
    result = validate_okf_bundle(bundle, profile="agentbundle-okf/v1")
    return [diagnostic.code for diagnostic in result.diagnostics]


def test_valid_bundle_reports_profile_mapped_okf_version(tmp_path: Path) -> None:
    bundle = _copy_fixture(tmp_path)

    result = validate_okf_bundle(bundle, profile="agentbundle-okf/v1")

    assert result.ok
    assert result.okf_version == "0.2"
    assert [concept.path for concept in result.concepts] == ["concepts/triage.md"]
    assert result.diagnostics == ()


@pytest.mark.parametrize("version", ["", "0.1", "0.3", 0.2])
def test_root_index_version_must_match_active_profile(
    tmp_path: Path, version: object
) -> None:
    bundle = _copy_fixture(tmp_path)
    version_text = "" if version == "" else f"okf_version: {version!r}\n"
    (bundle / "index.md").write_text(f"---\n{version_text}---\n# Root\n", encoding="utf-8")

    result = validate_okf_bundle(bundle, profile="agentbundle-okf/v1")

    assert not result.ok
    assert [diagnostic.code for diagnostic in result.diagnostics] == ["OKF002"]


def test_absent_root_index_is_reported_as_drift_not_parse_rejection(
    tmp_path: Path,
) -> None:
    bundle = _copy_fixture(tmp_path)
    (bundle / "index.md").unlink()

    result = validate_okf_bundle(bundle, profile="agentbundle-okf/v1")

    assert not result.ok
    assert [diagnostic.code for diagnostic in result.diagnostics] == ["OKF011"]


@pytest.mark.parametrize(
    ("frontmatter", "code"),
    [
        ("id: [unterminated\n", "OKF003"),
        ("tagged: !unsafe value\n", "OKF003"),
        ("alias: &anchor value\ncopy: *anchor\n", "OKF003"),
        ("value: .nan\n", "OKF003"),
        (DEEP_FRONTMATTER, "OKF003"),
        ("remote: https://example.invalid/source\n", "OKF009"),
        ("executor: python\n", "OKF009"),
        ("script: ./run.sh\n", "OKF009"),
        ("runtime: shell\n", "OKF009"),
        ("attester: signed\n", "OKF009"),
      ],
)
def test_yaml_and_authority_failures_are_diagnostics(
    tmp_path: Path, frontmatter: str, code: str
) -> None:
    bundle = _copy_fixture(tmp_path)
    _write_markdown(bundle / "concepts" / "triage.md", frontmatter)

    assert _codes(bundle) == [code]


def test_excessively_nested_yaml_fails_with_a_stable_diagnostic(
    tmp_path: Path,
) -> None:
    bundle = _copy_fixture(tmp_path)
    _write_markdown(
        bundle / "concepts" / "triage.md",
        EXCESSIVELY_DEEP_FRONTMATTER,
    )

    result = validate_okf_bundle(bundle, profile="agentbundle-okf/v1")

    assert [(item.code, item.message) for item in result.diagnostics] == [
        ("OKF003", "frontmatter contains unsupported values")
    ]


@pytest.mark.parametrize(
    "relative_path",
    [
        "../escape.md",
        "/absolute.md",
        "concepts\\windows.md",
        "concepts/bad\u0007name.md",
        "concepts/name?.md",
        "concepts/CON/readme.md",
        "concepts/trailingdot./readme.md",
        "concepts/trailingspace /readme.md",
    ],
)
def test_declared_or_discovered_unsafe_paths_reject_before_generation(
    tmp_path: Path, relative_path: str
) -> None:
    bundle = _copy_fixture(tmp_path)
    called = False

    def on_ready_to_generate() -> None:
        nonlocal called
        called = True

    result = validate_okf_bundle(
        bundle,
        profile="agentbundle-okf/v1",
        declared_paths=[relative_path],
        on_ready_to_generate=on_ready_to_generate,
    )

    assert not result.ok
    assert [diagnostic.code for diagnostic in result.diagnostics] == ["OKF004"]
    assert not called


def test_symlink_inputs_are_rejected(tmp_path: Path) -> None:
    bundle = _copy_fixture(tmp_path)
    target = bundle / "concepts" / "triage.md"
    target.unlink()
    target.symlink_to(bundle / "index.md")

    assert _codes(bundle) == ["OKF004"]


def test_hard_link_inputs_are_rejected(tmp_path: Path) -> None:
    bundle = _copy_fixture(tmp_path)
    link = bundle / "concepts" / "linked.md"
    link.hardlink_to(bundle / "concepts" / "triage.md")

    assert _codes(bundle) == ["OKF004"]


def test_reparse_or_junction_marker_is_rejected(tmp_path: Path) -> None:
    bundle = _copy_fixture(tmp_path)
    suspicious = bundle / "concepts" / "junction.md"
    _write_markdown(suspicious, "id: junction\n")

    result = validate_okf_bundle(
        bundle,
        profile="agentbundle-okf/v1",
        reparse_markers={suspicious},
    )

    assert [diagnostic.code for diagnostic in result.diagnostics] == ["OKF004"]


class _ReparseStat:
    def __init__(self, wrapped: object) -> None:
        self._wrapped = wrapped
        self.st_file_attributes = 0x400

    def __getattr__(self, name: str) -> object:
        return getattr(self._wrapped, name)


def test_real_reparse_stat_attribute_is_rejected_before_input_read(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    bundle = _copy_fixture(tmp_path)
    suspicious = bundle / "concepts" / "triage.md"
    original_lstat = Path.lstat

    def mark_reparse(path: Path) -> object:
        info = original_lstat(path)
        return _ReparseStat(info) if path == suspicious else info

    monkeypatch.setattr(Path, "lstat", mark_reparse)

    result = validate_okf_bundle(bundle, profile="agentbundle-okf/v1")

    assert [diagnostic.code for diagnostic in result.diagnostics] == ["OKF004"]


def test_oversized_input_is_rejected_before_open_callback(
    tmp_path: Path,
) -> None:
    bundle = _copy_fixture(tmp_path)
    oversized = bundle / "concepts" / "oversized.md"
    oversized.write_bytes(b"x" * (DEFAULT_LIMITS["markdown_bytes"] + 1))
    opened: list[Path] = []

    result = validate_okf_bundle(
        bundle,
        profile="agentbundle-okf/v1",
        before_open=opened.append,
    )

    assert [item.code for item in result.diagnostics] == ["OKF005"]
    assert oversized not in opened


def test_resolution_failure_is_rejected(tmp_path: Path) -> None:
    bundle = _copy_fixture(tmp_path)
    failing = bundle / "concepts" / "triage.md"

    result = validate_okf_bundle(
        bundle,
        profile="agentbundle-okf/v1",
        resolution_failures={failing},
    )

    assert [diagnostic.code for diagnostic in result.diagnostics] == ["OKF004"]


def test_symlink_swap_between_inspection_and_open_is_rejected(tmp_path: Path) -> None:
    bundle = _copy_fixture(tmp_path)
    target = bundle / "concepts" / "triage.md"

    def swap(path: Path) -> None:
        if path == target:
            path.unlink()
            path.symlink_to(bundle / "index.md")

    result = validate_okf_bundle(
        bundle,
        profile="agentbundle-okf/v1",
        before_open=swap,
    )

    assert [diagnostic.code for diagnostic in result.diagnostics] == ["OKF004"]


def test_unicode_nfc_and_case_fold_collisions_reject(tmp_path: Path) -> None:
    bundle = _copy_fixture(tmp_path)

    result = validate_okf_bundle(
        bundle,
        profile="agentbundle-okf/v1",
        declared_paths=[
            "concepts/TRIAGE.md",
            "concepts/Cafe\u0301.md",
            "concepts/Caf\u00e9.md",
        ],
    )

    assert [diagnostic.code for diagnostic in result.diagnostics] == ["OKF004", "OKF004"]


@pytest.mark.parametrize(
    ("mutation", "expected_code"),
    [
        ("file_count", "OKF005"),
        ("concept_count", "OKF005"),
        ("total_bytes", "OKF005"),
        ("directory_depth", "OKF005"),
        ("markdown_bytes", "OKF005"),
        ("frontmatter_bytes", "OKF005"),
    ],
)
def test_resource_limits_fail_before_generation(
    tmp_path: Path, mutation: str, expected_code: str
) -> None:
    bundle = _copy_fixture(tmp_path)
    called = False

    def on_ready_to_generate() -> None:
        nonlocal called
        called = True

    result = validate_okf_bundle(
        bundle,
        profile="agentbundle-okf/v1",
        resource_overrides={mutation: 0},
        on_ready_to_generate=on_ready_to_generate,
    )

    assert [diagnostic.code for diagnostic in result.diagnostics] == [expected_code]
    assert not called


def test_boundary_equal_resource_limits_pass(tmp_path: Path) -> None:
    bundle = _copy_fixture(tmp_path)

    result = validate_okf_bundle(
        bundle,
        profile="agentbundle-okf/v1",
        resource_overrides={
            "file_count": 2,
            "concept_count": 1,
            "total_bytes": sum(path.stat().st_size for path in bundle.rglob("*") if path.is_file()),
            "directory_depth": 1,
            "markdown_bytes": (bundle / "concepts" / "triage.md").stat().st_size,
            "frontmatter_bytes": 57,
        },
    )

    assert result.ok


def test_lifecycle_statuses_are_limited(tmp_path: Path) -> None:
    bundle = _copy_fixture(tmp_path)
    _write_markdown(bundle / "concepts" / "triage.md", "id: triage\nstatus: Removed\n")

    assert _codes(bundle) == ["OKF003"]


def test_diagnostics_sort_by_registry_then_path(tmp_path: Path) -> None:
    bundle = _copy_fixture(tmp_path)
    (bundle / "index.md").write_text("---\nokf_version: '0.3'\n---\n# Root\n", encoding="utf-8")
    _write_markdown(bundle / "concepts" / "bad.md", "id: [unterminated\n")
    (bundle / "concepts" / "link.md").symlink_to(bundle / "index.md")

    result = validate_okf_bundle(bundle, profile="agentbundle-okf/v1")

    assert [(item.code, item.path) for item in result.diagnostics] == [
        ("OKF002", "index.md"),
        ("OKF003", "concepts/bad.md"),
        ("OKF004", "concepts/link.md"),
    ]
