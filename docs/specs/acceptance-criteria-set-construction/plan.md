# Plan: acceptance-criteria set construction

- **Spec:** [`spec.md`](spec.md)
- **Status:** Approved <!-- Drafting | Approved | Executing | Done -->
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
delivery gate; the release surface closes last. Every task that edits `.apm/`
regenerates its projections in the same commit, per the spec's `Always do`:
`make build-self` takes `FORCE=1` on a dirty tree, so a single deferred run was
never required and the earlier rationale claiming otherwise was wrong.

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
| User-facing promise → `guides/core/reference/acceptance-criteria-authoring.md` | T2 | The roster-level content check over the page body, plus `validate_guides.py`, `check-guide-index.py` and `lint-guide-titles.py` all OK | Page exists, is scoped to set construction, and cites the shape owner |
| Reusable learning → `docs/specs/acceptance-criteria-set-construction/notes/verification-ledger.md` | T4 | The recorded run's per-candidate disposition table | T4's `Done when`, which owns the passing condition |
| Release history → `docs/product/changelog.md` | T5 | Free-standing topmost `core` section at the bumped version | `test_core_version_and_okf_declaration_are_synchronized` green |
| Current product truth → the brief's § "Spec map" | T5 | `lint-brief-coverage.py` resolves this spec through its `Brief:` header | Roll-up names this spec; nothing hand-written into the brief |

## Design (LLD)

### Design decisions

- **Extend the existing acceptance-criteria step rather than add a reference
  file.** The rubric earned its own file because it is worked per defect and
  re-read; a five-step selection procedure runs once, inline, before wording.
  Rejected: a second `references/` file, which splits the AC step's reading
  order across two files for no gain. Traces to: AC-0001, AC-0002.
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
  shape. Traces to: AC-0008.
- **Cite, never restate.** Every shape, diagnosis or repair question in the
  procedure resolves to `assets/spec.md` or the rubric by name. Rejected:
  summarising the conjunction test inline for the reader's convenience — a
  shorter restatement is still a second home. Traces to: the `Never do` boundary
  forbidding a rule owned by `assets/spec.md`, `assets/plan.md` or
  `references/spec-authoring-rubric.md` from being restated into a second file,
  and to AC-0015 where that boundary reaches the guide page. No criterion states
  the whole decision, which is why the boundary is cited rather than a number.
- **The count threshold has an owner, and it is not this spec.**
  `references/spec-authoring-rubric.md` § *What belongs here is the ordering and
  the threshold* already owns deriving a threshold from the author's own shipped
  corpus — a defined glob, a status predicate, a stated percentile, dated — and
  owns treating an above-threshold count as a signal to stop and talk, never as
  a refusal. The count-recording criterion was cut on that basis, owner-approved
  2026-09-10; the procedure cites the rubric section instead. **The owner search
  that missed it is the generator defect worth recording:** it read the six
  files in `guides/core/reference/` and never opened the rubric's own threshold
  section, three lines after naming the rubric as the diagnosis owner. The
  single-homing suite could not have caught it either — it compares exact
  sentences, and the duplicate was reworded. An owner search reads the surfaces
  it already cites, not only the surfaces it expects to find an owner in.
  Traces to: AC-0017, AC-0018.
- **Pin seeds before authoring cases.** Rejected: adding the three cases and
  then a shape test, which cannot fail on the commit that introduces it.
  Traces to: AC-0020.
- **No scorer script.** The brief adds no durable run schema, so the run is a
  recorded exercise and the counts live in prose. Traces to: AC-0021, AC-0028.
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
  finds the gap one stage after it is cheap to fix. Traces to: AC-0005, AC-0011.
- **The count assertion is span-scoped, not a whole-file token deny-list.** A
  pre-review probe on 2026-09-10 ran a candidate deny-list against the shipped
  `SKILL.md` and found `at most` already present in the output-rendering block
  ("Emphasize at most one load-bearing point per section") and `budget` in the
  shaping-review rule ("additionally rejects hard AC word budgets"). Both are
  correct text, so the deny-list would have red on the shipped file. The same
  probe found **zero** 7-word runs shared between a naturally-worded draft of
  the procedure and any of the three owned surfaces, so the single-homing
  collision is smaller than assumed and the ordering and count assertions carry
  more of the weight. Traces to: AC-0018.

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
Traces to: AC-0001, AC-0002.

**A requirement without its consequence reads as advice.** Three criteria pair a
requirement with what happens when it is unmet — composition with
compose-rather-than-check, the observing surface with stays-a-candidate,
bidirectional coverage with the pass failing. Assert both clauses per criterion:
the requirement alone is the form that leaves the existing habit in place.
Traces to: AC-0003, AC-0005, AC-0011.

