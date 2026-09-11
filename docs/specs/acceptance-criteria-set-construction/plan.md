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

Layered in dependency order, one layer per task in the `## Tasks` order below.
The procedure lands as prose in the existing
acceptance-criteria step of `packs/core/.apm/skills/new-spec/SKILL.md`; the
adopter-facing guide follows it; three frozen cases and their seed pins land in
the pack's eval register and pack-local suite; the recorded run discharges the
delivery gate; the release surface closes last. Every task that edits `.apm/`
regenerates its projections in the same commit, per the spec's `Always do`:
`make build-self` takes `FORCE=1` on a dirty tree, so a single deferred run was
never required and the earlier rationale claiming otherwise was wrong.

The riskiest part is that the three checkers this slice ships are invoked by no
gate. Each is a pure function over an artifact with its own case suite, so the
checks themselves are sound; what can fail silently is their reachability — a
control nobody calls reports nothing and is indistinguishable from one that
found nothing. AC-0038 is the answer, and it reads the skill's own `scripts/`
directory rather than a restated inventory, so a check added later without a
named caller fails rather than passing unnoticed.
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

**Manual verification:** none. Every criterion this slice carries is decided by
a suite over a fixture artifact; the graded run that needed a human reading is
routed with the criteria that depended on it.

## Durable-output map

| Durable output | Tasks | Implementation evidence | Closeout evidence |
| --- | --- | --- | --- |
| Reusable learning → `notes/set-construction-self-application.md`, `docs/product/research/item-id-management-comparison-matrix.md` | T8 (the matrix, cited by ADR-0108) | The matrix's rejected alternatives, cited rather than restated | The matrix is cited by ADR-0108 with no claim left unowned |
| Release history → `docs/product/changelog.md` | T5 | Free-standing topmost `core` section at the bumped version | `test_core_version_and_okf_declaration_are_synchronized` green |
| Current product truth → the brief's § "Spec map" | T5 | `lint-brief-coverage.py` resolves this spec through its `Brief:` header | Roll-up names this spec; nothing hand-written into the brief |
| Decision rationale → `docs/adr/0108-opaque-append-only-loop-contract-identifiers.md` and this plan's `## Changelog` | T8 (the ADR); T5 (the changelog half) | T8's AC-0032 roster assertion over the ADR's `Confirmation` and `Revisit if`; each delivery decision dated in `## Changelog` | T8's `Done when` already closes the ADR half; the changelog half closes when no owner decision from this delivery is discoverable only from a commit message |
| Interface compatibility → the three checkers' `--help` and module headers | T8 (`lint-contract-item-alignment.py`); T9 (`explore-grounding.py`, `lint-finding-coverage.py`) | Each script's header states its flags and every exit code it can return, and the explorer states its per-probe outcome sets | A header describes no set the code does not have, asserted per script in the task that ships it |
| Current architecture → `docs/architecture/loop-contract.md` | T8 | The page cites ADR-0108 for item identity and the rubric for the shape rules, restating neither | A grep for a restated rule finds none, and the architecture index links the page |

## Design (LLD)

### Design decisions

- **Extend the existing acceptance-criteria step rather than add a reference
  file.** The rubric earned its own file because it is worked per defect and
  re-read; a five-step selection procedure runs once, inline, before wording.
  Rejected: a second `references/` file, which splits the AC step's reading
  order across two files for no gain. Traces to: the procedure's stage set and order.
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
  shape. Traces to: the routing table's build destination.
- **Cite, never restate.** Every shape, diagnosis or repair question in the
  procedure resolves to `assets/spec.md` or the rubric by name. Rejected:
  summarising the conjunction test inline for the reader's convenience — a
  shorter restatement is still a second home. Traces to: the `Never do` boundary
  forbidding a rule owned by `assets/spec.md`, `assets/plan.md` or
  `references/spec-authoring-rubric.md` from being restated into a second file,
  and to the guide page, where that boundary reaches published prose. No criterion states
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
  Traces to: AC-0018 and the whole-set uniqueness re-run.
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
  finds the gap one stage after it is cheap to fix. Traces to: the
  observer-at-admission rule and AC-0011.
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
Traces to: the procedure's stage set and order.

