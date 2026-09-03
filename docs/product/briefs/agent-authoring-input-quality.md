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
11,258 words** — above the 96th percentile on criteria and within 3% of the
longest spec ever written here. Six of its criteria ran over 150 words, the
longest at 704. Eleven review rounds, no convergence, abandonment. Sizing is a
lever on this brief's outcome, not a style preference.

### Altitude precedes size

**Check the artifact's altitude before applying any bound below.** Every bound
in the band measures a property *within* an artifact. None of them asks whether
this is the right artifact, and an altitude mismatch is the one sizing failure
that trimming cannot repair — the repair is to re-home the work.

The recognized altitudes run `product-vision > product-strategy > capability >
feature`, and `decompose-intent` produces the levels beneath whichever is
chosen. This repository carries 28 intents against 8 briefs, tagged 20
`feature`, 6 `capability`, and 1 `product-strategy`. A delivery brief sits at
capability altitude with feature-level slices beneath it.

**Three tells that an artifact is above its altitude**, each cheaper to check
than any percentile:

- it proposes no slice a spec author could confirm, and the missing input is a
  decision rather than a detail;
- it carries a design position, an evidence base, an inventory, or a governance
  concern, rather than citing one;
- it changes the gating of its siblings, which a peer cannot do.

The exhibit is this brief's own sibling set. An artifact authored on
2026-09-02 to hold cross-adapter behavior enforcement reached 3,573 words as a
delivery brief and showed all three tells. The band would have reported it as
oversized, which was the symptom; the defect was product-strategy content in a
capability container, and the repair was re-homing it as an intent rather than
cutting it.

This is the altitude analogue of rubric category 5. A criterion that is too big
is cut; an artifact at the wrong altitude is moved.

### Corpus

The corpus has 416 specs, measured 2026-09-02. Its predicate, which the derivation states rather than re-derives: `docs/specs/*/spec.md` at exactly one
directory level, whose `- **Status:**` reduces to the leading token `Shipped`
once an annotation (`Shipped (2026-05-26)`) is stripped; a criterion is a
checkbox bullet under `## Acceptance Criteria`, since roughly half the corpus
labels them `**ACn —**` and half does not. Criteria per spec: p25 9, median 12,
p75 18, p90 28, max 104. Words per spec: p25 1,027, median 1,599, p75 2,392,
p90 3,969, max 11,569.

### Band

Each bound carries its origin; a bound without one cannot be
argued with.

| Dimension | Bound | Origin |
| --- | --- | --- |
| Owning surfaces | one primary surface per slice | Measured, not repo-local: 1 file → 95% resolution, 2 → 42% (SWE-bench Verified, Ganhotra 2025). |
| Criteria per spec | ceiling of 10, **never a floor** | **Screening only.** Practitioner ceiling ~10. No causal evidence exists in the literature, and this corpus records scope but not outcome, so no percentile of it corroborates a ceiling. A slice with fewer genuine criteria ships with fewer. |
| Criterion size | **not a word budget.** The gate is semantic atomicity, owned by `packs/core/.apm/skills/new-spec/assets/spec.md` § Acceptance Criteria — the conjunction/substitution test and worked examples E1–E5. Length only *orders* criteria for that test, longest first. | Hard AC word budgets are already rejected here: `docs/specs/shaping-review-contracts/spec.md` ships it as a ticked criterion, RFC-0099 states "no hard word budget is added", and `new-spec` SKILL.md:505 makes shaping review reject one. The length signal is real but is a sampler, not a bound: RFC-0098 took 16 rounds with ~60 findings concentrated in its three longest criteria (267–365 words) while its median 86-word criteria were quiet, and across 6,411 shipped criteria here p90 is 101 words and p96 is 162. |
| Spec body | ≤1,599 words; past 2,392 needs a stated reason | Measured, repo-local: the corpus median and p75. |
| Human-equivalent duration | under one hour | Measured: R² = 0.83 against success, ~1 hour ≈ 50% (METR 2025). |
| Floor | never below one surface plus its verification and its guide | Measured: cutting 8,500 → 2,100 tokens per step raised turns-to-solve from 4.0 to 14.0 (Augment 2025). **Smaller is not safer.** |

