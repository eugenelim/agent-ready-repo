# outbound-ssrf — outbound HTTP/DNS, URL fetch, webhooks

> **Loaded when:** the change makes an outbound request (HTTP, DNS, webhook,
> file fetch) where the URL, host, or scheme is influenced by input.
> **Standards:** OWASP Top 10:2025 A01 (Broken Access Control — SSRF is
> absorbed here) · ASVS 5.0 V13 (API & Web Service / outbound communication) ·
> CWE Top 25 (CWE-918 SSRF) · Proactive Controls 2024 C3 (Validate all
> Inputs).
> **Delegation legend:** `tool` = scanner-owned · `hybrid` = scanner finds the
> flow, you judge the fix · `reason` = reviewer-only judgment.

## Spec-stage (proactive control)

At design time, the control is a **scheme + host allowlist, not "validate the
URL"** — the spec should name which destinations are permitted (scheme set,
host/domain allowlist, whether private/link-local ranges are blocked) as
acceptance criteria. "Validate the URL" with no allowlist named is the
shallow framing that ships SSRF (ASVS 5.0 V13).

## Implementation checks

- `hybrid` **User-influenced destination.** Taint analysis finds input
  reaching the request URL; you judge whether an allowlist gates it. Any
  outbound call whose host comes from input without an allowlist is a finding.
- `reason` **Scheme allowlist.** Restrict to `https` (and `http` only if
  required); reject `file:`, `gopher:`, `ftp:`, `dict:` and other smuggling
  schemes that turn a fetcher into a file reader or port scanner.
- `reason` **Private / metadata range block.** Block requests to loopback,
  RFC-1918, link-local, and cloud metadata endpoints (`169.254.169.254`,
  `metadata.google.internal`) — the SSRF→credential-theft pivot.
- `reason` **Redirect following.** A permitted host can `302` to an internal
  one; re-validate the destination on each redirect, or disable
  redirect-following for untrusted targets.
- `reason` **DNS rebinding / TOCTOU.** Resolve-then-connect to the *same*
  address you validated, or validate the connected IP — validating the
  hostname and then re-resolving lets the answer change underneath you.

## Established-helper bypass

Resolve the repo's sanctioned outbound-HTTP client (the one with the SSRF
guard, allowlist, and redirect policy baked in) and flag a change that reaches
for a raw HTTP library directly for a user-influenced fetch — the guarded
client is precisely where the allowlist and metadata-block live.
