# Spec: worktree-runtime-hygiene

- **Status:** Implementing
- **Owner:** repository maintainers
- **Plan:** [`plan.md`](plan.md)
- **Contract:** none <!-- no REST/event/RPC surface; the `scan --json` shape is a command-output contract held in code and tests, not a published interface -->

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

Make parallel worktrees deterministic and safe to inspect and selectively clean.
Byte counts are diagnostic, never a disk-reclamation promise. The disk emergency is
over; its pressure previously caused browser-cache evictions, broken environment
state, and silently skipped tests unrelated to the actual space problem.

## Acceptance Criteria

- [x] **AC1 — scan has one authoritative worktree model.** `scan` discovers only
  `git worktree list --porcelain -z` records, including bare, detached, and prunable
  records, and emits deterministic human and JSON (`schema_version`, repository,
  git_common_dir, measurement, agentbundle_import, worktrees, shared_caches, warnings,
  totals) output.
  Paths with spaces and non-ASCII text are preserved. It performs one bounded,
  non-link-following traversal per present worktree, classifying candidates as it
  walks rather than rewalking per category.

- [x] **AC2 — byte output is honest.** Candidate byte counts use allocated blocks
  when `st_blocks` exists and logical size otherwise; the selected measurement is
  labelled. Sparse files and clones therefore do not become an unqualified
  "reclaimable" claim. Human output is a compact per-worktree category table,
  followed by shared storage and only the largest candidates.

- [x] **AC3 — scan diagnoses, but does not mutate, shared state.** It reports
  Playwright browser-path mode, local `.local-browsers`, duplicate browser revisions,
  npm cache placement, and worktree-local shared-cache resolution. It reports
  registered prunable records; it never removes worktrees, branches, browser caches,
  or arbitrary temporary-looking roots.

- [x] **AC4 — clean defaults to a receipt-only dry run.** `clean` deletes nothing
  unless both `--apply` and one or more category switches are supplied. Expensive
  dependency cleanup additionally requires `--include-dependencies`. There is no
  all/force option. Unlike repository-wide `scan`, `clean` defaults to the current
  worktree and accepts at most one explicit `--worktree`. Its kebab-case category
  switches and safety options are described by `clean --help`. The receipt names
  selected and skipped candidates, reasons, measurable bytes, failures, and remaining
  largest candidates.

- [x] **AC5 — every deletion has a bounded safety proof.** Before deletion the tool
  proves a known-model candidate is inside a selected registered worktree without a
  resolving link escape; rejects common-dir and `.git` administration paths, tracked
  files, non-ignored paths, `.loop-run`, `.context`, locks/leases, caller-protected
  worktrees, and paths that an installed distribution currently resolves into; then
  prints the exact target and bytes. Ignore and tracked checks are batched once per
  worktree. Common-directory discovery and path-taking Git-control failures fail
  closed, Git pathspecs are literal, and mount points are rejected. The current
  worktree is protected from expensive cleanup; callers may repeat
  `--protect-worktree` and supply protection roots through the environment.
  Attachment is never labelled liveness or activity: liveness is unobservable without
  that explicit handshake. The complete local safety predicate is re-run immediately
  before each deletion, narrowing but not eliminating the concurrent-mutation window.
  Git query failures reject the whole worktree rather than becoming negative answers.
  `__pycache__` is a correctness cleanup because stale bytecode can violate CAT-V-014
  during a run.

- [ ] **AC6 — round 2: concurrent operations are explicitly leased.** The second
  implementation task adds a caller-selected preview-port override and a gate wrapper
  that leases it without binding the shared default port. It also adds the cooperative
  worktree lease shared by cleanup and mutating build/test entry points; only that
  shared lease can close the remaining check-to-delete concurrency window completely.

- [x] **AC7 — round 2: bootstrap and browser cache choices remain explicit.** The
  second implementation task adds a browser-cache resolver and selective bootstrap
  profiles without shared mutable dependencies, symlinked virtualenvs, or automatic
  background work.

- [x] **AC8 — scan measures agentbundle import resolution.** `scan` runs exactly
  one isolated child process with the worktree `PYTHONPATH` stripped, the cwd
  `sys.path` entry removed (`-P`), and bytecode writes disabled, never comparing
  versions. It reports the resolved `__file__` and provenance (interpreter, cwd, and
  removed environment inputs) in both JSON and human output, with status invariant
  across invocation directories. If discovery fails or no registered worktree
  contains the invocation directory, it reports that fact as inconclusive without
  running the child. A path outside the current worktree is reported only as that
  fact; an absent, failed, timed-out, or unparseable probe is explicitly reported as
  absent or inconclusive rather than silently passing.

