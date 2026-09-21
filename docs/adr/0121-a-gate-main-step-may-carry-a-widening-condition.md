# ADR-0121: A gate-main step may carry a roster-authorized widening condition

- **Status:** Accepted
- **Date:** 2026-09-21
- **Areas:** ci, testing
- **Reversibility:** high
- **Decision-makers:** eugenelim
- **Supersedes:** none
- **Supersedes in part:** none
- **Superseded by:** none
- **Superseded in part:** none
- **Related:** ADR-0086 (the adjacent decision that split the SAST gate into its own CI job; not superseded)

## Decision summary

- **Decision:** A `gate-main` step may carry a step-level `if:` only when its scalar value exactly equals the widening expression derived for that step from `tools/lint-ci-parity.py`'s `STEP_DISPOSITION` roster.
- **Because:** `!cancelled()` widens execution beyond the implicit success condition, while the controls this exception amends were written to reject conditions that narrow execution and can hide a failed gate.
- **Applies to:** step-level `if:` conditions in the `gate-main` job of `.github/workflows/build-check.yml`; every other job, condition, and fail-open mechanism keeps its existing rule.
- **Tradeoff accepted:** the guard's admitted set now follows `STEP_DISPOSITION`, whose reasons are checked mechanically for presence but not truth, so a roster edit can widen what the guard accepts.
- **Revisit if:** an admitted expression can narrow execution, roster reasons become machine-interpreted policy, or the guard and `STEP_DISPOSITION` no longer derive one admitted set.

## Context

The original prohibition was correct. A step-level `if: ${{ false }}` is a one-line total bypass, and neither actionlint nor zizmor at `--min-severity high` flags it. The construction test therefore added explicit falsy-condition mutations for the `gate-main` anchor, the export-boundary step, and the aggregator (`tools/test-build-check-workflow.py:1917-1927`).

Three Shipped specs preserve how that prohibition was reached. `docs/specs/ci-gate-parallelization/spec.md:193-203` bans `continue-on-error` as a total bypass, and its retrospective table records at `:835` that the ban left "its exact twin, a falsy step-level `if:`" open for the next round. `docs/specs/pr-gate-suite-disposition/spec.md:231-234` makes AC-0005 require `lint-ci-parity.py` to exit 1 when a `PR_GATED` entry names a step or job carrying `continue-on-error` or an `if:` condition. `docs/specs/site-ci-contract-closure/spec.md:71-79` includes a step-level `if:` in the standing construction test's definition of a neutered module.

Those controls classify the presence of a condition as narrowing because their threat is a gate that does not run. `!cancelled()` has the opposite effect: compared with the implicit success condition, it adds execution after an earlier failure and removes no successful execution. It only widens when the step runs. Treating it as neutering is therefore a classification mismatch, not a defect in the widening condition.

The three Shipped specs remain unchanged as historical records and receive no backpointer. The frozen-document rule keeps their accepted prose fixed; the operative instruction belongs in the living guard and `tools/AGENTS.md`, at the roster-edit point of use.

## Decision

We will admit a step-level `if:` on a `gate-main` step only through an exact, roster-derived widening exception.

- **D1:** `gate-main` keeps a default prohibition on step-level `if:` conditions. A step is exempt only when `STEP_DISPOSITION` derives an admitted expression for that named step and the workflow scalar equals that expression exactly.
- **D2:** `!cancelled()` is an admitted widening expression. Relative to the implicit success condition, it allows the step to run after an earlier failure and never suppresses a run that the implicit condition would allow.
- **D3:** Every other condition remains forbidden, including every falsy or composed condition. Exact string equality makes `!cancelled() && false` fail admission.
- **D4:** The construction guard derives its admitted set from `STEP_DISPOSITION`; it does not maintain a second allowlist. A roster entry and its admitted workflow expression therefore change together or fail the guard.
- **D5:** This record does not amend or supersede a prior ADR. The reversed rule lives in the three Shipped specs, and ADR supersession fields cite ADRs, so all four supersession fields remain `none`. ADR-0086 stays the adjacent CI-gate decision and is not superseded.
- **D6:** The three Shipped specs are historical evidence, not living instruction. They remain frozen, receive no pointer to this record, and do not govern the admitted expression after this decision.

