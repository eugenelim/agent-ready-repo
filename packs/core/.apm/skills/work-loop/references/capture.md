# Capture: what to write, and what makes a note worth keeping

Load when routing a DECIDE scratch note to the `project-knowledge` seam.
`SKILL.md` § Capture owns when capture runs and points here; this file owns the
routing rule and its table — which destination a note reaches — what a kept note
should say, and the worked examples of those destinations.

## The question a capture answers

Before the PR is opened: *What would have made this work materially better —
more correct, complete, reliable, recoverable, secure, privacy-preserving,
deterministic, reproducible, operable, maintainable, reviewable, efficient, or
independent of hidden context?*

Speed is one useful signal, not the objective. A learning is worth keeping
when knowing it would materially change a future approach along one or more
of those attributes.

## Write the lesson, not the incident

Strip the PR details and write what you would tell a new team member. If the
only thing you can write is "in PR#42 we had to…", it is not ready: the
incident is not the lesson, and a reader without that PR in front of them
gets nothing from it.

This is the same discipline the discriminator serves on the capture side. A
note that records where something was found, without the fact the decision
turns on, is a locator; it looks like tracked work and is not.

## Routing to the seam

Use semantic-gate triage before writing anything. Route or discard normative
material first, then invoke the public `project-knowledge` producer profile.
It owns receipts and terminal-gate distillation; unresolved observations
remain pending. Any knowledge diff returns through the next verification and
review barrier before commit. If unavailable, record
`project-knowledge unavailable`; create no fallback file.

## Capturing and routing a note

A captured item carries its discriminator: the one fact the decision turns
on, not just the location. "Four sites use a 13px literal" is a locator;
"the third of them is the only sans one, so the shared token does not fit
it" is an item. Supply the discriminator before capturing; an item you
cannot give one to is not ready to capture, and it goes to the destination
its actual state names. A locator nobody can action looks like tracked work
and is not. Disposing an item now is cheaper than recording it: a recorded
item pays a tracking cost, a context-refresh cost, and often a new session,
and then still needs a discriminator that close-time reconstruction from
the diff cannot recover. A slightly longer loop is the cheaper option, and
capturing a ready-now item is a loss.

- **Review scratch notes** from this session's DECIDE passes. Anything
  generalisable that would have changed the approach goes to the
  `project-knowledge` public seam, and the examples in the capture reference
  are instances of that; the seam is additive. A note that names a defect
  routes by what it is:

  | What the note is | Where it goes |
  | --- | --- |
  | Generalisable practice | The existing `project-knowledge` route, unchanged |
  | Specific, real, blocked | Captured as a `work-item` |
  | Specific, real, ready now, ride-along eligible | Dispatched in-session, not captured |
  | Specific, real, ready now, not ride-along eligible | The session's next independently reviewed unit |
  | Specific, failing the razor | Refused, non-silently |

  Take the first row that applies and stop: a defect blocked on a decision, an
  instrument, elapsed time, or a dependency is captured as a `work-item`; a
  ride-along-eligible defect is dispatched now, grouped with related fixes
  sharing a file or a seam, over the human gate's `blocker-applied` return
  edge; a ready-now defect that is not ride-along eligible becomes the next
  independently reviewed unit in this session, over that same edge, where
  ready-now means it can be finished this session without a decision nobody
  present will make; and a defect the razor refuses — one an existing
  artifact already covers, or one no capture criterion admits — is refused,
  non-silently, rather than discarded. What a
  `work-item` capture must carry, what the razor checks, and what a refusal
  tells the author are in
  [Close-time work-item branch](work-item-capture.md#what-a-work-item-capture-must-carry).
  Before any `work-item` is written, one cold reasoning check runs per
  declined item, over at most twelve per close; an unavailable, timed-out,
  or unrecognized check refuses rather than admits — see
  [The reasoning check](work-item-capture.md#the-reasoning-check).
  A note that names no defect is done once the seam has taken it, and
  discarded if it had nothing for the seam either.

## Worked examples of destinations

Instances of the routing rule above. Each is a note shape
seen often enough to name, with the destination it reaches.

- "Grepped for `<thing>` repeatedly" → pointer in `docs/architecture/<subsystem>.md`.
- "The test command for this package is unusual" → add it to the package's `AGENTS.md`.
- "Made the same wrong assumption twice" → knowledge-base-shaped: the seam route above. Project-conventions context: relevant `AGENTS.md`. Vocabulary issue: `docs/guides/reference/` glossary.
- "This workflow is the third time I've done it" → propose it as a new skill.
