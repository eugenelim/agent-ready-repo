# RFC-0080: Local scope install

- **Status:** Accepted
- **Author:** eugenelim
- **Approver:** eugenelim
- **Date opened:** 2026-08-04
- **Date closed:**
- **Decision weight:** standard
- **Related:** [RFC-0004](0004-install-scope-per-pack.md) (install-scope per pack),
  [RFC-0005](0005-user-scope-hook-support.md) (user-scope hook support; defines force-merge as user-scope-only),
  [RFC-0008](0008-claude-plugins-install-route-parity.md) (Claude-plugins install-route parity),
  [RFC-0012](0012-repo-scope-per-adapter-projection.md) (repo-scope per-adapter projection; defines allowed-prefixes.repo)

## Reviewer brief

- **Decision:** Add `--scope local` to `agentbundle install`
  (agentbundle — the CLI that installs and manages packs; a pack is a bundle of
  agent skill files projected into a repo) — files land in the working tree
  (identical placement to `--scope repo`) but are excluded from git via
  `.git/info/exclude`, so a pack is usable in a session without touching any
  committed file.
- **Recommended outcome:** Accept.
- **Change if accepted:**
  - `LEGAL_SCOPES` in `scope.py` gains `"local"`; `allowed-scopes` pack schema
    gains `"local"` as a valid value; `"local"` is auto-allowed for any pack that
    allows `"repo"` (no existing `pack.toml` changes needed).
  - Install refuses if not inside a git working tree; resolves the exclude path
    via `git rev-parse --git-path info/exclude`; refuses if any target file is
    already tracked; appends a comment-delimited block to the exclude file.
    Uninstall removes working-tree files and strips the block.
  - New per-repo state file `.agentbundle-local-state.toml`, gitignored via the
    same block.
  - `_parse_adapter_row` in `config.py` is widened to source its scope allowlist
    from `LEGAL_SCOPES` rather than a hardcoded tuple, so `scope = "local"` rows
    are read correctly by the new binary.
- **Affected surface:** `agentbundle install`/`uninstall` CLI; `scope.py`
  (`LEGAL_SCOPES` + `resolve()` default-scope guard); `config.py`
  (`_parse_adapter_row` guard); `commands/_common.py` (`resolve_state_path`
  routing); `commands/list_installed.py` (three-scope default list; inline
  `if/else` routing must gain an explicit `local` branch); `commands/install.py`
  (substantial: new `local` branch in `_ScopePlan`-building loop at line 759;
  full site-by-site audit — see "install.py write-path threading" in Proposal
  for the complete fork-family enumeration including carve-outs and key sites; `--emit-install-routes + --scope local` refusal at
  `install.py:390`; `emit_install_routes` inference at line 258 — `cli_scope !=
  "user"` must become `cli_scope not in ("user", "local")` so local never infers the
  plugins-route producer; see implementation erratum in §4 of Proposal for the
  corrected form vs. the original `== "repo"` specification); `cli.py` (six hardcoded
  `choices=("repo","user")` sites at `cli.py` lines 261, 390, 525, 581, 630, 678);
  `pack.schema.json` (`allowed-scopes` `allOf` if/then constraint);
  `config.py:860` (`Literal["repo","user"]` type annotation on
  `load_adapt_discovery_typed` — a follow-on concern; not on the primary local
  write path, but must be widened if profile/adapt support is added later).
  `adapter.toml` does not change — local reuses the repo resolution path
  (`allowed_prefixes_repo` via the widened upstream gate at `install.py:513`);
  `safety.py:337` guards only `scope="user"`. No `pack.toml` changes needed for
  existing packs. Note: the `resolve()` local⇒repo invariant for the
  explicit-allowed-list case (when a pack names `["user","local"]` without
  `"repo"`) rests solely on the schema `allOf` gate — `resolve()` itself does
  not re-check it. Schema validation must precede `resolve()`; this ordering
  is the current behavior and must be preserved.
- **Stakes:** Reversible — `--scope local` installs can be undone; the scope can
  be deprecated without touching existing `repo`/`user` behaviour.
- **Review focus:** (1) The `.git/info/exclude` append/uninstall contract and
  its shared-across-worktrees behaviour. (2) The tracked-file collision detection
  and partial-overlap edge case.
- **Not in scope:** `.gitignore` writes; changes to pack content rules; user-scope
  equivalents; cross-clone persistence; per-pack ability to exclude `"local"` scope;
  `--scope local` for the claude-plugins adapter route (which uses
  `settings.local.json` as its target, not the working tree — a separate, untriggered
  problem).

## The ask

**Recommendation (BLUF — Bottom Line Up Front):** Accept a `--scope local`
install mode that installs pack files into the repo working tree and excludes
them from git via `.git/info/exclude`, so skills (Claude Code instruction files
installed to `.claude/skills/`) like `work-loop` (the implementation-loop skill)
can be used in any repo session without appearing in `git status` or being
committable.

**Why now (SCQA — Situation, Complication, Question, Answer):** Agent-ready-repo
(the open-source repo that publishes these packs) packs are useful in repos that haven't
permanently adopted them. Today's workarounds are `--scope user` (globally
persistent across all repos — wrong lifetime), `--scope repo` plus a manual
`.gitignore` entry (fragile; easy to forget; creates a diff), or
install-then-uninstall (files remain visible in `git status` during the session,
risking an accidental commit). A first-class local scope removes the last
friction on "try this in any repo without polluting its git history."

**Decisions requested:**

