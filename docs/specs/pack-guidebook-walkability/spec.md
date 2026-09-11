# Spec: pack guidebook walkability

- **Status:** Implementing <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** none
- **Brief:** docs/product/briefs/sdlc-guide-uplift-and-learning-paths.md
- **Discovery:** none
- **Contract:** none
- **Shape:** mixed

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

A team can find the four-discipline route today and cannot execute it. Slice S6
made it discoverable. What is missing is a **guidebook**: something a first-time
team walks, stage by stage, that tells them what to type, what comes back, what
they decide, what they now hold, and what to run next.

Measured on 2026-09-11 across the five packs a team needs to get from an idea to
a merged change — `desk-research`, `product-strategy`, `experience-design`,
`product-engineering`, `core`:

- **29 of 74 published skills are named nowhere in their own pack's journey.**
  `experience-design` names 10 of 20, `core` 8 of 18, `product-engineering`
  6 of 15.
- Across their 42 how-to and tutorial guides, **2 carry a literal prompt, a
  worked input, a sample output and a stated outcome together.**
  `experience-design` has 2 guides for 20 skills, and neither shows a prompt or
  an output.
- **6 of 74 skills name what to run next.** `experience-design` 0 of 20,
  `product-strategy` 0 of 9, `core` 0 of 18.

So the pack that should teach sequencing cannot teach its own use, and the
corpus is quadrant-complete with no usable path through it — a failure mode the
practitioner literature names and, as far as the survey behind this spec could
establish, has never documented a case of.

**This slice makes each pack's journey walkable as a guidebook.** It does that
by fixing a step contract, enforcing it mechanically, and building an ordered
guidebook per pack whose steps are that pack's journey stages.

### The guidebook step contract

Derived in
[`docs/product/research/workflow-guidebooks-survey.md`](../../product/research/workflow-guidebooks-survey.md),
which grounds each row in cited practitioner evidence and records what the
evidence does *not* support.

| # | Every guidebook step carries |
| --: | --- |
| 1 | Where you are — the sequence, with this step marked, in the page body |
| 2 | What you must already hold, and what skipping it costs |
| 3 | What you type — a literal utterance |
| 4 | What comes back — the agent's turn, attributed and separate from your input |
| 5 | That the output varies, **stated at this step and not once up front** |
| 6 | Where you decide — the human gate, or an explicit statement that this step has none |
| 7 | How to tell it worked — **the judgement a machine cannot make**, never a restatement of the request and never a structural check the lint already performs |
| 8 | What to do when it does not — **a named decision**: fix locally, re-prompt with the failing case, discard, step back, or escalate. Fullest at a declared decision gate |
| 9 | What you now hold — the deliverable named, **with its path, and any templated segment marked as templated** |
| 10 | What to expect inside it — **the expected heading outline**, with its source declared. Verified against the skill's template asset or a real artifact **where one exists**; where none does, the obligation is presence plus declared authorship and nothing verifies correctness. No embedded sample |
| 11 | What to run next — named and linked |
| 12 | **Any concept the step depends on** — named, and linked to where it is explained. Authored bounded, in a sentence or two plus a link out, only where no explanation exists |

**What actually exists to project from, measured per stage.** An earlier draft
of this spec claimed rows 3, 4, 6 and 9 already exist in the journey stages.
That is true of `experience-design` and false corpus-wide:

| Pack | stages | carry an utterance | carry a decision gate |
| --- | --: | --: | --: |
| `desk-research` | 3 | 1 | 2 |
| `product-strategy` | 4 | 3 | 3 |
| `experience-design` | 5 | 5 | 3 |
| `product-engineering` | 6 | 2 | 3 |
| `core` | 7 | 2 | 5 |
| **total** | **25** | **13** | **14** |

Four stages carry neither. `contract.youType` exists for every pack but is
**one utterance per pack, not one per stage**, so it cannot supply row 3 at
step granularity.

So every projected obligation needs a **source ladder with a stated fallback**,
and the absence of a source must be representable rather than silent — silence
currently means both "this step has no gate" and "nobody recorded one". The
ladders are fixed here and AC-0009 checks them:

| Row | First source | Fallback | If none |
| --- | --- | --- | --- |
| 3 utterance | the stage's own `Type …` line | the named skill's invocation phrasing in its `description` | authored, and recorded as authored |
| 4 response | the stage's fenced sample | — | authored, and recorded as authored |
| 6 decision | the stage's `You decide` line | — | the step states **no decision gate at this step** |
| 9 path | the named skill's `SKILL.md` | the stage's `Output` line | authored, and recorded as authored |
| 10 outline | the named skill's template asset | a real committed artifact of that type | authored against what the skill writes, and recorded as authored |

**Each row's standing in the evidence is labelled per row, because the survey's
confidence varies and a contract presenting every row as equally evidence-backed
converts a coherence choice into an effectiveness claim.**

| Row | Standing |
| --: | --- |
| 1 | House choice. Page-body primacy is `[moderate]`, but the sequence-map remedy has no controlled evidence. |
| 2 | `[moderate]` — per-step prerequisite gates, and the mislabelled-optional failure. |
| 3 | `[high]` — an utterance example was a publication requirement on a major skill platform. |
| 4 | `[high]` — a prompt without a response leaves success indistinguishable from error. |
| 5 | **Split.** Its *presence at each step* is `[high]`: a single disclaimer does not raise verification intensity while repetition does. Its *wording* is a house choice — no evidence exists on which phrasing calibrates a reader. |
| 6 | `[moderate]` — three conventions exist for marking an approval point and none is a standard; the explicit-absence rule is a house choice closing the silence ambiguity. |
| 7 | `[high]` on excluding machine-checkable items, from peer-reviewed automation-complacency work; `[moderate]` on plausibility-testing failure. |
| 8 | `[moderate]` — a review with no failure path causes approval; the inspection tradition's rework loop is older and stronger. |
| 9 | `[moderate]` — naming an artifact without its location is a named anti-pattern, and templated-path notation is `[high]`. |
| 10 | **Split.** The two-channel requirement is `[high]`. The outline-against-source mechanic is a house translation for a versioned repository. **Its authored fallback is a house choice and a known limitation**: where a skill declares no shape, nothing independent verifies the outline is right, and the contract says so rather than implying verification it does not perform. |
| 11 | House choice. The pinball anti-pattern is documented; the next-step link has no controlled evidence behind it. |
| 12 | **Split.** Linking rather than inlining is `[moderate]`, and the content-drift anti-pattern it avoids is `[high]`. Authoring a bounded explanation where none exists is a house choice — no surveyed source addresses an undocumented concept, because those corpora assume the conceptual material exists. |

### Why the guidebook is a guide, not a journey edit

The guidebook lives in `guides/<pack>/`, ordered by the `order:` frontmatter the
sidebar generator already consumes at `tools/build-site.py:872`. It projects its
prompts and agent responses verbatim from the owning `JOURNEY.md` stage rather
than restating them, so drift is a test failure rather than a hope — drift is
the top runbook anti-pattern in the cited evidence. No file under `packs/**`
changes, so this is not a released pack change.

### The walk's surfaces still lie, and that travels with this slice

