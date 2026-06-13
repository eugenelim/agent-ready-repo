# RFC-0031: Package-manager posture for the pack catalogue — rich pack manifest + lossy marketplace projection

- **Status:** Accepted <!-- Draft | Open | Final Comment Period | Accepted | Rejected | Withdrawn | Experimental (optional: trial running, results pending — see the Experiment / validation section) -->
- **Author:** eugenelim
- **Approver:** eugenelim
- **Date opened:** 2026-06-13
- **Date closed:** 2026-06-13
- **Related:** RFC-0001 (bundle distribution by adapter), RFC-0008 (claude-plugins install route), RFC-0011 (per-pack `allowed-adapters` — `pack.toml` field precedent), ADR-0001 (AGENTS.md + doc hierarchy), `docs/CHARTER.md` (scope: "catalogue"; non-goal "not a marketplace of specialized agents"; Principle 3 "a habit, not a tool")

## The ask

- **Recommendation (BLUF):** Make **`pack.toml` the rich, single source of truth for pack metadata** and **project a lossy, per-tool subset** into each adapter's native marketplace/manifest format. Treat this as *catalogue/distribution hygiene* — describing what we already ship as richly as the tools that consume it — **not** as building package-manager infrastructure. Approve the direction and the decomposition; the first concrete change (the enriched-manifest spec) follows separately.
- **Why now (SCQA):**
  - *Situation* — we are "a catalogue" (`docs/CHARTER.md`) that projects agent primitives onto every supported tool, and we already publish `agentbundle`/`credbroker` wheels to PyPI.
  - *Complication* — our own PyPI wheels get rich, rendered metadata for free, but our **packs** are described by only `name`/`version`/`description`. The richer marketplace formats the tools now ship (Claude Code, Codex, Copilot) accept author/license/links/keywords/categories — and we surface none of it. Meanwhile it is unclear *which file* owns pack metadata, because `marketplace.json` is Anthropic's format, not ours.
  - *Question* — where should rich pack metadata live, and how should it reach each tool, without drifting into building a hosted registry?
- **Decisions requested** (all recommended for approval; decide-by: at sign-off, default = accept as written):
  1. **Charter posture** — adopt the "catalogue hygiene / package-manager *posture*" framing; all hosted-registry/indexer/server **infrastructure stays out of scope**. *Recommended: accept.*
  2. **Metadata source of truth** — `pack.toml` is the rich superset; marketplace formats are lossy projections. *Recommended: accept.*
  3. **Field set** — a defined set of cross-tool-projectable fields become first-class; tool-specific knobs live in a `[pack.metadata.<tool>]` extension table. *Recommended: accept.*
  4. **README + docs** — bundle a `readme = "README.md"` (rendered + projected), keep `seeds/docs/` for adopter-owned guides, point a `documentation` URL at hosted deep docs. *Recommended: accept.*
  5. **`plugin.json` authoring** — derive the projectable fields from `pack.toml` rather than hand-author them twice. *Recommended: accept.*
  6. **Roadmap decomposition** — this RFC sets direction; the enriched-manifest **spec ships first**, with the neutral index contract, the virtual/blended catalogue, and provenance/scan-on-publish as **follow-on RFCs**, and indexer scaling + hosting explicitly **deferred infra**. *Recommended: accept.*
  7. **Scoped identity** — adopt `@catalogue/pack` (npm-style), bare/unscoped resolving to the public default catalogue, so private and public catalogues coexist without renaming. *Recommended: accept.* (See D7.)
  8. **Soft `categories` vocabulary** — ship a suggested default category list, validated with a warning (not an error), extensible and possibly free-form later — we do **not** control it as a hard registry. *Recommended: accept.* (See D8.)

## Problem & goals

**Diagnosis.** A pack is the unit we distribute, but the manifest that describes it (`packs/<pack>/pack.toml`) carries only `name`, `version`, and `description`. Three independent consequences follow:

1. **Under-description.** A consumer browsing the catalogue cannot see who maintains a pack, its license, where its source/docs/changelog live, or what it's *for* beyond one sentence — even though our own PyPI wheels expose all of this and the tools' own marketplace formats accept it.
2. **Ambiguous metadata home.** The aggregated index is `.claude-plugin/marketplace.json`, which is **Anthropic's Claude Code format** (consumed by `/plugin marketplace add`). It is not ours to own as a metadata home, and putting metadata there is upward-lossy to every other tool.
3. **No discovery surface.** With only name + a one-line description to match on, there is nothing to search or browse by — no keywords, no categories.

