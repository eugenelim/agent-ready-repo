# Spec: Source Conflict Install Guard

- **Status:** Draft <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** RFC-0072 (D3), spec/packstate-source-provenance (canonicalize_source)
- **Brief:** none
- **Discovery:** none
- **Contract:** none
- **Shape:** service

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

`agentbundle install` currently allows the same pack name to be installed at one scope from multiple canonical sources across different adapter rows. When a user runs `agentbundle install my-pack --adapter kiro` after `my-pack` is already installed at repo scope via `claude-code` from a different source, the state file records two rows with different sources for the same pack. This creates unresolvable provenance ambiguity: upgrade routing must pick one source to fetch from and cannot know which is authoritative; `list-installed` update-status reporting cannot determine which catalogue to check. Without ADR-0021's `@catalogue/pack` resolution implemented, a mixed-source state file has no recovery path short of uninstall or migration via upgrade.

This spec adds a pre-install scan that, before any mutation (including Step-3c `--force` orphan cleanup), reads all existing `(pack_name, adapter)` rows at the **target scope only**, canonicalizes each row's source using `canonicalize_source` (defined by `spec/packstate-source-provenance`), and refuses the install when any existing row's canonical source differs from the incoming canonical source. `--force` does not bypass this refusal (RFC-0072 D3 — explicit decision). Legacy rows with unknown provenance (`source = None` or `source = "agent-ready-repo"`) cannot be proven equal to any incoming canonical source and therefore also trigger refusal. Same-scope, same-canonical-source, multi-adapter installs remain allowed. Cross-scope conflicts (repo vs. user) are not blocked here; status reporting may warn there separately.

## Boundaries

### Always do

- Invoke `canonicalize_source` (from `agentbundle.config`, defined by `spec/packstate-source-provenance`) on both the incoming `catalogue_uri` and each existing row's `PackState.source` before comparing them — no inline string normalization, no ad-hoc case folding.
- Fire the refusal before **all** install mutations: before Step-3c's `--force` orphan cleanup (`_classify_pre_rfc0012_state`), before any projection write (`safety.write_jailed`), before hook-wiring merge, before state write (`persist_state_locked`), before seed delivery, before marker append (`_append_install_marker`), and before layout-section append (`_append_layout_section`).
- Check only the **requested scope's** state — not both scopes. In a dual-scope `--force`-and-other-already install, the "other scope" recap is not a new write and represents a cross-scope relationship that AC6 explicitly does not block.
- Include in the error message: the pack name, the target scope, the canonicalized incoming source (or "unknown/legacy source" if `canonicalize_source` returns `None`), the existing adapter name(s), the existing canonical source(s), and the recovery paths (upgrade from a concrete source migrates a legacy row; uninstall all existing adapters is the full-reset path).
- Treat `canonicalize_source` returning `None` for either the incoming or an existing row as "cannot prove equal" — a `None`-vs-`None` comparison is NOT treated as equal.
- Use Python 3.11 stdlib only — no new runtime dependencies.
- Redact any credentials or bearer tokens from source strings in all error messages (this is handled by `canonicalize_source` rejecting credentials before they reach storage or display; display the canonical form, which has credentials removed).

### Ask first

- Any change to the cross-scope (repo vs. user) conflict rule — the current spec deliberately does not block cross-scope different-source installs.
- Any softening of the `--force`-no-bypass rule — this is a load-bearing RFC-0072 D3 explicit decision.
- Any automatic migration of legacy rows at guard-check time — the guard must not write or mutate state.

### Never do

- Allow `--force` to bypass a source mismatch. `--force` bypasses the path-level footprint conflict (Tier-2 safety); it does not bypass the source-provenance conflict. These are separate gates.
- Fire the guard during upgrade — the upgrade path is the sanctioned migration mechanism for legacy rows; blocking it here would trap users with no recovery.
- Write credentials, bearer tokens, `Authorization` header values, or URL user-info into any error message or log line.
- Mutate, migrate, or write state during the conflict check — the check is read-only against the pre-flight state.
- Introduce a new runtime dependency.

## Testing Strategy

