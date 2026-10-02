"""_security_capability — capability issuance, intersection, and verification.

The capability issuer owns active-grant state. A grant not issued by this
instance, or that is expired or revoked, fails verification.

Child grants are computed as the intersection of the parent and the requested
grant: every field narrows or stays the same. Omitted network and child-process
fields in either parent or request deny all in the child.

Implements the security-capability.v1 contract for the work-loop skill scripts.

Standard library only. No third-party imports, no packaging, no installation.
Python 3.11+.
"""

import secrets
import sys
import time
from dataclasses import dataclass
from typing import Final

# Streams must be UTF-8 before any output; this module prints nothing to
# stdout/stderr but follows the pack convention for consistency.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

__all__ = [
    "CapabilityGrant",
    "CapabilityIssuer",
    "CapabilityError",
    "CapabilityRefused",
    "SUPPORTED_SCHEMA_VERSION",
    "_WritesGrant",
    "_NetworkGrant",
    "_ChildrenGrant",
    "_Limits",
    "intersect_grants",
    "validate_grant_dict",
]

SUPPORTED_SCHEMA_VERSION: Final[int] = 1


# ── Exception hierarchy ───────────────────────────────────────────────────────


class CapabilityError(Exception):
    """Base exception for capability operations."""


class CapabilityRefused(CapabilityError):
    """A capability operation was refused.

    ``denial_code`` carries a stable string that callers may log without
    sensitive payload bytes.
    """

    def __init__(self, denial_code: str, message: str = "") -> None:
        super().__init__(message or denial_code)
        self.denial_code: str = denial_code


# ── Sub-record types ──────────────────────────────────────────────────────────


@dataclass(frozen=True)
class _WritesGrant:
    """Write-permission sub-record of security-capability.v1."""

    allowed_roots: tuple[str, ...]

    def as_dict(self) -> dict:
        return {"allowed_roots": list(self.allowed_roots)}


@dataclass(frozen=True)
class _NetworkGrant:
    """Network-access sub-record of security-capability.v1.

    Absent (None at the parent level) means deny all network access.
    """

    allowed: bool
    allowed_destinations: tuple[str, ...] = ()

    def as_dict(self) -> dict:
        d: dict = {"allowed": self.allowed}
        if self.allowed_destinations:
            d["allowed_destinations"] = list(self.allowed_destinations)
        return d


@dataclass(frozen=True)
class _ChildrenGrant:
    """Child-process authority sub-record of security-capability.v1.

    Absent (None at the parent level) means deny all child processes.
    """

    allowed: bool

    def as_dict(self) -> dict:
        return {"allowed": self.allowed}


@dataclass(frozen=True)
class _Limits:
    """Resource-limits sub-record of security-capability.v1."""

    max_bytes: int | None = None
    timeout_s: int | None = None

    def as_dict(self) -> dict:
        d: dict = {}
        if self.max_bytes is not None:
            d["max_bytes"] = self.max_bytes
        if self.timeout_s is not None:
            d["timeout_s"] = self.timeout_s
        return d


# ── CapabilityGrant ───────────────────────────────────────────────────────────


@dataclass(frozen=True)
class CapabilityGrant:
    """Immutable security capability grant (security-capability.v1).

    All collection fields are tuples so the dataclass remains hashable.
    Use ``as_dict()`` to produce the schema-valid wire form.
    """

    schema_version: int
    grant_id: str
    roots: tuple[str, ...]
    operations: tuple[str, ...]
    trust_class: str
    writes: _WritesGrant
    control_denies: tuple[str, ...]
    limits: _Limits
    product_read_proof_mode: str | None = None
    network: _NetworkGrant | None = None    # absent = deny all network
    children: _ChildrenGrant | None = None  # absent = deny all child processes

    def as_dict(self) -> dict:
        """Serialize to a dict matching the security-capability.v1 schema."""
        d: dict = {
            "schema_version": self.schema_version,
            "grant_id": self.grant_id,
            "roots": list(self.roots),
            "operations": list(self.operations),
            "trust_class": self.trust_class,
            "writes": self.writes.as_dict(),
            "control_denies": list(self.control_denies),
            "limits": self.limits.as_dict(),
        }
        if self.product_read_proof_mode is not None:
            d["product_read_proof_mode"] = self.product_read_proof_mode
        if self.network is not None:
            d["network"] = self.network.as_dict()
        if self.children is not None:
            d["children"] = self.children.as_dict()
        return d


# ── Intersection ──────────────────────────────────────────────────────────────

# Product-read proof modes ordered by permissiveness; higher = more permissive.
# "none" = no proof required (most permissive).
# "allowlist" = proof via an allowlist (middle).
# "trace" = proof via complete trace (most controlled, least permissive).
# On intersection we take the STRICTER mode (lower permissiveness index).
_PROOF_MODE_ORDER: Final[dict[str, int]] = {
    "trace": 0,      # most controlled
    "allowlist": 1,
    "none": 2,       # least controlled
}


