#!/usr/bin/env python3
"""GitHub refresh processor using the approved fixed-host gh boundary."""

from __future__ import annotations

import contextlib
import importlib.util
import json
import re
import subprocess
import sys
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path
from types import ModuleType
from typing import Any, Callable, Mapping, cast
from urllib.parse import urlsplit

for _stream, _errors in ((sys.stdout, "strict"), (sys.stderr, "backslashreplace")):
    with contextlib.suppress(AttributeError, ValueError):
        _stream.reconfigure(encoding="utf-8", errors=_errors)  # type: ignore[union-attr]

PROFILE_PATH = Path(__file__).resolve().parents[1] / "references" / "refresh-profile.json"
GITHUB_PROFILE_ID = "github-default"
GITHUB_PROFILE_VERSION = "1.0"
GITHUB_REFRESH_CAPABILITIES = frozenset({
    "acquire",
    "trace-link",
    "display-status",
    "comment",
    "pull-request-link",
    "closure",
})
_REMOTE_ACTIONS = GITHUB_REFRESH_CAPABILITIES - {"acquire"}
_HOST_PATTERN = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9.-]{0,251}[A-Za-z0-9])?$")
_REPOSITORY_PATTERN = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
_ISSUE_PATTERN = re.compile(r"^[1-9][0-9]{0,11}$")
_LABEL_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:/ -]{0,99}$")


class GithubRefreshPolicyError(ValueError):
    """A stable, redacted GitHub processor refusal."""


class GithubWriteBackResult:
    """Redacted result for one confirmed GitHub write-back attempt."""

    def __init__(
        self,
        code: str,
        action: str,
        *,
        target: str = "",
        payload_digest: str | None = None,
        argv: list[str] | None = None,
        command_calls: int = 0,
        receipt: dict[str, object] | None = None,
    ) -> None:
        self.code = code
        self.action = action
        self.target = target
        self.payload_digest = payload_digest
        self.argv = argv or []
        self.stdin: None = None
        self.payload: dict[str, object] = {}
        self.command_calls = command_calls
        self.receipt = receipt or {}


def load_profile(path: Path = PROFILE_PATH) -> dict[str, Any]:
    """Load one strict, versioned GitHub refresh profile."""

    profile = json.loads(path.read_text(encoding="utf-8"), parse_constant=_reject_constant)
    if not isinstance(profile, dict) or set(profile) != {
        "contract_version",
        "id",
        "version",
        "destination",
        "capabilities",
        "revision_field",
        "field_mapping",
    }:
        raise GithubRefreshPolicyError("invalid_refresh_profile")
    if (
        profile["contract_version"] != "tracker-refresh-profile.v1"
        or profile["id"] != GITHUB_PROFILE_ID
        or profile["version"] != GITHUB_PROFILE_VERSION
    ):
        raise GithubRefreshPolicyError("unsupported_refresh_profile")
    if profile["revision_field"] != "updatedAt" or profile["field_mapping"] != {
        "Outcome": "title",
        "User stories": "body",
    }:
        raise GithubRefreshPolicyError("invalid_refresh_profile")
    destination = profile["destination"]
    if (
        not isinstance(destination, dict)
        or destination.get("boundary") != "approved-gh-fixed-host"
        or destination.get("host_source") != "trusted-configuration-only"
        or destination.get("payload_host_allowed") is not False
    ):
        raise GithubRefreshPolicyError("unapproved_github_boundary")
    capabilities = profile["capabilities"]
    if (
        not isinstance(capabilities, list)
        or any(not isinstance(value, str) for value in capabilities)
        or len(capabilities) != len(set(capabilities))
        or frozenset(capabilities) != GITHUB_REFRESH_CAPABILITIES
    ):
        raise GithubRefreshPolicyError("invalid_github_capabilities")
    allowed_hosts = destination.get("allowed_hosts")
    if allowed_hosts != ["github.com"]:
        raise GithubRefreshPolicyError("unapproved_github_boundary")
    return profile


def validate_configured_target(
    configured_host: str,
    repository: str,
    profile: dict[str, Any],
    *,
    tracker_host: str | None = None,
) -> tuple[str, str]:
    """Accept host and repository only from trusted configuration."""

    if tracker_host is not None:
        raise GithubRefreshPolicyError("untrusted_github_host")
    host = configured_host.rstrip(".").lower()
    allowed = {str(value).rstrip(".").lower() for value in profile["destination"]["allowed_hosts"]}
    if not _HOST_PATTERN.fullmatch(host) or host not in allowed:
        raise GithubRefreshPolicyError("untrusted_github_host")
    if not _REPOSITORY_PATTERN.fullmatch(repository) or "://" in repository:
        raise GithubRefreshPolicyError("untrusted_github_repository")
    owner, name = repository.split("/", 1)
    if owner in {".", ".."} or name in {".", ".."}:
        raise GithubRefreshPolicyError("untrusted_github_repository")
    return host, repository


