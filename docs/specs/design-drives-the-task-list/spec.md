# Spec: the design drives the task list

- **Status:** Shipped <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** ADR-0099
- **Brief:** none
- **Discovery:** none
- **Contract:** none
- **Shape:** mixed

## Outcome

Every `## Design (LLD)` sub-section with body content, in a plan that carries
`Owned by:` at least once, names the tasks that own it, and the authoring
surface emits a finding for one that names none. Grounding that arrives for a
seam the plan declared ungrounded is recorded without amending the sealed
plan, while a settled design decision that execution falsifies goes through
controlled amendment.

## What Changes

- `assets/plan.md`'s `## Design (LLD)` sub-sections gain an `Owned by:` field
  beside the existing `Traces to:`, carrying the task IDs that implement the
  sub-section's decisions.
- `new-spec/SKILL.md`'s pre-review walk gains a fifth traversal, from the LLD
  down into the task list. The four existing traversals are unchanged.
- `lint-contract-item-alignment.py` gains two rules over `Owned by:` —
  presence in a participating plan, and resolution to a defined task ID. A
  plan participates by carrying the field once, so a plan predating the field
  is reported rather than failed. Neither rule reads a base ref.
- The lint's `TASK` pattern accepts a lettered task-ID suffix, which it
  currently drops and `loop-cohort.py` already accepts.
- `work-loop/SKILL.md`'s DECIDE step gains cause-depth classification: a
  sustained finding whose cause is an LLD decision takes the
  `repair-the-generator` rung, over the tasks that sub-section's `Owned by:`
  field names.
- `work-loop`'s delivery-contract-lifecycle reference separates two in-flight
  cases that currently read alike: grounding arriving for a declared-ungrounded
  seam, which the ledger takes, and a settled decision falsified by execution,
  which controlled amendment takes.
- `new-spec/SKILL.md`'s routing table keeps its three rows; the residual row's
  destination gains a proportionality clause.
- Five `## Design (LLD)` sub-sections gain conditional prompts for design
  dimensions the template does not currently name.

## Durable Outputs

| Semantic role | Destination | Owner | Evidence | Closeout condition |
| --- | --- | --- | --- | --- |
| Maintainer procedure | `packs/core/.apm/skills/new-spec/SKILL.md`, `assets/plan.md` | eugenelim | the filled traversal and template fields | the fifth traversal and `Owned by:` ship in the pack source |
| Maintainer procedure | `packs/core/.apm/skills/work-loop/SKILL.md`, `references/delivery-contract-lifecycle.md` | eugenelim | the DECIDE cause-depth rungs and the two-case in-flight split | both ship in the pack source |
| Interface compatibility | `packs/core/.apm/skills/new-spec/scripts/lint-contract-item-alignment.py` | eugenelim | the new finding kinds and the widened task-ID pattern | `FINDING_KINDS` carries both kinds |
| Reusable learning | `docs/specs/design-drives-the-task-list/notes/verification-ledger.md` | eugenelim | the corpus counts | the ledger records the run over every recorded plan |
| Current product truth | `docs/product/changelog.md` | eugenelim | the released-artifact entry | the entry leads the core pack's changelog section |

Retention class: repository-durable for every row above. Each is readable by
any reviewer, worktree, or CI job from the repository itself.

## Agent Rules

### Always do

- Edit `packs/core/.apm/skills/` as the source, then rebuild the `.claude/` and
  `.agents/` projections with `make build-self`.
- Run a new or changed lint rule over every recorded plan under `docs/specs/`
  before treating its finding set as correct.
- Keep the traversal one-directional: LLD down into tasks, never tasks up into
  the LLD.

### Ask first

- Before changing the scope of the plan approval digest in
  `_loop_guards.py`, which ADR-0099 governs.
- Before adding a fourth row to the load-bearing-claim routing table, or
  altering its reversibility condition.
- Before routing any in-flight correction away from controlled amendment.

### Never do

- Never add a new gate, a new top-level directory, or a new dependency.
- Never edit step 5a of `new-spec/SKILL.md`, which `_5A_DIGEST` pins to a
  different brief's slice.
- Never reduce or merge an acceptance criterion to shorten this spec.
- Never widen the left set of the durable-retention rule in the `## Design
  (LLD)` retention paragraph.

## Testing Strategy

- **Template fields and prompts, TDD (AC-0001, AC-0020)** — a content
  assertion over the shipped template has a compressible invariant, and the
  template is already pinned this way.
