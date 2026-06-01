# Plan: kiro-adapter-split (RFC-0022)

- **Spec:** [`spec.md`](spec.md)
- **Driving RFC:** [RFC-0022](../../rfc/0022-kiro-adapter-split.md) — Accepted 2026-06-01
- **Branch:** `eugenelim/kiro-adapter-split-impl` (off `main`)

## Trio

**Files I'll touch** (implementation pass):

- `packages/agentbundle/agentbundle/_data/adapter.toml` + `_data/` mirror — contract v0.9 bump, `kiro-ide` + `kiro-cli` + `kiro` stub blocks, mapping tables, `kiro-ide-hook` activation.
- `packages/agentbundle/agentbundle/build/adapters/kiro.py` — `kiro-ide` and `kiro-cli` modules; `kiro` alias registration.
- `packages/agentbundle/agentbundle/build/adapters/__init__.py` — registry entries.
- `packages/agentbundle/agentbundle/build/projections/kiro_ide_hook.py` — no change to projector; schema/validate rail update only.
- `packages/agentbundle/agentbundle/build/scope_rails.py` — E3 vocabulary in `check_kiro_ide_hook`.
- `packages/agentbundle/agentbundle/cli.py` — help-text string (lines 198/296).
- `packages/agentbundle/tests/test_adapter_kiro*.py` — updated / new test files.
- `packages/agentbundle/tests/test_contract.py` — version assertion bump.
- `docs/rfc/0005-user-scope-hook-support.md` — errata append (T9).
- `docs/specs/kiro-ide-hook/probes.md` — Q11 outcome (T10).
- `docs/specs/distribution-adapters/spec.md` — footnote + table correction (T5).
- `docs/specs/agent-spec-cli/spec.md` — §v0.4 clarification (T6).

**What tests demonstrate done:**
`make build-check` green; `test_contract.py` asserts `"0.9"`; `test_adapter_kiro_ide.py` asserts no CLI-only keys; `test_adapter_kiro_cli.py` asserts CLI short names; `test_kiro_ide_hook.py` rail asserts E3 vocabulary; alias resolution test captures deprecation warning.

**What I am not changing:**
Skill, steering, and MCP projection (identical across IDE and CLI). `SELF_HOST_ADAPTERS` (both new adapters stay excluded, consistent with existing `kiro`). `pack.schema.json` adapter-contract enum (v0.9 is a contract internal version; pack files reference it by the `[contract].version` key, which is already free-string). No pack.toml files (packs declaring `"kiro"` continue to work via the alias).

**Declined patterns:**
- Tempted to add a `--surface` flag to `cli.py` (Option B from RFC-0022 § Options); declining — adapters *are* the surface in this model; a flag would be inconsistent with the one-adapter-one-target principle.
- Tempted to add user-scope `kiro-ide-hook` targets; declining — blocked on kirodotdev/Kiro#5440, tracked as Open Q1 in RFC-0022.
- Tempted to cross-check model id values against the live Kiro binary; declining — RFC-0022 D5 explicitly marks these as manually maintained.
- Tempted to set a removal timeline for the `kiro` alias; declining — RFC-0022 D1 explicitly sets none.

---

## Pre-execution gate: Q6 probe

**Q6 must be run and recorded in `docs/specs/kiro-ide-hook/probes.md` before T1 is committed.**
The probe determines the `target.repo` string for `kiro-ide-hook` in the contract block (RFC-0022 Key Assumption 4). If Q6 lands `no-recursion`, the path `<pack>/<name>.kiro.hook` flattens to `<pack>--<name>.kiro.hook` and T1's TOML must be amended before merging.

RFC-0022 assumes `yes-recursion` (lean quadrant); this plan carries the `yes-recursion` path throughout. If the probe overturns it, revise T1's TOML accordingly and note the deviation.

---

## Tasks

### T9 — Append RFC-0005 errata E1-E3 (prerequisite for T1 and T2)

`Depends on: none`  
`Touches: docs/rfc/0005-user-scope-hook-support.md`

**Tests:**

- Goal-based: `grep -c "## Errata"` in `docs/rfc/0005-user-scope-hook-support.md` returns 1.
- Goal-based: `grep "E1"` and `grep "E2"` and `grep "E3"` all match in the errata table.

**Approach:**

