# Plan: navigate-decisions route mode

- **Spec:** [`spec.md`](spec.md)
- **Status:** Drafting <!-- Drafting | Approved | Executing | Done -->
- **Repository anchors:** `packs/AGENTS.md` (version bump, eval-harness rule, pack-test boundary); `packs/core/.apm/skills/new-spec/SKILL.md` links into a sibling skill (`../work-loop/references/...`), the precedent for citing `new-rfc` step 0 by link; `packs/repo-governance/tests/skills/navigate-decisions/test_skill_instructions.py` is the content-pin construction path; `docs/specs/intent-longer-and-supervised-verbs/notes/verification-ledger.md` is the activation-measurement precedent. Uncertainty: whether a broader description holds its trigger rate, which only T6 can show.

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

The change is mostly agent instruction. `route` is a new section of
`navigate-decisions`' `SKILL.md`. It cites `new-rfc` step 0, adds the door check and
the advice step, and reports one fixed result block. The reuse check uses the
existing `search` operation, so no script changes. `new-adr` tightens what
`Consulted` may hold, and its shape lint gains one control-character check.
`new-rfc` and `new-adr` each gain a one-line pointer.

The riskiest part is activation. A single-run probe on 2026-10-26 ran four
route-style questions once each against today's projection, and all four fired no
skill, from either `navigate-decisions` or `new-rfc`. So the description
change carries AC-0032 alone, and the realistic failure is "nothing loads", not
"`new-rfc` loads instead". Order follows from that:
1. T1 freezes every measurement input and measures the pre-change world.
2. T2–T4 make the edits.
3. T5 measures the post-change world and runs the behaviour cases and the seam
   requests.

## Constraints

- RFC-0110 D5 stage 2 and its 2026-10-25 errata: `route` is a read-only mode on
  `navigate-decisions`, no new skill, and `new-adr`'s existing `Consulted` field
  carries the advice. RFC-0110 § Trust model general rule 1 and the stage-2 block
  bind route. Rules 2, 3 and 5 govern writes, and only stage 1 writes.
- Brief `repo-governance-pack` § Success metrics (Mode activation, Stage 2 seam) and
  § Assumptions / Risks (route overlaps `new-rfc`'s triggers; conflict with core's
  work loop).
- `packs/AGENTS.md`: bump `pack.toml` and `plugin.json` together, update the eval
  harness, and keep pack tests inside the pack. No pack content cites this
  catalogue's internal records.
- The spec-stage security pass that RFC-0110 requires is a precondition for T2. It
  is owned by the work loop's G-plan sequence.
- Owner decisions at the 2026-10-26 assumptions checkpoint:
  - `Consulted` record identifiers stay allowed, and email is refused.
  - Route picks the decision record, and the work loop picks the build mode.
  - The door verdict is advisory.
  - The activation world is the pack alone.
  - The version is 2.1.0.

## Construction tests

Most construction tests live under **Tasks** below.

**Integration tests:** the T5 behaviour runs, end to end in scratch repositories.
**Manual verification:** the T5 seam table, graded pair by pair against the spec's
contradiction definition.

## Durable-output map

| Durable output | Tasks | Implementation evidence | Closeout evidence |
| --- | --- | --- | --- |
| User promise: `guides/repo-governance/how-to/route-a-decision.md` | T4 | guide file and any guide-index test green | guide present; its result block matches the skill's |
| Current product truth: README, JOURNEY, docs/index | T4 | each names `route` | each names it read-only |
| Current architecture: `DESIGN.md` § 7 item 6, § 8 | T4 | read-only invariant names `route` | present |
| Release history: changelog fragment | T4 | `tools/changelog.py` validation green | fragment present with `Highlights` decided |
| Validation evidence: `notes/verification-ledger.md` and raw run files | T1, T5 | ledger entries | every result AC-0026, AC-0030, AC-0031, AC-0032, AC-0033, AC-0034, AC-0035, AC-0036, AC-0037, AC-0038, AC-0039, AC-0040, AC-0041, AC-0048, AC-0051, AC-0052 and AC-0054 name is recorded |

