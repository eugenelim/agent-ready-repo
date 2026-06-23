# Spec: infra-aware-work-loop

- **Status:** Draft <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** ADR-0031, RFC-0041 (P1, P2, P4, P5); ADR-0014 + RFC-0025 (the destructive/irreversible risk trigger that routes `apply` to full mode); ADR-0018 (orchestrator-inlined progressive-disclosure security depth, the mechanism P5 reuses); ADR-0017 (the SAST/SCA scanner family the policy-as-code/CSPM scanner joins)
- **Brief:** none
- **Contract:** none
- **Shape:** n/a — methodology/prose change (`work-loop` SKILL.md edits); no application LLD

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

Agents and adopters running the `core` pack get a `work-loop` that can drive an
**infrastructure inner loop end-to-end** instead of stalling the moment a deploy
is involved. Today the loop's verification modes (TDD / goal-based /
visual-manual-QA) silently assume the verification mechanism already exists and
assume a fast, local, stateless, single-hop gate; a cloud deploy is slow,
stateful, partially irreversible, multi-hop, and its mechanism (idempotent
apply, a smoke check, a throwaway target, teardown) frequently *doesn't exist
yet* — so the agent can't drive the loop and the human becomes a relay,
copy-pasting deploy errors back into the session. Success is: (P1) picking any
verification mode obligates confirming its mechanism exists — and if not,
building it is task zero — stated universally across light and full mode; (P2) a
fourth **infra/deploy** verification flavor gives infra work a layered GATES
sequence that matches its stateful, multi-hop, partially-irreversible reality;
(P4) the agent drives the deploy and reads real environment output itself, with
the human-as-relay named as the anti-pattern; and (P5) infra-flavored work
**non-skippably** runs `security-reviewer` (spec stage + diff) paired with the
P1-required policy-as-code/CSPM scanner. The change is delivered by editing the
`core` pack's `work-loop` SKILL.md source (a projected artifact), adds **no
executable code, skill, or artifact type**, and ships to every core-pack
adopter.

## Boundaries

The three-tier guard that keeps an implementing agent inside the lines.
*Always do* applies without asking; *Ask first* requires human sign-off
before proceeding; *Never do* is a hard rule, even under time pressure.

### Always do

- Edit the **source** `packs/core/.apm/skills/work-loop/SKILL.md`, then run
  `make build-self` to regenerate the projected copy (`.claude/skills/work-loop/SKILL.md`).
  Never edit the projection directly.
- Run **all** lint surfaces before declaring done: `make build-check` (includes
  `lint-packs`), `python tools/lint-agent-artifacts.py` (projection lint, not in
  build-check), and `python tools/lint-agents-md.py` (AGENTS.md hygiene) — the
  same three surfaces the `work-loop-light-mode` spec established for a core
  SKILL.md prose change.
- Keep P1 (the verification-mechanism preflight) **universal across both light
  and full mode** — it is one sentence and cheap; only the heavier P2 infra
  flavor and P5 mandatory-security wiring are full-mode-only (they fire on the
  destructive/irreversible trigger that already routes `apply` to full mode).
- Write **every** infra-flavor sentence tool-neutral — Terraform / Pulumi / CDK
  / CloudFormation / hand-rolled scripts alike. Illustrative examples are
  labelled as illustrative, never normative (Principle 1).
- Express the P1 infra mechanism as a **multi-artifact set, each its own
  task-zero**: a verify-status script, a teardown script, test-data / mock-user
  seeding, and a provider-appropriate policy-as-code/CSPM scanner — and name the
  scanner as the per-provider-depth source that feeds *both* P2's static
  preflight and P5's security depth.
- Cross-link P2's verification flavor to the plan template's existing
  `## Rollout` section (which owns *deployment sequencing*); the flavor owns
  *how we verify*. Cross-link, never duplicate.
- Bump the `core` pack version (`packs/core/pack.toml` + the projected
  `marketplace.json` via `make build-self`) and add a `docs/product/changelog.md`
  `[Unreleased]` entry for the behavior change.

### Ask first

- **Adding, dropping, or reordering any risk trigger.** RFC-0041 adds **no new
  trigger** (destructive/irreversible already routes `apply` to full mode);
  if implementation seems to need one, stop and surface it.
- **Introducing any executable code, script, or hook** as the feature mechanism
  — Decision 1 / ADR-0031 forbid it; surface before adding.
- Expanding scope to any skill other than `work-loop`, or editing
  `loop-cohort.py` / `lint-spec-status.py` (frozen byte-unchanged by this spec).

### Never do

- **Ship any executable infra tooling** — no deploy wrapper, plan-parser,
  cost-gate, or runtime. This spec ships doctrine + prose only (ADR-0031); the
  loop *offers to scaffold* the P1 task-zero artifacts but does not ship them.
