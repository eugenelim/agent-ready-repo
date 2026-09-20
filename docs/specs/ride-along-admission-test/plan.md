# Plan: Ride-along admission test

- **Spec:** [`spec.md`](spec.md)
- **Status:** Approved <!-- Drafting | Approved | Executing | Done -->
- **Repository anchors:** `packs/AGENTS.md` (§ Version bump rule, § Shipped
  pack content carries no internal-governance citations, § Self-hosting
  projection) and `packs/core/AGENTS.md`; analogous implementations —
  `packs/core/tests/pack/test_review_depth_and_verdict_contract.py` and
  `packs/core/tests/pack/test_spec_authority_scoping.py`, both cross-file
  prose pins over `.apm/` sources under the same `PACK_ROOT` idiom, collected
  by `Makefile:590` and `.github/workflows/build-check.yml:445`; named
  uncertainty — the sites sit at three different indent levels and one is
  inside a quoted brief, so a clause cannot be byte-identical as written and
  the control normalises whitespace instead (see Design decisions).

> **Plan contract:** this is the implementation strategy. It may change
> substantively only while its Status is `Drafting`, before approval records its
> baseline. After approval, `spec.md` and `plan.md` are pinned in substance;
> only lifecycle bookkeeping is permitted, and execution observations belong in
> `docs/specs/<feature>/notes/verification-ledger.md` (or the adopter's
> equivalent). A genuine artifact error follows the controlled-amendment path.
>
> **Not every field is contract.** `Touches`, `Tests` and `Done when` are what a
> completion gate reads, and they are pinned. `Design`, `Approach`, `Grounding`
> and `Risks` are working material that an implementer corrects in place only
> before approval: approval hashes the whole plan. After approval, grounding for
> a seam recorded as `no stub (implementation-discovered)` goes to the
> verification ledger; a settled design decision that execution falsified is a
> plan error that follows the controlled-amendment procedure. Treating them as
> contract is how a review spends a round on prose no gate consumes — the
> measured share is over half the plan's lines. `Grounding` stays *recorded*,
> because a per-task resolution that nobody wrote is not grounding; what it stops
> being is a claim a reviewer holds the plan to.

## Approach

The control comes first, because the defect being fixed is that nothing held
the sites together. T1 writes `test_ride_along_admission_test.py` against
clauses that do not exist yet and proves it red. T2 lands C1, C2, C3, the
sync comments, the report-template fields, and the retired-vocabulary sweep
across all four sites in one pass — the clauses sit in the same paragraphs, so
splitting them would reopen each host twice and leave shared test functions
half-green at the boundary. T3 and T4 are prose edits inside `SKILL.md` that
the same test file pins by equality. T5–T7 are the governance, release, and
projection tail.

The riskiest part is the `work-loop/SKILL.md` body-line budget, sized in
`Risks`.

## Constraints

- RFC-0090 § Vocabulary and § Tail-triage lane define the three tiers this
  change replaces. It is Accepted and frozen, so the correction is an
  append-only `Errata` entry per RFC-0055 §D1 and §D3, Approver-signed.
  Whole-RFC replacement is outside RFC-0055's scope and is not attempted.
- ADR-0088 gives the risk triggers a single documented home.
  `tools/lint-agents-md.py` check 10g enforces it in two ways: its `rglob`
  sweep (`:547-555`) fails any `*.md` outside the three work-loop `SKILL.md`
  homes that carries a `risk-triggers:start` marker at all, byte-identical or
  not, and its comparison branch (`:594-602`) fails divergence among the three
  homes. The sweep skips vendored, fixture, and frozen-record files, so those
  three classes are its blind spot. C1 therefore names the concept and C3
  points at the skill; neither carries a marker or a trigger.
- `packs/AGENTS.md` § Version bump rule: matching patch bump in `pack.toml`
  and `.claude-plugin/plugin.json`, and do not borrow an unreleased version
  from another change; § Shipped pack content carries no internal-governance
  citations: no RFC, ADR, spec, or PR reference inside `packs/`;
  § Self-hosting projection: `.apm/` is source, projections are generated; a
  non-cosmetic pack update also updates the pack's eval harness.

## Construction tests

**Integration tests:** none beyond per-task tests. Every criterion is a
content property of a file already on disk; nothing crosses a process or
component boundary.

**Manual verification:** after T7, read the installed
`.claude/skills/work-loop/SKILL.md` and walk the spec's three worked
discoveries through the changed EXECUTE and `## Capture` text, recording the
route each takes. The section was renamed by T4; this line named the retired
heading until amendment five corrected it. Observations go to the verification ledger.

## Durable-output map

| Durable output | Tasks | Implementation evidence | Closeout evidence |
| --- | --- | --- | --- |
| Published agent behaviour — four `.apm/` sites | T1, T1b, T2, T3, T4, T7 | `packs/core/tests/pack/test_ride_along_admission_test.py` green; the AC8 mutation record (T4) in the verification ledger | Every clause sits in its host at every site it belongs to; projections match |
| Decision rationale — RFC-0090 § Errata | T5 | Dated, Approver-signed entry; lines above `## Errata` unchanged against the merge base | The erratum names the replacement and its reason |
| Release history — changelog and both version files | T6 | Both version files one patch above the changelog's highest `[core]` version; topmost heading matches with `### Highlights` | Version and release note agree; no duplicate `[core]` version |
| Adopter documentation — the published guide | T1b, T4 | `tests/roster/test_capture_rename_guide.py` green; `lint-ci-parity.py` exits 0 | The guide names the step as shipped and its roster step is registered and placed |
| Reusable learning — work-loop eval register | T6 | Two new cases in `evals/evals.json` | One grades dispatch over discard; one grades the unattended fall-out |

## Design (LLD)

### Design decisions

Traces to: AC1–AC8 · contracts: none.

