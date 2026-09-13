# Plan: cognitive-rule-inlining

- **Spec:** [`spec.md`](spec.md)
- **Status:** Approved
- **Repository anchors:** root `AGENTS.md` § Coding conventions (owning-source
  rule), `packages/agentbundle/agentbundle/build/self_host.py` (projection
  boundary and dirty-tree refusal),
  `packages/agentbundle/agentbundle/catalogue_tooling/lint.py` (router pin,
  row-count floor, and every declaration keyed on the rules path),
  `tests/roster/test_cognitive_load_repository_contract.py` (byte-pinned lookup
  sentence and semantic lookup chain), `tools/lint-agents-md.py` (line caps),
  `tools/check-output-readability.py` (prose extraction the scorer reuses),
  `tools/score-cognition.py` (the measurement instrument)

## Approach

Four edits and one measurement, in plain order.

Change the seeds, let `FORCE=1 make build-self` project them, retire the topic file and
every declaration of it, hand-edit the one file the projection does not own, add
the regression floor, then run both arms repeatedly against the unchanged
tree and the finished one, recording every difference beside the standard error
it is read against.

The editing tasks are serial for a reason the roster contract dictates. That
suite byte-pins the lookup sentence and separately models the router-to-topic
read, so the order must leave the tree green at every step: **T3 first** (inline
the clauses, raise the caps that let them fit, rewrite the pinned lookup
assertion), **then T2** (empty the router, relax the lint, rewrite the
semantic-chain assertion), **then T2b** (delete the topic file and its
declarations). Emptying the router or deleting the topic file before the clauses
land reds the roster contract with no replacement in place. Only T1 is
independent.

The harness composes what already ships. `claude -p --output-format=stream-json`
gives a fresh session per task with the tree's own guidance loaded, and its
`result` event carries the final message — the only part the scorer reads.
`tools/check-output-readability.py` supplies the prose extraction
`tools/score-cognition.py` reuses. The new code is one committed scorer plus a
disposable runner — no new dependency, no new top-level directory.

## Constraints

- Root `AGENT_RULES.md` is a projection. Editing it directly is overwritten by
  `FORCE=1 make build-self`. `policy-families.md` is likewise projected to
  `.claude/skills/` and `.agents/skills/` — both hidden from a default `rg` — so a
  source edit needs a re-run.
- Root `AGENTS.md` is the inverse: excluded from projection, hand-maintained.
- Four surfaces pin this routing: the lint's preamble tuple, the lint's
  row-count floor, the roster contract's byte-pinned lookup sentence, and that
  suite's semantic lookup chain. All four move in the commit that changes the
  files, or the suites red.
- `lint.py:595` rejects a zero-row routing table. The floor is relaxed as part
  of this work; without that, an empty table and a passing lint cannot coexist.
- The readability surface is decided by measurement at T4, not in advance.
  Measured pre-change, per file: root 47.46/8.74, seed 44.48/9.46. Any figure for
  the inlined state predicts an artifact that does not exist, and T4 supersedes
  it with a real measurement — so none is recorded here.
- `tools/check-output-readability.py` refuses a path outside the repository, and
  `tools/score-cognition.py` now refuses the same, so harness artifacts are
  written under the gitignored `.context/`.
- Harness runs bill real model usage: every admitted task costs two sessions per
  repetition, and the design is paired and repeated. The pilot ran three tasks at
  three repetitions per arm — eighteen scored replies.
- Raw harness artifacts live under `.context/` (gitignored); the committed record
  under `notes/` is derived from them. The *runner* is never committed — it bills
  model usage and duplicates the measurement brief's machinery. The *scorer* is
  committed with its tests: it is deterministic and model-free.
- Arm order is a design variable, not a detail. The pilot ran all control runs
  before all treatment runs, confounding the arms with time; repetition does not
  reduce that. A real run interleaves arms and pre-registers the order.
- Removing the topic file changes `tests/fixtures/install_snapshot/core.paths.txt`,
  which lists it on line 1.
- `lint.py:528` requires the seed `AGENTS.md` to keep its `<project-name>`
  placeholder. T3 rewrites that file and must not drop the token.
