# Plan: acceptance-criteria set construction

- **Spec:** [`spec.md`](spec.md)
- **Status:** Drafting <!-- Drafting | Approved | Executing | Done -->
- **Repository anchors:** `packs/AGENTS.md` and `packs/core/AGENTS.md` for the
  `.apm/` export boundary and the version bump rule; `guides/AGENTS.md` and
  `contracts/guide.schema.json` for the guide surface. Analogous
  implementations: the rubric candidate at
  `packs/core/.apm/skills/new-spec/references/spec-authoring-rubric.md` (prose
  shipped into the same skill, wired from two surfaces) and
  `docs/specs/shaping-review-contracts/` (skill-prose slice with pack-local
  pinning tests). Construction path: `packs/core/tests/skills/new-spec/`.
  **Owner search, recorded:** criterion *shape* already has an owner
  (`assets/spec.md` § Acceptance Criteria) and per-criterion *diagnosis* already
  has one (the rubric). No owner exists for obligation *selection* — the brief
  records that as measured on 2026-09-02, and this plan re-checked it by reading
  the six files in `guides/core/reference/`. So the procedure is authored here,
  and every shape or diagnosis question is cited rather than restated.

> **Plan contract:** this is the implementation strategy. It may change
> substantively only while its Status is `Drafting`, before approval records its
> baseline. After approval, `spec.md` and `plan.md` are pinned in substance;
> only lifecycle bookkeeping is permitted, and execution observations belong in
> `docs/specs/<feature>/notes/verification-ledger.md`.

## Approach

Five layers, in dependency order. The procedure lands as prose in the existing
acceptance-criteria step of `packs/core/.apm/skills/new-spec/SKILL.md`; the
adopter-facing guide follows it; three frozen cases and their seed pins land in
the pack's eval register and pack-local suite; the recorded run discharges the
delivery gate; the release surface closes last, in one commit, because
`make build-self` refuses a dirty tree.

The riskiest part is calibrating the assertions, not writing the prose. The
single-homing suite asserts each pinned rule sentence appears in exactly one of
four authoring surfaces, so any phrasing that echoes an owned rule reds it — but
the 5a probe measured zero collisions for a naturally-worded draft, so that is a
residual risk rather than the leading one. What the probe *did* find is that a
count-threshold assertion scoped to the whole file reds on two lines of correct
shipped text, so the count and ordering assertions need the span scoping T1
carries. Extending the suite's pinned rule set in the same task as the prose is
still what keeps citation honest: a later edit that pastes an owned rule into the
procedure reds immediately rather than at review.

The second risk is the eval register. It is a frozen case list that no CI job
runs, so a case is only as good as the assertions pinning its seeded material.
The seed pins go in before the cases, red, so a case that silently stops grading
its gap cannot ship green.

## Constraints

- `packs/AGENTS.md` § *Version bump rule* — a `.apm/**` content change bumps
  `pack.toml` and `.claude-plugin/plugin.json` to the same version.
- `packs/AGENTS.md` § *Shipped pack content carries no internal-governance
  citations* — the procedure names no repository-only path, record or criterion.
- `packs/AGENTS.md` § *Self-hosting projection* — `.apm/` is the source; run
  self-host and commit source and projection together.
- `docs/CONVENTIONS.md` § *5c `guides/`* and § *Phase-slice planning* — the
  guide ships in the same slice as the tooling.
- Owner decisions recorded in
  `docs/product/briefs/agent-authoring-input-quality.md` § "Constraints /
  Appetite": no dependency on the guidance-activation measurement, and no fixed
  numerical criterion cap.
- Standing owner decision, 2026-08-18: a model-in-the-loop measurement runs
  in-agent through fresh subagents, never via an API key or SDK call.

## Construction tests

**Integration tests:** none beyond per-task tests. The four validation
commands the delivery uses are the repository's existing gates, listed under
Rollout.

**Manual verification:** the recorded three-case run in T4. One fresh subagent
per case, so three runs are three independent samples rather than one sample and
two recollections.

## Durable-output map

