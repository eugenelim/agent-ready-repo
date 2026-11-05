# Spec: Hand a captured item to its owner or close it, and record which

- **Status:** Draft
- **Owner:** eugenelim
- **Mode:** full
- **Plan:** [`plan.md`](plan.md)
- **Brief:** none
- **Discovery:** opportunity:work-item-promotion-routing
- **Constrained by:** [FEAT-0007 § For the spec to decide](../../product/intents/FEAT-0007-work-item-promotion-routing.md) — the grounds for each decision below; [docs/specs/work-item-capture/spec.md](../work-item-capture/spec.md) § D6 and § D10 — the stored-command rules, the stored-path set, and the disclosed merge path this spec's read path and envelope answer; [CAP-0005 § Boundary](../../product/intents/CAP-0005-work-item-capture-and-disposition.md) — every destination is an existing owner with its own contract
- **Depends on:** spec:work-item-capture
- **Contract:** none
- **Shape:** mixed

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.
>
> **Not every section is contract.** `Agent Rules`, `Testing Strategy` and
> `Acceptance Criteria` are what a completion gate reads, and an amendment
> changes them. `## Decisions this spec makes` is contract on the same footing:
> criteria dereference § D1, D2, D4–D11 for their meaning, so those decisions
> change only by amendment. `Outcome`, `What Changes`, `Durable Outputs`,
> `Follow-ons` and `Assumptions` are working material: they orient a reader and
> an author corrects them in place as the work teaches, without an amendment
> and without a review round. `Boundaries` restates fences other artifacts own
> and is working material on the same terms.

## Outcome

A triaged captured item reaches the owner that already handles work of its
shape, or is closed because it should go nowhere, and the terminal disposition
records which. Success is one outcome with a guardrail, per
[FEAT-0007](../../product/intents/FEAT-0007-work-item-promotion-routing.md):
the share of captured items still untriaged after a drain falls, without
dispositions an informed reader would dispute.

## What Changes

- **The store gains a drain-side reader** — open captures with their records
  and terminal state, in `knowledge_store.py`'s owning skill: the input every
  drain offer assembles from.
- **A drain module joins the store's skill** —
  `packs/core/.apm/skills/project-knowledge/scripts/promotion_drain.py`:
  offer assembly (including the read-path prose re-run), the per-item decision
  function, and the execution envelope for stored commands, co-located with
  the store API and the capture validator it re-uses.
- **The work-intake skill gains the drain procedure** — its `SKILL.md` gains
  the operator-facing sequence: offer, classify, confirm, transact, commit
  disposition.
- **Closure and disposition mapping** — three closure grounds with tests
  (§ D5) and a terminal-disposition mapping that adds no vocabulary value
  (§ D6).
- **Durable surfaces** — the work-item reference guide entry, the
  knowledge-capture architecture entry, and `docs/architecture/security.md`,
  which records the § D10 prose residual as settled by this spec's read path.
- **Follow-up hardening (post-review)** — four sustained findings from the
  merged delivery's review: a route with no dispatch wired holds instead of
  recording `routed` (`AC-0025`); a classification is validated against the
  classify table's six members (`AC-0026`); the superseded closure ground's
  mechanical test runs in the drain (`AC-0027`); a stale workspace lock is
  recovered so the re-run completes (`AC-0028`).

## Boundaries

This spec owns the drain: what it routes, what it closes, what it holds, and
the safety of every effect it commits. It does not own:

- **Governance record routing.** A sibling's, per FEAT-0007 § Non-goals;
  `docs/specs/governance-item-record-routing/spec.md`. `AC-0007` holds such items
  until it ships.
- **Telling whether an existing artifact already covers the item.**
  `docs/specs/duplicate-coverage-offer/spec.md`'s. Until it ships, promotion
  may create a second artifact for covered work, which CAP-0005
  § Decomposition decisions accepts as the shipping state.
- **Doing the work.** Every destination is an existing owner with its own
  contract, per CAP-0005 § Boundary.
- **What a stored command may contain.** Settled at write time by
  `docs/specs/work-item-capture/spec.md` § D6 — the argv structure, the
  command allowlist, the option refusal, and the argument rules. This spec
  does not re-decide any of them.

  **Execution safety is this spec's**, because write-time validation cannot
  establish a runtime property. That spec's § D6 hands over **six** residual
  controls by name, and the criteria below carry them: post-resolution
  repository confinement, environment neutralisation, a resource cap, a
  re-check of the stored command against § D6's argv rules before it runs,
  which matcher `grep` runs, and the treatment of the command's output.

  Its § D10 separately discloses a residual it does **not** hand over: no
  write-time prose control is re-established at execution. That residual is
  settled here, by § D4's read-path re-run of all three controls — a merged
  record's prose reaches no classification, reasoning, or durable write
  unscreened. The re-check exists because the store is committed repository
  content: a record can arrive by merge or contributor branch without any
  write-time validator seeing it, and the envelope's confinement, environment
  and resource bounds never inspect `argv[0]`. Re-checking is not re-deciding
  — this spec applies the capture spec's rules through its validator, and
  authors none of its own.

