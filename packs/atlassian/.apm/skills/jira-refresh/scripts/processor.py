"""Jira refresh processor composed with the shared work-intake runtime."""

from __future__ import annotations

import importlib.util
import sys
from contextlib import suppress
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Callable, Collection, Mapping

with suppress(AttributeError, ValueError):
    sys.stdout.reconfigure(encoding="utf-8", errors="strict")
with suppress(AttributeError, ValueError):
    sys.stderr.reconfigure(encoding="utf-8", errors="backslashreplace")

PROFILE_ID = "jira-default"
PROFILE_VERSION = "1.0"
SUPPORTED_REMOTE_ACTIONS = frozenset({"comment", "display-status", "closure"})


@dataclass(frozen=True)
class WriteBackResult:
    """Redacted result of one confirmed Jira write-back attempt."""

    code: str
    action: str
    target: str
    payload_digest: str | None = None
    receipt: object | None = None
    transport_calls: int = 0


def _load_refresh_runtime() -> Any:
    skills_root = Path(__file__).resolve().parents[2]
    try:
        resolved_root = skills_root.resolve(strict=True)
        runtime = (skills_root / "work-intake" / "scripts" / "refresh.py").resolve(
            strict=True
        )
        runtime.relative_to(resolved_root)
    except (OSError, ValueError) as exc:
        raise RuntimeError("work-intake refresh runtime is unavailable") from exc
    if not runtime.is_file():
        raise RuntimeError("work-intake refresh runtime is unavailable")
    spec = importlib.util.spec_from_file_location("work_intake_refresh_runtime", runtime)
    if spec is None or spec.loader is None:
        raise RuntimeError("work-intake refresh runtime is unavailable")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def register(
    registry: object,
    refresh_runtime: object | None = None,
    *,
    acquire: Callable[[str, str], Mapping[str, object]],
) -> None:
    """Register the exact Jira profile capability with work-intake."""

    refresh = refresh_runtime or _load_refresh_runtime()
    registry.register(
        refresh.ProcessorRegistration(
            name="jira-refresh",
            profile_id=PROFILE_ID,
            profile_version=PROFILE_VERSION,
            capabilities=frozenset({"acquire", *SUPPORTED_REMOTE_ACTIONS}),
            acquire=acquire,
            revision_field="updated",
            field_mapping=(("Outcome", "summary"), ("User stories", "description")),
        )
    )


def validate_destination(
    url: str,
    *,
    refresh_runtime: object | None = None,
    resolver: Callable[[str], Collection[str]] | None = None,
) -> object:
    """Validate the configured Jira destination before credentials or transport."""

    refresh = refresh_runtime or _load_refresh_runtime()
    policy = refresh.DestinationPolicy(
        schemes=frozenset({"https"}),
        hosts=frozenset({"tracker.example.test"}),
        ports=frozenset({443}),
        credentials_attached=True,
    )
    kwargs = {"policy": policy}
    if resolver is not None:
        kwargs["resolver"] = resolver
    return refresh.validate_destination(url, **kwargs)


async def write_back(
    *,
    client: object,
    action: str,
    target: str,
    payload: Mapping[str, object],
    confirmation: object,
    policy: object,
    receipt_store: object,
    artifact_path: str,
    source_revision: str,
    destination: str,
    refresh_runtime: object | None = None,
    destination_resolver: Callable[[str], Collection[str]] | None = None,
    now: datetime | None = None,
) -> WriteBackResult:
    """Perform one confirmed allowlisted Jira remote mutation."""

    refresh = refresh_runtime or _load_refresh_runtime()
    if action not in SUPPORTED_REMOTE_ACTIONS:
        return WriteBackResult("unsupported_capability", action, target)
    if getattr(client, "_auth_mode", "creds") == "sso-cookie":
        return WriteBackResult("sso_cookie_write_refused", action, target)
    client_policy = getattr(client, "_intake_policy", None)
    if client_policy is None or not getattr(client_policy, "allow_write", False):
        return WriteBackResult("guarded_write_client_required", action, target)
    if not isinstance(receipt_store, refresh.RemoteReceiptStore):
        return WriteBackResult("receipt_store_required", action, target)
    if receipt_store.artifact_path != artifact_path:
        return WriteBackResult("receipt_store_mismatch", action, target)

    try:
        validate_destination(
            destination,
            refresh_runtime=refresh,
            resolver=destination_resolver,
        )
        if getattr(client_policy, "origin", None) != destination.rstrip("/"):
            return WriteBackResult("guarded_write_client_mismatch", action, target)
        canonical_payload = _payload_for_action(action, target, payload)
        digest = refresh.canonical_payload_digest(canonical_payload)
    except refresh.RefreshRefusal as exc:
        return WriteBackResult(str(exc), action, target)
    except Exception:
        return WriteBackResult("destination_or_payload_invalid", action, target)
    binding = refresh.ConfirmationBinding(
        artifact_path=artifact_path,
        source_revision=source_revision,
        profile_id=PROFILE_ID,
        profile_version=PROFILE_VERSION,
        destination=destination,
        action=action,
        target=target,
        payload_digest=digest,
    )
    try:
        receipt = refresh.consume_remote_confirmation(
            confirmation=confirmation,
            expected_binding=binding,
            policy=policy,
            used_confirmation_ids=receipt_store.confirmation_ids(),
            now=now or datetime.now(UTC),
        )
    except refresh.RefreshRefusal as exc:
        return WriteBackResult(str(exc), action, target)
    except Exception:
        return WriteBackResult("confirmation_invalid", action, target)
    try:
        receipt_store.record(receipt)
    except Exception:
        return WriteBackResult("pending_receipt_failed", action, target)

    try:
        if action == "comment":
            await client.add_comment(target, str(canonical_payload["body"]))
        else:
            await client.transition_issue(
                target,
                transition_name=str(canonical_payload["transition"]),
            )
    except Exception:
        failed_receipt = replace(receipt, status="failed")
        try:
            receipt_store.record(failed_receipt)
            result_code = "remote_action_failed"
            durable_receipt = failed_receipt
        except Exception:
            result_code = "receipt_update_failed"
            durable_receipt = receipt
        return WriteBackResult(
            result_code,
            action,
            target,
            payload_digest=digest,
            receipt=durable_receipt,
            transport_calls=_transport_calls(client),
        )
    succeeded_receipt = replace(receipt, status="succeeded")
    try:
        receipt_store.record(succeeded_receipt)
    except Exception:
        return WriteBackResult(
            "receipt_update_failed",
            action,
            target,
            payload_digest=digest,
            receipt=receipt,
            transport_calls=_transport_calls(client),
        )
    return WriteBackResult(
        "succeeded",
        action,
        target,
        payload_digest=digest,
        receipt=succeeded_receipt,
        transport_calls=_transport_calls(client),
    )


def _payload_for_action(
    action: str,
    target: str,
    payload: Mapping[str, object],
) -> Mapping[str, object]:
    if action == "comment":
        body = payload.get("body")
        if not isinstance(body, str) or not body:
            raise ValueError("invalid_remote_payload")
        return {"issue_key": target, "body": body}
    transition = payload.get("transition")
    if not isinstance(transition, str) or not transition:
        raise ValueError("invalid_remote_payload")
    return {"issue_key": target, "transition": transition}


def _transport_calls(client: object) -> int:
    calls = getattr(client, "calls", ())
    try:
        return len(calls)
    except TypeError:
        return 0