- **Three shared clauses, not one.** C1 is the test, C2 resolves its clause
  (ii), C3 points at the triggers. They are separate strings because their
  site sets differ: C1 and C2 go to all four sites, C3 to the three mirrors
  only, since `SKILL.md` links its own in-file anchor and a path pointer there
  would point out of itself.
- **Every shared clause is site-independent.** `supervisor-mode.md` does not
  read its copy — it reproduces it inside a brief the supervisor pastes into a
  subagent prompt. A deictic phrase such as "this file" therefore refers to
  nothing the reader holds, which is why C3 says "a mirror" and C2 names no
  document.
- **The control normalises whitespace rather than comparing raw bytes.** The
  clauses sit at column 0 in `SKILL.md`, indented two spaces inside a bullet
  in `implementer.md`, three inside a numbered item in
  `adversarial-reviewer.md`, and inside a quoted string in
  `supervisor-mode.md`. Raw byte-identity is unachievable across those four,
  and a control that cannot pass is not a control. Collapsing each whitespace
  run to one space compares the words and the punctuation and ignores the
  wrapping. **Named blind spot:** it does not detect a rewrap, by design, and
  does not detect a paraphrase moved outside the matched span — AC7's
  vocabulary sweep is what catches retired wording surviving elsewhere.
- **Normalise the whole file, then extract — not the reverse.** A disposable
  spike over the four indent shapes disconfirmed the obvious order: extracting
  a span first and normalising it afterwards fails, because wrapping splits a
  clause's closing words across a line and no single-line end-anchor matches.
  Collapsing every whitespace run in the file first, then slicing between each
  clause's opening and closing literals, returns one identical value at all
  four indent levels and `None` when the clause is absent.
- **Identity alone is insufficient: the control also counts and anchors.**
  Four ways identity can hold while the shipped instruction is broken, each
  answered by an assertion. A clause pasted into the existing HTML sync
  comment satisfies identity while the normative bullet instructs nothing —
  answered by AC5's host check, which reads the raw un-normalised line so the
  two mechanisms do not fight. A second, divergent copy later in the same file
  passes a first-match comparison — answered by AC4's exactly-once count,
  which matters most in `implementer.md`, whose report template at `:125-129`
  already describes the carve-out a second time. A consistent reword of a
  closing anchor makes every extraction `None`, and "one distinct value" over
  an empty set passes — answered by asserting each extraction is non-`None`
  before comparing. A mis-scoped count or a comparison over two mirrors
  instead of three passes all of the above — answered by AC8's mutation set,
  which is why it names five mutations reaching AC1, AC4, AC5, AC3 and AC6
  rather than only the two the identity check owns.
- **Clause (ii) refuses an unresolved design call, not a design call.** The
  bound that survives is behaviour plus resolution, not difficulty. C2 states
  no test of how easy a decision looked, because a rule of that shape would
  license an agent to decide anything it found obvious; admissibility turns on
  the decision having been made and being recorded.
- **Attendance has two channels, and the direct one is the human gate.** A
  dispatch brief declares it, which covers supervised runs. A maintainer
  invoking the loop directly writes no brief, so if declaration were the only
  channel every direct run would be unattended and the owner at the keyboard
  could never give the one-line answer C2 authorises — the attended branch
  would be dead prose on the most common invocation. C2 therefore carries the
  question to the human gate the loop already stops at, where the answer is
  observed rather than inferred and an unanswered question falls out to
  capture. This adds no state: the gate exists, and the fix returns over the
  same `blocker-applied` edge C4's other routes use.
- **Both same-session routes reuse `("CODE-HUMAN-GATE", "blocker-applied")`**
  (`loop-engine.py:665`), already described at `SKILL.md` § REVIEW under
  "Further in-intent review unit". C4 names that route rather than restating
  its command sequence.

### Behavior & rules

Traces to: AC9–AC14 · contracts: none.

- **The DECIDE table gains a row, not an exception.** The existing
  `Does not match | Include now` row says "obtain an explicit scope change; it
  then becomes accepted intent" — it assumes including something means adding
  it to the contract. A ride-along never enters the contract: it alters no
  acceptance criterion, so `approved_spec_hash` does not move, and the finish
  checklist requires every final accepted AC to be `[x]` without requiring the
  converse. The new row is the case the table did not cover.
- **Five destinations, ordered rather than partitioned.** The scratch-note
  bullet currently routes two ways and ends "otherwise discard it", which
  throws away a specific, real, non-generalisable defect. A four-route set —
  project-knowledge, dispatch, capture, discard — leaks a ready-now defect
  that is not ride-along eligible, because capture is reserved for blocked
  work and discard for taste. `SKILL.md:670-674` already routes that item to
  "the next independently reviewed unit in the same session", so C4's fifth
  destination names a route the skill owns rather than inventing one.
  Disjointness then fails twice: a decision-blocked item matches both capture
  and the same-session route, and a note that is both generalisable and
  fixable matches both the seam and a defect route. C4 answers the first with
  an explicit order — first match wins, capture before the same-session route
  — in the same form `SKILL.md:689-691` already uses for the answer ladder,
  and the second by naming the seam as the one destination reachable in
  addition to another. AC14 walks three notes against that order.
- **The four example bullets below the scratch note stay, and are scoped.**
  `SKILL.md:859-862` name destinations for *generalisable* material. C4 says
  in one clause that they are instances of its first route, so the section
  cannot be read as routing eight ways.
- **Grouping is preferred over per-item dispatch.** Correcting one instance of
  a stale literal while leaving its siblings wrong is worse than fixing all or
  none, so related fixes sharing a file or a seam go out as one dispatch.
- **A captured item carries its discriminator.** Close-time capture
  reconstructs from the diff, which recovers the locator and loses the fact
  the decision turns on. C5 carries both that obligation and the economics
  that justify dispatching in preference to recording.

### Component / module decomposition

Traces to: AC1–AC14 · contracts: none.

Two new files, split by reach rather than by topic, because
`tools/lint-pack-test-boundary.py` check `pack-tests-stay-in-pack` fails any
pack test that climbs out of its own pack and the rule has no exemption.