- **Skill prose, TDD (AC-0002, AC-0015, AC-0016, AC-0024, AC-0017, AC-0018, AC-0019)** —
  the same, over `new-spec/SKILL.md` and `work-loop/SKILL.md`; a test is what
  catches a later removal.
- **Lint rules, TDD (AC-0003, AC-0004, AC-0005, AC-0006, AC-0007, AC-0008, AC-0009)** —
  each rule is a predicate over a plan text with a red case and a green case,
  which is what TDD is for.
- **In-flight routing prose, TDD (AC-0012, AC-0013, AC-0023)** — a content assertion
  over the lifecycle reference, whose two cases must stay distinguishable.
- **Digest behavior, TDD (AC-0014)** — a differential assertion over two plan
  texts is the only thing that shows the digest covers the whole file.
- **Corpus measurement, goal-based check (AC-0010, AC-0011)** — a single run
  over the recorded plans produces counts; the outcome is the numbers.
- **Preservation and size, goal-based check (AC-0021, AC-0022)** — a byte
  comparison and a line count each verify the outcome in one command.

## Acceptance Criteria

- [x] **AC-0001.** Each `## Design (LLD)` sub-section in
  `packs/core/.apm/skills/new-spec/assets/plan.md` carries an `Owned by:`
  field, documented as a comma-separated list of task IDs each matching
  `T[0-9]+[a-z]?`, stated beside that sub-section's existing `Traces to:`
  field.
- [x] **AC-0002.** The "Walk the whole plan once before review" list in
  `packs/core/.apm/skills/new-spec/SKILL.md` carries a fifth traversal: every
  interface, type, symbol, or ownership decision named in `## Design (LLD)`
  has an owning task.
- [x] **AC-0003.** In a plan where at least one `## Design (LLD)` sub-section
  carries an `Owned by:` field, `lint-contract-item-alignment.py` emits a
  failing finding for every sub-section of that plan which has body content
  and does not name at least one task ID matching `T[0-9]+[a-z]?` in an
  `Owned by:` field. An absent field, a present but empty field, and a field
  naming nothing that parses all fail this one predicate.
- [x] **AC-0004.** `lint-contract-item-alignment.py` emits a failing finding
  when an `Owned by:` field names a task ID that no `### T<n>` heading in the
  same plan defines.
- [x] **AC-0005.** A plan where no `## Design (LLD)` sub-section carries an
  `Owned by:` field contributes no failing finding from AC-0003.
- [x] **AC-0006.** A plan where no `## Design (LLD)` sub-section carries an
  `Owned by:` field is named in the run's reported-not-failing output as a
  plan predating the field.
- [x] **AC-0007.** Neither the AC-0003 rule nor the AC-0004 rule reads a base
  ref. Both appear in the run's no-input output exactly when the plan text is
  empty — whether `plan.md` is absent, its read was refused, or the file has
  no content, the three cases `check()` already treats alike — and in no
  other case.
- [x] **AC-0008.** `lint-contract-item-alignment.py` emits no failing finding
  in either of these cases: a task that no `## Design (LLD)` sub-section
  names, and a plan with no `## Design (LLD)` section at all.
- [x] **AC-0009.** The lint's `TASK` pattern admits a lettered task-ID suffix
  in both its capturing group and its lookahead, so a `### T2a` heading enters
  the set of defined task IDs that AC-0004 resolves against.
- [x] **AC-0010.** Running `lint-contract-item-alignment.py` over every plan
  under `docs/specs/` produces zero failing findings from the AC-0003 and
  AC-0004 rules.
- [x] **AC-0011.** `notes/verification-ledger.md` records, for the AC-0010
  run: the plan count, the count carrying a `## Design (LLD)` section, the
  count of sub-sections with body content, the participating plan count, and
  the predating plan count.
- [x] **AC-0012.** `work-loop`'s `references/delivery-contract-lifecycle.md`
  states that grounding which arrives for a seam the plan recorded as
  `no stub (implementation-discovered)` is recorded in the verification ledger,
  and that doing so amends neither approved artifact.
- [x] **AC-0013.** That same reference states that a design decision which
  approval settled and execution falsified is a plan error taking the
  controlled amendment procedure, and that the verification ledger is not a
  route for it.
- [x] **AC-0014.** Two `plan.md` texts differing only outside the
  `## Acceptance Criteria` section produce different approval digests, so the
  digest covers the whole plan and `## Design (LLD)` stays inside the pinned
  contract.