| Durable output | Tasks | Implementation evidence | Closeout evidence |
| --- | --- | --- | --- |
| User-facing promise → `guides/core/reference/acceptance-criteria-authoring.md` | T2 | The content check over the page body, plus `validate_guides.py`, `check-guide-index.py` and `lint-guide-titles.py` all OK | Page exists, is scoped to set construction, and cites the shape owner |
| Reusable learning → `docs/specs/acceptance-criteria-set-construction/notes/` | T4 | The recorded run's per-candidate disposition table | T4's `Done when`, which owns the passing condition |
| Release history → `docs/product/changelog.md` | T5 | Free-standing topmost `core` section at the bumped version | `test_core_version_and_okf_declaration_are_synchronized` green |
| Current product truth → the brief's § "Spec map" | T5 | `lint-brief-coverage.py` resolves this spec through its `Brief:` header | Roll-up names this spec; nothing hand-written into the brief |

## Design (LLD)

### Design decisions

- **Extend the existing acceptance-criteria step rather than add a reference
  file.** The rubric earned its own file because it is worked per defect and
  re-read; a five-step selection procedure runs once, inline, before wording.
  Rejected: a second `references/` file, which splits the AC step's reading
  order across two files for no gain. Traces to: AC1, AC2.
- **The build-discovery destination reuses the plan template's existing
  contract, and is not a new concept.** `assets/plan.md` already requires
  `no stub (implementation-discovered)` plus a discovery predicate, constraint,
  required outcome and verification mode for a seam the build must settle, and
  `SKILL.md` already states that assertion wording is expected to be incomplete
  at approval. What was missing is a *route*: the routing step named five
  destinations and none of them was the build. Rejected: inventing a
  `defer-to-build` disposition with its own fields, which would put a second
  home on a contract that already exists. The four fields are what stop this
  being a licence to under-specify — "we will figure it out" is worse than
  either specifying or omitting, while a stated predicate is a hole of known
  shape. Traces to: AC7.
- **Cite, never restate.** Every shape, diagnosis or repair question in the
  procedure resolves to `assets/spec.md` or the rubric by name. Rejected:
  summarising the conjunction test inline for the reader's convenience — a
  shorter restatement is still a second home. Traces to: AC18.
- **Pin seeds before authoring cases.** Rejected: adding the three cases and
  then a shape test, which cannot fail on the commit that introduces it.
  Traces to: AC20.
- **No scorer script.** The brief adds no durable run schema, so the run is a
  recorded exercise and the counts live in prose. Traces to: AC21, AC27.
- **The observer is named at admission, not at Testing Strategy.** Choosing the
  observing surface later means the criterion enters the checklist before
  anything is known to show its failure, and the gap is then invisible because
  the criterion itself reads fine. Classifying this spec's own seven shaping
  rounds put 11 of 22 sustained findings in exactly that class — a criterion
  with no observer, or an observer narrower than its claim — against 2 for
  wording defects. The commissioned survey names the same gap from the other
  side: the shaping failure classes are all per-criterion, and 29148's
  set-level *able to be validated* has no counterpart in the guidance. Rejected:
  leaving the observer to Testing Strategy and adding a reviewer check, which
  finds the gap one stage after it is cheap to fix. Traces to: AC5, AC10.
- **The count assertion is span-scoped, not a whole-file token deny-list.** A
  pre-review probe on 2026-09-10 ran a candidate deny-list against the shipped
  `SKILL.md` and found `at most` already present in the output-rendering block
  ("Emphasize at most one load-bearing point per section") and `budget` in the
  shaping-review rule ("additionally rejects hard AC word budgets"). Both are
  correct text, so the deny-list would have red on the shipped file. The same
  probe found **zero** 7-word runs shared between a naturally-worded draft of
  the procedure and any of the three owned surfaces, so the single-homing
  collision is smaller than assumed and the ordering and count assertions carry
  more of the weight. Traces to: AC16, AC18.

### Component / module decomposition

