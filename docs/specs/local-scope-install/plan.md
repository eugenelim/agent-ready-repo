# Plan: Local scope install (`--scope local`)

- **Spec:** [`spec.md`](spec.md)
- **Status:** Drafting <!-- Drafting | Approved | Executing | Done -->

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document is allowed to change as you learn. When it changes substantially,
> note why in the changelog at the bottom.

## Approach

Thread `"local"` through agentbundle bottom-up: schema and scope engine first
(T1–T3), then state-file routing (T4), then the two simpler read-path commands
(T5, T6), then the CLI choices (T7), then the install write-path (T8 — the
largest task, covering all six fork families plus carve-outs and key sites),
then the `.git/info/exclude` write and worktree-id logic (T9), then the uninstall
strip (T10), and finally a full integration test (T11). Each task is a coherent
commit. T8 and T9 share install.py but can be separated by landing T9's
helper functions before T8 calls them. All prior tasks must be green before T8
begins — the install write path touches every earlier layer.

The riskiest part is T8 (install.py): it has six scope-branching fork families,
carve-outs that must NOT be widened, and five "else-implies-user" ternary sites
that silently produce a zero-file install if missed. An integration test (T11)
that asserts specific files were actually written is the primary safety net
against silent misses.

## Constraints

- RFC-0080 — canonical authority for all design decisions.
- ADR-0070 — records the four implementation decisions (exclude mechanism,
  abort policy, keyed-block design, deferred locking).
- RFC-0004 — install-scope per pack; `allowed-scopes` schema precedent.
- RFC-0005 — user-scope hook support; force-merge is user-scope-only.
- RFC-0008 — claude-plugins install-route; `--emit-install-routes` guard.
- RFC-0012 — repo-scope per-adapter projection; `allowed-prefixes.repo` contract.
- ADR-0006 — doc drift prevention; spec and plan must stay in sync.

## Construction tests

**Integration tests:** T11 covers the full install / uninstall cycle across all
three phases: write, verify git-invisible, uninstall-clean. This is the primary
defence against the silent-zero-file hazard in T8.

**Manual verification:** After T11 is green, run `agentbundle install --pack core
--scope local` in a test repo and confirm: (a) files appear in the working tree,
(b) `git status` shows nothing, (c) `list-installed` shows `scope = local` row,
(d) `agentbundle uninstall --pack core --scope local` produces a clean `git status`.

## Design (LLD)

### Design decisions

*(Detailed rationale in ADR-0070 and RFC-0080; brief design notes here.)*

- **`LEGAL_SCOPES` is the single source of truth** for argparse `choices` at the
  three accepting `cli.py` sites — sourced as `tuple(sorted(LEGAL_SCOPES))` so
  `--help` order is stable. The three refusing sites retain `("repo","user")` to
  give argparse-native rejection (no runtime guard needed).
- **Separate state file** (`.agentbundle-local-state.toml`) means older agentbundle
  binaries see no effect; no schema-version bump required.
- **`_chain_adapt` skipped for local** — local installs are ephemeral; adapt-discovery
  re-running would apply to files the user considers git-invisible. This is a
  deliberate amendment to AC19b (the existing spec comment at `install.py:1468`
  that reads "invoke regardless of the install scope (markers are repo-only)");
  the PR description must record this deviation explicitly.
- **`install.py:377` stays `!= "user"`** — the force-merge guard correctly covers
  local scope; changing to `== "repo"` would introduce a security regression by
  letting `--force-merge --scope local` through.
- **`install.py:950` user aggregate stays unchanged** — local plans must not enter
  user-projection rendering; only the `:929` repo aggregate widens.

### Data & schema

State-file schema: identical `PackState` shape to `.agentbundle-state.toml`,
`schema-version = "0.4"`, all rows `scope = "local"`. Path:
`<repo>/.agentbundle-local-state.toml`. Included in the exclude block at install;
removed row-by-row at uninstall; file deleted when empty.