- `packs/core/tests/pack/test_ride_along_admission_test.py` — AC1–AC13 and
  AC20–AC22, the criteria decided by reading a file inside `packs/core/`.
  Not AC14 (a recorded walk), AC15–AC17 (repository documents outside the
  pack), AC18–AC19 (read from the eval register by T6), or AC23–AC24.
  Standard library only (`pathlib`, `re`), resolving `PACK_ROOT` as
  `Path(__file__).resolve().parents[2]` exactly as its two sibling pack tests
  do. Every path it reads is inside `packs/core/`.
- `tests/roster/test_capture_rename_guide.py` — AC23 and AC24. AC23 is the
  one check that reads `guides/core/explanation/core-pack.md`; AC24 parses
  `.github/workflows/build-check.yml`. Both sit outside `packs/core/`, which
  is why they share this file. Anchored at
  `Path(__file__).resolve().parents[2]` per `tests/AGENTS.md`.

This is the split commit `b14725c01` used for the same shape, pairing
`packs/core/tests/pack/test_spec_authority_scoping.py` with
`tests/roster/test_spec_authority_note.py`. Reused: nothing else. No new
module, boundary, or dependency.

### Interfaces & contracts

Not applicable — this change exposes and consumes no interface surface.

### Data & schema

Not applicable — no entity, field, migration, or persisted value changes.

### State & control flow

Not applicable — the engine's state machine is unchanged; both same-session
routes reuse an existing edge.

### Failure, edge cases & resilience

Not applicable — no external call, retry, timeout, or partial-failure path.

### Quality attributes (NFRs)

Not applicable as a criterion. The one numeric bar this change approaches —
the skill body cap — is owned by `CAT-S003`; its measured budget and headroom
are in `Risks`, stated once.

### Dependencies & integration

Not applicable — no external system, service, or library is added.

## Tasks

### T1: The clause control reds before the clauses exist

**Depends on:** none

**Touches:** packs/core/tests/pack/test_ride_along_admission_test.py

**Tests:** this task *is* the test. Verification mode: TDD.
- `test_c1_is_identical_across_the_four_sites`, `test_c2_…`, `test_c3_…` —
  collapse each file's whitespace runs to single spaces, slice between the
  clause's opening and closing literals, assert the slice is not `None` for
  each site that carries it, then assert one distinct value. Verifies AC1,
  AC2, AC3. Compilable red contract-surface assertion (`stub: true`):
  extraction returns `None` everywhere on the current tree, so each reds on
  absence.
- `test_clause_anchors_occur_exactly_once_where_carried` — each clause's
  opening words appear once in every carrying file and zero times elsewhere
  among the four. Verifies AC4.
- `test_clauses_sit_in_their_hosts` — for each site, the raw un-normalised
  line carrying the opening words is not inside an HTML comment or a fenced
  block, and the nearest preceding host marker is the one § Host markers
  names. Verifies AC5.
- `test_sync_comments_name_four_sites` — each of the four files carries an
  HTML comment containing `Bundled-fixes carve-out`, and each names all four
  sites adopter-visibly (`work-loop/SKILL.md`, `implementer.md`,
  `adversarial-reviewer.md`, `work-loop/references/supervisor-mode.md`), never
  a `packs/core/.apm/…` path. Verifies AC6. Reds today: `supervisor-mode.md`
  has no such comment and the other three name three sites.
- `test_retired_locality_vocabulary_is_absent` — none of the seven banned
  strings appears in any of the four files. Verifies AC7.
- Equality assertions for AC9, AC10 and AC11 over `SKILL.md`, and for AC12
  and AC13 over `implementer.md` and `supervisor-mode.md`: the exact
  disposition sentence, C4, C5, C6, C7, and the absence of
  `otherwise discard it`. C6 and C7 are pinned strings like the rest, so
  these are equality checks rather than readings of prose.
- `test_capture_heading_renamed` — `## Capture` present, `## Capture
  learnings` absent, and no link in the file targets `#capture-learnings`.
  Verifies AC20.
- `test_capture_anchor_links_resolve` — every in-file link targeting
  `#capture` resolves to a heading present in the file. Verifies AC21. Scoped
  to `#capture` rather than to every anchor: an unscoped check passes today,
  because each existing `#capture-learnings` link resolves against the
  un-renamed heading, so it could not red for the stated reason.
- `test_no_eval_prompt_names_the_old_section` — no case in
  `packs/core/.apm/skills/work-loop/evals/evals.json` has a prompt naming a
  `Capture learnings` section. Verifies AC22. This path is inside
  `packs/core/`, so it stays here.
- AC23's guide check is **not** in this file. It reads outside `packs/core/`
  and belongs to T1b.

**Approach:**
- Write the whole file now, red, rather than growing it per task: the identity
  assertions are meaningless until the sites move together, so a test added
  after T2 could never have failed for the reason it exists.

**Done when:** `python3 -m pytest packs/core/tests/pack/test_ride_along_admission_test.py -q`
fails, every assertion above is among the failures rather than erroring on a
missing file, and `python3 tools/lint-pack-test-boundary.py` exits 0 —
unfiltered, reading its own exit code, because piping it through `tail`
truncates the FAIL lines and reports the filter's status instead.

### T1b: The guide control reds, from the roster where it may read a guide

**Depends on:** T1 — T1 is what removes the AC23 guide read from the pack
file, so `lint-pack-test-boundary.py` cannot exit 0 until it has landed, and
this task's own `Done when` asserts that exit code.

**Touches:** tests/roster/test_capture_rename_guide.py,
.github/workflows/build-check.yml, tools/lint-ci-parity.py

**Tests:** verification mode: TDD.
- `test_guide_names_the_step_as_shipped` — `guides/core/explanation/core-pack.md`
  names the step `Capture` and describes it as routing a scratch note rather
  than only recording a learning. Verifies AC23. Reds today: the guide's
  step 10 reads "Capture learnings".
