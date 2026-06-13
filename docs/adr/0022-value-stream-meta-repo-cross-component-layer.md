# ADR-0022: The business-unit cross-component layer — a value-stream meta-repo, per-component brief slicing with `parent-intent` provenance, and a referenced (never forked) shared contract

- **Status:** Accepted <!-- Proposed | Accepted | Deprecated | Superseded by ADR-NNNN -->
- **Date:** 2026-06-13
- **Deciders:** eugenelim
- **Supersedes:** none
- **Related:** RFC-0030 (the product-engineering pack — decision #9 + Appendix A, which accepted this layer) · ADR-0019 (the v1 `intent` ontology / brief-as-projection / contract-maturity, which deferred these decisions to phase 2) · ADR-0008 + RFC-0017 + RFC-0018 (the contract-authoring seam this reuses) · RFC-0020 (`reference.md` golden-path — the `architect` seam) · RFC-0016 (the doc-drift discipline this layer's currency relies on) · RFC-0019 + ADR-0009 (`receive-brief` and its per-repo coverage rollup, which this aggregates above)

## Context

RFC-0030 (Accepted 2026-06-13) accepted, as decision #9 and Appendix A, a **business-unit, cross-component value-stream layer** for the `product-engineering` pack, and shipped v1 (app-scale, single-component) while deferring this layer to phase 2. ADR-0019 recorded the v1 decisions and explicitly left three things open "to revisit": the BU-scale meta-repo, the canonical home for a cross-repo shared contract, and the `parent-intent:` brief field. This ADR records those phase-2 decisions; the spec (`docs/specs/value-stream-meta-repo/`) and the implementation follow.

Several forces constrain the design:

- **The repo boundary is the spec-context boundary** (carried from ADR-0019). An implementable spec needs its target component repo's full context, so a cross-component feature *cannot* be specced upstream — it is sliced per component, and each slice is completed into specs *inside* the owning repo.
- **Polyrepo has no shared tree.** A monorepo solves contract-sharing in-tree (one interface library, atomic "change the contract and all consumers in one PR"); a polyrepo has nowhere for the cross-cutting artifacts — the catalog, the canonical contracts, the cross-component rollup, the system architecture — to live. That absence is what a coordinating repo fills.
- **Drift is the dominant failure mode.** Appendix A names it directly: agents follow a stale catalog or contract confidently. Currency must be a first-class, enforced discipline (the RFC-0016 doc-drift philosophy), not a nice-to-have.
- **The charter caps the shape.** Habits, not infrastructure: no engine, no hooks, no validators, no new subagents (the 3-reviewer ceiling), no runtime hub, no live tracker/coverage API. Pure-markdown skills + references + seeds.
- **It must compose, not duplicate.** Reuse Backstage's ontology, the existing `Contract:` seam, `receive-brief`'s per-repo coverage rollup, and `monorepo-extras` for structuring — extend them, don't fork them.

## Decision

**The cross-component layer is a value-stream meta-repo — a coordinating *repo*, not a service — that holds the artifacts no single component repo can own; a feature intent is sliced per component into one brief per repo carrying a `parent-intent:` provenance pointer; and the cross-repo shared contract is referenced by version (with a read-only courier snapshot), never forked.**

Six parts:

1. **The value-stream meta-repo.** At `business-unit` Scale, a coordinating repo with **no application code** sits above many component repos, anchored to Backstage's **Domain → System → Component → API** ontology. It holds: the cross-component (capability) intents, the **federated catalog** (it references each component repo's own `catalog-info.yaml` rather than re-authoring it), the **canonical shared contracts** (or a reference to wherever they live — part 3), the **C4 / bounded-context system architecture** (part 5), and the **cross-component delivery rollup** (part 4). It is a *place you read and edit*, never a running service that polls component repos. A new skill, **`align-value-stream`**, owns standing it up and keeping it current; the spine of that skill is currency.

