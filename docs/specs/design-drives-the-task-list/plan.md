# Plan: the design drives the task list

- **Status:** Done <!-- Drafting | Executing | Done -->
- **Spec:** [`spec.md`](spec.md)

## Approach

Add the missing down-edge as a declared field rather than an inferred one. The
LLD already carries an up-edge per sub-section (`Traces to:`), so the down-edge
is its mirror (`Owned by:`), and the lint crosses declared task IDs against
defined task headings the same way it already crosses a criterion identifier
against task entries. The semantic obligation — that every interface, type,
symbol, or ownership decision has an owning task — stays in the pre-review
walk, because no parser can decide it.

The in-flight cases separate rather than merge. The lifecycle reference today
admits an observation to the ledger and sends a genuine plan error to
controlled amendment, and those two sentences currently have to carry a
distinction they do not name. Grounding arriving for a seam the plan itself
recorded as `no stub (implementation-discovered)` is the observation case: the
plan predicted the discovery, so recording it is not a correction. A decision
that approval settled and execution falsified is the error case, and ADR-0099
priced it deliberately. The approval digest is therefore not rescoped and no
new cheap route is created.

## Constraints

- ADR-0099 D5–D7 keeps all sealed-baseline mutation inside the delivery
  engine, and its alternatives section rejects bounded advisory plan edits.
  The digest is not rescoped and the ledger gains no error-carrying role.
- `_5A_DIGEST` in `packs/core/tests/skills/new-spec/test_load_bearing_claim_grounding.py`
  byte-pins step 5a of `new-spec/SKILL.md`, spanning `_5A_START` to `"\n6. "`.
  That span belongs to another brief's slice and stays untouched.
- The same suite pins the routing table at three rows, its key set as a
  fixture, and the two exception routes' disjointness discriminator. This
  change adds no row, so all three stay green.
- `tests/roster/test_load_bearing_claim_routing_surfaces.py` allows exactly one
  shipped surface to carry the routing table and is the exhaustive-coverage
  mechanism the spec cites.
- CAT-S003 errors above 1,000 body lines and warns above 500.
  `new-spec/SKILL.md` measured 754 body lines at this plan's base ref, so the
  spec's 900-line budget reserves 100 lines of the 246 available.
- The approval digest is `canonical_contract(..., ac_section_only=(path.name
  != "plan.md"))` in `_loop_guards.py`, so `plan.md` is hashed whole. The spec
  states the behavior; this is the expression that produces it.
- `packs/core/.apm/skills/` is the source; `.claude/` and `.agents/` are
  projections rebuilt by `make build-self`.

## Construction tests

Every task states its `Tests:` before its `Approach:`. Prose assertions live in
the pack's existing skill-content suites
(`packs/core/tests/skills/new-spec/`, `packs/core/tests/skills/work-loop/`);
the lint's own suite is
`packs/core/tests/skills/new-spec/test_lint_contract_item_alignment.py`.

## Durable-output map

| Task | Durable output | Evidence |
| --- | --- | --- |
| T1, T2 | `assets/plan.md` template fields and prompts | shipped template text |
| T3, T4 | `new-spec/SKILL.md` traversal and routing destination | shipped skill text |
| T5 | lint finding kinds and task-ID pattern | `FINDING_KINDS` and `TASK` |
| T6, T7 | `work-loop` DECIDE rungs and the two-case in-flight split | shipped skill and reference text |
| T0 | corpus counts | `notes/verification-ledger.md` |
| T8 | preservation proof and released-artifact entry | byte comparison, `docs/product/changelog.md` |

## Design (LLD)

### Design decisions

The down-edge is declared, not inferred. A lint that scraped backticked
symbols out of LLD prose and hunted them in task bodies would be a lexical
proxy for a semantic claim, and would fire on every incidental mention. The
declared field moves the judgment to the author, where the pre-review walk
already sits, and leaves the machine checking only field integrity.

Rejected: a fourth routing-table row for in-flight correction. The three
existing rows all answer "you cannot settle this claim now"; a post-approval
falsification answers "this was settled and is now false", which is a
different rule rather than a fourth case of the same one. Keeping it out of
the table also leaves the table's fixture, disjointness, and vacuity pins
untouched.

