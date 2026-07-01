#!/usr/bin/env python3
"""
tier3.py — the Tier-3 managed-API assembly interface (transport-free).

The skill makes **no network call**. Tier 3 is reached **only** through the
explicit, declaration-gated assembly path here — never by automatic degradation
or upgrade (``convert.py:dispatch`` constructs only Tiers 0–2). This module is the
**sole** construction site for ``contract.TIER_3``. It:

  * validates an egress declaration (``{endpoint-allowlist, residency-region}``),
    **fail-closed** — no output is stamped unless the declaration is well-formed;
  * wraps adopter-obtained OCR text in the unified contract with
    ``tier="3-managed-api"``, ``requires-review: true`` and a fixed
    ``extraction-confidence: "low"`` (the skill neither performed nor verified the
    vendor OCR, so it never claims ``high`` for output it did not produce);
  * echoes the declared destination (endpoint + residency) into provenance so the
    egress target is auditable.

It ships **no HTTP client, no vendor SDK, no socket**, and accepts **no auth
material** (the declaration's key set must equal exactly the two allowed keys).
The actual vendor call is the adopter's provisioned transport; the socket-level
"egress only to the named destination" is that transport's obligation. The
endpoint validation here is **provenance-hygiene / a footgun-reducer, not an SSRF
control** — the skill never resolves a hostname or opens a socket. See
``references/tier3-managed-api.md``.
"""
from __future__ import annotations

import ipaddress
from pathlib import Path
from typing import Mapping

import contract
import safe_io

# The egress declaration's key set must equal EXACTLY these two keys — an
# allowlist of keys, not a denylist of credential-looking names, so no auth
# material (`authorization`, `x-api-key`, …) can be smuggled in beside them.
_ALLOWED_KEYS = frozenset({"endpoint-allowlist", "residency-region"})

# Wildcard / scheme-less catch-alls rejected outright.
_REJECT_LITERALS = frozenset({"", "*", ".", "0.0.0.0", "::"})

# Metadata / loopback hostnames rejected in disguise. NON-EXHAUSTIVE — the
# connect-time block in the adopter transport is authoritative; this only reduces
# the obvious footgun.
_REJECT_HOSTS = frozenset({"localhost", "metadata", "metadata.google.internal"})
_REJECT_HOST_SUFFIXES = (".localhost", ".internal")


class DeclarationError(ValueError):
    """The egress declaration is missing or malformed. Raised **fail-closed** — no
    Tier-3 output is ever stamped when this fires."""


def _reject_endpoint_element(raw: str) -> str | None:
    """Return a rejection reason for one endpoint element, or None if allowed.

    Footgun-reducer, not an SSRF control: rejects wildcards / catch-alls,
    metadata/loopback hostnames, and IP literals that resolve to a loopback /
    link-local / private / metadata / reserved range (IPv4, IPv6, and IPv4-mapped
    IPv6 uniformly, by rule). A CIDR or otherwise malformed IP-looking element is
    rejected rather than silently treated as a hostname.

    OUT OF SCOPE (the adopter transport's connect-time block is authoritative —
    see the grounding doc): alternate-radix IP encodings of an internal target
    (octal ``0177.0.0.1``, decimal ``2130706433``, hex ``0x7f000001``) that
    ``ipaddress`` does not parse are treated as ordinary hostnames here."""
    # Canonicalize a trailing dot up front (`metadata.google.internal.` and
    # `169.254.169.254.` resolve identically to their dotless forms) so both the
    # hostname list AND the IP-literal parse below see the canonical value.
    host = raw.strip().rstrip(".")
    if host in _REJECT_LITERALS:
        return f"wildcard / empty / catch-all endpoint {raw!r}"
    low = host.lower()
    if low in _REJECT_HOSTS or any(low.endswith(sfx) for sfx in _REJECT_HOST_SUFFIXES):
        return f"metadata/loopback hostname {raw!r}"
    if "/" in host:
        # An endpoint allowlist names hosts, not CIDRs; a `/` element (e.g. `::/0`,
        # `0.0.0.0/0`) is a malformed/over-broad literal, never a bare hostname.
        return f"CIDR / malformed endpoint {raw!r}"
    try:
        ip = ipaddress.ip_address(host)
    except ValueError:
        return None  # not an IP literal → treated as an ordinary hostname (allowed)
    mapped = getattr(ip, "ipv4_mapped", None)
    if mapped is not None:
        ip = mapped  # canonicalize ::ffff:a.b.c.d to its embedded IPv4
    if (ip.is_loopback or ip.is_link_local or ip.is_private or ip.is_multicast
            or ip.is_unspecified or ip.is_reserved):
        return f"loopback/link-local/private/metadata IP {raw!r}"
    return None


