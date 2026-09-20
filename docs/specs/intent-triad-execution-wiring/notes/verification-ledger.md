# Verification ledger: intent-triad-execution-wiring

Execution observations for run `9129ff2a-b134-4542-91db-210e993c1b3f`. The
approved `spec.md` and `plan.md` hold obligations; this file holds what
execution observed.

## T1-T3, T5 — the new pack test reds before the edits and greens after

`packs/product-engineering/tests/pack/test_intent_triad_execution_wiring.py`
was run against a scratch pack tree built from `git show HEAD:<path>` for the
six edited artifacts. All 12 tests failed there and all 12 pass against the
working tree, so every control can fail for the direction its name asserts.

Five further mutations were applied to the *edited* content to prove the
scope-dependent controls bite, since an absence that reds only because its
section is missing proves nothing about the absence itself:

| Mutation | Control | Result |
| --- | --- | --- |
| `identify-opportunities` injected into `## Pick a route` | `test_the_menu_names_no_six_step_skill_but_frame_situation` | red |
| `work-intake` left in the section but removed from the `portable rendered` sentence | `test_the_skill_fallback_sentence_names_work_intake` | red |
| `work-intake` removed from the `If Core is absent` sentence only | `test_the_decompose_skill_core_absent_sentence_names_work_intake` | red |
| `decompose-intent` present in the walk but unpaired from G3 | `test_the_gate_ladder_walk_pairs_each_triad_skill_with_its_gate` | red |
| `## Pick a route` moved below `## Procedure` | `test_frame_intent_carries_the_pick_a_route_section` | red |

## T3 — the AC7 reflow broke a literal the roster test reads unnormalised

The first AC7 edit wrapped the fallback sentence so that `Core absence` fell
across a line break. `tests/roster/test_shaping_handoff_pack_surface.py:101`
asserts that literal against the raw file, not a whitespace-normalised copy, so
it failed. The paragraph was re-wrapped to keep `Core absence` and
`portable rendered handoff` each contiguous on one line. Both suites pass.

## T6 — `the-discovery-loop.md` was NOT a no-op, contrary to the plan

The plan's T6 Approach recorded `guides/product-engineering/explanation/the-discovery-loop.md`
as a **verified no-op**, on a read taken before T3's edit existed. That read no
longer holds. The guide's "Where it sits" paragraph said an *explicitly
compatible* Core invocation admits the handoff through `work-intake`, and that
Core absence merely renders portable content. T3 rescoped exactly that
restriction in the skill so the capability bounds the **object**, not the
**target**: both branches now submit through `work-intake`.

Left alone, the guide would have stated the conditional route the shipped skill
contradicts — the drift this delivery exists to remove, and the condition the
spec's own Durable Outputs row forbids ("neither states a gate walk the shipped
agent contradicts"). The paragraph was therefore edited to make the
`work-intake` route unconditional and the capability bound the object.

