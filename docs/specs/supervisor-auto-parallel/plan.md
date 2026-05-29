# Plan: unattended auto-parallel for supervisor mode

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done <!-- Drafting | Executing | Done -->

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document is allowed to change as you learn. When it changes substantially
> (a different approach, not just a re-ordering), note why in the changelog
> at the bottom.

## Approach

The change is small and lives entirely in `loop-cohort.py` + `state.json` +
the doc-of-record — **no new module, dependency, or top-level dir** (ADR-0005 /
spec Boundaries). The whole feature is a **doc branch backed by one state
field**: follow-on 1 already expresses "present → opt-in → default sequential"
as an instruction the agent follows, so follow-on 4 adds (T1) an
`auto_parallel` field + a setter verb mirroring `approve-plan`, and (T2) the
SKILL §EXECUTE + supervisor-mode branch that reads it. T1 is TDD over the state
mutation; T2 + the clean-projection check are goal-based. The authoritative
gate, the `Touches:` screen, and `merge-abort` are **not touched** — this only
removes the human-confirm step for an already-cleared wave.

## Constraints

- **RFC-0015 + ADR-0005** — the gate (decision 3) and the read/write split stay
  authoritative; `auto_parallel` is GO-approval-only, never a gate input.
- **Parent specs** — `wave-scheduled-supervisor` (`state.json`, `approve-plan`,
  supervisor-mode procedure, follow-on 1), `supervisor-auto-classify`,
  `supervisor-predict-disjointness` (the gate/screen that must stay untouched).
- Self-host projection rule — edit `packs/core/...` source then `make
  build-self`; never edit the generated `.claude/...` copies.

## Construction tests

Most live per-task below. Cross-cutting:

**Integration tests:** none beyond per-task.
**Manual verification:** none — the doc branch is grep-verified; behavior is the
agent following the documented instruction (same shape as follow-on 1).

## Tasks

### PT1: `auto_parallel` state field + setter verb (AC1, AC2, AC5, AC4a)

**Depends on:** none

**Tests:** (`packages/agentbundle/tests/unit/`)
- a freshly `init`-ed `state.json` has `auto_parallel == False` (AC1).
- the setter verb flips it to `True` (atomic write); the `--off` form sets it
  back to `False`; a read-back pins both transitions (AC2).
- `auto_parallel` is **not** a parameter of `dispatch_decision`
  (`inspect.signature` stays `(categories, *, merge_tree_clean)`) — not a gate
  input (AC5).
- **code-backed failure backstop (AC4a):** `auto_parallel` is **absent** from
  `inspect.getsource(cmd_worktree_merge)` — the merge-abort backstop can't be
  influenced by the flag (structural test, mirroring AC5).

**Approach:**
- Add `"auto_parallel": false` to `assets/state.json`.
- Add `cmd_auto_parallel` mirroring `cmd_approve_plan` (read→set→atomic-write):
  sets `state["auto_parallel"] = not args.off`; register the verb in
  `build_parser` with a `--off` flag.
- Document in `references/state-schema.md`: the field in the fields table
  **and** the new setter verb in the verb roster (line ~13, the "only sanctioned
  way to write `state.json`" list) — a flat top-level field, explicitly distinct
  from the `worktrees` schema → no dry-run (AC1).

**Done when:** AC1/AC2/AC5/AC4a tests green; field defaults false; verb flips
both ways; `cmd_worktree_merge` provably free of `auto_parallel`.

### PT2: doc-of-record branch + strict boundary + clean projection (AC3, AC4b, AC6)

**Depends on:** PT1

**Tests:** (goal-based)
- grep confirms **both** `work-loop/SKILL.md` §EXECUTE and
  `references/supervisor-mode.md` state the branch with the
  `auto_parallel`-true clause **co-occurring with "gate-cleared"/"already
  cleared"** in the same block (so a vacuous doc fails); when false, follow-on
  1 is unchanged (AC3).
- grep confirms the existing follow-on-1 sentence ("an unattended run proceeds
  sequentially rather than blocking") is **qualified** to be conditional on
  `auto_parallel` being unset, in both surfaces (AC3 — no stale false claim).
- grep confirms both state the **doc-enforced** boundary: a blocked/failed
  implementer under `auto_parallel` still **Surfaces and stops** (no auto-retry
  / relaxed re-run) (AC4b).
- `make build-self` leaves a clean tree; both lint surfaces pass; grep confirms
  no new module/dir/dependency (AC6).

**Approach:**
- Edit the **follow-on-1 blocks specifically** — `SKILL.md` §EXECUTE (the
  "present the cleared-gate opportunity" paragraph) + the supervisor-mode
  "Present the cleared-gate opportunity" header block — concept only, **none of
  the six dry-run-gated worktree procedure surfaces** (pre-flight, worktree
  creation, report ordering, merge order, cleanup, `worktrees` schema; same
  carve-out as parent T3/T7). On a cleared gate, branch on `auto_parallel`: set
  ⇒ proceed in parallel without opt-in; unset ⇒ follow-on 1. **Qualify** the
  existing "proceeds sequentially" sentence so it's conditional on the flag
  being unset. State the boundary inline (GO-approval-only for an
  already-cleared wave; failures still Surface). `make build-self`.

**Done when:** AC3/AC4b grep checks pass on both surfaces (incl. the qualified
sentence + co-occurrence anchor); clean tree, both lint surfaces green, AC6 holds.

## Rollout

Purely additive and backward-compatible: `auto_parallel` defaults `false`, so
every existing run behaves exactly as today (follow-on 1). The switch is
session scratch (`state.json`), scoped per run; a fresh run starts off.
Reversible — removing the field + verb + doc branch restores follow-on-1-only
behavior. No default flips.

## Risks

- **A flag-on run proceeds on a wave the gate shouldn't have cleared** → bounded:
  `auto_parallel` is GO-approval-only and never a gate input; the gate +
  `merge-abort` backstop are unchanged, so a real collision still aborts and
  Surfaces. The flag widens *who approves*, not *what's allowed*.
- **User forgets the flag is on** → bounded by the per-run/default-off design
  (no sticky global); a fresh run is always off.
- **Doc-only enforcement** (the branch is an instruction, like follow-on 1) →
  accepted: it mirrors the existing, working follow-on-1 mechanism; the state
  field gives a concrete, testable artifact the agent consults.

## Changelog

- 2026-05-29: initial plan (implements ROADMAP follow-on 4 of
  `wave-scheduled-supervisor` — the autonomy capstone; Constrained-by RFC-0015
  + ADR-0005). Per-run `auto_parallel` state field + setter verb + doc branch;
  GO-approval-only, failures still Surface; default off (user-confirmed
  2026-05-29).
- 2026-05-29 (spec-mode review): AC4 split into **AC4a** (code-backed — a
  structural test that `cmd_worktree_merge` doesn't read `auto_parallel`, so the
  merge-abort backstop is flag-independent) and **AC4b** (doc-enforced
  implementer-blocked stop); AC1 pins `auto_parallel` as a top-level field
  distinct from the dry-run-gated `worktrees` schema; AC3 adds the
  co-occurrence grep anchor + a requirement to **qualify** the now-stale
  follow-on-1 "proceeds sequentially" sentence; citation points at the pack
  source, not the projected copy.
