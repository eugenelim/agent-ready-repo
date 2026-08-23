---
title: "config-misconfig"
type: "Reference"
status: "Active"
license: "Apache-2.0 OR MIT"
compatibility: "repo-original"
boundaries:
  - filesystem_read_untrusted
---
# config-misconfig

Use when the change edits CORS, IAM, infrastructure-as-code, server/framework
configuration, containers, or deployment settings.

## Spec-stage

Require secure-by-default posture: exact origins, principals, ports, and
least-privilege grants rather than vague hardening later.

## Implementation checks

- `tool` Confirm IaC or configuration scanners are wired.
- `reason` Reject wildcard CORS with credentials or reflected origins.
- `reason` Inspect IAM wildcards, broad trust policies, and `PassRole`.
- `reason` Remove default credentials, debug surfaces, and verbose errors.
- `reason` Confirm security headers and TLS posture are not weakened.

## Established-helper bypass

Resolve the sanctioned hardened module or configuration helper and flag one-off
permissive settings that bypass it.
