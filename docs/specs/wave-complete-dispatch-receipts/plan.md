# Plan: wave-complete dispatch receipts

- **Spec:** [`spec.md`](spec.md)
- **Status:** Drafting <!-- Drafting | Approved | Executing | Done -->
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
each of the four surfaces that instruct firing it:
`references/supervisor-mode.md`, `references/session-resumption.md`,
`references/finding-adjudication.md`, and the two repair paths in `SKILL.md`.

**The guard is an eight-row verdict table over two named well-formedness
predicates.** Four rounds produced criteria that overlapped or left gaps, and
this table's own first draft did both — an empty partition with a non-mapping
container satisfied two rows with opposite verdicts, and a malformed wave
element such as `[123]` satisfied none, falling through to the opaque
`@contained` refusal. So the partition is checked rather than asserted: 1,152
constructed states were walked, varying the type of `schedule_waves`, the type
of its current element, the presence and type of the container, and the type and
range of the pointer — zero overlapping, zero uncovered, every row reachable.
T3 carries that walk as a test, and its domain deliberately comes from the
fields the rows read rather than from the rows.

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
- **Eight verdict rows over two named well-formedness predicates.** Traces to:
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
- **The notice prints from `check --phase wave-exit`, called by GATES before the
  transition.** Traces to: the absent-container row and the GATES criterion.
  `cmd_check` emits a passing guard's `message`; the engine's adapter discards
  it, and no existing step invokes this verb, so without the GATES step the
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

Traces to: the verb's criteria, the verdict rows, the GATES criterion, and the
status criterion.

One new `loop-cohort dispatch-receipt` verb, following the shape both analogous
mutations already use: state lock held for the write, `--expect-run-id`
validated before anything is written, and a refusal that names what it
rejected. Receipt and decline are mutually exclusive on one invocation. The verb
takes the wave index explicitly and accepts a non-negative integer up to and
including the current wave index — a wave already left can be recorded against,
because `wave advance` is not coupled to this guard and the record would
otherwise be unobtainable; a wave not yet reached cannot, because `schedule`
prints the whole partition, so a forward index would let one pre-run batch
discharge every exit. An unusable partition — empty, or a pointer that is not a
valid index into it — is refused by name rather than indexed into.

`--phase wave-exit` is a fourth member of `PHASES`, carrying the verdict table.
`--phase implement` keeps its current behaviour. The engine's
`("code", "wave-complete")` guard-table entry points at the new phase.

`loop-cohort status` gains one key reporting whether receipts are enforced, in
both its default and `--json` forms.

### Failure, edge cases & resilience

Traces to: the eight verdict rows, the verb's unusable-partition refusal, and
the byte-equality criteria.

- **Interrupted dispatch.** Best-effort by decision. A controller that crashes
  between the implementer returning and the record being written has no record,
  and the remedy is to write it, not to recover it. This is the Option B line.
- **Contract amendment.** The container is cleared, so no pre-amendment record
  accounts for anything — including the case where the re-scheduled partition is
  byte-identical and its digest therefore unchanged.
- **Re-schedule without amendment.** A partition-preserving re-schedule keeps
  records; a partition-changing one removes the stale ones.
- **A wave advanced past without its exit check.** `wave advance` can move the
  pointer before the exit fires. Not closed here — a follow-on — but a record
  stays writable for it so the record is not also lost.
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

## Discovery channel

T1 is a **declared discovery task**. Exact helper names, fixture shapes, and
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
  hook every adopter has wired. Safe because the verdict table validates shape
  rather than trusting the schema, so it is total regardless of
  `schema_version`. Refined: none — this was settled before approval, so it is
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

### T1 (discovery): The guard surface is mapped and the pinned files are settled

**Depends on:** none

**Touches:** docs/specs/wave-complete-dispatch-receipts/notes/verification-ledger.md

**Tests:**
- `no stub (mode)` — goal-based.

