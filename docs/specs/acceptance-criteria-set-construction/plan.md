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

Layered in dependency order, one layer per task in the `## Tasks` order below.
The procedure lands as prose in the existing
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
| Decision rationale → `docs/adr/0108-opaque-append-only-loop-contract-identifiers.md` and this plan's `## Changelog` | T8 (the ADR); T5 (the changelog half) | T8's AC-0032 roster assertion over the ADR's `Confirmation` and `Revisit if`; each delivery decision dated in `## Changelog` | T8's `Done when` already closes the ADR half; the changelog half closes when no owner decision from this delivery is discoverable only from a commit message |
| Interface compatibility → the three checkers' `--help` and module headers | T8 (`lint-contract-item-alignment.py`); T9 (`explore-grounding.py`, `lint-finding-coverage.py`) | Each script's header states its flags and every exit code it can return, and the explorer states its per-probe outcome sets | A header describes no set the code does not have, asserted per script in the task that ships it |

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

The surfaces are the ones each task's `Touches` names, which is the only current
list; all existed before this slice except the guide page and the skill's own
`scripts/` directory. Nothing new is a module or a dependency. The one new
directory is the checkers' `scripts/`, admitted by the owner carve-out in the
spec's *Never do* rather than by this section.

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
- `python3 -m pytest tests/roster/test_tdd_stub_lifecycle_contract.py tests/roster/test_rfc0099_activation_coverage.py -q`
  — the repository-level pins on `SKILL.md`. The pack-local suite cannot reach
  them, so without this command a red this task causes closes green under its own
  `Done when`.
- **The pin, and what it establishes.** Extend `RULES`, owner `skill`, with one
  pinned entry per criterion in the spec's Testing Strategy goal-based group
  over the skill file. Five criteria have no bullet of their own below —
  **AC-0004, AC-0007, AC-0008, AC-0010, AC-0016** — and their whole claim is that a
  named sentence is present in the shipped procedure, so **presence of the
  pinned sentence inside the procedure span is the oracle** and no further
  assertion is owed. Each of the five takes exactly one `RULES` entry keyed to
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
- **AC-0036.** Assert the discovery pass sits after the durable-outputs step and
  before the spec body, that it is seeded by the resolved destinations, and that
  it instructs the result to be recorded. **Constraint on the span:** this
  assertion is scoped to the durable-outputs-to-body boundary, **not** to the
  procedure span every other T1 assertion slices — the pass runs before the
  acceptance-criteria step, so slicing the procedure span would look for it where
  it is not. Assert its offset falls between the two step markers.
  **Constraint on the framing:** assert the prose reads as discovery — what
  already owns and governs these surfaces — and not as a check on a criterion.
  A pass worded as validation reads as something to run after authoring, which
  is the placement this criterion exists to move.
- **AC-0006.** Assert the admission step names every member of the governing
  set — scoped `AGENTS.md`, gates and linters, existing owner documents,
  repository conventions — one assertion per member, iterating the set rather
  than a count of it, then assert the inadmissibility consequence separately. **Constraint on the members:** one
  assertion each, never one pin over the sentence. The members fail
  independently, and the three non-`AGENTS.md` members are the ones that matter:
  this plan's own pre-EXECUTE review sustained three blockers, and each rested on
  a linter, an owner document, or a convention — none on a scoped `AGENTS.md`
  file, all four of which the plan had already cited. **Constraint on the walk:**
  assert the `AGENTS.md` member reads as a walk — "each file found", not "the
  nearest" — because a nested scoped file does not replace the one above it and
  the root `AGENTS.md` says stopping at the first hit skips the rest silently.
  The mutation that must fail is rewriting the walk as a nearest-file lookup
  while leaving the consequence clause intact.
- **AC-0034.** Assert the procedure requires each candidate's disposition to be
  recorded and the two counts that follow from it. **Constraint:** assert the
  disposition record and the counts separately, and assert that the counts are
  stated as following from the dispositions. A count obligation standing alone
  is the corpus-threshold material the rubric owns, and restating it here is the
  second home this contract's own Boundary forbids — the distinction is that
  these counts describe what this selection did, while the rubric's threshold
  describes the author's shipped corpus.
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
  the author's stated threshold passes on its obligations alone, **and states the
  set-not-count authoring rule**: where a set is enumerated, the prose names the
  set and never its cardinality, and no criterion carries a count of the
  delivery's own history. Assert both halves — the rule and the
  history-count prohibition — since prose naming only the first leaves a round
  count admissible. **Constraint:**
  assert against whatever threshold the procedure records, never a percentile
  literal — the rubric that owns derivation says "derive the threshold rather
  than inheriting a number", so pinning one here makes the shipped prose breach
  its own owner. The count-recording obligation is the
  rubric's, not this spec's — see the ownership note in *Design decisions*.
- **AC-0017.** **Constraint, local to this assertion:** the criterion's content is
  the *difference* between its branches, so a high-branch assertion alone passes
  when the branch is unconditional, and naming a second lower threshold
  reinstates the undefined band the criterion was repaired to remove. One
  threshold, both branches. Assert the at-or-above condition against the
  procedure's recorded threshold, the pairwise whole-set uniqueness re-run, the
  record-the-result instruction, and the below-threshold branch — no percentile
  literal in any of the four.
- **AC-0017, AC-0018 together.** Slice the procedure span and assert the absence of a
  fixed absolute criterion count.
- **AC-0009.** Assert the pass states its subject as the spec-and-plan pair, assert
  every sweep member the criterion enumerates is named, then assert the
  plan-side question stated for each member that carries one — uniqueness,
  coverage, propagation — and
  the contract carried by propagation and residual freshness. **Constraint on
  the subject clause:** assert that both artifacts are named, not that the word
  "set" appears; a pass whose subject reads as the criteria alone is the one
  that shipped through round 5. **Constraint on scope:** assert the plan-reading
  members by name and assert no plan-side operation for the remaining members.
  Asserting a pair-wide reading over every member would claim a reach the prose
  does not have, which is the defect AC-0024 exists to answer.
  **Constraint on the consistency member:** assert that it reads the spec's own
  body prose against the criteria, not the criteria against each other, and
  assert separately that it tests the body for narrated delivery history and for
  a count standing beside the set it enumerates. Both decay with no edit at all,
  so a member that reads only criterion-against-criterion never reaches them;
  each ban must red on its own deletion, because one assertion over "the
  consistency member" is satisfied by prose carrying neither ban.
  **Constraint on the shape re-read:** assert that the member cites
  `assets/spec.md` as the owner of the two shape rules and never restates them —
  the spec's *Never do* forbids restating a rule that file owns, so an assertion
  demanding the rule text here is one no implementation can satisfy. Assert the
  re-read obligation and the citation separately. Deleting
  that clause must red this assertion; without it the member reads as a
  criteria-only comparison, and the body statement that contradicted its own
  criteria survived three rounds because nothing looked there.
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


**Grounding:**
- **Three further roster modules name this skill's paths** and were found by
  searching for the touched paths rather than by asking which rules apply:
  `test_spec_review_adjudication_documentation.py` (the review step T6 edits),
  `test_verification_ledger_contract.py` (the assets T7 edits), and
  `test_spec_authoring_rubric_brief_boundary.py`. The mechanical search is
  exhaustive over references-by-path; the semantic sweep that preceded it was
  not, and missed all of them.
- **Two roster modules pin `SKILL.md` prose, and the pack-local suite cannot
  reach them.** `tests/roster/test_tdd_stub_lifecycle_contract.py` pins six
  exact phrases inside step 4 — the step this slice rewrites — and applies a
  seven-phrase deny-list across the whole file;
  `tests/roster/test_rfc0099_activation_coverage.py` pins further `SKILL.md`
  prose. A red in either is invisible to `pytest packs/core/tests/skills/new-spec`,
  so the task's gate names both modules explicitly.
