# RFC-0058: Capability-tiered document extraction

- **Status:** Accepted <!-- Draft | Open | Final Comment Period | Accepted | Rejected | Withdrawn | Experimental -->
- **Author:** eugenelim
- **Approver:** eugenelim
- **Date opened:** 2026-06-30
- **Date closed:** 2026-06-30
- **Decision weight:** standard
- **Related:** RFC-0007 (the converters pack this changes); [RFC-0047 adopter-and-org-supplied-grounding](0047-adopter-and-org-supplied-grounding.md) + ADR-0037 (the presence-checked "detect-and-degrade" grounding doctrine this applies — *grounding* = the platform/framework/verification context an agent is given; that doctrine has the tool detect what context is actually supplied and degrade gracefully when a layer is absent); ADR-0034 (the no-bundled-per-vendor-knowledge-base rule this respects); `docs/specs/converters-pack/`, `docs/specs/converters-extraction-fixes/` (PR #471, the bug-fix slice that preceded this); notes: [`0058-notes/`](0058-notes/)

## Reviewer brief

- **Decision:** Should `file-to-markdown` (the `converters` pack's document/image → Markdown skill) become a **capability-tiered** pipeline — one that detects which extraction capabilities are actually available in the environment and degrades gracefully — instead of hard-depending on Docling (IBM's ML-based document-conversion toolkit it uses today)?
- **Recommended outcome:** accept (seven sub-decisions, all with a recommended option).
- **Change if accepted:**
  - A **no-ML floor** that works with ordinary parser libraries (or none), so the skill isn't dead where AI/ML libraries are banned.
  - A **unified output contract** (provenance + quality metadata) across both the document and image branches.
  - A **general image/PDF-page → text/table mode** plus opt-in higher-fidelity tiers (Docling enrichment, vision-model reads, managed OCR APIs).
- **Affected surface:** the `converters` pack's `file-to-markdown` skill (SKILL.md + `scripts/`), its declared dependencies, and its output format. No change to the CLI, the adapter contract, or other packs.
- **Stakes:** costly-to-reverse (adds dependencies — "forever"; changes a shipped skill's output shape) but not a one-way door; delivered incrementally via specs.
- **Review focus:** (1) the tiering model in D1 and whether "agent-vision" genuinely sidesteps the ML ban; (2) D5's managed-API tier, which crosses a **data-egress boundary**.
- **Not in scope:** a new pack; bundling ML models or per-vendor data (ADR-0034 holds); picking a managed-OCR vendor; chart→data extraction; the CLI/adapter contract.

## The ask

**Recommendation (Bottom Line Up Front):** Re-architect `file-to-markdown` as a **capability-tiered** extractor — a no-ML floor, an agent-vision tier, an approved-ML tier (today's Docling), and an opt-in managed-API tier — under a single **unified output contract** (every extraction carries provenance + a quality/confidence signal), and add a general image→text/table mode. Approve the seven decisions below; implementation lands as a sequence of specs, floor-first.

**Why now (Situation–Complication–Question, an SCQA framing).**
- *Situation:* the converters pack ships `file-to-markdown`, whose document branch is a thin wrapper over **Docling** (IBM's open-source document-conversion toolkit — layout model + table model + OCR (Optical Character Recognition) + optional vision models) and whose image branch is a diagram-only extractor.
- *Complication:* Docling **downloads machine-learning models on first run**, and some corporate environments **ban optional OCR/ML libraries outright** (every AI/ML model must clear an approval process). RFC-0007 foresaw this and judged it acceptable *at the time* because conversion is an opt-in capability per skill — its mitigation was *"adopters in pip/npm-hostile environments simply don't invoke the affected converter"* (RFC-0007 §Drawbacks). That leaves the skill **with no path at all** for PDFs/Office where ML is banned. Separately, pressure-testing the shipped code (see notes) found the document branch emits **no provenance or quality metadata**, and the image branch serves only diagrams — not the common "read this screenshot/scan/table image" case.
- *Question:* how should the skill produce trustworthy Markdown for AI **context layers** (the retrieval stores and injected reference material an agent is fed) **across the full range of environments**, from fully-locked-down to cloud-permitted?

**Decisions requested.**

| ID | Question | Recommendation | Why | Decide by | Reviewer action |
| --- | --- | --- | --- | --- | --- |
| D1 | Survive the banned-ML constraint how? | Capability-tiered w/ graceful degradation | Serves both locked-down and cloud-permitted orgs; applies ADR-0037's presence-check doctrine | this review | Confirm the tier model |
| D2 | What is the Tier-0 (no-ML) floor built on? | `pypdf` (new dep) for digital-PDF text + new Office→text code (`python-docx`/`openpyxl`, degrading to stdlib) | Ordinary libraries clear a far lower approval bar than ML models | this review | Confirm dep posture + that Tier-0 Office is new code |
| D3 | A unified output contract across both branches? | Yes — shared, versioned provenance + quality frontmatter | Consumers get consistent, auditable provenance | this review | Confirm the contract fields + version field |
| D4 | Add a general image/PDF-page → text/table mode? | Yes — routed by the existing overview classification | Serves the common case the diagram-only branch misses | this review | Confirm |
| D5 | Expose vision-model / enrichment / managed-API how? | Opt-in, off by default; Tier-3 egress explicit + never auto-reached | Fidelity without silent egress, hallucination, or model downloads | this review | Rule on the egress-boundary controls |
| D6 | Structure-preserving output + chunking? | Yes — optional, tier-dependent (Docling `HybridChunker` at the ML tier; section-aware Markdown below) | Directly serves "feed context layers"; extraction quality dominates chunking | this review | Confirm opt-in |
| D7 | Widen format coverage (HTML/EPUB/CSV/ODT/`.eml`)? | Yes — as Tier-0 cheap wins | Mostly stdlib/ordinary-lib or Docling-native; high value, low cost | this review | Confirm inclusion |

## Problem & goals

**Diagnosis.** `file-to-markdown` has three distinct problems, all confirmed against the shipped code (notes: [`pressure-test.md`](0058-notes/pressure-test.md)):

1. **It fails closed where ML is banned.** The document branch requires Docling; Docling requires downloaded ML models. Where those are prohibited (or egress to fetch them is blocked), the skill has *no fallback path at all* for PDFs or Office files.
2. **Its output is not context-layer-ready.** The document branch emits bare Markdown with **no frontmatter** — no source, page, confidence, or `requires-review` signal — so a scanned PDF that OCRs to garbage passes silently. (The image branch already emits rich frontmatter; the two branches disagree.)
3. **The image branch is diagram-only.** A screenshot of prose, a table image, a receipt, or a photo of a page is forced into a "diagram element" model, which is lossy for the most common image-ingestion needs.

**Goals.**
- Produce trustworthy Markdown for AI context layers across **all** environments, degrading gracefully rather than failing closed.
- Make **provenance and a quality/confidence signal** first-class on every extraction.
- Be **honest about approval posture**: the skill declares, per tier, what needs organizational sign-off.
- Preserve today's fidelity where the environment permits it (Docling stays — as a tier, not the base).

**Non-goals** (could-have-been-goals, deliberately dropped):
- **Bundling ML models or a per-vendor knowledge base** — ADR-0034's "ship awareness and doctrine, never bundled per-vendor data" rule holds; the higher tiers are *adopter-provisioned*, not shipped.
- **Choosing a managed-OCR vendor** (Mistral OCR, Azure Document Intelligence, AWS Textract, AWS Bedrock Data Automation — cloud document-extraction services) — the RFC defines the *tier interface*; the vendor is adopter config.
- **Chart/graph → structured-data extraction** — no reliable general solution exists in the current generation (notes: survey finding C7).
- **A new pack or CLI/adapter-contract change** — this stays inside `converters`.

## Proposal

Re-architect `file-to-markdown` around **capability tiers**. The skill detects which tiers are available, uses the best available for the input (with the Tier-3 exception in D5), and records which tier ran. "Agent-vision" below means *the already-running in-session model (e.g. Claude) reading a rendered image* — not an installed OCR model; this distinction is the load-bearing one for locked-down environments (and see D5 for its egress nuance).

| Tier | Mechanism | Needs | Handles | Approval bar |
| --- | --- | --- | --- | --- |
| **0 — no ML** | Pure parsers | `pypdf` (digital-PDF text — **new dep**); new Office→text code atop `python-docx`/`openpyxl`/`python-pptx`, degrading to stdlib `zipfile`+XML for OOXML (Office Open XML, the zip format of `.docx`/`.xlsx`/`.pptx`) | digital PDFs, Office files, and the D7 formats | ordinary library (or stdlib) |
| **1 — agent-vision** | Rasterize pages/images → the in-session model reads → deterministic reconcile | a **non-ML rasterizer** (`pymupdf` or `pdf2image` — **new, load-bearing dep**; note their native backends, MuPDF/AGPL and Poppler) + the in-session model | scanned PDFs, images, tables-as-image, the D4 general mode | no new *model*, but a new rasterizer dep + a data-handling event (see D5) |
| **2 — approved ML** | Docling (today's branch) | Docling + its downloaded models | best-fidelity full pipeline, enrichment (D5), chunking (D6) | ML-model approval required |
| **3 — managed API** | Outsourced OCR | egress + an approved vendor | high-volume / specialized OCR | cloud egress + vendor approval |

**D1 — tiering & graceful degradation.** The skill picks the highest available tier for the input class and degrades down when a tier is unavailable, surfacing which tier ran. This mirrors ADR-0037/RFC-0047's presence-checked "every layer free to be absent; degrade to today's behavior" doctrine, applied to extraction capability instead of grounding context. **Exception:** Tier 3 (managed API) is never reached by automatic degradation *or upgrade* — even when configured, it requires explicit selection (see D5).

**D2 — Tier-0 floor (honest cost).** Digital (text-layer) PDFs go through `pypdf`, a **new** ordinary dependency. Office extraction is **net-new code**: `file-to-markdown` imports only Docling today, so reading `.docx`/`.xlsx`/`.pptx` → text is new work — it can use `python-docx`/`openpyxl`/`python-pptx` (which are already in the pack's *adopter footprint* because the sibling **rendering** skills `markdown-to-docx`/`-xlsx`/`-pptx` ask adopters to `pip install` them on demand — but they are *not* current `file-to-markdown` deps and the extraction direction is a different API surface), degrading to pure-stdlib `zipfile`+XML if even those libraries are unapproved. When Tier 0 can't serve an input (a scanned/image-only PDF has no text layer, or `pypdf` returns only sparse/low-confidence text), the skill escalates to Tier 1 rather than emitting silent low-quality output (see the misclassification drawback).

**D3 — unified output contract.** Both branches emit shared YAML frontmatter: `contract-version` (so consumers can detect the shape), `source-file`, `content-type`, `tier` (which tier produced this), `ingestion-date`, `extraction-confidence`, `requires-review`, and provenance (page/section/bbox — *bbox* = bounding-box coordinates) where the tier provides it. This generalizes the image branch's existing frontmatter (present since the RFC-0007 import in #63; the branch's reconcile step was refined in #471) to the document branch.

**D4 — general image/PDF-page mode.** The image branch's existing overview-classification step routes: a diagram → the current strategy extractors; anything else (prose, table, form, receipt) → a new general **text/table** read that emits Markdown text/tables rather than typed diagram elements. Reuses the tiling + reconcile machinery.

**D5 — higher-fidelity, opt-in, egress-controlled** (the security boundary). Docling enrichment (formulas → LaTeX math markup, figure captioning, code) and the managed-API tier are **off by default**. Concretely:

- **Tier 1 is "no *new* egress," not "no egress."** Feeding a rendered page to the in-session model still sends document content to whatever endpoint serves that model: an air-gapped/local model ⇒ truly no egress; a cloud-hosted model ⇒ egress to the *already-approved* vendor. The doctrine must state this so an adopter never routes classified scans through a hosted model believing the RFC blessed it as egress-free.
- **Tier 3 egress declaration has a defined shape.** Enabling Tier 3 requires config that names (a) the specific vendor **endpoint/host as an allowlist** and (b) the **data-residency/region**; the implementing spec asserts egress occurs only to the named destination.
- **Tier 3 is never auto-reached.** Automatic degradation/upgrade (D1) must **exclude** Tier 3 — it requires explicit per-input (or explicit-scope) selection, so the degradation engine can never fail *open* into egress.
- **Redaction is out of scope; documents are sent unmodified.** Tier 3 ships documents wholesale — the RFC decides *not* to build pre-egress PII/secret redaction; adopters gate at their document-classification layer. (An optional pre-egress redaction hook is left as an open question.)
- **Vendor retention/no-train posture is a recorded control.** The shipped Tier-3 doctrine must make the adopter verify and record the vendor's data-retention and no-training-on-input terms as part of "vendor approval" (they differ materially across the named vendors); the spec asserts this appears in the tier's grounding doc.
- **Extracted text is untrusted data.** The Tier-1 read prompt must treat rasterized/extracted document text as data, never instructions (prompt-injection defense), since a document reading "ignore prior instructions…" would otherwise steer the agent whose context layer this feeds.

Tier 1 agent-vision (subject to the egress nuance above) needs no new *model* approval, distinguishing it from Tier 3. A `security-reviewer` pass gates the D5 spec and diff.

**D6 — structure + chunking.** Where Tier 2 runs, the skill can emit Docling's structured document and `HybridChunker` output (tokenizer-aware, structure-preserving chunks) instead of only flat Markdown; lower tiers emit section-aware Markdown. Opt-in, so the default stays a single Markdown file.

**D7 — format coverage.** Add HTML, EPUB, CSV/TSV, ODT/ODS/ODP (OpenDocument), and `.eml` (email) at Tier 0 — mostly stdlib, ordinary-lib, or Docling-native — as cheap wins alongside the floor.

**Migration path.** `file-to-markdown`'s current invocation stays valid; Tier 2 (Docling) is what runs today, so environments that already work are unchanged. New behavior (the floor, the contract, the general mode) is additive. Delivered as a sequence of specs, floor-first.

## Options considered

**Axis: how much the skill adapts to the extraction capability actually available in the environment.** The axis runs from "not at all" (ignore capability) through "one fixed choice" to "full runtime detection."

| Option | What it is | Trade-off | Verdict |
| --- | --- | --- | --- |
| **Do nothing** | Keep bare Docling | Zero new maintenance, dep surface stays at Docling. But the skill stays with no path where ML is banned. **This option is a decision to keep RFC-0007's judgment that the gap is acceptable** — this RFC argues that judgment should be reversed now that the locked-down segment is a priority | Rejected — the driving problem is unaddressed |
| **Single no-ML rewrite** | Drop Docling; pure parsers + agent-vision only | Portable everywhere; but discards a working high-fidelity tool for orgs that *can* run it, and caps fidelity for everyone | Rejected — throws away fidelity the environment may permit |
| **Two fixed modes, adopter-selected (no auto-detection)** | Ship a no-ML floor *and* keep Docling; the adopter picks by config; no runtime capability-detection/degradation machinery | Adapts to capability without D1's detection complexity (the real cost driver); but pushes the "which tier" decision onto every adopter, and can't degrade automatically when a configured tier turns out unavailable at runtime | Viable; rejected in favor of detection because the target users (locked-down orgs) often *don't know* their own tier boundaries, and auto-degradation is the feature that makes "just run it" work — but the machinery cost is real and is the main thing to weigh |
| **Capability-tiered (recommended)** | Detect + degrade across 4 tiers | Best fidelity per environment; honest approval posture; cost is the tiering machinery + new deps (`pypdf`, a rasterizer) | **Recommended** — the only option that serves both locked-down and cloud-permitted orgs without per-adopter configuration |

Prior art for the shape: this is the same **detect-and-recommend, presence-checked, free-to-be-absent** pattern ADR-0037/RFC-0047 chose for grounding context, and the "route by input class" consensus across the document-extraction field (notes: survey finding F1).

## Risks & what would make this wrong

**Pre-mortem.**
- *Tier-0 misclassification fails silently.* A scanned PDF with a thin/garbage text layer returns *some* text from `pypdf`, passes Tier 0, and never escalates — emitting low-quality output that looks fine. → Tier 0 must self-assess (sparse/low-confidence text) and escalate to Tier 1; the unified contract's `extraction-confidence` + `requires-review` surface it.
- *Tiering makes the skill hard to use or maintain.* → Detection is automatic; the default path stays one command; tiers are progressive-disclosure in SKILL.md.
- *An org's policy rejects agent-vision (Tier 1) too.* → Tier 0 still works for digital docs; the skill degrades and says so, never fails closed silently.
- *General-image mode (Tier 1) hallucinates, or is steered by document content.* → Confidence + `requires-review` in the contract; cross-check against a text layer when one exists; treat extracted text as untrusted data in the read prompt (D5).
- *Managed-API (Tier 3) leaks sensitive documents.* → Off by default; explicit opt-in naming the egress destination + residency; never auto-reached; vendor retention/no-train recorded (D5); `security-reviewer` at spec and diff.

**Key assumptions (falsifiable).**
- *Agent-vision's non-model pieces run without ML approval.* **Split:** the *tiling + reconcile* machinery is proven in-tree (the shipped image branch runs on Pillow, the Python imaging library, with no installed OCR). The *PDF-page rasterizer* (`pymupdf`/`pdf2image`) is **new and unproven** here — and whether it clears approval, and whether feeding page images to a hosted model counts as gated egress, is **org-specific** (see Open questions / D5). Don't read the Pillow result as proof of the rasterizer/egress claim.
- *Ordinary parser libraries clear approval where ML models don't.* Asserted from the constraint's own logic (an AI/ML-model approval process doesn't gate `pypdf`); adopter-verifiable.
- *Markdown + provenance is the right context-layer format.* Supported by the field (notes: survey finding F6).

**Drawbacks.** Adds dependencies (`pypdf` **and** a rasterizer) — "forever" per the repo's dependency rule; adds maintenance surface (the tiering machinery + a second image mode + new Office-extraction code); changes a shipped skill's output shape (mitigated by an additive, `contract-version`-stamped frontmatter — but the image branch already ships a *specific* field set, so any consumer parsing today's frontmatter is a caller to consider); and the Tier-3 managed-API path is a standing **data-egress** drawback, not merely a mitigated risk.

## Evidence & prior art

**Spike / de-risk (split, per the assumption above).**
- *Proven in-tree:* the image branch's tiling + reconcile runs on Pillow alone — no installed OCR model — so the "agent reads tiles, script reconciles" mechanism works without an ML dependency.
- *Unproven / org-specific:* the new PDF-page **rasterizer** (`pymupdf` = MuPDF/AGPL; `pdf2image` = Poppler) is the load-bearing new piece and is exactly the "ordinary software vs. approved component" gray zone; and whether page-image-to-hosted-model is gated egress is a policy question no spike settles. These are flagged, not claimed.
- *Also confirmed:* pure stdlib cannot extract PDF *text* (PDF is a page-description format), so Tier 0 must include a PDF parser (`pypdf`) or escalate to Tier 1 — reflected in D2.

**Repo precedent.**
- **RFC-0007 §Drawbacks** — explicitly predicted the locked-down-Docling hazard and judged it acceptable *because conversion is opt-in per skill*; this RFC reverses that judgment for the locked-down segment. On acceptance, RFC-0007 gets an erratum recording that its drawback is now addressed.
- **[RFC-0047 adopter-and-org-supplied-grounding](0047-adopter-and-org-supplied-grounding.md) / ADR-0037** — the presence-checked, detect-and-degrade, "every layer free to be absent" doctrine that D1 applies to extraction capability. (Note: two RFCs share the number 0047; the intended one is the grounding RFC linked here.)
- **ADR-0034** — "ship awareness and doctrine, never bundled per-vendor data"; the higher tiers are adopter-provisioned, keeping this rule intact.
- **`converters` pack** — `python-docx`/`python-pptx`/`openpyxl` are used by the sibling **rendering** skills (`markdown-to-*`) via pip-on-demand, *not* by `file-to-markdown`; Tier-0 Office extraction is new code (see D2).
- **PR #471 / `converters-extraction-fixes`** — the bug-fix slice (reconciler data-loss + honesty fixes); the frontmatter emitter it refined (originally from #63) is the seed D3 generalizes.

**External prior art.** Summarized here; full survey with confidence tags and citations in [`0058-notes/doc-extraction-survey.md`](0058-notes/doc-extraction-survey.md) (its F#/C# codes are finding IDs in that survey): no single winner → route by input (F1); the ML dependency *is* the constraint in locked-down orgs, and agent-vision reuses the already-approved model (F9a); Markdown is empirically the best LLM context format (F6); extraction quality dominates chunking strategy (F7); managed OCR spans a 15–30× price band with vendor-run benchmarks to distrust (F4); vision-LLMs win on degraded scans but hallucinate (F5).

**Promoted research.** The sustained investigation behind this RFC — an applied-mode research survey and a pressure-test of the shipped code — lives in [`0058-notes/`](0058-notes/); its conclusions are summarized above rather than pasted into the body.

## Open questions

1. **Chunking output format (D6) — Docling-native or a neutral chunk schema?** Recommended default: emit Docling's `HybridChunker` output as-is at Tier 2, section-aware Markdown below; introduce a neutral schema only if a consumer needs one. · owner: eugenelim · decide-by: the D6 spec.
2. **Does `msg-to-markdown` adopt the unified contract now?** Recommended default: apply the D3 frontmatter contract to `msg-to-markdown`; defer `.eml`/MIME to the D7 work. · owner: eugenelim · decide-by: the D3 spec.
3. **Optional pre-egress redaction hook for Tier 3?** D5 decides redaction is out of scope (documents sent unmodified); the residual is whether to offer an *optional* pre-egress redaction/classification hook adopters can wire in. Recommended default: don't build it in this RFC's specs; revisit if an adopter needs it. · owner: eugenelim · decide-by: the D5 spec.

## Follow-on artifacts

Filled in on acceptance:
- **ADR** — [ADR-0045](../adr/0045-capability-tiered-document-extraction.md) records the capability-tiering doctrine for extraction (peer to ADR-0037 for grounding). ✅ authored on acceptance.
- **Spec:** [`docs/specs/extraction-tier0-and-output-contract/`](../specs/extraction-tier0-and-output-contract/spec.md) — the no-ML floor (D2), unified contract (D3), and D7 formats. ✅ authored (floor-first); plan approved, implementation is the next slice.
- **Spec:** `docs/specs/extraction-general-image-mode/` — the general text/table mode (D4), Tier-1 PDF-page rasterization. *(Not yet authored — sequenced after the floor ships; depends on the unified contract this floor spec lands.)*
- **Spec:** `docs/specs/extraction-higher-tiers/` — opt-in enrichment/vision/managed-API (D5) and structure+chunking (D6), with a `security-reviewer` pass on the egress tier. *(Not yet authored — sequenced last; depends on both preceding specs.)*
- **Spec (Open-Q2 resolution):** `extraction-msg-to-markdown-python-contract` — Open Q2 ("does `msg-to-markdown` adopt the unified contract now?") is resolved by the floor spec's review: **defer**, because `msg-to-markdown` is a Node.js skill that cannot share the floor's Python contract builder. Adoption happens via a **Node→Python port** (not a JS re-implementation that would fork the contract) as its own slice. Tracked in [`docs/backlog.md`](../backlog.md#extraction-tier0-and-output-contract). *(Not yet authored.)*
- **Erratum** on RFC-0007 recording that its locked-down-dependency drawback is addressed here. ✅ appended to [RFC-0007 § Errata](0007-user-scope-converter-pack.md#errata).
