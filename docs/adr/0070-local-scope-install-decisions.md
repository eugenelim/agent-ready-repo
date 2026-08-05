# ADR-0070: Local scope install — `.git/info/exclude` exclusion, whole-install abort, per-worktree keyed blocks, and deferred concurrent-write lock

- **Status:** Accepted
- **Date:** 2026-08-04
- **Decision-makers:** eugenelim
- **Consulted:** adversarial-reviewer (25 passes on RFC-0080)
- **Supersedes:** none
- **Related:** RFC-0080, ADR-0002 (install scope per pack), ADR-0039 (install identity and footprint)

## Decision summary

- **Decision:** We will implement `--scope local` using `.git/info/exclude` for git
  exclusion (not `.gitignore`), abort the whole install on any tracked-file collision,
  key exclude blocks to `(pack, worktree-id)` pairs for multi-worktree safety, and
  defer file-locking to a follow-on release.
- **Because:** `.git/info/exclude` is never committed, is per-clone, and is the only
  exclusion mechanism that satisfies the "no git-visible side-effect" invariant for a
  local-scope install.
- **Applies to:** `agentbundle install --scope local`, `uninstall --scope local`, and
  any future subcommands that read or modify local-scope state.
- **Tradeoff accepted:** Concurrent writes by two agentbundle processes share a
  whole-file replacement strategy with no lock; the last writer wins (lost-update
  race documented but not prevented in v1).
- **Revisit if:** A user report demonstrates real data loss from the concurrent-write
  race; or a subcommand needs to accept `--scope local` alongside `--profile` (current
  guard already refuses this, but a future spec amendment could reopen the question).

## Context

RFC-0080 introduced `--scope local`: install pack files at the same working-tree
paths as `--scope repo`, but keep them invisible to git so they never appear in
`git status`, are never committed, and leave no trace after uninstall. The primary
use case is trialling a pack in a repo you don't own or haven't permanently adopted.

Implementing this requires four distinct architectural decisions, each with at least
two plausible alternatives. RFC-0080 researched and modelled each one before
implementation began. This ADR records the chosen options and their rationale.

Key constraints that shaped all four decisions:

- **No committed file.** Nothing written by `--scope local` may appear in
  `git status` or be committable. Corollary: the exclusion mechanism itself must
  not be a committed file.
- **Per-clone isolation.** Local installs are per-clone, not per-user. They must
  survive branch switches and `git stash` without becoming visible.
- **Atomic writes.** `os.replace` (POSIX-atomic, near-atomic on NTFS) is the only
  safe write mechanism for files that another process might read concurrently.
- **Multi-worktree correctness.** `git worktree add` creates linked worktrees that
  share the same `.git/info/exclude` file. An exclude block that doesn't identify its
  source worktree would be ambiguous and impossible to strip correctly on uninstall.

## Decision

### D1 — Use `.git/info/exclude`, not `.gitignore`, for per-file git exclusion

> We will resolve the exclude-file path via `git rev-parse --git-path info/exclude`
> and write all local-scope exclusions there. We will never write to `.gitignore`.

`.git/info/exclude` is the per-clone, per-working-tree exclusion file. It is never
committed, is not shared between clones, and is ignored by `git status` itself (its
own path is outside the working tree). `.gitignore` entries are committed, shared
across all clones, and appear in `git diff --stat` until committed — the opposite of
what a local-scope install requires.