- `tools/lint-agents-md.py:29-31` caps root `AGENTS.md` at 120 lines and the seed
  at 100. Both sit exactly on their cap today, so the caps are raised before the
  clauses land. The cap does **not** reach the `dist/<route>/` copy: `_is_vendored`
  excludes `dist` before the seed branch, and the comment at `:230-233` claiming
  otherwise is wrong independently of this change.
- Every declaration keyed on the literal rules path rejects a pack-shipped rules
  seed, not just one: `_seeds_check_file:671` fails loud on any seed absent from
  `_SEEDS_REQUIRED_PLACEHOLDERS`, `:633` rejects a row whose `read` target is
  absent from the same map, `_AGENT_GUIDANCE_SEEDS` selects the confined 64 KiB
  read, and the routing-topic set forbids a nested table. All move together; the
  criteria enumerate the set.
- The catalogue lint walks `packs/<pack>/seeds/`, so an adopter's repository-root
  router is never subject to either gate. The relaxations serve pack authors, who
  are the only actor that cannot ship the pattern today.
- `FORCE=1 make build-self` refuses a dirty tree (`build/self_host.py:1305-1308`) unless
  forced; the Makefile passes `--force` only on `FORCE=1`. Every task that edits
  a seed and then re-projects runs in a dirty worktree, so the invocation is
  `FORCE=1 make build-self`.
- `deliver_seeds` never visits a path the pack has dropped, so a retired seed
  stays on an adopter's disk and their `AGENT_RULES.md` diverges into an
  `.upstream` companion. The change reaches existing adopters only through the
  changelog instruction.

## Construction tests

Existing suites are the oracle wherever one exists. The catalogue lint covers the
router preamble and the seed placeholders; the roster contract covers the lookup
text; the install snapshot covers the retired path. Only the scorer needs new
coverage, for the places it can silently lie: hiding the table confound,
inventing a reading level below the word floor, and absorbing a regression into
a paired delta.

## Durable-output map

| Durable output | Tasks | Implementation evidence | Closeout evidence |
| --- | --- | --- | --- |
| Changelog entry for the seed change | T5 | Entry under the releasing version | Entry names the seed guidance change |
| Readability surface for both `AGENTS.md` files | T4 | Measured scores recorded; the chosen surface reds when a file gets worse; fixture case names a scorer change | Branch recorded per file with its measurement; fixture green |
| Measurement evidence | T6 | Pre-registration and one paired record under `notes/` | Record carries host, model identifier, both tree SHAs, date, every quantity's difference per task, the standard error each is read against, the pre-registration's SHA-256, first and last run timestamps, and the quantities unmeasured |

## Design (LLD)

### Design decisions

- **The router survives with an empty `always` column.** Deleting it would break
  a lint, an install snapshot and twelve test files, and would remove the
  extension point adopters use for conditional rules. Emptying the column costs
  one sentence rewrite.
- **Nothing in this plan gates on the harness.** Ease is a target per the owner,
  and the measurement is recorded rather than gated. Three successive gate
  designs were cut — a two-arm floor, a common-scored-set, and a single-arm
  floor — and the Changelog records why.
- **The topic file goes rather than becoming a stub.** Once the clauses are
  inline, a routed copy is a second home with no control watching it diverge,
  and the two copies would sit under different readability standards — 70/8 for
  the topic file, a regression floor near 47 for `AGENTS.md`. Deletion reaches at
  least twelve code and test surfaces, including a shipped policy-family module;
  a stub would have cost one. The owner chose the
  larger change to end the duplication outright.
- **Paired, repeated, recorded.** Each prompt runs on both trees, several times
  per arm, and every reply is scored. A single sample cannot be read: measured
  pooled within-arm spread was 4.97 ease points, and a difference of means is
  read against the standard error of a difference, 4.06 at three repetitions.
- **Every declaration keyed on the rules path is relaxed, for one reason.** The
  row-count floor, the unknown-seed fail-loud, the row read-target,
  `_AGENT_GUIDANCE_SEEDS` and the routing-topic set all reject states the
  router's own documentation promises: a table with no rows, and a pack shipping
  a rules file for a row to point at. None is a workaround for this change; all
  are latent defects it surfaces. The catalogue lint never sees an adopter's own
  tree, so the relaxations serve pack authors specifically. Widening
  `_AGENT_GUIDANCE_SEEDS` changes which read path a file class gets, so it is an
  Ask-first boundary with a security reviewer, not a lint tweak.
