# Plan: Catalogue-seeds lint — opt-in by construction, renamed `lint-catalogue-seeds`

- **Spec:** [`spec.md`](spec.md)
- **Status:** Drafting <!-- Drafting | Executing | Done -->

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document is allowed to change as you learn. When it changes substantially
> (a different approach, not just a re-ordering), note why in the changelog
> at the bottom.

## Approach

Two coupled changes that must land together: (1) gate the lint's enumeration on a per-pack `[pack].lint-seeds = true` flag read from `pack.toml`, and (2) add that flag to all four first-party scaffold packs in the **same** change — decoupling them silently drops enforcement. Then rename the tool and every reference in lockstep (`lint-seeds` → `lint-catalogue-seeds`). The riskiest part is the migration symmetry: the moment the gate flips, any pack without the flag is unenforced, so the four flags must be present in the same diff, asserted by a regression test. The contract-version question (does a new optional `pack.toml` field need an ADR-0021 bump?) is answered up front in this plan — additive + optional + catalogue-internal + unmapped to any projection ⇒ **no bump** — and the implementation must keep the field unmapped so that answer holds. Verification is TDD on the gating invariant (flagged pack enforced, unflagged pack skipped) plus goal-based grep for rename completeness and a clean end-to-end run.

## Constraints

- ADR-0037 D4 / RFC-0047 Decision 6 — single tool, opt-in flag, no central list, unenforced-by-construction for org packs.
- ADR-0021 — `pack.toml` source of truth, projected lossily; the contract-version rule governs whether the new field needs a bump.
- RFC-0002 — the placeholder-only seed contract the lint enforces (unchanged in content; only its *scope* becomes opt-in).
- `feedback_nonprojected_pack_bump_drifts_marketplace` — keep the new field unmapped so it does not drift `marketplace.json`/`plugin.json`.

## Design (LLD)

### Design decisions
- **Read the flag, don't list the packs.** The lint reads `[pack].lint-seeds` from each pack's `pack.toml` during enumeration and skips packs without it — no hardcoded first-party list (spec AC6). Alternative rejected: a central `FIRST_PARTY_PACKS` constant — it would drift and re-introduce the central-list maintenance the flag removes. *Traces to: AC2, AC6.*
- **Gate at enumeration, not per-check.** Gating `_enumerate_seed_files` (or its caller) on the flag is one chokepoint that covers all four checks at once, vs. threading a flag into each check. *Traces to: AC2.*
- **Field stays catalogue-internal, unmapped.** No projection mapping is added for `lint-seeds`, so it never reaches `plugin.json`/`marketplace.json`. *Traces to: AC7.*

### Interfaces & contracts
- `[pack].lint-seeds : bool` (optional, default absent ⇒ unenforced) in `pack.toml`. **Contract-version impact: none** — additive, optional, catalogue-internal, with no projection mapping; ADR-0021's contract version tracks the *projected* manifest shape, which is unchanged. Recorded here per spec AC8; revisit only if a reviewer reads the rule otherwise. *Traces to: AC8.*

## Construction tests

**Integration tests:** the gating behavior is the cross-cutting test — it spans the enumerator and the per-pack `pack.toml` read; wire it where the catalogue tooling tests run (it is **not** in `make build-check`, so it needs explicit CI/test wiring or it never gates — see Risks).
**Manual verification:** none beyond the end-to-end `python tools/lint-catalogue-seeds.py` run.

## Tasks

### T1: Gate enumeration on the `[pack].lint-seeds` flag

**Depends on:** none

**Tests:**
- A synthetic pack dir with a seed file and **no** `[pack].lint-seeds` flag raises **no** violation, even with instance-shaped content / a blocklisted string (spec AC2, AC4).
- A synthetic pack with `[pack].lint-seeds = true` and a missing-placeholder or leak violation still **fails** (spec AC5).
- The flag in `pack.toml` is what drives enforcement — a flagged pack is enforced, an unflagged one is not — and no central pack list is the source of truth (spec AC6; a read-failure bootstrap fallback, if present, is not the source).

