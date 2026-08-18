"""Construction tests for GitHub refresh and coordination write-back."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
import types
from datetime import UTC, datetime
from pathlib import Path
from typing import cast

import pytest

PACK_ROOT = Path(__file__).resolve().parents[3]
GITHUB_REFRESH_SCRIPT = (
    PACK_ROOT / ".apm" / "skills" / "github-refresh" / "scripts" / "processor.py"
)
REFRESH_SCRIPT = (
    PACK_ROOT.parent
    / "core"
    / ".apm"
    / "skills"
    / "work-intake"
    / "scripts"
    / "refresh.py"
)
SKILL_ROOT = PACK_ROOT / ".apm" / "skills" / "github-refresh"


def _unreached_acquire(_locator: str, _revision: str) -> dict[str, object]:
    raise AssertionError("acquisition should not run in this test")


@pytest.fixture(scope="module")
def github_mod() -> types.ModuleType:
    spec = importlib.util.spec_from_file_location("github_refresh_processor", GITHUB_REFRESH_SCRIPT)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def refresh_mod() -> types.ModuleType:
    spec = importlib.util.spec_from_file_location("work_intake_refresh", REFRESH_SCRIPT)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def _policy(refresh_mod: types.ModuleType):
    return refresh_mod.RefreshAuthorizationPolicy(
        draft_approver_roles=("product",),
        accepted_approver_roles=("product",),
        remote_mutation_approver_roles=("product",),
    )


def _approver(refresh_mod: types.ModuleType, *, role: str = "product"):
    return refresh_mod.ApproverEvidence(
        identity="approver@example.com",
        role=role,
        confirmed_at="2026-08-17T12:00:00Z",
        authorization_source="current-human-session",
    )


def _destination() -> str:
    return "gh://github.com/example-org/example-repo"


def _confirmation(
    refresh_mod: types.ModuleType,
    *,
    action: str = "comment",
    target: str = "101",
    payload: dict[str, object] | None = None,
    confirmation_id: str = "confirm-1",
    role: str = "product",
):
    payload = payload or {"issue_number": target, "body": "Looks good"}
    binding = refresh_mod.ConfirmationBinding(
        artifact_path="docs/product/briefs/example.md",
        source_revision="remote-rev-2",
        profile_id="github-default",
        profile_version="1.0",
        destination=_destination(),
        action=action,
        target=target,
        payload_digest=refresh_mod.canonical_payload_digest(payload),
    )
    return refresh_mod.RemoteConfirmation.issue(
        confirmation_id=confirmation_id,
        binding=binding,
        approver=_approver(refresh_mod, role=role),
        confirmed_at=datetime(2026, 8, 17, 12, 0, tzinfo=UTC),
    )


def _receipt_store(refresh_mod: types.ModuleType, tmp_path: Path):
    repo = tmp_path / "repo"
    artifact = repo / "docs/product/briefs/example.md"
    workspace = repo / "workspace.toml"
    artifact.parent.mkdir(parents=True)
    artifact.write_text(
        '''# Example

```toml source-authority
contract_version = "source-authority.v1"
mode = "tracker-origin"
source_ref = "github://issue/101"
source_revision = "remote-rev-2"

[owned_fields]
Outcome = "local"
```
''',
        encoding="utf-8",
    )
    workspace.write_text("# workspace\n", encoding="utf-8")
    return refresh_mod.RemoteReceiptStore.open(
        repository_root=repo,
        artifact_path="docs/product/briefs/example.md",
        expected_artifact_digest=refresh_mod.digest_bytes(artifact.read_bytes()),
        expected_workspace_digest=refresh_mod.digest_bytes(workspace.read_bytes()),
    )


def _processor(
    github_mod: types.ModuleType,
    refresh_mod: types.ModuleType,
    tmp_path: Path,
    *,
    calls: list[dict[str, object]] | None = None,
    receipts: list[dict[str, object]] | None = None,
):
    calls = calls if calls is not None else []
    receipts = receipts if receipts is not None else []
    store = _receipt_store(refresh_mod, tmp_path)

    def runner(argv: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        durable = refresh_mod.parse_source_authority(
            (store.repository_root / store.artifact_path).read_text()
        ).remote_actions
        receipts.append(dict(durable[-1]))
        calls.append({"argv": argv, **kwargs})
        return subprocess.CompletedProcess(argv, 0, "", "")

    return github_mod.GithubRefreshProcessor(
        configured_host="github.com",
        repository="example-org/example-repo",
        refresh_runtime=refresh_mod,
        receipt_store=store,
        runner=runner,
    )


def test_github_rejects_tracker_selected_host(
    github_mod: types.ModuleType, refresh_mod: types.ModuleType, tmp_path: Path
) -> None:
    calls: list[dict[str, object]] = []
    processor = _processor(github_mod, refresh_mod, tmp_path, calls=calls)

    result = processor.write(
        action="comment",
        target="101",
        body="Looks good",
        tracker_host="attacker.invalid",
        artifact_path="docs/product/briefs/example.md",
        source_revision="remote-rev-2",
        policy=_policy(refresh_mod),
        confirmation=_confirmation(refresh_mod),
        now=datetime(2026, 8, 17, 12, 0, tzinfo=UTC),
    )

    assert result.code == "untrusted_github_host"
    assert result.command_calls == 0
    assert calls == []


def test_github_content_cannot_add_argv(
    github_mod: types.ModuleType, refresh_mod: types.ModuleType, tmp_path: Path
) -> None:
    calls: list[dict[str, object]] = []
    processor = _processor(github_mod, refresh_mod, tmp_path, calls=calls)
    body = "--hostname attacker.invalid"
    confirmation = _confirmation(
        refresh_mod,
        payload={"issue_number": "101", "body": body},
    )

    result = processor.write(
        action="comment",
        target="101",
        body=body,
        artifact_path="docs/product/briefs/example.md",
        source_revision="remote-rev-2",
        policy=_policy(refresh_mod),
        confirmation=confirmation,
        now=datetime(2026, 8, 17, 12, 0, tzinfo=UTC),
    )

    assert result.code == "remote_action_succeeded"
    assert result.argv.count("--hostname") == 1
    assert result.stdin is None
    assert result.payload == {}
    assert calls[0]["shell"] is False
    assert calls[0]["input"] == body


@pytest.mark.parametrize(
    ("action", "kwargs", "payload", "expected_argv_tail", "expected_stdin"),
    [
        (
            "comment",
            {"body": "Reviewed."},
            {"issue_number": "101", "body": "Reviewed."},
            ["comment", "101", "--hostname", "github.com", "--repo", "example-org/example-repo", "--body-file", "-"],
            "Reviewed.",
        ),
        (
            "trace-link",
            {"url": "https://github.com/example-org/example-repo/issues/101"},
            {"issue_number": "101", "body": "Trace link: https://github.com/example-org/example-repo/issues/101"},
            ["comment", "101", "--hostname", "github.com", "--repo", "example-org/example-repo", "--body-file", "-"],
            "Trace link: https://github.com/example-org/example-repo/issues/101",
        ),
        (
            "pull-request-link",
            {"url": "https://github.com/example-org/example-repo/pull/5"},
            {"issue_number": "101", "body": "Pull request: https://github.com/example-org/example-repo/pull/5"},
            ["comment", "101", "--hostname", "github.com", "--repo", "example-org/example-repo", "--body-file", "-"],
            "Pull request: https://github.com/example-org/example-repo/pull/5",
        ),
        (
            "display-status",
            {"status": "status/ready"},
            {"issue_number": "101", "label": "status/ready"},
            ["edit", "101", "--hostname", "github.com", "--repo", "example-org/example-repo", "--add-label", "status/ready"],
            None,
        ),
        (
            "closure",
            {"body": "Done."},
            {"issue_number": "101", "state": "closed"},
            ["close", "101", "--hostname", "github.com", "--repo", "example-org/example-repo"],
            None,
        ),
    ],
)
def test_github_actions_are_confirmed_target_pinned_and_receipted(
    github_mod: types.ModuleType,
    refresh_mod: types.ModuleType,
    action: str,
    kwargs: dict[str, str],
    payload: dict[str, object],
    expected_argv_tail: list[str],
    expected_stdin: str | None,
    tmp_path: Path,
) -> None:
    calls: list[dict[str, object]] = []
    receipts: list[dict[str, object]] = []
    processor = _processor(
        github_mod, refresh_mod, tmp_path, calls=calls, receipts=receipts
    )
    confirmation = _confirmation(
        refresh_mod,
        action=action,
        payload=payload,
        confirmation_id=f"confirm-{action}",
    )

    result = processor.write(
        action=action,
        target="101",
        artifact_path="docs/product/briefs/example.md",
        source_revision="remote-rev-2",
        policy=_policy(refresh_mod),
        confirmation=confirmation,
        now=datetime(2026, 8, 17, 12, 0, tzinfo=UTC),
        **kwargs,
    )

    assert result.code == "remote_action_succeeded"
    assert result.argv == ["gh", "issue", *expected_argv_tail]
    assert result.stdin is None
    assert result.payload == {}
    assert result.payload_digest == refresh_mod.canonical_payload_digest(payload)
    assert calls == [
        {
            "argv": ["gh", "issue", *expected_argv_tail],
            "input": expected_stdin,
            "check": True,
            "capture_output": True,
            "text": True,
            "shell": False,
            "timeout": 30,
        }
    ]
    assert receipts[0]["status"] == "pending"
    assert receipts[0]["identity"] == "approver@example.com"
    assert receipts[0]["role"] == "product"
    store = processor._receipt_store
    durable = refresh_mod.parse_source_authority(
        (store.repository_root / store.artifact_path).read_text()
    ).remote_actions
    assert durable[-1]["status"] == "succeeded"


def test_reused_or_unauthorized_confirmation_runs_no_command(
    github_mod: types.ModuleType, refresh_mod: types.ModuleType, tmp_path: Path
) -> None:
    calls: list[dict[str, object]] = []
    processor = _processor(github_mod, refresh_mod, tmp_path, calls=calls)
    confirmation = _confirmation(refresh_mod)
    kwargs = {
        "action": "comment",
        "target": "101",
        "body": "Looks good",
        "artifact_path": "docs/product/briefs/example.md",
        "source_revision": "remote-rev-2",
        "policy": _policy(refresh_mod),
        "confirmation": confirmation,
        "now": datetime(2026, 8, 17, 12, 0, tzinfo=UTC),
    }

    assert processor.write(**kwargs).code == "remote_action_succeeded"
    replay = processor.write(**kwargs)

    assert replay.code == "confirmation_reused"
    assert replay.command_calls == 0
    assert len(calls) == 1

    unauthorized = _confirmation(refresh_mod, confirmation_id="confirm-unauth", role="guest")
    result = processor.write(**{**kwargs, "confirmation": unauthorized})
    assert result.code == "unauthorized_remote_mutation"
    assert len(calls) == 1


def test_durable_confirmation_ledger_is_required_across_processor_instances(
    github_mod: types.ModuleType, refresh_mod: types.ModuleType, tmp_path: Path
) -> None:
    calls: list[dict[str, object]] = []
    confirmation = _confirmation(refresh_mod)
    kwargs = {
        "action": "comment",
        "target": "101",
        "body": "Looks good",
        "artifact_path": "docs/product/briefs/example.md",
        "source_revision": "remote-rev-2",
        "policy": _policy(refresh_mod),
        "confirmation": confirmation,
        "now": datetime(2026, 8, 17, 12, 0, tzinfo=UTC),
    }
    without_ledger = github_mod.GithubRefreshProcessor(
        configured_host="github.com",
        repository="example-org/example-repo",
        refresh_runtime=refresh_mod,
        runner=lambda argv, **values: calls.append({"argv": argv, **values}),
    )
    store = _receipt_store(refresh_mod, tmp_path)
    durable_receipt = refresh_mod.consume_remote_confirmation(
        confirmation=confirmation,
        expected_binding=confirmation.binding,
        policy=_policy(refresh_mod),
        used_confirmation_ids=set(),
        now=datetime(2026, 8, 17, 12, 0, tzinfo=UTC),
    )
    store.record(durable_receipt)
    seeded_from_artifact = github_mod.GithubRefreshProcessor(
        configured_host="github.com",
        repository="example-org/example-repo",
        refresh_runtime=refresh_mod,
        receipt_store=store,
        runner=lambda argv, **values: calls.append({"argv": argv, **values}),
    )

    assert without_ledger.write(**kwargs).code == "receipt_store_required"
    assert seeded_from_artifact.write(**kwargs).code == "confirmation_reused"
    assert calls == []


def test_unsupported_requirement_body_and_bad_target_run_no_command(
    github_mod: types.ModuleType, refresh_mod: types.ModuleType, tmp_path: Path
) -> None:
    calls: list[dict[str, object]] = []
    processor = _processor(github_mod, refresh_mod, tmp_path, calls=calls)

    unsupported = processor.write(
        action="requirement_body",
        target="101",
        body="Change the requirement",
        artifact_path="docs/product/briefs/example.md",
        source_revision="remote-rev-2",
        policy=_policy(refresh_mod),
        confirmation=_confirmation(refresh_mod, action="requirement_body"),
        now=datetime(2026, 8, 17, 12, 0, tzinfo=UTC),
    )
    bad_target = processor.write(
        action="comment",
        target="https://github.com/example-org/example-repo/issues/101",
        body="Looks good",
        artifact_path="docs/product/briefs/example.md",
        source_revision="remote-rev-2",
        policy=_policy(refresh_mod),
        confirmation=None,
        now=datetime(2026, 8, 17, 12, 0, tzinfo=UTC),
    )

    assert unsupported.code == "unsupported_capability"
    assert bad_target.code == "invalid_remote_payload"
    assert calls == []


@pytest.mark.parametrize(
    ("action", "url"),
    [
        ("trace-link", "https://github.com/example-org/example-repo/issues/1\nInjected"),
        ("trace-link", "https://user@github.com/example-org/example-repo/issues/1"),
        ("trace-link", "https://example.invalid/example-org/example-repo/issues/1"),
        ("trace-link", "https://github.com/other-org/other-repo/issues/1"),
        ("trace-link", "https://github.com:443/example-org/example-repo/issues/1"),
        ("pull-request-link", "https://github.com/example-org/example-repo/issues/1"),
        ("pull-request-link", "https://github.com/example-org/example-repo/pull/0"),
    ],
)
def test_link_actions_reject_untrusted_or_injectable_urls_before_gh(
    github_mod: types.ModuleType,
    refresh_mod: types.ModuleType,
    action: str,
    url: str,
    tmp_path: Path,
) -> None:
    calls: list[dict[str, object]] = []
    processor = _processor(github_mod, refresh_mod, tmp_path, calls=calls)

    result = processor.write(
        action=action,
        target="101",
        url=url,
        artifact_path="docs/product/briefs/example.md",
        source_revision="remote-rev-2",
        policy=_policy(refresh_mod),
        confirmation=None,
        now=datetime(2026, 8, 17, 12, 0, tzinfo=UTC),
    )

    assert result.code == "invalid_remote_payload"
    assert result.command_calls == 0
    assert calls == []


def test_pending_receipt_precedes_gh_and_failed_command_is_retry_safe(
    github_mod: types.ModuleType, refresh_mod: types.ModuleType, tmp_path: Path
) -> None:
    events: list[object] = []
    store = _receipt_store(refresh_mod, tmp_path)

    def runner(argv: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        durable = refresh_mod.parse_source_authority(
            (store.repository_root / store.artifact_path).read_text()
        ).remote_actions
        events.append(("receipt", durable[-1]["status"]))
        events.append(("gh", argv, kwargs["input"]))
        raise subprocess.CalledProcessError(1, argv)

    processor = github_mod.GithubRefreshProcessor(
        configured_host="github.com",
        repository="example-org/example-repo",
        refresh_runtime=refresh_mod,
        receipt_store=store,
        runner=runner,
    )

    result = processor.write(
        action="comment",
        target="101",
        body="Looks good",
        artifact_path="docs/product/briefs/example.md",
        source_revision="remote-rev-2",
        policy=_policy(refresh_mod),
        confirmation=_confirmation(refresh_mod),
        now=datetime(2026, 8, 17, 12, 0, tzinfo=UTC),
    )

    assert result.code == "remote_action_failed"
    assert result.receipt["status"] == "failed"
    assert result.receipt["profile_version"] == "1.0"
    assert events[0] == ("receipt", "pending")
    assert cast(tuple[object, ...], events[1])[0] == "gh"
    durable = refresh_mod.parse_source_authority(
        (store.repository_root / store.artifact_path).read_text()
    ).remote_actions
    assert durable[-1]["status"] == "failed"


def test_pending_receipt_failure_runs_no_command(
    github_mod: types.ModuleType, refresh_mod: types.ModuleType, tmp_path: Path
) -> None:
    calls: list[dict[str, object]] = []
    store = _receipt_store(refresh_mod, tmp_path)
    artifact = store.repository_root / store.artifact_path
    artifact.write_text(artifact.read_text() + "\n# concurrent change\n")

    processor = github_mod.GithubRefreshProcessor(
        configured_host="github.com",
        repository="example-org/example-repo",
        refresh_runtime=refresh_mod,
        receipt_store=store,
        runner=lambda argv, **kwargs: calls.append({"argv": argv, **kwargs}),
    )
    result = processor.write(
        action="comment",
        target="101",
        body="Looks good",
        artifact_path="docs/product/briefs/example.md",
        source_revision="remote-rev-2",
        policy=_policy(refresh_mod),
        confirmation=_confirmation(refresh_mod),
        now=datetime(2026, 8, 17, 12, 0, tzinfo=UTC),
    )
    assert result.code == "fingerprint_mismatch"
    assert result.command_calls == 0
    assert calls == []


def test_github_refresh_registration_and_common_lifecycle_matrix(
    github_mod: types.ModuleType, refresh_mod: types.ModuleType
) -> None:
    registration = github_mod.github_refresh_registration(
        refresh_mod, acquire=_unreached_acquire
    )
    registry = refresh_mod.RefreshProcessorRegistry()
    registry.register(registration)

    assert registry.resolve("github-default", "1.0", "comment").name == "github-refresh"
    assert registration.revision_field == "updatedAt"
    assert registration.field_mapping == (
        ("Outcome", "title"),
        ("User stories", "body"),
    )
    assert registration.capabilities == frozenset({
        "acquire",
        "trace-link",
        "display-status",
        "comment",
        "pull-request-link",
        "closure",
    })

    policy = _policy(refresh_mod)
    approver = _approver(refresh_mod)
    now = datetime(2026, 8, 17, 12, 0, tzinfo=UTC)
    for lifecycle in ("Draft", "Accepted", "Ready", "Approved"):
        authority = refresh_mod.SourceAuthority(
            source_ref="gh://items/101",
            source_revision="remote-rev-1",
            accepted_revision="remote-rev-1",
            owned_fields={
                "requirement": "source" if lifecycle == "Draft" else "local"
            },
            acceptance=refresh_mod.Approval(
                identity="approver@example.com",
                role="product",
                decided_at="2026-08-17T12:00:00Z",
                authorization_source="current-human-session",
            ),
        )
        comparison = refresh_mod.RefreshComparison(
            artifact_path="docs/product/briefs/example.md",
            artifact_kind="brief",
            lifecycle=lifecycle,
            authority_mode="tracker-origin",
            current_revision="remote-rev-1",
            compared_revision="remote-rev-2",
            profile_id="github-default",
            profile_version="1.0",
            changed_fields=(refresh_mod.ChangedField("requirement", "local", "source"),),
        )
        result = refresh_mod.evaluate_refresh(
            comparison=comparison,
            authority=authority,
            policy=policy,
            approver=approver,
            decisions={"requirement": "accept-source"},
            now=now,
        )
        assert result.local_mutation == "pending"
        assert result.compared_revision == "remote-rev-2"

    for lifecycle in ("Implementing", "Executing", "Shipped"):
        comparison = refresh_mod.RefreshComparison(
            artifact_path="docs/product/briefs/example.md",
            artifact_kind="brief",
            lifecycle=lifecycle,
            authority_mode="tracker-origin",
            current_revision="remote-rev-1",
            compared_revision="remote-rev-2",
            profile_id="github-default",
            profile_version="1.0",
        )
        result = refresh_mod.evaluate_refresh(
            comparison=comparison,
            authority=authority,
            policy=policy,
            approver=approver,
            decisions={},
            now=now,
        )
        assert result.local_mutation == "refused"


def test_github_metadata_is_least_privilege() -> None:
    body = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")

    assert "allowed-tools: Read Bash" in body
    assert "network_fetch" in body
    assert "filesystem_read_untrusted" in body
    assert "filesystem_write" not in body
    assert "credentialed: true" in body
    assert "primitive-class: credentialed-cli" in body
    assert "auth: cli" in body
    assert "primitive-class: approved-cli" not in body
    assert "auth: gh" not in body
    assert "namespace:" not in body
    assert "keys:" not in body
