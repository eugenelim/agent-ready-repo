# Spec: sequential implementer dispatch

- **Status:** Shipped <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** ADR-0061
- **Brief:** docs/product/briefs/universal-implementer-dispatch.md
- **Discovery:** none
- **Contract:** none
- **Shape:** integration

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

An adopter running `work-loop` on `claude-code` or `codex` gets one
implementation envelope for every spec-backed plan task. Each
`CODE-IMPLEMENTATION` plan task goes to the `implementer` agent through a
bounded brief, one task at a time, in the order `loop-cohort schedule` emits,
whenever that agent is installed. The agent works in whichever execution root
the controller supplies — the primary working tree or an already-created
worktree — and the primary session keeps state transitions, scheduling, gates,
review dispatch, retry decisions, and closeout. Craft the agent needs reaches it
inlined in its brief, so a dispatched task carries the same guidance an inline
one did.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| Interface compatibility | Applicable — the agent contract gains a root, a commit owner, and an inlining clause | `packs/core/.apm/agents/implementer.md` | core pack | AC2-AC6 green; both adapters project the changed contract | Contract states two roots, one commit owner each, and inlined craft |
| Current architecture | Applicable — four surfaces state the contradicted rule | `packs/core/.apm/skills/work-loop/references/supervisor-mode.md`, `packs/core/.apm/skills/work-loop/evals/evals.json`, `packs/core/seeds/docs/CONVENTIONS.md` (the source; `docs/CONVENTIONS.md` is its self-host projection), `packs/core/.apm/agents/implementer.md` | work-loop skill and core pack | AC8 and AC9 green over the enumerated set | Every member checked by both halves of the predicate |
| User promise | Applicable — dispatch changes adopter-visible EXECUTE behaviour | `guides/core/how-to/plan-and-execute-non-trivial-work.md` | guides/core | AC10 green | Guide describes dispatch and retains the fan-out-disabled statement |
| Release history | Applicable — core ships a behaviour change | `docs/product/changelog.md` and `packs/core/pack.toml` | core pack | A `## [core][2.24.0]` section sitting directly beneath `[Unreleased]`, with `pack.toml` bumped to match | Entry topmost, version bumped, and `web/src/lib/now-highlights.generated.json` regenerated. Packs carry no `CHANGELOG.md`; only published packages do. |
| Decision rationale | Not applicable | — | — | — | ADR-0061 governs; this slice takes no new architectural decision |

## Boundaries

### Always do

- Supply the execution root explicitly in every dispatch brief, resolved by the
  controller before dispatch.
- Edit `packs/core/seeds/docs/CONVENTIONS.md` and let `make build-self`
  regenerate `docs/CONVENTIONS.md`. The root file is a projection; editing it
  directly is reverted by the gate chain.
- Anchor every rail on section identity, never a line range: this change edits
  text above the sections it names and moves them.
- Run the anchor-test sweep at `work-loop/SKILL.md` § 8a before editing, using
  patterns that catch ordered `.index()` and prose-substring pins as well as
  hashes and counts.

### Ask first

- Moving any statement out of `work-loop/SKILL.md` that is a state transition, a
  gate, a review-dispatch rule, or a closeout rule.
- Changing what `loop-cohort schedule` emits, or the meaning of a plan's
  `Depends on:` edges.
- Extracting task-implementation procedure from `work-loop/SKILL.md`. That is a
  separate slice; see Follow-ons.

### Never do

- Re-enable `dispatch-decision`, `worktree`, or `auto-parallel`, or add
  `pending_transition`. ADR-0061 is Frozen and defers all of it.
- Let the `implementer` transition loop state, run final gates, dispatch a
  reviewer, merge, or declare the loop complete.
- Let the `implementer` create a branch, mutate the index, or commit when the
  execution root is the primary working tree.
- Claim support for any host other than `claude-code` and `codex`.
- Add a new top-level directory, a new dependency, or a new module boundary.
- Change what the direct-light path does. It stays inline and this slice does
  not touch its statements in `work-loop/SKILL.md`.

## Testing Strategy

