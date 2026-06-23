# Plan: infra-aware-work-loop

- **Spec:** [`spec.md`](spec.md)
- **Status:** Drafting <!-- Drafting | Executing | Done -->

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document is allowed to change as you learn. When it changes substantially
> (a different approach, not just a re-ordering), note why in the changelog
> at the bottom.

## Approach

The change is **prose in one file** — `packs/core/.apm/skills/work-loop/SKILL.md`
— plus a version bump and a changelog line. The shape is four self-contained
prose edits, each at a distinct, already-existing anchor in the skill, so they
don't entangle:

- **P1** edits the PLAN *"Pick the verification mode for each plan task"* step —
  adds the mechanism-must-exist obligation (universal, light + full) and the
  infra multi-artifact task-zero set.
- **P2** edits the same PLAN verification-mode list — adds the fourth
  **infra/deploy** flavor with its five-layer GATES sequence, cross-linked to the
  plan template's `## Rollout`.
- **P4** edits the EXECUTE step — the agent-drives-verification doctrine and the
  Claude Code accelerant primitives, sitting beside P2's smoke layer.
- **P5** edits the REVIEW *Specialist reviewers* step and the PLAN *pre-EXECUTE
  secure-design review* step — makes `security-reviewer` non-skippable for
  infra-flavored work and force-loads the infra-relevant `security-checklists`
  modules, and states the reviewer-vs-scanner pairing.

The riskiest part is **not the edits but the discipline**: keeping every
sentence tool-neutral (Principle 1) and resisting the standing temptation to
"just add a small plan-parser" (Decision 1). Verification is goal-based +
judgmental: `make build-self` and the three lint surfaces prove projection and
hygiene; the spec-mode + diff-mode adversarial pass (plus a spec-stage
security-reviewer read, since the subject is a security boundary) proves the
doctrine actually routes as written. No production test file — there is no
compressible invariant to TDD.

## Constraints

- **ADR-0031** — doctrine + reference library only, no executable infra tooling;
  operational safety → `quality-engineer`; security on infra → mandatory
  `security-reviewer` + scanner pair. This plan must not contradict it.
- **RFC-0041** (Accepted) — P1/P2/P4/P5 as specified; no new risk trigger; no new
  reviewer; progressive delivery deferred.
- **ADR-0014 / RFC-0025** — the destructive/irreversible trigger that routes
  `apply` to full mode is unchanged; P2/P5 fire *because of* it, not via a new
  trigger.
- **ADR-0018** — the orchestrator-inlined progressive-disclosure mechanism P5
  reuses; P5 changes posture (discretionary → mandatory), not mechanism.
- **`work-loop-light-mode` spec** — the projection mechanics and the
  three-lint-surface gate for a core SKILL.md prose change are established there;
  reuse them.

## Construction tests

Per-task checks live under each task's `Tests:` subsection (all goal-based or
judgmental — no production test file). Cross-cutting:

**Integration tests:** none beyond per-task checks (single-file prose change).
**Manual verification:** after `make build-self`, read the projected
`.claude/skills/work-loop/SKILL.md` and confirm the four edits read coherently
in place and the infra/deploy flavor's cross-link to `## Rollout` resolves.

## Design (LLD)

n/a — methodology/prose change to one SKILL.md. No application LLD; the
"design" is the doctrine itself, fully specified by the spec's Acceptance
Criteria. The stack-neutral category headings do not apply to a prose edit.

## Tasks

### T1: P1 generalized verification-mechanism preflight (universal) + infra multi-artifact set

**Depends on:** none

**Tests:**
- `grep` the source SKILL.md PLAN verification-mode step for the
  mechanism-must-exist obligation, the "task zero" framing, the "agnostic"
  qualifier, and an explicit "universal across light and full mode" statement
  (spec AC: P1 generalized preflight).
- `grep` for the infra multi-artifact enumeration — verify-status, teardown,
  test-data/mock-user seeding, policy-as-code/CSPM scanner — each as a task-zero,
  with the scanner named as per-provider-depth source feeding P2 and P5, and the
  requirement stated as mechanism-level not tool-level (spec AC: P1 infra set).

**Approach:**
- Edit the PLAN *"Pick the verification mode for each plan task"* step in
  `packs/core/.apm/skills/work-loop/SKILL.md`: add the preflight obligation, kept
  to roughly one sentence for the universal core, then a short infra paragraph
  enumerating the multi-artifact set as task-zeros.
- Keep all of it tool-neutral; ground it in walking-skeleton / tracer-bullet /
  CD pipeline-first language (RFC-0041 research F4.1–4.2), not a specific tool.

**Done when:** both greps match in the source; the universal-mode statement is
present; no executable artifact is introduced (the loop *offers to scaffold*, it
does not ship the scripts).

### T2: P2 infra/deploy verification flavor (five-layer GATES) + Rollout cross-link

**Depends on:** T1 (the infra flavor's static-preflight layer references the P1
scanner task-zero introduced in T1)

**Tests:**
- `grep` for the fourth flavor name **infra/deploy** and all five layers (static
  preflight, plan/preview, idempotent convergent apply *named as precondition*,
  active end-to-end smoke, rollback) with the smoke layer's multi-hop probe
  spelled out (seed users → load real URL → assert render → read logs → debug →
  teardown) (spec AC: P2 verification flavor).
- Confirm the flavor cross-links to the plan template's `## Rollout` section and
  does not restate deployment sequencing (spec AC: P2 cross-link).

**Approach:**
- Add the infra/deploy flavor to the PLAN verification-mode list, after
  visual-manual-QA, framing smoke as an extension of the existing "exercise the
  real built artifact" doctrine.