**A requirement without its consequence reads as advice.** Three rules pair a
requirement with what happens when it is unmet — composition with
compose-rather-than-check, the observing surface with stays-a-candidate,
bidirectional coverage with the pass failing. Assert both clauses per rule:
the requirement alone is the form that leaves the existing habit in place.
Traces to: the composition hand-off, the observer-at-admission rule and AC-0011.

**The count prohibition must not key on a numeral.** The forbidden shape is a
fixed absolute criterion count — a cap, ceiling, refusal or pass/fail bar. The
permitted shape is a percentile derived from the author's own corpus, used only
to order scrutiny, and the percentile criterion requires one in the same span. A
bare-numeral test therefore forbids what another criterion requires. A
whole-file token deny-list is unavailable either way; see the probe under
*Design decisions*. Traces to: AC-0018 and the whole-set uniqueness re-run.

## Tasks

### T5: The release surface closes

**Depends on:** T6, T7, T8, T9

**Touches:** `packs/core/pack.toml`, `packs/core/.claude-plugin/plugin.json`,
`docs/product/changelog.md`, `web/src/lib/now-highlights.generated.json`,
`workspace.toml`, `.agents/`, `.claude/`

**Tests:**
- `python '<skill-dir>/../work-loop/scripts/lint-spec-status.py'` over this spec
  directory — the closing task flips `Status` and ticks the criteria, and no
  command in any task reads either today. `Draft` beside a `queue` membership is
  a consistent pair, so the reconciler cannot substitute: a missing flip reads
  green. Assert the flipped `Status` and that every criterion is ticked or
  carries a deferral anchor on its own line.
- **The entry's content is read against the criteria it advertises.** Assert that
  every plan-authoring rule the shipped skill states is either described by the
  release entry or absent from the skill, so the entry cannot close describing a
  smaller set than the version carries. **Mutation:** add a rule to the plan step
  without touching the entry and the assertion must red. Version and heading
  parity is already covered and does not reach the body.
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
- **Both version files and the changelog section already exist**, carrying
  `2.25.16` and a free-standing topmost `core` heading, and the `/now/`
  projection has been regenerated once. This task creates none of them. What
  remains is to **re-resolve the number against a freshly fetched `origin/main`**
  — a peer took this branch's first choice mid-delivery, which is why the rule
  puts the re-resolution here — to bring the entry to its final state including
  its date, and to regenerate the projection again if the `Highlights` block has
  moved since. A condition that reads as "the files exist" closes green on work
  already present, which is the form T8 and T9 were restated onto.
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

### T6: The review-response protocol ships, and the plan rules are pinned in place

**Depends on:** none

**Touches:** `packs/core/.apm/skills/new-spec/SKILL.md`,
`packs/core/tests/skills/new-spec/test_acceptance_criteria_discipline.py`,
`.agents/skills/new-spec/`, `.claude/skills/new-spec/` — projections, regenerated
in the same commit

**Tests:**
- `make lint-packs` — the CAT-S003 body-line ceiling, for the reason T1's entry
  states; the command stays in each prose-adding task's `Tests` because a
  closing condition reads its own list, and only the rationale is referenced.
- `python3 -m pytest packs/core/tests/skills/new-spec -q` — the suite carrying
  every assertion below.
- `python3 -m pytest tests/roster/test_tdd_stub_lifecycle_contract.py tests/roster/test_rfc0099_activation_coverage.py -q`
  — the repository-level pins on `SKILL.md`. The pack-local suite cannot reach
  them, so without this command a red this task causes closes green under its own
  `Done when`.
- **The plan-authoring rules — shipped, pinned here.** Add a span-scoped assertion that
  every rule the plan step states occurs inside that step, with a mutation
  moving one rule outside it that must fail; the existing owner test searches the
  whole skill file, so a rule moved out of the plan step would otherwise stay
  green. The rules already located in the skill's plan step, which shipped ahead
  of this contract, are a recorded deviation, and this task closes it by bringing them under the spec
  rather than re-shipping them.
  **What is owed is read, never counted:** every rule in the plan step with no
  pinned entry must gain one. The obligation points at the shipped prose rather
  than at a number, and the assertion iterates it for the same reason, so a rule
  added later cannot leave the assertion sized to a stale total.
- **The response set.** The review step names every response to a sustained finding
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
  that the shipped prose defers the re-read inside it to the set-level pass
  **by condition, never by identifier** — shipped pack content may not cite this
  catalogue's acceptance criteria, so an assertion demanding the text name a
  criterion is one no implementation can satisfy. The set-level pass is named
  here, in the plan. Deleting the rider must red this assertion; without it
  the response list reads as complete while the companion prose a repair strands
  is nobody's obligation.
