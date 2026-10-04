"""Finding 2 fix suite: intersect_grants network-destination and trust-class invariants.

Tests that fail when the corresponding fix is reverted:

- Disjoint network destinations produce denied=False rather than an empty set
  that reads as "any destination allowed".
- A one-side-empty destinations list does not widen the constrained side.
- A child grant never carries a more-trusted class than its parent.

Follows the importlib.util.spec_from_file_location loader pattern from sibling
suites.  No third-party imports at test collection time.
"""

from __future__ import annotations

import importlib.util
import os
import stat
import sys
from pathlib import Path
from types import ModuleType

import pytest

# ── Path anchor ───────────────────────────────────────────────────────────────

SCRIPTS = (
    Path(__file__).resolve().parents[3]
    / ".apm"
    / "skills"
    / "work-loop"
    / "scripts"
)

# ── Module loader ─────────────────────────────────────────────────────────────


def _load_module(name: str, path: Path) -> ModuleType:
    """Load an unregistered copy of a scripts module via importlib."""
    info = os.lstat(path)
    assert stat.S_ISREG(info.st_mode), f"not a regular file: {path}"
    previous = sys.dont_write_bytecode
    try:
        sys.dont_write_bytecode = True
        spec = importlib.util.spec_from_file_location(name, str(path))
        assert spec is not None and spec.loader is not None
        mod = importlib.util.module_from_spec(spec)
        sys.modules[name] = mod
        try:
            spec.loader.exec_module(mod)  # type: ignore[union-attr]
        finally:
            sys.modules.pop(name, None)
        return mod
    finally:
        sys.dont_write_bytecode = previous


@pytest.fixture(scope="module")
def sc() -> ModuleType:
    """_security_capability.py loaded by path."""
    return _load_module("sc_cap_intersect", SCRIPTS / "_security_capability.py")


# ── Grant construction helpers ────────────────────────────────────────────────


def _root_grant(
    sc_mod: ModuleType,
    *,
    roots: list[str],
    operations: list[str] | None = None,
    trust_class: str = "trusted-adapter",
    network: object | None = None,
) -> object:
    """Issue a root grant with the supplied network field and defaults."""
    issuer = sc_mod.CapabilityIssuer()
    return issuer.issue_root_grant(
        roots=roots,
        operations=operations or ["read", "write"],
        trust_class=trust_class,
        writes_allowed_roots=roots,
        control_denies=[],
        network=network,
    )


def _bare_grant(
    sc_mod: ModuleType,
    *,
    grant_id: str = "bare-grant",
    roots: list[str],
    operations: list[str] | None = None,
    trust_class: str = "trusted-adapter",
    network: object | None = None,
) -> object:
    """Build a CapabilityGrant directly (not issued) with the given fields."""
    return sc_mod.CapabilityGrant(
        schema_version=sc_mod.SUPPORTED_SCHEMA_VERSION,
        grant_id=grant_id,
        roots=tuple(sorted(roots)),
        operations=tuple(sorted(operations or ["read", "write"])),
        trust_class=trust_class,
        writes=sc_mod._WritesGrant(allowed_roots=tuple(sorted(roots))),
        control_denies=(),
        limits=sc_mod._Limits(),
        network=network,
    )


# ═══════════════════════════════════════════════════════════════════════════════
# Finding 2: intersect_grants — network destination intersection invariants
# ═══════════════════════════════════════════════════════════════════════════════


