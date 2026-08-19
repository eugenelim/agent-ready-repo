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

- [ ] **AC1 — scan has one authoritative worktree model.** `scan` discovers only
  `git worktree list --porcelain -z` records, including bare, detached, and prunable
  records, and emits deterministic human and JSON (`schema_version`, repository,
  git_common_dir, measurement, worktrees, shared_caches, warnings, totals) output.
  Paths with spaces and non-ASCII text are preserved. It performs one bounded,
  non-link-following traversal per present worktree, classifying candidates as it
  walks rather than rewalking per category.

- [ ] **AC2 — byte output is honest.** Candidate byte counts use allocated blocks
  when `st_blocks` exists and logical size otherwise; the selected measurement is
  labelled. Sparse files and clones therefore do not become an unqualified
  "reclaimable" claim. Human output is a compact per-worktree category table,
  followed by shared storage and only the largest candidates.

- [ ] **AC3 — scan diagnoses, but does not mutate, shared state.** It reports
  Playwright browser-path mode, local `.local-browsers`, duplicate browser revisions,
  npm cache placement, and worktree-local shared-cache resolution. It reports
  registered prunable records; it never removes worktrees, branches, browser caches,
  or arbitrary temporary-looking roots.

- [ ] **AC4 — clean defaults to a receipt-only dry run.** `clean` deletes nothing
  unless both `--apply` and one or more category switches are supplied. Expensive
  dependency cleanup additionally requires `--include-dependencies`. There is no
  all/force option. Unlike repository-wide `scan`, `clean` defaults to the current
  worktree and accepts at most one explicit `--worktree`. Its kebab-case category
  switches and safety options are described by `clean --help`. The receipt names
  selected and skipped candidates, reasons, measurable bytes, failures, and remaining
  largest candidates.

- [ ] **AC5 — every deletion has a bounded safety proof.** Before deletion the tool
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

- [ ] **AC7 — round 2: bootstrap and browser cache choices remain explicit.** The
  second implementation task adds a browser-cache resolver and selective bootstrap
  profiles without shared mutable dependencies, symlinked virtualenvs, or automatic
  background work.

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

Real `tempfile` fixtures exercise scan and clean guards. A fake subprocess runner
supplies Git porcelain and batched responses and proves Git calls are bounded by
worktree count; a traversal counter proves one walk per worktree. Mutations remove
each guard and must make its named falsification case fail. Python formatting, type,
and focused pytest gates are run by the supervisor only.

## Assumptions

1. Git is available when the command is invoked; scan reports a command failure
   rather than inventing a directory-based fallback.
2. Registered worktree paths are the only deletion roots; missing prunable paths are
   report-only records.
3. The environment protection variable is path-separator-delimited and is additive
   to repeated command-line protection roots.
