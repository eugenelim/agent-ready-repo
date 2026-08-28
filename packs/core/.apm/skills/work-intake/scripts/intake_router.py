"""Deterministic routing seam for semantically classified work intake."""

from __future__ import annotations

import importlib.util
import sys
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType
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
    direct_light: bool = False
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


@dataclass(frozen=True)
class HandoffSignals:
    """Trusted booleans derived after normalized-intake validation."""

    present: bool
    content_complete: bool
    source_matches: bool
    revision_matches: bool
    external_content_acquired: bool
    authority_mode: str
    named_gaps: bool = False
    confidentiality_allowed: bool = True
    mandatory_policy_conflict: bool = False


@dataclass(frozen=True)
class HandoffRoute:
    """Closed, zero-effect admission result for an optional handoff."""

    disposition: str
    semantic_role: str
    processor: str
    authority_mode: str
    next_action: str
    surface_resolution: object | None = None


_START_ROUTES = {
    "intent": ("shaping_queue.backlog", "intake-intent"),
    "spec": ("work.queue", "new-spec"),
    "brief": ("brief_queue.draft", "author-delivery-brief create"),
    "defect": ("backlog.open", "bug-fix"),
}


def route_intake(
    signals: RoutingSignals,
    refresh_processors: RefreshProcessorResolver | None = None,
) -> Route:
    """Map validated semantic signals to one deterministic intake route."""

    if signals.direct_light and (
        signals.action != "start"
        or signals.artifact != ""
        or signals.artifact_kind != ""
        or signals.named_gaps
        or signals.ready_brief
    ):
        raise ValueError("direct-light signals must not select a durable route")

    if signals.direct_light:
        return _route(signals, "none", "work-loop", "none")

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
        return _route(
            signals, "brief_queue.ready", "author-delivery-brief continue", "none"
        )

    if signals.named_gaps:
        return _route(signals, "draft-with-gaps", "none", "ask-or-draft-only")

    if signals.action == "remember":
        mutation = (
            "same-as-work-intake-remember"
            if signals.alias == "capture-work"
            else "materialize-draft-and-register-non-dispatchable"
        )
        processor = "intake-intent" if signals.artifact_kind == "intent" else "none"
        return _route(signals, "backlog.open", processor, mutation)

    if signals.action != "start" or signals.artifact_kind not in _START_ROUTES:
        raise ValueError("unsupported intake routing signals")

    membership, processor = _START_ROUTES[signals.artifact_kind]
    return _route(signals, membership, processor, "materialize-and-register")


def route_handoff(
    signals: HandoffSignals,
    surface_resolution: object | None,
) -> HandoffRoute:
    """Admit a validated Wave 1 result without materializing or dispatching."""

    if not _valid_handoff_signals(signals):
        return _handoff_route(
            signals,
            "refused",
            next_action="repair-handoff-signals",
        )
    if not signals.present:
        return _handoff_route(
            signals,
            "standalone",
            next_action="continue-standalone-classification",
        )
    if signals.named_gaps or not signals.content_complete:
        return _handoff_route(
            signals,
            "clarification-required",
            next_action="complete-bounded-handoff",
        )
    if not signals.confidentiality_allowed:
        return _handoff_route(
            signals,
            "refused",
            next_action="select-compatible-confidentiality",
        )
    if signals.mandatory_policy_conflict:
        return _handoff_route(
            signals,
            "refused",
            next_action="reconcile-mandatory-repository-policy",
        )
    if not signals.source_matches:
        return _handoff_route(
            signals,
            "refused",
            next_action="reconcile-handoff-source",
        )
    if not signals.revision_matches:
        return _handoff_route(
            signals,
            "refused",
            next_action="reconcile-handoff-revision",
        )

    resolver = _surface_resolver_module()
    try:
        if not isinstance(surface_resolution, resolver.SurfaceResolution):
            raise TypeError
        resolver.render_safe_result(surface_resolution)
    except (TypeError, ValueError):
        return _handoff_route(
            signals,
            "refused",
            next_action="repair-or-rerun-surface-resolution",
        )

    if surface_resolution.status != "resolved":
        disposition = (
            "clarification-required"
            if surface_resolution.status
            in {"confirmation-required", "destination-required"}
            else "refused"
        )
        return _handoff_route(
            signals,
            disposition,
            semantic_role=surface_resolution.role,
            next_action=surface_resolution.next_action
            or "repair-or-rerun-surface-resolution",
            surface_resolution=surface_resolution,
        )

    locator = surface_resolution.physical_locator
    if (
        surface_resolution.role not in {"delivery-brief", "delivery-contract"}
        or locator is None
        or surface_resolution.revision_or_fingerprint is None
    ):
        return _handoff_route(
            signals,
            "refused",
            next_action="repair-or-rerun-surface-resolution",
        )
    if locator.kind == "external" and not signals.external_content_acquired:
        return _handoff_route(
            signals,
            "refused",
            semantic_role=surface_resolution.role,
            next_action="supply-acquired-external-content",
            surface_resolution=surface_resolution,
        )

    if surface_resolution.role == "delivery-brief":
        mode = "continue" if locator.kind == "repository-path" else "create"
        processor = f"author-delivery-brief {mode}"
    else:
        processor = "new-spec"
    return _handoff_route(
        signals,
        "reuse",
        semantic_role=surface_resolution.role,
        processor=processor,
        next_action=processor,
        surface_resolution=surface_resolution,
    )


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


def _valid_handoff_signals(signals: object) -> bool:
    """Validate the closed trusted-signal shape without raising."""

    if not isinstance(signals, HandoffSignals):
        return False
    booleans = (
        signals.present,
        signals.content_complete,
        signals.source_matches,
        signals.revision_matches,
        signals.external_content_acquired,
        signals.named_gaps,
        signals.confidentiality_allowed,
        signals.mandatory_policy_conflict,
    )
    return all(isinstance(value, bool) for value in booleans) and (
        signals.authority_mode in {"repo-origin", "tracker-origin"}
    )


def _handoff_route(
    signals: object,
    disposition: str,
    *,
    semantic_role: str = "none",
    processor: str = "none",
    next_action: str,
    surface_resolution: object | None = None,
) -> HandoffRoute:
    """Construct one stable result without reflecting untrusted content."""

    authority_mode = getattr(signals, "authority_mode", "unknown")
    if authority_mode not in {"repo-origin", "tracker-origin"}:
        authority_mode = "unknown"
    return HandoffRoute(
        disposition=disposition,
        semantic_role=semantic_role,
        processor=processor,
        authority_mode=authority_mode,
        next_action=next_action,
        surface_resolution=surface_resolution,
    )


def _surface_resolver_module() -> ModuleType:
    """Load the sibling resolver once under a collision-proof module name."""

    module_name = "core_work_intake_surface_resolver"
    loaded = sys.modules.get(module_name)
    if loaded is not None:
        return loaded
    module_path = Path(__file__).resolve().with_name("surface_resolver.py")
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("surface resolver cannot be loaded")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module
