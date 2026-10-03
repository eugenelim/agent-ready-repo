"""_containment — containment launcher and delivery-control path constants.

No same-process wrapper may claim OS isolation.  The launcher reports which
containment axes the current host can attest and refuses to activate untrusted
code when the host cannot supply verified containment.

Every launcher attestation is compared with its grant: any attestation broader
than the grant in roots, read enforcement, network, children, or limits is
refused before launch or effect.

DELIVERY_CONTROL_PATHS is a built-in constant that names every path that
untrusted grants must not write to:

* The Core pack's own work-loop source tree.
* Every projected copy of the work-loop skill, one entry per distinct
  target-path prefix that ``contracts/adapter.toml`` declares for the Core
  pack's surfaces (the skill primitive).

A roster test pins this constant to the projections ``contracts/adapter.toml``
declares so drift is caught before merge.

Real launches and brokered effects run only in conformance fixtures; the module
defines the contract without performing production launches.

Implements the containment-attestation.v1 contract for the work-loop skill
scripts.

Standard library only. No third-party imports, no packaging, no installation.
Python 3.11+.
"""

from __future__ import annotations

import importlib.util
import os
import posixpath
import stat
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Final

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

__all__ = [
    # Delivery-control path constant
    "DELIVERY_CONTROL_PATHS",
    # Schema version
    "SUPPORTED_ATTESTATION_SCHEMA_VERSION",
    # Attestation dataclass
    "ContainmentAttestation",
    # Exceptions
    "ContainmentError",
    "ContainmentRefused",
    # Stable denial codes
    "ATTESTATION_DENIAL_CODES",
    # Host protocol and default
    "_SequentialReferenceHost",
    # Public API
    "validate_attestation_dict",
    "check_attestation_within_grant",
    "is_delivery_control_path",
    "report_host_containment_axes",
    "launch_untrusted",
]

# ---------------------------------------------------------------------------
# Sibling module loader
# ---------------------------------------------------------------------------

_SCRIPTS_DIR: Final[Path] = Path(__file__).resolve().parent


def _load_sibling(alias: str, filename: str) -> object:
    """Load a sibling script module by filename, registered temporarily.

    Uses the same importlib.util loader pattern as other script modules.
    """
    path = _SCRIPTS_DIR / filename
    try:
        info = os.lstat(path)
    except OSError as exc:
        raise ImportError(f"cannot locate {filename}: {exc}") from exc
    if not stat.S_ISREG(info.st_mode):
        raise ImportError(f"{filename} is not a regular file")
    previous = sys.dont_write_bytecode
    try:
        sys.dont_write_bytecode = True
        spec = importlib.util.spec_from_file_location(alias, str(path))
        if spec is None or spec.loader is None:
            raise ImportError(f"no import spec for {path}")
        mod = importlib.util.module_from_spec(spec)
        sys.modules[alias] = mod
        try:
            spec.loader.exec_module(mod)  # type: ignore[union-attr]
        finally:
            sys.modules.pop(alias, None)
        return mod
    finally:
        sys.dont_write_bytecode = previous


# ---------------------------------------------------------------------------
# Delivery-control path constant
# ---------------------------------------------------------------------------
#
# Paths that untrusted grants must not write to.  Includes the pack source
# and every projected copy of the work-loop skill per adapter target-path.
# A roster test in tests/roster/ pins this constant to the projections that
# contracts/adapter.toml declares for the Core pack's surfaces.
#
# Adopters lack contracts/adapter.toml, so the constant is self-contained
# here.  Paths are relative prefixes; the grant check normalises both sides
# before comparison.

DELIVERY_CONTROL_PATHS: Final[tuple[str, ...]] = (
    # Pack source — the canonical work-loop skill source tree.
    "packs/core/.apm/skills/work-loop/",
    # claude-code adapter projection target: .claude/skills/<name>/
    ".claude/skills/work-loop/",
    # kiro / kiro-ide / kiro-cli adapters: .kiro/skills/<name>/
    ".kiro/skills/work-loop/",
    # Cohort skill home shared by codex, cursor, gemini, copilot: .agents/skills/<name>/
    ".agents/skills/work-loop/",
    # Git metadata directory — any path component named .git is delivery-control.
    # is_delivery_control_path also detects .git at any depth in an absolute path.
    ".git/",
    # Shadow acceptance delivery-control record directory.
    ".shadow-acceptance/",
    # Loop-run event directory: the engine writes events.jsonl and events.pending
    # here and reads events.pending back during recovery.  Untrusted grants must
    # not write to this directory.
    ".loop-run/",
)

