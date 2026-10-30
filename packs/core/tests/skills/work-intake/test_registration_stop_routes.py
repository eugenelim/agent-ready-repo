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


# Routes recorded once as literals, with the tracker-origin rows updated for the
# registration stop:
# (artifact, artifact_kind, lifecycle_membership, processor, authority_mode, mutation).
_UNCHANGED = [
    ('direct-light', {'action': 'start', 'artifact': '', 'artifact_kind': '', 'authority_mode': 'repo-origin', 'direct_light': True}, ('', '', 'none', 'work-loop', 'repo-origin', 'none')),
    ('status-passthrough', {'action': 'status', 'artifact': 'workspace.toml', 'artifact_kind': 'workspace-status', 'authority_mode': 'read-only'}, ('workspace.toml', 'workspace-status', 'passthrough', 'workspace-status', 'read-only', 'none')),
    ('refresh-unavailable', {'action': 'refresh', 'artifact': 'docs/specs/example/spec.md', 'artifact_kind': 'spec', 'authority_mode': 'repo-origin'}, ('docs/specs/example/spec.md', 'spec', 'resolved-existing', 'none', 'repo-origin', 'none')),
    ('ambiguity', {'action': 'start', 'artifact': 'docs/product/intents/work-intake.md', 'artifact_kind': 'intent', 'authority_mode': 'repo-origin', 'named_gaps': True}, ('docs/product/intents/work-intake.md', 'intent', 'draft-with-gaps', 'none', 'repo-origin', 'ask-or-draft-only')),
    ('direct-spec', {'action': 'start', 'artifact': 'docs/specs/export-retention/spec.md', 'artifact_kind': 'spec', 'authority_mode': 'tracker-origin'}, ('docs/specs/export-retention/spec.md', 'spec', 'none', 'new-spec', 'tracker-origin', 'materialize-and-dispatch')),
    ('multi-spec-brief', {'action': 'start', 'artifact': 'docs/product/briefs/account-recovery.md', 'artifact_kind': 'brief', 'authority_mode': 'tracker-origin'}, ('docs/product/briefs/account-recovery.md', 'brief', 'none', 'author-delivery-brief create', 'tracker-origin', 'materialize-and-dispatch')),
    ('incoherent-collection', {'action': 'start', 'artifact': 'docs/product/intents/board-selection.md', 'artifact_kind': 'intent', 'authority_mode': 'tracker-origin', 'named_gaps': True}, ('docs/product/intents/board-selection.md', 'intent', 'draft-with-gaps', 'none', 'tracker-origin', 'ask-or-draft-only')),
    ('claimed-defect-without-evidence', {'action': 'start', 'artifact': 'docs/specs/login-investigation/spec.md', 'artifact_kind': 'spec', 'authority_mode': 'tracker-origin', 'named_gaps': True}, ('docs/specs/login-investigation/spec.md', 'spec', 'draft-with-gaps', 'none', 'tracker-origin', 'ask-or-draft-only')),
]


@pytest.mark.parametrize(("case_id", "signals", "expected"), _UNCHANGED, ids=[c[0] for c in _UNCHANGED])
def test_every_other_route_matches_its_recorded_route(
    case_id: str, signals: dict[str, Any], expected: tuple[str, ...]
) -> None:
    router = _load_router()
    assert _route_tuple(router.route_intake(router.RoutingSignals(**signals))) == expected


