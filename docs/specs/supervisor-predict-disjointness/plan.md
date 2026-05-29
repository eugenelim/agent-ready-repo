# Plan: predict wave file-disjointness before dispatch

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done <!-- Drafting | Executing | Done -->

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document is allowed to change as you learn. When it changes substantially
> (a different approach, not just a re-ordering), note why in the changelog
> at the bottom.

## Approach

The change lands entirely inside `loop-cohort.py` + the `new-spec` plan
template — **no new module, dependency, or top-level dir** (ADR-0005 / spec
Boundaries). Build order is bottom-up: first parse the optional `Touches:`
line (T1, mirroring `parse_depends_on`/`parse_plan`); then the pure overlap
predictor + wave verdict (T2, conservative — over-serialize is fail-safe);
then surface the per-wave `predicted-disjoint:` annotation in `schedule`
(T3) and document the grammar + screen-only invariant (T4). All logic is pure
functions over parsed plan text + glob sets, so the bulk is TDD; the `schedule`
annotation is exercised by subprocess against a fixture plan; the doc/template
surface is goal-based. The authoritative `dispatch-decision` / `dispatch_decision`
/ `wave_is_disjoint` path is **not touched** — this feature only adds an
advisory pre-dispatch screen.

## Constraints

- **RFC-0015 + ADR-0005** — the dispatch gate (decision 3) and the read/write
  split stay authoritative; this adds an advisory input, never a greenlight.
- **Parent specs** — `wave-scheduled-supervisor` (`parse_plan`, `schedule`,
  `dispatch_decision`) and `supervisor-auto-classify` (the diff-based
  authoritative path that must stay untouched).
- Self-host projection rule — edit `packs/core/...` source then `make
  build-self`; never edit the generated `.claude/...` copies.

## Construction tests

Most live per-task below. Cross-cutting:

**Integration tests:** none beyond per-task (pure functions + one subprocess
`schedule` test).
**Manual verification:** none.

## Tasks

### T1: parse the optional `Touches:` line (AC1)

**Depends on:** none

**Tests:** (`packages/agentbundle/tests/unit/test_loop_cohort_schedule.py`)
- `parse_touches("src/api/*.py, docs/api.md")` → `{"src/api/*.py", "docs/api.md"}`.
- trailing prose tolerated (`"src/*.py (the handlers)"` → `{"src/*.py"}`), like
  `parse_depends_on`.
- `parse_touches_by_task(plan_text)` maps each `### T<n>` to its globs; a task
  with **no** `**Touches:**` line is **absent from the map** (not a key with an
  empty set), **no error** (AC1 optional).

**Approach:**
- Add `TOUCHES_LINE_RE = ^\*\*Touches:\*\*\s*(.+)$` + `parse_touches(field)` to
  `loop-cohort.py`.
- Add a **separate** `parse_touches_by_task(text)` accessor that walks the
  `### T<n>` headings (same heading regex as `parse_plan`) — **`parse_plan`'s
  2-tuple `(ordered, deps)` signature is left UNCHANGED** so the ~8 test
  call-sites and `tools/lint-plan-deps.py:39`'s 2-tuple unpack keep working
  (no call-site churn, AC7 clean tree).

**Done when:** AC1 tests green (incl. the no-line / absent-from-map case) and
`parse_plan`'s signature is unchanged (existing callers untouched).

### T2: conservative overlap predictor + wave verdict (AC2, AC3)

**Depends on:** T1

**Tests:**
- `globs_overlap` — **default-overlap-unless-provably-disjoint**, segment-wise:
  `src/a/*` vs `src/b/*` → False (literal-segment mismatch); `src/*` vs
  `src/api/x.py` → False (depth, no `**`); `src/api/*` vs `src/api/x.py` → True;
  identical → True; **`src/api/*.py` vs `src/*/handler.py` → True** and
  **`a/*/x.py` vs `*/b/x.py` → True** (wildcard-vs-wildcard overlap — must NOT
  be reported disjoint); `**/*.py` vs `src/x.py` → True (fail-safe);
  `foo/*.py` vs `bar/*.py` → False; **`[abc].py` vs `a.py` → True** (a
  character-class segment is a *pattern*, not a literal — no false `==`-disjoint).
- `wave_touches_disjoint`: a pair of **declared** globs overlaps → `"no"`
  **even if another task omits Touches** (AC3); no overlap found + some task
  absent → `"unknown"`; all declared and pairwise-disjoint → `"yes"`.

**Approach:**
- Add `globs_overlap(a, b)`: **return `True` unless provably disjoint.** If
  either contains `**` → `True`. Split both on `/`; if segment counts differ →
  `False` (provably disjoint, no `**`). Else compare aligned segments: a segment
  pair is provably disjoint iff both are pure literals that differ, or one is a
  literal the other (a pattern) can't `fnmatch`; if **any** aligned pair is
  provably disjoint → `False`, else → `True`. A segment is a **pure literal**
  iff `glob.escape(seg) == seg` (contains none of `* ? [`) — a `[...]`
  character class is a pattern, compared via `fnmatch`, never the `==`
  shortcut. Per-segment `fnmatch` keeps `*` inside a segment (never crossing `/`). Do **not** use a both-ways
  `PurePosixPath.match` as the overlap signal — a double-miss does not prove
  disjointness for two patterns.
