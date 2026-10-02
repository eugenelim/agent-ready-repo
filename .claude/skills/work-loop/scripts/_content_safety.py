"""_content_safety — content-safety guard for Slice 1 semantic writer boundaries.

Accepts a named profile and payload bytes; returns a typed ContentSafetyDecision
without persisting anything. Standard library only.

AC-0014: every Slice 1 durable semantic writer and replay boundary is registered
in SLICE_1_WRITER_BOUNDARIES before use; a missing or unknown profile refuses
without persisting payload bytes. The delivery-content-safety.md §4 Slice 1
writer boundary table names the same set and the same profiles.

AC-0015: rejected payload bytes, excerpts, and content-derived hashes never
leave this module; accepted free text is returned as typed UntrustedData for
consumers. The inert wrapper signals that the value must not be concatenated
into system instructions, commands, tool calls, paths, approvals, or authority.

Classification vocabulary (content-safety-policy.v1):
  public, repository-internal  — may persist as bounded Git text
  restricted                   — requires a controlled reference; cannot persist
  credential, personal         — rejected immediately; producer-declared guard
  unknown                      — rejected as unknown-class

Python 3.11+ standard library only. No third-party imports, no packaging, no
installation.
"""

import hashlib
import re
from dataclasses import dataclass
from typing import ClassVar, Final

__all__ = [
    "ContentSafetyDecision",
    "UntrustedData",
    "POLICY_VERSION",
    "BOUNDARY_PROFILES",
    "SLICE_1_WRITER_BOUNDARIES",
    "check_content_safety",
    "wrap_as_untrusted",
]

# ── Policy identity ──────────────────────────────────────────────────────────

# Stable version identifier for this policy, matching content-safety-policy.v1.
POLICY_VERSION: Final[str] = "slice-1.v1"

# ── Boundary profile definitions ─────────────────────────────────────────────
#
# Limits from delivery-content-safety.md §4 "Boundary profile" table.
# Keys: profile names used in the Semantic boundary and Slice 1 boundary tables.
# Every key in SLICE_1_WRITER_BOUNDARIES must map to a key here.
BOUNDARY_PROFILES: Final[dict[str, dict]] = {
    # 64 KiB: allowlisted identifiers, enums, digests, numbers, repo-relative paths
    "structured-control": {
        "max_bytes": 64 * 1024,
    },
    # 64 KiB: embedded evidence; raw output is a controlled reference, never embedded
    "evidence-embedded-record": {
        "max_bytes": 64 * 1024,
    },
    # 1 MiB total, 64 KiB per free-text field: natural prose is UntrustedData
    "review-report": {
        "max_total_bytes": 1 * 1024 * 1024,
        "max_free_text_bytes": 64 * 1024,
    },
    # 256 KiB, 1 000 conflict paths: paths are repository-relative and classified
    "integration-diagnostic": {
        "max_bytes": 256 * 1024,
    },
    # 64 KiB: raw transcripts and unbounded tool output reject
    "knowledge-observation": {
        "max_bytes": 64 * 1024,
    },
    # Existing result byte cap: uses admission and scanner policy
    "product-addition": {},
}

# ── Slice 1 writer boundary registry ─────────────────────────────────────────
#
# The SINGLE declared registry that every Slice 1 durable semantic writer and
# replay boundary must use. A writer that bypasses this registry or uses a
# profile other than the one assigned here violates the content-safety contract.
#
# The delivery-content-safety.md §4 "Slice 1 writer boundaries" table names this
# same set and these same profiles. The roster test asserts both agree.
#
# T5 writers: initial-plan-review.v1, approval-record.v1, reviewed-execution-envelope.v1
# T7 writers: semantic-evidence-transaction.v1 (frame), evidence-receipt.v1,
#             evidence-supersession.v1
# T3a writers: security-event.v1
SLICE_1_WRITER_BOUNDARIES: Final[dict[str, str]] = {
    "initial-plan-review.v1": "structured-control",
    "approval-record.v1": "structured-control",
    "reviewed-execution-envelope.v1": "structured-control",
    "security-event.v1": "structured-control",
    "semantic-evidence-transaction.v1": "structured-control",
    "evidence-receipt.v1": "evidence-embedded-record",
    "evidence-supersession.v1": "evidence-embedded-record",
}

