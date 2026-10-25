"""repo-governance installs without core and seeds its layout section safely.

Drives the real `agentbundle install` against the real pack in this repository,
into a temporary repository where core is not installed.
"""

from __future__ import annotations

import tomllib
from pathlib import Path

import pytest
from agentbundle.cli import _build_parser
from agentbundle.commands.install import run

REPO_ROOT = Path(__file__).resolve().parents[2]
MANIFEST = REPO_ROOT / "packs" / "repo-governance" / "pack.toml"


def _install(output: Path) -> int:
    args = _build_parser().parse_args(
        [
            "install",
            str(REPO_ROOT),
            "--pack",
            "repo-governance",
            "--output",
            str(output),
            "--emit-install-routes",
        ]
    )
    return run(args)


@pytest.fixture(scope="module")
def with_layout_file(tmp_path_factory: pytest.TempPathFactory) -> tuple[int, Path]:
    repo = tmp_path_factory.mktemp("with-layout")
    layout = repo / "agentbundle-layout.toml"
    layout.write_text('[research]\noutput_dir = "docs/research"\n', encoding="utf-8")
    return _install(repo), repo


@pytest.fixture(scope="module")
def without_layout_file(tmp_path_factory: pytest.TempPathFactory) -> tuple[int, Path]:
    repo = tmp_path_factory.mktemp("without-layout")
    return _install(repo), repo


def test_installs_without_core_and_exits_zero(with_layout_file, without_layout_file):
    """AC1: both installs into a fresh repository with no core succeed."""
    for code, _repo in (with_layout_file, without_layout_file):
        assert code == 0


def test_existing_layout_file_gains_the_adr_section(with_layout_file):
    """AC2: an existing file gains `[adr]` and keeps its other content."""
    _, repo = with_layout_file
    text = (repo / "agentbundle-layout.toml").read_text(encoding="utf-8")
    assert text.startswith('[research]\noutput_dir = "docs/research"\n')
    assert tomllib.loads(text)["adr"] == {"output_dir": "docs/adr"}


def test_absent_layout_file_is_not_created(without_layout_file):
    """AC2: the install never creates `agentbundle-layout.toml`."""
    _, repo = without_layout_file
    assert not (repo / "agentbundle-layout.toml").exists()


def test_core_integrations_carry_consumer_provider_and_fallback():
    """AC11: decision weight, follow-on queue and RFC review hand-offs."""
    integrations = tomllib.loads(MANIFEST.read_text(encoding="utf-8"))["pack"][
        "integrations"
    ]
    core = {i["id"]: i for i in integrations if i["pack"] == "core"}
    expected = {
        "decision-weight-triggers": ["skill:work-loop"],
        "follow-on-queue-registration": ["skill:work-intake", "skill:workspace-status"],
        "rfc-review": ["agent:adversarial-reviewer", "agent:security-reviewer"],
    }
    for ident, providers in expected.items():
        entry = core[ident]
        assert entry["consumers"] == ["skill:new-rfc"]
        assert entry["providers"] == providers
        assert entry["fallback"].strip()