- [x] **AC9 — browser-gate failure evidence has a bounded lifecycle.** The
  Playwright configuration retains `trace: 'retain-on-failure'` and
  `screenshot: 'only-on-failure'`; the gate wrapper never weakens either diagnostic.
  It immediately removes successful-run `web/test-results/` and
  `web/playwright-report/` artifacts, copies each failed run into ignored,
  current-worktree-local evidence storage while retaining the live
  `web/test-results/` output for CI, and keeps the newest failed run by default.
  Retention orders lifecycle-owned `failed-<time_ns>` archives by that explicit
  creation time rather than copied source metadata, and runs after a successful
  archive so the new failure participates immediately. Older unpinned retained runs
  expire by the configurable
  `PLAYWRIGHT_FAILURE_EVIDENCE_MAX_AGE_SECONDS` age budget (seven days by default);
  a non-symlink `.pinned` marker (file or directory) preserves explicitly pinned
  evidence. Every lifecycle mutation
  re-establishes the same registered-current-worktree safety predicate immediately
  before acting and refuses an inconclusive worktree, so it never touches another
  worktree. If the live failure-output path changes, the Pages workflow upload
  contract (`browser-gate-failure`, seven-day retention, ignore when absent) and its
  contract tests change in the same commit.

- [x] **AC10 — optional lifecycle hooks report without removing.** The
  `after-create`, `before-run`, `after-run`, and `before-remove` commands work with
  plain Git worktrees and have no Orca dependency. They report Git-backed prune-signal,
  currently-active, default-branch-merged, and no-merge-or-prune-signal worktrees.
  The latter is an observation only: it does not infer activity or liveness.
  Currently-active means only the registered worktree containing the invocation
  directory, not liveness. Default-branch discovery comes from Git; when it cannot be
  determined, the merged result is explicitly undetermined. If an attachment
  observation is ever reported, it is named `attached`, never live, active, or busy.
  A prune signal is an administrative observation, not a claim that the path is
  absent.
  `before-remove` calls AC8's isolated import-resolution check and refuses outside,
  absent, or inconclusive resolution, because none proves that removing the worktree
  is safe. It also honours the existing repeatable `--protect-worktree` and
  `WORKTREE_HYGIENE_PROTECT_WORKTREES` input. No lifecycle command removes a
  worktree, directory, or branch.

## Limitations

Linux same-filesystem bind-mount detection uses one `/proc/self/mountinfo` snapshot for
selection and a fresh snapshot for each candidate immediately before deletion. Unit
tests cover mount-table parsing, mount-predicate propagation, and cross-device
boundaries, but no privileged fixture creates a genuine bind mount. A mount
created after that final re-assertion and before recursive deletion completes remains
unobservable without the cooperative lease deferred to round 2.

## Boundaries

**Never do**

- Infer a worktree from its directory name, infer activity from a pty, or follow
  symlinks/junctions while walking or deleting.
- Hash file content, invoke Git once per file, run `git check-ignore` once per
  candidate, or emit one confident clone-inflated reclaimable total.
- Remove a worktree, branch, Playwright cache, arbitrary path, `/private/tmp` root,
  or state outside a registered selected worktree.
- Change installation configuration, bind port 4321, add a dependency, or start
  round 2 in this implementation task.

## Testing Strategy

Real `tempfile` fixtures exercise scan, clean, and lifecycle-hook guards. A fake
subprocess runner supplies Git porcelain and batched responses and proves Git
calls are bounded by worktree count; a traversal counter proves one walk per
worktree. Mutations remove
each guard and must make its named falsification case fail. Python formatting, type,
and focused pytest gates are run by the supervisor only.

## Assumptions

1. Git is available when the command is invoked; scan reports a command failure
   rather than inventing a directory-based fallback.
2. Registered worktree paths are the only deletion roots; missing prunable paths are
   report-only records.
3. The environment protection variable is path-separator-delimited and is additive
   to repeated command-line protection roots.

## Known residual: preview-port probe TOCTOU

Alongside task 1's deferred cleanup TOCTOU, port selection retains one bounded race.
Participating gate wrappers are coordinated by the shared lease, but the availability
probe closes before Astro binds. An unrelated machine-local listener can therefore
take the selected port during that interval. The wrapper does not claim an absolute
reservation guarantee, and handing a bound socket to Astro is outside this scope.

A second, pre-existing case shares that boundary. `_run_child` reaps the child's
process group on its interrupt paths but not after a normal `wait()`, and the lease is
released as soon as the child returns. A gate command that backgrounds the preview
server and exits zero therefore leaves a descendant holding the port after release, so
a peer worktree can lease it and collide. This is task 2's shipped behaviour, unchanged
by the evidence-lifecycle work, which restored that original release ordering after
briefly holding the lease across archival. Closing it means reaping the process group on
the normal-exit path too, which is a change to shipped port-lease behaviour and belongs
with AC6's cooperative lease rather than here.
