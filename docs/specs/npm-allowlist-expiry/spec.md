# Spec: npm audit allowlist entries expire

- **Status:** Draft
- **Owner:** eugenelim
- **Plan:** none — authored after approval
- **Constrained by:** ADR-0083
- **Brief:** brief:scanner-suppression-and-pin-hygiene-delivery
- **Discovery:** intent:scanner-suppression-and-pin-hygiene
- **Contract:** none
- **Shape:** service

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.
>
> **Not every section is contract.** `Agent Rules`, `Testing Strategy` and
> `Acceptance Criteria` are what a completion gate reads, and an amendment
> changes them. `Outcome`, `What Changes`, `Durable Outputs`, `Follow-ons` and
> `Assumptions` are working material: they orient a reader and an author corrects them in place
> as the work teaches, without an amendment and without a review round.

## Outcome

Maintainers who allowlist an unfixable npm advisory must give the entry an end date, and the SAST gate returns the advisory to blocking once that date passes, so a suppression cannot outlive its justification.

## What Changes

- Each `[[allow]]` entry in `tools/npm-audit-allowlist.toml` carries a required `expires` date — the same file, including its three current entries.
- `tools/audit-npm.py` validates `expires`, and treats an entry past its date as not allowlisted — the same file.
- The allowlist's header comment documents the field next to `reason` and `unblocked_when` — the same file.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| Maintainer procedure | Applicable — the allowlist header is where authors learn the entry shape | `tools/npm-audit-allowlist.toml` header | eugenelim | Header lists `expires` with its rule | `close-work` reads the header against the validator |
| Current product truth | Applicable | `docs/product/briefs/scanner-suppression-and-pin-hygiene-delivery.md` Spec map | `lint-brief-coverage` | Roll-up resolves this spec through its `Brief:` link | No status hand-written into the brief |
| Release history, user promise | Not applicable — repository-internal gate | — | — | — | — |

## Agent Rules

### Always do

- Read the current date from one injectable clock, so tests fix the date.
- Treat a missing, blank or malformed `expires` as a tool error (exit 2), like a missing `reason`.
- Print the expired entry's id and its date when it blocks.

### Ask first

- Changing the 90-day horizon default or the blocking behavior of an expired entry.
- Giving any current entry a date later than 90 days after 2026-11-05.

### Never do

- Never let an expired entry stay silently allowlisted.
- Never read the network or the system clock more than once per run.

## Testing Strategy

- **TDD:** `tools/test-audit-npm.py` gains cases for a valid future date, a past date, a missing field, a malformed date and a date beyond the horizon, using the existing report fixtures and an injected clock.
- **Goal-based check:** running `python3 tools/audit-npm.py` on the real tree with the updated allowlist still passes.

## Acceptance Criteria

- [ ] An allowlist entry with no `expires`, a blank `expires`, or a value that is not an ISO 8601 calendar date makes `audit-npm.py` exit 2 and name the entry.
- [ ] An entry whose `expires` date is earlier than the run's UTC date is treated as not allowlisted, so its advisory blocks and the run exits 1, and the output names the entry id and its date.
- [ ] An entry whose `expires` date is on or after the run's UTC date suppresses its advisory as today.
- [ ] An entry whose `expires` date is more than 90 days after the run's UTC date makes `audit-npm.py` exit 2.
- [ ] Each of the three current entries carries an `expires` date no later than 2027-02-03, which is 90 days after 2026-11-05.
- [ ] The allowlist header documents `expires` beside `reason` and `unblocked_when`.

## Follow-ons

- eugenelim: `docs/product/briefs/scanner-suppression-and-pin-hygiene-delivery.md` slices 2 to 4 — the nosec registry flag, the `pack-evals.yml` lockfile install, the hash-locked SAST manifest.

## Assumptions

- Defaulted: Product: the horizon is 90 days and an expired entry blocks — default: as the brief's suggested defaults say; if wrong: the horizon constant and the blocking branch change (settled by: eugenelim).
- Defaulted: Technical: the `.snyk` file's `expires` field is the precedent for date form — default: ISO 8601 calendar date; if wrong: the validator's parse changes (settled by: eugenelim).