Block format in `.git/info/exclude`:
```
# agentbundle:local:<pack-name>:<worktree-id>:begin
/.agentbundle-local-state.toml
/.claude/skills/<pack-slug>/SKILL.md
# agentbundle:local:<pack-name>:<worktree-id>:end
```
Worktree-id: derived by comparing `git rev-parse --git-dir` and
`git rev-parse --git-common-dir` (equal → primary worktree, use a reserved
sentinel such as a hash of the common-dir path; unequal → last component of
`--git-dir`). The id must be sanitized to replace or reject `:` to preserve
the `:` -delimited block-key. Pack names are `[a-z0-9-]+` per schema; assert
the invariant at parse time.

### Component / module decomposition

| Module | Change |
|---|---|
| `pack.schema.json` (×2) | Add `"local"` to enum; add `allOf` if/then constraint |
| `scope.py` | Extend `LEGAL_SCOPES`; add `default-scope="local"` reject in `resolve()` |
| `config.py` | Widen `_parse_adapter_row` to `LEGAL_SCOPES` |
| `commands/_common.py` | Add `"local"` branch in `resolve_state_path` |
| `commands/list_installed.py` | Three-scope default; explicit `local` branch in inline if/else |
| `cli.py` | 3 sites gain `"local"`; 3 sites retain `("repo","user")` |
| `commands/install.py` | Substantial — see T8 task for full site list |
| New helper (install.py or a new module) | `write_exclude_block`, `strip_exclude_block`, `derive_worktree_id` |
| `commands/uninstall.py` | Block-strip path; worktree-id matching; `:105`/`:87` disambiguator |

### Failure, edge cases & resilience

- `git` not in PATH or not a git repo: pre-flight fails fast; clear error.
- `info/exclude` does not exist: created on first write.
- Block already exists for this `(pack, worktree-id)`: replaced in place (no duplicate).
- Target file already tracked: whole install aborts; no partial writes.
- Concurrent write (two processes writing simultaneously): lost-update race
  documented in ADR-0070; no lock in v1.
- Worktree deleted without uninstall: stale block accumulates in `info/exclude`;
  paths don't exist, git treats them as unmatchable — harmless.

## Tasks

### T1: Schema — add `"local"` to `pack.schema.json`

**Depends on:** none

**Tests:**
- `check_contract_parity.py` exits 0 (both copies byte-identical). Goal-based.
- `python3 -m pytest packages/agentbundle/tests/ -q` — any existing schema-
  validation tests still pass. Goal-based.
- A pack with `allowed-scopes = ["local"]` (no `"repo"`) fails schema validation.
  TDD.
- A pack with `allowed-scopes = ["user", "local"]` (has `"local"` but not `"repo"`)
  fails schema validation — this is the key case the `allOf` constraint closes. TDD.
- A pack with `allowed-scopes = ["repo", "local"]` passes. TDD.

**Approach:**
- Edit **both** `contracts/pack.schema.json` AND
  `packages/agentbundle/agentbundle/_data/pack.schema.json` byte-identically.
- In the `allowed-scopes` array enum, add `"local"` alongside `"repo"` and `"user"`.
- Add a new `allOf` sibling to the existing `if/then/else` block:
  `if allowed-scopes contains "local" then allowed-scopes must also contain "repo"`.
- Run `python3 tools/catalogue/check_contract_parity.py` to verify byte-identity.

**Done when:** `check_contract_parity.py` exits 0; the `allOf` constraint test is green.

---

### T2: `scope.py` — extend `LEGAL_SCOPES` and `resolve()` guard

**Depends on:** T1

**Tests:**
- `LEGAL_SCOPES == {"repo", "user", "local"}`. TDD.
- `resolve(pack, requested="local", default="repo", allowed=["repo"])` returns
  `"local"` (D4 auto-promote). TDD.
