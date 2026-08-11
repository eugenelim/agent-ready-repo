# Plan: Adopter-usable seed links

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done <!-- Drafting | Approved | Executing | Done -->

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document is allowed to change as you learn.

## Approach

Pin the adopter-visible failure at the existing first-install snapshot
boundary, then remove catalogue-only links from the canonical core seed. Move
the hook README pointer into the local maintainer context, regenerate the
self-hosted projection, and complete the pack's patch-release bookkeeping.

## Constraints

- `packs/core/seeds/docs/CONVENTIONS.md` remains the source of truth.
- The regression validates scaffolded output and does not treat the self-host
  repository's extra governance files as adopter payload.
- The existing single-line content-lint sentinel retains its documented uses;
  target resolution is a separate invariant.

## Construction tests

**Integration tests:** the core first-install snapshot test exercises the real
seed scaffold and checks governance-link target closure.

**Manual verification:** confirm the cleaned broker paragraph and local-only
hook guidance preserve their respective instructions.

## Design (LLD)

### Dependencies & integration

The existing snapshot test owns the scaffold boundary. A small link-target
check resolves every repository-relative link in the installed conventions
document and reports missing targets; no production module or public linter
surface changes. Traces to AC3.

### Interfaces & contracts

The shipped Markdown seed is the published interface. The self-host projection
and pack release metadata move in lockstep with it. Traces to AC1, AC2, AC4,
and AC5.

### Failure, edge cases & resilience

External URLs and same-document anchors are not findings. Other seed documents
retain their existing optional-link contract; this fix pins the published
conventions document named by the issue. Traces to AC3.

## Tasks

### T1: Missing scaffolded governance-link targets fail the install snapshot

**Depends on:** none

**Touches:** tests/roster/test_install_snapshot.py

**Tests:**
- `stub: false` — materialized before EXECUTE and replaced after the red
  `NotImplementedError` state was confirmed.
- TDD: `test_core_conventions_relative_links_resolve_after_scaffold` fails on
  the current core seed because its catalogue governance and hook-guide targets
  are absent from scaffolded output (AC3).
- The same scaffold-output regression rejects the exact catalogue-only
  `ADR-0003` and `RFC-0013` citations even when they are not links (AC1).
- Existing external and fragment-bearing links demonstrate that the check is
  target closure rather than a blanket identifier ban (AC3).

**Approach:**
- Parse repository-relative Markdown link targets in the scaffolded core
  conventions document.
- Report every target that does not exist relative to that installed file.

**Done when:** the focused test is red for the current seed for the intended
missing-target reason.

### T2: Core ships only adopter-usable conventions references

**Depends on:** T1

**Touches:** packs/core/seeds/docs/CONVENTIONS.md, docs/CONVENTIONS.md, AGENTS.local.md, packs/core/pack.toml, packs/core/.claude-plugin/plugin.json, .claude-plugin/marketplace.json, docs/product/changelog.md

**Tests:**
- Goal-based: the T1 regression passes after the seed edit (AC1-AC3).
- Goal-based: the seed and self-host projection are byte-identical (AC4).
- Goal-based: catalogue lint and build drift checks accept the manifests and
  regenerated marketplace (AC5).
- Goal-based: `docs/product/changelog.md` contains the matching core patch
  version entry and describes the adopter-visible correction (AC5).
- Manual QA: the broker list remains complete and `AGENTS.local.md` owns the
  maintainer-only hook README pointer (AC1, AC2).

**Approach:**
- Replace the ADR/RFC provenance sentence with a self-contained instruction.
- Remove both hook README links from shipped conventions prose and add one
  concise repo-local pointer under the local maintainer instructions.
- Patch-bump core, regenerate self-hosted output, and update the changelog.

**Done when:** AC1-AC5 are satisfied and all available gates are green.

## Rollout

The correction ships in the next core patch release. Rollback is a normal
content revert; there is no infrastructure, migration, or external sequencing.

## Risks

- A token-only ban could reject legitimate illustrative ADR examples; the test
  therefore checks unresolved link targets instead.
- Editing the projection independently would drift from the seed; regeneration
  and byte comparison guard the source relationship.

## Changelog

- 2026-08-11: initial plan.
- 2026-08-11: implementation completed; broadened the scaffold regression to
  all core conventions relative links and the two exact governance citations
  after adversarial review.