- **The in-repository-sensitivity residual.** Confinement refuses a path
  resolving *outside* the repository; an in-repository file never does, and no
  rule decides whether it is sensitive. That residual stays disclosed and
  unowned by `docs/specs/work-item-capture/spec.md` § D6; this spec adds no
  sensitivity classification and inherits the disclosure unchanged.

## Decisions this spec makes

Assigned by
[FEAT-0007](../../product/intents/FEAT-0007-work-item-promotion-routing.md)
§ For the spec to decide, which holds the grounds for each; the six residual
controls `docs/specs/work-item-capture/spec.md` § D6 hands over by name; and
that spec's § D10, whose disclosed prose residual § D4 below settles. Each
decision is contract: criteria dereference it by number.

### D1 — the terminal disposition is the commit point; re-running the drain is the one recovery path

The effects, in order, are the intake transaction — materialize under the
workspace-writer lock, then dispatch — followed by the terminal disposition.
The disposition is the sole irreversible effect and commits last, so no crash
can close a capture without its handoff. A crash before the disposition
leaves the capture open, and the recovery path is to re-run the drain: an
open capture is re-offered; the transaction's materializer treats an artifact
already on disk as materialized, per work-intake's rule that an existing
artifact keeps its own path; a repeated dispatch is a repeat invocation over
the same durable artifact, convergent rather than duplicative; and the
store's append is idempotent for an identical disposition, which
`knowledge_store.py`'s `_append_terminal_disposition` returns unchanged
without writing. The residual cost of the ordering is a possible repeated
processor invocation after a crash between dispatch and disposition; it is
bounded, visible, and strictly cheaper than the unrecoverable state the
opposite ordering admits — a capture closed with no handoff, which no later
action can repair because the store refuses a second terminal event.

A closure produces the terminal disposition alone and sits inside the unit
trivially. The duplicate-coverage offer sits outside the unit: a human gate
ahead of materialization, whose acceptance enters the sequence at the
transaction.

A route commit requires a real processor dispatch. A drain invoked with no
dispatch wired — no `transact` override and no `dispatch_processor` — holds
the item and records no disposition, on both route branches, and the hold
precedes every transaction effect: no lock is taken, no artifact is
materialized. A `routed`
disposition with no handoff is exactly the unrepairable state this section's
ordering exists to prevent, and a silent no-op default must not be able to
reach it. The work-intake procedure supplies the real dispatch; its § 8
records how the operator wires it at invocation.

The workspace-writer lock the transaction takes must not outlive its owner.
A lock left by a process that no longer exists is stale, and the transaction
recovers it — the lock records its owner's pid, and a stale owner is
detected by liveness probe; the removal re-verifies, immediately before the
unlink, that it removes the same lock it probed — same inode, same pid
payload — and refuses with lock-busy when the lock changed underneath,
patterned on the sibling `intent_rename.py` `_normalise_old_claim` defense —
then acquisition is retried once, so the
re-run this section names as the one recovery path completes instead of
returning lock-busy forever. A lock whose owner is alive is never taken; a
reused pid is bounded by the lock's short critical section and is recorded
as a residual risk, not a recovery trigger. The re-verify-to-unlink window
itself is a bounded residual on the same terms: two concurrent recoverers
that both verify against the same stale lock before either acts can still
race — the pattern the sibling writers' refusals name — and the token-keyed
reclaim `project-knowledge`'s own `_statelock.py` uses would close it, but
that changes the shared lock's payload protocol every taker reads, and so
belongs to the lock protocol's owner, not this spec. A lock whose payload
carries no
parseable pid is never removed — its owner is treated as live — and the
transaction's own acquisition closes the create-then-write window — the
lock is published by an atomic link of a pid-complete temporary file, the
sibling `_acquire_claim` link-publication step; the temporary's
holder-unique name — pid and a random token, created fresh on every
acquisition — is this spec's own mechanism, so
concurrent acquirers never collide on it and a killed creator's orphan
never blocks a later acquisition; every
lock it leaves carries its pid; a foreign pid-less lock left by a writer
killed mid-acquisition is a disclosed residual requiring manual removal,
strictly narrower than the permanent wedge this rule removes.

### D2 — `work_item.shape` selects the route family; per-shape fields select within it

- `defect` routes to the defect processor (`bug-fix`), gated on § D10's
  readiness condition.
- `decision` routes to the governance sibling, and is held until that spec
  ships (`AC-0007`).
- `question` is classified by the existing work-intake classification over
  the record's fields — `statement`, `finished_state`, `answered_by`,
  `necessity_rationale` — which selects among the shapes of work-intake's
  classify table. This spec adds no second routing table: that table is the
  authority on which input shapes exist and what each produces.

An item whose fields do not resolve to exactly one route is held
(`AC-0006`). A required field absent, or a field contradicting the route — a
defect whose `verification_route` fails the pre-execution re-check — holds
the item rather than routing it. Staleness is not a routing input: it is a
closure ground with its own test (§ D5).

### D3 — the drain is an operator-invoked procedure; the classifier is called, not extended

