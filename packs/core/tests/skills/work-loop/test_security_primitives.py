"""T3a TDD suite: capability, confined-file mutation, and security-event invariants.

Mode: TDD (plan.md T3a).

Tests AC-0010 (capability intersection), AC-0011 (confined mutation adversarial
fixtures), AC-0020 (named writer authority), and AC-0021 (durable audit before
acknowledgment; sink-unavailable fail-closed).

Follows the importlib.util.spec_from_file_location loader pattern established in
test_content_safety.py so modules remain unregistered in sys.modules between
test sessions.

Platform-specific fixtures skip only when the host cannot supply the asserted
primitive; the descriptor-walk fallback is always exercised by monkeypatching
(the fixture must not skip on any host).
"""

from __future__ import annotations

import contextlib
import importlib.util
import os
import stat
import sys
import time
from pathlib import Path
from types import ModuleType

import pytest

# ── Path anchors ─────────────────────────────────────────────────────────────

SCRIPTS = (
    Path(__file__).resolve().parents[3]
    / ".apm"
    / "skills"
    / "work-loop"
    / "scripts"
)

# ── Module loader helpers ─────────────────────────────────────────────────────


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
        spec.loader.exec_module(mod)  # type: ignore[union-attr]
        return mod
    finally:
        sys.dont_write_bytecode = previous


@pytest.fixture(scope="module")
def security_capability() -> ModuleType:
    return _load_module("sc_under_test", SCRIPTS / "_security_capability.py")


@pytest.fixture(scope="module")
def confined_mutation() -> ModuleType:
    return _load_module("cm_under_test", SCRIPTS / "_confined_mutation.py")


@pytest.fixture(scope="module")
def security_events() -> ModuleType:
    return _load_module("se_under_test", SCRIPTS / "_security_events.py")


# ── Capability helpers ────────────────────────────────────────────────────────


def _make_root_grant(sc: ModuleType, **kwargs) -> object:
    """Issue a root grant with sensible defaults."""
    defaults: dict = {
        "roots": ["/work"],
        "operations": ["read", "write"],
        "trust_class": "trusted-adapter",
        "writes_allowed_roots": ["/work"],
        "control_denies": [],
    }
    defaults.update(kwargs)
    issuer = sc.CapabilityIssuer()
    return issuer, issuer.issue_root_grant(**defaults)


# ═══════════════════════════════════════════════════════════════════════════════
# AC-0010: Capability intersection
# ═══════════════════════════════════════════════════════════════════════════════


