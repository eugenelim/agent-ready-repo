# supply-chain — dependencies, lockfiles, build trust

> **Loaded when:** the change adds, removes, or repins a dependency; edits a
> lockfile or package manifest; or changes how build artifacts are fetched.
> **Standards:** **OWASP Top 10:2025 A03 (Software Supply Chain Failures — new
> in 2025)** · ASVS 5.0 V10 (Coding & Build / dependency management) ·
> Proactive Controls 2024 C2 (Use Secure Components / leverage frameworks).
> **Delegation legend:** `tool` = scanner-owned · `hybrid` = scanner finds the
> flow, you judge the fix · `reason` = reviewer-only judgment.

## Spec-stage (proactive control)

At design time, a new dependency is a forever-decision — the spec/plan should
justify it (a second caller actually needs it) and prefer a maintained,
widely-used component over a thin or abandoned one. Where the change adds a
dependency, that addition should be a recorded decision, not an incidental
import (ASVS 5.0 V10; Proactive Controls 2024 C2).

## Implementation checks

- `tool` **Known CVEs.** Vulnerable-version detection is SCA's job, not the
  reviewer's — confirm `pip-audit` / `npm audit` / `govulncheck` /
  `cargo audit` / `bundler-audit` (or Snyk) is wired against the lockfile. If
  no scanner is detected, flag `degraded: no scanner` and state that CVE
  coverage is unverified — never assert the dependency tree is clean by eye.
- `reason` **Typosquat / dependency confusion.** A new package name one
  character off a popular one, or an internal name resolvable from a public
  index, is a reasoning finding a CVE scanner won't raise — verify the package
  is the intended one and the registry/scope is correct.
- `reason` **Pinning & integrity.** Dependencies should be pinned with a
  lockfile and integrity hashes; an unpinned or hash-less add lets the
  resolved artifact change silently.
- `reason` **Maintenance & provenance.** Flag an unmaintained or
  single-maintainer dependency added to a security-relevant path, and build
  steps that fetch from a non-pinned or unverified source (`curl | sh`).
- `reason` **Transitive surface.** A small direct add can pull a large
  transitive tree; note when the dependency footprint is disproportionate to
  the need.

## Established-helper bypass

Resolve the repo's sanctioned way to add a dependency (a workspace catalog, a
vetted-internal mirror, a recorded-in-ADR process). Flag a change that adds a
raw third-party dependency outside that path when the blessed mechanism or an
already-present equivalent exists — re-implementing or re-importing duplicates
the maintenance and audit surface the sanctioned path centralizes.