# ── Classification vocabulary ─────────────────────────────────────────────────

# Only these two classes may persist as bounded Git text.
_PERSISTABLE_CLASSES: Final[frozenset[str]] = frozenset(
    {"public", "repository-internal"}
)
_CREDENTIAL_CLASS: Final[str] = "credential"
_PERSONAL_CLASS: Final[str] = "personal"

# ── C0 control-character scanner ─────────────────────────────────────────────
#
# Rejects C0 control characters (0x00–0x1F) and DEL (0x7F), except:
#   HT (0x09), LF (0x0A), CR (0x0D) — valid whitespace in text content.
# ESC and other C0 survivors are dangerous in terminal-captured streams.
_CONTROL_RE: Final[re.Pattern[str]] = re.compile(
    r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]"
)

# ── Credential scanner patterns ───────────────────────────────────────────────
#
# High-confidence token shapes from the required scanner corpus.
# Matching any pattern returns rejected-credential without payload retention.
_CREDENTIAL_PATTERNS: Final[list[re.Pattern[str]]] = [
    # GitHub personal access tokens (classic 40-char suffix form)
    re.compile(r"ghp_[A-Za-z0-9]{36,}"),
    # GitHub fine-grained PATs
    re.compile(r"github_pat_[A-Za-z0-9_]{76,}"),
    # AWS access key IDs
    re.compile(r"AKIA[0-9A-Z]{16}"),
    # Generic high-entropy API/secret/access-token assignments (case-insensitive)
    re.compile(r"(?i)api[-_]?key\s*[:=]\s*[A-Za-z0-9/+_.\-]{20,}"),
    re.compile(r"(?i)secret[-_]?key\s*[:=]\s*[A-Za-z0-9/+_.\-]{20,}"),
    re.compile(r"(?i)access[-_]?token\s*[:=]\s*[A-Za-z0-9/+_.\-]{20,}"),
]

# ── Personal-data scanner patterns ────────────────────────────────────────────
#
# Direct personal identifiers from the required scanner corpus.
# Matching any pattern returns rejected-personal-data without payload retention.
_PERSONAL_DATA_PATTERNS: Final[list[re.Pattern[str]]] = [
    # Email addresses (any domain)
    re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}"),
    # US Social Security Numbers
    re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
    # US phone numbers (various formats)
    re.compile(r"\b(?:\+1[-. ]?)?\(?\d{3}\)?[-. ]?\d{3}[-. ]?\d{4}\b"),
]

# ── Executable-structure scanner patterns ─────────────────────────────────────
#
# Tool-call objects, shell shebangs, and authority-shaped fields that must not
# persist in any semantic record. These form executable or capability-granting
# structures in the content stream.
_EXECUTABLE_PATTERNS: Final[list[re.Pattern[str]]] = [
    # Agentic tool-call object patterns (common in LLM APIs)
    re.compile(r'"tool_call[s]?"\s*:', re.IGNORECASE),
    re.compile(r'"type"\s*:\s*"tool_use"', re.IGNORECASE),
    re.compile(r'"function"\s*:\s*\{[^}]*"name"\s*:', re.IGNORECASE),
    # Shell shebangs — interpreter invocations that must not appear in records
    re.compile(r"^#!(?:/usr)?/(?:bin|env)\b"),
    # Authority-shaped fields — unknown capability grants or privilege escalations
    re.compile(r'"_(?:grant|authority|sudo|root|admin|capability)\b', re.IGNORECASE),
    # Embedded script/frame tags
    re.compile(r"<(?:script|iframe|object|embed)\b", re.IGNORECASE),
]


# ── Decision dataclass ────────────────────────────────────────────────────────


