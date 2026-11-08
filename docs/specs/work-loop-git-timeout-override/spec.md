# Spec: the work-loop supervisor's git timeout is overridable

- **Status:** Draft <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** none
- **Brief:** none
- **Discovery:** none
- **Depends on:** none
- **Contract:** none
- **Shape:** service
- **Risk triggers:** security-boundary

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.
>
> **Not every section is contract.** `Agent Rules`, `Testing Strategy` and
> `Acceptance Criteria` are what a completion gate reads, and an amendment
> changes them. `Outcome`, `What Changes`, `Durable Outputs`, `Follow-ons` and
> `Assumptions` are working material: they orient a reader and an author corrects them in place
> as the work teaches, without an amendment and without a review round. A review
> finding against working material is advisory — it cannot block, because nothing
> gates the text it cites. Marking the tiers is the spec's job; honouring them
> when a finding is adjudicated is the reviewing surface's.

## Outcome

An owner running the work-loop supervisor on a loaded machine can raise the wall-clock limit on each supervisor git call by setting one environment variable. A run that previously ended in `denied-git-unavailable` under load completes, and a hung git process is still cut off within a bounded ceiling.

## What Changes

- The per-call git timeout becomes the value of `WORK_LOOP_GIT_TIMEOUT_S`, resolved once when the supervisor's git module loads — `packs/core/.apm/skills/work-loop/scripts/_supervisor_git.py`. Every process that loads that module reads the variable from its own environment: the supervisor, `brief-runner.py`, `evidence-gate.py` and `delivery-fact-feed.py`.
- The supervisor reference states what to do after a `denied-git-unavailable` refusal — `packs/core/.apm/skills/work-loop/references/supervisor.md`.
- Core releases a patch version with a changelog fragment — `packs/core/pack.toml`, `packs/core/.claude-plugin/plugin.json`, `docs/product/changelog.d/`.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| Operations | An adopter sets and interprets the variable | `packs/core/.apm/skills/work-loop/references/supervisor.md` (Refusals, the existing `denied-git-unavailable` row: its controller action changes, and no second statement of the action is added) | work-loop skill | the row names the variable, the 60 and 240 bounds, says a value that is not a number is ignored without notice, says where the value in effect shows (the `denied-git-unavailable` message and the `git-history` record's `timeout_s`), says "wait, retry once, then stop and ask", and warns that `brief-runner.py` ends a supervisor call at its own 300-second limit, so two slow git calls can surface as `CODE_TIMEOUT` instead | the row is present in the source and both projections |
| Release history | A pack content change | `docs/product/changelog.d/` fragment, core patch bump | core pack | `tools/changelog.py validate` and `tools/check-core-release.py` pass | the fragment names the new core version |
| User promise, product truth, architecture, decision rationale, interface compatibility, maintainer procedure | Not applicable: no user-facing behavior beyond the one variable, no structure or interface change | none | — | — | — |

## Agent Rules

### Always do

- Resolve the variable in one pure function and bind the result to the module-level `GIT_TIMEOUT_S`, so every existing reader and test that sets that name keeps working.
- Treat the variable's value as untrusted input: parse it as a number, require it finite, and clamp it; never pass it to a shell or a format string.
- Leave the default at 60 seconds when the variable is unset.
- Keep the ceiling at or below the run lock's margin for the git work around the red proof (`_LOCK_MARGIN_SECONDS` in `_supervisor_admission.py`, 300 seconds). One hung call at the ceiling must fit in that margin, or a second run could take a lock that is still held. This bounds a hung call only; it does not bound the total of many slow calls that each finish under the ceiling (see the Assumptions).
- Treat both bounds as security controls, not tuning. The setter is whoever controls the launching process's environment: the operator, or an orchestrating agent that prefixes a command. The floor stops anyone shortening the wait. The ceiling caps how long a setter can stretch it.

### Ask first

- Any change to the floor (60) or the ceiling (240).
- Any second timeout knob, a retry layer, or a per-call-type timeout.

### Never do

- Read the variable on every call, or read it from anywhere but the environment of the process that loads the module (git's stripped child environment is unchanged and never carries it).
- Add a new module, a new dependency, or a new refusal code.
- Touch the separate `GIT_TIMEOUT_S` constants in `brief-runner.py`, `lint-spec-status.py` or `lint-graph-pointers.py`.

## Testing Strategy

- **Timeout resolution (AC-0001 to AC-0004): TDD, in a test module that is not integration-gated.** A pure function with a closed input space; each acceptance criterion below is one table row.
- **Ceiling fits the lock margin (AC-0007): TDD.** A test reads the ceiling and `_LOCK_MARGIN_SECONDS` and fails if they disagree.
- **Both launch paths and the recorded evidence use the effective value (AC-0005, AC-0006): goal-based, exercised by the existing supervisor git suite** with a freshly loaded module copy and the variable set. The existing slow-child tests cover only `_launch_bounded`; a new test must prove the `_launch` path (`subprocess.run(..., timeout=GIT_TIMEOUT_S)`) refuses a call that runs past the value as `denied-git-unavailable`. New resolver and ceiling tests live in a module without the suite's integration marker, so they run in the default lane.
- **The supervisor note and the release bookkeeping: goal-based.** `grep` for the note in the source and projections, then `tools/changelog.py validate`, `tools/check-core-release.py` and the registry pin test.

## Acceptance Criteria

"Parses" means Python's `float()` accepts it, so surrounding whitespace, underscores, exponents and non-ASCII digits are accepted; the result is then clamped.

- [ ] **AC-0001.** With `WORK_LOOP_GIT_TIMEOUT_S` unset, `GIT_TIMEOUT_S` is 60.0 after the module loads.
- [ ] **AC-0002.** A value that parses to a finite number from 60 to 240 inclusive becomes `GIT_TIMEOUT_S` unchanged.
- [ ] **AC-0003.** A value that parses to a finite number outside 60 to 240 becomes the nearer bound.
- [ ] **AC-0004.** A value that does not parse to a finite number (empty, non-numeric, `nan`, `inf`, or an overflow such as `1e309`) leaves `GIT_TIMEOUT_S` at 60.0 and raises no error.
- [ ] **AC-0005.** A git call that runs past `GIT_TIMEOUT_S` is refused as `denied-git-unavailable` through each of the two launch paths.
- [ ] **AC-0006.** A `git-history` evidence record's `timeout_s` equals the `GIT_TIMEOUT_S` of the process that built it, the evidence process.
- [ ] **AC-0007.** The ceiling is no greater than `_LOCK_MARGIN_SECONDS`.

## Follow-ons

none

## Assumptions

- Decided: Product: the ceiling is 240 seconds — one hung call then fits the 300-second lock margin; the owner chose it (settled by: eugenelim).
- Defaulted: Technical: an unparseable value falls back to 60 without a warning — default: silent fallback, so no refusal path is added and the note says so; if wrong: add a stderr line at load (settled by: eugenelim).
- Defaulted: Technical: only `_supervisor_git.py` changes; the processes that load it pick the variable up, and `brief-runner.py` keeps its own separate `_launch` constant — default: out of scope; if wrong: a sibling spec applies the same function there (settled by: eugenelim).
- Defaulted: Product: the change carries no pack eval update — default: the variable is an operator setting with no skill-behaviour change; if wrong: add the eval work (settled by: eugenelim).
- Defaulted: Technical: an environment variable, not a `supervisor-policy.json` field — default: the module is also loaded by `evidence-gate.py`, `brief-runner.py` and the delivery feed, which do not read the policy, and an operator can set it per run without a repository edit; cost: admission's lock-invariant check cannot see the value, so AC-0007 pins the ceiling to the margin instead; if wrong: move the value into the policy and let admission check it (settled by: eugenelim).
- Defaulted: Technical: the runner-driven path is an accepted risk — `brief-runner.py` ends a supervisor call at 300 seconds, so two slow git calls at the ceiling can answer `CODE_TIMEOUT` rather than `denied-git-unavailable`; the operations row warns operators; if wrong: add a criterion tying the runner's limit to the ceiling (settled by: eugenelim).
- Defaulted: Technical: the total git time inside one run-lock hold is an accepted risk — the lock is stale after 2400 seconds and the red-proof budget is 1800, leaving 600 seconds; at the 60-second default that takes ten calls at the limit, and at the 240-second ceiling three calls just under it can pass it, so a second run could reclaim a lock that is still held; the operations row tells operators to keep the value low and raise it only after a refusal; if wrong: add a criterion bounding the total git wall-clock per hold (settled by: eugenelim).
