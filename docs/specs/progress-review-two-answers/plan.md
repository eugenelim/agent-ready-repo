# Plan: progress review two answers

- **Spec:** [`spec.md`](spec.md)
- **Status:** Drafting <!-- Drafting | Approved | Executing | Done -->
- **Repository anchors:**
  `packs/product-engineering/.apm/skills/frame-intent/SKILL.md` (the
  `[product] output_dir` resolution, anchored to the layout file's own
  location, and the compose-if-present degrade-if-absent pattern this follows);
  `packs/product-engineering/.apm/skills/frame-intent/assets/intent-template.md`
  (the `## Outcome` section this reads);
  `docs/specs/delivery-forecast-with-uncertainty/` (the forecast this takes as
  input). Named deviation: this skill renders a review, and no existing
  `product-engineering` skill renders a composed artifact from two sources.


> **Plan contract:** this is the implementation strategy. It may change
> substantively only while its Status is `Drafting`, before approval records its
> baseline. After approval, `spec.md` and `plan.md` are pinned in substance;
> only lifecycle bookkeeping is permitted, and execution observations belong in
> `docs/specs/<feature>/notes/verification-ledger.md` (or the adopter's
> equivalent). A genuine artifact error follows the controlled-amendment path.
>
> **Not every field is contract.** `Touches`, `Tests` and `Done when` are what a
> completion gate reads, and they are pinned. `Design`, `Approach`, `Grounding`
> and `Risks` are working material that an implementer corrects in place only
> before approval: approval hashes the whole plan. After approval, grounding for
> a seam recorded as `no stub (implementation-discovered)` goes to the
> verification ledger; a settled design decision that execution falsified is a
> plan error that follows the controlled-amendment procedure. Treating them as
> contract is how a review spends a round on prose no gate consumes — the
> measured share is over half the plan's lines. `Grounding` stays *recorded*,
> because a per-task resolution that nobody wrote is not grounding; what it stops
> being is a claim a reviewer holds the plan to.

<!-- Existing plans without this field remain valid. Treat its absence as a
named assurance gap during structural review, not a universal lint failure. -->

<!-- **Durable-plan fill.** This template is the implementation and verification
strategy for a durable delivery slice. Fill Approach, Constraints, Risks,
Design, Tasks, and Changelog to the depth the durable work requires. Its sibling

## Approach

The review is a composition, not an integration. It reads repository artifacts
— the intent tree at the adopter's configured `output_dir` — and takes a
forecast as supplied input rather than fetching one. That is what keeps it free
of any provider pack: the delivery-system skills are user scope and run in
whatever directory the user is in, so a review that called them would have to
resolve and confine a repository path on four providers.

The outcome half always works, because it reads an artifact that is always
there. The delivery half degrades to a stated absence. Both degradations are
rendered rather than silent, which is the same compose-if-present pattern
`frame-intent` already ships.

The riskiest part is the unchecked case, and it is risky because it is
tempting to drop. An intent whose outcome has no reading contributes nothing to
a review that is trying to look complete — and dropping it reproduces exactly
the selection effect the parent measured, where the claims least likely to be
checked are the ones that most need checking. So the unchecked case is a
criterion with its own test rather than a rendering nicety.

## Constraints

- **ADR-0125 D4** bounds what may be counted: below the floor a trace is
  readable and must not enter a statistic.
- **CAP-0004's guardrail** forbids a daemon, control plane, database or
  scheduler.
- **No provider dependency.** Delivery-system packs install at user scope;
  this skill neither calls one nor declares one.
- The intent's `## Outcome` section is the frame-intent template's, and this
  slice reads it without changing it. There is no new field and no lint.
- The forecast's shape belongs to `delivery-forecast-with-uncertainty`.

## Construction tests

- A verbatim check comparing rendered outcome text against the source intent's
  `## Outcome`.
- A scope-completeness fixture: removing any single in-scope intent from the
  rendered review fails the check.
- A no-forecast fixture asserting the delivery answer renders as unavailable
  and the outcome answer still renders.
- A separation check over rendered output asserting the two answers occupy
  distinct parts.
- Path-resolution fixtures: configured relative, configured absolute, unset.

## Durable-output map

| Output | Task | Evidence |
| --- | --- | --- |
| Intent tree resolution | T1 | path fixtures green |
| Closed scope and verbatim outcome rendering | T2 | removal fixture fails for every member |
| Delivery answer and its degradation | T3 | no-forecast fixture green |
| Separation contract | T4 | separation check green |
| `product-engineering` changelog entry and the user-facing promise | T4 | one entry; the separations drafted |

## Design (LLD)

### Design decisions

- **The forecast is an input, not a fetch.** A fetched forecast would couple
  this skill to four user-scope provider packs and give it a repository path to
  resolve on each. Taking it as input keeps the review composable in a
  conversation where a provider skill has just answered.
- **Nothing is graded.** A score over a recorded reading would manufacture the
  benefit overstatement the parent's evidence measures, so the review renders
  the reading and stops.