- `python3 tools/lint-pack-test-boundary.py` exits 0, read unfiltered.
  Verifies that the split actually discharges the boundary rule rather than
  moving the violation.
- `python3 tools/lint-ci-parity.py` exits 0 after the registration edits.
  This verifies registration and disposition; it does **not** reach step
  order, so it does not verify AC24.
- `test_roster_step_precedes_the_bulk_pytest_step` — parses
  `.github/workflows/build-check.yml`, finds the step naming
  `tests/roster/test_capture_rename_guide.py` and the step running
  `python -m pytest tests/ -q`, and asserts the first index is lower.
  Verifies AC24. It reds when written and this task turns it green, because
  this task owns the workflow edit; AC23's guide assertion is the only one
  still red at the end of T1b, and T4 owns turning it green.

**Approach:**
- Anchor at `Path(__file__).resolve().parents[2]` per `tests/AGENTS.md`, not
  at a pack root.
- `tests/AGENTS.md` obliges three registration edits, two of which apply
  here: a named step in `.github/workflows/build-check.yml` placed **above**
  the bulk `python -m pytest tests/ -q` at line 442 — the job is fail-fast
  with no step-level `if:`, so a named step below it never runs — and a
  matching `STEP_DISPOSITION` entry in `tools/lint-ci-parity.py` with
  `LOCAL("test-after-build-check")`. The third, a
  `.workspace-prune-protected.toml` entry, does not apply: this test names no
  `docs/specs/<slug>` path as a literal.
- Place the step beside the existing `tests/roster/test_spec_authority_note.py`
  step at line 436, which is already above the bulk step for the same reason.

**Done when:** `python3 -m pytest tests/roster/test_capture_rename_guide.py -q`
fails on the AC23 guide assertion and **only** that one — the AC24 step-order
assertion passes, because this task makes the workflow edit it checks — and
`python3 tools/lint-pack-test-boundary.py` and `python3 tools/lint-ci-parity.py`
each exit 0, read unfiltered.

### T2: C1, C2, C3 and the reporting fields replace the tiers at every site

**Depends on:** T1

**Touches:** packs/core/.apm/skills/work-loop/SKILL.md,
packs/core/.apm/agents/implementer.md,
packs/core/.apm/agents/adversarial-reviewer.md,
packs/core/.apm/skills/work-loop/references/supervisor-mode.md

**Tests:** verification mode: TDD — the assertions exist and are red before
this task writes anything, and this task is what turns them green.
- T1's AC1, AC2, AC3, AC4, AC6 and AC7 assertions go green, and AC5 goes
  green for C1, C2 and C3. AC4 and AC5 are single functions spanning all
  three clauses, so they can only go green once all three have landed —
  which is why this task lands them together rather than in two passes.
- T1's AC12 and AC13 assertions go green: the report entry carries its
  question-and-answer field and the dedup instruction excludes entries whose
  recorded questions differ.
- `python3 -m pytest packs/core/tests/pack/ -q` stays green — the sibling
  prose pins in `test_review_depth_and_verdict_contract.py` and
  `test_spec_authority_scoping.py` read the same two agent files.
- AC8's mutations are not run here. They require a green suite, and C4 and C5
  land in T4, so at the end of this task AC10 and AC11 are still red and no
  mutation's red could be attributed to the mutation.

**Approach:**
- Eleven sites carry retired or now-insufficient text, not four paragraphs.
  Beyond the four clause hosts: `SKILL.md:765` gates Concerns on "the
  accepted contract and bundled-fixes tiers" and becomes "the accepted
  contract and the bundled-fixes carve-out"; `SKILL.md:672` says the same in
  the DECIDE prose; `implementer.md:126`'s report template says "same-area
  mechanical ride-alongs landed under the carve-out" and becomes
  "ride-alongs landed under the carve-out", and gains C6; the dedup
  instruction at `supervisor-mode.md:194` falls back to "operator judgment
  when two lines describe the same change in different words" and gains C7 as
  an exception to that fallback; the sync comments at
  `SKILL.md:415-417`, `implementer.md:50-52` and
  `adversarial-reviewer.md:251-253` each say "all three sites" and must name
  four; and `supervisor-mode.md` gains the fourth comment, which it lacks.
- The sync comments name files the way an adopter sees them —
  `work-loop/SKILL.md`, `implementer.md`, `adversarial-reviewer.md`,
  `work-loop/references/supervisor-mode.md` — never `packs/core/.apm/…`,
  which does not exist in the installed projections and which
  `packs/AGENTS.md` forbids in shipped pack content.
- C2 follows C1 directly at each site: clause (ii)'s "unresolved" is
  unreadable without it, and the two occupy one paragraph block per host.
- `implementer.md:53-56` keeps its conditionality: a noticed unrelated issue
  still defaults to "Out of scope observed", and the carve-out still requires
  the supervisor's brief to authorise it. Only the admission test changes.
- `supervisor-mode.md:129-132` cannot take C1 by substitution. Its host reads
  `"Bundled fixes authorized per the carve-out in \`work-loop/SKILL.md\`
  (EXECUTE phase); apply same-area, same-concern, mechanical ride-alongs only
  and report under \`Bundled fixes:\` in your output."` Splicing C1 into the
  `apply …` slot produces "apply A change may ride along when …". The line is
  rewritten so each clause appears as a whole sentence: it opens
  `"Bundled fixes authorized per the carve-out in \`work-loop/SKILL.md\`
  (EXECUTE phase).`, then C1, then C2, then C3, then the attendance
  declaration, then `Report each ride-along under \`Bundled fixes:\` in your
  output."` The attendance sentence is
  `This run is <attended|unattended>.` A brief that omits it declares
  nothing, and C2's human-gate route is what a direct run uses instead.
- The surrounding paragraph at `supervisor-mode.md:133-136` already says an
  omitted authorization line means no carve-out. It is left alone: it governs
  the line's absence, not its content.