Rejected: widening `cheap-with-an-oracle`'s reversibility condition to admit a
low-stakes irreversible detail. Reversibility exists to remove exactly the
stakes judgment that widening reintroduces. The residual route's cost is what
was wrong, so the destination states proportionality instead.

Rejected: routing a falsified settled decision to the ledger. That is the
advisory path ADR-0099 rejected, reached by a different name.

Traces to: AC-0015, AC-0017, AC-0013 · contracts/: none
Owned by: T4, T7

### Data & schema

`Owned by:` holds a comma-separated list of task IDs matching `T[0-9]+[a-z]?`.
`loop-cohort.py`'s `TASK_HEADING_RE` already accepts that suffix; the lint's
`TASK` pattern does not, capturing only `T[0-9]+` in both its group and its
lookahead. A suffixed heading is therefore absent from the lint's defined-task
set today, which would make a correct `Owned by: T2a` resolve to nothing. The
pattern is widened rather than the field narrowed, because the two walkers
disagreeing is the defect.

No new identifier space is created: the field reuses task IDs, so nothing
needs a uniqueness or retirement rule.

Traces to: AC-0001, AC-0004, AC-0009 · contracts/: none
Owned by: T1, T5

### Interfaces & contracts

The lint gains two finding kinds in `FINDING_KINDS`, the catalogue every
message is formatted from, so each rule's wording keeps one home. Both read
the plan text alone and join `PLAN_GATED`, whose members `check()` places in
its no-input return value exactly when `plan.md` is falsy. Neither reads a
base ref, so neither touches `_changed_lines`.

Named test seams for crossed boundaries: the boundary is
`check(spec_dir, root, since, no_since_reason)`, whose four-value return
separates failing findings, whether the check ran, rules with no input, and
findings that report without failing. Both new rules are exercised through
`check` rather than through their own helpers, because the tier a finding
lands in is part of what is being asserted.

Traces to: AC-0003, AC-0006, AC-0007 · contracts/: none
Owned by: T5

### Failure, edge cases & resilience

Three cases must not produce a failing finding: a plan with no
`## Design (LLD)` section, a sub-section scaffolded but empty, and a plan
where no sub-section carries `Owned by:` at all. The first is the
one-directional constraint — at this plan's base ref, 921 of the repository's
2,511 task headings sat in the 183 plans with no LLD section. The third
grandfathers the corpus: a plan opts in by carrying the field once, and the
updated template makes every new plan opt in from birth.

A plan predating the field is named in the reported-not-failing output rather
than passing silently, because a rule that runs on nothing and reports nothing
is the partial-read-as-clean failure the module exists to detect.

The known hole is deletion. A participating plan can remove both a
sub-section's body and its `Owned by:` field and still pass, because what
remains is indistinguishable from a sub-section that was always empty.
Detecting it needs forward-only evidence across revisions, which would
reintroduce the base-ref dependency this design removed; it is a follow-on,
not a criterion here.

Traces to: AC-0005, AC-0008, AC-0010 · contracts/: none
Owned by: T0, T5

### Quality attributes (NFRs)

Observability surface: the run prints per-rule counts, the reported-not-failing
list, and the no-input reason, so a caller can distinguish zero findings from a
rule that had no input. The corpus run records counts in the ledger rather
than only a pass verdict.

Size: the spec budgets `new-spec/SKILL.md` at 900 body lines against
CAT-S003's 1,000-line error, and the enforcing assertion fails a 901-line
body.

Traces to: AC-0011, AC-0022 · contracts/: none
Owned by: T0, T8

## Tasks

### T0: measure the two predicates over the recorded corpus

**Tests:** goal-based check. Verifies AC-0010 and AC-0011. A throwaway probe
implements the spec's presence and resolution predicates and runs over every
`docs/specs/*/plan.md`, reporting plan count, LLD-bearing plan count,
sub-sections with body content, participating plans, and plans predating the
field.
**Done when:** `notes/verification-ledger.md` holds those five counts with a
run date, and the failing-finding count it records is zero.
**Depends on:** none
**Approach:** the probe is not committed. Its purpose is to disconfirm the
rule's shape before the rule is written. An earlier probe of this kind already
falsified a change-scoped design; its result is in the ledger.
**Touches:** `docs/specs/design-drives-the-task-list/notes/verification-ledger.md`

