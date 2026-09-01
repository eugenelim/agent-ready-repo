---
id: skills-and-subagents-common-floor
title: Skills and subagents common floor
type: Reference
status: Active
license: Apache-2.0 OR MIT
---
# Skills and subagents common floor

## Scope and routing signals

Use when deciding whether a skill should delegate work to a separate agent
context rather than continue in the caller's. Ask the capability questions
before reaching for any runtime's delegation syntax, because the syntax varies
while the questions do not.

## Decisions and minimum evidence

Eight questions decide the shape. Is the work better in the main context or an
isolated one? Which skill knowledge must the delegated agent receive — metadata,
full instructions, selected references, or a summarized brief? Does the runtime
inherit skills automatically, preload named skills, or require explicit paths?
Does the delegate share a filesystem or worktree, and who owns writes? Which
permission and tool restrictions survive delegation? Is nested delegation
supported, bounded, or prohibited? What concurrency cap, token budget, waiting
behavior, result contract, and synthesis owner apply? How are duplicate
exploration, conflicting writes, partial failures, and cancellation handled?

An answer that the floor cannot supply is a runtime question, not a gap in the
design. Record it as unresolved and consult the runtime profile.

## Construction method

Default conservatively. Delegate bounded, independent work. Prefer read-heavy
parallelism. Assign explicit ownership before any parallel write. Pass only the
skill context the delegate needs. Cap concurrency. Require a structured result
rather than free prose. Keep final synthesis and authority in the parent loop.

## Evidence and evaluation

Exercise a delegation that returns a structured result, one that fails partway,
and one that is cancelled. Confirm the parent still owns synthesis, that a
partial failure is visible rather than silently absorbed, and that no delegate
wrote outside the ownership the parent assigned.

## Failure modes

Delegating unbounded work returns a summary nobody can check. Parallel writes
without assigned ownership corrupt each other. Passing the whole caller context
defeats the isolation that motivated delegating. Treating a delegate's result as
authority moves the decision away from the loop accountable for it.

## Security and authority

A delegate receives no more authority than the task needs, and the parent
remains responsible for approvals. Permission and tool restrictions that do not
survive delegation are a capability question with a security consequence: where
a runtime cannot carry a restriction across the boundary, keep the restricted
operation in the parent instead.

## Related topics

For the container that distributes a delegate definition, consult
`plugin-package-common-floor`. For event-triggered execution, consult
`hooks-common-floor`.

## Provenance and lifecycle

Portable floor for the agent-skill-engineering pack. Maintain as governed OKF
source; generated router copies are not authoring surfaces. Runtime-specific
discovery, inheritance, nesting, and concurrency behavior belongs to the runtime
profiles and is deliberately absent here.

**Applicability limit:** This guidance is an observed practice from the seven
packs in the catalogue that developed this pack and ship agent definitions,
censused on 2026-08-31. It is not established beyond that population.
