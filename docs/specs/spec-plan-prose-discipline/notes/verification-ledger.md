# Verification ledger — spec-plan-prose-discipline

Execution observations for `docs/specs/spec-plan-prose-discipline/`. The spec
and plan are pinned; anything learned during execution is recorded here.

## Manual-QA recorded verdicts

The Testing Strategy declares five criteria unmechanizable. The verdict below
**is** the result; no keyword count stands behind it.

Reviewer: `codex exec`, `gpt-5.6-sol`, reasoning effort high, `--sandbox
read-only`. Two rounds, 2026-09-18. The reviewer is not the author of the
prose it read.

| Criterion | Verdict | Round |
| --- | --- | --- |
| AC-0013 — each note states its own rule and defers the other surface's | PASS | 1 |
| AC-0014 — the conditional `Approach:` rule is followable in both halves | PASS | 1 |
| AC-0015 — the reference covers only what the managed block does not, and reads as advice | PASS | 2 |
| AC-0016 — no obligation lost in the rewrite | PASS | 2 |
| AC-0019 — the two-sentence cap is applicable; `What Changes` is a delta | PASS | 1 |

### Round 1 findings and their adjudication

Round 1 returned FAIL on AC-0015 and AC-0016, naming six lost obligations.
Each was tested against the accepted contract before it was acted on.

**Sustained — AC-0015(a).** The echo-close tell read "A paragraph whose last
sentence restates its first, or a section that ends by summarising itself."
The second clause restates the managed output-rendering block's `no repeated
summary`, which the reference exists to avoid duplicating. Repaired: the
clause was cut and the block named as its owner.

**Sustained — AC-0016.** The retired Assumptions note obliged the author to
"fix the spec body in the same PR" when an assumption later turned out wrong.
Settling an open item and discovering a filed fact is wrong are different
events, and the rewrite homed only the first. Repaired: the note now sends the
correction to wherever the fact was doing work.

**Refuted — four.** Each is a reversal the accepted spec names in `What
Changes`, not a loss:

| Claimed loss | Why refuted |
| --- | --- |
| Plan Changelog records drafting changes | Reversed by AC-0001 and named in `What Changes` |
| Assumptions retains settled facts and sources | Reversed by AC-0002 and named in `What Changes` |
| `Tests:`-outnumbers-`Approach:` is a smell | Cannot exist once a task may carry no `Approach:`; a ratio needs both terms |
| Keep the former Objective to one paragraph | Superseded by a strictly tighter two-sentence cap, not dropped |

Round 2 re-read both repairs, returned PASS on each, and raised no new
finding.

## Mutation proof

`packs/core/tests/skills/new-spec/test_artifact_prose_discipline.py` was run
against sixteen single-property reversions. Each reversion restored a
pre-change statement or removed a post-change one; the module reddened on
every one, and each mutation was reverted before the next.

| Reverted property | Result |
| --- | --- |
| Drafting-history entry re-added to the plan Changelog | red |
| Approvals-only claim replaced by the old dated-entry instruction | red |
| `(source: …)` citation re-added to Assumptions | red |
| Routing destination generalised to "the plan somewhere" | red |
| `## Agent Rules` renamed back to `## Boundaries` | red |
| `## Outcome` renamed back to `## Objective` | red |
| Stale "plan keeps its own changelog" claim restored | red |
| Copy-the-confirmed-list instruction restored to SKILL.md step 3 | red |
| One of the reference's four parts renamed | red |
| Advisory opening replaced by "Apply these rules." | red |
| Gate vocabulary introduced into the reference | red |
| Second `prose-discipline` pointer added to the rubric | red |
| Legacy heading dropped from `adversarial-reviewer.md` | red |
| Old four-section list restored to the contract reference | red |
| (two anchors re-run after correcting for hard wrapping) | red |

The guard arm `TheSlicerIsNotVacuous` exists because every absence assertion in
the module passes over an empty string. It walks the same slice set the content
arms use rather than a list that could drift from it.

## Execution observations