**The count prohibition must not key on a numeral.** The forbidden shape is a
fixed absolute criterion count — a cap, ceiling, refusal or pass/fail bar. The
permitted shape is a percentile derived from the author's own corpus, used only
to order scrutiny, and the percentile criterion requires one in the same span. A
bare-numeral test therefore forbids what another criterion requires. A
whole-file token deny-list is unavailable either way; see the probe under
*Design decisions*. Traces to: AC-0017, AC-0018.

## Tasks

### T1: The selection procedure ships and its rules are single-homed

**Depends on:** none

**Touches:** `packs/core/.apm/skills/new-spec/SKILL.md`,
`packs/core/tests/skills/new-spec/test_acceptance_criteria_discipline.py`,
`.agents/skills/new-spec/`, `.claude/skills/new-spec/` — projections, regenerated
in the same commit

**Tests:**
- `python3 -m pytest packs/core/tests/skills/new-spec -q` — the suite carrying
  every assertion below. Each bullet names its criteria and the observation; the
  rules governing assertion shape are in *Behavior & rules*, cited not repeated.
- **The pin, and what it establishes.** Extend `RULES`, owner `skill`, with one
  pinned entry per criterion in the spec's Testing Strategy goal-based group
  over the skill file. Five criteria have no bullet of their own below —
  **AC-0004, AC-0007, AC-0008, AC-0010, AC-0016** — and their whole claim is that a
  named sentence is present in the shipped procedure, so **presence of the
  pinned sentence inside the procedure span is the oracle** and no further
  assertion is owed. Each of the seven takes exactly one `RULES` entry keyed to
  its identifier; the sentence itself is build-discovered, but the mapping from
  identifier to entry is fixed here, so propagation can name the entry to
  re-read when one of these criteria changes. The span matters: the owner test
  searches the whole file, so a sentence moved out of the procedure stays green
  under it, and the per-stage floor only places *some* pinned sentence in each
  interval. Assert span membership for this exact five-entry set; the mutation
  that must fail is moving one of the five outside the span while leaving it in
  the file. **AC-0012 and AC-0013 are deliberately not in it:** each states its
  requirement and its separately-failing consequence in *separate* sentences, so
  one contiguous pin leaves the second clause undetectable under deletion,
  against this task's own constraint that every assertion fails under deletion
  of the clause it pins. They take both-clause assertions below. AC-0008 and AC-0016
  stay, each being one contiguous sentence a whole-sentence pin does reach.
- **AC-0006.** Assert the admission step names the surface-guidance walk and states
  the inadmissibility consequence. **Constraint:** assert that the prose reads as
  a walk from the surface's own directory up to the root — "each file found", not
  "the nearest" — and assert the consequence clause separately. A walk stated as
  a single lookup is the defect: a nested scoped file does not replace the one
  above it, so stopping at the first hit skips the rest silently, and the root
  `AGENTS.md` says exactly that. The mutation that must fail is rewriting the
  walk as a nearest-file lookup while leaving the consequence clause intact.
- **A per-stage floor over the pinned set — a construction check, not a
  criterion.** At least one pinned sentence falls in each of the five stage
  intervals, the fifth closing at the end of the procedure span. This supports
  **AC-0001**; it is not a criterion of its own, because its failure would mean the
  tuple lacks a representative sentence rather than that the procedure lacks a
  stage. **Constraint:** `RULES` is a hand-declared tuple the suite iterates, so
  nothing here notices a rule nobody pinned, and whether a sentence states a
  rule is a judgement. The floor bounds that without closing it — do not
  describe it as a derivation.
- **AC-0001, AC-0002.** Two offset comparisons over the stage markers.
- **AC-0003, AC-0005, AC-0011, AC-0012, AC-0013.** Both clauses of each criterion — requirement
  and consequence. For AC-0012 and AC-0013 the two clauses are in separate sentences,
  so each takes two assertions rather than one spanning pin.
- **AC-0018.** The procedure span carries no rejection and states that a set above
  the p75 passes on its obligations alone. The count-recording obligation is the
  rubric's, not this spec's — see the ownership note in *Design decisions*.
- **AC-0017.** **Constraint, local to this assertion:** the criterion's content is
  the *difference* between its branches, so a high-branch assertion alone passes
  when the branch is unconditional, and naming a second lower threshold
  reinstates the undefined band the criterion was repaired to remove. One
  threshold, both branches. Assert the percentile condition, the pairwise whole-set uniqueness re-run,
  the record-the-result instruction, and the below-p75 branch.
