# Plan: extraction-higher-tiers

- **Spec:** [`spec.md`](spec.md)
- **Status:** Drafting

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document is allowed to change as you learn. When it changes substantially
> (a different approach, not just a re-ordering), note why in the changelog
> at the bottom.

## Approach

Three opt-in capabilities bolt onto the existing skill without disturbing its
default path. All three are *additive flags* on `convert.py` (plus one new small
module for the Tier-3 interface); with no flag, the skill behaves exactly as it
does after slice 2, and the byte-parity golden tests the predecessors established
prove it. **Enrichment** and **chunking** attach to the single Docling call in
`convert.py:_extract_docling` — enrichment by populating Docling's
`PdfPipelineOptions` with the selected `do_*` flags (and, critically, *never*
setting `enable_remote_services` or constructing a remote-VLM option), chunking by
running Docling's `HybridChunker` over the `DoclingDocument` the pipeline already
produces and writing its chunks as-is to a `<basename>.chunks.jsonl` sidecar (JSON
records, not YAML frontmatter, so the leading-block-only invariant holds). **Tier 3** is the egress-boundary piece and
the riskiest part: it is *not* a network client — the skill stays transport-free.
It is a new `tier3.py` module that validates an egress declaration
(`{endpoint-allowlist, residency-region}`) and, only when the declaration is valid
and Tier 3 was *explicitly* selected, wraps adopter-supplied OCR text in the unified
contract with `tier: "3-managed-api"` and the destination echoed into provenance.
`convert.py:dispatch()` routes by extension to Tiers 0–2 only; `contract.TIER_3` is
constructed in exactly one place (`tier3.assemble_tier3`, reached only via `--tier3`),
so degradation/upgrade can never fail open into egress.
The order of operations: enrichment first (smallest, exercises the pipeline-options
surface), chunking second (same Docling path), the Tier-3 interface + its grounding
doc third/fourth (the security core), then the cross-cutting guards
(no-network-import, never-auto-reach, default-unchanged, byte-stability), then
SKILL.md + release. Testing is TDD for every deterministic piece (gating, local-only
enforcement, declaration validation, contract stamping) with grep/AST guards for the
security invariants and manual QA for the Docling-installed happy paths.

## Constraints

- **RFC-0058** (Accepted 2026-06-30), D5 (opt-in higher fidelity + the egress
  boundary) and D6 (structure + chunking), with Open-Q1 (chunk output as-is) and
  Open-Q3 (redaction out of scope) resolved to their recommended defaults.
- **ADR-0045** — the capability-tiering doctrine; Tier 3 never auto-reached; higher
  tiers adopter-provisioned; unified versioned contract on every extraction.
- **ADR-0034** — ship the tier interface + doctrine, never bundled models or
  per-vendor data.
- **RFC-0007 / § Errata** — the converters pack this changes.
- **Predecessor slices** — `extraction-tier0-and-output-contract` (the `contract.py`
  builder, tier enum, `safe_io.confine`, byte-parity golden tests) and
  `extraction-general-image-mode` (the Tier-1 agent-vision path this leaves
  unchanged and sits above). Reuse, do not fork.
- **Process** — `converters` is a user-scope-default pack: the gate is `lint-packs`
  + `validate` + `build` + `pytest` (regenerating `marketplace.json`), not
  `build-self` / `pre-pr`; version bump 0.4.0 → 0.5.0 drifts `marketplace.json`.
- **Security** — `security-reviewer` gates this spec and the eventual diff.

## Construction tests

Most construction tests live per-task below. Cross-cutting ones:

**Integration tests:**
- **No-network / no-secret / no-leaky-log guard** (AC5) — a grep/AST guard over the
  whole skill asserts no network-client package (`requests`, `httpx`, `urllib`,
  `http.client`, `socket`, a vendor SDK) is imported on any path and no vendor
  endpoint string is bundled; a unit test asserts no auth field is accepted and no
  document body/endpoint is logged at default verbosity. Spans every module.
