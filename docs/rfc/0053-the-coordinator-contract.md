# RFC-0053: the coordinator contract — `discovery-lead`, the typed sidecar, and the no-engine framing, confirmed by prototype

- **Status:** Open <!-- Draft | Open | Final Comment Period | Accepted | Rejected | Withdrawn | Experimental -->
- **Author:** eugenelim
- **Approver:** eugenelim
- **Date opened:** 2026-06-26
- **Date closed:**
- **Related:** [RFC-0048](0048-autonomous-product-team-operating-model.md) (the foundation — this is **child 5**, the coordinator spike→RFC for Decisions 7 + 8; the provisional foundation this drift-aligns back to) · [RFC-0049](0049-the-release-loop-and-company-os.md) (the sibling *downstream* outer loop — `release-lead` + `release-loop`, the same agent-def + skill + harness pattern this RFC establishes upstream; both build on the same RFC-0048 substrate (the sidecar + the gate arc), and this RFC specifies the sidecar schema RFC-0049's release loop would also consume) · [RFC-0051](0051-the-self-coverage-gate.md) (the self-coverage gate — `discovery-loop` is its **second controller**; the gate is `discovery-loop`'s pre-G2 phase, seam specified there, wired here) · [RFC-0050](0050-the-experience-pack.md) (the `experience` lens this loop detect-and-degrades on) · [RFC-0041](0041-infra-aware-work-loop.md) + ADR-0031 (the *doctrine + reference library + reuse, no engine/no new reviewer* precedent the framing rests on) · RFC-0025 (`work-loop` light/full + the iteration cap this loop's outer cap mirrors) · RFC-0040 (the three-tier layout resolution the sidecar paths obey) · RFC-0019 (`receive-brief` — the brief→spec join at G3; its coverage lint child-4's traceability lint generalizes) · [ADR-0022](../adr/0022-value-stream-meta-repo-cross-component-layer.md) (the cross-repo reference-by-version mechanism the traceability slot reuses) · [`docs/specs/traceability-lint/`](../specs/traceability-lint/spec.md) (child-4 — the lint that consumes the traceability slot) · promoted research + the empirical prototype in [`0053-notes/`](0053-notes/); [`0048-notes/09`](0048-notes/09-gap-resolutions.md) (the paper resolutions this spike confirms) and [`0048-notes/02`](0048-notes/02-worked-example-flow-trace.md) (the worked example it was run against)

## The ask

**Recommendation (BLUF).** Adopt the **coordinator contract** the RFC-0048 Decision-7 spike
was meant to validate — and **ship it the way RFC-0041/0049 ship their loops: a
`discovery-lead` agent definition + a `discovery-loop` skill (content, like `implementer`)
+ the typed sidecar *schema* as a carried contract in the producing skill — no new runtime engine.** A timeboxed
**empirical prototype** ([`0053-notes/`](0053-notes/)) ran the loop against the worked
example ([`0048-notes/02`](0048-notes/02-worked-example-flow-trace.md)) on the form
`omnigent` stores (worktree files). On that **one worked example, walked once by a single
operator** (not replicated — the honest limit, flagged in the spike's Threats), every
transition — altitude descent, the answer-each-other ripple, gate rejection/recovery with
cascade-invalidation, saturation, and the outer cap *modelled* (it converged early and the
stall path was not hit live) — was performed by **one reasoning context editing four plain
files**, with a single ~60-line *lint* (not a coordinator) as the only executable. That
lint is the **reproducible** artifact: it flagged the injected defects pre-recovery and
reported converged after. The framing the prototype supports — *no engine is needed* — thus
moves from RFC-0048's stated hypothesis to a demonstration on one example plus a
reproducible connectedness check, which is what closes (with the residual scale risk named)
the one assumption RFC-0048's spike section left open for the coordinator.

**Why now (SCQA).** *Situation:* RFC-0048 decided the operating model and **resolved the
coordinator's design blockers on paper** ([`0048-notes/09`](0048-notes/09-gap-resolutions.md):
O11 rejection/recovery, O12 outer cap, A1 checkpoint/resume, A2 decision schema, A3 team
composition, O5 live lenses, O6 saturation), then deliberately *built nothing* — it
authorized a **spike, not a build** (D7), because the coordinator's Principle-3 fit was the
initiative's riskiest assumption and the only one demonstrated *for D1–D6 but merely
hypothesized for the coordinator*. *Complication:* a paper resolution is not a confirmation;
RFC-0048 is explicit that the spike's job is to **confirm the resolutions empirically via a
prototype on `omnigent`** — and until that runs, "the coordinator is doctrine, not an
engine" is an assertion, and the contract an adopter or a bespoke harness must implement is
unspecified. *Question:* does the convergence loop + its typed state survive contact with the
worked example as engine-free content, and what exactly is the harness-neutral contract?

**Decisions requested.**

1. **Adopt the no-engine coordinator contract — `discovery-lead` (agent) + `discovery-loop`
   (skill) in `product-engineering`, the sidecar *schema* carried in the `discovery-loop` skill — confirmed by the
   prototype.** The spike refutes the failure mode (no transition needed a scheduler, bus,
   or convergence solver); the catalogue ships content + schema, the harness supplies the
   store and gate enforcement. · *why:* it is the one D7/D8 claim that was hypothesized, now
   demonstrated; it is the spine every step of the operating model hangs from. · decide-by:
   RFC accept · default: adopt (spike-confirmed).
