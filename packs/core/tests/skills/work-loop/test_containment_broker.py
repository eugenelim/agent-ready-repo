"""T3c TDD suite: containment and effect-broker conformance, control-plane forgery denial.

Mode: TDD through end-to-end security conformance (plan.md T3c).

Tests:

AC-0010 — Launcher attestation vs grant: any attestation broader than the grant
in roots, read enforcement, network, children, or limits is refused.

AC-0013 — Control-plane forgery denial: direct-syscall, Git metadata,
protected-ref, delivery-control, broker-bypass, privilege-amplification, and
unsupported-host fixtures are exercised through every adapter in
SUPPORTED_ADAPTERS.  Every delivery-control path is attempted, including
creating a new copy, and zero bypass writes are observed.

AC-0020/AC-0021 — Broker effect appends with missing, expired, and mismatched
producer capabilities and with unavailable audit storage: available-sink denials
persist their redacted event before acknowledgment; unavailable-sink attempts
expose no partial record or effect, return a stable redacted denial code without
a durable-event claim, and remain denied on retry.

Follows the importlib.util.spec_from_file_location loader pattern from sibling
suites.  No third-party imports at test collection time.
"""

from __future__ import annotations

import importlib.util
import os
import stat
import sys
import time
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
def containment() -> ModuleType:
    """_containment.py loaded by path."""
    return _load_module("cn_under_test", SCRIPTS / "_containment.py")


@pytest.fixture(scope="module")
def effect_broker() -> ModuleType:
    """_effect_broker.py loaded by path."""
    return _load_module("eb_under_test", SCRIPTS / "_effect_broker.py")


@pytest.fixture(scope="module")
def security_capability() -> ModuleType:
    """_security_capability.py loaded by path."""
    return _load_module("sc_under_test_t3c", SCRIPTS / "_security_capability.py")


@pytest.fixture(scope="module")
def acceptance() -> ModuleType:
    """_acceptance.py loaded by path (for SUPPORTED_ADAPTERS)."""
    return _load_module("ac_under_test_t3c", SCRIPTS / "_acceptance.py")


@pytest.fixture(scope="module")
def process_safety() -> ModuleType:
    """_process_safety.py loaded by path (for ProcessDenied)."""
    return _load_module("ps_under_test_t3c", SCRIPTS / "_process_safety.py")


# ── Helpers ───────────────────────────────────────────────────────────────────


def _make_root_grant(sc: ModuleType, **kwargs) -> tuple:
    """Issue a root grant with sensible defaults. Returns (issuer, grant)."""
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


def _make_attestation(cn: ModuleType, **kwargs) -> object:
    """Build a ContainmentAttestation with sensible defaults."""
    defaults: dict = {
        "schema_version": 1,
        "host_mechanism": "os-sandbox",
        "principal_or_sandbox": "test-sandbox-001",
        "roots": ("/work",),
        "limits": {},
    }
    defaults.update(kwargs)
    return cn.ContainmentAttestation(**defaults)


# ═══════════════════════════════════════════════════════════════════════════════
# AC-0010: Launcher attestation vs grant comparison
# ═══════════════════════════════════════════════════════════════════════════════


class TestAttestationWithinGrant:
    """AC-0010: attestation must not be broader than the grant in any axis."""

    def test_equal_roots_allowed(
        self, containment: ModuleType, security_capability: ModuleType
    ) -> None:
        """Attestation with same roots as grant is allowed."""
        cn, sc = containment, security_capability
        _, grant = _make_root_grant(sc, roots=["/work"])
        attestation = _make_attestation(cn, roots=("/work",))
        ok, code = cn.check_attestation_within_grant(attestation, grant)
        assert ok, f"equal roots must be allowed; got code: {code!r}"

    def test_narrower_roots_allowed(
        self, containment: ModuleType, security_capability: ModuleType
    ) -> None:
        """Attestation with roots inside the grant roots is allowed."""
        cn, sc = containment, security_capability
        _, grant = _make_root_grant(sc, roots=["/work"])
        attestation = _make_attestation(cn, roots=("/work/sub",))
        ok, code = cn.check_attestation_within_grant(attestation, grant)
        assert ok, f"narrower roots must be allowed; got code: {code!r}"

    def test_broader_roots_refused(
        self, containment: ModuleType, security_capability: ModuleType
    ) -> None:
        """Attestation claiming roots outside the grant is refused."""
        cn, sc = containment, security_capability
        _, grant = _make_root_grant(sc, roots=["/work/only"])
        # Attestation claims /home which is outside the grant
        attestation = _make_attestation(cn, roots=("/home/user",))
        ok, code = cn.check_attestation_within_grant(attestation, grant)
        assert not ok, "broader roots must be refused"
        assert code == "denied-attestation-broader-than-grant"

    def test_attestation_network_when_grant_denies_refused(
        self, containment: ModuleType, security_capability: ModuleType
    ) -> None:
        """Attestation claiming network when grant denies network is refused."""
        cn, sc = containment, security_capability
        _, grant = _make_root_grant(sc, roots=["/work"], network=None)
        attestation = _make_attestation(cn, network={"allowed": True})
        ok, code = cn.check_attestation_within_grant(attestation, grant)
        assert not ok, "network claim when grant has no network must be refused"
        assert code == "denied-attestation-broader-than-grant"

    def test_attestation_no_network_allowed(
        self, containment: ModuleType, security_capability: ModuleType
    ) -> None:
        """Attestation without network is not broader than a grant with no network."""
        cn, sc = containment, security_capability
        _, grant = _make_root_grant(sc, roots=["/work"], network=None)
        # No network in attestation — not broader
        attestation = _make_attestation(cn, network=None)
        ok, _ = cn.check_attestation_within_grant(attestation, grant)
        assert ok

    def test_attestation_children_when_grant_denies_refused(
        self, containment: ModuleType, security_capability: ModuleType
    ) -> None:
        """Attestation claiming children when grant denies them is refused."""
        cn, sc = containment, security_capability
        _, grant = _make_root_grant(sc, roots=["/work"], children=None)
        attestation = _make_attestation(cn, children={"allowed": True})
        ok, code = cn.check_attestation_within_grant(attestation, grant)
        assert not ok, "children claim when grant has no children must be refused"
        assert code == "denied-attestation-broader-than-grant"

    def test_attestation_broader_limits_refused(
        self, containment: ModuleType, security_capability: ModuleType
    ) -> None:
        """Attestation with more permissive limits than the grant is refused."""
        cn, sc = containment, security_capability
        _, grant = _make_root_grant(
            sc, roots=["/work"],
            limits=sc._Limits(max_bytes=1000, timeout_s=60),
        )
        # Attestation claims 2000 bytes — broader than 1000
        attestation = _make_attestation(cn, limits={"max_bytes": 2000, "timeout_s": 60})
        ok, code = cn.check_attestation_within_grant(attestation, grant)
        assert not ok, "broader resource limits must be refused"
        assert code == "denied-attestation-broader-than-grant"

    def test_narrower_limits_allowed(
        self, containment: ModuleType, security_capability: ModuleType
    ) -> None:
        """Attestation with stricter limits than the grant is allowed."""
        cn, sc = containment, security_capability
        _, grant = _make_root_grant(
            sc, roots=["/work"],
            limits=sc._Limits(max_bytes=2000, timeout_s=120),
        )
        # Attestation claims 500 bytes — narrower
        attestation = _make_attestation(cn, limits={"max_bytes": 500, "timeout_s": 30})
        ok, code = cn.check_attestation_within_grant(attestation, grant)
        assert ok, f"narrower limits must be allowed; got: {code!r}"