This is a deviation from T6's literal method. It changes no acceptance
criterion: no AC covers this file, AC15 covers `run-a-discovery.md` only, and
the design decision it follows from (T3's rescoping) was approved and is
unchanged. It is recorded here rather than taken as a plan amendment for that
reason, and is flagged in the PR's "what did you not change that you
considered" answer.

## T6 — both eval harnesses needed a real update, not a no-op record

The plan allowed either updating each edited skill's `evals/` harness or
recording why no change was needed. Both needed a change:

- `discovery-loop/evals/evals.json`, case `g3-portable-rendered-fallback`, is
  the eval that describes the Core-absent branch T3 changed. Its
  `expected_output` now names the `work-intake` submission and it carries a new
  assertion for it.
- `decompose-intent/evals/evals.json`, case `capability-negotiated-handoff`,
  describes the same branch for the leaf projection, and was updated the same
  way.
- `discovery-loop/evals/eval_queries.json` gained one negative case,
  "Shape this product outcome into an intent before we spec it". AC6 removed
  `frame-intent` from the frontmatter exclusion clause, which weakens the
  trigger signal that routes a standalone intent-shaping prompt away from
  `discovery-loop`. No existing negative case covered that route, so the
  weakened exclusion would otherwise have gone unmeasured.

The three phrases `tests/roster/test_shaping_handoff_pack_surface.py` reads out
of the producer evals — `Core is absent`, `capability is unknown`, `predates` —
were re-checked after the edit and are intact.

## Preserved unmodified

`tests/roster/test_shaping_handoff_pack_surface.py`,
`packs/product-engineering/tests/pack/test_frame_intent_shaping_review.py`, and
`packs/product-engineering/tests/pack/test_de_risk_intent_reviewer_boundary.py`
were not edited and pass. `packs/product-engineering/pack.toml`'s
`fallback` integration string is byte-pinned by the first of those and carries
the pre-existing conditional wording; changing it is an "Ask first" item under
the spec's Agent Rules and was not in scope here.

## Review round 1 — sustained findings and their repairs

Three reviewers ran against commit `343a32ea5`; each raw report and its paired
adjudication sits under `.context/reviews/9129ff2a-b134-4542-91db-210e993c1b3f/`.
Every blocker the reviewers raised was refuted on repository evidence; the
sustained findings were advisory or concern-tier and are repaired below.

### The two mutations that defeated the original controls

Both reviewers found real ways to make a control pass while its criterion was
unsatisfied, which the first mutation pass had not reached:

1. **AC7's sentence boundary was movable.** `_sentence_containing` split only on
   `". "`. Re-punctuating the preceding sentence with a semicolon merged the
   Core-absent clause into the negotiated one — which names `work-intake`
   already — so the assertion passed on the wrong span. The helper is now
   `_clause_containing`, splitting on `[.;]`, and the G3 checks additionally
   assert the resolved clause does **not** contain the negotiated branch's
   `advertises` marker. That is the differential half: a span that reaches the
   negotiated sentence can no longer satisfy a Core-absent criterion.
2. **AC3's positional half was unguarded.** The criterion requires the floor
   rule *beneath* the section's existing opening sentence; the test asserted
   only the floor rule's own words, so deleting the anchor left every test
   green. The test now asserts the anchor is present and precedes the floor
   rule. The Testing Strategy's reason for not asserting the anchor does not
   apply to an ordering assertion, which cannot be satisfied before the edit.

Both defeating mutations were re-run against the repaired file and both now red.

### Other sustained repairs

| Finding | Repair |
| --- | --- |
| `_section` terminated only at its own heading level, so a `###` slice ran to end of file | terminates at the same level or shallower |
| the slot-shape assertions widened across a JSON block and the field table | bounded to the list item by `_list_item_containing` |
| `walk.count("decompose-intent") == 2` pinned a transcription count | dropped; the two gate pairings already carry AC5 |
| the route menu was matched by bullet position, which AC11 does not state | each route matched to whichever bullet names it |
| `len(description) <= 1024` borrowed a bound this spec does not own | dropped; `catalogue lint --deep` owns it |
| a missing `type` row raised `StopIteration` | now an assertion naming the file and the row |
| the changelog said "two guide passages … were corrected" | only one was a correction; the other gained a route it never stated |
| the release fold-forward left `product-engineering 0.13.13` cited but unreachable | repointed to `0.13.14`; a tree-wide search now returns no `0.13.13` |

Thirteen defeating mutations were run against the repaired test file and all
thirteen red. One legitimate change — rotating the three route bullets, which
AC11 permits — was confirmed to stay green, so the repair did not trade a
false negative for a false positive.

### Refuted blockers worth the owner's attention

All three adversarial blockers and the security reviewer's blocker were refuted,
two of them by independent adjudications reaching the same verdict. Two residues
were recorded by the adjudicators for the owner rather than as findings, and
neither is a defect in this delivery:

- `work-intake` is declared only by `packs/core/pack.toml`. On the genuine
  Core-absent limb the invocation AC7-AC9 name does not resolve, and the shipped
  prose does not say what the agent does then. The implementation conforms to
  AC7-AC9 as approved; changing it would be a spec amendment, not a repair.
- The plan's supporting quote for that routing is weaker than it reads:
  `docs/specs/shaping-intake-handoff/spec.md:17` governs requests *without a
  handoff* under a present Core, not Core absence. The adjudicators separately
  confirmed the prior spec's AC9 prohibitions are each satisfied — no mandatory
  core dependency is declared, and `packs/product-engineering/pack.toml` carries
  no `[pack.dependencies]` table — so there is no cross-spec contract conflict.
