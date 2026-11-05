# Brief: scanner suppressions and pinned installs have integrity and expiry

- **Slug:** `scanner-suppression-and-pin-hygiene-delivery`
- **Received:** 2026-11-05
- **Owner:** eugenelim
- **Status:** Ready
- **Ready confirmed:** 2026-11-05 by eugenelim, lifecycle owner. Bound to the file as reviewed with no blocker or concern by an independent delivery-brief review at commit `2607e4521`; the two nits it raised were removed afterwards, recorded as nonmaterial by the lifecycle owner. Slice membership and status are the Spec map's; this line does not restate them.
- **Parent intent:** intent:scanner-suppression-and-pin-hygiene

## Outcome

Every SAST and npm-audit suppression has a machine-checked expiry or form, and the installs that feed the SAST gate and the API-key workflow verify artifact integrity.

## Scope / Non-goals

**In scope.** Four slices: npm allowlist expiry, `--require-id-registry` for the nosec lint, a lockfile install in `pack-evals.yml`, and a hash-locked SAST manifest.

**Out of scope, each with an owner.**

- Pinning or vendoring the Semgrep registry rulesets and the `nosemgrep` form decision: `semgrep-registry-ruleset-pinning`.
- JavaScript coverage: `sast-scanner-coverage-expansion`.

## Current-state evidence

Checked 2026-11-05.

- `tools/npm-audit-allowlist.toml` has 3 `[[allow]]` entries. `tools/audit-npm.py` requires `reason` and `unblocked_when` but checks no expiry.
- `tools/lint-nosec-form.py` has no `--require-id-registry` option.
- `.github/workflows/pack-evals.yml:52` runs `npm install -g @anthropic-ai/claude-code@2.1.185` with the API key in the job. No lockfile exists for it.
- `tools/requirements-sast.txt` is range-based and has no hash-locked counterpart.

## Constraints / Appetite

- Non-waivable: a new check fails closed. An unreadable allowlist or registry is an error, not a pass.
- Each spec settles its own choices. Suggested defaults: allowlist `expires` at most 90 days out; hash lock built with `uv pip compile --generate-hashes` for macOS arm64, Linux x86_64 and Windows; a committed lockfile for the Claude Code CLI install in `pack-evals.yml`.
- Appetite: four small slices.

## Assumptions / Risks

- **[Risk]** Making Bandit mandatory locally adds contributor cost. The CI already requires it; the spec records the cost.
- **[Risk]** The hash lock breaks on a platform that resolves different wheels. The universal compile is the control; slice 4 proves it on the author's macOS arm64 host and lists the others for the CI run.

## Proposed cut

All four are independent. Gating is `agent-only`; the workflow slice needs a CI run for final proof, which is a non-blocking follow-up.

| Slice | Gating | Proof |
| --- | --- | --- |
| 1. npm allowlist expiry | agent-only | `tools/test-audit-npm.py` gains an expired-entry and a missing-expiry case |
| 2. `--require-id-registry` and the Bandit prerequisite | agent-only | The build-check chain's `lint-nosec-form` step passes `--require-id-registry`. With Bandit absent and `SKIP_SAST=1`, that step exits 2 where today it sets a caveat and exits 0; with Bandit present it exits 0. A test pins both |
| 3. `pack-evals.yml` lockfile install | agent-only; network access to the npm registry is allowed for the proof | `actionlint` clean; the workflow installs only via `npm ci` against the committed lockfile, and a posture assertion fails on a restored `npm install -g`; a local install from the lockfile in a clean directory puts a working `claude --version` on the path; the spec states whether `tools/audit-npm.py` covers the new lockfile and extends it if not |
| 4. Hash-locked SAST manifest | agent-only | `--require-hashes` install in a fresh venv succeeds; the `build-check.yml` SAST install step and the `pip install -r tools/requirements-sast.txt` hint printed by `make sast` both name the locked file; the Bandit pin check at `build-check.yml:213` reads `tools/requirements-sast-locked.txt` and agrees with the version the lock installs |

## Ready gaps

None open.

## Decisions

- Bandit is a hard prerequisite of `make build-check`, matching CI. Decided 2026-11-05 by eugenelim. In effect: the `lint-nosec-form` step of the build-check chain fails when Bandit's id registry cannot be resolved, instead of degrading to a caveat, so the prerequisite holds even under `SKIP_SAST=1`.

## Manual follow-ups (non-blocking)

- One CI dispatch of `pack-evals.yml` after slice 3 to confirm the workflow runs end to end.
- Platform spot-checks of the hash lock on Windows and Linux runners after slice 4.

## Spec map

| Spec | Status |
| --- | --- |

## Source

- Mode: repo-origin
- Locator: docs/product/intents/scanner-suppression-and-pin-hygiene.md
