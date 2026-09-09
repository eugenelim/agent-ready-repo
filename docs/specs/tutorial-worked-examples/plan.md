# Plan: tutorial worked examples

- **Spec:** [`spec.md`](spec.md)
- **Status:** Drafting
- **Repository anchors:** `tools/audit-guide-affordances.py`;
  `docs/specs/new-guide-conversation-first/spec.md`; `guides/AGENTS.md`;
  `docs-site/AGENTS.md`; `guides/architect/how-to/diagram-a-system.md`

> **Plan contract:** this is the implementation strategy. It may change
> substantively only while its Status is `Drafting`, before approval records its
> baseline. After approval, execution observations belong in
> `notes/verification-ledger.md`.

## Approach

Work the fixed tutorial ledger pack by pack. Reuse the tutorial's existing
scenario wherever it is concrete; otherwise select values from the owning
skill, journey, or current repository examples. Add only the missing half when
the existing half is already adequate, then ensure both halves read as one
worked exchange. Audit exact targets, review every example, and generate the
published site before closeout.

## Constraints

- The Shipped conversation-first spec is the quality reference and
  `author-product-docs` owns tutorial review; the prior spec's delivery boundary
  does not constrain this existing-guide uplift.
- `guides/**` is source; generated guide pages are outputs.
- The accepted-base ledger is closed and related-intent work is excluded.
- A 2026-09-09 pre-review path probe resolved every path in the accepted-base
  ledger and found no overlap with the how-to output ledger.

## Construction tests

**Integration tests:** before/after affordance ledgers, site generation, and the
targeted guide/link/build suites selected by the touched guide packs.

**Manual verification:** per-target review that supplied values and returned
content match, remain representative, and use safe placeholders. Record the
behavior source and verdict in `notes/verification-ledger.md`.

## Durable-output map

| Durable output | Tasks | Implementation evidence | Closeout evidence |
| --- | --- | --- | --- |
| Worked tutorial pairs | T1–T3 | Guide diffs, audit rows, documentation review | AC1–AC8 receipts |
| Accepted scope and execution evidence | T4 | Before/after exact-path comparison and gate results | AC9–AC13 and close-work verification |

## Design (LLD)

### Design decisions

- A worked pair has a stable three-part shape: supplied material, a
  representative response/artifact, and a short reading of what the output
  means next. This prevents a code block from satisfying the detector without
  teaching the workflow. Traces to AC1–AC5.
- Existing adequate halves are preserved and paired rather than rewritten.
  Traces to AC2–AC4.

### Failure, edge cases & resilience

- External integrations may return variable data; examples use generic
  placeholders and explicitly representative output.
- If the current repository does not support a claimed response, the target
  pauses for owner input rather than fabricating one.
- Concurrent edits are merged per file; no bulk rewrite may overwrite S1 work.

## Tasks

### T1: Architecture, tracker, and catalogue tutorials show complete worked pairs

**Depends on:** none

**Mode:** goal-based check plus manual documentation review

**Touches:** `guides/architect/tutorials/**`, `guides/atlassian/review-your-team-backlog.md`, `guides/catalogue-curation/tutorials/**`

**Tests:** exact target B/C audit; pair-coherence and source review.

**Approach:** add only the ledger-recorded gaps and preserve existing examples.

**Done when:** every accepted target in these paths has a reviewed B/C pair.

### T2: Core, research, and design-delivery tutorials show complete worked pairs

**Depends on:** none

**Mode:** goal-based check plus manual documentation review

**Touches:** `guides/core/tutorials/**`, `guides/desk-research/tutorials/**`, `guides/figma/tutorials/**`, `guides/frontend-engineering/tutorials/**`

**Tests:** exact target B/C audit; pair-coherence and source review.

**Approach:** use current workflow examples and generic placeholder data.

**Done when:** every accepted target in these paths has a reviewed B/C pair.

### T3: Governance, product, and release tutorials show complete worked pairs

**Depends on:** none

**Mode:** goal-based check plus manual documentation review

**Touches:** `guides/governance-extras/tutorials/**`, `guides/product-documentation/getting-started.md`, `guides/product-engineering/tutorials/**`, `guides/product-strategy/tutorials/**`, `guides/release-engineering/tutorials/**`

**Tests:** exact target B/C audit; pair-coherence and source review.

**Approach:** use current workflow examples and label outputs representative.

**Done when:** every accepted target in these paths has a reviewed B/C pair.

### T4: Generated tutorials preserve every accepted worked pair

**Depends on:** T1–T3

**Mode:** goal-based integration check

**Touches:** `docs-site/src/content/docs/guides/**`, `docs/specs/tutorial-worked-examples/notes/verification-ledger.md`

**Tests:** run `python3 tools/build-site.py`, then `npm run build --prefix web`,
then `npm run build --prefix docs-site`, then `make site-link-check`; run the
post-generation exact-path audit and B/C path-set containment comparison. Record
each command and result in `notes/verification-ledger.md`.

**Approach:** generate through repository tooling and record all receipts.

**Done when:** AC1–AC13 are evidenced in the verification ledger.

## Rollout

One guide-content release with no flag, infrastructure, service dependency, or
migration. Reverting canonical guide changes restores the prior state.

## Risks

- Mechanical examples can pass regexes while teaching nothing; every pair gets
  a source and documentation review.
- Large cross-pack guide diffs invite conflicts; T1–T3 own disjoint paths and
  generated output runs only after all three land.

## Changelog

- 2026-09-09: initial plan with the fixed tutorial accepted-base ledger.