**Done when:** T1's clause, comment and reporting assertions are green, and
`git grep -nE 'same-area|visibly smaller|Tier [123]|bundled-fixes tiers' --
packs/core/.apm/skills/work-loop/SKILL.md
packs/core/.apm/agents/implementer.md
packs/core/.apm/agents/adversarial-reviewer.md
packs/core/.apm/skills/work-loop/references/supervisor-mode.md`
returns nothing. The pathspec names the four files rather than
`packs/core/.apm/`, which also contains
`scripts/lint-traceability.py:275`'s unrelated `Tier 3:` comment and would
make the condition unsatisfiable.

### T3: DECIDE routes a non-matching, ride-along-eligible discovery

**Depends on:** T2

**Touches:** packs/core/.apm/skills/work-loop/SKILL.md

**Tests:** verification mode: TDD — AC9's equality assertion is already red
from T1 and this task turns it green.
- T1's AC9 assertion goes green, matching the pinned disposition sentence
  exactly.

**Approach:**
- The row goes directly below the existing `Does not match | Include now` row,
  so a reader meets the discriminator beside the row it distinguishes.

**Done when:** the AC9 assertion passes.

### T4: Capture is renamed, routes five ways, and states what capture costs

**Depends on:** T3, T1b

**Touches:** packs/core/.apm/skills/work-loop/SKILL.md,
packs/core/.apm/skills/work-loop/evals/evals.json,
guides/core/explanation/core-pack.md

**Tests:** two modes, one per work item. TDD for the clause text and the
mutation set — AC10, AC11 and AC8 are decided by assertions in the suite.
Goal-based check for AC14's routing walk — C4's destinations are prose, so
the check is a recorded walk against the clause as written, not an assertion.
- T1's AC20, AC21 and AC22 assertions go green, and T1b's AC23 assertion goes
  green: the heading is `## Capture`, no link targets `#capture-learnings`,
  every `#capture` link resolves, no eval prompt names the old section, and
  the guide names the step as shipped.
- T1's AC10 and AC11 assertions go green: the scratch-note bullet reads
  exactly C4, `## Capture learnings` contains C5, and
  `otherwise discard it` is gone.
- AC14's five worked notes are walked against C4, each reaching its named
  destinations and no others, recorded in the verification ledger.
- AC8's five mutations each red the suite, applied one at a time to the tree
  as it stands at the end of this task — the first point at which the suite
  is green and a single red is attributable — with the caught assertion named
  for each. Verifies AC8.

**Approach:**
- The rename lands with the routing change rather than separately: the old
  heading named the section's old job, and the two in-file links at
  `SKILL.md:776` and `:819` carry `#capture-learnings` anchors that break the
  moment the heading moves. The checklist item at `:819` also stops being
  true — "Learnings captured" no longer describes a section that dispatches
  and opens review units — so it becomes a scratch-note disposal item.
- `evals.json`'s existing `capture-learnings-quality-attributes` case has a
  prompt reading "you have completed a work-loop and are at Capture
  learnings"; the prompt is corrected and the case id left alone, because the
  id is an identifier rather than a reference to the heading.
- `docs/knowledge/topics/*.json` carry `semantic_gate: "capture-learnings"`.
  That value is validated only as a slug
  (`project-knowledge/scripts/knowledge_store.py:921`) against no controlled
  list — siblings in use include `verified-slice` and `legacy-import` — so it
  is a stable record identifier, not a pointer at the heading. Five committed
  topics keep it unchanged.
- Historical mentions in `docs/product/changelog.md`, `docs/rfc/0001`, and
  other specs are frozen records of what was true when written and are not
  touched.
- The four example bullets at `:859-862` stay where they are; C4's first
  clause names them as instances of the generalisable route.

**Done when:** those assertions pass, and AC14's walk, the five-mutation
record, and the measured `work-loop/SKILL.md` body-line count are all in
`docs/specs/ride-along-admission-test/notes/verification-ledger.md`.

### T5: RFC-0090 records the tier replacement as an Approver-signed erratum

**Depends on:** T2

**Touches:** docs/rfc/0090-change-sizing-and-decomposition.md

**Tests:**
- Verification mode: goal-based check. `git diff "$(git merge-base origin/main
  HEAD)" -- docs/rfc/0090-change-sizing-and-decomposition.md` shows additions
  only below the `## Errata` heading. Verifies AC15.
- The entry is dated, names what replaced the three tiers and why, and ends
  `Approver: eugenelim`.

**Approach:**
- RFC-0055 §D2 makes the two-layer current-state table optional and
  threshold-gated; this is the section's second entry and it supersedes
  nothing, so it stays a dated bullet.

**Done when:** the merge-base diff shows no line changed above `## Errata`,
and the new entry states the three reasons the tiers go — Tier 3 contradicts
the carve-out's own "verifiability, not locality" headline, "visibly smaller"
is ambiguous between "smaller than the main change" and "net-negative lines",
and the tiers exclude a verifiable class that matches none of the three —
and records that clause (ii) admits a design call already resolved by
citation or by an owner's in-session answer.

### T6: The release records the change

**Depends on:** T4

**Touches:** packs/core/pack.toml, packs/core/.claude-plugin/plugin.json,
docs/product/changelog.md, packs/core/.apm/skills/work-loop/evals/evals.json

**Tests:**
- Verification mode: goal-based check. Both version files declare the same
  value, one patch above the highest `[core]` version in
  `docs/product/changelog.md` and higher than every `[core]` version there
  (AC16); the topmost release heading is `## [core][<that version>] —
  <ISO date>` with a `### Highlights` block (AC17).
- `python3 -c "import json; json.load(open('packs/core/.apm/skills/work-loop/evals/evals.json'))"`
  parses, and the two new cases carry the assertions AC18 and AC19 require.

**Approach:**
- Derive the version from the changelog at execution time, not from the merge
  base and not from a value chosen now. Five core patch bumps landed on
  2026-09-18 alone, so a peer bump can reach `main` after this branch's merge
  base; the changelog on the merged result is what has to stay collision-free,
  and re-deriving immediately before the merge is what keeps it so.
