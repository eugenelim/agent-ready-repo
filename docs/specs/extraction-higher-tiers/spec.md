# Spec: extraction-higher-tiers

- **Status:** Shipped
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** RFC-0058, ADR-0045, ADR-0034 (no bundled per-vendor data / models), RFC-0007 (the converters pack this changes), and the two predecessor slices `extraction-tier0-and-output-contract` (whose `contract.py` builder, tier enum, and `safe_io` confinement this reuses) and `extraction-general-image-mode` (whose Tier-1 agent-vision path this leaves unchanged and sits above)
- **Contract:** none — the output is a Markdown file (or, for D6, a set of chunk records) with YAML frontmatter, not an API under `contracts/`. The frontmatter *is* the consumer-facing contract, pinned by the predecessor slices' `contract.py`; this slice adds only the enrichment/chunking variants of the Tier-2 body and the first real use of the `tier: "3-managed-api"` value, both gated behind opt-in flags. The Tier-3 **egress-declaration** is an adopter-facing config schema documented in the body and the tier grounding doc, not an interface under `contracts/`.
- **Shape:** service

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

<!-- Mode: full (work-loop). Risk triggers fired: governance (implements accepted
RFC-0058 D5 + D6, ADR-0045); security boundary (this is the DATA-EGRESS slice —
Tier-3 managed-API OCR crosses an egress boundary, and Docling's opt-in figure
captioning can covertly egress via a remote VLM unless forbidden); new dependency
(Docling enrichment models + HybridChunker are additional adopter-provisioned ML
surfaces, though no *new pack-declared* dep is added); public-interface change
(new opt-in flags on the shipped skill + first real use of the tier: "3-managed-api"
output value). This is the THIRD and FINAL RFC-0058 slice, sequenced after
`extraction-tier0-and-output-contract` (D2/D3/D7) and `extraction-general-image-mode`
(D4 + Tier-1). security-reviewer gates BOTH this spec and the eventual diff. -->

## Objective

`file-to-markdown` gains three **opt-in, off-by-default** higher-fidelity
capabilities on top of the no-ML floor (Tier 0), the agent-vision reads (Tier 1),
and the plain Docling pass (Tier 2) the two predecessor slices shipped — without
changing the default one-command experience for anyone who does not ask for them.
First, where an environment already permits Docling (Tier 2), a user can enable
**Docling enrichment** — formulas rendered to LaTeX (`do_formula_enrichment`),
code understanding (`do_code_enrichment`), figure classification
(`do_picture_classification`), and figure captioning (`do_picture_description`) —
running **local models only**, never Docling's remote-VLM path, so enrichment can
never become a covert egress channel that bypasses the Tier-3 gate. Second, a user
who has an **approved managed-OCR vendor** can route a specific input to **Tier 3**
— but only by *explicit* per-input (or explicit-scope) selection that names the
vendor endpoint as an allowlist and the data-residency/region; Tier 3 is **never**
reached by automatic degradation or upgrade, so the tiering engine can never fail
*open* into egress. The skill itself ships **no network client and makes no
network call**: it provides the Tier-3 *interface* (a gated assembly path that
stamps the unified contract onto adopter-obtained OCR text), the egress-declaration
config, the guardrails that refuse to proceed without a valid declaration, and the
doctrine that makes the adopter record the vendor's retention / no-training posture
as part of vendor approval — the actual vendor call is the adopter's provisioned
mechanism. Documents are sent to Tier 3 **unmodified**: pre-egress redaction is out
of scope. Third, where Tier 2 runs, a user can request **structure-preserving
output** — Docling's `HybridChunker` output emitted as-is at Tier 2, section-aware
Markdown below it — so the extraction feeds a retrieval store as tokenizer-aware,
structure-preserving chunks rather than only a flat Markdown file. Chunk output is a
separate JSON-lines sidecar (one record per chunk, each carrying the contract fields
as JSON) written through the same confined write path, distinct from the default
single `.md`, so the leading-block-only frontmatter invariant is never violated by
packing many records into one file. Every output of all three capabilities carries
the same versioned unified contract (with an honest `extraction-confidence` /
`requires-review` signal and the tier that produced it) the floor established, so
provenance stays first-class across the whole tier range. Enriched output —
figure captions especially — is **model-generated content derived from untrusted
document images**, so it is treated as untrusted data downstream exactly as every
extracted string is: it lands as inert body content that cannot forge the contract,
never as instructions to follow.

## Boundaries

### Always do

- Keep source changes inside `packs/converters/.apm/skills/file-to-markdown/`
  (`SKILL.md`, `scripts/`, `references/`), plus the pack version files
  (`pack.toml`, `.claude-plugin/plugin.json`), the top-level
  `.claude-plugin/marketplace.json` (regenerated), and `docs/product/changelog.md`.
- **Reuse the predecessors' machinery; do not fork it.** Enrichment and chunking
  attach to the existing `convert.py:_extract_docling` Tier-2 path. The **`.md`
  outputs** (enriched Tier-2 and Tier-3-assembled) are wrapped through the existing
  `contract.build_frontmatter(...)` YAML emitter — no second frontmatter builder. The
  **chunk JSONL sidecar** reuses the same contract **field set** (the dict
  `build_frontmatter` consumes and validates) serialized as JSON per record — *not* a
  second YAML emitter and not a `build_frontmatter` call (which returns a `---`-fenced
  YAML string, not JSON); this JSONL-per-record shape is the one deliberate carve-out
  from the "single builder emits every output" invariant, called out here. Every write
  goes to a path validated by `safe_io.confine`.