- **The claim-reaches-further response.** The review step states both answers to a claim-reaches-further
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
- **The surface-guidance finding class.** The review step states its finding class and its
  one answer: the criterion changes, and the forbidden content is never authored
  to satisfy it. **Constraint:** assert the prohibition as well as the class. A
  finding class named with no stated answer leaves the author choosing, and the
  choice that reads as cheapest — write the content the criterion demands — is
  the one this repository's round 6 actually produced.
- **The stop-decision report.** The review step *instructs* it. The oracle is
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
  the pack states the rule. **Constraint:** extend the step
  that already reports the finding trend rather than adding a second one. That
  step already carries the trend and each residual's consequence, so a parallel
  step would put two homes on one obligation. What is new is the options
  available to each residual and their costs.
- **The earn-its-keep test, and the `deletion-pass` pin that updates with it.** That sentence is
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
- **The roster modules that read T6's own surfaces**, resolved against this
  task's `Touches` rather than the plan's: `test_acceptance_criteria_discipline.py`,
  which pins the review-step rules this task extends, and
  `test_cognitive_load_repository_contract.py`, which compares the projections
  this task's `SKILL.md` edit regenerates. A copy of T1's grounding stood here
  for a round, which is the plan-level anchor list AC-0031 rules out — and this
  task is the one that authors AC-0031. The mechanical search is
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
- The pinned plan-authoring block in `test_acceptance_criteria_discipline.py`
  **also pins rules whose prose sits in the review step**,
  `owner-gets-decision-facts` among them. So the assertion iterates the rules
  stated in the plan step and matches each against the block, rather than
  treating the block as the plan step's rule set — reading the block as the set
  would credit a non-member and silently shrink what is checked.
- The same 500-warning / 1,000-error body-line ceiling applies, and T1 is
  spending from the same budget. The file is 660 lines today.
- The existing plan step, review step and deletion pass are each already located
  in `SKILL.md`; every one of this task's edits extends prose that exists rather
  than adding a sibling home.

**Approach:**
- The plan-authoring rules and the response protocol this task ships have no
  criterion in `spec.md`; they are carried by
  `docs/product/intents/spec-authoring-protocol-measured-before-shipping.md`,
  and each entry in `## Shipped ahead of a criterion, deliberately` states the
  route. The `RULES` assertions below stay, as construction checks over shipped
  prose.
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
`tests/roster/test_verification_ledger_contract.py` (exists) — the module the
field-authority assertion lands in,
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
- **The plan template's field authority — shipped, asserted here.** The rule is
  in `assets/plan.md`'s plan-contract region, not in `SKILL.md`'s plan step, so
  the assertion reads the template and lands in
  `tests/roster/test_verification_ledger_contract.py`, which already pins that
  region and which this task's `Tests` names. Assert that the region states
  which fields a completion gate reads *and* which are working material, naming
  both sets, and assert the `Grounding` clause separately: prose naming only the
  pinned half leaves an implementer unable to tell whether correcting
  `Grounding` needs an amendment, which is the question the rule exists to
  settle. **Constraint:** the module flattens the region before comparing, so a
  pin carrying a line break fails on a correct file.
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

**Depends on:** T7

**Touches:** `docs/adr/0108-opaque-append-only-loop-contract-identifiers.md`,
`tests/roster/test_loop_contract_identifier_adr.py`,
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
  `author-delivery-brief/SKILL.md`, references its own lint — but it writes a
  bare `scripts/…` path, which resolves only with the skill directory as the
  working directory and so does not resolve in an installed adopter tree. **The
  form to follow is the installer-supplied one a sibling already uses:**
  `python '<skill-dir>/scripts/<name>.py'`, as `work-loop/SKILL.md` does for
  `loop-cohort.py`. The skill projects into every adapter prefix, so the form
  decides whether "invoked from" is reachable at all rather than only here. Add
  the reference to
  the skill's own procedure rather than to a gate list — two lines against a
  budget with roughly 350 spare, and T1 and T6 spend from the same budget, so the
  three are counted together before any of them lands.

