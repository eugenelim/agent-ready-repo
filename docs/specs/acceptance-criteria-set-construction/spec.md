# Spec: acceptance-criteria set construction

- **Status:** Approved <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** ADR-0107
- **Brief:** docs/product/briefs/agent-authoring-input-quality.md
- **Discovery:** none
- **Contract:** none
- **Shape:** mixed

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

**Scope, widened by owner decision on 2026-09-10.** This spec covers three
authoring moves on the loop contract, not one. Two were added because the same
defect produced all three: the skill tells an author what a finished artifact
must look like and never what move to make, so an author selects by instinct,
places facts by habit, and answers every finding by repairing it. The added
moves are the plan-authoring rules, brought under contract here rather than
left shipped without one, and a review-response protocol the skill does not
have today.

An author using `new-spec` — human or agent — decides *which* contract
obligations become acceptance criteria before wording any of them. The skill's
acceptance-criteria step carries an ordered selection procedure: name the
changed contract obligations, admit only candidates whose failure independently
blocks shipment *and* whose observing surface the author can name, attach one
positive and one disconfirming scenario per admitted obligation, route every
rejected candidate to a named owner — including, for an obligation whose
content only the build can settle, a discovery predicate in the plan rather than
an answer invented at approval time — then run a set-level necessity, uniqueness,
consistency, joint-feasibility and coverage pass.

The procedure is a **self-check the author runs while authoring**, not a gate
another party applies afterwards. Its load-bearing move is that a criterion is
admissible only once something is named that would show its failure: an
obligation whose observer cannot be named stays a candidate. The set-level pass, whose members
AC-0009 enumerates once and nothing else restates, reads coverage in both
directions — every obligation reaches a criterion or
a routed owner, and every criterion has exactly one observer. Necessity is
operational rather than a word in a list: each criterion names the input that
makes it red, and a criterion whose red input a sibling already covers is
merged or removed.

The author records the candidate count, the final count, and each candidate's
disposition. Success for that author is that a distinct obligation
and a non-waivable guardrail always survive selection, while a seeded
implementation detail, a duplicate claim and an example-only variant do not
become criteria. Criterion count is a descriptive outcome that orders how hard
the set-level pass looks; it never rejects a spec and never proves one is
well-shaped, so a genuinely large irreducible set survives.

Each criterion is then composed from the parts those steps already named — the
obligation, the surface that observes its failure, and its disconfirming and
positive cases — rather than written whole and tested afterwards. Composing
from singular parts is what keeps one criterion to one predicate.

