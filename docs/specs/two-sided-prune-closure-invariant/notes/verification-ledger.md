# Verification ledger — two-sided prune closure invariant

Execution observations for the RFC-0096 Wave 7c slice 2 delivery. The spec and
plan are approved and pinned; anything learned by running the work is recorded
here.

Date: 2026-09-13.

## Gates

| Gate | Result |
| --- | --- |
| `lint-contract-item-alignment.py` on this spec | exit 0 — 0 findings |
| `lint-spec-status.py --root .` | exit 0 |
| `pytest tests/roster/test_two_sided_prune_closure_invariant.py` | exit 0 — 47 passed |
| Neighbouring roster suites (work-intake, workspace-status, slice 1) | exit 0 — 296 passed |
| `make build-self` | exit 0; source and both adapter projections byte-identical |
| `make lint-ruff` | exit 0 |
| `make lint-mypy` | exit 0 — 139 files, run after self-host so the projected engine is checked |

## End-to-end evidence

A disposable fixture outside this checkout, driven through the shipped projected
command at `.claude/skills/workspace-status/scripts/workspace_status.py`.

Successful two-sided prune, one selected target with two duplicate canonical
occurrences and one unselected neighbour:

- `--preview` exit 0. Emitted `operation_id`, `operation_digest`, `selection`,
  `targets` — and none of `subject`, `role`, `confirming_identity`, so the
  challenge is unsigned and cannot authorize itself.
- Prune without a confirmation: exit 2, `confirmation_missing`, nothing removed.
- Prune with the lock pre-planted: exit 2, `lock_busy`, nothing removed.
- Confirmed prune: exit 0, `artifact_absent: true`, `membership_absent: true`.
  The selected directory and its `notes/` subtree are gone, **both** duplicate
  occurrences were removed, and the unselected neighbour's directory is
  byte-identical with its workspace entry intact.

Forced half-state, via the `membership_write_noop` fault-injection point:

- Artifact removed, membership left on disk.
- Result: exit non-zero, `closure_failed`, naming
  `artifact_survives: false`, `membership_survives: true`, and the surviving
  occurrence with its collection and entry index.
- It did **not** report success. This is the behaviour the whole contract exists
  to guarantee, observed on the running artifact rather than inferred.

The confirmation file is resolved relative to the repository root, matching the
existing `repair-apply` route. An absolute path is refused as
`confirmation_invalid`.

## Defects found while building

**Two construction tests could not fail.** Worker mutation proofs exposed both,
and both were strengthened before the code was accepted.

- The empty-selection test never planted the lock, so a route that validated
  *after* acquiring it was indistinguishable from one that validated before.
  It now pre-plants the lock: a post-lock check surfaces `lock_busy` and the
  test goes red.
- The unsigned-challenge test exercised only the engine seam, so a CLI preview
  leaking authorization fields went undetected. It now drives the CLI too.

**The intake interval test asserted on source text.** It grepped
`intake_transaction.py` for the lock filename, which proves the string exists
and nothing about when the lock is held. Releasing the lock between
materialization and registration left it green. It now runs the real
transaction and records the lock's live presence inside each callback, so an
early release turns it red.

**An existing payload shape was broken.** Adding the prune route rewrote the
`unknown_subcommand` response from its established
`schema_version`/`mode`/`reason` shape into a new `error` object, which failed
slice 1's frozen contract. The original shape is restored and this slice's test
was corrected to assert the real contract rather than the shape it assumed.

**An `Implementing` spec in `work.queue` fails repository health.** The entry
produced `impossible_transition` and `unapproved_spec` findings until it moved
to `work.active`, which is where an in-flight spec belongs.

## Dispositions

**Worker sandbox cannot delete directories.** Every destructive case reported
`PermissionError: Operation not permitted` under the headless worker, inside
both its default temporary storage and `/private/tmp`. Thirteen cases and four
of five engine mutation proofs were inconclusive there. All were re-run in the
supervising environment, where the suite is fully green; the inconclusive
mutation proofs were re-run directly and are recorded above. This is an
environment limit, not a property of the code.

## Residual limitations, stated rather than implied

- The shared lock excludes only writers that take it. A writer that ignores
  `.workspace-repair.lock` — an editor, or an external process — can still
  fracture the observation, and no repository mechanism detects that today.
- A→B→A is excluded for lock participants only. The raw-byte digest alone does
  not detect it, and the documentation says so rather than claiming otherwise.
- Replay of a valid confirmation against an identically reconstructed state is
  not detected. Detecting it needs durable receipt state, which the exact-delta
  guarantee forbids writing.
