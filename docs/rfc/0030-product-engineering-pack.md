# RFC-0030: A `product-engineering` pack — level-agnostic product shaping that decomposes into specs, with a Backstage-anchored cross-component value-stream layer

- **Status:** Accepted <!-- Draft | Open | Final Comment Period | Accepted | Rejected | Withdrawn | Experimental -->
- **Author:** eugenelim
- **Approver:** eugenelim
- **Date opened:** 2026-06-12
- **Date closed:** 2026-06-13
- **Related:** RFC-0019 + ADR-0009 (product-brief intake / `receive-brief` / brief layer) · ADR-0008 + RFC-0017 + RFC-0018 (contract-authoring seam, pluggable API + event contracts) · RFC-0020 (`reference.md` golden-path — the `architect` seam) · RFC-0004 (install-scope per pack) · RFC-0007 (first user-scope pack — precedent) · RFC-0016 (doc-drift gate) · RFCs 0001–0003 (pack-catalogue model) · `architect` / `monorepo-extras` / `core` packs · upstream source: `github.com/eugenelim/ai-product-kit`

---

## The ask

**Recommendation (BLUF).** Add a new **opt-in, user-scope `product-engineering` pack** — product management + requirements engineering + process engineering — that gives the catalogue the *upstream* it currently lacks: a level-agnostic way to shape product **intent**, de-risk it, and decompose it into the shippable **specs** `core` already builds. It is **habits, not infrastructure** (three skills, progressive disclosure, no engine/hooks/validators/subagents) and **mined from `ai-product-kit`** by hand (no cross-repo coupling). Ship **v1 at app/solo scale (single-component handoff)**; specify but **defer** the business-unit, cross-component **value-stream meta-repo** (Backstage-anchored) to phase 2.

