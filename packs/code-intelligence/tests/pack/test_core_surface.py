"""Goal-based checks that the pack's non-markdown payload carries no Core name.

Runs the Core-name, open-a-location and preflight-invocation rules over every
non-markdown file under ``.apm/`` (evals.json, fixtures, scripts). The markdown
files are covered by ``test_authority_guidance.py``, whose matchers and planted
samples are reused here by loading it under a unique module name.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType

import pytest

_THIS_DIR: Path = Path(__file__).resolve().parent
_SPEC = importlib.util.spec_from_file_location(
    "code_intelligence_core_surface_authority_guidance",
    _THIS_DIR / "test_authority_guidance.py",
)
assert _SPEC is not None and _SPEC.loader is not None
_AUTH: ModuleType = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_AUTH)

PACK_ROOT: Path = _AUTH.PACK_ROOT
APM_ROOT: Path = _AUTH.APM_ROOT


def non_markdown_files() -> list[Path]:
    """Return every regular non-markdown file under ``.apm/``, sorted."""
    return sorted(
        p for p in APM_ROOT.rglob("*") if p.is_file() and p.suffix.lower() != ".md"
    )


def _read(path: Path) -> str:
    return path.read_text("utf-8", errors="replace")


def test_non_markdown_payload_is_scanned() -> None:
    names = {p.name for p in non_markdown_files()}
    assert "evals.json" in names
    assert "composition-blast-radius-b.json" in names
    assert "estate_preflight.py" in names


@pytest.mark.parametrize(
    "sample",
    ["a `read-locator` call", "Core owns it", '"prompt": "Use repository-exploration."']
)
def test_core_rule_flags_planted_sample_in_a_json_body(sample: str) -> None:
    assert _AUTH.find_core_names(sample)


def test_open_and_preflight_rules_flag_planted_samples() -> None:
    assert _AUTH.find_open_phrases('{"x": "hop files to inspect"}')
    assert _AUTH.preflight_violations("python scripts/estate_preflight.py --check")


def test_non_markdown_files_name_no_core() -> None:
    offenders = {
        p.relative_to(PACK_ROOT).as_posix(): _AUTH.find_core_names(_read(p))
        for p in non_markdown_files()
    }
    assert {k: v for k, v in offenders.items() if v} == {}


def test_non_markdown_files_have_no_open_location_phrasing() -> None:
    offenders = {
        p.relative_to(PACK_ROOT).as_posix(): _AUTH.find_open_phrases(_read(p))
        for p in non_markdown_files()
    }
    assert {k: v for k, v in offenders.items() if v} == {}


def test_non_markdown_preflight_invocations_use_skill_dir() -> None:
    offenders = {
        p.relative_to(PACK_ROOT).as_posix(): _AUTH.preflight_violations(_read(p))
        for p in non_markdown_files()
    }
    assert {k: v for k, v in offenders.items() if v} == {}