- **No-remote-services guard** (AC2) — a grep/AST guard asserts `enable_remote_services`
  and `PictureDescriptionApiOptions` (and any remote-VLM option class) appear nowhere
  in the skill, complementing T1's attribute-level truthiness assertion. Spans
  `convert.py` + any enrichment helper.
- **Never-auto-reach-Tier-3** (AC3) — there is no tier-*selection* function; the guard
  is a grep/AST-plus-call-graph assertion that `contract.TIER_3` is constructed only in
  `tier3.assemble_tier3` (reached via `--tier3`), plus a matrix test that every
  automatic path constructs only Tiers 0–2. Spans routing + the Tier-3 module boundary.
- **Default-unchanged regression** (AC11) — a no-flag `convert.py` run over each
  input class reproduces the slice-2 output exactly (byte-parity for the Tier-2
  body; existing golden frontmatter blocks unchanged).

**Manual verification:**
- With Docling installed: enrichment on a real formula/code/figure PDF (LaTeX +
  caption + `tier: "2-approved-ml"`); chunk-mode (HybridChunker chunks). Tier-3
  path against a **mock** adopter transport (no real vendor call in CI): gate +
  stamp + provenance.

## Design (LLD)

Shape: **service**. Stack: Python skill under
`packs/converters/.apm/skills/file-to-markdown/scripts/`, reusing `contract.py`,
`safe_io.py`, and the Docling Tier-2 path in `convert.py` established by the two
predecessor slices. No reference architecture file governs this pack; the stack is
the established one (pure-Python skill scripts, hand-rolled stdlib contract
emitter, pip-on-demand for optional libs).

### Design decisions
- **Tier 3 is transport-free (option B), not a shipped HTTP client (option A).**
  The skill gates + stamps + records; the adopter's SDK/CLI/MCP performs the call.
  Rejected A because a bundled egress client is a fail-open surface and contradicts
  the predecessors' no-network invariant. Traces to: AC4, AC5 · contracts/ n/a.
- **Enrichment is local-model-only by construction** — the code path never sets
  `enable_remote_services`; there is no flag that could. Rejected exposing a
  remote-captioning option because it is covert Tier-2 egress. Traces to: AC2.
- **`TIER_3` constructed in exactly one place** (`tier3.assemble_tier3`, reached only
  via `--tier3`) rather than guarded by a runtime candidate-set check — there is no
  tier-selection function in `convert.py`; `dispatch()` routes by extension to Tiers
  0–2, so a call-graph guard on where `contract.TIER_3` is constructed is the real
  invariant. Traces to: AC3.
- **HybridChunker output emitted as-is; no neutral schema** (RFC Open-Q1). Traces
  to: AC8, AC9.

### Data & schema
- **Tier-3 egress declaration** (adopter-facing config, validated, not persisted):
  `{endpoint-allowlist: [host, …], residency-region: str}`. Endpoint = non-empty
  hostname list; rejects wildcard / scheme-less catch-all (empty, `*`, `.`,
  `0.0.0.0`/`::`) **and** loopback / link-local / private-range / bare-IP metadata
  targets (`127.0.0.0/8`, `::1`, `169.254.0.0/16`, RFC-1918) — SSRF-adjacent
  hardening. Residency = non-empty string; **unknown fields rejected**
  (credential-smuggling guard — no auth material accepted). Echoed into provenance as
  scalars (endpoint **comma-joined**, `content-type` from `--source` suffix or
  `managed-ocr`) through `contract.build_frontmatter`, inheriting the predecessors'
  injection-safe escaping. Not a `contracts/` interface. Traces to: AC4 · AC5 · AC10.
- **Chunk output** — Docling `HybridChunker` chunk records written to a
  `<basename>.chunks.jsonl` sidecar (one JSON object per line = the **full contract
  field set serialized as JSON** — reusing the dict `build_frontmatter` consumes, not
  the YAML emitter — plus chunk text) to a path validated by `safe_io.confine`; JSON,
  not YAML frontmatter, so the leading-block-only invariant holds. No pack-defined
  chunk schema. Traces to: AC8 · AC9.

