"""Pin the router's registration-stop routes against the pre-change routes."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from typing import Any

import pytest

_ROUTER_PATH = (
    Path(__file__).resolve().parents[3]
    / ".apm"
    / "skills"
    / "work-intake"
    / "scripts"
    / "intake_router.py"
)


def _load_router() -> Any:
    name = "intake_router_registration_stop"
    spec = importlib.util.spec_from_file_location(name, _ROUTER_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _signals(action: str, kind: str, authority: str = "repo-origin") -> dict[str, Any]:
    return {
        "action": action,
        "artifact": f"docs/product/captured/{kind}-item.md",
        "artifact_kind": kind,
        "authority_mode": authority,
    }


def _route_tuple(route: Any) -> tuple[str, ...]:
    return (
        route.artifact,
        route.artifact_kind,
        route.lifecycle_membership,
        route.processor,
        route.authority_mode,
        route.mutation,
    )


@pytest.mark.parametrize("kind", ["defect", "design", "research"])
def test_remember_of_captured_kinds_registers_nothing(kind: str) -> None:
    router = _load_router()
    route = router.route_intake(router.RoutingSignals(**_signals("remember", kind)))
    assert route.lifecycle_membership == "none"
    assert route.mutation == "materialize-draft-non-dispatchable"
    assert "register" not in route.mutation
    assert route.processor == "none"


def test_start_defect_dispatches_bug_fix_without_registration() -> None:
    router = _load_router()
    route = router.route_intake(router.RoutingSignals(**_signals("start", "defect")))
    assert route.lifecycle_membership == "none"
    assert route.processor == "bug-fix"
    assert route.mutation == "materialize-and-dispatch"


# Routes the router returned at ff33d0dcc, recorded once as literals:
# (artifact, artifact_kind, lifecycle_membership, processor, authority_mode, mutation).
_UNCHANGED = [
    ('direct-light', {'action': 'start', 'artifact': '', 'artifact_kind': '', 'authority_mode': 'repo-origin', 'direct_light': True}, ('', '', 'none', 'work-loop', 'repo-origin', 'none')),
    ('remember-spec', {'action': 'remember', 'artifact': 'docs/specs/later/spec.md', 'artifact_kind': 'spec', 'authority_mode': 'repo-origin'}, ('docs/specs/later/spec.md', 'spec', 'backlog.open', 'none', 'repo-origin', 'materialize-draft-and-register-non-dispatchable')),
    ('status-passthrough', {'action': 'status', 'artifact': 'workspace.toml', 'artifact_kind': 'workspace-status', 'authority_mode': 'read-only'}, ('workspace.toml', 'workspace-status', 'passthrough', 'workspace-status', 'read-only', 'none')),
    ('refresh-unavailable', {'action': 'refresh', 'artifact': 'docs/specs/example/spec.md', 'artifact_kind': 'spec', 'authority_mode': 'repo-origin'}, ('docs/specs/example/spec.md', 'spec', 'resolved-existing', 'none', 'repo-origin', 'none')),
    ('ambiguity', {'action': 'start', 'artifact': 'docs/product/intents/work-intake.md', 'artifact_kind': 'intent', 'authority_mode': 'repo-origin', 'named_gaps': True}, ('docs/product/intents/work-intake.md', 'intent', 'draft-with-gaps', 'none', 'repo-origin', 'ask-or-draft-only')),
    ('direct-spec', {'action': 'start', 'artifact': 'docs/specs/export-retention/spec.md', 'artifact_kind': 'spec', 'authority_mode': 'tracker-origin'}, ('docs/specs/export-retention/spec.md', 'spec', 'work.queue', 'new-spec', 'tracker-origin', 'materialize-and-register')),
    ('multi-spec-brief', {'action': 'start', 'artifact': 'docs/product/briefs/account-recovery.md', 'artifact_kind': 'brief', 'authority_mode': 'tracker-origin'}, ('docs/product/briefs/account-recovery.md', 'brief', 'brief_queue.draft', 'author-delivery-brief create', 'tracker-origin', 'materialize-and-register')),
    ('incoherent-collection', {'action': 'start', 'artifact': 'docs/product/intents/board-selection.md', 'artifact_kind': 'intent', 'authority_mode': 'tracker-origin', 'named_gaps': True}, ('docs/product/intents/board-selection.md', 'intent', 'draft-with-gaps', 'none', 'tracker-origin', 'ask-or-draft-only')),
    ('claimed-defect-without-evidence', {'action': 'start', 'artifact': 'docs/specs/login-investigation/spec.md', 'artifact_kind': 'spec', 'authority_mode': 'tracker-origin', 'named_gaps': True}, ('docs/specs/login-investigation/spec.md', 'spec', 'draft-with-gaps', 'none', 'tracker-origin', 'ask-or-draft-only')),
]


@pytest.mark.parametrize(("case_id", "signals", "expected"), _UNCHANGED, ids=[c[0] for c in _UNCHANGED])
def test_every_other_route_matches_the_pre_change_route(
    case_id: str, signals: dict[str, Any], expected: tuple[str, ...]
) -> None:
    router = _load_router()
    assert _route_tuple(router.route_intake(router.RoutingSignals(**signals))) == expected


# Repo-origin intent and brief routes that no longer register (AC-0013).
_STOPPED = [
    ('start-intent', {'action': 'start', 'artifact': 'docs/product/intents/workspace-routing.md', 'artifact_kind': 'intent', 'authority_mode': 'repo-origin'}, ('docs/product/intents/workspace-routing.md', 'intent', 'none', 'intake-intent', 'repo-origin', 'materialize-and-dispatch')),
    ('start-brief', {'action': 'start', 'artifact': 'docs/product/briefs/new.md', 'artifact_kind': 'brief', 'authority_mode': 'repo-origin'}, ('docs/product/briefs/new.md', 'brief', 'none', 'author-delivery-brief create', 'repo-origin', 'materialize-and-dispatch')),
    ('remember-intent', {'action': 'remember', 'artifact': 'docs/product/intents/deferred-work.md', 'artifact_kind': 'intent', 'authority_mode': 'repo-origin'}, ('docs/product/intents/deferred-work.md', 'intent', 'none', 'intake-intent', 'repo-origin', 'materialize-draft-non-dispatchable')),
    ('remember-brief', {'action': 'remember', 'artifact': 'docs/product/briefs/later.md', 'artifact_kind': 'brief', 'authority_mode': 'repo-origin'}, ('docs/product/briefs/later.md', 'brief', 'none', 'none', 'repo-origin', 'materialize-draft-non-dispatchable')),
    ('ready-brief', {'action': 'start', 'artifact': 'docs/product/briefs/ready-without-specs.md', 'artifact_kind': 'brief', 'authority_mode': 'repo-origin', 'ready_brief': True}, ('docs/product/briefs/ready-without-specs.md', 'brief', 'none', 'author-delivery-brief continue', 'repo-origin', 'none')),
]


@pytest.mark.parametrize(("case_id", "signals", "expected"), _STOPPED, ids=[c[0] for c in _STOPPED])
def test_repo_origin_intent_and_brief_routes_register_nothing(
    case_id: str, signals: dict[str, Any], expected: tuple[str, ...]
) -> None:
    router = _load_router()
    route = router.route_intake(router.RoutingSignals(**signals))
    assert _route_tuple(route) == expected
    assert "register" not in route.mutation


def _outcome(router: Any, signals: dict[str, Any]) -> Any:
    try:
        return _route_tuple(router.route_intake(router.RoutingSignals(**signals)))
    except ValueError:
        return "ValueError"


# Tracker-origin start, remember, and ready-brief signals of each kind, as
# returned at ff33d0dcc (AC-0014); "ValueError" marks a refused signal shape.
_TRACKER_ORIGIN = [
    ('tracker-start-intent', {'action': 'start', 'artifact': 'docs/product/captured/intent-item.md', 'artifact_kind': 'intent', 'authority_mode': 'tracker-origin'}, ('docs/product/captured/intent-item.md', 'intent', 'shaping_queue.backlog', 'intake-intent', 'tracker-origin', 'materialize-and-register')),
    ('tracker-remember-intent', {'action': 'remember', 'artifact': 'docs/product/captured/intent-item.md', 'artifact_kind': 'intent', 'authority_mode': 'tracker-origin'}, ('docs/product/captured/intent-item.md', 'intent', 'backlog.open', 'intake-intent', 'tracker-origin', 'materialize-draft-and-register-non-dispatchable')),
    ('tracker-ready-brief-intent', {'action': 'start', 'ready_brief': True, 'artifact': 'docs/product/captured/intent-item.md', 'artifact_kind': 'intent', 'authority_mode': 'tracker-origin'}, 'ValueError'),
    ('tracker-start-brief', {'action': 'start', 'artifact': 'docs/product/captured/brief-item.md', 'artifact_kind': 'brief', 'authority_mode': 'tracker-origin'}, ('docs/product/captured/brief-item.md', 'brief', 'brief_queue.draft', 'author-delivery-brief create', 'tracker-origin', 'materialize-and-register')),
    ('tracker-remember-brief', {'action': 'remember', 'artifact': 'docs/product/captured/brief-item.md', 'artifact_kind': 'brief', 'authority_mode': 'tracker-origin'}, ('docs/product/captured/brief-item.md', 'brief', 'backlog.open', 'none', 'tracker-origin', 'materialize-draft-and-register-non-dispatchable')),
    ('tracker-ready-brief-brief', {'action': 'start', 'ready_brief': True, 'artifact': 'docs/product/captured/brief-item.md', 'artifact_kind': 'brief', 'authority_mode': 'tracker-origin'}, ('docs/product/captured/brief-item.md', 'brief', 'brief_queue.ready', 'author-delivery-brief continue', 'tracker-origin', 'none')),
    ('tracker-start-spec', {'action': 'start', 'artifact': 'docs/product/captured/spec-item.md', 'artifact_kind': 'spec', 'authority_mode': 'tracker-origin'}, ('docs/product/captured/spec-item.md', 'spec', 'work.queue', 'new-spec', 'tracker-origin', 'materialize-and-register')),
    ('tracker-remember-spec', {'action': 'remember', 'artifact': 'docs/product/captured/spec-item.md', 'artifact_kind': 'spec', 'authority_mode': 'tracker-origin'}, ('docs/product/captured/spec-item.md', 'spec', 'backlog.open', 'none', 'tracker-origin', 'materialize-draft-and-register-non-dispatchable')),
    ('tracker-ready-brief-spec', {'action': 'start', 'ready_brief': True, 'artifact': 'docs/product/captured/spec-item.md', 'artifact_kind': 'spec', 'authority_mode': 'tracker-origin'}, 'ValueError'),
    ('tracker-start-defect', {'action': 'start', 'artifact': 'docs/product/captured/defect-item.md', 'artifact_kind': 'defect', 'authority_mode': 'tracker-origin'}, ('docs/product/captured/defect-item.md', 'defect', 'none', 'bug-fix', 'tracker-origin', 'materialize-and-dispatch')),
    ('tracker-remember-defect', {'action': 'remember', 'artifact': 'docs/product/captured/defect-item.md', 'artifact_kind': 'defect', 'authority_mode': 'tracker-origin'}, ('docs/product/captured/defect-item.md', 'defect', 'none', 'none', 'tracker-origin', 'materialize-draft-non-dispatchable')),
    ('tracker-ready-brief-defect', {'action': 'start', 'ready_brief': True, 'artifact': 'docs/product/captured/defect-item.md', 'artifact_kind': 'defect', 'authority_mode': 'tracker-origin'}, 'ValueError'),
    ('tracker-start-design', {'action': 'start', 'artifact': 'docs/product/captured/design-item.md', 'artifact_kind': 'design', 'authority_mode': 'tracker-origin'}, 'ValueError'),
    ('tracker-remember-design', {'action': 'remember', 'artifact': 'docs/product/captured/design-item.md', 'artifact_kind': 'design', 'authority_mode': 'tracker-origin'}, ('docs/product/captured/design-item.md', 'design', 'none', 'none', 'tracker-origin', 'materialize-draft-non-dispatchable')),
    ('tracker-ready-brief-design', {'action': 'start', 'ready_brief': True, 'artifact': 'docs/product/captured/design-item.md', 'artifact_kind': 'design', 'authority_mode': 'tracker-origin'}, 'ValueError'),
    ('tracker-start-research', {'action': 'start', 'artifact': 'docs/product/captured/research-item.md', 'artifact_kind': 'research', 'authority_mode': 'tracker-origin'}, 'ValueError'),
    ('tracker-remember-research', {'action': 'remember', 'artifact': 'docs/product/captured/research-item.md', 'artifact_kind': 'research', 'authority_mode': 'tracker-origin'}, ('docs/product/captured/research-item.md', 'research', 'none', 'none', 'tracker-origin', 'materialize-draft-non-dispatchable')),
    ('tracker-ready-brief-research', {'action': 'start', 'ready_brief': True, 'artifact': 'docs/product/captured/research-item.md', 'artifact_kind': 'research', 'authority_mode': 'tracker-origin'}, 'ValueError'),
]


@pytest.mark.parametrize(("case_id", "signals", "expected"), _TRACKER_ORIGIN, ids=[c[0] for c in _TRACKER_ORIGIN])
def test_tracker_origin_routes_match_the_pre_change_route(
    case_id: str, signals: dict[str, Any], expected: Any
) -> None:
    router = _load_router()
    assert _outcome(router, signals) == expected