- **Bind P2's infra-flavor prose to a specific IaC tool** (Principle 1).
- **Make the infra security pass skippable** — P5 is non-skippable, runs at both
  spec stage and on the diff, and force-loads more than one `security-checklists`
  module (Decision 6).
- Edit the projected copy (`.claude/skills/work-loop/SKILL.md`) directly —
  `make build-self` reverts it; the source is the fix point.

## Testing Strategy

This change is agent-instruction prose in one SKILL.md — no executable logic —
so verification is **goal-based** plus **judgmental review**, with no TDD
(nothing carries a compressible invariant). This mirrors the verification
strategy the `work-loop-light-mode` spec used for the same class of change.

- **Projection correctness** (source → projected path agree after build-self):
  goal-based — `make build-self` then the drift/projection gates are clean.
- **Lint conformance**: goal-based — `make build-check`,
  `tools/lint-agent-artifacts.py`, and `tools/lint-agents-md.py` all exit 0.
- **Content presence/absence** (P1 obligation present and marked universal; the
  infra/deploy flavor and its five layers present; P4 agent-drives doctrine
  present; P5 mandatory-security wiring present; *no* executable code added;
  `loop-cohort.py` / `lint-spec-status.py` byte-unchanged): goal-based —
  `grep` / `git diff` checks.
- **Doctrine correctness** (does the prose actually *obligate* the mechanism,
  *sequence* the layered GATES with idempotent apply as a precondition, and
  *force-load* the security modules at both stages?): judgmental — the spec-mode
  and diff-mode `adversarial-reviewer` pass, since prose has no mechanical test.
  Because the subject is a security boundary, a `security-reviewer` spec-stage
  read confirms P5's controls are specified as acceptance criteria at the right
  depth.

## Acceptance Criteria

- [ ] **P1 — generalized preflight.** The PLAN verification-mode step states that
  picking a verification mode requires confirming the mechanism for that mode
  exists; if it does not, creating it is **task zero** (a precondition task, not
  an afterthought), and the loop offers to scaffold it. The obligation is
  explicitly **agnostic** (it applies to a missing test runner or build command
  as much as a missing smoke check) and explicitly **universal across light and
  full mode**.
- [ ] **P1 — infra multi-artifact set.** For infra work the preflight enumerates
  the mechanism as a multi-artifact set, **each its own task-zero**: (a) a
  verify-status script, (b) a teardown script, (c) test-data / mock-user
  seeding, and (d) a provider-appropriate policy-as-code/CSPM scanner. The
  scanner is named as the **per-provider-depth source** and as feeding *both*
  P2's static preflight (operational misconfig) and P5's security depth
  (security misconfig). The requirement is **mechanism-level, not tool-level**
  (a scanner must exist; the adopter picks Checkov / tfsec / cloud-native CSPM).
- [ ] **P2 — infra/deploy verification flavor.** The PLAN verification-mode list
  gains a fourth flavor, **infra/deploy**, whose contract is a layered GATES
  sequence rather than a single check: (1) static preflight (validate/lint/
  policy-as-code via the P1 scanner); (2) plan/preview (dry-run diff reviewed
  before any mutation); (3) **idempotent convergent apply, named as a
  precondition** (re-running after a fix must converge, not collide — imperative
  non-idempotent scripts flagged as the retry-collision root cause); (4) **active
  end-to-end smoke** — a multi-hop probe, not a single status check (seed
  test/mock users → load the real CDN/website URL → assert it actually renders →
  on failure pull access/error logs and debug → tear down), stated as an
  extension of the existing visual-manual-QA "exercise the real built artifact"
  doctrine; (5) rollback (the known-good re-apply path named *before* the first
  apply, since no atomic rollback exists).
- [ ] **P2 — cross-link, no duplication.** The infra/deploy flavor cross-links to
  the plan template's `## Rollout` section (deployment sequencing) and does not
  duplicate it; the flavor names *how we verify*, Rollout owns *the sequencing*.
- [ ] **P4 — agent drives verification.** The loop states as harness-agnostic
  doctrine that the agent runs the deploy and reads the real environment output
  itself, and names the **human-as-relay** pattern (a human pasting deploy errors
  back) as the anti-pattern. Claude Code primitives — background tasks for long
  applies, `asyncRewake` to wake on a background deploy's exit with stderr
  surfaced, `PreToolUse` to gate destructive commands — are named as
  **accelerant only, never a dependency** (matching how `/verify` and
  `/simplify` are treated); adapters without them lose the shortcut, not the
  doctrine.
