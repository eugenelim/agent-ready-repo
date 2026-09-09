# Spec: how-to sample-output coverage

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

Mode: full. The slice updates adopter-facing how-to content across the guide
corpus and verifies its generated publication.

## Objective

A reader who copies the request from any accepted-base how-to can also see a
representative response or artifact excerpt before invoking the skill. The
example is grounded in current behavior, labelled as illustrative rather than
exact, and explains which part of the response proves the requested job is
complete. Completion follows a fixed path ledger, so adding unrelated guides
does not move the goalposts.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| User-facing how-to truth | Applicable | How-to paths in [`notes/accepted-base.md`](notes/accepted-base.md) | `author-product-docs`; guide owners | Representative response and result-reading cue in every target | AC1–AC7 hold |
| Accepted scope | Applicable — corpus totals change | [`notes/accepted-base.md`](notes/accepted-base.md) | This spec | Fixed target paths and exclusions | Every ledger member passes |
| Execution evidence | Applicable | `notes/verification-ledger.md` | `work-loop` | Per-target source, audit, review, build, and link results | Closeout verifies AC1–AC13 |
| Release history, architecture, API contracts | Not applicable — guide-only content changes add no released pack version, runtime boundary, or schema | — | — | — | — |

## Boundaries

### Always do

- Derive sample content from the owning skill, journey contract, current guide,
  template, or another repository-owned behavior source.
- Place the representative response after the request it answers and state what
  signal in that response tells the reader the job succeeded.
- Preserve current safety, authority, confirmation, and failure guidance.

### Ask first

- Reclassifying an accepted-base how-to as ineligible.
- Changing behavior or an authority boundary to make a sample response possible.
- Changing the audit detector or guide schema.

### Never do

- Present variable agent prose, external-system data, or generated identifiers
  as an exact response guarantee.
- Include credentials, personal information, or live account identifiers.
- Edit generated docs as source.
- Pull how-tos without a literal request into this slice; their invocation gap
  remains separately owned.
- Deliver any related intent's excluded experience-design, cross-pack tutorial,
  intent-index, or new first-value content.

## Testing Strategy

- **Goal-based audit checks:** a fresh affordance ledger must show C on every
  exact accepted-base path. Exact membership is exhaustive; repository totals
  are supporting movement evidence only.
- **Goal-based structure checks:** every target keeps its literal request,
  follows it with a labelled representative response or artifact excerpt, and
  states the success signal the reader should inspect.
- **Goal-based integration checks:** site generation and targeted build/link
  suites prove the canonical guide additions reach the published site.
- **Documentation review:** `author-product-docs` checks source-grounding,
  response realism, safe placeholders, Diataxis fit, and the distinction between
  representative shape and exact output. Detector presence alone is
  insufficient.

No runtime logic changes, so TDD is not the primary mode. No new screen or
interaction is introduced, so visual QA is not required.

## Acceptance Criteria

- [ ] **AC1 — every accepted output gap closes.** Each path in
      [`notes/accepted-base.md`](notes/accepted-base.md) contains a
      representative agent response or resulting artifact excerpt.
- [ ] **AC2 — request and response stay connected.** In every target, the
      sample output follows the literal request it answers within the same
      procedure, with no intervening second invocation that could own it.
- [ ] **AC3 — each sample has a reading cue.** Every target names the field,
      section, decision, status, or other visible signal that tells the reader
      the requested job succeeded.
- [ ] **AC4 — response sources are traceable.** The verification ledger maps
      every added response to current repository-owned behavior.
- [ ] **AC5 — examples preserve product truth.** Documentation review records
      no invented capability or authority change in any accepted target.
- [ ] **AC6 — variable responses are labelled.** Each sample whose wording or
      values can vary is explicitly labelled representative.
- [ ] **AC7 — examples use safe values.** No sample contains personal
      information, a credential, or a live account identifier.
- [ ] **AC8 — existing invocation affordances do not regress.** Every accepted
      guide remains A-present in the post-implementation audit.
- [ ] **AC9 — canonical how-tos generate.** `tools/build-site.py` completes from
      the changed `guides/**` sources.
- [ ] **AC10 — the web prerequisite builds.** The web build completes after
      guide generation.
- [ ] **AC11 — the documentation site builds in order.** The documentation-site
      build completes after the web build.
- [ ] **AC12 — changed how-tos emit no broken internal link.** Every internal
      link emitted from an accepted-base how-to resolves to a page or fragment
      emitted by the same site build.
- [ ] **AC13 — sample-output coverage moves forward without regressions.** The
      post-implementation set of C-present guide paths contains every
      pre-implementation C-present path and every path in the accepted base.

## Follow-ons

- How-tos that lack a literal invocation remain outside this output-only slice
  and enter later work through the invocation/outcome ledger or work intake.
- `docs/product/intents/experience-design-delivery-packet.md` retains ownership
  of experience-design guide uplift.
- `docs/product/intents/digital-product-guides-update.md` retains ownership of
  the cross-pack digital-product tutorial and per-pack intent indexes.
- `docs/product/intents/nontechnical-pack-first-value-rollout.md` retains
  ownership of net-new first-value, safety, recovery, and evaluation content.

## Assumptions

- Technical: the audit records traceable A, C, and D evidence per guide
  (source: `tools/audit-guide-affordances.py`; probe 2026-09-09).
- Technical: `guides/**` is canonical and `tools/build-site.py` projects it
  into the site (source: `guides/AGENTS.md`).
- Product: close every eligible accepted-base how-to output target while
  preserving the related-intent boundaries (source: user confirmation
  2026-09-09).