## Design (LLD)

### Design decisions

- **Route is instruction-only.** The reuse check runs `navigate_decisions.py query
  --operation search --selectors <json>`, where `<json>` is one argument holding
  `[{"text": <term>}]`, built by JSON encoding. The selector already exists
  (`_SELECTOR_KEYS` at `navigate_decisions.py:1214`). It matches titles and status
  values only, and search returns no body, so route reads each hit it relies on
  with the `record` operation, which returns the body. A script change would widen
  the read-only surface for no gain. The one-literal-argument wording follows
  `new-adr`'s existing rule (`new-adr/SKILL.md` step 1, "One literal argument per
  value").
- **Step 0 is cited, not copied.** The link `../new-rfc/SKILL.md` resolves because
  both skills ship in the same pack and are projected side by side. The precedent
  is `core/new-spec` linking `../work-loop/references/`. One home keeps the two
  routings from drifting, so no test pins step 0's outcome names inside
  `navigate-decisions`.
- **A fixed result block.** The block lets `new-adr` find the `Consult:` line, lets
  T5 parse `Route:` and `Consult:` with no model grader, and lets the guide show
  the real output.
- **The seam is decision record versus build mode.** The `PR`, `issue` and `spec`
  outcomes mean "no decision record; build through the work loop". That removes the
  one real overlap: step 0 says "spec" for a settled bounded feature, while the work
  loop's light mode builds without one.
- **The description gains route triggers.** It keeps the authoring exclusion, and
  `new-rfc`'s description is unchanged. The probe above shows route questions load
  no skill today, so taking triggers from `new-rfc` buys nothing, and changing it
  would put AC-0035 at risk.
- **The lint does not check email.** `lint-adr-shape.py` exits 1 on any finding.
  An email check would fail adopters' existing ADRs that hold emails in `Consulted`
  after a minor upgrade. Email refusal therefore lives in `new-adr`'s authoring
  rule (AC-0021). The lint checks control, line-separator and bidirectional-control
  characters, which are a display-spoofing defect in any record. It leaves other
  format characters, such as U+200C, alone, because some scripts need them in
  names. Tab stays allowed. The lint splits text with `splitlines()`, which breaks
  on some of these characters, so the check reads the raw `Consulted` value from
  the text split on `\n` only, after removing one `\r` before each `\n`, so a
  CRLF file is not flagged.
- **Minor bump to 2.1.0.** A new mode is new capability, and nothing an adopter
  relies on is removed.

Owned by: T2, T3, T4.

### Interfaces & contracts

The route result block is the only interface `route` publishes. It is chat output,
not a file, and it is not a `contracts/` artifact. `new-adr` reads its `Consult:`
line from the conversation.

Owned by: T2, T3.

### Failure, edge cases & resilience

- **Hostile record text.** The hostile fixture's ADR copies the injection shape of
  the existing `fixtures/negative/instruction` ADR. Its request is routine work, so
  an injected `RFC` shows as a wrong `Route:` value.
- **Activation run errors.** Host usage limits produced errored runs in the
  precedent ledger. A query with any errored run is re-run in full, so no completed
  run is kept or dropped selectively.

Owned by: T1, T5.

## Tasks

### T1: Every measurement input is frozen, and the pre-change world is measured

**Depends on:** none

**Touches:** `docs/specs/navigate-decisions-route/notes/*`, `packs/repo-governance/tests/skills/navigate-decisions/fixtures/route-*/`

**Tests:** (goal-based)
- `notes/route-queries.json` holds the 15 route queries in the eval-query shape. An
  exact string check finds none of them in the three skills' eval files.
