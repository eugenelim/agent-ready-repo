# Spec: Cohort-state identity across a transition commit

- **Status:** Implementing <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** ADR-0061
- **Brief:** none
- **Discovery:** none
- **Contract:** none
- **Shape:** service

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.
>
> **Not every section is contract.** `Agent Rules`, `Testing Strategy` and
> `Acceptance Criteria` are what a completion gate reads, and an amendment
> changes them. `Outcome`, `What Changes`, `Durable Outputs`, `Follow-ons` and
> `Assumptions` are working material: they orient a reader and an author corrects them in place
> as the work teaches, without an amendment and without a review round. A review
> finding against working material is advisory — it cannot block, because nothing
> gates the text it cites. Marking the tiers is the spec's job; honouring them
> when a finding is adjudicated is the reviewing surface's.

## Outcome

A controller driving the loop gets a transition that commits only against the
cohort state its own reads saw. Success is that a concurrent cohort mutation can
no longer slip between a transition's decisions and its commit.

## What Changes

- `cmd_transition` records a fingerprint of cohort state before its first cohort read, re-reads it under the cohort lock, and refuses when it moved — `packs/core/.apm/skills/work-loop/scripts/loop-engine.py`.
- The commit moves inside that hold: a conditional, exception-guarded `events.pending` write followed by an unconditional engine-state write, kept as the one commit path rather than duplicated into a checked and an unchecked arm — same file.
- The lock-hold budget derivation covers cohort-lock acquisitions and the cohort lock's own holders, neither of which it reaches today — `packs/core/tests/skills/work-loop/test_loop_concurrency.py`.
- A rendezvous-forced two-process regression covers each racing mutator — same file.
- `loop-parallelism.md` § 2 records the shipped mechanism, its residuals and its cost derivation, and the document's status line becomes per-section; `loop-infrastructure.md` §§ 3, 4 and 6 describe the serialised commit and § 10's pin moves.

Nothing in `_loop_guards.py` changes. No guard signature, return type, field or
verdict-row behaviour moves.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| Current architecture | Applicable — `loop-parallelism.md` § 2 states this decision as PLANNED and describes a narrower mechanism than ships; `loop-infrastructure.md` § 6 states the race as live | `docs/architecture/loop-parallelism.md`, `docs/architecture/loop-infrastructure.md` | this spec's implementer | § 2's Decision paragraph describes a whole-state fingerprint check at commit rather than one verb returning one field; § 2 also carries every residual the Assumptions section lists, and the cost derivation; § 6 describes the serialised commit; § 10's pin names the shipping commit | neither document describes a mechanism narrower than what shipped, and every residual in this spec's Assumptions appears in § 2 |
| Decision rationale | Applicable, and discharged by citation rather than a new record — ADR-0061 **D3** has two clauses, and the locked read engages the *read-channel* clause, not the write clause. That clause is already recorded as drifted by the ADR's 2026-09-22 erratum, which notes the guard layer reads `state.json` directly through `_loop_guards.read_state` and expressly leaves re-align-or-supersede undecided. This read is a further instance of that recorded drift, not a new class | `docs/architecture/loop-parallelism.md` § 2 | this spec's implementer | § 2 cites the erratum where it states the engine's cohort read | the citation resolves and names the read clause |
| Release history and User promise | Applicable — the `core` pack ships these scripts, and two refusals are newly reachable: a cohort-state-moved refusal and a cohort-lock contention refusal | `docs/product/changelog.md`, with the version derived at T5 per the plan | this spec's implementer | a `## [core][<version>] — <date>` heading free-standing directly beneath `## [Unreleased]`, agreeing with `packs/core/pack.toml` and `packs/core/.claude-plugin/plugin.json`, and naming **both** new refusals | three version surfaces agree at one patch above a freshly fetched merge-base, and the entry names both refusals |
| Interface compatibility | Not applicable — no published signature, return type or field changes, and `_loop_guards.py` is untouched | — | — | — | — |
| Reusable learning | Applicable — a non-cosmetic `core` pack update | `packs/core/.apm/skills/work-loop/evals/evals.json` | this spec's implementer | a contract-record entry; nothing executes it | the entry exists and is honest |
| Maintainer procedure | Applicable — most of the new refusals clear on retry, but two lock classes never do: a non-regular `state.json.lock`, and a lock record this tool did not write, which is never reclaimed however old it is. Both need the file removed by hand, and after this change they wedge every non-exempt engine transition rather than cohort verbs alone | `docs/architecture/loop-parallelism.md` § 2 | this spec's implementer | § 2 names the two non-retryable classes and the manual removal that clears them | a reader hitting either refusal can tell it from a contention refusal and knows the remedy |