- **AC-0017, AC-0018 together.** Slice the procedure span and assert the absence of a
  fixed absolute criterion count.
- **AC-0009.** Assert the pass states its subject as the spec-and-plan pair, assert
  all seven sweep members are named, then assert the plan-side question stated
  for each of the three that carry one — uniqueness, coverage, propagation — and
  the contract carried by propagation and residual freshness. **Constraint on
  the subject clause:** assert that both artifacts are named, not that the word
  "set" appears; a pass whose subject reads as the criteria alone is the one
  that shipped through round 5. **Constraint on scope:** assert the three
  plan-reading members by name and assert no plan-side operation for the other
  four. Asserting a pair-wide reading over all seven would claim a reach the
  prose does not have, which is the defect AC-0024 exists to answer.
  **Propagation:** the
  sentence names the rubric's sibling check as its owner and adds only scope and
  timing — a re-read of each touched criterion's construction test and
  verification entry against that criterion's current wording, completing "in the
  same round, before the round is reported". **Constraint:** assert the citation,
  the read-back scope *and* the timing, never a restated propagation rule. A
  text-search reading passes this spec's own round 5, where two plan tests still
  described pre-repair criteria while every phrase grep came back clean;
  restating the rule here
  is the second home this spec's own Boundary forbids, and a propagation rule
  with no timing leaves reconciliation to a later pass — four findings across
  this cycle were exactly that later pass. **Residual freshness:** the sentence
  requires each recorded residual to be re-tested against current state rather
  than carried forward on its last wording. The mutation that must fail is
  dropping either clause while leaving the member's name in the list.
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
`tests/roster/test_acceptance_criteria_guide_boundary.py`

**Tests:**
- `python3 -m pytest tests/roster/test_acceptance_criteria_guide_boundary.py -q`
  — the module carrying the content check below. Without it the check is
  authored and never executed.
- **AC-0014 and AC-0015 — content check, at repository level, not in the pack suite.**
  This check relates a `guides/` page to a shipped `core` pack file, so it
  crosses the pack boundary. `tools/lint-pack-test-boundary.py`'s
  `pack-tests-stay-in-pack` case rejects a test under `packs/core/tests/` whose
  resolved path climbs above `packs/core`, and the precedent this plan cites,
  `tests/roster/test_spec_authoring_rubric_brief_boundary.py`, says so in its own
  docstring: cross-boundary coverage "cannot live under `packs/core/tests/`".
  A repository-level roster module is the established seam. The three guide validators are
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
`packs/core/tests/skills/new-spec/test_acceptance_criteria_discipline.py`,
`.agents/skills/new-spec/`, `.claude/skills/new-spec/` — projections, regenerated
in the same commit

**Tests:**
- `python3 -m pytest packs/core/tests/skills/new-spec -q` — the suite carrying
  the per-case assertions below.
- **AC-0019 and AC-0020** — one shape-and-seed test per case, following the precedent of
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
- **AC-0021** — assert the whole scoring contract appears in each case's `expected_output`:
  recall first, non-criterion rejection second, count descriptive, **and** the
  rule that a smaller set obtained by losing a distinct obligation or guardrail
  is a failure. The ranks without that rule leave the failure condition
  unstated, which is the half AC-0021 exists for.

**Approach:**
- Author the three prompts as authoring frames, not review frames — the graded
  actor is selecting candidates pre-seal.
- Give the large case a genuinely irreducible obligation set, so a candidate
  that compresses it fails on recall rather than on count.

**Done when:** every Tests bullet above passes, each having been red before the
entries landed and green after, and the full pack suite is green.

### T4: The recorded run discharges the delivery gate

**Depends on:** T3

**Touches:** `docs/specs/acceptance-criteria-set-construction/notes/verification-ledger.md`

**Tests:**
- **AC-0028 and AC-0029** — manual QA, both graded ranks. One fresh subagent per case, given only the shipped
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
recorded in `notes/verification-ledger.md` — the single home
`docs/CONVENTIONS.md` gives an execution-produced observation, so the run cannot
land beside the ledger as a second copy — and all three pass. A pass on one graded rank does not
close this task, and the count closes nothing.

### T5: The release surface closes

**Depends on:** T1, T2, T3, T4, T6, T7

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
- `python3 -m pytest tests/roster/test_acceptance_criteria_guide_boundary.py -q`
  — the module that carries the sweep below. Without this command the sweep has
  no closing oracle: it would be authored, never executed, and the task would
  still meet its gate.
