"""PLAN-time contract stubs for canonical intake routing."""

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
    # STUB: AC2
    # STUB: AC6
    router = load_router()
    base = dict(action="start", artifact="", authority_mode="repo-origin")
    intent = router.route_intake(
        router.RoutingSignals(artifact_kind="intent", **base)
    )
    brief = router.route_intake(
        router.RoutingSignals(artifact_kind="brief", **base)
    )
    assert intent.processor == "intake-intent"
    assert brief.processor == "author-delivery-brief"
