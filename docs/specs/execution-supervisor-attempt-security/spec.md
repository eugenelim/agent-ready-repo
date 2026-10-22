# Spec: Execution supervisor attempt security

- **Status:** Implementing <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** Platform Core
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** ADR-0144
- **Brief:** brief:acceptance-centered-work-loop
- **Discovery:** none
- **Contract:** `contracts/delivery/` (consumes `security-event.v1`, `security-capability.v1`, `safe-process.v1`, `containment-attestation.v1`, and `execution-supervisor-core`'s `execution-request.v1` and `execution-result.v1` unchanged)
- **Shape:** service

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.
>
> **Protected semantic-policy contract.** `Contract`, `Scope and Non-goals`,
> `Durable Outputs`, `Agent Rules`, `Testing Strategy`, `Acceptance Criteria`,
> `Terminal Intent`, and `Accepted Risk` are approval-bound or explicitly
> review-authorized. A change follows its owning amendment, review, or risk
> decision. `Outcome`, `What Changes`, `Follow-ons`, and `Assumptions` are
> working material that may be corrected without changing accepted authority.

## Outcome

Platform Core maintainers get a supervisor that refuses a worker attempt when the worker changed a file the supervisor trusts, touched Git control state, or asserted facts its request kind cannot carry, that never adopts such a change by any path, and that launches its own processes with recorded grants and whole-tree termination on every supported platform. Success is that no naive-forgery fixture reaches a supervisor commit or a task projection, while honest attempts, supervisor commits, and core's crash corpus still pass.

## What Changes

- Issuing a new attempt records a manifest of the files the supervisor trusts and of Git control state; every later `next` and `report` checks it before any write — `work-loop/scripts/_supervisor_attempt.py`.
- A refused or interfered-with attempt leaves `attempt-residue` until the controller restores the named paths.
- Supervisor `git` calls run through one hardened helper with signing off, and admission refuses repositories whose Git config would run code or change staged bytes unseen.
- Every supervisor entry point checks its own code and policy digests before importing a sibling.
- `_process_safety.py` gains a Windows branch that launches suspended into a breakaway-denied Job Object with an explicit handle list.

## Scope and Non-goals

This spec owns worker-attempt validation, residue, Git hardening, supervisor
pinning and regeneration, per-request-kind result acceptance, launch-grant
recording, the untrusted-code launch gate, and Windows process control. It
extends `execution-supervisor-core`, whose request kinds, change set,
`delivery/` lag rule, and step order it uses, and consumes Slice 1's security
primitives.

Its adversary is a naive worker attempt that writes files directly (ADR-0144
D11). While an attempt is open, any change to a trusted file counts against the
attempt whoever made it: the controller replans only between attempts, which
is how D11 narrows D3's approval-free replanning in practice. Worker attempts
are host subagents this spec never contains; the Accepted Risk states what
that leaves open.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| Current architecture | The process primitive and supervisor trust boundary change. | `docs/architecture/runtime-security-primitives.md` | `agentbundle` security maintainers | Architecture review | The page describes the Windows branch, Git hardening, the attempt checks, and which protections need verified containment. |
| User documentation | Some Git configurations are unsupported. | The supervisor reference that `execution-supervisor-cutover` owns; this spec supplies the refused-settings list | Core pack maintainers | Link check | The list is stated where adopters read it. |
| Release history | Live process code changes. | `packs/core/pack.toml`, `packs/core/.claude-plugin/plugin.json`, `docs/product/changelog.md` | Core pack release maintainers | Version parity | Each task's Core 3.x release carries a changelog line. |

## Agent Rules

### Always do

- Fail closed: an unverifiable check refuses with a stable code and a
  `security-event.v1` line in `<spec>/.supervisor/security-events.jsonl`.
- Reuse Slice 1 primitives for grants, events, confinement, and containment.
- Get a security-reviewer pass on each task's diff before merge.

### Ask first

- Widening any launch grant in the Launch grants table.
- Accepting any additional security risk.

### Never do

- Run a supervisor `git` command outside the hardened helper, except an
  out-of-helper config read.
- Fall back to a single-process kill on Windows.
- Add a dependency outside the Python standard library.

## Testing Strategy

- **Attempt checks and residue (AC-0001, AC-0002, AC-0003, AC-0004, AC-0005, AC-0006, AC-0007, AC-0008, AC-0026, AC-0027):**
  TDD over forgery, honest-write, interleaved-`next`, supervisor-commit, and
  crash fixtures in a temporary Git repository with no ignore rules.
- **Git hardening (AC-0009, AC-0010, AC-0011, AC-0012):** TDD with planted
  hooks, fsmonitor, filters, textconv, external diff, signing commands,
  includes, replace refs, grafts, packed refs, a rewritten gitfile, and global
  LFS and line-ending settings.
- **Launched code, pinning, and trust (AC-0013, AC-0014, AC-0015, AC-0016, AC-0017):**
  TDD with a test file that writes a trusted file, an edited installed module,
  a planted bytecode file, a regeneration, and untrusted-trust fixtures.
- **Result facts and grants (AC-0018, AC-0019, AC-0020):** TDD over the Result
  acceptance and Launch grants tables.
- **Windows (AC-0021, AC-0022, AC-0023, AC-0024):** TDD on the Windows CI job.
- **POSIX regression (AC-0025):** the existing safe-process suite on POSIX CI.

## Acceptance Criteria

### Definitions

- **Trusted files.** The spec's `spec.md` and `plan.md`, every record its
  `Constrained by:` cites, and the installed skill directory the supervisor runs
  from.
- **Supervisor store.** `<pinned Git directory>/agentbundle-supervisor/<run id>/`,
  outside the worktree and outside every cache core calls deletable. It holds
  the pinned digests, each issuance's manifest, each refusal record, the source
  digests recorded when a `regenerate` request is issued, and the ids of the
  commits the supervisor made.
- **Pinned digests.** The sha256 digests of every file under the installed
  skill's `scripts/` except `__pycache__`, and of `supervisor-policy.json` and
  `review-rules.json`. They are held only in the
  supervisor store, recorded once by the controller-run admitted `start`, and
  replaced only by the AC-0016 re-pin. When no pin record exists for the run,
  that `start` computes them from the installed bytes, without importing a
  sibling, and records them; it is the only entry point that may do so, and
  only for a run whose store already holds its made-commit record and whose
  supervisor commits are its first approval and terminal steps. A run admitted
  before pinning shipped has no store and is never pinned.
- **Git control state.** The resolved Git directory and common directory pinned
  at admission; the worktree's `.git` gitfile; `commondir`; `refs/replace/`;
  `info/`; `objects/info/alternates`; `hooks/`; every repository and worktree
  `config` file; and `HEAD` and the current branch ref. `HEAD` and the branch
  ref match the manifest when the manifest's `HEAD` is an ancestor of the
  current `HEAD` and every commit after it is listed in the supervisor store.
- **Worker request.** An `implement-task`, `write-stub`, `review-role`, or
  `assess-finding` request.
- **Manifest.** Path, size, and sha256 of every trusted file and Git control
  state file, excluding `__pycache__` directories, recorded in the supervisor
  store each time `next` issues or re-issues a worker, `run-gates`, or
  `regenerate` request after any residue has cleared, and each time the
  supervisor launches a red proof or scratch receipt with no attempt open; it
  is never re-recorded while that issuance is open. The
  supervisor's caches — the journal, `run.json`, locks,
  `security-events.jsonl`, and `.loop-run/` — are not covered.
- **Open attempt.** An issuance that records a manifest — a worker, `run-gates`,
  or `regenerate` request, or a red proof or scratch receipt the supervisor
  launches with no attempt open — that has not been reported, refused, or
  superseded. A launch-owned attempt closes when its launch ends and the
  post-run check completes; a refusal clears only against the refused
  issuance's own manifest.
- **Out-of-helper config read.** A `git config` read that runs no configured
  code, passes the pinned `--git-dir`, runs with the `git` row's environment
  from the Launch grants table, and serves exactly one of two purposes: the
  admission read of the effective config for the carried settings and for the
  filter definitions AC-0009 checks, or the once-per-run commit-identity read
  of `user.name` and `user.email`. No other `git` call qualifies.
- **Code-running Git setting.** Any configured key whose value Git runs as a
  program or command, including `filter.*.clean`, `filter.*.smudge`,
  `filter.*.process`, `diff.*.textconv`, `diff.*.command`, `diff.external`,
  `core.sshCommand`, `core.fsmonitor`, `core.hooksPath`, `gpg.program`,
  `gpg.*.program`, `gpg.ssh.defaultKeyCommand`, `include.path`, and
  `includeIf.*.path`, and any other key whose name ends in `command` or
  `program`.

### Result acceptance

| Request kind (from `execution-supervisor-core`) | Facts the result may assert | Everything else |
| --- | --- | --- |
| `implement-task`, `write-stub` | None; the supervisor computes the change set | Refused |
| `review-role` | One `review-report.v1` bound to the requested subject, or a selection record | Refused |
| `assess-finding` | One finding assessment for the requested finding | Refused |
| `run-gates` | Gate commands, exit codes, and output digests | Refused |
| `external-effect`, `effect-query` | Presence, absence, or unknowability, whether the attempt has ended, and the effect receipt | Refused |
| `regenerate` | Completion only; the supervisor computes the new digests | Refused |
| `human-decision` | The decision and its authority reference | Refused |
| Any other kind | Nothing | Refused |

### Launch grants

| Launch kind | Recorded write roots | Network | Environment |
| --- | --- | --- | --- |
| `red-proof` | Execution root minus trusted files and the Git directory | Not granted | `PATH`, `HOME`, `LANG`, `TMPDIR`; on Windows also `SYSTEMROOT`, `TEMP`, `TMP`, `PATHEXT`, `COMSPEC` |
| `scratch` | The temporary worktree | Not granted | As `red-proof` |
| `git` | The pinned Git and common directories, the execution root, and a scratch worktree's own Git directory | Not granted | As `red-proof`, plus `GIT_CONFIG_NOSYSTEM`, `GIT_CONFIG_GLOBAL`, and `GIT_INDEX_FILE`; an out-of-helper config read also gets `XDG_CONFIG_HOME`, and on Windows `USERPROFILE`, `HOMEDRIVE`, and `HOMEPATH` |

Without Slice 1 verified containment, write roots and network denial are
recorded, not enforced; AC-0013 detects trusted-file writes after the run.

### Criteria

Attempt checks and residue

- [ ] **AC-0001.** A worker attempt after which a trusted file or Git control
  state differs from the manifest, or a `delivery/` working copy is neither
  equal to nor a strict prefix of its `HEAD` version, is refused at `report`,
  logs a `security-event.v1` denial, and admits no evidence or completion.
- [ ] **AC-0002.** While an attempt is open, every `next` compares trusted files,
  Git control state, and `delivery/` against the manifest and `HEAD` before
  core's envelope derivation and before any write, and on a difference refuses
  the attempt, recording the refusal in the supervisor store.
- [ ] **AC-0003.** A worker edit to `plan.md`, `## Acceptance Criteria`, or
  `evidence.jsonl` by an implementer or a reviewer, followed by `next` before
  `report`, yields `attempt-residue`, no `replan` commit, and an unchanged task
  projection, on a first issuance and on a re-issuance after a refusal.
- [ ] **AC-0004.** A `resolve-effect` during an open attempt advances `HEAD`
  without refusing the attempt; a re-approval `start` during an open attempt
  first compares trusted files and Git control state with the manifest and
  refuses on a difference; and a kill at any core kill point around either
  leaves an attempt that core's crash corpus still completes.
- [ ] **AC-0026.** A worker rewind, amend, or commit carrying copied supervisor
  trailers during an open attempt refuses the attempt.
- [ ] **AC-0027.** Deleting the journal, `run.json`, and `security-events.jsonl`
  during an open attempt or after a refusal neither admits a forged attempt nor
  clears residue.
- [ ] **AC-0005.** After a refused attempt, `next` refuses with
  `attempt-residue`, naming each differing path, until the supervisor store's
  refusal record is cleared by trusted files and Git control state matching the
  manifest and `delivery/` matching `HEAD`.
- [ ] **AC-0006.** No change to a trusted file present when an attempt is
  refused is ever committed as a replan or changes a task projection.
- [ ] **AC-0007.** A worker attempt whose change set includes a symlink that
  resolves outside the execution root, into a trusted file, or into the Git
  directory is refused.
- [ ] **AC-0008.** A non-TDD worker attempt whose change set lies inside the
  execution root and leaves trusted files and Git control state unchanged —
  including one that imports the installed supervisor scripts, and one during
  which the journal is deleted — passes the attempt checks.

Git hardening

- [ ] **AC-0009.** `start` refuses with `unsupported-git-config`, naming the
  setting, when repository or worktree config sets a code-running Git setting,
  or when global or system config defines a filter that any attributes file Git
  reads for the worktree uses.
- [ ] **AC-0010.** Every supervisor `git` invocation other than an
  out-of-helper config read runs through one helper that ignores system and
  global config apart from carried line-ending and `core.excludesFile` settings,
  turns
  off commit and tag signing, disables hooks, fsmonitor, external diff,
  textconv, and replace refs, and first verifies Git control state by direct
  file reads: against the open attempt's manifest when one exists, and
  otherwise against the Git and common directories pinned at admission.
- [ ] **AC-0011.** A planted hook, fsmonitor command, filter driver, textconv
  driver, external diff, signing command, or config include runs nothing during
  any supervisor `git` call.
- [ ] **AC-0012.** A commit substituted through `refs/replace/` or a graft is
  never read as a supervisor commit. During an open attempt, neither is a commit
  reached through a packed-ref move or a rewritten gitfile or `commondir`.
  Outside an open attempt, the supervisor reads its commits by their trailers,
  so a rebase that preserves their messages still converges.

Launched code, pinning, and trust

- [ ] **AC-0013.** After each run of repository code that the supervisor
  launches or the controller reports — gates, scratch receipts, and red proofs —
  trusted files, Git control state, and `delivery/` are checked again before any
  commit, and a difference refuses the result.
- [ ] **AC-0014.** Every supervisor entry point compares the installed pinned
  files with the pinned digests read from the supervisor store before importing any sibling (the
  admitted `start` that records them, per the definition, excepted) — or, while
  a `regenerate` request is open, with the digests the supervisor recorded from
  the pack source's bytes at `HEAD` when it issued that request — and refuses
  with `supervisor-changed` on a mismatch. It also refuses, on every spec, when
  the installed pinned files differ from the pins of any run whose store holds
  an open attempt, or a refused issuance whose residue has not cleared. Each
  run's store directory appears with its spec record already in it; a run
  directory with no spec record refuses every spec until it is removed. While a run's store directory has no pin record, every entry point
  except `start` refuses `supervisor-changed` on that spec, until that run's
  `start` records its pins; that spec's `start` ignores such a directory when
  none of its made-commit ids is reachable from `HEAD`, judged through the
  hardened helper. A `<spec-dir>` whose case differs from the tracked path is
  refused as a usage error before any sibling loads.
- [ ] **AC-0015.** A bytecode file placed beside a pinned module is never
  executed.
- [ ] **AC-0016.** When `HEAD` holds the Core pack's work-loop source, review
  readiness holds, and the installed skill differs from that source, `next`
  emits one `regenerate` request; its result is exempt from the manifest for the
  installed skill only, and is admitted only when every file of the installed
  skill directory equals that source, after which the supervisor pins it.
  Without that source at `HEAD`, no `regenerate` is emitted. When the installed
  skill is tracked in the work tree, the controller commits the regenerated
  skill; until it does, `next` answers `uncommitted-changes`, and the next
  issuance first confirms that the committed installed skill equals what was
  admitted, and refuses `supervisor-changed` when it does not.
- [ ] **AC-0017.** Under an `untrusted` code-trust classification with no Slice 1
  verified containment, `next` emits no `run-gates` or `regenerate` request and
  the supervisor launches no red proof or scratch receipt; `next` emits a
  `human-decision`
  naming re-approval as `trusted` or supplying containment.

Result facts and grants

- [ ] **AC-0018.** Every row of the Result acceptance table returns its stated
  result.
- [ ] **AC-0019.** Every process the supervisor launches runs through the Slice 1
  safe-process primitive with its launch kind's grant from the Launch grants
  table recorded in its `safe-process.v1` record.
- [ ] **AC-0020.** A launched process's environment holds only its row's
  allowlisted variables.

Windows

- [ ] **AC-0021.** On Windows, a launched process is created suspended, assigned
  to a Job Object that denies breakaway and ends every member when its last
  handle closes, and only then resumed.
- [ ] **AC-0022.** On Windows, any failure to create, configure, or assign the
  Job Object refuses the launch with `denied-job-object` and ends the process.
- [ ] **AC-0023.** On Windows, a timeout terminates the job explicitly, and no
  descendant survives, including descendants of an exited intermediate process
  and a child that requested breakaway.
- [ ] **AC-0024.** On Windows, the launch branch passes the `safe-process.v1`
  contract suite, and a child does not inherit an inheritable handle the parent
  opened other than its standard streams.

POSIX

- [ ] **AC-0025.** On POSIX, the safe-process suite present at the merge-base
  with `main` when this spec's first task starts passes unchanged.

## Follow-ons

none

## Terminal Intent

`code` — implement the attempt checks, residue, Git hardening, pinning and
regeneration, grants, the untrusted launch gate, and the Windows Job Object
branch.

## Accepted Risk

Worker attempts are host subagents that this spec never contains, in any trust
mode. A deliberate worker can therefore act with the supervisor's full
same-user authority: it can rewrite the files it is checked against, write
outside the execution root, write ignored files that later gates read, and use
the network. The attempt checks catch naive writes to trusted files, Git control
state, and `delivery/` only. A naive worker's writes to ignored files elsewhere
in the execution root, and to the supervisor's local caches (the journal,
`run.json`, `security-events.jsonl`, and `.loop-run/`), are not caught; the
caches carry no authority, so such writes can mislead status displays only.
Network denial and write roots for supervisor-launched processes are enforced
only under Slice 1 verified containment. The Platform Core decision-maker
accepted the deliberate-worker portion of this risk on 2026-10-12 and the
naive-worker portion on 2026-10-12.

## Assumptions

none
