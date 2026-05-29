# Plan: auto-classify supervisor-mode task conflict categories

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done <!-- Drafting | Executing | Done -->

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document is allowed to change as you learn. When it changes substantially
> (a different approach, not just a re-ordering), note why in the changelog
> at the bottom.

## Approach

The change lands entirely inside `loop-cohort.py`
(`packs/core/.apm/skills/work-loop/scripts/`) — **no new module, dependency,
or top-level dir** (ADR-0005 / spec Boundaries). Build order is bottom-up:
first the pure classifier over parsed `git diff --name-status` lines (T1,
fail-closed by construction), then wire it into the `dispatch-decision` verb
behind the "`--category` omitted" path with diff-gathering + base resolution
(T2), then the doc-of-record + clean projection + the committed yield note
(T3). The classifier is pure logic over parsed status lines, so the bulk is
TDD with soundness fixtures; the diff-gathering is exercised against real
throwaway git branches (the parent spec's AC9 dry-run shape); docs/yield are
goal-based.

## Constraints

- **RFC-0015 + ADR-0005** — the safe-category definitions; the gate
  (`dispatch_decision`) is decision-3 and stays authoritative — the classifier
  only supplies its `categories` input.
- **Parent spec (`wave-scheduled-supervisor`)** — `dispatch-decision` verb,
  `_dispatch_rationale` (AC10), `SAFE_CATEGORIES`, `wave_is_disjoint`.
- Self-host projection rule — edit `packs/core/...` source then `make
  build-self`; never edit the generated `.claude/...` copies.

## Construction tests

Most live per-task below. Cross-cutting:

**Integration tests:** none beyond per-task (the classifier is pure; the verb
auto-path is exercised by subprocess over real throwaway branches).
**Manual verification:** none — the yield pass (AC9) is a recorded read-only
script, already drafted in `.context/`.

## Tasks

### T1: fail-closed classifier + cross-branch symbol guard (AC1–AC4, AC8-unit)

**Depends on:** none

**Tests:** (`packages/agentbundle/tests/unit/test_loop_cohort_schedule.py`)
- `classify_task`: all-added (`A` only, no danger-path) → `cannot-collide`;
  **and** the reverse — a single non-`A` status, or any danger-path, flips it
  off (the AC1 iff, both directions).
- a rename (`R`), a copy (`C`), and a delete (`D`) each → `move-or-delete` (AC2).
- each danger-path → `danger-path` (AC3): `poetry.lock`, `pyproject.toml`,
  `__init__.py`, `index.ts`, `.github/workflows/ci.yml`, `Makefile`,
  `marketplace.json`, **and a nested** `a/b/migrations/0001.py` (anchoring).
- a plain modified-existing file (`M`, no danger marker) → `modified-existing`
  (AC4), **not** `cannot-collide`.
- the four non-safe labels are all outside `SAFE_CATEGORIES`; the label strings
  are pinned as contract (AC7 names them).
- `added_paths_may_share_symbol`: two branches sharing an added basename → True;
  sharing an immediate parent dir → True; fully disjoint added paths → False
  (AC8 unit, both directions).

**Approach:**
- Add `classify_task(name_status: list[tuple[str, str]]) -> str` to
  `loop-cohort.py`: precedence = rename/copy/delete → `"move-or-delete"`;
  danger-path match → `"danger-path"`; all-added → `"cannot-collide"`; else →
  `"modified-existing"`. Only `cannot-collide` ∈ `SAFE_CATEGORIES`.
- Add `_DANGER_PATH_RE`, anchored over the **full repo-relative path** (so a
  nested `migrations/` still matches): migrations / lockfiles / shared manifests
  / append-point `__init__`·`index.*`·`mod.rs`·barrel·registry / `.github/workflows`
  / `Makefile` / `marketplace.json`.
- Add `added_paths_may_share_symbol(per_branch_added: list[set[str]]) -> bool`:
  pairwise — True if any shared basename or shared immediate parent dir
  (conservative; over-serializes, never under).

**Done when:** AC1–AC4 + AC8-unit tests green, incl. the iff both-directions,
the nested danger-path, and every soundness fixture serializing.

### T2: `dispatch-decision` auto-path + base resolution + additive rationale (AC5–AC10)

**Depends on:** T1

**Tests:** (subprocess over real throwaway git branches, parent-AC9-dry-run shape)
- omit `--category`, two all-added disjoint `--branch`es → stdout `parallel`;
  stderr names categories **auto-derived** (AC5/AC7).
- omit `--category`, one branch modifies an existing file → `serial`; stderr
  names `modified-existing` (AC5/AC7).
- omit `--category`, two all-added branches sharing an added basename → `serial`;
  stderr names `cross-branch-symbol` (AC8 integration).
- unresolvable/empty base (unrelated histories, or no merge-base) → `serial`;
  stderr names the base-resolution failure (AC9).
- explicit `--category typed-group-b` overrides verbatim, echoed as
  **human-supplied** (AC6); classifier never emits `typed-group-b`.
- **parent AC10 regression:** the six existing `_dispatch_rationale` tests pass
  unchanged (AC10).

**Approach:**
- In `cmd_dispatch_decision`: if `args.category` is empty, resolve the base
  (`args.base`, else `git merge-base` of the `--branch`es; unresolvable /
  multiple / empty → fail closed to `serial` with a named reason), gather
  `git diff --name-status <base>...<branch>` per branch → `classify_task` per
  branch; then if all `cannot-collide`, apply `added_paths_may_share_symbol`
  over the added sets → downgrade to `serial`/`cross-branch-symbol` on collision.
  If `args.category` non-empty, use verbatim (override). Drop `required=True`;
  add `--base`.
- Extend `_dispatch_rationale` with a **new optional param** (e.g.
  `source="human"|"auto"`, default preserving current output) so the parent
  AC10 tests pass unchanged; name auto-vs-human and the disqualifying label.

**Done when:** AC5–AC10 tests green; `--category` override + parent AC10
regressions green; `--category` optional.

### T3: doc-of-record + clean projection + committed yield note (AC11, AC12)

**Depends on:** T1, T2

**Tests:** (goal-based)
- `make build-self` leaves a clean tree; both lint surfaces pass (`lint-packs`
  + `tools/lint-agent-artifacts.py`) — AC11.
- grep confirms no new module/dir/dependency (AC11).
- `docs/specs/supervisor-auto-classify/notes/yield.md` exists; records the
  measured `cannot-collide` rate (descriptive, no threshold) **and** names the
  irreducible shared-symbol residual as known-uncovered / post-merge-backstopped
  (AC12).

**Approach:**
- Update `work-loop/SKILL.md` §EXECUTE + `references/supervisor-mode.md`: note
  that `dispatch-decision` auto-classifies when `--category` is omitted (the
  supervisor no longer hand-classifies), `--category` is the override,
  `typed-group-b` is override-only, and the cross-branch guard exists.
  **Header/concept only — none of the six dry-run-gated worktree procedure
  surfaces** (same carve-out as parent T3/T7).
- Commit the yield-pass result + method + residual statement to `notes/yield.md`.
- `make build-self`.

**Done when:** clean tree, both lint surfaces green, yield note committed.

## Rollout

Additive and backward-compatible: `--category` keeps working (now as
override); the only contract change is `--category` becoming optional.
Reversible — restore `required=True` to revert to hand-classified categories.
No default flips to parallel: the gate still requires safe-category ∧
merge-tree disjointness, and the classifier is conservative (fail-closed).

## Risks

- **Classifier mislabels a dangerous task `cannot-collide`** → the headline
  risk the parent spec fights. Mitigated by fail-closed construction (only
  all-`A` is safe) + the soundness fixtures (T1) + the merge-tree disjointness
  half of the gate still applying.
- **Base resolution wrong** (diffing the wrong ref skews the changed-path set)
  → pin with `git merge-base` of the wave's branches + an explicit `--base`
  escape hatch; cover in T2 tests.
- **Danger-path set drifts from the repo's real shared-surface files** → keep
  it conservative (over-serialize, never under); widening needs Owner sign-off
  (spec Boundaries → Ask first).

## Changelog

- 2026-05-29: initial plan (implements ROADMAP follow-on 2 of
  `wave-scheduled-supervisor`; Constrained-by RFC-0015 + ADR-0005). Signal
  source = Option A (committed branch diff), full auto-classification with
  `typed-group-b` override-only for fail-closed soundness; ~5.4% measured
  `cannot-collide` yield recorded as decision input.
- 2026-05-29 (spec-mode review): auto-`cannot-collide` narrowed to
  file-additive ∧ file-disjoint ∧ no-danger-path — it does **not** establish
  ADR-0005's full *disjoint-no-shared-symbol* (file-level merge-tree can't see
  shared symbols). Added the **cross-branch symbol guard**
  (`added_paths_may_share_symbol`, AC8) to shrink the residual, and named the
  irreducible string-key/cross-file-symbol residual as known-uncovered /
  post-merge-backstopped (not claimed). Also: base resolution fails closed
  (AC9); `_dispatch_rationale` change is additive so parent AC10 tests pass
  unchanged (AC10); danger-path anchoring + nested fixture (AC3); label
  vocabulary lifted to contract (AC7); yield rate is descriptive (AC12).
