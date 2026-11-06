# RFC-0113: One run grant at brief Ready

- **Status:** Draft
- **Author:** eugenelim
- **Approver:** eugenelim
- **Date opened:** 2026-11-05
- **Date closed:**
- **Decision weight:** heavy (it changes a published skill contract, gathers two human confirmations into one stop, and sets what an unattended run may do, which is an agent-authority trust model)
- **Related:** [RFC-0099](0099-cut-before-adding-and-artifact-shaping.md) (§7 keeps every spec-plan and human approval gate), [ADR-0157](../adr/0157-work-loop-approval-gates-park-instead-of-halting.md) (spec and plan approvals wait as parked gates bound to exact digests), [ADR-0150](../adr/0150-tdd-red-test-is-written-at-execute-and-mechanism-lives-in-the-plan-design.md) (D4 names the protected classes), [ADR-0159](../adr/0159-brief-level-runner-chains-slices-from-committed-records.md) and the [brief-level-runner spec](../specs/brief-level-runner/spec.md) (a read-only runner that chains a brief's slices; both are on an unmerged branch at 2026-11-05, and this RFC merges after them)

A few terms used throughout. They are grouped so you can skip what you know.

**Briefs and their skill**

- **Core** is this project's base pack of agent skills; adopters install it. A **delivery brief** coordinates one outcome that takes several slices. Its **Spec map** is a table listing those slices in order, one **row** per slice. A **slice** is one spec: one independently shippable change with its own plan.
- The `author-delivery-brief` skill moves a brief from `Draft` to `Ready`. Its continue mode runs in stages: 1 checks readiness, 2 runs the **shaping review**, 3 writes `Ready` after a human confirms it, and 4 asks a human to confirm the slice cut. The shaping review is an independent reviewer agent that checks the brief states the right outcome. Its result, `Clean` or `Findings`, is **revision-bound**: it holds only for the exact text it read.
- A brief is **Ready** when it passes stages 1 and 2 and a human confirms the transition. A Ready brief may list no slices yet, which is why the skill rules call its Spec map "empty-capable". **Executing** is the status a brief moves to once one of its slices is being built.
- The **slice cut** is the choice of which slices the brief splits into. Today a human confirms it at stage 4, after Ready.
- A **material edit** is one that changes the brief's outcome, scope, Spec map or other deciding content; it voids the shaping review's result. A wording or formatting fix is not material.
- The **brief coverage lint** checks each Spec map row's recorded status against the spec's real status. `close-work` is the skill that closes a finished brief. A `Shipped` brief must carry a `Cut-closed:` line recording that its cut is complete, and the lint refuses one without it.

**The runner and its run**

- **Full mode** is core's `work-loop` path for risky change. Each slice there has two human approvals, `spec-approved` and `plan-approved`. ADR-0157 lets them wait as **parked gates**: listed, answered later, and tied to an exact **digest** (a fingerprint of the file's contents), so an edited file cannot pass as approved.
- The **supervisor** is the script that runs one slice's work-loop procedure. It keeps committed delivery records, plus an uncommitted local store for parked gates.
- The **brief-level runner** (ADR-0159) is a read-only script above the supervisor. It reads the repository's committed records at the **base**, the freshly fetched default branch, and names the next slice to work on. It writes nothing and approves nothing.
- The runner has four commands, called **verbs**. `next` answers one action, such as `start-slice` or `resume-slice` (work on a slice), `await-gates` (a human approval is waiting), `await-merge` (a slice has reached its **merge-ready** stop: its run reports it ready to merge), `complete`, or `blocked`. A `blocked` answer lists each held-back row with one **reason code**, such as `refused` or `gate-not-clean`, in a fixed order so the most urgent reason shows. `status` prints each row's state. `gates` lists every parked gate and its state, such as `pending` or `stale`. `classify` takes a failed task and answers what to do: retry, split the task, replace the worker, abandon and **replan** (rewrite the remaining tasks), or `surface-to-human`.
- The **controller** is the agent that acts on the runner's answers. A **worker** is any agent the controller starts to do slice work, such as an implementer or a reviewer. Workers do the slice's writing.
- Each slice runs in its own **slice worktree**, a separate checkout on a branch named `brief/<brief-slug>/<spec-slug>`. The **main worktree** is the checkout that holds the base.
- **Standing orders** are one human-written file of numbered constraints per brief, passed to every worker (brief-level-runner AC-0015 to AC-0017).
- **Lease policy** is the supervisor's table of run limits: the retry budget per task, how many slices may be in flight at once, and each worker kind's **stuck-after runtime**, after which a worker with no visible progress is replaced (brief-level-runner AC-0018).