- The changelog entry and both eval cases cite no RFC, ADR, spec, or PR
  number: `packs/AGENTS.md` bans internal-governance citations in shipped pack
  content, and the changelog is read by adopters.

**Done when:** a disposable script, run from the repository root and not
committed, exits 0 having asserted all of: `pack.toml` and `plugin.json`
declare the same version V; V is greater than every `[core]` version in
`docs/product/changelog.md` before this change; V differs from the previous
highest `[core]` version only in its patch component, and by exactly one; the
topmost `## [<pack>][<version>]` heading in the file — of any pack, not only
`core` — is `## [core][V]`; and that heading ends with an ISO date matching
`\d{4}-\d{2}-\d{2}` and is followed by a `### Highlights` block before the
next `## ` heading. The first three assertions decide AC16 and the last two
decide AC17. No uniqueness assertion is included: AC16 already puts V above
every version the changelog held, so a second `## [core][V]` cannot arise
from a correct implementation, and asserting it would be stronger than any
criterion. AC18 and AC19 are read from `evals.json` rather than executed, as
the spec's Testing Strategy states, and the changelog's Highlights block
states the reader-visible change in plain words.

### T8: The review findings are repaired at every surface they reach

**Depends on:** none — T1–T6 are complete and frozen; this is the correction
task the amendment procedure requires instead of editing them.

**Touches:** packs/core/.apm/skills/work-loop/SKILL.md,
packs/core/.apm/agents/implementer.md,
packs/core/.apm/agents/adversarial-reviewer.md,
packs/core/.apm/skills/work-loop/references/supervisor-mode.md,
packs/core/.apm/hooks/pre-pr.py, tools/hooks/pre-pr.py, tools/hooks/README.md,
guides/core/explanation/core-pack.md,
packs/core/tests/pack/test_ride_along_admission_test.py,
tests/roster/test_capture_rename_guide.py

**Tests:** verification mode: TDD for every criterion below; the control
changes come first and must red before the prose and code they grade.
- AC25: each of AC1–AC3's assertions compares the extraction against the
  canonical constant already defined in the test module, not only across
  sites. Red first by rewording a clause identically at all four sites and
  confirming the current assertions pass — that demonstration goes in the
  ledger.
- AC26: AC4's count and AC5's host check iterate every occurrence, and a
  clause found in a non-carrying file fails.
- AC12 and AC5: C6 moves inside the fenced report template; the AC5 check
  exempts C6 from the fence clause and only from it.
- AC27: the roster guide assertion binds to the `Capture` step entry.
- AC24: the step-order check is per-job and covers every naming step.
- AC28: a sweep over `packs/`, `tools/` and `guides/` for the retired step
  name in every casing and separator, allowing only the `evals.json` case id
  and `docs/knowledge/` records.
- C1's clause (iv), C2's citation-independence and inert-in-content
  sentences, and the corrected DECIDE row land at all four sites; AC1–AC5 and
  AC9 stay green afterwards.

**Approach:**
- Clause (iv) is the structural replacement for what locality supplied by
  accident. Write it fail-closed: an undecidable file is in scope.
- Four live references survive, not three: `packs/core/.apm/hooks/pre-pr.py:13,115`,
  `tools/hooks/pre-pr.py:13,115`, `tools/hooks/README.md:66`, and
  `guides/core/explanation/core-pack.md:233` ("Why capture learnings"), which
  T4 missed because it corrected only step 10 at line 124. The original sweep
  used a case-sensitive pattern that could not match the capitalised
  hyphenated spelling, and a second pass scoped to one line missed a second
  hit in the same file; AC28's sweep is case-insensitive over all three
  separators and covers whole files, so neither variant of the miss recurs.

**Done when:** every criterion above passes; `python3 tools/lint-pack-test-boundary.py`,
`python3 tools/lint-ci-parity.py`, `python3 tools/lint-agents-md.py` and
`make lint-ruff lint-mypy` each exit 0 read unfiltered; `work-loop/SKILL.md`'s
body is at most 1,000 lines with the measured count in the ledger. The
installed-projection manual-QA walk is **not** required here: it reads the
projections T7 regenerates, so requiring it before T7 would make the graph
unschedulable. T7 owns it.

### T9: C2 names the artifact the direct-run branch writes to

**Depends on:** none — T1–T8 are complete and frozen; this is the correction
task the amendment procedure requires instead of editing them.

**Touches:** packs/core/tests/pack/test_ride_along_admission_test.py,
packs/core/.apm/skills/work-loop/SKILL.md,
packs/core/.apm/agents/implementer.md,
packs/core/.apm/agents/adversarial-reviewer.md,
packs/core/.apm/skills/work-loop/references/supervisor-mode.md

**Tests:** verification mode: TDD. C2 is pinned by equality at four sites, so
`test_c2_is_identical_across_the_four_sites` reds the moment the module's
canonical `C2` constant is updated, and greens only when all four sites carry
the new wording.
- Update the canonical `C2` constant first and record the observed failure.
  The red is **one** assertion, not four: the identity check compares the
  extracted value against the constant and stops at the first mismatch, so it
  names one site. `test_clauses_sit_in_their_hosts` stays green throughout —
  it reads C2's opening words, which this amendment does not change, so
  placement never moves. Claiming either a four-site red or two red tests
  would be describing a failure the control cannot produce.
- `packs/core/tests/pack/` and `tests/roster/test_capture_rename_guide.py`
  stay green afterwards.

**Approach:**
- The change is a near-swap: "the human gate's own record" becomes "wherever
  this run reports its result". The surrounding sentence, the reply-naming
  rule, and the fall-out sentence are unchanged.
- Generic rather than named, deliberately. Three contexts reach this branch
  and each has a different record: a full run's pull request, a direct-light
  run's handoff, and a briefed subagent's report to its supervisor. An
  earlier draft named the pull request and left the other two writing
  nowhere. The surface a run reports to is the one noun true in all three.