**Why now (SCQA).**
- *Situation.* The catalogue's product surface stops at `receive-brief` (RFC-0019): the *inbox* where an externally-authored brief is decomposed into specs. Everything upstream of the brief — strategy, discovery, validation, requirements decomposition — has no home.
- *Complication.* Teams (and the owner's own `ai-product-kit`) are building that upstream by hand, and the AI era has changed its shape: the shippable unit is the spec/vertical-slice, not the user story; discovery-first is now best practice; and distributed-system work needs cross-component coordination the brief layer doesn't model.
- *Question.* Should the catalogue carry that upstream as a pack, in a shape that is lightweight, recognizable, and composes with `core`/`architect`/`monorepo-extras` rather than duplicating them?

**Decisions requested** (each: recommended option · decide-by = on circulation close):

1. **Add the pack at all** → *yes, as an opt-in user-scope pack* (vs do-nothing / extend `core`).
2. **Name** → `product-engineering` (PM + requirements eng + process eng).
3. **Unifying artifact** → a level-tagged, recursive **`intent`** tree (capability/feature intents and PRDs are the *same* artifact at different levels; the leaf is a spec/slice).
4. **Skills** → three level-agnostic verbs: **`frame-intent`**, **`de-risk-intent`**, **`decompose-intent`**.
5. **Mode model** → one global **Scale** axis (app ↔ BU, resolved at intake: infer → confirm → ask), with **maturity**, **reversibility**, and a skill-baked, choosable **prototype-approach** (`prototype-led` ↔ `validate-first`) as per-intent flags.
6. **Brief reconciliation** → a brief *is* a feature-level intent **projected onto one repo**; `receive-brief` stays in `core`; `core` gains additive optional fields and still stands alone.
7. **Contract maturity** → behavioral @intent → interaction (CDC-shaped) @brief → **detailed wire contract @spec** (reuse `ADR-0008`/`RFC-0017/0018` `Contract:` seam) → verify @build.
8. **Tracker projection** → **one-way** canonical→tracker via per-mode profiles (Linear / Jira Align / none); **defer live API** integration to a later pack.
9. **Cross-component layer** → a **value-stream meta-repo** anchored to **Backstage Domain→System→Component→API**; holds cross-component intents, the catalog, canonical shared contracts, the rollup, and (the `architect` seam) the system architecture. **Phase 2.**
10. **v1 boundary** → ship **app-scale + single-component** fully; BU-scale meta-repo + cross-component contract/rollup is phase 2.

---

## Problem & goals

**Problem (diagnosis).** The catalogue makes a repo ready for engineering agents but assumes *someone else* did the product work and handed over a brief. In practice that upstream is where the expensive failures live — building the wrong thing, un-validated bets, requirements with no outcome, and (for distributed systems) cross-component features that get re-litigated inside individual specs. There is no shared, recognizable discipline for shaping intent into buildable specs, and the one artifact we do have (`brief`) is a receiving dock, not an authoring surface.

**Goals.**
- A lightweight, opt-in discipline for shaping product **intent** → de-risking it → decomposing it into the specs `core` builds, usable by a solo dev, a product-eng hybrid, and a BU product org alike.
- Anchored to **recognized** vocabulary (requirements engineering, product discovery, Backstage catalog, design-first contracts) — not invented jargon.
- Composes with `core` (`receive-brief`/`new-spec`/`Contract:` seam), `architect` (system design), and `monorepo-extras` (structuring) instead of duplicating them.
- Stays **habits, not infrastructure** — clears the charter's four principles, with no new reviewers (3-reviewer ceiling) and no engine.

**Non-goals** (could-have-been goals, deliberately dropped).
- **Not** a port of `ai-product-kit`'s 40-command / 84-object ontology surface — we mine its spine, not its mass.
- **Not** live tracker API integration (Linear/Jira Align) in this pack — projection *mapping + export* only; a live-sync integration pack is separate, later.
- **Not** a cross-repo coordination *hub* or a new runtime — the meta-repo is a coordinating *repo*, not a service.
- **Not** bidirectional tracker sync — one-way by default (bidirectional silently corrupts across mismatched hierarchies).
- **Not** a change to how `core` works standalone — the only `core` edits are additive, backward-compatible fields.

---

## Proposal

### Design brief at a glance

| Dimension | Decision |
|---|---|
| **Pack** | `product-engineering`, opt-in, user-scope (skills travel; seeds land repo-scope in `docs/product/`). Habits, not infra. |
| **Artifact** | `intent` — recursive, level-tagged; carries `{outcome, opportunity, assumptions}`; children are lower-level intents or, at the leaf, **specs/slices**. PRD = a feature-level intent rendered as a doc. |
| **Skills** | `frame-intent` · `de-risk-intent` · `decompose-intent` (level-agnostic verbs). |
| **Spine** | Steel-thread v2: vision/intent → outcome (input + lagging + **guardrail**) → opportunity (JTBD job map) → **[reversibility fork]** → predeclared **kill condition** → prototype → spec (**appetite**) → ship (**GTM**) → landing (**evals**) → back to intent. |
| **Lifecycle** | Per-intent loop (every level): framed → de-risking ⟲ (**prototype refines the intent**) → survived/killed → decomposed → child intents *or* leaf brief. Prototype = validator (irreversible bets) or **driver** (reversible bets); child kills bubble up; landing feeds back. See §11. |
| **Modes** | **Scale** (app ↔ BU) — one global axis, resolved at intake. Per-intent flags: **maturity** (greenfield/brownfield), **reversibility**, and a skill-baked, choosable **prototype-approach** (`prototype-led` ↔ `validate-first`). |
| **Brief** | A feature-level intent **projected onto one repo**: identity at app scale; per-component **slice** at BU scale. Owned by `core`. |
| **Contracts** | behavioral @intent → interaction (CDC) @brief → **wire contract @spec** (existing `Contract:` seam) → verify @build. |
| **Trackers** | One-way canonical→tracker via per-mode profiles: Linear (collapse) / Jira Align (expand) / none. Live API deferred. |
| **Cross-component** | **Phase 2:** a Backstage-anchored value-stream meta-repo holding intents, catalog, canonical contracts, rollup, + system architecture (`architect` seam). |
| **Seams** | `core` (brief / `receive-brief` / `Contract:`), `architect` (system arch in meta-repo via `reference.md`), `monorepo-extras` (structuring; meet only at "where the shared contract lives"). |
| **v1** | App-scale + single-component handoff, fully. BU-scale meta-repo + cross-component contract/rollup = phase 2. |

### 1. The artifact: a recursive, level-tagged `intent`

The unifying move is that **capability intent, feature intent, and PRD are not three artifact types — they are one artifact (`intent`) at different levels.** A PRD is a feature-level intent rendered as a stakeholder document. An intent carries `{outcome, opportunity, assumptions}` as fields and its children are **either lower-level intents or, at the leaf, specs/slices** (the shippable, agent-buildable unit). This resolves the two failures of a fixed model: decomposition is **recursive** (one level at a time, until specs), and assumptions are a **field of an intent** so de-risking always operates "this intent, at its level" (the *kind* of assumption — architectural/adoption vs desirability — follows the level).

### 2. The spine (steel-thread v2)

`vision/intent → outcome [controllable input + lagging + guardrail metric; qualitative-but-falsifiable allowed] → opportunity [JTBD job map default] → [reversibility fork] → riskiest assumption + predeclared kill condition in the test's own currency → prototype → spec [appetite/time-box] → ship [distribution/GTM] → landing [adopt/fix/kill; evals loop for AI products] → feeds back to vision.`

Pressure-tested against fast-moving leaders (2024–2026): the field is **bimodal** (outcome-led à la Cagan vs taste-led à la Linear/founder-mode), so the vision/intent root gives the taste-led mode a home and validation rigor is gated by reversibility, not mandated. The AI-era prototype-first shift **reinforces** the thread (the prototype validates the assumption and increasingly carries the spec; the vibe-coding tech-debt backlash raises the value of the kill-condition and landing steps). Platform↔module tension is held by **voluntary-adoption metrics (justify-down)**; trace-up is a sanity check, not SAFe traceability.

### 3. The three skills

All three adapt to the optional, per-intent **prototype-approach** mode (`prototype-led`
↔ `validate-first`; §4) — the prototype-approach (both paths) is baked into each skill's
behavior, not bolted on.

- **`frame-intent`** — author/shape an intent at any level: its outcome (input + lagging + guardrail), opportunity (JTBD job map default; journey map = enterprise/brownfield variant), level tag, parent link. Runs **intake** (resolve Scale; ask greenfield/brownfield).
- **`de-risk-intent`** — the load-bearing engine: reversibility triage (one-way/two-way door) → riskiest assumption (front with "what would have to be true") → **predeclared kill condition in the test's own currency** (quantitative threshold where there's traffic; qualitative bar in 0-to-1) → probe/prototype → survive/kill verdict.
- **`decompose-intent`** — break an intent into the **next level down** (child intents, or specs/slices at the leaf) and project to a tracker via a profile. Recursive; multi-level by construction.

