# Reference: folding in traditional requirements capture

Depth for [`SKILL.md`](../SKILL.md). Many enterprises still do classic
requirements work — a BRD, a PRD, an SRS/FRD, use cases, a requirements-traceability
matrix (RTM) — and often refine requirements at several levels at different times.
This loop does **not** replace that and adds **no requirements pillar of its own**;
it *maps* those artifacts onto what it already produces, **ingests** them as input,
and can **emit** in their format for sign-off. *(AC38.)*

## The crosswalk

| Traditional artifact | Maps to in this loop |
| --- | --- |
| **BRD** (the *why*; business objectives; success metrics) | a product-vision / strategy **`intent`** + the outcomes/metrics fields |
| **PRD** (product requirements, each traceable to a BRD outcome) | capability / feature **`intent`** slots + the **decision brief** |
| **FRD / FRS** ("the system shall…", functional behaviour) | the **journey + service-blueprint + screen-flow** slots, then the **spec ACs** (post-G3) |
| **SRS** (functional + NFR + use cases, system level) | the convergence outputs + the **architecture lens** + the spec |
| **Non-functional requirements** (perf, security, reliability, compliance) | the **discovery reviewers** (`discovery-threat-reviewer` / `discovery-reliability-reviewer`) + the architecture lens + spec ACs |
| **Use cases** | journey steps / screen flows |
| **Requirements Traceability Matrix (RTM)** | the **traceability slot** — a near-direct mapping; the loop already produces outcome→…→component traceability, which *is* an RTM, with the traceability lint as its completeness check |
| **IEEE 29148 quality attributes** (unambiguous, complete, consistent, testable, traceable) | what the **self-coverage gate + traceability lint + discovery reviewers** already enforce |

## Three integration directions (reuse-first)

- **Requirements as input (ingest).** An existing BRD/PRD/SRS *seeds* the loop
  instead of being authored from scratch: **`receive-brief`** (core) +
  **`frame-intent`** brownfield current-state inputs ingest it at G0/G1.5; the loop
  then **validates and enriches** it — `frame-domain` grounds it, the lenses add
  the journey/architecture a requirements doc usually lacks, `de-risk-intent`
  surfaces the assumptions it states as fact, and the self-coverage gate covers
  completeness / ambiguity / scenario-variation. *Net-new: at most a thin
  `receive-brief` extension* that recognizes the requirements-doc shapes — **not** a
  new skill.
- **Refinement at various levels / different times.** Enterprises that refine
  business → system → functional over time map directly onto the **recursive
  plan-tree**: each level is a node at its altitude, refined when reached and
  **resumable** later — the loop is built for exactly this staggered, multi-level
  refinement, not a single upfront capture.
- **Requirements as output (emit for sign-off).** Where governance *requires* a
  formal BRD/SRS/RTM with sign-off, the loop **projects** its decision brief +
  traceability matrix + spec ACs into that format — a **formatting/projection
  adapter** (the converters / md-to-office path, RFC-0036), **not** a discovery
  skill; the decision-log + the security & integrity controls supply the auditable
  sign-off trail.

## What this is not

Do **not** add a requirements writing / validation / enrichment pillar — the loop
already authors the equivalents, and the self-coverage gate + traceability lint
already validate them against the IEEE-29148-style quality attributes. Fold
traditional requirements in via this **crosswalk** (guidance here),
**`receive-brief` / `frame-intent` ingest** (a thin extension at most), the
**traceability slot as the RTM**, and a **projection adapter** to emit the
enterprise format. This is a reuse-first *integration* recommendation — **not** a
new decision.
