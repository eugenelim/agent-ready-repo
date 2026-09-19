# Intent: a loop's leftover work is captured as a record a cold session can act on

- **Slug:** `work-item-capture-contract` <!-- canonical identity; independent of the filename ordinal -->
- **Status:** Accepted
- **Level:** `feature`
- **Kind:** `opportunity`
- **Scale:** `app`
- **Maturity:** `brownfield`
- **Parent intent:** work-item-capture-and-disposition — [Work-item capture and disposition](CAP-0005-work-item-capture-and-disposition.md)

## Outcome

A work-loop that finishes with leftover work records it where a later session
can act on it without re-deriving what the original session already knew.

**How we will know.** The steerable input is the **share of captured items a cold
session can act on from the record alone**. Today the surviving records name
their artifacts and omit the fact that decides the fix, so the share is low.

## Opportunity

A loop that notices work it should not do has nowhere cheap to put it.

Recording costs a schema-valid entry pointing at an artifact that may not exist,
and the owner must ask for it. Declining costs one sentence in a pull-request
description. The economics decide the outcome, and the sentence wins.

The items that do survive are often unusable. Capture at the end of a loop is
reconstruction from the diff rather than recall: it recovers the artifact and
loses the fact that makes the artifact actionable.

| What the record named | What it lost | Why the loss blocks the fix |
| --- | --- | --- |
| Four 13px font sites | Which one is sans | That is the only reason the matching token cannot simply be adopted |
| Three test docstrings, by filename | The claim they should assert instead | The files are findable in a minute; the correct wording is not recoverable |
| "Eight roster-owned steps" | Which eight | No filter over the workflow file yields eight, so the set is unreconstructable |

Each names a location and omits a finished state. A reader can find the files in
a minute and cannot tell what done looks like.

Under current guidance this is not an accident. The close-time routine sorts
scratch notes into generalisable practice, which is kept, and everything else,
which is discarded. A specific, real, non-generalisable defect is thrown away by
instruction.

## What exists today

**Snapshot taken 2026-09-19.** These are locations, not contents. Each names a
file and why this intent cares about it, and deliberately reproduces no value,
status, field content or count from it — a copy would be a second home for
another artifact's state, and the date would record only when the copy was made,
not whether it still holds. Open them.

- **The store, and the skill that owns it.**
  `packs/core/.apm/skills/project-knowledge/`. Read it for where captures land
  and how they are partitioned.
- **The capture contract.**
  `contracts/jsonschema/knowledge-captured-observation.schema.json`. Read it for
  the required field set, the kind vocabulary, and its policy on unknown
  properties — all three decide whether a work-item kind is an additive change.
- **An evidence slot that already exists.** The same schema defines an optional
  route carrying a command and a path. Read it, then count how many records in
  `docs/knowledge/observations/` populate it; the answer is the premise of this
  intent's riskiest assumption and is worth re-deriving rather than trusting.
- **What a capture may say about scope.** `_validate_project_scope` in
  `packs/core/.apm/skills/project-knowledge/scripts/project_knowledge.py`.
- **The writer and its refusals.**
  `packs/core/.apm/skills/project-knowledge/scripts/knowledge_store.py`.
- **The admission rule this intent must change.** The close-time capture section
  of `packs/core/.apm/skills/work-loop/SKILL.md`.
- **The freshness item this intent excludes.** `workspace.toml`, `[backlog].open`,
  slug `knowledge-freshness-pins-bytes-and-the-pins-do-not-hold`. Its state and
  its recommendation are its own; read them there.
## Validation at capture

Capture validates before it writes, on two separate questions. A record that
turns out to be wrong later is a cost someone pays; a record that was wrong
when written, or that nobody needed, is one this feature is responsible for not
creating.

**Is it true, and is it needed.** These fail differently and neither implies
the other. A technically impeccable item — reproducible, correctly targeted,
current — can still be work nobody should do. The second test is the one that
keeps the well a well rather than a heap, and it is the harder of the two
because a real finding is easy to justify keeping.

Three classes of error motivate it, all observed in loops rather than imagined:

- **A repair proposed against an artifact that cannot take one.** The
  correction path differs by class and one class has none — a decision record
  supersedes, a proposal takes errata or amendments depending on its lifecycle
  state, and a shipped spec freezes so that correcting it means superseding it
  rather than editing its body. A loop holding the wrong class proposes a
  repair that is not available.
- **A claim the loop was not entitled to make**, asserted with the confidence
  of something read rather than inferred.
- **An item already false when written**, because the tree moved during the
  session that noticed it.

**The necessity test is the repository's own razor, not a new rubric.** The
`Cut before adding` ladder already governs this judgement, and its first rung
is the test: *skip an addition that is not genuinely needed and say so once*.
An item survives capture only if it clears that rung — and the ladder's later
rungs matter too, since an item asking for something an existing solution
already satisfies is a candidate for reuse rather than a work item.

Importing a separate principle here would give one judgement two homes that
drift, which is the defect this family exists to reduce.

**The rationale travels with the item.** An item that survives the razor
carries *why* — what was considered and rejected as sufficient. Without it the
next reader re-runs the judgement from scratch, which is the same
re-derivation cost the capture contract exists to prevent, and a surviving
item with no stated reason is indistinguishable from one nobody tested.

The owner confirms a judgement they can see, rather than a list already
filtered by reasoning they cannot. Where and how that rationale is surfaced is
the spec's.

**Two tiers, because one will not reach.** The first is mechanical and runs on
every capture: is the target frozen, does its recorded anchor still match the
file, does the cited artifact exist and carry a readable status. These are
deterministic and cheap.

The second is a reasoning check for what a rubric cannot enumerate — whether
the claim is entitled, whether the proposed repair suits the artifact's class,
whether the item is real, and whether it is needed at all. Enumerating a rule per class does not converge; the
classes multiply and the case nobody anticipated is the one that lands.

**The reasoning check runs in a context that did not produce the item.** A
check sharing the author's context inherits the author's errors: the session
that believes a wrong thing is the session that would be asked to catch it.
This is not a precaution — it is the observed behaviour of this family's own
shaping, where several confident and wrong claims passed the author repeatedly
and were caught only by cold review.

**The first tier is the floor.** If the reasoning check degrades or is skipped,
the deterministic checks still refuse a frozen target. A guard whose failure is
silent must not be the only guard.

## Non-goals

- **Knowledge freshness.** Whether a stored digest reflects a file's current
  state is a registered open item with its own owner, listed under
  `What exists today`. Its state, its disposition and whatever it recommends are
  read there, not here. This intent changes nothing about it and assumes no
  answer to it — including no assumption that the digest is the right instrument.
- **Where captured items are stored beyond the existing store.** No new store.
- **Promotion.** What happens to a captured item afterwards is a sibling's.

## Assumptions

- Ready-now work is dispatched in-session rather than captured. Disposing an
  item while its context is live costs less than recording it, and a recorded
  ready item pays a tracking cost to buy nothing. Capture is for work that
  cannot proceed: blocked on a decision, an instrument, elapsed time, or another
  item.
- The existing capture store is the destination. Its records are append-only and
  partitioned by kind and month. Concurrent branches do not make it
  conflict-free — same-topic conflicts require semantic resolution — but the
  shape is closer to one record per item than to a shared register.
- Some admitted item kinds cannot carry a reproduction command. A question whose
  deliverable is a decision has nothing to reproduce. Any required-evidence rule
  has to hold for those too, or it excludes them.

## Decomposition

None. One outcome, one measure.

## De-risk

**Reversibility: mixed.** Capture can be switched off and the schema rolled
back. Two halves cannot: records already written persist, because the store is
append-only, and useful items refused by an over-demanding required field are
not recovered by relaxing it later. The published contract carries a version
field, so a corrected shape can coexist — that bounds the first half and does
nothing for the second.

**Riskiest assumption.** *Leftover work can be made actionable by required
evidence, without excluding the kinds that cannot supply it.*