### Interfaces & contracts
- The consumer contract is the existing YAML frontmatter (`contract.py`), extended
  only by the *values* `tier: "2-approved-ml"` (enriched/chunked) and
  `tier: "3-managed-api"` (assembled), never by renamed/reordered keys. Traces to:
  AC1, AC8, AC10 · contracts/ n/a (Markdown + frontmatter, not an API).

### Failure, edge cases & resilience
- Tier-3 assembly refuses (clear error, no output stamped) on missing/empty
  declaration — fail *closed*, never open. Traces to: AC4.
- Enrichment/chunking on an input Docling cannot handle degrades to the existing
  Tier-2 error path; no silent high-confidence output. Traces to: AC10.
- Chunk-mode below Tier 2 (no `DoclingDocument`) yields section-aware Markdown, not
  an error and not chunk records. Traces to: AC9.

### Quality attributes (NFRs)
- **Security posture** is the load-bearing NFR: no network egress from the skill
  (AC5), no covert Tier-2 egress (AC2), Tier 3 never auto-reached (AC3), egress
  gated by a validated declaration (AC4), vendor retention/no-train recorded (AC7).
  Each has a pass/fail test or guard above. `security-reviewer` at spec + diff.

### Dependencies & integration
- No new pack-declared dependency. Docling enrichment models + the chunker's
  tokenizer are surfaces of the already adopter-provisioned Docling install
  (documented, pip-on-demand). Tier-3 transport is the adopter's mechanism.
  Traces to: AC6.

## Tasks

### T1: Docling enrichment is opt-in, off by default, and local-model-only

**Depends on:** none

**Touches:** packs/converters/.apm/skills/file-to-markdown/scripts/convert.py, packs/converters/.apm/skills/file-to-markdown/scripts/test_convert.py

**Tests:**
- With Docling monkeypatched: no enrichment flag ⇒ pipeline options set none of
  `do_*_enrichment` / `do_picture_*`, body passed through unmodified (byte-parity
  vs. plain Tier-2 body) (AC1).
- Enrichment flag ⇒ the selected `do_formula_enrichment` / `do_code_enrichment` /
  `do_picture_classification` / `do_picture_description` options are set; output
  carries `tier: "2-approved-ml"` (AC1).
- On both paths, the constructed pipeline-options object has **no remote-services
  attribute set truthy** (attribute-level, catches renamed symbols on a Docling bump)
  (AC2).
- Enriched-caption non-forgery: a fixture caption/formula/code containing `ignore all
  previous instructions …` + a `---`/`key:` line lands in the body verbatim, never in
  the frontmatter (AC12).

**Approach:**
- Add an explicit `--enrich` (opt-in) flag to `convert.py`; thread it into
  `_extract_docling`, populating `PdfPipelineOptions` with the selected `do_*`
  flags only when set.
- Never reference `enable_remote_services` or `PictureDescriptionApiOptions`
  anywhere; captioning uses Docling's local picture-description model.
- Keep the enriched body passed through the existing `assemble()` /
  `contract.build_frontmatter(...)` path unchanged — the leading-block-only guarantee
  makes the caption body inert; note in SKILL.md that captions are untrusted model
  output.

**Done when:** the T1 tests (incl. AC2 attribute-level guard and AC12 non-forgery) are
green and the default (no-flag) Tier-2 body is byte-identical to slice 2.

### T2: Opt-in structure-preserving chunk output (HybridChunker as-is at Tier 2, section-aware Markdown below)

**Depends on:** T1

**Touches:** packs/converters/.apm/skills/file-to-markdown/scripts/convert.py, packs/converters/.apm/skills/file-to-markdown/scripts/test_convert.py

