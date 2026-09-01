---
id: hooks-common-floor
title: Hooks common floor
type: Reference
status: Active
license: Apache-2.0 OR MIT
---
# Hooks common floor

## Scope and routing signals

Use when a workflow wants something to happen reliably at a point in an agent's
lifecycle rather than depending on the model choosing to do it. Hooks are the
mechanism for that, and they are not portable: the floor decides whether a hook
is the right instrument, and the runtime profile decides whether it exists.

## Decisions and minimum evidence

Six distinctions decide the design. Deterministic enforcement or
model-interpreted guidance. Lifecycle observation or authority-changing
interception. Pre-action blocking or post-action diagnostics. Component-scoped
or repository, user, package, or managed scope. Trusted executable code or
untrusted repository instructions. A stable event, input, and output contract or
a runtime-specific envelope.

## Construction method

Choose enforcement only where the outcome must not depend on interpretation, and
keep the enforcing code trusted and reviewed. Prefer observation where a
diagnostic is enough. State the degradation before recommending a hook: where a
target runtime lacks the required capability, say so and keep enforcement at the
boundary that actually owns it, rather than describing a control the runtime
will not apply.

## Evidence and evaluation

Exercise the blocking path with an action that must be refused and confirm the
action does not occur. Exercise the observation path and confirm it changes
nothing. Exercise the degraded path, where the capability is absent, and confirm
the workflow still completes and reports that enforcement was not applied.

## Failure modes

Claiming enforcement a runtime does not provide leaves an unguarded boundary
that reads as guarded. Interpreting an untrusted repository file as hook
instructions executes attacker-chosen code. Putting a decision in a post-action
hook cannot undo the action it observed.

## Security and authority

A hook that enforces policy is executable code under the runtime's and the
organization's trust controls, not corpus advice. Corpus text can describe a
control; it cannot apply one. Managed policy may narrow or disable locally
declared hooks, so a design that depends on a hook running must state what
happens when it does not.

## Related topics

For the delegation boundary a hook may fire around, consult
`skills-and-subagents-common-floor`. For distributing hook components, consult
`plugin-package-common-floor`.

## Provenance and lifecycle

Portable floor for the agent-skill-engineering pack. Maintain as governed OKF
source; generated router copies are not authoring surfaces. Event names, matcher
semantics, configuration paths, and output protocols are runtime-specific and
are deliberately absent here.

**lifecycle interception contract:**
A hook executes automatically on a declared lifecycle event, and a declared subset of those events can block the action before it occurs.
Last verified: 2026-08-31.
Revalidate when either documented hook event model changes.
Claude Code hooks reference — https://code.claude.com/docs/en/hooks
Retrieved at: 2026-08-31. Version state: none exposed.
Kiro hooks documentation — https://kiro.dev/docs/hooks/
Retrieved at: 2026-08-31. Version state: 2026-08-21.
