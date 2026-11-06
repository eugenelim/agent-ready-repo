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

A controller driving a full-mode run, on any model, gets the answer to its next question from the supervisor and the dispatcher themselves instead of from reading reference files. Five common stalls resolve in the output or in one pointer: a rejected `--json` flag, an `invalid-result` that names no field, a `status` or `next` answer that does not say what to do next, a refusal to start follow-up work on a `Shipped` spec, and a reviewer-fallback question that the section people search never answers.

## What Changes

- `--json` is accepted on every `work-supervisor.py` verb — `scripts/work-supervisor.py`
- Every `status` and `next` answer carries a one-line `route` naming the next action — `scripts/work-supervisor.py`
- The routing decision has one written home, a first-match table — `references/session-resumption.md`
- `invalid-result` from `report` names the field that failed — `scripts/_supervisor_loop.py`
- `dispatch.py` names the supported route when a named spec is `Shipped` or cooled — `scripts/dispatch.py`
- The single-agent fallback section points an undispatchable reviewer role at the existing reviewer rule — `references/supervisor-mode.md`
- The reference documents describe `--json` and `route` — `references/supervisor.md`, `references/state-schema.md`
- Two eval cases cover the `Shipped` route and the reviewer fallback — `evals/evals.json`
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

- Keep every refusal `code`, every exit code, and what each check accepts as it is today; only detail, hint text and one added key change.
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
- The routing table and reference sentences: goal-based; a pin test asserts the table rows and that each script `route` string equals its row.
- Evals and release files: goal-based; a JSON load and the release checker.

## Acceptance Criteria

- [ ] **AC-0001.** Each `work-supervisor.py` verb (`park`, `gates`, `start`, `next`, `report`, `status`, `resolve-effect`) given `--json` after the verb prints the same stdout and exits with the same code as the same call without it.
- [ ] **AC-0002.** Every `status` answer, on every output path, carries a `route` equal to the string the routing table in `references/session-resumption.md` gives for that answer's shape; the paths are the run view, a standing refusal, the `supervisor-changed` refusal (from the pin check and from the generic handler), the unsupported-ref-storage refusal, the invalid-policy refusal, the untrusted-unsafe-host refusal, and the Git, lock and internal-error refusals.
- [ ] **AC-0003.** On a `status` answer where `retry_count` and the retry cap can be read, a non-terminal run at or above the cap has the cap row's `route` even when a refusal stands, as `status --check` exits 3 for it.
- [ ] **AC-0004.** Every `next` answer, on every output path, carries a `route` equal to the string the routing table gives for that answer's shape: a refusal, a terminal answer, a `human-decision` request, or any other request.
- [ ] **AC-0005.** A `route` contains no `detail` text from a refusal and is 160 characters or fewer.
- [ ] **AC-0006.** `status --check` exits with the same codes as before `route` existed.
- [ ] **AC-0007.** `report` refuses with `invalid-result` and a detail naming the failing field when the result is not a JSON object, when `schema_version` is not equal to 1, or when `request_id`, `run_id` or `kind` is not a non-empty string; the detail states the required form and never repeats what was sent.
- [ ] **AC-0008.** `dispatch.py --start` or `--resume` on a `Shipped` spec, or on a spec whose lifecycle record has cooled, refuses with code `impossible_transition` and a `next_action` that says the spec is frozen without claiming a status the record does not establish, names starting a new spec, and names a decision record plus the `Shipped (superseded in part by ADR-NNNN — …)` form for the spec's Status line and the `Done (superseded in part by ADR-NNNN — …)` form for the plan's.
- [ ] **AC-0009.** Every `impossible_transition` finding that is not a `--start` or `--resume` refusal on a `Shipped` or cooled spec keeps its current `next_action`.
- [ ] **AC-0010.** `references/supervisor-mode.md` § Single-agent fallback sends an undispatchable reviewer role to the reviewer rule in `SKILL.md`, and restates no part of that rule.
- [ ] **AC-0011.** `references/session-resumption.md` holds the routing table as the one statement of the routing decision, with a first-match order and one row per `status` and `next` shape; `references/supervisor.md` states that `--json` goes after the verb on every verb and that `status` and `next` carry `route`; `references/state-schema.md` lists `route` among the `status` keys.
- [ ] **AC-0012.** `evals/evals.json` carries one case whose prompt asks to start follow-up work on a `Shipped` spec and one whose prompt has an undispatchable reviewer role, each with a unique `id` and assertions.
- [ ] **AC-0013.** The `core` version in `pack.toml` and `.claude-plugin/plugin.json` is one patch above the version `packs/core/pack.toml` carries at `git merge-base origin/main HEAD`, and the changelog fragment and `_RELEASED["core"]` pin name it.

## Terminal Intent

`code` — ship the flag, the `route` key and its table, the refusal wording, the reference sentences, the two eval cases, and the `core` patch release.

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
