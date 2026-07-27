# User-facing documentation

> The product's user-facing docs, organized by the
> [Diátaxis framework](https://diataxis.fr/). Four kinds of documentation,
> each serving a different user need. Each piece of content belongs in
> **exactly one** bucket — mixing kinds is the most common cause of
> documentation that frustrates everyone.

## The four kinds

|  | Practical (the user does something) | Theoretical (the user understands something) |
| --- | --- | --- |
| **Learning-oriented** (skill acquisition) | [`tutorials/`](tutorials/) — *Lessons.* "Take me through it from the start." | [`explanation/`](explanation/) — *Discussions.* "Help me understand why." |
| **Task-oriented** (goal accomplishment) | [`how-to/`](how-to/) — *Recipes.* "Help me solve this specific problem." | [`reference/`](reference/) — *Information.* "Tell me exactly what this thing does." |

## Quick decision guide

Before you write something, decide **which one** it is:

- **Tutorial** — if a beginner could follow your text from start to finish
  and end up having learned something. The reader is on rails. Has a
  guaranteed outcome ("at the end you'll have a running X"). Don't
  digress to explain — link out.
- **How-to guide** — if it solves a specific real-world problem the
  reader brought with them. Assumes baseline competence. Doesn't teach;
  helps. Don't include backstory — link out.
- **Reference** — if it's the authoritative description of an interface,
  config option, command, or API. Dry, complete, accurate. Don't
  editorialize — link out.
- **Explanation** — if it answers "why" or "how does this work, deeply".
  Theoretical, contextual, opinionated. Doesn't teach a skill, doesn't
  solve a task — illuminates. Don't include step-by-step instructions —
  link out.

The "link out" principle is the whole framework. When you find yourself
wanting to add explanation in the middle of a tutorial, that's the signal
to write a separate explanation page and link to it.

## How this fits with the rest of the repo

User-facing docs are *living* — they must match current product behavior.
This is different from:

- [`../specs/`](../specs/) — feature contracts, frozen once shipped.
  Specs are written for *contributors*; user docs are written for *users*.
  Once a feature ships, the spec is reference material for the team and
  the user-facing reference page is the source of truth for users.
- [`../adr/`](../adr/) — architecture history. Internal.
- [`../CHARTER.md`](../CHARTER.md) — project mission. Internal-leaning.

When a feature ships:

1. Its spec becomes part of the team's permanent record.
2. A reference page goes (or is updated) in [`reference/`](reference/).
3. If the feature changes how users do things, a how-to goes in [`how-to/`](how-to/).
4. If the feature is a new core concept, an explanation goes in
   [`explanation/`](explanation/) and the quickstart tutorial may need updating.

That last bullet is the part teams skip. Skipping it is how docs rot.

## Maintenance rules

See [`../CONVENTIONS.md`](../CONVENTIONS.md#document-lifecycle) for the
full lifecycle treatment. The short version: every PR that changes
user-visible behavior touches user docs in the same PR, or explains in
the description why it doesn't need to.
