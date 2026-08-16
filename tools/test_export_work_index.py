"""Red construction tests for the m6 Astro work-index exporter."""

from __future__ import annotations

import copy
import json
import subprocess
import sys
import time
from pathlib import Path

import pytest

# STUB: AC1, AC2, AC3, AC4 — production module is absent until T1.
from tools import export_work_index as exporter  # type: ignore[attr-defined]


def _status_payload(path: str = "docs/specs/example/spec.md") -> dict:
    ready = {
        "path": path,
        "slug": Path(path).parent.name,
        "kind": "spec",
        "ini_slug": "ini-002",
        "collection": "work.queue",
        "dispatchable": True,
        "findings": [],
    }
    attention = {
        "path": "docs/specs/attention/spec.md",
        "slug": "attention",
        "kind": "spec",
        "ini_slug": "ini-002",
        "collection": "work.queue",
        "dispatchable": False,
        "findings": [{
            "code": "unsatisfied_dependency",
            "path": "docs/specs/attention/spec.md",
            "dispatchable": False,
            "next_action": "Complete the declared predecessor.",
        }],
    }
    active = {
        "path": "docs/specs/active/spec.md",
        "slug": "active",
        "kind": "spec",
        "ini_slug": "ini-002",
        "collection": "work.active",
        "dispatchable": False,
        "findings": [],
    }
    legacy_shipped = {
        "path": "spec/legacy-shipped",
        "slug": "legacy-shipped",
        "kind": "spec",
        "ini_slug": "ini-002",
        "collection": "work.shipped",
        "dispatchable": False,
        "findings": [{
            "code": "legacy_entry",
            "path": "spec/legacy-shipped",
            "dispatchable": False,
            "next_action": "Run repair-plan, review it, then run repair-apply.",
        }],
    }
    return {
        "schema_version": 1,
        "initiatives": [{
            "slug": "ini-002",
            "name": "workspace.toml",
            "status": "active",
            "milestone": "workspace.toml",
            "brief_queue": {
                "executing": "",
                "ready": ["docs/product/briefs/adoption-wave.md"],
                "draft": [],
            },
            "queue_empty": False,
        }],
        "work": {
            "ready": [ready],
            "active": [active],
            "blocked": [attention, legacy_shipped],
            "shipped": [legacy_shipped],
        },
        "shaping": {
            "ready": [{
                "slug": "adoption-surface",
                "entry_type": "shape",
                "needs": [],
                "ini_slug": "ini-002",
                "blocking_needs": [],
            }],
            "signals": [],
            "blocked": [],
            "active_entries": [],
            "top_level_backlog": [],
        },
        "repo_backlog": {
            "open": [{
                "room": "repo",
                "slug": "follow-up",
                "summary": "Investigate follow-up",
                "needs": [],
            }],
        },
        "canonical": {
            "findings": [*attention["findings"], *legacy_shipped["findings"]],
            "evaluations": [ready, active, attention],
            "legacy_memberships": [legacy_shipped],
            "ready": [ready],
            "active": [active],
            "blocked": [attention, legacy_shipped],
        },
    }


def _workspace_payload(path: str = "docs/specs/example/spec.md") -> dict:
    return {
        "ini-002": {
            "name": "Adoption",
            "milestone": "P5",
            "work": {
                "queue": [
                    {
                        "path": path,
                        "kind": "spec",
                        "source": {"mode": "repo-origin"},
                        "summary": "Show canonical work",
                        "needs": [],
                    },
                    {
                        "path": "docs/specs/attention/spec.md",
                        "kind": "spec",
                        "source": {"mode": "repo-origin"},
                        "summary": "Resolve blocked work",
                        "needs": [],
                    },
                ],
                "active": [{
                    "path": "docs/specs/active/spec.md",
                    "kind": "spec",
                    "source": {"mode": "repo-origin"},
                    "summary": "Continue active work",
                    "needs": [],
                }],
                "shipped": ["spec/legacy-shipped"],
            },
        }
    }