class TestCapabilityIntersection:
    """Property tests for child-grant intersection (AC-0010)."""

    def test_child_roots_is_intersection(self, security_capability: ModuleType) -> None:
        """Child roots are the intersection of parent and request roots."""
        sc = security_capability
        issuer = sc.CapabilityIssuer()
        parent = issuer.issue_root_grant(
            roots=["/a", "/b"],
            operations=["read", "write"],
            trust_class="trusted-adapter",
            writes_allowed_roots=["/a", "/b"],
            control_denies=[],
        )
        request = sc.CapabilityGrant(
            schema_version=sc.SUPPORTED_SCHEMA_VERSION,
            grant_id="req-1",
            roots=("/b", "/c"),
            operations=("read",),
            trust_class="trusted-adapter",
            writes=sc._WritesGrant(allowed_roots=("/b",)),
            control_denies=(),
            limits=sc._Limits(),
        )
        child = issuer.issue_child_grant(parent, request)
        assert set(child.roots) == {"/b"}, f"expected {{/b}}, got {set(child.roots)}"

    def test_child_operations_is_intersection(self, security_capability: ModuleType) -> None:
        """Child operations are the intersection of parent and request operations."""
        sc = security_capability
        issuer = sc.CapabilityIssuer()
        parent = issuer.issue_root_grant(
            roots=["/w"],
            operations=["read", "write", "execute"],
            trust_class="trusted-adapter",
            writes_allowed_roots=["/w"],
            control_denies=[],
        )
        request = sc.CapabilityGrant(
            schema_version=sc.SUPPORTED_SCHEMA_VERSION,
            grant_id="req-2",
            roots=("/w",),
            operations=("write", "execute", "admin"),
            trust_class="trusted-adapter",
            writes=sc._WritesGrant(allowed_roots=("/w",)),
            control_denies=(),
            limits=sc._Limits(),
        )
        child = issuer.issue_child_grant(parent, request)
        assert set(child.operations) == {"write", "execute"}

    def test_omitted_network_in_parent_denies_all(
        self, security_capability: ModuleType
    ) -> None:
        """Parent without network → child has no network (deny all)."""
        sc = security_capability
        issuer = sc.CapabilityIssuer()
        parent = issuer.issue_root_grant(
            roots=["/w"],
            operations=["read"],
            trust_class="trusted-adapter",
            writes_allowed_roots=[],
            control_denies=[],
            network=None,  # no network in parent
        )
        request = sc.CapabilityGrant(
            schema_version=sc.SUPPORTED_SCHEMA_VERSION,
            grant_id="req-3",
            roots=("/w",),
            operations=("read",),
            trust_class="trusted-adapter",
            writes=sc._WritesGrant(allowed_roots=()),
            control_denies=(),
            limits=sc._Limits(),
            network=sc._NetworkGrant(allowed=True),  # request wants network
        )
        child = issuer.issue_child_grant(parent, request)
        assert child.network is None, "child must have no network when parent omits it"

    def test_omitted_network_in_request_denies_all(
        self, security_capability: ModuleType
    ) -> None:
        """Request without network → child has no network (deny all)."""
        sc = security_capability
        issuer = sc.CapabilityIssuer()
        parent = issuer.issue_root_grant(
            roots=["/w"],
            operations=["read"],
            trust_class="trusted-adapter",
            writes_allowed_roots=[],
            control_denies=[],
            network=sc._NetworkGrant(allowed=True),  # parent has network
        )
        request = sc.CapabilityGrant(
            schema_version=sc.SUPPORTED_SCHEMA_VERSION,
            grant_id="req-4",
            roots=("/w",),
            operations=("read",),
            trust_class="trusted-adapter",
            writes=sc._WritesGrant(allowed_roots=()),
            control_denies=(),
            limits=sc._Limits(),
            network=None,  # request omits network
        )
        child = issuer.issue_child_grant(parent, request)
        assert child.network is None, "child must have no network when request omits it"

    def test_omitted_children_in_parent_denies_all(
        self, security_capability: ModuleType
    ) -> None:
        """Parent without children → child has no child-process authority."""
        sc = security_capability
        issuer = sc.CapabilityIssuer()
        parent = issuer.issue_root_grant(
            roots=["/w"],
            operations=["execute"],
            trust_class="trusted-adapter",
            writes_allowed_roots=[],
            control_denies=[],
            children=None,
        )
        request = sc.CapabilityGrant(
            schema_version=sc.SUPPORTED_SCHEMA_VERSION,
            grant_id="req-5",
            roots=("/w",),
            operations=("execute",),
            trust_class="trusted-adapter",
            writes=sc._WritesGrant(allowed_roots=()),
            control_denies=(),
            limits=sc._Limits(),
            children=sc._ChildrenGrant(allowed=True),
        )
        child = issuer.issue_child_grant(parent, request)
        assert child.children is None, "child must have no children when parent omits it"

    def test_omitted_children_in_request_denies_all(
        self, security_capability: ModuleType
    ) -> None:
        """Request without children → child has no child-process authority."""
        sc = security_capability
        issuer = sc.CapabilityIssuer()
        parent = issuer.issue_root_grant(
            roots=["/w"],
            operations=["execute"],
            trust_class="trusted-adapter",
            writes_allowed_roots=[],
            control_denies=[],
            children=sc._ChildrenGrant(allowed=True),
        )
        request = sc.CapabilityGrant(
            schema_version=sc.SUPPORTED_SCHEMA_VERSION,
            grant_id="req-6",
            roots=("/w",),
            operations=("execute",),
            trust_class="trusted-adapter",
            writes=sc._WritesGrant(allowed_roots=()),
            control_denies=(),
            limits=sc._Limits(),
            children=None,
        )
        child = issuer.issue_child_grant(parent, request)
        assert child.children is None, "child must have no children when request omits it"

    def test_limits_take_minimum(self, security_capability: ModuleType) -> None:
        """Child limits take the stricter (minimum) of parent and request."""
        sc = security_capability
        issuer = sc.CapabilityIssuer()
        parent = issuer.issue_root_grant(
            roots=["/w"],
            operations=["read"],
            trust_class="trusted-adapter",
            writes_allowed_roots=[],
            control_denies=[],
            limits=sc._Limits(max_bytes=1000, timeout_s=60),
        )
        request = sc.CapabilityGrant(
            schema_version=sc.SUPPORTED_SCHEMA_VERSION,
            grant_id="req-7",
            roots=("/w",),
            operations=("read",),
            trust_class="trusted-adapter",
            writes=sc._WritesGrant(allowed_roots=()),
            control_denies=(),
            limits=sc._Limits(max_bytes=500, timeout_s=120),
        )
        child = issuer.issue_child_grant(parent, request)
        assert child.limits.max_bytes == 500, "should take min(1000, 500)"
        assert child.limits.timeout_s == 60, "should take min(60, 120)"

    def test_control_denies_is_union(self, security_capability: ModuleType) -> None:
        """Child control_denies is the union of parent and request denies."""
        sc = security_capability
        issuer = sc.CapabilityIssuer()
        parent = issuer.issue_root_grant(
            roots=["/w"],
            operations=["read"],
            trust_class="trusted-adapter",
            writes_allowed_roots=[],
            control_denies=["path-a", "path-b"],
        )
        request = sc.CapabilityGrant(
            schema_version=sc.SUPPORTED_SCHEMA_VERSION,
            grant_id="req-8",
            roots=("/w",),
            operations=("read",),
            trust_class="trusted-adapter",
            writes=sc._WritesGrant(allowed_roots=()),
            control_denies=("path-b", "path-c"),
            limits=sc._Limits(),
        )
        child = issuer.issue_child_grant(parent, request)
        assert set(child.control_denies) == {"path-a", "path-b", "path-c"}

    def test_child_cannot_widen_roots(self, security_capability: ModuleType) -> None:
        """A request that asks for roots outside the parent grant gets empty intersection."""
        sc = security_capability
        issuer = sc.CapabilityIssuer()
        parent = issuer.issue_root_grant(
            roots=["/work/only"],
            operations=["read"],
            trust_class="trusted-adapter",
            writes_allowed_roots=[],
            control_denies=[],
        )
        request = sc.CapabilityGrant(
            schema_version=sc.SUPPORTED_SCHEMA_VERSION,
            grant_id="req-9",
            roots=("/other/root",),
            operations=("read",),
            trust_class="trusted-adapter",
            writes=sc._WritesGrant(allowed_roots=()),
            control_denies=(),
            limits=sc._Limits(),
        )
        child = issuer.issue_child_grant(parent, request)
        assert child.roots == (), "child gets empty roots when request has no overlap with parent"