Separately measured and independently verified against the packs' own Shipped
specs: the claim that each discipline hands a named artifact to the next is
false. `product-engineering` ends at a decision brief and hands out to
`work-loop`; `experience-design`'s upstream inputs are optional by a Shipped
guarantee; `product-strategy` forks to both downstream packs. The evidence and
the owner decision are in
[`notes/walk-premise-correction.md`](notes/walk-premise-correction.md). A
guidebook built over a false spine would teach the false spine, so the
correction is carried here rather than deferred.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| User-facing promise | Applicable — the guidebooks are what a team walks | `guides/<pack>/` for the five packs, ordered by `order:` | `author-product-docs` conventions | Each guidebook's steps match its journey's stages in count and order, and every step satisfies the contract | The lint passes over all five |
| Current product truth | Applicable — the contract governs every future guidebook step | `guides/AGENTS.md`, the scoped guidance for the tree the contract applies to | This spec's owner | It enumerates its obligations by identifier, names its judgement kinds and its prohibited-claim vocabulary, and cites the survey for why each obligation exists | No new document and no new bucket: the rule-lookup walk already obliges an author to read this file, and `docs/CONVENTIONS.md` stays untouched because it is a pack-seed projection |
| Interface compatibility | Applicable — the slice ships a checker other packs will be held to | `tools/lint-guidebook-steps.py` and its `--help` | This spec's owner | `--help` names every obligation it checks, its flags, and what each exit code means | An adopter learns every check and exit code from `--help` alone |
| Decision rationale | Applicable — the contract is a house choice grounded in external evidence | `docs/product/research/workflow-guidebooks-survey.md` | This spec's owner | Each contract row traces to a cited finding; rows resting on weak evidence say so | Survey states the confidence behind every row and its known unknowns |
| Decision rationale | Applicable — an owner decision reversed the inherited walk premise | [`notes/walk-premise-correction.md`](notes/walk-premise-correction.md) and this plan's `## Changelog` | This spec's owner | The premise note states its evidence and authority; each delivery decision is dated | No owner decision is discoverable only from a commit message |
| Reusable learning | Applicable — the mutation proofs are a recorded exercise | `notes/verification-ledger.md` | This spec's owner | Every guard's mutation applied, observed red, restored by editing | Ledger records each mutation with its observed failure |
| Current product truth | Applicable — the brief tracks slice delivery, and this slice carves three pages out of two sibling specs, partly delivers one intent, and takes scope from another | the brief, the three sibling specs, `skill-sequence-wayfinding`, `experience-design-delivery-packet`, and the four bounded artifacts, all listed in [`notes/ownership-consolidation.md`](notes/ownership-consolidation.md) | `lint-brief-coverage` roll-up | The brief's Spec map cell is `<auto>`; every artifact in the ledger carries its own record | Roll-up names this spec; the ledger and the records agree in both directions |
| Release history | **Not applicable** | — | — | — | No `packs/**` source changes, so not a released pack change |

## Boundaries

### Always do

- Link to an explanation rather than absorbing it. Inlining explanation into a
  step is the content-drift anti-pattern, and a bounded explanation is admitted
  only where nothing exists to link to.
- Take every projected value from the highest rung of its ladder that exists —
  the owning `JOURNEY.md` stage, then the owning `SKILL.md`, then authored — and
  **record which rung it came from**. Authoring is permitted only at the bottom
  rung, only where no higher rung exists, and only with the rung recorded: 13 of
  25 stages carry an utterance and 14 a gate, so a rule forbidding authorship
  outright would forbid the guidebook. What is forbidden is authoring a value
  while a higher rung exists, or authoring one without recording it.
- Attribute the agent's turn separately from the reader's input in every sample.
- State that output varies wherever a sample response appears.
- Run `make site-build` before reading any assertion over built output.

### Ask first

- Adding a sixth pack, or changing which five are in scope.
- Any change to `packs/**`, which would make this a released pack change.
- Changing the contract's obligation set after the lint ships, because every
  guidebook is then held to it.

### Never do

- Claim on any surface that a guidebook improves adoption, completion, task
  success or time to first value. The survey establishes that the completion
  figures in this area are unsourced or single-vendor, and the
  install-to-first-value probe at
  `docs/specs/claude-apps-route-docs/notes/install-to-first-value-probe.md` is
  prepared and unrun.
- Mark a step's input optional without saying what skipping it costs. A false
  "optional" is a documented single-point failure.
- Present a sample agent response as deterministic.
- Describe the Claude-plugin and Agent Plugins 1.0.0 routes as equivalent;
  three of these packs ship agents and are refused on the second route.
- Edit `web/src/content/journeys/*.md`, which are generated and carry
  `generated: true`.
- Add an image to a guide; the projector rewrites image paths and copies no
  assets, so none renders on both GitHub and the docs site.
- Edit `site.toml` or its `[[guide_groups]]`; the navigation model belongs to
  `cohort-orientation-surfaces`, and a header change is "Ask first" under
  Shipped `docs/specs/site-shared-chrome/spec.md`.

## Testing Strategy

`GB` = `tools/test_lint_guidebook_steps.py`, new and repository-level; it reads
the convention, the guide markdown, and the five packs' `JOURNEY.md` and
`SKILL.md` sources, so it needs no build and cannot skip silently.

