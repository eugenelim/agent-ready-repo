# Dogfood brief — non-cloud design question

> **Fixture for `well-architected-cloud` manual QA.** Confirms the Stage-0
> concept **degrades gracefully** when no provider is in play. Referenced by
> path so the gesture is replayable.

## The brief

We maintain a **CLI tool** that parses large log files and emits a summary. Users
run it on their own machines. It's getting slow on multi-GB files and the parser
code has grown into one tangled module.

We're deciding **how to restructure the parser**: a single streaming pass with a
state machine, or a two-pass approach (index, then summarize). We want it to stay
a dependency-light single binary.

Constraints: must stay offline / local (no network calls), must not add heavy
dependencies, must handle files larger than memory.

Question: which parser shape should we choose, and why?

---

## Expected observables (QA scaffolding — not part of the brief)

- `architect-design`'s **Stage-0 concept still runs**: it shapes **problem /
  constraints / candidate shapes (streaming vs. two-pass) / quality attributes**
  (here: performance on large-out-of-memory files, maintainability).
- It does **not** force **provider selection** or **pillar-by-construction
  scaffolding** — there is no cloud in play, and the concept doesn't manufacture
  one.
- The streaming-vs-two-pass choice is surfaced as the **key tradeoff** (memory
  footprint vs. random-access flexibility).
