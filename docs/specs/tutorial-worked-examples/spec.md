# Spec: tutorial worked examples

- **Status:** Draft
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** none
- **Brief:** docs/product/briefs/sdlc-guide-uplift-and-learning-paths.md
- **Discovery:** none
- **Contract:** none
- **Shape:** mixed

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

Mode: full. The slice updates tutorial content across multiple guide packs and
proves the authored examples survive site generation.

## Objective

A newcomer following any accepted-base tutorial sees a worked exchange rather
than instructions alone: the tutorial shows the concrete values the reader
supplies and the representative response or artifact produced from those same
values. The pair remains part of one walkthrough, so readers can compare their
run with a believable example without mistaking illustrative output for an
exact guarantee.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| User-facing tutorial truth | Applicable | Tutorial paths in [`notes/accepted-base.md`](notes/accepted-base.md) | `author-product-docs`; guide owners | Worked input/output pair in every target | AC1–AC8 hold |
| Accepted scope | Applicable — corpus totals change | [`notes/accepted-base.md`](notes/accepted-base.md) | This spec | Fixed target paths and missing cells | Every ledger member passes |
| Execution evidence | Applicable | `notes/verification-ledger.md` | `work-loop` | Per-target source, audit, review, build, and link results | Closeout verifies AC1–AC13 |
| Release history, architecture, API contracts | Not applicable — guide-only content changes add no released pack version, runtime boundary, or schema | — | — | — | — |

## Boundaries

### Always do

- Use values and outcomes supported by the current skill, journey contract,
  tutorial workflow, or another repository-owned example.
- Keep demonstrated input and its matching output in the same worked run and
  label the output as representative.
- Preserve the tutorial's existing goal, order, and Diataxis kind.

### Ask first

- Reclassifying an accepted-base tutorial as ineligible.
- Changing workflow behavior, prerequisites, or safety boundaries to make an
  example easier to write.
- Changing the audit detector or guide schema.

### Never do

- Invent a capability, external-system result, or exact response guarantee.
- Edit generated docs under `docs-site/src/content/docs/guides/` as source.
- Create the related intents' cross-pack digital-product tutorial or
  role-specific first-value content.
- Freeze a repository-wide tutorial count into a completion check.

## Testing Strategy

- **Goal-based audit checks:** a fresh affordance ledger must show B and C on
  every exact path in the accepted base; path membership, not a corpus count,
  is the exhaustive set.
- **Goal-based structure checks:** each target contains a demonstrated input and
  a representative output that refer to the same scenario or named values.
- **Goal-based integration checks:** site generation and targeted link/build
  gates prove the examples reach published output.
- **Documentation review:** `author-product-docs` checks every pair for
  source-grounding, tutorial continuity, safe placeholder data, and clarity.
  `guides/architect/how-to/diagram-a-system.md` is the quality comparison point;
  detector presence alone is insufficient.

No runtime logic changes, so TDD is not the primary mode. No new screen or
interaction is introduced, so visual QA is not required.

## Acceptance Criteria

- [ ] **AC1 — accepted demonstrated-input gaps close.** Every tutorial row
      marked B in [`notes/accepted-base.md`](notes/accepted-base.md) shows the
      concrete answer, values, or material the reader supplies during the run.
- [ ] **AC2 — accepted sample-output gaps close.** Every tutorial row marked C
      in the accepted base shows a representative agent response or resulting
      artifact excerpt.
- [ ] **AC3 — every accepted tutorial has the pair.** Each accepted-base path
      contains both demonstrated input and sample output after implementation,
      including paths that initially lacked only one member.
- [ ] **AC4 — each pair uses one scenario.** The input and output in each target
      share the same named scenario or identifying example values.
- [ ] **AC5 — each pair shows the causal sequence.** Demonstrated input appears
      before its matching output within the same worked run.
- [ ] **AC6 — pair sources are traceable.** Each input/output pair matches the
      current repository-owned behavior source named for it in the verification
      ledger.
- [ ] **AC7 — variable output is not promised as exact.** Each response whose
      wording or values can vary is explicitly labelled representative.
- [ ] **AC8 — examples use safe placeholders.** No example contains personal
      information, credentials, live account identifiers, or a value presented
      as safe to paste when it is secret.
- [ ] **AC9 — canonical tutorials generate.** `tools/build-site.py` completes
      from the changed `guides/**` sources.
- [ ] **AC10 — the web prerequisite builds.** The web build completes after
      guide generation.
- [ ] **AC11 — the documentation site builds in order.** The documentation-site
      build completes after the web build.
- [ ] **AC12 — accepted tutorials emit no broken internal link.** Every rendered
      internal link from an accepted tutorial resolves.
- [ ] **AC13 — measured tutorial coverage moves forward without regressions.**
      For each of B and C, the post-implementation set of present guide paths
      contains every pre-implementation present path and every accepted-base
      tutorial path.

## Follow-ons

- `docs/product/intents/digital-product-guides-update.md`: future cross-pack
  digital-product tutorial and per-pack intent indexes.
- `docs/product/intents/nontechnical-pack-first-value-rollout.md`: new
  role-specific first-value tutorials, safety, recovery, and evaluation.

## Assumptions

- Technical: the audit records traceable B and C evidence for each guide
  (source: `tools/audit-guide-affordances.py`; probe 2026-09-09).
- Technical: `guides/**` is canonical and `tools/build-site.py` projects it
  into the site (source: `guides/AGENTS.md`).
- Product: close every eligible accepted-base tutorial while preserving the
  related-intent boundaries (source: user confirmation 2026-09-09).