- **Keep all three capabilities opt-in and off by default.** With no new flag,
  `python scripts/convert.py "<input-file>"` behaves exactly as it does after
  slice 2 — plain Docling body passed through unmodified at Tier 2, no enrichment,
  no chunking, no Tier-3. Enrichment, chunking, and Tier 3 are each reached only by
  an explicit flag / declaration.
- **Rework `main()`'s argument parsing so the flags are live.** Today `main()`
  special-cases only `--check` and otherwise treats **every** token as a file path
  (`for arg in args: convert_file(...)`), so a bare `--enrich` / `--chunk` / `--tier3`
  would be passed to `convert_file(Path("--enrich"))` and fail. Restructure `main()`
  (argparse, matching the sibling `reconcile.py`) so `--enrich` and `--chunk` are
  optional flags that coexist with the **positional multi-file batch** form
  (`convert.py <file> [file2 …]`) and the `--check` probe, and `--tier3` is a distinct
  mode taking `--ocr-text`, `--endpoint`, `--residency`, and the source name. The
  no-flag positional-batch behavior stays byte-for-byte what it is after slice 2.
- **Force Docling enrichment to local models only.** When enrichment is enabled,
  set the selected `do_*_enrichment` / `do_picture_*` pipeline options **and**
  ensure Docling's remote-services path stays off — `enable_remote_services` is
  never set to `True` and `PictureDescriptionApiOptions` (the remote-VLM option
  class) is never constructed. Figure captioning uses a local model. This is a
  security-boundary control: it stops enrichment from opening a data-egress channel
  inside Tier 2 that would bypass the Tier-3 gate. (`security-reviewer` gates it.)
- **Exclude Tier 3 from the automatic tier engine.** The degradation/upgrade logic
  the floor and slice 2 established selects only among Tiers 0–2 for its automatic
  routing; `TIER_3` is never a candidate the engine can land on. Tier-3 output is
  produced only through the explicit, declaration-gated assembly path.
- **Gate Tier 3 behind a validated egress declaration.** The Tier-3 assembly path
  refuses to run unless the caller supplies a declaration naming (a) the vendor
  endpoint/host as an **allowlist** and (b) the **data-residency/region**; both are
  validated (well-formed, non-empty) before any Tier-3 output is stamped. The
  declaration is echoed into the output's provenance so the destination is auditable.
- **Record the vendor retention / no-train posture and the transport-binding
  obligation as controls.** The Tier-3 **grounding doc** (a `references/` doc the
  skill ships) makes the adopter (a) verify and record the vendor's data-retention
  and no-training-on-input terms as part of "vendor approval," (b) **configure their
  transport to egress only to the declared endpoint allowlist and residency region**
  — the adopter-side control that carries RFC-0058 D5's "egress occurs only to the
  named destination" requirement, which a transport-free skill cannot itself enforce
  at the socket — and (c) treat redaction as their own document-classification
  responsibility. The pack ships the *doctrine*, never a vendor's terms as fact.
- **Accept no secret material anywhere.** The skill never accepts, stores, logs, or
  echoes vendor credentials or any auth material; the egress declaration is
  `{endpoint-allowlist, residency-region}` only, and its validator **rejects unknown
  fields** so a credential cannot be smuggled in beside the endpoint. Authentication
  to the vendor is entirely the adopter transport's concern.
- **Never log document content or the resolved endpoint.** At default verbosity the
  skill emits no document body/content and no full OCR text to logs, and the vendor
  endpoint appears only in the intended output provenance field — never in a log line.
  (STRIDE Information Disclosure is the dominant threat on this boundary; LINDDUN
  data-minimization on the document subject.)
- **Emit chunks at Tier 2 as Docling `HybridChunker` output as-is** (RFC Open-Q1
  recommended default): a chunk-mode Tier-2 run writes the HybridChunker chunks to a
  **JSON-lines sidecar** (`<basename>.chunks.jsonl`, one record per chunk, each record
  a JSON object carrying the contract fields plus the chunk text) through
  `safe_io.confine` — *not* many YAML-frontmatter blocks in one file, which would
  break the leading-block-only invariant. Lower tiers emit **section-aware Markdown**
  (heading-structured) in the ordinary `.md`, not chunk records — HybridChunker needs
  the `DoclingDocument` that only Tier 2 produces. Chunking requires the adopter's
  `docling-core[chunking]` tokenizer extra (documented, pip-on-demand); when it is
  absent the skill errors clearly rather than crashing.