- [x] **AC-0015.** `packs/core/.apm/skills/new-spec/SKILL.md`'s
  load-bearing-claim routing table has exactly three rows, whose keys are
  `reaches-the-contract`, `unstarted-task-method`, and
  `cheap-with-an-oracle`.
- [x] **AC-0016.** Across the two roots
  `tests/roster/test_load_bearing_claim_routing_surfaces.py` scans —
  `packs/core/.apm/skills` and `guides` — the surface in AC-0015 is the only
  one carrying the full set of three routing keys. Coverage is exhaustive
  over those two roots and is not claimed beyond them.
- [x] **AC-0024.** Each surface the same suite names as a pointer carries the
  `load-bearing-claim-routing` anchor and no routing-table row. This is a
  row-level claim about those named surfaces only; AC-0016 is a
  whole-table claim about the two roots.
- [x] **AC-0017.** The `reaches-the-contract` destination states that the
  bounded spike is proportionate to what the claim's falsehood would cost.
- [x] **AC-0018.** `work-loop/SKILL.md`'s DECIDE step obliges classifying a
  sustained finding's cause as task-level or LLD-level before an answer is
  taken, and states that an unresolved cause depth authorizes no repair.
- [x] **AC-0019.** `work-loop/SKILL.md` states that an LLD-level cause takes
  the `repair-the-generator` rung, that the rung's instances are the tasks
  named by the implicated sub-section's `Owned by:` field, and that the
  correction is routed by AC-0012 and AC-0013 rather than by editing the
  sealed plan.
- [x] **AC-0020.** `assets/plan.md` carries a conditional prompt for each of
  these five design dimensions, each in the sub-section named beside it:
  concurrency, consistency, locking, atomicity, and transaction boundaries in
  `### State & control flow`; stable error classes, retryability, and external
  failure mapping in `### Failure, edge cases & resilience`; a concrete
  observability surface in `### Quality attributes (NFRs)`; backfill
  checkpointing, restartability, and cutover validation in `### Data &
  schema`; and named test seams for crossed boundaries in
  `### Interfaces & contracts`. Each prompt is conditional on the spec's
  `Shape:` selecting its sub-section.
- [x] **AC-0023.** `packs/core/.apm/skills/new-spec/assets/plan.md`'s
  working-material paragraph states that its in-place correction permission
  for `Design` applies before approval only, because `plan.md` is hashed
  whole; after approval the two cases route by AC-0012 and AC-0013. The
  paragraph's separate claim about which fields a completion gate reads is
  unchanged.
- [x] **AC-0021.** Each of these texts is byte-identical to its form at this
  spec's base ref: the four pre-existing traversals in the AC-0002 list; every
  pre-existing `Traces to:` line in `assets/plan.md`; the routing table's
  reversibility condition; the `reaches-the-contract` destination's
  pre-existing sentences; and the span `_5A_DIGEST` pins.
- [x] **AC-0022.** `packs/core/.apm/skills/new-spec/SKILL.md`'s body, counted
  from the line after its closing frontmatter delimiter to end of file, is at
  most 900 lines; a body of 901 lines fails. The enforcing check is the
  line-count assertion added by the task that owns this criterion.

## Follow-ons

- Extending the `Tests:` walk from coverage to oracle is delivered, by
  `1ee13a99e` (#1369), independently of this spec. A `Tests:` bullet now owes
  the production seam its check drives. The re-measure this follow-on called
  for held: the gap was seam naming, not oracle-versus-proxy guidance, which
  the walk already carried.
- Reconcile the task-boundary walkers beyond AC-0009's pattern fix.
  `loop-cohort.py`'s `walk_task_sections` runs the final task to end of file,
  so `## Rollout`, `## Risks`, and `## Changelog` fall inside the last task's
  section hash; the lint already ends a task body at the next level-two
  heading. Owner: eugenelim.
- Detect removal of a previously owned design decision. Per-artifact opt-in
  cannot see a participating plan that deletes both a sub-section's body and
  its `Owned by:` field, because the remaining evidence is indistinguishable
  from a sub-section that was always empty. Owner: eugenelim.

## Assumptions

- Product: whether an adopter repository's plans carry enough `## Design
  (LLD)` content for the down-edge to bind there as it does here. The corpus
  evidence is this repository's plans; an adopter's distribution is unmeasured.
  It would change whether the AC-0003 rule needs an adopter-facing opt-out.
  Only an adopter's own corpus can settle it.