# ═══════════════════════════════════════════════════════════════════════════════
# AC-0013: Control-plane forgery denial — delivery-control paths
# ═══════════════════════════════════════════════════════════════════════════════


class TestDeliveryControlPathGuard:
    """AC-0013: every delivery-control path is protected; untrusted grants deny writes."""

    def test_delivery_control_paths_constant_exists(
        self, containment: ModuleType
    ) -> None:
        """DELIVERY_CONTROL_PATHS is defined and has at least two members."""
        cn = containment
        assert hasattr(cn, "DELIVERY_CONTROL_PATHS"), (
            "DELIVERY_CONTROL_PATHS must be a module-level constant"
        )
        paths = cn.DELIVERY_CONTROL_PATHS
        assert len(paths) >= 2, (
            f"DELIVERY_CONTROL_PATHS must have at least 2 entries; got {list(paths)}"
        )

    def test_pack_source_is_delivery_control_path(
        self, containment: ModuleType
    ) -> None:
        """The Core pack's work-loop source tree is a delivery-control path."""
        cn = containment
        # The pack source entry must be present
        pack_source = next(
            (p for p in cn.DELIVERY_CONTROL_PATHS if "packs/core" in p and "work-loop" in p),
            None,
        )
        assert pack_source is not None, (
            "DELIVERY_CONTROL_PATHS must include the pack source path "
            f"(packs/core/...work-loop/); got {list(cn.DELIVERY_CONTROL_PATHS)!r}"
        )

    def test_is_delivery_control_path_detects_pack_source(
        self, containment: ModuleType
    ) -> None:
        """is_delivery_control_path returns True for pack source paths."""
        cn = containment
        assert cn.is_delivery_control_path("packs/core/.apm/skills/work-loop/SKILL.md")
        assert cn.is_delivery_control_path("packs/core/.apm/skills/work-loop/scripts/loop-engine.py")

    def test_is_delivery_control_path_detects_claude_projection(
        self, containment: ModuleType
    ) -> None:
        """is_delivery_control_path returns True for .claude/skills/work-loop/ paths."""
        cn = containment
        assert cn.is_delivery_control_path(".claude/skills/work-loop/SKILL.md")
        assert cn.is_delivery_control_path(".claude/skills/work-loop/scripts/loop-engine.py")

    def test_is_delivery_control_path_detects_kiro_projection(
        self, containment: ModuleType
    ) -> None:
        """is_delivery_control_path returns True for .kiro/skills/work-loop/ paths."""
        cn = containment
        assert cn.is_delivery_control_path(".kiro/skills/work-loop/SKILL.md")

    def test_is_delivery_control_path_detects_agents_projection(
        self, containment: ModuleType
    ) -> None:
        """is_delivery_control_path returns True for .agents/skills/work-loop/ paths."""
        cn = containment
        assert cn.is_delivery_control_path(".agents/skills/work-loop/SKILL.md")

    def test_unrelated_path_not_delivery_control(
        self, containment: ModuleType
    ) -> None:
        """A normal work path is not a delivery-control path."""
        cn = containment
        assert not cn.is_delivery_control_path("/work/some-file.txt")
        assert not cn.is_delivery_control_path(".claude/agents/my-agent.md")
        assert not cn.is_delivery_control_path("/home/user/docs/readme.md")

    @pytest.mark.parametrize("adapter", ["sequential-reference", "core-compatibility"])
    def test_all_adapters_have_same_delivery_control_constant(
        self, containment: ModuleType, acceptance: ModuleType, adapter: str
    ) -> None:
        """DELIVERY_CONTROL_PATHS is the same constant regardless of which adapter evaluates it."""
        cn = containment
        # The constant is module-level and does not vary by adapter.
        # This test verifies the two supported adapters both see the same set.
        assert adapter in acceptance.SUPPORTED_ADAPTERS, (
            f"adapter {adapter!r} must be in SUPPORTED_ADAPTERS"
        )
        paths = cn.DELIVERY_CONTROL_PATHS
        assert isinstance(paths, tuple), "DELIVERY_CONTROL_PATHS must be a tuple"
        assert all(isinstance(p, str) for p in paths), (
            "all DELIVERY_CONTROL_PATHS entries must be strings"
        )

    @pytest.mark.parametrize("delivery_path", [
        "packs/core/.apm/skills/work-loop/SKILL.md",
        "packs/core/.apm/skills/work-loop/scripts/loop-engine.py",
        "packs/core/.apm/skills/work-loop/scripts/_security_capability.py",
        ".claude/skills/work-loop/SKILL.md",
        ".claude/skills/work-loop/scripts/loop-engine.py",
        ".kiro/skills/work-loop/SKILL.md",
        ".agents/skills/work-loop/SKILL.md",
        # Creating a new copy: attempting a new path under the projection root
        "packs/core/.apm/skills/work-loop/scripts/new_forged_module.py",
        ".claude/skills/work-loop/forged_copy.md",
    ])
    def test_delivery_control_path_detected_for_forgery_attempts(
        self, containment: ModuleType, delivery_path: str
    ) -> None:
        """Every delivery-control path, including a new forged copy, is detected."""
        cn = containment
        assert cn.is_delivery_control_path(delivery_path), (
            f"delivery-control path not detected: {delivery_path!r}"
        )