- Add `wave_touches_disjoint(per_task_globs)` → `"yes"|"no"|"unknown"`, mining
  the declared subset for a provable `"no"` before falling back to `"unknown"`.

**Done when:** AC2/AC3 tests green, incl. the wildcard-vs-wildcard overlap
cases, the depth/`*`-no-cross-`/` case, the fail-safe `**` case, and the
overlap-despite-missing → `"no"` case.

### T3: `schedule` per-wave `predicted-disjoint:` annotation (AC4, AC5)

**Depends on:** T2

**Tests:** (subprocess against a fixture plan)
- a wave with overlapping `Touches:` → stdout line `predicted-disjoint: no`.
- an all-disjoint-`Touches:` wave → `predicted-disjoint: yes`.
- a wave with a `Touches:`-less task → `predicted-disjoint: unknown`.
- single-task waves omit the annotation; `schedule` exit code unchanged.
- **screen-only (AC5):** a unit test asserts `dispatch_decision`'s signature +
  behavior are unchanged and no `schedule`/predict code path calls into the
  dispatch gate — the prediction never produces `parallel`.

**Approach:**
- In `cmd_schedule`, for each multi-task wave compute `wave_touches_disjoint`
  over the wave's tasks' globs and print `  predicted-disjoint: <verdict>`
  under the wave line. Advisory only — no exit-code change, no gate call.

**Done when:** AC4/AC5 tests green; dispatch path provably untouched.

### T4: plan-template grammar + screen-only doc + clean projection (AC6, AC7)

**Depends on:** T1, T3

**Tests:** (goal-based)
- `make build-self` leaves a clean tree; both lint surfaces pass — AC7.
- grep confirms no new module/dir/dependency (AC7).
- the plan template documents the **optional** `Touches:` grammar; `lint-plan-deps`
  (or equivalent) does **not** fail on plans lacking `Touches:` (AC6).
- grep confirms the screen-only invariant is stated where `schedule` is
  documented (SKILL §EXECUTE / supervisor-mode header).

**Approach:**
- Document the optional `Touches:` grammar in
  `packs/core/.apm/skills/new-spec/assets/plan.md` (extending the existing
  `Depends on:` grammar block at `assets/plan.md:67-76`, not mid-block); add a
  one-line note in `work-loop/SKILL.md` §EXECUTE +
  `references/supervisor-mode.md` that `schedule`'s `predicted-disjoint:` is a
  **serialize-only screen**, never a greenlight. Header/concept only — none of
  the six dry-run-gated worktree procedure surfaces. `make build-self`.

**Done when:** clean tree, both lint surfaces green, grammar + screen-only doc
present.

## Rollout

Purely additive and backward-compatible: `Touches:` is optional (absent →
`unknown`, no behavior change); the annotation is advisory; the authoritative
dispatch gate is untouched. Reversible — removing the annotation + parser
leaves the gate exactly as today. No default flips.

## Risks

- **`Touches:` under-declares** → prediction misses a real overlap. Bounded by
  design: the screen only serializes; the post-write `git merge-tree` +
  merge-abort remain authoritative, so a miss costs an avoidable dispatch, not
  a silent break.
- **Glob-overlap heuristic is imperfect** → mitigated by the
  conservative/fail-safe rule (undecidable ⇒ predict overlap ⇒ serialize).
- **Scope creep toward greenlight** → the AC5 test + Boundaries pin the
  screen-only invariant so a future edit can't quietly let globs greenlight.

## Changelog

- 2026-05-29: initial plan (implements ROADMAP follow-on 3 of
  `wave-scheduled-supervisor`; Constrained-by RFC-0015 + ADR-0005).
  Screen-only + optional `Touches:` + conservative heuristic + surfaced in
  `schedule` (user-confirmed "Option 1", 2026-05-29).
- 2026-05-29 (spec-mode review): `parse_plan` signature kept unchanged — globs
  via a **separate** `parse_touches_by_task` accessor (avoids breaking
  `lint-plan-deps.py` + ~8 test call-sites); `globs_overlap` semantics pinned
  to segment-wise `PurePosixPath.match` (`*` no-cross-`/`); AC3 mines the
  declared subset for a `"no"` even when some tasks omit `Touches:`; AC5
  restated positively (gate signature/call-sites unchanged, predict path shares
  no call with gate path); ROADMAP "decide up front" → screen-only divergence
  recorded.
- 2026-05-29 (spec-mode review, round 2): `globs_overlap` algorithm corrected —
  **default overlap unless provably disjoint** (segment-wise), NOT both-ways
  `.match` (which falsely reports disjoint for wildcard-vs-wildcard overlaps
  like `src/api/*.py` vs `src/*/handler.py`); added wildcard-vs-wildcard
  overlap fixtures so the conservative invariant is actually tested.
