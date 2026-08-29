---
id: progressive-result-presentation-and-next-actions
title: Progressive result presentation and next actions
type: Reference
status: Active
license: Apache-2.0 OR MIT
---
# Progressive result presentation and next actions

## Scope and routing signals

Use when a skill returns a result that may be complete, partial, blocked, or
ready for a later decision. Do not use it to turn a simple one-line result into
a status report.

## Decisions and minimum evidence

Lead with the current outcome and the next action that follows from it. Separate
completed work, unresolved risks, and requested decisions so a reader can
resume without reconstructing the procedure from tool narration.

## Construction method

Define the few result states the workflow can actually produce. For each state,
state the useful result first, then only the evidence, limitation, or next
action needed to continue. Keep routine progress quiet; surface a progress
update when a decision, safety boundary, material scope change, or long wait
changes what the user needs to know.

## Evidence and evaluation

Exercise a successful result, an incomplete result, and a result that needs
user input. Confirm that each names its state, preserves essential evidence,
and makes the next action clear without claiming a blocked task is complete.

## Failure modes

Chronological tool narration hides the outcome; an optimistic completion label
masks remaining work; and a vague request for input makes resumption depend on
unstated context.

## Security and authority

Do not expose secrets, protected paths, or raw diagnostics just to make a
result feel complete. A result may explain an authorization boundary without
disclosing the protected material behind it.

## Related topics

For concise output structure, consult
`instruction-density-and-progressive-disclosure`.

## Provenance and lifecycle

Foundation reference for the portable agent-skill-engineering pack. Maintain as
governed OKF source; generated router copies are not authoring surfaces.

**Applicability limit:** This guidance is an observed practice from the 137
authored agent skills in the catalogue that developed this pack, censused on
2026-08-28. It is not established beyond that population.
