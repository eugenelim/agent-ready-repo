# Capture: what to write, and what makes a note worth keeping

Load when routing a DECIDE scratch note to the `project-knowledge` seam.
`SKILL.md` § Capture owns the routing rule and its table — which destination a
note reaches — and this file owns what a kept note should say, plus the worked
examples of those destinations.

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

## Worked examples of destinations

Instances of the routing rule in `SKILL.md` § Capture. Each is a note shape
seen often enough to name, with the destination it reaches.

- "Grepped for `<thing>` repeatedly" → pointer in `docs/architecture/<subsystem>.md`.
- "The test command for this package is unusual" → add it to the package's `AGENTS.md`.
- "Made the same wrong assumption twice" → knowledge-base-shaped: the seam route above. Project-conventions context: relevant `AGENTS.md`. Vocabulary issue: `docs/guides/reference/` glossary.
- "This workflow is the third time I've done it" → propose it as a new skill.
