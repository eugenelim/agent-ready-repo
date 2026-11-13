# Spec: Tracker write-back preserves existing content

- **Status:** Shipped <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** none
- **Brief:** none
- **Discovery:** docs/product/research/tracker-write-back-survey.md
- **Depends on:** none
- **Contract:** none
- **Shape:** integration
- **Risk triggers:** security-boundary, structural-interface, persistent-representation

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

A person who asks an agent to improve a Jira or Jira Align record sees the exact before-and-after of every field, chooses what happens to the text already there, and approves one record at a time. The clients refuse any field write that is not bound to a previewed plan, refuse a write over values that changed since the preview, and keep a saved copy of what was replaced; the human approval itself is carried by the Agent Rules.

## What Changes

- A read-only `plan-update` command prints current value, proposed value, disposition, and a digest for every named field — `packs/atlassian/.apm/skills/jira/scripts/`, `packs/atlassian/.apm/skills/jira-align/scripts/`.
- The Jira and Jira Align clients refuse every non-GET request that is not on a closed allowlist unless it carries a verified plan; `update-issue` and `update` supply the plan — same two folders.
- `transition` with field content, `raw` writes, and comment edits fall under that refusal — same two folders.
- Three dispositions per text field: `keep`, `append`, `replace`. Other field types accept `keep` and `replace`. Jira Cloud edits operate on the ADF document tree, never on a string round trip.
- Every write saves the prior value first; `plan-undo` turns a saved record into a plan that goes through the same approval — same two folders.
- Jira Align `update` sends `PATCH`; `PUT` needs `--replace-record`.
- The story-triage and team-status skills, and the jira and jira-align evals, examples, and command tables, use the new flow — `packs/atlassian/.apm/skills/`.
- Linear and GitHub keep their closed no-text-write action sets, pinned by a test and an eval — `packs/linear/`, `packs/github/`.
- Tracker guides describe the flow — `guides/atlassian/`, `guides/linear/`, `guides/github/`.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| User-facing promise | A person now previews, chooses, and approves tracker edits | `guides/atlassian/`, `guides/linear/`, `guides/github/` (each read whole; refresh named in the plan) | repository owner | guide diff, link check | each guide describes preview, dispositions, undo, the no-text-write limit, and how to clean `~/.agentbundle/tracker-write-back/` |
| Interface compatibility | New commands, refusal exit codes, and the `PUT` change alter a published CLI | the two skills' `SKILL.md` command tables | repository owner | skill lint, command-table test | tables list `plan-update`, `plan-undo`, `--replace-record`, and the refusal codes |
| Release history | Three packs change behavior | `docs/product/changelog.d/` fragments for atlassian, linear, github | repository owner | `tools/changelog.py` validation | one fragment per bumped pack, with the Highlights decision recorded |
| Decision rationale | The survey carries the evidence for the design | `docs/product/research/tracker-write-back-survey.md` | repository owner | file present, cited from the plan | plan cites it |
| Current architecture, operations, maintainer procedure | none — the contract lives in each skill and its tests | — | — | — | — |

## Agent Rules

### Always do

- Run `plan-update` and show its full output for the one record before any field write.
- Ask for one approval per record, quoting the digest the plan printed.
- Ask the disposition for each named field that already holds text.
- Report the preview's old values and the saved prior-value path in the final report.

### Ask first

- Any `replace` disposition on a field that already holds text.
- Any `--allow-lossy` write.
- Any `--replace-record` plan, and any delete.
- Adding a text-field write action to a Linear or GitHub processor.

### Never do

- Write a Jira or Jira Align field without a plan whose recomputed digest matches the approved digest.
- Send `PUT` to Jira Align without `--replace-record`.
- Commit or log a prior-value record.
- Approve several records with one answer.
- Write a plan or record file outside `~/.agentbundle/tracker-write-back/`, by following a symlink, over an existing file, or with a mode wider than `0600`.
- Add a dependency, a new top-level directory, or a module boundary beyond the two skills' existing `scripts/` folders.

## Testing Strategy

- Plan output, digest recomputation, payload binding, disposition semantics, stale refusal, prior-value ordering, ADF and string handling, route refusal and its path normalisation, `PATCH` default, plan-undo: TDD against a fake transport that records every request, driven at the client and at the CLI.
- Linear and GitHub action sets: TDD over each processor's declared write capabilities.
- Skill command tables, evals, and lint: goal-based, through the existing skill lint and eval harness.
- The preview and approval conversation as an end user sees it: manual QA through the real CLI against a mocked transport, observed output recorded in the PR.

## Acceptance Criteria

The write allowlist, closed, per client. Jira: create issue (`POST` issue), comment create, attachment create, transition whose body holds neither `fields` nor `update`, and the JQL search `POST`. Jira Align: create, a `POST` to the single path segment `/rest/align/api/2/{resource}`. Deletes go only through each client's delete method, which takes an explicit confirm argument the CLI sets from `--yes`; that flag is a CLI convention, and the human gate for a delete is the Ask-first rule. Every other non-GET request is guarded. The guard error is `GuardRefused`; the guard exit code is 10.