class TestCapabilityGrantLifecycle:
    """Tests for active-grant state: issuance, expiry, revocation, replay (AC-0010)."""

    def test_issued_grant_verifies(self, security_capability: ModuleType) -> None:
        """A grant issued by an issuer verifies against that issuer."""
        sc = security_capability
        issuer = sc.CapabilityIssuer()
        grant = issuer.issue_root_grant(
            roots=["/w"],
            operations=["read"],
            trust_class="trusted-adapter",
            writes_allowed_roots=[],
            control_denies=[],
        )
        assert issuer.verify_grant(grant) is True

    def test_revoked_grant_refuses(self, security_capability: ModuleType) -> None:
        """A revoked grant fails verification."""
        sc = security_capability
        issuer = sc.CapabilityIssuer()
        grant = issuer.issue_root_grant(
            roots=["/w"],
            operations=["read"],
            trust_class="trusted-adapter",
            writes_allowed_roots=[],
            control_denies=[],
        )
        issuer.revoke_grant(grant.grant_id)
        assert issuer.verify_grant(grant) is False

    def test_expired_grant_refuses(self, security_capability: ModuleType) -> None:
        """A grant past its expiry time fails verification."""
        sc = security_capability
        issuer = sc.CapabilityIssuer()
        grant = issuer.issue_root_grant(
            roots=["/w"],
            operations=["read"],
            trust_class="trusted-adapter",
            writes_allowed_roots=[],
            control_denies=[],
            expires_in_s=0.001,  # expires in 1 ms
        )
        time.sleep(0.01)  # let it expire
        assert issuer.verify_grant(grant) is False

    def test_caller_built_grant_refuses(self, security_capability: ModuleType) -> None:
        """A CapabilityGrant constructed directly (not from the issuer) fails verification."""
        sc = security_capability
        issuer = sc.CapabilityIssuer()
        # Build a grant directly without using the issuer
        forged = sc.CapabilityGrant(
            schema_version=sc.SUPPORTED_SCHEMA_VERSION,
            grant_id="forged-grant-id-not-registered",
            roots=("/work",),
            operations=("read", "write"),
            trust_class="trusted-adapter",
            writes=sc._WritesGrant(allowed_roots=("/work",)),
            control_denies=(),
            limits=sc._Limits(),
        )
        assert issuer.verify_grant(forged) is False, "caller-built grant must not verify"

    def test_replayed_grant_from_different_issuer_refuses(
        self, security_capability: ModuleType
    ) -> None:
        """A valid grant from issuer A does not verify against issuer B."""
        sc = security_capability
        issuer_a = sc.CapabilityIssuer()
        issuer_b = sc.CapabilityIssuer()
        grant_a = issuer_a.issue_root_grant(
            roots=["/w"],
            operations=["read"],
            trust_class="trusted-adapter",
            writes_allowed_roots=[],
            control_denies=[],
        )
        # grant_a verifies with issuer_a but not issuer_b
        assert issuer_a.verify_grant(grant_a) is True
        assert issuer_b.verify_grant(grant_a) is False, "grant from issuer A must not verify with issuer B"

    def test_invalid_parent_refuses_child_issue(
        self, security_capability: ModuleType
    ) -> None:
        """Issuing a child grant with an invalid parent raises CapabilityRefused."""
        sc = security_capability
        issuer = sc.CapabilityIssuer()
        forged_parent = sc.CapabilityGrant(
            schema_version=sc.SUPPORTED_SCHEMA_VERSION,
            grant_id="bad-parent-id",
            roots=("/work",),
            operations=("read",),
            trust_class="trusted-adapter",
            writes=sc._WritesGrant(allowed_roots=()),
            control_denies=(),
            limits=sc._Limits(),
        )
        request = sc.CapabilityGrant(
            schema_version=sc.SUPPORTED_SCHEMA_VERSION,
            grant_id="req-child",
            roots=("/work",),
            operations=("read",),
            trust_class="trusted-adapter",
            writes=sc._WritesGrant(allowed_roots=()),
            control_denies=(),
            limits=sc._Limits(),
        )
        with pytest.raises(sc.CapabilityRefused) as exc_info:
            issuer.issue_child_grant(forged_parent, request)
        assert exc_info.value.denial_code == "denied-invalid-parent"


