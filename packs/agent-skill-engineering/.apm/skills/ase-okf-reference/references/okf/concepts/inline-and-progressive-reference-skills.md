---
id: inline-and-progressive-reference-skills
title: Inline and progressive-reference skills
type: Reference
status: Active
license: Apache-2.0 OR MIT
---
# Inline and progressive-reference skills

## Scope and routing signals

Use for a skill whose main workflow needs a short, usable path while some
decisions need deeper, conditional guidance. Do not use this topic to split a
small procedure merely to create more files.

## Decisions and minimum evidence

Keep the activation boundary, essential sequence, stopping conditions, and
user-visible result inline. Put a detail in a reference only when a named
condition determines whether it is needed, and give the main procedure a clear
route to that reference.

## Construction method

Start with the smallest end-to-end procedure. Name each conditional concern at
the step that discovers it, then load only the reference needed for that
concern. Keep references navigable from an index or an explicit link, and do
not make a reference a second top-level workflow.

## Evidence and evaluation

Exercise the normal path without loading optional material. Then exercise each
condition that should load a reference and confirm that it reaches the intended
detail without changing the main procedure's authority or outcome.

## Failure modes

An inline procedure that repeats every exception becomes hard to use; an
unrouted reference becomes dead content; and a reference that silently changes
the workflow's scope makes the result unpredictable.

## Security and authority

References may add decision support, not authority. Keep permission checks at
the operation that needs them, including when the relevant guidance is loaded
later.

## Related topics

For reusable inert knowledge, consult
`depth-libraries-and-okf-knowledge-providers`. For concise source structure,
consult `instruction-density-and-progressive-disclosure`. This topic owns one
decision: which detail belongs on the always-read path and which belongs
behind a condition. Every other question about the same files — whether an
over-long entrypoint should be split at all, where information belongs once it
is, how long a source may run, and auditing whether a resource has a caller —
stays with `instruction-density-and-progressive-disclosure`, which owns
resource discovery and placement.

## Provenance and lifecycle

Foundation reference for the portable agent-skill-engineering pack. Maintain as
governed OKF source; generated router copies are not authoring surfaces.

**Applicability limit:** This guidance is an observed practice from the 137
authored agent skills in the catalogue that developed this pack, censused on
2026-08-28. It is not established beyond that population.