**Approach:**
- Read each pack's `pack.toml` `[pack].lint-seeds` during `_enumerate_seed_files` (or its caller); skip packs without the flag set true.
- Red-green-refactor: write the two synthetic-pack tests first.

**Done when:** the two gating tests pass and the flag-read (not list) is in place.

### T2: Add `[pack].lint-seeds = true` to all four first-party packs

**Depends on:** T1

**Tests:**
- `pack.toml` for `core`, `governance-extras`, `monorepo-extras`, `user-guide-diataxis` each carries `[pack].lint-seeds = true` (spec AC3).
- After T1+T2, the current tree's first-party seeds are still enforced (the end-to-end run stays green and would fail on a planted leak).

**Approach:**
- Add the flag under `[pack]` in each of the four `pack.toml` files in this same change.

**Done when:** all four flags present; end-to-end enforcement intact on the real tree.

### T3: Rename the tool and every reference in lockstep

**Depends on:** T1

**Tests:**
- `git mv tools/lint-seeds.py tools/lint-catalogue-seeds.py`; `grep -rn "lint-seeds"` finds no surviving operative reference (CI job/path-filter/run line, pre-pr line, hooks README) — only historical changelog/ADR text may mention the old name (spec AC1).
- The tool's own internal `print` prefixes / error strings referencing the old name are updated.

**Approach:**
- Rename the file; update `.github/workflows/docs.yml` (lines ~23, ~82, ~88), `tools/pre-pr-catalogue.py:70`, `tools/hooks/README.md:77`, and internal strings.

**Done when:** rename complete; `grep` finds no operative `lint-seeds` reference.

### T4: Confirm no projection drift + end-to-end green

**Depends on:** T1-T3

**Tests:**
- `make build-self` (or the relevant projection) leaves `plugin.json`/`marketplace.json` clean — the new field does not project (spec AC7).
- `python tools/lint-catalogue-seeds.py` runs green on the current tree; `pre-pr-catalogue.py` invokes it (spec AC9).
- `lint-spec-status.py` clean.
- The gating regression tests are wired into the CI/test surface that actually runs them (Risks).
- `docs/product/changelog.md` `[Unreleased]` entry for the CI-step rename.

**Approach:**
- Run the projection and confirm no drift; run the lint end-to-end; wire the tests; add the changelog entry.

**Done when:** no projection drift, lint green, tests wired, changelog present.

## Rollout

Repo-internal catalogue tooling + manifest-field change. No runtime infra. **Deployment sequencing matters once**: the gate flip (T1) and the four flags (T2) must ship in the same PR, or first-party enforcement silently drops between them — they are one atomic change. The rename (T3) is cosmetic-but-wide; do it in the same PR so CI never references a missing path. Reversible by reverting; no data migration. **Sibling-spec note:** `adopter-grounding-surface` edits a `core` seed (the `AGENTS.md` block) — it must satisfy whichever lint name is current; if these land in separate PRs, sequence the rename-aware one to rebase onto the other.

## Risks

- **Decoupled migration** drops enforcement silently. Mitigation: T2 in the same change; spec AC3 + the on-real-tree enforcement test.
- **Regression tests never gate** because this lint is outside `make build-check`. Mitigation: T4 explicitly wires the tests into the CI/test surface that runs them (`reference_ci_package_tests_explicit_wiring`).
- **Contract-version misjudgment** — if a reviewer reads ADR-0021 as requiring a bump for any new field. Mitigation: the LLD records the reasoning; surface the finding rather than bumping silently (Boundaries: Ask first).
- **Stray rename reference** breaks CI. Mitigation: T3's `grep` sweep is an explicit gate.

## Changelog

- 2026-06-25: initial plan (RFC-0047 Decision 6 follow-on).
