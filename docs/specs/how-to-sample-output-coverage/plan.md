# Plan: how-to sample-output coverage

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

Work the fixed accepted-base ledger in disjoint pack groups. Preserve each existing
literal request, add a representative response or artifact excerpt grounded in
the owning workflow, and give the reader one visible success signal to inspect.
Audit exact paths before and after, review every example, then generate and test
the published site.

## Constraints

- The Shipped conversation-first spec is the quality reference and
  `author-product-docs` owns how-to review; the prior spec's delivery boundary
  does not constrain this existing-guide uplift.
- `guides/**` is source; generated guide pages are outputs.
- This is an output-only slice: guides without A are excluded.
- The accepted-base ledger and related-intent exclusions are fixed.
- A 2026-09-09 pre-review path probe resolved every path in the accepted-base
  ledger and found no overlap with the tutorial ledger.

## Construction tests

**Integration tests:** before/after affordance ledgers, site generation, and the
targeted guide/link/build suites selected by touched packs.

**Manual verification:** per-target source mapping and review of realism,
request/response adjacency, success cue, variability label, and safe
placeholders. Record evidence in `notes/verification-ledger.md`.

## Durable-output map

| Durable output | Tasks | Implementation evidence | Closeout evidence |
| --- | --- | --- | --- |
| Representative how-to responses | T1–T4 | Guide diffs, audit rows, documentation review | AC1–AC8 receipts |
| Accepted scope and execution evidence | T5 | Before/after exact-path comparison and gate results | AC9–AC13 and close-work verification |

## Design (LLD)

### Design decisions

- Each addition uses a three-part shape: `Representative response`, a fenced or
  structured response/artifact excerpt, then `Check` naming the success signal.
  Equivalent house-style headings are allowed when a guide already owns them.
  Traces to AC1–AC5.
- An existing request is the join key. No sample is added where the audit did
  not already find A, avoiding overlap with the invocation slice. Traces to
  AC2 and AC6.

### Failure, edge cases & resilience

- For nondeterministic or external-system responses, use generic placeholders
  and describe stable shape rather than exact values.
- If no current source supports a sample, stop on that row and ask instead of
  fabricating behavior.
- Generated output runs after canonical guide tasks to reduce concurrent-change
  collisions.

## Tasks

### T1: Shared, architecture, tracker, and contract how-tos show responses

**Depends on:** none

**Mode:** goal-based check plus manual documentation review

**Touches:** `guides/_shared/how-to/**`, `guides/architect/how-to/**`, `guides/atlassian/**`, `guides/contracts/how-to/**`

**Tests:** exact-path C audit; request/response, source, success-cue, and safety
review.

**Approach:** add only the sample and cue required by the accepted ledger.

**Done when:** every accepted target in these paths satisfies AC1–AC7.

### T2: Core how-tos show responses

**Depends on:** none

**Mode:** goal-based check plus manual documentation review

**Touches:** `guides/core/how-to/**`

**Tests:** exact-path C audit; request/response, source, success-cue, and safety
review.

**Approach:** group related lifecycle examples but review every file separately.

**Done when:** every accepted core target satisfies AC1–AC7.

### T3: Research, tracker-adapter, and monorepo how-tos show responses

**Depends on:** none

**Mode:** goal-based check plus manual documentation review

**Touches:** `guides/desk-research/how-to/**`, `guides/github/how-to/**`, `guides/governance-extras/how-to/**`, `guides/linear/how-to/**`, `guides/monorepo-extras/how-to/**`

**Tests:** exact-path C audit; request/response, source, success-cue, and safety
review.

**Approach:** keep external identifiers generic and outputs representative.

**Done when:** every accepted target in these paths satisfies AC1–AC7.

### T4: Product and release how-tos show responses

**Depends on:** none

**Mode:** goal-based check plus manual documentation review

**Touches:** `guides/product-engineering/how-to/**`, `guides/product-strategy/how-to/**`, `guides/release-engineering/how-to/**`

**Tests:** exact-path C audit; request/response, source, success-cue, and safety
review.

**Approach:** use existing artifacts and decision outputs as the response source.

**Done when:** every accepted target in these paths satisfies AC1–AC7.

### T5: Generated how-tos preserve every accepted response

**Depends on:** T1-T4

**Mode:** goal-based integration check

**Touches:** `docs-site/src/content/docs/guides/**`, `docs/specs/how-to-sample-output-coverage/notes/verification-ledger.md`

**Tests:** run `python3 tools/build-site.py`, then `npm run build --prefix web`,
then `npm run build --prefix docs-site`, then `make site-link-check`; run the
post-generation exact-path audit, A non-regression check, and C-present path-set
containment comparison. Record each command and result in the verification
ledger.

**Approach:** generate through repository tooling and record all receipts.

**Done when:** AC1–AC13 are evidenced in the verification ledger.

## Rollout

One guide-content release with no flag, infrastructure, service dependency, or
migration. Reverting canonical guide changes restores the prior state.

## Risks

- A catalogue-wide example pass can drift into generic boilerplate; per-file source mapping and
  success cues keep each response specific.
- External-system examples can leak realistic identifiers; generic placeholders
  and safety review are mandatory.
- Cross-pack edits invite merge conflicts; T1–T4 are path-disjoint and generated
  output is serialized after them.

## Changelog

- 2026-09-09: initial plan with the fixed how-to accepted-base ledger.
