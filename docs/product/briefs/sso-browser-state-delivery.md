# Brief: SSO browser state is bounded, minimal and serialized

- **Slug:** `sso-browser-state-delivery`
- **Received:** 2026-11-05
- **Owner:** eugenelim
- **Status:** Ready
- **Ready confirmed:** 2026-11-05 by eugenelim, lifecycle owner. Bound to the file as committed in `a96a878c4`, which an independent delivery-brief review returned `Clean` with no open Ready gap. Slice membership and status are the Spec map's; this line does not restate them.
- **Parent intent:** capability:sso-browser-state-protection

## Outcome

Persistent SSO browser state expires, stores only what it needs, cannot be launched twice at once for one profile, is not recaptured in a loop, and keeps macOS keychain calls inside a lock budget derived from batching and a per-call timeout. Capture and refresh expose three named modes and bounded errors.

## Scope / Non-goals

**In scope.** `sso-broker.py` capture, storage, expiry, cooldown, launch lock, keychain budget, the mode enum, and refresh stderr bounding in `packages/credbroker/credbroker/_sso.py`. The source is `packages/credbroker/`; `packs/credential-brokers/.apm/user-libs/credbroker/_sso.py` is a vendored copy, byte-identical today (checked with `cmp`), that the build refreshes from the package. A slice edits the package and rebuilds, never the vendored copy by hand. Broker slices edit `packs/credential-brokers/.apm/adapter-root-bins/sso-broker.py` directly; only `_sso.py` is sourced from the package.

**Out of scope, each with an owner.**

- Contention backoff and the audit log in `jira.py`: `sso-store-contention-and-audit-trail`.
- Pack dependency schemas and catalogue defaults: `credential-pack-defaults-projection`.
- Real-keychain timing runs and live-IdP transcripts: named manual follow-ups below.

## Current-state evidence

Read 2026-11-05.

- `_capture` in `sso-broker.py` still takes `persist: bool` and `headless: bool`.
- The broker has no session maximum age, no recapture cooldown and no launch lock. Only the store-transition lock exists, from `sso-store-transition-serialization`.
- `_sso.py` documents that engine stderr stays inherited.

## Constraints / Appetite

- Owner-approved configurable defaults: session maximum age 12 hours, recapture cooldown 15 minutes, launch-lock wait 120 seconds, keychain per-call timeout 5 seconds. Each is a documented setting, not a hard-coded value.
- The lock budget is derived: calls multiplied by the per-call timeout, plus margin. The spec states the formula.
- Non-waivable: the launch lock stays separate from the short store-transition lock so a long browser launch cannot starve `get-cookies`.
- Non-waivable: capture-time filtering supplements consumer-side cookie-send confinement; it never replaces it.
- Landing commits touching `packs/credential-brokers/**` need an `Engine-Change-RFC:` trailer. The gate checks only that the trailer is present. Owner decided 2026-11-05: each commit cites the RFC for its area, with RFC-0035 for credential-broker work, and no umbrella RFC is written. A commit with no governing RFC uses `n/a - <justification>`.
- `packs/credential-brokers` is a pack, so every slice bumps the pack version and updates the pack's eval harness (`packs/AGENTS.md`).

## Assumptions / Risks

- **[Risk]** Fake keychain and fake Chromium doubles hide real behaviour. The manual follow-ups cover that residue and block nothing.
- **[Assumption]** Session maximum age is enforced at read time, so no background process is needed.

## Governance references

- `docs/specs/sso-store-transition-serialization/spec.md` owns the store lock.
- `docs/specs/jira-check-sso-auto-login/spec.md` owns the automatic refresh path.

## Proposed cut

Dependency order: none. The six slices (1a, 1b, 2, 3, 4, 5) are independent and can ship in any order. Gating is `agent-only` unless stated.

| Slice | Gating | Proof |
| --- | --- | --- |
| 1a. Mode enum (`operator-register`, `ephemeral-register`, `automatic-refresh`) | agent-only | Test: the invalid fourth combination is unrepresentable |
| 1b. Refresh stderr bounding | agent-only | A fake child that prints a path to stderr yields a bounded error |
| 2. Keychain batching, per-call timeout and derived lock budget | agent-only | Fake `security` binary with injected latency; the batched path makes fewer calls than the unbatched path; budget assertion |
| 3. Per-profile browser-launch lock with stale recovery | agent-only | Two-process test with a fake singleton lock; `get-cookies` not starved |
| 4. Session maximum age, destination-filtered cookie storage, 0700 and 0600 modes | agent-only | Expired profile refused; filtered fixture; mode assertions |
| 5. Recapture cooldown in broker-written state | agent-only | Repeated automatic refresh inside the window is refused |

## Manual follow-ups (non-blocking)

- Real macOS keychain timing run (twenty consented timings), recorded in `docs/specs/sso-store-transition-serialization/manual-qa.md`.
- Live corporate IdP check of the 12-hour and 15-minute defaults.

## Ready gaps (Draft only)

None open.

## Spec map

| Spec | Status |
| --- | --- |

## Source

- Mode: repo-origin
- Locator: docs/product/intents/sso-browser-state-protection.md