- **Unit — refusal conditions (table-driven):** parametrize over (existing_source, incoming_catalogue_uri, should_refuse) to pin the four refusal/allow cases: (a) same concrete source → allow; (b) different concrete sources → refuse; (c) incoming concrete, existing None/legacy → refuse; (d) incoming None, existing concrete → refuse. Each case constructs a minimal `State` with one pre-existing row and calls the helper directly.
- **Unit — same-source with differing representations:** construct a test where the existing row's source and `catalogue_uri` represent the same path in different forms (e.g., `"/tmp/x/"` trailing slash vs `"/tmp/x"` without); assert the helper returns `None` (allow). This test fails unless `canonicalize_source` is actually engaged — bare string comparison would refuse. Verifies AC7.
- **Unit — `--force` no-bypass:** the helper is called without `force` as a parameter (it does not accept `force`) — the no-bypass property is structural. A code-review check confirms no `force` gate surrounds the call in `run()`. Verifies AC4.
- **Unit — cross-scope not blocked:** install at `repo` scope; the guard is called only with repo_state; user_state with a conflicting source is NOT passed. Assert returns `None`. Verifies AC6.
- **Unit — error message content:** capture the return value from a refusing call; assert it contains the pack name, the target scope, the incoming display value, the existing adapter name, the existing canonical source, "upgrade" or "run 'upgrade'", and the substring "uninstall all existing adapters". Verifies AC5.
- **Integration — multi-adapter same-source allowed:** install `core` for `claude-code` and then install `core` for `kiro` from the same local catalogue path; assert both succeed and both adapter rows are present in state. Verifies AC3.
- **Integration — refusal fires before any mutation:** install `core` for `claude-code` from catalogue A; attempt to install `core` for `kiro` from catalogue B (different local path, canonicalizes differently); assert exit code non-zero; assert `kiro` adapter row is absent from state; assert no new files at the `kiro` projection path. Verifies AC1, AC2.
- **Integration — `--force` no-bypass with mutation check:** same setup as refusal test; add `--force` to the attempt; assert exit code still non-zero, `kiro` row absent from state, no `kiro` projection files. Verifies AC4, AC1.
- **Integration — guard fires before Step-3c orphan cleanup under `--force`:** seed pre-RFC-0012 legacy state for a pack (a shape that would trigger `_classify_pre_rfc0012_state` orphan-branch cleanup under `--force`); attempt a second-adapter install from a different source with `--force`; assert the orphan files that the cleanup would delete still exist after the refusing run. This test would fail if the guard were moved after Step 3c. Verifies AC1.
- **Integration — same-adapter different-source reinstall refused by guard (not Step 4a):** seed state with `(pack, claude-code)` from source A; attempt `install --adapter claude-code` from source B; assert exit code non-zero and error message contains "source conflict" (not "use 'upgrade' to change version"). Verifies AC2 and the correct behavior described in Assumptions.
- **Integration — legacy row blocks second-adapter install:** seed a state file with an existing `(core, claude-code)` row whose `source = "agent-ready-repo"` (legacy); attempt install of `core` for `kiro` from a concrete catalogue; assert exit code non-zero and error message contains "uninstall all existing adapters". Verifies AC7, AC8.
- **Integration — cross-scope `--force` dual-scope path succeeds and preserves repo row source:** install `core` at repo scope from source A; run `install --scope user --force --pack core` from source B; assert user-scope install succeeds (cross-scope different-source is not blocked) and the repo row's recorded source is unchanged. Verifies AC6.
- **Integration — profile `_source_uri` contract (AC11):** drive a full `install.run()` invocation with `args._source_uri` set to a logical URI whose canonical matches the existing row's stored source, while `args.catalogue` (and hence `catalogue_uri`) is set to an unrelated temp-dir path whose canonical differs. Assert the install is allowed (no source conflict). A second invocation with `_source_uri` absent (only `catalogue_uri` = temp-dir) should refuse. This test fails if the call site uses `catalogue_uri` instead of the `getattr(args, "_source_uri", None) or catalogue_uri` derivation. The Done-when grep for the `getattr` literal is the complementary structural check. Verifies AC11.
- **Goal-based check — no new runtime dependency:** `pyproject.toml` dependency list unchanged; the guard code imports no non-stdlib module beyond what `agentbundle.config` and `install.py` already import. Verifies AC9.

## Acceptance Criteria

- [ ] AC1: The source conflict guard fires before any install mutation, including Step-3c `--force` orphan cleanup. No projection file is written, no hook wiring is merged, no state row is written, no seed is delivered, no orphan is deleted, and no marker is appended when the guard refuses.
- [ ] AC2: For any existing `(pack_name, adapter)` row at the target scope where `canonicalize_source(existing.source) != canonicalize_source(guard_source_uri)` or either canonical value is `None`, the install is refused with a non-zero exit code. `guard_source_uri` is derived per AC11.
- [ ] AC3: When all existing rows for `pack_name` at the target scope have the same non-`None` canonical source as `canonicalize_source(guard_source_uri)`, the install proceeds normally (same-source multi-adapter is allowed). This holds even when the raw source strings differ in representation (e.g., `..`-containing path vs. its resolved form — canonicalization normalizes them). `guard_source_uri` is derived per AC11.
- [ ] AC4: Passing `--force` does not bypass the source-mismatch refusal. The guard helper does not accept a `force` parameter; the call site in `run()` has no conditional on `force` guarding the call. The error message explicitly states that `--force` does not override source conflicts.
- [ ] AC5: The refusal error message (to stderr) identifies: (a) the pack name, (b) the target scope, (c) the incoming canonical source or "unknown/legacy source" if `None`, (d) the existing adapter name(s) and their canonical sources, (e) the recovery paths: that running `upgrade` from a concrete source migrates a legacy row, and that uninstalling all existing adapters enables reinstalling from a different source.
- [ ] AC6: The guard checks only the requested scope's state. A pack installed at `repo` scope from source A does not trigger the guard when a separate install is made at `user` scope from source B. The dual-scope `--force`-and-other-already recap scope is not checked (it is a cross-scope relationship, not a new write).
- [ ] AC7: `canonicalize_source` from `agentbundle.config` is the sole comparison function — no inline string normalization in the guard. Verified by: Done-when includes `grep -n "\.lower\(\)\|\.strip\(\)\|\.rstrip" install.py` in the guard function showing zero hits; the unit test with differing path representations confirms canonicalize_source is engaged.
- [ ] AC8: A row with `source = None` or `source = "agent-ready-repo"` (both canonicalize to `None`) triggers refusal when `canonicalize_source(guard_source_uri)` (per AC11) has a non-`None` canonical source, and also triggers refusal when that canonical source is also `None` — "cannot prove equal" applies in both directions.
- [ ] AC9: No new runtime dependency is introduced. Verified by: `pyproject.toml` dependency list unchanged; the guard code imports no non-stdlib module beyond what `agentbundle.config` and `install.py` already import.
- [ ] AC10: All existing agentbundle tests pass after the change with no modifications to the tests themselves.
- [ ] AC11: The call site derives the guard's incoming source URI using `getattr(args, "_source_uri", None) or catalogue_uri`. This expression: (a) uses `args._source_uri` when it is set and non-`None` (the logical catalogue URI threaded by the profile orchestrator); (b) falls back to `catalogue_uri` when `_source_uri` is absent or `None` (regular installs). `spec/packstate-source-provenance` uses the identical derivation expression at its source write site, so guard and write path compare the same value. Verified by: Done-when grep for the literal `getattr(args, "_source_uri"` at the call site in `install.py`; integration test `test_source_conflict_profile_source_uri_integration` confirms the path by seeding the attribute.