- The reply-nonce half of the same security Concern is **not** in scope: an
  answer still counts when the reply names the question, and the question is
  still text the agent wrote. That needs an attribution mechanism and a
  decision the owner has deferred to `work-intake`.

**Done when:** all four sites carry the amended C2 verbatim, the pack and
roster suites are green, `work-loop/SKILL.md`'s body is at most 1,000 lines
with the count recorded, and `python3 tools/lint-agents-md.py`,
`python3 tools/lint-pack-test-boundary.py`, `python3 tools/lint-ci-parity.py`
and `make lint-ruff lint-mypy` each exit 0 read unfiltered.

### T10: The contract shrinks to what can red, and three errors are corrected

**Depends on:** none

**Touches:** packs/core/.apm/agents/adversarial-reviewer.md,
packs/core/.apm/agents/implementer.md,
packs/core/.apm/skills/work-loop/SKILL.md,
packs/core/.apm/skills/work-loop/references/supervisor-mode.md,
docs/rfc/0090-change-sizing-and-decomposition.md,
packs/core/.apm/skills/work-loop/evals/evals.json,
packs/core/tests/pack/test_ride_along_admission_test.py,
tests/roster/test_capture_rename_guide.py,
.workspace-prune-protected.toml

**Tests:** modes are per work item, not per task.
- **TDD** for AC3, AC7, AC8 and AC12, matching the spec's Testing Strategy.
  - `test_pinned_clauses_match_the_spec` (AC3) — `stub: true`; the exact
    block is below, compiled and red-validated from disposable scratch, with
    no repository test file written during PLAN.
  - `test_retired_locality_vocabulary_is_absent` (AC7) — no new stub: the
    assertion exists in the shipped suite and this task changes its
    comparison. Red validation: wrap `visibly smaller` across a line break in
    a scratch copy of one of the four files and confirm the current raw
    substring check passes where the normalised one fails.
  - `test_c1_is_identical_across_the_four_sites` and
    `test_clauses_sit_in_their_hosts` (AC8) — no new stub; both exist. Red
    validation: apply each of AC8's six mutations in turn and record the
    assertion and the message it emits.
  - `test_retired_step_name_is_absent_from_shipped_content` (AC12) — no new
    stub; it exists. Red validation: place an unreadable byte sequence in a
    swept file and confirm the current control skips it where the repaired
    one fails.
- **Goal-based check** for the erratum (AC13) and the eval cases (AC15):
  `no stub (goal-based)`. Both are content at a named path decided by a
  command, with no callable seam to stub.
- **Goal-based check** for the prune entry: `no stub (goal-based)`.
  `tests/AGENTS.md` obliges a `.workspace-prune-protected.toml` entry when a
  roster test names a `docs/specs/<slug>` path as a literal, which AC3's new
  assertion does. A construction test re-derives that list, so the check is
  that it passes.
- **AC3** is new and needs a new binding. The pack test cannot read `docs/`
  under `lint-pack-test-boundary`, so the assertion comparing C1 and C2
  against this spec's § The shipped clauses blockquotes lives in
  `tests/roster/test_capture_rename_guide.py`, which may read both trees.
  Stub entry: `test_pinned_clauses_match_the_spec` (AC3), `stub: true`,
  compiled and red-validated from disposable scratch; repository test file
  not written during PLAN. Block:

  ```python
  # STUB: AC3
  SPEC = ROOT / "docs" / "specs" / "ride-along-admission-test" / "spec.md"

  def test_pinned_clauses_match_the_spec() -> None:
      """C1 and C2 in the pack module equal this spec's blockquotes."""
      import importlib.util
      spec_blocks = _shipped_clause_blockquotes(SPEC)   # C1, C2 by order
      module = _load_pack_module()                       # by unique name
      for label, text in (("C1", module.C1), ("C2", module.C2)):
          assert _flat(text) == _flat(spec_blocks[label]), (
              f"{label} in the pack test module diverges from spec.md "
              f"§ The shipped clauses"
          )
  # END STUB: AC3
  ```

  The three helpers are new and local to the roster module:
  `_shipped_clause_blockquotes(path)` parses § The shipped clauses into
  `{label: text}` by reading each `**C<n> — …**` heading and the blockquote
  that follows it; `_load_pack_module()` imports
  `packs/core/tests/pack/test_ride_along_admission_test.py` under a unique
  module name per `packs/AGENTS.md`; `_flat(text)` collapses whitespace runs
  the way both suites already do. Compile and red are validated from
  disposable scratch before the repository test file is written: red it by
  changing one word of C1 in `spec.md` alone and confirming this assertion is
  the only failure.
- **AC7** becomes case-insensitive over normalised text; red it by wrapping
  `visibly smaller` across a line break in a scratch copy.
- **AC12**'s sweep drops the `__pycache__` skip and fails rather than
  continues on an unreadable file, leaving exactly the two named exemptions.
- **AC8** gains two mutations (a C2 interior word, and an identical reword of
  C1 at all four sites) and requires the emitted message, not just the
  assertion name.
- **AC15**'s dispatch case gains the clause (iv) establishment its prompt
  currently omits.
- The assertions pinning C3–C7 stay exactly as they are. They are no longer
  criteria; they are the content pin those clauses keep.

**Approach:**
- Nothing blocks this task. T1–T6, T8 and T9 are complete and frozen; T7 is
  pending because its wave closed through `gates-clean` rather than a wave
  advance, so the cohort does not count it complete, and it re-runs after
  this task. That belongs here and not in `Depends on:`, which
  `loop-cohort schedule` parses as a comma-separated list of task IDs and
  ranges — prose naming other tasks there is read as real edges, which is how
  an earlier draft of this line produced a T10↔T7 cycle.
