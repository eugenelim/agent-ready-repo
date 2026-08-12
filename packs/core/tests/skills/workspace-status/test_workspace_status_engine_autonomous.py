"""Tests for is_need_satisfied() autonomous-dispatch mode."""
from __future__ import annotations

import importlib.util
import json
import sys
from collections.abc import Callable
from pathlib import Path
from types import SimpleNamespace

import pytest

_PACK_ROOT = Path(__file__).resolve().parents[3]
_ENGINE_PATH = (
    _PACK_ROOT / ".apm" / "skills" / "workspace-status" / "scripts"
    / "workspace_status_engine.py"
)
_CONTRACT_FIXTURES = (
    _PACK_ROOT / "tests" / "pack" / "fixtures" / "work-intake-contracts"
)


def _load_engine():
    spec = importlib.util.spec_from_file_location("workspace_status_engine", _ENGINE_PATH)
    mod = importlib.util.module_from_spec(spec)
    # Register before exec_module so dataclass string-annotation lookup finds the module.
    sys.modules["workspace_status_engine"] = mod
    spec.loader.exec_module(mod)
    return mod


def test_t1_group2_pack_contract_surface() -> None:
    mod = _load_engine()

    valid_target = json.loads(
        (
            _CONTRACT_FIXTURES
            / "workspace/target/valid/spec-with-cross-repo-need.json"
        ).read_text(encoding="utf-8")
    )
    entry, findings = mod.parse_workspace_entry(valid_target)
    assert findings == []
    assert isinstance(entry, mod.WorkspaceEntry)
    assert (entry.path, entry.kind, entry.summary) == (
        "docs/specs/self-service-reset/spec.md",
        "spec",
        "Let a user reset access without support.",
    )
    assert entry.source.mode == "tracker-origin"
    assert entry.source.ref == "example-service://projects/PROJ-123"
    assert [need.type for need in entry.needs] == ["local", "cross-repo"]
    assert entry.needs[1].receipt_id == "remote-prereq"
    assert not hasattr(entry, "dispatchable")

    for path in (_CONTRACT_FIXTURES / "workspace/target/valid").glob("*.json"):
        parsed, parsed_findings = mod.parse_workspace_entry(
            json.loads(path.read_text(encoding="utf-8"))
        )
        assert isinstance(parsed, mod.WorkspaceEntry), path.name
        assert parsed_findings == [], path.name

    legacy_cases = mod.parse_legacy_fixture_file(
        _CONTRACT_FIXTURES / "workspace/context/legacy-valid.toml"
    )
    assert legacy_cases
    assert all(isinstance(case, mod.LegacyWorkspaceEntry) for case in legacy_cases)
    assert {case.finding.code for case in legacy_cases} == {"legacy_entry"}
    assert not any(case.dispatchable for case in legacy_cases)

    invalid_legacy = mod.parse_legacy_fixture_file(
        _CONTRACT_FIXTURES / "workspace/context/legacy-invalid.toml"
    )
    assert invalid_legacy
    assert {case.finding.code for case in invalid_legacy} == {"unsupported_legacy"}
    assert not any(case.dispatchable for case in invalid_legacy)

    for collection in ("work.queue", "work.active", "work.shipped"):
        case = mod.parse_legacy_workspace_entry(collection, "spec/password-reset")
        assert case.finding.code == "legacy_entry"
    for collection in ("shaping_queue.active", "shaping_queue.backlog"):
        case = mod.parse_legacy_workspace_entry(collection, "shape-password-reset")
        assert case.finding.code == "legacy_entry"
    for collection in (
        "brief_queue.draft",
        "brief_queue.ready",
        "brief_queue.executing",
        "brief_queue.shipped",
    ):
        case = mod.parse_legacy_workspace_entry(
            collection, "docs/product/briefs/account-recovery.md"
        )
        assert case.finding.code == "legacy_entry"

    for path in (_CONTRACT_FIXTURES / "workspace/target/invalid").glob("*.json"):
        parsed, parsed_findings = mod.parse_workspace_entry(
            json.loads(path.read_text(encoding="utf-8"))
        )
        assert parsed is None, path.name
        assert parsed_findings, path.name
        expected_code = (
            "invalid_artifact_path"
            if path.name in {
                "absolute-path.json",
                "backslash-path.json",
                "dotdot-path.json",
                "empty-path.json",
                "windows-drive-path.json",
            }
            else "invalid_entry"
        )
        assert {finding.code for finding in parsed_findings} == {expected_code}, path.name

    valid_intake = json.loads(
        (
            _CONTRACT_FIXTURES
            / "normalized-intake/valid/refresh-tracker-origin.json"
        ).read_text(encoding="utf-8")
    )
    intake, intake_findings = mod.validate_normalized_intake(valid_intake)
    assert isinstance(intake, mod.NormalizedIntake)
    assert intake.action == "refresh"
    assert intake.refresh_target == "docs/specs/work-intake/spec.md"
    assert intake_findings == []

    for path in (_CONTRACT_FIXTURES / "normalized-intake/valid").glob("*.json"):
        parsed_intake, parsed_findings = mod.validate_normalized_intake(
            json.loads(path.read_text(encoding="utf-8"))
        )
        assert isinstance(parsed_intake, mod.NormalizedIntake), path.name
        assert parsed_findings == [], path.name

    for path in (_CONTRACT_FIXTURES / "normalized-intake/invalid").glob("*.json"):
        parsed_intake, parsed_findings = mod.validate_normalized_intake(
            json.loads(path.read_text(encoding="utf-8"))
        )
        assert parsed_intake is None, path.name
        assert parsed_findings, path.name
        expected_code = (
            "invalid_artifact_path"
            if path.name == "windows-drive-refresh-target.json"
            else "invalid_entry"
        )
        assert {finding.code for finding in parsed_findings} == {expected_code}, path.name

    for non_finite in (float("nan"), float("inf"), float("-inf")):
        payload = json.loads(json.dumps(valid_intake))
        payload["constraints"]["score"] = non_finite
        parsed_intake, parsed_findings = mod.validate_normalized_intake(payload)
        assert parsed_intake is None
        assert {finding.code for finding in parsed_findings} == {"invalid_entry"}


def test_t2_exact_canonical_path_shapes_and_legacy_extraction() -> None:
    mod = _load_engine()

    def source() -> dict:
        return {"mode": "repo-origin"}

    invalid_entries = [
        {
            "path": "docs/specs/nested/slug/spec.md",
            "kind": "spec",
            "source": source(),
            "summary": "Nested spec",
            "needs": [],
        },
        {
            "path": "docs/specs//spec.md",
            "kind": "spec",
            "source": source(),
            "summary": "Empty spec",
            "needs": [],
        },
        {
            "path": "docs/product/briefs/nested/brief.md",
            "kind": "brief",
            "source": source(),
            "summary": "Nested brief",
            "needs": [],
        },
        {
            "path": "docs/product/briefs/.md",
            "kind": "brief",
            "source": source(),
            "summary": "Empty brief",
            "needs": [],
        },
    ]
    for raw in invalid_entries:
        parsed, findings = mod.parse_workspace_entry(raw)
        assert parsed is None, raw["path"]
        assert {finding.code for finding in findings} == {"invalid_artifact_path"}

    workspace = {
        "ini-001": {
            "status": "active",
            "work": {
                "queue": [
                        "spec/password-reset",
                        "spec/not/accepted",
                        "../unsafe",
                        "docs/product/briefs/./unsafe.md",
                        "docs/product/briefs//unsafe.md",
                    {
                        "path": "docs/specs/malformed/spec.md",
                        "kind": "spec",
                        "source": source(),
                    },
                ],
                "active": [],
                "shipped": [],
            },
            "shaping_queue": {
                "backlog": [
                    "research-discovery",
                    {"slug": "design-review", "type": "design", "needs": []},
                    {"slug": "wrong", "source": "tracker", "summary": "Wrong", "needs": []},
                ],
                "active": ["shape-active"],
            },
            "brief_queue": {
                "ready": [
                    "docs/product/briefs/account-recovery.md",
                    "docs/product/briefs/nested/account-recovery.md",
                ],
                "draft": [],
                "executing": [],
                "shipped": [],
            },
        }
    }
    result = mod.run_canonical_reconciliation(workspace)
    scalar_legacy_by_raw = {
        membership.entry.raw: membership
        for membership in result.legacy_memberships
        if isinstance(membership.entry.raw, str)
    }
    assert set(scalar_legacy_by_raw) == {
        "spec/password-reset",
        "research-discovery",
        "shape-active",
        "docs/product/briefs/account-recovery.md",
    }
    work_legacy = scalar_legacy_by_raw["spec/password-reset"]
    assert work_legacy.ini_slug == "ini-001"
    assert work_legacy.collection == "work.queue"
    assert work_legacy.entry.path == "spec/password-reset"
    shaping_object = [
        membership
        for membership in result.legacy_memberships
        if membership.entry.raw == {"slug": "design-review", "type": "design", "needs": []}
    ]
    assert len(shaping_object) == 1
    assert shaping_object[0].entry.kind == "design"
    codes = [finding.code for finding in result.findings]
    assert "legacy_entry" in codes
    assert "unsupported_legacy" in codes
    assert codes.count("invalid_artifact_path") == 3
    assert "invalid_entry" in codes
    assert result.evaluations == []

    wrong_collection = {
        "ini-001": {
            "status": "active",
            "work": {
                "queue": [
                    {"slug": "shape-in-work", "type": "shape", "needs": []},
                ],
                "active": [],
                "shipped": [],
            },
            "shaping_queue": {
                "backlog": [
                    "spec/work-in-shaping",
                    {
                        "slug": "comment-rich",
                        "source": "tracker",
                        "summary": "Wrong collection legacy object",
                        "needs": [],
                        "type": "spec",
                    },
                ],
                "active": [],
            },
            "brief_queue": {
                "ready": ["spec/not-a-brief"],
                "draft": [],
                "executing": [],
                "shipped": [],
            },
        }
    }
    wrong_result = mod.run_canonical_reconciliation(wrong_collection)
    assert not wrong_result.legacy_memberships
    assert {finding.code for finding in wrong_result.findings} == {"unsupported_legacy"}