def _missing_artifact_payload() -> tuple[dict, dict]:
    path = "docs/specs/future/spec.md"
    status = _status_payload()
    missing = copy.deepcopy(status["canonical"]["blocked"][0])
    missing.update(path=path, slug="future")
    missing["findings"] = [{
        "code": "missing_artifact",
        "path": path,
        "dispatchable": False,
        "next_action": "Create and review the canonical artifact before dispatch.",
    }]
    status["initiatives"][0]["brief_queue"] = {
        "executing": "",
        "ready": [],
        "draft": [],
    }
    status["canonical"].update(
        findings=missing["findings"],
        evaluations=[missing],
        legacy_memberships=[],
        ready=[],
        active=[],
        blocked=[missing],
    )
    workspace = _workspace_payload(path)
    workspace["ini-002"]["work"]["queue"] = [
        workspace["ini-002"]["work"]["queue"][0]
    ]
    workspace["ini-002"]["work"]["active"] = []
    return status, workspace


def _workspace_toml(*, summaries: tuple[str, str], reversed_queue: bool, note: str) -> str:
    entries = [
        f'''{{path = "docs/specs/example/spec.md", kind = "spec", source = {{mode = "repo-origin"}}, summary = "{summaries[0]}", needs = []}}''',
        f'''{{path = "docs/specs/attention/spec.md", kind = "spec", source = {{mode = "repo-origin"}}, summary = "{summaries[1]}", needs = []}}''',
    ]
    if reversed_queue:
        entries.reverse()
    queue = ",\n  ".join(entries)
    return f'''\
["ini-002"]
name = "Adoption"
status = "active"
milestone = "P5"

["ini-002".work]
# {note}
queue = [
  {queue},
]
active = [
  {{path = "docs/specs/active/spec.md", kind = "spec", source = {{mode = "repo-origin"}}, summary = "Continue active work", needs = []}},
]
shipped = ["spec/legacy-shipped"]
'''


def _fake_repo(root: Path) -> Path:
    script = root / "packs/core/.apm/skills/workspace-status/scripts/workspace_status.py"
    script.parent.mkdir(parents=True)
    script.write_text("# fixture\n", encoding="utf-8")
    (root / "workspace.toml").write_text("# fixture\n", encoding="utf-8")
    return root


def _completed(payload: dict, *, stderr: bytes = b"") -> subprocess.CompletedProcess:
    return subprocess.CompletedProcess(
        args=["workspace-status"],
        returncode=0,
        stdout=json.dumps(payload, allow_nan=True).encode(),
        stderr=stderr,
    )


def _assert_confined_error(
    caught: pytest.ExceptionInfo,
    *,
    repo: Path | None = None,
    private_text: str = "private repository prose",
) -> None:
    message = str(caught.value)
    assert private_text not in message
    assert "Traceback" not in message
    if repo is not None:
        assert str(repo) not in message


def test_projection_preserves_canonical_status_and_joins_display_text() -> None:
    projection = exporter.build_projection(_status_payload(), _workspace_payload())

    item = projection["initiatives"][0]["ready"][0]
    assert item["dispatchable"] is True
    assert "next_action" not in item
    assert item["summary"] == "Show canonical work"
    assert projection["initiatives"][0]["name"] == "Adoption"
    assert projection["initiatives"][0]["milestone"] == "P5"
    finding = projection["initiatives"][0]["attention"][0]["findings"][0]
    assert finding["next_action"] == "Complete the declared predecessor."
    assert [item["path"] for item in projection["initiatives"][0]["attention"]] == [
        "docs/specs/attention/spec.md"
    ]
    assert projection["counts"] == {
        "active": 1,
        "ready": 1,
        "attention": 1,
        "briefs": 1,
        "shaping": 1,
        "backlog": 1,
    }
    assert projection["initiatives"][0]["active"][0]["summary"] == (
        "Continue active work"
    )
    assert "next_action" not in projection["initiatives"][0]["active"][0]
    assert projection["briefs"][0]["path"] == "docs/product/briefs/adoption-wave.md"
    assert projection["shaping"][0]["slug"] == "adoption-surface"
    assert projection["backlog"][0]["summary"] == "Investigate follow-up"


