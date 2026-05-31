# RFC-0017: Pluggable API-contract standards + a spec-driven contract seam

- **Status:** Accepted <!-- Draft | Open | Final Comment Period | Accepted | Rejected | Withdrawn | Experimental (optional: trial running, results pending — see the Experiment / validation section) -->
- **Author:** eugenelim
- **Approver:** eugenelim
- **Date opened:** 2026-05-30
- **Date closed:** 2026-05-30
- **Related:** RFC-0001 (bundle distribution / pack model), RFC-0004 (install-scope per pack), RFC-0007 (first user-scope pack), `packs/contracts/`, `new-spec` skill, `adapt-to-project` skill

## The ask

- **Recommendation (BLUF):** Turn `api-contract` from a Zalando-hardcoded skill into a **standard-driven engine** — the skill carries the API-design *method*, the ruleset is swappable *data* with Zalando as the bundled starter. Author contracts into a **repo-level `contracts/<type>/` tree** (single source of truth, many specs can modify one over time), wired in via a **contract-type-agnostic seam** in `new-spec` (`core`). Discovery is **convention-first**: the location convention is the anchor; a roster name-lookup only selects the authoring skill and degrades to direct file-edit when absent. Ship OpenAPI/REST first; keep the door open for event/other contract types. One RFC, staged: pluggability lands first, the seam second.

- **Why now (SCQA):** *Situation* — `contracts/api-contract` produces a validated OpenAPI 3.1 spec, and `new-spec` produces `spec.md` + `plan.md`. *Complication* — (a) the skill hardcodes one org's rules (Zalando's 138), useless for a consultancy crossing many orgs each with their own API guidelines; (b) the two skills are decoupled islands, so the spec→OpenAPI→plan chain only fires if a developer remembers to string it by hand; and (c) there is no home or lifecycle for the contract artifact — nowhere it lives across specs, no traceability, no update story. *Question* — how do we make org standards pluggable, give contracts a durable home with spec traceability, and wire authoring into the spec loop, without breaking the "compose around `core`, packs don't import each other" model?

- **Decisions requested:**
  1. **Contract authoring stays a separate pack; `core` integrates via an agnostic seam, not by absorbing `contracts`.** Why: folding `contracts` into `core` breaks three invariants (below). Default: keep separate.
  2. **Org standards are expressed as base + delta (`extends` + override/add), not full rewrite.** Why: Spectral, the dominant OpenAPI style-guide tool, proves the model; full-rewrite kills adoption. Default: base+delta.
  3. **The org's standard is delivered by `adapt-to-project`'s `.upstream` companion-merge (Class 2)** (install-time), not a new runtime resolver. Why: reuse over invent. Default: companion-merge.
  4. **v1 covers OpenAPI/REST only; a standalone event/other contract type is deferred** to a named follow-on. Why: CloudEvents is an envelope, not a peer type; AsyncAPI is the real event peer; neither is needed to prove the engine. Default: OpenAPI-only.
  5. **The `new-spec` seam is conditional, auto-detected, and degrades gracefully** — authors the contract into the `contracts/<type>/` tree (D8), links it from the spec header, points plan tests at it. Default: include.
  6. **One RFC, staged implementation** — pluggability (contracts-internal) first, seam (core + template) second. Default: one RFC.
  7. **Discovery is two-layer and convention-first** — artifact discovery by *location convention* (`contracts/<type>/`, the durable anchor); capability discovery by *name derived from the contract type* + roster presence check, degrading to direct file-edit when no authoring skill is installed. Why: the location convention, not a cross-pack name, carries the integration. Default: convention-first.
  8. **Contracts live in a repo-level `contracts/<type>/` tree** (`openapi`, `asyncapi`, `proto`, `graphql`, `jsonschema`, `jsonrpc`, `mcp`), not in the spec folder; a new top-level directory this RFC authorizes, and an `adapt-to-project` Class 3 relocation target for adopters whose contracts already live elsewhere. Default: repo-level tree.
  9. **Contracts are long-lived; subsequent specs may modify them, with bidirectional spec traceability and compatibility-gated updates.** Default: long-lived + traceable.

## Problem & goals

**Diagnosis.** One root cause — the contract capability was built as a standalone Zalando tool rather than as a composable, configurable, *persistent* part of the spec-driven loop — with three symptoms.

