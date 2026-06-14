# Spec: kiro-install-alias-parity

- **Status:** Shipped
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:**
  - [RFC-0022](../../rfc/0022-kiro-adapter-split.md) — `kiro` is a deprecated alias for `kiro-ide`; this spec completes that decision in the install path.
  - [ADR-0012](../../adr/0012-kiro-adapter-split.md) — the six split decisions.
  - [RFC-0005](../../rfc/0005-user-scope-hook-support.md) — user-scope hook-wiring merge (`merge-into-agent-json`).

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

> **Mode: full** (risk triggers: structural / public-interface change — the
> `agentbundle install` behavior for the `kiro` adapter changes; and it sits
> adjacent to a security boundary — the user-scope hook-wiring merge and its
> path-traversal rail).

## Objective

RFC-0022 made bare `kiro` a **deprecated alias for `kiro-ide`**. That alias was
wired into the build registry (`ADAPTERS["kiro"]` → `_kiro_alias_project` →
`kiro_ide.project`) but **never into the install path**: `agentbundle install`
had its own dispatch that routed `kiro` → `kiro.project`, which reads the legacy
`[adapter.kiro]` contract block and emits `.json` agents plus a hook-wiring
merge. Result: `make build` treated `kiro` as kiro-ide while
`install --adapter kiro` treated it as the legacy (≈ kiro-cli) adapter — a
silent divergence, and the symptom the user reported (kiro installs subagents as
JSON, not markdown).

Make `agentbundle install`/`uninstall`/`upgrade` treat `kiro` **exactly like
`kiro-ide`**: `.md` agents, hook-wiring **dropped** (no merge), kiro-ide drop
semantics. The legacy JSON-agents + hook-wiring-merge behavior is retained — it
lives under the `kiro-cli` adapter, which is where its test coverage moves.

The recorded `state.adapter` (and the `installed: … via <adapter>` summary) keep
showing the name the adopter chose — `kiro` — so the alias stays a working,
named adapter (RFC-0022 keeps it with no removal timeline). Only **behavior**
canonicalizes to kiro-ide; **identity** is preserved.

## Boundaries

**Always do:**
- Route `kiro` (install/uninstall/upgrade projection) through `kiro_ide.project`, matching the build registry alias.
- Drop hook-wiring for `kiro` at install time — via an explicit early return in `_merge_user_scope_hook_wiring` keyed on the canonical adapter, **before** any wiring-TOML parse or filesystem write: return no merge-owned rows, write no `.kiro/agents/<name>.json`, never crash on a hook-wiring-bearing pack.
- Make `_merge_user_scope_hook_wiring` dispatch on an explicit adapter allowlist (copilot → none; claude-code → settings merge; kiro/kiro-ide → none/dropped; kiro-cli → agent-JSON merge) and return no rows for any other adapter — no silent fall-through to Kiro merge semantics.
- Make the dropped-primitives install warning **enumerate** kiro-ide's drops (hook-wiring + command) for the `kiro` alias, while **displaying** the adopter's chosen adapter name (`kiro`) in the warning text.
- Keep the legacy JSON + hook-wiring-merge behavior reachable and tested under `kiro-cli`; retarget the affected fixtures and tests from `kiro` to `kiro-cli`.
- Fire the merge-path rails for the adapter that actually merges. The shared `scope_rails` rails (`check_kiro_attach_to_agent` / `check_kiro_wiring`), the install pre-flight (the Step-6 `check_kiro_wiring` call in `install.run`), and `validate`'s `_kiro_target_adapters` recognize the merge family `{"kiro", "kiro-cli"}`, so `kiro-cli` packs keep the symlink, malformed-TOML, missing/unknown-`attach-to-agent`, and path-traversal refusals that `kiro` packs had pre-split. The pre-flight fires for the merging adapter (`kiro-cli`), **not** for the `kiro` alias (which drops wiring, matching kiro-ide).
- Record `state.adapter` as the adopter's chosen name (`kiro` stays `kiro`, `kiro-cli` stays `kiro-cli`).
- Add a `docs/product/changelog.md` `[Unreleased]` entry (adopter-visible behavior change).