def github_refresh_registration(
    refresh_runtime: ModuleType | None = None,
    *,
    acquire: Callable[[str, str], Mapping[str, object]],
) -> object:
    """Return the configured GitHub refresh processor registration."""

    runtime = refresh_runtime or _load_refresh_runtime()
    return runtime.ProcessorRegistration(
        name="github-refresh",
        profile_id=GITHUB_PROFILE_ID,
        profile_version=GITHUB_PROFILE_VERSION,
        capabilities=GITHUB_REFRESH_CAPABILITIES,
        acquire=acquire,
        revision_field="updatedAt",
        field_mapping=(("Outcome", "title"), ("User stories", "body")),
    )


class GithubRefreshProcessor:
    """Configured GitHub refresh/write-back edge using shared confirmations."""

    def __init__(
        self,
        *,
        configured_host: str,
        repository: str,
        refresh_runtime: ModuleType | None = None,
        runner: Callable[..., subprocess.CompletedProcess[str]] | None = None,
        receipt_store: object | None = None,
        profile: dict[str, Any] | None = None,
    ) -> None:
        self._refresh = refresh_runtime or _load_refresh_runtime()
        self._profile = profile or load_profile()
        self._host, self._repository = validate_configured_target(
            configured_host,
            repository,
            self._profile,
        )
        self._runner = runner or self._default_runner
        self._receipt_store = receipt_store

    def write(
        self,
        *,
        action: str,
        target: str,
        artifact_path: str,
        source_revision: str,
        policy: object,
        confirmation: object | None,
        now: datetime | None = None,
        body: str | None = None,
        url: str | None = None,
        status: str | None = None,
        tracker_host: str | None = None,
        tracker_repository: str | None = None,
    ) -> GithubWriteBackResult:
        """Execute one confirmed GitHub mutation with a fakeable command runner."""

        try:
            if tracker_host is not None:
                raise GithubRefreshPolicyError("untrusted_github_host")
            if tracker_repository is not None:
                raise GithubRefreshPolicyError("untrusted_github_repository")
            if action not in _REMOTE_ACTIONS:
                return GithubWriteBackResult("unsupported_capability", action, target=target)
            receipt_store = self._receipt_store
            if not isinstance(receipt_store, self._refresh.RemoteReceiptStore):
                return GithubWriteBackResult(
                    "receipt_store_required", action, target=target
                )
            if receipt_store.artifact_path != artifact_path:
                return GithubWriteBackResult(
                    "receipt_store_mismatch", action, target=target
                )
            payload = self._payload_for_action(
                action=action,
                target=target,
                body=body,
                url=url,
                status=status,
            )
            if payload is None:
                return GithubWriteBackResult("invalid_remote_payload", action, target=target)
            argv, stdin_data = self._command_for_action(action, payload)
            payload_digest = self._refresh.canonical_payload_digest(payload)
            binding = self._refresh.ConfirmationBinding(
                artifact_path=artifact_path,
                source_revision=source_revision,
                profile_id=GITHUB_PROFILE_ID,
                profile_version=GITHUB_PROFILE_VERSION,
                destination=f"gh://{self._host}/{self._repository}",
                action=action,
                target=target,
                payload_digest=payload_digest,
            )
            if confirmation is None:
                raise self._refresh.RefreshRefusal("confirmation_required")
            receipt = self._refresh.consume_remote_confirmation(
                confirmation=confirmation,
                expected_binding=binding,
                policy=policy,
                used_confirmation_ids=receipt_store.confirmation_ids(),
                now=now or datetime.now(UTC),
            )
            try:
                receipt_store.record(receipt)
            except Exception:
                return GithubWriteBackResult("pending_receipt_failed", action)
            self._runner(
                list(argv),
                input=stdin_data,
                check=True,
                capture_output=True,
                text=True,
                shell=False,
                timeout=30,
            )
        except (GithubRefreshPolicyError, self._refresh.RefreshRefusal) as exc:
            return GithubWriteBackResult(str(exc), action, target=target)
        except (subprocess.SubprocessError, OSError):
            failed = {}
            code = "remote_action_failed"
            if "receipt" in locals():
                failed_receipt = replace(receipt, status="failed")
                try:
                    receipt_store.record(failed_receipt)
                    failed = dict(failed_receipt.__dict__)
                except Exception:
                    failed = dict(receipt.__dict__)
                    code = "receipt_update_failed"
            return GithubWriteBackResult(
                code,
                action,
                target=target,
                payload_digest=payload_digest if "payload_digest" in locals() else None,
                argv=argv if "argv" in locals() else [],
                command_calls=1 if "receipt" in locals() else 0,
                receipt=failed,
            )
        succeeded_receipt = replace(receipt, status="succeeded")
        succeeded = dict(succeeded_receipt.__dict__)
        try:
            receipt_store.record(succeeded_receipt)
        except Exception:
            return GithubWriteBackResult(
                "receipt_update_failed",
                action,
                target=target,
                payload_digest=payload_digest,
                argv=argv,
                command_calls=1,
                receipt={**receipt.__dict__, "status": "pending"},
            )
        return GithubWriteBackResult(
            "remote_action_succeeded",
            action,
            target=target,
            payload_digest=payload_digest,
            argv=argv,
            command_calls=1,
            receipt=succeeded,
        )

    def _command_for_action(
        self, action: str, payload: dict[str, object]
    ) -> tuple[list[str], str | None]:
        issue = str(payload["issue_number"])
        base = ["gh", "issue"]
        fixed = ["--hostname", self._host, "--repo", self._repository]
        if action in {"comment", "trace-link", "pull-request-link"}:
            return [*base, "comment", issue, *fixed, "--body-file", "-"], str(payload["body"])
        if action == "display-status":
            return [*base, "edit", issue, *fixed, "--add-label", str(payload["label"])], None
        return [*base, "close", issue, *fixed], None

    def _payload_for_action(
        self,
        *,
        action: str,
        target: str,
        body: str | None,
        url: str | None,
        status: str | None,
    ) -> dict[str, object] | None:
        if not _ISSUE_PATTERN.fullmatch(target):
            return None
        payload: dict[str, object] = {"issue_number": target}
        if action == "comment" and body is not None:
            payload["body"] = body
            return payload
        if action == "trace-link" and _trusted_https_url(
            url,
            host=self._host,
            repository=self._repository,
        ):
            payload["body"] = f"Trace link: {url}"
            return payload
        if action == "pull-request-link" and _trusted_https_url(
            url,
            host=self._host,
            repository=self._repository,
            require_pull=True,
        ):
            payload["body"] = f"Pull request: {url}"
            return payload
        if action == "display-status" and status and _LABEL_PATTERN.fullmatch(status):
            payload["label"] = status
            return payload
        if action == "closure":
            payload["state"] = "closed"
            return payload
        return None

    @staticmethod
    def _default_runner(
        argv: list[str],
        **kwargs: object,
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(  # noqa: S603 — argv is built by this processor.
            argv,
            input=cast(str | None, kwargs.get("input")),
            check=cast(bool, kwargs.get("check")),
            capture_output=cast(bool, kwargs.get("capture_output")),
            text=cast(bool, kwargs.get("text")),
            shell=False,
            timeout=cast(float, kwargs.get("timeout")),
        )


def _trusted_https_url(
    value: str | None,
    *,
    host: str,
    repository: str,
    require_pull: bool = False,
) -> bool:
    if not value or any(
        char.isspace() or ord(char) < 32 or ord(char) == 127 for char in value
    ):
        return False
    try:
        parsed = urlsplit(value)
        port = parsed.port
    except ValueError:
        return False
    if (
        parsed.scheme != "https"
        or parsed.username is not None
        or parsed.password is not None
        or parsed.hostname != host.lower()
        or port is not None
        or parsed.netloc.lower() != host.lower()
    ):
        return False
    repository_path = f"/{repository}"
    if require_pull:
        return bool(
            re.fullmatch(
                rf"{re.escape(repository_path)}/pull/[1-9][0-9]{{0,11}}/?",
                parsed.path,
            )
        )
    return parsed.path == repository_path or parsed.path.startswith(f"{repository_path}/")


def _load_refresh_runtime() -> ModuleType:
    """Load the shared work-intake refresh runtime from an installed skill tree."""

    here = Path(__file__).resolve()
    skills_root = here.parents[2]
    candidate = skills_root / "work-intake" / "scripts" / "refresh.py"
    try:
        resolved_root = skills_root.resolve(strict=True)
        resolved = candidate.resolve(strict=True)
        resolved.relative_to(resolved_root)
    except (OSError, ValueError) as exc:
        raise RuntimeError("work-intake refresh runtime unavailable") from exc
    if not resolved.is_file():
        raise RuntimeError("work-intake refresh runtime unavailable")
    spec = importlib.util.spec_from_file_location("work_intake_refresh", resolved)
    if spec is None or spec.loader is None:
        raise RuntimeError("work-intake refresh runtime unavailable")
    module = importlib.util.module_from_spec(spec)
    sys.modules.setdefault(spec.name, module)
    spec.loader.exec_module(module)  # type: ignore[union-attr]
    return module


def _reject_constant(value: str) -> None:
    raise GithubRefreshPolicyError(f"non-standard JSON constant: {value}")
