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

A controller driving a full-mode run, on any model, gets the answer to its next question from the supervisor and the dispatcher themselves instead of from reading reference files. Each of five common stalls — a rejected `--json` flag, an `invalid-result` that names no field, a `status` that does not say what to do next, a refusal to start follow-up work on a `Shipped` spec, and an unplaced reviewer-fallback rule — resolves in the output or in one sentence of the skill.

## What Changes

- `--json` is accepted on every `work-supervisor.py` verb — `scripts/work-supervisor.py`
- `status` carries a one-line `route` naming the next action — `scripts/work-supervisor.py`
- `invalid-result` from `report` names the field that failed — `scripts/_supervisor_loop.py`
- `dispatch.py` names the supported route when a named spec is `Shipped` — `scripts/dispatch.py`
- The reviewer rule for an undispatchable role sits in the single-agent fallback section — `references/supervisor-mode.md`
- The reference documents describe `--json` and `route` — `references/supervisor.md`, `references/state-schema.md`, `references/session-resumption.md`
- Two eval cases cover the `Shipped` route and the reviewer fallback — `evals/evals.json`
- The `core` pack ships these as one patch release — `pack.toml`, `.claude-plugin/plugin.json`, one changelog fragment

All paths above are under `packs/core/.apm/skills/work-loop/` except the three release files.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| Interface reference | `--json`, `route` and the refusal text change what a controller reads | `packs/core/.apm/skills/work-loop/references/supervisor.md`, `state-schema.md`, `session-resumption.md` | implementing task | a pin test on the three files | close-work confirms the three files agree |
| Release history | non-cosmetic `core` pack change | `docs/product/changelog.d/` fragment | implementing task | the release checker and the fragment | close-work confirms the fragment names the shipped version |
| User guides | none: the guides name `status --json` only to say it is run first, which stays true | none | none | none | none |
| Decision record | none: no decision is reversed or made | none | none | none | none |

## Agent Rules

### Always do

- Keep every refusal `code` and every exit code as it is today; only detail and hint text change.
- Write the failing test before the code for each behavior change.
- Say what a field must be, never what the controller sent.

### Ask first

- Adding any new verb, any new refusal code, or any new key other than `route` to a `status` or `next` answer.
- Any change to `review-artifact.py`.

### Never do

- Add `result_template`, `explain`, a per-code `remedy` field, a section index for `supervisor.md`, or an `ingest` command.
- Add a `## Not checked` footer to `adversarial-reviewer`; it would disqualify its reports from the clean fast path.
- Edit anything under `docs/specs/supervisor-self-describing-output/.supervisor/` or `delivery/`.

## Testing Strategy

- `--json`, `route`, `invalid-result` detail and the `Shipped` refusal text: TDD, exercised through `main(argv)` and `dispatch.py` on the supervisor test harness repository.
- Reference-file sentences: goal-based; a pin test asserts each sentence exists.
- Evals and release files: goal-based; a JSON load and the release checker.

## Acceptance Criteria

- [ ] **AC-0001.** Each `work-supervisor.py` verb (`park`, `gates`, `start`, `next`, `report`, `status`, `resolve-effect`) given `--json` prints the same stdout and exits with the same code as the same call without it.
- [ ] **AC-0002.** `status` output carries a `route` string, 160 characters or fewer, for each of these answers: a standing refusal (naming its `code` and `owner`), a terminal run, a retry count at the cap, non-empty `recovery_leftovers`, a pending regenerate step, an open `human-decision` request, and any other open request.
- [ ] **AC-0003.** A `route` contains no `detail` text from a refusal.
- [ ] **AC-0004.** `status --check` exits with the same codes as before `route` existed.
- [ ] **AC-0005.** `report` refuses with `invalid-result` and a detail naming the failing field when the result is not a JSON object, when `schema_version` is not the integer 1, or when `request_id`, `run_id` or `kind` is not a non-empty string; the detail states the required form and never repeats what was sent.
- [ ] **AC-0006.** `dispatch.py --start` or `--resume` on a `Shipped` spec refuses with code `impossible_transition` and a `next_action` that names starting a new spec and recording supersession in the old spec's Status line.
- [ ] **AC-0007.** Every other `impossible_transition` finding keeps its current `next_action`.
- [ ] **AC-0008.** `references/supervisor-mode.md` § Single-agent fallback states that an undispatchable mandatory reviewer is recorded `missing` and emits `BLOCKED`, and an undispatchable non-mandatory reviewer is a named skip.
- [ ] **AC-0009.** `references/supervisor.md` states that `--json` is accepted on every verb and defines `route`, and `state-schema.md` and `session-resumption.md` list `route` among the `status` keys.
- [ ] **AC-0010.** `evals/evals.json` carries one case whose prompt asks to start follow-up work on a `Shipped` spec and one whose prompt has an undispatchable reviewer role, each with unique `id` and assertions.
- [ ] **AC-0011.** The `core` version in `pack.toml` and `.claude-plugin/plugin.json` is one patch above the version `packs/core/pack.toml` carries at `git merge-base origin/main HEAD`, checked once before merge right after `git fetch origin` with the merge base equal to `origin/main`, and the changelog fragment and `_RELEASED["core"]` pin name it.

## Terminal Intent

`code` — ship the flag, the `route` key, the refusal wording, the reference sentences, the two eval cases, and the `core` patch release.

## Follow-ons

none

## Assumptions

- Technical: a `route` key on `status` does not break a caller that reads the answer by key — callers in this repository read named keys; none compares the whole object (settled by: the status tests).

## Closeout

Duties after the run reaches `terminal`; none is an acceptance criterion.

- Rebuild projections with `agentbundle catalogue self-host --root . --write --force` and commit them.
- Run the three `tools/` pin suites and both roster files named in the plan's Rollout.
- Set the spec `Shipped` and the plan `Done`, run `lint-spec-status.py`, open the PR with the four-question description.