| ID | Question | Recommendation | Why | Decide by | Reviewer action |
|----|----------|----------------|-----|-----------|-----------------|
| D1 | What does `--scope local` mean? | Working-tree files + `.git/info/exclude` exclusion | Same placement as `repo`; semantically consistent with RFC-0008's "not committed, per clone" use of `local` | This review | Confirm scope definition |
| D2 | Git exclusion mechanism? | Append to `.git/info/exclude` via `git rev-parse --git-path` (comment-delimited; never duplicate) | Not committed; creates no working-tree diff; stdlib-only | This review | Confirm mechanism |
| D3 | State file location? | `<repo>/.agentbundle-local-state.toml`, itself gitignored via same block | Transparent; mirrors `.agentbundle-state.toml`; separate file means old agentbundle never reads it | This review | Confirm location |
| D4 | Must packs opt in via `allowed-scopes`? | No — auto-allowed for any pack that allows `"repo"`, unconditionally | `local` is a visibility modifier on `repo`, same content rules; no pack author burden; no per-pack exclusion in v1 | This review | Confirm or require opt-in |

## Problem & goals

**Problem.** Pack skills are most useful precisely in repos that haven't adopted
them — one-off sessions in an unfamiliar codebase, a contractor repo without
the `core` pack, a quick audit. The two existing scopes don't cover this:

- `--scope repo` makes pack files visible in `git status` and committable. Fine
  for long-term adoption; wrong for a session.
- `--scope user` installs to `~/.claude/` and follows the user globally. Wrong
  lifetime (the skill shows up in every repo, forever).

The manual workaround — install, add paths to `.gitignore`, work, uninstall,
restore `.gitignore` — is fragile and error-prone.

**Goals.**

- One flag (`--scope local`) installs a pack into the working tree, fully
  functional for the session, with no git footprint.
- Uninstall is clean: working-tree files removed, no residue in
  `.git/info/exclude`, no stale state file.

**Non-goals.**

- Changing what adapter-projected files a pack projects (local scope projects
  the same adapter-overlay files as repo scope — i.e. the files listed in
  `allowed-prefixes.repo`). Seeds (repo-root `AGENTS.md`/`docs/CHARTER.md`,
  written at `install.py:1254`), the install marker (`_append_install_marker`
  at `:1447`), and the layout section (`_append_layout_section` at `:1456`) are
  **not** delivered in `--scope local` installs: they land at the repo root
  outside `allowed_prefixes_repo`, which would surface them in `git status` and
  defeat the no-footprint goal. `:1254` is already gated by `plan.scope ==
  "repo"` and can be left unchanged; `:1447` and `:1456` are **unconditional
  calls** that require an explicit `if plan.scope != "local":` guard (see
  Proposal, Carve-outs).
- Supporting `.gitignore` writes (`.git/info/exclude` is the right mechanism;
  see Options considered).
- A `--scope local` equivalent for user scope.
- Cross-clone persistence: local-scope installs are intentionally per-clone.
- Per-pack ability to exclude `"local"` scope (no v1 denylist; see D4).
- `--profile … --scope local`: profile installs (`install.py:4331`, `:4357`)
  have their own scope-routing and an `opposite` scope computation that breaks
  for `local`. No new refusal guard is needed in v1 — `install.py:162-165`
  already refuses any `--scope` flag alongside `--profile`; once `cli.py:390`
  adds `"local"` as a valid choice, `--profile --scope local` hits that existing
  guard unchanged, and the `scope_value` computations at `:4331`/`:4357` are
  only reachable when no `--scope` was passed. Follow-on deferred.

## Proposal

### Scope definition (D1)

`--scope local` installs pack files to the same working-tree paths as
`--scope repo` (governed by the adapter's `allowed-prefixes.repo` list — the
adapter is the per-target-tool integration layer, e.g. `claude-code` or
`cursor`; `allowed-prefixes.repo` is its declared list of permitted filesystem
path prefixes for repo-scope writes) and additionally appends a
comment-delimited exclusion block to the repo's per-clone `.git/info/exclude`
file (not a `.gitignore`; uses gitignore syntax but is never committed). From
git's perspective the files don't exist.

**Naming note.** RFC-0008 (Accepted) uses the `local` token in the context of
the Claude-plugins install route to mean "listed in `settings.local.json`
(a gitignored Claude Code settings file not committed to the repo), not
committed." The semantics are consistent — both uses mean "visible to this
clone, not committed, not shared" — but the mechanisms differ. No CLI conflict
exists: RFC-0008's `local` is a keyword in the Claude-plugins adapter's own
scope taxonomy, distinct from the `agentbundle install --scope` flag.

### Git exclusion contract (D2)

**Pre-flight check.** Before any file write, agentbundle verifies it is inside
a git working tree:

```bash
git rev-parse --is-inside-work-tree
```

If this fails or returns `false`, install aborts with:
```
error: --scope local requires a git working tree; use --scope repo instead.
```

**Exclude path resolution.** agentbundle resolves the exclude file path via:

```bash
git rev-parse --git-path info/exclude
```

This returns the correct path for all repo configurations. Verified spike:
in a linked worktree (`philadelphia-v1`), the command returns the main repo's
`.git/info/exclude` — `info/exclude` is shared across all worktrees of the
same repo, not per-worktree. This is the expected git behaviour (only a subset
of `.git/` paths are per-worktree; `info/exclude` is not one of them). In a
submodule, `git rev-parse --git-path` resolves relative to the submodule's own
gitdir.

**Block format.** agentbundle derives a worktree identifier by comparing
`git rev-parse --git-dir` and `git rev-parse --git-common-dir` (equal →
primary worktree; the implementation spec must choose a reserved sentinel that
cannot be a user-assigned worktree name, such as a hash of the common-dir
path; unequal → linked worktree, id taken from the last component of
`--git-dir`). agentbundle appends a keyed block to the resolved file (creating
it if absent):

```
# agentbundle:local:<pack-name>:<worktree-id>:begin
/.agentbundle-local-state.toml
/.claude/skills/work-loop/SKILL.md
# agentbundle:local:<pack-name>:<worktree-id>:end
```

