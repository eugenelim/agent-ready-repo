# Spec: load-bearing-claim-grounding

- **Status:** Shipped <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** none
- **Brief:** docs/product/briefs/agent-authoring-input-quality.md
- **Contract:** none

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.
>
> **Not every section is contract.** `Boundaries`, `Testing Strategy` and
> `Acceptance Criteria` are what a completion gate reads, and an amendment
> changes them. `Objective`, `Durable Outputs`, `Follow-ons` and `Assumptions`
> are working material: they orient a reader and an author corrects them in place
> as the work teaches, without an amendment and without a review round.

## Objective

An author using `new-spec` routes a claim they cannot settle by what its
falsehood would cost, before the approval gate freezes the contract on it. The
question is *what does this delivery assert that nobody has executed against the
relevant surface, and what would break if it were false?* A claim that could
change intent, an acceptance criterion, architecture, a dependency choice, a
security or data boundary, the task graph, or a verification mechanism is settled
before approval, because after approval it may not be settleable at all — five of
seven deliveries in [`notes/replay.md`](notes/replay.md) record a correction found
during execution that the freeze made unfixable, queued for a human gate, or
recoverable only by a destructive reset. A claim that could change only an
unstarted task's local method belongs in that task with a kill condition. A cheap
reversible detail with a direct test oracle belongs in code. Success is that the
consequence of being wrong decides where the claim goes.

## Durable Outputs

| Semantic role | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- |
| Shipped agent guidance | `new-spec`'s assumptions step, in the core pack | eugenelim | the routing rule present, single-homed, the five cut shapes absent, and the pre-review probe step unmoved | AC-0001 through AC-0009 hold |
| Adopter-facing description | `guides/core/how-to/plan-and-execute-non-trivial-work.md` § the assumption checkpoint | eugenelim | it carries the owning step's anchor identifier and no row of the routing table | AC-0002 holds |
| Decision rationale, non-normative | [`notes/replay.md`](notes/replay.md) | eugenelim | the seven-delivery replay, its dating table, and every cut with the evidence that defeated it | complete before scope approval; an approval precondition, never an obligation authority |
| Release history | `docs/product/changelog.md` | eugenelim | a core-pack entry in the same change as the version bump | the released-artifact gate passes |
| Reusable learning | `project-knowledge` topics | eugenelim | capture at the spec and plan gates | receipts recorded, or `project-knowledge unavailable` |
| Current architecture | not applicable | — | no module boundary, dependency, or interface moves | — |
| Operations | not applicable | — | no runtime surface changes | — |

## Boundaries

### Always do

- State the routing rule in exactly one shipped surface, and reach it from
  elsewhere by a pointer carrying that surface's anchor identifier and none of
  its content.
- Keep the assumption categories as AC-0003 fixes them, which is that
  criterion's sole obligation and is not restated here.
- Fire the rule only on a claim that meets AC-0004's consequence test.
- Describe a control over shipped prose as the mechanical proxy it is, and say
  which property it does not reach.

### Ask first

- Any addition to the routing table's destinations beyond the three AC-0006
  fixes. The table is a closed set, and widening it changes what the rule
  obliges.

### Never do

- Add any evidence-shape obligation. [`notes/replay.md`](notes/replay.md) cut
  five candidates across four review rounds and an extended sample of seven
  deliveries, each on measured evidence, and AC-0008 makes the cut contractual.
- Change the pre-review disconfirming-evidence step's heading, firing condition,
  or side-effect-free probe bound. AC-0007 makes this contractual, so it moves
  only through a controlled spec amendment with owner authority. That surface
  belongs to slice A4 of the parent brief.
- Remove the assumptions step's bound against an unbounded sweep. AC-0009
  removes only the one-per-candidate cardinality; the sweep bound is a separate
  protection and survives the change.
- Add a fourth assumption category, or otherwise widen the taxonomy past what
  AC-0003 fixes.
- Weaken any of these four named protections: the two human approval gates
  `loop-engine` fires as `spec-approved` and `plan-approved`; the controlled
  amendment path `loop-cohort contract-amendment` guards; the completed-task
  section guard `validate_completed_task_sections` enforces at `approve-plan`;
  and the append-only identifier history a spec's retired list records. An edit
  that removes, bypasses, or makes optional any observable behaviour of those
  four violates this boundary.
- Implement progressive task locking, a post-gate replanning channel, a
  universal mutation-testing requirement, or a settle-first lifecycle stage. The
  replay surfaced a well-evidenced post-gate replanning finding and routed it to
  that owner rather than absorbing it.

## Testing Strategy

Every criterion here is a **goal-based check** over the shipped guidance text,
run by a suite under the core pack's `new-spec` test directory.