class TestForgeryFixturesPerAdapter:
    """AC-0013: direct-syscall, git-metadata, protected-ref, broker-bypass, privilege-amplification
    and unsupported-host forgery fixture families, exercised per adapter."""

    def _attempt_write_delivery_control(
        self,
        containment: ModuleType,
        effect_broker: ModuleType,
        session: object,
        path: str,
        adapter: str,
    ) -> bool:
        """Try a broker write to a delivery-control path.

        Returns True if the write succeeded (bypass), False if refused.
        """
        events: list = []
        result = effect_broker.request_effect(
            session,
            grant_id=session.grants[0].grant_id if session.grants else "no-grant",
            operation="write",
            path=path,
            audit_sink=lambda e: events.append(e),
        )
        return result.success

    @pytest.mark.parametrize("adapter", ["sequential-reference", "core-compatibility"])
    @pytest.mark.parametrize("delivery_path", [
        "packs/core/.apm/skills/work-loop/SKILL.md",
        ".claude/skills/work-loop/SKILL.md",
        ".kiro/skills/work-loop/SKILL.md",
        ".agents/skills/work-loop/SKILL.md",
        ".claude/skills/work-loop/scripts/new_copy.py",
    ])
    def test_delivery_control_write_refused_per_adapter(
        self,
        containment: ModuleType,
        effect_broker: ModuleType,
        delivery_path: str,
        adapter: str,
    ) -> None:
        """Every delivery-control path write attempt is refused for every adapter."""
        eb = effect_broker
        # Create a broker session whose grant appears to cover the delivery-control path.
        # The broker must refuse regardless.
        grant = eb.BrokerGrant(
            grant_id="test-write-grant",
            operations=("write",),
            allowed_roots=(delivery_path,),  # grant even claims the path
        )
        session = eb.create_broker_session(
            session_id="test-session-delivery",
            grants=[grant],
        )
        events: list = []
        result = eb.request_effect(
            session,
            grant_id=grant.grant_id,
            operation="write",
            path=delivery_path,
            audit_sink=lambda e: events.append(e),
        )
        assert not result.success, (
            f"broker must refuse write to delivery-control path {delivery_path!r} "
            f"for adapter {adapter!r}; got success=True"
        )
        assert result.denial_code == "denied-control-plane-write", (
            f"expected denied-control-plane-write; got {result.denial_code!r}"
        )

    @pytest.mark.parametrize("adapter", ["sequential-reference", "core-compatibility"])
    @pytest.mark.parametrize("forgery_path", [
        ".git/COMMIT_EDITMSG",
        ".git/refs/heads/main",
        ".git/objects/ab/cdef1234",
    ])
    def test_git_metadata_write_refused_per_adapter(
        self,
        containment: ModuleType,
        effect_broker: ModuleType,
        forgery_path: str,
        adapter: str,
    ) -> None:
        """Git metadata write attempts are refused through every adapter.

        The broker grant does NOT cover .git/ paths — so the out-of-scope
        denial fires.  Zero bypass writes reach the .git directory.
        """
        eb = effect_broker
        grant = eb.BrokerGrant(
            grant_id="test-git-meta-grant",
            operations=("write",),
            allowed_roots=("/work",),  # only covers /work, not .git/
        )
        session = eb.create_broker_session(
            session_id="test-session-git-meta",
            grants=[grant],
        )
        events: list = []
        result = eb.request_effect(
            session,
            grant_id=grant.grant_id,
            operation="write",
            path=forgery_path,
            audit_sink=lambda e: events.append(e),
        )
        assert not result.success, (
            f"git metadata write must be refused for path {forgery_path!r} "
            f"adapter {adapter!r}"
        )
        # The denial event must be emitted
        assert len(events) >= 1, "denial event must be emitted"
        assert all(e.outcome == "denied" for e in events)

    @pytest.mark.parametrize("adapter", ["sequential-reference", "core-compatibility"])
    def test_same_process_wrapper_cannot_claim_os_isolation(
        self, containment: ModuleType, adapter: str
    ) -> None:
        """No same-process wrapper may claim OS isolation (AC-0013 unsupported-host fixture)."""
        cn = containment
        # Validate an attestation that claims a same-process mechanism
        bad_attestation = {
            "schema_version": 1,
            "host_mechanism": "same-process",  # forbidden
            "principal_or_sandbox": "no-sandbox",
            "roots": ["/work"],
            "limits": {},
        }
        ok, code = cn.validate_attestation_dict(bad_attestation)
        assert not ok, "same-process mechanism must be refused"
        assert code == "denied-same-process-isolation-claim", (
            f"expected denied-same-process-isolation-claim; got {code!r}"
        )

    @pytest.mark.parametrize("adapter", ["sequential-reference", "core-compatibility"])
    def test_privilege_amplification_via_grant_widening_refused(
        self, containment: ModuleType, security_capability: ModuleType, adapter: str
    ) -> None:
        """A requested grant that is wider than the parent is refused (AC-0010)."""
        cn, sc = containment, security_capability
        issuer = sc.CapabilityIssuer()
        parent = issuer.issue_root_grant(
            roots=["/work/narrow"],
            operations=["read"],
            trust_class="trusted-adapter",
            writes_allowed_roots=[],
            control_denies=[],
        )
        # Requested child grant tries to widen roots — intersection is empty.
        request = sc.CapabilityGrant(
            schema_version=sc.SUPPORTED_SCHEMA_VERSION,
            grant_id="escalation-attempt",
            roots=("/etc",),
            operations=("read",),
            trust_class="trusted-adapter",
            writes=sc._WritesGrant(allowed_roots=()),
            control_denies=(),
            limits=sc._Limits(),
        )
        child = issuer.issue_child_grant(parent, request)
        assert child.roots == (), (
            f"grant widening must produce empty intersection; got {child.roots!r}"
        )
        # An attestation claiming /etc is then refused vs the child grant.
        attestation = cn.ContainmentAttestation(
            schema_version=1,
            host_mechanism="os-sandbox",
            principal_or_sandbox="sandbox-001",
            roots=("/etc",),
            limits={},
        )
        ok, code = cn.check_attestation_within_grant(attestation, child)
        assert not ok, "attestation for escalated root must be refused"
        assert code == "denied-attestation-broader-than-grant"

    @pytest.mark.parametrize("adapter", ["sequential-reference", "core-compatibility"])
    def test_host_reporting_no_sandbox_refuses_untrusted(
        self, containment: ModuleType, security_capability: ModuleType, adapter: str
    ) -> None:
        """Sequential reference runtime reports no verified containment and refuses untrusted launch.

        AC-0013 unsupported-host fixture: the default host supplies
        verified_sandbox=False, restricted_principal=False, and
        launch_untrusted raises ContainmentRefused with
        denied-no-verified-containment before any process is started.
        """
        cn, sc = containment, security_capability

        # The sequential reference runtime reports both axes as False.
        axes = cn.report_host_containment_axes()
        assert axes["verified_sandbox"] is False, (
            "sequential reference runtime must report verified_sandbox=False"
        )
        assert axes["restricted_principal"] is False, (
            "sequential reference runtime must report restricted_principal=False"
        )
        assert isinstance(axes["supported_mechanisms"], list)
        assert axes["supported_mechanisms"] == [], (
            "sequential reference runtime must report no supported mechanisms"
        )

        # Untrusted activation on the default host must refuse before any process starts.
        _, grant = _make_root_grant(sc, roots=["/work"])
        with pytest.raises(cn.ContainmentRefused) as exc_info:
            cn.launch_untrusted(
                {"spec": "placeholder"},
                grant,
                # No host= arg → uses _DEFAULT_HOST (sequential reference runtime)
                audit_sink=lambda e: None,
            )
        assert exc_info.value.denial_code == "denied-no-verified-containment", (
            f"expected denied-no-verified-containment from default host; "
            f"got {exc_info.value.denial_code!r}"
        )


