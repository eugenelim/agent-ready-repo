# Scanner suppression and pin hygiene

- **Slug:** `scanner-suppression-and-pin-hygiene`
- **Status:** Accepted
- **Accepted:** 2026-11-05 by eugenelim, lifecycle owner. A fresh independent intent-mode shaping review on 2026-11-05 returned zero MALFORMED tokens.
- **Shaping-reviewed:** 2026-11-05
- **De-risked:** 2026-11-05
- **Level:** feature
- **Owner:** eugenelim
- **Governed by:** [spec/build-check-coverage-gaps Decision 1](../../specs/build-check-coverage-gaps/spec.md), [spec/semgrep-selftest-batching](../../specs/semgrep-selftest-batching/spec.md), [spec/npm-sca-gate](../../specs/npm-sca-gate/spec.md), and [spec/secret-scanner-for-api-key-workflows Assumption 5](../../specs/secret-scanner-for-api-key-workflows/spec.md)

## Outcome

SAST and npm-audit suppressions and the package installs that support their gates have explicit, durable integrity and expiry controls.

## Opportunity

The active SAST manifest is range-based, suppression policy is partly undocumented or able to degrade locally, the npm allowlist has no demand yet, and `pack-evals.yml` exposes `ANTHROPIC_API_KEY` beside a global npm install without artifact integrity verification.

## What this absorbs

### sast-requirements-hash-locked

Generate and install `tools/requirements-sast-locked.txt` with `--require-hashes`, mirroring the CI-security locked file. `tools/requirements-sast.txt` still specifies `bandit>=1.9,<2` and `semgrep>=1.174,<2`, and no hash-locked counterpart exists. Unblocks when the platform-targeting decision is made first.

### lint-nosec-form-require-id-registry

Add `--require-id-registry` to `lint-nosec-form.py` so an unreachable Bandit registry exits 2 instead of leaving an exit-0 caveat, and decide whether Bandit is a hard `make build-check` prerequisite. This was deferred because making Bandit mandatory for every contributor has a real cost and needs its own decision. `docs/specs/bandit-nosec-form-lint/spec.md:3` records that AC4b’s `build-check-installs-bandit-unconditionally` deferral was closed by `build-check-coverage-gaps`; CI now installs and probes Bandit unconditionally. The remaining degraded behavior is local and narrower than the original entry stated.

### sast-nosemgrep-has-no-form-lint (moved to `semgrep-registry-ruleset-pinning`; not delivered here)

Record the repository-wide canonical `nosemgrep` suppression form. `tools/lint-nosemgrep-form.py` already gates form from `build-check`, using Semgrep 1.175.0 core-binary patterns for inline and previous-line forms across `#`, `//`, `<!-- -->`, and `/* */`. Decide whether the statement belongs in an ADR-0084 addendum or a new ADR; that decision also owns Semgrep pinning because `tools/requirements-sast.txt` permits `>=1.174,<2` and the self-test only catches edits to the local pinned patterns, not upstream drift. `tools/lint-nosemgrep-form.py` records this unresolved decision. Unblocks when the ADR-shape decision named by `docs/specs/semgrep-ratchet-integrity/plan.md` is made.

### npm-allowlist-expiry-enforcement

Give `tools/npm-audit-allowlist.toml` a machine-checked expiry like `.snyk` so a suppression cannot outlive its justification. `tools/npm-audit-allowlist.toml` now carries three active `[[allow]]` entries, each with a `reason` and an `unblocked_when` condition that the tool requires but does not check for expiry. Unblocks when the expiry rule is chosen.

### pack-evals-npm-lockfile-integrity

Protect the long-lived API-key workflow introduced by `spec/pack-activation-evals`: `.github/workflows/pack-evals.yml` exposes `ANTHROPIC_API_KEY` and runs `npm install -g @anthropic-ai/claude-code@2.1.185`. The version pin has neither an npm lockfile nor a per-package integrity hash, so a compromised npm CDN or re-tagged release could deliver JavaScript that exfiltrates the key. Research whether global npm install supports `--integrity` or a lockfile; otherwise vendor the tarball or use another install path. `ci-security.yml` already runs gitleaks, actionlint, and zizmor, and none of them verifies the npm artifact. Unblocks when a concrete path to npm global-install integrity verification is found.

## Assumptions

- The `lint-nosec-form.py` scope changed: Bandit is unconditional in CI, while only the proposed local `--require-id-registry` behavior remains.

## Source

- Mode: repo-origin
- Locator: workspace.toml
- Revision: 581dd8b7aefba04f566e4ea9a3213da8c6afb55d

## Current truth

Verified 2026-11-05. All four remaining items are unshipped: `tools/npm-audit-allowlist.toml` has 3 `[[allow]]` entries and no expiry check; `lint-nosec-form.py` has no `--require-id-registry`; `pack-evals.yml:52` still runs a global `npm install` with the API key in scope; `tools/requirements-sast.txt` has no hash-locked counterpart. The `nosemgrep` form decision and Semgrep pin move to `semgrep-registry-ruleset-pinning`, so they no longer wait on a separate ADR-shape question. The `pack-evals` research step is unnecessary: `npm ci` against a committed lockfile verifies each tarball's integrity hash.

## Readiness

- **Route:** brief. See [scanner-suppression-and-pin-hygiene-delivery](../briefs/scanner-suppression-and-pin-hygiene-delivery.md). The four slices are independent; the platform-targeting decision for the hash lock is answered: universal compile for macOS arm64, Linux x86_64 and Windows.
- **First slice:** npm allowlist expiry, with a required `expires` field at most 90 days out.
- **Agent-only proof:** `tools/test-audit-npm.py` gains expired-entry and missing-expiry cases.
- **Manual dependency:** one CI dispatch after the `pack-evals.yml` change, non-blocking.

## Non-goals

- Pinning or vendoring the Semgrep registry rulesets and the `nosemgrep` form decision; both moved to `semgrep-registry-ruleset-pinning`.
- JavaScript scanner coverage, owned by `sast-scanner-coverage-expansion`.

## Riskiest assumption

**Riskiest assumption:** a hash-locked SAST manifest can install on every contributor platform. Tested agent-only by a `--require-hashes` install in a fresh venv on this host, with the other platforms covered by the non-blocking runner spot-check.

## De-risk result

2026-11-05. Ran `uv pip compile tools/requirements-sast.txt --generate-hashes --universal`, then installed the result into a fresh venv under `.context/` with `--require-hashes`. Result: 87 packages locked with hashes in 4.9 seconds; install took 11 seconds; `semgrep 1.183.0`, `bandit 1.9.4` and `pip-audit 2.10.1` all run. Two lines carry platform markers, which shows the universal compile varies by platform. This host only proves the install; Windows and Linux runners stay the non-blocking spot-check. Verdict: supported on this host.

## Decisions

- Bandit is a hard prerequisite of `make build-check`, matching CI. Decided 2026-11-05 by eugenelim. This settles the open question in `lint-nosec-form-require-id-registry`.
