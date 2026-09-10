# Spec: acceptance-criteria set construction

- **Status:** Draft <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** none
- **Brief:** docs/product/briefs/agent-authoring-input-quality.md
- **Discovery:** none
- **Contract:** none
- **Shape:** mixed

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

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
obligation whose observer cannot be named stays a candidate. The set-level pass
then reads coverage in both directions — every obligation reaches a criterion or
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
worded set — which is what its uniqueness and necessity checks compare.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| User-facing promise | Applicable — adopters install the skill and need the procedure outside it | `guides/core/reference/acceptance-criteria-authoring.md` (new; the per-criterion section is a later slice's) | `author-product-docs` conventions | Page validates and publishes; `title` matches the leading H1 | Page exists, carries the set-construction section only, and passes the guide validators |
| Reusable learning | Applicable — the delivery gate is a recorded exercise, not a suite | `docs/specs/acceptance-criteria-set-construction/notes/` | This spec's owner | Recorded three-case run with per-candidate dispositions | Run recorded with candidate count, final count and every disposition |
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
- Introduce a new top-level directory, a new module boundary, or a new
  dependency; the selection procedure is prose in files that already exist.
- Claim, in shipped text, that written guidance changes author behaviour in
  general. This slice's evaluation covers three frozen cases and nothing wider.

## Testing Strategy

- **The shipped procedure, its stage order, its admission grounds, its routing
  table, its composition hand-off, its set-level pass and the count policy
  (AC1, AC2, AC3, AC4, AC5, AC6, AC7, AC8, AC9, AC10, AC11, AC12, AC15, AC16,
  AC17, AC19):** goal-based check over the authored skill file. The observation
  is the presence, relative order and scope of that prose; the verification
  surface is the pack-local suite.
- **The pinned set's per-stage floor (AC18):** goal-based check. The observation is
  that the pinned set reaches every one of the five stages; it runs on the
  existing single-homing suite, which separately and already enforces that each
  pinned sentence occurs in exactly one of the four authoring surfaces. The pinned set is a
  **proxy**: whether a sentence states a rule is a judgement, so no check can
  enumerate every introduced rule sentence. The floor bounds the proxy's
  incompleteness rather than removing it, and the residue — a stage with two
  rules where only one is pinned — is caught at review or not at all.
- **The guide publishes the procedure (AC13):** goal-based check over the guide's
  own content. The observation is that each of the five stage names appears on
  the page. The guide validators establish publication, not content, so they do
  not discharge this criterion; the verification surface is a content check over
  the page.
- **The guide cites the shape owner (AC14):** goal-based check over the same
  page. The observation is that the criterion-shape owner is named and no rule
  that owner holds is restated. Separate from AC13 because a page can carry the
  stages while restating a shape rule, and can cite the owner while omitting a
  stage; the two fail on different inputs and need different repairs.
- **The three frozen cases and their seeded integrity (AC20, AC21):** TDD. Each
  case is data whose required shape and seeded material are compressible into
  assertions.
- **The frozen scoring order (AC22):** goal-based check. The observation is that
  every frozen case's stated scoring contract carries the three grading ranks
  and the losing-an-obligation failure rule; the verification surface is the
  pack-local suite.
- **The recorded run (AC23):** visual / manual QA. A model-in-the-loop
  measurement runs in-agent through one fresh subagent per case, and its recall
  verdict is read by a human from the recorded dispositions. No mechanical proxy
  substitutes for that reading.

## Acceptance Criteria

- [ ] The skill's acceptance-criteria step carries a numbered selection
      procedure whose steps run in the order name-obligations, admit,
      attach-scenarios, route, set-level pass.
- [ ] The procedure's hand-off to the criterion-shape owner sits after the
      routing step and before the set-level pass, so selection is complete
      before any candidate is worded and the pass reads a worded set.
- [ ] At that hand-off the procedure instructs composing each criterion from
      the parts its earlier steps already named — the obligation, the surface
      that observes its failure, and its disconfirming and positive cases —
      rather than writing a sentence and testing it afterwards.
- [ ] The procedure admits a candidate only on a named ship-blocking ground:
      an externally observable behaviour, a required refusal or recovery path,
      a compatibility or safety guardrail, or a measurable quality property
      under named conditions.
- [ ] Admission additionally requires naming the surface on which the
      candidate's failure would be observed, and the procedure states that a
      candidate whose observing surface cannot be named stays a candidate
      rather than becoming a criterion.
- [ ] Each admitted obligation carries one positive and one disconfirming
      scenario.
- [ ] The procedure routes each rejected candidate to a named destination:
      implementation choices to the plan, concrete cases and fixtures to
      Testing Strategy, an existing repository obligation to its owner,
      explanatory prose to the body, a duplicate or decoration out of the
      contract, and an obligation whose content only the build can settle to the
      plan as a discovery predicate carrying its constraint, required outcome
      and verification mode.
- [ ] The set-level pass tests necessity, uniqueness, consistency, joint
      feasibility, and coverage.
- [ ] The procedure defines coverage as satisfied for an Objective outcome or a
      non-waivable Boundary when it is either an admitted criterion or a routed
      disposition naming its owner, so no item can be both uncovered and
      correctly routed.
- [ ] The set-level pass additionally reads coverage from the criteria back to
      their observers: every admitted criterion has exactly one observing
      surface, and a criterion with none, or with two, fails the pass.
- [ ] The set-level pass reads the criteria back to the Objective as well:
      every admitted criterion names the Objective outcome or non-waivable
      Boundary its failure would leave unmet, and a criterion that names neither
      is decoration and is cut.
- [ ] The procedure defines the necessity check operationally: for each
      criterion, name the input that makes it red, then confirm that neither a
      sibling criterion nor an existing repository control — a test, lint or
      gate the repository already runs — reds on that same input. A criterion
      whose red input is already covered is merged, removed, or reduced to a
      citation of the owner that covers it.
- [ ] `guides/core/reference/acceptance-criteria-authoring.md` publishes the
      procedure's five stages.
- [ ] That guide cites the criterion-shape owner by document name and restates
      no rule that owner holds.
- [ ] The set-level pass states that a large irreducible set survives it, and
      that an independently shippable cluster becomes a decomposition proposal
      rather than a compound criterion.
- [ ] The procedure requires the author to record the criterion count and its
      position against their own shipped corpus.
- [ ] While the set is at or above the author's corpus p75, the procedure
      requires the uniqueness check to be re-run pairwise across the whole set
      with its result recorded; below that one position it requires only the
      per-criterion check against neighbours. One threshold, both branches, no
      band left undefined.
- [ ] The single-homing suite's pinned set carries at least one rule sentence
      from each of the procedure's five stages. Single-homing of those sentences
      is already delivered by that suite's existing owner test and is not
      restated here; this criterion is the floor that stops the set being empty
      or reaching only some stages.
- [ ] No shipped surface makes a criterion count reject a spec or prove one
      well-shaped, and a set above the corpus p75 passes on its obligations
      alone.
- [ ] The skill's eval register carries three frozen cases: a small change, a
      legitimately large change, and an amendment to an existing contract.
- [ ] Each frozen case carries its full seeded set: at least one
      implementation detail, one duplicate claim and one example-only variant
      that must not become criteria, and every objective and non-waivable
      guardrail that must remain represented.
- [ ] The shipped scoring order grades obligation and protected-guardrail
      recall first, non-criterion rejection second, and count as a descriptive
      outcome only, and records that a smaller set obtained by losing a
      distinct obligation or guardrail is a failure.
- [ ] The recorded three-case run retains every seeded objective and
      non-waivable guardrail, and admits no seeded implementation detail,
      duplicate claim or example-only variant as a criterion.

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
