# Spec: Local scope install (`--scope local`)

- **Status:** Shipped <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** RFC-0080, ADR-0070, RFC-0004, RFC-0005, RFC-0008, RFC-0012
- **Brief:** none
- **Discovery:** none
- **Contract:** `contracts/pack.schema.json` (and parity copy `packages/agentbundle/agentbundle/_data/pack.schema.json`) — AC1 modifies `allowed-scopes` in both copies
- **Shape:** integration

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

`agentbundle install --scope local` installs pack files into the working tree at
the same paths as `--scope repo`, but excludes every installed file from git via a
comment-delimited block in `.git/info/exclude` (the per-clone, never-committed
exclusion file). The result: a pack is fully functional for the session — skills
load, agents use them — and `git status` never shows any trace. Uninstall removes
the working-tree files and strips the block, leaving the repo in exactly the state
it was in before. The primary user is anyone who wants to trial a pack in a repo
they don't own or haven't permanently adopted it.

## Boundaries

### Always do

- Verify `git rev-parse --is-inside-work-tree` succeeds before any write.
- Resolve the exclude path via `git rev-parse --git-path info/exclude` (handles
  linked worktrees and submodules automatically).
- Write to `.git/info/exclude` atomically: read → modify in memory → write to a
  temp file in the same directory → `os.replace` (never in-place append).
- Abort the whole install (no partial writes) when any target file is already
  tracked by git.
- Enforce the repo/local cross-scope refusal as a hard, `--force`-immune check.
- Leave `:1060` and `:1254` (seed gates) unchanged — both are already gated
  `plan.scope == "repo"` and correctly exclude local; no new code needed there.
- Add explicit `if plan.scope != "local":` guards around `:1447` (install marker)
  and `:1456` (layout section) — these are unconditional calls with no existing guard.
- Skip `_chain_adapt` (Step 12) for `scope="local"` installs; update the
  `install.py:1468` comment and add an erratum note to `adapt-to-project/spec.md`
  AC19b in the implementing PR.
- Record adapter in the local state row (widen `install.py:1334`).

### Ask first

- Any change to the block-key format `# agentbundle:local:<pack>:<worktree-id>:{begin,end}`.
- Any change that causes `diff`, `upgrade`, or `init-state` to accept `--scope local`
  (deferred to a follow-on spec per RFC-0080).
- Any file lock added to `.git/info/exclude` or `.agentbundle-local-state.toml`.

### Never do

- Write to `.gitignore` (use `.git/info/exclude` only).
- Allow `--scope local` alongside `--profile` (existing `install.py:162-165` guard
  already covers this once `"local"` is a valid choice at `cli.py:390`).
- Allow `--scope local` alongside `--emit-install-routes`.
- Allow `default-scope = "local"` in a pack manifest.
- Allow `allowed-scopes = ["local"]` without `"repo"` (schema `allOf` constraint).
- Deliver seeds, install markers, or layout sections for local-scope installs.
- Widen `:950` user-aggregate beyond `any(p.scope == "user" ...)`; local plans
  must not enter user-projection rendering.
- Add any new guard around `:1060` or `:1254` — both are already correctly gated
  `plan.scope == "repo"` and that logic must not change.
- Change `install.py:377` `!= "user"` to `== "repo"` — the existing negation
  correctly refuses force-merge for every non-user scope.

## Testing Strategy

- **TDD** — for all logic with a compressible invariant: `resolve()` auto-promote
  rule, `_parse_adapter_row` scope coercion, `resolve_state_path` routing,
  block-key parse/strip round-trip, tracked-file collision check, `installed_at_*`
  flag derivation (adapter-level), repo/local cross-scope refusal (including
  `--force` immunity), `--force-merge --scope local` refusal, unowned pre-existing
  target refusal (AC10b — both same-content and different-content unowned cases),
  path-level cross-scope overlap refusal (AC12b, both directions),
  rollback round-trip (AC21), dependency validation with local state (AC23b),
  show-state loading (AC23c).