Four surfaces, all existing except the guide: the skill's acceptance-criteria
step (new procedure), the pack's eval register (three new entries), the
pack-local suite (new pins plus an extended rule set), and the new guide page.
Nothing new is a module, a dependency, or a directory.

### Behavior & rules

**The procedure span, defined once.** Several assertions below slice the same
region of `SKILL.md`, and naming its bound separately in each is how two of them
came to disagree. The span runs from the **first stage marker** to the **end of
the last stage's text** — not to the last marker, which would put the fifth
stage's body outside the span and leave its interval empty. Every assertion that
slices the procedure cites this definition instead of restating a bound.

The procedure's admission test, routing destinations and set-level checks are
the observable contract and live in `spec.md`. What follows is what the
implementer cannot infer about the assertions that verify them. Each rule is
stated once here; T1's `Tests` cite it rather than repeating it.

**Ordering is two comparisons, not one.** The hand-off's offset must fall
between the routing marker and the set-level pass marker. Comparing against
admission alone is too weak: routing and the pass both follow admission, so
wording could land mid-procedure and still pass. Stage order is one ascending
comparison across all five offsets, not pairwise against neighbours, because a
pairwise walk stays green under a swap of two non-adjacent stages.
Traces to: AC1, AC2.

**A requirement without its consequence reads as advice.** Three criteria pair a
requirement with what happens when it is unmet — composition with
compose-rather-than-check, the observing surface with stays-a-candidate,
bidirectional coverage with the pass failing. Assert both clauses per criterion:
the requirement alone is the form that leaves the existing habit in place.
Traces to: AC3, AC5, AC10.

**The count prohibition must not key on a numeral.** The forbidden shape is a
fixed absolute criterion count — a cap, ceiling, refusal or pass/fail bar. The
permitted shape is a percentile derived from the author's own corpus, used only
to order scrutiny, and the percentile criterion requires one in the same span. A
bare-numeral test therefore forbids what another criterion requires. A
whole-file token deny-list is unavailable either way; see the probe under
*Design decisions*. Traces to: AC17, AC18.

## Tasks

### T1: The selection procedure ships and its rules are single-homed

**Depends on:** none

**Touches:** `packs/core/.apm/skills/new-spec/SKILL.md`,
`packs/core/tests/skills/new-spec/test_acceptance_criteria_discipline.py`

**Tests:**
- `python3 -m pytest packs/core/tests/skills/new-spec -q` — the suite carrying
  every assertion below. Each bullet names its criteria and the observation; the
  rules governing assertion shape are in *Behavior & rules*, cited not repeated.
- **The pin, and what it establishes.** Extend `RULES`, owner `skill`, with one
  pinned entry per criterion in the spec's Testing Strategy goal-based group
  over the skill file. For the eight criteria with no bullet of their own below,
  whose whole claim is that a named sentence is present in the shipped
  procedure, **presence of the pinned sentence inside the procedure span is the
  oracle** and no further assertion is owed. The span matters: the owner test
  searches the whole file, so a sentence moved out of the procedure stays green
  under it, and the per-stage floor only places *some* pinned sentence in each
  interval. Assert span membership for this exact eight-entry set; the mutation
  that must fail is moving one of the eight outside the span while leaving it in
  the file. A reviewer has read this bullet as specifying nothing twice
  now, so the mapping is stated rather than inherited.
- **A per-stage floor over the pinned set — a construction check, not a
  criterion.** At least one pinned sentence falls in each of the five stage
  intervals, the fifth closing at the end of the procedure span. This supports
  **AC1**; it is not a criterion of its own, because its failure would mean the
  tuple lacks a representative sentence rather than that the procedure lacks a
  stage. **Constraint:** `RULES` is a hand-declared tuple the suite iterates, so
  nothing here notices a rule nobody pinned, and whether a sentence states a
  rule is a judgement. The floor bounds that without closing it — do not
  describe it as a derivation.
- **AC1, AC2.** Two offset comparisons over the stage markers.
- **AC3, AC5, AC10.** Both clauses of each criterion — requirement and
  consequence.
- **AC16, AC18.** The count sentence records count and corpus position; the same
  span carries no rejection and states that a set above the p75 passes on its
  obligations alone.
