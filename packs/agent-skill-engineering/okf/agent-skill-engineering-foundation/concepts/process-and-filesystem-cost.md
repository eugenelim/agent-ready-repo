---
id: process-and-filesystem-cost
title: Process and filesystem cost
type: Reference
status: Active
license: Apache-2.0 OR MIT
---
# Process and filesystem cost

## Scope and routing signals

Use for skill scripts and evaluations that repeat process launches or filesystem
work across many items. It does not prescribe general deployment or operations
practice.

## Decisions and minimum evidence

Measure the repeated unit before choosing its implementation. Per-item process
spawning was treated as free. Separate process startup, filesystem traversal,
and useful computation so the costly unit is visible.

## Construction method

Batch independent queries when one invocation can return all needed results.
Traverse a bounded tree once, retain only the data needed by the next step, and
use temporary files only when an in-memory handoff cannot carry the result.

## Evidence and evaluation

Record item count, process count, elapsed time, and the preserved result for a
representative evaluation. Compare the single-item form with the batched form
before retaining added coordination.

## Failure modes

A loop that launches one process per item can dominate total runtime. Repeated
directory walks duplicate I/O. A batch can be incorrect if it changes ordering,
error reporting, or per-item isolation without an explicit replacement.

## Security and authority

Batching does not relax input validation. Keep path confinement and argument
boundaries at the batch edge, and avoid retaining sensitive intermediate data
beyond the evaluation that needs it.

## Related topics

For package-level duplication, consult `pack-and-ci-critical-paths`. For
temporary-path ownership, consult `python-and-pytest`.

## Provenance and lifecycle

**Process cost:**
Per-item process spawning was treated as free.
Last verified: 2026-08-30.
Revalidate when another independent execution-cost failure is observed.
