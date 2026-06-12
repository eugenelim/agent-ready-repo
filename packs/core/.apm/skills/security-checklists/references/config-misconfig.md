# config-misconfig — CORS, IAM, IaC, server configuration

> **Loaded when:** the change edits server/framework config, CORS, IAM/role
> grants, infrastructure-as-code, container or deployment settings.
> **Standards:** OWASP Top 10:2025 A02 (Security Misconfiguration) · ASVS 5.0
> V14 (Configuration) · Proactive Controls 2024 C5 (Secure by Default
> Configurations).
> **Delegation legend:** `tool` = scanner-owned · `hybrid` = scanner finds the
> flow, you judge the fix · `reason` = reviewer-only judgment.

## Spec-stage (proactive control)

At design time, the control is **secure-by-default** — the spec should name
the least-privilege posture (which origins, which principals, which ports)
rather than leaving defaults to be hardened later. A config AC reads "CORS
allows exactly origin X with credentials off," not "configure CORS" (ASVS 5.0
V14; Proactive Controls 2024 C5).

## Implementation checks

- `tool` **IaC misconfiguration.** Public buckets, open security groups,
  over-broad IAM — IaC scanners (Checkov/tfsec/KICS, or Semgrep/CodeQL rules)
  own the common patterns; confirm one is wired. If none is detected, flag
  `degraded: no scanner` and reason the diff by hand rather than passing it
  silently.
- `reason` **CORS.** `Access-Control-Allow-Origin: *` together with
  `Allow-Credentials: true` is a credential-leak misconfiguration; reflecting
  the `Origin` header without an allowlist is the same bug in disguise.
- `reason` **IAM / role grants.** Wildcards in actions or resources
  (`"*"`), `PassRole` over-grants, and trust policies that admit too broad a
  principal are least-privilege violations a reviewer judges in context.
- `reason` **Default credentials & exposed surfaces.** Default admin
  passwords, debug/management endpoints enabled, directory listing, verbose
  error pages exposing stack traces or versions.
- `reason` **Security headers / TLS posture.** Missing HSTS, permissive
  `Content-Security-Policy`, TLS verification disabled, or downgraded
  protocol/cipher settings.

## Established-helper bypass

Resolve the repo's sanctioned config/module (the hardened web-server base, the
shared IAM module, the CORS middleware with the allowlist) and flag a change
that defines a one-off permissive config inline instead of extending the
blessed default — the shared module is where secure-by-default was already
decided.
