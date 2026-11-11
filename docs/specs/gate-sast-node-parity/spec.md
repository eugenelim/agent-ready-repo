# Spec: gate-sast runs under the declared Node version

- **Status:** Draft
- **Owner:** eugenelim
- **Constrained by:** ADR-0083, ADR-0086
- **Brief:** brief:remote-ci-verification-parity-delivery
- **Discovery:** intent:remote-ci-verification-parity
- **Contract:** none
- **Shape:** integration

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.
>
> **Not every section is contract.** `Agent Rules`, `Testing Strategy` and
> `Acceptance Criteria` are what a completion gate reads, and an amendment
> changes them. `Outcome`, `What Changes`, `Durable Outputs`, `Follow-ons` and
> `Assumptions` are working material an author corrects in place.

<!-- Mode: light (work-loop). The change adds one step to an existing job using an action already pinned by commit SHA in the same workflow, so it adds no dependency, crosses no new security boundary and is reversible. -->

## Outcome

A maintainer who dispatches or opens a pull request for `build-check.yml` gets an npm supply-chain scan that runs under Node 24, the version the repository declares. The scan no longer depends on whichever Node the hosted runner image ships.

## What Changes

- `gate-sast` in `.github/workflows/build-check.yml` gains a `Set up Node` step before `Run make sast`, using the same pinned `actions/setup-node` commit the workflow already uses.
- `tools/test-build-check-workflow.py` pins the step and carries a mutation that removes it.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| Current architecture | The runner-environment line for `gate-sast` changes | `docs/architecture/remote-verification.md` | eugenelim | The page states `gate-sast` provisions Node 24 | close-work finds no statement that the SCA leg runs under the runner default |

## Agent Rules

### Always do

- Reuse the `actions/setup-node` commit SHA already pinned in `build-check.yml`.
- Match the Node major to the `engines.node` field in `web/package.json` and `docs-site/package.json`.

### Ask first

- Adding `cache: npm` or any dependency install to `gate-sast`.

### Never do

- Add a new action or a new pinned SHA.
- Add `actions/setup-node` to jobs other than `gate-sast`.

## Testing Strategy

- Workflow posture: TDD, a mutation that removes the step must turn `tools/test-build-check-workflow.py` red, because the posture test is the only thing that notices a deleted setup step.
- The Node version actually used by the SCA leg: manual observation of the first run's log, recorded as a follow-on, because it needs a hosted runner.

## Acceptance Criteria

- [ ] `gate-sast` contains one `actions/setup-node` step that precedes the `Run make sast` step and sets `node-version` to `"24"`.
- [ ] That step's `uses:` value is byte-identical to the `actions/setup-node` value the `gate-css-tokens` job carries.
- [ ] The posture test fails when the step is removed from `gate-sast`.
- [ ] The `node-version` value is equal to the major in `engines.node` of `web/package.json`, and a test fails when the two differ.

## Follow-ons

- eugenelim: first hosted run of `build-check.yml` after merge — confirm the `Run make sast` log shows Node 24.

## Assumptions

- Technical: `engines.node` is `>=24.0.0` in both `web/package.json` and `docs-site/package.json` — the pin stays aligned with the lower bound, which only changes if a package raises it (settled by: the engines check in the fourth criterion).