- Name idempotent convergent apply as the precondition that makes iteration safe
  (research F1.2); name the known-good re-apply rollback path (F2.6).
- Cross-link, don't duplicate, `## Rollout`.

**Done when:** the grep matches all five layers; the cross-link resolves; every
example is labelled illustrative and no sentence binds to one IaC tool.

### T3: P4 agent-drives-verification doctrine + Claude Code accelerant

**Depends on:** none

**Tests:**
- `grep` the EXECUTE step for the agent-runs-deploy-and-reads-real-output
  doctrine, the **human-as-relay** anti-pattern by name, and the three Claude
  Code primitives (background tasks, `asyncRewake`, `PreToolUse`) framed as
  accelerant-not-dependency (spec AC: P4).

**Approach:**
- Edit the EXECUTE step (beside the visual/manual-QA discipline) to state the
  doctrine harness-agnostically, matching how `/verify` / `/simplify` are treated
  as optional accelerants.

**Done when:** the grep matches; the primitives are explicitly "accelerant,
never a dependency"; adapters without them are stated to lose only the shortcut.

### T4: P5 mandatory infra security — non-skippable reviewer + scanner pair

**Depends on:** T1 (the scanner half of the pair is the P1 task-zero scanner), T2
(infra-flavored work is what triggers the mandatory pass)

**Tests:**
- `grep` the REVIEW *Specialist reviewers* step and the PLAN *pre-EXECUTE
  secure-design review* step for the non-skippable framing, "spec stage **and**
  diff", and the force-load of the five infra `security-checklists` modules
  loaded 1–N per the existing routing table (spec AC: P5 mandatory).
- `grep` for the reviewer-is-not-per-provider-depth / scanner-holds-baselines /
  "pair" prose (spec AC: P5 pair).
- Confirm no new reviewer and no new `security-checklists` module is added
  (`git diff` shows only prose edits to existing anchors).

**Approach:**
- In the PLAN pre-EXECUTE security step and the REVIEW specialist-reviewers step,
  state that an infra/deploy-flavored task makes the `security-reviewer` pass
  mandatory at both stages and force-loads the named modules.
- State the pairing: reviewer = failure-class reasoning from standards; scanner =
  per-provider depth (its rulesets are the baselines).

**Done when:** both greps match; `git diff` confirms only existing-anchor prose
changed; the Profile-A opt-out and the no-matching-subagent fallback note remain
intact.

### T5: build-self, lint surfaces, version bump, changelog

**Depends on:** T1-T4

**Tests:**
- `make build-self` exits 0 and regenerates `.claude/skills/work-loop/SKILL.md`
  with no unexpected reverts elsewhere (`git status` review).
- `make build-check`, `python tools/lint-agent-artifacts.py`, and `python
  tools/lint-agents-md.py` all exit 0 (spec AC: projection + lint).
- `git diff` shows `loop-cohort.py` and `lint-spec-status.py` byte-unchanged
  (spec AC: no executable mechanism).
- `packs/core/pack.toml` version bumped; projected `marketplace.json` reflects
  it; `docs/product/changelog.md` `[Unreleased]` carries the entry (spec AC:
  release hygiene).

**Approach:**
- Run `make build-self`; verify the projection. Bump `core` version. Add the
  changelog `[Unreleased]` entry naming the infra-aware work-loop behavior.
- Run the three lint surfaces by hand (the latter two are not in build-check).

**Done when:** all gates green; version + changelog updated; projection clean.

## Rollout

- **Delivery:** big-bang prose change, fully reversible (revert the SKILL.md
  edits + version bump). Nothing irreversible — no data, no published interface
  beyond the projected skill text.
- **Infrastructure:** none.
- **External-system integration:** none. (The *subject* is infra deploys, but the
  *change* is doctrine prose; it provisions nothing.)
- **Deployment sequencing:** this spec and `operational-safety-checklists` both
  edit `work-loop` SKILL.md — land this one first (or both in one PR) so the
  `operational-safety` routing table (the other spec) is added against the
  infra-flavor prose this spec introduces.

## Risks

- **Co-edit collision with `operational-safety-checklists`.** Both specs edit
  `work-loop` SKILL.md, but at **different bullets of the REVIEW "Specialist
  reviewers" step**: this spec's P5 (T4) edits the **`security-reviewer`** bullet
  (plus the PLAN pre-EXECUTE secure-design step and the verification-mode step);
  the sibling adds its routing table at the **`quality-engineer`** bullet. The
  `quality-engineer` bullet is touched by exactly one spec (the sibling), the
  `security-reviewer` bullet by exactly one (this one). Mitigation: sequence (this
  spec first) or single PR; the conflict is small and mechanical.
- **Scope inflation back into tooling.** The standing temptation to add a
  "small plan-parser" or cost-gate. Mitigation: Boundaries' *Never do* and
  ADR-0031 make executable infra an explicit out-of-bounds; the adversarial pass
  checks for it.
- **Tool-specific drift.** A sentence quietly assuming Terraform. Mitigation:
  examples labelled illustrative; adversarial pass checks for stack-binding.
- **P1 becomes box-ticking** ("mechanism exists: yes"). Mitigation: the
  obligation is "name the mechanism or write task zero to build it" — a concrete
  artifact, not a checkbox; the spec AC requires the multi-artifact enumeration.

## Changelog

- 2026-06-23: initial plan (follow-on to Accepted RFC-0041; authored alongside
  ADR-0031 and the `operational-safety-checklists` spec in a docs-only PR;
  implementation is a separate later PR).