- **The line caps are raised rather than paid for by cuts.** The survey's
  controlled measurement of file size against adherence returned a null, and the
  vendor's contrary guidance resolved to signal density rather than length. The
  measured cost sits on adding instructions, which is a different axis from file
  size. Prose is still optimised in the same edit, because the readability floor
  rewards it — but nothing load-bearing is cut to fit a line count.
- **The row-count floor is relaxed, not routed around.** The lint rejects an
  empty table, and the two alternatives were worse: keeping a conditional row
  gives the rule two homes that drift, and leaving the `always` row intact
  preserves the skippable read this work exists to remove. An adopter who
  deletes the shipped row hits the same failure today, so the floor is wrong
  independently of this change.
- **No placebo, and no claim that needs one.** A length-matched placebo would
  separate the rule's effect from the effect of added text. This design never
  makes that separation, so it does not need the arm; the limitation is stated in
  the spec rather than designed around.

### Component / module decomposition

`tools/score-cognition.py`, committed with its tests: deterministic, model-free,
and the instrument every recorded number comes from. The runner that drives
`claude -p` stays under the gitignored `.context/` — it bills model usage and
duplicates the measurement brief's machinery. Everything else
is existing callables.

### Behavior & rules

Each task is run several times against each tree and every reply is scored. A
reply the scorer cannot read — below the shipped word floor — is recorded as
unmeasured for that quantity rather than counted as zero, because a missing
measurement and a neutral one are different facts. Arm order is interleaved and
pre-registered; running one arm to completion before the other confounds the arms
with time, which repetition does not fix.

### Failure, edge cases & resilience

A session that errors or times out is re-run once; a second failure is recorded
and that task drops from the set with its absence noted. Task admission is decided at T1 on a pilot draw that is never scored as an arm.
Selecting on the same measurement that is later scored is regression to the mean
and manufactures an apparent gain under a zero-effect null.

### Dependencies & integration

No new dependency. `claude` is already on PATH; the harness fails loudly with a
named message if it is not.

## Tasks


Sections below are in **execution order**, which is not label order: the
roster contract forces T3 ahead of T2 and T2b. Labels are left stable so
references elsewhere still resolve; `Depends on:` is authoritative.

### T1: Commit the scorer and the runner, then admit the task set

**Depends on:** none

**Tests:**
- A table-heavy reply and a prose reply of equal length report different
  `scored_pct` — the confound the shipped readability tool hides.
- A reply below the shipped tool's 30-word floor reports no reading level rather
  than a number, and a paired difference records that quantity as unmeasured.
- A reply with no words reports absent densities, never `0.0`, which would be the
  best possible score for something that could not be measured.
- A dotted name inside an inline-code span counts once, and two distinct names
  inside one span count twice: span identity is not token identity.
- `pair_delta` reports differences and asserts no direction; no field claims an
  improvement.
- The pooled standard deviation is `sqrt(SS/df)` across arms and the standard
  error of a difference of means is `s_p * sqrt(2/n)`. Both are computed by the
  tool, with a case pinning them against the recorded pilot values — pooled 4.97
  on SS 296.38 over 12 df, standard error 4.06 at n=3. Hand-computation got both
  halves wrong once already; the record documents it.
- A path outside the repository is refused. The scorer reads untrusted model
  output; this is the one property here on a trust boundary.

**Approach:**
- Commit `tools/score-cognition.py` and its tests beside it, and document it in
  `tools/README.md`, which main ships as the hand-maintained tool index.
- Add the statistics the measurement needs to the tool rather than leaving them
  to be hand-computed: pooled SD as `sqrt(SS/df)` across arms, standard error of
  a difference of means as `s_p * sqrt(2/n)`. A `--stats` mode emits both. This
  exists because hand-computation already produced a mean-of-SDs where a pooled
  figure was named, and read a difference of means against the wrong comparator.
