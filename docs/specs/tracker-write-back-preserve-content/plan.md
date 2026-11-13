# Plan: Tracker write-back preserves existing content

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done <!-- Drafting | Approved | Executing | Done -->
- **Repository anchors:** the Jira client's guarded-write seam (`packs/atlassian/.apm/skills/jira/scripts/_client.py`, `_guarded_write_matches`) and the `jira-refresh` processor that uses it; the Jira and Jira Align test folders under `packs/atlassian/tests/skills/`; the closed capability lists in the Linear and GitHub `refresh-profile.json` files. Named uncertainty: the two skills each ship their own `scripts/`, so shared code is a byte-identical copy rather than an import.

> **Plan contract:** this is the implementation strategy. After approval, a
> change needs an **amendment** only when it touches the spec's protected
> sections (contract, scope and non-goals, durable outputs, agent rules, testing
> strategy, acceptance criteria, accepted risk) or its `Terminal Intent`. A change
> to tasks, tests, stubs, design, or approach needs none: the controller makes it
> as an in-envelope working-plan change while no execution attempt is open, and
> the run continues with every finished task still finished. Execution
> observations belong in `docs/specs/<feature>/notes/verification-ledger.md` (or
> the adopter's equivalent). A genuine error in a protected section follows the
> controlled-amendment path.
>
> **Not every field is contract.** `Touches`, `Tests` and `Done when` are what a
> completion gate reads. `Design`, `Approach`, `Grounding` and `Risks` are working
> material the controller corrects in place, before or after approval, while no
> attempt is open. After approval, grounding for a seam or design means recorded
> as `implementation-discovered`, and each later correction, is a controller edit
> of the plan's `## Design (LLD)`, never a ledger line; a settled design decision
> that execution falsified is a plan error the owner agrees to, corrected the same
> way unless it reaches a protected section. A TDD task's `stub` fence is likewise
> written by the controller at task start, not carried in the approved plan.
> Treating working material as contract is how a review spends a round on prose
> no gate consumes — the measured share is over half the plan's lines. `Grounding` stays *recorded*,
> because a per-task resolution that nobody wrote is not grounding; what it stops
> being is a claim a reviewer holds the plan to.

<!-- Existing plans without this field remain valid. Treat its absence as a
named assurance gap during structural review, not a universal lint failure. -->

<!-- **Durable-plan fill.** This template is the implementation and verification
strategy for a durable delivery slice. Fill Approach, Constraints, Risks,
Design, Tasks, and Changelog to the depth the durable work requires. Its sibling
spec is the durable behavior contract. Eligible direct-light work does not
create this artifact. -->

## Approach

One small module implements the preserve-first write: build a plan from the current values, hash it, and on write recompute the hash, re-read, compare, save the prior value, and send the plan's resolved body. Jira and Jira Align each ship an identical copy, because installed skills cannot import from each other. The guard sits in each client at the `_request` chokepoint the repository already uses for guarded writes, so the CLI commands, `raw`, `transition`, and any direct caller reach it. The guard is deny-by-default: every non-GET request refuses unless it is on the spec's closed allowlist or carries a verified plan. The riskiest part is Jira Cloud's ADF, so append and lossy detection walk the document tree. Linear and GitHub need no code guard; a test pins their write capabilities.

Survey: [`docs/product/research/tracker-write-back-survey.md`](../../product/research/tracker-write-back-survey.md).

## Constraints

- The Jira SSO-cookie path stays read-only for writes (`jira-refresh` SKILL, work-intake refresh § remote write-back); the auth check runs before the guard's re-read.
- Tracker content is untrusted data; a plan never takes a host, path, or command from it.
- Plan and prior-value files hold tracker text and live under the per-user `~/.agentbundle/tracker-write-back/`, outside every repository, the way the credential store does.
- Shipped skill text states rules directly and cites no repository-internal record (`packs/AGENTS.md`, Shipped pack content).
- Versions follow `packs/AGENTS.md` § Version bump rule; changelog fragments follow `packs/AGENTS.local.md`.

## Construction tests

**Integration tests:** one fake-transport test per skill drives `plan-update` then `update-issue` / `update` end to end and asserts the recorded request list.

**Manual verification:** T6 runs the real CLI against a mocked transport for one Jira Cloud, one Jira Server, and one Jira Align record and pastes the preview, stale refusal, and undo output into the PR.

## Durable-output map

| Durable output | Tasks | Implementation evidence | Closeout evidence |
| --- | --- | --- | --- |
| Tracker guides refreshed | T7 | guide diffs, link check | each guide read whole and updated |
| Skill command tables | T5 | skill lint, table test | tables list the new commands and the guard exit code |
| Changelog fragments | T7 | `tools/changelog.py` validation | three fragments with the Highlights decision |
| Survey cited | T7 | plan link resolves | link check |

## Design (LLD)

### Design decisions

- The stale check compares the values of the named fields, not `updated`. No tracker offers a precondition on update, and `updated` also moves on unrelated edits.
- The plan digest is the SHA-256 of canonical JSON over the fields AC3 lists; the write recomputes it from the plan file and compares it to `--approved-digest`.
- The write body is built from the plan's resolved values only; `--field` and `--data-file` content is not merged in at write time.
- Dispositions: `keep` drops the field; `append` adds a labelled block after existing text; `replace` writes the proposed value. A merge is a `replace` drafted from the plan's current value and guarded by the stale check. `append` is defined for text fields only.
- Undo is a plan: `plan-undo` reads a saved record and emits a plan with `replace`, so the same approval and stale check apply.
- The guard code is 10, outside the credential and auth band 3 to 9 and distinct from 2, which sends the agent to credential setup.

### Data & schema

- Plan file: `~/.agentbundle/tracker-write-back/<instance-slug>/plans/<key>-<digest prefix>[-n].json`; the closed field set is stated in AC20. `base_url` only binds the approval and never builds a request.
- Prior-value record: `~/.agentbundle/tracker-write-back/<instance-slug>/prior/<timestamp>-<key>.json`, one record per write holding `entries` (field, old value, written value), created in folders AC18 governs.
- Windows: modes are no-ops, so privacy there rests on the per-user profile ACL plus reparse-point refusal, recorded as a named gap.

### Interfaces & contracts

- `plan-update KEY --field NAME=VALUE --disposition NAME=keep|append|replace`, read-only. Jira Align takes `RESOURCE ID`.
- `update-issue` / `update` take `--plan FILE --approved-digest HEX`; `plan-undo --record FILE`; Jira Align `update` adds `--replace-record`.

### Component / module decomposition

- `_preserve_write.py` in `jira/scripts/` and `jira-align/scripts/`, byte-identical, holding digest, dispositions, ADF walk, route matcher, plan and record I/O. A parity test fails when the copies differ.
- Client change: the non-GET path in each `_request` consults the route matcher and requires a verified plan token for guarded routes.

### Behavior & rules

- ADF append adds a labelled paragraph and the proposed nodes at the end of `doc.content`; Server/DC append concatenates after a blank line and the same label.
- The lossy check collects node types and mark types in the current and proposed documents; AC26 owns the exempt set.
- The matcher resolves the request path, refuses any path that still holds `..`, `;`, or an encoded separator, refuses method-override headers and other hosts, strips the API prefix, and compares method, path template, and (for the transition entry) the body against the spec's allowlist; anything else needs a verified plan, and a verified plan authorizes only the request it resolves to. The guard runs after the existing SSO-cookie, intake-policy, and receipt checks. Deletes are not on the allowlist: the client's delete method takes a confirmation the CLI sets from `--yes`, and any other `DELETE` is refused. A transition with field content is refused before the name lookup sends anything.

### Failure, edge cases & resilience

- A failed prior-value write sends nothing. A failed remote write leaves the record on disk; the failure message points back to the path already printed.
- A stale plan is refused; the person reruns `plan-update`. A small race remains between the final read and the write, and the refusal message says so.
- Jira Align `PATCH` can change unnamed fields; the post-write re-read reports them and the full-record copy allows manual restore.

### Dependencies & integration

- Standard library only. `implementation-discovered`: how each CLI resolves the home folder on Windows. Files are created exclusively, without following symlinks, under the user folder. The repository's confined-write helper lives in `agentbundle` and cannot be imported from an installed skill, so the module copies its behaviour: exclusive create, no symlink component, containment under the root.

## Tasks

### T1: Shared module tests pass and both copies are byte-identical

**Verification mode:** TDD, at the module boundary.

**Depends on:** none

**Tests:**
- Digest stability and recomputation, including an edited plan with an unchanged stored digest (AC3, AC7, AC6).
- Plan-to-request binding by method, absolute URL, and body (AC8); one non-GET request with the resolved body only (AC9, AC10).
- Output encoding of every tracker-text channel and the single `digest:` line (AC4, AC5).
- ADF, string, and Jira Align append; lossy refusal, pass, and report; non-text `append` refusal (AC23, AC24, AC25, AC26, AC27, AC28, AC29).
- Route matcher over the deny path forms, the origin and header checks, no redirect following, transition bodies, confirmed delete, and allowlisted writes (AC30, AC33, AC34, AC32, AC31, AC35).
- Record creation order, failure, contents, home, slug, channels, and path print (AC12, AC13, AC14, AC15, AC16, AC21, AC22).
- File handling: exclusive create and mode, folder ownership and mode for new and pre-existing folders, symlink and reparse refusal (AC17, AC18, AC19); a plan-file name clash gets a unique suffix without loosening exclusive create.
- Plan and record loaders: closed field sets, types, identifier alphabet, base URL match, confinement (AC20).
- Parity test fails when the two copies differ.

**Done when:** the T1 tests are green under `python3 -m pytest packs/atlassian/tests/skills/jira packs/atlassian/tests/skills/jira-align -q`.

### T2: Jira client and CLI enforce the guard

**Verification mode:** TDD, at the client and the CLI against a recording fake transport.

**Depends on:** T1

**Tests:**
- AC1, AC2, AC3, AC6, AC7, AC8, AC9, AC10, AC11, AC12, AC13, AC21, AC22, AC17, AC18, AC19, AC20, AC30, AC31, AC32, AC33, AC34, AC35 on the Jira client and CLI, including direct `update_issue`, `raw`, comment edit, and `transition --name X --field ...` asserting zero recorded requests, the lookup included.
- SSO-cookie client: every command in AC36 sends nothing, with the transition lookup behind the auth check and `raw GET` still sent; AC37 for the Jira receipt refusal; AC38.
- `plan-undo` round trip and stale refusal (AC43, AC44).

**Done when:** the T2 tests are green.

### T3: Jira Align client and CLI enforce the guard and record the method in the plan

**Verification mode:** TDD, at the client and the CLI against a recording fake transport.

**Depends on:** T1

**Tests:**
- The Jira Align cases of AC1, AC2, AC3, AC6, AC7, AC8, AC9, AC10, AC11, AC12, AC13, AC21, AC22, AC17, AC18, AC19, AC20, AC30, AC31, AC33, AC34, AC35, with the allowlisted create matched on a single path segment only.
- The Jira Align intake-policy refusal still fires first (AC37).
- `PATCH` recorded by default, `PUT` plus the omitted-field list with `--replace-record` (AC39); the write sends the plan's method and the `--method` flag is gone (AC40); undo (AC43, AC44).
- Full-record prior copy and post-write drift report (AC41, AC42).

**Done when:** the T3 tests are green.

### T4: Linear and GitHub write capabilities stay closed

**Verification mode:** TDD, over each profile and a recording fake transport, plus an eval case per pack.

**Depends on:** none

**Tests:**
- Capability allowlists, leaving out `acquire` (AC48).
- Recorded GraphQL variables (Linear) and recorded command arguments (GitHub) show no issue or pull-request title, description, or body write (AC49).
- The description-rewrite eval case in each pack expects the comment route (AC47).

**Done when:** the T4 tests are green.

### T5: Skills, evals, examples, and command tables describe and exercise the flow

**Verification mode:** goal-based, through skill lint, a text test over the changed skills, and the eval harness.

**Depends on:** T2, T3

**Tests:**
- A text test over the changed skills' `SKILL.md`, examples, and evals finds no `update-issue` or `update` call without `--plan` (AC45).
- Text pins with no criterion of their own: both command tables name guard code 10 with the action to take and state that `transition` with field content is always refused; `jira-story-triage` and `jira-team-status` name `plan-update` before any write and `plan-undo` as the recovery, and "There is no undo" is gone; the triage partial-failure retry text becomes a re-plan.
- The `jira-story-triage` adversarial-field eval case (AC46); the same case also checks the Always-do rule to ask the disposition for each non-empty text field and the Ask-first questions for `replace` over existing text and for `--allow-lossy`.
- Skill lint clean (AC50).

**Done when:** skill lint and the T5 tests are green.

### T6: Manual QA through the real CLI is recorded

**Verification mode:** visual / manual QA.

**Depends on:** T2, T3

**Tests:**
- The Jira Cloud, Jira Server, and Jira Align runs from § Construction tests, with preview, stale refusal, and undo output recorded in the verification ledger.

**Done when:** the ledger holds the three observed runs.

### T7: Guides, fragments, and versions land and the repository gate is green

**Verification mode:** goal-based.

**Depends on:** T4, T5, T6, T6a

**Tests:**
- Guides read whole and updated, including how to clean `~/.agentbundle/tracker-write-back/`; link check clean.
- Versions bumped (AC51); `python3 tools/changelog.py` validation clean for the three fragments.
- Home resolution is tested under both install scopes, resolving the way the credential store resolves it (AC15).

**Done when:** `make lint-ruff lint-mypy; make precheck PRECHECK_ARGS="--with-tests --base origin/main"` and `make build-self` exit 0.

### T6a: The preview shows the exact value each field will hold

**Verification mode:** TDD, at the CLI against the recording fake transports, then a rerun of the T6 manual QA driver.

**Depends on:** T2, T3

**Tests:**
- For an `append`, `plan-update` prints the value the field will hold after the write: the current value, the label the write adds, and the proposed value, for Jira Cloud (ADF), Jira Server/Data Center, and Jira Align. A person approving the digest has seen the exact written value.
- The dropped-type report prints under the field it concerns and only for ADF fields; a plain string field prints none.
- The Jira Align omitted-field list leaves out the record's identifier field.
- The preview still prints exactly one `digest:` line and the existing `plan-update` tests stay green.

**Done when:** the T6a tests are green and the T6 QA driver reruns with exit 0.

### T8: Review repairs: every supported material review finding is fixed and pinned

**Verification mode:** TDD, at the client and CLI against the recording fake transports, plus goal-based checks for the CI wiring and skill text.

**Depends on:** T7

**Tests:**
- Transition names read from the tracker are encoded in the no-such-transition error (AC4), checked through the CLI's stderr with control and bidirectional characters in a name.
- A Jira Align `PUT` plan carries every other field of the record as read as a `keep` entry, so the digest covers them, the apply-time stale check re-reads them, and a field changed after the preview makes `update` exit 10 with zero write requests (AC11, AC39, AC43); the preview still lists the omitted fields, now including the record identifier with a note that it is the record's identifier (AC39).
- The owner and mode check of every folder from the tracker-write-back root down, including `plans/` and the instance folder, runs after the plan loads and before the first request, so a loosened folder exits 10 with zero requests of any method (AC18); the existing check before the write stays.
- A failed write or a failed re-read points back to the record path already printed instead of printing it again (AC22), asserted by counting every occurrence of the path on stderr.
- `update-issue` and `update` print exactly one `digest:` line, the recomputed plan digest, on every refusal that happens after the plan file loads (AC5); the tests that pinned zero lines now pin one. Refusals before a plan exists (an unreadable path, an argument error) have no plan digest to print and are the one stated limit.
- The new guard, parity, and skill-text suites run in a pull-request check the way the repository already wires its SSO write-refusal suites, and the CI parity table classifies them as gated.
- The `jira`, `jira-align`, and `jira-story-triage` skill text and the Atlassian guide no longer tell the agent to show a preview of an undo plan, because `plan-undo` prints only the plan path and digest; they say to ask for approval of the saved values' restore with the digest and not to print the plan file. The text pins follow.

**Done when:** the T8 tests are green, the lint and CI-parity checks pass, and the T6 QA driver reruns with exit 0.

### T9: Second review repairs: the PUT stale check covers every record key, the folder preflight covers the plan's own folders, and the digest coverage is pinned

**Verification mode:** TDD, at the CLI against the recording fake transports, with mutation checks run by hand and reported.

**Depends on:** T8

**Tests:**
- A Jira Align `PUT` plan refuses at apply time when the record as re-read holds any key the plan does not list, with exit 10, zero write requests, and a message naming each uncovered key encoded; a key that appears after the preview and a key present at preview but changed both refuse; an unchanged record still writes only the named fields (AC11, AC39).
- The owner, mode and link preflight also checks every folder between the tracker-write-back root and the plan file's own folder, so a plan kept in a loosened folder under the root exits 10 with zero requests and no file written, in both CLIs (AC18).
- The digest covers `keep` entries: a test edits a keep entry's `current` in a stored plan and expects the verification refusal; a second test changes only a keep entry in `build_plan` input and expects a different digest; and the hand-run mutation (the digest skipping `keep` entries) turns at least two tests red, which the report states (AC3, AC7, AC11, AC39).

**Done when:** the T9 tests are green, the existing suites stay green, the lint and CI-parity checks pass, and the T6 QA driver reruns with exit 0.

### T10: Third review repairs: the stale check compares JSON values exactly, and plan-undo checks the record's folders

**Verification mode:** TDD, at the shared module and the CLI against the recording fake transports.

**Depends on:** T9

**Tests:**
- The stale check treats two values as equal only when their canonical JSON forms are equal, so a value that changed JSON type (`1` to `true`, `3` to `3.0`, an integer to a float identifier, a nested number to a nested boolean) makes `update-issue` and `update` exit 10 with zero write requests, for named fields and for `--replace-record` keep entries alike; values that really are equal still pass (AC11).
- `plan-undo` runs the same owner, mode and link preflight on every folder from the tracker-write-back root down to the record's own folder before it reads the record, in both CLIs, so a record in a loosened folder, a loosened sibling instance folder, or a symlinked ancestor exits 10 and writes no plan file; a record in the normal prior folder still produces its plan (AC18, AC21, AC43).

**Done when:** the T10 tests are green (each shown red against the old code first), the existing suites stay green, and the lint, parity and QA-driver checks pass.

### T11: Fourth review repair: the shipped text gives the right remedy for a folder refusal

**Verification mode:** goal-based, through the text pins in the skill-text suite and skill lint.

**Depends on:** T10

**Tests:**
- The exit-10 row of the `jira` and `jira-align` command tables, and the Atlassian guide's refusals paragraph and the folder sentence in the write-back guide, name a folder under the tracker-write-back root that is not owner-only, is owned by someone else, or is a link as a cause of exit 10, and give its remedy: make the folders owner-only again (mode 700 for each folder from `~/.agentbundle/tracker-write-back` down), keep plan and record files in their own plans and prior folders, and run the command again; they say that running `plan-update` again does not fix it (AC18, AC19). The text pins in the skill-text suite check that each of those places says so.

**Done when:** the T11 pins are green (red against the old text first), skill lint passes, and the Atlassian suites stay green.

### T12: Fifth review repair: the folder remedy covers every refusal the folder preflight raises

**Verification mode:** goal-based, through the text pins in the skill-text suite and skill lint.

**Depends on:** T11

**Tests:**
- The exit-10 row of the `jira` and `jira-align` command tables and the two Atlassian guide passages that T11 edited route to the folder remedy for every refusal the folder preflight raises, not only when the message names a folder: a message that says a symlink or reparse point sits in the tracker-write-back path, that a path component is not a folder, or that a folder cannot be inspected or prepared; and the remedy covers `~/.agentbundle` itself (it must not be a link, and the folders from `~/.agentbundle` down must be owner-only where the check applies), a file sitting where a folder should be, and a folder too tight to read (AC18, AC19). The pin in the skill-text suite checks each of those phrases in the single exit-10 row of both skills and fails on the T11 wording.

**Done when:** the pin is green (red against the T11 wording first), skill lint passes, and the Atlassian suites stay green.

### T13: AC5 holds on every path: the loader rejects non-finite numbers, plan commands render before they save, and diagnostics encode newlines

**Verification mode:** TDD, at the shared module and at the CLI against the recording fake transports.

**Depends on:** T12

**Tests:**
- The plan and record loaders refuse a file holding a non-finite number however it is written (`1e400`, `-1e400`, nested inside a field value, in a record `entries` value), with exit 10 and no digest line, so no accepted plan can raise while its digest is recomputed (AC5, AC20); a plan whose numbers are all finite still loads.
- In both CLIs, `plan-update` constructs its full preview and any omitted-field report, and `plan-undo` constructs its digest line, before saving the plan file. Neither command prints a digest line before a successful save. After saving, each command visibly encodes embedded newlines in the actual returned path and prints its prepared output; `plan-undo` prints only that path and digest. If construction before saving fails (the reproduced `plan-update` case is a Jira Cloud document whose `marks` field is an integer), the command exits non-zero, saves no plan file, and prints no digest line. A failed save prints no digest line. A normal run saves the plan and prints exactly one digest line equal to the digest recomputed from the saved plan's contents (AC5).
- Interpolated diagnostics cannot start a line that begins with `digest:`: the argument-error message, the field name in the existing-text refusal, and the printed plan and prior-record paths are encoded so an embedded newline is shown as an escape; one test per surface puts a newline followed by `digest:` in the value and asserts the digest-line count is the one AC5 requires for that path (AC5, AC4).

**Done when:** the T13 tests are green (each shown red against the old code first), the existing suites stay green, and the lint, CI-parity, and QA-driver checks pass.

### T14: Output safety holds for lone surrogates and for the program name

**Verification mode:** TDD, at the shared module and at the CLI against the recording fake transports.

**Depends on:** T13

**Tests:**
- `encode_text` shows a lone Unicode surrogate (category `Cs`) visibly encoded, as it does the other unsafe characters, so a value holding one can be printed; `plan-update` in both CLIs with a replace value holding a lone surrogate saves its plan, prints the preview and exactly one digest line, and exits 0; the same value in a refusal message does not make the command raise (AC4, AC5).
- Each CLI's argument parser prints its program name encoded, so an installed path holding a newline followed by `digest:` cannot start a line that begins `digest:` in a usage or error message; one test per CLI (AC5).

**Done when:** the T14 tests are green (each shown red against the old code first), the existing suites stay green, and the lint, CI-parity, and QA-driver checks pass.

### T15: Jira commands validate the issue key before any request

**Verification mode:** TDD, at the CLI against the recording fake transport.

**Depends on:** T14

**Tests:**
- `plan-update` and `update-issue` in the Jira CLI check the issue key against the Jira key pattern in AC20 before any request, so a key holding a newline, an escape sequence, a path separator, or any other character outside the pattern exits non-zero with no request, no saved plan, no digest line, and an encoded diagnostic; a valid key behaves as before; one test per command puts a newline followed by `digest:` and `plan_file:` text in the key and asserts no output line begins with either, and that the recording fake saw no request (AC5, AC20).
- The Jira Align commands are unchanged and keep validating their resource and id before any request; a test pins that.

**Done when:** the T15 tests are green (each shown red against the old code first), the existing suites stay green, and the lint, CI-parity, and QA-driver checks pass.

## Rollout

- **Delivery:** three pack releases. Reversible by reverting the pack versions.
- **Deployment sequencing:** none.

## Risks

- Scripts that call `update-issue` or Jira Align `update` directly now refuse; the refusal message names `plan-update`.
- Jira Align resources without `PATCH` support refuse field updates until `--replace-record` is used.
- Records accumulate under `~/.agentbundle/tracker-write-back/` until the person deletes them; the guides say how.
- `transition --field` is refused in every case; people set fields through `plan-update` and `update-issue`, then transition.

## Changelog

<!--
- YYYY-MM-DD: spec approved by <handle>
- YYYY-MM-DD: plan approved by <handle>
-->

- 2026-11-11: spec approved by eugenelim (scope)
- 2026-11-11: plan approved by eugenelim (build strategy)
- 2026-11-11: amendment approved by eugenelim (scope)
- 2026-11-11: plan approved by eugenelim (build strategy)
