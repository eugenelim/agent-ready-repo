# Spec: work-loop queue-to-shipped fix

- **Status:** Shipped <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Mode:** full (governance boundary — modifies a core skill's observable behaviour)
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** RFC-0064 (workspace.toml schema), workspace.toml ini-002

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

Two complementary fixes to the work-loop lifecycle so a spec is never left
dangling in `[work].queue` after its PR merges, plus a bundled fix for a
pre-existing path-resolution bug in Step 0.

**Root cause (observed with `spec/queue-add`, PR #566):** the done-step moves
a path from `active → shipped` only when `active` holds that path. When a
session starts work on a spec that was never moved from `queue → active`, the
done-step condition is false and `workspace.toml` is never updated.

**Fix 1 — done-step:** for each active initiative, extend the condition to
check `active` *or* `queue`. Move from whichever list (in whichever initiative)
holds the current spec's path. `active` is checked before `queue`. Queue
entries in `[work]` are bare strings or inline objects with a `path` field
(RFC-0064 `[work]` schema; `slug` is a shaping-queue field only); when an
object entry is moved, it collapses to a bare path string in `shipped`
(dropping `needs` and other fields).

**Fix 2 — Step 0 stale-queue warning:** after reading `workspace.toml`, check
every entry in `queue` and `active` for a `spec.md` that already reads
`Status: Shipped`. Surface a warning line for each stale entry and **proceed
to PLAN** — Fix 2 is advisory and non-blocking. The stale-check resolves entry
paths for lookup and naming purposes only; it never writes to `shipped`.

**Bundled fix — Step 0 line 177 path-resolution:** the existing Active-spec
orientation line reads `docs/specs/<path>/spec.md` where `<path>` is the
stored `spec/<slug>` value — producing the non-existent path
`docs/specs/spec/<slug>/spec.md`. Fix: strip the `spec/` prefix before
constructing the path, yielding `docs/specs/<slug>/spec.md`. Same resolution
rule as Fix 2; co-located under Task 1 as a same-file, same-concern
mechanical ride-along.

**Out of scope (not in this spec):**
- Step 0 surfacing the next unblocked queue item when `active` is empty.
- The `spec/workspace-status-queue-reconciliation` queue entry (different
  check, different direction — remains in the queue for separate implementation).

## State transitions

```
queue ──────────────────────────────────────► shipped   (Fix 1: done-step, new path)
queue ──► active ──────────────────────────► shipped   (existing path, unchanged)
queue / active → stale (Shipped) ──────────► warning   (Fix 2: Step 0 warns, proceeds)
```

### Case analysis (pressure-test)

| Case | Before | After Fix 1 | After Fix 2 |
|------|--------|-------------|-------------|
| A. Spec starts in `queue`, session works it, done-step fires | queue stays; workspace.toml not updated ❌ | moved to shipped ✓ | — |
| B. Spec moved to `active` before work (existing behaviour) | moved to shipped ✓ | unchanged ✓ | — |
| C. Spec in neither `active` nor `queue` | done-step skipped ✓ | unchanged ✓ | — |
| D. `workspace.toml` absent | done-step skipped ✓ | unchanged ✓ | — |
| E. Stale `queue` entry from a previous session | stays in queue across sessions ❌ | not caught at Step 0 | warning emitted; PLAN proceeds; user cleans up ✓ |
| F. Stale `active` entry from a previous session | stays in active across sessions ❌ | not caught at Step 0 | warning emitted; PLAN proceeds; user cleans up ✓ |
| G. Spec in both `active` and `queue` (invariant violation) | active → shipped; queue dangling | active checked first → moved from active; queue entry remains | dangling queue entry flagged by stale-queue warning on next session ✓ |
| H. Path in queue but no `spec.md` exists yet | — | — | silently skipped (spec not yet started) ✓ |
| I. Path in queue, `spec.md` exists, Status: Implementing | — | — | silently skipped (still in-flight) ✓ |
| J. Done-step fires, spec already in `shipped` | done-step skips (not in active) ✓ | not in active or queue → skips ✓ | — |
| K. This spec itself (`spec/work-loop-queue-shipped-fix`) ships | n/a | Fix 1 finds it in `queue` (added by Task 4a) → moves to shipped ✓ | — |
| L1. Current spec stored as inline object `{path = "spec/work-loop-queue-shipped-fix", needs = ...}` | — | path extracted from `path` field; moved to `shipped` as bare string; `needs` dropped ✓ | — |
| L2. Stale inline-object entry from a previous session `{path = "spec/foo", needs = ...}` | — | — (not the current spec) | warning emitted using resolved path from `path` field ✓ |

Case K is deliberate self-validation: this spec's path is added to
`workspace.toml` queue (Task 4a) so Fix 1 moves it to `shipped` as part of
this PR's diff, proving the fix works end-to-end.

## Acceptance Criteria

- [x] AC1. Done-step: if the current spec's path is in `["<slug>".work].queue`
  (and not in `active`), the done-step moves it from `queue → shipped` and
  stages the edit as part of this PR's diff (Cases A, K).
- [x] AC2. Done-step: existing `active → shipped` path is unchanged (Case B).
- [x] AC3. Done-step: if the path is in neither list, the step is skipped with
  no edit and no error (Cases C, D, J).
- [x] AC4. Done-step: `active` is checked before `queue`; a path found in
  `active` is moved from there (Case G partial cleanup).
- [x] AC5. Step 0: for each active initiative, any entry in `queue` or `active`
  whose corresponding spec.md already has `Status: Shipped` produces a
  non-blocking `Warning:` line naming the path and which list(s) it was found
  in; PLAN proceeds immediately after. Entries with no spec.md, or any other
  Status value, produce no output. The resolution algorithm (how queue entry
  paths map to filesystem paths, bare-string vs inline-object handling,
  trailing-comment stripping) is in plan Task 2.
- [x] AC6. Done-step: when an inline object entry (`{path = ..., needs = ...}`)
  is moved to `shipped` by the done-step, it is written as a bare path string
  (dropping `needs` and other fields), consistent with existing `shipped`
  entries (Cases L1).
- [x] AC7. Bundled fix: Step 0's Active-spec orientation correctly resolves
  `docs/specs/<slug>/spec.md` by stripping the `spec/` prefix from the stored
  path value (e.g. stored `spec/m1-work-queue` → reads `docs/specs/m1-work-queue/spec.md`).
- [x] AC8. All three `SKILL.md` copies are byte-identical after the change:
  `.claude/skills/work-loop/SKILL.md`, `.agents/skills/work-loop/SKILL.md`,
  `packs/core/.apm/skills/work-loop/SKILL.md`.

## Boundaries

**Touches:**
- `packs/core/.apm/skills/work-loop/SKILL.md` (source of truth; includes bundled fix to line 177 path-resolution)
- `docs/product/roadmap.md` (one line added by the done-step roadmap reminder when this spec ships)
- `.claude/skills/work-loop/SKILL.md` (projection — sync from pack source)
- `.agents/skills/work-loop/SKILL.md` (projection — sync from pack source)
- `workspace.toml` — add `spec/work-loop-queue-shipped-fix` to queue (Task 4a); done-step moves it to shipped in this PR's diff (Task 4b)
- `docs/specs/queue-add/spec.md` — Status flipped to Shipped, all ACs checked; this is the spec that triggered the bug (PR #566 merged without workspace.toml update). Closing out that drift is an intentional dogfood cleanup of the exact failure mode this PR fixes — not a new scope item.
- This spec file and plan.md

**Never:**
- Block PLAN or halt the session based on stale-queue findings (Fix 2 is advisory)
- Auto-move any workspace.toml entry in Step 0 (warn only; stale-check never writes)
- Add a new bucket to `[work]` (no `archived` or `stale` array)
- Add a new dependency to the pack

**Ask first:**
- Any change to the workspace-status skill
- Any change to `spec/workspace-status-queue-reconciliation` queue entry
- Pack version bump (doc-only change here; release is a separate decision)

## Testing strategy

Manual QA — there are no unit tests for skill markdown. Verification:
1. Walk each Case A–L2 against the updated skill prose. Every case must be
   handled unambiguously by the text. L1 verifies inline-object field-dropping
   (AC6); L2 verifies stale-check path resolution from an object's `path` field
   without writing (Fix 2 warn-only boundary).
2. Walk Step 0's orientation prose: confirm the bundled fix makes stored path
   `spec/<slug>` resolve to `docs/specs/<slug>/spec.md`, not
   `docs/specs/spec/<slug>/spec.md` (AC7).
3. `diff` the three SKILL.md copies to confirm byte-identity (exit 0).
4. Confirm `spec/work-loop-queue-shipped-fix` is in `workspace.toml` `shipped`
   and absent from `queue` in the final merged state (Case K self-validation).
   The add-to-queue and queue→shipped move land as separate commits; the
   aggregate diff from `main` shows the entry only in `shipped`.