- **AC17.** **Constraint, local to this assertion:** the criterion's content is
  the *difference* between its branches, so a high-branch assertion alone passes
  when the branch is unconditional, and naming a second lower threshold
  reinstates the undefined band the criterion was repaired to remove. One
  threshold, both branches. Assert the percentile condition, the pairwise whole-set uniqueness re-run,
  the record-the-result instruction, and the below-p75 branch.
- **AC17, AC18 together.** Slice the procedure span and assert the absence of a
  fixed absolute criterion count.
- **Exact assertion wording is build-discovered.** The phrases, markers and
  offsets cannot be settled until the procedure prose exists.
  **Discovery predicate:** each assertion is written against the shipped
  sentence once `SKILL.md` is authored. **Constraint:** no assertion keys on a
  bare numeral, and each fails under deletion of the clause it pins.
  **Required outcome:** the suite is red before the prose lands, green after.
  **Verification mode:** goal-based, pack-local suite.

**Approach:**
- Rewrite the AC step's `No Acceptance Criteria` bullet into the numbered
  procedure, keeping its existing pointers to step 9 and step 5 intact — the
  `step-four-pointers` pin and `test_step_pointers_name_headings_that_still_exist`
  both read them.
- Keep every shape and diagnosis question as a citation.

**Done when:** every Tests bullet above is landed as an assertion and
`python3 -m pytest packs/core/tests/skills/new-spec -q` is green. A green suite
missing one of them does not close this task.

### T2: The guide publishes the set-construction section

**Depends on:** T1

**Touches:** `guides/core/reference/acceptance-criteria-authoring.md`,
`packs/core/tests/skills/new-spec/test_acceptance_criteria_discipline.py`

**Tests:**
- `python3 -m pytest packs/core/tests/skills/new-spec -q` — the suite carrying
  the content check below. Without it the check is authored and never executed.
- **AC13 and AC14 — content check, in the pack-local suite.** The three guide validators are
  frontmatter and link gates and cannot observe content, so they do not verify
  this task's contract. Assert over the page body: each of the five procedure
  stage names is present, the criterion-shape owner is cited by document name,
  and no sentence from that owner's pinned rule collection appears in the guide
  body — an exact absence comparison against the named set, not a judgement
  about restatement. Paraphrase is outside this assertion and is a review
  obligation; the criterion was narrowed to match, so test and criterion now
  claim the same thing. The suite reads the guide by
  repository-relative path, the way
  `tests/roster/test_spec_authoring_rubric_brief_boundary.py` reaches across the
  pack boundary. **Constraint, local to this assertion:** assert one operative
  sentence per stage as well as the stage name. A page listing five headings and
  no instruction publishes nothing, and a name-only assertion passes on it; the
  mutation that must fail is deleting a stage's instruction while leaving its
  heading.
- `python3 tools/validate_guides.py`, `python3 tools/check-guide-index.py` and
  `python3 tools/lint-guide-titles.py` all OK — publication, not content. The
  frontmatter keys the schema requires are `title`, `summary`, `pack`, `kind`;
  `title` must equal the leading H1.
- Every link target stays inside `guides/`. A link out renders as an off-site
  GitHub blob URL.

**Approach:**
- Author the page as `kind: reference`, `pack: core`, scoped to selection,
  scenario placement, routing and the set-level pass.
- Leave the per-criterion failure-class section to the slice that owns it; do
  not scaffold an empty heading for it, which would decay.
- No `guide-nav-baseline.toml` row: that registry is transitional and shrinking,
  and a page with `title:` frontmatter needs none.

**Done when:** every Tests bullet above passes. The validators alone are not
sufficient — they are frontmatter and link gates, so a page passing only them
can be missing both guide outcomes.

### T3: Three frozen cases exist and cannot silently stop grading

**Depends on:** T1

**Touches:** `packs/core/.apm/skills/new-spec/evals/evals.json`,
`packs/core/tests/skills/new-spec/test_acceptance_criteria_discipline.py`

