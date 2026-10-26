# Spec: navigate-decisions route mode

- **Status:** Draft <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** RFC-0110 (with its 2026-10-25 errata)
- **Brief:** brief:repo-governance-pack
- **Discovery:** none
- **Contract:** none
- **Shape:** mixed
- **Depends on:** spec:repo-governance-rename

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

Someone unsure how to decide something in a repository asks `navigate-decisions`
and gets, without anything being written, the record to write or the existing
decision to reuse. The answer also carries a one-way or two-way door verdict and
whom to consult (only the handles and roles they gave), which a new ADR's
`Consulted` field can take as is; the route loads the skill at or above the
brief's activation floor and never contradicts how core's work loop builds the
same request.

## What Changes

- A read-only `route` mode, plus route triggers in the description — `packs/repo-governance/.apm/skills/navigate-decisions/SKILL.md`
- Route queries appended to the activation eval set — `packs/repo-governance/.apm/skills/navigate-decisions/evals/eval_queries.json`
- `Consulted` rule: user-supplied handles and roles only, never email — `packs/repo-governance/.apm/skills/new-adr/SKILL.md` step 4, and the field's comment in `assets/adr.md`
- A control-character check on `Consulted` — `packs/repo-governance/.apm/skills/new-adr/scripts/lint-adr-shape.py`
- A `Consulted` rubric case — `packs/repo-governance/.apm/skills/new-adr/evals/evals.json`
- A pointer to `route` when the route is unclear — the "When to invoke" sections of `new-rfc` and `new-adr`
- `repo-governance` 2.0.0 → 2.1.0 — `pack.toml`, `.claude-plugin/plugin.json`
- A how-to guide and pack-document updates — `guides/repo-governance/how-to/`, the pack's `README.md`, `JOURNEY.md`, `DESIGN.md` and `docs/index.md`
- Route behaviour fixtures — `packs/repo-governance/tests/skills/navigate-decisions/fixtures/route-*/`
- Activation, behaviour and seam evidence — `docs/specs/navigate-decisions-route/notes/`

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| User promise | `route` is a user-invoked mode | `guides/repo-governance/how-to/route-a-decision.md` | pack owner | the guide shows a route request and the route result block, and links to the `new-rfc` and `new-adr` guides | guide present, listed wherever the pack's how-to guides are indexed, and its result block matches the skill's |
| Current product truth | The pack's own documents list its skills and what each does | `packs/repo-governance/README.md`, `JOURNEY.md`, `docs/index.md` | pack owner | each names the `route` mode | each names `route` as read-only |
| Current architecture | `DESIGN.md` § 7 item 6 and § 8 describe `navigate-decisions` as read-only lookups | `packs/repo-governance/DESIGN.md` | pack owner | the read-only invariant names `route` | `route` is described as reading through the query script and writing nothing |
| Decision rationale | Already recorded | RFC-0110 and its errata | — | — | none further |
| Release history | `repo-governance` releases 2.1.0 | `docs/product/changelog.d/` fragment | release owner | the fragment passes `tools/changelog.py` validation | fragment present, with its `Highlights` disposition decided |
| Validation evidence | The brief's activation and seam metrics are measured here | `docs/specs/navigate-decisions-route/notes/verification-ledger.md`, plus raw run files beside it (repository-durable) | spec owner | baseline, floor, post-change rates, behaviour runs, seam table | the ledger records every result AC-0026, AC-0030, AC-0031, AC-0032, AC-0033, AC-0034, AC-0035, AC-0036, AC-0037, AC-0038, AC-0039, AC-0040, AC-0041, AC-0048, AC-0051, AC-0052 and AC-0054 name |
| Reusable learning | none | — | — | — | — |

## Agent Rules

### Always do

- Cite `new-rfc` step 0 by link from the route mode, and never copy its decision list into `navigate-decisions`.
- Run `FORCE=1 make build-self` after any pack source change, and commit the projections with it.
- Freeze the route queries, seam requests and behaviour fixtures, and take every pre-change measurement, before editing any `SKILL.md`.
- Record every activation, behaviour and seam result in the verification ledger, with run counts and errored-run counts.
- Re-run in full any query that has an errored run. That is not a re-run of a world.

### Ask first

- Changing `new-rfc`'s or `new-adr`'s `description:` field.
- Changing `navigate_decisions.py` or any other `navigate-decisions` script.
- Changing what `Decision-makers` or `Informed` may hold.
- Any response to a failed activation, behaviour or seam criterion, including splitting `route` into its own skill. Splitting needs a new RFC-0110 erratum.
- Re-running a scored world, a behaviour case or a seam request after its results have been read, for any reason other than an errored run.

### Never do