A drain runs when an operator invokes it. Per item it reads the offer — the
record, the re-check verdict, the envelope evidence, the prose re-run
verdicts — classifies, confirms (§ D11), transacts, and commits the
disposition. A capture write never dispatches and never routes; nothing
routes automatically at capture time. The drain derives work-intake's
bounded signals from the record's structured fields and hands them to the
existing classification; it holds only the shape-to-family mapping § D2
fixes, which is this spec's rule, and no per-shape routing table of its own.

The classification's output is a member of work-intake's classify table, by
name: one of `direct-light`, `spec`, `brief`, `remember`, `defect`,
`incomplete` — the six shapes that table's § 4 rows fix, each naming the
row, not a free string. An output that is not one of the six is not a
classification: the item is held as unroutable (§ D2), never routed on a
string no table row owns. A member whose row is non-dispatchable —
`remember`, `incomplete` — holds the item the same way, because no route
exists for the drain to commit (§ D1's dispatch rule above).

### D4 — the read path re-runs all three write-time prose controls before the record influences anything

The merge path `docs/specs/work-item-capture/spec.md` § D10 discloses reaches
the store with no write-time validation, so the drain re-runs, on the same
field set the write path scans — the set that spec's free-text-scan criterion
("Every free-text field a `work-item` record carries…") derives from the
schema, stated once there and nowhere else — all three controls that spec's
§ D10 names: `assert_persistable_text`'s eight-pattern privacy scan, the
instruction-shape refusal, and the framing of item content as data. They run
when the offer is
assembled, before the record influences any classification, reasoning, or
durable write. A record failing the privacy scan or the instruction-shape
refusal is refused as a routing input and held, with the refusing control
named in the drain's report (`AC-0023`); the framing governs every
presentation of record prose to a reasoning or classification step
(`AC-0024`), matching the write path's own data-framing discipline.

What a stored path may influence: only the execution envelope's confinement
checks and the command's own operands — never a classification input, never a
write target. What is carried through unexecuted: the stored command itself,
which no classification or reasoning step runs; only the envelope executes
it, after the re-check. Record prose copied into a materialized artifact is
carried as data and has already passed the re-run scan.

### D5 — three closure grounds, three tests, one operator

- **Overtaken** — the work the item names already exists at or beyond its
  `finished_state`. Test: the item's own evidence shows it — a defect
  carrying a `verification_route` run under the envelope no longer shows the
  deviation, or the named artifact at its stated location shows the finished
  state. The closure records what was run or read and what it showed.
- **Superseded** — a later capture or an existing live artifact records the
  same work. Test: the cited capture id resolves in the store, or the cited
  artifact path exists — a mechanical test the drain itself
  runs before the disposition commits; a superseded closure whose citation
  resolves nowhere is refused, whatever the operator attests. The closure
  input for this ground carries the citation as a required field —
  `citation` holding one of `{"capture_id": <id>}` or
  `{"path": <repository-relative path>}` — and an absent citation resolves
  nowhere and is refused. That an existing artifact is live — not withdrawn,
  tombstoned, or itself superseded — is the operator's attestation, riding
  the closure's evidence; the drain's mechanical check is resolution and
  existence, never liveness. The operator's `test_passes` verdict remains a
  veto on every ground, this one included: a false verdict refuses the
  closure even when the citation resolves, and a resolving citation is
  additionally required, so both gates must pass. The closure
  records the citation.
- **Falsified** — the premise the item rested on no longer holds. Test: the
  change that falsified it is named — a commit, an artifact state, an
  answered question — and the item's own evidence corroborates it. The
  closure records the named change and the corroboration.

Who runs each test: the superseded ground's test is mechanical and the
  drain's — it holds the store and can resolve the citation itself, and a
  closure proposal on that ground is refused when the citation resolves
  nowhere. The overtaken and falsified grounds' tests are the operator's:
  the operator runs or reads what the ground names and supplies the verdict,
  and the drain records that verdict and the evidence, never re-deriving it.

Where the closure's record lives: the ground rides the disposition's reason
code, and no evidence citation rides beside it — § D6's enumeration of
exactly three reason codes is what keeps a citation out. The store's
reason-code rule excludes a path outright (its charset admits no `/`) and a
capture id beside its ground prefix (the 80-character bound); a commit hash,
a citation form the falsified ground names, would pass the store's rule —
§ D6's enumeration, not the store, excludes it. The evidence — what was run or read and
what it showed, the citation, the named change and its corroboration — rides
the drain's run report, beside the closure it justifies. That follows the
capture spec's own discipline for a justification its event shapes cannot
carry: it lives in the run's own output, never in a widened store event.

Who may close: the attended operator, one item at a time, each closure
confirmed with its ground and evidence. A closure whose stated ground fails
its test — the deviation still shows, the citation does not resolve, the
named change does not exist — is refused (`AC-0003`).

### D6 — overtaken and falsified closures record `rejected`; the ground rides in the reason code

The terminal vocabulary gains no value. A routed item records `routed`; a
superseded-ground closure records `superseded`; overtaken and falsified
closures record `rejected`, with the ground in the reason code
(`closed_overtaken`, `closed_falsified`, `closed_superseded` — each within
the store's reason-code rule). `promoted` stays the review path's and is
never written by a drain; `duplicate` stays the duplicate-coverage sibling's.
The promoted-or-pruned split CAP-0005 § Riskiest assumption reads is
therefore: promoted side `promoted` and `routed`; pruned side `rejected`,
`superseded`, `duplicate`. Designating `rejected` rather than adding a sixth
value leaves the frozen vocabulary every store reader validates unchanged,
and the ground — the distinguishable bit — is exactly what the reason code
carries.

### D7 — the execution envelope: confined, neutralised, capped

- **Confinement.** Before a stored command runs, the envelope resolves every
  member of the stored-path set `docs/specs/work-item-capture/spec.md` § D6
  defines — every argv element after `argv[0]` except `grep`'s index-1
  pattern, plus `verification_route.path` — against the repository root,
  following symlinks, and refuses the command when any member resolves
  outside the root (`AC-0013`). The command's working directory is the
  repository root, so stored relative paths resolve as the write-time rules
  assumed.
- **Environment.** The command runs with no inherited environment: no
  ambient `PATH`, `GIT_*`, `HOME`, or locale; the envelope resolves `argv[0]`
  itself against the tool locations it declares, closes standard input, and
  pins `LC_ALL=C` so byte matching is deterministic (`AC-0014`). `GIT_*` and
  `.gitattributes` textconv drivers affect only `git` subprocesses, which the
  § D6 allowlist does not admit; they are named here against a future
  widening, per that spec's own disclosure.
- **Resource cap.** 10 seconds wall clock and 64 KiB of captured output per
  command. The wall-clock cap fires first on a command that does not
  terminate on repository content — an operand resolving to a named pipe
  inside the repository clears every write-time rule; the output cap fires
  first on a command whose output exceeds 64 KiB — `cat` of a larger
  repository file. Enforcement is the runner's: the process is terminated at
  the wall-clock cap, output beyond 64 KiB is discarded, and the item is held
  rather than reported verified (`AC-0015`). Both values are chosen
  provisional bounds with no observed traffic behind them, on the same terms
  as the capture spec's § D3 cap; the revision trigger is the first
  legitimate command a cap refuses.

### D8 — a command's output reaches two sinks, as data, scanned before anything durable

The output may reach the drain's run report, operator-visible, and the
readiness and closure evidence the operator reads. It is presented as
delimited data with no instruction authority at every reasoning or
classification step (`AC-0021`). It is never executed, never interpolated
into a command, and never written to the store. Before any durable write
carrying output bytes, the output passes the deterministic eight-pattern
privacy scan — the same scan § D4 re-runs on record prose — at one seam
where output crosses toward a durable sink. This delivery writes no such
sink; the seam exists so the boundary is enforced and testable rather than
absent.

### D9 — `grep` runs under `-F`

The envelope's `grep` invocation inserts the matcher itself; the stored argv
stays option-free. The admitted character class's only members that are
metacharacters under any candidate matcher are `.` and `+`; both are
literals under `-F`, so an admitted pattern denotes exactly the line set the
author wrote (`AC-0022`). `docs/specs/work-item-capture/spec.md` § D6
obligation 5 records that the class plus `AC-0022` together admit `-F` and
nothing else; this decision takes that narrowing rather than relaxing
`AC-0022`.

### D10 — a captured defect record is ready when its evidence shape holds and survives the re-check

The defect route's readiness condition — canonical context must exist — is
satisfied by the captured-item file the route materializes under
`docs/product/captured/`, which is the canonical context work-intake's
classify table names for cited defect evidence. A captured defect record
satisfies it when it carries a `verification_route` whose pre-execution
re-check passes and whose run under the envelope completes within the cap, or
both `work_item.observed` and `work_item.intended` — the two evidence shapes
`docs/specs/work-item-capture/spec.md` § D2 admits for a defect. A defect
failing this — a merged record with neither shape, a route refused at the
re-check, or a run terminated at the cap — does not meet the condition and
is held (`AC-0008`).

Whether the deviation is still present is closure evidence — § D5's
overtaken and falsified tests — not a routing input. The drain routes
defects whose evidence holds and surfaces dead ones to the operator as
closure offers; it never routes on an unattended interpretation of command
output.

### D11 — every route and every closure is attended

The operator running the drain confirms each item's disposition before its
effects commit. An unattended drain performs the read-only half only —
offers, re-checks, envelope runs, classification proposals, the report — and
holds every item: it writes no artifact, dispatches no processor, and
records no terminal disposition (`AC-0011`). A held item carries no terminal
disposition: holding is the open state, and an item leaves it only by an
attended route or closure. This rule binds every route reached from this
drain, including the governance and duplicate-coverage siblings, which state
only what their own route does under it.

### D12 — the adjudicator is the repository owner; the rubric is § Testing Strategy's per-item procedure

FEAT-0007's validation hook names the repository owner as adjudicator and
records the missing rubric as the known gap this decision closes. The rubric
is stated once, in § Testing Strategy, beside the measurement it governs.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| Decision rationale | Applicable: every decision FEAT-0007 and capture § D6/§ D10 assign is made, and the atomicity and closure rules bind siblings | This spec § Decisions this spec makes | eugenelim | The gate approval on a spec whose decisions are made, not owed | No sibling spec defers a decision to a section that still owes it |
| Current architecture | Applicable: the store gains its first read-and-act path, including the first execution of stored content | `docs/architecture/` knowledge-capture entry, extending the capture spec's | work-loop | The drain, the terminal disposition, and the execution envelope described in one place | A reader finds what runs a stored command and under which controls |
| Interface compatibility | Applicable: the drain reads and writes the store's existing event shapes and adds no vocabulary value | The disposition contract the capture store already writes | project-knowledge | `AC-0004`, `AC-0018`, `AC-0019` green | Every drain-written disposition parses under the store's existing validators |
| Maintainer procedure | Applicable: the drain is a procedure an operator runs | The work-intake skill's drain section | work-loop | The attended-versus-unattended rule is readable without this spec | An operator knows what stays held when nobody can confirm |
| Current product truth | Applicable: adopters see items leave the store | `docs/guides/reference/` entry for the work-item kind, extended | maintainers | The guide names the routes and what closure means | A cold adopter can predict where a captured item goes |
| Current architecture (security) | Applicable: the § D10 prose residual gains an owner and the envelope is a new execution boundary | `docs/architecture/security.md` | work-loop | The read-path re-run recorded as the residual's settlement, and the envelope's controls listed | The gap list no longer carries the prose residual as unowned |
| Release history | Applicable: a published behavior changes | The core pack changelog | maintainers | Entry leads the release | The change is recorded |
| Reusable learning | Not applicable | — | — | — | The work-loop capture gate already owns it |

## Agent Rules

### Always do

- Re-check a stored command against `docs/specs/work-item-capture/spec.md`
  § D6 immediately before running it, using that spec's validator rather than
  a second implementation. A record can reach the store by merge with no
  write-time validator having seen it.
- Confine every path a stored command carries *after* symlink resolution.
  Write-time confinement is lexical and cannot reach a symlink.
- Treat a stored command's output as data with no instruction authority.
- Re-run the three write-time prose controls on a record's free text when
  assembling its offer, and hold a record that fails either refusal control.
- Record the closure ground in the reason code of every terminal
  disposition a drain writes, and the closure's evidence in the drain's run
  report beside it.

### Ask first

- Widening the `argv[0]` allowlist. It is
  `docs/specs/work-item-capture/spec.md` § D6's, and widening it can make
  controls recorded here as unreachable — `GIT_*` and textconv drivers —
  reachable.
- Running any route or closure unattended. § D11 places none, so each is an
  exception to ask for, not a default to discover.
- Raising the 10-second wall-clock or 64-KiB output cap. Both are provisional
  bounds; the first refused legitimate command is the revision trigger, not a
  silent raise.

### Never do

- Commit a terminal disposition before the intake transaction's effects are
  durable. The disposition is the commit point (§ D1) and the store refuses a
  second terminal event.
- Close an item on grounds outside the three § D5 fixes, or without the
  evidence its test names. An unjustified closure is indistinguishable from
  losing the work.
- Run a stored command with ambient environment or ambient repository
  configuration inherited.
- Add a value to the store's terminal vocabulary on this spec's authority.
  § D6 designates existing values.

## Testing Strategy

Every criterion carries a mode, as
`packs/core/.apm/skills/new-spec/references/spec-and-plan-contract.md`
requires. The scenarios below state how each is driven.

- **`AC-0005` — TDD, unit, crash injected at each effect boundary, then a
  re-driven drain:** the ordering is only observable by interrupting between
  effects and observing the recovery complete.
- **`AC-0006`, `AC-0007`, `AC-0008`, `AC-0009` — TDD, unit, over the decision
  function's routing table:** each is a pure decision over a captured record's
  fields and verdicts.
- **`AC-0010`, `AC-0023`, `AC-0024` — TDD, unit, with a dispatch spy:** the
  trust-boundary refusals and the framing are asserted before dispatch,
  proven by zero calls or by the delimiter.
- **`AC-0011` — TDD, unit, one drain with no confirmer:** holding is asserted
  as the absence of every effect, which a spy over the disposition writer
  proves.
- **`AC-0012` — TDD, unit, against the disposition writer:** the
  single-terminal-event rule is the store's; the drain's obligation is never
  to attempt a second write.
- **`AC-0013`, `AC-0014`, `AC-0015` — TDD, integration, against a real
  subprocess:** confinement, environment and the resource cap are runtime
  properties a pure function cannot show.
- **`AC-0016`, `AC-0017` — TDD, unit, driven from the capture spec's shared
  § D6 case table:** these re-run the capture spec's own validators, so the
  test imports its fixture rather than restating its rules.
- **`AC-0018`, `AC-0019`, `AC-0020`, `AC-0021` — TDD, unit:** output
  treatment and the counts are assertions over one function's inputs and the
  store.
- **`AC-0022` — goal-based check, the `-F` matcher § D9 names:** pattern
  equivalence is decided by the chosen matcher, so the check runs the
  pattern under it.
- **`AC-0003`, `AC-0004` — goal-based check, store replay after a drain:**
  both are derived from the store alone, which is the property being
  claimed.
- **`AC-0025`, `AC-0026` — TDD, unit:** each is a pure decision over the
  drain's own inputs — a missing dispatch seam, a classification string —
  asserted through the drain's held/routed outcome, the store's absence of a
  terminal event, and the absence of transaction effects (no artifact, no
  lock).
- **`AC-0027` — TDD, unit, against a real store:** the superseded ground's
  test resolves a citation against the store, so the check seeds a store and
  closes against a resolving, a non-resolving, and an absent citation.
- **`AC-0028` — TDD, unit, against a real lock file:** liveness and retry are
  filesystem and process properties, asserted by writing a stale lock with
  a dead pid and a live lock with the running pid; the atomic publication
  is asserted by fault-injecting the link step — no lock exists at the
  path and no temporary is left behind.
- **`AC-0001`, `AC-0002` — visual / manual QA, the named adjudicator over
  the rubric below:** the disposition judgement is the adjudicator's, not a
  function's.

- After one drain, the adjudicator applies the rubric below to ten items the
  drain was **offered** — routed, held and closed alike, since sampling only
  routed items lets a drain that holds or closes every hard case pass
  (`AC-0001`, `AC-0002`). The kill threshold is FEAT-0007 § De-risk's and is
  derived there.
- Drive a crash at each effect boundary — before the transaction, inside it,
  after it before the disposition, and after the disposition; assert a crash
  before the disposition leaves the capture open, the re-run drain completes
  without a second artifact or a second terminal event, and no boundary
  yields a closed capture without its handoff (`AC-0005`).
- Drive a crash on the closure path, where the terminal disposition is the
  only effect; assert the identical-disposition no-op holds (`AC-0005`).
- Drain a captured record whose stored path resolves outside the repository,
  and one carrying a field the trust-boundary rules classify as untrusted;
  assert each is refused as a routing input, the item is held, and the field
  reaches the destination unexecuted (`AC-0009`, `AC-0010`).
- Assemble an offer for a merged record whose free text carries a
  privacy-violating string, and one carrying instruction-shaped prose; assert
  each is refused by the named control and held, and that a clean merged
  record passes all three re-run controls (`AC-0023`).
- Assert the classification dispatch presents record prose inside its data
  delimiter and no record field reaches instruction position (`AC-0024`).
- Offer the drain an item it cannot route; assert it is held (`AC-0006`).
- Run one drain with no confirmer available; assert every item is held and
  counted as held, and no terminal disposition is written (`AC-0011`).
- After a drain producing at least one routed item and at least one closure,
  assert every disposition falls on exactly one side of the split, that the
  closure falls on the pruned side, and that both counts derive from the store
  with no run log (`AC-0004`, `AC-0018`, `AC-0019`).
- Assert the run's reported counts use the same partition as the store-derived
  counts (`AC-0020`).
- Run a stored `grep` whose pattern contains `.` and one containing `+`;
  assert each matches exactly the lines containing that literal, and that no
  other matcher is used (`AC-0022`).
- Run a stored command whose output carries a credential-shaped string and an
  instruction-shaped line; assert the output is privacy-scanned at the
  durable-write seam before any write and reaches no reasoning step with
  instruction authority (`AC-0021`).
- Close an item stating each of the three grounds in turn with the ground's
  test failing; assert each closure is refused (`AC-0003`). This is the half
  the adjudicator sample cannot reach, because a refused closure produces no
  disposition to sample.
- Run the drain with no `transact` override and no `dispatch_processor`, over
  a routable question and a ready defect; assert each is held with the
  missing dispatch named, and no terminal disposition exists in the store
  (`AC-0025`).
- Classify a question with an output that is not one of the six members, and
  with each non-dispatchable member; assert each is held as unroutable, and
  that each dispatchable member still routes (`AC-0026`).
- Close an item on the superseded ground with a cited capture id that
  resolves, then with a capture id that resolves nowhere, then with a path
  that does not exist, then with no citation at all; assert the first
  closes and the second, third, and fourth are refused by the drain itself
  (`AC-0027`).
- Write a workspace lock holding a pid that no longer exists; assert the
  transaction recovers it and completes; that a fresh lock taken between the
  probe and the removal is refused, not removed; that a lock holding a
  live pid, or no parseable pid, is never taken; and that fault-injecting
  the acquisition's link step leaves no lock at the path and no temporary
  behind (`AC-0028`).
- Add a row to `docs/specs/work-item-capture/spec.md` § D6 cases and assert
  the pre-execution re-check drives it without any edit here (`AC-0017`).
- Drain a governance-shaped item while no governance route exists; assert it
  is held, and that a non-governance item in the same drain still routes
  (`AC-0007`).
- Assert the drain never attempts a second terminal disposition against one
  capture; the store's single-terminal-event rule is recorded in FEAT-0007
  § De-risk (`AC-0012`).
- Assert a defect-shaped item that does not meet § D10's readiness condition
  is held rather than routed (`AC-0008`).
- Run a stored command whose path argument is a repository-relative symlink
  pointing outside the repository; assert it is refused after resolution and
  the item is held (`AC-0013`).
- Run a stored command with a poisoned ambient environment and a poisoned
  repository configuration; assert neither reaches it (`AC-0014`).
- Run a stored command that exceeds either cap; assert it is terminated or
  truncated and the item is held rather than reported verified (`AC-0015`).
- Place a record in the store by writing the file directly, bypassing the
  capture API, carrying a string `command` and separately argv
  `["bash", "-c", "…"]`; assert each is refused at the pre-execution re-check
  and the item is held (`AC-0016`).
- Drive the symlink case against a non-final element and against
  `verification_route.path`; assert both are refused, so a runner confining
  one argument fails (`AC-0013`).

**The rubric (§ D12).** For each of ten items sampled from what one drain was
offered — routed, held, and closed alike — the adjudicator reads the record
and the original work behind it and judges:

1. A **routed** item by whether the destination is the one the record's
   fields select under § D2 and work-intake's classify table.
2. A **held** item by whether no shape fits, or a named check refuses it —
   readiness (§ D10), the pre-execution re-check, an envelope refusal, a
   prose re-run refusal (§ D4), a non-dispatchable classify member (§ D3),
   a missing processor dispatch (§ D1), or a refused closure citation
   (§ D5).
3. A **closed** item by whether the stated ground holds under § D5's test,
   with the recorded evidence.

An item counts against the drain when the adjudicator's judgement differs
from the drain's disposition. The kill threshold — three or more of ten — is
FEAT-0007 § De-risk's. The sample runs on the first drain the real store
offers ten items; until capture traffic exists, the fixture-driven drain
verifies the criteria below mechanically.

## Acceptance Criteria

> **Stable identifiers.** Each criterion carries a four-digit `AC`
> identifier assigned once and never reused or renumbered, matching
> `docs/specs/work-item-capture/spec.md`'s rule. Citations use the id, never
> a list position.

- [ ] **AC-0001.** A triaged item reaches the classifier and its capture records a terminal
      disposition.
- [ ] **AC-0002.** An item closed without routing records which of overtaken, superseded or
      falsified justifies it.
- [ ] **AC-0003.** A closure whose stated ground fails its test is refused.
- [ ] **AC-0004.** Every terminal disposition falls on exactly one side of the
      promoted-or-pruned split CAP-0005 § Riskiest assumption reads — promoted
      side `promoted` and `routed`, pruned side `rejected`, `superseded`,
      `duplicate`.
- [ ] **AC-0018.** A closure falls on the pruned side of that split.
- [ ] **AC-0019.** Both counts are derivable from the store alone.
- [ ] **AC-0005.** The terminal disposition is the sole commit point: a crash at
      any effect boundary ahead of it leaves the capture open, and re-running
      the drain completes the sequence without creating a second artifact or a
      second terminal event; no crash can leave a capture closed without its
      handoff.
- [ ] **AC-0006.** An item the drain cannot route is held.
- [ ] **AC-0020.** The run reports the held, routed and closed counts using the
      same partition as the store-derived counts.
- [ ] **AC-0022.** A stored `grep` pattern runs under `-F` and nothing else, and
      a pattern admitted at write time denotes the same line set the author
      wrote. This is obligation 5 in
      `docs/specs/work-item-capture/spec.md` § D6.
- [ ] **AC-0021.** A stored command's output is privacy-scanned before any
      durable write, and reaches no reasoning or classification step with
      instruction authority. The bytes are attacker-influenced whenever the
      record is, and the capture spec discloses a merge path that reaches the
      store with no write-time validation.
- [ ] **AC-0007.** A governance item is held until its own route exists; nothing else is
      blocked by that absence.
- [ ] **AC-0008.** A defect-shaped item that does not meet § D10's readiness
      condition is held, not routed.
- [ ] **AC-0009.** A stored path that resolves outside the repository is refused as a
      routing input and the item is held. Repository confinement is a floor,
      not a settlement.
- [ ] **AC-0010.** A captured field the trust-boundary rules classify as untrusted is
      refused as a routing input, and the field reaches the destination
      unexecuted.
- [ ] **AC-0011.** An unattended drain performs no route and no closure: it
      reports offers and holds every item, a held item carries no terminal
      disposition, and the run counts every held item as held.
- [ ] **AC-0012.** The drain never attempts a second terminal disposition against a capture.
      A mis-route is surfaced only through the recovery path § D1 names.
- [ ] **AC-0013.** Every member of the **stored-path set**
      `docs/specs/work-item-capture/spec.md` § D6 defines — which this
      criterion does not restate, and which includes
      `verification_route.path` — is resolved, and if any resolves outside
      the repository the command is refused at execution and the item is
      held. A runner that confines only the last argv element, or only
      `verification_route.path`, does not satisfy this. Write-time confinement
      is lexical and cannot reach symlinks.
- [ ] **AC-0014.** A stored command runs with no inherited environment — no
      ambient `PATH`, `GIT_*`, `HOME`, or locale — with standard input closed
      and `LC_ALL=C`, and a command run with ambient environment or ambient
      repository configuration inherited is a failure.
- [ ] **AC-0015.** A stored command exceeding either cap — 10 seconds wall
      clock, 64 KiB of captured output — is terminated or truncated, and the
      item is held rather than reported as verified.
- [ ] **AC-0016.** Every stored command is re-checked immediately before execution by the
      same validator the capture spec's write path uses — not a second
      implementation of § D6 — and one failing it is refused and the item held.
      A record that reached the store by merge or contributor branch, having
      passed no write-time validator, is refused here.
- [ ] **AC-0017.** The pre-execution re-check is driven against
      `docs/specs/work-item-capture/spec.md` § D6 cases as its shared table, so
      a row added there is a case here and the two enforcement points cannot
      diverge.
- [ ] **AC-0023.** A record whose free text fails a re-run write-time prose
      control — the eight-pattern privacy scan or the instruction-shape
      refusal — is refused as a routing input and held, and the drain's report
      names the control that refused it.
- [ ] **AC-0024.** Record prose reaches every reasoning or classification step
      as delimited data, and no record field is interpolated into instruction
      position.
- [ ] **AC-0025.** A route committed with no processor dispatch wired — no
      `transact` override and no `dispatch_processor`, on either route branch
      — holds the item with no transaction effect — no lock taken, no
      artifact materialized — and records no terminal disposition (§ D1).
- [ ] **AC-0026.** A question whose classification is not one of the six
      classify-table members, or names a non-dispatchable member, is held as
      unroutable (§ D3, extending `AC-0006`).
- [ ] **AC-0027.** A superseded closure whose citation is absent, or whose
      citation is a capture id that resolves nowhere, or whose citation is
      a path whose artifact does not exist, is refused by the drain itself
      (§ D5, extending `AC-0003`); the liveness of a cited artifact is the
      operator's attestation, and overtaken and falsified closures remain
      operator-attested.
- [ ] **AC-0028.** A workspace lock left by a process that no longer exists
      is recovered by the transaction, and the re-run completes the sequence
      (§ D1, extending `AC-0005`); the removal re-verifies the lock's
      identity — same inode, same pid payload — immediately before the
      unlink and refuses when the lock changed underneath; a lock whose
      owner is alive, or whose payload carries no parseable pid, is never
      taken; and the transaction's own acquisition publishes the lock
      atomically — a pid-complete temporary file, unique to its holder,
      linked into place — so a
      lock it leaves always carries its owner's pid; the temporary is
      unlinked immediately after publication and on link failure, and an
      orphaned temporary never blocks a later acquisition.

## Follow-ons

- governance-item-record-routing: `docs/specs/governance-item-record-routing/spec.md`
  — the route `AC-0007` holds governance items for; this spec's § D11 rule
  binds it.
- duplicate-coverage-offer: `docs/specs/duplicate-coverage-offer/spec.md` —
  the coverage offer § D1 places outside the atomic unit.
- work-item-mechanical-tier: `docs/specs/work-item-mechanical-tier/spec.md` —
  the deterministic validation tier upstream; it changes what the store
  admits, not what the drain does with what it finds there.
- The § D12 adjudicated sample: owner eugenelim — runs on the first drain the
  real store offers ten items; until capture traffic exists the measurement
  is gated, with the rubric in place above.
- Stale-lock recovery for the lock takers outside the shared transaction —
  `workspace-status`'s `workspace_status.py` and work-intake's
  `refresh.py` each take the same lock file with their own acquisition and
  refuse PID-probe recovery, each recording its own reason; the recovery
  `AC-0028` adds lands in the shared `_acquire_workspace_lock` and so
  reaches every `run_intake_transaction` caller — work-intake's § 5
  artifact-creating flows included. `intent_rename.py` already recovers its
  own dead-owner locks (`_normalise_old_claim`, the pattern `AC-0028`
  follows); the remaining gap is each foreign taker's recovery of locks
  other writers leave. Owner: eugenelim, routed when a writer outside the
  transaction wedges on a foreign stale lock.

## Assumptions

- Defaulted: Technical: the recovery ordering accepts a possible repeated
  processor invocation after a crash between dispatch and disposition —
  default: disposition-last with re-running the drain as the one recovery
  path (§ D1); if wrong: the unit widens or the store gains a pre-disposition
  marker, each an amendment (settled by: eugenelim).
- Defaulted: Technical: no new terminal vocabulary value; overtaken and
  falsified closures record `rejected` with a ground-coded reason — default:
  § D6's designation of existing values; if wrong: a sixth value is added and
  every store reader widens with it (settled by: eugenelim).
- Defaulted: Technical: the envelope's caps are 10 seconds wall clock and
  64 KiB of captured output — default: chosen provisional bounds on the same
  terms as the capture spec's § D3 cap; if wrong: the first legitimate
  command a cap refuses triggers a revision (settled by: eugenelim).
- Defaulted: Product: every route and every closure is attended, and an
  unattended drain reports and holds — default: § D11's strict rule; if
  wrong: named routes gain unattended placement, each an ask-first widening
  recorded here first (settled by: eugenelim).