- `skill_spec_lint.py` measures `SKILL.md` body length: **over 500 lines warns,
  over 1,000 errors.** The file is 660 lines today and T1 and T6 both add prose
  to it. Budget against the error ceiling, and treat the warning as already
  breached rather than as headroom.
- `test_acceptance_criteria_discipline.py` `RULES` pins exact normalized prose to
  one owner; `test_step_pointers_name_headings_that_still_exist` pins the step-5
  and step-9 headings; `test_corpus_absence_rule_precedes_the_sign_off_gate` pins
  a relative ordering. Any of the three reds on a careless edit to this step.
- `tests/roster/test_cognitive_load_repository_contract.py` requires exactly one
  rendering start/end marker pair per canonical skill and no internal routing
  references inside that block.
- Owners that must be cited, never restated: `assets/spec.md` (criterion shape),
  the rubric (six failure classes; ordering and the count threshold),
  `assets/plan.md` (construction-test placement).
- `packs/AGENTS.md` — a non-cosmetic pack change also updates that pack's eval
  harness, and shipped prose cites no internal record.

**Approach:**
- Rewrite the AC step's `No Acceptance Criteria` bullet into the numbered
  procedure, keeping its existing pointers to step 9 and step 5 intact — the
  `step-four-pointers` pin and `test_step_pointers_name_headings_that_still_exist`
  both read them.
- Keep every shape and diagnosis question as a citation.

**Done when:** every command this task's `Tests` names is green — named there, not restated here, so the two cannot drift — and every `Tests` bullet above is
landed as its own assertion. A green suite that is missing one of those bullets
does not close this task. `make build-self` also leaves no drift, since this task
edits `.apm/` and the spec's `Always do` requires source and projections to land
together.

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
  about restatement. **The set is loaded from the pack suite under a unique
  pack-and-skill-qualified module name — `importlib.util.spec_from_file_location`
  against the module's path, never a bare import — and never re-declared.** The
  directory carries no package marker and `packs/AGENTS.md` forbids bare-name
  loading of a pack module, so the seam is named here rather than left for the
  build to guess. A
  re-declared copy in `tests/roster/` is protected by no test, drifts silently,
  and is exactly the second home this plan exists to avoid; `SOURCES` in that
  module covers the four pack files only, so nothing would catch the drift. Paraphrase is outside this assertion and is a review
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


**Grounding:**
- **`tools/lint-guides-no-repo-only-refs.py` rejects a guide that links a
  governance path, carries an ADR or RFC token, or references a real
  `docs/specs/<slug>` directory.** The page therefore cannot cite this spec, the
  ADR behind the identifier convention, or any `docs/` path — it states its
  rules directly. This is the single constraint most likely to be breached by an
  author writing the page from the spec.
- `.github/workflows/docs.yml` runs `validate_guides.py` over the real tree and
  requires **0 errors and 0 warnings**; a warning is fatal there even though it
  is not locally.
- `contracts/guide.schema.json` requires `title`, `summary`, `pack`, `kind`,
  rejects any undeclared field, and constrains `kind` to tutorial / how-to /
  reference / explanation. `lint-guide-titles.py` requires the leading body H1 to
  match `title`.
- No registration is owed: `lint-guide-titles.py`, `build-site.py` and
  `check-guide-index.py` all discover pages recursively, `check-guide-index.py`
  checks pack-level links only, and `guide-nav-baseline.toml` is for deletes and
  renames. A titled page needs no baseline row.
- The new roster module is auto-collected by `make test` and `test-roster.yml`;
  there is no roster manifest. Its basename must be unique across suites sharing
  a process.

**Approach:**
- Author the page as `kind: reference`, `pack: core`, scoped to selection,
  scenario placement, routing and the set-level pass.
- Leave the per-criterion failure-class section to the slice that owns it; do
  not scaffold an empty heading for it, which would decay.
- No `guide-nav-baseline.toml` row: that registry is transitional and shrinking,
  and a page with `title:` frontmatter needs none.

**Done when:** every command this task's `Tests` names is green — named there, not restated here, so the two cannot drift — and the validators alone are not
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
- `python3 -m pytest tests/roster/test_cognitive_load_repository_contract.py -q`
  — this task's Grounding records its byte-equality pin over the eval register
  and both projections; without the command that pin is recorded and never run.
- **AC-0019 and AC-0020** — one shape-and-seed test per case, iterating the named
  failure classes rather than a case count, following the precedent of
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


**Grounding:**
- `skill_spec_lint.py` `_check_evals_json` requires a non-empty `skill_name`
  matching the skill, a non-empty `evals` list, unique non-Boolean ids, and
  non-empty string `prompt` and `expected_output`. **There is no id-format rule**
  — the kebab-case ids this plan uses are a local convention, not a validated
  one, so the construction test is their only guard.
- No test fixes the total entry count, so three new entries break no count pin.
- `tests/roster/test_cognitive_load_repository_contract.py` requires every
  publishable pack to keep at least one pinned `cognitive-load-*` eval, and
  requires the register to be byte-identical in both projections after
  self-host.
- `packs/AGENTS.md` — a non-cosmetic pack update updates the eval harness, which
  is what this task is.

**Approach:**
- Author the three prompts as authoring frames, not review frames — the graded
  actor is selecting candidates pre-seal.
- Give the large case a genuinely irreducible obligation set, so a candidate
  that compresses it fails on recall rather than on count. **This is a review
  obligation with no mechanical oracle**, and AC-0019 was narrowed to match:
  nothing in `Tests` observes irreducibility, so the criterion no longer claims
  it.

**Done when:** every command this task's `Tests` names is green — named there, not restated here, so the two cannot drift — and the task's own conditions hold, and `make build-self` leaves no drift, since this task edits `.apm/` and the spec's `Always do` requires source and projections to land together.

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


**Grounding:**
- `docs/CONVENTIONS.md` names `notes/verification-ledger.md` as the home for an
  execution-produced observation and pins an approved spec directory in
  substance, so the run is recorded there and never back into `spec.md` or
  `plan.md`.
- No automated validator reads this ledger path. The `Done when` above is its
  only gate, which is why the per-case contents are stated in `Tests` rather
  than left to `Approach`.

**Approach:**
- Record per case: candidate count, final count, and each candidate's
  disposition **in AC-0008's vocabulary** — admitted, or routed to the plan, to
  Testing Strategy, to an existing owner named, to the body, out of the
  contract, or to the plan as a discovery predicate. A collapsed `relocate`
  loses which named owner a rejected candidate reached, and AC-0010 counts a
  disposition as coverage only when it names that owner. This ledger is the sole
  closeout evidence for the reusable-learning output and cannot be corrected back
  into the pinned contract afterwards.
- A smaller set obtained by losing a distinct obligation or guardrail is a
  failure, not a pass — record it as one and stop rather than re-running.

**Done when:** this task's `Tests` names no command — both its cases are manual QA —
so what closes it is the record: every `Tests` bullet is discharged for all three
cases and written to `notes/verification-ledger.md`, the single home
`docs/CONVENTIONS.md` gives an execution-produced observation, so the run cannot
land beside the ledger as a second copy. All three cases pass. A pass on one graded
rank does not close this task, and the count closes nothing.

### T5: The release surface closes

**Depends on:** T1, T2, T3, T4, T6, T7, T8, T9