- **The contract's normative statement and its obligation set (AC-0001):**
  goal-based check over `guides/AGENTS.md`, on `GB`. The observation is
  structural and its parts fail independently: the section exists; it carries a
  normative statement binding every step; it enumerates obligations by
  identifier with no duplicate; its judgement-kinds closed set overlaps the
  obligation identifiers nowhere; and it declares its prohibited vocabulary.

  **Amended 2026-09-11 during T1.** The earlier wording had this oracle compare
  the identifiers "against the spec's table". That is not implementable — the
  spec's obligation table is numbered and carries no identifiers — and coupling
  it to the spec would have made a frozen document the runtime oracle for a
  living contract. The contract's agreement with the **lint** is AC-0003's, and
  that is where the drift risk actually sits. Evidence:
  [`notes/verification-ledger.md`](notes/verification-ledger.md).
- **The lint's verdict, its checker coverage, and the machine/human boundary
  (AC-0002, AC-0003, AC-0014):** TDD on `GB`. Each check is a function over a
  fixture step, so the cases compress into assertions. AC-0003 reads the
  obligation identifiers **out of the convention**, never out of the lint's own
  registry, so an obligation added to the contract without a check reds; a guard
  reading its own registry could not fail. AC-0014 is enforceable only because
  the two obligation classes carry distinct structured forms — without that the
  boundary would be prose with no oracle.
- **Guidebook shape — step count, order and stage identity (AC-0004):** TDD on
  `GB`, a function over each guidebook's frontmatter and its pack's `JOURNEY.md`.
- **The lint over real content (AC-0005):** goal-based check — the shipped lint
  run over all five guidebooks, exit 0. Distinct from AC-0002, which is the
  lint's behaviour on a fixture that isolates one obligation: a lint that failed
  without naming the obligation would satisfy AC-0005 and fail AC-0002.
- **Per-skill obligations and skill reach (AC-0015, AC-0008):** TDD on `GB`.
  AC-0015 walks every skill each step names and asserts that skill's own
  utterance, path and outline are present; AC-0008 is a set difference between
  the pack's published skills and the skills its steps name. They fail on
  different inputs — a step naming every skill with one shared utterance
  satisfies AC-0008 and fails AC-0015.
- **Projection ladders (AC-0006):** TDD on `GB`. For each projected value the
  oracle walks that row's ladder in order and requires either a source match or
  a recorded fallback, so an invented value with no recorded fallback reds.
- **Turn attribution (AC-0007):** TDD on `GB`, over each step's sample block.
- **Concept resolution (AC-0022):** TDD on `GB`. For each concept a step names
  as required, the oracle resolves its link within the tree, or accepts a
  bounded explanation on the step. It decides *resolution*, never sufficiency —
  a step silently assuming a concept is invisible to it, which is why the cold
  read carries that half.
- **The guides hub — corrected claims, placement and selection axis (AC-0009,
  AC-0010, AC-0018, AC-0020):** TDD on `GB`, over `guides/README.md`'s P2 and
  P2b spans. AC-0020's oracle is a pinned-axis check: P2b's condition names
  which disciplines the work needs, and neither span states the problem-clarity
  condition. It does not compare the spans for a shared term, because two
  conditions can select on the same thing while sharing no word.
- **The stage definition (AC-0019):** goal-based check over built output in
  `web/src/test/rendered-output.test.ts`, whose `AC2 — five stages in contract
  order` case at line 1183 implements a stage as a `P<n>` heading with a bare
  number and so deliberately excludes `P<n>b`. Named separately because it is a
  different file from the rest of the inherited set.
- **The journeys index — corrected group body, group signatures and onward
  route (AC-0011, AC-0016, AC-0017):** goal-based check over built output in
  `web/src/test/FourDisciplineSequence.test.ts` after `make site-build`, because
  `web/AGENTS.md` forbids observing an invented source seam. These three cases
  exist and pass today; each is re-derived by the mutation recorded against it
  in the plan before it counts as evidence, because three assertions in that
  file were shown after S6 shipped to be unable to fail.
- **The cold read (AC-0021):** visual / manual QA, **once per pack**. A fresh
  session is given only the rendered pages and answers the seven questions per
  step — the five execution questions plus the two semantic ones, on
  outcome-claim phrasing and on judgement checks a tool could perform. Its
  verdict is read by a human from the recorded answers. No mechanical proxy
  substitutes: those two questions are the residue AC-0009, AC-0013, AC-0014 and
  AC-0020 do not reach, and this is their only observer. The criterion is also
  what stops a recorded defect being deferred past the gate it guards.
