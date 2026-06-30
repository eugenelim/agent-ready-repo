# RFC-0049: The release loop — deployed e2e validation, the minimum-regret deploy carve, and the company-OS composition

- **Status:** Accepted <!-- Draft | Open | Final Comment Period | Accepted | Rejected | Withdrawn | Experimental -->
- **Parent:** a **child of [RFC-0048](0048-autonomous-product-team-operating-model.md)** (**Accepted 2026-06-30**). RFC-0048's child-set reconciliation treated this RFC as *modelled* — the `release-lead` seat is specified by the drafted [release-loop spec](../specs/release-loop/spec.md) and recorded at RFC-0048 § Amendments (the 2026-06-26 SRE-seat entry + the 2026-06-28 reviewer-reuse scope) — so 0048 could accept on RFC-0053's blockers **without** waiting on this RFC's implementation. **This RFC is now Accepted (2026-06-30)** — its implementing PR landed the `release-engineering` pack (the `release-lead` agent + `release-loop` skill), resolved OQ1/OQ2 in this RFC per their recommended defaults, authored the follow-on ADR-0044, and recorded the reconciling amendment into RFC-0048 (the gate arc, the company-OS framing).
- **Author:** eugenelim
- **Approver:** eugenelim
- **Date opened:** 2026-06-25
- **Date closed:** 2026-06-30
- **Decision weight:** heavy <!-- light | standard | heavy — defines deploy-to-prod autonomy doctrine (an irreversible + security boundary) and adds a new opt-in pack + agent; it reuses existing reviewers and runtime, but the prod / data / spend / irreversible gating is the heavy part, so explicit Approver sign-off is warranted. -->
- **Related:** [RFC-0048](0048-autonomous-product-team-operating-model.md) (the discovery+build foundation this extends — it details G0–G4; this details G4→G5) · RFC-0041 (infra-aware `work-loop` — whose deploy *flavor* this graduates into a proper outer loop) · RFC-0025 (`work-loop`) · `operational-safety` pack (the reliability/observability reference library this reuses) · [RFC-0051](0051-the-self-coverage-gate.md) (the self-coverage *goal* this loop realizes through a deploy-appropriate composite — see *Self-coverage — the release loop's guiding goal*) · omnigent (the harness; ephemeral-env + option-card support) · promoted design in [`0049-notes/`](0049-notes/)

## Reviewer brief

- **Decision:** whether to add a deployed e2e-validation **release loop** (the outer loop) above `work-loop`'s inner build loop, carve deploy autonomy by minimum-regret, and add a `release-lead` SRE/ops seat — completing the product → engineering → SRE "company OS".
- **Recommended outcome:** accept.
- **Change if accepted:**
  - Split the loop into **inner** (`work-loop`, local with local-infra-equivalents) and **outer** (`release-loop`, ephemeral deploy + e2e + iterate-to-converge).
  - Add a `release-lead` agent + `release-loop` skill in a new opt-in, **repo-scope** `release-engineering` pack, reusing `operational-safety` + `quality-engineer` + `security-reviewer` + the RFC-0053 sidecar — **no new runtime, no new reviewer** (the reuse of `core`'s repo-scope reviewers is sound because the pack is **repo-scope and co-located in the build repo** where `core` is installed — see OQ1).
  - Carve autonomy by **minimum-regret**: agents run inner + outer loops on ephemeral envs unwatched; humans gate prod / data / spend / security / irreversible (G5).
- **Affected surface:** a new **repo-scope** `release-engineering` pack (installed into the build repo) + agent + skill carrying the inner/outer split + the minimum-regret deploy carve as **`release-loop` skill doctrine** (not a CONVENTIONS edit — RFC-0048 § Amendments 2026-06-29); reuse of `core`'s operational/security reviewers + the RFC-0053 sidecar; the `omnigent` harness (ephemeral envs).
- **Stakes:** costly-to-reverse — it sets deploy-to-prod autonomy doctrine (an irreversible + security boundary); the prod-ship step itself stays human-gated, so the irreversible move is bounded.
- **Review focus:** (1) the minimum-regret carve draws the agent/human line correctly (reversible ⇒ autonomous on ephemeral; irreversible ⇒ human); (2) the no-new-runtime / no-new-reviewer claim holds for the release loop.
- **Not in scope:** building the harness; the exact `release-lead` agent shape (OQ2 — resolved by the child spec; the pack home, OQ1, already resolves to a new `release-engineering` pack); RFC-0048's G0–G4 discovery+build foundation (this is its G4→G5 extension).

## The ask

**Recommendation (BLUF).** On top of RFC-0048's discovery + build foundation, add the
**release loop** — a deployed **e2e-validation outer loop**. `work-loop` is the
**inner loop** (local build, made self-sufficient by local-infra-equivalents); the
**release-loop** deploys the integrated whole to an **ephemeral environment**, runs
e2e, observes telemetry, and **iterates with the inner loop until the deployed whole
converges**, then ships to prod at **G5** (human-ratified). Carve autonomy by
**minimum-regret**: agents run the inner loop *and* the outer loop **on ephemeral envs**
unwatched; humans gate prod / data / spend / security / irreversible. Add an
**`release-lead`** agent (the SRE/ops supervisor) — doctrine + reuse of
`operational-safety` + `quality-engineer` + `security-reviewer` + RFC-0041's infra doctrine, **no new runtime**,
running on the omnigent harness. This completes the **"company OS"**: product (discovery)
→ engineering (build) → SRE/ops (release).

**Why now (SCQA).** *Situation:* RFC-0048 gets the catalogue from vision → locally-built,
deploy-ready code (G0–G4). *Complication:* **deployed infrastructure surfaces what you
can't catch up front** (the irreducible shift-right ~20% — real traffic, infra drift,
version combinations, emergent behavior). RFC-0041 made `work-loop` infra-aware but kept
deploy as a *flavor* of the inner loop, with no ephemeral-env outer loop and no
iterate-until-converge — so the human becomes the relay for deployed findings.
*Question:* how far into deploy + e2e can agents go autonomously, with minimum regret?

**Decisions requested.**
| ID | Question | Recommendation | Why | Decide by | Reviewer action |
| --- | --- | --- | --- | --- | --- |
| D1 | Adopt the inner/outer split — `work-loop` = inner (local, with local-infra-equivalents); a new `release-loop` = outer (ephemeral deploy + e2e + iterate)? | Adopt | The inner loop can't surface deployed-only failures; the outer loop iterates the deployed whole to convergence | RFC accept | Confirm the inner/outer split |
| D2 | Adopt the minimum-regret carve — autonomous on the inner loop and the outer loop on ephemeral envs; human-gated at first real users/data, migrations, spend over threshold, security, anything irreversible, and prod ship (G5)? | Adopt | The reversibility primitives (ephemeral envs + feature flags + auto-rollback) make unwatched autonomy safe up to the irreversible line | RFC accept | Confirm where the carve draws the agent/human line |
| D3 | Make local-infra-equivalents a build-loop obligation — the fidelity ladder (fakes → contract tests → Testcontainers → LocalStack → docker-compose)? | Adopt | Software must run and verify locally before deploy, so the inner loop is self-sufficient | RFC accept | Confirm the obligation + the ladder |
| D4 | Ship `release-lead` (the outer-loop / SRE-ops seat) as an agent + a `release-loop` skill, reusing `operational-safety` + `quality-engineer` + `security-reviewer` + RFC-0041? | Adopt | A reuse-not-rebuild seat; no new runtime, no new reviewer | RFC accept (the seat) | Confirm the seat; pack home (OQ1) resolves to a new `release-engineering` pack, exact agent shape is OQ2 |
| D5 | Adopt the company-OS composition — three loop-teams (discovery → build → release) on RFC-0048's shared substrate, handing off at G3, at deploy, and at G5? | Adopt | Completes the autonomous product team end to end on one substrate | RFC accept | Confirm the three-team composition + the hand-offs |
| D6 | Adopt convergence by policy — promotion judged by automated policy (canary analysis + e2e coverage of the changed surface + flake < 2%) up to the irreversible human gate, with DORA as the health signal? | Adopt | Makes outer-loop promotion a checkable policy, not a human relay | RFC accept | Confirm the promotion policy + DORA as the signal |

## Problem & goals

**Diagnosis.** RFC-0048 ends at deploy-ready code. But (a) the inner loop is only autonomous
if the software *runs locally* without the real deployed infra — which requires
local-infra-equivalents the packs must produce; and (b) a deployed, integrated, distributed
system surfaces failures that no pre-deploy testing replicates (shift-right). Without an
outer loop, those findings are relayed by a human — the anti-pattern RFC-0041 named.

**Goals.** Drive the deployed e2e loop end-to-end autonomously *on reversible (ephemeral)
infrastructure*; iterate inner↔outer until convergence; keep humans at the irreversible
exits only; complete the company OS.

**Non-goals.** Running the live product-as-a-managed-service long-term (that's adopter
ops); a new deploy *runtime* (reuse the harness + IaC via `operational-safety`); replacing
`work-loop` (it remains the inner loop).

## Proposal

The full design is in [`0049-notes/01`](0049-notes/01-three-loops-and-company-os.md);
summary:

- **Inner loop = `work-loop`.** Local build + verification via the fidelity ladder
  (fakes → Pact → Testcontainers → LocalStack → docker-compose); run as high up as a
  sub-5-min budget tolerates; push the rest to the outer loop.
- **Outer loop = `release-loop`** under `release-lead`: deploy the integrated whole
  to an **ephemeral environment** → run e2e → observe telemetry (observability-driven) →
  feed findings back to the inner loop → redeploy → **converge** → assemble a
  **release-readiness record** (the *launch* PRR — the convergence result + the
  operational + security review verdicts + SLO/error-budget status, consolidating
  checks the loop already runs) → **G5** ship, where the human **ratifies the
  record** rather than a bare go/no-go. (This elaborates the existing G5 human gate;
  ongoing error-budget monitoring + on-call ownership stay with the future operate/incident loop.)
- **Minimum-regret carve** (the autonomy law applied to deploy): reversible (ephemeral)
  ⇒ autonomous; irreversible (prod/data/spend/security) ⇒ human.
- **Company OS:** three loop-teams on 0048's substrate; the release-loop is the SRE/ops
  seat, reusing `operational-safety` + `quality-engineer` + `security-reviewer`.

**Self-coverage — the release loop's guiding goal.** The release loop exists to **maximize deploy
autonomy** — take the agent as far into deploy + e2e as minimum-regret allows before a human is
needed. That *is* the **self-coverage goal** RFC-0048 names and [RFC-0051](0051-the-self-coverage-gate.md)
owns: *substitute rigorous checklists for what would otherwise be surfaced to a human; resolve
autonomously everything a checklist can resolve (**resolve-vs-surface**), and surface only the
irreducible.* The release loop realizes that goal **not** through the seven design-convergence
modules (there is no design artifact to ground, and it converges empirically on telemetry) but
through a **deploy-appropriate composite**:

- **Checklist content** — `operational-safety` (reliability: state & idempotency, blast-radius,
  drift & rollback, cost & teardown, observability), `security-reviewer` (the *security* gate), and
  `quality-engineer` (change quality). No single library covers it — `operational-safety` is the
  reliability lens only; the loop's human gates (prod / data / spend / **security** / irreversible)
  span more than reliability.
- **The stop-rule** — the automated convergence policy (canary analysis + e2e coverage of the
  changed surface + flake < 2%, DORA as the health signal — Decision 6). The **coverage record the
  seam requires is the pair**: the policy result (the empirical leg) *plus* the carve's recorded
  per-finding dispositions (the resolve-vs-surface leg). The policy alone is not the record — a
  green canary can pass while a class of risk was never enumerated; what makes the record
  non-skippable is that every deployed-only finding carries an explicit resolved-or-surfaced
  disposition, not just a telemetry gate.
- **The resolve-vs-surface disposition** — the minimum-regret carve (Decision 2): resolve
  autonomously everything reversible (ephemeral envs + flags + auto-rollback make it groundable);
  surface to the human the irreducible. The carve's static reversible/irreversible cut is the
  *floor*, not the whole predicate: a finding the composite **cannot ground** surfaces regardless of
  reversibility — e.g. a non-deterministic or novel failure that auto-rollback *masks but does not
  explain*, or convergence that needed anomalous iteration (a flapping canary, a coverage gap closed
  by retries). "Resolved autonomously" requires a *grounded* resolution, not merely a reversible
  one.

Applying resolve-vs-surface *across* the composite — every finding either resolved-with-a-referent
or surfaced-with-a-reason — is what keeps the carve honest: the loop surfaces only what a checklist
genuinely cannot resolve, which is precisely what lets it run unattended up to the irreversible
line. This **conforms to RFC-0051's cross-loop seam** (goal + resolve-vs-surface + a non-skippable
coverage record); it carries **no copy of the seven modules** and adds **no new reviewer** — the
same reuse-not-rebuild posture as Decision 4.