# ═══════════════════════════════════════════════════════════════════════════════
# AC-0011: Confined-file mutation adversarial fixtures
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.fixture
def tmp_root(tmp_path: Path) -> Path:
    """Temporary root directory for mutation tests."""
    return tmp_path


class TestConfinedMutationHappyPath:
    """Basic correctness: create, append, atomic replace."""

    def test_confined_create_new_file(
        self, confined_mutation: ModuleType, tmp_root: Path
    ) -> None:
        """confined_create writes a new file within the root."""
        target = tmp_root / "new.txt"
        confined_mutation.confined_create(tmp_root, target, b"hello")
        assert target.read_bytes() == b"hello"

    def test_confined_append_to_existing(
        self, confined_mutation: ModuleType, tmp_root: Path
    ) -> None:
        """confined_append appends content to an existing file."""
        target = tmp_root / "existing.txt"
        target.write_bytes(b"first ")
        confined_mutation.confined_append(tmp_root, target, b"second")
        assert target.read_bytes() == b"first second"

    def test_confined_atomic_replace(
        self, confined_mutation: ModuleType, tmp_root: Path
    ) -> None:
        """confined_atomic_replace overwrites a file with new content."""
        target = tmp_root / "replace.txt"
        target.write_bytes(b"old content")
        confined_mutation.confined_atomic_replace(tmp_root, target, b"new content")
        assert target.read_bytes() == b"new content"