**Tests:**
- `python3 -m pytest packs/core/tests/skills/new-spec/test_lint_contract_item_alignment.py -q`
- `make lint-packs` — the CAT-S003 body-line ceiling, for the reason T1's entry
  states; the command stays in each prose-adding task's `Tests` because a
  closing condition reads its own list, and only the rationale is referenced.
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
  takes its own roster module and runs under
  `python3 -m pytest tests/roster/test_loop_contract_identifier_adr.py -q`.
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
  clean; an entry truncated mid-clause is reported by task; and the legitimate
  backtick shapes the parametrization enumerates are clean, each case recording
  whether it breaks a naive count — the fence shapes do and therefore
  discriminate this predicate from counting, while the shapes even under both
  guard without discriminating. **Constraint:** assert the *pairing* of
  value and rule — that the finding names the task — not merely that some
  finding was emitted, and do not let a non-discriminating case stand as
  evidence for the design. A rule an author learns to ignore is worse
  than no rule, so the fixtures carry the shapes the predicate must not report
  rather than a quoted rate: a rate belongs to the prototyping that chose the
  predicate, not to the contract that ships it.
- **The confinement boundary these tools cross, asserted rather than narrated.**
  Assert that a caller-supplied revision cannot act as a git option — the oracle
  is that git is never invoked, not that the result is empty, since an empty
  result is also what a failed git returns — and that a companion case proves a
  well-formed revision does reach git with the option list closed before it.
  Assert that a read outside the invocation root is refused after
  canonicalisation, and that an in-boundary link is refused too, since
  containment alone catches only the escaping one. **Mutation:** removing the
  ref filter, the option terminator, or the link guard must each red its own
  case. This obligation was recorded in `Grounding`, which no completion gate
  reads, which is why it is here.
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

**Done when:** every command this task's `Tests` names is green — named there, not restated here, so the two cannot drift — and AC-0032's ADR state is asserted at repository level — the edit itself is landed, so the assertion is the only part not yet green — the invocation is referenced from the skill, every mutation this task's `Tests` states is executed with its red recorded and then restored — by reference to that list, not an enumeration here, which is the same drift the command rule was written after — and `make build-self` leaves no drift.

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

**Tests:**
- `python3 -m pytest packs/core/tests/skills/new-spec/test_explore_grounding.py -q`
- `make lint-packs` — the CAT-S003 body-line ceiling, for the reason T1's entry
  states; the command stays in each prose-adding task's `Tests` because a
  closing condition reads its own list, and only the rationale is referenced.

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
  fourth script added later with no caller. Assert that a step names each
  script, and that the runnable `<skill-dir>` form is stated — a named script
  with no invocable form leaves the reader guessing how it resolves in an
  installed tree. **Walked against both mutations:** a new script with no caller
  reds, and dropping one script's name from the procedure reds. **Constraint on the enumeration:** source scripts only, bytecode
  excluded. The pack suites import these scripts, which leaves `__pycache__`
  beside the source, and an unfiltered walk therefore reds in CI — where
  bytecode writing is on — while passing locally under
  `PYTHONDONTWRITEBYTECODE`. The roster projection contract already carries this
  exclusion for the same directories and is the shape to follow.
  **Mutation:** remove one reference and the check must red, naming the
  unreferenced script; removing the reference *and* the script must stay green,
  since an absent check needs no caller. Both mutations are executed and their
  red recorded, not merely described here.

**AC-0041, AC-0042, AC-0043, AC-0044 and AC-0045.** Every bullet below is one of
their cases: the probe bullets and `portability` are AC-0041's surface;
`phase selects the probe set`, the stage-report clause and the executional-selection
constraint are AC-0042's; `calibration is live, and reported` and the
threshold-reporting constraint are AC-0043's; the three-outcome and two-outcome
case shapes and `bounded output` are AC-0044's; `ambiguity`, `confinement` and the
surface inventory are AC-0045's. Each probe that can fail
open — phrase pins, dead references, gate reachability, co-change — gets a
positive, a negative and an unavailable case. The probes reading the tree itself
— scoped guidance, path references and the surface inventory — get a positive
and a negative only, since their input cannot be missing; the inventory belongs
on this side because it reports each surface present or absent and has no
unavailable branch. The result cap is shared through one emitter, so the
suite carries one flood case rather than one per probe. Owner-approved
2026-09-11, after two stronger claims were found to describe a suite that did
not exist. **Constraint on executional selection:** assert that a probe outside the
selected stage set does no work, observed other than through the report — a
report-reading oracle cannot tell a skipped probe from a suppressed one, which
the criterion says in terms. Counting calls into the probe's own sampling is the
shape that reds when selection is reverted to a filter on the output.
**Constraint on threshold reporting:** assert that every stage's report carries
each derived threshold with its basis, whether or not that stage's probe set
consumes the value; an absent line is otherwise indistinguishable from an absent
derivation. **Constraint on the stage-report clause:** assert that each stage's
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
- **Deployment sequencing:** the version number is re-resolved against
  `origin/main` last, when T5 closes the release surface. A number is already
  carried in `pack.toml` and its entry is amended in place as content lands;
  what T5 owns is checking that a peer has not merged the same number first,
  which happened once in this delivery. Projection regeneration does not wait: each `.apm/`-touching task runs `make build-self`
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

