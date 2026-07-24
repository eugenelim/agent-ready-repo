# Plan: Source Conflict Install Guard

- **Spec:** [`spec.md`](spec.md)
- **Status:** Drafting <!-- Drafting | Executing | Done -->

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document is allowed to change as you learn. When it changes substantially
> (a different approach, not just a re-ordering), note why in the changelog
> at the bottom.

## Approach

Single file change to `install.py`, with a new private helper `_check_source_conflict` that encapsulates the guard logic and makes it unit-testable without exercising the full install flow. The helper takes `pack_name`, `scope`, `state`, and `source_uri`; it does NOT take `force` (the no-bypass property is structural). The helper reads `rows_for_pack`, compares canonical sources using `canonicalize_source` from `agentbundle.config`, and returns a non-empty error string on conflict or `None` on allow.

The guard is called **after Step 3b** (dependency gate) and **before Step 3c** (AC24 `--force` orphan cleanup) — this is the earliest point where `pack_name`, `catalogue_uri`, `requested_scope`, `repo_state`, and `user_state` are all in scope and no mutation has yet occurred. It checks only the **requested scope's** state (not both scopes), so cross-scope conflicts are naturally not blocked (AC6 compliance without special-casing).

All existing tests continue to pass unchanged: they install packs from the same fixture catalogue, so `canonicalize_source(existing.source)` and `canonicalize_source(catalogue_uri)` both canonicalize to the same path and the guard allows the install.

## Constraints

- RFC-0072 D3: `--force` must not bypass source mismatch. The helper has no `force` parameter — there is no conditional around the call site.
- spec/packstate-source-provenance: `canonicalize_source` must be available in `agentbundle.config` before this spec is implemented. This spec depends on that one.
- RFC-0031 Principle 3: stdlib-only, no new runtime dependency.
- Security: never write credentials, bearer tokens, or URL user-info into error messages; `canonicalize_source` rejects these before storage.

## Construction tests

**Unit tests:** `_check_source_conflict` is a pure function that returns `str | None`. It is directly unit-testable without mocking the full install flow. The table-driven AC2/AC3/AC4/AC8 tests call it directly.

**Integration tests:** The three integration tests exercise the full `install.run()` path — multi-adapter same-source (AC3), second-source refusal with and without `--force` (AC1/AC2/AC4), legacy-row block (AC7/AC8), and cross-scope `--force` dual-scope path (AC6).

**Manual verification:** none beyond the integration tests above.

## Design

### Design decisions

