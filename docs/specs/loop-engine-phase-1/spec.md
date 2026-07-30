# Spec: loop-engine-phase-1

**Status:** Shipped
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** `packs/core/DESIGN.md` (§3, §4, §13), ADR-0014, RFC-0025
- **Brief:** none (intent prompt provided; converted to spec directly)
- **Contract:** none
- **Shape:** two new scripts + skill prose reduction + architecture doc

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

**Problem:** The work-loop skill embeds its full phase-transition choreography —
which loop-cohort verbs to call, in what order, at what events — as prose inside
the SKILL.md. This prose is unenforced: an agent can skip transitions, double-fire
events, or omit loop-cohort side effects with no mechanical consequence. It also
conflates mechanical procedure (fire this verb on this event) with LLM judgment
(select reviewers, route DECIDE, apply risk triggers) — making the skill harder
to read and giving no persistent record of current phase for session resumption.

**User:** A full-mode work-loop agent implementing a multi-task spec, needing
deterministic phase sequencing, reliable loop-cohort coordination, and a
persistent phase record for cross-session resumption.

**Success:** (1) `loop-engine.py` enforces the phase FSM and calls loop-cohort as
guard/side-effect so correct transitions cannot skip a phase; (2) SKILL.md is
meaningfully shorter with all loop-cohort choreography prose removed, replaced by
a mode-selection table and a human-gate-aware checkpoint table; (3)
`docs/architecture/loop-infrastructure.md` gives future maintainers the definitive
boundary between the two scripts and passes a design-reviewer gate before the plan
is finalised.

## Deliverables

Four co-dependent artifacts that must ship in one PR:

1. **`loop-engine.py`** — phase FSM validator and loop-cohort coordinator.
   Lives at `packs/core/.apm/skills/work-loop/scripts/loop-engine.py` alongside
   `loop-cohort.py`. Pure Python stdlib only.
2. **`check-spec-status.py`** — spec-status gate script. Verifies `**Status:**
   Shipped` in the current working tree for a given spec directory. Lives at
   `packs/core/.apm/skills/work-loop/scripts/check-spec-status.py`. Pure Python
   stdlib only.
3. **SKILL.md reduction** — remove loop-cohort choreography prose; add terse 3-sentence
   pointer to `references/loop-infrastructure.md` (pack-internal; mode and checkpoint
   tables live there, not inline in SKILL.md). Edit source at
   `packs/core/.apm/skills/work-loop/SKILL.md`, then `make build-self`.
4. **Architecture doc** — `docs/architecture/loop-infrastructure.md`, with a
   pointer added to the Subsystems section of `docs/architecture/overview.md`.

## Acceptance Criteria

### A — loop-engine.py: Command surface

- [x] **AC-A1.** Script lives at `packs/core/.apm/skills/work-loop/scripts/loop-engine.py`.
  Pure Python stdlib only. No external dependencies.

- [x] **AC-A2.** `loop-engine --help` and `loop-engine <command> --help` are
  sufficient to use the tool without reading the source. Every argument has a
  help string that explains what to pass.

- [x] **AC-A3.** All commands accept `<work-dir>` as either a **directory path**
  or a **file path**. When a file path is given (e.g., `docs/rfc/0076.md`), the
  engine resolves the parent directory as the work-dir and uses the file's stem
  as the `feature` name. When a directory is given, the directory is the work-dir
  and its basename is the `feature` name. `engine-state.json` always lives at
  `{resolved-work-dir}/engine-state.json`.

  Practical limit: one `engine-state.json` per directory. If two docs in the same
  directory need concurrent loop tracking, put each in its own subdirectory instead.

- [x] **AC-A4.** `loop-engine init <work-dir> --mode {code|spec-plan|doc}`
  creates `engine-state.json` atomically (tempfile + `os.replace`). Schema:
  ```json
  {
    "feature": "<basename of work-dir, or stem of doc file>",
    "mode": "code",
    "state": "SPEC-PLAN-DRAFTING",
    "last_transition_at": "<ISO-8601 UTC>"
  }
  ```
  If `engine-state.json` already exists, exits non-zero with a descriptive
  message rather than silently overwriting. (The skill calls `reset` before
  re-init when restarting.)