**Goals.**

- A single, repo-owned source of truth for pack metadata that is rich enough to describe a pack the way PyPI/crates.io describe a package.
- A defined, lossy projection from that source into each tool's native format, requiring **no upstream cooperation**.
- A discovery surface (keywords + a soft category vocabulary) and a rendered long-form description (a per-pack README) that travels with the pack.
- A scoped identity that lets a private/org catalogue and the public default coexist without renaming packs.
- A clean decomposition so the cheap, contained manifest work ships first and the heavier registry concerns are sequenced as their own RFCs.

**Non-goals** (could-have-been-goals, deliberately dropped):

- **A hosted registry, website, search service, or download-stats backend.** This is infrastructure; Principle 3 ("a habit, not a tool… not a piece of infrastructure") puts it out of bounds. We design the *shape* (a queryable index contract) so a future service can grow into it, but we build no server here.
- **A scalable indexer.** The live filesystem scan does not survive 10k packs; we are locking the manifest *shape* now and deferring the indexer to future infra. (See Risks.)
- **A dependency resolver.** We have declared dependencies with constraints today; a real range/transitive resolver waits until a second catalogue or real diamond conflicts exist.
- **Opening public, third-party pack submission.** That would change the impersonation threat model and the charter's "not a marketplace of specialized agents" stance. The scoped-identity design *leaves room* for it but does not enable it.
- **Replacing or retiring `.apm/`.** It remains the canonical primitive payload; this RFC only enriches the manifest beside it.

## Proposal

The design cascades under the eight requested decisions. Existing state to convert is small and handled by an optional, version-gated schema extension (see *Migration*).

### D1 — Charter posture: hygiene, not infrastructure

We frame this as making the catalogue's manifest describe what it already ships as richly as the tools that consume it. Concretely: every field added below either (a) already has a native home in a tool's marketplace format, or (b) describes the pack for our own catalogue. No runtime, no server, no daemon. The charter's non-goal ("not a marketplace of specialized agents") concerns *content* — not accumulating reviewer agents — and is untouched; this RFC adds zero primitives. Principle 3 is honored by the Non-goals above.

### D2 — `pack.toml` is the rich superset; marketplaces are lossy projections

`pack.toml` (ours; `docs/contracts/pack.schema.json`) becomes the single source of truth. Each tool receives a **subset** of the metadata, and — critically — **different fields land in different files per tool**: Claude Code and Copilot have rich `marketplace.json` *entries*, but Codex's marketplace entry is thin and its richness lives in `.codex-plugin/plugin.json` plus an `interface` block. The projector therefore routes each field to the right destination file for each tool. Projection is one-directional (`pack.toml` → tool format) and never round-trips.

### D3 — First-class fields vs. the `[pack.metadata.<tool>]` extension hatch

First-class (projects cleanly to ≥1 real tool, modeled on Cargo/PyPI/Helm):

```toml
[pack]
name = "core"; version = "0.4.0"          # existing
description = "…"                          # existing — plain-text one-liner
display_name = "Core"                      # OPTIONAL — Claude/Codex display name
readme = "README.md"                       # path pointer; rendered long-form (Cargo model)
license = "Apache-2.0 OR MIT"              # SPDX expression
[[pack.maintainers]]                       # Helm-style {name, email, url}
name = "…"; email = "…"; url = "…"
[pack.links]                               # distinct named URLs (Cargo + gemspec)
homepage = "…"; repository = "…"; documentation = "…"; changelog = "…"; issues = "…"; icon = "…"
categories = ["…"]                         # soft controlled vocab (D8), ≤5
keywords   = ["…"]                         # free-form, ≤5
[pack.metadata.claude]  strict = true      # extension hatch — Cargo [package.metadata] model
[pack.metadata.codex]   policy = { installation = "AVAILABLE", authentication = "ON_INSTALL" }
```

