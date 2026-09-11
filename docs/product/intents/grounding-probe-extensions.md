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

## Refuted by measurement, 2026-09-11 — the surface-to-verifier probe as a plan-text check

A third probe was prototyped and **refused**: given a plan task's `Touches:`
surfaces, report those no verifier reaches. It is recorded here because the
refusal is the reusable part, and because the same idea will look cheap again.

**It cannot work from plan text.** A plan states coverage as behavioural
assertions, not as paths or test-file names. `adapter-support-accuracy` T1
touches one guide page and checks that page's cells without ever repeating its
path; `catalogue-pack-defaults` T5 asserts `PackState` field behaviour without
naming the module or a test file. Any path-matching predicate scores both as
uncovered.

Two instrument designs, both hand-adjudicated against a deterministic sample of
the 171 Shipped plans that declare `Touches:`:

| Design | Reported | True | Precision |
| --- | --- | --- | --- |
| any touched path unreached by a verifier path | 37 over 2 specs | 2 | 5% |
| code modules with no conventionally-named test in their verifier | 206 of 381 modules (54%) | 0 of 3 checked | ~0% |

Two earlier whole-corpus runs disagreed with each other — 53% versus 7% of plans
zero-gap, median 0 versus 8 — which was itself the finding: neither was
measuring surface coverage, both were measuring whether verifier prose happens
to repeat a path string. Three successive calibration attempts each hit a
different noise source because the noise is the design, not a threshold.

**The successor hypothesis, which does not read plan text at all.** Ask the
repository instead: for a tracked module, does any test file name it? Measured
over 477 tracked non-test modules against 775 test files, this reports 28 (6%),
and the reports are meaningful rather than noisy — `route_agent_plugin.py`,
`route_claude_plugins.py` and `version_ranges.py` are each reached only through
a caller, so the finding is "no test names this module directly", which is a
real gap worth an author's attention. The rest are one-off spike harnesses under
`notes/` and generated projections, both of which a shipped probe would need to
exclude by rule rather than by list.

This successor is a coverage-shaped probe over code, not an authoring probe over
a contract, so it does not belong to the skill that owns the other probes
without a decision first. Settle that before building.

## Held for a later experiment, 2026-09-11 — the probes traverse paths, never claims

Owner decision: recorded, not built, to stop adding scope mid-delivery.

Every shipped probe is seeded by a path and answers a question of that shape —
what governs it, what names it, what runs it, what moves with it, what it names
that no longer resolves. None answers *what verifies this claim*. Measured on one
review round of this contract, eight of twenty-two findings were exactly that
traversal: a module header declaring an exit status its `main` cannot return, a
header asserting that a suite checks something no suite checks, a criterion
claiming a selection the code performs unconditionally while gating only the
printing.

Two halves of the idea already have owners and need nothing. A criterion's
observer is owned at authoring time — every admitted criterion has exactly one
observing surface — and the disagreement between a claim and its check is owned
at response time, in both directions, including the invisible one where shipped
behaviour no criterion authorises. The gap is exploration only.

**The cheap subset, if this is picked up.** A module's claims about its own
interface, checked against its own code: the exit statuses a header documents
against the values `main` returns, and the flags it documents against the parser.
That comparison is exact rather than heuristic, which is what the surface-to-
verifier probe refused above could never be — that one matched paths against
paths, and the signal was never in paths.

**What to settle first.** A claim-seeded probe needs a claim extractor, and the
claims here are prose. The interface subset avoids that because a header's
exit-code list is structured enough to parse; a criterion's obligation is not.
Deciding where the parseable boundary sits is prior to building anything.

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

- Does the successor probe above belong to `new-spec` at all? It reads code and
  tests, not a contract, so its natural owner may be a coverage surface rather
  than an authoring skill. Deciding that is prior to building it.
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