1. **The ruleset is hardcoded.** `api-contract/SKILL.md` weaves Zalando's `[#NNN]` rules into its phase prose and inlines the MUST/MUST-NOT quality gates. (The skill applies 138 of Zalando's 143 rules; 5 Zalando-internal rules are excluded.) An org with its own API guidelines (every large org has them) has no seam to plug them in short of forking the skill.
2. **The chain is opt-in-by-memory.** `new-spec` authors `spec.md` and `plan.md` as a pair with no gap to author a contract between them, and `api-contract` takes generic "user stories" as input and emits YAML "in the conversation" with no canonical home. So spec→OpenAPI→plan only happens if a human strings it manually.
3. **The contract has no home or lifecycle.** Even when authored, there is no durable location for it, no convention for which specs own or modify it, and no traceability — so a contract can't be a shared artifact that survives and evolves across features.

**Goals.**

- An org can supply its own API standard and have `api-contract` apply it, starting from a published base and overriding/adding a handful of rules — without forking the skill.
- The Zalando ruleset becomes a *replaceable starter standard*, not the only standard.
- Contracts live in a **repo-level, single-source-of-truth tree**, organized by contract type, that **multiple specs can create and modify over time**, with **bidirectional traceability** between a contract and the specs that define or touch it.
- For features with an API surface, `new-spec` authors (or delegates authoring of) the contract into that tree, links it from the spec, and points the plan's construction tests at it.
- Updating an existing API is a first-class flow: a later spec modifies the existing contract through the authoring skill, so the standard's **compatibility rules** apply and breaking changes are caught.
- `core` gains none of this as a hard dependency: with no contract pack installed, the contract still lands in its conventional location (hand-authored) and `new-spec` degrades with a note.

**Non-goals.**

