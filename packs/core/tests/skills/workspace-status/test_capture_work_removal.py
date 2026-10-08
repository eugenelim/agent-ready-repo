"""Removal contract for ordinary accepted-legacy reconciliation."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

_PACK_ROOT = Path(__file__).resolve().parents[3]
_ENGINE = (
    _PACK_ROOT
    / ".apm"
    / "skills"
    / "workspace-status"
    / "scripts"
    / "workspace_status_engine.py"
)


def _load_engine():
    spec = importlib.util.spec_from_file_location(
        "core_workspace_status_capture_work_removal",
        _ENGINE,
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


# STUB: AC-0003
def test_ordinary_reconciliation_rejects_former_legacy_memberships() -> None:
    engine = _load_engine()
    source = {"mode": "repo-origin"}
    workspace = {
        "ini-001": {
            "status": "active",
            "work": {
                "queue": [
                    "spec/legacy-work",
                    {
                        "path": "docs/specs/canonical/spec.md",
                        "kind": "spec",
                        "source": source,
                        "summary": "Canonical control",
                        "needs": [],
                    },
                ],
                "active": [],
                "shipped": [],
            },
            "shaping_queue": {
                "active": [],
                "backlog": [
                    "legacy-shape",
                    {"slug": "legacy-design", "type": "design", "needs": []},
                ],
            },
            "brief_queue": {
                "draft": [],
                "ready": ["docs/product/briefs/legacy-brief.md"],
                "executing": [],
                "shipped": [],
            },
        },
        "backlog": {
            "open": [
                {
                    "slug": "legacy-backlog",
                    "source": "capture-work",
                    "summary": "Legacy backlog",
                    "needs": [],
                    "type": "spec",
                }
            ],
            "closed": [],
        },
    }

    result = engine.run_canonical_reconciliation(workspace)
    codes = [finding.code for finding in result.findings]

    assert result.legacy_memberships == []
    assert "legacy_entry" not in codes
    assert codes.count("unsupported_legacy") == 5
    assert any(
        evaluation.entry.path == "docs/specs/canonical/spec.md"
        for evaluation in result.evaluations
    )


def _section10_workspace() -> dict[str, object]:
    source = {"mode": "repo-origin"}
    return {
        "ini-001": {
            "status": "active",
            "work": {
                "queue": [
                    "spec/legacy-work",
                    {
                        "path": "docs/specs/canonical/spec.md",
                        "kind": "spec",
                        "source": source,
                        "summary": "Canonical control",
                        "needs": [],
                    },
                ],
                "active": [],
                "shipped": [],
            },
            "shaping_queue": {
                "active": [],
                "backlog": [
                    "legacy-shape",
                    {"slug": "legacy-design", "type": "design", "needs": []},
                ],
            },
            "brief_queue": {
                "draft": [],
                "ready": ["docs/product/briefs/legacy-brief.md"],
                "executing": [],
                "shipped": [],
            },
        },
        "backlog": {
            "open": [
                {
                    "slug": "legacy-backlog",
                    "source": "capture-work",
                    "summary": "Legacy backlog",
                    "needs": [],
                    "type": "spec",
                }
            ],
            "closed": [],
        },
    }


def test_section10_legacy_matrix_is_unsupported_in_ordinary_reconciliation() -> None:
    engine = _load_engine()

    result = engine.run_canonical_reconciliation(_section10_workspace())
    codes = [finding.code for finding in result.findings]

    assert result.legacy_memberships == []
    assert "legacy_entry" not in codes
    assert codes.count("unsupported_legacy") == 5


def test_legacy_aliases_do_not_affect_duplicate_or_dispatch_derivation() -> None:
    engine = _load_engine()
    workspace = {
        "ini-001": {
            "status": "active",
            "work": {
                "queue": [
                    "spec/canonical",
                    {
                        "path": "docs/specs/canonical/spec.md",
                        "kind": "spec",
                        "source": {"mode": "repo-origin"},
                        "summary": "Canonical control",
                        "needs": [],
                    },
                ],
                "active": [],
                "shipped": [],
            },
        }
    }

    result = engine.run_canonical_reconciliation(workspace)
    duplicate_paths = {
        finding.path for finding in result.findings if finding.code == "duplicate_membership"
    }

    assert "docs/specs/canonical/spec.md" not in duplicate_paths
    assert "spec/canonical" not in result.dispatch_by_path
    assert "docs/specs/canonical/spec.md" in result.dispatch_by_path


def test_legacy_aliases_do_not_affect_cooling_or_dependency_derivation(
    tmp_path: Path,
) -> None:
    engine = _load_engine()
    workspace = {
        "ini-001": {
            "status": "active",
            "work": {
                "queue": ["spec/legacy-work"],
                "active": [],
                "shipped": [],
            },
            "shaping_queue": {
                "active": ["legacy-shape"],
                "backlog": [{"slug": "legacy-design", "type": "design", "needs": []}],
            },
            "brief_queue": {"ready": ["docs/product/briefs/legacy-brief.md"]},
        }
    }

    cooled = frozenset({tmp_path / "docs/specs/legacy-work/spec.md"})
    assert engine.cooled_work_entry_paths(workspace, tmp_path, cooled) == {}

    result = engine.run_canonical_reconciliation(workspace, tmp_path)
    assert result.legacy_memberships == []
    assert result.evaluations == []


def test_status_analysis_layer_keeps_its_unchanged_view() -> None:
    """Reporting and repair read historical shapes; canonical entries are unchanged.

    Only canonical reconciliation decides dispatch, so the status-analysis layer
    keeps reporting former legacy entries, and its view of canonical entries must
    not move: canonical shaping entries stay out of the legacy shaping lists, and
    a typed local need stays unsupported there.
    """
    engine = _load_engine()
    source = {"mode": "repo-origin"}
    workspace = {
        "ini-001": {
            "status": "active",
            "work": {
                "queue": [
                    "spec/legacy-work",
                    {
                        "path": "docs/specs/canonical/spec.md",
                        "kind": "spec",
                        "source": source,
                        "summary": "Canonical with a typed need",
                        "needs": [
                            {
                                "type": "local",
                                "kind": "research",
                                "path": "docs/research/topic.md",
                            }
                        ],
                    },
                ],
                "active": [],
                "shipped": [],
            },
            "shaping_queue": {
                "active": [
                    "legacy-shape",
                    {
                        "path": "docs/product/intents/canonical.md",
                        "kind": "intent",
                        "source": source,
                        "summary": "Canonical shaping entry",
                        "needs": [],
                    },
                ],
                "backlog": [],
            },
            "brief_queue": {"ready": ["docs/product/briefs/legacy-brief.md"]},
        }
    }

    initiative = engine.extract_initiatives(workspace)[0]

    assert [entry.path for entry in initiative.work.queue] == [
        "spec/legacy-work",
        "docs/specs/canonical/spec.md",
    ]
    assert initiative.work.queue[1].needs == ["unsupported-typed-need"]
    assert [entry.slug for entry in initiative.shaping.active] == ["legacy-shape"]
    assert initiative.brief_queue is not None
    assert initiative.brief_queue.ready == ["docs/product/briefs/legacy-brief.md"]


def test_rejected_open_entries_still_count_as_initiative_residue() -> None:
    engine = _load_engine()

    def initiative(shaping: dict, brief: dict) -> object:
        workspace = {
            "ini-001": {
                "status": "active",
                "work": {"queue": [], "active": [], "shipped": []},
                "shaping_queue": shaping,
                "brief_queue": brief,
            }
        }
        return engine.extract_initiatives(workspace)[0]

    empty_shaping = {"active": [], "backlog": []}
    empty_brief = {"executing": "", "ready": [], "draft": []}

    assert not initiative(empty_shaping, empty_brief).has_unsupported_open_entry
    assert initiative(
        {"active": ["legacy-shape"], "backlog": []}, empty_brief
    ).has_unsupported_open_entry
    assert initiative(
        {"active": [], "backlog": [{"slug": "legacy-design", "type": "design"}]},
        empty_brief,
    ).has_unsupported_open_entry
    assert initiative(
        empty_shaping,
        {"executing": "", "ready": ["docs/product/briefs/legacy-brief.md"], "draft": []},
    ).has_unsupported_open_entry
    assert initiative(
        empty_shaping,
        {"executing": "docs/product/briefs/legacy-brief.md", "ready": [], "draft": []},
    ).has_unsupported_open_entry