## Decision drivers

- **Bypass resistance.** A falsy, narrowing, or composed expression must still fail closed.
- **Semantic direction.** A widening condition must not be rejected by a control designed for narrowing conditions.
- **Single ownership.** The guard and the local-parity roster must not carry independent admitted-condition lists.
- **Mutation evidence.** The existing falsy-`if` mutations must remain caught after the exception is added.

## Consequences

**Positive:**
- A `gate-main` step can use `!cancelled()` without being mislabeled as neutered, while the default ban remains in force.
- Admission is closed under exact equality: a suffix, conjunction, falsy value, or different condition does not inherit the exception.
- The post-amendment `tools/test-build-check-workflow.py` self-test still reports **180 mutations caught across 80 assertion families**, including the falsy-`if` mutations.
- The post-amendment `tools/test-lint-ci-parity.py` self-test still passes **200/200**, including `if-false-is-conditional-by-presence` (`tools/test-lint-ci-parity.py:1354-1361`).

**Negative:**
- The guard now trusts `STEP_DISPOSITION` to define the admitted set. `tools/AGENTS.md:33-45` records that roster reasons are checked for presence, not truth, so a roster edit can widen what the guard accepts.
- Review must assess the semantic direction of a new roster-derived condition; the mechanical check proves exact agreement, not that the roster reason is true.
- The three Shipped specs continue to state the earlier absolute rule because their prose is frozen.

**Revisit if:** an admitted expression can narrow execution, roster reasons become machine-interpreted policy, or the guard and `STEP_DISPOSITION` no longer derive one admitted set.

## Confirmation

- **Mode:** lint/CI
- **Signal:** `tools/test-build-check-workflow.py` reports 180/180 mutations caught across 80 assertion families, including its falsy-step conditions, and `tools/test-lint-ci-parity.py` reports 200/200 with `if-false-is-conditional-by-presence` passing.
- **Owner:** eugenelim.

## Alternatives considered

- **Keep the absolute ban on every `gate-main` step-level `if:`.** Rejected against *semantic direction*: it treats the widening `!cancelled()` expression as equivalent to a falsy condition even though their effects are opposite.
- **Maintain a separate allowlist in the construction guard.** Rejected against *single ownership*: it duplicates `STEP_DISPOSITION` and can drift from the roster that explains each step's disposition.
- **Accept conditions after semantic expression analysis.** Rejected against *bypass resistance*: the required exception is one exact expression, and broader equivalence creates unnecessary admission paths. Exact equality rejects `!cancelled() && false` directly.
- **Edit the three Shipped specs or add backpointers to them.** Rejected because the frozen-document rule preserves them as historical records and puts the operative instruction in a living file at the point of use.

## References

- `tools/lint-ci-parity.py:328` — the `STEP_DISPOSITION` roster from which the admitted expression is derived.
- `tools/AGENTS.md:33-45` — roster-edit ownership and the human-review boundary for reason truth.
- `tools/test-build-check-workflow.py:1917-1927` — falsy step-level `if:` mutations that remain caught.
- `tools/test-lint-ci-parity.py:1354-1361` — `if-false-is-conditional-by-presence`.
- `docs/specs/ci-gate-parallelization/spec.md:193-203,835` — historical prohibition and the falsy-`if` gap it exposed.
- `docs/specs/pr-gate-suite-disposition/spec.md:231-234` — historical AC-0005.
- `docs/specs/site-ci-contract-closure/spec.md:71-79` — historical construction-test definition of a neutered module.
- ADR-0086 — the adjacent CI-gate decision; unchanged by this record.
