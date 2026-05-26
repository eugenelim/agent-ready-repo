# Plan: repo-scope-per-adapter-projection

- **Spec:** [`spec.md`](spec.md)
- **Status:** Drafting

> **Plan contract:** this is the implementation strategy. Unlike the spec, this document is allowed to change as you learn. When it changes substantially (a different approach, not just a re-ordering), note why in the changelog at the bottom.

## Approach

Single-PR implementation that lands the contract bump, schema rule, resolver rename + scope-branching, safety helper + path-jail widening, CLI flag, install-time messages, eight packs' contract bump, orphan-projection reliability fix, migration in-band detection, documentation surface, and tests in one merge per RFC-0004 atomicity (inherited from the sibling [`pack-allowed-adapters/spec.md`](../pack-allowed-adapters/spec.md)). Order of operations: (1) contract + safety helper — *the floor* (the data substrate the path-jail and resolver consult); (2) resolver rename + scope-branching + schema validator widening — *the central rail*; (3) CLI flag, handler-level mutex, removal of user-only `--adapter` binding — *the imperative escape valve*; (4) eight packs' v0.7 bump — *the actual adopter behaviour change at default-adapter time*; (5) install-time messages + in-band detection — *the migration safety net*; (6) projection-vs-state write-order fix + `--force` override — *the reliability gap RFC-0012 § Reliability closes*; (7) documentation + RFC-0011 erratum + ROADMAP; (8) gates. Tests-first per task. The task graph is **largely sequential** — T2 depends on T1, T3 on T1+T2, etc. — because the contract bump is the shared substrate. The path-jail widening (part of T2) is the structural prerequisite for repo-scope per-IDE writes; without it `safety.write_jailed` refuses every `<repo>/.kiro/skills/X` write. Supervisor mode (parallel implementers) is unlikely to earn its keep here.

## Constraints