**Ask first:**
- Any change to the recorded-adapter identity (normalizing `state.adapter` from `kiro` to `kiro-ide`) — out of scope; the alias stays a named adapter.
- Bumping the adapter contract version (`SPEC_VERSION`) — not required; no contract block changes.

**Never do:**
- Edit any `adapter.toml` block (RFC-0022 forbids removing the kiro block; no block needs changing).
- Normalize the alias anywhere the adopter sees the adapter name (stdout summary, state file, **drop-warning text**).
- Co-project `.md` and `.json` for the same agent: a single install resolves exactly one target adapter, so `kiro` (md) and `kiro-cli` (json) are never both projected in one run even for a pack that lists both in `allowed-adapters`.

## Acceptance Criteria

- [x] **AC1** — `install --adapter kiro` (repo and user scope) projects agents as `.kiro/agents/<name>.md`; no `.kiro/agents/*.json` is written.
- [x] **AC2** — `kiro` makes the **same** decisions as `kiro-ide` for a hook-wiring-bearing pack: at **repo** scope it installs without crashing, dropping the wiring (no agent JSON, no merge); at **user** scope a `user-scope-hooks = true` pack is **refused** identically to `kiro-ide` (the IDE has no user-scope hook-wiring mode — RFC-0005 AC25), because the install gate canonicalizes the alias before deciding. The merge-side drop (`_merge_user_scope_hook_wiring` early-return keyed on the canonical adapter, before any parse/write) is the defense-in-depth backstop, exercised via the legacy-state upgrade path.
- [x] **AC3** — The dropped-primitives install warning for `kiro` (repo scope) enumerates the primitives kiro-ide drops (for `core`: `hook-wiring` and `command`), while its text names the adopter's chosen adapter (`kiro`, not `kiro-ide`).
- [x] **AC4** — `install --adapter kiro-cli` retains the legacy behavior: `.json` agents with CLI tool tokens and hook-wiring merged into `.kiro/agents/<attach-to-agent>.json`, with `hook_wiring_owned` rows carrying the `target-file` field. (Verified by the retargeted user-hooks/uninstall/upgrade suites.)
- [x] **AC5** — A user-scope `kiro-cli` install of a pack whose `hook-wiring` declares a path-traversal `attach-to-agent` (`"../../../tmp/escape"`) is refused (`rc != 0`); the refusal text names `attach-to-agent`, and no file is created outside the user-scope root.
- [x] **AC6** — `state.adapter` records the adopter's chosen adapter name verbatim — a `kiro`-alias install records `kiro` (asserted by `test_kiro_alias_*`), a `kiro-cli` install records `kiro-cli` (retargeted suites); the `installed: … via <adapter>` summary matches.
- [x] **AC7** — The merge-path rails recognize the merge family `{"kiro", "kiro-cli"}`: `check_kiro_attach_to_agent` / `check_kiro_wiring` fire for `kiro-cli` (unit-tested), the install pre-flight rail (the `check_kiro_wiring` call in Step 6 of `install.run`) fires for `kiro-cli` and **not** for the `kiro` alias (which drops wiring), and `validate`'s `_kiro_target_adapters` + its caller gate run the rail for a `kiro-cli` pack. **Validate stays strict for the whole merge family by design** — it runs the `attach-to-agent` well-formedness rail for a `["kiro"]`-declared pack too (a pack-authoring check), intentionally stricter than install (where the `kiro` alias drops the wiring without validating it); this asymmetry is pinned by `test_kiro_legacy_alias_pack_validate_stays_strict`.
- [ ] **AC8** — A legacy `kiro` JSON install (pre-existing `.kiro/agents/<name>.json` + `hook_wiring_owned` rows, `state.adapter == "kiro"`) migrates cleanly under the new code. **Uninstall** removes the agent JSON via the merge-family unproject (no orphan) — fully verified. **Upgrade** re-renders `.md`, records `kiro`, and clears the merge rows — verified — but **leaves the stale `.json` orphaned**, a pre-existing general `upgrade` limitation (no orphan-removal on projection-shape change) that is exposed, not caused, by this migration. Deferred `(deferred: upgrade-orphan-removal-on-projection-shape-change)`; workaround is uninstall + reinstall.
- [x] **AC9** — `docs/product/changelog.md` `[Unreleased]` documents the install-behavior change for the `kiro` alias.