## Options considered

Axis: **where the deploy/e2e validation happens and who drives it.**
| Option | Shape | Verdict |
| --- | --- | --- |
| **A. Do nothing** | stop at 0048's deploy-readiness; humans relay deployed findings | Cost: the shift-right ~20% reaches a human as raw deploy errors — the RFC-0041 relay anti-pattern. Rejected. |
| **B. Deploy flavor inside `work-loop`** (RFC-0041 as-is) | inner loop also does apply + smoke | Conflates fast/local with slow/stateful/deployed; no ephemeral-env iterate-until-converge. Insufficient. |
| **C. A separate outer `release-loop` on ephemeral envs** ★ | inner/outer split; reversibility primitives | **Recommended** — the DevOps inner/outer ontology; ephemeral envs make it low-regret + autonomous. |
| **D. Full autonomous prod deploy** | agent ships to prod unwatched | Crosses the irreversible line; violates the minimum-regret carve. Rejected. |

## Risks & what would make this wrong

- **Pre-mortem:** ephemeral-env cost sprawl (mitigate: idle auto-shutdown, spot, teardown
  on cycle end); LocalStack/Testcontainers fidelity gaps mean some findings *only* appear
  in the outer loop (that's *why* the outer loop exists); AI-velocity increases change-fail
  rate (2025 DORA) — so canary gating must be strict.
- **Key assumptions (falsifiable):** ephemeral envs make deploy reversible-enough to
  automate; canary metric analysis + e2e coverage + flake are a sufficient promotion
  signal up to the human gate; the inner loop can reach useful fidelity locally.
- **Drawbacks:** ephemeral-env infra is a real adopter prerequisite; contract-testing
  (Pact) has provider-side adoption friction (Deloitte).

## Evidence & prior art

- **Spike/de-risk:** the inner/outer loop + ephemeral-env pattern is the established
  developer-experience ontology (boundary = `git push`); the reversibility-unlocks-autonomy
  claim is the same logic RFC-0048 already uses for tests-as-verifier, applied to deploy.
- **Repo precedent:** RFC-0048 (foundation), RFC-0041 (infra-aware `work-loop` — this
  graduates its deploy flavor), `operational-safety`, `work-loop` supervisor + `loop-cohort`.
- **External prior art** (fetched; full set in [`0049-notes/01`](0049-notes/01-three-loops-and-company-os.md)):
  inner/outer loop ([Telepresence](https://telepresence.io/docs/concepts/devloop)) ·
  contract testing ([Pact](https://docs.pact.io/)) · [Testcontainers](https://testcontainers.com/modules/localstack/)
  + LocalStack · ephemeral preview environments ([Northflank](https://northflank.com/blog/the-what-and-why-of-ephemeral-preview-environments-on-kubernetes-sandbox-testing)) ·
  shift-right / testing in production ([Microsoft](https://learn.microsoft.com/en-us/devops/deliver/shift-right-test-production),
  Charity Majors) · progressive delivery + auto-rollback ([Argo Rollouts](https://argo-rollouts.readthedocs.io/en/stable/features/analysis/)) ·
  [DORA metrics](https://octopus.com/devops/metrics/dora-metrics/).

## Open questions

*Both resolved per their recommended defaults by the child spec
([`docs/specs/release-loop/`](../specs/release-loop/spec.md), 2026-06-26) — recorded
here with where each landed (the RFC-0053 "None remain open" pattern). Neither was a
value/scope/conflict call; the recommendations were referent-grounded, so the child resolves
rather than re-litigates.*

1. **`release-lead`'s pack home — resolved: a dedicated opt-in `release-engineering` pack.**
   Not `core` — `core` is the universal base, and deploy-to-ephemeral-env is an opt-in
   capability with a real adopter prerequisite (ephemeral-env infra), exactly like discovery,
   which ships `discovery-lead` in the opt-in `product-engineering` pack, not `core`
   (RFC-0053 D1). The pack **hard-depends on `core`** (`operational-safety` +
   `quality-engineer` + `security-reviewer`) and detect-and-degrades on
   cloud/platform packs.

   **Scope — repo-scope, co-located in the build repo (this is what makes the
   reviewer reuse sound).** `release-engineering` installs at **repo scope**, into the
   same repo `work-loop` (the inner loop) ran in — the repo that holds the built,
   deploy-ready component and where `core` is therefore repo-installed. That co-location
   is *precisely what makes reusing `core`'s repo-scope `quality-engineer` /
   `security-reviewer` / `operational-safety` sound*: the reused reviewers and
   `release-lead` sit at the same scope in the same repo, so the reuse resolves by
   construction — `release-lead` is the downstream, repo-scope peer of `work-loop`'s
   supervisor (itself `core`, repo-scope) reusing the same reviewers, **not** a
   user-scope agent reaching for repo-scope reviewers it cannot assume are present. This
   is the **deliberate scope-inverse of the discovery loop's resolution**
   ([RFC-0048](0048-autonomous-product-team-operating-model.md) § Amendments — the
   2026-06-26 scope-decoupling entry + DRIFT-E): `discovery-lead` is **user-scope**
   because discovery runs *upstream of G3*, in non-repo document workspaces that cannot
   assume a `core` install, so it ships its **own** user-scope reviewers
   (`discovery-threat-reviewer` / `discovery-reliability-reviewer`); `release-lead` runs
   *downstream of the build, in the build repo*, so it **reuses** `core`'s. The same
   "user-scope-agent-reaching-for-a-repo-scope-reviewer is a footgun" rule, applied at
   opposite scopes — *scope follows where the work happens*, and the company-OS scope
   boundary falls at the G3 handoff where shaping becomes a concrete repo. ("Parallels
   `product-engineering`" below is a **discipline/seat-name** parallel, not a scope claim
   — the two packs are opt-in for different prerequisite reasons and need not share
   scope.)

   **Cross-repo / value-stream reach.** In a single product monorepo the build repo *is*
   the integrated whole, so the above holds directly. In a **polyrepo / value-stream**
   topology the "integrated whole" spans component repos. Two distinct mechanisms are in
   play, and conflating them would re-import the very presence assumption the discovery
   footgun rule forbids: **(i) reviewer presence is an adopter precondition, not something
   ADR-0022 provides** — each component repo, and whatever repo hosts the cross-component
   integrated-whole deploy + e2e (a value-stream meta-repo or a designated integration
   repo), must *itself* install `core` + `release-engineering` at repo scope; **absent that
   install the per-repo reuse is not sound, and the loop surfaces the gap rather than
   assuming the reviewers are present** (the same fail-closed posture as the discovery loop,
   one scope up). **(ii) artifact referencing across repos** — pointing at the other
   components' contracts / specs / built versions — uses the cross-repo mechanism already
   decided in [ADR-0022](../adr/0022-value-stream-meta-repo-cross-component-layer.md)
   (reference-by-version + the read-only courier snapshot), the same mechanism RFC-0048's
   traceability chain crosses repos with (§ Amendments, the 2026-06-25 note-08
   generalization), **not** a new coordinator. So `release-loop` runs **per-component-repo**
   (reuse sound where both packs are installed), and the cross-component e2e runs in its
   `core`-bearing host repo. The monorepo case is the minimum; the per-repo + named-install
   precondition + reference-by-version model is the generalization, detailed by the
   implementing spec where a concrete topology needs it.

   It **consumes the sidecar schema by convention** — reading the
   produced `_state/` instances and checking the `schema_version` stamp, not importing a
   shared definition (the schema *definition* is carried in `product-engineering`'s
   `discovery-loop` skill, per RFC-0048 § Amendments 2026-06-26 / RFC-0053 D2), so it adds no
   hard dependency on `product-engineering`. **Name `release-engineering`** — the discipline/seat name,
   parallel to `product-engineering` (the two company-OS discipline packs), keeping the
   agent/skill on a `release-*` prefix (`release-lead` / `release-loop`). Rejected:
   `integration` (collides with **Continuous Integration**, a build/*inner*-loop term —
   "integration" naming the *outer* loop reads backwards to anyone fluent in CI/CD);
   `delivery` (the dual-track ontology binds "delivery" to the *build* track — RFC-0048
   D7/D8 names `work-loop` "the delivery track"); a bare `release` pack (collides with the
   repo's own package-release register — `release-agentbundle.yml` / `[Unreleased]`, meaning
   *publish our own tooling*; the compound dodges it). The **concept is renamed in lockstep**
   — this RFC is "the release loop," its gate-arc step is "release (outer)," and the artifacts
   are `release-*`, so the whole reads uniformly (no concept/artifact split). The name remains
   the one taste call, overridable. · resolved-by: child spec AC2.
2. **Agent shape — resolved: a distinct `release-lead` agent + a `release-loop`
   skill.** The inner/outer split is real (different inputs — local code vs the deployed whole;
   different verifier — local tests vs deployed telemetry/canary; different autonomy posture —
   G4-auto vs ephemeral-auto/prod-gated), and RFC-0053 already confirmed the identical pattern
   upstream (`discovery-lead` agent + `discovery-loop` skill, not a `work-loop` mode). It
   heavily reuses `operational-safety` + `quality-engineer` + `security-reviewer`, adds no new
   reviewer, ships no engine (ADR-0031 idiom). · resolved-by: child spec AC1.

## Follow-on artifacts

Filled on acceptance:
- ADR: the inner/outer loop split + the minimum-regret deploy carve. *Authored:
  [ADR-0044](../adr/0044-inner-outer-loop-split-and-minimum-regret-deploy-carve.md)
  (Accepted 2026-06-30) — the sibling of RFC-0041's ADR-0031 / RFC-0053's ADR-0043,
  recording the expensive-to-reverse architectural decision the carve embodies.*
- Spec: `release-loop` + `release-lead` (+ its pack). *Shipped:
  [`docs/specs/release-loop/`](../specs/release-loop/spec.md) — implemented in this
  PR, all 15 ACs checked —
  resolves OQ1 (pack home → opt-in `release-engineering` pack) + OQ2 (distinct
  `release-lead` agent + `release-loop` skill); specifies the deploy + e2e +
  iterate-to-converge loop, the minimum-regret carve, the reuse of
  `operational-safety` + `quality-engineer` + `security-reviewer`, the sidecar
  consumption by convention (schema carried in `discovery-loop`, not `core`), the
  security/integrity control set (controls a–i + the AC7 artifact-provenance
  control), and the **release-readiness gate** (AC6b — the launch PRR consolidated
  before G5).*
- Amendment back into RFC-0048: reconcile its gate arc / company-OS framing as this lands.
  *Recorded — see RFC-0048 § Amendments, 2026-06-26 (the release-lead seat + pack home +
  agent shape specified; the company-OS third (SRE/ops) seat confirmed) and the
  2026-06-30 entry (RFC-0049 implemented — the `release-engineering` pack built, the
  work→release + release→prod handoffs wired).*
- Loop-skill doctrine (not a CONVENTIONS edit): the minimum-regret autonomy boundary (reversible ⇒ autonomous; irreversible ⇒ human) is carried in the `release-loop` skill (`release-engineering`), this loop's share of the operating model — RFC-0048 § Amendments 2026-06-29.
- Follow-on candidate: an **SLO / error-budget-authoring capability** — supplies the
  SLI/SLO + error-budget-policy artifact the **AC6b release-readiness gate** consumes.
  It is the one net-new input the gate needs beyond checks the loop already runs.
  **Pack home is provisional** (a skill in `release-engineering`, vs. part of the
  operate/incident loop below, vs. its own pack) — that scope call is **deferred to the
  sibling RFC**, not decided here; AC6b consumes the artifact **by convention** and, until
  it exists, records an explicit `error-budget: not-defined` field for the human (never a
  silent pass). This is the first candidate of the broader SRE build-out — an
  **operate/incident loop** carrying the same minimum-regret carve generalized to
  remediation — which, because it re-opens the live-service scope this RFC makes a
  non-goal, is owed its **own sibling RFC**, not folded in here.