**Two anchor tests needed updating, and one was byte-pinned.** The step-8a
sweep found `test_acceptance_criteria_discipline.py` (pinning the phrase "One
ratio, two causes, opposite remedies", retired with the `Approach:` ratio rule)
and `test_shaping_review.py` (pinning the old section-name list). It did not
find `packs/core/tests/pack/test_review_depth_and_verdict_contract.py`, whose
`LEGACY_REVIEW_MODES` constant is a byte-exact copy of a block in
`adversarial-reviewer.md`; it surfaced only when the pack suite ran. A
content-hash pin of another file's prose is invisible to a grep for the phrase
being changed, because the pin lives in a string literal that reads as test
data.

**A pack test cannot reach the guide.** `lint-pack-test-boundary` scopes a pack
test to `packs/<pack>/`, so AC-0009's `guides/core/` half lives in
`tests/roster/test_spec_prose_discipline_guide.py`. `test-roster.yml` is
dispatch-only, so that arm is partial evidence and is not a required PR check.
It was run directly for this delivery: 3 passed, 6 subtests.

**AC-0018 was unsatisfiable alongside a Markdown link.** The criterion requires
exactly one occurrence of `prose-discipline` in the rubric, and
`[`prose-discipline.md`](prose-discipline.md)` contains two. The pointer was
written as plain text rather than amending an approved criterion over
formatting; the rubric's sibling reference is in the same directory, so
navigation is unaffected.

**This run used no loop engine.** `loop-engine` and `loop-cohort` were never
initialised, so there is no `engine-state.json`, no `state.json`, and no
recorded `approved_spec_hash`. The approvals are recorded in the artifacts
themselves — `Status:` lines plus the two dated Changelog entries — which is
the form a later reader reads. Review rounds ran as Codex reviewer sessions
rather than installed subagents.

## Delivery measurements

**Template growth is authoring guidance, not reader surface.** A peer session
flagged that the templates grew +47 lines net and asked whether the change
moves reader cost the wrong way. Measured against `origin/main`, excluding
HTML authoring comments, which never reach a filled-in artifact:

| Template | Total lines | Emitted skeleton |
| --- | --- | --- |
| `assets/spec.md` | 285 → 324 (+39) | 59 → 60 (+1) |
| `assets/plan.md` | 301 → 309 (+8) | 115 → 123 (+8) |

Nearly all the growth is comment-only guidance. The reader's cost lives in the
emitted corpus, and at that peer's measured per-artifact rates this change
stops authoring roughly 11,600 lines of Assumptions audit trail across 404
specs and 7,600 lines of plan drafting history across 330 plans, with up to
13,900 more in task `Approach:` blocks where no ordering or seam decision
exists. Those are forward numbers for new artifacts; nothing existing is
retrofitted.

**A lint reported, without failing, that AC-0014 was reworded with no changed
assertion in `plan.md`.** The rewording is the `[goal-based]` / `[manual QA]`
tagging added when the Testing Strategy split, not a changed obligation; T1's
assertion naming AC-0014 still verifies what the criterion states. Recorded
here rather than silenced.

**Weak evidence pointing the other way, recorded and not acted on.** The same
peer reported a correlation pass over 17 specs: larger `## Objective` went
with fewer review findings (partial Spearman −0.49) and larger task
`Approach:` with fewer rounds (−0.49), both controlling for total size. Every
bootstrap interval crossed zero, and neither is a controlled comparison, so
this is a lead rather than a result. It is noted because both directions
oppose parts of this change; if either firms up, the two-sentence `Outcome`
cap and the conditional `Approach:` are where to look.

## Quality-engineer pass

Reviewer: `codex exec`, `gpt-5.6-terra`, reasoning effort high, read-only,
scoped to the two new test modules. Returned four Concerns and one Nit; none
was a Blocker.

| Finding | Disposition |
| --- | --- |
| Gate-vocabulary arm named for a property it cannot establish | repair-the-artifact — renamed to `test_it_carries_none_of_three_named_gate_words`, with the limit stated in the arm |
| Numeric-threshold arm misses spelled-out and `percent` forms | repair-the-artifact — renamed to `test_it_states_no_digit_shaped_threshold`; `percent` added to the pattern |
| The guide's exact-sentence pin reds on a harmless rewrite | repair-the-artifact — split into the two conditions the rule turns on |
| Bare-word `Objective` / `Boundaries` check can red on ordinary prose | accept-as-proportionate — AC-0009 states this as a closed list of three strings, the guide has no ordinary use of either noun, and a heading-shaped pattern would miss the prose references that are the real risk. Reason recorded in the arm |
| The stale-phrase glob passes vacuously on an empty result | repair-the-artifact — promoted from Nit and fixed, because it is the same vacuity hole the module's own guard class exists to close |

The first two findings are the review's third and fourth instance of one
class: a check named for more than it establishes. Adversarial round 1 found
it in AC-0007, round 2 found the same overclaim surviving in the plan's T1,
and this pass found it twice more in arm names. The class is worth naming:
when the property is a judgement, the arm's *name* is where the overclaim
hides, because the assertion itself is honest and only the label lies.

## Artifact exercised

The installed projection was scaffolded, not just the pack source:
`.claude/skills/new-spec/assets/{spec.md,plan.md}` were copied to a scratch
directory and read with comments stripped. The emitted skeleton carries
`## Outcome`, `## What Changes` and `## Agent Rules` with its three tiers, in
that order, and no `## Objective` or `## Boundaries`.