# Delivery-control record filenames: exact base names that untrusted adapters
# must never write to, regardless of which directory they appear in.
_DELIVERY_CONTROL_FILENAMES: Final[frozenset[str]] = frozenset({
    "state.json",
    "engine-state.json",
})

# ---------------------------------------------------------------------------
# Schema version
# ---------------------------------------------------------------------------

SUPPORTED_ATTESTATION_SCHEMA_VERSION: Final[int] = 1

# ---------------------------------------------------------------------------
# Stable denial codes — callers may match against these strings
# ---------------------------------------------------------------------------

ATTESTATION_DENIAL_CODES: Final[frozenset[str]] = frozenset({
    "denied-unknown-schema-version",
    "denied-missing-required-field",
    "denied-unknown-authority-field",
    "denied-same-process-isolation-claim",
    "denied-attestation-broader-than-grant",
    "denied-attestation-covers-control-plane",
    "denied-no-verified-containment",
    "denied-unsupported-host-containment",
    "denied-audit-sink-unavailable",
})

# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------


class ContainmentError(Exception):
    """Base exception for containment operations."""


class ContainmentRefused(ContainmentError):
    """A containment operation was refused with a stable denial code.

    ``denial_code`` is one of the strings in ``ATTESTATION_DENIAL_CODES`` and
    carries no sensitive payload bytes.
    """

    def __init__(self, denial_code: str, message: str = "") -> None:
        super().__init__(message or denial_code)
        self.denial_code: str = denial_code


# ---------------------------------------------------------------------------
# ContainmentAttestation
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ContainmentAttestation:
    """Attestation from the verified launcher to the supervisor and broker.

    Maps to the containment-attestation.v1 schema.  Authority is narrower
    than the grant; only verified read coverage can support complete access
    attestation.  Missing, unverifiable, or broader enforcement refuses.
    """

    schema_version: int
    host_mechanism: str
    principal_or_sandbox: str
    roots: tuple[str, ...]
    limits: dict

    # Optional fields — absent means no read enforcement, network, or children.
    read_enforcement: str | None = None
    trace_coverage: str | None = None
    network: dict | None = None
    children: dict | None = None

    def as_dict(self) -> dict:
        """Serialize to a dict matching the containment-attestation.v1 schema."""
        d: dict = {
            "schema_version": self.schema_version,
            "host_mechanism": self.host_mechanism,
            "principal_or_sandbox": self.principal_or_sandbox,
            "roots": list(self.roots),
            "limits": self.limits,
        }
        if self.read_enforcement is not None:
            d["read_enforcement"] = self.read_enforcement
        if self.trace_coverage is not None:
            d["trace_coverage"] = self.trace_coverage
        if self.network is not None:
            d["network"] = self.network
        if self.children is not None:
            d["children"] = self.children
        return d


# ---------------------------------------------------------------------------
# Schema validation
# ---------------------------------------------------------------------------

_REQUIRED_ATTESTATION_KEYS: Final[frozenset[str]] = frozenset({
    "schema_version",
    "host_mechanism",
    "principal_or_sandbox",
    "roots",
    "limits",
})

_ALLOWED_ATTESTATION_KEYS: Final[frozenset[str]] = frozenset({
    "schema_version",
    "host_mechanism",
    "principal_or_sandbox",
    "roots",
    "limits",
    "read_enforcement",
    "trace_coverage",
    "network",
    "children",
})

_VALID_READ_ENFORCEMENT: Final[frozenset[str]] = frozenset({"allowlist", "trace"})

# Same-process mechanism identifiers that must never be accepted.
_SAME_PROCESS_MECHANISMS: Final[frozenset[str]] = frozenset({
    "same-process",
    "in-process",
    "library-boundary",
    "wrapper",
    "subprocess-only",
    "no-sandbox",
})


def validate_attestation_dict(d: object) -> tuple[bool, str]:
    """Validate a containment-attestation.v1 record dict in code.

    Checks schema_version, required fields, absence of unknown
    authority-shaped fields, read_enforcement enum, and same-process
    isolation claim.  Does not import jsonschema at runtime.

    Returns:
        (True, "ok") when the record is schema-valid.
        (False, denial_code) when invalid; denial_code is one of:
          denied-unknown-schema-version — wrong or unknown schema_version.
          denied-missing-required-field — a required field is absent.
          denied-unknown-authority-field — an extra field not in the schema.
          denied-same-process-isolation-claim — host_mechanism names a
              same-process wrapper.
    """
    if not isinstance(d, dict):
        return False, "denied-missing-required-field"

    version = d.get("schema_version")
    if not isinstance(version, int) or version != SUPPORTED_ATTESTATION_SCHEMA_VERSION:
        return False, "denied-unknown-schema-version"

    missing = _REQUIRED_ATTESTATION_KEYS - set(d.keys())
    if missing:
        return False, "denied-missing-required-field"

    unknown = set(d.keys()) - _ALLOWED_ATTESTATION_KEYS
    if unknown:
        return False, "denied-unknown-authority-field"

    mechanism = d.get("host_mechanism", "")
    if not isinstance(mechanism, str) or not mechanism:
        return False, "denied-missing-required-field"
    if mechanism.lower() in _SAME_PROCESS_MECHANISMS:
        return False, "denied-same-process-isolation-claim"

    read_enf = d.get("read_enforcement")
    if read_enf is not None and read_enf not in _VALID_READ_ENFORCEMENT:
        return False, "denied-unknown-authority-field"

    return True, "ok"