### 4. The mode model

- **Scale** (the one global axis): *app/solo ↔ BU/enterprise*. Subsumes deployment-topology, altitude, and install-scope. **Resolved at the intake step** — infer (app code + single component → app; no app code / many component pointers → BU) → confirm → **ask if ambiguous** — and stamped (`scale:`) on the `docs/product/` root. No config file.
- **Maturity** (greenfield ↔ brownfield): a **per-intent intake flag**, not a global mode. Its only job: gate current-state inputs (process map L3 as constraint; journey map as input) — offered in brownfield, skipped in greenfield to avoid paving cow paths.
- **Reversibility/conviction**: **per-intent**, inside `de-risk-intent` — cheap/reversible bets ship a build-to-learn probe on conviction; expensive/irreversible bets get a predeclared kill condition. The reversibility triage **recommends** a prototype-approach (next bullet) but does not lock it.
- **Prototype-approach** (`prototype-led` ↔ `validate-first`): an **explicit, optional, per-intent mode baked into all three skills** — not merely an emergent lifecycle. `de-risk-intent` surfaces it as a choice (defaulted from reversibility, overridable), and each skill adapts:
  - **`prototype-led`** (default for reversible / taste-led): `frame-intent` frames *thin* (outcome + a hypothesis, detail deferred); `de-risk-intent` lets a cheap build-to-learn prototype **drive** the intent's refinement (the build *is* the test); `decompose-intent` slices against **what the prototype revealed**.
  - **`validate-first`** (default for irreversible / outcome-led): `frame-intent` frames *fully*; `de-risk-intent` **predeclares the kill condition** then builds to test it; `decompose-intent` slices from the validated intent.
  Choosing the approach changes the skills' behavior — it is the "choose your prototype approach" toggle, optional and reversible per intent.

### 5. The brief reconciliation (keeping `core` standalone)

