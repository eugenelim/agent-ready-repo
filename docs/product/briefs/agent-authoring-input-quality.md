# Brief: contracts a review loop converges on

- **Slug:** `agent-authoring-input-quality`
- **Received:** 2026-09-02
- **Owner:** Repository maintainers (`ini-002`)
- **Status:** Draft

## Outcome

An author — human or agent — writes a spec and plan that a review loop can
converge on. Today most of what review finds is not the subject but the way it
was written, and a contract can be sized past every point where this repository
has ever converged without anything objecting.

Three things change:

- **A criterion states an outcome that can fail, once, in one place**, and a
  plan task says what to verify rather than spelling out the assertion.
- **A plan records whether an owner already exists** for the responsibility it
  is about to design, alongside the imitation anchors the template asks for.
- **A contract is sized before it is written**, against what this repository
  has converged on rather than an author's sense of scope.

This only **partially** prevents non-convergence, deliberately. A better
contract still gets things wrong; what a loop does on that discovery is
[`agent-loop-escalation-recovery.md`](../intents/agent-loop-escalation-recovery.md).

## Success metrics

- Review rounds on a new contract find defects in the subject rather than in
  the criteria's wording — measured by classifying a round's findings, not by
  counting them.
- A round whose findings share a premise is classified as **one** finding about
  the mechanism, not several about the criteria. The first metric cannot see
  that failure alone: findings over a wrong mechanism score there as success.
- Every rule shipped here can be shown to have fired at least once. A rule with
  no firing is withdrawn, not re-worded.
- A contract over the sizing band stalls at authoring, not at round six.

**First firing evidence, 2026-09-08.** Every rubric class fired at least once
while the A1 candidate was authored and reviewed, so none is a withdrawal
candidate yet. **Recorded but not independently verifiable:** the firings are in
round-numbered review artifacts under `.context/reviews/`, which `.gitignore`
excludes, so they did not travel with the repository. Treat the metric as this
session's record rather than as evidence a later reader can check. **Firing is not activation**: it shows
the classes name real defects, not that shipping them as prose changes what an
author writes. Only the activation measurement settles the second, and the
ablation's marginal contribution is two of its six seeded defects.

The stall metric has a counter-example to answer: the candidate never stalled at
authoring, and its later rounds still returned blockers. Whether the band should
have stopped it, or whether the band does not govern a reference-shaped
deliverable, is open.

## Scope / Non-goals

**In scope**

- The failure-point rubric, and the authoring instructions derived from it.
- **The delegation anchor:** a plan records whether an existing owner for the
  contract was found.
- **Sizing discipline** — the band below, shipped as dated evidence plus the
  derivation that lets any repository recompute it.
- Widening `new-spec`'s existing step 5a so a criterion's satisfiability is
  probed before the spec gate. A scope change to a rule that exists.
- **The ownership survey.** Conditional; see § "The survey is a lean".

**Non-goals**

- Readiness at a stage handoff — the pre-creation pressure test, the checks at
  `new-spec`'s input and at the spec-to-implementer handoff, and review
  sequencing: [`stage-input-readiness.md`](stage-input-readiness.md).
- Whether written guidance activates at all:
  [`guidance-activation-measurement.md`](guidance-activation-measurement.md).
- Rewriting the cognitive-load or cut-before-adding rules.
- Changing the review lens, or how findings are adjudicated.
- What a loop does once it has discovered the contract is wrong.

## Constraints / Appetite

**Everything here waits on the activation measurement's report** (owner
decision, 2026-09-02). If that report says written guidance does not bind here,
these deliverables become machinery — and machinery leaves this brief until an
approved amendment sets its appetite.

Every rule shipped here carries the activation contract owned by
[`guidance-activation-measurement.md`](guidance-activation-measurement.md)
§ "Constraints / Appetite".

## Sizing discipline

The abandoned contract at `e1bdde746` carried **39 acceptance criteria in
11,258 words**, six of its criteria over 150 words and the longest at 704.
Those are frozen properties of one dated artifact. Where it sat against the
corpus is a live comparison, so run § "Corpus"'s instrument for it rather than
reading a percentile stored here. The outcome is what matters either way:
eleven review rounds, no convergence, abandonment. Sizing is a lever on this brief's outcome, not a
style preference.

### Altitude precedes size

**Check the artifact's altitude before applying any bound below.** The band's
bounds are all within-artifact, so none of them decides whether the artifact is
the right one. Rubric § 5 states that gap, the sizing failure behind it, and
the repair.