**Tests:**
- `python3 -m pytest packs/core/tests/skills/new-spec -q` — the suite carrying
  the per-case assertions below.
- **AC19 and AC20** — one shape-and-seed test per case, following the precedent of
  `test_post_repair_eval_grades_the_four_gaps_the_rubric_gained`: assert the
  entry's key set, id uniqueness across the register, the authoring frame in
  the prompt, and each seeded item's survival. `stub: true` — the contract
  surface compiles and is red before the entries exist:

  ```python
  def test_set_construction_cases_are_frozen_and_seeded() -> None:
      data = json.loads(EVALS.read_text(encoding="utf-8"))
      by_id = {entry["id"]: entry for entry in data["evals"]}
      assert len(by_id) == len(data["evals"])
      for case in (
          "ac-set-construction-small-change",
          "ac-set-construction-large-irreducible-set",
          "ac-set-construction-existing-contract-amendment",
      ):
          entry = by_id[case]
          assert set(entry) == {"id", "prompt", "expected_output", "assertions"}
  ```
- Extend that body per case with the seeded-item pins: one seeded
  implementation detail, one duplicate claim, one example-only variant, and
  every seeded objective and non-waivable guardrail. The construction test is
  the mutation — deleting any one seeded item from a case's prompt must red this
  module — which is why the pins are individual assertions rather than one
  aggregate membership check.
- **AC21** — assert the whole scoring contract appears in each case's `expected_output`:
  recall first, non-criterion rejection second, count descriptive, **and** the
  rule that a smaller set obtained by losing a distinct obligation or guardrail
  is a failure. The ranks without that rule leave the failure condition
  unstated, which is the half AC21 exists for.

**Approach:**
- Author the three prompts as authoring frames, not review frames — the graded
  actor is selecting candidates pre-seal.
- Give the large case a genuinely irreducible obligation set, so a candidate
  that compresses it fails on recall rather than on count.

**Done when:** every Tests bullet above passes, each having been red before the
entries landed and green after, and the full pack suite is green.

### T4: The recorded run discharges the delivery gate

**Depends on:** T3

**Touches:** `docs/specs/acceptance-criteria-set-construction/notes/`

**Tests:**
- **AC27 and AC28** — manual QA, both graded ranks. One fresh subagent per case, given only the shipped
  procedure and that case's prompt, returning its candidate set and
  dispositions.
- Each recorded case carries an explicit candidate count, an explicit final
  count, and a disposition for every candidate. This is the durable output's
  closeout condition, so it is observed here rather than left to Approach —
  Approach is an instruction and no completion gate reads it.
- Read the result against the scoring order: recall of every seeded objective
  and non-waivable guardrail first, then rejection of the seeded
  non-criterion material, then count as a description.

**Approach:**
- Record per case: candidate count, final count, and each candidate's
  `admit` / `merge` / `relocate` / `remove` disposition.
- A smaller set obtained by losing a distinct obligation or guardrail is a
  failure, not a pass — record it as one and stop rather than re-running.

**Done when:** every Tests bullet above is discharged for all three cases and
recorded in `notes/`, and all three pass. A pass on one graded rank does not
close this task, and the count closes nothing.

### T5: The release surface closes

**Depends on:** T1, T2, T3, T4, T6

**Touches:** `packs/core/pack.toml`, `packs/core/.claude-plugin/plugin.json`,
`packs/core/tests/skills/new-spec/test_acceptance_criteria_discipline.py`,
`docs/product/changelog.md`, `workspace.toml`,
`.agents/`, `.claude/`

**Tests:**
- `python3 .agents/skills/workspace-status/scripts/workspace_status.py reconcile
  --root .` — Type 1, 2 and 3 all 0.
- `python3 .agents/skills/author-delivery-brief/scripts/lint-brief-coverage.py
  --root .` resolves this spec under its brief.
- `python3 .agents/skills/work-loop/scripts/lint-traceability.py --root .` exits
  0. The 433 informational orphans are pre-existing.