## Assumptions

- Technical: `canonicalize_source(value: str | None) -> str | None` is defined in `agentbundle.config` by `spec/packstate-source-provenance` before this spec is implemented. This spec calls it but does not define it. (source: spec/packstate-source-provenance AC5)
- Technical: After `spec/packstate-source-provenance` lands, `PackState.source` is `str | None = None`. Legacy rows with `source = "agent-ready-repo"` still have that literal on read (AC3 of that spec); `canonicalize_source("agent-ready-repo")` returns `None`. (source: spec/packstate-source-provenance AC3, AC7)
- Technical: The guard is inserted after Step 3b (dependency gate, `validate_dependencies_required`) and before Step 3c (`_classify_pre_rfc0012_state` with its `--force` orphan cleanup). At this point: `pack_name`, `catalogue_uri`, `requested_scope`, `repo_state`, and `user_state` are all in scope; no mutation has yet occurred. (source: install.py code inspection — Step 3b ends ~line 369; Step 3c starts ~line 371)
- Technical: The guard uses `requested_scope` to select the target state (`repo_state` if `"repo"`, `user_state` if `"user"`). When `user_state` is `None` (unresolvable `$HOME`), the guard is a no-op (the install will fail at the user-root resolution step anyway). (source: install.py:332-349)
- Technical: `State.rows_for_pack(pack_name)` returns `{adapter: PackState}` for all existing adapter rows of `pack_name` at a scope. The guard sits before Step 4a (which routes same-adapter reinstalls to upgrade), so `rows_for_pack` may include a row with the same adapter as the incoming install. A same-scope, same-adapter, different-source reinstall is refused by the guard with the source-conflict message — not redirected to upgrade. This is correct per RFC-0072 D3 (which does not condition the refusal on "different adapter"); the guard's message names the upgrade path as a recovery option. (source: install.py Step 4a at ~line 506, guard insert point at ~line 370; RFC-0072 D3 rules table)
- Technical: The guard does NOT fire during the profile-install path (`_run_profile`). The profile orchestrator dispatches to `_run_profile` at line ~114, before `catalogue_uri` and `requested_scope` are set. Each sub-install within a profile hits the guard independently when the profile orchestrator calls `run()` recursively for each pack. (source: install.py:106-114)
- Technical: For profile sub-installs, the profile orchestrator sets `ns.catalogue = str(catalogue_dir)` (a resolved temp directory), making `catalogue_uri = str(catalogue_dir)` in the sub-install's `run()` invocation. The guard derives its incoming source URI as `getattr(args, "_source_uri", None) or catalogue_uri` — when `args._source_uri` is set to the logical catalogue URI by the profile orchestrator, the guard compares the same value the write path records; when `_source_uri` is absent or `None`, `catalogue_uri` is the fallback. This spec and `spec/packstate-source-provenance` must coordinate on the `_source_uri` attribute contract: packstate-source-provenance introduces `_source_uri` for the write path; this spec's AC11 reads it at the guard. (source: spec/packstate-source-provenance plan.md T3 — profile-install thread; install.py:4195)
- Technical: Python 3.11 stdlib-only runtime constraint. (source: `pyproject.toml`; RFC-0072)
- Process: RFC-0072 is Accepted; `spec/packstate-source-provenance` implements D3's prerequisite (`canonicalize_source`) and must ship first or simultaneously. This spec implements D3 itself. (source: RFC-0072 D3 and the spec queue)