- **Goal-based check** — schema validation: `python3 tools/lint-ruff.py` passes;
  `python3 -m pytest packages/agentbundle/tests/ -q` green; `check_contract_parity.py`
  exits 0 (both schema copies byte-identical).
- **Visual / manual QA** — full install / uninstall cycle exercised via the real
  `agentbundle` CLI in an integration test: files appear in working tree, do NOT
  appear in `git status`, `list-installed` shows `scope = local`, uninstall removes
  files and the exclude block, `git status` clean after.

## Acceptance Criteria

### Schema and scope engine

- [x] AC1: `pack.schema.json` `allowed-scopes` enum includes `"local"`; an
  `allOf` constraint rejects `allowed-scopes` that contain `"local"` but not `"repo"`.
  Both copies (`contracts/pack.schema.json` and
  `packages/agentbundle/agentbundle/_data/pack.schema.json`) are byte-identical;
  `check_contract_parity.py` exits 0.
- [x] AC2: `scope.py` `LEGAL_SCOPES` equals `{"repo", "user", "local"}`.
- [x] AC3: `scope.resolve()` raises `ScopeRefused` when `default-scope == "local"`,
  before the D4 auto-promote check.
- [x] AC4: `scope.resolve()` permits `scope="local"` for any pack whose
  `allowed-scopes` contains `"repo"`, without requiring explicit `"local"` in the
  pack's `allowed-scopes`.
- [x] AC5: `config.py` `_parse_adapter_row` sources its allowlist from `LEGAL_SCOPES`
  (not a hardcoded tuple); `scope = "local"` rows in `.agentbundle-local-state.toml`
  are preserved correctly.

### State file routing

- [x] AC6: `commands/_common.py` `resolve_state_path("local", root)` returns
  `root / ".agentbundle-local-state.toml"`.
- [x] AC7: `.agentbundle-local-state.toml` uses `schema-version = "0.4"` and the
  same `PackState` shape as `.agentbundle-state.toml`; all rows carry `scope = "local"`.
  The T11 integration test reads the written file and asserts `schema-version = "0.4"`.

### Install — pre-flight

- [x] AC8: `agentbundle install --scope local` fails with a clear error when run
  outside a git working tree.
- [x] AC9: `agentbundle install --scope local --emit-install-routes` is refused with
  an error that references RFC-0008 for the plugins route's own local-scope behaviour.
- [x] AC10: `agentbundle install --scope local` fails (no partial writes) when:
  (a) any target file is already tracked by git (checked via
  `git --literal-pathspecs ls-files --error-unmatch <path>`); or
  (b) any target file exists as an untracked file that has **no ownership record**
  in any agentbundle state (repo, user, or local) — regardless of content match.
  Matching content does not grant ownership: a pre-existing unowned file with
  identical content would be deleted on uninstall, violating the exact-restoration
  guarantee. For local scope, a conflicting untracked file must not be silently
  bypassed via companion-file routing (Tier-2 classification applies to unowned
  untracked files with different content, but the ownership check is broader).
- [x] AC11: `agentbundle install --scope local` fails when the pack is already
  installed at `--scope repo`; the refusal is `--force`-immune.
- [x] AC11b: `agentbundle install --force-merge --scope local` is refused; the
  force-merge guard (`install.py:377` `!= "user"` negation) covers local scope
  and must not be changed to `== "repo"`.
- [x] AC12: `agentbundle install --scope repo` fails when the pack is already
  installed at `--scope local`; the cross-scope refusal is `--force`-immune.
  (`--scope user` coexists with a local install — user-scope files land in `~/.claude/`
  outside the working tree and are unaffected by the exclude block; user/local
  coexistence is explicitly permitted by RFC-0080.)
- [x] AC12b: Cross-scope path collision (not just same-pack) is detected and refused:
  if a local install's projected paths overlap with any path owned by a repo-scope
  pack (or vice versa), the install is refused with a `--force`-immune error naming
  the colliding path and its owner.

### Install — write path

