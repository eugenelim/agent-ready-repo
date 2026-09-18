# Verification ledger — the design drives the task list

## Corpus measurement (AC-0010, AC-0011; T0 pre-image)

Run 2026-09-18 over every `docs/specs/*/plan.md` in this worktree, applying
the spec's presence and resolution predicates as specified.

| Count | Value |
| --- | --- |
| Spec directories swept | 485 |
| Plans | 435 |
| Plans carrying `## Design (LLD)` | 252 |
| LLD sub-sections with body content | 927 |
| Participating plans (carry `Owned by:` at least once) | 1 |
| Plans predating the field | 434 |
| Failing findings — sub-section naming no task ID | 0 |
| Failing findings — `Owned by:` naming an undefined task ID | 0 |
| Spec directories exiting non-zero | 4, all pre-existing and identical under the base revision of the checker |

Re-measured against the shipped implementation, after the ownership rules were
made reachable for specs that predate the criterion-identifier grammar. The
earlier figure of 23 predating reports was taken while the rules ran only on
the 24 labelled specs; 434 is the count once they reach every plan.

The single participating plan is this spec's own `plan.md`, which carries the
field in every filled sub-section. It produces no failing finding, so the rule
holds on the artifact that specifies it.

Task headings in the same run: 2,520 across the 435 plans. The pre-image
figures the plan's `## Design (LLD)` cites — 2,511 task headings, 921 of them
in the 183 plans with no LLD section — were measured before this spec's own
plan was added, and are labelled there as base-ref counts.

## Disconfirming probe that changed the design (step 5a)

The plan first specified the rule as change-scoped: fire on a sub-section with
body content whose lines changed since the base ref. One probe over real
history falsified it.

| Measurement | Value |
| --- | --- |
| Commits examined (`git log -n 200 -- docs/specs`) | 200 |
| Of those, touching a `plan.md` | 106 |
| Of those, changing a line inside `## Design (LLD)` | 53 (50%) |
| Sub-sections that would be flagged with no scoping at all | 927 |

Because no plan in the corpus carried `Owned by:`, a change-scoped rule would
have produced a failing finding on half of all plan-touching commits. The rule
was rewritten as per-artifact opt-in, which drops the base-ref dependency
entirely and yields the zeros above.

A first version of this probe used `@@` hunk headers as a proxy for section
membership and returned 0%. That was the instrument, not the result: the
corrected probe resolves changed line numbers against the post-image and
locates the `## Design (LLD)` range within it. The 0% is recorded because a
quiet instrument reads as a pass, and this one nearly shipped the design it
was meant to test.

Neither probe is committed.

## Review round 1 — sustained findings and their answers

Two read-only reviewer sessions, disjoint focus sets. Raw reports persisted
under `.context/reviews/ddttl/` (git-ignored).

| # | Finding | Answer |
| --- | --- | --- |
| A1 | Every mechanical check can pass while an individual decision is unowned | `narrow-the-claim` — the Outcome now states declared sub-section ownership |
| A2 | `What Changes` said both rules read changed lines, contradicting the criteria | `repair-the-artifact` — and a sweep found the same stale text in four further places |
| A3 | Seven criteria bundled independent predicates | `repair-the-artifact` — split; the preservation halves became one enumerated criterion |
| A4 | A criterion pinned the `_loop_guards.py` expression instead of behavior | `repair-the-artifact` — the criterion is now a differential digest assertion; the expression moved to the plan |
| A5 | "No other shipped surface" named no exhaustive mechanism | `repair-the-artifact` — the roster surface suite is now named as the mechanism |
| A6 | "Every task that decision reaches" named no closed set | `repair-the-artifact` — reachability is the sub-section's `Owned by:` task IDs |
| A7 | The size limit named no first-failing input or enforcement mechanism | `repair-the-artifact` — a 901-line body now fails, and the rationale was cut |
| B1 | Routing a falsified settled decision to the ledger recreates the path ADR-0099 rejected | `repair-the-artifact` — the two in-flight cases are separated; only declared-ungrounded grounding takes the ledger |
| B2 | The lint's `TASK` matches `T\d+` only, so a suffixed heading is not a defined task | `repair-the-artifact` — widening the pattern became its own criterion |
| B3 | Opt-in cannot see deletion of an owned decision | `accept-as-proportionate` — recorded as a risk and a follow-on; detecting it needs the base-ref dependency this design removed |
| B4 | A task tested a no-input path a base ref cannot produce | `repair-the-artifact` — verified against `check()`: `PLAN_GATED` reaches that tier only when `plan.md` is falsy |
| B5 | Corpus totals outside the ledger were stale | `repair-the-artifact` — labelled as base-ref counts and reconciled here |
| B6 | Five `Done when:` fields restated their `Tests:` | `repair-the-artifact` — each now names an artifact-level state |

