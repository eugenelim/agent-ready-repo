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
- **Cite, never restate.** Every shape, diagnosis or repair question in the
  procedure resolves to `assets/spec.md` or the rubric by name. Rejected:
  summarising the conjunction test inline for the reader's convenience — a
  shorter restatement is still a second home. Traces to: AC17.
- **Pin seeds before authoring cases.** Rejected: adding the three cases and
  then a shape test, which cannot fail on the commit that introduces it.
  Traces to: AC21.
- **No scorer script.** The brief adds no durable run schema, so the run is a
  recorded exercise and the counts live in prose. Traces to: AC22, AC23.
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
  more of the weight. Traces to: AC15, AC19.

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
the observable contract and live in `spec.md`. What the implementer cannot infer
is the *ordering constraint the suite must assert*: the hand-off's offset must
fall between the routing marker and the set-level pass marker, so the pin is a
pair of offset comparisons rather than a phrase-presence assertion. Comparing
against admission alone is too weak — routing and the pass both follow
admission, so wording could land mid-procedure and still pass. Traces to: AC2.

## Tasks

### T1: The selection procedure ships and its rules are single-homed

**Depends on:** none

**Touches:** `packs/core/.apm/skills/new-spec/SKILL.md`,
`packs/core/tests/skills/new-spec/test_acceptance_criteria_discipline.py`

**Tests:**
- `python3 -m pytest packs/core/tests/skills/new-spec -q` — the suite carrying
  every assertion below.
- **AC17 and AC18 — the pin, and the floor that makes it non-vacuous.** Extend
  `RULES` in `test_acceptance_criteria_discipline.py`, owner `skill`. The
  existing parametrised owner test gives **AC17** for every entry: present in
  `SKILL.md`, absent from `assets/spec.md`, `assets/plan.md` and
  `references/spec-authoring-rubric.md`. For **AC18** add one assertion that the
  pinned set reaches each of the five stages — reuse the stage markers the AC1
  assertion already locates, and require at least one pinned sentence in each of
  the five intervals. The fifth interval closes at the end of the procedure span
  as *Behavior & rules* defines it; without that bound the fifth stage has no
  next marker and its interval cannot be observed at all.

  **Do not describe this as a derivation.** `RULES` is a hand-declared tuple and
  the test iterates it, so nothing here can notice a rule sentence nobody
  pinned. Whether a sentence states a rule is a judgement and therefore not
  mechanizable: the pinned set is the proxy, and the per-stage floor bounds its
  incompleteness. Three earlier drafts of this bullet failed in different
  directions — one named no criterion, so pinning three of ten satisfied it; one
  named a list of criterion numbers, which went stale a round later; one claimed
  a derivation the tuple cannot perform. The floor is checkable and claims only
  what it checks.

  **Which criteria the pin covers, for traceability only.** One pinned entry per
  criterion in the spec's Testing Strategy goal-based group over the skill file.
  That is a pointer to the spec's list rather than a second copy, so the two
  cannot disagree when a criterion is added. Read it as traceability and not as
  a guarantee: nothing checks that the mapping is complete, which is exactly why
  AC18's floor exists.

  The criterion-specific bullets below add **content** assertions for the
  criteria needing more than presence. None of them replaces the pin.
- Add two offset assertions in the same module. **AC1** — the five stage
  markers appear in the mandated order, asserted as one ascending comparison
  across all five offsets, not pairwise against neighbours. **AC2** — the
  hand-off marker falls strictly between the routing marker and the set-level
  pass marker, asserted as two offset comparisons against those stages rather
  than against admission, per *Behavior & rules*. A phrase-set assertion alone
  stays green through a reordering; an admission-only comparison stays green
  when wording lands mid-procedure, since routing and the pass both follow
  admission.
- **AC3** — the hand-off passage instructs composing from the named parts and
  says plainly that a criterion is not written whole and then tested. Assert the
  composition instruction and the enumeration of parts it composes from; a
  passage naming the parts without the compose-not-check direction is the form
  that leaves the old habit in place.
