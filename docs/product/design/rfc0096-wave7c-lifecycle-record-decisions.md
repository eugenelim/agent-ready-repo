# RFC-0096 Wave 7c lifecycle-record decisions

- **Status:** Decided 2026-09-03

## Decision

The Approver chose **Option A** for `lifecycle-record-reclassified-gap`: pair
`retain-exception` with `Reclassified` in the lifecycle record, rather than
declaring the value projection-only. This reverses the recommendation below,
which is retained as the rejected alternative and its reasoning.

`lifecycle-record-entry-removal-fact` is unaffected and reassigned to
`rfc0096-wave7c-pruning`, as argued below.

Implementation is specified separately in
[`docs/specs/reclassified-lifecycle-result/`](../../specs/reclassified-lifecycle-result/).

The erratum drafted below is not needed: it belongs to the rejected Option B.
Option A does, however, need one frozen-spec supersession that this document did
not anticipate. Extending the transition table falsifies ticked AC22 of the
frozen spec `thirty-day-cooling-and-retirement`, whose oracle is a table inside
that spec's frozen `plan.md`. No gate detects it, because the refusal sweep runs
over a hardcoded domain. The Approver settled on 2026-09-03 that a new ADR plus
a `Status` parenthetical carries that correction — the same licensed carrier
this document identifies for Option B, applied to a different criterion.

## Outcome

Wave 7c's two absorbed follow-ons need one Approver decision and no code now.
Neither is the schema edit the 2026-09-03 Errata implies: one is an atomicity
requirement belonging to the pruning slice, and the other is a choice between
two contract readings.

## What each follow-on was buying

The 2026-09-03 Errata assigned two "schema follow-ons" to Wave 7c
(`docs/rfc/0096-portable-delivery-artifact-lifecycle.md:432`). Taken back to the
outcome each existed to deliver:

| Follow-on | Benefit sought | Finding |
| --- | --- | --- |
| `lifecycle-record-entry-removal-fact` | Stop a pruned artifact silently stranding its dependants. | The stranding harm does not occur. The residual requirement is atomicity, not a record field. |
| `lifecycle-record-reclassified-gap` | Stop RFC section 5 and the record contract disagreeing about `Reclassified`. | A real decision, with two viable repairs. |

## Follow-on 1 — the record field is not the repair

### The stated harm does not occur

The follow-on says an orphaned entry "silently strands every dependant the
receipt exists to protect, with every criterion green"
(`docs/specs/dependency-scoped-completion-receipts/notes/follow-ons.md:26`).

Nothing is green. In the tested state the two cases diverge:

| State | Result | Pinned by |
| --- | --- | --- |
| Correct prune — entry removed, file removed | Dependant resolves through its completion receipt, carrying no finding code | AC4, `tests/roster/test_dependency_scoped_completion_receipts.py:433` |
| Orphaned entry — entry kept, file removed | Dependant carries `unsatisfied_dependency`; the entry itself carries `missing_artifact` | AC5, `tests/roster/test_dependency_scoped_completion_receipts.py:530`; `packs/core/.apm/skills/workspace-status/scripts/workspace_status_engine.py:3153` |

The dependant fails closed, so the receipt's protection is not silently lost.

Two limits on that evidence. AC4 and AC5 exercise one shape — a canonical `spec`
entry in an active initiative, on the `status` surface
(`tests/roster/test_dependency_scoped_completion_receipts.py:70`) — and do not
pin aliases, paused or closed initiatives, non-spec kinds, `Retained` or
`ExternalAdvisory` records, or the repair surfaces. And the guarantee is
snapshot-scoped: `_cooled_locators` admits a locator only when the file exists
(`packs/core/.apm/skills/workspace-status/scripts/workspace_status_engine.py:2109`),
so the cooled early return that skips the existence check (`:3138`) is not
reached for a deleted artifact, but a deletion racing the scan between those two
points would be excluded without emitting `missing_artifact`.

### The residual requirement is atomicity, owned by pruning

Detection after the fact is not a pruning session proving its own precondition.
That distinction is the follow-on's real content, and it survives: nothing makes
the two removals atomic. `cooling.py` is the only record writer and has no prune
path — its single `os.unlink`
(`packs/core/.apm/skills/close-work/scripts/cooling.py:642`) is temp-file cleanup
inside the atomic write.

A record field would not supply atomicity. It would store a claim the pruning
session makes about itself, which is weaker than the invariant needed. The
requirement is an atomic prune, or a mandatory post-mutation invariant, defined
and verified by `rfc0096-wave7c-pruning`. Keep the follow-on open and reassign it
there; add no field now.

## Follow-on 2 — a real decision with two viable repairs

