# Spec: Catalogue-seeds lint — opt-in by construction, renamed `lint-catalogue-seeds`

- **Status:** Approved <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** RFC-0047 (Decision 6), ADR-0037 (D4), ADR-0021 (pack-manifest source of truth + contract-version rule), RFC-0002 (the placeholder-only seed contract)
- **Shape:** mixed <!-- tooling + manifest + CI change -->
- **Contract:** none <!-- repo-internal catalogue tooling; the new pack.toml field's manifest-contract impact is an explicit AC, not a published API surface -->

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

The catalogue's seed lint (`tools/lint-seeds.py`) enforces a *placeholder-only* scaffold contract on **every** pack that ships seeds — the anti-leak blocklist *and* the scaffold-shape checks (placeholder-required, fail-loud-on-unknown-seed, empty-`patterns.jsonl`). That is correct for the four first-party scaffold packs, but it is exactly wrong for an **organization pack**, which intentionally ships *instance content* (a filled-in `reference.md`, real conventions) — the inverse of the placeholder contract. An org pack must be unenforced **by construction**, with no edit to the lint and no central pack list to maintain. Success: the lint is renamed `lint-catalogue-seeds`, and **all** its checks are gated on an opt-in `[pack].lint-seeds = true` flag carried **only by the four first-party scaffold packs** (`core`, `governance-extras`, `monorepo-extras`, `user-guide-diataxis`), added in the **same change** so none silently loses enforcement. Any other pack — including any org pack — omits the flag and is unenforced by construction. It stays a **single tool, not split**.

## Boundaries

The three-tier guard that keeps an implementing agent inside the lines.
*Always do* applies without asking; *Ask first* requires human sign-off
before proceeding; *Never do* is a hard rule, even under time pressure.

### Always do

- Add `[pack].lint-seeds = true` to **all four** first-party scaffold packs' `pack.toml` in the **same change** that flips the lint to opt-in — or they silently stop being enforced (the one real migration step).
- Rename in lockstep: the tool (`tools/lint-seeds.py` → `tools/lint-catalogue-seeds.py`), the CI job + path-filter + run line (`.github/workflows/docs.yml`), the `pre-pr-catalogue.py` invocation, and the `tools/hooks/README.md` mention.
- Confirm, against ADR-0021's contract-version rule, **whether the new optional `pack.toml` field needs a manifest contract-version bump** — and record the answer (with reasoning) in the plan and the ADR's "to revisit" note.
- Gate **every** check (blocklist *and* scaffold-shape) on the flag — both serve one contract and key off the same is-first-party-scaffold predicate.

### Ask first

- Any change that would **split** the lint into two tools — Decision 6 is explicitly single-tool; the "for other things" bucket is empty.
- Bumping the manifest contract version (only if the contract-version rule turns out to require it — surface the finding first).

### Never do

- **Maintain a central hardcoded list** of which packs are first-party inside the lint — the flag in each pack's `pack.toml` is the single source; the lint reads the flag, not a list. (An unavoidable bootstrap default is allowed only if `pack.toml` cannot be read; prefer reading the flag.)
- **Enforce an org pack** that omits the flag — unenforced by construction is the whole point.
- Project the new `lint-seeds` flag to `plugin.json` / `marketplace.json` or any adapter output — it is catalogue-internal metadata.

## Testing Strategy

- **Gating behavior (TDD).** The lint enumerates only packs whose `pack.toml` carries `[pack].lint-seeds = true`; a synthetic pack with seeds but no flag is **skipped** (no violation raised on its instance-shaped content), and a flagged pack with a leak/placeholder violation still **fails**. This is the compressible invariant — test it directly.
- **Rename completeness (goal-based check).** `grep` confirms no surviving `lint-seeds.py` path or `lint-seeds` CI/pre-pr reference except the historical changelog; the renamed tool, CI job, path filter, run line, pre-pr line, and README mention all use `lint-catalogue-seeds`.
- **Migration completeness (goal-based check).** All four first-party packs' `pack.toml` carry `[pack].lint-seeds = true`; `grep`/`toml`-read confirms.
- **End-to-end (goal-based check).** `python tools/lint-catalogue-seeds.py` runs green on the current tree, and `pre-pr-catalogue.py` invokes it.

