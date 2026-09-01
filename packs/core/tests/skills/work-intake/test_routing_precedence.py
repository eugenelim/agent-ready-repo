"""Construction contracts for canonical intake routing."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROUTER = (
    Path(__file__).resolve().parents[3]
    / ".apm"
    / "skills"
    / "work-intake"
    / "scripts"
    / "intake_router.py"
)
SKILL = ROUTER.parents[1] / "SKILL.md"


def load_router():
    """Load the current deterministic routing seam."""
    spec = importlib.util.spec_from_file_location("_canonical_intake_router", ROUTER)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_canonical_intent_and_brief_routes_use_the_new_owners() -> None:
    """The executable router emits canonical processors for durable starts."""
    router = load_router()
    base = {"action": "start", "artifact": "", "authority_mode": "repo-origin"}
    intent = router.route_intake(
        router.RoutingSignals(artifact_kind="intent", **base)
    )
    brief = router.route_intake(
        router.RoutingSignals(artifact_kind="brief", **base)
    )
    assert intent.processor == "intake-intent"
    assert brief.processor == "author-delivery-brief create"


def test_status_refresh_ready_and_remember_preserve_their_distinct_routes() -> None:
    router = load_router()

    status = router.route_intake(
        router.RoutingSignals(
            action="status",
            artifact="workspace.toml",
            artifact_kind="workspace-status",
            authority_mode="read-only",
        )
    )
    refresh = router.route_intake(
        router.RoutingSignals(
            action="refresh",
            artifact="docs/specs/example/spec.md",
            artifact_kind="spec",
            authority_mode="repo-origin",
        )
    )
    ready = router.route_intake(
        router.RoutingSignals(
            action="start",
            artifact="docs/product/briefs/example.md",
            artifact_kind="brief",
            authority_mode="repo-origin",
            ready_brief=True,
        )
    )
    remembered = router.route_intake(
        router.RoutingSignals(
            action="remember",
            artifact="docs/product/intents/example.md",
            artifact_kind="intent",
            authority_mode="repo-origin",
        )
    )

    assert (status.processor, status.mutation) == ("workspace-status", "none")
    assert (refresh.processor, refresh.mutation) == ("none", "none")
    assert (ready.processor, ready.lifecycle_membership) == (
        "author-delivery-brief continue",
        "brief_queue.ready",
    )
    assert remembered.processor == "intake-intent"
    assert remembered.lifecycle_membership == "backlog.open"


def test_public_precedence_routes_explicit_work_directly() -> None:
    body = " ".join(SKILL.read_text(encoding="utf-8").split())
    status = body.index("Route status directly to `workspace-status`")
    explicit = body.index("Route a request that explicitly names")
    fallback = body.index("Route only a raw or ambiguous request")

    assert status < explicit < fallback
    for owner in (
        "`intake-intent`",
        "`author-delivery-brief create|continue`",
        "`new-rfc`",
        "`new-spec`",
        "`architect-design`",
        "`frame-intent`",
        "`bug-fix`",
    ):
        assert owner in body
    assert "Delegation from this skill" in body
    assert "not a second public answer" in body


def test_changed_intake_fixtures_write_only_canonical_processors() -> None:
    fixture_root = ROUTER.parents[1] / "evals"
    text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in sorted(fixture_root.rglob("*.json"))
    )

    assert '"processor":"author-brief"' not in text
    assert '"processor":"receive-brief"' not in text
    assert "routes to receive-brief or author-brief" not in text
    assert "author-delivery-brief" in text
    assert "intake-intent" in text
