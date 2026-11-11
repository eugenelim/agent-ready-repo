# Spec: Dispatch-only workflows carry a posture check

- **Status:** Draft
- **Owner:** eugenelim
- **Constrained by:** ADR-0086
- **Brief:** brief:workflow-posture-pinning-delivery
- **Discovery:** intent:dispatch-workflow-posture-assertions
- **Contract:** none
- **Shape:** integration

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.
>
> **Not every section is contract.** `Agent Rules`, `Testing Strategy` and
> `Acceptance Criteria` are what a completion gate reads, and an amendment
> changes them. `Outcome`, `What Changes`, `Durable Outputs`, `Follow-ons` and
> `Assumptions` are working material an author corrects in place.

<!-- Mode: light (work-loop). The change adds a drift check beside existing scanners and narrows no control; it adds no dependency (pure stdlib), crosses no new security boundary and is reversible. -->

## Outcome

A maintainer who edits `test-corpus.yml` or `test-roster.yml` sees a failed check when the edit widens the token, drops a timeout, adds a trigger or dispatch input, moves to a larger runner, removes `persist-credentials: false`, or references a secret. Each such edit fails before it reaches the default branch.

## What Changes

- A new posture check and its paired self-test under `tools/`, built on `tools/posture_harness.py`, audit both workflows.
- The check runs in the gate chain through `tools/repo/build_gate_chain.py`, and the ordered literal in `tools/test_build_gate_chain.py` names it.
- Both workflow paths join the tuple in `tools/check-zizmor-excessive-permissions.py`.
- `docs/architecture/remote-verification.md` states which properties of these two files are pinned.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| Current architecture | The page names the accepted residual and what is now pinned | `docs/architecture/remote-verification.md`, the accepted-residual paragraph | eugenelim | The paragraph lists the pinned properties and keeps the residual wording | close-work finds no claim that these files are unpinned |

## Agent Rules

### Always do

- Assert properties of the workflow; do not restate the file line by line.
- Give every assertion family a mutation that turns the check red.
- Refuse any key spelling or syntax form the check does not model.

### Ask first

- Adding a job to either workflow, because per-job assertions then need a mutation per instance.
- Any change to what the existing zizmor and actionlint steps verify.

### Never do

- Import a third-party YAML library into a new file under `tools/`.
- Weaken `actionlint` or `zizmor` coverage of these files.

## Testing Strategy

- The audit over each workflow and the refusal of unmodelled syntax: TDD, one mutation per family run through `tools/posture_harness.py`, because the harness already enforces baseline-clean and no-op rejection.
- Gate wiring: goal-based, `tools/test_build_gate_chain.py` passes with the new ordered literal.
- Scanner ownership of the permissions class: goal-based, `python3 tools/check-zizmor-excessive-permissions.py` passes with both files in its tuple.

## Acceptance Criteria

- [ ] The check exits 0 on the real `test-corpus.yml` and `test-roster.yml`.
- [ ] For each family in {trigger set, no `workflow_dispatch.inputs`, top-level `permissions: contents: read` with no job-level `permissions`, `timeout-minutes` on every job, `runs-on` an exact standard hosted label, `persist-credentials: false` on every checkout, no `secrets.` reference}, one seeded mutation of either file turns the check red and names the family.
- [ ] A seeded duplicate key, a flow-style mapping, an alias, and a quoted or escaped spelling of `permissions` each turn the check red rather than passing or being skipped.
- [ ] The self-test's baseline-clean and no-op checks pass, so a mutation that changes nothing is reported.
- [ ] The gate chain runs the check, and `tools/test_build_gate_chain.py` passes with the chain's ordered literal.
- [ ] `tools/check-zizmor-excessive-permissions.py` lists both workflow paths and passes on the real tree.
- [ ] The new files under `tools/` import only the standard library and `posture_harness`.

## Follow-ons

- eugenelim: `docs/product/intents/dispatch-workflow-posture-assertions.md` still cites `docs/architecture/verification-graph.md` section 7.4, a page that no longer exists; the residual lives in `docs/architecture/remote-verification.md`.

## Assumptions

- Technical: a key grammar that refuses every unmodelled form can be written for these two flat workflows — if wrong, the check cannot pin the properties and the work stops for a design decision (settled by: the mutation list in the third criterion).
- Defaulted: Technical: the new check is its own file rather than an extension of `tools/test-build-check-workflow.py` — default: own file built on `posture_harness`, because that file carries a bespoke driver; if wrong: extend it and drop the harness (settled by: eugenelim).
