"""Shared, fail-closed primitives for reviewed tracker refresh and write-back."""

from __future__ import annotations

import copy
import hashlib
import importlib
import importlib.util
import ipaddress
import json
import os
import re
import socket
import sys
import tempfile
import tomllib
from contextlib import suppress
from dataclasses import dataclass, field, replace
from datetime import UTC, datetime, timedelta
from pathlib import Path
from types import ModuleType
from typing import Callable, ClassVar, Collection, Mapping
from urllib.parse import urlsplit


class RefreshRefusal(ValueError):
    """A stable, redacted refusal safe to return to the caller."""


RESULT_CODES = frozenset(
    {
        "accepted_field_not_local",
        "authority_revision_mismatch",
        "cancelled_requirements_locked",
        "comparison_failed",
        "decision_required",
        "executing_requirements_locked",
        "fingerprint_mismatch",
        "implementing_requirements_locked",
        "invalid_authority",
        "invalid_local_update",
        "invalid_refresh_policy",
        "invalid_target",
        "local_field_locked",
        "local_write_failed",
        "local_write_inconsistent",
        "lock_busy",
        "ownership_map_missing",
        "projection_drift",
        "ready",
        "shipped_requirements_locked",
        "unauthorized_approver",
        "unsupported_artifact_kind",
        "unsupported_lifecycle",
        "withdrawn_requirements_locked",
    }
)


@dataclass(frozen=True)
class Approval:
    """Recorded approval evidence embedded in the local artifact."""

    identity: str
    role: str
    decided_at: str
    authorization_source: str


@dataclass(frozen=True)
class SourceAuthority:
    """Parsed source-authority contract from one artifact."""

    source_ref: str
    source_revision: str
    accepted_revision: str | None
    owned_fields: Mapping[str, str]
    acceptance: Approval | None
    source_decisions: tuple[Mapping[str, object], ...] = ()
    conflicts: tuple[Mapping[str, object], ...] = ()
    local_receipts: tuple[Mapping[str, object], ...] = ()
    remote_actions: tuple[Mapping[str, object], ...] = ()
    mode: str = "tracker-origin"


@dataclass(frozen=True)
class RefreshAuthorizationPolicy:
    """Repository-owned role policy for refresh decisions."""

    draft_approver_roles: tuple[str, ...]
    accepted_approver_roles: tuple[str, ...]
    remote_mutation_approver_roles: tuple[str, ...]


@dataclass(frozen=True)
class ApproverEvidence:
    """Current human-session evidence; never sourced from tracker content."""

    identity: str
    role: str
    confirmed_at: str
    authorization_source: str


@dataclass(frozen=True)
class ChangedField:
    """One normalized comparison between the local and source values."""

    name: str
    local_value: str
    source_value: str


@dataclass(frozen=True)
class RefreshComparison:
    """Normalized, untrusted-source comparison presented for review."""

    artifact_path: str
    artifact_kind: str
    lifecycle: str
    authority_mode: str
    current_revision: str
    compared_revision: str
    profile_id: str
    profile_version: str
    changed_fields: tuple[ChangedField, ...] = ()


@dataclass(frozen=True)
class RefreshResult:
    """Stable result returned without raw source payloads or exceptions."""

    code: str
    comparison_status: str
    local_mutation: str = "none"
    conflict_state: str = "none"
    compared_revision: str | None = None
    accepted_revision: str | None = None
    field_updates: Mapping[str, str] = field(default_factory=dict)
    decision_records: tuple[Mapping[str, str], ...] = ()
    remote_action: object | None = None

    def __post_init__(self) -> None:
        """Reject a coordinator result outside the closed public vocabulary."""

        if self.code not in RESULT_CODES:
            raise ValueError("unknown refresh result code")

    def as_record(self) -> dict[str, object]:
        """Return the closed JSON-compatible coordinator result contract."""

        record: dict[str, object] = {
            "contract_version": "refresh-result.v1",
            "code": self.code,
            "comparison_status": self.comparison_status,
            "local_mutation": self.local_mutation,
            "conflict_state": self.conflict_state,
            "field_updates": dict(self.field_updates),
            "decision_records": [dict(value) for value in self.decision_records],
        }
        if self.compared_revision is not None:
            record["compared_revision"] = self.compared_revision
        if self.accepted_revision is not None:
            record["accepted_revision"] = self.accepted_revision
        if self.remote_action is not None:
            record["remote_action"] = self.remote_action
        return record


@dataclass(frozen=True)
class RefreshAcquisitionRequest:
    """Trusted local context and configured acquisition seam for one refresh."""

    artifact_path: str
    artifact_kind: str
    lifecycle: str
    authority_mode: str
    source_ref: str
    current_revision: str
    compared_revision: str
    profile_id: str
    profile_version: str
    local_fields: Mapping[str, str]


@dataclass(frozen=True)
class RefreshInvocationResult:
    """Redacted configured-processor result returned to the intake front door."""

    code: str
    processor: str
    comparison: RefreshComparison | None = None
    normalized_record: Mapping[str, object] | None = None


@dataclass(frozen=True)
class ProcessorRegistration:
    """One executable, explicitly configured refresh processor."""

    name: str
    profile_id: str
    profile_version: str
    capabilities: frozenset[str]
    acquire: Callable[[str, str], Mapping[str, object]] | None = None
    revision_field: str | None = None
    field_mapping: tuple[tuple[str, str], ...] = ()

    def acquire_map_compare(
        self, request: RefreshAcquisitionRequest
    ) -> RefreshInvocationResult:
        """Acquire the exact source revision, map it, validate it, and compare it."""

        try:
            if (
                "acquire" not in self.capabilities
                or not callable(self.acquire)
                or self.revision_field is None
                or not self.field_mapping
                or request.profile_id != self.profile_id
                or request.profile_version != self.profile_version
            ):
                raise RefreshRefusal("processor_unavailable")
            if request.authority_mode != "tracker-origin":
                return RefreshInvocationResult("projection_drift", self.name)
            mapping = dict(self.field_mapping)
            if (
                len(mapping) != len(self.field_mapping)
                or not request.local_fields
                or not set(request.local_fields).issubset(mapping)
            ):
                raise RefreshRefusal("invalid_refresh_request")
            acquired = self.acquire(request.source_ref, request.compared_revision)
            if not isinstance(acquired, dict):
                raise RefreshRefusal("acquisition_failed")
            redact = _intake_guard_callable("_redact")
            object_type = acquired.get("type")
            if isinstance(object_type, str):
                object_type = redact(object_type)
            if (
                acquired.get("locator") != request.source_ref
                or acquired.get(self.revision_field) != request.compared_revision
                or not isinstance(object_type, str)
                or not object_type
                or len(object_type) > 120
            ):
                raise RefreshRefusal("acquired_source_mismatch")
            content: dict[str, list[str]] = {
                "outcomes": [],
                "constraints": [],
                "evidence": [],
                "behaviors": [],
                "assumptions": [],
                "named_gaps": [],
            }
            slots = {"Outcome": "outcomes", "User stories": "behaviors"}
            source_values: dict[str, str] = {}
            for canonical_field, source_field in self.field_mapping:
                slot = slots.get(canonical_field)
                value = acquired.get(source_field)
                if (
                    slot is None
                    or not isinstance(source_field, str)
                    or not source_field
                    or not isinstance(value, str)
                    or not value
                    or len(value) > 2000
                ):
                    raise RefreshRefusal("invalid_acquired_record")
                value = redact(value)
                if not isinstance(value, str):
                    raise RefreshRefusal("invalid_acquired_record")
                content[slot].append(value)
                source_values[canonical_field] = value
            normalized: dict[str, object] = {
                "contract_version": "normalized-intake.v1",
                "action": "refresh",
                "content": content,
                "source": {
                    "mode": "tracker-origin",
                    "locator": request.source_ref,
                    "revision": request.compared_revision,
                    "tracker_profile": {
                        "id": self.profile_id,
                        "version": self.profile_version,
                    },
                    "object_type": object_type,
                },
                "constraints": {},
                "proposed_authority": "tracker-origin",
                "refresh_target": request.artifact_path,
            }
            validator = _workspace_status_callable("validate_normalized_intake")
            parsed, findings = validator(normalized)
            if parsed is None or findings:
                raise RefreshRefusal("invalid_normalized_intake")
            changes = tuple(
                ChangedField(name, local_value, source_values[name])
                for name, local_value in request.local_fields.items()
                if local_value != source_values[name]
            )
            comparison = RefreshComparison(
                artifact_path=request.artifact_path,
                artifact_kind=request.artifact_kind,
                lifecycle=request.lifecycle,
                authority_mode=request.authority_mode,
                current_revision=request.current_revision,
                compared_revision=request.compared_revision,
                profile_id=request.profile_id,
                profile_version=request.profile_version,
                changed_fields=changes,
            )
            return RefreshInvocationResult(
                "completed", self.name, comparison, normalized
            )
        except RefreshRefusal as exc:
            return RefreshInvocationResult(str(exc), self.name)
        except (SystemExit, Exception):  # noqa: BLE001  # configured adapter boundary
            return RefreshInvocationResult("acquisition_failed", self.name)


