# Product Engineering Pack — Design Document

Living design reference for the product-engineering pack. Records the philosophy, architecture, invariants, and key decisions so the reasoning survives beyond individual PRs and applies when extending or replacing any skill.

**Related ADRs:** ADR-0019 (product intent ontology and brief projection), ADR-0043 (discovery coordinator is agent + skill + sidecar — no engine), ADR-0033 (intent Level is an open recognized set decoupled from Scale)

---

## TL;DR

`product-engineering` is the upstream shaping seat. Every product idea gets one path — frame → de-risk → decompose — over a single recursive artifact (the `intent`) that spans every altitude from product-vision to feature. `discovery-loop` is the supervised peer of `work-loop`: it diverges across candidate shapes, drives a lens roster to convergence, pauses at four human consent gates, emits a connected hypothesis with validation hooks, and hands the brief to the delivery loop at G3. The whole capability is content, not runtime — a `discovery-lead` agent definition, this skill, and a carried sidecar schema, executed by the harness an adopter already runs. `ux-writing` is the content layer: it writes the words users read in the UI, keyed to the per-screen state matrix produced by `experience-design`.

---

## Non-Goals

Things a reasonable reader might expect this pack to solve. It doesn't, by design:

- **Live tracker API sync.** The pack ships the one-way projection mapping (intent tree → Linear / Jira Align records). A live, bidirectional sync is a separate, later pack.
- **Wire-contract authoring.** That's the spec stage's `Contract:` seam in the `contracts` pack. This pack stays behavioral — it does not author interface contracts or API schemas.
- **Monorepo-vs-polyrepo structuring.** That decision lives in `monorepo-extras` (`new-package`). This pack meets it only at "where the shared contract lives" inside a value-stream meta-repo.
- **Subagents beyond the discovery roster.** The discovery roster is loop-scoped and capped: two required reviewers (threat + reliability) plus optional UX/research/architect lenses if installed. Shaping is a skill, not a multi-agent mesh; the harness handles the mesh layer.

---

## 1. The intent model

### One artifact at every altitude

The `intent` is the single recursive artifact of this pack. A product-vision intent, a product-strategy intent, a capability intent, and a feature intent are the same data structure at different altitudes — outcome + opportunity + assumptions + decomposition pointer. A PRD is a feature intent written as a long-form document; a strategy doc is a product-strategy intent. Nothing changes about the artifact as you descend the tree; only the altitude field changes.

This means decomposition is recursive by construction: `decompose-intent` produces the next level down from whatever level it receives, and stops when the leaf is a unit the delivery loop can build — at `app` Scale, that leaf is an ordinary `core` brief.

### Level is an open recognized set

The recognized set runs `product-vision › product-strategy › capability › feature` and is **open**: an organization may name an intervening level (program epic, initiative, theme, domain bet) and the pack accommodates it without requiring a mapping back to the four canonical names. The recognized members are not exhaustive — they are stable anchors. Inserting `program-epic` between `product-strategy` and `capability` is valid; the intent model assigns it a parent and decomposition works the same way.

This is different from a flag-parameterized enum. An open set means the altitude field accepts any string the organization recognizes, not only the four names the pack ships with.

### Scale resolved at intake, decoupled from Level

`Scale` (app ↔ business-unit) is resolved once at intake — inferred from the workspace and confirmed with the user — and stamped on the `docs/product/` root. It determines *where* decomposition fans out (same repo vs. per-component cross-repo briefs) but not *what altitude* the intent lives at. A business-unit capability intent and an app capability intent are the same level; they decompose differently. Decoupling the two axes prevents Scale from silently constraining the altitude the framing picks.

---

## 2. The discovery loop

### The loop model

```
   raw idea
      │
    G0 ── frame-intent ─────────────────── intent
      │
    G1 ── de-risk-intent ─── explore-options ─── candidates
      │
   G1.5 ── lens roster ─────────────────── filtered candidates
      │
    G2 ── discovery reviewers ──────────── decision-brief
      │
    G3 ── decompose-intent ──────────────── briefs → work-loop
```

The loop cannot advance past a consent gate (G0, G1.5, G2, G3) without a harness-attested human verdict. Between consent gates, non-consent steps (G1, the convergence loop) auto-advance unless a risk trigger fires.

