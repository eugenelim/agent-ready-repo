"""Construction tests for additive Wave 1 workspace surface metadata."""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

_PACK_ROOT = Path(__file__).resolve().parents[3]
_ENGINE_PATH = (
    _PACK_ROOT
    / ".apm"
    / "skills"
    / "workspace-status"
    / "scripts"
    / "workspace_status_engine.py"
)
_VALID_TARGETS = (
    _PACK_ROOT
    / "tests"
    / "pack"
    / "fixtures"
    / "work-intake-contracts"
    / "workspace"
    / "target"
    / "valid"
)
# Literal per-fixture paths: `lint-pack-test-boundary` resolves every pack-test
# path statically, so a fixture name may not arrive as a runtime segment.
_FIXTURE_PATHS = {
    "spec-path-with-surface-locator.json": (
        _VALID_TARGETS / "spec-path-with-surface-locator.json"
    ),
    "spec-locator-only.json": _VALID_TARGETS / "spec-locator-only.json",
}


def _load_engine():
    """Load the source workspace reader without depending on installation."""
    module_name = "core_workspace_status_semantic_surface_test"
    spec = importlib.util.spec_from_file_location(module_name, _ENGINE_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def _fixture(name: str) -> dict[str, object]:
    return json.loads(_FIXTURE_PATHS[name].read_text(encoding="utf-8"))


def test_t3_preserves_path_plus_surface_metadata() -> None:
    """A legacy path remains authoritative while additive metadata survives."""
    module = _load_engine()

    entry, findings = module.parse_workspace_entry(
        _fixture("spec-path-with-surface-locator.json")
    )

    assert findings == []
    assert entry is not None
    assert entry.path == "docs/specs/example/spec.md"
    assert entry.surface_role == "delivery-contract"
    assert entry.locator.kind == "external"
    assert entry.locator.value == "example-tracker:delivery/42"


def test_t3_parses_locator_only_without_inventing_a_path() -> None:
    """Wave 1 keeps locator-only records typed but execution-ineligible."""
    module = _load_engine()

    entry, findings = module.parse_workspace_entry(_fixture("spec-locator-only.json"))

    assert findings == []
    assert entry is not None
    assert entry.path is None
    assert entry.surface_role == "delivery-contract"
    assert entry.locator.kind == "external"
    assert entry.locator.value == "example-tracker:delivery/42"


def test_t3_locator_only_is_visible_but_never_dispatches(
    monkeypatch,
) -> None:
    """Canonical reconciliation emits the existing fail-closed finding first."""
    module = _load_engine()

    def unexpected_artifact_read(*_args, **_kwargs):
        raise AssertionError("locator-only entry attempted local artifact access")

    monkeypatch.setattr(module, "_artifact_metadata", unexpected_artifact_read)
    workspace = {
        "ini-001": {
            "status": "active",
            "work": {
                "queue": [_fixture("spec-locator-only.json")],
                "active": [],
                "shipped": [],
            },
        }
    }

    result = module.run_canonical_reconciliation(workspace)

    assert len(result.memberships) == 1
    assert len(result.evaluations) == 1
    evaluation = result.evaluations[0]
    assert evaluation.entry.path is None
    assert evaluation.entry.surface_role == "delivery-contract"
    assert evaluation.entry.locator.value == "example-tracker:delivery/42"
    assert evaluation.dispatchable is False
    assert [(item.code, item.path) for item in result.findings] == [
        ("configuration_mismatch", "workspace.toml")
    ]

    snapshot = module.canonical_result_snapshot(result)
    assert snapshot["evaluations"][0]["surface_role"] == "delivery-contract"
    assert snapshot["evaluations"][0]["locator"] == {
        "kind": "external",
        "value": "example-tracker:delivery/42",
    }


def test_t3_safe_projection_adds_metadata_only_when_declared(tmp_path: Path) -> None:
    """Path-only output stays unchanged while additive metadata is preserved."""
    module = _load_engine()
    raw = _fixture("spec-path-with-surface-locator.json")
    artifact = tmp_path / raw["path"]
    artifact.parent.mkdir(parents=True)
    artifact.write_text("# Example\n\n- **Status:** Approved\n", encoding="utf-8")
    (artifact.parent / "plan.md").write_text("# Plan\n", encoding="utf-8")

    def reconcile(entry: dict[str, object]):
        workspace = {
            "ini-001": {
                "status": "active",
                "work": {"queue": [entry], "active": [], "shipped": []},
            }
        }
        return module.canonical_result_snapshot(
            module.run_canonical_reconciliation(workspace, tmp_path)
        )

    with_surface = reconcile(raw)
    path_only = reconcile(
        {key: value for key, value in raw.items() if key not in {"surface_role", "locator"}}
    )

    assert with_surface["evaluations"][0]["surface_role"] == "delivery-contract"
    assert with_surface["evaluations"][0]["locator"] == {
        "kind": "external",
        "value": "example-tracker:delivery/42",
    }
    assert "surface_role" not in path_only["evaluations"][0]
    assert "locator" not in path_only["evaluations"][0]
