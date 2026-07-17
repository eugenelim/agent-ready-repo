# Self-coverage module — fresh-context adversarial review

Part of the [self-coverage gate](coverage-record.md). Runs **pre-G2** (the REVIEW
phase of the loop), and is the discovery analogue of `work-loop`'s
adversarial-reviewer pass.

## The move

A design reviewed in the same context that authored it **marks its own homework**.
The fix is a **forked context** that never saw the authoring chain-of-thought — it
is seeded with the artifacts + the grounded reference + the constraints, and
nothing about *how* the design was reached (the narrative is exactly what biases a
reviewer toward agreeing).

## Who runs

The **loop-scoped discovery reviewer roster** (keyed to
loop + work type), **required at G2 reconcile**:

- **`discovery-threat-reviewer`** — the threat-modeling + regulated-domain
  compliance lens.
- **`discovery-reliability-reviewer`** — the reliability / operability lens over
  the journey / blueprint / architecture.
- **Optional, detect-and-degrade:** `experience-reviewer` (if `experience` is
  installed — UX/design artifacts) and `design-reviewer` (if `architect` is
  installed — architecture artifacts).

They are **distinct agents from `work-loop`'s code reviewers** and **degrade only
in depth, never to nothing**. A security-boundary crossing with only baseline depth
installed **surfaces to the human** (the non-degradable-lens control).

## Output

Severity-tagged findings. Every fresh-context finding is **resolved or explicitly
deferred with a reason** before G2 — the done-checklist refusal in the coverage
record will not let G2 be declared otherwise. Conflicts: factual →
`discovery-lead` arbitrates via referents; value → the human at G2.