RFC section 5 lists five post-closeout states
(`docs/rfc/0096-portable-delivery-artifact-lifecycle.md:146`). The record
contract publishes four, omitting `Reclassified`
(`contracts/jsonschema/delivery-lifecycle-record.schema.json:18`).

A pairing for it is structurally available. `retain-exception` already pairs with
`ExternalAdvisory` — a `post_closeout_result` that is not itself that disposition
— as a shipped transition
(`packs/core/.apm/skills/close-work/scripts/cooling.py:63`) and a shipped outcome
mapping (`:875`). The objection is semantic: `retain-exception` mandates an
`exception` block (`contracts/jsonschema/delivery-lifecycle-record.schema.json:30`)
requiring `reason`, `owner_role`, and `review_on` (`:61`), so reusing it assigns
an obligation and a future review date to an artifact whose delivery authority
has ended (`docs/rfc/0096-portable-delivery-artifact-lifecycle.md:83`).

### Options

**Option A — pair `retain-exception` with `Reclassified`.** Add the value to the
schema enum and to `cooling.validate_payload`
(`packs/core/.apm/skills/close-work/scripts/cooling.py:331`), add a transition,
and define reader semantics, since `workspace-status` treats only `Retained` and
`ExternalAdvisory` as live obligations. Keeps the promise two Shipped specs make.
Cost: it records a review date for work that has none, and needs a producer,
since none exists.

As chosen, this option is narrower than the sketch above in reachability and
stricter in evidence. Reclassification is reachable only as a transition from a
retained record, and no `exception.reason` value is added — the durable owner
picks from the published enum. The acceptance is supplied and validated at the
transition rather than inherited from the prior record: adversarial review found
that the inheriting code path ignores its attestation, so an inherited block
would assert an acceptance nobody checked. Reclassification is also not
date-gated, because the seam that would have gated it compares a field no
transition updates, giving a check that cannot fail. The specified shape is in
[`docs/specs/reclassified-lifecycle-result/`](../../specs/reclassified-lifecycle-result/).

**Option B — declare `Reclassified` projection-only.** Leave the contract and
runtime unchanged. Cost: it contradicts statements in two Shipped specs, and
correcting those needs a second carrier — see *Option B needs two carriers*
below. It is not one signed paragraph.

### Recommendation (not taken)

The Approver chose Option A. This section is the rejected reasoning, kept so a
later reader can see what was weighed rather than re-deriving it.

Option B, unless the Approver can name a consumer that reads the value.
`docs/lifecycle/` holds one file, its `README.md`, and zero records, so Option A
would define a record shape for a lifecycle nothing has entered. The same
2026-09-03 Errata withdrew Wave 7b's portable contract on that reasoning
(`docs/rfc/0096-portable-delivery-artifact-lifecycle.md:417`).

Weighing against it: `close_work.py` already carries `Reclassified` in
`POST_CLOSEOUT_RESULTS` (`:38`), and two Shipped specs expect the value to be
recorded. Option A wins if closeout routing must be machine-readable before an
adopter asks.

Option B's cost is higher than it first appears — an ADR and two frozen-spec
annotations on top of the erratum — but that does not flip the recommendation.
Option A carries all of that reasoning work *plus* a contract change, a
producer, reader semantics, tests, regenerated projections, and a Core release.
The gap between them is narrower than stated above, not reversed.

## Option B needs two carriers, not one

Four statements must change, and they do not share a carrier.

An RFC erratum can correct the RFC body and ordinary documentation. It cannot
correct a frozen spec. `docs/CONVENTIONS.md:456` makes a parenthetical on the
`Status` token "the only edit a frozen spec accepts", and the rule at `:153`
requires that pointer to name an **ADR**, not a spec and not an erratum. A
Shipped spec is frozen (`docs/CONVENTIONS.md:111`), and both specs below are
Shipped.

| Statement to correct | Carrier |
| --- | --- |
| `docs/rfc/0096-portable-delivery-artifact-lifecycle.md:146` — section 5's phase table lists all five results as a "lifecycle record" state | RFC erratum |
| `docs/lifecycle/README.md:3` — owns one record "for each delivered artifact", broader than the contract's own scope of an artifact "in cooling or retention" (`contracts/jsonschema/delivery-lifecycle-record.schema.json:5`) | Ordinary edit |
| `docs/specs/close-work-extraction-and-immediate-disposition/spec.md:321` — AC4, ticked: "only `close-work` **records** a Post-closeout result of … `Reclassified`" | New ADR + `Status` parenthetical |
| `docs/specs/status-projection-and-context-exclusion/spec.md:78` — records the omission as a defect to be closed | New ADR + `Status` parenthetical |