2. **Per-component brief slicing with `parent-intent:` provenance.** At BU scale, `decompose-intent` gains a slicing branch: a de-risked feature intent is cut into **one brief per affected component**, and each brief crosses into its component repo carrying an optional **`parent-intent:`** back-pointer to the capability/feature intent it was projected from. This adds an optional `parent-intent:` field to **`core`'s** brief template — additive and backward-compatible, mirroring the existing `Epic:` pointer but a **distinct role** (`Epic:` names an external cross-repo *coordinator*; `parent-intent:` names the product-pack *intent* the slice was projected from). `receive-brief` never interprets it; `core` still imports nothing from the pack and stands alone. This is the field ADR-0019 corollary 2 named as "the only ever-needed addition" and deferred to here.

3. **The shared contract is referenced, never forked.** Authority lives in **one shared, version-pinned home**; each per-component brief **references `contract@version`** and attaches a **read-only courier snapshot** for provenance — never attach-as-authority (that forks the contract N ways). The default is **provider-contract-first** (defining a surface for not-yet-built components enables parallel development), with a **per-relationship override** to consumer-driven contracts where one provider serves known collaborating consumers. Provider/consumer roles are expressed by **mirroring Backstage's `providesApi`/`consumesApi`** relations (source fields `spec.providesApis`/`spec.consumesApis`) rather than novel frontmatter, and each relationship carries a **compatibility/upgrade direction** (who upgrades first). The **authority *location*** — the meta-repo, a dedicated contracts/interface repo, or a schema registry — is **org-specific and elicited at use time** (default: the meta-repo); the **reference-by-version + courier-snapshot *shape*** is the constant regardless of location. (This resolves RFC-0030 open question #2, whose *decide-by* clause named a "phase-2 RFC"; phase 2 ships by spec + this ADR rather than a new RFC because the layer was already accepted in RFC-0030 — recorded as an approver-signed erratum in RFC-0030 § Errata, 2026-06-13.)

4. **The cross-component rollup is a markdown snapshot, with no runtime hub.** `receive-brief`'s per-repo coverage answers "is *this* repo's slice shipped?"; the meta-repo holds the **whole-feature rollup** answering "is the feature delivered **across all** components?" — an aggregation above any single repo. It is a **markdown table** (one row per component slice → its brief → a status snapshot **+ a pointer** to that repo's own auto-derived coverage); the AND across rows is the answer. The row references the component repo's authoritative coverage and caches a snapshot — mirroring the contract pattern (reference the authority, cache a snapshot, never fork it). It is a **snapshot, not a live feed**: a live rollup would require the meta-repo to reach into N repos (auth, polling, rate limits) — a running service, which is deferred to a later live-integration pack and out of charter. Markdown (not YAML) because nothing machine-consumes it in scope, it matches the markdown coverage map it aggregates, and a schema'd YAML file would invite a validator script (infrastructure the charter forbids). Currency is the enforced discipline that keeps the snapshot honest.

