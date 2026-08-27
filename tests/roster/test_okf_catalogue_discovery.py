"""Repository-roster checks for OKF catalogue discovery."""

from __future__ import annotations

import json
import shutil
import tomllib
from pathlib import Path
from types import SimpleNamespace

from agentbundle.commands import show
from agentbundle.version import CLI_VERSION
from jsonschema import Draft202012Validator

REPO_ROOT = Path(__file__).resolve().parents[2]
PACKAGE_ROOT = REPO_ROOT / "packages" / "agentbundle"
SHOW_SCHEMA = REPO_ROOT / "contracts" / "jsonschema" / "agentbundle-show.schema.json"
CORE_PACK = REPO_ROOT / "packs" / "core"
COST_PILOT_PACK = REPO_ROOT / "packs" / "_okf-pilot-cost-engineering"
PRODUCT_CHANGELOG = REPO_ROOT / "docs" / "product" / "changelog.md"


def _args(pack: str, catalogue: Path) -> SimpleNamespace:
    return SimpleNamespace(
        pack=pack,
        catalogue=str(catalogue),
        format="json",
        root=".",
        _user_config=None,
    )


def _assert_show_schema(response: dict[str, object]) -> None:
    schema = json.loads(SHOW_SCHEMA.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema).validate(response)


