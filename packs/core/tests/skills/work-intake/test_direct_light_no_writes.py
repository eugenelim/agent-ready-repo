"""Decision-seam no-write coverage. Read the scope limits before trusting it.

What this establishes: for a direct-light signal, ``route_intake()`` returns an
all-absent ``Route``, and a caller that gates the transaction on any durable-route
marker will not invoke it.

What it does NOT establish, in two distinct ways:

1. ``route_intake()`` is a pure function with no filesystem actor, so the
   unchanged fixture snapshot is guaranteed by construction rather than earned.
   It catches a *code path* that starts writing; it cannot catch an agent
   following ``SKILL.md`` that writes. That property is recorded manual QA.
2. ``_drive_route`` below is *test-local* wiring, not production wiring. There is
   no production route-to-transaction dispatcher to exercise. So the
   "transaction not invoked" assertion proves the marker rule holds for a caller
   shaped like ``_drive_route`` — it would not catch a future orchestration layer
   that writes despite an all-absent route.

Both limits are deliberate: the alternative was inventing a dispatcher this
change does not need.
"""

from __future__ import annotations

import hashlib
import importlib.util
import sys
from pathlib import Path

import pytest

_PACK_ROOT = Path(__file__).resolve().parents[3]
_ROUTER_PATH = (
    _PACK_ROOT
    / ".apm"
    / "skills"
    / "work-intake"
    / "scripts"
    / "intake_router.py"
)
_TRANSACTION_PATH = (
    _PACK_ROOT
    / ".apm"
    / "skills"
    / "work-intake"
    / "scripts"
    / "intake_transaction.py"
)


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _snapshot_files(root: Path) -> dict[str, str]:
    """Return the complete recursive regular-file digest map below ``root``."""

    return {
        path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def _drive_route(route, run_transaction) -> None:
    """Invoke the transaction seam if *any* durable-route marker is present.

    Keyed on all three markers rather than ``mutation`` alone: a future
    production wiring might gate the transaction on the artifact path or the
    lifecycle membership instead, and a harness watching one field would keep
    passing while the other two drifted.
    """

    if (
        route.mutation != "none"
        or route.artifact != ""
        or route.lifecycle_membership != "none"
    ):
        run_transaction()


@pytest.fixture
def fixture_repository(tmp_path: Path) -> Path:
    (tmp_path / "workspace.toml").write_text("[work]\nqueue = []\n", encoding="utf-8")
    nested = tmp_path / "docs" / "nested"
    nested.mkdir(parents=True)
    (nested / "existing.md").write_text("fixture content\n", encoding="utf-8")
    return tmp_path


def test_direct_light_decision_seam_leaves_fixture_unchanged_and_skips_transaction(
    fixture_repository: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    router = _load_module("intake_router_direct_light", _ROUTER_PATH)
    transaction = _load_module("intake_transaction_direct_light", _TRANSACTION_PATH)
    before = _snapshot_files(fixture_repository)

    def fail_if_called() -> None:
        pytest.fail("direct-light must not invoke run_intake_transaction")

    monkeypatch.setattr(transaction, "run_intake_transaction", fail_if_called)
    route = router.route_intake(
        router.RoutingSignals(
            action="start",
            artifact="",
            artifact_kind="",
            authority_mode="repo-origin",
            direct_light=True,
        )
    )

    _drive_route(route, transaction.run_intake_transaction)

    assert (route.artifact, route.artifact_kind) == ("", "")
    assert (route.lifecycle_membership, route.processor) == ("none", "work-loop")
    assert route.mutation == "none"
    assert _snapshot_files(fixture_repository) == before
