# Spec: auto-classify supervisor-mode task conflict categories

- **Status:** Shipped <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** RFC-0015, ADR-0005

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

Today the supervisor-mode dispatch gate (`loop-cohort dispatch-decision`)
takes each task's conflict category as a **required, hand-supplied**
`--category` argument — the human classifies every task by judgement before
the gate can run. This spec removes that routine judgement: the tool
**auto-derives each task's category mechanically from its committed branch
diff**, so the user does none of the per-task classification work. For the
agent running a multi-task plan, the user-visible outcomes are:

1. **No manual category for the common case.** When `--category` is omitted,
   `dispatch-decision` classifies each `--branch` from
   `git diff --name-status <base>...<branch>` and feeds the result to the
   unchanged `dispatch_decision` gate.
2. **Fail-closed classification.** A task is labelled `cannot-collide` **only**
   when every changed path is an addition (status `A`) **and** no path matches
   the danger-path set. Any rename/copy/delete, any danger-path (migrations,
   lockfiles, shared manifests, append-point `__init__`/`index.*`/`mod.rs`/
   barrel/registry, CI/build config), or any modification of an existing file
   yields a **named non-safe label** that serializes. Uncertainty ⇒ serial.
3. **A cross-branch symbol guard.** Even when every task in a wave is
   `cannot-collide`, the wave serializes if two branches' **added** files share
   a basename or an immediate parent directory — a likely symbol/registration
   collision that file-level disjointness cannot see (see *Soundness scope*).
4. **`--category` still works as a human override** (no longer required), so a
   human who knows a change is type-only can assert `typed-group-b` — which is
   *not* auto-derived.
5. **Observability.** The `dispatch-decision` stderr rationale (parent spec
   AC10) names whether each category was **auto-derived** or **human-supplied**,
   and on `serial` names the disqualifying signal.

Success: a supervisor runs `dispatch-decision --branch …` with no `--category`
and gets a correct, conservative parallel/serial decision for the whole wave;
a task touching anything risky is never auto-labelled safe; the
hand-classification step is gone for the common case.

### Soundness scope (what auto-`cannot-collide` does and does NOT establish)

ADR-0005 defines `cannot-collide` as "additive **and disjoint-no-shared-symbol**."
Auto-derivation establishes the *file-additive* and (via the gate's
`git merge-tree` half) *file-disjoint* properties, and the cross-branch guard
(outcome 3) catches the common shared-symbol vector (same basename / same new
directory). It does **not** establish full symbol-disjointness: two file-disjoint,
additive branches that collide on a **runtime key in a string literal** or a
**symbol referenced from a third file** with **no test coverage** remain a
*known-uncovered* silent-break class. That residual is **the same irreducible
class RFC-0015 §2 already names and accepts** for the parallel-write path,
backstopped by the **post-merge integrated test gate** the work-loop runs in
the primary. This spec does not claim to catch it; auto-derivation trades the
human's no-shared-symbol vouch for zero routine labor, with the post-merge gate
as the standing backstop. `typed-group-b` (human override) carries no loud
backstop in a repo with **no post-merge typecheck** (e.g. this one) — that is
the human's risk to vouch for, inherited from the parent spec, not re-litigated
here.

## Boundaries

### Always do

- **Fail closed.** Any status/path signal that is not unambiguously additive,
  any cross-branch added-file collision, and any **unresolvable/ambiguous/empty
  diff base** yield serial. Uncertainty ⇒ serial.
- **Auto-derive only when `--category` is absent.** An explicit `--category` is
  the human override and takes precedence verbatim.
- **Reuse the existing gate.** The classifier feeds the unchanged
  `dispatch_decision` (safe-category ∧ `git merge-tree` disjointness); it
  determines the *category* input only — the gate logic stays authoritative.
- **Keep `_dispatch_rationale` changes additive** — a new optional parameter
  with a default that preserves the parent spec's AC10 output verbatim.

### Ask first

- Widening the **auto-safe set** beyond `cannot-collide` (auto-deriving
  `typed-group-b` / `textual-loud`) — needs a soundness argument and Owner
  sign-off; expands the auto-green-light surface.
- Adding or **loosening** any danger-path pattern or the cross-branch guard
  (the serialize allowlist is conservative by design).

### Never do

- **Never add a new module, package, top-level directory, or runtime
  dependency** — the classifier lives inside the existing `loop-cohort.py`
  (RFC-0015: reuse). Stdlib + `git` subprocess only.
- **Never auto-derive `typed-group-b`** or any category whose safety rests on a
  semantic judgement a mechanical rule can't make fail-closed.
- **Never make `dispatch_decision`'s gate logic depend on the classifier** —
  classification supplies the category list; the gate's rule is unchanged.
- **Never claim auto-`cannot-collide` establishes symbol-disjointness**, and
  never classify from task-body free text (keyword heuristics; ~F1 0.50).

## Testing Strategy

- **`classify_task(name_status) -> label`** — **TDD**. Pure function over parsed
  `git diff --name-status` lines; compressible invariant. Construction tests in
  `plan.md`, including **soundness fixtures**: rename, copy, delete, each
  danger-path (incl. a *nested* one), and a plain modified-existing file each
  assert a non-safe (serializing) label.
- **`added_paths_may_share_symbol(per_branch_added) -> bool`** — **TDD**. Pure
  function; shared basename or shared immediate-parent-dir across branches ⇒
  True (serialize).