- The protected-directory manifest reaches literal repository paths only. A path
  a test assembles at runtime is outside it. The manifest is defense in depth,
  not what makes a deletion safe.

## Review rounds on the implementation

Nine adversarial rounds ran on Codex against the finished diff. They found twenty
Blockers, and I reproduced the most severe ones directly against the running
code before accepting any of them. Every one is fixed and re-verified.

**A destructive authority bypass.** `prune_execute` replaced the caller's
selection with the selection decoded from the confirmation. Approving
`docs/specs/alpha` and then invoking the prune for `docs/specs/bravo` with
alpha's confirmation reported success and deleted **alpha** — an artifact the
operator never asked to remove — while leaving bravo. The selection is now fixed
from the execute arguments and immutable; a confirmation whose decoded selection
differs, order included, is refused `confirmation_binding_mismatch` before any
mutation. Re-verified: both directories survive.

**Success with a surviving membership, twice.** First, closure resolved through
the read-only report's four-collection scope, so a canonical occurrence in
`backlog.closed` survived a "successful" prune. Then, after that repair, an
occurrence nested inside a list under an array-of-tables still survived. Closure
now walks every dictionary and list recursively and fails on a resolving
occurrence anywhere. Removal stays scoped to recorded occurrences; detection
deliberately does not.

**Every comment in `workspace.toml` destroyed.** A successful prune reserialized
the parsed document: a fixture with three comments had zero afterwards. Against
the real 172 KB register this would have erased every load-bearing comment in one
run. Membership removal is now byte-span surgery against the locked baseline
bytes, locating elements structurally so a `}` or `,` inside a string cannot end
one early. Re-verified: 3 of 3 comments preserved, only the target element cut.

**Deletion could escape the repository.** Removal checked only whether the leaf
was a symlink, then called `shutil.rmtree` on the resolved path, so a symlinked
*parent* redirected deletion outside the root. Removal now descends through
`O_NOFOLLOW | O_DIRECTORY` descriptors and unlinks via `dir_fd`, and an on-disk
entry the manifest never recorded fails closed. Re-verified with an external
tree behind a symlinked parent: refused, and the external tree byte-identical.

**Drift after the baseline was overwritten rather than refused**, and **the CLI
read the confirmation file before taking the lock** (returning
`confirmation_invalid` where AC-0010 requires `lock_busy` with no repository read).
Both fixed and re-verified.

### Controls that could not fail

Five were found and strengthened. Worth recording, because each passed while the
property it named was violated:

- The empty-selection test never planted the lock, so pre-lock and post-lock
  validation were indistinguishable.
- The unsigned-challenge test exercised only the engine, so a CLI preview leaking
  authorization fields went undetected.
- The intake interval test grepped source text for the lock filename, which proves
  a string exists and nothing about when the lock is held.
- The compatibility test compared the branch against itself, and then against a
  hand-typed SHA; it now resolves `git merge-base origin/main HEAD`.
- The delivery test asserted only that version fields exist. It now requires both
  versions equal, exactly one patch above the merge base, and named by the
  core-led changelog entry. A major bump and unequal versions each turn it red.

## Version derivation

Re-derived immediately before the PR, not at branch start. `origin/main` moved
twice while this branch was in flight and claimed `2.25.26` and then `2.25.27` —
the second being the version this branch already held. The branch was rebased
onto `origin/main` and the pair re-derived to `2.25.28`, one patch above the new
merge base. This is exactly the silent collision a start-of-branch bump produces.

## Known deviation from the approved plan

T7 says the final diff must reject any change to this repository's
`workspace.toml`. The diff contains one: slice 2's own registration, moved from
`work.queue` to `work.active` when the spec went to `Implementing`. The owner
directed that the registration be kept, and an `Implementing` spec sitting in
`work.queue` produces `impossible_transition` and `unapproved_spec` findings that
fail the repository-health check. Recorded rather than silently resolved.

### Round four

**A non-`spec` kind membership at the selected path survived.** Both resolvers
filtered on `kind == "spec"`, so a `{path = "docs/specs/<slug>/spec.md",
kind = "defect"}` entry at the exact selected path outlived a "successful" prune.
This is a live shape, not a hypothetical: the skill's own eval fixture ships it,
and the live register carries 41 defect-kind entries. The prune now resolves
identity by exact selected artifact path regardless of canonical kind, for both
the occurrences it removes and the closure scan. Slice 1's read-only report keeps
its kind filter, which is correct for that report. Re-verified end to end: three
`doomed` references across two collections, including the defect-kind one, all
removed.