Criterion *shape* — whether a given sentence is one criterion or two — stays
owned by the skill's `assets/spec.md`. This spec owns which obligations reach
that question at all, and where the hand-off to that owner sits: after routing,
before the set-level pass. Selection finishes first, and the pass then reads a
worded set together with the plan entries tracing to it — which is what its
uniqueness and necessity checks compare.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| User-facing promise | Applicable — adopters install the skill and need the procedure outside it | `guides/core/reference/acceptance-criteria-authoring.md` (new; the per-criterion section is a later slice's) | `author-product-docs` conventions | Page validates and publishes; `title` matches the leading H1 | Page exists, carries the set-construction section only, and passes the guide validators |
| Reusable learning | Applicable — the delivery gate is a recorded exercise, not a suite | `docs/specs/acceptance-criteria-set-construction/notes/verification-ledger.md` | This spec's owner | Recorded three-case run with per-candidate dispositions | Run recorded with candidate count, final count and every disposition |
| Release history | Applicable — a `.apm/**` content change is a released pack change | `docs/product/changelog.md` (a pack keeps no `CHANGELOG.md` of its own; that convention is for published packages) | Pack release pipeline | Free-standing topmost `core` entry at the bumped version | Entry present at the version `pack.toml` and `plugin.json` both carry |
| Current product truth | Applicable — the brief tracks slice delivery | `docs/product/briefs/agent-authoring-input-quality.md` § "Spec map" | `lint-brief-coverage` roll-up | Coverage roll-up resolves this spec through its `Brief:` back-link | Roll-up names this spec; no status hand-written into the brief |
| Decision rationale | Not applicable — no architectural choice is made or reversed; the owner decisions are already recorded in the brief's § "Constraints / Appetite" | none | — | — | — |
| Interface compatibility | Not applicable — no published interface changes; the skill's step numbering is internal to the file | none | — | — | — |

## Boundaries

The three-tier guard that keeps an implementing agent inside the lines.
*Always do* applies without asking; *Ask first* requires human sign-off
before proceeding; *Never do* is a hard rule, even under time pressure.

### Always do

- Edit pack sources under `packs/core/.apm/`, then regenerate the `.agents/` and
  `.claude/` projections and commit source and projection together.
- Add a pointer when a rule already has an owner, and cite that owner by
  document and identifier.
- Bump `packs/core/pack.toml` and `packs/core/.claude-plugin/plugin.json` to the
  same version, with core leading its own free-standing changelog entry.

### Ask first

- Any change to `assets/spec.md` beyond adding a cross-reference, because that
  file owns criterion shape.
- Any edit to `docs/product/briefs/agent-authoring-input-quality.md`.
- Retiring, renaming or reordering an existing eval case.

### Never do

- Add a fixed absolute criterion count to any surface — a cap, a ceiling, a
  budget, a refusal, or a pass/fail bar on how many criteria a spec may carry. A
  percentile derived from the author's own corpus, used only to order scrutiny,
  is not one of these and is required elsewhere in this contract.
- Restate a rule owned by `assets/spec.md`, `assets/plan.md` or
  `references/spec-authoring-rubric.md` into a second file.
- Silence a pre-existing warn-only lint warning to make a gate read clean.
- Introduce a new top-level directory or a new dependency. The selection
  procedure, the plan rules and the response protocol are prose in files that
  already exist. The one admitted addition is the alignment checker in
  AC-0033, owner-approved 2026-09-10: it takes a `scripts/` directory inside
  this skill, which is the catalogue's standard skill layout and is already how
  seven sibling skills ship their own tooling.
- Claim, on any surface, that a criterion count proves a set well-shaped. The
  count orders how hard the set-level pass looks and settles nothing on its own;
  no check reaches this claim, so it is held here and read at review.
- Claim, in shipped text, that written guidance changes author behaviour in
  general. This slice's evaluation covers three frozen cases and nothing wider.
- Build the identity or fingerprint mechanism beneath the single-homing check.
  The phrase-based oracle is how that check already works; leaving it is
  declining to repair a pre-existing gap, not shipping new debt, and everything
  this spec delivers works the same underneath it.

## Testing Strategy

- **The shipped procedure, its stage order, its admission grounds, its routing
  table, its composition hand-off, its set-level pass and the count policy
  (AC-0001, AC-0002, AC-0003, AC-0004, AC-0005, AC-0006, AC-0007, AC-0008, AC-0009, AC-0010, AC-0011, AC-0012, AC-0013, AC-0016,
  AC-0017):** goal-based check over the authored skill file. The observation
  is the presence, relative order and scope of that prose; the verification
  surface is the pack-local suite.
- **The count prohibition (AC-0018) — split surface.** The span check that the
  procedure states no fixed absolute count is a goal-based check on the
  pack-local suite. The sweep across all three shipped surfaces is a goal-based
  check at repository level, because reading the guide page from
  `packs/core/tests/` breaches the pack-test boundary. Both are named here so the
  declared placement matches where each check lands.
- **The guide publishes the procedure (AC-0014):** goal-based check over the guide's
  own content. The observation is that each of the five stage names appears on
  the page. The guide validators establish publication, not content, so they do
  not discharge this criterion; the verification surface is a content check over
  the page.
- **The guide cites the shape owner (AC-0015):** goal-based check over the same
  page. The observation is that the criterion-shape owner is named and no rule
  that owner holds is restated. Separate from AC-0014 because a page can carry the
  stages while restating a shape rule, and can cite the owner while omitting a
  stage; the two fail on different inputs and need different repairs.
- **The three frozen cases and their seeded integrity (AC-0019, AC-0020):** TDD. Each
  case is data whose required shape and seeded material are compressible into
  assertions.
- **The frozen scoring order (AC-0021):** goal-based check. The observation is that
  every frozen case's stated scoring contract carries the three grading ranks
  and the losing-an-obligation failure rule; the verification surface is the
  pack-local suite.
- **The plan rules, the response protocol and the earn-its-keep scope (AC-0022, AC-0023, AC-0024, AC-0025, AC-0026, AC-0027):** goal-based check over the authored skill file, on the pack-local suite; five of the six plan rules are pinned there today and the sixth is added by the task that ships this.
- **The discovery pass (AC-0036):** goal-based check over the authored skill
  file, on the pack-local suite. Its surface is the boundary between the
  durable-outputs step and the spec body, not the acceptance-criteria step.
- **The grounding explorer (AC-0035):** TDD. Each probe is a function over a
  fixture tree, and its cases compress into assertions.
- **The disposition record (AC-0034):** goal-based check over the authored skill
  file, on the pack-local suite. Grouped with the procedure, which is its surface.
- **ADR-0107's confirmation state (AC-0032):** goal-based check over the ADR,
  at repository level. The ADR is not pack content, so the pack-local suite
  cannot read it.
- **The alignment checker (AC-0033):** TDD. The check is a pure function over a
  spec directory's two texts and its retired list, so its cases compress into
  assertions. Its scope is deliberately distinct from the repository's
  spec-status lint, which decides spec *state* — status vocabulary, criteria
  checked at a ship transition, deferral anchors, contract traceability. This
  one decides *item alignment* and owns no lifecycle question.
- **Per-task grounding (AC-0031):** goal-based check over the authored skill
  file, on the pack-local suite. Grouped with the plan rules rather than the
  procedure, because the plan step is its surface.
- **The template carries the identifier convention (AC-0030):** goal-based check
  over `assets/spec.md`, on the pack-local suite. The asset sits inside
  `packs/core`, so no pack-test boundary is crossed.
- **The recorded run, both graded ranks (AC-0028, AC-0029):** visual / manual QA. A model-in-the-loop
  measurement runs in-agent through one fresh subagent per case, and its recall
  verdict is read by a human from the recorded dispositions. No mechanical proxy
  substitutes for that reading.

## Acceptance Criteria

- [ ] **AC-0001.** The skill's acceptance-criteria step carries a numbered selection
      procedure whose steps run in the order name-obligations, admit,
      attach-scenarios, route, set-level pass.
- [ ] **AC-0002.** The procedure's hand-off to the criterion-shape owner sits after the
      routing step and before the set-level pass, so selection is complete
      before any candidate is worded and the pass reads a worded set.
- [ ] **AC-0003.** At that hand-off the procedure instructs composing each criterion from
      the parts its earlier steps already named — the obligation, the surface
      that observes its failure, and its disconfirming and positive cases —
      rather than writing a sentence and testing it afterwards.
- [ ] **AC-0004.** The procedure admits a candidate only on a named ship-blocking ground:
      an externally observable behaviour, a required refusal or recovery path,
      a compatibility or safety guardrail, or a measurable quality property
      under named conditions.
- [ ] **AC-0005.** Admission additionally requires naming the surface on which the
      candidate's failure would be observed, and the procedure states that a
      candidate whose observing surface cannot be named stays a candidate
      rather than becoming a criterion.
- [ ] **AC-0006.** Admission additionally requires grounding the criterion in what already
      governs the surface it demands content on. The procedure defines that
      **governing set** once, and it has four members: the scoped `AGENTS.md`
      files, resolved by walking from the surface's own directory up to the
      repository root and reading each file found; the gates and linters that run
      against that surface; the documents that already own rules for it; and the
      repository conventions that apply to it. A candidate demanding what any
      member forbids is not admissible in that form. The `AGENTS.md` member is
      stated as a walk, not a single lookup, because a nested file does not
      replace the one above it and stopping at the first hit skips the rest
      silently. The other three members are named because guidance files are the
      surfaces an author thinks to read, and a linter, an existing owner and a
      convention are the ones that actually fail the work.
- [ ] **AC-0007.** Each admitted obligation carries one positive and one disconfirming
      scenario.
- [ ] **AC-0008.** The procedure routes each rejected candidate to a named destination:
      implementation choices to the plan, concrete cases and fixtures to
      Testing Strategy, an existing repository obligation to its owner,
      explanatory prose to the body, a duplicate or decoration out of the
      contract, and an obligation whose content only the build can settle to the
      plan as a discovery predicate carrying its constraint, required outcome
      and verification mode.
- [ ] **AC-0009.** The set-level pass runs over the loop contract as one set — the spec's
      criteria together with the plan entries that trace to them — rather than
      over the criteria alone, and tests necessity, uniqueness, consistency,
      joint feasibility, coverage, propagation, and residual freshness. Three
      members carry a stated plan-side question: uniqueness asks whether a
      criterion and a construction test claim the same thing, coverage asks
      whether every admitted criterion has a plan entry, and propagation asks
      whether a touched criterion's entry still matches it. The rest read the
      criteria. Propagation cites the rubric's sibling
      check as its owner rather than restating it, adding only its scope and its
      timing: it re-reads each touched criterion's construction test and
      verification entry against that criterion's current wording, because a
      text search cannot see a test that still describes the pre-repair claim,
      and it completes in the same round before the round is reported. Residual
      freshness re-tests each recorded residual against current state rather
      than carrying it forward on its last wording.
- [ ] **AC-0010.** The procedure defines coverage as satisfied for an Objective outcome or a
      non-waivable Boundary when it is either an admitted criterion or a routed
      disposition naming its owner, so no item can be both uncovered and
      correctly routed.
- [ ] **AC-0011.** The set-level pass additionally reads coverage from the criteria back to
      their observers: every admitted criterion has exactly one observing
      surface, and a criterion with none, or with two, fails the pass.
- [ ] **AC-0012.** The set-level pass reads the criteria back to what they serve: every
      admitted criterion names the Objective outcome, non-waivable Boundary, or
      applicable Durable Output its failure would leave unmet. A criterion that
      names none of those is decoration and is cut.
- [ ] **AC-0013.** The procedure defines the necessity check operationally: for each
      criterion, state its whole failure predicate — the input, the expected
      outcome, and the observing surface — then confirm no sibling criterion and
      no existing repository control already enforces that same predicate. A
      matching input alone is not coverage: two controls can red on one input
      while asserting different outcomes. A criterion whose predicate is already
      enforced is merged, removed, or reduced to a citation of that owner.
- [ ] **AC-0014.** `guides/core/reference/acceptance-criteria-authoring.md` publishes the
      procedure's five stages.
- [ ] **AC-0015.** That guide cites the criterion-shape owner by document name, and none of
      that owner's pinned rule sentences appears on the page.
- [ ] **AC-0016.** The set-level pass states that a large irreducible set survives it, and
      that an independently shippable cluster becomes a decomposition proposal
      rather than a compound criterion.
- [ ] **AC-0017.** The procedure cites the rubric's threshold section as the owner of how a
      count threshold is derived and what an above-threshold count means, and
      states the threshold it branches on rather than deriving one: the rubric owns
      how an author measures a corpus and arrives at a percentile, this procedure
      owns only what happens on each side of whatever threshold that produced.
      While the set is at or above the author's stated threshold, the procedure
      requires the uniqueness check to be re-run pairwise across the whole set
      with its result recorded; below that one position it requires only the
      per-criterion check against neighbours. One threshold, both branches, no
      band left undefined.
- [ ] **AC-0018.** No surface this slice ships — the procedure span, the guide page, or the
      frozen eval entries — states a fixed absolute criterion count, meaning a
      cap, ceiling, budget, refusal or pass/fail bar on how many criteria a spec
      may carry, and a set above the author's stated threshold passes on its
      obligations alone.
      The surface set is the three this slice ships because that is what the
      check reads; pre-existing shipped surfaces are a recorded residual, not
      this criterion. The wider claim that count never proves quality is a
      non-waivable Boundary, not this criterion, because no check reaches it.
- [ ] **AC-0019.** The skill's eval register carries three frozen cases, one per named
      shape: a small change, a large change, and an amendment to an existing
      contract. Whether the large case's obligation set is genuinely irreducible
      is a review obligation, not this criterion — no check reads it, and a
      criterion claiming it would reach past its own oracle.
- [ ] **AC-0020.** Each frozen case carries its full seeded set: at least one
      implementation detail, one duplicate claim and one example-only variant
      that must not become criteria, and every objective and non-waivable
      guardrail that must remain represented.
- [ ] **AC-0021.** The shipped scoring order grades obligation and protected-guardrail
      recall first, non-criterion rejection second, and count as a descriptive
      outcome only, and records that a smaller set obtained by losing a
      distinct obligation or guardrail is a failure.
- [ ] **AC-0022.** The skill's plan step carries the plan-authoring rules: a fact belongs in
      the design unless a task must implement or verify it; a `Done when` points
      at its own `Tests`; an obligation a completion gate must read belongs in
      `Tests` rather than `Approach`; a claim about a check names the comparison
      its oracle performs; a `Tests`-outruns-`Approach` ratio is read before it
      is cut; and a whole-plan walk precedes review.
- [ ] **AC-0023.** The skill's review step names the responses available to a sustained
      finding — repair the artifact, narrow the claim to what its check reaches,
      cut the item the finding is about, dismiss the finding with its reason
      recorded and re-present it to the next round, repair the generator rather
      than the instance, route it to an owner that already covers it, bound it
      out of scope and record a follow-on that names its new owner, or accept it
      with the reason it is proportionate recorded — and
      states that a sustained finding does not by itself require an edit.
- [ ] **AC-0024.** Where a finding is that a claim reaches further than its check, the
      procedure states both answers and how to choose: strengthen the check when
      one can reach the stated obligation, narrow the claim when none can.
- [ ] **AC-0025.** Where a finding is that a criterion demands content the guidance
      governing its destination surface forbids, the procedure states that the
      criterion changes and the forbidden content is never authored to satisfy
      it. A criterion no implementation can satisfy is a defect in the
      criterion, and a repair round is where one is most often introduced.
- [ ] **AC-0026.** The skill's review step instructs the stop-decision report to carry the
      finding trend by round, and for each remaining residual its consequence,
      the responses available to it, and what each would cost — so the owner
      chooses between stated options rather than reading a list of problems. It
      states the protected-risk-class condition directly and enumerates no class
      list, because shipped pack content carries no citation to an internal
      record. The owner of that class set is
      `docs/product/intents/work-loop-review-economics.md` § Guardrail, named
      here in the contract and deliberately not in the pack.
- [ ] **AC-0027.** The earn-its-keep test applies to every criterion in the set rather than
      only to those added during review, and runs while rounds are still
      running rather than only after they converge.
- [ ] **AC-0028.** The recorded three-case run retains every seeded objective and
      non-waivable guardrail.
- [ ] **AC-0029.** That run admits no seeded implementation detail, duplicate claim or
      example-only variant as a criterion.
- [ ] **AC-0030.** The skill's bundled `assets/spec.md` carries the loop-contract
      identifier convention, stated directly rather than cited because shipped
      pack content carries no internal-record citation: every acceptance
      criterion and every verification item takes an opaque, append-only
      identifier scoped to its own spec directory, drawn from a class-marked
      form — `AC-` for an acceptance criterion, `VI-` for a verification item —
      so a reference names which class it resolves against and a derived
      identifier is detectable rather than a matter of opinion. Each is assigned
      once, never
      renumbered on insertion or reorder, never reused after removal, and each
      removal recorded under a `## Retired identifiers` heading in the same
      artifact, one bare identifier per list item, the heading omitted while
      nothing has been retired — and the template's own
      criteria list shows the labelled form, so a criterion is cited without
      being counted. The template also fixes the verification group's shape: a
      Testing Strategy group is a list item whose leading bold segment names, in
      parentheses, every criterion it covers. Without a stated shape the
      one-group-per-criterion rule has nothing to read.
- [ ] **AC-0031.** The plan step requires each task to be grounded against the same
      governing set AC-0006 defines, resolved for the surfaces that task's own
      work touches rather than for the plan as a whole, and to record what it
      resolved. A plan-level anchor list is not sufficient and the procedure says
      so: it is written once, against the surfaces the author expected to touch,
      and a task added later inherits it without ever testing it. The procedure
      names no tool for the resolving. It requires the recorded result and
      instructs the author to pick the most token-efficient bounded exploration
      the session actually offers — a subagent, a worker, or a direct search —
      because a named tool makes the rule unrunnable wherever that tool is
      absent, and the obligation is the grounding, never the mechanism. The
      resolving runs mechanically first and semantically second: every file that
      names a touched path is enumerated by search before any model is asked
      which rules apply, because the search is exhaustive over
      references-by-path while the question is not. What the search cannot reach
      — a gate matching by glob or directory walk, and a rule that applies by
      content rather than by path — is the stated residue that review still
      owns.
- [ ] **AC-0032.** ADR-0107's `Revisit if` names a tool that enforces no-reuse for
      inline-Markdown items, and the checker below is that tool, so the trigger
      fires on delivery. The ADR's `Confirmation` moves from reviewer-checked to
      the shipped check and its `Revisit if` records that the trigger fired and
      the decision stands unchanged. A shipped decision record stating that no
      lint enforces it, on the commit that ships the lint, is the conflict the
      repository's own guidance forbids resolving silently.
- [ ] **AC-0033.** The skill ships its own alignment checker, invoked from its own
      `scripts/` directory and depending on no other skill. It decides the
      mechanical alignment of a loop contract's items: every acceptance criterion
      carries a well-formed identifier, identifiers are unique within the spec
      directory, none appears in the retired list, every identifier reference in
      `spec.md` and `plan.md` carrying the criterion class marker resolves to a
      criterion that exists — an item-class identifier is resolved against the
      items, not the criteria — every
      criterion is named by at least one plan entry and appears in exactly one
      verification group, and a verification item's identifier is its own rather
      than derived from the criterion or task it serves. A spec whose criteria
      carry no identifiers is skipped rather than failed, so the checker is
      adoptable against the existing corpus on the commit that introduces it.
- [ ] **AC-0034.** The procedure requires each candidate's disposition to be recorded,
      and the candidate and final counts that follow from those dispositions. The
      rubric owns deriving a count threshold from the author's shipped corpus and
      what an above-threshold count means; it owns no record of what this
      selection did. That record is the procedure's own output — without it
      nothing distinguishes an obligation admitted from one routed to an owner,
      and the set-level pass has no list to read back against.
- [ ] **AC-0035.** The skill ships a grounding explorer in its own `scripts/`, depending
      on no other skill, answering the mechanical half of AC-0031 from a seed set
      of touched paths: which files name a seed, which historically change with
      one, which gates would run one, which quote a distinctive line from one,
      and which scoped guidance governs each. Every probe reports and none
      decides; the two thresholds whose right value is repository-shaped — the
      sweep-commit size and the phrase cutoff — derive from the adopter
      repository's own distribution rather than being fixed, and the report names
      each value with what it was derived from, so a mis-calibration is visible
      instead of silently narrowing the result; the remaining bounds are
      presentation limits with documented defaults and flags; every probe carries
      a bounded result; and
      every probe distinguishes three outcomes — found, none found, and input
      unavailable — because a probe that returns empty when its input is missing
      is indistinguishable from a clean result. Whatever the explorer cannot
      settle mechanically it emits as a named ambiguity with its candidate
      resolutions, for the author to decide once and record. It reads no
      configuration file of its own, and an absent or thin grounding surface
      lowers the starting information and never fails the run. The report carries
      a surface inventory saying which known grounding surfaces are present and
      which carry content, so a degraded grounding is legible rather than silent.
      Consuming those surfaces as probe input — a recorded value seeding a
      derivation, and a record the repository contradicts reported as drift — is
      named in the follow-on that owns it, not claimed here.
- [ ] **AC-0036.** Once durable outputs are planned and their destinations resolved,
      and before the spec body is written, the procedure runs a grounding pass
      over those destinations and records what it returned. This is discovery,
      not validation: no criterion exists yet, and the output is design input —
      what already owns these surfaces, what already governs them, what already
      runs them, and what an accepted decision has already settled about them.
      The procedure says why the placement is load-bearing: before durable
      outputs there are no destinations to ground, and after the body is written
      the same facts arrive one criterion at a time, against a design they would
      have changed.

## Follow-ons

- eugenelim: [`docs/product/intents/loop-contract-item-identity-mechanism.md`](../../product/intents/loop-contract-item-identity-mechanism.md)
  — derive the pinned set from rule identifiers, fingerprint each item, and route
  a changed item's dependants into the next re-review's scope. Closes two of the
  single-homing oracle's three blind spots and gives the propagation sweep a
  mechanical backing; paraphrase detection stays out of scope there too.
- eugenelim: [`docs/product/intents/review-response-protocol-across-reviewer-surfaces.md`](../../product/intents/review-response-protocol-across-reviewer-surfaces.md)
  — carry the eight-response protocol this spec ships into `new-spec` out to
  `shaping-reviewer` and the pack reviewer surfaces, and rule out relitigating a
  decision a brief records as settled. This spec owns the authoring side only;
  the receiving side names no legitimate answer to a finding, which is why a
  sustained finding there reads as an instruction to edit. That intent also
  carries the boundary with
  [`spec-review-validation-guidance`](../../product/intents/spec-review-validation-guidance.md),
  a Draft intent on marking a finding's origin and testing its facts before
  repair: it shares this contract's guardrail of adding no lint and no
  review-count limit, and the two must not both come to own how a finding is
  answered.
- eugenelim: [`docs/product/intents/grounding-probe-extensions.md`](../../product/intents/grounding-probe-extensions.md)
  — the two probes this slice's survey ranks second and third: authority and
  projection closure, and the executable document-contract check. Held back
  because neither is cheap the way live-references was, and the second would
  execute a consumer's parse mode, which is a security surface the shipped probes
  do not have.

## Assumptions

- Technical: the acceptance-criteria procedure's surface is the `new-spec`
  skill's `SKILL.md` step 4 "No Acceptance Criteria" bullet, with the
  criterion-shape deferral restated at the shaping-review step (source: file
  read, 2026-09-10)
- Technical: an eval entry carries exactly `id`, `prompt`, `expected_output`
  and `assertions`, with unique ids across the register (source:
  `packs/core/tests/skills/new-spec/test_acceptance_criteria_discipline.py`)
- Technical: a new guide needs `title`, `summary`, `pack` and `kind`
  frontmatter with `title` equal to the leading H1, and no navigation-baseline
  row (source: `contracts/guide.schema.json`; `guides/AGENTS.md`)
- Technical: `Shape: mixed` fits a skill-prose, guide and test change (source:
  `docs/specs/desk-research-build-handover/spec.md`)
- Process: a `.apm/**` content change bumps `pack.toml` and
  `.claude-plugin/plugin.json` together, and core leads its own free-standing
  changelog entry (source: `packs/AGENTS.md` § Version bump rule;
  `docs/product/changelog.md` header). The version is resolved against
  `origin/main` at release time, not reserved here: a peer change to the same
  pack already claims the next patch, so this slice takes the one after
  whichever version has landed when its release task runs (source: peer session
  notice, 2026-09-10 — corrects an earlier assumption that named a specific
  version from a local read)
- Process: a brief-derived spec registers in the workspace lifecycle index with
  the brief as its parent at spec-authoring time (source: `workspace.toml`
  precedent comment on the `sdlc-guide-uplift-and-learning-paths` S1 entry)
- Process: a model-in-the-loop evaluation runs in-agent through fresh
  subagents, never through an API key or SDK call (source: owner decision
  2026-08-18)
- Process: the evaluation adds no durable run schema, so no scorer script and
  no results file format (source:
  `docs/product/briefs/agent-authoring-input-quality.md` § "Author criteria
  from obligations, not from every check")
- Process: the brief's body is not edited by this slice; its § "Corpus"
  exclusion rule already covers this spec generically (source: user
  confirmation 2026-09-10)
- Product: this serves spec authors invoking `new-spec`, and the slice ends
  when the procedure, the guide's set-construction section, the three frozen
  cases, their seed pinning and the recorded run exist (source: user
  confirmation 2026-09-10)
- Product: the recorded three-case run happens inside this delivery rather
  than as a later exercise (source: user confirmation 2026-09-10)