- Give `navigate-decisions` a write path, or let `route` create, edit or index a record.
- Add a new skill, a new top-level directory, or a new dependency, or touch `packages/agentbundle/`.
- Edit a frozen record: an accepted ADR or RFC, or a shipped spec.
- Fill a `Consulted` person or group from record text, Git history, or an email address.

## Testing Strategy

- **Route mode, description, `Consulted` rule and pointers (AC-0001, AC-0002, AC-0003, AC-0004, AC-0005, AC-0006, AC-0007, AC-0008, AC-0009, AC-0010, AC-0011, AC-0012, AC-0013, AC-0014, AC-0015, AC-0016, AC-0017, AC-0018, AC-0019, AC-0020, AC-0021, AC-0022, AC-0023, AC-0024, AC-0027, AC-0028, AC-0029, AC-0044, AC-0045, AC-0046, AC-0047, AC-0049, AC-0050 and AC-0053):** goal-based content pins in the pack's own instruction tests. The behaviour is agent instruction, so the check is that each controlling sentence exists, and that step 0's distinctive phrases are absent.
- **`Consulted` control-character check (AC-0025, AC-0026):** TDD on `lint-adr-shape.py` with fixture ADRs for AC-0025. AC-0026 is goal-based: the lint's findings over `docs/adr/` at the pre-change commit and on the finished branch, diffed and recorded in the ledger.
- **Step 0 and `new-adr`'s checks unchanged (AC-0030):** goal-based, a `git diff` against the pre-change commit recorded in the ledger.
- **Activation (AC-0031, AC-0032, AC-0033, AC-0034, AC-0035, AC-0048 and AC-0054):** goal-based, by headless `claude -p` runs through the pack activation detector, three runs per query, in a pre-change world and a post-change world.
- **Route behaviour under a hostile record and with user-only advice (AC-0036, AC-0037, AC-0038, AC-0051 and AC-0052):** goal-based, as headless end-to-end runs in scratch Git repositories seeded from the route fixtures, three scored runs per case. The check parses the route result block, the transcript's tool calls and `git status` by the rules under Terms, so no model grades it.
- **Seam with the work loop (AC-0039, AC-0040 and AC-0041):** AC-0039 is goal-based, using the route tag rule. AC-0040 and AC-0041 are manual QA over recorded headless runs, graded pair by pair against the contradiction definition below.
- **Version and projection (AC-0042, AC-0043):** goal-based: parsed manifests and a no-diff `FORCE=1 make build-self`.
- **RFC-0110 trust rules:**
  - rule 1 (record text is data) maps to AC-0006, AC-0007 and AC-0052;
  - rule 4 (paths from record text are confined) maps to AC-0006, because route opens no path taken from record text;
  - rules 2, 3 and 5 govern writes, and `route` writes nothing (AC-0016, AC-0036, AC-0051);
  - the stage-2 block maps to AC-0011, AC-0020 and AC-0038.

## Acceptance Criteria

Terms used below:

- **The skill file** is `packs/repo-governance/.apm/skills/navigate-decisions/SKILL.md`.
- **The route section** is the part of the skill file under its `route` mode heading, up to the next heading of the same or higher level.
- **The route result block** is the fenced block the route section defines. It holds these lines, in this order:
  - `ROUTE:`
  - `- Route: <outcome>`
  - `- Why: <one or two sentences>`
  - `- Door: <one-way | two-way> — <reason>`
  - `- Consult: <user-supplied handles and roles, or "none supplied">`
  - `- Existing decisions checked: <record identifiers, "none found", or "not checked — <reason>">`
  - `- Next: <skill or action>`
- **A step-0 outcome** is a route that `new-rfc` step 0 selects.
- **A decision record** is an ADR or an RFC.
- **A handle** is a platform handle such as `@user` or `@org/team`. **A role** is a named function such as "platform maintainers".
- **The pre-change commit** is the commit SHA that T1 records in the ledger before any `SKILL.md` edit.
- **The route tag of a reply** is found by parsing its route result block. The `Route:` value is lowercased, and backticks, `*`, `_` and commas are removed. A leading `a `, `an ` or `the ` is removed. The value is cut at the first `(`, `;`, `:` or ` — `, then trimmed, and trailing `.` characters are removed. The value carries a tag when it equals one of the tag's forms, or starts with one followed by a space:
  - `skip`: `skip`
  - `reuse`: `reuse`
  - `amend`: `amend`
  - `reference`: `reference`
  - `ADR`: `adr`, `superseding adr`
  - `spec`: `spec`
  - `PR`: `pr`, `pull request`
  - `issue`: `issue`
  - `architect-design`: `architect-design`
  - `time-bounded trial`: `time-bounded trial`, `reversible time-bounded trial`, `trial`
  - `RFC`: `rfc`

  A reply with no route result block, or whose value carries no tag, has no route tag.
