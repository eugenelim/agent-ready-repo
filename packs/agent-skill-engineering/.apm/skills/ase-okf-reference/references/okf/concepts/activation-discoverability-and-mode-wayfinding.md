---
id: activation-discoverability-and-mode-wayfinding
title: Activation, discoverability, and mode wayfinding
type: Reference
status: Active
license: Apache-2.0 OR MIT
---
# Activation, discoverability, and mode wayfinding

## Scope and routing signals

Use for a skill with more than one user-visible mode or a workflow that begins
by identifying the user's intended operation. Do not use modes as labels for
minor implementation choices that the skill can make internally.

## Decisions and minimum evidence

Describe the task outcome and the distinction between modes in the activation
description. Give each mode a clear entry condition, retained boundaries, and
the authority it needs. When intent or target is ambiguous, begin with a
read-only framing mode.

## Construction method

Choose a safe default that can clarify intent without mutation. Require an
explicit transition before a mode crosses into writes or external side effects.
At the transition, state the target, scope, retained behavior, and verification
that apply to the selected operation.

## Evidence and evaluation

Use prompts for each intended mode and ambiguous prompts that should remain in
the safe default. Check that a mode-specific request reaches its procedure and
that a request lacking an authorized target does not perform a mutation.

## Failure modes

Overlapping mode names make routing arbitrary; a write-capable default makes
ambiguity unsafe; and describing modes only in deep references leaves users
without a reliable way to choose one.

## Security and authority

Activation selects guidance, not authority. A transition to a write or remote
operation needs its own explicit authorization and cannot inherit it from a
read-only mode.

## Related topics

For trigger quality, consult `framing-and-trigger-quality`. For routing
conditional detail, consult `inline-and-progressive-reference-skills`. This
topic's authority rule applies to choosing between modes; a question about what
activation itself grants, where no second mode is in play, belongs to
`framing-and-trigger-quality`. Which modules a mode loads, and where a file's
information is placed, belong to
`instruction-density-and-progressive-disclosure`; this topic covers entry
conditions and how a reader chooses between modes, not loading mechanics.

## Provenance and lifecycle

Foundation reference for the portable agent-skill-engineering pack. Maintain as
governed OKF source; generated router copies are not authoring surfaces.

**Applicability limit:** This guidance is an observed practice from the 137
authored agent skills in the catalogue that developed this pack, censused on
2026-08-28. It is not established beyond that population.
