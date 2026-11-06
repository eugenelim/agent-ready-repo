# Spec: Supervisor self-describing output

- **Status:** Draft
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** none
- **Brief:** none
- **Discovery:** none
- **Depends on:** none
- **Contract:** none
- **Shape:** service

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.
>
> **Not every section is contract.** `Agent Rules`, `Testing Strategy` and
> `Acceptance Criteria` are what a completion gate reads, and an amendment
> changes them. `Outcome`, `What Changes`, `Durable Outputs`, `Follow-ons` and
> `Assumptions` are working material.

## Outcome

A controller driving a full-mode run, on any model, gets the answer to its next question from the supervisor itself instead of from reading reference files. Four common stalls resolve in the output or in one pointer: a rejected `--json` flag, an `invalid-result` that names no field, a `status` or `next` answer that does not say what to do next, and a reviewer-fallback question that the section people search never answers.

## What Changes

- `--json` is accepted on every `work-supervisor.py` verb — `scripts/work-supervisor.py`
- Every `status` and `next` answer carries a one-line `route` naming the next action — `scripts/work-supervisor.py`
- The routing decision has one written home, a first-match table — `references/session-resumption.md`
- `invalid-result` from `report` names the field that failed — `scripts/_supervisor_loop.py`
- The single-agent fallback section points an undispatchable reviewer role at the existing reviewer rule — `references/supervisor-mode.md`
- The reference documents describe `--json` and `route` — `references/supervisor.md`, `references/state-schema.md`
- One eval case covers the reviewer fallback — `evals/evals.json`
- The `core` pack ships these as one patch release — `pack.toml`, `.claude-plugin/plugin.json`, one changelog fragment

All paths above are under `packs/core/.apm/skills/work-loop/` except the three release files.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| Interface reference | `--json`, `route` and the refusal text change what a controller reads | `packs/core/.apm/skills/work-loop/references/session-resumption.md`, `supervisor.md`, `state-schema.md` | implementing task | a pin test on the three files and on the script strings | close-work confirms the three files agree |
| Release history | non-cosmetic `core` pack change | `docs/product/changelog.d/` fragment | implementing task | the release checker and the fragment | close-work confirms the fragment names the shipped version |
| User guides | none: the guides name `status --json` only to say it is run first, which stays true | none | none | none | none |
| Decision record | none: no decision is reversed or made | none | none | none | none |

## Agent Rules

### Always do

- Keep every refusal `code`, every exit code, and what each check accepts as it is today; the only changes are refusal detail text, the added `route` key, and `--json` accepted after every verb.
- Write the failing test before the code for each behavior change.
- Say what a field must be; do not quote what the controller sent.

### Ask first

- Adding any new verb, any new refusal code, or any new key other than `route` to a `status` or `next` answer.
- Any change to `review-artifact.py`.

### Never do

- Add `result_template`, `explain`, a per-code `remedy` field, a section index for `supervisor.md`, or an `ingest` command.
- Add a `## Not checked` footer to `adversarial-reviewer`; it would disqualify its reports from the clean fast path.
- Add `route` to the answer of any verb other than `status` and `next`.
- Edit `dispatch.py`, its packaged mirror under `packages/agentbundle/`, or anything under `docs/specs/supervisor-self-describing-output/.supervisor/` or `delivery/`.

## Testing Strategy

- **Supervisor answers: `--json`, `route` and the routing table's strings (AC-0001, AC-0002, AC-0003, AC-0004, AC-0005, AC-0006, AC-0007, AC-0008)** use TDD through `main(argv)` on the supervisor test harness, because each is a deterministic answer over a run state. The git-backed cases are integration-gated and run by the Gate A-supervisor lane; the string, length and detail checks are ungated unit tests.
- **The `invalid-result` refusal text (AC-0009, AC-0010)** uses TDD at `loop.report` and `_validate_result`, because the detail is a pure function of the result sent.
- **Reference sentences and the routing table's rows (AC-0011, AC-0012, AC-0013, AC-0014, AC-0015, AC-0016, AC-0017)** use goal-based pin tests that read the reference files, because each criterion is the presence or absence of a stated sentence or row.
- **The eval case (AC-0018)** uses a goal-based pin test that loads `evals/evals.json`, because the criterion is the presence of one case.
- **Release (AC-0019, AC-0020, AC-0021)** uses goal-based checks: the release checker and the roster file that reads `_RELEASED["core"]`.

## Acceptance Criteria