**Each criterion names its own falsifying mutation, because the criteria do not
share one shape.** Only AC-0001 has an excluded-surface boundary and so takes the
two-sided arm: the table present on its owning surface, and absent from every
other file under the two scan roots. AC-0002 is a presence-and-absence pair on the
same two surfaces — the anchor identifier present, every table row absent. The
rest are falsified differently: AC-0003, AC-0004 and
AC-0006 by an exact-set comparison that reddens on an omitted, added, or renamed
member; AC-0005 by section extraction, which reddens when the bound sits outside
the step; AC-0007 by editing one word of the protected text, which must
mismatch the pre-change digest taken from `git show HEAD:`; AC-0008 by injecting each of its five fixture
entries in turn, identifier and demand sentence alike; and AC-0009 by a removal-and-
retention pair, reddening both when the cardinality survives in either home and
when the no-sweep bound is removed with it.

- **Single home (AC-0001)** — the negative scan is driven from two named roots,
  so a surface added later is in scope without editing the control.
- **The pointers that reach it (AC-0002)** — the anchor identifier asserted
  verbatim on each of the two surfaces, and every routing-table row asserted
  absent from both, driven from the table the suite already parses.
- **The taxonomy (AC-0003)** — the enumerated categories resolve to exactly
  three.
- **The firing predicate and where its bound sits (AC-0004, AC-0005)** — two
  groups, because a correct predicate stated in a preamble fails only the second.
- **The routing table's key set (AC-0006)** — the parsed row keys are compared
  against a three-identifier fixture written in the test before any mapping is
  built, so the domain never comes from the artifact under test.
- **The pre-review probe step is unmoved (AC-0007)** — a digest of its heading,
  firing condition, and probe bound taken from `git show HEAD:`, not the working
  tree.
- **The cuts hold, and the cardinality is gone while the sweep bound stays
  (AC-0008, AC-0009)** — one needed negative and one paired positive. The first
  fails on any of the five fixture entries — an identifier or its demand
  sentence — and on nothing outside that set, which is the limit AC-0008 states.
  The second fails if the cardinality survives in either of its two homes, or if
  the no-sweep bound is removed along with it.

**What these controls do not reach, stated rather than implied.** A control over
prose sees structure and location. It cannot see whether a sentence is true, and
it cannot see whether an author changed behaviour on reading it. So this spec
gates the structural properties above and **gates nothing on the behavioural
property**, which is the move the shipped rubric's class 6 prescribes for a
judgement over authored prose.

The behavioural property is observed once, and that observation is not a gate:
the delivery exercises the shipped rule against two real claims from this
delivery's own authoring and records the routing in the verification ledger — a
delivery-time observation, not a standing test.

An output eval is also added to the skill's register, and it is **documentation,
not coverage**. `agentbundle pack evals run` selects its check with
`--check`, whose `choices=("activation", "behavior")` default to `activation`;
`pack-evals.yml` passes neither `--mode` nor `--check`, so the defaults select
headless activation, which reads `evals/eval_queries.json`. Nothing in that
workflow opens `evals/evals.json`. So the entry is never executed by any workflow, on a pull
request or otherwise. A regression deleting the rule still passes every gate, and
the structural controls above are what catch it.

Projection parity and the version surface are **not** tested here. The shipped
`agentbundle catalogue self-host --check` step inside `make build-check` already
proves projection parity on every pull request, and the pack delivery-contract
suite already proves the version increment. A control for either would be a
second home for an obligation that already has an owner.

## Acceptance Criteria

- [x] **AC-0001.** The routing table appears in exactly one shipped surface. The
  scanned set is every regular Markdown file reachable recursively from exactly
  two roots — `packs/core/.apm/skills` and `guides` — enumerated by the control
  from those paths rather than from a hand-written list of directories, so a
  surface added later is in scope without editing the control.
- [x] **AC-0002.** Every surface that must reach the rule carries the owning
  step's stable anchor identifier verbatim, and carries no row of the routing
  table. The surfaces are the `work-loop` plan-stage self-coverage step and the
  adopter how-to's assumption checkpoint.
- [x] **AC-0003.** The assumption categories enumerated by the assumptions step
  resolve to exactly three — Technical, Product, and Process — and the step
  states that the routing rule applies across them rather than adding one. This
  criterion is the taxonomy's sole owner.
- [x] **AC-0004.** A load-bearing claim is defined by exactly six consequences of
  its falsehood — a changed acceptance criterion, boundary, task graph,
  verification strategy, consequential failure direction, or chosen mechanism —
  with no seventh and no alternative test.
- [x] **AC-0005.** The obligation's firing bound is stated in the same step as
  the obligation, not in a preamble or a reference the step points at.
- [x] **AC-0006.** The routing table's row keys equal this exact set of three
  stable routing-input identifiers, as a multiset and in no other set:
  `reaches-the-contract`, `unstarted-task-method`, and `cheap-with-an-oracle`.
  Each maps to exactly one destination — resolved before approval by a bounded
  spike, carried in the unstarted task's own fields, or settled in code rather
  than design prose — and the control compares row keys against a fixture
  written in the test before it builds the mapping. The `unstarted-task-method`
  destination enumerates five fields: discovery predicate, constraint, required
  outcome, verification mode, and kill condition.
- [x] **AC-0007.** The pre-review disconfirming-evidence step is unmoved: its
  heading, its firing condition, and its side-effect-free probe bound carry the
  same text after this change as before it.
