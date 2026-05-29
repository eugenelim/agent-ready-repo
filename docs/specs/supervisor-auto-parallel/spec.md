# Spec: unattended auto-parallel for supervisor mode

- **Status:** Shipped <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** RFC-0015, ADR-0005

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

Today supervisor mode never runs a wave in parallel without a **live human
opt-in** (follow-on 1): when a wave clears the gate, the loop *presents* the
opportunity and, absent an explicit "go", defaults to sequential. That makes
unattended completion impossible — leave your desk and the plan finishes
**entirely serially**, because no one is present to approve the safe waves.

This spec adds a **per-run pre-authorization** so a plan can complete
unattended while still taking the safe parallel waves: a `loop-cohort`
verb writes `auto_parallel: true` into *this run's* `state.json`, and when it
is set the supervisor **proceeds in parallel on a wave that has already
cleared every gate** — skipping only the human-confirm step, nothing else.

For the agent running a multi-task plan, the user-visible outcomes are:

1. **An off-by-default per-run switch.** A `loop-cohort` verb sets
   `auto_parallel` in the spec's `state.json` (default `false`); a `--off`
   form clears it. The field is session scratch, scoped to one plan's run — a
   fresh run starts `false`, so it can never be silently left globally on.
2. **Auto-approve the GO, only for already-cleared waves.** When
   `auto_parallel` is `true` and a wave has cleared the gate
   (safe-category ∧ `git merge-tree` disjoint ∧ not predicted-overlap), the
   supervisor fans out **without** waiting for human opt-in. When
   `auto_parallel` is `false`, behavior is unchanged (follow-on 1: present →
   opt-in → default sequential).
3. **Nothing else changes.** A wave that did **not** clear the gate still runs
   serial regardless of the flag; the gate, the `Touches:` screen, and the
   `merge-abort` backstop are untouched. A parallel wave that **fails**
   (merge-abort fires on a collision the gate missed) still **Surfaces and
   stops** — even unattended — never auto-retries and never relaxes a gate.

Success: with `auto_parallel` set, an unattended run takes every gate-cleared
wave in parallel and the rest serially; with it unset, behavior is exactly
today's; and no failure path auto-recovers because the flag is on.

## Boundaries

### Always do

- **Auto-approve the GO only.** `auto_parallel` removes *only* the human-confirm
  step for a wave that has **already cleared every gate**. It is never an input
  to the gate itself.
- **Default off, per-run.** The field lives in the spec's `state.json` (session
  scratch), defaults `false`, and is set explicitly per run.
- **Preserve every backstop.** Gate (category ∧ merge-tree ∧ `Touches:` screen)
  and `merge-abort → re-PLAN` are unchanged; a non-cleared wave stays serial.
- **Surface failures even when unattended.** A merge-abort or non-ready
  implementer still stops the loop and Surfaces — `auto_parallel` never triggers
  a retry or a relaxed re-run.
- **Mutate `state.json` only through a `loop-cohort` verb** (atomic write),
  never by hand — same discipline as `approve-plan`.

### Ask first