class RefreshProcessorRegistry:
    """Resolve only exact configured profile and version registrations."""

    def __init__(self) -> None:
        self._registrations: dict[tuple[str, str], ProcessorRegistration] = {}

    def register(self, registration: ProcessorRegistration) -> None:
        key = (registration.profile_id, registration.profile_version)
        if key in self._registrations:
            raise RefreshRefusal("processor_already_registered")
        if "acquire" in registration.capabilities and (
            not callable(registration.acquire)
            or registration.revision_field is None
            or not registration.field_mapping
        ):
            raise RefreshRefusal("invalid_processor_registration")
        self._registrations[key] = registration

    def resolve(
        self,
        profile_id: str,
        profile_version: str,
        required_capability: str | None = None,
    ) -> ProcessorRegistration:
        registration = self._registrations.get((profile_id, profile_version))
        if registration is not None:
            if (
                required_capability is not None
                and required_capability not in registration.capabilities
            ):
                raise RefreshRefusal("unsupported_capability")
            return registration
        if any(key[0] == profile_id for key in self._registrations):
            raise RefreshRefusal("profile_version_mismatch")
        raise RefreshRefusal("processor_unavailable")


@dataclass(frozen=True)
class ConfirmationBinding:
    """Exact mutation tuple covered by one human confirmation."""

    artifact_path: str
    source_revision: str
    profile_id: str
    profile_version: str
    destination: str
    action: str
    target: str
    payload_digest: str


@dataclass(frozen=True)
class RemoteConfirmation:
    """Fresh, single-use confirmation issued by the current human session."""

    confirmation_id: str
    binding: ConfirmationBinding
    approver: ApproverEvidence
    confirmed_at: datetime

    @classmethod
    def issue(
        cls,
        *,
        confirmation_id: str,
        binding: ConfirmationBinding,
        approver: ApproverEvidence,
        confirmed_at: datetime,
    ) -> RemoteConfirmation:
        if not confirmation_id or confirmed_at.tzinfo is None:
            raise RefreshRefusal("invalid_confirmation")
        return cls(confirmation_id, binding, approver, confirmed_at.astimezone(UTC))


@dataclass(frozen=True)
class RemoteActionReceipt:
    """Local pending record created before any adapter performs a write."""

    confirmation_id: str
    mutation_digest: str
    profile_version: str
    payload_digest: str
    identity: str
    role: str
    confirmed_at: str
    authorization_source: str
    action: str
    target: str
    status: str = "pending"


@dataclass(frozen=True)
class RemoteReceiptWriteResult:
    """Outcome and next artifact fingerprint for one durable receipt write."""

    code: str
    artifact_digest: str | None = None


@dataclass(frozen=True)
class DestinationPolicy:
    """Trusted destination allowlist supplied by an adapter profile."""

    schemes: frozenset[str]
    hosts: frozenset[str]
    ports: frozenset[int]
    credentials_attached: bool = False


@dataclass(frozen=True)
class PinnedDestination:
    """Validated destination plus addresses pinned for the request."""

    url: str
    scheme: str
    host: str
    port: int
    addresses: tuple[str, ...]


@dataclass(frozen=True)
class GuardedWriteResult:
    """Redacted outcome of the guarded artifact/workspace write."""

    code: str


_AUTHORITY_FENCE = re.compile(
    r"^```toml source-authority\s*$\n(?P<body>.*?)^```\s*$",
    re.MULTILINE | re.DOTALL,
)
_AUTHORITY_FENCE_OPENING = re.compile(
    r"^```toml source-authority[ \t]*(?:\r?\n)?$"
)
_COORDINATION_FENCE = re.compile(
    r"^```toml coordination-receipts\s*$\n(?P<body>.*?)^```\s*$",
    re.MULTILINE | re.DOTALL,
)
_SECTION_HEADING = re.compile(r"^##[ \t]+(?P<name>[^\r\n]+?)[ \t]*(?:\r?\n)?$")
_FENCE_LINE = re.compile(r"^[ \t]*(?P<fence>`{3,}|~{3,})")
_TOP_AUTHORITY_KEYS = {
    "contract_version",
    "mode",
    "source_ref",
    "source_revision",
    "accepted_revision",
    "owned_fields",
    "acceptance",
    "source_decisions",
    "conflicts",
    "local_receipts",
    "remote_actions",
}
_APPROVAL_KEYS = {"identity", "role", "decided_at", "authorization_source"}
_POLICY_KEYS = {
    "contract_version",
    "draft_approver_roles",
    "accepted_approver_roles",
    "remote_mutation_approver_roles",
}
_DECISIONS = {"keep-local", "accept-source", "revise-both"}
_REMOTE_ACTIONS = {
    "trace-link",
    "display-status",
    "comment",
    "pull-request-link",
    "closure",
}
_DRAFT_LIFECYCLES = {"Draft"}
_ACCEPTED_LIFECYCLES = {"Accepted", "Ready", "Approved"}


def _require_exact_keys(
    value: Mapping[str, object],
    allowed: set[str],
    required: set[str],
    code: str,
) -> None:
    if set(value) - allowed or not required.issubset(value):
        raise RefreshRefusal(code)