def intersect_grants(
    parent: CapabilityGrant,
    request: CapabilityGrant,
    *,
    new_grant_id: str,
) -> CapabilityGrant:
    """Compute the intersection of *parent* and *request* grants.

    Every field in the returned child grant is narrower than or equal to the
    corresponding field in the parent:

    - ``roots``: set intersection.
    - ``operations``: set intersection.
    - ``writes.allowed_roots``: set intersection.
    - ``network``: present only when both parent and request supply it; fields
      are then intersected.  Absent in either → absent (deny all).
    - ``children``: same logic as ``network``.
    - ``limits``: minimum (stricter) of each limit.
    - ``control_denies``: union (both sets of denied paths apply).
    - ``product_read_proof_mode``: stricter of the two (lower permissiveness);
      absent in either → absent (deny all product reads).
    - ``trust_class``: taken from the request.
    """
    # roots: intersection
    child_roots = tuple(sorted(set(parent.roots) & set(request.roots)))

    # operations: intersection
    child_ops = tuple(sorted(set(parent.operations) & set(request.operations)))

    # writes.allowed_roots: intersection
    child_write_roots = tuple(
        sorted(set(parent.writes.allowed_roots) & set(request.writes.allowed_roots))
    )
    child_writes = _WritesGrant(allowed_roots=child_write_roots)

    # network: absent in either → absent
    child_network: _NetworkGrant | None = None
    if parent.network is not None and request.network is not None:
        net_allowed = parent.network.allowed and request.network.allowed
        p_dests = set(parent.network.allowed_destinations)
        r_dests = set(request.network.allowed_destinations)
        if p_dests and r_dests:
            child_dests = tuple(sorted(p_dests & r_dests))
        elif p_dests:
            child_dests = tuple(sorted(p_dests))
        elif r_dests:
            child_dests = tuple(sorted(r_dests))
        else:
            child_dests = ()
        child_network = _NetworkGrant(allowed=net_allowed, allowed_destinations=child_dests)

    # children: absent in either → absent
    child_children: _ChildrenGrant | None = None
    if parent.children is not None and request.children is not None:
        child_children = _ChildrenGrant(
            allowed=parent.children.allowed and request.children.allowed
        )

    # limits: minimum of each limit field
    p_lim = parent.limits
    r_lim = request.limits

    if p_lim.max_bytes is not None and r_lim.max_bytes is not None:
        child_max_bytes: int | None = min(p_lim.max_bytes, r_lim.max_bytes)
    else:
        child_max_bytes = p_lim.max_bytes if p_lim.max_bytes is not None else r_lim.max_bytes

    if p_lim.timeout_s is not None and r_lim.timeout_s is not None:
        child_timeout: int | None = min(p_lim.timeout_s, r_lim.timeout_s)
    else:
        child_timeout = p_lim.timeout_s if p_lim.timeout_s is not None else r_lim.timeout_s

    child_limits = _Limits(max_bytes=child_max_bytes, timeout_s=child_timeout)

    # control_denies: union
    child_control_denies = tuple(
        sorted(set(parent.control_denies) | set(request.control_denies))
    )

    # product_read_proof_mode: stricter (lower permissiveness index); absent → absent
    child_proof_mode: str | None = None
    if parent.product_read_proof_mode is not None and request.product_read_proof_mode is not None:
        p_order = _PROOF_MODE_ORDER.get(parent.product_read_proof_mode, 1)
        r_order = _PROOF_MODE_ORDER.get(request.product_read_proof_mode, 1)
        # Lower index = stricter; pick the stricter one
        if p_order <= r_order:
            child_proof_mode = parent.product_read_proof_mode
        else:
            child_proof_mode = request.product_read_proof_mode

    return CapabilityGrant(
        schema_version=SUPPORTED_SCHEMA_VERSION,
        grant_id=new_grant_id,
        roots=child_roots,
        operations=child_ops,
        trust_class=request.trust_class,
        writes=child_writes,
        control_denies=child_control_denies,
        limits=child_limits,
        product_read_proof_mode=child_proof_mode,
        network=child_network,
        children=child_children,
    )


# ── CapabilityIssuer ──────────────────────────────────────────────────────────