- **The `dispatch-decision` auto-path** (omit `--category`, pass `--branch`) —
  **TDD** via subprocess over real throwaway git branches: an all-added disjoint
  wave → `parallel`; a danger-path/modified-existing branch → `serial`; a
  same-basename all-added wave → `serial` (cross-branch guard); an
  unresolvable base → `serial`. `--category` override still precedes.
- **Parent AC10 rationale backward-compat** — **goal-based/TDD**: the parent
  spec's six `_dispatch_rationale` tests pass unchanged.
- **Yield characterisation** — **goal-based check**: a read-only pass over the
  repo's recent commits records the `cannot-collide` rate (descriptive, asserts
  no threshold) and names the known-uncovered residual; committed to `notes/`.

## Acceptance Criteria

- [x] AC1 — `classify_task` returns `cannot-collide` **iff** every changed path
  has git status `A` **and** no path is a danger-path; a regression pins the iff
  in both directions.
- [x] AC2 — any rename (`R`), copy (`C`), or delete (`D`) yields a non-safe,
  serializing label.
- [x] AC3 — any changed path matching the danger-path set yields a non-safe
  label; matching is over the **full repo-relative path** with documented
  anchoring, and a fixture asserts a danger path in a **nested** directory
  (e.g. `a/b/migrations/0001.py`) still matches.
- [x] AC4 — a modified-existing file with no danger marker yields a non-safe,
  serializing label (fail-closed default — not `cannot-collide`).
- [x] AC5 — `dispatch-decision` with `--branch` and **no** `--category`
  auto-classifies each branch (diff vs. the resolved base) and feeds
  `dispatch_decision`; all-added disjoint → `parallel`, else `serial`.
  `--category` is no longer `required`.
- [x] AC6 — an explicit `--category` overrides the classifier verbatim (incl.
  human-vouched `typed-group-b`); the classifier never emits `typed-group-b`.
  The spec records that `typed-group-b` override has no loud backstop where no
  post-merge typecheck exists (cross-ref parent).
- [x] AC7 — the stderr rationale names whether the category was **auto-derived**
  or **human-supplied**, and on `serial` names the disqualifying signal. The
  label vocabulary — `cannot-collide`, `move-or-delete`, `danger-path`,
  `modified-existing`, `cross-branch-symbol` — is **contract** (distinct,
  rationale-nameable strings), not construction detail.
- [x] AC8 — a wave whose tasks are **all** `cannot-collide` but whose added
  files share a basename or an immediate parent directory across branches
  returns `serial` (the cross-branch symbol guard); `added_paths_may_share_symbol`
  has both a positive and a negative test.
- [x] AC9 — when the diff base is **unresolvable, ambiguous (multiple
  merge-bases), or empty**, `dispatch-decision` fails closed to `serial` and the
  rationale names the base-resolution failure.
- [x] AC10 — the parent spec's `_dispatch_rationale` AC10 tests pass
  **unchanged**; the signature change is additive (new optional param, default
  preserves current output).
- [x] AC11 — `make build-self` leaves a clean tree and both lint surfaces pass;
  no new module, dependency, or top-level directory was introduced.
- [x] AC12 — a read-only yield pass over the repo's recent commits is recorded
  in `notes/yield.md`, stating the measured `cannot-collide` rate (descriptive,
  asserting no threshold/regression target) and naming the irreducible
  shared-symbol residual as known-uncovered / post-merge-backstopped.

## Assumptions

- Technical: the gate to feed is `dispatch_decision(categories, *, merge_tree_clean)`
  + the `dispatch-decision` verb (`--category` currently `required=True`);
  `SAFE_CATEGORIES = {cannot-collide, typed-group-b, textual-loud}` (source:
  `loop-cohort.py:242,245,764`).
- Technical: `git 2.50.1` supports `git diff --name-status --diff-filter` and
  `git merge-base` (source: probe 2026-05-29 — `git version 2.50.1`).
- Technical: this repo has no static typechecker; `typed-group-b` is
  adopter-conditional and never auto-admissible, one reason it stays
  override-only and its override carries no loud backstop here (source: probe
  2026-05-29 — no mypy/pyright config).
- Technical: scheduler tests land in
  `packages/agentbundle/tests/unit/test_loop_cohort_schedule.py` (source:
  parent spec precedent).
- Technical: signal source is **Option A** (committed branch diff), over Option
  B (plan-declared touched-files; couples to unbuilt follow-on 3) and Option C
  (task-text keywords; ~F1 0.50, rejected) (source: user confirmation 2026-05-29).
- Technical: **full Option A** — auto-derive for every task; `--category`
  augmented to an override; `typed-group-b` override-only; auto-`cannot-collide`
  narrowed to file-additive ∧ file-disjoint ∧ no-danger-path **plus** the
  cross-branch symbol guard, with the irreducible residual named not claimed
  (source: user confirmation 2026-05-29 + spec-mode review Blocker 1).
- Technical: measured `cannot-collide` yield over 368 recent commits ≈ 5.4%;
  the feature's value is removing 100% of routine classification labor +
  fail-closed defence, not green-light volume (source: probe 2026-05-29 —
  `.context/research-workloop-coordination/autoclassify_yield.py`).
- Process: rides as a spec Constrained-by RFC-0015 + ADR-0005 (refines *how*
  decision-3's categories are determined; not a new architectural decision)
  (source: user confirmation 2026-05-29).
- Process: Owner = eugenelim; Draft → Shipped status set in the implementing PR
  (source: [[feedback_set_final_status_in_implementing_pr]] convention).
- Product: serves work-loop supervisor-mode users on multi-task plans; T2-live
  (real-implementer break frequency) stays out of scope (source: user
  confirmation 2026-05-29; parent spec precedent).