- **Ownership consolidation (AC-0012):** goal-based check on `GB` over **three**
  sets: the eligible target universe derived from the three siblings'
  accepted-base ledgers, this ledger's rows, and the reciprocal records. All
  three must agree. Two-set equality between the ledger and the records is
  explicitly insufficient and was the earlier oracle — a target omitted from
  both sides satisfies it while the scope disappears from both slices.
- **The no-outcome-claim prohibition (AC-0013):** goal-based check at repository
  level over every surface this slice writes.
- **Publication and navigation:** not a criterion.
  `tools/validate_guides.py`, `tools/lint-guide-titles.py`,
  `tools/check-guide-index.py` and the derived inventory already enforce it and
  run in `make build-check`.
- **The pack-source prohibition:** goal-based check at finish —
  `git diff -- packs/ web/src/content/journeys/` is empty.

## Acceptance Criteria

Identifiers are opaque and append-only: AC-0001 to AC-0013 keep the meanings
they were assigned, and the obligations round 1 surfaced were appended as
AC-0014 to AC-0021 rather than renumbered into place.

- [ ] **AC-0001.** `guides/AGENTS.md` carries the guidebook step contract: a
      normative statement that it governs every guidebook step, its obligations
      enumerated by identifier, its closed set of judgement kinds, and its
      prohibited-claim vocabulary. So a step author and a reviewer read the same
      list, and the list is binding rather than merely present. Both halves are
      checked: identifiers without the normative statement, and the statement
      without the identifiers, each fail.
- [ ] **AC-0002.** `tools/lint-guidebook-steps.py` fails a step missing any
      contract obligation, and its report names which obligation is missing on
      which step, so a failure is actionable without re-reading the contract.
- [ ] **AC-0003.** For every obligation the contract enumerates, the lint
      registers a check **and that check detects the obligation's failure**: the
      suite derives one failure fixture per obligation identifier read from the
      contract, and requires the registered check to emit that identifier.
      Registry-key equality alone is not enough — a no-op registered against a
      new obligation would satisfy it while checking nothing. For an obligation
      with more than one failure mode the suite carries one fixture per mode,
      and `artifact_outline` has two: **absent**, and **present but divergent
      from its source**. Omission alone would be satisfied by a
      presence-only implementation, which is the whole of what row 10 promises
      where a source exists.
- [ ] **AC-0004.** Each of the five packs has an ordered guidebook whose step
      count equals its journey's stage count, whose step order equals the
      journey's stage order, and each of whose steps names the stage it
      implements.
- [ ] **AC-0005.** The lint passes over every step of all five guidebooks.
- [ ] **AC-0006.** Every projected value traces to the source its ladder names,
      or the step records which fallback it used. A value matching no source and
      recording no fallback fails, so an invented utterance cannot pass as a
      projected one. The ladders are the ones fixed in the Objective, and they
      exist because only 13 of 25 stages carry an utterance and 14 a gate.
- [ ] **AC-0007.** In every step's sample, the reader's input and the agent's
      turn are separately attributed. A single unlabelled block containing both
      fails, which is what a journey stage does today.
- [ ] **AC-0008.** Every published skill in each of the five packs is named by
      at least one step of that pack's guidebook, so no skill is reachable only
      by reading the pack's source.
- [ ] **AC-0009.** `guides/README.md` § P2b contains none of the contract's
      enumerated handoff-chain phrasings, and states the corrected relationship
      in its place. The prohibition half is **lexical and says so**; a novel
      paraphrase passes it, and catching one is the cold read's obligation. The
      positive half is what stops the criterion being satisfied by deleting the
      sentence and saying nothing.
- [ ] **AC-0010.** P2b's fourth step ends at an approved, build-ready decision
      brief and routes onward to the build loop rather than promising a merged
      change.
- [ ] **AC-0011.** The journeys index's sequence group carries no claim that
      each discipline hands a named artifact to the next, **and no sequence card
      states a handoff the packs' contracts do not make**. The group body and
      the four cards are one predicate here because the existing suite asserts
      the *retired* claim on the first three cards: correcting the body while
      leaving that assertion in place would keep the surface false and green.
      The criterion is positive as well as prohibitive — each of the four cards
      states the relationship the Objective's seam table gives it, so emptying
      the cards of handoff language and saying nothing fails. That positive half
      is the brief's inherited requirement that all four taglines agree with
      their sequence position.
