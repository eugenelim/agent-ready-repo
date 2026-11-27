# Work-loop product ref

The supervisor keeps a run's result on a protected Git ref and moves it with
`HEAD` in one transaction per step. Every verb first classifies how the ref,
`HEAD`, and the run store relate.

History the supervisor did not make waits for the owner. A rebuilt install is a
supervisor step only at a known skill home.

This page owns the ref transaction, the classification table, history adoption,
and the `regenerate` step. [The supervisor page](work-loop-execution-supervisor.md#product-ref)
owns the request order and the rest of the procedure.
[Product result integration](work-loop-result-integration.md) owns the parallel
design, which is `STATUS: PLANNED`.

## 1. One transaction moves the ref and `HEAD` together

The result is `refs/agentbundle/delivery/<run-id>/<token>/product`, and only the
supervisor moves it.[^1] A step builds its commit in a private index. One
`git update-ref --stdin` transaction then moves `HEAD` (through the branch it
names) and the ref from their expected values, so `HEAD` stays attached.[^2]

The kill points are `commit-built`, `refs-moved`, `made-recorded`, and `synced`.
Repair adds `projection-updated` and `repaired`.[^2]

A result integrates only while the ref still names the commit its request was
issued from. Otherwise `report` refuses `integration-conflict` and keeps the
worker's files.[^2]

The run store records the ref's name and the commit it last recorded, and
trusts the ref at that value only.[^3] A commit counts as made once the
invocation that moved the refs records it. A step cut off between the move and
the record is never completed or trusted.

### What snapshots protect, and what costs file reads

For observed gates in new POSIX runs, the supervisor binds a passing result
to the frozen candidate supplied to the gate. Windows uses boolean reports,
and legacy pinned runs keep their earlier gate protocol. Before observed gate
execution, it freezes the candidate's paths, blob IDs, and file modes in a Git
tree through a private index. It copies those blobs into scratch without
`.git` and runs the approved commands there. Admission commits that frozen
tree's changes, including deletions and executable bits, even if the working
files change after the test.[^9]

Scratch keeps gate writes separate from the developer's working files. It is
not an operating-system sandbox or a fixed toolchain: commands inherit the
environment, may read external paths, and can mutate scratch between checks.
The binding names the initial candidate, not every byte each command later
reads. Testing in the live checkout would also expose the gate to edits that
change and revert while it runs; before/after hashes cannot rule those out.

Three operations have different costs:

| Operation | Reads and purpose |
| --- | --- |
| Committed acceptance identity | `delivery_subject()` lists paths and blob IDs from the result commit with `git ls-tree`; it does not open each working file. The Git port caches that tree within the invocation. |
| Working change capture | `working_changes()` and `change_set()` copy the existing index and run `git add -A` through that private copy. Unchanged files can use Git's cached file metadata. The spec directory and any caller-selected rehash paths are read again. |
| Gate scratch copy | `_materialize()` reads and writes every frozen tracked blob into a fresh directory, checks paths and links, and preserves modes. This still costs whole-tree I/O even when working change capture uses the cached index. |

The current blob reader starts two Git processes per path: `cat-file -s` for
the byte limit, then `cat-file blob` for the content. Each uses the hardened
Git runner. A bounded batch reader could remove most of that process cost
while keeping the same frozen tree, path/link checks, size limits, modes,
deadlines, and separate writable files. This is an optimization proposal;
the current implementation still reads each blob separately.[^11]

The index copy preserves its original timestamps so a same-size edit made in
the index's own second remains visible to Git. An unusable, oversized, or
unreadable index, an unmerged index, or entries marked assume-unchanged or
skip-worktree cause a fallback to `read-tree HEAD`. That fresh index has no
cached file metadata, so the following `git add -A` can reopen and hash every
tracked file.[^10]

The separate `legacy-worktree-snapshot` provider in `_subject_source.py` is
retained code that the current supervisor does not call. It is not the source
of this gate-copy cost. [Acceptance and evidence](work-loop-acceptance-evidence.md#the-subject)
owns acceptance identity; the installed supervisor reference's Observed gates
section owns execution proof. Eligible direct-light work does not initialize
the supervisor and does not take this gate snapshot.

## 2. Classification decides what a verb may do

Before the request order, every verb classifies the refs. `status` does so
read-only and never repairs or refuses. The first row that matches applies:[^4]

| State | Result |
| --- | --- |
| Ref storage is not Git's files backend | Refuse `unsupported-ref-storage` |
| An attempt is open | The attempt guard answers `attempt-residue` or `attempt-refused` until both refs are restored; no classification runs |
| The ref is not at the recorded value, and it names one commit the run never recorded whose parent is the recorded value, while `HEAD` is on the recorded value or on that same commit | `next` asks the `history-adoption` decision; every other verb refuses `history-adoption-required` |
| The ref is not at the recorded value in any other way (missing, symbolic, rolled back, planted, or `HEAD` elsewhere) | Refuse `product-ref-diverged` and name the restore command |
| The ref is at the recorded value and `HEAD` lags it through made commits | Project `HEAD` and the working tree forward, or refuse `projection-blocked` when a file matches neither version |
| The ref is at the recorded value and `HEAD` differs otherwise (a rebase, an amend, a commit on top) | `next` asks `history-adoption`; every other verb refuses `history-adoption-required` |

A run that predates the ref gains one at its latest made commit when that is
safe, and otherwise asks the same decision. Until it has a recorded ref, a run
whose steps were committed with an attempt open reads `HEAD` for its subject.

`result_authority` selects only what acceptance reads: the ref's commit or
`HEAD`. Both settings write the ref the same way.[^5] `status` shows the subject
beside any refusal or pending decision, so its subject can be computed while
foreign history sits on `HEAD`. That view is display only.

## 3. Foreign history waits for an owner answer

A `history-adoption` answer is `adopt-history` from the `adopt_history` role
(`owner`), naming the `HEAD` commit.[^6] It commits one `reanchor` step that
moves both refs. It refuses `adoption-refused` if it would change a `delivery/`
file.

After a `reanchor` that changes the product or the spec directory, gates and
reviews run again. A cut-off `regenerate` step changes no `delivery/` file, so
it can be adopted. The `reanchor` then holds the install, and no second
`regenerate` step is made.

After adopting a cut-off step, the real index is reset to `HEAD` for each of
that step's paths still indexed as at the recorded value. A path staged
otherwise is left alone.

## 4. A `regenerate` step commits a rebuilt install at a known home

A `regenerate` step is the supervisor's commit of a rebuilt install, in a
repository that tracks its running install at an adapter's skill home. The
homes are `.claude/skills/`, `.agents/skills/`, `.kiro/skills/`, and
`.github/skills/`, a fixed list that matches the adapter contract.[^7] An
install tracked anywhere else is never committed by the supervisor, and `next`
answers `uncommitted-changes`.

A copy counts only at such a home where `HEAD` already holds the same files as
the running install's copy. The running copy always counts and must be the one
rebuilt.

A new home, or a directory at a home whose committed files differ from
the running copy's, is not a copy. An example is the product's own skill of that
name.

The next `next` after the admission stages the pack source's own entries
(object and mode) at each rebuilt copy and checks the built tree before any ref
moves. It uses the same two-ref transaction and kill points as any step.

It acts only when every copy that counts ends equal to the pack source, nothing
else changed, and the index stages no version of a copy's file that is neither
`HEAD`'s nor the pack source's. Otherwise `next` answers `uncommitted-changes`.
The install is product, so the step makes earlier gate evidence and reviews
stale, and readiness runs again.[^7]

`status` shows the pending step as `pending_step` (operation, up to 20 paths,
and `path_count`) with stage `gating`. It shows no terminal state, gate,
request, or readiness, unless a `history-adoption` decision is pending, which
it shows instead.[^8]

A controller commit of the install is still foreign history. Once a
regeneration is admitted, nothing commits on top of `HEAD` and no other attempt
is issued until `HEAD`'s install equals the admitted one. This holds whether the
supervisor's step or an adopted controller commit put it there.

Otherwise the verb refuses `supervisor-changed`. A new `regenerate` request
replaces an admission that never landed.

[^1]: `packs/core/.apm/skills/work-loop/scripts/_supervisor_commit.py`:
    `PRODUCT_REF_RE`.

[^2]: `_supervisor_commit.py`: the two-ref transaction and `kill_point` calls;
    the compare-and-swap failure that raises `integration-conflict`.
    `_supervisor_recovery.py`: `projection-updated` and `repaired`.

[^3]: `_supervisor_attempt.py`: the run-store `product-ref` record.

[^4]: `_supervisor_recovery.py`: the divergence classification and the refusal
    codes it raises. `_supervisor_admission.py`: `unsupported-ref-storage`.

[^5]: `_supervisor_readiness.py`: `result_lineage`.

[^6]: `_supervisor_recovery.py`: `adoption_action`.

[^7]: `_supervisor_attempt.py`: `_SKILL_HOMES` and `RegeneratePlan`.

[^8]: `work-supervisor.py`: the `status` verb.

[^9]: `packs/core/.apm/skills/work-loop/scripts/_supervisor_execution.py`:
    `_freeze`, `_materialize`, and `execute`; the installed supervisor reference,
    Observed gates; `_supervisor_commit.py`: `working_changes` and `tree_modes`.

[^10]: `_supervisor_commit.py`: `_tree`, `_PrivateIndex`, `change_set`,
    and `working_changes`;
    `_supervisor_readiness.py`: `delivery_subject`.

[^11]: `_supervisor_commit.py`: `GitPort.blob`; `_supervisor_git.py`:
    the hardened Git runner; `_supervisor_execution.py`: `_materialize` and
    `_observe`; `packs/core/tests/skills/work-loop/test_supervisor_execution.py`:
    frozen-candidate admission after scratch mutation.

## Direct light authority and construction-history limits

The direct-light router's Boolean declares eligibility; it cannot establish the
origin or authority of the caller's request. The invoking skill and its evals
own that boundary and the existing risk policy. A pure-function no-write test
proves the router's behavior, not an agent's real session behavior. RFC-0094's
session-local route does not make previously persisted light specifications
unreadable or unresumable, and does not introduce a second home for risk triggers.

The doc-drift delivery's original projection premise is historical; RFC-0016's
erratum and the current portable linter/reference own the changed rule.
Historical frozen acceptance statements that cited old skills remain evidence
of their delivery scope, not a requirement to recreate deleted skills merely
to satisfy an obsolete citation.