## Testing Strategy

| Criterion | Mode | Verification |
|---|---|---|
| AC1 | TDD | `test_install_repo_scope_per_adapter.py::test_kiro_alias_projects_md_agents_not_json` — `.md` present, no `.json`. |
| AC2 | TDD | `KiroAliasRefusesUserScopeHooksLikeKiroIdeTests` — user-scope `kiro` and `kiro-ide` both refuse a `user-scope-hooks` pack with the same AC25 message; `test_kiro_alias_projects_md_agents_not_json` (repo) — installs `core` (ships hook-wiring) without crashing, no `.json`. |
| AC3 | TDD | `test_kiro_alias_projects_md_agents_not_json` asserts the repo-scope drop-warning names `hook-wiring` AND the text reads `kiro` (not `kiro-ide`). |
| AC4 | TDD | Retargeted `KiroUserHooksInstallTests`, `KiroUserHooksUninstallTests` (×2), `UpgradeThenUninstallTests`, `AttachToAgentRenameTests`, `KiroPerFileDropEndToEnd`, `KiroWarningEndToEnd` — now `kiro-cli`. |
| AC5 | TDD | Retargeted `AttachToAgentPathTraversalRefusedTests` (now `kiro-cli`) — `rc != 0`; refusal text names `attach-to-agent`; assert no `tmp/escape*` file created. |
| AC6 | goal-based | Retargeted tests assert `state.adapter == "kiro-cli"`; `test_kiro_alias_*` asserts `state.adapter == "kiro"` + the `via kiro` summary. |
| AC7 | TDD | New `scope_rails` unit case: rail fires for `{"kiro-cli"}`; existing `{"claude-code"}` no-op cases stay green. **End-to-end `validate`**: a malformed-wiring `kiro-cli` pack fails `validate` (rc 1) — covers the `validate` caller gate, not just `_kiro_target_adapters`'s return value. |
| AC8 | TDD | `LegacyKiroJsonUninstallMigrationTests` (uninstall — clean, verified); `LegacyKiroJsonUpgradeMigrationTests` (upgrade — `.md` projected + rows cleared verified; the orphaned-`.json` assertion is an `@unittest.expectedFailure` pinning the deferred limitation). |
| AC9 | goal-based | `grep` the changelog `[Unreleased]` block. |

## Assumptions

- **Verified** — the install resolver returns the adopter's chosen adapter un-normalized (`--adapter kiro` reaches the `== "kiro"` dispatch); this is why the projection bug existed and why the retarget tests fail today.
- **Verified** — the build-layer fixture tests (`test_kiro_user_hooks_fixture.py`, `test_kiro_repo_hooks_fixture.py`) call `merge_into_agent_json.project()` directly and do not read `allowed-adapters`, so the fixture retarget to `kiro-cli` does not affect them.
- **Verified** — `InMemoryRailNonKiroTargetTests` uses `{"claude-code"}` as its non-kiro example, so broadening the rail membership to `{"kiro", "kiro-cli"}` leaves the existing no-op cases green.
- **Verified** — the path-traversal refusal under `kiro-cli` is defended at two depths: the pre-flight rail (now firing for `kiro-cli`) refuses an `attach-to-agent` that names no shipped agent, and the in-merge grammar (`_AGENT_NAME_RE`) + path-jail (`safety.assert_under`) refuse before any write — confinement (CWE-73) holds regardless of which fires first.
