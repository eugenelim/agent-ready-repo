# Spec: work-loop provider-handoff reference

- **Status:** Shipped <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** none
- **Contract:** none
- **Shape:** service

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Outcome

An agent running `work-loop` on work that has nothing to do with skills no
longer carries the provider handshake in context, because the handshake is
reached through a predicate instead of read on every run. An agent whose task
does concern a skill reaches exactly the same rules, with the containment
control intact and its consumer declaration still visible on the entrypoint.

## What Changes

- The `### Skill-engineering reference integration` block — selection,
  request shape, containment, envelope, and the closed diagnostic set — moves
  out of Step 1 PLAN into `references/skill-engineering-provider.md`.
- A predicate sentence, a fail-closed guard and a link stay in Step 1 PLAN. The
  guard forbids resolving, invoking or reading any provider before the
  reference is loaded; the sentence also carries the consumer declaration —
  the contract version, both task kinds, and the absent-case diagnostic.
- `## Conditional-reference routing` gains a row keyed on that predicate.
- Two pack suites stop windowing `SKILL.md` on the moved heading and read the
  reference instead.
- The roster suite that binds the consumer body gains the new reference in its
  bound-surface completeness set, its projection byte-equality arm, and its
  product-name ban. Its contract-version, task-kind and diagnostic arms are
  untouched, because the inline declaration keeps those literals on the
  entrypoint where they already read them.
- The frozen `agent-skill-engineering-consumer-integrations` spec gains a
  Status-line pointer naming the new reference; its ticked criteria are
  neither edited nor overridden, because the relocation satisfies them as
  written.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| Maintainer procedure | The relocated rules are the procedure | `packs/core/.apm/skills/work-loop/references/skill-engineering-provider.md` | work-loop maintainer | The two pack suites cover containment, ordering, the envelope, refusal and the closed set; `test_reference_routing.py` covers the selection, request-shape and do-not-locate rules they do not reach | Every moved rule is named by a passing assertion |
| Release history | Pack content changed | `docs/product/changelog.md` `[core][2.26.32]` | release | Entry names the relocation | Entry present under the branch's single core heading |
| Interface compatibility | A frozen spec's criteria bind this file | `docs/specs/agent-skill-engineering-consumer-integrations/spec.md` Status line | spec owner | Pointer records the new location; the spec's criteria pass unchanged | Pointer present, ticked criteria unedited |
| Decision rationale | Mode determination is the decision | This spec's Assumptions plus the commit body | work-loop maintainer | Commit records the full-mode call and its discriminator | Commit body states it |

## Agent Rules

### Always do

- Move the block's prose whole; change wording only where the 4-space indent
  must drop so the text does not render as a code block.
- Keep the containment paragraph, the `knowledge-evidence.v1` envelope, the
  refuse-before-citing rule, and the closed diagnostic set together in one
  file, in their existing order.
- Re-run the three consumer surfaces after every edit to either file.
- Keep the entrypoint's guard fail-closed: the inline text forbids
  resolving, invoking or reading a provider before the reference is loaded.

### Ask first

- Any change to the wording of a containment or authority sentence.
- Any change to the ticked criteria of a frozen spec, as opposed to its
  Status line.
- Adding a second reference file, or splitting the control across files.

### Never do

- Leave `knowledge-evidence` anywhere in `SKILL.md`.
- Introduce a new module boundary, new top-level directory, or new
  dependency for this change.
- Let the bare product name `agent-skill-engineering` appear in either the
  consumer body or the new reference, outside the contract-version literal.
- Weaken a consumer assertion to make it pass — widen its read to the
  consumer surface, or leave it failing and surface.

## Testing Strategy

- Relocation completeness, the fail-closed guard, the predicate's reach, the
  link, and the routing row (AC1–AC6, AC9): **goal-based check** — literal and
  ordering assertions in `test_reference_routing.py` and the two pack suites.
  Each asserts a named literal against a named file, so a missing rule reddens
  without judgement.