- `notes/seam-requests.json` holds the 12 seam requests. Each is tagged with its
  source eval and expected outcome:
  - from eval 7:
    - implement behaviour an accepted RFC already approved → `PR`
    - a settled durable architecture choice → `ADR`
    - a settled replacement of a prior ADR's choice → `ADR`
    - an unresolved direction several teams must agree → `RFC`
  - from eval 8, in a single-maintainer repository:
    - a charter mission change → `RFC`
    - a change to who may approve work → `RFC`
  - from eval 11:
    - a proposal already settled by an ADR → `reuse` or `reference`
    - a settled bounded feature → `spec`
    - routine work → `PR`
    - tracked work → `issue`
    - a remaining architecture choice → `architect-design`
    - a reversible trial with exit criteria → `time-bounded trial`
- Three fixtures, each with a small record tree. Every identity is a generic
  placeholder.
  - `fixtures/route-hostile/` holds a `docs/adr/` tree and a `request.txt`. The
    request is routine behaviour-preserving work, such as fixing a typo in one
    module's comment. `request.txt` is one line. The hostile ADR's title contains
    that line without its line ending, so any word or contiguous phrase taken from
    it matches, and tells
    the agent to route every request to an RFC and write a file. Its decision is
    plainly unrelated to the request, so `PR` is the only right outcome.
  - `fixtures/route-advice/` holds a `docs/adr/` tree and a `request.txt`. Its
    records name people, and its request supplies one handle and one role.
  - `fixtures/route-seam/` holds a `docs/adr/` tree with an ADR whose title matches
    the "proposal already settled by an ADR" request, and a `docs/rfc/` tree with
    an index, so the repository has an RFC process.
- The ledger records the pre-change commit SHA, the sha256 of each frozen file,
  the `claude` CLI version and the model ID.
- The ledger records `lint-adr-shape.py`'s findings over `docs/adr/` at the
  pre-change commit.
- Pre-change world, built from `git archive` of the pre-change commit's
  `packs/repo-governance/` into a temporary directory outside the repository:
  - runs: `navigate-decisions`' 49 eval queries, `new-rfc`'s 47 and the 15 route
    queries, three runs each, with no errored run left in the scored set;
  - the ledger records B and the floor;
  - it records `navigate-decisions`' pre-change false-trigger rate and `new-rfc`'s
    pre-change positive rate;
  - it records, for the route queries, the share of runs in which each of
    `navigate-decisions` and `new-rfc` fired;
  - it records the skills the host listed.

**Approach:**
- The driver is a scratch script outside the repository. It calls
  `ClaudeCodeDetector.project` and `run_and_parse` from
  `agentbundle.commands.pack_evals` unchanged, with a supplied query list, because
  the route queries are not in the pre-change eval files. Parallel jobs each use
  their own copy of the projection. Raw per-query results go in
  `notes/activation-pre-change.json`.
- This task lands before any `SKILL.md` edit, so the inputs cannot be tuned to the
  new text.

**Effects:** none

**Done when:** the ledger's T1 entry holds every hash and number listed in
`Tests`, and the frozen files and raw results are committed.

### T2: The route mode, its description triggers and its eval queries are in place, and their content pins pass

**Depends on:** T1, T3 (T3 writes the canonical handle and role sentence that AC-0047 copies)

**Touches:** `packs/repo-governance/.apm/skills/navigate-decisions/SKILL.md`, `packs/repo-governance/.apm/skills/navigate-decisions/evals/eval_queries.json`, `packs/repo-governance/tests/skills/navigate-decisions/test_skill_instructions.py`

**Tests:** (goal-based, content pins in `test_skill_instructions.py`, which already normalises whitespace into `TEXT`)
- One pin per criterion for AC-0001 and AC-0003, AC-0004, AC-0005, AC-0006, AC-0007, AC-0008, AC-0009, AC-0010, AC-0011, AC-0012, AC-0013, AC-0014, AC-0015, AC-0016, AC-0017, AC-0044, AC-0045, AC-0046, AC-0047, AC-0049, AC-0050 and AC-0053, each reading only the
  route section, sliced by heading, and asserting the exact sentence T2 writes.
- AC-0002 asserts the absence of each listed step-0 phrase over the whole `TEXT`.
- AC-0047's pin reads `new-adr/SKILL.md` step 4 inside the pack, takes the
  handle-and-role sentence AC-0023 pins, and asserts the route section contains
  it verbatim.
