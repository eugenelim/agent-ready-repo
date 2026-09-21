# Intent: a captured question that only a decision can answer reaches a decider

- **Slug:** `governance-item-record-routing` <!-- canonical identity; independent of the filename ordinal -->
- **Status:** Accepted
- **Level:** `feature`
- **Owner:** eugenelim
- **Kind:** `opportunity`
- **Scale:** `app`
- **Maturity:** `brownfield`
- **Parent intent:** work-item-capture-and-disposition — [Work-item capture and disposition](CAP-0005-work-item-capture-and-disposition.md)
- **Depends on:** docs/product/intents/FEAT-0007-work-item-promotion-routing.md <!-- stated for a reader; the enforceable edge is a typed `needs` entry on the workspace registration, which does not exist yet -->

## Outcome

A captured item whose deliverable is a decision rather than work stops being
held: it becomes a record that names who decides.

**How we will know.** The share of captured governance items that reach a record
with a named decider, against the share still held.

There is no baseline to compare against, and saying the share is currently zero
would misdescribe why. Record types exist; what is absent is a route from a
capture to one — and capture itself is not running, so no such items exist to
count. The first measurement establishes the baseline rather than improving on
one.

## Opportunity

Decision-blocked items are the largest class of leftover work in the sample this
family was shaped from — items waiting on a human choice rather than on effort.
They are not backlog. They are unanswered questions, and nothing re-presents
them to anyone.

Two record types already exist that would hold such a question durably and name
who answers it. A decision record opens at `Proposed` and carries a
decision-makers field. A proposal opens at `Draft` and carries an approver. Both
ship in the same pack, and neither is core's.

Which of the two a given question takes is not a rule that generalises. Who may
decide alone, what needs wider input, and what must be recorded regardless
differ by repository — so encoding a test would be wrong somewhere, and asking
is cheap where the owner is present.

The sibling intent proposes to hold governance items rather than route them,
precisely because this destination does not exist. Neither that intent nor this
one is implemented, so the holding is a proposed interim rather than current
behaviour — nothing is being held today because nothing is being captured.

## What exists today

**Snapshot taken 2026-09-19.** These are locations, not contents. Each names a
file and why this intent cares about it, and deliberately reproduces no value,
status, field content or count from it — a copy would be a second home for
another artifact's state, and the date would record only when the copy was made,
not whether it still holds. Open them.

- **The two record types.** `packs/governance-extras/.apm/skills/new-adr/` and
  `.../new-rfc/`. Read each template for its lifecycle vocabulary and for the
  field naming who answers — those two facts are what make a held question
  answerable, and they differ between the two.
- **Their write gates.** The authoring step of each `SKILL.md`. They are not the
  same; read both before assuming one contract.
- **The pack scope the classifier operates within.**
  `packs/core/.apm/skills/work-intake/SKILL.md`. The record-authoring skills
  above sit outside it, which is the boundary this intent leaves open.
- **The absent-pack precedent, as context only.** `work-loop`'s handling of a
  missing reviewer pack. It is scoped to reviewers and settles nothing here.
## Upstream state, 2026-09-21

The capture contract ships. A `decision`-shaped `work-item` — the input
this child routes — exists as a record, requires a `significance` list
naming why it needs a durable record rather than an in-session call, and
has a closed `blocker`.

This child remains blocked on `docs/specs/work-item-promotion-handoff/spec.md`,
which is not built. Nothing upstream changed its framing.

## Non-goals

- **The other routes.** Bug, improvement and the rest are the sibling's.
- **Authoring the record.** The record-creating skills exist; nothing here
  changes what they produce.

## Assumptions

- The destinations already exist and are not invented here.
- They live outside the core pack, while the classifier that would reach them is
  core's, so the route to them is conditional on the pack being installed. The
  capture sink is not, so an item always has somewhere to go.

## Decomposition

None. One outcome, one measure.

## De-risk

**Reversibility: mixed.** Removing the route restores today's behaviour, which
is that these items are held. What a successful route has already written is not
reversible: a decision record or proposal is created and indexed, and the
capture's terminal disposition cannot be replaced once recorded.

Whether a refusal writes at all is not settled here. It depends on whether a
refusal records a terminal disposition, which the store treats as an ordinary
terminal event — and that choice is listed below as the spec's.

**Riskiest assumption.** *The owner can reliably tell which record type a
captured question needs, from what the record carries.*

This is the feature's value proposition rather than its packaging. If the
distinction cannot be drawn reliably at drain time, the route either adds
ceremony without resolving anything or produces the wrong governance artifact —
and a wrong one is worse than a held item, because it reads as settled.

**Kill condition, with its basis.** Over ten captured governance items, the
owner cannot decide the record type for three or more from the record alone, or
reverses the choice on reading the original work. The basis for three is that
this route's whole claim is that asking is cheaper than encoding a rule; at one
in three the asking is not cheap, and the record is not carrying what the
decision needs — which is the dependency's problem surfacing here rather than
this route's.

**Deliberately not the kill condition: how common these items are.** An earlier
draft set the bar at a share of captures, anchored near a figure already
observed in a different population. Prevalence does not test acceptability: a
rare permanently stuck item may be intolerable, and a common hold may be fine
where installing the pack is routine. That measure would have been fitted, and
would have tested the wrong thing.

**A second bet, named because the kill condition does not reach it.** *Creating
a record that names a decider is enough for the question to reach that person
and be answered.*

This is the feature's actual value, and nothing here tests it. A record can be
created, indexed, correctly typed and correctly addressed, and still sit unread
— in which case a held item has become a filed item and the question is no
closer to an answer. Presentation, acknowledgement and decision latency are all
outside the current hook.

It is named rather than tested because testing it needs elapsed time and a real
decider, neither of which exists before capture runs. A spec should not treat
record creation as the finish line on the strength of this intent alone.

**Both probes need the dependency shipped.** Nothing can be asked of an owner
until items are being captured.

```
validation_hook:
  assumption: the owner can reliably tell which record type a captured
    question needs, from what the record carries
  kill_condition: over 10 governance items, the owner cannot decide the record
    type for 3 or more from the record alone, or reverses on reading the
    original work
  activity: once capture is running, walk ten governance items with the owner;
    record the choice, the confidence, and whether reading the original work
    changed it
```

## For the spec to decide

- **What an absent pack does.** The record-creating skills are not core's and
  the classifier is, so a route to them is conditional on the pack. The
  intended shape is two destinations: the capture sink, always reachable, and
  the governance record start, which refuses loudly and records when the pack
  is absent. That keeps `work-intake`'s core-alone guarantee, which binds its
  four named operations rather than every destination within them — the defect
  route's existing readiness precondition is the precedent for a conditional
  destination inside `start`. The spec settles the wording; an earlier draft
  said both "refused and recorded" and "writes nothing", which cannot both
  hold.
- **The elicitation contract** — who answers, what the choices are, and what
  happens on cancellation, an invalid answer, or no answer.
- **The terminal disposition** for each of success, refusal, cancellation and an
  unattended run.
- **Whether the two record types are the only destinations**, given that one
  opens at `Proposed` with decision-makers and the other at `Draft` with an
  approver — different shapes for what this intent treats as one class.
- **Which governance items this route admits**, and the terminal disposition of
  one it refuses. The `governance` kind and its write-time threshold are
  [FEAT-0006](FEAT-0006-work-item-capture-contract.md)'s, because capture writes
  the record; this route decides only what it accepts once written, and does not
  re-argue the kind definition. An item admitted at write time and refused here
  is a state the parent capability requires a disposition for, and no other
  artifact supplies one.