def test_release_metadata_moves_together_for_okf_catalogue_discovery() -> None:
    """Public show JSON changes must move repository release surfaces together."""
    expected = "0.40.0"
    pyproject = tomllib.loads(
        (PACKAGE_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    )
    readme = (PACKAGE_ROOT / "README-pypi.md").read_text(encoding="utf-8")
    changelog = (PACKAGE_ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    agentbundle_doc = (REPO_ROOT / "docs" / "architecture" / "agentbundle.md").read_text(
        encoding="utf-8"
    )
    pack_layout_doc = (REPO_ROOT / "docs" / "architecture" / "pack-layout.md").read_text(
        encoding="utf-8"
    )

    assert expected == CLI_VERSION
    assert pyproject["project"]["version"] == expected
    assert f"What's new in {expected}" in readme
    for required in (
        "pack_metadata",
        "skill_metadata",
        "knowledge",
        "installed-state",
        "pre-release",
    ):
        assert required in readme
    assert f"## [{expected}]" in changelog
    assert "Engine-Change-RFC: RFC-0087" in changelog
    assert "pre-release" in agentbundle_doc
    assert "list-packs" in agentbundle_doc
    assert "marketplace" in agentbundle_doc
    assert "catalogue-index.json" in agentbundle_doc
    assert "excluded" in pack_layout_doc
    assert "catalogue-index.json" in pack_layout_doc


def test_okf_pack_releases_name_themselves_in_the_topmost_changelog_heading() -> None:
    """Each OKF-releasing pack's topmost changelog heading names its version.

    Scoped to the packs this change releases, not to every pack: `packs/core` and
    the cost-engineering pilot also ship OKF surfaces and are deliberately not
    covered here, so do not read a pass as repository-wide coverage.

    This is the third surface of the pack/plugin/changelog release invariant.
    It lives here rather than in each pack's own suite because
    `tools/lint-pack-test-boundary.py` forbids a pack test from reading above
    its own pack, and `docs/product/changelog.md` is repository-level. The two
    in-pack surfaces are asserted by each pack's release test.
    """
    lines = PRODUCT_CHANGELOG.read_text(encoding="utf-8").splitlines()

    for pack_name in ("catalogue-curation", "architect"):
        pack_dir = REPO_ROOT / "packs" / pack_name
        pack = tomllib.loads((pack_dir / "pack.toml").read_text(encoding="utf-8"))
        version = pack["pack"]["version"]
        heading = f"## [{pack_name}]["
        topmost = next((line for line in lines if line.startswith(heading)), None)
        assert topmost is not None, (
            f"docs/product/changelog.md has no {heading}…] heading at all, so "
            f"packs/{pack_name} {version!r} has no release entry"
        )
        assert topmost.startswith(f"{heading}{version}]"), (
            f"packs/{pack_name}/pack.toml is {version!r} but the topmost "
            f"{pack_name} changelog heading is {topmost!r}"
        )


def test_real_generated_core_pilot_cli_response_validates_schema(
    tmp_path: Path,
    capsys,
) -> None:
    catalogue = tmp_path / "catalogue"
    pack = catalogue / "packs" / "core"
    pack.mkdir(parents=True)
    shutil.copy2(CORE_PACK / "pack.toml", pack / "pack.toml")
    shutil.copy2(CORE_PACK / ".okf-generated.json", pack / ".okf-generated.json")
    shutil.copytree(
        CORE_PACK / "okf" / "security-checklists",
        pack / "okf" / "security-checklists",
    )
    shutil.copytree(
        CORE_PACK / ".apm" / "skills" / "security-checklists-reference",
        pack / ".apm" / "skills" / "security-checklists-reference",
    )
    shutil.copytree(
        CORE_PACK / ".apm" / "skills" / "security-checklists",
        pack / ".apm" / "skills" / "security-checklists",
    )

    rc = show.run(_args("core", catalogue))
    captured = capsys.readouterr()
    response = json.loads(captured.out)

    assert rc == 0
    assert captured.err == ""
    _assert_show_schema(response)
    assert response["name"] == "core"
    assert response["source"] == "catalogue"
    assert {"security-checklists", "security-checklists-reference"} <= set(response["skills"])
    assert response["knowledge"] == [
        {
            "id": "security-checklists",
            "format": "okf",
            "okf_version": "0.2",
            "router_skill": "security-checklists-reference",
            "content_license": "Apache-2.0 OR MIT",
            "concept_count": 11,
            "digest": response["knowledge"][0]["digest"],
        }
    ]
    assert response["knowledge"][0]["digest"].startswith("sha256:")
    router = next(
        item
        for item in response["skill_metadata"]
        if item["name"] == "security-checklists-reference"
    )
    assert router["generated_from"] == "okf/security-checklists"
    assert router["profile"] == "agentbundle-okf/v1"
    hand_authored_router = next(
        item
        for item in response["skill_metadata"]
        if item["name"] == "security-checklists"
    )
    assert hand_authored_router["generated_from"] is None
    assert hand_authored_router["profile"] is None
    assert hand_authored_router["digest"] is None


def test_real_architect_cli_response_includes_licensed_okf_bundle(capsys) -> None:
    """The shipped architect pack remains discoverable through public show JSON."""
    rc = show.run(_args("architect", REPO_ROOT))
    captured = capsys.readouterr()
    response = json.loads(captured.out)

    assert rc == 0
    assert captured.err == ""
    _assert_show_schema(response)
    assert response["name"] == "architect"
    assert response["source"] == "catalogue"
    assert response["knowledge"] == [
        {
            "id": "architecture-lenses",
            "format": "okf",
            "okf_version": "0.2",
            "router_skill": "architecture-lenses-reference",
            "content_license": "Apache-2.0 OR MIT",
            "concept_count": 47,
            "digest": response["knowledge"][0]["digest"],
        }
    ]
    assert response["knowledge"][0]["digest"].startswith("sha256:")
    router = next(
        item
        for item in response["skill_metadata"]
        if item["name"] == "architecture-lenses-reference"
    )
    assert router["generated_from"] == "okf/architecture-lenses"
    assert router["profile"] == "agentbundle-okf/v1"


def test_exact_cost_pilot_bytes_validate_cli_response(
    tmp_path: Path,
    capsys,
) -> None:
    catalogue = tmp_path / "catalogue"
    pack = catalogue / "packs" / "cost-engineering"
    shutil.copytree(COST_PILOT_PACK, pack)

    rc = show.run(_args("cost-engineering", catalogue))
    captured = capsys.readouterr()
    response = json.loads(captured.out)

    assert rc == 0
    assert captured.err == ""
    _assert_show_schema(response)
    assert response["name"] == "cost-engineering"
    assert response["skills"] == ["cost-engineering"]
    assert response["pack_metadata"] == {
        "categories": ["tooling"],
        "keywords": ["cost-engineering", "okf", "pilot"],
        "license": "Apache-2.0 OR MIT",
    }
    assert response["knowledge"] == [
        {
            "id": "cost-engineering",
            "format": "okf",
            "okf_version": "0.2",
            "router_skill": "cost-engineering",
            "content_license": "Apache-2.0 OR MIT",
            "concept_count": 6,
            "digest": response["knowledge"][0]["digest"],
        }
    ]
    assert response["knowledge"][0]["digest"].startswith("sha256:")
