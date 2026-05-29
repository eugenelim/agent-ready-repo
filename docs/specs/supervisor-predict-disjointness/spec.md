# Spec: predict wave file-disjointness before dispatch

- **Status:** Shipped <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** RFC-0015, ADR-0005

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

Today supervisor mode can only learn whether a wave's tasks collide on files
**after** dispatching them and letting them write (`git merge-tree` on populated
branches, with the step-5 merge-abort as the loud backstop). This spec adds a
**cheap pre-dispatch screen**: a plan task may declare the file globs it
expects to touch (a new optional `**Touches:**` line, parsed by `loop-cohort`
exactly as `Depends on:` is), and `loop-cohort schedule` predicts, per wave,
whether the wave's declared globs are disjoint — surfacing
`predicted-disjoint: yes | no | unknown` so an obviously-colliding wave is
serialized **before** anyone pays to dispatch it.

For the agent running a multi-task plan, the user-visible outcomes are:

1. **A `Touches:` line is parseable and optional.** A task may declare
   comma-separated path globs (e.g. `src/api/*.py, docs/api.md`); `parse_plan`
   exposes them per task. A task with no `Touches:` is fine — it is reported
   `unknown`, never an error, and no existing plan needs backfilling.
2. **`schedule` annotates each multi-task wave** with `predicted-disjoint:`
   — `no` when two tasks' declared globs overlap, `yes` when all declared and
   pairwise-disjoint, `unknown` when any task in the wave lacks `Touches:`.
3. **The prediction only ever says NO, never YES.** It is a screen, not a
   greenlight: `predicted-disjoint: no` is a reason to serialize early;
   `yes`/`unknown` change nothing about the authoritative gate — parallel
   writes **still** require the post-write `git merge-tree` disjointness check
   (and step-5 merge-abort). A wrong/under-declared `Touches:` can therefore
   never cause a silent parallel-write break; at worst it fails to catch a
   collision early, which the authoritative check then catches.

Success: a wave whose tasks declare overlapping globs is flagged
`predicted-disjoint: no` (serialize early) without dispatching; a wave with
disjoint or missing declarations is not green-lit by this feature alone; and
no existing plan breaks for lacking `Touches:`.

## Boundaries

### Always do

- **Screen-only, never greenlight.** The prediction may *downgrade* a wave to
  serial (`no`) but must never *promote* one to parallel — the post-write
  `git merge-tree` check stays the sole authority for actually parallelizing.
- **Treat missing/empty `Touches:` as `unknown`**, never as disjoint and never
  as an error.
- **Reuse the `Depends on:` parsing + plan-template machinery** (`parse_plan`,
  `DEPENDS_LINE_RE`-style line, the grammar block in the plan template).
- **Be conservative in the overlap heuristic** — when unsure whether two globs
  intersect, predict overlap (`no`), because over-serializing is fail-safe and
  the authoritative check covers any miss.

### Ask first

- Making `Touches:` **mandatory** (would force backfilling 244 existing tasks)
  or adding a lint that fails on its absence.
- Letting the prediction **influence the parallel greenlight** in any way
  (it must stay a serialize-only screen) — needs Owner sign-off.

### Never do

- **Never add a new module, package, top-level directory, or runtime
  dependency** — this lives inside the existing `loop-cohort.py` + plan
  template (RFC-0015: reuse). Stdlib glob (`fnmatch` / `PurePosixPath`) only.
- **Never let a declared-disjoint or unknown prediction skip the post-write
  `git merge-tree` check** — that is the trust-globs-to-greenlight path this
  spec rejects (under-declaration is unsafe).
- **Never raise/fail on a task that omits `Touches:`** — optional means
  optional.

## Testing Strategy

- **`parse_touches` + `parse_plan` exposure** — **TDD**. Pure parsing of a
  comma-separated glob list (prose-tolerant like `parse_depends_on`); a task
  without the line yields no globs. Compressible invariant; construction tests
  in `plan.md`.
- **`globs_overlap` / `wave_touches_disjoint`** — **TDD**. Pure functions over
  declared glob sets; the conservative invariant (shared-prefix / literal-match
  ⇒ overlap; provably-disjoint ⇒ disjoint; any-missing ⇒ unknown). Includes
  fail-safe fixtures (ambiguous globs predict overlap).
- **`schedule` per-wave annotation** — **TDD** via subprocess against a fixture
  plan: a wave with overlapping `Touches:` prints `predicted-disjoint: no`; an
  all-disjoint wave prints `yes`; a wave with a `Touches:`-less task prints
  `unknown`. Exit code unchanged (annotation is advisory, not a gate).
- **Plan-template grammar + screen-only invariant doc** — **goal-based check**:
  the plan template documents the optional `Touches:` grammar; a grep confirms
  the screen-only rule is stated in `schedule`'s output/docs and that
  `dispatch-decision`'s authoritative merge-tree path is untouched.

## Acceptance Criteria

- [x] AC1 — `parse_touches(field)` parses a comma-separated glob list
  (tolerating trailing prose like the `Depends on:` parser); `parse_plan`
  exposes per-task globs, and a task with no `**Touches:**` line yields an
  empty/absent set with **no error**.