**The operation read `workspace.toml` three times.** Round three's pre-mutation
re-check was added on top of an earlier baseline read, which broke AC-0012's
exact-two-read contract while satisfying AC-0028. Rather than amend a pinned
criterion to match the code, the two reads were collapsed: one taken as late as
possible — serving as both the baseline AC-0028 compares and the
immediately-pre-mutation state — and one after mutation for closure. Both
criteria now hold without a contract change.

**Artifact drift between the manifest check and removal** was deleted under the
stale confirmation; each recorded entry's digest, mode, type, and symlink target
is now validated through the held descriptors immediately before unlinking.

One control could not fail and was rewritten: the own-spec protection test only
asserted manifest membership, so an implementation that ignored the manifest at
execute time still passed. It now runs the real prune against a disposable copy.

One test expectation was stale rather than wrong-headed: it required a clean run
to FAIL because an out-of-allowlist occurrence survived. Once removal became
kind- and collection-agnostic, that occurrence is correctly removed, so the test
now asserts a clean two-sided success and proves the broad scan separately by
forcing the membership write to no-op and requiring both occurrences to be named.

## Semgrep disposition — load, not a finding

`make build-check` failed its SAST leg on all four runs, always on files outside
this diff: `packs/core/.apm/skills/work-loop/scripts/loop-cohort.py` every time,
and `packs/atlassian/.apm/skills/jira/scripts/_client.py` once. Measured 1-minute
load averages were 39.7, 39.8, 80.0 and 39.x on 10 CPUs, with several peer
sessions running gates concurrently.

Following the gate's own printed guidance: neither file appears in this diff, and
the exact invocation run against `loop-cohort.py` alone exits 0. Each of this
change's five modified Python sources was scanned individually with the same
invocation and is clean. Zero other build-check legs failed on any run. Slice 1
recorded the identical disposition for the same file at load 35.5.

## Quality-engineer pass

A separate operability lens ran after the adversarial rounds closed, and raised
three findings that the correctness lens had not:

- **An interrupted prune was not recoverable in practice.** A kill left the
  PID-stamped lock and a half-state, and a re-run then refused `lock_busy` or
  `nothing_to_remove` with no documented way forward. The shipped skill now
  carries a recovery procedure: check whether the recorded holder is alive before
  treating a lock as stale, read the reported phase to learn which half survived,
  and finish a partial removal through the repair route rather than by editing
  the register by hand.
- **Post-mutation failures said nothing useful.** They collapsed to
  `closure_failed` with only `observation_unavailable`. Every post-baseline exit
  now carries the fixed selection and the last completed phase
  (`selection_fixed`, `baseline_confirmed`, `artifacts_removed`,
  `memberships_removed`), so a half-state can be reconciled from the command's
  own output. Verified: a forced fault reports
  `last_completed_phase: memberships_removed` with its selection.
- **`lock_busy` could not be told from a stale lock.** It now reports the
  repository-relative lock file name and the process id recorded in it, with no
  absolute root. Verified.

The stale lock has no automatic recovery and this slice adds participants to it.
That remains a recorded follow-on rather than something this slice closes; the
new guidance makes it operable in the meantime.

### Rounds five to nine

The later rounds kept finding real defects, each narrower than the last. Recorded
because the pattern is the useful part, not the individual fixes.

- **Legacy *string* memberships survived.** The resolver tested only dict elements,
  so `active = ["spec/chosen"]` outlived a successful prune. Strings now resolve
  through the existing legacy alias path and participate in removal and closure.
- **The same nesting bug in two branches.** A doubly-nested lifecycle list records
  an inner index that the byte-span editor applied to the outer array, cutting an
  unselected sibling's membership while reporting success. Fixed first for the dict
  branch, then found again in the string branch. The second time it was closed at
  the class level: every occurrence-recording site on the prune's path now records
  the nesting marker, and nested occurrences fail closed. The other three recording
  sites live in slice 1's read-only resolver, which removes nothing and needs no
  marker. Verified refused for nested canonical, legacy-string, and parse-blocked
  forms.
- **Partial deletion on a refusal path.** Validation interleaved with deletion, so
  drift in a late-traversed entry was found only after an earlier one was already
  unlinked — data loss on a path that then reports a refusal. A whole-tree
  validate-only pass now runs over every selected manifest before the first unlink.
- **An unconfined read introduced by an earlier fix of mine.** The operability work
  added a lock-holder diagnostic that read the lock file with no `O_NOFOLLOW` and no
  size bound, so a symlinked lock leaked outside content. It now requires a
  no-follow open, a regular single-link file, and a 32-byte bound — and declines to
  open at all where no no-follow primitive exists. A diagnostic is never worth a
  confinement hole.