**Approach:**
- Confirm the pre-PR hook's `implement` leg is ungated by the engine state and
  runs for every `docs/specs/*/state.json`. The separate-phase design rests on
  it. If it does not hold, stop and surface.
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

**Done when:** the ledger answers all six predeclared questions, each naming the
surfaces read rather than a grep pattern; records the golden confirmation; and
records one run of the dispatch-rate generator.

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
- A non-matching `--expect-run-id` exits non-zero.
- One case per refusal above asserts `state.json` is byte-identical to its
  pre-invocation content, and one case asserts it for a refusal raised by the
  state read itself, so the property covers the verb's whole refusal set.
- Recording the same triple twice exits zero both times and leaves exactly one
  record.
- `init` leaves the container present; `schedule` leaves the container present.
- A `schedule` run producing the same partition leaves an earlier record
  present and unchanged; one producing a different partition leaves no record
  under the superseded digest.
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

**Touches:** packs/core/.apm/skills/work-loop/scripts/_loop_guards.py, packs/core/.apm/skills/work-loop/scripts/loop-cohort.py, packs/core/.apm/skills/work-loop/scripts/loop-engine.py, .claude/skills/work-loop/scripts/_loop_guards.py, .agents/skills/work-loop/scripts/_loop_guards.py, .claude/skills/work-loop/scripts/loop-cohort.py, .agents/skills/work-loop/scripts/loop-cohort.py, .claude/skills/work-loop/scripts/loop-engine.py, .agents/skills/work-loop/scripts/loop-engine.py, packs/core/tests/skills/work-loop/test_loop_guards.py, packs/core/tests/skills/work-loop/test_loop_guards_parity.py, packs/core/tests/skills/work-loop/test_loop_cohort_cli.py, packs/core/tests/skills/work-loop/test_loop_engine.py

**Tests:**
- One case per verdict row, asserting the exit code and the content of both
  streams.
- A partition-property case: cohort states constructed by varying the type of
  `schedule_waves`, the type of its current element, the presence and type of
  the container, and the type and range of the pointer; every constructed state
  satisfies exactly one row, and every row is satisfied by some state. The
  domain comes from the fields the rows read, not from the rows.
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
- Integration, in `test_loop_engine.py`: the real `wave-complete` transition out
  of `CODE-IMPLEMENTATION` exits non-zero against a state with one unaccounted
  task.
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
one, the three copies of each edited `.apm/` file hash equal, and
`python3 -m pytest packs/core/tests/skills/work-loop/test_loop_guards.py
packs/core/tests/skills/work-loop/test_loop_guards_parity.py
packs/core/tests/skills/work-loop/test_loop_cohort_cli.py
packs/core/tests/skills/work-loop/test_loop_engine.py
packs/core/tests/skills/work-loop/test_golden_fixtures.py -q` passes.

### T4: The controller-facing surfaces carry the calls, the authorship, and the codes

**Depends on:** T3

**Touches:** packs/core/.apm/skills/work-loop/SKILL.md, packs/core/.apm/skills/work-loop/references/supervisor-mode.md, packs/core/.apm/skills/work-loop/references/state-schema.md, packs/core/.apm/skills/work-loop/references/session-resumption.md, packs/core/.apm/skills/work-loop/references/finding-adjudication.md, packs/core/.apm/skills/work-loop/evals/evals.json, .claude/skills/work-loop/SKILL.md, .agents/skills/work-loop/SKILL.md, .claude/skills/work-loop/references/supervisor-mode.md, .agents/skills/work-loop/references/supervisor-mode.md, .claude/skills/work-loop/references/state-schema.md, .agents/skills/work-loop/references/state-schema.md, .claude/skills/work-loop/evals/evals.json, .agents/skills/work-loop/evals/evals.json

**Tests:**
- `no stub (mode)` — goal-based.

**Approach:**
- In `SKILL.md` § Step 2. EXECUTE, state `loop-cohort dispatch-receipt` as
  required once per plan task, using the section's existing cardinality
  vocabulary, and state that the controller records it and an `implementer` does
  not record its own. The section already declares what the controller retains,
  so this extends that sentence rather than adding a trust mechanism.
