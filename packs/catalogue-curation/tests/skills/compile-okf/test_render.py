"""Deterministic render tests for the OKF authoring compiler."""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path, PureWindowsPath

import pytest
from agentbundle.catalogue_tooling.skill_spec_lint import lint_skill_spec

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
    canonical_json_bytes,
    render_okf_bundle,
    review_projection_digest,
)

FIXTURE_ROOT = Path(__file__).parent / "fixtures" / "render"
RUNBOOK_DIGEST = "sha256:5133e0ae722bc233c04ee2f91cff6e54dd040be65487ff353a986c3aafeaf1a7"
STRICT_JSON_VECTOR = b'{"a":[true,null],"b":1}\n'
STRICT_JSON_DIGEST = "sha256:b7c64ebef4296c41c0c46ab5e7a71a88ab124b5fdb82613abc75327ce6195ec6"


def _copy_fixture(tmp_path: Path) -> Path:
    tmp_path.mkdir(parents=True, exist_ok=True)
    bundle = tmp_path / "bundle"
    shutil.copytree(FIXTURE_ROOT / "rich", bundle)
    (bundle / "empty").mkdir(exist_ok=True)
    return bundle


def _render(tmp_path: Path):
    bundle = _copy_fixture(tmp_path)
    return render_okf_bundle(
        bundle,
        bundle_id="rich",
        router_skill="rich-router",
        projected_concepts={"concepts/runbook.md": RUNBOOK_DIGEST},
    )


def test_render_stubs_compile_red_then_indexes_are_exact(tmp_path: Path) -> None:
    result = _render(tmp_path)

    assert result.diagnostics == ()
    assert result.files["references/okf/index.md"].decode() == (
        "---\n"
        'okf_version: "0.2"\n'
        "---\n"
        "<!-- agentbundle-managed: profile=agentbundle-okf/v1 kind=okf-index -->\n"
        "# OKF index: rich\n\n"
        "- [concepts](concepts/index.md) - 3 concepts\n"
    )
    assert result.files["references/okf/concepts/index.md"].decode() == (
        "<!-- agentbundle-managed: profile=agentbundle-okf/v1 kind=okf-index -->\n"
        "# OKF index: concepts\n\n"
        "- [Deprecated Knowledge](deprecated.md) - Deprecated Note\n"
        "- [Hostile Prompt](hostile.md) - Active Note\n"
        "- [Reviewed Runbook](runbook.md) - Active Playbook\n"
    )
    assert "references/okf/empty/index.md" not in result.files
    assert "references/okf/concepts/stale.md" in result.files