# ---------------------------------------------------------------------------
# Attestation-vs-grant comparison
# ---------------------------------------------------------------------------

# Product-read proof modes ordered by permissiveness (lower index = stricter).
# Same ordering as _security_capability.py.
_PROOF_MODE_PERMISSIVENESS: Final[dict[str, int]] = {
    "trace": 0,
    "allowlist": 1,
    "none": 2,
}

# Equivalence map from containment read_enforcement to grant proof mode names.
_ENFORCEMENT_TO_PROOF_MODE: Final[dict[str, str]] = {
    "trace": "trace",
    "allowlist": "allowlist",
}


def _roots_broader(attestation_roots: tuple[str, ...], grant_roots: tuple[str, ...]) -> bool:
    """Return True when the attestation claims roots outside the grant.

    A root is outside the grant when no grant root is a prefix of it.
    This is a conservative check: if the attestation root is ``/a`` but the
    grant only permits ``/a/sub``, the attestation is broader.
    """
    if not grant_roots:
        return bool(attestation_roots)
    for a_root in attestation_roots:
        a_norm = a_root.rstrip("/")
        covered = any(
            a_norm == g_root.rstrip("/") or a_norm.startswith(g_root.rstrip("/") + "/")
            for g_root in grant_roots
        )
        if not covered:
            return True
    return False


def check_attestation_within_grant(
    attestation: ContainmentAttestation,
    grant: object,
) -> tuple[bool, str]:
    """Check that *attestation* is not broader than *grant*.

    Returns (True, "ok") when the attestation is at most as permissive as the
    grant in every axis.  Returns (False, denial_code) when any axis of the
    attestation is broader than the grant allows.

    Checked axes (attestation must not be broader than the grant on any axis):
    - roots: attestation roots must be within grant roots.
    - read_enforcement / product_read_proof_mode: attestation must not claim
      weaker read coverage than the grant requires.
    - network: attestation must not claim network when grant denies it.
    - children: attestation must not claim children when grant denies it.
    - limits: attestation limits must be at most as permissive as the grant.

    ``grant`` is duck-typed to avoid a compile-time import of
    _security_capability.CapabilityGrant.
    """
    grant_roots: tuple[str, ...] = tuple(grant.roots)
    if _roots_broader(attestation.roots, grant_roots):
        return False, "denied-attestation-broader-than-grant"

    # read_enforcement vs product_read_proof_mode
    grant_proof_mode: str | None = getattr(grant, "product_read_proof_mode", None)
    if attestation.read_enforcement is not None and grant_proof_mode is not None:
        # Attestation claims a specific read enforcement; it must be at least as
        # strict as the grant requires.
        attest_perm = _PROOF_MODE_PERMISSIVENESS.get(
            _ENFORCEMENT_TO_PROOF_MODE.get(attestation.read_enforcement, ""), 2
        )
        grant_perm = _PROOF_MODE_PERMISSIVENESS.get(grant_proof_mode, 2)
        if attest_perm > grant_perm:
            # Attestation is weaker (more permissive) than the grant requires.
            return False, "denied-attestation-broader-than-grant"

    # network: if grant denies network (network is None), attestation must not claim it.
    grant_network = getattr(grant, "network", None)
    attest_net_allowed = (
        attestation.network is not None and attestation.network.get("allowed")
    )
    if grant_network is None and attest_net_allowed:
        return False, "denied-attestation-broader-than-grant"

    # children: if grant denies children, attestation must not claim it.
    grant_children = getattr(grant, "children", None)
    attest_child_allowed = (
        attestation.children is not None and attestation.children.get("allowed")
    )
    if grant_children is None and attest_child_allowed:
        return False, "denied-attestation-broader-than-grant"

    # limits: attestation limits must not be more permissive than the grant.
    grant_limits = getattr(grant, "limits", None)
    if grant_limits is not None:
        grant_max_bytes = getattr(grant_limits, "max_bytes", None)
        grant_timeout_s = getattr(grant_limits, "timeout_s", None)
        attest_max_bytes = attestation.limits.get("max_bytes")
        attest_timeout_s = attestation.limits.get("timeout_s")
        if (
            grant_max_bytes is not None
            and attest_max_bytes is not None
            and attest_max_bytes > grant_max_bytes
        ):
            return False, "denied-attestation-broader-than-grant"
        if (
            grant_timeout_s is not None
            and attest_timeout_s is not None
            and attest_timeout_s > grant_timeout_s
        ):
            return False, "denied-attestation-broader-than-grant"

    return True, "ok"