- **Moving `contracts` into `core`** (could have been the integration story — explicitly rejected; see Decision 1 / Options).
- **A new event-driven contract *type* in v1** — a standalone AsyncAPI/CloudEvents contract type is deferred (Decision 4), though both the seam and the `contracts/<type>/` tree are designed not to preclude it. (Zalando's inline event rules still ship inside the OpenAPI bundle.)
- **A separate contracts *repository*** — a real prior-art option (Axis E), rejected because it breaks the in-repo spec↔contract drift gate.
- **Code generation from contracts** — codegen/mock/SDK output is downstream tooling, out of scope here.
- **A runtime multi-standard resolver** — picking among several standards per-invocation is a deferred post-v1 trigger (Open question 1), not v1.
- **Authoring the standards themselves** — this RFC ships the *mechanism* and the Zalando starter; it does not write Google-AIP or Microsoft-REST standard bundles.
- **Replacing SAST/lint tooling** — the quality gates guide authoring; they are not a substitute for Spectral/CI validation of the emitted spec.

## Proposal

### D1 — Separate pack, agnostic seam (not a merge into core)

`api-contract` stays in `packs/contracts` (user-scope default, repo-scope allowed). `core`'s `new-spec` gains a seam anchored on the location convention (D8) and the contract type, resolving an authoring skill at runtime (D7). `core` imports no code from `contracts`.

Moving `contracts` into `core` is rejected because it breaks three documented invariants (`docs/architecture/overview.md`):
- *"compose around `core`, not subclass… they don't import code from each other"* — a core→contracts code path would be the first violation.
- `core` is **repo-only**; `contracts` is **user-scope default**. Folding in forces contracts to repo-only and kills the cross-engagement portability it was built for.
- `core` is the always-installed agnostic base; shipping OpenAPI in it imposes REST on every adopter — libraries, CLIs, data pipelines included.

### D2 — Standard = method (skill) + data (ruleset), base + delta

Split `api-contract/SKILL.md` into:
- **Method** (stays in the skill): the phase procedure — model the domain → URLs/methods → representations → errors → security → compatibility → quality gates → emit OpenAPI. Standard-agnostic.
- **Standard** (becomes swappable data): a bundle of
  - a **manifest** — `name`, `version`, attribution/license, and a `base` it `extends` plus `overrides` / `adds`;
  - **rule files** grouped by the method's phase categories (naming, URLs, methods/status, representations, errors, security, compatibility);
  - a **machine-checkable quality-gate checklist** — the MUST/MUST-NOT items the skill verifies before finalizing.

Zalando ships as the **bundled base standard** (`extends: zalando`). An org authors a delta — override or disable inherited rules, add house rules — exactly the Spectral `extends: spectral:oas` + `rules: { … : false }` shape. Per-standard attribution/license is preserved in the manifest (Zalando is CC-BY-4.0 — a legal requirement, not a style choice; every plugged-in standard carries its own).

### D3 — Delivery by `adapt-to-project`'s `.upstream` companion-merge

The org's standard is installed by **Class 2 companion merge** — the `.upstream.<ext>` overlay-and-reconcile mechanism `adapt-to-project` already provides (`adapt-to-project/SKILL.md` § "Class 2 — `.upstream.<ext>` companion merges"). When the org's standard differs from the bundled Zalando seed, install drops a `.upstream` companion; `adapt` proposes a merge and writes the result in the same scope the companion was found — the skill operates at either scope, repo or user. No new runtime resolver. Scope follows the pack's existing `allowed-scopes`: single-org → user-scope merge once; consultancy/per-engagement → repo-scope, adapt per client workspace.

(Not Class 1 — marker substitution is repo-only per RFC-0004 and operates on declared placeholder values, not file-level rulesets, so it cannot deliver a user-scope standard.)

### D4 — OpenAPI/REST in v1; other types deferred but not precluded

v1 authors OpenAPI 3.1 only — no new **contract type**. (Zalando's own event rules, #194–#247, already ship *inside* the OpenAPI bundle and continue to as today; what v1 defers is a separate AsyncAPI/CloudEvents *contract type*, not those inline rules.) The seam (D5) and the `contracts/<type>/` tree (D8) are contract-*type*-agnostic, so a future AsyncAPI, proto, GraphQL, JSON-Schema, JSON-RPC, or MCP standard plugs in as another type **without re-touching `core`**. CloudEvents is an envelope convention *inside* a future event standard, not a standalone type; it rides that follow-on.

### D5 — The `new-spec` seam

Insert a conditional step between `new-spec`'s spec-body step and its plan step:

- **Detect** whether the feature exposes an interface surface and of which type (auto-detected from the interface ACs, confirmed with the user — not a flag).
- **Locate or create** the contract at its conventional path (D8) — a new contract for a new API, or the existing file when the spec modifies a known API (D9).
- **If an authoring skill for the type is available** (D7): invoke it to author/modify the contract; **else** fall back to a direct file-edit and note the absence. (For v1's OpenAPI YAML the agent can hand-author a serviceable file without rule-enforcement; for formats the agent can't reliably author unaided — e.g. proto/graphql in a later type — the fallback is "stub + note," not a full contract.) Either way the contract path is reserved in the conventional location — the seam never blocks.
- **Link** it from the spec header via a `Contract:` field (alongside `Plan:` / `Constrained by:`); the plan's Construction-tests section references the contract as the artifact under test.
- **If not an API feature:** the existing spec→plan path runs untouched.

The `Contract:` header is a **spec-template edit** to `packs/core/.apm/skills/new-spec/assets/spec.md` — RFC-gated, and this RFC is the gate.

### D6 — One RFC, staged implementation

This RFC carries both halves; implementation stages them (pluggability first, seam + folder/traceability conventions second) as two specs — see Follow-on artifacts. The split into two separate RFCs stays available if review prefers it.

### D7 — Discovery: convention-first, two-layer

The user's question — *must the integration skill be found by name-lookup, or can it ride a location convention?* — resolves into two separable concerns:

- **Artifact discovery — by location convention (the anchor).** Contracts always live at `contracts/<type>/…` (D8). Any spec, skill, or agent finds them by globbing that path — no lookup, no installed skill required. This is the durable, adapter-agnostic contract; it carries the integration.
- **Capability discovery — by name derived from type, confirmed by roster.** To *author/validate* against a standard, the seam derives the expected authoring-skill capability from the contract type (e.g. type `openapi` → capability `api-contract`) and checks the agent's available-skills roster — the same roster the harness already injects and that `new-spec` step 6 uses to find reviewer agents. If present, invoke it; if absent, edit the file directly and note it.

So name-lookup is **not load-bearing**: a missing contract skill degrades authoring quality (no rule-enforcement) but does not break the integration — the contract still exists in its conventional place, linked and traceable. This is strictly better than the earlier roster-only design, because it removes the "first cross-pack name reference from `core`" from the critical path (it becomes an enhancement, not a dependency).

**Where the expectation is recorded — and why not a manifest.** The type→skill-name map lives **consumer-side, in `core`'s seam** (the only thing `core` can always read). It must *not* live in `contracts`' `pack.toml`: `contracts` is user-scope by default, so a repo-scope `core` has no visibility into its manifest — and an adopter may bring their own authoring skill as a bare `SKILL.md` with no pack or `.toml` at all. The **runtime roster is the one surface visible regardless of install scope or pack origin**, which is exactly why the match key is the *skill name in the roster*, not a manifest file. A user-scope `contracts` skill and a hand-dropped BYO skill both appear in the roster by name and both match. Detection of a rename or absence is therefore a **runtime note** at the moment of authoring ("expected `api-contract` for type `openapi` not found — authored without rule-enforcement"), not a build-time lint, because nothing `core` can read at build time sees a user-scope or BYO skill.

The map is an **explicit table, not a naming algorithm** — so it absorbs the legacy name `api-contract` (which authors OpenAPI) without forcing a rename, and lets a BYO skill be wired in by adding one row (`graphql → my-graphql-contract`), a repo-scope edit needing no pack. Its home and format: a **plain markdown table in the seam's reference file**. A structured format (TOML/YAML) would only be warranted if a *program* parsed the map, and none does — the seam is executed by the agent reading the SKILL.md instruction, and detection is a runtime note (agent behavior), not a lint.

### D8 — Repo-level `contracts/<type>/` tree + naming convention

Contracts live at the **adopter repo root**, grouped by contract type — *not* in `docs/specs/<feature>/`:

```
contracts/
  openapi/      # REST — .yaml
  asyncapi/     # event-driven APIs — the AsyncAPI doc + standalone event-payload schemas
  proto/        # gRPC / protobuf — .proto, buf-style versioned package dirs
  graphql/      # GraphQL SDL — .graphql / .graphqls
  jsonschema/   # standalone JSON Schema — .json
  jsonrpc/      # JSON-RPC service descriptors
  mcp/          # Model Context Protocol tool/resource schemas
```

**Naming.** One contract per logical API/service/domain, kebab-case by domain: `contracts/openapi/orders.yaml`, `contracts/asyncapi/order-events.yaml`. Proto follows buf's convention — versioned package directories (`contracts/proto/payments/v1/payments.proto`) and `lower_snake_case.proto` filenames. **Versioning:** minor/patch tracked in-contract (`info.version`) plus git history; a breaking **major** that must be served alongside the old one gets a parallel file/dir (`orders.v2.yaml`, `.../v2/`), per Zalando's no-breaking-change rule and buf's versioned dirs.

**Event-type folder contents (forward documentation — no AsyncAPI skill ships in this RFC).** `contracts/asyncapi/` is intended to hold *both* the AsyncAPI descriptor *and* the standalone event-payload schemas it references, so the schemas are consumable independently of AsyncAPI:

```
contracts/asyncapi/
  order-events.yaml          # the AsyncAPI document (channels / operations / messages)
  schemas/                   # standalone event-payload schemas (JSON Schema / Avro)
    order-created.json       #   ← usable directly by orgs that don't adopt AsyncAPI
    order-cancelled.json
```

An org that skips AsyncAPI still gets first-class event contracts by consuming `schemas/*` directly; an org that adopts it gets the descriptor wiring those schemas into channels. (These co-located event schemas are distinct from `contracts/jsonschema/`, which is for standalone domain schemas not tied to an event API.) This documents the folder's shape for when the event contract type lands (D4); it ships no authoring skill now.

This is a **new top-level directory**, which `AGENTS.md` requires be proposed via RFC — this RFC is that proposal. *Naming note:* the word "contracts" now names three distinct surfaces — the `contracts` *pack* (authoring skills), `docs/contracts/` (this repo's adapter/JSON schemas, per `docs/architecture/overview.md`), and the proposed repo-root `contracts/` (authored API artifacts). They are different layers and do not collide: adopter repos have no `packs/`, and the API tree is unambiguously **repo-root `contracts/`**, distinct from `docs/contracts/`. The distinction matters under self-host (`make build-self`), where all three coexist in this repo.

**`adapt-to-project` Class 3 is the relocation path.** Many adopters already keep contracts somewhere non-canonical — `api/openapi.yaml`, a root `swagger.json`, a top-level `proto/`, `schemas/`. The `contracts/<type>/` layout becomes a **Class 3 (discovery + restructuring) target** (`adapt-to-project/SKILL.md` § "Class 3 — Discovery + restructuring"): on adapt, the skill walks the adopter tree, flags contracts in non-canonical locations, and proposes relocating each into `contracts/<type>/` — per-finding accept / edit / decline, recorded at repo scope (contracts are repo artifacts, so no cross-scope move). This is the same mechanism that today moves a stray `DESIGN.md` into `docs/CHARTER.md`. So `adapt-to-project` serves this RFC twice: **Class 2** delivers the standard ruleset (D3), **Class 3** canonicalizes the contract *location*. Rewriting an adopter's downstream path references (codegen configs, CI globs) is **out of scope** — adapt proposes the move and flags it; the adopter owns their tooling paths.

*Anti-pattern reconciliation (required).* `adapt-to-project`'s register today says **"Never add a new top-level directory or a new package"** — and a Class 3 relocation into `contracts/` does add one. The reconciliation is narrow: this RFC *authorizes* the single `contracts/` root (the RFC process is exactly how `AGENTS.md` says new top-level directories get blessed), so the seam-stage spec must **amend that anti-pattern to carve out the RFC-authorized `contracts/` root specifically** — not relax it into a general license for adapt to invent directories. Absent that amendment, Class 3 must not create `contracts/`; it would relocate only into an already-present tree. The amendment is listed in Follow-on artifacts.

### D9 — Contract lifecycle: updates to existing APIs + traceability

A contract is a **long-lived artifact**. Its first spec creates it; later specs modify it. The spec↔contract relation is therefore **many-to-one over time**, which demands traceability and an update discipline:

- **Forward traceability (spec → contract):** the spec header `Contract:` field names the contract file(s) the spec defines or touches (one spec may list several).
- **Backward traceability (contract → spec):** the contract carries a machine-readable pointer to its defining/modifying specs via an **`x-spec` extension** where the format supports vendor extensions (OpenAPI/AsyncAPI: `x-spec: [docs/specs/orders/, docs/specs/order-cancel/]`), with a top-level **`contracts/REGISTRY.md`** map as the fallback for extensionless formats (proto/graphql). Unlike the capability name (D7), *both* sides of this link are repo-scope artifacts — spec and contract live in the same repo — so forward/backward agreement **is** checkable by an in-repo lint at Stage 2 (modeled on RFC-0016's doc-drift gate), which keeps `REGISTRY.md` from silently rotting.
- **Updates run through the authoring skill** so the active standard's **compatibility rules** apply (Zalando #106–108, #111, #114–115: no breaking changes to published fields, compatible-extension and tolerant-reader rules, media-type versioning). A change the rules classify as breaking is surfaced and routed to a new major (D8 versioning), not silently applied.
- **Drift discipline:** contract ↔ spec Acceptance Criteria ↔ implementation must agree; changing one without the others is a bug — the same rule the repo already applies to spec/code drift. The plan's contract tests verify the implementation against the contract.

### Migration path

- The existing Zalando references in `api-contract` become the bundled Zalando standard bundle; the SKILL.md body is rewritten to cite "the active standard" instead of literal `[#NNN]`. Existing direct invocations keep working (Zalando is the default base).
- The `contracts/` tree is greenfield in this catalogue repo. Adopters who already keep contracts elsewhere are migrated by `adapt-to-project` Class 3 (D8) — opt-in, per-finding relocation; those starting fresh just author their first contract into the tree.
- No adopter action required for the standard unless they want a custom one, in which case the `adapt` flow installs it.

## Options considered

**Axis A — how `core` integrates contract authoring** (exhaustive over dependency direction):

| Option | Trade-off | |
| --- | --- | --- |
| Merge `contracts` into `core` | Discoverable, but breaks 3 invariants (repo-only scope, no cross-pack imports, agnostic base) | ✗ |
| **Separate pack + agnostic seam, convention-first discovery** | Same discoverability; preserves the pack model; convention-coupling not import-coupling | ★ |
| Do nothing (manual chaining) | Zero cost now; leaves the drift defect and the hardcoded-ruleset defect unfixed | ✗ |

**Axis B — how an org expresses its standard** (exhaustive over authoring burden): full hardcode (status quo) / **base + delta** ★ / full-replacement-only. Base+delta is grounded in Spectral's `extends` + override model; full-replacement is rejected because no org rewrites ~140 inherited rules.

**Axis C — standard delivery mechanism** (exhaustive over bind time): **install-time companion-merge** ★ (reuses `adapt-to-project` Class 2) / runtime resolution (deferred post-v1 trigger, Open Q1) / both. Install-time wins on reuse and is final for v1.

**Axis D — contract-type coverage in v1** (exhaustive over sync/async/envelope): **OpenAPI/REST only** ★ / + AsyncAPI / + CloudEvents. Deferring events is grounded in the AsyncAPI-vs-CloudEvents taxonomy — CloudEvents is an envelope, not a contract type.

**Axis E — where contract artifacts live** (exhaustive over locality): in the spec folder (`docs/specs/<feature>/`) / **repo-level `contracts/<type>/` tree** ★ / a separate contracts repository. In-spec-folder ties a contract to one feature and blocks the many-specs-modify-one-contract goal; a separate repo maximises decoupling but breaks the in-repo spec↔contract drift gate and burdens adopters. The repo-level tree matches monorepo single-source-of-truth practice and buf's top-level versioned proto tree.

**Axis F — capability discovery** (exhaustive over signal source): pure name-lookup (roster-only) / pure location-convention (no authoring skill) / **convention-first hybrid** ★ (location anchors, type-derived name + roster presence selects the skill, degrades to direct edit). Roster-only makes a cross-pack name load-bearing; convention-only loses standard-enforcement; the hybrid keeps the integration robust and the enforcement opportunistic.

Do-nothing is modelled in Axis A and rejected: the cost of delay is continued spec/contract drift, no contract home/lifecycle, and a contract capability unusable outside Zalando shops.

## Risks & what would make this wrong

**Pre-mortem.**
- *The ruleset won't cleanly extract from the prose.* Mitigation: the `references/*.md` are already file-separated; the spike (below) confirms the residual work is mechanical.
- *Many-to-one spec↔contract drift* — a contract drifts from the specs that claim it. Mitigation: bidirectional traceability (D9) + contract tests in the plan + the existing drift-is-a-bug discipline.
- *The new `contracts/` top-level directory collides or confuses* — "contracts" now names three surfaces (the `contracts` pack, `docs/contracts/` adapter schemas, root `contracts/` API artifacts), most acutely under self-host where all three coexist. Mitigation: different layers, distinct paths (API tree is repo-root `contracts/`, not `docs/contracts/`); documented in D8.
- *The Class 3 relocation violates `adapt-to-project`'s "never add a top-level directory" rule.* Mitigation: the seam-stage spec amends that anti-pattern with a narrow carve-out for the RFC-authorized `contracts/` root (D8); absent the amendment, Class 3 relocates only into an existing tree.
- *Class 3 relocation breaks downstream path references* — moving an adopter's `api/openapi.yaml` into `contracts/openapi/` orphans codegen configs and CI globs pointing at the old path. Mitigation: relocation is opt-in per-finding (accept/edit/decline) and flagged; rewriting tooling paths is explicitly out of scope (D8) — the adopter owns that.
- *Capability misfire* — wrong/absent authoring skill for a type. Mitigation: convention-first (D7) means the contract still lands in place; a missing skill costs enforcement, not the integration.
- *Base+delta tempts standard sprawl.* Mitigation: the manifest's `extends` makes lineage auditable.

**Key assumptions (falsifiable).**
- The agent can reliably read its skill roster at runtime. *(Wrong if the harness stops surfacing it — but that breaks the existing step-6 reviewer discovery too. And with convention-first, this only degrades enforcement, not the integration.)*
- A repo-level tree is the right locality — adopters want contracts shared, not per-feature. *(Wrong → Axis E's in-spec-folder option returns.)*
- Orgs want one standard per repo/engagement, not several concurrently. *(Wrong → Open Q1's runtime resolver becomes load-bearing.)*
- The Zalando method generalises across org standards. *(Wrong if a standard needs phases Zalando's method lacks — e.g. RPC-shaped APIs.)*

**Drawbacks.** A new top-level directory and two new conventions (folder layout, traceability) for adopters to learn. Refactoring a shipped pack (`contracts` v0.1.0) risks regressions for existing Zalando users. The seam adds a branch and a template field to `new-spec`. Backward traceability for extensionless formats needs a `REGISTRY.md` file and a lint to keep it honest — a small maintenance surface.

## Evidence & prior art

**Spike / de-risk.** Riskiest assumption: the Zalando ruleset can be extracted into a swappable bundle the skill consumes generically. Result (structural read, no code spike needed): **feasible and mechanical.** `api-contract/references/*.md` are already separate files, so the architecture is half-proven; the remaining work is (a) lifting the machine-checkable quality-gate checklist out of `SKILL.md` into the standard manifest and (b) rewriting phase prose to cite "the active standard" instead of literal `[#NNN]`. Known shape, not a research gamble.

**Repo precedent.**
- `docs/architecture/overview.md` — "compose around `core`, not subclass; packs don't import each other"; `core` repo-only vs `contracts` user-scope-default (Decision 1).
- `new-spec` SKILL.md step 6 — "select a subagent matching `adversarial-reviewer`… absence is a note… not a blocker" (Decisions 5 & 7).
- `adapt-to-project` — Class 2 `.upstream` companion merges, at either scope (Decision 3); Class 3 discovery + restructuring, which relocates non-canonical primitives into their canonical home (Decision 8).
- `AGENTS.md` § Check before acting — "Propose new top-level directories via RFC" (Decision 8).
- `packs/contracts/.apm/skills/api-contract/` — `references/*.md` already file-separated; quality gates still inlined in `SKILL.md` (spike).

**External prior art.**
- [Spectral rulesets — `extends`](https://github.com/stoplightio/spectral/blob/develop/docs/getting-started/3-rulesets.md) and [override-to-`false`](https://lornajane.net/posts/2020/custom-openapi-style-rules-with-spectral) — base+delta, both halves fetched and confirmed (Decision 2).
- [AsyncAPI + CloudEvents](https://www.asyncapi.com/blog/asyncapi-cloud-events) and [which event-driven spec to use](https://www.asyncapi.com/blog/async_standards_compare) — OpenAPI = sync REST, AsyncAPI = the event peer, CloudEvents = envelope only (Decision 4).
- [Buf style guide](https://buf.build/docs/best-practices/style-guide/) — versioned package directories (`…/v1/`), `lower_snake_case.proto` filenames, "set up breaking change detection from day one" (fetched & confirmed; Decisions 8 & 9).
- [Structuring repositories with protocol buffers](https://dev.to/davidsbond/golang-structuring-repositories-with-protocol-buffers-3012) — top-level proto directory with domain/version subdirs (Decision 8).
- Alternative bases an org might `extends`: Google AIP, Microsoft REST API Guidelines, PayPal API Standards.

## Open questions

1. **Multi-standard per repo** (post-v1 trigger, not a re-litigation of D3) — if a monorepo later needs two API styles concurrently, install-time companion-merge can't express it and the runtime resolver (Axis C) becomes necessary. D3 is final for v1; this opens only if demand materialises. *Recommended default:* companion-merge only; revisit on demonstrated demand. *Owner:* eugenelim. *Decide-by:* deferred until the trigger appears.

## Follow-on artifacts

When accepted:
- **Spec:** `docs/specs/pluggable-api-standards/` — the standard bundle format (manifest + rule files + quality-gate checklist), Zalando extraction, and `adapt` wiring. (Stage 1.)
- **Spec:** `docs/specs/spec-contract-seam/` — the `new-spec` conditional step, `Contract:` header template edit, the `contracts/<type>/` tree + naming convention, bidirectional traceability (`x-spec` + `REGISTRY.md`) with an **in-repo forward/backward traceability lint**, plan contract-test wiring, the convention-first discovery (consumer-side capability map + roster match + runtime note), and the **`adapt-to-project` Class 3 contract-relocation** detection (a `core` skill edit). (Stage 2, depends on Stage 1.)
- **Convention change:** `docs/CONVENTIONS.md` (and `core` seeds) — record the `contracts/<type>/` layout, naming/versioning, and spec↔contract traceability as living conventions; note the new top-level directory.
- **Skill amendment:** `adapt-to-project` SKILL.md — carve a narrow exception into the "never add a new top-level directory" anti-pattern for the RFC-authorized `contracts/` root, enabling Class 3 contract relocation (Stage 2).
- **ADR:** record the "separate pack + agnostic, convention-first seam (not a merge)" decision, the repo-level contract-tree location, and the capability-name convention.
- Possible **follow-on RFC:** AsyncAPI / CloudEvents (or proto / GraphQL / MCP) standard as a second contract type.
</content>