- Resolve the confinement root the way `check-output-readability.py` resolves
  one, not from the current working directory — the cwd form passes a test run
  by pytest and reads any tree the tool is invoked from.
- Make the span-containment test linear over sorted spans. The current form
  compares every inline span against every technical-token span on untrusted
  model output capped at 1 MiB.
- Write the two cases the test list names that do not yet exist: a path outside
  the repository is refused, and two distinct names inside one span count twice.
  The first is the only property here on a trust boundary.
- Write the disposable runner under `.context/`. It shells
  `claude -p --output-format=stream-json` once per task per tree per repetition,
  takes the `result` event's final message, and pipes it to the scorer. It
  interleaves arms rather than running one to completion. It is never committed
  and never tested; every number it produces is the scorer's.
- Draw candidate tasks against the unchanged tree and admit on that draw alone.
  The admission draw is discarded, never reused as an arm: selecting on a low
  draw and then scoring the same measurement guarantees the next draw rises
  whether or not anything changed.
- Avoid any plain-language cue in a prompt. "Explain to a teammate" primes the
  behaviour under test and cost about five points of discrimination in the pilot.

**Done when:** the scorer's tests are green, the runner exists under `.context/`,
and `notes/measurement-protocol.md` is committed carrying the exact prompt text
and identifier for every admitted task, its admission score, the artifact path,
and the pre-registered arm order. Choosing the prompts is choosing part of the
experiment; leaving them to the implementer would make the experiment
unreproducible and its admission unauditable.

### T3: Inline the clauses, raise the caps, and rewrite the pinned assertion

**Depends on:** none

**Tests:**
- The seed `AGENTS.md` still contains the literal `<project-name>` placeholder
  after the rewrite, which the catalogue lint requires of it.
- `tests/roster/test_cognitive_load_repository_contract.py:218` and `:236` both
  assert `"AGENT_RULES.md" in root_context`. The rewrite must keep that mention
  while removing the unconditional read — the criterion's "instruct no
  unconditional read" must not be satisfied by deleting the link outright.
- `test_work_intake_surface.py:278` pins the seed's relative links to exactly
  `{AGENT_RULES.md, docs/CONVENTIONS.md}`. The rewrite reds it if a link is
  added or dropped; update the pinned set deliberately or leave the links alone.
- Both files pass `tools/lint-agents-md.py` under the raised caps.
- The roster contract's rewritten lookup assertion passes only when the clauses
  are present inline in both files, and reds against the pre-change text.

**Approach:**
- Raise `MAX_ROOT_LINES` and `MAX_SEED_LINES` in `tools/lint-agents-md.py`
  first. Both files sit exactly on their cap, so the clauses cannot land until
  the caps move. This task owns that edit; no other task does.
- Replace the "Rule lookups" pointer with the clauses in
  `packs/core/seeds/AGENTS.md`, then in root `AGENTS.md`.
- Prune in the same edit. Merge duplicated navigation and repeated caveats
  first; the rule's own author-load section names that as the reduction to make
  before adding text.
- Keep the scoped-`AGENTS.md` walk instruction, which is a separate obligation
  from the router read and is not removed by this change.

**Done when:** the rewritten roster assertion is green, the seed keeps its
`<project-name>` token, and both readability scores are recorded.

### T2: Empty the router and move its pin

**Depends on:** T3 — the roster contract's semantic chain asserts the router
carries the topic path, so emptying the table before T3 rewrites that assertion
reds the suite with no replacement staged.

**Tests:**
- A zero-row routing table lints clean. This case reds before the row-count
  floor is relaxed, which is what proves the relaxation landed.
- A pack-shipped `.agents/rules/*.md` seed lints clean. This case reds today
  with the unknown-seed fail-loud.
- A routing row whose `read` target is that path lints clean. This case reds
  today with `agent-rules-read-target-invalid`.
- A rules seed carrying a routing table is still rejected
  (`agent-rules-routing-topic-invalid`), so the nested-router guard survives.
- A rules seed over 64 KiB still reports `agent-guidance-unreadable`, so the
  confined read is not switched off for the files the relaxation admits.