## Agent Rules

The three-tier guard that keeps an implementing agent inside the lines.
*Always do* applies without asking; *Ask first* requires human sign-off
before proceeding; *Never do* is a hard rule, even under time pressure.

### Always do

- **The bounded-reader rail, stated once here and referenced elsewhere:** read cohort state only through the guard layer's exported bounded readers. `_budget_snapshot` (`loop-engine.py:276`) already reads this same file that way, through the engine's `_read_managed_json` wrapper rather than through `read_state` — either entry point carries the discipline; what matters is that neither is a raw read. A raw read inside the hold is the hazard `_loop_guards.py` documents at its own reader — a non-regular `state.json` blocks the lock-holding process until both locks are judged stale, admitting the second writer this delivery exists to exclude.
- Fingerprint the whole parsed state, not a field subset. Two earlier designs picked subsets and both missed cohort inputs their authors had not enumerated.
- Capture before the transition's first cohort read, so the fingerprint covers every cohort verdict the commit consumes — including the `run_id` preflight and the budget snapshot, neither of which is a `_GUARDS` entry.
- Take the engine lock before the cohort lock, the order `_locked` and `apply_contract_amendment` already establish.
- Bound every operation inside the cohort-lock hold to a local file read or write.
- Place the acquisition where no enclosing handler can continue past its failure.
- Edit `packs/core/.apm/`; treat `.claude/` and `.agents/` as projections and regenerate them with `make build-self`.

### Ask first

- Excluding any event other than `contract-amendment` from the check.
- Any change to the `auto_parallel` flag's meaning.
- Narrowing the check from the whole parsed state to a field subset.

### Never do

- Modify `_loop_guards.py`. The bounded-reader rail above is satisfied entirely through its existing exports, so this delivery needs no edit there at all.
- Write cohort *state* from the engine. ADR-0061 **D3**'s write clause permits only a read. Note this delivery does make the engine a writer in the cohort *directory* for the first time: `exclusive()` creates and unlinks the `state.json.lock` sibling. D3 governs state content, not the directory, and the shipped records say so rather than leaving the engine described as a pure reader there.
- Introduce `pending_transition`, an idempotency key, or crash-safe replay.
- Hold the cohort lock across the FSM table lookup, the plan-hash pre-guard, any guard evaluation, `apply_contract_amendment`, or outbox finalisation.

## Testing Strategy