def test_t2_legacy_aliases_participate_in_duplicate_detection() -> None:
    mod = _load_engine()

    def source() -> dict:
        return {"mode": "repo-origin"}

    def canonical_entry(path: str, kind: str) -> dict:
        return {
            "path": path,
            "kind": kind,
            "source": source(),
            "summary": f"Summary for {path}",
            "needs": [],
        }

    cases = [
        (
            "work spec alias in same collection",
            {
                "ini-001": {
                    "status": "active",
                    "work": {
                        "queue": [
                            canonical_entry("docs/specs/alias/spec.md", "spec"),
                            "spec/alias",
                        ],
                        "active": [],
                        "shipped": [],
                    },
                }
            },
            "docs/specs/alias/spec.md",
        ),
        (
            "brief alias across collections",
            {
                "ini-001": {
                    "status": "active",
                    "brief_queue": {
                        "ready": [
                            canonical_entry("docs/product/briefs/alias-brief.md", "brief")
                        ],
                        "draft": [],
                        "executing": [],
                        "shipped": ["docs/product/briefs/alias-brief.md"],
                    },
                }
            },
            "docs/product/briefs/alias-brief.md",
        ),
        (
            "comment rich backlog spec alias",
            {
                "backlog": {
                    "open": [
                        {
                            "slug": "backlog-alias",
                            "source": "tracker",
                            "summary": "Legacy backlog item",
                            "needs": [],
                            "type": "spec",
                        }
                    ],
                    "closed": [],
                },
                "ini-001": {
                    "status": "active",
                    "work": {
                        "queue": [
                            canonical_entry("docs/specs/backlog-alias/spec.md", "spec")
                        ],
                        "active": [],
                        "shipped": [],
                    },
                }
            },
            "docs/specs/backlog-alias/spec.md",
        ),
        (
            "typed shaping alias across collections",
            {
                "ini-001": {
                    "status": "active",
                    "shaping_queue": {
                        "active": [
                            canonical_entry("docs/product/design/design-alias.md", "design")
                        ],
                        "backlog": [
                            {"slug": "design-alias", "type": "design", "needs": []}
                        ],
                    },
                }
            },
            "docs/product/design/design-alias.md",
        ),
    ]
    for name, workspace, target_path in cases:
        result = mod.run_canonical_reconciliation(workspace)
        evaluation = result.dispatch_by_path[target_path]
        assert not evaluation.dispatchable, name
        assert "duplicate_membership" in {
            finding.code for finding in evaluation.findings
        }, name
        assert "legacy_entry" in {finding.code for finding in result.findings}, name
        assert result.legacy_memberships, name

    control = {
        "ini-001": {
            "status": "active",
            "shaping_queue": {
                "active": [
                    canonical_entry("docs/product/design/ambiguous-shape.md", "design")
                ],
                "backlog": ["ambiguous-shape"],
            },
        }
    }
    result = mod.run_canonical_reconciliation(control)
    evaluation = result.dispatch_by_path["docs/product/design/ambiguous-shape.md"]
    assert "duplicate_membership" not in {finding.code for finding in evaluation.findings}
    assert "legacy_entry" in {finding.code for finding in result.findings}

    legacy_only_cases = [
        (
            "legacy spec alias in same collection",
            {
                "ini-001": {
                    "status": "active",
                    "work": {
                        "queue": ["spec/legacy-only", "spec/legacy-only"],
                        "active": [],
                        "shipped": [],
                    },
                }
            },
            "docs/specs/legacy-only/spec.md",
        ),
        (
            "legacy spec alias across collections",
            {
                "ini-001": {
                    "status": "active",
                    "work": {
                        "queue": ["spec/cross-legacy"],
                        "active": ["spec/cross-legacy"],
                        "shipped": [],
                    },
                }
            },
            "docs/specs/cross-legacy/spec.md",
        ),
        (
            "legacy brief alias across collections",
            {
                "ini-001": {
                    "status": "active",
                    "brief_queue": {
                        "ready": ["docs/product/briefs/legacy-brief.md"],
                        "draft": [],
                        "executing": [],
                        "shipped": ["docs/product/briefs/legacy-brief.md"],
                    },
                }
            },
            "docs/product/briefs/legacy-brief.md",
        ),
    ]
    for name, workspace, duplicate_path in legacy_only_cases:
        result = mod.run_canonical_reconciliation(workspace)
        duplicate_findings = [
            finding
            for finding in result.findings
            if finding.code == "duplicate_membership"
        ]
        assert result.evaluations == [], name
        assert [finding.path for finding in duplicate_findings] == [duplicate_path], name
        assert [finding.code for finding in result.findings].count("legacy_entry") == 2, name
        assert len(result.legacy_memberships) == 2, name

    legacy_only_control = {
        "ini-001": {
            "status": "active",
            "work": {
                "queue": ["spec/legacy-a"],
                "active": ["spec/legacy-b"],
                "shipped": [],
            },
            "shaping_queue": {
                "backlog": ["ambiguous-shape"],
                "active": ["ambiguous-shape"],
            },
        }
    }
    result = mod.run_canonical_reconciliation(legacy_only_control)
    assert "duplicate_membership" not in {finding.code for finding in result.findings}
    assert [finding.code for finding in result.findings].count("legacy_entry") == 4
    assert len(result.legacy_memberships) == 4


def test_t2_legacy_only_duplicate_blocks_dependent_work(tmp_path: Path) -> None:
    mod = _load_engine()

    ready_path = "docs/specs/ready/spec.md"
    blocked_dependency = "docs/specs/legacy-dependency/spec.md"
    workspace = {
        "ini-001": {
            "status": "active",
            "work": {
                "queue": [
                    {
                        "path": ready_path,
                        "kind": "spec",
                        "source": {"mode": "repo-origin"},
                        "summary": "Ready spec with legacy-only duplicate dependency.",
                        "needs": [
                            {
                                "type": "local",
                                "kind": "spec",
                                "path": blocked_dependency,
                            }
                        ],
                    },
                    "spec/legacy-dependency",
                ],
                "active": ["spec/legacy-dependency"],
                "shipped": [],
            },
        }
    }
    spec_path = tmp_path / ready_path
    spec_path.parent.mkdir(parents=True, exist_ok=True)
    spec_path.write_text(
        "# Spec\n\n"
        "- **Status:** Approved\n"
        "- **Refresh conflict:** false\n\n"
        "## Body\n",
        encoding="utf-8",
    )
    (spec_path.parent / "plan.md").write_text("# Plan\n", encoding="utf-8")

    result = mod.run_canonical_reconciliation(workspace, tmp_path)
    ready_evaluation = result.dispatch_by_path[ready_path]
    duplicate_findings = [
        finding
        for finding in result.findings
        if finding.code == "duplicate_membership"
    ]

    assert not ready_evaluation.dispatchable
    assert "unsatisfied_dependency" in {
        finding.code for finding in ready_evaluation.findings
    }
    assert [finding.path for finding in duplicate_findings] == [blocked_dependency]
    assert [finding.code for finding in result.findings].count("legacy_entry") == 2
    assert len(result.legacy_memberships) == 2


def test_t2_malformed_same_path_blocks_canonical_membership() -> None:
    mod = _load_engine()

    def source() -> dict:
        return {"mode": "repo-origin"}

    def canonical_entry(path: str) -> dict:
        return {
            "path": path,
            "kind": "spec",
            "source": source(),
            "summary": f"Summary for {path}",
            "needs": [],
        }

    same_path = "docs/specs/same-path/spec.md"
    malformed_same_path = {
        "path": same_path,
        "kind": "spec",
        "source": source(),
        "summary": "Malformed target-like entry is missing needs.",
    }
    cases = [
        (
            "same collection",
            {
                "ini-001": {
                    "status": "active",
                    "work": {
                        "queue": [canonical_entry(same_path), malformed_same_path],
                        "active": [],
                        "shipped": [],
                    },
                }
            },
        ),
        (
            "cross collection",
            {
                "ini-001": {
                    "status": "active",
                    "work": {
                        "queue": [canonical_entry(same_path)],
                        "active": [malformed_same_path],
                        "shipped": [],
                    },
                }
            },
        ),
    ]
    for name, workspace in cases:
        result = mod.run_canonical_reconciliation(workspace)
        evaluation = result.dispatch_by_path[same_path]
        assert not evaluation.dispatchable, name
        assert "duplicate_membership" in {
            finding.code for finding in evaluation.findings
        }, name
        assert "invalid_entry" in {finding.code for finding in result.findings}, name

    unique_path = "docs/specs/malformed-unique/spec.md"
    unique_result = mod.run_canonical_reconciliation(
        {
            "ini-001": {
                "status": "active",
                "work": {
                    "queue": [
                        {
                            "path": unique_path,
                            "kind": "spec",
                            "source": source(),
                            "summary": "Malformed unique entry is missing needs.",
                        }
                    ],
                    "active": [],
                    "shipped": [],
                },
            }
        }
    )
    assert unique_result.evaluations == []
    assert {finding.code for finding in unique_result.findings} == {"invalid_entry"}

    mixed_path = "docs/specs/mixed/spec.md"
    malformed_mixed = {
        "path": mixed_path,
        "kind": "spec",
        "source": source(),
        "summary": "Malformed mixed entry is missing needs.",
    }
    mixed_cases = [
        (
            "same collection mixed",
            {
                "ini-001": {
                    "status": "active",
                    "work": {
                        "queue": [malformed_mixed, "spec/mixed"],
                        "active": [],
                        "shipped": [],
                    },
                }
            },
        ),
        (
            "cross collection mixed",
            {
                "ini-001": {
                    "status": "active",
                    "work": {
                        "queue": [malformed_mixed],
                        "active": ["spec/mixed"],
                        "shipped": [],
                    },
                }
            },
        ),
    ]
    for name, workspace in mixed_cases:
        result = mod.run_canonical_reconciliation(workspace)
        assert result.evaluations == [], name
        assert [finding.code for finding in result.findings].count("invalid_entry") == 1
        assert [finding.code for finding in result.findings].count("legacy_entry") == 1
        assert [
            finding.path
            for finding in result.findings
            if finding.code == "duplicate_membership"
        ] == [mixed_path], name

    non_collision_result = mod.run_canonical_reconciliation(
        {
            "ini-001": {
                "status": "active",
                "work": {
                    "queue": [
                        {
                            "path": "docs/specs/mixed-other/spec.md",
                            "kind": "spec",
                            "source": source(),
                            "summary": "Malformed mixed entry is missing needs.",
                        },
                        "spec/mixed",
                    ],
                    "active": [],
                    "shipped": [],
                },
            }
        }
    )
    assert "duplicate_membership" not in {
        finding.code for finding in non_collision_result.findings
    }

    unsafe_mixed_result = mod.run_canonical_reconciliation(
        {
            "ini-001": {
                "status": "active",
                "work": {
                    "queue": [
                        {
                            "path": "../mixed",
                            "kind": "spec",
                            "source": source(),
                            "summary": "Unsafe target-like path.",
                            "needs": [],
                        },
                        "spec/mixed",
                    ],
                    "active": [],
                    "shipped": [],
                },
            }
        }
    )
    assert "duplicate_membership" not in {
        finding.code for finding in unsafe_mixed_result.findings
    }
    assert "invalid_artifact_path" in {
        finding.code for finding in unsafe_mixed_result.findings
    }