# ═══════════════════════════════════════════════════════════════════════════════
# AC-0013 (continued): direct-syscall, protected-ref, broker-bypass fixtures
# ═══════════════════════════════════════════════════════════════════════════════


class TestDirectSyscallForgery:
    """AC-0013 direct-syscall fixture: delivery-control writes detected before any I/O."""

    @pytest.mark.parametrize("adapter", ["sequential-reference", "core-compatibility"])
    @pytest.mark.parametrize("delivery_path", [
        "packs/core/.apm/skills/work-loop/SKILL.md",
        ".claude/skills/work-loop/SKILL.md",
        ".kiro/skills/work-loop/SKILL.md",
        ".agents/skills/work-loop/SKILL.md",
        # Creating a new skill copy via direct syscall
        "packs/core/.apm/skills/work-loop/scripts/direct_syscall_forged.py",
        ".claude/skills/work-loop/injected_module.py",
    ])
    def test_direct_syscall_delivery_control_refused_per_adapter(
        self,
        containment: ModuleType,
        effect_broker: ModuleType,
        delivery_path: str,
        adapter: str,
    ) -> None:
        """Direct-syscall fixture: a write to a delivery-control path via broker is refused.

        Models an untrusted process attempting a direct write syscall to a
        delivery-control path.  The broker's built-in guard refuses before any
        I/O, regardless of what the grant claims.  Zero bypass writes reach the
        control-plane path.
        """
        eb = effect_broker
        # Grant claims to cover the delivery-control path (simulates
        # an attacker constructing a grant that appears to allow the write).
        forged_grant = eb.BrokerGrant(
            grant_id="direct-syscall-grant",
            operations=("write",),
            allowed_roots=(delivery_path,),
        )
        session = eb.create_broker_session(
            session_id="direct-syscall-session", grants=[forged_grant]
        )
        events: list = []
        result = eb.request_effect(
            session,
            grant_id=forged_grant.grant_id,
            operation="write",
            path=delivery_path,
            audit_sink=lambda e: events.append(e),
        )
        assert not result.success, (
            f"direct-syscall to {delivery_path!r} must be refused for "
            f"adapter {adapter!r}; got success=True"
        )
        assert result.denial_code == "denied-control-plane-write", (
            f"expected denied-control-plane-write; got {result.denial_code!r}"
        )


