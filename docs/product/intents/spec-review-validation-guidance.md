# Review-and-validation guidance for spec authoring

- **Slug:** `spec-review-validation-guidance`
- **Status:** Draft
- **Level:** feature
- **Scale:** app
- **Maturity:** brownfield

## Outcome

- **Input (steerable):** Before each repair, the author marks where each finding
  came from. The author says what each gate proves. The author sends each
  finding through the review check that is already in place.
- **Outcome (lagging):** Spec reviews reach a clean result with fewer repeat
  rounds. Authors do not act on findings that cannot occur in the feature.
- **Guardrail:** Keep the current rule to test facts before review. Reuse the
  current reachability check. Add no lint or review-count limit.

## Opportunity

An author needs to know what changed, what a green gate proves, and which
findings need a fix before the next round starts.

- **Functional job:** Check each finding against the current repo. Apply only
  the fixes that the feature needs.
- **Emotional job:** Trust that a clean review means the work is sound. Do not
  just move faults from one round to the next.
- **Social job:** Give the approver a clear reason to apply or reject each
  finding.
- **Struggling moment:** A repair adds new faults. A green gate is treated as
  proof of more than it checks. A finding from one route is passed to a route
  where the harm cannot occur.

## Current-state evidence

The first premise claimed four new rules. The repo shows a smaller gap:

- **The fact check exists.** `new-spec` step 5a asks for the cheapest check that
  could prove the plan wrong. This intent will point to that rule.
- **The reachability check exists.** Full-mode spec review sends each report to
  `finding-adjudicator`. It checks whether the claimed state can occur. The
  standalone `new-spec` path does not name this route.
- **The gate scope exists.** `lint-spec-status.py` lists its six checks and their
  limits. Authors need a pointer to that list when they read a green result.
- **The finding source is the new rule.** Current guidance does not ask if a
  finding was in the first draft or came from the last repair.

Other review logs show the same need:

- `credential-broker-contract` reached round 2 with drift left by round-1 fixes.
- `local-ci-orchestration` had a test stay green when the required route moved.
- `direct-skill-repository-installation` rejected a finding because its claimed
  harm could not occur.

## Assumptions

- Marking a finding's source will change repair choices, not just add a note.
- Standalone `new-spec` review can use the current review check without taking
  on the work-loop state machine.
- A short link to `lint-spec-status.py` is enough. Copying its list would make a
  second source of truth.
- One fixed review-count limit will not fit all specs. Keep the current
  three-pass stop rule.
- **Knowledge surface:** repo skills, scripts, and review notes checked on
  2026-08-29. This is one source. The change in user behavior is still unsure
  until the test below runs.

## De-risking

- **Reversibility:** two-way door. The team can change this guide without a
  runtime or stored-data change.
- **Prototype approach:** prototype-led. Use old review rounds as the test.
- **Verdict:** Kill the four-new-rules premise. Keep the smaller intent. Repo
  facts support it, but it is still `to-validate`. Desk work is not a user test.

```yaml
validation_hook:
  assumption: The missing origin, gate-scope, and adjudication cues materially improve review triage.
  kill_condition: Kill if fewer than 4 of 6 blinded historical replays avoid the seeded mis-triage, or if any cue causes an unnecessary scope-widening remedy.
  activity: Run six paired review replays without and with the revised guidance, then compare finding dispositions.
```

## Source

- Mode: repo-origin
- Locator: `docs/specs/spec-authoring-discipline/spec.md`
- Revision: `local-2026-08-28`
- Validation evidence:
  - `packs/core/.apm/skills/new-spec/SKILL.md`
  - `packs/core/.apm/skills/work-loop/SKILL.md`
  - `packs/core/.apm/agents/finding-adjudicator.md`
  - `packs/core/.apm/skills/work-loop/scripts/lint-spec-status.py`
  - `docs/specs/credential-broker-contract/notes/review-round-5.md`
  - `docs/specs/local-ci-orchestration/review-round-4.md`
  - `docs/specs/direct-skill-repository-installation/notes/reviews/preexecute-adversarial-adjudication.md`
