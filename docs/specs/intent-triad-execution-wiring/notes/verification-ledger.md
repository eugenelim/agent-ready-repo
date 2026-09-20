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