### Content, not runtime

The whole discovery capability is content: a `discovery-lead` agent definition, the `discovery-loop` skill, and a carried sidecar schema in plain files. The harness an adopter already runs executes it. What the pack does not ship — and must not ship — is a runtime coordinator, message bus, convergence solver, or state-machine engine. The recursion is data (status fields per node); the bounds are counters; the verdict set is status edits plus a recorded row in the decision log.

This is the no-engine principle (ADR-0043): the spike confirmed that a single reasoning context over plain files can run the discovery loop without a coordinator service. The depth/breadth bounds are explicit — the loop pauses and confirms when it hits them rather than auto-terminating.

### Converged ≠ validated

The brief the loop emits is a **connected hypothesis**. Every load-bearing assumption carries a validation hook: the predeclared kill condition plus the real-world activity that would confirm or enrich it. Desk-grounding is not validation; the loop says so structurally by flagging surviving bets whose only evidence is desk research as `to-validate`, not `grounded`.

---

## 3. Human gate design

### The four gates

| Gate | When | Duration | What to check |
|------|------|----------|---------------|
| **G0** | After `frame-intent` emits the initial framing | 10–15 min | Is the problem specific enough to eliminate candidates? Is the user named? Is the outcome measurable? |
| **G1.5** | After `explore-options` and the first lens-roster pass | 15–20 min | Which candidates survived? Is the field differentiated? Is anything missing? |
| **G2** | After the full lens-roster pass on surviving candidates | 20–30 min | Did the discovery reviewers flag anything blocking? Does the hypothesis have a validation hook? Is the decomposition sized for one loop iteration? |
| **G3** | After the reconciliation record is ratified | 5 min | Is the brief complete? Is there anything you are not prepared to build? |

### Why four gates, not two

`work-loop` has two gates because delivery has two human-irreplaceable decisions: agree the plan before code starts, and approve the diff before it merges. Discovery has more because the option space is open when the loop begins and must be narrowed across several human acts before a build commitment is valid.

G0 is the framing gate: a vague problem means the divergence step explores the wrong space — no amount of convergence fixes a bad framing. G1.5 is the option-space gate: the last cheap moment to expand or reject candidates before the lens roster runs on the survivors. G2 is the reconciliation gate: is the brief complete and are the reviewers clean? G3 is the commit gate: am I ready to build this, not just "is the brief complete?" These are two distinct decisions — collapsing them removes the deliberate pause between "this is a good brief" and "I am ready to act on it."

### Consent gates are a pause, not a runtime

A consent gate is a file write and a wait. `discovery-lead` sets `status: awaiting-human` on the sidecar, emits an option card, and stops. The harness surfaces the option card; the human's typed verdict is written to the append-only decision log through a channel the agent has no token for. The next round reads the log and resumes. There is no gate service, no webhook, no timeout — just a file and a convention.

---

## 4. The sidecar

### What it is

The sidecar is the coordination artifact the discovery loop carries through every phase. It is a versioned plain file (schema in `references/sidecar-schema.md`) that holds:

- The intent tree — one node per initiative and sub-idea, each with `status`, `round`, `cost_spent`
- The decision log — append-only, per-row actor attestation, SHA-256 hash-chain
- The convergence slots — one per lens (intent, domain-framing, assumption-test, decision-brief)
- The open-questions queue — the only channel through which parallel lens-agents coordinate without chat

### Where it lives

The sidecar lives in the harness's own store or branch, **never the product repo's main line**. This is a deliberate separation: working discovery state (including sensitive strategic assumptions and preliminary architecture decisions) is not a committed artifact until G3. After G3, the decision brief is promoted into `docs/product/` as a durable artifact; the sidecar remains in the harness store.

### Why the sidecar, not a database

A plain versioned file is readable by any tool, diff-able in review, and requires no service to maintain. The sidecar's append-only decision log is the audit trail; the `schema_version` field provides migration compatibility. A database would require an operator, a connection, and a migration story — none of which the no-engine principle permits.

---

## 5. The ux-writing content layer

### What it covers

