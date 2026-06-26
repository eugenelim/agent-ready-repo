# Spec: release-loop

- **Status:** Draft <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** RFC-0049 (the parent — the release (outer) loop + minimum-regret deploy carve + company-OS composition; resolves its OQ1 pack-home + OQ2 agent-shape) · RFC-0048 (the provisional foundation — the G4→G5 arc, the sidecar substrate, the company-OS framing) · RFC-0053 (the sibling — the `core` sidecar *schema* this loop consumes, and the `agent-def + skill + no-engine` pattern + § Security & integrity contract shape it mirrors downstream) · RFC-0041 + ADR-0031 (the *doctrine + reference-library + reuse-existing-reviewers, no engine / no new reviewer* precedent; the deploy *flavor* this graduates into a proper outer loop; P5's non-skippable security posture) · ADR-0018 (the orchestrator-inlined progressive-disclosure depth mechanism the reuse rides) · RFC-0025 (`work-loop` light/full + the iteration cap this loop's outer cap mirrors) · RFC-0040 (the three-tier layout resolution the sidecar paths obey)
- **Brief:** none
- **Contract:** none — the loop *consumes* the `core` sidecar schema (RFC-0053: blackboard · open-questions · traceability · decision-log); it authors no new `contracts/<type>/` surface.
- **Shape:** n/a — content/methodology change (a new `release-engineering` pack holding a `release-lead` agent definition + a `release-loop` skill); no application LLD. The "contract" is the loop's state machine + the minimum-regret carve + the security/integrity controls, specified below as Acceptance Criteria.

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

Agents and adopters who install a new opt-in **`release-engineering` pack** get a
**`release-lead`** agent and a **`release-loop`** skill that drive the
**deployed end-to-end validation outer loop** autonomously *on reversible
infrastructure*. `work-loop` remains the **inner loop** (local build +
verification); `release-loop` is the **outer loop** — it deploys the
integrated whole to an **ephemeral environment**, runs e2e, observes telemetry,
feeds deployed findings back to the inner loop (no human relay), redeploys, and
**iterates until the deployed whole converges**, then stops at the **human gate**
for the prod ship (G5). Convergence up to that gate is judged by **policy**
(canary metric analysis + e2e coverage of the changed surface + flake < 2%), not
by a human; **DORA** is the health signal. Autonomy is carved by
**minimum-regret**: the agent runs the inner *and* the outer loop on ephemeral
envs unwatched (deploy / e2e / iterate / teardown + canary with metric-gated
auto-rollback in non-prod tiers); the human is present only at the **irreversible
exits** — first real users or data, data migrations, spend over a pre-agreed
threshold, security/auth-boundary changes, anything irreversible beyond MTTR, and
the prod ship. `release-lead` is the SRE/ops **outer-loop supervisor**, a
*peer* of `work-loop`'s supervisor and `discovery-lead` — it reuses `core`'s
`operational-safety` depth modules + the `quality-engineer` and `security-reviewer`
reviewers, consumes `core`'s sidecar schema, ships **no new runtime engine and no
new reviewer agent** (the RFC-0041/ADR-0031 idiom), and runs on the **omnigent**
harness (ephemeral envs, option-card consent, cost policies) harness-neutrally.
This completes the **company OS**: product (discovery) → engineering (build) →
SRE/ops (release).