- [x] **AC-A5.** `loop-engine transition <work-dir> <event> [--fingerprints <hash>...]`
  validates the event against the transition table for the active mode (read from
  `engine-state.json`), fires any applicable guards in order, fires any applicable
  side effects on success, then writes the new state atomically. Exits non-zero
  with a descriptive one-line message if: (a) the event is invalid from the
  current state, or (b) any guard exits non-zero.

- [x] **AC-A6.** `loop-engine status <work-dir> [--json]` reads
  `engine-state.json`. With `--json`: emits the schema object to stdout, exits 0.
  Without `--json`: emits a human-readable one-line summary (`<feature> | <mode>
  | <state> | last transition: <relative time or timestamp>`), exits 0. Exits
  non-zero if `engine-state.json` is absent.

- [x] **AC-A7.** `loop-engine reset <work-dir>` deletes `engine-state.json`.
  Idempotent: exits 0 even if the file is already absent.

### B — loop-engine.py: Transition tables

State names embed the current phase so the position is readable at a glance.

- [x] **AC-B1.** Transition table for `code` mode:
  ```
  SPEC-PLAN-DRAFTING    + spec-ready       → SPEC-PLAN-REVIEW
  SPEC-PLAN-REVIEW      + reviewers-clean  → SPEC-PLAN-HUMAN-GATE
  SPEC-PLAN-REVIEW      + findings-remain  → SPEC-PLAN-DRAFTING
  SPEC-PLAN-HUMAN-GATE  + plan-approved    → CODE-IMPLEMENTATION
  SPEC-PLAN-HUMAN-GATE  + plan-rejected    → SPEC-PLAN-DRAFTING
  CODE-IMPLEMENTATION   + wave-complete    → CODE-VERIFICATION
  CODE-VERIFICATION     + gates-clean      → CODE-REVIEW
  CODE-VERIFICATION     + gates-failed     → CODE-IMPLEMENTATION
  CODE-REVIEW           + reviewers-clean  → CODE-HUMAN-GATE
  CODE-REVIEW           + findings-remain  → CODE-IMPLEMENTATION
  CODE-HUMAN-GATE       + done             → DONE
  CODE-HUMAN-GATE       + blocker-applied  → CODE-IMPLEMENTATION
  ```

- [x] **AC-B2.** Transition table for `spec-plan` mode (reuses first three code
  states; terminates at `SPEC-PLAN-HUMAN-GATE`):
  ```
  SPEC-PLAN-DRAFTING    + spec-ready       → SPEC-PLAN-REVIEW
  SPEC-PLAN-REVIEW      + reviewers-clean  → SPEC-PLAN-HUMAN-GATE
  SPEC-PLAN-REVIEW      + findings-remain  → SPEC-PLAN-DRAFTING
  SPEC-PLAN-HUMAN-GATE  + plan-approved    → DONE
  SPEC-PLAN-HUMAN-GATE  + plan-rejected    → SPEC-PLAN-DRAFTING
  ```
  `reviewers-clean` here means the spec/plan passes cold adversarial review —
  not that implementation is complete. This review cycle bypasses loop-cohort
  (no `review record` side effects; convergence bounded by LLM judgment).

- [x] **AC-B3.** Transition table for `doc` mode (covers RFC, ADR, architecture
  docs, and any other review-and-approve document):
  ```
  DOC-DRAFTING    + doc-ready       → DOC-REVIEW
  DOC-REVIEW      + reviewers-clean → DOC-HUMAN-GATE
  DOC-REVIEW      + findings-remain → DOC-DRAFTING
  DOC-HUMAN-GATE  + doc-approved    → DONE
  DOC-HUMAN-GATE  + doc-returned    → DOC-DRAFTING
  ```
  The SKILL.md defines what the human does at `DOC-HUMAN-GATE` for each document
  type. The engine does not distinguish between document types.

### C — loop-engine.py: Loop-cohort coordination and guards

Coordination with loop-cohort applies to `code` and `spec-plan` modes only.
`doc` mode bypasses loop-cohort entirely.

