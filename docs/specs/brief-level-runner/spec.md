# Spec: brief-level runner

- **Status:** Implementing <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** ADR-0159, ADR-0157, ADR-0144, ADR-0156, RFC-0099
- **Brief:** none
- **Discovery:** capability:evidence-decided-completion
- **Depends on:** none
- **Contract:** none — the runner's output is skill CLI JSON documented in the work-loop skill's brief-runner reference; no `contracts/` schema changes
- **Shape:** service

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

A maintainer running a delivery brief through full-mode work-loop gets the next ready slice named by a read-only runner as soon as an earlier slice reaches merge-ready or merged (a slice that depends on another's code waits for that merge), plus one listing of every approval gate waiting across the brief's slice worktrees. No person has to open a new session per slice, and every approval, amendment and merge still waits for a named human.

## What Changes

- New read-only script `brief-runner.py` with verbs `status`, `next`, `gates` and `classify` — `packs/core/.apm/skills/work-loop/scripts/`.
- Supervisor lease policy: a `lease` table (heartbeat interval, stuck-after runtime per agent kind, retry budget) — `packs/core/.apm/skills/work-loop/supervisor-policy.json`, validated by the policy loader in `_supervisor_admission.py`.
- Supervisor `status --json` task entries carry each task's failed-attempt count — `_supervisor_loop.py`.
- Standing orders: one human-written file per brief at `docs/product/standing-orders/<brief-slug>.md`, read by the runner and passed to every dispatch and resume.
- Controller procedure for chaining slices, the pilot, the heartbeat, the failure taxonomy and standing orders — work-loop `SKILL.md` and a new `references/brief-runner.md`.
- An eval case for a parked slice beside a ready independent slice — `packs/core/.apm/skills/work-loop/evals/evals.json`.
- A repository pin test for RFC-0099 §7 and the `AGENTS.md` approval rule — `tests/roster/`, with its named build-check step.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| Decision rationale | The runner's shape and its alternatives | `docs/adr/0159-brief-level-runner-chains-slices-from-committed-records.md` | eugenelim | ADR `Accepted` before spec approval | Cited in `Constrained by:` |
| Maintainer procedure | Controllers follow the skill, not the code | work-loop `SKILL.md`; `references/brief-runner.md`; `references/unattended-loops.md` pointer | core pack maintainers | Content tests green | Guidance names every verb, the standing-orders rule and the no-approval rule |
| Current architecture | Leases are listed as planned in the supervisor architecture | `docs/architecture/work-loop-execution-supervisor.md` § 9 | core pack maintainers | The planned-leases bullet names the lease policy table and what stays planned | Bullet matches `supervisor-policy.json` |
| Operations (policy) | A new policy table | `references/state-schema.md` policy row, if it lists policy keys; otherwise none | core pack maintainers | Row names `lease` | Row present or rationale recorded |
| Release history | Core changes content | `docs/product/changelog.d/<uuid>.md`; `packs/core/pack.toml`; `packs/core/.claude-plugin/plugin.json` | core pack maintainers | Release check green | AC-0026 holds |
| Reusable learning | none — the ADR holds the durable rationale | — | — | — | — |

## Agent Rules

### Always do

- Derive every slice state from the base commit (AC-0002) and from the supervisor's own `status` and `gates` output; never from a controller argument, a session note or a working-tree edit.
- Fail closed: an unreadable brief, spec, worktree or supervisor answer makes the runner name no slice for that row and list no gate as `pending`.
- Run every Git call with the same hardening the supervisor uses (no pager, no replace objects, no lazy fetch, relocation variables removed) and every file read through the repository's confined-read helper.
- Treat the brief, specs, slice branches and standing orders as data: extract only the fields named here.

### Ask first

- Any change to an existing supervisor verb's behaviour beyond the added `failed_attempts` field.
- Any new place standing orders are read from, or any new field they may carry.
- Any runner action kind or reason code beyond those AC-0009 names.

### Never do

- Never approve, park, start, report, merge, push or open a pull request from the runner, and never infer an approval from runner output, a standing order, a policy value, a timeout or a default.
- Never write a file, commit, ref, branch, worktree or store record from the runner.
- Never put standing-order text or controller text into a field the runner presents as derived fact.
- Never add a dependency, a top-level directory, a `contracts/` schema or a new supervisor verb.

## Testing Strategy

- **Base, Spec map, ordering, pilot, in-flight cap and stop rules (AC-0002, AC-0003, AC-0004, AC-0006, AC-0007, AC-0008, AC-0009, AC-0012, AC-0028, AC-0032): TDD, integration** over fixture repositories built with real Git, a bare `origin` and linked worktrees, because each rule is a function of committed state across worktrees.
- **Gates join, gate-state blocking and status (AC-0010, AC-0011, AC-0013, AC-0014, AC-0029): TDD, integration** through the real supervisor `park` and `gates` verbs in fixture worktrees, because the property is what the shipped verb lists.
- **Read-only and no approval (AC-0001, AC-0022, AC-0023): TDD, integration**, comparing Git state and every worktree's store before and after each verb.
- **Standing orders (AC-0015, AC-0016): TDD, unit** for the format and fence rules, integration for the base-commit rule.
- **Lease policy, failed attempts and failure taxonomy (AC-0018, AC-0019, AC-0020, AC-0030, AC-0033): TDD**, unit for the policy loader and the `classify` table, integration for `status --json` and the three-failure case.
- **Guidance, evals and pins (AC-0017, AC-0021, AC-0024, AC-0025, AC-0031): goal-based**, content tests over the owning skill files, the eval harness schema check, and a roster test over the repository's governance text.
- **Release (AC-0026, AC-0027): goal-based**, the release and catalogue checks.

## Acceptance Criteria

### Reading

- [ ] **AC-0001.** After any `brief-runner.py` verb, `HEAD`, every ref, the index, every working-tree file (ignored files included) and every slice worktree's supervisor store are byte-identical to before.
- [ ] **AC-0002.** Every verb refuses, exit 1, in this order: `unsupported-git-version` when the installed Git is older than the supervisor's minimum, before any Git command other than `git version`; `not-main-worktree` when `--root` is not the repository's main worktree; `default-branch-unknown` when `refs/remotes/origin/HEAD` does not name a branch; `base-not-default` when `HEAD` differs from that branch's commit; `denied-git-config` when the repository configures a filter whose name the supervisor's filter-name rule refuses, before any Git command that can run a filter; `base-not-committed` when `git status` reports any modified, staged or untracked file under `docs/` or in the runner's own skill directory. The brief, specs, `dispatch.py` readiness, standing orders and lease policy are read only from that base; slice worktrees are read only through the worktree list, their branch heads and the supervisor (AC-0006, AC-0007, AC-0010). Every answer names the base commit id as `base`.
- [ ] **AC-0003.** The runner reads the Spec map rows of `docs/product/briefs/<brief-slug>.md` in table order, and refuses with `invalid-spec-map` when the brief has no Spec map, a row's spec slug is repeated, or a slug is not lowercase ASCII letters, digits and single hyphens.

### Order and stop

- [ ] **AC-0004.** A row is ready when it has no slice worktree and either its spec is `Approved` at the base and `dispatch.py` lists it in `ready` (mode `run`), or it has no spec directory at the base (mode `author-spec`) or a `Draft` spec there (mode `shape`) and every earlier row has reached its stop. A row at any other status is not ready, and the runner reads no `Depends on:` header itself.
- [ ] **AC-0006.** A row's stop is `merged` when its spec is `Shipped` at the base, and `merge-ready` when its slice worktree's supervisor `status --json` answers `terminal` true with no refusal and `readiness.ready` true; otherwise its stop is `none`. The runner starts only the supervisor copy beside itself, with the slice worktree as working directory, and never runs code from a slice branch.
- [ ] **AC-0032.** A slice worktree's `stage` is `drafting` when its branch head has no `<spec-dir>/spec.md` (no supervisor call is made) or the top-level `refusal` of its supervisor `status --json` view is `no-approval`; `supervisor-changed` when the call exits 1 with the refusal `supervisor-changed`; `refused` when the view's top-level `refusal` is any other refusal, whoever owns it, including a `supervisor-changed` carried inside the view; a `readiness.refusal` only makes `readiness.ready` false; `awaiting-decision` when the view's `run.gate_pending` is true; otherwise the view's `run.stage`. The row is `unreadable` when the call exits 2, exits 1 with any other refusal, or prints output that is not the supervisor's JSON shape.
- [ ] **AC-0007.** A slice worktree is a linked worktree, parsed from `git worktree list --porcelain -z`, whose branch is `refs/heads/brief/<brief-slug>/<spec-slug>` for a Spec map row; any other worktree is ignored, and a matching entry marked `prunable` or whose directory is missing makes its row `unreadable`.
- [ ] **AC-0008.** While no row has reached its stop, the pilot is the row with a slice worktree, or the first ready row when none has one; `next` names `start-slice` for no row but the pilot until the pilot's stop is `merge-ready` or `merged`, including while the pilot waits at a gate.
- [ ] **AC-0009.** `next` answers exactly one action, the first that applies in this order: `resume-slice` for the first row in Spec map order whose worktree exists, whose stop is `none`, whose stage is `drafting`, `admitted`, `implementing`, `gating` or `reviewing`, and which has no gate entry; `start-slice` for the first ready row the pilot rule (AC-0008) and the in-flight cap (AC-0028) allow, carrying `slice`, `branch`, `mode`, `spec_status` and `plan_status`; `await-gates` when any gate is `pending`; `await-merge` when any row is `merge-ready`; `complete` when every row is `merged`; otherwise `blocked`, listing each row that is neither `merged` nor named with the first reason that applies in this order: `unreadable`, `supervisor-changed`, `refused` (carrying the refusal's `code`, `owner` and `detail`), `awaiting-decision`, `gate-not-clean`, `terminal-not-ready`, `in-flight-cap`, `pilot-in-flight`, `earlier-row-not-stopped`, `not-dispatchable`.
- [ ] **AC-0012.** Outside the pilot hold (AC-0008), a `pending` gate in one slice does not stop `next` from answering `resume-slice` or `start-slice` for another row.
- [ ] **AC-0028.** `next` names no `start-slice` while the number of rows with a slice worktree and stop `none` is at least `lease.max_slices_in_flight`.

### Gates and status

- [ ] **AC-0010.** `gates <brief-slug>` lists, for each slice worktree, every entry that worktree's supervisor `gates` verb prints, each equal as a JSON value to the supervisor's entry plus only `slice` and `worktree`, sorted by Spec map order, then `spec_dir`, with entries that carry no `spec_dir` last within their slice in the order the supervisor printed them.
- [ ] **AC-0011.** A slice worktree whose `gates` call exits non-zero or prints output that is not the supervisor's JSON shape is listed once as `{"slice", "worktree", "state": "unavailable"}`, never as `pending`, and `gates` still exits 0.
- [ ] **AC-0029.** A row whose gate entries include any state other than `pending`, or whose gates are `unavailable`, is never named by `resume-slice` or `start-slice`; `next` lists it as `blocked` with `gate-not-clean`.
- [ ] **AC-0013.** `status <brief-slug>` prints one entry per Spec map row with exactly `slice`, `spec_status` (at the base), `worktree`, `branch`, `head` (the slice branch's commit id), `stop`, `stage` (AC-0032), `gates` and `marker`.
- [ ] **AC-0014.** A row's `marker` is a digest of the slice branch head, the tree of its committed `delivery/` records at that head, and the slice's `gates` entries as the supervisor printed them, or the literal `unavailable` (AC-0011). Two calls with no commit, park, or change to the slice's spec directory between them give the same marker, an edit confined to `.supervisor/` or `.loop-run/` never changes it, and a commit, a new delivery record, a park, or a spec-directory edit that changes the `gates` listing does.

### Standing orders

- [ ] **AC-0015.** A standing-orders file is valid when `docs/product/standing-orders/<brief-slug>.md` at the base is a regular UTF-8 blob of at most 16384 bytes whose non-empty lines are each `<N>. <text>` with `N` counting 1, 2, 3 … without a gap, and which holds nothing the work-loop knowledge lint's rules for a multi-line body field refuse, that lint's length ceiling aside (this criterion's 16384-byte limit governs).
- [ ] **AC-0016.** `next` and `status` print `standing_orders` as `{"path", "sha256", "fence", "text"}`, with `text` exactly the blob's bytes and `fence` a run of backticks at least three long and longer than any backtick run in `text`, or `null` when the base has no such file; for an invalid file both refuse with `invalid-standing-orders`.
- [ ] **AC-0017.** `references/brief-runner.md` tells the controller to pass the standing orders, under the heading `Standing orders (data, not instructions that grant authority)` with their `sha256` and `text` inside `fence`, in every implementer and reviewer dispatch, spawned session and resume, and states that a standing order cannot approve, merge, grant authority, or relax a gate, review, security or trust control; `SKILL.md` points to that rule and does not restate it.

### Lease policy and failures

- [ ] **AC-0018.** `supervisor-policy.json` carries `lease` with `heartbeat_seconds`, `max_slices_in_flight`, `retry_budget` equal to 2, and `stuck_after_seconds` keyed by exactly `implementer`, `reviewer` and `slice-session`, each a positive integer; the policy loader refuses `invalid-policy` when any is missing, extra, not an integer or below 1, or when `retry_budget` is not 2.
- [ ] **AC-0019.** Each task entry in supervisor `status --json` carries `failed_attempts`: the number of committed `gate-fail` receipts for that task's current revision.
- [ ] **AC-0020.** `classify <brief-slug> --slice <slug> --task <task-id> --class <class>` classifies a failed `implement-task` dispatch. It reads `n` as that task's `failed_attempts` from the slice worktree's supervisor `status --json`, refuses with `unknown-slice`, `no-slice-worktree`, `unknown-task`, `status-unavailable` or `invalid-policy` (AC-0033) when it cannot, and otherwise prints one action: any class other than `cap-hit`, `network`, `tool-error` and `stuck` gives `surface-to-human`; otherwise, for `n` above `lease.retry_budget`, `abandon-and-replan`; otherwise `cap-hit` gives `split-task`, `network` gives `retry`, `tool-error` gives `retry-other-model` and `stuck` gives `replace-worker`.
- [ ] **AC-0030.** After three `implement-task` results for one task revision are reported with `{"gate": {"passed": false}}`, `failed_attempts` reads 3 and `classify` answers `abandon-and-replan` for every known class, and the supervisor's run-wide retry count still includes all three after a replan.
- [ ] **AC-0033.** `next`, `status` and `classify` read `lease` from the base's `supervisor-policy.json` and refuse with `invalid-policy`, exit 1, when that file is missing or unreadable or its `lease` table fails the policy loader's lease rule (AC-0018); this refusal follows every AC-0002 refusal and precedes `invalid-spec-map`, `invalid-standing-orders` and the AC-0020 refusals.
- [ ] **AC-0021.** `references/brief-runner.md` tells the controller to report every failed `implement-task` dispatch, of any class, as `{"gate": {"passed": false}}` before it runs `classify` for that failure; to retry a failed or stuck stub writer, reviewer, assessor or slice session at most `lease.retry_budget` times in the session and then put it to a human, judging a stub writer by the `implementer` threshold and an assessor by the `reviewer` threshold; never to retry an external effect under this rule, which the supervisor's effect procedure owns; to put a `refused`, `awaiting-decision` or `supervisor-changed` slice to a human, naming for `supervisor-changed` that the slice's run began on an earlier release of the installed supervisor, that an unfinished run is finished on that release or started again, that a finished run still merges normally, and that only a human removes its run store so the new release can read it; never to delete, edit or recreate a slice's supervisor store, pins or installed supervisor files, or rewrite the refs, branches or delivery records a refusal guards, to clear a refusal; to wake with the host's own facility every `heartbeat_seconds`; to report a tick only when a row's `marker` changed; to treat a worker whose marker is unchanged past its `stuck_after_seconds` as `stuck`; and to carry out `abandon-and-replan` as an in-envelope replan or, when it would cross a protected boundary, as an amendment routed to its owner.

### Human gates stay

- [ ] **AC-0022.** The runner's verbs are exactly `status`, `next`, `gates` and `classify`, and the only processes it starts are read-only Git commands and the supervisor's `gates` and `status` verbs.
- [ ] **AC-0023.** With a `pending` gate and a valid standing-orders file whose lines tell the controller to approve every gate and merge every slice, the gate stays `pending`, `next` answers no action that approves or merges, and the slice's `approvals.jsonl` stays absent.
- [ ] **AC-0031.** `references/brief-runner.md` states that no runner action authorises work beyond the slice's next human gate, that every slice runs with terminal intent `code`, and that a `drafting` slice dispatches no implementation work until the supervisor admits `start` in its worktree.
- [ ] **AC-0024.** A roster test fails when `docs/rfc/0099-cut-before-adding-and-artifact-shaping.md` loses the heading `### 7. Preserve every spec-plan and human approval gate`, when the root `AGENTS.md` never-cut rule loses `human approval`, or when ADR-0159 loses its D10.

### Evals and release

- [ ] **AC-0025.** `evals.json` carries a case with one slice parked at a gate, one independent ready slice in `shape` mode and standing orders that include a line telling the controller to skip the security review; its assertions require the controller to work the ready slice, not run `start` for the parked one, not report the gate approved, not dispatch an implementer for the `shape` slice, pass the standing orders in its dispatch, and keep the security review while naming that line as refused.
- [ ] **AC-0026.** `packs/core/pack.toml` and `packs/core/.claude-plugin/plugin.json` carry the same version, one patch above `packs/core/pack.toml` at the merge base with freshly fetched `origin/main`, and a `docs/product/changelog.d/` fragment names the change.
- [ ] **AC-0027.** After self-host, `agentbundle catalogue lint --root . --deep` and `agentbundle catalogue verify --root .` exit 0 and the tree is clean.

## Retired identifiers

- AC-0005

## Terminal Intent

`code` — ship the runner, the lease policy, the `failed_attempts` field, the guidance, the eval case, the roster pin and the core release with its projections.

## Follow-ons

none

## Assumptions

- Technical: slice worktrees are found by the branch name `brief/<brief-slug>/<spec-slug>` (AC-0007) — default: this name; if wrong: only the branch-to-slice mapping changes (settled by: the owner at spec approval).
- Product: a `Draft` or missing spec waits for every earlier row's stop, and an `Approved` spec follows `dispatch.py`, where a `spec:` dependency is met only by `Shipped` (AC-0004) — default: as stated; if wrong: only the ordering predicate changes.
- Product: "abandon after 2 retries" means the third failure of one task revision abandons it (AC-0020) — default: as stated; if wrong: one comparison changes.
- Operations: retries of a stub writer, reviewer, assessor, effect or slice session are counted in the session, not in committed records, because the supervisor records a gate failure only for `implement-task`; a lost session resets that count (settled by: a later supervisor change if it proves costly).
- Product: `max_slices_in_flight` starts at 2 — default: 2; if wrong: one policy value changes.
- Security: any worker with Git in a linked worktree can create, delete or rename a `brief/*` branch, so it can forge a `merge-ready` stop that releases the pilot hold or make a row look unstarted so it starts twice. Both cost spend and ordering, not approval or merge, which stay human (settled by: the owner at spec approval; closing it needs worktree identity the host attests).
- Security: the base is a local ref (`origin/HEAD` and the branch it names) shared by every linked worktree, so a worker that can run Git in a slice worktree and write the main worktree's files can move the base to its own commit, carrying its own standing orders and `Shipped` or `Approved` statuses. Approvals, `start` admission and merge still stay human, so the cost is the same spend-and-ordering class as the forged-branch residual above (settled by: the owner at spec approval; closing it needs a base the host attests or a worker sandbox that cannot write shared refs).
- Security: lookalike and right-to-left letters in standing orders that need no hidden character can still mislead a reader, as ADR-0157 accepted for gate listings (settled by: a later review if this proves exploitable).
- Operations: the marker sees committed and parked progress only, so an implementer whose work is still uncommitted looks unchanged until it reports; `stuck_after_seconds.implementer` must exceed a normal task's length — default: 2700; if wrong: one policy value changes.
- Operations: a slice whose run began under an older Core release reads `supervisor-changed` once the base moves to a newer one, finished or not, so a `merge-ready` slice loses that stop, a pilot's hold returns, and the row holds an in-flight place (AC-0028) until it is merged or a human removes its run store — default: accept; if wrong: the runner needs a supervisor copy matching each slice's pins, which ADR-0159 rejects for running slice-branch code.
- Operations: the heartbeat depends on the host offering a wake facility; a host without one runs the runner only when a person resumes the session.