2. **Ship the typed sidecar schema as a carried contract in the producing skill — the connectedness verifier.** (Not `core` — RFC-0048 § Amendments 2026-06-26.) The
   slots `blackboard` · `open-questions` · `traceability` · `decision-log`, each typed to a
   named schema, harness-neutral; the **store is the harness's** (omnigent's worktree).
   Paths resolve config → default → discover-by-marker (RFC-0040), never hardcoded. · *why:*
   omnigent's worktrees hold artifact *files*; only this typed state makes "everything holds
   together" *checkable* — and the prototype showed a ~60-line lint over it suffices. ·
   decide-by: RFC accept · default: adopt.
3. **Adopt the gate state machine — consent checkpoint/resume (A1/A2) + rejection/recovery
   with cascade-invalidation (O11).** A consent gate writes the decision brief, sets
   `status=awaiting-human`, surfaces an option card, records the verdict to the decision
   log, and resumes. A rejection emits reason→correction, re-enters the gate's phase,
   **cascade-invalidates downstream blackboard slots by walking the traceability edges**
   (mark stale, drop their edges), and re-runs only the affected lenses — the edge set
   *scopes the blast radius*. · *why:* the prototype ran this as a markdown+JSON edit, not a
   framework call; it is what makes a rejection cheap and bounded. · decide-by: RFC accept ·
   default: adopt.
4. **Adopt the outer cap + cost budget (O12).** `discovery-loop` carries an outer round cap
   and a cost budget (tunable defaults); on cap-with-unconverged-state the loop **does not
   loop forever** — it writes a stall record and **surfaces to the human** (surfacing
   predicate clause c). · *why:* the same safety valve `work-loop`'s cap and omnigent's
   `cost_budget` provide, lifted to the upstream loop; the prototype confirmed the counter
   is a `meta` field the controller increments, no runtime. · decide-by: RFC accept ·
   default: adopt (defaults: 12 rounds / a per-initiative cost budget, tunable).
5. **Adopt the supervisor topology — solo / lens-team right-sizing + a loop-scoped lens
   roster, MAST-safe by construction.** `discovery-lead` right-sizes between **solo**
   (switches lenses in one context) and **lens-team** (dispatches parallel lens-agents that
   bounce off each other *through the blackboard*, never agent-to-agent chat). The discovery
   roster is **loop-scoped** and distinct from `work-loop`'s three code reviewers. · *why:*
   the prototype's ripple settled with zero negotiation-to-consensus — the MAST guardrail
   held by topology, not by limiting the roster. · decide-by: RFC accept · default: adopt.

## Problem & goals

**Diagnosis.** RFC-0048 did the hard *design* work for the coordinator and recorded it
honestly as **resolved-on-paper** (note 09). What it could not do — by its own choice to
spike rather than build — is **confirm those resolutions empirically** and **specify the
contract** that survives. Two concrete gaps remain after RFC-0048:

1. **The no-engine claim for the coordinator was a hypothesis, not a demonstration.**
   RFC-0048's Evidence section is explicit: the no-engine verdict is *demonstrated for
   D1–D6* (they add only markdown, a reference library, a typed artifact, and a lint) but
   for the **coordinator** it is *a hypothesis* — "`loop-cohort` covers none of O1/O2/O3/O5/O7
   today, so the doctrine-not-engine fit is exactly what the Decision-7 spike must confirm."
   Nothing had been run.
2. **The contract was unspecified.** "A typed sidecar", "rejection/recovery transitions",
   "an outer cap", "checkpoint/resume" name *what* must exist; an adopter — or a future
   bespoke harness — needs the *schema and the transitions* written down, harness-neutrally,
   to implement against. Note 09 resolved the design; it did not write the contract.

This RFC closes both: it **runs the prototype** (Decision 1; [`0053-notes/`](0053-notes/))
and **writes the contract** the prototype validated (Decisions 2–5).

**Goals.**
- **Confirm the no-engine framing for the coordinator empirically**, against the worked
  example, on the form the reference harness stores — turning RFC-0048's hypothesis into a
  result.
- **Specify the harness-neutral contract**: the sidecar schema, the gate state machine, the
  outer cap, the supervisor topology — concrete enough that an adopter or a bespoke harness
  implements it without re-deriving it.
- Ship as the **RFC-0041 idiom** — doctrine + an agent def + a skill + a schema, with the
  design-time lens roster RFC-0048's authoritative roster table fixes (its own
  `discovery-threat-reviewer` / `discovery-reliability-reviewer`, not `work-loop`'s code
  reviewers) — so the capability is a *way of working*, not a runtime (CHARTER Principle 3).
- Keep `discovery-loop` **useful at the floor** (product-only discovery with just
  `product-engineering` + `core`) and **progressively enhanced** as lens packs install.

**Non-goals** (could-have-been goals, deliberately dropped).
- *A new orchestration runtime / engine / daemon / service.* The thing the spike was
  designed to prove unnecessary — and did (Decision 1; CHARTER Principle 3; RFC-0048 Option
  C).
