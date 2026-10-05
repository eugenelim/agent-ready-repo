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
  target path an installed adapter uses for this skill.

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
from datetime import UTC, datetime
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
# The list is self-contained so it needs no adapter configuration at run time.
# Paths are relative prefixes; the grant check normalises both sides before
# comparison.

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
    "denied-unverified-grant",
    "denied-invalid-attestation-field",
    "denied-containment-check-failed",
})

# Closed nested objects of containment-attestation.v1: name -> (required keys,
# allowed keys).  Values are type-checked separately below.
_ATTESTATION_NESTED_KEYS: Final[dict[str, tuple[frozenset[str], frozenset[str]]]] = {
    "limits": (frozenset(), frozenset({"max_bytes", "timeout_s"})),
    "network": (frozenset({"allowed"}), frozenset({"allowed"})),
    "children": (frozenset({"allowed"}), frozenset({"allowed"})),
}
_ATTESTATION_LIMIT_MINIMUMS: Final[dict[str, int]] = {"max_bytes": 0, "timeout_s": 1}


def _is_plain_int(value: object) -> bool:
    """True for an int that is not a bool (bool is an int subclass)."""
    return isinstance(value, int) and not isinstance(value, bool)

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


def _safe_correlation(value: object) -> str:
    """Return *value* as an audit correlation only if it is a non-empty string."""
    return value if isinstance(value, str) and value else "unknown"


def validate_attestation_dict(d: object) -> tuple[bool, str]:
    """Validate *d* without ever raising: any unexpected value refuses.

    A record of any shape returns a stable denial code instead of an
    exception, so every caller can audit the refusal.
    """
    try:
        return _validate_attestation_dict_checked(d)
    except Exception:  # noqa: BLE001 — validation must never raise
        return False, "denied-invalid-attestation-field"


def _validate_attestation_dict_checked(d: object) -> tuple[bool, str]:
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
    if (
        not isinstance(version, int)
        or isinstance(version, bool)
        or version != SUPPORTED_ATTESTATION_SCHEMA_VERSION
    ):
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

    # Optional string fields: absent is allowed, but a present value (null
    # included) must be a string the schema accepts.
    if "read_enforcement" in d and (
        not isinstance(d["read_enforcement"], str)
        or d["read_enforcement"] not in _VALID_READ_ENFORCEMENT
    ):
        return False, "denied-unknown-authority-field"
    if "trace_coverage" in d and (
        not isinstance(d["trace_coverage"], str) or not d["trace_coverage"]
    ):
        return False, "denied-invalid-attestation-field"
    if not isinstance(d.get("limits"), dict):
        return False, "denied-invalid-attestation-field"

    principal = d.get("principal_or_sandbox")
    if not isinstance(principal, str) or not principal:
        return False, "denied-invalid-attestation-field"
    roots = d.get("roots", ())
    if not isinstance(roots, (list, tuple)) or not all(
        isinstance(root, str) and root for root in roots
    ):
        return False, "denied-invalid-attestation-field"

    # Nested objects are closed and typed; a NaN, boolean, or string limit can
    # never stand in for a proven integer bound.
    for name, (required, allowed) in _ATTESTATION_NESTED_KEYS.items():
        if name not in d:
            continue
        nested = d[name]
        if not isinstance(nested, dict):
            return False, "denied-invalid-attestation-field"
        keys = set(nested)
        if not required <= keys or not keys <= allowed:
            return False, "denied-invalid-attestation-field"
        if "allowed" in nested and not isinstance(nested["allowed"], bool):
            return False, "denied-invalid-attestation-field"
    limits = d["limits"]
    for key, minimum in _ATTESTATION_LIMIT_MINIMUMS.items():
        if key not in limits:
            continue
        value = limits[key]
        if not _is_plain_int(value) or value < minimum:
            return False, "denied-invalid-attestation-field"

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


def _norm_path(raw: str) -> str:
    """Lexically normalise a path string for containment comparison.

    Uses posixpath.normpath so that traversal sequences like /w/../etc resolve
    before the check.  Trailing slashes are stripped so prefix comparison works
    consistently.  Backslashes are converted to forward slashes first so that
    Windows-style paths do not bypass normalisation.
    """
    return posixpath.normpath(raw.replace("\\", "/")).rstrip("/")