- [x] **AC-C1.** **Guards** — called before the named event is accepted;
  non-zero exit refuses the transition. Guards fire before the state write.

  *loop-cohort guards (code and spec-plan modes):*

  | Event | Current state | Guard | Mode |
  |-------|--------------|-------|------|
  | `plan-approved` | `SPEC-PLAN-HUMAN-GATE` | `loop-cohort check <work-dir> --phase plan` | code, spec-plan |
  | `wave-complete` | `CODE-IMPLEMENTATION` | `loop-cohort check <work-dir> --phase implement` | code |
  | `findings-remain` | `CODE-REVIEW` | `loop-cohort check <work-dir> --phase review` | code |

  `check --phase implement` and `check --phase review` both enforce iteration
  cap, token budget, and consecutive-same-error; `check --phase review` adds
  stasis detection.

  *Spec-status guard (code mode only):*

  | Event | Current state | Guard | Purpose |
  |-------|--------------|-------|---------|
  | `reviewers-clean` | `CODE-REVIEW` | `packs/core/.apm/skills/work-loop/scripts/check-spec-status.py <work-dir>` | `**Status:** Shipped` in working tree before PR goes to human |

  The spec-status guard fires at `CODE-REVIEW + reviewers-clean → CODE-HUMAN-GATE`
  — the point where the PR is about to be presented for human G-pr review. The
  LLM is expected to update the spec to `Status: Shipped` (and check off all ACs)
  before firing `reviewers-clean` from `CODE-REVIEW`. The guard verifies this
  happened. loop-engine does not edit `spec.md` — the update is an authored action.

  `reviewers-clean` from `SPEC-PLAN-REVIEW` (pre-plan phase) carries **no guard**
  — the spec is not being shipped at that point.

  **`plan-approved` guard pre-condition:** `loop-cohort check --phase plan`
  exits 0 only when `plan_review_status != "pending"`. The LLM must call
  `loop-cohort approve-plan <work-dir>` directly (after the pre-plan adversarial
  reviewer is clean and human G-plan sign-off is received) BEFORE firing
  `loop-engine transition plan-approved`. The guard verifies this happened.
  `approve-plan` is NOT a side effect — it is the mechanical step of G-plan.

  **Stasis detection sequencing:** the `findings-remain` guard (in `CODE-REVIEW`)
  fires before the `review record` side effect. It therefore sees fingerprints from
  the preceding round. Stasis is detected one round delayed.

- [x] **AC-C2.** **Side effects** — called after `engine-state.json` is
  written. Failure is logged to stderr; does not reverse the transition.

  | Event | Current state | Mode | Side effects (in order) |
  |-------|--------------|------|------------------------|
  | `init` (engine-level) | — | code, spec-plan | `loop-cohort init <work-dir>` (setup, not a transition) |
  | `plan-approved` | `SPEC-PLAN-HUMAN-GATE` | code only | `loop-cohort schedule <work-dir>` |
  | `reviewers-clean` | `CODE-REVIEW` | code only | `loop-cohort review record <work-dir> --report <report-path>` |
  | `findings-remain` | `CODE-REVIEW` | code only | `loop-cohort review record <work-dir> --fingerprint <h1> ...` |

  `review record` is **not idempotent** (increments `iteration_count`, rotates
  fingerprints). Do not retry it on failure; surface to the human instead.
  `schedule` is safe to re-run on failure.

  `reviewers-clean` and `findings-remain` side effects scope to `CODE-REVIEW`
  only — they do not fire when these events occur in `SPEC-PLAN-REVIEW` (pre-plan
  phase), which bypasses loop-cohort.

- [x] **AC-C3.** `engine-state.json` is written atomically (tempfile +
  `os.replace`). **loop-engine never reads or writes `state.json`** — that file
  belongs exclusively to loop-cohort. There is no field overlap between the two
  files as mutable state.

### D — check-spec-status.py

- [x] **AC-D1.** Script lives at
  `packs/core/.apm/skills/work-loop/scripts/check-spec-status.py`. Pure Python
  stdlib only. No external dependencies.

- [x] **AC-D2.** `check-spec-status.py <work-dir>` locates `spec.md` in
  `<work-dir>`, parses the `**Status:**` metadata line, and exits 0 if and only
  if the value is `Shipped`. Exits non-zero with a one-line message on stderr
  if: (a) `spec.md` is absent, (b) no `**Status:**` line is found, or (c) the
  value is not `Shipped`.

- [x] **AC-D3.** loop-engine invokes `check-spec-status.py` as a guard on
  `CODE-REVIEW + reviewers-clean → CODE-HUMAN-GATE` (code mode only). It is not
  invoked in spec-plan or doc modes, and is not invoked for any other event.

