# Plan: Intent review mandate split

- **Spec:** [`spec.md`](spec.md)
- **Status:** Approved
- **Repository anchors:** `packs/AGENTS.md` (runtime export boundary, version
  bump rule, portability rule), `packs/AGENTS.local.md` (projection ownership
  table, release pipeline), `docs/CONVENTIONS.md` § *Superseding a frozen
  document* (the `Status`-line carrier), `packs/core/.apm/agents/finding-adjudicator.md`
  (the six predicates' owning source). Analogous implementation: `finding-adjudicator.md`
  is the in-pack precedent for a read-only reviewer whose output vocabulary is closed
  and whose contract is pinned by a pack test; its paired suite is
  `packs/core/tests/pack/`. Named uncertainty: no existing reviewer in this pack
  carries two different output vocabularies across modes, so the mode-scoping
  idiom is established here rather than copied.

## Approach

Three edits carry the contract and everything else follows them: the
`shaping-reviewer` body gains a mode-scoped rubric and a second output
vocabulary, the `adversarial-reviewer` body gains a mode with its own two-shape
output, and the two intent callers branch on the new vocabulary. The
prose *is* the product, so each invariant lands with a pack-test assertion that
fails on the current bytes first; the release steps (versions, projections,
changelog) run last, once the sources have stopped moving.

## Constraints

- `packs/` content may not cite ADR-0108, RFC-0099, an acceptance criterion, or
  an internal `docs/` path; the portability grep in `packs/AGENTS.local.md:53`
  is the check.
- `.apm/` is the only source; `.claude/agents/`, `.codex/agents/`, and every
  other projection are regenerated, never edited.
- `make build-self` refuses a dirty tree, so the release task commits its
  sources before regenerating. That ordering is why observed behavior cannot be
  recorded before it: a host dispatches an agent from its projection, not from
  `.apm/`.
- The portability grep at `packs/AGENTS.local.md:53` already matches
  pre-existing permitted content under `packs/`, including one hit inside a file
  T1 edits (`test_shaping_review_contract.py:186`, "as ADR-0042 requires"), and
  its owning source says to judge what a hit points at rather than count hits.
  The check is therefore scoped to hits this change introduces, read against the
  merge base — a non-empty total is expected and proves nothing either way.
- Frozen records take a `Status`-line edit only.

## Construction tests

The assertions below fall into the two obligations Testing Strategy declares
apart, and the split is load-bearing: only the changed-bytes assertions are
expected to fail against today's bytes before their source edit. The
preservation controls and the already-shipped gates pass before and after, and an
implementer who makes one of them go red has weakened a control rather than
earned a red. Each bullet says which it is.

- `packs/core/tests/pack/test_shaping_review_contract.py` — the existing
  `_mode_bodies()` helper at line 75 **cannot carry the new assertions**, and a
  probe over today's bytes says why: it slices only between `### <name> mode`
  headings, so the intent slice is 278 characters that already exclude the
  failure-mode table, while the `spec` slice runs 4,784 characters to end of
  file and swallows the shared output contract. An assertion that the table is
  absent from intent mode would therefore pass before any edit, and an
  assertion that spec mode keeps severity and `Fix:` would be satisfied by tail
  text rather than by spec-mode scope. The suite gains a slicing helper
  **parameterised by heading level**, because the three new assertions do not
  share one granularity and using a single level for all of them reintroduces
  the defect the probe was run to find:
  - **`##` granularity.** The failure-mode table's owning heading names
    `delivery-brief` and `spec` — fails today, where the heading is
    mode-agnostic.
  - **`##` granularity.** The output-contract section states the two-vocabulary
    split — fails today, where one `Result values:` line governs all three
    modes.
  - **`###` granularity, and this assertion decides where the token list
    lives.** `### intent mode` sits inside `## Scope` beside its two sibling
    rubrics, and that level stays, because the heading-set assertion at line 104
    is a preservation control. A `##` slice would therefore span all three
    rubrics: the six-token assertion would be satisfied by a token written in
    the `delivery-brief` or `spec` rubric, and the forbidden-element half would
    pass before and after, since `## Scope` carries no severity label, `Fix:`
    line, or `Clean` either way. Both halves slice at `###` on `### intent
    mode`, which means the **token list and the forbidden-element rule live in
    the intent rubric itself**, not in the shared `## Output contract` — that
    section keeps the `Clean | Findings` rules for the other two modes.

  The three-mode heading set and the tools, boundary, and authority assertions
  keep using `_mode_bodies()` and the whole-body helper unchanged; they are the
  controls that catch a regression in the two modes this change does not touch.

  **The inventory names suites and control classes, not every assertion.** Three
  review rounds established that enumerating predicted assertion-by-assertion
  outcomes for four prose-pinning suites is neither achievable in prose nor
  needed: each round found a new correct instance, and each instance was a
  question one `pytest` run answers in seconds. Per the pre-EXECUTE standard,
  fixture-internal detail is build-time guidance. So each implementing task runs
  its suites first, reads the actual failures, and classifies each against the
  changed-bytes list the spec fixes — an **earned red** when the failing
  assertion pins prose a criterion changes, a **weakened control** otherwise,
  which stops the task and surfaces. Known moves are recorded where they are
  known, as orientation rather than as a closed set: `"core-only viability"` at
  `test_shaping_review_contract.py:119` is intent-rubric prose the six-condition
  rewrite deletes; the trust-boundary sentence at line 159 is reworded; the
  severity and `Fix:` assertions at lines 129-130, the five field assertions at
  lines 121-128, and the material-edit and pre-seal sentences at lines 132-133
  re-point onto the section-scoped slices.
- **Changed bytes.** New assertions for the adversarial `intent` mode live in the
  same file, because it already owns the cross-reviewer boundary
  (`ADVERSARIAL_REVIEWER` at line 8) and the roster collision test.
- **A second suite pins and slices `adversarial-reviewer.md`, and T2 cannot start
  without it.** `packs/core/tests/pack/test_review_depth_and_verdict_contract.py`
  went unnamed in the first draft of this plan and is the larger hazard of the
  two:
  - it pins `LEGACY_REVIEW_MODES` — the whole "You handle three modes" block —
    verbatim at lines 39-61 and asserts it at line 110, so correcting the mode
    enumeration moves a byte pin;
  - it pins the bridge sentence and the ordering `legacy block < bridge <
    "## RFC review mode"` at lines 31-36, so the bridge edit moves with it;
  - it slices the file **end to end on consecutive `##` headings** with bare
    `text.index(...)`: `## RFC review mode` → `## Project-knowledge evidence
    boundary` at lines 91-92, 111-112, 123-124, and 156-157, then
    `## Project-knowledge evidence boundary` → `## Load context first` at lines
    142-144. The second slice carries a **negative** assertion,
    `"reviewer routing" not in shared_envelope` at line 151, which new prose can
    turn red with no changed-bytes warrant. Those two headings sit at
    `adversarial-reviewer.md:63` and `:88`, so **every position between the RFC
    heading and `## Load context first` is inside one slice or the other** —
    there is no safe insertion point, and choosing one is the wrong variable.
    T2 therefore makes the boundaries explicit rather than hunting a position:
    it bounds each slice on a marker that new content cannot widen, and the four
    boundary expressions plus the negative assertion are **changed bytes**. The
    four RFC-mode content assertions inside the first slice and the shared-
    envelope positive assertion inside the second stay **preservation controls**
    and must remain green.
  - Line 144's `raw.index("## Load context first")` is a prefix match, so
    scoping that heading by appending a qualifier does not raise; renaming its
    prefix would.
- **A third suite pins the same surfaces T2 re-points.**
  `packs/core/tests/pack/test_reviewer_project_knowledge_boundary.py` pins the
  `adversarial-review-complete` gate string at lines 11 and 36, requires
  `## Predicate self-check before emission` to be a top-level section rather than
  nested under a mode, pins its position before `## Report numbered findings`,
  and pins the six predicate names inside a slice bounded by the next `\n## `
  heading (lines 102-143). All of these are **preservation controls**: T2 scopes
  the gate sentence's applicability without moving the string, and the
  self-check section stays top-level, which is what lets both intent modes
  reference it.
- `packs/core/tests/skills/intake-intent/test_intent_shaping_review.py` —
  inventoried by assertion, not by function, because one function holds both
  kinds. **Changed bytes:** the `Clean`-gated assertions at lines 38, 40, and 42,
  and the `` "`Clean` or `Findings`" `` assertion at line 62, which sits inside
  the receipt test. **Preservation:** the receipt assertions at lines 59-61,
  which prove the caller-owned receipt survived the vocabulary change.
- `packs/product-engineering/tests/pack/test_frame_intent_shaping_review.py` —
  the integration entry is compared as a whole dict at lines 45-70, so the
  `fallback` string changes in test and manifest together; the prose assertions
  at 73-85 gain the adversarial-dispatch line.
- The shared trust-boundary sentence is pinned verbatim at
  `test_shaping_review_contract.py:159` in its `Clean`-only wording, so
  rewording it for both vocabularies moves that assertion in the same commit;
  the surrounding authority assertions stay as controls.
- The three eval harnesses are behavioral activation fixtures, not pytest
  suites: `packs/core/.apm/skills/intake-intent/evals/evals.json` carries the
  intent vocabulary at lines 28-62 and
  `packs/product-engineering/.apm/skills/frame-intent/evals/evals.json` at lines
  34-37. Their update is a read of the changed expectations, not a test run.
- Portability, projection parity, version parity, and the shaping-review
  documentation set are already-shipped gates; they are run, not written.

## Durable-output map

| Durable output | Tasks | Implementation evidence | Closeout evidence |
| --- | --- | --- | --- |
| Decision rationale — `docs/adr/0108-…md` | none (pre-existing) | ADR Accepted and indexed | this spec's `Constrained by:` resolves |
| User-facing promise — three guide passages | T6 | a read of each changed passage plus the `! grep -q` absence check; the roster documentation suite covers `core-pack.md` only | every changed passage reads true against shipped agents |
| Interface compatibility — `core-intent-shaping-review` entry | T3 | `test_frame_intent_shaping_review.py` whole-dict comparison | entry names no `Clean` |
| Release history — `docs/product/changelog.md` | T7 | free-standing `##` entry per pack | versions match the shipped manifests |
| Frozen-record navigation — superseded spec, plan, RFC | T5 | `git diff` shows only `Status` lines | pointers resolve to ADR-0108 |

## Design (LLD)

### Design decisions

- **Carry the table's scope in its heading, not in a caveat.** The spec owns the
  outcome — the table states the modes it governs and intent is not among them.
  The heading is the mechanism, chosen because a caveat would leave the rows
  readable as intent guidance and, per the probe recorded under Construction
  tests, would be unassertable: the table already sits outside the intent slice,
  so only a heading is visible to both a reader and a test.
- **The token list is the mechanism that makes the output closed.** Naming six
  literal tokens in the body is what lets the test pin the set and what stops a
  seventh from being invented at review time; a prose rule ("emit a malformed
  marker per failed field") cannot be checked.
- **`de-risk-intent` states the boundary, not a dispatch rule.** The skill has no
  reviewer section today, so the edit is one sentence in its existing
  anti-patterns surface rather than a new section that would imply the skill once
  had the behavior.

### Behavior & rules

Every observable rule lives in `spec.md`. The plan adds one non-inferable
mechanism: the six-predicate self-check is referenced in both intent modes by
pointing at `finding-adjudicator.md`, which already owns the predicates. What
must not be copied is a predicate's definition or the list as an authoritative
set; naming a predicate inside a binding statement is not a copy, because the
binding is the new fact and it cannot be written without the name.

### Dependencies & integration

No dependency changes. The only cross-pack edge is the existing
`core-intent-shaping-review` integration entry, whose consumer is
`skill:frame-intent` and whose provider stays `agent:shaping-reviewer`; the
adversarial dispatch rides the same optional-augmentation shape without a second
entry, because the roster forbids declaring a new integration for a review a
caller may skip.

## Tasks

### T1: shaping-reviewer intent mode is mechanical and MALFORMED-only

**Depends on:** none

**Touches:** `packs/core/.apm/agents/shaping-reviewer.md`, `packs/core/tests/pack/test_shaping_review_contract.py`

**Tests:**
- Add the level-parameterised helper described under Construction tests, then
  assert the six-token set and the forbidden elements against the `###
  intent mode` slice, and the table's scoping against the table section's own
  `##` heading.
- Keep `order findings by severity` and `concrete \`Fix:\`` asserted, but move
  them onto the output-contract section's `delivery-brief`/`spec` clause, so a
  regression that re-globalises them fails.
- `stub: true` — one compilable red assertion: the `### intent mode` slice
  contains `MALFORMED(statement)`. It fails on today's bytes and is the
  narrowest proof the new contract is present, and the `###` bound is what stops
  a sibling rubric from satisfying it.

**Approach:**
- Rewrite the `### intent mode` section as the six conditions, dropping the
  least-artifact-projection and falsifiability rubric prose that belonged to the
  quality read. The ownership-precedence passage stays where it is, governing all
  three modes; the intent section states no precedence sentence of its own.
- Scope the restated-guidance-is-degraded rule and the emphasis-density routing
  to `delivery-brief` and `spec`, which is where they are expressible.
- Move the failure-mode table under a heading that scopes it to `delivery-brief`
  and `spec`, leaving both rubrics otherwise untouched.
- Split the output contract by location, not only by wording: `## Output
  contract` keeps the `Result values:` line and the severity/`Fix:` rules for
  the other two modes, while the token list, the forbidden elements, the
  fail-closed rule for an unsettleable condition, the refusal sentence, and the
  empty-output-is-complete rule live inside `### intent mode`. That placement is
  what lets the token assertion slice at `###` and fail for the right reason.
- Reword the shared trust-boundary sentence so its fail-closed consequence
  covers both vocabularies, and move the pinned assertion with it.
- Scope the always-include result block and the material-edit/pre-seal sentence
  to the two `Clean | Findings` modes. These sit in the shared output-contract
  section and are pinned whole-body at `test_shaping_review_contract.py:121-133`,
  so those five field assertions and the two sentence assertions move onto the
  section-scoped slice in the same commit.
- Reference the adjudicator-owned self-check without restating the predicate
  names, and state how the consequence and proposed-mechanism predicates bind in
  a vocabulary that carries neither severity nor remedy.
- Keep the existing Scope refusal reachable from intent mode by giving the
  refusal its own sentence there: with empty output reserved for the well-formed
  case, a silent refusal would be read as a pass.

**Done when:** `python3 -m pytest packs/core/tests/pack/test_shaping_review_contract.py -q` is green and the failure-mode table's owning heading names `delivery-brief` and `spec`. The earlier form of this line asked whether the intent slice contained a table row, which the probe above had already shown passes before any edit — half a control that cannot fail, standing as the evidence for exactly the criterion it could not check.

### T2: adversarial-reviewer gains a narrowed intent mode

**Depends on:** none

**Touches:** `packs/core/.apm/agents/adversarial-reviewer.md`, `packs/core/tests/pack/test_shaping_review_contract.py`, `packs/core/tests/pack/test_review_depth_and_verdict_contract.py`, `packs/core/tests/pack/test_reviewer_project_knowledge_boundary.py`

**Tests:**
- New assertions in the same suite: the `intent` mode section exists, names the
  riskiest assumption and the non-goals as its mandate, names both output
  shapes with the kill-condition-plus-activity requirement, forbids Blocker,
  Concern, Nit, rewrite, and "consider also", and states that empty is complete.
- A preservation control that the existing `Clean — ready to commit.` sentinel
  and the `## Blockers` / `## Concerns` / `## Nits` format survive for the other
  modes — green before and after; it fails only if the new mode is written as a
  global narrowing.
- In `test_review_depth_and_verdict_contract.py`: move the `LEGACY_REVIEW_MODES`
  literal and the bridge assertion to the corrected enumeration, and make both
  slices' boundaries explicit enough that the intent branch cannot widen either.
  Those boundary expressions and the `"reviewer routing"` negative assertion are
  changed bytes; the four RFC-mode content assertions and the shared-envelope
  positive assertion are preservation controls and must stay green.
- In `test_reviewer_project_knowledge_boundary.py`: nothing moves. Its
  gate-string, top-level-section, position, and predicate-name assertions are the
  preservation controls that prove T2 scoped the gate's applicability without
  relocating the self-check section.
- `stub: true` — one compilable red assertion on the mandate sentence.

**Approach:**
- Make the pinning suite's slice boundaries explicit **before** adding the
  branch. The region between `## RFC review mode` and `## Load context first` is
  sliced end to end, so no insertion point avoids every slice; bound each slice
  on a marker new content cannot widen, then place the branch where it reads best
  for a human. The RFC branch remains the idiom to follow for a mode with no diff
  to infer from — with one limit: it *does* retrieve independently, so the intent
  branch carries its own trust paragraph rather than inheriting one.
- Correct the mode enumeration and the code-facing bridge so both read true with
  five modes, and keep the diff-inference trailer from reaching the intent
  branch. Both sit in byte-pinned text, so the literal in
  `test_review_depth_and_verdict_contract.py` moves in the same commit.
- State the two output shapes and the empty-result rule inside that branch only,
  and point the existing predicate self-check section at it.
- Scope `## Load context first` and the `adversarial-review-complete` gate
  sentence to the code-facing and RFC modes. Left global, they instruct the
  intent branch to read the guidance chain and the diff, and to satisfy a gate
  whose sentinel it never emits.

**Done when:** the suite is green and `grep -c '^## Blockers' packs/core/.apm/agents/adversarial-reviewer.md` reports 1 — the single line-initial occurrence in the output-format block, which the new mode must not duplicate.

### T3: both intent callers branch on the new vocabulary

**Depends on:** T1, T2

**Touches:** `packs/core/.apm/skills/intake-intent/SKILL.md`, `packs/core/.apm/skills/intake-intent/evals/evals.json`, `packs/product-engineering/.apm/skills/frame-intent/SKILL.md`, `packs/product-engineering/.apm/skills/frame-intent/evals/evals.json`, `packs/product-engineering/pack.toml`, `packs/core/tests/skills/intake-intent/test_intent_shaping_review.py`, `packs/product-engineering/tests/pack/test_frame_intent_shaping_review.py`

**Tests:**
- Rewrite the `Clean`-gated assertions in both caller suites as `MALFORMED`-gated;
  keep the `BLOCKED` receipt and the material-revision assertions unchanged as
  controls.
- Update the whole-dict integration comparison and the manifest in the same
  commit, since the test compares the entry by equality and will fail on either
  half alone.
- Add a `frame-intent` assertion for the optional adversarial dispatch and its
  no-lifecycle-effect clause.

**Approach:**
- In `intake-intent`, replace the revision-bound-`Clean` gate with the
  no-`MALFORMED`-token gate, keeping the human-confirmation step, the materiality
  list, and the nonmaterial-correction carve-out as they stand. Add the
  second receipt for a non-completing dispatch next to the existing
  unavailable-route receipt at `SKILL.md:128-129`, so the two causes stay
  distinguishable on the intent. Both callers' receipts follow the shape already
  shipped there — a `BLOCKED:` prefix, the gate name, then the cause — so the
  new one is a sibling string rather than a new receipt grammar.
- In `frame-intent`, replace the `Clean`/`Findings` binding at `SKILL.md:158-161`
  with the caller-owned revision binding and the token reading, keep the
  unresolved-token handoff block, and add the optional adversarial dispatch
  paragraph.
- Update the integration entry's `purpose` and `fallback` text.
- Rewrite the four intent-review eval expectations in `intake-intent` and the
  one in `frame-intent` against the shipped vocabulary, including the
  grounding-gap case, which currently expects a withheld `Clean`.

**Done when:** `python3 -m pytest packs/core/tests/skills/intake-intent packs/product-engineering/tests/pack -q` is green.

### T4: de-risk-intent declares the adversarial boundary

**Depends on:** T2

**Touches:** `packs/product-engineering/.apm/skills/de-risk-intent/SKILL.md`, `packs/product-engineering/.apm/skills/de-risk-intent/evals/evals.json`, `packs/product-engineering/tests/pack/`

**Tests:**
- One assertion that the skill body states it never dispatches
  `adversarial-reviewer`. The suite location follows the pack's existing
  per-skill test layout; if no `de-risk-intent` module exists, it is created
  alongside its siblings rather than appended to the frame-intent module.

**Approach:**
- Add the boundary to the skill's existing anti-patterns surface, with the reason
  (the skill authors the kill condition itself).
- Add one eval expectation covering the boundary and nothing about the intent
  vocabulary, which this skill never consumes.

**Done when:** the new assertion is green, `SKILL.md` mentions
`adversarial-reviewer` exactly once — on the boundary line — and
`evals/evals.json` carries exactly one expectation naming it. The check is
per-file rather than a recursive grep over the skill directory: the eval
expectation has to name the agent to pin the boundary, so a directory-wide
"exactly one hit" condition would be failed by the task's own second step.

### T5: frozen records point forward

**Depends on:** none

**Touches:** `docs/specs/shaping-review-contracts/spec.md`, `docs/specs/shaping-review-contracts/plan.md`, `docs/rfc/0099-cut-before-adding-and-artifact-shaping.md`

**Tests:** goal-based — `git diff` on the three files shows only `Status` lines changed, and `python3 '.claude/skills/work-loop/scripts/lint-spec-status.py' --root .` accepts the annotated status tokens.

**Approach:**
- Append the scoped supersession parenthetical to each `Status` line, naming the
  intent-mode part and stating that the rest stands.

**Done when:** the diff is three single-line changes and the spec-status lint is clean.

### T6: the two guide passages state the new contract

**Depends on:** T1, T3

**Touches:** `guides/product-engineering/how-to/shape-a-feature-intent.md`, `guides/core/how-to/start-or-remember-work.md`, `guides/core/explanation/core-pack.md`

**Tests:** goal-based — a read of each changed passage, plus
`! grep -q '`Clean`' <each intent passage>` so the absence check exits 0 on
no-match rather than being reported as a failure. The roster documentation suite
is run as a regression control only: its closed eight-document set contains
neither intent passage, so its greenness is evidence for other files and cannot
establish this task's outcome. It does cover `core-pack.md`, which is in that
set.

**Approach:**
- Replace the result-vocabulary sentences in both intent passages with the
  token-or-nothing description, and name the two adversarial output types only in
  the product-engineering guide, whose skill is the one that may dispatch them.
- Scope `core-pack.md`'s `adversarial-reviewer` description: its
  severity-labeled-findings and cannot-be-skipped claims hold for the code-facing
  and RFC modes, not for the optional `intent` mode.

**Done when:** the suite is green and both passages describe the shipped contract.

### T7: both packs release with matching versions and a changelog entry

**Depends on:** T1, T2, T3, T4, T5, T6, T9

**Touches:** `packs/core/pack.toml`, `packs/core/.claude-plugin/plugin.json`, `packs/product-engineering/pack.toml`, `packs/product-engineering/.claude-plugin/plugin.json`, `docs/product/changelog.md`, `web/src/lib/now-highlights.generated.json`, generated projections

**Tests:** goal-based — `FORCE=1 make build-self` from a clean tree, then
`agentbundle catalogue lint --root . --deep`, `agentbundle catalogue verify
--root .`, and the projection-parity suites. The changelog entry level is read
directly, because a versioned entry nested under `[Unreleased]` passes every
gate and never publishes. Because the entries carry `Highlights` bullets,
`python3 tools/build-site.py --journeys-only` regenerates
`web/src/lib/now-highlights.generated.json` in the same change, and
`tools/test_build_site_routing.py::test_the_committed_now_projection_matches_the_changelog_source`
is the gate that fails on a stale one.

**Approach:**
- Bump both packs one patch level in both files each: the owning rule gives
  patch for changed content, and this change adds no primitive — the adversarial
  `intent` mode is a mode inside an existing agent, and the spec's Boundaries
  forbid a new agent or skill.
- Regenerate projections and the marketplace manifest.
- Write one free-standing `##` entry per pack and record the `Highlights`
  verdict; this change alters what a consumer of either pack can do, so the
  bullets are drafted rather than declined. Each highlight is a `-` bullet — a
  paragraph is dropped by the projection silently.
- Regenerate the `/now/` projection in the same change.

**Done when:** the lint and verify commands pass, `git status` is clean after a
second `FORCE=1 make build-self`, and both entries sit at `##`.

### T9: the consequence predicate holds for a severity-free vocabulary

**Depends on:** none

**Touches:** `packs/core/.apm/agents/finding-adjudicator.md`, `packs/core/tests/pack/test_finding_adjudication_contract.py`

**Tests:**
- One assertion that the consequence predicate states its reading for a source
  finding whose vocabulary carries no severity. Changed bytes; the other five
  predicate assertions in that suite are preservation controls.

**Approach:**
- Add one clause to predicate 5 at its owning source: where the source finding
  states no severity, the consequence is tested alone. Predicate 6 needs
  nothing — its existing `absent` outcome already covers an emission that
  proposes no mechanism, which is why the intent modes cite it rather than
  redefining it.
- Touch no other predicate. This is the smallest edit that removes a
  consumer-side narrowing, and it lands at the source that owns the predicates
  rather than in either consumer.

**Done when:** the new assertion is green, the other predicate assertions are
unchanged and green, and neither intent mode states a reading the owner does not.

### T8: observed reviewer behavior is recorded

**Depends on:** T1, T2, T3, T7

**Touches:** `docs/specs/intent-review-mandate-split/notes/verification-ledger.md`

**Tests:** visual / manual QA — three dispatches (a malformed intent, a
well-formed intent, and one adversarial intent pass), each recording the exact
output observed and the projected agent revision it ran against.

**Approach:**
- Run after T7, not before it. A host dispatches these agents from the adapter
  projection, so a run taken earlier exercises the pre-change bodies while being
  written down as evidence for the new contract.
- Record the projection's revision alongside each observation, so a later reader
  can tell which bytes produced the output.
- Use a real intent from `docs/product/intents/` for the well-formed case and a
  scratch copy with two conditions broken for the malformed case, so the check
  runs against production-shaped input.

**Done when:** the ledger records each dispatch, the projected revision
dispatched, the observed output, and whether it matched the contract.

## Rollout

- **Delivery:** one PR, no flag. Both reviewers are invoked per-dispatch, so the
  new contract takes effect at the next dispatch after install; there is no
  migration and no in-flight state to drain.
- **Reversibility:** revert the PR. An intent already `Accepted` under the old
  `Clean` gate keeps its status, because materiality is unchanged and the
  transition already happened.
- **Deployment sequencing:** sources before projections before release entries;
  T7 is last for that reason.

## Risks

- **The mode-scoped table is re-globalised by a later edit.** Mitigated by the
  moved severity and `Fix:` assertions, which fail if the rules return to the
  whole body.
- **A caller keeps reading a result the reviewer no longer emits.** Mitigated by
  T3 landing both caller suites with T1 and T2, and by the whole-dict integration
  comparison that cannot pass on a half-update.
- **`MALFORMED` reads as a severity to a future author.** Accepted: the ADR
  records that the token vocabulary is the mechanism, and the forbidden-element
  assertion is the standing check.

## Changelog

- 2026-09-11 — Adversarial spec-mode review, round 3: 6 findings, 4 sustained,
  2 refuted. Two were real target-state defects. The agent's findings-report,
  output-format, cross-lens-referral, and finding-specificity mandates are
  global, so the shipped body would have instructed the intent branch to group
  by severity, append a `Fix:`, and emit the clean sentinel — all three
  forbidden by its own criteria; four criteria now scope them. And the slicing
  helper was declared at `##` granularity while two of its assertions target
  `### intent mode`, which sits beside its sibling rubrics inside `## Scope` — so
  the six-token assertion would have been satisfiable by a token in another
  rubric, and the forbidden-element half could not fail at all. The helper is now
  level-parameterised, and the token list moves into the intent rubric so the
  assertion can isolate it. T1's and T4's `Done when` lines each carried a false
  observable and were corrected.
- 2026-09-11 — Owner decision closing the pre-EXECUTE lane: the assertion
  inventory stops predicting per-assertion outcomes across four prose-pinning
  suites and names suites plus control classes instead, with each task running
  its suites first and classifying the real failures as earned red or weakened
  control. Three rounds each found a new correct instance of the same class,
  every instance being something a `pytest` run settles immediately, and the
  pre-EXECUTE standard treats fixture-internal detail as build-time guidance.
  This lane closed on every sustained finding repaired, not on a clean verdict.
- 2026-09-11 — Adversarial spec-mode review, round 2: 7 findings, 3 sustained,
  4 refuted as the same build-time-guidance class round 1 refuted. The sustained
  blocker was the strategy, not the position: `test_review_depth_and_verdict_contract.py`
  slices `adversarial-reviewer.md` end to end on consecutive `##` headings, and
  the second slice carries a *negative* assertion, so every position between the
  RFC heading and `## Load context first` is inside some slice and picking one is
  the wrong variable. T2 now makes the boundaries explicit first and places the
  branch where it reads best. A third suite,
  `test_reviewer_project_knowledge_boundary.py`, entered the inventory as
  preservation controls only, and the two spec enumerations that still said "the
  two agent bodies" were widened to the three T9 makes true.
- 2026-09-11 — Adversarial spec-mode review, round 1: 14 findings, 11 sustained
  after adjudication, 3 refuted. The sustained blocker that mattered was a whole
  suite this plan never named —
  `packs/core/tests/pack/test_review_depth_and_verdict_contract.py` byte-pins the
  adversarial reviewer's mode enumeration and slices its body with bare
  `text.index(...)`, so the obvious insertion point for the intent branch would
  have widened four RFC-mode assertions into it. The branch now lands after
  `## Project-knowledge evidence boundary`, outside that slice. Also sustained:
  the agent's own "three modes" header and code-facing bridge were uncontracted
  and would have shipped false; T8's manual QA ran before the projections it
  dispatches from existed, so it now depends on T7 and records the projected
  revision; the Construction-tests preamble claimed red-first over preservation
  controls, the exact hazard Testing Strategy names; `core-pack.md:69`
  over-claims for the new mode and a `Clean` grep could never have found it; and
  T3's inventory had one assertion in both the convert and leave-alone sets. A
  new T9 puts the consequence predicate's severity-free reading at the source
  that owns the predicates, so neither intent mode narrows the owner's text.
  Three findings were refuted on existing handling: per-criterion assertion
  enumeration, a per-capability eval expectation, and T4's module path are all
  build-time guidance that cannot prevent a planning-level `Clean`.
- 2026-09-11 — Shaping review round 5 returned eight findings; all eight
  dispositioned as adopted, and the round closed there rather than iterating to a
  clean verdict. Four were target-state contradictions the contract could not
  have shipped with: a red-first verification claim made over criteria that must
  pass today, a Boundaries rail that forbade the retrieval the adversarial
  reviewer's other modes are built on, an Objective that restated the `Accepted`
  gate without its completion leg, and drafted `Highlights` bullets that oblige a
  `/now/` projection regeneration no task named. The rest removed second homes —
  the guide row, the predicate pair, the table's mechanism — and assigned the
  three pieces of mode-agnostic failure-mode prose a home each. The ownership
  precedence stays where it is, governing all three modes, and the intent section
  now states no precedence sentence of its own, so `MALFORMED(owner)`'s
  suppression rule is its single carrier.
- 2026-09-11 — Shaping review round 4 returned two blockers, both
  `prior-round-repair` origin: round 3's prose-refusal criterion contradicted the
  untouched closed-vocabulary criterion and Objective, and the Testing Strategy's
  first bullet claimed pack-test coverage for criterion groups that grew after it
  was written. The closed set is now scoped to *result* values for an in-scope
  target with the refusal admitted as the one non-result output, and Testing
  Strategy declares a mode for the eval harnesses, the frozen-record pointers,
  and the changelog. Three concerns adopted: the adversarial mode's empty output
  is stated as advisory and establishing nothing, which is why it needs none of
  the three completion controls the well-formedness mode has; all six predicates
  now state their binding rather than two; and two closeout cells lost rationale
  the plan's Changelog already owns.
- 2026-09-11 — Shaping review round 3 returned seven findings. Four clustered on
  one premise — an empty pass state carries no bytes, so a well-formed intent, a
  refused target, and a dead dispatch are the same output — and the owner settled
  it: empty means the six conditions hold and nothing else, an out-of-scope
  target draws a prose refusal, completion is read from the host's dispatch
  outcome, and each caller owns a receipt naming a non-completing dispatch. The
  other three were adopted directly: the adversarial `intent` branch carries its
  own trust-boundary paragraph, because that agent states its untrusted-data
  rules per branch and ships with `Bash`; its `description` gains the mode and
  scopes the re-run-until-`Clean` instruction; and the table-scoping criterion
  now names its failing observation.
- 2026-09-11 — Shaping review round 2 returned nine findings, no blockers; eight
  adopted as stated. The shared output-contract block and the material-edit rule
  are now scoped to the two `Clean | Findings` modes, so the shipped body cannot
  demand metadata from a mode whose pass state is empty. `frame-intent` gained
  the two lifecycle criteria it was missing, a non-completing dispatch gained its
  own receipt rather than borrowing the unavailable-route one, the eval
  obligation split along the dispatch boundary, the guide obligation split per
  guide, and the two predicates written for a severity-and-remedy vocabulary now
  state how they bind. On the ninth, the reviewer's first fix rested on a premise
  the ADR template contradicts — `Supersedes:` carries ADR ordinals only, and the
  ADR already points at the superseded RFC section through `Related:` and
  `References` — so the durable-output row states the one-way convention instead.
- 2026-09-11 — Plan drafted from ADR-0108 with the caller, guide, and release
  tasks separated from the two contract tasks, so the two agent bodies can land
  and be reviewed before anything depends on their new vocabulary.
- 2026-09-11 — Shaping review round 1 returned three blockers and eight
  findings, all adopted. The caller now owns the revision binding an empty
  result cannot carry; an unsettleable condition emits its token instead of
  passing; the three eval harnesses entered scope; `MALFORMED(owner)` suppresses
  the other tokens rather than joining them; the bump level is derived from the
  owning rule rather than fixed at minor; and the adversarial observation gained
  a positive path so it can fail. ADR-0108 was corrected to six conditions
  before commit so the governing record does not ship false.
- 2026-09-11 — A throwaway probe over the reviewer body disconfirmed the first
  test design: the existing mode-slicing helper made the table-scoping assertion
  unfailable and the severity assertion tail-satisfied. T1 now adds a
  `##`-section helper, and the table's scoping is carried by its heading so both
  a reader and a test can see it.