`ux-writing` writes the words users read in the UI: error messages, empty states, button labels, form labels. It is a method, not a word bank — voice characterization along a few axes (humor, formality, respect, enthusiasm), per-state formulas (blame-free + actionable), and a content checklist before copy ships.

### The design-seat pairing

`ux-writing` is the content layer of the design seat:

- **`experience-design`'s `user-flow`** produces the per-screen state matrix (one row per screen × state). Pass that matrix to `ux-writing` and it writes copy keyed to every cell — one string per screen/state combination.
- **`experience-design`'s `tone-of-voice`** sets the brand register: ranked copy goals and arbitration rules. `ux-writing` receives the voice direction and applies it per state.
- **Without a screen flow**, `ux-writing` is still fully useful: it detects absent and names states inline. The pairing is additive, not required.

### Scope boundary

`ux-writing` covers product UI copy: error states, empty states, button labels, loading messages. Marketing and acquisition copy (hero headlines, above-fold narrative, taglines, onboarding copy voice) belongs to `experience-design`'s `copy-direction`. Brand-level copy register belongs to `experience-design`'s `tone-of-voice`. Onboarding narrative arc and structure belongs to `experience-design`'s `content-design`. Documentation prose belongs to `new-guide`. The boundary is the surface type: UI state copy lives here; everything else does not.

---

## 6. Cross-pack dependencies

### Upstream: product-strategy

The `product-strategy` pack is the strategic anchor this pack builds on. Before `frame-situation` or `frame-intent` runs, a strategist may have committed altitude-0 artifacts to `docs/product/shaping/`: OKR cascade (`okr-cascade.md`), market context, portfolio position, stakeholder synthesis. `frame-situation` routes strategy-typed shaping-queue entries into the six-step shaping sequence; `frame-intent` uses market context as grounding when present. Both inputs are optional — the skills degrade gracefully when absent.

### Downstream: core (the G3 handoff)

At G3, `discovery-loop` hands the ratified decision brief to the delivery loop unchanged. The hand-off interface is `receive-brief` → `new-spec` → `work-loop`. No new machinery. At `app` Scale each leaf brief is an ordinary `core` brief; at `business-unit` Scale each leaf brief is a per-component slice that crosses into its component repo where the same delivery loop takes over.

### Downstream: experience-design

The per-screen state matrix from `experience-design`'s `user-flow` is the hand-off artifact `ux-writing` consumes. Each cell in the matrix (screen × state) maps to a copy string. The two packs are designed to meet at this interface. When discovery includes UX lens work, `experience-design` skills run inside the convergence loop as optional lens participants; when they are absent, the discovery floor degrades gracefully to product-only discovery.

---

## 7. Safety invariants

These constraints must never be violated by any skill in this pack or any skill that extends it.

1. **No engine, no hooks, no validators, no runtime hub.** The coordination is a file write and a convention. Any skill that ships a coordinator process, message bus, or convergence service violates the no-engine principle.

2. **The loop cannot advance past a consent gate without a harness-attested human verdict.** A gate is not passed because the agent judged the work ready. The loop's self-assessment is inadmissible as gate evidence.

3. **The security lens is non-degradable on a security boundary.** `discovery-threat-reviewer`'s depth keys on a risk trigger; a security-boundary crossing with only baseline depth surfaces to the human rather than degrading silently. Degrading silently is not a valid fallback.

4. **Sidecar goes to the harness store, never the product repo's main line.** Working discovery state — including sensitive assumptions, preliminary architecture decisions, and unratified candidates — is not committed until G3.

5. **Converged ≠ validated.** The decision brief emitted at G3 is a connected hypothesis. Every load-bearing assumption carries a validation hook. A brief that omits the validation hook on a to-validate assumption is not a valid G3 output.

6. **A lens only proposes; only the controller promotes.** A lens agent writes to its own slot; it does not promote ratified slots, write trusted edges, or self-assert `ratified-by: human` rows. The integrity of the decision log depends on this.

---

## 8. Design decisions and rationale log

### Why Level is an open recognized set (ADR-0033)

Organizations operate with different altitude names between vision and feature: program epics, domain bets, initiatives, themes, product areas. A closed four-tier hierarchy would require every organization to map their naming to the pack's names — friction without benefit. An open set names the recognized anchors (`product-vision › product-strategy › capability › feature`) but permits insertion of org-specific levels. The recognized members retain their semantics; the org adds what it needs above, below, or between them without breakage.