### E — Human gate invariants

These acceptance criteria protect `packs/core/DESIGN.md §4` (two human gates)
and `§13 invariant #1` (the loop cannot self-certify).

- [x] **AC-E1.** The checkpoint table in `references/loop-infrastructure.md`
  (see AC-H4) makes explicit that `plan-approved` is fired by the LLM **after**
  explicit human G-plan sign-off, not upon generating the plan. The LLM surfaces
  the plan and waits; the human approves; only then does the LLM call
  `loop-engine transition <work-dir> plan-approved`. G-plan remains a human gate;
  loop-engine automates nothing on the human's side.

- [x] **AC-E2.** The checkpoint table makes explicit that `done` fires after the
  human approved at G-pr and the merge is complete. The state `CODE-HUMAN-GATE`
  is the G-pr wait state; `done` fires when the human approved and the PR was
  merged. Loop-engine does not merge PRs; the human does.

- [x] **AC-E3.** loop-engine has no mechanism to mark a transition as bypassed
  or to override a guard's non-zero exit. There is no `--force` flag. A refused
  transition always exits non-zero.

- [x] **AC-E4.** (Human-wait states) A session may end in any of the following
  states with the work product committed to git on a named branch or open PR:
  `SPEC-PLAN-HUMAN-GATE`, `CODE-HUMAN-GATE`, `DOC-HUMAN-GATE`, or `DOC-REVIEW`
  (when review is async). When a new session resumes, it reads
  `loop-engine status <work-dir>` and waits for the human signal before firing
  the next event — it does not fire autonomously from a human-wait state.

### F — Iteration cap judgment

- [x] **AC-F1.** loop-engine does not read `max_iterations` from `state.json`
  and has no knowledge of iteration count. The iteration cap is a loop-cohort
  concern: `loop-cohort check --phase implement` exits non-zero when
  `iteration_count >= max_iterations`.

- [x] **AC-F2.** When `check --phase implement` or `check --phase review` signals
  a termination condition (iteration cap, token budget, stasis, consecutive-same-
  error), the SKILL.md's termination guidance applies: the LLM may (a) surface to
  the human with a concrete reason why another round is warranted and request
  permission, or (b) accept the signal and stop. The signal is judgment input, not
  a command. This guidance lives in SKILL.md, not in loop-engine.

### G — Spec status enum validation

- [x] **AC-G1.** `lint-spec-status.py` is extended to validate that the
  `**Status:**` field value is one of the canonical enum:
  `Draft | Approved | Implementing | Shipped | Archived`. Any other value causes
  a non-zero exit with a one-line message naming the offending value and listing
  the valid options. This catches hallucinated or non-standard status strings in
  CI and on-demand runs.

- [x] **AC-G2.** The checkpoint table in `references/loop-infrastructure.md`
  (AC-H4) includes the canonical status enum at the point where spec status is
  checked: `Valid status values: Draft | Approved | Implementing | Shipped |
  Archived`. This guides the LLM at write-time before a guard or linter can catch
  a hallucinated value.

### H — SKILL.md reduction

- [x] **AC-H1.** Edits are made to the source at
  `packs/core/.apm/skills/work-loop/SKILL.md`; the projection is regenerated
  via `make build-self`. No edits to projected copies.

- [x] **AC-H2.** Removed from SKILL.md: the inline loop-cohort verb call
  sequences embedded in the PLAN ("Initialize the loop's state file" block),
  EXECUTE (supervisor mode `loop-cohort schedule` / `loop-cohort dispatch-decision`
  blocks), REVIEW ("After each reviewer pass, record findings via the tool"
  block), and Termination (condition #2 `loop-cohort.py check` block).
  The judgment content adjacent to these blocks (risk triggers, reviewer
  selection, DECIDE routing, anti-patterns, supervisor wave flow) is unchanged.

- [x] **AC-H3.** Added to `references/loop-infrastructure.md` (pack-internal): a
  **mode-selection table** mapping detected work type to `loop-engine init --mode
  <mode>` (`code` for implementation, `spec-plan` for standalone spec/plan, `doc`
  for RFC/ADR/arch doc and any other review-and-approve document). Light mode
  explicitly noted as: "skip — not used."

- [x] **AC-H4.** Added to `references/loop-infrastructure.md`: a **checkpoint
  table** with columns: state, event the LLM fires to exit it, human gate
  requirement (if any), guards that run, and applicable mode(s). Includes the
  canonical spec status enum:
  `Valid status values: Draft | Approved | Implementing | Shipped | Archived`.

- [x] **AC-H5.** Added to SKILL.md: a 3-sentence **terse pointer** to
  `references/loop-infrastructure.md` under a "Loop-engine phase tracking (full
  mode only)" heading, replacing the removed loop-cohort prose. No
  `docs/architecture/` or other repo-local paths in SKILL.md — the core pack
  installs outside the repo.