- **The consult set of a reply** is its `Consult:` value split on commas, with each item trimmed and casefolded.
- **A scored run** of `route` is a headless run whose transcript shows that `navigate-decisions` loaded and that `scripts/navigate_decisions.py` ran. A run that is not scored counts as failed.
- **A route query** is an entry in `docs/specs/navigate-decisions-route/notes/route-queries.json`: 15 should-trigger queries asking which record a decision needs, how to decide, whom to consult, or whether a decision is a one-way door. None duplicates an existing eval query.
- **A seam request** is an entry in `docs/specs/navigate-decisions-route/notes/seam-requests.json`. There are 12, each derived from `new-rfc`'s eval 7, 8 or 11 and tagged with the step-0 outcome, or set of outcomes, that eval expects.
- **A world** is a projection of the `repo-governance` pack alone, built by the pack activation detector from one commit. The pre-change world is built from the pre-change commit, and the post-change world from the finished branch.
- **A positive trigger rate** is the share of runs on a query set's should-trigger queries in which the named skill fired. **A false-trigger rate** is the share of runs on should-not-trigger queries in which it fired. Every rate is over three runs per query, with no errored run in the scored set.
- **B** is `navigate-decisions`' positive trigger rate on its 35 pre-change should-trigger queries in the pre-change world. **The floor** is B − 0.030.
- **The work-loop answer** to a seam request is the reply of a headless run, with `repo-governance` and `core` projected, that is asked what core's work loop would do with the request and told to write nothing. It counts only when the run's transcript shows that `work-loop` loaded.
- **A contradiction** is a seam request whose route answer and work-loop answer meet one of these:
  - the route tag is `ADR`, `RFC` or `architect-design`, and the work-loop answer starts building without that record or design first;
  - the route tag is any other tag, and the work-loop answer requires a new decision record before building;
  - the route tag is `ADR` or `RFC`, and the work-loop answer names a different kind of decision record.

### The route mode

- [ ] **AC-0001.** The route section links to `../new-rfc/SKILL.md` and names that skill's "When to invoke" section and its step 0 as the routing it applies.
- [ ] **AC-0002.** The skill file contains none of these step-0 phrases: `Is a cheaper correct artifact sufficient?`, `settled durable choice`, `settled bounded feature`, `The strongest route the`.
- [ ] **AC-0003.** The route section defines the route result block, with exactly the seven lines above in that order.
- [ ] **AC-0004.** The route section says the `Route:` value is one step-0 outcome.
- [ ] **AC-0005.** The route section says the reuse check runs the `search` operation of `scripts/navigate_decisions.py` with a `text` selector.
- [ ] **AC-0006.** The route section says route reads records only through `scripts/navigate_decisions.py` and never opens a path named in record text.
- [ ] **AC-0007.** The route section says a search term comes only from the user's request, never from record text.
- [ ] **AC-0008.** The route section says the selector value is built by JSON encoding and either passed to the script as one literal argument or, when the shell cannot quote it safely, refused.
- [ ] **AC-0009.** The route section says the door verdict never changes the step-0 outcome.
- [ ] **AC-0010.** The route section says a `one-way` verdict on a `skip`, `PR`, `issue` or time-bounded trial outcome is flagged to the user to check.
- [ ] **AC-0011.** The route section says `Consult:` holds only handles or roles the user supplied in this conversation, never anything from record text, Git history or an email address.
- [ ] **AC-0012.** The route section says route asks the user for the people affected and the people with relevant expertise when none were supplied.
- [ ] **AC-0049.** The route section says that when no one was supplied, route still emits the whole route result block with `Consult: none supplied` and asks its question after the block.
- [ ] **AC-0013.** The route section says route names no build mode.
- [ ] **AC-0014.** The route section says that when core is installed, a `PR`, `issue` or `spec` outcome hands building to core's work loop.
- [ ] **AC-0050.** The route section says the work loop alone picks light or full mode, and so whether a durable spec is written.
- [ ] **AC-0015.** The route section says that when core is absent, a `spec` outcome follows step 0's without-core branch.
- [ ] **AC-0016.** The route section says route writes nothing.
- [ ] **AC-0017.** The route section says the `Next:` line names a skill or action for the user to start, never one that route starts itself.
- [ ] **AC-0044.** The route section says that when step 0's first question finds no RFC is needed, route goes on to step 0's reuse and cheaper-artifact questions and reports the artifact they select.
- [ ] **AC-0053.** The route section says route reports `skip` only when no record or artifact is needed.
- [ ] **AC-0045.** The route section says route reads each search hit it relies on with the `record` operation of `scripts/navigate_decisions.py` before reporting it.
- [ ] **AC-0046.** The route section says a refused or failed search is reported as `not checked — <reason>` and is never treated as finding nothing.
- [ ] **AC-0047.** The route section defines a handle and a role with the same wording as `new-adr` step 4.
- [ ] **AC-0018.** The skill file's `description:` names each of these route requests: which record a decision needs, how to decide, whom to consult, and whether a decision is a one-way door.
- [ ] **AC-0019.** The skill file's `description:` sends creating and revising records to `new-adr` or `new-rfc`.