**Out of scope (named here so the diff can't sprawl into them):** the
fidelity-ladder / local-infra-equivalents skills are the *inner-loop* obligation
RFC-0049 Decision 3 places on the build packs — a separate concern, not authored
here; the **harness** is not built or forked (omnigent exists; we ship the
contract it enforces); the **sidecar schema** is RFC-0053's `core` artifact — this
loop consumes it, never forks it; **G5 cloud-specific deploy mechanics / IaC** are
the adopter's, tool-neutral here; the **CONVENTIONS edit** naming the minimum-regret
boundary is a follow-on (RFC-0049's CONVENTIONS slice); **running the live
product-as-a-managed-service** long-term is adopter ops (RFC-0049 non-goal).

## Boundaries

The three-tier guard that keeps an implementing agent inside the lines.
*Always do* applies without asking; *Ask first* requires human sign-off
before proceeding; *Never do* is a hard rule, even under time pressure.

### Always do

- Ship the capability as an **agent definition** (`release-lead`) + a
  **skill** (`release-loop`) in the new opt-in **`release-engineering` pack**, and
  **reuse** `core`'s `operational-safety` reference modules + the
  `quality-engineer` and `security-reviewer` agents + the RFC-0053 `core` sidecar
  schema — content only, the `implementer`/`discovery-lead` shape, no engine
  (ADR-0031).
- Express the loop **harness-neutrally**; name **omnigent** as the *reference*
  runtime (ephemeral envs, human-in-the-loop option-card pause, cost policies),
  never hardcode its internals (RFC-0041 P4 harness-neutrality; Principle 1).
- Bind **every** irreversible / high-stakes action — first real users or data,
  data migrations, spend over threshold, security/auth-boundary changes, anything
  irreversible beyond MTTR, and the prod ship (G5) — to a **human consent gate**,
  surfaced as an option card and resumed from a harness-attested verdict.
- Make the **security/compliance pass non-degradable on a crossed boundary**
  (RFC-0041 P5 / RFC-0053): reuse `security-reviewer` at spec stage and on deploy
  diffs; when a deploy crosses a security boundary and the security lens is
  absent, **surface to the human**, never degrade silently.
- Judge convergence by **policy** up to the human gate — canary metric analysis
  (success / error / latency SLOs) + e2e coverage of the **changed surface** +
  flake < 2% — and treat **DORA** (deploy frequency, lead time, change-fail rate,
  MTTR, + 2025 rework rate) as the **health signal**, not a promotion gate.
- Carry an **outer round cap + cost budget** in the sidecar `meta` block; on
  cap-with-unconverged state, **write a stall record to the decision log and
  surface to the human** (the surfacing-predicate stall clause) — never churn
  forever.
- Make deployed findings **self-explanatory to the agent** (observability-driven)
  and feed them **back to `work-loop`** as build tasks via the sidecar blackboard
  — the agent reads real environment output itself; the **human-as-relay is the
  named anti-pattern** (RFC-0041 P4).
- **Tear down** ephemeral envs on cycle end (the `cost-and-teardown` module); a
  non-torn-down env is surfaced (the ephemeral-cost-sprawl pre-mortem).
- Bump the new pack version (`packs/release-engineering/pack.toml` +
  `.claude-plugin/plugin.json`), refresh `marketplace.json` via `make build-self`,
  register the agent + skill in the catalogue manifest, and add a
  `docs/product/changelog.md` `[Unreleased]` entry. Run **all** lint surfaces —
  `make build-check` (incl. `lint-packs`), `python tools/lint-agent-artifacts.py`,
  `python tools/lint-agents-md.py` — before declaring done.

### Ask first

- **The pack name.** Resolved to **`release-engineering`** — the discipline/seat
  name, parallel to `product-engineering` (the two company-OS discipline packs).
  It is the recognized SRE sub-discipline that owns the path-to-prod, and it keeps
  the agent/skill on a `release-*` prefix (`release-lead`, `release-loop`).
  Rejected alternatives: **`integration`** (collides with **Continuous
  Integration**, which is build/*inner*-loop — naming the *outer* loop "integration"
  reads backwards to anyone fluent in CI/CD); **`delivery`** (the dual-track
  ontology binds "delivery" to the *build* track — RFC-0048 D7/D8 names `work-loop`
  "the **delivery** track"); and a **bare `release`** pack (collides with the
  repo's own release register — `release-agentbundle.yml` / `release-credbroker.yml`
  / `[Unreleased]` changelogs all mean *publish our own tooling*; the compound
  `release-engineering` dodges that overload). The name is the one taste call —
  surface it for override before scaffolding the pack.
- **Authoring the fidelity-ladder / local-infra-equivalents skills**
  (RFC-0049 Decision 3) — that is the inner-loop build obligation, a separate
  effort; surface before expanding scope into it.
- **Any change to the `core` sidecar schema** (RFC-0053 owns it) — the loop
  consumes it; surface, don't fork.
- **Adding or reordering any risk trigger, or adding any reviewer** beyond the
  three reused (`quality-engineer`, `security-reviewer`, and — at the spec/diff —
  `adversarial-reviewer`).

### Never do

- **Ship any executable deploy runtime / engine / daemon / orchestrator /
  cost-gate / canary-analyzer** as the feature mechanism — content + doctrine only
  (Principle 3, ADR-0031). The loop *offers to scaffold* an adopter's deploy /
  smoke / teardown artifacts; it does not ship them.
- **Let an agent promote to prod, to real users or real data, past a spend
  threshold, or through any one-way door autonomously** — those are human consent
  gates, no clever workaround, even under time pressure.
- **Forge a `ratified-by: human` decision-log row or auto-advance a consent gate
  the human never saw** — the human verdict is written through a harness-attested
  channel the agent holds no token for.
- **Bind the loop to a specific cloud or IaC tool, or to omnigent internals**
  (harness- and tool-neutral; Principle 1).
- **Fork or duplicate the `core` sidecar schema** (RFC-0053) — consume the one
  source.
- **Edit the projected `.claude/...` copies directly** — `make build-self`
  reverts them; the `packs/...` source is the fix point.
- **Create any new top-level directory beyond the single RFC-0049-sanctioned
  `release-engineering` pack** (the structure is intentional; new dirs go through RFC).

## Testing Strategy

The change is **agent-instruction content** (one agent definition + one skill, in
a new pack) plus governance reconciliation — no executable logic carries a
compressible invariant — so verification is **goal-based** plus **judgmental
review**, with **no TDD**. This mirrors the verification strategy the
`infra-aware-work-loop` and `work-loop-light-mode` specs used for the same class
of change, and the worked-example validation RFC-0053's coordinator spike used.

- **Projection correctness** (source → projected paths agree after build-self):
  goal-based — `make build-self`, then the drift / projection gates are clean.
- **Lint conformance**: goal-based — `make build-check`,
  `tools/lint-agent-artifacts.py`, and `tools/lint-agents-md.py` all exit 0; the
  new agent's `tools:` surface and the skill frontmatter pass `lint-packs`.
- **Activation**: goal-based — a `pack-activation-evals` entry confirms the
  `release-loop` skill activates on deploy / e2e / "ship the integrated
  whole" / "iterate the deployed env" prompts and *not* on inner-loop build
  prompts (the inner/outer boundary is legible to the model).
- **Content presence** (the carve's two zones; the convergence policy; the outer
  cap + stall-surface; the sidecar consumption; the reuse wiring; the six
  security/integrity controls; *no* executable engine added): goal-based —
  `grep` / `git diff` checks against the Acceptance Criteria.
- **Doctrine correctness** (does the prose actually *carve* autonomy at the
  reversibility line, *gate* the irreversible exits, *bound* the loop with the
  cap, *reuse without forking*, and *bind* security to the boundary?): judgmental
  — the spec-mode and diff-mode `adversarial-reviewer` pass. Because the subject
  is a **security/irreversibility boundary**, a `security-reviewer` spec-stage
  read confirms the § Security & integrity controls (AC10) are specified as
  acceptance criteria at the right depth — exactly the pass that produced
  RFC-0053's § Security & integrity contract.
- **No-engine validation** (the load-bearing empirical claim): a worked-example
  trace (AC12) walks **one full outer-loop cycle** on the form omnigent stores,
  with a forced cap-hit and a forced security-boundary-without-a-lens, to
  demonstrate every transition is a file edit + a policy check, no runtime — and
  to honestly flag the single-example, single-operator limit.

## Acceptance Criteria

- [ ] **AC1 — the inner/outer split + the agent shape (RFC-0049 D1 / OQ2).** The
  `release-loop` skill is the **outer loop** (deploy the integrated whole →
  e2e → observe telemetry → feed findings to the inner loop → redeploy →
  converge), distinct from `work-loop`'s **inner loop** (local build); the
  boundary between them is named (the inner loop hands off the locally-built,
  deploy-ready whole; the outer loop owns everything from deploy onward).
  `release-lead` is a **distinct agent**, a *peer* of `work-loop`'s supervisor
  and `discovery-lead`, **not** a `work-loop` outer-mode — the skill and the agent
  state that the two loops have different inputs, verifiers, and autonomy postures
  and **must not be conflated**.
- [ ] **AC2 — the pack home (RFC-0049 OQ1).** The capability ships in a **new
  opt-in `release-engineering` pack** (not `core`), which **hard-depends** on `core` (the
  sidecar schema + `operational-safety` + `quality-engineer` + `security-reviewer`)
  and **detect-and-degrades** on cloud/platform/contract packs — with a defined
  observable: when a platform/cloud pack is **absent**, the loop **names the
  deploy / smoke / teardown artifacts it would otherwise consume and surfaces the
  gap** to the human (the "offer to scaffold" path), rather than failing or
  silently proceeding; when **present**, it consumes them. `core` is
  unchanged except for the version touch its `marketplace.json` aggregation
  requires. The pack carries `pack.toml`, `.claude-plugin/plugin.json`, and a
  `README.md`, and is registered in the catalogue / `marketplace.json`.
- [ ] **AC3 — the carve, autonomous zone (RFC-0049 D2).** The skill enumerates the
  **reversibility zone** the agent runs unwatched: the inner loop; the outer loop
  **on ephemeral environments** (deploy / e2e / observe / iterate / teardown); and
  **canary in non-prod tiers** with metric-gated **auto-rollback**. The "reversible"
  label is **conditioned on env isolation**: ephemeral envs are network- and
  data-isolated from prod **and from each other**, hold **no real user data**, and
  **cannot reach prod state** — a deploy target that cannot be proven isolated is
  itself a **consent-gate crossing** (it is no longer reversible), not an
  autonomous-zone action.
- [ ] **AC4 — the carve, human zone (RFC-0049 D2).** The skill binds to **human
  consent gates**: first promotion to **real users or real data**; **data
  migrations** (schema / destructive); **spend over a pre-agreed threshold**;
  **security / auth-boundary** changes; anything **irreversible beyond MTTR**; and
  the **prod ship (G5)**. `reversibility-class` is an **enumeration**
  (`reversible` / `costly-to-reverse` / `one-way-door`), not free text, and
  `one-way-door` binds to a **mandatory consent gate regardless of which gate it
  arose at** (RFC-0053's enumeration AC, applied downstream).
- [ ] **AC5 — the unlock (RFC-0049 D2).** The skill names the **reversibility
  primitives** — **ephemeral environments + feature flags + auto-rollback** — as
  what turns deploy from a one-way door into a two-way door, *which is what lets
  the outer loop run autonomously*, harness-neutrally, with omnigent as the
  reference for each primitive.
- [ ] **AC6 — convergence by policy (RFC-0049 D6).** Promotion up to the human
  gate is judged by **automated policy** — canary metric analysis
  (success / error / latency SLOs) **+** e2e coverage of the **changed surface**
  **+** flake **< 2%** — **not by a human**. Each conjunct carries a **checkable
  bar**: the **changed surface** is derived from the diff against the deployed
  baseline (changed endpoints / routes / journey-steps), and coverage means
  **every changed surface element has ≥ 1 passing e2e assertion** (no
  changed-but-unasserted element promotes); the adopter may tighten the bar but
  not waive it. **DORA** (deploy frequency, lead time, change-fail rate, MTTR, +
  the 2025 rework rate) is named as the **health signal**, explicitly *not* a
  per-promotion gate.
- [ ] **AC7 — the inner↔outer feedback seam + sidecar consumption.** A deployed
  finding is written to the **sidecar blackboard** and fed back to `work-loop` as
  a build task (observability-driven, **no human relay**); the loop then
  redeploys. The loop **consumes** the `core` sidecar schema (RFC-0053:
  blackboard · open-questions · traceability · decision-log) — every cycle's
  state is a blackboard slot, every consent a decision-log entry — and **does not
  fork it**. The seam is stated as **G4** (`work-loop` build done) → **the release
  loop (the release (outer) loop RFC-0048 places in the G4→G5 gap — a loop, not a
  numbered gate)** → **G5** (human prod
  ship), continuing RFC-0048's gate arc. The outer
  loop deploys the **digest-pinned artifact the inner loop verified** — a
  substituted or rebuilt artifact between G4 and deploy is detectable (artifact
  provenance across the handoff; OWASP 2025 supply-chain), not assumed identical.
- [ ] **AC8 — the outer cap + cost budget (RFC-0049; RFC-0053 D4 mirror).** The
  sidecar `meta` block carries `round`, `round_cap`, `cost_budget`, and
  `cost_spent`; the loop increments `round` by **exactly one per
  deploy→e2e→converge pass** (a pinned monotonic invariant, so the cap can't be
  stepped over). On `round >= round_cap` **or** `cost_spent ≥ cost_budget`
  **with** any failing canary / uncovered changed surface / open finding
  remaining, the loop writes `status: stalled-at-cap` to the decision log and
  **surfaces to the human**
  (surfacing-predicate stall clause); defaults are **tunable** (recommended: a
  small per-cycle round cap + the adopter's omnigent `cost_budget`).
- [ ] **AC9 — reuse, no new reviewer / no engine (ADR-0031).** The loop **reuses
  `quality-engineer`** for the operational lens — the orchestrator inlines the
  matching `operational-safety` REVIEW modules (`environment-isolation`,
  `blast-radius`, `cost-and-teardown`, `drift-and-rollback`,
  `observability-and-smoke`, `state-and-idempotency`) into the reviewer's brief
  via the **existing** progressive-disclosure mechanism (ADR-0018), and reuses
  `operational-safety`'s **`cloud-implementation-craft`** EXECUTE-craft module
  where the loop **authors / scaffolds** an adopter's deploy / smoke / teardown
  artifacts (the EXECUTE-consumer extension that module already serves) — and
  **reuses `security-reviewer`** on deploy diffs. It adds **no new reviewer agent** (the
  CHARTER three-reviewer ceiling holds; the operational lens is a *mode* of
  `quality-engineer`, not a new agent) and **no executable code** as the feature
  mechanism. `loop-cohort.py` / `lint-spec-status.py` are byte-unchanged.
- [ ] **AC10 — the security & integrity contract (mirrors RFC-0053, extended for
  the deploy boundary).** The skill / agent specify, as first-class controls:
  **(a) verdict write-authority** — the prod / irreversible consent verdict is
  written through a **harness-attested channel the agent holds no token for**
  (omnigent HITL), and resume is gated on a verdict whose `human` provenance is
  harness-attested, never a row the agent also writes;
  **(b) decision-log as a real audit trail** — append-only, per-row actor
  attestation, tamper-evidence (content-hash-chained rows or a harness immutable
  log), trusted timestamp (the DORA / compliance trail); **paired with its
  mechanical backstop** — where the log is in-repo, append-only is asserted by an
  add-only **lint/CI check**; where it is harness-delegated, the spec names which
  harness immutability guarantee is relied on (never append-only as prose only);
  **(c) non-degradable security lens on a crossed boundary** — a deploy crossing
  auth / secrets / untrusted-input / network / regulated-data with no security
  lens installed **surfaces to the human**, not a silent degrade (RFC-0041 P5
  posture); **(d) telemetry / canary / log integrity** — a canary, telemetry, or
  log signal a lens or agent could poison is **advisory until the controller
  validates** it (lens proposes, controller promotes), **and deployed telemetry,
  e2e output, and log lines are treated as data, not instructions** to the agent
  (isolated/tagged, never concatenated into the prompt as commands) — so a
  poisoned log line cannot become a forged build task on the AC7 finding→task
  path or spoof convergence (OWASP LLM-01); **(e) auto-rollback circuit-breaker
  with two independent triggers** — a rollback storm or non-settling
  canary-analysis loop surfaces and **halts promotion** after **N consecutive
  promote↔rollback oscillations** (an attempt threshold, *independent of* the cost
  budget, so a flapping canary is bounded by attempts not only by spend) **and**
  counts against the cost budget; **(f) teardown guarantee** — ephemeral envs are
  torn down on cycle end, and a non-torn-down env surfaces (the cost-sprawl
  lever); **(g) deploy-credential tiering** — deploy credentials are
  **broker-mediated and scoped to the ephemeral-env tier** (AGENTS.md's blessed
  secrets-broker boundary), so **no prod/irreversible-tier credential is reachable
  from the autonomous (ephemeral) zone**; an agent in the reversible zone holds no
  token that can act past a consent gate — the credential-side enforcement of (a),
  so the carve's integrity rests on *inability*, not merely prohibition;
  **(h) ephemeral-env isolation is a carve precondition** — the AC3 isolation
  conditions (no prod reachability, no real data, isolated from other ephemeral
  envs) are the security floor under the "reversible" label, not just a reviewer
  lens.
- [ ] **AC11 — the company-OS composition + drift reconciliation.** The spec
  records `release-loop` as the **third loop-team** (SRE/ops) on RFC-0048's
  shared substrate (sidecar + gate arc + harness), with leads handing off
  **work→release at deploy** and **release→prod at G5**. The
  implementing PR **resolves RFC-0049's OQ1 + OQ2 in RFC-0049 itself** (recording
  where each landed — `release-engineering` pack home + distinct `release-lead` agent
  + `release-loop` skill — per its recommended defaults, the same way RFC-0053
  closed its OQs), and adds a **tracked amendment to RFC-0048** (the
  release-lead seat + pack home + agent shape now specified; the company-OS
  third seat confirmed; the work→release + release→prod handoffs wired) —
  the series-execution reconcile-drift obligation.
- [ ] **AC11b — the inner/outer + minimum-regret ADR.** The RFC-0049 follow-on ADR
  — **"the inner/outer loop split + the minimum-regret deploy carve"** — is
  authored in this PR (the sibling of RFC-0041's ADR-0031 / RFC-0053's coordinator
  ADR), recording the expensive-to-reverse architectural decision the carve
  embodies. **Lifecycle note:** RFC-0049 is `Open` and its OQs `decide-by: this
  RFC's child spec`, a circular gate this PR closes by resolving the OQs in
  RFC-0049 and authoring this spec together; whether RFC-0049 flips to `Accepted`
  in the same PR is the **operator's call** and is surfaced, not assumed.
- [ ] **AC12 — no-engine validation.** A worked-example trace (`notes/`) walks
  **one full outer-loop cycle** (deploy → e2e finds a defect → finding to the
  blackboard → inner-loop fix → redeploy → canary + coverage + flake converge →
  surface the G5 consent gate) on the form omnigent stores, demonstrating every
  transition is a **file edit + a policy check**, no runtime. The trace reuses
  **RFC-0048 note-02's worked example (`example-assistant`)** as its subject, so
  the downstream demonstration is continuous with the upstream coordinator
  prototype. The trace
  **forces a cap-hit** (exercising the AC8 stall-surface path) **and** a
  **security-boundary-with-no-lens** (exercising the AC10c surface path), and
  **honestly flags** the single-example, single-operator limit (the residual
  scale risk, mirroring RFC-0053's spike Threats).
- [ ] **AC13 — projection + lint + release hygiene.** `make build-self`
  regenerates the projected agent + skill cleanly; `make build-check`,
  `python tools/lint-agent-artifacts.py`, and `python tools/lint-agents-md.py` all
  pass (the latter two not in `make build-check`; run by hand / in CI); any pack
  seeds are placeholder-shaped (`lint-seeds`); `packs/release-engineering/pack.toml` +
  `.claude-plugin/plugin.json` are versioned, `marketplace.json` reflects them
  after build-self, and `docs/product/changelog.md` carries an `[Unreleased]`
  entry.

## Assumptions

- Technical: the agent + skill sources live under `packs/release-engineering/.apm/agents/`
  and `packs/release-engineering/.apm/skills/`, projected to `.claude/...` by `build-self`,
  never edited in place (source: pack tree of `packs/product-engineering/.apm/...`;
  `infra-aware-work-loop` spec Assumptions).
- Technical: `core` already ships `operational-safety` as orchestrator-inlined
  reference modules consumed by `quality-engineer`, and `security-reviewer` as a
  reviewer agent — so the reuse (AC9) is a wiring + a `quality-engineer`
  operational *mode*, not a new mechanism (source:
  `packs/core/.apm/skills/operational-safety/SKILL.md` "How it loads";
  `packs/core/.apm/agents/quality-engineer.md`).
- Technical: the `core` sidecar schema (blackboard · open-questions · traceability
  · decision-log) is specified by RFC-0053 as a `core` schema reference, not yet
  built — so AC7's "consume the schema" carries a **dependency on RFC-0053's
  implementing spec** landing the schema; until then the loop names the slots and
  consumes them by convention (source: RFC-0053 Decision 2; RFC-0053 § Follow-on
  artifacts — the schema home is an open implementing spec).
- Technical: the omnigent harness provides ephemeral envs, a human-in-the-loop
  option-card pause, and `cost_budget` policies enforced outside the prompt — so
  the carve's human gates + the cost budget + verdict write-authority map onto
  existing harness primitives, not new ones (source: RFC-0049 / RFC-0053 Evidence,
  omnigent fetched 2026-06-26).
- Process: the `release-lead` seat is RFC-accepted in principle (RFC-0049
  Decision 4); the pack home (OQ1) + agent shape (OQ2) are **delegated to this
  child spec** to resolve, which this spec does per the recommended defaults
  (source: RFC-0049 § Open questions; RFC-0048 D9 series-execution standard).
- Process: a new pack is a new top-level dir under `packs/`, normally RFC-gated;
  RFC-0049 (the parent) sanctions exactly this one pack via OQ1, so no further RFC
  is needed for the directory (source: AGENTS.md § Check before acting; RFC-0049
  OQ1).
- Process: this spec resolves the OQs and reconciles drift back into RFC-0048/0049
  in the same PR, per the series-execution standard — RFC-0049 stays Open until
  its OQs resolve; RFC-0048 stays provisional until its child set aligns (source:
  RFC-0048 D9 + Amendments section; RFC-0053's reconciliation precedent).
- Product: the release loop ships as an **opt-in** capability for adopters who
  deploy to ephemeral envs — not a `core`-wide default — because ephemeral-env
  infra is a real adopter prerequisite (source: RFC-0049 Drawbacks; the
  `discovery-lead`-in-`product-engineering` opt-in precedent, RFC-0053 D1).
- Product: the pack name `release-engineering` (agent `release-lead`, skill
  `release-loop`) is resolved here against derived naming tenets — `integration`
  rejected (CI collision, build/inner-loop term), `delivery` rejected (dual-track
  build-track term), bare `release` rejected (collides with the repo's own
  package-release register); `release-engineering` parallels `product-engineering`
  and dodges the overload. The name remains overridable (source: this spec's
  Boundaries § Ask first; user direction 2026-06-26 to resolve the OQs + pressure-test
  the name against derived tenets).