- **AC-0018 across the three surfaces this slice ships.** T1's check slices
  `SKILL.md` because that is where the percentile trigger and the prohibition
  must coexist. AC-0018 is wider only in *surface*, not in claim. Assert the
  prohibition over the procedure span, the new guide page and the frozen eval
  entries, in one check that runs here, after the guide and the cases exist.
  **It lives in the same roster module as T2's check**, for the same reason:
  reading the guide page from `packs/core/tests/` breaches
  `pack-tests-stay-in-pack`. Pre-existing shipped surfaces — `assets/spec.md`,
  the rubric, and `SKILL.md` outside the procedure span — are outside both the
  check and the narrowed criterion, and are recorded as a residual under
  *Risks*. The broader statement that a count never proves quality is a
  non-waivable Boundary read at review, deliberately **not** attributed to this
  mechanical check, because no check reaches it.

  **The proxy is named, not implied.** This detects a fixed absolute count in
  the forms the criterion lists — cap, ceiling, budget, refusal, pass/fail bar.
  A differently worded policy with the same effect is outside it and is a review
  obligation. The criterion was narrowed to match, so neither over-claims.

  **Mutation proof required.** Invariant: no shipped surface carries a fixed
  absolute criterion count. Mutation: add `keep specs under 20 criteria` to the
  guide page, outside `SKILL.md`. Expected failure: this check reds naming the
  guide. A check that stays green under that mutation is scoped to the wrong
  surfaces and is not the guard AC-0018 needs. Restore by editing the sentence out,
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
- The `workspace.toml` entry already exists in `["ini-002".work].queue` with the
  brief as `source.parent`; registration is not this task's work. What closes
  here is the membership move that follows the spec's `Status`, since
  `work.active` requires `Implementing` and `work.shipped` requires `Shipped` —
  the reconciler returns `impossible_transition` on a mismatch. Move the entry
  to `work.shipped` when the `Status` flip happens, not before. The parent intent
  `work-loop-delivery-efficiency` is `Accepted` and stays out of every
  collection: the reconciler rejects a terminal Accepted intent.

**Done when:** every Tests bullet above passes, including the pack-local suite
with the cross-surface sweep present and its mutation proof recorded and
restored, and `make build-self` leaves no drift.

### T6: The review-response protocol ships, and the plan rules come under contract

**Depends on:** T1

**Touches:** `packs/core/.apm/skills/new-spec/SKILL.md`,
`packs/core/tests/skills/new-spec/test_acceptance_criteria_discipline.py`,
`.agents/skills/new-spec/`, `.claude/skills/new-spec/` — projections, regenerated
in the same commit

**Tests:**
- `python3 -m pytest packs/core/tests/skills/new-spec -q` — the suite carrying
  every assertion below.
- **AC-0022 — already shipped, asserted here. Two gaps close first:** the
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
- **AC-0023.** The review step names all **eight** responses to a sustained finding
  — repair, narrow, cut, dismiss-and-re-present, repair the generator, route,
  bound-and-defer, accept-with-reason — one assertion per response so none can
  be dropped silently, and
  states that a sustained finding does not by itself require an edit.
  **Constraint, local to this assertion:** assert the disclaimer as well as the
  list. A list of options with no statement that repair is optional leaves
  repair the default by omission, which is the present behaviour.
- **AC-0024.** The review step states both answers to a claim-reaches-further
  finding and the rule for choosing between them. **Constraint:** assert the
  choosing rule, not just the pair. A pair of options with no basis for choosing
  leaves the author picking by mood, which is the behaviour this criterion
  replaces.
- **AC-0025.** The review step states the surface-guidance finding class and its
  one answer: the criterion changes, and the forbidden content is never authored
  to satisfy it. **Constraint:** assert the prohibition as well as the class. A
  finding class named with no stated answer leaves the author choosing, and the
  choice that reads as cheapest — write the content the criterion demands — is
  the one this repository's round 6 actually produced.
- **AC-0026.** The review step *instructs* the stop-decision report. The oracle is
  the shipped instruction, because nothing in this task observes a produced
  report; an assertion phrased over the report would claim a reach it does not
  have. Assert the instructed fields — the finding trend by round, and per
  residual its consequence, the responses available to it, and what each would
  cost — and assert separately that the step states the protected-risk-class
  condition directly while enumerating no class list. **Constraint on the
  citation:** the assertion reads for the condition, never for a document name.
  `packs/AGENTS.md` forbids shipped pack content from citing this catalogue's
  internal records or repository-only paths, so an assertion demanding that the
  step name `docs/product/intents/work-loop-review-economics.md` is one no
  implementation can satisfy — that owner is named here, in the contract, and
  the pack states the rule. **Constraint:** extend the step that shipped in
  2.25.14 rather than adding a second one — that step already reports the trend
  and each residual's consequence, so a parallel step would put two homes on one
  obligation. What is new is the options and their costs.