Every outcome is a construction claim about what a shipped artifact declares or
where it projects, so the mode is **goal-based check** throughout: a test reads
the artifact and asserts a statement is present, absent, or projected. No
criterion asserts runtime honouring — there is no seam to observe it at, and
such a control could not fail. No criterion uses TDD: every subject is a
contract file, and a prose edit has no red-green cycle.

- **AC1-AC7, AC9 — pack tests** under `packs/core/tests/skills/work-loop/`,
  which `Makefile` line 545 collects by directory. Each reads shipped markdown
  or JSON inside `packs/core`.
- **AC8 — a roster test** under `tests/roster/`, because its enumerated set
  includes `packs/core/seeds/docs/CONVENTIONS.md` alongside pack-internal files
  and pack tests stay anchored inside their owning pack. `Makefile` line 530
  runs `pytest tests/ -q`, which collects that directory.
- **AC10 — a build-pipeline test** under
  `packages/agentbundle/tests/build_pipeline/`, exercised as an **integration**
  test: it projects the real `packs/core` through both adapters and asserts the
  resulting layout. It only proves out across the build boundary, so a unit test
  on either adapter alone would not establish it. The expected paths are
  declared independently of the adapter code under test.

## Acceptance Criteria

Every criterion names a literal string in a named file. A paraphrased criterion
over prose cannot fail, because the implementer supplies the comparison value.

- [x] **AC1:** `work-loop/SKILL.md` § EXECUTE carries a dispatch declaration
      containing all four literals: `implementer`, `loop-cohort schedule`,
      `once per plan task`, and `one implementer at a time`.
- [x] **AC2:** the `description:` frontmatter of `implementer.md` contains
      neither `supervisor mode` nor `multiple tasks declaring`. Both clauses
      restrict the agent today; removing one and leaving the other ships a
      contract that still scopes it away from the normal path.
- [x] **AC3:** `implementer.md` names `the primary working tree` and
      `an already-created worktree` as the execution roots the controller
      supplies, and names no third.
- [x] **AC4:** `implementer.md` names one commit owner per root: the controller
      for the primary working tree, the agent inside an already-created
      worktree.
- [x] **AC5:** `implementer.md`'s inlining clause applies to every
      predicate-fired craft source, not only infra-flavored work. The clause is
      scoped to one source today, so a criterion that only checks the clause
      exists is already satisfied.
- [x] **AC6:** `implementer.md` states that a dispatch brief missing the task
      body, the execution root, the spec path, the plan path, or the
      verification mode is refused before the first implementation write.
- [x] **AC7:** `work-loop/SKILL.md` states that `frontend-engineering` craft is
      inlined into the dispatch brief, and what happens when that pack is
      absent. This is the craft that can actually be absent: every row of
      § "Conditional-reference routing" points at work-loop's own `references/`,
      which ship with the skill.
- [x] **AC8:** none of the three asserting members still carries its recorded
      contradiction: `supervisor-mode.md` and
      `packs/core/seeds/docs/CONVENTIONS.md` no longer contain
      `single-agent, on every adapter`, that same seed no longer describes
      Profile A as a `single-agent work-loop`, and `implementer.md` no longer
      states that all edits happen inside `.worktrees/<task-id>/`. All are red
      today; the plan records the literal per member.
- [x] **AC9:** the two members whose defect is omission rather than assertion
      each carry the missing statement — the `phase1-disabled-parallel-commands`
      record in `work-loop/evals/evals.json` names `implementer`, and
      `supervisor-mode.md`'s single-agent fallback is retained with its
      no-installed-subagent condition intact. Retention is the recorded
      disposition, not one permitted option among several.
- [x] **AC10:** `guides/core/how-to/plan-and-execute-non-trivial-work.md`
      contains both its existing literal `Parallel fan-out (\`dispatch-decision\`,
      \`worktree\`, \`auto-parallel\`) is disabled in Phase 1` and a new sentence
      naming `implementer` dispatch.
- [x] **AC11:** projecting `packs/core` lands `.claude/agents/implementer.md`
      under the `claude-code` adapter and `.codex/agents/implementer.toml` under
      the `codex` adapter. The codex artifact is a TOML transform of the source
      markdown, not a copy.

## Follow-ons

