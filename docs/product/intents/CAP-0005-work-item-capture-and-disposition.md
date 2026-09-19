# Work-item capture and disposition

- **Slug:** `work-item-capture-and-disposition` <!-- canonical identity; independent of the filename ordinal -->
- **Status:** Accepted
- **Level:** capability
- **Scale:** app
- **Maturity:** brownfield
- **Parent intent:** none

## Outcome

- **Steerable input:** Reduce the share of work a loop notices and cannot do that leaves no record anyone can act on.
- **Lagging outcome:** Work a loop declines is either done in the same session or recorded so that a later session *could* act on it without re-deriving what the first one knew. Whether anyone does is a maintainer's call, not this capability's promise. What is recorded is a well of potential, not a commitment: a maintainer promotes from it or prunes it as they need.
- **Guardrail:** Recording stays rarer than doing. A loop that can dispose of an item in-session does so rather than filing it, because a record pays a tracking cost and a re-derivation cost to buy nothing. An item is validated before it is captured, so the well holds potential rather than noise. Nothing captured is treated as agreed work until a human has dispositioned it, no capture obliges anyone to act, and an unpromoted item is not a defect.

## Opportunity

A loop that notices work it should not do has nowhere cheap to put it, so the cheapest exit wins.

Measured across sixty merged pull requests over four days, **233 deferred items** were stated in pull-request descriptions. **One of the last forty merge commits** carried that section into the git history at all, so the items are written to a surface that is not versioned against the code and is never re-presented to anyone. Of a 58-item sample cross-referenced against the repository's own queue, **16 reached it**.

The items that do survive are frequently unusable, because capture at the end of a loop is reconstruction from the diff rather than recall: it recovers the artifact and loses the fact that makes the artifact actionable. Three worked examples are recorded in this capability's children.

Under current guidance this is not an accident. The close-time routine sorts scratch notes into generalisable practice, which is kept, and everything else, which is discarded — so a specific, real, non-generalisable defect is thrown away by instruction.

## Boundary

This capability owns the path a noticed-but-undone item takes: whether it is captured at all, what a capture must carry to be actionable later, where it goes when it leaves, and when it is closed without going anywhere.

Validity is part of "whether it is captured at all": an item that cannot be established as real is not written. What that check tests, how it runs, and what a refusal does are the capture child's, not this capability's.

It does not own:

- **The model of repository work as a graph**, or navigation over it. A captured item is upstream of that graph and enters it only on promotion.
- **The accepted decision corpus**, its records or its view. A captured question may become a decision record; what that record is and how it is read belongs elsewhere.
- **Where coordination state lives**, or the shape of the registry that holds it.
- **Doing the work.** Every destination this capability routes to is an existing owner with its own contract.

## Decomposition

Four children, cut by the question each answers rather than by the artifact each touches.

- [Work-item capture contract](FEAT-0006-work-item-capture-contract.md) — what a record must carry for a later session to act on it, and what is refused before it is written. Answers *is it real, is it worth recording, and is the record usable*.
- [Work-item promotion routing](FEAT-0007-work-item-promotion-routing.md) — handing a captured item to the owner that handles work of its shape, and closing its capture, including closing one that goes nowhere because it is stale, superseded or overtaken. Answers *where does it go or why does it not, and has it left the well*.
- [Governance item record routing](FEAT-0008-governance-item-record-routing.md) — the route for an item whose deliverable is a decision rather than work. Answers *who decides this*.
- [Duplicate coverage offer](FEAT-0009-duplicate-coverage-check.md) — surfacing an artifact that already covers an item before promotion creates a second one. Answers *does this already exist*.

### Decomposition decisions