def _nonempty_string(value: object, code: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise RefreshRefusal(code)
    return value


def _bounded_string(value: object, maximum: int, code: str) -> str:
    text = _nonempty_string(value, code)
    if len(text) > maximum:
        raise RefreshRefusal(code)
    return text


def _timestamp(value: object, code: str) -> str:
    text = _bounded_string(value, 40, code)
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError as exc:
        raise RefreshRefusal(code) from exc
    if parsed.tzinfo is None:
        raise RefreshRefusal(code)
    return text


def _digest(value: object, code: str) -> str:
    text = _nonempty_string(value, code)
    if re.fullmatch(r"[a-f0-9]{64}", text) is None:
        raise RefreshRefusal(code)
    return text


def parse_source_authority(markdown: str) -> SourceAuthority:
    """Parse the artifact's one closed ``source-authority`` TOML block."""

    matches = list(_AUTHORITY_FENCE.finditer(markdown))
    if len(matches) != 1:
        reason = "duplicate_source_authority" if len(matches) > 1 else "missing_source_authority"
        raise RefreshRefusal(reason)
    try:
        data = tomllib.loads(matches[0].group("body"))
        _require_exact_keys(
            data,
            _TOP_AUTHORITY_KEYS,
            {
                "contract_version",
                "mode",
                "source_ref",
                "source_revision",
                "owned_fields",
            },
            "invalid_source_authority",
        )
        if data["contract_version"] != "source-authority.v1" or data["mode"] != "tracker-origin":
            raise RefreshRefusal("invalid_source_authority")
        owned = data["owned_fields"]
        acceptance = data.get("acceptance")
        if not isinstance(owned, dict) or len(owned) > 200:
            raise RefreshRefusal("invalid_source_authority")
        if any(
            not isinstance(key, str)
            or not key
            or len(key) > 200
            or value not in {"local", "source"}
            for key, value in owned.items()
        ):
            raise RefreshRefusal("invalid_source_authority")

        def closed_records(
            name: str,
            allowed: set[str],
            required: set[str],
        ) -> tuple[Mapping[str, object], ...]:
            raw = data.get(name, [])
            if not isinstance(raw, list) or len(raw) > 1000:
                raise RefreshRefusal("invalid_source_authority")
            records: list[Mapping[str, object]] = []
            for item in raw:
                if not isinstance(item, dict):
                    raise RefreshRefusal("invalid_source_authority")
                _require_exact_keys(
                    item, allowed, required, "invalid_source_authority"
                )
                records.append(dict(item))
            return tuple(records)

        decisions = closed_records(
            "source_decisions",
            {
                "source_revision",
                "field",
                "decision",
                "value_digest",
                "identity",
                "role",
                "decided_at",
                "authorization_source",
            },
            {
                "source_revision",
                "field",
                "decision",
                "identity",
                "role",
                "decided_at",
                "authorization_source",
            },
        )
        if any(item["decision"] not in _DECISIONS for item in decisions):
            raise RefreshRefusal("invalid_source_authority")
        for item in decisions:
            _bounded_string(item["source_revision"], 200, "invalid_source_authority")
            _bounded_string(item["field"], 200, "invalid_source_authority")
            _bounded_string(item["identity"], 200, "invalid_source_authority")
            _bounded_string(item["role"], 200, "invalid_source_authority")
            _timestamp(item["decided_at"], "invalid_source_authority")
            _bounded_string(
                item["authorization_source"], 200, "invalid_source_authority"
            )
            if "value_digest" in item:
                _digest(item["value_digest"], "invalid_source_authority")
        decision_keys = [
            (str(item["source_revision"]), str(item["field"]))
            for item in decisions
        ]
        if len(set(decision_keys)) != len(decision_keys):
            raise RefreshRefusal("invalid_source_authority")
        conflicts = closed_records(
            "conflicts",
            {"source_revision", "field", "status", "decision"},
            {"source_revision", "field", "status"},
        )
        if any(
            item["status"] not in {"unresolved", "resolved"}
            or ("decision" in item and item["decision"] not in _DECISIONS)
            for item in conflicts
        ):
            raise RefreshRefusal("invalid_source_authority")
        for item in conflicts:
            _bounded_string(item["source_revision"], 200, "invalid_source_authority")
            _bounded_string(item["field"], 200, "invalid_source_authority")
        conflict_keys = [
            (str(item["source_revision"]), str(item["field"]))
            for item in conflicts
        ]
        if len(set(conflict_keys)) != len(conflict_keys):
            raise RefreshRefusal("invalid_source_authority")
        local_receipts = closed_records(
            "local_receipts",
            {
                "update_id",
                "artifact_digest",
                "workspace_digest",
                "status",
                "recorded_at",
            },
            {
                "update_id",
                "artifact_digest",
                "workspace_digest",
                "status",
                "recorded_at",
            },
        )
        for item in local_receipts:
            _bounded_string(item["update_id"], 200, "invalid_source_authority")
            _digest(item["artifact_digest"], "invalid_source_authority")
            _digest(item["workspace_digest"], "invalid_source_authority")
            if item["status"] not in {"pending", "failed", "committed"}:
                raise RefreshRefusal("invalid_source_authority")
            _timestamp(item["recorded_at"], "invalid_source_authority")
        update_ids = [str(item["update_id"]) for item in local_receipts]
        if len(set(update_ids)) != len(update_ids):
            raise RefreshRefusal("invalid_source_authority")
        remote_actions = closed_records(
            "remote_actions",
            {
                "confirmation_id",
                "mutation_digest",
                "profile_version",
                "payload_digest",
                "identity",
                "role",
                "confirmed_at",
                "authorization_source",
                "action",
                "target",
                "status",
            },
            {
                "confirmation_id",
                "mutation_digest",
                "profile_version",
                "payload_digest",
                "identity",
                "role",
                "confirmed_at",
                "authorization_source",
                "action",
                "target",
                "status",
            },
        )
        for item in remote_actions:
            _bounded_string(item["confirmation_id"], 200, "invalid_source_authority")
            _digest(item["mutation_digest"], "invalid_source_authority")
            _bounded_string(item["profile_version"], 100, "invalid_source_authority")
            _digest(item["payload_digest"], "invalid_source_authority")
            _bounded_string(item["identity"], 200, "invalid_source_authority")
            _bounded_string(item["role"], 200, "invalid_source_authority")
            _timestamp(item["confirmed_at"], "invalid_source_authority")
            _bounded_string(
                item["authorization_source"], 200, "invalid_source_authority"
            )
            if item["action"] not in _REMOTE_ACTIONS or item["status"] not in {
                "pending",
                "failed",
                "succeeded",
            }:
                raise RefreshRefusal("invalid_source_authority")
            _bounded_string(item["target"], 1000, "invalid_source_authority")
        confirmation_ids = [str(item["confirmation_id"]) for item in remote_actions]
        if len(set(confirmation_ids)) != len(confirmation_ids):
            raise RefreshRefusal("invalid_source_authority")
        approval = None
        if acceptance is not None:
            if not isinstance(acceptance, dict):
                raise RefreshRefusal("invalid_source_authority")
            _require_exact_keys(
                acceptance, _APPROVAL_KEYS, _APPROVAL_KEYS, "invalid_source_authority"
            )
            approval = Approval(
                identity=_bounded_string(
                    acceptance["identity"], 200, "invalid_source_authority"
                ),
                role=_bounded_string(
                    acceptance["role"], 200, "invalid_source_authority"
                ),
                decided_at=_timestamp(
                    acceptance["decided_at"], "invalid_source_authority"
                ),
                authorization_source=_bounded_string(
                    acceptance["authorization_source"], 200, "invalid_source_authority"
                ),
            )
        return SourceAuthority(
            source_ref=_bounded_string(
                data["source_ref"], 1000, "invalid_source_authority"
            ),
            source_revision=_bounded_string(
                data["source_revision"], 200, "invalid_source_authority"
            ),
            accepted_revision=(
                _bounded_string(
                    data["accepted_revision"], 200, "invalid_source_authority"
                )
                if "accepted_revision" in data
                else None
            ),
            owned_fields=dict(owned),
            acceptance=approval,
            source_decisions=decisions,
            conflicts=conflicts,
            local_receipts=local_receipts,
            remote_actions=remote_actions,
        )
    except (KeyError, TypeError, tomllib.TOMLDecodeError) as exc:
        raise RefreshRefusal("invalid_source_authority") from exc


def _toml_string(value: object) -> str:
    """Render one validated string as a deterministic TOML basic string."""

    if not isinstance(value, str):
        raise RefreshRefusal("invalid_source_authority")
    if "\r" in value or "\n" in value:
        raise RefreshRefusal("invalid_source_authority")
    # TOML basic strings reject raw DEL; ASCII escapes preserve every Unicode
    # value while keeping the rendered authority record parseable.
    return json.dumps(value, ensure_ascii=True)


def _toml_key(value: str) -> str:
    """Render one mapping key without admitting TOML structure."""

    return value if re.fullmatch(r"[A-Za-z0-9_-]+", value) else _toml_string(value)


def render_source_authority(authority: SourceAuthority) -> str:
    """Render the closed authority object in one deterministic fenced form."""

    lines = [
        "```toml source-authority",
        'contract_version = "source-authority.v1"',
        f'mode = {_toml_string(authority.mode)}',
        f'source_ref = {_toml_string(authority.source_ref)}',
        f'source_revision = {_toml_string(authority.source_revision)}',
    ]
    if authority.accepted_revision is not None:
        lines.append(
            f'accepted_revision = {_toml_string(authority.accepted_revision)}'
        )

    record_orders = (
        (
            "source_decisions",
            authority.source_decisions,
            (
                "source_revision",
                "field",
                "decision",
                "value_digest",
                "identity",
                "role",
                "decided_at",
                "authorization_source",
            ),
        ),
        (
            "conflicts",
            authority.conflicts,
            ("source_revision", "field", "status", "decision"),
        ),
        (
            "local_receipts",
            authority.local_receipts,
            (
                "update_id",
                "artifact_digest",
                "workspace_digest",
                "status",
                "recorded_at",
            ),
        ),
        (
            "remote_actions",
            authority.remote_actions,
            (
                "confirmation_id",
                "mutation_digest",
                "profile_version",
                "payload_digest",
                "identity",
                "role",
                "confirmed_at",
                "authorization_source",
                "action",
                "target",
                "status",
            ),
        ),
    )
    for name, records, order in record_orders:
        for record in records:
            if set(record) - set(order):
                raise RefreshRefusal("invalid_source_authority")
            lines.extend(("", f"[[{name}]]"))
            lines.extend(
                f"{key} = {_toml_string(record[key])}"
                for key in order
                if key in record
            )

    lines.extend(("", "[owned_fields]"))
    lines.extend(
        f"{_toml_key(key)} = {_toml_string(value)}"
        for key, value in authority.owned_fields.items()
    )
    if authority.acceptance is not None:
        lines.extend(
            (
                "",
                "[acceptance]",
                f"identity = {_toml_string(authority.acceptance.identity)}",
                f"role = {_toml_string(authority.acceptance.role)}",
                f"decided_at = {_toml_string(authority.acceptance.decided_at)}",
                "authorization_source = "
                f"{_toml_string(authority.acceptance.authorization_source)}",
            )
        )
    rendered = "\n".join((*lines, "```", ""))
    if parse_source_authority(rendered) != authority:
        raise RefreshRefusal("invalid_source_authority")
    return rendered


def _replace_source_authority(markdown: str, authority: SourceAuthority) -> str:
    """Replace exactly one authority fence with trusted canonical bytes."""

    matches = list(_AUTHORITY_FENCE.finditer(markdown))
    if len(matches) != 1:
        raise RefreshRefusal("invalid_source_authority")
    match = matches[0]
    return markdown[: match.start()] + render_source_authority(authority) + markdown[match.end() :]


def parse_refresh_authorization_policy(text: str) -> RefreshAuthorizationPolicy:
    """Parse the role-only policy from a complete repository workspace file."""

    try:
        root = tomllib.loads(text)
        if not isinstance(root.get("authorization"), dict):
            raise RefreshRefusal("invalid_refresh_policy")
        authorization = root["authorization"]
        if not isinstance(authorization.get("refresh"), dict):
            raise RefreshRefusal("invalid_refresh_policy")
        policy = authorization["refresh"]
        _require_exact_keys(policy, _POLICY_KEYS, _POLICY_KEYS, "invalid_refresh_policy")
        if policy["contract_version"] != "refresh-authorization-policy.v1":
            raise RefreshRefusal("invalid_refresh_policy")

        def roles(name: str) -> tuple[str, ...]:
            value = policy[name]
            if (
                not isinstance(value, list)
                or not value
                or any(not isinstance(role, str) or not role.strip() for role in value)
                or len(set(value)) != len(value)
                or len(value) > 50
                or any(len(role) > 100 for role in value)
            ):
                raise RefreshRefusal("invalid_refresh_policy")
            return tuple(value)

        return RefreshAuthorizationPolicy(
            roles("draft_approver_roles"),
            roles("accepted_approver_roles"),
            roles("remote_mutation_approver_roles"),
        )
    except (KeyError, TypeError, tomllib.TOMLDecodeError) as exc:
        raise RefreshRefusal("invalid_refresh_policy") from exc


def confirmation_ledger(authority: SourceAuthority) -> set[str]:
    """Seed replay protection from every durable remote-action receipt."""

    return {
        str(action["confirmation_id"])
        for action in authority.remote_actions
    }


def evaluate_refresh(
    *,
    comparison: RefreshComparison,
    authority: SourceAuthority | None,
    policy: RefreshAuthorizationPolicy,
    approver: ApproverEvidence,
    decisions: Mapping[str, str],
    now: datetime | None = None,
) -> RefreshResult:
    """Apply the shared lifecycle and approval matrix without performing I/O."""

    if comparison.authority_mode == "repo-origin":
        return RefreshResult("projection_drift", "completed")
    if comparison.authority_mode != "tracker-origin" or authority is None:
        return RefreshResult("invalid_authority", "not-started", local_mutation="refused")
    if comparison.artifact_kind not in {"intent", "brief", "spec"}:
        return RefreshResult("unsupported_artifact_kind", "not-started", local_mutation="refused")
    if comparison.current_revision != authority.source_revision:
        return RefreshResult(
            "authority_revision_mismatch", "not-started", local_mutation="refused"
        )
    if comparison.lifecycle == "Shipped":
        return RefreshResult(
            "shipped_requirements_locked", "completed", local_mutation="refused"
        )
    if comparison.lifecycle == "Implementing":
        return RefreshResult(
            "implementing_requirements_locked", "completed", local_mutation="refused"
        )
    if comparison.lifecycle == "Executing":
        return RefreshResult(
            "executing_requirements_locked", "completed", local_mutation="refused"
        )
    if comparison.lifecycle == "Withdrawn":
        return RefreshResult(
            "withdrawn_requirements_locked", "completed", local_mutation="refused"
        )
    if comparison.lifecycle == "Cancelled":
        return RefreshResult(
            "cancelled_requirements_locked", "completed", local_mutation="refused"
        )
    if comparison.lifecycle in _DRAFT_LIFECYCLES | _ACCEPTED_LIFECYCLES:
        lifecycle_code = "ready"
    else:
        return RefreshResult(
            "unsupported_lifecycle", "not-started", local_mutation="refused"
        )

    allowed_roles = (
        policy.draft_approver_roles
        if comparison.lifecycle in _DRAFT_LIFECYCLES
        else policy.accepted_approver_roles
    )
    acceptance_matches = (
        comparison.lifecycle in _DRAFT_LIFECYCLES
        or (
            authority.acceptance is not None
            and approver.identity == authority.acceptance.identity
            and approver.role == authority.acceptance.role
        )
    )
    try:
        confirmed = datetime.fromisoformat(approver.confirmed_at.replace("Z", "+00:00"))
        checked_at = now or datetime.now(UTC)
        age = checked_at.astimezone(UTC) - confirmed.astimezone(UTC)
        approval_is_fresh = (
            confirmed.tzinfo is not None
            and timedelta(0) <= age <= timedelta(minutes=5)
        )
    except ValueError:
        approval_is_fresh = False
    if (
        approver.role not in allowed_roles
        or approver.authorization_source != "current-human-session"
        or not acceptance_matches
        or not approval_is_fresh
    ):
        return RefreshResult(
            "unauthorized_approver", "completed", local_mutation="refused"
        )

    changed_names = {change.name for change in comparison.changed_fields}
    if any(name not in authority.owned_fields for name in changed_names):
        return RefreshResult(
            "ownership_map_missing", "completed", local_mutation="refused"
        )
    if (
        len(changed_names) != len(comparison.changed_fields)
        or set(decisions) != changed_names
        or any(
        value not in _DECISIONS for value in decisions.values()
        )
    ):
        return RefreshResult("decision_required", "completed", local_mutation="refused")
    if comparison.lifecycle in _DRAFT_LIFECYCLES and any(
        authority.owned_fields[name] == "local" and decisions[name] != "keep-local"
        for name in changed_names
    ):
        return RefreshResult("local_field_locked", "completed", local_mutation="refused")
    if comparison.lifecycle in _ACCEPTED_LIFECYCLES and any(
        authority.owned_fields[name] != "local" for name in changed_names
    ):
        return RefreshResult(
            "accepted_field_not_local", "completed", local_mutation="refused"
        )
    updates = {
        change.name: change.source_value
        for change in comparison.changed_fields
        if decisions[change.name] == "accept-source"
    }
    conflict = (
        "requires_revision"
        if any(value == "revise-both" for value in decisions.values())
        else "none"
    )
    accepted_revision = (
        comparison.compared_revision
        if changed_names and all(value == "accept-source" for value in decisions.values())
        else authority.accepted_revision
    )
    decision_records = tuple(
        {
            "source_revision": comparison.compared_revision,
            "field": change.name,
            "decision": decisions[change.name],
            "identity": approver.identity,
            "role": approver.role,
            "decided_at": approver.confirmed_at,
            "authorization_source": approver.authorization_source,
        }
        for change in comparison.changed_fields
    )
    return RefreshResult(
        lifecycle_code,
        "completed",
        local_mutation="pending",
        conflict_state="unresolved" if conflict != "none" else "none",
        compared_revision=comparison.compared_revision,
        accepted_revision=accepted_revision,
        field_updates=updates,
        decision_records=decision_records,
    )


def failed_comparison(code: str = "comparison_failed") -> RefreshResult:
    """Return a no-effect failure that advances no source revision."""

    return RefreshResult(code, "failed", local_mutation="none")


def consume_remote_confirmation(
    *,
    confirmation: RemoteConfirmation,
    expected_binding: ConfirmationBinding,
    policy: RefreshAuthorizationPolicy,
    receipt_store: RemoteReceiptStore,
    used_confirmation_ids: set[str],
    now: datetime,
) -> RemoteActionReceipt:
    """Consume one fresh exact confirmation before one adapter mutation."""

    if (
        not isinstance(policy, RefreshAuthorizationPolicy)
        or not is_remote_receipt_store(receipt_store)
    ):
        raise RefreshRefusal("invalid_refresh_policy")
    try:
        workspace = _confined_existing_file(
            receipt_store.repository_root, "workspace.toml"
        )
        workspace_bytes = workspace.read_bytes()
        if digest_bytes(workspace_bytes) != receipt_store.workspace_digest:
            raise RefreshRefusal("invalid_refresh_policy")
        durable_policy = parse_refresh_authorization_policy(
            workspace_bytes.decode("utf-8")
        )
    except (OSError, UnicodeDecodeError, RefreshRefusal) as exc:
        raise RefreshRefusal("invalid_refresh_policy") from exc
    if durable_policy != policy:
        raise RefreshRefusal("invalid_refresh_policy")
    _bounded_string(confirmation.confirmation_id, 200, "invalid_confirmation")
    _bounded_string(confirmation.approver.identity, 200, "invalid_confirmation")
    _bounded_string(confirmation.approver.role, 200, "invalid_confirmation")
    _bounded_string(
        confirmation.binding.profile_version, 100, "invalid_confirmation"
    )
    if confirmation.confirmation_id in used_confirmation_ids:
        raise RefreshRefusal("confirmation_reused")
    if (
        confirmation.binding.action not in _REMOTE_ACTIONS
        or not re.fullmatch(r"[a-f0-9]{64}", confirmation.binding.payload_digest)
    ):
        raise RefreshRefusal("unsupported_remote_action")
    if confirmation.binding != expected_binding:
        raise RefreshRefusal("confirmation_binding_mismatch")
    if (
        confirmation.approver.role not in policy.remote_mutation_approver_roles
        or confirmation.approver.authorization_source != "current-human-session"
    ):
        raise RefreshRefusal("unauthorized_remote_mutation")
    try:
        approver_confirmed_at = datetime.fromisoformat(
            confirmation.approver.confirmed_at.replace("Z", "+00:00")
        )
    except ValueError as exc:
        raise RefreshRefusal("invalid_confirmation_time") from exc
    if (
        approver_confirmed_at.tzinfo is None
        or approver_confirmed_at.astimezone(UTC) != confirmation.confirmed_at
    ):
        raise RefreshRefusal("invalid_confirmation_time")
    if now.tzinfo is None:
        raise RefreshRefusal("invalid_confirmation_time")
    age = now.astimezone(UTC) - confirmation.confirmed_at
    if age < timedelta(0) or age > timedelta(minutes=5):
        raise RefreshRefusal("confirmation_stale")
    mutation_record = {
        "artifact_path": confirmation.binding.artifact_path,
        "source_revision": confirmation.binding.source_revision,
        "profile_id": confirmation.binding.profile_id,
        "profile_version": confirmation.binding.profile_version,
        "destination": confirmation.binding.destination,
        "action": confirmation.binding.action,
        "target": confirmation.binding.target,
        "payload_digest": confirmation.binding.payload_digest,
    }
    mutation_digest = digest_bytes(
        json.dumps(mutation_record, sort_keys=True, separators=(",", ":")).encode()
    )
    return RemoteActionReceipt(
        confirmation.confirmation_id,
        mutation_digest,
        confirmation.binding.profile_version,
        confirmation.binding.payload_digest,
        confirmation.approver.identity,
        confirmation.approver.role,
        confirmation.confirmed_at.isoformat().replace("+00:00", "Z"),
        confirmation.approver.authorization_source,
        confirmation.binding.action,
        confirmation.binding.target,
    )


_FORBIDDEN_V4 = tuple(
    ipaddress.ip_network(network)
    for network in (
        "0.0.0.0/8",
        "10.0.0.0/8",
        "100.64.0.0/10",
        "127.0.0.0/8",
        "169.254.0.0/16",
        "172.16.0.0/12",
        "192.168.0.0/16",
        "198.18.0.0/15",
        "224.0.0.0/4",
        "240.0.0.0/4",
    )
)
_FORBIDDEN_V6 = tuple(
    ipaddress.ip_network(network)
    for network in (
        "::/128",
        "::1/128",
        "100::/64",
        "fc00::/7",
        "fe80::/10",
        "ff00::/8",
    )
)


def _default_resolver(host: str) -> tuple[str, ...]:
    return tuple(
        sorted(
            {
                str(item[4][0])
                for item in socket.getaddrinfo(host, None, type=socket.SOCK_STREAM)
            }
        )
    )


def _address_is_forbidden(address: str) -> bool:
    try:
        parsed = ipaddress.ip_address(address)
    except ValueError as exc:
        raise RefreshRefusal("destination_forbidden") from exc
    networks = _FORBIDDEN_V4 if parsed.version == 4 else _FORBIDDEN_V6
    if isinstance(parsed, ipaddress.IPv6Address) and parsed.ipv4_mapped is not None:
        return any(parsed.ipv4_mapped in network for network in _FORBIDDEN_V4)
    if isinstance(parsed, ipaddress.IPv6Address):
        numeric = int(parsed)
        embedded_v4: list[ipaddress.IPv4Address] = []
        if parsed in ipaddress.ip_network("64:ff9b::/96"):
            embedded_v4.append(ipaddress.IPv4Address(numeric & 0xFFFFFFFF))
        if parsed in ipaddress.ip_network("2002::/16"):
            embedded_v4.append(ipaddress.IPv4Address((numeric >> 80) & 0xFFFFFFFF))
        if parsed in ipaddress.ip_network("2001::/32"):
            embedded_v4.extend(
                (
                    ipaddress.IPv4Address((numeric >> 64) & 0xFFFFFFFF),
                    ipaddress.IPv4Address((~numeric) & 0xFFFFFFFF),
                )
            )
        if any(
            candidate in network
            for candidate in embedded_v4
            for network in _FORBIDDEN_V4
        ):
            return True
    return any(parsed in network for network in networks)


def validate_destination(
    url: str,
    *,
    policy: DestinationPolicy,
    resolver: Callable[[str], Collection[str]] = _default_resolver,
) -> PinnedDestination:
    """Validate a trusted allowlist and pin safe DNS results for one request."""

    try:
        parts = urlsplit(url)
        scheme = parts.scheme.lower()
        host = (parts.hostname or "").lower().rstrip(".")
        port = parts.port or (443 if scheme == "https" else 80)
    except ValueError as exc:
        raise RefreshRefusal("destination_invalid") from exc
    if (
        not host
        or parts.username is not None
        or parts.password is not None
        or parts.fragment
        or (policy.credentials_attached and scheme != "https")
        or scheme not in policy.schemes
        or host not in {allowed.lower().rstrip(".") for allowed in policy.hosts}
        or port not in policy.ports
    ):
        raise RefreshRefusal("destination_not_allowed")
    try:
        addresses = tuple(dict.fromkeys(str(value) for value in resolver(host)))
    except (OSError, ValueError) as exc:
        raise RefreshRefusal("destination_resolution_failed") from exc
    if not addresses or any(_address_is_forbidden(address) for address in addresses):
        raise RefreshRefusal("destination_forbidden")
    return PinnedDestination(url, scheme, host, port, addresses)


def digest_bytes(value: bytes) -> str:
    """Return the SHA-256 guard digest for local mutation inputs."""

    return hashlib.sha256(value).hexdigest()


def canonical_payload_digest(payload: object) -> str:
    """Digest a JSON-compatible payload without logging or rendering it."""

    try:
        canonical = json.dumps(
            payload,
            allow_nan=False,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise RefreshRefusal("invalid_remote_payload") from exc
    return digest_bytes(canonical)


def _confined_existing_file(root: Path, relative: str) -> Path:
    candidate = Path(relative)
    if (
        candidate.is_absolute()
        or "\\" in relative
        or re.match(r"^[A-Za-z]:", relative)
        or any(part in {"", ".", ".."} for part in relative.split("/"))
    ):
        raise RefreshRefusal("invalid_target")
    lexical = root / candidate
    if lexical.is_symlink():
        raise RefreshRefusal("invalid_target")
    resolved_root = root.resolve(strict=True)
    resolved = lexical.resolve(strict=True)
    try:
        resolved.relative_to(resolved_root)
    except ValueError as exc:
        raise RefreshRefusal("invalid_target") from exc
    if not resolved.is_file():
        raise RefreshRefusal("invalid_target")
    return resolved


def guarded_write_pair(
    *,
    repository_root: Path,
    artifact_path: str,
    expected_artifact_digest: str,
    expected_workspace_digest: str,
    artifact_bytes: bytes,
    workspace_bytes: bytes,
) -> GuardedWriteResult:
    """Replace an artifact and workspace file under the shared workspace lock."""

    temp_paths: list[Path] = []
    artifact: Path | None = None
    workspace: Path | None = None
    lock_path: Path | None = None
    lock_fd = -1
    lock_acquired = False
    before_artifact = b""
    before_workspace = b""
    artifact_replaced = False
    workspace_replaced = False
    try:
        resolved_root = repository_root.resolve(strict=True)
        if not resolved_root.is_dir():
            raise RefreshRefusal("invalid_target")
        # Share the existing workspace writer's repository-scoped lock so its
        # fingerprint check and this two-file transaction cannot interleave.
        # The lock is acquired before target resolution and held through any
        # rollback and temporary-file cleanup.
        lock_path = resolved_root / ".workspace-repair.lock"
        try:
            lock_fd = os.open(str(lock_path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError:
            # Do not remove a stale-looking lock: its owner may still be
            # committing the paired files. Recovery requires an operator.
            print(f"work-intake refresh lock busy: {lock_path}", file=sys.stderr)
            return GuardedWriteResult("lock_busy")
        lock_acquired = True
        with suppress(OSError):
            os.write(lock_fd, str(os.getpid()).encode("ascii"))
        os.close(lock_fd)
        lock_fd = -1

        artifact = _confined_existing_file(resolved_root, artifact_path)
        workspace = _confined_existing_file(resolved_root, "workspace.toml")
        before_artifact = artifact.read_bytes()
        before_workspace = workspace.read_bytes()
        if (
            digest_bytes(before_artifact) != expected_artifact_digest
            or digest_bytes(before_workspace) != expected_workspace_digest
        ):
            return GuardedWriteResult("fingerprint_mismatch")

        def stage(path: Path, value: bytes) -> Path:
            descriptor, name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
            staged = Path(name)
            temp_paths.append(staged)
            with os.fdopen(descriptor, "wb") as handle:
                os.fchmod(handle.fileno(), path.stat().st_mode & 0o777)
                handle.write(value)
                handle.flush()
                os.fsync(handle.fileno())
            return staged

        staged_artifact = stage(artifact, artifact_bytes)
        staged_workspace = stage(workspace, workspace_bytes)

        # Authenticate both exact targets again after staging, immediately
        # before the first replacement. Cooperative writers are serialized by
        # the lock; this re-resolution also rejects a target swap by a writer
        # that ignored it.
        checked_artifact = _confined_existing_file(resolved_root, artifact_path)
        checked_workspace = _confined_existing_file(resolved_root, "workspace.toml")
        current_artifact = checked_artifact.read_bytes()
        current_workspace = checked_workspace.read_bytes()
        if (
            checked_artifact != artifact
            or checked_workspace != workspace
            or digest_bytes(current_artifact) != expected_artifact_digest
            or digest_bytes(current_workspace) != expected_workspace_digest
        ):
            return GuardedWriteResult("fingerprint_mismatch")
        staged_artifact.replace(artifact)
        artifact_replaced = True
        temp_paths.remove(staged_artifact)
        staged_workspace.replace(workspace)
        workspace_replaced = True
        temp_paths.remove(staged_workspace)
        return GuardedWriteResult("written")
    except RefreshRefusal:
        return GuardedWriteResult("invalid_target")
    except OSError:
        try:
            if artifact is not None and artifact_replaced:
                staged_artifact = stage(artifact, before_artifact)
                staged_artifact.replace(artifact)
                temp_paths.remove(staged_artifact)
            if workspace is not None and workspace_replaced:
                staged_workspace = stage(workspace, before_workspace)
                staged_workspace.replace(workspace)
                temp_paths.remove(staged_workspace)
        except OSError:
            # A failed rollback leaves the reviewed pair inconsistent.  Do
            # not report this as the recoverable, clean-rollback outcome.
            return GuardedWriteResult("local_write_inconsistent")
        return GuardedWriteResult("local_write_failed")
    finally:
        for path in temp_paths:
            with suppress(FileNotFoundError):
                path.unlink()
        if lock_fd >= 0:
            with suppress(OSError):
                os.close(lock_fd)
        if lock_path is not None and lock_acquired:
            with suppress(OSError):
                lock_path.unlink()


def _remote_receipt_record(receipt: RemoteActionReceipt) -> dict[str, object]:
    """Return the closed durable representation of one remote receipt."""

    return {
        "confirmation_id": receipt.confirmation_id,
        "mutation_digest": receipt.mutation_digest,
        "profile_version": receipt.profile_version,
        "payload_digest": receipt.payload_digest,
        "identity": receipt.identity,
        "role": receipt.role,
        "confirmed_at": receipt.confirmed_at,
        "authorization_source": receipt.authorization_source,
        "action": receipt.action,
        "target": receipt.target,
        "status": receipt.status,
    }


def write_remote_action_receipt(
    *,
    repository_root: Path,
    artifact_path: str,
    expected_artifact_digest: str,
    expected_workspace_digest: str,
    receipt: RemoteActionReceipt,
) -> RemoteReceiptWriteResult:
    """Durably append or terminally update one exact remote-action receipt."""

    try:
        resolved_root = repository_root.resolve(strict=True)
        artifact = _confined_existing_file(resolved_root, artifact_path)
        workspace = _confined_existing_file(resolved_root, "workspace.toml")
        current_artifact = artifact.read_bytes()
        current_workspace = workspace.read_bytes()
        if (
            digest_bytes(current_artifact) != expected_artifact_digest
            or digest_bytes(current_workspace) != expected_workspace_digest
        ):
            raise RefreshRefusal("fingerprint_mismatch")
        current_text = current_artifact.decode("utf-8")
        authority = parse_source_authority(current_text)
        record = _remote_receipt_record(receipt)
        # Round-trip through the closed parser before any local effect.
        probe = replace(authority, remote_actions=authority.remote_actions + (record,))
        if receipt.status == "pending":
            if any(
                existing.get("confirmation_id") == receipt.confirmation_id
                or (
                    existing.get("mutation_digest") == receipt.mutation_digest
                    and existing.get("status") != "failed"
                )
                for existing in authority.remote_actions
            ):
                raise RefreshRefusal("confirmation_reused")
            updated = probe
        elif receipt.status in {"failed", "succeeded"}:
            matches = [
                (index, existing)
                for index, existing in enumerate(authority.remote_actions)
                if existing.get("confirmation_id") == receipt.confirmation_id
            ]
            if len(matches) != 1:
                raise RefreshRefusal("receipt_not_pending")
            index, existing = matches[0]
            expected_pending = {**record, "status": "pending"}
            if dict(existing) != expected_pending:
                raise RefreshRefusal("receipt_not_pending")
            actions = list(authority.remote_actions)
            actions[index] = record
            updated = replace(authority, remote_actions=tuple(actions))
        else:
            raise RefreshRefusal("invalid_remote_receipt")
        updated_text = _replace_source_authority(current_text, updated)
        # The paired guard also authenticates an unchanged workspace fingerprint,
        # while the exact original workspace bytes are written back unchanged.
        result = guarded_write_pair(
            repository_root=resolved_root,
            artifact_path=artifact_path,
            expected_artifact_digest=expected_artifact_digest,
            expected_workspace_digest=expected_workspace_digest,
            artifact_bytes=updated_text.encode("utf-8"),
            workspace_bytes=current_workspace,
        )
        if result.code != "written":
            return RemoteReceiptWriteResult(result.code)
        return RemoteReceiptWriteResult(
            "written", digest_bytes(updated_text.encode("utf-8"))
        )
    except (
        OSError,
        UnicodeDecodeError,
        RefreshRefusal,
    ) as exc:
        code = str(exc) if isinstance(exc, RefreshRefusal) else "local_write_failed"
        return RemoteReceiptWriteResult(code)


@dataclass(slots=True)
class RemoteReceiptStore:
    """Concrete guarded artifact store required by every write-back processor."""

    _runtime_module: ClassVar[ModuleType]
    repository_root: Path
    artifact_path: str
    artifact_digest: str
    workspace_digest: str

    @classmethod
    def open(
        cls,
        *,
        repository_root: Path,
        artifact_path: str,
        expected_artifact_digest: str,
        expected_workspace_digest: str,
    ) -> RemoteReceiptStore:
        """Open only when both exact durable fingerprints are still current."""

        resolved_root = repository_root.resolve(strict=True)
        artifact = _confined_existing_file(resolved_root, artifact_path)
        workspace = _confined_existing_file(resolved_root, "workspace.toml")
        artifact_bytes = artifact.read_bytes()
        workspace_bytes = workspace.read_bytes()
        if (
            digest_bytes(artifact_bytes) != expected_artifact_digest
            or digest_bytes(workspace_bytes) != expected_workspace_digest
        ):
            raise RefreshRefusal("fingerprint_mismatch")
        parse_source_authority(artifact_bytes.decode("utf-8"))
        return cls(
            resolved_root,
            artifact_path,
            expected_artifact_digest,
            expected_workspace_digest,
        )

    def confirmation_ids(self) -> set[str]:
        """Reload the durable artifact ledger at the current fingerprint."""

        artifact = _confined_existing_file(self.repository_root, self.artifact_path)
        workspace = _confined_existing_file(self.repository_root, "workspace.toml")
        artifact_bytes = artifact.read_bytes()
        if (
            digest_bytes(artifact_bytes) != self.artifact_digest
            or digest_bytes(workspace.read_bytes()) != self.workspace_digest
        ):
            raise RefreshRefusal("fingerprint_mismatch")
        authority = parse_source_authority(artifact_bytes.decode("utf-8"))
        return confirmation_ledger(authority)

    def record(self, receipt: RemoteActionReceipt) -> None:
        """Persist one pending or terminal receipt and advance the fingerprint."""

        result = write_remote_action_receipt(
            repository_root=self.repository_root,
            artifact_path=self.artifact_path,
            expected_artifact_digest=self.artifact_digest,
            expected_workspace_digest=self.workspace_digest,
            receipt=receipt,
        )
        if result.code != "written" or result.artifact_digest is None:
            raise RefreshRefusal(result.code)
        self.artifact_digest = result.artifact_digest


_REMOTE_RECEIPT_STORE_MODULE = sys.modules[__name__]
RemoteReceiptStore._runtime_module = _REMOTE_RECEIPT_STORE_MODULE


def is_remote_receipt_store(value: object) -> bool:
    """Accept only the exact store implementation from this runtime file."""

    store_type = type(value)
    module = getattr(store_type, "_runtime_module", None)
    module_path = getattr(module, "__file__", None)
    try:
        return (
            isinstance(module_path, str)
            and Path(module_path).resolve(strict=True) == Path(__file__).resolve(strict=True)
            and store_type is getattr(module, "RemoteReceiptStore", None)
        )
    except OSError:
        return False


def _workspace_status_callable(name: str) -> Callable[..., tuple[object, list[object]]]:
    """Load one canonical contract callable from the installed core runtime."""

    candidate = (
        Path(__file__).resolve().parents[2]
        / "workspace-status"
        / "scripts"
        / "workspace_status_engine.py"
    )
    module: object
    if candidate.is_file():
        skills_root = Path(__file__).resolve().parents[2]
        try:
            candidate.resolve(strict=True).relative_to(skills_root.resolve(strict=True))
        except (OSError, ValueError) as exc:
            raise RefreshRefusal("invalid_local_update") from exc
        spec = importlib.util.spec_from_file_location(
            "_work_intake_workspace_status_runtime", candidate
        )
        if spec is None or spec.loader is None:
            raise RefreshRefusal("invalid_local_update")
        loaded = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = loaded
        try:
            spec.loader.exec_module(loaded)
        except Exception as exc:  # noqa: BLE001  # trusted bundled runtime boundary
            raise RefreshRefusal("invalid_local_update") from exc
        module = loaded
    else:
        try:
            module = importlib.import_module(
                "agentbundle._data.workspace_status_engine"
            )
        except (ImportError, OSError) as exc:
            raise RefreshRefusal("invalid_local_update") from exc
    parser = getattr(module, name, None)
    if not callable(parser):
        raise RefreshRefusal("invalid_local_update")
    return parser


def _intake_guard_callable(name: str) -> Callable[[str], str]:
    """Load the intake renderer's canonical redactor from this skill tree."""

    candidate = Path(__file__).resolve().with_name("intake_guard.py")
    try:
        candidate.resolve(strict=True).relative_to(Path(__file__).resolve().parent)
    except (OSError, ValueError) as exc:
        raise RefreshRefusal("invalid_local_update") from exc
    spec = importlib.util.spec_from_file_location(
        "_work_intake_guard_runtime", candidate
    )
    if spec is None or spec.loader is None:
        raise RefreshRefusal("invalid_local_update")
    loaded = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = loaded
    try:
        spec.loader.exec_module(loaded)
    except Exception as exc:  # noqa: BLE001  # trusted bundled runtime boundary
        raise RefreshRefusal("invalid_local_update") from exc
    redactor = getattr(loaded, name, None)
    if not callable(redactor):
        raise RefreshRefusal("invalid_local_update")
    return redactor


def _workspace_entry_parser() -> Callable[[object], tuple[object, list[object]]]:
    """Load the canonical Group 3 workspace-entry parser."""

    return _workspace_status_callable("parse_workspace_entry")


def _artifact_sections(
    markdown: str,
) -> tuple[
    str,
    tuple[tuple[str, int], ...],
    Mapping[tuple[str, int], tuple[str, str]],
]:
    """Split canonical level-two fields after removing validated metadata blocks."""

    body = _AUTHORITY_FENCE.sub("", markdown, count=1)
    body = _COORDINATION_FENCE.sub("", body)
    preamble: list[str] = []
    order: list[tuple[str, int]] = []
    sections: dict[tuple[str, int], tuple[str, str]] = {}
    current_name: str | None = None
    current_ordinal = 0
    current_heading = ""
    current_body: list[str] = []
    fence_character: str | None = None
    fence_width = 0

    def flush() -> None:
        if current_name is not None:
            sections[(current_name, current_ordinal)] = (
                current_heading,
                "".join(current_body),
            )

    for line in body.splitlines(keepends=True):
        fence = _FENCE_LINE.match(line)
        if fence is not None:
            marker = fence.group("fence")
            if fence_character is None:
                fence_character = marker[0]
                fence_width = len(marker)
            elif marker[0] == fence_character and len(marker) >= fence_width:
                fence_character = None
                fence_width = 0
        heading = _SECTION_HEADING.fullmatch(line) if fence_character is None else None
        if heading is not None:
            flush()
            name = heading.group("name")
            current_ordinal = sum(existing_name == name for existing_name, _ in order)
            order.append((name, current_ordinal))
            current_name = name
            current_heading = line
            current_body = []
        elif current_name is None:
            preamble.append(line)
        else:
            current_body.append(line)
    flush()
    return "".join(preamble), tuple(order), sections


def _authority_location(markdown: str, _match: re.Match[str]) -> tuple[str, int]:
    """Return the authority fence's containing section and fenced-block ordinal."""

    section = "<preamble>"
    fenced_blocks = 0
    opening_fence: str | None = None
    for line in markdown.splitlines(keepends=True):
        fence = _FENCE_LINE.match(line)
        if fence is not None:
            marker = fence.group("fence")
            if opening_fence is None:
                if _AUTHORITY_FENCE_OPENING.fullmatch(line) is not None:
                    return (section, fenced_blocks)
                fenced_blocks += 1
                opening_fence = marker
                continue
            if marker.startswith(opening_fence):
                opening_fence = None
                continue
        if opening_fence is None:
            heading = _SECTION_HEADING.fullmatch(line)
            if heading is not None:
                section = heading.group("name")
                fenced_blocks = 0
    raise RefreshRefusal("invalid_local_update")


def _validate_artifact_field_update(
    *,
    current_markdown: str,
    proposed_markdown: str,
    comparison: RefreshComparison,
    result: RefreshResult,
) -> None:
    """Refuse caller-supplied bytes that do not encode exactly the reviewed delta."""

    current_authority = list(_AUTHORITY_FENCE.finditer(current_markdown))
    proposed_authority = list(_AUTHORITY_FENCE.finditer(proposed_markdown))
    if (
        len(current_authority) != 1
        or len(proposed_authority) != 1
        or current_authority[0].group(0) != proposed_authority[0].group(0)
    ):
        raise RefreshRefusal("invalid_local_update")
    if _authority_location(current_markdown, current_authority[0]) != _authority_location(
        proposed_markdown, proposed_authority[0]
    ):
        raise RefreshRefusal("invalid_local_update")
    current_preamble, current_order, current_sections = _artifact_sections(
        current_markdown
    )
    proposed_preamble, proposed_order, proposed_sections = _artifact_sections(
        proposed_markdown
    )
    if current_preamble != proposed_preamble or current_order != proposed_order:
        raise RefreshRefusal("invalid_local_update")
    changes = {change.name: change for change in comparison.changed_fields}
    section_keys = {
        name: tuple(key for key in current_order if key[0] == name)
        for name in changes
    }
    if any(len(keys) != 1 for keys in section_keys.values()):
        raise RefreshRefusal("invalid_local_update")
    changes_by_key = {
        section_keys[name][0]: change for name, change in changes.items()
    }
    for key in current_order:
        current_heading, current_body = current_sections[key]
        proposed_heading, proposed_body = proposed_sections[key]
        if current_heading != proposed_heading:
            raise RefreshRefusal("invalid_local_update")
        change = changes_by_key.get(key)
        if change is None:
            if current_body != proposed_body:
                raise RefreshRefusal("invalid_local_update")
            continue
        expected = result.field_updates.get(key[0], change.local_value)
        if (
            current_body.strip() != change.local_value
            or proposed_body.strip() != expected
        ):
            raise RefreshRefusal("invalid_local_update")


def coordinate_local_refresh(
    *,
    repository_root: Path,
    comparison: RefreshComparison,
    authority: SourceAuthority,
    policy: RefreshAuthorizationPolicy,
    approver: ApproverEvidence,
    decisions: Mapping[str, str],
    expected_artifact_digest: str,
    expected_workspace_digest: str,
    artifact_bytes: bytes,
    workspace_bytes: bytes,
    now: datetime | None = None,
) -> RefreshResult:
    """Evaluate and durably commit one semantic local refresh transaction."""

    try:
        resolved_root = repository_root.resolve(strict=True)
        current_workspace_bytes = _confined_existing_file(
            resolved_root, "workspace.toml"
        ).read_bytes()
        if digest_bytes(current_workspace_bytes) != expected_workspace_digest:
            raise RefreshRefusal("invalid_local_update")
        configured_policy = parse_refresh_authorization_policy(
            current_workspace_bytes.decode("utf-8")
        )
        if configured_policy != policy:
            raise RefreshRefusal("invalid_refresh_policy")
    except RefreshRefusal as exc:
        code = (
            "invalid_refresh_policy"
            if str(exc) == "invalid_refresh_policy"
            else "invalid_local_update"
        )
        return RefreshResult(code, "not-started", local_mutation="refused")
    except (OSError, UnicodeDecodeError):
        return RefreshResult(
            "invalid_local_update", "not-started", local_mutation="refused"
        )

    result = evaluate_refresh(
        comparison=comparison,
        authority=authority,
        policy=configured_policy,
        approver=approver,
        decisions=decisions,
        now=now,
    )
    if result.local_mutation != "pending":
        return result
    try:
        current_artifact_bytes = _confined_existing_file(
            resolved_root, comparison.artifact_path
        ).read_bytes()
        if digest_bytes(current_artifact_bytes) != expected_artifact_digest:
            raise RefreshRefusal("invalid_local_update")
        current_artifact_text = current_artifact_bytes.decode("utf-8")
        proposed_artifact_text = artifact_bytes.decode("utf-8")
        current_authority = parse_source_authority(current_artifact_text)
        proposed_authority = parse_source_authority(proposed_artifact_text)
        if current_authority != authority or proposed_authority != current_authority:
            raise RefreshRefusal("invalid_local_update")
        _validate_artifact_field_update(
            current_markdown=current_artifact_text,
            proposed_markdown=proposed_artifact_text,
            comparison=comparison,
            result=result,
        )
        current_workspace_root = tomllib.loads(current_workspace_bytes.decode("utf-8"))
        proposed_workspace_root = tomllib.loads(workspace_bytes.decode("utf-8"))

        def matching_entry(root: object) -> Mapping[str, object]:
            entries: list[Mapping[str, object]] = []
            pending: list[object] = [root]
            visited = 0
            while pending:
                current = pending.pop()
                visited += 1
                if visited > 10_000:
                    raise RefreshRefusal("invalid_local_update")
                if isinstance(current, dict):
                    if current.get("path") == comparison.artifact_path:
                        entries.append(current)
                    pending.extend(current.values())
                elif isinstance(current, list):
                    pending.extend(current)
            if len(entries) != 1:
                raise RefreshRefusal("invalid_local_update")
            return entries[0]

        current_entry = matching_entry(current_workspace_root)
        entry = matching_entry(proposed_workspace_root)
        entry_parser = _workspace_entry_parser()
        parsed_current, current_findings = entry_parser(dict(current_entry))
        parsed_entry, entry_findings = entry_parser(dict(entry))
        if (
            parsed_current is None
            or current_findings
            or parsed_entry is None
            or entry_findings
        ):
            raise RefreshRefusal("invalid_local_update")
        current_source = current_entry.get("source")
        source = entry.get("source")
        if not isinstance(current_source, dict) or not isinstance(source, dict):
            raise RefreshRefusal("invalid_local_update")
        expected_workspace_root = copy.deepcopy(current_workspace_root)
        expected_entry = matching_entry(expected_workspace_root)
        expected_source = expected_entry.get("source")
        if not isinstance(expected_source, dict):
            raise RefreshRefusal("invalid_local_update")
        expected_source["revision"] = result.compared_revision
        if expected_workspace_root != proposed_workspace_root:
            raise RefreshRefusal("invalid_local_update")
        if comparison.current_revision == result.compared_revision:
            if current_workspace_bytes != workspace_bytes:
                raise RefreshRefusal("invalid_local_update")
        else:
            current_revision_bytes = comparison.current_revision.encode("utf-8")
            compared_revision_bytes = result.compared_revision.encode("utf-8")
            offsets: list[int] = []
            start = 0
            while len(offsets) <= 10_000:
                offset = current_workspace_bytes.find(current_revision_bytes, start)
                if offset < 0:
                    break
                offsets.append(offset)
                start = offset + 1
            if len(offsets) > 10_000:
                raise RefreshRefusal("invalid_local_update")
            matching_replacements = sum(
                current_workspace_bytes[:offset]
                + compared_revision_bytes
                + current_workspace_bytes[offset + len(current_revision_bytes) :]
                == workspace_bytes
                for offset in offsets
            )
            if matching_replacements != 1:
                raise RefreshRefusal("invalid_local_update")
        current_profile = current_source.get("tracker_profile")
        profile = source.get("tracker_profile")
        if not isinstance(current_profile, dict) or not isinstance(profile, dict):
            raise RefreshRefusal("invalid_local_update")
        current_source_without_revision = {
            key: value for key, value in current_source.items() if key != "revision"
        }
        proposed_source_without_revision = {
            key: value for key, value in source.items() if key != "revision"
        }
        if (
            (
                comparison.lifecycle in _ACCEPTED_LIFECYCLES
                and any(
                    authority.owned_fields[change.name] != "local"
                    for change in comparison.changed_fields
                )
            )
            or current_entry.get("kind") != comparison.artifact_kind
            or entry.get("kind") != current_entry.get("kind")
            or entry.get("summary") != current_entry.get("summary")
            or current_entry.get("needs") != entry.get("needs")
            or current_source.get("mode") != "tracker-origin"
            or current_source.get("ref") != authority.source_ref
            or current_source.get("revision") != comparison.current_revision
            or current_profile.get("id") != comparison.profile_id
            or current_profile.get("version") != comparison.profile_version
            or proposed_source_without_revision != current_source_without_revision
            or tuple(
                match.group("body")
                for match in _COORDINATION_FENCE.finditer(current_artifact_text)
            )
            != tuple(
                match.group("body")
                for match in _COORDINATION_FENCE.finditer(proposed_artifact_text)
            )
            or source.get("mode") != "tracker-origin"
            or source.get("ref") != authority.source_ref
            or source.get("revision") != result.compared_revision
            or profile.get("id") != comparison.profile_id
            or profile.get("version") != comparison.profile_version
        ):
            raise RefreshRefusal("invalid_local_update")

        expected_decisions = authority.source_decisions + tuple(
            dict(decision) for decision in result.decision_records
        )
        expected_conflicts = authority.conflicts + tuple(
            {
                "source_revision": decision["source_revision"],
                "field": decision["field"],
                "status": "unresolved",
            }
            for decision in result.decision_records
            if decision["decision"] == "revise-both"
        )
        update_binding = {
            "artifact_path": comparison.artifact_path,
            "current_revision": comparison.current_revision,
            "compared_revision": result.compared_revision,
            "artifact_digest": expected_artifact_digest,
            "workspace_digest": expected_workspace_digest,
            "recorded_at": approver.confirmed_at,
        }
        receipt = {
            "update_id": "refresh-"
            + digest_bytes(
                json.dumps(
                    update_binding, sort_keys=True, separators=(",", ":")
                ).encode("utf-8")
            ),
            "artifact_digest": expected_artifact_digest,
            "workspace_digest": expected_workspace_digest,
            "status": "committed",
            "recorded_at": approver.confirmed_at,
        }
        expected_authority = replace(
            authority,
            source_revision=result.compared_revision,
            accepted_revision=result.accepted_revision,
            source_decisions=expected_decisions,
            conflicts=expected_conflicts,
            local_receipts=authority.local_receipts + (receipt,),
        )
        committed_artifact_bytes = _replace_source_authority(
            proposed_artifact_text, expected_authority
        ).encode("utf-8")
    except (
        KeyError,
        OSError,
        TypeError,
        UnicodeDecodeError,
        tomllib.TOMLDecodeError,
        RefreshRefusal,
    ):
        return replace(result, code="invalid_local_update", local_mutation="refused")

    write_result = guarded_write_pair(
        repository_root=repository_root,
        artifact_path=comparison.artifact_path,
        expected_artifact_digest=expected_artifact_digest,
        expected_workspace_digest=expected_workspace_digest,
        artifact_bytes=committed_artifact_bytes,
        workspace_bytes=workspace_bytes,
    )
    if write_result.code != "written":
        local_mutation = (
            "inconsistent"
            if write_result.code == "local_write_inconsistent"
            else "refused"
        )
        return replace(
            result,
            code=write_result.code,
            local_mutation=local_mutation,
        )
    return replace(result, local_mutation="committed")