**Other records**

- The **protected classes** are a security boundary, data loss or durability, a migration or persisted state, a public interface, and an irreversible operation (ADR-0150 D4).
- **`auto_parallel`** was a per-run grant in the old work-loop engine. A human turned it on to let a run go through parallel groups of tasks ("waves") that had already cleared their gates, without asking each time. It was removed with that engine in core 4.0.0 (PR #1651), and nothing replaced it.
- ADR-0159's **"Revisit if"** line asks for that record to be reopened "if a run grant changes which actions may proceed without a human".

## Reviewer brief

- **Decision:** Whether a human may start a brief's run at one stop that asks for the Ready confirmation, the slice-cut confirmation and the run's limits together.
- **Recommended outcome:** Accept D1 to D6.
- **Change if accepted:**
  - `author-delivery-brief` offers an optional **run grant** at Ready: one stop with two distinct answers (Ready, the cut) and a short record of limits.
  - The brief-level runner reads that record and only ever tightens its own limits with it. It refuses to run a brief that is not `Ready` or `Executing`.
  - One follow-on spec builds both, and amends the brief-level-runner spec and the skill.
- **Affected surface:** `author-delivery-brief` continue mode, the brief-level runner, a new committed file kind `docs/product/run-grants/<brief-slug>.md`, and one merge-check script. Every adopter of core gets them on the release that ships the follow-on spec; the merge check protects an adopter only once they wire it as a required check.
- **Stakes:** a two-way door. A grant is optional. Removing the feature returns briefs to today's two stops, and no stored state outside the grant files changes.
- **Review focus:** what a grant bounds against an honest controller, and what it cannot bound against a worker that can write the base (D3).
- **Not in scope:**
  - any change to `spec-approved`, `plan-approved` or amendment reapproval, which stay as RFC-0099 §7 and ADR-0157 set them;
  - merge authority, which stays human in v1 (D5);
  - cross-repository briefs and write destinations beyond the runner's own branches;
  - building anything: this RFC records the decision, and the follow-on spec ships the code.

## The ask

**Recommendation:** accept all six decisions. A grant removes one stop per brief and bounds an unattended run. It takes no answer away from a human.

**Why now:** ADR-0159's runner removes the per-slice "start the next slice" stop. Two stops remain before any slice runs: the Ready confirmation and the later slice-cut confirmation (`author-delivery-brief` continue stages 3 and 4). A run that chains slices without a human also has no per-brief limit beyond the repository-wide retry cap and in-flight cap. `auto_parallel` was the only run-level grant, and it recorded no limits. ADR-0159's "Revisit if" names this grant.

| ID | Question | Recommendation | Why | Decide by | Reviewer action |
| --- | --- | --- | --- | --- | --- |
| D1 | Gather the Ready and slice-cut confirmations into one stop? | Yes, as an optional grant path that still asks two distinct answers; with no grant, today's two stops stay | Removes one stop per brief, and every confirmation is still a separate human answer | 2026-11-12 | Accept, or keep two stops |
| D2 | Where does the grant live, and how is it bound? | A committed file `docs/product/run-grants/<brief-slug>.md`, bound to the shaping-reviewed brief revision and the standing orders, with a closed grammar | The runner reads only committed records; the digests tie the grant to what the human read | 2026-11-12 | Accept, or name another home |
| D3 | What does a grant bound, and against whom? | It only narrows. It binds an honest controller fully. Against a worker that can write the base, its floor is the shipped runner's limits | A worker can forge repository files; a grant that could widen would let it widen too | 2026-11-12 | Accept, or show a safe widening |
| D4 | How is each limit enforced? | The runner enforces expiry, the cut, exit, retries and slices in flight. The controller enforces spend and `Also human`, as procedure | The runner sees only committed records and its own clock | 2026-11-12 | Accept, or move a limit |
| D5 | Is "merge if granted" in v1? | No. Merge stays human, and the human-only list can grow but never shrink | ADR-0159 D10 keeps merge human, and a forged merge-ready stop cannot be told apart today | 2026-11-12 | Accept |
| D6 | What follows? | One spec that amends the brief-level-runner spec and the skill; no separate ADR | The RFC records the decision; the spec ships it | 2026-11-12 | Accept |

## Problem & goals

### Problem

A brief stops for a human at Ready, then again at the slice cut, before the first slice's own spec work begins. Both stops ask about the same brief revision. The second one exists because Ready may have zero slices, so the cut is a separate choice.

Once ADR-0159's runner chains slices, a run may go on for hours without a person. It is bounded only by the lease policy's retry budget and in-flight cap, which are repository-wide. Nothing records, per brief:

- when the run should stop as done;
- how long it may run, or how much it may spend;
- which slices it may touch;
- what the human has kept for themselves beyond the fixed rules.

`auto_parallel` showed the shape of a run-level grant. It was off by default, it skipped only a human confirm step for work that had already cleared its gates, it was never an input to a gate, and a failure still stopped the run. It had no fields, so it could not bound anything, and it is gone.

### Goals

- One stop can start a brief's run, ask for both brief-level confirmations, and record the run's limits.
- Every spec, plan and amendment approval stays exactly as RFC-0099 §7 and ADR-0157 set it.
- A grant can only make a run stop sooner or do less than the shipped runner.
- A grant-path brief whose grant is missing, stale or malformed does not run.
- The RFC states plainly which limits hold against which actor.

### Non-goals

- **Unattended merge.** Plausible, and the main thing an operator might want from a grant. Excluded from v1 by D5.
- **A grant per slice.** It removes no stop, because each slice already has its own approvals.
- **Metering spend inside the repository.** Hosts report usage in different ways or not at all. D4 leaves spend to the controller and says what that costs.
- **Bounding a worker that can write the base.** The brief-level-runner spec accepts that residual, and a file read from the base cannot close it. D3 says what it costs.

## Proposal

### D1. One stop, two distinct answers

`author-delivery-brief` continue mode offers two paths after the readiness check.

- **Two-step path (today, and the default):** confirm Ready, then later confirm a slice cut. Unchanged for a brief whose Spec map is empty, which is every brief today. A turned-down grant path can leave a `Draft` brief with Spec map rows in it. For such a brief, stage 3 also asks the cut question in the same sitting and applies the table below. That way Ready is never written over rows nobody confirmed.
- **Grant path:** the skill derives the slice cut first and puts its rows in the brief's Spec map while the brief is still `Draft`. A row may have no spec yet; the runner later starts it in `author-spec` mode (brief-level-runner AC-0004). The shaping review then runs over the brief with its Spec map, so the review covers the cut. After a revision-bound `Clean`, the skill shows the human one stop with three parts:
  1. **Ready:** confirm the `Ready` transition of this exact brief revision — yes or no.
  2. **Slice cut:** confirm these Spec map rows as the cut — yes or no.
  3. **Grant:** confirm this grant record (D2) — yes or no.

The skill writes nothing until all three answers are in. One invariant governs every write the skill makes: **the skill never writes a `Ready` or `Executing` brief that holds a Spec map row no human has confirmed.** Two controls cover writes made outside the skill. First, the merge check (D2) fails a Spec map row change on a running brief when the same pull request also changes files outside `docs/`. Second, the runner adds one new refusal (added to brief-level-runner AC-0003): it refuses any brief whose `Status:` at the base is not `Ready` or `Executing`, the two running states in the brief status vocabulary. A `Draft` brief's rows never run, whoever committed them.

| Ready | Slice cut | Grant | What the skill writes |
| --- | --- | --- | --- |
| yes | yes | yes | `Status: Ready`, the `Run grant: required` header (D2) and the grant file, as one change (D2) |
| yes | yes | no | `Status: Ready` only. The cut is confirmed, so the rows stay, and the runner runs with its shipped limits. This is today's result after both stages |
| yes | no | any | Nothing yet. The unconfirmed rows must leave the Spec map first. That is a material edit, so the brief takes a fresh shaping review before Ready is asked again |
| no | any | any | Nothing. The brief stays `Draft`, and the runner refuses it |

The "yes, no" row costs a fresh review. That is the price of putting the rows in before the review: a Ready answer cannot be written over rows the human rejected.

This is one stop, not one approval. ADR-0157 and ADR-0159 share a driver: no human approval is "removed, merged, or inferred". RFC-0099 §7's heading covers "every spec-plan and human approval gate". The grant path keeps the Ready answer and the cut answer as two distinct human answers to two named questions. Either can be "no", and the table above says what each combination does. The skill's "second, distinct human confirmation" of the cut is still its own separate answer. It is just asked in the same sitting instead of later. No spec, plan or amendment approval is touched.

The follow-on spec amends four rules in `author-delivery-brief`:

- stage 3's Ready write-back, which now asks the cut question when the Spec map already holds rows;
- stage 4's "Only a confirmed slice invokes `new-spec`";
- stage 4's "a rejected or deferred cut changes neither Ready status nor the empty-capable Spec map";
- the Delivery map rule "Only confirmed specs enter the Spec map".

On the grant path, unconfirmed rows enter a `Draft` brief's Spec map before confirmation. They never run, because the runner refuses a `Draft` brief.

### D2. The grant file and its binding

The grant lives at `docs/product/run-grants/<brief-slug>.md`, beside the standing orders file. The brief itself gains one metadata line, `Run grant: required`, which records that it took the grant path, so the runner knows a grant must exist. The runner reads the grant file only from the base, the same way it reads standing orders (brief-level-runner AC-0002). The file holds exactly these fields:

| Field | Meaning | v1 grammar |
| --- | --- | --- |
| `Brief` | The brief this grant covers | `brief:<slug>`, equal to the file's own slug |
| `Brief digest` | The brief revision the shaping `Clean` bound | `sha256:<hex>` |
| `Standing orders` | The standing orders' sha256 at confirmation | `sha256:<hex>`, or `none` when the base has no file |
| `Granted by`, `Granted on` | Who the approver said they were, and when | a handle (letters, digits, single hyphens) and a date |
| `Expires` | When the run must stop starting or resuming work | an absolute UTC time ending in `Z`, later than `Granted on` |
| `Exit` | When the run counts as done | `all-merge-ready`, `all-merged`, or `after:<spec-slug>` with the slug in `Slice cut` |
| `Slice cut` | Which Spec map rows the run may work on | spec slugs, each a Spec map row, in Spec map order, no repeats |
| `Retries` | Retry budget per task | an integer from 0 to the lease policy's `retry_budget` |
| `Slices in flight` | Most slices started and not stopped | an integer from 1 to the lease policy's `max_slices_in_flight` |
| `Spend cap` | Spend the controller must not exceed | a positive number with a unit from a closed list, or `none` |
| `Also human` | Actions the human keeps beyond the fixed floor (D5) | zero or more of `push`, `pr-open` |

**Format rules.** The follow-on spec defines the file at the same depth as standing orders (brief-level-runner AC-0015): a regular UTF-8 blob, a size limit, no hidden characters, the fields above and no others. Any value outside its grammar makes the grant malformed. An out-of-range `Retries` or `Slices in flight` is malformed, never clamped. An unknown `Also human` action is malformed, so a misspelled reservation cannot vanish silently. The runner emits only the parsed, typed values, never the file's text. No grant text is passed to an agent as an instruction.

**What the digest covers.** `Brief digest` is the brief revision the shaping `Clean` bound, and the human is shown it in the record. The digest ignores exactly three things:

- the status token, as ADR-0157 D5's gate digest does, so writing `Status: Ready` or later `Executing` does not stale the grant;
- the `Run grant: required` header line, which the write-back adds;
- the values of the Spec map's Status column. That column is maintained as specs move from `Draft` to `Shipped`, and the brief coverage lint fails a recorded cell that differs from the spec's real status. Without this rule, ordinary slice progress would stale every grant.

Everything else stays digested, including each Spec map row's slug, the row order and the row count. The digest skips the header line, so deleting the header does not make the grant stale. Instead the runner refuses the brief, because a grant file with no header is its own refusal case (D3 table, last row). The follow-on spec names the exact digest function.

**Binding to what the human read.**

- The write-back refuses when the current brief or standing orders differ from the digests in the record shown to the human.
- The skill writes the grant bytes exactly as shown.
- `Status: Ready`, the brief's `Run grant: required` header and the grant file are written as one change. The skill writes files and does not run a shell, so the session that ran it commits that change in one commit. If any write fails, the skill rolls all three back when safe, or records a non-dispatchable reconciliation finding (a recorded mismatch that blocks all work until a human fixes it), as the skill does today for a failed Ready write. A brief left `Ready` with the header and no valid grant refuses to run (D3).
- The commit reaches the default branch only through a human-reviewed pull request. The merging human checks the grant file in that diff against the record they confirmed. That review, not the commit, is the final binding.

**Changing a grant.** A brief edit or a standing-orders edit makes the grant **stale**. Changing only the grant, such as renewing `Expires`, needs one human confirmation of the new grant record, with no fresh shaping review.

**A merge check.** Slice work merges through pull requests that carry worker commits, mostly code. The follow-on spec adds one check, keyed on the paths a pull request changes, not on its branch name. It must have these properties:

- **What it watches.** A **grant edit** is any of these:
  - any change to a run grant or standing-orders file;
  - a brief status change into `Ready`, from any status, or adding a new brief file whose status is already `Ready` or `Executing`;
  - adding, removing or reordering a Spec map row of a `Ready` or `Executing` brief;
  - any other change to a brief with the `Run grant: required` header, except three things ordinary slice and close-out pull requests must update: the status token, the Spec map Status values, and the `Cut-closed:` line.
- **What it refuses.** A pull request that carries a grant edit fails when it also changes any file outside `docs/`. A grant edit therefore cannot hide inside a pull request that carries code, contracts or pack content.
- **Where its logic comes from.** The check's script and the configuration that runs it always come from the base branch, never from the pull request under evaluation. A pull request cannot weaken the check that judges it. A change to the check is judged by the old check and takes effect only after a human merges it, so it needs no special route. That also covers a core release or an adopter's core upgrade that rewrites the script.

What it costs and what it misses:

- A mixed pull request that readies briefs and also changes files outside `docs/`, such as PR #1694, which also changed `contracts/REGISTRY.md`, must split that change out.
- A stage-4 cut write that adds a confirmed slice to a `Ready` brief touches only `docs/` (the brief and the new spec), so it passes.
- A slice whose own work lies inside `docs/` is not caught. There the reviewing human is the only control.

The check narrows the slice-merge path; it does not close it. The reviewing human remains the control. It protects only where it is a required status check. Core ships the check as a script, and an adopter wires it into their own required checks. Where it is not wired, the slice-merge path is open, and the confirmation record says so.

### D3. What a grant bounds, and against whom

A grant is a set of limits on the runner's own shipped behavior. It never adds anything.

| Grant state at the base | `next`, `status` | `gates` | `classify` |
| --- | --- | --- | --- |
| Brief has no `Run grant: required` header, and no grant file | shipped behavior | shipped behavior | shipped behavior |
| Valid and fresh, row inside the grant | shipped behavior narrowed by D4 | shipped behavior | uses the lower retry budget |
| Valid, but expired, past exit, or row outside the cut | shipped behavior narrowed by D4 | shipped behavior | answers `surface-to-human`, never a retry |
| Header present, file missing, malformed or stale | refuse | shipped behavior | answers `surface-to-human` |
| Grant file present, brief has no header | refuse | shipped behavior | answers `surface-to-human` |

`gates` never refuses on a grant problem, because the human needs the gate listing most when the run has stopped. It matches brief-level-runner AC-0011, where `gates` keeps exiting 0 for unreadable slices. Standing orders refuse only `next` and `status` (brief-level-runner AC-0016), and the grant follows the same split. `classify` never sends work out again once a grant limit has fired, so an expired run cannot keep retrying its last tasks.

**Against an honest controller and runner,** every limit in D4 holds, and a grant's limits are the human's limits.

**Against a worker that can write the base,** a grant bounds nothing beyond the shipped runner. The brief-level-runner spec accepts two `Security:` residuals in its Assumptions. A worker with Git in a slice worktree can create or rename `brief/*` branches. A worker that can also write the main worktree's files can move the base to its own commit. That worker can edit or delete the grant, or remove the header, and the runner cannot tell. Because a grant only narrows, the worst such a worker can do is return the run to the shipped runner's limits. That is the spend-and-ordering risk the brief-level-runner spec already accepts. It is not an approval or merge risk. The merge check in D2 narrows the slice-merge path where it is a required check. A worker that rewrites the base on the local machine is still not caught. That gap closes only when the host can prove the base is genuine, or can stop workers from writing shared Git refs.

The confirmation record tells the human this in two lines: "These limits hold for the controller; a worker that can rewrite this repository's default branch locally can lift them back to the runner's defaults." and "A grant change merged inside a pull request is caught only where the grant merge check is a required status check, and only when that pull request also changes files outside `docs/`; otherwise the reviewing human is the only check."

### D4. Who enforces each limit

The runner enforces the limits it can derive from committed records and its own clock. It reads its process clock once per verb.

- **Expiry:** past `Expires`, the runner names no `start-slice` or `resume-slice`.
- **Slice cut:** a row outside the cut is never named by `start-slice` or `resume-slice`.
- **Exit:** once the exit predicate holds, the runner names no `start-slice` or `resume-slice`.
- **Retries:** `classify` uses the lower of `Retries` and the lease policy's `retry_budget`. A replan still never resets the supervisor's run-wide retry count.
- **Slices in flight:** the in-flight cap is the lower of `Slices in flight` and `lease.max_slices_in_flight`.

These rules only remove `start-slice` and `resume-slice` candidates. The rest of brief-level-runner AC-0009's action order is unchanged: `await-gates`, `await-merge`, `complete` and `blocked` keep their order, so pending gates and merges still reach the human. When `next` answers `blocked`, each row a grant rule held back carries one grant reason: one each for an expired grant, a row outside the cut, and an exit already reached. Grant reasons sit after `gate-not-clean` and before `terminal-not-ready` in AC-0009's reason order. A row that is `unreadable`, `supervisor-changed`, `refused`, `awaiting-decision` or `gate-not-clean` still shows that reason, because each one sends the row to a human with its own instructions. If `next` says `blocked` and every row is held back only because the exit is reached or the row is outside the cut, the grant's work is finished.

The controller enforces two limits by procedure, because the runner never pushes, opens a pull request, or sees spend. `next` and `status` carry `Also human` and `Spend cap` as parsed values read from the base. The controller uses only those values, never a grant file in its working tree or a slice worktree, which a worker can edit.

- **`Also human`:** before a `push` or a pull-request open, the controller checks `Also human` in the latest runner answer and stops for the human when the action is reserved. On a header brief whose runner answer is a refusal, it stops for the human before any push or pull-request open. The confirmation record says this limit is procedure only.
- **Spend:** when the host reports usage, the controller stops starting and resuming work once the run passes `Spend cap`, and reports that to the human. Spend counts within one session only. It is not a committed record, so a resumed session starts from zero, and host reports may leave out spawned subagents. At grant time, the skill marks a numeric `Spend cap` as "not enforced on this host" in the confirmation record when the host reports no usage. Expiry, the cut, retries and the in-flight cap then act as the bound.

Running out of any limit parks the run. Work already dispatched finishes its current task, bounded by the lease policy's stuck-after runtime, and is never retried (D3). Nothing extends a limit except a new human-confirmed grant revision. Silence, a timeout or a session end never does.

### D5. What stays human

The grant cannot remove anything from this **fixed floor**. The floor lives in the skill and the runner, not in the grant file, so no grant can edit it:

- every `spec-approved` and `plan-approved`, still parked and digest-bound under ADR-0157;
- reapproval after a material amendment;
- every merge;
- every irreversible operation;
- acceptance of residual risk in a protected class.

A grant's `Also human` field can add `push` or `pr-open` to this list. It cannot remove from it.

Merge stays human in v1. ADR-0159 D10 keeps every merge human. The runner's `merge-ready` stop is derived from a slice worktree's own records, and the brief-level-runner spec accepts that a worker can forge it. Letting a grant release merge would therefore let a worker trigger merge. A later RFC may revisit this once the host can attest which worker wrote a record.

The grant is never an input to a gate. It never approves a spec or a plan, never relaxes a review or a security control, and never turns a parked gate into an approval. A test pins that rule, beside the brief-level-runner spec's AC-0024 test, which fails if RFC-0099 §7 or the root approval rule is weakened.

### D6. Follow-on

One spec delivers the grant. It amends the brief-level-runner spec rather than standing beside it, because it changes these parts of that spec:

- AC-0002's list of what the runner reads from the base (adds the grant file);
- AC-0003 (refuses a brief that is not `Ready` or `Executing`);
- AC-0009's reason codes (adds the grant reasons);
- AC-0013, whose exact `status` field list gains `Also human` and `Spend cap`, and the same two values in `next`;
- AC-0016's refusal rule, which gains a grant refusal for `next` and `status`;
- AC-0020's action table (`classify` answers `surface-to-human` once a grant limit fires);
- the Agent Rules: "extract only the fields named here" gains the grant fields, and "Ask first" covers new reason codes.

The same spec delivers:

- the grant file format, validation and digest function (D2);
- the grant path and decline route in `author-delivery-brief` continue mode, and the `author-delivery-brief` rules D1 lists as amended;
- the merge check (D2);
- a seeded grant template under `docs/product/run-grants/`;
- tests for each D3 row, including `classify` after expiry; a forged grant that tries to raise each limit; a deleted grant on a header brief; an `Also human` that tries to remove a floor item; and merge-check cases for a grant edit inside a slice pull request, a slice pull request that flips a `Draft` brief to `Ready`, a lifecycle-only slice pull request, a code pull request that adds a Spec map row to a running brief, a code pull request that adds a new brief already at `Ready`, and a pull request that edits the check's script and makes a grant edit, which must still fail;
- the run grant and standing-orders trust model in `docs/architecture/security.md`;
- the core release.

No separate ADR is needed. This RFC records the decision. ADR-0159 asks to be revisited "if a run grant changes which actions may proceed without a human". A narrowing grant does change that set, because it removes actions, so the trigger fires. This RFC is that revisit. Its outcome is that ADR-0159's decision stands as written: a grant adds no action that proceeds without a human, and every rule ADR-0159 sets (read-only runner, committed records, human approvals and merge) still holds. A grant that added an action would need a new revisit.

## Options considered

**D1 — how many stops start a brief run.**

- **Do nothing:** two stops per brief, and an unattended run with no per-brief limit. Rejected: it keeps the stop this RFC exists to remove, and leaves a long run with only repository-wide limits.
- **A grant per slice:** removes no stop, since each slice already has its own spec and plan approvals.
- **One stop with distinct answers (recommended):** one sitting, every confirmation still its own answer, and the old path kept.
- **One combined approval:** a single yes for Ready, cut and limits. Rejected: it merges two human answers into one, which the shared ADR-0157 and ADR-0159 driver forbids.
- **Bring back a per-run on/off flag like `auto_parallel`:** removes a stop but records no limit.

**D2 — where the grant lives.**

- **A section inside the brief:** every budget change would be a material brief edit, forcing a fresh shaping review for a time extension.
- **The per-checkout supervisor store:** it is per worktree and uncommitted, and ADR-0159 reads only committed records at the base.
- **Chat only:** leaves nothing to check after the session ends.
- **Its own committed file (recommended):** matches the standing-orders pattern, and the digests bind it to what the human read.

**D3 — narrow only or may widen.** Widening is rejected for v1: a worker that can write the base could widen too.

**D4 — who enforces the limits.** A new supervisor verb is rejected: the brief-level-runner spec forbids new supervisor verbs, and ADR-0159 rejects a verb that owns a brief. Controller procedure alone is rejected for every limit the runner can derive, because a derived limit survives a lost session.

**D5 — merge.** One line: merge stays human because a forged `merge-ready` stop cannot yet be told from a real one.

## Risks & what would make this wrong

- **One stop gets less attention than two.** A human may answer three questions in one sitting without reading them. Mitigation: each answer is its own yes or no, the record is short and fixed, and the two-step path stays the default. *Wrong if* grant-path briefs show more rejected or reworked slices than two-step briefs.
- **Grant churn.** A brief or standing-orders edit stales the grant and parks the run until a human re-grants. *Wrong if* re-grants are routine on ordinary briefs. Then the digest covers too much, and the follow-on spec should narrow it further.
- **A worker that can write the base.** It can edit or delete the grant, or remove the header, and lift the run back to the shipped runner's limits. The merge check narrows the slice-merge path where it is a required check. The local-base path stays open. Bound: the brief-level-runner spec's accepted spend-and-ordering risk. Closed by: a host-attested base or a worker sandbox that cannot write shared refs.
- **A controller that fakes the confirmation.** The controller runs the grant path, and `Granted by` records who the approver said they were, not who answered. ADR-0157 accepted the same limit for approval-entry lines. Here the result starts a whole run, so the cost is larger. Bound: a faked grant can only narrow the shipped runner, and the grant reaches the base only through a human-reviewed merge. Closed by: host-attested approver identity.
- **Spend is weakly enforced.** It is controller-reported, counts per session, and may miss spawned subagents. On a host that reports no usage it is not enforced at all, and the record says so at grant time. Bound: expiry, the cut, retries and the in-flight cap.
- **Clock skew.** The runner's clock decides expiry. A slow clock can extend the run past the expiry the human chose, though never past the shipped runner's limits.
- **Work in flight at expiry.** A task already dispatched runs until it ends or passes its stuck-after runtime, and `classify` sends nothing out again. Bound: one stuck-after runtime per task in flight.
- **An adopter without the merge check.** Where the check is not a required status check, a grant change can ride in a slice pull request, and only the reviewing human catches it. The confirmation record says so.
- **Unconfirmed rows added outside the skill.** A docs-only pull request, or one merged where the check is not required, can add a Spec map row to a running brief without a cut answer. The runner then starts that row with its shipped limits. Bound: the spend-and-ordering risk the brief-level-runner spec already accepts, because the row's spec and plan approvals stay human.
- **Split product pull requests.** Readying a brief in the same pull request as changes outside `docs/` now fails the check, so those changes travel separately.
- **A stale grant stops a healthy run.** Failing closed costs time, not safety. *Wrong if* operators delete grants or headers to keep runs moving. That stays safe but defeats the purpose.

## Evidence & prior art

- `auto_parallel`, removed in commit `49a239a72` (core 4.0.0, PR #1651). The removed `work-loop` text described it as "GO-approval-only", meaning it replaced only the human's go-ahead: it skipped only the human-confirm step for an already-cleared wave, was "never a gate input", and a failed wave still surfaced and stopped. The loop-infrastructure Phase 1 plan listed token-budget and same-error-count fields as Phase-2 future run-state fields. None were built.
- [RFC-0099 §7](0099-cut-before-adding-and-artifact-shaping.md#7-preserve-every-spec-plan-and-human-approval-gate): every spec-plan and human approval gate stays, approval binds to exact revisions, and a stale approved hash never resumes.
- [ADR-0157](../adr/0157-work-loop-approval-gates-park-instead-of-halting.md): parked gates. Its first driver forbids removing, merging or inferring a human approval. D4 says no verb, flag, default or record turns a parked gate into an approval. D5 defines the gate digest, which ignores the status token.
- [ADR-0159](../adr/0159-brief-level-runner-chains-slices-from-committed-records.md): the runner reads only committed records (D2), standing orders cannot grant authority (D6), and approvals, merge and irreversible operations stay human (D10). It shares ADR-0157's first driver.
- The [brief-level-runner spec](../specs/brief-level-runner/spec.md): the base-read rule (AC-0002), Spec map reading (AC-0003, AC-0004), `next`'s action and reason order (AC-0009), `gates` exiting 0 (AC-0011), the standing-orders file (AC-0015 to AC-0017), lease keys (AC-0018), and the `Security:` assumptions on forgeable branches and base.
- `author-delivery-brief` continue mode: stage 3's Ready confirmation, stage 4's "second, distinct human confirmation" of the cut, and the material-edit rule for delivery maps. Its brief coverage lint fails a Spec map Status cell that differs from the spec's real status.

## Experiment / validation

- **Hypothesis:** a grant-path brief reaches its first slice's spec work with one fewer stop than a two-step brief, and never does anything a no-grant run would not.
- **Measure:** on the first two briefs run on the grant path, count stops before the first slice's spec work, and compare each run's runner answers with the no-grant answers at the same base.
- **Success:** one fewer stop per brief. No runner answer outside the no-grant answers. Every stale, malformed or missing grant on a header brief refused.
- **Failure:** any runner answer a no-grant run would not give, or a stale or missing grant that lets work continue. Either one is a defect in the follow-on spec, and it blocks that spec's release.

The follow-on spec's tests carry the safety half of this (D6).

## Open questions

1. **Which units may `Spend cap` use?** Default: tokens, the unit hosts most often report. Owner: eugenelim. Decide by: when the follow-on spec is drafted.

## Follow-on artifacts

- One spec that amends the brief-level-runner spec and `author-delivery-brief`, adds the grant file, the merge check, a seeded template, the tests and the security-architecture section, and ships the core release (D6).
- No ADR. This RFC is ADR-0159's revisit, and ADR-0159 stays as written (D6).