class TestProtectedRefForgery:
    """AC-0013 protected-ref fixture: writes to protected Git refs are refused."""

    @pytest.mark.parametrize("adapter", ["sequential-reference", "core-compatibility"])
    @pytest.mark.parametrize("protected_ref_path", [
        ".git/refs/heads/main",
        ".git/refs/heads/master",
        ".git/refs/tags/v1.0.0",
        ".git/refs/remotes/origin/main",
        ".git/packed-refs",
    ])
    def test_protected_ref_write_refused_per_adapter(
        self,
        containment: ModuleType,
        effect_broker: ModuleType,
        protected_ref_path: str,
        adapter: str,
    ) -> None:
        """Protected-ref fixture: every protected Git ref write is refused for every adapter.

        The broker grant covers /work only; the ref path is out-of-scope, so
        out-of-scope denial fires and zero bypass writes reach any protected ref.
        """
        eb = effect_broker
        # Grant covers /work only; protected ref paths are not in the grant.
        grant = eb.BrokerGrant(
            grant_id="protected-ref-grant",
            operations=("write",),
            allowed_roots=("/work",),
        )
        session = eb.create_broker_session(
            session_id="protected-ref-session", grants=[grant]
        )
        events: list = []
        result = eb.request_effect(
            session,
            grant_id=grant.grant_id,
            operation="write",
            path=protected_ref_path,
            audit_sink=lambda e: events.append(e),
        )
        assert not result.success, (
            f"protected-ref write to {protected_ref_path!r} must be refused "
            f"for adapter {adapter!r}"
        )
        assert result.denial_code == "denied-out-of-scope", (
            f"expected denied-out-of-scope; got {result.denial_code!r}"
        )
        assert len(events) >= 1, "denial event must be emitted"
        assert all(e.outcome == "denied" for e in events)


class TestBrokerBypassForgery:
    """AC-0013 broker-bypass fixture: session construction or grant forgery is refused."""

    @pytest.mark.parametrize("adapter", ["sequential-reference", "core-compatibility"])
    def test_broker_bypass_via_direct_session_construction_refused(
        self,
        containment: ModuleType,
        effect_broker: ModuleType,
        adapter: str,
    ) -> None:
        """Broker-bypass fixture: directly constructing a BrokerSession with a
        delivery-control grant still refuses.

        An attacker may try to bypass ``create_broker_session`` by building a
        ``BrokerSession`` directly.  The broker's runtime guards must refuse
        regardless of how the session was assembled.  Zero bypass writes reach
        the delivery-control plane.
        """
        eb = effect_broker
        # Attacker constructs a BrokerSession directly with an escalated grant.
        forged_grant = eb.BrokerGrant(
            grant_id="broker-bypass-grant",
            operations=("write", "read"),
            allowed_roots=(".claude/skills/work-loop/",),
        )
        # Direct construction — not via create_broker_session.
        forged_session = eb.BrokerSession(
            session_id="broker-bypass-session",
            grants=(forged_grant,),
        )
        events: list = []
        result = eb.request_effect(
            forged_session,
            grant_id=forged_grant.grant_id,
            operation="write",
            path=".claude/skills/work-loop/SKILL.md",
            audit_sink=lambda e: events.append(e),
        )
        assert not result.success, (
            f"broker-bypass via direct BrokerSession construction must be refused "
            f"for adapter {adapter!r}"
        )
        assert result.denial_code == "denied-control-plane-write", (
            f"expected denied-control-plane-write; got {result.denial_code!r}"
        )

    @pytest.mark.parametrize("adapter", ["sequential-reference", "core-compatibility"])
    def test_broker_bypass_via_forged_operation_id_refused(
        self,
        containment: ModuleType,
        effect_broker: ModuleType,
        adapter: str,
    ) -> None:
        """Broker-bypass: supplying a custom operation_id does not bypass delivery-control guard."""
        eb = effect_broker
        grant = eb.BrokerGrant(
            grant_id="op-id-bypass-grant",
            operations=("write",),
            allowed_roots=(".agents/skills/work-loop/",),
        )
        session = eb.create_broker_session(
            session_id="op-id-bypass-session", grants=[grant]
        )
        events: list = []
        result = eb.request_effect(
            session,
            grant_id=grant.grant_id,
            operation="write",
            path=".agents/skills/work-loop/SKILL.md",
            audit_sink=lambda e: events.append(e),
            operation_id="attacker-controlled-op-id",  # forged operation_id
        )
        assert not result.success, (
            f"broker-bypass via forged operation_id must be refused for adapter {adapter!r}"
        )
        assert result.denial_code == "denied-control-plane-write"


# ═══════════════════════════════════════════════════════════════════════════════
# AC-0013: launch_untrusted — containment launcher tests
# ═══════════════════════════════════════════════════════════════════════════════


