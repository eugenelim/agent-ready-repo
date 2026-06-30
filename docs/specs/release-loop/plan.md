# Plan: release-loop

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done <!-- Drafting | Executing | Done -->


> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document is allowed to change as you learn. When it changes substantially
> (a different approach, not just a re-ordering), note why in the changelog
> at the bottom.

## Approach

The change is **content + governance reconciliation**, not code: a new opt-in
`release-engineering` pack holding one agent definition (`release-lead`) and one skill
(`release-loop`), reusing `core`'s `operational-safety` depth modules + the
`quality-engineer` and `security-reviewer` reviewers + the RFC-0053 sidecar
schema (carried in `product-engineering`'s `discovery-loop` skill, not `core`;
consumed by convention), and reconciling RFC-0049's two OQs + a tracked RFC-0048 amendment. The
shape is the established `implementer`/`discovery-lead` pattern: **shipping an
agent def + a loop skill is shipping content, not a runtime** — Principle 3 forbids
the harness, which omnigent supplies and we do not ship.

Order of operations: scaffold the pack shell first (T1) so the agent + skill have
a home and a manifest to register in; author the skill (T2) and the agent (T3) in
parallel against the spec's ACs; wire the reuse seam (T4 — the orchestrator-inlined
`operational-safety` modules for the loop's REVIEW step + the non-degradable
`security-reviewer` pass); produce the worked-example no-engine validation (T5 —
the load-bearing empirical artifact, mirroring RFC-0053's spike); then release
hygiene + projection + lint + the RFC-0048/0049 drift reconciliation (T6).

The **riskiest part** is the security/integrity contract (AC10) and the carve's
human-gate enforcement (AC4): the loop holds the irreversible-promotion act
RFC-0048 D1 reserves for the human, so the verdict-write-authority and
non-degradable-security controls must be specified at the same depth RFC-0053's
secure-design pass forced — a `security-reviewer` spec-stage read is the check.
The second risk is **scope sprawl** into the fidelity-ladder skills (RFC-0049 D3)
or the sidecar schema (RFC-0053) — both fenced off as Never-do / Ask-first.

## Constraints

- **RFC-0049** (the parent): the inner/outer split (D1), the minimum-regret carve
  (D2), convergence by policy (D6), the company-OS composition (D5); and its OQ1
  (pack home) + OQ2 (agent shape), which this plan resolves.
- **RFC-0048** (the foundation, Accepted 2026-06-30): the G4→G5 arc, the sidecar
  substrate, the company-OS framing; reconciled here as a tracked amendment (D9
  series-execution standard).
- **RFC-0053** (the sibling): the sidecar schema this loop consumes by convention (carried in `product-engineering`'s `discovery-loop` skill, not `core`), the
  `agent-def + skill + no-engine` pattern, and the § Security & integrity contract
  shape AC10 mirrors downstream.
- **RFC-0041 + ADR-0031**: doctrine + reference-library + reuse-existing-reviewers,
  **no engine, no new reviewer**; the deploy *flavor* this graduates; P5's
  non-skippable security posture.
- **ADR-0018**: the orchestrator-inlined progressive-disclosure depth mechanism
  the `operational-safety` reuse rides.
- **RFC-0025**: `work-loop` light/full + the iteration cap the outer cap mirrors.
- **RFC-0040**: the three-tier layout resolution the sidecar paths obey.

## Construction tests

Most tests are per-task (below). Cross-cutting:

**Integration tests:** none beyond per-task — there is no executable logic; the
cross-cutting verification is the **worked-example trace** (T5), which exercises
the full loop state machine (deploy→e2e→feedback→converge→gate) end-to-end on
paper, plus the forced cap-hit (AC8) and forced security-surface (AC10c) paths.

**Manual verification:** the spec-mode + diff-mode `adversarial-reviewer` pass
(iterate to `Clean — ready to commit.`) and the `security-reviewer` spec-stage
read (AC10 controls specified at depth) — prose has no mechanical test for
doctrine correctness.

## Tasks

### T1: The `release-engineering` pack shell exists and is registered

**Depends on:** none

**Tests:**
- `lint-packs` passes on `packs/release-engineering/pack.toml` +
  `.claude-plugin/plugin.json` (valid manifest, version present). Verifies AC2.
- `marketplace.json` lists the `release-engineering` pack after `make build-self`
  (goal-based: `grep release-engineering marketplace.json`). Verifies AC2 / AC13.
- **Precondition (the "grep to verify before importing" rule, applied to module
  names + sidecar slots):** confirm the six `operational-safety` REVIEW modules +
  `cloud-implementation-craft` exist as files under
  `packs/core/.apm/skills/operational-safety/references/`, and confirm the sidecar
  slot field-names (blackboard · open-questions · traceability · decision-log +
  the `meta` block `round` / `round_cap` / `cost_budget` / `cost_spent`) from
  `packs/product-engineering/.apm/skills/discovery-loop/references/sidecar-schema.md`
  **before** wiring them in T4/T2 — so the consume-by-convention claim is
  falsifiable here, not mid-EXECUTE. (Verified during PLAN: all seven modules and
  all four slots + the meta block exist.)

**Approach:**
- Create `packs/release-engineering/` with `pack.toml`, `.claude-plugin/plugin.json`
  (version `0.1.0`), and `README.md` describing the SRE/ops outer-loop seat and
  its `core` hard-dependency + cloud/platform detect-and-degrade.
- Declare the `core` hard-dependency (`operational-safety` +
  `quality-engineer` + `security-reviewer`) per the pack-manifest convention; the
  sidecar schema is consumed by convention (definition carried in
  `product-engineering`'s `discovery-loop`, not `core`), so it is **not** a manifest
  hard-dependency on `core` or `product-engineering`.
- **Two distinct scope axes — do not conflate them.** (1) **Adopter install
  scope:** `release-engineering` is **`repo`-scope** (`pack.toml`
  `[pack.install] default-scope = "repo"`, `allowed-scopes` including `repo`) —
  this is **architecturally load-bearing** (AC2 / AC9): the pack installs into the
  same build repo `work-loop` ran in, where `core` is repo-installed, so the reuse
  of `core`'s repo-scope `quality-engineer` / `security-reviewer` /
  `operational-safety` resolves at the same scope. This is the deliberate
  scope-**inverse** of the user-scope `discovery-lead`. (2) **This repo's
  self-host projection:** `release-engineering` is **not** in
  `recipes/self-host.toml`'s `include` list, so `make build-self` does **not**
  project its agent/skill into this repo's `.claude/` tree (the
  core + governance-extras + user-guide-diataxis scope) — it is only advertised in
  `marketplace.json` via aggregation. Setting `default-scope = "user"` to "match"
  the non-projection would invert AC9's reuse soundness — the two axes are
  orthogonal.

**Done when:** `lint-packs` is green on the new pack and `marketplace.json`
carries it after build-self.

### T2: The `release-loop` skill drives the deployed outer loop

**Depends on:** T1

**Tests:**
- Activation legibility (judgmental, the `discovery-loop` precedent — no
  activation eval): the skill `description` carries the activating triggers
  (deploy / e2e / "ship the integrated whole" / "iterate the deployed env") and a
  disjoint `Do NOT use` clause fencing it off from the inner-loop build. Verifies
  AC1 (legible inner/outer boundary). `release-loop` is **not** added to
  `[pack.evals]` (supervisor-run loop skill, like `discovery-loop`).
- `grep` presence checks against AC3–AC8: both carve zones, the convergence
  policy (canary + e2e coverage of changed surface + flake < 2%), DORA as health
  signal, the outer cap + stall-surface, the sidecar-consumption slots. Verifies
  AC3–AC8.
- `grep` presence of the **release-readiness gate** (AC6b): the readiness-record
  assembly before G5 (convergence result + operational + security verdicts +
  cumulative error-budget status), the *ratify-a-record* framing, the AC10(d)
  advisory-until-validated constraint on the telemetry pre-fill, and the explicit
  `error-budget: not-defined` recorded field when the artifact is absent. Verifies AC6b.
- `lint-packs` + `tools/lint-agent-artifacts.py` pass on the SKILL.md frontmatter.

**Approach:**
- Author `packs/release-engineering/.apm/skills/release-loop/SKILL.md`: the cycle
  (deploy to ephemeral env → e2e → observe telemetry → finding to the sidecar
  blackboard → back to `work-loop` inner loop → redeploy → converge), the
  minimum-regret carve (two zones, AC3/AC4), the reversibility primitives (AC5),
  convergence by policy + DORA (AC6), the inner↔outer feedback seam + sidecar
  consumption (AC7), the outer cap + cost budget + stall-surface (AC8), and the
  **release-readiness gate** (AC6b — assemble the readiness record consolidating
  the convergence + operational + security verdicts + cumulative error-budget
  status, AC10(d)-validated telemetry, ratified at G5; record an explicit
  `error-budget: not-defined` field when the artifact is absent).
- Keep every sentence **harness- and tool-neutral**; name omnigent + cloud/IaC
  tools only as *illustrative* (Principle 1).
- Cross-link `operational-safety`'s modules + the `quality-engineer` /
  `security-reviewer` reuse rather than restating their content (one canonical
  home).
- Add `references/` modules only if the SKILL.md body would otherwise exceed the
  lean-prose bar — default to inline.

**Done when:** activation legibility reads clean (triggers + disjoint Do-NOT-use
in the frontmatter), the AC3–AC8 and AC6b grep checks are present,
and `lint-packs` is green.

### T3: The `release-lead` agent definition is the outer-loop supervisor

**Depends on:** T1

**Tests:**
- `tools/lint-agent-artifacts.py` + `lint-packs` pass on the agent frontmatter
  (valid `name`, `description`, `tools:` surface, `model:`). Verifies AC13.
- `grep` presence: the agent states it is a **peer** of `work-loop`'s supervisor
  + `discovery-lead`, **not** a `work-loop` mode, and runs `release-loop`.
  Verifies AC1.

**Approach:**
- Author `packs/release-engineering/.apm/agents/release-lead.md`: the SRE/ops
  outer-loop supervisor; loads AGENTS.md + CONVENTIONS + the spec/plan; runs the
  `release-loop` skill; right-sizes solo / fan-out-to-disjoint-deploy-targets
  (mirroring `discovery-lead`'s solo / lens-team topology, controller + blackboard,
  never agent-to-agent chat); talks to the human at the consent gates.
- Set the `tools:` surface to what a deploy/e2e supervisor needs (Read, Grep,
  Glob, Bash, Edit/Write for the sidecar) — no more (least-privilege).

**Done when:** the agent passes `lint-agent-artifacts.py` + `lint-packs` and the
AC1 peer/non-conflation framing greps clean.

### T4: The reuse seam is wired — `quality-engineer` + `security-reviewer`, no new agent

**Depends on:** T2, T3

**Tests:**
- `grep` presence: the loop's REVIEW step dispatches against the
  `operational-safety` Module index (the named modules: `environment-isolation`,
  `blast-radius`, `cost-and-teardown`, `drift-and-rollback`,
  `observability-and-smoke`, `state-and-idempotency`) inlined into the
  `quality-engineer` brief via the existing mechanism (ADR-0018). Verifies AC9.
- `grep` presence + `git diff` absence: the non-degradable `security-reviewer`
  pass on deploy diffs (AC10c); **no new reviewer agent** added under
  `packs/release-engineering/.apm/agents/` beyond `release-lead`; `loop-cohort.py` /
  `lint-spec-status.py` byte-unchanged. Verifies AC9 / AC10c.
- `grep` presence of the AC10 controls (a–i) + the AC7 artifact-provenance
  control in the skill/agent body — including (g) deploy-credential tiering (named
  `credbroker` boundary + falsifiable tier scoping), (h) ephemeral-env-isolation-as-
  precondition, and (i) sidecar data-classification + branch-protection. Verifies AC10.

**Approach:**
- In `release-loop` SKILL.md, wire the orchestrator-inlined
  `operational-safety` routing for the loop's REVIEW step (reuse the
  `work-loop`/`security-checklists` table-routed mechanism — load only the modules
  the cycle raises, inline into the reviewer brief, never self-discovered), and
  wire `cloud-implementation-craft` (the EXECUTE-craft module) where the loop
  authors/scaffolds deploy/smoke/teardown artifacts.
- Specify the AC10 security/integrity controls (a–i, plus the AC7 artifact
  provenance) as loop doctrine: verdict write-authority (harness-attested);
  audit-trail decision log **(harness-delegated posture — named omnigent
  immutable-log guarantee + anchored hash-chain tip; in-repo add-only lint named
  as the adopter's option, not shipped)**; non-degradable security lens on a
  crossed boundary; telemetry/canary/log integrity (advisory-until-validated **+
  the `untrusted:` marking discipline + inert-promote**); auto-rollback
  circuit-breaker (**oscillation-attempt trigger + cost trigger**); teardown
  guarantee; **deploy-credential tiering** (named four-broker `credbroker`
  boundary; no prod-tier token reachable from the ephemeral zone — falsifiable);
  **ephemeral-env isolation as a carve precondition**; **sidecar
  data-classification** (`public`/`internal`/`sensitive`/`regulated`,
  redact-or-surface before a shared-store write + state-branch history protection).

**Done when:** the AC9 + AC10 greps are present (controls a–i + provenance), no new
agent/engine is added, and the frozen scripts show empty `git diff`.

### T5: The worked-example trace demonstrates no-engine (cap-hit + security-surface forced)

**Depends on:** T2, T3, T4

**Tests:**
- The trace under `docs/specs/release-loop/notes/` walks **one full cycle**
  and shows every transition is a file edit + a policy check (no runtime).
  Verifies AC12.
- The trace **forces four negative paths** — a cap-hit (AC8 stall-surface), a
  security-boundary-with-no-lens (AC10(c) surface), a forged-consent attempt
  rejected (AC10(a)), and an in-place decision-log tamper detected (AC10(b)) —
  and **flags** the single-example / single-operator limit. Verifies AC12.

**Approach:**
- Author `notes/01-worked-example-trace.md`: a deployed e2e defect → finding to
  the blackboard → inner-loop fix → redeploy → canary + coverage + flake converge
  → surface the G5 consent gate, on the form omnigent stores (worktree files +
  the four sidecar slots).
- Re-use RFC-0048 note 02's worked example (`example-assistant`) as the subject so
  the trace is continuous with the upstream prototype.
- Inject the four negative paths: the cap-hit, the no-lens surface, a controller
  self-write of a `ratified_by: human` row that resume rejects, and an in-place
  edit of a prior decision-log row that the anchored-tip check detects.
- State the Threats-to-validity honestly (one example, single operator, the four
  negative paths exercised by injection not natural occurrence).

**Done when:** the trace exists, exercises the two forced paths, and reads as a
no-engine demonstration with its limits flagged.

### T6: ADR, release hygiene, projection, lint, and RFC-0048/0049 drift reconciliation

**Depends on:** T2, T3, T4, T5

**Tests:**
- A new ADR ("the inner/outer loop split + the minimum-regret deploy carve")
  exists under `docs/adr/` and is linked from RFC-0049's follow-on list. Verifies
  AC11b.
- `make build-self` clean; `make build-check`, `tools/lint-agent-artifacts.py`,
  `tools/lint-agents-md.py`, `lint-seeds` all pass. Verifies AC13.
- RFC-0049 § Open questions records OQ1 + OQ2 resolved (pointing to this spec);
  RFC-0048 § Amendments carries a dated tracked entry for the release-lead
  seat + pack home + agent shape + company-OS third seat. Verifies AC11.
- `docs/specs/README.md` lists `release-loop`; `docs/product/changelog.md`
  has an `[Unreleased]` entry. Verifies AC13.

**Approach:**
- Author the RFC-0049 follow-on **ADR** (the inner/outer split + the
  minimum-regret deploy carve) via `new-adr`, recording the carve as the
  expensive-to-reverse decision (AC11b).
- Resolve RFC-0049's OQ1 (dedicated opt-in `release-engineering` pack) + OQ2 (distinct
  `release-lead` agent + `release-loop` skill) **in RFC-0049's § Open
  questions**, recording the grounding (the RFC-0053 "None remain open" pattern).
  **Surface to the operator** whether RFC-0049 flips to `Accepted` in this PR (it
  is `Open`; its OQs decide-by this child spec — a circular gate this PR closes).
- Add a dated RFC-0048 § Amendments entry (the D9 reconcile-drift obligation):
  the release-lead seat + pack home + agent shape now specified; the
  company-OS third (SRE/ops) seat confirmed; the work→release (deploy) and
  release→prod (G5) handoffs wired.
- Bump `packs/release-engineering/pack.toml` + `plugin.json`; refresh `marketplace.json`
  (build-self); add the changelog `[Unreleased]` entry; add `release-loop` to
  `docs/specs/README.md`.

**Done when:** the ADR exists, all lint surfaces pass, the OQs are recorded
resolved, the RFC-0048 amendment is in place, and the README + changelog are
updated.

## Rollout

- **Delivery:** content only — a new opt-in pack. Reversible: the pack is additive
  (no `core` behavior change beyond the `marketplace.json` version aggregation).
  Nothing irreversible ships.
- **Infrastructure:** none — the spec ships no runtime; the loop *offers to
  scaffold* an adopter's deploy / smoke / teardown artifacts, it does not ship
  them.
- **External-system integration:** the omnigent harness (ephemeral envs, HITL
  pause, cost policies) and the RFC-0053 sidecar schema (carried in
  `product-engineering`'s `discovery-loop` skill, not `core`) are
  named-but-not-built dependencies — the loop consumes both by convention until
  RFC-0053's schema lands; flagged in the spec Assumptions.
- **Deployment sequencing:** T1 before T2/T3 (pack home before its residents);
  T4 after T2/T3 (the seam wires both); T6 last (reconciliation needs the
  artifacts to exist).

## Risks

- **The sidecar schema (RFC-0053; carried in `discovery-loop`, not `core`) is not built yet.** AC7 consumes it by
  convention until it lands; if RFC-0053's schema differs from the slots named
  here, AC7's wording needs a follow-up sync. Mitigation: cite RFC-0053 as the
  single source and name the consume-by-convention fallback explicitly (spec
  Assumptions).
- **Scope sprawl into the fidelity ladder (RFC-0049 D3) or the harness.** Fenced
  as Never-do / Ask-first; the worked example references but does not author
  local-infra-equivalents.
- **The security/integrity controls under-specified.** The `security-reviewer`
  spec-stage pass is the check; mirror the AC10 control set's depth exactly
  (controls a–i + the AC7 artifact-provenance control).

## Changelog

- 2026-06-26: initial plan (resolves RFC-0049 OQ1 + OQ2; mirrors RFC-0053's
  agent-def + skill + no-engine shape downstream).
- 2026-06-30: pre-EXECUTE review sharpenings folded into the contract before
  implementation. T1: declared the pack **`repo`-scope** (was mis-described as
  user-scope-default — that conflated install-scope with this repo's self-host
  projection; repo-scope is load-bearing for AC9 reuse soundness) + a precondition
  test (verify the named `operational-safety` modules + sidecar slots exist).
  AC10 sharpened: (b) harness-delegated posture + anchored hash-chain tip, in-repo
  lint named as the adopter's option not shipped; (d) the `untrusted:` marking
  discipline + inert-promote; (g) named four-broker `credbroker` boundary +
  falsifiable tier-scoping; new (i) sidecar data-classification + redact-or-surface
  + state-branch protection (the RFC-0053 control-7 LINDDUN leg, dropped before).
  AC12 extended to force four negative paths (added forged-consent-rejected +
  decision-log-tamper-detected). Count-coupled "nine" prose made count-free.
