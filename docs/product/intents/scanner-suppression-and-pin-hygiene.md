# Scanner suppression and pin hygiene

- **Status:** Draft
- **Level:** feature
- **Authority:** [spec/build-check-coverage-gaps Decision 1](../../specs/build-check-coverage-gaps/spec.md), [spec/semgrep-selftest-batching](../../specs/semgrep-selftest-batching/spec.md), [spec/npm-sca-gate](../../specs/npm-sca-gate/spec.md), and [spec/secret-scanner-for-api-key-workflows Assumption 5](../../specs/secret-scanner-for-api-key-workflows/spec.md)

## Outcome

SAST and npm-audit suppressions and the package installs that support their gates have explicit, durable integrity and expiry controls.

## Opportunity

The active SAST manifest is range-based, suppression policy is partly undocumented or able to degrade locally, the npm allowlist has no demand yet, and `pack-evals.yml` exposes `ANTHROPIC_API_KEY` beside a global npm install without artifact integrity verification.

## What this absorbs

### sast-requirements-hash-locked

Generate and install `tools/requirements-sast-locked.txt` with `--require-hashes`, mirroring the CI-security locked file. `tools/requirements-sast.txt:10` still specifies `bandit>=1.9,<2`, and no hash-locked counterpart exists. Unblocks when the platform-targeting decision is made first.

### lint-nosec-form-require-id-registry

Add `--require-id-registry` to `lint-nosec-form.py` so an unreachable Bandit registry exits 2 instead of leaving an exit-0 caveat, and decide whether Bandit is a hard `make build-check` prerequisite. This was deferred because making Bandit mandatory for every contributor has a real cost and needs its own decision. `docs/specs/bandit-nosec-form-lint/spec.md:3` records that AC4b’s `build-check-installs-bandit-unconditionally` deferral was closed by `build-check-coverage-gaps`; CI now installs and probes Bandit unconditionally. The remaining degraded behavior is local and narrower than the original entry stated.

### sast-nosemgrep-has-no-form-lint

Record the repository-wide canonical `nosemgrep` suppression form. `tools/lint-nosemgrep-form.py` already gates form from `build-check`, using Semgrep 1.175.0 core-binary patterns for inline and previous-line forms across `#`, `//`, `<!-- -->`, and `/* */`. Decide whether the statement belongs in an ADR-0084 addendum or a new ADR; that decision also owns Semgrep pinning because `tools/requirements-sast.txt` permits `>=1.174,<2` and the self-test only catches edits to the local pinned patterns, not upstream drift. `tools/lint-nosemgrep-form.py:45` records this unresolved decision. Unblocks when the ADR-shape decision named by `docs/specs/semgrep-ratchet-integrity/plan.md` is made.

### npm-allowlist-expiry-enforcement

Give `tools/npm-audit-allowlist.toml` a machine-checked expiry like `.snyk` so a suppression cannot outlive its justification. `tools/npm-audit-allowlist.toml:37` is currently `allow = []`; no active suppression exists. Unblocks when the allowlist gains its first entry.

### pack-evals-npm-lockfile-integrity

Protect the long-lived API-key workflow introduced by `spec/pack-activation-evals`: `.github/workflows/pack-evals.yml` exposes `ANTHROPIC_API_KEY` and at line 52 runs `npm install -g @anthropic-ai/claude-code@2.1.185`. The version pin has neither an npm lockfile nor a per-package integrity hash, so a compromised npm CDN or re-tagged release could deliver JavaScript that exfiltrates the key. Research whether global npm install supports `--integrity` or a lockfile; otherwise vendor the tarball or use another install path. No secret scanner is wired today beyond CodeQL and Bandit/Semgrep; adjacent gaps are actionlint and zizmor Security. Unblocks when a concrete path to npm global-install integrity verification is found.

## Assumptions

- The `lint-nosec-form.py` scope changed: Bandit is unconditional in CI, while only the proposed local `--require-id-registry` behavior remains.

## Source

- Mode: repo-origin
- Locator: workspace.toml
- Revision: 581dd8b7aefba04f566e4ea9a3213da8c6afb55d