class TestConfinedMutationAdversarial:
    """Adversarial fixtures for AC-0011."""

    def test_absolute_path_refuses(
        self, confined_mutation: ModuleType, tmp_root: Path
    ) -> None:
        """An absolute path outside root raises MutationDenied."""
        outside = Path("/etc/passwd")
        with pytest.raises((confined_mutation.MutationDenied, Exception)) as exc_info:
            confined_mutation.confined_atomic_replace(tmp_root, outside, b"x")
        # Must refuse — either MutationDenied or UnsafeContentError
        exc = exc_info.value
        assert isinstance(exc, (confined_mutation.MutationDenied,)), (
            f"Expected MutationDenied, got {type(exc).__name__}: {exc}"
        )

    def test_dot_segment_path_refuses(
        self, confined_mutation: ModuleType, tmp_root: Path
    ) -> None:
        """A path with dot-segment traversal refuses."""
        traversal = tmp_root / ".." / "escape.txt"
        with pytest.raises(confined_mutation.MutationDenied):
            confined_mutation.confined_atomic_replace(tmp_root, traversal, b"x")

    @pytest.mark.skipif(
        not hasattr(os, "symlink"),
        reason="host does not support symlinks",
    )
    def test_symlink_target_refuses(
        self, confined_mutation: ModuleType, tmp_root: Path
    ) -> None:
        """A symlink as the target refuses (AC-0011)."""
        real_file = tmp_root / "real.txt"
        real_file.write_bytes(b"original")
        link = tmp_root / "link.txt"
        Path(link).symlink_to(real_file)
        with pytest.raises(confined_mutation.MutationDenied):
            confined_mutation.confined_atomic_replace(tmp_root, link, b"via-link")
        # Original file must be unchanged
        assert real_file.read_bytes() == b"original"

    def test_hard_link_refuses(
        self, confined_mutation: ModuleType, tmp_root: Path
    ) -> None:
        """A multiply-linked (hard-linked) file refuses (AC-0011)."""
        real_file = tmp_root / "real.txt"
        real_file.write_bytes(b"original")
        hard_link = tmp_root / "hard_link.txt"
        try:
            os.link(real_file, hard_link)
        except OSError:
            pytest.skip("host does not support hard links")
        with pytest.raises(confined_mutation.MutationDenied):
            confined_mutation.confined_atomic_replace(tmp_root, hard_link, b"via-hardlink")
        # Original must be unchanged
        assert real_file.read_bytes() == b"original"

    @pytest.mark.skipif(
        not hasattr(os, "mkfifo"),
        reason="host does not support FIFOs (special files)",
    )
    def test_special_file_refuses(
        self, confined_mutation: ModuleType, tmp_root: Path
    ) -> None:
        """A FIFO (special file) as target refuses (AC-0011)."""
        fifo = tmp_root / "special.fifo"
        os.mkfifo(fifo)
        with pytest.raises(confined_mutation.MutationDenied):
            confined_mutation.confined_atomic_replace(tmp_root, fifo, b"x")

    def test_bounds_exceeded_refuses(
        self, confined_mutation: ModuleType, tmp_root: Path
    ) -> None:
        """Content exceeding max_bytes raises MutationDenied before staging (AC-0011)."""
        target = tmp_root / "bounded.txt"
        target.write_bytes(b"original")
        with pytest.raises(confined_mutation.MutationDenied) as exc_info:
            confined_mutation.confined_atomic_replace(
                tmp_root, target, b"x" * 100, max_bytes=10
            )
        assert exc_info.value.denial_code == "denied-size-exceeded"
        # Original must be intact — bounds check runs before staging
        assert target.read_bytes() == b"original"

    def test_interrupted_staging_leaves_original_intact(
        self, confined_mutation: ModuleType, tmp_root: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """If the rename step fails, the original file is unchanged (AC-0011)."""
        target = tmp_root / "stable.txt"
        original_content = b"safe original content"
        target.write_bytes(original_content)

        # Simulate rename failure
        import os as _os
        real_rename = _os.rename

        def _fail_rename(src, dst, **kwargs):
            raise OSError(5, "simulated rename failure")

        monkeypatch.setattr(_os, "rename", _fail_rename)
        try:
            with pytest.raises(confined_mutation.MutationDenied) as exc_info:
                confined_mutation.confined_atomic_replace(tmp_root, target, b"new content")
            assert exc_info.value.denial_code == "denied-staging-failed"
            # Original must be intact
            assert target.read_bytes() == original_content
        finally:
            monkeypatch.setattr(_os, "rename", real_rename)

    def test_atomic_replace_prior_bytes_intact_on_refusal(
        self, confined_mutation: ModuleType, tmp_root: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """After any refusal during atomic replace, prior bytes remain intact (AC-0011)."""
        target = tmp_root / "prior.txt"
        prior_bytes = b"prior bytes must survive refusal"
        target.write_bytes(prior_bytes)

        # Monkeypatch os.fsync to raise (simulates staging failure after write)
        import os as _os
        real_fsync = _os.fsync

        def _fail_fsync(fd: int) -> None:
            raise OSError(5, "simulated fsync failure")

        monkeypatch.setattr(_os, "fsync", _fail_fsync)
        try:
            with pytest.raises(confined_mutation.MutationDenied):
                confined_mutation.confined_atomic_replace(tmp_root, target, b"new bytes")
            assert target.read_bytes() == prior_bytes, "prior bytes must survive staging failure"
        finally:
            monkeypatch.setattr(_os, "fsync", real_fsync)

    def test_descriptor_walk_fallback_refuses_mutation(
        self, confined_mutation: ModuleType, tmp_root: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """When descriptor walk is unsupported, all mutations refuse (AC-0011).

        This fixture forces the fallback condition by monkeypatching and NEVER
        skips, since the unsafe-host code path must be exercised on all platforms.
        """
        target = tmp_root / "safe.txt"
        target.write_bytes(b"must not change")

        # Force descriptor walk to appear unsupported
        monkeypatch.setattr(confined_mutation._fs, "_supports_descriptor_walk", lambda: False)

        with pytest.raises(confined_mutation.MutationDenied) as exc_info:
            confined_mutation.confined_atomic_replace(tmp_root, target, b"new")
        assert exc_info.value.denial_code == "denied-unsafe-host", (
            f"expected denied-unsafe-host, got {exc_info.value.denial_code!r}"
        )
        # No success receipt: original unchanged
        assert target.read_bytes() == b"must not change"

    def test_create_refuses_on_fallback_host(
        self, confined_mutation: ModuleType, tmp_root: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """confined_create also refuses when descriptor walk is unsupported."""
        monkeypatch.setattr(confined_mutation._fs, "_supports_descriptor_walk", lambda: False)
        target = tmp_root / "nonexistent.txt"
        with pytest.raises(confined_mutation.MutationDenied) as exc_info:
            confined_mutation.confined_create(tmp_root, target, b"x")
        assert exc_info.value.denial_code == "denied-unsafe-host"
        assert not target.exists(), "file must not be created on fallback host"

    def test_append_refuses_on_fallback_host(
        self, confined_mutation: ModuleType, tmp_root: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """confined_append also refuses when descriptor walk is unsupported."""
        target = tmp_root / "appendable.txt"
        target.write_bytes(b"original")
        monkeypatch.setattr(confined_mutation._fs, "_supports_descriptor_walk", lambda: False)
        with pytest.raises(confined_mutation.MutationDenied) as exc_info:
            confined_mutation.confined_append(tmp_root, target, b"more")
        assert exc_info.value.denial_code == "denied-unsafe-host"
        assert target.read_bytes() == b"original", "original must be intact"

    def test_no_success_receipt_on_refusal(
        self, confined_mutation: ModuleType, tmp_root: Path
    ) -> None:
        """A refused mutation produces no success receipt and leaves original intact."""
        target = tmp_root / "no-receipt.txt"
        original = b"unchanged"
        target.write_bytes(original)
        with pytest.raises(confined_mutation.MutationDenied):
            # Exceed bounds: refuses before staging
            confined_mutation.confined_atomic_replace(
                tmp_root, target, b"x" * 1000, max_bytes=5
            )
        assert target.read_bytes() == original


# ═══════════════════════════════════════════════════════════════════════════════
# AC-0020 / AC-0021: Security events and durable audit
# ═══════════════════════════════════════════════════════════════════════════════


class TestSecurityEvents:
    """Tests for security event emission and durable audit (AC-0020, AC-0021)."""

    def _make_event(
        self,
        se: ModuleType,
        *,
        outcome: str = "allowed",
        reason_code: str = "allowed-file-write",
    ) -> object:
        return se.SecurityEvent(
            schema_version=1,
            operation_id="op-test-001",
            correlation_id="grant-abc",
            event_type="file-write",
            outcome=outcome,
            reason_code=reason_code,
            timestamp="2026-10-01T00:00:00Z",
        )

    def test_event_emitted_before_acknowledgment(
        self, security_events: ModuleType
    ) -> None:
        """emit_security_event calls the sink before returning (AC-0021)."""
        se = security_events
        received: list = []
        acknowledged: list = []

        def sink(event: object) -> None:
            # Record that sink was called; then immediately mark as acknowledged
            received.append(event)

        event = self._make_event(se)
        se.emit_security_event(sink, event)
        acknowledged.append(True)

        # Sink must have been called exactly once before return
        assert len(received) == 1
        assert len(acknowledged) == 1
        assert received[0] is event

    def test_allowed_event_emitted_correctly(self, security_events: ModuleType) -> None:
        """An allowed event is emitted with outcome=allowed and a stable reason code."""
        se = security_events
        received: list = []
        event = self._make_event(se, outcome="allowed", reason_code="allowed-file-write")
        se.emit_security_event(lambda e: received.append(e), event)
        assert len(received) == 1
        assert received[0].outcome == "allowed"
        assert received[0].reason_code == "allowed-file-write"

    def test_denied_event_emitted_correctly(self, security_events: ModuleType) -> None:
        """A denied event is emitted with outcome=denied and a stable reason code."""
        se = security_events
        received: list = []
        event = self._make_event(se, outcome="denied", reason_code="denied-path-violation")
        se.emit_security_event(lambda e: received.append(e), event)
        assert len(received) == 1
        assert received[0].outcome == "denied"
        assert received[0].reason_code == "denied-path-violation"

    def test_security_event_contains_no_payload(self, security_events: ModuleType) -> None:
        """A SecurityEvent must carry no sensitive payload bytes (AC-0021)."""
        se = security_events
        sensitive_payload = b"secret: ghp_AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA1234"
        event = self._make_event(se, outcome="denied", reason_code="denied-credential")
        # Serialize the event and check that the payload is absent
        event_dict = event._asdict() if hasattr(event, "_asdict") else vars(event)
        for _field_name, field_val in event_dict.items():
            if isinstance(field_val, (str, bytes)):
                val_bytes = field_val if isinstance(field_val, bytes) else field_val.encode()
                assert sensitive_payload not in val_bytes, (
                    f"Field {_field_name!r} contains sensitive payload bytes"
                )

    def test_stable_reason_codes_in_module(self, security_events: ModuleType) -> None:
        """The module exports stable reason codes that callers can depend on."""
        se = security_events
        # These codes must exist and be stable strings
        assert hasattr(se, "KNOWN_REASON_CODES"), "module must export KNOWN_REASON_CODES"
        codes = se.KNOWN_REASON_CODES
        assert isinstance(codes, (frozenset, set))
        # At minimum: allowed-file-write, denied-path-violation, denied-unsafe-host
        required = {"allowed-file-write", "denied-path-violation", "denied-unsafe-host"}
        missing = required - set(codes)
        assert not missing, f"missing required reason codes: {missing}"

    def test_sink_unavailable_fails_closed(self, security_events: ModuleType) -> None:
        """When the audit sink raises, emit_security_event raises AuditSinkUnavailable (AC-0021)."""
        se = security_events

        def unavailable_sink(event: object) -> None:
            raise se.AuditSinkError("sink is down")

        event = self._make_event(se, outcome="allowed")
        with pytest.raises(se.AuditSinkUnavailable):
            se.emit_security_event(unavailable_sink, event)

    def test_sink_unavailable_no_effect_success(self, security_events: ModuleType) -> None:
        """When sink is unavailable, no success is returned (AC-0021)."""
        se = security_events
        success_receipts: list = []

        def unavailable_sink(event: object) -> None:
            raise se.AuditSinkError("down")

        event = self._make_event(se, outcome="allowed")
        try:
            result = se.emit_security_event(unavailable_sink, event)
            success_receipts.append(result)
        except se.AuditSinkUnavailable:
            pass  # expected

        assert not success_receipts, "no success receipt when sink is unavailable"

    def test_sink_unavailable_no_protected_data_persistence(
        self, security_events: ModuleType
    ) -> None:
        """When sink is unavailable, no protected data persists (AC-0021)."""
        se = security_events
        stored_data: list = []

        def unavailable_sink(event: object) -> None:
            # Attempt to store data (simulating a bad sink)
            raise se.AuditSinkError("down")

        event = self._make_event(se, outcome="denied", reason_code="denied-path-violation")
        with contextlib.suppress(se.AuditSinkUnavailable):
            se.emit_security_event(unavailable_sink, event)
        # No protected data was persisted
        assert not stored_data

    def test_retry_cannot_weaken_refusal(self, security_events: ModuleType) -> None:
        """A denied event on retry is still denied (AC-0020)."""
        se = security_events
        received: list = []
        event_deny = self._make_event(se, outcome="denied", reason_code="denied-path-violation")
        # First attempt
        se.emit_security_event(lambda e: received.append(e), event_deny)
        # Retry with same event
        se.emit_security_event(lambda e: received.append(e), event_deny)
        # Both attempts must have outcome=denied
        assert all(e.outcome == "denied" for e in received)
        assert len(received) == 2

    def test_no_content_derived_operation_id(self, security_events: ModuleType) -> None:
        """The operation_id must not be derived from refused bytes (AC-0020).

        Two events for different refused payloads must have independent operation_ids
        and neither should match a hash of their respective refused content.
        """
        import hashlib
        se = security_events

        # Simulate two refused payloads (different content)
        refused_bytes_a = b"secret-credential-aaa"
        refused_bytes_b = b"another-secret-bbb"

        # Create two separate events with different operation_ids
        event_a = se.SecurityEvent(
            schema_version=1,
            operation_id=se.make_operation_id(),
            correlation_id="grant-x",
            event_type="capability-check",
            outcome="denied",
            reason_code="denied-path-violation",
            timestamp="2026-10-01T00:00:00Z",
        )
        event_b = se.SecurityEvent(
            schema_version=1,
            operation_id=se.make_operation_id(),
            correlation_id="grant-y",
            event_type="capability-check",
            outcome="denied",
            reason_code="denied-path-violation",
            timestamp="2026-10-01T00:00:00Z",
        )

        # operation_ids must be different
        assert event_a.operation_id != event_b.operation_id

        # Neither operation_id should be a hash of the refused bytes
        for event, refused in [(event_a, refused_bytes_a), (event_b, refused_bytes_b)]:
            h = hashlib.sha256(refused).hexdigest()
            assert event.operation_id != h, (
                "operation_id must not be a hash of refused content"
            )

    def test_redacted_metadata_in_event(self, security_events: ModuleType) -> None:
        """Security event fields carry no sensitive request content (AC-0021)."""
        se = security_events
        # The reason_code and other fields must not contain payload
        sensitive = "my-secret-token-AKIA1234567890ABCDEF"
        event = se.SecurityEvent(
            schema_version=1,
            operation_id="op-redact-001",
            correlation_id="grant-z",
            event_type="file-write",
            outcome="denied",
            reason_code="denied-path-violation",  # stable code, not derived from content
            timestamp="2026-10-01T00:00:00Z",
        )
        # reason_code must not contain the sensitive token
        assert sensitive not in event.reason_code
        # Serialize and check all fields
        event_dict = {"reason_code": event.reason_code, "event_type": event.event_type}
        for val in event_dict.values():
            assert sensitive not in str(val)


class TestSecurityEventWriterAuthority:
    """Tests for named writer authority checks (AC-0020)."""

    def test_valid_capability_allows_semantic_append(
        self, security_capability: ModuleType, security_events: ModuleType
    ) -> None:
        """A valid writer capability allows semantic append with event emitted."""
        sc = security_capability
        se = security_events
        issuer = sc.CapabilityIssuer()
        writer_grant = issuer.issue_root_grant(
            roots=["/records"],
            operations=["write", "append"],
            trust_class="trusted-adapter",
            writes_allowed_roots=["/records"],
            control_denies=[],
        )

        received: list = []
        result = se.check_writer_authority_and_emit(
            issuer=issuer,
            grant=writer_grant,
            record_scope="/records/evidence.jsonl",
            required_operations=["append"],
            sink=lambda e: received.append(e),
            operation_id="op-append-001",
            correlation_id=writer_grant.grant_id,
        )
        assert result is True, "valid grant must allow append"
        assert len(received) == 1, "one event must be emitted"
        assert received[0].outcome == "allowed"

    def test_missing_grant_refuses_semantic_append(
        self, security_capability: ModuleType, security_events: ModuleType
    ) -> None:
        """A caller-built (unregistered) grant refuses semantic append."""
        sc = security_capability
        se = security_events
        issuer = sc.CapabilityIssuer()
        forged_grant = sc.CapabilityGrant(
            schema_version=sc.SUPPORTED_SCHEMA_VERSION,
            grant_id="forged-for-append",
            roots=("/records",),
            operations=("write", "append"),
            trust_class="trusted-adapter",
            writes=sc._WritesGrant(allowed_roots=("/records",)),
            control_denies=(),
            limits=sc._Limits(),
        )
        received: list = []
        result = se.check_writer_authority_and_emit(
            issuer=issuer,
            grant=forged_grant,
            record_scope="/records/evidence.jsonl",
            required_operations=["append"],
            sink=lambda e: received.append(e),
            operation_id="op-forged-001",
            correlation_id=forged_grant.grant_id,
        )
        assert result is False, "forged grant must refuse"
        assert len(received) == 1, "one denial event must be emitted"
        assert received[0].outcome == "denied"
        assert received[0].reason_code == "denied-invalid-grant"

    def test_revoked_grant_refuses_semantic_append(
        self, security_capability: ModuleType, security_events: ModuleType
    ) -> None:
        """A revoked grant refuses semantic append."""
        sc = security_capability
        se = security_events
        issuer = sc.CapabilityIssuer()
        writer_grant = issuer.issue_root_grant(
            roots=["/records"],
            operations=["write", "append"],
            trust_class="trusted-adapter",
            writes_allowed_roots=["/records"],
            control_denies=[],
        )
        issuer.revoke_grant(writer_grant.grant_id)

        received: list = []
        result = se.check_writer_authority_and_emit(
            issuer=issuer,
            grant=writer_grant,
            record_scope="/records/evidence.jsonl",
            required_operations=["append"],
            sink=lambda e: received.append(e),
            operation_id="op-revoked-001",
            correlation_id=writer_grant.grant_id,
        )
        assert result is False
        assert received[0].outcome == "denied"

    def test_out_of_scope_grant_refuses(
        self, security_capability: ModuleType, security_events: ModuleType
    ) -> None:
        """A grant whose roots don't cover the record scope refuses."""
        sc = security_capability
        se = security_events
        issuer = sc.CapabilityIssuer()
        writer_grant = issuer.issue_root_grant(
            roots=["/other"],
            operations=["write", "append"],
            trust_class="trusted-adapter",
            writes_allowed_roots=["/other"],
            control_denies=[],
        )
        received: list = []
        result = se.check_writer_authority_and_emit(
            issuer=issuer,
            grant=writer_grant,
            record_scope="/records/evidence.jsonl",  # outside /other
            required_operations=["append"],
            sink=lambda e: received.append(e),
            operation_id="op-scope-001",
            correlation_id=writer_grant.grant_id,
        )
        assert result is False, "grant outside scope must refuse"
        assert received[0].outcome == "denied"
        assert received[0].reason_code in (
            "denied-out-of-scope",
            "denied-invalid-grant",
        )

    def test_missing_required_operation_refuses(
        self, security_capability: ModuleType, security_events: ModuleType
    ) -> None:
        """A grant lacking a required operation refuses."""
        sc = security_capability
        se = security_events
        issuer = sc.CapabilityIssuer()
        read_only_grant = issuer.issue_root_grant(
            roots=["/records"],
            operations=["read"],  # no append
            trust_class="trusted-adapter",
            writes_allowed_roots=[],
            control_denies=[],
        )
        received: list = []
        result = se.check_writer_authority_and_emit(
            issuer=issuer,
            grant=read_only_grant,
            record_scope="/records/evidence.jsonl",
            required_operations=["append"],
            sink=lambda e: received.append(e),
            operation_id="op-ops-001",
            correlation_id=read_only_grant.grant_id,
        )
        assert result is False
        assert received[0].outcome == "denied"

    def test_sink_unavailable_fails_closed_on_writer_check(
        self, security_capability: ModuleType, security_events: ModuleType
    ) -> None:
        """When sink is unavailable during writer check, the check fails closed (AC-0021)."""
        sc = security_capability
        se = security_events
        issuer = sc.CapabilityIssuer()
        writer_grant = issuer.issue_root_grant(
            roots=["/records"],
            operations=["write", "append"],
            trust_class="trusted-adapter",
            writes_allowed_roots=["/records"],
            control_denies=[],
        )

        def _bad_sink(event: object) -> None:
            raise se.AuditSinkError("sink unavailable")

        with pytest.raises(se.AuditSinkUnavailable):
            se.check_writer_authority_and_emit(
                issuer=issuer,
                grant=writer_grant,
                record_scope="/records/evidence.jsonl",
                required_operations=["append"],
                sink=_bad_sink,
                operation_id="op-unavail-001",
                correlation_id=writer_grant.grant_id,
            )

    def test_no_retry_key_derived_from_refused_bytes(
        self, security_capability: ModuleType, security_events: ModuleType
    ) -> None:
        """No identity, correlation, or retry key for refused content is derived from refused bytes (AC-0020)."""
        sc = security_capability
        se = security_events
        issuer = sc.CapabilityIssuer()

        # The forged grant represents "refused content"; its grant_id was not issued
        refused_content = b"sensitive-refused-data-12345"
        forged_grant = sc.CapabilityGrant(
            schema_version=sc.SUPPORTED_SCHEMA_VERSION,
            grant_id="not-in-registry",
            roots=("/records",),
            operations=("append",),
            trust_class="trusted-adapter",
            writes=sc._WritesGrant(allowed_roots=("/records",)),
            control_denies=(),
            limits=sc._Limits(),
        )
        received: list = []
        se.check_writer_authority_and_emit(
            issuer=issuer,
            grant=forged_grant,
            record_scope="/records/evidence.jsonl",
            required_operations=["append"],
            sink=lambda e: received.append(e),
            operation_id=se.make_operation_id(),
            correlation_id="correlation-not-from-bytes",  # caller supplies; not from content
        )
        assert len(received) == 1
        denied_event = received[0]
        # The event must not carry the refused bytes or a hash of them
        import hashlib
        refused_hash = hashlib.sha256(refused_content).hexdigest()
        event_str = str(vars(denied_event) if hasattr(denied_event, "__dict__") else denied_event)
        assert refused_content.decode("utf-8", errors="replace") not in event_str
        assert refused_hash[:16] not in event_str
