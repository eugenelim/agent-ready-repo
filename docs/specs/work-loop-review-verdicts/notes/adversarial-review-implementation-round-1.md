## Blockers

**1. Persistent-state migration can still skip the quality route.** `packs/core/.apm/skills/work-loop/SKILL.md:76`. The new migration depth is only reachable through the existing full-mode or infra/destructive quality path, so a non-destructive persistent representation change can remain light-mode and never receive the required quality-engineer migration review. Fix: add persistent representation or mixed-version deployment as a full-mode and quality-engineer operational-safety trigger independent of infra/destructive routing.

**2. The core version bump leaves an existing test red.** `tests/roster/test_security_checklists_okf_projection.py:106`. The pack and plugin say `2.10.6`, but this test still asserts `2.10.5`. Fix: update the assertions while preserving the OKF checks.

**3. The shipping metadata is still open.** `docs/specs/work-loop-review-verdicts/spec.md:3`. The spec remains `Implementing`, the plan remains `Executing`, the README says `Implementing`, and every AC is unchecked. Fix: mark the spec `Shipped`, plan `Done`, update the index, and check or explicitly defer every AC.

**4. Verdict precedence verification misses two blocking cases.** `packs/core/.apm/skills/work-loop/evals/evals.json:426`. The evals do not cover failed required gates or missing/invalid mandatory reviewers. Fix: add eval cases and focused assertions that both produce `BLOCKED`.

## Concerns

**5. Finding IDs are not required to be stable in shipped doctrine.** `packs/core/.apm/skills/work-loop/SKILL.md:810`. The implementation requires only a non-empty `id`, allowing per-run IDs that break adjudication and verdict traceability. Fix: require stable non-empty IDs and assert that contract.