- `resolve(pack, requested=None, default="local", allowed=["repo", "local"])`
  raises `ScopeRefused`. TDD (default-scope reject precedes auto-promote).
- `resolve(pack, requested="local", default="repo", allowed=["user"])` raises
  `ScopeRefused` (repo not in allowed). TDD.

**Approach:**
- Add `"local"` to `LEGAL_SCOPES` in `scope.py`.
- In `resolve()`, add an explicit check: if the resolved default is `"local"`,
  raise `ScopeRefused` before the D4 auto-promote logic.
- In the auto-promote path: if `requested == "local"` (or resolved to `"local"`),
  allow if `"repo" in allowed_scopes` (the pack's allowed-scopes list).

**Done when:** all four new unit tests green; `python3 -m pytest packages/agentbundle/tests/ -q` still green.

---

### T3: `config.py` — widen `_parse_adapter_row`

**Depends on:** T2

**Tests:**
- `_parse_adapter_row(row_with_scope="local")` preserves `scope="local"` (not
  coerced to `default_scope`). TDD.
- `_parse_adapter_row(row_with_scope="unknown")` still coerces to `default_scope`.
  TDD.

**Approach:**
- In `config.py:524-529`, replace hardcoded `("repo", "user")` with `LEGAL_SCOPES`
  (imported from `scope.py`).

**Done when:** both new tests green; `python3 -m pytest packages/agentbundle/tests/ -q` green.

---

### T4: `commands/_common.py` — `resolve_state_path` local branch

**Depends on:** T2

**Tests:**
- `resolve_state_path("local", root=Path("/repo"))` returns
  `Path("/repo/.agentbundle-local-state.toml")`. TDD.
- `resolve_state_path("repo", root=Path("/repo"))` returns
  `Path("/repo/.agentbundle-state.toml")` (unchanged). TDD.
- `resolve_state_path("user", root=...)` returns the user-scoped path (unchanged). TDD.

**Approach:**
- Add an `elif scope == "local":` branch in `resolve_state_path` returning
  `root / ".agentbundle-local-state.toml"`.

**Done when:** all three routing tests green.

---

### T5: `commands/list_installed.py` — three-scope default + `local` branch

**Depends on:** T4

**Tests:**
- `list-installed` without `--scope` lists all three scopes (repo, user, local).
  TDD / goal-based against a fixture state.
- `list-installed --scope local` shows rows with `scope = local` and the
  `(not committed; per-clone only)` annotation. TDD.
- The existing else-user fallthrough is replaced by an explicit `local` branch;
  no `local` rows are silently routed to the user state file. TDD.

**Approach:**
- Update the hardcoded `["user", "repo"]` scope list to `["user", "repo", "local"]`
  (or derive from `LEGAL_SCOPES`).
- Replace the inline `if sc == "repo": … else: # user` routing at lines 477–486
  with an explicit three-way branch that handles `"local"` explicitly.

**Done when:** fixture-based tests green; `python3 -m pytest packages/agentbundle/tests/ -q` green.

---

### T6: `cli.py` — update `choices=` at the three accepting sites

**Depends on:** T2

**Tests:**
- `agentbundle install --scope local --help` lists `{local,repo,user}` (or sorted
  equivalent). Goal-based (run actual CLI).
- `agentbundle diff --scope local` is rejected by argparse with a "invalid choice"
  error (not a runtime guard). Goal-based.
- Same argparse-native rejection for `upgrade --scope local` and
  `init-state --scope local`. Goal-based.

**Approach:**
- At `cli.py` lines **261** (`list-installed`), **390** (`install`), **630**
  (`uninstall`): change `choices=("repo","user")` to
  `choices=tuple(sorted(LEGAL_SCOPES))` (import from `scope.py`).
- Lines **525** (`diff`), **581** (`upgrade`), **678** (`init-state`): leave as
  `("repo","user")` — argparse-native rejection is the v1 refusal mechanism.

**Done when:** all three goal-based CLI tests pass.

---

### T7: `commands/install.py` — upstream gates, `_ScopePlan` branch, `emit_install_routes` inference

**Depends on:** T4, T6

**Tests:**
- `agentbundle install --scope local --emit-install-routes` is refused with the
  RFC-0008-referencing error message. TDD.
- `emit_install_routes` inference at line 258: `cli_scope == "repo"` (not
  `!= "user"`). Unit test for the fixture-fallback path. TDD.
- Upstream gate at line 513: `requested_scope in ("repo", "local")` resolves
  `allowed_prefixes_repo` correctly for a local request. TDD.
- `any(p.scope in ("repo", "local"))` aggregate at line 929 gates projection
  rendering for a local plan. TDD.
- `any(p.scope == "user")` at line 950 does NOT include local plans. TDD.
- A new `_ScopePlan(scope="local", ...)` is produced for a local request. TDD.

**Approach:**
- `install.py:258`: change `cli_scope != "user"` to `cli_scope == "repo"`.
- `install.py:390-393`: branch the `--emit-install-routes` guard to emit the
  RFC-0008-referencing message when `requested_scope == "local"`.
- `install.py:513`: widen gate to `requested_scope in ("repo", "local") and not
  emit_install_routes`.
- `install.py:759`: add a `local` branch producing
  `_ScopePlan(scope="local", root=output_root,
  state_path=output_root / ".agentbundle-local-state.toml",
  allowed_prefixes=allowed_prefixes_repo)`
  (`output_root` is the function-level variable; `repo_root` is not defined here).
- `install.py:929`: widen to `any(p.scope in ("repo", "local") ...)`.
- (`:950` is unchanged — user-only.)

**Done when:** all six unit tests green; `python3 -m pytest packages/agentbundle/tests/ -q` green.

---

### T8: `commands/install.py` — full six-family fork audit

**Depends on:** T7, T9

*This is the largest task. Proceed site-by-site per the six families below.
Use `git diff` after each sub-group to confirm no unintended changes.*

> **Line-number caveat:** all absolute line references in this task reflect
> pre-T7 `install.py`. T7 inserts a `_ScopePlan` local branch at ~`:759`, shifting
> every line below it. In this task, always **locate sites by symbol name or
> surrounding comment text** (as noted per site below), not by the raw number.
> The "~:" prefix signals a pre-T7 estimate; treat it as a grep hint, not a
> go-to-line instruction.

**Tests:**
- Projection write: `repo_projection if plan.scope in ("repo","local") else user_projection`
  at lines 1018, 1045, 1086 — TDD: a local plan selects repo_projection (non-None). TDD.
- Adapter selection: `:859` and `:1093` widen to `plan.scope in ("repo","local")` —
  TDD: local plan selects `repo_target_adapter`. TDD.
- `:486` state-file routing for source-conflict check routes local to
  `.agentbundle-local-state.toml`. TDD.
- `:631` upgrade-offer guard gains `(requested_scope=="local" and installed_at_local)`
  — TDD: local reinstall routes to upgrade-offer. TDD.
- `:668` cross-scope conflict loads `installed_at_local`; repo refusal is
  `--force`-immune. TDD.
- `:377` force-merge guard: `agentbundle install --force-merge --scope local` is
  refused; this is the AC11b behavioral test. TDD (assert non-zero exit and error
  message; do NOT change `:377` to `== "repo"`).
- `:814` left repo-only (v0.1 reload moot for new local state file) — no test
  change needed; assert it is unchanged.
- `:1334` adapter recording: `plan.scope in ("repo","local") and repo_target_adapter
  is not None` — TDD: local state row has adapter field set. TDD.
- `:1356` compound condition: both conjuncts accept `.agentbundle-local-state.toml`
  — TDD: local state write not blocked by prefix check. TDD.
- `:1447` and `:1456` wrapped in `if plan.scope != "local":` — TDD: no marker/
  layout writes for local scope. TDD.
- `:1471-1477` `_chain_adapt` skipped for local — TDD: adapt not invoked. TDD.
- `:1493-1543` Step-13 emission: local branch emits
  `installed: <pack> @ local (excluded via <path>)` — TDD / visual QA via CLI. TDD.
- Silent-zero-file guard: integration test (T11) asserts specific files were
  written to disk for a local install.

**Approach:**

**Family 1 — `requested_scope ==` equality comparisons (grep: `requested_scope == "repo"`, `requested_scope == "user"`):**
- `:486`: `repo_state if requested_scope in ("repo","local") else user_state`.
- `:631`: add `(requested_scope=="local" and installed_at_local)` to upgrade-offer guard.
- `:668`: add `installed_at_local` derivation; enforce repo/local refusal before
  `--force` check (outside `scopes_to_install` computation).
- Other sites (`390`, `397`, `432`, `513`, `577`, `663`, `739`): review each;
  widen or leave as-is per their individual semantics.

**Family 2 — `!= "user"` negation comparisons:**
- `:258`: already handled in T7 (change to `== "repo"`).
- `:377`: **leave unchanged** — `requested_scope != "user"` correctly refuses
  force-merge for local; do NOT change to `== "repo"`.

**Family 3 — `scope_value ==` (profile path, lines 760, 4331, 4357):**
- Guarded by `install.py:162-165` which already refuses `--scope` alongside
  `--profile` once `"local"` is a valid CLI choice. Audit that the guard fires
  correctly; no code change to `:4331`/`:4357` needed.

**Family 4 — `plan.scope ==` and `p.scope ==` forks (grep both):**
- Review each site; apply `in ("repo","local")` where the site drives a repo-path
  operation; leave user-branch sites unchanged.
- Carve-outs (leave as repo-only): `:1060`, `:1254`.
- Unconditional carve-outs (add guard): wrap `:1447` and `:1456` in
  `if plan.scope != "local":`.

**Family 5 — else-implies-user ternaries (`X if plan.scope == "repo" else <user>`):**
- `:1018`, `:1045`, `:1086`: `repo_projection if plan.scope in ("repo","local") else user_projection`.
- `:859`, `:1093`: `repo_target_adapter if plan.scope in ("repo","local") else user_target_adapter`.

**Additional key sites** (locate by symbol — absolute line numbers shift after T7
inserts a `_ScopePlan` branch; use grep on function name or comment text):
- `_reload_state` call (currently ~`:814`): leave repo-only (v0.1 reload moot for
  the new local state file; add a one-line comment to mark it intentional).
- Adapter ternary `repo_target_adapter`/`user_target_adapter` selection (~`:859`):
  widened in Family 5; ensures the adjacent warning (~`:863`) fires for local too.
- Adapter recording condition `repo_target_adapter is not None …` (~`:1334`):
  widen to `plan.scope in ("repo","local") and repo_target_adapter is not None`.
- Compound condition guarding state write (~`:1356`): update both conjuncts to
  accept `.agentbundle-local-state.toml`.
- `_chain_adapt` call site (locate via `_chain_adapt` symbol; ~`:1471-1477`):
  wrap the Step-12 block in `if requested_scope != "local":` (not `continue` —
  the call site is not inside a loop; use a conditional guard wrapping the block).
  **Also** update the adjacent comment (~`:1468`) to record the local-scope
  exception. **Also** add erratum notes to `docs/specs/adapt-to-project/spec.md`
  AC19b ("regardless of install scope" → "except local scope, which is ephemeral")
  and a clarifying note to AC19a ("every successful install" → "every successful
  repo/user install — local is ephemeral and writes no marker").
- Step-13 emission loop (locate via `# Step 13` comment or `"installed:"` string;
  ~`:1493-1543`): add `local` branch emitting exclude-path suffix.

**Family 6 — `any(p.scope == ...)` aggregates:**
- `:929`: already widened in T7.
- `:950`: unchanged (user-only; leave as-is).

**Done when:** all family-audit tests green; `python3 -m pytest packages/agentbundle/tests/ -q` green; no new `plan.scope == "repo" else` sites in the diff that aren't documented.

---

### T9: exclude-file write path and worktree-id derivation

**Depends on:** T4

*Can be authored in parallel with T7 since T9 provides helpers that T8 calls.
Land T9 first — T9 and T7 are DAG-independent (both depend on T4 only) but
both edit `install.py`; to avoid merge conflicts, complete T9 before starting T7.*

**Tests:**
- `derive_worktree_id()` returns the sentinel for the primary worktree (same
  `--git-dir` and `--git-common-dir`). TDD.
- `derive_worktree_id()` returns the last component of `--git-dir` for a linked
  worktree. TDD.
- Worktree-id containing `:` is sanitized (replaced or rejected). TDD.
- `write_exclude_block(path, pack, worktree_id, patterns)` appends a new block
  when none exists. TDD.
- `write_exclude_block` replaces an existing block for the same `(pack, worktree_id)`
  pair in place. TDD.
- Two different worktree-ids coexist in the file. TDD.
- `strip_exclude_block(path, pack, worktree_id)` removes the block and leaves
  sibling blocks intact. TDD.
- Write is atomic: a temp-file `os.replace` is used (not in-place append). TDD.
- `git ls-files --error-unmatch <path>` exits non-zero for a tracked file → install
  aborts with clear error. TDD.
- Pre-flight `git rev-parse --is-inside-work-tree` failure → install aborts. TDD.

**Approach:**
- Implement `derive_worktree_id()` using `subprocess.run(["git", "rev-parse",
  "--git-dir"])` and `--git-common-dir`, compare; sanitize with `re.sub(r":", "_", id)`.
- Implement `write_exclude_block(exclude_path, pack, worktree_id, patterns)`:
  read file (create if absent), find existing block by marker, replace or append,
  write atomically via `tempfile.NamedTemporaryFile` + `os.replace`.
- Implement `strip_exclude_block(exclude_path, pack, worktree_id)`: read file,
  find and remove the `begin`/`end` block (inclusive), write atomically.
- Wire into `commands/install.py` pre-flight and write path.
- In the `write_exclude_block` docstring, document: (a) the concurrent-write
  lost-update limitation (two processes writing simultaneously; last writer wins)
  and (b) the cross-worktree side-effect (a leading-`/` pattern in the shared
  `info/exclude` silently git-ignores same-path untracked files in *all* linked
  worktrees, not only the installing one). This satisfies AC26 and AC27.

**Done when:** all ten new tests green; `python3 -m pytest packages/agentbundle/tests/ -q` green.

---

### T10: `commands/uninstall.py` — block-strip and worktree-id matching

**Depends on:** T9

**Tests:**
- `agentbundle uninstall --scope local` removes installed files. TDD.
- `agentbundle uninstall --scope local` strips only the correct worktree's block
  (sibling blocks untouched). TDD.
- Uninstall removes pack rows from `.agentbundle-local-state.toml`; file deleted
  when empty. TDD.
- `uninstall.py:105`/`:87` disambiguator explicitly handles `"local"` scope (no
  else-fallthrough to repo). TDD.
- `git status` is clean after uninstall. Goal-based.

**Approach:**
- In `uninstall.py`, add a `"local"` branch in the `:105`/`:87` disambiguator.
- Call `strip_exclude_block` with the current worktree-id.
- Update state-file rows via `resolve_state_path("local", root)`.

**Done when:** all five tests green; `python3 -m pytest packages/agentbundle/tests/ -q` green.

---

### T11: Integration test — full install / uninstall cycle

**Depends on:** T8, T10

**Tests:**
- Install `core` pack with `--scope local` in a temp git repo:
  - Specific files appear in the working tree (assert at least one skill file
    exists at the expected path — guards against the silent-zero-file hazard).
  - `git status --short` output is empty (files not visible to git).
  - `git rev-parse --git-path info/exclude` target file contains the keyed block.
  - `agentbundle list-installed --scope local` output includes a row for `core`
    with `scope = local`.
  - Install success line contains `@ local (excluded via`.
  - `.agentbundle-local-state.toml` contains `schema-version = "0.4"` (AC7).
  - Neither `AGENTS.md` nor `docs/CHARTER.md` was written (seed absence; AC17).
  - `write_exclude_block` docstring references the lost-update limitation (AC26).
  - `write_exclude_block` docstring contains the cross-worktree side-effect text
    (AC27) — assert a key phrase (e.g. "linked worktrees") is present in the
    docstring body.
- Uninstall `core` pack with `--scope local`:
  - Working-tree files removed.
  - Exclude block stripped.
  - `git status --short` output is empty.
  - `.agentbundle-local-state.toml` deleted (was the only pack).
- Conflict (repo↔local): installing `core` at `--scope local` when already
  installed at `--scope repo` is refused, and vice versa; both refusals survive
  `--force`. (`--scope user` coexists with local — no refusal expected; assert
  user/local install succeeds.)
- Reinstall (same-scope local → local): routes to upgrade-offer flow.

**Approach:**
- Add an integration test under `packages/agentbundle/tests/` (or
  `packages/agentbundle/build/tests/` — check both test roots; add to whichever
  pattern the CI already picks up).
- Set up a temporary git repo (`tempfile.mkdtemp` + `git init`), install a real
  or fixture pack, assert the above behaviours, clean up.
- This test may require a real git binary; gate behind `pytest.mark.integration`
  or equivalent if the CI environment doesn't guarantee one.

**Done when:** integration test green; all prior task tests still green.

## Rollout

Pure Python library change; no infra, no external services. Shipped as a new
`agentbundle` wheel version. The `--scope local` flag is additive and backwards-
compatible: old binaries ignore `.agentbundle-local-state.toml` (they never
enumerate it). Reversible: `--scope local` installs can be fully uninstalled;
the scope can be deprecated without touching `repo`/`user` behaviour.

## Risks

- **Silent-zero-file install** from a missed ternary in T8 — mitigated by T11's
  file-presence assertion.
- **`os.replace` not atomic on Windows across volumes** — blocked by existing
  constraint (temp file must be in the same directory as the target). Already
  the pattern used for `.agentbundle-state.toml`; no new risk.
- **Concurrent write lost-update** — documented in ADR-0070; no mitigation in v1.
- **Stale worktree blocks** — documented and declared harmless; manual cleanup
  CLI deferred to the follow-on spec.
- **`install.py` fork-family audit incomplete** — mitigated by the six-family
  taxonomy in RFC-0080 and the explicit grep patterns in T8.

## Changelog

- 2026-08-04: initial plan, derived from RFC-0080 (Accepted).
- 2026-08-04: adversarial review pass 1 — added `["user","local"]` rejection
  test to T1; added AC11b force-merge behavioral test to T8; added `_chain_adapt`
  erratum sub-step and symbol-based key-site location guidance to T8; added
  schema-version and seed-absence assertions to T11; added AC26/AC27 documentation
  requirement to T9.
- 2026-08-04: adversarial review pass 2 — corrected AC12 (user/local coexistence
  allowed per RFC); extended AC19 erratum to cover AC19a marker-write universal;
  fixed T8 `_chain_adapt` skip mechanism (conditional guard, not `continue`);
  added AC27 docstring verification to T11; hoisted line-number caveat to T8 header;
  clarified T11 conflict test removes user/local refusal; added T9/T7 ordering note.
- 2026-08-04: adversarial review pass 3 — corrected T7 `_ScopePlan` illustrative
  branch from `repo_root` to `output_root` (the actual function-level variable).