- **A FIFO at the lock path hung the command.** The diagnostic open blocked forever
  waiting for a writer. It now opens non-blocking.
- **Confined removal is platform-conditional.** It rests on no-follow descriptor
  descent. Where that primitive is absent the operation now declines rather than
  deleting with weaker protection.
- **A generated site input was tracked.** `web/src/lib/now-highlights.generated.json`
  is absent on the default branch and the scoped guidance says these inputs are
  generated, not committed. An earlier slice had committed it by accident; this
  branch untracks it. No suite depends on it.

Six controls that could not fail were found and strengthened across these rounds,
each mutation-proven afterwards. Two review findings were corrected rather than
adopted: one test expectation was stale rather than the code being wrong, and one
proposed remedy would have amended a pinned criterion to match the implementation
instead of fixing the implementation.

## Owner decision — dedicated refusal code, 2026-09-14

The platform case previously returned `closure_failed` with an
`unsupported_platform` detail field, because adding a refusal code is an
*Ask first* boundary in this spec. The owner signed off, so it is now its own
code, `unsupported_platform`.

No amendment was needed. The spec names codes only where an individual criterion
requires one and nowhere enumerates the set, so the exhaustive list lives in the
shipped `SKILL.md` — a Durable Output rather than contract. Adding a code
therefore changed documentation and behaviour, not an acceptance criterion.

The code is its own refusal rather than a closure failure on purpose: nothing was
attempted and nothing about the repository is wrong. The host simply offers no
no-follow directory primitive, and confined removal depends on one.

Two controls came with it, both mutation-proven:

- The platform test previously asserted the capability probe equalled its own
  definition, which proves nothing. It now forces the capability off, drives the
  real execute path, and requires the dedicated refusal, the named selection, and
  a byte-identical tree.
- A new sweep reads every code the engine can emit straight out of the source and
  requires each to appear in the shipped refusal list. Removing the new code from
  `SKILL.md` turns it red. An undocumented code leaves an operator holding a
  result they cannot look up, and that list is the only place to look.
## Remote evidence — the authoritative signal

On the final rebase onto `origin/main` (base core `2.26.0`, so the pair was
re-derived to `2.26.1`):

- All **36** PR checks pass, zero failures. Four jobs report `SKIPPING`
  (`deploy`, `publish-pypi`, `publish-artifactory`, Gate H pre-release), which
  are not applicable to a pull request.
- `ci-security` passes, which settles the local semgrep disposition: the timeouts
  were machine load, not this change. The Windows jobs pass too, which is the
  platform the no-follow capability guard exists for.
- Dispatched `test-corpus` and `test-roster` both completed successfully.

`origin/main` moved three times while this branch was in flight and claimed
`2.25.26`, then `2.25.27`, then `2.26.0` — the middle one being a version this
branch already held. Re-deriving at branch start rather than immediately before
the PR would have shipped a silent collision each time.

### Review of the dedicated-code change

One scoped round ran on the follow-up. It sustained two findings about the new
documentation sweep, both of which were real and are fixed:

- The sweep searched the whole `SKILL.md`, not the refusal list. `invalid_workspace`
  also appears in an unrelated table, so deleting it from the list an operator is
  told to consult left the control green. The search is now bounded to the list
  section, anchored on its own heading line, and the control fails loudly if that
  anchor ever moves.
- The sweep read only literal `_prune_error("code")` calls, so a code assembled at
  runtime would escape it. Non-literal refusal codes are now rejected outright.

Both are mutation-proven: removing the code from the list only, and emitting a code
through a variable, each turn the sweep red.

One finding was **refuted**. It reported that ordinary prune execution returns
`closure_failed` on this change, citing 14 failures in its own run. Those are the
worker sandbox's directory-removal denial — the same documented environment limit
recorded in every prior round — not a property of the code. The suite is 47 passed
in the supervising environment, and an end-to-end run of the projected command
prunes successfully. The finding's narrower point, that the platform test forces
the cached capability flag rather than detecting a genuinely unsupported host, is
accepted as proportionate: the flag is the seam, and runtime-probing destructive
filesystem operations to reach the same branch would be worse than the test it
replaces.

### Remote re-verification after the dedicated-code change

Rebased again onto `origin/main`, which had claimed `2.26.1` — the version this
branch was holding — so the pair was re-derived to `2.26.2`. That is the fourth
collision this branch avoided by re-deriving at push time rather than at branch
start; `origin/main` has moved through `2.25.26`, `2.25.27`, `2.26.0` and `2.26.1`
while this work was in flight.