class CapabilityIssuer:
    """Tracks active-grant state for the capability lifecycle.

    A grant not issued by this instance, or that is expired or revoked, fails
    verification. Child grants are the intersection of parent and request.
    """

    def __init__(self) -> None:
        # grant_id → (CapabilityGrant, revoked: bool, expires_at_monotonic: float | None)
        self._grants: dict[str, tuple[CapabilityGrant, bool, float | None]] = {}

    def _new_grant_id(self) -> str:
        return "grant-" + secrets.token_hex(16)

    def issue_root_grant(
        self,
        roots: list[str],
        operations: list[str],
        trust_class: str,
        writes_allowed_roots: list[str],
        control_denies: list[str],
        *,
        limits: _Limits | None = None,
        network: _NetworkGrant | None = None,
        children: _ChildrenGrant | None = None,
        product_read_proof_mode: str | None = None,
        expires_in_s: float | None = None,
    ) -> CapabilityGrant:
        """Issue a new root grant and register it with this issuer.

        The grant_id is generated internally and cannot be supplied by the
        caller, preventing caller-built replay attacks.

        Raises CapabilityRefused if ``operations`` is empty.
        """
        if not operations:
            raise CapabilityRefused(
                "denied-empty-operations",
                "operations must be non-empty",
            )
        grant_id = self._new_grant_id()
        grant = CapabilityGrant(
            schema_version=SUPPORTED_SCHEMA_VERSION,
            grant_id=grant_id,
            roots=tuple(sorted(roots)),
            operations=tuple(sorted(operations)),
            trust_class=trust_class,
            writes=_WritesGrant(allowed_roots=tuple(sorted(writes_allowed_roots))),
            control_denies=tuple(sorted(control_denies)),
            limits=limits if limits is not None else _Limits(),
            product_read_proof_mode=product_read_proof_mode,
            network=network,
            children=children,
        )
        expires_at: float | None = None
        if expires_in_s is not None:
            expires_at = time.monotonic() + expires_in_s
        self._grants[grant_id] = (grant, False, expires_at)
        return grant

    def issue_child_grant(
        self,
        parent: CapabilityGrant,
        request: CapabilityGrant,
    ) -> CapabilityGrant:
        """Issue a child grant as the intersection of *parent* and *request*.

        Verifies the parent is currently valid before issuing.

        Raises CapabilityRefused if the parent is not valid.
        """
        if not self.verify_grant(parent):
            raise CapabilityRefused(
                "denied-invalid-parent",
                "parent grant is not valid (not issued here, expired, or revoked)",
            )
        new_id = self._new_grant_id()
        child = intersect_grants(parent, request, new_grant_id=new_id)
        self._grants[new_id] = (child, False, None)
        return child

    def revoke_grant(self, grant_id: str) -> None:
        """Revoke a grant.  Revoked grants fail all future verifications."""
        entry = self._grants.get(grant_id)
        if entry is not None:
            grant, _, expires_at = entry
            self._grants[grant_id] = (grant, True, expires_at)

    def verify_grant(self, grant: CapabilityGrant) -> bool:
        """Return True iff *grant* was issued by this issuer and is not expired or revoked.

        A caller-built grant (grant_id not in this registry) or a grant whose
        fields do not match the registered copy both return False.
        """
        entry = self._grants.get(grant.grant_id)
        if entry is None:
            return False
        registered_grant, revoked, expires_at = entry
        if revoked:
            return False
        if expires_at is not None and time.monotonic() > expires_at:
            return False
        # Guard against a replayed grant with altered fields (privilege escalation)
        return registered_grant is grant or registered_grant == grant


# ── In-code schema validation ─────────────────────────────────────────────────

# Fields allowed in a security-capability.v1 record dict.
_ALLOWED_GRANT_KEYS: Final[frozenset[str]] = frozenset({
    "schema_version",
    "grant_id",
    "roots",
    "operations",
    "trust_class",
    "writes",
    "product_read_proof_mode",
    "control_denies",
    "network",
    "children",
    "limits",
})

# Fields required in a security-capability.v1 record dict.
_REQUIRED_GRANT_KEYS: Final[frozenset[str]] = frozenset({
    "schema_version",
    "grant_id",
    "roots",
    "operations",
    "trust_class",
    "writes",
    "control_denies",
    "limits",
})


def validate_grant_dict(d: dict) -> tuple[bool, str]:
    """Validate a security-capability.v1 record dict in code.

    Checks schema_version, required fields, and absence of unknown
    authority-shaped fields.  Does not import jsonschema at runtime.

    Returns:
        (True, "ok") when the record is schema-valid.
        (False, denial_code) when the record is invalid; denial_code is one of:
          denied-unknown-schema-version — unknown or wrong schema_version.
          denied-missing-required-field — a required field is absent.
          denied-unknown-authority-field — an authority-shaped field not in the schema.
          denied-empty-operations — operations list is empty.
    """
    if not isinstance(d, dict):
        return False, "denied-missing-required-field"

    version = d.get("schema_version")
    if not isinstance(version, int) or version != SUPPORTED_SCHEMA_VERSION:
        return False, "denied-unknown-schema-version"

    missing = _REQUIRED_GRANT_KEYS - set(d.keys())
    if missing:
        return False, "denied-missing-required-field"

    # No unknown keys (unknown authority-shaped fields must be refused).
    unknown = set(d.keys()) - _ALLOWED_GRANT_KEYS
    if unknown:
        return False, "denied-unknown-authority-field"

    ops = d.get("operations", [])
    if not isinstance(ops, (list, tuple)) or len(ops) == 0:
        return False, "denied-empty-operations"

    return True, "ok"