def test_t2_parse_only_duplicates_emit_result_level_finding() -> None:
    mod = _load_engine()

    def source() -> dict:
        return {"mode": "repo-origin"}

    def malformed(path: str, summary: str) -> dict:
        return {
            "path": path,
            "kind": "spec",
            "source": source(),
            "summary": summary,
        }

    duplicate_path = "docs/specs/parse-only/spec.md"
    cases = [
        (
            "same collection",
            {
                "ini-001": {
                    "status": "active",
                    "work": {
                        "queue": [
                            malformed(duplicate_path, "First malformed entry."),
                            malformed(duplicate_path, "Second malformed entry."),
                        ],
                        "active": [],
                        "shipped": [],
                    },
                }
            },
            2,
        ),
        (
            "cross collection",
            {
                "ini-001": {
                    "status": "active",
                    "work": {
                        "queue": [malformed(duplicate_path, "Queue malformed entry.")],
                        "active": [malformed(duplicate_path, "Active malformed entry.")],
                        "shipped": [],
                    },
                }
            },
            2,
        ),
        (
            "three way",
            {
                "ini-001": {
                    "status": "active",
                    "work": {
                        "queue": [
                            malformed(duplicate_path, "First malformed entry."),
                            malformed(duplicate_path, "Second malformed entry."),
                        ],
                        "active": [malformed(duplicate_path, "Third malformed entry.")],
                        "shipped": [],
                    },
                }
            },
            3,
        ),
    ]
    for name, workspace, invalid_count in cases:
        result = mod.run_canonical_reconciliation(workspace)
        assert result.evaluations == [], name
        assert [finding.code for finding in result.findings].count("invalid_entry") == (
            invalid_count
        )
        assert [
            finding.path
            for finding in result.findings
            if finding.code == "duplicate_membership"
        ] == [duplicate_path], name

    unique_result = mod.run_canonical_reconciliation(
        {
            "ini-001": {
                "status": "active",
                "work": {
                    "queue": [malformed("docs/specs/parse-a/spec.md", "A")],
                    "active": [malformed("docs/specs/parse-b/spec.md", "B")],
                    "shipped": [],
                },
            }
        }
    )
    assert "duplicate_membership" not in {finding.code for finding in unique_result.findings}

    unsafe_result = mod.run_canonical_reconciliation(
        {
            "ini-001": {
                "status": "active",
                "work": {
                    "queue": [
                        {
                            "path": "../parse-only",
                            "kind": "spec",
                            "source": source(),
                            "summary": "Unsafe malformed entry.",
                            "needs": [],
                        },
                        {
                            "path": "../parse-only",
                            "kind": "spec",
                            "source": source(),
                            "summary": "Unsafe malformed entry two.",
                            "needs": [],
                        },
                    ],
                    "active": [],
                    "shipped": [],
                },
            }
        }
    )
    assert "duplicate_membership" not in {finding.code for finding in unsafe_result.findings}
    assert [finding.code for finding in unsafe_result.findings].count(
        "invalid_artifact_path"
    ) == 2


def test_t2_ref_revision_provenance_is_tracker_origin_only() -> None:
    mod = _load_engine()

    def entry(path: str, source: dict) -> dict:
        return {
            "path": path,
            "kind": "spec",
            "source": source,
            "summary": f"Summary for {path}",
            "needs": [],
        }

    def workspace(entries: list[dict]) -> dict:
        return {
            "ini-001": {
                "status": "active",
                "work": {"queue": entries, "active": [], "shipped": []},
            }
        }

    metadata_by_path = {
        "docs/specs/repo-ref/spec.md": mod.ArtifactMetadata(
            path="docs/specs/repo-ref/spec.md",
            kind="spec",
            status="Approved",
            exists=True,
            plan_exists=True,
            plan_readable=True,
        ),
        "docs/specs/tracker-match/spec.md": mod.ArtifactMetadata(
            path="docs/specs/tracker-match/spec.md",
            kind="spec",
            status="Approved",
            exists=True,
            plan_exists=True,
            plan_readable=True,
            ref="example-service://tracker/match",
            revision="rev-1",
        ),
        "docs/specs/tracker-mismatch/spec.md": mod.ArtifactMetadata(
            path="docs/specs/tracker-mismatch/spec.md",
            kind="spec",
            status="Approved",
            exists=True,
            plan_exists=True,
            plan_readable=True,
            ref="example-service://tracker/other",
            revision="rev-2",
        ),
    }

    def fake_metadata(_workspace: dict, parsed_entry, _root: Path | None):
        return metadata_by_path[parsed_entry.path]

    mod._artifact_metadata = fake_metadata
    result = mod.run_canonical_reconciliation(
        workspace(
            [
                entry(
                    "docs/specs/repo-ref/spec.md",
                    {
                        "mode": "repo-origin",
                        "ref": "example-service://repo/citation",
                    },
                ),
                entry(
                    "docs/specs/tracker-match/spec.md",
                    {
                        "mode": "tracker-origin",
                        "ref": "example-service://tracker/match",
                        "revision": "rev-1",
                    },
                ),
                entry(
                    "docs/specs/tracker-mismatch/spec.md",
                    {
                        "mode": "tracker-origin",
                        "ref": "example-service://tracker/mismatch",
                        "revision": "rev-1",
                    },
                ),
            ]
        )
    )

    assert result.dispatch_by_path["docs/specs/repo-ref/spec.md"].findings == []
    assert result.dispatch_by_path["docs/specs/tracker-match/spec.md"].findings == []
    assert "provenance_mismatch" in {
        finding.code
        for finding in result.dispatch_by_path[
            "docs/specs/tracker-mismatch/spec.md"
        ].findings
    }