Paths are anchored with a leading `/` to match at repo root only, following
gitignore semantics for absolute paths. Each path is gitignore-metacharacter-escaped
before writing: `[`, `]`, `*`, `?`, and `\` are backslash-escaped. (`#` and `!`
need not be escaped because the leading `/` anchor ensures they can never appear at
line start.) This ensures that projected filenames containing gitignore pattern
syntax (e.g. `references/[draft].md`) are matched literally rather than as
character-class or glob patterns.
Because gitignore deduplicates equivalent patterns, multiple worktrees having
overlapping path entries is harmless.

**Block rules.**

- **Append-or-replace-in-place, never duplicate a `(pack-name, worktree-id)`
  block.** agentbundle reads the file first; if a block keyed to this pack name
  and worktree id already exists, it replaces it in place (e.g. when a second
  adapter is installed for the same pack — the block is rewritten with the union
  of both adapters' patterns). Otherwise it appends. Two different worktrees installing the same pack will
  have path entries that overlap — gitignore deduplicates patterns at match time;
  this is not a violation of the "no duplicate block" rule, which is
  per-`(pack-name, worktree-id)` pair.
- **One block per `(pack-name, worktree-id)` pair.** Multiple packs write
  independent named blocks; the same pack in different worktrees writes
  independent worktree-keyed blocks.
- **Uninstall strips only this worktree's block and removes its working-tree
  files.** Uninstall: (1) removes installed working-tree files (same as `repo`
  scope uninstall); (2) reads the exclude file, strips the `(pack-name,
  worktree-id)` block inclusive of markers, and writes back atomically via
  `os.replace` (write to a temp file in the same directory, then rename);
  (3) removes this pack's rows from `.agentbundle-local-state.toml`; deletes
  the file only when it becomes empty (mirrors how `repo`-scope uninstall
  removes rows rather than the whole state file). Install uses the same atomic
  mechanism (read → modify in memory → write to temp file → `os.replace`) so
  that all writes to `info/exclude` are full-file replacements, not in-place
  appends.
- **Stale blocks from deleted worktrees accumulate and require pruning.**
  When a worktree is deleted without uninstalling (e.g. Conductor deleting an
  ephemeral workspace), its block remains in `info/exclude`. The patterns in that
  block continue excluding same-path files in **all** linked worktrees that share
  the common-dir `info/exclude`. If a tracked or committed file is later created
  at that path in another worktree, git silently hides it — `git status` and
  `git add` do not see it. Cleanup is manual; the exact CLI surface
  (`agentbundle local prune` or equivalent) is deferred to a follow-on spec.
  The implementation must document this risk in a user-visible location
  (spec AC26/AC27; see `write_exclude_block` docstring).

**Tracked-file collision check.** Before writing any file, agentbundle runs
`git --literal-pathspecs ls-files --error-unmatch <path>` for each target path
(the `--literal-pathspecs` flag prevents pathspec syntax in filenames —
e.g. `foo[bar].md` — from being interpreted as a pattern and matching unrelated
tracked files). If any path is already tracked, the install aborts with:
```
error: <path> is already tracked by git; --scope local cannot shadow a
       committed file. Use --scope repo or remove the tracked file first.
```
The whole install aborts (no partial writes). This is conservative — see Risks
for the partial-overlap trade-off.

**Repo/local conflict detection.** If the same pack is already installed at
`--scope repo` in this working tree, `--scope local` refuses:
```
error: <pack> is already installed at --scope repo; uninstall it first or
       use --scope repo to upgrade.
```
The reverse direction — `--scope repo` install when a local install already
exists — is also refused:
```
error: <pack> is already installed at --scope local; uninstall it first
       (agentbundle uninstall --scope local), then reinstall.
```
This prevents a `--scope repo` install from writing files that the local
exclude block hides from `git status`, which would make a committed install
invisible to `git add`/`git commit`. `--scope user` installs land in
`~/.claude/` (outside the working tree) and are unaffected by the exclude
block, so user/local coexistence is allowed.

Both directions are **hard refusals, immune to `--force`**. The existing
cross-scope machinery at `install.py:668-684` is binary and `--force`-bypassable
(`if other_already and not force:`). Wiring `installed_at_local` into that path
would let `--scope repo --force` dual-install over a local install, writing
committed files hidden by the exclude block. The local cross-scope refusal must
be enforced before the `--force` check, outside the `scopes_to_install`
computation.

**Same-scope local reinstall.** The upgrade-offer guard at `install.py:631` is
`(requested_scope=="repo" and installed_at_repo) or (requested_scope=="user" and
installed_at_user)`. A `--scope local` reinstall of an already-local pack
matches neither disjunct. **Implementation erratum (see spec AC21b):** routing
through `upgrade.run` is incorrect for v1 because `upgrade.run` has no local-scope
support. Instead, `install.py:631` must refuse (adapter-identity check: refuse only
when the requested adapter row already exists in `local_state`) with a message
naming `agentbundle uninstall --scope local` then `install --scope local` as the
v1 refresh path. A second *different* adapter for the same pack must fall through
to the multi-adapter union-write path (AC14b).

**Multi-worktree support.** Because blocks are keyed per `(pack-name,
worktree-id)`, multiple worktrees can hold independent `--scope local` installs
of the same pack simultaneously, and each worktree's uninstall strips only its
own block. Ephemeral worktrees (e.g. Conductor workspaces) may be deleted without
uninstalling; their stale blocks accumulate. Stale blocks are **not harmless**:
see Block rules above for the data-loss risk (stale patterns continuing to hide
files in other worktrees).

**Important: exclusion patterns are repo-global.** The keyed blocks scope only
bookkeeping and uninstall — not git exclusion. A leading-`/` pattern in the
shared `info/exclude` file anchors to each worktree's own root, so worktree A's
install also suppresses those paths in worktree B. Consequence: the tracked-file
collision check (see above) only protects the installing worktree; if worktree B
has an untracked file at the same path that it intends to commit, A's
local-install block will silently git-ignore it in B. Users with multiple
active worktrees should be aware that `--scope local` affects git visibility
across all worktrees of the same repo.

**Concurrent-write limitation.** agentbundle does not hold a file lock on
`.git/info/exclude` during install or uninstall. Because both install and
uninstall use full-file atomic writes (`os.replace`), two simultaneous
operations produce a *lost update*: one writer's full-file replacement clobbers
the other's block, silently removing those pack files from the exclusion list
and making them git-visible and committable. The same race applies to
`.agentbundle-local-state.toml`. This is a known limitation; the implementation
must document it prominently. Locking is out of scope for v1.

### `_parse_adapter_row` guard (Blocker addressed)

`config.py:524-529` currently contains a hardcoded tuple `("repo", "user")` that
silently coerces unknown scope values to `default_scope` (the fallback scope
recorded in the state row when no valid scope is found). The new binary must
widen this guard to source from `LEGAL_SCOPES` (the frozenset in `scope.py`
listing all valid scope values; after this RFC it becomes `{"repo", "user",
"local"}`), so `scope = "local"` rows read from `.agentbundle-local-state.toml`
are preserved correctly. Concretely:

```python
# Before:
raw_scope if isinstance(raw_scope, str) and raw_scope in ("repo", "user") else default_scope
# After (single-source from LEGAL_SCOPES):
raw_scope if isinstance(raw_scope, str) and raw_scope in LEGAL_SCOPES else default_scope
```

This is a one-line change but is load-bearing for `list-installed` and any path
that reads the local state file.

### State file (D3)

Local-scope state lives in `<repo>/.agentbundle-local-state.toml`. Its schema is
identical to `.agentbundle-state.toml` (same `PackState` shape — the dataclass
recording which files a pack installed and their content hashes — same
`schema-version = "0.4"`) except all rows carry `scope = "local"`. The file is
included in the pack's exclusion block at install time and removed at uninstall.

**Backward compatibility.** Old agentbundle never enumerates
`.agentbundle-local-state.toml` — `resolve_state_path` in
`commands/_common.py` (the function that returns the canonical state-file path
for a given scope) currently routes any non-`user` scope to
`<root>/.agentbundle-state.toml`. This must be extended to route `"local"` to
`<root>/.agentbundle-local-state.toml`. A team member on an older binary sees
no effect (the new state file doesn't exist for them). No schema-version bump
is needed.

### `allowed-scopes` auto-promotion (D4)

`scope.resolve()` (the function that checks whether the requested scope is
permitted for a given pack) treats `"local"` as in-scope for any pack whose
`allowed-scopes` contains `"repo"`. No per-pack exclusion mechanism exists in
v1 — unconditional. The pack schema's `allowed-scopes` enum gains `"local"` as a valid explicit
value so a pack may enumerate it (e.g. `allowed-scopes = ["repo", "local"]`);
`default-scope` retains the `["repo", "user"]` enum and `"local"` is rejected
there. No existing pack needs to change.

`LEGAL_SCOPES` in `scope.py` is extended from `{"repo", "user"}` to
`{"repo", "user", "local"}`.

**Standalone `"local"` without `"repo"` is rejected.** A pack declaring
`allowed-scopes = ["local"]` (without `"repo"`) is invalid — `"local"` is a
visibility modifier on `"repo"` and has no meaning without it. Two enforcement
points are required:

1. **Schema rule.** `pack.schema.json`'s `[pack.install]` object already uses a
   single `if/then/else` block (default-scope=user ⇒ contains user; else
   contains repo). JSON Schema permits only one bare `if` per object; the new
   local⇒repo constraint must be added as an `allOf` sibling:
   `allOf: [{ if: { contains "local" }, then: { must also contain "repo" } }]`.
   Without this, `allowed-scopes = ["user", "local"]` passes existing schema
   validation and the auto-promote guard.

2. **`resolve()` guard.** Adding `"local"` to `LEGAL_SCOPES` would otherwise
   loosen the existing `pack_default not in LEGAL_SCOPES` check in `scope.py`,
   allowing `default-scope = "local"` to pass runtime validation. `resolve()`
   must gain an explicit check that runs **before** D4 auto-promotion:
   ```python
   # Illustrative — exact exception args/message to be determined by the spec
   if pack_default == "local":
       raise ScopeRefused(pack_name, "local", allowed_scopes)
   ```
   The `default-scope = "local"` reject must precede auto-promotion so a
   hand-edited pack.toml with `default-scope = "local"` and no `--scope` flag
   is caught before `"repo" in allowed` is evaluated.

**Claude-plugins install-route guard.** `claude-plugins` is an install-route
(not an adapter name); it is selected via the `--emit-install-routes` flag on
`agentbundle install`, which writes `settings.local.json` entries for the
`claude-code` adapter (see `contracts/adapter.toml:185`, `adapter.schema.json:240`).
`commands/install.py:390` currently binds the plugins route to
`requested_scope == "user"`; this check must also reject `scope = "local"` so
`--emit-install-routes --scope local` is refused at install time with a
scope-specific message (branched from the existing `--scope repo` error):
```
error: --scope local is not supported with --emit-install-routes.
       See RFC-0008 for the plugins route's own local-scope behavior.
```
The existing guard at `install.py:390-393` emits a single shared string;
widening it to cover `local` requires branching so the `local` path emits the
message above rather than the repo-scoped one. Uninstall, diff, upgrade,
list-installed, and init-state operate on state rows whose adapter is
`claude-code` (never a separate `claude-plugins` entry), so no additional guard
is needed in those subcommands. `commands/install.py` is the sole enforcement
point. This is a v1 decision; a future RFC may define the interaction.

### install.py write-path threading

`commands/install.py` is the most complex change in this RFC — it is a
two-valued `repo`/`user` machine at every level, and local must be threaded
through each layer:

1. **Upstream resolution gates.** `install.py:513` gates resolution of
   `allowed_prefixes_repo`, `repo_target_adapter`, and the repo projection
   on `requested_scope == "repo" and not emit_install_routes`. For a local
   request `requested_scope == "local"`, this block is skipped and
   `allowed_prefixes_repo` stays `None` — breaking the write-jail fence.
   This gate must become `requested_scope in ("repo", "local") and not
   emit_install_routes`. Similarly, `install.py:929` (`if any(p.scope ==
   "repo" ...)`) and `:950` (`any(p.scope == "user" ...)`) gate projection
   rendering; the repo aggregate must become `any(p.scope in ("repo",
   "local") ...)` so local plans produce a projection.

2. **`_ScopePlan`-building loop.** A new `local` branch at `install.py:759`
   must produce `_ScopePlan(scope="local", root=repo_root, state_path=
   <repo>/.agentbundle-local-state.toml, allowed_prefixes=allowed_prefixes_repo)`.

3. **Downstream fork audit.** `install.py` has six families of
   scope-branching sites — all must be audited:
   - **`requested_scope == "repo"/"user"` equality comparisons** (e.g. lines
     390, 397, 432, 486, 513, 577, 631, 663, 668, 739). Line 486
     (`repo_state if requested_scope == "repo" else user_state`) routes
     source-conflict checks; the `local` path must route to the new local
     state file. Lines 631 and 668 drive the "already installed" and
     cross-scope conflict checks — these currently only load
     `installed_at_repo`/`installed_at_user`; a new `local_state` load and
     `installed_at_local` flag must be derived so that the D4 repo/local
     refusal is actually enforced.
   - **`!= "user"` negation comparisons** — two sites, each needing different
     treatment:
     - `install.py:258` (`cli_scope != "user"`) — must become
       `cli_scope not in ("user", "local")` (see implementation erratum in
       point 4 — the originally-specified `== "repo"` breaks `None`-scope callers).
       Handled by point 4 below; only protects the test-fixture fallback.
     - `install.py:377` (`if force_merge and requested_scope != "user":`) —
       correctly refuses force-merge for every non-user scope; force-merge is
       user-scope-only (RFC-0005). This guard works for local as-is. **Do not
       change `!= "user"` to `== "repo"` here** — that would let
       `--force-merge --scope local` slip through and execute undefined
       behavior. If the implementer wants to be explicit, use
       `requested_scope in ("repo", "local")` to make the intent legible, but
       the behavior of the existing `!= "user"` is already correct.
   - **`scope_value == "repo"/"user"` comparisons** in the profile-install
     path (lines 760, 4331, 4357). All three are guarded by the v1 profile
     refusal (see Non-goals), but must be explicitly skipped or wired if
     profile support is added in a follow-on.
   - **`plan.scope == "repo"/"user"` and `p.scope == "repo"/"user"` forks**
     throughout the `_ScopePlan` processing loop (grep both variants).
   - **`X if plan.scope == "repo" else <user-variant>` ternaries** — the
     "else-implies-user" hazard, symmetric to the negation hazard above.
     These are the load-bearing sites that select which projection is actually
     written to disk: `install.py:1018`, `:1045`, `:1086` select
     `repo_projection if plan.scope == "repo" else user_projection`; `:859`
     and `:1093` select the adapter. For a `local` plan, all five default to
     the user branch. When a user-only install is not present `user_projection` is
     `None`; `install.py:1087-1088` coerces `None → {}`, so a missed ternary
     site yields a **silent zero-file install that reports success**. These
     five sites must use `plan.scope in ("repo", "local")` rather than a plain
     equality check. This silent-`{}` failure mode makes a missed ternary site
     undetectable without an integration test that asserts files were written.
   - **`any(p.scope == ...)` aggregates**: the `:929` repo aggregate is widened
     in point 1 (`any(p.scope in ("repo","local") ...)`); the `:950` user
     aggregate (`any(p.scope == "user" ...)`) must **stay user-only** — local
     plans must not enter user-projection rendering.
   **Carve-outs** — sites that must be adjusted so local scope is *excluded*,
   not widened:
   - `install.py:1060` — dry-run seed preview, gated by `plan.scope ==
     "repo"` — leave as-is (twin of `:1254`; correctly excludes local).
   - `install.py:1254` — seed delivery (root `AGENTS.md`/`docs/CHARTER.md`);
     already gated by `plan.scope == "repo"` — leave it as-is.
   - `install.py:1447` (`_append_install_marker`) and `:1456`
     (`_append_layout_section`) — **both are unconditional calls** (no
     existing `plan.scope == "repo"` guard). For a local plan both write
     root-level files outside `allowed_prefixes_repo`; `write_jailed` raises
     `PathJailError`, and the loop's `except` at `:1463` returns 1 — the local
     install cannot complete. The implementer must add an explicit scope guard
     wrapping both calls (e.g. `if plan.scope != "local":`) so they are skipped
     for local installs. Do *not* widen the per-prefix skip at `:2716`/`:2851`
     (those are `scope == "repo"` only by design).

   **Additional key sites** (add to the spec's individual enumeration):
   - `install.py:814` — `if plan.scope == "repo" and not plan.already_installed:`
     reloads state in `for_write=True` mode to fire the v0.1-format refusal.
     Leave repo-only; `.agentbundle-local-state.toml` is always new so the
     v0.1 reload is moot for local. Mark it explicitly "intentionally
     repo-only" so the spec's implementer doesn't treat it as a missed site.
   - `install.py:859` — `repo_target_adapter if plan.scope == "repo" else
     user_target_adapter` adapter-selection ternary (also counted in the fifth
     "else-implies-user ternary" fork family above; listed here for the `:863`
     warning-suppression detail). For a local plan resolves to
     `user_target_adapter` (None), suppressing the `_maybe_emit_dropped_warning`
     call at `:863`. Widen to `plan.scope in ("repo","local")`.
   - `install.py:1334` — `elif plan.scope == "repo" and repo_target_adapter is
     not None:` sets `new_pack_state.adapter`. A local plan matches neither
     this branch nor the user branch at `:1305`, so the local state row's
     `adapter` field is never populated — diverging from an equivalent repo
     install and causing `_parse_adapter_row`/`list-installed` to read back an
     empty adapter. Widen the condition to
     `plan.scope in ("repo","local") and repo_target_adapter is not None:`
     (the adapter is already resolved via the `:1093` / `:859` fix).
   - `install.py:1356` — compound condition `plan.scope == "repo" and
     state_relpath == ".agentbundle-state.toml"` skips the RFC-0012 prefix
     check so the root-level state write isn't blocked. The second conjunct does
     not match `.agentbundle-local-state.toml`, so the local state write would
     be blocked by the prefix check. Both conjuncts must be updated to accept
     the local state filename.
   - `install.py:1493-1543` (Step 13 emission loop) — has no `local` branch;
     a `local` plan falls through to a bare `installed: core @ local` without
     the mandated exclude-path suffix. A `local` branch must be added to emit
     `installed: <pack> @ local (excluded via <git-resolved exclude path>)`.
   - `install.py:1471-1477` (Step 12 `_chain_adapt`) — runs unconditionally;
     for `local` scope, chain-adapt should be **skipped** (local installs are
     ephemeral; adapt-discovery re-running would apply to files the user
     considers invisible). The comment at `install.py:1468` records AC19b as
     "invoke … regardless of the install scope (markers are repo-only)";
     skipping for local is a deliberate amendment to AC19b — the derived spec
     must record this change explicitly rather than silently diverging from it.

4. **`emit_install_routes` inference.** `install.py:258` (`emit_install_routes
   = cli_scope != "user"`) must become `cli_scope not in ("user", "local")` so
   local never silently enters the plugins-route producer. **Implementation
   erratum:** the RFC originally specified `cli_scope == "repo"` here, but that
   value breaks programmatic/legacy callers that pass a `Namespace` without an
   explicit `scope` attribute (`None == "repo"` is `False`, misrouting them from
   the repo-dist-tree path to adapter projection). The correct expression is
   `cli_scope not in ("user", "local")` so that `None` is treated as repo-like,
   matching the historical behavior. The primary guard is the explicit refusal at
   `install.py:390-393`.

### CLI surface

`cli.py` currently hardcodes `choices=("repo","user")` at six argparse sites.
Three accept `local` in v1; three refuse it:

| `cli.py` line | Subcommand | v1 treatment |
|---|---|---|
| 261 | `list-installed` | add `"local"` |
| 390 | `install` | add `"local"` |
| 525 | `diff` | **leave as `("repo","user")`** — argparse-native rejection |
| 581 | `upgrade` | **leave as `("repo","user")`** — argparse-native rejection |
| 630 | `uninstall` | add `"local"` |
| 678 | `init-state` | **leave as `("repo","user")`** — argparse-native rejection |

For the three that accept `local`, source `choices` from
`tuple(sorted(LEGAL_SCOPES))` rather than duplicating the tuple, resolving
the pre-existing single-sourcing drift the `scope.py:44-45` comment notes but
does not enforce. The sorted-tuple form (not the bare frozenset) is required so
`--help` and error messages render in stable, deterministic order across Python
versions and `PYTHONHASHSEED` values — consistent with how
`shipped_adapters_from_contract()` returns a sorted tuple at `scope.py:247-256`.
The three refused sites **retain** `("repo","user")` so argparse rejects
`--scope local` natively, giving users a consistent error without a runtime guard.

Per-subcommand behavior for `--scope local` (v1):

| Subcommand | Accepts `local`? | Notes |
|---|---|---|
| `install` | Yes | Primary use case |
| `uninstall` | Yes | Removes local-scope install |
| `list-installed` | Yes | Filters output to local scope |
| `diff` | **No — refused** | `diff.py` has its own `== "user"` routing; follow-on |
| `upgrade` | **No — refused** | `upgrade.py` has its own state-routing; follow-on |
| `init-state` | **No — refused** | `init_state.py` hardcodes `.agentbundle-state.toml`; follow-on |

`diff`, `upgrade`, and `init-state` each have their own inline scope-routing that
does not go through `resolve_state_path` and would silently misroute a `local`
request to the repo state file. v1 refuses `--scope local` on these three
subcommands with:
```
error: --scope local is not yet supported for this subcommand.
       Install, uninstall, and list-installed are fully supported.
```
**Implementation erratum (see spec AC25):** the argparse-native `invalid choice:
'local'` mechanism (retaining `("repo","user")` as the choices list) is the v1
refusal; the friendly message above is reserved for a future custom argparse action
if the UX is revisited. The net user-visible behavior is the same, but the error text
in v1 will be argparse's own wording, not the string above.
Threading `local` through `diff.py` (`:85,102,183`), `upgrade.py`
(`:524,601,843,958,994`), `init_state.py` (`:122,141,169`), and the
`uninstall.py:105`/`:87` disambiguator is deferred to the follow-on spec.

```
agentbundle install --pack core --scope local
agentbundle uninstall --pack core --scope local
agentbundle list-installed   # local-scope rows shown with scope = local
                             # and a note: "not committed; per-clone only"
```

The install success line must report both the scope and the actual
exclude-file path written (resolved via `git rev-parse --git-path info/exclude`,
which may point to the main repo's `.git/info/exclude` for a linked worktree
or `.git/modules/<name>/info/exclude` for a submodule), e.g.:
```
installed: core @ local (excluded via /path/to/repo/.git/info/exclude)
```

## Options considered

Axis: *what is the install target, and what git mechanism provides per-clone
exclusion without a committed diff?*

The option space is exhausted along two dimensions: (A) where files land
(working-tree vs. out-of-tree); (B) for working-tree options, how they are
excluded from git. Do-nothing is included.

| Option | Files land in | Git-hidden? | Committed diff? | Verdict |
|--------|--------------|-------------|-----------------|---------|
| **A. Working-tree + `.git/info/exclude`** *(proposed)* | `<repo>/` | Yes — per-clone exclude | No | ✓ Recommended |
| **B. `--scope user` alias** | `~/.claude/` | N/A — never in repo | No | ✗ Wrong lifetime: global, not per-session |
| **C. Working-tree + `.gitignore` write** | `<repo>/` | Yes | Yes — `.gitignore` change creates a diff | ✗ Defeats the purpose |
| **D. Working-tree + `--skip-worktree`** | `<repo>/` | Yes — index flag | No | ✗ Requires files to be previously committed; irrelevant for new installs |
| **E. Temp-dir install** | System temp | N/A | No | ✗ Fixed discovery paths in harness (the Claude Code runtime that loads skills from fixed locations); requires harness changes out of scope |
| **F. No automation (do-nothing)** | N/A | User-managed | Varies | ✗ Cost of delay: every user rediscovers the workaround; risk of accidental commits stays; per-session onboarding friction persists |

A is the only option that satisfies "working-tree visible to Claude Code,
excluded from git without a committed diff, stdlib-only."

## Risks & what would make this wrong

**Pre-mortem.**

- *User runs `--scope local` and the pack's files are already tracked in the
  repo.* The install aborts with a clear error; no partial write. This is the
  correct conservative behaviour, but it means `--scope local` cannot be used
  in repos that already track a colliding path (e.g. a repo that already commits
  `.claude/skills/work-loop/`). This is an intentional non-goal: `--scope repo`
  is the right scope for repos that track pack files.
- *Multi-worktree installs of the same pack.* Per-worktree keyed blocks allow
  independent simultaneous installs. Stale blocks from deleted worktrees
  accumulate in `info/exclude` and are **not harmless**: their patterns continue
  excluding same-path files in all linked worktrees; a committed file added later
  at that path is silently invisible to `git status`. Pruning via
  `agentbundle local prune` is deferred; documented in `write_exclude_block` docstring.
- *Concurrent agentbundle calls on the same repo.* Without a file lock, two
  simultaneous `--scope local` installs produce a lost update: one writer's
  atomic full-file replace clobbers the other's block, silently making those
  files git-visible and committable. Same applies to the state file. Known
  limitation; locking is deferred to v2.
- *User deletes the repo and re-clones.* The exclude file and state file are
  machine-local; a fresh clone has neither. Pack files also don't transfer.
  Correct behaviour for local scope.

**Key assumptions (falsifiable).**

- `git rev-parse --git-path info/exclude` is available in all git versions users
  are likely to have (introduced git ≥2.5.0, 2015).
- `info/exclude` (or its submodule equivalent) is writable by the process that
  owns the working tree.
- `git ls-files --error-unmatch` correctly identifies tracked paths before the
  install writes any file.

**Drawbacks.**

- Adds a third scope to a two-scope system; `scope.resolve()` logic grows.
- `.git/info/exclude` is per-clone: CI pipelines and teammates on a fresh clone
  do not have the exclusions. Correct for local scope but may surprise users who
  expect the pack to "just work" in CI.
- The whole-install abort on any tracked-file collision is conservative: a repo
  that already tracks `.claude/skills/work-loop/SKILL.md` for some other reason
  cannot use `--scope local` for the `core` pack at all. This is by design
  (shadowing a tracked file is git-breaking) but limits the feature for partially
  pre-configured repos.
- No per-pack ability to restrict `--scope local` in v1.

## Evidence & prior art

**Spike / de-risk result.** Verified in the current working directory, which is
itself a git linked worktree (a checkout that shares git history with the main
repo but has its own working directory):

1. `git rev-parse --git-path info/exclude` → returns main repo's
   `.git/info/exclude` (not a per-worktree path). `info/exclude` is shared
   across all worktrees; the command resolves correctly in all repo configurations
   via the git-path abstraction.
2. `echo "test-entry" >> .git/info/exclude && git status` — the entry is
   honoured immediately, no git process restart required.
3. Atomic replace (`os.replace`) is standard POSIX/Windows stdlib; no third-party
   dependency.

**Repo precedent.**
- RFC-0004 (`0004-install-scope-per-pack.md`) — canonical scope RFC; established
  `"repo"` and `"user"`, explicitly noted that adding scopes later is "a one-line
  schema bump"; rejected `"global"` (system-wide), not `"local"`.
- RFC-0008 (`0008-claude-plugins-install-route-parity.md:202`) — uses the
  `local` token to mean "project-local, not committed" in the Claude-plugins
  install route. Semantically aligned with this RFC's `--scope local`.
- `scope.py:46` — `LEGAL_SCOPES = frozenset({"repo", "user"})` — the extension
  point this RFC expands.
- `config.py:524-529` — `_parse_adapter_row` hardcoded tuple; widening to
  `LEGAL_SCOPES` is a one-line fix required by this RFC.

**External prior art.**
- [git-scm.com/docs/gitignore](https://git-scm.com/docs/gitignore) — documents
  `.git/info/exclude` as the per-clone, user-private, never-committed exclusion
  mechanism. Pattern syntax identical to `.gitignore`.
- `git config --local / --global / --system` — canonical three-tier scope
  hierarchy; the `local` naming here is intentionally aligned.
- Ansible `blockinfile` module — documents the comment-delimited
  `# BEGIN ANSIBLE MANAGED BLOCK` / `# END ANSIBLE MANAGED BLOCK` managed-section
  pattern that this RFC's `:begin`/`:end` markers follow.
  ([docs.ansible.com/ansible/latest/collections/ansible/builtin/blockinfile_module.html](https://docs.ansible.com/ansible/latest/collections/ansible/builtin/blockinfile_module.html))

## Follow-on artifacts

- Spec: `docs/specs/local-scope-install/` — implementation plan covering:
  - `scope.py` (`LEGAL_SCOPES`; `resolve()` default-scope reject-before-promote
    guard)
  - `config.py` (`_parse_adapter_row` widen to `LEGAL_SCOPES`)
  - `commands/_common.py` (`resolve_state_path` local branch)
  - `commands/list_installed.py` (three-scope default list; explicit `local`
    branch in inline `if/else` at lines 477-486 — the existing else-user
    fallthrough misroutes `local` to `~/.agentbundle/state.toml`)
  - `commands/install.py` — the largest change: (1) widen upstream resolution
    gate at line 513 (`requested_scope in ("repo","local") and not
    emit_install_routes`) and the repo projection-rendering aggregate at line 929
    (`any(p.scope in ("repo","local") ...)`); the `:950` user aggregate stays
    user-only — see fork-family 6 in the Proposal;
    (2) new `local` branch in `_ScopePlan`-building loop at line 759; (3) full
    site-by-site audit per the Proposal's "install.py write-path threading"
    section — grep patterns:
    `requested_scope == "repo"`, `requested_scope == "user"`,
    `scope_value == "repo"`, `scope_value == "user"`,
    `plan.scope == "repo"`, `plan.scope == "user"`,
    `p.scope == "repo"`, `p.scope == "user"`; **IMPORTANT**: some key sites
    are grep-invisible and must be handled by line number from the Proposal
    rather than via grep hits:
    - Truly grep-invisible (no `plan.scope ==` comparison): `:1447`/`:1456`
      (unconditional carve-out calls — see Proposal "Carve-outs"), `:1471-1477`
      (`_chain_adapt`), `:1493-1543` (Step-13 emission loop). Also: `:258`
      (`cli_scope != "user"`) and `:377` (`requested_scope != "user"`) use
      `!=` and are invisible to all `==` grep patterns — `:258` handled per
      Proposal point 4; `:377` handled per Proposal fork-family 2 (the
      force-merge "do not change to `== "repo"`" warning).
    - Grep-surfaced but needing site-specific treatment (see Proposal
      "Additional key sites"): `:814` (intentionally leave repo-only), `:859`
      (widen to `in ("repo","local")`), `:1334` (widen adapter recording),
      `:1356` (update both conjuncts).
    Key grep results to resolve: `:486` (state-file routing for source-conflict
    check), `:631`/`:668` (add `local_state`/`installed_at_local` for conflict
    checks);
    (4) `--emit-install-routes + --scope local` refusal at line 390, branching
    the error message for `local` vs. `repo`; (5) `emit_install_routes`
    inference at line 258 changed from `cli_scope != "user"` to
    `cli_scope == "repo"` (protects test-fixture fallback)
  - `cli.py` (six `choices=` sites; source from `tuple(sorted(LEGAL_SCOPES))`
    — sorted tuple required for stable `--help` output)
  - `install.py` (`.git/info/exclude` write path; worktree-id derivation)
  - `uninstall.py` (block-strip path; worktree-id matching; also fix
    `uninstall.py:105`/`:87` disambiguator which has no `local` branch)
  - `diff.py`, `upgrade.py`, `init_state.py`: v1 retains `("repo","user")` at
    their argparse `choices=` sites (argparse-native rejection); a follow-on
    spec threads full `--scope local` support through each subcommand's inline
    state routing
  - `install.py` profile path (`:4331`/`:4357`): no new guard needed —
    `install.py:162-165` already refuses any `--scope` alongside `--profile`;
    audit only (verify the guard covers `"local"` once it is a valid choice at
    `cli.py:390`); follow-on deferred for full profile support
  - `pack.schema.json` (`allOf` if/then: local⇒repo) — this file exists as two
    byte-identical copies: `contracts/pack.schema.json` and
    `packages/agentbundle/agentbundle/_data/pack.schema.json`. **Both must be
    edited by hand to remain byte-identical.** `check_contract_parity.py` is
    the CI gate (verify-only — no `--write` flag); run it locally after editing
    both files to confirm parity before committing.
  - Block-key encoding: both `<pack-name>` and `<worktree-id>` fields in the
    `# agentbundle:local:<pack-name>:<worktree-id>:begin/end` markers are
    `:`-delimited positionally. Pack names follow the existing `[a-z0-9-]+`
    identifier convention (enforced by `pack.schema.json`) and never contain
    `:` — assert this invariant at parse time. Worktree-id (last component of
    `git rev-parse --git-dir`) must be sanitized to replace or reject `:` so
    the key is unambiguously parseable.
- ADR: record the decision to use `.git/info/exclude` over `.gitignore`, the
  whole-install-abort policy for tracked-file collisions, the per-worktree
  keyed-block design (blocks keyed by `(pack-name, worktree-id)`), and the
  deferred concurrent-write locking.

## Open questions

None. All decisions are resolved in the D1–D4 table (each row carries a
recommendation and `decide-by: This review`). Implementation-detail deferrals
(stale-block cleanup CLI surface, worktree-id sanitization encoding, and the
sentinel choice for the block-key delimiter) are tracked in the follow-on spec
(`docs/specs/local-scope-install/`), not left as open questions here.