5. **The architect seam: `reference.md` lives in the meta-repo.** At BU scale the C4 / bounded-context system architecture (the home `RFC-0020`'s `docs/architecture/reference.md` already implies) lives in the **meta-repo**; each component repo's own `reference.md` **links to / conforms to** it rather than re-deriving the system view. Same audience, same artifacts — this is the `architect` seam.

6. **Contract maturity and the `monorepo-extras` seam are unchanged.** Maturity stays staged exactly as v1: behavioral @intent → interaction (CDC-shaped) @brief → **detailed wire contract @spec** (the existing ADR-0008 / RFC-0017/0018 `Contract:` seam at `new-spec` step 4b) → verify @build. This layer adds **no new contract machinery** and stays behavioral. The monorepo-vs-polyrepo **structuring** decision stays in `monorepo-extras` (`new-package`); the two packs meet **only** at "where the shared contract lives" (in-tree for a monorepo; in the meta/contracts repo for a polyrepo).

## Consequences

**Positive:**
- One model still spans solo→BU: the standing value-stream plane is the only addition, and the per-feature loop (`frame-intent` → `de-risk-intent` → `decompose-intent`) is unchanged but for `decompose-intent`'s slicing branch.
- Composes cleanly: the leaf is still a `core` brief; the rollup aggregates `receive-brief`'s existing per-repo coverage; the wire contract reuses the existing seam; the catalog and provider/consumer roles reuse Backstage; structuring stays in `monorepo-extras`. No duplication, no new infrastructure.
- Reference-by-version + courier snapshot gives provenance without forking the contract; provider-contract-first enables parallel development across not-yet-built components.
- `core` stays standalone — the only `core` change is one additive, never-interpreted optional brief field.
- Currency is treated as the first-class discipline the dominant failure mode demands.

**Negative:**
- The layer introduces a coordination pattern with **real hard limits an adopter must accept**: **no atomic cross-repo commit** and **no shared release train** (polyrepo's inherent cost). These are stated honestly, not engineered away.
- The rollup is a **hand-maintained snapshot** — it can drift if a slice ships and its row isn't flipped. Mitigated (not eliminated) by pointing each row at the component repo's *auto-derived* coverage, so only the cached snapshot can go stale, and by the RFC-0016 currency discipline.
- The meta-repo adds a standing artifact a BU must maintain; its value collapses if it is allowed to go stale.

**Neutral / to revisit:**
- The contract-authority **location** is intentionally left org-specific (elicited per value stream); only the reference + courier shape is fixed.
- **Live** tracker/coverage API integration remains deferred to a separate, later pack; this layer ships the one-way mapping and the snapshot discipline only.

## Alternatives considered

- **Leave the cross-cutting artifacts in each component repo.** Rejected: no repo owns the catalog, the canonical contract, or the whole-feature rollup — they are cross-cutting by definition, so they have no home and silently rot.
- **Force a monorepo.** Rejected: a monorepo *does* solve contract-sharing in-tree, but at the cost of one tree and one release train — that structuring decision belongs to `monorepo-extras`, and a BU running polyrepos can't adopt it. The two packs meet only at "where the shared contract lives."
- **An external coordination SaaS / a running hub service.** Rejected: out of charter (runtime infrastructure), and it makes the catalog/contracts a service to operate rather than a habit to keep current.
- **A live rollup that polls component repos.** Rejected for v-this-phase: auth, rate limits, idempotency, and conflict rules make it infrastructure, not a habit; deferred to the later live-integration pack. The snapshot + pointer is the in-charter answer.
- **Attach the contract to each brief as authority (copy it in).** Rejected: forks the contract N ways and drift is immediate. Reference by version; carry only a read-only courier snapshot.
- **A YAML (schema'd) rollup.** Rejected: nothing machine-consumes it in scope, it mismatches the markdown coverage map it aggregates, and it invites a validator script — infrastructure the charter forbids. The catalog stays YAML only because Backstage (a real external tool) mandates `catalog-info.yaml`.
- **Novel provider/consumer frontmatter.** Rejected: Backstage's `providesApi`/`consumesApi` is a recognized formalization; inventing parallel fields adds jargon for nothing.

## References

- RFC-0030 — the accepted proposal; decision #9 and Appendix A (§A.1–A.7) carry the phase-2 research this records.
- ADR-0019 — the v1 decisions and the three deferrals this resolves.
- ADR-0008, RFC-0017, RFC-0018 — the contract-authoring seam reused at the spec stage.
- RFC-0020 — `docs/architecture/reference.md` as the golden-path anchor; the meta-repo's architecture home.
- RFC-0016 — the doc-drift discipline the meta-repo's currency relies on.
- RFC-0019, ADR-0009 — `receive-brief` and its per-repo coverage rollup, aggregated above by the cross-component rollup.
- External anchors (per RFC-0030, author-verified): Backstage Domain→System→Component→API and `providesApi`/`consumesApi`; design-first / contract-first; Team Topologies (one coordinating repo per value stream).

## Errata

- **2026-06-13 (enriched-pack-manifest; Approver: eugenelim).** The Decision's
  shape line read "Pure-markdown skills + references + **seeds**." The
  cross-component rollup template shipped as a repo `seeds/` seed, but a pack
  with a non-empty `seeds/` cannot be user-scope (RFC-0004 Rail A), which broke
  `product-engineering`'s `agentbundle validate`. The rollup template now ships
  as the `align-value-stream` skill's `assets/rollup-template.md` (copied into
  `docs/product/rollups/<slug>.md` at runtime) and is no longer a seed; read
  "skills + references + skill-asset templates." No infrastructure is added —
  the no-engine/no-hooks/no-validator caps are unchanged. See RFC-0030 Errata.