- [x] AC1: `plan-update` sends only `GET` requests, in both skills.
- [x] AC2: `plan-update` prints, for every named field, its current value, proposed value, and disposition.
- [x] AC3: The plan digest covers the target, flavor, configured base URL, write method, notify setting, and each field's current value, proposed value, and disposition.
- [x] AC4: Tracker-sourced characters in Unicode categories `Cc` (other than the newline that ends a line), `Cf`, `Zl`, `Zp`, and the escape character appear visibly encoded on every stdout and stderr channel that can carry them, including the preview, ADF type names, drift output, refusal messages, `plan-undo` output, and tracker error bodies.
- [x] AC5: Each invocation of `plan-update` or `plan-undo` that saves a plan file, and each invocation of `update-issue` or `update` whose plan file the loader accepts (AC20), whether or not a later check refuses the update, prints exactly one line that begins with `digest:`, counted across stdout and stderr together, and it is the digest AC3 defines, computed from the plan's contents; any other invocation of those four commands prints none.
- [x] AC6: A guarded client call with no plan, or with a plan whose digest recomputed from its contents differs from the approved digest, raises `GuardRefused` and sends zero requests.
- [x] AC7: `update-issue` and `update` given a plan file edited after approval, its stored digest unchanged, exit 10 and send zero requests.
- [x] AC8: A verified plan authorizes only the single request whose method, absolute URL, and body equal the plan's resolved write; any other guarded request carrying it raises `GuardRefused` and sends zero requests, checked through `raw` and through a direct client call.
- [x] AC9: Given a plan whose recomputed digest matches and whose named fields are unchanged, the write sends exactly one non-GET request.
- [x] AC10: The body's field map holds the resolved value of each `replace` or `append` field and no `keep` field or other key.
- [x] AC11: When any named field differs from the plan's recorded current value at write time, the write exits 10 and sends zero write requests.
- [x] AC12: The prior-value record exists on disk before the first write request.
- [x] AC13: When a prior-value record cannot be written, zero write requests are sent.
- [x] AC14: Each prior-value record holds, per written field, the field name, old value, and written value, and holds the record identifier (Jira issue key; Jira Align resource and id) and the plan digest.
- [x] AC15: Plan and record files are written under `~/.agentbundle/tracker-write-back/<instance-slug>/`, and the resolved path of each stays under `~/.agentbundle/tracker-write-back/`.
- [x] AC16: The instance slug is the host plus a hash of the normalized scheme, host, port, and context path, holds only letters, digits, dot, and hyphen, and is never empty or made only of dots.
- [x] AC17: Every plan and record file is created exclusively, so an existing file fails the create, and with mode `0600`.
- [x] AC18: Every folder from `~/.agentbundle/tracker-write-back/` down is owned by the current user and grants no group or other access, whether this run created it or found it; otherwise the write exits 10 before any file is written or request is sent.
- [x] AC19: A symlink, or on Windows any reparse point, at any folder from `~/.agentbundle` down to a plan or record file makes the write exit 10.
- [x] AC20: `--plan` and `--record` files that resolve outside `~/.agentbundle/tracker-write-back/`, hold a field outside the closed field set, hold a mistyped field, hold an identifier outside the identifier alphabet, hold a `base_url` that differs from the configured base URL, or set a path, method other than the plan's `method` field, or header exit 10 before any request. The plan field set is `contract_version`, `target`, `flavor`, `base_url`, `method`, `notify`, `fields`, `digest`; the record field set is `identifier`, `plan_digest`, `entries`, and for Jira Align `record`. The identifier alphabet is the Jira key pattern `[A-Z][A-Z0-9]{0,9}-[1-9][0-9]{0,11}`, the Jira Align resource name `[A-Za-z][A-Za-z0-9]{0,63}`, and the numeric id `[1-9][0-9]{0,11}`.
- [x] AC21: `update-issue`, `update`, and `plan-undo` print no value read from a record file to stdout, stderr, or logs, and `plan-undo` writes its plan to a file and prints only the path and digest.
- [x] AC22: Each record's path is printed once, on stderr, before the first write request.
- [x] AC23: After an `append` on Jira Cloud, every pre-existing ADF node is equal and in the same order in the written document.
- [x] AC24: After an `append` on Jira Server/Data Center, the original string is a byte-exact prefix of the written value.
- [x] AC25: After an `append` on Jira Align, the original field value is a byte-exact prefix of the written value.
- [x] AC26: A `replace` that drops any ADF node type outside `paragraph`, `heading`, `bulletList`, `orderedList`, `listItem`, `codeBlock`, `text`, `hardBreak`, or any mark type, exits 10 without `--allow-lossy`.
- [x] AC27: A `replace` that drops only the node types the lossy-refusal criterion permits, or any type with `--allow-lossy`, proceeds to the write.
- [x] AC28: `plan-update` names every ADF node type and mark type a `replace` would drop.
- [x] AC29: For a non-text field, `append` exits 10.
- [x] AC30: Every non-GET request a client sends that is not on the allowlist raises `GuardRefused` without a verified plan, whatever its prefix or path form: relative, absolute, versioned, Agile, bulk-edit, percent-encoded, trailing-slash, `..`, and `;` matrix-parameter.
- [x] AC31: A `DELETE` that does not come through the client's delete method with its explicit confirm argument raises `GuardRefused` with zero requests, including from `raw`.
- [x] AC32: A transition request whose body carries `fields` or `update` raises `GuardRefused` with zero requests, including the name-lookup request, whether it arrives from `transition`, `raw`, or a direct client call.
- [x] AC33: A request whose scheme, host, and port together differ from the configured base URL, or that carries any of the headers `X-HTTP-Method-Override`, `X-HTTP-Method`, or `X-Method-Override`, raises `GuardRefused` with zero requests.
- [x] AC34: A guarded or allowlisted non-GET request does not follow a redirect.
- [x] AC35: With token authentication and no intake-policy or receipt refusal, an allowlisted write is not refused by the guard.
- [x] AC36: Under Jira SSO-cookie authentication each of `update-issue`, `transition`, `create-issue`, `comment`, `attach`, `delete-issue`, and `raw` with any method other than `GET` or `HEAD` exits before any request, while `raw GET` still reaches the wire.
- [x] AC37: The Jira client's intake-policy receipt refusal and the Jira Align client's intake-policy non-GET refusal each still refuse the requests they refused before the guard.
- [x] AC38: Under Jira SSO-cookie authentication `plan-update` succeeds.
- [x] AC39: For Jira Align, `plan-update` records method `PATCH` unless `--replace-record` is given, and with `--replace-record` records method `PUT` and lists every field of the record as read that the `PUT` body omits.
- [x] AC40: The Jira Align write sends the method its approved plan records, and `update` has no `--method` flag.
- [x] AC41: For Jira Align, the prior-value record holds the full record as read.
- [x] AC42: After a Jira Align write, the CLI re-reads the record and prints, on stderr, every field outside the plan whose value changed.
- [x] AC43: `plan-undo` from a saved record emits a plan that replaces each field with its saved old value.
- [x] AC44: `plan-undo` yields a plan that the stale-write criterion refuses when the remote no longer equals the written value in the record.
- [x] AC45: In the `jira-story-triage` eval case whose field value tells the agent to skip approval, the agent shows the preview and waits for a separate approval before any write.
- [x] AC46: Every `update-issue` and `update` invocation in a changed skill's `SKILL.md`, examples, and evals carries `--plan`.
- [x] AC47: An eval case in each of the Linear and GitHub packs asks for a description rewrite and expects the comment route.
- [x] AC48: Each of the Linear and GitHub refresh profiles declares write capabilities, leaving out `acquire`, equal to `comment`, `trace-link`, `pull-request-link`, `display-status`, `closure`.
- [x] AC49: No Linear or GitHub write targets an issue's or pull request's title, description, or body; a comment body and an attachment or link title are allowed. Linear is checked from recorded GraphQL variables and GitHub from recorded command arguments.
- [x] AC50: `agentbundle` skill lint passes for every changed skill.
- [x] AC51: Atlassian, Linear, and GitHub each bump one patch above fetched main, in `pack.toml` and `plugin.json` together.