- **The serialisation itself (AC2, AC11, AC12): TDD, exercised by an end-to-end concurrency test.** It only proves out across two real operating-system processes contending on real lock files, so each case drives one engine transition and one `loop-cohort` mutator concurrently through a rendezvous that forces capture → mutation-commit → engine-commit. A sequential call of the two paths proves nothing about the race and does not satisfy these. Artifact: `packs/core/tests/skills/work-loop/test_loop_concurrency.py`.
- **Mutual exclusion (AC4): TDD, exercised by an integration test.** A wrong or absent lock target passes every ordering case above, so this one observes the exclusion directly, while a peer holds the lock. Artifact: `test_loop_concurrency.py`.
- **Capture point, exemption wiring and structural placement (AC1, AC3, AC5, AC6, AC7): goal-based check, by static assertion** over `cmd_transition`'s AST, at the existing `_locked_region_source` seam. Artifact: `test_loop_concurrency.py`.
- **The bounded reader, the fingerprint's domain and its totality (AC19, AC20, AC21): TDD, unit.** Artifact: `packs/core/tests/skills/work-loop/test_loop_engine.py`.
- **Lock-failure behaviour (AC8, AC13): TDD, unit plus one representative engine-level case.** `_statelock`'s own delivery owns per-class lock behaviour; what this spec owns is that each class reaches a refusal on this path. Artifact: `test_loop_engine.py`.
- **Refusal wording and channel (AC9, AC10): TDD, exercised at the CLI surface.** The line a caller sees is emitted by `stop()`, so both assertions run against real process stderr. Artifact: `test_loop_engine.py`.
- **`contract-amendment` under the new commit shape (AC14): TDD, exercised end-to-end.** Artifact: `packs/core/tests/skills/work-loop/test_contract_amendment_wave4.py`.
- **The three budget derivations and the two lock rails (AC15, AC16, AC17, AC18, AC22): goal-based check, by AST assertion**, modelled on the existing import-allowlist case. Artifact: `test_loop_concurrency.py`.

## Acceptance Criteria