- **AC-0027. The `deletion-pass` pin updates with the prose.** That sentence is
  pinned verbatim in `RULES`, so rescoping it reds the existing entry; update
  the entry in the same change, the way this task already declares the
  whole-plan-walk pin addition, so the red reads as planned work rather than a
  regression. The earn-its-keep test is stated over every criterion rather than
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

### T7: The spec template emits identified criteria

**Depends on:** none

**Touches:** `packs/core/.apm/skills/new-spec/assets/spec.md`,
`packs/core/tests/skills/new-spec/test_acceptance_criteria_discipline.py`,
`.agents/skills/new-spec/`, `.claude/skills/new-spec/` — projections, regenerated
in the same commit

**Tests:**
- `python3 -m pytest packs/core/tests/skills/new-spec -q` — the suite carrying
  the assertions below. The asset sits inside `packs/core`, so this check crosses
  no pack-test boundary and stays pack-local, unlike T2's and T5's.
- **AC-0030, the convention.** Assert `assets/spec.md` states each property
  separately — opaque, append-only, spec-directory scoped, assigned once, never
  renumbered on insertion or reorder, never reused after removal, removals
  recorded in a retired list — one assertion per property. **Constraint:** one
  assertion per property, not a single pin over a paragraph. The properties fail
  independently: a template that says "give each criterion an identifier" and
  omits no-reuse ships a convention that silently permits the defect it exists
  to prevent, and a paragraph-level pin stays green through that deletion.
- **AC-0030, the emitted form.** Assert the template's own criteria list carries
  labelled items, so an author copying it inherits the form rather than reading
  about it. **Constraint:** assert the label shape on a template criterion, not
  merely that the word "identifier" appears in the prose. A convention described
  but not demonstrated is one the next author will not follow; this repository's
  own 442 specs are the evidence.
- **Constraint on the prose itself:** `packs/AGENTS.md` forbids shipped pack
  content from citing this catalogue's internal records, so the template states
  the rule directly and names no ADR. The assertion reads for the properties,
  never for a record identifier.

**Approach:**
- State the convention inside the existing `## Acceptance Criteria` comment block
  in the asset, beside the `- [ ]` / `- [x]` notation note it already carries.
  That block already owns notation, so the identifier form belongs to it rather
  than to a new section.
- Adopt it forward-only. The 442 existing spec directories are not renumbered —
  the same basis on which ADR numbering was introduced here.

**Done when:** every Tests bullet above passes and `make build-self` leaves no
drift.

## Rollout

- **Delivery:** big bang, fully reversible. The change is prose, JSON entries
  and tests in a versioned pack; rollback is a revert plus a self-host run.
  Nothing is irreversible — no migration, no published event, no external call.
- **Infrastructure:** none.
- **External-system integration:** none. The eval workflow at
  `.github/workflows/pack-evals.yml` is schedule-and-dispatch-only and
  report-only, so it is not a precondition and is not this gate.
- **Deployment sequencing:** the version bump comes last. Projection
  regeneration does not: each `.apm/`-touching task runs `make build-self`
  (`FORCE=1` on a dirty tree, per `docs/CONVENTIONS.md`) and commits source and
  projections together, which is what the spec's `Always do` requires.

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
- **AC-0018's check reads three surfaces; older shipped surfaces go unread.**
  `assets/spec.md`, the rubric, and `SKILL.md` outside the procedure span carry
  no check for a fixed absolute criterion count. The criterion was narrowed to
  the three surfaces this slice ships so it claims only what its oracle reaches;
  the rest is a review obligation with no mechanical backing. Mitigation: none
  available at proportionate cost — recorded so the gap is visible rather than
  implied by a wider-sounding criterion.
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
- 2026-09-10: owner-approved scope addition — T7 carries the identifier
  convention into the spec template, and this spec's own criteria are the first
  to be labelled. Identifiers assigned 2026-09-10 and frozen from that point;
  the renumbering before that date is history, not retirement, so the retired
  list starts empty.
- 2026-09-10: pre-EXECUTE adversarial review sustained nine findings. Cut the
  count-recording criterion to the rubric that already owned it; moved the two
  cross-boundary checks to `tests/roster/`; gave every `.apm/`-touching task its
  own projection regeneration; bounded AC-0018 to the surfaces its check reads.
