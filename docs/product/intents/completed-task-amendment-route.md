# A completed task's section has no amendment route

- **Slug:** `completed-task-amendment-route`
- **Status:** Draft
- **Level:** feature
- **Owner:** eugenelim

## Outcome

- **Steerable input:** A contract error that only doing the work could reveal is
  corrected in the contract, without the run losing its audit trail, when the
  correction falls inside a task already recorded complete.
- **Lagging outcome:** A correction discovered during execution lands in the
  contract, and the run keeps its audit trail — review rounds, retry counters,
  finding fingerprints and completed-task evidence — rather than trading one for
  the other.
- **Guardrail:** Completed work is not silently rewritten. Whatever route exists
  preserves owner authority, the reason reference, run identity and the
  approved-hash pins, and leaves an auditable record that a completed section was
  re-pinned and why. It does not weaken `validate_completed_task_sections` into
  accepting an unrecorded change, and it does not let an amendment reach back
  into work already shipped under the old contract.

## Boundary

- Includes the completed-task case only: an amendment whose correction falls inside a task already recorded complete, where `validate_completed_task_sections` refuses and no primitive re-pins the section.
- Excludes the pre-wave case, which `contract-amendment-pre-wave-window` already shipped in core 2.15.5 — the evidence binding is conditional on completed work existing, so an amendment before any task runs is reachable today.
- Excludes relaxing the guard itself as the answer. Its docstring — "Return a stable refusal when an amended plan rewrites completed work" — names a property worth keeping; the gap is the absence of a licensed route, not the presence of the refusal.
- Excludes `loop-cohort reset` as an acceptable route. It is the only escape today and it deletes `state.json`, which is why deliveries chose to carry a false contract instead of using it.
- Excludes progressive task locking and a settle-first lifecycle stage.

## Owner

- eugenelim, Platform Core maintainer.

## Unresolved questions

- Is the answer a re-pin primitive, a narrower amendment scope that cannot reach a completed section, or an ordering rule that forces the correction before completion is recorded? The third is the cheapest and may not be reachable: two deliveries found the error only by doing the work.
- RFC-0099 § 7 defines the post-seal correction route as legal from implementation, verification or review, and lists only preservation effects with no completed-work precondition. Does `validate_completed_task_sections` therefore already conflict with an accepted decision, as the pre-wave guard did? That is a conformance question and it is prior to designing anything.
- What is the real frequency? Four deliveries are recorded here, all between 2026-08-17 and 2026-09-17, and all authored by the same maintainer. The rate may be an artifact of one working style.

## Projection

- Shaping only. No RFC, brief or spec is selected, and the conformance question above is prior to choosing one.

## Opportunity

Four deliveries record the same wall, and each paid a different price for it. `work-loop-in-process-guards` states it as a design finding in its own words: "the tooling forbids exactly the mid-execution amendment the contract invites, and the only sanctioned escape is a destructive reset that clears the retry counters", and "a correction found during review — a wrong count, a stale citation — is the ordinary case, not an exceptional one". Eight amendments were queued for a human gate rather than applied; one correction was applied and then reverted "to restore hash currency"; and its T7 `Touches:` field still names a false two-file version-bump surface in four places of the shipped contract, with no amendment covering it. `agent-skill-engineering-corpus` hit a pin that was "unsatisfiable without writing a false count back into a completed section, and no re-pin primitive exists", and took a deliberate acceptance-criterion numbering gap because "renumbering it to AC17 would edit T3, a completed task section, which is the rule that already cost this change a cohort replay". `loop-telemetry-export` withdrew two corrections outright: T4's `Touches:` fix, because T4 was complete and frozen, and AC-0055, because "a criterion needs a task entry, and its only honest home is T2, which is frozen". AC-0055's identifier had reached pushed history, so it is now carried as retired having never been approved. `pr-gate-suite-disposition` hit the same refusal — `approve-plan` rejected the amended baseline with "completed task section changed". The guard is `validate_completed_task_sections` at `loop-cohort.py:612`. Its docstring states the property it enforces. Nothing in the repository states what to do when that property and a necessary correction conflict.


## Assumptions

- **Riskiest: that this is a property of the mechanism rather than of one
  author's working style.** All four recorded instances fall between 2026-08-17
  and 2026-09-17 and were authored by the same maintainer. If the real driver is
  a habit of over-specifying pinned task fields, the cheaper answer is authoring
  guidance and this intent should be retired rather than built. Testing it means
  counting how often a completed-section correction was actually needed across
  authors, not how often this one hit it.
- That the four instances are the same defect and not four different ones that
  happen to end at the same guard.
- That preserving the audit trail matters more than the simplicity of a reset.
  Three of the four deliveries chose to carry a false contract rather than reset,
  which is evidence for it but not proof.

## Related, recorded rather than folded in

A round-2 reviewer of the approval-recording change (core 2.26.13) raised a
Blocker this intent does not own but which belongs beside it: the engine's
`spec-approved` and `plan-approved` guards still admit `Status: Approved`
alone, so the dated approval entry is instructed and not enforced. The change
shipped the instruction on all three routes that reach those gates — the two
G-plan modes and the crash-recovery resume — and claims no more than that.

Making it enforced means the engine parsing a free-form dated entry and
refusing a human gate when it is absent. That is a new refusal on an approval
gate, which is a governance surface, and it needs owner authority and its own
contract rather than riding a light-mode change. Recorded here because the two
questions share a subject — what the approval record has to guarantee — and
whoever picks this up should decide both together.

## Source

- Mode: repo-origin
- Locator: docs/product/intents/contract-amendment-pre-wave-window.md
- Revision: f443b09ff
- Authority: repo-origin
