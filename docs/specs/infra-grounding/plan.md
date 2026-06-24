# Plan: infra-grounding

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done <!-- Drafting | Executing | Done -->

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document is allowed to change as you learn. When it changes substantially
> (a different approach, not just a re-ordering), note why in the changelog
> at the bottom.

## Approach

A prose change to the `core` pack, delivered **source-first** then `make build-self`. It lands four kinds of artifact: one new protocol-shaped skill (`infra-contract-acquisition`), one new `operational-safety` module (`cloud-implementation-craft`), edits to an existing module (`observability-and-smoke`), and edits to `work-loop` SKILL.md. The riskiest part is **keeping the protocol tool-neutral while its `references/` oracle table is concrete**, and **wiring `cloud-implementation-craft` as an EXECUTE consumer** without disturbing the existing REVIEW-consumer wiring of `operational-safety`.

Order of operations: author the new skill (A1: protocol body + oracle table) first because everything downstream references it; add its EXECUTE contract-grounding gate to `work-loop`; add the craft module (A2) and its EXECUTE-brief wiring; then the `work-loop` / module prose for P, V1, V2, and D; then the `quality-engineer` Delivery wiring; finally release hygiene (build-self, version bump, marketplace manifest, changelog) as the closing task. Each family is sized to a coherent commit; T1–T9 can land in one implementing PR or a short stack.