Tool-specific knobs (Claude `strict`, Codex `policy`/`interface` store-listing) go in `[pack.metadata.<tool>]`, which the schema ignores — so we never break the schema to add a tool. Existing tables (`[pack.adapter-contract]`, `[pack.install]`, `[pack.dependencies.*]`, `[pack.adaptation]`, `seeds`, `recipes`) are unchanged. `[pack.adapter-contract] version` already serves as our host-compat floor (the analogue of Cargo's `rust-version`), so no new compat field is needed.

### D4 — README + docs: three roles, each for its purpose

- **`readme = "README.md"`** — a file pointer (Cargo auto-detects `README.md` if omitted). The README already exists at pack root; the projectors copy it into each dist route and reference it. It is the version-pinned, travels-with-the-pack long-form description, rendered on the catalogue/plugin page. The one-line `description` stays for dense UIs (the PyPI `summary`/`long_description` split).
- **`seeds/docs/`** — unchanged; this is how a pack ships docs the *adopter owns and edits in their repo* (precedent: the `user-guide-diataxis` pack ships `seeds/docs/guides/{tutorials,how-to,reference,explanation}`).
- **`[pack.links].documentation`** — a URL to hosted deep docs that shouldn't bloat every install.

We explicitly do **not** bundle multi-page guides into `.apm/` (the primitive payload) — that inflates every install.

### D5 — Derive `plugin.json` projectable fields from `pack.toml`

Today `.claude-plugin/plugin.json` is hand-authored (`docs/architecture/pack-layout.md`), with the build already synthesizing part of it (the `SessionStart` hook, per RFC-0008). We extend that: the projectable metadata fields are **derived from `pack.toml`** so there is one source of truth, not two that drift. Full elimination of hand-authoring is a natural endpoint but out of this RFC's scope.

### D6 — Roadmap decomposition

| Gap | Vehicle |
| --- | --- |
| Enriched `pack.toml` schema + README projection + surfacing the projectable subset into `marketplace.json` (relaxing our `additionalProperties:false`) + `@catalogue/pack` identity + soft `categories` | **First spec** (`new-spec`) |
| Neutral, queryable index contract (`marketplace.json` projected *from* it) | Follow-on RFC |
| Virtual / blended private+upstream catalogue (Artifactory virtual-repo / devpi index-inheritance model) | Follow-on RFC |
| Provenance generate/verify + scan-on-publish (reusing the security-reviewer + SAST direction) | Follow-on RFC |
| Channels, real/bounded dependency resolver, reproducible lock | Deferred (after the index contract) |
| 10k-pack indexer, hosted registry, download stats | Deferred infra (pre-staged by the index contract; not built here) |

### D7 — Scoped identity: `@catalogue/pack`

Adopt npm-style `@catalogue/pack`, with a **bare, unscoped `pack` resolving to the public default catalogue**. This is the smallest move from today's two-field model (`catalogue = "…"` + `pack = "…"`), and it gives the property we want: a private/org catalogue and the public default can host packs of the same short name simultaneously without renaming — the unscoped name resolves against the default, the scoped name against its bound catalogue. Inherit npm's lexical rules (lowercase, URL-safe, hyphens, no leading `.`/`_`). Ownership-proof is deliberately deferred (a curated catalogue needs convention, not cryptography); if public submission is ever opened, bind a scope to a verified GitHub org/domain at publish time — a registry policy, not a syntax change. (Reverse-DNS, à la the MCP Registry, was rejected as high-authoring-cost and only justified by open public submission, which is a non-goal.)

### D8 — A soft `categories` vocabulary (suggested defaults, not enum-locked)

We ship a **suggested default** category list and validate an unknown slug with a **warning, not an error** — the list can grow, and may become fully free-form later. Direct precedent: Claude Code's marketplace `category` is a free-form string with no enum; Smithery/PulseMCP browse by open tags. Style: kebab-case, flat (no `::` hierarchy until the list is large; the upgrade path is non-breaking). Proposed initial slugs (~16), each mapping to our existing/ planned pack lineup: `code-review`, `testing`, `documentation`, `architecture`, `security`, `research`, `product-management`, `project-management`, `integrations`, `file-conversion`, `api-design`, `governance`, `credentials`, `devops`, `data`, `ai-agent`. We do **not** control the vocabulary as a hard registry; these are defaults with room to extend.

### Migration

Follow RFC-0011's model exactly: a single **adapter-contract version bump** (currently `0.13` per `docs/contracts/adapter.toml` — the spec must re-grep at authoring time, the contract moves fast) gates the schema extension; **every new field is optional**; legacy packs need no migration. The breaking-shaped change is relaxing **both** of our `additionalProperties:false` gates to admit the projectable fields: the authoring `docs/contracts/plugin-manifest.schema.json` **and** the projected-output `plugin-manifest.derived.schema.json` (the binding gate — it validates the `dist/.../plugin.json` the new fields actually land in; relaxing only the authoring schema would fail the build). Both are entirely within our control and verified safe on the consumer side (see Evidence).

## Options considered

**Axis: where the source of truth for pack metadata lives.** This axis is exhaustive — metadata must live in *our* manifest, in a *tool's* format, in a *new* file, or nowhere new (status quo). Each option below is grounded in prior art.

| Option | Prior art | Trade-offs |
| --- | --- | --- |
| **(a)** Put rich metadata in `marketplace.json` / `plugin.json` (Anthropic's format) | Claude Code marketplace | Native rendering in Claude — but it's **not our format to own**, it's upward-lossy to every non-Claude tool, and our `plugin-manifest.schema.json` exists precisely to *constrain* it. Rejected. |
| **(b) `pack.toml` rich superset + lossy per-tool projection** ★ | Cargo `[package]` + `[package.metadata]`; our own `.apm/` → per-tool projection (`pack-layout.md`); RFC-0001 adapter-contract-as-source-of-truth | Ours, already extensible, projection is the established repo model; cost is writing per-tool projectors. **Recommended.** |
| **(c)** Introduce a new neutral index file *now*, separate from both `pack.toml` and `marketplace.json` | PEP 691 simple-index JSON; MCP `/v0/servers` | The right long-term shape for a *queryable index* — but premature as the *manifest*; it's the follow-on index-contract RFC, not this one. Deferred, not rejected. |
| **(d) Do nothing** — keep the three-field manifest | — | Zero cost now; but the brief's actual complaint (packs under-described vs. our own wheels) stands, and the gap widens as tools ship richer marketplace formats. Cost of delay: every pack stays undiscoverable and the metadata-home ambiguity persists. |

## Risks & what would make this wrong

**Pre-mortem (assume it shipped and failed):**

- *The projectors drift from each tool's evolving format.* Mitigation: projection is mechanical and gate-tested (we already drift-gate projected artifacts); a contract version pins the shape.
- *Scope creep into infrastructure.* The "package manager" framing tempts a hosted registry. Mitigation: D1 + Non-goals draw the line explicitly; the indexer and server are named as deferred infra, not silent omissions.
- *The soft category list ossifies into a de-facto hard enum.* Mitigation: validate-with-warning, documented as extensible, with free-form as the stated escape hatch.

**Key assumptions (falsifiable):**

- *Tools tolerate a rich, lossy projection without upstream cooperation.* Falsified if a tool erred on the metadata fields. **Verified for Claude** — every proposed field is natively supported by its marketplace entry (see Evidence). Copilot (mirrors Claude's schema) and Codex (richness in `.codex-plugin/plugin.json`) are **to be confirmed by each tool's projector at build time** — their unknown-field handling / marketplace-file location are not authoritatively documented.
- *The binding constraint is our own schema, not a tool's loader.* Falsified if some tool rejected unknown fields. Verified: the only `additionalProperties:false` gates in the path are ours (the authoring + the projected-output `plugin-manifest` schemas).
- *`@catalogue/pack` lets private + public coexist without renaming.* Falsified if npm's scope model didn't actually behave this way. Verified against npm docs (Evidence).

**Drawbacks (not "none"):**

- Per-tool projectors are ongoing maintenance as marketplace formats evolve.
- A richer manifest is more for pack authors to fill in (mitigated: every new field is optional).
- We are committing to a manifest shape *before* the index contract exists, so a later index-contract RFC must stay compatible with it (accepted: the manifest is the stabler of the two).

## Evidence & prior art

**Spike / de-risk result.** The riskiest assumption — that we can project rich metadata to the tools' marketplace formats *without upstream cooperation and without breaking the loader* — was tested by fetching the live Claude Code marketplace docs ([code.claude.com/docs/en/plugin-marketplaces](https://code.claude.com/docs/en/plugin-marketplaces)). Result: a plugin entry may include "any field from the plugin manifest schema… plus `source`, `category`, `tags`, `strict`," and the documented field table natively includes `displayName`, `author`, `homepage`, `repository`, `license` (SPDX), `keywords`, `category`, `tags`, `defaultEnabled`. The validate error/warning lists contain **no unrecognized-field rule**. So the projection relies on *supported* fields, not merely tolerated extras, and the only `additionalProperties:false` gates in the chain are our own — the authoring `plugin-manifest.schema.json` and the projected-output `plugin-manifest.derived.schema.json` (the latter being the binding gate for what actually ships, per Migration). **Direction viable with zero external dependency.**

**Repo precedent.**

- `docs/CHARTER.md` — "this catalogue is an attempt to build one"; non-goal "Not a marketplace of specialized agents"; Principle 3 "A habit, not a tool… not a piece of infrastructure"; "tools with their own primitives layer those on top" — grounds lossy per-tool projection as charter-consistent and bounds the infrastructure line.
- `docs/architecture/pack-layout.md` — `pack.toml` is "pack metadata, schema-enforced"; `.apm/` is "projected by the build pipeline"; `plugin.json` is "hand-authored"; the build "projects `.apm/<type>` into per-tool output." Projection from a source is the established model.
- RFC-0001 — the adapter contract lives in TOML and is the "live source of truth," projected per-IDE. Source-of-truth-plus-projection precedent.
- RFC-0008 — `plugin.json` is already partly *derived* (synthesized `SessionStart`), establishing the derive-from-source direction D5 extends.
- RFC-0011 — added an optional field to `[pack.install]` under an adapter-contract bump with no migration for legacy packs — the exact migration model adopted here.
- `docs/contracts/pack.schema.json` (`[pack]` has no `additionalProperties:false` → already extensible) and `plugin-manifest.schema.json` (has it → the constraint we own).

**External prior art** (each fetched and confirmed to contain the cited claim):

- **Cargo manifest** ([doc.rust-lang.org/cargo/reference/manifest.html](https://doc.rust-lang.org/cargo/reference/manifest.html)) — confirmed: `readme` is a file path (auto-detected `README.md`); `documentation`/`homepage`/`repository` are three distinct URLs; `categories` is the controlled crates.io list (max 5) vs. free-form `keywords` (max 5); `[package.metadata]` is "completely ignored by Cargo" and exists for external tools. This is the primary model (the TOML sibling).
- **npm scopes** ([docs.npmjs.com/about-scopes](https://docs.npmjs.com/about-scopes)) — confirmed: `@scope/name`, scope = user/org namespace, and "A scope allows you to create a package with the same name as a package created by another user or organization without conflict." This is the coexistence property D7 relies on.
- **Claude Code marketplace** — verified above (the spike).
- **Comparators** (consulted; not all primary-fetched, flagged where reconstructed): PyPI `summary`/`long_description`; Helm `maintainers`/`icon`; RubyGems `metadata` URIs (`changelog`/`issues`); Codex plugins (`developers.openai.com/codex/plugins` — exists; marketplace-file location is inconsistently documented, so the Codex *projector* must verify before build); Copilot CLI (mirrors Claude's schema, unknown-field handling undocumented); Artifactory virtual-repository / devpi index-inheritance (the blended-catalogue model, reserved for the follow-on RFC). Working research consolidated during drafting; load-bearing claims above are the fetched ones.

*Empty-prior-art check:* not empty — every decision is grounded in a shipping ecosystem. The one genuinely novel slugs (`architecture`, `governance`) are flagged as agent-primitive-specific with no clean third-party precedent.

## Open questions

1. **Scope ownership-verification** — if/when public third-party submission is ever opened, how is a `@catalogue` scope's ownership proven? *Recommended default: defer entirely; bind a scope to a verified GitHub org/domain at publish time when (and only if) public submission becomes a goal — no syntax change required.* · owner: eugenelim · decide-by: only when public submission is proposed.
2. **Follow-on RFC sequencing** — index contract vs. virtual catalogue vs. provenance, which first? *Recommended default: the neutral index contract first, since the other two and the deferred infra all hang off it.* · owner: eugenelim · decide-by: when the manifest spec lands.

*(Original open questions on the charter framing, the namespacing syntax, and the category list are resolved in the body under D1, D7, and D8 respectively.)*

## Follow-on artifacts

Filled in on acceptance:

- **ADR** — record the decision that `pack.toml` is the metadata source of truth with lossy per-tool projection (D2), and the `@catalogue/pack` identity (D7).
- **Spec** — `docs/specs/<enriched-pack-manifest>/` : the first-class field set (D3), README projection (D4), `plugin.json` derivation (D5), `@catalogue/pack` (D7), the soft `categories` default (D8), gated by an adapter-contract bump with the `additionalProperties:false` relaxation.
- **Follow-on RFCs** — neutral queryable index contract; virtual/blended private+upstream catalogue; provenance + scan-on-publish.
- **Architecture** — update `docs/architecture/pack-layout.md`'s `[pack]` field list (currently "name, version, description") and its contract-version mention, in the enriched-manifest spec's PR.
- **CONVENTIONS** — none anticipated; if the soft-category warning becomes a lint, note it then.