def test_t2_positive_dispatch_and_reconciliation_surface(tmp_path: Path) -> None:
    mod = _load_engine()

    def source(parent: str | None = "docs/product/briefs/parent.md") -> dict:
        data = {"mode": "repo-origin"}
        if parent is not None:
            data["parent"] = parent
        return data

    def entry(
        path: str,
        *,
        kind: str = "spec",
        parent: str | None = "docs/product/briefs/parent.md",
        needs: list[dict] | None = None,
    ) -> dict:
        return {
            "path": path,
            "kind": kind,
            "source": source(parent),
            "summary": f"Summary for {path}",
            "needs": needs or [],
        }

    def workspace() -> dict:
        return {
            "ini-001": {
                "status": "active",
                "work": {
                    "queue": [
                        entry(
                            "docs/specs/ready/spec.md",
                            needs=[
                                {
                                    "type": "local",
                                    "kind": "design",
                                    "path": "docs/product/design/approved.md",
                                },
                            ],
                        )
                    ],
                    "active": [],
                    "shipped": [
                        entry(
                            "docs/specs/shipped/spec.md",
                            parent="docs/product/briefs/done.md",
                        )
                    ],
                    },
                    "shaping_queue": {
                        "backlog": [],
                        "active": [],
                },
                "brief_queue": {
                    "ready": [
                        entry(
                            "docs/product/briefs/ready-without-specs.md",
                            kind="brief",
                            parent="docs/product/intents/parent.md",
                        )
                    ],
                    "draft": [],
                    "executing": [],
                    "shipped": [],
                },
            },
        }

    def write_artifact(
        rel_path: str,
        *,
        status: str,
        parent: str | None = None,
        refresh_conflict: bool = False,
        plan: bool = False,
        resolution: str | None = None,
    ) -> None:
        path = tmp_path / rel_path
        path.parent.mkdir(parents=True, exist_ok=True)
        parent_field = f"- **Brief:** {parent}\n" if parent is not None else ""
        refresh_field = f"- **Refresh conflict:** {str(refresh_conflict).lower()}\n"
        resolution_field = f"- **Resolution:** {resolution}\n" if resolution is not None else ""
        path.write_text(
            "# Artifact\n\n"
            f"- **Status:** {status}\n"
            f"{parent_field}{refresh_field}{resolution_field}\n"
            "## Body\n",
            encoding="utf-8",
        )
        if plan:
            plan_path = path.parent / "plan.md"
            if plan_path.is_symlink():
                plan_path.unlink()
            elif plan_path.is_dir():
                plan_path.rmdir()
            plan_path.write_text("# Plan\n", encoding="utf-8")

    def write_base_artifacts() -> None:
        write_artifact(
            "docs/specs/ready/spec.md",
            status="Approved",
            parent="docs/product/briefs/parent.md",
            plan=True,
        )
        write_artifact(
            "docs/specs/shipped/spec.md",
            status="Shipped",
            parent="docs/product/briefs/done.md",
            plan=True,
        )
        write_artifact(
            "docs/product/design/approved.md",
            status="Approved",
            parent="docs/product/intents/parent.md",
        )
        write_artifact(
            "docs/product/briefs/ready-without-specs.md",
            status="Ready",
            parent="docs/product/intents/parent.md",
        )

    def escape_ready_plan() -> None:
        (tmp_path / "docs/specs/ready/plan.md").unlink()
        escaped_plan = tmp_path.parent / "escaped-plan.md"
        escaped_plan.write_text("# Plan\n", encoding="utf-8")
        try:
            (tmp_path / "docs/specs/ready/plan.md").symlink_to(escaped_plan)
        except OSError:
            pytest.skip("symlink creation is unavailable in this environment")

    write_base_artifacts()
    result = mod.run_canonical_reconciliation(workspace(), tmp_path)
    ready_eval = result.dispatch_by_path["docs/specs/ready/spec.md"]
    assert ready_eval.dispatchable
    assert ready_eval.findings == []
    assert result.dispatch_by_path["docs/product/briefs/ready-without-specs.md"].findings == []
    assert not result.dispatch_by_path["docs/product/briefs/ready-without-specs.md"].dispatchable

    cases: list[tuple[str, Callable[[dict], None], str]] = [
        (
            "missing_artifact",
            lambda _ws: (tmp_path / "docs/specs/ready/spec.md").unlink(),
            "missing_artifact",
        ),
        (
            "missing_plan",
            lambda _ws: (tmp_path / "docs/specs/ready/plan.md").unlink(),
            "missing_plan",
        ),
        (
            "escaped_plan",
            lambda _ws: escape_ready_plan(),
            "invalid_artifact_path",
        ),
        (
            "directory_plan",
            lambda _ws: (
                (tmp_path / "docs/specs/ready/plan.md").unlink(),
                (tmp_path / "docs/specs/ready/plan.md").mkdir(),
            ),
            "unreadable_artifact",
        ),
        (
            "unapproved_spec",
            lambda _ws: write_artifact(
                "docs/specs/ready/spec.md",
                status="Draft",
                parent="docs/product/briefs/parent.md",
                plan=True,
            ),
            "unapproved_spec",
        ),
        (
            "inactive_initiative",
            lambda ws: ws["ini-001"].__setitem__("status", "paused"),
            "inactive_initiative",
        ),
        (
            "provenance_mismatch",
            lambda _ws: write_artifact(
                "docs/specs/ready/spec.md",
                status="Approved",
                parent="docs/product/briefs/other.md",
                plan=True,
            ),
            "provenance_mismatch",
        ),
        (
            "missing_workspace_parent",
            lambda ws: (
                ws["ini-001"]["work"]["queue"].__setitem__(
                    0,
                    entry("docs/specs/ready/spec.md", parent=None),
                )
            ),
            "provenance_mismatch",
        ),
        (
            "refresh_conflict",
            lambda _ws: write_artifact(
                "docs/specs/ready/spec.md",
                status="Approved",
                parent="docs/product/briefs/parent.md",
                refresh_conflict=True,
                plan=True,
            ),
            "refresh_conflict",
        ),
        (
            "missing_dependency",
            lambda _ws: (tmp_path / "docs/product/design/approved.md").unlink(),
            "missing_dependency",
        ),
        (
            "unsatisfied_dependency",
            lambda _ws: write_artifact(
                "docs/product/design/approved.md",
                status="Draft",
                parent="docs/product/intents/parent.md",
            ),
            "unsatisfied_dependency",
        ),
    ]
    for name, mutate, expected in cases:
        write_base_artifacts()
        changed = workspace()
        mutate(changed)
        evaluation = mod.run_canonical_reconciliation(changed, tmp_path).dispatch_by_path[
            "docs/specs/ready/spec.md"
        ]
        assert not evaluation.dispatchable, name
        assert expected in {finding.code for finding in evaluation.findings}, name

    duplicate = workspace()
    duplicate["ini-001"]["work"]["active"].append(entry("docs/specs/ready/spec.md"))
    write_base_artifacts()
    duplicate_eval = mod.run_canonical_reconciliation(duplicate, tmp_path).dispatch_by_path[
        "docs/specs/ready/spec.md"
    ]
    assert "duplicate_membership" in {finding.code for finding in duplicate_eval.findings}

    impossible = workspace()
    impossible["ini-001"]["work"]["active"].append(entry("docs/specs/draft-active/spec.md"))
    write_base_artifacts()
    write_artifact(
        "docs/specs/draft-active/spec.md",
        status="Draft",
        parent="docs/product/briefs/parent.md",
        plan=True,
    )
    impossible_eval = mod.run_canonical_reconciliation(impossible, tmp_path).dispatch_by_path[
        "docs/specs/draft-active/spec.md"
    ]
    assert "impossible_transition" in {finding.code for finding in impossible_eval.findings}

    cycle = workspace()
    cycle["ini-001"]["work"]["queue"] = [
        entry(
            "docs/specs/a/spec.md",
            needs=[{"type": "local", "kind": "spec", "path": "docs/specs/b/spec.md"}],
        ),
        entry(
            "docs/specs/b/spec.md",
            needs=[{"type": "local", "kind": "spec", "path": "docs/specs/a/spec.md"}],
        ),
    ]
    write_base_artifacts()
    write_artifact(
        "docs/specs/a/spec.md",
        status="Approved",
        parent="docs/product/briefs/parent.md",
        plan=True,
    )
    write_artifact(
        "docs/specs/b/spec.md",
        status="Approved",
        parent="docs/product/briefs/parent.md",
        plan=True,
    )
    cycle_result = mod.run_canonical_reconciliation(cycle, tmp_path)
    assert {
        finding.code
        for evaluation in cycle_result.dispatch_by_path.values()
        for finding in evaluation.findings
    } >= {"dependency_cycle"}

    no_parent = workspace()
    no_parent["ini-001"]["work"]["queue"] = [entry("docs/specs/no-parent/spec.md", parent=None)]
    write_artifact("docs/specs/no-parent/spec.md", status="Approved", parent="none", plan=True)
    no_parent_eval = mod.run_canonical_reconciliation(no_parent, tmp_path).dispatch_by_path[
        "docs/specs/no-parent/spec.md"
    ]
    assert no_parent_eval.dispatchable

    parent_shape_cases = [
        (
            "workspace nested parent",
            "docs/product/briefs/nested/parent.md",
            "docs/product/briefs/parent.md",
            {"invalid_artifact_path", "provenance_mismatch"},
        ),
        (
            "artifact nested parent",
            "docs/product/briefs/parent.md",
            "docs/product/briefs/nested/parent.md",
            {"invalid_artifact_path", "provenance_mismatch"},
        ),
        (
            "matching nested parents",
            "docs/product/briefs/nested/parent.md",
            "docs/product/briefs/nested/parent.md",
            {"invalid_artifact_path"},
        ),
        (
            "matching canonical parent",
            "docs/product/briefs/parent.md",
            "docs/product/briefs/parent.md",
            set(),
        ),
    ]
    for name, workspace_parent, artifact_parent, expected in parent_shape_cases:
        changed = workspace()
        changed["ini-001"]["work"]["queue"] = [
            entry("docs/specs/parent-shape/spec.md", parent=workspace_parent)
        ]
        write_artifact(
            "docs/specs/parent-shape/spec.md",
            status="Approved",
            parent=artifact_parent,
            plan=True,
        )
        evaluation = mod.run_canonical_reconciliation(changed, tmp_path).dispatch_by_path[
            "docs/specs/parent-shape/spec.md"
        ]
        codes = {finding.code for finding in evaluation.findings}
        assert expected.issubset(codes), name
        assert evaluation.dispatchable is (not expected), name

    non_spec_parent = workspace()
    non_spec_parent["ini-001"]["shaping_queue"]["backlog"].append(
        entry(
            "docs/product/design/non-spec-parent.md",
            kind="design",
            parent="docs/product/intents/parent.md",
        )
    )
    write_artifact(
        "docs/product/design/non-spec-parent.md",
        status="Draft",
        parent="docs/product/intents/parent.md",
    )
    non_spec_eval = mod.run_canonical_reconciliation(non_spec_parent, tmp_path).dispatch_by_path[
        "docs/product/design/non-spec-parent.md"
    ]
    assert "invalid_artifact_path" not in {finding.code for finding in non_spec_eval.findings}

    escape = workspace()
    escape["ini-001"]["work"]["queue"] = [entry("docs/specs/escape/spec.md")]
    escape_target = tmp_path.parent / "escaped-spec.md"
    escape_target.write_text("- **Status:** Approved\n", encoding="utf-8")
    escape_path = tmp_path / "docs/specs/escape/spec.md"
    escape_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        escape_path.symlink_to(escape_target)
    except OSError:
        pytest.skip("symlink creation is unavailable in this environment")
    escape_eval = mod.run_canonical_reconciliation(escape, tmp_path).dispatch_by_path[
        "docs/specs/escape/spec.md"
    ]
    assert "invalid_artifact_path" in {finding.code for finding in escape_eval.findings}

    brief_mismatch = workspace()
    write_artifact(
        "docs/product/briefs/ready-without-specs.md",
        status="Draft",
        parent="docs/product/intents/parent.md",
    )
    brief_eval = mod.run_canonical_reconciliation(brief_mismatch, tmp_path).dispatch_by_path[
        "docs/product/briefs/ready-without-specs.md"
    ]
    assert "impossible_transition" in {finding.code for finding in brief_eval.findings}

    shaping_impossible = workspace()
    shaping_impossible["ini-001"]["shaping_queue"]["active"].append(
        entry(
            "docs/product/design/approved.md",
            kind="design",
            parent="docs/product/intents/parent.md",
        )
    )
    shaping_eval = mod.run_canonical_reconciliation(
        shaping_impossible, tmp_path
    ).dispatch_by_path["docs/product/design/approved.md"]
    assert "impossible_transition" in {finding.code for finding in shaping_eval.findings}

    defect_lifecycle = {
        "backlog": {
            "open": [entry("docs/product/defects/open.md", kind="defect", parent=None)],
            "closed": [entry("docs/product/defects/closed.md", kind="defect", parent=None)],
        }
    }
    write_artifact("docs/product/defects/open.md", status="Closed", resolution="fixed")
    write_artifact("docs/product/defects/closed.md", status="Open")
    defect_result = mod.run_canonical_reconciliation(defect_lifecycle, tmp_path)
    assert {
        finding.code
        for evaluation in defect_result.dispatch_by_path.values()
        for finding in evaluation.findings
    } >= {"impossible_transition"}

    invalid_parent = workspace()
    write_artifact(
        "docs/specs/ready/spec.md",
        status="Approved",
        parent="../outside.md",
        plan=True,
    )
    invalid_parent_eval = mod.run_canonical_reconciliation(
        invalid_parent, tmp_path
    ).dispatch_by_path["docs/specs/ready/spec.md"]
    assert "invalid_artifact_path" in {finding.code for finding in invalid_parent_eval.findings}

    parent_target = tmp_path.parent / "escaped-parent.md"
    parent_target.write_text("# Parent\n", encoding="utf-8")
    parent_link = tmp_path / "docs/product/briefs/escaped-parent.md"
    parent_link.parent.mkdir(parents=True, exist_ok=True)
    try:
        parent_link.symlink_to(parent_target)
    except OSError:
        pytest.skip("symlink creation is unavailable in this environment")
    escaped_parent = workspace()
    escaped_parent["ini-001"]["work"]["queue"] = [
        entry("docs/specs/escaped-parent/spec.md", parent="docs/product/briefs/escaped-parent.md")
    ]
    write_artifact(
        "docs/specs/escaped-parent/spec.md",
        status="Approved",
        parent="docs/product/briefs/escaped-parent.md",
        plan=True,
    )
    escaped_parent_eval = mod.run_canonical_reconciliation(
        escaped_parent, tmp_path
    ).dispatch_by_path["docs/specs/escaped-parent/spec.md"]
    assert "invalid_artifact_path" in {
        finding.code for finding in escaped_parent_eval.findings
    }

    backlog_lifecycle = {
        "backlog": {
            "open": [
                entry("docs/specs/backlog-approved/spec.md", parent=None),
                entry("docs/product/intents/backlog-accepted.md", kind="intent", parent=None),
            ],
            "closed": [
                entry("docs/product/intents/backlog-draft.md", kind="intent", parent=None),
            ],
        }
    }
    write_artifact("docs/specs/backlog-approved/spec.md", status="Approved", plan=True)
    write_artifact("docs/product/intents/backlog-accepted.md", status="Accepted")
    write_artifact("docs/product/intents/backlog-draft.md", status="Draft")
    backlog_result = mod.run_canonical_reconciliation(backlog_lifecycle, tmp_path)
    assert all(
        "impossible_transition" in {finding.code for finding in evaluation.findings}
        for evaluation in backlog_result.evaluations
    )

    noncanonical_ini = {
        "ini-alpha": {
            "status": "active",
            "work": {
                "queue": [
                    entry(
                        "docs/specs/noncanonical/spec.md",
                        parent="docs/product/briefs/parent.md",
                    )
                ],
                "active": [],
                "shipped": [],
            },
            "shaping_queue": {"backlog": [], "active": []},
        }
    }
    write_artifact(
        "docs/specs/noncanonical/spec.md",
        status="Approved",
        parent="docs/product/briefs/parent.md",
        plan=True,
    )
    noncanonical_result = mod.run_canonical_reconciliation(noncanonical_ini, tmp_path)
    assert {finding.code for finding in noncanonical_result.findings} == {"invalid_workspace"}
    assert "docs/specs/noncanonical/spec.md" not in noncanonical_result.dispatch_by_path

    malformed_unrelated = workspace()
    malformed_unrelated["backlog"] = "invalid"
    malformed_result = mod.run_canonical_reconciliation(malformed_unrelated, tmp_path)
    malformed_ready = malformed_result.dispatch_by_path["docs/specs/ready/spec.md"]
    assert not malformed_ready.dispatchable
    assert "invalid_workspace" in {finding.code for finding in malformed_ready.findings}

    malformed_sections = [
        ("top-level backlog", {"backlog": "invalid"}),
        ("initiative work", {"ini-001": {"status": "active", "work": "invalid"}}),
        (
            "initiative shaping",
            {"ini-001": {"status": "paused", "shaping_queue": "invalid"}},
        ),
        (
            "initiative brief",
            {"ini-001": {"status": "closed", "brief_queue": "invalid"}},
        ),
    ]
    for _name, malformed_workspace in malformed_sections:
        result = mod.run_canonical_reconciliation(malformed_workspace, tmp_path)
        assert "invalid_workspace" in {finding.code for finding in result.findings}

    backlog_closed_restrictions = {
        "backlog": {
            "open": [],
            "closed": [
                entry("docs/specs/closed-spec/spec.md", parent=None),
                entry("docs/product/defects/closed-fixed.md", kind="defect", parent=None),
                entry("docs/product/defects/closed-unknown.md", kind="defect", parent=None),
            ],
        }
    }
    write_artifact("docs/specs/closed-spec/spec.md", status="Shipped", plan=True)
    write_artifact("docs/product/defects/closed-fixed.md", status="Closed", resolution="fixed")
    write_artifact("docs/product/defects/closed-unknown.md", status="Closed")
    backlog_closed_result = mod.run_canonical_reconciliation(
        backlog_closed_restrictions, tmp_path
    )
    closed_codes = {
        path: {finding.code for finding in evaluation.findings}
        for path, evaluation in backlog_closed_result.dispatch_by_path.items()
    }
    assert "impossible_transition" in closed_codes["docs/specs/closed-spec/spec.md"]
    assert not closed_codes["docs/product/defects/closed-fixed.md"]
    assert "impossible_transition" in closed_codes["docs/product/defects/closed-unknown.md"]