The recognized altitudes run `product-vision > product-strategy > capability >
feature`, and `decompose-intent` produces the levels beneath whichever is
chosen. A delivery brief sits at capability altitude with feature-level slices
beneath it. (A tally of this repository's intents by level stood here; no bound,
gate or decision read it, and its figures were stale on every term, so the
rubric's own decoration test deletes it.)

**Three tells that an artifact is above its altitude**, each cheaper to check
than any percentile, now ship in the rubric's § 5 under *Altitude precedes
size*, which is their home. One of the three is decidable against the
Proposed-slices table's own columns, and § "The rubric is a deliverable" routes
that one to a policy family. Neither document marks which tell that is; the
rubric states the tells without marking decidability at all.

The exhibit is this brief's own sibling set. An artifact authored on
2026-09-02 to hold cross-adapter behavior enforcement reached 3,573 words as a
delivery brief and showed all three tells. The band would have reported it as
oversized, which was the symptom; the defect was product-strategy content in a
capability container, and the repair was re-homing it as an intent rather than
cutting it.

This is the altitude analogue of rubric class 5, and the rubric owns that
class's repair.

### Corpus

**This section publishes an instrument, not a snapshot.** Every figure it used
to carry was an exact count over a corpus that grows, which is rubric class 4's
decay case: a stored count of a growing set is wrong as soon as the set moves,
and nothing here would notice. The bound that reads this corpus is stated as
the derivation instead, so it means the current corpus on the day anyone
asks.

**The instrument.** `docs/specs/*/spec.md` at exactly one directory level. The
status is the first line matching `^-?\s*\*\*Status:\*\*`, which must reduce to
the leading token `Shipped` once an annotation (`Shipped (2026-05-26)`) is
stripped — the leading `- ` is optional, and omitting that clause is what made an
earlier predicate under-count. A criterion is a checkbox bullet under
`## Acceptance Criteria`, since roughly half the corpus labels them `**ACn —**`
and half does not. A spec's word count is the whole file, verbatim, including its
metadata header. § "Corpus exclusion" names the specs a run must leave out;
that rule is part of the instrument rather than a caveat on it.

Running it is one command, and it stores nothing — which is why it is not the
regenerator § "Why no regenerator" rejects:

```bash
python3 - <<'EOF'
import glob, re, statistics
EXCLUDE = {"agent-authoring-input-quality"}   # plus A1, A3, A4 and A5's specs
rows = []
for path in glob.glob("docs/specs/*/spec.md"):
    if path.split("/")[2] in EXCLUDE:
        continue
    body = open(path, encoding="utf-8").read()
    status = next(iter(re.findall(r"(?m)^-?\s*\*\*Status:\*\*\s*(.+)$", body)), "")
    if status.split("(")[0].strip() != "Shipped":
        continue
    section = re.search(r"(?ms)^## Acceptance Criteria\n(.*?)(?=^## |\Z)", body)
    criteria = re.findall(r"(?m)^\s*[-*] \[[ xX]\]", section.group(1)) if section else []
    rows.append((len(criteria), len(body.split())))
pct = lambda xs, p: statistics.quantiles(sorted(xs), n=100, method="inclusive")[p - 1]
for name, xs in ("criteria", [r[0] for r in rows]), ("words", [r[1] for r in rows]):
    print(f"{name}: n={len(xs)} median={statistics.median(xs):.0f} p75={pct(xs, 75):.0f}")
EOF
```

**No percentile is published here.** Not the spec-body pair the band reads, and
not a criterion-length pair — three attempts at the latter each differed on the
block boundary and none reproduced. A reader who needs a number runs the
instrument and states the date they ran it; a reader who needs a bound reads the
band, which names the percentile rather than its value.

### Band

Each bound carries its origin; a bound without one cannot be
argued with.

| Dimension | Bound | Origin |
| --- | --- | --- |
| Owning surfaces | one primary surface per slice | Measured, not repo-local, and now triangulated: 1 file → 95% resolution, 2 → 42% (SWE-bench Verified, Ganhotra 2025); Agentless localization falls 81.7% → 58.3% → 56.3% across file, function and edit-location stages; SWE-bench Pro resolves ~23% at 4.1 files against >70% on near-single-line work. Those figures are measured; that localization rather than repair is where the success is *lost* is an attribution no published ablation makes, so treat it as a synthesis. |
| Criteria per spec | ceiling of 10, **never a floor** | **Screening only, but no longer unevidenced.** Practitioner ceiling ~10. Joint satisfaction of independent verifiable constraints falls 77.7% → 33.0% from one-to-two up to four-to-eight, and 57.1% → 7.5% from two to eight, decaying near-multiplicatively. Both are single-generation benchmarks over stateless constraints, not an implementation loop with gates between attempts, so they establish the *shape* and not the threshold. This corpus records scope but not outcome, so no percentile of it corroborates a ceiling either. |
| Criterion size | **not a word budget.** The gate is semantic atomicity, owned by `packs/core/.apm/skills/new-spec/assets/spec.md` § Acceptance Criteria — the conjunction/substitution test and worked examples E1–E5. Rubric § 5 owns how length is used against that test. | Hard AC word budgets are already rejected here: `docs/specs/shaping-review-contracts/spec.md` ships it as a ticked criterion, RFC-0099 states "no hard word budget is added", and `new-spec/SKILL.md` Procedure step 6 makes shaping review reject one — "additionally rejects hard AC word budgets". The length signal is real but is a sampler, not a bound: RFC-0098 took 16 rounds with ~60 findings concentrated in its three longest criteria while its median-length criteria were quiet. § "Corpus" publishes no criterion-length percentile and records why. |
| Spec body | at or under the corpus median; past the corpus p75 needs a stated reason | Measured, repo-local, and stated as the derivation rather than a value so it cannot go stale: run § "Corpus"'s instrument and take the median and p75 of the words-per-spec distribution. |
| Human-equivalent duration | under one hour | Measured: R² = 0.83 against success, ~1 hour ≈ 50% (METR 2025). |
| Floor | never below one surface plus its verification and its guide | **Illustrative, not measured** — the label was overstated: cutting 8,500 → 2,100 tokens per step raised turns-to-solve from 4.0 to 14.0 while total consumption fell only 14% (Augment 2025), which is a practitioner writeup with no controlled arm and the only published number on the trade-off. **Smaller is not safer.** |

### Limit interaction

As `assets/spec.md` requires of any quantity
carrying two: both are reachable, because they bound different quantities and neither implies
the other: a spec can exceed the criteria ceiling well inside the body bound, and
exceed the body bound with few criteria. § "Corpus"'s instrument derives each distribution
separately — criteria per spec, and words per spec — and nothing relating one to
the other within a spec, so no bound here claims a ratio. Criterion size is not a
limit, so it can neither dominate nor be dominated.

### Corpus limits

Files changed per spec is not obtainable — no spec-to-PR linkage, and slug-grep
over-matches badly — so **no files-changed figure is quoted for this
repository**; the surfaces bound is imported from SWE-bench. Nothing records
review rounds per spec, so the corpus measures scope but not outcome. Nothing
establishes a criteria *floor*.

### Why no regenerator

Rejected: a regenerator slice — and the reason is now structural rather than a
judgement about cost. Rubric class 4 is the decay class, and one band row reads
this repository's growing corpus, so the class applies to it. That row states
the percentile rather than its value, and § "Corpus" publishes the instrument
rather than a snapshot, so there is no stored figure left to regenerate. What a
regenerator would maintain is exactly what class 4 rejects: a predicate that
cannot reproduce its own figures, criterion-length percentiles no instrument
reproduces, and a spec-body pair that goes stale within a week. The criteria ceiling is
screening-only — its evidence status is stated once, in the § "Band" row for
criteria per spec — so a stall threshold needs an order of magnitude rather
than a maintained script.

What an adopter needs is the **derivation**, which rubric class 5 states and the
guidance carries. Shipping our percentiles
as numbers would be wrong for every adopter on day one; shipping the derivation
is right for each. The figures here are dated evidence, refreshed by hand, and a
slice sized against them cites that date.

### Corpus exclusion

This brief does not grade its own sizing: an artifact measuring itself is
rubric class 6, and the exculpation has to be checkable or it is that same
defect. It is checkable because the brief stores no figure of its own corpus:
whoever needs one runs § "Corpus"'s instrument, outside this brief, and states
the date they ran it. **The corpus-exclusion rule travels with the
derivation:** A1, A3, A4 and A5's own specs are excluded from any run, or the
measurement grades specs written to the band it derives from them.

## What actually works, and what does not

Each finding below should shape every deliverable.
[`stage-input-readiness.md`](stage-input-readiness.md) cites this section by
name rather than restating it;
[`guidance-activation-measurement.md`](guidance-activation-measurement.md)
cites this findings corpus rather than restating its exhibits.

**This corpus is observed, not exhaustive, and deliberately uncounted.** The
entries are failure modes seen in live sessions, accumulated as they occurred.
One piece of work remains owed before it can claim coverage: **mining this
repository's own corpus** for the classes no session happened to hit. Until it
lands, treat an absent class as unobserved rather than absent, and do not size
a slice against the number of entries here.

The three entries dated 2026-09-08 came from authoring and reviewing this
brief's own first deliverable, so they extend the observed set without touching
the owed corpus mining. They also change what the corpus is evidence *for*: the
earlier entries are failures of contracts, and these are failures of **repairs
to** contracts, which is a population the corpus had no entry for.

**The prior-art placement is discharged**, in
[`spec-authoring-quality-survey.md`](../research/spec-authoring-quality-survey.md)
§ 1, which maps every class onto ISO/IEC/IEEE 29148:2018's nine
individual-requirement and five set-level characteristics, INCOSE's 42-rule
guide, and the eight requirements smells of Femmer et al. (2017). Its result is
load-bearing for the rubric rather than decorative: **five classes have no
equivalent in any of the three frames** — the design should have delegated, the
criterion decays, it targets a projection, it cuts a non-waivable control, and
it hand-enumerates a derivable set — **and a sixth, draft narration, has only a
weak one**, too weak to import from. Call that set **the unmatched six**; it is
not the rubric's six classes, and four of its members ship as sub-clauses inside
rubric classes 4 and 6. That section is also the one home for the shared cause
behind most of the unmatched six and for which of them it covers, so this brief
states neither. All of the unmatched six must be taught; the rest can cite a
frame.

The survey also names the one clear import we lack — a criterion *syntax*, for
which EARS supplies five templates and AWS Kiro is the agent-facing precedent —
and the one gap it opens: every class here is per-criterion, and 29148's
set-level characteristics have no counterpart in our authoring guidance. EARS
carries no controlled defect-reduction evidence in sixteen years, so it ships
as an optional aid and never as a gate.

### External binding

A rule's value is whether it binds to something outside the document. **That
now has an effect size from outside this repository.** Presenting a model with
byte-identical erroneous claims raises its correction rate by **23 to 93
percentage points** when the error arrives as a tool response or a user message
rather than as its own prior thought — significant at p<0.001 in 10 of 13
conditions, across seven model families
([`spec-authoring-quality-survey.md`](../research/spec-authoring-quality-survey.md)
§ 2). The failure is role-dependent, not content-dependent, which is why warm
self-review cannot substitute for an independent reviewer and why a criterion
graded from an implementer's own account of its work is weaker than one graded
by a test. Genuine self-correction does occur when the model calls a tool, so
the boundary is not *self* versus *other* but whether the signal originates
outside the actor.

Across the eleven review rounds at `e1bdde746`, every mechanism
that caught a defect **on its first run** bound the document to something
external — criterion-identifier parity between spec and plan,
assumption-citation parity in both directions, claims bound to a live symbol
table, and mutation proofs. The rules that lived only as prose were loaded in
context throughout and fired never.

Four non-activation exhibits from the corpus are concrete. Cognitive-load
simplification was routed from the root context while artifacts remained long
and dense with precise claims. The observable-outcome rule was read, cited as
authority, and broken repeatedly. Repository-anchoring tests asserted that
sentences existed in skill files, while the abandoned plan carried four
imitation anchors and no record of whether an owner existed.

A fourth target is a lean, not a finding. A measurement taken before the
claim is committed would bind the same way. Nothing in the corpus exhibits it,
and the one pre-commitment rule this repository ships is step 5a, whose firing
the activation measurement settles. Reject it without touching the three
findings.

### Wrong mechanism

A loop can fail to converge over a wrong mechanism. The review
question was "is this contract correct?" when the answer needed was "is this
the right mechanism?" Correctness review over a wrong mechanism has no stopping
point: every defect it finds is real, and every repair adds surface to a design
that should not exist. The exhibit is several rounds refining an
inline-restatement design this repository had already rejected, ending in
abandonment. The discriminator is cheap: has this repository already solved
this responsibility, and does the mechanism match it?

The razor's bounded search found that precedent inside ten minutes. The
failure was recognition, not retrieval.

### Completeness proved by decomposition, where the definition is the target

> **Recorded, not shaped.** This subsection is evidence captured for a later
> shaping pass. It is **out of scope** for any confirmed slice, it sizes
> nothing. Its derivability half has since shipped as rubric class 4's
> sub-text; the rest is unshaped. A reviewer of the change that
> added it should not treat it as a proposal, and should not review it as one.
> It was persisted here rather than held in a session so that it survives to be
> shaped. Owner decision, 2026-09-03.

An author decomposed a definition, then built machinery to prove the
decomposition covered it. The reported exhibit: verification split into six
lanes, then a contract module, a claim-exactly-once predicate, an exclusion map
and a two-layer path check, all to prove the split covers `make ci`. Roughly 32
of about 100 review findings were defects **in that proof machinery**. None was
a defect in the subject — remote verification — which was sound throughout.
(Figures as reported by the originating session; not measured here.)

This is adjacent to "Wrong mechanism" above but distinct from it, and the
difference is what makes it worth recording. There, the subject design is
wrong, so every real defect adds surface to something that should not exist.
Here the subject is **right**; what is wrong is a proof obligation the author
manufactured. `make ci` already *is* the definition of verified. Restating it as
six lanes creates a completeness claim that did not previously exist, cannot be
discharged, and generates findings that are all real and all beside the
point.

**What now catches it, and what still does not.** Rubric class 4 ships the
decidable half of this exhibit. Its other two homes are classes 1 and 6, which
this brief routes to prose above because neither has a decidable predicate, so
for this exhibit they arrive as guidance: `make ci` is the owner the obligation
was restated away from, and the exclusion map and predicate were authored
alongside the decomposition they validate.

**Why that may be wrong, and the part worth shaping.** This case does appear to
carry a decidable predicate, which would move it out of the prose-only region:
*is the set being enumerated already mechanically enumerable from a named
artifact?* For `make ci` the answer is decidable rather than a judgment, and by
two independent instruments in this repository: the `Makefile` declares
`ci: build-check lint-ruff lint-mypy test-after-build-check` on one line, and
`make -np` emits the same prerequisite list from make's own database without
parsing prose. The candidate rule is the one rubric class 4 now
states as its first clause.

Note the granularity trap before shaping this: `make ci` names four
prerequisites while the exhibit split into six lanes. That is not by itself a
defect — `build-check` fans out further, so a six-lane cut may be a legitimate
decomposition at a lower level. Class 4 carries the level-comparison clause
that keeps the predicate from firing on correct work; this is the exhibit that
made it necessary.

That is the same remedy § "Why no regenerator" already reaches for — *"what an
adopter needs is the derivation"* — applied to an enumeration whose completeness
is the claim rather than to a figure that decays. The principle is already in
this brief; its scope is narrower than the failure it needs to cover.

**Open, for the shaping pass:** whether the predicate survives contact with a
corpus, since "mechanically enumerable" is easy to assert and harder to bound.
It shipped inside class 4 rather than as a seventh class; whether it also
belongs in the policy-family registry is that registry owner's call.

### Exhibits behind rubric class 4

> **Shaped and shipped.** Both clauses of this rule are now rubric class 4's
> sub-text, and **the shipped rubric owns them**; this subsection keeps only the
> two exhibits that produced it. It is distinct from the numbered
> cut-before-adding razor elsewhere in this brief, which has rungs.

**Exhibit for the first clause, on hand-enumerating a derivable set.** See
§ "Completeness proved by decomposition", where proving a hand-written
enumeration covered its machine-readable source consumed about a third of a
review corpus.

**Exhibit for the second clause, on precision that is decoration.** Authoring
one delivery brief produced seven wrong counts — elicitation points, request
kinds, owed edges, capability briefs, brief statuses, the dispatch set,
dispatch sites — **twice inside the edit that was fixing a previous instance**.
Not one of the seven was load-bearing for a criterion. Guidance had been read
and acknowledged in the same session, which is the argument for enforcement
over restatement.

### The impacted-flow trace, as an authoring practice

> **Recorded, not shaped.** Out of scope for any confirmed slice. Owner
> decision, 2026-09-04.

The proposal: a spec or plan author maps the **flow the change lands in** — not
a diagram of the changes. The plan owns it, because the plan owns mechanism; the
spec's Assumptions cite only the edges its criteria depend on, with a source.

**Why it earns its place.** In one delivery brief's authoring, six substantive
design defects surfaced only at review rounds three through six. A flow trace
reaches all six at authoring time, because each is a property of the system
rather than of the artifact:

- three of four re-entry edges are instructed in a *different file* than the
  slice's declared owning surface — visible from "which file instructs each
  in-edge?"
- the controller *delegates* first drafting to another skill — one hop upstream
  of the traced state, and it moved a slice boundary
- the single exit edge carries **no guard** — visible from "what guards the only
  way out?"
- one in-edge exists in one engine mode only
- the drafting procedure writes a third artifact nobody had assigned
- the drafting procedure returns to a human repeatedly, which defeated a
  one-dispatch design

Two of the six forced an owner decision and one invalidated two prior slice
boundaries. Review found them late because a reviewer reads the artifact, not
the system.

**It catches nothing else.** It would not have caught any of that session's
citation or count errors, nor the altitude error itself. Flow tracing and review
are blind on opposite axes: review is cheap at "is this claim true" and dear at
"is this the right decomposition."

**Derive it; do not draw it** — the rule above applies to this practice first.
In this repository the engine's transition tables are data, so the relevant
neighbourhood is generated rather than authored: read the composed
`_TRANSITIONS_BY_MODE` in `loop-engine.py`, select the edges whose source or
destination is a named state, and report the mode each edge appears under.

**And the derivation itself has a trap that proves the point.** An earlier
revision of this section shipped a regex that matched each transition table
separately. That is wrong: `_CODE_TRANSITIONS` and `_SPEC_PLAN_TRANSITIONS` are
each built with `**_BOTH_TRANSITIONS`, so their shared edges are never literal
text inside their own blocks. Per-block matching finds **1** literal edge in the
spec-plan table when that mode actually carries eight — it would have missed
every in-edge the exhibit above depends on. Compose the spread before matching,
or read the composed mapping.

So: ship a deriver in the plan, never a rendered graph, which snapshots and
decays — and prove the deriver against a known neighbourhood before trusting it,
because a deriver that under-reports looks exactly like a small graph.

**Where no machine-readable source exists, the trace is an assumption, not a
fact.** A prose procedure can only be traced by hand, so its edges carry a
source line and a hedge. In the exhibit the human-return count could honestly be
stated only as a floor — "at least eight" — because each is a conditional
imperative in prose with no mechanical filter. Derived edges are facts; edges
traced from prose are assumptions. Keeping that distinction is what stops the
trace becoming one more thing reviewers litigate.

**Bound it before authoring it.** Without a stop rule "the impacted flow"
expands without limit. One candidate bound, sufficient for every defect above:
the one-hop neighbourhood of each state the spec names, plus the file that
instructs each edge.

**Then the plan walks its change DAG over the flow DAG.** The plan already has a
change DAG and does not need a new one: task `Depends on:` edges, computed by
`loop-cohort schedule`. It **fails** on a dependency cycle
(`loop-cohort.py:603-607`) but only **warns and reorders** on a
forward-reference (`loop-cohort.py:1385-1392`), so an ill-formed plan is
caught at PLAN only in the cycle case. Note `supervisor-mode.md` lines 13-15
states both as failing; that conflict is owed to that file's owner and is not
resolved here — an earlier draft of this paragraph restated its wording by
hand and inherited the error, which is this section's own subject.
Both graphs are therefore derived, and the walk is their join — mechanical, not
prose. It answers three questions no single-graph view can:

- **Coverage — does every impacted flow edge have an owning task?** An edge with
  no task is the defect where a slice's declared owning surface cannot implement
  it, found above only at review round three.
- **Order safety — does any task leave the flow broken when it completes?** A
  dispatch wired before the validation that bounds it is green per task and
  broken between tasks. Task-local `Done when:` cannot see this; only the walk
  can.
- **Reachability — is any authored task on no impacted edge?** Then either the
  flow trace is incomplete or the task belongs to a different slice. Both are
  worth knowing before the cut is confirmed.

Coverage and reachability are the two directions of the same join, and skipping
either leaves one silent: unowned edges ship broken, unreachable tasks widen the
slice. Neither the spec's criteria nor the plan's task list detects them alone,
which is why the walk belongs to the plan that owns both.

### A brief that pre-empts its own spec

> **Recorded, not shaped.** Out of scope for any confirmed slice; sizes nothing;
> changes no rubric class yet. Owner decision, 2026-09-03.

A brief defined the contract its slice's spec was going to define. The exhibit:
a delivery brief carried a controller-to-author contract — request kinds,
payloads, return states, validation timing — justified in its own words as
"stated here rather than left to the spec." Brief-level review then adjudicated
spec-level detail against a rubric that does not govern it, for **six rounds**,
while the six canonical Ready-gate fields had been satisfied since the first.
The brief doubled, 232 to 484 lines, and roughly half the growth was prose
defending earlier prose.

This is **class 1 at brief altitude** — an obligation authored where an owner
already exists, the spec being the owner of what done means. It is worth a
separate entry only because the tell is different: class 1's usual shape is
one obligation restated across several consumers, whereas here it is restated
*down a level*, into an artifact whose review rubric cannot evaluate it. The
brief-level control is the question rubric class 1 states, asked of a brief's
sections rather than a spec's; the rubric owns that question and the
counter-intuitive repair that goes with it.

### Presence-only gates

A readiness gate that checks presence cannot tell whether the next stage can
work. Its exhibit is this brief's own predecessor, which passed
seven review rounds while its first slice was unwritable, because the gate
verified that Outcome, In scope and Non-goals existed rather than that an
author could write from them. Acting on this belongs to
[`stage-input-readiness.md`](stage-input-readiness.md).
The abandoned spec was also authored with no brief and no workspace entry;
nothing objected for its whole life, and registering it mid-flight satisfied
the only detector that would have flagged it.

### Self-observed activation failure

A fifth, self-observed non-activation instance shows that artifact guidance
can be present through two routes and still lose every conflict.
`author-delivery-brief/SKILL.md:37` requires descriptive headings, short
resumable sections, one fact per sentence, no repeated summary, and at most one
load-bearing point per section. On 2026-09-02, these three briefs measured
1.4–1.6 load-bearing points per section; one predicate appeared three times in
one file; and this brief had grown from 3,622 to 4,746 words. The clause had no
oracle, preserving substance made adding safer than cutting, and the review
loop had no subtractive move because every finding was closed by writing.

### Authoring and reviewing this brief's own first deliverable

> **Observed 2026-09-04 to 2026-09-08.** Exhibits for the corpus above. The
> rules they bear on live in the rubric.

The A1 candidate went through repeated `adversarial-reviewer` rounds under
light mode's divergence checkpoint; the round-numbered artifacts are the count,
and this section does not restate it. Three things those rounds showed are new
to this corpus.

**A repair can instantiate the defect it repairs.** § "Corpus" published
percentiles under a predicate that, run literally, admitted fewer specs than it
claimed. The repair rewrote the predicate and introduced a different
non-reproducibility; a later round found the same class one level down, and the
section records the withdrawal. Two adjacent instances the same week: a guard
against verbatim overlap shipped at a threshold one word above the duplication
it existed to catch, and a measurement reported its result in classes when it
had sampled defects. Each passed a careful re-read by its author and failed the
first external check, with the governing rule in context every time. **This is
the corpus's first population of failures in *repairs to* contracts rather than
in contracts.**

**Shipping the rule did not make the author follow it.** Rubric class 4 is the
decay class, and the same session that shipped it let three separate figure sets
decay in the document that ships it — each caught by a review round, none by the
author, with the rule in context throughout. The rule was not wrong; it was
unactionable in four specific ways, all now repaired in class 4 itself: it gave
no way to tell a live figure from a frozen one, so effort went to dated
observations that cannot decay while a live count went stale; it accepted "dated
and instrumented" as sufficient, which is what each of the three stale sets
was; it named no stopping rule, so the answer to a stale figure was to measure
it again; and its tells reached measurements but not narration, which is how a
review-round tally sat stale across several rounds without looking like a
figure at all.

**What actually stopped it was a check, not the repair.** Two roster guards now
fail if a snapshot returns to the corpus section or a value returns to the bound
that reads it. That ordering is this corpus's oldest finding — prose that was
loaded and acknowledged fired never — and it applies to the strengthened rule
too: treat the class-4 revision as the cheaper half and the guards as the
binding half.

**A line-oriented search over wrapped prose returns confident wrong answers.**
Four times in one session, `grep` for a phrase spanning a line break reported
absent and produced a decision rather than an error — a clause declared never to
have existed, a landed repair declared unapplied, a duplicate count wrong, a
guard's calibration citing the wrong run length. Flatten whitespace before
matching. A prose rule saying "check the artifact" does not reach this, because
the author did check, with an instrument that lies quietly on wrapped text.

**Repair-induced findings are the signal the count hides.** Severity fell across
the rounds while the share of findings traceable to the previous round's repairs
did not, and the last two rounds each produced most of their blockers that way.
Two rounds were repaired from reviewer prose without adjudication, which the
gateway forbids and which the round-numbered artifacts record as raw so no later
read treats them as sustained. Two other rounds returned
`ADJUDICATION-INDETERMINATE` because a read-only adjudicator cannot reach
repository state; both closed on one guarded evidence retry, so budget for that
hop wherever a finding turns on repository state rather than file content.

## The rubric is a deliverable, not content here

The failure-point rubric is distilled from this repository's memory and its
`docs/knowledge/` topics. It is what the work produces, not what the brief
carries — so **this brief states no class's tell, move or repair.** It does
name a class's defining clause where an argument turns on it. The six classes,
their order, their tells, their moves and their repairs live in
`packs/core/.apm/skills/new-spec/references/spec-authoring-rubric.md`. Read them
there.

**What the brief keeps, and what is checked.** The arguments below cite classes
by number, with at most a few words identifying which one is meant — "class 4,
the decay class" — because a bare number is unreadable, and with a class's
defining clause where an exhibit turns on it. What they do not do is state a
class's tell, its move, or its repair. The checked half is narrow and worth
naming: a roster guard fails if this brief and the rubric share a verbatim run
of seven prose words or more, table delimiters excluded. A paraphrase passes it,
and so does a shorter run; the guard's own `ADMITTED_SIX_WORD_RUNS` records
which shorter runs are admitted, and is the one home of that set. So the rest is
authoring discipline rather than enforcement.

Earlier attempts to keep "just the names", "just the glosses" or "just the
exhibits" each went stale within a review round, because every edit to the
rubric falsified a sentence here that described it. Identifying words survive a
rubric edit; descriptions of a rule do not.

**A1 supplies family definitions; it does not register or enforce them.** The
registry surface belongs to
[`phase-scoped-policy-delivery.md`](phase-scoped-policy-delivery.md) and the
deterministic check to
[`policy-arrival-validator.md`](policy-arrival-validator.md). Without that
split A1 would silently own a registry and an enforcement path it does not
name.

**Classes 2, 4 and 5 ship as policy families; 1 and 6 stay prose.** The three
decidable ones become families in the registry owned by
[`cross-adapter-behavior-enforcement.md`](../intents/cross-adapter-behavior-enforcement.md),
delivered to the authoring agent for its phase and checked deterministically.
Classes 1 and 6 have no decidable predicate and remain authoring guidance. This
is a routing decision over the class numbers, and reads none of their text.

**That supplies A1's activation contract**, which prose could not: the
activation point is the phase gate, the measurement is the per-family verdict,
and the stated failure mode is the recorded block rate. **The altitude check
splits across that line** — one of its tells is decidable against the slice
table's own columns and the rest are not, so the family carries the decidable
one and the rubric keeps all of them as guidance.

**A family ships precise or advisory, never in between.** Applying an emphasis
density predicate to everything `docs/AGENTS.md` governs blocks 405 of 1,477
files, 27.4%, against a 0.4% per-family budget. A family that cannot be
calibrated is delivered as guidance and never blocks.

**For plan tasks:** name what to verify, not how. A bullet spelling out the
assertion, the fixture, and the expected message is pseudo-code — reviewed as
code while unable to run, and every detail in it is a claim the next round can
falsify.

## Satisfiability is tested late, not designed late

The LLD lives in `plan.md`, authored after the spec's criteria and locked after
the spec's gate — so criteria are committed before the design that must satisfy
them exists. That is late for exactly one thing: **satisfiability**. The
abandoned contract had a criterion no design could satisfy, and an
observability premise that was a design question never asked.

Hoisting the LLD earlier inverts the contract/strategy split, and the plan is
deliberately the document allowed to change. So: **widen `new-spec`'s existing
step 5a** — cheapest disconfirming evidence, one fixture or measurement or
read-only probe, uncommitted — so that **a criterion making a claim about live
behaviour gets its probe before the spec gate**, against the criterion's
satisfiability rather than the plan's mechanism.

### A4 firing predicate

That clause is A4's firing predicate. Step 5a today probes the *plan's*
load-bearing mechanism — `new-spec/SKILL.md` Procedure step 5a, "one throwaway
check that could disconfirm the plan's load-bearing mechanism" — and one probe
cannot cover an unbounded set of criteria. "A claim about live behaviour" is
what selects the criteria that get one.

[`stage-input-readiness.md`](stage-input-readiness.md)
§ "What nothing checks today" owns the step-5a-versus-routing-spike
distinction and its slicing consequence.

## The survey is a lean

This is not an owner decision. It lets a reviewer disagree with the
conclusion without re-deriving the evidence.

- **A worker guarantees retrieval, not recognition — and retrieval was never
  the failure.** The gain lands on the half that already worked.
- **Its scope is a landscape, not a verdict:** what exists in the area, what
  each component owns, which are reusable. Judging "is this an owner for the
  contract I am about to write" needs the contract, which the worker does not
  have; forced to judge, it returns confident wrong answers. Recognition stays
  with the author and becomes cheap because the inventory is organised for it.
- **Not the host's built-in explorer** — on ownership, not capability. Only
  Claude Code's `Explore` was inspectable, so no claim covers Codex, Cursor,
  Copilot, or Gemini. A host built-in is not ours to **instrument**, and
  delegating a rule to a component whose firing we cannot measure reintroduces
  the blindness the activation measurement exists to remove.
- **Its sources are role-scoped**, and only its *permission* behaviour is
  already owned. `packs/architect/.apm/skills/architect-design/references/knowledge-surfaces.md`
  governs detection by capability rather than product name, treating retrieved
  context as attributed and untrusted, and degrading visibly when no surface is
  usable. It does **not** govern which grounding technique to use — that is the
  open question below. That pack is also the warning: three role-scoped copies, two
  duplicating their common half.

### Repository grounding is a developed field, and this is where the survey competes

Naming the prior art matters because most of it optimises **retrieval**, and
this brief's own evidence says the failure was **recognition**. The classes,
roughly cheapest first:

| Class | Exemplars | What it returns |
| --- | --- | --- |
| Lexical / agentic search | ripgrep, glob; the search loop coding agents run | Exact matches, no index, no staleness |
| Symbol indexes | LSP, SCIP and LSIF, ctags | Definitions and references, not text matches |
| Repo maps / code graphs | aider's tree-sitter map with graph ranking | A whole-repo skeleton ranked into a context budget |
| Dense or hybrid chunk retrieval | embedding indexes, BM25 hybrids | High recall over prose and code, weak on ownership |
| Build and dependency graphs | Bazel and Buck targets, Nx project graphs, package manifests | Module boundaries, declared mechanically |
| Ownership declarations | `CODEOWNERS`, service catalogues such as Backstage | **Ownership, answered directly** |
| Agentic localization | Agentless's localize-then-repair, AutoCodeRover's search APIs, SWE-agent's file viewer | A ranked file set; localization is a dominant error source |

The first four are retrieval, and the razor's search already ran and already
returned the precedent, so they address the half that worked. **The last two
are the ones that bear on recognition**, because they make ownership a declared
fact rather than an inference — and this repository ships neither: there is no
`CODEOWNERS`, no service catalogue, and no target graph declaring module
ownership.

That reorders the options. A mechanical ownership declaration is cheaper than a
worker, is inspectable, and fails loudly when stale; a survey that reads an
undeclared tree infers ownership every time it runs. **Weigh adopting one
before admitting A5** — the razor's second rung asks for exactly this, and A5
is the addition it would screen.

### Code graphs

A code graph is not an ownership declaration, and the code-graph benchmark is
not this work. [`code-graph-review-benchmark.md`](../intents/code-graph-review-benchmark.md)
is a separate Draft intent asking whether graph-assisted exploration improves
**code-review** findings, measured by valid finding yield, false-positive rate,
and review time against repository-native exploration. Three reasons it stays
separate rather than folding in here: it is a review-time question, which this
brief's non-goals exclude; it explicitly does not authorize adopting a
code-graph provider; and in the table above, repo maps and code graphs return a
ranked skeleton while ownership declarations answer ownership directly. **So
adopting a code graph would not fire A5's kill condition** — that condition
needs a declaration that *records* an owner, not a retrieval surface that infers
one. The two share prior art and should not duplicate it: that intent carries
its own survey at
`docs/specs/work-loop-review-verdicts/notes/code-graph-code-review-effectiveness-survey.md`,
and this brief keeps the grounding-classes table.
- **Against a designer agent.** `plan.md`'s `## Design (LLD)` owns producing a
  design; `design-reviewer` in the architect pack owns critiquing one, reached
  by conditional routing with a named skip as `new-spec` already does for
  `design-review`. Only "is a draft criterion satisfiable by any design" is
  unowned — a probe, not a designer.
- **It has a prose budget on the other side of the ledger.** Some
  repository-anchoring prose in `work-loop` and `new-spec` stops needing to be
  carried there. Net that out rather than treating the worker as pure cost.
- **The survey and the probe cannot merge.** The survey runs before criteria
  exist, because its output shapes which to write; the probe runs after,
  because it needs something to test.

### Kill conditions

Each condition names the row it kills and the report line that decides it.

- **A5 dies** if M's verdict for **the repository-anchoring variant M1 selects**
  is *fired*. Repository anchoring is a **rule family, not a rule**: measured
  on 2026-09-02, at least `adapt-to-project`,
  `contract-acquisition`, `new-spec` and `work-loop` each carry their own
  normative anchoring span, plus `architect-design` in the architect pack, and
  each is normative only inside its own skill's trigger context. M1 must pick
  one variant and its artifact; this kill condition reads that one. If M1
  instead records repository anchoring as *not gradable*, **this condition never
  fires and A5 is decided by a named human at its confirmation gate** — it does
  not silently pass.
- **A5 also dies if this repository adopts a mechanical ownership
  declaration** — a `CODEOWNERS`, a service catalogue, or a target graph naming
  the owner of a surface. A declaration records ownership rather than judging
  it, which is why it is the cheaper option the razor's second rung screens A5
  against. Rejected: "a knowledge surface returns ownership directly", which is
  unfirable, because judging *responsibility* ownership needs the contract no
  retrieval surface has.
  **The decision sits at A5's confirmation gate, not at this brief's Ready
  gate** (owner decision, 2026-09-02). Verified absent from this repository on
  that date: no `CODEOWNERS` at the root or under `.github/`, no service
  catalogue, and no ownership-declaring target graph. A5 is gated after M
  regardless, so nothing is blocked by leaving it open — and adopting a
  root-level ownership declaration is a repository-wide change that belongs in
  its own decision, not settled inside a brief's readiness review.
- **A4 dies** if M's verdict for `new-spec` step 5a is *fired*: the widening
  exists to make a step activate that may already activate. A4's Gating cell is
  conditional in the same way A5's is. **This condition depends on M grading
  process provenance, not authored artifacts alone** (owner decision,
  2026-09-02): step 5a requires that the probe ran *before* review, stayed
  side-effect-free, and was not committed, and none of that is recoverable from
  an authored spec or plan. M's grading contract was widened to admit run and
  revision provenance so this verdict is obtainable; if M nevertheless records
  step 5a as *not gradable*, A4 is decided by a named human at its confirmation
  gate rather than passing by default.
- **A designer agent** becomes necessary only if one of the two existing owners
  does not cover its half — a finding about that owner, not grounds for a third
  agent.

## Proposed slices

None is confirmed and no spec is authored. Slice sizes are targets a spec
author writes to under § "Sizing discipline", and the AC ceiling is governed by
rubric class 5, which states how a count threshold is used and what it never
becomes.

| # | Slice | Owning surface | Verification | Guide | AC ceiling | Gating |
| --- | --- | --- | --- | --- | --- | --- |
| A1 | The failure-point rubric and the authoring instructions derived from it — **open; a candidate mechanism ships, see below** | `packs/core/.apm/skills/new-spec/references/spec-authoring-rubric.md`, wired from `packs/core/.apm/skills/new-spec/assets/spec.md` § Acceptance Criteria and from `new-spec/SKILL.md`'s acceptance-criteria step | an eval case in `new-spec/evals/` grading an authored criterion against a named rubric class | **still owed:** `guides/core/reference/acceptance-criteria-authoring.md` | 10 | after M reports, and after `phase-scoped-policy-delivery` and `policy-arrival-validator` |
| A3 | The delegation anchor | `packs/core/.apm/skills/new-spec/assets/plan.md`'s `Repository anchors` field | a plan authored with the field records whether an owner was found, and the recorded answer resolves | `guides/core/reference/spec-shape-and-lld.md` | 6 | after A1 |
| A4 | Widening `new-spec` step 5a | step 5a in `packs/core/.apm/skills/new-spec/SKILL.md` | an eval case proving a criterion claiming live behaviour gets a probe before the spec gate, and one not claiming it does not | `guides/core/how-to/plan-and-execute-non-trivial-work.md` § "Step 1 — Run `new-spec`" | 6 | after A1; **conditional** — dies if M's step-5a verdict is *fired*, and decided by a named human if that verdict is *not gradable* |
| A5 | The ownership survey — **a conditional candidate, not a sized slice** | named at confirmation | named at confirmation | named at confirmation | 10 | **conditional** — after M, and only if the kill conditions above do not fire |

### A rubric candidate exists, and A1 stays open

Owner instruction, 2026-09-04: build the rubric now, track it, and **do not let
it replace an existing slice**. So `new-spec` ships
`references/spec-authoring-rubric.md` as a **measured candidate for A1's
delivery mechanism, not as A1's discharge.** A1 remains an open slice, still
gated on the activation report and the two policy briefs; nothing below should
be read as satisfying that gating.

**The open question the candidate does not settle.** A rubric delivered as a
skill reference and read by the primary session is one of at least two ways to
put these classes in front of an author. The other is a dispatched authoring
agent that receives them cold, which
[`spec-author-agent.md`](spec-author-agent.md) S1 owns and which is cheap to
reach now that coding harnesses can invoke headless instances. **Which of the
two produces better contracts is unmeasured**, and a rubric-ablation result
cannot answer it, because ablating a reference measures the content while the
comparison is about the delivery route. Settling it needs S1's envelope to
exist. Until then the candidate is evidence about the classes, not a verdict
about where they belong — and S1's scope is unchanged, including its non-goal of
not changing review rubrics.

What shipping early costs, recorded rather than glossed:

- **The activation risk is unretired, and one of its two halves is now
  answered.** § "Assumptions / Risks" names shipping another unactivated rule as
  the most likely failure. All six classes have now been shown to fire
  (§ "Success metrics", 2026-09-08), on a record that section marks as not
  independently verifiable — so the withdrawal metric is satisfied on this
  session's evidence, and no class is a withdrawal candidate on it. What remains open is the other half:
  whether the classes shipped *as prose* change what an author writes. The
  ablation reaches two defects in two classes; the activation measurement owns
  the rest.
- **Classes 2, 4 and 5 shipped as prose, not as policy families.** The split
  in § "The rubric is a deliverable" routes them to a registry that does not
  exist yet. Nothing about the shipped file forecloses that; the registry's
  owners inherit three families whose definitions are now fixed in
  adopter-facing text.
- **The guide does not exist.** `guides/core/reference/acceptance-criteria-authoring.md`
  is still owed, so an adopter reads the rubric inside the skill and has no
  reference page for it. A1 cannot close while that is true.
- **Class 3 ships A4's substance while step 5a still probes the plan.** The
  rubric's class 3 points the pre-review probe at a criterion's
  *satisfiability*, which is what A4 exists to widen `new-spec` step 5a to do;
  step 5a itself still instructs a probe against the plan's load-bearing
  mechanism, so shipped guidance now carries two aims for one move. **A4 stays
  open** and keeps the step-5a surface, its live-behaviour firing predicate and
  its eval. The rubric adds no selector, which is tolerable only because its
  classes are worked in order and class 3's tells gate the move.
- **Six classes ship at a length the change's own evidence argues against.**
  The [ablation](../research/spec-authoring-rubric-ablation.md), which scored
  a paired arm-A/arm-B run over six pre-registered defects, found four of the
  six already reachable from shipped guidance — and it sampled only four of the
  six classes, never 1 or 5 — so the measured marginal value is two defects in
  two classes. Two of the four unflipped scores were taken against class 4 text
  that has since been rewritten, so they are provisional; the two that flipped,
  which carry the marginal-value claim, were not. and the
  commissioned survey records vendor guidance that an over-long instruction
  file gets half-ignored. The six ship whole anyway for one reason: the rubric
  is worked **in order**, stopping at the first class that explains a given
  defect — never at the first defect — so every class has to be present and in
  place for the ordering to mean anything.
  Replacing the four already-reachable classes with pointers would keep the
  ordering only by making the reader follow a pointer mid-sequence. Revisit if
  the activation report shows the later classes never firing.
- **The rounds did not reach clean.** Classified rather than counted, as
  § "Success metrics" prescribes: the later rounds' blockers were predominantly
  in the prose *around* the reference rather than in the reference itself, and
  mostly in this brief. Read that as evidence about this brief's coupling to the
  rubric, which the cut and its guard now bound, rather than as evidence about
  the reference. § "Authoring and reviewing this brief's own
  first deliverable" carries what the rounds showed.
- **The home is renamed.** `spec-authoring-rubric.md`, not
  `failure-point-rubric.md`. Same directory, same precedent — § "A1 home"
  still governs.

The rubric's own class 1 applies to this entry: it records state, and the
decision that produced it stays with the owner.

### Guide ownership

A1 ships a new guide. Measured 2026-09-02: **no adopter-facing Core guide owns
acceptance-criteria authoring.** `guides/core/reference/spec-shape-and-lld.md`
owns the `Shape:` field, durable outputs and the plan's LLD — it notes that UI
states and measurable NFRs rise to criteria but carries no criterion rubric — so
A1 cannot extend it. A3 belongs there because the `Repository anchors` field
lives in the plan that guide owns.

### A1 home

A1's home follows the precedent in the surface it extends. As of
2026-09-02, `packs/core/.apm/skills/new-spec/references/` already holds exactly
this artifact class — on that date its one file was `contract-types.md`, and
the rubric is the second — and
`assets/spec.md` § Acceptance Criteria is already the named owner of the
semantic-atomicity gate that rubric class 5 defers to, so the rubric lands
next to its precedent, and the surface that already governs criterion shape is
one of the two that reach it. `docs/knowledge/topics/` stores observations rather than
shipped guidance, so a rubric there would not reach adopters.

### Slice relationships

A1 and A3 share one guide, each extending its own section. The guide is
the secondary surface, not the primary one, so sharing it does not breach the
one-primary-surface bound; three slices editing three sections of one reference
page is not one slice.

- **A3 is the template field alone.** Rejected: pairing it with the repository-anchoring rule, which is a second surface in an unnamed home and breaches the one-surface bound. Whether repository-anchoring prose also has to move is A5's prose-budget
question, not A3's.

- **A1 keeps the rubric and its instructions together.** Two files, one
deliverable: the rubric with no instruction change is content nobody reads, and
the instruction change with no rubric has no source. Splitting them lands below
the over-splitting floor.

- **A3 and A4 are independent** and run in any order once A1 lands.

**A5 is deliberately not size-assessable yet, and that is a state rather than a
gap.** Its worker home, verification and guide are named at its confirmation
gate, because two kill conditions may retire it first: M's verdict for the
selected repository-anchoring variant, and this repository adopting a mechanical
ownership declaration. Sizing a slice that two named conditions may delete would
be work spent on a candidate, so the row records the conditionality instead of
inventing a surface. A reviewer should read A5 as a candidate; a spec author
should not attempt it before the gate. A2 is withdrawn and its number is not reused, so the identifiers cited elsewhere stay valid.

## Assumptions / Risks

- **This brief ships another unactivated rule.** The most likely failure, and
  the reason everything waits on the activation report. The withdrawal metric
  above is the guard.
- **The ownership survey ships, observably runs, and leaves recognition still
  failing.** Every kill condition above is a necessity condition; none covers
  "it ran and did not work". A survey can return a correct landscape the author
  still does not recognise the precedent in. Answer this before A5 is
  confirmed.
- **The rubric grows into doctrine on one instance.** The hypothesis is in
  `[backlog].open` with what would earn it.
- **The sizing band is screening evidence dressed as a bound.** The criteria
  count's evidence status is the § "Band" row's to state; whatever it says, the
  count should stall a contract for a conversation and never silently refuse
  one.

## Ready gaps (Draft only)

- **Settled — A1's second upstream is named.** Classes 2, 4 and 5 ship as
  policy families, so A1 waits on
  [`phase-scoped-policy-delivery.md`](phase-scoped-policy-delivery.md) and
  [`policy-arrival-validator.md`](policy-arrival-validator.md) as well as on M's
  report. A3, A4 and A5 inherit that through A1.
- **Open, but not a Ready blocker: the mechanical ownership declaration.** Its
  decision sits at A5's confirmation gate by owner decision, recorded with the
  evidence in § "The survey is a lean". A5 is gated after M, so no slice waits
  on it.
- **Carried, not closed: the "ran and did not work" assumption.** It is a Risks
  bullet above and must be answered before A5 is confirmed. Recorded here so
  the obligation is not lost between the brief and the slice cut.

## Rabbit holes

- **Do not mechanize a judgment.** "Is this criterion well-founded?" is not a
  predicate.
- **Do not let the rubric become a review checklist.** It is authoring
  guidance, and it states that bound itself in its opening lines.
- **Do not hardcode a percentile.** The band names the percentile; the reader
  runs § "Corpus"'s instrument for its value on the day they ask.

## Spec map

| Spec | Status |
| --- | --- |
|  |  |

## Provenance

- Source: repository origin. Distilled from this repository's memory, its
  `docs/knowledge/` topics, and one abandoned delivery attempt whose spec and
  plan are preserved at commit `e1bdde746`.
- Measurement of the shipped rubric, run 2026-09-04:
  [`spec-authoring-rubric-ablation.md`](../research/spec-authoring-rubric-ablation.md).
  A paired ablation over six pre-registered defects: two flip on the rubric's
  presence, four are reachable without it, and four of the six classes were
  sampled. It records its own length confound and n.
- Prior-art basis, commissioned 2026-09-04 and discharging the desk-research
  item this brief owed:
  [`spec-authoring-quality-survey.md`](../research/spec-authoring-quality-survey.md).
  It supplies the class-to-frame mapping in § "What actually works, and what
  does not", the
  constraint-count and localization evidence in § "Band", and the external-signal
  effect size in § "External binding".
- Promoted on 2026-09-02 from a shaping intent of the same slug, added at
  `082285e73` and removed by that promotion; it was itself split out of
  [`work-loop-next-action.md`](work-loop-next-action.md).
- **Split on 2026-09-02 at commit `5ff0d3b19`**, where this brief had reached
  3,622 words against a 2,619-word precedent. The activation measurement moved
  to
  [`guidance-activation-measurement.md`](guidance-activation-measurement.md)
  and stage-handoff readiness to
  [`stage-input-readiness.md`](stage-input-readiness.md). This file kept the
  slug because two artifacts outside the split's scope link to it by path, and
  it retains the findings corpus all three cite.
