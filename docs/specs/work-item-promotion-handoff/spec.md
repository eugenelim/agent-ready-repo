# Spec: Hand a captured item to its owner and close its capture

- **Status:** Draft
- **Owner:** eugenelim
- **Mode:** full
- **Brief:** none
- **Discovery:** docs/product/intents/FEAT-0007-work-item-promotion-routing.md
- **Constrained by:** none recorded yet

> **Draft, materialised ahead of shaping.** Nothing here is agreed.

## Objective

Give the capture store an exit: hand a triaged item to the classifier that
already handles work of its shape, and commit the terminal disposition once it
has gone. The classifier and its input shapes exist; the step that reaches them
does not.

**Two corrections the parent records, repeated because a spec author will
otherwise assume the opposite.** The defect route materialises an artifact
*and* registers a workspace entry — it is not a bare handoff to a processor.
And the store refuses a second terminal event against a capture, so a
mis-routed item cannot be re-dispositioned.

## Decisions this spec owes

- **Atomicity across four effects** — artifact creation, workspace
  registration, handoff, and the terminal disposition — one of which is
  irreversible. A crash between them either creates work without closing the
  capture, or closes it without the handoff. Ordering, idempotency, retry and
  recovery all follow from this and nothing else settles it.
- **Which captured fields decide each destination**, and the behaviour when
  they are absent, stale, or contradict each other.
- **When routing happens and what invokes it** — whether the classifier is
  extended or called, and at what point in a drain.
- **The trust boundary on captured content.** Prose, paths and commands written
  by an earlier session become classifier inputs here.
- **Attended versus unattended operation** — who may confirm a route, and what
  must remain held when nobody can.
- **The adjudicator and rubric** the routing measure depends on. The parent
  names the repository owner, which makes the test runnable but not
  reproducible across readers.

## Testing Strategy

- After one drain, have the named adjudicator read the original work behind ten
  items the drain was **offered** and judge its disposition of each — routed
  and held alike, since sampling only routed items lets a drain that holds
  every hard case pass.
- Drive a crash between each pair of the four effects; assert no state in which
  work exists without its capture closed, or a capture closes without handoff.
- Assert a second terminal disposition against one capture is refused, not
  silently dropped.

## Acceptance Criteria

- [ ] A triaged item reaches the classifier and its capture records a terminal
      disposition.
- [ ] The four effects commit as one recoverable unit, per the atomicity rule
      this spec settles.
- [ ] An item the drain cannot route is held, and the run reports the held
      count alongside the routed count.
- [ ] A governance item is held until its own route exists; nothing else is
      blocked by that absence.
- [ ] A mis-routed item's capture cannot be re-dispositioned; the recovery path
      this spec names is the only one.