### T1: add `Owned by:` to the LLD sub-sections

**Tests:** TDD. Verifies AC-0001. Assert every `### ` sub-section under
`## Design (LLD)` in `assets/plan.md` documents an `Owned by:` field whose
documented value is a comma-separated list of task IDs matching
`T[0-9]+[a-z]?`.
**Done when:** `assets/plan.md` carries the field in all nine sub-sections and
its retention paragraph is unchanged.
**Depends on:** T0
**Touches:** `packs/core/.apm/skills/new-spec/assets/plan.md`,
`packs/core/tests/skills/new-spec/`

### T2: add the five conditional design prompts

**Tests:** TDD. Verifies AC-0020. Assert each of the five dimensions appears
in the sub-section the criterion names, and that each prompt is marked
conditional on `Shape:`.
**Done when:** `assets/plan.md` carries five new prompts, one per named
sub-section, and no sub-section gained an unconditional obligation.
**Depends on:** T1
**Touches:** `packs/core/.apm/skills/new-spec/assets/plan.md`,
`packs/core/tests/skills/new-spec/`

### T3: add the fifth pre-review traversal

**Tests:** TDD. Verifies AC-0002. Assert the "Walk the whole plan once before
review" list carries a traversal naming `## Design (LLD)` and an owning task.
**Done when:** the list holds five traversals and the paragraph reads as one
sentence per traversal.
**Depends on:** none
**Touches:** `packs/core/.apm/skills/new-spec/SKILL.md`,
`packs/core/tests/skills/new-spec/`

### T4: state the residual route's proportionality

**Tests:** TDD. Verifies AC-0015, AC-0016, AC-0024 and AC-0017. Assert the
`reaches-the-contract` destination states the spike is proportionate to what
the claim's falsehood would cost; assert the table still has exactly three
rows with the fixture's three keys; run the roster surface suite to confirm no
other shipped surface carries a row.
**Done when:** the destination carries the proportionality sentence, the table
is unchanged in row count and keys, and the inherited routing suite passes
without a fixture or digest edit.
**Depends on:** none
**Approach:** additive text only. The existing semantics are pinned with
`assertIn`, so a sentence added to the destination keeps them green while a
rewrite would not.
**Touches:** `packs/core/.apm/skills/new-spec/SKILL.md`,
`packs/core/tests/skills/new-spec/`

### T5: add the two `Owned by:` lint rules and widen the task-ID pattern

**Tests:** TDD, through `check()` rather than the helpers. Verifies AC-0003,
AC-0004, AC-0005, AC-0006, AC-0007, AC-0008 and AC-0009. Red cases: a
participating plan whose other filled sub-section carries no `Owned by:`; an
`Owned by:` naming an undefined task ID. Green cases: a plan with no
`## Design (LLD)`; an empty sub-section; a plan carrying no `Owned by:`
anywhere; a task no sub-section names; an `Owned by:` present but empty.
Tier cases: a predating plan appears in `check()`'s reported-not-failing
value, and both rules appear in its no-input value in each of the three
empty-text cases — absent, refused, and present-but-empty — and in no other
case. Suffix case: a
`### T2a` heading resolves an `Owned by: T2a`.
**Done when:** both kinds appear in `FINDING_KINDS`, `TASK` admits the suffix
in group and lookahead, and `lint-finding-coverage.py` reports no rule whose
message no test observes.
**Depends on:** T1
**Touches:** `packs/core/.apm/skills/new-spec/scripts/lint-contract-item-alignment.py`,
`packs/core/tests/skills/new-spec/test_lint_contract_item_alignment.py`

### T6: add cause-depth classification to DECIDE