@dataclass(frozen=True)
class ContentSafetyDecision:
    """Typed content-safety decision returned by check_content_safety.

    Maps to content-safety-decision.v1 schema fields.

    AC-0015 invariant: rejected decisions carry NO payload bytes, excerpts,
    or content-derived hashes. Only `accepted` carries normalized_record_digest.
    The dataclass raises ValueError if either half of the invariant is violated,
    so any code that constructs a decision with a digest on rejection is caught
    at construction time rather than silently leaking.
    """

    source_record_id: str
    policy_version: str
    profile: str
    decision_code: str
    # Present only when decision_code == "accepted". Absent on any rejection.
    normalized_record_digest: str | None = None

    def __post_init__(self) -> None:
        if self.decision_code != "accepted" and self.normalized_record_digest is not None:
            raise ValueError(
                "ContentSafetyDecision: rejected decision must not carry "
                f"normalized_record_digest (decision_code={self.decision_code!r})"
            )
        if self.decision_code == "accepted" and self.normalized_record_digest is None:
            raise ValueError(
                "ContentSafetyDecision: accepted decision must carry "
                "normalized_record_digest"
            )

    @property
    def accepted(self) -> bool:
        """True iff decision_code is 'accepted'."""
        return self.decision_code == "accepted"


# ── UntrustedData wrapper ─────────────────────────────────────────────────────


@dataclass(frozen=True)
class UntrustedData:
    """Typed inert-data wrapper for accepted free text.

    Maps to untrusted-data.v1 schema fields.

    AC-0015: Consumers MUST NOT concatenate .value into system instructions,
    commands, tool calls, paths, approvals, or authority. The value field is
    opaque data, not procedure. The four boolean properties below enforce the
    typed boundary: they always return False because an inert wrapper is
    never an executable.
    """

    record_id: str
    field_path: str
    policy_version: str
    value: str

    # Schema version for untrusted-data.v1 (class-level constant, not a field).
    SCHEMA_VERSION: ClassVar[int] = 1

    def can_select_tools(self) -> bool:
        """Always False: typed inert data cannot select tools (AC-0015)."""
        return False

    def can_grant_authority(self) -> bool:
        """Always False: typed inert data cannot grant authority (AC-0015)."""
        return False

    def can_alter_procedure(self) -> bool:
        """Always False: typed inert data cannot alter procedure (AC-0015)."""
        return False

    def can_supply_executable_path(self) -> bool:
        """Always False: typed inert data cannot supply executable paths (AC-0015)."""
        return False


# ── Internal helpers ──────────────────────────────────────────────────────────


def _reject(
    source_record_id: str,
    policy_version: str,
    profile: str,
    decision_code: str,
) -> ContentSafetyDecision:
    """Construct a rejection decision.

    AC-0015: carries NO payload bytes, excerpts, or content-derived hashes.
    normalized_record_digest is always absent.
    """
    return ContentSafetyDecision(
        source_record_id=source_record_id,
        policy_version=policy_version,
        profile=profile,
        decision_code=decision_code,
        normalized_record_digest=None,
    )


def _accept(
    source_record_id: str,
    policy_version: str,
    profile: str,
    normalized_bytes: bytes,
) -> ContentSafetyDecision:
    """Construct an acceptance decision.

    The normalized_record_digest is the SHA-256 of the normalized bytes,
    prefixed with 'sha256:'. The caller supplies normalized bytes, not raw.
    """
    digest = "sha256:" + hashlib.sha256(normalized_bytes).hexdigest()
    return ContentSafetyDecision(
        source_record_id=source_record_id,
        policy_version=policy_version,
        profile=profile,
        decision_code="accepted",
        normalized_record_digest=digest,
    )


def _profile_max_bytes(profile_cfg: dict) -> int | None:
    """Return the byte cap for the given profile config, or None if uncapped."""
    if "max_bytes" in profile_cfg:
        return profile_cfg["max_bytes"]
    if "max_total_bytes" in profile_cfg:
        return profile_cfg["max_total_bytes"]
    return None


# ── Public guard entry point ──────────────────────────────────────────────────