**Touches:** `packs/core/pack.toml`, `packs/core/.claude-plugin/plugin.json`,
`tests/roster/test_acceptance_criteria_guide_boundary.py`,
`docs/product/changelog.md`, `web/src/lib/now-highlights.generated.json`,
`workspace.toml`, `.agents/`, `.claude/`

**Tests:**
- `python3 .agents/skills/workspace-status/scripts/workspace_status.py reconcile
  --root .` — Type 1, 2 and 3 all 0.
- `python3 .agents/skills/author-delivery-brief/scripts/lint-brief-coverage.py
  --root .` resolves this spec under its brief.
- `python3 .agents/skills/work-loop/scripts/lint-traceability.py --root .` exits
  0. Its informational structural orphans are pre-existing: compare the count
  against the base ref rather than against a number recorded here, because a
  literal decays between authoring and execution — this one moved from 433 to
  435 during the delivery.
- `python3 tools/build-site.py --journeys-only` then
  `python3 -m pytest tools/test_build_site_routing.py -k now -q` — the `/now/`
  projection this task's `Touches` names. `docs/product/AGENTS.md` requires both
  in the same change as a `### Highlights` block, and the staleness check passes
  silently on a dropped paragraph, so the regeneration is a command here rather
  than a note under Grounding.
- `python3 -m pytest packs/core/tests/skills/new-spec -q` — every assertion the
  skill-editing tasks landed, whichever those are in the task list rather than a
  count restated here. Re-run here because no required remote gate
  reaches this suite, so T5 is the last point at which a red is visible before
  release.
- `python3 -m pytest tests/roster/test_acceptance_criteria_guide_boundary.py -q`
  — the module that carries the sweep below. Without this command the sweep has
  no closing oracle: it would be authored, never executed, and the task would
  still meet its gate.
- **AC-0018 across the surfaces this slice ships.** T1's check slices
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


**Grounding:**
- Four independent checks assert pack/plugin version parity: catalogue lint,
  catalogue verify step 5, `tests/conformance/test_pack_metadata.py`, and
  `tests/roster/test_security_checklists_okf_projection.py`. The last also
  requires the **topmost** `## [core][...]` changelog heading to carry the new
  version.
- `tests/roster/test_workspace_status_projection.py` carries a ratchet rejecting
  any increase in nested dated or versioned releases — the new section is
  free-standing at `##` directly beneath `[Unreleased]`, not nested.
- **If the entry carries a `### Highlights` block**, `docs/product/AGENTS.md`
  requires regenerating `web/src/lib/now-highlights.generated.json` in the same
  commit, checked by `tools/test_build_site_routing.py -k now`. A highlight must
  be a `-` bullet; a paragraph is dropped silently and the staleness check still
  passes.
- `workspace_status_engine.py` gates membership on spec `Status`: `work.active`
  requires `Implementing`, `work.shipped` requires `Shipped`, and `queue` rejects
  both. A mismatch returns `impossible_transition`.
- Core is repo-only, so no root marketplace entry is expected for it.

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

**Done when:** every command this task's `Tests` names is green — named there, not restated here, so the two cannot drift — and the cross-surface sweep
its `Tests` names carries its mutation proof, recorded and restored, and
`make build-self` leaves no drift.

### T6: The review-response protocol ships, and the plan rules come under contract

**Depends on:** T1

**Touches:** `packs/core/.apm/skills/new-spec/SKILL.md`,
`packs/core/tests/skills/new-spec/test_acceptance_criteria_discipline.py`,
`.agents/skills/new-spec/`, `.claude/skills/new-spec/` — projections, regenerated
in the same commit

**Tests:**
- `python3 -m pytest packs/core/tests/skills/new-spec -q` — the suite carrying
  every assertion below.
- `python3 -m pytest tests/roster/test_tdd_stub_lifecycle_contract.py tests/roster/test_rfc0099_activation_coverage.py -q`
  — the repository-level pins on `SKILL.md`. The pack-local suite cannot reach
  them, so without this command a red this task causes closes green under its own
  `Done when`.
- **AC-0022 — partly shipped, asserted here.** Add a span-scoped assertion that
  every rule AC-0022 enumerates occurs inside the plan step, with a mutation
  moving one rule outside it that must fail; the existing owner test searches the
  whole skill file, so a rule moved out of the plan step would otherwise stay
  green. The rules that landed in core 2.25.14 ahead of this contract are a
  recorded deviation, and this task closes it by bringing them under the spec
  rather than re-shipping them. **What is owed is read, never counted:** every
  rule the criterion enumerates that has no prose in the plan step must be
  written, and every one with no pinned entry must gain one. This bullet has now
  twice carried a count of the gap that was false by the round that read it —
  the criterion gained a seventh rule, then an eighth and a ninth — which is why
  the obligation points at the enumeration and the shipped prose rather than at a
  number. The assertion iterates the enumeration for the same reason, so a rule
  added later cannot leave it sized to a stale total.
- **AC-0023.** The review step names every response to a sustained finding
  — repair, narrow, cut, dismiss-and-re-present, repair the generator, route,
  bound-and-defer, accept-with-reason — one assertion per response so none can
  be dropped silently, and
  states that a sustained finding does not by itself require an edit.
  **Constraint, local to this assertion:** assert the disclaimer as well as the
  list. A list of options with no statement that repair is optional leaves
  repair the default by omission, which is the present behaviour.
  **Constraint on the class-count clause:** assert that a finding instantiating
  a contract rule triggers a count of every instance before any repair. Deleting
  that clause must red this assertion. Repairing the reported instance alone is
  what left two further instances of one class standing in this cycle.
  **Constraint on the repair rider:** assert separately that repair obliges a
  sweep of the prose adjacent to a changed artifact outside the contract, and
  that the rider cites AC-0009 for the re-read inside it. Deleting the rider
  must red this assertion; without it the response list reads as complete while
  the companion prose a repair strands is nobody's obligation, which is how a
  docstring came to describe the opposite of the predicate beneath it. Deleting
  that clause must red this assertion. Repairing the reported instance alone is
  what left two further instances of one class standing in this cycle, and the
  walk that clause requires turned a two-instance finding into five.
- **AC-0024.** The review step states both answers to a claim-reaches-further
  finding and the rule for choosing between them. **Constraint:** assert the
  choosing rule, not just the pair. A pair of options with no basis for choosing
  leaves the author picking by mood, which is the behaviour this criterion
  replaces. **Constraint on the second direction:** assert separately that a
  *check* reaching further than any claim — shipped behaviour no criterion
  authorises — is brought under a criterion or cut, and assert the stated reason
  that direction needs saying. One assertion over "both directions" is satisfied
  by prose naming only the first, which is the direction that shows up on its
  own as a criterion nothing verifies; the second is invisible, because the
  artifact works and nothing is failing.
- **AC-0031.** The plan step requires per-task grounding against the governing
  set and requires the task to record what it resolved. **Constraint:** assert
  the per-task scoping and the recording obligation separately, and assert that
  the prose rules out a plan-level anchor list as sufficient. A rule that says
  "ground the plan" is satisfied by the `Repository anchors:` field that already
  exists and that this plan filled in — with three `AGENTS.md` files, a schema
  and two analogues — while missing all three blockers. The mutation that must
  fail is relaxing "each task" to "the plan".
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
  cost — and assert separately that the trend is instructed as a *split*, into
  findings against settled text and findings against text the round changed.
  Deleting the split must red this assertion: an undivided trend satisfies "the
  finding trend by round" while losing the distinction the stop decision turns
  on. Also assert that the step states the protected-risk-class
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
  regression. The conjunction is asserted over each check its siblings define,
  read from that set rather than from a count of it. The earn-its-keep test is
  stated over every criterion rather than
  only those added during review, and is stated to run during rounds rather than
  only after convergence. Assert both scopings; the existing deletion pass
  already reads as a post-convergence pass over review-added items, so a partial
  edit leaves the old reading intact. **Constraint on the naming clause:** assert
  that the prose names the earn-its-keep test *and* states it over both halves of
  the conjunction its siblings define — a criterion names the outcome its failure
  would leave unmet, and no sibling criterion or existing repository control
  already enforces its predicate. Deleting either half must red this assertion:
  named over one half only, the criterion scopes a test the contract never
  establishes.