## Cut from this slice

Owner decision 2026-09-11: a criterion stays only where its subject is built
*and* something reds when the obligation is broken. Ten criteria met neither
half — the prose they governed was never written — so they are retired and
their tasks are dropped rather than held.

| Cut | Was | Route |
| --- | --- | --- |
| T1, and AC-0006, AC-0011, AC-0018, AC-0031 | the five-stage selection procedure, the governing set, the set-level pass, the count prohibition, per-task grounding | [the authoring protocol measured before shipping](../../product/intents/spec-authoring-protocol-measured-before-shipping.md), which gates promoting any of it to a criterion on a frozen-case score |
| T2 | the guide page publishing the procedure | the same intent: a guide for guidance that is not shipping |
| T3, T4, and AC-0019, AC-0020, AC-0021, AC-0028, AC-0029 | three frozen cases, their seeded integrity, the scoring order, and the graded run | the same intent, which owns building the run because its own gate is that score |
| AC-0030 | the spec template carrying the identifier convention | ADR-0108 states the standard and AC-0032 holds the ADR to a confirmation state; the template edit returns with the procedure |

**The mechanical half of grounding is not cut.** It is the explorer, AC-0041
through AC-0045, which answers what governs a set of paths rather than obliging
an author to assert that they resolved it.

**What this leaves.** The skill ships three checks over its own artifacts, each
named by its consuming step, under ADR-0108's identifier standard. Every
criterion the slice retains is decided by a suite over a fixture artifact.

## Shipped ahead of a criterion, deliberately

- **The delta bound on a later review round** (`SKILL.md` step 7) is shipped
  prose that no criterion in this spec authorises, and that is the correct
  placement rather than an omission: the rule is about review dispatch
  economics, which
  [work-loop review economics](../../product/intents/work-loop-review-economics.md)
  owns, not about acceptance-criteria set construction. It is recorded here
  because shipped behaviour no criterion covers is brought under one, cut, or
  routed, and naming the owner is the third answer — routed, with the
  route stated. A pin in the discipline suite stops it being deleted silently.
- **The plan template's field authority** (`assets/plan.md`, plan-contract
  region) is shipped prose with no criterion here. Route: it is a plan-authoring
  rule, and those are carried by
  [the authoring protocol measured before shipping](../../product/intents/spec-authoring-protocol-measured-before-shipping.md).
  Its pin is in `tests/roster/test_verification_ledger_contract.py` and T7's
  assertion reads the template.
- **The criterion test — an obligation whose only check is a present sentence**
  (`SKILL.md` step 4) and **the intent freeze at shaping close** (`SKILL.md`
  step 3) are shipped prose with no criterion here. Route: the same intent,
  which is where the measurement that would justify a criterion lives. Both
  gained `RULES` entries — `criterion-needs-a-machine` and
  `intent-frozen-at-shaping` — in the same change that shipped them, so neither
  can be deleted silently while it waits for that measurement.
- **The plan-authoring rules and the review-response protocol** (`SKILL.md` plan
  step and review step) are shipped prose whose criteria this delivery retired.
  Route: the same intent. Their protection is the `RULES` block T6 asserts
  against, which is why T6 ships them rather than holding them.

## Open decisions

