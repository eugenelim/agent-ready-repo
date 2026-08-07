# Self-coverage module — discovery-risk taxonomy

Part of the [self-coverage gate](coverage-record.md). Runs at **convergence** —
walk the canonical product-discovery risk taxonomy so a blind spot is *named*, not
silently skipped.

## The four risks (SVPG)

Walk every load-bearing slot of the converging spine against the four:

- **Value** — will anyone want it? Does the `intent` trace to a real outcome, and
  does the decision brief carry the required **success-metrics / North-Star slot**
  (the done-criterion the build loop iterates against)?
- **Usability** — can they use it? Is the journey / screen flow grounded in how the
  activity is *really* done (`frame-domain`), or in a fantasy of it?
- **Feasibility** — can we build it? Has the architecture lens (if installed) been
  consulted, or is feasibility assumed?
- **Viability** — does it work for the business / within constraints? Compliance,
  cost, and the regulated-data classification (routes to the discovery reviewers).

## The IEEE-29148 quality overlay

For each requirement-shaped slot, check it is **unambiguous, complete, consistent,
testable, traceable** — the attributes the self-coverage gate + traceability lint +
discovery reviewers already enforce. A slot that fails *testable* has no validation
hook; a slot that fails *traceable* is a lint orphan.

## Output

Each risk either **covered-with-referent** (name what grounds it) or **surfaced**
(a real gap the loop can't close — carries to the coverage record). The taxonomy is
a checklist of *lenses*, not a gate that re-decides value — a value gap surfaces to
the human at G2.