- **Exact wording is build-discovered**, on the same predicate, constraint,
  required outcome and verification mode as T1's.


**Grounding:**
- **Three further roster modules name this skill's paths** and were found by
  searching for the touched paths rather than by asking which rules apply:
  `test_spec_review_adjudication_documentation.py` (the review step T6 edits),
  `test_verification_ledger_contract.py` (the assets T7 edits), and
  `test_spec_authoring_rubric_brief_boundary.py`. The mechanical search is
  exhaustive over references-by-path; the semantic sweep that preceded it was
  not, and missed all of them.
- **Two roster modules pin `SKILL.md` prose, and the pack-local suite cannot
  reach them.** `tests/roster/test_tdd_stub_lifecycle_contract.py` pins six
  exact phrases inside step 4 — the step this slice rewrites — and applies a
  seven-phrase deny-list across the whole file;
  `tests/roster/test_rfc0099_activation_coverage.py` pins further `SKILL.md`
  prose. A red in either is invisible to `pytest packs/core/tests/skills/new-spec`,
  so the task's gate names both modules explicitly.
- **The review step already carries exact content and order pins** in
  `test_acceptance_criteria_discipline.py` — review persistence, clean-report
  shape, dispatch order and the repair gateway; the executable adjudication path
  and its ordering; the two origin labels and the unresolved-origin stop rule.
  Editing this step reds them unless each is updated deliberately, exactly as
  this task already declares for the `deletion-pass` pin.
- The pinned plan-authoring block in `test_acceptance_criteria_discipline.py` is
  **not** a subset of AC-0022's enumeration: it also pins rules whose prose sits
  in the review step, `owner-gets-decision-facts` among them, which AC-0026
  owns. So the assertion iterates AC-0022's enumeration and matches each rule
  against the block, rather than treating the block as the criterion's rule set —
  reading the block as the set would credit a non-member and silently shrink what
  AC-0022 is checked against.
- The same 500-warning / 1,000-error body-line ceiling applies, and T1 is
  spending from the same budget. The file is 660 lines today.
- The existing plan step, review step and deletion pass are each already located
  in `SKILL.md`; every one of this task's edits extends prose that exists rather
  than adding a sibling home.

**Approach:**
- Extend the review step rather than adding a new one; the responses belong
  where a finding is already being dispositioned.
- Widen the existing deletion pass in place. A second pass beside it would put
  two homes on one obligation.

**Done when:** every command this task's `Tests` names is green — named there, not restated here, so the two cannot drift — and the task's own conditions hold, and `make build-self` leaves no drift, since this task edits `.apm/` and the spec's `Always do` requires source and projections to land together.

### T7: The spec template emits identified criteria

**Depends on:** none

**Touches:** `packs/core/.apm/skills/new-spec/assets/spec.md`,
`packs/core/.apm/skills/new-spec/assets/plan.md`,
`packs/core/tests/skills/new-spec/test_acceptance_criteria_discipline.py`,
`.agents/skills/new-spec/`, `.claude/skills/new-spec/` — projections, regenerated
in the same commit

**Tests:**
- `python3 -m pytest packs/core/tests/skills/new-spec -q` — the suite carrying
  the assertions below. The asset sits inside `packs/core`, so this check crosses
  no pack-test boundary and stays pack-local, unlike T2's and T5's.
- `python3 -m pytest tests/roster/test_verification_ledger_contract.py -q` — that
  module pins exact phrases inside `assets/plan.md`'s plan-contract, `Done when`
  and changelog regions, and this task edits that file. The pack-local suite
  cannot reach it, so a red this task causes would otherwise be invisible to its
  own gate.
- **AC-0030, the convention.** Assert `assets/spec.md` states each property
  separately — opaque, append-only, spec-directory scoped, assigned once, never
  renumbered on insertion or reorder, never reused after removal, removals
  recorded in a retired list — one assertion per property. **Constraint:** one
  assertion per property, not a single pin over a paragraph. The properties fail
  independently: a template that says "give each criterion an identifier" and
  omits no-reuse ships a convention that silently permits the defect it exists
  to prevent, and a paragraph-level pin stays green through that deletion.
- **AC-0030, the verification half.** The convention covers acceptance criteria
  *and* verification items, and a verification item lives in the plan template's
  per-task `Tests:` subsection, not in the spec template. Assert `assets/plan.md`
  carries the same convention for verification items, including that an item's
  identifier is its own and never derived from the criterion or task it serves.
  **Constraint:** this is a second file, not a second home, and the split is
  stated per clause rather than asserted. `assets/spec.md` owns every shared
  property — assigned once, never renumbered, never reused, removals recorded —
  and `assets/plan.md` carries a cross-reference to it plus only what is its
  own: the `VI-` class marker and the independence rule. Identical property
  clauses in both would red `test_acceptance_criterion_rule_has_one_owner`,
  which asserts each pinned phrase is absent from the other three sources.
  **State whether these assertions join `RULES`:** they do, under owner `spec`
  for the properties and owner `plan` for the item-class clauses, the way T6
  declares its own pin interaction. Without it AC-0032's checker has a rule to
  enforce over items no template ever labels.
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


**Grounding:**
- `assets/spec.md` carries its own exact pins:
  `test_worked_example_has_one_owner_and_occurs_once` fixes every worked-example
  label, rationale and exemplar to exactly one occurrence and absence elsewhere,
  and `test_rubric_is_reachable_from_both_authoring_surfaces` pins the asset's
  rubric reference and its "This section owns criterion shape" sentence. Add
  beside them; do not reflow the section.
- `SKILL.md` and the rubric both already defer criterion shape to this asset, so
  the convention goes in the asset and is not restated in either.
- **A pinned sentence enumerates what that block owns, and identifiers are not in
  it.** `RULES` carries, owner `skill`: "`assets/spec.md`'s `## Acceptance
  Criteria` guidance owns the criterion-shape rules, including the independence
  boundary, worked examples, limits, claim minimality, and the mechanism
  give-away." Adding the identifier convention to that block widens what it owns
  past its own stated enumeration, so the pin is extended in the same change —
  the way T6 extends `deletion-pass` — and the assertion checks the enumeration
  still matches the block's contents. Leaving them to diverge is the drift a
  Shipped sibling spec, `spec-authoring-discipline`, holds criteria over: each
  rule resolves to one owning file.
- **Two Shipped specs hold frozen criteria over this file.**
  `spec-authoring-discipline` owns the criterion-shape rules in this block;
  `doc-drift-prevention` owns its status-line comment at line 3, which this task
  does not touch. Neither spec may be edited — a frozen spec takes a status-line
  pointer only — so a collision is resolved by changing this task, never by
  amending theirs.
- **Co-change mining over the seed paths found this task's gap**: `assets/plan.md`
  moves with `assets/spec.md` in 9 of the 36 commits touching either — 25%,
  measured 2026-09-11 with `git log --follow` over both asset paths, which is
  what carries the count across the `docs/_templates/` rename. An earlier
  denominator of 47 counted a base the rename had inflated and understated the
  coupling. Two
  other frequent co-changes were checked and dismissed with evidence — the root
  `.claude-plugin/marketplace.json` carries no `core` entry, and
  `packs/core/README.md` inventories skills rather than their assets or scripts,
  so neither moves for this change.
- `packs/AGENTS.md` — the asset cannot cite the ADR or any internal identifier,
  which is why the convention is stated directly; and changing a shipped asset
  bumps the core pack version.

**Approach:**
- State the convention inside the existing `## Acceptance Criteria` comment block
  in the asset, beside the `- [ ]` / `- [x]` notation note it already carries.
  That block already owns notation, so the identifier form belongs to it rather
  than to a new section.