- `python3 -m pytest packs/core/tests/skills/new-spec -q` — the suite that
  carries the sweep below. Without this command the sweep has no closing
  oracle: it would be authored, never executed, and the task would still meet
  its gate.
- **AC18 across every shipped surface, not just the procedure span.** T1's
  check slices `SKILL.md` because that is where the percentile trigger and the
  prohibition must coexist. AC18 is wider only in *surface*, not in claim: no
  shipped surface may state a fixed absolute count in the forms the criterion
  lists. The broader statement that a count never proves quality is a
  non-waivable Boundary read at review, and is deliberately **not** attributed
  to this mechanical check — the criterion was narrowed away from it precisely
  because no check reaches it. Assert the prohibition over all three
  surfaces this slice ships — the procedure span, the new guide page, and the
  frozen eval entries — in one check that runs here, after the guide and the
  cases exist.

  **The proxy is named, not implied.** This detects a fixed absolute count in
  the forms the criterion lists — cap, ceiling, budget, refusal, pass/fail bar.
  A differently worded policy with the same effect is outside it and is a review
  obligation. The criterion was narrowed to match, so neither over-claims.

  **Mutation proof required.** Invariant: no shipped surface carries a fixed
  absolute criterion count. Mutation: add `keep specs under 20 criteria` to the
  guide page, outside `SKILL.md`. Expected failure: this check reds naming the
  guide. A check that stays green under that mutation is scoped to the wrong
  surfaces and is not the guard AC18 needs. Restore by editing the sentence out,
  never by `git checkout`.
- `python3 -m pytest tests/roster/test_security_checklists_okf_projection.py -q`
  — reuse, do not rebuild. Its
  `test_core_version_and_okf_declaration_are_synchronized` already asserts
  `plugin.json`'s version equals `pack.toml`'s *and* that the topmost
  `## [core][<version>]` changelog heading carries that same version, which is
  this task's whole release-parity obligation. It lives in `make test`, not
  `build-check`, so a green `build-check` says nothing about it.
- `make build-self` regenerates the projections with no drift.

**Approach:**
- Bump `pack.toml` and `plugin.json` together — patch, since nothing added is a
  new primitive. Diff `origin/main`'s `pack.toml` first: an unpushed peer bump
  to the same version collides silently.
- Give core its own free-standing topmost changelog section. A combined heading
  with another guarded pack leaves that pack's topmost heading on an older
  release.
- Register this spec in `workspace.toml`'s `["ini-002".work].active` with the
  brief as `source.parent`. The parent intent `work-loop-delivery-efficiency` is
  `Accepted` and stays out of every collection — the reconciler rejects a
  terminal Accepted intent.

**Done when:** every Tests bullet above passes, including the pack-local suite
with the cross-surface sweep present and its mutation proof recorded and
restored, and `make build-self` leaves no drift. Counting the commands here is
what went stale when one was added.

### T6: The review-response protocol ships, and the plan rules come under contract

**Depends on:** T1

**Touches:** `packs/core/.apm/skills/new-spec/SKILL.md`,
`packs/core/tests/skills/new-spec/test_acceptance_criteria_discipline.py`

**Tests:**
- `python3 -m pytest packs/core/tests/skills/new-spec -q` — the suite carrying
  every assertion below.
- **AC22 — already shipped, asserted here. Two gaps close first:** the
  whole-plan-walk rule has no pinned entry, so add one; and the existing owner
  test searches the whole skill file, so a rule moved out of the plan step would
  stay green. Add a span-scoped assertion that all six occur inside the plan
  step, with a mutation moving one rule outside it that must fail. The six plan-authoring rules
  landed in core 2.25.14 ahead of this contract; that was a recorded deviation,
  and this task closes it by bringing them under the spec rather than by
  re-shipping them. **Five are already pinned; the sixth, the whole-plan walk,
  is added by this task.** The completed assertion inspects that six-entry
  mapping, span-scoped to the plan step, and checks the prose still reads as the
  criterion states. No new rule prose is written for this criterion.