- [ ] **AC-0012.** Every target path inside the five packs that the three
      sibling accepted-base ledgers own is accounted for exactly once — taken by
      this slice or retained by its sibling — and the consolidation ledger and
      each artifact's own record agree on which. The oracle compares **three**
      sets, not two: the eligible universe derived from the siblings' ledgers,
      this ledger's rows, and the reciprocal records. Two-set equality was not
      enough, because a target omitted from both the ledger and the record
      passes it while the scope disappears from both slices. Paths rather than
      pack names, because S3 alone holds 16 `packs/**/.apm/skills/**` targets
      inside the five packs that this slice cannot edit.
- [ ] **AC-0013.** No surface this slice writes contains any term from the
      contract's stated prohibited-claim vocabulary — the adoption, completion,
      task-success and first-value terms enumerated there. The criterion is
      **lexical and says so**: a paraphrase it does not enumerate passes, and
      catching one is a review obligation carried by the cold read, not a claim
      this criterion makes.
- [ ] **AC-0014.** Each human judgement check declares its kind from the
      contract's closed set of judgement kinds, and no machine-owned obligation
      identifier appears in that set. The lint fails a judgement check
      declaring no kind, or one declaring a kind that names a machine-owned
      obligation. Automation complacency means a judgement list polluted with
      machine-checkable items degrades its own judgement items, so the boundary
      needs an oracle — and a closed set of kinds is one a lint can decide,
      where "does this paraphrase a machine check" is not. Whether a declared
      judgement is a *good* one stays with the cold read.
- [ ] **AC-0015.** For every skill a step names, that step carries that skill's
      own utterance, artifact path and expected outline, **keyed to that skill**
      in a per-skill sub-entry rather than shared across the step. Naming ten
      skills against one shared utterance does not satisfy this criterion — and
      a step-level value cannot be attributed to a skill at all, which is why
      the representation is part of the obligation and not left to the
      implementer.
- [ ] **AC-0016.** Each of the three journey groups on the index carries the
      modifier assigned to its own relationship, and each of those modifiers
      declares its own at-rest style rule, the three rules differing. The
      criterion reaches the declared rules only; *visual* distinction is a
      review obligation and not a claim it makes.
- [ ] **AC-0017.** The onward route from the sequence resolves to P2b's own
      anchor, matched whole rather than by a shared fragment.
- [ ] **AC-0018.** P2b sits immediately after P2, with no other path heading
      between them.
- [ ] **AC-0019.** P2b is not counted as a stage of the five-stage walkthrough.
- [ ] **AC-0020.** P2b's selection condition names the disciplines the work
      needs, and neither P2's nor P2b's contains the contract's enumerated
      problem-clarity phrasings. Lexical on the prohibition, positive on the
      axis — so restating clarity in words the contract does not enumerate
      passes, and the cold read owns that residue.
- [ ] **AC-0022.** Every concept a step names as required resolves to an
      explanation — a link that resolves, or a bounded explanation on the step
      itself where nothing to link to exists. A named concept resolving to
      nothing fails. Whether a step *should* have named a concept it silently
      assumes is not reachable mechanically and is the cold read's obligation,
      so this criterion claims resolution and not sufficiency.
- [ ] **AC-0021.** **Each** pack's guidebook gets a cold read, and each one
      records for every step: what to type, what comes back, where to decide,
      what is held, what runs next, **whether any sentence claims the reader
      will adopt faster or reach value sooner however phrased, and whether any
      judgement check asks for something the lint already checks, and whether
      any step assumed a concept it never named**. The last three are the
      residue AC-0009, AC-0013, AC-0014, AC-0020 and AC-0022 explicitly do not
      reach; assigning them to this observer for one pack only would have left
      them unobserved in the other four.

      **A finding blocks the next wave only when a check can decide it.** Where
      the read finds something mechanically decidable — a link that does not
      resolve, a placeholder outside the declared form, internal bookkeeping on
      a reader-facing page — the answer is a lint check, and the wave does not
      open until it passes. Where the finding is about the adequacy of prose it
      is recorded and dispositioned, not gated: severity is not a cold reader's
      to assign, and two models arguing about malleable wording is not a gate.
      An earlier draft made every finding the read labelled an "execution
      defect" a blocker, which handed the gate to a label.