## Acceptance Criteria

- [ ] `tools/lint-seeds.py` is renamed to `tools/lint-catalogue-seeds.py`; the `.github/workflows/docs.yml` job, path-filter, and run line, the `tools/pre-pr-catalogue.py` invocation, and the `tools/hooks/README.md` mention are renamed in lockstep (no surviving `lint-seeds` reference except historical changelog/ADR text).
- [ ] **All** lint checks (anti-leak blocklist, placeholder-required, fail-loud-on-unknown-seed, empty-`patterns.jsonl`) are gated on the pack carrying `[pack].lint-seeds = true`; a pack without the flag is **skipped entirely**.
- [ ] All four first-party scaffold packs (`core`, `governance-extras`, `monorepo-extras`, `user-guide-diataxis`) carry `[pack].lint-seeds = true`, added in the **same change** as the gating flip.
- [ ] A synthetic pack that ships seeds but **omits** the flag raises **no** violation even on instance-shaped content (unenforced by construction) — a regression test asserts this.
- [ ] A flagged pack with a real leak or missing-placeholder violation still **fails** — a regression test asserts the enforcement is intact for first-party packs.
- [ ] The lint reads the flag from each pack's `pack.toml`; it does **not** carry a central hardcoded first-party pack list **as the source of truth**. (A read-failure bootstrap fallback, if one exists per the Boundaries carve-out, is not the source of truth and does not violate this — verification is "the flag drives enforcement", not "no list literal exists anywhere".)
- [ ] The new `[pack].lint-seeds` field is **not** projected to `plugin.json`, `marketplace.json`, or any adapter output (catalogue-internal metadata) — confirmed by build-self leaving those clean.
- [ ] The **manifest contract-version question is resolved**: the plan records, with reasoning against ADR-0021's contract-version rule, whether the new optional field requires a bump — and the implementation matches that answer (default expectation: additive + optional ⇒ no bump).
- [ ] `python tools/lint-catalogue-seeds.py` runs green on the current tree; `pre-pr-catalogue.py` invokes it; `lint-spec-status.py` clean.

## Assumptions

- Technical: today the lint enumerates `packs/*/seeds/` for **all** packs (`_enumerate_seed_files`), with no per-pack gate; only the four named packs ship seeds. (source: verified `tools/lint-seeds.py:149-161` + `ls packs/*/seeds` 2026-06-25)
- Technical: the lint is wired in three non-`make build-check` places — CI (`docs.yml:23,82,88`), `pre-pr-catalogue.py:70`, and referenced in `tools/hooks/README.md:77`. (source: verified 2026-06-25)
- Technical: `pack.toml` is the metadata source of truth, projected lossily per tool (ADR-0021); a catalogue-internal field with no projection mapping does not reach `plugin.json`/`marketplace.json`. (source: ADR-0021; `feedback_nonprojected_pack_bump_drifts_marketplace` memory — version aggregates, an unmapped field does not)
- Process: this lint is a CI/pre-pr gate, **not** part of `make build-check`; the regression tests for the gating behavior need explicit wiring or they never gate. (source: `reference_ci_package_tests_explicit_wiring`, `reference_loop_cohort_state_schema_selftest` memory)
- Process: a user-visible CI-step rename is a `docs/product/changelog.md` `[Unreleased]` entry in the implementing PR. (source: `feedback_changelog_for_skill_changes` memory)
- Product: an org pack omitting the flag and being unenforced by construction is the desired behavior, not a gap. (source: RFC-0047 Decision 6; user direction 2026-06-25)
