# Plan: wave-complete dispatch receipts

- **Spec:** [`spec.md`](spec.md)
- **Status:** Approved <!-- Drafting | Approved | Executing | Done -->
- **Repository anchors:** ADR-0061 § Context (its Concern/Owner table carries
  the read-only-guard / explicit-mutation split this change sits inside);
  `packs/core/.apm/skills/work-loop/scripts/loop-cohort.py` `cmd_record_attempt`
  and `cmd_wave_advance` as the two analogous explicit cohort mutations, both
  `@_locked` and both `--expect-run-id`-authorized; their tests in
  `packs/core/tests/skills/work-loop/test_loop_cohort.py`,
  `test_loop_cohort_schedule.py` for the `schedule` change, and the golden
  contracts in `test_golden_fixtures.py` plus the replay in
  `test_loop_guards_parity.py` as the construction path; named uncertainty —
  whether `test_loop_cohort_cli.py` pins the parser's verb set, which T1 settles
  before T2 adds a verb.

> **Plan contract:** this is the implementation strategy. It may change
> substantively only while its Status is `Drafting`, before approval records its
> baseline. After approval, `spec.md` and `plan.md` are pinned in substance;
> only lifecycle bookkeeping is permitted, and execution observations belong in
> `docs/specs/<feature>/notes/verification-ledger.md`.
>
> **Not every field is contract.** `Touches`, `Tests` and `Done when` are what a
> completion gate reads, and they are pinned. `Approach`, `Constraints`,
> `Design`, `Rollout` and `Risks` are working material: an implementer corrects
> them in place as the work teaches, without an amendment and without a review
> round.

## Approach

One additive field in cohort state, one explicit mutation named
`dispatch-receipt` that writes it, one guard verdict table that reads it, and
one enforcement line on `loop-cohort status`.

Four earlier rounds of this plan failed the same way: a criterion was written as
a desired outcome and only then checked against the code that would satisfy it.
This revision inverts that order. Every decision below was taken from a code
read first, and where the read contradicted the previous plan, the plan changed.

**The accounting gets its own phase, and `implement` is left alone.** The
pre-PR hook globs every `docs/specs/*/state.json` and runs
`check --phase implement` on each with no state-machine gate, exiting non-zero
on failure — harmless today only because that phase is a stub that always
passes. Putting the accounting there would have made every push fail while any
spec directory had an unaccounted task. So `--phase wave-exit` carries the
verdict and the engine's `("code", "wave-complete")` entry points at it.
`PHASES` has no test pinning it, and the parity table's guard families key on
the verb, so a new phase under `check` owes no golden row — which matters,
because the fixture is generated once and never regenerated. It also makes the
golden `check/implement-ok` row untouched in the literal sense rather than
preserved by argument.

**The discriminator is the wave partition, not the plan hash.**
`canonical_contract` normalizes only four things, so `plan_hash` changes for an
ordinary prose edit to `plan.md`; keying on it would invalidate correct records
on a re-schedule that changed no wave, and an invalidated record is fabrication
pressure at a blocking exit. A digest of `schedule_waves` changes exactly when
the partition changes, and needs no new field — both sides compute it from state
already on disk.

**The digest alone is not enough, because an amendment can preserve the
partition.** The amendment path computes newly-completed tasks as those in the
waves before the current index, so an amendment raised at wave index zero with
no prior completions re-schedules the identical graph and produces an identical
digest — and pre-amendment records would discharge the post-amendment exit. So
the amendment path clears the container, which is also semantically right: the
contract changed, so every assertion about the old one is void. Between them,
`schedule` pruning records under a superseded digest and the amendment clearing
the container bound the stored set to one live partition, which is why no
explicit size cap is needed where the sibling collections in this file have one.