# Repo-origin intent, brief, and spec routes that no longer register (AC-0013).
_STOPPED = [
    ('start-intent', {'action': 'start', 'artifact': 'docs/product/intents/workspace-routing.md', 'artifact_kind': 'intent', 'authority_mode': 'repo-origin'}, ('docs/product/intents/workspace-routing.md', 'intent', 'none', 'intake-intent', 'repo-origin', 'materialize-and-dispatch')),
    ('start-brief', {'action': 'start', 'artifact': 'docs/product/briefs/new.md', 'artifact_kind': 'brief', 'authority_mode': 'repo-origin'}, ('docs/product/briefs/new.md', 'brief', 'none', 'author-delivery-brief create', 'repo-origin', 'materialize-and-dispatch')),
    ('remember-intent', {'action': 'remember', 'artifact': 'docs/product/intents/deferred-work.md', 'artifact_kind': 'intent', 'authority_mode': 'repo-origin'}, ('docs/product/intents/deferred-work.md', 'intent', 'none', 'intake-intent', 'repo-origin', 'materialize-draft-non-dispatchable')),
    ('remember-brief', {'action': 'remember', 'artifact': 'docs/product/briefs/later.md', 'artifact_kind': 'brief', 'authority_mode': 'repo-origin'}, ('docs/product/briefs/later.md', 'brief', 'none', 'none', 'repo-origin', 'materialize-draft-non-dispatchable')),
    ('start-repo-origin-spec', {'action': 'start', 'artifact': 'docs/specs/new/spec.md', 'artifact_kind': 'spec', 'authority_mode': 'repo-origin'}, ('docs/specs/new/spec.md', 'spec', 'none', 'new-spec', 'repo-origin', 'materialize-and-dispatch')),
    ('remember-spec', {'action': 'remember', 'artifact': 'docs/specs/later/spec.md', 'artifact_kind': 'spec', 'authority_mode': 'repo-origin'}, ('docs/specs/later/spec.md', 'spec', 'none', 'none', 'repo-origin', 'materialize-draft-non-dispatchable')),
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
# compared with the repo-origin route of the same signal (AC-0009).
_TRACKER_ORIGIN = [
    ('tracker-start-intent', {'action': 'start', 'artifact': 'docs/product/captured/intent-item.md', 'artifact_kind': 'intent', 'authority_mode': 'tracker-origin'}),
    ('tracker-remember-intent', {'action': 'remember', 'artifact': 'docs/product/captured/intent-item.md', 'artifact_kind': 'intent', 'authority_mode': 'tracker-origin'}),
    ('tracker-ready-brief-intent', {'action': 'start', 'ready_brief': True, 'artifact': 'docs/product/captured/intent-item.md', 'artifact_kind': 'intent', 'authority_mode': 'tracker-origin'}),
    ('tracker-start-brief', {'action': 'start', 'artifact': 'docs/product/captured/brief-item.md', 'artifact_kind': 'brief', 'authority_mode': 'tracker-origin'}),
    ('tracker-remember-brief', {'action': 'remember', 'artifact': 'docs/product/captured/brief-item.md', 'artifact_kind': 'brief', 'authority_mode': 'tracker-origin'}),
    ('tracker-ready-brief-brief', {'action': 'start', 'ready_brief': True, 'artifact': 'docs/product/captured/brief-item.md', 'artifact_kind': 'brief', 'authority_mode': 'tracker-origin'}),
    ('tracker-start-spec', {'action': 'start', 'artifact': 'docs/product/captured/spec-item.md', 'artifact_kind': 'spec', 'authority_mode': 'tracker-origin'}),
    ('tracker-remember-spec', {'action': 'remember', 'artifact': 'docs/product/captured/spec-item.md', 'artifact_kind': 'spec', 'authority_mode': 'tracker-origin'}),
    ('tracker-ready-brief-spec', {'action': 'start', 'ready_brief': True, 'artifact': 'docs/product/captured/spec-item.md', 'artifact_kind': 'spec', 'authority_mode': 'tracker-origin'}),
    ('tracker-start-defect', {'action': 'start', 'artifact': 'docs/product/captured/defect-item.md', 'artifact_kind': 'defect', 'authority_mode': 'tracker-origin'}),
    ('tracker-remember-defect', {'action': 'remember', 'artifact': 'docs/product/captured/defect-item.md', 'artifact_kind': 'defect', 'authority_mode': 'tracker-origin'}),
    ('tracker-ready-brief-defect', {'action': 'start', 'ready_brief': True, 'artifact': 'docs/product/captured/defect-item.md', 'artifact_kind': 'defect', 'authority_mode': 'tracker-origin'}),
    ('tracker-start-design', {'action': 'start', 'artifact': 'docs/product/captured/design-item.md', 'artifact_kind': 'design', 'authority_mode': 'tracker-origin'}),
    ('tracker-remember-design', {'action': 'remember', 'artifact': 'docs/product/captured/design-item.md', 'artifact_kind': 'design', 'authority_mode': 'tracker-origin'}),
    ('tracker-ready-brief-design', {'action': 'start', 'ready_brief': True, 'artifact': 'docs/product/captured/design-item.md', 'artifact_kind': 'design', 'authority_mode': 'tracker-origin'}),
    ('tracker-start-research', {'action': 'start', 'artifact': 'docs/product/captured/research-item.md', 'artifact_kind': 'research', 'authority_mode': 'tracker-origin'}),
    ('tracker-remember-research', {'action': 'remember', 'artifact': 'docs/product/captured/research-item.md', 'artifact_kind': 'research', 'authority_mode': 'tracker-origin'}),
    ('tracker-ready-brief-research', {'action': 'start', 'ready_brief': True, 'artifact': 'docs/product/captured/research-item.md', 'artifact_kind': 'research', 'authority_mode': 'tracker-origin'}),
]


@pytest.mark.parametrize(("case_id", "signals"), _TRACKER_ORIGIN, ids=[c[0] for c in _TRACKER_ORIGIN])
def test_tracker_origin_routes_match_the_repo_origin_route(
    case_id: str, signals: dict[str, Any]
) -> None:
    router = _load_router()
    tracker = _outcome(router, signals)
    repo = _outcome(router, {**signals, "authority_mode": "repo-origin"})
    if repo == "ValueError":
        assert tracker == "ValueError"
        return
    assert tracker[:4] == repo[:4]
    assert tracker[4] == "tracker-origin"
    assert tracker[5:] == repo[5:]
    assert "register" not in tracker[5]


# Refresh front door: the profile comes from the artifact's own record.
_ARTIFACT = "docs/specs/example/spec.md"
_PROFILE_TABLE = '\n[tracker_profile]\nid = "example-service"\nversion = "1.0"\n'


def _record(*, profile: str) -> str:
    return (
        "# Spec: Example\n\n```toml source-authority\n"
        'contract_version = "source-authority.v1"\nmode = "tracker-origin"\n'
        'source_ref = "example-service://work/ITEM-1"\nsource_revision = "rev-1"\n'
        f"{profile}\n[owned_fields]\n```\n"
    )


class _Resolver:
    """Counts acquisition-capable resolutions; none may happen in refusals."""

    def __init__(self) -> None:
        self.acquire_resolutions = 0

    def resolve(self, profile_id: str, profile_version: str, capability: str | None = None) -> Any:
        if capability == "acquire":
            self.acquire_resolutions += 1
        raise ValueError("no registration")


class _Request:
    artifact_path = _ARTIFACT
    artifact_kind = "spec"
    lifecycle = "Approved"
    authority_mode = "tracker-origin"
    current_revision = "rev-1"
    compared_revision = "rev-2"
    profile_id = "example-service"
    profile_version = "1.0"


def _refresh_signals(router: Any, **overrides: str) -> Any:
    fields = {
        "action": "refresh",
        "artifact": _ARTIFACT,
        "artifact_kind": "spec",
        "authority_mode": "tracker-origin",
        "profile_id": "example-service",
        "profile_version": "1.0",
        **overrides,
    }
    return router.RoutingSignals(**fields)


class _Registered:
    name = "example-refresh"


class _RegisteredResolver(_Resolver):
    def resolve(self, profile_id: str, profile_version: str, capability: str | None = None) -> Any:
        if capability == "acquire":
            self.acquire_resolutions += 1
            raise ValueError("stop before acquisition")
        return _Registered()


def _plant(tmp_path: Path, text: str | None) -> Path:
    if text is not None:
        target = tmp_path / _ARTIFACT
        target.parent.mkdir(parents=True)
        target.write_text(text, encoding="utf-8")
    return tmp_path


def test_ac0004_record_without_profile_table_is_refresh_unavailable(tmp_path: Path) -> None:
    router = _load_router()
    resolver = _RegisteredResolver()
    result = router.invoke_refresh(
        _refresh_signals(router), resolver, _Request(), _plant(tmp_path, _record(profile=""))
    )
    assert result.code == "refresh-unavailable"
    assert result.remediation == "add-record-tracker-profile"
    assert result.invocation is None
    assert resolver.acquire_resolutions == 0


@pytest.mark.parametrize("field", ["profile_id", "profile_version"])
def test_ac0005_signals_naming_a_different_profile_are_refresh_unavailable(
    tmp_path: Path, field: str
) -> None:
    router = _load_router()
    resolver = _RegisteredResolver()
    signals = _refresh_signals(router, **{field: "other"})
    request = type("Req", (_Request,), {field: "other"})()
    result = router.invoke_refresh(
        signals, resolver, request, _plant(tmp_path, _record(profile=_PROFILE_TABLE))
    )
    assert result.code == "refresh-unavailable"
    assert result.invocation is None
    assert resolver.acquire_resolutions == 0


def test_ac0005_matching_record_profile_reaches_the_processor_resolution(
    tmp_path: Path,
) -> None:
    router = _load_router()
    resolver = _RegisteredResolver()
    result = router.invoke_refresh(
        _refresh_signals(router),
        resolver,
        _Request(),
        _plant(tmp_path, _record(profile=_PROFILE_TABLE)),
    )
    assert resolver.acquire_resolutions == 1
    assert result.code == "refresh-unavailable"


@pytest.mark.parametrize("text", [None, "not a record\n"])
def test_unreadable_or_unparseable_record_is_a_named_no_effect_result(
    tmp_path: Path, text: str | None
) -> None:
    router = _load_router()
    resolver = _RegisteredResolver()
    result = router.invoke_refresh(
        _refresh_signals(router), resolver, _Request(), _plant(tmp_path, text)
    )
    assert result.code == "refresh-unavailable"
    assert result.remediation == "repair-or-rerun-refresh-record-read"
    assert resolver.acquire_resolutions == 0
    assert not (tmp_path / "workspace.toml").exists()


def test_ac0004_signals_without_a_profile_still_reach_the_record_check(
    tmp_path: Path,
) -> None:
    router = _load_router()
    resolver = _RegisteredResolver()
    signals = router.RoutingSignals(
        action="refresh",
        artifact=_ARTIFACT,
        artifact_kind="spec",
        authority_mode="tracker-origin",
    )
    result = router.invoke_refresh(
        signals, resolver, _Request(), _plant(tmp_path, _record(profile=""))
    )
    assert result.code == "refresh-unavailable"
    assert result.remediation == "add-record-tracker-profile"
    assert resolver.acquire_resolutions == 0


def test_ac0005_signals_without_a_profile_resolve_the_record_profile(
    tmp_path: Path,
) -> None:
    router = _load_router()
    resolver = _RegisteredResolver()
    signals = router.RoutingSignals(
        action="refresh",
        artifact=_ARTIFACT,
        artifact_kind="spec",
        authority_mode="tracker-origin",
    )
    result = router.invoke_refresh(
        signals,
        resolver,
        _Request(),
        _plant(tmp_path, _record(profile=_PROFILE_TABLE)),
    )
    assert resolver.acquire_resolutions == 1
    assert result.remediation == "configure-compatible-refresh-processor"


def test_ac0005_no_profile_signals_with_a_mismatched_request_profile_are_unavailable(
    tmp_path: Path,
) -> None:
    router = _load_router()
    resolver = _RegisteredResolver()
    signals = router.RoutingSignals(
        action="refresh",
        artifact=_ARTIFACT,
        artifact_kind="spec",
        authority_mode="tracker-origin",
    )
    request = type("Req", (_Request,), {"profile_id": "other"})()
    result = router.invoke_refresh(
        signals, resolver, request, _plant(tmp_path, _record(profile=_PROFILE_TABLE))
    )
    assert result.code == "refresh-unavailable"
    assert result.invocation is None
    assert resolver.acquire_resolutions == 0