- **Give the retired list a home the checker can read.** The convention names a
  `## Retired identifiers` heading carrying one bare identifier per list item,
  omitted entirely while nothing has been retired. T8's checker reads that
  heading, so an undefined location leaves its input undetermined and T8 unable
  to start; state the heading and its list shape in the template, not just the
  obligation to keep one.
- Adopt it forward-only. The 442 existing spec directories are not renumbered —
  the same basis on which ADR numbering was introduced here.

**Done when:** every command this task's `Tests` names is green — named there, not restated here, so the two cannot drift — and `make build-self` leaves no drift.

### T8: The skill ships its own alignment checker

**Depends on:** T2, T7

**Touches:** `docs/adr/0108-opaque-append-only-loop-contract-identifiers.md`,
`tests/roster/test_acceptance_criteria_guide_boundary.py`,
`packs/core/.apm/skills/new-spec/SKILL.md`,
`packs/core/.apm/skills/new-spec/scripts/lint-contract-item-alignment.py` (exists),
`packs/core/tests/skills/new-spec/test_lint_contract_item_alignment.py` (exists),
`.agents/skills/new-spec/`, `.claude/skills/new-spec/` — projections, regenerated
in the same commit

**Grounding:**
- **This task creates no file; it brings existing code under the spec.** Every
  condition below is an assertion or an edit, because a `Done when` that reads as
  "the file exists" closes green on work already present. What remains is
  whatever of this task's `Tests` is not yet green — by reference, never
  enumerated: an enumeration of residue is a fact no task verifies. The
  deviation this closes is dated in `## Changelog`, which owns delivery history.
- **The checker belongs to this skill and depends on no other.**
  `packs/AGENTS.md` states skills are independent. The precedent is
  `author-delivery-brief/scripts/lint-brief-coverage.py` with its test at
  `packs/core/tests/skills/author-delivery-brief/test_lint_brief_coverage.py`:
  an authoring skill shipping a lint over the artifacts it authors. Seven sibling
  core skills carry a `scripts/` directory, so the layout is standard and
  `CAT-S004` treats layout findings as warnings rather than errors.
- **Its scope is not the spec-status lint's.** That lint decides spec *state* —
  status vocabulary, criteria checked at a ship transition, deferral anchors,
  contract traceability — and is owned by the skill that runs the gates. This one
  decides *item alignment* and owns no lifecycle question. Neither invokes the
  other; that is the point.
- `pack.toml` declares no per-skill script inventory, so the script needs no
  manifest entry. It ships by being inside the skill directory.
- The script is projected to `.agents/` and `.claude/`; `.apm/` is the source,
  and `test_cognitive_load_repository_contract.py` requires byte equality across
  all three.
- `packs/AGENTS.md` — any `.apm/` script writing to stdout or stderr reconfigures
  both streams to UTF-8 before its first print.
- Repository security rule: every read is confined and rejects links, reparse
  points and non-regular files before opening.
- **The invocation is wired, and this task owns it.** A shipped script no
  surface names is a control nobody runs: the sibling precedent,
  `author-delivery-brief/SKILL.md`, references its own lint. Add the reference to
  the skill's own procedure rather than to a gate list — two lines against a
  budget with roughly 350 spare, and T1 and T6 spend from the same budget, so the
  three are counted together before any of them lands.

**Tests:** `python3 -m pytest packs/core/tests/skills/new-spec/test_lint_contract_item_alignment.py -q`
- `python3 -m pytest tests/roster/test_cognitive_load_repository_contract.py -q` —
  this task adds files under the skill's `scripts/`, and that module compares
  every non-bytecode file under a canonical skill byte-for-byte across `.apm/`,
  `.agents/` and `.claude/`. A projection this task forgets to regenerate reds
  there and nowhere else, so omitting the command closes this task green while
  the repository is broken.
- `python3 -m pytest tests/roster/test_tdd_stub_lifecycle_contract.py tests/roster/test_rfc0099_activation_coverage.py -q` —
  this task edits `SKILL.md`, and both modules pin content in it. T1 and T6 name
  them for the same reason: a red this task causes closes green under its own
  `Done when` if the command is not named here.
- **AC-0032, the ADR — at repository level, not pack-local.** `docs/adr/` climbs
  above `packs/core`, which `pack-tests-stay-in-pack` rejects, so this assertion
  joins the roster module T2 and T5 already use and runs under
  `python3 -m pytest tests/roster/test_acceptance_criteria_guide_boundary.py -q`.
  The AC-0033 cases stay pack-local. Assert `docs/adr/0108-opaque-append-only-loop-contract-identifiers.md` no longer states that no lint
  enforces the convention, that its `Confirmation` names the shipped check, and
  that its `Revisit if` records the trigger as fired with the decision unchanged.
  **Constraint:** this is a lifecycle edit to an accepted record, not a reversal
  — the decision stands, and only the confirmation state moves. Assert the
  decision text is unchanged in the same check, so a future edit cannot use this
  precedent to reopen the decision itself.
- **AC-0040, a reworded criterion whose assertion did not follow.** Cases, each on
  a fixture repository with real commits rather than this repository's history:
  a criterion reworded with a plan line naming it also changed is clean; the same
  rewording with the plan untouched is reported; an unresolvable base revision,
  a tree with no history and no `--since` at all are each *skipped* and counted
  as a rule with no input, never reported as clean. **Constraint:** each skip
  case asserts that the rule appears in the no-input list, not the exit code —
  returning "no findings" is what every skip case did before they were
  distinguished, and a rule that cannot run reading as a rule that passed is the
  failure this checker exists to detect elsewhere. **Constraint on the scope:**
  a case where the only line naming the criterion sits outside an assertion
  block — a changelog entry — must still report, since reading the document as a
  whole is what silenced the rule. **Constraint on the over-report:** a case
  where a criterion is trimmed with its obligation unchanged must *also* report,
  asserting the stated residue rather than a precision the rule does not have —
  the measured figure came from a span of additions only, and pinning it as a
  property would make the rule's first prose-reduction round read as a
  regression.
- **The Interface-compatibility durable output, asserted per script.** Read each
  script's module docstring and assert it names every flag the parser accepts and
  every exit code the script can return, and that it claims no outcome the code
  cannot reach. **Mutation:** add a fourth exit code to a header and the
  assertion must red; remove a flag from the parser without touching the header
  and it must red too, since the row's closeout is that a header describes no set
  the code does not have — a one-directional check passes on a header that has
  drifted behind the code. The row is the only home for this obligation; it is
  observed here rather than left to the durable-output table, which no command
  reads.
- **AC-0039, a structurally broken task entry.** Cases: a balanced entry is
  clean; an entry truncated mid-clause is reported by task; and four legitimate
  backtick shapes are clean, each case recording whether it breaks a naive count
  — the two fence shapes do and therefore discriminate this predicate from
  counting, while a doubled delimiter and a balanced pair are even under both
  and guard without discriminating. **Constraint:** assert the *pairing* of
  value and rule — that the finding names the task — not merely that some
  finding was emitted, and do not let a non-discriminating case stand as
  evidence for the design. A rule an author learns to ignore is worse
  than no rule, so the fixtures carry the shapes the predicate must not report
  rather than a quoted rate: a rate belongs to the prototyping that chose the
  predicate, not to the contract that ships it.