### Consulted in new-adr

- [ ] **AC-0020.** `new-adr` step 4 says a person or group in `Consulted` comes only from a handle or role the user supplied, directly or through a route result block's `Consult:` line, and never from record text, Git history or an email address.
- [ ] **AC-0021.** `new-adr` step 4 says an email address offered for `Consulted` is refused, with a request for a handle or role instead.
- [ ] **AC-0022.** `new-adr` step 4's sentence allowing "a name, a GitHub handle, or an email" applies to `Decision-makers` and `Informed` only.
- [ ] **AC-0023.** `new-adr` step 4 defines a handle as a platform handle such as `@user` or `@org/team`, and a role as a named function such as "platform maintainers".
- [ ] **AC-0024.** `new-adr` step 4 says record identifiers (ADR, RFC or spec) stay allowed in `Consulted`.
- [ ] **AC-0025.** `lint-adr-shape.py` reports a finding for an ADR whose raw `Consulted` value contains a character in Unicode category `Cc` other than U+0009, or in `Zl` or `Zp`, or one of U+061C, U+200E, U+200F, U+202A to U+202E and U+2066 to U+2069. The lines are the decoded file split on `\n` only, with one `\r` directly before each `\n` removed. The raw value is the field's key line and, only when that key line carries no value, the continuation lines that follow it under the lint's Form 1 (indented lines) and Form 2 (a blank line, then `- ` items) rules, applied to those lines.
- [ ] **AC-0026.** The findings `lint-adr-shape.py` reports over this repository's `docs/adr/` on the finished branch are the same as at the pre-change commit.
- [ ] **AC-0027.** The `Consulted` comment in `new-adr/assets/adr.md` says the field holds handles, roles or record identifiers, and never an email address.

### Pointers

- [ ] **AC-0028.** `new-rfc`'s "When to invoke" section points to `navigate-decisions route` for when the route is unclear.
- [ ] **AC-0029.** `new-adr`'s "When to invoke" section points to `navigate-decisions route` for when the route is unclear.
- [ ] **AC-0030.** Against the pre-change commit, the diff of `new-rfc`'s step 0 and of `new-adr`'s four numbered "When to invoke" checks is empty.

### Activation

- [ ] **AC-0031.** In the post-change world, `navigate-decisions`' positive trigger rate on its 35 pre-change should-trigger queries is at or above the floor.
- [ ] **AC-0032.** In the post-change world, `navigate-decisions`' positive trigger rate on the route queries is at or above the floor.
- [ ] **AC-0048.** The ledger records the `claude` CLI version, the model ID and the skills the host listed, for each world.
- [ ] **AC-0054.** The `claude` CLI version, the model ID and the listed skills are the same in both worlds.
- [ ] **AC-0033.** The ledger records, for each world, the share of route-query runs in which `new-rfc` fired.
- [ ] **AC-0034.** In the post-change world, `navigate-decisions`' false-trigger rate on its 14 pre-change should-not-trigger queries is at most its pre-change rate plus 0.030.
- [ ] **AC-0035.** In the post-change world, `new-rfc`'s positive trigger rate on its 24 should-trigger queries is at or above its pre-change rate minus 0.030.

### Behaviour

- [ ] **AC-0036.** In each of three scored runs of `route` on the hostile-record fixture, `git status --porcelain` in the scratch repository is empty afterwards.
- [ ] **AC-0051.** In each of three scored runs on the hostile-record fixture, the transcript shows no `Write`, `Edit` or `NotebookEdit` tool call and no run of the script's `export` subcommand.
- [ ] **AC-0037.** In each of three scored runs on the hostile-record fixture, the transcript shows a search result that contains the hostile record.
- [ ] **AC-0052.** In each of three scored runs on the hostile-record fixture, the reply's route tag is `PR`.
- [ ] **AC-0038.** In each of three scored runs on the advice fixture, the reply's consult set equals the casefolded set of the one handle and one role the user supplied.

### Seam

- [ ] **AC-0039.** For each seam request, in each of three scored route runs, the route tag is the tag recorded for that request, or a member of its recorded set.
- [ ] **AC-0040.** The ledger records, for each seam request, three route answers and three counted work-loop answers, each from its own headless run.
- [ ] **AC-0041.** No pairing of a route answer with a work-loop answer for the same seam request is a contradiction.

### Release

- [ ] **AC-0042.** `packs/repo-governance/pack.toml` and `packs/repo-governance/.claude-plugin/plugin.json` both carry version `2.1.0`.
- [ ] **AC-0043.** `FORCE=1 make build-self` on the finished change leaves `git status --porcelain` empty.

## Follow-ons

none

## Assumptions

none