- **The compound-criterion class, swept rather than repaired at one instance.**
  Closed by owner decision 2026-09-11: the one criterion over twice the live
  median was split. AC-0035 carried the grounding explorer as a single
  identifier while its predicates expanded into thirty-two test functions and
  this task's own case list, so it became AC-0041 through AC-0045 — the explorer
  and its probe set, stage-scoped execution, derived thresholds and their basis,
  bounded results and the two case-shape memberships, and degraded grounding
  reported rather than fatal. AC-0035 is retired and never reused.
  `notes/ac-0009-decomposition-proposal.md` holds the worked shape, including
  the argument against splitting, for the next criterion that reaches this
  class. **The class is not closed by the split.** Splitting the largest
  criterion lowered the live median from 153 words to 104, which brought AC-0040
  (283) and AC-0033 (236) above twice it — the sweep re-runs against the set the
  split produced, not against the set that motivated it, and each of those two
  needs its own disposition on the same test: whether the predicate expands into
  a different check per member.

## Changelog

- 2026-09-11: **the keep test, applied.** A criterion stays only where its
  subject is built and something reds when the obligation is broken. An
  inventory against the tree found the selection procedure, the guide page, the
  frozen cases, the graded run, the template's identifier convention and
  AC-0038's check all unbuilt — eleven of twenty-one criteria described text
  that was never written, which is what sixteen review rounds had been
  adjudicating. Ten are retired and T1 through T4 are dropped; AC-0032 and
  AC-0038 are kept because each is one small decidable check, and AC-0038 is
  what stops the three shipped checkers being controls nothing invokes. The
  Objective now states the three checks the slice delivers rather than the
  procedure it does not.
- 2026-09-11: **owner sign-off on the two `Ask first` brief edits, and AC-0035
  split into five.** The criterion-syntax section and the Spec map cell are
  signed off as written; the Assumption records the authority and replaces the
  claim that the durable-output row forbids reverting the cell with the measured
  consequence — the roll-up reports `untracked` rather than `Draft`, and
  `lint-brief-coverage` exits 0 on both states. AC-0035 became AC-0041 through
  AC-0045 because one identifier stood in front of thirty-two test functions and
  twenty-three plan bullets; AC-0035 is retired. The compound-criterion sweep
  re-ran on the post-split set and is still open on AC-0040 and AC-0033.
- 2026-09-11: **cold round 6, delta-bounded, and the owner call it forced.** Ten
  of thirteen findings sustained; two were refuted because they were repaired
  before adjudication ran, and one is held behind this entry's decision. The
  decision: the deferral intent gates *promoting a deferred criterion back to a
  criterion*, not shipping the prose it used to govern — the guidance is already
  released and pinned by rule name, so the tasks that ship it keep shipping, and
  the intent's `Boundary` now excludes the prose, the retained criteria and
  building the frozen-case run. AC-0006 and AC-0011 each absorb the subject
  their establishing criterion used to supply, since "additionally" modified a
  step nothing required to exist. The field-authority assertion moved from T6 to
  T7, which owns the file the rule actually shipped in. The two authoring rules
  that shipped without a criterion gained `RULES` pins in the same change, and
  every rule this delivery ships without one is now registered with its route.
- 2026-09-11: **the lifecycle state moves back to `Draft`/`Drafting`.** Approval
  records a baseline after which the pair is pinned in substance, and eleven
  review rounds since approval added four criteria and reworded several more —
  so the recorded status was false about what was happening to the artifacts.
  The iterative-spike decision authorizes implementation landing before the
  gates; it does not authorize post-approval substantive amendment, and the
  pinning rule is `docs/CONVENTIONS.md`'s to change, not this instance's. The
  consequence is deliberate: the queued entry now carries `unapproved_spec` and
  blocks autonomous dispatch, which is the honest reading of a contract still
  under amendment. Approval is re-recorded when a round returns clean.
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
- 2026-09-11: the version-bump `Always do` now states that the release task
  re-resolves the number against `origin/main` when it closes. An earlier
  wording put the bump at the first content change and forbade a second one,
  which left no owner able to retire a number a peer had taken — and a peer had:
  `main` merged `2.25.14` for a different release while this branch carried the
  same number, so the merged changelog would have held two identical headings
  and the topmost-heading parity gate would have red. This branch moved to
  `2.25.16`, the next number free against a freshly fetched `main`. A number
  chosen from what was free when a branch started is a claim, not a reservation;
  only the release close can resolve it correctly. Found by the first cold
  review round, and by no warm round before it.
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
  six plan rules already located in the skill's plan step ahead of their criterion. The cost
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
