"""Deterministic routing seam for semantically classified work intake."""

from __future__ import annotations

from dataclasses import dataclass


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


@dataclass(frozen=True)
class Route:
    """Complete observable route selected for one intake request."""

    artifact: str
    artifact_kind: str
    lifecycle_membership: str
    processor: str
    authority_mode: str
    mutation: str


_START_ROUTES = {
    "intent": ("shaping_queue.backlog", "none"),
    "spec": ("work.queue", "new-spec"),
    "brief": ("brief_queue.draft", "author-brief"),
    "defect": ("backlog.open", "bug-fix"),
}


def route_intake(signals: RoutingSignals) -> Route:
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
        processor = _START_ROUTES.get(signals.artifact_kind, ("", "none"))[1]
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