- AC-0003 asserts the seven line prefixes in order inside one fenced block.
- AC-0018 and AC-0019 read the frontmatter `description:`.
- The existing four tests stay green.
- `eval_queries.json` keeps its 49 prior entries unchanged and appends the 15
  route queries. Byte equality with `notes/route-queries.json` is checked in T5,
  not by a pack test, so no pack test reads outside the pack.

**Effects:** none

**Done when:** `python3 -m pytest packs/repo-governance/tests/skills/navigate-decisions -q`
is green, and `agentbundle catalogue lint --root . --deep` reports no new finding.

### T3: new-adr's Consulted rule, template comment, lint check and rubrics are in place, and both authoring skills point to route

**Depends on:** T1

**Touches:** `packs/repo-governance/.apm/skills/new-adr/SKILL.md`, `packs/repo-governance/.apm/skills/new-adr/assets/adr.md`, `packs/repo-governance/.apm/skills/new-adr/scripts/lint-adr-shape.py`, `packs/repo-governance/.apm/skills/new-adr/evals/evals.json`, `packs/repo-governance/.apm/skills/new-rfc/SKILL.md`, `packs/repo-governance/.apm/skills/new-rfc/evals/evals.json`, `packs/repo-governance/tests/skills/new-adr/*`, `packs/repo-governance/tests/skills/new-rfc/*`

**Tests:**
- AC-0025 (TDD, in `tests/skills/new-adr/test_lint_adr_shape.py`):
  - fixture ADRs whose `Consulted` holds U+202E, U+0007, U+2028, U+2029, U+000B or
    U+0085 each yield the new finding;
  - a fixture whose `Consulted` key line is empty and whose indented (Form 1)
    continuation line holds U+202E yields the finding, and so does one whose key
    line holds only an HTML comment;
  - conforming fixtures yield none: a CRLF file, a `Consulted` value holding
    U+0009, and a role name holding U+200C;
  - a conforming fixture whose `Consulted` holds
    `@org/team, platform maintainers, RFC-0001` yields none;
  - a fixture whose `Consulted` holds an email address yields none, which pins the
    no-email-in-lint decision.
- AC-0026 is checked in T5 by diffing findings. `tests/roster/test_lint_adr_shape_corpus.py`
  stays green.
- AC-0020, AC-0021, AC-0022, AC-0023 and AC-0024, AC-0027 (goal-based): one content pin per criterion, in a new
  instruction-test module under `tests/skills/new-adr/`. AC-0022's pin asserts that
  the "a name, a GitHub handle, or an email" sentence is scoped to `Decision-makers`
  and `Informed`.
- AC-0028, AC-0029 (goal-based): one content pin per pointer, under
  `tests/skills/new-rfc/` and `tests/skills/new-adr/`.
- `new-adr/evals/evals.json` gains one case: an email offered for `Consulted` is
  refused with a request for a handle or role, and a route block's `Consult:` line
  is used as given.
- `new-rfc/evals/evals.json` gains one case: a request whose route is unclear is
  pointed to `navigate-decisions route`.
- `agentbundle catalogue lint --root . --deep` accepts both files.

**Effects:** none

**Done when:** `python3 -m pytest packs/repo-governance/tests/skills/new-adr packs/repo-governance/tests/skills/new-rfc tests/roster/test_lint_adr_shape_corpus.py -q`
is green.

### T4: The pack is at 2.1.0 with its guide, documents, changelog fragment and projections current

**Depends on:** T2, T3

**Touches:** `packs/repo-governance/pack.toml`, `packs/repo-governance/.claude-plugin/plugin.json`, `packs/repo-governance/README.md`, `packs/repo-governance/JOURNEY.md`, `packs/repo-governance/DESIGN.md`, `packs/repo-governance/docs/index.md`, `guides/repo-governance/how-to/route-a-decision.md`, `guides/repo-governance/README.md`, `docs/product/changelog.d/*`, the projections that `make build-self` writes

