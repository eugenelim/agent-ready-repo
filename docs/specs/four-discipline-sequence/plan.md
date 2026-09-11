# Plan: the four disciplines read as one sequence

- **Spec:** [`spec.md`](spec.md)
- **Status:** Draft

## Discovery predicates

Two obligations were routed here because only the build can settle them. Each
carries its constraint, its required outcome, and its verification mode.

### D1 — the collection count

**Constraint.** The prior session's uncommitted sketch reported rendering 19
journeys; `web/src/content/journeys/` holds 20 `.md` files, all carrying a
tagline. The discrepancy is unexplained.
**Required outcome.** It is explained before any membership claim is made, and
AC-0005's construction test asserts against the collection's own contents rather
than against a literal.
**Verification.** The test reads `getCollection('journeys')` and compares the
multiset of its slugs to the multiset of rendered card slugs. A literal `20` in
the test is a defect: it would pass while a journey silently stopped being
collected.

### D2 — step-number styling and the dropped list rule

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
| T1 | **Diagnose and report** why `make bootstrap-sites` exits 0 without emitting `build/docs/` | — (verification enabler) | Four `web/` vitest cases already fail locally on this, and every built-HTML criterion observes through that build. **Diagnosis only.** Any repair is a separate decision with its own scope: CI is green, so this is not a product defect, and "fix it" here would authorize an unscoped mutation. Build order is load-bearing — `web/` cleans repository `build/` |
| T2 | Regroup `web/src/pages/journeys/index.astro` into three collection-derived groups | AC-0001, AC-0002, AC-0003, AC-0005, AC-0006 | Start from the reconstructed sketch; keep its collection derivation, discard its CSS gaps. Resolve D1 and D2 here |
| T3 | Write the sequence and handoff copy on the index | AC-0004, AC-0007, AC-0016, AC-0017, AC-0019 | Hand-authored page copy only. AC-0018 forbids reaching into generated journey content |
| T4 | Add the construction tests on the `web/` vitest suite | AC-0001 – AC-0006, AC-0021 | `npm run test --prefix web`. AC-0005 compares slug multisets per D1; AC-0006 needs a fixture journey named in no group |
| T5 | Add the ordered path to `guides/README.md` | AC-0008, AC-0009, AC-0010, AC-0011, AC-0022 | Match the P1–P6 shape. AC-0010's disclosure of the P2 order difference is required, not optional. Add a path within the existing hub structure; do not restructure the navigation model |
| T6 | Run the guide gates and the link check | AC-0013, AC-0014, AC-0015, AC-0020 | `validate_guides.py`, `lint-guide-titles.py`, `check-guide-index.py`, `make site-link-check` — each run separately, even after one fails |
| T7 | Whole-diff prohibition reads and the path-scoped diff | AC-0016, AC-0017, AC-0018, AC-0019 | AC-0018 is `git diff -- web/src/content/journeys/`, which must be empty |
| T8 | Cold read | AC-0012 | A reader who has seen only the two surfaces names the order and one handoff |
| T9 | Record the verification ledger | Durable Output — "Reusable learning" | `notes/verification-ledger.md`: the collection multiset, the rendered multiset, and the D1 explanation. A Durable Output is an admissible task target under the authoring contract; this task deliberately traces to one rather than to a criterion |

## Task tests

`docs/CONVENTIONS.md` places construction tests in `plan.md`, attached to each
task's `Tests:` subsection, before Approach. Only T2, T4 and T5 carry
construction tests; T1 and T6–T9 are execution and recording tasks whose
evidence is the command output named in their row.

### T2 — Tests

1. `sequence group renders the four in the decided order` — assert the text
   content of the sequence group's card headings equals
   `['Product Strategy','Desk Research','Experience Design','Product Engineering']`
   in that order. Red before T2: the page has no sequence group. (AC-0001,
   AC-0002)
2. `sequence group is an ordered list` — assert the sequence group's list
   element is `ol`, and that the assertion is scoped to that group rather than
   to any list on the page. Red before T2: the only list is a `ul`. (AC-0003)

### T4 — Tests

3. `every collection journey renders exactly once` — build the multiset of
   slugs from `getCollection('journeys')` and the multiset of slugs from the
   rendered cards; assert deep equality of the two multisets. **Not** their
   lengths: see the AC-0005 mutation below, which is count-preserving. (AC-0005)
4. `a journey in no group still renders` — inject a fixture journey whose slug
   appears in no production group and in no hardcoded fallback; assert it
   renders in the catch-all group. (AC-0006)
5. `each discipline card links to its journey` — assert each of the four cards
   has an `href` resolving to `/journeys/<slug>/` for its own slug. (AC-0021)
6. `step position is exposed to assistive technology` — assert each card
   heading's accessible name begins with its step number, and that the visible
   number carries `aria-hidden`. Red before T3: the number is decorative only.
   (AC-0004)

### T5 — Tests

7. `the path names the four in the decided order and links each to its guide` —
   a content check over `guides/README.md` asserting the four appear in order
   within the new path and each carries a link to its guide directory.
   (AC-0008, AC-0022)

## Mutation proofs

Three criteria install a guard whose removal must be caught.

| Guard | Test that must catch removal | Mutation | Expected failure |
| --- | --- | --- | --- |
| AC-0005 — no journey dropped or duplicated | the membership construction test | **exclude** one slug from the rendered output entirely — filter it out of the catch-all as well as its group, so it does not fall through — **and** duplicate a different slug into two groups | the multiset comparison reports one slug missing and one slug present twice. A length-only comparison passes, because the omission and the duplication cancel: 20 slugs in, 20 cards out. That cancellation is the whole reason the criterion is specified on multisets rather than counts |
| AC-0006 — ungrouped journeys still render | the catch-all test, whose fixture injects a **novel** slug that appears in no production group and in no hardcoded fallback | replace the collection-derived catch-all with a hardcoded list of the production slugs | the novel fixture slug is absent from the rendered page. The novelty is load-bearing: a fixture reusing an existing slug would be present in the hardcoded list and the mutated code would pass |
| AC-0003 — order lives in the markup | the markup assertion | change the `<ol>` to a `<ul>` while leaving the visual order intact | the assertion on the ordered-list element fails even though the page looks unchanged |

A test that still passes under its mutation is not proof. AC-0006's mutation is
the exact defect that previously dropped five journeys, including
`product-strategy`, so that guard is calibrated to a defect that actually
occurred. AC-0005's mutation is deliberately count-preserving, because the
obvious implementation — comparing lengths — survives the naive mutation and
would be a control that cannot fail.

## Sequencing

T1 first; it gates T4's local evidence. T2 and T5 are independent of each other.
T3 depends on T2. T4 depends on T2 and T1. T6–T8 run after both surfaces exist.
T9 last.