Both halves have to hold. The evidence field already exists in the contract and
no record in the corpus populates it, so nobody has ever supplied it. The count
of records is deliberately not stated: it moves, and the zero is the claim. The empirical bug-report literature reports the same shape — reproduction
steps are what readers value most and what reporters supply least. And a
required field nobody can answer causes the item not to be filed at all, which
is a documented failure in real trackers rather than a theoretical one.

**Kill condition — qualitative, and deliberately so.** There is no traffic to
set a rate against: zero items have been captured under this contract, so any
percentage would be invented. The bar is therefore stated in the test's own
currency, and it has to reach both halves of the assumption, because a sample
drawn from one kind can pass while the other fails silently.

The actionability half fails if, after one real loop's close, a second session
with no prior context reads the captured items and reports that it could not act
on most of them.

The exclusion half fails if any kind that the contract admits could not be
recorded because it could not supply the required evidence. This half is asked
of the capturing author directly rather than sampled, because an excluded item
leaves no record to sample — which is why a rate over what was captured cannot
see it.

**Probe run — retrospective, and it proves less than it looks.** Six commands
were written for items deferred in two real pull requests and run against the
merged tree. All six reproduced, and two returned facts contradicting the
original prose. That shows a command-backed record self-corrects as the tree
moves. It does not show an agent can write one at close, because these were
written with hindsight by a session that already knew the answers.

```
validation_hook:
  assumption: leftover work can be made actionable by required evidence,
    without excluding the kinds that cannot supply it
  kill_condition: after one loop's close, a second session with no prior
    context cannot act on most captured items — or admitted items went
    unrecorded because the evidence could not be supplied
  activity: run the capture contract at one real loop's close; have a second
    session attempt each item from its record alone; separately ask the
    capturing author what they wanted to record and could not
```

## For the spec to decide

These are named so a spec author knows they are open, not deferred by oversight.
None is settled here.

- **Where validation runs and at what granularity.** Capture happens at a
  loop's close, so the reasoning check may run per item or once over the
  batch. Per item is more precise and costs a dispatch each; over the batch is
  cheaper and may miss an item-specific error. Nothing here settles it.
- **What a refusal does, and it needs a binding minimum rather than a
  preference.** An item that fails validation is not captured. A true item
  refused as unnecessary is the dangerous case: the razor is a judgement, so it
  will sometimes be wrong, and a silent refusal then loses exactly the work
  this feature exists to keep — invisibly, and with a control reading as
  working. Whether the author is told, whether the refusal is retained, and
  whether a corrected item can be re-submitted are open; that *some* non-silent
  handling exists is not.
- **The trust boundary on a stored command.** A captured record may carry a
  command that a later session runs. Authorship, confinement, permitted effects,
  timeout and failure handling are unaddressed, and a schema that ships without
  them is harder to correct afterwards than before.
- **Which fields are required, per kind**, and what an item whose kind cannot
  carry evidence supplies instead.
- **Whether the item's prose reuses the existing lesson field or gains its own.**
  Reuse is cheaper because the schema forbids unknown properties; its cost is
  one field carrying two meanings.
- **What the item kinds are, what bounds the set, and what each kind's
  threshold is.** A candidate test — a kind is warranted only when its required
  field set differs from every existing one — is offered as a starting point,
  not a rule. It is what stops the *set* sprawling.

  It does not stop a *kind* over-collecting, and one already does. A kind whose
  deliverable is a decision is defined by that property alone, and that test
  admits almost any design choice: during this family's own shaping it was
  applied to a route's degradation behaviour — spec content — and produced a
  proposed decision record for it. A drain inheriting only the definition will
  escalate at that rate.

  So each kind needs a threshold as well as a definition. For the decision kind
  the missing half is whether the choice is architecturally significant,
  expensive to reverse, or constrains work beyond the feature that raised it; a
  question failing all three is spec content however cleanly it fits the
  definition. Whether every kind needs such a second half, or only this one, is
  the open question.
- **Operational definitions** for "can act on", "cold session", and the false or
  already-fixed count the second signal would read.
- **How the existing records and the admission rule change.** The close-time
  routine currently admits only generalisable practice; a specific defect is
  exactly what it discards, so that rule needs a branch rather than a loosening.