Append the following block verbatim to the end of `docs/rfc/0005-user-scope-hook-support.md`. Fill `DATE_OF_MERGE` with the actual merge date at merge time (or `2026-06-01` if merged same day as RFC acceptance).

```markdown
## Errata

Corrections below are Approver-signed amendments. The RFC body above is preserved
unchanged; errata supersede where noted. (Approver: eugenelim, DATE_OF_MERGE.)

| ID | Introduced by | Date | Correction |
|----|--------------|------|------------|
| E1 | RFC-0022 | DATE_OF_MERGE | RFC-0005 assumed a single `kiro` adapter. Superseded: `kiro` is a deprecated alias for `kiro-ide`; `kiro-cli` is the separate CLI target. |
| E2 | RFC-0022 | DATE_OF_MERGE | `hook-wiring` (merge-into-agent-json) is CLI-only for Kiro. The IDE loader drops any agent carrying a `hooks` key. `hook-wiring` moves to `kiro-cli`; `kiro-ide` drops it in favour of the `kiro-ide-hook` primitive. |
| E3 | RFC-0022 | DATE_OF_MERGE | RFC-0005 described the IDE event vocabulary as a "best-guess" (Unresolved Q11); `distribution-adapters/spec.md:749` marked it `<probe-pinned per Q11>`. RFC-0022 closes Q11 via static analysis of `extension.js` `IDEListenableEvent` enum (2026-06-01) — a deliberate substitution of RFC-0005's stated fixture-probe verification method. Authoritative vocabulary: `fileEdited`, `fileCreated`, `fileDeleted`, `userTriggered`, `promptSubmit`, `agentStop`, `preToolUse`, `postToolUse`, `preTaskExecution`, `postTaskExecution`, `sessionStart`. Actions: `askAgent` / `runCommand`. Shipped validate rail (`fileSave`/`fileEdit`/`manualTrigger`) superseded; updates in T2. `probes.md` Q11 outcome recorded in T10. |
```

**Done when:** `grep -c "## Errata" docs/rfc/0005-user-scope-hook-support.md` returns `1` AND `grep -c "| E1 "`, `grep -c "| E2 "`, `grep -c "| E3 "` all return `1`.

---

### T10 — Update probes.md Q11 Outcome (no code dependency)

`Depends on: none`  
`Touches: docs/specs/kiro-ide-hook/probes.md`

**Tests:**

- Goal-based: `grep "RFC-0022" docs/specs/kiro-ide-hook/probes.md` returns a match in the Q11 Outcome block.
- Goal-based: `grep "fileEdited" docs/specs/kiro-ide-hook/probes.md` returns a match.
- Goal-based: `grep "sessionStart" docs/specs/kiro-ide-hook/probes.md` returns a match (last term in E3 list; most likely to be dropped in a truncation).

**Approach:**

Replace the Q11 Outcome block (lines 93–105 in the current file):

```markdown
### Outcome

> **Not yet run.** This row is the surface-to-operator gate.

- **Captured fixture(s):** _<list filenames under `tests/fixtures/kiro_ide_hook/captured/`>_
- **Canonical `when.type` strings observed:** _<comma-separated list>_
- **Canonical `then.type` strings observed:** _<comma-separated list>_
- **`ide-event-vocabulary` to declare in `adapter.toml`:**
  _<probe-pinned list ...>_
- **`ide-action-vocabulary` to declare in `adapter.toml`:**
  _<at minimum `["askAgent", "runCommand"]` ...>_
- **Date of observation:** _<YYYY-MM-DD>_
- **Kiro version observed:** _<e.g. 0.2.13>_
```

Replace with:

```markdown
### Outcome

> **Closed by RFC-0022 (static analysis, 2026-06-01).** RFC-0022 closes Q11 via
> static analysis of `extension.js` `IDEListenableEvent` enum rather than an
> IDE-UI-authored fixture. This is a deliberate substitution of the
> fixture-probe verification method (RFC-0005 § Errata, E3). No fixture is
> required under this closure.

- **Closure method:** static analysis of `extension.js` `IDEListenableEvent` enum (2026-06-01)
- **Captured fixture(s):** none required under RFC-0022 substitution
- **Canonical `when.type` strings (E3 vocabulary):** `fileEdited`, `fileCreated`,
  `fileDeleted`, `userTriggered`, `promptSubmit`, `agentStop`, `preToolUse`,
  `postToolUse`, `preTaskExecution`, `postTaskExecution`, `sessionStart`
- **Canonical `then.type` strings:** `askAgent`, `runCommand`
- **`ide-event-vocabulary` declared in `adapter.toml`:** the E3 list above
- **`ide-action-vocabulary` declared in `adapter.toml`:** `["askAgent", "runCommand"]`
- **Date of closure:** 2026-06-01
- **Kiro version verified against:** `extension.js` snapshot (2026-06-01)
- **Governance reference:** RFC-0022 E3; `docs/rfc/0005-user-scope-hook-support.md` § Errata
```

**Done when:** `grep "RFC-0022" docs/specs/kiro-ide-hook/probes.md` returns a match AND `grep "fileEdited" docs/specs/kiro-ide-hook/probes.md` returns a match AND `grep "sessionStart" docs/specs/kiro-ide-hook/probes.md` returns a match.

---

### T3 — `kiro-cli` adapter block + mapping table (no dependencies)

`Depends on: none`  
`Touches: packages/agentbundle/agentbundle/_data/adapter.toml (+ _data/ mirror)`

**Tests:**

- TDD: write `test_adapter_kiro_cli.py` before the adapter code:
  - `test_cli_agent_is_json`: project a synthetic agent; assert output file is `.json`.
  - `test_cli_tool_short_names`: assert `tools` array contains `"read"`, `"grep"`, `"glob"`, `"write"`, `"shell"`, `"web_fetch"`, `"web_search"`.
  - `test_cli_no_ide_hook_field`: assert no `ide-event-vocabulary` or `kiro-ide-hook` section in output.

**Approach:**

Add `[adapter.kiro-cli]` block to `adapter.toml` per RFC-0022 § 4. Add `kiro-cli-agent-frontmatter-v1.0` frontmatter-mapping table per RFC-0022 § 4 (tool values map to CLI short names). Mirror to `_data/` byte-identical copy. Add `kiro_cli.py` projector module alongside `kiro_ide.py`; register `"kiro-cli"` in `adapters/__init__.py`.

**Done when:** red tests go green; `make build-check` passes.

---

### T4 — `kiro` deprecated alias stub + registry (no dependencies)

`Depends on: none`  
`Touches: packages/agentbundle/agentbundle/_data/adapter.toml, adapters/__init__.py`

**Tests:**

- TDD: write `test_adapter_kiro_alias.py` before the alias code:
  - `test_kiro_resolves_to_kiro_ide`: call `adapters.get("kiro")` and assert it returns `kiro_ide.project`.
  - `test_kiro_emits_deprecation_warning`: assert `logging.warning` or equivalent called with a string containing `"kiro-ide"`.
  - `test_kiro_alias_in_shipped_for_cli`: assert `"kiro"` in `_shipped_for_cli` (derived from contract).

**Approach:**

Retain `[adapter.kiro]` stub block in `adapter.toml` with deprecation comment. In `adapters/__init__.py`, add `"kiro": kiro_ide.project` to the registry dict. Wrap the alias call site to emit the deprecation warning before dispatching.

**Done when:** red tests go green.

---

### T5 — `distribution-adapters` spec footnote + table correction (no dependencies)

`Depends on: none`  
`Touches: docs/specs/distribution-adapters/spec.md`

**Tests:**

- Goal-based: `grep "kiro-ide projects"` in `distribution-adapters/spec.md` returns a match.
- Goal-based: `grep "confirming agents are JSON"` returns no match (stale footnote removed).

**Approach:**

Locate lines 214–218 (the footnote "RFC-0005 / T7 introduced the JSON emission … *confirming agents are JSON*"). Replace with: "`kiro-ide` projects `.md`; `kiro-cli` projects `.json`; the IDE accepts both (verified in `extension.js` `p16` / `loadCustomAgentFile`, 2026-06-01)." Update the agent row and hook-wiring row in the primitive table to reflect the split.

**Done when:** both greps pass.

---

### T6 — `agent-spec-cli` §v0.4 clarification (no dependencies)

`Depends on: none`  
`Touches: docs/specs/agent-spec-cli/spec.md`

**Tests:**

- Goal-based: `grep "contract activation deferred to RFC-0022"` in `agent-spec-cli/spec.md` returns a match.