def test_t2_active_and_shipped_specs_validate_sibling_plan(tmp_path: Path) -> None:
    mod = _load_engine()

    def entry(path: str) -> dict:
        return {
            "path": path,
            "kind": "spec",
            "source": {"mode": "repo-origin"},
            "summary": f"Summary for {path}",
            "needs": [],
        }

    def workspace() -> dict:
        return {
            "ini-001": {
                "status": "active",
                "work": {
                    "queue": [],
                    "active": [entry("docs/specs/active/spec.md")],
                    "shipped": [entry("docs/specs/shipped/spec.md")],
                },
            }
        }

    def write_spec(rel_path: str, status: str, *, plan: bool = True) -> None:
        path = tmp_path / rel_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            "# Spec\n\n"
            f"- **Status:** {status}\n"
            "- **Refresh conflict:** false\n\n"
            "## Body\n",
            encoding="utf-8",
        )
        if plan:
            plan_path = path.parent / "plan.md"
            if plan_path.is_dir():
                plan_path.rmdir()
            elif plan_path.exists() or plan_path.is_symlink():
                plan_path.unlink()
            plan_path.write_text("# Plan\n", encoding="utf-8")

    def write_valid_specs() -> None:
        write_spec("docs/specs/active/spec.md", "Implementing")
        write_spec("docs/specs/shipped/spec.md", "Shipped")

    write_valid_specs()
    valid_result = mod.run_canonical_reconciliation(workspace(), tmp_path)
    assert valid_result.dispatch_by_path["docs/specs/active/spec.md"].findings == []
    assert valid_result.dispatch_by_path["docs/specs/shipped/spec.md"].findings == []

    cases: list[tuple[str, str, Callable[[], None], str]] = [
        (
            "active missing plan",
            "docs/specs/active/spec.md",
            lambda: (tmp_path / "docs/specs/active/plan.md").unlink(),
            "missing_plan",
        ),
        (
            "shipped missing plan",
            "docs/specs/shipped/spec.md",
            lambda: (tmp_path / "docs/specs/shipped/plan.md").unlink(),
            "missing_plan",
        ),
        (
            "active directory plan",
            "docs/specs/active/spec.md",
            lambda: (
                (tmp_path / "docs/specs/active/plan.md").unlink(),
                (tmp_path / "docs/specs/active/plan.md").mkdir(),
            ),
            "unreadable_artifact",
        ),
        (
            "shipped directory plan",
            "docs/specs/shipped/spec.md",
            lambda: (
                (tmp_path / "docs/specs/shipped/plan.md").unlink(),
                (tmp_path / "docs/specs/shipped/plan.md").mkdir(),
            ),
            "unreadable_artifact",
        ),
    ]
    for name, target_path, mutate, expected in cases:
        write_valid_specs()
        mutate()
        evaluation = mod.run_canonical_reconciliation(workspace(), tmp_path).dispatch_by_path[
            target_path
        ]
        assert expected in {finding.code for finding in evaluation.findings}, name


def test_t2_workspace_parent_validated_for_missing_and_unreadable_specs(
    tmp_path: Path,
) -> None:
    mod = _load_engine()

    def entry(path: str, parent: str) -> dict:
        return {
            "path": path,
            "kind": "spec",
            "source": {"mode": "repo-origin", "parent": parent},
            "summary": f"Summary for {path}",
            "needs": [],
        }

    def workspace(path: str, parent: str) -> dict:
        return {
            "ini-001": {
                "status": "active",
                "work": {
                    "queue": [entry(path, parent)],
                    "active": [],
                    "shipped": [],
                },
            }
        }

    def make_unreadable_artifact(path: str) -> None:
        artifact_path = tmp_path / path
        artifact_path.parent.mkdir(parents=True, exist_ok=True)
        artifact_path.mkdir()

    cases = [
        (
            "missing malformed parent",
            "docs/specs/missing-bad-parent/spec.md",
            "docs/product/briefs/nested/parent.md",
            lambda _path: None,
            {"missing_artifact", "invalid_artifact_path"},
        ),
        (
            "missing canonical parent",
            "docs/specs/missing-good-parent/spec.md",
            "docs/product/briefs/parent.md",
            lambda _path: None,
            {"missing_artifact"},
        ),
        (
            "unreadable malformed parent",
            "docs/specs/unreadable-bad-parent/spec.md",
            "docs/product/briefs/nested/parent.md",
            make_unreadable_artifact,
            {"unreadable_artifact", "invalid_artifact_path"},
        ),
        (
            "unreadable canonical parent",
            "docs/specs/unreadable-good-parent/spec.md",
            "docs/product/briefs/parent.md",
            make_unreadable_artifact,
            {"unreadable_artifact"},
        ),
    ]
    for name, path, parent, setup, expected in cases:
        setup(path)
        evaluation = mod.run_canonical_reconciliation(
            workspace(path, parent), tmp_path
        ).dispatch_by_path[path]
        assert expected.issubset({finding.code for finding in evaluation.findings}), name


def test_t2_collection_kind_validated_for_missing_and_unreadable_artifacts(
    tmp_path: Path,
) -> None:
    mod = _load_engine()

    def entry(path: str, kind: str) -> dict:
        return {
            "path": path,
            "kind": kind,
            "source": {"mode": "repo-origin"},
            "summary": f"Summary for {path}",
            "needs": [],
        }

    cases = [
        (
            "brief in work queue missing",
            {"work": {"queue": [entry("docs/product/briefs/wrong-work.md", "brief")]}},
            "docs/product/briefs/wrong-work.md",
            lambda _path: None,
            {"impossible_transition", "missing_artifact"},
        ),
        (
            "spec in brief ready missing",
            {
                "brief_queue": {
                    "ready": [entry("docs/specs/wrong-brief/spec.md", "spec")]
                }
            },
            "docs/specs/wrong-brief/spec.md",
            lambda _path: None,
            {"impossible_transition", "missing_artifact"},
        ),
        (
            "brief in shaping active unreadable",
            {
                "shaping_queue": {
                    "active": [entry("docs/product/briefs/wrong-shaping.md", "brief")]
                }
            },
            "docs/product/briefs/wrong-shaping.md",
            lambda path: (tmp_path / path).mkdir(parents=True),
            {"impossible_transition", "unreadable_artifact"},
        ),
        (
            "spec in work queue missing control",
            {"work": {"queue": [entry("docs/specs/missing-control/spec.md", "spec")]}},
            "docs/specs/missing-control/spec.md",
            lambda _path: None,
            {"missing_artifact"},
        ),
        (
            "brief in brief ready unreadable control",
            {
                "brief_queue": {
                    "ready": [entry("docs/product/briefs/unreadable-control.md", "brief")]
                }
            },
            "docs/product/briefs/unreadable-control.md",
            lambda path: (tmp_path / path).mkdir(parents=True),
            {"unreadable_artifact"},
        ),
    ]
    for name, sections, target_path, setup, expected in cases:
        workspace = {
            "ini-001": {
                "status": "active",
                "work": {"queue": [], "active": [], "shipped": []},
                "shaping_queue": {"backlog": [], "active": []},
                "brief_queue": {"draft": [], "ready": [], "executing": [], "shipped": []},
            }
        }
        for section_name, values in sections.items():
            for list_name, entries in values.items():
                workspace["ini-001"][section_name][list_name] = entries
        setup(target_path)
        evaluation = mod.run_canonical_reconciliation(workspace, tmp_path).dispatch_by_path[
            target_path
        ]
        assert {finding.code for finding in evaluation.findings} == expected, name


def test_t2_collection_kind_and_brief_child_state_matrix(tmp_path: Path) -> None:
    mod = _load_engine()

    def entry(
        path: str,
        *,
        kind: str = "spec",
        parent: str | None = None,
    ) -> dict:
        source = {"mode": "repo-origin"}
        if parent is not None:
            source["parent"] = parent
        return {
            "path": path,
            "kind": kind,
            "source": source,
            "summary": f"Summary for {path}",
            "needs": [],
        }

    def write_artifact(
        rel_path: str,
        *,
        status: str,
        parent: str | None = None,
        plan: bool = False,
    ) -> None:
        path = tmp_path / rel_path
        path.parent.mkdir(parents=True, exist_ok=True)
        parent_field = f"- **Brief:** {parent}\n" if parent is not None else ""
        path.write_text(
            f"# Artifact\n\n- **Status:** {status}\n{parent_field}\n## Body\n",
            encoding="utf-8",
        )
        if plan:
            (path.parent / "plan.md").write_text("# Plan\n", encoding="utf-8")

    invalid_collection_cases = [
        (
            "work brief",
            {"work": {"queue": [entry("docs/product/briefs/wrong.md", kind="brief")]}},
            "docs/product/briefs/wrong.md",
            "Ready",
        ),
        (
            "brief spec",
            {"brief_queue": {"ready": [entry("docs/specs/wrong/spec.md", kind="spec")]}},
            "docs/specs/wrong/spec.md",
            "Approved",
        ),
        (
            "shaping spec",
            {"shaping_queue": {"active": [entry("docs/specs/shape/spec.md", kind="spec")]}},
            "docs/specs/shape/spec.md",
            "Implementing",
        ),
        (
            "backlog closed intent",
            {"backlog": {"closed": [entry("docs/product/intents/closed.md", kind="intent")]}},
            "docs/product/intents/closed.md",
            "Accepted",
        ),
    ]
    for _name, sections, path, status in invalid_collection_cases:
        if "backlog" in sections:
            workspace = sections
        else:
            workspace = {
                "ini-001": {
                    "status": "active",
                    "work": sections.get("work", {"queue": [], "active": [], "shipped": []}),
                    "shaping_queue": sections.get(
                        "shaping_queue", {"backlog": [], "active": []}
                    ),
                    "brief_queue": sections.get(
                        "brief_queue",
                        {"ready": [], "draft": [], "executing": [], "shipped": []},
                    ),
                }
            }
        write_artifact(path, status=status, plan=path.endswith("/spec.md"))
        result = mod.run_canonical_reconciliation(workspace, tmp_path)
        assert "impossible_transition" in {
            finding.code for finding in result.dispatch_by_path[path].findings
        }

    valid_backlog_open = {
        "backlog": {
            "open": [
                entry("docs/specs/open-draft/spec.md"),
                entry("docs/product/intents/open-draft.md", kind="intent"),
                entry("docs/product/research/open-draft.md", kind="research"),
                entry("docs/product/design/open-draft.md", kind="design"),
                entry("docs/product/briefs/open-draft.md", kind="brief"),
                entry("docs/product/defects/open.md", kind="defect"),
            ],
            "closed": [],
        }
    }
    for item in valid_backlog_open["backlog"]["open"]:
        status = "Open" if item["kind"] == "defect" else "Draft"
        write_artifact(item["path"], status=status, plan=item["path"].endswith("/spec.md"))
    open_result = mod.run_canonical_reconciliation(valid_backlog_open, tmp_path)
    assert all(
        "impossible_transition" not in {finding.code for finding in evaluation.findings}
        for evaluation in open_result.evaluations
    )

    def brief_workspace(
        collection: str,
        brief_status: str,
        child_collection: str | None,
        child_status: str | None,
    ) -> dict:
        work = {"queue": [], "active": [], "shipped": []}
        if child_collection is not None:
            work[child_collection].append(
                entry(
                    f"docs/specs/{collection}-{child_collection}-{child_status}/spec.md",
                    parent="docs/product/briefs/parent.md",
                )
            )
        return {
            "ini-001": {
                "status": "active",
                "work": work,
                "shaping_queue": {"backlog": [], "active": []},
                "brief_queue": {
                    "draft": [],
                    "ready": [],
                    "executing": [],
                    "shipped": [],
                    collection: [
                        entry(
                            "docs/product/briefs/parent.md",
                            kind="brief",
                            parent="docs/product/intents/parent.md",
                        )
                    ],
                },
            }
        }

    brief_cases = [
        ("ready", "Ready", None, None, False),
        ("ready", "Ready", "active", "Implementing", True),
        ("executing", "Executing", "active", "Implementing", False),
        ("executing", "Executing", None, None, True),
        ("shipped", "Shipped", "shipped", "Shipped", False),
        ("shipped", "Shipped", "queue", "Approved", True),
        ("shipped", "Shipped", "shipped", "Approved", True),
    ]
    for collection, brief_status, child_collection, child_status, expect_block in brief_cases:
        workspace = brief_workspace(collection, brief_status, child_collection, child_status)
        write_artifact(
            "docs/product/briefs/parent.md",
            status=brief_status,
            parent="docs/product/intents/parent.md",
        )
        if child_collection is not None and child_status is not None:
            child_path = workspace["ini-001"]["work"][child_collection][0]["path"]
            write_artifact(
                child_path,
                status=child_status,
                parent="docs/product/briefs/parent.md",
                plan=True,
            )
        result = mod.run_canonical_reconciliation(workspace, tmp_path)
        codes = {
            finding.code
            for finding in result.dispatch_by_path["docs/product/briefs/parent.md"].findings
        }
        assert ("impossible_transition" in codes) is expect_block