def check_content_safety(
    profile: str,
    payload: bytes,
    *,
    source_record_id: str,
    classification: str = "public",
) -> ContentSafetyDecision:
    """Apply the named content-safety profile to payload bytes.

    Returns a ContentSafetyDecision without persisting anything.
    On rejection, carries NO payload bytes, excerpts, or content-derived hashes.
    On acceptance, carries a SHA-256 digest of the normalized bytes.

    Checks, in order:
      1. Profile lookup       — unknown profile: rejected-missing-profile
      2. Classification check — credential: rejected-credential
                               personal: rejected-personal-data
                               restricted or unknown: rejected-unknown-class
      3. UTF-8 decoding       — invalid encoding: rejected-encoding
      4. Control characters   — C0 except HT/LF/CR and DEL: rejected-encoding
      5. Size limit           — over profile cap: rejected-size
      6. Executable structure — tool-call, shebang, authority field: rejected-structure
      7. Credential scanner   — high-confidence token patterns: rejected-credential
      8. Personal-data scanner — direct identifiers: rejected-personal-data
      9. Accept               — returns digest of CRLF-normalized UTF-8 bytes

    Args:
        profile:          Named boundary profile from BOUNDARY_PROFILES.
        payload:          Raw bytes to evaluate. Never stored on rejection.
        source_record_id: Stable identity of the source record.
        classification:   Producer-declared content class. Defaults to 'public'.
                         Only 'public' and 'repository-internal' may persist.
    """
    # Step 1 — Profile lookup. An unknown profile blocks without inspecting payload.
    profile_cfg = BOUNDARY_PROFILES.get(profile)
    if profile_cfg is None:
        return _reject(source_record_id, POLICY_VERSION, profile, "rejected-missing-profile")

    # Step 2 — Classification check. Reject non-persistable classes immediately.
    if classification not in _PERSISTABLE_CLASSES:
        if classification == _CREDENTIAL_CLASS:
            return _reject(source_record_id, POLICY_VERSION, profile, "rejected-credential")
        if classification == _PERSONAL_CLASS:
            return _reject(source_record_id, POLICY_VERSION, profile, "rejected-personal-data")
        # restricted and any unknown class use the unknown-class code.
        return _reject(source_record_id, POLICY_VERSION, profile, "rejected-unknown-class")

    # Step 3 — UTF-8 encoding check. Payload must decode without error.
    try:
        text = payload.decode("utf-8", errors="strict")
    except UnicodeDecodeError:
        return _reject(source_record_id, POLICY_VERSION, profile, "rejected-encoding")

    # Step 4 — Control-character check. C0 except HT/LF/CR and DEL reject.
    if _CONTROL_RE.search(text):
        return _reject(source_record_id, POLICY_VERSION, profile, "rejected-encoding")

    # Step 5 — Size limit against the profile cap.
    max_bytes = _profile_max_bytes(profile_cfg)
    if max_bytes is not None and len(payload) > max_bytes:
        return _reject(source_record_id, POLICY_VERSION, profile, "rejected-size")

    # Step 6 — Executable-structure check. Tool-call objects, shebangs, and
    # authority-shaped fields signal executable or capability-granting content.
    for pattern in _EXECUTABLE_PATTERNS:
        if pattern.search(text):
            return _reject(source_record_id, POLICY_VERSION, profile, "rejected-structure")

    # Step 7 — Credential scanner. High-confidence token patterns reject the
    # whole record without retaining any payload bytes.
    for pattern in _CREDENTIAL_PATTERNS:
        if pattern.search(text):
            return _reject(source_record_id, POLICY_VERSION, profile, "rejected-credential")

    # Step 8 — Personal-data scanner. Direct personal identifiers reject without
    # payload retention.
    for pattern in _PERSONAL_DATA_PATTERNS:
        if pattern.search(text):
            return _reject(source_record_id, POLICY_VERSION, profile, "rejected-personal-data")

    # Step 9 — Accept. Normalize CRLF→LF (matches canonical_contract normalization)
    # and compute the SHA-256 digest of the normalized UTF-8 bytes.
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    normalized_bytes = normalized.encode("utf-8")
    return _accept(source_record_id, POLICY_VERSION, profile, normalized_bytes)


# ── UntrustedData constructor ─────────────────────────────────────────────────


def wrap_as_untrusted(
    record_id: str,
    field_path: str,
    value: str,
) -> UntrustedData:
    """Wrap accepted free text as typed inert UntrustedData.

    The returned wrapper records the policy version that admitted the value
    and the field path within the source record. Callers MUST NOT pass a value
    that was rejected by check_content_safety; this function has no way to
    verify that precondition and trusts the caller's decision record.

    Consumers of the returned UntrustedData MUST NOT concatenate .value into
    system instructions, commands, tool calls, paths, approvals, or authority.
    """
    return UntrustedData(
        record_id=record_id,
        field_path=field_path,
        policy_version=POLICY_VERSION,
        value=value,
    )
