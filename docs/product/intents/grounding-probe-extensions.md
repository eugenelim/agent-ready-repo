# Grounding probe extensions: authority closure and document contracts

- **Status:** Draft
- **Kind:** outcome
- **Level:** feature
- **Scale:** app
- **Maturity:** brownfield
- **Parent intent:** work-loop-delivery-efficiency — [Work-loop delivery efficiency](work-loop-delivery-efficiency.md)

## Outcome

- **Steerable input:** Add the two probes ranked in
  [the grounding-probes survey](../research/repository-grounding-probes-survey.md)
  that were not cheap enough to ship with the first set — authority and
  projection closure, and the executable document-contract check.
- **Lagging outcome:** An author learns that a file they are about to change has
  generated mirrors, a manifest, and a release surface around it, and that a
  document they are about to write is parsed by something with an opinion about
  its headings — before the build discovers either.
- **Guardrail:** Both report; neither decides. No exit status but success absent
  an operational error, and no gate consumes either. Every threshold derives from
  the adopter's own distribution with its basis reported, as the shipped probes
  already do.

## Opportunity

This repository's own recorded defect history ranks these second and third by
defects-they-would-have-caught over implementation cost, behind the live-reference
probe that shipped.

**Authority and projection closure — eight recorded defects.** A plan sees the
intended edit but not the closure around it: source to projection, manifest to
release, register to tree, contract to consumer. Two plan amendments in one
delivery came from checking authored sources while the shipped guards read the
compiled projection. A pack version change spans three or four files depending on
the route, and the self-host run syncs none of the version surfaces.

**Executable document-contract check — four recorded defects.** Machine-consumed
documents are parser interfaces, and authoring checks treat them as free prose.
One task-heading pattern was discovered only after the plan had been hash-pinned.

## Boundary

- Includes both probes, their calibration, and their fixtures.
- Excludes re-deriving the explorer. `new-spec` owns it, its staging, and its
  calibration posture; this extends it and restates none of it.
- Excludes any blocking behaviour, any new configuration file — ADR-0037 D2 —
  and any repository-wide index, graph or parse. Both stay seed-bounded.
- **Excludes executing arbitrary repository code.** The document-contract probe
  runs a consumer's parse-only mode where one exists; discovering and invoking an
  entry point is a security surface the shipped probes do not have, and that
  boundary is decided before it is built, not during.

## Owner

- eugenelim, Platform Core maintainer.

## Unresolved questions

- Is a role in the closure graph assertable from two mechanical signals — a
  generator edge plus a matching relative path, or a manifest declaration plus
  content parity — or does it need judgment? The survey proposes two signals; it
  is untested.
- Can a document contract be checked without executing anything, by reading the
  consumer's heading patterns only? That would remove the security surface at the
  cost of missing a parser whose rules are not literal.
- Does the closure probe overlap `lint-generated-path-ownership.py`, which
  already exists? Settle before building; an existing owner is a reason to cite
  rather than duplicate.

## Source

- Mode: repo-origin
- Locator: docs/product/research/repository-grounding-probes-survey.md
- Authority: repo-origin