- [x] AC1: In `cmd_transition`'s body the fingerprint capture precedes every statement except the crash-recovery helpers and the engine-state read, so no later-added cohort read can precede it; asserted positionally, because the guard dispatch and the `_guards()` calls are indirect through a runtime-loaded module and no call-graph walk can decide the read set.
- [x] AC2: Before committing, the engine re-reads cohort state while holding the cohort lock and refuses when the fingerprint differs from the captured one.
- [x] AC3: `cmd_transition` decides the exemption by consulting a single declared set whose only member is `contract-amendment`, so neither a hard-coded event literal at the branch nor a second member passes.
- [x] AC4: While a peer process holds `state.json.lock`, a checked transition does not write `engine-state.json`.
- [x] AC5: The `events.pending` write and the `engine-state.json` write each appear exactly once in `cmd_transition`, so no second commit path can drift from the checked one.
- [x] AC6: The cohort-lock hold contains the re-read and both writes, and contains none of the FSM table lookup, the plan-hash pre-guard, any guard evaluation, `apply_contract_amendment`, or the outbox append and unlink — asserted against the module's AST.
- [x] AC7: The cohort-lock acquisition is lexically outside both the handler and the guarded body of every `try` whose handler continues after catching, so an acquisition failure cannot be swallowed and fall through to the unconditional engine-state write.
- [x] AC8: Every `StateLockError` class the acquisition can raise — the unusable lock path, the acquisition timeout, and the base class raised for any other acquisition `OSError` — exits non-zero, leaves `engine-state.json` unchanged, and leaves no `events.pending`.
- [x] AC9: The fingerprint-mismatch refusal reaches stderr as one line carrying the process's own `loop-engine: stop — ` prefix, names both fingerprints, and interpolates no other cohort-derived value.
- [x] AC10: The cohort-lock contention refusal reaches stderr as one line and names the cohort lock as the contended resource, so a reader can tell it from an engine-lock failure.
- [x] AC11: For each pair below, the transition is refused when the mutator commits between the fingerprint capture and the commit, `engine-state.json` is byte-identical to its pre-transition content, and no `events.pending` remains: `wave-complete` with `wave advance`; `wave-complete` with `schedule` leaving `current_wave_index` at the value the guard read; `wave-complete` with `schedule` creating a previously absent receipts container; `wave-complete` with `reset` then `init` then `schedule` changing the cohort `run_id` while every guard verdict still approves; `gates-clean` with `schedule`.
- [x] AC12: Each case in AC11 is driven by two real CLI processes whose interleaving is forced by a rendezvous the test controls, not by scheduling, and each case fails when the fingerprint comparison is removed from the source.
- [x] AC13: A cohort-lock reclaim detected at the end of the hold exits non-zero.
- [x] AC14: A `contract-amendment` transition completes end-to-end under the new commit shape, taking no engine-side cohort lock.
- [x] AC15: The derived maximum engine-lock hold counts each cohort-lock acquisition reachable from `cmd_transition`, taking the maximum over mutually exclusive branches rather than their sum, and the inequality `timeout < maximum hold < stale_after` holds. Membership is decided without naming any function. On the engine side, an acquisition counts only when it locks a cohort path inside the region the budget covers, so the outer engine-state acquisition in `_locked` is not counted as a nested one. On the cohort side, every `_cohort_mutator().<fn>(` site is recovered syntactically and `<fn>` counts as acquiring when its definition in `loop-cohort.py` reaches a hold by any of the three shapes AC17 enumerates — a literal `exclusive` call, a `with_state_lock(...)` call, or the `@_locked` decorator. Recognising only the literal call would miss the majority shape, since `loop-cohort.py` has just two `exclusive` sites while seven verbs acquire through the decorator.
- [x] AC16: The cohort lock's own holders in `loop-cohort.py` — whose bound this design newly depends on and which no budget check reaches today — have a derived maximum below `stale_after`, so a live holder is never judged dead while the engine waits on it. The derivation names where each holder's bound comes from; those holders spawn nothing under the lock, so a subprocess-only formula would report zero and must not be reused unexamined.
- [x] AC17: Every code path in `loop-cohort.py` that writes or unlinks cohort `state.json` executes inside a cohort-lock hold, asserted by a static check that resolves all three shapes a hold takes there — the `@_locked` decorator, the inline `with sl.exclusive` in `apply_contract_amendment`, and the body callable passed to `with_state_lock`, which is how `_schedule_run_impl`'s write is held. The check is not discharged by exempting a write site.
- [x] AC18: `loop-cohort.py` acquires no lock on an engine-state path and reads no engine-state file, asserted by a static check.
- [x] AC19: The engine obtains cohort state for the fingerprint through the guard layer's exported bounded reader, and a `state.json` that is not a regular file reaches a refusal rather than a blocking read.
- [x] AC20: The fingerprint yields four mutually distinct failure values — absent, not-a-regular-file, content-unusable, and other-unusable — each outside the space a content fingerprint can produce. The not-a-regular-file value comes from the engine's own `lstat` check before the read, because the guard layer's reader reports non-regular files and unconvertible parse failures with the same bare `ValueError`, so exception type alone cannot separate them.
- [x] AC21: The fingerprint is total over *any* outcome of the read-and-canonicalise step, not only over the four classes AC20 names, and covering the `lstat` pre-check as well as the read: no input reaching it can raise out of the cohort-lock hold. In particular: the canonicalisation is chosen so its encode step cannot fail on content the bounded reader accepts; a parse failure the reader does not convert still reaches a sentinel; and every outcome of the `lstat` pre-check other than a missing file and a non-regular mode — a permission, loop, not-a-directory or name-too-long error — reaches a sentinel too, because hoisting that `lstat` out of the reader removed the conversion the reader applied to exactly those cases.
- [x] AC22: The engine-side cohort-lock hold — the only hold this delivery creates — has a derived maximum, stated as a number with its origin, that is **below** `_statelock`'s acquisition timeout, so a contending cohort verb never times out against it, and therefore far below `stale_after`. The `timeout < maximum hold` half of the engine lock's inequality does not apply here and is deliberately not carried over: it exists so contenders do not abandon a live holder of the outer lock, whereas this hold must be short, and it contains no subprocess for the repository's existing derivation to measure.

## Follow-ons