def validate_declaration(declaration: Mapping[str, object]) -> tuple[list[str], str]:
    """Validate the egress declaration, returning ``(endpoints, residency)``.

    Raises ``DeclarationError`` (fail-closed) on anything malformed: a non-mapping;
    a key set that is not exactly ``{endpoint-allowlist, residency-region}``; an
    empty/non-list endpoint allowlist or a rejected endpoint element; an empty
    residency."""
    if not isinstance(declaration, Mapping):
        raise DeclarationError("egress declaration must be a mapping of "
                               f"{sorted(_ALLOWED_KEYS)}")
    keys = set(declaration)
    if keys != set(_ALLOWED_KEYS):
        raise DeclarationError(
            f"egress declaration keys must be exactly {sorted(_ALLOWED_KEYS)}; got "
            f"{sorted(keys)} — no unknown fields or auth material are accepted"
        )
    endpoints = declaration["endpoint-allowlist"]
    if not isinstance(endpoints, (list, tuple)) or not endpoints:
        raise DeclarationError("endpoint-allowlist must be a non-empty list of hosts")
    cleaned: list[str] = []
    for raw in endpoints:
        if not isinstance(raw, str):
            raise DeclarationError(f"endpoint element must be a string; got {raw!r}")
        reason = _reject_endpoint_element(raw)
        if reason is not None:
            raise DeclarationError(f"rejected endpoint — {reason}")
        cleaned.append(raw.strip())
    residency = declaration["residency-region"]
    if not isinstance(residency, str) or not residency.strip():
        raise DeclarationError("residency-region must be a non-empty string")
    return cleaned, residency.strip()


def _content_type_from_source(source: str) -> str:
    """Derive content-type from the source name's suffix; fall back to
    ``managed-ocr`` when indeterminate. The suffix is normalized to lowercase
    alphanumerics so a stray space or non-ASCII character can't reach a consumer
    keying on ``content-type`` (the value is escaped either way)."""
    suffix = Path(source).suffix.lower().lstrip(".").strip()
    if not suffix or not (suffix.isascii() and suffix.isalnum()):
        return "managed-ocr"
    return suffix


def assemble_tier3(
    ocr_text_path: str | Path, source: str, declaration: Mapping[str, object]
) -> str:
    """Assemble the unified-contract Markdown for adopter-obtained Tier-3 OCR text.

    Refuses (``DeclarationError``, fail-closed) before reading anything if the
    declaration is malformed. On success, reads the OCR text (through the
    ``safe_io.check_input_size`` DoS ceiling), stamps ``tier="3-managed-api"`` with
    a fixed ``low`` confidence + ``requires-review: true`` (the skill did not verify
    the OCR), and echoes the declared endpoint (comma-joined scalar) + residency
    into provenance — all through ``contract.build_frontmatter``'s injection-safe
    escaping, so an injection-bearing endpoint or source name cannot break the
    frontmatter block."""
    endpoints, residency = validate_declaration(declaration)  # gate before any read
    path = Path(ocr_text_path)
    safe_io.check_input_size(path)  # unbounded-read guard on operator-supplied input
    ocr_text = path.read_text(encoding="utf-8", errors="replace")

    fields = {
        "source-file": source,
        "content-type": _content_type_from_source(source),
        "ingestion-date": contract.now_iso(),
        # Auditable egress provenance — comma-joined so the emitter's scalar
        # escaping applies and the value stays parseable.
        "egress-endpoint": ",".join(endpoints),
        "egress-residency": residency,
    }
    frontmatter = contract.build_frontmatter(
        tier=contract.TIER_3,
        extraction_confidence="low",   # fixed — the skill did not verify vendor OCR
        requires_review=True,          # non-negotiable; no caller override
        fields=fields,
    )
    # The OCR text is untrusted document content — it sits below the leading
    # frontmatter fence as inert body, exactly like the Tier-0/2 bodies.
    return frontmatter + "\n\n" + ocr_text.rstrip("\n") + "\n"