# ---------------------------------------------------------------------------
# Delivery-control path guard
# ---------------------------------------------------------------------------


def is_delivery_control_path(path: str) -> bool:
    """Return True when *path* is within a delivery-control path.

    Handles all path spellings: relative, absolute, ``./``-prefixed,
    ``..``-traversal, and case variants (comparison is case-insensitive
    so the guard holds on case-insensitive filesystems such as macOS and
    Windows).

    Specifically:
    - Any path component named ``.git`` is delivery-control, regardless of
      its position in the path (e.g. ``/repo/.git/config`` is caught).
    - Exact base-file names in ``_DELIVERY_CONTROL_FILENAMES`` are refused
      regardless of the containing directory.
    - Every prefix in ``DELIVERY_CONTROL_PATHS`` is matched after lexical
      normalization of the requested path so that ``./`` prefixes and ``..``
      segments are resolved before the comparison.
    """
    # Normalize: resolve ./ and ../ without following symlinks.
    # posixpath.normpath is cross-platform and performs only lexical
    # normalization; it never touches the real filesystem.
    normalized = posixpath.normpath(path.replace("\\", "/"))
    normalized_lower = normalized.lower()

    # Split into components for element-level checks.
    parts = [p for p in normalized.split("/") if p and p != "."]

    # .git as a path component at any depth is always delivery-control.
    if any(p.lower() == ".git" for p in parts):
        return True

    # Exact filename check for delivery-control record names.
    if parts and parts[-1].lower() in {n.lower() for n in _DELIVERY_CONTROL_FILENAMES}:
        return True

    for prefix in DELIVERY_CONTROL_PATHS:
        norm_prefix = prefix.rstrip("/").lower()

        # Strip any leading slash for relative-path comparison.
        norm_rel = normalized_lower.lstrip("/")

        # Relative-path match: exactly the prefix or a path under it.
        if norm_rel == norm_prefix or norm_rel.startswith(norm_prefix + "/"):
            return True

        # Absolute-path match: /prefix or a direct child, and also the
        # "anywhere in path" form (/repo/.claude/skills/work-loop/x).
        if (
            normalized_lower == "/" + norm_prefix
            or normalized_lower.startswith("/" + norm_prefix + "/")
            or ("/" + norm_prefix + "/") in normalized_lower
            or normalized_lower.endswith("/" + norm_prefix)
        ):
            return True

    return False


# ---------------------------------------------------------------------------
# Host containment axis reporting
# ---------------------------------------------------------------------------

# Same-process adapters are trusted infrastructure.  Untrusted code has no
# same-process mode; the launcher refuses when the host cannot supply a
# verified sandbox or restricted principal.

def report_host_containment_axes() -> dict:
    """Report which containment axes the current host can attest.

    Returns a dict with keys:
      ``verified_sandbox``:   bool — whether the host supplies a verified
                              OS sandbox (always False for the sequential
                              reference runtime, which is trusted in-process).
      ``restricted_principal``: bool — whether the host supplies a restricted
                              security principal for untrusted code.
      ``supported_mechanisms``: list[str] — names of mechanisms the host can
                              prove.

    The sequential reference runtime is a trusted in-process adapter; it cannot
    attest OS-level containment for untrusted code. Hosts that cannot supply
    any verified containment must report both ``verified_sandbox`` and
    ``restricted_principal`` as False.
    """
    # The sequential reference runtime operates as a trusted in-process
    # adapter.  It cannot claim OS isolation for untrusted code.
    return {
        "verified_sandbox": False,
        "restricted_principal": False,
        "supported_mechanisms": [],
    }


# ---------------------------------------------------------------------------
# Containment host protocol
# ---------------------------------------------------------------------------