B2 and B4 were each verified against the cited source before adoption rather
than taken on the reviewer's reading. A2 and B4 share one cause: an earlier
repair round's string replacements silently failed to match text a previous
replacement had already changed, so both files were rewritten whole instead.

## Review rounds 2-4

| Round | Findings | Severity mix | Outcome |
| --- | --- | --- | --- |
| 1 | 7 + 6 across two disjoint reviewers | 4 Blocker, 9 Concern | all answered |
| 2 | 5 | 3 Blocker, 2 Concern | all answered |
| 3 | 3 | 3 Concern | all answered |
| 4 | 0 | — | `Clean — ready to commit.` |

### Round 2

| # | Finding | Answer |
| --- | --- | --- |
| C1 | `assets/plan.md` tells implementers to correct `Design` in place without amendment, contradicting the amendment route | `repair-the-artifact` — became AC-0023 and task T9 |
| C2 | A present but empty `Owned by:` satisfied both rules | `repair-the-artifact` — AC-0003 became one predicate over "names no valid task ID" |
| C3 | The no-input tier covers a refused plan too, so "absent, and in no other case" was false | `repair-the-artifact` — verified at `lint-contract-item-alignment.py:512-522,572` |
| C4 | The roster suite scans two roots, so exhaustiveness was overstated | `narrow-the-claim` — AC-0016 bounded to those roots |
| C5 | `Touches:` omitted the test files the tasks add assertions to | `repair-the-artifact` |

### Round 3

| # | Finding | Answer |
| --- | --- | --- |
| D1 | A present but empty `plan.md` is a third no-input case | `repair-the-artifact` — AC-0007 now names all three empty-text cases |
| D2 | The roster sweep rejects an isolated row only on named pointer surfaces, not root-wide | `repair-the-artifact` — AC-0016 is the whole-table claim, AC-0024 the row-level one |
| D3 | AC-0023 still permitted the post-approval in-place edit AC-0019 forbids | `repair-the-artifact` — the permission is bounded to before approval |

### What the rounds cost, and where

Round 1's Blockers were substantive: a governance misroute and a false claim
about a parser's grammar. Rounds 2 and 3 were almost entirely the same class —
a criterion claiming slightly more than its check delivers — found three times
in three different places. C3, C4, D1 and D2 are one defect class: a universal
claim written from intent rather than from the mechanism's actual behavior.
Each was settled by reading the mechanism.

C1 is the finding worth keeping. The template already grants an in-place
`Design` correction "without an amendment", while `_loop_guards.py` hashes
`plan.md` whole, so the guard refuses what the template permits. That
contradiction shipped before this spec and is what made the in-flight case
look unrouted.

## Execution observations

### Deviations from a task row's literal method

- **T8 absorbed three obligations the plan did not enumerate.** The scoped
  `packs/AGENTS.md` requires a version bump in both `pack.toml` and
  `.claude-plugin/plugin.json` for any `.apm/**` change, an eval-harness
  update for a non-cosmetic pack change, and `catalogue lint --deep` plus
  `catalogue verify`. None appear in the sealed plan. They are obligations of
  delivering the accepted intent, not new scope, so they were done under T8
  and recorded here rather than by amending the plan. Core pack 2.26.16 →
  2.26.17 (patch: changed content, no new primitive).
- **`make build-self` required `FORCE=1`.** It refuses a dirty tree, and the
  source edits it projects are themselves the dirt. `--force` overrides the
  dirty-tree check only.