- **Nothing is detected inside `## Outcome`.** That section's contract belongs
  to `frame-intent`, which defines declarations and no reading representation,
  and the accepted cut carries no slice that adds one. The review reproduces
  the section and adds nothing, so it never has to decide what a reading is.
- **Scope is closed and every member renders.** Asserting that *an* intent with
  nothing recorded appears passes while another is silently dropped. The
  parent's evidence is that the missing reviews are non-randomly the important
  ones, so completeness is the criterion, not visibility of one example.

### Data & schema

Input is the intent tree at the resolved `output_dir`, plus an optional
forecast. Output is a rendered review with two named parts.

### Interfaces & contracts

No new interface. The forecast is passed in the shape
`delivery-forecast-with-uncertainty` renders.

### Component / module decomposition

Everything lands in `packs/product-engineering/`.

### State & control flow

The review is computed on invocation and holds no state between runs.

### Behavior & rules

An intent with no `## Outcome` section is reported as malformed rather than
skipped — malformed is still in scope and still renders. The section is
reproduced as written; the review makes no claim about what it contains.
Neither answer is derived from the other.

### Failure, edge cases & resilience

An unresolvable `output_dir` produces a stated failure, not an empty review,
because an empty review reads as "nothing to report". A forecast supplied in an
unrecognised shape is reported as unavailable rather than rendered partially.

### Quality attributes (NFRs)

The separation criteria carry the pass/fail bar: two distinct parts, neither
presenting the other's answer.

### Dependencies & integration

No new dependency, and explicitly no provider pack.

## Tasks

### T1: the intent tree resolves through the adopter's configured output_dir

**Depends on:** none

**Tests:**
- Configured relative, configured absolute, and unset each resolve or fail as
  `frame-intent` specifies. Verifies *resolves through the configured
  `[product] output_dir`*.
- An unresolvable tree produces a stated failure, not an empty review.
  Verifies *says so rather than rendering an empty review*.

**Approach:**
- Reuses `frame-intent`'s resolution semantics — anchored to the layout file's
  own location, `..` rejected after anchoring — rather than reimplementing
  them, so the two skills cannot disagree about where intents live.

**Done when:** all three path fixtures behave as specified and the
unresolvable case states its failure.

**Touches:** packs/product-engineering/.apm/skills/**

### T2: the scope is closed and every intent in it renders verbatim

**Depends on:** T1

**Tests:**
- The review states its scope as a closed, enumerable set. Verifies *states its
  scope as a closed, enumerable set*.
- Removing any single in-scope intent from the rendered review fails. Verifies
  *every intent in that scope appears; omitting any one fails*.
- Each section is reproduced verbatim and labelled as declared. Verifies *whole
  `## Outcome` section is reproduced verbatim*.
- A section carrying nothing beyond its declarations renders them above an
  explicit statement that nothing further is recorded. Verifies *renders those
  measures above an explicit statement*.
- No checked/unchecked label, score, grade or judgement appears. Verifies *the
  review classifies no intent as checked or unchecked* and *renders no score,
  grade or judgement*.

**Approach:**
- Completeness is asserted by removal, not by presence of one example. An
  omitted intent produces no error anywhere, so a presence assertion passes
  while the set silently shrinks.

**Done when:** the removal fixture fails for every member of the scope.

**Touches:** packs/product-engineering/.apm/skills/**

### T3: the delivery answer degrades to a stated absence

**Depends on:** T1

**Tests:**
- With no forecast supplied, the delivery answer renders as unavailable and
  the outcome answer still renders. Verifies *states the delivery answer is
  unavailable and still renders the outcome answer*.
- No rendered review presents a forecast as a committed date.

**Done when:** the no-forecast fixture renders both parts, one of them as an
explicit absence.

**Touches:** packs/product-engineering/.apm/skills/**

### T4: the two answers cannot be read as each other

**Depends on:** T2, T3

**Tests:**
- The two answers occupy distinct parts of the rendered review. Verifies *the
  two answers occupy distinct parts*.
- No rendered review presents delivery completion as outcome movement.
- The skill calls no delivery-system skill and the pack declares no provider
  dependency.
- A review leaves no resident process.

**Done when:** the separation check is green, the pack manifest names no
provider dependency, `packs/product-engineering/CHANGELOG.md` leads an entry,
and the two separations are drafted on the user-facing surface.

**Touches:** packs/product-engineering/**, packs/product-engineering/CHANGELOG.md

## Rollout

T2 and T3 are independent once T1 lands. T4 gates, because the separations are
what distinguish this review from a page with two numbers on it.

## Risks

- **An intent is silently dropped from the reviewed set.** Mitigated by the
  removal fixture, which fails for every member rather than checking that one
  example is present.
- **The two answers drift toward one number.** Mitigated by the separation
  check running over rendered output, where the collapse would actually occur.
- **A future change makes the review fetch a forecast.** The no-provider-
  dependency assertion is the detector.

## Changelog

- 2026-09-24 — plan drafted.
