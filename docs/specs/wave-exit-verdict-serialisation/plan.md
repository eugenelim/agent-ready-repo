# Plan: Cohort-state identity across a transition commit

- **Spec:** [`spec.md`](spec.md)
- **Status:** Approved <!-- Drafting | Approved | Executing | Done -->
- **Repository anchors:** `docs/architecture/loop-parallelism.md` § 2 (the
  decision), `docs/architecture/loop-infrastructure.md` §§ 3, 4, 6 (current
  behaviour and the race), ADR-0061 **D3** with its 2026-09-22 erratum.
  Analogous implementations: the shipped engine-then-cohort nested hold —
  `loop-engine.py:1605` calls `apply_contract_amendment`, which takes the cohort
  lock at `loop-cohort.py:992` while `_locked` (`loop-engine.py:1166`) holds the
  engine lock (`:1522` is the same call inside the divergence-recovery branch,
  not the ordinary path) — and `_budget_snapshot` (`loop-engine.py:267-277`),
  which is how this module already reads cohort `state.json` safely. Their
  tests: `test_loop_concurrency.py` (the barriered two-process harness, the AST
  lock-hold budget at `:687-825`, `_locked_region_source` at `:687`) and
  `test_contract_amendment_wave4.py` (the only end-to-end amendment cases).
  Named uncertainty: the residuals in the spec's Assumptions, none of which this
  delivery closes; that section is the count's single home.

## Approach

Compare the whole state, not a summary of it, and read it the way this module
already reads it.

Two earlier designs asked "which cohort facts did this verdict depend on?" and
answered it per guard — first as pinned fields, then as a guard re-evaluation
over a derived set. Review killed both the same way. The pinned set missed the
unsupported-schema and absent-container rows. The derived set missed the
`run_id` preflight and the budget snapshot, neither of which is a `_GUARDS`
entry. Every version of that question has an answer that looks complete and is
not, because the cohort reads a commit consumes are not something a rule over
guard names can enumerate.

So the engine stops enumerating. It fingerprints cohort state once, before its
first cohort read, and re-fingerprints under the cohort lock before committing.
If it moved, the transition refuses. That covers the pointer, the partition, the
receipts container, the schema, the retry counters and the `run_id` — everything,
including whatever a future field adds.

The fingerprint is over the *parsed and canonicalised* state, obtained through
the guard layer's exported bounded reader, not over raw bytes from a fresh
`read_bytes()`. That is not a style preference. `_loop_guards.py:464-471`
documents the hazard at its own reader: swap `state.json` for a FIFO between the
`lstat` and the open and a raw read blocks forever, and in-process that block
sits inside the critical section until the lock is judged stale and a second
writer is admitted — the exact failure this delivery exists to prevent, made
worse than today because today no cohort lock is held at commit. The bounded
reader is non-following, non-blocking, size-capped and regular-file-only.
Canonical form over parsed content is also the better predicate: a rewrite that
changes bytes without changing content no longer false-refuses, and identical
content implies identical verdicts because every verdict is computed from the
parsed form.

`contract-amendment` is the one exclusion, for a mechanical reason: its own
effect writes cohort state, so its fingerprint always differs and the check would
refuse every amendment. That same exclusion keeps the hold from ever enclosing
`apply_contract_amendment`, which takes the cohort lock itself and would
self-deadlock on a non-reentrant lock. The cost is stated as a residual rather
than hidden: the transition that rewrites the approved baseline is the one this
delivery does not serialise.

The commit moves inside the hold as it is: a conditional, exception-guarded
`events.pending` write at `loop-engine.py:1676-1680` followed by the
unconditional engine-state write at `:1684`. It is not one unbranched sequence
and this delivery does not make it one — what it must not do is fork into a
checked and an unchecked copy, which is what AC5 pins.

`_loop_guards.py` gains no behaviour change. The lock order is already fixed: the
three `exclusive(` call sites in the scripts directory are `loop-engine.py:1193`
on the engine-state path and `loop-cohort.py:270` and `:992` on the cohort path,
so no site takes the pair in the other direction. No prose states the ordering — `loop-cohort.py:2427` pins the converse rail, not
the order — so T4 turns both into checks.