- [x] **AC-H6.** Light mode is unchanged. The SKILL.md's existing "No
  `loop-cohort` state machine" note in the Modes section is extended to read:
  "No `loop-cohort` state machine and no `loop-engine` — light mode does not
  invoke either script."

- [x] **AC-H7.** The risk-triggers sentinel block
  (`<!-- risk-triggers:start -->` … `<!-- risk-triggers:end -->`) is preserved
  byte-identical. After editing, grep-equality against `AGENTS.md`,
  `packs/core/seeds/AGENTS.md`, and `docs/CONVENTIONS.md` is verified and passes.

### I — Architecture doc

- [x] **AC-I1.** `docs/architecture/loop-infrastructure.md` exists and covers
  all of the following:
  - Role and source-tree location of `loop-cohort.py` and `loop-engine.py`;
    what each owns.
  - Interaction model: engine calls cohort verbs as guards and side effects;
    cohort never calls engine; engine never reads or writes `state.json`.
  - State ownership table: fields in `state.json` vs `engine-state.json` with
    no mutable-state overlap; `max_iterations` explicitly in `state.json`.
  - Three modes (`code`, `spec-plan`, `doc`) with full transition tables and
    state names.
  - Guards table with current-state context, mode scope, and purpose per guard.
  - `check-spec-status.py` guard at `CODE-REVIEW + reviewers-clean` and the
    rationale for optimistic in-PR spec status update.
  - Human-wait states table and session-boundary resumption rule.
  - Convergence loops with four termination mechanisms for code mode.
  - Cross-reference to `packs/core/DESIGN.md §3` for light/full mode selection.

- [x] **AC-I2.** `docs/architecture/overview.md` Subsystems section includes a
  bullet for `loop-infrastructure.md` alongside the existing `pack-layout.md`,
  `agentbundle.md`, and `credentials.md` entries.

### J — Tests

- [x] **AC-J1.** `packs/core/.apm/skills/work-loop/scripts/test-loop-engine.py`
  exists and passes (15 tests). Co-located alongside the script it tests, matching
  the existing `test-lint-spec-status.py` pattern. Uses a temp directory as
  work-dir with no real git-state mutations. Covers: all three mode lifecycles,
  invalid transitions, guard refusal (loop-cohort and check-spec-status stubs),
  side-effect scope boundary (no review record from SPEC-PLAN-REVIEW), file-path
  resolution, and idempotent reset.

- [x] **AC-J2.** `packs/core/.apm/skills/work-loop/scripts/test-check-spec-status.py`
  exists and passes (9 tests). Covers: exits 0 when Status is Shipped; exits
  non-zero when Status is another canonical value; exits non-zero when `spec.md`
  is absent; exits non-zero when no bare `**Status:**` line is present; file path
  resolves to parent dir.

- [x] **AC-J3.** loop-cohort is absent in test dirs (guard returns non-zero,
  verifying wiring); `check-spec-status.py` is patched in-place for the guard
  refusal test and restored in a `finally` block.

### K — Pack version bump

- [x] **AC-K1.** `packs/core/pack.toml` version is bumped (patch) to reflect the
  new scripts (`loop-engine.py`, `check-spec-status.py`) and SKILL.md reduction.
  Run `make build-self` after bumping so the projected `plugin.json` reflects the
  new version. Current version at spec time: `0.15.7`.

### L — Gitignore and ecosystem

- [x] **AC-L1.** `docs/specs/**/engine-state.json` is covered by `.gitignore`.
  Verify with `git check-ignore -v docs/specs/dummy/engine-state.json`.