- Retiring this spec's `workspace.toml` `[backlog].open` entry is a separate `chore(workspace):` commit after the fix lands, not a task in this plan.
- **`gates-clean` does not check dispatch receipts at all.** A wave entered after a legitimate `wave-complete` can still be exited without its receipts being read, because `gates-clean` asks only whether the current wave is the last. That is a missing check rather than a lost race — no interleaving is involved and serialisation cannot close it — so it is untouched here. Retiring the registered entry asserts that a transition can no longer commit against cohort state its own reads did not see; it does not assert that every wave exit reads receipts.
- Defect A (`_loop_guards.py`, repair-round dispatch assertion) and defect D (`0061-loop-infrastructure-phase-1.md`, durable trace on an unenforced wave exit) stay open; neither is closed or narrowed here.
- `loop-parallelism.md` § 1 (durable transitions) and § 3 (plan width) stay unimplemented; both need governance records that do not exist.

## Assumptions

Eight residuals, all of which the shipped `loop-parallelism.md` § 2 must name.

- The check refuses on *any* concurrent cohort write in the window, including a benign `dispatch-receipt` that would only have made a verdict more true. Deliberate: fail-closed, retryable, unreachable in a sequential single-controller run, and the alternative is a field subset review showed cannot be enumerated correctly.
- **`contract-amendment` is exempt, so its own decision-to-commit window stays open.** Its replay-status check and plan-hash pre-guard run unlocked, and its effect then commits on state read fresh under its own lock. The exemption is mechanically forced — its effect writes cohort state, so its fingerprint always differs — but it means the transition that rewrites the approved baseline is the one transition this delivery does not serialise.
- **The hold serialises cohort `state.json` only.** Every other guard input in and under the spec directory — `spec.md` and `plan.md` status and hashes, any artifact `check_artifact_status` stats, the bundled retry-cap defaults — stays exactly as unserialised as today. The shipped records must not describe the hold as making a whole verdict current.
- **The check is endpoint identity, not interval quiescence.** It compares two samples, so a write-and-revert inside the window would leave a guard having judged an intermediate state while the commit proceeds. No shipped cohort verb appears able to produce that reversion, which is why it is disclosed rather than closed — but the record must not describe the window as quiet.
- **Two cohort-lock failure classes are not retryable.** A non-regular `state.json.lock` raises `StateLockUnusable` immediately, and a lock record this tool did not write is never reclaimed however old it is. Both need manual removal, and after this change they block every non-exempt engine transition rather than only cohort verbs. The realistic trigger is a foreign or other-uid lock file, not an attacker.
- **Any failure sentinel observed at both samples compares equal and admits the commit.** The check is `fp0 != fp1`, so sentinel separation prevents a *cross-class* collision and does nothing about a *same-class* one: absent at capture and absent again at the re-read compares equal, as does non-regular twice, content-unusable twice, or two different `other-unusable` causes. The shipped record must not describe the four sentinels as closing this. Reaching it needs a foreign writer to break, heal and re-break `state.json` inside one transition, because at least one intermediate guard read must genuinely succeed for the commit to be reached — and that load rests entirely on the `run_id` preflight's `check_identity`, since `_budget_snapshot` swallows every exception and carries none of it. No shipped cohort verb can produce the sequence, and a writer that could has easier routes; but if that preflight ever became conditional, this branch's reachability jumps.
- **Acquisition timeout, not the fingerprint mismatch, is the dominant refusal under ordinary contention.** `_statelock`'s acquisition timeout is 10 s while a healthy cohort verb may hold for `GIT_TIMEOUT_S` = 20 s per spawn edge, so a non-exempt transition overlapping an ordinary cohort verb waits the full timeout and then refuses on acquisition. The wait sits inside the engine lock, so the spec's whole engine surface stalls for it. Fail-closed and retryable, and two orders of magnitude above the uncontended cost.
- A cohort-lock reclaim mid-hold leaves a committed transition behind a non-zero exit, because `_statelock` can only detect lost ownership after the block, and the skipped outbox finalisation leaves an `events.pending` that `_recover_pending` completes on the next run. Bounding that absolutely needs a two-phase commit, which the registered entry forbids, so AC13 pins the reporting obligation.