- [x] AC2 — `globs_overlap(a, b)` is **conservative — it returns `True`
  (overlap) unless the pair is *provably disjoint*** (so a both-ways
  `.match`-miss is **not** taken as proof of disjointness). Segment-wise
  semantics: `*` matches within one `/`-segment, never across `/`. Provably
  disjoint (`False`) **only** when: (a) neither glob contains `**` **and** they
  have a different number of `/`-segments (different depth); **or** (b) at some
  **aligned segment** both sides are pure literals that differ, or one side is
  a literal the other side's segment-pattern cannot `fnmatch`. A segment is a
  **pure literal** iff it contains no glob metacharacter — pinned as
  `glob.escape(seg) == seg` (none of `* ? [`), so a character-class segment
  like `[abc].py` is a *pattern*, not a literal, and is compared via `fnmatch`
  (never the literal `==` shortcut). Any glob containing `**`, and any aligned
  segment where both sides are patterns, counts as **could-overlap → `True`**.
  Fixtures pin every branch:
  `src/a/*` vs `src/b/*` → False (literal-segment mismatch); `src/*` vs
  `src/api/x.py` → False (depth, no `**`); `src/api/*` vs `src/api/x.py` → True;
  **`src/api/*.py` vs `src/*/handler.py` → True and `a/*/x.py` vs `*/b/x.py`
  → True** (wildcard-vs-wildcard overlap — the case a both-ways `.match` misses);
  `**/*.py` vs `src/x.py` → True (fail-safe); **`[abc].py` vs `a.py` → True**
  (character class is a pattern, not a literal — no false `==`-disjoint).
- [x] AC3 — `wave_touches_disjoint(per_task_globs)` returns **`no` if any pair
  of *declared* globs overlaps** (even when other tasks omit `Touches:` — a
  provable overlap is always worth serializing early); `unknown` if no overlap
  is found *and* at least one task omits `Touches:` (absence blocks only a
  `yes`, never a `no`); `yes` only when every task declares and all pairs are
  disjoint.
- [x] AC4 — `loop-cohort schedule` prints `predicted-disjoint: <yes|no|unknown>`
  per multi-task wave, derived from the plan's `Touches:` lines; single-task
  waves and the exit code are unaffected.
- [x] AC5 — the prediction is **screen-only**, asserted positively (a negative
  is unprovable): `dispatch_decision`'s signature and call sites are
  **unchanged**, and the `schedule` prediction path shares **no function call**
  with the gate path (`dispatch_decision` / `wave_is_disjoint`). A test pins
  that the gate's inputs (`categories`, `merge_tree_clean`) are derived from
  `--category`/diff-classification and `wave_is_disjoint` only — never from any
  `Touches:`/glob value.
- [x] AC6 — the plan template documents the **optional** `Touches:` grammar
  (globs, comma-separated, prose-tolerant) alongside the `Depends on:` grammar;
  no existing plan is required to add it and no lint fails on its absence.
- [x] AC7 — `make build-self` leaves a clean tree and both lint surfaces pass;
  no new module, dependency, or top-level directory was introduced.

## Assumptions

- Technical: `Touches:` parsing mirrors `Depends on:` — `DEPENDS_LINE_RE` +
  `parse_plan` walking `### T` headings (source: `loop-cohort.py:125,161`);
  grammar block in the plan template (source: `assets/plan.md:67`).
- Technical: the pre-dispatch signal surfaces in `schedule` (which already
  reads the plan + computes waves); `dispatch-decision` stays diff-based
  (source: `loop-cohort.py:457` — it takes `--branch`, not task IDs).
- Technical: glob matching is stdlib (`fnmatch` / `pathlib.PurePosixPath.match`)
  — no new dependency (source: probe 2026-05-29).
- Technical: making `Touches:` mandatory would force backfilling 244 tasks
  across 23 plans, so it is **optional** (source: probe 2026-05-29 — task count;
  user confirmation 2026-05-29).
- Technical: tests land in
  `packages/agentbundle/tests/unit/test_loop_cohort_schedule.py` (source:
  parent-spec precedent).
- Technical: **screen-only, never greenlight** — declared globs serialize early
  on predicted overlap but never substitute for the authoritative post-write
  `git merge-tree`; the overlap heuristic is conservative (over-serialize is
  fail-safe) (source: user confirmation 2026-05-29 — "Option 1"). This
  **narrows the ROADMAP follow-on-3 wording** ("predicting disjointness … would
  let the gate decide up front", which implies the prediction influencing the
  decision) to a serialize-only screen — the safer reading, recorded here so the
  divergence from the roadmap direction is on the record.
- Process: rides as a spec Constrained-by RFC-0015 + ADR-0005 (refines the
  inputs to decision-3's gate; not a new architectural decision) (source: user
  confirmation 2026-05-29).
- Process: Owner = eugenelim; Draft → Shipped status set in the implementing PR
  (source: [[feedback_set_final_status_in_implementing_pr]] convention).
- Product: serves work-loop supervisor-mode users on multi-task plans; T2-live
  (real-implementer break frequency) stays out of scope (source: user
  confirmation 2026-05-29).