- Repository maintainers: [`docs/product/briefs/universal-implementer-dispatch.md`](../../product/briefs/universal-implementer-dispatch.md)
  § "Proposed slices" — U3, extracting task-implementation procedure from
  `work-loop/SKILL.md`. Split out of this slice on 2026-09-03 after six of nine
  candidate statements proved immovable for independent reasons: two are
  load-bearing one-liners their own destination files require `SKILL.md` to
  keep, one is a gate scoped to both the light and full paths, one is pinned by
  an ordered roster assertion, one routes to a real documented artifact, and one
  is converted in place rather than removed.
- Repository maintainers: same brief § "Proposed slices" — U2, direct-light
  policy-verdict dispatch, gated on three slices across two other briefs.
- Repository maintainers: same brief § "Success metrics" — emitting a signal
  that distinguishes `inline` from `dispatched`. Deferred because the eval
  runner that would read it is an explicit non-goal of this brief, not because
  no seam exists: `loop-engine.py` already writes a durable `events.jsonl` that
  a shipped test reads.
- Repository maintainers: same brief § "Constraints" — collapsing the
  bundled-fixes carve-out's three copies into one home.

## Assumptions

- Technical: a sequential-execution procedure already has an owner that
  contradicts this outcome — `supervisor-mode.md` line 11 ("topological order,
  single-agent"), its Phase 1 procedure section, and its single-agent fallback
  section (source: repository read)
- Technical: no agent in the core pack holds the Skill tool, and the same
  reference projects to a different path per adapter
  (`.claude/skills/work-loop/references/` versus
  `.agents/skills/work-loop/references/`), so no single path in the agent
  contract is correct on both hosts. The agent can read a path it is given —
  `implementer.md` line 30 already says so — but it cannot reliably construct
  one, and skill invocation is model-invoked and adapter-variable, so depth must
  not depend on self-discovery (source: probe measuring both projections;
  `security-checklists/SKILL.md` line 47)
- Technical: `docs/CONVENTIONS.md` is a self-host projection of
  `packs/core/seeds/docs/CONVENTIONS.md`; the seed is the governed source
  (source: `Makefile` lines 68-80 running `catalogue self-host --write`; the
  repository's recorded rule at `docs/specs/m3-backlog-absorption/plan.md` line
  384)
- Technical: `Makefile` line 530 runs `pytest tests/ -q`, which collects all 81
  files under `tests/roster/`; by-name wiring in `build-check.yml` is a second
  runner, not the only one (source: repository read)
- Technical: three of the four `CODE-IMPLEMENTATION` re-entry edges carry repair
  rather than a plan task, so they do not dispatch; `wave-passed` carries the
  next wave and does (source: `loop-engine.py` lines 548, 550, 552, 554)
- Technical: `frontend-engineering` craft currently reaches EXECUTE as ambient
  governance ("its craft rules govern", `work-loop/SKILL.md` line 413), which
  does not survive the move into a subagent (source: repository read)
- Technical: packs carry no `CHANGELOG.md`; core release history is
  `docs/product/changelog.md` as `## [core][<version>] — YYYY-MM-DD` sitting
  directly beneath `[Unreleased]`, and only published packages keep a sibling
  `CHANGELOG.md` (source: `docs/CONVENTIONS.md` lines 700-711)
- Technical: `origin/main` already ships core `2.23.0` and its changelog section
  exists, so this change takes `2.24.0` and bumps `packs/core/pack.toml` to
  match (source: `git show origin/main:packs/core/pack.toml`)
- Technical: `web/src/lib/now-highlights.generated.json` is a generated
  projection of the changelog and must be regenerated by the build; the `/now/`
  surface forbids development vocabulary, so the entry avoids words like
  `unreleased`, `backlog`, `queue`, and `in progress` (source: repository read)
- Technical: `packs/core/tests/skills/work-loop/test_reference_routing.py` pins
  six prose substrings inside `supervisor-mode.md`, three of them inside the
  Phase 1 section this change rewrites. An earlier sweep missed it because it
  matched hashing and counting patterns but not plain substring assertions
  (source: repository read)
- Process: the AC ceiling for this slice is 11, raised from the brief's 8 by
  owner decision rather than splitting the dispatch work; this spec ships 11
  (source: user confirmation 2026-09-03)
- Process: extraction is a separate slice, and the guide leads with the worktree
  path (source: user confirmation 2026-09-03)
