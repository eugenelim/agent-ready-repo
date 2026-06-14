# Plan: kiro-install-alias-parity

- **Spec:** [`spec.md`](spec.md)
- **Mode:** full

## Trio

- **Files I'll touch:** `packages/agentbundle/agentbundle/commands/install.py` (projection dispatch — done; explicit-allowlist hook-wiring merge gate; drop-warning enumerate-canonical/display-original; pre-flight `:639` → merging adapter; a single `_canonical_install_adapter` helper); `packages/agentbundle/agentbundle/build/scope_rails.py` (merge-family membership for the two attach-to-agent rails); `packages/agentbundle/agentbundle/commands/validate.py` (`_kiro_target_adapters` recognizes `kiro-cli`); the two fixtures' `pack.toml` (`allowed-adapters` → `kiro-cli`); the integration + unit tests listed below; `docs/product/changelog.md`.
- **What proves done:** the full `agentbundle` pytest suite is green, including (a) a new regression test that a `kiro`-alias user-scope install of a hook-wiring pack drops the wiring without crashing; (b) the retargeted `kiro-cli` suites pinning the legacy JSON + merge behavior with the rails still firing; (c) a new rail-fires-for-kiro-cli unit case; (d) a legacy-JSON-upgrade migration test.
- **What I'm NOT changing:** the `adapter.toml` contract (no block edits, no `SPEC_VERSION` bump); the recorded-adapter identity (state stays `kiro`/`kiro-cli`); the build adapters (`kiro_ide.py` / `kiro_cli.py` / `kiro.py`).

**Declined patterns.** Tempted to normalize `state.adapter` from `kiro`→`kiro-ide` at the resolver (one clean chokepoint); declining — it rewrites the adopter's chosen adapter identity, which RFC-0022 keeps as a named alias. Tempted to add an install-time deprecation-warning line for the `kiro` alias (mirroring the build registry's `DeprecationWarning`); declining — out of scope for "behave like kiro-ide", and adds stderr noise the tests would need to absorb. Tempted to make `_merge_user_scope_hook_wiring` *raise* on an unrecognized adapter (strict fail-closed); declining — returning `[]` (no spurious `.kiro/agents/*.json` write) is the safe behavior and raising risks breaking a legitimate-but-unmodeled adapter that ships user-scope hooks; the no-fall-through-to-Kiro-merge property is what the security finding actually required.

> **Review note:** the pre-EXECUTE adversarial + security pass corrected an earlier "leave the rails alone" decision — retargeting the merge behavior to `kiro-cli` while the rails keyed on literal `"kiro"` would have silently dropped the install-time symlink / malformed-TOML / missing-`attach-to-agent` / path-traversal refusals for the merging adapter. The rails now recognize the merge family; the diff grows by a membership-set change in three call sites (no new abstraction).

## Tasks

### T1 — Projection dispatch routes `kiro` → kiro-ide + `_canonical_install_adapter` helper

**Depends on:** none.

