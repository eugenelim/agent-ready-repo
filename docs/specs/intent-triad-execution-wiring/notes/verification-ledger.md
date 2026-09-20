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
| the release fold-forward left `product-engineering 0.13.13` cited but unreachable | repointed to `0.13.14`; the only `0.13.13` left in the tree is this ledger row and the rows below that name it |

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

## Review round 2 — the repair reproduced its own root cause

Round 2 re-reviewed the round-1 repairs and defeated two of them. Both raw
reports and adjudications are under `.context/reviews/9129ff2a-b134-4542-91db-210e993c1b3f/`.

### The class, named

The adjudicator confirmed a single class behind every finding in both rounds:

> every finding across both rounds is a control whose assertion is necessary but
> not discriminating, because the differential premise that would make it
> discriminating is assumed rather than asserted.

Round 1's own repair is the clearest instance. It closed AC7's movable boundary
by asserting that the resolved clause does **not** contain the negotiated
branch's `advertises` marker — and then never asserted that the marker still
existed. Rewording it to a synonym turned the guard into a vacuous negative, and
round 2 reinstated the exact defect round 1 claimed to close. An absence is only
evidence while the thing being looked for still exists to be found.

### The class-level repair

Rather than patch each instance, every helper now asserts the premise its bound
rests on, so the bound fails loudly instead of widening or going vacuous:

| Helper | Premise now asserted |
| --- | --- |
| `_assert_core_absent_clause_names_work_intake` | the differential marker is present in the body before its absence from the clause is read as evidence |
| `_list_item_containing` | no blank line separates the anchor from the bullet claimed as its own list item, so a de-listed anchor fails instead of widening across the JSON fence and the field table |
| the AC3 check (round 1) | the anchor sentence exists and precedes the floor rule |

The marker was also widened from `advertises` to the stem `advertis`, and the
helper comment corrected: two of the three G3 surfaces name `work-intake` on the
negotiated branch, not all three, which is what the spec's Testing Strategy says.

AC2's check was the second shape — a count standing in for a pairing. It now
binds `internal` to each slot type by proximity instead of counting occurrences,
so a rewrite naming the level once for both types no longer false-reds.

### Mutation evidence after the class-level repair