- **AC-0033, the partial-report contract.** Assert that a spec with no `plan.md`
  reports every plan-gated rule as having no input, by name, and that the
  summary distinguishes that state from a clean run. **Constraint:** the
  expectation is written in the suite and the subject's own rule set is compared
  *against* it, never read as it — reading the subject on both sides made one
  tuple compare to itself and left the case green when a rule was dropped from
  it. Assert also that a rule still deciding part of its subject is not listed,
  which is why rule 4 is absent from the set.
- **AC-0033, the invariants.** One case per rule, each named below. Every bullet
  in this task traces to AC-0033; the criterion's own checker asserts that every
  criterion is named by at least one plan entry, so a task leaving its criterion
  unnamed would red the check it ships.
- Unlabelled spec → skipped, zero findings. The adoption case; without it the
  commit that introduces the checker fails 442 existing specs.
- Spec with no `## Retired identifiers` heading → treated as an empty retired
  list, not as a finding. Absence is the normal state and is what this spec
  itself carries.
- Partially labelled spec → finding naming the unlabelled criterion.
- Duplicate identifier → finding naming both line numbers.
- Identifier present in the retired list → finding.
- Malformed identifier → finding.
- Reference in `plan.md` to an identifier no criterion carries → finding.
- Criterion named by no plan entry → finding.
- Criterion in two verification groups, and in none → a finding each.
- Verification item whose identifier mirrors its criterion → finding. Task
  derivation and `VI-` uniqueness are **not** asserted: nothing relates an item
  to a task number and the uniqueness rule reads criteria only. AC-0033 was
  narrowed to match rather than claim an oracle the checker does not have.
- **Mutation proof:** delete one criterion's label and confirm the partial case
  reds. A green run there means the checker keyed on the reference side only and
  never looked at the criteria.

**Approach:**
- One pass over the spec directory returning findings; no lifecycle knowledge, no
  `workspace.toml` read, no status parsing. Those belong to the state lint and
  duplicating them here would put two homes on one obligation.
- Skip-when-unlabelled is the first condition, not a late guard.

**Done when:** every command this task's `Tests` names is green — named there, not restated here, so the two cannot drift — and the AC-0032 ADR edit is landed and asserted at repository level, the invocation is referenced from the skill, every mutation this task's `Tests` states is executed with its red recorded and then restored — by reference to that list, not an enumeration here, which is the same drift the command rule was written after — and `make build-self` leaves no drift.

### T9: The skill ships its grounding explorer and its coverage check

**Depends on:** T8

**Touches:** `packs/core/.apm/skills/new-spec/SKILL.md`,
`packs/core/.apm/skills/new-spec/scripts/explore-grounding.py` (exists),
`packs/core/.apm/skills/new-spec/scripts/lint-finding-coverage.py` (exists),
`packs/core/tests/skills/new-spec/test_explore_grounding.py` (exists),
`packs/core/tests/skills/new-spec/test_lint_finding_coverage.py` (exists),
`packs/core/tests/skills/new-spec/test_acceptance_criteria_discipline.py`,
`.agents/skills/new-spec/`, `.claude/skills/new-spec/` — projections, regenerated
in the same commit

**Grounding:**
- **This task creates no file either, on the same footing as T8.** What remains
  is whatever of its `Tests` is not yet green, by reference for the reason T8
  gives.
- Same skill-owned precedent and layout as T8; seven sibling core skills carry a
  `scripts/` directory and `pack.toml` declares no script inventory.
- **These two invocations are wired here, and this task owns the closing check.**
  T8 wires its own checker; the explorer and the coverage check had no named
  caller at all, which is the control-nobody-runs case on the same rationale.
  The explorer is named at the discovery pass, the coverage check at the step
  whose artifacts it reads. Because AC-0038 closes over every check the skill
  ships, the assertion can only run once T8's reference exists — which is why
  this task now depends on T8. The three references spend from the same line
  budget T1, T6 and T8 draw on, counted together before any of them lands.
- `packs/AGENTS.md` — an `.apm/` script writing to stdout or stderr reconfigures
  both streams to UTF-8 before its first print.
- **`tools/lint-conformance-portability.py` already names this script's central
  risk:** shipped code that reaches a repository-only directory fails on an
  adopter's first run. Every top-level name, tracked-file set and ignore rule is
  derived from the repository at run time, never hardcoded.
- **The work-loop degrades without git rather than requiring it** —
  `lint-spec-status.py` warns "no base ref resolvable" and continues. This
  explorer matches that posture: git-derived probes fall back to a filesystem
  walk, and the co-change probe, which has no fallback, reports unavailable.
- `work-loop` grounds at its own PLAN step and cannot call this, because skills
  are independent. A second copy or a shared home follows; recorded as a revisit.
- **ADR-0037 D2 forecloses the obvious design, by name.** It records "No new
  top-level config file (no `grounding.toml`)", and states the posture the rest
  must take: a recorded surface *seeds* discovery and never replaces it, every
  read is if-present, absence lowers only the starting information, and no CI
  gate enforces it. So whatever this explorer cannot derive at run time it reads
  from surfaces the adopter already owns. Found by running the explorer on its
  own skill: the accepted decision predates, and rules out, the design proposed
  for it. **The correction it forces is not just "no file" but "no substitute
  for deriving":** the record seeds the derivation, and a recorded value the
  repository contradicts is surfaced as drift, never trusted over live state.
- **There is no skill-has-run state to detect, and the explorer must not look for
  one.** `adapt-to-project`'s anchoring phase is marker-independent and read-only
  by default, emits zero filesystem diff, and "remains useful when the repository
  has no pack state, install marker, root `AGENTS.md`, or durable adaptation
  files". The detectable signal is the *surface's content*, not the skill's
  history: whether `reference.md` exists and its named slots carry content. This
  repository is the worked example — 95 lines with the Constraints, Solution
  strategy and Crosscutting slots filled, and the identifier standard already
  recorded in them.
- **The known grounding surfaces, and what each is good for.**
  `adapt-to-project` writes `.adapt-discovery.toml`, `.adapt-pending.md` and
  `.adapt-install-marker.toml`; the durable anchoring surfaces are the
  `AGENTS.md` chain and `docs/architecture/reference.md`. Presence and schema
  version are detectable for all five. **Content value differs sharply:** this
  repository's `.adapt-discovery.toml` carries `[markers]` — project name, repo
  URL, owner, default branch — and none of the `[[findings.*]]` arrays its schema
  allows, so it grounds nothing. `reference.md`'s filled arc42 slots and the
  `AGENTS.md` chain are where the content is.
- **The read boundary is narrower than that file's header first reads.**
  "Consumed by `make build-self` only" continues "every other *build mode* copies
  markers through unchanged" — the restriction is on build modes substituting
  markers, not on readers. A grounding read of the findings arrays is legitimate;
  reading `[markers]` to substitute is not, and this explorer does neither
  substitution nor writing.
- **A thin surface is reported, never escalated.** The explorer names what the
  absent surface cost and may offer that `adapt-to-project` fills it, because the
  skill ships in the same pack. It never requires the skill to have run, never
  fails on absence, and is never wired to a gate — D2 makes the presence check
  absolute in the other direction, and a grounding tool that blocks on a missing
  optional document is the consequence-bound blocking already killed here.