## Constraints

- ADR-0061 **D3** write clause: the engine reads cohort state, never writes it. Its read clause is already recorded as drifted by the ADR's 2026-09-22 erratum, and this read is a further instance of that drift rather than a new class.
- `_statelock`'s one budget: `timeout (10s) < maximum hold < stale_after (300s)`. **`test_lock_hold_budget` bounds neither side of what this design needs.** It derives `max_hold` as `SUBPROCESS_TIMEOUT_S × MAX_SUBPROCESS_CALLS_UNDER_LOCK` = 40 s from same-module `subprocess.<attr>` calls only, so it sees no lock acquisition at all — not this delivery's, and not the two `apply_contract_amendment` edges that already ship — and it never scans `loop-cohort.py`, whose holds this design newly relies on. T2 extends both halves (AC15, AC16).
- The new acquisition takes `_statelock`'s default timeout. The bound is the **maximum** over mutually exclusive branches, not their sum: `contract-amendment` is the only event that acquires the cohort lock via its effect and the only event exempt from the check, so at most one cohort acquisition is live on any path. 40 s + 10 s = 50 s, still under `stale_after`.
- No `pending_transition`, idempotency key, or crash-safe replay — the registered entry's *Never do*.
- The check is unconditional outside its one exemption, not gated on `auto_parallel`.

## Construction tests

T1-T4 are TDD. T3's mode is TDD exercised by an end-to-end concurrency test — it
only proves out across two real processes. T5 is goal-based.

## Durable-output map

