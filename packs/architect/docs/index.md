# Architect

> Assess the architecture that exists, decide what to do next, design the future,
> diagram it, and review the evidence.

Ask **“Assess architecture and provide an action plan”** for a progressive
current-state assessment. You first get a conceptual map and evidence coverage
to correct, then an attention heat map to redirect before detailed
investigation. Standard mode finishes with traced findings and action waves;
survey stops earlier; deep adds separately authorized evidence.

## What ships

**User-facing skills (4):** `architect-assess`, `architect-design`,
`architect-diagram`, and `architect-review`.

**Knowledge router (1):** `architecture-lenses-reference`, generated from the
pack's reference-only architecture corpus and used internally by assessment,
design, and review.

**Subagent (1):** `design-reviewer`, a forked-context, read-only reviewer for
design and assessment artifacts. It flags; it never rewrites or re-assesses.

The assessment is read-only by default. Its optional profiler executes no
repository code, installs nothing, and returns evidence signals rather than a
score. Private retrieval, executable checks, runtime access, experiments, and
writes require approval.

See the [architect guide home](../../../guides/architect/README.md) for task-led
instructions.