- All four are constructible from a fixture tree, so nothing goes into the
  shipped seed and the read this change removes is not reinstated.
- The catalogue lint passes with the rewritten preamble, which fails if the
  pinned tuple and the file text disagree.
- The roster contract's rewritten `_semantic_lookup_chain` no longer asserts the
  router carries `.agents/rules/cognitive-load.md`, and still exercises the
  bounded-read path it was written to cover (`:45`).
- `:109`'s `reads == ["AGENT_RULES.md", ".agents/rules/cognitive-load.md"]` is
  rewritten. It breaks twice over otherwise: the emptied router yields one entry
  here, and the deleted seed raises at T2b.
- `:219`'s `"| always | \`.agents/rules/cognitive-load.md\` |" in router` is
  rewritten for the empty table.
- `:241`'s comparison against the host fixture is rewritten, **and
  `packages/agentbundle/tests/fixtures/cognitive-load-hosts.json` moves in this
  task, not T2b.** Its `ordered_agent_reads` pins the chain for all three hosts,
  so leaving it to T2b ends T2 red — the exact shape the T3 → T2 → T2b order
  exists to prevent.
- `FORCE=1 make build-self` leaves no drift, proving the root projections regenerated
  from the edited seed.

**Approach:**
- Edit `packs/core/seeds/AGENT_RULES.md`: drop the `always` row, rewrite the
  first sentence so the read is conditional on a matching `when` row.
- Update `_AGENT_RULES_INSTRUCTIONS`'s routing sentence only — its bounded-read
  and instruction-authority sentences stay. Then relax the row-count floor and
  widen every
  declaration keyed on the literal rules path — the unknown-seed fail-loud, the
  row read-target rule, `_AGENT_GUIDANCE_SEEDS`, and the routing-topic literal
  set — in the same commit. Widening only the first two switches off the
  nested-router guard and the bounded read for exactly the files admitted.
- Rewrite every roster assertion this task moves — `:45`, `:109`, `:219`, `:241`
  — and edit `cognitive-load-hosts.json` here rather than in T2b. Rewriting, not deleting: deleting it retires
  the only control that observes this routing at all.
- Run `FORCE=1 make build-self` to project both root files.

**Done when:** the catalogue lint is green and `git status` shows the two root
projections updated without hand edits.

### T2b: Retire the topic file and every declaration of it

**Depends on:** T2 — and therefore T3. The topic file is read by the roster
contract until T3 rewrites it and routed to until T2 empties the table; deleting
it earlier reds both.

**Tests:**
- The catalogue lint passes with the path absent from its seed map, its
  guidance-seed set, and its topic-file rule.
- The install-snapshot suite passes with the path removed from
  `core.paths.txt`.
- The readability parametrize passes with its entry retired.
- The roster contract passes with its root-vs-seed byte check for that path
  removed rather than left pointing at a missing file.

**Approach:**
- Delete `.agents/rules/cognitive-load.md` and its seed.
- Remove the three `lint.py` declarations, the snapshot line, the parametrize
  entry, and the roster byte check.
- Re-point the `cognitive-load` member of the work-loop policy family registry
  at `seed:AGENTS.md`, which is where `the-razor` already points. This is a
  behaviour change across eight mentions, not a path edit: check the six phase
  selection lists still select what they did.
- `test_work_intake_surface.py:290` asserts the topic seed `.is_file()`; it
  passes today and reds on deletion. Remove that assertion with the file.
- Update the remaining fixtures and tests that name the path:
  `cognitive-load-hosts.json`, `test_catalogue_tooling_file_safety.py`,
  `test_policy_family_registry.py`, `test_lint_agents_md_progressive_disclosure.py`.
  Not `cognitive-load-hosts.json` — T2 owns that fixture.
- `tools/lint-agents-md.py:47` matches `.agents/rules/*.md`. Leave the rule in
  place; the spec's Follow-ons records what it loses.

**Done when:** no code or test surface references the path, the policy family
member resolves to an existing module, `FORCE=1 make build-self` has re-projected
`policy-families.md` to `.claude/skills/` and `.agents/skills/` with no drift, and the suites above are
green.

### T4: Score both `AGENTS.md` files without breaking the 70/8 gate