- **Treat enriched output as untrusted content.** A figure caption, formula, or code
  block Docling enrichment produces is model-generated from an untrusted document
  image; it is emitted as inert body content that cannot forge the contract (the
  predecessors' leading-block-only + first-fence guarantee), never as instructions.
  The grounding doc / SKILL.md notes captions are untrusted model output.
- Keep every higher-tier output honest: the enriched / chunked Tier-2 paths inherit
  the existing plain-Tier-2 confidence stamp (no new assessment logic — enrichment
  adds fidelity, not risk), and the **Tier-3-assembled** path defaults
  `requires-review: true` because the skill neither produced nor verified the vendor
  OCR — it never auto-claims `high` for output it did not produce.

### Ask first

- Bumping the converters pack's **minor** version — 0.4.0 → 0.5.0 is expected
  (this adds capability); confirm the number.
- Adding **any** new pack-declared dependency. This slice adds none: Docling
  enrichment models are additional surfaces of the *already adopter-provisioned*
  Docling install, `HybridChunker`'s tokenizer is the adopter's `docling-core
  [chunking]` extra (resolved on demand, documented, never a hard `pack.toml` dep),
  and Tier-3 transport is the adopter's mechanism (no client shipped). Any *other*
  deviation — a bundled HTTP client, a vendor SDK, a tokenizer the skill pins itself
  — is an escalation.
- Introducing a **neutral chunk schema** (a pack-defined chunk record shape rather
  than Docling's own). RFC Open-Q1's recommended default is *don't* — emit
  HybridChunker output as-is; introduce a neutral schema only if a consumer needs
  one. Adding one is a scope change to confirm.
- Extending the Tier-3 egress-declaration schema beyond `{endpoint-allowlist,
  residency-region}` (e.g. adding auth-material handling) — it changes the security
  surface `security-reviewer` gates.

### Never do

- **Ship a network client or make any network call from the skill.** The skill
  stays transport-free: no HTTP client, no vendor SDK, no socket. Tier-3 egress is
  the adopter's provisioned mechanism; the skill only gates, stamps, and records.
  (A grep/AST guard asserts no network-client import on any path.)
- **Enable Docling remote services on the enrichment path.** Never set
  `enable_remote_services=True`; never construct `PictureDescriptionApiOptions` or
  any remote-VLM option. Enrichment is local-model-only.
- **Let Tier 3 be reachable by automatic degradation or upgrade.** `contract.TIER_3`
  is constructed in exactly one place (`tier3.assemble_tier3`, reached only via the
  explicit `--tier3` entry point); `dispatch()` and every automatic path construct
  only Tiers 0–2, so no per-input / explicit-scope selection aside produces Tier 3.
- **Accept, store, log, or echo any secret / vendor credential**, and never log
  document content, OCR text, or the resolved endpoint. The declaration validator
  rejects unknown fields; auth is the adopter transport's concern.
- **Build a pre-egress redaction / PII-scrubbing hook.** Redaction is out of scope
  (RFC D5); documents are sent unmodified and the adopter gates at their
  classification layer. (The residual — an *optional* hook — is recorded as a
  deferred backlog item, not built here.)
- **Bundle any ML model, managed-OCR vendor endpoint, vendor SDK, per-vendor
  config, or per-vendor knowledge base** (ADR-0034 holds). The pack ships the tier
  interface and the doctrine; the adopter supplies the model, the enrichment, and
  the vendor.
- **Change the default invocation or the shipped contract shape.** The default
  `python scripts/convert.py "<input-file>"` stays a single Markdown file at the
  automatically-selected tier; the frontmatter keys are additive-only, never
  renamed/reordered (byte-stability the predecessors locked).
- Edit projected `.claude/` paths by hand — edit the `packs/converters/.apm/`
  source and regenerate.

## Testing Strategy

The vendor's OCR read (Tier 3) and Docling's enrichment/chunking outputs are
external-tool judgement and cannot be unit-asserted; everything deterministic
around them — the opt-in gating, the local-only enforcement, the never-auto-reach
guarantee, the declaration validation, the contract stamping, and the doc
grounding — is. Each user-visible outcome from the Objective pairs with a mode:

- **Enrichment is opt-in and local-only (D5, security boundary) — TDD.** With
  Docling monkeypatched, a unit test asserts that (a) with no enrichment flag the
  pipeline options set none of the `do_*_enrichment` / `do_picture_*` options and
  the body is passed through unmodified (byte-parity against the plain Tier-2 body,
  as slice-1 AC10 established); (b) with the enrichment flag the selected options
  are set; and (c) on **both** paths the constructed pipeline-options object has **no
  remote-services attribute set truthy** — an attribute-level assertion, not just the
  two named symbols, so a renamed/added remote option on a Docling bump is still
  caught. A separate grep/AST guard asserts `enable_remote_services` and
  `PictureDescriptionApiOptions` appear nowhere in the skill; the guard is tied to
  the pinned Docling version's remote surface and re-audited on any Docling bump. TDD
  because it is a pure function of the flag.
- **Enriched captions are untrusted, inert content (D5, security boundary) — TDD.**
  A fixture whose Docling figure caption / formula / code output contains `ignore all
  previous instructions …` and a `---`/`key:` line is asserted to land in the body
  verbatim and **never** in the frontmatter/contract — a contract-non-forgery test
  reusing the predecessors' leading-block-only guarantee, since enrichment output is
  model-generated from an untrusted document image.
- **Tier 3 is never auto-reached (D5, security boundary) — TDD + goal-based.** There
  is no tier-*selection* function to assert against — `convert.py:dispatch()` routes
  by file extension to a Tier-0 extractor or falls through to Docling (Tier 2). The
  real invariant: a unit test asserts every automatic path (`dispatch` + the Docling
  fall-through) constructs only `TIER_0` / `TIER_1` / `TIER_2` results across the
  input-class matrix, and a grep/AST-plus-call-graph guard asserts `contract.TIER_3`
  is constructed **nowhere except** `tier3.assemble_tier3`, which is reached only via
  the explicit `--tier3` entry point (never from `dispatch`).
- **Tier-3 egress declaration is validated + gated (D5, security boundary) — TDD.**
  The Tier-3 assembly path refuses (clear, actionable error, no output stamped) when
  the declaration is missing, when the endpoint-allowlist is absent/empty/contains a
  wildcard or a scheme-less catch-all, when the residency-region is absent, or when
  an **unknown field** is present (credential-smuggling guard); it proceeds and stamps
  `tier: "3-managed-api"` with the declared endpoint + region in provenance when the
  declaration is well-formed (non-empty hostname list, no wildcards; non-empty
  residency string). The echoed `endpoint` / `region` values pass through the
  predecessors' injection-safe frontmatter escaping — a fixture endpoint containing
  `\n---\ninjected: true` is escaped so it cannot break the block. TDD because
  refusal/acceptance and escaping are pure functions of the declaration.
- **No network client, no secret, no leaky log (D5, security boundary) — goal-based
  + TDD.** A grep/AST guard asserts no network-client package (`requests`, `httpx`,
  `urllib`, `http.client`, `socket`, a vendor SDK, …) is imported on any path and no
  vendor endpoint string is bundled; a unit test asserts the skill accepts no auth
  material (the declaration validator rejects unknown fields) and that at default
  verbosity no document body/OCR text and no endpoint is written to logs (the
  endpoint appears only in the intended provenance field).
- **Vendor retention/no-train, transport-binding, and redaction-out-of-scope
  doctrine (D5) — content check.** A content check asserts the Tier-3 grounding doc
  (a) names the retention / no-training-on-input control the adopter must record,
  (b) requires the adopter to **configure their transport to egress only to the
  declared endpoint allowlist and residency region** (the adopter-side control that
  carries RFC-0058 D5's "egress only to the named destination" under option B), and
  (c) states redaction is the adopter's document-classification responsibility
  (documents sent unmodified).
- **Chunking emits HybridChunker output as-is at Tier 2; section-aware Markdown
  below (D6) — TDD + goal-based.** With Docling monkeypatched, a unit test asserts a
  Tier-2 chunk-mode run writes a `<basename>.chunks.jsonl` sidecar (one JSON record
  per chunk carrying the full contract field set as JSON + chunk text) to a path
  validated by `safe_io.confine`; a
  below-Tier-2 chunk-mode request yields section-aware Markdown in the `.md`, not
  chunk records; a run with the `docling-core[chunking]` tokenizer extra absent errors
  clearly (no crash); a goal-based check asserts no neutral chunk schema was
  introduced (Docling's chunk shape is passed through).
- **Opt-in default is unchanged — goal-based.** A goal-based check confirms the
  documented default invocation is still the single `python scripts/convert.py
  "<input-file>"` form and that a no-flag run produces exactly the slice-2 output
  (plain Tier-2 body, no enrichment, no chunking, no Tier-3).
- **Unified contract on every higher-tier output — TDD.** Each of the enriched
  Tier-2, chunked Tier-2, and Tier-3-assembled outputs carries the versioned unified
  contract via `contract.build_frontmatter(...)` with the correct `tier` value and an
  honest confidence/`requires-review`; a byte-parity golden test proves the existing
  Tier-0/1/2 frontmatter blocks are unchanged.
- **End-to-end higher-fidelity happy paths — manual / visual QA.** In an environment
  with Docling installed: run enrichment on a real formula/code/figure PDF and
  confirm the LaTeX/caption output + `tier: "2-approved-ml"`; run chunk-mode and
  confirm HybridChunker chunks. The Tier-3 path is exercised against a *mock* adopter
  transport (no real vendor call in CI) confirming the gate + stamp + provenance.
- **Release hygiene — goal-based.** `pack.toml` / `plugin.json` / `marketplace.json`
  version-consistent (0.4.0 → 0.5.0, regenerated); `lint-packs`, `validate`,
  `build`, `pytest` green; a `docs/product/changelog.md` `[Unreleased]` entry records
  the user-visible additions; SKILL.md documents the three opt-ins, the egress
  boundary, and the local-only enrichment posture as progressive disclosure.

## Acceptance Criteria

- [x] **AC1 — Docling enrichment is opt-in, off by default, and stamps Tier 2.**
  A new explicit flag enables Docling enrichment on the Tier-2 path — formulas →
  LaTeX (`do_formula_enrichment`), code (`do_code_enrichment`), figure
  classification (`do_picture_classification`), and figure captioning
  (`do_picture_description`). With no flag, `convert.py` behaves exactly as after
  slice 2 (plain Docling body passed through unmodified; a byte-parity assertion
  against the plain Tier-2 body proves the default path is untouched). Enriched
  output carries the unified contract with `tier: "2-approved-ml"`.

- [x] **AC2 — Enrichment is local-model-only; it can never egress (security
  boundary).** On **both** the default and the enrichment path, Docling's
  remote-services path is never activated: `enable_remote_services` is never set to
  `True` and `PictureDescriptionApiOptions` (or any remote-VLM option class) is
  never constructed — figure captioning uses a local model. A unit test asserts the
  constructed pipeline-options object has **no remote-services attribute set truthy**
  (an attribute-level check, so a renamed/added remote option on a Docling bump is
  still caught), and a grep/AST guard asserts the named remote-VLM symbols appear
  nowhere in the skill — the guard is tied to the pinned Docling version's remote
  surface and re-audited on any Docling bump. This closes the covert-egress-inside-
  Tier-2 path so enrichment cannot bypass the Tier-3 gate. `security-reviewer`
  reviews this AC at spec and on the diff.

- [x] **AC3 — Tier 3 is never auto-reached (security boundary).** `convert.py` has no
  tier-*selection* function with a candidate set — `dispatch()` routes by file
  extension to a Tier-0 extractor or falls through to Docling (Tier 2). The invariant
  is asserted two ways. **Behaviorally:** a unit test over the full input-class matrix
  (digital PDF, scan, Office, image, unsupported) asserts every automatic path
  (`dispatch` + the Docling fall-through) constructs only `TIER_0` / `TIER_1` /
  `TIER_2` results. **Structurally:** an **AST guard** (`ast.walk`, not a text regex —
  a regex would false-match the `TIER_3` enum *definition* in `contract.py`, the
  "never reached here" docstrings, and the hostile `"3-managed-api"` string in an
  existing test fixture) parses each **production** module and checks two node classes
  separately, since production code references the *name* while the *literal* lives at
  the enum definition: (1) the **name/attribute** `TIER_3` / `contract.TIER_3`
  (`ast.Name` / `ast.Attribute`) is referenced **nowhere except** `tier3.py`; (2) the
  **string literal** `"3-managed-api"` (`ast.Constant`) appears **nowhere except**
  `contract.py`'s single enum definition. Test modules are out of scope for both. `tier3.assemble_tier3` (the
  sole construction site) is reachable **only** via the explicit `--tier3` entry point
  and never from `dispatch`. So no degradation/upgrade path can fail *open* into egress.
  `security-reviewer` reviews this AC.

- [x] **AC4 — Enabling Tier 3 requires a validated egress declaration; its provenance
  values are injection-safe (security boundary).** Tier 3 is reached only by an
  explicit entry point (`--tier3`) that takes the adopter-obtained OCR text (a file
  path), the source name, and the egress declaration. The `--ocr-text` input path is
  read through the existing `safe_io.check_input_size` ceiling (an unbounded-read DoS
  guard on operator-supplied input, reusing the blessed helper). The assembly path
  refuses — clear, actionable error, **no output stamped** — unless the declaration is
  well-formed:
  - (a) a **non-empty hostname allowlist**. Each element is **stripped of surrounding
    whitespace first**, then rejected if it is a wildcard / scheme-less catch-all (empty
    or whitespace-only string, `*`, `.`, `0.0.0.0`, `::`) or a **loopback / link-local /
    private / metadata target**. IP-literal elements are validated by a **rule, not an
    enumerated list**: parse via `ipaddress.ip_address` (canonicalizing IPv4-mapped IPv6
    such as `::ffff:169.254.169.254` to its embedded IPv4) and reject if any of
    `is_loopback`, `is_link_local`, `is_private`, `is_multicast`, `is_unspecified`, or
    `is_reserved` — so IPv4, IPv6 link-local (`fe80::/10`), ULA (`fc00::/7`), and
    IPv4-mapped forms are covered uniformly by construction rather than by an example
    list an implementer could ship gaps against. An element that **looks like an IP/CIDR
    literal but fails `ipaddress.ip_address` parsing** (e.g. a `::/0` or `0.0.0.0/0`
    CIDR, which is not a bare address) is **rejected, not silently treated as a
    hostname**, so a malformed-but-suggestive literal cannot bypass the IP rule. Hostname
    elements that are metadata/loopback names in disguise are also rejected by an
    exact/suffix list (`localhost`, `*.localhost`, `metadata`, `metadata.google.internal`,
    `*.internal`; **non-exhaustive — the connect-time block in AC7 is authoritative**).
    **This string validation is a footgun-reducer, not the SSRF control** — the skill
    opens no socket and never resolves a hostname, so a hostname that *resolves* to a
    metadata/private IP still passes the string check; the resolve-time / connect-time
    block is the adopter transport's obligation, recorded in AC7. The rejection is
    deliberate provenance-hygiene defense-in-depth over RFC-0058 D5, recorded in
    Assumptions.
  - (b) a **non-empty residency-region string**.
  - (c) **no unknown fields** — the declaration's key set must **equal exactly**
    `{endpoint-allowlist, residency-region}` (an allowlist-of-keys check, not a denylist
    of credential-looking names, so `authorization` / `x-api-key` cannot slip through);
    this is the credential-smuggling guard.

  When valid it stamps `tier: "3-managed-api"`, sets `content-type` from the `--source`
  name's suffix (falling back to `managed-ocr` when indeterminate), and echoes the
  declared endpoint (as a **comma-joined scalar**, so the hand-rolled emitter's scalar
  escaping applies and the value stays auditable and parseable) + region into
  provenance. **All three echoed-into-frontmatter values — endpoint, region, and the
  `--source`-derived `content-type` — pass through the predecessors' injection-safe
  frontmatter escaping** (`contract.build_frontmatter`'s `_escape`), so an element
  containing `\n---\ninjected: true` is escaped and cannot break the block. Tests cover
  missing declaration; empty/`*`/`.`/`0.0.0.0` endpoint; a loopback / metadata-IP
  endpoint (IPv4 **and** an IPv4-mapped-IPv6 form); a `localhost` / metadata-hostname
  endpoint; absent residency; an unknown field; an injection-bearing endpoint element
  **and an injection-bearing `--source` name**; and the valid case. `security-reviewer`
  reviews this AC.

- [x] **AC5 — The skill ships no network client, holds no secret, and leaks nothing to
  logs (security boundary).** No HTTP client, vendor SDK, or socket is imported on any
  path and no vendor endpoint string is bundled (a grep/AST guard asserts this). The
  guard **enumerates the skill's production `*.py` scripts by directory glob, not a
  hard-coded file list**, so the new `tier3.py` (and any future module) is covered by
  construction — the existing static `_ALL_SCRIPTS` list in `test_convert.py` is
  replaced by (or augmented to derive from) the glob, closing the false-green where a
  new high-risk module is silently skipped. Tier-3 egress is the adopter's provisioned
  transport. The skill **accepts, stores, logs, or
  echoes no auth material** — the declaration validator rejects unknown fields, and
  authentication is entirely the transport's concern. At default verbosity the skill
  writes **no document body / OCR text and no endpoint** to logs; the endpoint appears
  only in the intended provenance field. The spec states the honest boundary: the skill
  gates and declares; the adopter's transport enforces the socket. `security-reviewer`
  reviews this AC.

- [x] **AC6 — No bundled models or per-vendor data (ADR-0034).** No ML model,
  managed-OCR vendor endpoint, vendor SDK, per-vendor config, or per-vendor knowledge
  base ships with the pack. Docling enrichment models are adopter-provisioned via the
  already-documented Docling install; the chunker tokenizer is the adopter's
  `docling-core[chunking]` extra; the Tier-3 vendor is adopter config. The pack ships
  the tier **interface**, not a chosen vendor.

- [x] **AC7 — Retention/no-train + transport-binding are recorded controls; redaction
  is out of scope.** The Tier-3 grounding doc (a shipped `references/` doc) makes the
  adopter (a) verify and record the vendor's data-retention and no-training-on-input
  terms as part of vendor approval, (b) **configure their transport to egress only to
  the declared endpoint allowlist and residency region** — the adopter-side control
  that carries RFC-0058 D5's "egress occurs only to the named destination" under the
  transport-free (option B) design, which the skill cannot enforce at the socket — and
  (c) treat redaction as their document-classification responsibility; documents are
  sent to Tier 3 **unmodified** and the skill builds no pre-egress redaction hook. A
  content check asserts all three statements are present. The *optional* pre-egress
  redaction hook (RFC Open-Q3 residual) is recorded as a deferred backlog item, not
  built. `security-reviewer` reviews this AC.

- [x] **AC8 — Structure-preserving chunk output at Tier 2 is opt-in and emitted
  as-is, as a JSONL sidecar (D6).** A new explicit flag (`--chunk`) makes a Tier-2 run
  write Docling's `HybridChunker` output (tokenizer-aware, structure-preserving chunks)
  to a **`<basename>.chunks.jsonl` sidecar** — one JSON record per chunk. Each record
  carries the **full unified contract field set** (`contract-version`, `source-file`,
  `content-type`, `tier: "2-approved-ml"`, `ingestion-date`, and the nested
  `ingestion-quality` block) **serialized as JSON**, plus the chunk text — produced by
  the **shared `contract.build_fields(...)` builder** (AC10), not by calling
  `build_frontmatter` (which returns YAML), so the field set has one source and no
  leading-block-only invariant is violated by packing many records into one file. Written to a path validated by
  `safe_io.confine`, separate from the default `.md`. Chunking requires the adopter's
  `docling-core[chunking]` tokenizer extra; when it is absent the run errors clearly
  (no crash). Off by default — the default stays a single Markdown file.

- [x] **AC9 — Below Tier 2, structure-preserving output is section-aware Markdown; no
  neutral chunk schema (D6, Open-Q1).** When chunk-mode is requested below Tier 2 (no
  `DoclingDocument` available), the output is **section-aware (heading-structured)
  Markdown**, not chunk records. No pack-defined neutral chunk schema is introduced —
  Docling's chunk shape is passed through as-is (a goal-based check asserts no neutral
  schema was added).

- [x] **AC10 — Every higher-tier output carries the unified contract, honestly.**
  The enriched Tier-2 and Tier-3-assembled `.md` outputs emit the versioned unified
  contract via `contract.build_frontmatter(...)`; the chunked JSONL records carry the
  **same field set** as JSON (AC8), produced by a **single shared field-set builder in
  `contract.py`** (`build_fields(...) -> OrderedDict`) that both `build_frontmatter`
  (which then emits YAML) and the JSONL writer (which then `json.dumps`) consume — so
  the contract-version prepend, the `tier` key, the nested `ingestion-quality` block,
  **and the contract validation** (tier / confidence enum membership, reserved-key
  shadowing, required-key presence) all have **one source in `build_fields`**; the JSONL
  path — which never calls `build_frontmatter` — still inherits every validation, so it
  cannot fork or forge the contract. (`build_fields` validates the caller-assembled
  `fields`; it does not synthesize them, so each JSONL per-record field set must itself
  carry `source-file` / `content-type` / `ingestion-date` for the inherited presence
  check to pass.) Each output carries
  the correct `tier` value, and confidence is stamped honestly, not optimistically: the
  enriched / chunked Tier-2 paths **inherit the existing plain-Tier-2 confidence stamp**
  (this slice adds no new confidence-assessment logic, so Docling's happy path stays
  `high` as it does today — enrichment adds fidelity, not risk), while the
  **Tier-3-assembled** path — where the skill neither performs nor verifies the vendor
  OCR — is stamped **`requires-review: true` non-negotiably** with a fixed
  `extraction-confidence: "low"`, with **no caller override**: the skill never claims
  `high` / `requires-review: false` for output it did not produce, and there is no flag
  or parameter by which a caller could. A byte-parity golden test proves the existing
  Tier-0/1/2 frontmatter blocks are unchanged (additive-only).

- [x] **AC11 — Opt-in default is unchanged (no regression).** A no-flag `python
  scripts/convert.py "<input-file>"` run produces exactly the slice-2 output for every
  input class (plain Tier-2 body when Docling runs, Tier-0/1 as before) — no
  enrichment, no chunking, no Tier-3. A goal-based check confirms the documented
  default invocation is still the single one-command form.

- [x] **AC12 — Enriched output is untrusted, inert content (security boundary).**
  Docling enrichment output — a figure caption, formula, or code block — is
  model-generated from an untrusted document image, so it is emitted as body content
  that cannot forge the contract: a fixture whose caption/formula/code contains
  `ignore all previous instructions …` and a `---`/`key:` line is asserted to land in
  the body verbatim and **never** in the frontmatter (a contract-non-forgery test
  reusing the predecessors' leading-block-only + first-fence guarantee), and the
  grounding doc / SKILL.md note that enriched captions are untrusted model output to be
  treated as data, never instructions, downstream. `security-reviewer` reviews this AC.

- [x] **AC13 — Release hygiene + progressive-disclosure default.** The converters pack
  is bumped 0.4.0 → 0.5.0 across `pack.toml`, `plugin.json`, and the regenerated
  `marketplace.json`; `lint-packs`, `validate`, `build`, and `pytest` are green;
  `docs/product/changelog.md` records the user-visible additions; SKILL.md documents
  the three opt-ins, the egress boundary, the local-only enrichment posture, and the
  Tier-3 declaration + doctrine as progressive disclosure, with the default invocation
  still the single `python scripts/convert.py "<input-file>"` form. (Test coverage of
  AC1–AC12's deterministic pieces is the Testing Strategy's obligation, verified under
  each of those ACs — not re-asserted here as a meta-criterion.)

## Assumptions

- Technical: the target skill is `file-to-markdown` in the `converters` pack
  (now **v0.4.0**, both predecessor slices shipped); `contract.py` already exports
  `TIER_2 = "2-approved-ml"`, `TIER_3 = "3-managed-api"` (commented "never reached
  here"), `TIERS`, `build_frontmatter(...)`, and `now_iso()`, which this slice
  reuses. *(source: repo read of
  `packs/converters/.apm/skills/file-to-markdown/scripts/contract.py` + `pack.toml`
  + `.claude-plugin/plugin.json`, 2026-07-01.)*
- Technical: the Docling Tier-2 path is `convert.py:_extract_docling` — a bare
  `DocumentConverter().convert(...).export_to_markdown()` with the body passed
  through unmodified, `tier=TIER_2`, hard-coded `confidence="high"`, and no
  enrichment or chunking today; this slice attaches the opt-in enrichment/chunking
  there. *(source: repo read of `convert.py:602-656`, 2026-07-01.)*
- Technical: Docling enrichment is enabled through pipeline options
  `do_code_enrichment` / `do_formula_enrichment` / `do_picture_classification` /
  `do_picture_description`, all **disabled by default**, each requiring additional
  models. *(source: [Docling enrichments docs](https://docling-project.github.io/docling/usage/enrichments/),
  fetched 2026-07-01.)*
- Technical (security-critical): Docling's figure captioning (`do_picture_description`)
  can call a **remote VLM API** via `PictureDescriptionApiOptions` +
  `enable_remote_services=True` — an egress path *inside* Tier 2 that this slice
  forbids so enrichment cannot bypass the Tier-3 gate. *(source:
  [Docling enrichments docs](https://docling-project.github.io/docling/usage/enrichments/),
  fetched 2026-07-01.)*
- Technical: Docling's `HybridChunker` produces tokenizer-aware, structure-preserving
  chunks (`chunk()` over a `DoclingDocument` + `contextualize()`), the D6 recommended
  default emitted as-is; its HuggingFace tokenizer requires the adopter's
  `docling-core[chunking]` extra (not pulled by base Docling), documented and
  pip-on-demand. *(source:
  [Docling chunking docs](https://docling-project.github.io/docling/concepts/chunking/)
  + RFC-0058 D6 / Open-Q1, fetched 2026-07-01.)*
- Technical: no Tier-3 client, enrichment call, or chunker exists in the pack today
  — this slice is all net-new; `TIER_3` is defined but unreached. *(source: grep across
  `packs/converters/`, 2026-07-01.)*
- Product: RFC D5's "vision-model reads" lever ships as **nothing new** beyond the
  already-shipped Tier-1 agent-vision read (slice 2) plus local Docling figure
  captioning (`do_picture_description`, kept local-model-only) — a deliberate scope
  reduction, not a separate fourth higher-fidelity vision mechanism. A reader checking
  RFC D5 coverage should see this reduction plainly. *(source: user confirmation
  2026-07-01.)*
- Product: Tier 3 ships as the **interface + config + guardrails + doctrine** (option B)
  — the skill makes no network call; the vendor OCR call is the adopter's provisioned
  transport (SDK / CLI / MCP), and the skill's job is to gate, stamp the contract, and
  record the doctrine. *(source: user confirmation 2026-07-01.)*
- Process (RFC reconciliation): RFC-0058 D5 charges the implementing spec to "assert
  egress occurs only to the named destination." Under option B the skill owns no socket
  and makes no egress, so it cannot assert this at the socket level; the requirement is
  reinterpreted as **the declaration gate constrains the destination and the adopter's
  transport enforces the socket** (a recorded adopter control in the Tier-3 grounding
  doc — AC7). This is a deliberate spec-vs-RFC reinterpretation, recorded here rather
  than left as silent drift, and `security-reviewer` signs off on it. *(source: RFC-0058
  D5 line 87 + user steer 2026-07-01; security-reviewer spec-stage pass.)*
- Process (spec-over-RFC hardening): the declaration validator's rejection of
  loopback / link-local / private / metadata / IPv4-mapped-IPv6 targets and
  metadata/loopback hostnames (AC4) is a **deliberate addition over RFC-0058 D5**,
  which requires only an endpoint allowlist + residency. Because the skill is
  transport-free it opens no socket and resolves no hostname, so this is
  **provenance-hygiene defense-in-depth (a footgun-reducer), not a socket-level SSRF
  control** — the connect-time metadata/private-range block is the adopter transport's
  obligation (AC7). Recorded here rather than left as silent gold-plating.
  *(source: spec-stage adversarial + security review 2026-07-01.)*
- Product: redaction is out of scope (documents sent unmodified); the *optional*
  pre-egress redaction hook (RFC Open-Q3 residual) is deferred, not built. *(source:
  RFC-0058 D5 + Open-Q3 recommended default; user confirmation 2026-07-01.)*
- Product: chunk output is Docling `HybridChunker` as-is at Tier 2, section-aware
  Markdown below; no neutral chunk schema (RFC Open-Q1 recommended default). *(source:
  RFC-0058 D6 / Open-Q1; user confirmation 2026-07-01.)*
- Product: the consumer of the output is an AI **context layer** (retrieval stores /
  injected reference material), for which Markdown + provenance + structure-preserving
  chunks is the right shape. *(source: RFC-0058 Problem & goals + Evidence F6/F7.)*
- Process: RFC-0058 (Accepted 2026-06-30) is the governing decision and ADR-0045
  records the doctrine; this is the D5 + D6 slice its Follow-on artifacts name,
  sequenced **last** after both predecessor slices. *(source: `docs/rfc/0058-*.md`,
  `docs/adr/0045-*.md`.)*
- Process: `converters` is a user-scope-default pack (not in this repo's self-host
  projection), so the version bump drifts `marketplace.json` and the gate is
  `lint-packs` + `validate` + `build` + `pytest` (regenerating `marketplace.json`),
  **not** `build-self` / `pre-pr`. *(source: predecessor slice `plan.md` § Constraints +
  repo convention.)*
- Process: the pack bump is **minor** — 0.4.0 → 0.5.0 (adds capability). *(source:
  user confirmation 2026-07-01.)*
- Process: this is the egress-boundary slice; `security-reviewer` gates BOTH the spec
  (spec-stage secure-design pass) and the eventual diff. *(source: RFC-0058 D5 +
  Reviewer brief review-focus; user instruction 2026-07-01.)*

### Declined patterns

- Tempted to ship a **thin allowlist-enforcing HTTP client** in the skill so Tier-3
  egress goes only to the named endpoint at the socket level (my earlier lean A);
  declining — it adds a bundled general-purpose egress surface that could fail open,
  contradicts the predecessors' "skill makes no network call" invariant, and is
  unnecessary when the adopter's harness/SDK/MCP already provides transport. Option B
  (interface + gate + doctrine, transport-free skill) is safer and honors ADR-0034;
  the honest boundary (skill gates + declares, adopter transport enforces the socket)
  is stated for `security-reviewer` to rule on.
- Tempted to enable Docling **figure captioning via its remote VLM** (`PictureDescription
  ApiOptions`) since it is the highest-fidelity captioner; declining — it is a covert
  egress channel inside Tier 2 that would bypass the Tier-3 gate. Captioning stays
  local-model-only; `enable_remote_services` is never set.
- Tempted to introduce a **neutral pack-defined chunk schema** so consumers aren't
  coupled to Docling's chunk shape; declining (RFC Open-Q1 recommended default) — emit
  HybridChunker output as-is; a neutral schema is introduced only if a consumer needs
  one, and that would be its own slice.
- Tempted to build the **optional pre-egress redaction hook** (RFC Open-Q3 residual) so
  Tier-3 documents can be scrubbed before egress; declining — RFC D5 decides redaction
  out of scope (adopters gate at their classification layer). Recorded as a deferred
  backlog item to revisit if an adopter needs it.
- Tempted to make enrichment or chunking **on by default** for higher fidelity;
  declining — RFC D5/D6 make all three opt-in and off by default so the default
  one-command experience and the shipped output shape are unchanged (extra models /
  processing time / a changed output shape are the adopter's explicit choice).
- Tempted to let Tier 3 be an **automatic upgrade** when a vendor is configured (so
  high-volume inputs route there without per-input selection); declining — RFC D5
  makes Tier 3 explicit-only and never auto-reached, so the tiering engine can never
  fail open into egress. Configuration availability is not selection.
