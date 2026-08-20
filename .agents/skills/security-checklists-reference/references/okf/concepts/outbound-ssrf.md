---
title: "outbound-ssrf"
type: "Reference"
status: "Active"
license: "Apache-2.0 OR MIT"
compatibility: "repo-original"
boundaries:
  - filesystem_read_untrusted
---
# outbound-ssrf

Use when the change makes outbound HTTP, DNS, webhook, or fetch calls where the
URL, host, or scheme is influenced by input.

## Spec-stage

Require explicit scheme and host allowlists, private-address blocking, and
redirect handling rather than generic URL validation.

## Implementation checks

- `hybrid` Gate user-influenced destinations with an allowlist.
- `reason` Restrict schemes and reject file or port-scanning schemes.
- `reason` Block loopback, private, link-local, and metadata endpoints.
- `reason` Re-validate redirects or disable following for untrusted targets.
- `reason` Avoid DNS rebinding by validating the connected address.

## Established-helper bypass

Resolve the sanctioned outbound client with SSRF protections and flag raw
HTTP-library calls for user-influenced fetches.
