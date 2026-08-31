---
id: framing-and-trigger-quality
title: Framing and trigger quality
type: Reference
status: Active
license: Apache-2.0 OR MIT
---
# Framing and trigger quality

## Scope and routing signals

Use for skill purpose, naming, descriptions, activation boundaries, positive
and negative prompts, user intent, and deciding whether a skill should exist.
Do not route generic feature design or prose editing here merely because an
agent will perform the work.

## Decisions and minimum evidence

Name the observable task outcome, users, realistic prompts that should and
should not activate, adjacent skills, authority boundaries, and explicit
non-goals. A useful description distinguishes the requested task at discovery
time without exposing internal implementation vocabulary.

## Construction method

Frame before writing. Prefer a short action-oriented name, a discriminating
description, and the smallest workflow that adds non-obvious decision support.
Keep automatic discovery unless the product explicitly requires manual-only
invocation; operational sensitivity belongs at the authorization boundary,
not hidden in activation.

## Evidence and evaluation

Version activation positives and negatives. Include near misses from generic
writing, coding, architecture, review, and repository maintenance. Evaluate
whether the correct skill is selected, whether unrelated prompts remain dark,
and whether ambiguous intent stays in a read-only frame.

## Failure modes

Catchall descriptions cause false positives; lists of implementation detail
hide the actual user task; examples mistaken for universal policy narrow the
skill incorrectly; and creating a skill where ordinary agent capability is
sufficient adds maintenance without value.

## Security and authority

Activation never grants filesystem, network, credential, identity, or external
side-effect authority. Require the relevant authorization immediately before
the operation and preserve the user's selected scope.

## Related topics

For file layout and progressive loading, consult
`instruction-density-and-progressive-disclosure`. For deterministic helpers and
exit behavior, consult `resources-scripts-and-exit-contracts`. Activation
boundaries and the authority a trigger does not grant stay here, for a skill of
any shape; consult `activation-discoverability-and-mode-wayfinding` only when
the question is how a reader chooses between two or more user-visible modes.

## Provenance and lifecycle

Foundation reference for the portable agent-skill-engineering pack. Maintain as
governed OKF source; generated router copies are not authoring surfaces.

**Applicability limit:** This guidance is an observed practice from the 137
authored agent skills in the catalogue that developed this pack, censused on
2026-08-28. It is not established beyond that population.
