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

## Invalid committed observations

The pending drain excludes an invalid journal line on its own and lists it in
the receipt's `diagnostics` as a location and a closed reason code, never as
record text. A capture whose disposition line is invalid is excluded too, rather
than shown as pending again, and a disposition whose capture is invalid is
excluded. A partition file that is a link or not a regular file is excluded as
`unsafe` and never read. When a partition holds an invalid line that cannot be tied to one
capture, the drain shows no capture from that partition. At most 100 entries are
listed, followed by one counted `overflow` entry.

A workflow-receipt selection whose named capture is excluded or hidden still
refuses with `replay_required`, so a gate never drains fewer captures than it
named. Every disposition and promotion still refuses the whole operation when
its partition or the topic store holds an invalid record; repair or revert it
through version control.
