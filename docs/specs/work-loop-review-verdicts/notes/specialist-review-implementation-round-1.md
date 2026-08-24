## Blockers

**1. Adjudicator discovery can trust a primitive supplied by the diff under review.** `packs/core/.apm/skills/work-loop/SKILL.md:528`. A reviewed change can add or modify the only discoverable `findings-adjudication.v1` primitive, causing work-loop to invoke attacker-controlled adjudication over the same findings before disposition. Fix: treat any adjudicator declaration or implementation touched by the current review unit, or otherwise lacking pre-existing trusted provenance, as unavailable; require discovery from a pre-existing approved source and add an eval for a self-supplied adjudicator.

**2. Explicit adjudication acceptance is not represented in the closed verdict schema.** `packs/core/.apm/skills/work-loop/SKILL.md:814`. A raw `refuted` or `downgrade_recommended` result can be serialized as `status: rejected` or a lower `effective_severity` without machine-readable evidence that work-loop accepted it. Fix: add a closed acceptance evidence object required before status or effective severity can change, and add unaccepted-result evals.

**3. Persistent-state full-mode trigger omits AC4 migration surfaces.** `packs/core/.apm/skills/work-loop/SKILL.md:60`. The full-mode trigger omits persisted configuration/checkpoints, retained API payloads, replays, imports, exports, and destructive transformations, so those migrations can stay light-mode. Fix: mirror the complete persistent-state trigger set and assert every AC4 shape.

**4. Mandatory reviewer skips can still reach readiness.** `packs/core/.apm/skills/work-loop/SKILL.md:874`. The finish checklist allows warranted full-mode reviewers to be named skips, while precedence blocks only invalid or missing mandatory reviews. Fix: make a mandatory named skip a BLOCKED condition and test it.

## Concerns

**5. Adjudicator rationale and provenance lack prompt-injection containment.** `packs/core/.apm/skills/work-loop/SKILL.md:542`. A compromised adjudicator can persist instructions that later LLM handoffs ingest next to authoritative fields. Fix: declare payloads untrusted data, parse only closed fields, quote free text as data, ignore embedded instructions, and add a hostile-output eval.