**The notice needs a caller, and GATES is not it.** `cmd_check` emits a passing
guard's `message`, so a passing guard can print — but the engine's adapter
discards it, and nothing in the skill invokes `check` for this phase at all.
Without a documented caller the notice would be contract with no invoker. The
caller cannot be GATES: GATES fires `wave-passed`, `gates-clean` and
`gates-failed`, and every documented firing of `wave-complete` reads "fire
`wave-complete`, then run GATES" — so GATES runs *after* the transition it would
have to precede. The check therefore goes immediately before the transition at
every site that instructs firing it. Some of those files carry more than one
such site, which is why the obligation is per site rather than per file; the set
is measured from the tree in § 2 of the verification ledger (“Which surfaces
execute the wave-exit guard's sibling phase”) rather than stored here.

**The guard is a verdict table whose predicates derive from one
declaration.** Four rounds produced criteria that overlapped or left gaps, and
this table then did it twice more. Its first draft let an empty partition with a
non-mapping container satisfy two rows with opposite verdicts, and a malformed
wave element such as `[123]` satisfy none, falling through to the opaque
`@contained` refusal. Its third draft bounded container well-formedness at two
key levels while the data model declared three, so every correctly shaped
container classified as malformed and the exit would have refused every valid
wave — and that round's walk stayed green, because the container values
were hand-built at the same two levels the predicate expected. The oracle
ratified the author's construction rather than the declaration.

So the container's key path is declared once, and both the predicate's nesting
depth and the domain's shapes derive from it. The current walk's size, domain and result
are recorded in § 4 of the verification ledger rather than restated here, so this
paragraph cannot fall a generation behind the walk as its predecessor did. T3 carries that walk,
and generating the domain from the declaration is part of what T3 implements
rather than an incidental test detail.

**Leaving a wave is coupled to the same predicate.** A guard that refuses an
unaccounted wave is worth little while `wave advance` walks past the same wave
unchecked, so the verb gains the accounting check — on the branch where
`current_wave_index` equals `--from-index` and the pointer moves, and not on the
branch that recognises the move as already applied. That asymmetry is
deliberate: the skill documents the verb as idempotent and `session-resumption`
re-issues it on a `wave-passed` resume, so a refusal on the already-applied
branch would turn crash recovery into a dead end. The check sits after the
verb's existing refusals, so nothing that refuses today refuses for a new
reason. `wave advance` has no golden row — it is a mutation, not one of the six
guard families the parity table covers — so the frozen fixture does not
constrain it.

Order of operations: settle what the pinned files require, add the field and the
mutation, then the verdict table and the reporting, then the controller-facing
prose, then prove each clause by removing it.

## Constraints

- **ADR-0061 (Frozen, Option A).** `loop-engine` owns read-only guard
  enforcement; `loop-cohort` owns skill-invoked mutations. Option B's durable
  side-effect semantics need a `pending_transition` schema that does not exist,
  so the record is best-effort by decision, not by omission.
- **The shared guard contract.** A `GuardResult` that passes may carry a
  `message` but not a `reason`, and the engine's guard table is typed to a
  refusal string or None. Changing that adapter is `Ask first` in the spec, and
  this plan does not.
- **The golden fixture is frozen.** Generated once before the guard extraction
  and deliberately never regenerated. No row may be added, rewritten, or
  regenerated; a row without an `after` is asserted byte-for-byte on both
  streams, and an `after` is legal only when the return code flips.
- **`loop-infrastructure-phase-1` (Shipped, frozen).** Its plan declares
  `check --phase implement` a Phase-1 compatibility stub. This change preserves
  that phase's behaviour exactly and adds a separate one, so the frozen plan
  stays accurate as well as unedited.
- **The pre-PR hook.** `tools/hooks/pre-pr.py` and its packaged copy run
  `check --phase implement` for every `docs/specs/*/state.json` on every push,
  ungated by the engine state. Nothing this change does may alter that phase's
  verdict for any state.
- **`packs/AGENTS.md`.** Pack content carries no internal-governance citations,
  every `.apm/` change bumps `pack.toml` and `.claude-plugin/plugin.json`
  together with a topmost changelog entry, a non-cosmetic pack update also
  updates the pack's eval harness, and adapter projections are never edited
  directly — they are regenerated by self-host after the pack edits. The
  projections are tracked files, so every task that edits `.apm/` regenerates
  them in the same task and names them in its `Touches`; deferring all
  regeneration to the last task would leave the intervening commits with
  sources and projections out of sync.
- **Phase-1 parallel verbs stay disabled.** `worktree`, `dispatch-decision`,
  and `auto-parallel` remain non-zero. The record is for the sequential path.

## Construction tests

**Integration tests:** one, landing in
`packs/core/tests/skills/work-loop/test_loop_engine.py` because that is the
transition-level suite — drive the real `wave-complete` transition through
`loop-engine` against a cohort state with an unaccounted task and assert a
non-zero exit. This is the only check that proves the guard reaches the live
exit rather than merely returning a refusal when called directly.

**Manual verification:** the mutation proof (T5). Each clause added in T2 and T3
is removed in turn, the suite re-run, and the observed red recorded in the
verification ledger. A clause whose removal leaves the suite green is not
verified and returns to T2 or T3.

## Durable-output map

| Durable output | Tasks | Implementation evidence | Closeout evidence |
| --- | --- | --- | --- |
| User promise / `docs/product/changelog.md` `[core]` entry with Highlights | T6 | Topmost `## [core][<version>]` heading agreeing with both pack manifests | Entry names the new refusal and the declines that avoid it |
| Maintainer procedure / `SKILL.md` § Step 2. EXECUTE + `supervisor-mode.md` § Single-agent fallback | T4 | Section-scoped checks find the call, its authorship, and both reason codes; three projected copies byte-identical | Both named sections carry all three |
| Interface compatibility / `references/state-schema.md` | T4 | Reference names the container and its absence rule | Absence rule documented |
| Reusable learning / `notes/verification-ledger.md` | T1, T5 | T1's `Done when` requires the pinning survey and the dispatch-rate measurement; T5's requires the mutation table | Ledger records all three, each obliged by a pinned field |

## Design (LLD)

### Design decisions

- **A separate `wave-exit` phase; `implement` untouched.** Traces to: the
  verdict rows and the criterion that `implement` returns what it returns today.
  The pre-PR hook runs `implement` for every spec directory on every push with
  no engine gate, so a refusal there is a push gate. Rejected alternative:
  gating the hook's `implement` leg on the engine state — it widens the change
  into a shipped hook every adopter has wired, to buy nothing the new phase does
  not.
- **Per-task, not per-wave.** Traces to: the verb's accept criteria. A
  wave-granular record would let one entry discharge a five-task wave, which is
  the hole being closed.
- **The run identifier is a staleness check, not an authenticator, and the
  partition digest is not tamper-evidence.** Traces to: the run-identifier
  refusal. Neither establishes which party wrote a record; the digest is an
  unkeyed function of state held beside the records it partitions. Rejected
  alternative: a distinguishing element identifying the caller — a new trust
  mechanism the spec routes to `Ask first`.
- **The partition digest discriminates a stale partition; the amendment path
  clears the container.** Traces to: the record-lifecycle criteria. The digest
  alone is insufficient because an amendment at wave index zero with no
  completions reproduces the identical partition. Together, pruning on a
  partition-changing `schedule` and clearing on amendment keep at most one live
  partition's records, which is why no explicit size cap is specified where the
  sibling collections in this file carry one.
- **Records carry no run identifier of their own.** Traces to: nothing, which is
  the point. `init` refuses an existing `state.json` and `reset` deletes it, so
  a record cannot outlive its run and a stored run identifier would be a field
  no reachable state could falsify.
- **Verdict rows whose predicates derive from one key-path declaration.** Traces to:
  the verdict rows and the two partition criteria. Branch order is an
  optimisation; the preconditions decide behaviour. The predicates are named
  once rather than repeated per row, because repeating them informally is how
  the first draft of this table omitted one and produced two rows with opposite
  verdicts over the same state.
- **`current_wave_index` is validated by the guard layer's existing
  non-negative-integer helper.** Traces to: the pointer row and the verb's
  index criterion. It already rejects `bool` and owns its message shape, and
  `check_wave` and `check_plan_current` consume it for the same kind of field.
  Rejected alternative: a fresh predicate, which would be a second authority on
  one field.
- **The notice prints from `check --phase wave-exit`, run immediately before the
  transition at each firing site.** Traces to: the absent-container row and the
  firing-site criteria.
  `cmd_check` emits a passing guard's `message`; the engine's adapter discards
  it, and no existing step invokes this verb, so without the pre-transition run the
  notice would be contract with no caller.
- **Closed two-value decline set, enforced on both sides.** Traces to: the
  reason-code refusal and the accounting criterion. Validating only the write
  path leaves the state the guard reads unbounded.

### Data & schema

Traces to: the accounting criteria, the lifecycle criteria, the duplicate
criterion, and the absent-container row.

One additive, optional mapping on cohort `state.json`, alongside the existing
`completed_task_evidence` map, which is the keyed-map precedent — `worktrees` is
a list and always empty in Phase 1, so it is not one. A record is held under the
partition digest, the wave index, and the task identifier, which makes one
record per triple and a repeat write a replacement. A record carries its kind
and, for a decline, its reason; nothing else.

The partition is `schedule_waves`, read with an absent key defaulting to the
empty list, which is what every existing guard that reads that field does. Its
digest is computed by one helper both the verb and the guard call, and is not
persisted: deriving it on each read means it cannot drift from the partition it
describes.

Lifecycle: `init` and `schedule` leave the container present; `schedule` removes
records held under a digest other than the one it just computed; the contract
amendment path leaves the container empty. Those two removals are the only ones,
and together they bound the stored set to one live partition. `schema_version`
stays as it is: the field is additive and read through a defaulting accessor.
An absent container means the state predates receipts — or that the key was
removed, which the guard cannot distinguish and the spec discloses.

### Interfaces & contracts

Traces to: the verb's criteria, the verdict rows, the firing-site criteria, and the
status criterion.

One new `loop-cohort dispatch-receipt` verb, following the shape both analogous
mutations already use: state lock held for the write, `--expect-run-id`
validated before anything is written, and a refusal that names what it
rejected. Receipt and decline are mutually exclusive on one invocation. The verb
takes the wave index explicitly and accepts a non-negative integer up to and
including the current wave index — a wave already left can be recorded against,
because the verb-mediated advance is coupled to this guard only on the branch
that moves the pointer — a wave left by the already-applied branch, or by a
direct `state.json` write, still needs its record to be obtainable; a wave not
yet reached cannot, because `schedule`
prints the whole partition, so a forward index would let one pre-run batch
discharge every exit. An unusable partition — empty, or a pointer that is not a
valid index into it — is refused by name rather than indexed into.

`--phase wave-exit` is a fourth member of `PHASES`, carrying the verdict table.
`--phase implement` keeps its current behaviour. The engine's
`("code", "wave-complete")` guard-table entry points at the new phase.

`loop-cohort status` gains one key reporting whether receipts are enforced, in
both its default and `--json` forms.

### Failure, edge cases & resilience

Traces to: the verdict rows, the verb's unusable-partition refusal, and
the byte-equality criteria.

- **Interrupted dispatch.** Best-effort by decision. A controller that crashes
  between the implementer returning and the record being written has no record,
  and the remedy is to write it, not to recover it. This is the Option B line.
- **Contract amendment.** The container is cleared, so no pre-amendment record
  accounts for anything — including the case where the re-scheduled partition is
  byte-identical and its digest therefore unchanged.
- **Re-schedule without amendment.** A partition-preserving re-schedule keeps
  records; a partition-changing one removes the stale ones.
- **A wave advanced past without its exit check.** `wave advance` moving the
  pointer before the exit fires is closed for the verb-mediated path: the
  advancing branch applies the same accounting predicate. A record stays
  writable for an already-left wave regardless, so a record is not lost on the
  already-applied branch. What remains open is a pointer moved by a direct
  `state.json` write, disclosed in the spec's Boundaries at the same strength
  as forgery and container deletion.
- **A repair round.** `gates-failed`, `findings-remain`, and `blocker-applied`
  re-enter `CODE-IMPLEMENTATION` without moving the pointer, so the first pass's
  records satisfy every later exit for that wave. Disclosed and registered.
- **Malformed state.** A `schedule_waves` that is not a list, a container that
  is not a mapping, and a current wave that is not a list of strings each get a
  named refusal row. `check_phase` is wrapped by `@contained`, so an escaping
  exception already becomes a refusal — fail-closed, but opaque, which is what
  the rows replace. The verb gets the matching refusal so it does not raise out
  of a lock-holding mutation.
- **Guard purity.** The criteria comparing state bytes before and after a run,
  for every row whose state has a file, make the no-write rule falsifiable on
  the paths where a write would be tempting.

## Where a claim is settled

Three tiers, and a claim belongs to exactly one:

- **Settled before approval, here or in `spec.md`.** Anything that could change
  intent, an acceptance criterion, architecture, a dependency choice, a security
  or data boundary, the task graph, or a verification mechanism. These are not
  discoverable; deferring one means approving a contract whose meaning is still
  open.
- **In an unstarted task, with a kill condition.** A claim that could change
  only that task's local method — which fixture to extend, which helper to
  reuse — and nothing another task or criterion depends on.
- **In code, with a direct test oracle.** A cheap, reversible detail whose
  wrongness a test states immediately: a message's exact words, a helper's name,
  a fixture's internal shape.

**The discovery channel below is spent, and that is recorded rather than
quietly dropped.** Every question T1 predeclared now has an answer, and the
answers do not all live in one place, so the pointer names each home rather
than the ledger as a whole. Ledger § 2 holds the pre-PR chain and the
firing-site set; § 3 holds the helper contracts and the length bounds; the
`schema_version` answer is the first entry in § Discovery decisions in this
plan, because it fired the kill condition. The pinning survey, the phase-list
surface inventory, and the inventory of statements asserting that `implement`
guards `wave-complete` are **not** recorded yet — they are T1's `Done when`,
which is why that field names the survey explicitly. Several answers turned out
to be tier one rather than tier two — the `schema_version` behaviour is a verification
mechanism *and* a security boundary, the pre-PR chain decides which surface the
change gates, the firing-site set decides the task graph, and the length bounds
decide a criterion. Its kill condition fired before T1 ever ran and was resolved
by taking a bounded alternative, which is recorded as the first entry in
§ Discovery decisions. What remains in T1 is the obligation to record two ledger
entries, which is not discovery. Nothing tier-one is deferred to it.

## Discovery channel (spent; retained for its decision record)

T1 was a **declared discovery task**. Exact helper names, fixture shapes, and
local construction details for an unstarted task may remain unresolved until it
runs; T1 may then refine those details in named, unstarted tasks only. A task
section locks when its execution begins, and a completed section is immutable.

- **Discovery predicate, predeclared.** T1 resolves exactly six questions, each
  with a stated form of answer: which surfaces execute `check --phase implement`
  and whether each consumes the exit code; which sites fire `wave-complete` and
  whether each runs before or after GATES; what `check_phase` does with an
  unsupported `schema_version` for a phase other than `implement`; which
  statements in the tree assert that `implement` guards `wave-complete`; which
  surfaces enumerate the phase list; and what length bound each refusal channel
  applies. Anything outside those six is not discovery.
- **Kill condition.** If the `schema_version` answer is that a new phase refuses
  where `implement` passes, the separate-phase approach is killed, because it
  would change the transition's verdict for in-flight pre-Phase-1 runs — the
  breakage the design exists to prevent. Bounded alternatives, in preference
  order: (i) keep the accounting in `implement` and scope the pre-PR hook's
  `implement` leg to the engine state, which widens the change into a shipped
  hook; (ii) add the accounting as a second, `implement`-exempt branch sharing
  `implement`'s schema exemption; (iii) leave the guard a stub and close the gap
  at a different transition. Selecting any alternative is a contract amendment,
  not discovery.
- **Refinable tasks.** T1 may refine only T2 and T3, and only their `Approach`
  bullets and the helper, fixture, and path details inside their `Tests`
  entries. It may not change a task's stated outcome, its `Done when`, its
  `Depends on:` edge, or any acceptance criterion.
- **Decision record.** Every refinement appends one dated entry to
  § Discovery decisions below, naming the question, the evidence, the surfaces
  read, and the task and field refined. Entries are append-only; a superseded
  entry is answered by a later entry, never edited.
- **Scoped review.** A refinement re-reviews the changed task and every task
  whose `Depends on:` edge reaches it — for a T2 refinement that is T2 and T3;
  for a T3 refinement, T3 alone. Not the whole plan.
- **Preserved.** Discovery writes nothing to `amendment_history` and nothing to
  `completed_task_ids` or `completed_task_section_hashes`; a refinement of an
  unstarted task leaves both untouched, which is what keeps it distinct from an
  amendment.

Any change outside those bounds — an acceptance criterion, a task's outcome, a
dependency edge, a verification obligation, or any started task — uses the
controlled amendment path in
[`delivery-contract-lifecycle.md`](../../../packs/core/.apm/skills/work-loop/references/delivery-contract-lifecycle.md).

## Discovery decisions

<!-- Append-only. One entry per refinement: date, question, evidence, surfaces
read, task and field refined. Never edit an existing entry. -->

- **2026-09-17 — the kill condition fired before T1 ran, and an alternative was
  taken.** Question: what does `check_phase` do with an unsupported
  `schema_version` for a phase other than `implement`? Evidence:
  `_loop_guards.py` refuses when `phase != "implement" and
  state.get("schema_version") != SCHEMA_VERSION`, before any phase dispatch —
  so a new `wave-exit` phase would refuse where `implement` passes, changing the
  `wave-complete` verdict for in-flight pre-Phase-1 runs. That is the
  predeclared kill condition for the separate-phase approach. Surfaces read:
  `packs/core/.apm/skills/work-loop/scripts/_loop_guards.py` (the shared
  preamble in `check_phase`) and
  `packs/core/tests/skills/work-loop/test_loop_guards.py`, whose assertions pin
  only that `implement` passes and `review` refuses on `schema_version: 99` —
  they say nothing about a third exempt phase. Alternative taken: (ii), share
  `implement`'s exemption, widening the exempt set rather than keeping the
  accounting in `implement`, because (i) would widen the change into a shipped
  hook every adopter has wired. The exemption alone was not sufficient: it buys
  totality, not verdict preservation, so the table additionally passes an
  unsupported-schema state on its own row before any shape is read. Refined:
  none — this was settled before approval, so it is
  a revision of the Draft spec through the pre-EXECUTE review loop, not a
  discovery-time refinement of an unstarted task, and no amendment machinery
  applies. Recorded here because the channel's kill condition is what surfaced
  it.

## Inline proof obligation

Three mechanisms in this change have a consequential false-pass direction: the
verdict table and the accounting predicate are classifiers whose wrong answer is
a wave exiting unaccounted; the verb's validation chain is a gate whose wrong
answer is a record written under a key the guard never reads; and the partition
walk is a negative control whose wrong answer is a green suite over an
unexplored domain. The dispatch-rate generator is an extractor whose wrong
answer is a motivating figure that overstates the gap.

Each of those arms proves itself in the task that introduces it, and each proof
carries four parts:

1. a discriminating positive case and a consequential negative case;
2. a demonstration that removing or neutralising the arm reddens a **named**
   case;
3. exercise of the real entry path — the CLI verb or the transition — not only
   the helper it calls;
4. the condition that retires the approach.

`Done when` entries below carry these; they are not deferred to T5. T5 remains
the exhaustive per-clause sweep, not the first time an arm is tested.

## Tasks

### T1: The measurement and the pinning survey are recorded

**Depends on:** none

**Touches:** docs/specs/wave-complete-dispatch-receipts/notes/verification-ledger.md

**Tests:**
- `no stub (mode)` — goal-based.

**Approach:**
- The questions this task predeclared are settled as *answers*, but not all are
  recorded. Ledger § 2 and § 3 hold the pre-PR chain, the firing-site set, the
  helper contracts and the length bounds, with the surfaces read; the
  `schema_version` answer is in § Discovery decisions above. Read those rather
  than re-deriving them: a settled tier-one claim is read, not rediscovered.
  The pinning survey, the phase-list surfaces, and the `implement`-guards-
  `wave-complete` assertion inventory are the ones this task still writes.
- Confirm the pre-PR hook's `implement` leg is still ungated by the engine state
  and still runs for every `docs/specs/*/state.json`, since the separate-phase
  design rests on it and the tree may have moved. If it no longer holds, stop
  and surface — this is a tier-one premise, not a detail to work around.
- Confirm no golden row replays `check` with a phase other than `implement`,
  `review`, or `gates-failed`, and that the parity table's guard-family
  assertion keys on the verb rather than the phase.
- Establish whether `test_loop_cohort_cli.py` pins the parser's verb set, the
  `--help` output, or neither, and whether anything pins `PHASES`.
- Record what each of `test_golden_fixtures.py`, `test_loop_guards_parity.py`,
  `test_loop_cohort_cli.py`, and `test_loop_cohort_schedule.py` pins, and what
  T2 or T3 must do about it.
- Record the dispatch-rate measurement that motivated the change — session
  counts, dispatch counts, controller edit counts for the pre- and
  post-reminder windows — with the scan method. The ledger is its single home;
  the spec cites it rather than repeating the figures.
- Read-only task: it writes only the ledger.

**Done when:** the ledger answers every question this task predeclared, each
naming the surfaces read rather than a grep pattern; records the pinning survey,
naming for each of `test_golden_fixtures.py`, `test_loop_guards_parity.py`,
`test_loop_cohort_cli.py`, and `test_loop_cohort_schedule.py` what it pins and
what T2 or T3 owes it; records the golden confirmation; and records one run of
the dispatch-rate generator.

**Inline proof — the dispatch-rate generator is an extractor.**
- Positive: the tight pattern matches a real `loop-cohort.py schedule
  docs/specs/<slug>` invocation. Negative: it does not match a command that
  mentions `loop-cohort` without the subcommand and an argument, which is the
  over-count direction; the generator reports that loose count alongside so the
  gap is visible.
- Neutralising proof: replacing the tight pattern with the loose one changes the
  reported engine-driven count on the recorded corpus. The ledger records both
  numbers from one run, so the substitution is falsifiable from the artifact.
- Real entry path: the generator is run as a committed script from the
  repository root, not imported; the ledger cites the command.
- Retires when: the loop records dispatch in cohort state, at which point the
  rate is a query over `state.json` and transcript scanning is obsolete.

### T2: The record mutation and the record lifecycle behave as specified

**Depends on:** T1

**Touches:** packs/core/.apm/skills/work-loop/scripts/loop-cohort.py, packs/core/.apm/skills/work-loop/assets/state.json, .claude/skills/work-loop/scripts/loop-cohort.py, .agents/skills/work-loop/scripts/loop-cohort.py, .claude/skills/work-loop/assets/state.json, .agents/skills/work-loop/assets/state.json, packs/core/tests/skills/work-loop/test_loop_cohort.py, packs/core/tests/skills/work-loop/test_loop_cohort_cli.py, packs/core/tests/skills/work-loop/test_loop_cohort_schedule.py, packs/core/tests/skills/work-loop/test_contract_amendment_wave4.py, packs/core/tests/skills/work-loop/test_loop_concurrency.py

**Tests:**
- A receipt for a task in the named wave with a matching run identifier exits
  zero and the task reads as accounted for.
- A decline with `no-implementer-installed` does the same, and one with
  `human-directed` does the same.
- Recording against the current wave index exits zero; recording against a
  lower index the schedule contains exits zero.
- Recording against an index above the current wave index exits non-zero.
- Recording against a negative index, a boolean, and a non-integer each exit
  non-zero through the guard layer's existing non-negative-integer validation.
- Recording when the partition is empty, and when the pointer is not a valid
  index into it, each exit non-zero naming the unusable partition, and neither
  raises.
- Receipt and decline together exit non-zero.
- A decline reason outside the closed set exits non-zero and the message
  contains both accepted codes.
- A task absent from the named wave exits non-zero and the message names that
  wave's tasks.
- A named wave whose identifier list exceeds the per-value interpolation bound
  drives the verb's largest state-derived refusal; the verb's own stderr is
  bounded, discloses truncation, and contains only whole identifiers.
- A non-matching `--expect-run-id` exits non-zero.
- Every shape the well-formedness declaration calls malformed, derived from
  that declaration rather than sampled: `schedule_waves` a non-list; the wave
  element at the named index a non-list, an **empty** list, and a list
  containing a **non-string**; and the receipts container malformed at each
  declared depth in turn. Each exits non-zero and names the malformed position
  rather than surfacing an exception type, and each leaves `state.json`
  byte-identical. Three wave shapes rather than one because the declaration
  requires a non-empty list of strings, so a single non-list case leaves the
  other two conjuncts unexercised. Derived from the same
  key-path and well-formedness declarations the guard's rows use, so the two
  cannot disagree about which shapes are hostile.
- A state whose `schema_version` is not the supported value exits non-zero and
  the message names the schema. Separate from the run-identifier case because
  `_validate_run_id` emits a distinct message for the schema branch, so the
  run-id case cannot stand in for it.
- One case per refusal above asserts `state.json` is byte-identical to its
  pre-invocation content, and one case asserts it for a refusal raised by the
  state read itself, so the property covers the verb's whole refusal set.
- Recording the same triple twice exits zero both times and leaves exactly one
  record.
- `init` leaves the container present; `schedule` leaves the container present.
- A `schedule` run producing the same partition leaves an earlier record
  present and unchanged, with an intervening edit to `plan.md` that
  `canonical_contract` does not normalise — so `plan_hash` moves while the
  partition does not, and a `plan_hash`-keyed implementation reds. Without that
  edit the assertion is satisfied by a no-op re-schedule and discriminates
  nothing.
- A `schedule` run producing a different partition leaves no record under the
  superseded digest.
- A contract amendment leaves the container empty, asserted for the case where
  the re-scheduled partition is identical and the digest therefore unchanged.
- `stub: true` — one compilable red assertion on the accounted-for predicate
  for a single recorded receipt; the seam is grounded because both analogous
  mutations already establish the shape.

**Approach:**
- Add the container to the bundled `state.json` template; have `cmd_schedule`
  create it when absent and drop records under any other digest; have the
  amendment path leave it empty.
- Add the partition-digest helper, computed from `schedule_waves` with an absent
  key defaulting to the empty list, called by both the verb and the guard.
- Add the `dispatch-receipt` verb beside `record-attempt`, reusing its
  state-lock and run-identifier validation shape, and the guard layer's
  non-negative-integer helper for the index.
- Validate in refuse-cheapest-first order: run identifier, mutual exclusivity,
  reason code, index type and range, usable partition, task membership. Nothing
  is written until every check passes.
- Apply whatever T1 recorded about verb-set and `PHASES` pinning.
- Three details are deliberately left to code, each with the oracle that states
  its wrongness immediately: the exact words of each refusal, the names of the
  helpers added, and the internal shape of each new fixture. The oracle is the
  task's own pytest invocation — a wrong message fails the assertion that reads
  it, a wrong helper name fails to import, a wrong fixture shape fails the case
  built on it. None of them is a claim another task or criterion depends on.
- Run `FORCE=1 make build-self` and verify the three copies of each edited
  `.apm/` file are byte-identical before finishing.

**Inline proof — the verb's validation chain is a gate.**
- Positive: a receipt for a task in the current wave with a matching run
  identifier is accepted and reads as accounted for. Negative, consequential in
  the false-pass direction: a wave index one above `current_wave_index` is
  refused, because accepting it lets one pre-run batch discharge every later
  exit.
- Neutralising proof: deleting the upper-bound comparison reddens the named case
  `a wave index above the current wave index exits non-zero`; deleting the
  reason-code membership check reddens the named closed-set case.
- Real entry path: both are asserted through the CLI verb by subprocess, not
  only against the validation helper, because the parser is what a controller
  reaches.
- Retires when: caller identity becomes establishable, at which point the
  index bound stops being the thing that limits a forged batch.

**Approach note:** the digest helper is single-sourced deliberately. A test that
the verb and guard name the same container key cannot be written once the key
has one home, so agreement is proved by the round trip in T3 instead.

**Done when:** every assertion above is green, the three copies of each edited
`.apm/` file hash equal, and `python3 -m pytest
packs/core/tests/skills/work-loop/test_loop_cohort.py
packs/core/tests/skills/work-loop/test_loop_cohort_cli.py
packs/core/tests/skills/work-loop/test_loop_cohort_schedule.py
packs/core/tests/skills/work-loop/test_contract_amendment_wave4.py
packs/core/tests/skills/work-loop/test_loop_concurrency.py -q` passes.
`test_contract_amendment_wave4.py` calls `apply_contract_amendment` directly and
is the suite that owns the path this task changes; `test_loop_concurrency.py`
covers the state lock a new mutation takes.

### T3: The wave exit refuses an unaccounted task and names it

**Depends on:** T2

**Touches:** packs/core/.apm/skills/work-loop/scripts/_loop_guards.py, packs/core/.apm/skills/work-loop/scripts/loop-cohort.py, packs/core/.apm/skills/work-loop/scripts/loop-engine.py, .claude/skills/work-loop/scripts/_loop_guards.py, .agents/skills/work-loop/scripts/_loop_guards.py, .claude/skills/work-loop/scripts/loop-cohort.py, .agents/skills/work-loop/scripts/loop-cohort.py, .claude/skills/work-loop/scripts/loop-engine.py, .agents/skills/work-loop/scripts/loop-engine.py, packs/core/tests/skills/work-loop/test_loop_guards.py, packs/core/tests/skills/work-loop/test_loop_guards_parity.py, packs/core/tests/skills/work-loop/test_loop_cohort.py, packs/core/tests/skills/work-loop/test_loop_cohort_cli.py, packs/core/tests/skills/work-loop/test_loop_engine.py, packs/core/tests/skills/work-loop/test_loop_concurrency.py

**Tests:**
- One case per verdict row, asserting the exit code and the content of both
  streams.
- A partition-property case over **every** axis the spec's domain criterion
  enumerates — the state-read outcome as returned-or-refused, `schedule_waves`,
  its element at the pointer, the container, a record's `kind` **and its
  `reason`**, `schema_version`, and `current_wave_index`, each varied by
  presence, type, and value — plus a separate case asserting
  that every kind in the reader's refusal vocabulary classifies to the
  read-refusal row and nowhere else, which is what licenses the two-valued
  axis. That criterion is the
  canonical list and this entry cites it rather than restating a subset, because
  restating it is how three axes went missing while the walk stayed green.
  Container values are generated from the declared key path — a correct instance
  nested from it, then mutated at each depth with each hostile value — not
  hand-built at a literal depth.
- Every constructed state satisfies exactly one row; every row is satisfied by
  some state.
- Three tasks, two accounted for → the refusal names the one unaccounted task
  and not the two accounted ones.
- A decline record whose reason is outside the closed set does not account for
  its task, so the guard refuses.
- A record held under a superseded partition digest does not account for its
  task, so the guard refuses.
- A round trip: a record written by `dispatch-receipt` is counted by
  `check --phase wave-exit` with no intervening re-schedule.
- One case per row whose state has a file, asserting `state.json` is
  byte-identical before and after the guard invocation.
- `check --phase implement` returns the same exit code and streams as before
  this change, asserted over the states the new rows distinguish.
- `check --phase wave-exit` on a state with `schema_version: 99` reaches the
  verdict table rather than refusing on the schema, and `--phase review` and
  `--phase gates-failed` on the same state still refuse — the discriminating
  pair for the widened exemption.
- `loop-cohort status` reports receipts not enforced when the container is
  absent and enforced when present, in both the default and `--json` forms.
- A wave whose unaccounted-task list exceeds the per-value interpolation bound:
  the refusal states the list is partial, and every identifier it prints is
  whole — no fragment of an identifier appears.
- A state-derived value longer than the bound: the refusal does not carry it
  whole, asserted on the stream rather than on the helper.
- A bad-reason decline: the guard refuses **and** stderr names the malformed
  field, so removing the reason check from the record definition — which would
  turn that state into an accounted-for pass — flips the verdict and reddens.
- `wave advance --from-index n` with `current_wave_index == n` and an
  unaccounted task in wave `n`: exits non-zero, names that task, and leaves
  `state.json` byte-identical so the pointer does not move.
- The same call with wave `n` fully accounted for: exits zero and advances.
- `wave advance --from-index n` with the receipts container absent and
  `current_wave_index == n`: exits zero and advances, which is the
  absent-container exemption reached through the verb rather than the guard.
- `wave advance --from-index n` with `current_wave_index` stored as `"1"`,
  `1.9`, `True`, and `None` in turn: each exits non-zero, names the field, and
  leaves `state.json` byte-identical. Four cases rather than one because the
  reading this replaces — `int(...)` — accepts the first three and raises on
  the fourth, so a single case cannot show the change.
- `wave advance --from-index n` against every shape the well-formedness
  declaration calls malformed, derived from it rather than sampled:
  `schedule_waves` a non-list; the element at `n` a non-list, an empty list,
  and a list containing a non-string; and the container malformed at each
  declared depth in turn. Each refuses by name rather than raising, and names
  `reset` where the unusable value is in cohort state.
- `wave advance --from-index n` with `current_wave_index` matching neither `n`
  nor `n + 1`: keeps its existing mismatch refusal, unchanged by the accounting
  check. This is the third branch, and without a case the sweep in T5 cannot
  tell it apart from the advancing branch.
- A bounded survey of the state reader's refusal vocabulary, read from
  `_loop_guards.py` rather than from the walk's own constant, asserting that the
  constant names every kind the reader can refuse with. The walk proves each
  listed kind lands on the read-refusal row; only this survey closes the other
  half. It belongs here rather than in T1 because T1's question set is closed
  and does not contain it, and because it is a property of the row this task
  implements.
- The bounding pair driven through the verb, not only the guard: a wave whose
  unaccounted-task list exceeds the per-value interpolation bound, and a
  state-derived value longer than the bound, each asserted on `wave advance`'s
  own stderr. Separate from the guard-side pair above because the verb emits
  through `loop-cohort`'s diagnostic helper, which the ledger measures as
  applying no length bound at all — so the guard-side cases prove nothing about
  this channel.
- `wave advance --from-index n` with `current_wave_index == n + 1` and wave `n`
  unaccounted: exits zero, because that is the documented crash-resume replay.
  This is the discriminating pair for the branch asymmetry — a coupling applied
  to both branches passes the first case and fails this one.
- Each of the verb's existing refusals — empty partition, negative index,
  out-of-range index, final wave, run-identifier mismatch — still exits non-zero
  with its current reason, asserted against a state where the accounting check
  would also have refused, so precedence is pinned rather than incidental.
- Integration, in `test_loop_engine.py`: the real `wave-complete` transition out
  of `CODE-IMPLEMENTATION` exits non-zero against a state with one unaccounted
  task.
- Integration, in `test_loop_engine.py`: distinguish the current wave from the
  next wave, run the pre-transition verdict before any pointer advance, and
  assert that it names the unaccounted task in the current wave and not a task
  in the next wave.
- Every existing call site that drives `wave advance` through the real CLI still
  behaves as it does today. Enumerate the call sites by globbing the suite
  tree rather than by naming files from memory — a hand-picked file list
  undercounted this set once; `test_loop_cohort_cli.py` was the file that
  earlier tally missed, and its `_scheduled()` fixture drives
  `wave advance --from-index 0` asserting exit zero with no receipts written,
  so that fixture needs records. Then enumerate which of the sites reach the
  advancing branch — the others refuse before the accounting
  check and are unaffected — and give each of those a record in its fixture.
  Pinned because the failure is otherwise discovered rather than planned.
- Every existing path that drives `init` → `schedule` → `wave-complete` through
  the real CLI still reaches `CODE-VERIFICATION`. `make_crash_window_run` and
  `make_code_review_run` in `test_loop_engine.py` populate `schedule_waves` and
  write no records, so container-at-`init` makes them refuse; each gets a record
  written in the fixture. Pinned here because the failure is otherwise
  discovered rather than planned.
- `stub: true` — one compilable red assertion that the guard refuses a
  single-task wave with no record.

**Approach:**
- Add `wave-exit` to `PHASES` and a `wave-exit` branch to `check_phase`
  carrying the verdict table. Leave the `implement` branch exactly as it is.
- Widen `check_phase`'s schema-validation exemption from the single `implement`
  phase to a named set containing `implement` and `wave-exit`, so a run in
  flight from before this change reaches the rows instead of being refused on
  its schema. This is the alternative the kill condition selected; the existing
  test pins only `implement` passing and `review` refusing, so it constrains
  neither direction of this change and must still pass unaltered.
- Point the engine's `("code", "wave-complete")` guard-table entry at a new
  adapter over the `wave-exit` phase. This adds a table entry and a function; it
  does not change `_guard_reason`'s contract.
- Implement the rows in precondition order, but write each precondition so it
  stands alone — the partition property is what the test asserts, not the order.
- Derive the container predicate's nesting depth from the declared key path, not
  from a literal. A restated depth is what made an earlier draft reject every
  valid container.
- Let the unsupported-schema row pass before the table is consulted, so a state
  the `implement` phase passes today keeps its passing verdict. Widening the
  schema exemption alone only guarantees the state reaches the table;
  `implement` returns ok for any readable state, so the table could still land
  it on a refusing row using a field whose shape an unsupported schema leaves
  unspecified.
- Build the refusal from the set difference so it names tasks rather than a
  count.
- Carry the absent-container notice in the passing result's `message`, which
  `cmd_check` prints on stdout.
- Add the `status` enforcement key to both output forms.
- Re-probe the projected tree, not only the edited source: after `build-self`,
  run the wave-exit check and the `status` verb from the projected
  `.claude/skills/work-loop/scripts/` copy and confirm the verdict and the
  enforcement key match the ones asserted against `.apm/`. Regeneration and
  re-measurement both stay inside this task.

**Inline proof — the verdict table and the accounting predicate are
classifiers; the partition walk is a negative control.**
- Positive: a wave whose every task carries a record exits zero silently.
  Negative, consequential: a wave with one unaccounted task exits non-zero and
  names that task, and a record whose `kind` or shape is outside the accepted
  set does **not** account for its task.
- Neutralising proof: replacing the accounting predicate with `True` reddens the
  named case `one task carrying neither → refuses`; deleting the record-shape
  check reddens the named malformed-record case; and replacing the partition
  walk's generated domain with one example per row leaves the suite green, which
  is itself recorded as the demonstration that the domain — not the predicate —
  is what the control rests on.
- Real entry path: the refusal is asserted through the `wave-complete`
  transition via `loop-engine`, and the notice through the `check` CLI verb, not
  only against `check_phase`.
- Retires when: the engine records per-task state of its own, at which point the
  guard reads engine state and the cohort-side table is redundant.
- Run `FORCE=1 make build-self` and verify the three copies of each edited
  `.apm/` file are byte-identical before finishing.

**Done when:** every assertion above is green, including the transition-level
one; no **live, editable** surface still asserts that `check --phase implement`
guards the `wave-complete` transition. Five assert it today, measured
exhaustively in § 8.2 of the verification ledger rather than sampled:
`_loop_guards.py:1194` (`check_phase`'s docstring), `loop-cohort.py:1558`
(`cmd_check`'s docstring), `test_loop_guards.py:2037` (a docstring),
`loop-engine.py:1012` (the guard-table entry, which the retarget clause below
already changes), and `test_loop_engine.py:1615` (a docstring). The scope word
is load-bearing: `docs/specs/loop-infrastructure-phase-1/plan.md` states the
same coupling at six lines and is Shipped and frozen, which this plan's
Constraints require unedited, so an unscoped clause could never be discharged.
That frozen statement is a recorded historical account of Phase 1, not a live
claim about the guard, and it stays;
`_guard_check_phase_implement` is either removed or given a caller, since
retargeting the guard table leaves it with neither; the three copies of each
edited `.apm/` file hash equal; and
`python3 -m pytest packs/core/tests/skills/work-loop/test_loop_guards.py
packs/core/tests/skills/work-loop/test_loop_guards_parity.py
packs/core/tests/skills/work-loop/test_loop_cohort.py
packs/core/tests/skills/work-loop/test_loop_cohort_cli.py
packs/core/tests/skills/work-loop/test_loop_engine.py
packs/core/tests/skills/work-loop/test_loop_concurrency.py
packs/core/tests/skills/work-loop/test_golden_fixtures.py -q` passes.

### T4: The controller-facing surfaces carry the calls, the authorship, and the codes

**Depends on:** T3

**Touches:** packs/core/.apm/skills/work-loop/SKILL.md, packs/core/.apm/skills/work-loop/references/supervisor-mode.md, packs/core/.apm/skills/work-loop/references/state-schema.md, packs/core/.apm/skills/work-loop/references/session-resumption.md, packs/core/.apm/skills/work-loop/references/finding-adjudication.md, packs/core/tests/pack/test_finding_adjudication_contract.py, packs/core/.apm/skills/work-loop/evals/evals.json, .claude/skills/work-loop/SKILL.md, .agents/skills/work-loop/SKILL.md, .claude/skills/work-loop/references/supervisor-mode.md, .agents/skills/work-loop/references/supervisor-mode.md, .claude/skills/work-loop/references/state-schema.md, .agents/skills/work-loop/references/state-schema.md, .claude/skills/work-loop/references/session-resumption.md, .agents/skills/work-loop/references/session-resumption.md, .claude/skills/work-loop/references/finding-adjudication.md, .agents/skills/work-loop/references/finding-adjudication.md, .claude/skills/work-loop/evals/evals.json, .agents/skills/work-loop/evals/evals.json

**Tests:**
- `no stub (mode)` — goal-based.
- A section-scoped absence check over `## Step 3. GATES` succeeds as
  `! grep -q -- '--phase wave-exit'`, proving GATES carries no pre-exit
  instruction.

**Approach:**
- In `SKILL.md` § Step 2. EXECUTE, state `loop-cohort dispatch-receipt` as
  required once per plan task, using the section's existing cardinality
  vocabulary, and state that the controller records it and an `implementer` does
  not record its own. The section already declares what the controller retains,
  so this extends that sentence rather than adding a trust mechanism.
- Instrument every *site* that instructs firing `wave-complete`, not every
  file. `SKILL.md` carries the changes-requested, further-in-intent-unit and
  specialist-adjudication sites; `references/finding-adjudication.md` carries
  its post-GATES re-entry and its FIX re-entry; `references/supervisor-mode.md`
  and `references/session-resumption.md` each carry one. Name them by what they
  are, not by how many: a stored count decays the moment a site is added. Do
  not put the check in GATES: GATES runs after that transition.
- The checked region differs by surface shape, so state it per shape rather than
  assuming a fenced block: `SKILL.md` uses fenced command blocks for the
  changes-requested and specialist-adjudication sites, and running prose inside
  a bullet for the further-in-intent-unit site; `supervisor-mode.md` uses a
  fenced command block; `session-resumption.md` uses a table cell; and
  `finding-adjudication.md` uses running prose. For the prose and table shapes,
  the check is a proximity condition in the same bullet, sentence, or cell,
  which is decidable on each.
- Which of the two admissible edits to the pinned `finding-adjudication.md`
  sentence to take — inserting before it, or rewriting it — is this task's local
  method, so it is decided here and not in the spec. Kill condition: if neither
  edit leaves the substring assertion passing, stop and surface rather than
  weakening the assertion, because that would change a verification mechanism
  and those are settled before approval.
- Survey what pins each surface before editing, the way the EXECUTE pins are
  surveyed above. `test_finding_adjudication_contract.py` asserts a literal
  sentence against a sliced region of `finding-adjudication.md` as a substring,
  so a preceding sentence survives it while a rewrite of that sentence does not
  — record which of the two is taken.
- In `supervisor-mode.md` § Single-agent fallback, name
  `no-implementer-installed` as what the controller records, and name
  `human-directed` as recording a human instruction with no testable
  precondition.
- In `state-schema.md`, document the container and state that an absent
  container means the guard does not enforce.
- State the unsupported-schema asymmetry on both surfaces the criterion names:
  on `state-schema.md`'s `schema_version` field row, and in
  `supervisor-mode.md` § Single-agent fallback beside the decline codes. Both
  halves each time — the exit tolerates the class and the verb refuses it, and
  the end-to-end outcome is that the run cannot pass the next wave boundary
  without a schema migration. Stating only the exit half is what the criterion
  was written to prevent.
- Add an eval case covering both calls, the authorship, and both decline codes.
- The EXECUTE section is pinned from two directions. A pack test slices it
  between `## Step 2. EXECUTE` and `## Step 3. GATES` and requires the literals
  `once per plan task` and `one implementer at a time`, so the new sentence uses
  that vocabulary rather than a second phrasing. A roster test requires the
  section to carry the verification-ledger pointer verbatim and forbids three
  retired plan-mutability phrasings in it; the new sentence must not reintroduce
  any of them. All of SKILL.md's firing sites sit inside `## Step 4. REVIEW`,
  so the pre-transition runs land outside the sliced EXECUTE region.
- Run `FORCE=1 make build-self` and verify the three copies of each edited
  `.apm/` file are byte-identical, trusting the parity check rather than the
  exit code. Projections are never edited directly.

**Done when:** a check scoped to `## Step 2. EXECUTE` finds
`loop-cohort dispatch-receipt` and the authorship sentence; every site that
instructs firing `wave-complete` also instructs
`loop-cohort check --phase wave-exit` immediately before the fire instruction
at that site; a check scoped to
`## Single-agent fallback` finds both reason codes; a check scoped to the
state-schema field table finds the absence rule; a check scoped to the
`schema_version` field row and one scoped to `## Single-agent fallback` each
find the asymmetry's exit half, verb half, and end-to-end outcome; a check
scoped to
`references/session-resumption.md` finds a row naming `amendment_pending` with
`approve-plan` and `schedule` as its route; every surface that instructs
`wave advance` states the accounting precondition, and no surface still
describes the call as unconditionally safe to replay; `evals/evals.json` parses
and
contains a case naming both calls, the authorship, and both codes; the three
copies of each edited file hash equal; and `python3 -m pytest
packs/core/tests/skills/work-loop/test_reference_routing.py
packs/core/tests/skills/work-loop/test_sequential_implementer_dispatch.py
tests/roster/test_verification_ledger_contract.py -q` passes.

### T5: Every clause is proved by its own removal

**Depends on:** T4

**Touches:** docs/specs/wave-complete-dispatch-receipts/notes/verification-ledger.md

**Tests:**
- `no stub (mode)` — manual QA.

**Approach:**
- Remove each clause added in T2 and T3 in turn — the run-identifier check, the
  mutual-exclusivity check, the verb's reason-code check, the index type check,
  each end of the index range check, the usable-partition check, the
  task-membership check, the partition-digest match, the guard's reason-code
  check, every verdict row, the accounting check on `wave
  advance`'s advancing branch, its absence from the already-applied branch, the
  precedence of the verb's existing refusals over it, the shared reading of
  `current_wave_index` on the advancing branch, the absent-container exemption
  inside the shared predicate, the verb's refuse-by-name handling of each
  malformed position, the `schedule` container
  creation, the
  `schedule` stale-record pruning, the amendment clearing, and the `status` key
  — re-running the suite after each.
- Record, per clause, the named test that turned red and the observed failure.
- Two of those clauses are passes rather than refusals, so "remove it" means
  invert it: the absent-container exemption is neutralised by making the
  advancing branch refuse an absent container, and the already-applied branch's
  unconditional pass by making it apply the accounting check. Both must redden
  a named case. A pass clause silently dropped from a mutation list is how an
  exemption ships unverified.
- A clause whose removal leaves the suite green returns to T2 or T3 for a
  discriminating assertion. Record that round too; a mutation table with no
  survivors and no recorded rounds is the shape a table gets when it was written
  from intent rather than run.

**Done when:** the ledger holds one row per clause, each naming a test and an
observed failure, and every row reporting a green survival names the task that
closes it. Amendment 0002 narrowed this from "and no row reports a green
survival": a survivor is closed by a discriminating assertion in a test file,
and this task's `Touches` is the ledger alone, so the unnarrowed clause could
not be discharged by the task carrying it. The obligation moved to T7, and T6
sits behind T7, so nothing ships with a survivor open.

### T7: The partition assertions discriminate the row they name

**Depends on:** T5

**Touches:** packs/core/tests/skills/work-loop/test_loop_cohort.py, docs/specs/wave-complete-dispatch-receipts/notes/verification-ledger.md

**Tests:**
- Each malformed-partition case asserts the word its **own** row owns, carried
  per parameter rather than once for the parametrized test. An empty partition
  must assert the unusable-partition wording; a non-list partition must assert
  it too; the wave-shape parameters must keep asserting `malformed`, because
  their rows correctly say `malformed` and a shared expectation reddens them on
  a green tree.

**Approach:**
- Added by amendment 0002. T5's sweep found one clause of the 34 it mutated
  survived green — the verb's usable-partition check — because both driving
  cases assert only the substring `schedule_waves`, which three different rows'
  messages all contain. The clause is correct; the assertion cannot tell the
  rows apart. This task lands the discriminating form T5 walked and reverted.
- Take the per-parameter shape. T5 recorded that a single expectation for the
  whole parametrized test reddens three wave-shape parameters on the unmutated
  tree, so the parameter list needs its own expected word per case.
- Re-run the survivor mutation after landing it, and record the row as caught,
  superseding T5's green row rather than editing it. T5's table keeps the
  survival, because the survival is the finding.
- While here, check the sibling assertions T5 flagged as the same shape —
  `test_wave_advance_refuses_a_malformed_partition`'s parameters — and give them
  the same treatment where a row owns a distinct word. Do not widen beyond
  assertions on rows this spec added.

**Inline proof — this task's whole output is a control, so it proves itself.**
- Positive: with the clause present, every case passes.
- Consequential negative: with the clause neutralised, a named case fails. T5
  measured 9 passed / 2 failed for the walked shape; this task reproduces that
  against what it actually lands.
- Neutralising proof: the mutation is the one T5 recorded as the survivor, so
  the before and after are directly comparable on one clause.
- Real entry path: the cases drive the `dispatch-receipt` CLI, not the validator.
- Retires when: the verdict rows stop owning distinct wording, at which point a
  per-row assertion has nothing to pin and the rows themselves need rework.

**Done when:** every malformed-partition case names a word its own row owns; the
suite is green on the unmutated tree; neutralising the usable-partition check
fails at least one named case, with the observed text recorded; and the ledger
carries a caught row superseding T5's green one.

### T6: The pack release surface agrees

**Depends on:** T7

**Touches:** packs/core/pack.toml, packs/core/.claude-plugin/plugin.json, docs/product/changelog.md

**Tests:**
- `no stub (mode)` — goal-based.

**Approach:**
- Apply a patch bump. `packs/AGENTS.md` § Version bump rule gives patch for
  changed content, minor for new primitives, major for removals; this change
  adds no file to the runtime export boundary that section defines, so it is
  changed content and there is nothing left to decide at push time.
- Derive the version immediately before pushing: this repository has collided on
  the same core version twice in one session, and a collision produces no
  conflict in either manifest because both sides write identical bytes.
- Bump both manifests together and write a topmost
  `## [core][<version>] — <date>` entry with a `Highlights` block. Word it at
  the strength the Objective states — the exit refuses an unasserted task — not
  as proof that dispatch occurred.
- After any conflict resolution, re-read the heading order and re-check it
  against both manifests: inserting a renumbered section can strand the landed
  version's heading above it with an empty body while every conflict marker is
  gone.

**Done when:** both manifests read the same patch-level version as the topmost
changelog entry, and `python3 -m pytest
tests/roster/test_wave4_durable_outputs_and_release.py
tools/test_build_site_routing.py -q` passes.

## Rollout

- **Delivery:** big bang within the pack release, reversible by reverting the
  version bump. Nothing is irreversible: no migration, no published event, no
  durable consumer state beyond the additive optional field.
- **Deployment sequencing:** the guard (T3) must not ship before the mutation
  (T2), or the wave exit refuses with nothing able to satisfy it. The task
  dependency chain enforces that order.
- **Mixed-version behaviour:** cohort state written by an earlier core version
  has no container, and the guard passes on it with a stdout notice. Such a run
  acquires the container at its next `schedule` — but a run mid-schedule
  advances rather than re-scheduling, which is why the advancing branch carries
  its own absent-container pass rather than relying on that. What bounds the
  class rather
  than leaving it open-ended. A run that starts on the new version and is
  finished by an older one ignores the field, which is why the Durable Outputs
  row calls it additive-and-ignored rather than jointly read.
- **Infrastructure / external systems:** none.

## Risks

- **The refusal strands a legitimate run.** The guard sits on a mandatory
  transition, so a false refusal blocks the loop rather than degrading it. The
  passing rows carry this — a recorded decline, an absent container, and a
  record for an already-left wave. An empty partition is **not** among them on a
  supported schema: round 8 made it malformed there, and the amendment crash
  window is handled by naming the recovery rather than by passing. On an
  unsupported schema it passes, because that row decides before any shape is
  read — which is the compatibility guarantee, not a second verdict. The
  transition-level assertion
  proves the refusal fires where intended. Keeping the accounting out of
  `--phase implement` is the other half: that phase is a push gate, not a wave
  gate. This is the risk that decides whether the change is safe to ship.
- **Any actor that can read the run identifier can discharge a wave.** `run_id`
  is a plaintext key in the spec directory, and a dispatched `implementer` ships
  with `Read` and `Bash` and is told to read that directory, so it — or
  repository content that influences it — can write records for any task in the
  current or an earlier wave, because nothing scopes a record to the task its
  writer was dispatched for. The partition digest does not help: it is an
  unkeyed function of state held beside the records. Accepted deliberately:
  scoping a record to its writer means establishing caller identity, which the
  spec routes to `Ask first` and which `loop-cohort` has no mechanism for. What
  the change buys is a durable per-task record of the choice, legible after the
  fact instead of inferable only from a transcript.
- **`human-directed` has no testable precondition.** It records a human
  instruction, and nothing bounds how many tasks in a wave may use it, so a wave
  can be discharged entirely by declines while the exit passes.
- **A repair round is discharged by the first pass's records.** `gates-failed`,
  `findings-remain`, and `blocker-applied` all re-enter `CODE-IMPLEMENTATION`
  without moving `current_wave_index`, and repair rounds are exactly where the
  controller most often works alone — so second and later passes through a
  wave's exit assert nothing new. Registered as a follow-on. Not closed here
  because scoping a record to a round needs a counter advancing on all three
  edges, and `implementation_retry_count` advances on one, so building on it
  would look like a control without being one.
- **Removing the container is a silent per-run off-switch.** The pass on an
  absent container cannot be told apart from a pass on a container that was
  deleted, so the party the guard constrains can disable it by deleting one key,
  and nothing records that. This is cheaper than forgery, which at least leaves
  the per-task record that is the change's stated value. Accepted because the
  only candidate evidence — a provenance marker written by the same actor to the
  same file — is equally removable, and because conditioning the pass on
  evidence that does not exist would refuse every genuinely pre-upgrade run. It
  is disclosed in the spec's Objective, not only here.
- **A wave advanced past before the exit fires is now checked too.** `wave
  advance` applies the same accounting predicate on the branch that moves the
  pointer, so the bypass this plan previously disclosed and deferred is closed.
  What remains open, deliberately: the already-applied branch exits zero
  regardless, because the documented crash-resume replay re-issues the verb
  after the pointer has moved. A controller that advances, has its records
  removed, and then replays therefore still advances — a narrower window than
  the bypass it replaces, and the alternative is a dead end in crash recovery.
- **An enforcement-off exit leaves no durable trace.** The notice and the
  `status` key are both ephemeral and read by the constrained party, and for
  state whose `schema_version` is unsupported `status` refuses outright. A
  durable in-state trace would be a side effect written on a transition, which
  is ADR-0061 Option B. Registered as a follow-on.

## Changelog

- 2026-09-17: initial plan.
- 2026-09-17: revised from review round 1 (19 sustained findings). Named the
  verb; corrected the false claim that an `implementer` cannot hold the run
  identifier; added the init-produced-state and byte-comparison criteria;
  bounded the wave index; completed the `Touches` fields.
- 2026-09-17: revised from review round 2 (9 blockers, all inside the round-1
  repairs). Moved the disclosure off the engine; discovered the frozen golden
  row is an *unscheduled* state, so passing silently with no schedule preserves
  it; dropped the planned fixture edit and new row; added a schedule
  discriminator.
- 2026-09-17: revised from review round 3 (6 blockers, again inside the round-2
  repairs) and restructured rather than patched. Round 3 showed the cause was
  not any individual criterion but the order of derivation, so every decision
  here was taken from a code read first. The guard's criteria became a
  verdict table with disjoint preconditions, and a test asserts the
  partition — round 3's blockers were criteria that overlapped with opposite
  consequents, which that form cannot express. The discriminator changed from
  `plan_hash` to a digest of `schedule_waves`, because `canonical_contract`
  normalizes only four things and a prose edit would otherwise invalidate
  correct records; holding records under that digest also means `schedule`
  never has to rewrite them, which closes the wipe reading of "establish the
  container". The forward-wave bound was closed, so one pre-run batch can no
  longer discharge every exit. The no-write invariant became one criterion over
  the enumerated refusal set. The guard now validates a decline's reason too,
  instead of trusting the write path. The claim that `check` could not report a
  passing guard was corrected — `cmd_check` emits `message` — so the
  absent-container notice now prints at the exit and `status` supplements it.
  The record dropped its run identifier, which no reachable state could
  falsify. Repair-round re-entry and the `status` schema-version gap were
  disclosed and registered rather than half-closed.
- 2026-09-17: restructured again from review round 4, which surfaced a caller
  nobody had enumerated. `tools/hooks/pre-pr.py` and its packaged copy run
  `check --phase implement` for every `docs/specs/*/state.json` on every push,
  ungated by the engine state, so putting the accounting in that phase would
  have made a wave-exit guard into a repository-wide push gate here and for
  every adopter. The accounting moved to a new `wave-exit` phase and `implement`
  is now preserved exactly, which also makes the frozen golden row untouched
  literally rather than by argument. Round 4 also showed the digest alone cannot
  scope a record across a contract amendment — an amendment at wave index zero
  with no completions reproduces the identical partition — so the amendment path
  clears the container, which additionally bounds the stored set to one live
  partition and removes the need for a size cap. The notice was given a caller:
  the engine discards a passing guard's text and no step invoked `check` for it,
  so GATES now runs the pre-exit check. The verdict table gained a row for a
  malformed current wave, found by widening the partition walk's domain over
  field types rather than over the rows — the earlier walk could only find
  overlaps, never gaps. The verb gained an unusable-partition
  refusal, the guard layer's existing non-negative-integer helper replaced an
  invented predicate, the no-write property now binds the verb's whole refusal
  set, the accepted lower index bound got its own criterion, both artifacts
  carry their template tier declarations, the measurement has one home, each
  task now regenerates the projections it invalidates, and the four accepted
  limits are disclosed in the spec's Objective rather than only in these Risks.
- 2026-09-17: revised from review round 9 on both lanes, then swept for decaying
  structural counts. Both lanes independently opened on the same state: the
  round-8 rewrite made an empty partition malformed while a Boundaries rail
  still required the guard to pass "no schedule persisted", and those are one
  state because an absent `schedule_waves` reads as `[]`. The verdict is now
  refuse in both places, and the justification changed too: the claim that an
  empty partition could only come from a hand-write was false, because
  `begin_contract_amendment` writes `schedule_waves: []` and the engine applies
  that cohort mutation before its own state write, leaving a crash window. The
  spec now names that window and its recovery — `amendment_pending`,
  `approve-plan`, then `schedule` — and requires
  `references/session-resumption.md` to carry a row for it, since it has none.
  `current_wave_index` gained one declared reading for both the branch selector
  and the accounting predicate, because `cmd_wave_advance` reads it through
  `int()` while the predicate uses the guard layer's validation, and the two
  disagree on `"1"`, `1.9`, `True` and `None`. The advancing branch gained an
  absent-container pass, without which every in-flight pre-receipts run would
  strand at its next boundary with no migration step to repair it. The
  forward-pointer route is now disclosed in Boundaries at the same strength as
  forgery and container deletion. The verb's refusal enumeration went from four
  to all of them, and its third branch is named. The partition walk's
  acquisition vocabulary was an inert constant; it now carries the
  read-refusal row's scope as an assertion that reddens under a widened
  `readable`.
- 2026-09-17: **amendment 0001**, the first controlled contract amendment on this
  plan. Authority:
  [`notes/amendment-0001-owner-authority.md`](notes/amendment-0001-owner-authority.md).
  Reason: § 8.2 of the verification ledger. T1 had already completed and its
  section is immutable; the amendment preserved it with an evidence binding and
  cleared the schedule, so rescheduling emits T2 onward and treats T1 as met.
  One clause changed. T3's `Done when` required that *no statement in the tree*
  assert the `implement`/`wave-complete` coupling, which could never be
  discharged: `loop-infrastructure-phase-1/plan.md` states it at six lines and
  is Shipped and frozen, and this plan's Constraints require it unedited. The
  clause now reaches live, editable surfaces and names all five of them, where
  it had named three — T1's exhaustive read found `loop-engine.py:1012` and a
  docstring at `test_loop_engine.py:1615` missing from the list. The
  guard-table entry was already covered by the retarget clause, so the
  operative omission was the test docstring, which nothing else in T3 reached.
- 2026-09-18: **amendment 0002**, adding a task. Authority:
  [`notes/amendment-0002-owner-authority.md`](notes/amendment-0002-owner-authority.md).
  Reason: § 13 of the verification ledger. T5's sweep applied 34 mutations and
  33 reddened a named test; one survived green — the verb's usable-partition
  check — because both driving cases assert only the substring `schedule_waves`,
  which three different rows' messages all contain, so the case passes whichever
  row refuses. The clause is correct and the assertion cannot discriminate.
  T5's `Touches` is the ledger alone and the repair is a test edit, so the plan
  anticipated the survivor (its `Approach` says one "returns to T2 or T3") while
  its task graph could not express the repair, T2 and T3 being complete and
  immutable. Three changes: T7 added, depending on T5, to land the
  discriminating assertion T5 walked and reverted; T6 re-pointed from T5 to T7
  so the release bump stays last; and T5's `Done when` narrowed to require every
  green survival to name the task that closes it, which is the one started-task
  edit and moves the obligation rather than dropping it. T1 through T4 stay
  complete and immutable, and T5's table keeps the green row, because the
  survival is the finding.
  Found by T1 rather than by a review round, which is what a discovery task is
  for; surfaced to the owner rather than reinterpreted, because a `Done when`
  clause is a verification obligation and contract.
- 2026-09-17: revised from review round 10, run on two Codex reviewers with
  disjoint focus sets. Both blockers on the contract lane were drift from the
  round-9 repairs themselves. The Boundaries sentence stating that an empty
  `schedule_waves` is never exempt was unconditional, while the
  unsupported-schema row passes before any shape is read — so an unsupported
  state with an empty partition had two contract verdicts. The sentence is now
  scoped to the supported-schema case, which is the compatibility guarantee
  rather than a second verdict; the reviewer's remedy, narrowing the pass row,
  was not taken because it would break the criterion that no state
  `check --phase implement` passes today may start refusing. The same sentence
  also claimed a run at this exit has a persisted schedule "by construction",
  which the crash-window prose added in the same commit refutes; the claim is
  gone and the reason for refusing is now the silent pass direction.
  A fourth off-switch was found and disclosed: an actor who can write
  `state.json` sets an unsupported `schema_version`, fires the transition, and
  restores the value, leaving nothing durable behind. Container deletion's
  disclosure was corrected too — it is a restorable window, not a run-long
  state. The claim that `_validate_run_id` covers "every cohort mutation" was
  narrowed, because `reset` and `init` do not call it. Every branch round 9
  added gained a T3 case, the bounding pair is now driven through
  `wave advance`'s own channel rather than only the guard's, the verb's
  malformed-position criterion gained T2 carriers, and T5's mutation list gained
  the two *pass* clauses with an explicit instruction to invert rather than
  delete them.
