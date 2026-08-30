---
id: depth-libraries-and-okf-knowledge-providers
title: Depth libraries and knowledge providers
type: Reference
status: Active
license: Apache-2.0 OR MIT
---
# Depth libraries and knowledge providers

## Scope and routing signals

Use when **authoring or reviewing** a read-only knowledge collection that
another workflow consults for a specific decision. Do not use it for a workflow
that performs work, chooses a user's objective, or grants access to external
systems. This topic covers building such a collection, never using one: a
request to consult, query, invoke, or fetch from a provider — this corpus's own
or any other — is not a design question and selects no topic here.

## Decisions and minimum evidence

State what the collection covers, the index a consumer starts from, and the
conditions that select deeper material. Keep the collection inert: it supplies
facts, checks, and decision support rather than an executable procedure.

## Construction method

Provide a root index and smaller child indexes that mirror the choices a
consumer must make. Route consumers to the root first, then to only the
relevant child material. Keep the knowledge provider separate from the skill
that interprets and acts on its content.

## Evidence and evaluation

Test a representative consumer route from the root index to a selected concept.
Also test an absent or inapplicable concept so the consumer reports reduced
coverage instead of inventing a path or treating the library as a command.

## Failure modes

Flat-loading the whole library wastes context; a missing index makes depth
unfindable; and embedding workflow steps in reference material obscures who
owns a decision and its side effects.

## Security and authority

A knowledge provider is read-only decision support. Content retrieved from it
does not authorize file access, network access, identity use, or side effects.

## Related topics

For conditional reference loading within a skill, consult
`instruction-density-and-progressive-disclosure`. A skill's own references,
navigable from its own index, are that topic's; this topic begins where a
collection is consulted by a workflow other than the one that ships it.

## Provenance and lifecycle

Foundation reference for the portable agent-skill-engineering pack. Maintain as
governed OKF source; generated router copies are not authoring surfaces.

**Applicability limit:** This guidance is an observed practice from the 137
authored agent skills in the catalogue that developed this pack, censused on
2026-08-28. It is not established beyond that population.
