"""Regression tests for cooling-record load diagnoses."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

_PACK_ROOT = Path(__file__).resolve().parents[3]
_COOLING_PATH = _PACK_ROOT / ".apm/skills/close-work/scripts/cooling.py"


def _load_cooling():
    """Load the cooling source under a test-specific module name."""
    module_name = "core_close_work_cooling_diagnosis"
    spec = importlib.util.spec_from_file_location(module_name, _COOLING_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def test_load_record_distinguishes_unavailable_confinement_authority(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """An unavailable authority is not evidence that the record is invalid."""
    cooling = _load_cooling()

    def unavailable_authority() -> object:
        raise ImportError("close-work authority seam is unavailable")

    monkeypatch.setattr(cooling, "_close_work", unavailable_authority)

    result = cooling.load_record(tmp_path, tmp_path / "docs/lifecycle/example.json")

    assert result.code == "cooling-state-unavailable"


def test_load_record_keeps_malformed_record_diagnosis(tmp_path: Path) -> None:
    """A readable malformed record remains a record-specific refusal."""
    cooling = _load_cooling()
    record_path = tmp_path / "docs/lifecycle/example.json"
    record_path.parent.mkdir(parents=True)
    record_path.write_text("{", encoding="utf-8")

    result = cooling.load_record(tmp_path, record_path)

    assert result.code == "record-invalid"