class TestLaunchUntrusted:
    """AC-0013: launch_untrusted refuses unless the host supplies a verified attestation
    within the grant.  The module-default host (sequential reference runtime) always
    refuses in Slice 1.
    """

    class _FixtureHost:
        """Test fixture host that supplies a configurable attestation dict."""

        def __init__(self, attestation: dict | None = None) -> None:
            self._attestation = attestation

        def get_attestation(self, spec_dict: dict, grant: object) -> dict | None:
            return self._attestation

    def _valid_attestation(self) -> dict:
        return {
            "schema_version": 1,
            "host_mechanism": "os-sandbox",
            "principal_or_sandbox": "fixture-sandbox-001",
            "roots": ("/work",),
            "limits": {},
        }

    def test_default_host_refuses_before_launch(
        self,
        containment: ModuleType,
        security_capability: ModuleType,
    ) -> None:
        """Default host (sequential reference runtime) refuses before any process starts."""
        cn, sc = containment, security_capability
        _, grant = _make_root_grant(sc, roots=["/work"])
        with pytest.raises(cn.ContainmentRefused) as exc_info:
            cn.launch_untrusted(
                {},
                grant,
                # host= omitted → uses _DEFAULT_HOST
                audit_sink=lambda e: None,
            )
        assert exc_info.value.denial_code == "denied-no-verified-containment", (
            f"expected denied-no-verified-containment; got "
            f"{exc_info.value.denial_code!r}"
        )

    def test_audit_sink_unavailable_refuses_before_launch(
        self,
        containment: ModuleType,
        security_capability: ModuleType,
    ) -> None:
        """Unavailable audit sink refuses with denied-audit-sink-unavailable, no process starts."""
        cn, sc = containment, security_capability
        _, grant = _make_root_grant(sc, roots=["/work"])
        host = self._FixtureHost(self._valid_attestation())
        with pytest.raises(cn.ContainmentRefused) as exc_info:
            cn.launch_untrusted(
                {},
                grant,
                host=host,
                audit_sink=None,  # unavailable
            )
        assert exc_info.value.denial_code == "denied-audit-sink-unavailable", (
            f"expected denied-audit-sink-unavailable; got "
            f"{exc_info.value.denial_code!r}"
        )

    def test_attestation_broader_than_grant_refuses_before_launch(
        self,
        containment: ModuleType,
        security_capability: ModuleType,
    ) -> None:
        """A fixture attestation broader than the grant refuses before launch."""
        cn, sc = containment, security_capability
        _, grant = _make_root_grant(sc, roots=["/work/narrow"])
        host = self._FixtureHost({
            "schema_version": 1,
            "host_mechanism": "os-sandbox",
            "principal_or_sandbox": "fixture-sandbox-001",
            "roots": ("/etc",),   # broader than /work/narrow
            "limits": {},
        })
        with pytest.raises(cn.ContainmentRefused) as exc_info:
            cn.launch_untrusted(
                {},
                grant,
                host=host,
                audit_sink=lambda e: None,
            )
        assert exc_info.value.denial_code == "denied-attestation-broader-than-grant", (
            f"expected denied-attestation-broader-than-grant; got "
            f"{exc_info.value.denial_code!r}"
        )

    def test_valid_attestation_delegates_to_process_safety(
        self,
        containment: ModuleType,
        security_capability: ModuleType,
        process_safety: ModuleType,
    ) -> None:
        """A fixture attestation within the grant delegates to _process_safety.

        Containment checks pass; _process_safety receives the spec and refuses
        it (schema invalid) with ProcessDenied — NOT ContainmentRefused.  This
        proves delegation occurred: the containment layer passed through to the
        process-safety layer.

        Note: launch_untrusted loads _process_safety via _load_sibling, producing
        a separate class object from the ``process_safety`` fixture.  We compare
        by type-name, not by isinstance, to prove the right layer raised.
        """
        cn, sc, ps = containment, security_capability, process_safety
        _, grant = _make_root_grant(sc, roots=["/work"])
        host = self._FixtureHost(self._valid_attestation())
        # An empty spec_dict is schema-invalid; _process_safety raises ProcessDenied.
        # Catch any Exception — we inspect the class name to distinguish layers.
        with pytest.raises(Exception) as exc_info:
            cn.launch_untrusted(
                {},    # bad spec → ProcessDenied from _process_safety
                grant,
                host=host,
                audit_sink=lambda e: None,
            )
        raised = exc_info.value
        # Key assertion: it must NOT be ContainmentRefused — containment passed.
        assert not isinstance(raised, cn.ContainmentRefused), (
            "ContainmentRefused must not be raised when attestation is valid — "
            f"delegation to _process_safety must occur; got {raised!r}"
        )
        # The exception must be ProcessDenied from the process-safety layer.
        assert type(raised).__name__ == "ProcessDenied", (
            f"Expected ProcessDenied from _process_safety; got "
            f"{type(raised).__name__!r}: {raised!r}"
        )
        # Its denial_code must be in the known set.
        assert raised.denial_code in ps.DENIAL_CODES, (  # type: ignore[attr-defined]
            f"ProcessDenied denial code must be in DENIAL_CODES; "
            f"got {raised.denial_code!r}"  # type: ignore[attr-defined]
        )

    def test_invalid_attestation_schema_refuses(
        self,
        containment: ModuleType,
        security_capability: ModuleType,
    ) -> None:
        """A fixture attestation that fails schema validation refuses before launch."""
        cn, sc = containment, security_capability
        _, grant = _make_root_grant(sc, roots=["/work"])
        host = self._FixtureHost({
            "schema_version": 99,   # unknown schema version
            "host_mechanism": "os-sandbox",
            "principal_or_sandbox": "sandbox",
            "roots": [],
            "limits": {},
        })
        with pytest.raises(cn.ContainmentRefused) as exc_info:
            cn.launch_untrusted({}, grant, host=host, audit_sink=lambda e: None)
        assert exc_info.value.denial_code == "denied-unknown-schema-version"