def test_t2_dependency_terminal_state_matrix(tmp_path: Path) -> None:
    mod = _load_engine()

    def source() -> dict:
        return {"mode": "repo-origin", "parent": "docs/product/briefs/parent.md"}

    def ready_entry(dep_kind: str, dep_path: str) -> dict:
        return {
            "path": "docs/specs/ready/spec.md",
            "kind": "spec",
            "source": source(),
            "summary": "Ready spec",
            "needs": [{"type": "local", "kind": dep_kind, "path": dep_path}],
        }

    def workspace(dep_kind: str, dep_path: str) -> dict:
        return {
            "ini-001": {
                "status": "active",
                "work": {"queue": [ready_entry(dep_kind, dep_path)], "active": [], "shipped": []},
                "shaping_queue": {"backlog": [], "active": []},
            }
        }

    def write_artifact(
        rel_path: str,
        *,
        status: str,
        parent: str | None = None,
        resolution: str | None = None,
        refresh_conflict: bool = False,
        plan: bool = False,
    ) -> None:
        path = tmp_path / rel_path
        path.parent.mkdir(parents=True, exist_ok=True)
        parent_field = f"- **Brief:** {parent}\n" if parent is not None else ""
        resolution_field = f"- **Resolution:** {resolution}\n" if resolution is not None else ""
        refresh_field = f"- **Refresh conflict:** {str(refresh_conflict).lower()}\n"
        path.write_text(
            "# Artifact\n\n"
            f"- **Status:** {status}\n"
            f"{parent_field}{resolution_field}{refresh_field}\n"
            "## Body\n",
            encoding="utf-8",
        )
        if plan:
            (path.parent / "plan.md").write_text("# Plan\n", encoding="utf-8")

    def evaluate(
        dep_kind: str,
        dep_path: str,
        *,
        status: str,
        resolution: str | None = None,
        parent: str | None = None,
        refresh_conflict: bool = False,
    ) -> set[str]:
        write_artifact(
            "docs/specs/ready/spec.md",
            status="Approved",
            parent="docs/product/briefs/parent.md",
            plan=True,
        )
        write_artifact(
            dep_path,
            status=status,
            resolution=resolution,
            parent=parent,
            refresh_conflict=refresh_conflict,
        )
        result = mod.run_canonical_reconciliation(workspace(dep_kind, dep_path), tmp_path)
        return {
            finding.code
            for finding in result.dispatch_by_path["docs/specs/ready/spec.md"].findings
        }

    matrix = [
        (
            "spec",
            "docs/specs/dep/spec.md",
            [("Shipped", None)],
            ["Approved", "Superseded", "Unknown"],
        ),
        (
            "brief",
            "docs/product/briefs/dep.md",
            [("Ready", None), ("Executing", None), ("Shipped", None)],
            ["Draft", "Superseded", "Unknown"],
        ),
        (
            "intent",
            "docs/product/intents/dep.md",
            [("Accepted", None), ("Fulfilled", None)],
            ["Draft", "Superseded", "Unknown"],
        ),
        (
            "research",
            "docs/product/research/dep.md",
            [("Complete", None)],
            ["Draft", "Superseded", "Unknown"],
        ),
        (
            "design",
            "docs/product/design/dep.md",
            [("Approved", None)],
            ["Draft", "Superseded", "Unknown"],
        ),
        (
            "defect",
            "docs/product/defects/dep.md",
            [],
            ["Open", "Closed", "Superseded", "Unknown"],
        ),
    ]
    for kind, path, satisfied_cases, unsatisfied_statuses in matrix:
        for status, resolution in satisfied_cases:
            assert "unsatisfied_dependency" not in evaluate(
                kind, path, status=status, resolution=resolution
            ), (kind, status, resolution)
        for status in unsatisfied_statuses:
            resolution = "duplicate" if kind == "defect" and status == "Closed" else None
            assert "unsatisfied_dependency" in evaluate(
                kind, path, status=status, resolution=resolution
            ), (kind, status, resolution)

    clean_terminal_codes = evaluate(
        "spec",
        "docs/specs/unregistered-terminal/spec.md",
        status="Shipped",
    )
    assert "unsatisfied_dependency" not in clean_terminal_codes

    spec_probe_parent_cases = [
        (
            "canonical brief",
            "docs/specs/probe-canonical/spec.md",
            "docs/product/briefs/parent.md",
            False,
        ),
        ("absent brief", "docs/specs/probe-absent/spec.md", None, False),
        ("brief none", "docs/specs/probe-none/spec.md", "none", False),
        (
            "nested brief",
            "docs/specs/probe-nested/spec.md",
            "docs/product/briefs/nested/parent.md",
            True,
        ),
    ]
    for name, dep_path, parent, invalid in spec_probe_parent_cases:
        codes = evaluate("spec", dep_path, status="Shipped", parent=parent)
        assert ("invalid_artifact_path" in codes) is invalid, name
        if not invalid:
            assert "unsatisfied_dependency" not in codes, name

    non_spec_parent_codes = evaluate(
        "design",
        "docs/product/design/probe-parent.md",
        status="Approved",
        parent="docs/product/intents/parent.md",
    )
    assert "invalid_artifact_path" not in non_spec_parent_codes
    assert "unsatisfied_dependency" not in non_spec_parent_codes

    malformed_target_dependency_workspace = workspace(
        "spec",
        "docs/specs/malformed-target-dep/spec.md",
    )
    malformed_target_dependency_workspace["ini-001"]["work"]["active"].append(
        {
            "path": "docs/specs/malformed-target-dep/spec.md",
            "kind": "spec",
            "source": {"mode": "repo-origin"},
            "summary": "Malformed dependency registration is missing needs.",
        }
    )
    write_artifact(
        "docs/specs/ready/spec.md",
        status="Approved",
        parent="docs/product/briefs/parent.md",
        plan=True,
    )
    write_artifact("docs/specs/malformed-target-dep/spec.md", status="Shipped")
    malformed_target_dependency_result = mod.run_canonical_reconciliation(
        malformed_target_dependency_workspace,
        tmp_path,
    )
    malformed_target_dependency_codes = {
        finding.code
        for finding in malformed_target_dependency_result.dispatch_by_path[
            "docs/specs/ready/spec.md"
        ].findings
    }
    assert "invalid_entry" in {
        finding.code for finding in malformed_target_dependency_result.findings
    }
    assert "unsatisfied_dependency" in malformed_target_dependency_codes

    nested_malformed_cases = [
        (
            "docs/specs/nested-parent-dep/spec.md",
            {
                "path": "docs/specs/nested-parent-dep/spec.md",
                "kind": "spec",
                "source": {
                    "mode": "repo-origin",
                    "parent": "../outside.md",
                },
                "summary": "Nested parent is invalid.",
                "needs": [],
            },
            "../outside.md",
        ),
        (
            "docs/specs/nested-need-dep/spec.md",
            {
                "path": "docs/specs/nested-need-dep/spec.md",
                "kind": "spec",
                "source": {"mode": "repo-origin"},
                "summary": "Nested dependency path is invalid.",
                "needs": [
                    {
                        "type": "local",
                        "kind": "spec",
                        "path": "../outside.md",
                    }
                ],
            },
            "../outside.md",
        ),
    ]
    for dep_path, malformed_entry, nested_bad_path in nested_malformed_cases:
        nested_malformed_workspace = workspace("spec", dep_path)
        nested_malformed_workspace["ini-001"]["work"]["active"].append(
            malformed_entry
        )
        write_artifact(
            "docs/specs/ready/spec.md",
            status="Approved",
            parent="docs/product/briefs/parent.md",
            plan=True,
        )
        write_artifact(dep_path, status="Shipped")
        nested_malformed_result = mod.run_canonical_reconciliation(
            nested_malformed_workspace,
            tmp_path,
        )
        nested_malformed_codes = {
            finding.code
            for finding in nested_malformed_result.dispatch_by_path[
                "docs/specs/ready/spec.md"
            ].findings
        }
        invalid_path_findings = [
            finding
            for finding in nested_malformed_result.findings
            if finding.code == "invalid_artifact_path"
        ]
        assert "unsatisfied_dependency" in nested_malformed_codes
        assert [finding.path for finding in invalid_path_findings] == [nested_bad_path]

    standalone_defect = evaluate(
        "defect",
        "docs/product/defects/standalone.md",
        status="Closed",
        resolution="fixed",
    )
    assert "unsatisfied_dependency" in standalone_defect

    bad_parent_codes = evaluate(
        "brief",
        "docs/product/briefs/bad-parent.md",
        status="Ready",
        parent="../outside.md",
    )
    assert "invalid_artifact_path" in bad_parent_codes

    refresh_conflict_codes = evaluate(
        "brief",
        "docs/product/briefs/refresh-conflict.md",
        status="Ready",
        refresh_conflict=True,
    )
    assert "refresh_conflict" in refresh_conflict_codes

    write_artifact(
        "docs/specs/ready/spec.md",
        status="Approved",
        parent="docs/product/briefs/parent.md",
        plan=True,
    )
    escaped_dep_target = tmp_path.parent / "escaped-dependency.md"
    escaped_dep_target.write_text("# Escaped\n\n- **Status:** Ready\n", encoding="utf-8")
    escaped_dep_path = tmp_path / "docs/product/briefs/escaped-dep.md"
    escaped_dep_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        escaped_dep_path.symlink_to(escaped_dep_target)
    except OSError:
        pytest.skip("symlink creation is unavailable in this environment")
    escaped_dep_result = mod.run_canonical_reconciliation(
        workspace("brief", "docs/product/briefs/escaped-dep.md"), tmp_path
    )
    assert "invalid_artifact_path" in {
        finding.code
        for finding in escaped_dep_result.dispatch_by_path[
            "docs/specs/ready/spec.md"
        ].findings
    }

    kind_mismatch_workspace = {
        "ini-001": {
            "status": "active",
            "work": {
                "queue": [
                    {
                        "path": "docs/specs/ready/spec.md",
                        "kind": "spec",
                        "source": source(),
                        "summary": "Ready spec",
                        "needs": [
                            {
                                "type": "local",
                                "kind": "research",
                                "path": "docs/product/design/registered.md",
                            }
                        ],
                    }
                ],
                "active": [],
                "shipped": [],
            },
            "shaping_queue": {
                "backlog": [
                    {
                        "path": "docs/product/design/registered.md",
                        "kind": "design",
                        "source": {"mode": "repo-origin"},
                        "summary": "Registered design",
                        "needs": [],
                    }
                ],
                "active": [],
            },
        }
    }
    write_artifact(
        "docs/specs/ready/spec.md",
        status="Approved",
        parent="docs/product/briefs/parent.md",
        plan=True,
    )
    write_artifact("docs/product/design/registered.md", status="Complete")
    kind_mismatch_result = mod.run_canonical_reconciliation(kind_mismatch_workspace, tmp_path)
    assert "unsatisfied_dependency" in {
        finding.code
        for finding in kind_mismatch_result.dispatch_by_path[
            "docs/specs/ready/spec.md"
        ].findings
    }

    defect_workspace = {
        "ini-001": {
            "status": "active",
            "work": {
                "queue": [
                    ready_entry("defect", "docs/product/defects/closed-member.md")
                ],
                "active": [],
                "shipped": [],
            },
            "shaping_queue": {"backlog": [], "active": []},
        },
        "backlog": {
            "open": [],
            "closed": [
                {
                    "path": "docs/product/defects/closed-member.md",
                    "kind": "defect",
                    "source": {
                        "mode": "repo-origin",
                        "ref": "example-service://defects/closed-member",
                    },
                    "summary": "Closed defect",
                    "needs": [],
                }
            ],
        },
    }
    write_artifact(
        "docs/specs/ready/spec.md",
        status="Approved",
        parent="docs/product/briefs/parent.md",
        plan=True,
    )
    write_artifact(
        "docs/product/defects/closed-member.md",
        status="Closed",
        resolution="fixed",
    )
    defect_member_result = mod.run_canonical_reconciliation(defect_workspace, tmp_path)
    defect_member_codes = {
        finding.code
        for finding in defect_member_result.dispatch_by_path[
            "docs/specs/ready/spec.md"
        ].findings
    }
    assert "unsatisfied_dependency" not in defect_member_codes