All **36** PR checks pass, zero failures, with the same four deploy/publish jobs
reporting `SKIPPING` as before. Dispatched `test-corpus` and `test-roster` both
completed successfully. Local: 47 focused roster cases, 314 neighbouring cases,
ruff, mypy, spec-status and contract-alignment all clean, projections
byte-identical across both adapters and the packaged runtime.

## The prune moved into its own module, 2026-09-14

`gate-sast` failed on CI. I first concluded the failure was caused by this change,
measuring one semgrep taint rule at 11.4s before and 15.1s after on
`workspace_status_engine.py`. **That conclusion was wrong and the measurement was
unsound.** Repeated three times per arm the difference is ~13.6s to ~14.8s, about
9%, and the decisive fact is simpler: the engine bytes are byte-identical between
`bd76d6e75`, where `gate-sast` passed, and `987855b70`, where it failed. The only
difference between those heads is fifteen lines of markdown in this file. The rule
sits near its per-file budget on 4-CPU runners and flakes there.

The owner approved the module split anyway, on its own merits rather than as a fix
for that failure: the engine had grown to 7,451 lines, and the prune code is
unusually expensive for syscall taint analysis — 8.2s for 1,289 lines against 11.4s
for the original 6,136 — so this slice moved a near-budget rule closer to its edge
for everyone who touches that file next.

`workspace_status_prune.py` now holds the prune implementation. The engine is back
to 6,150 lines against a pre-slice 6,136. The prune module loads the engine as a
sibling by file path, registering it with `sys.modules.setdefault` before
`exec_module` so one engine instance is shared and a test monkeypatch still reaches
the code under test. Neither module touches `sys.path`.

### Two defects the re-verification caught

- **The packaged runtime shipped incomplete.** `make build-self` synced the engine
  into `packages/agentbundle/agentbundle/_data/` but not the new sibling, because
  runtime pairs are declared explicitly in `self_host.py`. The packaged copy would
  have held an engine whose sibling was absent. The pair is now declared.
- **The drift gate skipped rather than failed.** A declared pair whose bundled copy
  is missing hit `continue`, so an incomplete packaged runtime passed build-check
  silently. Tightening it to fail was implemented and mutation-proven here, then
  **reverted**: CI showed `tests/integration/test_build_check_drift_gates.py:291`
  asserts the gate returns 0 against a synthetic minimal tree that legitimately
  lacks bundled files, so the stricter check reds an existing test. Closing the gap
  needs that fixture updated too, which is a change to a pre-existing gate rather
  than to this slice, so it is recorded as a follow-on. The pair declaration itself
  stays — that part is required, and byte-drift is still caught whenever both files
  exist, which is the state `make build-self` always produces.

A third finding was fixed as a residual: the CLI registers a module in `sys.modules`
before `exec_module`, so a raising exec left a half-built module that a later attempt
would reuse. The loader now drops only what that call registered.

Two review findings were **refuted**. One reported the prune suite red after the
move, citing 14 failures — again the worker sandbox's directory-removal denial; the
suite is 47 passed here. The other described the CLI loader evicting the engine while
retaining the prune module; the loader has no eviction path at all, reusing both
through `sys.modules.get` behind an `_ENGINE_BOUND` guard, and the only
`sys.modules.pop` sites in the engine use hash-derived names for unrelated modules.

### A measurement trap worth recording

Loading `self_host.py` by path to test its gate silently exercised the **primary
checkout**: its module-level `REPO_ROOT` resolves from the installed package
location, not from the file path it was loaded through. The first mutation run
reported "none" for both arms because it was inspecting a tree that does not contain
this work at all. Pointing `REPO_ROOT` at this worktree made the gate fire correctly.

### A third surface the new module reaches

CI found one more: `.gitattributes` must declare `merge=regen` for every
gate-covered generated file, and the new packaged runtime was not listed.
`tools/test_gitattributes_merge_driver.py` reports it as under-scoped and reds
`gate-main`, which in turn reds `make build-check` because that job only
aggregates the others.

Adding a generated file therefore touches four surfaces, not one: the pack source,
both adapter projections, the packaged-runtime pair declaration in `self_host.py`,
and the `merge=regen` block in `.gitattributes`. Only the projections are produced
automatically; the last two are hand-declared and each has its own gate. Local runs
caught none of this — `make build-self` is silent about all three, and the
`.gitattributes` check lives in a suite that takes 105 seconds and is not part of
the local gate set.
