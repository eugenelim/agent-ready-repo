# Distill Mode

Read bounded pending observations, bounded candidate topics, and explicitly named confined sources.

Use either an explicit workflow receipt list from the capture gate or a scoped
direct-maintainer pending drain. Pending captures remain non-queryable until a
terminal disposition is recorded.

Pass either selection request to `project-knowledge --distill --pending`.
After semantic triage, pass each explicit disposition or promotion proposal to
`project-knowledge --distill` without `--pending`.

The agent proposes the semantic decision: one terminal disposition and, only for
promotion, at most one topic mutation. Deterministic code validates the proposal,
applies the guarded mutation, appends exactly one terminal disposition, and
refuses ambiguous splits, contradictions, stale preconditions, or uncertain
routing.

Routing output is a suggestion for normal repository work intake. It must never
edit agent instruction files or adapter projections directly.
