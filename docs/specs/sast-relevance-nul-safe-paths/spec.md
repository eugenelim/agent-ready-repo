# Spec: SAST relevance step sees every changed path

- **Status:** Draft
- **Owner:** eugenelim
- **Constrained by:** ADR-0113, ADR-0086
- **Brief:** brief:gates-that-read-clean-delivery
- **Discovery:** intent:gates-that-read-clean-while-gating-nothing
- **Contract:** none
- **Shape:** integration

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.
>
> **Not every section is contract.** `Agent Rules`, `Testing Strategy` and
> `Acceptance Criteria` are what a completion gate reads, and an amendment
> changes them. `Outcome`, `What Changes`, `Durable Outputs`, `Follow-ons` and
> `Assumptions` are working material an author corrects in place.

<!-- Mode: full (work-loop). The change edits a security gate in the workflow that carries the required check, so the security-boundary trigger fires and ADR-0113 requires the change its own review. -->

## Outcome

A maintainer who changes a file under a scanned directory sees `gate-sast` run its scan whatever characters the file name holds. A pull request can no longer turn a security scan off by naming a changed file with a non-ASCII or special character.

## What Changes

- The `Detect whether SAST-relevant files changed` step in `.github/workflows/build-check.yml` reads changed paths NUL-delimited and matches them without the line-oriented quoting that hides a path.
- `tools/test-build-check-workflow.py` gains a bash differential that runs the step body against fixture repositories, and a posture mutation that restores the quoted form.
- The step's fail-closed fallbacks (unreadable `SAST_DIRS`, unreadable `SAST_CONFIG`, failed diff) stay as they are.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| Decision rationale | ADR-0113 records the quoted-path gap as a residual it deliberately left open | `docs/adr/0113-sast-guarantee-moves-from-the-local-gate-to-gate-sast.md` Context | eugenelim | The Context paragraph states the residual is closed and names this spec | close-work reads the ADR and finds no open residual |
| Current architecture | none | the gate topology is unchanged | eugenelim | none | none |

## Agent Rules

### Always do

- Make the relevance predicate see more paths, never fewer; a repair that drops a path class is a defect.
- Keep every existing fail-closed fallback: an unreadable input runs SAST.
- Route the change through the security reviewer before merge.

### Ask first

- Any change to which directories or config files count as SAST-relevant.
- Any edit to a workflow other than `build-check.yml`.

### Never do

- Make `Run make sast` skippable by a new condition.
- Add a third-party dependency to the posture test.
- Edit `.github/workflows/docs.yml` in this spec; its ADR-immutability step is a separate warn-only heuristic.

## Testing Strategy

- Relevance predicate over odd path names: goal-based, a bash differential that runs the real step body against a fixture git repository per case, because the behavior only shows when `git` quotes a path.
- Posture pin on the repaired form: TDD, a mutation that restores `--name-only` without `-z` must turn `tools/test-build-check-workflow.py` red.
- Security review of the diff: a required reviewer pass, recorded in the pull request.

## Acceptance Criteria

- [ ] For a fixture pull request whose only change is a file named `tools/weird<U+00E9>.py` (any directory in `SAST_DIRS`), the step writes `skip_sast=false`.
- [ ] For a fixture pull request whose only change is a file under a `SAST_DIRS` directory with a space, a double quote, a backslash or a newline in its name, the step writes `skip_sast=false` in each case.
- [ ] For a fixture pull request that changes only files outside `SAST_DIRS` and outside the SAST config files, the step writes `skip_sast=true`.
- [ ] For a fixture whose `git diff` fails, the step writes `skip_sast=false`.
- [ ] The posture test fails when the step's diff command is replaced by `git diff --name-only` without `-z`.
- [ ] The posture test passes on the repaired workflow with its mutation count and family coverage otherwise unchanged except for the added family.

## Follow-ons

- eugenelim: `.github/workflows/docs.yml` ADR-immutability step uses `git diff --name-only` and an unquoted word-split loop; it is a warn-only heuristic, so it is recorded here and not repaired.

## Assumptions

- Defaulted: Technical: the repair is `git diff --name-only -z` with NUL-safe matching, not `core.quotePath=false` — default: `-z`, because it also removes the newline-in-path ambiguity; if wrong: switch to `quotePath` and drop the newline case from the second criterion (settled by: eugenelim).