- [x] **AC-0008.** The assumptions step carries none of the five cut
  evidence-shape obligations. The obligation is exactly a five-entry fixture,
  each entry pairing an identifier with the demand sentence
  [`notes/replay.md`](notes/replay.md) records for it: `reused-machinery` with a
  machinery contract plus a discriminating example; `set-membership` with a
  distribution plus residuals; `generated-output` with the representation the
  real gate consumes; `generated-measurement` with a generator, a counted unit,
  and one home; `sweep-completeness` with a conclusion naming its surface. For
  each entry the control asserts the step names neither the identifier nor that
  sentence, and T1 injects all five in turn as mutations that must redden. The
  criterion reaches exactly those five entries and claims nothing about a
  paraphrase outside them.
- [x] **AC-0009.** The one-per-candidate *cardinality* is gone from both of its
  homes — the assumptions step's heading and the load-bearing sentence in its
  body — and the step's bound against an unbounded sweep is **retained**. A
  claim routed to a pre-approval spike may need more than one check; neither that
  nor any criterion here licenses a sweep.

## Follow-ons

- **The approval anchor is not recorded in any delivery's artifacts.** Dating the
  seven-delivery sample established that no `plan.md` searched carries an
  owner-approval line, which is why this replay could not test a
  frozen-at-approval discriminator and withdrew it. Recording that datum is cheap
  and would make the next replay of this kind answerable; it is not in this
  slice's scope.
- **The plan contract invites mid-execution amendment while the tooling forbids
  it**, and the only sanctioned escape is a destructive reset.
  `work-loop-in-process-guards` raises this as a design finding in its own words.
  That is a post-gate replanning channel and belongs to S2, not here.
- **Whether the rule changes what an author writes** is unmeasured and owned by
  `docs/product/briefs/guidance-activation-measurement.md`. This spec ships an
  obligation and proves it is stated and single-homed; it claims no behaviour
  change.

## Assumptions

- Process: no RFC is required. `CONTRIBUTING.md:33` reserves an RFC for
  unresolved direction needing more than one owner, the charter's mission or
  scope, who may approve work, a security trust model, or a broken published
  compatibility promise; none applies (user confirmation 2026-09-17).
- Process: the sample was extended to seven deliveries on owner instruction, and
  the resulting scope — routing only, every evidence-shape demand cut — follows
  the intake's own kill-or-narrow instruction (user confirmation 2026-09-17).
- Process: the pre-review probe step stays with slice A4, which
  `docs/product/briefs/agent-authoring-input-quality.md` § "Slice relationships"
  records as keeping that surface, its firing predicate, and its eval.
- Technical: the rule's delta over shipped guidance is measured, not asserted.
  The existing pre-review step requires one throwaway check of the load-bearing
  mechanism, and `construction-time-razor` complied with it while leaving four
  consequence-bearing claims unresolved; the existing grounded-plan-detail rule
  carries no kill condition and does not classify a claim by what its falsehood
  would change ([`notes/replay.md`](notes/replay.md) § "Of the three
  fully-baselined deliveries").
- Technical: three deliveries in the sample ran with all four catchers in force
  — `telemetry-sender-owns-its-configuration`, `pr-gate-suite-disposition`, and
  `construction-time-razor` — and only `construction-time-razor` was replayed
  against the routing rule, so the delta rests on one of those three while the
  freeze-damage evidence rests on five
  ([`notes/replay.md`](notes/replay.md) § dating table).
- Technical: exactly one shipped surface outside the skill restates the sentence
  this change edits — `guides/core/how-to/plan-and-execute-non-trivial-work.md:80`
  (probe: literal sweep for `one targeted check` across the repository, one hit).
- Technical: the cardinality has two homes in the skill, not one — the step
  heading at `SKILL.md:72-73` and the body sentence at `:74-75` (probe: read both).
- Technical: an output eval for this skill is **never executed**, so it is
  documentation rather than coverage. `new-spec` is in
  `packs/core/pack.toml`'s `[pack.evals].skills` list, but the `--check` flag
  carries `choices=("activation", "behavior")` with `default="activation"`
  (`packages/agentbundle/agentbundle/commands/pack_evals.py:1143-1148`) and
  `.github/workflows/pack-evals.yml:68` passes neither `--mode` nor `--check`,
  so the defaults select headless activation over `eval_queries.json`; no
  workflow opens `evals/evals.json` (probe: read both files and the parser).
- Technical: projection parity is already gated. `tools/repo/build_gate_chain.py`
  runs `agentbundle catalogue self-host --check` inside `make build-check`, and
  the two projections of the skill are byte-identical to the pack source today
  (probe: `shasum -a 256` over all three, one digest).
- Technical: the core pack's release surface is three files — `pack.toml` and
  `.claude-plugin/plugin.json` at 2.26.11, plus a changelog entry — because core
  carries no root marketplace entry (probe: no `"core"` match in
  `.claude-plugin/marketplace.json`).
- Technical: no content-hash or line-count test pins the skill file; the one
  existing pin is on the pre-review step's heading text, which AC-0007 preserves
  (`packs/core/tests/skills/new-spec/test_acceptance_criteria_discipline.py:120-122`).