class TestNetworkDestinationIntersection:
    """intersect_grants must not produce an empty-destinations-allowed=True grant
    when both sides constrain to disjoint destinations.
    """

    def test_disjoint_destinations_deny_network(self, sc: ModuleType) -> None:
        """A parent limited to a.example and a request for b.example produce denied network.

        Before the fix the intersection of {"a.example"} and {"b.example"} yields
        an empty set, so intersect_grants built _NetworkGrant(allowed=True,
        allowed_destinations=()), which the module's convention reads as "any
        destination allowed".  After the fix, a disjoint intersection produces
        _NetworkGrant(allowed=False).

        Fails when the disjoint-intersection guard is removed from intersect_grants.
        """
        request = _bare_grant(
            sc,
            roots=["/work"],
            network=sc._NetworkGrant(allowed=True, allowed_destinations=("b.example",)),
        )
        issuer = sc.CapabilityIssuer()
        real_parent = issuer.issue_root_grant(
            roots=["/work"],
            operations=["read", "write"],
            trust_class="trusted-adapter",
            writes_allowed_roots=["/work"],
            control_denies=[],
            network=sc._NetworkGrant(allowed=True, allowed_destinations=("a.example",)),
        )
        child = issuer.issue_child_grant(real_parent, request)
        assert child.network is not None, "child network field must be set"
        assert not child.network.allowed, (
            "disjoint destination intersection must produce network.allowed=False, "
            f"got allowed={child.network.allowed!r}, "
            f"destinations={child.network.allowed_destinations!r}"
        )

    def test_one_side_empty_does_not_widen_constrained_side(
        self, sc: ModuleType
    ) -> None:
        """One-side-empty destinations do not widen the constrained side.

        Parent is constrained to a.example; request has empty destinations
        (meaning unconstrained).  The child must be limited to a.example —
        it must not widen to the empty-set "any" convention.

        This tests the existing correct behaviour is preserved after the fix
        so that the disjoint guard does not accidentally affect the one-side
        case.
        """
        issuer = sc.CapabilityIssuer()
        real_parent = issuer.issue_root_grant(
            roots=["/work"],
            operations=["read", "write"],
            trust_class="trusted-adapter",
            writes_allowed_roots=["/work"],
            control_denies=[],
            network=sc._NetworkGrant(allowed=True, allowed_destinations=("a.example",)),
        )
        # Request has empty allowed_destinations (unconstrained on its side).
        request = _bare_grant(
            sc,
            roots=["/work"],
            network=sc._NetworkGrant(allowed=True, allowed_destinations=()),
        )
        child = issuer.issue_child_grant(real_parent, request)
        assert child.network is not None, "child network field must be set"
        assert child.network.allowed, (
            "child network must be allowed when only one side constrains"
        )
        # The constrained parent list must be preserved; the empty request
        # must not widen to "any destination".
        assert child.network.allowed_destinations == ("a.example",), (
            "child destinations must equal parent's constrained list; "
            f"got {child.network.allowed_destinations!r}"
        )

    def test_one_side_empty_request_does_not_widen(self, sc: ModuleType) -> None:
        """Symmetric: parent unconstrained, request constrained — child is constrained.

        Parent has empty destinations (any allowed); request constrains to b.example.
        Child must be limited to b.example, not to the empty-set "any".
        """
        issuer = sc.CapabilityIssuer()
        real_parent = issuer.issue_root_grant(
            roots=["/work"],
            operations=["read", "write"],
            trust_class="trusted-adapter",
            writes_allowed_roots=["/work"],
            control_denies=[],
            network=sc._NetworkGrant(allowed=True, allowed_destinations=()),
        )
        request = _bare_grant(
            sc,
            roots=["/work"],
            network=sc._NetworkGrant(allowed=True, allowed_destinations=("b.example",)),
        )
        child = issuer.issue_child_grant(real_parent, request)
        assert child.network is not None
        assert child.network.allowed
        assert child.network.allowed_destinations == ("b.example",), (
            "child must be limited to request's constrained list; "
            f"got {child.network.allowed_destinations!r}"
        )


# ═══════════════════════════════════════════════════════════════════════════════
# Finding 2: intersect_grants — trust_class never more trusted than parent
# ═══════════════════════════════════════════════════════════════════════════════


class TestTrustClassNeverEscalated:
    """A child grant's trust_class must never be more trusted than its parent's.

    No explicit ordering exists in the module, so the parent's class is kept
    whenever the two differ.
    """

    def test_child_trust_class_never_exceeds_parent(
        self, sc: ModuleType
    ) -> None:
        """A request naming a different trust class than the parent gets the parent's class.

        Before the fix, intersect_grants copied trust_class directly from the
        request, so a child could name any class regardless of the parent.
        After the fix, the parent's class is kept unless both sides already agree.

        Fails when the trust_class assignment reverts to unconditionally using
        request.trust_class.
        """
        issuer = sc.CapabilityIssuer()
        real_parent = issuer.issue_root_grant(
            roots=["/work"],
            operations=["read", "write"],
            trust_class="trusted-adapter",
            writes_allowed_roots=["/work"],
            control_denies=[],
        )
        # Request claims a different trust class than the parent.
        request = _bare_grant(
            sc,
            roots=["/work"],
            trust_class="system",  # different from parent's "trusted-adapter"
        )
        child = issuer.issue_child_grant(real_parent, request)
        assert child.trust_class == "trusted-adapter", (
            "child must inherit parent's trust_class when request differs; "
            f"got {child.trust_class!r}"
        )

    def test_matching_trust_class_preserved(self, sc: ModuleType) -> None:
        """When both parent and request use the same trust class, the child keeps it."""
        issuer = sc.CapabilityIssuer()
        real_parent = issuer.issue_root_grant(
            roots=["/work"],
            operations=["read", "write"],
            trust_class="trusted-adapter",
            writes_allowed_roots=["/work"],
            control_denies=[],
        )
        request = _bare_grant(
            sc,
            roots=["/work"],
            trust_class="trusted-adapter",  # same as parent
        )
        child = issuer.issue_child_grant(real_parent, request)
        assert child.trust_class == "trusted-adapter", (
            "matching trust class must be preserved; "
            f"got {child.trust_class!r}"
        )