def test_t2_local_dependency_fails_when_target_has_findings(tmp_path: Path) -> None:
    mod = _load_engine()

    def entry(
        path: str,
        *,
        kind: str = "spec",
        parent: str | None = None,
        needs: list[dict] | None = None,
    ) -> dict:
        source = {"mode": "repo-origin"}
        if parent is not None:
            source["parent"] = parent
        return {
            "path": path,
            "kind": kind,
            "source": source,
            "summary": f"Summary for {path}",
            "needs": needs or [],
        }

    def write_spec(path: str, status: str, *, parent: str | None = None) -> None:
        spec_path = tmp_path / path
        spec_path.parent.mkdir(parents=True, exist_ok=True)
        parent_field = f"- **Brief:** {parent}\n" if parent is not None else ""
        spec_path.write_text(
            f"# Spec\n\n- **Status:** {status}\n{parent_field}\n## Body\n",
            encoding="utf-8",
        )
        (spec_path.parent / "plan.md").write_text("# Plan\n", encoding="utf-8")

    def workspace_for(dep_entry: dict, *, initiative_status: str = "active") -> dict:
        return {
            "ini-001": {
                "status": "active",
                "work": {
                    "queue": [
                        entry(
                            "docs/specs/ready/spec.md",
                            parent="docs/product/briefs/parent.md",
                            needs=[
                                {
                                    "type": "local",
                                    "kind": "spec",
                                    "path": dep_entry["path"],
                                }
                            ],
                        )
                    ],
                    "active": [],
                    "shipped": [],
                },
                "shaping_queue": {"backlog": [], "active": []},
            },
            "ini-002": {
                "status": initiative_status,
                "work": {"queue": [], "active": [dep_entry], "shipped": []},
                "shaping_queue": {"backlog": [], "active": []},
            },
        }

    write_spec(
        "docs/specs/ready/spec.md",
        "Approved",
        parent="docs/product/briefs/parent.md",
    )

    cases = [
        (
            "duplicate_membership",
            lambda dep: {
                **workspace_for(dep),
                "ini-003": {
                    "status": "active",
                    "work": {"queue": [], "active": [dep], "shipped": []},
                    "shaping_queue": {"backlog": [], "active": []},
                },
            },
        ),
        ("impossible_transition", lambda dep: workspace_for(dep)),
        ("provenance_mismatch", lambda dep: workspace_for(dep)),
        ("inactive_initiative", lambda dep: workspace_for(dep, initiative_status="paused")),
    ]
    for name, make_workspace in cases:
        dep = entry(
            f"docs/specs/{name}/spec.md",
            parent="docs/product/briefs/parent.md",
        )
        artifact_parent = (
            "docs/product/briefs/other.md"
            if name == "provenance_mismatch"
            else "docs/product/briefs/parent.md"
        )
        write_spec(dep["path"], "Shipped", parent=artifact_parent)
        result = mod.run_canonical_reconciliation(make_workspace(dep), tmp_path)
        ready_codes = {
            finding.code
            for finding in result.dispatch_by_path["docs/specs/ready/spec.md"].findings
        }
        dep_codes = {
            finding.code
            for finding in result.dispatch_by_path[dep["path"]].findings
        }
        assert name in dep_codes
        assert "unsatisfied_dependency" in ready_codes