- [x] AC13: Installed files appear in the working tree at the same paths as
  `--scope repo`; they do NOT appear in `git status` output.
- [x] AC14: A comment-delimited block keyed to `(pack-name, worktree-id)` is appended
  to the file returned by `git rev-parse --git-path info/exclude` (which resolves to
  the common-dir `info/exclude` from both primary and linked worktrees). Block format:
  `# agentbundle:local:<pack>:<worktree-id>:begin / [paths] / …:end`. Each path
  written into the block is gitignore-metacharacter-escaped before writing: the
  characters `[`, `]`, `*`, `?`, and `\` are backslash-escaped. (All paths are
  written with a leading `/` anchor, so `#` and `!` can never appear at line start
  and need no escaping.) This ensures filenames containing gitignore pattern syntax
  are matched literally and not as globs.
- [x] AC14b: The exclude block for a pack represents the **union** of all adapter rows
  installed locally for that pack. Installing a second adapter replaces the block with
  a block containing all paths from both adapters. Uninstalling one adapter recomputes
  the block from the remaining rows; the block is stripped only when the last row is
  removed.
- [x] AC15: When a second adapter is installed locally for the same pack
  (multi-adapter union path per AC14b), the block is replaced in place with the
  union of both adapters' patterns — no duplicate blocks. Same-adapter reinstall
  is governed by AC21b's refusal (not this AC).
- [x] AC16: Two different worktrees installing the same pack each write their own
  keyed block; the blocks coexist in the shared `info/exclude` file.
- [x] AC17: Seeds (`AGENTS.md`/`docs/CHARTER.md`), install markers, and layout
  sections are NOT written for `--scope local` installs.
- [x] AC18: The local state row includes the adapter field (populated from
  `repo_target_adapter`).
- [x] AC19: `_chain_adapt` (Step 12) is skipped for `--scope local` installs.
  Amends `adapt-to-project/spec.md` AC19b ("regardless of install scope"); the
  implementing PR adds an erratum note to AC19b and updates the adjacent
  `install.py` comment to record the local-scope exception. Also addresses AC19a
  (the "every successful install" universal is now scoped to repo/user installs
  only — local installs are ephemeral and do not write install markers); the PR
  adds a clarifying note to AC19a as well.
- [x] AC20: The install success line reports both the scope and the actual
  exclude-file path: `installed: <pack> @ local (excluded via <exclude-path>)`.

### Install — rollback on failure

- [x] AC21: The write path follows the order: (1) snapshot prior exclude-file content,
  (2) write the exclude block (so installed files are git-invisible from the moment
  they exist), (3) write projected files, (4) write state row. If any step fails after
  step 1, the install rolls back in the inverse order: (a) delete any projected files
  written so far, THEN (b) restore the exclude block to its snapshotted content, THEN
  (c) discard any uncommitted state row. Deleting files before restoring the block
  ensures that the exclude file is never restored while the installed files still
  exist on disk (which would create a transient window where files are git-visible
  and unexcluded). The working tree, exclude file, and local state are identical to
  their pre-install values after rollback. Writing the block before the files
  guarantees that no background git tooling can observe the files in a non-excluded
  state.

### Install — same-scope reinstall

- [x] AC21b: `agentbundle install --scope local` on an already-local pack, **same
  adapter**, same scope, is refused with a clear "already installed" message. The
  guard fires only when the requested adapter row already exists in `local_state`
  (adapter-identity check, not a pack-level boolean). The install does not route
  through `upgrade.run` (which does not support local scope in v1) and does not
  modify any state. The v1 message names `uninstall --scope local` then
  `install --scope local` as the refresh path. Amends RFC-0080 §"Same-scope local
  reinstall" (which mandated upgrade-offer routing — that routing fails because
  `upgrade.run` has no local support); this amendment is recorded in the
  implementing PR description.

### Uninstall

