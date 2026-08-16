# Enterprise rollout playbook tabletop scenarios

## Scope boundary

These cold tabletop checks used only the authored rollout playbook source. They exercised track selection, role handoffs, stage preparation, the pilot contract, the rollout checklist, the stage decision record, the retrospective, the mid-market refusal, and the completion receipt.

No live rollout, credential use, repository write, external-system mutation, wave, or organization-wide deployment occurred. Each scenario stopped at its recorded pilot verdict. Later stages and technical distribution were reviewed as documented branches, not exercised behavior.

## Technical track — advance one measured wave

- **Chosen track and stage:** Technical, pilot.
- **First task:** A technical PM asks the agent to turn a known dependency-upgrade problem into a bounded spec and plan. The PM can verify the scope and acceptance criteria in minutes because the affected workflow is already theirs.
- **Human controls:** The PM approves the input and judges the brief/spec quality. The platform owner confirms the isolated repository boundary and recovery route. The executive sponsor alone decides whether to widen.
- **Evidence:** The draft spec/plan names assumptions, acceptance criteria, tests, and unresolved risks; a second engineer confirms it is implementable without a sync meeting. Baseline and elapsed time are recorded, recovery is checked, and no checklist item remains open.
- **Recipient:** The engineer who would implement or review the spec.
- **Unresolved risk:** The pilot does not prove support capacity across several teams.
- **Artifact and mutation status:** Exact draft spec/plan paths recorded; repository writes limited to those approved files; `External mutation: none`.
- **Final verdict:** `advance` to one timeboxed wave in the same technical track, conditional on declared champion coverage and support capacity.

The record does not claim organization-wide readiness. The wave must reproduce first value with each team using its own known problem.

## Enterprise track — hold before external support exits

- **Chosen track and stage:** Enterprise, pilot.
- **First task:** An enterprise AI champion and client practitioner run one existing incident-review workflow from the operating guide. The practitioner knows the source incident and can verify the resulting review artifact.
- **Human controls:** The practitioner judges domain correctness. The platform owner approves access and safeguards. The champion records the outcome and support burden. The sponsor owns widening, and the external specialist cannot accept the handoff on the client's behalf.
- **Evidence:** The artifact is useful and the recipient accepts it, but the client has not yet completed an independently executed recovery run. The support path still depends on the external specialist.
- **Recipient:** The named internal service owner and executive sponsor.
- **Unresolved risk:** Handoff completeness and independent operation after external support exits are unproven.
- **Artifact and mutation status:** Exact review-artifact path and status recorded; the exercise used sanitized inputs; `External mutation: none`.
- **Final verdict:** `hold` at pilot scope until the client-owned run exercises both the documented support route and recovery path without the external specialist leading it.

The positive artifact result cannot override missing exit evidence. The guide leads to `hold` without consulting the spec.

## Non-technical track — revise the pilot

- **Chosen track and stage:** Non-technical, pilot.
- **First task:** A same-role UX peer champion helps a designer synthesize a sanitized set of interview notes into a familiar journey-map draft. The participant recognizes the sources and owns the quality bar.
- **Human controls:** The designer approves source use, checks provenance, edits the journey, and decides whether it is fit to share. The platform owner confirms the read/write boundary. The sponsor decides only whether the pilot may repeat or widen.
- **Evidence:** Provenance is complete and the recipient can inspect the draft, but the designer records that two sections feel generic and do not preserve the research's craft distinctions.
- **Recipient:** The design-review facilitator.
- **Unresolved risk:** Craft integrity is not yet strong enough for a shareable final artifact; the next prompt and review rubric need participant-led changes.
- **Artifact and mutation status:** Chat-only draft, explicitly recorded as unapproved; no repository writes; `External mutation: none`.
- **Final verdict:** `revise` the current pilot with the designer's named changes, then repeat the same bounded task. Do not advance to a wave.

The scenario preserves participant voice instead of recasting criticism as adoption success. The next run stays identity-safe: assistance removes collation work while the designer retains strategic authorship.