**Tests:** TDD. Verifies AC-0018 and AC-0019. Assert DECIDE obliges
classifying a sustained finding's cause as task-level or LLD-level, states
that an unresolved cause depth authorizes no repair, and routes an LLD-level
cause to `repair-the-generator` with the implicated sub-section's `Owned by:`
tasks as its instances.
**Done when:** the DECIDE step carries the classification obligation and the
existing rung vocabulary is unchanged.
**Depends on:** none
**Touches:** `packs/core/.apm/skills/work-loop/SKILL.md`,
`packs/core/tests/skills/work-loop/`

### T7: separate the two in-flight cases

**Tests:** TDD. Verifies AC-0012, AC-0013 and AC-0014. Assert the lifecycle
reference routes declared-ungrounded grounding to the ledger and a falsified
settled decision to controlled amendment, naming the ledger as not a route for
the latter. Separately assert two `plan.md` texts differing only outside
`## Acceptance Criteria` produce different approval digests.
**Done when:** the reference distinguishes the two cases in its own words, and
the digest assertion fails if `ac_section_only` is ever made true for
`plan.md`.
**Depends on:** T6
**Touches:** `packs/core/.apm/skills/work-loop/references/delivery-contract-lifecycle.md`,
`packs/core/tests/skills/work-loop/`

### T9: reconcile the template's working-material paragraph

**Tests:** TDD. Verifies AC-0023. Assert `assets/plan.md`'s working-material
paragraph states that an in-place `Design` correction moves the plan's
approval digest, and routes the two post-approval cases to the ledger and to
controlled amendment respectively. Assert its existing sentence about what a
completion gate reads is byte-identical to its base-ref form.
**Done when:** the paragraph names both cases and no longer reads as a blanket
permission to edit `Design` after approval without consequence.
**Depends on:** T7
**Approach:** the paragraph is right that `Design` is not what a completion
gate reads, and that stays. What it cannot also say is that an implementer
corrects it in place after approval, because `plan.md` is hashed whole and
the transition guard refuses the edit. The permission is bounded to the
drafting phase and the post-approval cases are routed instead.
**Touches:** `packs/core/.apm/skills/new-spec/assets/plan.md`,
`packs/core/tests/skills/new-spec/`

### T8: prove preservation, hold the budget, rebuild the projections

**Tests:** goal-based check. Verifies AC-0021 and AC-0022. Byte-compare each
text the preservation criterion enumerates against its form at the base ref.
Count `new-spec/SKILL.md`'s body from the line after its closing frontmatter
delimiter and assert at most 900, with a 901-line body failing.
**Done when:** every enumerated text is byte-identical, the body count is at
or below 900, and `make build-self` leaves the `.claude/` and `.agents/`
projections matching the pack source with no unexpected drift in
`git status`.
**Depends on:** T2, T3, T4, T5, T6, T7, T9
**Touches:** `packs/core/tests/skills/new-spec/`, `.claude/skills/`,
`.agents/skills/`, `docs/product/changelog.md`

## Rollout

No runtime surface changes. The template and skill edits reach adopters
through the next core pack release. The rules are per-artifact opt-in, so an
adopter's existing plans produce no new findings at all; a plan participates
once it carries `Owned by:`, which the updated template supplies.

## Risks

- The declared field checks integrity, not the semantic obligation. A plan can
  satisfy every lint rule and still leave an individual design decision
  unowned. The pre-review walk is the only control for that, and it is
  instructed. The spec's Outcome is written to the declared property rather
  than the semantic one, so no criterion claims the lint decides it.
- Per-artifact opt-in means a plan that never adopts `Owned by:` is never
  checked, and a participating plan can delete an owned decision silently.
  Accepted as proportionate with the detection gap recorded as a follow-on.
  Measured before this design was fixed: 53 of the 106 recent commits touching
  a `plan.md` changed a line inside `## Design (LLD)`, so the change-scoped
  alternative would have fired on half of them against a corpus where no plan
  carried the field.
- The lint is skill-invoked, not gated. Its only automated exercise is a
  dispatch-only roster test, so a regression in the new rules can reach main.
  T5 adds cases to the pack's own suite, which does run on a PR.
- `make build-self` refuses a dirty tree, so T8 sequences after every editing
  task rather than beside them.

## Changelog

- 2026-09-18: spec approved by eugenelim
- 2026-09-18: plan approved by eugenelim