- **AC5** — the admission step names the observing-surface requirement, *and*
  the span states that a candidate whose observer cannot be named stays a
  candidate. Assert both clauses: the requirement without the consequence reads
  as advice, which is the form that does not change what an author writes.
- **AC10** — the set-level pass states both coverage directions. Assert the
  every-criterion-has-exactly-one-observer direction specifically: the
  every-obligation-is-covered direction already shipped, so an assertion over
  the section as a whole stays green when only the new direction is missing.
- Trace the count assertions to the criteria that now hold them, one each.
  **AC15** — the procedure's count sentence records the count and its corpus
  position. **AC19** — the same span carries no rejection, and states that a set
  above the corpus p75 passes on its obligations alone; assert that second
  sentence by phrase, since it is the only written form of the
  obligations-only pass condition.
- **AC16, positively.** Assert the procedure's span carries the heightened-
  scrutiny action itself, not merely a permitted trigger: the corpus-percentile
  condition, the pairwise whole-set uniqueness re-run, and the instruction to
  record its result. Assert too that the same span states the per-criterion
  check alone applies **below that same p75 position** — one threshold, both
  branches. The criterion's content is the *difference* between the two
  positions, so an assertion on the high branch alone passes when the branch is
  unconditional; and asserting a second, lower threshold would reinstate the
  undefined band the criterion was repaired to remove.
- **AC16's trigger and AC19's prohibition must not collide.** Slice `SKILL.md`
  to the procedure span as *Behavior & rules* defines it, and assert the
  absence of a *fixed absolute* criterion count: a cap, a ceiling, a refusal, or
  a pass/fail bar on how many criteria a spec may carry. Do **not** assert the
  absence of a numeral, and do not treat a numeral-bearing construction as
  disqualifying on its own: AC16 requires a derived corpus-percentile trigger in
  that same span, and a bare numeral test would forbid what AC16 requires. The
  permitted shape is a percentile derived from the author's own corpus and used
  only to order scrutiny; the forbidden shape is an absolute count that decides
  whether a spec passes. A whole-file token deny-list is not available either;
  see the probe under *Design decisions*.

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
- **AC12 and AC13 — content check, in the pack-local suite.** The three guide validators are
  frontmatter and link gates and cannot observe content, so they do not verify
  this task's contract. Assert over the page body: each of the five procedure
  stage names is present, and the criterion-shape owner is cited by document
  name with no shape rule restated. The suite reads the guide by
  repository-relative path, the way
  `tests/roster/test_spec_authoring_rubric_brief_boundary.py` reaches across the
  pack boundary.
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
- **AC20 and AC21** — one shape-and-seed test per case, following the precedent of
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
- **AC22** — assert the whole scoring contract appears in each case's `expected_output`:
  recall first, non-criterion rejection second, count descriptive, **and** the
  rule that a smaller set obtained by losing a distinct obligation or guardrail
  is a failure. The ranks without that rule leave the failure condition
  unstated, which is the half AC22 exists for.

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
- **AC23** — manual QA. One fresh subagent per case, given only the shipped
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

**Depends on:** T1, T2, T3, T4

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
- **AC19 across every shipped surface, not just the procedure span.** T1's
  check slices `SKILL.md` because that is where the percentile trigger and the
  prohibition must coexist. AC19 is wider: no shipped surface may make a
  criterion count reject a spec or prove one well-shaped, and the Boundary
  forbids a fixed absolute count anywhere. Assert the prohibition over all three
  surfaces this slice ships — the procedure span, the new guide page, and the
  frozen eval entries — in one check that runs here, after the guide and the
  cases exist.

  **Mutation proof required.** Invariant: no shipped surface carries a fixed
  absolute criterion count. Mutation: add `keep specs under 20 criteria` to the
  guide page, outside `SKILL.md`. Expected failure: this check reds naming the
  guide. A check that stays green under that mutation is scoped to the wrong
  surfaces and is not the guard AC19 needs. Restore by editing the sentence out,
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
  different words is invisible to it. AC17 is therefore scoped to the pinned set
  and AC18 puts a per-stage floor under it, so together they promise exactly
  what the oracle delivers and no more.
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
