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


def test_surviving_alias_refuses_canonical_twin_dispatch() -> None:
    """A surviving legacy alias makes its canonical twin non-dispatchable.

    _legacy_canonical_alias maps spec/<slug> to docs/specs/<slug>/spec.md.
    When that canonical entry exists, it carries duplicate_membership and is
    excluded from dispatch. Without the alias the same entry is dispatchable.
    """
    engine = _load_engine()
    workspace_with_alias = {
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

    result = engine.run_canonical_reconciliation(workspace_with_alias)
    duplicate_paths = {
        finding.path for finding in result.findings if finding.code == "duplicate_membership"
    }

    assert "docs/specs/canonical/spec.md" in duplicate_paths
    evaluation = result.dispatch_by_path["docs/specs/canonical/spec.md"]
    assert "duplicate_membership" in {finding.code for finding in evaluation.findings}
    assert "spec/canonical" not in result.dispatch_by_path

    # Without the alias the canonical entry dispatches normally.
    workspace_without_alias = {
        "ini-001": {
            "status": "active",
            "work": {
                "queue": [
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
    clean_result = engine.run_canonical_reconciliation(workspace_without_alias)
    clean_duplicate_paths = {
        finding.path for finding in clean_result.findings
        if finding.code == "duplicate_membership"
    }
    assert "docs/specs/canonical/spec.md" not in clean_duplicate_paths


def test_legacy_aliases_do_not_affect_cooling_derivation(
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


def test_extractor_positions_cover_every_rfc0083_section10_shape() -> None:
    """extract_legacy_migration_memberships returns exact positions for every §10 shape.

    Pins (ini_slug, collection, entry_index) for each RFC-0083 section 10 shape
    including multi-entry lists and the scalar brief_queue.executing form.
    """
    engine = _load_engine()

    workspace: dict = {
        # Top-level backlog: five-key spec object at index 1 (after a non-legacy entry)
        "backlog": {
            "open": [
                {
                    "path": "docs/specs/canonical/spec.md",
                    "kind": "spec",
                    "source": {"mode": "repo-origin"},
                    "summary": "Canonical — not legacy",
                    "needs": [],
                },
                {
                    "slug": "backlog-spec",
                    "source": "capture-work",
                    "summary": "Legacy backlog spec",
                    "needs": [],
                    "type": "spec",
                },
            ],
            "closed": [],
        },
        "ini-001": {
            "status": "active",
            "work": {
                # spec/<slug> strings at indices 0 and 1
                "queue": ["spec/queue-a", "spec/queue-b"],
                "active": [],
                "shipped": [],
            },
            "shaping_queue": {
                # bare slug string at index 0; typed design dict at index 1
                "active": [
                    "bare-shaping",
                    {"slug": "design-one", "type": "design", "needs": []},
                ],
                "backlog": [
                    {"slug": "research-one", "type": "research", "needs": []},
                ],
            },
            "brief_queue": {
                # scalar executing string (legacy brief path)
                "executing": "docs/product/briefs/executing-brief.md",
                "ready": ["docs/product/briefs/ready-brief.md"],
                "draft": [],
                "shipped": [],
            },
        },
    }

    memberships = engine.extract_legacy_migration_memberships(workspace)
    positions = [
        (m.ini_slug, m.collection, m.entry_index)
        for m in memberships
    ]

    # Top-level backlog: five-key spec object is at index 1 (index 0 is canonical)
    assert ("", "backlog.open", 1) in positions

    # Initiative work.queue: two spec strings at indices 0 and 1
    assert ("ini-001", "work.queue", 0) in positions
    assert ("ini-001", "work.queue", 1) in positions

    # shaping_queue.active: bare slug at index 0, typed design at index 1
    assert ("ini-001", "shaping_queue.active", 0) in positions
    assert ("ini-001", "shaping_queue.active", 1) in positions

    # shaping_queue.backlog: typed research at index 0
    assert ("ini-001", "shaping_queue.backlog", 0) in positions

    # brief_queue.executing: scalar string becomes index 0
    assert ("ini-001", "brief_queue.executing", 0) in positions

    # brief_queue.ready: legacy brief path at index 0
    assert ("ini-001", "brief_queue.ready", 0) in positions

    # Total: 1 (backlog) + 2 (work.queue) + 2 (shaping.active) + 1 (shaping.backlog)
    #        + 1 (executing) + 1 (ready) = 8
    assert len(memberships) == 8


def test_malformed_historical_type_is_a_finding_not_an_exception() -> None:
    """A non-string `type` in a historical object ends as a finding, never a raise."""
    engine = _load_engine()
    workspace = {
        "ini-001": {
            "status": "active",
            "work": {"queue": [], "active": [], "shipped": []},
            "shaping_queue": {
                "active": [],
                "backlog": [{"slug": "x", "type": ["a"], "needs": []}],
            },
        },
        "backlog": {"open": [{"slug": "y", "type": {"k": "v"}}], "closed": []},
    }

    assert engine.extract_legacy_migration_memberships(workspace) == []
    result = engine.run_canonical_reconciliation(workspace)
    assert result.legacy_memberships == []
    assert result.evaluations == []
    assert result.findings
