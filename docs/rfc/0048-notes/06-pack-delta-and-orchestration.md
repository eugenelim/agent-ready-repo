# Per-pack subagent/skill delta + orchestration design

Net change the operating model implies, by pack. ✦ new · ⊕ modify · ✓ reuse (no change).
The bias is **reuse + a few new pure-markdown skills**, never a new runtime — per RFC-0041/0043.

## Delta by pack

### `core`
- ⊕ **`work-loop`** — gate-ladder doctrine: the G0–G2 + **G1.5** overlay, the surfacing
  predicate, the **three-act human boundary** (originate value · accept irreversible
  risk · **adjudicate value conflicts**), and **stakes-density** right-sizing (down to
  light *and up* for regulated/high-assurance). G3–G5 *are* the existing gates (seam).
- ⊕ **`new-spec` / `receive-brief`** — consume the convergence artifacts (close GAP-O8);
  `receive-brief` gains multi-stakeholder / conflicting-seed intake awareness.
- ✦ **self-coverage gate** — reference library + doctrine (domain-grounding table ·
  pre-mortem · taxonomy walk · saturation · fresh-context adversarial · **scenario-
  variation**); **no new reviewer**. Packaging (library vs skill) = OQ3.
- ✦ **traceability lint** — a tool: *structural* orphan detection along the chain.
- ✦ **sidecar schema** — the shared typed-state contract both loops read (blackboard ·
  open-questions · traceability · decision log); harness-neutral doctrine, the *store* is
  the harness's.
- ⊕ **`security-reviewer` + `quality-engineer`** (agents) — gain a **design-artifact /
  live-lens mode** so they can review a journey/blueprint mid-loop (GAP-O5).
- ✓ **`implementer`, `loop-cohort`** — reused as-is for G4 parallel fan-out.

### `product-engineering`
- ✦ **`discovery-lead`** (agent) + **`discovery-loop`** (skill) — the chief / upstream
  supervisor; an *opt-in product capability*; hard-deps PE's intent skills + `core`'s
  sidecar schema + the G3 handoff; **optional detect-and-degrade** on `research` /
  `experience` / `architect` (lights up as packs are installed).
- ⊕ **`frame-intent`** — multi-stakeholder intake + conflict surfacing; brownfield
  current-state inputs.
- ✦ **`domain-anchor`** — new skill + typed artifact: real-world-activity half **and**
  (brownfield) a current-system half (reverse-engineered); wraps `research` applied mode.
- ⊕ **`de-risk-intent`** — an optional value-conflict assumption kind.
- ⊕ **`voice-and-microcopy`** — cross-linked into the `experience` seat; wired to consume
  the screen inventory (GAP-C1).
- ✓ **`decompose-intent`** — reused (brief authoring + linkage).
- conflict artifact: ✓ **reuse `identify-perspectives`' tension map** (research pack) — no
  new skill.

### `experience` (renamed from `design-craft` — OQ1)
- ✦ **`map-journey`** · ✦ **`blueprint-service`** · ✦ **`inventory-screens`** — the
  connective layer; all three carry the **platform/surface axis** (web · iOS · Android ·
  cross-platform).
- ⊕ **`aesthetic-direction`** — grounded in persona + precedent + standards + platform
  conventions (the taste reference).
- ⊕ **`design-critique`** — evidence-grounded taste mode + platform-fit; can run as the
  design-artifact reviewer.
- ✓ **`design-system-foundations`, `layout-and-information-architecture`, handle-all-states
  floor** — reused (states defer here from `inventory-screens`).

### `architect`
- ⊕ **`architect-design` / `architect-diagram`** — consume the service blueprint;
  brownfield current-state C4 *extraction* (reverse).
- ⊕ **`design-reviewer`** (agent) — optional live-lens mode for design artifacts.

### `research`  — pure reuse, the analyst seat
- ✓ `research` (applied) → domain-anchor · `identify-perspectives` → conflict/tension
  artifact · `decision-archaeology` → brownfield current-state · `devils-advocate` →
  the self-coverage fresh-context pass. **No new skills.**

### `contracts` / `governance-extras` — no change
- ✓ `api-contract` / `event-contract` consume blueprint backstage services.
- ✓ `new-rfc` / `new-adr` produce the child RFCs/ADRs.