- [ ] **AC-0001.** Each `work-supervisor.py` verb (`park`, `gates`, `start`, `next`, `report`, `status`, `resolve-effect`) given `--json` after the verb prints the same stdout and exits with the same code as the same call without it.
- [ ] **AC-0002.** Every `status` answer that is a run view or carries a top-level refusal has a `route` equal to the string the routing table in `references/session-resumption.md` gives for its shape, including the refusal from the pin check, the unsupported-ref-storage refusal, and, when forced by a test fault, the lock refusal and the internal-error refusal.
- [ ] **AC-0003.** On a `status` answer where `retry_count` and the retry cap can be read, a non-terminal run at or above the cap has the cap row's `route` even when a refusal stands, as `status --check` exits 3 for it; a `next` answer whose request is the `retry-cap` human decision has the same `route`.
- [ ] **AC-0004.** Every `next` answer from the request, terminal and refusal shapes, and the pin-check refusal, has a `route` equal to the string the routing table gives for its shape: a refusal, a terminal answer, a `human-decision` request, or any other request.
- [ ] **AC-0005.** A usage error (exit 2) from `status` or `next` carries no `route`.
- [ ] **AC-0006.** A `route` contains no `detail` text from a refusal.
- [ ] **AC-0007.** A `route` is 160 characters or fewer.
- [ ] **AC-0008.** `status --check` exits with the same codes as before `route` existed.
- [ ] **AC-0009.** `report` refuses with `invalid-result` and a detail that names the failing field and states its required form when the result is not a JSON object, when `schema_version` is not equal to 1, or when `request_id`, `run_id` or `kind` is not a non-empty string.
- [ ] **AC-0010.** An `invalid-result` detail from `report` contains no non-empty value the controller sent, except where that value falls inside the detail's fixed field name and required-form text.
- [ ] **AC-0011.** `references/supervisor-mode.md` § Single-agent fallback sends an undispatchable reviewer role to `SKILL.md` § Step 4. REVIEW and to the `fallback` and `mandatory_when` fields of `review-rules.json`.
- [ ] **AC-0012.** `references/supervisor-mode.md` § Single-agent fallback restates no part of the reviewer rule that `SKILL.md` and `review-rules.json` hold.
- [ ] **AC-0013.** `references/session-resumption.md` holds a routing table for the `status` and `next` shapes with a first-match order and one row per shape.
- [ ] **AC-0014.** Step 1 of `references/session-resumption.md` points to that table instead of ranking shapes.
- [ ] **AC-0015.** `references/supervisor.md` states that `--json` goes after the verb on every verb.
- [ ] **AC-0016.** `references/supervisor.md` states that `status` and `next` carry `route`.
- [ ] **AC-0017.** `references/state-schema.md` lists `route` among the `status` keys.
- [ ] **AC-0018.** `evals/evals.json` carries a case with id `undispatchable-reviewer-follows-roster-rule`, a prompt that has an undispatchable reviewer role, a non-empty `expected_output` and non-empty `assertions`.
- [ ] **AC-0019.** The `core` version in `pack.toml` and `.claude-plugin/plugin.json` is one patch above the version `packs/core/pack.toml` carries on `origin/main` as fetched when this criterion is checked.
- [ ] **AC-0020.** `tools/check-core-release.py --base origin/main` passes.
- [ ] **AC-0021.** The changelog fragment and the `_RELEASED["core"]` pin in `tests/roster/test_registry_upgrade_notes.py` name the version of AC-0019.

## Terminal Intent

`code` — ship the flag, the `route` key and its table, the `invalid-result` wording, the reference sentences, the eval case, and the `core` patch release.

## Follow-ons

none

## Assumptions

- Technical: a `route` key on `status` or `next` does not break a caller that reads the answer by key — callers in this repository read named keys; none compares the whole object (settled by: the status and next tests).
- Technical: models usually pipe `status` and `next` output into a script (Pi 91 of 97 `next` calls, Claude Code about half piped and half captured), so `route` reaches them only when the script prints it; its value is unmeasured (settled by: a transcript comparison after release).

## Closeout

Duties after the run reaches `terminal`; none is an acceptance criterion.

- Run `git fetch origin`, check that `origin/main` has not shipped a newer `core` patch, and re-point the version, fragment and `_RELEASED["core"]` pin to the next patch above it if it has.
- Rebuild projections with `agentbundle catalogue self-host --root . --write --force` and commit them.
- Run the suites and roster files named in the plan's Rollout.
- Set the spec `Shipped` and the plan `Done`, run `lint-spec-status.py`, open the PR with the four-question description.