**A brief is a feature-level intent projected onto a single repo.** At app scale the projection is *identity* (the intent **is** the brief). At BU scale it is a *slice* (the feature intent is cut per component; each per-component slice is a brief that crosses into that component's repo). Either way it is exactly what `core`'s `receive-brief` consumes — which is the airtight reason `receive-brief` stays in `core`: **every component repo receives its own projection, whether or not the product pack is installed upstream.** Three authors, one inbox: a human (externally-authored), the product pack at app scale (whole intent), the product pack at BU scale (a slice). The only `core` change is additive and backward-compatible: the brief gains optional `level:`, `parent-intent:`, and (BU) `component:` + a contract reference. These **extend rather than collide with** the existing optional `Epic:` pointer (`Epic:` names an external cross-repo *coordinator*; `parent-intent:` names the product-pack *intent* this brief was projected from — distinct roles, both upward pointers), and because `receive-brief` **never mandates a schema** (RFC-0019), optional additive fields are absorbed without breaking briefs authored before them. `core` imports nothing from the pack and works alone.

### 6. Contract maturity along the SDLC

The detailed wire contract is pinned at the **spec** stage — where full component context lives — not at intent:

| Stage | Contract maturity here | Recognized name |
|---|---|---|
| intent | behavioral only (example-shaped expectations; no fields/types) | Specification by Example / BDD |
| brief / slice | per-component **interaction contract** (consumer expectations, dependency direction); not a full schema | Consumer-Driven Contract (consumer-expectation form) |
| **spec** (component repo) | **detailed wire contract** — OpenAPI/AsyncAPI/proto, fields, types, errors, compat | design-first / contract-first |
| build | implement against the pinned contract + verify | code-against-contract |

This reuses the catalogue's existing `Contract:` seam (`ADR-0008`, `RFC-0017/0018`, `new-spec` step 4b) at exactly the stage it already lives. The product pack stays **behavioral**; `core`/`new-spec` pins the wire contract.

### 7. Cross-repo shared contract (phase 2)

Authority lives in **one shared, version-pinned home** (the meta-repo / a registry / an interface repo); the brief packet **references** `contract@version` and may **attach a read-only courier snapshot** for provenance — never attach-as-authority (that forks the contract N ways). Default **provider-contract-first** (defining a surface for not-yet-built components enables parallel dev), with a **per-relationship override** to CDC where one provider serves known collaborating consumers. Provider/consumer roles are expressed by **mirroring Backstage's `providesApi`/`consumesApi` relations** (source fields `spec.providesApis`/`spec.consumesApis`) rather than novel frontmatter, plus a **compatibility direction** (who upgrades first).

### 8. Tracker projection (one-way)

The canonical intent tree is **deeper than any tracker**; trackers are lossy downward projections of it, via a per-mode **projection profile** mapping `level → tracker object`:

| Canonical | → Linear (lean; collapse tree) | → Jira Align (deep; expand tree) |
|---|---|---|
| top (capability) intent | Initiative | Epic (Portfolio tier) |
| feature-level intent | Project | Feature (Program tier) |
| extra intervening intents | flatten to labels / sub-issues | rare; Capability sits at the Solution tier (multi-ART) |
| **spec / slice** | **Issue** | **Story** (Team tier) |
| story-trace | sub-issue / checklist | Story / sub-task |

The *same* canonical **feature-level intent** lands at a **Project** in Linear and a **Feature** in Jira Align (and that Jira Align Feature is itself a Jira Software *Epic* on sync) — proof the model must be canonical and the tracker a render. **One-way** (canonical→tracker) by default; live API integration is deferred to a separate pack.

### 9. The cross-component value-stream meta-repo (phase 2)

For distributed systems, a **value-stream / product-org meta-repo** (BU scale) coordinates work fanning out to many component repos, anchored to **Backstage's Domain→System→Component→API** ontology. It holds: cross-component intents, the catalog (System/Component/API), the **canonical shared contracts**, the **cross-component rollup**, and — same audience, same artifacts — the **system architecture** (C4 + bounded-context map), which is the **`architect` seam** (it is the home `RFC-0020`'s `reference.md` already implies). Monorepo-vs-polyrepo **structuring** stays in `monorepo-extras`; the two packs meet only at "where the shared contract lives" (in-tree for monorepo; in the meta/contracts repo for polyrepo). Framed via **Team Topologies** (one coordinating repo per value stream, platform-as-product). The dominant failure mode is **drift** of the contracts/maps — so currency is a first-class, enforced discipline (the `RFC-0016` doc-drift philosophy).

### 10. Guides (first-class deliverables)

Diátaxis set via `new-guide` (as `product-brief-intake` shipped): an **explanation** ("the intent tree and why level-agnostic shaping"), **two how-tos** (one per Scale — "frame a feature intent in an app repo"; "run a capability intent in a product-org repo"), and a **reference** (intent fields, level tags, mode resolution, projection profiles).

### 11. Intent lifecycle, inter-level handoff & prototype-driven refinement

The spine (§2) and skills (§3) are *states and verbs*; this is how they compose
over time. An intent moves through a small lifecycle **at every level**, and the
prototype is the engine that refines it — not a one-shot gate.

**States (any level):** `framed` (frame-intent: outcome + opportunity + level) →
`de-risking` (de-risk-intent; the **inner loop** below) → `{survived | killed}` →
(survived) `decomposed` (decompose-intent) → child intents *or*, at the leaf,
a brief handed to `core`.

**Inner loop — prototype-driven refinement.** Inside `de-risk-intent`, the prototype/
probe runs `build → learn → refine the intent → re-build`, rewriting the intent's
outcome/opportunity/assumptions as evidence arrives, until a survive/kill verdict.
The prototype's **role is the choosable `prototype-approach` mode (§4)** — baked into
all three skills, defaulted by the reversibility fork, overridable per intent:
- *`validate-first` (default: irreversible / outcome-led) → prototype-as-validator*:
  predeclare the kill condition, build to test it, take the verdict.
- *`prototype-led` (default: reversible / taste-led) → prototype-as-driver*: build a
  cheap prototype early and let what it reveals **drive** the intent's refinement —
  the build is the test.

