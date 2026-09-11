# Plan: the four disciplines read as one sequence

- **Spec:** [`spec.md`](spec.md)
- **Status:** Draft

## Discovery predicates

Two items were routed here because only the build can settle them. Each carries
its constraint, its required outcome, and how it is verified.

### D1 — the collection count

**Constraint.** The prior session's sketch reported rendering 19 journeys;
`web/src/content/journeys/` holds 20 `.md` files, all carrying a tagline.
**Required outcome.** The discrepancy is explained before any membership claim
is made, and AC-0005's construction test asserts against the collection's own
count rather than against a literal.
**Verification.** The test reads `getCollection('journeys')` and compares its
length to the rendered card count. A literal `20` in the test is a defect: it
would pass while a journey silently stopped being collected.

### D2 — step-number styling

**Constraint.** The sketch applies `.journeys-grid--ordered`,
`.journey-card--step` and `.journey-card__step` with no rule defined for any of
them, and its `.journeys-grid` rule drops the `list-style: none` the committed
version carries — so both the `<ol>` and the `<ul>`s would render markers.
**Required outcome.** Every class applied has a rule, list markers are
suppressed, and the step number meets the repository's contrast floor in both
themes.
**Verification.** Built-page inspection at two themes, plus the existing
accessibility fixture suite.

## Tasks

| # | Task | Criteria | Notes |
| --- | --- | --- | --- |
| T1 | Reproduce and fix `make bootstrap-sites` exiting 0 without emitting `build/docs/` | — | **Blocks T4's evidence.** Four `web/` vitest cases already fail locally on this. Build order is load-bearing: `web/` cleans repository `build/`. CI is green, so this is local-evidence repair, not a product fix |
| T2 | Regroup `web/src/pages/journeys/index.astro` into three collection-derived groups | AC-0001, AC-0002, AC-0003, AC-0005, AC-0006 | Start from the reconstructed sketch, not from scratch; keep its collection derivation, discard its CSS gaps. Resolve D1 and D2 here |
| T3 | Write the sequence and handoff copy on the index | AC-0004, AC-0010, AC-0015, AC-0016, AC-0018 | Hand-authored page copy only. AC-0017 forbids reaching into generated journey content |
| T4 | Add the construction tests on the `web/` vitest suite | AC-0001 – AC-0006 | `npm run test --prefix web`. AC-0006 needs a fixture journey named in no group; AC-0005 needs the collection count, per D1 |
| T5 | Add the ordered path to `guides/README.md` | AC-0007, AC-0008, AC-0009, AC-0010 | Match the P1–P6 shape. AC-0009's disclosure of the P2 order difference is required, not optional |
| T6 | Run the guide gates and link check | AC-0012, AC-0013, AC-0014, AC-0019 | `validate_guides.py`, `lint-guide-titles.py`, `check-guide-index.py`, `make site-link-check` — each run separately |
| T7 | Whole-diff prohibition reads and the path-scoped diff | AC-0015, AC-0016, AC-0017, AC-0018 | AC-0017 is `git diff -- web/src/content/journeys/`, which must be empty |
| T8 | Cold read | AC-0011 | A reader who has seen only the two surfaces names the order and one handoff |
| T9 | Record the ledger | Durable Output | `notes/verification-ledger.md`: collection count, rendered count, and the D1 explanation |

## Mutation proofs

Two criteria install a guard whose removal must be caught.

| Guard | Test that must catch removal | Mutation | Expected failure |
| --- | --- | --- | --- |
| AC-0005 — no journey dropped | the membership construction test | remove one slug from a group array **and** from the catch-all filter | the test reports a collection journey rendering zero times |
| AC-0006 — ungrouped journeys still render | the catch-all test | replace the collection-derived catch-all with a hardcoded list | the fixture journey named in no group is absent from the rendered page |

A test that still passes under its mutation is not proof. AC-0006's mutation is
the exact defect that previously dropped five journeys, including
`product-strategy`, so the guard is calibrated to a defect that actually
occurred rather than to a hypothetical one.

## Sequencing

T1 first — it gates T4's evidence. T2 and T5 are independent of each other and
can run in either order. T3 depends on T2. T4 depends on T2 and T1. T6–T8 run
after both surfaces exist. T9 last.