The path is resolved via `git rev-parse --git-path info/exclude` rather than
hard-coded as `.git/info/exclude`. In both primary and linked worktrees, this
command resolves to the **common-dir** exclude file (i.e. `.git/info/exclude`
under the main repository's `.git/` directory), not a per-worktree variant.
This is because git routes `--git-path` for `info/exclude` through the common
directory even when run from a linked worktree, making the resolved path
identical from any worktree. The command also handles submodules correctly.
The per-worktree discriminant needed for block attribution is provided by D3's
keyed-block design, not by writing to separate files.

The file is created on first write if absent (it is optional in a fresh repo).
Writes are always atomic: read → modify in memory → write to a temp file in the same
directory → `os.replace`.

### D2 — Abort the whole install when any target file is already tracked by git

> We will check every target file for git-tracked status before writing any of them.
> If any file is tracked, the whole install aborts with no partial writes.

A partial install (some files written, some refused) is worse than no install:
it is hard to reason about, hard to undo, and can leave the repo in a state where
`git status` shows unexpected deletions or modifications. An atomic "all or nothing"
contract is simpler to communicate and to implement.

The check runs as a pre-flight step using
`git --literal-pathspecs ls-files --error-unmatch <path>` on every target path
(`--literal-pathspecs` prevents pathspec syntax in filenames from matching
unrelated tracked files). Exit 0 → tracked;
exit non-zero → untracked. On any tracked file, the install is refused before any
files are written.

The refusal message names all tracked files (not just the first) so the user can
decide whether to `git rm --cached` them before retrying.

### D3 — Key exclude blocks to `(pack-name, worktree-id)` pairs

> We will write exclude blocks with a structured comment key:
> `# agentbundle:local:<pack>:<worktree-id>:{begin,end}`.
> The worktree-id is derived at install time and stored only in the block key itself.

`.git/info/exclude` is shared across all linked worktrees of the same repository
(the primary worktree and all `git worktree add` clones share the same common-dir
`info/exclude`). Without a worktree discriminant, two different worktrees installing
the same pack would write overlapping blocks, and uninstall in one worktree would
strip the other's block.

The worktree-id is derived by comparing `git rev-parse --git-dir` and
`git rev-parse --git-common-dir`:
- Equal → primary worktree; use a stable sentinel derived from the common-dir path
  (e.g. a short hash of the absolute path) so the key is deterministic.
- Unequal → linked worktree; use the last component of `--git-dir` (the name git
  assigned under `.git/worktrees/`).

Sanitization: the id must not contain `:` (the block-key delimiter). Any `:` is
replaced with `_`.

The block key is the only identity mechanism: no external registry, no state-file
field, no cross-file reference. Pack names are `[a-z0-9-]+` per `pack.schema.json`;
the worktree-id after sanitization is also URL-safe. Together they are sufficient to
identify, locate, and strip a block without ambiguity.

Block format (canonical):
```
# agentbundle:local:<pack-name>:<worktree-id>:begin
/.agentbundle-local-state.toml
/.claude/skills/<pack-slug>/SKILL.md
# agentbundle:local:<pack-name>:<worktree-id>:end
```

Rules:
- Leading `/` anchors patterns to the repo root (same behaviour as `.gitignore`).
- Each path is gitignore-metacharacter-escaped before writing (`[`, `]`, `*`, `?`,
  and `\` are backslash-escaped; `#`/`!` need not be escaped because the leading `/`
  anchor prevents them from appearing at line start) so that projected filenames
  containing gitignore pattern syntax are matched literally.
- If a block for this `(pack, worktree-id)` already exists, it is replaced in place
  (no duplicate accumulation).
- Blocks from different worktrees coexist; each is stripped only by its own
  `(pack, worktree-id)` uninstall.
- Stale blocks (from deleted worktrees) accumulate in `info/exclude`. They are **not**
  harmless: their patterns continue to apply in all linked worktrees that share the
  common-dir `info/exclude`. A stale block can silently hide a tracked or committed
  file in another worktree. Pruning deferred to a follow-on `agentbundle local prune`
  CLI; risk must be documented in the `write_exclude_block` docstring.

### D4 — Defer file locking on `.git/info/exclude` to a follow-on release

> We will not add a file lock in v1. Concurrent writes use whole-file atomic
> replacement (`os.replace`); a lost-update race is possible when two agentbundle
> processes write simultaneously. This is documented and accepted as a v1 limitation.

A POSIX advisory lock (`fcntl.flock`) would serialize concurrent writers.
The cost: complexity in the write path, platform divergence (Windows `msvcrt.locking`
vs. POSIX `flock`), and a non-trivial test surface.

The lost-update scenario requires two agentbundle processes to simultaneously write
to the same `.git/info/exclude`. In practice this is rare: `agentbundle install`
is a CLI command typically run by one developer at a time. The risk-adjusted cost
of the race is low relative to the implementation cost of a correct cross-platform
lock in v1.

`os.replace` is POSIX-atomic (the kernel guarantees the rename is atomic) and
near-atomic on NTFS (the replacement is visible to other processes either before or
after, never as a torn write). This eliminates the corruption scenario; only the
lost-update scenario remains.

The follow-on specification for concurrent-write locking should evaluate whether
`filelock` (a small, cross-platform advisory-lock library) is an appropriate
dependency, or whether the POSIX `fcntl`-based approach is sufficient given the
actual platform mix of agentbundle users.

## Decision drivers

- **No committed file.** The exclusion mechanism must not appear in `git status`.
  Eliminates `.gitignore` for D1.
- **Atomic writes.** File writes must be resilient to concurrent reads.
  Drives `os.replace` for all writes; drives D4's deferred-lock acceptance.
- **Multi-worktree correctness.** Blocks must be attributable to a specific
  worktree so uninstall strips only the correct block.
  Drives the keyed-block design in D3.
- **Simplicity over completeness.** v1 should ship a correct, tested, minimal
  implementation. Concurrency handling beyond `os.replace` is deferred.
  Drives D4.
- **User experience.** A partial install is harder to recover from than a clean
  refusal. Drives the abort-on-any-collision policy in D2.

## Consequences

**Positive:**

- Local-scope installs leave no git-visible trace; `git status` is clean before
  and after install/uninstall cycles.
- Multi-worktree safety is guaranteed at the data-model level (block keys), not by
  runtime coordination.
- Whole-install atomicity (D2) means the repo is always either fully installed or
  unmodified.
- The `os.replace` write path is already used by agentbundle for `.agentbundle-state.toml`;
  no new platform abstraction is needed.

**Negative:**

- Stale blocks accumulate in `.git/info/exclude` when worktrees are deleted without
  uninstalling. They are **not** harmless: their patterns continue excluding same-path
  files in all linked worktrees sharing the common-dir `info/exclude`, potentially
  hiding a tracked or committed file added later in another worktree. A future
  `agentbundle local prune` command could clean them; deferred. The risk is documented
  in the `write_exclude_block` docstring (AC26/AC27).
- The lost-update race (D4) can result in one process's block being silently overwritten
  by another. Users running parallel `agentbundle install` processes will need to
  re-run the losing install. Unlikely in practice; documented.
- `.git/info/exclude` is not visible to `git status` itself, so users cannot
  directly inspect it via normal git UX. They can read the file, or run
  `agentbundle list-installed --scope local` for the agentbundle-managed view.

**Revisit if:**

- A user report demonstrates real data loss (not just inconvenience) from the
  concurrent-write race in D4.
- A future subcommand needs `--scope local` alongside `--profile`; the current
  pre-flight guard (`:162-165`) would need amending.
- `git rev-parse --git-path info/exclude` begins resolving differently for linked
  worktrees in a future git version (currently stable across git ≥2.5).

## Confirmation

- **Mode:** architecture fitness test + reviewer-checked
- **Signal:**
  - `python3 -m pytest packages/agentbundle/tests/ -q` green with the
    integration test (T11 in `plan.md`) exercising the full install/uninstall cycle.
  - The integration test asserts: (a) specific files exist on disk after install,
    (b) `git status --short` is empty, (c) the keyed block is in `info/exclude`,
    (d) `git status --short` is empty after uninstall, (e) the block is gone.
  - Adversarial reviewer confirms no new site in `install.py` uses a
    `plan.scope == "repo" else` ternary without being documented in RFC-0080's
    threading section.
- **Owner:** eugenelim

## Alternatives considered

### D1 alternatives

- **`.gitignore`** — Rejected. `.gitignore` is a committed file; adding entries to it
  via `agentbundle install` would produce `git status` output (the modified
  `.gitignore`), directly violating the no-visible-trace requirement.
- **`git update-index --assume-unchanged`** — Rejected. This marks a tracked file
  as unchanged, not an untracked file as ignored. It is the wrong primitive for
  new files that should never be tracked at all. It also has surprising interactions
  with `git stash` and `git checkout`.
- **`git update-index --skip-worktree`** — Rejected for the same reason as
  `--assume-unchanged`; both operate on already-tracked files.

### D2 alternatives

- **Partial install (skip tracked files, write the rest)** — Rejected. Leaves the
  repo in an inconsistent state. The user's intent was to install the full pack; a
  silently partial install is harder to diagnose than an explicit refusal.
- **Overwrite tracked files** — Rejected. Would produce visible modifications in
  `git status` (the tracked files would show as modified), violating the invariant.
- **Warn and continue** — Rejected. Same problem as partial install; the risk of
  undetected inconsistency outweighs the convenience.

### D3 alternatives

- **Single-worktree assumption (no worktree-id in block key)** — Rejected. Any repo
  with `git worktree add` would accumulate overlapping blocks from different
  worktrees; uninstall from one would silently break the other's exclusion.
- **External registry (a separate file mapping worktree-id to block ranges)** —
  Rejected. Introduces a second file to keep in sync with `info/exclude`, a second
  failure mode (registry and exclude diverge), and a second write requiring
  coordination. The block key is self-describing.
- **Per-worktree state only (no shared exclude file)** — Rejected. The `info/exclude`
  in a linked worktree under `.git/worktrees/<name>/` is a separate file from the
  primary worktree's `info/exclude`. Writing only to the per-worktree file would
  mean local installs in linked worktrees are invisible from the primary worktree's
  perspective. The shared common-dir `info/exclude` is the correct single location;
  the block key is the per-worktree discriminant.

### D4 alternatives

- **`fcntl.flock` (POSIX advisory lock)** — Deferred, not rejected. Correct and
  efficient on POSIX; not available on Windows (`fcntl` is POSIX-only). A
  cross-platform lock would need `msvcrt.locking` on Windows or a third-party
  library such as `filelock`. Cost is real; defer until a user report justifies it.
- **`filelock` library (cross-platform)** — Deferred. Would be the preferred
  approach if locking is added in a follow-on release; avoids platform branches.
  Not added in v1 to avoid a new dependency (per the repo's Dependencies are
  forever constraint in `AGENTS.md`).

## References

- RFC-0080 — canonical authority for all design decisions recorded here
- ADR-0002 — install-scope is a per-pack default + allowance
- ADR-0039 — install identity is the content-addressed footprint
- `docs/specs/local-scope-install/spec.md` — acceptance criteria and boundaries
- `docs/specs/local-scope-install/plan.md` — implementation tasks and rollout
