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

## Deferred authority (per-provider secure-config depth)

This module reasons from cross-cutting standards and catches security failure
*classes*; it deliberately does **not** carry per-provider secure-config
baselines (they would be stale on arrival and break tool-neutrality). The
per-provider depth lives in two places, named here by **stable publisher +
document, with no URL and no version** so the pointer stays evergreen by naming
rather than linking:

- **CIS Benchmarks** — the per-service hardening baselines.
- **AWS Well-Architected Security Pillar**, **Microsoft Cloud Adoption
  Framework / Azure Well-Architected Security**, and **Google Cloud
  Architecture Framework (Security)** — each provider's standing
  well-architected security guidance.

The **actual, current per-provider depth lives in the self-updating
policy-as-code / CSPM scanner** the work-loop's infra preflight requires (its
vendor-maintained rulesets *are* these baselines, kept fresh by the vendor) —
not in this pointer. A stale name here never gates a real check; the scanner
does. Confirm the scanner is wired (the `tool` bullet above) rather than
re-deriving provider baselines by hand.

## The reliability-vs-security carve

This module owns **IaC *security* config** (IAM, CORS, public exposure, secrets
posture, TLS). The **reliability / ops** side of infrastructure — idempotent
convergence, blast radius, environment isolation, cost/teardown, drift/rollback,
observability/smoke — lives in the **`operational-safety`** skill, consumed by
`quality-engineer`. Route IaC-security here; route IaC-reliability there. Don't
pull operational checks into this module, and don't let security config drift
into an operational one.

## Established-helper bypass

Resolve the repo's sanctioned config/module (the hardened web-server base, the
shared IAM module, the CORS middleware with the allowlist) and flag a change
that defines a one-off permissive config inline instead of extending the
blessed default — the shared module is where secure-by-default was already
decided.