- [x] **AC-L2.** After spec and plan are approved (G-plan), add
  `"spec/loop-engine-phase-1"` to `["ini-002".work].queue` in `workspace.toml`.

- [x] **AC-L3.** In `docs/product/shaping/ecosystem-overview.md`, add one
  sentence to the INI-003 section stating that `loop-engine status --json` is
  the per-worker observation interface factory workers call to observe headless
  loop instances.

## Boundaries

### Always do

- Edit the SKILL.md source under `packs/core/.apm/skills/work-loop/`, not the
  projection. Run `make build-self` after.
- Implement `loop-engine.py` and `check-spec-status.py` using pure Python stdlib
  only; no external packages.
- Keep `loop-cohort.py` unchanged. Zero edits to that file.
- Write `engine-state.json` atomically (tempfile + `os.replace`) on every
  mutation.
- Run `SKIP_SAST=1 make build-check` after all code changes before review.

### Ask first

- Any deviation from the transition tables in AC-B1–AC-B3.
- Any addition to loop-engine's verb surface beyond `init`, `transition`,
  `status`, `reset`.
- Any change to `state.json` schema or `loop-cohort.py` behavior.
- Adding a `--force` flag or any mechanism to override a guard's refusal.
- loop-engine editing `spec.md` or any file other than `engine-state.json`.

### Never do

- Have loop-engine read or write `state.json`. That belongs exclusively to
  loop-cohort.
- Invoke loop-engine in light mode. The SKILL.md update must be explicit.
- Add pack-detection logic to loop-engine. The skill decides the mode; the
  engine is mode-agnostic.
- Fire `plan-approved` before human G-plan sign-off, or `done` before human
  G-pr merge.
- Fire the next event from a human-wait state (`SPEC-PLAN-HUMAN-GATE`,
  `CODE-HUMAN-GATE`, `DOC-HUMAN-GATE`) autonomously across a session boundary.

## Testing Strategy

**loop-engine.py + check-spec-status.py (TDD + manual QA):**
- TDD: AC-J1/AC-J2/AC-J3 integration tests cover the full lifecycle for all three
  modes, invalid transitions, guard refusal (loop-cohort and check-spec-status),
  side-effect ordering, and the scope boundary (no review record from
  SPEC-PLAN-REVIEW). Red stubs written before implementation.
- Manual QA: run `loop-engine --help` and all subcommand `--help`; confirm
  self-documenting output. Run a real `spec-plan` lifecycle on a scratch spec
  directory; verify `engine-state.json` advances through
  `SPEC-PLAN-DRAFTING → SPEC-PLAN-REVIEW → SPEC-PLAN-HUMAN-GATE → DONE` and
  `loop-engine status --json` emits valid JSON at the end.

**SKILL.md reduction (goal-based + visual QA):**
- Goal-based: `make build-self` passes; `python tools/lint-agent-artifacts.py`
  passes; risk-triggers grep-equality holds across all four locations (AC-H7).
- Visual QA: diff the updated SKILL.md against origin/main; confirm removed
  prose is precisely the loop-cohort choreography, judgment content is intact,
  and the mode-selection and checkpoint tables are present.

**Architecture doc (design-reviewer gate during PLAN):**
- Draft `loop-infrastructure.md` before finalising the plan; run `design-reviewer`
  iterating until SHIP IT or SHIP WITH CHANGES with no remaining blockers.
  Seed with: agreed concept (cohort owns state.json; engine owns engine-state.json;
  one-way direction; light mode skips both), constraints (pure stdlib, no branch
  changes, cohort unchanged, backwards-compatible state.json).

## Assumptions

1. `loop-cohort.py` has a stable exit-code contract (exit 0 success, non-zero
   with one-line reason on stderr). This spec does not change that contract.
2. `make build-self` regenerates the projected SKILL.md after source edits.
3. `SKIP_SAST=1 make build-check` is the appropriate gate for non-SAST changes.
4. The `doc` mode is invoked for RFC, ADR, and arch docs; the engine does not
   distinguish between document types. Mode selection is a SKILL.md obligation.
5. `docs/specs/**/state.json` is already in `.gitignore`; `engine-state.json`
   may or may not be covered (AC-L1 requires verification).
6. `last_transition_at` ISO-8601 UTC timestamps are sufficient for INI-003's
   stale-worker detection. No sub-second precision is required.