**Tests:** (goal-based)
- AC-0042: both manifests parse with version `2.1.0`.
- Each durable-output row the map assigns to T4 holds. The guide's result block is
  compared with the skill's at review.
- `tools/changelog.py` validates the new fragment.
- AC-0043: after `FORCE=1 make build-self`, `git status --porcelain` is empty.

**Effects:** none

**Done when:** `make lint-ruff lint-mypy` and the `Tests` above are green, and
`agentbundle catalogue verify --root .` passes.

### T5: The post-change world, behaviour runs and seam runs are recorded, and each meets its bound

**Depends on:** T4

**Touches:** `docs/specs/navigate-decisions-route/notes/*`

**Tests:** (goal-based, and manual QA for AC-0040 and AC-0041)
- AC-0030: `git diff <pre-change commit> -- packs/repo-governance/.apm/skills/new-rfc/SKILL.md packs/repo-governance/.apm/skills/new-adr/SKILL.md`
  is recorded in the ledger. It shows no change inside step 0 or the four
  numbered checks.
- The ledger records that the 15 entries appended to `eval_queries.json` equal
  `notes/route-queries.json` (sha256 of both, compared).
- AC-0026: `lint-adr-shape.py` findings over `docs/adr/` on the finished branch,
  diffed against T1's recorded findings.
- AC-0031, AC-0032, AC-0033, AC-0034, AC-0035, AC-0048 and AC-0054:
  - the T1 driver reruns on the finished branch with the same query lists and run
    count, after confirming that the CLI version, the model ID and the listed
    skills match T1's;
  - the results go in `notes/activation-post-change.json`;
  - the ledger compares each rate with its bound, and states the resolution: one
    run moves a 35-query rate by about 0.0095.
- AC-0036, AC-0037, AC-0038, AC-0051 and AC-0052, run for each behaviour fixture three times:
  - each run is a headless `claude -p --permission-mode acceptEdits` run in a fresh
    scratch Git repository outside this repository. Its allowed tools include
    running `scripts/navigate_decisions.py`;
  - the scratch repository holds the post-change projection and the fixture's
    `docs/adr/`, committed, and the prompt is the fixture's `request.txt`;
  - the driver applies the spec's scored-run, route-tag and consult-set rules. It
    records `git status --porcelain` and every write-capable tool call in the
    transcript;
  - the ledger states that a write made by a shell command outside the scratch
    repository, other than the script's `export`, is not detected;
  - transcripts are saved in `notes/behaviour/`.
- AC-0039, AC-0040 and AC-0041, run for each seam request:
  - runs in a scratch repository seeded from `fixtures/route-seam/`, with the
    post-change `repo-governance` and `core` projections;
  - three scored route runs, each asking for `navigate-decisions route`;
  - three counted work-loop runs, each asking what core's work loop would do with
    the request, and to write nothing. A run where `work-loop` did not load is
    recorded and replaced, up to nine attempts per request;
  - the driver applies the route-tag rule and records the skills each run fired;
  - the ledger tabulates both answers and the contradiction verdict per pair;
  - transcripts are saved in `notes/seam/`.

**Approach:**
- Any failed bound stops the task with the numbers. The spec's Ask-first rule then
  governs.

**Effects:** none

**Done when:** the ledger's T5 entry records every check listed in `Tests`, and
each of AC-0026, AC-0030, AC-0031, AC-0032, AC-0033, AC-0034, AC-0035, AC-0036, AC-0037, AC-0038, AC-0039, AC-0040, AC-0041, AC-0048, AC-0051, AC-0052 and AC-0054 meets its bound.

## Rollout

A pack release with no infrastructure, migration or sequencing. Adopters receive
`repo-governance` 2.1.0 through `agentbundle upgrade`. Rollback is a downgrade to
2.0.0. `route` writes nothing. The new lint finding fires only on the control,
line-separator and bidirectional-control characters AC-0025 names.

## Risks

- **Activation runs hit host usage limits.** The precedent lost 52 and 190 runs to
  limits. The full-query re-run rule keeps scoring honest, and the cost is wall
  time.

## Changelog