Either way, prototype findings fold back into the intent — this is where
prototype-driven refinement of the requirements actually happens. (Anchors: Lean
Startup build-measure-learn; Torres's "crummy first draft, refine"; the AI-era
prototype-first shift — the prototype both validates the assumption and carries
behavioral detail forward.)

**Inter-level handoff.** `decompose-intent` runs on a *survived* parent and emits
child intents, each stamped with `parent-intent` and inheriting the parent's
outcome/scope context; each child re-enters at `framed` and runs its own loop. Two
rules govern the handoff:
- **Gate:** decompose only after the level's riskiest assumption *survives* — don't
  fan a bet out into children you haven't de-risked at its own altitude (capability
  level → architectural/adoption assumptions; feature level → desirability).
- **Upward feedback:** a child's `killed` verdict **bubbles up** — forcing the parent
  to re-decompose (drop/replace that branch) or, if it invalidates the bet, re-frame
  the parent. This upward edge is the cross-level coupling the recursion needs.

**Prototype → spec handoff.** At the leaf, the prototype's *behavioral* detail
travels with the brief into the component repo and becomes the raw material
`new-spec` formalizes into acceptance criteria; the **detailed wire contract is
pinned at the spec stage** (§6), not in the prototype. The prototype carries
behavioral truth; the spec formalizes it and pins the contract.

**Outer loop.** Cross-level recursion (decompose → children loop; kills bubble up)
plus the post-ship **landing** (adopt/fix/kill) feeding back into the intent for the
next cycle — closing the spine (§2) back to vision/intent.

---

## Options considered

**Axis A — where the upstream product discipline lives** (exhaustive: it lives nowhere / in `core` / in a new pack / in an external tool):

| Option | Prior art | Trade-off |
|---|---|---|
| **Do-nothing** (stay at `receive-brief`) | RFC-0019 scope | Zero cost; but the upstream stays ad-hoc and `ai-product-kit` stays unmineable by the catalogue. Cost of delay: every team re-invents shaping. |
| Extend `core` | `core` owns `receive-brief` | Forces product-shaping onto every adopter, including pure-eng repos — violates "opt-in" and bloats `core`. |
| **New opt-in pack** ★ | `architect`, `research` (user-scope opt-in); RFC-0007 (first user-scope pack) | Clears charter Principle 2 (substantive, upstream of `receive-brief`, not duplicative); opt-in keeps pure-eng repos clean. |
| External tool only | `ai-product-kit` standalone | Already exists; but then the catalogue can't offer the discipline as a travelling habit, which is the whole point. |

