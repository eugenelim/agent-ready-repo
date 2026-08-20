"""Deterministic routing seam for semantically classified work intake."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


class RefreshProcessor(Protocol):
    """Executable registration shape consumed by the intake front door."""

    name: str
    capabilities: frozenset[str]

    def acquire_map_compare(self, request: RefreshRequest) -> RefreshInvocation:
        """Acquire, map, validate, and compare one exact source revision."""


class RefreshRequest(Protocol):
    """Trusted local request fields checked before processor invocation."""

    artifact_path: str
    artifact_kind: str
    lifecycle: str
    authority_mode: str
    current_revision: str
    compared_revision: str
    profile_id: str
    profile_version: str


class RefreshInvocation(Protocol):
    """Redacted configured-processor result."""

    code: str
    processor: str


class RefreshProcessorResolver(Protocol):
    """Configured registry contract; tracker-specific behavior stays outside core."""

    def resolve(
        self,
        profile_id: str,
        profile_version: str,
        required_capability: str | None = None,
    ) -> RefreshProcessor:
        """Resolve an exact profile registration or fail closed."""


@dataclass(frozen=True)
class RoutingSignals:
    """Bounded semantic signals derived from a validated intake request."""

    action: str
    artifact: str
    artifact_kind: str
    authority_mode: str
    named_gaps: bool = False
    ready_brief: bool = False
    alias: str | None = None
    profile_id: str | None = None
    profile_version: str | None = None


@dataclass(frozen=True)
class Route:
    """Complete observable route selected for one intake request."""

    artifact: str
    artifact_kind: str
    lifecycle_membership: str
    processor: str
    authority_mode: str
    mutation: str


@dataclass(frozen=True)
class RefreshFrontDoorResult:
    """Public refresh delegation outcome with one stable next action."""

    route: Route
    code: str
    remediation: str
    invocation: RefreshInvocation | None = None


_START_ROUTES = {
    "intent": ("shaping_queue.backlog", "none"),
    "spec": ("work.queue", "new-spec"),
    "brief": ("brief_queue.draft", "author-brief"),
    "defect": ("backlog.open", "bug-fix"),
}


def route_intake(
    signals: RoutingSignals,
    refresh_processors: RefreshProcessorResolver | None = None,
) -> Route:
    """Map validated semantic signals to one deterministic intake route."""

    if signals.action == "status":
        return _route(signals, "passthrough", "workspace-status", "none")

    if signals.action == "refresh":
        processor = "none"
        if (
            refresh_processors is not None
            and signals.profile_id is not None
            and signals.profile_version is not None
        ):
            try:
                processor = refresh_processors.resolve(
                    signals.profile_id, signals.profile_version
                ).name
            except ValueError:
                # Missing and version-incompatible registrations share the stable,
                # no-effect refresh-unavailable route at this public front door.
                processor = "none"
        return _route(signals, "resolved-existing", processor, "none")

    if signals.ready_brief:
        if signals.artifact_kind != "brief":
            raise ValueError("only a brief can use the ready-brief route")
        return _route(signals, "brief_queue.ready", "receive-brief", "none")

    if signals.named_gaps:
        return _route(signals, "draft-with-gaps", "none", "ask-or-draft-only")

    if signals.action == "remember":
        mutation = (
            "same-as-work-intake-remember"
            if signals.alias == "capture-work"
            else "materialize-draft-and-register-non-dispatchable"
        )
        return _route(signals, "backlog.open", "none", mutation)

    if signals.action != "start" or signals.artifact_kind not in _START_ROUTES:
        raise ValueError("unsupported intake routing signals")

    membership, processor = _START_ROUTES[signals.artifact_kind]
    return _route(signals, membership, processor, "materialize-and-register")


def invoke_refresh(
    signals: RoutingSignals,
    refresh_processors: RefreshProcessorResolver,
    request: RefreshRequest,
) -> RefreshFrontDoorResult:
    """Resolve and invoke one configured refresh processor through work-intake."""

    if signals.action != "refresh":
        raise ValueError("refresh invocation requires refresh routing signals")
    route = route_intake(signals, refresh_processors)
    if (
        signals.profile_id is None
        or signals.profile_version is None
        or route.processor == "none"
    ):
        return RefreshFrontDoorResult(
            route,
            "refresh-unavailable",
            "configure-compatible-refresh-processor",
        )
    if (
        request.artifact_path != signals.artifact
        or request.artifact_kind != signals.artifact_kind
        or request.authority_mode != signals.authority_mode
        or request.profile_id != signals.profile_id
        or request.profile_version != signals.profile_version
    ):
        return RefreshFrontDoorResult(
            route,
            "invalid-refresh-request",
            "repair-refresh-request-profile",
        )
    try:
        processor = refresh_processors.resolve(
            signals.profile_id,
            signals.profile_version,
            "acquire",
        )
    except ValueError:
        return RefreshFrontDoorResult(
            _route(signals, "resolved-existing", "none", "none"),
            "refresh-unavailable",
            "configure-compatible-refresh-processor",
        )
    try:
        invocation = processor.acquire_map_compare(request)
    except (SystemExit, Exception):  # noqa: BLE001  # configured processor boundary
        return RefreshFrontDoorResult(
            route,
            "dispatch_failed",
            "retry-or-repair-configured-refresh-processor",
        )
    if invocation.code != "completed":
        return RefreshFrontDoorResult(
            route,
            invocation.code,
            "retry-or-repair-configured-refresh-processor",
            invocation,
        )
    comparison = getattr(invocation, "comparison", None)
    expected_comparison = (
        request.artifact_path,
        request.artifact_kind,
        request.lifecycle,
        request.authority_mode,
        request.current_revision,
        request.compared_revision,
        request.profile_id,
        request.profile_version,
    )
    actual_comparison = tuple(
        getattr(comparison, name, None)
        for name in (
            "artifact_path",
            "artifact_kind",
            "lifecycle",
            "authority_mode",
            "current_revision",
            "compared_revision",
            "profile_id",
            "profile_version",
        )
    )
    if comparison is None or actual_comparison != expected_comparison:
        return RefreshFrontDoorResult(
            route,
            "invalid-refresh-request",
            "repair-refresh-request-profile",
        )
    return RefreshFrontDoorResult(route, "completed", "none", invocation)


def _route(
    signals: RoutingSignals,
    membership: str,
    processor: str,
    mutation: str,
) -> Route:
    return Route(
        artifact=signals.artifact,
        artifact_kind=signals.artifact_kind,
        lifecycle_membership=membership,
        processor=processor,
        authority_mode=signals.authority_mode,
        mutation=mutation,
    )