### Limit interaction

As `assets/spec.md` requires of any quantity
carrying two: both are reachable, because 10 criteria at the corpus median of
35 words each is ~350 words against a 1,599-word body. Criterion size is not a
limit, so it can neither dominate nor be dominated.

### Corpus limits

Files changed per spec is not obtainable — no spec-to-PR linkage, and slug-grep
over-matches badly — so **no files-changed figure is quoted for this
repository**; the surfaces bound is imported from SWE-bench. Nothing records
review rounds per spec, so the corpus measures scope but not outcome. Nothing
establishes a criteria *floor*.

### Why no regenerator

Rejected: a regenerator slice. Rubric category 4 below is "the criterion decays
— exact counts over a growing corpus", and every figure here is a percentile of
416 specs measured 2026-09-02. Decay is real but cheap to answer: two of the six
rows are repo-derived percentiles, the rest are imported measurements, the corpus
grows slowly, and a hand measurement is one command. The criteria ceiling is
screening-only with no causal evidence behind it, so a stall threshold needs an
order of magnitude rather than a maintained script.

What an adopter needs is the **derivation**, which the guidance carries: the
named glob, the status predicate, and the percentile. Shipping our percentiles
as numbers would be wrong for every adopter on day one; shipping the derivation
is right for each. The figures here are dated evidence, refreshed by hand, and a
slice sized against them cites that date.

### Corpus exclusion

This brief does not grade its own sizing: an artifact measuring itself is
rubric category 6, and the exculpation has to be checkable or it is that same
defect. What happened: the percentiles were produced on 2026-09-02 by a
throwaway instrument outside this brief, which first reproduced every figure
the owner supplied independently. **The corpus-exclusion rule travels with the derivation:** A1, A3, A4 and A5's
own specs are excluded from any recomputation, or the measurement grades specs
written to the band it derives from them.

## What actually works, and what does not

Three findings, and each should shape every deliverable.
[`stage-input-readiness.md`](stage-input-readiness.md) cites this section by
name rather than restating it;
[`guidance-activation-measurement.md`](guidance-activation-measurement.md)
cites this findings corpus rather than restating its exhibits.

### External binding

A rule's value is whether it binds to something outside the document. Across
the eleven review rounds at `e1bdde746`, every mechanism
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

## The rubric is a deliverable, not content here

The failure-point rubric is distilled from this repository's memory and its
`docs/knowledge/` topics. It is what the work produces, not what the brief
carries. Its categories, in the order they matter:

1. **The design should have delegated** — an obligation restated per consumer,
   where an owner already exists. Precedes every other shape, because no
   criterion craft rescues it. Its counter-intuitive repair: shortening or
   single-homing a long restatement is the *wrong* fix.
2. **The criterion cannot fail.**
3. **The criterion is unsatisfiable or contradicts a sibling.**
4. **The criterion decays** — exact counts over a growing corpus, line
   citations in portable artifacts, figures derived from other figures.
5. **The criterion is too big** — the band above is what mechanizes this one.
6. **The property is not mechanizable** — a gate over a judgment, or an
   artifact measuring itself.

**A1 supplies family definitions; it does not register or enforce them.** The
registry surface belongs to
[`phase-scoped-policy-delivery.md`](phase-scoped-policy-delivery.md) and the
deterministic check to
[`policy-arrival-validator.md`](policy-arrival-validator.md). A1's own surfaces
stay the rubric and its one consumer, so its slice remains one primary surface;
without that split A1 would silently own a registry and an enforcement path it
does not name.

**Categories 2, 4 and 5 ship as policy families; 1 and 6 stay prose.** The
checkable ones — a criterion that cannot fail, a criterion that decays on exact
counts, a criterion that is too big — become families in the registry owned by
[`cross-adapter-behavior-enforcement.md`](../intents/cross-adapter-behavior-enforcement.md),
delivered to the authoring agent for its phase and checked deterministically.
Category 1 (the design should have delegated) and category 6 (the property is
not mechanizable) have no decidable predicate and remain authoring guidance.