- **Constrained by:** [RFC-0012](../../rfc/0012-repo-scope-per-adapter-projection.md) — every task implements one or more of RFC-0012's commitments; deviations require the RFC to amend first.
- **Builds on:** [RFC-0011](../../rfc/0011-pack-allowed-adapters.md) six-step lookup, `[pack.install] allowed-adapters` field, `PackState.adapter` (AC10a) and state-hint short-circuit (AC10b); [RFC-0004](../../rfc/0004-install-scope-per-pack.md) `[pack.install]` table + scope-resolution helper; [RFC-0009](../../rfc/0009-codex-native-skills.md) live codex `direct-directory` projection at `adapter.toml` (kept untouched).
- **Single PR per RFC-0004 atomicity.** Partial landings risk a known-bad coherence state (schema accepts `allowed-prefixes.repo` but path-jail still refuses repo-scope per-IDE writes; or eight packs bump to v0.7 but resolver still routes by legacy heuristic at repo scope).
- **Schema enum hydrated in Python**, not in `pack.schema.json` literal (RFC-0011 convention; this spec doesn't change it).
- **Refuse-and-explain wording fixed by RFC**; tests assert exact strings.
- **No new third-party Python dependency.** stdlib + existing `jsonschema`.

## Construction tests

Most construction tests live under **Tasks** below (per-task `Tests:`).

**Cross-cutting tests** (span more than one task):

- **End-to-end install integration suite** at `packages/agentbundle/tests/integration/test_install_repo_scope_per_adapter.py`. Installs each of the eight shipped packs against fixture repos at each of the four shipped adapters' projection shapes. Three migration triggers exercised end-to-end (shape-mismatch, adapter-disagreement, orphan-recovery). Upgrade-with-state-hint at repo scope covers AC10b parity. This *is* T8; cross-referenced here for the cross-cutting view. Covers spec AC33; prerequisites span T2, T3, T4, T5, T6, T7.
- **`pre-pr.py` end-to-end** — `python3 tools/hooks/pre-pr.py` exits 0 on the final tree. Covers spec AC36; spans every task.
- **`make build-self FORCE=1` clean** after the final commit. Covers spec AC35; spans T4 (the eight `pack.toml` bumps) and T9 (documentation that touches `packs/core/seeds/` via the ROADMAP).

**Manual verification:**

- Read the diff end-to-end against RFC-0012 *Follow-on artifacts* list (AC25-AC29). Spot-check the README's extended `Where primitives land` table renders correctly on GitHub. Confirm the RFC-0011 erratum block reads cleanly without contradicting RFC-0011's body.

## Tasks

Order matters — listed in the order they should be done. Most `Depends on:` chains are linear because the contract bump is the shared substrate; T6 (projection dispatch, `Depends on: T1, T2, T3`) and T7 (install-time messages + in-band detection, `Depends on: T2, T5, T6`) both consume the resolver landed in T2 and the safety helper from T2.

### T1: Contract bump v0.6 → v0.7 plus `[adapter.copilot.scope]` table plus `allowed-prefixes.repo` on every adapter (atomic edit)

**Depends on:** none

**Spec mapping:** AC1, AC2, AC4. Mode: goal-based check (contract is data; test is grep + version-equality assertion + schema-load).

**Atomicity requirement:** the version bump AND the new copilot scope table AND every adapter's `allowed-prefixes.repo` addition land in a **single commit**. Splitting these leaves an intermediate snapshot (`version = "0.7"` without `allowed-prefixes.repo` keys) that breaks every dependent test (T2's path-jail expects the keys; T8's integration tests expect the copilot scope table). Verify atomicity by reviewing the commit diff before merging T1.

**Tests:**
- `packages/agentbundle/agentbundle/build/tests/test_contract_v07.py::test_contract_version_is_07` — load `_data/adapter.toml`, assert `tomllib.loads(...)["contract"]["version"] == "0.7"`.
- `test_contract_v07.py::test_copilot_scope_table_shape` — assert `[adapter.copilot.scope]` exists with `repo == "."`, `allowed-prefixes.repo == [".github/instructions/"]`, **no `user` key**.
- `test_contract_v07.py::test_every_adapter_has_allowed_prefixes_repo` — iterate every `[adapter.<name>.scope]` table; assert `allowed-prefixes.repo` is present and is a non-empty list.
- `test_contract_v07.py::test_existing_user_prefixes_invariants` — parse the contract and assert property-based invariants per adapter rather than against a frozen snapshot: `claude-code`'s `allowed-prefixes.user` contains `.claude/` and `.agentbundle/`; `kiro`'s contains `.kiro/` and `.agentbundle/`; `codex`'s contains `.agents/skills/` and `.agentbundle/`. The invariants are spec-derived (RFC-0011 § *Contract bump* surface) and don't require a checked-in v0.6 fixture file. A frozen snapshot is brittle and would be its own maintenance surface; the invariant form survives header-comment edits and `allowed-prefixes` list-order changes.
- Schema validator AC4 test: a fixture contract with `repo` omitted from any adapter's `scope` table fails validation with pinned refusal text.

**Approach:**
- Edit `packages/agentbundle/agentbundle/_data/adapter.toml`:
  - Bump `[contract] version` `"0.6"` → `"0.7"`.
  - Add `[adapter.copilot.scope]` table per RFC-0012 § *Contract bump v0.6 → v0.7* (`repo = "."`, `allowed-prefixes.repo = [".github/instructions/"]`).
  - Add `allowed-prefixes.repo` key to each of `[adapter.claude-code.scope]`, `[adapter.kiro.scope]`, `[adapter.codex.scope]` per the same RFC section.
  - Update the header comment to name RFC-0012 / this spec alongside existing pointers.
  - **All edits in one commit.**
- Run `make build-self FORCE=1` to propagate any projected `adapter.toml` copies.
- Extend the schema validator at `packages/agentbundle/agentbundle/commands/validate.py` to enforce AC4 (`repo` key mandatory per scope table; `allowed-prefixes.repo` mandatory; `user` stays optional). Add the corresponding test.

**Done when:** the five contract tests pass and `make build-self FORCE=1` produces a clean working tree.

---

### T2: Safety helper `scan_for_pack_artifacts` + path-jail widening + resolver rename + scope-branching

**Depends on:** T1

**Spec mapping:** AC7, AC8, AC9, AC10, AC11, AC12, AC13, AC30, AC31. Mode: TDD (resolver is a pure function; safety helper is pure I/O over a fixture tree).

**Tests:**

Two test modules, both new or extended:

1. **Extend `packages/agentbundle/tests/unit/test_resolve_user_scope_target_adapter.py`** with `scope=repo` parametrise. Cases per spec AC30:
   - Per-adapter repo-scope projection with `--adapter <X>`: claude-code → `.claude/`, kiro → `.kiro/`, codex → `.agents/skills/`, copilot → `.github/instructions/`.
   - Default-adapter resolution at repo scope (no `--adapter`, no probe).
   - **`test_repo_scope_does_not_probe_dot_claude`** — load-bearing asymmetry: `<repo>/.claude/` populated, `--adapter kiro` passed, assert resolver returns `"kiro"`.
   - **`test_step0_publisher_drift_scope_uniform`** — parametrise (`scope=user`, `scope=repo`); pack declares `allowed-adapters = ["nonexistent"]`; assert refusal text identical modulo `<verb>` prefix.
   - **`test_step1_copilot_admitted_at_repo_user_refused`** — scope-conditional subcheck: same pack at both scopes; copilot admits at repo, refuses at user with pinned `v0.7` wording.
   - Legacy heuristic at repo scope for `< v0.7` packs without `allowed-adapters`: returns `"claude-code"` or `"kiro"`, never `"codex"`/`"copilot"`.
   - **State-hint short-circuit at repo scope (AC10b parity)** — install under `--adapter kiro`; populate `<repo>/.claude/`; upgrade; assert `"kiro"` returned (no cross-adapter refusal).
   - `_make_pack` helper widens to materialise `pack.toml` for the scope-table read (RFC-0012 § *High-leverage construction tests* — "resolver test fixture widens to materialise `pack.toml`").
   - `fake_repo` fixture lands alongside `fake_home`.

2. **New module `packages/agentbundle/tests/unit/test_safety_repo_scope_prefixes.py`** per spec AC31:
   - For each adapter (`claude-code`, `kiro`, `codex`, `copilot`): write to an in-prefix repo-scope path succeeds; write to an out-of-prefix path fails with `PathJailError`.
   - `scan_for_pack_artifacts` against a fixture tree with mixed orphan and present files returns only the orphan list.
   - `scan_for_pack_artifacts` is read-only (asserts no state mutation against a `tmp_path` snapshot).

**Approach:**

- **Add `safety.scan_for_pack_artifacts(root: Path, allowed_prefixes: list[str]) -> list[Path]`** to `packages/agentbundle/agentbundle/safety.py`. Walks `<root>/<prefix>/` for each prefix; returns every file found. No state mutation; pure I/O.
- **Widen the existing path-jail check inside `safety.write_jailed`** to read `allowed-prefixes.repo` at repo scope. Today the check consults the user-scope prefix list by construction (repo scope previously had no per-IDE projection). Thread the repo-scope prefix list through the existing call sites; preserve the user-scope behaviour byte-identically.
- **Rename `_resolve_user_scope_target_adapter` → `_resolve_target_adapter`** at `install.py:1383`. The function gains a `scope: str` keyword argument:
  ```python
  def _resolve_target_adapter(
      pack_dir: Path,
      *,
      scope: str,                             # "user" | "repo"
      adapter: str | None,
      allowed_adapters: list[str] | None,
      contract_version: str | None,
      state_adapter: str | None = None,
      command_name: str = "install",
  ) -> str:
  ```
- **Implement the six-step lookup** with the three scope-branched points (Steps 0, 4, 5) per spec AC9:
  - **Step 0 (publisher-drift refusal)** — scope-uniform on the refusal text modulo `<verb>` prefix. At repo scope, the user-scope-capability subcheck is **skipped** (Copilot is admissible at repo scope).
  - **Step 1 (`--adapter` override)** — validated against `allowed-adapters` (when declared); else, at user scope against `user_scope_capable_adapters_from_contract()`; at repo scope against `shipped_adapters_from_contract()`. Refuse with pinned message on miss.
  - **Step 2 (state-hint short-circuit)** — scope-uniform; RFC-0011 substrate.
  - **Step 3 (contract-version gate)** — scope-uniform; uses existing `contract_supports_hook_wiring(version)` predicate (RFC-0011 substrate; reused).
  - **Step 4** — scope-branched: user scope walks the per-adapter probe table; repo scope returns `DEFAULT_ADAPTER` if in `allowed-adapters`, else `allowed-adapters[0]`. **No probe at repo scope.**
  - **Step 5 (legacy heuristic)** — `.apm/agents/*.md` present ⇒ `"kiro"`; else `"claude-code"`. At repo scope this only fires for `< v0.7` packs without `allowed-adapters` and can only return claude-code/kiro (Drawback #7 surface).
- **Update every call site.** Run `grep -rn "_resolve_user_scope_target_adapter" packages/agentbundle/agentbundle/ packages/agentbundle/tests/` and rename each hit; the predicate must return zero hits post-rename. Current-snapshot offenders: function definition at `install.py:1383`, self-naming docstring at `install.py:1234-1235` (inside `_render_for_user_scope`), call sites at `install.py:329` and `install.py:1260`, imports at `upgrade.py:235` and `upgrade.py:348`, calls at `upgrade.py:257` and `upgrade.py:352`. (Note: `upgrade.py:240` is `_render_for_user_scope(...)`, a different function — do not touch.) Existing callers pass `scope="user"` (preserves user-scope behaviour byte-identically); the new repo-scope install code path in T3/T6 passes `scope="repo"`.
- **Update step-count literals across all surfaces** per spec AC8's grep-and-allow-list. Run the narrowed predicate `rg -n "(four|five|six)[- ]step.*(lookup|resolver|resolution)" packages/ docs/` (unrelated phrases like "four-step migration" / "five-step action plan" are excluded by construction). Flip every code-surface hit to "six-step (0–5)" per AC8's `flip` disposition; preserve Changelog-entry hits per the `preserve as historical record` disposition. The function docstring at `install.py:1393` opens with "The six-step lookup" — verify and re-enumerate the body steps 0–5 (the current body enumerates 0–4 = five steps; AC8 requires the body to actually match the six-step claim).
- **Widen the schema validator** at `validate.py` so `[pack.install] allowed-adapters` validation fires at both scopes; the user-scope-capability subcheck becomes scope-conditional. Test pins both behaviours (AC11).

**Done when:** every parametrized test case in the two test modules passes; the new `scope=repo` parametrise actually invokes `_resolve_target_adapter(scope="repo", ...)` against the four shipped adapters with a full pack.toml fixture (the unit layer exercises the resolver's repo-scope branches directly — not via stubs in T6's dispatch tests); `grep -rn "_resolve_user_scope_target_adapter" packages/` returns zero hits; existing user-scope tests continue to pass byte-identically; `pytest packages/agentbundle/` exits 0.

---

### T3: CLI surface — `--emit-install-routes` flag, remove user-scope-only `--adapter` binding, handler-level mutex

**Depends on:** T2

**Spec mapping:** AC14, AC15, AC16, AC17, AC32. Mode: TDD (argparse + refusal-path correctness).

**Tests:**

New module `packages/agentbundle/tests/unit/test_install_argparse_emit_install_routes.py`. Cases:

- **`--emit-install-routes` parses at both scopes** (argparse-level admission; handler enforces the binding).
- **`--adapter kiro --scope repo` admitted** — RFC-0011's pinned `install: --adapter is bound to --scope user` no longer fires; assert install proceeds (or fails at a later step, not at the bound-to-user-scope check).
- **`--emit-install-routes --scope user` refused** — assert stderr exact match `install: --emit-install-routes is bound to --scope repo`; non-zero exit.
- **`--emit-install-routes` with no `--scope` flag against a pack whose `[scope] default-scope = "user"` refused** — pins that the binding consults `requested_scope` (resolved), not `args.scope` (raw CLI flag). The test fixture is a v0.7 user-scope-eligible pack with default-scope user; invoke `agentbundle install --pack <X> --emit-install-routes <repo>` (no `--scope`); assert stderr exact match `install: --emit-install-routes is bound to --scope repo`; non-zero exit. Without this test, an implementation that reads `args.scope` (None when omitted) silently bypasses the binding and the AC30b case 1 ordering test still passes (case 1 supplies `--scope user` explicitly).
- **`--adapter X --emit-install-routes` at `--scope repo` refused** — assert stderr exact match `install: --adapter and --emit-install-routes are mutually exclusive at --scope repo`; non-zero exit.
- **Implementation does NOT use `argparse.add_mutually_exclusive_group`** — assert via introspection (`install_subparser._mutually_exclusive_groups` empty for these args) or via behavioural test that the same flag combo at user scope refuses with a *different* pinned message (the scope-conditional shape).
- **Existing tests asserting `install: --adapter is bound to --scope user`** are deleted or flipped per AC17. The plan enumerates them below.

**Approach:**

- In `packages/agentbundle/agentbundle/cli.py` `install` subparser:
  - Add `--emit-install-routes` as `action="store_true"`. Help text matches RFC-0012 § *CLI surface* wording.
  - Argparse-level `choices=` on `--adapter` continues to be hydrated from `shipped_adapters_from_contract()` (RFC-0011 substrate; unchanged).
- In `packages/agentbundle/agentbundle/commands/install.py`:
  - **Remove the pinned refusal at `:112-115` and `:204-213`** (`install: --adapter is bound to --scope user`).
  - **Add the handler-level mutex** *after* Step 2 (`scope_mod.resolve()` at `install.py:182`) — placement is load-bearing for AC30b case 1's tier-1-before-tier-2 ordering; placement before scope resolution silently inverts the tiers. The checks consult `requested_scope` (the resolved scope), not `args.scope` (the raw CLI flag), matching the existing-codebase precedent at `install.py:197` (`if force_merge and requested_scope != "user"`):
    - If `requested_scope == "user" and args.emit_install_routes`: emit `install: --emit-install-routes is bound to --scope repo`; exit non-zero.
    - If `requested_scope == "repo" and args.adapter and args.emit_install_routes`: emit `install: --adapter and --emit-install-routes are mutually exclusive at --scope repo`; exit non-zero.
    The `requested_scope` semantics matter when `--scope` is omitted at the CLI and the pack's `[scope] default-scope` provides the value — the resolved scope is what the rest of the install handler operates on, so the mutex must match.
  - The refusal-ordering invariant (RFC-0012 § *Pinned refusal messages*): `scope.resolve()` declared-scope refusals fire first; handler-level flag refusals second; resolver-internal refusals (publisher-drift at step 0; `--adapter` at step 1) third.
- **Enumerate AC17's test deletions/flips.** Sweep with `grep -rn "adapter is bound" packages/agentbundle/tests/`; the predicate must return zero hits post-PR. **Current-snapshot offender (verify in EXECUTE):** the single test method `test_adapter_at_repo_scope_refused` at `tests/integration/test_install_user_scope_allowed_adapters.py:186-196` has one `--scope repo --adapter` invocation and one assertion (`self.assertIn("--adapter is bound to --scope user", stderr)`). The method's purpose evaporates with AC15; the cleanest fix is **deletion**. If kept, rewrite the single assertion to assert the install proceeds at `--scope repo` (or fails at a later step — not at the bound-to-user-scope check). Re-run the grep after the change to confirm zero hits.

**Done when:** all argparse-test cases pass; the sweep for `"adapter is bound"` returns no live assertions; `pytest packages/agentbundle/` exits 0.

---

### T4: Constant rename `DEFAULT_USER_SCOPE_ADAPTER` → `DEFAULT_ADAPTER` + deprecation alias

**Depends on:** T2

**Spec mapping:** AC18, AC19. Mode: TDD (rename + DeprecationWarning assertion).

**Tests:**

Extend `tests/unit/test_resolve_user_scope_target_adapter.py` (or a new sibling module if cleaner):

- **`test_default_adapter_value_unchanged`** — `from agentbundle.scope import DEFAULT_ADAPTER; assert DEFAULT_ADAPTER == "claude-code"`.
- **`test_deprecation_alias_fires_warning`** — `import warnings; with warnings.catch_warnings(record=True) as w: warnings.simplefilter("always"); from agentbundle.scope import DEFAULT_USER_SCOPE_ADAPTER; assert any(issubclass(x.category, DeprecationWarning) for x in w)`. Assert the value equals `DEFAULT_ADAPTER`.
- **Existing test at `test_resolve_user_scope_target_adapter.py:139`** flips to import `DEFAULT_ADAPTER` directly (per RFC-0012 § *Implementation-spec-level ACs surfaced on review*).

**Approach:**

- In `scope.py`:
  - Rename `DEFAULT_USER_SCOPE_ADAPTER` → `DEFAULT_ADAPTER` at line 45.
  - Below the new name, add the deprecation alias via PEP 562 `__getattr__`:
    ```python
    def __getattr__(name: str) -> str:
        if name == "DEFAULT_USER_SCOPE_ADAPTER":
            import warnings
            warnings.warn(
                "DEFAULT_USER_SCOPE_ADAPTER is deprecated; use DEFAULT_ADAPTER. "
                "Removed in agentbundle 0.2.0.",
                DeprecationWarning,
                stacklevel=2,
            )
            return DEFAULT_ADAPTER
        raise AttributeError(name)
    ```
    Module-level `__getattr__` fires only on access of the deprecated name; direct access to `DEFAULT_ADAPTER` is warning-free.
  - The removal version `agentbundle 0.2.0` is single-sourced in RFC-0012 § *Module-level constant rename*; the warning message references it once.
- Update call sites at `install.py:1414, 1433, 1519, 1520` to reference `DEFAULT_ADAPTER` directly.
- **Update the existing test's monkeypatch targets at `test_resolve_user_scope_target_adapter.py:138-139` and `:154-155`** — these are `monkeypatch.setattr` calls; flip the **string targets** from `"agentbundle.scope.DEFAULT_USER_SCOPE_ADAPTER"` to `"agentbundle.scope.DEFAULT_ADAPTER"` (the values being patched in — `"kiro"` and `"codex"` — are unchanged). Also flip the comment at line 133 (`# DEFAULT_USER_SCOPE_ADAPTER` → `# DEFAULT_ADAPTER`).

**Done when:** the three test cases above pass; `grep -rn "DEFAULT_USER_SCOPE_ADAPTER" packages/agentbundle/agentbundle/` returns only the deprecation alias declaration (no live consumers); `pytest packages/agentbundle/` exits 0.

---

### T5: Eight packs bump to v0.7 (four user-scope-capable + four repo-only)

**Depends on:** T1, T2

**Spec mapping:** AC5, AC6. Mode: goal-based check (TOML edit + projection-noop assertion).

**Tests:**

New module `packages/agentbundle/agentbundle/build/tests/test_shipped_packs_v07_declarations.py`:

- For each of `atlassian`, `figma`, `converters`, `contracts`: load `pack.toml`, assert `[pack.adapter-contract] version == "0.7"`; assert `[pack.install] allowed-adapters == ["claude-code", "kiro", "codex"]` (unchanged from RFC-0011).
- For each of `core`, `governance-extras`, `user-guide-diataxis`, `monorepo-extras`: assert `[pack.adapter-contract] version == "0.7"` (bumped from `"0.2"`); assert no `allowed-adapters` declared.
- `make build-self FORCE=1` is a noop on the eight packs' projections after the bump (no stray content drift; only the `pack.toml` edits themselves register in `git status`).

**Approach:**

- For each of the eight packs, edit `packs/<pack>/pack.toml`:
  - Bump `[pack.adapter-contract] version`:
    - User-scope-capable: `"0.6"` → `"0.7"`.
    - Repo-only: `"0.2"` → `"0.7"`.
  - No other field changes.
- Run `make build-self FORCE=1`.
- Verify `git status --short` is clean modulo the eight `pack.toml` edits themselves.

**Done when:** the test cases above all pass; `make build-self FORCE=1` produces a clean working tree.

---

### T6: Repo-scope projection dispatch — adopter-side per-IDE direct writes

**Depends on:** T1, T2, T3

**Spec mapping:** AC9 (Step 4 repo-scope branch), AC13 (path-jail enforcement). Mode: TDD (dispatch + path-jail integration).

**Tests:**

Extend `tests/unit/test_resolve_user_scope_target_adapter.py` with cases that exercise the post-resolution projection at repo scope:

- For each of the four adapters: stub the resolved adapter, drive `_render_for_repo_scope` (the new bridge function, mirroring `_render_for_user_scope`), assert the right `<adapter>.project(...)` is invoked with `root=<repo>`, not `~/`.
- Integration coverage in T8 (the full smoke); this T6 layer is the unit-test surface.

**Approach:**

- The current repo-scope code path at `install.py` runs the dist-tree-producing recipes (`per-pack-claude-plugin`, `per-pack-apm-package`, `marketplace`). Add a **branching condition at the install handler**:
  - If `args.scope == "repo" and not args.emit_install_routes`: invoke a new helper `_render_for_repo_scope(pack_dir, *, adapter, allowed_adapters, contract_version, state_adapter, command_name)` that mirrors `_render_for_user_scope` but writes into `<repo>/` instead of `~/`.
  - If `args.scope == "repo" and args.emit_install_routes`: invoke the existing dist-tree recipes (unchanged path).
- `_render_for_repo_scope`:
  - Calls `_resolve_target_adapter(scope="repo", ...)` to get the target adapter.
  - Dispatches to the appropriate adapter projection module (`claude_code.project(...)`, `kiro.project(...)`, `codex.project(...)`, `copilot.project(...)`). For codex this is the same `direct-directory` projection RFC-0009 ships; for copilot it's the build-pipeline's `[adapter.copilot.projection]` recipes.
  - Threads `allowed-prefixes.repo` from the contract into `safety.write_jailed` so the path-jail fences each write under `<repo>/.kiro/` (etc.).
- **Self-hosting overlay reference.** RFC-0012 § *Prior art* names `packages/agentbundle/agentbundle/build/recipes/self-host.toml` as the in-tree mechanism that already produces per-IDE direct writes for the catalogue's self-host. The adopter-side dispatch is a generalisation of that mechanism — the projection rules are identical; only the root differs.
- **Stdout line** at the end of a successful repo-scope per-IDE install: `installed: <pack> @ repo via <adapter>` (AC20). For `--emit-install-routes`: `emitted install routes for <pack> at <route-list>`.

**Done when:** the dispatch unit tests pass; T8's integration smoke confirms per-adapter projection at repo scope writes to the right directory.

---

### T7: Install-time message rail + in-band detection of pre-RFC-0012 state + orphan-projection refusal

**Depends on:** T2, T5, T6

**Spec mapping:** AC20, AC21, AC22, AC23, AC24. Mode: TDD (format-string + state-classification + refusal correctness).

**Tests:**

New module `packages/agentbundle/tests/unit/test_install_messages_repo_scope.py`. Cases:

- Successful repo-scope install of a v0.7 pack with explicit `--adapter kiro`: stdout contains `installed: <pack> @ repo via kiro`.
- Successful repo-scope install with `--emit-install-routes`: stdout contains `emitted install routes for <pack> at <repo>/claude-plugins/<pack>/ and <repo>/apm/<pack>/` (substring per-route; not the full string per RFC-0012 § *Install-time message rail (repo scope)*).
- Default-adapter (no `--adapter`) at repo scope against `core`: stdout contains `installed: core @ repo via claude-code`; no suffix.
- **No "other declared adapters" suffix at repo scope** (AC21) — RFC-0011's suffix logic does not fire here; assert absence.

New module `packages/agentbundle/tests/unit/test_install_inband_detection.py`. Cases per AC24:

- **Trigger (b) shape-mismatch:** fixture `state.toml` with a `[packs.<pack_name>]` row recorded; dist-tree files exist at `<repo>/claude-plugins/<pack_name>/`; resolver picks claude-code (matching `state.adapter == "claude-code"`); install at repo scope; assert pinned stderr names dist-tree paths to remove; assert short-circuit silence on second install call within the session keyed by `(<repo>, <pack_name>)`.
- **Trigger (a) adapter disagreement:** fixture `state.toml[packs.<pack_name>].adapter == "claude-code"`; **no dist-tree files exist** (so (b) doesn't fire); resolver picks kiro; assert pinned stderr names the recorded vs. resolved adapter.
- **Trigger (c) orphan recovery:** `state.toml` has no row for `<pack_name>` (mutually exclusive with (b)); orphan projection files at `<repo>/.kiro/skills/X/SKILL.md`; install at `--scope repo` without `--force`; assert pinned `install: orphan projection files for pack <name> at <prefix> — prior install interrupted; rerun with --force to clean and reinstall, or delete the listed paths and rerun`; assert non-zero exit.
- **Per-pack precedence (b)+(c) test** — fixture has a state row for pack A AND dist-tree files for pack A (so (b) would fire for pack A) AND orphan files for pack B at `<repo>/.kiro/skills/B/SKILL.md` with no state row for B (so (c) would fire for pack B in isolation); call install for pack A first and assert (b)'s line fires (not (c)'s); call install for pack B in the same session and assert (c)'s line fires; verifies the per-`(<repo>, <pack_name>)` evaluation is correctly scoped.

New module `packages/agentbundle/tests/unit/test_install_orphan_force.py`. Cases per AC23:

- **`--force` clears orphans and proceeds** — orphan files at `<repo>/.kiro/`; install with `--force`; assert orphans deleted, install completes, `state.files` matches every on-disk path.
- **Monkeypatch falsifier:** monkeypatch `safety.write_jailed` to raise on the `N`th call **with `N ≥ 2`** (so at least one file lands on disk before the crash and the post-crash shape is non-empty — `N=1` would leave the repo orphan-free and the falsifier becomes a no-op). Assert no state row written; rerun install without `--force` fires AC22; rerun with `--force` completes and `state.files` matches every on-disk path. Per memory rule `feedback_rfc_code_precondition`, this test is co-landed with the §Reliability fix in the implementation PR — not deferred.

**Approach:**

- In `packages/agentbundle/agentbundle/commands/install.py`:
  - Extend the existing `installed: <pack> @ <scope>` print (RFC-0004's rail) with the `via <adapter>` clause for repo scope (mirroring RFC-0011 AC14's user-scope addition). For `--emit-install-routes`: emit the `emitted install routes for ...` line instead. The route list is the **per-pack-emitting subset** of `DEFAULT_RECIPES` — today the two recipes that produce `<repo>/<route>/<pack>/` directories (`per-pack-claude-plugin` → `<repo>/claude-plugins/<pack>/`; `per-pack-apm-package` → `<repo>/apm/<pack>/`). The `marketplace` recipe at `build/main.py:167-171` is excluded because it doesn't produce a per-pack directory. The list is formatted via the `_format_route_list` helper introduced by AC20 (`N=1 → "X"`; `N=2 → "X and Y"`; `N≥3 → "X, Y, and Z"`). Today N=2; a future codex-plugins addition extends N automatically.
- **In-band detection** (AC24) — a new helper `_classify_pre_rfc0012_state(root, pack_name, state, resolver_pick) -> str | None` returns a pinned stderr line or `None`. Triggers evaluated in precedence order (b)→(a)→(c); first match wins. Detection runs once per pack per session (use a module-level `set` keyed by `(root, pack_name)`).
- **Orphan-projection refusal** (AC22) — invoked before classifying any file. Reads `<repo>/.agentbundle-state.toml`; if no row for pack AND `safety.scan_for_pack_artifacts(root, allowed_prefixes)` is non-empty, emit the pinned stderr; exit non-zero unless `--force` is passed.
- **`--force` override** (AC23) — pre-existing flag at `install.py` (RFC-0004); the orphan-clean path is new. If `--force`: delete every orphan file `scan_for_pack_artifacts` returned, then proceed with install.
- Pin the literal `<RFC-0012-version>` placeholder at **one** site in `install.py` (e.g., a module-level `_RFC_0012_VERSION = "0.2.0"` constant aligned with the deprecation removal version) and reference it from each trigger.

**Done when:** all eleven message / detection / orphan tests pass; integration smoke (T8) confirms the messages appear in real installs.

---

### T8: End-to-end install integration tests

**Depends on:** T2, T3, T4, T5, T6, T7

**Spec mapping:** AC33. Mode: TDD (integration; treats install as a black box and asserts state-file + filesystem + stdout outcomes).

**Tests:**

New module `packages/agentbundle/tests/integration/test_install_repo_scope_per_adapter.py`. Parametrise over (pack ∈ eight shipped packs) × (case ∈ listed below):

- **Kiro greenfield.** Fixture `<repo>` empty; `agentbundle install --pack <pack> --scope repo --adapter kiro <repo>`; assert `<repo>/.kiro/skills/<skill>/SKILL.md` exists (or `<repo>/.kiro/agents/<agent>` for agent primitives); assert `<repo>/.agentbundle-state.toml` `packs.<pack>.adapter == "kiro"`; stdout matches `installed: <pack> @ repo via kiro`.
- **Codex greenfield.** Same shape, `--adapter codex` → `<repo>/.agents/skills/`.
- **Copilot greenfield.** Same shape, `--adapter copilot` → `<repo>/.github/instructions/<pack>.md`.
- **Claude Code default.** No `--adapter` → `<repo>/.claude/skills/`.
- **`--emit-install-routes`.** Assert `<repo>/claude-plugins/<pack>/` AND `<repo>/apm/<pack>/` exist; assert per-IDE directories do NOT exist; assert stdout matches `emitted install routes for <pack> at ...`.
- **Upgrade with state-hint (AC10b at repo scope).** Two-step: install under `--adapter kiro`; populate `<repo>/.claude/` post-install; `agentbundle upgrade --pack <pack> --scope repo <repo>`; assert state stays `adapter = "kiro"` and the cross-adapter refusal at `upgrade.py:365-377` does not fire.
- **Migration trigger (b) shape-mismatch.** Fixture: `<repo>/.agentbundle-state.toml` has a `[packs.<pack>]` row recorded (any prior state contents); `<repo>/claude-plugins/<pack>/` populated with dist-tree files; install at repo scope without `--adapter` and without `--emit-install-routes`; assert stderr fires (b)'s pinned line; assert install refuses (non-zero exit). (No CLI-version field is read — the pre-RFC-0012 signal is on-disk dist-tree shape + entry on the per-IDE install code path, per spec AC24's narrowed inference rule.)
- **Migration trigger (a) adapter disagreement.** Fixture: `state.toml[packs.<pack>].adapter == "claude-code"` AND no dist-tree files on disk (so (b) doesn't fire); pack `allowed-adapters = ["claude-code", "kiro"]`; install with `--adapter kiro`; assert (a)'s pinned line.
- **Orphan recovery (c).** Fixture: `<repo>/.kiro/skills/<skill>/SKILL.md` orphan; no state row; install without `--force` fires AC22; rerun with `--force` completes.

**Approach:**

- Reuse the existing integration-test fixtures (`tmp_path` + monkeypatched `HOME` + `<repo>` argument). The `<repo>` is a `tmp_path` subdirectory; no `~/` writes happen.
- Assert filesystem state (which `<repo>/.<ide>/skills/<skill>/SKILL.md` exists) and state-file content (parse `<repo>/.agentbundle-state.toml` and check `packs.<pack>.adapter`).
- Don't fabricate test packs unless the shipped eight are inadequate.

**Done when:** every parametrized case passes; `pytest packages/agentbundle/tests/integration/` exits 0.

---

### T9: README + migration guide + RFC-0011 erratum + ROADMAP

**Depends on:** T1, T5

**Spec mapping:** AC25, AC26, AC27, AC28, AC29. Mode: manual QA + goal-based grep.

**Tests:**

- Goal-based grep: `README.md` `Where primitives land` table contains a `repo-scope` column for each of the four shipped adapters; per-adapter substrings `<repo>/.claude/skills/`, `<repo>/.kiro/skills/`, `<repo>/.agents/skills/`, `<repo>/.github/instructions/`.
- Goal-based grep: `docs/guides/explanation/install-routes.md` mentions `--emit-install-routes` and the default per-IDE projection at repo scope.
- Goal-based grep: `docs/guides/how-to/v06-to-v07-pack-upgrade.md` exists; contains substrings `[pack.adapter-contract]`, `0.7`, `--emit-install-routes`, `v0.2` (the repo-only-pack jump origin).
- Goal-based grep: `docs/rfc/0011-pack-allowed-adapters.md` ends with an erratum block recording the three RFC-0012 reconciliations (step-count, resolver rename, deprecation alias).
- Goal-based grep: `docs/ROADMAP.md` contains the line `repo-scope-per-adapter-projection` with the spec's open ACs.
- Manual: read each new file end-to-end against AC25-AC29 commitments.

**Approach:**

- Edit `README.md` (per AC26):
  - Extend `Where primitives land` table with per-adapter repo-scope landing paths. Pack rows continue to link into the table (single canonical location per memory rule `feedback_writing_style`).
- Edit `docs/guides/explanation/install-routes.md` (per AC27) to note the default per-IDE projection at repo scope and the `--emit-install-routes` opt-in.
- Write `docs/guides/how-to/v06-to-v07-pack-upgrade.md` (per AC25): one section for the contract bump; one for the v0.2 → v0.7 repo-only-pack jump (Drawback #7); one for the uninstall + reinstall flow on AC24 (a) disagreement.
- Append erratum block to `docs/rfc/0011-pack-allowed-adapters.md` (per AC28) — recording all three step-count drifts plus the renames: (i) RFC-0011's body literal "four-step" at `:59` and `:74`; (ii) the function docstring's pre-fix "six-step" claim that enumerated only 0–4 (five-step body); (iii) RFC-0012's reconciliation to "six-step (0–5)"; (iv) the resolver rename to `_resolve_target_adapter` plus the `DEFAULT_USER_SCOPE_ADAPTER` → `DEFAULT_ADAPTER` rename and deprecation alias. The erratum names RFC-0012 as the closing reference. RFC-0011 is Accepted/frozen, so this is an appended block, not an in-body edit.
- Add `docs/ROADMAP.md` section for `repo-scope-per-adapter-projection` (per AC29) listing the open ACs.

**Done when:** the five grep cases pass; manual read confirms each commitment landed.

---

### T10: Sibling-spec amendments — `pack-allowed-adapters`, `agent-spec-cli`, `distribution-adapters`

**Depends on:** T1, T2, T3

**Spec mapping:** spec's *Constrained by* line (the three sibling specs amended in-PR). Mode: manual QA + goal-based grep.

**Tests:**

- Goal-based grep: `docs/specs/pack-allowed-adapters/spec.md` Changelog gains an entry naming RFC-0012's scope-conditional widening of AC15.
- Goal-based grep: `docs/specs/agent-spec-cli/spec.md` records the `--emit-install-routes` flag addition and the `--adapter` scope-binding removal.
- Goal-based grep: `docs/specs/distribution-adapters/spec.md` Changelog gains a v0.6 → v0.7 entry with conformance cases for repo-scope per-IDE projection.

**Approach:**

- Edit `docs/specs/pack-allowed-adapters/spec.md`: add a Changelog entry naming RFC-0012's scope-conditional widening of the user-scope-capability subcheck. Don't restate RFC-0012's content — link to it.
- Edit `docs/specs/agent-spec-cli/spec.md`: the `install` CLI surface section gains the `--emit-install-routes` flag and notes that `--adapter` is now accepted at both scopes (the binding refusal removed).
- Edit `docs/specs/distribution-adapters/spec.md`: the conformance section gains repo-scope per-IDE projection cases (per shipped adapter); the Changelog records the v0.6 → v0.7 bump.

**Done when:** the three grep cases pass; manual read confirms each amendment is consistent with the source spec.

---

### T11: Gates pass — final sweep

**Depends on:** T1, T2, T3, T4, T5, T6, T7, T8, T9, T10

**Spec mapping:** AC34, AC35, AC36, AC37. Mode: goal-based check (gates).

**Tests:**

- `pytest packages/agentbundle/` exits 0.
- `make build-self FORCE=1 && git status --short` shows no changes.
- `python3 tools/hooks/pre-pr.py` exits 0.
- CI replication of `build-check` linux + windows, `pytest` windows, `docs` lint suite — verified post-push on the PR.

**Approach:**

- Sweep for any test that touched `_resolve_user_scope_target_adapter`, `DEFAULT_USER_SCOPE_ADAPTER`, the four user-scope packs' `pack.toml`, the four repo-only packs' contract version, the install argparse setup, or the user-scope-only `--adapter` binding. Update each to match v0.7 expectations.
- Run the full local gate suite. Resolve any drift.
- Commit; push; verify CI green.

**Done when:** all four local gates pass; CI on the open PR is green.

## Rollout

This spec ships behind no flag. The contract bump `v0.6 → v0.7` is the gate: any v0.7 pack at repo scope routes through the new per-IDE projection path; any pack at `< v0.7` continues through the legacy heuristic at step 5 (claude-code/kiro only). **Adopter-facing behaviour change:** post-merge, a Kiro or Codex adopter installing any of the eight shipped packs at repo scope lands the pack at their IDE's project-local skills directory; a Claude Code adopter sees `<repo>/.claude/skills/` instead of `<repo>/claude-plugins/<pack>/...` (visible on-disk diff). Catalogue maintainers scripting `agentbundle install --scope repo` for publishing add `--emit-install-routes` to their script — one-line fix; the migration guide names this explicitly.

**Reversible.** If a regression surfaces post-merge, revert the implementation PR (the contract bump reverts to v0.6; the eight packs' `pack.toml` reverts; the resolver renames back; the path-jail widening reverts). No data migration; no persistent state change beyond `state.adapter` (which v0.6 already wrote for user scope, this spec extends to repo scope; `state.adapter`'s field shape is unchanged).

## Risks

- **Test surface across two test roots is large.** ~7 new test modules across `packages/agentbundle/tests/unit/`, `packages/agentbundle/tests/integration/`, and `packages/agentbundle/agentbundle/build/tests/`. Risk: a regression in one root masks a regression in the other. **Mitigation:** the cross-cutting tests section names the end-to-end smoke as the integration belt; T11's final sweep includes both roots.
- **Migration's in-band detection has three triggers with subtle precedence.** Risk: a misordered check fires the wrong stderr line. **Mitigation:** AC24 pins the precedence (b)→(a)→(c) explicitly; T7's tests parametrise each combination including the (b)+(c) overlap.
- **The orphan-projection refusal (AC22) and `--force` override (AC23) interact with the existing Tier-2 squatter detection.** Risk: an orphan file from a crashed install gets classified as Tier-2 squatter and gets a `.upstream.<ext>` companion. **Mitigation:** AC22's refusal fires *before* `_classify_for_install` runs; the regression test in T7's `test_install_orphan_force` is the falsifier.
- **The probe-asymmetry (`test_repo_scope_does_not_probe_dot_claude`) is load-bearing but counterintuitive.** Risk: a future contributor reads the code, thinks "this is missing the repo-scope probe", and adds it — silently breaking the no-fall-through guarantee. **Mitigation:** the unit test is named for the asymmetry; the resolver docstring at `install.py:1393` names the asymmetry as intentional and points at RFC-0012 § *Alternatives considered* #4.
- **Eight packs bumping to v0.7 in one PR is a lot of `pack.toml` edits.** Risk: a typo in one of the eight breaks `agentbundle validate` for that pack. **Mitigation:** T5's per-pack test loads each `pack.toml` via `tomllib.loads` and asserts the bumped version; `make build-self FORCE=1` is the second belt.
- **`--emit-install-routes` is a flag without users.** RFC-0012 § *Alternatives considered* #6 names this as the cost-side rationale; the flag carries a `DeprecationWarning` from day one and is targeted for removal in the next minor. Not a risk introduced by the implementation — already a documented cost.

## Changelog

- 2026-05-26 — Initial Drafting. Plan follows from RFC-0012 (Accepted same day) and mirrors `pack-allowed-adapters/plan.md` in shape per the RFC's *Follow-on artifacts* bullet. Eleven tasks (T1-T11) ordered by dependency: contract bump → resolver + safety → CLI → constant rename → packs → projection dispatch → messages + detection → integration → docs → sibling-spec amendments → gates.
- 2026-05-26 (round-1) — Pre-EXECUTE adversarial review pass. **T1** swaps the brittle snapshot-comparison test for property-based invariants (no checked-in v0.6 fixture file required). **T2** pins the rename's live grep predicate and corrects the call-site list (adds `install.py:1234-1235`; drops `upgrade.py:240` which is `_render_for_user_scope`, a different function); adds the step-count grep across `packages/` and `docs/` per spec AC8. **T2 Done when** strengthened — the unit-test layer must actually exercise `_resolve_target_adapter(scope="repo", ...)` directly, not via T6's stub-driven dispatch tests. **T3** names the actual offender for the `--adapter is bound` flip (`tests/integration/test_install_user_scope_allowed_adapters.py:196`). **T4** corrects the monkeypatch flip — the test sites are `monkeypatch.setattr` string-target updates at `:138-139` and `:154-155`, not import statements. **T7** in-band detection cases re-scoped per-pack: (b)/(a)/(c) trigger logic clarified; (b)+(c) precedence test reframed as per-pack-A/per-pack-B; falsifier monkeypatch pins `N ≥ 2`. **T9** erratum scope widens to record all three step-count drifts. Closes 6 Blockers + 11 Concerns from the round-1 review.
- 2026-05-26 (round-4) — Fourth pre-EXECUTE adversarial review pass (2 Concerns + 1 Nit addressed). **T3** handler-level mutex checks consult `requested_scope` (resolved scope), not `args.scope` (raw CLI flag), matching the existing-codebase precedent at `install.py:197` — without this, a pack with `[scope] default-scope = "user"` and no `--scope` flag bypasses the binding silently. **T3** placement of the mutex pinned to *after* Step 2 (`scope_mod.resolve()` at `install.py:182`); placement is load-bearing for AC30b case 1's tier-1-before-tier-2 ordering. **T3** test list gains an explicit `default-scope = "user"` + no `--scope` flag case to pin the resolved-scope semantics (AC30b case 1 alone would mask the `args.scope`-vs-`requested_scope` defect because it supplies `--scope` explicitly). Closes 2 Concerns + 1 Nit from round-4.
- 2026-05-26 (round-3) — Third pre-EXECUTE adversarial review pass. **T2** step-count grep narrowed to match spec AC8's predicate (`(four|five|six)[- ]step.*(lookup|resolver|resolution)`); references AC8's allow-list dispositions instead of broad-grep-and-decide. **T7** route-list construction uses the per-pack-emitting subset of `DEFAULT_RECIPES` (today: `per-pack-claude-plugin`, `per-pack-apm-package`; `marketplace` excluded — doesn't produce a per-pack directory) and the `_format_route_list` helper from AC20, instead of joining `DEFAULT_RECIPES` with " and " (which produced ungrammatical N=3 output). Closes 2 Concerns from round-3.
- 2026-05-26 (round-2) — Second pre-EXECUTE adversarial review pass. **T3** test-flip description corrected — there is one test method (`test_adapter_at_repo_scope_refused` at `:186-196`) with one assertion; the method either deletes or rewrites its single assertion (no phantom `:198` companion site). **T7** trigger (b) fixture description rewritten — no CLI-version field is read; the pre-RFC-0012 signal is on-disk dist-tree shape + entry on the per-IDE install code path. **T8** trigger (b)/(a) integration fixtures match the same shape. **T8** cross-adapter refusal cite corrected from `upgrade.py:318-326` to `:365-377` (the actual block at `if old_adapter_recorded != new_target_adapter:`). Closes 3 Blockers + 5 Concerns + 2 Nits from the round-2 review.