**Approach:**

In the §v0.4 / `kiro-ide-hook` section of `agent-spec-cli/spec.md`, add a parenthetical: "(Code shipped in PR #99; contract activation deferred to RFC-0022.)" after the Shipped status claim.

**Done when:** grep returns a match.

---

### T7 — `cli.py` help text (no dependencies)

`Depends on: none`  
`Touches: packages/agentbundle/agentbundle/cli.py`

**Tests:**

- Goal-based: `python -m agentbundle --help` output contains `kiro-ide` and `kiro-cli`.
- Goal-based: `grep "kiro-ide"` in `cli.py` at lines 198/296 returns a match.

**Approach:**

Find the hardcoded `"claude-code, kiro, copilot, codex"` string in `cli.py` (lines ~198 and ~296). Replace with `"claude-code, kiro-ide, kiro-cli, kiro (deprecated → kiro-ide), copilot, codex"`.

**Done when:** both greps pass and `--help` output is correct.

---

### T2 — Validate rail update: E3 vocabulary (depends on T9)

`Depends on: T9`  
`Touches: packages/agentbundle/agentbundle/build/projections/kiro_ide_hook.py, packages/agentbundle/agentbundle/build/scope_rails.py`

**Tests:**

- TDD (red-green on updated tests in `test_kiro_ide_hook.py`):
  - `test_old_vocabulary_rejected`: `{"when": {"type": "fileSave"}, ...}` → assert validation error.
  - `test_old_vocabulary_rejected_file_edit`: same for `"fileEdit"` and `"manualTrigger"`.
  - `test_e3_vocabulary_accepted`: `{"when": {"type": "fileEdited"}, ...}` → assert no error.
  - `test_e3_session_start_accepted`: same for `"sessionStart"`.

**Approach:**

Update the `IDE_EVENT_VOCABULARY` constant in `kiro_ide_hook.py` (and mirrored in `scope_rails.py` `check_kiro_ide_hook`) from the RFC-0005 inferred list (`fileSave`, `fileEdit`, `manualTrigger`) to the E3 verified list (`fileEdited`, `fileCreated`, `fileDeleted`, `userTriggered`, `promptSubmit`, `agentStop`, `preToolUse`, `postToolUse`, `preTaskExecution`, `postTaskExecution`, `sessionStart`).

Write the red tests first, confirm they fail on the current vocabulary, then update the constant.

**Done when:** all four new tests pass; existing `test_kiro_ide_hook_*` tests still pass.

---

### T1 — Contract v0.9 bump + `kiro-ide` adapter block (depends on Q6 probe + T9)

`Depends on: Q6 probe (human gate), T9`  
`Touches: packages/agentbundle/agentbundle/_data/adapter.toml (+ _data/ mirror), packages/agentbundle/agentbundle/build/adapters/kiro.py`

**Tests:**

- TDD:
  - `test_contract_version_is_0_9`: parse `adapter.toml` and assert `[contract].version == "0.9"`.
  - `test_kiro_ide_agent_is_md`: project a synthetic agent via `kiro-ide`; assert output file is `.md`.
  - `test_kiro_ide_no_cli_only_keys`: assert none of `hooks`, `allowedTools`, `toolsSettings`, `mcpServers` appear in the projected `.md` frontmatter output.
  - `test_kiro_ide_hook_declared_in_contract`: parse `adapter.toml` and assert `[adapter.kiro-ide.projections.kiro-ide-hook]` exists.
  - `test_frontmatter_table_renamed`: assert `kiro-ide-agent-frontmatter-v0.9` key exists; assert `kiro-agent-frontmatter-v0.9` does not.

**Approach:**

1. Confirm Q6 probe outcome is recorded in `probes.md` (gate check).
2. Bump `[contract] version` from `"0.8"` to `"0.9"` in `adapter.toml`.
3. Add `[adapter.kiro-ide]` block per RFC-0022 § 3 (scope, projections, `kiro-ide-hook` sub-block, vocabulary).
4. Rename `kiro-agent-frontmatter-v0.9` → `kiro-ide-agent-frontmatter-v0.9` in the contract block and in all call sites inside `kiro.py`.
5. Mirror to `_data/` byte-identical copy.

Write the red tests first, then make them green.