- *Building or forking the harness.* `omnigent` exists and is the reference runtime; we
  ship the contract it (or a successor) enforces, not the harness (RFC-0048 non-goal;
  RFC-0041 P4 harness-neutrality).
- *The `experience`, `architect`, `research`, and security/compliance **lens skills
  themselves.*** Those are RFC-0050 (child-1) and reused packs; this RFC wires them as
  *optional detect-and-degrade lenses*, it does not author them.
- *The traceability lint.* Child-4 (`docs/specs/traceability-lint/`) builds the lint; this
  RFC defines the **traceability slot** the lint reads and the **cascade-invalidation**
  transition that walks its edges. The spike's `check_sidecar.py` is a *demonstrator*, not
  the shipped lint.
- *The self-coverage gate's modules.* RFC-0051 (child-3) ships the gate; this RFC names it
  as `discovery-loop`'s pre-G2 phase (the seam RFC-0051 specified for its second controller).
- *The downstream / deploy loop.* `work-loop` (G3–G5 build) is unchanged; the
  release/deploy outer loop is RFC-0049's `release-lead`. This RFC is the **upstream**
  (G0–G2) coordinator only; the two loops hand off at G3 and must not be conflated.
- *Multi-week project statefulness beyond one initiative.* One `discovery-loop` run = one
  decision brief = one backlog (note 08); cross-initiative memory is the harness's
  (omnigent's documented gap), not this contract's.

## Proposal

Cascaded under the requested decisions. The detail and the worked artifacts live in
[`0053-notes/`](0053-notes/); this section states the contract.

### Decision 1 — the no-engine coordinator contract (the shape, confirmed)

`discovery-lead` ships as an **agent definition** and `discovery-loop` as a **skill**, both
in `product-engineering` (an opt-in product capability — `discovery-loop` is
product-discipline-specific, so it ships in the product pack an adopter chooses, not the
universal `core`; the *sidecar schema* it carries lives in the `discovery-loop` skill, not `core`). This is precisely the
`implementer`-shape precedent: shipping an agent def + a loop skill is shipping **content**,
not a runtime — what Principle 3 forbids is the harness, which we do not ship.

`discovery-lead` is the human-facing **upstream supervisor**, a *peer* of `work-loop`'s
supervisor and `implementer`. It runs `discovery-loop` (intents → frame-domain →
blackboard convergence → decision brief at consent gates → emits briefs/specs), holds the
blackboard in **one reasoning context**, fans out only to disjoint workers, and talks to the
human at the consent gates. It is **not** `work-loop`'s supervisor: `work-loop` supervises
the *downstream* spec→build loop; `discovery-lead` supervises the *upstream* vision→brief
loop; they **hand off at G3**.

*What the prototype confirmed.* The riskiest assumption — that orchestrating the loop needs
a runtime engine — is **refuted**. Walking the worked example G0→G2 as one context, with the
two named failure modes (over-scope; an unbacked security-sensitive screen) deliberately
injected, every transition was a file edit plus, at most, a lint. See Evidence and
[`0053-notes/01-spike-report.md`](0053-notes/01-spike-report.md).

### Decision 2 — the typed sidecar schema (carried contract in the producing skill)

> **Revised per RFC-0048 § Amendments 2026-06-26 (scope-decoupling).** This decision
> originally shipped the schema as **`core` doctrine**. Because `discovery-loop`'s owning
> pack `product-engineering` is user-scope and must run portably (Obsidian vault / non-repo),
> the schema *definition* is now a `references/` file **carried in the `discovery-loop`
> skill**, not single-sourced in repo-scope `core`. There is no shared cross-pack layer (the
> skills spec has none): downstream consumers — the traceability lint, `work-loop`, the
> release loop — **read the produced `_state/` instances by convention + a `schema_version`
> stamp**, they do not import the definition. "Versioned contract" = the instances carry
> `schema_version` and consumers check compatibility. The slot field-set below is unchanged.

The typed state both loops share, its *definition* carried in the producing `discovery-loop`
skill (harness-neutral); the *store* is the harness's (omnigent's git-worktree). The slots,
with their schemas as the prototype instantiated them ([`0053-notes/spike/`](0053-notes/spike/)):

- **blackboard** — the typed artifact slots (= the artifact inventory, note 04), each
  `{id, type, lens, status ∈ draft|proposed|ratified|stale|rejected, version, produced_by,
  path?, round_last_touched}`, plus a `meta` block carrying the round counter, the cost
  budget, the gate, and the saturation state.
- **open-questions** — the queue lenses answer each other through:
  `{id, raised-by, target-discipline, question, status ∈ open|routed|resolved|surfaced,
  resolution, round}`.
- **traceability** — the `outcome→…→component` edge set the lint checks (orphan = defect):
  typed `nodes` (each with a `kind` and a `backed_by ∈ file|container|ladder` — the child-4
  reconciliation that four chain rungs are intent-ladder rungs or journey/blueprint-embedded
  entries, not files) and `edges`, with a `root` and `leaf_kind`. Node ids are stable,
  location-independent markers (slug / `contract@version` / Backstage `kind:namespace/name`),
  so the chain crosses repo boundaries by convention not path (the ADR-0022 reuse RFC-0048's
  amendment already recorded).