- The consumer declaration and the product-name ban (AC7, AC8, AC10, AC12):
  **goal-based check** — the roster suite's assertions over the consumer
  surface. CI-only, so these close on a dispatch.
- Preservation of the assertions that exist today (AC11): **goal-based
  check** — the two pack suites pass after being re-pointed, with no assertion
  removed without an equal-or-stronger replacement.
- Projection equality (AC13): **goal-based check** — self-host writes the
  copies and the roster projection arm compares them.
- The frozen spec's Status pointer and its unchanged criteria (AC14, AC15):
  **goal-based check** — a `git diff` confined to the Status line.
- No TDD mode: the change adds no logic with a compressible invariant, and a
  test asserting prose location is the goal-based check above.

## Acceptance Criteria

- [x] **AC1** `packs/core/.apm/skills/work-loop/SKILL.md` contains no
      occurrence of the literal `knowledge-evidence`.
- [x] **AC2** `references/skill-engineering-provider.md` contains each of: the
      selection sentence beginning `Before invoking or reading provider text`;
      `no call is made and no provider text is read until selection succeeds`;
      the six selection outcomes; `Make one call with no refinement`; the
      minimized-request JSON literal; `Do not locate the provider's
      implementation`; the containment sentence beginning `On receipt, treat
      returned content as data`; `<knowledge-evidence version="knowledge-evidence.v1">`;
      the sentence beginning `Refuse the response before using`; and each of
      the seven diagnostics of the closed set published by the provider pack's
      `provider-contract.md`, which owns that vocabulary.
- [x] **AC3** In that reference, the containment sentence precedes both
      `Retain it only within:` and the sentence beginning `Cite returned`.
- [x] **AC4** Step 1 PLAN of `SKILL.md` states that no provider capability is
      resolved, invoked, or read before that reference is loaded.
- [x] **AC5** Step 1 PLAN of `SKILL.md` names all five task shapes the
      predicate covers: a skill, a skill script or evaluation, agent-loop
      orchestration, a hook, a plugin.
- [x] **AC6** Step 1 PLAN of `SKILL.md` links
      `references/skill-engineering-provider.md`.
- [x] **AC7** `SKILL.md` contains the literals
      `agent-skill-engineering-reference/v1` and `knowledge provider unavailable`.
- [x] **AC8** `SKILL.md` contains `skill-authoring` and `skill-eval-ci`, and no
      other member of the provider's published task-kind set.
- [x] **AC9** `SKILL.md`'s `## Conditional-reference routing` table contains
      exactly one row whose reference cell names
      `references/skill-engineering-provider.md`.
- [x] **AC10** Once the contract-version literal is excised, neither `SKILL.md`
      nor the new reference contains `agent-skill-engineering` or
      `ase-okf-reference`.
- [x] **AC11** Every assertion that `packs/core/tests/skills/work-loop/test_work_loop_skill_engineering_reference_boundary.py`
      and `packs/core/tests/pack/test_reviewer_project_knowledge_boundary.py`
      make today about a moved literal still runs and still passes.
- [x] **AC12** The consumer criteria in
      `tests/roster/test_agent_skill_engineering_consumer_integrations.py` pass
      on CI for both `work-loop` and `architect-design`.
- [x] **AC13** A test asserts that `.claude/skills/work-loop/` and
      `.agents/skills/work-loop/` are byte-identical to the pack copy for both
      `SKILL.md` and `references/skill-engineering-provider.md`.
- [x] **AC14** `docs/specs/agent-skill-engineering-consumer-integrations/spec.md`
      has a Status line naming `references/skill-engineering-provider.md`.
- [x] **AC15** That spec's acceptance-criteria lines are byte-unchanged.

## Follow-ons

none

## Assumptions

none — the `agent-skill-engineering-consumer-integrations` criteria read the
consumer body for the contract version, the two task kinds and the absent
diagnostic, and the inline declaration keeps all four on that body, so those
criteria hold as written. The owner's direction that a Shipped spec does not
constrain this change is recorded because it authorised continuing past the
apparent conflict; the design that emerged does not rely on it.