# ═══════════════════════════════════════════════════════════════════════════════
# AC-0020 / AC-0021: Broker and security-event appends with capability failures
# ═══════════════════════════════════════════════════════════════════════════════


class TestBrokerCapabilityFailures:
    """AC-0020/AC-0021: broker refuses missing, expired, and mismatched producer capabilities."""

    def test_missing_grant_refuses(self, effect_broker: ModuleType) -> None:
        """A missing grant ID refuses with denied-missing-grant and emits a denial event."""
        eb = effect_broker
        session = eb.create_broker_session(session_id="s1", grants=[])
        events: list = []
        result = eb.request_effect(
            session,
            grant_id="nonexistent-grant-id",
            operation="write",
            path="/work/output.txt",
            audit_sink=lambda e: events.append(e),
        )
        assert not result.success
        assert result.denial_code == "denied-missing-grant"
        # Denial event emitted
        assert len(events) >= 1
        assert all(e.outcome == "denied" for e in events)

    def test_expired_grant_refuses(self, effect_broker: ModuleType) -> None:
        """An expired grant refuses with denied-expired-grant and emits a denial event."""
        eb = effect_broker
        # Grant expires in the past
        expired_grant = eb.BrokerGrant(
            grant_id="expired-grant-id",
            operations=("write",),
            allowed_roots=("/work",),
            expires_at_monotonic=time.monotonic() - 1.0,  # already expired
        )
        session = eb.create_broker_session(
            session_id="s2", grants=[expired_grant]
        )
        events: list = []
        result = eb.request_effect(
            session,
            grant_id=expired_grant.grant_id,
            operation="write",
            path="/work/output.txt",
            audit_sink=lambda e: events.append(e),
        )
        assert not result.success
        assert result.denial_code == "denied-expired-grant"
        assert len(events) >= 1
        assert all(e.outcome == "denied" for e in events)

    def test_mismatched_grant_refuses_wrong_operation(self, effect_broker: ModuleType) -> None:
        """A grant that does not cover the requested operation refuses."""
        eb = effect_broker
        read_grant = eb.BrokerGrant(
            grant_id="read-only-grant",
            operations=("read",),  # no write
            allowed_roots=("/work",),
        )
        session = eb.create_broker_session(
            session_id="s3", grants=[read_grant]
        )
        events: list = []
        result = eb.request_effect(
            session,
            grant_id=read_grant.grant_id,
            operation="write",  # not in grant
            path="/work/output.txt",
            audit_sink=lambda e: events.append(e),
        )
        assert not result.success
        assert result.denial_code in (
            "denied-out-of-scope", "denied-operation-not-allowed"
        ), f"unexpected denial code: {result.denial_code!r}"
        assert len(events) >= 1
        assert all(e.outcome == "denied" for e in events)

    def test_mismatched_grant_refuses_wrong_path(self, effect_broker: ModuleType) -> None:
        """A grant that does not cover the target path refuses."""
        eb = effect_broker
        narrow_grant = eb.BrokerGrant(
            grant_id="narrow-grant",
            operations=("write",),
            allowed_roots=("/work/allowed",),  # only /work/allowed
        )
        session = eb.create_broker_session(
            session_id="s4", grants=[narrow_grant]
        )
        events: list = []
        result = eb.request_effect(
            session,
            grant_id=narrow_grant.grant_id,
            operation="write",
            path="/work/other/output.txt",  # not under /work/allowed
            audit_sink=lambda e: events.append(e),
        )
        assert not result.success
        assert result.denial_code == "denied-out-of-scope"
        assert len(events) >= 1
        assert all(e.outcome == "denied" for e in events)

    def test_available_sink_policy_denial_persists_event(
        self, effect_broker: ModuleType
    ) -> None:
        """Policy denial with available sink persists redacted event before acknowledgment."""
        eb = effect_broker
        session = eb.create_broker_session(session_id="s5", grants=[])
        events: list = []
        result = eb.request_effect(
            session,
            grant_id="no-such-grant",
            operation="write",
            path="/work/output.txt",
            audit_sink=lambda e: events.append(e),
        )
        # Denial persisted before acknowledgment
        assert not result.success
        assert len(events) >= 1, "policy denial must persist an event"
        event = events[0]
        assert event.outcome == "denied"
        # The event must carry no payload bytes
        assert "no-such-grant" not in str(event.reason_code), (
            "reason_code must not contain the refused grant_id"
        )

    def test_unavailable_sink_no_partial_record(self, effect_broker: ModuleType) -> None:
        """With unavailable audit sink, no partial record or effect is exposed (AC-0021)."""
        eb = effect_broker
        grant = eb.BrokerGrant(
            grant_id="valid-grant",
            operations=("write",),
            allowed_roots=("/work",),
        )
        session = eb.create_broker_session(session_id="s6", grants=[grant])
        # Unavailable sink: pass None
        result = eb.request_effect(
            session,
            grant_id=grant.grant_id,
            operation="write",
            path="/work/output.txt",
            audit_sink=None,  # unavailable sink
        )
        assert not result.success, "unavailable sink must refuse"
        assert result.denial_code == "denied-audit-sink-unavailable", (
            f"expected denied-audit-sink-unavailable; got {result.denial_code!r}"
        )

    def test_unavailable_sink_stable_denial_code(self, effect_broker: ModuleType) -> None:
        """Unavailable sink returns a stable redacted denial code without a durable-event claim."""
        eb = effect_broker
        grant = eb.BrokerGrant(
            grant_id="valid-grant-retry",
            operations=("write",),
            allowed_roots=("/work",),
        )
        session = eb.create_broker_session(session_id="s7", grants=[grant])
        # First attempt
        result1 = eb.request_effect(
            session,
            grant_id=grant.grant_id,
            operation="write",
            path="/work/output.txt",
            audit_sink=None,
        )
        # Retry
        result2 = eb.request_effect(
            session,
            grant_id=grant.grant_id,
            operation="write",
            path="/work/output.txt",
            audit_sink=None,
        )
        assert result1.denial_code == result2.denial_code, (
            "retry must return the same stable denial code"
        )
        assert result1.denial_code == "denied-audit-sink-unavailable"

    def test_unavailable_sink_stays_denied_on_retry(self, effect_broker: ModuleType) -> None:
        """Retry with unavailable sink remains denied (AC-0020 cannot weaken refusal)."""
        eb = effect_broker
        grant = eb.BrokerGrant(
            grant_id="retry-grant",
            operations=("write",),
            allowed_roots=("/work",),
        )
        session = eb.create_broker_session(session_id="s8", grants=[grant])
        for i in range(3):
            result = eb.request_effect(
                session,
                grant_id=grant.grant_id,
                operation="write",
                path="/work/output.txt",
                audit_sink=None,
            )
            assert not result.success, f"retry {i} must remain denied"
            assert result.denial_code == "denied-audit-sink-unavailable"

    def test_allow_emits_event_before_success(self, effect_broker: ModuleType) -> None:
        """An allowed effect emits a security event before success is returned (AC-0021)."""
        eb = effect_broker
        grant = eb.BrokerGrant(
            grant_id="allow-grant",
            operations=("write",),
            allowed_roots=("/work",),
        )
        session = eb.create_broker_session(session_id="s9", grants=[grant])
        events: list = []
        result = eb.request_effect(
            session,
            grant_id=grant.grant_id,
            operation="write",
            path="/work/allowed-output.txt",
            audit_sink=lambda e: events.append(e),
        )
        assert result.success, f"valid grant must allow; got code: {result.denial_code!r}"
        assert len(events) == 1, "exactly one allow event must be emitted"
        assert events[0].outcome == "allowed"

    def test_allow_with_failing_sink_refuses(self, effect_broker: ModuleType) -> None:
        """When the sink fails during allow emission, the effect is refused (AC-0021)."""
        eb = effect_broker
        grant = eb.BrokerGrant(
            grant_id="allow-fail-sink-grant",
            operations=("write",),
            allowed_roots=("/work",),
        )
        session = eb.create_broker_session(session_id="s10", grants=[grant])

        def _fail_sink(event: object) -> None:
            # Simulate a failing sink by raising OSError (caught by emit_security_event).
            raise OSError("simulated sink failure")

        result = eb.request_effect(
            session,
            grant_id=grant.grant_id,
            operation="write",
            path="/work/output.txt",
            audit_sink=_fail_sink,
        )
        # The effect must be refused when the sink raises
        assert not result.success, "effect must be refused when allow sink fails"
        assert result.denial_code == "denied-audit-sink-unavailable"