**Depends on:** T3

**Tests:**
- For each file, the control T4 selected reds below its threshold and passes at
  or above it. A file on the 70/8 branch has no floor, so a test asserting a
  floor for both files is unsatisfiable.
- The 70/8 parametrize holds the two files that survive T2b's retirement, plus
  any `AGENTS.md` that measurement shows now meets it. No file is added to an
  assertion it does not meet, and the control's name matches its contents.

**Approach:**
- Add the regression-floor assertion beside the tool it exercises, under
  `tools/`, so pytest's directory-based collection reaches it. A test landing in
  an uncollected path passes vacuously forever.
- Measure both finished files first, then choose the surface. A file at or above
  70/8 joins the existing assertion; one below takes a floor pinned to its own
  measured score with a tolerance sized against it. Record which branch each file
  took and the measurement that selected it. The pre-change figures are never the
  pin: a floor at 47.46 sits ~19 points below where the file will land and could
  never fire.
- Score a fixed fixture string in the same test, so a scorer change reds on the
  fixture and names itself instead of reding on `AGENTS.md` and blaming the prose.

**Done when:** both new cases are green and `make test` is no redder than before
the change.

### T5: Changelog entry

**Depends on:** T3

**Tests:**
- The changelog gate for the releasing version passes.

**Approach:**
- Record the seed guidance change as an adopter-visible entry with four things
  the adopter cannot discover otherwise: that `.agents/rules/cognitive-load.md`
  is retired and should be deleted from their tree by hand, because seed delivery
  never removes it; that their `AGENT_RULES.md` will arrive as an `.upstream`
  companion rather than replacing the live file; that a customised root
  `AGENTS.md` does the same, so the inlined clauses arrive as `AGENTS.upstream.md`
  and must be merged by hand; and the shape of a routing row, since the shipped
  table is now empty.

**Done when:** the changelog gate is green.

### T6: Run both arms and record the differences

**Depends on:** T2b, T4, T5 — every editing task. The treatment arm is the
*finished* tree, so it cannot run while the topic file and its declarations are
still present; the scheduler paired T6 with T2b precisely because that edge was
missing.

**Tests:**
- Each task's record carries both tree SHAs, the model identifier, every
  quantity's difference, the pre-registration's SHA-256, and the first and last
  run timestamps — the fields the spec makes contract.
- A quantity the scorer could not measure is recorded as unmeasured, not as zero.

**Approach:**
- Commit the pre-registration before the first scored run.
- Run the frozen set at least three times per arm against both trees,
  interleaving arms rather than running one to completion.
- Record each difference beside the standard error of a difference of means. A
  difference inside it is recorded as not separable from noise. Nothing here
  gates: control scores differ widely by task, so a threshold would report which
  task was drawn rather than what the clauses did.

**Done when:** the pre-registration and the paired record are both committed, and
every difference is stated beside the standard error it is read against —
including the case where none clears it. The pilot recorded under `notes/` does
not close this task: it compared a hand-inlined root `AGENTS.md`, not the
finished tree, and its arms were not interleaved.

## Rollout

- **Delivery:** one PR. A revert is not a no-op: it restores a deleted seed and
  its projection, a snapshot line, a readability parametrize entry, three
  `lint.py` declarations and a policy-family module, and `FORCE=1 make build-self` must
  be re-run afterwards to re-project the restored seed.
- **Infrastructure:** none.
- **External-system integration:** none. The harness calls a local CLI.
- **Deployment sequencing:** none beyond the task dependencies. Dropping the
  before/after floor removed the ordering hazard an earlier draft carried; the
  control arm is obtained from a worktree at the branch's merge-base, never by
  stashing, because the stash stack is shared across worktrees.

## Risks

- **Widening `_AGENT_GUIDANCE_SEEDS` changes which read path a file gets.** That
  selection chooses the confined 64 KiB `_read_agent_guidance` over a plain
  `read_text`, so admitting a new path class crosses a file-reading trust
  boundary. Route to a security reviewer before the relaxation lands rather than
  treating it as a lint tweak.

- **The run is not repeatable across model versions.** Mitigation: the record
  names the model identifier and date, and the spec states that no comparison
  against another version is supported.