- **decision-log** — `{ts, gate, decision, ratified-by ∈ human|discovery-lead,
  reversibility-class, rationale}` (canonical field order, used in the body and the spike
  artifacts alike); a **decision record** that becomes the audit trail the high-stakes /
  regulated case needs (RFC-0048 D1 stakes-density) **only with the integrity properties the
  implementing spec must carry** — append-only, an attested ratifier (a `human` row the
  controller cannot forge), tamper-evidence, and a trusted timestamp (see § Security &
  integrity contract). As a plain mutable file it is a record, not yet an audit trail; the
  contract names the gap rather than implying the schema closes it.

The sidecar is the **connectedness verifier**: the prototype's `check_sidecar.py`
(child-4's lint shape) read the traceability + open-questions slots and reported orphans
pre-recovery and CONVERGED after — connectedness is checkable in ~60 lines, no engine
(Decision 2's load-bearing empirical claim). Paths obey RFC-0040's three tiers; each
producing skill creates its dir lazily on first write.

*Schema home.* The schema ships as a **small `core` schema reference** — the
`operational-safety` / `self-coverage` reference shape, **not** a self-discovered skill — so
that child-4's traceability lint, RFC-0049's release loop, and `discovery-loop` all cite
**one source** for the slot shapes. The exact file layout is a spec-time detail; that the
home is a single `core` reference (not duplicated prose in `work-loop`, not a skill an agent
must choose to load) is decided here.

### Decision 3 — the gate state machine (checkpoint/resume + rejection/recovery)

*Consent checkpoint/resume (A1/A2).* A consent gate (G0, G1.5, G2; G5 is RFC-0049's) is a
pause, not a special runtime: `discovery-lead` writes the **decision brief** to the
blackboard, sets `status=awaiting-human`, and emits an **option card** —
`{gate, summary, decisions-requested, recommended, reversibility-class, artifacts}` (A2). The
harness surfaces it (omnigent's human-in-the-loop pause; a Claude-Code plan-mode-style
read-only state); the human's verdict is written to the decision log; the next round reads
the log and resumes. Non-consent gates auto-advance unless a risk trigger (RFC-0025) fires.

*Rejection/recovery with cascade-invalidation (O11).* A rejection (a human "no" at a
consent gate, or a lens invalidating a prior slot) runs, in the controller's own context:

1. emit `reason → correction`; re-enter that gate's phase;
2. **cascade-invalidate downstream blackboard slots by walking the traceability out-edges**
   from the rejected node — mark each `stale`, drop its edges from the active matrix;
3. re-run **only the affected lenses** on the reduced surface.

The edge set *scopes the blast radius* — the whole reason the matrix is typed. The
prototype ran this for the fulfillment over-scope: the human rejected
`cap.external-fulfillment` at G1.5, the walk marked `screen:fulfillment` +
`service:fulfillment` stale and dropped their edges, and only the UX lens re-ran (see
[`0053-notes/spike/loop-trace.md`](0053-notes/spike/loop-trace.md) §O11). This is the
LangGraph-checkpointer / plan-mode reject→revise shape (note 09 O11), realized as a state
edit, not a framework call.

*The answer-each-other ripple (O5).* Lenses bounce off each other **through the
open-questions queue and the blackboard**, never by chat. The reconcile lens runs
`product-engineering`'s **own user-scope design reviewers** (the discovery security/quality
lenses — distinct names from `core`'s code reviewers, degrading to `core`'s depth library when
present; RFC-0048 § Amendments 2026-06-26, revising the original "core reviewers in a mode"
reading of O5) over the journey/blueprint mid-loop. The prototype's OQ-3 settled
security→product→tech→ux→design
as queue-status + blackboard edits with **zero agent-to-agent negotiation** — the MAST
guardrail held by topology (Decision 5).

### Decision 4 — the outer cap + cost budget (O12)

`discovery-loop`'s `meta` block carries `round`, `round_cap`, `cost_budget`, and
`cost_spent`. The loop increments `round` per convergence pass. On
`round == round_cap` **or** `cost_spent ≥ cost_budget` **with any open/routed OQ or any
orphan remaining**, the loop **does not churn forever**: it writes `status: stalled-at-cap`
to the decision log and **surfaces to the human** (surfacing predicate clause c — a loop
that cannot converge). Defaults are tunable (recommended: 12 rounds; a per-initiative cost
budget). The prototype converged at **round 4 of 12, $6.40 of $25** — so the stall path was
*modelled, not hit live* (an honest gap, flagged in the spike's Threats; the transition is a
counter-compare grounded in `work-loop`'s cap + omnigent's `cost_budget`, no runtime).

### Decision 5 — the supervisor topology (solo / lens-team; loop-scoped roster)

`discovery-lead` right-sizes:
- **Solo** (small discovery) — holds the blackboard in one context, switches lenses itself
  (cheap, no coordination cost). The prototype ran solo.
- **Lens-team** (large, multi-discipline) — dispatches **parallel lens-agents** that each
  supervise their domain (research/analyst · product · UX/design · architecture ·
  security/compliance) and **bounce off each other through the blackboard** (the
  open-questions ripple), with `discovery-lead` as controller — the proven supervisor +
  blackboard topology (LangGraph supervisor; omnigent Polly + cross-vendor review), **not
  chat negotiation**. This extends autonomy and parallelism without MAST thrash, because the
  thrash is the *other* pattern (agents negotiating to consensus via chat), which the
  blackboard + controller mediation never does.

The discovery roster is **loop-scoped** and authoritatively defined by RFC-0048's roster
table — this RFC adds no roster of its own. The discovery **security/compliance** and
**quality/reliability** lenses are *design-time* roles (threat-modeling + regulated-domain
compliance, and reliability/operability, over the journey/blueprint/architecture), carried
by `product-engineering`'s **`discovery-threat-reviewer`** and
**`discovery-reliability-reviewer`** — **distinct agents from `work-loop`'s code
`security-reviewer` / `quality-engineer`**, by exact name (the collision-hardening RFC-0048's
table requires). So the charter's "three reviewers is the ceiling" is a
`work-loop`/code-review constraint; the discovery loop carries its own design-time lens
roster (RFC-0048's roster table — disciplined, not a marketplace; the CHARTER's reviewer
ceiling itself stays a `work-loop`/code-review cap, recorded as a tracked RFC-0048 amendment
by this child — see Follow-on artifacts). **Lens conflicts:** factual disagreement →
`discovery-lead` arbitrates via referents on the blackboard; *value* disagreement (security
says no, product says ship) → the human at G2 (the conflict-adjudication act). **Progressive
enhancement (A3):** hard deps are `product-engineering`'s intent skills + the carried
versioned sidecar-schema contract (harness-neutral, travels with its producer pack — RFC-0048
§ Amendments 2026-06-26) + the G3 handoff + the two `product-engineering` discovery reviewers,
**required at G2 reconcile** and degrading only in *depth* (their own baseline checklists when
`core`'s `security-checklists` / `operational-safety` + `quality-engineer` depth is absent,
never to nothing). The `research` / `experience` / `architect` lenses are the optional
detect-and-degrade set — product-only discovery alone, lighting up as packs install. The
"team" is the installed lens-packs + a thin team-manifest; omnigent YAML agent-defs are the
harness expression.

### Security & integrity contract (spec-stage acceptance criteria)

The coordinator orchestrates an autonomous, multi-lens loop that designs LLM/agent products
and holds the human-gate (value/accountability) acts RFC-0048 D1 says are irreducibly human.
A spec-stage secure-design pass surfaced controls that must be **first-class parts of the
contract**, named here and carried as **acceptance criteria in the implementing spec** (this
RFC ships no code, so it specifies the controls, it does not implement them):

- **Verdict write-authority (no forged consent).** Because the *same* reasoning context both
  sets `status=awaiting-human` and reads the decision log to resume, the contract must
  prevent the controller (or a poisoned lens) from writing its own `ratified-by: human` row
  and auto-advancing a consent gate the human never saw. **AC:** the human verdict is written
  through a **harness-attested channel the agent has no token for** (omnigent's HITL pause
  writing the verdict), and resume is gated on a verdict whose `human` provenance is
  harness-attested, not self-asserted in a file the agent also writes.
- **Decision-log as a real audit trail.** **AC:** the decision-log slot is **append-only**
  with **per-row actor attestation** and **tamper-evidence** (content-hash-chained rows, or
  the integrity delegated to a harness-provided immutable log) and a **trusted timestamp**.
  Append-only is partly mechanically checkable (a lint/CI assertion that the slot's commits
  are add-only), so pair the AC with that wiring.
- **Security/compliance lens is non-degradable on a security boundary.** The
  `discovery-threat-reviewer` is a hard dep (required at G2; it ships in `product-engineering`,
  the floor) and degrades only in *depth* — never silently skipped. But its baseline checklist
  must not silently stand in for full depth on a security-relevant product (the worked
  example's whole ripple is an OWASP LLM-01/08 prompt-injection-self-modification finding).
  **AC:** tie the lens's *depth* to a **risk trigger** (mirroring RFC-0025 / the surfacing
  predicate) — when an intent or artifact crosses a security boundary (auth,
  untrusted-input-to-memory, regulated data) and `core`'s `security-checklists` depth is absent
  (only the reviewer's baseline checklist is available), the loop **surfaces to the human**
  ("security-relevant boundary crossed, only baseline security depth installed") rather than
  degrading silently.
- **Lens-write integrity (no blackboard poisoning).** In lens-team mode, lens-agents write
  the blackboard the controller trusts for convergence and cascade-invalidation; a lens that
  ingests untrusted external content (web `research`, adopter docs) is an injection sink.
  **AC:** a lens may only **propose** (`status: proposed`); **only the controller promotes**
  to `ratified`; lens-asserted traceability edges are **advisory until the controller
  validates** them; any lens ingesting untrusted external content is a trust boundary whose
  output is **data, not instructions**, to the controller.
- **Cascade-invalidation circuit-breaker.** O11's edge-walk *scopes* a rejection, but the
  same primitive is a denial-of-convergence lever (spurious edges from a high-fan-out node
  could invalidate the whole blackboard and burn the budget). **AC:** cascade re-runs count
  against the cost budget, and an invalidation exceeding a fan-out threshold **surfaces to
  the human** rather than auto-cascading.
- **`reversibility-class` is an enumeration, not free text.** It gates consent stakes, so an
  agent must not under-classify a one-way door as `reversible`. **AC:** enumerate the classes
  (`reversible` / `costly-to-reverse` / `one-way-door`) and bind `one-way-door` to a
  mandatory consent gate regardless of which gate it arose at.
- **Traceability backstop is a reachability check, not just presence.** The RFC leans on
  child-4's lint as the backstop against an under-implemented sidecar, but the spike's
  demonstrator is a *presence* check (flags a node missing an edge), which a
  disconnected-but-locally-edged subtree or a fabricated edge passes. **AC (child-4):** the
  shipped lint performs a **root→leaf reachability** pass, so the backstop can actually
  detect the failure it is invoked against; flagged as a child-4 dependency so this RFC's
  backstop claim is not load-bearing on the weaker presence check.

### The seam with the rest of the operating model

- **G3 handoff to `work-loop`** (unchanged): `discovery-loop` emits a brief → `new-spec` →
  `work-loop`. The two loops meet here; different inputs, different verifier, different
  autonomy posture.
- **The self-coverage gate** (RFC-0051) runs as `discovery-loop`'s **pre-G2 phase** — the
  seam RFC-0051 specified for its second controller, wired here.
- **The traceability lint** (child-4) consumes the **traceability slot** this RFC defines;
  the cascade-invalidation transition (D3) walks the same edges. The lint is authoritative
  when the matrix is present and derives from on-disk artifacts when the sidecar is absent
  (RFC-0048's child-4 amendment), so the loop and the standalone lint share one edge model.
- **The backlog bridge** (note 08): the decision brief decomposes into an ordered,
  dependency-aware backlog; `loop-cohort` orders it; `work-loop` pulls one item at a time.

## Options considered

**Axis: how much new machinery the coordinator is delivered as** — the same axis RFC-0048's
Options table uses for the whole initiative ("nothing → prose doctrine → new tool → new
engine → monolith"), here narrowed to the coordinator. It exhausts the space because any
coordinator must sit somewhere on it; prior art grounds each point.

| Option | Shape | Verdict |
| --- | --- | --- |
| **A. Do nothing** — leave the coordinator a noun (RFC-0048's diagnosis: "a noun, not a design") | none | Cost of delay: every operating-model step assumes an unspecified orchestrator; the gate ladder stays un-runnable; the connectedness claim stays an assertion. Rejected. |
| **B. Doctrine + agent-def + skill + sidecar schema, reviewers-as-content, no engine** ★ | the RFC-0041 / RFC-0049 idiom, one altitude up (with its own design-time reviewer roster — RFC-0048's table, not `core`'s code reviewers reused) | **Recommended.** Fits Principle 3; **spike-confirmed** (Decision 1); the contract is harness-neutral; `discovery-loop` is useful at the floor and progressively enhanced. |
| **C. A coordinator runtime / engine** (a scheduler + convergence solver + message bus) | MetaGPT / ChatDev / CrewAI manager-routing shape | Rejected for two distinct reasons: (i) Principle 3 forbids shipping runtime infrastructure; (ii) *separately*, manager-routing/chat-negotiation multi-agent measures 41–86% failure (MAST). The spike showed none of it is needed — the loop runs as content + a lint. Rejected; the harness (omnigent) supplies the runner without us shipping it. |
| **D. Fold the coordinator into `work-loop`** (one loop for discovery + build) | a single mega-loop | Conflates two loops with different inputs, verifiers, and autonomy postures (RFC-0048 D8's "must not be conflated"); the upstream has no local verifier, the downstream does. Un-right-sizable. Rejected. |

Prior art grounds the axis: RFC-0041 chose the B-shape ("no executable tooling, no new
reviewer, no new runtime") for the infra loop and was Accepted; RFC-0049 chose it again for
the *downstream* outer loop (`release-lead` + `release-loop` + the harness); MetaGPT
/ ChatDev / CrewAI are C-shape and MAST measures their failure cost; the charter forbids C.

## Risks & what would make this wrong

**Pre-mortem.**
- *The single-example spike over-generalizes* — the worked example happened to be
  convergence-friendly. **Mitigation:** the example was taken verbatim from note 02 (authored
  before the spike) and the two failure modes were *injected deliberately* to test the
  transitions rather than narrate past them; still, it is one example walked once (Threats,
  spike report). The implementing spec should run a second, structurally different example.
- *The cap transition is modelled, not run* — O12's stall-surfaces-to-human path was not
  exercised because the happy path converged early. **Mitigation:** the transition is a
  counter-compare grounded in `work-loop`'s cap; a spec-time test should force a cap hit. The
  RFC states this honestly rather than claiming "ran".
- *The sidecar schema drifts from child-4's lint / RFC-0049's reuse* — three efforts touch
  the same typed state. **Mitigation:** `core` owns the schema (Decision 2); child-4's lint
  and RFC-0049's release loop *consume* it; the edge model is the one ADR-0022 + the
  child-4 amendment already fixed.
- *Lens-team mode reintroduces MAST thrash* — parallel lens-agents could negotiate.
  **Mitigation:** the topology forbids agent-to-agent chat *structurally* — all coordination
  is controller + blackboard; the prototype's ripple settled with zero negotiation. The
  guardrail is *how* they coordinate, not *how many* there are.
- *The contract is too thin and an adopter under-implements the sidecar* → the connectedness
  check silently passes on a partial matrix. **Mitigation:** the traceability lint (child-4)
  is the mechanical backstop, authoritative-when-present and artifact-derived when absent —
  but only if child-4's lint does a **root→leaf reachability** pass, not the demonstrator's
  presence check (named as a child-4 AC in § Security & integrity contract).
- *A consent gate is auto-advanced with a forged `ratified-by: human` row*, or the
  decision-log is rewritten — the value/accountability act RFC-0048 D1 reserves for the human
  is bypassed, and the "audit trail" is repudiable. **Mitigation:** the verdict
  write-authority + append-only-attested-decision-log ACs (§ Security & integrity contract);
  the RFC no longer claims the bare schema *is* an audit trail.
- *A poisoned lens-agent writes the blackboard* — flips a slot to `ratified`, fabricates a
  traceability edge that hides an orphan (making the lint wrongly report converged), or
  amplifies a cascade-invalidation to burn the budget. **Mitigation:** the lens-write
  integrity AC (lens proposes, controller promotes; edges advisory until validated; untrusted
  input is data not instructions) + the cascade circuit-breaker AC.
- *Security is silently skipped on a security-relevant product* because the security lens
  pack isn't installed and the loop degrades quietly. **Mitigation:** the non-degradable
  security-lens AC (a security-boundary crossing with no lens installed surfaces to the
  human, mirroring the RFC-0025 risk-trigger posture).

**Key assumptions (falsifiable).**
- *The convergence loop is single-context-followable without a runtime.* If a real
  multi-module discovery needs a scheduler the controller can't be, the no-engine framing
  fails. (Believed false — **demonstrated** for the worked example; the residual risk is
  scale, addressed by lens-team mode, which is still controller + blackboard.)
- *A typed sidecar of plain files is a sufficient connectedness verifier.* If "everything
  holds together" needs richer state than a blackboard + queue + edge set + log, the schema
  under-serves. (Believed sufficient — the lint over it caught the injected defects.)
- *Cascade-invalidation by traceability edges bounds a rejection correctly.* If rejections
  routinely invalidate slots the edges don't reach, the blast radius is mis-scoped.
  (Believed adequate — the edges *are* the dependency model; a slot not reachable from the
  rejected node genuinely does not depend on it.)

**Drawbacks.** A new agent def + a new skill + a `core` schema to maintain, plus the
design-artifact reviewer modes (RFC-0048 O5) — real surface, justified because the
coordinator is the spine the whole operating model needs. The sidecar adds a typed-state
discipline an adopter must keep current (the same cost any blackboard carries). The
contract is harness-neutral but *demonstrated* on one harness's storage form (omnigent
worktree files); a different harness must map the slots to its store.

## Evidence & prior art

**Spike / de-risk result — the load-bearing evidence.** The riskiest assumption is the
coordinator's **no-engine / Principle-3 fit** (RFC-0048's own framing: demonstrated for
D1–D6, *hypothesized* for the coordinator). The prototype ([`0053-notes/`](0053-notes/))
ran `discovery-loop` against the worked example on the form omnigent stores and **supported
the framing on that one example**: walking G0→G2 as one reasoning context, with over-scope
and an unbacked security-sensitive screen injected, every transition was a plain-file edit,
and the only executable was a ~60-line lint (`check_sidecar.py`, child-4's shape) which —
*reproducibly* — flagged 2 dangling service leaves pre-recovery and reported CONVERGED after
recovery + ripple. Each note-09 paper resolution mapped to a confirmed (O2/O3/O4/O5/O7/O11/
A1/A2 + the ripple) or honestly-qualified (O12 modelled-not-run; O6's "no invalidating edit"
clause stays a judgment) result — see [`0053-notes/01-spike-report.md`](0053-notes/01-spike-report.md)
for the table and the Threats-to-validity (one example, single operator, cap not hit live).
**Conclusion:** the no-engine framing is **demonstrated on one worked example plus a
reproducible connectedness lint** — stronger than RFC-0048's bare hypothesis, weaker than a
replicated multi-example result; the assumption survives, with the residual scale risk named
in Risks and a second-example run owed at spec time.

**Repo precedent.** RFC-0048 D7/D8 + [`0048-notes/09`](0048-notes/09-gap-resolutions.md) (the
paper resolutions this confirms) and [`02`](0048-notes/02-worked-example-flow-trace.md) (the
worked example); RFC-0041 + ADR-0031 (the doctrine + reference-library + reuse, no-engine
idiom); RFC-0049 (the sibling downstream loop shipped as `release-lead` agent + skill +
harness — the exact pattern this establishes upstream); RFC-0051 (the self-coverage gate,
whose second controller is `discovery-loop`); RFC-0050 (the `experience` lens);
`work-loop`'s supervisor mode + `loop-cohort` (doctrine + a scheduler-*script*, not a
service — the precedent that a scheduler can be a lint); RFC-0025 (the iteration cap +
light/full); RFC-0040 (the three-tier layout the sidecar paths obey); RFC-0019's
`lint-brief-coverage.py` (the coverage lint child-4 generalizes); ADR-0022 (the cross-repo
reference-by-version the traceability slot reuses); `docs/specs/traceability-lint/` (child-4,
the lint that consumes the slot).

**External prior art** (fetched and confirmed). **`omnigent`** ([repo](https://github.com/omnigent-ai/omnigent),
fetched 2026-06-26) — confirmed present: an open-source meta-harness with a runner/server
control plane, **policy gates enforced outside the prompt** (spend caps, tool-call limits,
approval-before-shell), **git-worktrees as the shared store**, declarative **YAML agent
defs**, three-level (server/agent/session) governance with **human-in-the-loop pauses**, and
**cost policies** with hard caps + soft thresholds. Its docs describe **no state-sidecar /
general-blackboard capability beyond worktrees** (silence, matching RFC-0048's "documented
alpha gaps (no general blackboard beyond worktrees)" framing) — exactly the gap this
contract fills, and the reason the spike prototyped the sidecar in omnigent's storage form
rather than relying on a native one. The MAST
(41–86% multi-agent failure; arXiv:2503.13657), MetaGPT (arXiv:2308.00352), ChatDev
(arXiv:2307.07924), and LangGraph-checkpointer groundings were fetched and confirmed in
RFC-0048's notes and are not re-litigated here.

**Promoted research.** [`0053-notes/`](0053-notes/) holds the spike report + the prototype
artifacts (the four sidecar slots, two traceability snapshots, the demonstrator lint, the
loop trace). Per the RFC-0048 D9 series-execution standard, this effort appends its own
resolve-vs-surface sample reads to [`0048-notes/09`](0048-notes/09-gap-resolutions.md) and
reconciles its drift back into RFC-0048 in the same change (see Follow-on artifacts).

## Open questions

**None remain open.** The two mechanics/validation-rigor questions this RFC surfaced are
resolved per their recommended defaults (they were never genuine value/scope/conflict calls —
the parent pre-decided those in D7/D8 + note 09; per the note-09 sample, a child whose parent
settled the value calls *resolves*, it does not re-litigate). Recorded with where each landed:

1. **Validation rigor — resolved.** The implementing spec **must** run **one
   structurally-different second example** that **forces a cap hit** (exercising the
   modelled-not-run O12 stall path) — this is a spec gate. A full live on-`omnigent`
   end-to-end run is a **nice-to-have, not a spec gate**, because the contract is
   harness-neutral by design and the sidecar was already prototyped in omnigent's storage
   form. Folded into § Evidence and the Follow-on spec bullet.
2. **Sidecar schema home — resolved.** A **small `core` schema reference** (the
   `operational-safety` / `self-coverage` reference shape), **not** a self-discovered skill
   and **not** duplicated prose in `work-loop`, so child-4's lint, RFC-0049, and
   `discovery-loop` cite one source. Folded into Decision 2 (§ *Schema home*).

(The outer-cap default values are *decided* in Decision 4 — tunable defaults, recommended 12
rounds + the adopter's omnigent `cost_budget` — so they were never an open question here.)

## Follow-on artifacts

Filled in on acceptance.

- **ADR:** record "the upstream coordinator is `discovery-lead` (agent) + `discovery-loop`
  (skill) + a carried sidecar-schema contract (in the skill, not `core`) — no new runtime
  engine, spike-confirmed; the sidecar is the connectedness verifier" (the sibling of
  RFC-0041's ADR-0031 / RFC-0049's coordinator ADR).
- **Spec:** `docs/specs/coordinator-contract/` (or `discovery-loop/`) — the `discovery-lead`
  agent def + the `discovery-loop` skill (the gate state machine, the rejection/recovery +
  cascade-invalidation transition, the cap), **AC0 the carried sidecar-schema `references/`
  file** (in the skill, not a `core` doctrine file — RFC-0048 § Amendments 2026-06-26),
  **`product-engineering`'s own user-scope design reviewers** (not a mode-edit to `core`'s
  code reviewers), the second-example validation run
  (forcing the O12 cap-stall path), the **§ Security & integrity contract ACs** (verdict
  write-authority; append-only-attested decision log; non-degradable security lens on a
  boundary; lens-write integrity; cascade circuit-breaker; `reversibility-class`
  enumeration), and the G3 / self-coverage-gate / traceability-lint (incl. its root→leaf
  reachability AC) / backlog seams.
- **`discovery-loop` ↔ self-coverage gate:** wire RFC-0051's gate as the pre-G2 phase (the
  seam RFC-0051 specified, this RFC's consumer).
- **CONVENTIONS touch:** name the two-loop split (discovery vs delivery) + the surfacing
  predicate's stall clause in the operating-model section (RFC-0048's CONVENTIONS slice).
- **Changelog:** `docs/product/changelog.md` `[Unreleased]` entry for the new
  `discovery-lead` / `discovery-loop` capability.
- **Pack version:** bump `product-engineering` (new agent + skill + the carried
  sidecar-schema `references/` file + the discovery design reviewers); `core` is **not**
  bumped for the schema (it no longer carries it — § Amendments 2026-06-26); add
  `discovery-lead` / `discovery-loop` to the catalogue/marketplace manifest at spec time.
- **Foundation reconciliation (done in this PR):** RFC-0048 D7/D8 marked
  **spike-confirmed**; the loop-scoped-reviewer-roster change recorded as a tracked RFC-0048
  amendment (the CHARTER ceiling stays a `work-loop`/code-review cap); the note-09 sample-bank
  appended with this child's resolve-vs-surface reads (per the D9 series-execution standard).
  See the Amendments section of RFC-0048.