- [x] AC22: `agentbundle uninstall --scope local` removes installed working-tree
  files for the specified adapter row, recomputes the exclude block from the remaining
  local rows for this pack (strips the block if no local rows remain), and removes
  the specified adapter row from `.agentbundle-local-state.toml` (deletes the state
  file only when it becomes empty). `git status` is clean after. When multiple
  adapter rows exist for the same pack, uninstalling one adapter leaves the other
  adapter's files excluded and in-place.

### List-installed

- [x] AC23: `agentbundle list-installed` includes local-scope rows with
  `scope = local` and a note `(not committed; per-clone only)`.

### Dependency validation

- [x] AC23b: `validate_dependencies_required()` (called during install pre-flight)
  receives the local state in addition to repo and user state when `requested_scope ==
  "local"`. A required dependency installed only at local scope satisfies the
  dependency check for a local install.

### Show command

- [x] AC23c: `agentbundle show <pack>` includes `.agentbundle-local-state.toml` in
  its `_load_states()` fallback. After a local-only install with the catalogue
  unavailable, `show` correctly reports the pack as installed (`source:
  installed-state`). The current `show` output format does not include a top-level
  scope field; extending the output contract to expose scope is deferred to a
  follow-on spec.

### CLI surface

- [x] AC24: `agentbundle install --scope local`, `uninstall --scope local`, and
  `list-installed --scope local` are accepted by argparse. `diff --scope local`,
  `upgrade --scope local`, and `init-state --scope local` are rejected by argparse
  (choices list does not include `"local"` on those three subcommands).
- [x] AC25: `agentbundle diff --scope local`, `upgrade --scope local`, and
  `init-state --scope local` produce an argparse-native `invalid choice: 'local'`
  error (not a runtime guard). The argparse rejection is the v1 "not yet supported"
  mechanism; the friendly RFC-0080 message at lines 582-585 is reserved for a future
  custom action if the UX is revisited.

### Documentation

- [x] AC26: The concurrent-write lost-update limitation (two `agentbundle` processes
  writing simultaneously; last writer wins) is documented in at least one user-visible
  location: a docstring on `write_exclude_block`, a note in the `--scope local` entry
  of the guides, or an inline `# WARNING:` comment in the write helper. The location
  is named in the PR description.
- [x] AC27: The cross-worktree exclusion side-effects are documented in a user-visible
  location (same as AC26 — docstring, guide note, or inline comment):
  (a) **Live-worktree side-effect:** a leading-`/` pattern in `info/exclude` excludes
  same-path untracked files in *all* linked worktrees, not just the installing one.
  (b) **Stale-block risk:** when a worktree is deleted without uninstalling, its block
  remains in `info/exclude` and continues excluding same-path files in all remaining
  worktrees — including tracked or committed files added later. The documentation must
  name `agentbundle local prune` (deferred) as the cleanup path and record this as a
  known v1 limitation. Verified by a T11 assertion that the documented text is present
  in the chosen location (docstring content check or guide file existence check).

## Assumptions

- Technical: `.git/info/exclude` is shared across all linked worktrees of the same
  repo — verified by spike in the philadelphia-v1 worktree (source: RFC-0080
  §Git exclusion contract).
- Technical: `os.replace` is atomic on POSIX and near-atomic on Windows (NTFS);
  sufficient for the v1 lost-update tolerance documented in ADR-0070
  (source: RFC-0080 §Concurrent-write limitation).
- Technical: `git rev-parse --git-path info/exclude` resolves correctly for
  standard repos, linked worktrees, and submodules (source: RFC-0080 spike).
- Technical: `install.py:162-165` already refuses `--scope <anything>` alongside
  `--profile`; no new guard needed once `"local"` is a valid choice (source:
  RFC-0080 pass-19 adversarial reviewer).
- Process: `check_contract_parity.py` is the CI gate for `pack.schema.json` parity;
  no `--write` flag exists — both copies must be hand-edited (source: RFC-0080
  §Follow-on artifacts).
- Process: `install.py:377` (`requested_scope != "user"` negation) must NOT be
  changed to `== "repo"` — the existing negation correctly excludes force-merge
  for local scope; changing it would introduce a security regression (source:
  RFC-0080 adversarial pass-20).
