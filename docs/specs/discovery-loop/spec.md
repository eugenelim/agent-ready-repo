# Spec: discovery-loop

- **Status:** Shipped <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** RFC-0053 (governing — the no-engine coordinator contract, the typed sidecar, the gate state machine, the bounds, the supervisor topology, and the exploratory scaffold this spec implements); RFC-0048 (the foundation; this is child 5 — it marks D7/D8 spike-confirmed, owns all four acceptance blockers, and carries the loop-scoped reviewer roster); RFC-0051 (the self-coverage gate — `discovery-loop` is the primary home of the full seven-module design-convergence instantiation, wired as the pre-G2 phase); RFC-0049 (the sibling downstream release loop that reads the same sidecar instances by convention); RFC-0050 (the `experience` lens this loop detect-and-degrades on); RFC-0041 + ADR-0031 (the doctrine + reference-library + reuse, no-engine idiom); RFC-0040 (the three-tier layout the sidecar paths obey); RFC-0025 (the iteration cap + light/full this loop's outer cap mirrors); RFC-0019 (`receive-brief`, the requirements-ingest seam); RFC-0036 (the converters / md-to-office projection adapter for enterprise-format emit); ADR-0022 (the cross-repo reference-by-version the traceability slot reuses); ADR-0042 (reviewer selection keyed to loop + work type)
- **Brief:** none
- **Contract:** the typed sidecar schema — `references/sidecar-schema.md` carried in the `discovery-loop` skill (a carried, `schema_version`-stamped contract read by convention, **not** a `contracts/<type>/` REST/event surface and **not** a `core` doctrine file)
- **Shape:** mixed

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

A product person names a raw idea and an AI **discovery lead** turns it into a ratified,
build-ready **decision brief** — diverging across candidate product shapes, converging the chosen
one through a research / product / UX / architecture / safety lens roster, pausing at a few human
sign-off points, and handing off to `work-loop` at G3 — **with no new engine, scheduler, or service**.
The whole capability ships as the RFC-0041 idiom: a `discovery-lead` **agent definition** + a
`discovery-loop` **skill** + a carried, versioned **sidecar schema**, all in the `product-engineering`
pack, runnable by whatever harness the adopter already uses (the contract is harness-neutral; the
prototype walked it as one reasoning context editing plain files plus a ~60-line connectedness lint).
The loop keeps its working state in a few plain, typed files — the **discovery-workspace** (the
blackboard, the open-questions queue, the traceability graph, the decision log, and a recursive
plan-tree) — that downstream tools (the traceability lint, `work-loop`, the release loop) only *read*,
by slot-name plus a `schema_version` stamp, never by importing the definition. Success: an adopter
can run a discovery end-to-end from a single high-level prompt, the loop **cannot forge a human's
sign-off, tamper with the decision log, or run away unbounded**, the brief it emits is labelled as a
**connected hypothesis** (every load-bearing assumption carries a validation hook — *converged ≠
validated*), and the capability arrives with the full Diátaxis guide set the adoption AC below gates
on (four pages — explanation, how-to, reference, and a tutorial that walks a real example end-to-end).
This spec is the harness-neutral
contract an adopter or a bespoke harness implements
without re-deriving it; building the harness that runs it is out of scope (RFC-0053 § Out of scope).

## Boundaries

The three-tier guard that keeps an implementing agent inside the lines.
*Always do* applies without asking; *Ask first* requires human sign-off
before proceeding; *Never do* is a hard rule, even under time pressure.

### Always do

- **Ship as content, not runtime.** `discovery-lead` is an agent def and `discovery-loop` a skill,
  both authored under `packs/product-engineering/.apm/…` then projected by `make build-self` — never
  edit the projected `.claude/` copies directly. The sidecar schema is a `references/` file and the
  plan-tree is an `assets/` file, both **carried in the `discovery-loop` skill**.
- **Carry the sidecar schema definition in the producing skill, single-sourced.** Downstream consumers
  (child-4's traceability lint, `work-loop`, the release loop, the self-coverage gate) read the
  produced `_state/` instances **by convention plus a `schema_version` stamp**; they never import the
  definition. A schema bump moves the definition + its producing skill atomically.
- **Name RFC-0048's roster as authoritative.** The discovery reviewers are
  `discovery-threat-reviewer` and `discovery-reliability-reviewer`, by exact name, distinct agents
  from `work-loop`'s code `security-reviewer` / `quality-engineer`. They are required at G2 and
  degrade only in *depth*, never to nothing.
- **Make every blackboard-changing verdict reuse one cascade mechanism** (walk traceability
  out-edges → mark `stale` → re-run only the affected lenses), always gated by the two integrity
  guards (impact-before-blast; no-jumping-ahead).
- **Write the Security & integrity controls as acceptance criteria** — verdict write-authority,
  append-only attested decision log, non-degradable security lens, lens-write integrity, cascade
  circuit-breaker, `reversibility-class` enumeration, and slot data-classification.
- **Force the modelled-not-run paths in tests.** The validation run must force a cap hit on the
  concentration-bound + pause-at-bound-resume path and walk a genuinely recursive (≥2-level) tree
  exercising the actual discovery reviewers.

### Ask first

- **Renaming the spec directory away from `discovery-loop/`** — RFC-0053 § Follow-on offered
  `coordinator-contract/` or `discovery-loop/`; this spec resolved to `discovery-loop/`, and the
  directory is referenced by the README and the sibling specs.
- **Changing the cross-loop self-coverage seam wording** (goal + resolve-vs-surface + the
  non-skippable coverage record) that `work-loop` / `release-loop` must also conform to — RFC-0051
  owns that one cross-copy invariant.
- **Choosing faithful per-gate `meta` snapshot vs. gate-granularity reset** for cross-teardown resume
  (the RFC recommends the snapshot as default but leaves the call to this spec's AC).
- **Adding any lens skill beyond the two D6 skills** (`explore-options`, `plan-validation`) or any
  reviewer beyond the two named discovery reviewers — the roster is RFC-0048's, disciplined, not a
  marketplace.

### Never do

- **Never ship a coordinator runtime / engine / scheduler / message bus / convergence solver** — the
  whole point the spike confirmed is that none is needed (Option C, rejected; CHARTER Principle 3).
- **Never put the sidecar schema in `core`, in a self-discovered skill, or duplicated as prose in
  `work-loop`** — it is the carried `discovery-loop` reference, the single source of truth (RFC-0048
  § Amendments 2026-06-26).
- **Never let a lens write `ratified` slots or trusted traceability edges** — a lens only *proposes*;
  only the controller promotes; lens-asserted edges are advisory until the controller validates them;
  untrusted external content is data, not instructions.
- **Never advance past a consent gate without an explicit, harness-attested human verdict**, and never
  let the agent write its own `ratified-by: human` row — the verdict arrives through a channel the
  agent has no token for.
- **Never degrade the security lens silently on a security boundary** — a boundary crossing with only
  baseline depth installed surfaces to the human, mirroring the RFC-0025 risk-trigger posture.
- **Never commit a `sensitive`/`regulated` slot fact verbatim** to a shared/remote store, and never
  write the working state to the product repo's main line — checkpoints go to the harness store/branch
  under the data-classification controls.
- **Never carry the operating-model two-loop split or the surfacing predicate as a `CONVENTIONS.md`
  section** — that doctrine lives in the loop skills (RFC-0048 § Amendments 2026-06-29). The only
  `CONVENTIONS.md` § 4 edit this spec makes is the **spec-format** `Discovery:` up-edge header +
  `type:` markers (DRIFT-G), which is format, not operating-model doctrine.
- **Never bump `core` for the schema** — `core` no longer carries it; bump `product-engineering`.

## Testing Strategy

This capability ships as agent/skill **content** plus one Python lint dependency (child-4's
traceability lint, owned by `docs/specs/traceability-lint/`), so verification is mostly **goal-based**
(presence-of-prose / presence-of-file greps and `make build-self` drift) with a **manual-QA**
end-to-end validation run that is the load-bearing gate for the modelled-not-run transitions:

- **Schema, template, agent, and skill content** (the slot field-sets, the plan-tree scaffold, the
  gate state machine prose, the verdict table, the bounds, the roster, the D6 skills, the security
  ACs as skill/agent prose): **goal-based check** — `grep` the source artifacts for each named slot,
  field, verdict, guard, and bound; the contract is presence-and-shape of typed prose, not a
  compressible runtime invariant.
- **The `schema_version` conformance + the append-only decision-log assertion**: **goal-based check**
  exercised by an **integration** surface — child-4's traceability lint (a real Python script) reads a
  fixture `_state/` and reports orphan / non-conforming / stale-`schema_version` slots; the append-only
  property is a lint/CI assertion that the slot's commits are add-only.
- **Projection**: **goal-based check** — `make build-self` projects the new agent + skill +
  references + assets to every adapter and the dry-run drift gate is clean.
- **End-to-end validation run** (the spec gate from RFC-0053 Open-question 1): **manual QA, exercised
  end-to-end** — run `discovery-loop` on **one structurally-different second example** that **forces a
  cap hit** (the concentration-bound + pause-at-bound-resume path — the recursion-specific behaviour
  the flat-cap counter-compare does not cover), walks a **genuinely recursive (≥2-level) tree**, and
  exercises the **actual discovery reviewers** (not `core`'s code-reviewers-in-a-mode). Record the
  observed loop trace, the lint's orphan→CONVERGED transition, and the forced bound-pause/resume. A
  full live on-`omnigent` run is a **nice-to-have, not a spec gate** (the contract is harness-neutral;
  the sidecar was already prototyped in omnigent's storage form).
- **Guides**: **goal-based + manual QA** — the four Diátaxis pages exist under
  `docs/guides/product-engineering/…` and the tutorial walks a real example end-to-end.

## Acceptance Criteria

**Decision 1 — the no-engine coordinator contract.**

- [x] **AC1.** `discovery-lead` ships as an **agent definition** and `discovery-loop` as a **skill**, both
  under `packs/product-engineering/.apm/…`, and the change ships **no runtime, scheduler, service,
  message bus, or convergence solver** — the diff adds only agent/skill/reference/asset content plus
  the existing-lint dependency. `discovery-lead` is the upstream supervisor, a peer of `work-loop`'s
  supervisor (not its supervisor), handing off at G3.
- [x] **AC2.** The recursion is **data, not runtime**: the plan-tree's `intent` slots nest via `parent_id` and
  one controller descends them depth-first under the same gate ladder + outer cap (HTN-over-blackboard,
  not a nested finite-state machine). The contract states honestly that controller-in-context
  scheduling at depth is a **bet on a shallow tree**, gated conservatively by D4's depth/breadth bounds
  (Risks); scheduling many concurrent / long-parked threads stays the harness's job.

**Decision 2 — the typed sidecar schema (carried contract).**

- [x] **AC3.** The sidecar schema **definition** ships as a `references/sidecar-schema.md` file **carried in
  the `discovery-loop` skill** (`product-engineering`, user scope) — **not** in `core`, **not** a
  self-discovered skill, **not** duplicated as prose in `work-loop`. Every produced instance carries a
  `schema_version` stamp; downstream consumers read instances by convention + the stamp and never
  import the definition.
- [x] **AC4.** The schema defines the slots with their field-sets: **blackboard** (`{id, type, lens, status ∈
  draft|proposed|ratified|stale|rejected, version, produced_by, path?, round_last_touched,
  parent_id?}` + a `meta` block carrying round counter, cost budget, gate, saturation); **open-questions**
  (`{id, raised-by, target-discipline, question, status ∈ open|routed|resolved|surfaced, resolution,
  round}`); **traceability** (typed `nodes` with `kind` + `backed_by ∈ file|container|ladder`, `edges`,
  a `root`, a `leaf_kind`, stable location-independent ids — slug / `contract@version` / Backstage
  `kind:namespace/name`); **decision-log** (`{ts, gate, decision, ratified-by ∈ human|discovery-lead,
  reversibility-class, rationale}`, canonical field order).
- [x] **AC5.** The **three status namespaces** are partitioned onto distinct fields, not one drifting enum: a
  **slot status** (`draft|proposed|ratified|stale|rejected`); the plan-tree **node lifecycle**
  (`draft→diverging→converging→ratified|stale`, plus `parked`/`abandoned`) and its **validation
  status** (`hypothesis→validating→validated|refuted`); and a **meta gate-state** (`awaiting-human` /
  `paused-at-bound` / `stalled-at-cap`). A **per-verdict cross-namespace write-set** table fixes which
  fields each verdict writes (e.g. `abandon` sets a node `abandoned` *and* its slots `stale`).
- [x] **AC6.** A **plan-tree template** ships as a carried **`assets/` file** (not just a field-list): a node =
  an `intent` slot + `parent_id` + the per-node status lifecycle, a **sub-idea index** (open / parked /
  done sub-walks), plus the D6 shapes — a **candidate set + selection** (not-chosen retained as
  `rejected`/`parked` with rationale, revivable) and a **per-node validation status + hook**.
  `discovery-lead` instantiates and fills it per initiative; the traceability lint walks it. No planner
  engine — the template is the mechanism.
- [x] **AC7.** **One plan-tree per initiative** (a forest, not a master tree): one directory per initiative
  under the RFC-0040 discovery root (repo mode `docs/discovery/<slug>/`), with a `_state/` subdir for
  the working sidecar (Tier 1) and the committed durable artifacts beside it (Tier 2); dirs created
  lazily on first write; initiatives cross-link by **stable ids**, never by sharing a tree. A
  portfolio index across initiatives is **not** a contract file (it is the harness's or an adopter
  roadmap).
- [x] **AC8.** The discovery-workspace is **durably checkpointed at each round and each consent gate** (not per
  keystroke) — to the **harness's own store/branch, never the product repo's main line** — under the
  data-classification + redaction controls, with the state branch **protected against history rewrite**
  (so the decision log's append-only / hash-chained / timestamped properties make it a real audit
  trail). The exact cadence/location is the harness's; the requirement is the contract's.
- [x] **AC9.** Anti-drift is structural: the **controller is the principal slot-writer** (cross-pack lenses emit
  native artifacts and *propose* through the open-questions queue — they never touch the schema); the
  **only direct slot-writers are same-pack** (`explore-options` / `plan-validation` / `frame-domain`,
  all in `product-engineering`); and a **`schema_version` stamp + a conformance check** (the
  traceability lint flags a non-conforming or stale-stamped slot) is the mechanical backstop.

**Decision 3 — the gate state machine (checkpoint/resume + rejection/recovery).**

- [x] **AC10.** A consent gate (G0, G1.5, G2) is a **pause, not a runtime**: `discovery-lead` writes the
  decision brief, sets `status=awaiting-human`, and emits an **option card** (`{gate, summary,
  decisions-requested, recommended, reversibility-class, artifacts}`); the harness surfaces it; the
  human's typed verdict + rationale is written to the (append-only, attested) decision log; the next
  round reads the log and resumes. Non-consent gates auto-advance unless a risk trigger (RFC-0025)
  fires.
- [x] **AC11.** **Rejection/recovery with cascade-invalidation** runs in the controller's own context: emit
  `reason → correction`, re-enter the gate's phase, **cascade-invalidate downstream slots by walking
  the traceability out-edges** from the rejected node (mark each `stale`, drop its edges from the
  active matrix), and **re-run only the affected lenses** on the reduced surface.
- [x] **AC12.** The verdict is a **typed enum**, each row with its own transition: **approve** /
  **approve-with-constraint** / **redirect (steer)** / **explore-alternatives** / **abandon** /
  **park (defer)** / **extend (override)**. Every blackboard-changing row **reuses the one cascade
  mechanism**; `explore-alternatives` routes back to the D6 divergence phase; `extend/override` is the
  row used at a paused-at-bound gate.
- [x] **AC13.** **Two integrity guards bind every row**: (1) **impact-before-blast** — any verdict that would
  invalidate/change slots first **shows the affected set and waits for confirmation** before cascading;
  (2) **no-jumping-ahead** — the loop does not advance past a gate without an explicit typed verdict, a
  scope limitation is honoured before proceeding, and the verdict + type + rationale are written to the
  **append-only, attested** decision log.
- [x] **AC14.** **Persistence is two-tier**: Tier 1 — the working `_state/` store is durable while the
  initiative is active (parked nodes in the sub-idea index persist; a run pauses `awaiting-human` and
  **resumes across sessions**); Tier 2 — on run-end / teardown the loop **promotes the durable record
  into committed artifacts** (the decision log records every park/abandon + rationale; the **backlog
  bridge** carries parked sub-ideas as **first-class entries**; the intent tree persists as committed
  docs). A parked idea is **resumable**, and `decision-archaeology`'s **revival check** can later flag
  one whose deferral rationale no longer holds.
- [x] **AC15.** **Resume is specified** (a load + a status read, no runtime): (a) **entry** — invoke
  `discovery-lead` on an initiative id, **or** on a fresh-start request the skill's first action is to
  **scan the discovery root for in-progress / parked discoveries and offer to resume** before
  scaffolding; (b) **reconstruction** — load Tier-1 `_state/` if present, else re-hydrate from the
  Tier-2 committed record; (c) **re-entry** — the per-node status says where to resume; (d)
  **integrity on resume** — check `schema_version` (migrate/flag, never silently mis-read), re-run the
  connectedness lint, re-attest any human verdict through the harness-attested channel, and be
  **idempotent** (re-applying a logged verdict/cascade is a no-op). **AC choice:** Tier-2 carries a
  **per-gate snapshot of `meta` + per-node status** so cross-teardown resume is faithful (the
  recommended default); absent it, cross-teardown resume is gate-granularity-only with counters reset.

**Decision 4 — the outer cap + cost budget.**

- [x] **AC16.** The `meta` block and each plan-tree node carry `round`/`round_cap` and
  `cost_budget`/`cost_spent` (data counters, no runtime): **per-initiative** enforcement, a **per-node
  convergence round cap**, **per-node spend** for observability, a **concentration bound** (a
  configurable ~40% fraction), and **structural depth/breadth bounds** (max sub-walk depth + max open
  sub-ideas).
- [x] **AC17.** **Every bound is a pause-and-confirm/override gate, not an auto-terminal**: hitting a bound sets
  `status: paused-at-bound` (a paused-awaiting-human state, not a terminal `stalled` walk-away), writes
  an option card, and surfaces the D3 verdict set (**extend/override** / narrow / park / abandon); a
  paused-at-bound initiative **resumes** once the human overrides or narrows. The end-to-end validation
  run **forces** this path — specifically the **concentration-bound + pause-at-bound-resume** path, not
  just the flat cap.

**Decision 5 — the supervisor topology (loop-scoped roster).**

- [x] **AC18.** `discovery-lead` right-sizes **solo** (holds the blackboard in one context, switches lenses
  itself) ↔ **lens-team** (parallel lens-agents that **bounce off each other only through the
  blackboard / open-questions queue**, controller-mediated — **never free-form agent-to-agent
  chat-negotiation-to-consensus**, the MAST failure mode). The invariant is *structured coordination +
  verification*, scoped to **inside one discovery loop**; inter-loop handoff is durable contract
  artifacts and company-OS scale is the harness's mesh (this contract ships only the stable-id
  substrate a mesh consumes, not the mesh).
- [x] **AC19.** The discovery roster is **loop-scoped** per RFC-0048's roster table:
  **`discovery-threat-reviewer`** + **`discovery-reliability-reviewer`** ship in `product-engineering`
  as **distinct agents** from `work-loop`'s code reviewers (collision-hardened names), **required at
  G2 reconcile**, degrading only in *depth* (their own baseline checklists when `core`'s
  `security-checklists` / `operational-safety` depth is absent, **never to nothing**). The
  `research` / `experience` / `architect` lenses are the **optional detect-and-degrade** set
  (product-only discovery at the floor). Lens conflicts: factual → `discovery-lead` arbitrates via
  referents; value → the human at G2.
- [x] **AC20.** The CHARTER's "three reviewers is the ceiling" stays a **`work-loop`/code-review cap**; the
  loop-scoped discovery roster is recorded as a **tracked RFC-0048 amendment**, not a CHARTER edit.

**Decision 6 — the exploratory scaffold (divergence → convergence → validation).**

- [x] **AC21.** Two thin PE skills ship: **`explore-options`** (divergence — *generate* N candidate product
  shapes across **altitude × mechanic**, each with its riskiest assumption, before convergence) and
  **`plan-validation`** (turn assumptions into a validation plan — assumption → kill condition → the
  real-world activity that confirms it — **and scaffold the primary-research instruments**: interview
  guide, usability-test plan, transcript synthesis). **No new agent, no new reviewer, no engine.**
  Running the interview/pilot sessions themselves stays **out of charter** (`plan-validation` scaffolds
  and synthesizes; a human runs them).
- [x] **AC22.** `de-risk-intent` gains a **validation-hook field**; `decompose-intent` optionally gains a
  **prioritization/ranking** step; and a **validation-plan typed slot** is added to the sidecar. The
  divergence stage adds a **candidate set + selection** and the validation stage a **per-node
  validation status + hook** to the plan-tree template (data, no engine).
- [x] **AC23.** **Provisional-spine emission at G2**: the decision brief is emitted as a **connected
  hypothesis** — each load-bearing assumption carries a **validation hook** (kill condition + the
  real-world activity), every node is labelled **grounded** / **surfaced** / **to-validate**, and
  *converged ≠ validated* is a **structural property of the tree** (a validated-status field), with the
  brief stating plainly that desk-grounding ≠ validation.
- [x] **AC24.** The **decision-brief template carries a required, structured success-metrics / North-Star slot**
  — the one concrete brief-template requirement RFC-0053 § Skill-coverage pressure test routes to this
  spec by name ("elevate metrics to a required brief-template slot … the implementing spec owns the
  template"). It is **not** a new skill (`frame-intent` / `decompose-intent` already name outcomes); it
  is a required slot so a brief cannot reach G3 without a done-criterion the build loop can iterate
  against. The metric *instrumentation* implementation stays downstream / out of charter.

**Security & integrity contract (each is a hard AC).**

- [x] **AC25.** **Verdict write-authority (no forged consent).** The human verdict is written through a
  **harness-attested channel the agent has no token for**; resume is gated on a verdict whose `human`
  provenance is harness-attested, not self-asserted in a file the agent also writes. The AC **tests the
  channel** (the agent provably cannot forge the row), not merely the slot's append-only-ness; the
  contract records that an adopter whose harness cannot provide an agent-untokened channel **cannot run
  the loop unattended safely**.
- [x] **AC26.** **Decision-log as a real audit trail.** The decision-log slot is **append-only** with **per-row
  actor attestation** and **tamper-evidence** and a **trusted timestamp**, paired with a lint/CI
  assertion that the slot's commits are add-only. **Tamper-evidence is verified, not asserted:** the
  implementing PR ships **either** (a) a **hash-chain field** in the decision-log row schema **plus** a
  lint asserting each row's hash covers the prior row's hash (so an in-place edit of a prior row's
  `rationale`/`decision` that keeps the append-length is detected — the add-only lint alone does not
  catch it), **or** (b) an explicit harness-conformance precondition naming a **harness-provided
  immutable log**, recorded in the schema reference. The validation run exercises a **tamper attempt**
  (an in-place prior-row edit) and records that it is detected.
- [x] **AC27.** **Non-degradable security lens on a boundary.** The `discovery-threat-reviewer`'s *depth* is tied
  to a **risk trigger** (mirroring RFC-0025): when an intent/artifact crosses a security boundary
  (auth, untrusted-input-to-memory, regulated data) and `core`'s `security-checklists` depth is absent,
  the loop **surfaces to the human** rather than degrading silently.
- [x] **AC28.** **Lens-write integrity (no blackboard poisoning).** A lens may only **propose**
  (`status: proposed`); **only the controller promotes** to `ratified`; lens-asserted traceability
  edges are **advisory until the controller validates** them; any lens ingesting untrusted external
  content is a trust boundary whose output is **data, not instructions**.
- [x] **AC29.** **Cascade-invalidation circuit-breaker.** Cascade re-runs **count against the cost budget**, and
  an invalidation exceeding a **fan-out threshold surfaces to the human** rather than auto-cascading.
  The threshold is a **spec-tunable default** (mirroring D4's ~40% concentration default — a
  modelled-not-run control must not ship without a value), and the validation run **forces one
  over-threshold invalidation** and records that it surfaced rather than auto-cascading.
- [x] **AC30.** **`reversibility-class` is an enumeration** (`reversible` / `costly-to-reverse` /
  `one-way-door`), not free text; `one-way-door` binds to a **mandatory consent gate** regardless of
  which gate it arose at.
- [x] **AC31.** **Sidecar data-handling / classification.** The spec **classifies each slot** (`public` /
  `internal` / `sensitive` / `regulated`, or an adopter equivalent), gives **redaction guidance** for
  examples and promoted notes, and states **retention/export expectations** for `_state/` and
  harness-backed stores; a **regulated- or secret-bearing artifact surfaces** to the human /
  `discovery-threat-reviewer` before being written to a shared repo-backed sidecar. The classification
  check is a **precondition on the per-round/per-gate checkpoint write** (the D2 checkpoint AC): a
  `sensitive`/`regulated` slot is redacted-or-surfaced **before** it reaches the shared store, not as a
  separate later step — so the two ACs compose rather than being satisfiable independently.

**Seams with the rest of the operating model.**

- [x] **AC32.** **G3 handoff** to `work-loop` is wired: `discovery-loop` emits a brief → `new-spec` →
  `work-loop` (unchanged; different inputs, verifier, autonomy posture).
- [x] **AC33.** **The self-coverage gate** (RFC-0051) is wired as `discovery-loop`'s **pre-G2 phase**, and this
  loop is the **primary home of the full seven-module design-convergence instantiation** — it carries
  its **own co-scoped copy of all seven modules** in `product-engineering`, right-sized by this loop's
  progressive mode, conforming to RFC-0051's cross-loop seam (goal + resolve-vs-surface + a
  non-skippable coverage record). It runs the full battery (unlike `work-loop`'s net-new slice).
- [x] **AC34.** **The traceability slot** this spec defines is consumed by **child-4's lint**
  (`docs/specs/traceability-lint/`), and the D3 cascade transition walks the **same edges**. **Child-4
  dependency — now MET:** the disconnected-subtree backstop relies on a **root→leaf reachability**
  pass, and child-4's lint **now performs it** (`traceability-lint`, amended 2026-06-30 — the
  `reachability_sidecar` pass on the authoritative sidecar graph). The cascade backstop therefore
  catches the **whole** disconnected subtree, not merely the orphan *tip* the earlier per-node
  presence check flagged. Scoped honestly: reachability **closes** the disconnected-subtree half and
  **surfaces** (informationally, never silently green — it cannot mechanically distinguish a forged
  cross-repo token from a not-yet-catalogued one in an open-world graph) the fabricated-edge half.
  *This spec's obligation — consume the slot, walk the same edges, and rest only on a claim that is
  now true — is met; the formerly-tracked gap is resolved
  (`docs/backlog.md` → `discovery-loop-traceability-reachability`).*
- [x] **AC35.** **The backlog bridge**: the decision brief decomposes into an **ordered, dependency-aware
  backlog** (parked sub-ideas carried as first-class entries); `loop-cohort` orders it; `work-loop`
  pulls one item at a time.

**DRIFT-G — the spec→discovery up-edge (RFC-0048 acceptance blocker #4).**

- [x] **AC36.** This spec **owns** the `new-spec` **`Discovery:` up-edge header** + the discovery-artifact
  **`type:` markers** — a **spec-format addition** in `docs/CONVENTIONS.md` § 4 + the `new-spec` skill
  (format, **not** operating-model doctrine). `discovery-loop` is the **consumer** of that up-edge (the
  brief/spec→discovery edge the traceability lint walks at G3).
- [x] **AC37.** **Producer-before-consumer sequencing**: `new-spec` emits the header + markers **first**, and
  only then is child-4's traceability lint wired **fail-closed (`--strict`)** at the G2/convergence
  gate — until then the lint stays **warn-only** (specs without the header are warnings, not failures).
  The `--strict` flip is sequenced **here**, downstream of the header landing. This **resolves RFC-0048
  acceptance blocker #4** and discharges the generic spec-metadata / `new-spec` follow-on owner.

**Folding in traditional requirements capture.**

- [x] **AC38.** The **BRD/PRD/SRS/FRD/use-case/RTM crosswalk** ships as **guidance in the `discovery-loop`
  skill** (not a new pillar); requirements-as-input is handled by **`receive-brief` + `frame-intent`
  brownfield ingest** (a **thin `receive-brief` extension at most**, recognizing the requirements-doc
  shapes — not a new skill); the **traceability slot serves as the RTM**; and requirements-as-output
  (a formal BRD/SRS/RTM with sign-off) rides the **converters / md-to-office projection adapter**
  (RFC-0036), not a discovery skill. **No new requirements writing/validation/enrichment pillar.**

**Adoption & packaging (a release gate, not optional).**

- [x] **AC39.** A **coordinator ADR** is recorded (the sibling of RFC-0041's ADR-0031 / RFC-0049's coordinator
  ADR): *the upstream coordinator is `discovery-lead` (agent) + `discovery-loop` (skill) + a carried
  sidecar-schema contract (in the skill, not `core`) — no new runtime engine, spike-confirmed; the
  sidecar is the connectedness verifier.* (The ADR is authored in the implementing PR, not this
  authoring PR — RFC-0053 § Follow-on lists it first.)
- [x] **AC40.** The **Diátaxis guide set** is authored (via `new-guide`, under `docs/guides/product-engineering/…`)
  **as an acceptance criterion before the capability counts as shipped**: an **Explanation** (the
  coordinator contract, the divergence → convergence → validation arc, *converged ≠ validated*, the
  no-engine model, recursion); a **How-to** (run a discovery end-to-end — the one-prompt + targeted
  forms; recurse into a sub-idea; fold in existing requirements via the crosswalk); a **Tutorial** (a
  fully walked example, promoting a note-11 / note-12-style walk); and a **Reference** (the sidecar
  slots, the plan-tree template, the skill / agent roster).
- [x] **AC41.** The **loop-skill doctrine** — the two-loop split (discovery vs delivery) + the surfacing
  predicate's stall clause — is carried in the **`discovery-loop` skill doctrine**, **not** a
  `CONVENTIONS.md` operating-model section (RFC-0048 § Amendments 2026-06-29).
- [x] **AC42.** **`product-engineering` is version-bumped** (`pack.toml` **and** `.claude-plugin/plugin.json`,
  with `marketplace.json` reconciled via `make build-self`) carrying the new agent + skill +
  sidecar-schema reference + plan-tree template asset + the two discovery reviewers + the two D6 skills
  + the `de-risk-intent` / `decompose-intent` extensions; **`core` is not bumped** for the schema; and
  `discovery-lead` / `discovery-loop` are added to the catalogue/marketplace manifest. A
  `docs/product/changelog.md` `[Unreleased]` entry records the new capability.
- [x] **AC43.** **`make build-self`** projects the new agent + skill + references + assets to every adapter and
  the dry-run drift gate is clean.

**Validation run (the empirical spec gate).**

- [x] **AC44.** The implementing PR runs **one structurally-different second example** that **forces a cap hit**
  (the concentration-bound + pause-at-bound-resume path), walks a **genuinely recursive (≥2-level)
  tree**, and exercises the **actual discovery reviewers**; the run records the observed loop trace and
  the traceability lint's orphan → CONVERGED transition. The run also exercises the **negative /
  adversarial paths** the security ACs above demand — controls otherwise modelled-not-run: (a) the
  controller **attempts to self-write a `ratified-by: human` row** and resume, and the run records the
  forged row is **rejected/flagged** (or, for a harness that cannot provide the agent-untokened verdict
  channel, records that the loop **refuses unattended operation**) — *testing the channel, not the
  slot*; (b) a **tamper attempt** (an in-place prior-row decision-log edit) is **detected**; (c) one
  **over-threshold cascade fan-out surfaces** rather than auto-cascading. A full live on-`omnigent`
  end-to-end run is a **nice-to-have, not a spec gate**.

## Assumptions

- Technical: `discovery-loop` / `explore-options` / `plan-validation` skills, the `discovery-lead` /
  `discovery-threat-reviewer` / `discovery-reliability-reviewer` agents, and the `Discovery:` up-edge
  **do not yet exist** — this spec is the contract for unbuilt artifacts (source: repo read 2026-06-30
  — `packs/product-engineering/.apm/skills/` holds only `align-value-stream`, `de-risk-intent`,
  `decompose-intent`, `frame-domain`, `frame-intent`, `voice-and-microcopy`; no `.apm/agents/`
  content; no `Discovery:` in `docs/CONVENTIONS.md` or `new-spec`).
- Technical: `product-engineering` is at pack version `0.8.0` / contract `0.13`; a projected/aggregated
  pack bump needs both `pack.toml` and `.claude-plugin/plugin.json` with `marketplace.json` reconciled
  via `make build-self` (source: `packs/product-engineering/pack.toml`, `.claude-plugin/plugin.json`;
  reference memory *Pack bump needs plugin.json too* / *Non-projected pack version bump drifts
  marketplace.json*).
- Technical: the sidecar slot field-sets, the gate transitions, the verdict set, and the security ACs
  are transcribed from RFC-0053 §§ Decision 2 / Decision 3 / Security & integrity contract (source:
  `docs/rfc/0053-the-discovery-loop.md`, read 2026-06-30); the prototype artifacts demonstrating the
  connectedness lint live in `docs/rfc/0053-notes/spike/`.
- Process: child-4's traceability lint is owned by `docs/specs/traceability-lint/` (Shipped 2026-06-29;
  amended 2026-06-30 to add the **root→leaf reachability** pass this spec's backstop claim depends on —
  the dependency is now MET) and sequences the `--strict` flip after the `Discovery:` header lands
  (source: RFC-0053 § Security & integrity contract + § Follow-on DRIFT-G).
- Process/governance: the spec slug is `discovery-loop/` (RFC-0053 § Follow-on offered
  `coordinator-contract/` or `discovery-loop/`; resolved to the skill-matching name — a naming call the
  RFC authorized either way) (source: RFC-0053 § Follow-on → Spec; resolve-vs-surface disposition,
  resolved-with-referent).
- Process/governance: the operating-model doctrine is **skill-resident with no `CONVENTIONS.md`
  operating-model section**; the only `CONVENTIONS.md` § 4 edit is the spec-format `Discovery:` up-edge
  (source: RFC-0048 § Amendments 2026-06-29; RFC-0053 § Follow-on → DRIFT-G + loop-skill doctrine).
- Process/governance: this spec is **Draft** and unbuilt; its merge as an *implementing* PR is gated on
  RFC-0053 / RFC-0048 acceptance — satisfied by construction, since RFC-0053 is flipped to Accepted in
  the same PR that authors this spec (source: RFC-0053 status flip this PR; sibling Draft spec
  `release-loop` is the precedent for an authored-but-unbuilt loop spec).
- Product: the value of the upstream coordinator (turning a raw idea into a build-ready, validated
  brief) and the six decisions are **pre-decided by RFC-0053** (spike-confirmed spine + specified-in-shape
  extensions); this spec wires the contract, it does not re-open the decisions (source: RFC-0053 § The
  ask + § Decisions requested; note 09's "a child must not re-litigate what the foundation settled").