def test_t2_coordination_receipt_block_contract(tmp_path: Path) -> None:
    mod = _load_engine()

    brief_path = "docs/product/briefs/remote-prereq.md"

    def source(parent: str | None = "docs/product/briefs/parent.md") -> dict:
        data = {"mode": "repo-origin"}
        if parent is not None:
            data["parent"] = parent
        return data

    def entry(path: str, *, kind: str = "spec", needs: list[dict] | None = None) -> dict:
        return {
            "path": path,
            "kind": kind,
            "source": source("docs/product/briefs/parent.md"),
            "summary": f"Summary for {path}",
            "needs": needs or [],
        }

    def cross_repo_need(**overrides: object) -> dict:
        need: dict[str, object] = {
            "type": "cross-repo",
            "kind": "brief",
            "path": brief_path,
            "containing_brief": brief_path,
            "receipt_id": "remote-prereq",
            "accepted_revision": "remote-rev-9",
        }
        need.update(overrides)
        return need

    def workspace(needs: list[dict] | None = None) -> dict:
        return {
            "ini-001": {
                "status": "active",
                "work": {
                    "queue": [entry("docs/specs/ready/spec.md", needs=needs)],
                    "active": [],
                    "shipped": [],
                },
                "shaping_queue": {"backlog": [], "active": []},
                "brief_queue": {
                    "ready": [
                        {
                            "path": "docs/product/briefs/local-only.md",
                            "kind": "brief",
                            "source": source("docs/product/intents/parent.md"),
                            "summary": "Local brief needs no receipt block.",
                            "needs": [],
                        }
                    ],
                    "draft": [],
                    "executing": [],
                    "shipped": [],
                },
            }
        }

    def write_artifact(rel_path: str, *, status: str, parent: str | None = None) -> None:
        path = tmp_path / rel_path
        path.parent.mkdir(parents=True, exist_ok=True)
        parent_field = f"- **Brief:** {parent}\n" if parent is not None else ""
        path.write_text(
            f"# Artifact\n\n- **Status:** {status}\n{parent_field}\n## Body\n",
            encoding="utf-8",
        )

    def write_spec() -> None:
        write_artifact(
            "docs/specs/ready/spec.md",
            status="Approved",
            parent="docs/product/briefs/parent.md",
        )
        (tmp_path / "docs/specs/ready/plan.md").write_text("# Plan\n", encoding="utf-8")

    def receipt_block(**overrides: object) -> str:
        receipt: dict[str, object] = {
            "id": '"remote-prereq"',
            "remote_kind": '"brief"',
            "remote_ref": '"example-service://projects/example-artifact"',
            "accepted_revision": '"remote-rev-9"',
            "required_status": '"Shipped"',
            "reported_status": '"Shipped"',
            "reviewed_by": '"Example Reviewer"',
            "reviewed_at": '"2026-08-10T00:00:00Z"',
            "refresh_conflict": "false",
        }
        for key, value in overrides.items():
            if value is None:
                receipt.pop(key)
            else:
                receipt[key] = value
        body = "\n".join(f"{key} = {value}" for key, value in receipt.items())
        return f"```toml coordination-receipts\n[[coordination_receipts]]\n{body}\n```"

    def write_brief(markdown: str) -> None:
        path = tmp_path / brief_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(markdown, encoding="utf-8")

    def valid_brief() -> str:
        return (
            "# Brief\n\n"
            "- **Status:** Ready\n\n"
            "Ignore this prose:\n"
            "```toml\n"
            "[[coordination_receipts]]\n"
            'id = "remote-prereq"\n'
            "```\n\n"
            f"{receipt_block()}\n"
        )

    def evaluate(needs: list[dict] | None, markdown: str | None) -> set[str]:
        write_spec()
        write_artifact(
            "docs/product/briefs/local-only.md",
            status="Ready",
            parent="docs/product/intents/parent.md",
        )
        if markdown is not None:
            write_brief(markdown)
        result = mod.run_canonical_reconciliation(workspace(needs), tmp_path)
        return {
            finding.code
            for finding in result.dispatch_by_path["docs/specs/ready/spec.md"].findings
        }

    assert "invalid_receipt" not in evaluate([cross_repo_need()], valid_brief())
    write_spec()
    write_artifact(
        "docs/product/briefs/local-only.md",
        status="Ready",
        parent="docs/product/intents/parent.md",
    )
    write_brief(valid_brief())
    duplicate_brief_workspace = workspace([cross_repo_need()])
    duplicate_brief_entry = {
        "path": brief_path,
        "kind": "brief",
        "source": source("docs/product/intents/parent.md"),
        "summary": "Duplicate receipt-containing brief.",
        "needs": [],
    }
    duplicate_brief_workspace["ini-001"]["brief_queue"]["ready"].append(
        duplicate_brief_entry
    )
    duplicate_brief_workspace["ini-001"]["brief_queue"]["shipped"].append(
        duplicate_brief_entry
    )
    duplicate_brief_result = mod.run_canonical_reconciliation(
        duplicate_brief_workspace, tmp_path
    )
    duplicate_ready_codes = {
        finding.code
        for finding in duplicate_brief_result.dispatch_by_path[
            "docs/specs/ready/spec.md"
        ].findings
    }
    assert "invalid_receipt" not in duplicate_ready_codes
    assert "unsatisfied_dependency" in duplicate_ready_codes
    assert "duplicate_membership" in {
        finding.code
        for finding in duplicate_brief_result.dispatch_by_path[brief_path].findings
    }
    local_only = mod.run_canonical_reconciliation(workspace(None), tmp_path)
    assert not local_only.dispatch_by_path["docs/product/briefs/local-only.md"].findings

    non_brief_result = mod.run_canonical_reconciliation(
        workspace(
            [
                cross_repo_need(
                    kind="spec",
                    path="docs/specs/not-a-brief/spec.md",
                    containing_brief="docs/specs/not-a-brief/spec.md",
                )
            ]
        ),
        tmp_path,
    )
    assert "invalid_artifact_path" in {finding.code for finding in non_brief_result.findings}

    invalid_cases: list[tuple[str, list[dict], str | None]] = [
        ("missing block", [cross_repo_need()], "# Brief\n\n- **Status:** Ready\n"),
        ("multiple blocks", [cross_repo_need()], f"{receipt_block()}\n\n{receipt_block()}"),
        ("malformed toml", [cross_repo_need()], "```toml coordination-receipts\n[[\n```"),
        (
            "top-level extra table",
            [cross_repo_need()],
            "```toml coordination-receipts\n"
            "extra = true\n"
            "[[coordination_receipts]]\n"
            "id = \"remote-prereq\"\n"
            "remote_kind = \"brief\"\n"
            "remote_ref = \"example-service://projects/example-artifact\"\n"
            "accepted_revision = \"remote-rev-9\"\n"
            "required_status = \"Shipped\"\n"
            "reported_status = \"Shipped\"\n"
            "reviewed_by = \"Example Reviewer\"\n"
            "reviewed_at = \"2026-08-10T00:00:00Z\"\n"
            "refresh_conflict = false\n"
            "```",
        ),
        ("path mismatch", [cross_repo_need(path="docs/product/briefs/other.md")], valid_brief()),
        (
            "containing brief mismatch",
            [cross_repo_need(containing_brief="docs/product/briefs/other.md")],
            valid_brief(),
        ),
        ("remote kind mismatch", [cross_repo_need()], receipt_block(remote_kind='"spec"')),
        ("id mismatch", [cross_repo_need()], receipt_block(id='"other"')),
        (
            "accepted revision mismatch",
            [cross_repo_need()],
            receipt_block(accepted_revision='"other-rev"'),
        ),
        ("required status mismatch", [cross_repo_need()], receipt_block(required_status='"Ready"')),
        ("reported status mismatch", [cross_repo_need()], receipt_block(reported_status='"Ready"')),
        ("missing reviewed_by", [cross_repo_need()], receipt_block(reviewed_by=None)),
        ("missing reviewed_at", [cross_repo_need()], receipt_block(reviewed_at=None)),
        (
            "naive reviewed_at",
            [cross_repo_need()],
            receipt_block(reviewed_at='"2026-08-10T00:00:00"'),
        ),
        (
            "space separator reviewed_at",
            [cross_repo_need()],
            receipt_block(reviewed_at='"2026-08-10 00:00:00+00:00"'),
        ),
        ("conflict true", [cross_repo_need()], receipt_block(refresh_conflict="true")),
        ("missing field", [cross_repo_need()], receipt_block(remote_ref=None)),
        (
            "extra field",
            [cross_repo_need()],
            receipt_block(extra_field='"extra"'),
        ),
        (
            "duplicate ids",
            [cross_repo_need()],
            "```toml coordination-receipts\n"
            "[[coordination_receipts]]\n"
            "id = \"remote-prereq\"\n"
            "remote_kind = \"spec\"\n"
            "remote_ref = \"example-service://projects/example-one\"\n"
            "accepted_revision = \"remote-rev-1\"\n"
            "required_status = \"Shipped\"\n"
            "reported_status = \"Shipped\"\n"
            "reviewed_by = \"Example Reviewer\"\n"
            "reviewed_at = \"2026-08-10T00:00:00Z\"\n"
            "refresh_conflict = false\n"
            "[[coordination_receipts]]\n"
            "id = \"remote-prereq\"\n"
            "remote_kind = \"brief\"\n"
            "remote_ref = \"example-service://projects/example-artifact\"\n"
            "accepted_revision = \"remote-rev-9\"\n"
            "required_status = \"Shipped\"\n"
            "reported_status = \"Shipped\"\n"
            "reviewed_by = \"Example Reviewer\"\n"
            "reviewed_at = \"2026-08-10T00:00:00Z\"\n"
            "refresh_conflict = false\n"
            "```",
        ),
        (
            "prose injection inert",
            [cross_repo_need(accepted_revision="wrong-rev")],
            valid_brief() + "\naccepted_revision = \"wrong-rev\"\n",
        ),
        (
            "other fence inert",
            [cross_repo_need(accepted_revision="wrong-rev")],
            valid_brief()
            + "\n```toml\n[[coordination_receipts]]\naccepted_revision = \"wrong-rev\"\n```",
        ),
    ]
    for name, needs, markdown in invalid_cases:
        assert "invalid_receipt" in evaluate(needs, markdown), name

    write_spec()
    write_artifact(
        "docs/product/briefs/local-only.md",
        status="Ready",
        parent="docs/product/intents/parent.md",
    )
    receipt_path = tmp_path / brief_path
    if receipt_path.exists() or receipt_path.is_symlink():
        receipt_path.unlink()
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    escaped_receipt = tmp_path.parent / "escaped-receipt.md"
    escaped_receipt.write_text(valid_brief(), encoding="utf-8")
    try:
        receipt_path.symlink_to(escaped_receipt)
    except OSError:
        pytest.skip("symlink creation is unavailable in this environment")
    escaped_result = mod.run_canonical_reconciliation(workspace([cross_repo_need()]), tmp_path)
    escaped_codes = {
        finding.code
        for finding in escaped_result.dispatch_by_path["docs/specs/ready/spec.md"].findings
    }
    assert "invalid_artifact_path" in escaped_codes


def _make_ini(
    slug: str = "ini-001",
    shaping_active_slugs: list[str] | None = None,
    shaping_backlog: list[tuple[str, str]] | None = None,  # (slug, type)
) -> object:
    """Build a minimal Initiative-like object for is_need_satisfied testing."""
    _load_engine()  # ensure module is registered in sys.modules

    def _entry(s, t):
        e = SimpleNamespace()
        e.slug = s
        e.entry_type = t
        return e

    active = [_entry(s, "shape") for s in (shaping_active_slugs or [])]
    backlog = [_entry(s, t) for s, t in (shaping_backlog or [])]

    shaping = SimpleNamespace(active=active, backlog=backlog)
    work = SimpleNamespace(active=[], shipped=[], queue=[])
    return SimpleNamespace(slug=slug, shaping=shaping, work=work, brief_queue=None)


class TestShapeNeedAutonomous:
    """Shape: need — absent from active AND backlog → unsatisfied when autonomous."""

    def test_shape_absent_unsatisfied_autonomous(self) -> None:
        pytest.skip(
            "STUB: a need absent from both active and backlog is "
            "unsatisfied in autonomous mode"
        )

    def test_shape_in_active_unsatisfied_both_modes(self) -> None:
        mod = _load_engine()
        ini = _make_ini(slug="ini-001", shaping_active_slugs=["my-shape"])
        # In human mode: slug in active → NOT satisfied (slug not in active_slugs = False)
        assert not mod.is_need_satisfied("shape:my-shape", "ini-001", [ini], False)
        # In autonomous mode: same result
        assert not mod.is_need_satisfied("shape:my-shape", "ini-001", [ini], True)

    def test_shape_in_backlog_not_active_satisfied_autonomous(self) -> None:
        mod = _load_engine()
        ini = _make_ini(
            slug="ini-001",
            shaping_active_slugs=[],
            shaping_backlog=[("my-shape", "shape")],
        )
        # Autonomous: in backlog (planned but not started) → satisfied (intentional asymmetry)
        assert mod.is_need_satisfied("shape:my-shape", "ini-001", [ini], True)
        # Human mode: not in active → satisfied
        assert mod.is_need_satisfied("shape:my-shape", "ini-001", [ini], False)

    def test_shape_absent_satisfied_human_mode(self) -> None:
        mod = _load_engine()
        ini = _make_ini(slug="ini-001", shaping_active_slugs=[], shaping_backlog=[])
        # Human mode: absent from active → satisfied (graduated or never existed)
        assert mod.is_need_satisfied("shape:my-shape", "ini-001", [ini], False)

    def test_shape_absent_unsatisfied_autonomous_mode(self) -> None:
        mod = _load_engine()
        ini = _make_ini(slug="ini-001", shaping_active_slugs=[], shaping_backlog=[])
        # Autonomous mode: absent from both → unsatisfied (never planned)
        assert not mod.is_need_satisfied("shape:my-shape", "ini-001", [ini], True)


class TestResearchNeedAutonomous:
    """Research: need — absence from backlog means satisfied in both human and autonomous mode.

    Absent = satisfied because completed research is removed from the backlog;
    there is no way to distinguish "completed" from "never planned" from backlog state alone.
    """

    def test_research_in_backlog_unsatisfied_both_modes(self) -> None:
        mod = _load_engine()
        ini = _make_ini(
            slug="ini-001",
            shaping_backlog=[("my-research", "research")],
        )
        # Both modes: in backlog as type "research" → NOT satisfied (still pending)
        assert not mod.is_need_satisfied("research:my-research", "ini-001", [ini], False)
        assert not mod.is_need_satisfied("research:my-research", "ini-001", [ini], True)

    def test_research_absent_satisfied_both_modes(self) -> None:
        mod = _load_engine()
        ini = _make_ini(slug="ini-001", shaping_backlog=[])
        # Both modes: not in backlog → satisfied (completed or never needed).
        # autonomous_dispatch does NOT change research semantics — absent means completed.
        assert mod.is_need_satisfied("research:my-research", "ini-001", [ini], False)
        assert mod.is_need_satisfied("research:my-research", "ini-001", [ini], True)

    def test_research_wrong_type_in_backlog_does_not_block(self) -> None:
        mod = _load_engine()
        ini = _make_ini(
            slug="ini-001",
            shaping_backlog=[("my-research", "shape")],  # same slug, but type=shape not research
        )
        # Both modes: entry exists but type != "research" → NOT in research_slugs → satisfied
        assert mod.is_need_satisfied("research:my-research", "ini-001", [ini], False)
        assert mod.is_need_satisfied("research:my-research", "ini-001", [ini], True)
