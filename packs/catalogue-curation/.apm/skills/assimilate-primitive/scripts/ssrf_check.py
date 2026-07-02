#!/usr/bin/env python3
"""SSRF-guarded source validation for catalogue-curation ingest (RFC-0059,
spec "URL-source SSRF confinement").

A source is a local path or a URL. A URL is fetched only over an allowlisted
scheme, and never to a private / loopback / link-local / cloud-metadata address
— the design-time control is the allowlist, not "validate the URL". Pure-stdlib,
no network calls: this validates the *target* of a fetch before the fetch runs.

**Duplicated, by design.** Both `assimilate-primitive` and `assimilate-repo`
carry a byte-identical copy under their own `scripts/` (the pack model has no
cross-skill shared-code location). `tools/lint-catalogue-curation-guard.py`
enforces the copies stay in sync — edit one, the lint fails until both match.

Usage (as a library): `check_source(src)` raises `SsrfRejected` on a
disallowed source; returns the normalized kind otherwise.
"""

from __future__ import annotations

import ipaddress
import socket
from urllib.parse import urlsplit

ALLOWED_URL_SCHEMES = frozenset({"https", "git", "ssh"})
# Schemes that turn "fetch a URL" into a local-file read or an SSRF pivot.
REJECTED_URL_SCHEMES = frozenset({"file", "ftp", "gopher", "data", "http"})


class SsrfRejected(ValueError):
    """A source was rejected by the ingest SSRF policy."""


def _is_blocked_ip(host: str) -> bool:
    """True if host is an IP literal (or resolves) to a private / loopback /
    link-local / metadata range. A hostname that does not resolve is treated as
    not-an-IP here (the fetch will fail loudly on its own)."""
    candidates: list[str] = [host]
    try:
        # Resolve DNS names too — a name pointing at 169.254.169.254 is the pivot.
        infos = socket.getaddrinfo(host, None)
        candidates.extend(info[4][0] for info in infos)
    except (socket.gaierror, UnicodeError, OSError):
        pass
    for cand in candidates:
        try:
            ip = ipaddress.ip_address(cand)
        except ValueError:
            continue
        if (
            ip.is_private
            or ip.is_loopback
            or ip.is_link_local  # 169.254/16 and fe80::/10 — includes cloud metadata
            or ip.is_reserved
            or ip.is_multicast
            or ip.is_unspecified
        ):
            return True
    return False


def check_url(url: str) -> None:
    """Raise SsrfRejected unless the URL is safe to fetch.

    NOTE: this validates the *initial* URL's host only. It cannot cover a 3xx
    redirect to a blocked host, nor a DNS-rebind between this check and the
    fetch (an inherent TOCTOU window). The fetch call-site MUST disable redirects
    or re-run check_url on every redirect target, and pin/re-resolve the host at
    connect time — see the skill's ingest-safety reference."""
    parts = urlsplit(url)
    scheme = parts.scheme.lower()
    if scheme in REJECTED_URL_SCHEMES:
        raise SsrfRejected(f"scheme '{scheme}' is not allowed for an ingest source")
    if scheme not in ALLOWED_URL_SCHEMES:
        raise SsrfRejected(
            f"scheme '{scheme or '(none)'}' is not on the allowlist "
            f"{sorted(ALLOWED_URL_SCHEMES)}"
        )
    host = parts.hostname or ""
    if not host:
        raise SsrfRejected("URL has no host")
    if _is_blocked_ip(host):
        raise SsrfRejected(
            f"host '{host}' resolves to a private/loopback/link-local/metadata "
            "address — refused"
        )


def looks_like_url(src: str) -> bool:
    """A source string is treated as a URL when it has a multi-char URL scheme.

    A single-letter scheme is a Windows drive path (`C:\\...`), not a URL — real
    URL schemes are >= 2 chars, so requiring that avoids misclassifying a
    drive-letter local path as a URL and rejecting it."""
    scheme = urlsplit(src).scheme
    return len(scheme) >= 2


def check_source(src: str) -> str:
    """Validate an ingest source. Returns 'url' or 'path'; raises SsrfRejected
    for a disallowed URL. A local path is returned as 'path' (still write-jailed
    on land; symlink/traversal is handled by write_jail, not here)."""
    if looks_like_url(src):
        check_url(src)
        return "url"
    return "path"


if __name__ == "__main__":
    import sys

    try:
        kind = check_source(sys.argv[1] if len(sys.argv) > 1 else "")
    except SsrfRejected as exc:
        print(f"ssrf_check: rejected — {exc}", file=sys.stderr)
        raise SystemExit(2)
    print(f"ssrf_check: ok ({kind})")