def test_display_changes_cannot_change_canonical_work_fields() -> None:
    status = _status_payload()
    base_workspace = exporter.parse_workspace_display(
        _workspace_toml(
            summaries=("Show canonical work", "Resolve blocked work"),
            reversed_queue=False,
            note="first comment",
        )
    )
    variant_status = copy.deepcopy(status)
    variant_status["work"]["blocked"].reverse()
    variant_workspace = exporter.parse_workspace_display(
        _workspace_toml(
            summaries=("Changed ready label", "Changed attention label"),
            reversed_queue=True,
            note="different comment and order",
        )
    )

    base = exporter.build_projection(status, base_workspace)
    variant = exporter.build_projection(variant_status, variant_workspace)

    def canonical_fields(projection: dict) -> list[tuple]:
        fields = []
        for initiative in projection["initiatives"]:
            for bucket in ("ready", "active", "attention"):
                for item in initiative[bucket]:
                    findings = tuple(
                        (finding["code"], finding["next_action"])
                        for finding in item["findings"]
                    )
                    fields.append(
                        (
                            bucket,
                            item["path"],
                            item["dispatchable"],
                            findings,
                        )
                    )
        return fields

    assert canonical_fields(base) == canonical_fields(variant)
    assert base["initiatives"][0]["ready"][0]["summary"] != (
        variant["initiatives"][0]["ready"][0]["summary"]
    )


def test_projection_sorts_same_bucket_by_canonical_path() -> None:
    status = _status_payload()
    second = copy.deepcopy(status["work"]["ready"][0])
    second.update(path="docs/specs/alpha/spec.md", slug="alpha")
    status["work"]["ready"].append(second)
    status["canonical"]["evaluations"].append(second)
    status["canonical"]["ready"].append(second)
    workspace = _workspace_payload()
    workspace["ini-002"]["work"]["queue"].append({
        "path": "docs/specs/alpha/spec.md",
        "kind": "spec",
        "source": {"mode": "repo-origin"},
        "summary": "Alpha ready work",
        "needs": [],
    })

    projection = exporter.build_projection(status, workspace)

    assert [
        item["path"] for item in projection["initiatives"][0]["ready"]
    ] == [
        "docs/specs/alpha/spec.md",
        "docs/specs/example/spec.md",
    ]


@pytest.mark.parametrize("path", ["/outside/repository", "../outside", "C:/outside"])
def test_projection_rejects_non_repository_relative_identity(path: str) -> None:
    with pytest.raises(exporter.ProjectionError):
        exporter.build_projection(_status_payload(path), _workspace_payload(path))


def test_projection_rejects_unsupported_schema() -> None:
    status = _status_payload()
    status["schema_version"] = 2

    with pytest.raises(exporter.ProjectionError):
        exporter.build_projection(status, _workspace_payload())


@pytest.mark.parametrize(
    "malformed",
    [
        None,
        {},
        {"collection": 1},
        {"collection": "work.queue", "findings": "bad"},
        {"collection": "work.queue", "findings": []},
    ],
)
def test_projection_rejects_malformed_blocked_items(malformed: object) -> None:
    status = _status_payload()
    status["canonical"]["blocked"].append(malformed)

    with pytest.raises(exporter.ProjectionError):
        exporter.build_projection(status, _workspace_payload())


def test_projection_errors_expose_only_stable_bounded_codes() -> None:
    known = exporter.ProjectionError("canonical blocked work item is malformed")
    unknown = exporter.ProjectionError("private repository prose")

    assert known.code == "canonical-blocked-work-item-is-malformed"
    assert unknown.code == "unexpected-projection-error"


def test_projection_rejects_ambiguous_display_join_without_prose_leak() -> None:
    workspace = _workspace_payload()
    duplicate = copy.deepcopy(workspace["ini-002"]["work"]["queue"][0])
    duplicate["summary"] = "private repository prose"
    workspace["ini-002"]["work"]["queue"].append(duplicate)

    with pytest.raises(exporter.ProjectionError) as caught:
        exporter.build_projection(_status_payload(), workspace)

    _assert_confined_error(caught)


def test_workspace_status_argv_is_fixed_and_shell_free(tmp_path: Path) -> None:
    repo = _fake_repo(tmp_path)
    argv = exporter.workspace_status_argv(repo)

    assert argv == [
        sys.executable,
        str(repo / "packs/core/.apm/skills/workspace-status/scripts/workspace_status.py"),
        "status",
        "--root",
        str(repo),
    ]


