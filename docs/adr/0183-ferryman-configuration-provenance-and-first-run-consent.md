# ADR-0183: Ferryman configuration is generated and committed by a human, and the first run shows permissions

- **Status:** Proposed
- **Date:** 2026-11-10
- **Areas:** install, security
- **Reversibility:** high
- **Decision-makers:** eugenelim
- **Supersedes:** none
- **Supersedes in part:** none
- **Superseded by:** none
- **Superseded in part:** none
- **Related:** RFC-0115 (the proposal this records); RFC-0112 (pack-defaults projection); ADR-0174 (the trusted configuration pin and allowlists); ADR-0182 (distribution and the version rule)

## Context

Seeds are written once and never upgraded, so a seeded configuration would drift. A worker runs with an `allow` list, a model and a pinned CLI, and the user should see these before the first real run.

## Decision

We will generate `ferryman.toml` once for a human to review and commit, and we will show each role's effective permissions and ask once before the first real run.

- **D1:** `ferryman init` generates `ferryman.toml`, and a human reviews and commits it. No configuration is seeded.
- **D2:** The file carries a `schema_version`, and `doctor` reports drift.
- **D3:** `init` writes no install state and nothing to the tracker.
- **D4:** Before the first real run, `ferryman` shows each role's effective permissions (the `allow` list), model and pinned CLI version, and asks once. `ferryman session` shows the same display.
- **D5:** Consent is stored in `~/.ferryman/consent.json`, keyed on profile, model and CLI version. `ferryman` asks again when one changes.
- **D6:** Hook wiring follows the distribution route's consent rule: it publishes only with consent.
- **D7:** The consent file is a convenience and not a security boundary. A same-user worker could rewrite it. The pin of ADR-0174 only catches a change made while `ferryman` runs, and it is not a defence against that rewrite.

## Consequences

**Positive:**
- A reviewed, committed file replaces a seed that cannot be upgraded.
- The user sees what a worker may do before it runs.

**Negative:**
- The user does one review and one confirmation before the first run.
- A rewritten consent file can skip the prompt, so it is never a defence.

**Revisit if:** the RFC-0112 pack-defaults projection for non-sensitive defaults, a candidate to evaluate first, proves a better source.

## Confirmation

- **Mode:** lint/CI
- **Signal:** a drift test for `schema_version`, a test that `init` writes no install state and no tracker change, a test that the display appears before the first real run and in `ferryman session`, and a test that a change of profile, model or CLI version asks again.
- **Owner:** eugenelim

## Alternatives considered

- **Ship a seed file:** seeds are never upgraded.
- **Show permissions on request only:** the user could run a worker without seeing its permissions.

## References

- `docs/architecture/unattended-delivery-runner/14-installation-and-adoption-experience.md`
- `docs/architecture/unattended-delivery-runner/03b-headless-worker-launch.md`
- `docs/architecture/unattended-delivery-runner/10d-folded-decisions-and-defaults.md` (D52, D54)
- `docs/rfc/0112-pack-defaults-projection-for-stdlib-readers.md`
