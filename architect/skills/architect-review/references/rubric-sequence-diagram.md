# Sequence-diagram rubric — for `architect-review`

For critiquing a `sequenceDiagram` (Mermaid or other notation).

> Note: intentionally duplicated content with `architect-diagram`'s
> sequence guidance. Skill autonomy beats DRY at this scale.

## Universal

- [ ] **Renders.** Mermaid source parses.
- [ ] **Title or scope sentence** above the diagram names the flow.
- [ ] **Fits one screen.** If the flow is too long, split by scope
      sentence.

## Participants

- [ ] **All lifelines declared at top.** Every participant has a
      declaration before its first arrow.
- [ ] **Participants named with their role and tech.** "API service
      [Go, gRPC]" beats "API".
- [ ] **External actors clearly marked** — `actor` for humans;
      label external systems.

## Arrows

- [ ] **Synchronous vs. asynchronous arrows are different shapes.**
      Solid for sync (`->>`), dashed for async (`-)`). No mixing.
- [ ] **Every arrow has a message label.** Bare `A->>B` fails.
- [ ] **Returns rendered explicitly** when the caller waits for one.

## Flow shape

- [ ] **Error / alt paths shown** where they matter. A happy path
      with no error handling is a fiction.
- [ ] **Time skips noted.** `Note over A: waits 24h for human` or
      a separator — never a silent gap.
- [ ] **Parallel branches use `par`** when relevant; sequential
      lines don't pretend to be parallel.
- [ ] **No unexplained loops.** `loop` blocks have a clear exit
      condition.

## Notes

- [ ] **Assumptions surfaced.** Authorization state, prior
      context, retry policy — anything the picture can't show
      goes in a `Note over`.

## Severity mapping (typical)

- 🟥 **Blocker** — Happy path only with no failure handling;
  diagram contradicts the prose it's illustrating; unexplained
  time skips that change correctness.
- 🟧 **Major** — Participants un-typed; sync/async arrows
  inconsistent; one critical alt missing.
- 🟨 **Minor** — Activation bars used inconsistently; one
  long message label that should be a Note.
- ⚪ **Nit** — Alias style, label punctuation.