Verification is goal-based (grep / git-diff for content presence, the three lint surfaces, build-self drift gate) plus judgmental review (spec-mode + diff-mode `adversarial-reviewer`; a `security-reviewer` spec-stage read for the four-way carve; a `quality-engineer` read for the `operational-safety` EXECUTE-consumer wiring) plus a manual-QA exercise of the new skill — no TDD, since the change carries no compressible invariant. The implementing PR runs the full-mode `loop-cohort` state machine; **this authoring PR does not** (see the spec's Process assumptions).

## Constraints

- **ADR-0034** — the load-bearing calls: doctrine + references, one new protocol-shaped skill, tool-keyed generality, craft at EXECUTE, no executable tooling / per-vendor data / new agent.
- **RFC-0044** — the six MECE families (A1, A2, P, V1, V2, D) and Delivery; the protocol body + oracle table content shape; the evidence base.
- **ADR-0031 + RFC-0041** — the scaffold extended: P1 multi-artifact preflight (a fifth artifact added), P2 smoke (refined by V1/V2), `observability-and-smoke` (strengthened by D), the no-new-reviewer ceiling honored.
- **ADR-0023** — three-reviewer ceiling (forecloses a dedicated infra-contract reviewer now).
- **ADR-0018 + RFC-0029** — the orchestrator-loaded progressive-disclosure depth-library mechanism reused by the new skill and module.
- **RFC-0025 + ADR-0014** — risk triggers already route infra to full mode; **no new trigger** added.

## Construction tests

Most tests are per-task below. Cross-cutting:

**Integration tests:** none beyond per-task (prose change; no executable logic).
**Manual verification:**
- `make build-self` runs clean; `git status` shows only the intended source + projected paths changed.
- The three lint surfaces (`make build-check`, `tools/lint-agent-artifacts.py`, `tools/lint-agents-md.py`) all exit 0.
- `git diff --exit-code` on `packs/core/.apm/skills/work-loop/scripts/loop-cohort.py` and `.../lint-spec-status.py` is empty (the byte-unchanged guard).
- The new skill is exercised as a user/agent-invoked artifact: its `description:` triggers on an infra-authoring prompt and the protocol body + oracle table read end-to-end as a runnable procedure (record the observation).

## Design (LLD)

n/a — methodology / prose change across the `core` pack (one new skill, one new + one edited `operational-safety` module, `work-loop` SKILL.md edits); there is no application low-level design. The "design" is the doctrine itself, captured in the spec's Acceptance Criteria. Rollout is a pure-prose ship (below).

## Tasks

### T1: `infra-contract-acquisition` skill — protocol body + per-tool oracle table (A1)

**Depends on:** none

**Tests:**
- Goal-based: `packs/core/.apm/skills/infra-contract-acquisition/SKILL.md` exists with valid frontmatter (`name`, `description`) and `lint-packs` accepts it; a `references/` oracle table file exists. Verifies AC "A1 — skill exists" and "A1 — protocol-shaped".
- Goal-based (grep): the protocol body names T0→T1→T2→T3→Final and the schema-heterogeneity note (CFN `createOnlyProperties` / Pulumi `replaceOnChanges` from schema; Terraform force-new from `plan`+docs). Verifies "A1 — protocol-shaped".
- Goal-based (grep): the spectrum (strong / medium / weak) + "declare tier + confidence" + the weak-oracle runtime-probe fallback are present. Verifies "A1 — oracle-tier honesty".
- Manual-QA: the `description:` triggers on infra-authoring prompts; the protocol reads as a runnable acquisition procedure.

**Approach:**
- Create the skill dir + `SKILL.md` (protocol-shaped, tool-keyed prose) + `references/oracle-table.md` (per-tool concrete commands, labelled the reference instance).
- State the four-way carve in the front matter (paired with T3).
- Keep every normative sentence tool-neutral; concrete commands live only in the references table.

**Done when:** `lint-packs` accepts the skill; the grep checks above pass; the manual-QA observation is recorded.

### T2: EXECUTE contract-grounding gate in `work-loop` (A1)

**Depends on:** T1

**Tests:**
- Goal-based (grep): `work-loop` SKILL.md EXECUTE prose states "acquire the contract before generating a CLI invocation, an IaC resource, **or application code that runs on a managed runtime** (e.g. a handler whose packaging / import model the platform dictates), against an unfamiliar platform; never guess a flag / schema shape / field constraint / packaging assumption", named as the infra generalization of AGENTS.md's "grep to verify a function exists." Verifies AC "A1 — EXECUTE contract-grounding gate" (incl. RFC-0044 § Errata 2026-06-24).

**Approach:** add the gate to the EXECUTE section, cross-referencing the `infra-contract-acquisition` skill; keep it universal where RFC-0044 states (the grounding gate is the infra analog of the verification-mechanism preflight obligation).

**Done when:** the grep check passes; build-self clean.

### T3: `cloud-implementation-craft` module + EXECUTE-consumer wiring (A2)

**Depends on:** T1

**Tests:**
- Goal-based: `packs/core/.apm/skills/operational-safety/references/cloud-implementation-craft.md` exists with the module shape (Loaded-when / Grounded-in blockquote + checks). Verifies AC "A2 — module".
- Goal-based (grep): the seven craft areas are present (sufficient-permissions-in-one-pass; eventual-consistency / propagation waits; timeout / cold-start / client-tolerance / backoff; dependency ordering; terminal-failed-state; deployment-artifact packaging & entrypoint / module-resolution model — platform specifics deferred to T2; externalized script configuration — resource prefixes / region / account / tags / naming tokens from external config, never hardcoded, illustrative mechanisms only). Verifies "A2 — module" (incl. RFC-0044 § Errata 2026-06-24). Build-1 evidence: the flat-package-root / relative-import `ModuleNotFoundError` failure is exactly the packaging area.
- Goal-based (grep): `work-loop` SKILL.md states the orchestrator inlines this module into the **implementer's EXECUTE brief** on infra-flavored work, via the `operational-safety` routing table; the routing table gains the `cloud-implementation-craft` row. Verifies "A2 — loaded at EXECUTE".
- Goal-based (grep): the module front matter states the four-way carve. Verifies "A2 — carve".

**Approach:**
- Author the module mirroring the existing `operational-safety` reference shape.
- Add the EXECUTE-consumer prose to `work-loop` (a deliberate extension: `operational-safety` consumed at EXECUTE, not only REVIEW) and the routing-table row.
- State the carve in front matter.

**Done when:** the greps pass; `lint-packs` accepts the module; build-self clean.

### T4: P — fifth preflight artifact, terminal-failed-state, reusable-script corollary

**Depends on:** T2

**Tests:**
- Goal-based (grep): `work-loop`'s infra multi-artifact preflight lists a **fifth artifact — a durable credential session** (establish-once / single identity check / reuse / profile-vs-static precedence) alongside the four RFC-0041 artifacts. Verifies AC "P — fifth preflight artifact".
- Goal-based (grep): `operational-safety/references/state-and-idempotency.md` names terminal-failed-state (`ROLLBACK_COMPLETE` → destroy-recreate) as a convergence case. Verifies "P — terminal-failed-state".
- Goal-based (grep): `work-loop` states every live-environment interaction (deploy / probe / log pull / debug) goes through a reusable, idempotent, credential-reusing script, framed as sharpening RFC-0041 P4. Verifies "P — reusable-script corollary".
- Goal-based (grep): the corollary states the scripts are **externally parameterized** (resource name prefixes / region / account / tags / naming tokens from external config — tfvars / `TF_VAR_*` / env / CDK context, never hardcoded — illustrative only, Principle 1), enabling org naming conventions + like-for-like environments. Verifies the externalized-script-config half of "P — reusable-script corollary" (RFC-0044 § Errata 2026-06-24).

**Approach:** edit the `work-loop` infra preflight prose; edit `state-and-idempotency.md`; add the reusable-script corollary near P4.

**Done when:** the greps pass; build-self clean.

### T5: V1 — phased oracle fidelity (`work-loop`)

**Depends on:** T2

**Tests:**
- Goal-based (grep): `work-loop` infra PLAN / EXECUTE prose states oracles are phased and increasing-fidelity (static < plan/preview < runtime deploy+smoke), cheap-early oracle necessary-not-sufficient ("synth passed" ≠ done), and states the A1 / V1 carve (A1 = ground authoring; V1 = don't mistake a green early oracle for "works"). Verifies AC "V1 — phased oracle fidelity".

**Approach:** add the phased-fidelity prose and the explicit A1/V1 carve sentence.

**Done when:** the grep passes; build-self clean.

### T6: V2 — readiness-aware data-plane probe refining P2 (`work-loop`)

**Depends on:** T2

**Tests:**
- Goal-based (grep): `work-loop`'s infra smoke (RFC-0041 P2) names in-network-if-private, data-plane round-trip (write→read-back / drive to terminal user-visible result), readiness-aware poll-with-bounded-backoff (not-ready ≠ broken), and self-teardown against an ephemeral uniquely-named target (`defer destroy` / `dev-test-run-uuid`); cross-links P2 + `## Rollout`, does not duplicate the GATES sequence. Verifies AC "V2 — readiness-aware data-plane probe".

**Approach:** refine the P2 smoke-layer prose; cross-link Rollout (never duplicate sequencing); fold the probe into the teardown artifact.

**Done when:** the grep passes; build-self clean.

### T7: D — symptom→layer log playbook in `observability-and-smoke`

**Depends on:** none

**Tests:**
- Goal-based (grep): `observability-and-smoke.md` gains the localization method — enumerate log groups; symptom→emitting-layer map (504→proxy/facade; 403→authorizer/IAM; 500→handler); chain bisection; correlation id; failure-signature→likely-cause catalog matched first. Verifies AC "D — symptom→layer log playbook". (No new module file is created.)

**Approach:** strengthen the existing module; confirm no new module is added (the AC's no-new-module clause).

**Done when:** the grep passes; `git status` shows no new `operational-safety/references/*.md` beyond `cloud-implementation-craft.md`; build-self clean.

### T8: Delivery — `quality-engineer` infra-flavored wiring (`work-loop`)

**Depends on:** T1, T3

**Tests:**
- Goal-based (grep): `work-loop`'s REVIEW `quality-engineer` step loads `infra-contract-acquisition` + `cloud-implementation-craft` on infra-flavored work and re-derives the contract **independently** from the oracles (not from the implementer's evidence); names `design-reviewer` as the spec-stage home for the auth-flow-contradiction class; names the dedicated `infra-contract-reviewer` as deferred behind the RFC-0044 Decision 8 evidence trigger. Verifies AC "Delivery — `quality-engineer` wiring, no new agent".
- Goal-based: no new agent file under `packs/core/.apm/agents/`. Verifies the no-new-agent clause.

**Approach:** edit the `quality-engineer` REVIEW bullet + the `operational-safety` routing-table prose; add the independent-re-derivation sentence and the deferral note.

**Done when:** the grep passes; no new agent file; build-self clean.

### T9: Release hygiene — build-self, version bump, marketplace manifest, changelog

**Depends on:** T1-T8

**Tests:**
- Goal-based: `make build-self` regenerates the new skill + modules + `work-loop` projections cleanly (drift gate clean).
- Goal-based: `make build-check`, `tools/lint-agent-artifacts.py`, `tools/lint-agents-md.py` all exit 0.
- Goal-based: `git diff --exit-code` on `loop-cohort.py` and `lint-spec-status.py` is empty. Verifies AC "No executable mechanism".
- Goal-based: `packs/core/pack.toml` + `packs/core/.claude-plugin/plugin.json` versions bumped; `marketplace.json` reflects it after build-self and lists `infra-contract-acquisition`; `docs/product/changelog.md` has an `[Unreleased]` entry. Verifies AC "Projection + lint" and "Release hygiene".

**Approach:** bump `core` version in both files by hand, run `make build-self` (aggregates `marketplace.json`), add the changelog entry, run all three lint surfaces, confirm the byte-unchanged guard.

**Done when:** all gates green; the byte-unchanged guard holds; the manifest lists the new skill.

## Rollout

- **Delivery:** big-bang prose ship in the `core` pack; reversible by reverting the PR. No data migration, no published event, nothing irreversible.
- **Infrastructure:** none — the change is agent-instruction prose; the loop *offers to scaffold* the P1 task-zero artifacts but ships none.
- **External-system integration:** none.
- **Deployment sequencing:** none beyond the within-PR task order (T1 before its consumers; T9 last). The new skill must be present before `work-loop` references it, which the task order guarantees.

## Risks

- **Tool-neutrality drift** — the per-tool oracle table tempts vendor-binding in the normative prose. Mitigation: table is labelled the reference instance; an adversarial pass checks for vendor-binding; the weak-oracle row + tier-honesty are mandatory ACs.
- **EXECUTE-brief bloat** — loading `cloud-implementation-craft` at EXECUTE grows the implementer's context. Mitigation: loads only on infra-flavored work, via the existing 1–N routing table, never a flat march.
- **`quality-engineer` window bloat** from oracle output + a second module. Mitigation: contract fetched in slices; the dedicated-agent escape hatch (Decision 8) is pre-named with its evidence trigger.
- **Box-ticking** ("contract acquired: yes"). Mitigation: A1's output is a cited contract slice the build references; A2 is reviewed against deployed reality; `quality-engineer` re-derives independently.
- **Family inconsistency** — the new skill is protocol-shaped where the libraries are checklist-shaped. Accepted and recorded in ADR-0034; not a blocker.

## Changelog

- 2026-06-24: initial plan — authored alongside ADR-0034 as the RFC-0044 governance-docs follow-on; nine tasks across the six MECE families + Delivery + release hygiene; implementation deferred to a separate PR per the house two-PR pattern.
- 2026-06-24 (implementation): **progressive-disclosure restructure.** `work-loop/SKILL.md`'s body was already at 990/1000 lines (the skill-spec hard cap), so the spec's seven doctrine additions could not land inline. Per the maintainer's direction ("it should be progressive disclosure for sure … consider if other mode-specific work-loop instructions should be progressive disclosure"), the full **infra/deploy verification-mode doctrine** — the layered GATES sequence detail, the multi-artifact preflight (incl. the new durable-credential artifact), the EXECUTE contract-grounding gate + craft load + reusable-script corollary, V1 phased fidelity, the V2 data-plane probe, the mandatory-infra security pass, and the `quality-engineer` independent re-derivation — was consolidated into a **new `packs/core/.apm/skills/work-loop/references/infra-verification.md`** (the 5th work-loop reference, loaded on infra-flavored work, the same on-demand mechanism as the existing four). `SKILL.md` keeps the **load-bearing one-liners** (the mode entry in the PLAN list, the EXECUTE contract-grounding gate, a lean security-infra stub) and the **cross-referenced routing tables** (load-bearing reviewer-dispatch mechanism, anchors intact); each carries a pointer to the reference. Net effect: SKILL.md is **979 body lines (983 incl. frontmatter) — 11 below the 990-line pre-PR body baseline** — despite the new doctrine. **Verification impact:** the per-task goal-based greps (T2/T4/T5/T6/T8) now target `SKILL.md` **and/or** `references/infra-verification.md` (still "work-loop … states", satisfying the frozen spec, which does not pin SKILL.md vs. references). This also relocated existing `infra-aware-work-loop` P2/P4/P5 prose into the reference — a deliberate progressive-disclosure relocation (the doctrine still ships and still loads on infra work), not a deletion.