- [ ] **P5 — mandatory infra security.** Infra-flavored work **non-skippably**
  invokes `security-reviewer` at **both** the spec stage (secure-design pass: is
  the control specified as an acceptance criterion at the right depth?) and on
  the diff — not via the discretionary security-boundary trigger. **"Infra-flavored"
  is the defined signal, not an ad-hoc judgement** (ADR-0031): work the
  destructive/irreversible risk trigger routes to full mode *and* whose diff/spec
  matches the boundary→module routing table's IaC/deploy-config entry — so the
  mandatory pass keys on the existing classifier and cannot be silently skipped
  on an infra diff. The
  orchestrator **force-loads** the infra-relevant `security-checklists` modules
  (`config-misconfig`, `access-control`, `secrets-and-crypto`, `outbound-ssrf`,
  `supply-chain`), loaded 1–N as the diff warrants per the existing
  boundary→module routing table. This adds **no new reviewer and no new
  module** — it makes the *existing* security pass mandatory and multi-module.
- [ ] **P5 — reviewer + scanner pair.** The prose states that `security-reviewer`
  is **not** the per-provider depth source: it reasons from cross-cutting
  standards (OWASP / ASVS / CWE + STRIDE/LINDDUN) and catches failure *classes*,
  while per-provider secure-config depth comes from the P1-required policy-as-code/
  CSPM scanner (its rulesets *are* the provider baselines). Security on infra is
  a **pair**; neither substitutes for the other.
- [ ] **No executable mechanism.** The change adds no new skill directory, no new
  artifact/template format, and no executable code as the feature mechanism
  (ADR-0031 structural constraint). `loop-cohort.py` and `lint-spec-status.py`
  are byte-unchanged (empty `git diff` for both; the sibling
  `operational-safety-checklists` spec asserts the same guard — one `git diff`
  satisfies both in a combined PR).
- [ ] **Projection + lint.** `make build-self` regenerates the projected
  `work-loop` SKILL.md cleanly; `make build-check`, `python
  tools/lint-agent-artifacts.py`, and `python tools/lint-agents-md.py` all pass
  (the latter two are not in `make build-check`; run by hand / in CI).
- [ ] **Release hygiene.** `packs/core/pack.toml` version is bumped, the
  projected `marketplace.json` reflects it after `make build-self`, and
  `docs/product/changelog.md` carries an `[Unreleased]` entry for the work-loop
  behavior change.

## Assumptions

- Technical: the `work-loop` skill source is
  `packs/core/.apm/skills/work-loop/SKILL.md`; the `.claude/...` copy is
  projected by `build-self`, not edited (source: `ls
  packs/core/.apm/skills/work-loop/`; precedent: `work-loop-light-mode` spec).
- Technical: the boundary→module routing table P5 reuses already exists in
  `work-loop` SKILL.md and already routes "IaC / deploy config" →
  `config-misconfig`, and the orchestrator already inlines `security-checklists`
  modules into the `security-reviewer` brief — so P5 is a posture change
  (discretionary → mandatory, one module → multi-module), not new mechanism
  (source: RFC-0041 spike result; `security-checklists/SKILL.md` "How it loads").
- Technical: `make build-check` (= `lint-packs build`) does not run build-self,
  the projection lint, or the AGENTS hygiene lint; those run by hand / in CI
  (source: `work-loop-light-mode` spec Assumptions; `Makefile`).
- Process: P4 (agent-drives-verification, RFC-0041 Decision 5) is a `work-loop`
  SKILL.md doctrine edit that co-locates with P2's smoke step, so it lands in
  *this* spec, not `operational-safety-checklists`. RFC-0041's follow-on-artifacts
  list originally named only P1/P2/P5 here; the **2026-06-23 P4-placement
  amendment** to RFC-0041 records P4 landing here explicitly, so the `Constrained
  by:` "(P1, P2, P4, P5)" above reconciles with the RFC rather than silently
  diverging (source: RFC-0041 Decision 5 + Amendments).
- Process: this spec and `operational-safety-checklists` **both edit `work-loop`
  SKILL.md, but at different bullets of the REVIEW "Specialist reviewers" step**
  — this spec's P5 edits the **`security-reviewer`** bullet (and the PLAN
  pre-EXECUTE secure-design step + the verification-mode step); the sibling adds
  its `operational-safety` routing table at the **`quality-engineer`** bullet.
  The `quality-engineer` bullet is touched by exactly one spec (the sibling); the
  `security-reviewer` bullet by exactly one (this spec). They land sequentially
  (this spec first) or in one PR; either way the conflict is small and mechanical
  (source: the two specs' scopes; `work-loop` SKILL.md "Specialist reviewers"
  section).
- Process: decision frozen in ADR-0031 (Accepted) + RFC-0041 (Accepted
  2026-06-22); the risk-trigger set is unchanged, so no CONVENTIONS/AGENTS
  risk-trigger edit is expected (confirm at implementation) (source:
  `docs/adr/0031-…`, `docs/rfc/0041-…`).
- Product: the infra-aware loop ships in `core` as the adopter-wide default,
  consistent with how `work-loop-light-mode` shipped (source: RFC-0041 scope;
  this is a follow-on of an Accepted RFC).