**Mode:** TDD. **Done when:** a module-level `_canonical_install_adapter(adapter) -> str` (maps `"kiro"`→`"kiro-ide"`, else identity; single source for the alias in install.py, mirroring the registry's `_kiro_alias_project`) exists, and both `_render_for_user_scope` and `_render_for_repo_scope` dispatch on it (the routing half landed in the pre-spec spike as inline `in ("kiro","kiro-ide")`; refactor onto the helper here); unused `kiro` import dropped.

**Tests:** `test_kiro_alias_projects_md_agents_not_json` (added) — `.md` agents, no `.json`. (AC1) + `state.adapter == "kiro"` assertion added in T5.

**Approach:** Add the helper near the other adapter constants; replace the two inline `in ("kiro","kiro-ide")` dispatch checks with `_canonical_install_adapter(target_adapter) == "kiro-ide"`.

### T2 — Hook-wiring merge: explicit adapter allowlist; drop for the kiro alias

**Depends on:** T1 (`_canonical_install_adapter`).

**Mode:** TDD. **Done when:** `_merge_user_scope_hook_wiring` dispatches on an explicit allowlist — copilot → `[]`; claude-code → settings merge; `_canonical_install_adapter(target_adapter) == "kiro-ide"` (i.e. `kiro`/`kiro-ide`) → `[]` (early, before parse/write); `kiro-cli` → the agent-JSON merge; any other adapter → `[]` (no fall-through to Kiro merge).

**Tests:**
- New: user-scope install (`--adapter kiro`) of a hook-wiring-bearing pack → rc 0, `.kiro/agents/<name>.md` exists, no `.json`, `hook_wiring_owned == []`. (AC2)
- Existing `kiro-cli` retargeted suites still merge (AC4) — guards against over-gating.

**Approach:** Reshape the trailing branch: add `if _canonical_install_adapter(target_adapter) == "kiro-ide": return []` ahead of the merge, change the merge guard to `if target_adapter == "kiro-cli":`, and end with `return []` for the unmodeled-adapter case, with a comment naming kiro-cli as the only agent-JSON merger **and why the fall-through returns empty** (no merge owner; avoids a spurious `.kiro/agents/*.json` write — a future adapter that ships user-scope hooks must add its own branch rather than silently riding this one).

### T3 — Drop-warning: enumerate canonical, display the adopter's name

**Depends on:** T1 (`_canonical_install_adapter`).

**Mode:** TDD. **Done when:** the warning for a `kiro` install enumerates kiro-ide's drops (hook-wiring + command for `core`) but its text names `kiro`, not `kiro-ide`.

**Tests:** New/extended assertion: the `kiro` drop-warning clause contains `hook-wiring` AND the message text contains `kiro` and not `kiro-ide`. (AC3)

**Approach:** Give `_maybe_emit_dropped_warning` separate enumeration-vs-display adapters: enumerate dropped/compatible sets with `_canonical_install_adapter(adapter)` (kiro-ide), but pass the original `adapter` (`kiro`) as the display name into `format_drop_message`. `kiro-cli`/others: canonical == original, no change.

### T4 — Merge-path rails recognize the merge family `{"kiro","kiro-cli"}`

**Depends on:** none (independent of T1's helper; uses a scope_rails constant).

**Mode:** TDD. **Done when:**
- `check_kiro_attach_to_agent` (scope_rails ~328) and `check_kiro_wiring` (~488) fire on intersection with a module constant `_MERGE_INTO_AGENT_JSON_ADAPTERS = {"kiro", "kiro-cli"}`;
- `validate._kiro_target_adapters` returns the merge-family members present in `allowed-adapters`, **and** the validate caller gate at `validate.py:196` fires on `target_adapters & _MERGE_INTO_AGENT_JSON_ADAPTERS` (not literal `"kiro"`), passing the resolved member into `enumerate_event_dropped_wirings` / `format_drop_message` at `:239`/`:245`;
- the install pre-flight at `install.py:639` fires for `user_target_adapter == "kiro-cli"` (passing `{"kiro-cli"}`), not for the `kiro` alias, and its comment block (`:633-639`) is updated to say "fires for the merging adapter, not the `kiro` alias".

**Tests:**
- New unit case in `test_validate_attach_to_agent.py`: the in-memory rail + filesystem wrapper fire (refuse) for `{"kiro-cli"}`; existing `{"claude-code"}` no-op cases unchanged. (AC7)
- New **end-to-end** `validate`-command test: a malformed-wiring `kiro-cli` pack fails `validate` (rc 1) — pins the `:196` caller gate, not just `_kiro_target_adapters`'s return value. (AC7)
- The retargeted `AttachToAgentPathTraversalRefusedTests` (T5) exercises the pre-flight firing for kiro-cli end-to-end. (AC5)

**Approach:** Replace the two literal `"kiro" not in set(...)` guards in scope_rails with `not (set(target_adapters or ()) & _MERGE_INTO_AGENT_JSON_ADAPTERS)`; in `validate._kiro_target_adapters` return `{a for a in ("kiro","kiro-cli") if a in allowed_strs}` (heuristic fall-through stays `{"kiro"}`); widen the `validate.py:196` gate + thread the resolved member through `:239`/`:245`; change `install.py:639` to the merging-adapter trigger + update its comment.

### T5 — Retarget fixtures + tests to `kiro-cli`

**Depends on:** T2, T4 (retargeted tests assert the new merge gate + rails behavior).

**Mode:** TDD (the tests are the contract). **Done when:** the two fixtures declare `allowed-adapters = ["kiro-cli"]` and every legacy-behavior test installs via `kiro-cli`, with `state.adapter` expectations updated to `kiro-cli`.

**Tests (retargeted):** `KiroUserHooksInstallTests`, `AttachToAgentPathTraversalRefusedTests` (strengthen: assert refusal names `attach-to-agent` AND no `tmp/escape*` file created), `KiroUserHooksUninstallTests` (×2), `UpgradeThenUninstallTests::test_kiro_install_upgrade_uninstall_removes_agent_file`, `AttachToAgentRenameTests`, `KiroPerFileDropEndToEnd`, `KiroWarningEndToEnd::test_kiro_warning_names_command_only`. (AC4, AC5, AC6) Also add a `state.adapter == "kiro"` assertion to `test_kiro_alias_*`.

**Approach:** Flip `allowed-adapters` in `tests/fixtures/packs/{kiro-user-hooks,kiro-repo-hooks}/pack.toml`; change each test's `--adapter kiro` / inline `allowed-adapters = ["kiro"]` to `kiro-cli`, and `assertEqual(ps.adapter, "kiro")` → `"kiro-cli"`. Verify the build-layer fixture tests stay green (call `project()` directly).

### T6 — Legacy-JSON upgrade migration

**Depends on:** T1, T2 (exercises the new projection + merge-drop on an upgrade).

**Mode:** TDD. **Done when:** a synthesized pre-existing legacy `kiro` JSON install (`.kiro/agents/<name>.json` + `hook_wiring_owned` state rows recorded under adapter `kiro`) transitions cleanly when the new code runs upgrade/install: no crash, `.md` projected, stale `.json` + merge-owned rows reconciled (not orphaned, no adopter-edited false-refusal).

**Tests:** New test under `test_upgrade_user_hooks.py` (or a new module) synthesizing the legacy state and asserting the clean transition. (AC8) If the upgrade machinery surfaces a real bug, fix it in `install.py`; if it cannot be fixed within scope, **Surface** rather than rabbit-hole.

### T7 — Changelog

**Depends on:** none.

**Mode:** goal-based. **Done when:** `docs/product/changelog.md` `[Unreleased]` has a `Fixed` entry for the kiro install alias. (AC9) (No `docs/backlog.md` deferral — the validate-rail gap is closed by T4.)

## Verification

`cd packages/agentbundle && python -m pytest tests/ agentbundle/build/tests/ -q` green; targeted re-run of the seven retargeted classes + the two new tests; `make build-check` from repo root if any projected surface is implicated (it is not — this is package code only).
