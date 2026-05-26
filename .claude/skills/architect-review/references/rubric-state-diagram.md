# State-diagram rubric — for `architect-review`

For critiquing a `stateDiagram-v2` or other state-machine notation.

> Note: intentionally duplicated content with `architect-diagram`'s
> state guidance. Skill autonomy beats DRY at this scale.

## Universal

- [ ] **Renders.** Mermaid source parses.
- [ ] **Title or scope sentence** above names the lifecycle.
- [ ] **Fits one screen.** Composite states for nested detail.

## States

- [ ] **State names are nouns or past-tense verbs.** "Approved"
      passes; "Approve" fails (that's an event).
- [ ] **Initial state explicit.** `[*] --> Initial` so the reader
      knows where to start.
- [ ] **Terminal states explicit** when the lifecycle ends.
- [ ] **No unreachable states.** Every non-initial state has at
      least one inbound transition.

## Transitions

- [ ] **Every transition labeled** with the event that fires it.
- [ ] **Guard conditions surfaced** when transitions are conditional
      (`[reviewer=lead]` or similar).
- [ ] **Actions surfaced** when relevant (`/ send notification`).
- [ ] **No silent transitions.** A `A --> B` with no label is a
      gap, not a feature.

## Composite states

- [ ] **Used when the substates are load-bearing.** Don't nest
      for the sake of nesting.
- [ ] **Entry / exit transitions to the composite are explicit.**
      The reader sees how you get in and out.

## Concurrent regions

- [ ] **Used sparingly.** Concurrency is hard to read; reach for
      it only when the system is actually concurrent.

## Severity mapping (typical)

- 🟥 **Blocker** — Unreachable terminal state; transition with no
  event label; lifecycle has no initial state.
- 🟧 **Major** — One state named as an event; guard conditions
  missing on a conditional transition; composite state used
  decoratively.
- 🟨 **Minor** — Naming inconsistent (some states tense-mismatched
  with others).
- ⚪ **Nit** — Layout, label style.