def test_repository_root_is_derived_from_exporter_not_cwd(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    expected = Path(exporter.__file__).resolve().parents[1]
    monkeypatch.chdir(tmp_path)

    repo = exporter.repository_root()

    assert repo == expected
    assert exporter.workspace_status_argv(repo) == [
        sys.executable,
        str(expected / "packs/core/.apm/skills/workspace-status/scripts/workspace_status.py"),
        "status",
        "--root",
        str(expected),
    ]


def test_workspace_status_run_uses_exact_bounded_subprocess_contract(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo = _fake_repo(tmp_path)
    calls: list[list[str]] = []

    def capture(argv: list[str]) -> subprocess.CompletedProcess:
        calls.append(argv)
        return _completed(_status_payload())

    monkeypatch.setattr(exporter, "_run_bounded_status", capture)

    result = exporter.run_workspace_status(repo)

    assert result["schema_version"] == 1
    assert calls == [exporter.workspace_status_argv(repo)]


def test_bounded_status_runner_stops_while_stdout_is_streaming(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(exporter, "MAX_STDOUT_BYTES", 64)
    argv = [
        sys.executable,
        "-c",
        "import sys; sys.stdout.buffer.write(b'x' * 1048576)",
    ]

    with pytest.raises(exporter.ProjectionError) as caught:
        exporter._run_bounded_status(argv)

    assert "byte limit" in str(caught.value)


def test_bounded_status_runner_kills_on_timeout(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(exporter, "STATUS_TIMEOUT_SECONDS", 0.01)
    argv = [sys.executable, "-c", "import time; time.sleep(2)"]

    with pytest.raises(exporter.ProjectionError) as caught:
        exporter._run_bounded_status(argv)

    assert "did not complete" in str(caught.value)


def test_bounded_status_runner_cannot_hang_on_inherited_pipe(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(exporter, "READER_JOIN_SECONDS", 0.05)
    argv = [
        sys.executable,
        "-c",
        (
            "import subprocess, sys; "
            "subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(2)'])"
        ),
    ]
    started = time.monotonic()

    with pytest.raises(exporter.ProjectionError) as caught:
        exporter._run_bounded_status(argv)

    assert time.monotonic() - started < 1
    assert "did not complete" in str(caught.value)


def test_workspace_status_nonzero_exit_is_confined(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo = _fake_repo(tmp_path)
    private_text = f"Traceback: {repo}/private repository prose"
    result = subprocess.CompletedProcess(
        args=["workspace-status"],
        returncode=2,
        stdout=b"",
        stderr=private_text.encode(),
    )
    monkeypatch.setattr(exporter, "_run_bounded_status", lambda _argv: result)

    with pytest.raises(exporter.ProjectionError) as caught:
        exporter.run_workspace_status(repo)

    _assert_confined_error(caught, repo=repo)


@pytest.mark.parametrize("raw_json", [b"not-json", b'{"schema_version": 1'])
def test_workspace_status_invalid_or_truncated_json_is_confined(
    raw_json: bytes,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo = _fake_repo(tmp_path)
    result = subprocess.CompletedProcess(
        args=["workspace-status"],
        returncode=0,
        stdout=raw_json,
        stderr=b"private repository prose",
    )
    monkeypatch.setattr(exporter, "_run_bounded_status", lambda _argv: result)

    with pytest.raises(exporter.ProjectionError) as caught:
        exporter.run_workspace_status(repo)

    _assert_confined_error(caught, repo=repo)


def test_workspace_status_missing_collection_is_confined(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo = _fake_repo(tmp_path)
    payload = _status_payload()
    payload.pop("work")
    payload["private"] = "private repository prose"
    monkeypatch.setattr(exporter, "_run_bounded_status", lambda _argv: _completed(payload))

    with pytest.raises(exporter.ProjectionError) as caught:
        exporter.run_workspace_status(repo)

    _assert_confined_error(caught, repo=repo)


def test_workspace_status_timeout_is_single_attempt_and_confined(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo = _fake_repo(tmp_path)
    attempts = 0

    def time_out(_argv: list[str]) -> subprocess.CompletedProcess:
        nonlocal attempts
        attempts += 1
        raise exporter.ProjectionError("workspace-status did not complete successfully")

    monkeypatch.setattr(exporter, "_run_bounded_status", time_out)

    with pytest.raises(exporter.ProjectionError) as caught:
        exporter.run_workspace_status(repo)

    assert attempts == 1
    assert str(repo) not in str(caught.value)


def test_workspace_status_rejects_non_finite_json(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo = _fake_repo(tmp_path)
    payload = _status_payload()
    payload["unsafe_number"] = float("nan")
    monkeypatch.setattr(exporter, "_run_bounded_status", lambda _argv: _completed(payload))

    with pytest.raises(exporter.ProjectionError):
        exporter.run_workspace_status(repo)


def test_workspace_status_rejects_oversized_json(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo = _fake_repo(tmp_path)
    monkeypatch.setattr(exporter, "MAX_JSON_BYTES", 32)
    monkeypatch.setattr(
        exporter, "_run_bounded_status", lambda _argv: _completed(_status_payload())
    )

    with pytest.raises(exporter.ProjectionError):
        exporter.run_workspace_status(repo)


def test_workspace_status_rejects_json_depth_overflow(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo = _fake_repo(tmp_path)
    payload = _status_payload()
    payload["too_deep"] = {"a": {"b": {"c": True}}}
    monkeypatch.setattr(exporter, "MAX_JSON_DEPTH", 3)
    monkeypatch.setattr(exporter, "_run_bounded_status", lambda _argv: _completed(payload))

    with pytest.raises(exporter.ProjectionError):
        exporter.run_workspace_status(repo)


def test_workspace_status_rejects_item_overflow(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo = _fake_repo(tmp_path)
    payload = _status_payload()
    payload["work"]["ready"] *= 2
    monkeypatch.setattr(exporter, "MAX_STATUS_ITEMS", 1)
    monkeypatch.setattr(exporter, "_run_bounded_status", lambda _argv: _completed(payload))

    with pytest.raises(exporter.ProjectionError):
        exporter.run_workspace_status(repo)


def test_workspace_display_is_rejected_before_oversized_toml_is_parsed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo = _fake_repo(tmp_path)
    monkeypatch.setattr(exporter, "MAX_WORKSPACE_BYTES", 32)
    (repo / "workspace.toml").write_bytes(b"private repository prose" * 4)

    with pytest.raises(exporter.ProjectionError) as caught:
        exporter.load_workspace_display(repo)

    assert "byte limit" in str(caught.value)
    assert "private repository prose" not in str(caught.value)


@pytest.mark.parametrize("collection", ["briefs", "backlog"])
@pytest.mark.parametrize("failure", ["missing", "symlink"])
def test_context_targets_must_resolve_inside_repository(
    collection: str,
    failure: str,
    tmp_path: Path,
) -> None:
    repo = _fake_repo(tmp_path / "repo")
    target = repo / "docs/product/briefs/context.md"
    target.parent.mkdir(parents=True)
    if failure == "symlink":
        outside = tmp_path / "outside.md"
        outside.write_text("outside\n", encoding="utf-8")
        target.symlink_to(outside)
    projection = {
        "initiatives": [],
        "briefs": ([{"path": target.relative_to(repo).as_posix()}] if collection == "briefs" else []),
        "backlog": ([{"path": target.relative_to(repo).as_posix()}] if collection == "backlog" else []),
    }

    with pytest.raises(exporter.ProjectionError):
        exporter._validate_projection_targets(projection, repo)


def test_missing_artifact_attention_target_may_be_absent(tmp_path: Path) -> None:
    repo = _fake_repo(tmp_path / "repo")
    projection = {
        "initiatives": [{
            "active": [],
            "ready": [],
            "attention": [{
                "path": "docs/specs/future/spec.md",
                "findings": [{"code": "missing_artifact"}],
            }],
        }],
        "briefs": [],
        "backlog": [],
    }

    exporter._validate_projection_targets(projection, repo)


def test_export_accepts_canonical_missing_artifact_attention_leaf(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo = _fake_repo(tmp_path / "repo")
    status, workspace = _missing_artifact_payload()
    monkeypatch.setattr(exporter, "run_workspace_status", lambda _repo: status)
    monkeypatch.setattr(exporter, "load_workspace_display", lambda _repo: workspace)

    projection = exporter.export_work_index(repo)

    assert projection["initiatives"][0]["attention"][0]["path"] == (
        "docs/specs/future/spec.md"
    )


def test_missing_artifact_attention_rejects_escaping_parent_symlink(
    tmp_path: Path,
) -> None:
    repo = _fake_repo(tmp_path / "repo")
    outside = tmp_path / "outside"
    outside.mkdir()
    (repo / "docs").symlink_to(outside, target_is_directory=True)
    projection = {
        "initiatives": [{
            "active": [],
            "ready": [],
            "attention": [{
                "path": "docs/specs/future/spec.md",
                "findings": [{"code": "missing_artifact"}],
            }],
        }],
        "briefs": [],
        "backlog": [],
    }

    with pytest.raises(exporter.ProjectionError):
        exporter._validate_projection_targets(projection, repo)


def test_main_confines_missing_artifact_parent_symlink_diagnostic(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    repo = _fake_repo(tmp_path / "repo")
    outside = tmp_path / "outside"
    outside.mkdir()
    (repo / "docs").symlink_to(outside, target_is_directory=True)
    status, workspace = _missing_artifact_payload()
    monkeypatch.setattr(exporter, "repository_root", lambda: repo)
    monkeypatch.setattr(exporter, "run_workspace_status", lambda _repo: status)
    monkeypatch.setattr(exporter, "load_workspace_display", lambda _repo: workspace)

    assert exporter.main() == 1
    assert capsys.readouterr().err == (
        "work-index export failed: "
        "required-repository-path-is-unavailable-or-unsafe\n"
    )


@pytest.mark.parametrize("bucket", ["active", "ready"])
def test_missing_artifact_must_be_an_absent_attention_leaf(
    bucket: str,
    tmp_path: Path,
) -> None:
    repo = _fake_repo(tmp_path / "repo")
    item = {
        "path": "docs/specs/future/spec.md",
        "findings": [{"code": "missing_artifact"}],
    }
    projection = {
        "initiatives": [{
            "active": [item] if bucket == "active" else [],
            "ready": [item] if bucket == "ready" else [],
            "attention": [],
        }],
        "briefs": [],
        "backlog": [],
    }

    with pytest.raises(exporter.ProjectionError):
        exporter._validate_projection_targets(projection, repo)


def test_missing_artifact_attention_rejects_status_drift(tmp_path: Path) -> None:
    repo = _fake_repo(tmp_path / "repo")
    target = repo / "docs/specs/future/spec.md"
    target.parent.mkdir(parents=True)
    target.write_text("# Materialized\n", encoding="utf-8")
    projection = {
        "initiatives": [{
            "active": [],
            "ready": [],
            "attention": [{
                "path": target.relative_to(repo).as_posix(),
                "findings": [{"code": "missing_artifact"}],
            }],
        }],
        "briefs": [],
        "backlog": [],
    }

    with pytest.raises(exporter.ProjectionError):
        exporter._validate_projection_targets(projection, repo)


@pytest.mark.parametrize("target_name", ["workspace.toml", "workspace_status.py"])
def test_workspace_status_rejects_symlink_escape(
    target_name: str,
    tmp_path: Path,
) -> None:
    repo = _fake_repo(tmp_path / "repo")
    outside = tmp_path / "outside"
    outside.mkdir()
    escaped = outside / target_name
    escaped.write_text("# outside\n", encoding="utf-8")
    target = (
        repo / "workspace.toml"
        if target_name == "workspace.toml"
        else repo / "packs/core/.apm/skills/workspace-status/scripts/workspace_status.py"
    )
    target.unlink()
    target.symlink_to(escaped)

    with pytest.raises(exporter.ProjectionError):
        exporter.workspace_status_argv(repo)


def test_workspace_status_rejects_symlink_loop(tmp_path: Path) -> None:
    repo = _fake_repo(tmp_path)
    script = repo / "packs/core/.apm/skills/workspace-status/scripts/workspace_status.py"
    script.unlink()
    script.symlink_to(script)

    with pytest.raises(exporter.ProjectionError):
        exporter.workspace_status_argv(repo)