AC4 needs amending for `Reclassified` only. The other four results genuinely are
record-backed: `cooling.py` is part of the `close-work` skill and is the only
writer (`packs/core/.apm/skills/close-work/scripts/cooling.py:554`;
`docs/lifecycle/README.md:6`). What `project_lifecycle` does not do is source or
persist the value — it accepts a caller-supplied result and returns the generic
phase `Post-closeout`
(`packs/core/.apm/skills/close-work/scripts/close_work.py:1037`), and is
documented as projecting "without changing any source record" (`:1003`).

Two consequences worth weighing before choosing:

- **Option A needs no frozen-spec correction.** It makes AC4 true by supplying
  the producer, and closes the recorded defect rather than withdrawing it. The
  supersession cost falls entirely on Option B.
- **Option B collides with in-flight work.**
  `docs/specs/status-projection-and-context-exclusion/spec.md` is row 3 of the
  AC23 digest table, and the Wave 7b session is already adding an ADR-0104
  supersession parenthetical to that exact `Status` line. Option B would put a
  second pointer on the same line and move the same pinned digest again.

## Drafted erratum for Option B

This is the first of Option B's two carriers; a companion ADR is still needed
for the two frozen specs. Unsigned:
`tests/roster/test_cooling_scope_closure.py:1019` asserts no RFC-0096 erratum
entry lacks `(Approver: …)`, so appending this before it is signed would fail
that test.

> - **YYYY-MM-DD (Approver: NAME) — `Reclassified` is a projection, and the
>   entry-removal fact moves to pruning.**
>
>   `lifecycle-record-reclassified-gap` read the record contract's omission of
>   `Reclassified` as a defect. The contract is correct as published: it scopes
>   itself to an artifact in cooling or retention, and `Reclassified` ends
>   delivery authority without entering either state. `Reclassified` is a
>   post-closeout projection evidenced by the accepting durable owner, and no
>   lifecycle record carries it.
>
>   This corrects section 5's phase table, and only as to `Reclassified`: the
>   table lists it as a lifecycle-record state, and it is a projected state. The
>   other four results remain record-backed, written by `close-work` through its
>   cooling seam. `docs/lifecycle/README.md` is corrected by ordinary edit: the
>   directory owns one record for each artifact entering cooling or retention,
>   not for each delivered artifact.
>
>   Two Shipped specs also state that the result is recorded:
>   `docs/specs/close-work-extraction-and-immediate-disposition/spec.md:321`
>   (AC4) and `docs/specs/status-projection-and-context-exclusion/spec.md:78`.
>   A frozen spec accepts only a `Status`-token parenthetical naming an ADR, so
>   this erratum does not correct them and cannot. ADR-NNNN carries that
>   correction and both specs point at it.
>
>   `lifecycle-record-entry-removal-fact` is not a record field. A pruned
>   artifact's workspace entry must be removed with its file, and the guarantee
>   needed is that both removals happen together — an invariant a self-reported
>   record field cannot supply. The follow-on is reassigned to
>   `rfc0096-wave7c-pruning`, which must define an atomic prune or a mandatory
>   post-mutation reconciliation and verify it. Wave 7c's remaining scope is
>   that slice alone.

## What was measured

Observed 2026-09-03 at commit `807fc8ef1`. These are measurements; the
inferences drawn from them are argued above.

| Fact | Value | Source |
| --- | --- | --- |
| Lifecycle records on disk | 0, only `README.md` | `docs/lifecycle/` |
| Post-closeout values in the record contract | 4 | `contracts/jsonschema/delivery-lifecycle-record.schema.json:18` |
| Post-closeout states in RFC section 5 | 5 | `docs/rfc/0096-portable-delivery-artifact-lifecycle.md:146` |
| Values in `close_work.POST_CLOSEOUT_RESULTS` | 5 | `packs/core/.apm/skills/close-work/scripts/close_work.py:38` |
| Artifact-prune paths in the only record writer | 0 | `packs/core/.apm/skills/close-work/scripts/cooling.py` |

The last row establishes that no current writer enforces entry removal. It does
not by itself decide whether the precondition is needed.

## If a contract change is ever made

Option A would edit two files byte-pinned by AC23 of `cooling-scope-closure`, a
spec that is `Status: Implementing`:
`contracts/jsonschema/delivery-lifecycle-record.schema.json` and
`packs/core/.apm/skills/close-work/scripts/cooling.py`. The digests appear twice
— a constant at `tests/roster/test_cooling_scope_closure.py:842` and a table at
`docs/specs/cooling-scope-closure/spec.md:284` — and both must move in the same
commit. Option B changes neither file.