**Alternative considered:** a closed four-tier hierarchy with a `custom-level` escape hatch (a string field on the intent for orgs that don't fit). Rejected because the escape hatch becomes the default within one sprint — teams stop using the recognized names and the recognized semantics evaporate. An open set with documented anchors preserves the semantics for orgs that use them while not blocking orgs that don't.

### Why Scale is decoupled from Level (ADR-0033)

Scale (app vs. business-unit) determines *where* decomposition fans out — same repo versus per-component cross-repo briefs. Level determines *what altitude* the intent lives at. Before decoupling, Scale implicitly suggested a Level ceiling: a business-unit brief was assumed to be `capability` level. This made it impossible to author a business-unit `feature` intent (a cross-component feature that is still a feature, not a capability). Decoupling removes the implicit ceiling: Scale stamps on the `docs/product/` root once; Level is picked per intent without Scale bias.

**Alternative considered:** keep the coupled model and document the suggested altitude per Scale. Rejected because "suggested" always becomes "required" in practice — the documentation overhead of the exception is higher than the cost of the decoupling.

### Why habits, not infrastructure (ADR-0043)

The discovery loop's coordination is a file write plus a plain-text convention, not a service. The spike confirmed this: a single reasoning context walking a status-annotated plan tree over plain files runs the discovery loop without a coordinator service, message bus, or state-machine engine. The no-engine principle keeps the pack content-only — no process to start, no service to maintain, no version mismatch between the loop's runtime and the adapters that run it. The only code the pack ships is a ~60-line connectedness lint; everything else is content.

**Alternative considered:** a lightweight coordinator microservice that handles persistence, gate-enforcement, and concurrent lens coordination. Rejected because: (a) every adopter would need to operate the service, creating a dependency the pack's user-scope install doesn't warrant; (b) it introduces a versioning seam between the pack and the coordinator; (c) the spike confirmed the in-context model is viable at the depth/breadth bounds the pack documents. Scheduling many concurrent or long-parked threads across initiatives remains the harness's job.

### Why four gates, not two (from day one)

`work-loop` has two gates because delivery has two irreducible human decisions: agree the spec before code starts, and approve the diff before it merges. Discovery starts with an open option space and must narrow it across multiple acts before a build commitment is valid. Collapsing G0 and G1.5 means an unconverged framing drives a full lens-roster run — expensive work on candidates that a ten-minute framing review would have eliminated. Collapsing G2 and G3 removes the deliberate gap between "is this brief complete?" (a quality question) and "am I ready to build this?" (a commitment question). They are different cognitive acts; conflating them degrades both.

**Alternative considered:** two gates mirroring `work-loop` — one before divergence (approve the framing), one before handoff (approve the brief). Rejected because a single mid-loop consent point means either the diverge step runs without framing approval (high waste on bad framings) or the convergence step runs without candidate confirmation (converges on a candidate the human would have redirected at G1.5). The asymmetry in cost — cheap gate vs. expensive loop iteration — strongly favors more gates, not fewer.

### Why ux-writing lives in product-engineering, not experience-design (from v1)

`ux-writing` writes the words users read in the product UI. It is a product-engineering skill because the decision of what to say in an error or empty state is a product-content decision, not a design-methods decision. `experience-design` sets the surface intent (what the screen is trying to accomplish) and derives the state matrix (what states exist per screen); `ux-writing` writes the copy for each state. The two packs meet at the state matrix interface. Placing `ux-writing` in `experience-design` would create a pack that conflates method (how to structure screens) with content (what words go in them) — and would make the content layer unavailable to teams that want to write copy without running the full design sequence.

**Alternative considered:** place `ux-writing` in `experience-design` as a terminal craft step, after `interaction-design`. Rejected because: (a) product teams write copy without running a full design thread — the content layer should be independently usable; (b) the design seat's method principle is "derive, never prescribe" with no values tables — `ux-writing`'s copy output is content, not method, and doesn't fit that principle; (c) the product-engineering pack already owns the product-content layer (`decompose-intent` produces feature intents; `ux-writing` writes the words those features render).