**That supplies A1's activation contract**, which prose could not: the
activation point is the phase gate, the measurement is the per-family verdict,
and the stated failure mode is the recorded block rate. **The altitude check is
one of these families** — the tell "carries a design position or an inventory
rather than citing one" is not decidable, but "proposes no slice a spec author
could confirm" is, against the slice table's own columns.

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

That clause is A4's firing predicate. Step 5a
today probes the *plan's* load-bearing mechanism
(`packs/core/.apm/skills/new-spec/SKILL.md:475`), and one probe cannot cover an
unbounded set of criteria. "A claim about live behaviour" is what selects the
criteria that get one.

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
author writes to under § "Sizing discipline". **The AC ceiling is a ceiling
and a stall threshold, never a floor** — a slice with fewer genuine criteria
ships with fewer.

| # | Slice | Owning surface | Verification | Guide | AC ceiling | Gating |
| --- | --- | --- | --- | --- | --- | --- |
| A1 | The failure-point rubric and the authoring instructions derived from it | `packs/core/.apm/skills/new-spec/references/failure-point-rubric.md`, consumed by `packs/core/.apm/skills/new-spec/assets/spec.md` § Acceptance Criteria | an eval case in `new-spec/evals/` grading an authored criterion against a named rubric category | **new** `guides/core/reference/acceptance-criteria-authoring.md` | 10 | after M reports, and after `phase-scoped-policy-delivery` and `policy-arrival-validator` |
| A3 | The delegation anchor | `packs/core/.apm/skills/new-spec/assets/plan.md`'s `Repository anchors` field | a plan authored with the field records whether an owner was found, and the recorded answer resolves | `guides/core/reference/spec-shape-and-lld.md` | 6 | after A1 |
| A4 | Widening `new-spec` step 5a | step 5a in `packs/core/.apm/skills/new-spec/SKILL.md` | an eval case proving a criterion claiming live behaviour gets a probe before the spec gate, and one not claiming it does not | `guides/core/how-to/plan-and-execute-non-trivial-work.md` § "Step 1 — Run `new-spec`" | 6 | after A1; **conditional** — dies if M's step-5a verdict is *fired*, and decided by a named human if that verdict is *not gradable* |
| A5 | The ownership survey — **a conditional candidate, not a sized slice** | named at confirmation | named at confirmation | named at confirmation | 10 | **conditional** — after M, and only if the kill conditions above do not fire |

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
this artifact class — its only current file is `contract-types.md` — and
`assets/spec.md` § Acceptance Criteria is already the named owner of the
semantic-atomicity gate that rubric category 5 defers to, so the rubric lands
next to its precedent and its one consumer is the file that already governs
criterion shape. `docs/knowledge/topics/` stores observations rather than
shipped guidance, so a rubric there would not reach adopters.

### Slice relationships

A1 and A3 share one guide, each extending its own section. The guide is
the secondary surface, not the primary one, so sharing it does not breach the
one-primary-surface bound; three slices editing three sections of one reference
page is not one slice.

- **A3 is the template field alone.** Rejected: pairing it with the repository-anchoring rule, which is a second surface in an unnamed home and breaches the one-surface bound. Whether that rule's prose also has to move is A5's prose-budget question. Whether repository-anchoring prose also has
to move is A5's prose-budget question, not A3's.

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
  count has no causal evidence behind it. It should stall a contract for a
  conversation, never silently refuse one.

## Ready gaps (Draft only)

- **Settled — A1's second upstream is named.** Categories 2, 4 and 5 ship as
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
  guidance. Handed to reviewers it becomes a source of nits, which is the
  problem it exists to reduce.
- **Do not hardcode a percentile.** The band is a snapshot; the check
  recomputes it.

## Spec map

| Spec | Status |
| --- | --- |
|  |  |

## Provenance

- Source: repository origin. Distilled from this repository's memory, its
  `docs/knowledge/` topics, and one abandoned delivery attempt whose spec and
  plan are preserved at commit `e1bdde746`.
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