class _SequentialReferenceHost:
    """Default host for the sequential reference runtime.

    The sequential reference runtime is a trusted in-process adapter.  It
    cannot supply a verified OS sandbox or restricted security principal for
    untrusted code.  Activating untrusted code under this host always refuses
    with ``denied-no-verified-containment``.
    """

    def report_axes(self) -> dict:
        """Return containment axes for this host."""
        return report_host_containment_axes()

    def get_attestation(
        self,
        spec_dict: dict,  # noqa: ARG002 — unused in base; hosts may inspect the spec
        grant: object,    # noqa: ARG002
    ) -> dict | None:
        """Return None; the sequential reference runtime provides no verified attestation."""
        return None


#: Module-default host — the sequential reference runtime.
#: Activating untrusted code always refuses; no OS-level containment is available.
_DEFAULT_HOST: Final[_SequentialReferenceHost] = _SequentialReferenceHost()


# ---------------------------------------------------------------------------
# Untrusted process launcher
# ---------------------------------------------------------------------------


def launch_untrusted(
    spec_dict: dict,
    grant: object,
    *,
    host: object | None = None,
    audit_sink: Callable | None = None,
    operation_id: str | None = None,
) -> object:
    """Launch an untrusted executable under verified host containment.

    Refuses before any process starts unless all of the following hold:

    1. The audit sink is available.
    2. The host supplies a valid containment attestation.
    3. The attestation is within the grant on every axis.

    Only then does it delegate to ``_process_safety.launch_safe_process()``.

    The module-default host is the sequential reference runtime, which cannot
    supply verified containment for untrusted code.  The production path
    therefore always refuses with ``denied-no-verified-containment``.
    A host fixture that provides an attestation lives only in test files.

    Args:
        spec_dict:     A safe-process.v1 spec dict for the untrusted process.
        grant:         Capability grant the process operates under.
        host:          Object with a ``get_attestation(spec_dict, grant) →
                       dict | None`` method.  Defaults to the sequential
                       reference runtime (always returns None).
        audit_sink:    Callable accepting a SecurityEvent.  ``None`` means
                       the sink is unavailable; refuses immediately with no
                       event persisted.
        operation_id:  Stable operation ID for the audit event; generated
                       when absent.

    Returns:
        The ``ProcessResult`` from ``_process_safety.launch_safe_process()``.

    Raises:
        ContainmentRefused: with a stable denial code on any containment
            refusal (sink unavailable, no attestation, invalid attestation,
            or attestation broader than the grant).
        _process_safety.ProcessDenied: propagated from ``launch_safe_process``
            when containment checks pass but the process itself fails.
    """
    # Unavailable sink → fail closed immediately, no data persisted.
    if audit_sink is None:
        raise ContainmentRefused(
            "denied-audit-sink-unavailable",
            "audit sink is unavailable; untrusted launch refused with no event persisted",
        )

    resolved_host = host if host is not None else _DEFAULT_HOST

    # Ask the host for a verified containment attestation.
    raw_attestation = resolved_host.get_attestation(spec_dict, grant)
    if raw_attestation is None:
        raise ContainmentRefused(
            "denied-no-verified-containment",
            "host supplies no verified containment attestation; refusing untrusted launch",
        )

    # Validate the attestation dict against the containment-attestation.v1 schema.
    ok, denial_code = validate_attestation_dict(raw_attestation)
    if not ok:
        raise ContainmentRefused(
            denial_code,
            f"attestation schema validation failed: {denial_code}",
        )

    # Build a typed ContainmentAttestation from the validated dict.
    attestation = ContainmentAttestation(
        schema_version=raw_attestation["schema_version"],
        host_mechanism=raw_attestation["host_mechanism"],
        principal_or_sandbox=raw_attestation["principal_or_sandbox"],
        roots=tuple(raw_attestation.get("roots", ())),
        limits=raw_attestation.get("limits", {}),
        read_enforcement=raw_attestation.get("read_enforcement"),
        trace_coverage=raw_attestation.get("trace_coverage"),
        network=raw_attestation.get("network"),
        children=raw_attestation.get("children"),
    )

    # Attestation must not be broader than the grant on any axis.
    ok, denial_code = check_attestation_within_grant(attestation, grant)
    if not ok:
        raise ContainmentRefused(
            denial_code,
            f"attestation is broader than the grant: {denial_code}",
        )

    # All containment checks pass — delegate to the process safety primitive.
    # Loaded lazily to avoid imposing _process_safety's import cost when only
    # the containment-checking functions are used.
    _ps = _load_sibling("_ps_cont_launch", "_process_safety.py")
    return _ps.launch_safe_process(  # type: ignore[attr-defined]
        spec_dict,
        cwd_roots=tuple(grant.roots),
        audit_sink=audit_sink,
        operation_id=operation_id,
    )