| Mutation | Expected | Result |
| --- | --- | --- |
| synonym + comma join + `work-intake` dropped (round 2's defeating mutation) | red | red |
| `assumption-test` sentence de-listed (round 2's defeating mutation) | red | red |
| AC8's differential marker reworded away | red | red |
| AC2 reworded to name `internal` once for both types | green | green |
| a third legitimate `decompose-intent` mention in the walk | green | green |

The last two matter as much as the first three: a repair that trades a false
negative for a false positive has moved the defect, not removed it.

### AC11's fit half is not mechanizable — recorded, not pinned

Round 2 showed that the three route bullets' bolded situation leads can be
swapped between routes with every test green, so AC11's "each with a one-line
statement of the situation it fits" is only half-guarded: the check proves each
route is named and carries *a* situation, not that the situation fits *that*
route.

Fit is a semantic relation. Every mechanical binding available would pin a
lexical anchor per route — `bet`, `raw idea`, `portfolio` — that AC11 does not
state, which buys a guard against a swap at the cost of reddening legitimate
rewordings the criterion permits. The adjudicator graded the reviewer's proposed
mechanism over-broad for that reason and offered recording the limit as the
alternative.

**Disposition: recorded, not pinned.** The named-and-present half stays
mechanically guarded; the fit half is verified by delivery-time read, performed
here — each bullet's lead states the situation its route serves: one bet end to
end, a raw idea with no named outcome, and positioning before naming a bet. A
future editor changing a route's wording is not fighting a test that pins prose
the criterion left free.

## Review round 3 — the class recurred a third time, once as a regression

Round 3 found the named class twice more, and one finding was a regression the
round-2 repair itself introduced.

### The regression

Round 2 replaced AC2's `count("`internal`") == 2` with a proximity regex, to
stop a legitimate rewrite false-redding. The regex was tempered against a repeat
of `internal` rather than against a *rival level*, so it matched whenever
`internal` and each type name appeared anywhere in the clause. A slot type
pinned to `sensitive` or `regulated` passed. That is **weaker than the count it
replaced**: the count would at least have caught it. Fixing a false red produced
a false green, which is the trade the round-2 ledger entry itself warned about
and then failed to test for.

### The premise was asserted at the wrong scope

Round 2's G3 repair asserted the differential marker was present *somewhere in
the body*, while the differential it licenses is *clause* scope. The gap is
reachable: reword the adjacent sentence's marker to a synonym, join the clauses
with punctuation the splitter does not terminate on, drop `work-intake` from the
Core-absent branch, and add any unrelated line elsewhere in the file containing
the marker — and the premise is satisfied by the unrelated line while the
criterion is violated on the surface. Round 3 demonstrated it end to end.

The premise was moved to the clause preceding the resolved one, so an
occurrence elsewhere in the file no longer satisfied it. **Round 4 showed this
claim was wrong in two ways**, both corrected below: `_preceding_clause`
actually returned the two clauses before the span, not one, and relative
adjacency cannot certify that a span resolved at all — the same attack worked
with "elsewhere in the file" replaced by "one clause earlier".

### AC2, repaired without either failure direction

The check now asserts both slot types are named, `internal` is the level given,
and no rival level from the schema's vocabulary appears in the clause. The
vocabulary is held in the test rather than parsed from the table under test, and
the test asserts the table still lists exactly those four levels — so a level
added to the schema reds the premise instead of silently widening what the
absence check means.

### Mutation evidence, both directions

Round 2's table recorded only green-direction outcomes for the two controls the
repair changed, so it could not tell a discriminating control from a permissive
one. Both directions are recorded now.

| Mutation | Expected | Result |
| --- | --- | --- |
| round 3's B2 defeat: synonym + `--` join + `work-intake` dropped + marker elsewhere in file | red | red |
| round 3's B1 defeat: `delivery-contract` given a rival level | red | red |
| B1 mirror: `assumption-test` given a rival level | red | red |
| a level added to the schema table but not the test vocabulary | red | red — but only for a name matching `[a-z]+`; round 4 showed a hyphenated name passed, and that hole is closed in round 4 below |
| AC7's marker removed from the clause next door | red | red |
| AC7's `work-intake` dropped from the Core-absent clause | red | red |
| AC8's `work-intake` dropped | red | red |
| AC4's `assumption-test` bullet de-listed | red | red |
| AC2 reworded to name `internal` once for both types | green | green |
| a third legitimate `decompose-intent` mention in the walk | green | green |

### Two limits now stated rather than assumed

`_list_item_containing` models a single-paragraph `- ` bullet; a multi-paragraph
item, a nested list, or an ordered list reds rather than widens.
`_clause_containing` splits on `[.;]\s`, so a sentence-internal abbreviation
would narrow a span. Both failure directions are red, not green, and both are
now named in the helpers' docstrings so a future red is diagnosable as the
helper's shape assumption rather than a missing obligation.

## Review round 4 — the class closed by changing scope, not by another premise

Round 4 defeated round 3's repair too, and its findings were stronger than
round 3's rather than weaker. That ended the repair chain: four rounds, each
finding the same class, is a signal about the approach rather than about the
individual controls.

### Why the previous three repairs all failed the same way

Each one scoped the check *around* or *behind* the anchor and then tried to
certify that scoping with a premise — the marker's presence in the body, then
in the neighbouring clause. Round 4 stated the reason that cannot work:
**relative adjacency to a resolved span cannot certify that the span resolved.**
Whatever the premise names, the attacker moves the same boundary the premise is
computed from.

### The fix: scope forward, where nothing can supply a false positive

The check now reads from the Core-absent anchor *forward* to the end of its own
clause. Nothing behind the anchor can satisfy a forward span, so the merge
attack has nothing to offer: the negotiated branch's own `work-intake` lies
behind. Two shipped sentences were reordered so the obligation follows its
anchor, which AC7 and AC8 permit — they fix which sentence must name
`work-intake`, not the order within it.

The one remaining direction is a *forward* merge, and that premise is asserted
rather than assumed: the clause after the Core-absent one must not name
`work-intake` either. `_preceding_clause` is deleted.

AC2 now parses the `from <level> for <types>` pairings and requires each unit
naming a slot type to give exactly `internal`, covering both types between
them. That closes a type given a rival level, a type given no level, and a
rival level written without a code span. The level-vocabulary premise now
extracts any backticked cell name, so a hyphenated level reds it.

### A control was deleted and nearly shipped

While applying these repairs a block replacement silently removed
`test_the_classification_section_states_the_floor_rule`, which is AC3's only
guard. The suite stayed green at 19 tests instead of 20 — a passing suite is
not evidence that the control you meant to keep is still in it. It was caught
by comparing the test count against `HEAD` and restored. No name-set pin was
added in response, because pinning the set blocks adding a test later; the
check that caught it — compare the inventory against the previous commit — is
the one worth repeating.

### Mutation evidence

| Mutation | Expected | Result |
| --- | --- | --- |
| round 4's B1: merge + reword + drop obligation + marker one clause earlier | red | red |
| round 4's B2: `delivery-contract` given no level at all | red | red |
| round 4's B2b: rival level written without a code span | red | red |
| round 4's B3: a hyphenated level added to the schema table | red | red |
| AC7's `work-intake` dropped | red | red |
| AC8's `work-intake` dropped | red | red |
| AC9's `work-intake` dropped | red | red |
| AC3's anchor sentence deleted | red | red |
| AC4's `assumption-test` bullet de-listed | red | red |
| AC2 reworded to name `internal` once for both types | green | green |
| a third legitimate `decompose-intent` mention in the walk | green | green |

### Open, for the owner

Round 4's Blocker 1 is closed for the forward-merge direction that remains, but
the general lesson stands and is not a defect to fix here: a sentence-scoped
obligation over free-form prose is guarded by a text-slicing check only as far
as the punctuation holds. The realistic regression — an editor drops
`work-intake` — has been caught by every version of this control since round 1.
The exotic one — an editor re-punctuates *and* drops the obligation — is what
took four rounds. Whether that second bar is worth carrying is an owner
decision, recorded here rather than decided by the implementer.

## Owner decision — the bar was reduced, and this is what it costs

After four review rounds the owner weighed the two failure shapes and declined
the second:

- **An editor drops the obligation.** The realistic regression. Guarded.
- **An editor re-punctuates the surrounding prose *and* drops the obligation.**
  Declined as not worth carrying.

The G3 checks were simplified accordingly: the premise assertion guarding the
merge case is removed, `NEGOTIATED_MARKER` is deleted (already dead after the
forward-scoping change), and two docstrings that argued the reasoning at length
now state the limit in three lines and point here.

### What the simplification actually gives up — measured, not assumed

Reading forward from the anchor turns out to carry most of the declined
protection for free, because the negotiated branch's own `work-intake` lies
*behind* the anchor on all three surfaces and cannot satisfy a forward span. The
attack that defeated three earlier versions of this control — merge backwards,
reword, drop the obligation — still reds.

Exactly one shape is now unguarded, and it was constructed and confirmed green
rather than reasoned about:

> the Core-absent clause loses the obligation, the text that *follows* it names
> `work-intake` for an unrelated reason, and the two are joined so the forward
> span reaches it.

That shape is not reachable in the current text: the clause following the
Core-absent one is "Do not send the unsupported top-level object…", which does
not name `work-intake` on any of the three surfaces. It becomes reachable only
if a future edit puts `work-intake` into that following clause. Nothing now
warns when that happens, and that is the accepted residue.

### The reduced bar, verified

Eleven mutations were run against the simplified controls. Every realistic
regression still reds:

| Mutation | Result |
| --- | --- |
| AC7 `work-intake` dropped from the Core-absent branch | red |
| AC8 `work-intake` dropped | red |
| AC9 `work-intake` dropped | red |
| AC7's whole Core-absent sentence deleted | red |
| AC7 re-punctuated backwards *and* obligation dropped | red |
| AC2 `delivery-contract` given a rival level | red |
| AC2 `delivery-contract` given no level at all | red |
| AC3 anchor sentence deleted | red |
| AC4 `prototype-approach` dropped | red |
| AC1 `delivery-contract` dropped from the `type` row | red |
| AC5 G3 pairing unpaired | red |
| AC6 `frame-intent` re-added to the exclusion | red |
| AC12 later-step skill injected into the menu | red |
| AC13 pointer removed | red |

The test inventory was re-checked at 12, matching the count before the
simplification, so no control was lost to the edit.

## AC16 was wrong, and CI caught it after the rebase

AC16 originally required the `product-engineering` heading "placed above every
other pack release heading". That is unsatisfiable whenever `core` has a live
release entry, and the repository enforces the opposite:

> `tests/roster/test_verification_ledger_contract.py::test_the_core_release_heading_sits_directly_beneath_unreleased`
> asserts the first versioned heading after `[Unreleased]` is `[core]` at
> `packs/core/pack.toml`'s version, so this pack's entry goes below the `core`
> block even though it carries a later date.
> — `docs/specs/channel-minimum-width/spec.md` AC-0013

The criterion was authored while this branch's only release was
`product-engineering`, and no `core` entry sat above it, so the conflict was
invisible until the rebase brought `core 2.26.21` onto the branch.

**Correction applied:** the `core 2.26.21` block is re-seated directly beneath
`[Unreleased]`, with `product-engineering 0.13.14` below it. AC16 now states
the topmost-for-this-pack rule and cites the enforcing test.

### The near-miss worth recording

The first diagnosis was that the test was an over-fitted delivery-time criterion
turned standing guard, and the evidence looked strong: replaying main's history
showed two commits where a non-core heading sat topmost while the test was
live — one of them `product-engineering`. That replay was sound about the
commits and wrong about the conclusion, because it never asked whether a
*convention* existed that those two commits had simply violated. Reading the
owning spec settled it in one line.

**A history replay shows what happened, not what is permitted.** Before calling
a guard over-fitted, find the artifact that owns it and read what it requires.
Two violations in 133 commits is as consistent with a convention occasionally
broken as with a guard that is wrong, and the two cases take opposite repairs.