- **`docs/specs/repository-context-anchoring/` is Shipped** and owns how an
  adopter's real development guidance is identified, including the rubric reused
  across `adapt-to-project`, authoring skills and focused review. The
  scoped-guidance probe consumes that identification and cites it rather than
  restating the rubric.

**Tests:** `python3 -m pytest packs/core/tests/skills/new-spec/test_explore_grounding.py -q`

- `python3 -m pytest packs/core/tests/skills/new-spec/test_lint_finding_coverage.py -q` —
  AC-0037's suite. Named here because `Tests` is what a completion gate reads and
  `Approach` is not, which is this contract's own rule.
- `python3 -m pytest packs/core/tests/skills/new-spec/test_acceptance_criteria_discipline.py -q` —
  AC-0038's assertion reads the authored `SKILL.md`, so it belongs in the module
  that already asserts over this skill's prose rather than in either script
  suite. Named here because a `Done when` closes on the commands its own `Tests`
  names, and an assertion in a module no command runs closes green unauthored.
- `python3 -m pytest tests/roster/test_cognitive_load_repository_contract.py -q` —
  this task adds files under the skill's `scripts/`, and that module compares
  every non-bytecode file under a canonical skill byte-for-byte across `.apm/`,
  `.agents/` and `.claude/`. A projection this task forgets to regenerate reds
  there and nowhere else, so omitting the command closes this task green while
  the repository is broken.
- `python3 -m pytest tests/roster/test_tdd_stub_lifecycle_contract.py tests/roster/test_rfc0099_activation_coverage.py -q` —
  this task edits `SKILL.md`, and both modules pin content in it. T1 and T6 name
  them for the same reason: a red this task causes closes green under its own
  `Done when` if the command is not named here.

- **The Interface-compatibility durable output** is asserted per script by the
  bullet T8 states; this task's scripts are covered by that same assertion and
  its mutations. Stated once there rather than copied here — two homes for one
  condition is the drift the by-reference rule was written after, and this bullet
  was a byte-identical second copy that claimed to be the only home.
- **AC-0037, the finding-coverage check.** Assert each rule with a fixture skill
  tree rather than this repository's layout: a covered subject is clean; an
  unobserved rule is named; a subject declaring no catalogue is skipped and
  counted; **a discovery scan finding no participant fails rather than passes**,
  which is the vacuous-pass guard and the defect the check exists to detect one
  level up; a catalogue with no suite is a finding naming the directories
  considered; the searched directories are named on a clean report too; the
  repository-wide tests tree is a fallback and not a widener, or a fragment
  observed by an unrelated suite reads as covered; an unparseable subject is
  reported rather than counted as a non-participant; and the catalogue is parsed
  rather than imported, proven by a subject whose import would leave a marker.
  **Constraint:** the suite is found at more than one depth. An installed skill,
  a pack in a catalogue and a loose script sit at different distances from their
  tests, and guessing one finds nothing in the other two, silently.

- **AC-0038, every shipped check names its consuming step.** Read the skill's own
  `scripts/` directory and assert that each script in it is referenced by the
  procedure — not from a restated list of three, which would pass unchanged on a
  fourth script added later with no caller. Assert the discovery pass names the
  explorer. **Constraint on the enumeration:** source scripts only, bytecode
  excluded. The pack suites import these scripts, which leaves `__pycache__`
  beside the source, and an unfiltered walk therefore reds in CI — where
  bytecode writing is on — while passing locally under
  `PYTHONDONTWRITEBYTECODE`. The roster projection contract already carries this
  exclusion for the same directories and is the shape to follow.
  **Mutation:** remove one reference and the check must red, naming the
  unreferenced script; removing the reference *and* the script must stay green,
  since an absent check needs no caller. Both mutations are executed and their
  red recorded, not merely described here.

**AC-0035.** Every bullet below is one of its cases. Each probe that can fail
open — one reading a seed's text, a runner set or history — gets a positive, a
negative and an unavailable case. The two reading the tree itself, scoped
guidance and path references, get a positive and a negative only, since their
input cannot be missing. The result cap is shared through one emitter, so the
suite carries one flood case rather than one per probe. Owner-approved
2026-09-11, after two stronger claims were found to describe a suite that did
not exist. **Constraint on the stage-report clause:** assert that each stage's
report names the probes it ran, per stage, with a case that would red if the
report named the probe set of a different stage or named none. A suite that only
asserts a probe behaves correctly cannot tell whether it ran at all, and stage
selection is the one thing that decides that.

- **path refs** — a fixture naming the seed is found; a near-miss path is not;
  the seed is excluded from its own results.
- **co-change** — a fixture history where two files move together surfaces the
  partner; **a repository with no history reports unavailable, distinguishable
  in the output from "no partners found"**. Without that distinction the probe
  is silently empty on a pre-git repository.
- **gate reachability** — a seed named by a runner is reported with it; **a seed
  no runner reaches is reported as unreached**, which is the finding, not its
  absence.
- **calibration is live, and reported.** The sweep-commit threshold comes from
  the repository's own p90 commit size and the phrase cutoff from the observed
  match distribution; both fall back to a documented default when there is too
  little signal, and both print the value with its basis. A fixed constant is a
  guess about someone else's repository — a monorepo's ordinary commit touches
  more files than a small library's, and being wrong is silent either way, since
  an over-tight threshold simply reports nothing. Assert a small fixture and a
  large one derive different thresholds, and that each names its basis.
- **phrase pins** — a line quoted once is found; a line in more than the cutoff
  number of files is excluded. **Mutation proof:** removing the cutoff must red
  this case, with a fixture carrying shipped boilerplate across many files.
- **scoped rules** — the walk returns every governing file from the seed's own
  directory to the root, in order, not only the nearest.
- **portability** — **a fixture repository whose top-level names differ from this
  one's returns findings.** A suite that only ever runs against this layout
  passes on a hardcoded allowlist and proves nothing about an adopter; the
  prototype demonstrated exactly that, returning zero on a seeded dead path
  under a top level its list omitted.
- **bounded output** — a probe exceeding its cap emits the cap plus an exact
  remainder count, never the full list.
- **ambiguity** — a path resolving under a non-root prefix is emitted as an
  ambiguity with its candidates, not asserted as dead.
- **confinement** — a symlink escaping the root is rejected, not followed.

**On writing the mutations.** Each killing mutation must remove the property from
*every* place the check reads, not from the most obvious one. Prototyping this
sweep took four attempts: two mutations left the identifier inside the scope
being checked and the check stayed green, a third removed it everywhere so a
weaker check would also have caught it, and only the fourth — present in the
document but absent from the checked scope — separated the strong check from the
weak one. A mutation that does not red is evidence about the mutation before it
is evidence about the check.

**Approach:**
- One tree walk shared by every probe; a script per probe would scan once per
  probe. The
  probe set is selected by stage, and the report names which probes ran: at
  discovery a dead-reference scan is a reassuring empty result because nothing is
  authored yet, and at review the artifacts are the seeds. Assert each stage's
  probe set and that the report names it.
- Probes report; none decides. No exit code but success absent an operational
  error, and never a gate. A tool that blocks on a heuristic is the
  consequence-bound blocking this repository already measured and killed.
- Glob-owner matching is deliberately absent: the prototype returned bare `*`
  matches from twenty unrelated files and never found a real owner. Recorded as
  tried and cut, not as an oversight.

