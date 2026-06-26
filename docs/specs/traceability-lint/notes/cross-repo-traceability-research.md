# Cross-repo traceability — research synthesis

Wide prior-art research (2026-06-25) backing the cross-repo design of the
traceability lint. Four parallel evidence sweeps; the finding is that **every
mature cross-boundary traceability system converges on the same pattern**, and the
catalogue already realizes it in-repo via the value-stream layer (ADR-0022). The
lint reuses that mechanism rather than inventing one.

## The convergent pattern (across all four threads)

Across a tool / repo / org boundary you cannot resolve a file path — you carry a
**stable, location-independent identifier by convention**, and you validate link
integrity while owning **only one endpoint**:

| System | Stable node id | Version pinning | Edge record |
| --- | --- | --- | --- |
| **OSLC** | HTTP URI (concept-resource URI) | `Configuration-Context` header → version URI | RDF triple embedding the remote URI ("link by URI, don't copy") |
| **OpenLineage** | `(namespace, name)` | run UUID; dataset version facet | each producer emits its own RunEvent `inputs[]`/`outputs[]` |
| **SLSA / in-toto** | subject digest (content-addressed) | resolved digest at consumption | each step attests `resolvedDependencies` (uri + digest) |
| **SBOM (SPDX/CycloneDX)** | `purl` (`pkg:type/ns/name@version`) | version / digest in purl | typed `relationships[]` / `dependsOn[]` |
| **Backstage** | `kind:namespace/name` triplet (lowercase) | `targetRevision` / pinned ref | `providesApi`/`consumesApi`/`dependsOn`/`partOf` relations |
| **in-repo (ADR-0022)** | brief slug · `contract@version` · component | `contract@version` + read-only courier snapshot | `parent-intent:`, `Brief:`, `Component:`, rollup row |

Five transferable principles, each held by ≥3 of the systems above:

1. **Stable-id-not-path.** Identity is a namespaced id that survives a move across
   directory/repo/tool. Paths are local; ids are portable. (OSLC URI · OpenLineage
   namespace · purl · Backstage triplet.)
2. **Decentralized edge emission / federation, not central crawl.** Each producer
   declares its own edges; the graph assembles from the union. (OpenLineage events
   · SLSA per-step attestation · Backstage per-repo `catalog-info.yaml` federated
   via `Location` · in-repo per-brief `parent-intent:`.)
3. **Reference + pinned version + read-only snapshot, never fork.** (OSLC version
   URI · SLSA resolved digest · Argo `targetRevision` SHA · repo-tool `revision` ·
   ADR-0022 `contract@version` + courier snapshot.)
4. **Three endpoint states, not two.** An edge endpoint is *local*,
   *satisfied-by-reference* (a well-formed pointer, target elsewhere), or
   *unresolvable* — and unresolvable sub-classifies as broken vs unverifiable
   (OSLC's 404-vs-5xx). A cross-repo reference is **not** a dangling edge.
5. **Open-world + honest gaps.** A not-yet-present target is reported, never
   false-greened. (Backstage `spec.presence: optional` + orphan annotation;
   Roadie "honest about what it knows"; rollup `unknown / not-yet-catalogued`.)

## Structural vs semantic — the split is grounded, not asserted

- **Structural presence is mechanizable; semantic correctness is not.** SoK on
  software-artifact traceability: "A link can be structurally present but
  semantically incorrect if it connects artifacts that should not relate."
  ReqToCode: "The approach guarantees structural presence, not semantic
  correctness." Automated *semantic* trace recovery (IR: VSM/LSI; ML) reports
  precision too low for unsupervised use (the "needle-in-a-haystack" sparsity — 361
  true links among 51,700 candidate pairs in NASA CM-1). → **the lint mechanizes
  structure; semantic scope-creep stays the human call at G1.5 (RFC-0048 D6/O10).**
- **Backward orphan = scope creep.** Forward orphan (requirement with no
  implementation) vs backward orphan (artifact with no justifying requirement = the
  gold-plating / scope-creep signal). Both are first-class, distinct error classes
  in RTM practice and are *mandated* bidirectionally by ISO 26262 / DO-178C (an
  auditor walks both directions; any gap blocks certification). → **the lint's
  up-orphan = backward, down-orphan = forward; backward orphans are the scope-creep
  surface the human adjudicates.**
- **No rename/redirect → renames orphan inbound refs.** Backstage has no HTTP-301
  equivalent; OSLC suggests an `oslc:archived=TRUE` stub. → **stable-ids must not
  change after first publish (an Ask-first/governance rule); an optional
  forwarding/"moved-to" convention prevents a rename from manufacturing phantom
  orphans.** (Logged as a future refinement, not v1 scope.)

## Selected citations

**By-convention cross-boundary linking:** OSLC Core v3.0 / Config-Mgt v1.1 /
Tracked Resource Set v3.0 (oasis-open-projects.org); Eclipse Capra (artifact
wrappers + change-listener integrity). **Lineage/provenance:** OpenLineage object
model (openlineage.io); SLSA build provenance + in-toto attestation framework
(slsa.dev, github.com/in-toto/attestation); SPDX 3.0 / CycloneDX; Package URL
ECMA-427. **Polyrepo/catalog:** Backstage software-catalog descriptor + references
+ life-of-an-entity (backstage.io); Google `repo` manifest.xml; Argo CD
app-of-apps; `RoadieHQ/backstage-entity-validator` (+ Backstage #16284, the
no-CI-reference-validation gap). **Software-traceability research:** Gotel &
Finkelstein 1994; Cleland-Huang "Grand Challenges of Traceability" (arXiv:1710.03129);
SoK traceability (arXiv:2603.16208); ReqToCode (arXiv:2603.13999); traceability
decay / TRAIL (arXiv:1807.06684); NLP-for-traceability survey (arXiv:2405.10845);
Mader et al. "Requirements Traceability across Organizational Boundaries" (REFSQ
2013). **In-repo mechanism:** ADR-0022; `align-value-stream` SKILL + references
(`shared-contract-handoff.md`, `cross-component-rollup.md`, `backstage-ontology.md`)
+ `assets/rollup-template.md`; `decompose-intent` business-unit slicing branch;
`packs/core/seeds/docs/product/briefs/_template.md` (`parent-intent:` field).

## Open questions surfaced (not resolved here)

- **Full federated multi-root crawl** vs **per-repo + reference-resolution**: v1
  takes the latter (run per repo, resolve cross-repo references via the rollup /
  sidecar / present snapshot); a multi-root crawler is a later posture.
- **Snapshot-at-reference vs current-HEAD** for living docs (RFCs/specs evolve):
  v1 follows the value-stream courier-snapshot posture (referenced-at, pinned),
  consistent with SLSA's "what was actually consumed."
