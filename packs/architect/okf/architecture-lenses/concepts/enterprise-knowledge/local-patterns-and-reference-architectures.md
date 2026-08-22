---
title: "Local patterns and reference architectures"
type: "Reference"
status: "Active"
license: "Apache-2.0 OR MIT"
compatibility: "agentbundle-okf/v1"
research_claims:
  - LP-1
  - LP-1b
---
# Local patterns and reference architectures

## Scope and routing signals

Use when approved exemplars, paved roads, reusable components, reference
architectures, or engineering patterns could constrain or accelerate change.

## Decisions and minimum evidence

Supports reuse and conformance decisions. Minimum evidence names pattern owner,
intended context, forces, guarantees, version, adoption evidence, exceptions,
and whether it is guidance or mandate.

## Architectural questions

- Which forces and quality scenarios make the pattern applicable here?
- What platform guarantees does it assume and how are they verified?
- Where have teams adapted or rejected it, and why?

## Mechanisms and trade-offs

Paved roads reduce repeated design and operations work; reference architectures
make decisions visible. They can also become cargo cults or central bottlenecks
when context and feedback are ignored.

## Evidence and counter-evidence

Seek maintained exemplars, templates, conformance tests, adoption data, owner
guidance, and exceptions. Counter-evidence includes copy-only repositories,
stale versions, undocumented divergence, and workload mismatch.

## Failure modes and false positives

Similarity does not prove required conformance. A popular internal example may
be legacy rather than preferred; a reference is not evidence the target uses it.

## Confirmation scenarios

Compare one target path with the pattern's forces, contracts, and exercised
guarantees; record justified divergence separately from accidental drift.

## Related concepts and escalation

Pair with provider/platform operating models and constraints. Escalate ambiguity
to the pattern or platform owner.

## Provenance and lifecycle

Synthesized from well-architected guidance, DORA platform/team practices, and
architecture decision methods. Confidence: moderate; review annually.

Research claim trace: `LP-1`, `LP-1b`; see the living source packet with the same concept path.