### Net
- **New:** 4 skills (`map-journey`, `blueprint-service`, `inventory-screens`,
  `domain-anchor`) + 1 reference-library/doctrine (self-coverage gate) + 1 tool
  (traceability lint).
- **Modify:** `work-loop`, `new-spec`/`receive-brief`, `frame-intent`,
  `aesthetic-direction`, `design-critique`, `voice-and-microcopy`,
  `architect-design`/`-diagram`; agents `security-reviewer`, `quality-engineer`,
  `design-reviewer`.
- **The chief ships as an agent def + convergence-loop skill** (the upstream
  supervisor); only the *harness/runtime* is not shipped (below).

## Orchestration — the "chief" question

**Yes, a chief — shipped as an agent + a convergence-loop skill (the upstream
supervisor), but NOT a runtime.** It is a *peer* of `work-loop`'s supervisor running a
**different loop** (vision→brief, not spec→build); the two hand off at G3 and must not be
conflated. Names: **`discovery-lead`** (agent) + **`discovery-loop`** (loop), resident in
**`product-engineering`** (opt-in product capability; the sidecar schema it reads is
`core` doctrine). Three layers:

1. **The chief = a supervisor of a discovery lens-team, running the gate-ladder doctrine.**
   It holds the blackboard, routes each judgment to its referent or the human (the
   three-act boundary), and renders decision packages at the consent gates. It
   right-sizes: **solo** (small discovery — switches lenses in one context, cheap) or
   **lens-team** (large/multi-discipline — dispatches parallel lens-agents that each
   supervise a domain). Peer of `work-loop`'s supervisor at a different altitude — the
   **upstream convergence loop** (vision→brief), not the **downstream spec-build loop**;
   hand off at G3, never conflate. Shipped as an **agent def + convergence-loop skill**.
2. **The lens-team — multi-agent done the way that works.** Lens-agents (research/analyst ·
   product · UX/design · architecture · **security/compliance**) each supervise their
   domain and **bounce off each other *through the blackboard*** (the open-questions
   ripple), scheduled by `discovery-lead` as controller — the supervisor + blackboard
   topology (LangGraph supervisor, omnigent Polly + cross-vendor review). This is what
   extends autonomy + parallelism. The MAST 41–86% thrash is the *other* pattern —
   agents **negotiating to consensus via chat**; we never do that (controller + blackboard
   mediate, never agent-to-agent negotiation). The team is **loop-scoped**: the discovery
   security/compliance lens (design-time threat-model + compliance) is a *different agent*
   from `work-loop`'s code `security-reviewer`, and the "three reviewers ceiling" is a
   work-loop constraint, not a cap on the discovery roster. Plus the existing
   `implementer`/reviewer fan-out at G4 for disjoint build work.
3. **The harness executes it.** A desktop app coordinating headless Claude Code / Kiro /
   Codex processes provides process management, blackboard persistence, the
   **option-card consent UI** (the headless checkpoint → surface → resume contract),
   team composition, document ingestion, and artifact review. The harness is a **tool**
   (out of the catalogue's charter, Principle 3); the catalogue ships the chief's
   *playbook*, the harness runs it.

**Anti-pattern (rejected):** a "chief" *agent* that specialist agents message/report to
in a hierarchy — CrewAI-style manager routing, which MAST and the CrewAI field reports
show thrashes (output overwrite, token blowup). The chief is the single reasoning
context, not a message router.

`omnigent` answers the harness question (it exists, it works), so what remains is a
**sidecar + chief-loop prototype on `omnigent`** (Decision 7): the typed state sidecar
(blackboard + open-questions + traceability + gate-outcome log) omnigent lacks, the
chief's convergence-loop contract, and the gate rejection/recovery transitions — the
sidecar being the thing that makes "everything holds together" *checkable*.

## Updated flow (with the folded gaps)

`G0 Intake` (value seed; **multi-stakeholder intake surfaces conflicting seeds**) →
`G1 Strategy` → **`G1.5 Domain & MVP`** (domain-anchor: real-activity + brownfield
current-system half; MVP/out-of-scope register) → **convergence loop** (product/UX/tech/
reconcile lenses on the blackboard; UX carries the platform axis; self-coverage gate incl.
scenario-variation; **conflict-adjudication surfaces to the human**) → `G2 Convergence`
(decision package; stakes-density sets gate frequency) → `G3 Spec` → `G4 Build`
(autonomous; tests are the referent) → `G5 Ship` (irreversible; human).