- Making `auto_parallel` **sticky / global** (a remembered cross-run preference)
  rather than per-run — needs Owner sign-off (re-introduces the
  forgot-it's-on risk this spec avoids).
- Letting `auto_parallel` **influence the gate** (e.g. loosen a category or skip
  the merge-tree check) in any way — it must stay GO-approval-only.

### Never do

- **Never add a new module, package, top-level directory, or runtime
  dependency** — the field + verb live in the existing `loop-cohort.py` +
  `state.json` (RFC-0015: reuse).
- **Never auto-recover.** A failed parallel wave under `auto_parallel` Surfaces
  and stops; the flag must not cause a silent retry, a serial re-run, or a
  gate relaxation.
- **Never let `auto_parallel` parallelize a wave the gate did not clear.**

## Testing Strategy

- **The setter verb + state field** — **TDD**. `auto_parallel` defaults
  `false`; the verb flips it `true` (and `--off` back to `false`) via atomic
  write, mirroring `approve-plan`; a read-back asserts the value. Construction
  tests in `plan.md`.
- **The doc-of-record branch** (SKILL §EXECUTE + supervisor-mode.md) —
  **goal-based check**: a grep confirms both surfaces state the
  `auto_parallel`-set branch (proceed on a cleared gate without opt-in) **and**
  the strict boundary (only-already-cleared; failures still Surface). Mirrors
  how follow-on 1's instruction is verified.
- **Clean projection** — **goal-based check**: `make build-self` leaves a clean
  tree, both lint surfaces pass, no new module/dep/dir; `state-schema.md`
  documents the new field.

## Acceptance Criteria

- [x] AC1 — `state.json` carries `auto_parallel` defaulting to `false` (template
  + a freshly `init`-ed state); `references/state-schema.md` documents it in
  **both** the fields table **and** the verb roster (the new setter joins
  `init`/`approve-plan`/`review record`/`worktree` as a sanctioned writer).
  `auto_parallel` is a **flat top-level field, distinct from the dry-run-gated
  `worktrees` schema** (CONVENTIONS § Supervisor mode "Known limitation"), so no
  worktree dry-run is required for this change.
- [x] AC2 — a `loop-cohort` verb sets `auto_parallel: true` for a spec via
  atomic write, and a `--off` form sets it back to `false`; a read-back test
  pins both transitions. (Mutation-only-through-the-verb is convention-enforced,
  parity with `approve-plan` — not separately test-pinned.)
- [x] AC3 — SKILL §EXECUTE + `references/supervisor-mode.md` document the
  branch: when `auto_parallel` is **true**, a **gate-cleared** wave fans out
  **without** the human opt-in (the `auto_parallel`-true clause must **co-occur
  with "gate-cleared" / "already cleared"** in the same block, so a vacuous doc
  fails the check); when **false**, follow-on 1 is unchanged (present → opt-in →
  default sequential). The existing follow-on-1 sentence ("an unattended run
  proceeds sequentially rather than blocking") is **qualified** to be
  conditional on `auto_parallel` being unset, so it is not left false. A grep
  pins the branch + the qualification in both surfaces.
- [x] AC4 — failures still stop the loop under `auto_parallel`, via two
  **distinctly-named** paths: (a) **code-backed** — the `worktree merge`
  merge-abort backstop does **not** read `auto_parallel` (a structural test
  asserts `auto_parallel` is absent from `cmd_worktree_merge`), so a real
  collision aborts + exits non-zero regardless of the flag; (b) **doc-enforced**
  — both surfaces state that a blocked/failed implementer under `auto_parallel`
  still **Surfaces and stops** (no auto-retry / no relaxed re-run), grep-verified.
- [x] AC5 — the gate path (`dispatch_decision` / `wave_is_disjoint` /
  `classify_task` / `globs_overlap`) is **unchanged**; a test asserts
  `auto_parallel` is not an input to `dispatch_decision` (`inspect.signature`
  stays `(categories, *, merge_tree_clean)`); it is never a gate input.
- [x] AC6 — `make build-self` leaves a clean tree and both lint surfaces pass;
  no new module, dependency, or top-level directory was introduced.

## Assumptions

- Technical: the setter mirrors `cmd_approve_plan` — a verb that flips a
  `state.json` field via read→set→atomic-write (source — **edit the pack
  source, not the projected copy**: `packs/core/.apm/skills/work-loop/scripts/loop-cohort.py:654`).
- Technical: `state.json` is a flat field set (source: `assets/state.json`
  probe); `auto_parallel: false` joins it; `references/state-schema.md` exists
  and documents the schema.
- Technical: follow-on 1's present→opt-in→default-sequential is a **doc
  instruction** in SKILL §EXECUTE + supervisor-mode.md (no code-enforced wait),
  so follow-on 4 is a state field + setter verb + a doc branch the agent reads —
  symmetric with follow-on 1 (source: `SKILL.md:293-297` probe).
- Technical: `state.json` is gitignored session scratch, scoped per spec-dir, so
  the field is naturally **per-run** (a fresh run defaults `false`) (source:
  work-loop state-schema convention).
- Technical: tests land in the agentbundle unit suite (source: parent-spec
  precedent).
- Process: per-run (not sticky/global), default off, dedicated setter verb,
  GO-approval-only with failures still Surfacing (source: user confirmation
  2026-05-29).
- Process: rides as a spec Constrained-by RFC-0015 + ADR-0005 (the autonomy
  capstone of the wave-scheduled-supervisor line; not a new architectural
  decision) (source: user confirmation 2026-05-29).
- Process: Owner = eugenelim; Draft → Shipped status set in the implementing PR
  (source: [[feedback_set_final_status_in_implementing_pr]] convention).
- Product: serves the "leave my desk, let the plan finish, taking safe parallel
  waves on its own" case; T2-live (real-implementer break frequency) stays out
  of scope (source: user confirmation 2026-05-29).