## Follow-ons

- eugenelim: the remaining 17 packs have no guidebook. This slice fixes the
  contract and proves it on the five a team SOP needs; extending it is a
  separate decision about appetite, not a gap in this one.
- eugenelim: `cohort-orientation-surfaces` — the marketing home has no route to
  the sequence. `web/src/pages/index.astro` carries no `/journeys/` reference
  and `journeys` is absent from `[shared_chrome].header`.
  `docs/design/content/marketing-home.md:386-412` has decided the answer and
  records itself as "not authority to edit the header"; Shipped
  `docs/specs/site-shared-chrome/spec.md:35-41` puts the change under
  "Ask first".
- eugenelim: `claude-apps-route-docs` (Draft, unimplemented) — the no-terminal
  route for a Claude Desktop reader.
- eugenelim: `packs/experience-design/DESIGN.md` names the state-matrix
  consumer `voice-and-microcopy`, a skill that does not exist; the skill is
  `ux-writing`. A pack source fix, excluded here by boundary.
- eugenelim: no committed-byte parity check exists between a `packs/*/JOURNEY.md`
  and its generated projection under `web/src/content/journeys/`. This slice
  changes no pack source and so cannot exercise that gate's red case.

## Assumptions

- Technical: `order:` frontmatter is consumed and produces an explicit ordered
  navigation list ahead of the kind buckets (source: `tools/build-site.py:872`);
  `journey:` frontmatter is declared but stripped before writing and read by
  nothing (source: `tools/build-site.py:908`)
- Technical: a new guide needs `title`, `summary`, `pack` and `kind`
  frontmatter with `title` equal to the leading H1, and needs no
  `guide-nav-baseline.toml` entry, which pins only pages lacking a title
  (source: `contracts/guide.schema.json`; `guide-nav-baseline.toml` header)
- Technical: `lint-journey-contract.py` freezes each journey stage's label set
  and order, so a stage's structure is stable enough to project from (source:
  file read, 2026-09-11)
- Technical: 63 of 74 skills in the five packs name an artifact path in their
  own `SKILL.md`, and 6 of 25 journey stages name one in their `Output` line, so
  a step's artifact location is projectable from the skill rather than authored
  (source: measured 2026-09-11)
- Technical: 18 of 74 skills ship a template asset and 23 state a shape in
  prose, while 38 supply neither, so row 10's outline is authored for roughly
  half the corpus (source: measured 2026-09-11)
- Technical: a guide linking into `docs/` renders as an off-site GitHub blob URL
  and escapes the rendered-link fragment audit, so an artifact pointer is stated
  as a path rather than linked (source: `guides/AGENTS.md:21`;
  `tools/check-rendered-site-links.py` header)
- Product: the second channel of the deliverable standard is the reader's own
  first run, not an embedded sample — embedded samples propagate their errors
  and drift silently (source:
  `docs/product/research/workflow-guidebooks-survey.md` Part 3)
- Technical: `web/src/test/FourDisciplineSequence.test.ts` skips when
  `build/journeys/index.html` is absent, so `make site-build` must run first and
  a skip reports as a pass (source: file read, lines 15-17 and 53)
- Product: the five packs are `desk-research`, `product-strategy`,
  `experience-design`, `product-engineering` and `core`; a guidebook step maps
  to a journey stage rather than to a skill, giving 25 steps (source: owner
  decision 2026-09-11)
- Product: this slice supersedes no sibling. Measured, the three siblings own
  34 guide targets inside the five packs and 31 carry no `order:`, so they are
  not guidebook steps; the siblings keep every target they own. Only three
  pages collide, all in `guides/core/`, and the carve-out is recorded for those
  three (source: owner decision 2026-09-11, correcting an earlier decision
  taken before the targets were enumerated)
- Product: `core` already carries an ordered fragment at orders 9 to 12, and T6
  absorbs those four pages into its seven-step guidebook rather than leaving
  two competing ordered sets on one sidebar (source: owner decision 2026-09-11)
- Product: the contract's obligations are a mix of evidence-backed mechanics and
  labelled house choices, grounded in cited
  evidence, and no claim rests on completion-rate figures, which the survey
  establishes are unsourced or single-vendor (source:
  `docs/product/research/workflow-guidebooks-survey.md`)