- At each of the four surfaces that instruct firing `wave-complete` — the two
  repair paths in `SKILL.md`, `references/supervisor-mode.md`,
  `references/session-resumption.md`, and
  `references/finding-adjudication.md` — require
  `loop-cohort check --phase wave-exit` immediately before the transition. Do
  not put it in GATES: GATES runs after that transition, so a check placed
  there could never precede it.
- In `supervisor-mode.md` § Single-agent fallback, name
  `no-implementer-installed` as what the controller records, and name
  `human-directed` as recording a human instruction with no testable
  precondition.
- In `state-schema.md`, document the container and state that an absent
  container means the guard does not enforce.
- Add an eval case covering both calls, the authorship, and both decline codes.
- The EXECUTE section is pinned from two directions. A pack test slices it
  between `## Step 2. EXECUTE` and `## Step 3. GATES` and requires the literals
  `once per plan task` and `one implementer at a time`, so the new sentence uses
  that vocabulary rather than a second phrasing. A roster test requires the
  section to carry the verification-ledger pointer verbatim and forbids three
  retired plan-mutability phrasings in it; the new sentence must not reintroduce
  any of them. The GATES step lands outside the sliced region.
- Run `FORCE=1 make build-self` and verify the three copies of each edited
  `.apm/` file are byte-identical, trusting the parity check rather than the
  exit code. Projections are never edited directly.

**Done when:** a check scoped to `## Step 2. EXECUTE` finds
`loop-cohort dispatch-receipt` and the authorship sentence; every one of the
four `wave-complete` firing surfaces carries `--phase wave-exit` within the
instruction block that fires the transition; a check scoped to
`## Single-agent fallback` finds both reason codes; a check scoped to the
state-schema field table finds the absence rule; `evals/evals.json` parses and
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
  check, each of the eight verdict rows, the `schedule` container creation, the
  `schedule` stale-record pruning, the amendment clearing, and the `status` key
  — re-running the suite after each.
- Record, per clause, the named test that turned red and the observed failure.
- A clause whose removal leaves the suite green returns to T2 or T3 for a
  discriminating assertion. Record that round too; a mutation table with no
  survivors and no recorded rounds is the shape a table gets when it was written
  from intent rather than run.

**Done when:** the ledger holds one row per clause, each naming a test and an
observed failure, and no row reports a green survival.

### T6: The pack release surface agrees

**Depends on:** T5

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
  acquires the container at its next `schedule`, which bounds the class rather
  than leaving it open-ended. A run that starts on the new version and is
  finished by an older one ignores the field, which is why the Durable Outputs
  row calls it additive-and-ignored rather than jointly read.
- **Infrastructure / external systems:** none.

## Risks

- **The refusal strands a legitimate run.** The guard sits on a mandatory
  transition, so a false refusal blocks the loop rather than degrading it. Four
  passing rows carry this — recorded decline, empty partition, absent container,
  and a record for an already-left wave — and the transition-level assertion
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
- **A wave can be advanced past without ever being checked.** `wave advance` is
  not coupled to this guard. Registered as a follow-on; a record stays writable
  for an already-left wave so it is not lost as well.
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
  seven-row verdict table with disjoint preconditions, and a test asserts the
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
  so GATES now runs the pre-exit check. The verdict table grew an eighth row for
  a malformed current wave, found by widening the partition walk's domain from
  1,152 states over field types rather than over the rows — the earlier walk
  could only find overlaps, never gaps. The verb gained an unusable-partition
  refusal, the guard layer's existing non-negative-integer helper replaced an
  invented predicate, the no-write property now binds the verb's whole refusal
  set, the accepted lower index bound got its own criterion, both artifacts
  carry their template tier declarations, the measurement has one home, each
  task now regenerates the projections it invalidates, and the four accepted
  limits are disclosed in the spec's Objective rather than only in these Risks.