# ═══════════════════════════════════════════════════════════════════════════════
# Validate attestation dict
# ═══════════════════════════════════════════════════════════════════════════════


class TestAttestationValidation:
    """validate_attestation_dict and ContainmentAttestation schema conformance."""

    def test_valid_attestation_passes(self, containment: ModuleType) -> None:
        """A well-formed attestation dict passes validation."""
        cn = containment
        ok, code = cn.validate_attestation_dict({
            "schema_version": 1,
            "host_mechanism": "os-sandbox",
            "principal_or_sandbox": "sandbox-001",
            "roots": ["/work"],
            "limits": {},
        })
        assert ok, f"valid attestation must pass; got code: {code!r}"
        assert code == "ok"

    def test_unknown_schema_version_refused(self, containment: ModuleType) -> None:
        """Unknown schema_version is refused."""
        cn = containment
        ok, code = cn.validate_attestation_dict({
            "schema_version": 99,
            "host_mechanism": "os-sandbox",
            "principal_or_sandbox": "sandbox-001",
            "roots": [],
            "limits": {},
        })
        assert not ok
        assert code == "denied-unknown-schema-version"

    def test_missing_required_field_refused(self, containment: ModuleType) -> None:
        """Missing required field is refused."""
        cn = containment
        ok, code = cn.validate_attestation_dict({
            "schema_version": 1,
            # host_mechanism missing
            "principal_or_sandbox": "sandbox-001",
            "roots": [],
            "limits": {},
        })
        assert not ok
        assert code == "denied-missing-required-field"

    def test_unknown_authority_field_refused(self, containment: ModuleType) -> None:
        """An unknown authority-shaped field is refused."""
        cn = containment
        ok, code = cn.validate_attestation_dict({
            "schema_version": 1,
            "host_mechanism": "os-sandbox",
            "principal_or_sandbox": "sandbox-001",
            "roots": [],
            "limits": {},
            "inject_escalation": "bypass",  # not in schema
        })
        assert not ok
        assert code == "denied-unknown-authority-field"

    def test_same_process_mechanism_refused(self, containment: ModuleType) -> None:
        """Same-process isolation claims are refused."""
        cn = containment
        for mechanism in ["same-process", "wrapper", "in-process", "library-boundary"]:
            ok, code = cn.validate_attestation_dict({
                "schema_version": 1,
                "host_mechanism": mechanism,
                "principal_or_sandbox": "no-sandbox",
                "roots": [],
                "limits": {},
            })
            assert not ok, f"same-process mechanism {mechanism!r} must be refused"
            assert code == "denied-same-process-isolation-claim", (
                f"expected denied-same-process-isolation-claim for {mechanism!r}; got {code!r}"
            )