## Follow-ons

none

## Assumptions

- Defaulted: Technical: the append disposition adds a visible labelled block rather than a hidden marker — default: visible block; if wrong: the merge step re-reads and re-checks the block (settled by: repository owner).
- Technical: whether Jira Align `PATCH` is accepted on every resource this skill reaches, and whether its body is a plain object or a JSON Patch operation list — what it would change: resources without `PATCH` refuse field updates until `--replace-record`, and a different body shape changes how AC8 binds the payload (settled by: a sandbox Jira Align instance).
- Technical: whether Jira Cloud preserves a labelled block through an edit in the Jira editor — what it would change: append would need a node-level identifier (settled by: a sandbox Jira Cloud site).
- Defaulted: Technical: plan and record files live under `~/.agentbundle/tracker-write-back/<host-slug>/`, the per-user root the credential store already uses — default: `~/.agentbundle`; if wrong: the folder follows a configured user root (settled by: repository owner).
- Defaulted: Process: all three packs take a patch bump, because new subcommands inside an existing skill are changed content under the pack version rule — default: patch; if wrong: Atlassian takes a minor bump (settled by: repository owner).
- Named gap: Privacy: plan and record files, including full Jira Align records that may hold assignee names and emails, stay under `~/.agentbundle/tracker-write-back/` until the person deletes them, and the CLI enforces no retention bound — what is therefore ungrounded: how long saved tracker text lives (settled by: repository owner, who accepts this at approval).
- Named gap: Platform: on Windows, file modes are no-ops, so privacy rests on the per-user profile ACL and the reparse-point refusal — what is therefore ungrounded: an explicit ACL (settled by: repository owner).