- **The eval-harness updates ran as two parallel workers.** They touch
  disjoint files (`new-spec/evals/evals.json`, `work-loop/evals/evals.json`),
  so the one-implementer-at-a-time default was overridden on the owner's
  instruction. No other pair of remaining tasks was independent.

### A cohort advance that outran its engine transition

Firing `wave-passed` and `loop-cohort wave advance` in one command advanced
the cohort pointer 0 → 1 while the engine refused the transition: `wave-passed`
is legal only from `CODE-VERIFICATION`, and the engine was in
`CODE-IMPLEMENTATION`. The skill's GATES snippet omits the `wave-complete`
step that moves between them; the REVIEW section names it.

Effect: the engine recorded three wave cycles for four scheduled waves. It is
not a verification gap — wave 0's gates ran and passed before the advance, and
every task carries a dispatch receipt. There is no un-advance that is not a
forbidden hand-edit of `state.json`, so the pointer was left where it landed
and every later transition was issued one command at a time.

### A corpus count measured against the wrong denominator

A sweep reported 23 predating-plan reports where 254 were expected, which read
as a rule firing on 9% of the plans it should reach. The checker skips a spec
whose criteria do not use the `AC-NNNN` identifier grammar — 24 of 485 spec
directories use it. Of those 24, 23 predate the field and one participates. So
23 is exact and the expectation was wrong, not the rule.

### Worker output corrected before acceptance

- **T6 wrote this spec's criterion identifiers into shipped skill prose.**
  `packs/AGENTS.md` forbids internal-governance citations in pack content, and
  the identifiers would dangle once this spec is archived. The prose now names
  the two routes directly; the test asserts `AC-00` does not appear.
- **T9 dropped two clauses its criterion did not ask it to remove**, including
  the measured claim that working-material prose is over half a plan's lines.
  Both were restored alongside the new pre-approval bound.
- **T1 wrote a concrete value into a template slot.** `Owned by: T1, T2a.`
  would have been copied verbatim into every plan authored from the template.
  It is now a placeholder, and the test asserts the documented form rather
  than a task-ID list.
- **Two workers tripped `ruff` `I001` import ordering**, fixed in place; later
  briefs carried a ruff check.

## Post-gates review

Two lanes, disjoint focus, read-only: spec conformance and test quality.

| Round | Findings | Severity | Outcome |
| --- | --- | --- | --- |
| 1 | 6 | 2 Blocker, 3 Concern, 1 Nit | all answered |
| 2 | 3 | 3 Concern | all answered |
| 3 | 2 | 2 Concern | all answered |
| 4 | 0 | — | both lanes `Clean — ready to commit.` |

### What the rounds found

- **The ownership rules were unreachable for most of the corpus.** `check()`
  returned before them whenever the sibling spec used no `AC-NNNN`
  identifiers — 461 of 485 spec directories. The first corpus sweep reported
  zero failing findings and was partly vacuous for exactly that reason. The
  block moved into `design_ownership_findings()`, called on both paths; a
  differential run against the base revision of the checker shows no new
  non-zero exit in any of the 485 directories.
- **The nine `Traces to:` lines were not byte-identical**, and the test that
  should have caught it counted occurrences instead of comparing them. The
  template's design section was rebuilt from the base revision with the field
  and the five prompts in their own adjacent comments, so no original line
  moves; the test now compares the ordered tuple.
- **A regression test carried a name it had not earned.** The lettered-task
  case sat after `T1`, and `^### T\d+\b` does not match `### T2a`, so the
  unrecognised heading was absorbed into T1's body and its criteria still
  looked covered. It passed with or without suffix support. Isolating the
  task fixed it; reverting the checker's pattern now reds 2 of 3 selected
  tests.
- **Two repairs shipped without a test of their own** — the scoped no-input
  list and the paired comment delimiters — and both are now pinned by
  equality assertions rather than subset checks.

Rounds 2 and 3 were the same class as rounds 2 and 3 of the spec review: a
control asserting slightly less than its name claims. Three of the five were
found by asking what would still pass if the behavior were reverted.