| Semantic role | Destination | Task |
| --- | --- | --- |
| Current architecture | `docs/architecture/loop-parallelism.md` (§ 2 Decision, the Assumptions section's residuals, cost derivation, status line), `docs/architecture/loop-infrastructure.md` (§§ 3, 4, 6 and the § 10 pin) | T5 |
| Decision rationale (by citation) | `docs/architecture/loop-parallelism.md` § 2 | T5 |
| Release history and User promise | `docs/product/changelog.md`, `packs/core/pack.toml`, `packs/core/.claude-plugin/plugin.json` | T5 |
| Reusable learning | `packs/core/.apm/skills/work-loop/evals/evals.json` | T5 |

The released version is **not** pinned in this plan or in the spec. T5 derives it
from a fresh `git fetch origin` immediately before pushing, because a literal
written earlier goes stale when `main` moves and two identical literals on both
sides produce no merge conflict.

## Design (LLD)

### Design decisions

**Owned by:** T1, T2

- **D1. Whole parsed state, not a field subset.** The subset question has been answered wrongly twice — pinned fields missed two verdict rows, the derived guard set missed the `run_id` preflight and the budget snapshot. A fingerprint has no subset to get wrong.
- **D2. Through the exported bounded reader, never a raw read.** See Approach: a raw read of a non-regular `state.json` inside the hold is unbounded, and the module documents that exact hazard.
- **D3. Capture before the first cohort read.** The earliest capture is the fail-closed one: a mutation the transition's own reads did not see is caught, and so is one that landed between the capture and a read, which would otherwise commit on mixed state.
- **D4. One exclusion, mechanically forced, disclosed as a residual.** `contract-amendment` writes cohort state as its effect, so including it would refuse every amendment.
- **D5. One commit sequence.** The hold is the cohort lock or `contextlib.nullcontext()`, so the two writes stay the single sequence they already are.
- **D6. The acquisition sits outside every continuing `try`, body and handler alike.** The pending write at `loop-engine.py:1676-1680` sits in a `try` whose `except Exception` warns and falls through to the unconditional engine-state write at `:1684`. An acquisition placed in that **body** — not just in the handler — is swallowed and becomes an unlocked commit, so AC7 excludes both.
- **D7. The hold ends before outbox finalisation.** A refusal before the pending write leaves no record for a transition that never happened, which `_recover_pending` would otherwise replay; the append and unlink run after the engine-state write has already made the transition durable.

### Interfaces & contracts

**Owned by:** T2

- No published signature, return type or field changes. `_loop_guards.py` gains no behaviour change; the engine uses its already-exported bounded reader.
- New engine-internal `_cohort_fingerprint(spec_dir) -> str` — the sha256 of the canonical JSON form of cohort state, obtained through the guard layer's exported `read_state`, canonicalised with `sort_keys=True` and compact separators as `_contract_amendment_id` does at `loop-engine.py:1378-1384`, but with **`ensure_ascii=True`, deliberately unlike that precedent**. Verified on this interpreter: a `state.json` containing `"\ud800"` passes the reader's strict UTF-8 decode, parses to a lone surrogate, dumps fine under `ensure_ascii=False`, and then raises `UnicodeEncodeError` at `.encode("utf-8")` — inside the hold, escaping `_locked`'s `except sl.StateLockError` as a traceback. `ensure_ascii=True` makes the dump pure ASCII so the encode cannot fail. Do not "restore" the flag to match the amendment-id precedent.
- Its four sentinels come from an `lstat` pre-check plus an explicit exception mapping, in this order. First `os.lstat`: `FileNotFoundError` → the **absent** sentinel; not `S_ISREG` → the **non-regular** sentinel; **any other `OSError` → the other-unusable sentinel** — a permission, `ELOOP`, `ENOTDIR` or `ENAMETOOLONG` failure of the `lstat` call itself. That arm is not defensive padding: `_read_managed_bytes` converts exactly those cases to a bare `ValueError` at `_loop_guards.py:452-457`, so hoisting the `lstat` out in front of the reader *removed* coverage that already existed, and without the arm they escape the hold as a traceback past `_locked`'s `except sl.StateLockError`. Then `read_state`, with `ManagedContentError` → the **content-unusable** sentinel, and a broad catch-all → the **other-unusable** sentinel. The pre-check is load-bearing and not belt-and-braces: `ManagedContentError` subclasses `ValueError` (`_loop_guards.py:144`) and its own docstring says it is distinct from the structural failures *sharing that vocabulary*, so `_read_managed_bytes` reports a non-regular file as a **bare** `ValueError` — the same type `json.loads` raises for an integer literal over 4300 digits, which `read_managed_json` does not convert. Without the `lstat`, unreadable and malformed collapse into one value. The catch-all must be broad: a deeply nested `state.json` well under the 8 MiB cap raises `RecursionError` in both `json.loads` and `json.dumps`, and that is neither a `ValueError` nor an `OSError`. Each sentinel carries a prefix outside `[0-9a-f]`, so disjointness from the digest space is a property of the value.
- New engine-internal `_FINGERPRINT_EXEMPT_EVENTS: frozenset[str] = {"contract-amendment"}`, consulted at the Step 3 branch and asserted by T4.

### State & control flow

**Owned by:** T2

```
_locked("transition")            # engine lock, already held for the whole verb
  recover engine-state tmp / pending        (engine state only)
  read engine-state                          (engine state only)
  fp0 = _cohort_fingerprint(spec_dir)        <-- before ANY cohort read
  Step 0  run_id preflight          -> check_identity        (cohort read)
  Step 0b contract-amendment replay branch -> _schedule_check_current (cohort read),
          apply_contract_amendment (cohort WRITE), early return — never reaches Step 3
  Step 1  FSM lookup
  Step 1b plan-hash pre-guard       -> check_schedule_current (cohort read)
  Step 2  event guard                                        (cohort read)
  Step 2a contract-amendment effect, when that event         (cohort WRITE)
  Step 2b build new_state; _lifecycle_fields -> _budget_snapshot (cohort read)
  Step 3  with (cohort lock if event not exempt else nullcontext):
            if not exempt and _cohort_fingerprint(spec_dir) != fp0: refuse
            write events.pending
            write engine-state.json (atomic)
  Step 4  append events.jsonl, unlink pending   # outside the hold
```

Four cohort reads sit between the capture and the commit, and the fingerprint
dominates all of them. AC1 does **not** try to recover that set: guard dispatch
goes through `_GUARDS.get(...)` and the `_guards()` calls are attribute calls on
a module loaded at runtime, so no static walk can decide it — `test_loop_concurrency.py`
records that verdict in its own words. AC1 instead pins a positional property the
AST can falsify: the capture precedes every statement in `cmd_transition`'s body
except the crash-recovery helpers and the engine-state read. A fifth cohort read
added anywhere after it is therefore dominated whether or not anything can name it.

### Failure, edge cases & resilience

**Owned by:** T2

- Unusable cohort lock path, acquisition timeout, or any other acquisition `OSError` surfacing as the base `StateLockError`: refuse via `stop()`, one line, nothing written. AC10 requires the message to name the cohort lock so it is distinguishable from the engine-lock failure the same handler renders.
- `state.json` absent at one point and present at the other, unreadable at either, or malformed at either: the four sentinels are mutually distinct and disjoint from the digest space, so a transition whose two samples land in different failure classes refuses; two samples in the same class compare equal, which residual six discloses.
- `state.json` not a regular file: the bounded reader rejects it without blocking, and the sentinel refuses. This is the case a raw read would hang on.
- `StateLockLost` at the end of the hold: `exclusive` raises only after the body, so the engine-state write has already landed and the outbox finalisation is skipped, leaving an `events.pending` that `_recover_pending` finishes on the next run. The verb exits non-zero. AC13 pins the reporting half.
- An unavailable lock *module* cannot occur here: `_locked` resolved and memoised it before `cmd_transition` ran. It is deliberately absent from AC8.
- `contract-amendment` keeps today's behaviour exactly, on both its normal path and its replay-recovery early return.

### Quality attributes (NFRs)

**Owned by:** T2, T5

One acquire-release plus one extra bounded cohort read per checked transition.
`loop-parallelism.md` § 2's published ratio divides an acquire-release into a
738.6 ms transition median whose stated basis is "three `git rev-parse
--show-toplevel` calls per transition"; `_get_repo_root` now memoises per working
directory, so that basis no longer describes HEAD. T5 records the measured
acquire-release cost and the method used to obtain it, and states a ratio only if
the transition baseline is re-derived on this tree — never by dividing into the
stored figure.

### Dependencies & integration

**Owned by:** T2

No new dependency. `loop-engine.py` already imports `contextlib` (line 31) and
`hashlib` (line 33), and already loads `_statelock` and `_loop_guards` by path.

## Tasks

### T1: The fingerprint is total, distinguishing, and safely read

**Depends on:** none

**Touches:** packs/core/.apm/skills/work-loop/scripts/loop-engine.py, packs/core/tests/skills/work-loop/test_loop_engine.py

**Tests:**
- AC19: the fingerprint is obtained through the guard layer's exported bounded reader, and a `state.json` that is a FIFO yields a refusal sentinel promptly rather than blocking. The FIFO case is the one that distinguishes this from a raw read; a test that omits it proves nothing about the hazard.
- AC20: the four classes — absent, non-regular, content-unusable and other-unusable — yield four mutually distinct sentinels, each outside the space a sha256 hex digest occupies, so no two *different* failure classes and no failure-and-success pair compare equal. (Two observations of the *same* class do compare equal; that is residual six, not a defect in this criterion.)
- AC21: the fingerprint is total over any outcome of the `lstat` pre-check *and* read-and-canonicalise, not only the four named classes — including a case that makes the `lstat` call itself raise, such as a path whose parent component is a regular file (`ENOTDIR`), which none of the other listed cases reaches — cases cover a lone-surrogate string and an integer literal over 4300 digits, both of which the bounded reader accepts or fails in ways its own handlers do not convert.
- Stability and sensitivity: identical content yields an identical fingerprint across calls; changed content yields a different one; content identical but byte-different (key order, whitespace) yields the same one.

  ```python
  # stub: true — red contract surface for T1
  def test_cohort_fingerprint_is_total_and_never_blocks(tmp: Path) -> None:
      """A raw read here would hang the lock-holding process on a FIFO."""
      eng = load_engine()
      spec_dir = tmp / "spec"; spec_dir.mkdir()
      absent = eng._cohort_fingerprint(spec_dir)
      (spec_dir / "state.json").write_text('{"a": 1, "b": 2}', encoding="utf-8")
      present = eng._cohort_fingerprint(spec_dir)
      (spec_dir / "state.json").write_text('{"b":2,"a":1}', encoding="utf-8")
      assert eng._cohort_fingerprint(spec_dir) == present   # canonical, not bytes
      (spec_dir / "state.json").write_text("not json", encoding="utf-8")
      malformed = eng._cohort_fingerprint(spec_dir)
      assert len({absent, present, malformed}) == 3
      os.unlink(spec_dir / "state.json"); os.mkfifo(spec_dir / "state.json")
      nonregular = eng._cohort_fingerprint(spec_dir)
      # Distinct from MALFORMED, not merely from a successful digest. Both reach
      # the reader as bare ValueError, so only the lstat pre-check separates them;
      # a `except ValueError` arm alone collapses this assertion to three values.
      assert len({absent, present, malformed, nonregular}) == 4
  ```

**Approach:**
- Give each sentinel a prefix outside `[0-9a-f]`, so disjointness from the digest space is a property of the value rather than an authoring intention.

**Done when:** AC19, AC20 and AC21 are each asserted green, the stability-and-sensitivity group passes, and the FIFO case returns within the test's own timeout.

### T2: A transition refuses when cohort state moved under it

**Depends on:** T1

**Touches:** packs/core/.apm/skills/work-loop/scripts/loop-engine.py, packs/core/tests/skills/work-loop/test_loop_engine.py, packs/core/tests/skills/work-loop/test_loop_concurrency.py, packs/core/tests/skills/work-loop/test_contract_amendment_wave4.py

**Tests:**
- AC2: the transition refuses when the fingerprint moved and proceeds when it did not.
- AC9 and AC10 at the CLI surface: the mismatch refusal is one stderr line carrying `loop-engine: stop — ` (`loop-engine.py:1115`) naming both fingerprints and no other cohort value; the contention refusal is one line naming the cohort lock. Split cases, so a failure says which refusal broke.
- AC8: unusable lock path, acquisition timeout, and a base `StateLockError` each exit non-zero with `engine-state.json` unchanged and no `events.pending`.
- AC13: a reclaim detected at the end of the hold exits non-zero.
- AC14: a `contract-amendment` transition completes end-to-end under the new commit shape and takes no engine-side cohort lock. This is the exemption's only verification, and it lives in `test_contract_amendment_wave4.py` — `test_loop_engine.py` carries no amendment transition case.
- AC1, AC3, AC5, AC6, AC7: static assertions at the `_locked_region_source` seam — the capture's only permitted predecessors in `cmd_transition`'s body are the crash-recovery helpers and the engine-state read; the exemption is read from the declared set at the branch rather than compared to a literal; one `_write_events_pending` and one `_write_engine_state_atomic` call; the hold's contents and exclusions; the acquisition outside any continuing handler.
- AC22: the engine-side cohort hold's own maximum is derived as a number and satisfies the inequality — this is the only hold the delivery creates, and AC6's exclusion list cannot bound it.
- AC15 and AC16: the engine-side derivation declares its acquisition set, that declaration equals the set recovered by matching an engine-side cohort-path acquisition and a `_cohort_mutator().<fn>(` site whose target reaches a hold by any of AC17's three shapes, the bound takes the maximum over mutually exclusive branches, and the same inequality is asserted for `loop-cohort.py`'s own holders.
- Regression: the existing wave-complete cases (`test_loop_engine.py:1612`, `:4027`, `:4055`) stay green.

  ```python
  # stub: true — red contract surface for T2
  def test_transition_refuses_when_cohort_state_moved(tmp: Path) -> None:
      """AC2: the fingerprint taken before the first cohort read must still hold."""
      spec_dir = make_scheduled_run(tmp)
      rc, _, err = run_engine_with_mutation_before_commit(
          spec_dir, "wave-complete", mutate=lambda: advance_wave(spec_dir))
      assert rc != 0
      assert err.startswith("loop-engine: stop — ") and err.count("\n") == 1
      assert not events_pending_path(spec_dir).exists()
  ```

**Approach:**
- `test_loop_concurrency.py` is in `Touches:` because AC1, AC3 and AC5-AC7 and both budget criteria assert at seams defined there, which also makes T2's overlap with T3 and T4 visible to the scheduler's disjointness prediction.

**Done when:** the stub is green, AC1, AC3, AC5-AC10, AC13-AC16 and AC22 are asserted, and `python3 -m pytest packs/core/tests/skills/work-loop/test_loop_engine.py packs/core/tests/skills/work-loop/test_contract_amendment_wave4.py packs/core/tests/skills/work-loop/test_loop_concurrency.py -q` passes — the third suite included because seven of T2's criteria assert at seams defined there, and omitting it lets T2 be declared done with them never executed.

### T3: Two real processes prove each racing mutator, and the lock itself

**Depends on:** T2

**Touches:** packs/core/tests/skills/work-loop/test_loop_concurrency.py

**Tests:**
- AC11 and AC12: the five (event, mutator) pairs the spec enumerates, each driven by two real CLI processes through a rendezvous the test controls. `gates-clean` pairs with `schedule` rather than `wave advance`, because `wave advance` refuses from the final wave (`loop-cohort.py:1682`) while `gates-clean` passes only on the final wave, so no advance can commit in that window. Each case: engine exits non-zero, `engine-state.json` byte-identical, no `events.pending`.
- AC12's second half: each case fails when the fingerprint comparison is removed from the source. This is the criterion's own mutation requirement, not just delivery evidence.
- AC4: mutual exclusion observed directly — a peer holds `state.json.lock`, the transition starts, and `engine-state.json` is unchanged while the peer still holds it. Observing it *during* the hold rather than after a full `DEFAULT_TIMEOUT` both runs faster and is the stronger assertion; without it, a lock taken on the wrong path passes every ordering case above.

**Approach:**
- `_run_barriered(n, target, argvs, cwd)` passes one target module to every child and `_child_path` writes `_barriered_child.py` only when absent. These cases need two different verbs and their own child source, so add a sibling launcher taking a per-child target and an explicit child source, and leave `_run_barriered` and its four existing callers untouched.
- The new child wraps `_cohort_fingerprint` to signal after the capture and wait for the mutator's commit. That is a better rendezvous point than a guard: one function, called once, on every checked path.
- If real overlap cannot be constructed for a pair, say so plainly rather than shipping a sequential test that looks like one.

**Done when:** `python3 -m pytest packs/core/tests/skills/work-loop/test_loop_concurrency.py -q` passes, AC12's removal-mutation shows every case red, and a wrong-path lock edit shows AC4 red.

### T4: The exemption and both lock rails are checked, not asserted

**Depends on:** T2

**Touches:** packs/core/tests/skills/work-loop/test_loop_concurrency.py

**Tests:**
- AC3's set half: `_FINGERPRINT_EXEMPT_EVENTS == {"contract-amendment"}`, with the assertion naming why — the only event whose own effect writes cohort state.
- AC17: every path in `loop-cohort.py` that writes or unlinks cohort `state.json` executes inside a cohort-lock hold. This is the premise the whole mechanism rests on and nothing pins it today; AC18 pins only the converse direction. The check must resolve all three hold shapes: the `@_locked` decorator, the inline `with sl.exclusive` in `apply_contract_amendment` (`loop-cohort.py:992`), and the body callable passed to `with_state_lock` — which is the only route holding `_schedule_run_impl`'s write at `loop-cohort.py:1565`, reached through the lambda at `:1598-1602`. Discharging a failing site by allowlisting it is forbidden: that is the shape that blinds the check to the exact path it was written for.
- AC18: `loop-cohort.py` acquires no lock on an engine-state path and reads no engine-state file, modelled on the AST import-allowlist case in `test_loop_guards.py:328-347`.
- Each assertion fails when a probe edit breaks its property.

**Approach:**
- The lock-order property holds today but nothing states it: `loop-cohort.py:2427` says "this module never reads `engine-state.json`", which is AC18's rail, not the ordering. The ordering rests only on the three `exclusive(` call sites happening to lock one path each, and the nested hold's deadlock argument depends on it.

**Done when:** all three assertions are green and each reddens under its probe edit.

### T5: The record matches what shipped

**Depends on:** T3, T4

**Touches:** docs/architecture/loop-parallelism.md, docs/architecture/loop-infrastructure.md, docs/product/changelog.md, packs/core/pack.toml, packs/core/.claude-plugin/plugin.json, packs/core/.apm/skills/work-loop/evals/evals.json, .claude/, .agents/

**Tests:**
- Goal-based: `make build-self` three-copy parity check clean; `python3 -m pytest packs/core/tests/pack -q` green; `lint-spec-status.py --root .` clean.
- Goal-based: `packs/core/pack.toml`, `packs/core/.claude-plugin/plugin.json` and the topmost `## [core][<version>]` heading in `docs/product/changelog.md` all carry the same version, free-standing directly beneath `## [Unreleased]`.

**Approach:**
- Rewrite § 2's **Decision paragraph**. It currently reads "the `wave-complete` guard returns the `current_wave_index` it judged" — one verb, one field, a returned value. What ships is a whole-state fingerprint comparison at commit across every event but one, with no guard change at all.
- `loop-parallelism.md:3` reads "**STATUS: PLANNED.** Nothing here is implemented." That is document-level, becomes false once § 2 ships, and cannot be scoped to a section as written. Replace it with a per-section line: § 2 implemented, §§ 1 and 3 planned.
- § 2 also gains every residual from the spec's Assumptions, the ADR-0061 erratum citation for D3's read clause, and the cost derivation.
- `loop-infrastructure.md` §§ 3, 4 and 6 describe the serialised commit; § 10's "Last verified against commit" pin moves off `8d30c6f6c`.
- The changelog entry names **both** new refusals.
- Derive the version from `git fetch origin` immediately before pushing.

**Done when:** the three version surfaces agree, `make build-self` reports three-copy parity, the pack suite is green, **and every closeout condition in the spec's Durable Outputs table is met** — § 2 carries the rewritten Decision paragraph, every residual from the spec's Assumptions, the per-section status line, the ADR-0061 erratum citation, the cost derivation and the two non-retryable lock classes; `loop-infrastructure.md` §§ 3, 4 and 6 describe the serialised commit and § 10's pin has moved off `8d30c6f6c`; the changelog entry names both new refusals; and the evals entry exists. A version check alone cannot fail when the record is incomplete.

## Rollout

Pure-logic change to a CLI shipped inside a pack. No flag, no infrastructure, no
migration, no deployment sequencing. Reversible by reverting the commit; nothing
durable is written that an older build cannot read.

Two user-visible outcomes are new, and the changelog names both. A transition can
refuse because cohort state changed under it, and it can refuse on cohort-lock
contention. Both are self-describing — AC9 and AC10 require each to say which
condition fired — and the recovery for both is to retry once the competing verb
finishes, so neither needs an operator procedure.

## Risks

- **A refusal that fires when it should not.** Accepted and stated as a residual: any concurrent cohort write in the window refuses, including a benign one. Fail-closed, retryable, unreachable in a sequential run. The alternative is a field subset, which review showed cannot be enumerated correctly.
- **An unbounded read inside the hold.** The reason D2 mandates the bounded reader, and the reason T1's FIFO case exists. A raw read here is strictly worse than shipping nothing.
- **A hold that outgrows the lock budget.** The existing `test_lock_hold_budget` sees no acquisition at all and never scans `loop-cohort.py`. AC15 and AC16 close both halves.
- **A lock taken on the wrong path.** Every ordering test would still pass, which is why AC4 observes mutual exclusion directly and T3 includes a wrong-path probe edit.
- **A test that looks concurrent and is not.** The named risk of T3, and the reason AC12 carries its own removal-mutation requirement rather than leaving it to delivery evidence.
- **The exempt transition.** `contract-amendment` is not serialised, and it is the transition that rewrites the approved baseline. Disclosed as a residual, not closed.

## Changelog

- 2026-09-22: spec approved by eugenelim
- 2026-09-22: plan approved by eugenelim
