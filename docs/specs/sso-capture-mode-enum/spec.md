# Spec: SSO capture takes one of three named modes

- **Status:** Draft
- **Owner:** eugenelim
- **Plan:** none — authored after approval
- **Constrained by:** RFC-0035
- **Brief:** brief:sso-browser-state-delivery
- **Discovery:** capability:sso-browser-state-protection
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

Credential-broker maintainers read and extend SSO capture through three named modes, and the fourth, meaningless combination of the old two flags cannot be expressed. Operators see no change: `register`, `register --ephemeral` and the automatic refresh behave and exit exactly as before.

## What Changes

- `_capture` in `packs/credential-brokers/.apm/adapter-root-bins/sso-broker.py` takes a mode (`operator-register`, `ephemeral-register`, `automatic-refresh`) in place of the `persist` and `headless` booleans — the same file, its three call sites.
- The AC35 comment on the refused `persist=False, headless=True` row is replaced by the mode definitions — the same file.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| Current architecture | Applicable — the credentials page describes capture behavior | `docs/architecture/credentials.md` | eugenelim | The page names the three modes if it names the two flags today | `close-work` verifies no stale `persist`/`headless` wording remains |
| Release history | Applicable — the pack ships to adopters | the repository changelog and `packs/credential-brokers/pack.toml` version | eugenelim | A patch version bump and a changelog line | The version bump matches `packs/AGENTS.md` |
| Maintainer procedure | Applicable — pack changes update the pack eval harness (`packs/AGENTS.md`) | the credential-brokers pack tests and evals | eugenelim | The updated harness passes | `close-work` verifies the harness ran |
| Current product truth | Applicable | `docs/product/briefs/sso-browser-state-delivery.md` Spec map | `lint-brief-coverage` | Roll-up resolves this spec through its `Brief:` link | No status hand-written into the brief |

## Agent Rules

### Always do

- Keep the exit codes `0`, `3` and `5` and their meanings unchanged for every mode.
- Land the change with an `Engine-Change-RFC: RFC-0035` trailer, per the repository decision that credential-broker commits cite RFC-0035.
- Edit `sso-broker.py` directly; edit `_sso.py` in `packages/credbroker/` only if the change needs it, and rebuild the vendored copy.

### Ask first

- Any change to the `register`, `refresh` or `--ephemeral` command-line surface.
- Any change to what a mode writes to disk. This slice only renames how the mode is selected.

### Never do

- Never expose a fourth mode or let a caller pass the old boolean pair.
- Never change the headed or headless browser launch behavior of any mode.

## Testing Strategy

- **TDD:** a table test over the three modes asserts the observable behavior the three call sites have today (profile written or not, browser headed or headless, exit code per outcome), using the existing fake-browser doubles in the credential-brokers tests.
- **Goal-based check:** a test or a grep confirms no `persist:` or `headless:` parameter remains on `_capture`.

## Acceptance Criteria

- [ ] `_capture` accepts exactly the three modes `operator-register`, `ephemeral-register` and `automatic-refresh`, and rejects any other value.
- [ ] Under `operator-register`, `_capture` captures into the standing `browser-state/<profile>` profile in a headed browser, as `register` does today.
- [ ] Under `ephemeral-register`, `_capture` captures in a throwaway headed context and seeds the standing profile from it, as `register --ephemeral` does today.
- [ ] Under `automatic-refresh`, `_capture` captures in the standing profile in a headless browser and returns `5` when it cannot complete without a human, as `refresh` does today.
- [ ] A headless capture that seeds the standing profile from an ephemeral context cannot be requested.
- [ ] The existing credential-brokers test suite and pack eval harness pass unchanged apart from the call-site rename.

## Follow-ons

- eugenelim: `docs/product/briefs/sso-browser-state-delivery.md` slice 1b — bound refresh stderr; slices 2 to 5 — keychain, launch lock, expiry, cooldown.

## Assumptions

- Defaulted: Technical: the three call sites are the `register` handler (persist unless `--ephemeral`, headed) and the `refresh` handler (persist, headless); a read on 2026-11-05 shows no other caller — default: build on that; if wrong: the extra caller gets its mode in the same change (settled by: the implementer's grep).
- Defaulted: Process: the credential-brokers pack version bumps by a patch because behavior is unchanged — default: patch bump; if wrong: the owner picks the level at approval (settled by: eugenelim).