- `_check_source_conflict` is a module-level private helper in `install.py` rather than a method on `State` or a function in `config.py`. It is install-specific logic (not a general state operation), has no place in the data model, and keeping it in `install.py` collocates the guard with the flow it protects. The helper takes `State` and `source_uri` as plain arguments, making it pure and testable without constructing a full args namespace.
- The guard is placed before Step 3c rather than after Step 5. This is the correct AC1 insert point: Step 3c's `_classify_pre_rfc0012_state` under `--force` can perform orphan unlink and state rewrite, which are mutations. The pre-Step-3c location is the earliest point where all required variables are in scope and none have been mutated.
- The guard checks `requested_scope` only (not both scopes). Dual-scope `--force`-and-other-already builds `plans = [repo_plan(already_installed=True), user_plan]`, but the "other scope" recap is a cross-scope relationship — AC6 explicitly says cross-scope different-source is not blocked. Checking only `requested_scope` implements this without special-casing.
- The helper returns a `str | None` error message rather than raising an exception. This matches the existing pattern in `install.py` where errors are returned as exit codes and printed to stderr, not raised.
- `None`-vs-`None` canonical comparison is treated as "cannot prove equal" → refuse. The alternative (allow both-unknown) is rejected: two unknown sources may be different, and RFC-0072 D3's conservative bridging posture requires proof of equality, not absence of proof of inequality.
- The error message displays `canonicalize_source(source_uri)` for the incoming source. When this is `None` (incoming source is unknown), the message says "unknown/legacy source" to avoid the confusing literal `None`. Same for existing row display.
- The error message names both recovery paths: upgrade from a concrete source (which migrates a legacy row's provenance) and uninstall-all-then-reinstall (the full-reset path). This matches RFC-0072 D3's documented migration path.

### Data & schema

No schema changes. The guard is read-only against the state loaded at pre-flight. Traces to: AC1, AC9.

### Interfaces & contracts

`_check_source_conflict(pack_name: str, scope: str, state: "State | None", source_uri: str) -> str | None` — private to `install.py`. `source_uri` is the logical source URI for comparison (derived at the call site per AC11; may be `catalogue_uri` or `args._source_uri`). Accepts `None` for `state` (unresolvable user scope); returns `None` immediately in that case. Returns `None` when the install is allowed; returns a non-empty error string (ready to print to stderr) when refused. Traces to: AC2–AC8, AC11.

Call site in `run()` (after Step 3b, before Step 3c):

```python
# ── Source conflict guard (RFC-0072 D3) ──────────────────────────────────────
# Fires before all mutations including Step-3c --force cleanup.
# --force does NOT bypass; no conditional on `force` here.
# Derive the logical source URI: profile sub-installs set _source_uri to the
# logical catalogue URI; regular installs use catalogue_uri directly (AC11).
_guard_source_uri = getattr(args, "_source_uri", None) or catalogue_uri
_src_conflict = _check_source_conflict(
    pack_name,
    requested_scope,
    repo_state if requested_scope == "repo" else user_state,
    _guard_source_uri,
)
if _src_conflict is not None:
    print(f"install: {_src_conflict}", file=sys.stderr)
    return 1
```

### Behavior & rules

`_check_source_conflict` logic:

1. If `state` is `None` → return `None` (guard is a no-op; install will fail later at user-root resolution).
2. `existing_rows = state.rows_for_pack(pack_name)` — get all adapter rows for the pack at this scope.
3. If `existing_rows` is empty → return `None` (no conflict possible; first install for this pack at this scope).
4. `incoming_canonical = canonicalize_source(source_uri)` — import from `agentbundle.config` inside the function.
5. For each `(adapter, ps)` in `sorted(existing_rows.items())`:
   a. `existing_canonical = canonicalize_source(ps.source)`.
   b. Conflict condition: `incoming_canonical is None or existing_canonical is None or existing_canonical != incoming_canonical`.
   c. If conflict: collect `(adapter, existing_canonical)` into a conflict list.
6. If no conflicts → return `None` (all existing rows have same non-`None` canonical source as incoming → allowed).
7. Build and return the error message (see AC5 shape).

Error message shape (AC5):

```
{pack_name}: source conflict at {scope} scope — incoming source {incoming_display!r} differs from existing installation(s):
  {adapter1}: {existing_display1}
  {adapter2}: {existing_display2}
  ...
--force does not override source conflicts.
Recovery: run 'agentbundle upgrade --pack {pack_name}' from a concrete source to migrate a legacy row,
  or uninstall all existing adapters first ('agentbundle uninstall --pack {pack_name}') then reinstall.
```

Where `incoming_display` is `canonicalize_source(source_uri)` or `"unknown/legacy source"` if `None`; `existing_display` is `canonicalize_source(ps.source)` or `"unknown/legacy source"` if `None`.

Traces to: AC2, AC4, AC5, AC8.

### Failure, edge cases & resilience

- **`user_state` is `None`:** The guard returns `None` immediately (rule 1). The install will fail later at the user-root resolution step; the guard does not need to surface this.
- **Empty `rows_for_pack` return:** Covered in rule 3 — fast-path return `None`. No exception path.
- **Dual-scope `--force` path:** The guard fires using `requested_scope` → checks the NEW write scope only. The recap scope (other-already, cross-scope) is never checked. AC6 is satisfied without any special-casing of `plan.already_installed`.
- **Profile-install path:** `_run_profile` returns at line ~114 before `catalogue_uri` and `requested_scope` are set. Each sub-install within the profile hits the guard independently when it calls `run()` recursively with its own `requested_scope`.
- **`canonicalize_source` import:** Inside the function body, lazy-loaded. Consistent with `install.py`'s lazy-import convention. No circular import risk: `config.py` is already imported by `install.py`.

## Tasks

### T1: Implement `_check_source_conflict` and wire the guard into `install.run()`

**Depends on:** spec/packstate-source-provenance (for `canonicalize_source` in `agentbundle.config`)

**Touches:** `packages/agentbundle/agentbundle/commands/install.py`

**Tests (TDD — all tests below require red stubs materialized at EXECUTE PLAN):**

- `test_source_conflict_no_existing_rows_allowed`: `state` with no rows for `pack_name` → returns `None`. Verifies fast-path resilience (empty scope).
- `test_source_conflict_same_canonical_source_allowed`: state has `(pack, claude-code)` with `source = "/tmp/catalogue"` (concrete); incoming `source_uri = "/tmp/catalogue"` → returns `None`. Verifies AC3.
- `test_source_conflict_differing_representations_allowed`: state has `(pack, claude-code)` with `source` set to a path with a `..` segment (e.g., `"/tmp/x/../catalogue"` which resolves to `"/tmp/catalogue"`); incoming `source_uri = "/tmp/catalogue"`; assert returns `None` (only `canonicalize_source`'s `Path.resolve()` normalizes `..`; a bare string compare would refuse). Verifies AC3, AC7.
- `test_source_conflict_different_concrete_sources_refused`: state has `(pack, claude-code)` with source canonicalizing to `/tmp/catA`; incoming canonicalizes to `/tmp/catB` → returns non-`None` error string. Verifies AC2.
- `test_source_conflict_incoming_none_existing_concrete_refused`: incoming `source_uri` canonicalizes to `None` (e.g., `"agent-ready-repo"`); existing row has concrete source → returns non-`None`. Verifies AC8.
- `test_source_conflict_existing_none_incoming_concrete_refused`: state has `(pack, claude-code)` with `source = None`; incoming is concrete → returns non-`None`. Verifies AC8.
- `test_source_conflict_both_none_refused`: state has `(pack, claude-code)` with `source = "agent-ready-repo"` (canonicalizes to `None`); incoming `source_uri` also canonicalizes to `None` → returns non-`None`. Verifies AC8.
- `test_source_conflict_legacy_literal_refused`: state has `(pack, claude-code)` with `source = "agent-ready-repo"`; incoming is concrete → returns non-`None`. Verifies AC7, AC8.
- `test_source_conflict_multiple_adapters_all_same_source_allowed`: state has `(pack, claude-code)` and `(pack, kiro)`, both with same concrete canonical source as incoming → returns `None`. Verifies AC3.
- `test_source_conflict_state_none_returns_none`: pass `state=None`; assert returns `None` regardless of `source_uri`. Verifies resilience edge case.
- `test_source_conflict_error_message_contains_pack_name`: trigger a conflict; assert returned string contains the pack name. Verifies AC5(a).
- `test_source_conflict_error_message_contains_scope`: trigger a conflict; assert returned string contains the scope. Verifies AC5(b).
- `test_source_conflict_error_message_contains_incoming_source`: trigger a conflict with concrete incoming source; assert returned string contains the incoming canonical source string. Verifies AC5(c).
- `test_source_conflict_error_message_contains_existing_adapter_and_source`: trigger a conflict; assert returned string contains the existing adapter name and the existing canonical source display. Verifies AC5(d).
- `test_source_conflict_error_message_contains_upgrade_recovery`: trigger a conflict; assert returned string contains "upgrade". Verifies AC5(e).
- `test_source_conflict_error_message_contains_uninstall_recovery`: trigger a conflict; assert returned string contains "uninstall all existing adapters". Verifies AC5(e).
- `test_source_conflict_error_message_force_no_bypass_note`: trigger a conflict; assert returned string contains "--force does not". Verifies AC4, AC5.
- `test_source_conflict_cross_scope_not_blocked` (unit): call the helper with repo_state containing a pack row (source A) while passing user_state (empty) as `state`; assert returns `None`. Verifies AC6 (guard only inspects the passed state, never the other scope's state).
- `test_source_conflict_force_flag_does_not_bypass` (integration): install `core` for `claude-code` from catalogue A; attempt install of `core` for `kiro` from catalogue B with `force=True`; assert exit code non-zero AND `kiro` adapter row absent from state AND no `kiro` projection files on disk. Verifies AC4, AC1.
- `test_source_conflict_refusal_before_any_file_written` (integration): install `core` for `claude-code` from catalogue A; attempt install `core` for `kiro` from catalogue B; assert exit code non-zero, `kiro` adapter row absent from state, and `kiro` projection directory absent or unchanged. Verifies AC1, AC2.
- `test_source_conflict_guard_before_step3c_orphan_cleanup` (integration): seed pre-RFC-0012 legacy state for `(core, claude-code)` from source A at repo scope, with the following conjunction that activates the orphan-cleanup branch: (1) `requested_scope == "repo"`; (2) incoming adapter (`kiro`) has no state row; (3) place orphan files on disk under the kiro `allowed_prefixes.repo` path detected by `scan_for_pack_artifacts`; (4) orphan files NOT in the current projection relpaths; (5) orphan files NOT in the `claude-code` row's `files` map. Attempt `install --adapter kiro` from source B (different canonical) with `force=True` AND `yes=True` (so that, absent the guard, Step 3c would confirm and delete the orphan files). Assert exit code non-zero and the orphan files still exist on disk. This test fails if the guard is moved after Step 3c (orphans would be deleted before the guard fires). Verifies AC1.
- `test_source_conflict_same_adapter_different_source_refused` (integration): seed state with `(core, claude-code)` from source A; attempt `install --adapter claude-code` from source B; assert exit code non-zero; assert error message contains "source conflict" and does NOT contain "use 'upgrade' to change version". Verifies AC2 and the Assumption that the guard precedes Step 4a.
- `test_source_conflict_multi_adapter_same_source_allowed` (integration): install `core` for `claude-code`; install `core` for `kiro` from same catalogue; assert both succeed and both rows present in state. Verifies AC3.
- `test_source_conflict_legacy_row_blocks_second_adapter` (integration): seed state with `(core, claude-code)` row with `source = "agent-ready-repo"`; attempt install of `core` for `kiro` from a concrete catalogue; assert exit code non-zero and error message contains "uninstall all existing adapters". Verifies AC7, AC8.
- `test_source_conflict_cross_scope_force_dual_scope_succeeds` (integration): install `core` at repo scope from catalogue A; run `install --scope user --force --pack core` from catalogue B; assert user-scope install succeeds; assert repo row's recorded source is unchanged (still the canonical of catalogue A). Verifies AC6.
- `test_source_conflict_profile_source_uri_integration` (integration): construct an `args` namespace where `args._source_uri` is a logical local-path URI whose canonical matches an existing row's stored source, while `args.catalogue` points to a different local directory (simulating the profile orchestrator). Drive `install.run(args)` for a pack that already has a row at the target scope. Assert the install is allowed (no source conflict — `_source_uri` is used). Drive a second invocation with `args._source_uri = None` (attribute present but `None`, triggering the `or catalogue_uri` fallback to the different dir). Assert the install is refused (the fallback canonical differs). This test fails if the call site uses only `catalogue_uri` or only `getattr(args, "_source_uri", catalogue_uri)` (which would not handle the `_source_uri = None` case). Verifies AC11.

**Approach:**

1. Define `_check_source_conflict` as a module-level private function in `install.py`, placed near the other module-level helpers (below `_ScopePlan` and above `run()`):

   ```python
   def _check_source_conflict(
       pack_name: str, scope: str, state: "State | None", source_uri: str
   ) -> str | None:
       """Return an error message string if a source conflict is detected, else None.

       Implements RFC-0072 D3: refuse an install at ``scope`` when existing
       (pack, adapter) rows at that scope have a different canonical source from
       ``source_uri``. ``--force`` is NOT a parameter — callers must not gate
       this check on ``force``. ``source_uri`` is the logical catalogue URI
       (derived at the call site via ``getattr(args, "_source_uri", None) or
       catalogue_uri``); do not pass ``catalogue_uri`` directly.
       """
       if state is None:
           return None
       existing_rows = state.rows_for_pack(pack_name)
       if not existing_rows:
           return None
       from agentbundle.config import canonicalize_source
       incoming_canonical = canonicalize_source(source_uri)
       conflicts: list[tuple[str, str]] = []
       for adapter, ps in sorted(existing_rows.items()):
           existing_canonical = canonicalize_source(ps.source)
           if (
               incoming_canonical is None
               or existing_canonical is None
               or existing_canonical != incoming_canonical
           ):
               display = existing_canonical if existing_canonical is not None else "unknown/legacy source"
               conflicts.append((adapter, display))
       if not conflicts:
           return None
       incoming_display = incoming_canonical if incoming_canonical is not None else "unknown/legacy source"
       lines = [
           f"{pack_name}: source conflict at {scope} scope — "
           f"incoming source {incoming_display!r} differs from existing installation(s):",
       ]
       for adapter, display in conflicts:
           lines.append(f"  {adapter}: {display!r}")
       lines.append("--force does not override source conflicts.")
       lines.append(
           f"Recovery: run 'agentbundle upgrade --pack {pack_name}' from a concrete source "
           f"to migrate a legacy row, or uninstall all existing adapters first "
           f"('agentbundle uninstall --pack {pack_name}') then reinstall."
       )
       return "\n".join(lines)
   ```

2. Wire the call into `run()` after Step 3b and before Step 3c:

   ```python
   # ── Source conflict guard (RFC-0072 D3) ──────────────────────────────────────
   # Must fire before Step-3c --force cleanup (the earliest mutation point).
   # --force does NOT bypass; this call has no conditional on `force`.
   # Derive the logical source URI (AC11): profile sub-installs set
   # `args._source_uri` to the logical catalogue URI; `catalogue_uri` is the
   # resolved temp dir in that case. `or catalogue_uri` also handles the
   # `_source_uri = None` case (attribute present but None).
   _guard_source_uri = getattr(args, "_source_uri", None) or catalogue_uri
   _src_conflict = _check_source_conflict(
       pack_name,
       requested_scope,
       repo_state if requested_scope == "repo" else user_state,
       _guard_source_uri,
   )
   if _src_conflict is not None:
       print(f"install: {_src_conflict}", file=sys.stderr)
       return 1
   ```

3. No other files change. `config.py` is not touched (the guard is install-specific).

**Done when:** all unit tests above pass; integration tests pass; `grep -n "_check_source_conflict" packages/agentbundle/agentbundle/commands/install.py` confirms the function is defined and called; body-scoped check `sed -n '/^def _check_source_conflict/,/^def /p' packages/agentbundle/agentbundle/commands/install.py | grep -E '\bforce\b'` shows zero hits — `force` is not referenced inside the guard function (AC4); body-scoped check `sed -n '/^def _check_source_conflict/,/^def /p' packages/agentbundle/agentbundle/commands/install.py | grep -E '\.lower\(\)|\.strip\(|\.rstrip'` shows zero inline normalizations (AC7); `grep -n 'getattr(args, "_source_uri"' packages/agentbundle/agentbundle/commands/install.py` confirms the `getattr` derivation is present at the call site (AC11).

---

### T2: Run existing test suite; confirm no regression

**Depends on:** T1

**Touches:** none (read-only verification)

**Tests:**

- Run full agentbundle test suite: `python -m pytest packages/agentbundle/ -x`.
- Goal-based: `git diff pyproject.toml` shows no new dependency entries. Verifies AC9.

**Approach:**

- Run the test suite.
- If failures arise: distinguish pre-existing failures from regressions. Pre-existing failures are documented in the backlog; any new failure caused by this change is a blocker.
- Existing tests install packs from the same catalogue fixture, so `canonicalize_source(existing.source)` and `canonicalize_source(catalogue_uri)` resolve to the same path — the guard allows the install and existing tests are unaffected.

**Done when:** pytest exits 0 (or all failures are pre-existing and documented) and AC9 goal-based check passes. Verifies AC10.

## Rollout

Pure logic change — no schema change, no new dependency, no infrastructure. Backward-compatible for existing state files (the guard reads `source` via `canonicalize_source`, which handles all existing literal values). Ships as part of the broader ini-004 agentbundle release. `spec/packstate-source-provenance` must ship first or simultaneously.

## Risks

- **Existing multi-adapter installs with different sources:** Once this guard lands, any state file that already has rows with different sources will not be touched (the guard only fires on new installs, not on existing state). Future installs of a new adapter will be blocked until the user upgrades or uninstalls+reinstalls. This is the intended behavior per RFC-0072 D3.
- **Legacy rows blocking all second-adapter installs:** Existing repos that installed a pack before `spec/packstate-source-provenance` landed will have `source = "agent-ready-repo"` rows. The guard will refuse any second-adapter install until the user runs an explicit upgrade (which migrates the source) or uninstalls and reinstalls. The error message names both recovery paths. Mitigation: `spec/packstate-source-provenance` should ship before or simultaneously with this spec.
- **`canonicalize_source` not yet available:** This spec depends on `spec/packstate-source-provenance` implementing `canonicalize_source`. If that spec has not shipped, this spec cannot be implemented. The dependency is declared in the header.
- **Profile-install sub-install interactions:** If a profile installs the same pack twice from different profile entries (unusual, possibly malformed profile), the second sub-install will hit the guard. This is correct behavior — the first sub-install wrote a source, and the second proposes a different one. The error will name the recovery step.
- **Profile-path logical-URI vs. resolved-temp-dir:** AC11 closes this risk when the profile orchestrator sets `args._source_uri` to the logical URI; the guard uses `getattr(args, "_source_uri", None) or catalogue_uri` and therefore compares the logical URI against the stored canonical. The residual risk is when `args._source_uri` is absent (the orchestrator does not set it) — in that case the guard falls back to `catalogue_uri`, which for a remote profile install may be a temp-dir canonical that differs from the stored logical-URI canonical. This residual requires `spec/packstate-source-provenance` to set `_source_uri` in the profile orchestrator path (AC14b). Mitigation: `spec/packstate-source-provenance` must ship its AC14b fix before or simultaneously with this spec. The AC11 integration test (`test_source_conflict_profile_source_uri_integration`) covers the `_source_uri` present and `_source_uri = None` cases; the absent-attribute case is deferred to that spec. Tracked in Assumptions.

## Changelog

- 2026-07-24: initial plan
- 2026-07-24: second draft — addressed adversarial review findings: moved guard to before Step 3c (Blocker 2, AC1 accuracy); narrowed guard to check requested_scope only (Blocker 1, AC6); added `None` state handling; added differing-representation test (Concern 3, AC7); added incoming+existing source assertions in error-message tests (Concern 4, AC5); extended force-bypass test to check mutation absence (Concern 5); added upgrade recovery path to error message and AC5 (Concern 6); added cross-scope dual-scope integration test (Concern 7); removed dead call-site import from snippet (Nit 8); added inline-normalization grep to Done-when (Nit 9)
- 2026-07-24: third draft — addressed second adversarial review: added orphan-survival integration test (Blocker 1, AC1); corrected Assumption about same-adapter reinstalls (Concern 2 — guard precedes Step 4a, same-adapter different-source is refused by guard); added same-adapter different-source integration test; changed differing-representation test to use `..` segment (stronger canonicalize_source discriminator, Nit 4); relabeled empty-rows test as resilience edge case (Nit 5); added repo-source-preservation assertion to cross-scope integration test (Nit 6); documented profile-path dependency on spec/packstate-source-provenance AC14b (Concern 3)
- 2026-07-24: fourth draft — addressed third adversarial review: added `yes=True` to orphan-survival test and enumerated five conjunction preconditions for the orphan branch to activate (Blocker 1); added profile AC14b false-conflict scenario to Risks section with deferred-coverage note (Concern 3)
- 2026-07-24: fifth draft — addressed fourth adversarial review: added AC11 + `getattr(args, "_source_uri", catalogue_uri)` at call site for profile sub-install logical-URI alignment (Blocker 1); fixed body-scoped grep pattern for AC4/AC7 Done-when verification (Concerns 2 and 3); added AC11 unit test pinning the _source_uri contract
- 2026-07-24: sixth draft — addressed fifth adversarial review: AC11 call-site derivation changed to `getattr(args, "_source_uri", None) or catalogue_uri` to handle `_source_uri = None` case (Concern 3); replaced AC11 unit test with integration test that exercises the `getattr` call site (Blocker 1); added `getattr` literal grep to Done-when (Blocker 1/Nit 6); updated AC2/AC3/AC8 in spec to reference `guard_source_uri` (per AC11) rather than raw `catalogue_uri` (Concern 2); renamed `_check_source_conflict` parameter from `catalogue_uri` to `source_uri` throughout (Nit 5); stated write-path/guard symmetry as identical `getattr(args, "_source_uri", None) or catalogue_uri` expression (Concern 4)
- 2026-07-24: seventh draft — addressed sixth adversarial review: fixed dangling AC11 test citation (Blocker 1 — `test_source_conflict_profile_source_uri_used_when_present` → `test_source_conflict_profile_source_uri_integration`); replaced remaining `catalogue_uri` references in Design-decisions and Risks sections with `source_uri` / `guard_source_uri`; updated profile-path Risk section to reflect that AC11 closes the primary risk and scope the residual to the absent-`_source_uri` case
- 2026-07-24: eighth draft — addressed seventh adversarial review: fixed spec Assumption line 86 from `getattr(args, "_source_uri", catalogue_uri)` to `getattr(args, "_source_uri", None) or catalogue_uri` (Blocker 1); renamed `catalogue_uri` to `source_uri` in remaining unit-test descriptions (Nit 2)