- C2 loses "of your report, or of the pull request when you are not reporting
  to a supervisor". That phrase told a reader the record was theirs to write,
  which contradicts `adversarial-reviewer.md`'s own output contract — it
  permits only severity sections or the clean sentinel, and C2 is hosted
  there as a rule the reviewer *applies*, not one it follows.
- The erratum says "three-clause"; C1 has carried four since clause (iv)
  landed. The entry is corrected in place rather than superseded by a second
  entry: it is unmerged, so it is still being authored, and RFC-0055's
  immutability applies to published corrections.
- `plan.md:471` — T4's pinned `Tests:` field — says "`## Capture learnings`
  contains C5" and is wrong. It cannot be repaired: the amendment procedure
  forbids editing a completed task section. It is recorded in the ledger as a
  frozen error, which is the only disposition available.

**Done when:** every criterion except AC16's installed-artifact half holds;
`packs/core/tests/pack/`, `tests/roster/`, `lint-pack-test-boundary`,
`lint-ci-parity`, `lint-agents-md` and `make lint-ruff lint-mypy` are each
clean read unfiltered; and the ledger carries AC16's mutation set, its two
goal-based command records, and the five-note `## Capture` walk. The three
installed-artifact discoveries are **not** required here — they read the
projection T7 regenerates, so requiring them before T7 would make the graph
unschedulable, as an earlier draft of T8 did. T7 owns them.

### T7: Projections match the changed sources

**Depends on:** T10

**Touches:** .claude/, .agents/, .codex/

**Tests:**
- Verification mode: goal-based check. `agentbundle catalogue self-host
  --check --root .` reports no drift after the write. CI runs the
  Windows-driven form of the same drift check at
  `build-check-windows.yml:106` (`--check --windows`).

**Approach:**
- `build-self` refuses a dirty tree, so T1–T6 are committed before this runs.
- Write first (`--write`), then re-run with `--check` for the evidence; the
  bare command without `--check` writes rather than reports, so it cannot be
  the verification step.

**Done when:** `agentbundle catalogue self-host --check --root .` exits clean,
`git status` shows no unstaged projection, and the manual-QA walk is recorded
in the verification ledger — three worked discoveries driven through the
**installed** `.claude/skills/work-loop/SKILL.md`, one resolved by citation,
one needing an owner answer at the human gate, and one in a
declared-unattended dispatch, each with the route it took.

## Rollout

Pure content change to a published pack. Delivery is the version bump in T6;
rollback is a revert of the PR. No infrastructure, no external system, no
deployment sequencing. Nothing here is irreversible.

## Risks

- **The body-line budget.** `work-loop/SKILL.md`'s body is 918 lines of the
  1,000 `CAT-S003` allows, leaving 82. The per-clause deltas, so the sum can
  be checked without recounting the file: C1 about +1 over the five tier
  lines it replaces, C2 about +19 (it replaces nothing), C4 about +9 over the
  three-line bullet it supersedes, C5 about +11, T3's table row +1, and the
  widened sync comment +1 — roughly +42, leaving about 40. C6 and C7 cost
  nothing here: they live in `implementer.md` and `supervisor-mode.md`, which
  `CAT-S003` does not measure. C2 is the largest
  single addition and folding it in is what makes this tight. If the total
  overruns, the remedy is to shorten C5's economics sentences, not to move an
  obligation into a reference file where no gate reads it.
- **A fifth carrying surface.** The grep that found `supervisor-mode.md`
  covered `packs/*/.apm/`; a surface outside that root that paraphrases the
  tiers would not have been found. T2's pathspec is narrower still — four
  named files — so it inherits that blind spot by construction rather than by
  accident.
- **The erratum outruns its convention.** RFC-0055 governs corrections
  *within* an RFC and puts whole-RFC supersession out of scope. Replacing the
  tiers and refining clause (ii) are substantive changes to one decision, not
  to the RFC; if review reads them as whole-RFC replacement, the remedy is a
  superseding RFC and T5 becomes a follow-on rather than growing in place.
- **The editable install resolves outside this worktree.** `agentbundle`
  imports from `/Users/eu.gene.lim/orca/agent-ready-repo`. Both checkouts are
  at `1eda7f279` with a clean `packages/agentbundle/`, so T7 runs the code CI
  runs; if the main checkout moves mid-loop, re-verify before trusting T7.

## Changelog

<!-- Approvals only. -->

- 2026-09-19: spec approved by eugenelim. Approved over an unresolved review
  residual, recorded here because the transition name does not carry it: the
  adversarial lane ran three spec-mode rounds (9, then 5, then 3 findings)
  and never returned `Clean`. Round 3's three repairs and the later
  `## Capture learnings` → `## Capture` rename were not re-reviewed. One
  round-3 concern is accepted rather than fixed — clause (ii)'s recognition
  step does not reach a behaviour-neutral placement, ordering, or
  decomposition choice — and the spec records that limit beside C2.
- 2026-09-19: plan approved by eugenelim.
- 2026-09-19: spec re-approved by eugenelim after the controlled amendment.
  Authority: the owner decision recorded in
  `notes/verification-ledger.md`. The amendment splits AC23's guide check into
  `tests/roster/`, because `tools/lint-pack-test-boundary.py` forbids a pack
  test reading above its own pack; it adds AC24 for the roster step's
  placement, which no existing gate enforces; and it adds T1b. Amendment
  review reached `Clean — ready to commit.` in three rounds (4, then 2, then
  0 findings).
- 2026-09-19: plan re-approved by eugenelim after the controlled amendment.
- 2026-09-19: spec and plan re-approved by eugenelim after the second
  controlled amendment, which closes four Blockers introduced by removing
  locality and six from the implementation review. Amendment review reached
  `Clean — ready to commit.` in two rounds.
- 2026-09-19: spec and plan re-approved by eugenelim after the third
  controlled amendment, which names the surface C2 fallback writes to.
- 2026-09-19: spec and plan re-approved by eugenelim after the fourth
  controlled amendment, which cut the contract from 28 criteria to 16 and
  demoted C3-C7 to working material. Review reached clean in four rounds.
