# Adversarial review 5 — post-EXECUTE

**Date:** 2026-07-22
**Reviewer:** adversarial-reviewer subagent

## Blockers

1. `docs/architecture/reference.md` + README link are outside declared scope (pilot side-effect; pilot evidence lives in transcript.md; reference.md is a normative golden-path doc, not a spec deliverable)
2. Spec metadata stale — Status still `Implementing`, ACs still `[ ]`; plan status still `Executing`

## Concerns

3. Verification method deviates — Step 1 was trigger-analysis, Step 2 was subagent dispatch (not live pack-installed session)
4. Pilot repo is docs-heavy easy case; target audience may have docs-light repos
5. Architect pack contributes nothing to the pilot path; ask-first gate was not surfaced for human decision
6. AC5 missing fourth case ("completed via direct model reasoning, no skill fired")

## Nit

7. Plan status not advanced to Done

## Resolution

- Blocker 1: Extract reference.md + README.md link to separate PR; revert from this PR
- Blocker 2 + Nit 7: Flip spec Status → Shipped, check ACs, add AC5 fourth case; plan → Done  
- Concern 3: Amend Testing Strategy to sanction trigger-analysis + subagent method with reason
- Concern 4: Add generalization-limit note to transcript
- Concern 5: SURFACE to user — value origination question (see below)
- Concern 6: Addressed as part of Blocker 2

## Concern 5 — surfacing to user

The no-skill finding is new information not anticipated in the spec's ask-first conditions. The ask-first gate covers adapt-to-project routing but not "no skill" routing. The reviewer correctly flags that this is a value origination question: the architect pack's `tutorial` field is now wired pointing to a tutorial for a path that does not involve any architect skill. Whether this is acceptable (the pack's value is in subsequent design/diagram/review skills that reference.md enables) is a judgment the operator should make explicitly.

Decision options:
A. Accept as-is: path works, tutorial is honest, pack value is in subsequent sessions not the starter-prompt
B. Update the spec to explicitly acknowledge no-skill routing and document why the field wiring is still correct
C. Hold the tutorial field wiring until a separate review of the contract's audience fit

The plan's T3 precondition was: "if T2 triggers non-architect skill routing, human confirmation required." The observed route was "no skill" — not covered by the precondition's exact wording, but close enough in spirit that surfacing is the right call.