**Tests:**
- With Docling monkeypatched: `--chunk` on a Tier-2 run writes a
  `<basename>.chunks.jsonl` sidecar (one JSON record per chunk carrying the full
  contract field set as JSON + chunk text) to a path validated by `safe_io.confine`
  (AC8).
- `--chunk` with the `docling-core[chunking]` tokenizer extra absent errors clearly
  (no crash) (AC8).
- `--chunk` requested below Tier 2 (no `DoclingDocument`) yields section-aware
  (heading-structured) Markdown in the `.md`, not chunk records (AC9).
- A goal-based check asserts no neutral/pack-defined chunk schema was introduced —
  Docling's chunk shape is passed through (AC9).

**Approach:**
- Add an explicit `--chunk` flag; when set on the Tier-2 path, run
  `HybridChunker().chunk(doc)` over the `DoclingDocument` and serialize each chunk
  (contextualized text + Docling's own metadata) as one JSON line carrying the **full
  contract field set** (the dict `build_frontmatter` consumes — `contract-version`,
  `source-file`, `content-type`, `tier`, `ingestion-date`, `ingestion-quality`) as
  JSON, into `<basename>.chunks.jsonl` at a path validated by `safe_io.confine`. Reuse
  the field-set assembly, **not** `build_frontmatter` (which returns YAML) — JSON
  records, so the leading-block-only invariant is never violated.
- Probe the tokenizer extra with a clear error path when `docling-core[chunking]` is
  absent (mirroring the pip-on-demand posture).
- Below Tier 2, produce section-aware Markdown from the existing extracted body
  (heading-structured), not chunk records.
- Default (no `--chunk`) stays a single Markdown file.

**Done when:** the T2 tests are green (sidecar shape, tokenizer-absent error,
below-Tier-2 Markdown) and default output shape is unchanged.

### T3: Tier-3 interface — validated egress declaration, gated assembly, never auto-reached

**Depends on:** T1

**Touches:** packs/converters/.apm/skills/file-to-markdown/scripts/tier3.py, packs/converters/.apm/skills/file-to-markdown/scripts/test_tier3.py, packs/converters/.apm/skills/file-to-markdown/scripts/convert.py

**Tests:**
- Across the full input-class matrix (digital PDF, scan, Office, image, unsupported),
  every automatic path (`dispatch` + Docling fall-through) constructs only
  `TIER_0`/`TIER_1`/`TIER_2` results; a grep/AST-plus-call-graph guard asserts
  `contract.TIER_3` is constructed nowhere except `tier3.assemble_tier3`, reached only
  via `--tier3` (AC3).
- Tier-3 assembly refuses (clear, actionable error, **no output stamped**) on: missing
  declaration; empty/`*`/`.`/`0.0.0.0` endpoint; a loopback / private-range /
  metadata-IP endpoint (SSRF-adjacent); absent residency; an unknown field
  (credential-smuggling guard) (AC4).
- Valid declaration ⇒ output stamped `tier: "3-managed-api"`, `content-type` from the
  `--source` suffix (else `managed-ocr`), `requires-review: true` by default (the skill
  did not verify the OCR), with the endpoint (comma-joined scalar) + region echoed into
  provenance; an injection-bearing endpoint element (`\n---\ninjected: true`) is escaped
  by the contract emitter and cannot break the block (AC4, AC10).
- No network-client package or vendor SDK is imported by `tier3.py`; no vendor
  endpoint string is bundled; no auth field is accepted; no document text/endpoint is
  logged at default verbosity (AC5).

**Approach:**
- New `tier3.py`: `validate_declaration({endpoint-allowlist, residency-region})`
  (non-empty hostname list; reject wildcard / scheme-less catch-all / loopback /
  link-local / private-range / bare-IP metadata targets; non-empty residency; reject
  unknown fields) and `assemble_tier3(ocr_text_path, source, declaration)` that returns
  the unified contract-wrapped Markdown with `tier=contract.TIER_3`, `content-type`
  from the source suffix (else `managed-ocr`), `requires-review: true` by default, and
  the destination in provenance (endpoint comma-joined scalar, escaped by
  `contract.build_frontmatter`) — only after validation passes.
- CLI: `python scripts/convert.py --tier3 --ocr-text <path> --endpoint <host[,host]>
  --residency <region> "<source>"` — the adopter runs the vendor, saves the OCR text,
  and hands the path + declaration to the skill; there is no auto path to `--tier3`.
- Keep `convert.py`'s `dispatch()` constructing only Tiers 0–2; expose Tier 3 only via
  the explicit entry point, never from `dispatch`/degradation/upgrade.
- Import nothing that can open a socket; accept no auth material; log no document
  content or endpoint.

**Done when:** the T3 tests are green; Tier 3 is reachable only through its explicit
gated path and its provenance values are injection-safe.

### T4: Tier-3 grounding doc + doctrine (retention/no-train, redaction out of scope) + deferred-redaction backlog entry

**Depends on:** none

**Touches:** packs/converters/.apm/skills/file-to-markdown/references/tier3-managed-api.md, docs/backlog.md

**Tests:**
- A content check asserts the Tier-3 grounding doc names all three adopter controls:
  (a) verify + record the vendor retention / no-training-on-input terms; (b) configure
  the transport to egress only to the declared endpoint allowlist + residency region;
  (c) redaction is the adopter's document-classification responsibility — documents
  sent unmodified, no pre-egress redaction hook built (AC7).
- The optional pre-egress redaction hook is recorded as a deferred item in
  `docs/backlog.md` under a `## extraction-higher-tiers` section (AC7).

**Approach:**
- Author `references/tier3-managed-api.md`: the tier interface, the egress
  declaration schema (`{endpoint-allowlist, residency-region}`), the never-auto-reach
  posture, the retention/no-train recorded control, the **transport-binding** adopter
  control (carries RFC D5's "egress only to the named destination" under option B),
  and the redaction-out-of-scope doctrine — all vendor-neutral (no vendor named as
  fact; ADR-0034).
- Add to `docs/backlog.md` a `## extraction-higher-tiers` section with a
  `### extraction-tier3-pre-egress-redaction-hook` anchor (matching the existing
  `## <spec-name>` → `### <anchor>` convention) for the RFC Open-Q3 residual.

**Done when:** the content check (all three controls) passes and the backlog
section + anchor exist.

### T5: Cross-cutting security guards + contract stamping + default-unchanged regression

**Depends on:** T1, T2, T3

**Touches:** packs/converters/.apm/skills/file-to-markdown/scripts/test_convert.py, packs/converters/.apm/skills/file-to-markdown/scripts/test_contract.py

**Tests:**
- No-network / no-secret / no-leaky-log guard: no network-client import on any path;
  no bundled endpoint; no auth field accepted; no document body/OCR text and no
  endpoint written to logs at default verbosity (AC5).
- No-remote-services guard: `enable_remote_services` / `PictureDescriptionApiOptions`
  appear nowhere (AC2), complementing T1's attribute-level assertion.
- No-bundled-artifact guard: no ML model, vendor endpoint/SDK, or per-vendor config
  file ships in the pack; enrichment models / chunker tokenizer / vendor are all
  adopter-provisioned (AC6).
- Never-auto-reach-Tier-3: automatic paths construct only Tiers 0–2; `contract.TIER_3`
  constructed only in `tier3.assemble_tier3` (AC3).
- Every higher-tier output (enriched Tier-2, chunked Tier-2 JSONL, Tier-3-assembled)
  carries the unified contract with the correct `tier` and an honest
  confidence/`requires-review`; none auto-stamps `high` (AC10).
- Byte-parity golden test: existing Tier-0/1/2 frontmatter blocks unchanged (AC10).
- Default-unchanged regression: no-flag run reproduces slice-2 output per input
  class (AC11).

**Approach:**
- Add the grep/AST guards (network / secret / remote-services / call-graph) and the
  byte-parity + default-unchanged regression tests.
- Consolidate the contract-stamping assertions across the three higher-tier paths.

**Done when:** all T5 guards + regressions are green.

### T6: SKILL.md progressive disclosure + release hygiene (0.4.0 → 0.5.0)

**Depends on:** T1, T2, T3, T4, T5

**Touches:** packs/converters/.apm/skills/file-to-markdown/SKILL.md, packs/converters/pack.toml, packs/converters/.claude-plugin/plugin.json, .claude-plugin/marketplace.json, docs/product/changelog.md

**Tests:**
- Goal-based: SKILL.md documents the three opt-ins (enrichment, chunking, Tier 3),
  the egress boundary, the local-only enrichment posture, and the Tier-3 declaration
  + doctrine as progressive disclosure; the default invocation stays the single
  `python scripts/convert.py "<input-file>"` form (AC13).
- Goal-based: no new pack-declared dependency is added (`pack.toml` runtime deps
  unchanged — enrichment/chunker/vendor all adopter-provisioned) (AC6).
- Goal-based: `pack.toml` / `plugin.json` / regenerated `marketplace.json`
  version-consistent at 0.5.0; `lint-packs`, `validate`, `build`, `pytest` green; a
  `docs/product/changelog.md` `[Unreleased]` entry records the additions (AC13).

**Approach:**
- Extend SKILL.md's tiers section with the opt-in flags and the egress doctrine
  (link `references/tier3-managed-api.md`), keeping the default one-command flow up
  top.
- Bump the version across the three files, regenerate `marketplace.json`, add the
  changelog entry.

**Done when:** the release gate (`lint-packs` + `validate` + `build` + `pytest` +
regenerated `marketplace.json`) is green and SKILL.md's default invocation is
unchanged.

## Rollout

- **Delivery:** additive, behind opt-in flags; the default path is unchanged, so no
  migration and no cutover. Reversible — the flags can be removed with no data
  effect. The one irreversible-in-effect action is *an adopter's* Tier-3 egress, but
  that is the adopter's explicit choice through their own transport, gated by the
  declaration; the skill ships no egress.
- **Infrastructure:** none — no new infra, no secrets, no IAM. Docling enrichment
  models + the chunker tokenizer are the adopter's existing Docling install.
- **External-system integration:** the Tier-3 vendor is adopter-provisioned and
  out of the pack; nothing external must be live for the pack to ship.
- **Deployment sequencing:** single PR; version bump + regenerated `marketplace.json`
  land together (release hygiene).

## Risks

- **The honest Tier-3 boundary may not satisfy a socket-level reviewer.** Because
  the skill is transport-free, "egress only to the named destination" is enforced by
  the declaration gate + the adopter's allowlisted transport, not a socket the skill
  owns. Mitigation: state the boundary explicitly; `security-reviewer` rules at spec
  and diff. If found insufficient, the fallback is option A (a thin allowlist-only
  client) — a scope change, surfaced not silently taken.
- **Docling API drift** — enrichment pipeline-options names / HybridChunker API may
  differ across Docling versions. Mitigation: monkeypatched tests assert *our*
  wiring, not Docling internals; manual QA on a real Docling install confirms; the
  version is the adopter's pinned Docling.
- **Enrichment default-path regression** — touching `_extract_docling` risks
  altering the default Tier-2 body. Mitigation: the byte-parity + default-unchanged
  regressions (T5) fail loudly on any drift.

## Changelog

- 2026-07-01: initial plan — third/final RFC-0058 slice (D5 + D6). Tier 3 resolved
  to option B (transport-free interface + gate + doctrine, no bundled HTTP client)
  per user steer; enrichment forced local-model-only; chunking emits HybridChunker
  as-is (Open-Q1); redaction out of scope with an optional-hook backlog deferral
  (Open-Q3).
