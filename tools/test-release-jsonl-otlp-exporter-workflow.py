"""Structural checks on the jsonl-otlp-exporter release workflow.

Covers AC-0046, AC-0057, AC-0058, AC-0059 of `docs/specs/jsonl-otlp-exporter`.

These live here, not in the package's own suite, on purpose. The package must
stay extractable: its tests use only its own fixtures, so a suite asserting
things about this repository's `.github/` would be exactly the coupling the
spec's extraction constraint forbids.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

yaml = pytest.importorskip("yaml")

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "release-jsonl-otlp-exporter.yml"

SHA_PINNED = re.compile(r"^[^@]+@[0-9a-f]{40}$")


@pytest.fixture(scope="module")
def workflow() -> dict:
    return yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))


def _steps(workflow: dict):
    for job in workflow["jobs"].values():
        for step in job.get("steps", []):
            yield job, step


def test_every_third_party_action_is_pinned_to_a_full_length_sha(workflow):
    """AC-0058. A tag is mutable: `@v4` can be repointed at any commit, so a
    pinned tag is not a pin at all."""
    unpinned = [
        step["uses"] for _, step in _steps(workflow)
        if "uses" in step and not SHA_PINNED.match(step["uses"])
    ]
    assert not unpinned, f"not pinned to a full-length commit SHA: {unpinned}"


def test_publishing_uses_oidc_and_stores_no_long_lived_credential(workflow):
    """AC-0057. `id-token: write` mints a short-lived token at run time; a stored
    API token is a credential that can leak and outlive the job."""
    publish = workflow["jobs"]["publish-pypi"]
    assert publish["permissions"]["id-token"] == "write"
    text = WORKFLOW.read_text(encoding="utf-8")
    for forbidden in ("PYPI_API_TOKEN", "TWINE_PASSWORD", "password:"):
        assert forbidden not in text, f"{forbidden} implies a stored PyPI credential"


def test_a_tag_that_disagrees_with_pyproject_is_refused(workflow):
    """AC-0046. The check must compare the tag against pyproject, and fail."""
    step = next(
        step for _, step in _steps(workflow)
        if step.get("name", "").startswith("Assert tag matches")
    )
    body = step["run"]
    assert "pyproject.toml" in body
    assert "sys.exit(1)" in body
    assert step.get("if") == "github.ref_type == 'tag'"


def test_the_wheel_is_installed_into_a_fresh_venv_before_publishing(workflow):
    """AC-0059. Building is not evidence the artifact works; installing it is."""
    smoke = next(
        step for _, step in _steps(workflow)
        if step.get("name", "").startswith("Smoke")
    )
    body = smoke["run"]
    assert "python3 -m venv" in body
    assert "dist/*.whl" in body
    assert "jsonl-otlp-export --version" in body
    assert workflow["jobs"]["publish-pypi"]["needs"] == ["build-and-smoke"]


def test_publishing_only_happens_on_a_tag(workflow):
    """Claiming a PyPI name is irreversible, so it must never ride a merge."""
    assert workflow["jobs"]["publish-pypi"]["if"] == "github.ref_type == 'tag'"


def test_the_workflow_asserts_no_profile_is_bundled(workflow):
    """The one thing a wheel could silently regain: shipped profile data."""
    step = next(
        step for _, step in _steps(workflow)
        if step.get("name", "").startswith("Assert the wheel bundles no profile")
    )
    assert "zipfile" in step["run"] and "sys.exit(1)" in step["run"]