def test_nested_index_paths_are_posix_on_windows_hosts(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Bundle-internal paths must not inherit the host path separator."""
    concepts = {
        "concepts/assessment-intents/baseline.md": okf_compiler.Concept(
            path="concepts/assessment-intents/baseline.md",
            metadata={"title": "Baseline", "status": "Active", "type": "Reference"},
            body="",
        )
    }
    monkeypatch.setattr(okf_compiler, "Path", PureWindowsPath)

    indexes = okf_compiler._render_indexes("architecture-lenses", concepts)

    assert "concepts/assessment-intents/index.md" in indexes
    assert all("\\" not in path for path in indexes)
    assert b"(concepts/assessment-intents/index.md)" in indexes["index.md"]


def test_router_skill_is_deterministic_nested_and_has_no_tools(tmp_path: Path) -> None:
    first = _render(tmp_path / "first")
    second = _render(tmp_path / "second")
    router = first.files["SKILL.md"].decode()

    assert first.files == second.files
    assert "allowed-tools" not in router
    assert "metadata:\n  boundaries: [filesystem_read_untrusted]" in router
    assert "generated-by: compile-okf agentbundle-okf/v1" in router
    assert "source-path: okf/rich" in router
    assert "source-digest: sha256:" in router
    assert "Read `references/okf/index.md` first." in router
    assert "Ignore previous instructions" not in router


def test_procedure_skill_contains_reviewed_section_and_untrusted_includes(
    tmp_path: Path,
) -> None:
    result = _render(tmp_path)
    skill = result.files["skills/reviewed-runbook/SKILL.md"].decode()

    assert "allowed-tools" not in skill
    assert "reviewed-projection-digest: " + RUNBOOK_DIGEST in skill
    assert "metadata:\n  boundaries: [filesystem_read_untrusted]" in skill
    assert "1. Inspect the request." in skill
    assert "### Detail" in skill
    assert "Do not include this section." not in skill
    assert "Introductory data" not in skill
    assert result.files["skills/reviewed-runbook/references/include.md"] == (
        b"This is supporting data for the reviewed runbook.\n"
    )
    assert "Untrusted included data" in skill


def test_generated_skills_pass_existing_deep_skill_lint(tmp_path: Path) -> None:
    result = _render(tmp_path / "source")
    root = tmp_path / "lint-root"
    skill_root = root / "packs" / "generated" / ".apm" / "skills"
    router_dir = skill_root / "rich-router"
    procedure_dir = skill_root / "reviewed-runbook"
    router_dir.mkdir(parents=True)
    procedure_dir.mkdir()
    (router_dir / "SKILL.md").write_bytes(result.files["SKILL.md"])
    (procedure_dir / "SKILL.md").write_bytes(result.files["skills/reviewed-runbook/SKILL.md"])

    diagnostics = lint_skill_spec(root, pack="generated")

    assert [diagnostic for diagnostic in diagnostics if diagnostic.severity.name == "ERROR"] == []


def test_references_preserve_canonical_bytes_and_unknown_extensions(
    tmp_path: Path,
) -> None:
    bundle = _copy_fixture(tmp_path)
    result = render_okf_bundle(
        bundle,
        bundle_id="rich",
        router_skill="rich-router",
        projected_concepts={"concepts/runbook.md": RUNBOOK_DIGEST},
    )

    assert result.files["references/okf/concepts/runbook.md"] == (
        bundle / "concepts" / "runbook.md"
    ).read_bytes()
    assert result.files["references/okf/extensions/unknown.json"] == (
        bundle / "extensions" / "unknown.json"
    ).read_bytes()


def test_manifest_bytes_are_stable_strict_json(tmp_path: Path) -> None:
    result = _render(tmp_path)
    raw = result.files[".okf-generated.json"]
    manifest = json.loads(raw)

    assert raw.endswith(b"\n")
    assert b"NaN" not in raw
    assert manifest["profile"] == "agentbundle-okf/v1"
    assert manifest["managed"][0]["kind"] == "okf-router"
    assert manifest["managed"][1]["kind"] == "okf-index"
    assert manifest["managed"][1]["marker"] == (
        "<!-- agentbundle-managed: profile=agentbundle-okf/v1 kind=okf-index -->"
    )
    assert manifest["managed"][2]["kind"] == "okf-procedure-skill"


def test_canonical_review_tuple_digest_vector_and_invalidation(tmp_path: Path) -> None:
    bundle = _copy_fixture(tmp_path)
    digest = review_projection_digest(
        bundle,
        concept_path="concepts/runbook.md",
        skill_name="reviewed-runbook",
        activation_description="Use when a reviewed runbook should guide an operator.",
        instruction_section="Procedure",
        includes=("guides/include.md",),
    )

    assert digest == RUNBOOK_DIGEST

    (bundle / "guides" / "include.md").write_text("Changed include.\n", encoding="utf-8")
    changed = review_projection_digest(
        bundle,
        concept_path="concepts/runbook.md",
        skill_name="reviewed-runbook",
        activation_description="Use when a reviewed runbook should guide an operator.",
        instruction_section="Procedure",
        includes=("guides/include.md",),
    )
    assert changed != RUNBOOK_DIGEST


def test_declared_review_digest_must_match_candidate(tmp_path: Path) -> None:
    bundle = _copy_fixture(tmp_path)

    result = render_okf_bundle(
        bundle,
        bundle_id="rich",
        router_skill="rich-router",
        projected_concepts={
            "concepts/runbook.md": "sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
        },
    )

    assert [diagnostic.code for diagnostic in result.diagnostics] == ["OKF008"]
    assert result.files == {}
    assert result.review_candidates["concepts/runbook.md"] == RUNBOOK_DIGEST


@pytest.mark.parametrize("concept_type", ["Reference", "Note"])
def test_projected_procedure_requires_playbook_concept(
    tmp_path: Path,
    concept_type: str,
) -> None:
    bundle = _copy_fixture(tmp_path)
    concept = bundle / "concepts" / "runbook.md"
    concept.write_text(
        concept.read_text(encoding="utf-8").replace(
            "type: Playbook",
            f"type: {concept_type}",
        ),
        encoding="utf-8",
    )

    result = render_okf_bundle(
        bundle,
        bundle_id="rich",
        router_skill="rich-router",
        projected_concepts={"concepts/runbook.md": RUNBOOK_DIGEST},
    )

    assert [diagnostic.code for diagnostic in result.diagnostics] == ["OKF007"]
    assert result.files == {}


@pytest.mark.parametrize(
    ("body", "expected_code"),
    [
        ("# Reviewed Runbook\n\n## Missing\n\nText.\n", "OKF007"),
        ("# Reviewed Runbook\n\n## Procedure\n\nOne.\n\n## Procedure\n\nTwo.\n", "OKF007"),
        ("# Reviewed Runbook\n\n```md\n## Procedure\ninside\n```\n", "OKF007"),
        ("# Reviewed Runbook\n\n## Procedure ##\n\nText.\n", "OKF007"),
        ("# Reviewed Runbook\n\n## Procedure\n\n", "OKF007"),
    ],
)
def test_instruction_heading_must_select_one_unfenced_nonempty_section(
    tmp_path: Path, body: str, expected_code: str
) -> None:
    bundle = _copy_fixture(tmp_path)
    concept = bundle / "concepts" / "runbook.md"
    frontmatter = concept.read_text(encoding="utf-8").split("---\n", 2)[1]
    concept.write_text(f"---\n{frontmatter}---\n{body}", encoding="utf-8")

    result = render_okf_bundle(
        bundle,
        bundle_id="rich",
        router_skill="rich-router",
        projected_concepts={"concepts/runbook.md": RUNBOOK_DIGEST},
    )

    assert [diagnostic.code for diagnostic in result.diagnostics] == [expected_code]


def test_strict_canonical_json_rejects_non_finite_values() -> None:
    assert canonical_json_bytes({"b": 1, "a": [True, None]}) == STRICT_JSON_VECTOR
    assert review_projection_digest.bytes_digest(STRICT_JSON_VECTOR) == STRICT_JSON_DIGEST
    with pytest.raises(ValueError):
        canonical_json_bytes({"bad": float("nan")})