- **AC23.** The review step names all **six** responses to a sustained finding —
  repair, narrow, cut, dismiss-and-re-present, repair the generator, route — one
  assertion per response so none can be dropped silently, and
  states that a sustained finding does not by itself require an edit.
  **Constraint, local to this assertion:** assert the disclaimer as well as the
  list. A list of options with no statement that repair is optional leaves
  repair the default by omission, which is the present behaviour.
- **AC24.** The review step states both answers to a claim-reaches-further
  finding and the rule for choosing between them. **Constraint:** assert the
  choosing rule, not just the pair. A pair of options with no basis for choosing
  leaves the author picking by mood, which is the behaviour this criterion
  replaces.
- **AC25.** The stop-decision report carries the trend and, per residual, its
  consequence, its available responses, each response's cost, and any
  protected-class marking. **Constraint:** extend the step that shipped in
  2.25.14 rather than adding a second one — that step already reports the trend
  and each residual's consequence, so a parallel step would put two homes on one
  obligation. What is new is the options and their costs.
- **AC26.** The procedure requires a changed criterion's references and
  verifications to be reconciled in the same round. **Constraint:** assert
  "in the same round, before the round is reported". A propagation rule with no
  timing leaves it to a later pass, and four findings across this cycle were
  exactly that later pass.
- **AC26.** The earn-its-keep test is stated over every criterion rather than
  only those added during review, and is stated to run during rounds rather than
  only after convergence. Assert both scopings; the existing deletion pass
  already reads as a post-convergence pass over review-added items, so a partial
  edit leaves the old reading intact.
- **Exact wording is build-discovered**, on the same predicate, constraint,
  required outcome and verification mode as T1's.

**Approach:**
- Extend the review step rather than adding a new one; the responses belong
  where a finding is already being dispositioned.
- Widen the existing deletion pass in place. A second pass beside it would put
  two homes on one obligation.

**Done when:** every Tests bullet above passes.

## Rollout

- **Delivery:** big bang, fully reversible. The change is prose, JSON entries
  and tests in a versioned pack; rollback is a revert plus a self-host run.
  Nothing is irreversible — no migration, no published event, no external call.
- **Infrastructure:** none.
- **External-system integration:** none. The eval workflow at
  `.github/workflows/pack-evals.yml` is schedule-and-dispatch-only and
  report-only, so it is not a precondition and is not this gate.
- **Deployment sequencing:** the version bump and self-host run come last, in
  one commit, because self-host refuses a dirty tree.

## Risks

- **The single-homing suite reds on correct text.** Selection language and shape
  language overlap in vocabulary, so a well-written procedure can still echo an
  owned sentence. The 5a probe measured this at zero shared 7-word runs, so it
  is a residual rather than the leading risk. Mitigation: extend the pinned rule
  set in the same task as the prose, and treat a red as a signal to cite rather
  than to reword.
- **The single-homing oracle cannot see a paraphrase — named, not closed.** The
  suite compares exact sentences over a hand-listed tuple, so a restatement in
  different words is invisible to it. Per-entry single-homing belongs to the
  suite's own owner test rather than to any criterion here, so this slice
  promises exactly what it delivers. The guide criterion is scoped the same way:
  a shape rule paraphrased onto the guide page is outside its oracle too, with
  the same mitigation.
  The residue is real and accepted: paraphrased duplication is caught at review,
  by the rubric's first class, and by nothing mechanical. Widening the tuple on
  sight is the maintenance habit that keeps the gap small.
- **A count assertion scoped too widely reds on correct text.** Measured, not
  hypothesised — see the probe under *Design decisions*. Mitigation: the span
  slice in T1, and no assertion that reads the whole file for a bare token.
- **Step renumbering strands a pointer.** The AC step carries pointers to step 9
  and step 5, and an existing test anchors both ordinals to their headings.
  Mitigation: do not renumber; if a step is inserted, move the pointer and the
  anchor together.
- **The recorded run is a small sample.** Three cases, one attempt each, is the
  gate the brief specifies and not a general claim. Mitigation: record it as
  three samples and make no portable claim in shipped text.

## Changelog

- 2026-09-10: initial plan.