**Done when:** all five new tests pass; `make build-check` green.

---

### T8 — Test suite updates (depends on T1, T2, T3, T4)

`Depends on: T1, T2, T3, T4`  
`Touches: packages/agentbundle/tests/test_adapter_kiro*.py, packages/agentbundle/tests/test_contract.py`

**Tests:**

- Goal-based: `pytest packages/agentbundle/tests/` exits 0 with no errors.
- Goal-based: `make build-check` exits 0.

**Approach:**

Consolidate any now-redundant `kiro` tests with the new `kiro-ide`/`kiro-cli`/alias tests. Ensure `test_contract.py` asserts `"0.9"`. Run the full test suite; fix any contract-drift gate failures. Update any snapshot or fixture that references `kiro-agent-frontmatter-v0.9` (old name) to `kiro-ide-agent-frontmatter-v0.9`.

**Done when:** `pytest` and `make build-check` both green.

---

## Dependency graph

```
T9 ─────────────────────────┬──► T2 ──────────┐
                             │                 │
Q6 probe (human) ────────────┤                 │
T9 ──────────────────────────┴──► T1 ──────────┤
T3 ──────────────────────────────────────────►─┤──► T8
T4 ──────────────────────────────────────────►─┘
T5, T6, T7, T10 ─── independent (any order, any wave)
```

**Wave 0 (human gate):** Run Q6 probe; record outcome in `probes.md`.  
**Wave 1 (no code deps):** T9, T10, T3, T4, T5, T6, T7 — all independent.  
**Wave 2:** T2 (after T9 only), T1 (after T9 + Q6 probe recorded).  
**Wave 3:** T8 (after T1, T2, T3, T4).

## Design (LLD)

### Design decisions

1. **Adapter identity model.** `kiro-ide` and `kiro-cli` are first-class adapter entries in the Python registry, not conditionals inside a single `kiro` module. The registry is two name-keyed dicts in `adapters/__init__.py`; adding entries is the change — no routing logic introduced.
2. **Alias mechanism.** `kiro` maps to `kiro_ide.project` at the registry level. The contract retains a `[adapter.kiro]` stub so `_shipped_for_cli` (derived from the adapter key set) continues to include `"kiro"` and `allowed-adapters` validation keeps accepting it. Without the stub, `"kiro"` falls out of the derived enum.
3. **`kiro-ide-hook` activation is declaration-only.** The projector (`kiro_ide_hook.py`), schema, and test suite shipped in PR #99. Activation is adding the primitive to the `[adapter.kiro-ide.projections]` block in `adapter.toml` — no new code.
4. **Vocabulary update is a constant swap.** `IDE_EVENT_VOCABULARY` in `kiro_ide_hook.py` / `scope_rails.py` is a module-level constant. The update is a list replacement; no structural change to the rail function.

### Interfaces & contracts

- **`adapters/__init__.py` registry:** `str → Callable[[Pack, Config], None]`. New entries: `"kiro-ide"` and `"kiro-cli"` (canonical); `"kiro"` (alias → `kiro_ide.project`).
- **`adapter.toml` `[contract] version`:** `"0.9"` (was `"0.8"`). Adapter key set grows from 4 (`claude-code`, `kiro`, `copilot`, `codex`) to 6 (`claude-code`, `kiro-ide`, `kiro-cli`, `kiro`, `copilot`, `codex`).
- **Frontmatter mapping tables:** `kiro-ide-agent-frontmatter-v0.9` (renamed), `kiro-cli-agent-frontmatter-v1.0` (new).

### Failure, edge cases & resilience

- **Packs declaring `allowed-adapters = ["kiro"]`:** the alias and stub together ensure `validate` keeps accepting `"kiro"` and `install` resolves to `kiro-ide`. No pack.toml changes required.
- **Q6 lands `no-recursion`:** T1 TOML path changes to `<pack>--<name>.kiro.hook`. T-E1b in the `kiro-ide-hook` spec fires (hook-body user-scope retarget). Revise T1's approach before merging; note deviation in PR description.
- **Old vocabulary in existing `.kiro.hook` files:** the validate rail update (T2) will reject them at validate time. The backlog shows no shipping pack using `.apm/kiro-ide-hooks/`; this is a safe breakage gate — it catches packs built against the wrong list before they project wrong files.
