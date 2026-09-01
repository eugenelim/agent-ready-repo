---
id: plugin-package-common-floor
title: Plugin package common floor
type: Reference
status: Active
license: Apache-2.0 OR MIT
---
# Plugin package common floor

## Scope and routing signals

Use when a set of skills and adjacent components is about to be distributed as
one installable unit. A package is a distribution container, not a universal
manifest, so the floor covers what any container must answer and leaves the
manifest to the runtime profile.

## Decisions and minimum evidence

Seven concerns decide whether the unit is coherent. Component cohesion: do these
components belong together for a reason a user would recognize? Least authority:
does the package request only what its components need? Dependency disclosure:
what does it pull in, and is that visible before install? Install-time trust:
what is the user agreeing to execute? Update and version provenance: how does a
consumer know what changed and where it came from? Namespace collision: what
happens when two packages claim the same name? Independent disable and recovery:
can one component be turned off, and does uninstall leave nothing behind?

## Construction method

Package by user-recognizable purpose rather than by authoring convenience.
Declare dependencies where a consumer sees them before installing. Namespace
components so a collision is detectable rather than silent. Make disable and
uninstall complete: no residual executable component, permission, writable
state, or entry that shadows a user's own.

## Evidence and evaluation

Install, update, disable, and uninstall the package, and after each step check
what remains. The uninstall check is the load-bearing one: confirm no hook,
executable component, permission, writable state, or shadowing entry survives.

## Failure modes

A package assembled by authoring convenience gives users components they cannot
explain. Undeclared dependencies surprise at install time. Silent namespace
collision shadows a user's own component with one they did not choose. An
uninstall that leaves executable residue leaves authority the user believes they
revoked.

## Security and authority

Installing a package is a supply-chain decision: its components are instruction
and code inputs, and install-time trust is the moment the user grants them
authority. A package must not embed credentials or invent a cross-runtime
credential field; authentication stays with the client. Where a runtime's
managed policy can narrow or disable a package, a design depending on it must
state what happens when it is narrowed.

## Related topics

For the components a package most often carries, consult
`skills-and-subagents-common-floor` and `hooks-common-floor`.

## Provenance and lifecycle

Portable floor for the agent-skill-engineering pack. Maintain as governed OKF
source; generated router copies are not authoring surfaces. Manifest shape,
install commands, and enablement behavior are runtime-specific and are
deliberately absent here.

**Applicability limit:** This guidance is an observed practice from the 23 packs
in the catalogue that developed this pack and ship a package manifest, censused
on 2026-08-31. It is not established beyond that population.