def _norm_covered_by(a_norm: str, g_root: str) -> bool:
    """Return True when normalised attestation root *a_norm* is within *g_root*.

    *g_root* is normalised here so callers need not pre-normalise grant roots.
    """
    g_norm = _norm_path(g_root)
    return a_norm == g_norm or a_norm.startswith(g_norm + "/")


def _roots_broader(attestation_roots: tuple[str, ...], grant_roots: tuple[str, ...]) -> bool:
    """Return True when the attestation claims roots outside the grant.

    A root is outside the grant when no grant root is a prefix of it.
    Both sides are normalised with posixpath.normpath before comparison so that
    traversal sequences like /w/../etc resolve before the check.  A normalised
    attestation root that still contains a ``..`` component (e.g. ``../outside``)
    is always treated as broader — it cannot be verified to be within any grant.
    """
    if not grant_roots:
        return bool(attestation_roots)
    for a_root in attestation_roots:
        a_norm = _norm_path(a_root)
        # A path that retains .. after normalisation escapes its start point
        # and cannot be contained within any grant root.
        if ".." in a_norm.split("/"):
            return True
        covered = any(_norm_covered_by(a_norm, g_root) for g_root in grant_roots)
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
    if grant_proof_mode is not None:
        if attestation.read_enforcement is None:
            # Grant requires read coverage but attestation claims none — refuse.
            # An absent read_enforcement is weaker than any required proof mode.
            return False, "denied-attestation-broader-than-grant"
        # Attestation claims a specific read enforcement; it must be at least as
        # strict as the grant requires.
        attest_perm = _PROOF_MODE_PERMISSIVENESS.get(
            _ENFORCEMENT_TO_PROOF_MODE.get(attestation.read_enforcement, ""), 2
        )
        grant_perm = _PROOF_MODE_PERMISSIVENESS.get(grant_proof_mode, 2)
        if attest_perm > grant_perm:
            # Attestation is weaker (more permissive) than the grant requires.
            return False, "denied-attestation-broader-than-grant"

    # network: deny when the grant disallows network (absent or allowed=False).
    # A grant field of allowed=False is treated the same as absent.
    grant_network = getattr(grant, "network", None)
    grant_net_denied = grant_network is None or not getattr(grant_network, "allowed", True)
    attest_net_allowed = (
        attestation.network is not None and attestation.network.get("allowed")
    )
    if grant_net_denied and attest_net_allowed:
        return False, "denied-attestation-broader-than-grant"

    # children: deny when the grant disallows children (absent or allowed=False).
    grant_children = getattr(grant, "children", None)
    grant_child_denied = grant_children is None or not getattr(grant_children, "allowed", True)
    attest_child_allowed = (
        attestation.children is not None and attestation.children.get("allowed")
    )
    if grant_child_denied and attest_child_allowed:
        return False, "denied-attestation-broader-than-grant"

    # Destination restriction: when the grant allows network but restricts to
    # specific destinations, the v1 attestation schema has no destinations field
    # and therefore cannot prove that restriction.  Any network-allowed attestation
    # against such a grant must be refused.
    grant_net_allowed = grant_network is not None and getattr(grant_network, "allowed", False)
    if attest_net_allowed and grant_net_allowed:
        grant_dests = getattr(grant_network, "allowed_destinations", ())
        if grant_dests:
            return False, "denied-attestation-broader-than-grant"

    # limits: attestation limits must not be more permissive than the grant.
    # When the grant sets a limit, an attestation that omits it cannot prove
    # that restriction and must be refused.
    grant_limits = getattr(grant, "limits", None)
    if grant_limits is not None:
        grant_max_bytes = getattr(grant_limits, "max_bytes", None)
        grant_timeout_s = getattr(grant_limits, "timeout_s", None)
        attest_max_bytes = attestation.limits.get("max_bytes")
        attest_timeout_s = attestation.limits.get("timeout_s")
        if grant_max_bytes is not None and attest_max_bytes is None:
            return False, "denied-attestation-broader-than-grant"
        if grant_timeout_s is not None and attest_timeout_s is None:
            return False, "denied-attestation-broader-than-grant"
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
    issuer: object | None = None,
) -> object:
    """Launch an untrusted executable under verified host containment.

    Refuses before any process starts unless all of the following hold:

    1. The audit sink is available.
    2. When an issuer is provided, the grant must verify against it.
    3. The host supplies a valid containment attestation.
    4. The attestation is within the grant on every axis.

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
        issuer:        Optional owning issuer.  When given, the grant must
                       pass ``issuer.verify_grant(grant)``; a caller-built
                       or revoked grant is refused with an audited denial and
                       the ``denied-unverified-grant`` code before any host
                       interaction.  When absent (default), no issuer check
                       is performed.

    Returns:
        The ``ProcessResult`` from ``_process_safety.launch_safe_process()``.

    Raises:
        ContainmentRefused: with a stable denial code on any containment
            refusal (sink unavailable, unverified grant, no attestation,
            invalid attestation, or attestation broader than the grant).
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
    se = _load_sibling("_se_cont_launch", "_security_events.py")
    event_operation_id = (
        operation_id
        if isinstance(operation_id, str) and operation_id
        else se.make_operation_id()  # type: ignore[attr-defined]
    )
    # Refusals this function built and audited; only these may pass the guard.
    audited_refusals: set[int] = set()

    def refuse(denial_code: str, message: str) -> ContainmentRefused:
        """Audit a containment refusal through the checked emitter, then return it."""
        se.emit_denial_best_effort(  # type: ignore[attr-defined]
            audit_sink,
            se.SecurityEvent(  # type: ignore[attr-defined]
                schema_version=1,
                operation_id=event_operation_id,
                correlation_id=_safe_correlation(getattr(grant, "grant_id", None)),
                event_type="containment-launch",
                outcome="denied",
                reason_code=denial_code,
                timestamp=datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
            ),
        )
        refusal = ContainmentRefused(denial_code, message)
        audited_refusals.add(id(refusal))
        return refusal

    def check_before_launch() -> tuple[str, ...]:
        """Run every pre-launch check; return the grant roots to confine cwd to."""
        # When an issuer is provided, verify the grant before trusting any of its
        # fields.  A caller-built grant or a revoked grant fails verification and
        # is refused with an audited denial before any host interaction.
        if issuer is not None and not issuer.verify_grant(grant):
            raise refuse(
                "denied-unverified-grant",
                "grant could not be verified with its issuer; refusing untrusted launch",
            )

        # Ask the host for a verified containment attestation.
        raw_attestation = resolved_host.get_attestation(spec_dict, grant)
        if raw_attestation is None:
            raise refuse(
                "denied-no-verified-containment",
                "host supplies no verified containment attestation; refusing untrusted launch",
            )

        # Validate the attestation dict against the containment-attestation.v1 schema.
        ok, denial_code = validate_attestation_dict(raw_attestation)
        if not ok:
            raise refuse(
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
        try:
            ok, denial_code = check_attestation_within_grant(attestation, grant)
        except Exception:  # noqa: BLE001 — any check failure refuses, audited
            ok, denial_code = False, "denied-invalid-attestation-field"
        if not ok:
            raise refuse(
                denial_code,
                f"attestation is broader than the grant: {denial_code}",
            )
        return tuple(grant.roots)  # type: ignore[attr-defined]

    # Every pre-launch step runs inside one guard: an exception from the host,
    # the issuer, validation, or the comparison still ends in an audited
    # refusal, never an unaudited escape.
    try:
        cwd_roots = check_before_launch()
    except ContainmentRefused as exc:
        if id(exc) in audited_refusals:
            raise
        # A refusal raised by host or issuer code was never audited and may
        # carry a code outside the stable set: audit it under a stable code.
        raise refuse(
            "denied-containment-check-failed",
            "a containment pre-launch check failed; refusing untrusted launch",
        ) from None
    except Exception:  # noqa: BLE001 — any pre-launch failure refuses, audited
        raise refuse(
            "denied-containment-check-failed",
            "a containment pre-launch check failed; refusing untrusted launch",
        ) from None

    # All containment checks pass — delegate to the process safety primitive.
    # Loaded lazily to avoid imposing _process_safety's import cost when only
    # the containment-checking functions are used.
    _ps = _load_sibling("_ps_cont_launch", "_process_safety.py")
    return _ps.launch_safe_process(  # type: ignore[attr-defined]
        spec_dict,
        cwd_roots=cwd_roots,
        audit_sink=audit_sink,
        operation_id=operation_id,
    )