- **Run-to-run spread swamps a single-sample difference.** Measured within-arm
  standard deviation was 4.97 reading-ease points, pooled across six arms; in a separate
  control-only check, two of six control-vs-control pairings looked like
  improvement. Mitigation: repeat each arm at least three times and report the
  standard error of a difference of means beside every difference — not the
  spread of single observations, which is a different quantity and gives a
  different verdict. A difference inside that standard error is not reported as
  one.
- **The design as run is underpowered, and by a known amount.** Resolving a
  5-point effect needs roughly sixteen repetitions per arm per task, about
  ninety-six runs for three tasks; three points needs nearer forty-four per arm. Going further is
  a cost decision with a stated price, not a design problem.
- **Selecting tasks on the scored measurement manufactures a gain.** Regression
  to the mean produces an apparent improvement under a zero-effect null most of
  the time. Mitigation: admission uses a separate draw that is never scored.
- **The pilot showed the instrument responds and nothing more.** The
  population-level design is owned by `guidance-activation-measurement.md`.
- **Existing adopters receive nothing automatically.** A retired seed is never
  removed and a diverged `AGENT_RULES.md` becomes an `.upstream` companion, so
  the old `always` row stays live in every tree that already installed. The
  changelog instruction is the whole delivery mechanism. Mitigation: T5 names the
  orphaned path explicitly rather than describing the change in general terms.
- **Re-pointing the policy family may change phase selection.** Mitigation: T2b
  checks the six selection lists rather than assuming a module swap is inert.
- **Pruning removes something load-bearing.** Mitigation: the Ask-first boundary
  requires sign-off before any existing rule, rung, row or command is cut.

## Changelog

- 2026-09-13 — initial draft.
- 2026-09-13 — the behavioural measurement was run under pre-registration: three
  tasks, three repetitions per arm, both trees. Result inconclusive by its own
  rule; pooled within-arm spread was 4.97 points and the largest |t| was 1.14. The earlier
  single-sample spike's +9.16 fell to +4.51 when repeated. Outcome 3 states the
  recorded null and the price of resolving it; a stated bound was withdrawn as
  unsupportable at this n.
- 2026-09-13 — shaping review returned four blockers. Router emptying collided
  with the lint's row-count floor (owner chose to relax the floor); three
  further pinned surfaces were found beyond the one recorded; the readability
  gate would have committed a permanently red assertion; and the kill condition
  was restated with a common scored set, void thresholds, and a confirming
  re-run.
- 2026-09-13 — shaping review round 2. Testing Strategy and Durable Outputs still
  described the design round 1 replaced. The emptied router orphaned the topic
  file into a second home under a different readability standard; the owner chose
  deletion over a stub. The common-scored-set fix was found to select against the
  regression it hunts, since degradation lowers tool-call counts, so an
  exclusion-gap guard was added. The decision rule became two-branch, because a
  low pre-change baseline is what this spec predicts and a regression-only rule
  would void on it. The adapter was split from the runner so its tests can be
  committed.
- 2026-09-13 — shaping review round 3. The two-arm design was cut. It had
  reached the point of rejecting the change for failing to produce an adherence
  benefit the spec disclaims, on the branch the spec's own premise predicts —
  three rounds of repair-origin findings on one control. Replaced by a single
  run against a floor fixed in advance. That floor was then cut too, after a
  spike showed the quiet-work oracle passing on the unchanged tree while
  readability, table density and token density all separated the arms cleanly.
  Review also found the topic-file surface
  list understated: the work-loop policy family registry points its
  `cognitive-load` module at the deleted file, which is a behaviour change.
- 2026-09-13 — adversarial spec review, run with execution rather than reading.
  Five blockers that six contract rounds missed: both `AGENTS.md` files sit
  exactly on hard line caps; a test asserts the retired seed exists; the
  policy-family criterion demanded invariance of the thing being changed; the
  regression floor was pinned to a pre-change score that inlining improves by
  ~19 points, so it could never fire; and the read-target whitelist would have
  left the router unable to route to any rules file. Owner raised the caps and
  chose to make the extension point real.