**Axis B — the decomposition/work-item model** (exhaustive along "how levels are typed"): fixed distinct types (capability/feature/PRD/story) [the SAFe/Jira-Align reification — rejected: levels disagree across tools, story≠spec] · flat fixed object set [the earlier 5-object draft — rejected: doesn't handle arbitrary depth] · **recursive level-tagged `intent` tree** ★ [handles any depth; projects to both lean and deep trackers] · tracker-native model [rejected: tool dictates the model].

**Axis C — tracker sync direction** (exhaustive): none/manual · **one-way canonical→tracker** ★ · bidirectional [rejected: silent drift/corruption across mismatched hierarchies, documented].

**Axis D — where the detailed wire contract is pinned** (exhaustive along the stage ladder): intent [premature lock-in — Hyrum/Postel] · brief [still no full component context] · **spec** ★ [design-first's "design stage"; full context present; before parallel build] · build [late-integration surprises — the failure CDC exists to prevent].

**Axis E — cross-component coordination home** (exhaustive): each component repo [no one owns the cross-cutting artifacts] · monorepo [solves it in-tree but forces one tree/release train] · **value-stream meta-repo** ★ [the polyrepo answer; Backstage-anchored] · external SaaS [out of charter — runtime infra].

---

## Risks & what would make this wrong

**Pre-mortem (top failure modes + mitigations).**
- *It balloons into `ai-product-kit`-scale infra.* → The v1 boundary (app-scale, single-component, three skills, defer meta-repo) + progressive disclosure (SKILL.md <100 lines) + the charter four-principle gate per primitive. **This is the riskiest assumption — spiked below.**
- *Adopters never reach for it* (fails "used often"). → Opt-in user scope, like `architect`/`research`; the spine is reached for at the start of every feature/initiative.
- *The meta-repo's contracts/maps go stale* (the documented dominant failure). → Phase 2 treats currency as enforced (the `RFC-0016` doc-drift discipline), and the v1 cut avoids the meta-repo entirely.
- *`intent` reads as invented jargon.* → It formalizes the owner's own term and anchors to "strategic intent" (Hamel/Prahalad, Rumelt); every other noun (outcome, opportunity, spec, contract) is canonical.

**Key assumptions (falsifiable).**
- *The recursive intent ontology projects cleanly to both Linear (lean) and Jira Align (deep) without forcing story=spec.* (Spiked below.)
- *Pinning the wire contract at the spec stage is correct* — falsifiable if real teams need it pinned at intent; the design-first/CDC literature says otherwise.
- *A brief = a feature-intent projected onto one repo* covers both app and BU cases without a separate artifact. Falsifiable if the BU slice needs fields a brief can't additively carry.

**Drawbacks (not "none").** A third product-adjacent surface (after `core` brief layer and `architect`) raises the catalogue's conceptual surface area; `intent` is one mildly-novel term; the BU-scale meta-repo introduces a coordination pattern with real hard limits (no atomic cross-repo commit, no shared release train) that adopters must accept; and manual sync from `ai-product-kit` is a standing maintenance cost.

---

## Evidence & prior art

**Spike / de-risk (riskiest assumption: does one canonical tree project to both tracker modes?).** Worked example — a 2-level intent `billing-platform` (capability) → `dunning-retries` (feature) → 3 specs:
- **Jira Align (deep):** `billing-platform`→Epic, `dunning-retries`→Feature, specs→Stories. Near-1:1; uses native depth. ✓
- **Linear (lean):** `billing-platform`→Initiative, `dunning-retries`→Project, specs→Issues; the capability/feature distinction collapses into the Initiative/Project pair (Linear has **no Epic/Feature type** — verified). ✓
The same spec lands at **Story** (Align) and **Issue** (Linear) from one source; the deep tracker expands, the lean tracker collapses. Both tracker object-models are author-verified (see prior art), and the projection table (§8) and this spike now use one consistent mapping. The projection-profile mechanism holds. **Spike passes.**

**Repo precedent.**
- RFC-0019 + ADR-0009 — the brief layer and `receive-brief`; this RFC is the upstream that authors what they receive.
- ADR-0008 + RFC-0017 + RFC-0018 — the contract-authoring seam this RFC reuses at the spec stage.
- RFC-0020 — `docs/architecture/reference.md` as the golden-path anchor; the meta-repo's architecture home (the `architect` seam).
- RFC-0004 / RFC-0007 — install-scope per pack and the first user-scope pack precedent.
- RFC-0016 — the doc-drift gate philosophy the phase-2 meta-repo currency relies on.
- `research-pack` / `converters-pack` specs — the shape precedent for adding a pack via spec.
- `monorepo-extras` (`new-package` skill) — the structuring concern this RFC keeps separate.
- `docs/CHARTER.md` — the four principles and the 3-reviewer ceiling this pack is gated by.

**External prior art** (✓ = fetched and confirmed by the author; ◦ = surfaced by research subagents, to be re-verified in the pre-handoff gate):
- ✓ **Backstage software catalog** — Domain → System → Component → API; "a System is a collection of resources and components that exposes one or several public APIs" ([system-model](https://backstage.io/docs/features/software-catalog/system-model/)); relation *types* are singular **`providesApi`/`consumesApi`** (+ `ownedBy`/`partOf`; source fields `spec.providesApis`/`spec.consumesApis`) — author-verified ([well-known relations](https://backstage.io/docs/features/software-catalog/well-known-relations/)).
- ✓ **Design-first / contract-first** — "describe every API design… before you write any code"; "fixing issues once the API is coded costs far more than during the design phase" ([Stoplight](https://blog.stoplight.io/api-first-api-design-first-or-code-first-which-should-you-choose)).
- ✓ **Linear** — Workspace/Team/Issue with optional Project/Initiative/Cycle; an Issue must belong to one Team; **no Epic/Feature object type** ([conceptual model](https://linear.app/docs/conceptual-model)).
- ✓ **Jira Align** — Theme→Epic→Feature→Story (tiers Portfolio/Program/Team; Capability sits at the **Solution** tier for multi-ART work, not a plain optional level); "Jira Align Features equate to Epics in Jira" ([Atlassian community](https://community.atlassian.com/forums/Jira-Align-articles/A-Crash-Course-on-Jira-Align-s-Core-Hierarchies/ba-p/1167395)).
- ◦ **Consumer-Driven Contracts** — consumer-expectation contracts, roles by publish/verify action ([Pact](https://docs.pact.io/)); **Specification by Example** ([Adzic](https://gojko.net/books/specification-by-example/)); **Hyrum's / Postel's** evolution tension ([Nordic APIs](https://nordicapis.com/meet-hyrum-and-postel/)).
- ◦ **Continuous discovery / OST** ([Product Talk](https://www.producttalk.org/opportunity-solution-trees/)); **JTBD job map ≠ journey map** ([Ulwick](https://jobs-to-be-done.com/mapping-the-job-to-be-done-45336427b3bc)); **Team Topologies** platform-as-product ([key concepts](https://teamtopologies.com/key-concepts)); **GitHub Spec Kit** verb-noun command vocabulary ([spec-kit](https://github.com/github/spec-kit)).
- ◦ Naming canvas: Obra Superpowers, gstack, BMAD anchor weakly; Spec Kit / deanpeters / Anthropic knowledge-work plugins anchor well (verb-noun + canonical terms verbatim).

---

## Open questions

1. **Pack version & marketplace registration mechanics** — new pack ⇒ `pack.toml` + `plugin.json` + `marketplace.json` aggregation; confirm whether v1 ships user-scope-default (not projected to this repo's working tree) like `architect`/`research`. *Default:* yes, user-scope-default. *Owner:* eugenelim. *Decide-by:* spec authoring.
2. **Phase-2 contract-authority home** — meta-repo vs a dedicated contracts/interface repo vs a schema registry is org-specific; v1 doesn't decide it. *Default:* reference-by-version, courier-snapshot; authority location chosen per org in phase 2. *Owner:* eugenelim. *Decide-by:* phase-2 RFC.

---

## Follow-on artifacts

Filled in on acceptance:
- **ADR-NNNN** — the `intent` ontology + the brief-as-projection + the contract-maturity-by-stage decisions (the durable architectural record).
- **Spec:** `docs/specs/product-engineering-pack/` — v1 (app-scale, single-component): the three skills, the Scale-intake, the seeds for `docs/product/`, the additive `core` brief fields, the Diátaxis guides.
- **Spec (phase 2):** `docs/specs/value-stream-meta-repo/` — the Backstage-anchored cross-component layer, shared-contract handoff, cross-component rollup, `architect` seam.
- **Convention edits:** `docs/CONVENTIONS.md` — the `intent` artifact + the brief's additive `level:`/`parent-intent:`/`component:` fields + the contract-maturity-by-stage note.
- **Guides:** via `new-guide` (explanation + two how-tos + reference).

---

## Errata

Post-acceptance corrections to this frozen RFC. Each is approver-signed and dated.

- **2026-06-13 (eugenelim):** Open question #2 ("Phase-2 contract-authority home") was stamped *Decide-by: **phase-2 RFC***. Phase 2 is being delivered by a spec (`docs/specs/value-stream-meta-repo/`) + **ADR-0022**, **not** a new RFC — because the cross-component layer was already *accepted* in this RFC (decision #9 + Appendix A), so no cross-cutting proposal remained to circulate (per the project rule: open a new RFC only if phase-2 scope exceeds what this RFC accepted; it does not). ADR-0022 resolves the open question exactly to this RFC's stated default: the authority **location** stays org-specific (elicited per value stream; default the meta-repo), and only the **reference-by-version + courier-snapshot shape** is fixed. The "phase-2 RFC" decide-by vehicle is therefore satisfied by **ADR-0022**.

---

## Appendix A — Phase-2 cross-component research (straight-to-spec)

This appendix preserves the phase-2 research in enough depth to author
`docs/specs/value-stream-meta-repo/` (spec + plan) without re-deriving it. (`✓`
= author-verified citation; `◦` = research-surfaced, re-verify at phase-2 spec.)

### A.1 The handoff model — two decompositions at two boundaries

The load-bearing claim: **the repo (component) boundary is the spec-context
boundary** — an implementable AI spec needs the target component's full context
(architecture, conventions, code, contracts), so a cross-component feature
*cannot* be specced upstream; it is **sliced per component** and each slice is
completed into specs *inside* the owning repo. This yields two decompositions:

1. **Cross-component slicing** — product pack, upstream, in the meta-repo:
   feature intent → one **brief per component** (the handoff unit that crosses
   the repo boundary).
2. **Within-component spec-building** — `core`'s `receive-brief` → `new-spec`,
   downstream, in each component repo, *with* that repo's context.

Consequence: the product pack needs **no new `new-spec` integration** — it stops
at the brief (the repo boundary), and `core` already takes a brief the rest of
the way. This is *why* `receive-brief` lives in `core` (universal receiver) and
the slicer is the optional upstream pack. Component = repo (polyrepo) or module
(monorepo); the model is identical, only the landing differs.

### A.2 The meta / value-stream repo — patterns + ontology

Recognized pattern ("meta-repo" / "virtual monorepo"), in flavors:
- **Manifest/orchestration** — Google's `repo` tool ([AOSP repo](https://source.android.com/docs/setup/reference/repo)) ◦, the `meta` tool, git submodules (high-maintenance) ◦.
- **Documentation/context meta-repo** — "no application code at all: only documentation, manifests, scripts, agent configuration"; the closest flavor to ours ◦.
- **Dedicated contracts/interface repo** — shared OpenAPI/proto/schemas in one repo ◦.
- **Architecture-as-code repo** — C4 + ADRs version-controlled centrally ◦.

**Anchor ontology = Backstage Domain → System → Component → API** ✓, with
first-class relations **`providesApi`/`consumesApi`**, `ownedBy`, `partOf`
(source fields `spec.providesApis`/`spec.consumesApis`) ✓. Maps 1:1: value
stream ≈ Domain/System; cross-component feature → Components; shared contracts ≈
API entities; provider/consumer = `providesApi`/`consumesApi`. The meta-repo
holds intents + the catalog + canonical contracts + the rollup + the C4/
bounded-context **system architecture** (the `architect` seam; the home
`RFC-0020`'s `reference.md` already implies). Frame via **Team Topologies**
(one coordinating repo per value stream; platform-as-product) ◦.

**Hard limits to state in the spec:** no atomic cross-repo commit, no shared
release train, and **drift of contracts/maps is the dominant failure** ("agents
follow stale instructions confidently") ◦ → currency must be a first-class
enforced discipline (the `RFC-0016` doc-drift philosophy).

### A.3 Shared-contract handoff — approaches + verdicts

| Approach | Where the contract lives | Provider/consumer roles | Tradeoff |
|---|---|---|---|
| Consumer-Driven Contracts (Pact) ◦ | a broker | implicit, by publish/verify action | real-usage guarantee; consumers must write pact tests |
| Provider-contract-first / API-first ◦ | provider's spec file | ownership-based (provider authors) | best for many/unknown consumers; provider bias risk |
| Schema registry (Confluent/Buf/Apicurio) ◦ | central registry | producer/consumer + compatibility mode | strongest automated guarantee; a running service |
| Shared contract / interface repo ◦ | a git repo / published package | CODEOWNERS / directory | simple; mutable VCS ref gives no stable version contract |

**Verdicts:** (a) **reference the canonical version-pinned contract; attach only a
read-only courier snapshot** — never attach-as-authority (forks it N ways). (b)
**Default provider-contract-first** (defining a surface for not-yet-built
components enables parallel dev), with **per-relationship override** to CDC
(bi-directional contract testing explicitly endorses mixing per consumer) ◦. (c)
**Roles: mirror Backstage `providesApi`/`consumesApi`** ✓ (a recognized
formalization) rather than novel frontmatter; carry a **compatibility/upgrade
direction** (BACKWARD→consumers first / FORWARD→providers first) ◦.

### A.4 Contract maturity along the SDLC

Detailed wire contract pinned at the **spec** stage — design-first's "design"
stage: downstream of discovery, upstream of build, where full context lives.
"Fixing issues once the API is coded costs far more than during the design
phase" ✓ ([Stoplight](https://blog.stoplight.io/api-first-api-design-first-or-code-first-which-should-you-choose)).

| Stage | Maturity | Recognized name |
|---|---|---|
| intent | behavioral only (examples; no fields/types) | Specification by Example / BDD (Adzic) ◦ |
| brief/slice | interaction contract (consumer expectations, dependency direction) | Consumer-Driven Contract ◦ |
| **spec** | **detailed wire contract** (fields/types/errors/compat) | design-first ✓ |
| build | implement + verify (provider verifies CDC; schema-compat) | code-against-contract |

Pin earlier → premature lock-in (**Hyrum's Law / Postel tension**) ◦; defer past
integration → late-integration surprises (the failure CDC exists to prevent) ◦.

### A.5 Cross-component rollup

`core`'s brief coverage answers "is *this component's* slice shipped?"; the
**whole-feature-intent rollup** ("delivered across all components?") is an
aggregation *above* any single repo — the product pack's job in the meta-repo
(the platform-altitude "measure at the system level" / justify-down step). No
single component repo can do it.

### A.6 Monorepo vs polyrepo (the `monorepo-extras` seam)

Monorepo solves contract-sharing **in-tree** (one `libs/api-interface`, project
graph knows consumers, **atomic "change contract + all consumers in one PR"**) ◦;
polyrepo needs the **meta/contracts repo** *because there is no shared tree* ◦.
The structuring decision stays in `monorepo-extras` (`new-package`); the two
packs meet only at "**where does the shared contract live**." Axiom: monorepos
trade tooling complexity for low coordination cost; polyrepos the reverse ◦.

### A.7 Phase-2 open design questions (for the spec)

- Contract-authority home: meta-repo vs dedicated contracts repo vs schema
  registry (org-specific; reference-by-version is the constant).
- How the meta-repo's Backstage catalog is authored/kept current vs federated
  `catalog-info.yaml` from each component repo.
- Rollup mechanics: how the meta-repo reads per-component brief coverage across
  repos without becoming a runtime hub.
- The precise `architect` seam: does `reference.md` live in the meta-repo, and
  how do component repos reference it.