- **The cut is by question, not by layer.** Capture and promotion could have been one child, since neither is useful alone. They are separate because their bets fail differently: capture fails if a record cannot be acted on, promotion fails if a record cannot be routed, and a single child would let a green result on one stand in for the other.
- **The two specialised routes are children rather than parts of promotion.** Governance routing crosses a pack boundary and elicits from a human; duplicate coverage is a control that runs before a write. Each has its own measure and its own failure mode, and promotion ships without either — holding governance items and creating without checking — which is worse than today only in the second case.
- **This capability has no parent.** It is not part of a larger arc. The work-graph strategy owns the model of work the loops act on, and the platform strategy's decomposition is closed; neither claims the path an undone item takes, and attaching to the nearer of the two would be accretion rather than placement.

## Assumptions

- The existing capture store is sufficient. No new store is built, and the children inherit its properties — including that its records are append-only and that a terminal disposition, once recorded, is not replaced by a conflicting one.
- A destination exists for every kind of item this capability admits, or the item is held rather than forced somewhere.
- Ready-now work is dispatched in-session. This capability's volume depends on that holding; if ready items are captured instead, the register fills with work that should have been done.

## De-risk

**Reversibility: two-way for this capability, one-way for what its children write.**
This artifact is a framing document — retiring it re-homes four children and
changes no state. Its children are not: captured records are append-only, and a
terminal disposition, once recorded, is not replaced by a conflicting one. The
capability can be withdrawn; what it has already caused to be written cannot.

## Riskiest assumption

*The well is drawn from.*

This capability exists to prevent session loss: work a session noticed and could
not do should be recoverable later rather than evaporating. A sink serves that
whether or not it empties — an item sitting unpromoted is potential retained,
not a backlog going stale, and pruning is a disposition rather than a failure.

So the failure is not accumulation. It is a write-only store: items go in,
nobody ever promotes or prunes, and the sink has relocated session loss rather
than prevented it. Work that was invisible in a pull-request body is then
invisible in a file nobody opens, at the cost of the machinery to put it there.

**Kill condition, predeclared.** Over two consecutive quarters after capture
ships, no captured item leaves the well in either direction — nothing promoted
and nothing discarded. Zero of both, not a low rate of either: a maintainer
drawing on the well occasionally is the intended behaviour, and only total
disuse falsifies the bet. Two quarters rather than one because a well is
allowed to fill before anyone needs it.

**This test cannot run as written, and that is a delivery obligation rather
than a caveat.** "Promoted" maps to an existing terminal disposition. "Pruned"
does not — the store's terminal set has no such value, and the closest
existing ones carry different meanings. Either a disposition for discarding is
added, or two existing ones are designated to mean it. Until that mapping is
decided the count is unreadable, so the mapping is part of delivering this
capability, not of measuring it afterwards.

Note what this deliberately does not measure: how much was lost before. Items
that evaporated left no trace, so the loss this capability prevents is not
countable, and any figure claiming to count it would be invented.

**No probe supports this assumption, and none is proposed before delivery.**
A well is drawn from or it is not, and that is observable only once one exists
and someone has had reason to reach into it.

This repository runs a register with a manual disposal path and it is used, but
that is one repository, one stack and one maintainer, and it was not built as a
sink. It is not a smaller version of this bet and is not offered as support for
it — it is recorded in this session's history as background, not carried here
as evidence. A reader looking for grounds to believe the assumption will not
find any in this artifact, which is the accurate state.

```
validation_hook:
  assumption: the well is drawn from — maintainers promote from it or prune it
  kill_condition: over two consecutive quarters after capture ships, zero
    captured items are promoted and zero are pruned
  activity: read the disposition counts at each quarter boundary; on a kill,
    the sink is write-only and the machinery should be withdrawn rather than
    extended
  unmeasurable: the session loss this prevents. Evaporated items leave no
    trace, so the counterfactual cannot be counted and no proxy for it is
    proposed
  local_only: this repository's register drains, which is informational about
    one stack and one maintainer and is not evidence about an adopter
```

## Unresolved questions

- Whether a capability-level measure exists that is not just the sum of its children's. The steerable input above is readable per-child; whether the capability as a whole has a distinct one is unsettled.

