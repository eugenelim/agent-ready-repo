# ADR-0045: Document extraction is capability-tiered and presence-checked — a no-ML floor degrades up through agent-vision, approved-ML, and an explicit-only managed-API tier

- **Status:** Accepted
- **Date:** 2026-06-30
- **Decision-makers:** eugenelim
- **Related:** [RFC-0058](../rfc/0058-capability-tiered-document-extraction.md) (the accepted decision this records, incl. its seven-decision set, options table, and pre-mortem); [ADR-0037](0037-grounding-is-adopter-and-org-supplied-and-presence-checked-one-gate-from-infra-to-framework.md) (the presence-checked "detect-and-degrade, every layer free to be absent" grounding doctrine this mirrors for extraction *capability*); [ADR-0034](0034-infra-grounding-toolchain-oracle-doctrine-not-tooling-vendor-data-or-agent.md) (the "ship awareness and doctrine, never bundled per-vendor data" rule this extends, not breaks); [RFC-0007 § Errata](../rfc/0007-user-scope-converter-pack.md#errata) (the locked-down-dependency drawback this reverses for `file-to-markdown`)

## Decision summary

- **Decision:** We will re-architect `file-to-markdown` as a **capability-tiered** extractor — a no-ML Tier-0 floor, an agent-vision Tier 1, an approved-ML Tier 2 (today's Docling), and an explicit-only managed-API Tier 3 — that detects which tiers the environment permits, uses the best available for the input class, and records which tier ran, all under one versioned unified output contract carrying provenance and a quality signal.
- **Because:** it is the only shape that serves both locked-down (ML-banned) and cloud-permitted orgs without per-adopter configuration, while staying honest about each tier's approval posture.
- **Applies to:** the `converters` pack's `file-to-markdown` skill (and the shared output contract `msg-to-markdown` adopts); not the CLI, the adapter contract, or other packs.
- **Tradeoff accepted:** new dependencies ("forever" — `pypdf` and, at Tier 1, a rasterizer), added maintenance surface (the tiering machinery + a second image mode + new Office-extraction code), and a changed output shape (mitigated by an additive, `contract-version`-stamped frontmatter).
- **Revisit if:** a single extraction engine covers the full environment range (ML-banned through cloud) at acceptable fidelity, collapsing the need for tiers; or the locked-down segment stops being a priority.

## Context

The `converters` pack ships `file-to-markdown`, whose document branch is a thin
wrapper over **Docling** (IBM's ML-based document-conversion toolkit: layout
model + table model + OCR + optional vision models) and whose image branch is a
diagram-only extractor. Docling **downloads ML models on first run**, and some
corporate environments **ban optional OCR/ML libraries outright** — every AI/ML
model must clear an approval process, and egress to fetch models may be blocked.

RFC-0007 foresaw this hazard and judged it acceptable *at the time*, on the
reasoning that conversion is opt-in per skill: its mitigation was that adopters
in pip-hostile environments "simply don't invoke the affected converter." That
leaves `file-to-markdown` with **no path at all** for PDFs or Office files where
ML is banned. The locked-down segment is now a priority, so that judgment is
reversed (RFC-0007 § Errata). Pressure-testing the shipped code additionally
found the document branch emits no provenance or quality metadata (a scanned PDF
that OCRs to garbage passes silently), and the image branch serves only diagrams,
not the common "read this screenshot/scan/table image" case.

The repo already chose a **presence-checked, detect-and-degrade** doctrine for
*grounding context* in ADR-0037/RFC-0047 ("every layer is free to be absent;
degrade to today's behavior"). Extraction *capability* is the same shape at a
different layer.

## Decision

We will make `file-to-markdown` **capability-tiered**. The skill detects which
tiers are available, uses the highest available tier for the input class, and
records which tier ran in the output. The four tiers:

| Tier | Mechanism | Approval bar |
| --- | --- | --- |
| **0 — no ML** | Pure parsers: `pypdf` for digital-PDF text; ordinary Office parsers (`python-docx`/`openpyxl`/`python-pptx`) degrading to stdlib `zipfile`+XML; plus the D7 formats | ordinary library (or stdlib) |
| **1 — agent-vision** | Rasterize pages/images → the **already-running in-session model** reads → deterministic reconcile | a new rasterizer dep, but no new *model* (a data-handling event — see the egress carve below) |
| **2 — approved ML** | Docling (today's branch) + its downloaded models | ML-model approval |
| **3 — managed API** | Outsourced OCR to an adopter-provisioned vendor | cloud egress + vendor approval |

Load-bearing boundaries of the decision:

- **Detect and degrade, never fail closed silently.** The skill degrades to a
  lower tier when a higher one is unavailable and surfaces which tier ran. This
  mirrors ADR-0037's presence-check doctrine applied to extraction capability.
- **"Agent-vision" means the in-session model reading a rendered image** — not
  an installed OCR model. This is the load-bearing distinction for locked-down
  environments: it reuses the already-approved model rather than adding one.
- **Tier 3 is never auto-reached.** Automatic degradation *or upgrade* excludes
  Tier 3; it requires explicit per-input (or explicit-scope) selection, so the
  degradation engine can never fail *open* into egress. Tier 1 is "no *new*
  egress," not "no egress" — a cloud-hosted in-session model still sends content
  to its (already-approved) endpoint.
- **A unified, versioned output contract** carries provenance + a quality/
  confidence signal (`contract-version`, `tier`, `extraction-confidence`,
  `requires-review`, …) on **every** extraction, across both the document and
  image branches, so consumers get consistent, auditable provenance.
- **Higher tiers are adopter-provisioned, never bundled.** No ML models, no
  managed-OCR vendor, and no per-vendor knowledge base ship with the pack —
  ADR-0034 holds. The pack ships the tier *interface* and the doctrine; the
  adopter supplies the model, the enrichment, or the vendor.

## Decision drivers

- **Serve the full environment range** — fully-locked-down through
  cloud-permitted — from one skill, without per-adopter configuration.
- **Honesty about approval posture** — the skill declares, per tier, what needs
  organizational sign-off.
- **No silent egress and no silent low-quality output** — egress is explicit and
  never auto-reached; low-confidence extractions carry `requires-review`.
- **Preserve today's fidelity where permitted** — Docling stays, as a tier.
- **Respect ADR-0034** — awareness and doctrine ship; per-vendor data does not.

## Consequences

**Positive:**

- `file-to-markdown` has a working path in ML-banned environments (Tier 0) for
  the first time, instead of failing closed.
- Provenance + quality metadata become first-class on every extraction, so
  garbage-OCR and low-confidence reads surface instead of passing silently.
- The general image/PDF-page → text/table case (screenshots, scans, table
  images) is served, not just diagrams.
- The approval posture is legible: an adopter knows exactly which tier needs
  sign-off and why.

**Negative:**

- New dependencies, "forever" per the repo's dependency rule: `pypdf` at Tier 0
  and a rasterizer at Tier 1.
- Added maintenance surface: the tiering/detection machinery, a second image
  mode, and new Office-extraction code.
- A changed output shape for the document branch (additive frontmatter) — any
  consumer parsing today's image-branch frontmatter is a caller to consider,
  mitigated by the `contract-version` stamp.
- The managed-API tier is a standing **data-egress** surface, gated by explicit
  opt-in and a `security-reviewer` pass at its spec and diff.

**Revisit if:** a single extraction engine covers the full environment range
(ML-banned through cloud) at acceptable fidelity, collapsing the need for tiers;
or the locked-down segment stops being a priority.

## Confirmation

- **Mode:** reviewer-checked
- **Signal:** the implementing specs (floor-first:
  `extraction-tier0-and-output-contract`, then `extraction-general-image-mode`,
  then `extraction-higher-tiers`) each specify their tier's behavior and approval
  posture as acceptance criteria; the egress tier carries a `security-reviewer`
  pass at spec and diff. The unified contract's `tier` field records, at runtime,
  which tier actually ran.
- **Owner:** eugenelim

## Alternatives considered

- **Do nothing (keep bare Docling).** Zero new maintenance; but keeps
  `file-to-markdown` with no path where ML is banned — this is a decision to keep
  RFC-0007's now-reversed judgment. Rejected: the driving problem is unaddressed.
- **Single no-ML rewrite (drop Docling; pure parsers + agent-vision only).**
  Portable everywhere; but discards a working high-fidelity tool for orgs that
  *can* run it, and caps fidelity for everyone. Rejected against the
  *preserve-fidelity-where-permitted* driver.
- **Two fixed modes, adopter-selected (no auto-detection).** Ship a no-ML floor
  and keep Docling; the adopter picks by config, with no runtime
  detection/degradation. Adapts to capability without the detection machinery
  (the real cost driver), but pushes the "which tier" decision onto every adopter
  and can't degrade when a configured tier turns out unavailable at runtime.
  Rejected against the *serve-the-full-range-without-per-adopter-config* driver —
  the target users (locked-down orgs) often don't know their own tier boundaries,
  and auto-degradation is what makes "just run it" work; the machinery cost is the
  accepted tradeoff.