**Done when:** every command this task's `Tests` names is green — named there, not restated here, so the two cannot drift — and every mutation this task's `Tests` states is executed with its red recorded and then restored — by reference to that list, not an enumeration here, since this clause named four while `Tests` had come to state more — and `make build-self` leaves no drift.

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
- **No required remote gate runs the suite six tasks close on.**
  `.github/workflows/catalogue-tooling-ci-gates.yml` runs a curated list of pack
  suites and omits `packs/core/tests/skills/new-spec/`; `make test` walks the
  whole tree but reaches CI only through a manually dispatched workflow that the
  repository's own guidance calls partial evidence, never required. So T1, T3,
  T6, T7, T8 and T9 all close on a suite a merge can go green without, and the
  roster-hosted AC-0032 assertion sits behind a separately dispatched workflow.
  Mitigation:
  run it locally at every task boundary and again in T5, and read a green remote
  run as saying nothing about it. Widening the curated list is a separate change
  with its own owner and is not smuggled in here. An open backlog intent,
  `docs/product/intents/new-spec-review-phrase-contract.md`, already records this
  omission alongside a review-phrase defect in the same file T6 edits; its
  phrase claim no longer reproduces — the test passes today — but the gate
  omission does.
- **AC-0018's check reads three surfaces; the rest go unread.**
  `assets/spec.md`, the rubric, and `SKILL.md` outside the procedure span carry
  no check for a fixed absolute criterion count. "Older" no longer describes the
  set: T7 authors new identifier-convention prose into `assets/spec.md` in this
  slice, so the unread set contains a file this delivery writes. It carries no
  count prose, which is why it stays outside the check rather than inside it. The criterion was narrowed to
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

- 2026-09-11: owner-approved tuning — **state sets, never counts, and narrate no
  delivery history.** AC-0018 gains the authoring rule (where a set is
  enumerated, name the set and not its cardinality; no criterion carries a count
  of the delivery's own history) and AC-0009's consistency member gains both as
  sweep tests. The reason is measured rather than aesthetic: across three review
  rounds, roughly eight of thirty-five sustained findings were number-accuracy
  churn — a stale denominator, a wrong ratio, an enumeration that had outgrown
  its count — and none of them changed what an implementer builds. A count
  beside an enumeration is checkable only against the list it duplicates, so it
  generates a finding per round and resolves nothing. Applied to this contract
  in the same change: the counts standing beside enumerated sets were replaced
  by their sets, and the assertions that read them now iterate the set. Rule 9
  reported six criteria whose assertions had not followed, which is how the
  propagation was found rather than remembered.
- 2026-09-11: owner-approved tuning — the version-bump `Always do` now states
  its timing: the bump lands once, on the release task, covering every `.apm/`
  change in the delivery. As worded before, an unconditional `Always do` and the
  rollout's deferral of the bump to T5 contradicted each other, which is the
  body-versus-criteria inconsistency AC-0009's consistency member reads for. The
  ordering itself was already authorized; only the wording was false. Same shape
  as the 2026-09-10 `Never do` amendment below.
- 2026-09-11: **owner decision — this slice runs a quasi-normal lifecycle, in
  iterative spike mode, until the contract-finding rate quietens.** Implementation
  may land alongside contract review rather than strictly after the engine gates,
  because the contract is about authoring moves whose value is only legible once
  the checks exist: three of this cycle's most serious findings were found by
  code that the strict ordering would not have written yet. The obligation the
  mode keeps is the one the deviation below broke — the plan must stay true about
  what already exists, so a task never carries a creation step for a file on
  disk. The mode ends when the rounds quieten, and the engine gates are fired
  from the state the repository is actually in at that point, not from the state
  the plan was written against.
- 2026-09-11: **recorded deviation — the three checkers landed before the engine
  gates.** `lint-contract-item-alignment.py`, `explore-grounding.py` and
  `lint-finding-coverage.py`, with their suites, were built during the
  pre-EXECUTE review rounds on direct owner instruction and committed to
  `.apm/`, with projections, while this pair was still under review and no
  engine state existed. T8 and T9 are therefore restated to close the deviation
  rather than to create the files: their conditions are assertions and edits, not
  creations. Owner decision 2026-09-11, on the precedent T6 already uses for the
  six plan rules that landed in core 2.25.14 ahead of their criterion. The cost
  of the ordering is recorded here because nothing else would show it: a plan
  frozen with a creation step for an existing file gives two tasks a gate that
  passes without the work.
- 2026-09-10: initial plan.
- 2026-09-10: every task grounded against its own governing set and the result
  recorded under `**Grounding:**`, per AC-0031. The plan-level
  `Repository anchors:` field above was filled in and still missed all three
  pre-EXECUTE blockers, which is the evidence for making grounding per-task.
- 2026-09-10: owner-approved — AC-0036 places a discovery grounding pass between
  the durable-outputs step and the spec body. The existing anchor resolution runs
  a step earlier, before destinations are resolved, so it grounds a feature area
  rather than a surface list. Both of this session's design-changing finds —
  ADR-0037 D2 naming `grounding.toml`, and repository-context-anchoring already
  owning guidance discovery — came from seeding by surfaces, and both changed
  criteria.
- 2026-09-11: grounded-cycle round 5 raised eleven findings — ten sustained,
  none refuted, one indeterminate pending an owner decision on whether the three
  scripts' invocation surface is a published interface. Four of the seven
  blockers were one class: a `Done when` omitting a command its own `Tests`
  calls load-bearing. Sweeping all nine tasks found **eight** of them affected
  and seventeen missing commands, against the four the reviewer named — so the
  response was repair-the-generator rather than four repairs. The rule now
  admits a *reference* to the `Tests` list instead of a second copy of it,
  because a duplicated list is the drift the rule was written after.
- 2026-09-11: grounded-cycle round 4 raised thirteen findings — twelve sustained,
  none refuted, one indeterminate only because the `/now/` projection was
  regenerated while adjudication ran, so the adjudicator read the repaired file.
  Three of the four blockers were the previous round's own tunings failing to
  propagate: AC-0022 gained a seventh plan rule with no implementing work, the
  Testing Strategy still stated six, and T1's `Done when` still omitted the
  command the new rule is about. AC-0037 brings the finding-coverage check under
  a criterion, which the newly bidirectional AC-0024 required.
- 2026-09-11: grounded-cycle round 3 raised fifteen findings — ten sustained,
  four refuted on authority or existing handling, one indeterminate and then
  settled by measuring. Rule 5's own entry scope reproduced the mention-anywhere
  defect it exists to eliminate.
- 2026-09-11: grounded-cycle round 2 raised fourteen findings, all fourteen
  sustained — the first report of this delivery to survive adjudication intact,
  because its claims were about code rather than prose.
- 2026-09-10: pre-EXECUTE round 3 raised fourteen findings: eleven sustained and
  three refuted. AC-0032 was added for ADR-0108's confirmation state, which the
  shipped checker falsifies on the commit that lands it.
- 2026-09-10: pre-EXECUTE round 2 sustained eight of eleven findings; three were
  refuted, one of them because the reviewer's proposed fix contradicted T6.
- 2026-09-10: owner-approved — the skill ships its own alignment checker (T8,
  AC-0033) rather than extending the repository's spec-status lint. Skills are
  independent, and the two jobs differ: that lint decides spec state, this one
  decides item alignment. The `Never do` boundary was amended in the same
  decision to admit the `scripts/` directory it needs.
- 2026-09-10: owner-approved scope addition — T7 carries the identifier
  convention into the spec template, and this spec's own criteria are the first
  to be labelled. Identifiers assigned 2026-09-10 and frozen from that point;
  the renumbering before that date is history, not retirement, so the retired
  list starts empty.
- 2026-09-10: pre-EXECUTE adversarial review sustained nine findings. Cut the
  count-recording criterion to the rubric that already owned it; moved the two
  cross-boundary checks to `tests/roster/`; gave every `.apm/`-touching task its
  own projection regeneration; bounded AC-0018 to the surfaces its check reads.
